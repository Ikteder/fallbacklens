"""Static graph and workload-contract analysis."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable

from .models import AuditReport, Contract, ContractMetrics, Finding, Policy, Profile


def audit_policy(policy: Policy, profile: Profile) -> AuditReport:
    findings = list(policy.findings)
    adjacency = _adjacency(policy)

    for edge in policy.edges:
        if edge.source not in policy.nodes:
            findings.append(
                Finding("FALLBACK_SOURCE_UNKNOWN", "error", f"fallback source {edge.source!r} is not a configured model group", nodes=(edge.source,))
            )
        if edge.target not in policy.nodes:
            findings.append(
                Finding("FALLBACK_TARGET_UNKNOWN", "error", f"fallback target {edge.target!r} is not a configured model group", nodes=(edge.target,))
            )

    cycles = _strongly_connected_cycles(policy.nodes, adjacency)
    for cycle in cycles:
        findings.append(
            Finding(
                "FALLBACK_CYCLE",
                "error",
                "fallback graph contains a cycle: " + " -> ".join((*cycle, cycle[0])),
                nodes=cycle,
            )
        )

    metrics: list[ContractMetrics] = []
    all_reachable: set[str] = set()
    cycle_nodes = {node for cycle in cycles for node in cycle}
    for contract in profile.contracts:
        contract_findings, contract_metrics, reachable = _audit_contract(
            policy, profile, contract, adjacency, cycle_nodes
        )
        findings.extend(contract_findings)
        metrics.append(contract_metrics)
        all_reachable.update(reachable)

    for node in sorted(policy.nodes - all_reachable):
        findings.append(
            Finding(
                "MODEL_GROUP_UNREACHABLE",
                "warning",
                f"model group {node!r} is unreachable from every declared contract entrypoint",
                nodes=(node,),
            )
        )

    findings = _deduplicate(findings)
    findings.sort(key=lambda item: ({"error": 0, "warning": 1, "info": 2}.get(item.severity, 3), item.code, item.contract or "", item.nodes))
    return AuditReport(policy=policy, profile=profile, findings=findings, metrics=metrics)


def _audit_contract(
    policy: Policy,
    profile: Profile,
    contract: Contract,
    adjacency: dict[str, list[str]],
    cycle_nodes: set[str],
) -> tuple[list[Finding], ContractMetrics, set[str]]:
    findings: list[Finding] = []
    if contract.entrypoint not in policy.nodes:
        findings.append(
            Finding(
                "CONTRACT_ENTRYPOINT_UNKNOWN",
                "error",
                f"contract entrypoint {contract.entrypoint!r} is not a configured model group",
                contract=contract.name,
                nodes=(contract.entrypoint,),
            )
        )
        return findings, ContractMetrics(contract.name, 0, None, None, None, None), set()

    reachable = _reachable(contract.entrypoint, adjacency)
    for node in sorted(reachable):
        facts = profile.models.get(node)
        if facts is None:
            findings.append(
                Finding(
                    "MODEL_FACTS_MISSING",
                    "error",
                    f"no profile facts were supplied for reachable model group {node!r}",
                    contract=contract.name,
                    nodes=(node,),
                )
            )
            continue
        missing_capabilities = sorted(contract.required_capabilities - facts.capabilities)
        if missing_capabilities:
            findings.append(
                Finding(
                    "CAPABILITY_DRIFT",
                    "error",
                    f"{node!r} lacks required capabilities: {', '.join(missing_capabilities)}",
                    contract=contract.name,
                    nodes=(node,),
                )
            )
        if facts.context_window_tokens is None:
            findings.append(
                Finding(
                    "CONTEXT_WINDOW_UNKNOWN",
                    "warning",
                    f"{node!r} has no declared context window",
                    contract=contract.name,
                    nodes=(node,),
                )
            )
        elif facts.context_window_tokens < contract.required_context_tokens:
            findings.append(
                Finding(
                    "CONTEXT_WINDOW_DRIFT",
                    "error",
                    f"{node!r} declares {facts.context_window_tokens} context tokens, below required {contract.required_context_tokens}",
                    contract=contract.name,
                    nodes=(node,),
                )
            )
        if contract.require_zero_data_retention:
            if facts.zero_data_retention is None:
                findings.append(
                    Finding(
                        "RETENTION_UNKNOWN",
                        "warning",
                        f"{node!r} has no zero-data-retention declaration",
                        contract=contract.name,
                        nodes=(node,),
                    )
                )
            elif not facts.zero_data_retention:
                findings.append(
                    Finding(
                        "PRIVACY_DRIFT",
                        "error",
                        f"{node!r} does not satisfy the zero-data-retention contract",
                        contract=contract.name,
                        nodes=(node,),
                    )
                )

    if reachable & cycle_nodes:
        findings.append(
            Finding(
                "UNBOUNDED_ROUTE",
                "error",
                "a reachable fallback cycle prevents a finite configured exposure bound",
                contract=contract.name,
                nodes=tuple(sorted(reachable & cycle_nodes)),
            )
        )
        return findings, ContractMetrics(contract.name, None, None, None, None, None), reachable

    paths = _terminal_paths(contract.entrypoint, adjacency)
    if not paths:
        findings.append(
            Finding(
                "NO_TERMINAL_PATH",
                "error",
                "no terminal route is reachable from the contract entrypoint",
                contract=contract.name,
                nodes=(contract.entrypoint,),
            )
        )
        return findings, ContractMetrics(contract.name, 0, None, None, None, None), reachable

    if policy.retries is None:
        return findings, ContractMetrics(contract.name, len(paths), max(paths, key=len), None, None, None), reachable

    attempts_per_node = policy.retries + 1
    path_metrics: list[tuple[list[str], int, float | None, float | None]] = []
    for path in paths:
        attempts = len(path) * attempts_per_node
        cost: float | None = 0.0
        latency: float | None = 0.0
        for node in path:
            facts = profile.models.get(node)
            if facts is None:
                cost = None
                latency = None
                continue
            if facts.input_usd_per_million is None or facts.output_usd_per_million is None:
                cost = None
            elif cost is not None:
                per_attempt = (
                    contract.expected_input_tokens * facts.input_usd_per_million
                    + contract.expected_output_tokens * facts.output_usd_per_million
                ) / 1_000_000
                cost += per_attempt * attempts_per_node
            if facts.latency_p95_ms is None:
                latency = None
            elif latency is not None:
                latency += facts.latency_p95_ms * attempts_per_node
        path_metrics.append((path, attempts, cost, latency))

    worst_attempt_entry = max(path_metrics, key=lambda item: item[1])
    costs = [entry for entry in path_metrics if entry[2] is not None]
    latencies = [entry for entry in path_metrics if entry[3] is not None]
    worst_cost_entry = max(costs, key=lambda item: item[2] or 0.0) if costs else None
    worst_latency_entry = max(latencies, key=lambda item: item[3] or 0.0) if latencies else None
    max_cost = worst_cost_entry[2] if worst_cost_entry else None
    max_latency = worst_latency_entry[3] if worst_latency_entry else None

    if worst_attempt_entry[1] > contract.max_attempts:
        findings.append(
            Finding(
                "ATTEMPT_BUDGET_EXCEEDED",
                "error",
                f"configured exposure is {worst_attempt_entry[1]} attempts, above budget {contract.max_attempts}",
                contract=contract.name,
                nodes=tuple(worst_attempt_entry[0]),
            )
        )
    if max_cost is None:
        findings.append(
            Finding(
                "COST_BOUND_UNKNOWN",
                "warning",
                "cost exposure cannot be calculated because reachable price metadata is incomplete",
                contract=contract.name,
            )
        )
    elif max_cost > contract.max_cost_usd:
        findings.append(
            Finding(
                "COST_BUDGET_EXCEEDED",
                "error",
                f"configured cost exposure is ${max_cost:.6f}, above budget ${contract.max_cost_usd:.6f}",
                contract=contract.name,
                nodes=tuple(worst_cost_entry[0]) if worst_cost_entry else (),
            )
        )
    if max_latency is None:
        findings.append(
            Finding(
                "LATENCY_BOUND_UNKNOWN",
                "warning",
                "latency exposure cannot be calculated because reachable p95 metadata is incomplete",
                contract=contract.name,
            )
        )
    elif max_latency > contract.max_latency_ms:
        findings.append(
            Finding(
                "LATENCY_BUDGET_EXCEEDED",
                "error",
                f"configured p95 latency exposure is {max_latency:.1f} ms, above budget {contract.max_latency_ms:.1f} ms",
                contract=contract.name,
                nodes=tuple(worst_latency_entry[0]) if worst_latency_entry else (),
            )
        )

    return (
        findings,
        ContractMetrics(
            contract.name,
            len(paths),
            worst_attempt_entry[0],
            worst_attempt_entry[1],
            max_cost,
            max_latency,
        ),
        reachable,
    )


def _adjacency(policy: Policy) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {node: [] for node in policy.nodes}
    for edge in sorted(policy.edges, key=lambda item: (item.source, item.kind, item.order, item.target)):
        if edge.source in policy.nodes and edge.target in policy.nodes and edge.target not in result[edge.source]:
            result[edge.source].append(edge.target)
    return result


def _reachable(start: str, adjacency: dict[str, list[str]]) -> set[str]:
    seen: set[str] = set()
    queue = deque([start])
    while queue:
        node = queue.popleft()
        if node in seen:
            continue
        seen.add(node)
        queue.extend(adjacency.get(node, []))
    return seen


def _terminal_paths(start: str, adjacency: dict[str, list[str]]) -> list[list[str]]:
    paths: list[list[str]] = []

    def visit(node: str, path: list[str]) -> None:
        targets = adjacency.get(node, [])
        if not targets:
            paths.append([*path, node])
            return
        for target in targets:
            if target in path:
                continue
            visit(target, [*path, node])

    visit(start, [])
    return paths


def _strongly_connected_cycles(nodes: Iterable[str], adjacency: dict[str, list[str]]) -> list[tuple[str, ...]]:
    index = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    components: list[tuple[str, ...]] = []

    def connect(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for target in adjacency.get(node, []):
            if target not in indices:
                connect(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[target])
        if lowlinks[node] == indices[node]:
            component: list[str] = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member == node:
                    break
            ordered = tuple(sorted(component))
            if len(ordered) > 1 or (len(ordered) == 1 and ordered[0] in adjacency.get(ordered[0], [])):
                components.append(ordered)

    for node in sorted(nodes):
        if node not in indices:
            connect(node)
    return sorted(components)


def _deduplicate(findings: list[Finding]) -> list[Finding]:
    seen: set[tuple[object, ...]] = set()
    result: list[Finding] = []
    for finding in findings:
        key = (finding.code, finding.severity, finding.message, finding.contract, finding.nodes)
        if key not in seen:
            seen.add(key)
            result.append(finding)
    return result
