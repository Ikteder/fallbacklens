# Model card: no trained model used

Date: 2026-09-30

FallbackLens 0.1 does not train, download, or call a machine-learning model. Audit results come from deterministic graph algorithms, declared metadata, arithmetic exposure bounds, and scenario replay.

## Intended use

Pre-deployment review and CI regression testing for LLM fallback policies.

## Non-goals

- Predicting answer quality or task success.
- Inferring model capabilities from names.
- Replacing live provider or gateway testing.
- Establishing legal, privacy, or regulatory compliance.

## Risks

The main risk is false confidence from incomplete or stale operator metadata. Unknown values are surfaced, and documentation explicitly limits what a passing audit means.

## Providers and cost

No provider was called. Actual provider cost for development and verification was USD 0.00.
