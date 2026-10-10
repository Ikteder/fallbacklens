# Actual instrumentation, synthetic inputs

Captured2026-10-09 from local LiteLLM1.104.2 and OTelSDK1.45.1 under owned mock fixture,
MIT authored test inputs, Apache2 OTel encoder used as installed dependency, MIT LiteLLM
core dependency. Nine captures, three configurations repeated3times. No third-party
trace data or code copied. Raw inputs/responses, IDs and times are generated locally;
no real provider or customer. EvidenceJSON contains minimized report, package versions,
span kinds/scopes and counted mocked requests, not actual prompts or raw identifiers.

No train/test split, statistical sample, holdout, independence or adoption claim.
This independently exercises SDK emissions instead of authoring every span directly,
but its synthetic workload and expected verdicts remain implementation-aligned.
No gateway Router or provider retries exercised. Only pinned versions/configurations.
Keep real telemetry private; new captures require explicit permission and redaction.
