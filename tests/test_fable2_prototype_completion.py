"""Positive and adversarial controls for the Phase 2C completion policies."""
import copy
import json
import sys
import unittest
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import Fable2PrototypeCompletion as c
import Fable2PrototypeTrust as t
from test_fable2_prototype_semantics import make_image

class AblationTests(unittest.TestCase):
    @unittest.skipUnless((t.ROOT/c.OUT/'feature-ablation.json').exists(),'private ablation corpus unavailable')
    def test_production_ablation_populations_physics_and_hammer(self):
        doc=t.read(c.OUT/'feature-ablation.json')
        self.assertEqual(803,len(doc['proposal_packets']))
        self.assertEqual(99,len(doc['closed_records']))
        self.assertEqual(97,sum(bool(r['anchors']) for r in doc['closed_records']))
        packets={r['id']:r for r in doc['proposal_packets']}
        for pair in ('0x82631A30:0x82630C30','0x829506B0:0x82950A98'):
            self.assertEqual('candidate',packets[pair]['baseline']['grade'])
            self.assertFalse(packets[pair]['baseline']['semantic_transport'])
            self.assertEqual(0x3C,packets[pair]['donor']['size'])
            self.assertEqual(0x3C,packets[pair]['target']['size'])
        hammer=packets['0x8229B488:0x8229B1B8']
        self.assertEqual('reviewed-strong-proposal',hammer['baseline']['grade'])
        self.assertNotIn('HammerCombat',json.dumps(hammer['reference_evidence']))
        crossed=next(r for r in doc['closed_records'] if r['donor_start']=='0x82631A30')
        self.assertTrue(all(not r['semantic_transport'] for r in crossed['counterfactuals']))

    def proposal(self):
        return {'donor_start':'D','target_start':'T','independent_support':[{'class':'trusted-mapped-caller','donor':'seed','target':'target-seed'}],
                'contradictions':[],'boundary_valid':True,'shape_equal':True,'internal_region_support':[],
                'unproved_calls':[],'unproved_external_tail_transfers':[]}

    def evaluate(self,p,removed=(),candidates=None,reverse=None):
        return c.evaluate_proposal(p,removed,candidates or ['T'],reverse or ['D'],{'seed':'target-seed'})

    def test_ablation_removes_support_without_double_counting(self):
        p=self.proposal()
        self.assertTrue(self.evaluate(p)['semantic_transport'])
        self.assertFalse(self.evaluate(p,['caller'])['semantic_transport'])
        self.assertFalse(self.evaluate(p,['string-data-canonicalization'])['semantic_transport'])
        p['independent_support']=[]
        self.assertFalse(self.evaluate(p)['semantic_transport'])

    def test_removed_gate_recomputes_reciprocity_and_grade(self):
        self.assertEqual('ambiguous',self.evaluate(self.proposal(),candidates=['T','U'])['grade'])
        self.assertEqual('ambiguous',self.evaluate(self.proposal(),reverse=['D','E'])['grade'])
        p=self.proposal(); p['contradictions']=[{'class':'literal-conflict'}]
        for removed in c.CLASSES:
            self.assertEqual('rejected-proposal',self.evaluate(p,[removed])['grade'])

    def test_fixed_point_is_seeded_non_circular_and_order_independent(self):
        nodes=[{'donor':'B','target':'b','eligible':True,'support_options':[[('A','a')]]},
               {'donor':'C','target':'c','eligible':True,'support_options':[[('B','b')]]}]
        result=c.expand_dependencies({'A':'a'},nodes)
        self.assertEqual([1,2],[r['generation'] for r in result])
        self.assertEqual(result,c.expand_dependencies({'A':'a'},list(reversed(nodes))))
        self.assertEqual([],c.expand_dependencies({},nodes+[{'donor':'A','target':'a','eligible':True,'support_options':[[('C','c')]]}]))

    def test_crossed_targets_and_community_do_not_bootstrap(self):
        nodes=[{'donor':d,'target':'t','eligible':True,'support_options':[[('A','a')]]} for d in ('B','C')]
        self.assertEqual([],c.expand_dependencies({'A':'a'},nodes))
        nodes[0]['community_only']=True
        self.assertEqual([],c.expand_dependencies({'A':'a'},nodes[:1]))

class BoundaryPolicyTests(unittest.TestCase):
    def test_collective_fragment_coverage_preserves_missing_boundaries(self):
        self.assertEqual([],c.coverage_gaps(0,16,[(0,8),(8,16)]))
        self.assertEqual([[4,8]],c.coverage_gaps(0,16,[(0,4),(8,20)]))
        self.assertEqual([[0,16]],c.coverage_gaps(0,16,[(20,24)]))
        self.assertEqual([],c.coverage_gaps(0,16,[(-4,12),(4,16)]))

    def test_behavior_features_preserve_fields_and_known_cfg(self):
        a=make_image([(0x1000,[0x80640008,0x4E800020])],b'x\0')
        b=make_image([(0x1000,[0x8064000C,0x4E800020])],b'x\0')
        first=c.behavior_features(a,a.by_start[0x1000])
        self.assertEqual(8,first['field_accesses'][0]['displacement'])
        self.assertNotEqual(first,c.behavior_features(b,b.by_start[0x1000]))
        diamond=make_image([(0x1000,[0x41820008,0x38600000,0x4E800020])],b'x\0')
        cfg=c.behavior_features(diamond,diamond.by_start[0x1000])
        self.assertEqual([0,2],dict(cfg['dominators'])[2])
        self.assertEqual([0,2,3],dict(cfg['postdominators'])[0])

    def test_exact_region_extension_never_crosses_pdata_owner(self):
        left=make_image([(0x1000,[0x60000000]*16)],b'x\0')
        right=make_image([(0x1100,[0x60000000]*4),(0x1110,[0x60000000]*12)],b'x\0')
        self.assertIsNone(c.extend_match(left,right,left.by_start[0x1000],0x1000,0x1108))
        region=c.extend_match(left,right,left.by_start[0x1000],0x1000,0x1110)
        self.assertEqual('0x00001140',region['target_end_exclusive'])
        self.assertEqual(48,region['size'])

    def facts(self):
        return {'executable':True,'aligned':True,'exact_shared_regions':True,'coverage_complete':True,
                'entry_exit_compatible':True,'external_edges_correspond':True,'donor_owner_count':1,
                'target_owner_count':1,'equal_bounds':True}

    def test_all_transformation_classes_positive_and_adversarial(self):
        variants={'ordinary-function-pair':{},'split':{'target_owner_count':2},'merge':{'donor_owner_count':2},
                  'outline':{'equal_bounds':False,'call_boundary_change':'outlined-call'},
                  'inline':{'equal_bounds':False,'call_boundary_change':'inlined-call'}}
        for expected,change in variants.items():
            with self.subTest(expected=expected):
                f={**self.facts(),**change}
                self.assertEqual(expected,c.relation_class(f))
                for gate in ('coverage_complete','entry_exit_compatible','external_edges_correspond'):
                    self.assertEqual('shared-body',c.relation_class({**f,gate:False}))
                self.assertEqual('unresolved-boundary',c.relation_class({**f,'executable':False}))

    def test_thunk_tail_internal_and_unresolved_have_distinct_bounds(self):
        for whole,expected in ((True,'thunk'),(False,'tail')):
            f={**self.facts(),'single_nonlink_transfer':True,'target_has_owner':True,'whole_body_transfer':whole}
            self.assertEqual(expected,c.relation_class(f))
            self.assertNotEqual(expected,c.relation_class({**f,'single_nonlink_transfer':False}))
        f={**self.facts(),'internal_callable':True,'independent_pdata':False}
        self.assertEqual('internal-code-region',c.relation_class(f))
        self.assertNotEqual('internal-code-region',c.relation_class({**f,'independent_pdata':True}))
        self.assertEqual('unresolved-boundary',c.relation_class({**self.facts(),'exact_shared_regions':False}))

class TypedPolicyTests(unittest.TestCase):
    def test_vtable_positive_requires_complete_typed_chain(self):
        facts={'table_kind':'vtable','bounds_proven':True,'aligned':True,'executable_slots':True,
               'typed_descriptor_proven':True,'object_vptr_writer_proven':True,'slot_correspondence_proven':True}
        self.assertEqual('proposed-vtable',c.typed_disposition(facts))
        for gate in ('bounds_proven','aligned','executable_slots','typed_descriptor_proven','object_vptr_writer_proven','slot_correspondence_proven'):
            self.assertNotEqual('proposed-vtable',c.typed_disposition({**facts,gate:False}))
        for kind in ('jump-table','callback-array','import-table','mixed-data'):
            self.assertEqual('rejected-vtable-alternative',c.typed_disposition({**facts,'table_kind':kind}))
        for flag in ('interior','overlap'):
            self.assertEqual('unresolved-object-boundary',c.typed_disposition({**facts,flag:True}))

    def test_global_identity_needs_boundaries_roles_and_compatible_content(self):
        facts={'bounds_proven':True,'mapped_access_roles':True,'complete_content_equal':True}
        self.assertEqual('proposed-stable-global',c.typed_disposition(facts))
        self.assertEqual('rejected-incompatible-object-or-access',c.typed_disposition({**facts,'incompatible_content':True}))
        self.assertEqual('rejected-incompatible-object-or-access',c.typed_disposition({**facts,'incompatible_access':True}))
        self.assertEqual('unresolved-object-boundary',c.typed_disposition({**facts,'bounds_proven':False}))
        self.assertEqual('type-context-not-constructor',c.typed_disposition({'type_string_only':True}))

class ProvenanceTests(unittest.TestCase):
    def test_report_summary_and_actual_bytes_three_way(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root); path=root/'evidence.json'; path.write_bytes(b'{}\n')
            row={'path':'evidence.json','size':3,'sha256':t.digest(b'{}\n')}
            report=f"| `evidence.json` | 3 | `{row['sha256']}` |"
            c.report_bindings(root,report,[row])
            for bad in (report.replace('| 3 |','| 4 |'),report+'\n'+report,''):
                with self.assertRaises(ValueError): c.report_bindings(root,bad,[row])
            path.write_bytes(b'[]\n')
            with self.assertRaises(ValueError): c.report_bindings(root,report,[row])

    def test_two_hop_requires_each_trusted_non_oracular_hop(self):
        secondary={'s':{'target':'b','trusted':True}}
        primary={'b':{'target':'t','trusted':True}}
        self.assertEqual([('s','b'),('b','t')],c.two_hop('s',secondary,primary))
        for which in ('secondary','primary'):
            a,b=copy.deepcopy(secondary),copy.deepcopy(primary)
            (a['s'] if which=='secondary' else b['b'])['trusted']=False
            self.assertIsNone(c.two_hop('s',a,b))
        self.assertIsNone(c.two_hop('s',secondary,{}))

    def test_bound_artifacts_detect_mutations(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'evidence.json'
            path.write_bytes(b'{}\n')
            row={'size':3,'sha256':t.digest(b'{}\n')}
            c.check_identity(path,row)
            path.write_bytes(b'[]\n')
            with self.assertRaises(ValueError): c.check_identity(path,row)

    def test_forbidden_paths_are_not_allowlisted(self):
        for name in ('fable2_manifest.toml','generated/file.cpp','src/runtime.cpp','assets/image.xex','../rexglue-sdk-v0.10/src/a.cpp'):
            with self.assertRaises(ValueError): t.output(Path(name))
        self.assertTrue(t.output(c.OUT/'safe.json').is_relative_to(t.ROOT))

    @unittest.skipUnless((t.ROOT/c.OUT/'boundary-completion.json').exists(),'private boundary corpus unavailable')
    def test_unmatched_and_boundary_population_is_exhaustive(self):
        doc=t.read(c.OUT/'boundary-completion.json')
        self.assertEqual({'primary':713,'september':33,'comparators':2},doc['populations'])
        rows=[r for r in doc['records'] if r.get('population')=='unmatched']
        self.assertEqual({'0x826E3720','0x82BAD3B8'},{r['donor']['start'] for r in rows})
        self.assertEqual(748,len({r['id'] for r in doc['records']}))
        self.assertTrue(all(not r['semantic_transport'] for r in rows))

    def test_script_state_categories_do_not_prove_runtime_identity(self):
        for category in ('game','scripts_r','GUI','startup'):
            result=c.state_provenance(category)
            self.assertEqual(category,result['path_category'])
            self.assertFalse(result['runtime_state_proven'])
            self.assertTrue(c.state_provenance(category,{'native':'synthetic-proven-chain'})['runtime_state_proven'])

    def test_preservation_needs_first_party_presence_and_dependencies(self):
        self.assertEqual('dependency-linked-preservation-candidate',c.preservation_disposition(True,['native-dependency']))
        self.assertEqual('presence-only-dependencies-unresolved',c.preservation_disposition(True,[]))
        self.assertEqual('insufficient-first-party-presence',c.preservation_disposition(False,['Debug.ToggleFreeCam']))
        self.assertEqual('insufficient-first-party-presence',c.preservation_disposition(True,['Debug.ToggleFreeCam'],community_only=True))

    def test_historical_blob_is_readonly_and_hashed_by_existing_verifier(self):
        import Fable2IndirectTargets as p
        stream=c.GitBlobInput(b'historical metadata\n')
        self.assertEqual(t.digest(b'historical metadata\n'),p.sha256_file(stream))
        self.assertNotEqual(p.sha256_file(stream),p.sha256_file(c.GitBlobInput(b'changed\n')))
        with self.assertRaises(ValueError): stream.open('wb')

    def test_review_selection_positive_negative_and_deterministic(self):
        a=t.select_review({'empty':[],'present':['b','a','a']},1)
        self.assertEqual(a,t.select_review({'present':['a','b'],'empty':[]},1))
        self.assertEqual({'available':0,'selected':0},a[1]['empty'])
        self.assertEqual({'available':2,'selected':1},a[1]['present'])

if __name__=='__main__':
    unittest.main()
