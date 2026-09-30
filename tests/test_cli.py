from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def test_audit_writes_all_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "fallbacklens",
                    "audit",
                    str(ROOT / "examples" / "litellm-safe.yaml"),
                    "--profile",
                    str(ROOT / "examples" / "profile-safe.json"),
                    "--json",
                    str(output / "report.json"),
                    "--html",
                    str(output / "report.html"),
                    "--svg",
                    str(output / "graph.svg"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("0 error(s)", result.stdout)
            for name in ("report.json", "report.html", "graph.svg"):
                self.assertGreater((output / name).stat().st_size, 100)

    def test_invalid_input_exits_two(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "fallbacklens", "audit", "missing.yaml", "--profile", "missing.json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(2, result.returncode)


if __name__ == "__main__":
    unittest.main()
