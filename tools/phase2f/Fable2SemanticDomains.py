"""Exhaustive frozen-domain reconciliation; contextual links are not proof."""
from __future__ import annotations

import collections
import hashlib
from pathlib import Path

import Fable2SemanticSources as s
import Fable2SemanticRoutes as r


def bound_start(value):
    if not isinstance(value, dict):
        return None
    return value.get("start") or value.get("boundary", {}).get("start")


def obligations_callable(facts):
    required = ("native_name", "payload", "callback", "adapter", "state", "namespace", "tu1_consumer", "reachability")
    return all(facts.get(k) is True for k in required)


def typed_proof(facts):
    return all(facts.get(k) is True for k in ("bounds_proven", "typed_descriptor_proven", "object_vptr_writer_proven", "slot_correspondence_proven"))


def runtime_script_proof(facts):
    return all(facts.get(k) is True for k in ("native_binding", "state_owner", "namespace_owner", "startup_consumer", "retail_provenance"))


def role_routes(engine, build, roles):
    result = {}
    for lane, mapping in sorted(engine.maps.items()):
        route_rows = []
        for role, address, owned in sorted(set(roles)):
            middle, pair, edges = engine.owner(build, address, mapping)
            usable = pair is not None and owned
            native_target = build == r.TARGET and owned
            route_rows.append({"role":role, "donor":address, "target":address if native_target else pair["target_start"] if usable else None,
                "edges":edges if usable else [], "reservations":r.reservations(edges) if usable else [],
                "grade":"native-target-evidence" if native_target else "contextual-native-route" if usable else "ownership-or-boundary-blocked" if not owned else "suppression-blocked" if middle in r.SUPPRESSIONS else "mapping-blocked",
                "independent_semantic_corroboration":False})
        result[lane] = route_rows
    return result


def changed_roles(lanes):
    before = {(x["role"],x["donor"]):x for x in lanes["S"]}
    return [x for x in lanes["O"] if x["target"] != before[(x["role"],x["donor"])]["target"]]


def domain_audits(engine, lane_o):
    inputs = engine.inputs
    documents = {}
    collections_index = []

    def collection(path, field, name, roles_fn=None):
        path = Path(path)
        if path not in documents:
            documents[path] = inputs.read(path)
        rows = documents[path][field]
        result = []
        for i, row in enumerate(rows):
            roles = roles_fn(row) if roles_fn else []
            lanes = role_routes(engine, row.get("build",r.DONOR), roles)
            item = {"id":name+":"+str(i).zfill(5), "source":inputs.ref(path,"/"+field+"/"+str(i)),
                    "source_record_sha256":s.digest(s.payload(row)), "build":row.get("build"),
                    "lanes":lanes, "changed_roles":changed_roles(lanes), "canonical_adoption":False}
            result.append(item)
        collections_index.append({"population":name,"source":inputs.ref(path,"/"+field),"records":len(rows),
                                  "ids":[x["id"] for x in result], "overlap":"domain records are not additional Phase 2B semantic terminals"})
        return rows,result

    def reg_roles(row):
        callback = row.get("callback")
        result = [("caller",row["caller"]["start"],True),("payload-helper",row["helper"],True)]
        if callback:
            start = bound_start(callback)
            if start:
                result.append(("callback",start,callback.get("kind") == "pdata-function"))
        return result

    uses, registrations = collection(s.C/"registration.json","constructor_uses","registration-call",reg_roles)
    shapes, shape_results = collection(s.C/"registration.json","recognizer_candidates","registration-shape",
        lambda x:[("helper",x["boundary"]["start"],True),("adapter",x["shape"]["adapter"],True)])
    target_uses = collections.defaultdict(list)
    for i,row in enumerate(uses):
        if row["build"] == r.TARGET:
            target_uses[row["caller"]["start"]].append((i,row))
    for source,row in zip(uses,registrations):
        row["native_name_sha256"] = (source.get("name") or {}).get("full_sha256")
        row["native_name_text"] = (source.get("name") or {}).get("full_text")
        row["remaining_obligations"] = source["blockers"]
        row["compatible_target_calls"] = []
        role_map = {x["role"]:x["target"] for x in row["lanes"]["O"]}
        for index,target in target_uses[role_map.get("caller")]:
            if int(target["call"]["instruction"],16)-int(target["caller"]["start"],16) != int(source["call"]["instruction"],16)-int(source["caller"]["start"],16):
                continue
            row["compatible_target_calls"].append({"source":inputs.ref(s.C/"registration.json","/constructor_uses/"+str(index)),
                "helper_corresponds":role_map.get("payload-helper") == target["helper"],
                "callback_corresponds":role_map.get("callback") is not None and role_map["callback"] == bound_start(target.get("callback")),
                "complete_name_matches":row["native_name_sha256"] is not None and row["native_name_sha256"] == (target.get("name") or {}).get("full_sha256"),
                "state_and_namespace_proven":False})
        row["tu1_callable"] = False
    structure = documents[s.C/"registration.json"]["recovered_structures"][0]
    free_roles = [("caller",structure["caller"],True),("helper",structure["helper"],True),
                  ("adapter",structure["adapter"],True),("internal-callback",structure["callback_region"]["start"],False)]
    for proof in structure["evidence"]:
        free_roles.append(("construction-chain-callee",proof["boundary"]["start"],True))
    free_lanes = role_routes(engine,r.DONOR,free_roles)
    freecamera = {"source":inputs.ref(s.C/"registration.json","/recovered_structures/0"),
        "native_name_address":structure["name"]["address"], "native_name":structure["name"]["full_text"],
        "caller":structure["caller"], "callsite":structure["callsite"], "callback_behavior":structure["callback_behavior"],
        "lanes":free_lanes, "changed_roles":changed_roles(free_lanes),
        "facts":{"native_name":True,"payload":True,"callback":True,"adapter":True,"state":False,"namespace":False,"tu1_consumer":False,"reachability":False},
        "remaining_obligations":["corresponding-TU1-caller/helper/adapter/internal-callback-chain","native-Lua-or-command-state-lifetime",
                                 "Debug-namespace/table-ownership","corresponding-TU1-registration-consumer","callable-reachability"],
        "tu1_callable":False,"community_spelling_accepting":False}
    s.require(not obligations_callable(freecamera["facts"]),"Free-camera authorization drift")

    script_rows,scripts = collection(s.C/"scripts.json","records","script")
    pair_rows,script_pairs = collection(s.C/"scripts.json","script_pairs","script-pair")
    pres_rows,preservation = collection(s.C/"preservation.json","records","preservation")
    by_spelling = collections.defaultdict(list)
    by_anchor = collections.defaultdict(list)
    for terminal in lane_o["records"]:
        if terminal["target_start"] is not None:
            by_spelling[engine.anchors[terminal["anchor_id"]]["spelling"]].append(terminal)
            by_anchor[terminal["anchor_id"]].append(terminal)
    newly_routed_ids = {row["id"] for row in engine.rows if engine.route(row,engine.maps["S"])["target_start"] is None}
    for source,row in zip(pres_rows,preservation):
        names = sorted({name for dep in source["dependencies"] for name in dep.get("required_command_names",[])})
        links = {t["terminal_id"]:t for name in names for t in by_spelling[name]}
        row.update(path=source["path"], presence_grade=source["grade"], portability=source["portability_class"],
            required_command_names=names, routed_terminal_ids=sorted(links),
            newly_routed_terminal_ids=sorted(set(links)&newly_routed_ids),
            native_state_proven=False, runnable_recovery_proven=False,
            blockers=["native-state/namespace/consumer","bank-format-and-content-closure","retail-provenance"],
            current_runtime_presence=source["current_runtime_presence"])
    # Static literal identity relationships only. Lua constants are metadata
    # hashes, not executed or decoded script payloads. The frozen Lua parser
    # EXCLUDES the terminator, while native full_sha256 INCLUDES it. Recompute
    # the former from the already bound complete ASCII literal, never compare
    # incompatible hash conventions or infer a state/binding from equality.
    routed_hashes = collections.defaultdict(set)
    prior = {x["id"]:x for x in engine.rows}
    for terminal in lane_o["records"]:
        if terminal["target_start"] is None:
            continue
        for ref_id in prior[terminal["terminal_id"]]["donor_xrefs"]:
            obj = engine.obj(engine.refs[ref_id])
            if obj.get("encoding") == "ascii" and obj.get("pointer_relation") == "start" and obj.get("full_text"):
                routed_hashes[s.digest(obj["full_text"].encode("ascii"))].add(terminal["terminal_id"])
    for source,row in zip(script_rows,scripts):
        hashes = {x["sha256"] for prototype in source.get("parsed",{}).get("prototypes",[]) for x in prototype["string_constants"]}
        linked = set().union(*(routed_hashes[h] for h in hashes)) if hashes else set()
        row.update(path=source["path"],status=source["status"],constant_hash_count=len(hashes),
            literal_relationship_terminal_ids=sorted(linked),new_literal_relationship_terminal_ids=sorted(linked & newly_routed_ids),
            relationship_grade="literal-identity-not-native-binding" if linked else "no-bound-native-literal-relationship",
            native_binding=False,retail_startup_proven=False,bank_parser_available=False)
    for source,row in zip(pair_rows,script_pairs):
        row.update(build=source["build"], scripts=source["scripts"], scripts_r=source["scripts_r"],
                   structural_relationship=source["same_executable_structure"], semantic_identity=False,retail_startup_proven=False)
    inventory = inputs.read(r.historical_b.P1/"prototype-inventory.json")
    e3 = []
    for i,row in enumerate(inventory["files"]):
        if "e3" in row["relative_path"].lower():
            e3.append({"source":inputs.ref(r.historical_b.P1/"prototype-inventory.json","/files/"+str(i)),
                "build":row["build_id"],"path":row["relative_path"],"size":row["size"],"sha256":row["sha256"],
                "grade":"confirmed-presence", "native_dependencies":[],"runnable_recovery_proven":False})
    s.require(len(e3) == 21,"E3 presence population changed")

    typed_path = s.C/"completion/typed-completion.json"
    type_rows,types = collection(typed_path,"type_contexts","type")
    pointer_rows,pointers = collection(typed_path,"pointer_runs","pointer-run",
        lambda x:[("pointer-slot:"+slot["slot"],slot["entry"],True) for slot in x["slots"]]+
                 [("reader-writer:"+use["instruction"],use["function"]["start"],True) for use in x["native_readers_writers"]])
    global_rows,globals_out = collection(typed_path,"globals","global",
        lambda x:[("access-owner",x["donor_access"]["function"]["start"],True)])
    boundary_rows,boundaries = collection(s.C/"completion/boundary-completion.json","records","boundary",
        lambda x:[("boundary-owner",x["donor"]["start"],x["relation"] != "internal-code-region")] if x.get("donor") else [])
    for source,row in zip(type_rows,types):
        terminals = by_anchor.get(source["id"],[])
        row.update(routed_terminal_ids=sorted(t["terminal_id"] for t in terminals),
                   newly_routed_terminal_ids=sorted(t["terminal_id"] for t in terminals if t["terminal_id"] in newly_routed_ids),
                   disposition=source["disposition"],constructor_identity_proven=False)
    target_runs = collections.defaultdict(list)
    for i,source in enumerate(pointer_rows):
        if source["build"] == r.TARGET:
            target_runs[tuple(slot["entry"] for slot in source["slots"])].append(inputs.ref(typed_path,f"/pointer_runs/{i}"))
    for source,row in zip(pointer_rows,pointers):
        row.update(disposition=source["disposition"], facts=source["facts"], vtable_proven=typed_proof(source["facts"]))
        row["changed_slot_sequence_comparison"] = {}
        if row["changed_roles"]:
            for lane,roles in row["lanes"].items():
                by_slot = {x["role"]:x["target"] for x in roles if x["role"].startswith("pointer-slot:")}
                sequence = tuple(by_slot["pointer-slot:"+x["slot"]] for x in source["slots"])
                row["changed_slot_sequence_comparison"][lane] = {"all_slots_routed":all(sequence),
                    "matching_native_target_runs":target_runs.get(sequence,[]) if all(sequence) else [],
                    "complete_object_proven":False,"semantic_corroboration":False}
    for source,row in zip(global_rows,globals_out):
        row.update(disposition=source["disposition"],facts=source["facts"],complete_object_proven=False,
                   donor_access=source["donor_access"],target_access=source["target_access"])
    for source,row in zip(boundary_rows,boundaries):
        row.update(relation=source["relation"],semantic_transport=False)

    # Exact current-project indexes are already bound upstream; membership is
    # contextual even where the target has a Ghidra or coverage entry.
    sets = r.historical_b.problem_sets()
    intersections = []
    for mapping in engine.maps["O"].values():
        if mapping["generation"] == 0:
            continue
        links = r.historical_b.intersections({"start":mapping["target_start"],"end_exclusive":mapping["target_end_exclusive"]},sets)
        for link in links:
            s.require(link["source"] in inputs.pins, "Unbound project intersection")
        intersections.append({"mapping_id":mapping["id"],"batch":mapping["provenance"]["batch"],
            "donor_start":mapping["donor_start"],"target_start":mapping["target_start"],"reservations":mapping["reservations"],
            "intersections":links,"disposition":"context-and-priority-only","independent_semantic_corroboration":False})
    profile_rows = []
    packets = inputs.read(s.D/"packets.json")["records"]
    for i,packet in enumerate(packets):
        if packet["id"] not in engine.actions:
            continue
        action = engine.actions[packet["id"]]
        owner_terminals = [t for t in lane_o["records"] if t["build"] == r.DONOR and t["donor_start"] == packet["donor_start"]]
        references = []
        for j,reference in enumerate(packet["donor_profile"]["references"]):
            obj = reference["object"]
            matches = sorted(t["terminal_id"] for t in owner_terminals if any(engine.refs[x]["instruction"] == reference["reference"]["instruction"] for x in next(y["donor_xrefs"] for y in engine.rows if y["id"] == t["terminal_id"])))
            references.append({"source":inputs.ref(s.D/"packets.json",f"/records/{i}/donor_profile/references/{j}"),
                "object":obj,"role":reference["reference"],"semantic_terminal_aliases":matches,
                "mapping_canonicalization_consumed":True,"independent_semantic_vote":False,
                "category":r.category(obj.get("text",""))})
        profile_rows.append({"mapping_id":packet["id"],"source":inputs.ref(s.D/"packets.json",f"/records/{i}"),
            "batch":action["source_batch"],"reservations":action["reservations"],"references":references,
            "reference_distinctiveness":packet["reference_distinctiveness"],"helpers":packet["helpers"],
            "behavior_evidence_consumed_by_mapping":True,"new_independent_semantic_evidence":[],
            "limitation":"Full-reference, field/argument/return and topology observations were already gates in Phase 2D; they are not fresh semantic votes."})
    return {"collection-index":collections_index,
        "registration-debug-freecamera":{"records":registrations,"shapes":shape_results,"freecamera":freecamera,
            "counts":{"calls":len(uses),"shapes":len(shapes),"complete_candidates":sum(x["name"] is not None and r.historical_c.identity_token(x["name"]) is not None and x["callback"] is not None for x in uses),
                      "changed_calls":sum(bool(x["changed_roles"]) for x in registrations),"changed_shapes":sum(bool(x["changed_roles"]) for x in shape_results),"callable_tu1_chains":0}},
        "script-preservation":{"scripts":scripts,"script_pairs":script_pairs,"preservation":preservation,"e3_presence":e3,
            "counts":{"scripts":len(scripts),"parsed":sum("parsed" in x for x in script_rows),"inventory_only":sum("parsed" not in x for x in script_rows),"pairs":len(script_pairs),"preservation":len(preservation),"e3":len(e3),
                      "new_preservation_links":sum(bool(x["newly_routed_terminal_ids"]) for x in preservation),"new_script_literal_links":sum(bool(x["new_literal_relationship_terminal_ids"]) for x in scripts),"runnable_recoveries":0}},
        "type-global-boundary":{"types":types,"pointer_runs":pointers,"globals":globals_out,"boundaries":boundaries,
            "counts":{"types":len(types),"pointer_runs":len(pointers),"globals":len(globals_out),"boundaries":len(boundaries),
                      "changed_pointer_runs":sum(bool(x["changed_roles"]) for x in pointers),"changed_globals":sum(bool(x["changed_roles"]) for x in globals_out),"changed_boundaries":sum(bool(x["changed_roles"]) for x in boundaries),
                      "changed_runs_matching_native_target_sequence":sum(bool(x["changed_slot_sequence_comparison"].get("O",{}).get("matching_native_target_runs")) for x in pointers),
                      "retained_incompatible_globals":sum(x["disposition"] == "rejected-incompatible-object-or-access" for x in globals_out),
                      "proven_vtables":sum(x["vtable_proven"] for x in pointers),"proven_complete_objects":0}},
        "project-intersections":{"records":intersections,"counts":{k:sum(any(x["set"] == k for x in row["intersections"]) for row in intersections) for k in sets}},
        "mapping-context-packets":{"records":profile_rows,"counts":{"mappings":len(profile_rows),"references":sum(len(x["references"]) for x in profile_rows)}}}
