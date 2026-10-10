"""Private fresh-process worker; third-party imports occur after network denial."""

from __future__ import annotations

import argparse
import asyncio
import importlib.metadata
import json
import os
from collections import Counter
from pathlib import Path

from .interop import CASES, deny_external_sockets
from .loaders import policy_from_data, profile_from_data
from .trace_benchmark import corpus
from .traces import audit_traces


async def capture(name: str, directory: Path, guard: dict):
    import httpx
    import litellm
    import respx
    from opentelemetry.exporter.otlp.json.common.trace_encoder import encode_spans
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )
    from opentelemetry.trace import SpanKind

    if name.startswith("experimental"):
        os.environ["OTEL_SEMCONV_STABILITY_OPT_IN"] = "gen_ai_latest_experimental"
    if name.endswith("dedicated"):
        os.environ["USE_OTEL_LITELLM_REQUEST_SPAN"] = "true"
    from litellm.integrations.opentelemetry import OpenTelemetry, OpenTelemetryConfig

    done = asyncio.Event()

    class CompletedCallback(OpenTelemetry):
        async def async_log_success_event(self, *args, **kwargs):
            await super().async_log_success_event(*args, **kwargs)
            done.set()

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    callback = CompletedCallback(
        config=OpenTelemetryConfig(exporter=exporter), tracer_provider=provider
    )
    litellm.callbacks = [callback]
    litellm.disable_aiohttp_transport = True
    tracer = provider.get_tracer("fallbacklens-mock-gateway")
    # Authored mock response schema, not a provider completion or capability test.
    response = {
        "id": "synthetic-response",
        "object": "chat.completion",
        "created": 1,
        "model": "gpt-4.1-mini",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "SYNTHETIC_RESPONSE"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 8, "completion_tokens": 2, "total_tokens": 10},
    }
    with respx.mock(assert_all_mocked=True, assert_all_called=True) as mock:
        route = mock.post("https://fixture.invalid/v1/chat/completions").mock(
            return_value=httpx.Response(200, json=response)
        )
        with tracer.start_as_current_span(
            "synthetic gateway request", kind=SpanKind.SERVER
        ) as root:
            await litellm.acompletion(
                model="gpt-4.1-mini",
                api_base="https://fixture.invalid/v1",
                api_key="fixture-key-not-a-credential",
                messages=[{"role": "user", "content": "SYNTHETIC_PROMPT"}],
            )
            await asyncio.wait_for(done.wait(), timeout=15)
        assert route.call_count == 1
    provider.force_flush(timeout_millis=5000)
    finished = exporter.get_finished_spans()
    encoded = encode_spans(finished).to_dict()
    (directory / "raw-synthetic-otlp.json").write_text(
        json.dumps(encoded, indent=2) + "\n", encoding="utf-8"
    )
    fixture = corpus()["cases"][0]
    fixture["bindings"]["scopes"] = ["litellm"]
    fixture["bindings"]["model_groups"] = {"gpt-4.1-mini": "primary"}
    context = root.get_span_context()
    fixture["bindings"]["requests"][0].update(
        trace_id=f"{context.trace_id:032x}", root_span_id=f"{context.span_id:016x}"
    )
    # Mock instrumentation includes module/setup cost; avoid a performance/SLO claim.
    fixture["profile"]["contracts"][0]["max_latency_ms"] = 60_000
    report = audit_traces(
        policy_from_data(fixture["policy"]),
        profile_from_data(fixture["profile"]),
        encoded,
        fixture["bindings"],
    )
    private = json.dumps(report)
    assert all(
        value not in private
        for value in (
            "SYNTHETIC_PROMPT",
            "SYNTHETIC_RESPONSE",
            "fixture-key-not-a-credential",
            f"{context.trace_id:032x}",
            f"{context.span_id:016x}",
        )
    )
    verdict = report["requests"][0]["verdict"]
    evidence = {
        "verdict": verdict,
        "mock_http_requests": route.call_count,
        "span_kinds": dict(Counter(span.kind.name for span in finished)),
        "instrumentation_scopes": sorted(
            {span.instrumentation_scope.name for span in finished}
        ),
        "external_sockets_allowed": 0,
        **guard,
        "versions": {
            package: importlib.metadata.version(package)
            for package in (
                "litellm",
                "opentelemetry-sdk",
                "opentelemetry-exporter-otlp-json-common",
                "respx",
            )
        },
        "report": report,
    }
    (directory / "evidence.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    provider.shutdown()


def main():
    parser = argparse.ArgumentParser(
        description="Internal mocked instrumentation worker"
    )
    parser.add_argument("--case", required=True, choices=CASES)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    with deny_external_sockets() as guard:
        asyncio.run(capture(args.case, args.output, guard))


if __name__ == "__main__":
    main()
