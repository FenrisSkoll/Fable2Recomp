"""Synthetic PPC and metadata fixtures; no game bytes or runtime launches."""
import copy
import struct
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import Fable2SemanticNative as native
import Fable2PrototypeSemantics as semantic


def instruction(op, rt, ra, imm):
    return (op << 26) | (rt << 21) | (ra << 16) | (imm & 65535)


def call(pc, target):
    return 0x48000001 | ((target - pc) & 0x03FFFFFC)


def fixture(*, alias=False, interior=False, use_callback=True, loop=False):
    data = bytearray(0x180)
    struct.pack_into(">IIII", data, 0, 0x2100, 0x1204 if interior else 0x1200,
                     0x2120, 0x1200 if alias else 0x1220)
    data[0x100:0x100 + len(b"DistinctAlpha\0")] = b"DistinctAlpha\0"
    data[0x120:0x120 + len(b"DistinctBeta\0")] = b"DistinctBeta\0"
    if loop:
        words = [instruction(14, 31, 0, 0x2000), instruction(14, 30, 0, 0x2010),
                 instruction(32, 4, 31, 0), instruction(32, 5, 31, 4), call(0x1010, 0x1100),
                 instruction(14, 31, 31, 8),
                 (31 << 26) | (6 << 23) | (31 << 16) | (30 << 11) | (32 << 1),
                 (16 << 26) | (12 << 21) | (24 << 16) | ((0x1008 - 0x101C) & 65532),
                 0x4E800020]
    else:
        words = []
        for offset in (0, 8):
            words.extend([instruction(14, 6, 0, 0x2000 + offset),
                          instruction(32, 4, 6, 0),
                          instruction(32, 5, 6, 4) if use_callback else instruction(14, 5, 0, 0)])
            words.append(call(0x1000 + len(words) * 4, 0x1100))
        words.append(0x4E800020)
    functions = [(0x1000, words), (0x1100, [instruction(36, 4, 3, 0), instruction(36, 5, 3, 4), 0x4E800020]),
                 (0x1200, [0x60000000, 0x4E800020]), (0x1220, [0x60000000, 0x4E800020])]
    return make_image(functions, bytes(data)), {0x2100, 0x2120}


def make_image(functions, data=b"", data_start=0x2000, writable=False):
    code = bytearray(0x400)
    pdata = bytearray()
    for start, words in functions:
        payload = struct.pack(">" + "I" * len(words), *words)
        code[start - 0x1000:start - 0x1000 + len(payload)] = payload
        pdata.extend(struct.pack(">II", start, len(words) << 8))
    blocks = [SimpleNamespace(name=".pdata", start=0x800, data=bytes(pdata), execute=False, write=False),
              SimpleNamespace(name=".text", start=0x1000, data=bytes(code), execute=True, write=False),
              SimpleNamespace(name=".data" if writable else ".rdata", start=data_start, data=data, execute=False, write=writable)]
    return native.Image("synthetic", blocks)


class NativeEvidenceTests(unittest.TestCase):
    def test_direct_string_pointer_and_valid_callback_descriptor(self):
        image, anchors = fixture()
        scan = native.scan_image(image, anchors)
        records = native.constructor_registrations(image, anchors, scan["calls"])
        self.assertEqual(2, len(records))
        self.assertTrue(all(r["status"] == "proven-native-descriptor" for r in records))
        self.assertEqual(["0x00001200", "0x00001220"], [r["callback"] for r in records])
        self.assertEqual("0x00001100", records[0]["name_store"]["instruction"])

    def test_signed_low_half_carry(self):
        image = make_image([(0x1000, [instruction(15, 4, 0, 0x8201), instruction(14, 4, 4, 0xF000),
                                      call(0x1008, 0x1100), 0x4E800020])], b"DistinctAnchor\0", data_start=0x8200F000)
        refs, _, _ = native.scan_function(image, image.functions[0], {0x8200F000})
        used = [r for r in refs if r["role"] == "call-argument"]
        self.assertEqual(1, len(used))
        self.assertEqual(["0x00001000", "0x00001004"], used[0]["definition_instructions"])

    def test_base_relative_indirect_readonly_table_load(self):
        image, anchors = fixture()
        refs = native.scan_image(image, anchors)["references"]
        use = next(r for r in refs if r["role"] == "call-argument")
        self.assertTrue(use["readonly_pointer_slots"])
        self.assertIn("0x00002000", use["readonly_pointer_slots"])

    def test_repeated_fixed_stride_records_with_joint_load(self):
        image, anchors = fixture()
        calls = native.scan_image(image, anchors)["calls"]
        tables = native.table_candidates(image, anchors, calls)
        self.assertEqual(2, len(tables))
        self.assertTrue(all(r["repeated_layout"] and r["joint_field_load_calls"] for r in tables))

    def test_counted_loop_proves_complete_descriptor_array(self):
        image, anchors = fixture(loop=True)
        rows = native.recover_counted_registration_loops(image, anchors)
        self.assertEqual(2, len(rows))
        self.assertTrue(all(r["kind"] == "counted-descriptor-loop" for r in rows))
        self.assertEqual("0x00002010", rows[0]["table_end_exclusive"])

    def test_nearby_code_value_not_loaded_is_quarantined(self):
        image, anchors = fixture(use_callback=False)
        scan = native.scan_image(image, anchors)
        self.assertEqual([], native.constructor_registrations(image, anchors, scan["calls"]))
        tables = native.table_candidates(image, anchors, scan["calls"])
        self.assertTrue(all("name-and-callback-not-proven-loaded-together" in r["reasons"] for r in tables))

    def test_interior_callback_has_no_implicit_thunk_explanation(self):
        image, anchors = fixture(interior=True)
        scan = native.scan_image(image, anchors)
        tables = native.table_candidates(image, anchors, scan["calls"])
        self.assertIn("interior-callback-without-entry-proof", tables[0]["reasons"])
        self.assertFalse(any(r["status"] == "proven-native-descriptor" for r in
                             native.constructor_registrations(image, anchors, scan["calls"])))

    def test_multiple_aliases_can_share_callback(self):
        image, anchors = fixture(alias=True)
        scan = native.scan_image(image, anchors)
        rows = native.constructor_registrations(image, anchors, scan["calls"])
        self.assertEqual(2, len(rows))
        self.assertEqual({"0x00001200"}, {r["callback"] for r in rows})

    def test_unknown_write_kills_materialized_value(self):
        image = make_image([(0x1000, [instruction(15, 4, 0, 0x8201), 0x7C842214,
                                      instruction(14, 4, 4, 0xF000), call(0x100C, 0x1100), 0x4E800020])])
        refs, _, _ = native.scan_function(image, image.functions[0], {0x8200F000})
        self.assertEqual([], refs)

    def test_writable_initialized_pointer_not_assumed_runtime_constant(self):
        image = make_image([(0x1000, [instruction(14, 6, 0, 0x2000), instruction(32, 4, 6, 0),
                                      call(0x1008, 0x1100), 0x4E800020])], struct.pack(">I", 0x2100), writable=True)
        refs = native.scan_image(image, {0x2100})["references"]
        self.assertEqual([], refs)

    def test_loop_wrong_backedge_or_bound_is_rejected(self):
        image, anchors = fixture(loop=True)
        image.blocks[1].data = image.blocks[1].data[:0x1C] + struct.pack(">I", 0x4182FFEC) + image.blocks[1].data[0x20:]
        self.assertEqual([], native.recover_counted_registration_loops(image, anchors))

    def test_intermediate_lis_is_not_a_consumed_string_reference(self):
        image = make_image([(0x1000, [instruction(15, 4, 0, 0x2000), instruction(14, 4, 4, 0x100),
                                      call(0x1008, 0x1100), 0x4E800020])])
        refs, _, _ = native.scan_function(image, image.functions[0], {0x20000000})
        self.assertEqual([], refs)

    def test_nonexecutable_callback_is_preserved_as_negative(self):
        image, anchors = fixture()
        data = bytearray(image.blocks[2].data)
        struct.pack_into(">I", data, 4, 0x2000)
        image.blocks[2].data = bytes(data)
        tables = native.table_candidates(image, anchors, native.scan_image(image, anchors)["calls"])
        self.assertIn("nonexecutable-or-no-pdata-callback", tables[0]["reasons"])

    def test_stripped_target_requires_three_pairs_and_real_paired_stores(self):
        donor, anchors = fixture()
        source = native.constructor_registrations(donor, anchors, native.scan_image(donor, anchors)["calls"])[0]
        target, _ = fixture()
        data = bytearray(target.blocks[2].data)
        struct.pack_into(">I", data, 0, 0)
        struct.pack_into(">I", data, 8, 0)
        target.blocks[2].data = bytes(data)
        destination = native.constructor_registrations(target, {0}, native.scan_image(target, {0})["calls"])[0]
        pairs = [{"target_start": address, "status": "accepted-exact-unique"}
                 for address in ("0x00001200", "0x00001100", "0x00001000")]
        self.assertTrue(semantic.descriptor_support(source, destination, *pairs, False))
        self.assertFalse(semantic.descriptor_support(source, destination, pairs[0], pairs[1], None, False))
        destination["callback_store"]["offset"] = 8
        self.assertFalse(semantic.descriptor_support(source, destination, *pairs, False))


class SemanticPolicyTests(unittest.TestCase):
    def outcome(self, **overrides):
        args = dict(filtered=False, donor_refs=["X-exact"],
                    mapping={"status": "accepted-exact-unique"},
                    corroboration=[{"kind": "proven-equivalent-descriptor"}], contradictions=[])
        args.update(overrides)
        return semantic.grade(**args)[0]

    def test_donor_without_accepted_mapping_is_blocked(self):
        self.assertEqual("candidate-donor-only", self.outcome(mapping=None))

    def test_mapping_alone_cannot_accept(self):
        self.assertEqual("candidate-target-unconfirmed", self.outcome(corroboration=[]))

    def test_stripped_string_with_independent_descriptor_support(self):
        # No string-equivalence observation: only structurally proven descriptor
        # context may support this policy gate. The native fixtures test recovery.
        self.assertEqual("accepted-registered-callback", self.outcome(registration=True))

    def test_conflicting_target_role_forces_quarantine(self):
        self.assertEqual("quarantined", self.outcome(contradictions=["different-callback-field"]))

    def test_duplicate_generic_strings_are_ambiguous(self):
        self.assertEqual("generic-string", semantic.classify("Load"))
        self.assertEqual("ambiguous", self.outcome(filtered=True, ambiguous=True))

    def test_external_only_observation_never_accepts(self):
        self.assertEqual("external-only-observation", semantic.classify("Debug.ReloadShaderBank", external=True))
        self.assertEqual("quarantined", self.outcome(filtered=True, donor_refs=[]))

    def test_nonaccepted_binary_candidate_join_raises(self):
        with self.assertRaises(ValueError):
            self.outcome(mapping={"status": "candidate-structural"})

    def test_graph_high_fanout_cannot_contaminate_region(self):
        graph = native.expand(["seed"], {"seed": list(map(str, range(9)))})
        self.assertEqual(1, len(graph))
        self.assertEqual("fanout-limit", graph[0]["reason"])
        self.assertFalse(graph[0]["semantic_acceptance"])

    def test_graph_depth_cycles_and_determinism(self):
        edges = {"a": ["c", "b"], "b": ["a"], "c": ["d"]}
        self.assertEqual(native.expand(["a"], edges), native.expand(["a", "a"], {"a": ["b", "c"], "b": ["a"], "c": ["d"]}))
        self.assertEqual(2, len(native.expand(["a"], edges)))
        self.assertIn("cycle", {r["reason"] for r in native.expand(["a"], edges, depth=2)})

    def test_same_address_data_with_incompatible_use_rejected(self):
        self.assertFalse(native.compatible_access({"width": 4, "mode": "read"}, {"width": 4, "mode": "write"}))

    def test_output_escape_and_forbidden_paths_rejected(self):
        for path in ("fable2_manifest.toml", "generated/test.cpp", "../outside.json", "C:/outside.json"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                semantic.output_path(path)

    def test_provenance_timestamp_not_hidden_input(self):
        first = semantic.envelope("index", records=[])
        self.assertNotIn("generated_at", first)
        self.assertEqual(semantic.data_bytes(first), semantic.data_bytes(semantic.envelope("index", records=[])))


def minimal_family():
    anchor = {"id": "A-test", "spelling": "DistinctAnchor", "provenance": [{"source": "synthetic"}],
              "occurrences": [], "categories": ["subsystem-profiling-label"], "subsystem": "debug", "filters": []}
    rows = [{"id": "S-" + build, "anchor_id": "A-test", "build": build, "kind": "native-xref-context",
             "donor_function": None, "donor_xrefs": [], "mapping": None, "target_corroboration": [],
             "contradictions": [], "status": "quarantined", "reason": "no-proven-native-donor-reference",
             "correspondence_block": None, "proposed_name": None, "canonical_adoption": False, "intersections": []}
            for build in semantic.BUILDS[:2]]
    queue, availability = semantic.review_queue(rows, {anchor["id"]: anchor}, [])
    return {"inventory": {"anchors": [anchor]}, "xrefs": {"references": [], "data_pointers": []},
            "registrations": {"records": []}, "index": {"records": rows}, "accepted": {"records": []},
            "mapping-review": {"records": []}, "graph": {"records": []}, "globals": {"records": []},
            "review": {"records": queue, "availability": availability, "problem_sets": []}}


class CrossArtifactTests(unittest.TestCase):
    def test_valid_terminal_family_and_deterministic_serialization(self):
        first, second = minimal_family(), minimal_family()
        semantic.validate_family(first, [])
        self.assertEqual(semantic.data_bytes(first), semantic.data_bytes(second))

    def test_duplicate_identifier_rejected(self):
        family = minimal_family()
        family["index"]["records"].append(copy.deepcopy(family["index"]["records"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate record"):
            semantic.validate_family(family, [])

    def test_duplicate_association_even_with_new_id_rejected(self):
        family = minimal_family()
        row = copy.deepcopy(family["index"]["records"][0])
        row["id"] = "different"
        family["index"]["records"].append(row)
        with self.assertRaisesRegex(ValueError, "duplicate association"):
            semantic.validate_family(family, [])

    def test_missing_terminal_rejected(self):
        family = minimal_family()
        family["index"]["records"].pop()
        with self.assertRaisesRegex(ValueError, "terminal coverage"):
            semantic.validate_family(family, [])

    def test_unsupported_accepted_record_rejected(self):
        family = minimal_family()
        family["index"]["records"][0]["status"] = "accepted-xref-corroborated"
        with self.assertRaisesRegex(ValueError, "incomplete accepted"):
            semantic.validate_family(family, [])

    def test_accepted_subset_drift_rejected(self):
        family = minimal_family()
        family["accepted"]["records"] = [family["index"]["records"][0]]
        with self.assertRaisesRegex(ValueError, "accepted subset"):
            semantic.validate_family(family, [])

    def test_review_availability_drift_rejected(self):
        family = minimal_family()
        family["review"]["availability"]["quarantined"]["available"] += 1
        with self.assertRaisesRegex(ValueError, "review selection"):
            semantic.validate_family(family, [])

    def test_no_canonical_name_or_graph_propagation(self):
        for kind in ("index", "graph"):
            family = minimal_family()
            if kind == "index":
                family[kind]["records"][0]["proposed_name"] = "Invented"
            else:
                family[kind]["records"].append({"semantic_acceptance": True})
            with self.assertRaisesRegex(ValueError, "propagation forbidden"):
                semantic.validate_family(family, [])

    def test_terminal_counts_cannot_drift(self):
        family = minimal_family()
        with self.assertRaisesRegex(ValueError, "terminal total"):
            semantic.validate_family(family, [], {"investigated_associations": 1, "accepted": 0})

    def test_report_payload_and_provenance_envelope_regression(self):
        family = minimal_family()
        summary = {"counts": {"accepted": 0}, "source_pins_sha256": "0" * 64, "artifacts": []}
        report = semantic.report_text(summary, family)
        self.assertEqual(report, semantic.report_text(copy.deepcopy(summary), copy.deepcopy(family)))
        changed = copy.deepcopy(summary)
        changed["counts"]["accepted"] = 1
        self.assertNotEqual(report, semantic.report_text(changed, family))
        changed = copy.deepcopy(summary)
        changed["source_pins_sha256"] = "1" * 64
        self.assertNotEqual(report, semantic.report_text(changed, family))
        self.assertNotIn("generated_at", semantic.envelope("validation"))

    def test_committed_schema_defines_every_family(self):
        import json
        schema = json.loads((semantic.ROOT / "tools/schemas/fable2-prototype-semantics-v1.schema.json").read_text())
        names = schema["properties"]["schema"]["properties"]["name"]["enum"]
        self.assertEqual(11, len(names))
        self.assertIn("association", schema["$defs"])
        self.assertEqual(False, schema["$defs"]["association"]["properties"]["canonical_adoption"]["const"])


if __name__ == "__main__":
    unittest.main()
