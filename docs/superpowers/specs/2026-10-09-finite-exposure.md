# Reject non-finite assumptions and exposure overflow

Approved2026-10-09 before implementation. Manual continuation, seed20261009 focus2,
existing-project patch0.3.1, no new weighted draw. User: LLM gateway operators using
offline contract audit in CI. Real local failure:0.3 accepted NaN cost/latency budgets
and NaN primary latency, reported0errors/0findings and max_latency_ms NaN. This can
silently disable budget comparisons and emit JSON that independent consumers reject.

Existing LiteLLM/Langfuse/OpenInference/OTel comparisons and source/license/activity
review remain current from this run. Additional primary comparison:

| System | Verified numeric behavior | Application gap |
|---|---|---|
| Python3.14 json | [official docs](https://docs.python.org/3.14/library/json.html): default accepts/encodes NaN and Infinity; parse_constant allows rejection | Decoder success does not validate finite workload assumptions; huge exponent can overflow independently |
| YAML1.2/PyYAML6.0.3 safe loader | [spec](https://yaml.org/spec/1.2.2/#10213-floating-point): .nan/.inf are legitimate float values; safe loader blocks object construction, not non-finite scalars | Validate application numeric fields after both YAML and JSON parsing |
| Pydantic | [FiniteFloat](https://pydantic.dev/docs/validation/latest/api/pydantic/types/#finitefloat) explicitly separates finite values from generic/non-negative floats | Useful validation pattern, not reason to add a new runtime dependency |

[RFC8259 section6](https://www.rfc-editor.org/rfc/rfc8259#section-6) excludes NaN/Infinity
and permits implementation range limits. No primary claims imply Pydantic/gateway bugs.
No reference code copied; independent MIT patch, existing PyYAMLMIT unchanged.

Scope: require finite non-negative optional price/latency facts and required cost/latency
limits; null remains allowed only for optional facts. Reject JSON non-standard constants
explicitly. Huge integer-to-float conversion must raise ValueError, not crash. Guard
derived cost/latency multiplication and accumulation against overflow/non-finite results;
return input error before success report, do not clamp to budget or infer safe.

Acceptance:5 numeric fields x4 invalid cases(NaN,+inf,-inf,10**400) reject with ValueError;
finite zero/positive and optional null continue; JSON/YAML file paths and CLI invalid
exit2 produce no success artifacts; finite-input arithmetic overflow rejects; original
static10/10, trace16/16, replay2/2 and optional integration remain. Preserve historical
results and record old0.3 behavior with its clean wheel, not a hypothetical baseline.
Full core suite, package/clean wheel, current public CI and evidence documents required.

Originality: closes measured false safety and improves interoperable, content-free
error handling without changing routing or rebuilding validation frameworks. Bounds use
binary64, not exact currency/decimal finance arithmetic or an SLO. Graph-size/duplicate
key hardening and domain-specific precision remain separate, explicitly unimplemented.
