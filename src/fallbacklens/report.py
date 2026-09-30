"""Deterministic JSON, HTML, SVG, and terminal report rendering."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .models import AuditReport


def write_json(data: dict[str, Any], path: str | Path) -> None:
    write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def write_text(path: str | Path, content: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def render_terminal(report: AuditReport) -> str:
    summary = report.summary
    lines = [
        f"FallbackLens: {summary['errors']} error(s), {summary['warnings']} warning(s)",
        f"Graph: {len(report.policy.nodes)} model group(s), {len(report.policy.edges)} fallback edge(s), retries={report.policy.retries}",
    ]
    for metric in report.metrics:
        cost = "unknown" if metric.max_cost_usd is None else f"${metric.max_cost_usd:.6f}"
        latency = "unknown" if metric.max_latency_ms is None else f"{metric.max_latency_ms:.1f} ms"
        lines.append(
            f"Contract {metric.name}: paths={metric.path_count}, attempts={metric.max_attempts}, cost={cost}, latency={latency}"
        )
    for finding in report.findings:
        contract = f" [{finding.contract}]" if finding.contract else ""
        lines.append(f"{finding.severity.upper()} {finding.code}{contract}: {finding.message}")
    return "\n".join(lines)


def render_html(report: AuditReport) -> str:
    data = report.to_dict()
    summary = report.summary
    rows = "".join(
        "<tr>"
        f"<td><span class='badge {html.escape(finding.severity)}'>{html.escape(finding.severity)}</span></td>"
        f"<td><code>{html.escape(finding.code)}</code></td>"
        f"<td>{html.escape(finding.contract or 'global')}</td>"
        f"<td>{html.escape(finding.message)}</td>"
        "</tr>"
        for finding in report.findings
    ) or "<tr><td colspan='4'>No findings.</td></tr>"
    metric_rows = "".join(
        "<tr>"
        f"<td>{html.escape(metric.name)}</td>"
        f"<td>{metric.path_count if metric.path_count is not None else 'unbounded'}</td>"
        f"<td>{metric.max_attempts if metric.max_attempts is not None else 'unknown'}</td>"
        f"<td>{'unknown' if metric.max_cost_usd is None else f'${metric.max_cost_usd:.6f}'}</td>"
        f"<td>{'unknown' if metric.max_latency_ms is None else f'{metric.max_latency_ms:.1f} ms'}</td>"
        "</tr>"
        for metric in report.metrics
    )
    embedded = json.dumps(data, sort_keys=True).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FallbackLens audit report</title>
<style>
:root{{--ink:#172033;--muted:#60708b;--paper:#f5f7fb;--panel:#fff;--good:#16794b;--warn:#a15c00;--bad:#b42318;--line:#d8dfeb}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 system-ui,sans-serif}}
main{{max-width:1100px;margin:auto;padding:32px 18px 60px}} h1{{margin:0 0 6px;font-size:clamp(28px,5vw,48px)}} .lead{{color:var(--muted);max-width:760px}}
.cards{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:24px 0}} .card{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px}}
.number{{font-size:34px;font-weight:750}} .error .number{{color:var(--bad)}} .warning .number{{color:var(--warn)}} .ok .number{{color:var(--good)}}
.table-wrap{{overflow:auto;background:var(--panel);border:1px solid var(--line);border-radius:14px;margin:14px 0 28px}} table{{width:100%;border-collapse:collapse;min-width:700px}} th,td{{padding:12px 14px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}} th{{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}}
.badge{{display:inline-block;border-radius:999px;padding:2px 8px;font-weight:700}} .badge.error{{color:var(--bad);background:#fee4e2}} .badge.warning{{color:var(--warn);background:#fff0c2}} .badge.info{{color:#175cd3;background:#e8f1ff}}
code{{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}} @media(max-width:620px){{.cards{{grid-template-columns:1fr}} main{{padding-top:22px}}}}
</style>
</head>
<body><main>
<p>OFFLINE ROUTE CONTRACT AUDIT</p><h1>FallbackLens</h1>
<p class="lead">Profile facts dated {html.escape(report.profile.as_of)}. Exposure values are conservative configuration bounds, not bills or SLO predictions.</p>
<section class="cards">
<article class="card error"><div class="number">{summary['errors']}</div><div>errors</div></article>
<article class="card warning"><div class="number">{summary['warnings']}</div><div>warnings</div></article>
<article class="card ok"><div class="number">{len(report.policy.nodes)}</div><div>model groups</div></article>
</section>
<h2>Contract exposure</h2><div class="table-wrap"><table><thead><tr><th>Contract</th><th>Paths</th><th>Attempts</th><th>Cost bound</th><th>Latency bound</th></tr></thead><tbody>{metric_rows}</tbody></table></div>
<h2>Findings</h2><div class="table-wrap"><table><thead><tr><th>Severity</th><th>Code</th><th>Scope</th><th>Evidence</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="lead">Static success does not replace live provider validation, failure injection, or terms review.</p>
<script type="application/json" id="fallbacklens-report">{embedded}</script>
</main></body></html>"""


def render_svg(report: AuditReport) -> str:
    nodes = sorted(report.policy.nodes)
    error_nodes = {node for finding in report.findings if finding.severity == "error" for node in finding.nodes}
    width = max(820, 220 + len(nodes) * 170)
    height = 310
    positions = {node: (80 + index * 170, 155) for index, node in enumerate(nodes)}
    edge_parts: list[str] = []
    for edge in report.policy.edges:
        if edge.source not in positions or edge.target not in positions:
            continue
        x1, y1 = positions[edge.source]
        x2, y2 = positions[edge.target]
        bend = -45 if edge.kind == "context_window" else (45 if edge.kind == "content_policy" else 0)
        mid_x = (x1 + x2) / 2
        edge_parts.append(
            f'<path d="M {x1 + 65} {y1} Q {mid_x} {y1 + bend} {x2 - 65} {y2}" fill="none" stroke="#8290a8" stroke-width="2" marker-end="url(#arrow)"/>'
        )
    node_parts: list[str] = []
    for node, (x, y) in positions.items():
        is_error = node in error_nodes
        fill = "#fee4e2" if is_error else "#e7f8ef"
        stroke = "#b42318" if is_error else "#16794b"
        label = html.escape(node)
        node_parts.append(
            f'<rect x="{x - 65}" y="{y - 32}" width="130" height="64" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
            f'<text x="{x}" y="{y + 5}" text-anchor="middle" font-size="14" font-weight="700" fill="#172033">{label}</text>'
        )
    summary = report.summary
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">FallbackLens verified route graph</title>
<desc id="desc">{len(nodes)} model groups and {len(report.policy.edges)} fallback edges with {summary['errors']} errors and {summary['warnings']} warnings.</desc>
<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#8290a8"/></marker></defs>
<rect width="100%" height="100%" rx="18" fill="#f5f7fb"/>
<text x="40" y="48" font-size="26" font-weight="750" fill="#172033">Fallback policy evidence</text>
<text x="40" y="76" font-size="14" fill="#60708b">{summary['errors']} errors · {summary['warnings']} warnings · retries {report.policy.retries}</text>
{''.join(edge_parts)}{''.join(node_parts)}
<text x="40" y="278" font-size="13" fill="#60708b">Green nodes satisfy declared contracts in this static audit. Red nodes have error findings.</text>
</svg>
"""
