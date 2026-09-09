"""Portable metadata fixtures plus adversarial semantic and PPC decoder checks."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import Fable2OwnershipCorroboration as ownership
from test_fable2_indirect_targets import schema_errors

EVIDENCE = ROOT / "docs/fable2-discovery-pipeline/ownership"


class OwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((EVIDENCE / "ownership-ledger.json").read_text())
        cls.expected = {(r["target"], r["phase4_category"]) for r in cls.report["targets"]}

    def mutated(self):
        return copy.deepcopy(self.report)

    def test_accepted_corpus_and_exact_population(self):
        ownership.validate(self.report, self.expected)
        self.assertEqual(self.report["counts"]["by_phase4_category"], {
            "existing_function_internal_entry": 42, "known_jump_table_case": 114})
        self.assertEqual(self.report["counts"]["unresolved"], 0)

    def test_schemas_and_review_companion(self):
        for filename, schema_name in (("ownership-ledger.json", "fable2-focused-ownership-ledger"),
                                      ("ownership-reviewed-import-plan.json", "fable2-ownership-reviewed-plan")):
            data = json.loads((EVIDENCE / filename).read_text())
            schema = json.loads((ROOT / f"tools/schemas/{schema_name}-v1.schema.json").read_text())
            self.assertEqual(schema_errors(data, schema), [])
        self.assertEqual(json.loads((EVIDENCE / "ownership-reviewed-import-plan.json").read_text()),
                         ownership.reviewed_plan(self.report))

    def test_duplicate_rejected(self):
        data = self.mutated()
        data["targets"].append(data["targets"][0])
        with self.assertRaisesRegex(ValueError, "duplicate ledger"):
            ownership.validate(data, self.expected)

    def test_omission_rejected(self):
        data = self.mutated()
        data["targets"].pop()
        with self.assertRaisesRegex(ValueError, "coverage mismatch"):
            ownership.validate(data, self.expected)

    def test_counts_rejected(self):
        data = self.mutated()
        data["counts"]["targets"] -= 1
        with self.assertRaisesRegex(ValueError, "total mismatch"):
            ownership.validate(data)

    def test_overlapping_owner_rejected(self):
        data = self.mutated()
        data["targets"][0]["boundary_evidence"]["unique_exact_body_owners"].append("0x82000000")
        with self.assertRaisesRegex(ValueError, "overlapping owner"):
            ownership.validate(data)

    def test_false_promotion_rejected(self):
        data = self.mutated()
        data["targets"][0]["independent_function_proven"] = True
        with self.assertRaisesRegex(ValueError, "unsupported promotion"):
            ownership.validate(data)

    def test_wrong_lr_rejected(self):
        data = self.mutated()
        data["targets"][0]["return_checks"][0]["lr_after_call"] = "0x82000000"
        with self.assertRaisesRegex(ValueError, "invalid return pairing"):
            ownership.validate(data)

    def test_omitted_return_source_rejected(self):
        data = self.mutated()
        data["targets"][0]["return_checks"][0]["source"] = "0x82000000"
        with self.assertRaisesRegex(ValueError, "return sources omitted"):
            ownership.validate(data)

    def test_wrong_dispatch_owner_rejected(self):
        data = self.mutated()
        data["dispatchers"][0]["owner"] = "0x82000000"
        with self.assertRaisesRegex(ValueError, "wrong dispatcher owner"):
            ownership.validate(data)

    def test_wrong_case_index_rejected(self):
        data = self.mutated()
        row = next(r for r in data["targets"] if r["case_membership"])
        row["case_membership"][0]["indices"] = []
        with self.assertRaisesRegex(ValueError, "case membership mismatch"):
            ownership.validate(data)

    def test_ignored_boundary_conflict_rejected(self):
        data = self.mutated()
        data["targets"][0]["boundary_evidence"]["exact_ghidra_start"] = {"entry": data["targets"][0]["target"]}
        with self.assertRaisesRegex(ValueError, "boundary conflict"):
            ownership.validate(data)

    def test_default_membership_rejected(self):
        data = self.mutated()
        row = next(r for r in data["targets"] if r["case_membership"])
        row["case_membership"][0]["default_destination"] = not row["case_membership"][0]["default_destination"]
        with self.assertRaisesRegex(ValueError, "default case mismatch"):
            ownership.validate(data)

    def test_false_tail_function_rejected(self):
        data = self.mutated()
        row = next(r for r in data["targets"] if r["immediate_tail_transfer"])
        row["immediate_tail_transfer"]["case_itself_is_standalone_thunk"] = True
        with self.assertRaisesRegex(ValueError, "invalid tail transfer"):
            ownership.validate(data)

    def test_direct_branch_sign_extension_and_link(self):
        self.assertEqual(ownership.direct_branch(0x82000100, 0x4BFFFFFD), 0x820000FC)
        self.assertEqual(ownership.direct_branch(0x82000100, 0x48000009), 0x82000108)
        self.assertEqual(ownership.direct_branch(0x82000100, 0x48000102), 0x100)
        self.assertIsNone(ownership.direct_branch(0x82000100, 0x4E800421))

    def test_conditional_returns_not_calls_or_ordinary_blr(self):
        self.assertTrue(ownership.conditional_lr_return(0x4D820020))
        self.assertTrue(ownership.conditional_lr_return(0x4C820020))
        for word in (0x4E800020, 0x4D820021, 0x4E800420, 0x4E800421):
            self.assertFalse(ownership.conditional_lr_return(word))

    def test_signed_relative_table_and_mismatch(self):
        table = {"element_width": 1, "element_signed": True, "table_address": "0x82000000",
                 "storage_size": "0x00000002", "case_count": 2, "kind": "relative_offset",
                 "anchor_address": "0x82000100", "target_scale": 4,
                 "targets": ["0x820000FC", "0x82000108"]}
        read = lambda address, size: bytes([255, 2])[address - 0x82000000:address - 0x82000000 + size]
        self.assertEqual(ownership.decode_table(table, read), table["targets"])
        table["targets"][0] = "0x82000000"
        with self.assertRaisesRegex(ValueError, "table bytes disagree"):
            ownership.decode_table(table, read)

    def test_markdown_is_generated(self):
        self.assertEqual((EVIDENCE / "ownership-ledger.md").read_bytes(), ownership.markdown(self.report))


if __name__ == "__main__":
    unittest.main()
