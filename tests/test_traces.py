from __future__ import annotations

import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from copy import deepcopy
from pathlib import Path

from fallbacklens import __version__
from fallbacklens.benchmark import run_benchmark
from fallbacklens.cli import main
from fallbacklens.loaders import policy_from_data, profile_from_data
from fallbacklens.trace_benchmark import (
    corpus,
    render_trace_benchmark_svg,
    run_trace_benchmark,
)
from fallbacklens.traces import audit_traces, load_trace_json, render_trace_html


class TraceTests(unittest.TestCase):
    def setUp(self):
        self.case = corpus()["cases"][0]

    def audit(self):
        return audit_traces(
            policy_from_data(self.case["policy"]),
            profile_from_data(self.case["profile"]),
            self.case["trace"],
            self.case["bindings"],
        )

    def spans(self):
        return self.case["trace"]["resourceSpans"][0]["scopeSpans"][0]["spans"]

    def test_versioned_corpus(self):
        result = run_trace_benchmark(corpus())
        self.assertEqual(result["cases"], result["correct"])
        self.assertLess(result["baseline_correct"], result["correct"])
        ET.fromstring(render_trace_benchmark_svg(result))

    def test_static_evidence_records_actual_package_version(self):
        root = Path(__file__).resolve().parents[1]
        result = run_benchmark(root / "benchmarks/policy-cases-v1.json")
        self.assertEqual(__version__, result["fallbacklens"]["version"])

    def test_privacy_and_relative_timing(self):
        result = run_trace_benchmark(corpus())
        output = json.dumps(result) + "".join(
            render_trace_html(r["report"]) for r in result["results"]
        )
        for secret in ("PRIVATE", "a" * 32, "vendor/one", "resourceSpans", "spanId"):
            self.assertNotIn(secret, output)
        report = self.audit()["requests"][0]
        self.assertEqual(190, report["inference_envelope_ms"])
        self.assertEqual(10, report["calls"][0]["start_ms"])

    def test_duplicate_spans(self):
        self.spans().append(deepcopy(self.spans()[1]))
        with self.assertRaises(ValueError):
            self.audit()

    def test_span_limit(self):
        self.spans().extend([deepcopy(self.spans()[1]) for _ in range(2000)])
        with self.assertRaises(ValueError):
            self.audit()

    def test_client_enum_name(self):
        self.spans()[1]["kind"] = "SPAN_KIND_CLIENT"
        self.assertEqual("observed-no-drift", self.audit()["requests"][0]["verdict"])

    def test_no_bindings_rejected(self):
        self.case["bindings"]["requests"] = []
        with self.assertRaises(ValueError):
            self.audit()

    def test_nested_unknown_model_stays_inconclusive(self):
        self.spans()[2]["parentSpanId"] = self.spans()[1]["spanId"]
        self.spans()[2]["startTimeUnixNano"] = self.spans()[1]["startTimeUnixNano"]
        self.spans()[2]["endTimeUnixNano"] = self.spans()[1]["endTimeUnixNano"]
        self.spans()[2]["attributes"][1]["value"]["stringValue"] = "unknown"
        self.assertEqual("inconclusive", self.audit()["requests"][0]["verdict"])

    def test_malformed_semantic_value(self):
        self.spans()[1]["attributes"][0]["value"] = {"intValue": "3"}
        with self.assertRaises(ValueError):
            self.audit()

    def test_duplicate_contract_name(self):
        self.case["profile"]["contracts"].append(
            deepcopy(self.case["profile"]["contracts"][0])
        )
        with self.assertRaises(ValueError):
            self.audit()

    def test_invalid_benchmark_corpus(self):
        for data in (
            {},
            {
                "suite": "synthetic-otlp-v1",
                "schema_version": 1,
                "seed": 20261009,
                "cases": [None],
            },
        ):
            with self.assertRaises(ValueError):
                run_trace_benchmark(data)

    def test_duplicate_attributes(self):
        self.spans()[1]["attributes"].append(deepcopy(self.spans()[1]["attributes"][0]))
        with self.assertRaises(ValueError):
            self.audit()

    def test_cycle(self):
        self.spans()[0]["parentSpanId"] = self.spans()[1]["spanId"]
        with self.assertRaises(ValueError):
            self.audit()

    def test_invalid_span_fields(self):
        for field, value in (
            ("traceId", "bad"),
            ("spanId", "0" * 16),
            ("kind", True),
            ("startTimeUnixNano", "1.0"),
            ("endTimeUnixNano", "1"),
        ):
            with self.subTest(field=field):
                self.setUp()
                self.spans()[1][field] = value
                with self.assertRaises(ValueError):
                    self.audit()

    def test_containment(self):
        self.spans()[1]["endTimeUnixNano"] = "9999999999"
        with self.assertRaises(ValueError):
            self.audit()

    def test_overlapping_root_bindings(self):
        request = deepcopy(self.case["bindings"]["requests"][0])
        request["root_span_id"] = self.spans()[1]["spanId"]
        self.case["bindings"]["requests"].append(request)
        with self.assertRaises(ValueError):
            self.audit()

    def test_root_external_parent_supported(self):
        self.spans()[0]["parentSpanId"] = "b" * 16
        self.assertEqual("observed-no-drift", self.audit()["requests"][0]["verdict"])

    def test_unknown_retry_policy_inconclusive(self):
        self.case["policy"]["router_settings"].pop("num_retries")
        self.assertEqual("inconclusive", self.audit()["requests"][0]["verdict"])

    def test_invalid_policy_never_passes(self):
        self.case["policy"]["router_settings"]["fallbacks"].append({"primary": None})
        self.assertEqual("inconclusive", self.audit()["requests"][0]["verdict"])

    def test_bindings_strict(self):
        for mutation in (
            "bool-schema",
            "bad-alias",
            "missing-scopes",
            "unknown-contract",
        ):
            with self.subTest(mutation=mutation):
                self.setUp()
                bindings = self.case["bindings"]
                if mutation == "bool-schema":
                    bindings["schema_version"] = True
                elif mutation == "bad-alias":
                    bindings["model_groups"]["vendor/one"] = "<secret>"
                elif mutation == "missing-scopes":
                    bindings["scopes"] = []
                else:
                    bindings["requests"][0]["contract"] = "missing"
                with self.assertRaises(ValueError):
                    self.audit()

    def test_nonfinite_threshold_rejected(self):
        self.case["profile"]["contracts"][0]["max_latency_ms"] = float("nan")
        with self.assertRaises(ValueError):
            self.audit()

    def test_parser_does_not_echo_invalid_content(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            for text in ('{"PRIVATE_SECRET":NaN}', '{"x":1,"x":2}', "PRIVATE_SECRET"):
                path.write_text(text, encoding="utf-8")
                with self.assertRaises(ValueError) as caught:
                    load_trace_json(path)
                self.assertNotIn("PRIVATE_SECRET", str(caught.exception))

    def test_cli_roundtrip_and_exits(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            trace = output / "trace.json"
            binding = output / "binding.json"
            self.case["bindings"]["model_groups"] = {
                "vendor/one": "agent-primary",
                "vendor/two": "agent-secondary",
            }
            trace.write_text(json.dumps(self.case["trace"]), encoding="utf-8")
            binding.write_text(json.dumps(self.case["bindings"]), encoding="utf-8")
            args = [
                "trace-audit",
                str(root / "examples/litellm-safe.yaml"),
                "--profile",
                str(root / "examples/profile-safe.json"),
                "--trace",
                str(trace),
                "--bindings",
                str(binding),
                "--json",
                str(output / "report.json"),
                "--html",
                str(output / "report.html"),
            ]
            self.assertEqual(0, main(args))
            self.assertNotIn(
                "PRIVATE", (output / "report.html").read_text(encoding="utf-8")
            )
            self.case["bindings"]["model_groups"]["vendor/one"] = "agent-local"
            binding.write_text(json.dumps(self.case["bindings"]), encoding="utf-8")
            self.assertEqual(1, main(args))
            trace.write_text("PRIVATE_SECRET", encoding="utf-8")
            self.assertEqual(2, main(args))

    def test_cli_cannot_overwrite_trace_input(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.json"
            original = json.dumps(self.case["trace"])
            path.write_text(original, encoding="utf-8")
            args = [
                "trace-audit",
                str(root / "examples/trace-policy.json"),
                "--profile",
                str(root / "examples/trace-profile.json"),
                "--trace",
                str(path),
                "--bindings",
                str(root / "examples/trace-bindings.json"),
                "--json",
                str(path),
            ]
            self.assertEqual(2, main(args))
            self.assertEqual(original, path.read_text(encoding="utf-8"))
