"""Deterministic read-only Fable II prototype analyst annotation layer."""

from __future__ import annotations

import argparse
import copy
import contextlib
import io
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools/phase2i"), str(ROOT / "tools/phase2e")]

import Fable2AnalystSources as sources  # noqa: E402
import Fable2PrototypeOverlay as overlay  # noqa: E402


INDEX_PATH = sources.OUT / "normalized-annotation-index.json"
SUMMARY_PATH = sources.DOC / "evidence/annotation-summary.json"

PHASE2A_MAP = Path("docs/fable2-prototype-archaeology/phase2a/evidence/prototype-correspondence-accepted.json")
PHASE2E_DECISION = Path("docs/fable2-prototype-archaeology/phase2e/evidence/owner-decision.json")
PHASE2E_DELTA = Path("docs/fable2-prototype-archaeology/phase2e/evidence/approved-overlay-delta.json")
PHASE2E_EFFECTIVE = Path("out/prototype-archaeology/phase2e/effective-map.json")
PHASE2E_EXCLUSIONS = Path("out/prototype-archaeology/phase2e/exclusion-audit.json")
PHASE2F_QUEUES = Path("out/prototype-archaeology/phase2f/review-queues.json")
PHASE2F_INTERSECTIONS = Path("out/prototype-archaeology/phase2f/project-intersections.json")
PHASE2F_DELTA = Path("out/prototype-archaeology/phase2f/lane-delta.json")
PHASE2G_SUMMARY = Path("docs/fable2-prototype-archaeology/phase2g/evidence/packet-summary.json")
PHASE2G_SELECTION = Path("out/prototype-archaeology/phase2g/review-selection.json")
PHASE2H_PINS = Path("docs/fable2-prototype-archaeology/phase2h/evidence/source-pins.json")
PHASE2H_DECISION = Path("docs/fable2-prototype-archaeology/phase2h/evidence/owner-decision.json")
PHASE2H_DELTA = Path("docs/fable2-prototype-archaeology/phase2h/evidence/semantic-correction-delta.json")
PHASE2H_VIEW = Path("out/prototype-archaeology/phase2h/materialized-reviewed-semantic-view.json")

MAPPING_VIEWS = ("none", "closed-phase2a-default", "phase2e-v1")
SEMANTIC_VIEWS = ("none", "phase2f-evidence", "phase2h-v1")
PROFILES = (
    "address",
    "phase2h-approved",
    "overlay-review",
    "project-relevant",
    "semantic-review",
    "all-correspondences",
    "excluded-review",
)

SUPPRESSED_PAIRS = {
    ("0x82631A30", "0x82950A98"),
    ("0x828EA448", "0x82681198"),
    ("0x83062950", "0x83060C30"),
}
VECTOR_PAIRS = {
    ("0x83060A80", "0x83060C30"),
    ("0x83062950", "0x83060CD8"),
}
VECTOR_CONTEXT = {
    ("0x83060A80", "0x83060C30"): "__vcfsx",
    ("0x83062950", "0x83060CD8"): "__vspltb",
}
SUPPRESSION_CONTEXT = {
    ("0x82631A30", "0x82950A98"): ("Navigator", "Controlled"),
    ("0x828EA448", "0x82681198"): ("TROLL_FOOTSTEP", "DESTROY_ENTITY"),
    ("0x83062950", "0x83060C30"): ("__vspltb", "__vcfsx"),
}
PACKET_C_PAIR = ("0x825240E8", "0x82522C10")

DISPLAY_ORDER = {
    "suppression-warning": 0,
    "excluded-proposal-warning": 1,
    "correspondence-provenance": 2,
    "overlay-addition": 3,
    "rejected-alias-warning": 4,
    "unreviewed-semantic-evidence": 5,
    "corroborated-review-evidence": 6,
    "semantic-edge-correction": 7,
    "owner-reviewed-contextual-role": 8,
}


class SelectionError(ValueError):
    """An explicit selection is missing, partial, altered, or incompatible."""


def selection_require(condition: Any, message: str) -> None:
    if not condition:
        raise SelectionError(message)


def envelope(schema_name: str, **fields: Any) -> dict[str, Any]:
    return {
        "schema": {"name": schema_name, "version": 1},
        "phase2h_commit": sources.PHASE2H_COMMIT,
        "analysis_only": True,
        "annotation_generation_only": True,
        "canonical_name_authority": False,
        "production_mapping_authority": False,
        "runtime_authority": False,
        "ghidra_mutation_authority": False,
        **fields,
    }


def address(value: str | int) -> int:
    try:
        number = value if isinstance(value, int) else int(value, 0)
    except (TypeError, ValueError) as error:
        raise SelectionError(f"Invalid guest address: {value!r}") from error
    selection_require(0 <= number <= 0xFFFFFFFF, f"Guest address outside 32-bit range: {value!r}")
    return number


def address_text(value: str | int) -> str:
    return f"0x{address(value):08X}"


def interval(start: str | int, end_exclusive: str | int | None = None) -> dict[str, str]:
    first = address(start)
    last = first + 1 if end_exclusive is None else address(end_exclusive)
    sources.require(last > first, "Invalid annotation range")
    return {"start": address_text(first), "end_exclusive": address_text(last)}


def sanitize(value: Any) -> str:
    """Produce one deterministic, non-forgeable display line fragment."""
    escaped = json.dumps(str(value), ensure_ascii=False)[1:-1]
    return escaped.replace("[F2PA:", "\\u005BF2PA:")


def source_registry(pins: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["path"]: {key: row[key] for key in ("path", "size", "sha256")} for row in pins["sources"]}


def source_reference(
    registry: dict[str, dict[str, Any]],
    path: str | Path,
    pointer: str,
    node: Any,
) -> dict[str, Any]:
    name = Path(path).as_posix()
    sources.require(name in registry, "Unbound annotation source: " + name)
    sources.require(pointer.startswith("/"), "JSON pointer must be absolute")
    return {
        **registry[name],
        "json_pointer": pointer,
        "record_identity": sources.digest(sources.payload(node)),
    }


def annotation_id(
    display_kind: str,
    target: dict[str, Any],
    donor: dict[str, Any] | None,
    stable_identity: str,
    evidence_sources: list[dict[str, Any]],
) -> str:
    seed = {
        "display_kind": display_kind,
        "target": target,
        "donor": donor,
        "stable_identity": stable_identity,
        "record_identities": sorted(row["record_identity"] for row in evidence_sources),
    }
    return "A-" + sources.digest(sources.payload(seed))[:24]


def annotation(
    *,
    display_kind: str,
    target_range: dict[str, str],
    donor_range: dict[str, str] | None,
    stable_identity: str,
    display_title: str,
    comment: str,
    mapping: dict[str, Any] | None,
    semantic: dict[str, Any] | None,
    evidence_sources: list[dict[str, Any]],
    limitations: Iterable[str],
    mapping_views: Iterable[str],
    project_memberships: Iterable[str] = (),
    relationships: Iterable[dict[str, Any]] = (),
    selection_layer: str,
    safe: bool = True,
) -> dict[str, Any]:
    target = {"build": "fable2-goty-tu1", "range": target_range}
    donor = {"build": "build-23.12.02.0330", "range": donor_range} if donor_range else None
    refs = sorted(evidence_sources, key=lambda row: (row["path"], row["record_identity"], row["json_pointer"]))
    value_id = annotation_id(display_kind, target, donor, stable_identity, refs)
    return {
        "annotation_id": value_id,
        "namespace_marker": f"[F2PA:phase2i:{value_id}]",
        "target": target,
        "donor": donor,
        "display_kind": display_kind,
        "display_title": sanitize(display_title),
        "comment_body": sanitize(comment),
        "suggestion": {
            "comment_type": "PRE_COMMENT",
            "bookmark_category": "F2PA/Phase2I/" + display_kind,
        },
        "mapping": mapping,
        "semantic": semantic,
        "sources": refs,
        "limitations": [sanitize(value) for value in limitations],
        "safe_for_analyst_comment_display": safe,
        "canonical_name_authority": False,
        "production_mapping_authority": False,
        "runtime_authority": False,
        "mapping_views": sorted(set(mapping_views)),
        "project_memberships": sorted(set(project_memberships)),
        "relationships": sorted(list(relationships), key=sources.payload),
        "selection_layer": selection_layer,
    }


def record_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    target_range = row["target"]["range"]
    return (
        address(target_range["start"]),
        address(target_range["end_exclusive"]),
        DISPLAY_ORDER[row["display_kind"]],
        row["annotation_id"],
    )


def deduplicate_records(records: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    unique: dict[str, dict[str, Any]] = {}
    duplicate_count = 0
    for candidate in records:
        row = copy.deepcopy(candidate)
        existing = unique.get(row["annotation_id"])
        if existing is None:
            unique[row["annotation_id"]] = row
            continue
        duplicate_count += 1
        left = dict(existing)
        right = dict(row)
        left_sources = left.pop("sources")
        right_sources = right.pop("sources")
        sources.require(left == right, "Annotation ID collision with different content: " + row["annotation_id"])
        combined = {sources.payload(item): item for item in left_sources + right_sources}
        existing["sources"] = sorted(combined.values(), key=lambda item: (item["path"], item["record_identity"]))
    return sorted(unique.values(), key=record_sort_key), duplicate_count


def common_mapping(
    *,
    source: str,
    status: str,
    grade: str,
    record_id: str,
    reservations: list[str],
    decision_ids: list[str] | None = None,
    batch_id: str | None = None,
) -> dict[str, Any]:
    return {
        "source": source,
        "status": status,
        "evidence_grade": grade,
        "record_id": record_id,
        "decision_ids": decision_ids or [],
        "batch_id": batch_id,
        "reservations": list(reservations),
    }


def _mapping_comment(prefix: str, donor: dict[str, str], target: dict[str, str], grade: str, reservations: list[str]) -> str:
    reservation = "RESERVED: " + ", ".join(reservations) if reservations else "unreserved"
    return (
        f"MAPPING — ACTIVE — {prefix} — {reservation}. Build-23 "
        f"[{donor['start']},{donor['end_exclusive']}) corresponds to TU1 "
        f"[{target['start']},{target['end_exclusive']}). Evidence grade: {grade}. "
        "Authority: correspondence provenance only; never a function name, production mapping, or runtime instruction."
    )


def _project_memberships(intersections: list[dict[str, Any]]) -> list[str]:
    return sorted({row["set"] for row in intersections})


def build_mapping_records(
    registry: dict[str, dict[str, Any]],
    closed: dict[str, Any],
    delta: dict[str, Any],
    intersections: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    intersection_by_id = {row["mapping_id"]: row for row in intersections["records"]}
    closed_by_target: dict[str, dict[str, Any]] = {}
    all_by_target: dict[str, dict[str, Any]] = {}

    for index, row in enumerate(closed["records"]):
        pair = (row["donor_start"], row["target_start"])
        record_id = row["donor_start"] + ":" + row["target_start"]
        donor_range = interval(row["donor_start"], row["donor_end_exclusive"])
        target_range = interval(row["target_start"], row["target_end_exclusive"])
        source_ref = source_reference(registry, PHASE2A_MAP, f"/records/{index}", row)
        mapping_views = ["closed-phase2a-default"]
        if pair not in SUPPRESSED_PAIRS:
            mapping_views.append("phase2e-v1")
        mapping = common_mapping(
            source="closed-phase2a",
            status="validated-active-correspondence",
            grade=row["evidence_grade"],
            record_id=record_id,
            reservations=[],
        )
        value = annotation(
            display_kind="correspondence-provenance",
            target_range=target_range,
            donor_range=donor_range,
            stable_identity=record_id,
            display_title="Closed Phase 2A correspondence provenance",
            comment=_mapping_comment("CLOSED PHASE 2A", donor_range, target_range, row["evidence_grade"], []),
            mapping=mapping,
            semantic=None,
            evidence_sources=[source_ref],
            limitations=["Validated cross-build correspondence only; no semantic or naming authority."],
            mapping_views=mapping_views,
            selection_layer="mapping-active",
        )
        records.append(value)
        compact = {
            "id": record_id,
            "donor_start": row["donor_start"],
            "donor_end_exclusive": row["donor_end_exclusive"],
            "target_start": row["target_start"],
            "target_end_exclusive": row["target_end_exclusive"],
            "reservations": [],
            "source": "closed-phase2a",
        }
        closed_by_target[row["target_start"]] = compact
        if pair not in SUPPRESSED_PAIRS:
            all_by_target[row["target_start"]] = compact

    for index, action in enumerate(delta["actions"]):
        donor_range = interval(action["donor"]["start"], action["donor"]["end_exclusive"])
        target_range = interval(action["target"]["start"], action["target"]["end_exclusive"])
        source_ref = source_reference(registry, PHASE2E_DELTA, f"/actions/{index}", action)
        if action["action"] == "add-mapping":
            record_id = action["phase2d_ledger_id"]
            reservations = list(action["reservations"])
            project = intersection_by_id.get(record_id, {"intersections": []})
            project_refs = []
            if record_id in intersection_by_id:
                project_index = intersections["records"].index(intersection_by_id[record_id])
                project_refs.append(source_reference(registry, PHASE2F_INTERSECTIONS, f"/records/{project_index}", project))
            mapping = common_mapping(
                source="phase2e-owner-approved-noncanonical-addition",
                status="owner-approved-noncanonical-active",
                grade=action["original_phase2c_grade"],
                record_id=record_id,
                reservations=reservations,
                decision_ids=[action["human_decision_record_id"]],
                batch_id=action["source_batch"]["id"],
            )
            comment = _mapping_comment("OWNER-APPROVED NON-CANONICAL PHASE 2E", donor_range, target_range, action["original_phase2c_grade"], reservations)
            pair = (action["donor"]["start"], action["target"]["start"])
            if pair in VECTOR_CONTEXT:
                comment += f" Context-only vector reference: {VECTOR_CONTEXT[pair]}; not a function name."
            records.append(annotation(
                display_kind="overlay-addition",
                target_range=target_range,
                donor_range=donor_range,
                stable_identity=record_id,
                display_title="Phase 2E owner-approved non-canonical correspondence",
                comment=comment,
                mapping=mapping,
                semantic=None,
                evidence_sources=[source_ref, *project_refs],
                limitations=["Owner approval covers non-canonical analysis correspondence only; reference text is not a semantic label."],
                mapping_views=["phase2e-v1"],
                project_memberships=_project_memberships(project["intersections"]),
                selection_layer="mapping-active",
            ))
            all_by_target[action["target"]["start"]] = {
                "id": record_id,
                "donor_start": action["donor"]["start"],
                "donor_end_exclusive": action["donor"]["end_exclusive"],
                "target_start": action["target"]["start"],
                "target_end_exclusive": action["target"]["end_exclusive"],
                "reservations": reservations,
                "source": "phase2e-addition",
            }
            continue

        conflict = action["reference_identity_summaries"][0]
        pair = (action["donor"]["start"], action["target"]["start"])
        donor_text, target_text = SUPPRESSION_CONTEXT[pair]
        record_id = action["phase2d_ledger_id"]
        mapping = common_mapping(
            source="phase2e-suppression",
            status="suppressed-tombstone-inactive",
            grade="mandatory-semantic-suppression",
            record_id=record_id,
            reservations=action["reservations"],
            decision_ids=[action["human_decision_record_id"]],
            batch_id=action["source_batch"]["id"],
        )
        records.append(annotation(
            display_kind="suppression-warning",
            target_range=target_range,
            donor_range=donor_range,
            stable_identity=record_id,
            display_title="Suppressed unsafe historical correspondence",
            comment=(
                f"MAPPING WARNING — SUPPRESSED — RESERVED: {', '.join(action['reservations'])}. Historical "
                f"{donor_range['start']} -> {target_range['start']} transported {donor_text} to {target_text}. "
                "Tombstone only; never route through this pair."
            ),
            mapping=mapping,
            semantic=None,
            evidence_sources=[source_ref],
            limitations=["Suppression is inactive correspondence and cannot supply a mapping or semantic route."],
            mapping_views=["phase2e-v1"],
            selection_layer="mapping-suppression",
            safe=True,
        ))

    return records, closed_by_target, all_by_target


def build_exclusion_records(
    registry: dict[str, dict[str, Any]],
    document: dict[str, Any],
) -> list[dict[str, Any]]:
    result = []
    populations = (
        ("unapproved_phase2d_ledger_records", "unapproved Phase 2D proposal"),
        ("probable_proposals", "probable proposal"),
    )
    for population, title in populations:
        for index, row in enumerate(document[population]):
            donor_start, target_start = row["id"].split(":")
            classification = row.get("classification", "probable")
            blocker = row.get("exclusive_blocker_signature", "additional evidence required")
            source_ref = source_reference(registry, PHASE2E_EXCLUSIONS, f"/{population}/{index}", row)
            mapping = common_mapping(
                source="phase2e-excluded-proposal",
                status="excluded-inactive-warning-only",
                grade=classification,
                record_id=row["id"],
                reservations=[blocker],
            )
            result.append(annotation(
                display_kind="excluded-proposal-warning",
                target_range=interval(target_start),
                donor_range=interval(donor_start),
                stable_identity=population + ":" + row["id"],
                display_title="Excluded correspondence proposal",
                comment=(
                    f"MAPPING WARNING — EXCLUDED — {title}: {donor_start} -> {target_start}. "
                    f"Disposition: {row['disposition']}; limitation: {blocker}. Inactive warning only; supplies no route."
                ),
                mapping=mapping,
                semantic=None,
                evidence_sources=[source_ref],
                limitations=["Start-only review record; no function range or active correspondence is asserted."],
                mapping_views=["phase2e-v1"],
                selection_layer="mapping-excluded",
                safe=True,
            ))
    return result


def _flatten_semantic_queues(document: dict[str, Any]) -> list[tuple[str, int, dict[str, Any]]]:
    result = []
    for queue_name in sorted(document["queues"]):
        for index, row in enumerate(document["queues"][queue_name]):
            result.append((queue_name, index, row))
    return result


def build_phase2f_records(
    registry: dict[str, dict[str, Any]],
    queues: dict[str, Any],
    phase2g: dict[str, Any],
    phase2g_selection: dict[str, Any],
    all_by_target: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    result = []
    review_by_terminal = {row["primary_terminal"]: row for row in phase2g_selection["records"]}
    packet_summary = {row["packet"]: row for row in phase2g["records"]}
    for queue_name, index, row in _flatten_semantic_queues(queues):
        mapping_row = all_by_target[row["target_start"]]
        donor_range = interval(mapping_row["donor_start"], mapping_row["donor_end_exclusive"])
        target_range = interval(mapping_row["target_start"], mapping_row["target_end_exclusive"])
        source_ref = source_reference(registry, PHASE2F_QUEUES, f"/queues/{queue_name}/{index}", row)
        review = review_by_terminal.get(row["terminal_id"])
        refs = [source_ref]
        display_kind = "unreviewed-semantic-evidence"
        static_review = None
        if review is not None:
            summary = packet_summary[review["packet"]]
            summary_index = phase2g["records"].index(summary)
            selection_index = phase2g_selection["records"].index(review)
            refs.extend([
                source_reference(registry, PHASE2G_SUMMARY, f"/records/{summary_index}", summary),
                source_reference(registry, PHASE2G_SELECTION, f"/records/{selection_index}", review),
            ])
            display_kind = "corroborated-review-evidence"
            static_review = {
                "packet": review["packet"],
                "disposition": review["primary_disposition"],
                "reservation_disposition": review["reservation_disposition"],
                "owner_approved": False,
            }
        reservations = sorted({reason for item in row["reservations"] for reason in item["reservations"]})
        reservation_text = "RESERVED: " + ", ".join(reservations) if reservations else "unreserved"
        review_text = (
            f"Static review: {static_review['disposition']}; NOT OWNER-REVIEWED. "
            if static_review else "UNREVIEWED analysis evidence. "
        )
        limitations = list(row["limitations"])
        if review and review["packet"] == "A":
            limitations.extend([
                "HammerCombat is literal context only; neither owner nor generic callee may be named HammerCombat.",
                "Reservation internal-code-region-dependent remains retained.",
            ])
        if review and review["packet"] == "B":
            limitations.extend([
                "Behaviorally corresponding reserved review evidence is not an approved role.",
                "No oxygen simulation logic or canonical identity is established.",
            ])
        semantic = {
            "grade": row["grade"],
            "review_status": "unreviewed-analysis-evidence",
            "terminal_id": row["terminal_id"],
            "evidence_text": sanitize(row["reference_text"]),
            "category": row["category"],
            "newly_routable": row["newly_routable"],
            "static_review": static_review,
            "reservations": reservations,
        }
        result.append(annotation(
            display_kind=display_kind,
            target_range=target_range,
            donor_range=donor_range,
            stable_identity=row["terminal_id"],
            display_title="Unreviewed semantic context: " + row["reference_text"],
            comment=(
                f"SEMANTIC EVIDENCE — {review_text}{reservation_text}. Context {row['reference_text']} at TU1 "
                f"{target_range['start']}; grade {row['grade']}. Transported string/context is not a function name "
                "and does not authorize a mapping, runtime behavior, or canonical label."
            ),
            mapping=None,
            semantic=semantic,
            evidence_sources=refs,
            limitations=limitations,
            mapping_views=["phase2e-v1"],
            selection_layer="semantic-phase2f",
        ))
    return result


def build_phase2h_records(
    registry: dict[str, dict[str, Any]],
    view: dict[str, Any],
    all_by_target: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    result = []
    owner = view["reviewed_roles"][0]
    owner_mapping = all_by_target[owner["owner_mapping"]["target"]]
    owner_target = interval(owner_mapping["target_start"], owner_mapping["target_end_exclusive"])
    owner_donor = interval(owner_mapping["donor_start"], owner_mapping["donor_end_exclusive"])
    role_ref = source_reference(registry, PHASE2H_VIEW, "/reviewed_roles/0", owner)
    limitations = [
        "Visitor range [0x825237C8,0x82524454) has unresolved direction.",
        "No reward granting or reward arithmetic is claimed.",
        "No map-marker creation or visibility update is claimed.",
        "No constructor identity, serialization direction, or complete quest-object ownership is claimed.",
    ]
    result.append(annotation(
        display_kind="owner-reviewed-contextual-role",
        target_range=owner_target,
        donor_range=owner_donor,
        stable_identity="P2G-OWNER-DECISION-001:Packet-C-role",
        display_title="Owner-reviewed Packet C contextual role",
        comment=(
            "SEMANTIC EVIDENCE — OWNER-REVIEWED — RESERVED: single-independent-support-class. "
            "CONTEXTUAL ROLE — NOT A FUNCTION NAME: conditional keyed reward/world-map field materializer. "
            "Visitor [0x825237C8,0x82524454) direction unresolved. No reward granting/arithmetic, map-marker "
            "creation, visibility updates, constructor identity, serialization direction, or complete quest-object ownership."
        ),
        mapping=None,
        semantic={
            "grade": "owner-reviewed non-canonical contextual role",
            "review_status": "owner-reviewed",
            "decision_id": view["decision_record_id"],
            "packet": "C",
            "contextual_role_description": owner["contextual_role"],
            "reservations": [owner["reservation"]],
        },
        evidence_sources=[role_ref],
        limitations=limitations,
        mapping_views=["phase2e-v1"],
        relationships=[{
            "kind": "independent-visitor",
            "target_range": interval(owner["visitor"]["target_start"], owner["visitor"]["target_end_exclusive"]),
            "direction": "unresolved",
        }],
        selection_layer="semantic-phase2h",
    ))

    correction_comments = {
        "handle-resolver": "handle resolver; resolves a two-word handle and does not consume RewardMoney or RewardRenown",
        "scalar-key-consumer": "scalar key consumer; key in r4; RewardRenown -> +0x20/4, RewardMoney -> +0x24/4; signedness and representation unresolved",
        "boolean-like-key-consumer": "Boolean-like key consumer; AppearOnWorldMap -> +0x4D/1 normalized byte",
    }
    for index, correction in enumerate(view["semantic_corrections"]):
        mapping_row = all_by_target[correction["target"]]
        target_range = interval(mapping_row["target_start"], mapping_row["target_end_exclusive"])
        donor_range = interval(mapping_row["donor_start"], mapping_row["donor_end_exclusive"])
        ref = source_reference(registry, PHASE2H_VIEW, f"/semantic_corrections/{index}", correction)
        detail = correction_comments[correction["kind"]]
        result.append(annotation(
            display_kind="semantic-edge-correction",
            target_range=target_range,
            donor_range=donor_range,
            stable_identity="P2G-OWNER-DECISION-001:correction:" + correction["kind"],
            display_title="Owner-reviewed Packet C semantic edge correction",
            comment=(
                f"SEMANTIC EVIDENCE — OWNER-REVIEWED CORRECTION — {correction['donor']} -> "
                f"{correction['target']}: {detail}. CONTEXTUAL EVIDENCE — NOT A FUNCTION NAME."
            ),
            mapping=None,
            semantic={
                "grade": "owner-reviewed semantic correction",
                "review_status": "owner-reviewed",
                "decision_id": view["decision_record_id"],
                "correction_kind": correction["kind"],
                "reservations": [],
            },
            evidence_sources=[ref],
            limitations=["Correction changes semantic attribution only; the corresponding mapping is unchanged."],
            mapping_views=["phase2e-v1"],
            relationships=[{
                "kind": "corrected-edge",
                "donor": correction["donor"],
                "target": correction["target"],
            }],
            selection_layer="semantic-phase2h",
        ))

    rejected = view["rejected_aliases"][0]
    ref = source_reference(registry, PHASE2H_VIEW, "/rejected_aliases/0", rejected)
    result.append(annotation(
        display_kind="rejected-alias-warning",
        target_range=owner_target,
        donor_range=owner_donor,
        stable_identity="P2G-OWNER-DECISION-001:rejected:" + rejected["terminal"],
        display_title="Rejected Packet C alias",
        comment=(
            "SEMANTIC EVIDENCE WARNING — OWNER-REVIEWED REJECTION — SetObjectiveTag "
            "(S-26C37A0D8DC5C81610D44E94) is a rejected false high-half alias, not a Packet C key or "
            "semantic vote. TU1 0x820C0000 is an interior pointer to different text and is not a valid Packet C string."
        ),
        mapping=None,
        semantic={
            "grade": "rejected-false-high-half-alias",
            "review_status": "owner-reviewed-rejection",
            "decision_id": view["decision_record_id"],
            "terminal_id": rejected["terminal"],
            "rejected_evidence_text": rejected["text"],
            "reservations": [],
        },
        evidence_sources=[ref],
        limitations=["The interior TU1 address is evidence against the alias and is not an annotation target."],
        mapping_views=["phase2e-v1"],
        relationships=[{
            "kind": "rejected-alias",
            "terminal_id": rejected["terminal"],
            "interior_address_not_valid_evidence": "0x820C0000",
        }],
        selection_layer="semantic-phase2h",
    ))
    return result


def validate_index(document: dict[str, Any]) -> None:
    sources.require(document["schema"] == {"name": "fable2-prototype-analyst-annotation-normalized-index", "version": 1}, "Wrong index schema")
    records = document["records"]
    sources.require(len(records) == len({row["annotation_id"] for row in records}), "Duplicate annotation IDs")
    sources.require(records == sorted(records, key=record_sort_key), "Index ordering changed")
    counts = document["counts"]
    sources.require(counts["closed_correspondences"] == 15299, "Closed index count changed")
    sources.require(counts["overlay_additions"] == 83, "Addition index count changed")
    sources.require(counts["suppression_tombstones"] == 3, "Suppression index count changed")
    sources.require(counts["excluded_proposals"] == 720, "Exclusion index count changed")
    sources.require(counts["phase2f_contexts"] == 116, "Semantic index count changed")
    sources.require(counts["phase2f_new_routes"] == 115 and counts["phase2f_strengthened_contexts"] == 1, "Phase 2F route split changed")
    sources.require(counts["phase2h_owner_reviewed_roles"] == 1, "Phase 2H role count changed")
    sources.require(counts["phase2h_corrections"] == 3 and counts["phase2h_rejected_aliases"] == 1, "Phase 2H correction counts changed")
    sources.require(counts["project_relevant_union"] == 82, "Project intersection union changed")
    sources.require(counts["closed_view_active"] == 15299 and counts["overlay_view_active"] == 15379, "Mapping view count changed")
    forbidden = {"function_name", "symbol_name", "rename_to", "canonical_label", "canonical_function_name", "semantic_function_name", "proposed_name"}

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            sources.require(not (set(value) & forbidden), "Forbidden naming field in annotation output")
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(document)
    for row in records:
        sources.require(row["canonical_name_authority"] is False, "Canonical-name flag changed")
        sources.require(row["production_mapping_authority"] is False, "Production-mapping flag changed")
        sources.require(row["runtime_authority"] is False, "Runtime flag changed")
        sources.require("\n" not in row["comment_body"] and "\r" not in row["comment_body"] and "\t" not in row["comment_body"], "Unsafe comment body")
        sources.require("[F2PA:" not in row["comment_body"], "Namespace marker injection survived")


def build_index() -> dict[str, Any]:
    committed_pins = sources.read_json(sources.SOURCE_PINS_PATH)
    sources.validate_source_pins(committed_pins)
    registry = source_registry(committed_pins)

    closed = sources.read_json(PHASE2A_MAP)
    effective = sources.read_json(PHASE2E_EFFECTIVE)
    delta = sources.read_json(PHASE2E_DELTA)
    exclusions = sources.read_json(PHASE2E_EXCLUSIONS)
    intersections = sources.read_json(PHASE2F_INTERSECTIONS)
    queues = sources.read_json(PHASE2F_QUEUES)
    route_delta = sources.read_json(PHASE2F_DELTA)
    phase2g = sources.read_json(PHASE2G_SUMMARY)
    phase2g_selection = sources.read_json(PHASE2G_SELECTION)
    phase2h = sources.read_json(PHASE2H_VIEW)

    sources.require(len(closed["records"]) == 15299, "Closed Phase 2A map changed")
    sources.require(len(effective["records"]) == 15379, "Phase 2E effective map changed")
    sources.require(delta["counts"] == {
        "actions": 86,
        "mapping_additions": 83,
        "reserved_mapping_additions": 66,
        "semantic_transport_suppressions": 3,
        "unreserved_mapping_additions": 17,
    }, "Phase 2E delta arithmetic changed")
    sources.require(exclusions["counts"] == {
        "held_original_strong_excluded": 3,
        "physics_candidates_excluded": 2,
        "probable_proposals_excluded": 715,
        "unapproved_ledger_records_excluded": 5,
    }, "Phase 2E exclusion counts changed")
    sources.require(route_delta["counts"] == {"changed": 116, "newly_corroborated": 1, "newly_routable": 115}, "Phase 2F route delta changed")

    mapping_records, _, all_by_target = build_mapping_records(registry, closed, delta, intersections)
    records = mapping_records
    records.extend(build_exclusion_records(registry, exclusions))
    records.extend(build_phase2f_records(registry, queues, phase2g, phase2g_selection, all_by_target))
    records.extend(build_phase2h_records(registry, phase2h, all_by_target))
    records, duplicate_count = deduplicate_records(records)

    active_closed = [row for row in records if row["selection_layer"] == "mapping-active" and "closed-phase2a-default" in row["mapping_views"]]
    active_overlay = [row for row in records if row["selection_layer"] == "mapping-active" and "phase2e-v1" in row["mapping_views"]]
    additions = [row for row in records if row["display_kind"] == "overlay-addition"]
    semantic_rows = [row for row in records if row["selection_layer"] == "semantic-phase2f"]
    project_union = [row for row in additions if set(row["project_memberships"]) & {"closure", "coverage", "ghidra"}]
    counts = {
        "records": len(records),
        "deduplicated_inputs": duplicate_count,
        "closed_correspondences": sum(row["display_kind"] == "correspondence-provenance" for row in records),
        "overlay_additions": len(additions),
        "suppression_tombstones": sum(row["display_kind"] == "suppression-warning" for row in records),
        "reserved_additions": sum(bool(row["mapping"]["reservations"]) for row in additions),
        "unreserved_additions": sum(not row["mapping"]["reservations"] for row in additions),
        "excluded_proposals": sum(row["display_kind"] == "excluded-proposal-warning" for row in records),
        "physics_excluded": 2,
        "held_strong_excluded": 3,
        "probable_excluded": 715,
        "phase2f_contexts": len(semantic_rows),
        "phase2f_new_routes": sum(bool(row["semantic"]["newly_routable"]) for row in semantic_rows),
        "phase2f_strengthened_contexts": sum(not row["semantic"]["newly_routable"] for row in semantic_rows),
        "phase2g_static_review_records": sum(row["display_kind"] == "corroborated-review-evidence" for row in semantic_rows),
        "phase2h_owner_reviewed_roles": sum(row["display_kind"] == "owner-reviewed-contextual-role" for row in records),
        "phase2h_corrections": sum(row["display_kind"] == "semantic-edge-correction" for row in records),
        "phase2h_rejected_aliases": sum(row["display_kind"] == "rejected-alias-warning" for row in records),
        "project_relevant_union": len(project_union),
        "project_membership_closure": sum("closure" in row["project_memberships"] for row in additions),
        "project_membership_coverage": sum("coverage" in row["project_memberships"] for row in additions),
        "project_membership_ghidra": sum("ghidra" in row["project_memberships"] for row in additions),
        "closed_view_active": len(active_closed),
        "overlay_view_active": len(active_overlay),
    }
    document = envelope(
        "fable2-prototype-analyst-annotation-normalized-index",
        source_pins=sources.identity(sources.SOURCE_PINS_PATH),
        counts=counts,
        records=records,
        ordering="target range, stable authority order, evidence-derived annotation ID",
    )
    validate_index(document)
    return document


def write_index(check: bool = False) -> dict[str, Any]:
    return sources.write_json(INDEX_PATH, build_index(), check)


def _exact_selection_identity(path: str | None, expected: Path, sha256: str | None) -> dict[str, Any]:
    selection_require(path == expected.as_posix(), "Explicit opt-in requires exact repository-relative path: " + expected.as_posix())
    selection_require(sha256 is not None, "Explicit opt-in requires SHA-256: " + expected.as_posix())
    actual = sources.identity(expected)
    selection_require(sha256.upper() == actual["sha256"], "Explicit opt-in hash mismatch: " + expected.as_posix())
    return actual


def validate_selections(arguments: argparse.Namespace) -> dict[str, Any]:
    mapping_view = arguments.mapping_view
    semantic_view = arguments.semantic_view
    selection_require(mapping_view in MAPPING_VIEWS, "Unknown mapping view")
    selection_require(semantic_view in SEMANTIC_VIEWS, "Unknown semantic view")

    phase2e_values = [
        arguments.phase2e_decision,
        arguments.phase2e_decision_sha256,
        arguments.phase2e_delta,
        arguments.phase2e_delta_sha256,
        arguments.phase2e_effective_map,
        arguments.phase2e_effective_map_sha256,
    ]
    mapping = {"view": mapping_view, "active_count": 0, "opt_in": None}
    if mapping_view == "none":
        selection_require(not any(phase2e_values), "Phase 2E inputs are over-broad when mapping view is none")
    elif mapping_view == "closed-phase2a-default":
        selection_require(not any(phase2e_values), "Phase 2E inputs supplied for closed Phase 2A selection")
        provenance = overlay.load_default_mapping()
        selection_require(provenance["selection"] == mapping_view and provenance["mapping_count"] == 15299, "Closed selection validation failed")
        mapping["active_count"] = 15299
        mapping["opt_in"] = provenance
    else:
        selection_require(all(value is not None for value in phase2e_values), "Partial Phase 2E opt-in refused")
        decision = _exact_selection_identity(arguments.phase2e_decision, PHASE2E_DECISION, arguments.phase2e_decision_sha256)
        delta = _exact_selection_identity(arguments.phase2e_delta, PHASE2E_DELTA, arguments.phase2e_delta_sha256)
        effective_identity = _exact_selection_identity(arguments.phase2e_effective_map, PHASE2E_EFFECTIVE, arguments.phase2e_effective_map_sha256)
        # The frozen loader prints its own successful verifier summary. Keep
        # that diagnostic out of Phase 2I's machine-readable stdout.
        with contextlib.redirect_stdout(io.StringIO()):
            _, provenance = overlay.load_opt_in_mapping(
                "phase2e-v1",
                ROOT / PHASE2E_DECISION,
                decision["sha256"],
                ROOT / PHASE2E_DELTA,
                delta["sha256"],
                ROOT / PHASE2E_EFFECTIVE,
                effective_identity["sha256"],
            )
        selection_require(provenance["selection"] == "phase2e-v1" and provenance["mapping_count"] == 15379, "Phase 2E opt-in validation failed")
        mapping["active_count"] = 15379
        mapping["opt_in"] = provenance

    phase2h_values = [
        arguments.phase2h_source_pins,
        arguments.phase2h_source_pins_sha256,
        arguments.phase2h_decision,
        arguments.phase2h_decision_sha256,
        arguments.phase2h_delta,
        arguments.phase2h_delta_sha256,
        arguments.phase2h_view,
        arguments.phase2h_view_sha256,
    ]
    semantic = {"view": semantic_view, "context_count": 0, "opt_in": None}
    if semantic_view != "phase2h-v1":
        selection_require(not any(phase2h_values), "Phase 2H inputs supplied without phase2h-v1 selection")
    if semantic_view == "phase2f-evidence":
        selection_require(mapping_view == "phase2e-v1", "Phase 2F evidence requires the exact Phase 2E mapping view")
        semantic["context_count"] = 116
        semantic["opt_in"] = {"selection": "phase2f-evidence", "owner_approval": False}
    elif semantic_view == "phase2h-v1":
        selection_require(mapping_view == "phase2e-v1", "Phase 2H reviewed role requires its compatible Phase 2E mapping view")
        selection_require(all(value is not None for value in phase2h_values), "Partial Phase 2H opt-in refused")
        identities = {
            "source_pins": _exact_selection_identity(arguments.phase2h_source_pins, PHASE2H_PINS, arguments.phase2h_source_pins_sha256),
            "decision": _exact_selection_identity(arguments.phase2h_decision, PHASE2H_DECISION, arguments.phase2h_decision_sha256),
            "delta": _exact_selection_identity(arguments.phase2h_delta, PHASE2H_DELTA, arguments.phase2h_delta_sha256),
            "view": _exact_selection_identity(arguments.phase2h_view, PHASE2H_VIEW, arguments.phase2h_view_sha256),
        }
        view = sources.read_json(PHASE2H_VIEW)
        selection_require(view["layer_version"] == "phase2h-v1" and view["opt_in_applied"] is True, "Wrong Phase 2H materialized view")
        selection_require(len(view["reviewed_roles"]) == 1 and view["approved_packets"] == ["C"], "Phase 2H opt-in is over-broad")
        semantic["context_count"] = 1
        semantic["opt_in"] = {"selection": "phase2h-v1", "identities": identities}
    return {"mapping": mapping, "semantic": semantic}


def _load_index() -> dict[str, Any]:
    committed_pins = sources.read_json(sources.SOURCE_PINS_PATH)
    sources.validate_source_pins(committed_pins)
    document = sources.read_json(INDEX_PATH)
    validate_index(document)
    if (ROOT / SUMMARY_PATH).is_file():
        summary = sources.read_json(SUMMARY_PATH)
        if summary.get("result") == "pass":
            matches = [row for row in summary.get("artifacts", []) if row["path"] == INDEX_PATH.as_posix()]
            sources.require(len(matches) == 1, "Published summary does not bind exactly one normalized index")
            sources.check_identity(matches[0])
    return document


def selected_records(document: dict[str, Any], selection: dict[str, Any]) -> list[dict[str, Any]]:
    mapping_view = selection["mapping"]["view"]
    semantic_view = selection["semantic"]["view"]
    result = []
    for row in document["records"]:
        layer = row["selection_layer"]
        if layer.startswith("mapping-") and mapping_view != "none" and mapping_view in row["mapping_views"]:
            result.append(row)
        elif layer == "semantic-phase2f" and semantic_view == "phase2f-evidence":
            result.append(row)
        elif layer == "semantic-phase2h" and semantic_view == "phase2h-v1":
            result.append(row)
    return sorted(result, key=record_sort_key)


def query_records(records: list[dict[str, Any]], addresses: Iterable[str | int]) -> dict[str, Any]:
    requested = sorted({address(value) for value in addresses})
    exact = []
    containing = []
    for row in records:
        start = address(row["target"]["range"]["start"])
        end = address(row["target"]["range"]["end_exclusive"])
        if any(value == start for value in requested):
            exact.append(row)
        elif any(start < value < end for value in requested):
            containing.append(row)
    return {
        "addresses": [address_text(value) for value in requested],
        "exact_matches": exact,
        "containing_range_matches": containing,
        "reason": None if exact or containing else "No selected frozen evidence exists for the requested TU1 address(es).",
    }


def profile_records(
    records: list[dict[str, Any]],
    profile: str,
    selection: dict[str, Any],
    addresses: Iterable[str | int] = (),
    bulk: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    selection_require(profile in PROFILES, "Unknown export profile")
    if profile == "address":
        requested = list(addresses)
        selection_require(bool(requested), "Address profile requires at least one explicit TU1 address")
        query = query_records(records, requested)
        chosen = query["exact_matches"] + query["containing_range_matches"]
    elif profile == "phase2h-approved":
        selection_require(selection["semantic"]["view"] == "phase2h-v1", "phase2h-approved requires phase2h-v1")
        chosen = [row for row in records if row["selection_layer"] == "semantic-phase2h"]
        chosen.extend(row for row in records if row["selection_layer"] == "mapping-active" and row["mapping"]["record_id"] == ":".join(PACKET_C_PAIR))
    elif profile == "overlay-review":
        selection_require(selection["mapping"]["view"] == "phase2e-v1", "overlay-review requires phase2e-v1")
        chosen = [row for row in records if row["display_kind"] in {"overlay-addition", "suppression-warning"}]
    elif profile == "project-relevant":
        selection_require(selection["mapping"]["view"] == "phase2e-v1", "project-relevant requires phase2e-v1")
        chosen = [
            row for row in records
            if row["display_kind"] == "overlay-addition"
            and set(row["project_memberships"]) & {"closure", "coverage", "ghidra"}
        ]
    elif profile == "semantic-review":
        selection_require(selection["semantic"]["view"] == "phase2f-evidence", "semantic-review requires phase2f-evidence")
        chosen = [row for row in records if row["selection_layer"] == "semantic-phase2f"]
    elif profile == "excluded-review":
        selection_require(selection["mapping"]["view"] == "phase2e-v1", "excluded-review requires phase2e-v1")
        chosen = [row for row in records if row["display_kind"] == "excluded-proposal-warning"]
    else:
        selection_require(selection["mapping"]["view"] != "none", "all-correspondences requires an explicit mapping view")
        selection_require(bulk, "all-correspondences requires --bulk")
        chosen = [row for row in records if row["selection_layer"] == "mapping-active"]

    chosen, duplicate_count = deduplicate_records(chosen)
    counts = annotation_counts(chosen)
    counts["deduplicated"] = duplicate_count
    counts["filtered"] = len(records) - len(chosen)
    return chosen, counts


def annotation_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    def reservations(row: dict[str, Any]) -> list[Any]:
        if row["mapping"] is not None:
            return row["mapping"].get("reservations", [])
        if row["semantic"] is not None:
            return row["semantic"].get("reservations", [])
        return []

    active_mappings = [row for row in records if row["selection_layer"] == "mapping-active"]
    semantic_contexts = [row for row in records if row["selection_layer"] == "semantic-phase2f"]
    return {
        "selected": len(records),
        "excluded": sum(row["display_kind"] == "excluded-proposal-warning" for row in records),
        "suppressed": sum(row["display_kind"] == "suppression-warning" for row in records),
        "reserved": sum(bool(reservations(row)) for row in records),
        "unreserved": sum(not reservations(row) for row in records),
        "approved_role": sum(row["display_kind"] == "owner-reviewed-contextual-role" for row in records),
        "unreviewed_context": sum(row["selection_layer"] == "semantic-phase2f" for row in records),
        "rejected_alias": sum(row["display_kind"] == "rejected-alias-warning" for row in records),
        "active_correspondence": len(active_mappings),
        "reserved_active_correspondence": sum(bool(row["mapping"]["reservations"]) for row in active_mappings),
        "unreserved_active_correspondence": sum(not row["mapping"]["reservations"] for row in active_mappings),
        "reserved_unreviewed_context": sum(bool(row["semantic"]["reservations"]) for row in semantic_contexts),
        "unreserved_unreviewed_context": sum(not row["semantic"]["reservations"] for row in semantic_contexts),
    }


def human_query(document: dict[str, Any], selection: dict[str, Any]) -> str:
    lines = [
        "Phase 2I analyst lookup",
        f"Mapping view: {selection['mapping']['view']}",
        f"Semantic view: {selection['semantic']['view']}",
        "Addresses: " + ", ".join(document["addresses"]),
    ]
    for label, key in (("Exact matches", "exact_matches"), ("Containing-range matches", "containing_range_matches")):
        rows = document[key]
        lines.append(f"{label}: {len(rows)}")
        for row in rows:
            lines.append(f"  {row['namespace_marker']} {row['target']['range']['start']} {row['comment_body']}")
            for source in row["sources"]:
                lines.append(f"    source {source['path']}#{source['json_pointer']} {source['sha256']}")
    if document["reason"]:
        lines.append("Reason: " + document["reason"])
    return "\n".join(lines) + "\n"


def add_selection_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--mapping-view", choices=MAPPING_VIEWS, default="none")
    parser.add_argument("--semantic-view", choices=SEMANTIC_VIEWS, default="none")
    parser.add_argument("--phase2e-decision")
    parser.add_argument("--phase2e-decision-sha256")
    parser.add_argument("--phase2e-delta")
    parser.add_argument("--phase2e-delta-sha256")
    parser.add_argument("--phase2e-effective-map")
    parser.add_argument("--phase2e-effective-map-sha256")
    parser.add_argument("--phase2h-source-pins")
    parser.add_argument("--phase2h-source-pins-sha256")
    parser.add_argument("--phase2h-decision")
    parser.add_argument("--phase2h-decision-sha256")
    parser.add_argument("--phase2h-delta")
    parser.add_argument("--phase2h-delta-sha256")
    parser.add_argument("--phase2h-view")
    parser.add_argument("--phase2h-view-sha256")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command")
    index = commands.add_parser("index", help="generate or replay-check the normalized ignored index")
    index.add_argument("--check", action="store_true")
    commands.add_parser("validate", help="validate frozen sources and the normalized index without writing")
    query = commands.add_parser("query", help="query one or more explicit TU1 guest addresses")
    add_selection_arguments(query)
    query.add_argument("--address", action="append", required=True)
    query.add_argument("--format", choices=("human", "json"), default="human")
    return result


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    if arguments.command is None:
        parser().print_help()
        return 0
    try:
        if arguments.command == "index":
            result = write_index(arguments.check)
            print(f"PASS normalized annotation index: {result['size']} bytes {result['sha256']}")
            return 0
        if arguments.command == "validate":
            document = _load_index()
            print(f"PASS Phase 2I annotation index: {len(document['records'])} records")
            return 0
        selection = validate_selections(arguments)
        document = _load_index()
        chosen = selected_records(document, selection)
        query = query_records(chosen, arguments.address)
        if arguments.format == "json":
            sys.stdout.buffer.write(sources.payload(envelope(
                "fable2-prototype-analyst-annotation-bundle",
                source_pins=sources.identity(sources.SOURCE_PINS_PATH),
                selection=selection,
                profile="address",
                counts=annotation_counts(query["exact_matches"] + query["containing_range_matches"]),
                query=query,
                records=query["exact_matches"] + query["containing_range_matches"],
            )))
        else:
            sys.stdout.write(human_query(query, selection))
        return 0 if query["exact_matches"] or query["containing_range_matches"] else 1
    except SelectionError as error:
        print("REFUSED:", error, file=sys.stderr)
        return 2
    except (sources.EvidenceError, OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        print("VALIDATION FAILURE:", error, file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
