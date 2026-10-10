# Actual LiteLLM instrumentation, mocked inference

Approved2026-10-09 before implementation, sustained manual-work authorization.
Same seed20261009/focus2. FallbackLens0.2 public CI passed; extend its documented
independent-export gap with actual SDK instrumentation, not another synthetic span builder.

## Evidence and gap

Original comparison remains current: LiteLLM v1/v2 tracing source/docs, Langfuse OTel
and attribute enum, OpenInference workflow classification issue/proposed tests, OTel
relocated logical/client inference conventions and reference scenario. Additional source:
LiteLLM tests/unit/integrations/test_opentelemetry_request_spans.py uses mocked httpx
with respx plus an injected in-memory exporter; gen_ai_semconv.py explicitly sets CLIENT
only under gen_ai_latest_experimental. Official OTel Python trace_encoder exposes
encode_spans; JSON common package0.66b1 and SDK1.45.1 verified in PyPI on2026-10-09.
Current OTel reference LiteLLM scenario manually authors semantic spans around mocked
calls, so it does not independently validate LiteLLM's own callback hierarchy.

## Scope and safety

Add an optional pinned interoperability extra: LiteLLM1.104.2, OTelSDK1.45.1,
OTLPJSONcommon0.66b1, respx0.23.1. Keep base runtime and39 tests free of these dependencies.
Authored script runs each case in a fresh worker with a narrowly allowlisted environment,
no inherited provider credentials/export settings. Use synthetic messages/responses and
explicit fixture.invalid API base with fake fixture key. respx must reject all unmocked
httpx requests, disable aiohttp, block non-loopback socket connect/connect_ex/DNS before
imports, use bundled model-cost map. No external exporter; in-memory only. This is
network-denial testing, not an OS/filesystem sandbox. Never call a real model/provider.

Cases: latest-experimental dedicated request span => observed-no-drift, legacy dedicated
INTERNAL span => inconclusive, latest-experimental collapsed SERVER root => inconclusive.
Explicit gateway SERVER root binds the request; scope from actual emitted instrumenter.
Wait for callback completion with a bounded event rather than sleeps. Flush and end root,
encode ReadableSpan objects with official OTLPJSON encoder; preserve synthetic raw JSON
locally and publish only data-minimized evidence, exact dependency/date/cost records.
Record emitted kinds/counts and ambiguity, not fabricated provider attempts.

Acceptance: each three-case run repeated3times,9 expectedmatches, declaredmockrequests
exactly1 each, no external socket allowed, zero actualpaidcalls. Do not preclaim counts
or support if current pinned callback lacks the assumed shape: inspect and document.
Base39tests remain, add safe optional-extra CLI/safety tests, exact output-preservation
checks. Package/clean install, lint/compile/dependency audit, base CI plus optional
Python3.12 interoperability CI gate. MIT local extension, no upstream copy/PR/acceptance.
If latest dependency has advisories, inspect and adjust pins or don't ship that integration.

## Originality and limits

Adds exact versioned instrumentation evidence and executable negative compatibility
examples to existing policy/runtime/privacy work. One mocked completion is not real
gateway Router fallback execution, provider retry observability, production data,
compatibility with all releases, streaming behavior or external collector conformance.
No company benchmark reproduced, no paid provider, actualUSD0.00.
