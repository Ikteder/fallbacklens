"""Optional integration suite. Run explicitly after installing .[interop]."""

import tempfile
import unittest
from pathlib import Path

from fallbacklens.interop import run_interop


class LiteLLMInteropTests(unittest.TestCase):
    def test_actual_instrumentation_under_mock_and_network_denial(self):
        with tempfile.TemporaryDirectory() as directory:
            report = run_interop(Path(directory) / "run", repetitions=1)
        self.assertEqual(3, report["expected_matches"])
        self.assertEqual(0, report["actual_provider_cost_usd"])
        kinds = {case["case"]: case["span_kinds"] for case in report["results"]}
        self.assertEqual({"CLIENT": 1, "SERVER": 1}, kinds["experimental-dedicated"])
        self.assertEqual({"INTERNAL": 2, "SERVER": 1}, kinds["legacy-dedicated"])
        self.assertEqual({"SERVER": 1}, kinds["experimental-collapsed"])
        for case in report["results"]:
            self.assertEqual(1, case["mock_http_requests"])
            self.assertEqual(0, case["blocked_external_operations"])
            self.assertEqual(0, case["external_sockets_allowed"])
