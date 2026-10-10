# LiteLLM instrumentation interoperability

2026-10-09 America/Denver, seed20261009, Windows Python3.14.7. Actual LiteLLM1.104.2
callback, OTelSDK1.45.1, official OTLPJSON encoder0.66b1, respx0.23.1. Exact request model
string gpt-4.1-mini, fully authored mocked responses. No real OpenAI or other provider
called, actualUSD0.00. The transitive OpenAI SDK2.54.0 handled mock HTTP, not inference.

```
python -m pip install -e '.[interop]'
fallbacklens interop-run --repetitions 3 --output artifacts/trace-interop-final
python scripts/export_interop_evidence.py artifacts/trace-interop-final/report.json
python -m unittest discover -s tests -v
python -m unittest discover -s integration_tests -v
python -m pip check
python -m pip_audit
```

Initial run started before optional install finished: ModuleNotFoundError litellm,
local diagnostic retained, not a failed provider request or passing test. After install,
all three single cases matched. Final repeated actual instrumentation9/9 expectedmatches.
Base safety/core suite initially43 passed in1.248s, including credential/export environment
allowlist, DNS/connect/connect_ex denial/restoration, existing output preservation,
invalid repetitions and previous39 tests. Dependency consistency and vulnerability
audit passed including installed optional deps, with cache warnings and local-project skip.

| Configuration | Actual emitted spans, each of3 repetitions | Verdict |
|---|---|---|
| experimental + dedicated | CLIENT1, SERVER1 | observed-no-drift |
| legacy + dedicated | INTERNAL2, SERVER1 | inconclusive |
| experimental + collapsed | SERVER1 | inconclusive |

Every case had exactly1 respx-intercepted HTTP request, no external connect attempt,
no allowed outbound TCP connection, no external exporter, no inherited provider/export
credentials. In-memory callbacks completed under bounded event waits before ending the
root. Official encoder produced parser-compatible typed attributes, string timestamps
and hexadecimal IDs. Minimized reports omit rawIDs, prompts and fixture key; raw SDK
exports are synthetic local-only artifacts, not published. No upstream source copied.

This checks a mocked SDK completion and three tracing settings, not the live Router,
actual fallback dispatch, streaming, retries, independent customer traces, billed
tokens/cost, real model output or all release compatibility. Span IDs/times vary across
fresh processes; verdicts/counts are reproducible. A logical span can contain retries.
Runtime depends on optional packages; base installation remains PyYAML-only.

Separate optional integration test passed in33.917s (three fresh mocked workers).
Source and wheel0.3.0 build passed. Clean base wheel installation passed all43 then
current tests without LiteLLM installed, pip consistency and16/16 trace cases. Final
45 tests passed in1.198s. Timeout regressions preserve a content-free failure receipt
without a partial success report. Desktop1265px and narrow375px report had9 rows and no page overflow; the narrow
table scrolls internally. No claim about zero browser-console errors on reused QA tabs.
Published source2a983eec78b1c52d513de9901afe55cc30fe8c79 and workflow
52313b7caec2c609be1930d85d66267814ac3bc2. Public
[CI38017289936](https://github.com/Ikteder/fallbacklens/actions/runs/38017289936)
passed allthree base Python3.10/3.12/3.14 jobs and the separate Python3.12 optional job:
actual mocked integration test, CLI three-case run, dependency audit and package build.
Final revised clean no-LiteLLM wheel passed45 core tests. Remote SHA verified before
the subsequent finite-assumption patch. This is compatibility evidence only for the
pinned settings, not all versions or provider reliability.
