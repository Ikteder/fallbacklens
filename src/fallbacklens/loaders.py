"""Safe input loaders and the LiteLLM route-graph adapter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .models import Contract, Edge, Finding, ModelFacts, Policy, Profile


def _read_mapping(path: str | Path) -> dict[str, Any]:
    input_path = Path(path)
    text = input_path.read_text(encoding="utf-8")
    if input_path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"{input_path}: root must be an object")
    return data


def policy_from_data(data: dict[str, Any]) -> Policy:
    findings: list[Finding] = []
    model_list = data.get("model_list", [])
    if not isinstance(model_list, list):
        findings.append(Finding("MODEL_LIST_SHAPE", "error", "model_list must be a list"))
        model_list = []

    nodes: set[str] = set()
    for index, item in enumerate(model_list):
        if not isinstance(item, dict) or not isinstance(item.get("model_name"), str):
            findings.append(
                Finding("MODEL_ENTRY_SHAPE", "error", f"model_list[{index}] must contain a string model_name")
            )
            continue
        nodes.add(item["model_name"])

    router_settings = data.get("router_settings", {})
    if router_settings is None:
        router_settings = {}
    if not isinstance(router_settings, dict):
        findings.append(Finding("ROUTER_SETTINGS_SHAPE", "error", "router_settings must be an object"))
        router_settings = {}

    retries_raw = router_settings.get("num_retries")
    retries: int | None
    if retries_raw is None:
        retries = None
        findings.append(
            Finding(
                "RETRIES_UNKNOWN",
                "warning",
                "router_settings.num_retries is absent; attempt, cost, and latency exposure cannot be bounded",
            )
        )
    elif isinstance(retries_raw, int) and not isinstance(retries_raw, bool) and retries_raw >= 0:
        retries = retries_raw
    else:
        retries = None
        findings.append(Finding("RETRIES_INVALID", "error", "router_settings.num_retries must be a non-negative integer"))

    edges: list[Edge] = []
    fields = (
        ("fallbacks", "general"),
        ("context_window_fallbacks", "context_window"),
        ("content_policy_fallbacks", "content_policy"),
    )
    for field_name, kind in fields:
        raw_entries = router_settings.get(field_name, [])
        if raw_entries is None:
            continue
        if not isinstance(raw_entries, list):
            findings.append(Finding("FALLBACK_LIST_SHAPE", "error", f"router_settings.{field_name} must be a list"))
            continue
        for entry_index, entry in enumerate(raw_entries):
            if not isinstance(entry, dict) or len(entry) != 1:
                findings.append(
                    Finding(
                        "FALLBACK_ENTRY_SHAPE",
                        "error",
                        f"router_settings.{field_name}[{entry_index}] must be a one-key object",
                    )
                )
                continue
            source, targets_raw = next(iter(entry.items()))
            if not isinstance(source, str):
                findings.append(Finding("FALLBACK_SOURCE_SHAPE", "error", f"{field_name}[{entry_index}] source must be a string"))
                continue
            targets = [targets_raw] if isinstance(targets_raw, str) else targets_raw
            if not isinstance(targets, list) or not targets or not all(isinstance(target, str) for target in targets):
                findings.append(
                    Finding(
                        "FALLBACK_TARGET_SHAPE",
                        "error",
                        f"router_settings.{field_name}[{entry_index}] targets must be a string or non-empty string list",
                        nodes=(source,),
                    )
                )
                continue
            for order, target in enumerate(targets):
                edges.append(Edge(source=source, target=target, kind=kind, order=order))

    return Policy(nodes=nodes, edges=edges, retries=retries, findings=findings)


def load_litellm_config(path: str | Path) -> Policy:
    return policy_from_data(_read_mapping(path))


def profile_from_data(data: dict[str, Any]) -> Profile:
    if data.get("schema_version") != 1:
        raise ValueError("profile schema_version must be 1")
    as_of = data.get("as_of")
    sources = data.get("sources")
    if not isinstance(as_of, str) or not as_of:
        raise ValueError("profile as_of must be a non-empty string")
    if not isinstance(sources, list) or not sources or not all(isinstance(item, str) and item for item in sources):
        raise ValueError("profile sources must be a non-empty string list")

    raw_models = data.get("models")
    if not isinstance(raw_models, dict):
        raise ValueError("profile models must be an object")
    models: dict[str, ModelFacts] = {}
    for name, raw in raw_models.items():
        if not isinstance(name, str) or not isinstance(raw, dict):
            raise ValueError("each profile model must be a named object")
        capabilities = raw.get("capabilities", [])
        if not isinstance(capabilities, list) or not all(isinstance(value, str) for value in capabilities):
            raise ValueError(f"models.{name}.capabilities must be a string list")
        models[name] = ModelFacts(
            capabilities=frozenset(capabilities),
            context_window_tokens=_optional_int(raw, "context_window_tokens", name),
            input_usd_per_million=_optional_number(raw, "input_usd_per_million", name),
            output_usd_per_million=_optional_number(raw, "output_usd_per_million", name),
            latency_p95_ms=_optional_number(raw, "latency_p95_ms", name),
            zero_data_retention=_optional_bool(raw, "zero_data_retention", name),
        )

    raw_contracts = data.get("contracts")
    if not isinstance(raw_contracts, list) or not raw_contracts:
        raise ValueError("profile contracts must be a non-empty list")
    contracts: list[Contract] = []
    for index, raw in enumerate(raw_contracts):
        if not isinstance(raw, dict):
            raise ValueError(f"contracts[{index}] must be an object")
        required = raw.get("required_capabilities", [])
        if not isinstance(required, list) or not all(isinstance(value, str) for value in required):
            raise ValueError(f"contracts[{index}].required_capabilities must be a string list")
        contracts.append(
            Contract(
                name=_required_str(raw, "name", index),
                entrypoint=_required_str(raw, "entrypoint", index),
                required_capabilities=frozenset(required),
                required_context_tokens=_required_nonnegative_int(raw, "required_context_tokens", index),
                require_zero_data_retention=_required_bool(raw, "require_zero_data_retention", index),
                expected_input_tokens=_required_nonnegative_int(raw, "expected_input_tokens", index),
                expected_output_tokens=_required_nonnegative_int(raw, "expected_output_tokens", index),
                max_attempts=_required_nonnegative_int(raw, "max_attempts", index),
                max_cost_usd=_required_nonnegative_number(raw, "max_cost_usd", index),
                max_latency_ms=_required_nonnegative_number(raw, "max_latency_ms", index),
            )
        )
    return Profile(as_of=as_of, sources=sources, models=models, contracts=contracts)


def load_profile(path: str | Path) -> Profile:
    return profile_from_data(_read_mapping(path))


def _optional_int(raw: dict[str, Any], key: str, name: str) -> int | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"models.{name}.{key} must be a non-negative integer or null")
    return value


def _optional_number(raw: dict[str, Any], key: str, name: str) -> float | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
        raise ValueError(f"models.{name}.{key} must be a non-negative number or null")
    return float(value)


def _optional_bool(raw: dict[str, Any], key: str, name: str) -> bool | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, bool):
        raise ValueError(f"models.{name}.{key} must be a boolean or null")
    return value


def _required_str(raw: dict[str, Any], key: str, index: int) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"contracts[{index}].{key} must be a non-empty string")
    return value


def _required_bool(raw: dict[str, Any], key: str, index: int) -> bool:
    value = raw.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"contracts[{index}].{key} must be a boolean")
    return value


def _required_nonnegative_int(raw: dict[str, Any], key: str, index: int) -> int:
    value = raw.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"contracts[{index}].{key} must be a non-negative integer")
    return value


def _required_nonnegative_number(raw: dict[str, Any], key: str, index: int) -> float:
    value = raw.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
        raise ValueError(f"contracts[{index}].{key} must be a non-negative number")
    return float(value)
