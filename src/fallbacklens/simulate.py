"""Bounded deterministic replay for declared provider-failure scenarios."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .models import Edge, Policy


def load_scenarios(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("scenario file must be a schema_version 1 object")
    if not isinstance(data.get("scenarios"), list):
        raise ValueError("scenario file must contain a scenarios list")
    return data


def replay_scenarios(policy: Policy, data: dict[str, Any]) -> dict[str, Any]:
    max_steps = data.get("max_steps", 100)
    if not isinstance(max_steps, int) or isinstance(max_steps, bool) or max_steps <= 0:
        raise ValueError("max_steps must be a positive integer")
    results = [replay_scenario(policy, scenario, max_steps) for scenario in data["scenarios"]]
    return {
        "schema_version": 1,
        "max_steps": max_steps,
        "summary": {
            "scenarios": len(results),
            "matched_expectation": sum(result["matched_expectation"] for result in results),
            "bounded_aborts": sum(result["status"] == "bounded_abort" for result in results),
        },
        "results": results,
    }


def replay_scenario(policy: Policy, scenario: dict[str, Any], max_steps: int) -> dict[str, Any]:
    if not isinstance(scenario, dict):
        raise ValueError("each scenario must be an object")
    name = scenario.get("name")
    entrypoint = scenario.get("entrypoint")
    outcomes = scenario.get("outcomes", {})
    if not isinstance(name, str) or not name:
        raise ValueError("scenario name must be a non-empty string")
    if not isinstance(entrypoint, str) or not entrypoint:
        raise ValueError(f"scenario {name}: entrypoint must be a non-empty string")
    if not isinstance(outcomes, dict) or not all(isinstance(key, str) and isinstance(value, list) for key, value in outcomes.items()):
        raise ValueError(f"scenario {name}: outcomes must map model groups to lists")
    remaining = deepcopy(outcomes)
    retries = policy.retries if policy.retries is not None else 0
    trace: list[dict[str, Any]] = []
    current = entrypoint
    status = "failed"
    terminal: str | None = None
    last_error: str | None = None

    while len(trace) < max_steps:
        exhausted = True
        for attempt in range(retries + 1):
            if len(trace) >= max_steps:
                status = "bounded_abort"
                break
            values = remaining.get(current, [])
            outcome = values.pop(0) if values else "success"
            if not isinstance(outcome, str):
                raise ValueError(f"scenario {name}: outcomes for {current} must be strings")
            trace.append({"step": len(trace) + 1, "model_group": current, "attempt": attempt + 1, "outcome": outcome})
            if outcome == "success":
                status = "success"
                terminal = current
                exhausted = False
                break
            last_error = outcome
        if status in {"success", "bounded_abort"}:
            break
        if not exhausted:
            break
        next_target = _next_target(policy.edges, current, last_error or "error")
        if next_target is None:
            terminal = current
            status = "failed"
            break
        current = next_target
    else:
        status = "bounded_abort"

    expected_status = scenario.get("expected_status")
    expected_terminal = scenario.get("expected_terminal")
    matched = (expected_status is None or status == expected_status) and (
        expected_terminal is None or terminal == expected_terminal
    )
    return {
        "name": name,
        "status": status,
        "terminal": terminal,
        "attempts": len(trace),
        "matched_expectation": matched,
        "trace": trace,
    }


def _next_target(edges: list[Edge], source: str, error: str) -> str | None:
    preferred_kind = {
        "context_window": "context_window",
        "content_policy": "content_policy",
    }.get(error, "general")
    candidates = sorted(
        (edge for edge in edges if edge.source == source and edge.kind == preferred_kind),
        key=lambda edge: (edge.order, edge.target),
    )
    if not candidates and preferred_kind != "general":
        candidates = sorted(
            (edge for edge in edges if edge.source == source and edge.kind == "general"),
            key=lambda edge: (edge.order, edge.target),
        )
    return candidates[0].target if candidates else None
