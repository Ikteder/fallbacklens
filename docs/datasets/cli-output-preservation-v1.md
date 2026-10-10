# CLI output-preservation fixtures

Authored2026-10-09, MIT. Two actual old-wheel demonstrations use disposable synthetic
copies of the safe policy/profile: audit JSON overwrites its input profile; identical
JSON/HTML output leaves HTML at the requested JSON path. Old0.3.1returned0 in both.
Current shared guard expects exit2, original bytes preserved, no new collision output.

Additional unit cases cover every input of five commands, four dual-output commands,
all five commands through a hard-link input alias, hard-link outputs, parent components
and a real symlink when platform permissions permit. Sentinel invalid input ensures
the specific preflight error occurs before parsing, not accidental parser rejection.
Existing valid audit/trace/corpus/replay tests retain ordinary output support.
No customer files, provider traces, model data, train/test split or external dataset.
