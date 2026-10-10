import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import yaml

from fallbacklens.audit import audit_policy
from fallbacklens.cli import main
from fallbacklens.loaders import load_litellm_config, load_profile, profile_from_data

ROOT = Path(__file__).resolve().parents[1]
FIELDS = (
    ("model", "input_usd_per_million"),
    ("model", "output_usd_per_million"),
    ("model", "latency_p95_ms"),
    ("contract", "max_cost_usd"),
    ("contract", "max_latency_ms"),
)


class NumericTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "examples/profile-safe.json").read_text())
        self.policy_path = ROOT / "examples/litellm-safe.yaml"

    def target(self, data, location):
        return (
            data["models"]["agent-primary"]
            if location == "model"
            else data["contracts"][0]
        )

    def test_invalid_assumptions_matrix(self):
        for location, field in FIELDS:
            for value in (float("nan"), float("inf"), -float("inf"), 10**400):
                with self.subTest(
                    location=location, field=field, value=str(value)[:20]
                ):
                    data = copy.deepcopy(self.data)
                    self.target(data, location)[field] = value
                    with self.assertRaisesRegex(ValueError, "finite"):
                        profile_from_data(data)

    def test_finite_zero_and_positive_preserved(self):
        for location, field in FIELDS:
            for value in (0, -0.0, 0.01, 100):
                data = copy.deepcopy(self.data)
                self.target(data, location)[field] = value
                profile_from_data(data)

    def test_optional_null_preserved_required_null_rejected(self):
        for location, field in FIELDS:
            data = copy.deepcopy(self.data)
            self.target(data, location)[field] = None
            if location == "model":
                profile_from_data(data)
            else:
                with self.assertRaises(ValueError):
                    profile_from_data(data)

    def test_json_yaml_and_cli_reject_nonfinite_without_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            for extension in ("json", "yaml"):
                for value in (float("nan"), float("inf"), -float("inf")):
                    data = copy.deepcopy(self.data)
                    data["contracts"][0]["max_cost_usd"] = value
                    profile = Path(directory) / f"profile.{extension}"
                    output = Path(directory) / "report.json"
                    profile.write_text(
                        json.dumps(data)
                        if extension == "json"
                        else yaml.safe_dump(data),
                        encoding="utf-8",
                    )
                    with self.assertRaises(ValueError):
                        load_profile(profile)
                    with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
                        self.assertEqual(
                            2,
                            main(
                                [
                                    "audit",
                                    str(self.policy_path),
                                    "--profile",
                                    str(profile),
                                    "--json",
                                    str(output),
                                ]
                            ),
                        )
                    self.assertFalse(output.exists())

    def test_json_exponent_overflow_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            text = json.dumps(self.data).replace(
                '"max_cost_usd": 0.08', '"max_cost_usd": 1e400'
            )
            path.write_text(text, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "finite"):
                load_profile(path)

    def test_finite_input_exposure_overflow_rejected(self):
        for field in ("input_usd_per_million", "latency_p95_ms"):
            data = copy.deepcopy(self.data)
            data["models"]["agent-primary"][field] = 1e308
            with self.assertRaisesRegex(ValueError, "finite arithmetic"):
                audit_policy(
                    load_litellm_config(self.policy_path), profile_from_data(data)
                )

    def test_huge_integer_arithmetic_rejected(self):
        data = copy.deepcopy(self.data)
        data["contracts"][0]["expected_input_tokens"] = 10**400
        with self.assertRaisesRegex(ValueError, "finite arithmetic"):
            audit_policy(load_litellm_config(self.policy_path), profile_from_data(data))

    def test_original_nan_false_safety_rejected(self):
        self.data["contracts"][0].update(
            max_cost_usd=float("nan"), max_latency_ms=float("nan")
        )
        self.data["models"]["agent-primary"]["latency_p95_ms"] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite"):
            profile_from_data(self.data)

    def test_latency_integer_conversion_overflow_rejected(self):
        data = copy.deepcopy(self.data)
        for facts in data["models"].values():
            facts["input_usd_per_million"] = None
        policy = load_litellm_config(self.policy_path)
        policy.retries = 10**400
        with self.assertRaisesRegex(ValueError, "latency exposure"):
            audit_policy(policy, profile_from_data(data))

    def test_arithmetic_overflow_cli_error_has_no_success_artifact(self):
        data = copy.deepcopy(self.data)
        data["models"]["agent-primary"]["input_usd_per_million"] = 1e308
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            output = Path(directory) / "report.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
                self.assertEqual(
                    2,
                    main(
                        [
                            "audit",
                            str(self.policy_path),
                            "--profile",
                            str(path),
                            "--json",
                            str(output),
                        ]
                    ),
                )
            self.assertFalse(output.exists())
