from __future__ import annotations

import copy
import csv
import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools/phase2i/Fable2AnalystExport.py"
SPEC = importlib.util.spec_from_file_location("fable2_phase2i_export", MODULE_PATH)
assert SPEC and SPEC.loader
exporter = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = exporter
SPEC.loader.exec_module(exporter)
annotations = exporter.annotations


def selection(mapping: str = "phase2e-v1", semantic: str = "none") -> dict:
    return {
        "mapping": {"view": mapping, "active_count": 15379 if mapping == "phase2e-v1" else 0, "opt_in": None},
        "semantic": {"view": semantic, "context_count": 0, "opt_in": None},
    }


class ExportModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = json.loads((ROOT / annotations.INDEX_PATH).read_bytes())
        cls.index_identity = exporter.sources.identity(annotations.INDEX_PATH)
        cls.selected = annotations.selected_records(cls.index, selection())
        cls.records, cls.counts = annotations.profile_records(
            cls.selected, "overlay-review", selection()
        )
        cls.bundle = exporter.build_bundle(cls.records, selection(), "overlay-review", cls.counts, [], cls.index_identity)
        cls.plan = exporter.build_ghidra_plan(cls.records, selection(), "overlay-review", cls.counts, cls.index_identity)
        cls.rollback = exporter.build_rollback_manifest(cls.records, selection(), "overlay-review", cls.counts, cls.index_identity)
        cls.table = exporter.tsv_bytes(cls.records)

    def test_bundle_plan_table_and_rollback_reconcile(self) -> None:
        exporter.validate_reconciliation(self.bundle, self.plan, self.rollback, self.table)
        self.assertEqual(len(self.records), 86)

    def test_table_is_deterministic_and_has_one_row_per_record(self) -> None:
        self.assertEqual(self.table, exporter.tsv_bytes(self.records))
        rows = list(csv.DictReader(io.StringIO(self.table.decode("utf-8")), dialect="excel-tab"))
        self.assertEqual(len(rows), len(self.records))
        self.assertEqual([row["annotation_id"] for row in rows], [row["annotation_id"] for row in self.records])

    def test_plan_is_data_only(self) -> None:
        self.assertEqual(self.plan["mode"], "preview-only-data-plan")
        self.assertFalse(self.plan["executable_code"])
        self.assertFalse(self.plan["naming_capability"])
        self.assertFalse(self.plan["database_write_capability"])
        forbidden_keys = {"rename_to", "symbol_name", "function_name", "transaction", "save_database"}
        for entry in self.plan["entries"]:
            self.assertFalse(set(entry) & forbidden_keys)
            self.assertEqual(entry["comment_type"], "PRE_COMMENT")
            self.assertTrue(entry["bookmark_category"].startswith("F2PA/Phase2I/"))

    def test_plan_same_address_stable_authority_order(self) -> None:
        entries = [entry for entry in self.plan["entries"] if entry["target_address"] == "0x83060C30"]
        self.assertEqual(len(entries), 2)
        records = {row["annotation_id"]: row for row in self.records}
        self.assertEqual([records[entry["annotation_id"]]["display_kind"] for entry in entries], ["suppression-warning", "overlay-addition"])

    def test_every_block_hash_reconciles(self) -> None:
        by_id = {row["annotation_id"]: row for row in self.records}
        for entry in self.plan["entries"]:
            self.assertEqual(entry["namespaced_block_sha256"], exporter.block_identity(by_id[entry["annotation_id"]]))

    def test_preview_is_bounded_and_deterministic(self) -> None:
        first = exporter.preview_bytes(self.records, selection(), "overlay-review", self.counts, 5)
        second = exporter.preview_bytes(self.records, selection(), "overlay-review", self.counts, 5)
        self.assertEqual(first, second)
        text = first.decode("utf-8")
        self.assertIn("Displayed: 5", text)
        self.assertIn("Omitted by preview bound: 81", text)

    def test_output_confinement(self) -> None:
        relative, resolved = exporter.export_root("out/prototype-archaeology/phase2i/profiles/test")
        self.assertEqual(relative.as_posix(), "out/prototype-archaeology/phase2i/profiles/test")
        self.assertTrue(resolved.is_relative_to((ROOT / exporter.sources.OUT).resolve()))
        with self.assertRaises(annotations.SelectionError):
            exporter.export_root("../outside")
        with self.assertRaises(annotations.SelectionError):
            exporter.export_root("out/prototype-archaeology/phase2h")


class CollisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        index = json.loads((ROOT / annotations.INDEX_PATH).read_bytes())
        cls.record = next(row for row in index["records"] if row["display_kind"] == "owner-reviewed-contextual-role")

    def test_no_preexisting_comment(self) -> None:
        result = exporter.simulate_collision(None, [], self.record)
        self.assertEqual(result["disposition"], "add-to-empty-comment")
        self.assertEqual(result["comment_after_preview"], exporter.namespaced_block(self.record))
        self.assertFalse(result["write_performed"])

    def test_existing_user_comment_is_preserved(self) -> None:
        user = "analyst text byte-for-byte"
        result = exporter.simulate_collision(user, [], self.record)
        self.assertEqual(result["disposition"], "append-after-user-content")
        self.assertTrue(result["comment_after_preview"].startswith(user + "\n"))
        removal = exporter.removal_preview(result["comment_after_preview"], self.record)
        self.assertEqual(removal["comment_after_preview"], user)

    def test_existing_unrelated_bookmark_is_preserved(self) -> None:
        bookmarks = [{"category": "User", "note": "keep"}]
        result = exporter.simulate_collision("", bookmarks, self.record)
        self.assertEqual(result["bookmarks_before"], bookmarks)
        self.assertEqual(result["bookmarks_after_preview"], bookmarks)
        self.assertTrue(result["unrelated_bookmarks_preserved"])

    def test_identical_owned_block_is_idempotent(self) -> None:
        block = exporter.namespaced_block(self.record)
        result = exporter.simulate_collision(block, [], self.record)
        self.assertEqual(result["disposition"], "idempotent-identical-owned-block")
        self.assertEqual(result["comment_after_preview"], block)

    def test_stale_same_id_block_conflicts(self) -> None:
        stale = self.record["namespace_marker"] + "\nstale content"
        result = exporter.simulate_collision(stale, [], self.record)
        self.assertEqual(result["disposition"], "conflict-stale-owned-block")
        self.assertEqual(result["comment_after_preview"], stale)
        removal = exporter.removal_preview(stale, self.record)
        self.assertEqual(removal["disposition"], "conflict-stale-owned-block")
        self.assertEqual(removal["comment_after_preview"], stale)

    def test_exact_removal_preserves_surrounding_user_bytes(self) -> None:
        user = "prefix\nwith user formatting  "
        planned = exporter.simulate_collision(user, [], self.record)["comment_after_preview"]
        removal = exporter.removal_preview(planned, self.record)
        self.assertEqual(removal["disposition"], "exact-owned-block-removal-preview")
        self.assertEqual(removal["comment_after_preview"].encode("utf-8"), user.encode("utf-8"))

    def test_two_records_at_one_address_remain_distinct(self) -> None:
        index = json.loads((ROOT / annotations.INDEX_PATH).read_bytes())
        records = [row for row in index["records"] if row["target"]["range"]["start"] == "0x82522C10"]
        self.assertGreaterEqual(len(records), 3)
        self.assertEqual(len(records), len({row["annotation_id"] for row in records}))


if __name__ == "__main__":
    unittest.main()
