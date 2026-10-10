"""Command-line interface for FallbackLens."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .audit import audit_policy
from .benchmark import render_benchmark_svg, run_benchmark
from .interop import run_interop
from .loaders import load_litellm_config, load_profile
from .report import render_html, render_svg, render_terminal, write_json, write_text
from .simulate import load_scenarios, replay_scenarios
from .trace_benchmark import render_trace_benchmark_svg, run_trace_benchmark
from .traces import audit_traces, load_trace_json, render_trace_html


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fallbacklens",
        description="Audit and replay LLM fallback policies offline",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit = subparsers.add_parser(
        "audit", help="audit a LiteLLM configuration against workload contracts"
    )
    audit.add_argument("config")
    audit.add_argument("--profile", required=True)
    audit.add_argument("--json", dest="json_path")
    audit.add_argument("--html", dest="html_path")
    audit.add_argument("--svg", dest="svg_path")
    audit.add_argument(
        "--fail-on", choices=("error", "warning", "never"), default="error"
    )

    simulate = subparsers.add_parser(
        "simulate", help="replay bounded deterministic failure scenarios"
    )
    simulate.add_argument("config")
    simulate.add_argument("--scenarios", required=True)
    simulate.add_argument("--json", dest="json_path")

    benchmark = subparsers.add_parser(
        "benchmark", help="run the versioned static-policy comparison corpus"
    )
    benchmark.add_argument("cases")
    benchmark.add_argument("--json", dest="json_path")
    benchmark.add_argument("--svg", dest="svg_path")

    traces = subparsers.add_parser(
        "trace-audit",
        help="compare bound observed inference spans with contracts offline",
    )
    traces.add_argument("config")
    traces.add_argument("--profile", required=True)
    traces.add_argument("--trace", required=True)
    traces.add_argument("--bindings", required=True)
    traces.add_argument("--json", dest="json_path")
    traces.add_argument("--html", dest="html_path")
    trace_benchmark = subparsers.add_parser(
        "trace-benchmark", help="compare the authored OTLP regression corpus"
    )
    trace_benchmark.add_argument("cases")
    trace_benchmark.add_argument("--json", dest="json_path")
    trace_benchmark.add_argument("--svg", dest="svg_path")
    interop = subparsers.add_parser(
        "interop-run",
        help="optional LiteLLM instrumentation with network-denied mock responses",
    )
    interop.add_argument("--output", type=Path, required=True)
    interop.add_argument("--repetitions", type=int, default=3)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "interop-run":
            result = run_interop(args.output, args.repetitions)
            print(
                json.dumps(
                    {
                        key: result[key]
                        for key in (
                            "cases",
                            "expected_matches",
                            "actual_provider_cost_usd",
                        )
                    }
                )
            )
            return 0 if result["expected_matches"] == result["cases"] else 1
        if args.command == "trace-benchmark":
            result = run_trace_benchmark(load_trace_json(args.cases))
            print(json.dumps(result, indent=2, sort_keys=True))
            if args.json_path:
                write_json(result, args.json_path)
            if args.svg_path:
                write_text(args.svg_path, render_trace_benchmark_svg(result))
            return 0 if result["correct"] == result["cases"] else 1
        if args.command == "trace-audit":
            inputs = {
                Path(value).resolve()
                for value in (args.config, args.profile, args.trace, args.bindings)
            }
            outputs = [
                Path(value).resolve()
                for value in (args.json_path, args.html_path)
                if value
            ]
            if len(set(outputs)) != len(outputs) or inputs.intersection(outputs):
                raise ValueError(
                    "trace outputs must be distinct and must not overwrite input files"
                )
            result = audit_traces(
                load_litellm_config(args.config),
                load_profile(args.profile),
                load_trace_json(args.trace),
                load_trace_json(args.bindings),
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            if args.json_path:
                write_json(result, args.json_path)
            if args.html_path:
                write_text(args.html_path, render_trace_html(result))
            return (
                1
                if result["summary"]["drift"] or result["summary"]["inconclusive"]
                else 0
            )
        if args.command == "audit":
            report = audit_policy(
                load_litellm_config(args.config), load_profile(args.profile)
            )
            print(render_terminal(report))
            if args.json_path:
                write_json(report.to_dict(), args.json_path)
            if args.html_path:
                write_text(args.html_path, render_html(report))
            if args.svg_path:
                write_text(args.svg_path, render_svg(report))
            if args.fail_on == "error" and report.summary["errors"]:
                return 1
            if args.fail_on == "warning" and (
                report.summary["errors"] or report.summary["warnings"]
            ):
                return 1
            return 0
        if args.command == "simulate":
            result = replay_scenarios(
                load_litellm_config(args.config), load_scenarios(args.scenarios)
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            if args.json_path:
                write_json(result, args.json_path)
            return (
                0
                if result["summary"]["matched_expectation"]
                == result["summary"]["scenarios"]
                else 1
            )
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
