"""Synthetic adversarial fixtures plus exhaustive private production checks."""
import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools/phase2f"))
import Fable2SemanticSources as s
import Fable2SemanticRoutes as r
import Fable2SemanticDomains as d
import Fable2SemanticAudit as a
import VerifyFable2SemanticAudit as verify


class EvidenceGateTests(unittest.TestCase):
    def facts(self, **changes):
        return dict(complete=True,equal=True,compatible_role=True,readonly=True,interior=False,
                    empty=False,canonicalized=False,common=False,independent_callee=True,**changes)

    def gate(self, **changes):
        facts = self.facts()
        facts.update(changes)
        return r.evidence_gate(**facts)

    def test_independent_target_role(self):
        self.assertEqual("independent",self.gate())

    def test_native_literal_wrong_role_quarantined(self):
        self.assertEqual("conflict",self.gate(compatible_role=False))

    def test_contradiction_precedes_donor_similarity(self):
        self.assertEqual("conflict",self.gate(contradiction=True,canonicalized=True))

    def test_canonicalization_cannot_vote_twice(self):
        self.assertEqual("mapping-consumed-or-low-entropy",self.gate(canonicalized=True))

    def test_common_helper_not_independent(self):
        self.assertEqual("mapping-consumed-or-low-entropy",self.gate(common=True))

    def test_interior_prefix_empty_and_writable_negatives(self):
        for changes in ({"interior":True},{"complete":False},{"empty":True},{"readonly":False},{"equal":False}):
            with self.subTest(changes=changes):
                self.assertEqual("insufficient",self.gate(**changes))

    def test_same_address_changed_content(self):
        # Address equality never enters the evidence gate; complete changed
        # content at the same role is explicitly contradictory.
        self.assertEqual("conflict",self.gate(equal=False,contradiction=True))

    def test_unmapped_callee_insufficient(self):
        self.assertEqual("insufficient",self.gate(independent_callee=False))

    def test_reference_text_never_function_name(self):
        self.assertEqual("sdk-compiler-vector",r.category("__vspltb(%s, %d)"))
        self.assertEqual("sdk-compiler-vector",r.category("__lvx(%s, 0)"))
        self.assertEqual("sdk-compiler-vector",r.category("XMConvertVectorIntToFloat(%s, %d)"))
        self.assertEqual("fable-game-specific",r.category("HammerCombat"))
        self.assertEqual("unknown",r.category("UniqueID"))

    def test_grade_precedence(self):
        facts=dict(owned=True,routed=True,suppressed=False,conflicts=False,independent=True,reserved=True,addition=True)
        self.assertEqual("target-corroborated",r.terminal_grade(**facts))
        facts["conflicts"]=True
        self.assertEqual("semantic-conflict-quarantined",r.terminal_grade(**facts))
        facts.update(routed=False,suppressed=True)
        self.assertEqual("suppression-blocked",r.terminal_grade(**facts))

    def test_reserved_and_unreserved_distinct(self):
        facts=dict(owned=True,routed=True,suppressed=False,conflicts=False,independent=False,reserved=True,addition=True)
        self.assertEqual("transported-context-reserved",r.terminal_grade(**facts))
        facts["reserved"]=False
        self.assertEqual("transported-context-unreserved",r.terminal_grade(**facts))

    def test_multi_route_primary_order_deterministic(self):
        base={"edges":[{"id":"a"}],"reservations":[],"independent":False,"evidence":None}
        proof={"edges":[{"id":"a"},{"id":"b"}],"reservations":["reserved"],"independent":True,"evidence":{"role":"independent"}}
        self.assertEqual(proof,r.primary_route([base,proof]))
        self.assertEqual(proof,r.primary_route([proof,base]))

    def test_joint_enabling_route_counts_terminal_once(self):
        before={"lane":"S","records":[{"terminal_id":"t","target_start":None,"grade":"mapping-blocked","used_additions":[],"reservations":[],"conflicts":[]}]}
        after={"lane":"O","records":[{"terminal_id":"t","target_start":"target","grade":"target-corroborated","used_additions":["B01:a","B02:b"],"reservations":["B02:b"],"conflicts":[]}]}
        change=a.comparison(before,after)
        self.assertEqual(1,change["counts"]["newly_routable"])
        self.assertEqual(1,change["counts"]["newly_corroborated"])

    def test_freecamera_every_obligation_required(self):
        facts={k:True for k in ("native_name","payload","callback","adapter","state","namespace","tu1_consumer","reachability")}
        self.assertTrue(d.obligations_callable(facts))
        for key in facts:
            self.assertFalse(d.obligations_callable({**facts,key:False}))

    def test_scripts_pairs_paths_not_runtime_ownership(self):
        self.assertFalse(d.runtime_script_proof({"structural_pair":True,"loose_script":True,"e3_path":True}))
        facts={k:True for k in ("native_binding","state_owner","namespace_owner","startup_consumer","retail_provenance")}
        self.assertTrue(d.runtime_script_proof(facts))
        for key in facts:
            self.assertFalse(d.runtime_script_proof({**facts,key:False}))

    def test_types_require_complete_ownership(self):
        self.assertFalse(d.typed_proof({"address_density":True,"type_string":True}))
        facts={k:True for k in ("bounds_proven","typed_descriptor_proven","object_vptr_writer_proven","slot_correspondence_proven")}
        self.assertTrue(d.typed_proof(facts))
        for key in facts:
            self.assertFalse(d.typed_proof({**facts,key:False}))

    def test_output_relative_and_physical_root_guards(self):
        for path in ("../outside.json","C:/outside.json","fable2_manifest.toml","generated/default/a.cpp","assets/runtime/test.json","tools/phase2e/new.json"):
            with self.subTest(path=path),self.assertRaises(ValueError):
                s.output(path)

    def test_starting_identity_each_field_matters(self):
        correct={"branch":"fable2-prototype-archaeology-phase2e","head":s.BASE,"tree":s.TREE,"index":[],"worktree":[],"subject":"Document Phase 2E opt-in rollback and handoff"}
        s.exact_start(correct)
        for key in correct:
            with self.subTest(key=key),self.assertRaises(ValueError):
                s.exact_start({**correct,key:"wrong"})

    def test_git_allowlist_blocks_frozen_and_runtime_paths(self):
        for path in ("tools/Fable2PrototypeTrust.py","src/main.cpp","fable2_manifest.toml","docs/fable2-prototype-archaeology/phase2e/report.md"):
            with self.subTest(path=path),self.assertRaises(ValueError):
                verify.git_audit([path])

    def test_path_audit_preserves_guest_text_not_absolute_evidence_paths(self):
        verify.path_audit({"text":"E:\\dev\\Fable2\\Source.cpp","path":"out/prototype-archaeology/phase2f/test.json"})
        for path in ("C:/outside.json","../outside.json","/outside.json"):
            with self.subTest(path=path),self.assertRaises(ValueError):
                verify.path_audit({"source":path})

    def test_terminal_subset_reconciliation_rejects_duplicates(self):
        row={"terminal_id":"t","grade":"mapping-blocked","target_start":None,"routes":[],"primary_route":None}
        lane={"records":[row],"counts":{"grades":{g:int(g=="mapping-blocked") for g in r.GRADES},"routable":0}}
        verify.lane_consistency(lane,{"t"})
        with self.assertRaises(ValueError):
            verify.lane_consistency({**lane,"records":[row,row]},{"t"})
        bad=copy.deepcopy(lane);bad["counts"]["grades"]["mapping-blocked"]=0
        with self.assertRaises(ValueError):
            verify.lane_consistency(bad,{"t"})


class ProductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pins=s.read(s.DOC/"evidence/source-pins.json")
        cls.effective,cls.selection=s.opt_in()
        cls.closed=s.read(s.overlay.PHASE2A_MAP_PATH)["records"]
        cls.maps=r.lane_maps(cls.effective,cls.closed)
        cls.lanes={name:s.read(s.OUT/("lane-"+name+".json")) for name in cls.maps}
        cls.full=cls.lanes["O"]["records"]
        cls.contribution=s.read(s.OUT/"mapping-contribution.json")["records"]

    def test_every_trust_root_actual_bytes(self):
        for name,(size,sha) in s.TRUST.items():
            s.check({"path":(s.E/name).as_posix(),"size":size,"sha256":sha})

    def test_overlay_opt_in_and_default_unchanged(self):
        self.assertEqual("phase2e-v1",self.selection["selection"])
        self.assertFalse(self.selection["fallback_permitted"])
        default=s.overlay.load_default_mapping()
        self.assertEqual(("closed-phase2a-default",15299),(default["selection"],default["mapping_count"]))

    def test_wrong_version_and_hash_refuse_without_fallback(self):
        args=["phase2e-v1",s.ROOT/s.E/"evidence/owner-decision.json",s.TRUST["evidence/owner-decision.json"][1],
              s.ROOT/s.E/"evidence/approved-overlay-delta.json",s.TRUST["evidence/approved-overlay-delta.json"][1],s.ROOT/s.EFFECTIVE,s.EFFECTIVE_HASH]
        for index,value in ((0,"wrong-version"),(2,"0"*64),(4,"0"*64),(6,"0"*64),(5,s.ROOT/s.OUT/"missing-overlay.json")):
            bad=list(args);bad[index]=value
            with self.subTest(index=index),self.assertRaises((ValueError,FileNotFoundError)):
                s.overlay.load_opt_in_mapping(*bad)

    def test_altered_effective_overlay_refuses(self):
        modified=copy.deepcopy(self.effective)
        modified["records"][0]["target_start"]="0x00000000"
        with self.assertRaises(ValueError):
            s.overlay.validate_effective_map(modified)

    def test_lane_pair_arithmetic(self):
        self.assertEqual(15296,len(self.maps["S"]))
        self.assertEqual(15379,len(self.maps["O"]))
        self.assertEqual([15313,15318,15378,15379],[len(self.maps["S+"+"+".join(r.BATCHES[:i+1])]) for i in range(4)])
        self.assertEqual([15362,15374,15319,15378],[len(self.maps["O-minus-"+b]) for b in r.BATCHES])

    def test_all_suppressions_held_physics_probable_absent(self):
        probable=s.read(s.D/"probable-blockers.json")["records"]
        self.assertEqual(715,len(probable))
        forbidden={x["id"] for x in probable}|{a+":"+b for a,b in r.HELD|r.PHYSICS|set(r.SUPPRESSIONS.items())}
        for lane,mapping in self.maps.items():
            if lane != "H-2A":
                self.assertFalse(forbidden & {x["id"] for x in mapping.values()})

    def test_corrected_vectors_present(self):
        for a,b in (("0x83060A80","0x83060C30"),("0x83062950","0x83060CD8")):
            self.assertEqual(b,self.maps["O"][a]["target_start"])

    def test_every_terminal_once_each_lane(self):
        expected={x["id"] for x in s.read(s.B/"semantic-index.json")["records"]}
        for name,lane in self.lanes.items():
            rows=lane["records"]
            self.assertEqual(51657,len(rows))
            self.assertEqual(expected,{x["terminal_id"] for x in rows})
            self.assertEqual(51657,sum(lane["counts"]["grades"].values()))

    def test_historical_exact_policy_counts(self):
        history=s.read(s.OUT/"historical-H.json")
        self.assertEqual(4,history["phase2b"]["counts"]["joined"])
        self.assertEqual(s.read(s.B/"semantic-index.json")["records"],history["phase2b"]["records"])
        for record,name in zip(history["phase2c"],(s.C/"semantic-v2.json",s.C/"completion/semantic-final.json")):
            self.assertEqual(s.read(name)["records"],record["records"])
            self.assertEqual(118,record["counts"]["newly_joined"])

    def test_three_removed_one_safe_reroute(self):
        audit=s.read(s.OUT/"suppression-impact.json")
        self.assertEqual({"removed_historical_associations":3,"safely_rerouted":1,"remaining_suppression_blocked":2},audit["counts"])
        self.assertTrue(all(x["S"]["grade"]=="suppression-blocked" for x in audit["records"]))

    def test_no_suppressed_dependency_fallback_or_september_route(self):
        for lane in ("S","O"):
            for terminal in self.lanes[lane]["records"]:
                for route in terminal["routes"]:
                    for edge in route["edges"]:
                        self.assertNotEqual(r.SUPPRESSIONS.get(edge["donor"],"absent"),edge["target"])
                        for dependency in edge["mapping_dependencies"]:
                            self.assertNotEqual(r.SUPPRESSIONS.get(dependency["donor"],"absent"),dependency["target"])
        september=s.read(s.OUT/"suppression-impact.json")["september"]
        self.assertEqual(9600,september["original_pairs"])
        self.assertEqual({9284},set(september["routed_counts"].values()))

    def test_all_83_productive_or_dormant_present(self):
        expected={x["id"] for x in self.maps["O"].values() if x["generation"]}
        self.assertEqual(expected,{x["mapping_id"] for x in self.contribution})
        self.assertEqual(83,len(self.contribution))
        self.assertTrue(all(isinstance(x["productive"],bool) for x in self.contribution))

    def test_all_66_reservations_propagate_exactly(self):
        reserved={x["id"]:x["reservations"] for x in self.maps["O"].values() if x["reservations"]}
        self.assertEqual(66,len(reserved))
        observed=set()
        for terminal in self.full:
            for route in terminal["routes"]:
                self.assertEqual(r.reservations(route["edges"]),route["reservations"])
                for edge in route["edges"]:
                    if edge["id"] in reserved:
                        self.assertEqual(reserved[edge["id"]],edge["reservations"])
                        observed.add(edge["id"])
        self.assertEqual(set(reserved),observed)

    def test_new_route_target_evidence_not_double_counted(self):
        delta=s.read(s.OUT/"lane-delta.json")
        self.assertEqual(115,delta["counts"]["newly_routable"])
        self.assertEqual(1,delta["counts"]["newly_corroborated"])
        self.assertFalse(any(x["newly_routable"] and x["newly_corroborated"] for x in delta["records"]))
        for terminal in self.full:
            for route in terminal["routes"]:
                if route["independent"]:
                    self.assertFalse(route["evidence"]["canonicalization_consumed"])

    def test_hammer_exclusion_guard_not_internal_function(self):
        hammer=next(x for x in self.full if x["terminal_id"]=="S-FCEF3DCAA6D1D5FB2EF8AB8F")
        self.assertEqual("target-corroborated",hammer["grade"])
        self.assertEqual(["internal-code-region-dependent"],hammer["reservations"][0]["reservations"])
        self.assertIsNone(hammer["canonical_function_name"])
        self.assertNotIn("0x8226DB80",self.maps["O"])

    def test_b05_proof_not_new_owner_route(self):
        batches=s.read(s.OUT/"batch-attribution.json")
        b05=next(x for x in batches["cumulative"] if x["batch"]=="B05")
        self.assertEqual(0,b05["counts"]["newly_routable"])
        self.assertEqual(1,b05["counts"]["newly_corroborated"])

    def test_native_registration_and_freecamera_still_blocked(self):
        reg=s.read(s.OUT/"registration-debug-freecamera.json")
        self.assertEqual((2662,206,2647),(reg["counts"]["calls"],reg["counts"]["shapes"],reg["counts"]["complete_candidates"]))
        self.assertEqual(0,reg["counts"]["changed_calls"])
        self.assertFalse(reg["freecamera"]["tu1_callable"])
        self.assertFalse(d.obligations_callable(reg["freecamera"]["facts"]))

    def test_all_scripts_and_e3_presence_reconciled(self):
        doc=s.read(s.OUT/"script-preservation.json")
        self.assertEqual((160,108,52,54,200,21),tuple(doc["counts"][k] for k in ("scripts","parsed","inventory_only","pairs","preservation","e3")))
        self.assertTrue(all(not x["runnable_recovery_proven"] for x in doc["preservation"]+doc["e3_presence"]))
        self.assertTrue(all(not x["retail_startup_proven"] for x in doc["scripts"]+doc["script_pairs"]))

    def test_types_globals_and_boundaries_not_promoted(self):
        doc=s.read(s.OUT/"type-global-boundary.json")
        self.assertEqual((425,4939,2479,748),tuple(doc["counts"][k] for k in ("types","pointer_runs","globals","boundaries")))
        self.assertEqual(0,doc["counts"]["proven_vtables"])
        self.assertEqual(0,doc["counts"]["proven_complete_objects"])

    def test_project_intersections_are_not_votes(self):
        doc=s.read(s.OUT/"project-intersections.json")
        self.assertEqual(83,len(doc["records"]))
        self.assertTrue(all(not x["independent_semantic_corroboration"] for x in doc["records"]))

    def test_no_canonical_names_in_any_terminal(self):
        self.assertTrue(all(x["canonical_function_name"] is None for x in self.full))

    def test_six_blockers_pending_and_scoped_approval_unchanged(self):
        self.assertEqual(s.read(s.E/"evidence/validation.json")["inherited_blockers"],self.pins["inherited_blockers"])
        ledger=s.read("docs/fable2-prototype-archaeology/phase2d/evidence/human-decision-ledger.json")
        self.assertEqual(91,len(ledger["records"]))
        self.assertTrue(all(x["human_decision"]=="pending" for x in ledger["records"]))
        self.assertFalse(self.effective["canonical_adoption"])

    def test_sdk_exact_state_and_fifteen_hashes(self):
        s.review.verify_sdk({"sdk_start":self.pins["sdk"]})

    def test_stable_primary_and_serialization(self):
        for terminal in self.full:
            primary=r.primary_route(list(reversed(terminal["routes"])))
            self.assertEqual(primary,terminal["routes"][terminal["primary_route"]] if terminal["primary_route"] is not None else None)
        self.assertEqual(s.payload(self.selection),s.payload(copy.deepcopy(self.selection)))


if __name__ == "__main__":
    unittest.main()
