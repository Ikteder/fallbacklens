# FallbackLens 0.1 verification

Date: 2026-09-30

Environment: Windows, Python 3.14.7, PyYAML 6.0.3. All model and provider behavior is synthetic.

## Commands and outcomes

| Check | Command | Result |
|---|---|---|
| Unit and integration tests | `.venv/Scripts/python -m unittest discover -s tests -v` | 15/15 passed |
| Lint | `.venv/Scripts/python -m ruff check src tests` | Passed with 0 findings |
| Dependency consistency | `.venv/Scripts/python -m pip check` | No broken requirements |
| Dependency vulnerability audit | `.venv/Scripts/python -m pip_audit` | No known vulnerabilities in auditable dependencies; local `fallbacklens` package was skipped because it is not on PyPI |
| Package build | `.venv/Scripts/python -m build` | Source distribution and 21,957-byte universal wheel built without warnings |
| Isolated wheel smoke test | fresh virtual environment plus the built wheel | Installed with PyYAML 6.0.3; benchmark reproduced 2/10 baseline and 10/10 FallbackLens |
| Safe audit | `fallbacklens audit examples/litellm-safe.yaml --profile examples/profile-safe.json` | 0 errors, 0 warnings |
| Risky audit | same command with `litellm-risky.yaml` and `--fail-on never` | `FALLBACK_CYCLE` and `UNBOUNDED_ROUTE` |
| Failure replay | `fallbacklens simulate ...` | 2/2 scenarios matched expectations |
| Comparison | `fallbacklens benchmark benchmarks/policy-cases-v1.json` | FallbackLens 10/10; baseline 2/10 |

## Safe-demo exposure

- Model groups: 3
- Fallback edges: 4 across general, context-window, and content-policy routes
- Terminal paths from `agent-primary`: 2
- Configured retries: 1 per group
- Longest-path attempt exposure: 6
- Conservative cost exposure: USD 0.048000
- Conservative p95-latency exposure: 10000.0 ms

The values use the synthetic dated profile. They are not a bill or SLO prediction.

## Browser QA

The standalone safe-audit HTML was served over loopback and inspected in Chrome.

| View | Result |
|---|---|
| Desktop, 1280-class capture | Three summary cards, contract table, findings table, and interpretation note rendered without clipping |
| Narrow, 390 by 844 | Summary cards stacked to one column; `document.body.scrollWidth` equaled `document.documentElement.clientWidth` at 375 CSS pixels; wide table scrolled inside its container |
| Console | 0 warnings and 0 errors |
| Benchmark SVG | Rendered labels, bars, 2/10 baseline, 10/10 FallbackLens, and synthetic-evidence disclaimer |

## Uncertainty

The corpus is implementation-aligned and synthetic. Browser coverage used one local Chrome environment. Hosted Python-matrix results are recorded separately only after a public CI run completes.
