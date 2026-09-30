from __future__ import annotations

import json
import unittest
from pathlib import Path

from fallbacklens.audit import audit_policy
from fallbacklens.benchmark import run_benchmark
from fallbacklens.loaders import (
    load_litellm_config,
    load_profile,
    policy_from_data,
    profile_from_data,
)
from fallbacklens.report import render_html, render_svg

ROOT = Path(__file__).resolve().parents[1]


class AuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = load_profile(ROOT / "examples" / "profile-safe.json")

    def test_safe_demo_has_no_findings(self) -> None:
        report = audit_policy(load_litellm_config(ROOT / "examples" / "litellm-safe.yaml"), self.profile)
        self.assertEqual({"errors": 0, "warnings": 0, "info": 0}, report.summary)
        self.assertEqual(2, report.metrics[0].path_count)
        self.assertEqual(6, report.metrics[0].max_attempts)
        self.assertAlmostEqual(0.048, report.metrics[0].max_cost_usd or -1)
        self.assertAlmostEqual(10000.0, report.metrics[0].max_latency_ms or -1)

    def test_cycle_is_error_and_unbounded(self) -> None:
        report = audit_policy(load_litellm_config(ROOT / "examples" / "litellm-risky.yaml"), self.profile)
        codes = {finding.code for finding in report.findings}
        self.assertIn("FALLBACK_CYCLE", codes)
        self.assertIn("UNBOUNDED_ROUTE", codes)
        self.assertIsNone(report.metrics[0].max_attempts)

    def test_unknown_target_is_error(self) -> None:
        policy = policy_from_data(
            {
                "model_list": [{"model_name": "primary"}],
                "router_settings": {"num_retries": 0, "fallbacks": [{"primary": "missing"}]},
            }
        )
        profile = profile_from_data(
            {
                "schema_version": 1,
                "as_of": "2026-09-30",
                "sources": ["test"],
                "models": {"primary": _facts()},
                "contracts": [_contract(max_attempts=1)],
            }
        )
        report = audit_policy(policy, profile)
        self.assertIn("FALLBACK_TARGET_UNKNOWN", {finding.code for finding in report.findings})

    def test_missing_capability_and_privacy_are_errors(self) -> None:
        data = json.loads((ROOT / "examples" / "profile-safe.json").read_text(encoding="utf-8"))
        data["models"]["agent-secondary"]["capabilities"] = ["json_schema"]
        data["models"]["agent-secondary"]["zero_data_retention"] = False
        report = audit_policy(load_litellm_config(ROOT / "examples" / "litellm-safe.yaml"), profile_from_data(data))
        codes = {finding.code for finding in report.findings}
        self.assertIn("CAPABILITY_DRIFT", codes)
        self.assertIn("PRIVACY_DRIFT", codes)

    def test_missing_retry_value_blocks_bounds(self) -> None:
        policy = policy_from_data({"model_list": [{"model_name": "primary"}], "router_settings": {}})
        profile = profile_from_data(
            {
                "schema_version": 1,
                "as_of": "2026-09-30",
                "sources": ["test"],
                "models": {"primary": _facts()},
                "contracts": [_contract(max_attempts=1)],
            }
        )
        report = audit_policy(policy, profile)
        self.assertIn("RETRIES_UNKNOWN", {finding.code for finding in report.findings})
        self.assertIsNone(report.metrics[0].max_attempts)

    def test_reports_embed_same_summary(self) -> None:
        report = audit_policy(load_litellm_config(ROOT / "examples" / "litellm-risky.yaml"), self.profile)
        html = render_html(report)
        embedded = html.split('<script type="application/json" id="fallbacklens-report">', 1)[1].split("</script>", 1)[0]
        self.assertEqual(report.summary, json.loads(embedded)["summary"])
        svg = render_svg(report)
        self.assertIn("<svg", svg)
        self.assertIn("FallbackLens verified route graph", svg)

    def test_benchmark_classifies_all_cases(self) -> None:
        result = run_benchmark(ROOT / "benchmarks" / "policy-cases-v1.json")
        self.assertEqual(10, result["cases"])
        self.assertEqual(2, result["baseline"]["correct"])
        self.assertEqual(10, result["fallbacklens"]["correct"])


def _facts() -> dict[str, object]:
    return {
        "capabilities": ["tools", "json"],
        "context_window_tokens": 64000,
        "input_usd_per_million": 1,
        "output_usd_per_million": 1,
        "latency_p95_ms": 100,
        "zero_data_retention": True,
    }


def _contract(max_attempts: int) -> dict[str, object]:
    return {
        "name": "agent",
        "entrypoint": "primary",
        "required_capabilities": ["tools", "json"],
        "required_context_tokens": 1000,
        "require_zero_data_retention": True,
        "expected_input_tokens": 100,
        "expected_output_tokens": 100,
        "max_attempts": max_attempts,
        "max_cost_usd": 1,
        "max_latency_ms": 1000,
    }


if __name__ == "__main__":
    unittest.main()
