"""Optional, network-denied instrumentation checks with synthetic mocked responses."""

from __future__ import annotations

import json
import math
import os
import socket
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

CASES = {
    "experimental-dedicated": "observed-no-drift",
    "legacy-dedicated": "inconclusive",
    "experimental-collapsed": "inconclusive",
}
ENV_ALLOWLIST = frozenset(
    {
        "PATH",
        "SYSTEMROOT",
        "WINDIR",
        "TEMP",
        "TMP",
        "USERPROFILE",
        "APPDATA",
        "LOCALAPPDATA",
        "COMSPEC",
    }
)


def isolated_environment(source: dict[str, str]) -> dict[str, str]:
    result = {
        key: value for key, value in source.items() if key.upper() in ENV_ALLOWLIST
    }
    result.update({"LITELLM_LOCAL_MODEL_COST_MAP": "True", "PYTHONIOENCODING": "utf-8"})
    return result


@contextmanager
def deny_external_sockets():
    original_connect, original_connect_ex, original_dns = (
        socket.socket.connect,
        socket.socket.connect_ex,
        socket.getaddrinfo,
    )
    counts = {"blocked_external_operations": 0}

    def validate(host):
        if host not in (
            "127.0.0.1",
            "::1",
            "localhost",
            b"localhost",
            b"127.0.0.1",
            b"::1",
        ):
            counts["blocked_external_operations"] += 1
            raise OSError("external networking disabled by interoperability fixture")

    def connect(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            validate(address[0])
        return original_connect(sock, address)

    def connect_ex(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            validate(address[0])
        return original_connect_ex(sock, address)

    def dns(host, *args, **kwargs):
        validate(host)
        return original_dns(host, *args, **kwargs)

    socket.socket.connect, socket.socket.connect_ex, socket.getaddrinfo = (
        connect,
        connect_ex,
        dns,
    )
    try:
        yield counts
    finally:
        socket.socket.connect, socket.socket.connect_ex, socket.getaddrinfo = (
            original_connect,
            original_connect_ex,
            original_dns,
        )


def run_interop(output: Path, repetitions: int = 3, timeout: float = 60) -> dict:
    if type(repetitions) is not int or not 1 <= repetitions <= 10:
        raise ValueError("interop repetitions must be1 to10")
    if not math.isfinite(timeout) or not 0 < timeout <= 120:
        raise ValueError("interop timeout must be finite and in(0,120]")
    output.mkdir(parents=True, exist_ok=False)
    results = []
    for name, expected in CASES.items():
        for repetition in range(repetitions):
            directory = output / f"{name}-{repetition}"
            directory.mkdir()
            try:
                process = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "fallbacklens.interop_worker",
                        "--case",
                        name,
                        "--output",
                        str(directory),
                    ],
                    env=isolated_environment(dict(os.environ)),
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired:
                (directory / "failure.json").write_text(
                    json.dumps({"reason": "worker_timeout", "timeout_seconds": timeout})
                    + "\n",
                    encoding="utf-8",
                )
                raise ValueError(
                    "optional instrumentation worker timed out; local failure preserved"
                ) from None
            if process.returncode:
                # Workers have only authored synthetic inputs. Do not echo their raw
                # library logs; preserve locally for diagnosis, not publication.
                (directory / "worker-stderr.txt").write_text(
                    process.stderr, encoding="utf-8"
                )
                raise ValueError(
                    "optional instrumentation worker failed; local diagnostics preserved"
                )
            evidence = json.loads(
                (directory / "evidence.json").read_text(encoding="utf-8")
            )
            results.append(
                {
                    "case": name,
                    "repetition": repetition,
                    "expected": expected,
                    **evidence,
                }
            )
    report = {
        "schema_version": 1,
        "suite": "litellm-mock-interop-v1",
        "seed": 20261009,
        "cases": len(results),
        "expected_matches": sum(r["verdict"] == r["expected"] for r in results),
        "actual_provider_cost_usd": 0.0,
        "results": results,
        "limits": "Actual instrumentation with mocked completion, not real gateway fallback, paid provider inference, streaming or production traces.",
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report
