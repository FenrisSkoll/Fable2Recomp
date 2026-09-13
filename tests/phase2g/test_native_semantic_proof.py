"""Phase 2G independence, frozen-state and confinement regressions."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/phase2g"))

import Fable2NativeProof as proof
import Fable2NativeProofSources as sources
import VerifyFable2NativeProof as verifier


class IndependenceGateTests(unittest.TestCase):
    def test_every_class_is_exactly_reachable(self):
        cases = {
            "mapping-consumed": {"mapping_consumed": True},
            "correlated-with-mapping": {"correlated": True},
            "independent-target-native": {"target_native": True},
            "independent-cross-build-behavior": {"cross_build": True},
            "context-only": {"context_only": True},
            "contradictory": {"contradictory": True},
            "unresolved": {},
        }
        for expected, arguments in cases.items():
            with self.subTest(expected=expected):
                self.assertEqual(expected, proof.classify_observation(**arguments))

    def test_observation_cannot_count_twice(self):
        with self.assertRaises(ValueError):
            proof.classify_observation(mapping_consumed=True, target_native=True)
        with self.assertRaises(ValueError):
            proof.classify_observation(correlated=True, contradictory=True)

    def test_consumed_and_correlated_never_vote(self):
        base = {"material": True, "compatible": True, "owned": True, "circular": False}
        for evidence_class in ("mapping-consumed", "correlated-with-mapping", "context-only",
                               "contradictory", "unresolved"):
            with self.subTest(evidence_class=evidence_class):
                self.assertFalse(proof.proof_eligible({**base, "independence_class": evidence_class}))

    def test_independent_vote_requires_every_safety_gate(self):
        base = {"independence_class": "independent-target-native", "material": True,
                "compatible": True, "owned": True, "circular": False}
        self.assertTrue(proof.proof_eligible(base))
        for key in ("material", "compatible", "owned"):
            with self.subTest(key=key):
                self.assertFalse(proof.proof_eligible({**base, key: False}))
        self.assertFalse(proof.proof_eligible({**base, "circular": True}))


class FrozenStateTests(unittest.TestCase):
    def test_exact_phase2f_start_every_field_matters(self):
        sources.exact_start(sources.START_STATE)
        for key in sources.START_STATE:
            bad = copy.deepcopy(sources.START_STATE)
            bad[key] = "wrong"
            with self.subTest(key=key), self.assertRaises(ValueError):
                sources.exact_start(bad)

    def test_three_packet_ids_and_addresses_fixed(self):
        self.assertEqual(["S-FCEF3DCAA6D1D5FB2EF8AB8F"], proof.PACKETS["A"]["terminal_ids"])
        self.assertEqual("0x8229B308:0x8229B038", proof.PACKETS["A"]["owner"])
        self.assertEqual("0x82406F98:0x82405868", proof.PACKETS["B"]["owner"])
        self.assertEqual("0x825240E8:0x82522C10", proof.PACKETS["C"]["owner"])
        self.assertEqual(3, len(proof.PACKETS["B"]["terminal_ids"]))
        self.assertEqual(4, len(proof.PACKETS["C"]["terminal_ids"]))

    def test_reservations_are_fixed(self):
        self.assertEqual("internal-code-region-dependent", proof.PACKETS["A"]["reservation"])
        self.assertEqual("single-independent-support-class", proof.PACKETS["B"]["reservation"])
        self.assertEqual("single-independent-support-class", proof.PACKETS["C"]["reservation"])

    def test_output_root_enforcement(self):
        for path in ("../outside.json", "C:/outside.json", "fable2_manifest.toml",
                     "generated/default/a.cpp", "tools/phase2f/new.json"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                sources.output(path)

    def test_overlay_tamper_refuses_without_fallback(self):
        validation = sources.read(sources.PHASE2F_DOC / "evidence/validation.json")
        selection = copy.deepcopy(validation["overlay_selection"])
        sources.verify_overlay(selection, validation)
        for key, value in (("selection", "wrong"), ("mapping_count", 15378),
                           ("fallback_permitted", True), ("overlay_enabled", False)):
            bad = copy.deepcopy(selection)
            bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                sources.verify_overlay(bad, validation)

    def test_every_ledger_pointer_and_record_hash_resolves(self):
        pins = sources.source_bindings()
        inputs = sources.Inputs(pins)
        ledger = proof.consumed_ledger(inputs)
        self.assertEqual(len(ledger["records"]), len({row["id"] for row in ledger["records"]}))
        for row in ledger["records"]:
            provenance = row["provenance"]
            document = json.loads((ROOT / provenance["path"]).read_bytes())
            node = document
            for token in provenance.get("json_pointer", "").split("/")[1:]:
                token = token.replace("~1", "/").replace("~0", "~")
                node = node[int(token)] if isinstance(node, list) else node[token]
            if "record_sha256" in provenance:
                self.assertEqual(provenance["record_sha256"], sources.digest(sources.payload(node)))

    def test_bad_pointer_and_record_hash_fail_closed(self):
        pins = sources.source_bindings()
        inputs = sources.Inputs(pins)
        path = "out/prototype-archaeology/phase2d/packets.json"
        with self.assertRaises(ValueError):
            inputs.ref(path, "/records/999999")
        with self.assertRaises(ValueError):
            inputs.ref(path, "/records/6", "0" * 64)


class HammerPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = json.loads((ROOT / "out/prototype-archaeology/phase2g/hammercombat/native-proof-packet.json").read_bytes())

    def test_boundaries_and_reservation_are_retained(self):
        packet = self.packet
        self.assertEqual("0x8229B308", packet["owner_mapping"]["donor"]["boundary"]["start"])
        self.assertEqual("0x8229B484", packet["owner_mapping"]["donor"]["boundary"]["end_exclusive"])
        self.assertEqual("0x8229B1B8", packet["reserved_callee"]["target"]["boundary"]["start"])
        self.assertEqual("internal-code-region-dependent",
                         packet["dispositions"]["reservation_reason"])
        for region in packet["comparator_regions"]:
            self.assertEqual("internal-code-region", region["kind"])
            self.assertFalse(region["independent_pdata_entry"])
            self.assertIsNone(region["containing_owner"])

    def test_hammer_text_never_becomes_function_name(self):
        packet = self.packet
        self.assertEqual("not-authorized", packet["dispositions"]["canonical_name"])
        self.assertTrue(packet["adversarial"]["callee_hammer_name_rejected"])
        self.assertTrue(packet["adversarial"]["owner_hammer_name_rejected"])

    def test_target_consumer_is_the_only_independent_vote(self):
        observations = self.packet["independence_observations"]
        eligible = [row for row in observations if row["proof_eligible"]]
        self.assertEqual(["A-tu1-byte-consumer-family"], [row["id"] for row in eligible])
        self.assertEqual(1, eligible[0]["detail"]["family_vote_count"])
        self.assertEqual("independently-corroborated-role",
                         self.packet["dispositions"]["primary"])

    def test_comparator_equivalence_does_not_promote_boundary(self):
        regions = self.packet["comparator_regions"]
        self.assertEqual(regions[0]["reachable_byte_sha256"],
                         regions[1]["reachable_byte_sha256"])
        self.assertEqual(21, regions[0]["instruction_count"])
        self.assertEqual(21, regions[1]["instruction_count"])


class PropertyPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oxygen = json.loads((ROOT / "out/prototype-archaeology/phase2g/oxygen/native-proof-packet.json").read_bytes())
        cls.world = json.loads((ROOT / "out/prototype-archaeology/phase2g/world-map-reward/native-proof-packet.json").read_bytes())
        cls.shared = json.loads((ROOT / "out/prototype-archaeology/phase2g/shared-helper/property-pattern.json").read_bytes())

    def test_oxygen_keys_offsets_widths_and_roles(self):
        rows = self.oxygen["field_role_table"]
        keyed = {row["key"]: row for row in rows if row["key"] is not None}
        self.assertEqual({"MaxOxygen", "OxygenConsumptionRate", "OxygenRecoveryRate"}, set(keyed))
        self.assertEqual([0x38, 0x3C, 0x40], [keyed[name]["offset"] for name in
                         ("MaxOxygen", "OxygenConsumptionRate", "OxygenRecoveryRate")])
        self.assertTrue(all(row["width"] == 4 for row in keyed.values()))
        self.assertEqual("mapping-consumed", keyed["MaxOxygen"]["evidence_class"])

    def test_oxygen_is_loading_not_gameplay(self):
        role = self.oxygen["role_classification"]
        self.assertTrue(role["keyed_load_or_deserialization_style"])
        self.assertFalse(role["property_registration"])
        self.assertFalse(role["outbound_serialization"])
        self.assertFalse(role["runtime_depletion_or_recovery"])
        self.assertEqual("behaviorally-corresponding-role-reserved",
                         self.oxygen["dispositions"]["primary"])

    def test_world_aliases_reconcile_three_keys_to_four_terminals(self):
        reconciliation = self.world["terminal_reconciliation"]
        self.assertEqual(4, reconciliation["population"])
        self.assertEqual(3, reconciliation["genuine_complete_key_contexts"])
        self.assertEqual(0, reconciliation["independent_votes_from_aliases"])
        self.assertEqual("S-26C37A0D8DC5C81610D44E94", reconciliation["spurious_terminal"])

    def test_world_fields_and_boolean_width(self):
        rows = {row["key"]: row for row in self.world["field_role_table"]}
        self.assertEqual((0x20, 4), (rows["RewardRenown"]["offset"], rows["RewardRenown"]["width"]))
        self.assertEqual((0x24, 4), (rows["RewardMoney"]["offset"], rows["RewardMoney"]["width"]))
        self.assertEqual((0x4D, 1), (rows["AppearOnWorldMap"]["offset"], rows["AppearOnWorldMap"]["width"]))
        self.assertIn("normalized Boolean", rows["AppearOnWorldMap"]["operation"])

    def test_world_independent_consumer_and_conflict_are_separate(self):
        eligible = [row["id"] for row in self.world["independence_observations"]
                    if row["proof_eligible"]]
        self.assertEqual(["C-second-tu1-field-visitors"], eligible)
        self.assertEqual("review-triggered", self.world["dispositions"]["mapping"])
        self.assertFalse(self.world["mapping_mutation_allowed"])
        self.assertEqual("retained", self.world["dispositions"]["reservation"])

    def test_property_pattern_does_not_transfer_votes_or_claim_gameplay(self):
        comparison = self.shared["comparison"]
        self.assertFalse(comparison["cross_packet_similarity_is_independent_vote"])
        self.assertTrue(comparison["not_identical_support_topology"])
        self.assertIn("not runtime gameplay", comparison["conclusion"])

    def test_same_strings_can_have_different_roles(self):
        control = self.oxygen["same_string_different_role_control"]
        self.assertFalse(control["approved_correspondence"])
        self.assertIn("field-visitor", control["result"])


class AdversarialPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.controls = json.loads((ROOT / "out/prototype-archaeology/phase2g/negative-controls/results.json").read_bytes())
        cls.scope = json.loads((ROOT / "out/prototype-archaeology/phase2g/expanded-function-scope.json").read_bytes())

    def test_invalid_string_objects_are_rejected(self):
        for name in ("prefix", "interior", "empty", "writable", "unterminated"):
            with self.subTest(name=name):
                self.assertEqual("rejected", self.controls["synthetic"][name]["disposition"])

    def test_role_and_caller_conflicts_quarantine(self):
        self.assertEqual("semantic-conflict-quarantined",
                         self.controls["synthetic"]["same-string-different-role"]["disposition"])
        self.assertEqual("semantic-conflict-quarantined",
                         self.controls["synthetic"]["compatible-body-incompatible-caller"]["disposition"])
        self.assertEqual("semantic-conflict-quarantined",
                         self.controls["synthetic"]["same-helper-incompatible-field"]["disposition"])
        self.assertEqual("rejected",
                         self.controls["synthetic"]["circular-owner-callee"]["disposition"])

    def test_real_collisions_and_exclusions_remain(self):
        collisions = {row["action_id"] for row in self.controls["real_collision_controls"]}
        self.assertEqual({"P2E:suppress:0x82631A30:0x82950A98",
                          "P2E:suppress:0x828EA448:0x82681198",
                          "P2E:suppress:0x83062950:0x83060C30"}, collisions)
        self.assertEqual(2, len(self.controls["exclusions"]["physics"]))
        self.assertEqual(3, len(self.controls["exclusions"]["held_strong"]))
        self.assertEqual(715, self.controls["exclusions"]["probable_count"])
        self.assertFalse(self.controls["mapping_mutation_on_conflict"])

    def test_every_expansion_is_bounded_and_reasoned(self):
        self.assertEqual(self.scope["counts"]["expansions"], len(self.scope["records"]))
        self.assertTrue(all(row["bounded"] and row["reason"] for row in self.scope["records"]))
        self.assertEqual({"A", "B", "C"}, {row["packet"] for row in self.scope["records"]})

    def test_field_labels_do_not_claim_complete_types(self):
        world = json.loads((ROOT / "out/prototype-archaeology/phase2g/world-map-reward/native-proof-packet.json").read_bytes())
        oxygen = json.loads((ROOT / "out/prototype-archaeology/phase2g/oxygen/native-proof-packet.json").read_bytes())
        self.assertIn("complete object/type identity", world["unresolved"])
        self.assertIn("complete object identity", oxygen["unresolved"])
        self.assertFalse(world["role_classification"]["runtime_reward_granting"])
        self.assertFalse(world["role_classification"]["runtime_map_marker_behavior"])


class FinalEnvelopeTests(unittest.TestCase):
    def test_summary_validation_report_and_actual_bytes_agree(self):
        summary = sources.read(sources.DOC / "evidence/packet-summary.json")
        validation = sources.read(sources.DOC / "evidence/validation.json")
        actual = verifier.output_json_identities()
        self.assertEqual(actual, summary["artifacts"])
        self.assertEqual(actual, validation["artifacts"])
        self.assertEqual(actual, verifier.parse_report_table())

    def test_every_artifact_path_is_relative_and_confined(self):
        for row in verifier.output_json_identities():
            with self.subTest(path=row["path"]):
                self.assertFalse(Path(row["path"]).is_absolute())
                self.assertTrue(row["path"].startswith("out/prototype-archaeology/phase2g/"))

    def test_review_selection_is_deterministic(self):
        selection = sources.read(sources.OUT / "review-selection.json")
        self.assertEqual(["A", "B", "C"], [row["packet"] for row in selection["records"]])
        self.assertEqual(1, selection["counts"]["human_review_candidates"])
        self.assertEqual("packet-id ascending; no randomized or score-based selection",
                         selection["ordering"])

    def test_prohibited_operations_and_feedback_remain_disabled(self):
        validation = sources.read(sources.DOC / "evidence/validation.json")
        self.assertTrue(all(value is False for value in validation["prohibited_operations"].values()))
        self.assertFalse(validation["canonical_adoption"])
        self.assertFalse(validation["semantic_feedback_allowed"])
        self.assertFalse(validation["mapping_mutation_allowed"])
        self.assertFalse(validation["canonical_names_authorized"])

    def test_git_delta_is_exactly_phase2g(self):
        names = set(verifier.git_delta())
        expected = set(verifier.DOCUMENTATION + verifier.IMPLEMENTATION + [
            "docs/fable2-prototype-archaeology/phase2g/evidence/validation.json"])
        self.assertEqual(expected, names)

    def test_six_blockers_and_historical_mismatch_remain_verbatim(self):
        validation = sources.read(sources.DOC / "evidence/validation.json")
        self.assertEqual(6, len(validation["inherited_blockers"]))
        serialized = json.dumps(validation["inherited_blockers"])
        self.assertIn("generated/default/fable2_recomp.136.cpp", serialized)
        self.assertIn("6053CC0EAC4636AA03AAA26581162B707C37E1B52BEE4C10F205D07C63EBDF59", serialized)
        frozen_report = (ROOT / sources.PHASE2F_DOC / "report.md").read_text(encoding="utf-8")
        self.assertIn("D25E664A98833BF9433413336AC92A7376102A67049C0FF35F1270E6BDEB44CB",
                      frozen_report)


if __name__ == "__main__":
    unittest.main()
