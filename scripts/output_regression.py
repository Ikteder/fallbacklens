"""Measure old/new installed CLI only against disposable synthetic copies."""

import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path

from fallbacklens import __version__
from fallbacklens.cli import main

root = Path(__file__).resolve().parents[1]
results = []
for case in ("audit-input", "audit-output-collision"):
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        policy = base / "policy.yaml"
        profile = base / "profile.json"
        policy.write_bytes((root / "examples/litellm-safe.yaml").read_bytes())
        profile.write_bytes((root / "examples/profile-safe.json").read_bytes())
        before = profile.read_bytes()
        output = profile if case == "audit-input" else base / "report.json"
        args = ["audit", str(policy), "--profile", str(profile), "--json", str(output)]
        if case == "audit-output-collision":
            args += ["--html", str(output)]
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            code = main(args)
        results.append(
            {
                "case": case,
                "exit_code": code,
                "input_preserved": profile.read_bytes() == before,
                "output_created": output.exists() if case != "audit-input" else None,
                "controlled_rejection": code == 2,
            }
        )
report = {
    "package_version": __version__,
    "suite": "cli-output-preservation-v1",
    "seed": 20261009,
    "cases": 2,
    "controlled_rejections": sum(row["controlled_rejection"] for row in results),
    "results": results,
}
text = json.dumps(report, indent=2) + "\n"
if len(sys.argv) == 2:
    Path(sys.argv[1]).write_text(text, encoding="utf-8")
print(text)
