"""Phase 2C policy fixtures use synthetic bytes; no game execution."""
import copy
import struct
import sys
import unittest
import tempfile
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import Fable2PrototypeTrust as trust
from test_fable2_prototype_semantics import make_image, instruction, call


def string_image(value, address=0x2000, words=None):
    return make_image([(0x1000, words or [0x4E800020])], value, data_start=address)


class CallbackConstructionTests(unittest.TestCase):
    def fixture(self):
        # Synthetic destinations; only the documented register-flow shape.
        words = [int(x,16) for x in '''7D8802A6 48000001 9421FF80 7C7E1B78
            7C9F2378 7CBD2B78 817E0000 2B0B0000 419A006C 838B0000
            3880D8F0 80AB0004 7F83E378 48000001 38800004 7F83E378
            48000001 7C6B1B78 3D401234 38A00001 388A8000 7F83E378
            93AB0000 48000001 7FE5FB78 7F84E378 7FC3F378 48000001
            7FE5FB78 3880FFFE 7F83E378 48000001 817C0008 392BFFF8
            913C0008 38210080 48000000'''.split()]
        return words

    def test_payload_shape_exposes_unproven_callees(self):
        shape = trust.callback_payload_shape(self.fixture(),0x1000)
        self.assertEqual('0x12338000',shape['adapter'])
        self.assertEqual(4,shape['payload_size'])
        self.assertIn('state-and-namespace',shape['unverified_obligations'])

    def test_adversarial_payload_width_source_and_name_flow(self):
        for index,word in ((14,0x38800008),(22,0x9BAB0000),(22,0x938B0000),
                           (28,0x7FC5F378),(19,0x38A00002),(23,0x48000000),
                           (8,0x419A0068),(20,0x388B8000)):
            with self.subTest(index=index,word=word):
                words=self.fixture()
                words[index]=word
                self.assertIsNone(trust.callback_payload_shape(words,0x1000))

    def test_adjacency_and_truncated_layout_do_not_match(self):
        self.assertIsNone(trust.callback_payload_shape([0x2000,0x1000]*19,0x1000))
        self.assertIsNone(trust.callback_payload_shape(self.fixture()[:-1],0x1000))


@unittest.skipUnless((trust.ROOT/trust.OUT/'mapping-freeze.json').exists(), 'private Phase 2C evidence unavailable')
class ProductionEvidenceTests(unittest.TestCase):
    def test_comparators_are_equal_reachable_unowned_regions(self):
        regions=trust.read(trust.OUT/'known-cases.json')['comparator_regions']
        self.assertEqual(2,len(regions))
        self.assertEqual(1,len({r['reachable_byte_sha256'] for r in regions}))
        for r in regions:
            self.assertEqual('internal-code-region',r['kind'])
            self.assertEqual(21,r['instruction_count'])
            self.assertEqual(0x54,int(r['end_exclusive'],16)-int(r['start'],16))
            self.assertIsNone(r['containing_owner'])
            self.assertFalse(r['independent_pdata_entry'])
            self.assertEqual([],r['blockers'])

    def test_hammer_callee_diff_is_only_empty_pointer_and_comparator_call(self):
        functions=trust.read(trust.OUT/'known-cases.json')['functions']
        selected={r['boundary']['start']:r for r in functions}
        a,b=(selected[x] for x in ('0x8229B488','0x8229B1B8'))
        wa=[line.split()[1] for line in a['disassembly']]
        wb=[line.split()[1] for line in b['disassembly']]
        self.assertEqual([0x20,0x54],[i*4 for i,(x,y) in enumerate(zip(wa,wb)) if x!=y])
        self.assertEqual(31,len(wa))
        self.assertEqual(31,len(wb))

    def test_closed_collision_is_suppressed_in_effective_consumer_view(self):
        view=trust.read(trust.OUT/'effective-map.json')
        crossed=('0x82631A30','0x82950A98')
        self.assertNotIn(crossed,{(r['donor_start'],r['target_start']) for r in view['records']})
        self.assertIn(crossed,{(r['donor_start'],r['target_start']) for r in view['suppressions']})
        self.assertFalse(view['canonical_consumer_enabled'])

    def test_secondary_pair_level_result_matches_closed_aggregate(self):
        secondary=trust.read(trust.OUT/'september-pairs.json')
        closed=trust.read(trust.semantic.P2/'prototype-correspondence-validation.json')['september_robustness_study']
        self.assertEqual(closed,secondary['original_aggregate'])
        self.assertEqual(9600,len(secondary['original_pairs']))
        self.assertEqual(45707,len(secondary['original_terminals']))
        for field in ('donor_start','target_start'):
            self.assertEqual(9600,len({r[field] for r in secondary['original_pairs']}))

    def test_frozen_mapping_files_remain_byte_bound(self):
        frozen=trust.verified_freeze()
        self.assertFalse(frozen['semantic_feedback_allowed'])


class StringIdentityTests(unittest.TestCase):
    def compare(self, a, b, left=0x2000, right=0x2000):
        return (trust.object_at(string_image(a, left), left),
                trust.object_at(string_image(b, right), right))

    def test_production_physics_spellings_share_prefix_but_not_identity(self):
        a,b = self.compare(b'CECPhysicsSimulationCharacterNavigator\0', b'CECPhysicsSimulationCharacterControlled\0')
        self.assertEqual(a['window_sha256'], b['window_sha256'])
        self.assertNotEqual(trust.identity_token(a), trust.identity_token(b))
        self.assertEqual('suppressed-semantic-collision', trust.trust_disposition(False, False, False, [0], True))

    def test_synthetic_shared_sixteen_byte_prefix(self):
        a,b = self.compare(b'1234567890abcdefLeft\0', b'1234567890abcdefRight\0')
        self.assertEqual(a['window_sha256'], b['window_sha256'])
        self.assertNotEqual(trust.identity_token(a), trust.identity_token(b))

    def test_same_virtual_address_different_content(self):
        a,b = self.compare(b'FirstValue\0', b'SecondValue\0')
        self.assertEqual(a['address'], b['address'])
        self.assertNotEqual(trust.identity_token(a), trust.identity_token(b))

    def test_relocated_complete_string(self):
        a,b = self.compare(b'ExactLiteral\0', b'ExactLiteral\0', right=0x3000)
        self.assertNotEqual(a['address'], b['address'])
        self.assertEqual(trust.identity_token(a), trust.identity_token(b))

    def test_interior_and_suffix_are_explicit(self):
        image = string_image(b'LongLiteralSuffix\0')
        obj = trust.object_at(image, 0x200B)
        self.assertEqual('interior-suffix', obj['pointer_relation'])
        self.assertEqual('LongLiteralSuffix', obj['full_text'])
        self.assertEqual(11, obj['pointer_byte_offset'])

    def test_utf16_boundaries_and_terminator(self):
        obj = trust.object_at(string_image('FullString\0'.encode('utf-16le')), 0x2000)
        self.assertEqual('utf-16le', obj['encoding'])
        self.assertEqual(2, obj['terminator_bytes'])
        self.assertEqual(20, obj['length_bytes'])

    def test_ascii_terminator_required(self):
        obj = trust.object_at(string_image(b'Unterminated'), 0x2000)
        self.assertEqual('bounded-byte-window', obj['kind'])

    def test_common_zero_is_not_independent_support(self):
        a,b = self.compare(bytes(32), bytes(32), right=0x3000)
        self.assertIsNone(trust.identity_token(a))
        self.assertIsNone(trust.identity_token(b))
        self.assertEqual('review-required-partial-anchor', trust.trust_disposition(False, False, False, [], True))

    def test_empty_byte_string_requires_explicit_use_context(self):
        image = string_image(bytes(32))
        obj = trust.object_at(image, 0x2000, allow_empty=True)
        self.assertEqual('', obj['full_text'])
        self.assertEqual('empty-at-terminator', obj['pointer_relation'])

    def test_binary_header_has_no_invented_boundary(self):
        obj = trust.object_at(string_image(b'\x01\x02\x03\x04' * 8), 0x2000)
        self.assertFalse(obj['boundary_proven'])
        self.assertIsNone(trust.identity_token(obj))

    def test_partial_data_only_loses_trust(self):
        self.assertEqual('review-required-partial-anchor', trust.trust_disposition(False, False, False, [], True))

    def test_independent_evidence_survives_anchor_removal(self):
        self.assertEqual('retained-independent-evidence', trust.trust_disposition(False, True, False, [], True))

    def test_literal_contradiction_overrides_exact_bytes(self):
        self.assertEqual('suppressed-semantic-collision', trust.trust_disposition(True, True, False, [0], True))


class CanonicalizationTests(unittest.TestCase):
    def fixture(self, address=0x8200F000, constant=7):
        high = (address + 0x8000) >> 16
        words = [instruction(15, 4, 0, high), instruction(14, 4, 4, address & 65535),
                 instruction(14, 5, 0, constant), call(0x100C, 0x1100), 0x4E800020]
        image = string_image(b'DistinctLiteral\0', address, words)
        refs = trust.function_refs(image, image.functions[0])
        return image, refs

    def test_signed_low_carry_and_only_proven_immediates(self):
        image, refs = self.fixture()
        result = trust.canonicalize(image, image.functions[0], refs)
        self.assertEqual([0, 4], [r['offset'] for r in result['changed_instructions']])
        self.assertEqual('0x8200F000', refs[0]['anchor_address'])

    def test_relocation_canonicalizes_but_unrelated_constant_does_not(self):
        a, ar = self.fixture()
        b, br = self.fixture(0x8201E000)
        c, cr = self.fixture(0x8201E000, 8)
        ca = trust.canonicalize(a, a.functions[0], ar)
        cb = trust.canonicalize(b, b.functions[0], br)
        cc = trust.canonicalize(c, c.functions[0], cr)
        self.assertEqual(ca['fingerprint'], cb['fingerprint'])
        self.assertNotEqual(ca['fingerprint'], cc['fingerprint'])

    def test_literal_evidence_does_not_create_topology(self):
        d = {'start': '0x00001000', 'direct_calls': []}
        t = {'start': '0x00002000', 'direct_calls': []}
        support, conflicts, calls = trust.independent_support(d, t, {}, {}, {})
        self.assertEqual(([], [], []), (support, conflicts, calls))

    def test_internal_reachable_region_is_not_function(self):
        image = make_image([(0x1000, [0x60000000, 0x38600000, 0x4E800020])])
        region = trust.code_region(image, 0x1004)
        self.assertEqual('internal-code-region', region['kind'])
        self.assertFalse(region['independent_pdata_entry'])
        self.assertEqual('0x00001000', region['containing_owner']['start'])

    def test_output_roots_fail_closed(self):
        for path in ('fable2_manifest.toml', '../outside.json', 'generated/code.cpp'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                trust.output(path)

    def test_no_clock_or_head_in_analytical_envelope(self):
        a = trust.envelope('audit', records=[])
        self.assertEqual(trust.payload(a), trust.payload(copy.deepcopy(a)))
        self.assertFalse(a['canonical_adoption'])
        self.assertNotIn('timestamp', a)


class OverlayTests(unittest.TestCase):
    def pair(self):
        return {'donor_start':'0x00001000','target_start':'0x00002000'}

    def audit(self, disposition='retained-independent-evidence'):
        return {'original_record_index':0,'disposition':disposition}

    def proposal(self, donor='0x00001100', target='0x00002100', generation=1, dependency='0x00001000', dep_target='0x00002000'):
        return {'donor_start':donor,'target_start':target,'grade':'reviewed-strong-proposal','generation':generation,
                'reciprocal_unique':True,'boundary_valid':True,'shape_equal':True,'contradictions':[],
                'unproved_calls':[],'unproved_external_tail_transfers':[],
                'canonicalized_reference_evidence':{'canonicalized_references':[{'identity':'synthetic-complete-string'}]},
                'independent_support':[{'class':'trusted-mapped-callee','donor':dependency,'target':dep_target}]}

    def test_suppression_takes_precedence(self):
        result = trust.effective_view([self.pair()],[self.audit('suppressed-semantic-collision')],[])
        self.assertEqual([],result['records'])
        self.assertEqual(-1,result['counts']['delta'])

    def test_duplicate_target_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate effective target'):
            trust.effective_view([self.pair()],[self.audit()],[self.proposal(target='0x00002000')])

    def test_duplicate_donor_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate effective donor'):
            trust.effective_view([self.pair()],[self.audit()],[self.proposal(donor='0x00001000')])

    def test_string_cannot_double_count_as_independent_support(self):
        proposal = self.proposal()
        proposal['independent_support'] = []
        with self.assertRaisesRegex(ValueError,'double-counted'):
            trust.effective_view([self.pair()],[self.audit()],[proposal])

    def test_circular_same_generation_cannot_seed_itself(self):
        a = self.proposal(dependency='0x00001200',dep_target='0x00002200')
        b = self.proposal(donor='0x00001200',target='0x00002200',dependency='0x00001100',dep_target='0x00002100')
        with self.assertRaisesRegex(ValueError,'circular'):
            trust.effective_view([self.pair()],[self.audit()],[a,b])

    def test_multiple_generations_have_external_seed_and_stable_result(self):
        a = self.proposal()
        b = self.proposal(donor='0x00001200',target='0x00002200',generation=2,dependency='0x00001100',dep_target='0x00002100')
        result = trust.effective_view([self.pair()],[self.audit()],[a,b])
        self.assertEqual(3,result['counts']['effective'])
        reversed_result = trust.effective_view([self.pair()],[self.audit()],[b,a])
        self.assertEqual(result['records'],reversed_result['records'])

    def test_probable_proposals_are_excluded(self):
        proposal = self.proposal()
        proposal['grade'] = 'reviewed-probable-proposal'
        self.assertEqual(1,trust.effective_view([self.pair()],[self.audit()],[proposal])['counts']['effective'])

    def test_unsupported_community_class_cannot_create_mapping(self):
        proposal = self.proposal()
        proposal['independent_support'][0]['class'] = 'community-only'
        with self.assertRaisesRegex(ValueError,'unsupported independent'):
            trust.effective_view([self.pair()],[self.audit()],[proposal])

    def test_unproved_tail_blocks_strong_effective_inclusion(self):
        proposal = self.proposal()
        proposal['unproved_external_tail_transfers'] = [{'offset':4,'destination':'0x00003000'}]
        with self.assertRaisesRegex(ValueError,'unresolved behavior'):
            trust.effective_view([self.pair()],[self.audit()],[proposal])


class LuaAndFreezeTests(unittest.TestCase):
    def chunk(self, debug):
        integer = lambda n: struct.pack('<I',n)
        source = integer(5) + b'test\0' if debug else integer(0)
        return b'\x1bLua\x51\x00\x01\x04\x04\x04\x08\x00' + source + integer(0)*2 + bytes([0,0,2,2]) + integer(1) + integer(0x80001E) + integer(0)*2 + (integer(1)+integer(1) if debug else integer(0)) + integer(0)*2

    def test_stripped_debug_information_preserves_executable_pair(self):
        a,b = trust.LuaChunk(self.chunk(True)).parse(), trust.LuaChunk(self.chunk(False)).parse()
        self.assertEqual(a['executable_structure_sha256'],b['executable_structure_sha256'])
        self.assertEqual(1,a['prototypes'][0]['line_info_count'])
        self.assertEqual(0,b['prototypes'][0]['line_info_count'])

    def test_lua_invalid_or_unrelated_container_fails_closed(self):
        for data in (b'BankContainer', self.chunk(True)[:-1], self.chunk(True)+b'garbage'):
            with self.subTest(data=data[:12]), self.assertRaises(ValueError):
                trust.LuaChunk(data).parse()

    def test_frozen_hash_prevents_semantic_feedback(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(trust,'ROOT',Path(directory)):
            artifact = trust.ROOT/trust.OUT/'audit.json'
            artifact.parent.mkdir(parents=True)
            artifact.write_bytes(b'unchanged')
            trust.write(trust.OUT/'mapping-freeze.json',trust.envelope('mapping-freeze',artifacts=[{'path':(trust.OUT/'audit.json').as_posix(),'size':9,'sha256':trust.digest(b'unchanged')}]))
            trust.verified_freeze()
            artifact.write_bytes(b'new-value')
            with self.assertRaisesRegex(ValueError,'frozen mapping bytes changed'):
                trust.verified_freeze()


if __name__ == '__main__':
    unittest.main()
