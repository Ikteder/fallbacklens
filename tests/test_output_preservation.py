import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path

from fallbacklens.cli import main


class OutputPreservationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.paths = [self.base / f"input{index}.json" for index in range(4)]
        for path in self.paths:
            path.write_bytes(b"KEEP INPUT BYTES")

    def commands(self):
        a, b, c, d = map(str, self.paths)
        return [
            (["audit", a, "--profile", b], self.paths[:2]),
            (["simulate", a, "--scenarios", b], self.paths[:2]),
            (["benchmark", a], self.paths[:1]),
            (["trace-benchmark", a], self.paths[:1]),
            (
                ["trace-audit", a, "--profile", b, "--trace", c, "--bindings", d],
                self.paths,
            ),
        ]

    def rejected(self, args):
        error = io.StringIO()
        with (
            contextlib.redirect_stderr(error),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(2, main(args))
        self.assertIn("outputs must be distinct", error.getvalue())
        self.assertTrue(
            all(path.read_bytes() == b"KEEP INPUT BYTES" for path in self.paths)
        )

    def test_every_command_input_preserved(self):
        for args, inputs in self.commands():
            for path in inputs:
                with self.subTest(command=args[0], input=path.name):
                    self.rejected([*args, "--json", str(path)])

    def test_duplicate_outputs_preserved_before_parsing(self):
        for args, _ in self.commands():
            if args[0] == "simulate":
                continue
            output = self.base / "report.json"
            output.write_bytes(b"KEEP REPORT BYTES")
            second = "--html" if args[0] in ("audit", "trace-audit") else "--svg"
            self.rejected([*args, "--json", str(output), second, str(output)])
            self.assertEqual(b"KEEP REPORT BYTES", output.read_bytes())

    def test_hard_link_input_alias_rejected(self):
        alias = self.base / "alias.json"
        os.link(self.paths[0], alias)
        for args, _ in self.commands():
            self.rejected([*args, "--json", str(alias)])
        self.assertEqual(b"KEEP INPUT BYTES", alias.read_bytes())

    def test_hard_link_output_alias_rejected(self):
        first, second = self.base / "report.json", self.base / "report.html"
        first.write_bytes(b"KEEP REPORT BYTES")
        os.link(first, second)
        self.rejected(
            [*self.commands()[0][0], "--json", str(first), "--html", str(second)]
        )
        self.assertEqual(b"KEEP REPORT BYTES", first.read_bytes())
        self.assertEqual(b"KEEP REPORT BYTES", second.read_bytes())

    def test_parent_component_alias_rejected(self):
        (self.base / "nested").mkdir()
        output = self.base / "nested" / ".." / self.paths[0].name
        self.rejected([*self.commands()[0][0], "--json", str(output)])

    def test_symbolic_input_alias_rejected_when_supported(self):
        alias = self.base / "symbolic.json"
        try:
            alias.symlink_to(self.paths[0])
        except OSError as error:
            self.skipTest(f"symbolic link unavailable: {type(error).__name__}")
        self.rejected([*self.commands()[0][0], "--json", str(alias)])
