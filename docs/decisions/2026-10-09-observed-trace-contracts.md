# Bound logical-call evidence, not provider-attempt reconstruction

2026-10-09. Extend FallbackLens instead of building a gateway or hosted dashboard.
Evidence and rejected broader approaches: ../notes/2026-10-09-trace-reference-review.md.

Bindings schema1 is an operator-controlled JSON document containing `as_of`, a nonempty
`scopes` instrumentation-name allowlist, `model_groups` mapping exact request-model
strings to configured logical aliases, and `requests` containing `trace_id`,
`root_span_id`, `contract`. Example: ../../examples/trace-bindings.json. One binding is
one logical gateway invocation, not an entire multi-turn agent session. Overlapping
roots are rejected. No profile-source URLs or binding notes are exported as telemetry.

Supported OTLP/HTTP JSON shape: resourceSpans -> scopeSpans -> spans; scope.name required;
traceId32hex/spanId16hex nonzero, optional parentSpanId16hex; start/end Unix-nanosecond
decimal strings; kind integer or SPAN_KIND_* enum string. CLIENT is3, not SERVER2.
Allowlisted semantic fields use typed stringValue: gen_ai.operation.name and
gen_ai.request.model. Operations chat/generate_content/text_completion only.
Resource attributes, span names, events, status messages and other attributes are never
retained in normalized spans or exported. Sensitive raw exports still exist on disk:
this tool does not sanitize, overwrite or remove its inputs.

Hard limits:10MB per JSON document,2000 spans,64-level ancestry,128 attributes per span,
256 selected inference candidates per binding,100 roots,32 scopes,256 model mappings.
Aliases have a96character ASCII safe alphabet. Duplicate object keys, duplicate span
identities, duplicate attributes, cycles, invalid timestamps and incompatible parent
intervals reject input. This strict single-clock export assumption can reject skewed
distributed traces; don't silently repair them. Output uses relative milliseconds and
request ordinal, never raw IDs or request-model strings. User-defined logical aliases
must themselves be nonsensitive; the tool cannot infer whether a harmless-looking alias
is confidential. Generic validation errors don't echo raw telemetry values.

Same-group nested CLIENT spans are treated as instrumentation wrappers and leaf spans
selected. That is a documented heuristic, not proof of duplicate instrumentation.
Different-group nesting is inconclusive. Unknown mappings, missing parent links within
a bound trace, no supported calls, INTERNAL inference, parallel order, unknown retry
policy or malformed policy findings cannot produce observed-no-drift.

For unambiguous serial calls, compare entrypoint and transitions against the union of
configured fallback types; don't infer trigger kind, priorities or runtime scheduler
implementation. Compare logical-call count with contract.max_attempts and total observed
calls per group with retries+1 as diagnostics, not measured provider attempts or exact
LiteLLM retry semantics. Compare inference envelope max-end minus min-start with the
contract latency threshold: this is observed wall time, not sum-of-p95 predictions or
an SLO estimate. No cost estimate is produced from traces.

Verdicts observed-no-drift/drift/inconclusive, CLI0/1/1; invalid input2. Drift signals
exist only under the documented mapping/instrumentation assumptions. Missing spans can
hide failures even in observed-no-drift. Static contract audit remains a separate command.

Synthetic fixtures are own MIT data. No live backend, paid provider, model, upstream copy
or PR. OpenInference discourages unsolicited feature contributions; this is a local
extension of an already documented project gap, not an upstream classification patch.
