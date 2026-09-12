"""Phase 2E decision, overlay, consumer and rollback regressions."""

from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/phase2e"))

import Fable2PrototypeOverlay as overlay


class CanonicalHashAndPathTests(unittest.TestCase):
    def test_set_hash_is_sorted_compact_json_with_one_lf(self):
        self.assertEqual(overlay.set_hash(["b", "a"]), overlay.sha256(b'["a","b"]\n'))
        self.assertEqual(
            "8E9CBB93751C0F0B13FF04F1809207D72C0C96587369FEEA0C528F0A9EEE2363",
            overlay.set_hash(overlay.validate_decision_inputs()["selected_ids"]),
        )

    def test_duplicate_set_identity_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            overlay.set_hash(["same", "same"])

    def test_output_root_and_traversal_enforcement(self):
        for path in ("../escape.json", "fable2_manifest.toml", "generated/default/bad.json", str(ROOT / "absolute.json")):
            with self.subTest(path=path), self.assertRaises(ValueError):
                overlay.output_path(path)

    def test_reference_text_cannot_become_canonical_name(self):
        overlay.assert_no_canonical_names({"contextual_reference_text": ["HammerCombat"], "canonical_function_name": None})
        with self.assertRaisesRegex(ValueError, "canonical function name"):
            overlay.assert_no_canonical_names({"canonical_function_name": "HammerCombat"})


class OwnerDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = overlay.validate_decision_inputs()
        cls.decision = overlay.build_owner_decision()

    def test_exact_frozen_ledger_and_batch_identities(self):
        ledger = self.inputs["ledger"]
        self.assertEqual(91, len(ledger["records"]))
        self.assertEqual(overlay.PHASE2D_LEDGER_SET_HASH, ledger["proposal_set_sha256"])
        self.assertTrue(all(row["human_decision"] == "pending" for row in ledger["records"]))
        self.assertFalse(ledger["human_approval"])
        self.assertFalse(ledger["canonical_adoption"])
        for batch_id, (count, expected_hash) in overlay.APPROVED_BATCHES.items():
            row = self.inputs["batch_rows"][batch_id]
            self.assertEqual(count, len(row["mapping_ids"]))
            self.assertEqual(expected_hash, overlay.set_hash(row["mapping_ids"]))

    def test_b00_is_recomputed_from_risk_artifact(self):
        row = self.inputs["risk"]["mandatory_suppression_batch"]
        self.assertEqual(3, row["mapping_count"])
        self.assertEqual(overlay.APPROVED_BATCHES[row["id"]][1], overlay.set_hash(row["mapping_ids"]))

    def test_selected_action_population_is_exactly_86(self):
        self.assertEqual(86, len(self.inputs["selected_ids"]))
        self.assertEqual(overlay.SELECTED_ACTION_SET_HASH, overlay.set_hash(self.inputs["selected_ids"]))

    def test_external_decision_values_and_surface_are_exact(self):
        decision = self.decision["decision"]
        self.assertEqual("FenrisSkoll", decision["approver_identity"])
        self.assertEqual("2026-09-12T22:00:00+01:00", decision["decision_timestamp"])
        self.assertEqual("P2D-OWNER-DECISION-001", decision["external_decision_record_id"])
        self.assertEqual("approve", decision["decision"])
        self.assertEqual("reversible non-canonical semantic-transport and mapping overlay only", decision["approved_surface"])
        self.assertTrue(self.decision["human_approval"])
        self.assertFalse(self.decision["canonical_adoption"])

    def test_altered_owner_data_fails_closed(self):
        mutations = {
            "approver_identity": "someone-else",
            "decision_timestamp": "2026-09-12T22:00:01+01:00",
            "external_decision_record_id": "changed",
            "approved_surface": "canonical",
        }
        for key, value in mutations.items():
            changed = copy.deepcopy(self.decision)
            changed["decision"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                overlay.validate_decision_records([changed])

    def test_altered_selected_set_hash_fails_closed(self):
        changed = copy.deepcopy(self.decision)
        changed["selected_action_set_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            overlay.validate_decision_records([changed])

    def test_duplicate_decision_record_id_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            overlay.validate_decision_records([self.decision, copy.deepcopy(self.decision)])

    def test_unknown_or_altered_batch_fails_closed(self):
        changed = copy.deepcopy(self.decision)
        changed["approved_batches"][0]["id"] = "B99-unknown"
        with self.assertRaises(ValueError):
            overlay.validate_decision_records([changed])

    def test_empty_batches_cannot_authorize_anything(self):
        for batch_id in overlay.EMPTY_BATCHES:
            row = self.inputs["batch_rows"][batch_id]
            self.assertEqual([], row["mapping_ids"])
            self.assertEqual(0, row["mapping_count"])
            self.assertNotIn(batch_id, overlay.APPROVED_BATCHES)

    def test_packet_hashes_are_bound_for_all_86_actions(self):
        selected = self.decision["selected_actions"]
        self.assertEqual(86, len(selected))
        self.assertTrue(all(len(row["phase2d_packet"]["sha256"]) == 64 for row in selected))


class DeltaAndMappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.delta = overlay.build_delta()
        cls.effective, cls.dependencies = overlay.build_effective_map(cls.delta)
        cls.pairs = {(row["donor_start"], row["target_start"]) for row in cls.effective["records"]}

    def test_delta_counts(self):
        actions = self.delta["actions"]
        suppressions = [row for row in actions if row["action"] == "suppress-semantic-transport"]
        additions = [row for row in actions if row["action"] == "add-mapping"]
        self.assertEqual((3, 83, 86), (len(suppressions), len(additions), len(actions)))

    def test_exact_effective_arithmetic_and_injectivity(self):
        counts = self.effective["counts"]
        self.assertEqual((15299, 3, 83, 15379),
                         (counts["closed_phase2a"], counts["semantic_transport_suppressions"], counts["mapping_additions"], counts["effective"]))
        records = self.effective["records"]
        self.assertEqual(15379, len(records))
        self.assertEqual(15379, len({row["donor_start"] for row in records}))
        self.assertEqual(15379, len({row["target_start"] for row in records}))

    def test_all_three_suppressions_and_vector_replacements(self):
        self.assertFalse(overlay.SUPPRESSED_PAIRS & self.pairs)
        self.assertIn(("0x83060A80", "0x83060C30"), self.pairs)
        self.assertIn(("0x83062950", "0x83060CD8"), self.pairs)
        self.assertNotIn(("0x83062950", "0x83060C30"), self.pairs)

    def test_suppression_precedence_routes(self):
        documents = overlay.build_materialized_documents(self.delta)
        audit = documents[overlay.OUT / "suppression-route-audit.json"]
        self.assertEqual(3, len(audit["records"]))
        for row in audit["records"]:
            self.assertFalse(row["effective_pair_present"])
            self.assertEqual({"primary", "dependency", "fallback", "september", "consumer_merge"}, set(row["routes"]))

    def test_b01_unreserved_and_66_exact_reservations(self):
        additions = [row for row in self.delta["actions"] if row["action"] == "add-mapping"]
        b01 = [row for row in additions if row["source_batch"]["id"] == "B01-unreserved"]
        reserved = [row for row in additions if row["reservations"]]
        self.assertEqual(17, len(b01))
        self.assertTrue(all(row["reservations"] == [] for row in b01))
        self.assertEqual(66, len(reserved))

    def test_hammer_mapping_is_context_not_name(self):
        hammer = next(row for row in self.effective["records"] if (row["donor_start"], row["target_start"]) == overlay.HAMMER_PAIR)
        self.assertEqual(("0x8229B504", "0x8229B234"), (hammer["donor_end_exclusive"], hammer["target_end_exclusive"]))
        self.assertEqual(["internal-code-region-dependent"], hammer["reservations"])
        self.assertIsNone(hammer["canonical_function_name"])

    def test_physics_held_strong_and_probable_exclusions(self):
        documents = overlay.build_materialized_documents(self.delta)
        audit = documents[overlay.OUT / "exclusion-audit.json"]
        self.assertEqual(2, audit["counts"]["physics_candidates_excluded"])
        self.assertEqual(3, audit["counts"]["held_original_strong_excluded"])
        self.assertEqual(715, audit["counts"]["probable_proposals_excluded"])
        self.assertTrue(all(not row["effective_pair_present"] for row in audit["unapproved_phase2d_ledger_records"]))
        self.assertTrue(all(not row["effective_pair_present"] for row in audit["probable_proposals"]))

    def test_dependency_consistency(self):
        self.assertEqual(0, self.dependencies["cycles"])
        self.assertEqual(0, self.dependencies["same_generation_edges"])
        self.assertEqual(0, self.dependencies["dangling_edges"])

    def test_dangling_suppressed_and_same_generation_dependencies_fail(self):
        base_record = {
            "provenance": {"record_sha256": "A" * 64},
        }
        retained = {("S", "T"): base_record}
        action = {
            "phase2d_ledger_id": "A:B",
            "donor": {"start": "A"},
            "target": {"start": "B"},
            "original_phase2c_generation": 1,
            "dependency_seeds": [{"donor": "missing", "target": "missing", "generation": 0, "closed_record_sha256": "A" * 64}],
        }
        with self.assertRaisesRegex(ValueError, "Dangling"):
            overlay.validate_dependencies([action], retained)
        suppressed = copy.deepcopy(action)
        suppressed["dependency_seeds"][0].update(donor="0x83062950", target="0x83060C30")
        with self.assertRaisesRegex(ValueError, "Suppressed"):
            overlay.validate_dependencies([suppressed], retained)
        same = copy.deepcopy(action)
        same["dependency_seeds"][0].update(donor="A", target="B", generation=1)
        with self.assertRaisesRegex(ValueError, "Same-generation"):
            overlay.validate_dependencies([same], retained)

    def test_byte_identical_in_memory_reconstruction(self):
        self.assertEqual(overlay.payload(self.delta), overlay.payload(overlay.build_delta()))
        self.assertEqual(overlay.payload(self.effective), overlay.payload(overlay.build_effective_map(self.delta)[0]))


@unittest.skipUnless((ROOT / overlay.OUT / "effective-map.json").is_file(), "Phase 2E overlay not materialized")
class ConsumerAndRollbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decision_path = ROOT / overlay.DECISION_PATH
        cls.delta_path = ROOT / overlay.DELTA_PATH
        cls.effective_path = ROOT / overlay.OUT / "effective-map.json"
        cls.decision_hash = overlay.sha256(cls.decision_path.read_bytes())
        cls.delta_hash = overlay.sha256(cls.delta_path.read_bytes())
        cls.effective_hash = overlay.sha256(cls.effective_path.read_bytes())

    def test_default_selection_is_unchanged_phase2a(self):
        before = overlay.identity(overlay.PHASE2A_MAP_PATH)
        selection = overlay.load_default_mapping()
        after = overlay.identity(overlay.PHASE2A_MAP_PATH)
        self.assertEqual(before, after)
        self.assertEqual("closed-phase2a-default", selection["selection"])
        self.assertEqual(15299, selection["mapping_count"])
        self.assertFalse(selection["overlay_enabled"])

    def test_explicit_opt_in_loads_exact_overlay_and_provenance(self):
        document, provenance = overlay.load_opt_in_mapping(
            overlay.OVERLAY_VERSION,
            self.decision_path,
            self.decision_hash,
            self.delta_path,
            self.delta_hash,
            self.effective_path,
            self.effective_hash,
        )
        self.assertEqual(15379, len(document["records"]))
        self.assertEqual("P2D-OWNER-DECISION-001", provenance["owner_decision_record_id"])
        self.assertEqual(self.effective_hash, provenance["effective_map"]["sha256"])
        self.assertFalse(provenance["fallback_permitted"])

    def test_missing_stale_tampered_or_unknown_overlay_refuses_without_fallback(self):
        with tempfile.TemporaryDirectory(dir=ROOT / overlay.OUT) as folder:
            temp_root = Path(folder)
            tampered = temp_root / "effective-map.json"
            shutil.copyfile(self.effective_path, tampered)
            tampered.write_bytes(tampered.read_bytes() + b" ")
            cases = [
                ("unknown", self.decision_path, self.decision_hash, self.delta_path, self.delta_hash, self.effective_path, self.effective_hash),
                (overlay.OVERLAY_VERSION, temp_root / "missing.json", self.decision_hash, self.delta_path, self.delta_hash, self.effective_path, self.effective_hash),
                (overlay.OVERLAY_VERSION, self.decision_path, "0" * 64, self.delta_path, self.delta_hash, self.effective_path, self.effective_hash),
                (overlay.OVERLAY_VERSION, self.decision_path, self.decision_hash, self.delta_path, self.delta_hash, tampered, self.effective_hash),
            ]
            for case in cases:
                with self.subTest(case=case[0:2]), self.assertRaises(ValueError):
                    overlay.load_opt_in_mapping(*case)

    def test_rollback_receipt_restores_pre_phase2e_selection(self):
        rollback = overlay.read(overlay.OUT / "rollback-verification.json")
        self.assertTrue(rollback["disable_result"]["matches_pre_adoption"])
        self.assertEqual(15299, rollback["disable_result"]["count"])
        self.assertFalse(rollback["frozen_evidence_rewrite_required"])
        self.assertFalse(rollback["deletion_or_regeneration_of_phase1_through_phase2d_required"])


if __name__ == "__main__":
    unittest.main()
