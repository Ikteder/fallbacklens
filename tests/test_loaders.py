from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from fallbacklens.loaders import (
    load_litellm_config,
    policy_from_data,
    profile_from_data,
)


class LoaderTests(unittest.TestCase):
    def test_safe_yaml_loader_does_not_construct_python_objects(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unsafe.yaml"
            path.write_text("!!python/object/apply:os.system ['echo unsafe']\n", encoding="utf-8")
            with self.assertRaises(yaml.YAMLError):
                load_litellm_config(path)

    def test_all_three_fallback_kinds_are_loaded(self) -> None:
        policy = policy_from_data(
            {
                "model_list": [{"model_name": name} for name in ("a", "b", "c")],
                "router_settings": {
                    "num_retries": 0,
                    "fallbacks": [{"a": "b"}],
                    "context_window_fallbacks": [{"a": "c"}],
                    "content_policy_fallbacks": [{"b": "c"}],
                },
            }
        )
        self.assertEqual(["content_policy", "context_window", "general"], sorted(edge.kind for edge in policy.edges))

    def test_profile_rejects_missing_sources(self) -> None:
        with self.assertRaisesRegex(ValueError, "sources"):
            profile_from_data({"schema_version": 1, "as_of": "2026-09-30", "models": {}, "contracts": []})


if __name__ == "__main__":
    unittest.main()
