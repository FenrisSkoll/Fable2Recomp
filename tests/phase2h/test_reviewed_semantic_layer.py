from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools/phase2h")]

import Fable2ReviewedSemanticConsumer as consumer
import Fable2ReviewedSemantics as layer


class ReviewedSemanticLayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pins = layer.read_json(layer.SOURCE_PINS_PATH)
        cls.decision = layer.read_json(layer.DECISION_PATH)
        cls.delta = layer.read_json(layer.DELTA_PATH)
        cls.view = layer.read_json(layer.VIEW_PATH)

    def test_01_exact_phase2g_starting_state(self) -> None:
        self.assertEqual(self.pins["starting_state"], layer.PHASE2G_STARTING_STATE)

    def test_02_exact_phase2g_commit_sequence(self) -> None:
        expected = [{"commit": commit, "subject": subject} for commit, subject in layer.PHASE2G_SEQUENCE]
        self.assertEqual(self.pins["phase2g_commit_sequence"], expected)

    def test_03_all_frozen_sources_are_identical(self) -> None:
        self.assertEqual(len(self.pins["sources"]), 501)
        for row in self.pins["sources"]:
            layer.check_identity(row)

    def test_04_phase2g_trust_roots(self) -> None:
        self.assertEqual(len(self.pins["phase2g_trust_roots"]), 9)
        for row in self.pins["phase2g_trust_roots"]:
            layer.check_identity(row)

    def test_05_phase2g_ignored_artifacts(self) -> None:
        self.assertEqual(self.pins["phase2g_ignored_artifacts"], 13)

    def test_06_exact_statement_identity(self) -> None:
        statement = self.decision["normalized_statement"]
        self.assertEqual(statement["bytes"], 477)
        self.assertEqual(statement["sha256"], layer.STATEMENT_SHA256)
        self.assertFalse(statement["terminal_newline"])
        self.assertEqual(statement, layer.statement_identity())

    def test_07_exact_decision_identity(self) -> None:
        self.assertEqual(self.decision["decision_record_id"], "P2G-OWNER-DECISION-001")
        self.assertEqual(self.decision["approver"], "FenrisSkoll")
        self.assertEqual(self.decision["decision_date"], "2026-09-13")
        self.assertEqual(self.decision["source"], "owner-supplied-chat-statement")

    def test_08_packet_c_is_only_approved_packet(self) -> None:
        self.assertEqual(self.decision["approval_scope"]["approved_packets"], ["C"])
        self.assertEqual(self.delta["approved_packets"], ["C"])
        self.assertEqual(self.view["approved_packets"], ["C"])

    def test_09_owner_mapping_unchanged(self) -> None:
        mapping = self.delta["contextual_role_adoption"]["owner_mapping"]
        self.assertEqual((mapping["donor"], mapping["target"]), ("0x825240E8", "0x82522C10"))
        self.assertEqual(mapping["disposition"], "unchanged")
        self.assertFalse(mapping["canonical"])
        self.assertEqual(self.view["mapping_changes"], [])

    def test_10_exact_contextual_role_is_noncanonical(self) -> None:
        role = self.delta["contextual_role_adoption"]
        self.assertEqual(role["contextual_role"], layer.CONTEXTUAL_ROLE)
        self.assertEqual(role["role_status"], layer.ROLE_STATUS)
        self.assertIsNone(role["canonical_function_name"])
        self.assertEqual(self.view["canonical_function_names"], [])

    def test_11_reservation_is_retained_everywhere(self) -> None:
        self.assertEqual(self.decision["approval_scope"]["reservation"], layer.RESERVATION)
        self.assertEqual(self.delta["contextual_role_adoption"]["reservation"], layer.RESERVATION)
        self.assertEqual(self.delta["preservation"]["reservation"], layer.RESERVATION)
        self.assertEqual(self.view["reservation"], layer.RESERVATION)

    def test_12_visitor_direction_unresolved(self) -> None:
        visitor = self.delta["contextual_role_adoption"]["visitor"]
        self.assertEqual((visitor["target_start"], visitor["target_end_exclusive"]),
                         ("0x825237C8", "0x82524454"))
        self.assertEqual(visitor["direction"], "unresolved")
        self.assertEqual(self.view["visitor_direction"], "unresolved")

    def test_13_handle_resolver_does_not_consume_reward_keys(self) -> None:
        edge = self.delta["corrected_semantic_edges"][0]
        self.assertEqual((edge["donor"], edge["target"]), ("0x821B2528", "0x821B24F8"))
        self.assertEqual(edge["reward_keys_consumed"], [])
        self.assertEqual(edge["parked_registers_read"], [])
        self.assertEqual(edge["parked_registers_not_read"], ["r5", "r6", "r7"])

    def test_14_scalar_helper_consumes_both_keys_in_r4(self) -> None:
        edge = self.delta["corrected_semantic_edges"][1]
        self.assertEqual((edge["donor"], edge["target"]), ("0x823C0588", "0x823BF820"))
        self.assertEqual([(field["key"], field["key_register"]) for field in edge["fields"]],
                         [("RewardRenown", "r4"), ("RewardMoney", "r4")])

    def test_15_scalar_stores_and_representation(self) -> None:
        fields = self.delta["corrected_semantic_edges"][1]["fields"]
        self.assertEqual([(row["store"]["offset"], row["store"]["bytes"]) for row in fields],
                         [("0x20", 4), ("0x24", 4)])
        self.assertTrue(all(row["signedness"] == "unresolved" for row in fields))
        self.assertTrue(all(row["numeric_representation"] == "unresolved" for row in fields))

    def test_16_boolean_route_is_retained(self) -> None:
        edge = self.delta["corrected_semantic_edges"][2]
        self.assertEqual((edge["donor"], edge["target"]), ("0x82310448", "0x82310290"))
        self.assertEqual(edge["field"], {
            "key": "AppearOnWorldMap",
            "store": {"base": "object", "offset": "0x4D", "bytes": 1},
            "representation": "normalized-0-or-1",
        })

    def test_17_set_objective_tag_is_rejected(self) -> None:
        alias = self.delta["rejected_alias"]
        self.assertEqual(alias["terminal"], "S-26C37A0D8DC5C81610D44E94")
        self.assertEqual(alias["text"], "SetObjectiveTag")
        self.assertEqual(alias["disposition"], "rejected-false-high-half-alias")
        self.assertFalse(alias["semantic_vote"])

    def test_18_false_alias_is_not_a_genuine_key(self) -> None:
        self.assertNotIn("SetObjectiveTag", self.delta["genuine_packet_c_keys"])
        self.assertEqual(self.delta["genuine_packet_c_keys"],
                         ["AppearOnWorldMap", "RewardMoney", "RewardRenown"])

    def test_19_packets_a_and_b_are_not_approved(self) -> None:
        self.assertEqual(self.decision["unapproved_packets"], ["A", "B"])
        self.assertEqual(self.delta["unapproved_packets"], ["A", "B"])
        self.assertEqual(self.view["unapproved_packets"], ["A", "B"])
        self.assertFalse(self.view["all_other_semantic_rows_approved"])

    def test_20_nonpropagation_flags(self) -> None:
        for document in (self.pins, self.decision, self.delta, self.view):
            self.assertFalse(document["canonical_adoption"])
            self.assertFalse(document["canonical_names_authorized"])
            self.assertFalse(document["mapping_mutation_allowed"])
            self.assertFalse(document["semantic_feedback_allowed"])

    def test_21_default_is_closed(self) -> None:
        default = layer.build_default_view()
        self.assertFalse(default["opt_in_applied"])
        self.assertEqual(default["approved_packets"], [])
        self.assertEqual(default["reviewed_roles"], [])
        self.assertEqual(default["semantic_corrections"], [])

    def exact_opt_in_args(self) -> argparse.Namespace:
        identities = {name: layer.identity(path) for name, path in consumer.EXACT_PATHS.items()}
        return argparse.Namespace(
            opt_in=layer.LAYER_VERSION,
            source_pins=consumer.EXACT_PATHS["source_pins"],
            source_pins_sha256=identities["source_pins"]["sha256"],
            decision=consumer.EXACT_PATHS["decision"],
            decision_sha256=identities["decision"]["sha256"],
            delta=consumer.EXACT_PATHS["delta"],
            delta_sha256=identities["delta"]["sha256"],
            view=consumer.EXACT_PATHS["view"],
            view_sha256=identities["view"]["sha256"],
        )

    def test_22_exact_explicit_opt_in(self) -> None:
        selected = consumer.select(self.exact_opt_in_args())
        self.assertTrue(selected["opt_in_applied"])
        self.assertEqual(selected["approved_packets"], ["C"])
        self.assertEqual(len(selected["reviewed_roles"]), 1)

    def test_23_missing_opt_in_parameter_refuses(self) -> None:
        arguments = self.exact_opt_in_args()
        arguments.decision_sha256 = None
        with self.assertRaisesRegex(ValueError, "Partial"):
            consumer.select(arguments)

    def test_24_wrong_version_refuses(self) -> None:
        arguments = self.exact_opt_in_args()
        arguments.opt_in = "phase2h-v2"
        with self.assertRaisesRegex(ValueError, "Wrong"):
            consumer.select(arguments)

    def test_25_wrong_hash_refuses(self) -> None:
        arguments = self.exact_opt_in_args()
        arguments.delta_sha256 = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            consumer.select(arguments)

    def test_26_wrong_path_refuses(self) -> None:
        arguments = self.exact_opt_in_args()
        arguments.view = "out/prototype-archaeology/phase2h/other.json"
        with self.assertRaisesRegex(ValueError, "exact repository-relative"):
            consumer.select(arguments)

    def test_27_altered_decision_refuses(self) -> None:
        altered = copy.deepcopy(self.decision)
        altered["approver"] = "NotFenrisSkoll"
        with self.assertRaisesRegex(ValueError, "owner decision"):
            layer.validate_owner_decision(altered, self.pins)

    def test_28_overbroad_decision_refuses(self) -> None:
        altered = copy.deepcopy(self.decision)
        altered["approval_scope"]["approved_packets"] = ["A", "B", "C"]
        with self.assertRaisesRegex(ValueError, "owner decision"):
            layer.validate_owner_decision(altered, self.pins)

    def test_29_altered_delta_refuses(self) -> None:
        altered = copy.deepcopy(self.delta)
        altered["contextual_role_adoption"]["reservation"] = "removed"
        with self.assertRaisesRegex(ValueError, "semantic delta"):
            layer.validate_semantic_delta(altered, self.pins, self.decision)

    def test_30_materialized_view_is_exact(self) -> None:
        layer.validate_materialized_view(self.view, self.pins, self.decision, self.delta)

    def test_31_overlay_and_default_counts_unchanged(self) -> None:
        state = self.pins["overlay_preservation"]
        self.assertEqual((state["overlay_pairs"], state["default_pairs"]), (15379, 15299))
        self.assertEqual((state["reservations"], state["suppressions"]), (66, 3))
        self.assertEqual((state["physics_excluded"], state["held_strong_excluded"],
                          state["probable_excluded"]), (2, 3, 715))

    def test_32_six_inherited_blockers_unchanged(self) -> None:
        phase2g = layer.read_json("docs/fable2-prototype-archaeology/phase2g/evidence/validation.json")
        self.assertEqual(len(self.pins["inherited_blockers"]), 6)
        self.assertEqual(self.pins["inherited_blockers"], phase2g["inherited_blockers"])

    def test_33_provenance_is_repository_relative_and_bound(self) -> None:
        for row in self.delta["input_identities"]:
            self.assertFalse(Path(row["path"]).is_absolute())
            self.assertNotIn("..", Path(row["path"]).parts)
            layer.check_identity(row)

    def test_34_documents_are_canonical_json(self) -> None:
        for path in (layer.SOURCE_PINS_PATH, layer.DECISION_PATH, layer.DELTA_PATH, layer.VIEW_PATH):
            document = layer.read_json(path)
            self.assertEqual((ROOT / path).read_bytes(), layer.payload(document))

    def test_35_sdk_state_is_preserved(self) -> None:
        layer.phase2d_review.verify_sdk({"sdk_start": self.pins["sdk"]})

    def test_36_no_prohibited_claims(self) -> None:
        self.assertEqual(len(self.delta["claims_not_made"]), 7)
        self.assertFalse(self.delta["preservation"]["production_propagation"])
        self.assertFalse(self.delta["preservation"]["mapping_records_mutated"])


if __name__ == "__main__":
    unittest.main()
