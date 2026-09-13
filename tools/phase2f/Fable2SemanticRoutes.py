"""Deterministic semantic transport; mapping decisions are immutable inputs."""
from __future__ import annotations

import collections
import copy
import re

import Fable2SemanticSources as s
import Fable2PrototypeSemantics as historical_b
import Fable2PrototypeTrust as historical_c
import Fable2SemanticNative as native

DONOR = "build-23.12.02.0330"
TARGET = "canonical-tu1"
BATCHES = ("B01", "B02", "B04", "B05")
GRADES = ("target-corroborated", "transported-context-reserved", "transported-context-unreserved",
          "target-unconfirmed", "semantic-conflict-quarantined", "suppression-blocked",
          "mapping-blocked", "ownership-or-boundary-blocked")
SUPPRESSIONS = {"0x82631A30": "0x82950A98", "0x828EA448": "0x82681198", "0x83062950": "0x83060C30"}
PHYSICS = {("0x82631A30", "0x82630C30"), ("0x829506B0", "0x82950A98")}
HELD = {("0x82BC43E8", "0x82BC3FA8"), ("0x82E510E0", "0x82E515D0"), ("0x82FB6620", "0x82FB6C50")}


def counts(rows, key):
    return dict(sorted(collections.Counter(r[key] for r in rows).items()))


def category(text):
    """Lexical context class, NEVER an inferred function identity."""
    lower = text.lower().replace("\\", "/")
    if re.search(r"\b__(?:v[a-z0-9_]+|lvx|stvx|[a-z]*intrinsic)\b", lower) or any(x in lower for x in
            ("xdk/", "xnamath", "xmvector", "xmconvertvector", "xmstorefloat", "xmcomparison", "xm_matrix", "compiler", "crt/", "vc/include", "defconst statements")):
        return "sdk-compiler-vector"
    if any(x in lower for x in ("fable", "lionhead", "hammercombat", "maxcombo", "quest", "hero", "childhood", "albion", "e3", "gameflow", "gameface", "cec", "troll_footstep", "destroy_entity",
            "gui_death_xp", "canreceivegift", "oxygen", "appropriate", "worldmap", "rewardmoney", "rewardrenown", "absorbdistance", "allowedtoknock", "silverkeys", "weakspot", "marriage", "marry", "goldcanextort", "goldwillgivetobeggar", "childtakes", "triggerchildgrowth", "weapon.weapon")):
        return "fable-game-specific"
    if any(x in lower for x in ("memory", "thread", "filesystem", "invalid table index", "assert", "buffer", "malloc", "error", "platform", "direct3d", "d3d", "lua", "luaplus", "_loadlib", "xbox 360", "xts.webservices", "$$base_index")):
        return "generic-platform"
    return "unknown"


def lane_maps(effective, closed):
    safe = {r["donor_start"]: r for r in effective["records"] if r["generation"] == 0}
    additions = {r["donor_start"]: r for r in effective["records"] if r["generation"] > 0}
    s.require(len(safe) == 15296 and len(additions) == 83, "Lane input arithmetic")
    result = {"S": safe, "O": {**safe, **additions}}
    cumulative = dict(safe)
    for i, batch in enumerate(BATCHES):
        cumulative.update({k: r for k, r in additions.items() if r["provenance"]["batch"]["id"].split("-", 1)[0] == batch})
        result["S+" + "+".join(BATCHES[:i+1])] = dict(cumulative)
        result["O-minus-" + batch] = {k: r for k, r in result["O"].items() if k not in additions or r["provenance"]["batch"]["id"].split("-", 1)[0] != batch}
    # A historical-policy mapping view isolates the effect of B00. It is never
    # consumed by a safe route and does not grant enhanced transport approval.
    result["H-2A"] = {r["donor_start"]: {
        "id": r["donor_start"] + ":" + r["target_start"], "donor_start": r["donor_start"],
        "donor_end_exclusive": r["donor_end_exclusive"], "target_start": r["target_start"],
        "target_end_exclusive": r["target_end_exclusive"], "size": r["size"],
        "generation": 0, "source": "historical-closed-phase2a", "reservations": [],
        "provenance": {"status": r["status"], "record_index": i}}
        for i, r in enumerate(closed)}
    expected = {"S":15296, "O":15379, "H-2A":15299,
                "S+B01":15313, "S+B01+B02":15318, "S+B01+B02+B04":15378,
                "S+B01+B02+B04+B05":15379,
                "O-minus-B01":15362, "O-minus-B02":15374, "O-minus-B04":15319, "O-minus-B05":15378}
    for lane, mapping in result.items():
        s.require(len(mapping) == expected[lane], "Lane mapping count: " + lane)
        s.require(len({r["target_start"] for r in mapping.values()}) == len(mapping), "Target injectivity")
        if lane != "H-2A":
            pairs = {(r["donor_start"], r["target_start"]) for r in mapping.values()}
            s.require(not pairs & (set(SUPPRESSIONS.items()) | PHYSICS | HELD), "Forbidden route")
    return result


def edge(row, role="owner"):
    return {"id": row["id"], "donor": row["donor_start"], "target": row["target_start"],
            "role": role, "source": row["source"], "generation": row["generation"],
            "reservations": row["reservations"], "provenance": row["provenance"],
            "mapping_dependencies": row.get("dependencies", [])}


def route_kind(edges):
    if any(e["source"] == "september-trust" for e in edges):
        return "mixed-approved-route" if any(e["generation"] > 0 for e in edges) else "historical-september-two-hop"
    if any(e["generation"] > 0 for e in edges):
        return "owner-approved-phase2e-addition"
    return "exact-one-edge-phase2a" if edges[0]["provenance"].get("status") == "accepted-exact-unique" else "normalized-one-edge-phase2a"


def reservations(edges):
    return [{"mapping_id": e["id"], "batch": e["provenance"]["batch"]["id"], "reservations": e["reservations"]}
            for e in sorted(edges, key=lambda e: e["id"]) if e["reservations"]]


def primary_route(routes):
    # One terminal, all alternatives retained. Shorter proof paths do not
    # become stronger evidence: independent gate precedes path length.
    ordered = sorted(routes, key=lambda r: (not r["independent"], bool(r["reservations"]),
                                           len(r["edges"]), s.payload(r)))
    return ordered[0] if ordered else None


def evidence_gate(*, complete, equal, compatible_role, readonly, interior, empty,
                  canonicalized, common, independent_callee, contradiction=False):
    if contradiction or (complete and equal and not compatible_role):
        return "conflict"
    if not complete or not equal or not readonly or interior or empty:
        return "insufficient"
    if canonicalized or common:
        return "mapping-consumed-or-low-entropy"
    return "independent" if independent_callee else "insufficient"


def terminal_grade(*, owned, routed, suppressed, conflicts, independent, reserved, addition):
    if not owned:
        return "ownership-or-boundary-blocked"
    if not routed:
        return "suppression-blocked" if suppressed else "mapping-blocked"
    if conflicts:
        return "semantic-conflict-quarantined"
    if independent:
        return "target-corroborated"
    if reserved:
        return "transported-context-reserved"
    if addition:
        return "transported-context-unreserved"
    return "target-unconfirmed"


class Engine:
    def __init__(self, inputs, effective):
        self.inputs = inputs
        self.family = {k: inputs.read(s.B / ("semantic-" + k + ".json")) for k in
                       ("inventory", "xrefs", "index", "accepted", "review", "mapping-review", "graph", "globals", "registrations")}
        self.rows = self.family["index"]["records"]
        self.anchors = {a["id"]: a for a in self.family["inventory"]["anchors"]}
        self.refs = {r["id"]: r for r in self.family["xrefs"]["references"]}
        self.closed = inputs.read(s.overlay.PHASE2A_MAP_PATH)["records"]
        self.maps = lane_maps(effective, self.closed)
        self.sep_document = inputs.read(s.C / "september-pairs.json")
        self.sep = {r["donor_start"]: r for r in self.sep_document["trust_dispositions"] if r["disposition"].startswith("retained-")}
        self.delta = inputs.read(s.E / "evidence/approved-overlay-delta.json")
        self.actions = {r["phase2d_ledger_id"]: r for r in self.delta["actions"] if r["action"] == "add-mapping"}
        self.by_role = collections.defaultdict(list)
        self.by_function = collections.defaultdict(list)
        for ref in self.refs.values():
            self.by_role[(ref["build"], ref["function"]["start"], historical_c.role_key(ref))].append(ref)
            self.by_function[(ref["build"], ref["function"]["start"])].append(ref)
        self.images = {}
        # The upstream source graph has already authenticated these extracted
        # sections. load_build additionally checks each manifest block hash.
        for build in historical_b.BUILDS:
            _, blocks, _ = historical_b.phase2a.load_build(s.ROOT / historical_b.DERIVED, build)
            self.images[build] = native.Image(build, blocks)
        self.objects = {}
        self.packets = []

    def obj(self, ref):
        key = (ref["build"], ref["anchor_address"])
        if key not in self.objects:
            self.objects[key] = historical_c.object_at(self.images[key[0]], int(key[1], 16))
        return self.objects[key]

    def owner(self, build, start, mapping):
        secondary = self.sep.get(start) if build == "sep-2008" else None
        middle = secondary["target_start"] if secondary else start if build == DONOR else None
        pair = mapping.get(middle)
        edges = []
        if secondary:
            edges.append({"id": secondary["id"], "donor": start, "target": middle, "role": "owner",
                          "source": "september-trust", "generation": 0, "reservations": [],
                          "provenance": {"source": (s.C / "september-pairs.json").as_posix(),
                                         "original_record_index": secondary["original_record_index"],
                                         "status": secondary["disposition"]}, "mapping_dependencies": []})
        if pair:
            edges.append(edge(pair))
        return middle, pair, edges

    def historical(self):
        """Recompute historical policies; no closed writer/branch bypass."""
        historical_b.validate_family(self.family, self.closed)
        mappings = {r["donor_start"]: (i, r) for i, r in enumerate(self.closed)}
        replay = []
        for original in self.rows:
            row = copy.deepcopy(original)
            anchor = self.anchors[row["anchor_id"]]
            start = row["donor_function"]["start"] if row["donor_function"] else None
            item = mappings.get(start) if row["build"] == DONOR else None
            row["mapping"] = {"source": s.overlay.PHASE2A_MAP_PATH.as_posix(), "record_index": item[0], "record": item[1]} if item else None
            support, conflicts = [], []
            if item:
                for ref_id in row["donor_xrefs"]:
                    ref = self.refs[ref_id]
                    occurrences = [o for o in anchor["occurrences"] if o["build"] == row["build"] and o["address"] == ref["anchor_address"] and o["match"] == "exact"]
                    for _ in occurrences:
                        if ref["role"] != "call-argument":
                            continue
                        callee = mappings.get(ref["destination"])
                        for target in self.by_function[(TARGET, item[1]["target_start"])]:
                            if historical_c.role_key(ref)[:3] != historical_c.role_key(target)[:3]:
                                continue
                            exact = any(o["build"] == TARGET and o["match"] == "exact" and o["address"] == target["anchor_address"] for o in anchor["occurrences"])
                            if not exact:
                                conflicts.append({"kind":"different-literal-in-corresponding-call-argument", "donor_xref":ref_id, "target_xref":target["id"], "interpretation":"semantic-conflict-for-review-not-disproof-of-binary-correspondence"})
                            elif callee and target["destination"] != callee[1]["target_start"]:
                                conflicts.append({"kind":"mapped-callee-role-conflict", "donor_xref":ref_id, "target_xref":target["id"]})
                            elif callee:
                                support.append({"kind":"same-distinctive-anchor-same-argument-mapped-callee", "donor_xref":ref_id, "target_xref":target["id"], "callee_mapping_index":callee[0]})
            row["target_corroboration"] = sorted(support, key=s.payload)
            row["contradictions"] = sorted(conflicts, key=s.payload)
            duplicates = len({o["address"] for o in anchor["occurrences"] if o["build"] == row["build"]}) > 1 and "generic-string" in anchor["categories"]
            row["status"], row["reason"] = historical_b.grade(filtered=bool(anchor["filters"]), donor_refs=row["donor_xrefs"], mapping=item[1] if item else None,
                corroboration=support, contradictions=conflicts, ambiguous=duplicates and bool(row["donor_xrefs"]))
            s.require(row == original, "Historical Phase 2B policy mismatch: " + row["id"])
            replay.append(row)
        b_doc = dict(self.family["index"], records=replay)
        s.require(s.payload(b_doc) == (s.ROOT / s.B / "semantic-index.json").read_bytes(), "Historical B bytes")
        c_outputs = []
        for mapping_root, name in ((s.C, "semantic-v2.json"), (s.C / "completion", "semantic-final.json")):
            generated = historical_c.semantic_stage(self.images, mapping_root)
            original = self.inputs.read(mapping_root / name)
            s.require(s.payload(generated) == (s.ROOT / mapping_root / name).read_bytes(), "Historical C bytes: " + name)
            c_outputs.append({"source": self.inputs.ref(mapping_root / name, ""), "counts": generated["counts"], "records": generated["records"]})
        return {"phase2b": {"source": self.inputs.ref(s.B / "semantic-index.json", ""), "records": replay,
                            "counts": {"records": len(replay), "statuses": counts(replay, "status"), "joined": sum(r["mapping"] is not None for r in replay)}},
                "phase2c": c_outputs, "reproduction": "byte-identical-original-envelopes; independently-recomputed-B-policy-and-original-pure-C-policy"}

    def route(self, row, mapping, historical=False):
        start = row["donor_function"]["start"] if row["donor_function"] else None
        middle, pair, owners = self.owner(row["build"], start, mapping)
        owned = start is not None
        if pair and row["build"] == DONOR and row["donor_function"]["end_exclusive"] != pair["donor_end_exclusive"]:
            owned, pair, owners = False, None, []
        s.require(len(owners) <= 2, "Owner route depth exceeded")
        proofs, conflicts, rejected = [], [], []
        if pair:
            for ref_id in row["donor_xrefs"]:
                ref = self.refs[ref_id]
                mids = self.by_role[(DONOR, middle, historical_c.role_key(ref))] if row["build"] == "sep-2008" else [ref]
                for mid in mids:
                    a, m = self.obj(ref), self.obj(mid)
                    if historical_c.identity_token(a) is None or historical_c.identity_token(a) != historical_c.identity_token(m):
                        continue
                    for target in self.by_function[(TARGET, pair["target_start"])]:
                        b = self.obj(target)
                        same_role = historical_c.role_key(ref) == historical_c.role_key(target)
                        same_offset = historical_c.role_key(ref)[0] == historical_c.role_key(target)[0]
                        equal = historical_c.identity_token(a) == historical_c.identity_token(b)
                        if not same_role and not (equal and same_offset):
                            continue
                        callee = mapping.get(mid["destination"])
                        callee_ok = ref["role"] == "call-argument" and callee is not None and callee["target_start"] == target["destination"]
                        secondary_callee = self.sep.get(ref["destination"]) if row["build"] == "sep-2008" else None
                        if row["build"] == "sep-2008":
                            callee_ok = callee_ok and secondary_callee is not None and secondary_callee["target_start"] == mid["destination"]
                        action = self.actions.get(pair["id"])
                        consumed = bool(action and any(x["identity"][3] == a.get("full_sha256") for x in action["reference_identity_summaries"]))
                        helpers = any("common" in r for r in pair["reservations"])
                        gate = evidence_gate(complete=historical_c.identity_token(b) is not None, equal=equal,
                            compatible_role=same_role, readonly=not self.images[TARGET].block(int(target["anchor_address"],16)).write,
                            interior=a.get("pointer_relation") != "start" or b.get("pointer_relation") != "start",
                            empty=not a.get("length_bytes"), canonicalized=consumed,
                            common=helpers or bool(self.anchors[row["anchor_id"]]["filters"]), independent_callee=callee_ok,
                            contradiction=same_role and historical_c.identity_token(b) is not None and not equal)
                        packet = {"donor_xref": ref_id, "middle_xref": mid["id"], "target_xref": target["id"],
                                  "donor_instruction": ref["instruction"], "target_instruction": target["instruction"],
                                  "donor_object": a, "target_object": b, "role": list(historical_c.role_key(ref)),
                                  "target_role": list(historical_c.role_key(target)), "gate": gate,
                                  "canonicalization_consumed": consumed, "callee_corresponds": bool(callee_ok)}
                        if gate == "conflict":
                            conflicts.append(packet)
                        elif equal:
                            proof_edges = list(owners)
                            if callee_ok:
                                proof_edges.append(edge(callee, "literal-consumer-callee"))
                                if secondary_callee:
                                    proof_edges.append({"id":secondary_callee["id"], "donor":ref["destination"], "target":mid["destination"],
                                        "role":"literal-consumer-callee", "source":"september-trust", "generation":0, "reservations":[],
                                        "provenance":{"status":secondary_callee["disposition"]}, "mapping_dependencies":[]})
                            proofs.append({"edges": proof_edges, "reservations": reservations(proof_edges),
                                           "independent": gate == "independent", "evidence": packet})
                        else:
                            rejected.append(packet)
            # A base owner route is always represented, even if every target
            # evidence candidate is rejected or no target reference exists.
            proofs.append({"edges":owners, "reservations":reservations(owners), "independent":False, "evidence":None})
        proofs = sorted({s.payload(p):p for p in proofs}.values(), key=s.payload)
        primary = primary_route(proofs)
        all_edges = {e["id"]:e for p in proofs for e in p["edges"]}
        if not historical:
            for e in all_edges.values():
                s.require(SUPPRESSIONS.get(e["donor"]) != e["target"], "Suppressed dependency survived")
                for dependency in e["mapping_dependencies"]:
                    actual = mapping.get(dependency["donor"])
                    s.require(actual and actual["target_start"] == dependency["target"] and actual["generation"] < e["generation"], "Missing or same-generation mapping dependency")
        reserved = reservations(list(all_edges.values()))
        used_additions = sorted(e["id"] for e in all_edges.values() if e["generation"] > 0)
        grade = terminal_grade(owned=owned, routed=bool(pair), suppressed=middle in SUPPRESSIONS,
            conflicts=bool(conflicts), independent=any(p["independent"] for p in proofs),
            reserved=bool(primary and primary["reservations"]), addition=bool(primary and any(e["generation"] > 0 for e in primary["edges"])))
        return {"terminal_id": row["id"], "anchor_id": row["anchor_id"], "build": row["build"], "donor_start":start,
                "target_start":pair["target_start"] if pair else None, "grade":grade,
                "route_kind":route_kind(primary["edges"]) if primary else grade,
                "routes":proofs, "primary_route":proofs.index(primary) if primary else None,
                "reservations":reserved, "used_additions":used_additions,
                "conflicts":conflicts, "rejected_target_evidence":rejected,
                "category":category(self.anchors[row["anchor_id"]]["spelling"]),
                "filters":self.anchors[row["anchor_id"]]["filters"], "canonical_function_name":None,
                "reason":{
                    "target-corroborated":"Compatible complete target-native literal role and corresponding callee; mapping-consumed/low-entropy evidence excluded; all reservation provenance retained.",
                    "transported-context-reserved":"Approved route with inherited reservations; no independent target-semantic proof.",
                    "transported-context-unreserved":"Unreserved approved owner route; no independent target-semantic proof.",
                    "target-unconfirmed":"Closed owner route exists, but independent target-role/callee evidence is insufficient.",
                    "semantic-conflict-quarantined":"Incompatible complete target-native literal or role overrides donor similarity; overlay unchanged.",
                    "suppression-blocked":"B00 removed the historical owner mapping and no included same-semantic replacement exists.",
                    "mapping-blocked":"No included approved owner route; no held, probable, physics or fallback edge allowed.",
                    "ownership-or-boundary-blocked":"No proven native donor owner or its complete boundary is incompatible with the mapping."
                }[grade]}

    def lane(self, name):
        records = [self.route(r, self.maps[name], name == "H-2A") for r in self.rows]
        s.require(len(records) == 51657 and len({r["terminal_id"] for r in records}) == 51657, "Terminal reconciliation")
        return {"lane":name, "mapping_count":len(self.maps[name]), "mapping_set_sha256":s.digest(s.payload(sorted(r["id"] for r in self.maps[name].values()))),
                "records":records, "counts":{"terminals":len(records), "grades":{g:sum(r["grade"] == g for r in records) for g in GRADES},
                "routable":sum(r["target_start"] is not None for r in records), "route_kinds":counts(records,"route_kind"),
                "owner_route_lengths":dict(sorted(collections.Counter(len([e for e in r["routes"][r["primary_route"]]["edges"] if e["role"] == "owner"]) if r["primary_route"] is not None else 0 for r in records).items()))}}
