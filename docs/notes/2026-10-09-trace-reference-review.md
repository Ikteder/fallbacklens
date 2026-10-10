# Trace import discovery

Accessed 2026-10-09 America/Denver, manual continuation, seed 20261009, focus 2.
Existing public FallbackLens main de90a5e names trace import as its next improvement.
No new random draw: the day's original selection created ResumeProbe; this follow-on
compounds a clean existing repository under the user's sustained-work authorization.

| Reference | User and capability | Primary evidence and activity | Interface / gap | License and contribution |
|---|---|---|---|---|
| [LiteLLM](https://github.com/BerriAI/litellm) | Gateway operators, provider routing and tracing | v1.104.2 Oct 8; main active Oct 9 local; PR 45714 provider-wide fallbacks. [v1 source](https://github.com/BerriAI/litellm/blob/main/litellm/integrations/opentelemetry.py) has parent collapse / USE_OTEL_LITELLM_REQUEST_SPAN; [v2 docs](https://docs.litellm.ai/docs/observability/opentelemetry_v2) describe opt-in span trees and semantic fields. Unit-test contribution surface inspected, not run locally. | OTel CLIENT inference plus HTTP SERVER roots. A collapsed root cannot establish an observed call sequence. Don't build another gateway. | Root license MIT outside enterprise/, separately licensed enterprise. Guide requires CLA, scoped change, mocked unit tests, lint. No upstream code copied or PR. |
| [Langfuse](https://github.com/langfuse/langfuse) | Observability teams, nested generation and agent observations | v4.56.0 Oct 9; PR18567 token mapping; [OTel endpoint docs](https://langfuse.com/integrations/native/opentelemetry) support HTTP JSON/protobuf, not gRPC, evolving attribute mappings, propagated trace fields. [data model](https://langfuse.com/docs/observability/data-model) distinguishes traces and observations. Test/type/lint contribution gates inspected, not a locally reproduced benchmark. Guessed worker source path returned404, no source-compatibility claim from that path. | Use local OTLP JSON export, no Langfuse account/backend or ingestion write. Backend dashboards don't directly bind this repository's policy contracts. | MIT outside ee/web/src/ee/worker/src/ee; third-party notices separate. CLA and issue discussion before substantial changes. No copied code. |
| [OpenInference](https://github.com/Arize-ai/openinference) | Instrumentation developers, AI span attributes and conversion | vercel3.3.0 Oct 9; [issue4008](https://github.com/Arize-ai/openinference/issues/4008) and [open PR4007](https://github.com/Arize-ai/openinference/pull/4007) describe workflow spans mislabeled LLM. Inspected proposed utils/constants/test patches. Its author's live results are not reproduced here; PR was unmerged when read. | Counting every LLM label can count control-flow spans. Use explicit operations/kind/scope and ancestry instead, not vendor-specific reclassification patches. | Apache2. Guide currently discourages unsolicited feature work, requires maintainer alignment, focused tested changes, CLA. Separate local MIT extension appropriate. |
| [OTel GenAI conventions](https://github.com/open-telemetry/semantic-conventions-genai) | Instrumentation maintainers, semantic interoperability | Active Oct9 local; development-status [client inference](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/client-inference.md), [logical span semantics](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-spans.md). Old website explicitly moved here. [reference matrix](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/reference/README.md) uses deterministic local mocks and Weaver per-library compliance, not workload-contract enforcement. Issue592 token metric modality. | CLIENT recommended; INTERNAL permitted for in-process models. Retries can live inside a single logical span. This slice supports CLIENT only and never proves provider attempt counts or full trace coverage. | Apache2; guide model changes, generated docs, policy checks, reference scenarios, changelog, small PRs. No convention changes or copied code. |

[Applied ML](https://github.com/eugeneyan/applied-ml) is a discovery map, not evidence.
Today's original [Uber strong data article](https://www.uber.com/blog/strong-data/)
review motivates stable identity and end-to-end reconciliation: bind a request subtree
explicitly, then compare observed logical routes against policy instead of trusting a
span label or success status. No Uber result is reproduced. Cognee is not applicable:
no semantic memory or knowledge infrastructure is being built.

Chosen gap: privacy-minimized, bounded offline reconciliation between configured LLM
fallback contracts and operator-bound observed inference subtrees. Original dimensions:
policy-to-runtime route/latency checks, ambiguity-aware hierarchy deduplication, and
data minimization. Existing static audit stays separate. No broad performance/adoption
claim. Community telemetry fixtures remain the best follow-on validation.

Follow-up source inspection resolved the earlier guessed-path404: Langfuse
[shared OTel attributes](https://github.com/langfuse/langfuse/blob/main/packages/shared/src/server/otel/attributes.ts)
defines observation type, input/output, model and usage/cost fields. This confirms why
arbitrary Langfuse attributes must not be retained in this content-minimized importer.
No new backend compatibility or benchmark claim follows from this enum inspection.
