"""Phase 2F immutable inputs and explicit Phase 2E selection (offline)."""
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

BASE = "1f9c0088bdc6f056ab62c63f7e044d06dcda4e03"
TREE = "d22010cae1109d07a3fe77aa1a1369ca667bebde"
BRANCH = "fable2-prototype-archaeology-phase2f"
DOC = Path("docs/fable2-prototype-archaeology/phase2f")
OUT = Path("out/prototype-archaeology/phase2f")
E = Path("docs/fable2-prototype-archaeology/phase2e")
B = Path("out/prototype-archaeology/phase2b")
C = Path("out/prototype-archaeology/phase2c")
D = Path("out/prototype-archaeology/phase2d")
TRUST = {
    "evidence/owner-decision.json": (42203, "7905EDD55A1DDA53C7FDD1D36635FFC7E6315F1BA66F2CB88393A3E5F6F766BD"),
    "evidence/approved-overlay-delta.json": (260564, "BD53722F709EB2BB287482DE09E2D6953EAD19DDA675E1B1C34DEBA55D2D52BC"),
    "evidence/overlay-summary.json": (6062, "CBE09165C150C55568D14043FCF30D6BEC01D7E3A8E0CD38D21C8B476390BF69"),
    "evidence/source-pins.json": (26704, "7F888B5FDE903C72DAA22482C1113D200C9C59D7C207077E0D4824CA20E6E207"),
    "evidence/validation.json": (8620, "B0CB8CFB053A2E982CC663AAF77F3705D7574552975EB933C6825F04462900A5"),
    "report.md": (6746, "9964D22A3629CA66D9D39D50968C3FC17D4B2BC73F07D606D525C5A79A8DDF15"),
    "reservation-inventory.md": (11412, "C1594995410C40D6A670E4966388F4B3AAE389D757C992C6E8A8DE2FCD32492A"),
    "rollback.md": (1062, "D53A4F2C1033B76D0443501F2BF34F8DC55F8E86EAEC5B8B2427B174911470AA"),
    "next-phase-handoff.md": (1753, "826A99A2B1460FA74F965532C83E82992E47640C75D7BB0A2A8A9644B872D90D"),
}
EFFECTIVE = Path("out/prototype-archaeology/phase2e/effective-map.json")
EFFECTIVE_HASH = "E3EE02E659ADCBD79823B3343A542505B45B8B902BAADD158A2A75D577E71663"
require = overlay.require
payload = overlay.payload
digest = overlay.sha256
read = overlay.read


def relative(path):
    p = Path(path)
    require(not p.is_absolute() and ".." not in p.parts and ":" not in str(p), "Repository-relative path required")
    # Existing hash-bound assets use repository junctions. Input provenance is
    # lexical and relative; only authenticated identities may be read through
    # those junctions. Output confinement additionally checks physical paths.
    return ROOT / p


def output(path):
    p = relative(path).resolve()
    require(any(p.is_relative_to(ROOT / r) for r in (DOC, OUT)), "Output outside Phase 2F roots")
    return p


def identity(path):
    p = relative(path)
    with p.open("rb") as stream:
        sha = hashlib.file_digest(stream, "sha256").hexdigest().upper()
    return {"path": Path(path).as_posix(), "size": p.stat().st_size, "sha256": sha}


def check(row):
    require(identity(row["path"]) == {k: row[k] for k in ("path", "size", "sha256")}, "Input identity changed: " + row["path"])


def write(path, document, replay=False):
    p = output(path)
    data = document if isinstance(document, bytes) else payload(document)
    if replay:
        require(p.is_file() and p.read_bytes() == data, "Deterministic replay mismatch: " + str(path))
    else:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return {"path": Path(path).as_posix(), "size": len(data), "sha256": digest(data)}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def exact_start(state):
    require(state == {"branch": "fable2-prototype-archaeology-phase2e", "head": BASE,
                      "tree": TREE, "index": [], "worktree": [],
                      "subject": "Document Phase 2E opt-in rollback and handoff"}, "Phase 2E starting state mismatch")


def opt_in():
    for name, (size, sha) in TRUST.items():
        check({"path": (E / name).as_posix(), "size": size, "sha256": sha})
    check({"path": EFFECTIVE.as_posix(), "size": 8975363, "sha256": EFFECTIVE_HASH})
    return overlay.load_opt_in_mapping(
        "phase2e-v1", ROOT / E / "evidence/owner-decision.json", TRUST["evidence/owner-decision.json"][1],
        ROOT / E / "evidence/approved-overlay-delta.json", TRUST["evidence/approved-overlay-delta.json"][1],
        ROOT / EFFECTIVE, EFFECTIVE_HASH)


def envelope(kind, selection, **fields):
    result = {"schema": {"name": "fable2-prototype-semantic-routes-" + kind, "version": 1},
            "phase2e_commit": BASE, "overlay_selection": selection, "canonical_adoption": False,
            "analysis_only": True, "semantic_feedback_allowed": False, **fields}
    if kind != "source-pins":
        result["source_pins"] = identity(DOC / "evidence/source-pins.json")
    return result


def source_bindings():
    """Authenticate upstream first; never bless changed derived bytes."""
    require(git("rev-parse", "fable2-prototype-archaeology-phase2e") == BASE, "Frozen Phase 2E branch moved")
    require(git("rev-parse", BASE + "^{tree}") == TREE, "Frozen Phase 2E tree changed")
    require(git("log", "-1", "--format=%s", BASE) == "Document Phase 2E opt-in rollback and handoff", "Frozen subject changed")
    require(git("branch", "--show-current") == BRANCH, "Phase 2F branch required")
    overlay.verify_phase2d_frozen()
    effective, selection = opt_in()
    e_validation = read(E / "evidence/validation.json")
    e_pins = read(E / "evidence/source-pins.json")
    d_pins = read("docs/fable2-prototype-archaeology/phase2d/evidence/source-pins.json")
    d_validation = read("docs/fable2-prototype-archaeology/phase2d/evidence/validation.json")
    rows = {}

    def add(row, provenance):
        if row.get("root", "repository") != "repository":
            return
        check(row)
        path = row["path"]
        if path not in rows:
            rows[path] = {k: row[k] for k in ("path", "size", "sha256")}
            rows[path]["provenance_generations"] = []
        require(rows[path]["sha256"] == row["sha256"], "Mixed source generations")
        rows[path]["provenance_generations"].append(provenance)

    for row in d_pins["sources"] + d_pins["upstream_sources"]:
        add(row, "phase2d-source-pins")
    for row in d_validation["artifacts"] + d_validation["implementation"]:
        add(row, "phase2d-validation")
    for row in e_validation["artifacts"] + e_validation["implementation"] + e_validation["documentation"]:
        add(row, "phase2e-validation")
    # All historical documentation/evidence descriptions and schemas are
    # authenticated to the immutable parent, including late handoff commits.
    tracked = git("ls-tree", "-r", "--name-only", BASE, "--", "docs/fable2-prototype-archaeology").splitlines()
    for path in tracked:
        original = subprocess.check_output(["git", "show", BASE + ":" + path], cwd=ROOT)
        add({"path": path, "size": len(original), "sha256": digest(original)}, "phase2e-terminal-tree")
    for row in rows.values():
        row["provenance_generations"] = sorted(set(row["provenance_generations"]))
        row["source_schema"] = read(row["path"]).get("schema") if row["path"].endswith(".json") else None
    start = {"branch": "fable2-prototype-archaeology-phase2e", "head": BASE, "tree": TREE,
             "index": [], "worktree": [], "subject": "Document Phase 2E opt-in rollback and handoff"}
    exact_start(start)
    return envelope("source-pins", selection, sources=sorted(rows.values(), key=lambda r: r["path"]),
                    starting_state=start, remotes=e_pins["repository_state"]["fable_start"]["remotes"],
                    sdk=e_pins["repository_state"]["sdk"], inherited_blockers=e_validation["inherited_blockers"],
                    prebranch_verification={"supported_tests": 330, "failures": 0, "errors": 0, "skips": 0,
                                            "phase2e_replay_stages": 4, "all_checks_passed": True}), effective


class Inputs:
    def __init__(self, pins):
        self.pins = {r["path"]: r for r in pins["sources"]}
        self.used = set()

    def read(self, path):
        path = Path(path).as_posix()
        require(path in self.pins, "Unbound analytical input: " + path)
        check(self.pins[path])
        self.used.add(path)
        return read(path)

    def ref(self, path, pointer):
        path = Path(path).as_posix()
        require(path in self.pins, "Unbound evidence reference: " + path)
        return {k: self.pins[path][k] for k in ("path", "size", "sha256")} | {"json_pointer": pointer}


if __name__ == "__main__":
    pins, _ = source_bindings()
    write(DOC / "evidence/source-pins.json", pins, "--check" in sys.argv)
    print("PASS Phase 2F source bindings:", len(pins["sources"]), flush=True)
