#!/usr/bin/env python3
"""Corroborate the Phase 4 P1/P2 ownership queue; never modify guest functions.

Inputs are the supported Phase 4 outputs, exact-image Ghidra map, generated
source and a private guest-memory snapshot. Only identity/address/provenance
metadata is emitted. --check regenerates in memory and compares every byte.
"""
from __future__ import annotations

import argparse
import bisect
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

import Fable2FunctionMap as fm
import Fable2IndirectTargets as p4

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.0.0"
POPULATIONS = {"existing_function_internal_entry", "known_jump_table_case"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def addr(value):
    return int(value, 16)


def hx(value):
    return f"0x{value:08X}"


def digest(data):
    return hashlib.sha256(data).hexdigest().upper()


def member(address, ranges):
    return any(addr(r["start"]) <= address < addr(r["end"]) for r in ranges)


def direct_branch(site, word):
    if word >> 26 != 18:
        return None
    displacement = word & 0x03FFFFFC
    if displacement & 0x02000000:
        displacement -= 0x04000000
    return ((0 if word & 2 else site) + displacement) & 0xFFFFFFFF


def conditional_lr_return(word):
    return (word >> 26 == 19 and (word >> 1) & 1023 == 16
            and not word & 1 and ((word >> 21) & 0x14) != 0x14)


def decode_table(table, read):
    """Independently decode selected table storage, not its emitted targets."""
    width = table["element_width"]
    require(width in (1, 2, 4), "unsupported table element width")
    base = addr(table["table_address"])
    require(table["storage_size"] == hx(table["case_count"] * width),
            "table storage size/count mismatch")
    result = []
    for index in range(table["case_count"]):
        value = int.from_bytes(read(base + index * width, width), "big",
                               signed=table["element_signed"])
        if table["kind"] == "absolute_pointer":
            target = value
        else:
            require(table["kind"] == "relative_offset", "unsupported table encoding")
            target = (addr(table["anchor_address"]) + value * table["target_scale"]) & 0xFFFFFFFF
        result.append(hx(target))
    require(result == table["targets"], "table bytes disagree with recovered destinations")
    return result


def generated_index(wanted):
    result = {}
    pattern = re.compile(r"^DEFINE_REX_FUNC\((sub_[0-9A-F]{8}), (0x[0-9A-F]{8}),")
    for path in sorted((ROOT / "generated/default").glob("fable2_recomp.*.cpp")):
        lines = path.read_text(encoding="utf-8").splitlines()
        active = None
        for number, line in enumerate(lines, 1):
            match = pattern.match(line)
            if match:
                active = addr(match[2]) if addr(match[2]) in wanted else None
                if active is not None:
                    require(active not in result, f"duplicate generated function {hx(active)}")
                    result[active] = {"file": path.relative_to(ROOT).as_posix(),
                                      "function": match[1], "line": number,
                                      "lines": [], "file_sha256": p4.sha256_file(path)}
            if active is not None:
                result[active]["lines"].append(line)
    require(wanted <= result.keys(), "selected owner is absent from generated source")
    return result


def build(args):
    directory = args.phase4_directory
    queue_path = directory / "phase4-static-ownership-follow-up.json"
    plan_path = directory / "fable2-indirect-targets.import-plan.json"
    summary_path = directory / "xenia-indirect-targets.summary.json"
    contract = fm.load_contract(p4.DEFAULT_EVIDENCE)
    expected = contract["expected_image_identity"]
    queue = fm.read_json(queue_path)
    plan = p4.read_plan(plan_path)
    summary = p4.read_summary(summary_path, expected)
    closure = fm.read_json(args.closure)
    fmap = fm.validate_map(fm.read_json(args.ghidra_map))
    require(fm.assess_identity(fmap, contract)["state"] == "exact_image_match",
            "Ghidra map is not an exact image match")
    require(closure["image_identity"]["patched_image_sha256"] == expected["patched_image_sha256"],
            "closure image mismatch")
    require(plan["inputs"]["closure"]["sha256"] == p4.sha256_file(args.closure), "stale closure")
    require(plan["inputs"]["summary"]["sha256"] == p4.sha256_file(summary_path), "stale summary")
    require(plan["inputs"]["manifest"]["sha256"] == p4.sha256_file(p4.DEFAULT_MANIFEST), "stale manifest")
    require(plan["inputs"]["shared_evidence"]["sha256"] == p4.sha256_file(p4.DEFAULT_EVIDENCE), "stale shared evidence")
    input_hashes = {r["role"]: r["sha256"] for r in queue["inputs"]}
    require(input_hashes["import_plan"] == p4.sha256_file(plan_path), "queue/plan mismatch")
    require(input_hashes["merged_summary"] == p4.sha256_file(summary_path), "queue/summary mismatch")
    require(input_hashes["entrypoint_closure"] == p4.sha256_file(args.closure), "queue/closure mismatch")
    run = queue["scope"]["contributing_run_id"]
    p4.validate_static_ownership_follow_up(queue)
    baseline_runs = set(p4.follow_up_baseline_ids(queue["scope"], queue["schema"]["version"]))
    grouped, _ = p4.group_target_observations(summary)
    expected_queue = {t for t, pairs in grouped.items()
                      if any(run in p["observed_runs"] for p in pairs)
                      and not any(baseline_runs.intersection(p["observed_runs"]) for p in pairs)}
    require(len(queue["targets"]) == len({r["target"] for r in queue["targets"]}), "duplicate queue target")
    require(expected_queue == {addr(r["target"]) for r in queue["targets"]}, "queue omits or adds targets")
    selected = [r for r in queue["targets"] if r["classification"] in POPULATIONS]
    selected.sort(key=lambda r: (r["priority"]["rank"], r["target"]))
    planned = {r["target"]: r for r in plan["targets"]}
    for row in selected:
        require(planned[row["target"]]["classification"] == row["classification"], "queue category mismatch")

    image = args.guest_snapshot.read_bytes()

    def read(address, size):
        offset = address - args.guest_base
        require(0 <= offset and offset + size <= len(image), f"snapshot does not cover {hx(address)}")
        return image[offset:offset + size]

    def word(address):
        return struct.unpack(">I", read(address, 4))[0]

    checked_sections = []
    pdata_block = next(b for b in fmap["identity_evidence"]["memory_blocks"] if b["name"] == ".pdata")
    for section in expected["executable_sections"] + [dict(name=".pdata", **pdata_block["range"], sha256=pdata_block["sha256"])]:
        actual = digest(read(addr(section["start"]), addr(section["end"]) - addr(section["start"])))
        require(actual == section["sha256"], f"snapshot section hash mismatch: {section['name']}")
        checked_sections.append({k: section[k] for k in ("name", "start", "end", "sha256")})

    pdata = {}
    for record in range(addr(pdata_block["range"]["start"]), addr(pdata_block["range"]["end"]), 8):
        entry, packed = struct.unpack(">II", read(record, 8))
        length = ((packed >> 8) & 0x3FFFFF) * 4
        require(entry not in pdata, "duplicate pdata entry")
        pdata[entry] = {"record": hx(record), "start": hx(entry), "end": hx(entry + length),
                        "size": hx(length), "prolog_instruction_count": packed & 255,
                        "exception_flag": bool(packed & 0x80000000)}
    require(set(pdata) == {addr(r["entry"]) for r in fmap["pdata_functions"]}, "pdata/map entry mismatch")
    ranges = {addr(r["range"]["start"]): r for r in closure["function_ranges"]}
    require(len(ranges) == len(closure["function_ranges"]), "duplicate recovered owner")
    starts = sorted(ranges)

    def owner(address):
        index = bisect.bisect_right(starts, address) - 1
        require(index >= 0, f"unowned address {hx(address)}")
        start = starts[index]
        require(member(address, ranges[start]["basic_blocks"]), f"address outside exact owner body {hx(address)}")
        return start

    maps = {addr(r["entry"]): r for r in fmap["functions"]}
    candidates = {addr(r["address"]): r for r in closure["candidates"]}
    sites = {addr(r["site"]): r for r in closure["jump_table_recovery"]["indirect_sites"]}
    registrations = p4.load_generated_registrations(p4.DEFAULT_GENERATED_INIT)
    wanted = {addr(r["owner"]["address"]) for r in selected}
    wanted.update(owner(addr(s["source"])) for r in selected for s in r["observed_sources"])
    generated = generated_index(wanted)
    exact_refs = defaultdict(list)
    for edge in closure["direct_edges"]:
        exact_refs[addr(edge["target"])].append(edge)

    def location(entry):
        return {k: v for k, v in generated[entry].items() if k != "lines"}

    def assembly(address):
        result = subprocess.run([str(args.disassembler), str(args.guest_snapshot), hx(args.guest_base),
                                 hx(address), hx(address + 4)], capture_output=True, text=True, check=True)
        match = re.fullmatch(r"0x[0-9A-F]{8}: [0-9A-F]{8}  (.+)\s*", result.stdout.strip())
        require(match is not None, "disassembler output is malformed")
        return match[1]

    ledger = []
    dispatch_records = {}
    for row in selected:
        target = addr(row["target"])
        claimed = addr(row["owner"]["address"])
        current = ranges[claimed]
        body_owners = [hx(start) for start, r in ranges.items() if member(target, r["basic_blocks"])]
        require(body_owners == [hx(claimed)], f"overlapping/wrong target ownership {row['target']}")
        require(target not in registrations, "selected internal target already registered")
        boundary_conflicts = []
        if target in pdata or target in maps or exact_refs[target]:
            boundary_conflicts.append("independent_entry_or_direct_reference_requires_review")
        observations = grouped[target]
        observed_sources = sorted({(p["source"], p["branch_kind"], p["link"]) for p in observations})
        require(observed_sources == sorted({(p["source"], p["branch_kind"], p["link"]) for p in row["observed_sources"]}),
                "queue source set differs from recorded population")
        checks = []
        unresolved = []
        case_membership = []
        for source_text, kind, link in observed_sources:
            source = addr(source_text)
            source_owner = owner(source)
            if row["classification"] == "existing_function_internal_entry":
                call = target - 4
                call_target = direct_branch(call, word(call))
                indirect_call = word(call) == 0x4E800421
                matches = [p for p in summary["pairs"] if p["source"] == hx(call)
                           and p["target"] == hx(source_owner) and p["branch_kind"] == "bctrl"
                           and p["link"] and run in p["observed_runs"]]
                valid = (kind == "bclr" and not link and conditional_lr_return(word(source))
                         and ((word(call) & 1 and call_target == source_owner) or (indirect_call and matches)))
                if not valid:
                    unresolved.append(f"call/conditional-return pairing not established for {source_text}")
                source_asm = assembly(source)
                # The native implementation already performs a C++ return; no
                # dispatcher registration at the continuation is necessary.
                callee_lines = generated[source_owner]["lines"]
                source_lines = [i for i, line in enumerate(callee_lines)
                                if source_asm == line.strip().removeprefix("// ")]
                require(source_lines,
                        f"return mnemonic absent from generated owner {source_text}")
                require(any("return;" in "\n".join(callee_lines[i + 1:i + 5]) for i in source_lines),
                        "generated conditional LR instruction does not return")
                caller_lines = generated[claimed]["lines"]
                marker = f"ctx.lr = {hx(target)};"
                require(any(marker in line for line in caller_lines), "generated call LR differs")
                checks.append({"source": source_text, "source_owner": hx(source_owner),
                               "source_instruction": source_asm, "source_generated": location(source_owner),
                               "call_site": hx(call), "call_instruction": assembly(call),
                               "call_target": hx(call_target) if call_target is not None else None,
                               "matching_indirect_call_observations": matches,
                               "lr_after_call": hx(target), "lr_value_observed_directly": False,
                               "lr_context_basis": "decoded_call_link_semantics_and_resolved_bclr_destination",
                               "generated_lr_assignment_lines": [generated[claimed]["line"] + i for i, line in enumerate(caller_lines) if marker in line],
                               "generated_return_mnemonic_lines": [generated[source_owner]["line"] + i for i in source_lines],
                               "pairing_established": bool(valid)})
            else:
                require(kind == "bctr" and not link and word(source) == 0x4E800420, "switch transfer mismatch")
                site = sites[source]
                table = site["selected_table"]
                require(table is not None and site["owner_address"] == hx(claimed), "dispatcher owner mismatch")
                decoded = decode_table(table, read)
                indices = [i for i, value in enumerate(decoded) if value == hx(target)]
                require(indices, "observed target absent from table")
                for instruction in table["instruction_evidence"]:
                    require(word(addr(instruction["address"])) == addr(instruction["raw_instruction"]),
                            "table control-flow instruction differs from TU1")
                valid_bounds = [b for b in site["dataflow"]["bound_candidates"] if b["rejection"] is None]
                require(valid_bounds or table["origin"] == "manual", "no accepted table bound proof")
                case_membership.append({"dispatcher": source_text, "table": table["table_address"],
                                        "indices": indices, "default_destination": table["default_target"] == hx(target)})
                dispatch_records[source_text] = {
                    k: v for k, v in table.items() if k not in ("raw_entries", "instruction_evidence", "targets")}
                dispatch_records[source_text].update({"decoded_destinations": decoded,
                    "dispatcher": source_text, "owner": hx(claimed),
                    "bound_proofs": valid_bounds, "index_transform_chain": site["dataflow"]["index_transform_chain"],
                    "target_expression": site["dataflow"]["target_expression"],
                    "instruction_evidence_addresses": sorted({i["address"] for i in table["instruction_evidence"]}),
                    "all_entries_and_evidence_instructions_match_tu1": True})
                require(any(f"goto loc_{target:08X}" in line for line in generated[claimed]["lines"]),
                        f"generated case branch missing {hx(target)}")

        tail_transfer = None
        classification = "return_continuation" if row["classification"] == "existing_function_internal_entry" else "switch_case_block"
        if case_membership:
            if any(m["default_destination"] for m in case_membership):
                classification = "switch_default_case"
            elif any(len(m["indices"]) > 1 for m in case_membership):
                classification = "shared_switch_case_body"
            destination = direct_branch(target, word(target))
            if destination is not None and not word(target) & 1 and not member(destination, current["basic_blocks"]):
                classification = "switch_case_tail_transfer"
                require(destination in ranges and destination in registrations,
                        "case tail destination lacks an existing registered function boundary")
                tail_transfer = {"site": hx(target), "destination": hx(destination),
                                 "destination_range": ranges[destination]["range"],
                                 "destination_pdata": pdata.get(destination),
                                 "instruction": assembly(target), "link": False,
                                 "case_itself_is_standalone_thunk": False}
        unresolved.extend(boundary_conflicts)
        if unresolved:
            classification = "unresolved"
        candidate = candidates.get(target)
        rationale = (f"{hx(target - 4)} establishes LR={hx(target)}; observed non-linking conditional LR returns resume this owner's call continuation."
                     if checks else "Observed non-linking dispatcher, exact decoded table entries, accepted bound proof and generated goto agree on this owner's internal case body.")
        ledger.append({"target": hx(target), "phase4_category": row["classification"],
                       "phase4_candidate_id": row["candidate_id"], "current_owner": {
                           "address": hx(claimed), "range": current["range"],
                           "body_ranges": current["basic_blocks"], "authority": current["authority"],
                           "pdata": pdata.get(claimed), "generated": location(claimed)},
                       "observations": observations, "return_checks": checks,
                       "case_membership": case_membership,
                       "immediate_tail_transfer": tail_transfer,
                       "boundary_evidence": {"exact_pdata_start": pdata.get(target),
                           "exact_ghidra_start": maps.get(target), "exact_direct_edges": exact_refs[target],
                           "ghidra_owner_entry_present": claimed in maps,
                           "ghidra_owner_body_contains_target": claimed in maps and member(target, maps[claimed]["body_ranges"]),
                           "unique_exact_body_owners": body_owners,
                           "closure_candidate": candidate},
                       "classification": classification,
                       "confidence": "UNRESOLVED" if unresolved else "CONFIRMED",
                       "action": "retain_owner_no_promotion",
                       "promotion_would_overlap_owner": True,
                       "independent_function_proven": False,
                       "runtime_entry_requirement": "none_new_proven_existing_call_return_or_switch_goto",
                       "rationale": rationale, "unresolved_questions": unresolved,
                       "xhigh_material": bool(unresolved)})

    counts = {"targets": len(ledger), "by_phase4_category": dict(sorted(Counter(r["phase4_category"] for r in ledger).items())),
              "by_classification": dict(sorted(Counter(r["classification"] for r in ledger).items())),
              "genuine_functions_or_thunks": 0, "corrected_owners": 0,
              "rejected_promotions": len(ledger), "manifest_changes": 0,
              "unresolved": sum(bool(r["unresolved_questions"]) for r in ledger),
              "dispatchers": len(dispatch_records)}
    inputs = {"phase4_queue": {"file": queue_path.name, "sha256": p4.sha256_file(queue_path), "report_id": queue["report_id"]},
              "import_plan": {"file": plan_path.name, "sha256": p4.sha256_file(plan_path), "plan_id": plan["plan_id"]},
              "summary": {"file": summary_path.name, "sha256": p4.sha256_file(summary_path)},
              "closure": {"file": args.closure.name, "sha256": p4.sha256_file(args.closure)},
              "ghidra_map": {"file": args.ghidra_map.name, "sha256": p4.sha256_file(args.ghidra_map)},
              "guest_snapshot": {"file": args.guest_snapshot.name, "guest_base": hx(args.guest_base),
                                 "verified_sections": checked_sections},
              "manifest": plan["inputs"]["manifest"], "shared_evidence": plan["inputs"]["shared_evidence"]}
    report = {"schema": {"name": "fable2-focused-ownership-ledger", "version": 1},
            "tool": {"name": "Fable2OwnershipCorroboration", "version": VERSION},
            "image_identity": expected, "inputs": inputs, "source_queue_counts": queue["counts"],
            "run_provenance": queue["run_provenance"], "counts": counts, "targets": ledger,
            "dispatchers": [dispatch_records[k] for k in sorted(dispatch_records)],
            "unresolved_shortlist": [{"target": r["target"], "questions": r["unresolved_questions"]}
                                      for r in ledger if r["xhigh_material"]],
            "safety": {"manifest_modified": False, "generated_code_modified": False,
                       "raw_runtime_observations_preserved": True, "automatic_promotion": False,
                       "runtime_correctness_claimed_from_compilation": False}}
    validate(report, {(r["target"], r["classification"]) for r in selected})
    return report


def validate(report, expected_targets=None):
    """Fail closed on coverage, ownership, provenance and disposition contradictions.

    This checks the evidence representation, not the private bytes; build()/--check
    additionally reconstruct the proof from those bytes and supported inputs.
    """
    require(report["schema"] == {"name": "fable2-focused-ownership-ledger", "version": 1}, "unsupported ledger schema")
    rows = report["targets"]
    actual = {(r["target"], r["phase4_category"]) for r in rows}
    require(len(rows) == len({r["target"] for r in rows}), "duplicate ledger target")
    if expected_targets is not None:
        require(actual == expected_targets, "ledger target/category coverage mismatch")
    counts = report["counts"]
    require(counts["targets"] == len(rows), "ledger total mismatch")
    require(counts["by_phase4_category"] == dict(Counter(r["phase4_category"] for r in rows)), "population counts mismatch")
    require(counts["by_classification"] == dict(Counter(r["classification"] for r in rows)), "classification counts mismatch")
    dispatchers = {d["dispatcher"]: d for d in report["dispatchers"]}
    require(len(dispatchers) == len(report["dispatchers"]) == counts["dispatchers"], "duplicate/miscounted dispatcher")
    used = set()
    for row in rows:
        target = addr(row["target"])
        owner = row["current_owner"]
        require(row["phase4_category"] in POPULATIONS, "unexpected population")
        require(addr(owner["address"]) == addr(owner["range"]["start"]) < target,
                "target is not internal to claimed owner")
        require(member(target, owner["body_ranges"]), "target outside exact body")
        require(row["boundary_evidence"]["unique_exact_body_owners"] == [owner["address"]], "overlapping owner evidence")
        require(row["action"] == "retain_owner_no_promotion" and not row["independent_function_proven"], "unsupported promotion")
        require(row["promotion_would_overlap_owner"], "internal promotion overlap not represented")
        require(row["observations"], "missing runtime provenance")
        require(all(p["target"] == row["target"] and p["observed_runs"] for p in row["observations"]), "observation target/run mismatch")
        require(bool(row["unresolved_questions"]) == (row["classification"] == "unresolved"), "unresolved disposition mismatch")
        require(row["confidence"] == ("UNRESOLVED" if row["unresolved_questions"] else "CONFIRMED"), "confidence mismatch")
        if not row["unresolved_questions"]:
            boundary = row["boundary_evidence"]
            require(not boundary["exact_pdata_start"] and not boundary["exact_ghidra_start"]
                    and not boundary["exact_direct_edges"], "independent boundary conflict was ignored")
        if row["classification"] == "return_continuation":
            require(row["phase4_category"] == "existing_function_internal_entry", "return population mismatch")
            require(row["return_checks"] and not row["case_membership"], "missing return proof")
            observed = {(p["source"], p["branch_kind"], p["link"]) for p in row["observations"]}
            require(observed == {(c["source"], "bclr", False) for c in row["return_checks"]}, "return sources omitted")
            for check in row["return_checks"]:
                require(check["pairing_established"] and addr(check["call_site"]) + 4 == target
                        and check["lr_after_call"] == row["target"], "invalid return pairing")
        elif row["classification"] != "unresolved":
            require(row["phase4_category"] == "known_jump_table_case", "switch population mismatch")
            require(row["case_membership"] and not row["return_checks"], "missing switch proof")
            require({(p["source"], p["branch_kind"], p["link"]) for p in row["observations"]}
                    == {(m["dispatcher"], "bctr", False) for m in row["case_membership"]}, "switch sources omitted")
            for membership in row["case_membership"]:
                used.add(membership["dispatcher"])
                table = dispatchers[membership["dispatcher"]]
                require(table["owner"] == owner["address"] and table["table_address"] == membership["table"], "wrong dispatcher owner/table")
                require(membership["indices"] == [i for i, t in enumerate(table["decoded_destinations"]) if t == row["target"]], "case membership mismatch")
                require(table["all_entries_and_evidence_instructions_match_tu1"], "unverified table")
                require(bool(membership["indices"]), "empty case membership")
                require(membership["default_destination"] == (table["default_target"] == row["target"]), "default case mismatch")
            require((row["classification"] == "switch_case_tail_transfer") == (row["immediate_tail_transfer"] is not None), "tail-transfer disposition mismatch")
            expected_class = "switch_case_block"
            if any(m["default_destination"] for m in row["case_membership"]):
                expected_class = "switch_default_case"
            elif any(len(m["indices"]) > 1 for m in row["case_membership"]):
                expected_class = "shared_switch_case_body"
            if row["immediate_tail_transfer"]:
                expected_class = "switch_case_tail_transfer"
                tail = row["immediate_tail_transfer"]
                require(tail["site"] == row["target"] and not tail["link"]
                        and tail["destination"] == tail["destination_range"]["start"]
                        and not member(addr(tail["destination"]), owner["body_ranges"])
                        and not tail["case_itself_is_standalone_thunk"], "invalid tail transfer")
            require(row["classification"] == expected_class, "switch subtype mismatch")
    require(used == set(dispatchers), "orphan dispatcher")
    require(counts["unresolved"] == sum(bool(r["unresolved_questions"]) for r in rows), "unresolved count mismatch")
    require(report["unresolved_shortlist"] == [{"target": r["target"], "questions": r["unresolved_questions"]} for r in rows if r["xhigh_material"]], "shortlist mismatch")
    require(counts["genuine_functions_or_thunks"] == counts["corrected_owners"] == counts["manifest_changes"] == 0, "unsupported function action")
    require(counts["rejected_promotions"] == len(rows), "promotion count mismatch")


def reviewed_plan(report):
    """Semantic review companion; never reinterpret a block as a function proposal."""
    return {"schema": {"name": "fable2-ownership-reviewed-plan", "version": 1},
            "input_plan": report["inputs"]["import_plan"],
            "ledger_sha256": digest(p4.canonical_json_bytes(report)),
            "application_policy": "annotation_only_no_manifest_application",
            "function_proposals": [],
            "targets": [{"target": r["target"], "phase4_candidate_id": r["phase4_candidate_id"],
                         "phase4_category": r["phase4_category"], "semantic_classification": r["classification"],
                         "owner": r["current_owner"]["address"], "action": r["action"]}
                        for r in report["targets"]]}


def markdown(report):
    lines = ["# Focused ownership ledger", "", "Generated by `tools/Fable2OwnershipCorroboration.py`; JSON is authoritative.", "",
             "| Target | Phase 4 category | Owner [start, exclusive end) | Final classification | Sources | Action |",
             "| --- | --- | --- | --- | --- | --- |"]
    for r in report["targets"]:
        owner = r["current_owner"]["range"]
        sources = ", ".join(sorted({p["source"] for p in r["observations"]}))
        lines.append(f"| `{r['target']}` | `{r['phase4_category']}` | `[{owner['start']},{owner['end']})` | `{r['classification']}` / {r['confidence']} | {sources} | retain; no promotion |")
    lines += ["", "## Reconciliation", "", "```json", json.dumps(report["counts"], indent=2, sort_keys=True), "```", "",
              "The JSON records exact body fragments (not just enclosing extents), source/run/thread provenance, call/LR checks, table indices and bounds, independent boundary checks, generated source locations and unresolved dispositions.", "",
              "No new dispatcher registration is established as necessary. A call-return continuation is not an alternate callable entry; switch membership is not independent function evidence.", ""]
    return "\n".join(lines).encode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase4-directory", type=Path, required=True)
    parser.add_argument("--closure", type=Path, required=True)
    parser.add_argument("--ghidra-map", type=Path, default=p4.default_analysis_path("ghidra-function-map.json"))
    parser.add_argument("--guest-snapshot", type=Path, required=True)
    parser.add_argument("--guest-base", type=lambda s: int(s, 0), default=0x82000000)
    parser.add_argument("--disassembler", type=Path, default=ROOT / "out/tools/ppc-disasm.exe")
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = build(args)
    outputs = {"ownership-ledger.json": p4.canonical_json_bytes(report), "ownership-ledger.md": markdown(report),
               "ownership-reviewed-import-plan.json": p4.canonical_json_bytes(reviewed_plan(report))}
    for filename, data in outputs.items():
        output = args.output_directory / filename
        if args.check:
            require(output.read_bytes() == data, f"regenerated evidence differs: {output}")
        else:
            p4.atomic_write_bytes(output, data)
    print("PASS: " + json.dumps(report["counts"], sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
