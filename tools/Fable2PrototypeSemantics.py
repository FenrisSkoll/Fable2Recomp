#!/usr/bin/env python3
"""Phase 2B static semantic evidence, separate from canonical symbol adoption."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import platform
import re
import subprocess
import sys
from pathlib import Path

import Fable2PrototypeCorrespondence as phase2a
import Fable2SemanticNative as native
import VerifyFable2PrototypePhase2AConsistency as consistency


ROOT = Path(__file__).resolve().parents[1]
SDK = Path("C:/Dev/rexglue-sdk-v0.10")
BASE = "6ce54cbdcaa9fef23c6cd13e86fe46d3783cf3fd"
BASE_TREE = "774c4f401bd44f8de1ea8f95c7344988ad12773c"
SDK_HEAD = "fa10315ff88ca56b2d0b380de40bad5b59b542bd"
BUNDLE = "DA77AF8D9345C684F81FDD342CDB1E95E48CC826A374D783EEC561F1EDE42B2F"
COMMUNITY_HASH = "A46F45954371927A89DEB51AA9D3372916C2F74CC86BBB944E4F90F1D3324D3F"
COMMUNITY_COMMIT = "8ba7f3d9807e8566475afb5e54f478b235fc309a"
COMMUNITY_URL = "https://raw.githubusercontent.com/JustSomeGuy1234/Fable2Modding/" + COMMUNITY_COMMIT + "/Functions%20and%20Tables%20I%20found.txt"
DOC = Path("docs/fable2-prototype-archaeology/phase2b")
OUT = Path("out/prototype-archaeology/phase2b")
P1 = Path("docs/fable2-prototype-archaeology/phase1/evidence")
P2 = Path("docs/fable2-prototype-archaeology/phase2a/evidence")
DERIVED = Path("out/prototype-archaeology/derived")
CORPUS = Path("D:/Fable2-Recomp/prototypes")
PIN_FILE = DOC / "evidence/semantic-source-pins.json"
ANALYSIS = Path("out/analysis/" + phase2a.EXPECTED["target_postpatch"])
CURRENT_CLOSURE = Path("out/phase5a/tranche-001/closure-after/entrypoint-closure.json")
CURRENT_PLAN = Path("out/phase5a/tranche-001/merged/fable2-indirect-targets.import-plan.json")
BUILDS = ("build-23.12.02.0330", "sep-2008", "canonical-tu1")
STATUSES = ("accepted-registered-callback", "accepted-xref-corroborated",
            "candidate-target-unconfirmed", "candidate-donor-only", "ambiguous", "quarantined", "rejected")
CLASSES = ("distinctive-debug-lua-command", "rtti-type-name", "assertion-diagnostic",
           "source-path-filename", "subsystem-profiling-label", "renderer-debug-label",
           "generic-string", "external-only-observation")


def run(*args, cwd=ROOT):
    return subprocess.check_output(list(args), cwd=cwd).decode("utf-8").strip()


def read(path):
    return json.loads((ROOT / path).read_bytes())


def sha(path):
    return phase2a.sha256_file(path)


def data_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def output_path(path):
    resolved = (ROOT / path).resolve()
    if not resolved.is_relative_to(ROOT) or not any(resolved.is_relative_to(ROOT / r) for r in (DOC, OUT)):
        raise ValueError(f"output outside approved Phase 2B roots: {path}")
    return resolved


def write(path, value, check=False):
    target = output_path(path)
    payload = data_bytes(value)
    if check:
        if not target.is_file() or target.read_bytes() != payload:
            raise ValueError(f"determinism mismatch: {path}")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)


def write_text(path, value, check=False):
    target = output_path(path)
    payload = value.encode("utf-8")
    if check:
        if not target.is_file() or target.read_bytes() != payload:
            raise ValueError(f"report consistency mismatch: {path}")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)


def envelope(kind, **fields):
    return {"schema": {"name": "fable2-prototype-semantics-" + kind, "version": 1},
            "generator": {"name": "Fable2PrototypeSemantics.py", "version": "1.0.0"},
            "phase2a_closeout": BASE, "phase2a_input_bundle_sha256": BUNDLE,
            "timestamp_policy": "omitted-no-clock-input", **fields}


def identity(path, root=ROOT, kind="repository-evidence"):
    full = root / path
    result = {"path": path.as_posix(), "root": "repository" if root == ROOT else "corpus",
              "kind": kind, "size": full.stat().st_size, "sha256": sha(full)}
    if root == ROOT and path.suffix == ".json":
        document = json.loads(full.read_bytes())
        result["schema"] = document.get("schema", {"version": document.get("schema_version")})
        result["producer"] = document.get("generator", document.get("tool", document.get("analyzer_version")))
        result["collections"] = {k: len(v) for k, v in sorted(document.items()) if isinstance(v, list)}
    return result


def sdk_state():
    sub = SDK / "thirdparty/libmspack"
    names = run("git", "diff", "--name-only", cwd=sub).splitlines()
    return {"branch": run("git", "branch", "--show-current", cwd=SDK),
            "head": run("git", "rev-parse", "HEAD", cwd=SDK),
            "tree": run("git", "rev-parse", "HEAD^{tree}", cwd=SDK),
            "remotes": run("git", "remote", "-v", cwd=SDK).splitlines(),
            "status": run("git", "status", "--porcelain=v2", cwd=SDK).splitlines(),
            "libmspack": [{"path": p, "sha256": sha(sub / p), "size": (sub / p).stat().st_size}
                           for p in sorted(names)]}


def audit(pins=None):
    if run("git", "rev-parse", BASE + "^{tree}") != BASE_TREE:
        raise ValueError("Phase 2A closeout tree mismatch")
    if run("git", "branch", "--show-current") != "fable2-prototype-archaeology-phase2b":
        raise ValueError("wrong Phase 2B branch")
    run("git", "merge-base", "--is-ancestor", BASE, "HEAD")
    allowed = {".gitattributes", "tools/Fable2SemanticNative.py", "tools/Fable2PrototypeSemantics.py",
               "tools/schemas/fable2-prototype-semantics-v1.schema.json",
               "tools/Verify-Fable2PrototypeSemantics.ps1",
               "tests/test_fable2_prototype_semantics.py"}
    changed = run("git", "diff", "--name-only", BASE).splitlines()
    untracked = run("git", "ls-files", "--others", "--exclude-standard").splitlines()
    for path in sorted(set(changed + untracked)):
        if path not in allowed and not path.startswith(DOC.as_posix() + "/"):
            raise ValueError(f"forbidden path changed: {path}")
    original_attributes = run("git", "show", BASE + ":.gitattributes")
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8").strip()
    suffix = ("\n\n# Phase 2B hashes implementation and evidence bytes across Windows checkouts.\n"
              "/docs/fable2-prototype-archaeology/phase2b/** text eol=lf\n"
              "/tools/Fable2PrototypeSemantics.py text eol=lf\n"
              "/tools/Fable2SemanticNative.py text eol=lf\n"
              "/tools/Verify-Fable2PrototypeSemantics.ps1 text eol=lf\n"
              "/tools/schemas/fable2-prototype-semantics-v1.schema.json text eol=lf\n"
              "/tests/test_fable2_prototype_semantics.py text eol=lf")
    if attributes != original_attributes + suffix:
        raise ValueError("non-Phase-2B attribute change")
    state = sdk_state()
    if state["head"] != SDK_HEAD:
        raise ValueError("ReXGlue HEAD changed")
    if pins is not None and state != pins["sdk_start"]:
        raise ValueError("ReXGlue or libmspack state changed")
    return sorted(set(changed + untracked))


def bind():
    if (ROOT / PIN_FILE).exists():
        raise ValueError("source pins already exist; no implicit rebind")
    audit()
    consistency.validate(ROOT, ROOT / consistency.SUMMARY_RELATIVE_PATH, ROOT / consistency.REPORT_RELATIVE_PATH)
    summary = read(P2 / "prototype-correspondence-summary.json")
    if summary["input_binding"]["input_bundle_sha256"] != BUNDLE:
        raise ValueError("closed Phase 2A bundle mismatch")
    phase2a.phase1_consistency.validate(ROOT / P1, ROOT / DERIVED, ROOT / P1.parent / "report.md")
    paths = set()
    for prefix in (P1, P2):
        paths.update(p.relative_to(ROOT) for p in (ROOT / prefix).glob("*.json"))
    paths.update(p.relative_to(ROOT) for p in (ROOT / "docs").rglob("*.md"))
    paths.update(p.relative_to(ROOT) for p in (ROOT / "tools/schemas").glob("*.json") if "prototype-semantics" not in p.name)
    paths.update({Path("README.md"), Path("tools/fable2-entrypoint-closure-evidence.json"),
                  Path("tools/Fable2PrototypeCorrespondence.py"), Path("tools/VerifyFable2PrototypePhase2AConsistency.py"),
                  ANALYSIS / "entrypoint-closure.json", ANALYSIS / "ghidra-function-map.json", CURRENT_CLOSURE, CURRENT_PLAN,
                  Path("docs/fable2-native-renderer/candidate-hook-inventory.json"),
                  Path("docs/fable2-discovery-pipeline/ownership/ownership-ledger.json"),
                  Path("docs/fable2-discovery-pipeline/coverage/phase5a-reference-001-ownership/ownership-ledger.json"),
                  Path("docs/fable2-discovery-pipeline/coverage/phase5a-reference-001.json"),
                  Path("docs/fable2-discovery-pipeline/coverage/phase5a-native-001.json"),
                  Path("assets/tu1/default.xex"), Path("assets/tu1/default.xexp")})
    paths.update(consistency.ARTIFACTS.values())
    for build in (*BUILDS, "jul-2009"):
        manifest_path = DERIVED / build / "derived-image.json"
        manifest = read(manifest_path)
        paths.add(manifest_path)
        paths.update(DERIVED / build / row["derived_relative_path"] for row in manifest["memory_blocks"])
    records = [identity(path) for path in sorted(paths)]
    corpus = read(P1 / "prototype-inventory.json")
    for row in corpus["files"]:
        path = Path(corpus["build_summaries"][row["build_id"]]["directory_name"]) / row["relative_path"]
        actual = identity(path, CORPUS, "immutable-corpus")
        if actual["sha256"] != row["sha256"] or actual["size"] != row["size"]:
            raise ValueError(f"Phase 1 corpus differs: {path}")
        records.append(actual)
    community_path = OUT / "external/community-lua.txt"
    community = {"url": COMMUNITY_URL, "commit": COMMUNITY_COMMIT, "expected_sha256": COMMUNITY_HASH,
                 "classification": "unverified-external-community-runtime-evidence", "status": "unavailable"}
    if (ROOT / community_path).is_file():
        actual = identity(community_path, kind="external-community")
        if actual["sha256"] == COMMUNITY_HASH:
            records.append(actual)
            community["status"] = "hash-verified"
        else:
            community["status"] = "unavailable-hash-mismatch"
    result = envelope("source-pins", sources=sorted(records, key=lambda r: (r["root"], r["path"])),
                      community=community, sdk_start=sdk_state(),
                      fable_start={"branch": "fable2-prototype-archaeology-phase2a", "head": BASE,
                                   "tree": BASE_TREE, "status": [], "remotes": run("git", "remote", "-v").splitlines()},
                      python_runtime={"implementation": platform.python_implementation(), "version": platform.python_version()})
    write(PIN_FILE, result)
    print(f"Bound {len(records)} sources")


def verify_inputs():
    pins = read(PIN_FILE)
    audit(pins)
    consistency.validate(ROOT, ROOT / consistency.SUMMARY_RELATIVE_PATH, ROOT / consistency.REPORT_RELATIVE_PATH)
    if pins["phase2a_closeout"] != BASE or pins["phase2a_input_bundle_sha256"] != BUNDLE:
        raise ValueError("wrong closed Phase 2A identity")
    if pins["python_runtime"] != {"implementation": platform.python_implementation(), "version": platform.python_version()}:
        raise ValueError("runtime identity differs from source pins")
    source_keys = [(r["root"], r["path"]) for r in pins["sources"]]
    if len(source_keys) != len(set(source_keys)):
        raise ValueError("duplicate source identity")
    for record in pins["sources"]:
        root = ROOT if record["root"] == "repository" else CORPUS
        relative = Path(record["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("invalid bound relative source path")
        path = (root / record["path"]).resolve()
        # Canonical assets are an established read-only junction. Source identity
        # is the pinned relative input plus exact bytes; output checks are stricter.
        if not path.is_file() or path.stat().st_size != record["size"] or sha(path) != record["sha256"]:
            raise ValueError(f"bound source changed or missing: {record['path']}")
    documents = {
        p.name: read(p.relative_to(ROOT)) for p in sorted((ROOT / P2).glob("*.json"))}
    phase2a.validate_documents(documents, BUNDLE)
    return pins, documents


def descriptor_support(donor, target, callback_pair, callee_pair, caller_pair, exact_name):
    """Independent descriptor role, including an explicitly null stripped name.

    Three accepted pairs and the same caller-relative site are mandatory. A
    missing or unknown target value is not interpreted as a stripped name.
    """
    if not all((callback_pair, callee_pair, caller_pair)):
        return False
    if any(p["status"] not in phase2a.ACCEPTED_STATUSES for p in (callback_pair, callee_pair, caller_pair)):
        return False
    fields = ("object_argument", "value_argument", "offset", "width")
    return (donor["status"] == target["status"] == "proven-native-descriptor"
            and all(donor[k][f] == target[k][f] for k in ("name_store", "callback_store") for f in fields)
            and target["callback"] == callback_pair["target_start"]
            and target["callee"] == callee_pair["target_start"]
            and target["registration_function"]["start"] == caller_pair["target_start"]
            and int(donor["call_instruction"], 16) - int(donor["registration_function"]["start"], 16)
            == int(target["call_instruction"], 16) - int(target["registration_function"]["start"], 16)
            and (exact_name or target["name_address"] == "0x00000000"))


def classify(text, categories=(), command=False, external=False):
    lower = text.lower()
    if external:
        return "external-only-observation"
    if any(c in categories for c in ("source-file", "source-build-path")) or re.search(r"\.(?:cpp|hpp|c|h|pdb)$", lower):
        return "source-path-filename"
    if "rtti-type" in categories or text.startswith((".?AV", ".?AU")):
        return "rtti-type-name"
    if "assertion-residue" in categories or any(x in lower for x in ("assert", "failed", "invalid ")):
        return "assertion-diagnostic"
    if len(text) < 8 or len(set(text)) < 4 or lower in ("animation", "navigation", "perception", "load", "debug"):
        return "generic-string"
    if any(x in lower for x in ("shader", "render", "mesh", "drawgui", "texture", "lighting")):
        return "renderer-debug-label"
    if command:
        return "distinctive-debug-lua-command"
    if "subsystem-terminology" in categories or any(x in lower for x in ("combat", "profile", "queue")):
        return "subsystem-profiling-label"
    return "generic-string"


def subsystem(text):
    for name, tokens in (("renderer", ("shader", "render", "mesh", "texture", "lighting", "drawgui")),
                         ("ai-navigation", ("kynapse", "navigation", "perception", "behaviour")),
                         ("physics", ("physics", "havok")), ("audio", ("audio", "sound", "xlip")),
                         ("combat", ("combat", "weapon")), ("debug", ("debug", "profile"))):
        if any(token in text.lower() for token in tokens):
            return name
    return "unassigned"


def inventory(pins, images):
    anchors = {}
    external_lines = []

    def add(text, provenance, category):
        if not isinstance(text, str) or not text:
            return
        if text not in anchors:
            anchors[text] = {"id": "A-" + native.digest(text)[:24], "spelling": text,
                             "lookup_key": " ".join(text.casefold().split()), "provenance": [],
                             "categories": [], "occurrences": [], "subsystem": subsystem(text)}
        anchors[text]["provenance"].append(provenance)
        anchors[text]["categories"].append(category)

    for suffix, field in (("debug-strings", "records"), ("script-symbols", "records"),
                          ("debug-interfaces", "debug_menu_entries")):
        path = P1 / f"prototype-{suffix}.json"
        for index, row in enumerate(read(path)[field]):
            if suffix == "debug-strings":
                values = [row["string"]]
            elif suffix == "script-symbols":
                values = [row["name"]]
            else:
                values = row["names"]
            for value in values:
                provenance = {"source": path.as_posix(), "json_pointer": f"/{field}/{index}",
                              "build": row["build_id"], "location": {k: v for k, v in row.items()
                               if k in ("source_file", "source_path", "source_line", "source_offset", "offset", "guest_address", "derived_image", "encoding")}}
                add(value, provenance, classify(value, row.get("categories", []), suffix != "debug-strings"))
    features = read(consistency.ARTIFACTS["exhaustive_function_features"])
    for build, rows in sorted(features["builds"].items()):
        for index, row in enumerate(rows):
            for string_index, value in enumerate(row["references"]["strings"]):
                add(value, {"source": consistency.ARTIFACTS["exhaustive_function_features"].as_posix(),
                            "json_pointer": f"/builds/{build}/{index}/references/strings/{string_index}",
                            "build": build, "location": {}}, classify(value))
    if pins["community"]["status"] == "hash-verified":
        namespace = None
        path = OUT / "external/community-lua.txt"
        for line_number, line in enumerate((ROOT / path).read_text(encoding="utf-8-sig").splitlines(), 1):
            code = line.split("--", 1)[0].strip()
            observation = {"line": line_number, "line_sha256": hashlib.sha256(line.encode("utf-8")).hexdigest().upper(),
                           "decision": "ignored-nonidentifier-or-comment", "normalized_name": None}
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\.", code):
                namespace = code[:-1]
                observation["decision"] = "namespace-header"
                observation["normalized_name"] = namespace
            elif re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", code) and namespace:
                observation["decision"] = "unverified-community-observation"
                observation["normalized_name"] = namespace + "." + code
                add(namespace + "." + code, {"source": path.as_posix(), "json_pointer": None,
                     "build": "unknown-external", "location": {"line": line_number}}, "external-only-observation")
            external_lines.append(observation)
    # Exact NUL-terminated byte matches only. Qualified-to-terminal lookups are
    # candidate aliases, never proof of a namespace or binding.
    lookup = collections.defaultdict(list)
    for text in sorted(anchors):
        lookup[text].append(text)
        if re.fullmatch(r"[A-Za-z_]\w*(?:[.:][A-Za-z_]\w*)+", text):
            lookup[re.split(r"[.:]", text)[-1]].append(text)
    for build, image in sorted(images.items()):
        for block in image.blocks:
            if block.execute or block.name not in (".rdata", ".data"):
                continue
            for encoding, pattern in (("ascii", rb"[\x20-\x7e]{3,}\x00"),
                                      ("utf-16le", rb"(?:[\x20-\x7e]\x00){3,}\x00\x00")):
                for match in re.finditer(pattern, block.data):
                    payload = match.group()[:-1 if encoding == "ascii" else -2]
                    spelling = payload.decode(encoding)
                    for text in sorted(set(lookup.get(spelling, []))):
                        anchors[text]["occurrences"].append({"build": build, "address": native.hx(block.start + match.start()),
                            "section": block.name, "offset": match.start(), "encoding": encoding,
                            "match": "exact" if text == spelling else "terminal-candidate", "native_spelling": spelling,
                            "source": (DERIVED / build / block.relative_path).as_posix()})
    for row in anchors.values():
        row["categories"] = sorted(set(row["categories"]))
        row["provenance"] = sorted(row["provenance"], key=lambda p: data_bytes(p))
        row["occurrences"] = sorted(row["occurrences"], key=lambda p: data_bytes(p))
        row["filters"] = []
        if set(row["categories"]) <= {"generic-string", "external-only-observation"}:
            row["filters"].append("generic-or-external-only-no-semantic-acceptance")
        if len(row["spelling"]) > 200:
            row["filters"].append("overlong-anchor-review-only")
        row["duplicate_provenance_count"] = len(row["provenance"]) - 1
    return sorted(anchors.values(), key=lambda a: a["id"]), features, external_lines


def grade(*, filtered, donor_refs, mapping, corroboration, contradictions, ambiguous=False, registration=False):
    if contradictions:
        return "quarantined", "contradictory-target-context"
    if ambiguous:
        return "ambiguous", "multiple-native-meanings-or-field-roles"
    if filtered:
        return "quarantined", "generic-external-or-unsafe-anchor"
    if not donor_refs:
        return "quarantined", "no-proven-native-donor-reference"
    if mapping is None:
        return "candidate-donor-only", "no-closed-accepted-correspondence"
    if mapping["status"] not in phase2a.ACCEPTED_STATUSES:
        raise ValueError("attempted nonaccepted mapping join")
    if not corroboration:
        return "candidate-target-unconfirmed", "target-semantic-support-insufficient"
    return ("accepted-registered-callback" if registration else "accepted-xref-corroborated"), "all-evidence-gates-satisfied"


def record_ids(rows, prefix):
    for row in rows:
        row["id"] = prefix + "-" + native.digest(row)[:24]
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate {prefix} record")
    rows.sort(key=lambda r: r["id"])
    return rows


def validate_family(payloads, mappings, counts=None):
    """Cross-artifact semantic invariants, independent of JSON shape validation."""
    def require(condition, message):
        if not condition:
            raise ValueError(message)

    def indexed(rows):
        result = {r["id"]: r for r in rows}
        require(len(result) == len(rows), "duplicate record identifier")
        return result

    anchors = indexed(payloads["inventory"]["anchors"])
    refs = indexed(payloads["xrefs"]["references"])
    indexed(payloads["xrefs"]["data_pointers"])
    regs = indexed(payloads["registrations"]["records"])
    rows = payloads["index"]["records"]
    row_ids = indexed(rows)
    indexed(payloads["mapping-review"]["records"])
    indexed(payloads["globals"]["records"])
    keys, actual, expected = set(), set(), set()
    address_functions = collections.defaultdict(set)
    for ref in refs.values():
        boundary = ref["function"]
        require(int(boundary["start"], 16) <= int(ref["instruction"], 16) < int(boundary["end_exclusive"], 16), "xref outside boundary")
        require(boundary["size"] == int(boundary["end_exclusive"], 16) - int(boundary["start"], 16), "boundary size mismatch")
        address_functions[(ref["build"], ref["anchor_address"])].add(boundary["start"])
    for anchor in anchors.values():
        require(bool(anchor["provenance"]), "anchor missing provenance")
        for build in BUILDS[:2]:
            functions = set()
            for occurrence in anchor["occurrences"]:
                if occurrence["build"] == build:
                    functions.update(address_functions[(build, occurrence["address"])])
            expected.update((anchor["id"], build, f) for f in functions or {None})
    accepted = []
    for row in rows:
        require(row["anchor_id"] in anchors, "unknown anchor")
        require(row["status"] in STATUSES, "unknown terminal status")
        require(row["canonical_adoption"] is False and row["proposed_name"] is None, "semantic propagation forbidden")
        function = row["donor_function"]
        key = (row["anchor_id"], row["build"], row["kind"], function["start"] if function else None, row.get("donor_registration"))
        require(key not in keys, "duplicate association or mapping join")
        keys.add(key)
        if row["kind"] == "native-xref-context":
            actual.add((row["anchor_id"], row["build"], function["start"] if function else None))
        anchor = anchors[row["anchor_id"]]
        occurrences = {(o["build"], o["address"]) for o in anchor["occurrences"]}
        for ref_id in row["donor_xrefs"]:
            require(ref_id in refs, "missing donor xref")
            ref = refs[ref_id]
            require(ref["build"] == row["build"] and ref["function"] == function, "donor xref owner mismatch")
            require((ref["build"], ref["anchor_address"]) in occurrences, "xref does not reference anchor")
        mapping = row["mapping"]
        if mapping:
            index = mapping["record_index"]
            require(0 <= index < len(mappings) and mappings[index] == mapping["record"], "closed mapping identity mismatch")
            pair = mapping["record"]
            require(pair["status"] in phase2a.ACCEPTED_STATUSES and row["build"] == BUILDS[0], "nonaccepted or secondary join")
            require(function is not None and function["start"] == pair["donor_start"] and function["end_exclusive"] == pair["donor_end_exclusive"], "mapping boundary mismatch")
            require(row["correspondence_block"] is None, "joined record also blocked")
        if row["contradictions"]:
            require(row["status"] in ("quarantined", "rejected"), "contradiction escaped quarantine")
        for support in row["target_corroboration"]:
            require(mapping is not None, "support without mapping")
            ci = support["callee_mapping_index"]
            require(0 <= ci < len(mappings) and mappings[ci]["status"] in phase2a.ACCEPTED_STATUSES, "uncorroborated callee")
            if support["kind"] == "same-distinctive-anchor-same-argument-mapped-callee":
                require(support["donor_xref"] in row["donor_xrefs"] and support["target_xref"] in refs, "missing support xref")
                donor, target = refs[support["donor_xref"]], refs[support["target_xref"]]
                exact = {(o["build"], o["address"]) for o in anchor["occurrences"] if o["match"] == "exact"}
                require((donor["build"], donor["anchor_address"]) in exact and (target["build"], target["anchor_address"]) in exact, "nonexact anchor support")
                require(target["build"] == "canonical-tu1" and target["function"]["start"] == pair["target_start"], "wrong target owner")
                require(donor["role"] == target["role"] == "call-argument" and donor["operand"] == target["operand"], "incompatible target role")
                require(donor["destination"] == mappings[ci]["donor_start"] and target["destination"] == mappings[ci]["target_start"], "callee mismatch")
                require(int(donor["instruction"], 16) - int(function["start"], 16) == int(target["instruction"], 16) - int(pair["target_start"], 16), "call offset mismatch")
            elif support["kind"] == "proven-equivalent-descriptor":
                require(support["donor_registration"] in regs and support["target_registration"] in regs, "missing registration context")
                donor, target = regs[support["donor_registration"]], regs[support["target_registration"]]
                exact = any(o["build"] == "canonical-tu1" and o["address"] == target["name_address"] and o["match"] == "exact" for o in anchor["occurrences"])
                require(descriptor_support(donor, target, pair, mappings[ci], mappings[support["caller_mapping_index"]], exact), "descriptor role mismatch")
            else:
                raise ValueError("unsupported target corroboration")
        if row["status"].startswith("accepted-"):
            require(not anchor["filters"] and not row["contradictions"] and mapping and row["target_corroboration"], "incomplete accepted evidence chain")
            require(bool(row["donor_xrefs"]) or row.get("donor_registration") in regs, "no native accepted evidence")
            accepted.append(row)
    require(actual == expected, "terminal coverage mismatch")
    require(payloads["accepted"]["records"] == accepted, "accepted subset mismatch")
    for row in payloads["graph"]["records"] + payloads["globals"]["records"]:
        require(row["semantic_acceptance"] is False, "graph/global semantic propagation forbidden")
    for row in payloads["mapping-review"]["records"]:
        require(row["association_id"] in row_ids and row["mapping_changed"] is False, "mapping review mutated or orphaned")
    queue, availability = review_queue(rows, anchors, sorted({i["set"] for r in rows for i in r["intersections"]} | set(payloads["review"]["problem_sets"])))
    require(queue == payloads["review"]["records"] and availability == payloads["review"]["availability"], "review selection/count drift")
    if counts is not None:
        require(counts["investigated_associations"] == len(rows) and counts["accepted"] == len(accepted), "terminal total mismatch")
        require(counts["statuses"] == {s: sum(r["status"] == s for r in rows) for s in STATUSES}, "terminal count mismatch")


def review_queue(rows, anchors, problem_names):
    strata = [(s, lambda r, s=s: r["status"] == s) for s in STATUSES]
    strata += [("subsystem:" + sub, lambda r, sub=sub: anchors[r["anchor_id"]]["subsystem"] == sub)
               for sub in sorted({a["subsystem"] for a in anchors.values()})]
    strata += [("category:" + cat, lambda r, cat=cat: cat in anchors[r["anchor_id"]]["categories"]) for cat in CLASSES]
    strata += [("source:" + build, lambda r, build=build: r["build"] == build) for build in BUILDS[:2]]
    strata += [("problem:" + key, lambda r, key=key: any(i["set"] == key for i in r["intersections"])) for key in sorted(problem_names)]
    queue, availability = [], {}
    for name, predicate in strata:
        available = sorted([r for r in rows if predicate(r)], key=lambda r: r["id"])
        selection = available[:3]
        availability[name] = {"available": len(available), "selected": len(selection)}
        queue.extend({"stratum": name, "association_id": r["id"]} for r in selection)
    return queue, availability


def problem_sets():
    closure = read(CURRENT_CLOSURE)
    plan = read(CURRENT_PLAN)
    ghidra = read(ANALYSIS / "ghidra-function-map.json")
    if closure["image_identity"]["patched_image_sha256"] != phase2a.EXPECTED["target_postpatch"]:
        raise ValueError("current closure target identity mismatch")
    sets = collections.defaultdict(list)
    for index, row in enumerate(closure["candidates"]):
        address = row.get("address", row.get("target"))
        if address:
            sets["closure"].append((int(address, 16), CURRENT_CLOSURE.as_posix(), f"/candidates/{index}", row["classification"]))
    for index, row in enumerate(closure["jump_table_recovery"]["indirect_sites"]):
        if row.get("uses_ctr") and row.get("classification") != "switch_bctr" and not row.get("link", True):
            sets["indirect"].append((int(row["site"], 16), CURRENT_CLOSURE.as_posix(),
                                      f"/jump_table_recovery/indirect_sites/{index}", row["classification"]))
    for path in (Path("docs/fable2-discovery-pipeline/ownership/ownership-ledger.json"),
                 Path("docs/fable2-discovery-pipeline/coverage/phase5a-reference-001-ownership/ownership-ledger.json")):
        for index, row in enumerate(read(path)["targets"]):
            sets["ownership"].append((int(row["target"], 16), path.as_posix(), f"/targets/{index}", row["classification"]))
    for index, row in enumerate(plan["targets"]):
        sets["coverage"].append((int(row["target"], 16), CURRENT_PLAN.as_posix(), f"/targets/{index}", row["classification"]))
    for index, row in enumerate(ghidra["functions"]):
        entry = row.get("entry", row.get("entry_point"))
        if entry:
            sets["ghidra"].append((int(entry, 16), (ANALYSIS / "ghidra-function-map.json").as_posix(), f"/functions/{index}", "map-entry-not-semantic-proof"))
    renderer_path = Path("docs/fable2-native-renderer/candidate-hook-inventory.json")
    for index, row in enumerate(read(renderer_path)["candidates"]):
        entry = row.get("guest_address", row.get("address", row.get("entry")))
        if entry:
            sets["renderer"].append((int(entry, 16), renderer_path.as_posix(), f"/candidates/{index}", "existing-renderer-review-candidate"))
    # Historical crash addresses are historical review intersections, not open
    # failures. Their current resolved disposition stays explicit.
    for address, path in ((0x82174734, "docs/fable2-discovery-pipeline/04-runtime-indirect-target-seed.md"),
                          (0x8223FD7C, "docs/fable2-discovery-pipeline/03a-jump-table-regression-closure.md"),
                          (0x825E28B0, "docs/fable2-discovery-pipeline/09-phase5a-tranche-001.md")):
        sets["historical-crash"].append((address, path, None, "resolved-historical-target"))
    return {key: sorted(rows) for key, rows in sorted(sets.items())}


def intersections(function, sets):
    start, end = int(function["start"], 16), int(function["end_exclusive"], 16)
    return [{"set": key, "address": native.hx(address), "source": source,
             "json_pointer": pointer, "disposition": disposition}
            for key, values in sorted(sets.items()) for address, source, pointer, disposition in values
            if start <= address < end]


def global_evidence(scans, images, mappings):
    target_uses = collections.defaultdict(list)
    for use in scans["canonical-tu1"]["accesses"]:
        key = (use["function"]["start"], int(use["instruction"], 16) - int(use["function"]["start"], 16))
        target_uses[key].append(use)
    result = []
    for donor in scans[BUILDS[0]]["accesses"]:
        pair = mappings.get(donor["function"]["start"])
        if pair is None:
            continue
        offset = int(donor["instruction"], 16) - int(donor["function"]["start"], 16)
        for target in target_uses[(pair[1]["target_start"], offset)]:
            left = images[BUILDS[0]].read(int(donor["address"], 16), donor["width"])
            right = images["canonical-tu1"].read(int(target["address"], 16), target["width"])
            equal = left == right
            compatible = native.compatible_access(donor, target)
            result.append({"donor_access": donor, "target_access": target,
                           "mapping_index": pair[0], "content_equal": equal,
                           "donor_content_sha256": hashlib.sha256(left).hexdigest().upper(),
                           "target_content_sha256": hashlib.sha256(right).hexdigest().upper(),
                           "compatible_width_and_direction": compatible,
                           "status": "candidate-compatible-scalar" if equal and compatible else "quarantined",
                           "semantic_acceptance": False,
                           "limitation": "Access-sized scalar only; complete object boundary and aliasing are unproved."})
    return record_ids(result, "G")


def report_text(summary, payloads):
    anchors = {r["id"]: r for r in payloads["inventory"]["anchors"]}
    refs = {r["id"]: r for r in payloads["xrefs"]["references"]}
    rows = payloads["index"]["records"]
    examples = [r for r in rows if r["mapping"]]
    examples += next(([r] for r in rows if r["status"] == "ambiguous"), [])
    examples += next(([r] for r in rows if r["reason"] == "no-proven-native-donor-reference"), [])
    lines = ["# Prototype archaeology Phase 2B — static semantic evidence", "",
             "Generated report; regenerate with `python tools/Fable2PrototypeSemantics.py generate`.", "",
             "## Result and interpretation", "",
             f"**CONFIRMED:** {summary['counts']['accepted']} semantic associations satisfy this version's full acceptance policy. "
             "This is a bounded static-analysis result, not proof that the binaries contain no recoverable semantics.", "",
             "The 15,299 Phase 2A binary correspondences are **not 15,299 semantic names**. "
             "Their 2,779 exact and 12,520 normalized acceptances remain closed and unchanged. "
             "September's 9,600 secondary mappings are not a semantic-accuracy measurement. "
             "The closed artifacts retain that secondary result as aggregate validation, not an exhaustive reusable pair index; "
             "this pipeline therefore reports September native evidence without inventing secondary joins. July is only an exact-image alias/control.", "",
             "Community observations are unverified live-Lua-environment reports with unknown executable version. "
             "Their spelling, namespace headers and line provenance are candidate material, never native callback proof.", "",
             "## Exact identities", "",
             f"Phase 2A close-out commit: `{BASE}`; tree: `{BASE_TREE}`.", "",
             f"Phase 2A input bundle: `{BUNDLE}`.", "",
             f"Source inventory SHA-256: `{summary['source_pins_sha256']}`. "
             "[Source pins](evidence/semantic-source-pins.json) bind every input's relative path, size, hash, available schema/producer metadata, "
             "collection counts, initial repository states and the pre-existing SDK modification hashes. "
             "[Validation](evidence/semantic-validation.json) binds implementation and exhaustive output bytes.", "",
             "Preferred donor container: `0686A9F292A3F6777BEB6E8D4924F96247D1E8E3E2370323572F797E6637A4AA`; "
             "initialized executable fingerprint: `AE15F6D9AF8C76B3643A0CB5EF7B108E686794250F6822C2A71C78FE3D0BE956`.", "",
             "TU1 post-patch image: `BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00`; "
             "initialized executable fingerprint: `5C8B78B84C93028D166E3DF347206E6642BA40BF374AD1AF8D958B2211320357`.", "",
             "## Reconciled counts", "",
             "Counts below are generated from the actual terminal index. Category/source totals overlap when an anchor has multiple provenance records. "
             "An association is one anchor/build/containing-function context (or one no-XREF terminal); callback-descriptor contexts are separate. "
             "Instruction references and direct data slots are different evidence kinds. Quarantined table records are not structurally proven registrations. "
             "Blocked-by-status counts overlap terminal grades; they are not additional associations.", "", "```json",
             json.dumps(summary["counts"], sort_keys=True, indent=2), "```", "",
             "## Evidence family", "", "| Artifact | Bytes | SHA-256 |", "| --- | ---: | --- |"]
    for item in summary["artifacts"]:
        lines.append(f"| `{item['path']}` | {item['size']} | `{item['sha256']}` |")
    lines += ["", "All eleven JSON documents use `tools/schemas/fable2-prototype-semantics-v1.schema.json`, "
              "with distinct schema names and version 1. The nine exhaustive outputs remain ignored; only byte bindings and review-sized documentation are committed. "
              "No executable bytes or script-bank contents are embedded in committed evidence.", "",
              "## Bounded policy and limitations", "",
              "CONFIRMED XREFs require exact .pdata ownership and a consumed address at a call argument, store or memory access. "
              "An intermediate `lis` value is not a string reference. Address construction models signed addis/addi, ori/oris, mr/or and selected byte/halfword/word direct/indexed loads and stores. "
              "Unknown operations, basic-block boundaries and calls kill constants; chains are bounded to 32 instructions. "
              "Only initialized read-only non-executable pointers are propagated. No ABI TOC constant, writable initial pointer, interprocedural state or cross-CFG value is assumed.", "",
              "A call-argument XREF proves that the value reaches that argument register at the call, not that the callee interprets it as a Lua name. "
              "Distinctive literal acceptance additionally requires the exact target literal, matching argument/call offset, accepted callee correspondence and no competing target evidence. "
              "Source filenames remain context, not proposed function names.", "",
              "Registration recovery tests 8-byte name/callback layouts, repeated joint loads, bounded constructor stores and a strict counted descriptor loop. "
              "A layout alone always remains quarantined. Constructor proof requires repeated exact argument flow into nonoverlapping fields of the same object; "
              "the loop additionally proves cursor, unsigned bound, stride, exact backedge and every callback boundary. "
              "A proven descriptor is not proof of a complete Lua namespace or invocation lifetime. Target acceptance requires three accepted pairs "
              "(callback, constructor and containing caller), corresponding callsite and field roles. An explicitly null target name may use this structural support; an unknown value may not. "
              "Other layouts, complex registration routines and larger loops remain outside this recognizer's coverage.", "",
              "Graph expansion is depth 1/fan-out 8, with cycles and fan-out truncation recorded. "
              "Edges require donor direct calls and corresponding TU1 calls through accepted pairs. Neighbours receive no semantic names. "
              "Scalar data candidates require exact mapped accesses and content hashes; width/read-write conflicts quarantine them. "
              "No scalar candidate is accepted as a global object: complete object boundaries and aliasing remain unproved. "
              "The approximately 99.02% same-address data observation is not an acceptance rule.", "",
              "## Current recompilation intersections", "",
              f"Current closure source: `{CURRENT_CLOSURE.as_posix()}`. Current coverage/import source: `{CURRENT_PLAN.as_posix()}`. "
              "These are distinct from the older closure retained in Phase 2A. Exact source hashes are pinned; the latter is not silently substituted for current problem evidence. "
              "Ownership rows retain both authoritative ledgers and their dispositions. Renderer boundaries are the eleven existing review candidates, not newly established renderer identities. "
              "Historical crash addresses `0x82174734`, `0x8223FD7C` and `0x825E28B0` are explicitly resolved historical intersections, not asserted open failures.", "",
              "The aggregate intersection counts above and each association's `intersections` provide exact review links. "
              "No intersection by itself raises a semantic grade or authorizes a manifest/runtime fix.", "",
              "## Representative evidence chains", "",
              "All joined contexts are shown below, followed by a bounded ambiguous and no-XREF example. "
              "The complete mapping record is retained; XREF definitions identify exact donor/target instruction addresses. "
              "Only one provenance row is displayed here; the inventory preserves all original spellings and provenance. "
              "Literal conflicts are confirmed differences at corresponding argument sites, not automatic disproof of the closed binary mapping."]
    for row in examples:
        anchor = anchors[row["anchor_id"]]
        selected_refs = list(row["donor_xrefs"])
        for support in row["target_corroboration"] + row["contradictions"]:
            if "target_xref" in support:
                selected_refs.append(support["target_xref"])
        example = {"anchor": anchor["spelling"], "anchor_id": anchor["id"],
                   "provenance_example": anchor["provenance"][0], "association": row,
                   "references": [refs[key] for key in sorted(set(selected_refs))[:6]],
                   "reference_display_limit": 6, "complete_reference_count": len(set(selected_refs))}
        lines += ["", f"### {row['status']}: `{anchor['spelling'].replace('`', '')[:120]}`", "", "```json",
                  json.dumps(example, ensure_ascii=False, sort_keys=True, indent=2), "```"]
    lines += ["", "There are no accepted real examples to promote and no real `rejected` terminal assertions in this run. "
              "Rejection fixtures instead demonstrate disproven hypotheses (non-executable/interior callbacks, wrong loop backedges and incompatible access roles); "
              "production retains these unsafe candidates as quarantined records. Synthetic positive descriptor/stripped-name fixtures validate implemented gates, not retail semantic accuracy.", "",
              "## Verification and safety", "",
              "Generation rehashes all sources, runs the closed Phase 2A consistency verifier before consumption, "
              "checks the closed document invariants, reconciles exact terminal coverage, accepted subsets and review availability, "
              "and audits the complete Git delta against a Phase 2B-only allowlist. SDK branch/HEAD/tree/status and modified libmspack bytes must equal the initial capture. "
              "Verification repeats analysis and compares every JSON and this report byte-for-byte; timestamps and current HEAD are not analytical inputs. "
              "Schema checking is a separate required command documented in the README. Mutation tests cover omitted/duplicated records, unsupported acceptance, review drift and forbidden propagation.", "",
              "No canonical names, manifest entries, overrides, generated source, runtime code, renderer code, SDK code or binary inputs were changed. "
              "Neither prototype nor TU1 was launched. No gameplay, input automation, screenshots, build/codegen or shader/resource parsing was performed. "
              "The only network operation was the authorized pinned community raw-file retrieval. No push, fetch, pull, merge, tag, PR, upload or release operation was performed.", "",
              "Next step: review the mapped literal conflicts and the HammerCombat callee boundary/context statically; do not adopt symbols yet. "
              "See [review guide](review-guide.md), [handoff](phase2c-handoff.md) and [reproduction commands](README.md).", ""]
    return "\n".join(lines)


def generate(check=False):
    pins, documents = verify_inputs()
    images = {}
    for build in BUILDS:
        manifest, blocks, _ = phase2a.load_build(ROOT / DERIVED, build)
        images[build] = native.Image(build, blocks)
    anchors, features, external_lines = inventory(pins, images)
    scans = {}
    for build in BUILDS:
        addresses = {int(o["address"], 16) for a in anchors for o in a["occurrences"] if o["build"] == build}
        scans[build] = native.scan_image(images[build], addresses)
        scans[build]["tables"] = native.table_candidates(images[build], addresses, scans[build]["calls"])
        descriptor_names = addresses | ({0} if build == "canonical-tu1" else set())
        scans[build]["constructors"] = native.constructor_registrations(images[build], descriptor_names, scans[build]["calls"])
        scans[build]["constructors"].extend(native.recover_counted_registration_loops(images[build], addresses))
        print(f"Scanned {build}: {len(scans[build]['references'])} instruction references", flush=True)
    refs = record_ids([r for build in BUILDS for r in scans[build]["references"]], "X")
    pointers = record_ids([r for build in BUILDS for r in scans[build]["pointers"]], "P")
    registrations = record_ids([r for build in BUILDS for r in scans[build]["tables"] + scans[build]["constructors"]], "R")
    by_address = collections.defaultdict(list)
    for row in refs:
        by_address[(row["build"], row["anchor_address"])].append(row)
    mappings = {r["donor_start"]: (index, r) for index, r in enumerate(documents["prototype-correspondence-accepted.json"]["records"])}
    status_index = {r["donor_start"]: r for r in documents["prototype-correspondence-index.json"]["functions"]}
    targets_by_offset = collections.defaultdict(list)
    for row in scans["canonical-tu1"]["references"]:
        targets_by_offset[(row["function"]["start"], int(row["instruction"], 16) - int(row["function"]["start"], 16))].append(row)
    sets = problem_sets()
    associations = []
    for anchor in anchors:
        for build in BUILDS[:2]:
            occurrences = [o for o in anchor["occurrences"] if o["build"] == build]
            grouped = collections.defaultdict(list)
            for occurrence in occurrences:
                for ref in by_address[(build, occurrence["address"])]:
                    grouped[ref["function"]["start"]].append((ref, occurrence))
            if not grouped:
                grouped[None] = []
            for function, pairs in sorted(grouped.items(), key=lambda item: item[0] or ""):
                refs_for_item = sorted({r["id"] for r, _ in pairs})
                mapping_entry = mappings.get(function) if build == BUILDS[0] else None
                mapping = mapping_entry[1] if mapping_entry else None
                support, contradictions = [], []
                if mapping:
                    for donor_ref, occurrence in pairs:
                        if donor_ref["role"] != "call-argument" or occurrence["match"] != "exact":
                            continue
                        offset = int(donor_ref["instruction"], 16) - int(function, 16)
                        callee_mapping = mappings.get(donor_ref["destination"])
                        for target_ref in targets_by_offset[(mapping["target_start"], offset)]:
                            if target_ref["role"] != "call-argument" or donor_ref["operand"] != target_ref["operand"]:
                                continue
                            exact_target = any(o["build"] == "canonical-tu1" and o["match"] == "exact" and
                                               o["address"] == target_ref["anchor_address"] for o in anchor["occurrences"])
                            if not exact_target:
                                contradictions.append({"kind": "different-literal-in-corresponding-call-argument",
                                                       "donor_xref": donor_ref["id"], "target_xref": target_ref["id"],
                                                       "interpretation": "semantic-conflict-for-review-not-disproof-of-binary-correspondence"})
                            elif callee_mapping and target_ref["destination"] != callee_mapping[1]["target_start"]:
                                contradictions.append({"kind": "mapped-callee-role-conflict", "donor_xref": donor_ref["id"], "target_xref": target_ref["id"]})
                            elif exact_target and callee_mapping:
                                support.append({"kind": "same-distinctive-anchor-same-argument-mapped-callee",
                                                "donor_xref": donor_ref["id"], "target_xref": target_ref["id"],
                                                "callee_mapping_index": callee_mapping[0]})
                duplicates = len({o["address"] for o in occurrences}) > 1 and "generic-string" in anchor["categories"]
                status, reason = grade(filtered=bool(anchor["filters"]), donor_refs=refs_for_item,
                                       mapping=mapping, corroboration=support, contradictions=contradictions,
                                       ambiguous=duplicates and bool(pairs))
                blocked = None
                if pairs and mapping is None:
                    blocked = status_index.get(function, {}).get("status", "no-accepted-pair") if build == BUILDS[0] else "no-closed-secondary-pair-record"
                associations.append({"anchor_id": anchor["id"], "build": build, "kind": "native-xref-context",
                    "donor_function": pairs[0][0]["function"] if pairs else None, "donor_xrefs": refs_for_item,
                    "mapping": {"source": (P2 / "prototype-correspondence-accepted.json").as_posix(),
                                "record_index": mapping_entry[0], "record": mapping} if mapping else None,
                    "target_corroboration": sorted(support, key=data_bytes), "contradictions": sorted(contradictions, key=data_bytes),
                    "status": status, "reason": reason, "correspondence_block": blocked,
                    "proposed_name": None, "canonical_adoption": False,
                    "intersections": intersections({"start": mapping["target_start"], "end_exclusive": mapping["target_end_exclusive"]}, sets) if mapping else []})
    # Descriptor callback associations are distinct from the containing
    # registration routine's string context. Do not conflate those functions.
    for registration in registrations:
        if registration["build"] != BUILDS[0] or registration["status"] != "proven-native-descriptor":
            continue
        for anchor in anchors:
            if not any(o["build"] == BUILDS[0] and o["address"] == registration["name_address"] for o in anchor["occurrences"]):
                continue
            mapping_entry = mappings.get(registration["callback"])
            mapping = mapping_entry[1] if mapping_entry else None
            callee_mapping = mappings.get(registration["callee"])
            support, contradictions = [], []
            caller_mapping = mappings.get(registration["registration_function"]["start"])
            donor_exact = any(o["build"] == BUILDS[0] and o["address"] == registration["name_address"] and o["match"] == "exact" for o in anchor["occurrences"])
            for target in registrations:
                if target["build"] != "canonical-tu1" or target["status"] != "proven-native-descriptor":
                    continue
                target_exact = any(o["build"] == "canonical-tu1" and o["address"] == target["name_address"] and o["match"] == "exact" for o in anchor["occurrences"])
                role_equal = (target["name_store"]["offset"], target["callback_store"]["offset"]) == (registration["name_store"]["offset"], registration["callback_store"]["offset"])
                if mapping and callee_mapping and caller_mapping and role_equal and target["callee"] == callee_mapping[1]["target_start"]:
                    if donor_exact and descriptor_support(registration, target, mapping, callee_mapping[1], caller_mapping[1], target_exact):
                        support.append({"kind": "proven-equivalent-descriptor", "donor_registration": registration["id"], "target_registration": target["id"], "callee_mapping_index": callee_mapping[0], "caller_mapping_index": caller_mapping[0], "target_name": "exact" if target_exact else "explicit-null-stripped"})
                    elif target["callback"] != mapping["target_start"]:
                        contradictions.append({"kind": "descriptor-callback-role-conflict", "target_registration": target["id"]})
            status, reason = grade(filtered=bool(anchor["filters"]), donor_refs=[registration["id"]], mapping=mapping,
                                   corroboration=support, contradictions=contradictions, registration=True)
            associations.append({"anchor_id": anchor["id"], "build": BUILDS[0], "kind": "registered-callback-context",
                "donor_function": registration["callback_boundary"], "donor_xrefs": [], "donor_registration": registration["id"],
                "mapping": {"source": (P2 / "prototype-correspondence-accepted.json").as_posix(), "record_index": mapping_entry[0], "record": mapping} if mapping else None,
                "target_corroboration": support, "contradictions": contradictions, "status": status, "reason": reason,
                "correspondence_block": None if mapping else status_index.get(registration["callback"], {}).get("status", "no-accepted-pair"),
                "proposed_name": None, "canonical_adoption": False,
                "intersections": intersections({"start": mapping["target_start"], "end_exclusive": mapping["target_end_exclusive"]}, sets) if mapping else []})
    associations = record_ids(associations, "S")
    accepted = [r for r in associations if r["status"].startswith("accepted-")]
    mapping_review = record_ids([{"association_id": r["id"], "anchor_id": r["anchor_id"],
                                 "donor_function": r["donor_function"], "blocking_status": r["correspondence_block"],
                                 "phase2a_record": status_index.get(r["donor_function"]["start"]),
                                 "reason": "target-semantic-conflict" if r["contradictions"] else "native-anchor-context-for-later-mapping-review",
                                 "contradictions": r["contradictions"], "mapping_changed": False}
                                for r in associations if r["donor_function"] and r["build"] == BUILDS[0] and (r["correspondence_block"] or r["contradictions"])], "M")
    target_features = {r["start"]: r for r in features["builds"]["canonical-tu1"]}
    edges = {}
    for row in features["builds"][BUILDS[0]]:
        if row["start"] not in mappings:
            continue
        target_calls = {c["instruction_offset"]: c["target"] for c in target_features[mappings[row["start"]][1]["target_start"]]["direct_calls"]}
        edges[row["start"]] = [c["target"] for c in row["direct_calls"] if c["target"] in mappings and
                               target_calls.get(c["instruction_offset"]) == mappings[c["target"]][1]["target_start"]]
    anchor_by_id = {a["id"]: a for a in anchors}
    graph = native.expand([r["donor_function"]["start"] for r in associations if r["donor_xrefs"] and not anchor_by_id[r["anchor_id"]]["filters"] and r["build"] == BUILDS[0]], edges)
    globals_found = global_evidence(scans, images, mappings)
    queue, availability = review_queue(associations, anchor_by_id, sorted(sets))
    counts = {"sources": len(pins["sources"]), "anchors": len(anchors),
              "filtered_anchors": sum(bool(a["filters"]) for a in anchors),
              "xref_resolved_anchors": len({r["anchor_id"] for r in associations if r["donor_xrefs"]}),
              "instruction_xrefs": len(refs), "data_pointer_xrefs": len(pointers),
              "registration_records": len(registrations),
              "proven_native_descriptors": sum(r["status"] == "proven-native-descriptor" for r in registrations),
              "investigated_associations": len(associations), "joins": sum(r["mapping"] is not None for r in associations),
              "target_corroborated": sum(bool(r["target_corroboration"]) for r in associations),
              "accepted": len(accepted), "statuses": {s: sum(r["status"] == s for r in associations) for s in STATUSES},
              "blocked_by_status": dict(sorted(collections.Counter(r["correspondence_block"] for r in associations if r["correspondence_block"]).items())),
              "accepted_mapping_status": dict(sorted(collections.Counter(r["mapping"]["record"]["status"] for r in accepted).items())),
              "accepted_with_september_pair_corroboration": 0,
              "instruction_xrefs_by_build": {b: sum(r["build"] == b for r in refs) for b in BUILDS},
              "data_pointer_xrefs_by_build": {b: sum(r["build"] == b for r in pointers) for b in BUILDS},
              "sources_by_kind": dict(sorted(collections.Counter(r["kind"] for r in pins["sources"]).items())),
              "anchors_by_category": {c: sum(c in a["categories"] for a in anchors) for c in CLASSES},
              "anchors_by_source": dict(sorted(collections.Counter(source for a in anchors for source in {p["source"] for p in a["provenance"]}).items())),
              "associations_by_build": {b: sum(r["build"] == b for r in associations) for b in BUILDS[:2]},
              "joins_by_mapping_status": dict(sorted(collections.Counter(r["mapping"]["record"]["status"] for r in associations if r["mapping"]).items())),
              "contradictory_associations": sum(bool(r["contradictions"]) for r in associations),
              "mapping_review_records": len(mapping_review),
              "graph_records": len(graph),
              "scalar_data_candidates": len(globals_found),
              "accepted_by_subsystem": dict(sorted(collections.Counter(anchor_by_id[r["anchor_id"]]["subsystem"] for r in accepted).items())),
              "anchors_by_subsystem": dict(sorted(collections.Counter(a["subsystem"] for a in anchors).items())),
              "problem_set_availability": {key: len(rows) for key, rows in sets.items()},
              "accepted_problem_intersections": {key: sum(any(i["set"] == key for i in r["intersections"]) for r in accepted) for key in sets},
              "all_problem_intersections": {key: sum(any(i["set"] == key for i in r["intersections"]) for r in associations) for key in sets}}
    payloads = {"inventory": {"anchors": anchors, "external_line_audit": external_lines}, "xrefs": {"references": refs, "data_pointers": pointers},
                "registrations": {"records": registrations}, "index": {"records": associations},
                "accepted": {"records": accepted}, "review": {"records": queue, "availability": availability, "problem_sets": sorted(sets)},
                "mapping-review": {"records": mapping_review}, "graph": {"records": graph},
                "globals": {"records": globals_found}}
    validate_family(payloads, documents["prototype-correspondence-accepted.json"]["records"], counts)
    bindings = []
    for kind, payload in sorted(payloads.items()):
        document = envelope(kind, source_pins_sha256=sha(ROOT / PIN_FILE), **payload)
        path = OUT / ("semantic-" + kind + ".json")
        write(path, document, check)
        bindings.append({"path": path.as_posix(), "size": len(data_bytes(document)), "sha256": hashlib.sha256(data_bytes(document)).hexdigest().upper()})
    tool_paths = [Path("tools/Fable2PrototypeSemantics.py"), Path("tools/Fable2SemanticNative.py"),
                  Path("tools/schemas/fable2-prototype-semantics-v1.schema.json"), Path("tests/test_fable2_prototype_semantics.py"),
                  Path("tools/Verify-Fable2PrototypeSemantics.ps1")]
    summary = envelope("validation", source_pins_sha256=sha(ROOT / PIN_FILE), counts=counts, artifacts=bindings,
                       implementation=[identity(path, kind="phase2b-implementation") for path in tool_paths],
                       policies={"canonical_adoption": False, "graph_depth": 1, "graph_fanout": 8,
                                 "review_limit_per_stratum": 3, "scores_create_acceptance": False,
                                 "september": "native-xrefs-only-no-exhaustive-closed-secondary-pairs",
                                 "july": "exact-image-alias-control-only"})
    report = report_text(summary, payloads)
    summary["report"] = {"path": (DOC / "report.md").as_posix(), "size": len(report.encode("utf-8")),
                         "sha256": hashlib.sha256(report.encode("utf-8")).hexdigest().upper()}
    write_text(DOC / "report.md", report, check)
    write(DOC / "evidence/semantic-validation.json", summary, check)
    audit(pins)
    print(json.dumps(counts, sort_keys=True, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("bind", "generate", "verify"))
    args = parser.parse_args()
    if args.command == "bind":
        bind()
    else:
        generate(check=args.command == "verify")


if __name__ == "__main__":
    main()
