"""Phase 2F static analysis driver. All writes are Phase 2F-scoped."""
from __future__ import annotations

import argparse
import collections
from pathlib import Path

import Fable2SemanticSources as s
import Fable2SemanticRoutes as r
import Fable2SemanticDomains as domains


def comparison(before, after):
    left = {x["terminal_id"]:x for x in before["records"]}
    changed = []
    for row in after["records"]:
        old = left[row["terminal_id"]]
        keys = ("target_start","grade","used_additions","reservations","conflicts")
        if any(row[k] != old[k] for k in keys):
            changed.append({"terminal_id":row["terminal_id"],"before":{k:old[k] for k in keys},"after":{k:row[k] for k in keys},
                            "newly_routable":old["target_start"] is None and row["target_start"] is not None,
                            "newly_corroborated":old["grade"] != "target-corroborated" and row["grade"] == "target-corroborated"})
    return {"from":before["lane"],"to":after["lane"],"records":changed,
            "counts":{"changed":len(changed),"newly_routable":sum(x["newly_routable"] for x in changed),
                      "newly_corroborated":sum(x["newly_corroborated"] for x in changed)}}


def source_index(engine):
    inputs = engine.inputs
    rows = []
    for i,row in enumerate(engine.rows):
        anchor = engine.anchors[row["anchor_id"]]
        rows.append({"terminal_id":row["id"],"source":inputs.ref(s.B/"semantic-index.json",f"/records/{i}"),
            "anchor_id":anchor["id"],"reference_text":anchor["spelling"],"reference_is_function_name":False,
            "anchor_provenance":anchor["provenance"],"build":row["build"],"donor_function":row["donor_function"],
            "donor_xrefs":row["donor_xrefs"],"filters":anchor["filters"],"subsystem":anchor["subsystem"],
            "category":r.category(anchor["spelling"]),"historical_grade":row["status"],"canonical_function_name":None})
    collections_out = []
    for family,field in (("inventory","anchors"),("xrefs","references"),("xrefs","data_pointers"),
                         ("mapping-review","records"),("registrations","records"),("globals","records"),("graph","records")):
        values = engine.family[family][field]
        collections_out.append({"source":inputs.ref(s.B/("semantic-"+family+".json"),"/"+field),
            "population":family+"/"+field,"records":len(values),"members":[{"id":x["id"],"source_index":i,
            "semantic_terminal_alias":x.get("association_id")} for i,x in enumerate(values)],
            "overlap":"reference/anchor/review/registration/global evidence; not additional semantic terminals"})
    return {"records":rows,"collections":collections_out,"counts":{"terminals":len(rows),"anchors":len(engine.anchors),
        "filtered_anchors":sum(bool(x["filters"]) for x in engine.anchors.values()),
        "donor_xref_resolved_anchors":len({x["anchor_id"] for x in engine.rows if x["donor_xrefs"]}),
        "instruction_xrefs":len(engine.refs),"data_pointer_xrefs":len(engine.family["xrefs"]["data_pointers"]),
        "mapping_review_aliases":len(engine.family["mapping-review"]["records"])}}


def contributions(engine, lanes):
    baseline = {x["terminal_id"]:x for x in lanes["S"]["records"]}
    full = lanes["O"]["records"]
    records = []
    for mapping in engine.maps["O"].values():
        if mapping["generation"] == 0:
            continue
        action = engine.actions[mapping["id"]]
        encountered = [x for x in full if mapping["id"] in x["used_additions"] or (x["build"] == r.DONOR and x["donor_start"] == mapping["donor_start"])]
        absent = {k:v for k,v in engine.maps["O"].items() if k != mapping["donor_start"]}
        terminals = {x["id"]:x for x in engine.rows}
        leaveout = [engine.route(terminals[x["terminal_id"]],absent) for x in encountered]
        needed_route = [x["terminal_id"] for x,y in zip(encountered,leaveout) if x["target_start"] and not y["target_start"]]
        needed_proof = [x["terminal_id"] for x,y in zip(encountered,leaveout) if x["grade"] == "target-corroborated" and y["grade"] != "target-corroborated"]
        newly = [x for x in encountered if x["target_start"] and baseline[x["terminal_id"]]["target_start"] is None]
        records.append({"mapping_id":mapping["id"],"donor_start":mapping["donor_start"],"target_start":mapping["target_start"],
            "batch":mapping["provenance"]["batch"],"reservations":mapping["reservations"],"decision_binding":mapping["provenance"],
            "reference_text":action["contextual_reference_text"],"reference_is_function_name":False,
            "encountered_terminal_ids":[x["terminal_id"] for x in encountered],"newly_routable_terminal_ids":[x["terminal_id"] for x in newly],
            "leave_one_mapping_out":{"route_necessary":needed_route,"corroboration_necessary":needed_proof},
            "counts":{"encountered":len(encountered),"newly_routable":len(newly),"newly_target_corroborated":len(needed_proof),
                      "transported_only":sum(x["grade"] != "target-corroborated" for x in encountered),
                      "conflicts":sum(bool(x["conflicts"]) for x in encountered),"categories":r.counts(encountered,"category")},
            "productive":bool(needed_route or needed_proof),"distinctiveness":action["reference_distinctiveness"],
            "common_helper_reserved":any("common" in x for x in mapping["reservations"]),
            "reference_population":"all-unique-in-each-population" if action["reference_distinctiveness"] and all(x["unique_in_each_population"] for x in action["reference_distinctiveness"]) else "has-repeated-or-nondistinctive-reference",
            "independent_support_classes":action["support_classes"]})
    return {"records":sorted(records,key=lambda x:x["mapping_id"]),"counts":{"mappings":len(records),
            "productive":sum(x["productive"] for x in records),"dormant":sum(not x["productive"] for x in records)},
            "counting":"Mapping totals overlap for joint semantic proofs; terminal IDs, not summed rows, define universe totals."}


def enrich_domains(mapping, domain, suppression):
    families = {
        "registration":domain["registration-debug-freecamera"]["records"],
        "registration-shape":domain["registration-debug-freecamera"]["shapes"],
        "script":domain["script-preservation"]["scripts"],
        "preservation":domain["script-preservation"]["preservation"],
        "type":domain["type-global-boundary"]["types"],
        "pointer-run":domain["type-global-boundary"]["pointer_runs"],
        "global":domain["type-global-boundary"]["globals"],
        "boundary":domain["type-global-boundary"]["boundaries"]}
    project = {x["mapping_id"]:x for x in domain["project-intersections"]["records"]}
    for contribution in mapping["records"]:
        ids = set(contribution["encountered_terminal_ids"])
        contribution["domain_intersections"] = {}
        for name,rows in families.items():
            matches = []
            for row in rows:
                route_ids = {e["id"] for role in row["lanes"]["O"] for e in role["edges"]}
                semantic_ids = set(row.get("routed_terminal_ids",row.get("literal_relationship_terminal_ids",[])))
                if contribution["mapping_id"] in route_ids or ids & semantic_ids:
                    matches.append(row["id"])
            contribution["domain_intersections"][name] = matches
        contribution["project_intersections"] = project[contribution["mapping_id"]]["intersections"]
    removed = []
    for name,rows in families.items():
        for row in rows:
            collisions = [role for role in row["lanes"]["H-2A"] if any(r.SUPPRESSIONS.get(e["donor"]) == e["target"] for e in role["edges"])]
            if collisions:
                removed.append({"population":name,"id":row["id"],"source":row["source"],
                    "historical_roles":collisions,"S":row["lanes"]["S"],"O":row["lanes"]["O"]})
    suppression["domain_historical_associations_removed"] = removed
    suppression["domain_removal_counts"] = r.counts(removed,"population")
    b04 = [x for x in mapping["records"] if x["batch"]["id"].startswith("B04-")]
    mapping["b04_strata"] = {"mappings":len(b04),"reference_population":r.counts(b04,"reference_population"),
        "common_helper_reserved":sum(x["common_helper_reserved"] for x in b04),
        "non_common_helper_reserved":sum(not x["common_helper_reserved"] for x in b04),
        "semantic_categories":dict(sorted(sum((collections.Counter(x["counts"]["categories"]) for x in b04),collections.Counter()).items()))}


def batch_audit(engine, lanes):
    cumulative = []
    leaveout = []
    previous = "S"
    for i,batch in enumerate(r.BATCHES):
        name = "S+"+"+".join(r.BATCHES[:i+1])
        change = comparison(lanes[previous],lanes[name])
        enabled = {x["terminal_id"] for x in change["records"] if x["newly_routable"]}
        change["batch"] = batch
        change["categories"] = r.counts([x for x in lanes[name]["records"] if x["terminal_id"] in enabled],"category")
        proof_ids = {x["terminal_id"] for x in change["records"] if x["newly_corroborated"]}
        change["corroboration_categories"] = r.counts([x for x in lanes[name]["records"] if x["terminal_id"] in proof_ids],"category")
        cumulative.append(change)
        ablation = comparison(lanes["O-minus-"+batch],lanes["O"])
        ablation["batch"] = batch
        ids = {x["terminal_id"] for x in ablation["records"] if x["newly_routable"]}
        ablation["categories"] = r.counts([x for x in lanes["O"]["records"] if x["terminal_id"] in ids],"category")
        proof_ids = {x["terminal_id"] for x in ablation["records"] if x["newly_corroborated"]}
        ablation["corroboration_categories"] = r.counts([x for x in lanes["O"]["records"] if x["terminal_id"] in proof_ids],"category")
        leaveout.append(ablation)
        previous = name
    return {"cumulative":cumulative,"leave_one_batch_out":leaveout,
            "interpretation":"Exclusive first owner-route enablement in B01,B02,B04,B05 order; leave-out necessity is a counterfactual, not an additive causal vote."}


def suppression_audit(engine, lanes):
    historical = {x["terminal_id"]:x for x in lanes["H-2A"]["records"]}
    safe = {x["terminal_id"]:x for x in lanes["S"]["records"]}
    full = {x["terminal_id"]:x for x in lanes["O"]["records"]}
    source = {x["id"]:x for x in engine.rows}
    rows = []
    for terminal_id,old in historical.items():
        used = {(edge["donor"],edge["target"]) for route in old["routes"] for edge in route["edges"]}
        collisions = used & set(r.SUPPRESSIONS.items())
        if not collisions:
            continue
        original = source[terminal_id]
        rows.append({"terminal_id":terminal_id,"anchor_id":old["anchor_id"],"reference_text":engine.anchors[old["anchor_id"]]["spelling"],
            "historical_grade":original["status"],"historical_routes":old["routes"],"suppressed_pairs":sorted(collisions),
            "S":safe[terminal_id],"O":full[terminal_id],
            "disposition":"safely-rerouted" if full[terminal_id]["target_start"] else "suppression-blocked",
            "downstream_consumers":[x["id"] for x in engine.family["mapping-review"]["records"] if x["association_id"] == terminal_id]})
    # Traverse all frozen September pair routes, not just semantic joins.
    september = []
    for start,secondary in sorted(engine.sep.items()):
        by_lane = {}
        for lane,mapping in sorted(engine.maps.items()):
            _,pair,edges = engine.owner("sep-2008",start,mapping)
            by_lane[lane] = {"target":pair["target_start"] if pair else None,"edges":edges if pair else [],
                            "reservations":r.reservations(edges) if pair else []}
        september.append({"id":secondary["id"],"donor":start,"middle":secondary["target_start"],"lanes":by_lane})
    s.require(len(engine.sep_document["original_pairs"]) == 9600,"September original count")
    return {"records":rows,"counts":{"removed_historical_associations":len(rows),"safely_rerouted":sum(x["disposition"] == "safely-rerouted" for x in rows),
        "remaining_suppression_blocked":sum(x["disposition"] == "suppression-blocked" for x in rows)},
        "september":{"original_pairs":9600,"trusted_pairs":len(september),"records":september,
                     "routed_counts":{lane:sum(x["lanes"][lane]["target"] is not None for x in september) for lane in engine.maps}},
        "physics_review_only":[{"donor":a,"target":b,"approved_route":False} for a,b in sorted(r.PHYSICS)]}


def review_queues(engine, lanes, domain, mapping):
    baseline = {x["terminal_id"]:x for x in lanes["S"]["records"]}
    queues = collections.defaultdict(list)
    for row in lanes["O"]["records"]:
        if not row["used_additions"]:
            continue
        anchor = engine.anchors[row["anchor_id"]]
        if row["conflicts"]:
            queue = "semantic-conflicts"
        elif row["category"] == "sdk-compiler-vector":
            queue = "sdk-compiler-support"
        elif row["grade"] == "target-corroborated":
            queue = "target-corroborated-game-context" if row["category"] == "fable-game-specific" else "target-corroborated-other"
        elif any(t in anchor["spelling"].lower() for t in ("camera","debug","console","cheat","command")):
            queue = "registration-debug-freecamera"
        elif any(t in anchor["spelling"].lower() for t in ("script","e3","demo","startup","quest","childhood","presentation")):
            queue = "script-e3-preservation"
        elif row["category"] == "fable-game-specific":
            queue = "reserved-game-context" if row["reservations"] else "unreserved-game-context"
        else:
            queue = "generic-or-unknown"
        queues[queue].append({"terminal_id":row["terminal_id"],"source":engine.inputs.ref(s.B/"semantic-index.json","/records/"+str(next(i for i,x in enumerate(engine.rows) if x["id"] == row["terminal_id"]))),
            "reference_text":anchor["spelling"],"donor_start":row["donor_start"],"target_start":row["target_start"],
            "grade":row["grade"],"category":row["category"],"routes":row["routes"],"mapping_ids":row["used_additions"],
            "reservations":row["reservations"],"newly_routable":baseline[row["terminal_id"]]["target_start"] is None,
            "limitations":["Context text is not a canonical function name.","Mapping-consumed evidence is not an independent semantic vote."],
            "next_static_action":"Inspect the exact bound target instruction and its caller/consumer obligation; do not revise mappings or invoke commands."})
    order = ("semantic-conflicts","target-corroborated-game-context","reserved-game-context","unreserved-game-context",
             "registration-debug-freecamera","script-e3-preservation","target-corroborated-other","generic-or-unknown","sdk-compiler-support")
    # Full queues are exhaustive; the human tranche is bounded and excludes
    # support wrappers. One representative per owner/target/category group.
    selected,seen = [],set()
    for name in order[:-2]:
        for row in sorted(queues[name],key=lambda x:(x["donor_start"],x["terminal_id"])):
            key = (name,row["donor_start"],row["target_start"])
            if key in seen or len(selected) >= 8:
                continue
            seen.add(key)
            selected.append({"queue":name,**row})
    for name in order:
        queues[name].sort(key=lambda x:(x["donor_start"],x["terminal_id"]))
    return {"queues":dict(queues),"selected":selected,"ranking":"conflict precedence, independently corroborated game context, reserved/unreserved game context, native debug and preservation relevance; stable address ties",
            "counts":{name:len(queues[name]) for name in order},"selected_count":len(selected),
            "project_intersections":domain["project-intersections"]["records"],
            "zero_yield_mappings":[x["mapping_id"] for x in mapping["records"] if not x["productive"]]}


def analyze(replay=False):
    pins,effective = s.source_bindings()
    s.write(s.DOC/"evidence/source-pins.json",pins,replay)
    selection = pins["overlay_selection"]
    inputs = s.Inputs(pins)
    engine = r.Engine(inputs,effective)
    artifacts = []

    def emit(name, fields, root=s.OUT):
        document = s.envelope(name,selection,**fields)
        artifacts.append(s.write(root/(name+".json"),document,replay))
        return document

    emit("source-terminal-index",source_index(engine))
    print("PASS semantic universe",len(engine.rows),flush=True)
    emit("historical-H",engine.historical())
    print("PASS historical B/C byte-identical reproduction",flush=True)
    lanes = {}
    for name in sorted(engine.maps):
        lanes[name] = engine.lane(name)
        emit("lane-"+name,lanes[name])
        print("PASS lane",name,lanes[name]["counts"],flush=True)
    change_document = comparison(lanes["S"],lanes["O"])
    full_by_id = {x["terminal_id"]:x for x in lanes["O"]["records"]}
    historical_c = inputs.read(s.C/"completion/semantic-final.json")["records"]
    change_document["phase2c_routes_excluded_by_phase2e"] = [{"terminal_id":x["prior_record_id"],"reference_text":engine.anchors[x["anchor_id"]]["spelling"],
        "historical_target":x["target_start"],"historical_grade":x["status"],"historical_dependencies":x["mapping_dependencies"],
        "approved_lane_grade":full_by_id[x["prior_record_id"]]["grade"],"reason":"held-Phase2D-mapping-not-owner-approved"}
        for x in historical_c if x["target_start"] and not full_by_id[x["prior_record_id"]]["target_start"]]
    emit("lane-delta",change_document)
    mapping = contributions(engine,lanes)
    batches = batch_audit(engine,lanes)
    emit("batch-attribution",batches)
    suppression = suppression_audit(engine,lanes)
    print("PASS mapping, batch and suppression reconciliation",flush=True)
    domain = domains.domain_audits(engine,lanes["O"])
    enrich_domains(mapping,domain,suppression)
    emit("mapping-contribution",mapping)
    emit("suppression-impact",suppression)
    for name,document in domain.items():
        emit(name,{"records":document} if isinstance(document,list) else document)
    print("PASS all domain populations",flush=True)
    interesting = [x for x in lanes["O"]["records"] if x["used_additions"]]
    emit("target-corroboration",{"records":interesting,"counts":r.counts(interesting,"grade")})
    emit("semantic-quarantine",{"records":[x for x in lanes["O"]["records"] if x["conflicts"]]})
    review = review_queues(engine,lanes,domain,mapping)
    emit("review-queues",review)
    emit("high-value-review",{"selected":review["selected"],"counts":review["counts"],"ranking":review["ranking"]},s.DOC/"evidence")
    changed = comparison(lanes["S"],lanes["O"])
    newly_ids = {x["terminal_id"] for x in changed["records"] if x["newly_routable"]}
    newly_sources = [x for x in engine.rows if x["id"] in newly_ids]
    summary = {"lanes":{name:{"mapping_count":d["mapping_count"],**d["counts"]} for name,d in lanes.items()},
        "newly_routable":changed["counts"]["newly_routable"],"newly_corroborated":changed["counts"]["newly_corroborated"],
        "newly_routable_and_corroborated":sum(x["newly_routable"] and x["newly_corroborated"] for x in changed["records"]),
        "new_from_mapping_blocked":sum(x["newly_routable"] and x["before"]["grade"] == "mapping-blocked" for x in changed["records"]),
        "new_from_suppression_blocked":sum(x["newly_routable"] and x["before"]["grade"] == "suppression-blocked" for x in changed["records"]),
        "new_owner_routes_relative_to_historical_phase2c":sum(not x["target_start"] and full_by_id[x["prior_record_id"]]["target_start"] is not None for x in historical_c),
        "new_route_population_units":{"terminals":len(newly_sources),"owner_functions":len({x["donor_function"]["start"] for x in newly_sources}),
            "anchor_ids":len({x["anchor_id"] for x in newly_sources}),"distinct_native_xref_records":len({ref for x in newly_sources for ref in x["donor_xrefs"]}),
            "xref_memberships":sum(len(x["donor_xrefs"]) for x in newly_sources)},
        "mapping_contribution":mapping["counts"],"b04_strata":mapping["b04_strata"],
        "suppression":suppression["counts"],"suppression_domain_counts":suppression["domain_removal_counts"],
        "batches":{"cumulative":[{k:x[k] for k in ("batch","counts","categories","corroboration_categories")} for x in batches["cumulative"]],
                   "leave_one_out":[{k:x[k] for k in ("batch","counts","categories","corroboration_categories")} for x in batches["leave_one_batch_out"]]},
        "domains":{k:v["counts"] for k,v in domain.items() if isinstance(v,dict) and "counts" in v},
        "review_counts":review["counts"],"selected_count":review["selected_count"],"artifacts":artifacts,
        "phase2c_routes_excluded":change_document["phase2c_routes_excluded_by_phase2e"],
        "inherited_blockers":pins["inherited_blockers"],"consumed_sources":sorted(inputs.used)}
    s.write(s.OUT/"analysis-summary.json",s.envelope("route-summary",selection,**summary),replay)
    print("PASS Phase 2F analysis",{k:summary[k] for k in ("newly_routable","newly_corroborated","newly_routable_and_corroborated","mapping_contribution")},flush=True)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true")
    args = parser.parse_args()
    analyze(args.check)
