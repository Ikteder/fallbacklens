# Synthetic OTLP contract corpus v1

Authored2026-10-09, seed20261009, MIT under this repository. No customer data, provider
response, prompts, credentials or third-party trace exports. PRIVATE_* values are
deliberate synthetic privacy sentinels, not real secrets. Generator:
../../scripts/generate_trace_evidence.py; corpus ../../benchmarks/trace-cases-v1.json.

16 cases:4 no-observed-drift,5 drift,7 inconclusive. Cases cover serial fallback, duplicate
instrumentation heuristic, agent workflow mislabeled LLM, flattened SERVER, unknown
model, parent gap, excessive logical calls, repeated group calls, unconfigured transition,
long latency, parallel order ambiguity, nested different groups, excluded scope,
incorrect entrypoint, unsupported INTERNAL inference and privacy sentinels.

Fixtures bind one root each and use tiny single-clock nanosecond intervals. Labels were
written before evaluation in the authored generator. No training, fitting, calibration,
split, leakage-free holdout or independent prevalence estimate. Same author designs
checks and fixtures; perfect score is regression evidence only. No provider attempt,
capability, bill, retention, quality or production telemetry claim.

Count-only baseline counts all recognized semantic operations or LLM labels, regardless
of kind, scope, ancestry, mapping, routing or latency; threshold is contract.max_attempts.
It cannot represent inconclusive exports. This is a narrow pedagogical comparison,
not a benchmark of LiteLLM, Langfuse, OpenInference or OTel reference implementations.
