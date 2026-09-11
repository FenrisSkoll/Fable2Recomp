from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "tools" / "VerifyFable2PrototypePhase1Consistency.py"
)
SPEC = importlib.util.spec_from_file_location("phase1_consistency", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
verify = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = verify
SPEC.loader.exec_module(verify)


class Phase1ConsistencyTests(unittest.TestCase):
    def fixture(self, root: Path, stale_report: bool = False) -> tuple[Path, Path, Path]:
        evidence = root / "evidence"
        derived = root / "derived"
        evidence.mkdir()
        payloads = {
            "sep-2008": b"SEPTEMBER",
            "jul-2009": b"JULY-BUILD-23",
            "build-23.12.02.0330": b"JULY-BUILD-23",
        }
        records = []
        identities = {}
        for build_id, payload in payloads.items():
            section_dir = derived / build_id / "sections"
            section_dir.mkdir(parents=True)
            section = section_dir / "03-.text-82170000.bin"
            section.write_bytes(payload)
            digest = hashlib.sha256(payload).hexdigest().upper()
            block = {
                "name": ".text",
                "start": "0x82170000",
                "size": len(payload),
                "derived_relative_path": "sections/03-.text-82170000.bin",
                "sha256": digest,
            }
            manifest = {"memory_blocks": [block]}
            (derived / build_id / "derived-image.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            records.append({"artifact_id": build_id, "derived_image": manifest})
            identities[build_id] = block
        (evidence / "prototype-xex-metadata.json").write_text(
            json.dumps({"records": records}), encoding="utf-8"
        )
        (evidence / "prototype-tu1-relationship.json").write_text(
            json.dumps(
                {
                    "july_vs_build_23_sections": [
                        {
                            "section": ".text",
                            "left_sha256": identities["jul-2009"]["sha256"],
                            "right_sha256": identities["build-23.12.02.0330"]["sha256"],
                        }
                    ],
                    "build_23_vs_canonical_tu1_sections": [
                        {
                            "section": ".text",
                            "left_sha256": identities["build-23.12.02.0330"]["sha256"],
                            "right_sha256": "0" * 64,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        sep_hash = identities["sep-2008"]["sha256"]
        if stale_report:
            sep_hash = "F" * 64
        report = root / "report.md"
        report.write_text(
            "\n".join(
                (
                    "| Build | `.text` start | Size | SHA-256 |",
                    "| --- | ---: | ---: | --- |",
                    f"| September | `0x82170000` | 9 | `{sep_hash}` |",
                    "| July / build 23 | `0x82170000` | 13 | "
                    f"`{identities['build-23.12.02.0330']['sha256']}` |",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        return evidence, derived, report

    def test_matching_bytes_evidence_and_report_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            evidence, derived, report = self.fixture(Path(directory))
            result = verify.validate(evidence, derived, report)
        self.assertEqual(3, result["full_xex_builds_checked"])
        self.assertEqual(1, result["july_build_23_initialized_sections_checked"])

    def test_stale_human_report_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            evidence, derived, report = self.fixture(Path(directory), stale_report=True)
            with self.assertRaisesRegex(verify.ConsistencyError, "report September"):
                verify.validate(evidence, derived, report)

    def test_changed_derived_bytes_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            evidence, derived, report = self.fixture(Path(directory))
            section = derived / "sep-2008" / "sections" / "03-.text-82170000.bin"
            section.write_bytes(b"changed")
            with self.assertRaisesRegex(verify.ConsistencyError, "size mismatch"):
                verify.validate(evidence, derived, report)


if __name__ == "__main__":
    unittest.main()
