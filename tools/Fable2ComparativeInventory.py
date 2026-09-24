#!/usr/bin/env python3
"""Report-only external manifest census. Candidate matches never authorize names/ranges."""
from __future__ import annotations

import argparse
import bisect
import collections
import csv
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import tomllib

ROOT = Path(__file__).resolve().parents[1]
BASE = 0x82000000
BASE_IMAGE = "B8F294DDAE3DA4A01DE455F5003CD1452D7C838EDC3DE1C166F3CAB9008B77A8"
TU1_IMAGE = "BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00"


def hx(value: int) -> str:
    return f"0x{value:08X}"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def load_image(directory: Path, expected: str) -> tuple[bytes, dict[int, bytes]]:
    data = (directory / "image.bin").read_bytes()
    if digest(data) != expected:
        raise ValueError(f"wrong image identity: {directory}")
    with (directory / "sections.tsv").open() as stream:
        section = next(s for s in csv.DictReader(stream, delimiter="\t") if s["name"] == ".pdata")
    offset, size = int(section["address"]) - BASE, int(section["size"])
    if offset < 0 or offset + size > len(data) or size % 8:
        raise ValueError("invalid .pdata extent")
    functions = {}
    for address, unwind in struct.iter_unpack(">II", data[offset:offset + size]):
        length = ((unwind >> 8) & 0x3FFFFF) * 4
        start = address - BASE
        if not length or start < 0 or start + length > len(data) or address in functions:
            raise ValueError("invalid/duplicate .pdata function")
        functions[address] = data[start:start + length]
    return data, functions


def branch_key(code: bytes) -> bytes:
    # Candidate generation only: masking branch displacements is NOT CFG proof.
    words = struct.iter_unpack(">I", code)
    return b"".join(struct.pack(">I", w & 0xFC000003 if w >> 26 == 18 else
                                w & 0xFFFF0003 if w >> 26 == 16 else w) for (w,) in words)


def match_index(functions: dict[int, bytes], normalize=False) -> dict[bytes, list[int]]:
    result = collections.defaultdict(list)
    for address, code in functions.items():
        result[branch_key(code) if normalize else code].append(address)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--base-snapshot", type=Path, required=True)
    parser.add_argument("--tu1-snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        head = subprocess.check_output(["git", "-C", str(args.external), "rev-parse", "HEAD"], text=True).strip()
        if head != args.commit or subprocess.check_output(
                ["git", "-C", str(args.external), "status", "--porcelain=v1"], text=True).strip():
            raise ValueError("external checkout must be clean and match the pinned commit")
        manifest_path = args.external / "fable_2_manifest.toml"
        manifest_text = manifest_path.read_text(encoding="utf-8")
        external = tomllib.loads(manifest_text)["entrypoint"]
        entries = external["functions"]
        current = tomllib.loads((ROOT / "fable2_manifest.toml").read_text())["entrypoint"]["functions"]
        base_image, base_functions = load_image(args.base_snapshot, BASE_IMAGE)
        _, target_functions = load_image(args.tu1_snapshot, TU1_IMAGE)
        raw, normalized = match_index(target_functions), match_index(target_functions, True)
        base_raw, base_norm = match_index(base_functions), match_index(base_functions, True)
        closure_root = ROOT / "out/analysis" / TU1_IMAGE
        closure = json.loads((closure_root / "entrypoint-closure.json").read_text())
        jumps = json.loads((closure_root / "jump-table-recovery.json").read_text())
        ranges = {int(f["range"]["start"], 16): f["range"] for f in closure["function_ranges"]}
        generated = {int(x, 16) for x in re.findall(
            r"\{\s*0x([0-9A-Fa-f]{8}),", (ROOT / "generated/default/fable2_init.cpp").read_text())}
        unresolved_records = [s for s in jumps["indirect_sites"]
                              if s["uses_ctr"] and not s["link"] and s["selected_table"] is None]
        unresolved = {int(s["site"], 16): s for s in unresolved_records}
        mappings = {}
        for address, code in base_functions.items():
            choices = raw.get(code, [])
            if len(choices) == 1 and len(base_raw[code]) == 1:
                mappings[address] = (choices[0], "reciprocal-unique-raw-candidate")
            else:
                key = branch_key(code)
                choices = normalized.get(key, [])
                if len(choices) == 1 and len(base_norm[key]) == 1:
                    mappings[address] = (choices[0], "reciprocal-unique-branch-candidate")
        line_map = {match.group(1).upper(): i for i, line in enumerate(manifest_text.splitlines(), 1)
                    if (match := re.match(r'\[entrypoint.functions."(0x[0-9A-Fa-f]+)"\]', line))}
        rows, boundaries = [], []
        for address, entry in sorted(entries.items(), key=lambda x: int(x[0], 16)):
            start = int(address, 16)
            code = base_functions.get(start)
            kind, choices = "no-pdata-body", []
            if code:
                choices, kind = raw.get(code, []), "raw-exact"
                if not choices:
                    choices, kind = normalized.get(branch_key(code), []), "branch-normalized"
                if not choices:
                    kind = "unmatched"
            rows.append({"external_commit": head, "external_file": "fable_2_manifest.toml",
                         "external_line": line_map.get(address.upper()), "external_address": hx(start),
                         "external_symbol": entry.get("name", ""),
                         "explicit_size": hx(entry["size"]) if "size" in entry else "",
                         "base_pdata_size": hx(len(code)) if code else "",
                         "candidate_kind": kind, "candidate_addresses": ";".join(map(hx, choices)),
                         "reciprocal_unique_candidate": hx(mappings[start][0]) if start in mappings else "",
                         "candidate_registered": ";".join(hx(a) for a in choices if a in generated),
                         "status": "REVISION_MISMATCH", "confidence": "HYPOTHESIS",
                         "action": "Review rebased body/control/data references; do not propagate name or boundary."})
            if "size" in entry:
                boundaries.append({"external_address": hx(start), "external_size": hx(entry["size"]),
                                   "base_pdata_size": hx(len(code)) if code else None,
                                   "base_pdata_agrees": len(code) == entry["size"] if code else None,
                                   "same_address_tu1_range": ranges.get(start),
                                   "same_address_our_override": current.get(hx(start)),
                                   "status": "REVISION_MISMATCH"})
        tables = tomllib.loads((args.external / "fable2_switch_tables.toml").read_text())["switch_tables"]
        relative_tables = collections.defaultdict(list)
        for site in jumps["indirect_sites"]:
            table = site["selected_table"]
            if table:
                dispatch = int(site["site"], 16)
                key = tuple(int(target, 16) - dispatch for target in table["targets"])
                relative_tables[key].append(site["site"])
        table_shapes = []
        for table in tables:
            hint = table["address"]
            # Hints in this source name the materialization sequence, not bctr.
            dispatches = [hint + offset for offset in range(0, 32, 4)
                          if base_image[hint + offset - BASE:hint + offset - BASE + 4]
                          == bytes.fromhex("4e800420")]
            dispatch = dispatches[0] if len(dispatches) == 1 else None
            choices = relative_tables.get(tuple(label - dispatch for label in table["labels"]), []) if dispatch else []
            table_shapes.append({"external_hint_address": hx(hint),
                                 "base_bctr_within_32_bytes": hx(dispatch) if dispatch else None,
                                 "case_count": len(table["labels"]),
                                 "already_recovered_shape_candidates": choices,
                                 "status": "UNVERIFIED",
                                 "limitation": "Relative label shape alone is not revision rebasing or ownership proof."})
        starts = sorted(base_functions)
        projections = []
        for table in tables:
            site = table["address"]
            i = bisect.bisect_right(starts, site) - 1
            owner = starts[i] if i >= 0 else None
            if owner is None or site >= owner + len(base_functions[owner]) or owner not in mappings:
                continue
            target, kind = mappings[owner]
            mapped_site = target + site - owner
            projections.append({"external_dispatch": hx(site), "base_owner": hx(owner),
                                "tu1_owner_candidate": hx(target), "tu1_dispatch_candidate": hx(mapped_site),
                                "candidate_method": kind, "intersects_unresolved": mapped_site in unresolved,
                                "status": "UNVERIFIED", "labels_not_imported": True})
        ext_starts = {int(a, 16) for a in entries}
        report = {"schema_version": 1, "external_repository": "himdo/Fable-2-Recomp",
                  "external_commit": head, "base_image_sha256": BASE_IMAGE, "tu1_image_sha256": TU1_IMAGE,
                  "scope": "Exhaustive manifest census; candidates are not accepted semantic mappings or function proposals.",
                  "counts": {"external_named_entries": len(entries), "external_explicit_sizes": len(boundaries),
                             "external_generic_ProcessAndProcess_names": sum(e.get("name", "").startswith("ProcessAndProcess") for e in entries.values()),
                             "external_manual_tables": len(tables), "external_midasm_hooks": len(external["midasm_hook"]),
                             "base_pdata": len(base_functions), "tu1_pdata": len(target_functions),
                             "our_explicit_entries": len(current), "our_effective_registrations": len(generated),
                             "candidate_kinds": dict(collections.Counter(row["candidate_kind"] for row in rows)),
                             "unique_target_candidates": sum(len(row["candidate_addresses"].split(";")) == 1 and bool(row["candidate_addresses"]) for row in rows),
                             "reciprocal_unique_candidates": sum(bool(row["reciprocal_unique_candidate"]) for row in rows),
                             "reciprocal_unique_candidates_already_registered": sum(
                                 bool(row["reciprocal_unique_candidate"]) and
                                 int(row["reciprocal_unique_candidate"], 16) in generated for row in rows),
                             "explicit_sizes_with_base_pdata_start": sum(r["base_pdata_size"] is not None for r in boundaries),
                             "explicit_sizes_disagreeing_with_base_pdata": sum(r["base_pdata_agrees"] is False for r in boundaries),
                             "raw_address_coincidences_with_registrations": len(ext_starts & generated),
                             "external_raw_addresses_absent_from_our_registrations": len(ext_starts - generated),
                             "our_registrations_absent_from_external_manifest_raw_addresses": len(generated - ext_starts),
                             "current_unresolved_nonlink_ctr_records": len(unresolved_records),
                             "current_unresolved_nonlink_ctr_distinct_addresses": len(unresolved),
                             "external_hints_with_one_nearby_bctr": sum(bool(t["base_bctr_within_32_bytes"]) for t in table_shapes),
                             "external_tables_with_recovered_relative_shape_candidate": sum(bool(t["already_recovered_shape_candidates"]) for t in table_shapes),
                             "table_dispatch_candidate_projections": len(projections),
                             "table_projections_into_unresolved": sum(p["intersects_unresolved"] for p in projections)},
                  "raw_address_counts_are_not_coverage_differences": True,
                  "boundary_review": boundaries, "switch_candidate_projections": projections,
                  "switch_relative_shape_candidates": table_shapes,
                  "unresolved_sites_with_named_owner_candidate": [
                      {"external_owner": hx(a), "external_name": entries.get(hx(a), {}).get("name"),
                       "tu1_owner_candidate": hx(target), "site": s["site"], "status": "UNVERIFIED"}
                      for a, (target, _) in mappings.items() if hx(a) in entries
                      for s in unresolved_records if int(s["owner_address"], 16) == target],
                  "inputs": {str(p): digest(p.read_bytes()) for p in [manifest_path,
                     args.external / "fable2_switch_tables.toml", closure_root / "entrypoint-closure.json",
                     closure_root / "jump-table-recovery.json", ROOT / "generated/default/fable2_init.cpp"]}}
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "inventory.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        with (args.output / "external-functions.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        print(json.dumps(report["counts"], indent=2))
        return 0
    except (OSError, ValueError, KeyError, StopIteration, subprocess.CalledProcessError) as error:
        print(f"FAIL: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
