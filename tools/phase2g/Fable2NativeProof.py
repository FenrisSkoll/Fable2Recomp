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
        record(inputs, "C-fourth-terminal-r6", "C",
               "The SetObjectiveTag terminal is an incidental donor r6 high-half intermediate; target 0x820C0000 is an interior pointer into different bytes.",
               "contradictory", inputs.ref(xrefs, "/references"), material=False, compatible=False,
               detail={"terminal_id": "S-26C37A0D8DC5C81610D44E94",
                       "donor_xref": "X-755D156689799A74601CB30A",
                       "donor_address": "0x820C0000", "target_address": "0x820C0000",
                       "disposition": "alias-reconciled-not-a-semantic-vote"}),
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


def analyze(replay=False):
    pins = sources.source_bindings()
    sources.write(sources.DOC / "evidence/source-pins.json", pins, replay)
    inputs = sources.Inputs(pins)
    ledger = sources.envelope("independence-ledger", pins["overlay_selection"],
                              **consumed_ledger(inputs), consumed_sources=sorted(inputs.used))
    artifact = sources.write(sources.OUT / "consumed-evidence/independence-ledger.json", ledger, replay)
    images = native_analysis.load_images(inputs)
    hammer = native_analysis.hammer_packet(inputs, images, sys.modules[__name__], pins["overlay_selection"])
    hammer_artifact = sources.write(sources.OUT / "hammercombat/native-proof-packet.json", hammer, replay)
    print("PASS Phase 2G consumed-evidence ledger:", len(ledger["records"]), flush=True)
    print("PASS Phase 2G HammerCombat native proof:", hammer["dispositions"]["primary"], flush=True)
    return {"artifacts": [artifact, hammer_artifact], "consumed_sources": sorted(inputs.used)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    analyze(arguments.check)
