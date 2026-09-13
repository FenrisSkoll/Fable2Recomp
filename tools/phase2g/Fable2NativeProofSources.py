"""Phase 2G immutable inputs and output confinement (offline)."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "tools/phase2e")]

import Fable2PrototypeOverlay as overlay
import Fable2PrototypeReview as review

BASE = "d348952f780d47b47368792a1b6587a2f574ddfe"
TREE = "b002fd60ae678597faf5fde8b9f39908d376e51f"
BRANCH = "fable2-prototype-archaeology-phase2g"
PARENT_BRANCH = "fable2-prototype-archaeology-phase2f"
PARENT_SUBJECT = "Document Phase 2F deterministic route audit and handoff"
DOC = Path("docs/fable2-prototype-archaeology/phase2g")
OUT = Path("out/prototype-archaeology/phase2g")
PHASE2F_DOC = Path("docs/fable2-prototype-archaeology/phase2f")
PHASE2F_OUT = Path("out/prototype-archaeology/phase2f")

TRUST = {
    "README.md": (3797, "EB06043E011082D0FA95404D070EE65D149C2C1C19CDB3E0E40D962557121337"),
    "report.md": (18266, "E72ED6B17A3AEE1FCCBC9C4751DEF5710D4434D7B4629823FAF485FC5F6D9DB3"),
    "policy.md": (7707, "20ADCE626191F2FE351FE811DC944A1E035C8099BEF11A389CAD23EF0DD34330"),
    "review-guide.md": (3237, "F718D6EB7C4AEB7759CBB675AEDFAD195344585842D418FB3ADB0378E233E681"),
    "preservation-findings.md": (4996, "65C7E0FC02EEA13AADE1B29F8A3BFE6238FDB150846B2E1EF4814DEC201F22F1"),
    "next-phase-handoff.md": (2854, "9EC87516856FC531ED2F71F5C5C4A17C968D1B37B7E1F024E4966FA3A1CF9B02"),
    "evidence/source-pins.json": (107810, "EAFEFFB9EF4221537C37D4875C2A64C003F3148FC68CB6052CDA871BFC62752C"),
    "evidence/route-summary.json": (19920, "ABE80AC3FE87B56577E3CE9DF3D238521D6F1A67A4AB10FF5E93509185B1DBE6"),
    "evidence/high-value-review.json": (59323, "EA661BC999EFDD4450949D812B955541D9C8325F6431EEB124E297080046B718"),
    "evidence/validation.json": (15222, "856E1776EE12715DE5A87FBDD5A6DA94C20187421596EE524ADC355574F2AE71"),
}

START_STATE = {
    "branch": PARENT_BRANCH,
    "head": BASE,
    "tree": TREE,
    "index": [],
    "worktree": [],
    "subject": PARENT_SUBJECT,
}

require = overlay.require
payload = overlay.payload
digest = overlay.sha256


def read(path):
    return json.loads((ROOT / path).read_bytes())


def relative(path):
    value = Path(path)
    require(not value.anchor and ".." not in value.parts and ":" not in str(value),
            "Repository-relative path required")
    return ROOT / value


def output(path):
    resolved = relative(path).resolve()
    roots = ((ROOT / DOC).resolve(), (ROOT / OUT).resolve())
    require(any(resolved.is_relative_to(root) for root in roots),
            "Output outside Phase 2G roots")
    return resolved


def identity(path):
    file_path = relative(path)
    with file_path.open("rb") as stream:
        sha256 = hashlib.file_digest(stream, "sha256").hexdigest().upper()
    return {"path": Path(path).as_posix(), "size": file_path.stat().st_size, "sha256": sha256}


def check(row):
    expected = {key: row[key] for key in ("path", "size", "sha256")}
    require(identity(row["path"]) == expected, "Input identity changed: " + row["path"])


def write(path, document, replay=False):
    target = output(path)
    data = document if isinstance(document, bytes) else payload(document)
    if replay:
        require(target.is_file() and target.read_bytes() == data,
                "Deterministic replay mismatch: " + Path(path).as_posix())
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return {"path": Path(path).as_posix(), "size": len(data), "sha256": digest(data)}


def git(*args, cwd=ROOT):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def exact_start(state):
    require(state == START_STATE, "Phase 2F starting state mismatch")


def verify_overlay(selection, validation):
    require(selection["selection"] == "phase2e-v1", "Wrong overlay selection")
    require(selection["mapping_count"] == 15379, "Wrong overlay mapping count")
    require(selection["overlay_enabled"] is True, "Overlay not enabled")
    require(selection["fallback_permitted"] is False, "Overlay fallback enabled")
    require(selection["canonical_adoption"] is False, "Canonical adoption enabled")
    default = validation["default_consumer"]
    require((default["selection"], default["mapping_count"], default["overlay_enabled"]) ==
            ("closed-phase2a-default", 15299, False), "Default consumer changed")


def verify_phase2f():
    require(git("rev-parse", PARENT_BRANCH) == BASE, "Frozen Phase 2F branch moved")
    require(git("rev-parse", BASE + "^{tree}") == TREE, "Frozen Phase 2F tree changed")
    require(git("log", "-1", "--format=%s", BASE) == PARENT_SUBJECT,
            "Frozen Phase 2F subject changed")
    require(git("branch", "--show-current") == BRANCH, "Phase 2G branch required")
    require(git("merge-base", BASE, "HEAD") == BASE, "Phase 2G does not descend from exact Phase 2F")

    for name, (size, sha256) in TRUST.items():
        check({"path": (PHASE2F_DOC / name).as_posix(), "size": size, "sha256": sha256})

    pins = read(PHASE2F_DOC / "evidence/source-pins.json")
    summary = read(PHASE2F_DOC / "evidence/route-summary.json")
    validation = read(PHASE2F_DOC / "evidence/validation.json")
    require(summary["artifacts"] == validation["artifacts"],
            "Phase 2F summary/validation artifact disagreement")
    ignored = [row for row in validation["artifacts"]
               if row["path"].startswith(PHASE2F_OUT.as_posix() + "/")]
    require(len(ignored) == 32, "Phase 2F ignored artifact count changed")
    for row in validation["artifacts"] + validation["documentation"] + validation["implementation"]:
        check(row)

    verify_overlay(summary["overlay_selection"], validation)
    require(summary["canonical_adoption"] is False and summary["semantic_feedback_allowed"] is False,
            "Phase 2F propagation flags changed")
    require(summary["newly_routable"] == 115 and summary["newly_corroborated"] == 1 and
            summary["newly_routable_and_corroborated"] == 0,
            "Phase 2F route totals changed")
    require(summary["mapping_contribution"] == {"dormant": 0, "mappings": 83, "productive": 83},
            "Phase 2F mapping contribution changed")
    require(summary["lanes"]["S"]["mapping_count"] == 15296 and
            summary["lanes"]["O"]["mapping_count"] == 15379,
            "Phase 2F lane mapping counts changed")
    require(all(row["terminals"] == 51657 for row in summary["lanes"].values()),
            "Phase 2F semantic terminal reconciliation changed")
    require(summary["suppression"] == {"remaining_suppression_blocked": 2,
            "removed_historical_associations": 3, "safely_rerouted": 1},
            "Phase 2F suppressions changed")
    require(len(summary["inherited_blockers"]) == 6 and
            summary["inherited_blockers"] == validation["inherited_blockers"],
            "Phase 2F inherited blockers changed")
    require(validation["sdk"] == pins["sdk"], "Phase 2F SDK binding changed")
    review.verify_sdk({"sdk_start": pins["sdk"]})
    require(git("remote", "-v").splitlines() == pins["remotes"], "Fable remotes changed")
    return pins, summary, validation


def envelope(kind, selection, **fields):
    result = {
        "schema": {"name": "fable2-prototype-native-semantic-proof-" + kind, "version": 1},
        "phase2f_commit": BASE,
        "overlay_selection": selection,
        "canonical_adoption": False,
        "analysis_only": True,
        "semantic_feedback_allowed": False,
        "mapping_mutation_allowed": False,
        "canonical_names_authorized": False,
        **fields,
    }
    if kind != "source-pins":
        result["source_pins"] = identity(DOC / "evidence/source-pins.json")
    return result


def source_bindings():
    """Rehash the complete frozen Phase 2F envelope; never bless changed bytes."""
    pins, summary, validation = verify_phase2f()
    rows = {}

    def add(row, provenance):
        check(row)
        path = row["path"]
        if path not in rows:
            rows[path] = {key: row[key] for key in ("path", "size", "sha256")}
            rows[path]["provenance_generations"] = []
        require(rows[path]["size"] == row["size"] and rows[path]["sha256"] == row["sha256"],
                "Mixed source identities: " + path)
        rows[path]["provenance_generations"].append(provenance)

    for row in pins["sources"]:
        add(row, "phase2f-source-pins")
    for row in validation["artifacts"]:
        add(row, "phase2f-validation-artifact")
    for row in validation["documentation"] + validation["implementation"]:
        add(row, "phase2f-validation-surface")
    for name, (size, sha256) in TRUST.items():
        add({"path": (PHASE2F_DOC / name).as_posix(), "size": size, "sha256": sha256},
            "phase2f-trust-root")

    for row in rows.values():
        row["provenance_generations"] = sorted(set(row["provenance_generations"]))
        row["source_schema"] = read(row["path"]).get("schema") if row["path"].endswith(".json") else None

    exact_start(START_STATE)
    document = envelope(
        "source-pins",
        summary["overlay_selection"],
        sources=sorted(rows.values(), key=lambda row: row["path"]),
        starting_state=START_STATE,
        remotes=pins["remotes"],
        sdk=pins["sdk"],
        inherited_blockers=summary["inherited_blockers"],
        phase2f_artifact_counts={"validation_entries": len(validation["artifacts"]),
                                 "ignored_artifacts": 32},
        phase2f_verification=summary["verification"],
    )
    return document


class Inputs:
    def __init__(self, pins):
        self.pins = {row["path"]: row for row in pins["sources"]}
        self.used = set()

    def read(self, path):
        name = Path(path).as_posix()
        require(name in self.pins, "Unbound analytical input: " + name)
        check(self.pins[name])
        self.used.add(name)
        return read(name)

    def ref(self, path, pointer=None, record_sha256=None):
        name = Path(path).as_posix()
        require(name in self.pins, "Unbound evidence reference: " + name)
        document = self.read(name)
        result = {key: self.pins[name][key] for key in ("path", "size", "sha256")}
        if pointer is not None:
            node = document
            require(pointer == "" or pointer.startswith("/"),
                    "Invalid JSON pointer: " + pointer)
            for raw_token in pointer.split("/")[1:]:
                token = raw_token.replace("~1", "/").replace("~0", "~")
                if isinstance(node, list):
                    require(token.isdecimal() and int(token) < len(node),
                            "Unresolved JSON pointer: " + pointer)
                    node = node[int(token)]
                else:
                    require(isinstance(node, dict) and token in node,
                            "Unresolved JSON pointer: " + pointer)
                    node = node[token]
            result["json_pointer"] = pointer
        if record_sha256 is not None:
            require(pointer is not None, "Record hash requires a JSON pointer")
            require(digest(payload(node)) == record_sha256,
                    "Evidence record hash changed: " + name + pointer)
            result["record_sha256"] = record_sha256
        return result


if __name__ == "__main__":
    source_pins = source_bindings()
    write(DOC / "evidence/source-pins.json", source_pins, "--check" in sys.argv)
    print("PASS Phase 2G frozen source bindings:", len(source_pins["sources"]), flush=True)
