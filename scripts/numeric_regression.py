"""Evaluate exact installed loader behavior; usable with the old clean wheel."""

import copy
import json
import sys
from pathlib import Path

from fallbacklens import __version__
from fallbacklens.loaders import profile_from_data

root = Path(__file__).resolve().parents[1]
template = json.loads((root / "examples/profile-safe.json").read_text(encoding="utf-8"))
fields = [
    ("model", "input_usd_per_million"),
    ("model", "output_usd_per_million"),
    ("model", "latency_p95_ms"),
    ("contract", "max_cost_usd"),
    ("contract", "max_latency_ms"),
]
values = {
    "nan": float("nan"),
    "positive_inf": float("inf"),
    "negative_inf": -float("inf"),
    "huge_integer": 10**400,
}
results = []
for location, field in fields:
    for name, value in values.items():
        data = copy.deepcopy(template)
        target = (
            data["models"]["agent-primary"]
            if location == "model"
            else data["contracts"][0]
        )
        target[field] = value
        try:
            profile_from_data(data)
            observed = "accepted"
        except ValueError:
            observed = "controlled_rejection"
        except OverflowError:
            observed = "uncontrolled_overflow"
        results.append(
            {"field": f"{location}.{field}", "input": name, "observed": observed}
        )
report = {
    "schema_version": 1,
    "suite": "finite-assumptions-v1",
    "seed": 20261009,
    "package_version": __version__,
    "cases": len(results),
    "controlled_rejections": sum(
        row["observed"] == "controlled_rejection" for row in results
    ),
    "accepted": sum(row["observed"] == "accepted" for row in results),
    "uncontrolled_overflows": sum(
        row["observed"] == "uncontrolled_overflow" for row in results
    ),
    "results": results,
    "limits": "Authored numeric edge cases, not independent gateway traffic or a model benchmark.",
}
text = json.dumps(report, indent=2, allow_nan=False) + "\n"
if len(sys.argv) == 2:
    Path(sys.argv[1]).write_text(text, encoding="utf-8")
print(text)
