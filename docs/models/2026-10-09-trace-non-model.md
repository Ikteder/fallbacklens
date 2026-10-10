# Trace audit model non-use card

2026-10-09, FallbackLens0.2, Python3.10+, PyYAML6, deterministic typed rules and JSON.
No LLM, embedding, paid provider, model weights, inference API, token usage or training.
Actual provider costUSD0.00. Synthetic aliases do not name a real evaluated model.

Intended use: offline debugging of operator-bound LLM routing trace exports. Non-goals:
production safety proof, full telemetry coverage, provider-attempt count, actual billing,
model output correctness, retention compliance or replacing observability backends.
Mapping/scope/clock assumptions and nested-wrapper heuristic can misrepresent a real
deployment. Missing or sampled spans can hide drift. Do not upload private traces to
GitHub for reproduction. Keep raw inputs local; reports minimize but do not sanitize
the original files. See decision and dataset cards for bounded supported export shape.
