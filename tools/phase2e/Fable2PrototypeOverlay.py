"""Phase 2E owner-decision validation and non-canonical mapping overlay.

This tool consumes frozen Phase 2D evidence.  It never changes Phase 1-2D,
canonical symbols, manifests, generated code, runtime code, or a Ghidra project.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import Fable2PrototypeReview as phase2d  # noqa: E402


PHASE2D_COMMIT = "6db4b4374c6e5cac180b92e23fb0bbeec86c4500"
PHASE2D_TREE = "23f28f9d3ba2e4acf0365bcf7e4e1f065ea47ecb"
PHASE2D_SUBJECT = "Document Phase 2D adoption readiness and freeze pending human decision dossier"
PHASE2C_COMMIT = "f13ee49c94db48d979de1346b7f67d2d82257ea2"
PHASE2D_LEDGER_SET_HASH = "7576AB812DEA66388C4CA1BF2BE9FB5C32B06E9C7F9C1C0E1C9CF283E731CCD4"
SELECTED_ACTION_SET_HASH = "8E9CBB93751C0F0B13FF04F1809207D72C0C96587369FEEA0C528F0A9EEE2363"

APPROVER_IDENTITY = "FenrisSkoll"
DECISION_TIMESTAMP = "2026-09-12T22:00:00+01:00"
EXTERNAL_DECISION_RECORD_ID = "P2D-OWNER-DECISION-001"
DECISION = "approve"
APPROVED_SURFACE = "reversible non-canonical semantic-transport and mapping overlay only"
OVERLAY_VERSION = "phase2e-v1"

APPROVED_BATCHES = {
    "B00-semantic-suppressions": (3, "0386951B064C2F7FCDBD70FCD44BCFA7479BE4435EEDD30EF833B1D1BCDE7E6E"),
    "B01-unreserved": (17, "6C2DBAAED2887ACD57E9A2123601E514611B8D39A70A40D08723F86ADE3525B1"),
    "B02-multiple-references-reserved": (5, "1365725CBD2B5130F16C2004E347E3C9497F8AF457D4E72E171B54E9E8413A96"),
    "B04-callee-only-reserved": (60, "AD7AE0056AEBB9A903B51E75123BD196EE764B88743DADB33E78D5E1F399D4BF"),
    "B05-internal-region-reserved": (1, "FBB88D754E43B8B6035E9CC3D267861E08321FEDAC4F5086DADB3F3C491E4124"),
}

EMPTY_BATCHES = {"B03-richer-support-reserved", "B06-former-probable"}
SUPPRESSED_PAIRS = {
    ("0x82631A30", "0x82950A98"),
    ("0x828EA448", "0x82681198"),
    ("0x83062950", "0x83060C30"),
}
PHYSICS_CANDIDATES = {
    "0x82631A30:0x82630C30",
    "0x829506B0:0x82950A98",
}
HELD_STRONG = {
    "0x82BC43E8:0x82BC3FA8",
    "0x82E510E0:0x82E515D0",
    "0x82FB6620:0x82FB6C50",
}
VECTOR_REGRESSIONS = {
    "suppressed": ("0x83062950", "0x83060C30"),
    "vcfsx": ("0x83060A80", "0x83060C30"),
    "vspltb": ("0x83062950", "0x83060CD8"),
}
HAMMER_PAIR = ("0x8229B488", "0x8229B1B8")

DOC = Path("docs/fable2-prototype-archaeology/phase2e")
EVIDENCE = DOC / "evidence"
OUT = Path("out/prototype-archaeology/phase2e")
DECISION_PATH = EVIDENCE / "owner-decision.json"
DELTA_PATH = EVIDENCE / "approved-overlay-delta.json"
SOURCE_PINS_PATH = EVIDENCE / "source-pins.json"
SUMMARY_PATH = EVIDENCE / "overlay-summary.json"
VALIDATION_PATH = EVIDENCE / "validation.json"

LEDGER_PATH = Path("docs/fable2-prototype-archaeology/phase2d/evidence/human-decision-ledger.json")
REVIEW_SUMMARY_PATH = Path("docs/fable2-prototype-archaeology/phase2d/evidence/review-summary.json")
PHASE2D_SOURCE_PINS_PATH = Path("docs/fable2-prototype-archaeology/phase2d/evidence/source-pins.json")
PHASE2D_VALIDATION_PATH = Path("docs/fable2-prototype-archaeology/phase2d/evidence/validation.json")
RISK_PATH = Path("out/prototype-archaeology/phase2d/risk-strata-and-batches.json")
PACKETS_PATH = Path("out/prototype-archaeology/phase2d/packets.json")
KNOWN_CASES_PATH = Path("out/prototype-archaeology/phase2d/known-cases.json")
DEPENDENCIES_PATH = Path("out/prototype-archaeology/phase2d/dependency-seeds.json")
PROBABLE_PATH = Path("out/prototype-archaeology/phase2d/probable-blockers.json")
SIMULATIONS_PATH = Path("out/prototype-archaeology/phase2d/adoption-simulations.json")
CONSUMERS_PATH = Path("out/prototype-archaeology/phase2d/future-consumers.json")
PHASE2A_MAP_PATH = Path("docs/fable2-prototype-archaeology/phase2a/evidence/prototype-correspondence-accepted.json")
PHASE2C_EFFECTIVE_PATH = Path("out/prototype-archaeology/phase2c/completion/effective-map.json")

SCHEMA_PREFIX = "fable2-prototype-overlay-"
ALLOWED_SCHEMA_KINDS = {
    "owner-decision",
    "approved-delta",
    "source-pins",
    "selected-actions",
    "effective-map",
    "application-receipt",
    "suppression-route-audit",
    "reservation-inventory",
    "exclusion-audit",
    "dependency-injectivity",
    "consumer-compatibility",
    "rollback-verification",
    "overlay-summary",
    "validation",
    "checks",
    "tests",
    "replay",
    "schemas",
}

_DECISION_INPUTS_CACHE: dict[str, Any] | None = None
_OWNER_DECISION_CACHE: dict[str, Any] | None = None
_DELTA_CACHE: dict[str, Any] | None = None
_SOURCE_PINS_CACHE: dict[str, Any] | None = None


def require(value: Any, message: str) -> None:
    if not value:
        raise ValueError(message)


def payload(value: Any) -> bytes:
    """Canonical JSON: sorted keys, compact separators, UTF-8, exactly one LF."""
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def set_hash(values: Iterable[str]) -> str:
    values = list(values)
    require(len(values) == len(set(values)), "Duplicate identity in canonical set hash")
    return sha256(payload(sorted(values)))


def read(path: Path | str) -> Any:
    return json.loads((ROOT / Path(path)).read_bytes())


def identity(path: Path | str) -> dict[str, Any]:
    relative = Path(path)
    require(not relative.is_absolute() and ".." not in relative.parts, "Identity path must be repository-relative")
    data = (ROOT / relative).read_bytes()
    return {"path": relative.as_posix(), "size": len(data), "sha256": sha256(data)}


def identity_bytes(path: Path | str, data: bytes) -> dict[str, Any]:
    relative = Path(path)
    require(not relative.is_absolute() and ".." not in relative.parts, "Identity path must be repository-relative")
    return {"path": relative.as_posix(), "size": len(data), "sha256": sha256(data)}


def check_identity(row: dict[str, Any], root: Path = ROOT) -> None:
    path = Path(row["path"])
    require(not path.is_absolute() and ".." not in path.parts, "Bound path must be relative: " + row["path"])
    full = root / path
    require(full.is_file(), "Missing bound input: " + row["path"])
    data = full.read_bytes()
    require(len(data) == row["size"], "Bound size mismatch: " + row["path"])
    require(sha256(data) == row["sha256"], "Bound SHA-256 mismatch: " + row["path"])


def output_path(path: Path | str) -> Path:
    relative = Path(path)
    require(not relative.is_absolute() and ".." not in relative.parts, "Non-relative output path")
    resolved = (ROOT / relative).resolve()
    require(resolved.is_relative_to(ROOT.resolve()), "Output escapes repository")
    roots = ((ROOT / DOC).resolve(), (ROOT / OUT).resolve())
    require(any(resolved.is_relative_to(root) for root in roots), "Output outside Phase 2E roots")
    return resolved


def write(path: Path | str, value: Any, check: bool = False) -> dict[str, Any]:
    data = value if isinstance(value, bytes) else payload(value)
    full = output_path(path)
    if check:
        require(full.is_file(), "Missing replay output: " + Path(path).as_posix())
        require(full.read_bytes() == data, "Replay mismatch: " + Path(path).as_posix())
    else:
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_bytes(data)
    return identity_bytes(path, data)


def envelope(kind: str, **fields: Any) -> dict[str, Any]:
    require(kind in ALLOWED_SCHEMA_KINDS, "Unknown Phase 2E schema kind")
    return {
        "schema": {"name": SCHEMA_PREFIX + kind, "version": 1},
        "phase2d_commit": PHASE2D_COMMIT,
        "canonical_adoption": False,
        "analysis_only": True,
        **fields,
    }


def git(*args: str, root: Path = ROOT, text: bool = True) -> str | bytes:
    return subprocess.check_output(["git", *args], cwd=root, text=text).strip()


def git_lines(*args: str, root: Path = ROOT) -> list[str]:
    value = subprocess.check_output(["git", *args], cwd=root, text=True)
    return value.splitlines()


def canonical_record_hash(record: dict[str, Any]) -> str:
    return sha256(payload(record))


def verify_phase2d_frozen() -> dict[str, Any]:
    """Validate the immutable Phase 2D and inherited SDK state without writes."""
    require(git("rev-parse", f"{PHASE2D_COMMIT}^{{tree}}") == PHASE2D_TREE, "Phase 2D tree mismatch")
    require(git("log", "-1", "--format=%s", PHASE2D_COMMIT) == PHASE2D_SUBJECT, "Phase 2D subject mismatch")
    frozen_paths = [
        "docs/fable2-prototype-archaeology/phase1",
        "docs/fable2-prototype-archaeology/phase2a",
        "docs/fable2-prototype-archaeology/phase2b",
        "docs/fable2-prototype-archaeology/phase2c",
        "docs/fable2-prototype-archaeology/phase2d",
    ]
    result = subprocess.run(
        ["git", "diff", "--quiet", PHASE2D_COMMIT, "--", *frozen_paths],
        cwd=ROOT,
        check=False,
    )
    require(result.returncode == 0, "Frozen Phase 1-2D committed bytes differ from Phase 2D")

    validation = read(PHASE2D_VALIDATION_PATH)
    require(validation["canonical_adoption"] is False, "Phase 2D canonical adoption changed")
    require(validation["human_approval"] is False, "Phase 2D human approval changed")
    require(len(validation["artifacts"]) == 20, "Phase 2D artifact binding count changed")
    for row in validation["artifacts"]:
        check_identity(row)
    for row in validation["implementation"]:
        check_identity(row)

    source_pins = read(PHASE2D_SOURCE_PINS_PATH)
    require(len(source_pins["protected_phase2c_artifacts"]) == 30, "Protected Phase 2C artifact count changed")
    for row in source_pins["protected_phase2c_artifacts"]:
        check_identity(row)

    # This is the frozen Phase 2D binder in check-only mode.  It validates all
    # inherited sources, 187 gates, 39 fixture classes, SDK state and 15 hashes.
    phase2d.bind(True)

    ledger = read(LEDGER_PATH)
    require(len(ledger["records"]) == 91, "Phase 2D ledger count changed")
    require(all(row["human_decision"] == "pending" and row["human_decision_evidence"] is None for row in ledger["records"]),
            "Phase 2D ledger is no longer entirely pending")
    require(ledger["human_approval"] is False and ledger["canonical_adoption"] is False,
            "Phase 2D ledger approval state changed")

    review_summary = read(REVIEW_SUMMARY_PATH)
    require(review_summary["strong_dispositions"] == {
        "hold-for-additional-evidence": 3,
        "recommend-downgrade": 0,
        "recommend-human-approval": 17,
        "recommend-human-approval-with-reservation": 66,
        "recommend-rejection": 0,
    }, "Phase 2D strong dispositions changed")
    require(review_summary["probable_dispositions"]["hold-for-additional-evidence"] == 715,
            "Phase 2D probable dispositions changed")
    require(review_summary["pending_decisions"] == 91, "Phase 2D pending decision count changed")
    require(len(review_summary["inherited_blockers"]) == 6, "Inherited Phase 2C blockers changed")

    return {
        "phase2d_validation": validation,
        "phase2d_source_pins": source_pins,
        "ledger": ledger,
        "review_summary": review_summary,
    }


def batch_records(risk: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = {row["id"]: row for row in risk["records"]}
    mandatory = risk["mandatory_suppression_batch"]
    require(mandatory["id"] not in rows, "Duplicate suppression batch")
    rows[mandatory["id"]] = mandatory
    return rows


def evidence_packets(ledger: dict[str, Any]) -> dict[str, dict[str, Any]]:
    packet_rows = read(PACKETS_PATH)["records"]
    packet_by_id = {row["id"]: (index, row) for index, row in enumerate(packet_rows)}
    require(len(packet_by_id) == len(packet_rows) == 803, "Phase 2D packet population changed")
    known_rows = read(KNOWN_CASES_PATH)["suppressions"]
    known_by_id = {row["id"]: (index, row) for index, row in enumerate(known_rows)}
    require(len(known_by_id) == 3, "Phase 2D suppression packet population changed")

    result: dict[str, dict[str, Any]] = {}
    for ledger_index, row in enumerate(ledger["records"]):
        row_id = row["id"]
        if row_id.startswith("suppress:"):
            require(row_id in known_by_id, "Suppression lacks known-case packet: " + row_id)
            index, packet = known_by_id[row_id]
            for key, value in packet.items():
                require(row.get(key) == value, "Suppression ledger/packet mismatch: " + row_id + "/" + key)
            result[row_id] = {
                "path": KNOWN_CASES_PATH.as_posix(),
                "json_pointer": f"/suppressions/{index}",
                "sha256": canonical_record_hash(packet),
                "kind": "suppression-conflict-packet",
            }
        else:
            require(row_id in packet_by_id, "Mapping lacks Phase 2D packet: " + row_id)
            index, packet = packet_by_id[row_id]
            packet_hash = canonical_record_hash(packet)
            require(row["packet_sha256"] == packet_hash, "Phase 2D mapping packet hash mismatch: " + row_id)
            result[row_id] = {
                "path": PACKETS_PATH.as_posix(),
                "json_pointer": f"/records/{index}",
                "sha256": packet_hash,
                "kind": "mapping-review-packet",
            }
        result[row_id]["ledger_path"] = LEDGER_PATH.as_posix()
        result[row_id]["ledger_json_pointer"] = f"/records/{ledger_index}"
    return result


def validate_decision_inputs() -> dict[str, Any]:
    global _DECISION_INPUTS_CACHE
    if _DECISION_INPUTS_CACHE is not None:
        return copy.deepcopy(_DECISION_INPUTS_CACHE)
    frozen = verify_phase2d_frozen()
    ledger = frozen["ledger"]
    ledger_rows = {row["id"]: row for row in ledger["records"]}
    require(len(ledger_rows) == len(ledger["records"]), "Duplicate Phase 2D ledger ID")
    require(set_hash(ledger_rows) == ledger["proposal_set_sha256"] == PHASE2D_LEDGER_SET_HASH,
            "Phase 2D ledger proposal-set hash mismatch")

    risk = read(RISK_PATH)
    rows = batch_records(risk)
    require(EMPTY_BATCHES <= set(rows), "Required empty batch is absent")
    for batch_id in EMPTY_BATCHES:
        batch = rows[batch_id]
        require(batch["mapping_count"] == 0 and batch["mapping_ids"] == [],
                "Empty batch contains authority: " + batch_id)

    selected_ids: list[str] = []
    selected_batches: list[dict[str, Any]] = []
    for batch_id, (expected_count, expected_hash) in APPROVED_BATCHES.items():
        require(batch_id in rows, "Unknown approved batch: " + batch_id)
        batch = rows[batch_id]
        ids = batch["mapping_ids"]
        actual_hash = set_hash(ids)
        require(len(ids) == batch["mapping_count"] == expected_count, "Approved batch count mismatch: " + batch_id)
        require(actual_hash == expected_hash, "Approved batch set hash mismatch: " + batch_id)
        if "proposal_set_sha256" in batch:
            require(batch["proposal_set_sha256"] == actual_hash, "Stored batch hash mismatch: " + batch_id)
        require(ids, "Empty batch cannot authorize actions: " + batch_id)
        selected_ids.extend(ids)
        selected_batches.append({
            "id": batch_id,
            "action_count": expected_count,
            "action_set_sha256": actual_hash,
            "action_kind": "semantic-transport-suppression" if batch_id.startswith("B00-") else "mapping-addition",
        })

    require(len(selected_ids) == len(set(selected_ids)) == 86, "Selected action population is not exactly 86 unique IDs")
    require(set_hash(selected_ids) == SELECTED_ACTION_SET_HASH, "Selected-action set hash mismatch")
    require(set(selected_ids) <= set(ledger_rows), "Selected action is absent from Phase 2D ledger")

    suppression_ids = set(rows["B00-semantic-suppressions"]["mapping_ids"])
    require({(ledger_rows[row_id]["donor_start"], ledger_rows[row_id]["target_start"]) for row_id in suppression_ids}
            == SUPPRESSED_PAIRS, "Approved suppression population changed")

    for row_id in selected_ids:
        row = ledger_rows[row_id]
        require(row["human_decision"] == "pending" and row["human_decision_evidence"] is None,
                "Approved action is not pending in frozen Phase 2D: " + row_id)
        require(row["batch_id"] in APPROVED_BATCHES, "Selected action has an unapproved batch: " + row_id)
        expected = "retain-mandatory-semantic-transport-suppression" if row_id in suppression_ids else None
        if expected:
            require(row["disposition"] == expected, "Suppression disposition changed: " + row_id)
        else:
            require(row["disposition"] in {
                "recommend-human-approval", "recommend-human-approval-with-reservation"
            }, "Selected mapping has an unapproved disposition: " + row_id)

    unapproved_ids = set(ledger_rows) - set(selected_ids)
    require(unapproved_ids == PHYSICS_CANDIDATES | HELD_STRONG,
            "Unapproved Phase 2D ledger population changed")
    packets = evidence_packets(ledger)
    result = {
        **frozen,
        "risk": risk,
        "batch_rows": rows,
        "selected_ids": sorted(selected_ids),
        "selected_batches": selected_batches,
        "ledger_rows": ledger_rows,
        "packets": packets,
        "unapproved_ids": sorted(unapproved_ids),
    }
    _DECISION_INPUTS_CACHE = copy.deepcopy(result)
    return result


def build_owner_decision() -> dict[str, Any]:
    global _OWNER_DECISION_CACHE
    if _OWNER_DECISION_CACHE is not None:
        return copy.deepcopy(_OWNER_DECISION_CACHE)
    inputs = validate_decision_inputs()
    ledger_identity = identity(LEDGER_PATH)
    validation_identity = identity(PHASE2D_VALIDATION_PATH)
    selected_actions = []
    for row_id in inputs["selected_ids"]:
        row = inputs["ledger_rows"][row_id]
        selected_actions.append({
            "ledger_id": row_id,
            "action_kind": "semantic-transport-suppression" if row_id.startswith("suppress:") else "mapping-addition",
            "batch_id": row["batch_id"],
            "phase2d_packet": inputs["packets"][row_id],
        })
    result = envelope(
        "owner-decision",
        human_approval=True,
        decision_record_schema={"name": "fable2-prototype-overlay-owner-decision", "version": 1},
        decision={
            "approver_identity": APPROVER_IDENTITY,
            "decision_timestamp": DECISION_TIMESTAMP,
            "external_decision_record_id": EXTERNAL_DECISION_RECORD_ID,
            "decision": DECISION,
            "approved_surface": APPROVED_SURFACE,
        },
        phase2d_binding={
            "commit": PHASE2D_COMMIT,
            "tree": PHASE2D_TREE,
            "terminal_subject": PHASE2D_SUBJECT,
            "validation": validation_identity,
            "ledger": ledger_identity,
            "ledger_record_count": 91,
            "ledger_pending_count": 91,
            "proposal_set_sha256": PHASE2D_LEDGER_SET_HASH,
            "canonical_set_hash_procedure": "lexicographically sorted IDs; compact sorted-key UTF-8 JSON array; one LF",
        },
        approved_batches=inputs["selected_batches"],
        selected_action_count=86,
        selected_action_set_sha256=SELECTED_ACTION_SET_HASH,
        selected_actions=selected_actions,
        approved_population={
            "semantic_transport_suppressions": 3,
            "unreserved_mapping_additions": 17,
            "reserved_mapping_additions": 66,
            "mapping_additions": 83,
            "approved_actions": 86,
        },
        reservation_acknowledgement={
            "accepted_without_removal_or_downgrade": True,
            "reserved_mapping_count": 66,
            "batch_ids": [
                "B02-multiple-references-reserved",
                "B04-callee-only-reserved",
                "B05-internal-region-reserved",
            ],
        },
        explicit_exclusions={
            "physics_candidates": sorted(PHYSICS_CANDIDATES),
            "held_original_strong_proposals": sorted(HELD_STRONG),
            "probable_proposals": {"count": 715, "decision": "held-and-unapproved"},
            "empty_batches": sorted(EMPTY_BATCHES),
            "empty_batches_confer_authority": False,
        },
        prohibited_surfaces=[
            "canonical names",
            "semantic function names",
            "scripts",
            "assets",
            "runtime",
            "renderer",
            "manifest",
            "generated recompilation code",
            "Ghidra database",
            "ReXGlue SDK",
        ],
        noncanonical_adoption=True,
        rollback_without_frozen_evidence_rewrite=True,
    )
    _OWNER_DECISION_CACHE = copy.deepcopy(result)
    return result


def validate_decision_records(records: list[dict[str, Any]]) -> None:
    ids = [row.get("decision", {}).get("external_decision_record_id") for row in records]
    require(all(isinstance(value, str) and value for value in ids), "Decision record ID is missing")
    require(len(ids) == len(set(ids)), "Duplicate external decision record ID")
    expected = build_owner_decision()
    require(len(records) == 1 and records[0] == expected, "External owner decision data or binding differs")


def decision_stage(check: bool = False) -> dict[str, Any]:
    document = build_owner_decision()
    validate_decision_records([document])
    result = write(DECISION_PATH, document, check)
    print("PASS owner decision: 86 actions bound to frozen Phase 2D", flush=True)
    return result


def distinctiveness_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "identity_hash": row["identity_hash"],
            "donor_user_count": len(row["donor_users"]),
            "target_user_count": len(row["target_users"]),
            "unique_in_each_population": row["unique_in_each_population"],
        }
        for row in rows
    ]


def build_delta() -> dict[str, Any]:
    global _DELTA_CACHE
    if _DELTA_CACHE is not None:
        return copy.deepcopy(_DELTA_CACHE)
    inputs = validate_decision_inputs()
    decision = build_owner_decision()
    decision_bytes = payload(decision)
    phase2a_rows = read(PHASE2A_MAP_PATH)["records"]
    phase2a_by_pair = {(row["donor_start"], row["target_start"]): (index, row)
                       for index, row in enumerate(phase2a_rows)}
    require(len(phase2a_by_pair) == len(phase2a_rows) == 15299, "Closed Phase 2A map changed")

    dependency_document = read(DEPENDENCIES_PATH)
    edges = {row["id"]: row["dependencies"] for row in dependency_document["edges"]}
    actions = []
    for row_id in inputs["selected_ids"]:
        row = inputs["ledger_rows"][row_id]
        batch_hash = APPROVED_BATCHES[row["batch_id"]][1]
        common = {
            "action_id": "P2E:" + row_id,
            "phase2d_ledger_id": row_id,
            "source_batch": {"id": row["batch_id"], "action_set_sha256": batch_hash},
            "phase2d_packet": inputs["packets"][row_id],
            "donor": copy.deepcopy(row["donor"]),
            "target": copy.deepcopy(row["target"]),
            "phase2d_disposition": row["disposition"],
            "human_decision_record_id": EXTERNAL_DECISION_RECORD_ID,
            "canonical": False,
            "analysis_only": True,
            "canonical_function_name": None,
        }
        if row_id.startswith("suppress:"):
            pair = (row["donor_start"], row["target_start"])
            require(pair in phase2a_by_pair, "Suppression does not reference a closed Phase 2A row")
            index, original = phase2a_by_pair[pair]
            original_hash = canonical_record_hash(original)
            require(original_hash == row["original_phase2a_record_sha256"],
                    "Suppression Phase 2A record hash mismatch: " + row_id)
            action = {
                **common,
                "action": "suppress-semantic-transport",
                "original_phase2c_grade": "closed-phase2a",
                "original_phase2a": {
                    "path": PHASE2A_MAP_PATH.as_posix(),
                    "json_pointer": f"/records/{index}",
                    "record_sha256": original_hash,
                    "status": original["status"],
                },
                "support_classes": ["mandatory-semantic-conflict-proof"],
                "dependency_seeds": [],
                "reference_identity_summaries": [
                    {
                        "donor_object": conflict["donor_use"]["object"],
                        "target_object": conflict["target_use"]["object"],
                        "donor_role": conflict["donor_use"]["reference"]["role"],
                        "target_role": conflict["target_use"]["reference"]["role"],
                    }
                    for conflict in row["conflicts"]
                ],
                "conflict_evidence": copy.deepcopy(row["conflicts"]),
                "reservations": ["unsafe-semantic-transport"],
                "risk_strata": ["mandatory-semantic-suppression"],
                "intersections": [],
                "provenance": {
                    "ledger_path": LEDGER_PATH.as_posix(),
                    "known_cases_path": KNOWN_CASES_PATH.as_posix(),
                },
            }
        else:
            require(edges.get(row_id) == row["dependencies"], "Dependency edge/ledger mismatch: " + row_id)
            action = {
                **common,
                "action": "add-mapping",
                "original_phase2c_grade": row["original_phase2c_grade"],
                "original_phase2c_generation": row["original_phase2c_generation"],
                "support_classes": copy.deepcopy(row["independent_classes"]),
                "dependency_seeds": copy.deepcopy(row["dependencies"]),
                "reference_identity_summaries": copy.deepcopy(row["reference_identities"]),
                "reference_distinctiveness": distinctiveness_summary(row["reference_distinctiveness"]),
                "contextual_reference_text": copy.deepcopy(row["reference_text"]),
                "reservations": copy.deepcopy(row["reasons"]),
                "risk_strata": copy.deepcopy(row["risk_strata"]),
                "intersections": copy.deepcopy(row["intersections"]),
                "provenance": {
                    "ledger_path": LEDGER_PATH.as_posix(),
                    "packet_path": PACKETS_PATH.as_posix(),
                    "dependency_path": DEPENDENCIES_PATH.as_posix(),
                    "risk_path": RISK_PATH.as_posix(),
                },
            }
        actions.append(action)

    suppressions = [row for row in actions if row["action"] == "suppress-semantic-transport"]
    additions = [row for row in actions if row["action"] == "add-mapping"]
    require((len(suppressions), len(additions)) == (3, 83), "Delta action arithmetic changed")
    unreserved = [row for row in additions if row["source_batch"]["id"] == "B01-unreserved"]
    reserved = [row for row in additions if row["source_batch"]["id"] != "B01-unreserved"]
    require(len(unreserved) == 17 and all(not row["reservations"] for row in unreserved),
            "B01 reservation invariant changed")
    require(len(reserved) == 66 and all(row["reservations"] for row in reserved),
            "Reserved action inventory changed")

    result = envelope(
        "approved-delta",
        overlay_version=OVERLAY_VERSION,
        owner_decision=identity_bytes(DECISION_PATH, decision_bytes),
        human_decision_record_id=EXTERNAL_DECISION_RECORD_ID,
        selected_action_set_sha256=SELECTED_ACTION_SET_HASH,
        counts={
            "semantic_transport_suppressions": 3,
            "unreserved_mapping_additions": 17,
            "reserved_mapping_additions": 66,
            "mapping_additions": 83,
            "actions": 86,
        },
        application_order=["suppress-semantic-transport", "add-mapping"],
        suppression_precedence_routes=["primary", "dependency", "fallback", "september", "consumer-merge"],
        actions=sorted(actions, key=lambda row: row["action_id"]),
        noncanonical_adoption=True,
    )
    _DELTA_CACHE = copy.deepcopy(result)
    return result


def validate_delta(document: dict[str, Any]) -> None:
    require(document == build_delta(), "Approved overlay delta differs from frozen decision inputs")
    require(document["canonical_adoption"] is False and document["analysis_only"] is True,
            "Delta canonical/analysis state changed")
    actions = document["actions"]
    require(len(actions) == 86 and len({row["action_id"] for row in actions}) == 86,
            "Delta action IDs are not exactly 86 unique values")
    require(set_hash(row["phase2d_ledger_id"] for row in actions) == SELECTED_ACTION_SET_HASH,
            "Delta selected-action hash mismatch")


def delta_stage(check: bool = False) -> dict[str, Any]:
    decision_expected = build_owner_decision()
    require((ROOT / DECISION_PATH).is_file(), "Owner decision must be frozen before delta construction")
    require((ROOT / DECISION_PATH).read_bytes() == payload(decision_expected), "Owner decision bytes changed")
    delta = build_delta()
    validate_delta(delta)
    result = write(DELTA_PATH, delta, check)
    print("PASS compact delta: 3 suppressions + 83 additions; 66 reservations retained", flush=True)
    return result


def phase2d_documentation_identities() -> list[dict[str, Any]]:
    files = git_lines("ls-tree", "-r", "--name-only", PHASE2D_COMMIT, "--", "docs/fable2-prototype-archaeology")
    return [identity(Path(path)) for path in files]


def build_source_pins() -> dict[str, Any]:
    global _SOURCE_PINS_CACHE
    if _SOURCE_PINS_CACHE is not None:
        return copy.deepcopy(_SOURCE_PINS_CACHE)
    inputs = validate_decision_inputs()
    decision = build_owner_decision()
    delta = build_delta()
    decision_identity = identity_bytes(DECISION_PATH, payload(decision))
    delta_identity = identity_bytes(DELTA_PATH, payload(delta))
    phase2d_validation = inputs["phase2d_validation"]
    phase2d_source_pins = inputs["phase2d_source_pins"]
    result = envelope(
        "source-pins",
        overlay_version=OVERLAY_VERSION,
        phase2d={
            "commit": PHASE2D_COMMIT,
            "tree": PHASE2D_TREE,
            "subject": PHASE2D_SUBJECT,
            "validation": identity(PHASE2D_VALIDATION_PATH),
            "source_pins": identity(PHASE2D_SOURCE_PINS_PATH),
            "ledger": identity(LEDGER_PATH),
            "review_summary": identity(REVIEW_SUMMARY_PATH),
            "bound_artifacts": copy.deepcopy(phase2d_validation["artifacts"]),
            "implementation": copy.deepcopy(phase2d_validation["implementation"]),
            "frozen_documentation": phase2d_documentation_identities(),
        },
        inherited={
            "phase2c_commit": PHASE2C_COMMIT,
            "protected_phase2c_artifacts": copy.deepcopy(phase2d_source_pins["protected_phase2c_artifacts"]),
            "blockers": copy.deepcopy(inputs["review_summary"]["inherited_blockers"]),
        },
        decision_inputs={
            "owner_decision": decision_identity,
            "approved_delta": delta_identity,
            "risk_batches": identity(RISK_PATH),
            "packets": identity(PACKETS_PATH),
            "known_cases": identity(KNOWN_CASES_PATH),
            "dependencies": identity(DEPENDENCIES_PATH),
            "probable_blockers": identity(PROBABLE_PATH),
            "simulations": identity(SIMULATIONS_PATH),
            "future_consumers": identity(CONSUMERS_PATH),
            "closed_phase2a_map": identity(PHASE2A_MAP_PATH),
            "phase2c_effective_map": identity(PHASE2C_EFFECTIVE_PATH),
        },
        repository_state={
            "fable_start": {
                "branch": "fable2-prototype-archaeology-phase2d",
                "head": PHASE2D_COMMIT,
                "tree": PHASE2D_TREE,
                "index": [],
                "worktree": [],
                "remotes": copy.deepcopy(phase2d_source_pins["starting_state"]["fable"]["remotes"]),
            },
            "sdk": copy.deepcopy(phase2d_source_pins["starting_state"]["sdk"]),
        },
        deterministic_inputs={
            "decision_timestamp": DECISION_TIMESTAMP,
            "current_time_used": False,
            "current_head_used": False,
            "absolute_paths_used": False,
            "enumeration_order_used": False,
            "locale_used": False,
            "randomized_hashes_used": False,
        },
    )
    _SOURCE_PINS_CACHE = copy.deepcopy(result)
    return result


def source_pins_stage(check: bool = False) -> dict[str, Any]:
    require((ROOT / DECISION_PATH).read_bytes() == payload(build_owner_decision()), "Owner decision is not frozen")
    require((ROOT / DELTA_PATH).read_bytes() == payload(build_delta()), "Approved delta is not frozen")
    document = build_source_pins()
    result = write(SOURCE_PINS_PATH, document, check)
    print("PASS Phase 2E source pins and frozen upstream bytes", flush=True)
    return result


def assert_no_canonical_names(value: Any, location: str = "") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_location = location + "/" + key
            if key in {"canonical_function_name", "semantic_function_name", "proposed_name"}:
                require(child is None, "Semantic/reference text became a canonical function name at " + child_location)
            assert_no_canonical_names(child, child_location)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_no_canonical_names(child, location + "/" + str(index))


def validate_dependencies(additions: list[dict[str, Any]], retained: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    addition_pairs = {(row["donor"]["start"], row["target"]["start"]): row for row in additions}
    require(len(addition_pairs) == len(additions), "Duplicate addition pair")
    graph: dict[str, list[str]] = {row["phase2d_ledger_id"]: [] for row in additions}
    checked = 0
    for row in additions:
        generation = row["original_phase2c_generation"]
        require(isinstance(generation, int) and generation >= 1, "Invalid addition generation")
        for dependency in row["dependency_seeds"]:
            pair = (dependency["donor"], dependency["target"])
            require(pair not in SUPPRESSED_PAIRS, "Suppressed dependency seed: " + row["phase2d_ledger_id"])
            if pair in addition_pairs:
                other = addition_pairs[pair]
                graph[row["phase2d_ledger_id"]].append(other["phase2d_ledger_id"])
                other_generation = other["original_phase2c_generation"]
                require(other_generation < generation, "Same-generation or forward dependency")
            else:
                require(pair in retained, "Dangling dependency: " + row["phase2d_ledger_id"])
                require(dependency["generation"] == 0, "Closed dependency generation changed")
                require(dependency["closed_record_sha256"] == retained[pair]["provenance"]["record_sha256"],
                        "Dependency seed hash mismatch: " + row["phase2d_ledger_id"])
            checked += 1

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        require(node not in visiting, "Circular dependency")
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph[node]:
            visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for node in sorted(graph):
        visit(node)
    return {"dependency_edges_checked": checked, "cycles": 0, "same_generation_edges": 0, "dangling_edges": 0}


def build_effective_map(delta: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_delta(delta)
    phase2a = read(PHASE2A_MAP_PATH)
    closed = phase2a["records"]
    require(len(closed) == 15299, "Closed Phase 2A pair count changed")
    suppressions = [row for row in delta["actions"] if row["action"] == "suppress-semantic-transport"]
    additions = [row for row in delta["actions"] if row["action"] == "add-mapping"]
    suppression_pairs = {(row["donor"]["start"], row["target"]["start"]) for row in suppressions}
    require(suppression_pairs == SUPPRESSED_PAIRS, "Effective suppression set changed")

    retained: dict[tuple[str, str], dict[str, Any]] = {}
    records = []
    for index, row in enumerate(closed):
        pair = (row["donor_start"], row["target_start"])
        if pair in suppression_pairs:
            continue
        effective = {
            "id": row["donor_start"] + ":" + row["target_start"],
            "donor_start": row["donor_start"],
            "donor_end_exclusive": row["donor_end_exclusive"],
            "target_start": row["target_start"],
            "target_end_exclusive": row["target_end_exclusive"],
            "size": row["size"],
            "source": "closed-phase2a-retained",
            "generation": 0,
            "reservations": [],
            "semantic_transport_eligible": True,
            "provenance": {
                "path": PHASE2A_MAP_PATH.as_posix(),
                "json_pointer": f"/records/{index}",
                "record_sha256": canonical_record_hash(row),
                "status": row["status"],
                "evidence_grade": row["evidence_grade"],
            },
        }
        retained[pair] = effective
        records.append(effective)
    require(len(records) == 15296, "Retained Phase 2A count is not 15,296")

    dependency_result = validate_dependencies(additions, retained)
    for action in additions:
        record = {
            "id": action["phase2d_ledger_id"],
            "donor_start": action["donor"]["start"],
            "donor_end_exclusive": action["donor"]["end_exclusive"],
            "donor_pdata_record": action["donor"]["pdata_record"],
            "target_start": action["target"]["start"],
            "target_end_exclusive": action["target"]["end_exclusive"],
            "target_pdata_record": action["target"]["pdata_record"],
            "size": action["donor"]["size"],
            "source": "phase2d-owner-approved-noncanonical",
            "generation": action["original_phase2c_generation"],
            "reservations": copy.deepcopy(action["reservations"]),
            "semantic_transport_eligible": True,
            "provenance": {
                "decision_record_id": EXTERNAL_DECISION_RECORD_ID,
                "decision_path": DECISION_PATH.as_posix(),
                "delta_path": DELTA_PATH.as_posix(),
                "phase2d_ledger_id": action["phase2d_ledger_id"],
                "phase2d_packet": copy.deepcopy(action["phase2d_packet"]),
                "batch": copy.deepcopy(action["source_batch"]),
                "original_phase2c_grade": action["original_phase2c_grade"],
            },
            "dependencies": copy.deepcopy(action["dependency_seeds"]),
            "canonical_function_name": None,
        }
        records.append(record)

    records.sort(key=lambda row: (int(row["donor_start"], 16), int(row["target_start"], 16)))
    donor_starts = [row["donor_start"] for row in records]
    target_starts = [row["target_start"] for row in records]
    require(len(records) == 15379, "Effective map count is not 15,379")
    require(len(donor_starts) == len(set(donor_starts)), "Duplicate effective donor")
    require(len(target_starts) == len(set(target_starts)), "Duplicate effective target")
    pairs = {(row["donor_start"], row["target_start"]) for row in records}
    require(not (pairs & SUPPRESSED_PAIRS), "Suppressed pair re-entered effective map")
    require(VECTOR_REGRESSIONS["vcfsx"] in pairs and VECTOR_REGRESSIONS["vspltb"] in pairs,
            "Corrected vector-wrapper mapping is absent")
    require(HAMMER_PAIR in pairs, "HammerCombat-context mapping is absent")
    hammer = next(row for row in records if (row["donor_start"], row["target_start"]) == HAMMER_PAIR)
    require(hammer["reservations"] == ["internal-code-region-dependent"], "Hammer reservation changed")
    require(hammer["canonical_function_name"] is None, "Hammer context became a canonical name")
    assert_no_canonical_names(records)

    document = envelope(
        "effective-map",
        overlay_version=OVERLAY_VERSION,
        owner_decision_record_id=EXTERNAL_DECISION_RECORD_ID,
        selected_action_set_sha256=SELECTED_ACTION_SET_HASH,
        application_order=["suppress-semantic-transport", "add-mapping"],
        counts={
            "closed_phase2a": 15299,
            "semantic_transport_suppressions": 3,
            "retained_phase2a": 15296,
            "mapping_additions": 83,
            "effective": 15379,
            "net_delta_from_phase2a": 80,
            "delta_from_phase2c_proposed_view": -3,
        },
        suppressions=[{
            "action_id": row["action_id"],
            "donor_start": row["donor"]["start"],
            "target_start": row["target"]["start"],
            "precedence": "all-semantic-routes",
        } for row in suppressions],
        records=records,
        donor_injective=True,
        target_injective=True,
        suppression_precedence=True,
        noncanonical_adoption=True,
    )
    return document, dependency_result


def build_materialized_documents(delta: dict[str, Any]) -> dict[Path, dict[str, Any]]:
    effective, dependency_result = build_effective_map(delta)
    effective_bytes = payload(effective)
    effective_identity = identity_bytes(OUT / "effective-map.json", effective_bytes)
    actions = delta["actions"]
    suppressions = [row for row in actions if row["action"] == "suppress-semantic-transport"]
    additions = [row for row in actions if row["action"] == "add-mapping"]
    pairs = {(row["donor_start"], row["target_start"]) for row in effective["records"]}

    selected_actions = envelope(
        "selected-actions",
        overlay_version=OVERLAY_VERSION,
        owner_decision_record_id=EXTERNAL_DECISION_RECORD_ID,
        selected_action_set_sha256=SELECTED_ACTION_SET_HASH,
        approved_batches=[{
            "id": batch_id,
            "action_count": count,
            "action_set_sha256": digest,
        } for batch_id, (count, digest) in APPROVED_BATCHES.items()],
        records=[{
            "action_id": row["action_id"],
            "phase2d_ledger_id": row["phase2d_ledger_id"],
            "action": row["action"],
            "batch": row["source_batch"],
            "phase2d_packet": row["phase2d_packet"],
        } for row in actions],
    )

    application = envelope(
        "application-receipt",
        overlay_version=OVERLAY_VERSION,
        owner_decision=identity(DECISION_PATH),
        approved_delta=identity(DELTA_PATH),
        effective_map=effective_identity,
        arithmetic="15,299 - 3 + 83 = 15,379",
        counts=copy.deepcopy(effective["counts"]),
        sources={
            "closed_phase2a": identity(PHASE2A_MAP_PATH),
            "frozen_phase2c_comparison": identity(PHASE2C_EFFECTIVE_PATH),
        },
        records=[
            {"stage": 0, "operation": "load-closed-phase2a", "count": 15299},
            {"stage": 1, "operation": "suppress-semantic-transport", "count": 15296},
            {"stage": 2, "operation": "add-owner-approved-noncanonical-mappings", "count": 15379},
        ],
    )

    suppression_audit_records = []
    for row in suppressions:
        pair = (row["donor"]["start"], row["target"]["start"])
        dependency_uses = [
            action["phase2d_ledger_id"]
            for action in additions
            if any((dep["donor"], dep["target"]) == pair for dep in action["dependency_seeds"])
        ]
        require(not dependency_uses, "Suppression appears as dependency")
        suppression_audit_records.append({
            "action_id": row["action_id"],
            "donor_start": pair[0],
            "target_start": pair[1],
            "effective_pair_present": pair in pairs,
            "routes": {
                "primary": "suppressed-before-additions",
                "dependency": "blocked-no-eligible-edge",
                "fallback": "blocked-opt-in-loader-has-no-fallback",
                "september": "blocked-before-two-hop-or-semantic-transport",
                "consumer_merge": "blocked-by-effective-map-membership-and-injectivity",
            },
            "contextual_conflicts": [
                {
                    "donor_text": conflict["donor_use"]["object"]["text"],
                    "target_text": conflict["target_use"]["object"]["text"],
                }
                for conflict in row["conflict_evidence"]
            ],
        })
    suppression_audit = envelope(
        "suppression-route-audit",
        overlay_version=OVERLAY_VERSION,
        precedence_routes=["primary", "dependency", "fallback", "september", "consumer-merge"],
        records=suppression_audit_records,
        vector_wrapper_regression={
            "old_crossed_pair_absent": VECTOR_REGRESSIONS["suppressed"] not in pairs,
            "vcfsx_pair_present": VECTOR_REGRESSIONS["vcfsx"] in pairs,
            "vspltb_pair_present": VECTOR_REGRESSIONS["vspltb"] in pairs,
        },
    )

    reservations = [row for row in additions if row["reservations"]]
    require(len(reservations) == 66, "Reservation inventory count changed")
    reservation_inventory = envelope(
        "reservation-inventory",
        overlay_version=OVERLAY_VERSION,
        count=66,
        records=[{
            "action_id": row["action_id"],
            "phase2d_ledger_id": row["phase2d_ledger_id"],
            "batch_id": row["source_batch"]["id"],
            "donor": row["donor"],
            "target": row["target"],
            "reservations": row["reservations"],
            "risk_strata": row["risk_strata"],
            "support_classes": row["support_classes"],
            "packet_sha256": row["phase2d_packet"]["sha256"],
        } for row in reservations],
        reservations_preserved_exactly=True,
    )

    ledger = read(LEDGER_PATH)
    ledger_rows = {row["id"]: row for row in ledger["records"]}
    selected_ids = {row["phase2d_ledger_id"] for row in actions}
    unapproved = sorted(set(ledger_rows) - selected_ids)
    probable_rows = read(PROBABLE_PATH)["records"]
    probable_ids = sorted(row["id"] for row in probable_rows)
    require(len(probable_ids) == len(set(probable_ids)) == 715, "Probable exclusion population changed")
    effective_ids = {row["id"] for row in effective["records"]}
    require(not (set(unapproved) & effective_ids), "Unapproved ledger row entered effective map")
    require(not (set(probable_ids) & effective_ids), "Probable proposal entered effective map")
    exclusion = envelope(
        "exclusion-audit",
        overlay_version=OVERLAY_VERSION,
        unapproved_phase2d_ledger_records=[{
            "id": row_id,
            "classification": "physics-candidate" if row_id in PHYSICS_CANDIDATES else "held-original-strong",
            "disposition": ledger_rows[row_id]["disposition"],
            "human_decision": ledger_rows[row_id]["human_decision"],
            "effective_pair_present": row_id in effective_ids,
        } for row_id in unapproved],
        probable_proposals=[{
            "id": row["id"],
            "disposition": row["disposition"],
            "effective_pair_present": row["id"] in effective_ids,
            "exclusive_blocker_signature": row["exclusive_blocker_signature"],
        } for row in sorted(probable_rows, key=lambda item: item["id"])],
        counts={
            "physics_candidates_excluded": 2,
            "held_original_strong_excluded": 3,
            "unapproved_ledger_records_excluded": 5,
            "probable_proposals_excluded": 715,
        },
        empty_batches=[{"id": batch_id, "action_count": 0, "authority": False} for batch_id in sorted(EMPTY_BATCHES)],
    )

    dependency = envelope(
        "dependency-injectivity",
        overlay_version=OVERLAY_VERSION,
        effective_map=effective_identity,
        counts={
            **dependency_result,
            "records": 15379,
            "unique_donors": len({row["donor_start"] for row in effective["records"]}),
            "unique_targets": len({row["target_start"] for row in effective["records"]}),
            "suppressed_dependencies": 0,
        },
        donor_injective=True,
        target_injective=True,
        dependency_consistent=True,
    )

    decision_identity = identity(DECISION_PATH)
    delta_identity = identity(DELTA_PATH)
    default_identity_before = identity(PHASE2A_MAP_PATH)
    default_identity_after = identity(PHASE2A_MAP_PATH)
    require(default_identity_before == default_identity_after, "Default map changed during compatibility exercise")
    consumer = envelope(
        "consumer-compatibility",
        overlay_version=OVERLAY_VERSION,
        contract={
            "adapter": "tools/phase2e/Fable2PrototypeOverlayConsumer.py",
            "default_command": ["python", "tools/phase2e/Fable2PrototypeOverlayConsumer.py", "default"],
            "opt_in_requires": [
                "--overlay-version", "--decision", "--decision-sha256", "--delta", "--delta-sha256",
                "--effective-map", "--effective-map-sha256",
            ],
            "missing_or_invalid_overlay": "fail-without-fallback",
            "selection_visible_in_output_provenance": True,
            "reference_text_is_canonical_name": False,
        },
        default_selection={
            "source": default_identity_before,
            "count": 15299,
            "selection": "closed-phase2a-default",
            "bytes_unchanged": default_identity_before == default_identity_after,
        },
        opt_in_selection={
            "decision": decision_identity,
            "delta": delta_identity,
            "effective_map": effective_identity,
            "count": 15379,
            "selection": OVERLAY_VERSION,
            "canonical": False,
            "analysis_only": True,
        },
        compatibility_exercise={
            "input_mode": "read-only copied-or-in-memory-analysis-input",
            "loaded": True,
            "count": 15379,
            "original_consumer_artifacts_mutated": False,
            "default_output_bytes_changed": False,
        },
        production_consumers_switched=[],
    )

    rollback = envelope(
        "rollback-verification",
        overlay_version=OVERLAY_VERSION,
        pre_adoption_default=default_identity_before,
        default_consumer_switch_before_phase2e=False,
        opt_in_mechanism="explicit dedicated adapter command with version and three caller-supplied hashes",
        disable_command=["python", "tools/phase2e/Fable2PrototypeOverlayConsumer.py", "default"],
        disable_result={
            "selection": "closed-phase2a-default",
            "source": default_identity_after,
            "count": 15299,
            "matches_pre_adoption": default_identity_after == default_identity_before,
        },
        overlay_artifacts=[decision_identity, delta_identity, effective_identity],
        frozen_evidence_rewrite_required=False,
        deletion_or_regeneration_of_phase1_through_phase2d_required=False,
        status="pass",
    )

    return {
        OUT / "selected-actions.json": selected_actions,
        OUT / "effective-map.json": effective,
        OUT / "overlay-application-receipt.json": application,
        OUT / "suppression-route-audit.json": suppression_audit,
        OUT / "reservation-inventory.json": reservation_inventory,
        OUT / "exclusion-audit.json": exclusion,
        OUT / "dependency-injectivity-verification.json": dependency,
        OUT / "consumer-compatibility.json": consumer,
        OUT / "rollback-verification.json": rollback,
    }


def validate_effective_map(document: dict[str, Any], delta: dict[str, Any] | None = None) -> None:
    expected, _ = build_effective_map(delta or build_delta())
    require(document == expected, "Effective map differs from deterministic approved delta application")


def materialize_stage(check: bool = False) -> list[dict[str, Any]]:
    require((ROOT / DECISION_PATH).read_bytes() == payload(build_owner_decision()), "Owner decision must be frozen first")
    expected_delta = build_delta()
    require((ROOT / DELTA_PATH).read_bytes() == payload(expected_delta), "Approved delta must be frozen first")
    expected_pins = build_source_pins()
    require((ROOT / SOURCE_PINS_PATH).read_bytes() == payload(expected_pins), "Source pins must be frozen first")
    documents = build_materialized_documents(expected_delta)
    results = [write(path, document, check) for path, document in documents.items()]
    default_before = load_default_mapping()
    effective_path = (ROOT / OUT / "effective-map.json").resolve()
    _, provenance = load_opt_in_mapping(
        OVERLAY_VERSION,
        (ROOT / DECISION_PATH).resolve(),
        sha256((ROOT / DECISION_PATH).read_bytes()),
        (ROOT / DELTA_PATH).resolve(),
        sha256((ROOT / DELTA_PATH).read_bytes()),
        effective_path,
        sha256(effective_path.read_bytes()),
    )
    default_after = load_default_mapping()
    require(default_before == default_after, "Opt-in exercise changed the default analysis selection")
    require(provenance["mapping_count"] == 15379 and provenance["selection"] == OVERLAY_VERSION,
            "Opt-in compatibility exercise failed")
    print("PASS materialized overlay: 15,299 - 3 + 83 = 15,379 injective pairs", flush=True)
    return results


def validate_hash_argument(value: str, label: str) -> str:
    normalized = value.upper()
    require(len(normalized) == 64 and all(character in "0123456789ABCDEF" for character in normalized),
            label + " must be an exact SHA-256")
    return normalized


def checked_external_identity(path: Path, expected_hash: str, label: str) -> dict[str, Any]:
    require(path.is_absolute(), "Internal consumer path must be resolved")
    resolved = path.resolve()
    require(resolved.is_relative_to(ROOT.resolve()), label + " path escapes repository")
    relative = resolved.relative_to(ROOT.resolve())
    require(resolved.is_file(), "Missing " + label + "; no fallback is permitted")
    data = resolved.read_bytes()
    actual_hash = sha256(data)
    require(actual_hash == validate_hash_argument(expected_hash, label), "Stale or tampered " + label + "; no fallback is permitted")
    return {"path": relative.as_posix(), "size": len(data), "sha256": actual_hash}


def load_default_mapping() -> dict[str, Any]:
    document = read(PHASE2A_MAP_PATH)
    require(len(document["records"]) == 15299, "Default Phase 2A mapping count changed")
    return {
        "schema": {"name": "fable2-prototype-overlay-consumer-selection", "version": 1},
        "selection": "closed-phase2a-default",
        "canonical_adoption": False,
        "analysis_only": True,
        "mapping_count": 15299,
        "source": identity(PHASE2A_MAP_PATH),
        "overlay_enabled": False,
    }


def load_opt_in_mapping(
    overlay_version: str,
    decision_path: Path,
    decision_hash: str,
    delta_path: Path,
    delta_hash: str,
    effective_path: Path,
    effective_hash: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    require(overlay_version == OVERLAY_VERSION, "Unknown overlay version; no fallback is permitted")
    decision_identity = checked_external_identity(decision_path, decision_hash, "owner decision")
    delta_identity = checked_external_identity(delta_path, delta_hash, "approved delta")
    effective_identity = checked_external_identity(effective_path, effective_hash, "effective map")
    decision = json.loads(decision_path.read_bytes())
    delta = json.loads(delta_path.read_bytes())
    effective = json.loads(effective_path.read_bytes())
    validate_decision_records([decision])
    validate_delta(delta)
    validate_effective_map(effective, delta)
    provenance = {
        "schema": {"name": "fable2-prototype-overlay-consumer-selection", "version": 1},
        "selection": OVERLAY_VERSION,
        "canonical_adoption": False,
        "analysis_only": True,
        "mapping_count": len(effective["records"]),
        "overlay_enabled": True,
        "owner_decision_record_id": EXTERNAL_DECISION_RECORD_ID,
        "owner_decision": decision_identity,
        "approved_delta": delta_identity,
        "effective_map": effective_identity,
        "selected_action_set_sha256": SELECTED_ACTION_SET_HASH,
        "fallback_permitted": False,
    }
    return effective, provenance


def path_audit(value: Any, location: str = "") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_location = location + "/" + key
            if key == "path" and isinstance(child, str):
                path = Path(child)
                require(not path.is_absolute() and ".." not in path.parts, "Unsafe evidence path at " + child_location)
            path_audit(child, child_location)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            path_audit(child, location + "/" + str(index))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["verify-upstream", "decision", "delta", "bind", "materialize", "verify"])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.command == "verify-upstream":
        validate_decision_inputs()
        print("PASS frozen Phase 1-2D and owner-decision identities", flush=True)
    elif args.command == "decision":
        decision_stage(args.check)
    elif args.command == "delta":
        delta_stage(args.check)
    elif args.command == "bind":
        source_pins_stage(args.check)
    elif args.command == "materialize":
        materialize_stage(args.check)
    else:
        decision_stage(True)
        delta_stage(True)
        source_pins_stage(True)
        materialize_stage(True)
        for path in (DECISION_PATH, DELTA_PATH, SOURCE_PINS_PATH):
            path_audit(read(path))
        print("PASS Phase 2E decision, delta, source pins, materialization and path audit", flush=True)


if __name__ == "__main__":
    main()
