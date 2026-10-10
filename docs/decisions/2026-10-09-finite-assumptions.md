# Finite assumptions are an application contract

2026-10-09. Reject non-finite and non-representable profile numbers with ValueError
at ingestion for both YAML and JSON. Keep optional null for missing price/latency;
required budget null remains invalid. JSON NaN/Infinity extension literals are rejected
explicitly, and exponent overflow is caught by field validation. Do not add Pydantic
just for this rule or equate safe YAML object construction with domain validation.

Arithmetic also guards non-finite accumulated exposure and integer conversion overflow.
Fail closed as input error, never clamp or emit a passing audit with infinity/NaN.
The evaluator uses binary64 and may reject huge finite inputs whose intermediate
products overflow, even if algebraic reordering would fit. No exact-currency claim.
Independent graph-size, duplicate-key and domain-precision work is intentionally separate.
