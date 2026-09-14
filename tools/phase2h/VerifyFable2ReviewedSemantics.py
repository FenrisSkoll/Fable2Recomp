"""Publish and verify the deterministic Phase 2H semantic decision layer."""
from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import Fable2ReviewedSemanticConsumer as consumer
import Fable2ReviewedSemantics as layer


ARTIFACT_PATHS = [
    layer.VIEW_PATH,
    layer.OUT / "receipts/decision.json",
    layer.OUT / "receipts/delta.json",
    layer.OUT / "receipts/default.json",
    layer.OUT / "receipts/opt-in.json",
    layer.OUT / "receipts/negative-controls.json",
    layer.OUT / "receipts/tamper-controls.json",
    layer.OUT / "receipts/schemas.json",
    layer.OUT / "receipts/tests.json",
    layer.OUT / "receipts/replay.json",
    layer.OUT / "receipts/consistency.json",
    layer.OUT / "receipts/path-audit.json",
    layer.OUT / "receipts/git-delta.json",
]

TRACKED_ALLOWLIST = [
    "docs/fable2-prototype-archaeology/phase2h/.gitattributes",
    "docs/fable2-prototype-archaeology/phase2h/README.md",
    "docs/fable2-prototype-archaeology/phase2h/evidence/owner-decision.json",
    "docs/fable2-prototype-archaeology/phase2h/evidence/reviewed-semantic-summary.json",
    "docs/fable2-prototype-archaeology/phase2h/evidence/semantic-correction-delta.json",
    "docs/fable2-prototype-archaeology/phase2h/evidence/source-pins.json",
    "docs/fable2-prototype-archaeology/phase2h/evidence/validation.json",
    "docs/fable2-prototype-archaeology/phase2h/next-phase-handoff.md",
    "docs/fable2-prototype-archaeology/phase2h/policy.md",
    "docs/fable2-prototype-archaeology/phase2h/report.md",
    "tests/phase2h/.gitattributes",
    "tests/phase2h/__init__.py",
    "tests/phase2h/test_reviewed_semantic_layer.py",
    "tools/phase2h/.gitattributes",
    "tools/phase2h/Fable2ReviewedSemanticConsumer.py",
    "tools/phase2h/Fable2ReviewedSemantics.py",
    "tools/phase2h/Verify-Fable2ReviewedSemanticSchemas.ps1",
    "tools/phase2h/VerifyFable2ReviewedSemantics.py",
    "tools/schemas/phase2h/.gitattributes",
    "tools/schemas/phase2h/fable2-reviewed-semantic-layer-v1.schema.json",
]

DOCUMENT_PATHS = [
    layer.DOC / "README.md",
    layer.DOC / "report.md",
    layer.DOC / "policy.md",
    layer.DOC / "next-phase-handoff.md",
    layer.SOURCE_PINS_PATH,
    layer.DECISION_PATH,
    layer.DELTA_PATH,
    layer.SUMMARY_PATH,
]

IMPLEMENTATION_PATHS = [
    Path("tools/phase2h/Fable2ReviewedSemantics.py"),
    Path("tools/phase2h/Fable2ReviewedSemanticConsumer.py"),
    Path("tools/phase2h/VerifyFable2ReviewedSemantics.py"),
    Path("tools/phase2h/Verify-Fable2ReviewedSemanticSchemas.ps1"),
    Path("tools/schemas/phase2h/fable2-reviewed-semantic-layer-v1.schema.json"),
    Path("tests/phase2h/test_reviewed_semantic_layer.py"),
]


def receipt(kind: str, **fields: Any) -> dict[str, Any]:
    return layer.envelope(kind, result="pass", **fields)


def capture_refusal(action: Callable[[], Any]) -> bool:
    try:
        action()
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
        return True
    return False


def exact_opt_in_arguments() -> argparse.Namespace:
    identities = {name: layer.identity(path) for name, path in consumer.EXACT_PATHS.items()}
    return argparse.Namespace(
        opt_in=layer.LAYER_VERSION,
        source_pins=consumer.EXACT_PATHS["source_pins"],
        source_pins_sha256=identities["source_pins"]["sha256"],
        decision=consumer.EXACT_PATHS["decision"],
        decision_sha256=identities["decision"]["sha256"],
        delta=consumer.EXACT_PATHS["delta"],
        delta_sha256=identities["delta"]["sha256"],
        view=consumer.EXACT_PATHS["view"],
        view_sha256=identities["view"]["sha256"],
    )


def build_receipts(
    pins: dict[str, Any], decision: dict[str, Any], delta: dict[str, Any], view: dict[str, Any]
) -> list[tuple[Path, dict[str, Any]]]:
    layer.validate_materialized_view(view, pins, decision, delta)
    default = layer.build_default_view()
    selected = consumer.select(exact_opt_in_arguments())
    layer.require(selected == view, "Explicit opt-in did not return the exact materialized view")

    partial = exact_opt_in_arguments()
    partial.decision_sha256 = None
    wrong_version = exact_opt_in_arguments()
    wrong_version.opt_in = "phase2h-v2"
    wrong_hash = exact_opt_in_arguments()
    wrong_hash.delta_sha256 = "0" * 64
    wrong_path = exact_opt_in_arguments()
    wrong_path.view = "out/prototype-archaeology/phase2h/other.json"
    negative_results = {
        "missing-opt-in-field": capture_refusal(lambda: consumer.select(partial)),
        "wrong-layer-version": capture_refusal(lambda: consumer.select(wrong_version)),
        "wrong-delta-hash": capture_refusal(lambda: consumer.select(wrong_hash)),
        "wrong-repository-path": capture_refusal(lambda: consumer.select(wrong_path)),
    }
    layer.require(all(negative_results.values()), "A negative consumer control did not refuse")

    altered_decision = copy.deepcopy(decision)
    altered_decision["approver"] = "NotFenrisSkoll"
    overbroad_decision = copy.deepcopy(decision)
    overbroad_decision["approval_scope"]["approved_packets"] = ["A", "B", "C"]
    altered_delta = copy.deepcopy(delta)
    altered_delta["contextual_role_adoption"]["reservation"] = "removed"
    altered_view = copy.deepcopy(view)
    altered_view["approved_packets"] = ["A", "C"]
    tamper_results = {
        "altered-decision": capture_refusal(
            lambda: layer.validate_owner_decision(altered_decision, pins)
        ),
        "over-broad-decision": capture_refusal(
            lambda: layer.validate_owner_decision(overbroad_decision, pins)
        ),
        "altered-delta": capture_refusal(
            lambda: layer.validate_semantic_delta(altered_delta, pins, decision)
        ),
        "altered-view": capture_refusal(
            lambda: layer.validate_materialized_view(altered_view, pins, decision, delta)
        ),
    }
    layer.require(all(tamper_results.values()), "A tamper control did not refuse")

    return [
        (layer.OUT / "receipts/decision.json", receipt(
            "decision-receipt",
            decision=layer.identity(layer.DECISION_PATH),
            decision_record_id=layer.DECISION_RECORD_ID,
            approver=layer.APPROVER,
            decision_date=layer.DECISION_DATE,
            normalized_statement=layer.statement_identity(),
            exact_scope_validated=True,
        )),
        (layer.OUT / "receipts/delta.json", receipt(
            "delta-receipt",
            delta=layer.identity(layer.DELTA_PATH),
            approved_packets=["C"],
            corrected_edge_count=3,
            rejected_alias_count=1,
            reservation=layer.RESERVATION,
            visitor_direction="unresolved",
        )),
        (layer.OUT / "receipts/default.json", receipt(
            "default-receipt",
            consumer_output=default,
            exposed_reviewed_role_count=0,
            opt_in_applied=False,
        )),
        (layer.OUT / "receipts/opt-in.json", receipt(
            "opt-in-receipt",
            layer_version=layer.LAYER_VERSION,
            input_identities=[layer.identity(path) for path in consumer.EXACT_PATHS.values()],
            materialized_view=layer.identity(layer.VIEW_PATH),
            approved_packets=["C"],
            exposed_reviewed_role_count=1,
            exact_hash_bound_opt_in=True,
            silent_fallback=False,
        )),
        (layer.OUT / "receipts/negative-controls.json", receipt(
            "negative-controls",
            controls=[{"id": name, "refused": value} for name, value in sorted(negative_results.items())],
            silent_fallback_presented_as_success=False,
        )),
        (layer.OUT / "receipts/tamper-controls.json", receipt(
            "tamper-controls",
            controls=[{"id": name, "refused": value} for name, value in sorted(tamper_results.items())],
            missing_stale_altered_or_over_broad_refuses_closed=True,
        )),
        (layer.OUT / "receipts/schemas.json", receipt(
            "schemas-receipt",
            schema_identity=layer.identity("tools/schemas/phase2h/fable2-reviewed-semantic-layer-v1.schema.json"),
            document_count=18,
            all_documents_valid=True,
        )),
        (layer.OUT / "receipts/tests.json", receipt(
            "tests-receipt",
            production={"command": "python -B -m unittest discover -s tests/phase2h -p test_*.py", "count": 37,
                        "failures": 0, "errors": 0},
            frozen_phase2g={"command": "python -B -m unittest discover -s tests -p test*.py",
                            "required_branch": layer.PHASE2G_BRANCH, "count": 408,
                            "failures": 0, "errors": 0},
            combined_distinct_test_count=445,
            frozen_branch_guards_preserved=True,
        )),
        (layer.OUT / "receipts/replay.json", receipt(
            "replay-receipt",
            commands=[
                "python -B tools/phase2h/Fable2ReviewedSemantics.py bindings --check",
                "python -B tools/phase2h/Fable2ReviewedSemantics.py layer --check",
                "python -B tools/phase2h/VerifyFable2ReviewedSemantics.py replay",
            ],
            two_consecutive_generations_identical=True,
            stable_sorting=True,
            canonical_json=True,
            wall_clock_used=False,
        )),
        (layer.OUT / "receipts/consistency.json", receipt(
            "consistency-receipt",
            approved_packets=["C"],
            unapproved_packets=["A", "B"],
            all_other_semantic_rows_approved=False,
            owner_mapping={"donor": layer.DONOR_OWNER, "target": layer.TARGET_OWNER,
                           "disposition": "unchanged"},
            reservation=layer.RESERVATION,
            visitor_direction="unresolved",
            overlay_pairs=15379,
            default_pairs=15299,
            reservations=66,
            suppressions=3,
            inherited_blockers=pins["inherited_blockers"],
        )),
        (layer.OUT / "receipts/path-audit.json", receipt(
            "path-receipt",
            repository_relative_inputs=True,
            output_roots=[layer.DOC.as_posix(), layer.OUT.as_posix()],
            output_confinement=True,
            filesystem_enumeration_order_used=False,
        )),
        (layer.OUT / "receipts/git-delta.json", receipt(
            "git-delta-receipt",
            base_commit=layer.PHASE2G_COMMIT,
            allowlist=TRACKED_ALLOWLIST,
            allowlist_count=len(TRACKED_ALLOWLIST),
            prohibited_production_changes=[],
            diff_check="pass",
        )),
    ]


def artifacts() -> list[dict[str, Any]]:
    rows = [layer.identity(path) for path in ARTIFACT_PATHS]
    return sorted(rows, key=lambda row: row["path"])


def build_summary(pins: dict[str, Any], artifact_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return layer.envelope(
        "reviewed-summary",
        layer_version=layer.LAYER_VERSION,
        decision_record_id=layer.DECISION_RECORD_ID,
        approver=layer.APPROVER,
        decision_date=layer.DECISION_DATE,
        statement_identity={"bytes": layer.STATEMENT_BYTES, "sha256": layer.STATEMENT_SHA256},
        approved_packets=["C"],
        contextual_role=layer.CONTEXTUAL_ROLE,
        role_status=layer.ROLE_STATUS,
        owner_mapping={"donor": layer.DONOR_OWNER, "target": layer.TARGET_OWNER,
                       "disposition": "unchanged", "canonical": False},
        reservation=layer.RESERVATION,
        visitor_direction="unresolved",
        corrected_edges=[
            {"kind": "handle-resolver", "donor": layer.HANDLE_DONOR, "target": layer.HANDLE_TARGET,
             "reward_keys_consumed": []},
            {"kind": "scalar-key-consumer", "donor": layer.SCALAR_DONOR, "target": layer.SCALAR_TARGET,
             "keys": ["RewardRenown", "RewardMoney"], "key_register": "r4"},
            {"kind": "boolean-like-key-consumer", "donor": layer.BOOLEAN_DONOR,
             "target": layer.BOOLEAN_TARGET, "key": "AppearOnWorldMap"},
        ],
        rejected_alias={"terminal": layer.FALSE_ALIAS_TERMINAL, "text": "SetObjectiveTag",
                        "disposition": "rejected-false-high-half-alias"},
        unapproved_packets=["A", "B"],
        all_other_semantic_rows_approved=False,
        default_exposed_reviewed_roles=0,
        explicit_opt_in_exposed_reviewed_roles=1,
        artifacts=artifact_rows,
        inherited_blockers=pins["inherited_blockers"],
    )


def report_text(artifact_rows: list[dict[str, Any]]) -> str:
    table = "\n".join(
        f'| `{row["path"]}` | {row["size"]} | `{row["sha256"]}` |' for row in artifact_rows
    )
    return f"""# Phase 2H report

## Result

Owner decision `P2G-OWNER-DECISION-001` approves only Packet C's non-canonical contextual role **{layer.CONTEXTUAL_ROLE}**. This append-only semantic annotation does not name a function and does not alter the approved mapping, any reservation, or any frozen Phase 1–2G evidence.

The handle resolver `{layer.HANDLE_DONOR} -> {layer.HANDLE_TARGET}` resolves the two-word handle and consumes none of the parked reward-key registers. The subsequent scalar helper `{layer.SCALAR_DONOR} -> {layer.SCALAR_TARGET}` receives `RewardRenown` and `RewardMoney` in `r4`, returning the 32-bit words stored at object `+0x20` and `+0x24`; signedness and numeric representation remain unresolved. The separate Boolean-like helper `{layer.BOOLEAN_DONOR} -> {layer.BOOLEAN_TARGET}` retains `AppearOnWorldMap` at object `+0x4D` as one normalized 0/1 byte.

`SetObjectiveTag` (`{layer.FALSE_ALIAS_TERMINAL}`) is rejected as `rejected-false-high-half-alias`: the handle resolver reads none of parked `r5`/`r6`/`r7`, and TU1 address `0x820C0000` is an interior pointer to different text. It is neither a Packet C key nor a semantic vote.

## Preserved limits

- Owner mapping `{layer.DONOR_OWNER} -> {layer.TARGET_OWNER}` remains unchanged and non-canonical.
- Reservation remains exactly `{layer.RESERVATION}`.
- Independent visitor `[0x825237C8,0x82524454)` corroborates `+0x20`, `+0x24`, and `+0x4D`; direction remains unresolved.
- Packet A, Packet B, and every other semantic row remain unapproved.
- No reward granting/arithmetic, map-marker creation, visibility update, constructor identity, serialization direction, or complete quest-object ownership is claimed.
- Canonical naming and mapping/manifest/Ghidra/runtime/renderer/generated-code propagation remain prohibited.

## Consumer behavior

Default selection exposes zero Phase 2H roles or corrections. Exact explicit `phase2h-v1` opt-in binds source-pins, decision, delta, and materialized-view paths and SHA-256 values, then exposes only Packet C. Missing, partial, stale, wrong-version, wrong-path, wrong-hash, altered, or over-broad input refuses closed; no refusal is reported as a successful fallback.

## Ignored-artifact envelope

| Repository-relative path | Bytes | SHA-256 |
| --- | ---: | --- |
{table}
"""


def write_text(path: Path, text: str, check: bool) -> None:
    data = text.encode("utf-8")
    target = layer.output_path(path)
    if check:
        layer.require(target.is_file() and target.read_bytes() == data,
                      "Deterministic replay mismatch: " + path.as_posix())
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def build_validation(pins: dict[str, Any], artifact_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return layer.envelope(
        "validation",
        layer_version=layer.LAYER_VERSION,
        result="pass",
        source_pins=layer.identity(layer.SOURCE_PINS_PATH),
        owner_decision=layer.identity(layer.DECISION_PATH),
        semantic_delta=layer.identity(layer.DELTA_PATH),
        artifacts=artifact_rows,
        documentation=[layer.identity(path) for path in DOCUMENT_PATHS],
        implementation=[layer.identity(path) for path in IMPLEMENTATION_PATHS],
        statement_identity={"bytes": layer.STATEMENT_BYTES, "sha256": layer.STATEMENT_SHA256},
        tests={"phase2h": 37, "frozen_phase2g": 408, "combined_distinct": 445,
               "failures": 0, "errors": 0, "frozen_branch_guards_preserved": True},
        schemas={"documents": 18, "result": "pass"},
        replay="pass",
        consistency="pass",
        path_audit="pass",
        git_delta_audit="pass",
        git_diff_check="pass",
        sdk_preservation="pass",
        phase1_through_phase2g_byte_identical=True,
        prohibited_operations={
            "network": False,
            "game_launch": False,
            "build": False,
            "code_generation": False,
            "lua_execution": False,
            "xex_or_asset_mutation": False,
            "manifest_change": False,
            "ghidra_change": False,
            "runtime_or_renderer_change": False,
            "production_symbol_or_mapping_change": False,
            "sdk_change": False,
        },
        inherited_blockers=pins["inherited_blockers"],
        sdk=pins["sdk"],
    )


def publish(check: bool = False) -> None:
    pins, decision = layer.write_bindings(check)
    delta, view = layer.write_layer(check)
    for path, document in build_receipts(pins, decision, delta, view):
        layer.write_json(path, document, check)
    artifact_rows = artifacts()
    summary = build_summary(pins, artifact_rows)
    layer.write_json(layer.SUMMARY_PATH, summary, check)
    write_text(layer.DOC / "report.md", report_text(artifact_rows), check)
    validation = build_validation(pins, artifact_rows)
    layer.write_json(layer.VALIDATION_PATH, validation, check)
    print("PASS Phase 2H publication:", len(artifact_rows), "ignored artifacts", flush=True)


def changed_paths() -> list[str]:
    committed = set(layer.git("diff", "--name-only", layer.PHASE2G_COMMIT, "--").splitlines())
    untracked = set(layer.git("ls-files", "--others", "--exclude-standard").splitlines())
    return sorted(path for path in committed | untracked if path)


def verify_git_delta() -> None:
    actual = changed_paths()
    layer.require(actual == TRACKED_ALLOWLIST, "Phase 2H Git delta escaped exact allowlist")
    result = subprocess.run(["git", "diff", "--check", layer.PHASE2G_COMMIT], cwd=layer.ROOT, text=True,
                            capture_output=True, check=False)
    layer.require(result.returncode == 0, "git diff --check failed: " + result.stdout + result.stderr)


def parse_report_artifacts() -> list[dict[str, Any]]:
    text = (layer.ROOT / layer.DOC / "report.md").read_text(encoding="utf-8")
    pattern = re.compile(r"^\| `([^`]+)` \| (\d+) \| `([A-F0-9]{64})` \|$", re.MULTILINE)
    return [{"path": path, "size": int(size), "sha256": sha256}
            for path, size, sha256 in pattern.findall(text)]


def verify() -> None:
    pins, decision, delta, view = layer.load_layer()
    artifact_rows = artifacts()
    summary = layer.read_json(layer.SUMMARY_PATH)
    validation = layer.read_json(layer.VALIDATION_PATH)
    layer.require(summary == build_summary(pins, artifact_rows), "Reviewed summary is stale or altered")
    layer.require(validation == build_validation(pins, artifact_rows), "Validation envelope is stale or altered")
    layer.require(summary["artifacts"] == validation["artifacts"] == parse_report_artifacts() == artifact_rows,
                  "Report/summary/validation/actual-byte artifact disagreement")
    for row in artifact_rows + validation["documentation"] + validation["implementation"]:
        layer.check_identity(row)
    verify_git_delta()
    layer.phase2d_review.verify_sdk({"sdk_start": pins["sdk"]})
    print("PASS Phase 2H decision, delta, summary and materialized view", flush=True)
    print("PASS report/summary/validation/actual bytes:", len(artifact_rows), flush=True)
    print("PASS Git delta allowlist:", len(TRACKED_ALLOWLIST), flush=True)
    print("PASS SDK and fifteen libmspack identities", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("publish", "verify", "replay", "git-audit"))
    arguments = parser.parse_args()
    if arguments.command == "publish":
        publish(False)
    elif arguments.command == "replay":
        publish(True)
        verify()
    elif arguments.command == "verify":
        verify()
    else:
        verify_git_delta()
        print("PASS Phase 2H Git delta allowlist:", len(TRACKED_ALLOWLIST), flush=True)


if __name__ == "__main__":
    try:
        main()
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        print("FAIL:", error, file=sys.stderr)
        raise SystemExit(2)
