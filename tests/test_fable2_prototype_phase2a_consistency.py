from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1] / "tools"
MODULE_PATH = TOOLS / "VerifyFable2PrototypePhase2AConsistency.py"
SPEC = importlib.util.spec_from_file_location("phase2a_consistency", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
consistency = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = consistency
SPEC.loader.exec_module(consistency)


class Phase2AConsistencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.identities: dict[str, dict[str, object]] = {}
        for key, relative_path in consistency.ARTIFACTS.items():
            path = self.root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((key + "\n").encode("ascii"))
            self.identities[key] = {
                "ignored_repository_relative_path": relative_path.as_posix(),
                "size": path.stat().st_size,
                "sha256": consistency.sha256_file(path),
            }
        self.summary = self.root / "summary.json"
        self.report = self.root / "report.md"
        self.write_summary()
        self.write_report()

    def write_summary(self) -> None:
        self.summary.write_text(
            json.dumps(self.identities, sort_keys=True), encoding="utf-8"
        )

    def write_report(self) -> None:
        lines = ["| Artifact | Size | SHA-256 |", "| --- | ---: | --- |"]
        for key, relative_path in consistency.ARTIFACTS.items():
            identity = self.identities[key]
            lines.append(
                f"| `{relative_path.as_posix()}` | {identity['size']:,} | "
                f"`{identity['sha256']}` |"
            )
        self.report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def validate(self) -> int:
        return consistency.validate(self.root, self.summary, self.report)

    def test_matching_report_summary_and_bytes_pass(self) -> None:
        self.assertEqual(2, self.validate())

    def test_stale_report_is_rejected(self) -> None:
        text = self.report.read_text(encoding="utf-8")
        original = str(self.identities["exhaustive_candidate_groups"]["sha256"])
        replacement = ("0" if original[0] != "0" else "1") + original[1:]
        self.report.write_text(text.replace(original, replacement, 1), encoding="utf-8")
        with self.assertRaises(consistency.ConsistencyError):
            self.validate()

    def test_stale_summary_is_rejected(self) -> None:
        self.identities["exhaustive_candidate_groups"]["size"] = 1
        self.write_summary()
        with self.assertRaises(consistency.ConsistencyError):
            self.validate()

    def test_changed_ignored_bytes_are_rejected(self) -> None:
        relative_path = consistency.ARTIFACTS["exhaustive_function_features"]
        with (self.root / relative_path).open("ab") as stream:
            stream.write(b"changed")
        with self.assertRaises(consistency.ConsistencyError):
            self.validate()


if __name__ == "__main__":
    unittest.main()
