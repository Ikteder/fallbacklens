# Dataset card: fallback-policy-safety-v1

Date: 2026-09-30

## Summary

This is a ten-case synthetic configuration corpus for regression testing fallback-policy audits. It contains one valid policy and nine invalid policies covering malformed entry shape, a three-node cycle, an unknown target, capability drift, context-window drift, privacy drift, attempt-budget overflow, cost-budget overflow, and latency-budget overflow.

## Source and license

- Source: independently constructed for FallbackLens.
- Version: schema 1, accessed from the repository at test time.
- License: MIT with the project.
- Personal, proprietary, and production data: none.

## Schema

`base_config` is a small LiteLLM-compatible route shape. `base_profile` holds synthetic model facts and one workload contract. Each case provides deterministic patches and an `expected_valid` label.

## Labels and exclusions

Labels are specification-derived, not human annotations. A case is valid only if it has no error finding. Warning-only cases, deployment-level heterogeneity, concurrency, cooldowns, weighted routing, real provider failures, and probabilistic reliability are excluded from version 1.

## Leakage and evaluation limits

The cases were designed from the implemented rule set and are used by unit tests. This is intentional regression coverage but creates direct construction leakage. The 100% result must not be interpreted as generalization to arbitrary gateway configuration or production defect rates.

The shape-only baseline checks only whether fallback lists contain one-key objects. It is an evidence-aligned comparison with the inspected scope of LiteLLM's current `validate_fallbacks`, not a full comparison with the LiteLLM runtime.

## Quality concerns

- Small sample size.
- Synthetic and balanced toward known defects.
- One provider-neutral contract shape.
- No independent annotation or adversarial third-party cases.

## Next dataset improvement

Add independently authored configurations from multiple gateway adapters, preserve their licenses and version metadata, and include ambiguous cases that should produce warnings rather than binary failure.
