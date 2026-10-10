"""Export only the minimized interop report, never raw SDK exports or worker logs."""

import argparse
import json
from pathlib import Path

from fallbacklens.traces import render_trace_html

parser = argparse.ArgumentParser()
parser.add_argument("report", type=Path)
args = parser.parse_args()
report = json.loads(args.report.read_text(encoding="utf-8"))
assert report["suite"] == "litellm-mock-interop-v1"
assert report["cases"] == report["expected_matches"] == 9
assert all(
    case["mock_http_requests"] == 1 and case["external_sockets_allowed"] == 0
    for case in report["results"]
)
root = Path(__file__).resolve().parents[1]
(root / "docs/experiments/litellm-mock-interop-v1.json").write_text(
    json.dumps(report, indent=2) + "\n", encoding="utf-8"
)
requests = [
    {**case["report"]["requests"][0], "request": index, "configuration": case["case"]}
    for index, case in enumerate(report["results"], 1)
]
view = {
    "limits": report["limits"],
    "requests": requests,
    "summary": {"requests": 9, "observed-no-drift": 3, "inconclusive": 6, "drift": 0},
}
(args.report.parent / "report.html").write_text(
    render_trace_html(view), encoding="utf-8"
)
print("Exported nine minimized instrumentation cases; no raw spans or IDs published")
