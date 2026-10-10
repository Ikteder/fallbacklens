# FallbackLens 0.2 observed trace contracts

Approved 2026-10-09 before implementation, user's sustained project-work authorization.
Primary research and comparison: ../../notes/2026-10-09-trace-reference-review.md.

## Impact gate

User: LLM gateway operators already maintaining fallback policies and workload budgets.
Problem: static policy checks cannot show actual deployed route/latency divergence;
naive span counting can mistake agent steps or nested instrumenters for model calls.
Current evidence: primary LiteLLM tracing source, Langfuse OTLP integration, OpenInference
issue and proposed test fix, current OTel logical-span retry semantics. Original value
in policy/runtime reconciliation and privacy/ambiguity handling. Finishable local CLI
slice, no new service, no paid dependency, existing MIT project. No code copied.

## Interface and boundaries

Add `trace-audit CONFIG --profile PROFILE --trace OTLP_JSON --bindings BINDINGS`
with JSON and static HTML output. Bindings schema1: operator provenance date, instrument
scope allowlist, request-model to configured-group map, and explicit trace/root/contract
bindings. Identifiers are validated; arbitrary raw telemetry names, events, content,
resource attributes, error messages, trace/span IDs and request-model values are not
exported. Only trusted logical contract/group aliases and relative times leave the parser.

Read bounded10MB OTLP/HTTP JSON resourceSpans/scopeSpans/spans, max2000 spans; string
nanosecond timestamps, hexadecimal identifiers, typed string semantic attributes.
Reject duplicate span/attribute IDs, impossible duration/containment, cycles, malformed
shape, unsafe sizes/nonfinite JSON, ambiguous duplicate/overlapping root bindings.
Selected roots may have an unexported external parent. Other gaps within a bound trace
produce inconclusive results. Restrict inference to CLIENT and chat/generate_content/
text_completion operations from explicitly selected instrumentation scopes. INTERNAL
local inference and legacy flattened SERVER attributes are unsupported and inconclusive
when no supported calls exist. Missing/unknown mappings are inconclusive, never success.

Suppress nested inference wrappers only when descendant aliases agree; differing nested
aliases make interpretation inconclusive. Leaf-most observed spans represent logical
inference calls, not provider attempts. Compare call-count threshold against contract's
max_attempts as an observed logical-call diagnostic with this explicit caveat. Observe
inference envelope latency and compare max_latency_ms; this is not a p95 or hard bound.
Check initial entrypoint and serial configured transitions; repeated aliases can be
retries, bounded by configured retries+1 per visit. Parallel overlap makes route-order
checks inconclusive rather than fabricated. Union fallback types allowed, no assertion
that a particular error triggered the correct fallback kind/order.

Verdicts: observed-no-drift, drift, inconclusive. No production-safe, exact billed cost,
complete export, provider attempt, quality, ZDR, or capability proof. Missing sampled
spans can hide failures. Static audit stays independently available.

## Acceptance and baseline

Preserve all15 existing tests. New authored corpus covers normal fallback, nested same
model wrappers, workflow mislabeled LLM, SERVER-only, unknown model, missing parent,
excess calls/retries, unsupported transition, long latency, parallel calls, incompatible
nested aliases, duplicate spans, scoped exclusion and privacy sentinels. Compare with
naive count-all-semantic-spans baseline on a fixed versioned corpus; measure, don't
preclaim scores. JSON/HTML must omit content, names, IDs and unmapped values. CLI exits
0 no observed drift,1 drift or inconclusive,2 invalid input. Package build/clean install,
Ruff, compilation, dependency audit, existing benchmark/replay, generated evidence visual
and browser narrow/desktop QA, existing public Python3.10/3.12/3.14 CI are publication gates.

## Non-goals and publication

No exporter SDK, live endpoint, cloud credentials, actual provider/model execution,
telemetry upload, hosted observability product, new random draw, or upstream PR. Synthetic
MIT-owned data only, actual provider costUSD0.00. Small typed modules, documented bindings
and privacy policy, dated dataset/model/evaluation/decision notes, README and catalog.
Publish intentionally to existing https://github.com/Ikteder/fallbacklens after verification.
