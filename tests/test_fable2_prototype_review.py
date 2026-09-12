"""Independent Phase 2D synthetic and private-production regressions."""
import copy
import inspect
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import Fable2PrototypeReview as r
import Fable2PrototypeReviewDecision as d
import VerifyFable2PrototypeReview as verify
from test_fable2_prototype_semantics import make_image, instruction, call


class ReconstructionTests(unittest.TestCase):
    def image(self, text=b'DistinctAlpha\0', address=0x2000):
        high = ((address + 0x8000) >> 16) & 65535
        code = [instruction(15, 4, 0, high), instruction(14, 4, 4, address), call(0x1008, 0x1100), 0x4E800020]
        image = make_image([(0x1000, code), (0x1100, [0x4E800020])], text, data_start=address)
        for block in image.blocks:
            block.relative_path = 'synthetic/' + block.name
            block.sha256 = r.sha(block.data)
        return image

    def profile(self, image):
        return r.canonical(image, image.by_start[0x1000])

    def test_reference_relocation_and_signed_low_carry(self):
        a, b = self.profile(self.image()), self.profile(self.image(address=0x18000))
        self.assertEqual(a['canonical_sha256'], b['canonical_sha256'])
        self.assertNotEqual(a['raw_sha256'], b['raw_sha256'])
        self.assertTrue(b['references'][0]['signed_low'])
        self.assertEqual('0x00018000', b['references'][0]['constructed_address'])

    def test_shared_prefix_changed_full_identity(self):
        a = self.profile(self.image(b'CECPhysicsSimulationCharacterNavigator\0'))
        b = self.profile(self.image(b'CECPhysicsSimulationCharacterControlled\0'))
        self.assertNotEqual(a['canonical_sha256'], b['canonical_sha256'])

    def test_padding_empty_requires_byte_read(self):
        image = self.image(b'\0' * 30)
        self.assertFalse(r.text_object(image, 0x2000)['proven'])
        self.assertTrue(r.text_object(image, 0x2000, True)['proven'])
        self.assertIsNone(self.profile(image)['canonical_sha256'])

    def test_interior_identity_is_preserved(self):
        obj = r.text_object(self.image(b'AlphaSuffix\0'), 0x2005)
        self.assertEqual('interior-suffix', obj['relation'])
        self.assertEqual(5, obj['interior_offset'])

    def test_blind_unique_recovery(self):
        p = {'start': 'D', 'canonical_sha256': 'S'}
        result = r.blind_candidates(p, {'S': ['T']}, {'S': ['D']})
        self.assertEqual('T', result['selected_target'])

    def test_blind_tie_refuses_selection(self):
        p = {'start': 'D', 'canonical_sha256': 'S'}
        self.assertIsNone(r.blind_candidates(p, {'S': ['T', 'U']}, {'S': ['D']})['selected_target'])

    def test_blind_reverse_ambiguity_refuses_selection(self):
        p = {'start': 'D', 'canonical_sha256': 'S'}
        self.assertIsNone(r.blind_candidates(p, {'S': ['T']}, {'S': ['D', 'E']})['selected_target'])

    def test_concealed_target_grade_does_not_enter_matching(self):
        p = {'start': 'D', 'canonical_sha256': 'S'}
        expected = r.blind_candidates(p, {'S': ['T']}, {'S': ['D']})
        poisoned = {**p, 'grade': 'accepted', 'target_start': 'WRONG', 'semantic_label': 'Oracle'}
        self.assertEqual(expected, r.blind_candidates(poisoned, {'S': ['T']}, {'S': ['D']}))

    def test_same_shape_alternative_defeats_false_uniqueness(self):
        a, b = self.profile(self.image()), self.profile(self.image(address=0x2200))
        self.assertEqual(a['reference_erased_sha256'], b['reference_erased_sha256'])
        result = r.blind_candidates(a, {a['canonical_sha256']: ['T', 'U']}, {a['canonical_sha256']: [a['start']]})
        self.assertIsNone(result['selected_target'])

    def test_field_width_and_control_flow_conflicts(self):
        a = make_image([(0x1000, [0x80640008, 0x4E800020])], b'x\0')
        b = make_image([(0x1000, [0x88640008, 0x4E800020])], b'x\0')
        self.assertFalse(d.compatible_behavior(d.behavior(a, '0x00001000'), d.behavior(b, '0x00001000'), []))

    def test_pdata_entry_is_not_internal_region(self):
        result = d.internal_region(self.image(), '0x00001100')
        self.assertTrue(result['independent_pdata_entry'])
        self.assertTrue(result['problems'])


class DecisionPolicyTests(unittest.TestCase):
    def facts(self):
        return {'original_grade': 'reviewed-strong-proposal', 'mandatory_pass': True,
                'independent_classes': ['callee', 'caller'], 'contradictions': [],
                'unresolved': [], 'internal_region': False, 'common_helpers': False, 'common_only': False}

    def test_multiple_independent_classes(self):
        self.assertEqual(d.RECOMMEND, d.choose_disposition(self.facts()))

    def test_callee_only_has_reservation(self):
        self.assertEqual(d.RESERVE, d.choose_disposition({**self.facts(), 'independent_classes': ['callee']}))

    def test_common_helper_distinguished_from_distinctive(self):
        self.assertEqual(d.RESERVE, d.choose_disposition({**self.facts(), 'common_helpers': True}))
        self.assertEqual(d.RECOMMEND, d.choose_disposition(self.facts()))

    def test_low_entropy_and_common_helper_hold(self):
        self.assertEqual(d.HOLD, d.choose_disposition({**self.facts(), 'common_only': True}))

    def test_canonicalization_is_not_independent_support(self):
        self.assertEqual(d.HOLD, d.choose_disposition({**self.facts(), 'independent_classes': []}))

    def test_probable_missing_one_obligation_stays_held(self):
        self.assertEqual(d.HOLD, d.choose_disposition({**self.facts(), 'original_grade': 'reviewed-probable-proposal', 'unresolved': ['helper']}))

    def test_probable_requires_all_strong_gates(self):
        facts = {**self.facts(), 'original_grade': 'reviewed-probable-proposal'}
        self.assertEqual(d.RECOMMEND, d.choose_disposition(facts))
        self.assertEqual(d.HOLD, d.choose_disposition({**facts, 'mandatory_pass': False}))

    def test_physics_spelling_has_no_exception(self):
        facts = {**self.facts(), 'original_grade': 'candidate', 'independent_classes': [], 'spelling': 'CECPhysicsSimulationCharacterNavigator'}
        self.assertEqual(d.HOLD, d.choose_disposition(facts))

    def test_contradiction_rejects(self):
        self.assertEqual(d.REJECT, d.choose_disposition({**self.facts(), 'contradictions': ['literal-use-conflict']}))

    def test_boundary_disagreement_downgrades_strong(self):
        self.assertEqual(d.DOWNGRADE, d.choose_disposition({**self.facts(), 'mandatory_pass': False}))

    def test_internal_region_requires_reservation(self):
        self.assertEqual(d.RESERVE, d.choose_disposition({**self.facts(), 'internal_region': True}))

    def node(self, donor='D', target='T', generation=1, dependencies=None):
        return {'donor_start': donor, 'target_start': target, 'generation': generation,
                'dependencies': dependencies or [{'donor': 'S', 'target': 'U'}]}

    def test_global_injectivity_conflict(self):
        with self.assertRaisesRegex(ValueError, 'injectivity'):
            d.graph_valid({'S': 'U'}, [self.node(), self.node('E')])

    def test_suppressed_seed_barred(self):
        with self.assertRaisesRegex(ValueError, 'Suppressed'):
            d.graph_valid(dict(r.SUPPRESSIONS), [])

    def test_same_generation_and_circular_dependencies(self):
        with self.assertRaisesRegex(ValueError, 'generation'):
            d.graph_valid({'S': 'U'}, [self.node(), self.node('E', 'V', dependencies=[{'donor': 'D', 'target': 'T'}])])
        with self.assertRaisesRegex(ValueError, 'circular'):
            d.graph_valid({}, [self.node(dependencies=[{'donor': 'E', 'target': 'V'}]), self.node('E', 'V', dependencies=[{'donor': 'D', 'target': 'T'}])])

    def test_dangling_dependency(self):
        with self.assertRaisesRegex(ValueError, 'Dangling'):
            d.graph_valid({}, [self.node()])


class BindingTests(unittest.TestCase):
    def test_relative_evidence_paths_preserve_guest_source_text(self):
        verify.relative_evidence_paths({'path': 'out/prototype-archaeology/phase2d/packets.json',
                                        'text': 'E:\\dev\\Fable2\\SourceCode\\example.cpp'})
        for path in ('C:/Dev/private.json', '../escape.json', '/tmp/private.json'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                verify.relative_evidence_paths({'nested': [{'path': path}]})

    def test_report_validation_and_actual_bytes_three_way(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'data.json').write_bytes(b'{}\n')
            row = {'path': 'data.json', 'size': 3, 'sha256': r.sha(b'{}\n')}
            report = f"| `data.json` | 3 | `{row['sha256']}` |"
            with patch.object(r, 'ROOT', root):
                verify.three_way(report, [row])
                for bad in ('', report + '\n' + report, report.replace('| 3 |', '| 4 |')):
                    with self.assertRaises(ValueError):
                        verify.three_way(bad, [row])

    def test_forbidden_git_delta_and_canonical_propagation(self):
        for path in ('fable2_manifest.toml', 'generated/default/fable2_init.cpp', 'src/main.cpp', 'overrides/override.cpp',
                     'docs/fable2-native-renderer/candidate-hook-inventory.json', 'docs/fable2-prototype-archaeology/phase2c/report.md',
                     'assets/tu1/default.xex', 'tools/Fable2PrototypeTrust.py'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                verify.audit_paths([path])
        verify.audit_paths(['tools/Fable2PrototypeReview.py'])

    def test_hash_mutation_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'input').write_bytes(b'frozen')
            row = {'path': 'input', 'size': 6, 'sha256': r.sha(b'frozen')}
            r.check_identity(root, row)
            (root / 'input').write_bytes(b'change')
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                r.check_identity(root, row)

    def test_output_roots_and_relative_paths(self):
        for path in ('fable2_manifest.toml', 'generated/default/test.cpp', 'src/test.cpp', '../escape', str(r.ROOT / r.OUT / 'absolute.json')):
            with self.subTest(path=path), self.assertRaises(ValueError):
                r.output_path(path)
        self.assertTrue(r.output_path(r.OUT / 'test.json').is_relative_to(r.ROOT))

    def test_complete_original_populations(self):
        strong, probable = r.universe()
        self.assertEqual(86, len({(p['donor_start'], p['target_start']) for p in strong}))
        self.assertEqual(715, len({(p['donor_start'], p['target_start']) for p in probable}))

    def test_no_semantic_result_enters_extraction(self):
        source = inspect.getsource(r.canonical) + inspect.getsource(r.reconstruct)
        self.assertNotIn('semantic-final', source)
        self.assertNotIn('candidate-profiles.json', source)
        self.assertNotIn('semantic-xrefs.json', source)


class HumanAndSimulationTests(unittest.TestCase):
    def ledger(self):
        return {'records': [{'id': 'D:T', 'batch_id': 'B01', 'human_decision': 'pending', 'human_decision_evidence': None}],
                'proposal_set_sha256': r.sha(r.payload(['D:T']))}

    def test_pending_is_default_and_recommendation_is_not_approval(self):
        ledger = self.ledger()
        ledger['records'][0]['disposition'] = d.RECOMMEND
        d.validate_ledger(ledger)
        self.assertEqual('pending', ledger['records'][0]['human_decision'])

    def test_approval_requires_external_user_decision(self):
        ledger = self.ledger()
        ledger['records'][0]['human_decision'] = 'approved'
        with self.assertRaisesRegex(ValueError, 'pending'):
            d.validate_ledger(ledger)
        with self.assertRaisesRegex(ValueError, 'explicit human'):
            d.validate_ledger(ledger, require_pending=False)

    def test_each_explicit_approval_field_required(self):
        ledger = self.ledger()
        evidence = {'external_decision_id': 'synthetic-owner-input', 'approver': 'synthetic-test-owner',
                    'timestamp': '2000-01-01T00:00:00Z', 'proposal_set_sha256': ledger['proposal_set_sha256'], 'batch_id': 'B01'}
        ledger['records'][0].update(human_decision='approved', human_decision_evidence=evidence)
        external = {'synthetic-owner-input': {**evidence, 'decision': 'approved'}}
        d.validate_ledger(ledger, external, require_pending=False)
        for key in evidence:
            bad = copy.deepcopy(ledger)
            del bad['records'][0]['human_decision_evidence'][key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                d.validate_ledger(bad, external, require_pending=False)

    def test_approval_external_set_and_batch_must_match(self):
        ledger = self.ledger()
        ledger['proposal_set_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'set hash'):
            d.validate_ledger(ledger)

    def test_simulation_excludes_hold_reject_and_downgrade(self):
        closed = [{'donor_start': 'S', 'target_start': 'U'}]
        p = {'id': 'D:T', 'donor_start': 'D', 'target_start': 'T', 'generation': 1,
             'dependencies': [{'donor': 'S', 'target': 'U'}], 'disposition': d.HOLD}
        for status in (d.HOLD, d.REJECT, d.DOWNGRADE):
            p['disposition'] = status
            with self.subTest(status=status), self.assertRaises(ValueError):
                d.simulation(closed, [p], [p['id']])

    def test_all_three_suppressions_precede_every_simulated_view(self):
        closed = [{'donor_start': a, 'target_start': b} for a, b in r.SUPPRESSIONS.items()]
        closed.append({'donor_start': 'S', 'target_start': 'U'})
        view = d.simulation(closed, [], [])
        self.assertEqual([{'donor_start': 'S', 'target_start': 'U'}], view['records'])
        self.assertFalse(view['human_approval'])
        self.assertFalse(view['canonical_consumer_enabled'])


@unittest.skipUnless((r.ROOT / r.OUT / 'review-index.json').exists(), 'Phase 2D private review artifacts not yet generated')
class ProductionReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = r.read(r.OUT / 'review-index.json')['records']
        cls.packets = r.read(r.OUT / 'packets.json')['records']
        cls.summary = r.read(r.DOC / 'evidence/review-summary.json')

    def test_every_strong_reviewed_and_pending_exactly_once(self):
        original, _ = r.universe()
        expected = {(x['donor_start'], x['target_start']) for x in original}
        actual = [p for p in self.index if p['original_phase2c_grade'] == 'reviewed-strong-proposal']
        self.assertEqual(86, len(actual))
        self.assertEqual(expected, {(x['donor_start'], x['target_start']) for x in actual})
        self.assertTrue(all(x['human_decision'] == 'pending' for x in actual))

    def test_all_probable_have_terminal_blockers(self):
        rows = r.read(r.OUT / 'probable-blockers.json')['records']
        self.assertEqual(715, len({p['id'] for p in rows}))
        self.assertTrue(all(set(p['obligation_states']) == set(d.BLOCKERS) for p in rows))

    def test_callee_import_is_one_obligation(self):
        self.assertTrue(all(h['callee_import_obligation_count'] == 1 for p in self.packets for h in p['helpers']))

    def test_two_reference_identities_do_not_add_support_classes(self):
        strong = [p for p in self.packets if p['original_phase2c_grade'] == 'reviewed-strong-proposal']
        self.assertEqual(17, sum(p['reference_identity_count'] >= 2 for p in strong))
        self.assertTrue(all(set(p['independent_classes']) <= {'callee', 'caller', 'neighbourhood-order'} for p in strong))

    def test_support_strata_overlap_reconciles(self):
        strata = self.summary['strata']
        a, b, c = [set(strata[k]['ids']) for k in ('callee-only', 'richer-support', 'multi-reference')]
        self.assertEqual((66, 20, 17), (len(a), len(b), len(c)))
        self.assertFalse(a & b)
        self.assertEqual(17, len(a & c) + len(b & c))

    def test_hammer_regions_and_context_are_not_names(self):
        known = r.read(r.OUT / 'known-cases.json')
        self.assertIn('exclusion guard', known['hammer']['semantic_role'])
        self.assertIn('no function name assigned', known['hammer']['semantic_role'])
        self.assertTrue(all(p['kind'] == 'internal-code-region' and not p['independent_pdata_entry'] and p['owner'] is None for p in known['comparator_regions']))

    def test_three_suppressions_reproduced_from_use_proofs(self):
        rows = r.read(r.OUT / 'known-cases.json')['suppressions']
        self.assertEqual(dict(r.SUPPRESSIONS), {p['donor_start']: p['target_start'] for p in rows})
        self.assertTrue(all(p['conflicts'] for p in rows))

    def test_ledger_every_decision_pending(self):
        ledger = r.read(r.DOC / 'evidence/human-decision-ledger.json')
        d.validate_ledger(ledger)
        self.assertEqual(self.summary['pending_decisions'], len(ledger['records']))

    def test_batch_counts_membership_and_injectivity(self):
        batches = r.read(r.OUT / 'risk-strata-and-batches.json')['records']
        ids = [i for b in batches for i in b['mapping_ids']]
        self.assertEqual(len(ids), len(set(ids)))
        for b in batches:
            self.assertEqual(len(b['mapping_ids']), b['mapping_count'])
            self.assertEqual(r.sha(r.payload(sorted(b['mapping_ids']))), b['proposal_set_sha256'])

    def test_exact_simulation_arithmetic(self):
        for name, view in r.read(r.OUT / 'adoption-simulations.json')['views'].items():
            self.assertEqual(view['count'] - 15299, view['delta_from_phase2a'])
            self.assertEqual(view['count'] - 15382, view['delta_from_phase2c'])
            if 'records' in view:
                self.assertEqual(view['count'], len({p['donor_start'] for p in view['records']}))
                self.assertEqual(view['count'], len({p['target_start'] for p in view['records']}))

    def test_inherited_blockers_verbatim(self):
        original = r.read(r.C / 'evidence/validation.json')['remaining_blockers']
        self.assertEqual(original, self.summary['inherited_blockers'])

    def test_independent_ablation_matches_frozen_direct_policy(self):
        self.assertTrue(all(x['frozen_policy_agrees'] for p in self.packets for x in p['counterfactuals']))

    def test_full_same_size_cfg_competitors_include_selected_target(self):
        self.assertTrue(all(p['target_start'] in p['same_size_cfg_targets'] and p['donor_start'] in p['same_size_cfg_donors'] for p in self.packets))

    def test_reconstruction_is_hash_frozen(self):
        frozen = d.frozen_reconstruction()
        self.assertFalse(frozen['semantic_feedback_allowed'])

    def test_high_half_only_references_cannot_create_semantic_conflicts(self):
        for p in self.packets:
            for ref in p['donor_profile']['references'] + p['target_profile']['references']:
                self.assertEqual(2, len(ref['definition_offsets']))
            for conflict in p['contradictions']:
                self.assertNotIn(conflict.get('donor', {}).get('address'), ('0x820B0000', '0x820C0000', '0x820D0000'))


if __name__ == '__main__':
    unittest.main()
