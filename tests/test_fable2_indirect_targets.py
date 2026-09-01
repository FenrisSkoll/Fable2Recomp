from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "phase4"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
MODULE_PATH = TOOLS / "Fable2IndirectTargets.py"
SPEC = importlib.util.spec_from_file_location("fable2_indirect_targets", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
p4 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p4)


BASE = "A" * 64
UPDATE = "B" * 64
PATCHED = "C" * 64
FINGERPRINT = "D" * 64
TEXT_HASH = "E" * 64


def range_value(start: int, end: int) -> dict[str, str]:
    return {
        "start": f"0x{start:08X}",
        "end": f"0x{end:08X}",
        "size": f"0x{end - start:08X}",
    }


def contract() -> dict:
    return {
        "schema_version": 4,
        "expected_image_identity": {
            "base_xex_sha256": BASE,
            "title_update_sha256": UPDATE,
            "patched_image_sha256": PATCHED,
            "executable_memory_fingerprint_algorithm": (
                "fable2-executable-memory-sha256-v1"
            ),
            "executable_memory_sha256": FINGERPRINT,
            "image_base": "0x82000000",
            "image_size": "0x02000000",
            "title_id": "0x4D5307F1",
            "media_id": "0x716F0A0D",
            "version": "0.0.1.26",
            "executable_sections": [
                {
                    "name": ".text",
                    "start": "0x82170000",
                    "end": "0x832CA03C",
                    "size": "0x0115A03C",
                    "permissions": "r-x",
                    "sha256": TEXT_HASH,
                }
            ],
        },
        "runtime_indirect_evidence": {
            "schema_version": 1,
            "observations": [
                {
                    "target": "0x82174734",
                    "owner_address": "0x821746A8",
                    "classification": "known_jump_table_case",
                    "evidence_level": "CONFIRMED",
                    "source_sites": ["0x823DCAD8", "0x82403720"],
                    "branch_kinds": ["bctr"],
                    "manifest_policy": (
                        "forbidden_unless_independent_callable_evidence"
                    ),
                    "provenance": "synthetic Run 047 address-only regression",
                }
            ],
        },
        "acceptance_fixtures": [
            {
                "address": "0x829647F0",
                "size": "0x10",
                "verified_classification": "virtual-dispatch leaf thunk",
            },
            {
                "address": "0x82C03B28",
                "size": "0x1C",
                "verified_classification": "callback leaf",
            },
            {
                "address": "0x829675E0",
                "size": "0x10",
                "verified_classification": "virtual-dispatch leaf thunk",
            },
        ],
    }


def closure_range(
    start: int,
    end: int,
    *,
    authority: str = "cfg",
    exception_entries: list[int] | None = None,
) -> dict:
    return {
        "range": range_value(start, end),
        "authority": authority,
        "boundary_provenance": ["synthetic_exact_tu1"],
        "trusted": True,
        "preliminary": False,
        "manifest": False,
        "exception_function": bool(exception_entries),
        "basic_blocks": [range_value(start, end)],
        "exception_entries": [
            f"0x{value:08X}" for value in (exception_entries or [])
        ],
        "labels": [],
    }


def closure_document() -> dict:
    return {
        "schema_version": 3,
        "analyzer_version": "synthetic-phase4",
        "image_identity": {"patched_image_sha256": PATCHED},
        "function_ranges": [
            closure_range(0x82190000, 0x82190018),
            closure_range(0x82191000, 0x82191020),
            closure_range(
                0x82192000,
                0x82192030,
                authority="pdata",
                exception_entries=[0x82192010],
            ),
            closure_range(0x82194000, 0x82194020),
            closure_range(0x82195000, 0x82195020, authority="pdata"),
        ],
        "candidates": [
            {
                "address": "0x82196000",
                "classification": "probable",
                "confidence": "probable",
                "proposed_range": range_value(0x82196000, 0x82196010),
                "boundary_provenance": ["synthetic_cfg"],
                "conflicts": [],
                "rejection_reasons": [],
            }
        ],
        "jump_table_recovery": {
            "schema_version": 1,
            "boundary_effects": [],
            "indirect_sites": [
                {
                    "site": "0x823DCAD8",
                    "owner_address": "0x821746A8",
                    "selected_table": {
                        "targets": ["0x82174734"],
                        "kind": "absolute",
                        "table_address": "0x83000000",
                        "origin": "synthetic",
                        "confidence": "strong",
                    },
                }
            ],
        },
    }


def map_function(
    entry: int,
    end: int,
    *,
    pdata: bool = True,
    internal_label: int | None = None,
) -> dict:
    name = f"Function_{entry:08X}"
    labels = []
    if internal_label is not None:
        labels.append(
            {
                "address": f"0x{internal_label:08X}",
                "name": f"LAB_{internal_label:08X}",
                "source_type": "analysis",
                "inbound_code_references": [f"0x{internal_label - 4:08X}"],
            }
        )
    pdata_records = [f"0x{entry - 0x100000:08X}"] if pdata else []
    return {
        "entry": f"0x{entry:08X}",
        "body_ranges": [range_value(entry, end)],
        "body_size": f"0x{end - entry:08X}",
        "extent": range_value(entry, end),
        "contiguous_body": True,
        "primary_name": {"name": name, "source_type": "analysis"},
        "aliases": [
            {
                "name": name,
                "source_type": "analysis",
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
        "thunk": None,
        "pdata_records": pdata_records,
        "inbound_references": [
            {
                "from": f"0x{entry - 4:08X}",
                "to": f"0x{entry:08X}",
                "category": "code",
                "type": "UNCONDITIONAL_CALL",
                "source_type": "analysis",
                "operand_index": 0,
                "primary": True,
            }
        ],
        "callable_internal_labels": labels,
        "other_function_entries_in_body": [],
        "overlapping_function_entries": [],
    }


def map_document(*, related: bool = False) -> dict:
    functions = (
        [map_function(0x82197000, 0x82197010)]
        if related
        else [
            map_function(0x82194000, 0x82194030),
            map_function(0x82195000, 0x82195020),
            map_function(0x82199000, 0x82199020, internal_label=0x82199004),
        ]
    )
    mismatch = "1" * 64
    base_hash = mismatch if related else BASE
    update_hash = "2" * 64 if related else UPDATE
    patched_hash = "3" * 64 if related else PATCHED
    fingerprint = "4" * 64 if related else FINGERPRINT
    section_hash = "5" * 64 if related else TEXT_HASH
    artifact_id = "synthetic-related" if related else "synthetic-exact"
    return {
        "schema": {"name": "fable2-ghidra-function-map", "version": 1},
        "exporter": {"name": "fixture", "version": "1.0.0", "commit": "test"},
        "source_artifact": {
            "id": artifact_id,
            "kind": "synthetic",
            "url": None,
            "commit_or_release": None,
            "claimed_edition": "Fable II GOTY",
            "claimed_region": None,
            "claimed_title_update": "TU1" if not related else "base",
            "project_path": "/synthetic",
            "program_name": artifact_id,
            "original_input_sha256": base_hash,
            "title_update_sha256": update_hash,
            "patched_image_sha256": patched_hash,
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
            "image_base": "0x82000000",
            "image_base_source": "fixture",
            "executable_format": "fixture",
            "executable_sha256": base_hash,
            "memory_block_count": 1,
            "function_count": len(functions),
        },
        "identity_evidence": {
            "base_xex_sha256": base_hash,
            "title_update_sha256": update_hash,
            "patched_image_sha256": patched_hash,
            "executable_memory_fingerprint_algorithm": (
                "fable2-executable-memory-sha256-v1"
            ),
            "executable_memory_fingerprint": fingerprint,
            "executable_memory_fingerprint_status": "complete",
            "image_base": "0x82000000",
            "image_base_source": "fixture",
            "memory_blocks": [
                {
                    "name": ".text",
                    "range": range_value(0x82170000, 0x832CA03C),
                    "permissions": {"read": True, "write": False, "execute": True},
                    "initialized": True,
                    "loaded": True,
                    "overlay": False,
                    "mapped": False,
                    "artificial": False,
                    "volatile": False,
                    "source_name": None,
                    "sha256": section_hash,
                    "hash_status": "complete",
                }
            ],
        },
        "functions": functions,
        "pdata_functions": [
            {"entry": item["entry"], "record_addresses": item["pdata_records"]}
            for item in functions
            if item["pdata_records"]
        ],
        "overlaps": [],
    }


def manifest_text(newline: str = "\n") -> str:
    lines = [
        "# synthetic manifest comment",
        "[project]",
        'name = "synthetic"',
        "",
        "[entrypoint]",
        'file_path = "synthetic.xex"',
        "",
        "[entrypoint.functions]",
        "# preserve this function-table comment",
        '"0x829647F0" = { size = 0x10 } # virtual fixture',
        '"0x82C03B28" = { size = 0x1C } # callback fixture',
        '"0x829675E0" = { size = 0x10 } # bclr fixture',
        "",
        "[analysis]",
        'marker = "preserve me"',
        "",
    ]
    return newline.join(lines)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class RawTraceTests(unittest.TestCase):
    def test_canonical_acceptance_fixture_matches_phase4_identity(self) -> None:
        expected = p4.load_expected_identity(p4.DEFAULT_EVIDENCE)
        summary = p4.aggregate_raw_runs(
            [p4.parse_raw_trace(FIXTURES / "canonical-acceptance.raw.jsonl")],
            expected["patched_image_sha256"],
            expected,
        )
        self.assertEqual(1, summary["counts"]["accepted_runs"])
        self.assertEqual(5, summary["counts"]["unique_pairs"])
        assessment = summary["runs"][0]["identity_assessment"]
        self.assertTrue(assessment["module_fingerprint_match"])
        self.assertEqual([], summary["quarantine"])

    def test_streaming_aggregation_covers_branch_shapes_and_threads(self) -> None:
        runs = [
            p4.parse_raw_trace(FIXTURES / "synthetic-run-a.raw.jsonl"),
            p4.parse_raw_trace(FIXTURES / "synthetic-run-b.raw.jsonl"),
        ]
        summary = p4.aggregate_raw_runs(runs, PATCHED)
        self.assertEqual(summary["counts"]["accepted_runs"], 2)
        self.assertEqual(summary["counts"]["quarantined_runs"], 0)
        self.assertEqual(summary["counts"]["unique_pairs"], 17)
        self.assertEqual(summary["counts"]["total_hits"], 146)
        self.assertEqual(summary["counts"]["dropped_hits"], 2)
        self.assertEqual(summary["counts"]["io_errors"], 1)
        self.assertEqual(
            {pair["branch_kind"] for pair in summary["pairs"]},
            {"bctr", "bctrl", "bclr", "blr"},
        )
        pair = next(
            item
            for item in summary["pairs"]
            if item["source"] == "0x82180000"
            and item["target"] == "0x829647F0"
        )
        self.assertEqual(pair["hit_count"], 6)
        self.assertEqual(len(pair["thread_observations"]), 3)
        self.assertEqual(
            {(item["run_id"], item["thread_key"]) for item in pair["thread_observations"]},
            {
                ("synthetic-run-a", "guest:00000001"),
                ("synthetic-run-a", "guest:00000002"),
                ("synthetic-run-b", "guest:00000001"),
            },
        )

    def test_truncated_tail_is_usable_but_corrupt_middle_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_lines = (FIXTURES / "synthetic-run-a.raw.jsonl").read_bytes().splitlines()
            truncated = root / "truncated.raw.jsonl"
            truncated.write_bytes(b"\n".join(source_lines[:4]) + b"\n{\"record\":\"pair\"")
            parsed = p4.parse_raw_trace(truncated)
            self.assertTrue(parsed["corrupt_tail"])
            self.assertEqual(parsed["flush_status"], "abnormal_truncated_tail")
            self.assertGreater(len(parsed["pairs"]), 0)

            corrupt = root / "corrupt.raw.jsonl"
            corrupt.write_bytes(
                source_lines[0] + b"\n{not json}\n" + source_lines[-1] + b"\n"
            )
            with self.assertRaisesRegex(p4.Phase4Error, "corrupt JSON"):
                p4.parse_raw_trace(corrupt)

    def test_schema_image_and_duplicate_guards(self) -> None:
        first = p4.parse_raw_trace(FIXTURES / "synthetic-run-a.raw.jsonl")
        with self.assertRaisesRegex(p4.Phase4Error, "duplicate raw trace"):
            p4.aggregate_raw_runs([first, first], PATCHED)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            records = [
                json.loads(line)
                for line in (FIXTURES / "synthetic-run-a.raw.jsonl").read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
            records[0]["label"] = "different content, same run ID"
            duplicate_id = root / "duplicate-id.raw.jsonl"
            duplicate_id.write_text(
                "".join(json.dumps(item, separators=(",", ":")) + "\n" for item in records),
                encoding="utf-8",
            )
            second = p4.parse_raw_trace(duplicate_id)
            with self.assertRaisesRegex(p4.Phase4Error, "duplicate run ID"):
                p4.aggregate_raw_runs([first, second], PATCHED)

            records[0]["run_id"] = "mismatch-run"
            records[0]["identity"]["expected_image_sha256"] = "9" * 64
            for record in records[1:]:
                if "run_id" in record:
                    record["run_id"] = "mismatch-run"
            mismatch = root / "mismatch.raw.jsonl"
            mismatch.write_text(
                "".join(json.dumps(item, separators=(",", ":")) + "\n" for item in records),
                encoding="utf-8",
            )
            quarantined = p4.aggregate_raw_runs([p4.parse_raw_trace(mismatch)], PATCHED)
            self.assertEqual(quarantined["counts"]["accepted_runs"], 0)
            self.assertEqual(quarantined["counts"]["quarantined_runs"], 1)
            self.assertEqual(quarantined["pairs"], [])

            records[0]["schema_version"] = 99
            bad_schema = root / "bad-schema.raw.jsonl"
            bad_schema.write_text(
                "".join(json.dumps(item) + "\n" for item in records), encoding="utf-8"
            )
            with self.assertRaisesRegex(p4.Phase4Error, "schema version"):
                p4.parse_raw_trace(bad_schema)

    def test_title_metadata_and_module_range_mismatches_are_quarantined(self) -> None:
        parsed = p4.parse_raw_trace(FIXTURES / "synthetic-run-a.raw.jsonl")
        expected = contract()["expected_image_identity"]
        accepted = p4.aggregate_raw_runs([parsed], PATCHED, expected)
        self.assertEqual(accepted["counts"]["accepted_runs"], 1)
        self.assertEqual(
            accepted["runs"][0]["identity_assessment"]["strength"],
            "configured_sha256_metadata_and_module_ranges",
        )

        wrong_range = copy.deepcopy(parsed)
        title_module = next(
            module for module in wrong_range["modules"] if module["title_module"]
        )
        title_module["executable_end"] = "0x82180000"
        wrong_range["header"]["run_id"] = "wrong-module-range"
        quarantined = p4.aggregate_raw_runs([wrong_range], PATCHED, expected)
        self.assertEqual(quarantined["counts"]["accepted_runs"], 0)
        self.assertIn(
            "title_module_does_not_contain_executable_sections",
            quarantined["quarantine"][0]["reasons"],
        )

        fingerprinted = copy.deepcopy(parsed)
        title_module = next(
            module for module in fingerprinted["modules"] if module["title_module"]
        )
        title_module["fingerprint"] = {
            "algorithm": "sha1_contiguous_loaded_executable_memory",
            "value": "A" * 40,
        }
        expected_with_fingerprint = copy.deepcopy(expected)
        expected_with_fingerprint.update(
            {
                "xenia_module_fingerprint_algorithm": (
                    "sha1_contiguous_loaded_executable_memory"
                ),
                "xenia_module_fingerprint": "A" * 40,
            }
        )
        accepted = p4.aggregate_raw_runs(
            [fingerprinted], PATCHED, expected_with_fingerprint
        )
        assessment = accepted["runs"][0]["identity_assessment"]
        self.assertTrue(assessment["module_fingerprint_match"])
        self.assertEqual(
            assessment["strength"],
            "configured_sha256_metadata_ranges_and_pinned_observed_module_fingerprint",
        )

        expected_with_fingerprint["xenia_module_fingerprint"] = "B" * 40
        mismatched = p4.aggregate_raw_runs(
            [fingerprinted], PATCHED, expected_with_fingerprint
        )
        self.assertEqual(0, mismatched["counts"]["accepted_runs"])
        self.assertIn(
            "xenia_module_fingerprint_mismatch",
            mismatched["quarantine"][0]["reasons"],
        )

        refreshed = copy.deepcopy(parsed)
        original_title_module = next(
            module for module in refreshed["modules"] if module["title_module"]
        )
        original_title_module["fingerprint"] = {
            "algorithm": "sha1_contiguous_loaded_executable_memory",
            "value": "F" * 40,
        }
        post_patch_module = copy.deepcopy(original_title_module)
        post_patch_module["fingerprint"]["value"] = "A" * 40
        refreshed["modules"].append(post_patch_module)
        expected_with_fingerprint["xenia_module_fingerprint"] = "A" * 40
        accepted_refresh = p4.aggregate_raw_runs(
            [refreshed], PATCHED, expected_with_fingerprint
        )
        self.assertEqual(1, accepted_refresh["counts"]["accepted_runs"])
        self.assertEqual(
            "A" * 40,
            accepted_refresh["runs"][0]["identity_assessment"][
                "selected_title_module"
            ]["fingerprint"]["value"],
        )

    def test_unresolved_prepatch_module_snapshot_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            raw = Path(temporary) / "prepatch-module.raw.jsonl"
            lines = (FIXTURES / "synthetic-run-a.raw.jsonl").read_text(
                encoding="utf-8"
            ).splitlines()
            unresolved = {
                "record": "module",
                "run_id": "synthetic-run-a",
                "name": "default.xex",
                "image_base": "0x82000000",
                "executable_start": "0x00000000",
                "executable_end": "0x00000000",
                "executable": True,
                "title_module": False,
                "fingerprint": {
                    "algorithm": "sha1_contiguous_loaded_executable_memory",
                    "value": "",
                },
            }
            lines.insert(1, json.dumps(unresolved, separators=(",", ":")))
            raw.write_text("\n".join(lines) + "\n", encoding="utf-8")

            parsed = p4.parse_raw_trace(raw)
            self.assertTrue(
                any(
                    module["name"] == "default.xex"
                    and module["executable_start"] == "0x00000000"
                    and not module["title_module"]
                    for module in parsed["modules"]
                )
            )
            summary = p4.aggregate_raw_runs(
                [parsed], PATCHED, contract()["expected_image_identity"]
            )
            self.assertEqual(1, summary["counts"]["accepted_runs"])

            invalid = copy.deepcopy(unresolved)
            invalid["title_module"] = True
            invalid_lines = list(lines)
            invalid_lines[1] = json.dumps(invalid, separators=(",", ":"))
            raw.write_text("\n".join(invalid_lines) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(
                p4.Phase4Error, "title module executable range must be non-empty"
            ):
                p4.parse_raw_trace(raw)

    def test_count_overflow_saturates_and_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            header = json.loads(
                (FIXTURES / "synthetic-run-a.raw.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()[0]
            )
            header["run_id"] = "overflow-run"
            pair = {
                "record": "pair",
                "run_id": "overflow-run",
                "batch_id": 1,
                "thread_key": "guest:00000001",
                "source": "0x82180000",
                "target": "0x82195000",
                "branch_kind": "bctrl",
                "link": True,
                "ordinary_return": False,
                "source_module": "default.xex",
                "target_module": "default.xex",
                "hit_count": p4.UINT64_MAX,
                "first_thread_sequence": 1,
                "last_thread_sequence": p4.UINT64_MAX,
                "target_validity": "known_executable_module",
            }
            footer = {
                "record": "footer",
                "run_id": "overflow-run",
                "shutdown_status": "normal",
                "total_hits": p4.UINT64_MAX,
                "total_pair_records": 2,
                "dropped_hits": 0,
                "io_errors": 0,
                "count_overflows": 1,
            }
            raw = root / "overflow.raw.jsonl"
            raw.write_text(
                "".join(
                    json.dumps(value, separators=(",", ":")) + "\n"
                    for value in (header, pair, pair, footer)
                ),
                encoding="utf-8",
            )
            summary = p4.aggregate_raw_runs([p4.parse_raw_trace(raw)], PATCHED)
            self.assertEqual(summary["pairs"][0]["hit_count"], p4.UINT64_MAX)
            self.assertGreaterEqual(summary["counts"]["count_overflows"], 2)

    def test_repeated_summary_merge_is_deterministic_and_duplicate_safe(self) -> None:
        first = p4.aggregate_raw_runs(
            [p4.parse_raw_trace(FIXTURES / "synthetic-run-a.raw.jsonl")], PATCHED
        )
        second = p4.aggregate_raw_runs(
            [p4.parse_raw_trace(FIXTURES / "synthetic-run-b.raw.jsonl")], PATCHED
        )
        merged_ab = p4.merge_summaries([first, second])
        merged_ba = p4.merge_summaries([second, first])
        self.assertEqual(p4.canonical_json_bytes(merged_ab), p4.canonical_json_bytes(merged_ba))
        with self.assertRaisesRegex(p4.Phase4Error, "duplicate run ID"):
            p4.merge_summaries([first, first])
        changed = copy.deepcopy(second)
        changed["identity"]["expected_image_sha256"] = "F" * 64
        with self.assertRaisesRegex(p4.Phase4Error, "identities disagree"):
            p4.merge_summaries([first, changed])


class PlannerFixture:
    def __init__(self, root: Path):
        self.root = root
        self.evidence = root / "evidence.json"
        self.closure = root / "closure.json"
        self.manifest = root / "manifest.toml"
        self.generated = root / "generated_init.cpp"
        self.exact_map = root / "exact-map.json"
        self.related_map = root / "related-map.json"
        self.summary_path = root / "summary.json"
        write_json(self.evidence, contract())
        write_json(self.closure, closure_document())
        self.manifest.write_text(manifest_text(), encoding="utf-8", newline="")
        self.generated.write_text(
            "static const Entry entries[] = {\n"
            "  { 0x80002000, __imp__SyntheticKernelImport },\n"
            "  { 0x82198000, sub_82198000 },\n"
            "};\n",
            encoding="utf-8",
        )
        write_json(self.exact_map, map_document())
        write_json(self.related_map, map_document(related=True))
        summary = p4.aggregate_raw_runs(
            [
                p4.parse_raw_trace(FIXTURES / "synthetic-run-a.raw.jsonl"),
                p4.parse_raw_trace(FIXTURES / "synthetic-run-b.raw.jsonl"),
            ],
            PATCHED,
        )
        p4.atomic_write_json(self.summary_path, summary)
        self.summary = summary

    def plan(self, manifest: Path | None = None) -> dict:
        return p4.build_plan(
            self.summary,
            self.summary_path,
            manifest or self.manifest,
            self.closure,
            self.evidence,
            self.generated,
            [self.exact_map, self.related_map],
        )


class ImportPlannerTests(unittest.TestCase):
    def test_all_classifications_evidence_and_mandatory_fixtures(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlannerFixture(Path(temporary))
            before = fixture.manifest.read_bytes()
            plan = fixture.plan()
            self.assertEqual(fixture.manifest.read_bytes(), before)
            by_target = {item["target"]: item for item in plan["targets"]}

            for target in ("0x829647F0", "0x82C03B28", "0x829675E0"):
                self.assertEqual(
                    by_target[target]["classification"], "existing_manifest_function"
                )
                self.assertIsNone(by_target[target]["proposal"])

            case = by_target["0x82174734"]
            self.assertEqual(case["classification"], "known_jump_table_case")
            self.assertEqual(case["ownership"]["owner_address"], "0x821746A8")
            self.assertEqual(
                case["runtime"]["source_sites"], ["0x823DCAD8", "0x82403720"]
            )
            self.assertIsNone(case["proposal"])

            expected = {
                "0x80001000": "known_import_or_kernel_target",
                "0x82191004": "existing_function_internal_entry",
                "0x82192010": "known_exception_landing_pad",
                "0x82193002": "invalid_or_non_executable_target",
                "0x82194000": "conflicting_range",
                "0x82195000": "strong_new_function",
                "0x82196000": "probable_new_function",
                "0x82197000": "ambiguous_target",
                "0x82198000": "existing_manifest_function",
                "0x82199004": "existing_function_internal_entry",
            }
            for target, classification in expected.items():
                self.assertEqual(by_target[target]["classification"], classification, target)

            generated = p4.load_generated_registrations(fixture.generated)
            self.assertEqual(generated[0x80002000], "__imp__SyntheticKernelImport")
            imported = p4.classify_target(
                0x80002000,
                [
                    {
                        "source": "0x82180000",
                        "target": "0x80002000",
                        "branch_kind": "bctrl",
                        "link": True,
                        "ordinary_return": False,
                        "source_module": "default.xex",
                        "target_module": "default.xex",
                        "hit_count": 1,
                        "observed_runs": ["synthetic-run-a"],
                    }
                ],
                {},
                generated,
                p4.load_closure_indices(fixture.closure),
                {},
                {},
                {},
                {},
                [(0x80000000, 0x832CA03C, "synthetic")],
                {"default.xex"},
            )
            self.assertEqual(
                imported["classification"], "known_import_or_kernel_target"
            )
            self.assertEqual(
                imported["evidence"][1]["symbol"],
                "__imp__SyntheticKernelImport",
            )

            computed_tail = by_target["0x82190000"]
            self.assertEqual(computed_tail["classification"], "strong_new_function")
            self.assertFalse(computed_tail["automatic_application_permitted"])
            self.assertIn(
                "bctr_only_observation_requires_stronger_switch_vs_tail_review",
                computed_tail["rejection_reasons"],
            )

            related = by_target["0x82197000"]
            self.assertTrue(
                any(
                    item["kind"] == "related_build_ghidra_quarantined"
                    for item in related["evidence"]
                )
            )
            self.assertEqual(plan["counts"]["ignored_ordinary_returns"], 1)
            self.assertTrue(all(item["passed"] for item in plan["fixture_results"]))
            self.assertFalse(plan["safety"]["canonical_manifest_modified"])
            self.assertFalse(plan["safety"]["placeholder_implementations_supported"])
            self.assertFalse(plan["safety"]["runtime_observation_establishes_size"])

    def test_plan_bytes_are_deterministic_and_integrity_guarded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlannerFixture(Path(temporary))
            first = fixture.plan()
            second = fixture.plan()
            self.assertEqual(p4.canonical_json_bytes(first), p4.canonical_json_bytes(second))
            self.assertIs(p4.validate_plan(first), first)
            tampered = copy.deepcopy(first)
            tampered["proposals"][0]["proposal"]["size_value"] += 4
            with self.assertRaisesRegex(p4.Phase4Error, "integrity check failed"):
                p4.validate_plan(tampered)

    def test_explicit_apply_is_atomic_guarded_idempotent_and_format_preserving(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlannerFixture(Path(temporary))
            crlf_manifest = fixture.root / "manifest-crlf.toml"
            crlf_manifest.write_bytes(manifest_text("\r\n").encode("utf-8"))
            plan = fixture.plan(crlf_manifest)
            strong = next(
                item for item in plan["proposals"] if item["target"] == "0x82195000"
            )
            self.assertTrue(strong["automatic_application_permitted"])
            original = crlf_manifest.read_bytes()
            result = p4.apply_reviewed_plan(
                plan, crlf_manifest, {strong["candidate_id"]}
            )
            self.assertEqual(result["status"], "applied")
            updated = crlf_manifest.read_bytes()
            self.assertNotEqual(updated, original)
            self.assertNotIn(b"\r\r\n", updated)
            self.assertIn(b"# preserve this function-table comment\r\n", updated)
            self.assertIn(b'marker = "preserve me"\r\n', updated)
            self.assertIn(
                (
                    f'"0x82195000" = {{ size = 0x20 }} '
                    f'# Phase 4 reviewed {strong["candidate_id"]}'
                ).encode("utf-8"),
                updated,
            )
            backup = crlf_manifest.with_name(crlf_manifest.name + ".phase4.bak")
            self.assertEqual(backup.read_bytes(), original)
            second = p4.apply_reviewed_plan(
                plan, crlf_manifest, {strong["candidate_id"]}
            )
            self.assertEqual(second["status"], "already_applied")
            self.assertFalse(second["manifest_modified"])
            self.assertEqual(crlf_manifest.read_bytes(), updated)

    def test_stale_and_unreviewable_candidates_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlannerFixture(Path(temporary))
            plan = fixture.plan()
            strong = next(
                item for item in plan["proposals"] if item["target"] == "0x82195000"
            )
            computed = next(
                item for item in plan["proposals"] if item["target"] == "0x82190000"
            )
            with self.assertRaisesRegex(p4.Phase4Error, "not permitted"):
                p4.apply_reviewed_plan(
                    plan, fixture.manifest, {computed["candidate_id"]}
                )
            fixture.manifest.write_text(
                manifest_text().replace("synthetic manifest", "changed manifest"),
                encoding="utf-8",
                newline="",
            )
            with self.assertRaisesRegex(p4.Phase4Error, "stale plan"):
                p4.apply_reviewed_plan(
                    plan, fixture.manifest, {strong["candidate_id"]}
                )
            with self.assertRaisesRegex(p4.Phase4Error, "unknown candidate"):
                p4.apply_reviewed_plan(plan, fixture.manifest, {"P4-NOT-REVIEWED"})

    def test_no_stub_generation_path_exists(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("RETURN_R3_ZERO", source)
        self.assertNotIn("placeholder implementation", source.lower())
        rendered = p4.render_manifest_additions(
            [
                {
                    "target": "0x82195000",
                    "candidate_id": "P4-SYNTHETIC",
                    "proposal": {"size_value": 0x20},
                }
            ],
            "\n",
        )
        self.assertEqual(
            rendered,
            '"0x82195000" = { size = 0x20 } # Phase 4 reviewed P4-SYNTHETIC\n',
        )


if __name__ == "__main__":
    unittest.main()
