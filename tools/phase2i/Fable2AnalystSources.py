"""Frozen Phase 2I source bindings and deterministic I/O helpers.

This module is deliberately independent of the frozen Phase 2H branch guard.
It validates that branch, its complete bound source graph, and the SDK state from
the Phase 2I descendant without rewriting or rebinding any earlier phase.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
DOC = Path("docs/fable2-prototype-archaeology/phase2i")
OUT = Path("out/prototype-archaeology/phase2i")
SOURCE_PINS_PATH = DOC / "evidence/source-pins.json"

PHASE2H_BRANCH = "fable2-prototype-archaeology-phase2h"
PHASE2I_BRANCH = "fable2-prototype-archaeology-phase2i"
PHASE2H_COMMIT = "d9721cd72a98420eaa06548ee54a01c5a076fa62"
PHASE2H_TREE = "d7943ac3b62af5664d86a033ea37ed763704e370"
PHASE2H_SUBJECT = "Audit the complete Phase 2H Git delta"
PHASE2H_SEQUENCE = [
    ["3400b989801535f91dceeec3f9f3640625e30206", "Bind Phase 2H frozen sources and owner decision"],
    ["cbdf617dea8f09ac351711f6657be59c823c3a1b", "Apply Phase 2H Packet C semantic correction layer"],
    ["6e43a2a81c05d65d8b2ebd29bdda13777d1e7e68", "Verify Phase 2H semantic decision handoff"],
    ["d9721cd72a98420eaa06548ee54a01c5a076fa62", "Audit the complete Phase 2H Git delta"],
]

PHASE2H_DOC = Path("docs/fable2-prototype-archaeology/phase2h")
PHASE2H_OUT = Path("out/prototype-archaeology/phase2h")
PHASE2H_TRUST_ROOTS = {
    ".gitattributes": (42, "D3F1E52E52EBDBFBDD7B015EEC847A978C055B21CF05B5DB6E7698091AC3027B"),
    "README.md": (3299, "BB1351327AA6BF6D9B0EE43744B3108C8DB6A7DF0D3AE511B6D0A09BE8C5ED3B"),
    "report.md": (4065, "6D08D9E0CB90242E8EDE87E0A50C9E68F4653050970155A3464EC369B698BCFF"),
    "policy.md": (2724, "C6D17399B30423D010779A78B622FA97EA7151B09F784BCDBECE40D165B94919"),
    "next-phase-handoff.md": (1758, "C4F613237A8AF3E9879CA96847DB587881E08174390D28571DE87ABF41BEC4AE"),
    "evidence/owner-decision.json": (6746, "C08DD7C73BB790ED6BE7F113A32ED21EBD44FF9CA4523199B4128622C895D4D1"),
    "evidence/semantic-correction-delta.json": (6414, "0D5DCA939AF9F0A2FD7B2DDC603FCE4BBFCE6B56A8EA67BB4C9985C6CCCF4F3F"),
    "evidence/reviewed-semantic-summary.json": (4783, "4425B21BFB72D8B389D134558A3D81119A771E626F1645DAFB6D10D5B9064158"),
    "evidence/source-pins.json": (135206, "81C38C88DB1B41E70AEC2B499B0378F1B5A9A3F2F95E3B9FC7CD751FB676B810"),
    "evidence/validation.json": (9650, "FA77F01340E46864C604579689AC2834C5DF8FB8733DCB09677193B1F3A3DD5B"),
}

FABLE_REMOTES = [
    "fork\thttps://github.com/FenrisSkoll/Fable2Recomp-old-fork.git (fetch)",
    "fork\thttps://github.com/FenrisSkoll/Fable2Recomp-old-fork.git (push)",
    "origin\thttps://github.com/FenrisSkoll/Fable2Recomp.git (fetch)",
    "origin\thttps://github.com/FenrisSkoll/Fable2Recomp.git (push)",
    "upstream\thttps://github.com/Fable2Recomp/Fable2Recomp.git (fetch)",
    "upstream\thttps://github.com/Fable2Recomp/Fable2Recomp.git (push)",
]
SDK_ROOT = Path(r"C:\Dev\rexglue-sdk-v0.10")
SDK_BRANCH = "fable2-prototype-archaeology-phase1"
SDK_HEAD = "fa10315ff88ca56b2d0b380de40bad5b59b542bd"
SDK_TREE = "ec06d4e7e56beb81551c6089e9768b7588606f20"
SDK_STATUS = [
    "1 .M S.M. 160000 160000 160000 305907723a4e7ab2018e58040059ffb5e77db837 "
    "305907723a4e7ab2018e58040059ffb5e77db837 thirdparty/libmspack"
]
SDK_REMOTES = [
    "origin\thttps://github.com/FenrisSkoll/rexglue-sdk.git (fetch)",
    "origin\thttps://github.com/FenrisSkoll/rexglue-sdk.git (push)",
    "upstream\thttps://github.com/rexglue/rexglue-sdk.git (fetch)",
    "upstream\thttps://github.com/rexglue/rexglue-sdk.git (push)",
]

EXPECTED_BLOCKERS = [
    {
        "id": "L.script-bank-parser-or-blocker",
        "reason": "Bounded inventory completed; validated proprietary bank-entry layout is unavailable in the existing supported parsers.",
    },
    {
        "id": "L.game-GUI-startup-states",
        "reason": "Path categories are preserved, but a native Lua-state lifetime/namespace ownership chain is absent.",
    },
    {
        "id": "L.retail-provenance",
        "reason": "Current-runtime script inventory is not an authenticated retail-disc bank and dependency inventory.",
    },
    {
        "id": "M.complete-chain-or-blocker",
        "reason": "The native callback payload is proven, but helper/adapter, native state and corresponding TU1 registration obligations remain unresolved.",
    },
    {
        "id": "validation.baseline-bound-ownership",
        "reason": "Exact historical generated/default/fable2_recomp.136.cpp bytes with SHA-256 6053CC0EAC4636AA03AAA26581162B707C37E1B52BEE4C10F205D07C63EBDF59 are absent; only three baseline-bound provenance fields differ.",
    },
    {
        "id": "validation.all-existing-verifiers",
        "reason": "Current validators pass; exact historical ownership JSON replay remains blocked by the hash-bound generated input. The closed Phase 2B generator retains its branch guard and is not rebound.",
    },
]


class EvidenceError(ValueError):
    """A frozen input or internal evidence invariant failed validation."""


def require(condition: Any, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def payload(document: Any) -> bytes:
    return (json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def read_json(path: str | Path) -> Any:
    return json.loads((ROOT / Path(path)).read_bytes())


def repository_path(path: str | Path) -> Path:
    value = Path(path)
    require(not value.is_absolute() and ".." not in value.parts, "Path must be repository-relative")
    # Frozen input junctions are authenticated by bytes and intentionally use
    # lexical repository-relative paths. Physical confinement is an output rule.
    return ROOT / value


def output_path(path: str | Path) -> Path:
    resolved = repository_path(path).resolve()
    allowed = ((ROOT / DOC).resolve(), (ROOT / OUT).resolve())
    require(any(resolved.is_relative_to(root) for root in allowed), "Output outside Phase 2I roots")
    return resolved


def identity(path: str | Path) -> dict[str, Any]:
    value = Path(path).as_posix()
    file_path = repository_path(value)
    require(file_path.is_file(), "Missing bound input: " + value)
    data = file_path.read_bytes()
    return {"path": value, "size": len(data), "sha256": digest(data)}


def check_identity(row: dict[str, Any]) -> None:
    expected = {key: row[key] for key in ("path", "size", "sha256")}
    require(identity(row["path"]) == expected, "Bound input identity changed: " + row["path"])


def write_json(path: str | Path, document: Any, check: bool = False) -> dict[str, Any]:
    relative = Path(path).as_posix()
    target = output_path(relative)
    data = payload(document)
    if check:
        require(target.is_file() and target.read_bytes() == data, "Generated bytes changed: " + relative)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return {"path": relative, "size": len(data), "sha256": digest(data)}


def git(*arguments: str, cwd: Path = ROOT) -> str:
    return subprocess.check_output(["git", *arguments], cwd=cwd, text=True).strip()


def git_lines(*arguments: str, cwd: Path = ROOT) -> list[str]:
    value = git(*arguments, cwd=cwd)
    return value.splitlines() if value else []


def _identity_at_root(root: Path, relative: str) -> dict[str, Any]:
    path = root / Path(relative)
    require(path.is_file(), "Missing SDK input: " + relative)
    data = path.read_bytes()
    return {"path": relative, "size": len(data), "sha256": digest(data)}


def _verify_invariants(pins: dict[str, Any], validation: dict[str, Any]) -> None:
    summary = read_json(PHASE2H_DOC / "evidence/reviewed-semantic-summary.json")
    decision = read_json(PHASE2H_DOC / "evidence/owner-decision.json")
    delta = read_json(PHASE2H_DOC / "evidence/semantic-correction-delta.json")
    view = read_json(PHASE2H_OUT / "materialized-reviewed-semantic-view.json")
    phase2e = read_json("docs/fable2-prototype-archaeology/phase2e/evidence/overlay-summary.json")
    phase2f = read_json("docs/fable2-prototype-archaeology/phase2f/evidence/route-summary.json")

    require(decision["decision_record_id"] == "P2G-OWNER-DECISION-001", "Owner decision ID changed")
    require(decision["approver"] == "FenrisSkoll" and decision["decision_date"] == "2026-09-13", "Owner identity/date changed")
    require(decision["normalized_statement"]["bytes"] == 477, "Owner statement size changed")
    require(decision["normalized_statement"]["sha256"] == "BF6D59C103E1144BA04EDB0CBC654D67EDFAB8DD2A91A04AB59D1C704247C051", "Owner statement hash changed")
    require(summary["default_exposed_reviewed_roles"] == 0, "Phase 2H default role count changed")
    require(summary["explicit_opt_in_exposed_reviewed_roles"] == 1, "Phase 2H opt-in role count changed")
    require(summary["contextual_role"] == "conditional keyed reward/world-map field materializer", "Packet C role changed")
    require(summary["owner_mapping"] == {"canonical": False, "disposition": "unchanged", "donor": "0x825240E8", "target": "0x82522C10"}, "Packet C mapping changed")
    require(summary["reservation"] == "single-independent-support-class", "Packet C reservation changed")
    require(summary["visitor_direction"] == "unresolved", "Visitor direction changed")
    require(summary["unapproved_packets"] == ["A", "B"] and summary["all_other_semantic_rows_approved"] is False, "Unapproved semantic scope changed")
    require(delta["rejected_alias"]["terminal"] == "S-26C37A0D8DC5C81610D44E94", "Rejected alias changed")
    require(delta["rejected_alias"]["text"] == "SetObjectiveTag" and delta["rejected_alias"]["genuine_packet_c_key"] is False, "SetObjectiveTag disposition changed")
    require(len(view["reviewed_roles"]) == 1 and len(view["semantic_corrections"]) == 3 and len(view["rejected_aliases"]) == 1, "Phase 2H materialized population changed")
    require(summary["inherited_blockers"] == EXPECTED_BLOCKERS == validation["inherited_blockers"] == pins["inherited_blockers"], "Inherited blockers changed")

    require(phase2e["counts"]["closed_phase2a"] == 15299, "Closed Phase 2A count changed")
    require(phase2e["counts"]["effective"] == 15379, "Phase 2E effective count changed")
    require(phase2e["counts"]["semantic_transport_suppressions"] == 3, "Suppression count changed")
    require(phase2e["counts"]["mapping_additions"] == 83, "Addition count changed")
    require(phase2e["approvals"]["reserved_mapping_additions"] == 66, "Reservation count changed")
    require(phase2e["approvals"]["unreserved_mapping_additions"] == 17, "Unreserved count changed")
    require(pins["overlay_preservation"] == {
        "additions": 83,
        "default_pairs": 15299,
        "default_selection": "closed-phase2a-default",
        "held_strong_excluded": 3,
        "overlay_pairs": 15379,
        "physics_excluded": 2,
        "probable_excluded": 715,
        "reservations": 66,
        "selection": "phase2e-v1",
        "suppressions": 3,
    }, "Phase 2H overlay preservation changed")
    require(phase2f["newly_routable"] == 115 and phase2f["newly_corroborated"] == 1, "Phase 2F route counts changed")
    require(phase2f["newly_routable_and_corroborated"] == 0, "Phase 2F route separation changed")


def verify_frozen_sources() -> tuple[dict[str, Any], dict[str, Any]]:
    require(git("rev-parse", PHASE2H_BRANCH) == PHASE2H_COMMIT, "Frozen Phase 2H branch moved")
    require(git("rev-parse", PHASE2H_COMMIT + "^{tree}") == PHASE2H_TREE, "Frozen Phase 2H tree changed")
    require(git("log", "-1", "--format=%s", PHASE2H_COMMIT) == PHASE2H_SUBJECT, "Frozen Phase 2H subject changed")
    sequence = [line.split(" ", 1) for line in reversed(git_lines("log", "-4", "--format=%H %s", PHASE2H_COMMIT))]
    require(sequence == PHASE2H_SEQUENCE, "Phase 2H commit sequence changed")
    require(git("branch", "--show-current") == PHASE2I_BRANCH, "Phase 2I branch required")
    require(git("merge-base", PHASE2H_COMMIT, "HEAD") == PHASE2H_COMMIT, "Phase 2I is not descended from Phase 2H")
    require(git_lines("remote", "-v") == FABLE_REMOTES, "Fable2Recomp remotes changed")

    for name, (size, sha256) in PHASE2H_TRUST_ROOTS.items():
        check_identity({"path": (PHASE2H_DOC / name).as_posix(), "size": size, "sha256": sha256})

    pins = read_json(PHASE2H_DOC / "evidence/source-pins.json")
    validation = read_json(PHASE2H_DOC / "evidence/validation.json")
    require(pins["schema"] == {"name": "fable2-prototype-reviewed-semantic-source-pins", "version": 1}, "Phase 2H source-pins schema changed")
    require(validation["result"] == "pass", "Phase 2H validation is not passing")
    for row in pins["sources"]:
        check_identity(row)
    for row in validation["artifacts"] + validation["documentation"] + validation["implementation"]:
        check_identity(row)

    require(git("branch", "--show-current", cwd=SDK_ROOT) == SDK_BRANCH, "SDK branch changed")
    require(git("rev-parse", "HEAD", cwd=SDK_ROOT) == SDK_HEAD, "SDK HEAD changed")
    require(git("rev-parse", "HEAD^{tree}", cwd=SDK_ROOT) == SDK_TREE, "SDK tree changed")
    require(git_lines("remote", "-v", cwd=SDK_ROOT) == SDK_REMOTES, "SDK remotes changed")
    require(git_lines("status", "--porcelain=v2", cwd=SDK_ROOT) == SDK_STATUS, "SDK worktree state changed")
    require(validation["sdk"]["libmspack"] == pins["sdk"]["libmspack"], "Frozen libmspack identities disagree")
    for row in pins["sdk"]["libmspack"]:
        actual = _identity_at_root(SDK_ROOT / "thirdparty/libmspack", row["path"])
        require(actual == row, "libmspack identity changed: " + row["path"])

    _verify_invariants(pins, validation)
    return pins, validation


def _unique_sources(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    by_path: dict[str, dict[str, Any]] = {}
    for row in rows:
        identity_row = {key: row[key] for key in ("path", "size", "sha256")}
        previous = by_path.get(row["path"])
        require(previous is None or previous == identity_row, "Mixed frozen identity: " + row["path"])
        by_path[row["path"]] = identity_row
    return [by_path[path] for path in sorted(by_path)]


def build_source_pins() -> dict[str, Any]:
    pins, validation = verify_frozen_sources()
    rows: list[dict[str, Any]] = list(pins["sources"])
    rows.extend(validation["artifacts"])
    rows.extend(validation["documentation"])
    rows.extend(validation["implementation"])
    rows.extend(
        {"path": (PHASE2H_DOC / name).as_posix(), "size": size, "sha256": sha256}
        for name, (size, sha256) in PHASE2H_TRUST_ROOTS.items()
    )
    return {
        "schema": {"name": "fable2-prototype-analyst-annotation-source-pins", "version": 1},
        "phase2h_commit": PHASE2H_COMMIT,
        "analysis_only": True,
        "annotation_generation_only": True,
        "canonical_name_authority": False,
        "production_mapping_authority": False,
        "runtime_authority": False,
        "ghidra_mutation_authority": False,
        "starting_state": {
            "branch": PHASE2H_BRANCH,
            "head": PHASE2H_COMMIT,
            "tree": PHASE2H_TREE,
            "subject": PHASE2H_SUBJECT,
            "index": [],
            "worktree": [],
        },
        "phase2h_commit_sequence": [
            {"commit": commit, "subject": subject} for commit, subject in PHASE2H_SEQUENCE
        ],
        "phase2h_trust_roots": [
            {"path": (PHASE2H_DOC / name).as_posix(), "size": size, "sha256": sha256}
            for name, (size, sha256) in PHASE2H_TRUST_ROOTS.items()
        ],
        "phase2h_ignored_artifacts": list(validation["artifacts"]),
        "sources": _unique_sources(rows),
        "remotes": list(FABLE_REMOTES),
        "inherited_blockers": list(EXPECTED_BLOCKERS),
        "overlay_preservation": dict(pins["overlay_preservation"]),
        "semantic_preservation": {
            "phase2f_new_routes": 115,
            "phase2f_strengthened_contexts": 1,
            "phase2h_default_roles": 0,
            "phase2h_opt_in_roles": 1,
            "phase2h_approved_packets": ["C"],
        },
        "sdk": {
            "branch": SDK_BRANCH,
            "head": SDK_HEAD,
            "tree": SDK_TREE,
            "remotes": list(SDK_REMOTES),
            "status": list(SDK_STATUS),
            "libmspack": list(pins["sdk"]["libmspack"]),
        },
        "all_phase1_through_phase2h_byte_identical": True,
    }


def validate_source_pins(document: dict[str, Any]) -> None:
    require(document == build_source_pins(), "Phase 2I source pins differ from frozen inputs")


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare committed source pins without writing")
    arguments = parser.parse_args(argv)
    try:
        document = build_source_pins()
        result = write_json(SOURCE_PINS_PATH, document, arguments.check)
    except (EvidenceError, OSError, KeyError, TypeError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print("REFUSED:", error, file=sys.stderr)
        return 3
    print(f"PASS Phase 2I frozen bindings: {len(document['sources'])} sources; {result['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
