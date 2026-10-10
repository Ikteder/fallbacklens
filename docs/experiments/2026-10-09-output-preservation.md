# Preserve CLI input and report bytes

2026-10-09, seed20261009, Python3.14.7, same manual continuation, costUSD0.00.
Primary path identity documentation and current three-system research recorded in spec.

Actual clean wheel0.3.1ran scripts/output_regression.py only on disposable temp copies.
audit-input:exit0,input_preserved=false. audit-output-collision:exit0,input preserved,
output_created=true; JSON report had been replaced by HTML.0/2controlled rejections.
No user/project source input was overwritten during these reproductions.

Current script:2/2controlled rejections,exit2,input preserved in both; duplicate-output
case creates no new report.61 core tests ran1.251s:60passed,1real symlink test skipped
because Windows lacks symbolic-link creation permission. Hard-link tests all passed.
Separate clean base wheel61 tests ran, same skip; dependency consistency, lint,
compile and0.3.2sdist/wheel build passed. pip-audit found no known dependency advisories,
skipped local package itself. Published source2428b1edb129ed9296e75cc3fd2094df8e237ef4,
remote verified. [CI38017997193](https://github.com/Ikteder/fallbacklens/actions/runs/38017997193)
passed allfourjobs. Linux3.10/3.12/3.14 each61passed with real symlink cases, no skips;
times0.436/0.401/0.382s are runner observations, not a performance comparison. Optional
integration passed11.881s plus CLI3/3 mocked expectedmatches, actualprovidercost0.
Full mocked optional integration is
unchanged and remains independently gated. No upstream code copied or PR; independent
MIT patch. This is preflight detection, not race-free permissions or atomic multi-file IO.

```
OLD_CLEAN_WHEEL_PYTHON scripts/output_regression.py docs/experiments/output-preservation-baseline-v031.json
python scripts/output_regression.py docs/experiments/output-preservation-v032.json
python -m unittest discover -s tests -q
python -m ruff check src tests scripts integration_tests
python -m build
```

Final post-publication cross-check: the16case corpus equals its authored generator,
raw minimized evidence equals current evaluation, SVG equals current render exactly,
privacy sentinels absent. Valid distinct CLI outputs still worked: static0errors/
0warnings, configured$0.048/10000ms; replay2/2; serial trace190ms observed-no-drift.
These are synthetic assumptions/results, not actual provider prices/latency guarantees.

Final documentation mainf97813cf47fde687959b2a6e8792df041918b67d and
[CI38018169434](https://github.com/Ikteder/fallbacklens/actions/runs/38018169434) verified
allfourjobs. Subsequent verification-only report-safety test supplies script-like model,
contract/date/source labels: HTML visible text and embedded JSON remain escaped, SVG
contains no script/img element and preserves literal label text.62 local tests ran
1.395s,61passed and the same Windows symlink-permission skip. No renderer implementation
change; no claim of a complete XSS audit or protection from hostile report dictionaries.
