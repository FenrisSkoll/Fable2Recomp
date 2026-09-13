"""Phase 2H append-only owner-reviewed semantic layer (offline and deterministic)."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools")]

import Fable2PrototypeReview as phase2d_review

PHASE2G_BRANCH = "fable2-prototype-archaeology-phase2g"
PHASE2H_BRANCH = "fable2-prototype-archaeology-phase2h"
PHASE2G_COMMIT = "e89317f75c43bdce8b7108bb291c2b52dddb6182"
PHASE2G_TREE = "0d7caf8fc30d24989d85d0b64423a24232881178"
PHASE2G_SUBJECT = "Deduplicate Phase 2G semantic evidence ledger"
PHASE2G_SEQUENCE = [
    ["055ec0db6c1f4a6b4666f78269e6f9cc7d30368b", "Bind Phase 2G frozen sources and independence policy"],
    ["3dea7f201ee1c2f188bf8c4f68b297a961f2eeb4", "Prove Phase 2G HammerCombat exclusion and byte-state role"],
    ["4891a365dfeb7e1b10e7a86e96b7628145c8c0cb", "Resolve Phase 2G property field roles and shared machinery"],
    ["9c3cfa60ccf264649e987c1dcef87c507a35f08d", "Verify Phase 2G semantic proofs and preservation handoff"],
    ["e89317f75c43bdce8b7108bb291c2b52dddb6182", "Deduplicate Phase 2G semantic evidence ledger"],
]

DOC = Path("docs/fable2-prototype-archaeology/phase2h")
OUT = Path("out/prototype-archaeology/phase2h")
PHASE2G_DOC = Path("docs/fable2-prototype-archaeology/phase2g")
PHASE2G_OUT = Path("out/prototype-archaeology/phase2g")

SOURCE_PINS_PATH = DOC / "evidence/source-pins.json"
DECISION_PATH = DOC / "evidence/owner-decision.json"
DELTA_PATH = DOC / "evidence/semantic-correction-delta.json"
SUMMARY_PATH = DOC / "evidence/reviewed-semantic-summary.json"
VALIDATION_PATH = DOC / "evidence/validation.json"
VIEW_PATH = OUT / "materialized-reviewed-semantic-view.json"

STATEMENT = (
    "Approved as FenrisSkoll: adopt the non-canonical contextual role “conditional keyed "
    "reward/world-map field materializer” for Packet C. Correct the semantic attribution so "
    "RewardMoney and RewardRenown are consumed by the subsequent scalar helper, not the handle "
    "resolver, and reject SetObjectiveTag as a false alias. Preserve the approved owner mapping, "
    "the single-independent-support-class reservation, unresolved visitor direction, and the "
    "prohibition on canonical naming."
)
STATEMENT_BYTES = 477
STATEMENT_SHA256 = "BF6D59C103E1144BA04EDB0CBC654D67EDFAB8DD2A91A04AB59D1C704247C051"
DECISION_RECORD_ID = "P2G-OWNER-DECISION-001"
APPROVER = "FenrisSkoll"
DECISION_DATE = "2026-09-13"
DECISION_SOURCE = "owner-supplied-chat-statement"
LAYER_VERSION = "phase2h-v1"

PACKET = "C"
TERMINAL = "S-202449BD00F31D43FE6EBBA4"
FALSE_ALIAS_TERMINAL = "S-26C37A0D8DC5C81610D44E94"
CONTEXTUAL_ROLE = "conditional keyed reward/world-map field materializer"
ROLE_STATUS = "owner-reviewed non-canonical contextual role"
RESERVATION = "single-independent-support-class"
DONOR_OWNER = "0x825240E8"
TARGET_OWNER = "0x82522C10"
HANDLE_DONOR = "0x821B2528"
HANDLE_TARGET = "0x821B24F8"
SCALAR_DONOR = "0x823C0588"
SCALAR_TARGET = "0x823BF820"
BOOLEAN_DONOR = "0x82310448"
BOOLEAN_TARGET = "0x82310290"

PHASE2G_TRUST_ROOTS = {
    ".gitattributes": (42, "D3F1E52E52EBDBFBDD7B015EEC847A978C055B21CF05B5DB6E7698091AC3027B"),
    "README.md": (2836, "CE36D858D82495203244B6EE827BDBA2D4DA9AEC38A643E1922F3920913A59C3"),
    "report.md": (12254, "C56249B2D1B407E03D270086138D2B450C8558281F4794B8972B58CDC14AE123"),
    "policy.md": (4310, "318EE4FA6E9A1901525BD8973C03FF8017F991982111EEAE3CC4C3E3365ECEB1"),
    "review-guide.md": (1984, "7C0B59455D6A28B96EA41CF9503698CDC2FDC34B76931797EA21D7D2A2A31B6A"),
    "next-phase-handoff.md": (1789, "9FC2FF949F59F5B71D61F611C1E2F1D9919BCD1503D5D241A16284E802EEF026"),
    "evidence/source-pins.json": (122108, "C5A5FFB7D84EC47D27D019DBBB54B9C55D206727C0650F29CA059CB358985B35"),
    "evidence/packet-summary.json": (6162, "CFAC8A7757D2B6A687995D4AE2BC69E9ECDD5BEA82551A52F99B4A3C43623F59"),
    "evidence/validation.json": (11707, "1CAEF4571E7785DF0DD0901995CEC335BD8065F4DA3DF5DD800D43C22F14D002"),
}

PHASE2G_STARTING_STATE = {
    "branch": PHASE2G_BRANCH,
    "head": PHASE2G_COMMIT,
    "tree": PHASE2G_TREE,
    "index": [],
    "worktree": [],
    "subject": PHASE2G_SUBJECT,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def payload(document: Any) -> bytes:
    return (json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def read_json(path: str | Path) -> Any:
    return json.loads((ROOT / Path(path)).read_bytes())


def repository_path(path: str | Path) -> Path:
    value = Path(path)
    require(not value.is_absolute() and not value.anchor and ".." not in value.parts and ":" not in str(value),
            "Repository-relative path required")
    return ROOT / value


def output_path(path: str | Path) -> Path:
    resolved = repository_path(path)
    roots = ((ROOT / DOC).resolve(), (ROOT / OUT).resolve())
    require(any(resolved.is_relative_to(root) for root in roots), "Write escaped Phase 2H roots")
    return resolved


def identity(path: str | Path) -> dict[str, Any]:
    value = Path(path).as_posix()
    file_path = repository_path(value)
    with file_path.open("rb") as stream:
        sha256 = hashlib.file_digest(stream, "sha256").hexdigest().upper()
    return {"path": value, "size": file_path.stat().st_size, "sha256": sha256}


def check_identity(row: dict[str, Any]) -> None:
    expected = {key: row[key] for key in ("path", "size", "sha256")}
    require(identity(row["path"]) == expected, "Input identity changed: " + row["path"])


def write_json(path: str | Path, document: Any, check: bool = False) -> dict[str, Any]:
    data = payload(document)
    target = output_path(path)
    if check:
        require(target.is_file() and target.read_bytes() == data,
                "Deterministic replay mismatch: " + Path(path).as_posix())
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return {"path": Path(path).as_posix(), "size": len(data), "sha256": digest(data)}


def git(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def envelope(kind: str, **fields: Any) -> dict[str, Any]:
    return {
        "schema": {"name": "fable2-prototype-reviewed-semantic-" + kind, "version": 1},
        "phase2g_commit": PHASE2G_COMMIT,
        "analysis_only": True,
        "semantic_annotation_only": True,
        "canonical_adoption": False,
        "canonical_names_authorized": False,
        "mapping_mutation_allowed": False,
        "semantic_feedback_allowed": False,
        **fields,
    }


def statement_identity() -> dict[str, Any]:
    raw = STATEMENT.encode("utf-8")
    require(len(raw) == STATEMENT_BYTES, "Owner statement byte count mismatch")
    require(digest(raw) == STATEMENT_SHA256, "Owner statement SHA-256 mismatch")
    require(not raw.startswith(b"\xef\xbb\xbf") and not raw.endswith((b"\n", b"\r")),
            "Owner statement normalization mismatch")
    return {
        "encoding": "UTF-8",
        "text": STATEMENT,
        "bytes": STATEMENT_BYTES,
        "sha256": STATEMENT_SHA256,
        "terminal_newline": False,
    }


def exact_start(state: dict[str, Any]) -> None:
    require(state == PHASE2G_STARTING_STATE, "Phase 2G starting state mismatch")


def exact_sequence(sequence: list[list[str]]) -> None:
    require(sequence == PHASE2G_SEQUENCE, "Phase 2G commit sequence mismatch")


def verify_frozen_phase2g() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    require(git("rev-parse", PHASE2G_BRANCH) == PHASE2G_COMMIT, "Frozen Phase 2G branch moved")
    require(git("rev-parse", PHASE2G_COMMIT + "^{tree}") == PHASE2G_TREE, "Frozen Phase 2G tree changed")
    require(git("log", "-1", "--format=%s", PHASE2G_COMMIT) == PHASE2G_SUBJECT,
            "Frozen Phase 2G subject changed")
    actual_sequence = [line.split(" ", 1) for line in
                       reversed(git("log", "-5", "--format=%H %s", PHASE2G_COMMIT).splitlines())]
    exact_sequence(actual_sequence)
    require(git("branch", "--show-current") == PHASE2H_BRANCH, "Phase 2H branch required")
    require(git("merge-base", PHASE2G_COMMIT, "HEAD") == PHASE2G_COMMIT,
            "Phase 2H does not descend from exact Phase 2G")

    for name, (size, sha256) in PHASE2G_TRUST_ROOTS.items():
        check_identity({"path": (PHASE2G_DOC / name).as_posix(), "size": size, "sha256": sha256})

    pins = read_json(PHASE2G_DOC / "evidence/source-pins.json")
    summary = read_json(PHASE2G_DOC / "evidence/packet-summary.json")
    validation = read_json(PHASE2G_DOC / "evidence/validation.json")
    require(len(pins["sources"]) == 468, "Phase 2G frozen source population changed")
    for row in pins["sources"]:
        check_identity(row)
    require(len(validation["artifacts"]) == 13, "Phase 2G ignored artifact population changed")
    for row in validation["artifacts"] + validation["documentation"] + validation["implementation"]:
        check_identity(row)
    require(summary["artifacts"] == validation["artifacts"], "Phase 2G summary/validation disagreement")

    ledger = read_json(PHASE2G_OUT / "consumed-evidence/independence-ledger.json")
    expected_counts = {
        "mapping-consumed": 6,
        "correlated-with-mapping": 5,
        "independent-target-native": 3,
        "independent-cross-build-behavior": 0,
        "context-only": 1,
        "contradictory": 2,
        "unresolved": 4,
    }
    require(ledger["counts"] == expected_counts and len(ledger["records"]) == 21,
            "Phase 2G independence ledger changed")
    eligible = sorted(row["id"] for row in ledger["records"] if row["proof_eligible"])
    require(eligible == ["A-tu1-byte-consumer-family", "C-second-tu1-field-visitors"],
            "Phase 2G positive-vote population changed")

    packet_records = {row["packet"]: row for row in summary["records"]}
    require(packet_records["A"]["primary"] == "independently-corroborated-role" and
            packet_records["A"]["mapping"] == "unchanged" and
            packet_records["A"]["reservation"] == "retained", "Packet A changed")
    require(packet_records["B"]["primary"] == "behaviorally-corresponding-role-reserved" and
            packet_records["B"]["mapping"] == "unchanged" and
            packet_records["B"]["reservation"] == "retained", "Packet B changed")
    require(packet_records["C"]["primary"] == "independently-corroborated-role" and
            packet_records["C"]["mapping"] == "review-triggered" and
            packet_records["C"]["reservation"] == "retained", "Packet C changed")

    phase2f_validation = read_json("docs/fable2-prototype-archaeology/phase2f/evidence/validation.json")
    require(validation["overlay_selection"]["mapping_count"] == 15379 and
            validation["overlay_selection"]["overlay_enabled"] is True and
            validation["overlay_selection"]["fallback_permitted"] is False and
            phase2f_validation["default_consumer"]["mapping_count"] == 15299 and
            phase2f_validation["default_consumer"]["overlay_enabled"] is False,
            "Mapping consumer counts or isolation changed")
    consistency = read_json(PHASE2G_OUT / "receipts/consistency.json")
    require((consistency["additions"], consistency["reservations"], consistency["suppressions"]) ==
            (83, 66, 3), "Mapping preservation counts changed")
    require((consistency["physics_excluded"], consistency["held_strong_excluded"],
             consistency["probable_excluded"]) == (2, 3, 715), "Mapping exclusions changed")
    for document in (pins, summary, validation, ledger):
        require(document["canonical_adoption"] is False and
                document["canonical_names_authorized"] is False and
                document["mapping_mutation_allowed"] is False and
                document["semantic_feedback_allowed"] is False,
                "Frozen propagation flag changed")
    require(len(pins["inherited_blockers"]) == 6 and
            pins["inherited_blockers"] == summary["inherited_blockers"] == validation["inherited_blockers"],
            "Inherited blockers changed")
    require(git("remote", "-v").splitlines() == pins["remotes"], "Fable remotes changed")
    require(validation["sdk"] == pins["sdk"], "Phase 2G SDK envelope changed")
    phase2d_review.verify_sdk({"sdk_start": pins["sdk"]})
    statement_identity()
    return pins, summary, validation


def build_source_pins() -> dict[str, Any]:
    pins, summary, validation = verify_frozen_phase2g()
    rows: dict[str, dict[str, Any]] = {}

    def add(row: dict[str, Any], provenance: str) -> None:
        check_identity(row)
        name = row["path"]
        existing = rows.get(name)
        if existing is None:
            existing = {key: row[key] for key in ("path", "size", "sha256")}
            existing["provenance_generations"] = []
            existing["source_schema"] = row.get("source_schema")
            rows[name] = existing
        require(existing["size"] == row["size"] and existing["sha256"] == row["sha256"],
                "Mixed frozen identity: " + name)
        existing["provenance_generations"].append(provenance)

    for row in pins["sources"]:
        add(row, "phase2g-inherited-source-pins")
    for row in validation["artifacts"]:
        add(row, "phase2g-ignored-artifact")
    for row in validation["documentation"]:
        add(row, "phase2g-documentation")
    for row in validation["implementation"]:
        add(row, "phase2g-implementation")
    add(identity(PHASE2G_DOC / "evidence/validation.json"), "phase2g-validation-root")
    for row in rows.values():
        row["provenance_generations"] = sorted(set(row["provenance_generations"]))

    exact_start(PHASE2G_STARTING_STATE)
    exact_sequence(PHASE2G_SEQUENCE)
    return envelope(
        "source-pins",
        sources=sorted(rows.values(), key=lambda row: row["path"]),
        starting_state=PHASE2G_STARTING_STATE,
        phase2g_commit_sequence=[{"commit": commit, "subject": subject}
                                 for commit, subject in PHASE2G_SEQUENCE],
        phase2g_trust_roots=[{"path": (PHASE2G_DOC / name).as_posix(), "size": size, "sha256": sha256}
                             for name, (size, sha256) in PHASE2G_TRUST_ROOTS.items()],
        phase2g_ignored_artifacts=13,
        all_phase1_through_phase2g_byte_identical=True,
        remotes=pins["remotes"],
        sdk=pins["sdk"],
        overlay_preservation={
            "selection": "phase2e-v1",
            "overlay_pairs": 15379,
            "default_selection": "closed-phase2a-default",
            "default_pairs": 15299,
            "additions": 83,
            "reservations": 66,
            "suppressions": 3,
            "physics_excluded": 2,
            "held_strong_excluded": 3,
            "probable_excluded": 715,
        },
        packet_preservation={
            "A": {"mapping": "unchanged", "owner_approved": False, "reservation": "retained"},
            "B": {"mapping": "unchanged", "owner_approved": False, "reservation": "retained"},
            "C": {"mapping": "unchanged", "reservation": RESERVATION,
                  "visitor_direction": "unresolved"},
        },
        inherited_blockers=summary["inherited_blockers"],
    )


class Inputs:
    def __init__(self, pins: dict[str, Any]):
        self.rows = {row["path"]: row for row in pins["sources"]}
        self.used: set[str] = set()

    def ref(self, path: str, pointer: str | None = None) -> dict[str, Any]:
        name = Path(path).as_posix()
        require(name in self.rows, "Unbound source: " + name)
        check_identity(self.rows[name])
        result = {key: self.rows[name][key] for key in ("path", "size", "sha256")}
        self.used.add(name)
        if pointer is not None:
            require(pointer == "" or pointer.startswith("/"), "Invalid JSON pointer")
            node = read_json(name)
            for raw_token in pointer.split("/")[1:]:
                token = raw_token.replace("~1", "/").replace("~0", "~")
                if isinstance(node, list):
                    require(token.isdecimal() and int(token) < len(node), "Unresolved JSON pointer: " + pointer)
                    node = node[int(token)]
                else:
                    require(isinstance(node, dict) and token in node, "Unresolved JSON pointer: " + pointer)
                    node = node[token]
            result["json_pointer"] = pointer
            result["record_sha256"] = digest(payload(node))
        return result

    def identities(self) -> list[dict[str, Any]]:
        return [{key: self.rows[name][key] for key in ("path", "size", "sha256")}
                for name in sorted(self.used)]


def validate_source_pins(pins: dict[str, Any]) -> None:
    require(pins == build_source_pins(), "Missing, stale, altered or over-broad Phase 2H source pins")


def build_owner_decision(pins: dict[str, Any]) -> dict[str, Any]:
    inputs = Inputs(pins)
    provenance = [
        inputs.ref("docs/fable2-prototype-archaeology/phase2g/evidence/packet-summary.json", "/records/2"),
        inputs.ref("out/prototype-archaeology/phase2g/review-selection.json", "/records/2"),
        inputs.ref("out/prototype-archaeology/phase2g/world-map-reward/native-proof-packet.json", "/dispositions"),
        inputs.ref("out/prototype-archaeology/phase2g/world-map-reward/native-proof-packet.json", "/role_classification"),
        inputs.ref("out/prototype-archaeology/phase2g/consumed-evidence/independence-ledger.json", "/records/17"),
        inputs.ref("out/prototype-archaeology/phase2g/consumed-evidence/independence-ledger.json", "/records/18"),
        inputs.ref("out/prototype-archaeology/phase2g/consumed-evidence/independence-ledger.json", "/records/19"),
        inputs.ref("out/prototype-archaeology/phase2f/mapping-context-packets.json", "/records/6"),
        inputs.ref("out/prototype-archaeology/phase2f/target-corroboration.json", "/records/12"),
        inputs.ref("docs/fable2-prototype-archaeology/phase2f/evidence/high-value-review.json", "/selected/2"),
        inputs.ref("docs/fable2-prototype-archaeology/phase2f/evidence/route-summary.json"),
    ]
    return envelope(
        "owner-decision",
        decision_record_id=DECISION_RECORD_ID,
        approver=APPROVER,
        decision_date=DECISION_DATE,
        source=DECISION_SOURCE,
        normalized_statement=statement_identity(),
        approval_scope={
            "approved_packets": [PACKET],
            "packet": PACKET,
            "terminal": TERMINAL,
            "owner_mapping": {
                "donor": DONOR_OWNER,
                "target": TARGET_OWNER,
                "disposition": "unchanged",
                "canonical": False,
            },
            "contextual_role": {
                "text": CONTEXTUAL_ROLE,
                "status": ROLE_STATUS,
                "function_name": False,
            },
            "approved_actions": [
                "adopt-contextual-role",
                "correct-reward-key-consumer-attribution",
                "reject-false-high-half-alias",
                "preserve-limitations",
            ],
            "reservation": RESERVATION,
            "visitor_direction": "unresolved",
            "canonical_name": "prohibited",
        },
        explicitly_not_approved=[
            "canonical name for Packet C",
            "mapping change or reservation removal",
            "Packet A or Packet B contextual label",
            "any other Phase 2F high-value review row",
            "any held, probable or physics mapping",
            "any manifest, Ghidra, runtime, renderer or generated-code change",
            "bulk semantic-label adoption",
            "free-camera, Lua, script-bank or E3/demo integration",
        ],
        unapproved_packets=["A", "B"],
        all_other_semantic_rows_approved=False,
        source_pins=identity(SOURCE_PINS_PATH),
        provenance=provenance,
        input_identities=inputs.identities(),
    )


def validate_owner_decision(document: dict[str, Any], pins: dict[str, Any]) -> None:
    require(document == build_owner_decision(pins),
            "Missing, stale, altered, incorrectly hashed or over-broad owner decision")


def write_bindings(check: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    pins = build_source_pins()
    write_json(SOURCE_PINS_PATH, pins, check)
    decision = build_owner_decision(pins)
    write_json(DECISION_PATH, decision, check)
    print("PASS Phase 2H frozen bindings:", len(pins["sources"]), flush=True)
    print("PASS owner statement:", STATEMENT_BYTES, STATEMENT_SHA256, flush=True)
    return pins, decision


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("bindings",))
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    if arguments.command == "bindings":
        write_bindings(arguments.check)
