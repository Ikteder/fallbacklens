"""Versioned comparison against a shape-only fallback validator."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .audit import audit_policy
from .loaders import policy_from_data, profile_from_data


def run_benchmark(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("cases"), list):
        raise ValueError("benchmark corpus must be a schema_version 1 object with cases")
    base_config = data.get("base_config")
    base_profile = data.get("base_profile")
    if not isinstance(base_config, dict) or not isinstance(base_profile, dict):
        raise ValueError("benchmark corpus must contain base_config and base_profile objects")
    results: list[dict[str, Any]] = []
    for case in data["cases"]:
        if not isinstance(case, dict):
            raise ValueError("each benchmark case must be an object")
        expected_valid = case.get("expected_valid")
        if not isinstance(expected_valid, bool):
            raise ValueError("each benchmark case needs a boolean expected_valid")
        config_patch = case.get("config_patch", {})
        profile_patch = case.get("profile_patch", {})
        if not isinstance(config_patch, dict) or not isinstance(profile_patch, dict):
            raise ValueError("case patches must be objects")
        config = _deep_merge(base_config, config_patch)
        profile_data = _deep_merge(base_profile, profile_patch)
        baseline_valid = _shape_only_valid(config)
        report = audit_policy(policy_from_data(config), profile_from_data(profile_data))
        fallbacklens_valid = report.summary["errors"] == 0
        results.append(
            {
                "name": case.get("name"),
                "expected_valid": expected_valid,
                "baseline_valid": baseline_valid,
                "baseline_correct": baseline_valid == expected_valid,
                "fallbacklens_valid": fallbacklens_valid,
                "fallbacklens_correct": fallbacklens_valid == expected_valid,
                "finding_codes": sorted({finding.code for finding in report.findings}),
            }
        )
    total = len(results)
    baseline_correct = sum(result["baseline_correct"] for result in results)
    lens_correct = sum(result["fallbacklens_correct"] for result in results)
    return {
        "schema_version": 1,
        "corpus": data.get("name"),
        "cases": total,
        "baseline": {
            "name": "shape-only fallback validation",
            "correct": baseline_correct,
            "accuracy": baseline_correct / total if total else 0.0,
        },
        "fallbacklens": {
            "version": "0.1.0",
            "correct": lens_correct,
            "accuracy": lens_correct / total if total else 0.0,
        },
        "results": results,
    }


def render_benchmark_svg(result: dict[str, Any]) -> str:
    total = result["cases"]
    baseline = result["baseline"]["correct"]
    lens = result["fallbacklens"]["correct"]
    baseline_width = 520 * baseline / total if total else 0
    lens_width = 520 * lens / total if total else 0
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="820" height="330" viewBox="0 0 820 330" role="img" aria-labelledby="title desc">
<title id="title">FallbackLens synthetic policy benchmark</title>
<desc id="desc">The shape-only baseline correctly classified {baseline} of {total} cases. FallbackLens correctly classified {lens} of {total} cases.</desc>
<rect width="820" height="330" rx="20" fill="#f5f7fb"/>
<text x="42" y="54" font-size="28" font-family="system-ui,sans-serif" font-weight="750" fill="#172033">Unsafe routes need more than syntax checks</text>
<text x="42" y="82" font-size="14" font-family="system-ui,sans-serif" fill="#60708b">Correct classification on the versioned 2026-09-30 synthetic corpus</text>
<text x="42" y="137" font-size="16" font-family="system-ui,sans-serif" fill="#172033">Shape-only baseline</text>
<rect x="222" y="116" width="520" height="28" rx="8" fill="#d8dfeb"/><rect x="222" y="116" width="{baseline_width:.1f}" height="28" rx="8" fill="#a15c00"/>
<text x="754" y="137" font-size="16" font-family="system-ui,sans-serif" font-weight="700" fill="#172033">{baseline}/{total}</text>
<text x="42" y="207" font-size="16" font-family="system-ui,sans-serif" fill="#172033">FallbackLens 0.1</text>
<rect x="222" y="186" width="520" height="28" rx="8" fill="#d8dfeb"/><rect x="222" y="186" width="{lens_width:.1f}" height="28" rx="8" fill="#16794b"/>
<text x="754" y="207" font-size="16" font-family="system-ui,sans-serif" font-weight="700" fill="#172033">{lens}/{total}</text>
<text x="42" y="270" font-size="13" font-family="system-ui,sans-serif" fill="#60708b">Cases cover cycles, missing nodes, contract drift, and bounded attempt, cost, and latency exposure.</text>
<text x="42" y="295" font-size="13" font-family="system-ui,sans-serif" fill="#60708b">Synthetic configuration evidence, not a live-provider reliability benchmark.</text>
</svg>
"""


def _shape_only_valid(config: dict[str, Any]) -> bool:
    settings = config.get("router_settings", {})
    if not isinstance(settings, dict):
        return False
    for key in ("fallbacks", "context_window_fallbacks", "content_policy_fallbacks"):
        entries = settings.get(key, [])
        if entries is None:
            continue
        if not isinstance(entries, list):
            return False
        if any(not isinstance(entry, dict) or len(entry) != 1 for entry in entries):
            return False
    return True


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result
