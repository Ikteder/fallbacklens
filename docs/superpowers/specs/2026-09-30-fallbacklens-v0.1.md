# FallbackLens 0.1 implementation spec

Date: 2026-09-30

Status: Approved for this scheduled run after current reference review.

## Problem and user

AI platform engineers configure retries and fallbacks across model groups, but configuration syntax alone does not show whether the resulting route graph is finite or whether a fallback silently violates tool-calling, structured-output, context, privacy, latency, or cost requirements. The intended user is an engineer reviewing a LiteLLM deployment or a provider-neutral routing policy before rollout.

## Evidence-based gap

LiteLLM, Portkey Gateway, OpenRouter, and RouteLLM all provide routing or fallback execution. LiteLLM's current `Router.validate_fallbacks` implementation at commit `50f5cc9bbb55bacecd3c0f07623566df6a04e1df` verifies only that each entry is a one-key dictionary. LiteLLM issue 35303 reports a four-node cycle contributing to 79,858 attempts from one malformed request on version 1.93.0. The issue is closed as a duplicate, so this project does not claim the runtime remains vulnerable in every current path. The current source still does not reject cyclic fallback configuration in `validate_fallbacks`.

The chosen gap is offline policy verification, not another gateway: import a LiteLLM YAML route graph, join it with explicit operator-owned model metadata and contracts, identify unsafe paths, calculate conservative exposure bounds, and replay deterministic failures without provider calls.

## Scope

- Parse LiteLLM YAML `model_list` plus general, context-window, and content-policy fallback lists.
- Accept a JSON sidecar with model capabilities, context windows, zero-retention declarations, per-million-token prices, p95 latency assumptions, and workload contracts.
- Detect malformed edges, missing nodes, self-loops, multi-node cycles, and unreachable groups.
- Check every reachable fallback target against required capabilities, context, and zero-retention requirements.
- Calculate conservative configured attempt, cost, and p95-latency exposure on finite paths.
- Replay versioned failure scenarios with a hard step bound and machine-readable traces.
- Emit JSON, terminal, standalone HTML, and a generated SVG evidence visual.
- Keep all verification offline; no provider credential or paid API is required.

## Non-goals

- Proxying requests or replacing a gateway.
- Predicting response quality.
- Discovering provider prices or capabilities automatically.
- Exactly emulating every version-specific retry path in LiteLLM.
- Claiming a policy is production-safe from static analysis alone.

## Acceptance tests

1. The valid demo has no error findings and its deterministic outage scenario reaches the declared terminal model.
2. A cyclic graph is rejected and scenario replay terminates at the configured safety bound.
3. Capability, context, privacy, missing-node, attempt, cost, and latency regressions are reported with stable codes.
4. The benchmark evaluates ten versioned cases. FallbackLens must classify all ten as expected and outperform the documented shape-only baseline.
5. JSON and HTML reports agree on summary counts; the generated SVG is valid XML and reproducible byte for byte.
6. Unit and CLI integration tests pass on Python 3.10+ without network calls.
7. README, research note, decision record, dataset card, model card, experiment record, and catalog entry are complete. README contains no em dash character.

## Risks and controls

| Risk | Control |
|---|---|
| Static metadata becomes stale | Require explicit `as_of` and source fields; report unknown metadata instead of guessing. |
| Conservative bounds overstate real billed cost | Label them exposure bounds and preserve all assumptions in output. |
| LiteLLM semantics change | Record inspected commit and adapter limits; keep canonical audit model separate from loader. |
| Users interpret lint success as reliability proof | State that live fault injection and provider validation remain required. |
| Untrusted YAML creates objects | Use `yaml.safe_load` only and reject non-mapping roots. |

## Comparison baseline

The baseline accepts a fallback list when every item is a one-key object, mirroring the scope of the inspected LiteLLM validator. The benchmark measures correct case classification over a ten-case synthetic corpus. No company or upstream benchmark result is claimed as locally reproduced.

## Publication plan

Create an MIT-licensed public repository named `fallbacklens` after local tests, package build, benchmark, report consistency, visual verification, README style validation, and secret scan pass. If repository creation or push is blocked, preserve the verified local commit and report the exact setup needed.
