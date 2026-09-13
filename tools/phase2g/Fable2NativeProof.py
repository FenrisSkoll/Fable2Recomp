"""Bounded Phase 2G native semantic proof records; no mapping or naming feedback."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import Fable2NativeProofSources as sources
import Fable2NativeProofAnalysis as native_analysis

CLASSES = (
    "mapping-consumed",
    "correlated-with-mapping",
    "independent-target-native",
    "independent-cross-build-behavior",
    "context-only",
    "contradictory",
    "unresolved",
)
INDEPENDENT_CLASSES = {"independent-target-native", "independent-cross-build-behavior"}
PACKETS = {
    "A": {
        "terminal_ids": ["S-FCEF3DCAA6D1D5FB2EF8AB8F"],
        "owner": "0x8229B308:0x8229B038",
        "reservation": "internal-code-region-dependent",
    },
    "B": {
        "terminal_ids": [
            "S-31139DC943017A090C85C7E0",
            "S-818A834A4CED040235B7B86D",
            "S-F48219FB96F897D4D426B8C0",
        ],
        "owner": "0x82406F98:0x82405868",
        "reservation": "single-independent-support-class",
    },
    "C": {
        "terminal_ids": [
            "S-202449BD00F31D43FE6EBBA4",
            "S-26C37A0D8DC5C81610D44E94",
            "S-36653A3F9B530DB894F7EE5F",
            "S-53D9FAFB09CA0C7E1FC73807",
        ],
        "owner": "0x825240E8:0x82522C10",
        "reservation": "single-independent-support-class",
    },
}


def classify_observation(*, mapping_consumed=False, correlated=False, target_native=False,
                         cross_build=False, context_only=False, contradictory=False):
    positive = [mapping_consumed, correlated, target_native, cross_build, context_only, contradictory]
    if sum(bool(value) for value in positive) > 1:
        raise ValueError("Observation cannot receive more than one independence class")
    if mapping_consumed:
        return "mapping-consumed"
    if correlated:
        return "correlated-with-mapping"
    if target_native:
        return "independent-target-native"
    if cross_build:
        return "independent-cross-build-behavior"
    if context_only:
        return "context-only"
    if contradictory:
        return "contradictory"
    return "unresolved"


def proof_eligible(observation):
    return (observation["independence_class"] in INDEPENDENT_CLASSES and
            observation.get("material", False) and
            observation.get("compatible", False) and
            observation.get("owned", False) and
            not observation.get("circular", True))


def semantic_fixture(*, complete=True, interior=False, empty=False, readonly=True,
                     terminated=True, compatible_role=True, circular=False,
                     body_compatible=True, caller_compatible=True, field_compatible=True):
    reasons = []
    if not complete:
        reasons.append("prefix")
    if interior:
        reasons.append("interior")
    if empty:
        reasons.append("empty")
    if not readonly:
        reasons.append("writable")
    if not terminated:
        reasons.append("unterminated")
    if circular:
        reasons.append("circular-support")
    if not compatible_role:
        reasons.append("different-consumer-role")
    if body_compatible and not caller_compatible:
        reasons.append("incompatible-caller-context")
    if not field_compatible:
        reasons.append("incompatible-field-offset-or-width")
    if any(reason in reasons for reason in ("incompatible-caller-context", "different-consumer-role",
                                             "incompatible-field-offset-or-width")):
        disposition = "semantic-conflict-quarantined"
    elif reasons:
        disposition = "rejected"
    else:
        disposition = "independent-eligible"
    return {"disposition": disposition, "reasons": reasons}


def record(inputs, identifier, packet, claim, independence_class, provenance,
           *, material=False, compatible=True, owned=True, circular=False, detail=None):
    sources.require(independence_class in CLASSES, "Unknown independence class")
    value = {
        "id": identifier,
        "packet": packet,
        "claim": claim,
        "independence_class": independence_class,
        "provenance": provenance,
        "material": material,
        "compatible": compatible,
        "owned": owned,
        "circular": circular,
    }
    if detail is not None:
        value["detail"] = detail
    value["proof_eligible"] = proof_eligible(value)
    return value


def consumed_ledger(inputs):
    accepted = "docs/fable2-prototype-archaeology/phase2a/evidence/prototype-correspondence-accepted.json"
    candidates = "out/prototype-archaeology/phase2c/reference-candidates.json"
    semantic = "out/prototype-archaeology/phase2c/completion/semantic-final.json"
    packets = "out/prototype-archaeology/phase2d/packets.json"
    ledger = "docs/fable2-prototype-archaeology/phase2d/evidence/human-decision-ledger.json"
    delta = "docs/fable2-prototype-archaeology/phase2e/evidence/approved-overlay-delta.json"
    review = "docs/fable2-prototype-archaeology/phase2f/evidence/high-value-review.json"
    xrefs = "out/prototype-archaeology/phase2b/semantic-xrefs.json"
    inventory = "out/prototype-archaeology/phase2b/semantic-inventory.json"
    for path in (accepted, candidates, semantic, packets, ledger, delta, review, xrefs, inventory):
        inputs.read(path)

    observations = [
        record(inputs, "A-owner-correspondence", "A",
               "Owner body, HammerCombat identity, CFG and exact raw equality approved the Phase 2A owner mapping.",
               "mapping-consumed", inputs.ref(accepted, "/records/809",
               "BDDB830B46109840F8BFB63627CE37CEA5AF8D2A04F3A6CF7A4DFE50F52DC058")),
        record(inputs, "A-reserved-callee-correspondence", "A",
               "The 0x7C callee body, empty fallback, caller and neighbourhood established the reserved callee mapping.",
               "mapping-consumed", inputs.ref(packets, "/records/6",
               "E2FF8F2E4DA73B5806EC41CC2865979FBF5877E20A02EF94E91D860F6F0C47CB")),
        record(inputs, "A-comparator-equivalence", "A",
               "The identical internal comparator regions were a required Phase 2C/2D behavior gate.",
               "mapping-consumed", inputs.ref(candidates, "/proposals/12",
               "6DD74BBB1F90AEB695952D87731970B1FEFD2C00745F40D48C75CAFA9B1C09B3"), owned=False),
        record(inputs, "A-phase2f-semantic-route", "A",
               "Same literal role and newly approved callee supplied the Phase 2F semantic route.",
               "correlated-with-mapping", inputs.ref(review, "/selected/0")),
        record(inputs, "B-owner-body-and-keys", "B",
               "Complete owner body, three key identities, field/argument/return roles and helper topology approved the mapping.",
               "mapping-consumed", inputs.ref(packets, "/records/68",
               "6873CCA3463EEDAE82F36B8099C0F37125C162113A1BB2FC185306D5729816F8")),
        record(inputs, "B-three-semantic-terminals", "B",
               "The three oxygen terminal/XREF pairs reuse the canonicalized references used by proposal approval.",
               "correlated-with-mapping", inputs.ref(semantic, "/records")),
        record(inputs, "B-duplicate-user-topology", "B",
               "The second donor/target user population for each key was consumed as reference distinctiveness.",
               "mapping-consumed", inputs.ref(ledger, "/records/4")),
        record(inputs, "C-owner-body-and-keys", "C",
               "Complete owner body, three complete key identities, field/argument/return roles and six helper calls approved the mapping.",
               "mapping-consumed", inputs.ref(packets, "/records/128",
               "3D19299998B3D2F7CCA86622038FEBF50CF14E0DA6FC27E3DE3C3E4419942EFB")),
        record(inputs, "C-three-complete-key-terminals", "C",
               "RewardMoney, RewardRenown and AppearOnWorldMap target observations reuse canonicalized proposal evidence.",
               "correlated-with-mapping", inputs.ref(semantic, "/records")),
        record(inputs, "C-duplicate-user-topology", "C",
               "The second donor/target user population for each complete key was consumed as reference distinctiveness.",
               "mapping-consumed", inputs.ref(ledger, "/records/6")),
        record(inputs, "all-owner-approval", "cross-packet",
               "Phase 2E adopted the three additions only as analysis-only noncanonical mappings and retained reservations.",
               "context-only", inputs.ref(delta, "/actions")),
    ]
    sources.require(all(observation["independence_class"] in CLASSES for observation in observations),
                    "Unclassified evidence observation")
    sources.require(len({observation["id"] for observation in observations}) == len(observations),
                    "Duplicate evidence observation")
    return {
        "classes": list(CLASSES),
        "records": observations,
        "counts": {name: sum(row["independence_class"] == name for row in observations)
                   for name in CLASSES},
        "independent_proof_count": sum(row["proof_eligible"] for row in observations),
        "rule": "Each observation has exactly one class; consumed/correlated observations never vote independently.",
    }


def complete_ledger(base, packets):
    observations = list(base["records"])
    for packet in packets:
        observations.extend(packet["independence_observations"])
    sources.require(len({row["id"] for row in observations}) == len(observations),
                    "Evidence observation appears more than once")
    return {
        "classes": list(CLASSES),
        "records": observations,
        "counts": {name: sum(row["independence_class"] == name for row in observations)
                   for name in CLASSES},
        "independent_proof_count": sum(row["proof_eligible"] for row in observations),
        "rule": "Each observation has exactly one class and appears once in this vote ledger; packet copies are presentational only.",
    }


def expanded_scope(selection, inputs):
    records = [
        ("A", "build-23.12.02.0330", "0x8229B488", "reserved direct callee"),
        ("A", "canonical-tu1", "0x8229B1B8", "reserved direct callee"),
        ("A", "build-23.12.02.0330", "0x8226DB80", "direct comparator dependency; internal region"),
        ("A", "canonical-tu1", "0x8226D7F8", "direct comparator dependency; internal region"),
        ("A", "canonical-tu1", "0x822756E8", "direct owner caller and byte-result comparator"),
        ("A", "canonical-tu1", "0x8285A850", "direct owner caller; repeated-reference control"),
        ("A", "canonical-tu1", "0x8285C6A8", "direct owner caller and byte-result store"),
        ("B", "build-23.12.02.0330", "0x823ADDA8", "direct keyed-load helper"),
        ("B", "canonical-tu1", "0x823AD468", "direct keyed-load helper"),
        ("B", "build-23.12.02.0330", "0x821F3F00", "direct key-transform dependency; internal region"),
        ("B", "canonical-tu1", "0x821F3D58", "direct key-transform dependency; internal region"),
        ("B", "build-23.12.02.0330", "0x8238D020", "direct attachment helper"),
        ("B", "canonical-tu1", "0x8238D4B8", "direct attachment helper"),
        ("B", "build-23.12.02.0330", "0x82407030", "adjacent same-string/different-role control"),
        ("B", "canonical-tu1", "0x82405900", "adjacent same-string/different-role control"),
        ("C", "build-23.12.02.0330", "0x821B2528", "direct two-word handle resolver"),
        ("C", "canonical-tu1", "0x821B24F8", "direct two-word handle resolver"),
        ("C", "build-23.12.02.0330", "0x823C0588", "direct scalar keyed lookup"),
        ("C", "canonical-tu1", "0x823BF820", "direct scalar keyed lookup"),
        ("C", "build-23.12.02.0330", "0x82310448", "direct Boolean keyed lookup"),
        ("C", "canonical-tu1", "0x82310290", "direct Boolean keyed lookup"),
        ("C", "build-23.12.02.0330", "0x82524CA0", "direct owner caller and same-field visitor context"),
        ("C", "canonical-tu1", "0x825237C8", "direct owner caller and independent same-field visitor"),
        ("C", "build-23.12.02.0330", "0x8251D1C0", "direct owner caller; allocation/population context"),
        ("C", "canonical-tu1", "0x8251BCE8", "direct owner caller; allocation/population context"),
        ("C", "canonical-tu1", "0x824807C8", "direct scalar field visitor"),
        ("C", "canonical-tu1", "0x82A1CE48", "direct Boolean-like field visitor"),
        ("C", "canonical-tu1", "0x82A006C8", "scalar lookup dependency"),
        ("C", "canonical-tu1", "0x82A003B0", "Boolean lookup dependency"),
    ]
    return sources.envelope("expanded-scope", selection,
                            records=[{"packet": packet, "build": build, "address": address,
                                      "reason": reason, "bounded": True}
                                     for packet, build, address, reason in records],
                            counts={"expansions": len(records),
                                    "by_packet": {packet: sum(row[0] == packet for row in records)
                                                  for packet in PACKETS}},
                            rule="Every inspected function or internal region outside the three primary owners is listed.",
                            input_identities=inputs.identities())


def negative_controls(selection, inputs):
    prior_path = "out/prototype-archaeology/phase2f/negative-controls.json"
    exclusion_path = "out/prototype-archaeology/phase2e/exclusion-audit.json"
    delta_path = "docs/fable2-prototype-archaeology/phase2e/evidence/approved-overlay-delta.json"
    prior = inputs.read(prior_path)
    exclusions = inputs.read(exclusion_path)
    delta = inputs.read(delta_path)
    real = [row for row in prior["records"] if row["kind"] == "real-collision"]
    sources.require(len(real) == 3, "Suppression collision population changed")
    sources.require(exclusions["counts"] == {
        "held_original_strong_excluded": 3, "physics_candidates_excluded": 2,
        "probable_proposals_excluded": 715, "unapproved_ledger_records_excluded": 5},
        "Excluded population changed")
    actions = {row["action_id"]: row for row in delta["actions"]}
    expected_suppressions = [
        ("P2E:suppress:0x82631A30:0x82950A98", "Navigator", "Controlled"),
        ("P2E:suppress:0x828EA448:0x82681198", "TROLL_FOOTSTEP", "DESTROY_ENTITY"),
        ("P2E:suppress:0x83062950:0x83060C30", "__vspltb", "__vcfsx"),
    ]
    for identifier, _, _ in expected_suppressions:
        sources.require(identifier in actions and actions[identifier]["action"] == "suppress-semantic-transport",
                        "Suppression changed: " + identifier)
    sources.require("P2E:0x83062950:0x83060CD8" in actions,
                    "Corrected vector route changed")
    fixtures = {
        "valid-independent": semantic_fixture(),
        "same-string-different-role": semantic_fixture(compatible_role=False),
        "same-helper-incompatible-field": semantic_fixture(field_compatible=False),
        "compatible-body-incompatible-caller": semantic_fixture(caller_compatible=False),
        "prefix": semantic_fixture(complete=False),
        "interior": semantic_fixture(interior=True),
        "empty": semantic_fixture(empty=True),
        "writable": semantic_fixture(readonly=False),
        "unterminated": semantic_fixture(terminated=False),
        "circular-owner-callee": semantic_fixture(circular=True),
    }
    return sources.envelope(
        "negative-controls", selection, synthetic=fixtures,
        real_collision_controls=[{"action_id": identifier, "donor_text": left,
                                  "target_text": right, "result": "suppression-retained"}
                                 for identifier, left, right in expected_suppressions],
        corrected_vector_route={"suppressed_collision": "0x83062950:0x83060C30",
                                "approved_route": "0x83062950:0x83060CD8",
                                "unchanged": True},
        exclusions={"physics": ["0x82631A30:0x82630C30", "0x829506B0:0x82950A98"],
                    "held_strong": ["0x82BC43E8:0x82BC3FA8", "0x82E510E0:0x82E515D0",
                                    "0x82FB6620:0x82FB6C50"],
                    "probable_count": 715, "all_remain_excluded": True,
                    "address_preserving_semantic_confusion_vote": False},
        mapping_mutation_on_conflict=False,
        prior_controls=inputs.ref(prior_path), exclusion_audit=inputs.ref(exclusion_path),
        input_identities=inputs.identities())


def review_selection(selection, inputs, packets):
    rows = []
    for packet in sorted(packets, key=lambda row: row["packet"]):
        label = packet["dispositions"]["role_label"]
        rows.append({"packet": packet["packet"], "primary_terminal": packet["terminal_ids"][0],
                     "primary_disposition": packet["dispositions"]["primary"],
                     "mapping_disposition": packet["dispositions"]["mapping"],
                     "reservation_disposition": packet["dispositions"]["reservation"],
                     "role_label": label, "canonical_name": "not-authorized",
                     "selected_for_human_review": label["kind"] == "human-review candidate"})
    sources.require([row["packet"] for row in rows] == ["A", "B", "C"],
                    "Review selection order changed")
    return sources.envelope("review-selection", selection, records=rows,
                            counts={"packets": 3, "human_review_candidates":
                                    sum(row["selected_for_human_review"] for row in rows)},
                            ordering="packet-id ascending; no randomized or score-based selection",
                            input_identities=inputs.identities())


def analyze(replay=False):
    pins = sources.source_bindings()
    sources.write(sources.DOC / "evidence/source-pins.json", pins, replay)
    inputs = sources.Inputs(pins)
    base_ledger = consumed_ledger(inputs)
    images = native_analysis.load_images(inputs)
    hammer = native_analysis.hammer_packet(inputs, images, sys.modules[__name__], pins["overlay_selection"])
    hammer_artifact = sources.write(sources.OUT / "hammercombat/native-proof-packet.json", hammer, replay)
    oxygen = native_analysis.oxygen_packet(inputs, images, sys.modules[__name__], pins["overlay_selection"])
    oxygen_artifact = sources.write(sources.OUT / "oxygen/native-proof-packet.json", oxygen, replay)
    world_reward = native_analysis.world_reward_packet(
        inputs, images, sys.modules[__name__], pins["overlay_selection"])
    world_artifact = sources.write(
        sources.OUT / "world-map-reward/native-proof-packet.json", world_reward, replay)
    shared = native_analysis.shared_property_pattern(inputs, images, pins["overlay_selection"])
    shared_artifact = sources.write(
        sources.OUT / "shared-helper/property-pattern.json", shared, replay)
    scope = expanded_scope(pins["overlay_selection"], inputs)
    scope_artifact = sources.write(sources.OUT / "expanded-function-scope.json", scope, replay)
    controls = negative_controls(pins["overlay_selection"], inputs)
    controls_artifact = sources.write(sources.OUT / "negative-controls/results.json", controls, replay)
    selection = review_selection(pins["overlay_selection"], inputs, (hammer, oxygen, world_reward))
    selection_artifact = sources.write(sources.OUT / "review-selection.json", selection, replay)
    ledger = sources.envelope("independence-ledger", pins["overlay_selection"],
                              **complete_ledger(base_ledger, (hammer, oxygen, world_reward)),
                              input_identities=inputs.identities())
    artifact = sources.write(sources.OUT / "consumed-evidence/independence-ledger.json", ledger, replay)
    print("PASS Phase 2G consumed-evidence ledger:", len(ledger["records"]), flush=True)
    print("PASS Phase 2G HammerCombat native proof:", hammer["dispositions"]["primary"], flush=True)
    print("PASS Phase 2G oxygen native proof:", oxygen["dispositions"]["primary"], flush=True)
    print("PASS Phase 2G world/reward native proof:", world_reward["dispositions"]["primary"], flush=True)
    return {"artifacts": [artifact, hammer_artifact, oxygen_artifact, world_artifact, shared_artifact,
                          scope_artifact, controls_artifact, selection_artifact],
            "consumed_sources": sorted(inputs.used)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    analyze(arguments.check)
