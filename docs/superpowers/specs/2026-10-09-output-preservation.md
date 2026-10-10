# Preserve audit inputs and distinct reports

Approved2026-10-09 before implementation, manual continuation seed20261009 focus2.
Same-day primary LiteLLM/Langfuse/OpenInference/OTel comparison remains current. Local
CLI source: trace-audit checks resolved names; older audit/simulate/benchmark and
trace-benchmark can overwrite supplied inputs or another report. Hard links bypass
resolved-name comparison. User: gateway operator iterating on costly authored policy,
profile and regression evidence. Preserve exact bytes, not just a path spelling.

Primary [Python3.14 Path](https://docs.python.org/3.14/library/pathlib.html#pathlib.Path.samefile)
and [samefile](https://docs.python.org/3.14/library/os.path.html#os.path.samefile) docs
support resolved symbolic paths plus existing file identity on Windows and Unix.
No copied code, no new dependency, independent MIT patch0.3.2. Existing project standard
source/license/contribution review and AppliedML identity/reconciliation framing apply.

Scope: one shared CLI preflight before reading/evaluating/writing. Every input field
and enabled output field participate. Reject resolved aliases and existing hard links,
and collisions among outputs. interop exclusive fresh directory stays unchanged.
Exit2 and preserve input/output bytes on rejection. Ordinary distinct reports and
explicit replacement of unrelated existing reports remain allowed.

Acceptance: actual old clean wheel reproduces audit-input overwrite and JSON/HTML
collision only in disposable synthetic temp fixtures. Shared guard tests all five
file-reading commands, duplicate outputs, dot/resolved aliases, existing input/output
hard links, fresh valid outputs. Preserve core/trace/static/replay/mock integration,
package, clean install, documentation and public CI.

Original value: protects authored policies and portable evaluation provenance while
making command behavior consistent; extends compatible project rather than inventing
a filesystem framework. Not race-free authorization: hostile concurrent symlink/link
changes between preflight and write, arbitrary filesystem writes, multi-artifact atomic
publication and caller misuse of low-level report writers remain outside this slice.
