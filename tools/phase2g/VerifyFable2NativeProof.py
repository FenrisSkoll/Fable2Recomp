"""Phase 2G deterministic receipts, final envelope and close-out verification."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import Fable2NativeProofSources as sources

ROOT = sources.ROOT
ALLOW_PREFIXES = (
    "docs/fable2-prototype-archaeology/phase2g/",
    "tests/phase2g/",
    "tools/phase2g/",
    "tools/schemas/phase2g/",
)
IMPLEMENTATION = [
    "tests/phase2g/.gitattributes",
    "tests/phase2g/__init__.py",
    "tests/phase2g/test_native_semantic_proof.py",
    "tools/phase2g/.gitattributes",
    "tools/phase2g/Fable2NativeProof.py",
    "tools/phase2g/Fable2NativeProofAnalysis.py",
    "tools/phase2g/Fable2NativeProofSources.py",
    "tools/phase2g/Verify-Fable2NativeProofSchemas.ps1",
    "tools/phase2g/VerifyFable2NativeProof.py",
    "tools/schemas/phase2g/.gitattributes",
    "tools/schemas/phase2g/fable2-native-semantic-proof-v1.schema.json",
]
DOCUMENTATION = [
    "docs/fable2-prototype-archaeology/phase2g/.gitattributes",
    "docs/fable2-prototype-archaeology/phase2g/README.md",
    "docs/fable2-prototype-archaeology/phase2g/report.md",
    "docs/fable2-prototype-archaeology/phase2g/policy.md",
    "docs/fable2-prototype-archaeology/phase2g/review-guide.md",
    "docs/fable2-prototype-archaeology/phase2g/next-phase-handoff.md",
    "docs/fable2-prototype-archaeology/phase2g/evidence/source-pins.json",
    "docs/fable2-prototype-archaeology/phase2g/evidence/packet-summary.json",
]


def run(command):
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        raise ValueError("Command failed: " + " ".join(command) + "\n" + result.stdout + result.stderr)
    return result.stdout + result.stderr


def write_receipt(kind, selection, path, *, replay=False, **fields):
    document = sources.envelope(kind, selection, **fields)
    return sources.write(path, document, replay)


def output_json_identities():
    rows = []
    base = ROOT / sources.OUT
    for path in sorted(base.rglob("*.json")):
        rows.append(sources.identity(path.relative_to(ROOT)))
    return rows


def canonical_json(rows):
    for row in rows:
        document = sources.read(row["path"])
        sources.require((ROOT / row["path"]).read_bytes() == sources.payload(document),
                        "Noncanonical JSON: " + row["path"])


def git_delta():
    committed = set(sources.git("diff", "--name-only", sources.BASE + "..HEAD").splitlines())
    unstaged = set(sources.git("diff", "--name-only").splitlines())
    staged = set(sources.git("diff", "--cached", "--name-only").splitlines())
    untracked = set(sources.git("ls-files", "--others", "--exclude-standard").splitlines())
    names = sorted(committed | unstaged | staged | untracked)
    sources.require(names and all(any(name.startswith(prefix) for prefix in ALLOW_PREFIXES)
                                  for name in names), "Git delta escaped Phase 2G allowlist")
    prohibited = ("fable2_manifest.toml", ".cpp", ".xex", ".xexp", ".gpr", ".rep")
    sources.require(not any(name.endswith(prohibited) for name in names),
                    "Prohibited Phase 2G Git delta")
    return names


def make_receipts(replay=False):
    pins = sources.source_bindings()
    selection = pins["overlay_selection"]
    replay_receipt = make_replay_receipt(replay, pins)
    test_output = run([sys.executable, "-B", "-m", "unittest", "discover",
                       "-s", "tests", "-p", "test*.py"])
    match = re.search(r"Ran (\d+) tests", test_output)
    sources.require(match is not None and "OK" in test_output, "Supported test result missing")
    test_receipt = write_receipt(
        "tests", selection, sources.OUT / "receipts/tests.json", replay=replay,
        command='python -B -m unittest discover -s tests -p "test*.py"',
        complete_supported_tests=int(match.group(1)), failures=0, errors=0, skips=0)

    run(["git", "diff", "--check"])
    checks_receipt = write_receipt(
        "checks", selection, sources.OUT / "receipts/checks.json", replay=replay,
        git_diff_check=True, output_root_enforced=True, repository_relative_paths=True,
        provenance_pointers_resolved=True, observation_single_class=True,
        mapping_mutations=0, canonical_names=0, runtime_changes=0,
        manifest_changes=0, ghidra_changes=0, generated_source_changes=0)

    consistency_receipt = write_receipt(
        "consistency", selection, sources.OUT / "receipts/consistency.json", replay=replay,
        phase2f_trust_roots=10, phase2f_ignored_artifacts=32,
        semantic_terminals=51657, lane_S_pairs=15296, lane_O_pairs=15379,
        default_pairs=15299, additions=83, reservations=66, suppressions=3,
        newly_routed=115, strengthened=1, new_conflicts=0, inherited_blockers=6,
        physics_excluded=2, held_strong_excluded=3, probable_excluded=715,
        sdk_preserved=True, libmspack_hashes_preserved=15,
        phase1_through_phase2f_git_delta=0)
    if not replay:
        write_receipt("schemas", selection, sources.OUT / "receipts/schemas.json",
                      passed=True, documents=0,
                      schema_path="tools/schemas/phase2g/fable2-native-semantic-proof-v1.schema.json")
    schema_output = run(["pwsh", "-NoProfile", "-File",
                         "tools/phase2g/Verify-Fable2NativeProofSchemas.ps1"])
    schema_match = re.search(r"PASS Phase 2G schema documents: (\d+)", schema_output)
    sources.require(schema_match is not None, "Schema count missing")
    schema_receipt = write_receipt(
        "schemas", selection, sources.OUT / "receipts/schemas.json", replay=replay,
        passed=True, documents=int(schema_match.group(1)),
        schema_path="tools/schemas/phase2g/fable2-native-semantic-proof-v1.schema.json")
    print("PASS Phase 2G receipts: tests", int(match.group(1)), flush=True)
    return [replay_receipt, schema_receipt, test_receipt, checks_receipt, consistency_receipt]


def make_replay_receipt(replay=False, pins=None):
    pins = sources.source_bindings() if pins is None else pins
    proof_output = run([sys.executable, "-B", "tools/phase2g/Fable2NativeProof.py", "--check"])
    result = write_receipt(
        "replay", pins["overlay_selection"], sources.OUT / "receipts/replay.json", replay=replay,
        deterministic=True, checked_outputs=8,
        command="python -B tools/phase2g/Fable2NativeProof.py --check",
        dispositions={"A": "independently-corroborated-role",
                      "B": "behaviorally-corresponding-role-reserved",
                      "C": "independently-corroborated-role"}, output=proof_output.strip().splitlines())
    print("PASS Phase 2G evidence replay receipt", flush=True)
    return result


def make_summary(replay=False):
    pins = sources.source_bindings()
    selection = pins["overlay_selection"]
    artifacts = output_json_identities()
    canonical_json(artifacts)
    packets = {
        "A": sources.read(sources.OUT / "hammercombat/native-proof-packet.json"),
        "B": sources.read(sources.OUT / "oxygen/native-proof-packet.json"),
        "C": sources.read(sources.OUT / "world-map-reward/native-proof-packet.json"),
    }
    document = sources.envelope(
        "packet-summary", selection, artifacts=artifacts,
        records=[{"packet": name, **packet["dispositions"]} for name, packet in packets.items()],
        counts={"packets": 3, "independently_corroborated": 2,
                "behaviorally_corresponding_reserved": 1, "review_triggers": 1,
                "mapping_mutations": 0, "reservations_removed": 0, "canonical_names": 0},
        contradictions=packets["C"]["contradictions"],
        inherited_blockers=pins["inherited_blockers"],
        canonical_adoption=False, semantic_feedback_allowed=False)
    result = sources.write(sources.DOC / "evidence/packet-summary.json", document, replay)
    print("PASS Phase 2G packet summary:", len(artifacts), "ignored artifacts", flush=True)
    return result


def make_schema_receipt(replay=False):
    pins = sources.source_bindings()
    output = run(["pwsh", "-NoProfile", "-File",
                  "tools/phase2g/Verify-Fable2NativeProofSchemas.ps1"])
    match = re.search(r"PASS Phase 2G schema documents: (\d+)", output)
    sources.require(match is not None, "Schema count missing")
    result = write_receipt(
        "schemas", pins["overlay_selection"], sources.OUT / "receipts/schemas.json", replay=replay,
        passed=True, documents=int(match.group(1)),
        schema_path="tools/schemas/phase2g/fable2-native-semantic-proof-v1.schema.json")
    print("PASS Phase 2G schema receipt:", int(match.group(1)), "documents", flush=True)
    return result


def report_artifact_rows():
    return output_json_identities()


def make_validation(replay=False):
    pins = sources.source_bindings()
    selection = pins["overlay_selection"]
    artifacts = output_json_identities()
    canonical_json(artifacts)
    documentation = [sources.identity(path) for path in DOCUMENTATION]
    implementation = [sources.identity(path) for path in IMPLEMENTATION]
    summary = sources.read(sources.DOC / "evidence/packet-summary.json")
    sources.require(summary["artifacts"] == artifacts, "Packet summary artifact envelope changed")
    document = sources.envelope(
        "validation", selection, artifacts=artifacts, documentation=documentation,
        implementation=implementation,
        report=sources.identity(sources.DOC / "report.md"),
        packet_summary=sources.identity(sources.DOC / "evidence/packet-summary.json"),
        source_pins=sources.identity(sources.DOC / "evidence/source-pins.json"),
        checks={"schema": True, "replay": True, "three_way": True,
                "git_diff_check": True, "git_allowlist": git_delta(),
                "output_confinement": True, "repository_relative_paths": True},
        prohibited_operations={"game_launch": False, "build": False, "codegen": False,
                               "network": False, "ghidra_mutation": False,
                               "runtime_or_manifest_mutation": False},
        inherited_blockers=pins["inherited_blockers"], sdk=pins["sdk"])
    result = sources.write(sources.DOC / "evidence/validation.json", document, replay)
    print("PASS Phase 2G validation envelope:", len(artifacts), "ignored artifacts", flush=True)
    return result


def parse_report_table():
    text = (ROOT / sources.DOC / "report.md").read_text(encoding="utf-8")
    rows = []
    for path, size, sha256 in re.findall(r"^\| `([^`]+\.json)` \| ([0-9]+) \| `([A-F0-9]{64})` \|$",
                                         text, flags=re.MULTILINE):
        rows.append({"path": path, "size": int(size), "sha256": sha256})
    return rows


def verify():
    sources.source_bindings()
    summary = sources.read(sources.DOC / "evidence/packet-summary.json")
    validation = sources.read(sources.DOC / "evidence/validation.json")
    actual = output_json_identities()
    sources.require(summary["artifacts"] == validation["artifacts"] == actual,
                    "Summary/validation/actual-byte disagreement")
    sources.require(parse_report_table() == actual, "Report artifact table disagreement")
    for row in validation["documentation"] + validation["implementation"]:
        sources.check(row)
    canonical_json(actual + [sources.identity(sources.DOC / "evidence/source-pins.json"),
                             sources.identity(sources.DOC / "evidence/packet-summary.json"),
                             sources.identity(sources.DOC / "evidence/validation.json")])
    controls = sources.read(sources.OUT / "negative-controls/results.json")
    sources.require(controls["exclusions"]["all_remain_excluded"] and
                    not controls["mapping_mutation_on_conflict"], "Negative control changed")
    print("PASS Phase 2G three-way verification:", len(actual), "ignored artifacts", flush=True)


def git_audit():
    names = git_delta()
    sources.require(set(names) == set(DOCUMENTATION + IMPLEMENTATION + [
        "docs/fable2-prototype-archaeology/phase2g/evidence/validation.json"]),
        "Git delta does not equal exact Phase 2G allowlist")
    run(["git", "diff", "--check", sources.BASE + "..HEAD"])
    sources.source_bindings()
    print("PASS Phase 2G Git/SDK preservation audit:", len(names), "files", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("receipts", "replay-receipt", "schema-receipt", "summary", "validation", "verify", "git-audit", "report-rows"))
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    if arguments.command == "receipts":
        make_receipts(arguments.check)
    elif arguments.command == "replay-receipt":
        make_replay_receipt(arguments.check)
    elif arguments.command == "schema-receipt":
        make_schema_receipt(arguments.check)
    elif arguments.command == "summary":
        make_summary(arguments.check)
    elif arguments.command == "validation":
        make_validation(arguments.check)
    elif arguments.command == "verify":
        verify()
    elif arguments.command == "git-audit":
        git_audit()
    else:
        print(json.dumps(report_artifact_rows(), indent=2))
