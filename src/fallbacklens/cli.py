"""Command-line interface for FallbackLens."""

from __future__ import annotations

import argparse
import json
import sys

from .audit import audit_policy
from .benchmark import render_benchmark_svg, run_benchmark
from .loaders import load_litellm_config, load_profile
from .report import render_html, render_svg, render_terminal, write_json, write_text
from .simulate import load_scenarios, replay_scenarios


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fallbacklens", description="Audit and replay LLM fallback policies offline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit = subparsers.add_parser("audit", help="audit a LiteLLM configuration against workload contracts")
    audit.add_argument("config")
    audit.add_argument("--profile", required=True)
    audit.add_argument("--json", dest="json_path")
    audit.add_argument("--html", dest="html_path")
    audit.add_argument("--svg", dest="svg_path")
    audit.add_argument("--fail-on", choices=("error", "warning", "never"), default="error")

    simulate = subparsers.add_parser("simulate", help="replay bounded deterministic failure scenarios")
    simulate.add_argument("config")
    simulate.add_argument("--scenarios", required=True)
    simulate.add_argument("--json", dest="json_path")

    benchmark = subparsers.add_parser("benchmark", help="run the versioned static-policy comparison corpus")
    benchmark.add_argument("cases")
    benchmark.add_argument("--json", dest="json_path")
    benchmark.add_argument("--svg", dest="svg_path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "audit":
            report = audit_policy(load_litellm_config(args.config), load_profile(args.profile))
            print(render_terminal(report))
            if args.json_path:
                write_json(report.to_dict(), args.json_path)
            if args.html_path:
                write_text(args.html_path, render_html(report))
            if args.svg_path:
                write_text(args.svg_path, render_svg(report))
            if args.fail_on == "error" and report.summary["errors"]:
                return 1
            if args.fail_on == "warning" and (report.summary["errors"] or report.summary["warnings"]):
                return 1
            return 0
        if args.command == "simulate":
            result = replay_scenarios(load_litellm_config(args.config), load_scenarios(args.scenarios))
            print(json.dumps(result, indent=2, sort_keys=True))
            if args.json_path:
                write_json(result, args.json_path)
            return 0 if result["summary"]["matched_expectation"] == result["summary"]["scenarios"] else 1
        if args.command == "benchmark":
            result = run_benchmark(args.cases)
            print(json.dumps(result, indent=2, sort_keys=True))
            if args.json_path:
                write_json(result, args.json_path)
            if args.svg_path:
                write_text(args.svg_path, render_benchmark_svg(result))
            return 0 if result["fallbacklens"]["correct"] == result["cases"] else 1
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"fallbacklens: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
