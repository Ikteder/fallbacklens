"""Typed data structures shared by the loader, auditor, and reporters."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    kind: str = "general"
    order: int = 0


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    message: str
    contract: str | None = None
    nodes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["nodes"] = list(self.nodes)
        return data


@dataclass
class Policy:
    nodes: set[str]
    edges: list[Edge]
    retries: int | None
    findings: list[Finding] = field(default_factory=list)
    source_format: str = "litellm"


@dataclass(frozen=True)
class ModelFacts:
    capabilities: frozenset[str]
    context_window_tokens: int | None
    input_usd_per_million: float | None
    output_usd_per_million: float | None
    latency_p95_ms: float | None
    zero_data_retention: bool | None


@dataclass(frozen=True)
class Contract:
    name: str
    entrypoint: str
    required_capabilities: frozenset[str]
    required_context_tokens: int
    require_zero_data_retention: bool
    expected_input_tokens: int
    expected_output_tokens: int
    max_attempts: int
    max_cost_usd: float
    max_latency_ms: float


@dataclass
class Profile:
    as_of: str
    sources: list[str]
    models: dict[str, ModelFacts]
    contracts: list[Contract]


@dataclass
class ContractMetrics:
    name: str
    path_count: int | None
    worst_path: list[str] | None
    max_attempts: int | None
    max_cost_usd: float | None
    max_latency_ms: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditReport:
    policy: Policy
    profile: Profile
    findings: list[Finding]
    metrics: list[ContractMetrics]

    @property
    def summary(self) -> dict[str, int]:
        return {
            "errors": sum(f.severity == "error" for f in self.findings),
            "warnings": sum(f.severity == "warning" for f in self.findings),
            "info": sum(f.severity == "info" for f in self.findings),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "source_format": self.policy.source_format,
            "profile_as_of": self.profile.as_of,
            "profile_sources": self.profile.sources,
            "summary": self.summary,
            "graph": {
                "nodes": sorted(self.policy.nodes),
                "edges": [asdict(edge) for edge in self.policy.edges],
                "retries": self.policy.retries,
            },
            "contracts": [metric.to_dict() for metric in self.metrics],
            "findings": [finding.to_dict() for finding in self.findings],
        }
