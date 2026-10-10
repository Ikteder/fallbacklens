"""Regenerate only authored project fixtures and content-minimized evidence."""

import json
from pathlib import Path

from fallbacklens.trace_benchmark import (
    corpus,
    render_trace_benchmark_svg,
    run_trace_benchmark,
)
from fallbacklens.traces import render_trace_html

root = Path(__file__).resolve().parents[1]
data = corpus()
result = run_trace_benchmark(data)
for relative, value in (
    ("benchmarks/trace-cases-v1.json", data),
    ("docs/experiments/trace-comparison-v1.json", result),
    ("examples/trace-otlp.json", data["cases"][0]["trace"]),
    ("examples/trace-bindings.json", data["cases"][0]["bindings"]),
    ("examples/trace-policy.json", data["cases"][0]["policy"]),
    ("examples/trace-profile.json", data["cases"][0]["profile"]),
):
    (root / relative).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
(root / "docs/assets/trace-comparison-v1.svg").write_text(
    render_trace_benchmark_svg(result), encoding="utf-8"
)
artifacts = root / "artifacts/trace-v1"
artifacts.mkdir(parents=True, exist_ok=True)
(artifacts / "report.html").write_text(
    render_trace_html(result["results"][0]["report"]), encoding="utf-8"
)
(artifacts / "comparison.svg").write_text(
    render_trace_benchmark_svg(result), encoding="utf-8"
)
print(
    json.dumps({key: result[key] for key in ("cases", "correct", "baseline_correct")})
)
