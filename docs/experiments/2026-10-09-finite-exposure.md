# Finite numeric assumptions

2026-10-09 America/Denver, seed20261009, Python3.14.7, PyYAML6.0.3, no models,
paid provider costUSD0.00. Approved spec includes primary reference comparison.

Before patch: modified safe profile with NaN budgets and primary latency. Actual0.3
audit returned errors0, codes[],max_cost_usd0.048,max_latency_msNaN. That is silent
false safety for invalid assumptions, not evidence of a breached real provider budget.

```
OLD_CLEAN_WHEEL_PYTHON scripts/numeric_regression.py docs/experiments/finite-assumptions-baseline-v03.json
python scripts/numeric_regression.py docs/experiments/finite-assumptions-v031.json
python -m unittest discover -s tests -q
fallbacklens benchmark benchmarks/policy-cases-v1.json --json artifacts/benchmark031.json
fallbacklens trace-benchmark benchmarks/trace-cases-v1.json --json artifacts/trace031.json
fallbacklens simulate examples/litellm-safe.yaml --scenarios examples/scenarios.json --json artifacts/replay031.json
```

| Installed evaluator | Controlled invalid-input rejection | Invalid accepted | Uncontrolled overflow |
|---|---:|---:|---:|
| Actual clean wheel0.3.0 |5/20|10/20|5/20|
| Revised0.3.1 |20/20|0/20|0/20|

Initial53tests passed1.224s; final55passed1.058s, including latency huge retry conversion
and CLI finite arithmetic overflow with no success output. Separate mocked actual SDK
integration passed34.230s. Original static10/10vs2/10, trace16/16vs3/16, replay2/2 stayed
green. Ruff/compile/dependency consistency/vulnerability audit and0.3.1sdist/wheel build
passed; pip-audit skipped local project, found no known dependency advisories.
Fresh clean base wheel passed55 tests, pip consistency and20/20 numeric rejection
cases without LiteLLM installed. Public CI recorded after completion. Corpus is authored,
implementation-aligned and small, no real traffic.
Binary64 range/precision, intermediate product overflow and other graph/input limits
remain explicit boundaries. No upstream code copied, no PR or acceptance claim.
