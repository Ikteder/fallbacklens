"""Bounded, content-minimizing reconciliation of operator-bound OTLP JSON exports."""

from __future__ import annotations

import html
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import Policy, Profile

INFERENCE = frozenset({"chat", "generate_content", "text_completion"})
ALIAS = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}\Z")
LIMITS = "Observed logical calls only; retries can be hidden inside a span. Missing/sampled telemetry can hide drift. Not provider attempts, complete coverage, billed cost, model quality, or production safety."


def _fail() -> None:
    # Never echo untrusted telemetry values, attribute keys, or parser excerpts.
    raise ValueError(
        "invalid or ambiguous trace/binding structure; see trace schema documentation"
    )


def _pairs(pairs: list[tuple[str, Any]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            _fail()
        result[key] = value
    return result


def load_trace_json(path: str | Path) -> dict:
    with Path(path).open("rb") as source:
        raw = source.read(10_000_001)
    if len(raw) > 10_000_000:
        _fail()
    try:
        result = json.loads(
            raw, object_pairs_hook=_pairs, parse_constant=lambda _: _fail()
        )
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError("invalid trace JSON; no raw content retained") from exc
    if not isinstance(result, dict):
        _fail()
    return result


def _list(value: Any, limit: int) -> list:
    if not isinstance(value, list) or len(value) > limit:
        _fail()
    return value


def _text(value: Any, limit: int = 512) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= limit:
        _fail()
    return value


def _id(value: Any, length: int) -> str:
    if (
        not isinstance(value, str)
        or not re.fullmatch(rf"[0-9a-fA-F]{{{length}}}", value)
        or int(value, 16) == 0
    ):
        _fail()
    return value.lower()


def _nano(value: Any) -> int:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{1,20}", value):
        _fail()
    result = int(value)
    if not 0 < result <= 2**64 - 1:
        _fail()
    return result


@dataclass(frozen=True)
class Span:
    trace: str
    identity: str
    parent: str | None
    start: int
    end: int
    scope: str
    kind: int
    operation: str | None
    model: str | None


def parse_spans(data: dict) -> dict[tuple[str, str], Span]:
    spans: dict[tuple[str, str], Span] = {}
    for resource in _list(data.get("resourceSpans"), 2000):
        if not isinstance(resource, dict):
            _fail()
        for scope_data in _list(resource.get("scopeSpans"), 2000):
            if not isinstance(scope_data, dict) or not isinstance(
                scope_data.get("scope"), dict
            ):
                _fail()
            scope = _text(scope_data["scope"].get("name"))
            for raw in _list(scope_data.get("spans"), 2000):
                if not isinstance(raw, dict) or len(spans) >= 2000:
                    _fail()
                trace, identity = (
                    _id(raw.get("traceId"), 32),
                    _id(raw.get("spanId"), 16),
                )
                parent = (
                    _id(raw["parentSpanId"], 16) if raw.get("parentSpanId") else None
                )
                start, end = (
                    _nano(raw.get("startTimeUnixNano")),
                    _nano(raw.get("endTimeUnixNano")),
                )
                kind = raw.get("kind")
                if isinstance(kind, str):
                    kind = {
                        "SPAN_KIND_INTERNAL": 1,
                        "SPAN_KIND_SERVER": 2,
                        "SPAN_KIND_CLIENT": 3,
                        "SPAN_KIND_PRODUCER": 4,
                        "SPAN_KIND_CONSUMER": 5,
                    }.get(kind)
                if (
                    type(kind) is not int
                    or kind not in range(1, 6)
                    or end < start
                    or (trace, identity) in spans
                ):
                    _fail()
                attributes: dict[str, str] = {}
                seen: set[str] = set()
                for attribute in _list(raw.get("attributes", []), 128):
                    if not isinstance(attribute, dict):
                        _fail()
                    key = _text(attribute.get("key"))
                    if key in seen:
                        _fail()
                    seen.add(key)
                    if key in {"gen_ai.operation.name", "gen_ai.request.model"}:
                        value = attribute.get("value")
                        if not isinstance(value, dict) or set(value) != {"stringValue"}:
                            _fail()
                        attributes[key] = _text(value["stringValue"])
                spans[trace, identity] = Span(
                    trace,
                    identity,
                    parent,
                    start,
                    end,
                    scope,
                    kind,
                    attributes.get("gen_ai.operation.name"),
                    attributes.get("gen_ai.request.model"),
                )
    if not spans:
        _fail()
    # Iterative ancestry, bounded by export size; no recursion on untrusted parent chains.
    for span in spans.values():
        seen = {span.identity}
        cursor = span
        while cursor.parent and (cursor.trace, cursor.parent) in spans:
            if cursor.parent in seen or len(seen) >= 64:
                _fail()
            seen.add(cursor.parent)
            cursor = spans[cursor.trace, cursor.parent]
    return spans


def _ancestor(span: Span, root: Span, spans: dict[tuple[str, str], Span]) -> bool:
    cursor = span
    while cursor.trace == root.trace:
        if cursor.identity == root.identity:
            return True
        if not cursor.parent or (cursor.trace, cursor.parent) not in spans:
            return False
        cursor = spans[cursor.trace, cursor.parent]
    return False


def audit_traces(policy: Policy, profile: Profile, data: dict, bindings: dict) -> dict:
    spans = parse_spans(data)
    if (
        type(bindings.get("schema_version")) is not int
        or bindings["schema_version"] != 1
    ):
        _fail()
    if not isinstance(bindings.get("as_of"), str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}", bindings["as_of"]
    ):
        _fail()
    scopes = {_text(scope) for scope in _list(bindings.get("scopes"), 32)}
    mapping = bindings.get("model_groups")
    if not scopes or not isinstance(mapping, dict) or not 1 <= len(mapping) <= 256:
        _fail()
    for model, group in mapping.items():
        _text(model)
        if (
            not isinstance(group, str)
            or not ALIAS.fullmatch(group)
            or group not in policy.nodes
        ):
            _fail()
    contracts = {contract.name: contract for contract in profile.contracts}
    if len(contracts) != len(profile.contracts) or any(
        not ALIAS.fullmatch(name) for name in contracts
    ):
        _fail()
    if any(not ALIAS.fullmatch(node) for node in policy.nodes):
        _fail()
    bound: list[tuple[Span, Any]] = []
    for request in _list(bindings.get("requests"), 100):
        if not isinstance(request, dict) or set(request) != {
            "trace_id",
            "root_span_id",
            "contract",
        }:
            _fail()
        identity = (_id(request["trace_id"], 32), _id(request["root_span_id"], 16))
        name = request["contract"]
        if identity not in spans or not isinstance(name, str) or name not in contracts:
            _fail()
        root = spans[identity]
        if any(
            _ancestor(root, prior, spans) or _ancestor(prior, root, spans)
            for prior, _ in bound
        ):
            _fail()
        contract = contracts[name]
        if (
            not math.isfinite(contract.max_latency_ms)
            or contract.entrypoint not in policy.nodes
        ):
            _fail()
        bound.append((root, contract))
    if not bound:
        _fail()
    requests = []
    for index, (root, contract) in enumerate(bound, 1):
        subtree = [span for span in spans.values() if _ancestor(span, root, spans)]
        uncertain, drift = [], []
        if any(finding.severity == "error" for finding in policy.findings):
            uncertain.append("INVALID_POLICY_STRUCTURE")
        # A root binding cuts an external parent intentionally. Other missing links in
        # this trace could contain omitted inference calls: do not certify their absence.
        if any(
            span.trace == root.trace
            and span != root
            and span.parent
            and (span.trace, span.parent) not in spans
            for span in spans.values()
        ):
            uncertain.append("PARENT_GAP")
        for span in subtree:
            if span.start < root.start or span.end > root.end:
                _fail()
            if span != root and span.parent:
                parent = spans[span.trace, span.parent]
                if span.start < parent.start or span.end > parent.end:
                    _fail()
        candidates = [
            span
            for span in subtree
            if span.scope in scopes and span.kind == 3 and span.operation in INFERENCE
        ]
        if len(candidates) > 256:
            _fail()
        if any(
            span.scope in scopes and span.kind == 1 and span.operation in INFERENCE
            for span in subtree
        ):
            uncertain.append("INTERNAL_INFERENCE_UNSUPPORTED")
        known = []
        for span in candidates:
            if span.model not in mapping:
                uncertain.append("MODEL_MAPPING_UNKNOWN")
            else:
                known.append(span)
        leaves = []
        for span in known:
            descendants = [
                child
                for child in known
                if child != span and _ancestor(child, span, spans)
            ]
            if descendants:
                if any(
                    mapping[child.model] != mapping[span.model] for child in descendants
                ):
                    uncertain.append("NESTED_ROUTE_AMBIGUOUS")
            else:
                leaves.append(span)
        leaves.sort(key=lambda span: (span.start, span.end, span.identity))
        if not leaves:
            uncertain.append("NO_SUPPORTED_CALLS")
        overlap = any(
            left.end > right.start
            for left, right in zip(leaves, leaves[1:], strict=False)
        )
        if overlap:
            uncertain.append("PARALLEL_ROUTE_ORDER_UNKNOWN")
        groups = [mapping[span.model] for span in leaves]
        duration = (
            (max(span.end for span in leaves) - min(span.start for span in leaves))
            / 1_000_000
            if leaves
            else None
        )
        # Wrapper ambiguity invalidates interpreting the leaf sequence as this contract.
        if not uncertain:
            if len(leaves) > contract.max_attempts:
                drift.append("LOGICAL_CALL_THRESHOLD_EXCEEDED")
            if duration is not None and duration > contract.max_latency_ms:
                drift.append("OBSERVED_LATENCY_EXCEEDED")
            if groups[0] != contract.entrypoint:
                drift.append("ENTRYPOINT_DRIFT")
            edges = {(edge.source, edge.target) for edge in policy.edges}
            if any(
                left != right and (left, right) not in edges
                for left, right in zip(groups, groups[1:], strict=False)
            ):
                drift.append("UNCONFIGURED_TRANSITION")
            if policy.retries is None:
                uncertain.append("RETRY_POLICY_UNKNOWN")
            elif any(count > policy.retries + 1 for count in Counter(groups).values()):
                drift.append("LOGICAL_GROUP_CALL_THRESHOLD_EXCEEDED")
        verdict = (
            "inconclusive" if uncertain else "drift" if drift else "observed-no-drift"
        )
        requests.append(
            {
                "request": index,
                "contract": contract.name,
                "verdict": verdict,
                "findings": sorted(set(uncertain + drift)),
                "observed_logical_calls": len(leaves),
                "nested_wrappers_removed": len(known) - len(leaves),
                "inference_envelope_ms": duration,
                "call_threshold": contract.max_attempts,
                "latency_threshold_ms": contract.max_latency_ms,
                "calls": [
                    {
                        "group": mapping[span.model],
                        "start_ms": (span.start - root.start) / 1_000_000,
                        "duration_ms": (span.end - span.start) / 1_000_000,
                    }
                    for span in leaves
                ],
            }
        )
    return {
        "schema_version": 1,
        "suite": "observed-trace-contract-v1",
        "bindings_as_of": bindings["as_of"],
        "limits": LIMITS,
        "summary": {
            "requests": len(requests),
            **{
                verdict: sum(r["verdict"] == verdict for r in requests)
                for verdict in ("observed-no-drift", "drift", "inconclusive")
            },
        },
        "requests": requests,
    }


def render_trace_html(report: dict) -> str:
    rows = "".join(
        f"<tr><td>{r['request']}</td><td>{html.escape(r['contract'])}</td><td>{r['verdict']}</td>"
        f"<td>{r['observed_logical_calls']}</td><td>{r['inference_envelope_ms']}</td></tr>"
        for r in report["requests"]
    )
    evidence = html.escape(json.dumps(report, indent=2))
    return f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>FallbackLens observed trace contracts</title><style>*{{box-sizing:border-box}}body{{background:#101827;color:#e2e8f0;
font:16px/1.6 system-ui;margin:0}}main{{max-width:1100px;margin:auto;padding:28px 20px}}h1{{font-size:clamp(28px,5vw,42px)}}
.table{{overflow:auto}}table{{width:100%;border-collapse:collapse}}th,td{{padding:12px;text-align:left;border-bottom:1px solid #475569}}
pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#1e293b;padding:16px;border-radius:10px}}</style><main>
<h1>Observed route, not inferred safety</h1><p>{html.escape(LIMITS)}</p><div class="table"><table><thead><tr>
<th>Request</th><th>Contract</th><th>Verdict</th><th>Logical calls</th><th>Envelope ms</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Content-minimized evidence</h2><pre>{evidence}</pre></main></html>"""
