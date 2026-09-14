"""Export deterministic Phase 2I analyst bundles and preview-only Ghidra plans."""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/phase2i"))

import Fable2AnalystAnnotations as annotations  # noqa: E402
import Fable2AnalystSources as sources  # noqa: E402


OUTPUT_FILES = {
    "bundle": "annotations.json",
    "table": "annotations.tsv",
    "plan": "ghidra-plan.json",
    "rollback": "rollback-manifest.json",
    "preview": "preview.txt",
    "receipt": "export-receipt.json",
}


def namespaced_block(record: dict[str, Any]) -> str:
    return record["namespace_marker"] + "\n" + record["comment_body"]


def block_identity(record: dict[str, Any]) -> str:
    return sources.digest(namespaced_block(record).encode("utf-8"))


def build_bundle(
    records: list[dict[str, Any]],
    selection: dict[str, Any],
    profile: str,
    counts: dict[str, int],
    requested_addresses: list[str],
    index_identity: dict[str, Any],
) -> dict[str, Any]:
    return annotations.envelope(
        "fable2-prototype-analyst-annotation-bundle",
        source_pins=sources.identity(sources.SOURCE_PINS_PATH),
        normalized_index=index_identity,
        selection=selection,
        profile=profile,
        requested_addresses=[annotations.address_text(value) for value in sorted({annotations.address(item) for item in requested_addresses})],
        counts=counts,
        records=records,
        ordering="target range, stable authority order, evidence-derived annotation ID",
    )


def build_ghidra_plan(
    records: list[dict[str, Any]],
    selection: dict[str, Any],
    profile: str,
    counts: dict[str, int],
    index_identity: dict[str, Any],
) -> dict[str, Any]:
    entries = []
    for record in records:
        block = namespaced_block(record)
        block_sha256 = sources.digest(block.encode("utf-8"))
        entries.append({
            "annotation_id": record["annotation_id"],
            "target_address": record["target"]["range"]["start"],
            "target_range": record["target"]["range"],
            "comment_type": record["suggestion"]["comment_type"],
            "bookmark_category": record["suggestion"]["bookmark_category"],
            "namespaced_content": block,
            "namespaced_block_sha256": block_sha256,
            "rollback_identity": {
                "annotation_id": record["annotation_id"],
                "marker": record["namespace_marker"],
                "exact_block_sha256": block_sha256,
            },
            "collision_disposition": "append-if-absent; identical-is-idempotent; stale-same-id-is-conflict",
        })
    return annotations.envelope(
        "fable2-prototype-analyst-annotation-ghidra-plan",
        source_pins=sources.identity(sources.SOURCE_PINS_PATH),
        normalized_index=index_identity,
        selection=selection,
        profile=profile,
        counts=counts,
        mode="preview-only-data-plan",
        executable_code=False,
        naming_capability=False,
        database_write_capability=False,
        entries=entries,
        ordering="same as annotation bundle",
    )


def build_rollback_manifest(
    records: list[dict[str, Any]],
    selection: dict[str, Any],
    profile: str,
    counts: dict[str, int],
    index_identity: dict[str, Any],
) -> dict[str, Any]:
    entries = []
    for record in records:
        block_sha256 = block_identity(record)
        entries.append({
            "annotation_id": record["annotation_id"],
            "target_address": record["target"]["range"]["start"],
            "owned_kinds": [record["suggestion"]["comment_type"], "BOOKMARK_SUGGESTION"],
            "comment_type": record["suggestion"]["comment_type"],
            "bookmark_category": record["suggestion"]["bookmark_category"],
            "exact_namespaced_block_sha256": block_sha256,
            "expected_removal_selector": {
                "annotation_id": record["annotation_id"],
                "marker": record["namespace_marker"],
                "exact_block_sha256": block_sha256,
                "exact_text_required": True,
            },
            "collision_disposition": "conflict-on-stale-content; never-overwrite-user-content",
        })
    return annotations.envelope(
        "fable2-prototype-analyst-annotation-rollback-manifest",
        source_pins=sources.identity(sources.SOURCE_PINS_PATH),
        normalized_index=index_identity,
        selection=selection,
        profile=profile,
        counts=counts,
        pre_existing_analyst_content_owned_by_phase2i=False,
        ownership_rule="Only exact marker, exact block bytes, and exact SHA-256 identify Phase 2I content.",
        entries=entries,
    )


def tsv_bytes(records: list[dict[str, Any]]) -> bytes:
    output = io.StringIO(newline="")
    fields = [
        "annotation_id",
        "target_start",
        "target_end_exclusive",
        "donor_start",
        "donor_end_exclusive",
        "display_kind",
        "display_title",
        "mapping_status",
        "evidence_grade",
        "reservations",
        "semantic_grade",
        "review_status",
        "project_memberships",
        "comment_body",
        "source_pointers",
        "namespace_marker",
    ]
    writer = csv.DictWriter(output, fieldnames=fields, dialect="excel-tab", lineterminator="\n")
    writer.writeheader()
    for record in records:
        mapping = record["mapping"] or {}
        semantic = record["semantic"] or {}
        reservations = mapping.get("reservations", semantic.get("reservations", []))
        source_pointers = [row["path"] + "#" + row["json_pointer"] for row in record["sources"]]
        writer.writerow({
            "annotation_id": record["annotation_id"],
            "target_start": record["target"]["range"]["start"],
            "target_end_exclusive": record["target"]["range"]["end_exclusive"],
            "donor_start": record["donor"]["range"]["start"] if record["donor"] else "",
            "donor_end_exclusive": record["donor"]["range"]["end_exclusive"] if record["donor"] else "",
            "display_kind": record["display_kind"],
            "display_title": record["display_title"],
            "mapping_status": mapping.get("status", ""),
            "evidence_grade": mapping.get("evidence_grade", ""),
            "reservations": json.dumps(reservations, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            "semantic_grade": semantic.get("grade", ""),
            "review_status": semantic.get("review_status", ""),
            "project_memberships": json.dumps(record["project_memberships"], ensure_ascii=False, separators=(",", ":")),
            "comment_body": record["comment_body"],
            "source_pointers": json.dumps(source_pointers, ensure_ascii=False, separators=(",", ":")),
            "namespace_marker": record["namespace_marker"],
        })
    return output.getvalue().encode("utf-8")


def preview_bytes(
    records: list[dict[str, Any]],
    selection: dict[str, Any],
    profile: str,
    counts: dict[str, int],
    limit: int,
) -> bytes:
    annotations.selection_require(0 <= limit <= 1000, "Preview limit must be between 0 and 1000")
    displayed = records[:limit]
    lines = [
        "Phase 2I dry-run annotation preview",
        f"Profile: {profile}",
        f"Mapping view: {selection['mapping']['view']}",
        f"Semantic view: {selection['semantic']['view']}",
        f"Selected: {counts['selected']}",
        f"Displayed: {len(displayed)}",
        f"Omitted by preview bound: {len(records) - len(displayed)}",
        "No Ghidra project or database was opened or changed.",
    ]
    for record in displayed:
        lines.extend([
            "",
            f"Target {record['target']['range']['start']} [{record['display_kind']}]",
            namespaced_block(record),
        ])
    return ("\n".join(lines) + "\n").encode("utf-8")


def _marker_conflict(existing_comment: str, record: dict[str, Any]) -> bool:
    marker = record["namespace_marker"]
    return marker in existing_comment and namespaced_block(record) not in existing_comment


def simulate_collision(
    existing_comment: str | None,
    existing_bookmarks: list[dict[str, Any]],
    record: dict[str, Any],
) -> dict[str, Any]:
    before = "" if existing_comment is None else existing_comment
    block = namespaced_block(record)
    if _marker_conflict(before, record):
        disposition = "conflict-stale-owned-block"
        after = before
    elif block in before:
        disposition = "idempotent-identical-owned-block"
        after = before
    elif before:
        disposition = "append-after-user-content"
        after = before + "\n" + block
    else:
        disposition = "add-to-empty-comment"
        after = block
    return {
        "annotation_id": record["annotation_id"],
        "disposition": disposition,
        "comment_before": before,
        "comment_after_preview": after,
        "user_comment_prefix_preserved": after == before or after.startswith(before),
        "bookmarks_before": existing_bookmarks,
        "bookmarks_after_preview": list(existing_bookmarks),
        "unrelated_bookmarks_preserved": True,
        "write_performed": False,
    }


def removal_preview(existing_comment: str, record: dict[str, Any]) -> dict[str, Any]:
    block = namespaced_block(record)
    marker = record["namespace_marker"]
    expected_hash = block_identity(record)
    if block not in existing_comment:
        disposition = "conflict-stale-owned-block" if marker in existing_comment else "exact-owned-block-absent"
        return {
            "annotation_id": record["annotation_id"],
            "disposition": disposition,
            "comment_before": existing_comment,
            "comment_after_preview": existing_comment,
            "exact_block_sha256": expected_hash,
            "write_performed": False,
        }
    occurrences = existing_comment.count(block)
    if occurrences != 1:
        return {
            "annotation_id": record["annotation_id"],
            "disposition": "conflict-multiple-identical-owned-blocks",
            "comment_before": existing_comment,
            "comment_after_preview": existing_comment,
            "exact_block_sha256": expected_hash,
            "write_performed": False,
        }
    if existing_comment == block:
        after = ""
    elif ("\n" + block) in existing_comment:
        after = existing_comment.replace("\n" + block, "", 1)
    else:
        after = existing_comment.replace(block, "", 1)
    return {
        "annotation_id": record["annotation_id"],
        "disposition": "exact-owned-block-removal-preview",
        "comment_before": existing_comment,
        "comment_after_preview": after,
        "exact_block_sha256": expected_hash,
        "write_performed": False,
    }


def validate_reconciliation(
    bundle: dict[str, Any],
    plan: dict[str, Any],
    rollback: dict[str, Any],
    table: bytes,
) -> None:
    bundle_ids = [row["annotation_id"] for row in bundle["records"]]
    plan_ids = [row["annotation_id"] for row in plan["entries"]]
    rollback_ids = [row["annotation_id"] for row in rollback["entries"]]
    table_rows = list(csv.DictReader(io.StringIO(table.decode("utf-8")), dialect="excel-tab"))
    table_ids = [row["annotation_id"] for row in table_rows]
    sources.require(bundle_ids == plan_ids == rollback_ids == table_ids, "JSON/TSV/plan/rollback identity mismatch")
    sources.require(len(bundle_ids) == bundle["counts"]["selected"], "Export count mismatch")
    for record, plan_entry, rollback_entry in zip(bundle["records"], plan["entries"], rollback["entries"]):
        expected = block_identity(record)
        sources.require(plan_entry["namespaced_block_sha256"] == expected, "Plan block hash mismatch")
        sources.require(rollback_entry["exact_namespaced_block_sha256"] == expected, "Rollback block hash mismatch")


def export_root(value: str) -> tuple[Path, Path]:
    relative = Path(value)
    annotations.selection_require(not relative.is_absolute() and ".." not in relative.parts, "Export output must be repository-relative")
    resolved = (ROOT / relative).resolve()
    allowed = (ROOT / sources.OUT).resolve()
    annotations.selection_require(resolved.is_relative_to(allowed), "Export output must be under out/prototype-archaeology/phase2i")
    return relative, resolved


def write_bytes(relative: Path, data: bytes) -> dict[str, Any]:
    target = sources.output_path(relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return {"path": relative.as_posix(), "size": len(data), "sha256": sources.digest(data)}


def export(arguments: argparse.Namespace) -> dict[str, Any]:
    selection = annotations.validate_selections(arguments)
    index = annotations._load_index()
    selected = annotations.selected_records(index, selection)
    records, counts = annotations.profile_records(
        selected,
        arguments.profile,
        selection,
        addresses=arguments.address,
        bulk=arguments.bulk,
    )
    relative_root, resolved_root = export_root(arguments.output)
    index_identity = sources.identity(annotations.INDEX_PATH)
    bundle = build_bundle(records, selection, arguments.profile, counts, arguments.address, index_identity)
    plan = build_ghidra_plan(records, selection, arguments.profile, counts, index_identity)
    rollback = build_rollback_manifest(records, selection, arguments.profile, counts, index_identity)
    table = tsv_bytes(records)
    preview = preview_bytes(records, selection, arguments.profile, counts, arguments.preview_limit)
    validate_reconciliation(bundle, plan, rollback, table)

    # No directory is created until every input, selection, profile, and output
    # document has passed validation in memory.
    resolved_root.mkdir(parents=True, exist_ok=True)
    artifacts = [
        write_bytes(relative_root / OUTPUT_FILES["bundle"], sources.payload(bundle)),
        write_bytes(relative_root / OUTPUT_FILES["table"], table),
        write_bytes(relative_root / OUTPUT_FILES["plan"], sources.payload(plan)),
        write_bytes(relative_root / OUTPUT_FILES["rollback"], sources.payload(rollback)),
        write_bytes(relative_root / OUTPUT_FILES["preview"], preview),
    ]
    receipt = annotations.envelope(
        "fable2-prototype-analyst-annotation-receipt",
        source_pins=sources.identity(sources.SOURCE_PINS_PATH),
        normalized_index=index_identity,
        profile=arguments.profile,
        selection=selection,
        counts=counts,
        preview={"limit": arguments.preview_limit, "displayed": min(len(records), arguments.preview_limit), "omitted": max(0, len(records) - arguments.preview_limit)},
        artifacts=artifacts,
        output_root=relative_root.as_posix(),
        result="pass",
    )
    receipt_identity = write_bytes(relative_root / OUTPUT_FILES["receipt"], sources.payload(receipt))
    return {"records": len(records), "counts": counts, "artifacts": artifacts, "receipt": receipt_identity}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    annotations.add_selection_arguments(result)
    result.add_argument("--profile", choices=annotations.PROFILES)
    result.add_argument("--output")
    result.add_argument("--address", action="append", default=[])
    result.add_argument("--bulk", action="store_true")
    result.add_argument("--preview-limit", type=int, default=100)
    return result


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    if arguments.profile is None and arguments.output is None:
        parser().print_help()
        return 0
    try:
        annotations.selection_require(arguments.profile is not None, "Export requires an explicit profile")
        annotations.selection_require(arguments.output is not None, "Export requires an explicit output path")
        result = export(arguments)
        print(f"PASS Phase 2I export: records={result['records']} receipt={result['receipt']['sha256']}")
        return 0 if result["records"] else 1
    except annotations.SelectionError as error:
        print("REFUSED:", error, file=sys.stderr)
        return 2
    except (sources.EvidenceError, OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        print("VALIDATION FAILURE:", error, file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
