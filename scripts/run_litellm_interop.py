"""Optional mock-only check. Install .[interop] first; output directory must be new."""

import argparse
import json
from pathlib import Path

from fallbacklens.interop import run_interop

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--repetitions", type=int, default=3)
args = parser.parse_args()
report = run_interop(args.output, args.repetitions)
print(
    json.dumps(
        {
            key: report[key]
            for key in ("cases", "expected_matches", "actual_provider_cost_usd")
        }
    )
)
raise SystemExit(0 if report["expected_matches"] == report["cases"] else 1)
