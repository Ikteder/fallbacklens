# Decision: keep auditing static and metadata explicit

Date: 2026-09-30

## Context

Provider catalogs, prices, retention terms, model context limits, and structured-output capabilities change. Automatically scraping those values would make a supposedly reproducible audit depend on live mutable data and could create false confidence.

## Decision

FallbackLens imports route structure from LiteLLM YAML but requires an operator-owned JSON profile for capability, context, price, latency, privacy, and workload-contract facts. Every profile carries `as_of` and `sources` fields. Unknown values produce warnings and block claims that depend on them.

Cost and latency are reported as conservative configured exposure under declared token and p95-latency assumptions. They are not bills or SLO predictions.

## Consequences

- CI remains deterministic and free of provider credentials.
- Reviews can diff policy facts independently from gateway configuration.
- Operators must maintain the sidecar when models or provider terms change.
- Live fault injection and provider-specific validation remain separate work.
