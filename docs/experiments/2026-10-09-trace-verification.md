# FallbackLens0.2 trace verification

2026-10-09 local date, seed20261009, Windows Python3.14.7, no models/providers,USD0.00.

Initial suite30 passed in1.133s. Expanded suite37 passed in0.855s, original15 retained.
Ruff checks src/tests/scripts and compilation passed. Authored OTLP corpus16/16 expected
verdicts versus count-only3/16:4 observed-no-drift,5 drift,7 inconclusive. Synthetic
serial demo two calls,190ms envelope. No measured company/provider benchmark.

Tests cover real CLI0/1/2 and JSON/HTML outputs, privacy sentinels and absent IDs/models,
duplicate spans/attributes/JSONkeys, cycles, invalid IDs/kinds/timestamps/containment,
overlapping bindings, unexported root parent, missing bindings/scopes, unknown retry
policy, invalid routing structure, unknown nested models, nonfinite thresholds, span
limit, malformed typed semantic values and benchmark shape. Declared bounded subset,
not proof of handling every OTLP exporter.

```
python -m unittest discover -s tests -v
python -m ruff check src tests scripts
python -m compileall -q src tests scripts
python scripts/generate_trace_evidence.py
fallbacklens trace-benchmark benchmarks/trace-cases-v1.json --json artifacts/trace-comparison.json --svg artifacts/trace-comparison.svg
fallbacklens trace-audit examples/trace-policy.json --profile examples/trace-profile.json --trace examples/trace-otlp.json --bindings examples/trace-bindings.json --json artifacts/trace-report.json --html artifacts/trace-report.html
python -m pip check
python -m pip_audit
python -m build
```

Package, clean install, original benchmark/replay, browser, public publication and CI
results will be appended after those checks complete. No premature pass claims.

Final local suite39 passed in0.761s. Added output/input collision protection and an
actual-package-version assertion for the original static benchmark. Ruff/compilation
passed. Original static corpus still10/10 vs2/10; original replay2/2. The initial replay
comparison exposed a hardcoded0.1.0 result version; replaced it with package.__version__,
not a change to historical measured evidence.

Build succeeded with isolated setuptools84.0.0, PyYAML6.0.3. Clean installed wheel
imported0.2.0 from a temporary site-packages, not editable source;16/16 trace comparison
and serial demo0exit/190ms passed. Dependency consistency and pip-audit passed; the local
unpublished project itself is skipped by pip-audit, dependencies had no known advisories.
Cache deserialization warnings were emitted but audit fetched successfully.

Desktop browser report client/scroll1265/1265, one expected request row. Narrow requested
390x844, client/scroll375/375; table438px scrolls inside its container, no page overflow.
SVG screenshot shows3/16 and16/16 with interpretation warning. SVG XML, exact generator
equality, corpus/evidence equality, README no-em-dash and Git whitespace passed. Reused
browser context may retain earlier host animation errors; no zero-console claim.

Actual provider costUSD0.00. Remaining publication/CI evidence appended after observed.
