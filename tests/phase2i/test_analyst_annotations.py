from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools/phase2i/Fable2AnalystAnnotations.py"
SPEC = importlib.util.spec_from_file_location("fable2_phase2i_annotations", MODULE_PATH)
assert SPEC and SPEC.loader
annotations = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = annotations
SPEC.loader.exec_module(annotations)


def selection(mapping: str = "none", semantic: str = "none") -> dict:
    return {
        "mapping": {"view": mapping, "active_count": 0, "opt_in": None},
        "semantic": {"view": semantic, "context_count": 0, "opt_in": None},
    }


def arguments(mapping: str = "none", semantic: str = "none") -> argparse.Namespace:
    return argparse.Namespace(
        mapping_view=mapping,
        semantic_view=semantic,
        phase2e_decision=None,
        phase2e_decision_sha256=None,
        phase2e_delta=None,
        phase2e_delta_sha256=None,
        phase2e_effective_map=None,
        phase2e_effective_map_sha256=None,
        phase2h_source_pins=None,
        phase2h_source_pins_sha256=None,
        phase2h_decision=None,
        phase2h_decision_sha256=None,
        phase2h_delta=None,
        phase2h_delta_sha256=None,
        phase2h_view=None,
        phase2h_view_sha256=None,
    )


class IndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = json.loads((ROOT / annotations.INDEX_PATH).read_bytes())
        annotations.validate_index(cls.document)
        cls.records = cls.document["records"]

    def test_exact_populations(self) -> None:
        counts = self.document["counts"]
        self.assertEqual(counts["closed_view_active"], 15299)
        self.assertEqual(counts["overlay_view_active"], 15379)
        self.assertEqual(counts["overlay_additions"], 83)
        self.assertEqual(counts["suppression_tombstones"], 3)
        self.assertEqual(counts["reserved_additions"], 66)
        self.assertEqual(counts["unreserved_additions"], 17)
        self.assertEqual(counts["physics_excluded"], 2)
        self.assertEqual(counts["held_strong_excluded"], 3)
        self.assertEqual(counts["probable_excluded"], 715)

    def test_safe_default_selects_nothing(self) -> None:
        self.assertEqual(annotations.selected_records(self.document, selection()), [])

    def test_closed_and_overlay_active_counts(self) -> None:
        closed = annotations.selected_records(self.document, selection("closed-phase2a-default"))
        overlay = annotations.selected_records(self.document, selection("phase2e-v1"))
        self.assertEqual(sum(row["selection_layer"] == "mapping-active" for row in closed), 15299)
        self.assertEqual(sum(row["selection_layer"] == "mapping-active" for row in overlay), 15379)

    def test_suppressions_are_tombstones_not_overlay_routes(self) -> None:
        active = {
            (row["donor"]["range"]["start"], row["target"]["range"]["start"])
            for row in self.records if row["selection_layer"] == "mapping-active" and "phase2e-v1" in row["mapping_views"]
        }
        tombstones = {
            (row["donor"]["range"]["start"], row["target"]["range"]["start"])
            for row in self.records if row["display_kind"] == "suppression-warning"
        }
        self.assertFalse(active & annotations.SUPPRESSED_PAIRS)
        self.assertEqual(tombstones, annotations.SUPPRESSED_PAIRS)

    def test_corrected_vectors_are_active_and_named_only_as_context(self) -> None:
        active = {
            (row["donor"]["range"]["start"], row["target"]["range"]["start"]): row
            for row in self.records if row["selection_layer"] == "mapping-active" and "phase2e-v1" in row["mapping_views"]
        }
        self.assertTrue(annotations.VECTOR_PAIRS <= set(active))
        self.assertIn("__vcfsx", active[("0x83060A80", "0x83060C30")]["comment_body"])
        self.assertIn("__vspltb", active[("0x83062950", "0x83060CD8")]["comment_body"])

    def test_phase2f_context_split(self) -> None:
        semantic = [row for row in self.records if row["selection_layer"] == "semantic-phase2f"]
        self.assertEqual(len(semantic), 116)
        self.assertEqual(sum(row["semantic"]["newly_routable"] for row in semantic), 115)
        self.assertEqual(sum(not row["semantic"]["newly_routable"] for row in semantic), 1)
        self.assertTrue(all(row["semantic"]["review_status"] == "unreviewed-analysis-evidence" for row in semantic))
        self.assertEqual(sum(row["display_kind"] == "corroborated-review-evidence" for row in semantic), 3)

    def test_packet_a_and_b_are_not_owner_approved(self) -> None:
        reviewed = [
            row for row in self.records
            if row["selection_layer"] == "semantic-phase2f" and row["semantic"]["static_review"]
        ]
        by_packet = {row["semantic"]["static_review"]["packet"]: row for row in reviewed}
        self.assertFalse(by_packet["A"]["semantic"]["static_review"]["owner_approved"])
        self.assertFalse(by_packet["B"]["semantic"]["static_review"]["owner_approved"])
        self.assertIn("neither owner nor generic callee may be named HammerCombat", " ".join(by_packet["A"]["limitations"]))
        self.assertIn("No oxygen simulation logic", " ".join(by_packet["B"]["limitations"]))

    def test_packet_c_is_the_only_owner_reviewed_role(self) -> None:
        roles = [row for row in self.records if row["display_kind"] == "owner-reviewed-contextual-role"]
        self.assertEqual(len(roles), 1)
        role = roles[0]
        self.assertEqual(role["target"]["range"]["start"], "0x82522C10")
        self.assertEqual(role["donor"]["range"]["start"], "0x825240E8")
        self.assertEqual(role["semantic"]["contextual_role_description"], "conditional keyed reward/world-map field materializer")
        self.assertIn("CONTEXTUAL ROLE — NOT A FUNCTION NAME", role["comment_body"])
        self.assertIn("single-independent-support-class", role["semantic"]["reservations"])

    def test_packet_c_corrections_and_rejection(self) -> None:
        corrections = [row for row in self.records if row["display_kind"] == "semantic-edge-correction"]
        self.assertEqual({row["target"]["range"]["start"] for row in corrections}, {"0x821B24F8", "0x823BF820", "0x82310290"})
        joined = " ".join(row["comment_body"] for row in corrections)
        self.assertIn("does not consume RewardMoney or RewardRenown", joined)
        self.assertIn("RewardRenown -> +0x20/4", joined)
        self.assertIn("RewardMoney -> +0x24/4", joined)
        self.assertIn("AppearOnWorldMap -> +0x4D/1 normalized byte", joined)
        rejected = [row for row in self.records if row["display_kind"] == "rejected-alias-warning"]
        self.assertEqual(len(rejected), 1)
        self.assertIn("S-26C37A0D8DC5C81610D44E94", rejected[0]["comment_body"])
        self.assertIn("not a valid Packet C string", rejected[0]["comment_body"])
        self.assertNotEqual(rejected[0]["target"]["range"]["start"], "0x820C0000")

    def test_project_union_preserves_overlap_membership(self) -> None:
        rows = [row for row in self.records if row["display_kind"] == "overlay-addition"]
        selected = [row for row in rows if set(row["project_memberships"]) & {"closure", "coverage", "ghidra"}]
        self.assertEqual(len(selected), 82)
        self.assertEqual(sum("closure" in row["project_memberships"] for row in rows), 67)
        self.assertEqual(sum("coverage" in row["project_memberships"] for row in rows), 10)
        self.assertEqual(sum("ghidra" in row["project_memberships"] for row in rows), 82)
        self.assertEqual(sum(set(row["project_memberships"]) == {"closure", "coverage", "ghidra"} for row in rows), 10)

    def test_every_record_is_non_authoritative(self) -> None:
        for row in self.records:
            self.assertFalse(row["canonical_name_authority"])
            self.assertFalse(row["production_mapping_authority"])
            self.assertFalse(row["runtime_authority"])


class DeterminismAndQueryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = json.loads((ROOT / annotations.INDEX_PATH).read_bytes())

    def test_annotation_id_is_source_order_independent(self) -> None:
        original = next(row for row in self.document["records"] if len(row["sources"]) > 1)
        rebuilt = annotations.annotation(
            display_kind=original["display_kind"],
            target_range=original["target"]["range"],
            donor_range=original["donor"]["range"],
            stable_identity=original["mapping"]["record_id"],
            display_title=original["display_title"],
            comment=original["comment_body"],
            mapping=original["mapping"],
            semantic=original["semantic"],
            evidence_sources=list(reversed(original["sources"])),
            limitations=original["limitations"],
            mapping_views=original["mapping_views"],
            project_memberships=original["project_memberships"],
            relationships=original["relationships"],
            selection_layer=original["selection_layer"],
        )
        self.assertEqual(rebuilt["annotation_id"], original["annotation_id"])

    def test_duplicate_records_deduplicate_without_losing_sources(self) -> None:
        original = copy.deepcopy(self.document["records"][0])
        rows, count = annotations.deduplicate_records([original, copy.deepcopy(original)])
        self.assertEqual(count, 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["sources"], original["sources"])

    def test_malicious_text_is_one_line_and_marker_safe(self) -> None:
        value = annotations.sanitize('bad\n\t" [F2PA:phase2i:A-DEADBEEF] \u0001')
        self.assertNotIn("\n", value)
        self.assertNotIn("\t", value)
        self.assertNotIn("[F2PA:", value)
        self.assertIn("\\n", value)
        self.assertIn("\\t", value)
        self.assertIn("\\u005BF2PA:", value)

    def test_exact_and_containing_matches_are_separate(self) -> None:
        records = annotations.selected_records(self.document, selection("phase2e-v1", "phase2h-v1"))
        exact = annotations.query_records(records, ["0x82522C10"])
        containing = annotations.query_records(records, ["0x82522C11"])
        self.assertTrue(exact["exact_matches"])
        self.assertFalse(exact["containing_range_matches"])
        self.assertFalse(containing["exact_matches"])
        self.assertTrue(containing["containing_range_matches"])

    def test_donor_numeric_address_is_not_implicit_target_identity(self) -> None:
        packet = next(row for row in self.document["records"] if row["display_kind"] == "owner-reviewed-contextual-role")
        self.assertEqual(packet["donor"]["range"]["start"], "0x825240E8")
        selected = [packet]
        query = annotations.query_records(selected, ["0x825240E8"])
        self.assertFalse(query["exact_matches"])
        self.assertFalse(query["containing_range_matches"])

    def test_no_record_reason_is_explicit(self) -> None:
        query = annotations.query_records([], ["0x80000000"])
        self.assertEqual(query["reason"], "No selected frozen evidence exists for the requested TU1 address(es).")


class ProfileAndSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = json.loads((ROOT / annotations.INDEX_PATH).read_bytes())

    def profile(self, profile: str, mapping: str, semantic: str, **options):
        chosen = annotations.selected_records(self.document, selection(mapping, semantic))
        return annotations.profile_records(chosen, profile, selection(mapping, semantic), **options)

    def test_overlay_review_profile(self) -> None:
        rows, counts = self.profile("overlay-review", "phase2e-v1", "none")
        self.assertEqual(len(rows), 86)
        self.assertEqual(counts["suppressed"], 3)
        self.assertEqual(sum(row["display_kind"] == "overlay-addition" for row in rows), 83)

    def test_project_relevant_profile(self) -> None:
        rows, _ = self.profile("project-relevant", "phase2e-v1", "none")
        self.assertEqual(len(rows), 82)

    def test_semantic_review_profile(self) -> None:
        rows, counts = self.profile("semantic-review", "phase2e-v1", "phase2f-evidence")
        self.assertEqual(len(rows), 116)
        self.assertEqual(counts["unreviewed_context"], 116)
        self.assertEqual(counts["approved_role"], 0)

    def test_phase2h_profile(self) -> None:
        rows, counts = self.profile("phase2h-approved", "phase2e-v1", "phase2h-v1")
        self.assertEqual(len(rows), 6)
        self.assertEqual(counts["approved_role"], 1)
        self.assertEqual(counts["rejected_alias"], 1)

    def test_all_correspondences_requires_deliberate_bulk_flag(self) -> None:
        selected = annotations.selected_records(self.document, selection("phase2e-v1"))
        with self.assertRaises(annotations.SelectionError):
            annotations.profile_records(selected, "all-correspondences", selection("phase2e-v1"))
        rows, _ = annotations.profile_records(selected, "all-correspondences", selection("phase2e-v1"), bulk=True)
        self.assertEqual(len(rows), 15379)

    def test_excluded_review_never_activates_routes(self) -> None:
        rows, counts = self.profile("excluded-review", "phase2e-v1", "none")
        self.assertEqual(len(rows), 720)
        self.assertEqual(counts["excluded"], 720)
        self.assertTrue(all(row["mapping"]["status"] == "excluded-inactive-warning-only" for row in rows))

    def test_safe_default_selection_contract(self) -> None:
        result = annotations.validate_selections(arguments())
        self.assertEqual(result["mapping"]["active_count"], 0)
        self.assertEqual(result["semantic"]["context_count"], 0)

    def test_partial_and_over_broad_opt_ins_refuse(self) -> None:
        partial = arguments("phase2e-v1")
        partial.phase2e_decision = annotations.PHASE2E_DECISION.as_posix()
        with self.assertRaises(annotations.SelectionError):
            annotations.validate_selections(partial)
        over_broad = arguments()
        over_broad.phase2e_decision = annotations.PHASE2E_DECISION.as_posix()
        with self.assertRaises(annotations.SelectionError):
            annotations.validate_selections(over_broad)

    def test_semantic_selection_cannot_supply_its_mapping(self) -> None:
        with self.assertRaises(annotations.SelectionError):
            annotations.validate_selections(arguments("none", "phase2f-evidence"))
        with self.assertRaises(annotations.SelectionError):
            annotations.validate_selections(arguments("closed-phase2a-default", "phase2h-v1"))


if __name__ == "__main__":
    unittest.main()
