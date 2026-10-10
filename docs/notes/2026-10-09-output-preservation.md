# One CLI preservation boundary

2026-10-09. Actual old clean wheel overwrote only disposable copies, confirmed two
zero-exit data-loss/conflicting-format cases. Shared guard precedes parsing in all
five file-reading commands. Specific guard-message assertions ensure invalid sentinels
do not pass merely due to later parser rejection. Existing hard links and normalized
parent aliases passed negative tests. Windows symbolic-link case skipped for missing
creation permission; hosted Unix CI will exercise it if supported, not preclaimed.

No customer files copied or exposed. Standard-library path logic, no new dependencies,
no paid APIs or models, USD0.00. Direct writer misuse and filesystem races remain out
of scope. Keep permission checks, input integrity and report generation distinct.
