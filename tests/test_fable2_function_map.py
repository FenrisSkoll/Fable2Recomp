from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "Fable2FunctionMap.py"
SPEC = importlib.util.spec_from_file_location("fable2_function_map", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
fm = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fm)


BASE = "A" * 64
UPDATE = "B" * 64
PATCHED = "C" * 64
FINGERPRINT = "D" * 64
TEXT_HASH = "E" * 64


def range_value(start: int, end: int) -> dict[str, str]:
    return fm.range_record(start, end)


def function(
    entry: int,
    ranges: list[tuple[int, int]] | None = None,
    *,
    name: str | None = None,
    source_type: str = "analysis",
    pdata: bool = True,
    inbound: bool = True,
    thunk: bool = False,
    labels: list[dict] | None = None,
    overlapping: list[int] | None = None,
) -> dict:
    ranges = ranges or [(entry, entry + 0x10)]
    body_ranges = [range_value(start, end) for start, end in ranges]
    extent = range_value(ranges[0][0], ranges[-1][1])
    return {
        "entry": fm.address_text(entry),
        "body_ranges": body_ranges,
        "body_size": fm.address_text(sum(end - start for start, end in ranges)),
        "extent": extent,
        "contiguous_body": len(ranges) <= 1,
        "primary_name": {
            "name": name or f"Function_{entry:08X}",
            "source_type": source_type,
        },
        "aliases": [
            {
                "name": name or f"Function_{entry:08X}",
                "source_type": source_type,
                "symbol_type": "function",
                "primary": True,
                "external": False,
            }
        ],
        "external": False,
        "imported": False,
        "entrypoint": False,
        "no_return": False,
        "calling_convention": "unknown",
        "signature_source_type": "default",
        "thunk": (
            {
                "is_thunk": True,
                "direct_target": "0x00002000",
                "terminal_target": "0x00002000",
                "target_name": "Function_00002000",
            }
            if thunk
            else None
        ),
        "pdata_records": [fm.address_text(0x8000 + entry)] if pdata else [],
        "inbound_references": (
            [
                {
                    "from": fm.address_text(entry - 4),
                    "to": fm.address_text(entry),
                    "category": "code",
                    "type": "UNCONDITIONAL_CALL",
                    "source_type": "analysis",
                    "operand_index": 0,
                    "primary": True,
                }
            ]
            if inbound
            else []
        ),
        "callable_internal_labels": labels or [],
        "other_function_entries_in_body": [],
        "overlapping_function_entries": [
            fm.address_text(value) for value in (overlapping or [])
        ],
    }


def contract() -> dict:
    return {
        "schema_version": 2,
        "expected_image_identity": {
            "base_xex_sha256": BASE,
            "title_update_sha256": UPDATE,
            "patched_image_sha256": PATCHED,
            "executable_memory_fingerprint_algorithm": fm.__dict__.get(
                "FINGERPRINT_ALGORITHM", "fable2-executable-memory-sha256-v1"
            ),
            "executable_memory_sha256": FINGERPRINT,
            "image_base": "0x00001000",
            "executable_sections": [
                {
                    "name": ".text",
                    "start": "0x00001000",
                    "end": "0x00002000",
                    "size": "0x00001000",
                    "permissions": "r-x",
                    "sha256": TEXT_HASH,
                }
            ],
        },
        "manual_evidence": [
            {
                "address": "0x00001700",
                "size": "0x10",
                "evidence": ["manual_verified", "fault_walker_verified"],
                "provenance": "synthetic test",
            }
        ],
        "acceptance_fixtures": [
            {
                "address": "0x00001000",
                "size": "0x10",
                "verified_classification": "synthetic exact function",
            }
        ],
    }


def map_document(functions: list[dict] | None = None) -> dict:
    values = sorted(functions or [function(0x1000)], key=lambda item: item["entry"])
    return {
        "schema": {"name": fm.MAP_SCHEMA_NAME, "version": 1},
        "exporter": {"name": "fixture", "version": "1.0.0", "commit": "test"},
        "source_artifact": {
            "id": "synthetic-exact",
            "kind": "synthetic",
            "url": None,
            "commit_or_release": None,
            "claimed_edition": "Fable II GOTY",
            "claimed_region": None,
            "claimed_title_update": "TU1",
            "project_path": "/synthetic",
            "program_name": "synthetic",
            "original_input_sha256": BASE,
            "title_update_sha256": UPDATE,
            "patched_image_sha256": PATCHED,
        },
        "toolchain": {
            "ghidra_version": "test",
            "xexloader_version": "test",
            "loader_name": "test",
            "language_id": "PowerPC:BE:64:A2ALT-32addr",
            "processor": "PowerPC",
            "compiler_spec": "default",
        },
        "program": {
            "image_base": "0x00001000",
            "image_base_source": "fixture",
            "executable_format": "fixture",
            "executable_sha256": BASE,
            "memory_block_count": 1,
            "function_count": len(values),
        },
        "identity_evidence": {
            "base_xex_sha256": BASE,
            "title_update_sha256": UPDATE,
            "patched_image_sha256": PATCHED,
            "executable_memory_fingerprint_algorithm": "fable2-executable-memory-sha256-v1",
            "executable_memory_fingerprint": FINGERPRINT,
            "executable_memory_fingerprint_status": "complete",
            "image_base": "0x00001000",
            "image_base_source": "fixture",
            "memory_blocks": [
                {
                    "name": ".text",
                    "range": range_value(0x1000, 0x2000),
                    "permissions": {"read": True, "write": False, "execute": True},
                    "initialized": True,
                    "loaded": True,
                    "overlay": False,
                    "mapped": False,
                    "artificial": False,
                    "volatile": False,
                    "source_name": None,
                    "sha256": TEXT_HASH,
                    "hash_status": "complete",
                }
            ],
        },
        "functions": values,
        "pdata_functions": [
            {
                "entry": item["entry"],
                "record_addresses": item["pdata_records"],
            }
            for item in values
            if item["pdata_records"]
        ],
        "overlaps": [],
    }


def closure_range(entry: int, end: int) -> dict:
    return {
        "range": range_value(entry, end),
        "authority": "discovered",
        "boundary_provenance": ["synthetic"],
        "trusted": True,
        "preliminary": False,
        "manifest": False,
        "exception_function": False,
        "basic_blocks": [range_value(entry, end)],
    }


class IdentityTests(unittest.TestCase):
    def identity(self, mutate) -> str:
        document = map_document()
        mutate(document)
        fm.validate_map(document)
        return fm.assess_identity(document, contract())["state"]

    def test_all_identity_states(self) -> None:
        self.assertEqual(self.identity(lambda _: None), "exact_image_match")

        def matching_memory(document):
            for key in ("base_xex_sha256", "title_update_sha256", "patched_image_sha256"):
                document["identity_evidence"][key] = None

        self.assertEqual(self.identity(matching_memory), "matching_executable_memory")

        def probable(document):
            matching_memory(document)
            document["identity_evidence"]["executable_memory_fingerprint"] = None
            document["identity_evidence"]["executable_memory_fingerprint_status"] = "incomplete"

        self.assertEqual(self.identity(probable), "probable_same_build")

        def related(document):
            document["identity_evidence"]["base_xex_sha256"] = "1" * 64
            document["identity_evidence"]["title_update_sha256"] = "2" * 64
            document["identity_evidence"]["patched_image_sha256"] = "3" * 64
            document["identity_evidence"]["executable_memory_fingerprint"] = "4" * 64
            document["identity_evidence"]["memory_blocks"][0]["sha256"] = "5" * 64

        self.assertEqual(self.identity(related), "related_build_or_title_update")

        def incomplete(document):
            matching_memory(document)
            document["identity_evidence"]["executable_memory_fingerprint"] = None
            document["identity_evidence"]["executable_memory_fingerprint_status"] = "incomplete"
            document["identity_evidence"]["memory_blocks"][0]["sha256"] = "5" * 64
            document["source_artifact"]["id"] = "unknown"
            document["source_artifact"]["claimed_edition"] = None
            document["source_artifact"]["claimed_title_update"] = None

        self.assertEqual(self.identity(incomplete), "identity_incomplete")

        def mismatch(document):
            document["identity_evidence"]["executable_memory_fingerprint"] = "4" * 64

        self.assertEqual(self.identity(mismatch), "confirmed_mismatch")


class ValidationTests(unittest.TestCase):
    def test_contiguous_and_fragmented_bodies(self) -> None:
        document = map_document(
            [
                function(0x1000),
                function(0x1100, [(0x1100, 0x1108), (0x1120, 0x1128)]),
            ]
        )
        self.assertIs(fm.validate_map(document), document)
        imported = fm.imported_evidence(document, fm.assess_identity(document, contract()))
        self.assertEqual(imported["functions"][1]["body_size"], "0x00000010")
        self.assertEqual(imported["functions"][1]["extent"]["size"], "0x00000028")

    def test_malformed_ranges_and_schema_are_rejected(self) -> None:
        document = map_document()
        document["functions"][0]["body_ranges"][0]["size"] = "0x00000020"
        with self.assertRaises(fm.MapValidationError):
            fm.validate_map(document)
        document = map_document()
        document["schema"]["version"] = 2
        with self.assertRaises(fm.MapValidationError):
            fm.validate_map(document)

    def test_thunks_aliases_multiple_entries_labels_and_overlap_validate(self) -> None:
        label = {
            "address": "0x00001008",
            "name": "callback_entry",
            "source_type": "user_defined",
            "inbound_code_references": [],
        }
        document = map_document(
            [function(0x1000, thunk=True, labels=[label], overlapping=[0x1008])]
        )
        document["functions"][0]["other_function_entries_in_body"] = ["0x00001008"]
        document["overlaps"] = [
            {
                "entries": ["0x00001000", "0x00001008"],
                "body_ranges": [range_value(0x1008, 0x1010)],
            }
        ]
        fm.validate_map(document)


class DiffTests(unittest.TestCase):
    def build(self, identity_mutator=None):
        label = {
            "address": "0x00001408",
            "name": "internal_callback",
            "source_type": "user_defined",
            "inbound_code_references": [
                {
                    "from": "0x00002000",
                    "to": "0x00001408",
                    "category": "code",
                    "type": "UNCONDITIONAL_CALL",
                    "source_type": "user_defined",
                    "operand_index": 0,
                    "primary": True,
                }
            ],
        }
        functions = [
            function(0x1000),
            function(0x1100, name="NamedByGhidra", source_type="user_defined"),
            function(0x1200, [(0x1200, 0x1220)]),
            function(0x1300, thunk=True),
            function(0x1400, labels=[label]),
            function(0x1500, overlapping=[0x1508]),
            function(0x1600, pdata=False, inbound=False),
            function(0x1800, [(0x1800, 0x1808), (0x1820, 0x1828)]),
        ]
        document = map_document(functions)
        document["pdata_functions"].append(
            {"entry": "0x00001A00", "record_addresses": ["0x00009A00"]}
        )
        if identity_mutator:
            identity_mutator(document)
        fm.validate_map(document)
        identity = fm.assess_identity(document, contract())
        manifest = {
            0x1000: {"entry": "0x00001000", "range": range_value(0x1000, 0x1010), "name": None},
            0x1100: {"entry": "0x00001100", "range": range_value(0x1100, 0x1110), "name": "OtherName"},
            0x1200: {"entry": "0x00001200", "range": range_value(0x1200, 0x1210), "name": None},
            0x1700: {"entry": "0x00001700", "range": range_value(0x1700, 0x1710), "name": None},
            0x1900: {"entry": "0x00001900", "range": range_value(0x1900, 0x1910), "name": None},
        }
        rex = {
            0x1000: closure_range(0x1000, 0x1010),
            0x1100: closure_range(0x1100, 0x1110),
            0x1200: closure_range(0x1200, 0x1210),
            0x1300: closure_range(0x1300, 0x1310),
            0x1400: closure_range(0x1400, 0x1410),
            0x1500: closure_range(0x1500, 0x1510),
            0x1800: closure_range(0x1800, 0x1828),
        }
        metadata = {"schema_version": 2, "analyzer_version": "1.1.0"}
        return fm.build_diff(
            document, identity, manifest, rex, {}, metadata, contract(), "exact"
        )

    def test_every_diff_class_except_identity_modes(self) -> None:
        report = self.build()
        classes = {
            value
            for item in report["differences"]
            for value in item["classifications"]
        }
        expected = fm.DIFF_CLASSES - {"related_build_candidate", "unresolved_identity"}
        self.assertTrue(expected <= classes, expected - classes)

    def test_related_and_unresolved_identity_classes(self) -> None:
        def related(document):
            document["identity_evidence"]["base_xex_sha256"] = "1" * 64
            document["identity_evidence"]["title_update_sha256"] = "2" * 64
            document["identity_evidence"]["patched_image_sha256"] = "3" * 64
            document["identity_evidence"]["executable_memory_fingerprint"] = "4" * 64
            document["identity_evidence"]["memory_blocks"][0]["sha256"] = "5" * 64

        report = self.build(related)
        self.assertIn("related_build_candidate", report["differences"][0]["classifications"])

        def incomplete(document):
            for key in ("base_xex_sha256", "title_update_sha256", "patched_image_sha256"):
                document["identity_evidence"][key] = None
            document["identity_evidence"]["executable_memory_fingerprint"] = None
            document["identity_evidence"]["executable_memory_fingerprint_status"] = "incomplete"
            document["identity_evidence"]["memory_blocks"][0]["sha256"] = "5" * 64
            document["source_artifact"]["id"] = "unknown"
            document["source_artifact"]["claimed_edition"] = None
            document["source_artifact"]["claimed_title_update"] = None

        report = self.build(incomplete)
        self.assertIn("unresolved_identity", report["differences"][0]["classifications"])

    def test_deterministic_idempotence(self) -> None:
        first = json.dumps(self.build(), indent=2, sort_keys=True)
        second = json.dumps(self.build(), indent=2, sort_keys=True)
        self.assertEqual(first, second)

    def test_diff_command_does_not_mutate_manifest(self) -> None:
        document = map_document()
        closure = {
            "schema_version": 2,
            "analyzer_version": "1.1.0",
            "image_identity": {},
            "function_ranges": [
                {
                    "range": range_value(0x1000, 0x1010),
                    "authority": "discovered",
                    "boundary_provenance": ["synthetic"],
                    "trusted": True,
                    "preliminary": False,
                    "manifest": True,
                    "exception_function": False,
                    "basic_blocks": [range_value(0x1000, 0x1010)],
                }
            ],
            "candidates": [],
            "safety": {"mode": "report_only"},
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            map_path = root / "map.json"
            evidence_path = root / "evidence.json"
            closure_path = root / "closure.json"
            manifest_path = root / "manifest.toml"
            output = root / "reports"
            for path, value in (
                (map_path, document),
                (evidence_path, contract()),
                (closure_path, closure),
            ):
                path.write_text(json.dumps(value), encoding="utf-8")
            manifest_path.write_text(
                '[entrypoint.functions]\n"0x00001000" = { size = 0x10 }\n',
                encoding="utf-8",
            )
            before = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            args = argparse.Namespace(
                map=map_path,
                mode="exact",
                evidence=evidence_path,
                manifest=manifest_path,
                closure=closure_path,
                output_directory=output,
                run_metadata=None,
            )
            self.assertEqual(fm.diff_command(args), 0)
            after = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            self.assertEqual(before, after)
            self.assertTrue((output / "function-map-diff.json").exists())
            self.assertTrue((output / "function-map-diff-review.toml").exists())


if __name__ == "__main__":
    unittest.main()
