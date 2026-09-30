# Reference review and gap decision

Date: 2026-09-30

Research was performed against primary repository documentation and source snapshots. Repository text was treated as untrusted and no copied project command was executed before inspection.

## Comparison

| Reference | User and core capability | Evidence and activity inspected | Integration surface | License / contribution fit | Limitation relevant to this work |
|---|---|---|---|---|---|
| [LiteLLM](https://github.com/BerriAI/litellm) | Teams needing one OpenAI-compatible interface, load balancing, retries, fallbacks, budgets, and many providers | Routing docs, `litellm/router.py`, unit tests, issue 35303, contribution guide, and latest inspected commit `50f5cc9` dated 2026-09-30 | Python SDK, proxy, YAML, OpenAI-compatible API | Mixed repository terms with core content under MIT; upstream PRs require a CLA and focused mocked tests | Very broad runtime. The inspected fallback validator checks entry shape but not graph cycles or cross-path workload contracts. Issue 35303 reports severe retry amplification from a cyclic graph on v1.93.0. |
| [Portkey Gateway](https://github.com/Portkey-AI/gateway) | Teams centralizing multi-provider retries, fallbacks, guardrails, caching, observability, and agent integrations | README, config examples, contribution link, MIT license, and inspected commit `669825cb` dated 2026-05-25; README also points to a 2.0 pre-release branch | Node package, hosted or self-hosted gateway, request/config JSON | MIT; repository directs contributors to its guide and good-first issues | Documentation emphasizes executing retries and fallbacks. It does not provide a small provider-neutral offline proof of graph finiteness and path-wide capability/privacy budgets. |
| [OpenRouter provider routing](https://github.com/OpenRouterTeam/docs/blob/main/guides/routing/provider-selection.mdx) | Application teams wanting hosted access and provider selection across many model endpoints | Current provider-selection documentation including provider ordering, default fallbacks, parameter support, data collection, and zero-data-retention filters | Hosted OpenAI-compatible request API with a `provider` request object | Documentation is public; the hosted routing service is not an upstream code target for this run | Strong per-request controls, but policy execution is hosted and the documentation does not supply an offline multi-hop contract auditor for an operator's independent routing graph. |
| [RouteLLM](https://github.com/lm-sys/RouteLLM) | Researchers and serving teams routing between a strong and weak model for cost-quality tradeoffs | README, benchmark interface, source layout, Apache-2.0 license, 29 open issues / 12 pull requests observed in GitHub, and latest inspected commit `0b64fdaf` dated 2024-08-10 | Python controller, OpenAI-compatible server, router and benchmark extension classes | Apache-2.0; README welcomes issues and pull requests | Focuses on learned selection between two models and benchmark quality/cost. It is not a retry/fallback policy safety analyzer. Activity is substantially older than the other reviewed gateways. |
| [Applied ML index](https://github.com/eugeneyan/applied-ml) and its linked [Expedia cascade-bandit article](https://medium.com/expedia-group-tech/how-to-optimise-rankings-with-cascade-bandits-5d92dfa0f16b) | Practitioners discovering production ML problem patterns; the linked article discusses sequential ranking under partial feedback | Index commit `d58606b6` dated 2024-05-02 and the original 2022 Expedia article were opened and checked | Discovery index and article, not a reusable routing package | Repository metadata and linked-source terms were reviewed only for discovery; no code or reported result is reused | The cascade pattern reinforces evaluating a sequence rather than one choice, but its recommendation feedback setting does not establish LLM fallback safety. No Expedia result is treated as locally reproduced. |

## Issues and pull-request signals

- LiteLLM issue 35303 is closed as a duplicate of 33842. Its incident evidence is still useful problem evidence, but it is not proof that every current runtime path remains vulnerable.
- Current LiteLLM source was inspected directly. `validate_fallbacks` checks container shape and does not perform graph-cycle analysis.
- RouteLLM's GitHub page showed 29 open issues and 12 pull requests during review; the shallow default-branch snapshot's latest commit was from 2024-08-10.
- Portkey Gateway's README announces ongoing 2.0 pre-release work. The default-branch snapshot was not treated as the complete commercial product.

## Chosen gap and impact gate

| Gate | Evidence |
|---|---|
| Real problem | A bad retry/fallback policy can multiply traffic, cost, latency, and logs or silently move an agent onto a model that cannot honor its tool or privacy contract. |
| Current evidence | LiteLLM issue 35303 provides a production incident; current source shows shape-only validation; current gateway docs expose several interacting retry and fallback controls. |
| Original value | FallbackLens combines graph-safety checks, path-wide workload contracts, conservative exposure bounds, and deterministic failure replay. These improve reliability, cost control, privacy, and reviewability. |
| Measurability | Ten versioned synthetic cases, a shape-only baseline, deterministic scenario traces, stable finding codes, and report consistency tests. |
| Finishability | One LiteLLM adapter plus a small canonical engine and offline report is a complete vertical slice. |
| Maintainability | Typed dataclasses, explicit JSON sidecar, stable schema version, deterministic fixtures, and no provider integrations. |
| License fit | New implementation is MIT. PyYAML is MIT. No upstream code or dataset is copied. |

## Decision

Build FallbackLens as an independent compatible tool. An upstream LiteLLM patch would address only one gateway and one cycle check; the selected mode is a distinct project, and the broader workload-contract evidence belongs in a separate provider-neutral package.
