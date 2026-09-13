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


def oxygen_packet(inputs, images, proof_module, selection):
    donor, target = images[DONOR], images[TARGET]
    owner_d = function_record(donor, 0x82406F98)
    owner_t = function_record(target, 0x82405868)
    sources.require((owner_d["boundary"]["end_exclusive"], owner_t["boundary"]["end_exclusive"]) ==
                    ("0x82407030", "0x82405900"), "Oxygen owner boundary changed")
    sources.require(owner_d["raw_body_sha256"] ==
                    "BB7CAF03EFA995811F529C0ED8D1DA189A90DE1E49784ED618DC4CA8CCE7D5AB" and
                    owner_t["raw_body_sha256"] ==
                    "3072920306575617A083AFC89F5901550D7C618047E383498B573CD17BF2E942",
                    "Oxygen owner bytes changed")
    owner_changes = changed_words(owner_d, owner_t)
    sources.require(len(owner_changes) == 7, "Oxygen owner relocation count changed")

    keyed_d = function_record(donor, 0x823ADDA8)
    keyed_t = function_record(target, 0x823AD468)
    attach_d = function_record(donor, 0x8238D020, include_disassembly=False)
    attach_t = function_record(target, 0x8238D4B8, include_disassembly=False)
    neighbor_d = function_record(donor, 0x82407030, include_disassembly=False)
    neighbor_t = function_record(target, 0x82405900, include_disassembly=False)
    hash_d = trust.code_region(donor, 0x821F3F00)
    hash_t = trust.code_region(target, 0x821F3D58)
    sources.require(keyed_d["boundary"]["size"] == keyed_t["boundary"]["size"] == 0x70,
                    "Oxygen keyed helper boundary changed")
    sources.require(attach_d["boundary"]["size"] == attach_t["boundary"]["size"] == 0x184,
                    "Oxygen attachment helper boundary changed")
    sources.require(all(region["kind"] == "internal-code-region" and
                        not region["independent_pdata_entry"] for region in (hash_d, hash_t)),
                    "Key hash internal regions acquired function ownership")
    sources.require(direct_callers(donor, 0x82406F98) == [] and
                    direct_callers(target, 0x82405868) == [],
                    "Oxygen direct-caller result changed")

    fields = [
        {"key": "MaxOxygen", "terminal_id": "S-818A834A4CED040235B7B86D",
         "literal_sha256": "AD22BC91792D4AFEE9DBED9D803FD6090C08E02EA9BDA94D31A4B5F7E91C30FA",
         "donor_literal": "0x820B11B8", "target_literal": "0x820B11DC",
         "donor_instruction": "0x82406FD8", "target_instruction": "0x824058A8",
         "argument": "r5=object+0x38", "offset": 0x38, "width": 4,
         "operation": "conditional keyed 32-bit write", "helper": "0x823ADDA8:0x823AD468",
         "evidence_class": "mapping-consumed", "confidence": "CONFIRMED"},
        {"key": "OxygenConsumptionRate", "terminal_id": "S-31139DC943017A090C85C7E0",
         "literal_sha256": "3DB2050F6A52B8BDB5D2D9153B2511895CD0D7493E5C057AEA731111A3B29909",
         "donor_literal": "0x820B11C4", "target_literal": "0x820B11E8",
         "donor_instruction": "0x82406FEC", "target_instruction": "0x824058BC",
         "argument": "r5=object+0x3C", "offset": 0x3C, "width": 4,
         "operation": "conditional keyed 32-bit write", "helper": "0x823ADDA8:0x823AD468",
         "evidence_class": "mapping-consumed", "confidence": "CONFIRMED"},
        {"key": "OxygenRecoveryRate", "terminal_id": "S-F48219FB96F897D4D426B8C0",
         "literal_sha256": "6AA64E2A8803EA8BDEAEE6B5FF865CFF7B74A5B38222B677B15B5F34F12C0A57",
         "donor_literal": "0x820B11DC", "target_literal": "0x820B1200",
         "donor_instruction": "0x82407000", "target_instruction": "0x824058D0",
         "argument": "r5=object+0x40", "offset": 0x40, "width": 4,
         "operation": "conditional keyed 32-bit write", "helper": "0x823ADDA8:0x823AD468",
         "evidence_class": "mapping-consumed", "confidence": "CONFIRMED"},
        {"key": None, "terminal_id": None, "donor_instruction": "0x82407004/0x82407008",
         "target_instruction": "0x824058D4/0x824058D8", "argument": "object-local",
         "offset": 0x34, "source_offset": 0x38, "width": 4,
         "operation": "unconditional 32-bit copy after optional loads", "helper": None,
         "evidence_class": "mapping-consumed", "confidence": "CONFIRMED"},
    ]
    require_words(donor, {0x82406FB8: 0x807F0004, 0x82406FBC: 0x4BF86065,
                          0x82406FD8: 0x4BFA6DD1, 0x82406FEC: 0x4BFA6DBD,
                          0x82407000: 0x4BFA6DA9, 0x82407004: 0x811F0038,
                          0x82407008: 0x911F0034})
    require_words(target, {0x82405888: 0x807F0004, 0x8240588C: 0x4BF87C2D,
                           0x824058A8: 0x4BFA7BC1, 0x824058BC: 0x4BFA7BAD,
                           0x824058D0: 0x4BFA7B99, 0x824058D4: 0x811F0038,
                           0x824058D8: 0x911F0034})

    packets = "out/prototype-archaeology/phase2d/packets.json"
    accepted = "docs/fable2-prototype-archaeology/phase2a/evidence/prototype-correspondence-accepted.json"
    index = "docs/fable2-prototype-archaeology/phase2a/evidence/prototype-correspondence-index.json"
    observations = [
        proof_module.record(inputs, "B-owner-body-fields", "B",
                            "Complete owner, literal, argument, CFG, helper and field roles.",
                            "mapping-consumed", inputs.ref(packets, "/records/68",
                            "6873CCA3463EEDAE82F36B8099C0F37125C162113A1BB2FC185306D5729816F8"), material=True),
        proof_module.record(inputs, "B-keyed-helper-semantics", "B",
                            "The consumed keyed callee hashes a key and conditionally copies one word.",
                            "correlated-with-mapping", inputs.ref(accepted, "/records/1609",
                            "9A66305E990063027373B24ED3C1B511ED3652049D749C8743A22E54600BBDBB")),
        proof_module.record(inputs, "B-attachment-helper-semantics", "B",
                            "The consumed attachment edge has generic object/container behavior.",
                            "correlated-with-mapping", inputs.ref(accepted, "/records/1570",
                            "F2B9E5DFDAE3F7E75C349B764E16A7827BDEC834002EBC7A66B45F5B843F9F1E")),
        proof_module.record(inputs, "B-neighbor-different-role", "B",
                            "The adjacent bodies use the same keys and offsets through a field visitor, not the keyed-load helper.",
                            "correlated-with-mapping", inputs.ref(index, "/functions/5435")),
        proof_module.record(inputs, "B-no-direct-callers", "B",
                            "The complete TU1 .pdata population has no direct bl caller to the owner.",
                            "independent-target-native", inputs.ref(index, "/functions/5434"),
                            material=False, compatible=True, owned=True, circular=False),
        proof_module.record(inputs, "B-storage-scalar-type", "B",
                            "Integer versus floating representation and current-oxygen meaning of +0x34.",
                            "unresolved", inputs.ref(packets, "/records/68"), material=False),
        proof_module.record(inputs, "B-runtime-consumers", "B",
                            "A bounded downstream depletion/recovery consumer was not established.",
                            "unresolved", inputs.ref(index, "/functions/5434"), material=False),
    ]
    sources.require(not any(row["proof_eligible"] for row in observations),
                    "Oxygen packet unexpectedly gained an independent semantic vote")
    return sources.envelope(
        "oxygen-packet", selection, packet="B", terminal_ids=proof_module.PACKETS["B"]["terminal_ids"],
        owner_mapping={"donor": owner_d, "target": owner_t, "changed_words": owner_changes,
                       "canonical_body_sha256": "04BAAB6EA6005344343106826998B73AD4F14A296012A1DB390D266A8955CF19",
                       "equivalent_complete_owned_body": True},
        calling_convention={"r3": "object", "r4": "nullable source/context",
                            "attachment": "r3=lwz object+4; r4=object",
                            "keyed_load": "r3=context; r4=complete key start; r5=destination word",
                            "return": "unstable helper residue; no meaningful owner return established"},
        field_role_table=fields,
        keyed_helper={"donor": keyed_d, "target": keyed_t,
                      "role": "hash NUL-terminated key with seed 0x811C9DC5 and prime 0x01000193; nullable lookup; conditional 32-bit copy; return 1/0",
                      "hash_regions": [hash_d, hash_t], "mapping_support_reuse": True},
        attachment_helper={"donor": attach_d, "target": attach_t,
                           "role": "generic object/container attachment; not oxygen ownership",
                           "mapping_support_reuse": True},
        same_string_different_role_control={"donor": neighbor_d, "target": neighbor_t,
                                            "result": "rejected as independent; same keys/offsets flow through field-visitor topology",
                                            "approved_correspondence": False},
        direct_callers={"donor": [], "target": [], "indirect_callers": "unresolved"},
        role_classification={"property_registration": False, "keyed_load_or_deserialization_style": True,
                             "initialization": "unconditional +0x38 to +0x34 word copy only",
                             "outbound_serialization": False, "runtime_depletion_or_recovery": False,
                             "storage_type": "opaque 32-bit words"},
        independence_observations=observations,
        dispositions={"primary": "behaviorally-corresponding-role-reserved", "mapping": "unchanged",
                      "reservation": "retained", "reservation_reason": "single-independent-support-class",
                      "role_label": {"kind": "provisional contextual label",
                                     "value": "keyed oxygen-field load plus 32-bit current-from-maximum initialization"},
                      "canonical_name": "not-authorized"},
        contradictions=[], unresolved=["typed scalar representation", "indirect caller ownership",
                                        "downstream depletion/recovery consumer", "complete object identity"],
        input_identities=inputs.identities())


def world_reward_packet(inputs, images, proof_module, selection):
    donor, target = images[DONOR], images[TARGET]
    owner_d = function_record(donor, 0x825240E8)
    owner_t = function_record(target, 0x82522C10)
    sources.require((owner_d["boundary"]["end_exclusive"], owner_t["boundary"]["end_exclusive"]) ==
                    ("0x82524188", "0x82522CB0"), "World/reward owner boundary changed")
    sources.require(owner_d["raw_body_sha256"] ==
                    "DBAC5D6EEF3C47A317C64CB88501A73753B9784317C488B3F7AA43E3C58EC451" and
                    owner_t["raw_body_sha256"] ==
                    "3A660B7E2F8973DDCF054A80BF3023EB3329480933C32DB3BD4F525B4F83B443",
                    "World/reward owner bytes changed")
    owner_changes = changed_words(owner_d, owner_t)
    sources.require(len(owner_changes) == 9, "World/reward owner relocation count changed")

    resolver_d = function_record(donor, 0x821B2528)
    resolver_t = function_record(target, 0x821B24F8)
    scalar_d = function_record(donor, 0x823C0588)
    scalar_t = function_record(target, 0x823BF820)
    boolean_d = function_record(donor, 0x82310448)
    boolean_t = function_record(target, 0x82310290)
    second_d = function_record(donor, 0x82524CA0, include_disassembly=False)
    second_t = function_record(target, 0x825237C8, include_disassembly=False)
    scalar_visitor = function_record(target, 0x824807C8, include_disassembly=False)
    boolean_visitor = function_record(target, 0x82A1CE48, include_disassembly=False)
    scalar_lookup = function_record(target, 0x82A006C8, include_disassembly=False)
    boolean_lookup = function_record(target, 0x82A003B0, include_disassembly=False)
    sources.require(resolver_d["boundary"]["size"] == resolver_t["boundary"]["size"] == 0x78,
                    "World/reward handle resolver boundary changed")
    sources.require(scalar_d["boundary"]["size"] == scalar_t["boundary"]["size"] == 0x68,
                    "World/reward scalar helper boundary changed")
    sources.require(boolean_d["boundary"]["size"] == boolean_t["boundary"]["size"] == 0x60,
                    "World/reward Boolean helper boundary changed")

    callers_d = direct_callers(donor, 0x825240E8)
    callers_t = direct_callers(target, 0x82522C10)
    sources.require({row["caller"]["start"] for row in callers_t} == {"0x8251BCE8", "0x825237C8"},
                    "World/reward target direct-caller population changed")
    require_words(target, {
        0x82523874: 0x7FA3EB78, 0x82523878: 0x4BFFF399,
        0x82523A30: 0x388B0398, 0x82523A38: 0x4BD09499,
        0x82523A50: 0x38BD0020, 0x82523A58: 0x4BF5CD71,
        0x82523A6C: 0x388B03A8, 0x82523A74: 0x4BD0945D,
        0x82523A8C: 0x38BD0024, 0x82523A94: 0x4BF5CD35,
        0x82523CF0: 0x388A03B4, 0x82523CF8: 0x4BD091D9,
        0x82523CFC: 0x38BD004D, 0x82523D08: 0x484F9141,
        0x8251BD5C: 0x7FA3EB78, 0x8251BD60: 0x48006EB1,
    })

    fields = [
        {"key": "RewardRenown", "terminal_id": "S-53D9FAFB09CA0C7E1FC73807",
         "literal_sha256": "4C3B17A9FEA97313458EBFFDB888A1D77CF6FE5519BB8DE3EFAD22AC5E18FF82",
         "donor_range": "[0x820C0364,0x820C0371)", "target_range": "[0x820C0398,0x820C03A5)",
         "donor_instruction": "0x82524134/0x82524138", "target_instruction": "0x82522C5C/0x82522C60",
         "offset": 0x20, "width": 4, "operation": "keyed scalar return then stw",
         "helper": "0x823C0588:0x823BF820", "evidence_class": "mapping-consumed",
         "confidence": "CONFIRMED"},
        {"key": "RewardMoney", "terminal_id": "S-202449BD00F31D43FE6EBBA4",
         "literal_sha256": "D63CEE739771D6B234ADDAF1002E6B0CBA03C6562DFEF6005F66A13BDC5FC1FE",
         "donor_range": "[0x820C0374,0x820C0380)", "target_range": "[0x820C03A8,0x820C03B4)",
         "donor_instruction": "0x82524150/0x82524154", "target_instruction": "0x82522C78/0x82522C7C",
         "offset": 0x24, "width": 4, "operation": "keyed scalar return then stw",
         "helper": "0x823C0588:0x823BF820", "evidence_class": "mapping-consumed",
         "confidence": "CONFIRMED"},
        {"key": "AppearOnWorldMap", "terminal_id": "S-36653A3F9B530DB894F7EE5F",
         "literal_sha256": "CA08CFD4FE64BD87DF841D38C815EDC5E64AE5C52AC247B8DE26D5AEB676DFC7",
         "donor_range": "[0x820C0380,0x820C0391)", "target_range": "[0x820C03B4,0x820C03C5)",
         "donor_instruction": "0x82524168/0x8252416C", "target_instruction": "0x82522C90/0x82522C94",
         "offset": 0x4D, "width": 1, "operation": "keyed normalized Boolean return then stb",
         "helper": "0x82310448:0x82310290", "evidence_class": "mapping-consumed",
         "confidence": "CONFIRMED"},
    ]
    require_words(donor, {0x825240FC: 0x81640000, 0x82524110: 0x917E0004,
                          0x82524114: 0x81240004, 0x82524118: 0x913E0008,
                          0x82524134: 0x4BE9C455, 0x82524138: 0x907E0020,
                          0x82524150: 0x4BE9C439, 0x82524154: 0x907E0024,
                          0x82524168: 0x4BDEC2E1, 0x8252416C: 0x987E004D})
    require_words(target, {0x82522C24: 0x81640000, 0x82522C38: 0x917E0004,
                           0x82522C3C: 0x81240004, 0x82522C40: 0x913E0008,
                           0x82522C5C: 0x4BE9CBC5, 0x82522C60: 0x907E0020,
                           0x82522C78: 0x4BE9CBA9, 0x82522C7C: 0x907E0024,
                           0x82522C90: 0x4BDED601, 0x82522C94: 0x987E004D})

    packets = "out/prototype-archaeology/phase2d/packets.json"
    features = "out/prototype-archaeology/phase2a/prototype-correspondence-function-features.json"
    rejected = "out/prototype-archaeology/phase2c/completion/effective-map.json"
    target_routes = "out/prototype-archaeology/phase2f/target-corroboration.json"
    observations = [
        proof_module.record(inputs, "C-owner-body-fields", "C",
                            "Complete owner, three keys, helper edges, field offsets and widths.",
                            "mapping-consumed", inputs.ref(packets, "/records/128",
                            "3D19299998B3D2F7CCA86622038FEBF50CF14E0DA6FC27E3DE3C3E4419942EFB"), material=True),
        proof_module.record(inputs, "C-helper-property-semantics", "C",
                            "The same consumed helper topology resolves a source and performs keyed scalar/Boolean lookup.",
                            "correlated-with-mapping", inputs.ref(packets, "/records/128")),
        proof_module.record(inputs, "C-second-tu1-field-visitors", "C",
                            "A direct TU1 caller independently revisits +0x20/+0x24/+0x4D through distinct typed visitor families.",
                            "independent-target-native", inputs.ref(features, "/builds/canonical-tu1/7939"),
                            material=True, compatible=True, owned=True, circular=False,
                            detail={"vote_count": 1, "scalar_offsets": [0x20, 0x24],
                                    "boolean_like_offset": 0x4D}),
        proof_module.record(inputs, "C-fourth-terminal-alias", "C",
                            "SetObjectiveTag is a rejected donor-only r6 high-half alias; H1 never consumes r6 and TU1 0x820C0000 is interior unrelated text.",
                            "contradictory", inputs.ref(rejected,
                            "/additions/6/canonicalized_reference_evidence/rejected_references/0"),
                            material=True, compatible=False, owned=True, circular=False,
                            detail={"terminal_id": "S-26C37A0D8DC5C81610D44E94",
                                    "mapping_mutation": False, "review_trigger": True,
                                    "contradicts": "literal-use attribution only"}),
        proof_module.record(inputs, "C-phase2f-h1-consumer-attribution", "C",
                            "Phase 2F labels H1 as a literal consumer, but H1 reads neither r5, r6 nor r7; H2 is the scalar key consumer.",
                            "contradictory", inputs.ref(target_routes, "/records/12"),
                            material=True, compatible=False, owned=True, circular=False,
                            detail={"mapping_mutation": False, "review_trigger": True,
                                    "contradicts": "semantic edge attribution, not owner correspondence"}),
        proof_module.record(inputs, "C-runtime-reward-or-map-behavior", "C",
                            "Reward granting, arithmetic, map-marker behavior and complete quest ownership.",
                            "unresolved", inputs.ref(packets, "/records/128"), material=False),
    ]
    sources.require(sum(row["proof_eligible"] for row in observations) == 1,
                    "World/reward independent vote reconciliation changed")
    return sources.envelope(
        "world-reward-packet", selection, packet="C",
        terminal_ids=proof_module.PACKETS["C"]["terminal_ids"],
        terminal_reconciliation={"population": 4, "genuine_complete_key_contexts": 3,
                                 "independent_votes_from_aliases": 0,
                                 "spurious_terminal": "S-26C37A0D8DC5C81610D44E94",
                                 "reason": "SetObjectiveTag donor-only high-half alias; no complete consumed target key"},
        owner_mapping={"donor": owner_d, "target": owner_t, "changed_words": owner_changes,
                       "canonical_body_sha256": "D67ADBEEC8AD31A0F02EA0043912AB5072E92EECA363F3C44F26C45153C7EADE",
                       "reference_erased_sha256": "396577219772DB2A341FD36515F63EB98ACDAC6F1576C0D676CD848BC8D8007F",
                       "equivalent_complete_owned_body": True},
        owner_data_flow={"input": "r3 destination object; r4 two-word source handle",
                         "initial_copy": "lwz/stw source[0:4] -> object+4; source[4:8] -> object+8",
                         "condition": "skip property stores when copied first word is zero",
                         "populated_path": "resolve object+4 handle, load two keyed 32-bit scalars and one normalized byte",
                         "missing_key_defaults": "+0x20/+0x24 become zero and +0x4D becomes false",
                         "zero_handle": "skip all three stores; prior field values remain",
                         "return": "destination residue on skipped path; final Boolean-helper byte on populated path; not a stable owner return"},
        field_role_table=fields,
        helpers={"handle_resolver": {"donor": resolver_d, "target": resolver_t,
                                     "role": "resolve two-word handle; does not consume r5/r6/r7"},
                 "scalar_lookup": {"donor": scalar_d, "target": scalar_t,
                                   "deep_target": scalar_lookup,
                                   "role": "hash r4 key, nullable mode-1 lookup, return entry word or zero"},
                 "boolean_lookup": {"donor": boolean_d, "target": boolean_t,
                                    "deep_target": boolean_lookup,
                                    "role": "zero local byte, hash r4 key, mode-0 lookup normalizing word nonzero to 1, return byte"}},
        target_native_consumer={"function": second_t, "donor_context_only": second_d,
                                "direct_call_window": instruction_window(target, 0x82523860, 0x8252387C),
                                "reward_windows": [instruction_window(target, 0x82523A28, 0x82523A9C)],
                                "world_map_windows": [instruction_window(target, 0x82523CE8, 0x82523D10)],
                                "typed_visitors": {"scalar": scalar_visitor, "boolean_like": boolean_visitor},
                                "classification": "one independent target-native field-consumer family"},
        direct_callers={"donor": callers_d, "target": callers_t,
                        "smaller_target_caller": {"window": instruction_window(target, 0x8251BCF0, 0x8251BD68),
                                                  "return_consumed": False,
                                                  "context": "allocation/initial-population sequence only; no constructor/type proof"}},
        role_classification={"property_registration": False, "keyed_load_or_materialization": True,
                             "visitor_direction": "unresolved", "runtime_reward_granting": False,
                             "runtime_map_marker_behavior": False, "serialization_direction": "unresolved",
                             "reward_storage": "opaque 32-bit words", "appear_storage": "normalized 0/1 byte"},
        independence_observations=observations,
        dispositions={"primary": "independently-corroborated-role", "mapping": "review-triggered",
                      "mapping_result": "approved correspondence unchanged; semantic attribution correction only",
                      "reservation": "retained", "reservation_reason": "single-independent-support-class",
                      "role_label": {"kind": "human-review candidate",
                                     "value": "conditional keyed reward/world-map field materializer"},
                      "canonical_name": "not-authorized"},
        contradictions=["SetObjectiveTag fourth-terminal literal-use attribution is false",
                        "Phase 2F H1 literal-consumer-callee attribution is false for RewardMoney/RewardRenown"],
        unresolved=["reward scalar signedness/type", "visitor direction", "complete object/type identity",
                    "runtime reward granting", "runtime world-map behavior"],
        input_identities=inputs.identities())


def shared_property_pattern(inputs, images, selection):
    return sources.envelope(
        "shared-property-pattern", selection,
        comparison={
            "common": ["complete NUL-terminated keys", "0x811C9DC5-seeded key transform",
                       "generic nullable property lookup", "writes/returns feeding bounded object fields"],
            "oxygen": "direct (context,key,&field) conditional word-copy helper plus +0x38 -> +0x34 initialization",
            "world_reward": "handle resolver followed by scalar-return or normalized-Boolean-return lookup helpers",
            "conclusion": "both are generic property-bag/schema loading or visitation patterns, not runtime gameplay calculations",
            "not_identical_support_topology": True,
            "cross_packet_similarity_is_independent_vote": False,
            "generic_engine_vs_fable_context": "machinery is generic; only complete keys and proven offsets supply Fable-specific field context",
        },
        adversarial={"same_strings_prove_same_role": False,
                     "same_helper_family_proves_mapping": False,
                     "property_metadata_proves_gameplay": False,
                     "field_labels_prove_complete_type": False},
        input_identities=inputs.identities())
