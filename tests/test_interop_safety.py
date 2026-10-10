import json
import socket
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fallbacklens.interop import (
    deny_external_sockets,
    isolated_environment,
    run_interop,
)


class InteropSafetyTests(unittest.TestCase):
    def test_environment_does_not_inherit_provider_or_export_credentials(self):
        environment = isolated_environment(
            {
                "PATH": "tools",
                "SYSTEMROOT": "windows",
                "OPENAI_API_KEY": "private",
                "OTEL_EXPORTER_OTLP_ENDPOINT": "private",
                "CUSTOM_SECRET": "private",
                "HTTPS_PROXY": "private",
            }
        )
        self.assertEqual("tools", environment["PATH"])
        self.assertNotIn("private", environment.values())

    def test_external_dns_and_connects_blocked_and_restored(self):
        originals = (
            socket.socket.connect,
            socket.socket.connect_ex,
            socket.getaddrinfo,
        )
        with deny_external_sockets() as counts:
            with self.assertRaises(OSError):
                socket.getaddrinfo("fixture.invalid", 443)
            with socket.socket() as sock:
                with self.assertRaises(OSError):
                    sock.connect(("192.0.2.1", 443))
                with self.assertRaises(OSError):
                    sock.connect_ex(("192.0.2.1", 443))
            self.assertEqual(3, counts["blocked_external_operations"])
        self.assertEqual(
            originals,
            (socket.socket.connect, socket.socket.connect_ex, socket.getaddrinfo),
        )

    def test_existing_interop_output_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            marker = path / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                run_interop(path)
            self.assertEqual("keep", marker.read_text(encoding="utf-8"))

    def test_invalid_repetitions_have_no_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "new"
            for repetitions in (0, 11, True):
                with self.assertRaises(ValueError):
                    run_interop(path, repetitions=repetitions)
            self.assertFalse(path.exists())

    def test_timeout_preserves_failure_without_raw_process_content(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "new"
            timeout = subprocess.TimeoutExpired("worker", 1, stderr="private")
            with patch("fallbacklens.interop.subprocess.run", side_effect=timeout):
                with self.assertRaisesRegex(ValueError, "timed out"):
                    run_interop(path, repetitions=1, timeout=1)
            failure = path / "experimental-dedicated-0" / "failure.json"
            self.assertEqual(
                {"reason": "worker_timeout", "timeout_seconds": 1},
                json.loads(failure.read_text(encoding="utf-8")),
            )
            self.assertNotIn("private", failure.read_text(encoding="utf-8"))
            self.assertFalse((path / "report.json").exists())

    def test_invalid_timeout_has_no_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "new"
            for timeout in (0, 121, float("inf"), float("nan")):
                with self.assertRaises(ValueError):
                    run_interop(path, timeout=timeout)
            self.assertFalse(path.exists())
