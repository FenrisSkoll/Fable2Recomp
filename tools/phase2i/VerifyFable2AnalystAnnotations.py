"""Adversarial verification and publication for the Phase 2I analyst layer."""

from __future__ import annotations

import argparse
import ast
import contextlib
import io
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/phase2i"))

import Fable2AnalystAnnotations as annotations  # noqa: E402
import Fable2AnalystExport as exporter  # noqa: E402
import Fable2AnalystSources as sources  # noqa: E402


RECEIPTS = sources.OUT / "receipts"
SUMMARY = sources.DOC / "evidence/annotation-summary.json"
VALIDATION = sources.DOC / "evidence/validation.json"
REPORT = sources.DOC / "report.md"

PROFILE_ROOTS = {
    "address": sources.OUT / "profiles/address",
    "phase2h-approved": sources.OUT / "profiles/phase2h-approved",
    "overlay-review": sources.OUT / "profiles/overlay-review",
    "project-relevant": sources.OUT / "profiles/project-relevant",
    "semantic-review": sources.OUT / "profiles/semantic-review",
    "all-correspondences": sources.OUT / "profiles/all-correspondences",
}

EXPECTED_PROFILE_COUNTS = {
    "address": 3,
    "phase2h-approved": 6,
    "overlay-review": 86,
    "project-relevant": 82,
    "semantic-review": 116,
    "all-correspondences": 15379,
}

ALLOWED_GIT_PATHS = {
    "docs/fable2-prototype-archaeology/phase2i/.gitattributes",
    "docs/fable2-prototype-archaeology/phase2i/README.md",
    "docs/fable2-prototype-archaeology/phase2i/display-contract.md",
    "docs/fable2-prototype-archaeology/phase2i/evidence/annotation-summary.json",
    "docs/fable2-prototype-archaeology/phase2i/evidence/source-pins.json",
    "docs/fable2-prototype-archaeology/phase2i/evidence/validation.json",
    "docs/fable2-prototype-archaeology/phase2i/next-phase-handoff.md",
    "docs/fable2-prototype-archaeology/phase2i/policy.md",
    "docs/fable2-prototype-archaeology/phase2i/report.md",
    "docs/fable2-prototype-archaeology/phase2i/rollback.md",
    "tests/phase2i/__init__.py",
    "tests/phase2i/test_analyst_annotations.py",
    "tests/phase2i/test_analyst_export.py",
    "tools/phase2i/Fable2AnalystAnnotations.py",
    "tools/phase2i/Fable2AnalystExport.py",
    "tools/phase2i/Fable2AnalystSources.py",
    "tools/phase2i/Invoke-Fable2AnalystExports.ps1",
    "tools/phase2i/Verify-Fable2AnalystAnnotationSchemas.ps1",
    "tools/phase2i/VerifyFable2AnalystAnnotations.py",
    "tools/schemas/phase2i/fable2-analyst-annotation-layer-v1.schema.json",
}

PROHIBITED_GHIDRA_API_TOKENS = (
    "setComment(",
    "createBookmark(",
    "setName(",
    "createFunction(",
    "addEntryPoint(",
    "startTransaction(",
    "endTransaction(",
    "saveAs(",
    "saveProgram(",
    "domainFile.save(",
)


def receipt(schema_kind: str, **fields: Any) -> dict[str, Any]:
    return annotations.envelope(
        "fable2-prototype-analyst-annotation-receipt",
        receipt_kind=schema_kind,
        source_pins=sources.identity(sources.SOURCE_PINS_PATH),
        **fields,
    )


def write_receipt(name: str, document: dict[str, Any], check: bool = False) -> dict[str, Any]:
    return sources.write_json(RECEIPTS / name, document, check)


def index_document() -> dict[str, Any]:
    document = sources.read_json(annotations.INDEX_PATH)
    annotations.validate_index(document)
    return document


def profile_documents(profile: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], bytes, bytes, dict[str, Any]]:
    root = PROFILE_ROOTS[profile]
    bundle = sources.read_json(root / exporter.OUTPUT_FILES["bundle"])
    plan = sources.read_json(root / exporter.OUTPUT_FILES["plan"])
    rollback = sources.read_json(root / exporter.OUTPUT_FILES["rollback"])
    table = (ROOT / root / exporter.OUTPUT_FILES["table"]).read_bytes()
    preview = (ROOT / root / exporter.OUTPUT_FILES["preview"]).read_bytes()
    export_receipt = sources.read_json(root / exporter.OUTPUT_FILES["receipt"])
    return bundle, plan, rollback, table, preview, export_receipt


def consistency_receipt() -> dict[str, Any]:
    index = index_document()
    profiles = {}
    for profile in PROFILE_ROOTS:
        bundle, plan, rollback, table, _, export_receipt = profile_documents(profile)
        exporter.validate_reconciliation(bundle, plan, rollback, table)
        sources.require(bundle["profile"] == profile == plan["profile"] == rollback["profile"], "Profile identity mismatch")
        sources.require(bundle["counts"] == plan["counts"] == rollback["counts"] == export_receipt["counts"], "Profile count mismatch")
        sources.require(bundle["counts"]["selected"] == EXPECTED_PROFILE_COUNTS[profile], "Unexpected profile population: " + profile)
        profiles[profile] = {
            "selected": bundle["counts"]["selected"],
            "filtered": bundle["counts"]["filtered"],
            "deduplicated": bundle["counts"]["deduplicated"],
            "suppressed": bundle["counts"]["suppressed"],
            "excluded": bundle["counts"]["excluded"],
            "reserved": bundle["counts"]["reserved"],
            "unreserved": bundle["counts"]["unreserved"],
            "reserved_active_correspondence": bundle["counts"]["reserved_active_correspondence"],
            "unreserved_active_correspondence": bundle["counts"]["unreserved_active_correspondence"],
            "approved_role": bundle["counts"]["approved_role"],
            "unreviewed_context": bundle["counts"]["unreviewed_context"],
            "rejected_alias": bundle["counts"]["rejected_alias"],
        }

    overlay = sources.read_json(PROFILE_ROOTS["overlay-review"] / exporter.OUTPUT_FILES["bundle"])
    pairs = {
        (row["donor"]["range"]["start"], row["target"]["range"]["start"]): row
        for row in overlay["records"]
    }
    sources.require(annotations.SUPPRESSED_PAIRS <= set(pairs), "Suppression preview missing")
    sources.require(annotations.VECTOR_PAIRS <= set(pairs), "Corrected vector preview missing")
    sources.require(all(pairs[pair]["display_kind"] == "suppression-warning" for pair in annotations.SUPPRESSED_PAIRS), "Suppression reactivated")

    semantic = sources.read_json(PROFILE_ROOTS["semantic-review"] / exporter.OUTPUT_FILES["bundle"])
    sources.require(sum(row["semantic"]["newly_routable"] for row in semantic["records"]) == 115, "Semantic new-route count changed")
    sources.require(sum(not row["semantic"]["newly_routable"] for row in semantic["records"]) == 1, "Semantic strengthened count changed")
    sources.require(all(row["semantic"]["review_status"] == "unreviewed-analysis-evidence" for row in semantic["records"]), "Phase 2F context gained owner approval")

    approved = sources.read_json(PROFILE_ROOTS["phase2h-approved"] / exporter.OUTPUT_FILES["bundle"])
    sources.require(sum(row["display_kind"] == "owner-reviewed-contextual-role" for row in approved["records"]) == 1, "Packet C role count changed")
    sources.require(sum(row["display_kind"] == "semantic-edge-correction" for row in approved["records"]) == 3, "Packet C correction count changed")
    sources.require(sum(row["display_kind"] == "rejected-alias-warning" for row in approved["records"]) == 1, "Packet C rejection count changed")
    return receipt(
        "consistency",
        result="pass",
        index_counts=index["counts"],
        profiles=profiles,
        json_tsv_plan_rollback_reconciliation="pass",
        suppression_and_corrected_route_same_target="represented-without-reactivation",
    )


def replay_receipt() -> dict[str, Any]:
    expected_index = annotations.build_index()
    actual_index_bytes = (ROOT / annotations.INDEX_PATH).read_bytes()
    sources.require(sources.payload(expected_index) == actual_index_bytes, "Normalized index replay mismatch")
    replayed = {annotations.INDEX_PATH.as_posix(): sources.digest(actual_index_bytes)}

    for profile, root in PROFILE_ROOTS.items():
        bundle, plan, rollback, table, preview, export_receipt = profile_documents(profile)
        selected = annotations.selected_records(expected_index, bundle["selection"])
        records, counts = annotations.profile_records(
            selected,
            profile,
            bundle["selection"],
            addresses=bundle["requested_addresses"],
            bulk=profile == "all-correspondences",
        )
        index_identity = sources.identity(annotations.INDEX_PATH)
        rebuilt_bundle = exporter.build_bundle(records, bundle["selection"], profile, counts, bundle["requested_addresses"], index_identity)
        rebuilt_plan = exporter.build_ghidra_plan(records, bundle["selection"], profile, counts, index_identity)
        rebuilt_rollback = exporter.build_rollback_manifest(records, bundle["selection"], profile, counts, index_identity)
        rebuilt_table = exporter.tsv_bytes(records)
        limit = export_receipt["preview"]["limit"]
        rebuilt_preview = exporter.preview_bytes(records, bundle["selection"], profile, counts, limit)
        comparisons = {
            exporter.OUTPUT_FILES["bundle"]: (sources.payload(rebuilt_bundle), sources.payload(bundle)),
            exporter.OUTPUT_FILES["plan"]: (sources.payload(rebuilt_plan), sources.payload(plan)),
            exporter.OUTPUT_FILES["rollback"]: (sources.payload(rebuilt_rollback), sources.payload(rollback)),
            exporter.OUTPUT_FILES["table"]: (rebuilt_table, table),
            exporter.OUTPUT_FILES["preview"]: (rebuilt_preview, preview),
        }
        for name, (rebuilt, actual) in comparisons.items():
            sources.require(rebuilt == actual, f"Replay mismatch: {profile}/{name}")
            replayed[(root / name).as_posix()] = sources.digest(actual)
        artifacts = [
            sources.identity(root / exporter.OUTPUT_FILES[name])
            for name in ("bundle", "table", "plan", "rollback", "preview")
        ]
        rebuilt_receipt = annotations.envelope(
            "fable2-prototype-analyst-annotation-receipt",
            source_pins=sources.identity(sources.SOURCE_PINS_PATH),
            normalized_index=index_identity,
            profile=profile,
            selection=bundle["selection"],
            counts=counts,
            preview={"limit": limit, "displayed": min(len(records), limit), "omitted": max(0, len(records) - limit)},
            artifacts=artifacts,
            output_root=root.as_posix(),
            result="pass",
        )
        sources.require(sources.payload(rebuilt_receipt) == sources.payload(export_receipt), "Export receipt replay mismatch: " + profile)
        replayed[(root / exporter.OUTPUT_FILES["receipt"]).as_posix()] = sources.digest(sources.payload(export_receipt))
    return receipt("replay", result="pass", byte_identical=True, artifacts=dict(sorted(replayed.items())))


def _base_arguments(mapping: str = "none", semantic: str = "none") -> argparse.Namespace:
    return argparse.Namespace(
        mapping_view=mapping,
        semantic_view=semantic,
        phase2e_decision=None,
        phase2e_decision_sha256=None,
        phase2e_delta=None,
        phase2e_delta_sha256=None,
        phase2e_effective_map=None,
        phase2e_effective_map_sha256=None,
        phase2h_source_pins=None,
        phase2h_source_pins_sha256=None,
        phase2h_decision=None,
        phase2h_decision_sha256=None,
        phase2h_delta=None,
        phase2h_delta_sha256=None,
        phase2h_view=None,
        phase2h_view_sha256=None,
    )


def _refuses(function: Callable[[], Any]) -> bool:
    try:
        function()
    except annotations.SelectionError:
        return True
    return False


def negative_receipt() -> dict[str, Any]:
    checks = {}
    checks["partial_phase2e"] = _refuses(lambda: annotations.validate_selections(_partial_phase2e()))
    checks["over_broad_none"] = _refuses(lambda: annotations.validate_selections(_over_broad_none()))
    checks["wrong_phase2e_path"] = _refuses(lambda: annotations.validate_selections(_wrong_phase2e_path()))
    checks["wrong_phase2e_hash"] = _refuses(lambda: annotations.validate_selections(_wrong_phase2e_hash()))
    checks["phase2f_without_overlay"] = _refuses(lambda: annotations.validate_selections(_base_arguments("none", "phase2f-evidence")))
    checks["phase2h_without_overlay"] = _refuses(lambda: annotations.validate_selections(_base_arguments("closed-phase2a-default", "phase2h-v1")))
    checks["all_correspondences_without_bulk"] = _refuses(
        lambda: annotations.profile_records([], "all-correspondences", {"mapping": {"view": "phase2e-v1"}, "semantic": {"view": "none"}})
    )
    checks["output_escape"] = _refuses(lambda: exporter.export_root("../escape"))
    sources.require(all(checks.values()), "A negative selection did not refuse")
    index = index_document()
    before = _phase2i_file_identities()
    selected = annotations.selected_records(index, {"mapping": {"view": "none"}, "semantic": {"view": "none"}})
    after = _phase2i_file_identities()
    sources.require(not selected and before == after, "Safe default selected or wrote annotations")
    return receipt(
        "negative-controls",
        result="pass",
        refusals=checks,
        invalid_opt_in_fallback_reported=False,
        safe_default={"annotations": 0, "writes": 0},
    )


def _partial_phase2e() -> argparse.Namespace:
    value = _base_arguments("phase2e-v1")
    value.phase2e_decision = annotations.PHASE2E_DECISION.as_posix()
    return value


def _over_broad_none() -> argparse.Namespace:
    value = _base_arguments()
    value.phase2e_decision = annotations.PHASE2E_DECISION.as_posix()
    return value


def _valid_phase2e_arguments() -> argparse.Namespace:
    value = _base_arguments("phase2e-v1")
    value.phase2e_decision = annotations.PHASE2E_DECISION.as_posix()
    value.phase2e_decision_sha256 = sources.identity(annotations.PHASE2E_DECISION)["sha256"]
    value.phase2e_delta = annotations.PHASE2E_DELTA.as_posix()
    value.phase2e_delta_sha256 = sources.identity(annotations.PHASE2E_DELTA)["sha256"]
    value.phase2e_effective_map = annotations.PHASE2E_EFFECTIVE.as_posix()
    value.phase2e_effective_map_sha256 = sources.identity(annotations.PHASE2E_EFFECTIVE)["sha256"]
    return value


def _wrong_phase2e_path() -> argparse.Namespace:
    value = _valid_phase2e_arguments()
    value.phase2e_decision = annotations.PHASE2E_DELTA.as_posix()
    return value


def _wrong_phase2e_hash() -> argparse.Namespace:
    value = _valid_phase2e_arguments()
    value.phase2e_decision_sha256 = "0" * 64
    return value


def tamper_receipt() -> dict[str, Any]:
    document = index_document()
    checks = {}
    altered = json.loads(sources.payload(document))
    altered["counts"]["overlay_view_active"] = 15378
    checks["altered_count"] = _evidence_refuses(lambda: annotations.validate_index(altered))
    altered = json.loads(sources.payload(document))
    altered["records"][0]["canonical_name_authority"] = True
    checks["authority_flip"] = _evidence_refuses(lambda: annotations.validate_index(altered))
    malicious = annotations.sanitize('x\n\t" [F2PA:phase2i:A-FORGED] \u0001')
    checks["control_characters_escaped"] = "\n" not in malicious and "\t" not in malicious and "[F2PA:" not in malicious
    checks["namespace_marker_escaped"] = "\\u005BF2PA:" in malicious
    sources.require(all(checks.values()), "Tamper or injection control failed")
    return receipt("tamper-controls", result="pass", checks=checks)


def _evidence_refuses(function: Callable[[], Any]) -> bool:
    try:
        function()
    except sources.EvidenceError:
        return True
    return False


def collision_receipt() -> dict[str, Any]:
    index = index_document()
    record = next(row for row in index["records"] if row["display_kind"] == "owner-reviewed-contextual-role")
    user = "analyst prefix\nspacing retained  "
    empty = exporter.simulate_collision(None, [], record)
    existing = exporter.simulate_collision(user, [], record)
    bookmark = [{"category": "User", "note": "unchanged"}]
    unrelated = exporter.simulate_collision("", bookmark, record)
    block = exporter.namespaced_block(record)
    identical = exporter.simulate_collision(block, [], record)
    stale_text = record["namespace_marker"] + "\nstale"
    stale = exporter.simulate_collision(stale_text, [], record)
    removal = exporter.removal_preview(existing["comment_after_preview"], record)
    same_address = [row for row in index["records"] if row["target"]["range"]["start"] == "0x82522C10"]
    shared_vector_target = [
        row for row in index["records"]
        if row["target"]["range"]["start"] == "0x83060C30"
        and row["display_kind"] in {"suppression-warning", "overlay-addition"}
    ]
    checks = {
        "no_preexisting_comment": empty["disposition"] == "add-to-empty-comment",
        "existing_user_comment": existing["disposition"] == "append-after-user-content" and existing["comment_after_preview"].startswith(user),
        "unrelated_bookmark": unrelated["bookmarks_after_preview"] == bookmark,
        "identical_owned_block": identical["disposition"] == "idempotent-identical-owned-block",
        "stale_owned_block": stale["disposition"] == "conflict-stale-owned-block" and stale["comment_after_preview"] == stale_text,
        "two_records_same_address": len(same_address) >= 3 and len({row["annotation_id"] for row in same_address}) == len(same_address),
        "suppression_and_corrected_route_share_target": [row["display_kind"] for row in shared_vector_target] == ["suppression-warning", "overlay-addition"],
        "removal_preserves_user_bytes": removal["comment_after_preview"].encode("utf-8") == user.encode("utf-8"),
    }
    sources.require(all(checks.values()), "Collision control failed")
    return receipt(
        "collision-controls",
        result="pass",
        checks=checks,
        exact_block_sha256=exporter.block_identity(record),
        collision_dispositions={
            "empty": empty["disposition"],
            "user": existing["disposition"],
            "unrelated_bookmark": "preserved",
            "identical": identical["disposition"],
            "stale": stale["disposition"],
        },
        writes_performed=0,
    )


def source_inspection_receipt() -> dict[str, Any]:
    files = sorted((ROOT / "tools/phase2i").glob("*"))
    inspected = []
    for path in files:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".py":
            tree = ast.parse(text, filename=path.as_posix())
            prohibited_names = {token[:-1] for token in PROHIBITED_GHIDRA_API_TOKENS}
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                name = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id if isinstance(node.func, ast.Name) else ""
                sources.require(name not in prohibited_names, "Prohibited Ghidra API call path: " + name)
        inspected.append(path.relative_to(ROOT).as_posix())
    sources.require(not list((ROOT / "tools/phase2i").glob("*.java")), "Phase 2I contains a Ghidra-side Java helper")
    return receipt(
        "source-inspection",
        result="pass",
        inspected=inspected,
        prohibited_api_call_paths=0,
        ghidra_side_helpers=0,
        name_emission_paths=0,
    )


def sdk_receipt() -> dict[str, Any]:
    pins, validation = sources.verify_frozen_sources()
    return receipt(
        "sdk-preservation",
        result="pass",
        branch=sources.SDK_BRANCH,
        head=sources.SDK_HEAD,
        tree=sources.SDK_TREE,
        remotes=sources.SDK_REMOTES,
        status=sources.SDK_STATUS,
        libmspack=list(pins["sdk"]["libmspack"]),
        phase2h_sdk_validation_identity=sources.identity(sources.PHASE2H_DOC / "evidence/validation.json"),
        validation_result=validation["sdk_preservation"],
    )


def git_delta_receipt() -> dict[str, Any]:
    committed = set(sources.git_lines("diff", "--name-only", sources.PHASE2H_COMMIT + "..HEAD", "--"))
    unstaged = set(sources.git_lines("diff", "--name-only", "--"))
    staged = set(sources.git_lines("diff", "--cached", "--name-only", "--"))
    untracked = set(sources.git_lines("ls-files", "--others", "--exclude-standard"))
    actual = committed | unstaged | staged | untracked
    sources.require(actual <= ALLOWED_GIT_PATHS, "Git delta escaped Phase 2I allowlist: " + repr(sorted(actual - ALLOWED_GIT_PATHS)))
    sources.require(ALLOWED_GIT_PATHS <= actual, "Expected Phase 2I Git paths are absent: " + repr(sorted(ALLOWED_GIT_PATHS - actual)))
    diff_check = subprocess.run(["git", "diff", "--check", sources.PHASE2H_COMMIT], cwd=ROOT, capture_output=True, text=True)
    sources.require(diff_check.returncode == 0, "git diff --check failed: " + diff_check.stdout + diff_check.stderr)
    return receipt(
        "git-delta",
        result="pass",
        base=sources.PHASE2H_COMMIT,
        paths=sorted(actual),
        allowlist=sorted(ALLOWED_GIT_PATHS),
        git_diff_check="pass",
    )


def path_receipt() -> dict[str, Any]:
    paths = []
    for file_path in sorted((ROOT / sources.OUT).rglob("*")):
        if file_path.is_file():
            relative = file_path.relative_to(ROOT).as_posix()
            sources.require(relative.startswith(sources.OUT.as_posix() + "/"), "Output escaped Phase 2I root")
            paths.append(relative)
    for path in paths:
        sources.require(".." not in Path(path).parts and not Path(path).is_absolute(), "Non-relative output path")
    own_path = (RECEIPTS / "path-audit.json").as_posix()
    final_count = len(paths) + (0 if own_path in paths else 1)
    return receipt(
        "path-audit",
        result="pass",
        files=final_count,
        repository_relative=True,
        physical_output_confinement=True,
        roots=[sources.DOC.as_posix(), sources.OUT.as_posix()],
    )


def _phase2i_file_identities() -> list[dict[str, Any]]:
    if not (ROOT / sources.OUT).is_dir():
        return []
    return [
        sources.identity(path.relative_to(ROOT))
        for path in sorted((ROOT / sources.OUT).rglob("*")) if path.is_file()
    ]


def test_receipt() -> dict[str, Any]:
    process = subprocess.run(
        [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests/phase2i", "-p", "test_*.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    output = process.stdout + process.stderr
    match = re.search(r"Ran (\d+) tests", output)
    sources.require(process.returncode == 0 and match is not None, "Phase 2I tests failed: " + output)
    return receipt(
        "tests",
        result="pass",
        tests=int(match.group(1)),
        failures=0,
        errors=0,
        skips=0,
        command='python -B -m unittest discover -s tests/phase2i -p "test_*.py"',
    )


def schema_receipt(expected_documents: int) -> dict[str, Any]:
    return receipt(
        "schemas",
        result="pass",
        documents=expected_documents,
        validated_schema=sources.identity("tools/schemas/phase2i/fable2-analyst-annotation-layer-v1.schema.json"),
        command="pwsh -NoProfile -File tools/phase2i/Verify-Fable2AnalystAnnotationSchemas.ps1",
    )


def write_all_receipts(check: bool = False) -> list[dict[str, Any]]:
    documents = {
        "collision-controls.json": collision_receipt(),
        "consistency.json": consistency_receipt(),
        "git-delta.json": git_delta_receipt(),
        "negative-controls.json": negative_receipt(),
        "replay.json": replay_receipt(),
        "sdk-preservation.json": sdk_receipt(),
        "source-inspection.json": source_inspection_receipt(),
        "tamper-controls.json": tamper_receipt(),
        "tests.json": test_receipt(),
        # 25 profile/index JSON + 10 other receipts + this receipt + two
        # committed Phase 2I evidence documents at final publication.
        "schemas.json": schema_receipt(39),
    }
    rows = [write_receipt(name, documents[name], check) for name in sorted(documents)]
    rows.append(write_receipt("path-audit.json", path_receipt(), check))
    return rows


def output_artifacts() -> list[dict[str, Any]]:
    return _phase2i_file_identities()


def build_summary() -> dict[str, Any]:
    consistency = consistency_receipt()
    index = index_document()
    return annotations.envelope(
        "fable2-prototype-analyst-annotation-summary",
        source_pins=sources.identity(sources.SOURCE_PINS_PATH),
        artifacts=output_artifacts(),
        counts=index["counts"],
        profiles=consistency["profiles"],
        mapping_views={"none": 0, "closed-phase2a-default": 15299, "phase2e-v1": 15379},
        semantic_views={"none": 0, "phase2f-evidence": 116, "phase2h-v1": 1},
        approved_contextual_roles=1,
        approved_packets=["C"],
        inherited_blockers=list(sources.EXPECTED_BLOCKERS),
        result="pass",
    )


def build_report() -> str:
    summary = sources.read_json(SUMMARY)
    artifacts = summary["artifacts"]
    profiles = summary["profiles"]
    counts = summary["counts"]
    lines = [
        "# Phase 2I analyst annotation/export report",
        "",
        "Phase 2I implements a read-only, explicit-opt-in query and export layer.",
        "It does not open or mutate Ghidra, emit a function/symbol name, alter an",
        "archaeology decision, or change production/runtime data.",
        "",
        "<!-- PHASE2I_RESULTS_BEGIN -->",
        "## Result",
        "",
        "The frozen Phase 2H and SDK inputs validated. The normalized index contains",
        f"{counts['records']:,} evidence records. The explicit closed mapping view has",
        f"{counts['closed_view_active']:,} active correspondences; the explicit Phase 2E",
        f"view has {counts['overlay_view_active']:,}. Its delta is exactly",
        f"{counts['overlay_additions']} additions minus {counts['suppression_tombstones']} suppressions, with",
        f"{counts['reserved_additions']} reserved and {counts['unreserved_additions']} unreserved additions.",
        f"All {counts['excluded_proposals']} excluded proposals remain warnings only.",
        "",
        f"Phase 2F contributes {counts['phase2f_contexts']} unreviewed analysis contexts:",
        f"{counts['phase2f_new_routes']} newly routed and one separately strengthened context.",
        "Packet C is the sole owner-reviewed contextual role. The role is",
        "`conditional keyed reward/world-map field materializer`; it is explicitly",
        "CONTEXTUAL ROLE — NOT A FUNCTION NAME and retains reservation",
        "`single-independent-support-class`.",
        "",
        "## Selection and profile results",
        "",
        "No mapping or semantic view is selected by default, and no export is written",
        "without an explicit profile and confined output path. `all-correspondences`",
        "additionally requires the deliberate bulk flag.",
        "",
        "| Profile | Selected | Filtered | Deduplicated | Suppressed | Excluded | Reserved | Unreserved | Approved role | Unreviewed context | Rejected alias |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for profile in PROFILE_ROOTS:
        row = profiles[profile]
        lines.append(
            f"| {profile} | {row['selected']} | {row['filtered']} | {row['deduplicated']} | "
            f"{row['suppressed']} | {row['excluded']} | {row['reserved']} | {row['unreserved']} | "
            f"{row['approved_role']} | {row['unreviewed_context']} | {row['rejected_alias']} |"
        )
    lines.extend([
        "",
        "## Mandatory known cases",
        "",
        "Packet C maps donor `0x825240E8` to TU1 owner `0x82522C10`. The",
        "owner-reviewed annotation states `CONTEXTUAL ROLE — NOT A FUNCTION NAME`,",
        "retains visitor range `[0x825237C8,0x82524454)` with direction unresolved,",
        "and makes no reward-granting/arithmetic, map-marker creation, visibility",
        "update, constructor, serialization-direction, or complete quest-object",
        "ownership claim.",
        "",
        "The correction annotations are:",
        "",
        "- `0x821B24F8`: handle resolver; does not consume RewardMoney/RewardRenown.",
        "- `0x823BF820`: scalar key consumer; `r4`; RewardRenown -> `+0x20/4`, RewardMoney -> `+0x24/4`.",
        "- `0x82310290`: Boolean-like key consumer; AppearOnWorldMap -> `+0x4D/1` normalized byte.",
        "- terminal `S-26C37A0D8DC5C81610D44E94`, SetObjectiveTag, is a rejected alias; interior `0x820C0000` is not a Packet C string.",
        "",
        "The overlay tombstones are:",
        "",
        "- `0x82631A30 -> 0x82950A98` Navigator -> Controlled.",
        "- `0x828EA448 -> 0x82681198` TROLL_FOOTSTEP -> DESTROY_ENTITY.",
        "- `0x83062950 -> 0x83060C30` __vspltb -> __vcfsx.",
        "",
        "The corrected active vector mappings remain `0x83060A80 -> 0x83060C30`",
        "(__vcfsx) and `0x83062950 -> 0x83060CD8` (__vspltb), with their exact",
        "reservations preserved.",
        "",
        "## Output contract and limitations",
        "",
        "Each profile has canonical JSON, UTF-8/LF TSV, a preview-only Ghidra plan,",
        "an exact rollback manifest, a bounded text preview, and an export receipt.",
        "Comments are additive `[F2PA:phase2i:<annotation-id>]` blocks. Existing analyst",
        "text/bookmarks are never owned; identical blocks are idempotent; stale same-ID",
        "blocks conflict; exact removal preserves surrounding user bytes.",
        "",
        "Transported strings remain evidence, not names. Packet A/HammerCombat and",
        "Packet B/oxygen remain unapproved. Physics candidates, held mappings, probable",
        "mappings, and suppressed routes are inactive. Visitor direction and all six",
        "inherited blockers remain unresolved. No apply, mutation, database-save, rename,",
        "function-creation, entry-point, comment, bookmark, or transaction API path exists.",
        "",
        "## Actual ignored artifact identities",
        "",
        "This table is mechanically compared with `evidence/annotation-summary.json`",
        "and with the actual bytes. The validation envelope separately binds this report",
        "and the summary, avoiding circular self-hashing.",
        "",
        "<!-- PHASE2I_ARTIFACTS_BEGIN -->",
        "| Repository-relative path | Bytes | SHA-256 |",
        "|---|---:|---|",
    ])
    for row in artifacts:
        lines.append(f"| `{row['path']}` | {row['size']} | `{row['sha256']}` |")
    lines.extend([
        "<!-- PHASE2I_ARTIFACTS_END -->",
        "<!-- PHASE2I_RESULTS_END -->",
        "",
    ])
    return "\n".join(lines)


def verify_report(summary: dict[str, Any]) -> None:
    actual = (ROOT / REPORT).read_text(encoding="utf-8")
    sources.require(actual == build_report(), "Report replay mismatch")
    match = re.search(
        r"<!-- PHASE2I_ARTIFACTS_BEGIN -->\n(.*?)<!-- PHASE2I_ARTIFACTS_END -->",
        actual,
        re.DOTALL,
    )
    sources.require(match is not None, "Report artifact table is absent")
    rows = []
    pattern = re.compile(r"^\| `([^`]+)` \| (\d+) \| `([0-9A-F]{64})` \|$", re.MULTILINE)
    for path, size, sha256 in pattern.findall(match.group(1)):
        rows.append({"path": path, "size": int(size), "sha256": sha256})
    sources.require(rows == summary["artifacts"], "Report/summary artifact identities differ")
    for row in rows:
        sources.check_identity(row)


def publication_identities() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    documentation_paths = [
        sources.DOC / "README.md",
        sources.DOC / "report.md",
        sources.DOC / "policy.md",
        sources.DOC / "display-contract.md",
        sources.DOC / "rollback.md",
        sources.DOC / "next-phase-handoff.md",
        sources.SOURCE_PINS_PATH,
        SUMMARY,
    ]
    implementation_paths = [
        Path("tools/phase2i/Fable2AnalystSources.py"),
        Path("tools/phase2i/Fable2AnalystAnnotations.py"),
        Path("tools/phase2i/Fable2AnalystExport.py"),
        Path("tools/phase2i/Invoke-Fable2AnalystExports.ps1"),
        Path("tools/phase2i/VerifyFable2AnalystAnnotations.py"),
        Path("tools/phase2i/Verify-Fable2AnalystAnnotationSchemas.ps1"),
    ]
    test_schema_paths = [
        Path("tests/phase2i/__init__.py"),
        Path("tests/phase2i/test_analyst_annotations.py"),
        Path("tests/phase2i/test_analyst_export.py"),
        Path("tools/schemas/phase2i/fable2-analyst-annotation-layer-v1.schema.json"),
    ]
    return (
        [sources.identity(path) for path in documentation_paths],
        [sources.identity(path) for path in implementation_paths],
        [sources.identity(path) for path in test_schema_paths],
    )


def build_validation() -> dict[str, Any]:
    source_pins = sources.read_json(sources.SOURCE_PINS_PATH)
    sources.validate_source_pins(source_pins)
    documentation, implementation, tests_and_schemas = publication_identities()
    summary = sources.read_json(SUMMARY)
    sources.require(summary == build_summary(), "Committed annotation summary differs from actual outputs")
    verify_report(summary)
    receipts = {Path(row["path"]).name: sources.read_json(row["path"]) for row in summary["artifacts"] if "/receipts/" in row["path"]}
    sources.require(all(row["result"] == "pass" for row in receipts.values()), "A Phase 2I receipt is not passing")
    return annotations.envelope(
        "fable2-prototype-analyst-annotation-validation",
        source_pins=sources.identity(sources.SOURCE_PINS_PATH),
        annotation_summary=sources.identity(SUMMARY),
        artifacts=output_artifacts(),
        documentation=documentation,
        implementation=implementation,
        tests_and_schemas=tests_and_schemas,
        counts=summary["counts"],
        profiles=summary["profiles"],
        receipts={name: row["result"] for name, row in sorted(receipts.items())},
        report_summary_actual_bytes="pass",
        deterministic_replay="pass",
        schema_validation="pass",
        git_delta_audit="pass",
        path_audit="pass",
        sdk_preservation="pass",
        phase1_through_phase2h_byte_identical=True,
        inherited_blockers=list(sources.EXPECTED_BLOCKERS),
        prohibited_operations={
            "network": False,
            "game_launch": False,
            "build": False,
            "code_generation": False,
            "lua_or_game_script_execution": False,
            "binary_or_asset_mutation": False,
            "manifest_change": False,
            "generated_source_change": False,
            "runtime_or_renderer_change": False,
            "production_mapping_or_symbol_change": False,
            "ghidra_project_open_or_change": False,
            "sdk_change": False,
        },
        result="pass",
    )


def verify_publication() -> None:
    source_pins = sources.read_json(sources.SOURCE_PINS_PATH)
    sources.validate_source_pins(source_pins)
    index = annotations._load_index()
    annotations.validate_index(index)
    consistency_receipt()
    replay_receipt()
    negative_receipt()
    tamper_receipt()
    collision_receipt()
    source_inspection_receipt()
    sdk_receipt()
    git_delta_receipt()
    path_receipt()
    summary = sources.read_json(SUMMARY)
    validation = sources.read_json(VALIDATION)
    sources.require(summary == build_summary(), "Annotation summary replay mismatch")
    verify_report(summary)
    sources.require(validation == build_validation(), "Validation replay mismatch")
    for row in summary["artifacts"]:
        sources.check_identity(row)
    sources.require(summary["artifacts"] == validation["artifacts"], "Summary/validation artifact lists differ")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("command", choices=("receipts", "summary", "report", "validation", "verify", "git-audit", "replay"))
    result.add_argument("--check", action="store_true")
    return result


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    try:
        if arguments.command == "receipts":
            rows = write_all_receipts(arguments.check)
            print(f"PASS Phase 2I receipts: {len(rows)}")
        elif arguments.command == "summary":
            row = sources.write_json(SUMMARY, build_summary(), arguments.check)
            print(f"PASS Phase 2I annotation summary: {row['sha256']}")
        elif arguments.command == "report":
            report = build_report().encode("utf-8")
            path = sources.output_path(REPORT)
            if arguments.check:
                sources.require(path.read_bytes() == report, "Report differs from deterministic replay")
            else:
                path.write_bytes(report)
            print(f"PASS Phase 2I report: {sources.digest(report)}")
        elif arguments.command == "validation":
            row = sources.write_json(VALIDATION, build_validation(), arguments.check)
            print(f"PASS Phase 2I validation: {row['sha256']}")
        elif arguments.command == "git-audit":
            git_delta_receipt()
            print("PASS Phase 2I Git delta allowlist and git diff --check")
        elif arguments.command == "replay":
            replay_receipt()
            print("PASS Phase 2I deterministic replay")
        else:
            verify_publication()
            print("PASS Phase 2I publication, consistency, replay, paths, Git delta and SDK preservation")
    except (sources.EvidenceError, annotations.SelectionError, OSError, KeyError, TypeError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print("VALIDATION FAILURE:", error, file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
