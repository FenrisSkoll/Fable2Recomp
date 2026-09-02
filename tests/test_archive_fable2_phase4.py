from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
SPEC = importlib.util.spec_from_file_location(
    "archive_fable2_phase4",
    ROOT / "tools" / "Archive-Fable2Phase4.py",
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load Archive-Fable2Phase4.py")
archive_tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(archive_tool)


class DeterministicArchiveTests(unittest.TestCase):
    def test_zip_is_deterministic_and_extracts_to_the_allowlist(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fable2-phase4-archive-test-") as root:
            directory = Path(root)
            source = directory / "source.json"
            source.write_bytes(b'{"synthetic":true}\n')
            members = {
                "README.md": b"synthetic compact evidence\n",
                "evidence/source.json": source,
            }
            first = directory / "first.zip"
            second = directory / "second.zip"
            first_records = archive_tool.create_deterministic_zip(first, members)
            second_records = archive_tool.create_deterministic_zip(second, members)
            archive_tool.verify_zip(first, first_records)
            archive_tool.verify_zip(second, second_records)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(first_records, second_records)

    def test_private_or_escaping_members_are_rejected(self) -> None:
        for member in (
            "../escape.json",
            "/absolute.json",
            "C:/windows-absolute.json",
            r"folder\windows-separator.json",
            ".env",
            "runtime/content/title.bin",
            "binary/xenia_canary.exe",
            "game/default.xex",
            "trace/run.raw.jsonl",
            "metadata/private_key.txt",
        ):
            with self.subTest(member=member):
                with self.assertRaises(archive_tool.ArchiveError):
                    archive_tool.ensure_safe_member(member)

    def test_extracted_hash_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fable2-phase4-archive-test-") as root:
            path = Path(root) / "evidence.zip"
            records = archive_tool.create_deterministic_zip(
                path, {"evidence.json": b"synthetic\n"}
            )
            records[0]["sha256"] = "0" * 64
            with self.assertRaises(archive_tool.ArchiveError):
                archive_tool.verify_zip(path, records)


if __name__ == "__main__":
    unittest.main()
