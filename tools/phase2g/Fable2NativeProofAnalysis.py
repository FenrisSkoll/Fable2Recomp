"""Instruction-level Phase 2G proof packets using the existing verified PPC readers."""
from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path

import Fable2NativeProofSources as sources

sys.path.insert(0, str(sources.ROOT / "tools"))
import Fable2PrototypeCompletion as completion
import Fable2PrototypeCorrespondence as correspondence
import Fable2PrototypeTrust as trust
import Fable2SemanticNative as native

DONOR = "build-23.12.02.0330"
TARGET = "canonical-tu1"


def load_images(inputs):
    images = {}
    for build in (DONOR, TARGET):
        manifest = f"out/prototype-archaeology/derived/{build}/derived-image.json"
        inputs.read(manifest)
        _, blocks, _ = correspondence.load_build(sources.ROOT / "out/prototype-archaeology/derived", build)
        for block in blocks:
            inputs.bind(f"out/prototype-archaeology/derived/{build}/{block.relative_path}")
        images[build] = native.Image(build, blocks)
    inputs.bind("out/tools/ppc-disasm.exe")
    return images


def raw_sha256(data):
    return hashlib.sha256(data).hexdigest().upper()


def function_record(image, start, *, include_disassembly=True):
    function = image.by_start.get(start)
    sources.require(function is not None, f"Missing .pdata function {image.build}/{native.hx(start)}")
    body = image.read(start, function["end"] - start)
    result = {
        "build": image.build,
        "boundary": native.boundary(function),
        "instruction_count": len(body) // 4,
        "raw_body_sha256": raw_sha256(body),
        "cfg_and_accesses": completion.behavior_features(image, function),
    }
    if include_disassembly:
        result["disassembly"] = trust.disassemble(image, start, function["end"])
    return result


def direct_callers(image, target):
    records = []
    for function in image.functions:
        body = image.read(function["start"], function["end"] - function["start"])
        for index, (word,) in enumerate(struct.iter_unpack(">I", body)):
            pc = function["start"] + index * 4
            if word >> 26 == 18 and word & 1 and native.branch(word, pc) == target:
                records.append({"caller": native.boundary(function), "callsite": native.hx(pc),
                                "word": f"{word:08X}"})
    return records


def instruction_window(image, start, end):
    owner = image.owner(start)
    sources.require(owner is not None and end <= owner["end"], "Instruction window lacks one .pdata owner")
    return {"owner": native.boundary(owner), "start": native.hx(start),
            "end_exclusive": native.hx(end), "disassembly": trust.disassemble(image, start, end)}


def require_words(image, expected):
    rows = []
    for address, word in sorted(expected.items()):
        actual = int.from_bytes(image.read(address, 4), "big")
        sources.require(actual == word, f"Instruction changed at {native.hx(address)}")
        rows.append({"address": native.hx(address), "word": f"{actual:08X}"})
    return rows


def changed_words(left, right):
    left_start = int(left["boundary"]["start"], 16)
    right_start = int(right["boundary"]["start"], 16)
    left_words = [line.split()[1] for line in left["disassembly"]]
    right_words = [line.split()[1] for line in right["disassembly"]]
    sources.require(len(left_words) == len(right_words), "Body instruction counts differ")
    return [{"offset": index * 4,
             "donor_address": native.hx(left_start + index * 4), "donor_word": donor,
             "target_address": native.hx(right_start + index * 4), "target_word": target}
            for index, (donor, target) in enumerate(zip(left_words, right_words)) if donor != target]


def hammer_packet(inputs, images, proof_module, selection):
    donor, target = images[DONOR], images[TARGET]
    owner_d = function_record(donor, 0x8229B308)
    owner_t = function_record(target, 0x8229B038)
    callee_d = function_record(donor, 0x8229B488)
    callee_t = function_record(target, 0x8229B1B8)
    sources.require(owner_d["raw_body_sha256"] == owner_t["raw_body_sha256"] ==
                    "7DC8302D7AFF26667F1C4C429DC837D7874A00B2F26231B19F5E3389C3B0B240",
                    "Hammer owner complete bodies changed")
    sources.require(callee_d["raw_body_sha256"] ==
                    "3F6E2EF7782C3F77E81950CE90B45948EB6FC533519480F50CDA49F50B5B5A23" and
                    callee_t["raw_body_sha256"] ==
                    "0EBC32E8EC28FB5D0361AFCEA572773BD259D6B4C726B08BFB1F008F42263A73",
                    "Hammer callee complete bodies changed")
    sources.require(len(changed_words(callee_d, callee_t)) == 2,
                    "Hammer callee relocation delta changed")

    comparator_d = trust.code_region(donor, 0x8226DB80)
    comparator_t = trust.code_region(target, 0x8226D7F8)
    for region, image in ((comparator_d, donor), (comparator_t, target)):
        region["disassembly"] = trust.disassemble(
            image, int(region["start"], 16), int(region["end_exclusive"], 16))
        sources.require(region["kind"] == "internal-code-region" and
                        not region["independent_pdata_entry"] and region["containing_owner"] is None,
                        "Comparator was promoted or acquired .pdata ownership")
    sources.require(comparator_d["reachable_byte_sha256"] == comparator_t["reachable_byte_sha256"] ==
                    "75D59403DCA922941AF9DE2C4FCD6ACCC10FC50F291BBB78FC2BD047BB4DBD5E",
                    "Comparator bytes changed")

    target_callers = direct_callers(target, 0x8229B038)
    caller_starts = {row["caller"]["start"] for row in target_callers}
    sources.require({"0x822756E8", "0x8285C6A8"}.issubset(caller_starts),
                    "Required independent TU1 caller family changed")
    target_caller_words = require_words(target, {
        0x8285CB2C: 0x7F43D378, 0x8285CB30: 0x4BA3E509, 0x8285CB38: 0x987A0024,
        0x8285CB48: 0x4E800421, 0x8285CB4C: 0x987A0025,
        0x822757A0: 0x7FE3FB78, 0x822757A4: 0x48025895, 0x822757A8: 0x897F0024,
        0x822757AC: 0x546A063E, 0x822757B0: 0x7F0A5840, 0x822757C8: 0x4E800421,
    })

    accepted = "docs/fable2-prototype-archaeology/phase2a/evidence/prototype-correspondence-accepted.json"
    candidates = "out/prototype-archaeology/phase2c/reference-candidates.json"
    packets = "out/prototype-archaeology/phase2d/packets.json"
    mapping_context = "out/prototype-archaeology/phase2f/mapping-context-packets.json"
    features = "out/prototype-archaeology/phase2a/prototype-correspondence-function-features.json"
    observations = [
        proof_module.record(inputs, "A-complete-owner", "A", "Complete owner equivalence and Hammer literal role.",
                            "mapping-consumed", inputs.ref(accepted, "/records/809",
                            "BDDB830B46109840F8BFB63627CE37CEA5AF8D2A04F3A6CF7A4DFE50F52DC058"), material=True),
        proof_module.record(inputs, "A-callee-and-comparator", "A", "Nullable-string inequality body and comparator equivalence.",
                            "mapping-consumed", inputs.ref(packets, "/records/6",
                            "E2FF8F2E4DA73B5806EC41CC2865979FBF5877E20A02EF94E91D860F6F0C47CB"), material=True),
        proof_module.record(inputs, "A-phase2f-literal-route", "A", "Phase 2F reused the same literal/callee semantic route.",
                            "correlated-with-mapping", inputs.ref(mapping_context, "/records/1")),
        proof_module.record(inputs, "A-tu1-byte-consumer-family", "A",
                            "TU1 callers store/compare the owner result against the same object's +0x24 byte.",
                            "independent-target-native", inputs.ref(features, "/builds/canonical-tu1/15201"),
                            material=True, compatible=True, owned=True, circular=False,
                            detail={"family_vote_count": 1, "calls": target_callers,
                                    "instructions": target_caller_words}),
        proof_module.record(inputs, "A-object-type", "A", "Complete object/type and virtual-slot meanings.",
                            "unresolved", inputs.ref(candidates, "/proposals/12"), material=False),
    ]
    sources.require(sum(row["proof_eligible"] for row in observations) == 1,
                    "Hammer independent vote reconciliation changed")

    return sources.envelope(
        "hammercombat-packet", selection,
        packet="A", terminal_ids=proof_module.PACKETS["A"]["terminal_ids"],
        owner_mapping={"donor": owner_d, "target": owner_t,
                       "canonical_body_sha256": "C550B8DBD0E4DDFFC7E55A4D913D38065782A6E1F2B97E7E6CB3553DDB6C98FB",
                       "branch_normalized_sha256": "FCC89B3DD14AD60470CD8FE2FA11F288631D64D98CCA6159C1778CCB1A09DE47",
                       "equivalent_complete_owned_body": True},
        reserved_callee={"donor": callee_d, "target": callee_t,
                         "changed_words": changed_words(callee_d, callee_t),
                         "canonical_body_sha256": "2562EC6BD8DD82540BF82AA7B35F652CD26E3F715E8DE2F8414C1376406F62DC",
                         "semantic_role": "nullable-string inequality predicate; 0 equal, 1 unequal",
                         "empty_fallbacks": ["0x82000CA4", "0x82000CA0"]},
        comparator_regions=[comparator_d, comparator_t],
        owner_data_flow={
            "guard": "object+8 nullable 32-bit guest-pointer slot; compare pointed byte string with r4 HammerCombat; equality returns 0",
            "post_guard": "if nested +0x24 bit 0 is set, select an 8-byte record with signed key 24 and return selected +0x3C byte; otherwise return 0",
            "accesses": [
                {"base": "owner", "offset": 4, "width": 4, "operation": "read nested-state guest pointer"},
                {"base": "owner", "offset": 8, "width": 4, "operation": "address nullable guest-pointer member"},
                {"base": "nested", "offset": 36, "width": 1, "operation": "test bit 0"},
                {"base": "nested", "offset": 72, "width": 4, "operation": "read record start"},
                {"base": "nested", "offset": 76, "width": 4, "operation": "read record end"},
                {"base": "nested", "offset": 140, "width": 4, "operation": "read optional selector"},
                {"base": "selector", "offset": 24, "width": 1, "operation": "read index scaled by eight"},
                {"base": "record", "offset": 0, "width": 4, "operation": "signed key compare with 24"},
                {"base": "record", "offset": 4, "width": 4, "operation": "read selected guest pointer"},
                {"base": "selected", "offset": 60, "width": 1, "operation": "return byte"},
            ],
            "return": "byte-valued result; not proven strict Boolean",
        },
        target_native_callers={"records": target_callers,
                               "windows": [instruction_window(target, 0x822757A0, 0x822757CC),
                                           instruction_window(target, 0x8285CB2C, 0x8285CB50)],
                               "interpretation": "one independent byte-state consumer family"},
        independence_observations=observations,
        dispositions={"primary": "independently-corroborated-role", "mapping": "unchanged",
                      "reservation": "retained", "reservation_reason": "internal-code-region-dependent",
                      "role_label": {"kind": "provisional contextual label",
                                     "value": "byte-state query with HammerCombat equality exclusion guard"},
                      "canonical_name": "not-authorized"},
        adversarial={"callee_hammer_name_rejected": True, "owner_hammer_name_rejected": True,
                     "comparator_promoted_to_function": False,
                     "literal_reuse_is_independent": False,
                     "branch_relocations_are_divergence": False,
                     "complete_object_identity_proved": False,
                     "material_contradictions": []},
        input_identities=inputs.identities())
