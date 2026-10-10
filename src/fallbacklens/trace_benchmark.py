"""Authored synthetic trace fixtures, not independently collected provider data."""

from __future__ import annotations

from copy import deepcopy

from .loaders import policy_from_data, profile_from_data
from .traces import ALIAS, audit_traces

TRACE = "a" * 32


def span(
    identity: int,
    parent: int | None,
    model: str | None,
    start: int,
    end: int,
    *,
    kind: int = 3,
    operation: str = "chat",
) -> dict:
    attributes = [{"key": "gen_ai.operation.name", "value": {"stringValue": operation}}]
    if model:
        attributes.append(
            {"key": "gen_ai.request.model", "value": {"stringValue": model}}
        )
    return {
        "traceId": TRACE,
        "spanId": f"{identity:016x}",
        "parentSpanId": f"{parent:016x}" if parent else "",
        "kind": kind,
        "startTimeUnixNano": str(1_000_000_000 + start * 1_000_000),
        "endTimeUnixNano": str(1_000_000_000 + end * 1_000_000),
        "attributes": attributes,
        "name": "PRIVATE_SPAN_NAME",
        "events": [{"name": "PRIVATE_EVENT"}],
        "status": {"message": "PRIVATE_STATUS"},
    }


def corpus() -> dict:
    policy = {
        "model_list": [
            {"model_name": name} for name in ("primary", "secondary", "local")
        ],
        "router_settings": {
            "num_retries": 1,
            "fallbacks": [{"primary": "secondary"}, {"secondary": "local"}],
        },
    }
    profile = {
        "schema_version": 1,
        "as_of": "2026-10-09",
        "sources": ["authored synthetic facts"],
        "models": {},
        "contracts": [
            {
                "name": "tool-agent",
                "entrypoint": "primary",
                "required_capabilities": [],
                "required_context_tokens": 0,
                "require_zero_data_retention": False,
                "expected_input_tokens": 0,
                "expected_output_tokens": 0,
                "max_attempts": 3,
                "max_cost_usd": 0,
                "max_latency_ms": 500,
            }
        ],
    }
    bindings = {
        "schema_version": 1,
        "as_of": "2026-10-09",
        "scopes": ["gateway-fixture"],
        "model_groups": {
            "vendor/one": "primary",
            "vendor/two": "secondary",
            "vendor/three": "local",
        },
        "requests": [
            {"trace_id": TRACE, "root_span_id": f"{1:016x}", "contract": "tool-agent"}
        ],
    }
    root = span(1, None, None, 0, 1000, kind=2, operation="gateway")
    one = span(2, 1, "vendor/one", 10, 100)
    two = span(3, 1, "vendor/two", 110, 200)
    cases = []

    def add(
        name: str, spans: list[dict], expected: str, *, scope: str = "gateway-fixture"
    ):
        cases.append(
            {
                "name": name,
                "expected": expected,
                "policy": deepcopy(policy),
                "profile": deepcopy(profile),
                "bindings": deepcopy(bindings),
                "trace": {
                    "resourceSpans": [
                        {
                            "resource": {
                                "attributes": [
                                    {
                                        "key": "private",
                                        "value": {"stringValue": "PRIVATE_RESOURCE"},
                                    }
                                ]
                            },
                            "scopeSpans": [
                                {"scope": {"name": scope}, "spans": deepcopy(spans)}
                            ],
                        }
                    ]
                },
            }
        )

    add("serial-fallback", [root, one, two], "observed-no-drift")
    add(
        "nested-wrapper",
        [root, span(4, 1, "vendor/one", 5, 105), {**one, "parentSpanId": f"{4:016x}"}],
        "observed-no-drift",
    )
    cases[-1]["profile"]["contracts"][0]["max_attempts"] = 1
    workflow = span(4, 1, None, 5, 210, kind=1, operation="workflow")
    workflow["attributes"].append(
        {"key": "openinference.span.kind", "value": {"stringValue": "LLM"}}
    )
    add(
        "workflow-labeled-llm",
        [
            root,
            workflow,
            {**one, "parentSpanId": f"{4:016x}"},
            {**two, "parentSpanId": f"{4:016x}"},
        ],
        "observed-no-drift",
    )
    cases[-1]["profile"]["contracts"][0]["max_attempts"] = 2
    add(
        "flattened-server",
        [span(1, None, "vendor/one", 0, 1000, kind=2)],
        "inconclusive",
    )
    add(
        "unknown-model",
        [root, span(2, 1, "PRIVATE_UNKNOWN_MODEL", 10, 100)],
        "inconclusive",
    )
    add("missing-parent", [root, {**one, "parentSpanId": f"{99:016x}"}], "inconclusive")
    add(
        "call-threshold",
        [
            root,
            one,
            two,
            span(4, 1, "vendor/three", 210, 250),
            span(5, 1, "vendor/three", 260, 300),
        ],
        "drift",
    )
    add(
        "group-call-threshold",
        [
            root,
            one,
            span(3, 1, "vendor/one", 110, 200),
            span(4, 1, "vendor/one", 210, 300),
        ],
        "drift",
    )
    add(
        "unconfigured-transition",
        [root, one, span(3, 1, "vendor/three", 110, 200)],
        "drift",
    )
    add("latency-drift", [root, span(2, 1, "vendor/one", 10, 700)], "drift")
    add(
        "parallel-ambiguity",
        [root, one, span(3, 1, "vendor/two", 50, 150)],
        "inconclusive",
    )
    add(
        "nested-route-ambiguity",
        [root, span(4, 1, "vendor/two", 5, 105), {**one, "parentSpanId": f"{4:016x}"}],
        "inconclusive",
    )
    add("scope-not-selected", [root, one], "inconclusive", scope="unknown-instrumenter")
    add("entrypoint-drift", [root, two], "drift")
    add("internal-inference", [root, {**one, "kind": 1}], "inconclusive")
    add(
        "privacy-sentinel",
        [
            root,
            {
                **one,
                "attributes": one["attributes"]
                + [
                    {
                        "key": "gen_ai.input.messages",
                        "value": {"stringValue": "PRIVATE_PROMPT_AND_SECRET"},
                    }
                ],
            },
        ],
        "observed-no-drift",
    )
    return {
        "schema_version": 1,
        "suite": "synthetic-otlp-v1",
        "seed": 20261009,
        "cases": cases,
    }


def run_trace_benchmark(data: dict) -> dict:
    if (
        data.get("suite") != "synthetic-otlp-v1"
        or data.get("schema_version") != 1
        or data.get("seed") != 20261009
    ):
        raise ValueError("expected versioned synthetic OTLP corpus")
    if not isinstance(data.get("cases"), list) or not 1 <= len(data["cases"]) <= 256:
        raise ValueError("expected 1 to 256 authored trace cases")
    results = []
    for case in data["cases"]:
        if (
            not isinstance(case, dict)
            or not {"name", "expected", "policy", "profile", "trace", "bindings"}
            <= set(case)
            or not isinstance(case["name"], str)
            or not ALIAS.fullmatch(case["name"])
            or case["expected"] not in ("observed-no-drift", "drift", "inconclusive")
            or any(
                not isinstance(case[key], dict)
                for key in ("policy", "profile", "trace", "bindings")
            )
        ):
            raise ValueError("invalid authored trace case")
        report = audit_traces(
            policy_from_data(case["policy"]),
            profile_from_data(case["profile"]),
            case["trace"],
            case["bindings"],
        )
        actual = report["requests"][0]["verdict"]
        # Deliberately naive baseline: any semantic operation or LLM label is a call,
        # then only compare count with budget. It can't represent inconclusive exports.
        raw_spans = [
            s
            for r in case["trace"]["resourceSpans"]
            for sc in r["scopeSpans"]
            for s in sc["spans"]
        ]
        count = sum(
            any(
                a["key"] == "gen_ai.operation.name"
                and a["value"].get("stringValue")
                in {"chat", "generate_content", "text_completion"}
                or a["key"] == "openinference.span.kind"
                and a["value"].get("stringValue") == "LLM"
                for a in s["attributes"]
            )
            for s in raw_spans
        )
        baseline = (
            "drift"
            if count > case["profile"]["contracts"][0]["max_attempts"]
            else "observed-no-drift"
        )
        results.append(
            {
                "case": case["name"],
                "expected": case["expected"],
                "observed": actual,
                "baseline": baseline,
                "naive_count": count,
                "report": report,
            }
        )
    return {
        "schema_version": 1,
        "suite": "synthetic-otlp-comparison-v1",
        "seed": data["seed"],
        "cases": len(results),
        "correct": sum(r["observed"] == r["expected"] for r in results),
        "baseline_correct": sum(r["baseline"] == r["expected"] for r in results),
        "results": results,
    }


def render_trace_benchmark_svg(result: dict) -> str:
    width = result["cases"] * 40
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 320" role="img" aria-labelledby="title">
<title id="title">Synthetic observed trace contract comparison</title><rect width="960" height="320" rx="16" fill="#101827"/>
<g font-family="system-ui,sans-serif" fill="#e2e8f0"><text x="30" y="48" font-size="25">Labels are not a fallback contract</text>
<text x="30" y="85" font-size="16">Authored OTLP fixtures: routing, latency, nesting, missing evidence and privacy.</text>
<text x="30" y="135" font-size="17">Count-only</text><rect x="200" y="110" width="{result["baseline_correct"] * 40}" height="36" fill="#fb923c" rx="5"/>
<text x="{220 + result["baseline_correct"] * 40}" y="135" font-size="17">{result["baseline_correct"]}/{result["cases"]}</text>
<text x="30" y="195" font-size="17">Trace contract</text><rect x="200" y="170" width="{result["correct"] * 40}" height="36" fill="#5eead4" rx="5"/>
<text x="{220 + width}" y="195" font-size="17">{result["correct"]}/{result["cases"]}</text>
<text x="30" y="250" font-size="16">A logical inference span may include retries. Missing spans can hide drift.</text>
<text x="30" y="281" font-size="14">Not a provider benchmark, actual billed cost, complete telemetry or production-safety proof.</text></g></svg>'''
