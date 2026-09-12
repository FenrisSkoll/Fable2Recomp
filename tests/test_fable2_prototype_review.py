"""Independent Phase 2D synthetic and private-production regressions."""
import copy
import inspect
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import Fable2PrototypeReview as r
import Fable2PrototypeReviewDecision as d
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


if __name__ == '__main__':
    unittest.main()
