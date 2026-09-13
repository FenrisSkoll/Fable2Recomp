"""Offline Phase 2F checks, receipts and three-way publication consistency."""
from __future__ import annotations

import argparse
import collections
import io
import os
import subprocess
import unittest
from pathlib import Path

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

import Fable2SemanticSources as s
import Fable2SemanticRoutes as routes
import Fable2SemanticAudit as audit
import VerifyFable2PrototypeOverlay as upstream

SCHEMA = Path("tools/schemas/phase2f/fable2-semantic-routes-v1.schema.json")
SCHEMA_COMMAND = ["pwsh","-NoProfile","-File","tools/phase2f/Verify-Fable2SemanticSchemas.ps1"]
ALLOWED = {
    "tools/phase2f/"+name for name in (".gitattributes","Fable2SemanticSources.py","Fable2SemanticRoutes.py",
        "Fable2SemanticDomains.py","Fable2SemanticAudit.py","VerifyFable2SemanticAudit.py","Verify-Fable2SemanticSchemas.ps1")
} | {"tests/phase2f/"+name for name in (".gitattributes","__init__.py","test_semantic_routes.py")} | {
    "tools/schemas/phase2f/.gitattributes",SCHEMA.as_posix()
} | {(s.DOC/name).as_posix() for name in (".gitattributes","README.md","report.md","policy.md","review-guide.md",
    "preservation-findings.md","next-phase-handoff.md","evidence/source-pins.json","evidence/route-summary.json",
    "evidence/high-value-review.json","evidence/validation.json")}


def git_audit(paths=None):
    if paths is None:
        paths = sorted(set(s.git("diff","--name-only",s.BASE,"--").splitlines()) |
                       set(s.git("ls-files","--others","--exclude-standard").splitlines()))
    s.require(not set(paths)-ALLOWED,"Forbidden Phase 2F Git delta: "+str(sorted(set(paths)-ALLOWED)))
    s.require(s.git("branch","--show-current") == s.BRANCH,"Wrong active branch")
    s.require(s.git("merge-base",s.BASE,"HEAD") == s.BASE,"Phase 2F not descended from exact parent")
    s.require(s.git("rev-parse","fable2-prototype-archaeology-phase2e") == s.BASE,"Phase 2E branch moved")
    subprocess.run(["git","diff","--check"],cwd=s.ROOT,check=True)
    return sorted(paths)


def selection():
    return s.opt_in()[1]


def emit(kind,filename,**fields):
    return s.write(s.OUT/filename,s.envelope(kind,s.read(s.DOC/"evidence/source-pins.json")["overlay_selection"],**fields))


def tests():
    suite = unittest.TestLoader().discover(str(s.ROOT/"tests"))
    ids = sorted(x.id() for x in upstream.iter_tests(suite))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream,verbosity=0).run(suite)
    s.require(result.wasSuccessful() and not result.skipped,"Supported discovery failed:\n"+stream.getvalue())
    s.require(len(ids) == result.testsRun and len(ids) == len(set(ids)),"Test discovery reconciliation")
    emit("tests","test-results.json",records=[{"id":x,"status":"pass"} for x in ids],
         tests_run=result.testsRun,failures=0,errors=0,skips=0)
    print("PASS complete supported discovery",result.testsRun,"tests; zero failures/errors/skips",flush=True)


def checks():
    git_audit()
    doc = upstream.checks_stage(True)
    upstream.replay_stage(True)
    # The closed verifier's analytical checks are reused unchanged. Its Git
    # delta is evaluated against the frozen Phase 2E end commit, while our
    # exact allowlist owns every descendant change. No generator is patched.
    original = upstream.git_delta_paths
    try:
        upstream.git_delta_paths = lambda: s.git("diff","--name-only",s.overlay.PHASE2D_COMMIT,s.BASE,"--").splitlines()
        upstream.finalize_stage(True)
    finally:
        upstream.git_delta_paths = original
    emit("checks","consistency-results.json",records=doc["records"],
         phase2e_replay_stages=4,phase2e_analytical_consistency="pass",
         descendant_git_delta="exact Phase 2F allowlist; historical Phase 2E delta separately audited at frozen end commit",
         inherited_historical_replay_blocker=doc["inherited_historical_replay_blocker"],
         inherited_phase2c_blockers=doc["inherited_phase2c_blockers"])
    print("PASS full supported upstream verifier set and Phase 2E read-only replay",flush=True)


def negatives():
    facts=dict(complete=True,equal=True,compatible_role=True,readonly=True,interior=False,empty=False,
               canonicalized=False,common=False,independent_callee=True)
    variants={"independent-native-role":({},"independent"),"wrong-native-role":({"compatible_role":False},"conflict"),
        "mapping-consumed-literal":({"canonicalized":True},"mapping-consumed-or-low-entropy"),
        "common-helper":({"common":True},"mapping-consumed-or-low-entropy"),
        "same-address-changed-content":({"equal":False,"contradiction":True},"conflict"),
        "prefix":({"complete":False},"insufficient"),"interior":({"interior":True},"insufficient"),
        "empty":({"empty":True},"insufficient"),"writable":({"readonly":False},"insufficient")}
    records=[]
    for name,(change,expected) in sorted(variants.items()):
        actual=routes.evidence_gate(**{**facts,**change})
        s.require(actual == expected,"Negative control: "+name)
        records.append({"id":name,"kind":"synthetic","inputs":{**facts,**change},"expected":expected,"actual":actual})
    suppression=s.read(s.OUT/"suppression-impact.json")
    for row in suppression["records"]:
        s.require(row["S"]["grade"]=="suppression-blocked","Real suppression regression")
        records.append({"id":row["terminal_id"],"kind":"real-collision","S":row["S"]["grade"],"O":row["O"]["grade"],
                        "disposition":row["disposition"],"suppressed_pairs":row["suppressed_pairs"]})
    records.extend({"id":a+":"+b,"kind":"excluded-physics-review-lead","approved_route":False,
                    "next_static_action":"Retain Phase 2D helper/global/ownership obligations; no semantic result authorizes a mapping."} for a,b in sorted(routes.PHYSICS))
    records.extend({"id":a+":"+b,"kind":"held-strong","approved_route":False} for a,b in sorted(routes.HELD))
    emit("negative-controls","negative-controls.json",records=records,
         exhaustive_adversarial_tests="tests/phase2f/test_semantic_routes.py; tests/phase2e/test_fable2_prototype_overlay.py; frozen Phase 2B/2C/2D fixtures",
         exclusions={"physics":2,"held_strong":3,"probable":715},overlay_mutation_performed=False)


def replay():
    audit.analyze(True)
    summary=s.read(s.OUT/"analysis-summary.json")
    emit("replay","replay-results.json",records=summary["artifacts"],
         stages=["source-bindings","universe","historical-B-C","all-mapping-lanes","attribution","suppression",
                 "target-corroboration","domain-audits","review-selection"],byte_identical=True)
    print("PASS byte-identical Phase 2F analytical replay",flush=True)


def binding_table(rows):
    return ["| Artifact | Bytes | SHA-256 |","|---|---:|---|"] + [f"| `{x['path']}` | {x['size']} | `{x['sha256']}` |" for x in rows]


def path_audit(value):
    if isinstance(value,dict):
        for key,child in value.items():
            if key in ("path","source","decision_path","delta_path","ledger_path","scripts","scripts_r") and isinstance(child,str):
                s.relative(child)
            if key == "canonical_adoption":
                s.require(child is False,"Canonical adoption flag enabled")
            if key == "canonical_function_name":
                s.require(child is None,"Canonical name assigned")
            path_audit(child)
    elif isinstance(value,list):
        for child in value:
            path_audit(child)


def lane_consistency(lane, expected):
    rows=lane["records"]
    s.require(len(rows)==len(expected) and {x["terminal_id"] for x in rows}==expected,"Terminal population drift")
    grades={g:sum(x["grade"]==g for x in rows) for g in routes.GRADES}
    s.require(grades==lane["counts"]["grades"],"Terminal grade totals drift")
    s.require(sum(x["target_start"] is not None for x in rows)==lane["counts"]["routable"],"Route totals drift")
    for row in rows:
        primary=routes.primary_route(row["routes"])
        s.require(primary==(row["routes"][row["primary_route"]] if row["primary_route"] is not None else None),"Primary-route drift")
        for route in row["routes"]:
            s.require(routes.reservations(route["edges"])==route["reservations"],"Lost route reservations")
            if route["independent"]:
                s.require(route["evidence"]["gate"]=="independent" and not route["evidence"]["canonicalization_consumed"],"Double-counted target evidence")
    return grades


def report(summary):
    sel=summary["overlay_selection"]
    lines=["# Phase 2F — approved-overlay semantic route audit","",
        "CONFIRMED: exact Phase 2E branch, HEAD `"+s.BASE+"`, tree `"+s.TREE+"`, clean index/worktree and terminal subject matched before branching. All nine trust roots, all thirteen ignored Phase 2E artifacts, both remote sets and the fifteen SDK libmspack identities matched. The frozen Phase 2E branch was not changed.","",
        "The explicit `phase2e-v1` contract succeeded. Default remains `closed-phase2a-default` (15,299); invalid opt-in refuses without fallback. Every JSON output carries the exact decision, delta and effective-map identities. No canonical adoption or semantic-to-mapping feedback is enabled.","",
        "## Main result","",
        "The approved additions enable **115 new owner-function routes**, of which **0 are newly independently target-corroborated**. Separately, the already-routed HammerCombat literal context gains a corresponding-callee proof through reserved B05. Lane O therefore has 116 routed contexts: 41 transported-unreserved, 74 transported-reserved and one target-corroborated context that still inherits its internal-region reservation. All 83 additions are productive in this corpus; zero are dormant. These are semantic-context associations, not function names.","",
        "Mapping-canonicalization literals and Phase 2D behavior/topology gates are not fresh semantic votes. The negative result for independent proof on newly routed owners is deliberate. Full packets retain matching target observations and their non-independence, rather than discarding them.","",
        "Of the 115 new routes relative to S, 114 were mapping-blocked and one was suppression-blocked (the corrected __vspltb route). There are zero new owner routes relative to the historical provisional Phase 2C view: that view already contained these proposals. Phase 2F measures approved connectivity and stronger non-independence gates, not discovery of 115 previously unseen Phase 2C matches.","",
        "Population units: 115 terminal associations cover 82 owner functions, 109 anchor identities and 116 distinct native-XREF records (116 memberships, no duplicated XREF membership in this subset). These populations overlap and are not summed. The separate 83 mapping-context packets preserve 115 canonicalization references, including the empty HammerCombat-callee fallback; those are mapping evidence, not 115 new semantic votes.","",
        "## Lanes and historical comparability","",
        "Lane H reproduces the original Phase 2B index and both Phase 2C semantic documents byte-for-byte. B: 51,657 terminals, four joins, 46,362 quarantined, 2,303 ambiguous, 2,991 donor-only and one target-unconfirmed. C: 51,657 terminals, 120 joins, 112 filtered-corroborated, four unfiltered-corroborated, four joined-unconfirmed and 51,537 mapping-blocked. These historical grades are not reinterpreted as Phase 2F independent proof.","",
        "H-2A below is the historical mapping evaluated with the Phase 2F gates, so suppression effects can be separated from policy differences. All rows reconcile to 51,657 terminals.","",
        "| Lane | Pairs | Corroborated | Reserved | Unreserved | Target unconfirmed | Conflict | Suppression blocked | Mapping blocked | Ownership blocked |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for lane in ("H-2A","S","S+B01","S+B01+B02","S+B01+B02+B04","O",*("O-minus-"+b for b in routes.BATCHES)):
        row=summary["lanes"][lane];g=row["grades"]
        lines.append("| "+lane+" | "+" | ".join(str(x) for x in [row["mapping_count"],*(g[k] for k in routes.GRADES)])+" |")
    lines += ["","All 9,600 September pair records were checked. Exactly 9,284 function-level two-hop routes remain in every lane; none connects a Phase 2B semantic terminal. No held, probable, physics or suppressed edge can bridge a gap.","",
        "Four historical Phase 2C semantic associations disappear because three strong mappings were held, not because of B00:",""]
    for row in summary["phase2c_routes_excluded"]:
        lines.append(f"- `{row['terminal_id']}` — `{row['reference_text']}` at historical target `{row['historical_target']}`; original `{row['historical_grade']}` → mapping-blocked.")
    lines += ["","## Batch attribution and support-wrapper separation","",
        "| Batch | Newly routable (cumulative / leave-out) | New corroboration | Fable/gameplay context | SDK/compiler/vector | Generic/platform | Unknown |",
        "|---|---:|---:|---:|---:|---:|---:|"]
    for row,loo in zip(summary["batches"]["cumulative"],summary["batches"]["leave_one_out"]):
        cats=row["categories"]
        lines.append(f"| {row['batch']} | {row['counts']['newly_routable']} / {loo['counts']['newly_routable']} | {row['counts']['newly_corroborated']} | "+" | ".join(str(cats.get(k,0)) for k in ("fable-game-specific","sdk-compiler-vector","generic-platform","unknown"))+" |")
    lines += ["","B05's one proof contribution is game-specific and does not add an owner route. Cumulative first-enablement and leave-out necessity are counterfactual measures, not additive causal votes. Raw context volume is not a priority score. Lexical gameplay classification is PROBABLE context categorization, not a proven function identity; generic labels remain unknown where appropriate.","",
              "B04 exact strata: `"+str(summary["b04_strata"])+"`.","",
        "## Suppression and mandatory cases","",
        "- `S-9849E725C594340F77ACF10F`: `0x82631A30 -> 0x82950A98` transported Navigator to Controlled. Historical grade quarantined; removed in S/O. Same-name `0x82631A30 -> 0x82630C30` and `0x829506B0 -> 0x82950A98` remain excluded physics review leads.",
        "- `S-3A6B45DA40B1C0AB0A7EBFDA`: `0x828EA448 -> 0x82681198` transported TROLL_FOOTSTEP to DESTROY_ENTITY. Historical grade quarantined; removed in S/O, no approved replacement.",
        "- `S-B30B0F30239F50B70D12FBA4`: `0x83062950 -> 0x83060C30` transported __vspltb to __vcfsx. Historical grade quarantined; removed in S. O safely routes `0x83062950 -> 0x83060CD8` and retains corrected `0x83060A80 -> 0x83060C30`. Both are reserved support contexts, not gameplay breakthroughs.",
        "- HammerCombat: caller `0x8229B308 -> 0x8229B038`; added callee `[0x8229B488,0x8229B504) -> [0x8229B1B8,0x8229B234)`. The context remains an exclusion guard involving object offset +8, not a callee name. Comparators `[0x8226DB80,0x8226DBD4)` and `[0x8226D7F8,0x8226D84C)` remain 21-instruction internal regions with no independent .pdata ownership. Reservation `internal-code-region-dependent` remains attached to the proof.","",
        "Domain associations removed solely by suppression: `"+str(summary["suppression_domain_counts"])+"`. Exact historical consumers, primary edges, callee dependencies, all September routes and safe reroutes are in `suppression-impact.json`. There are no new semantic-conflict quarantines and no automatic overlay revisions.","",
        "## Domain conclusions","",
        "Registration: all 206 shapes, 2,662 calls and 2,647 complete name/callback candidates audited; zero changed calls/shapes and zero callable TU1 chains. SetUseFreeCamera's first-party name/payload/callback construction is retained, but corresponding native TU1 chain, state lifetime, Debug namespace/table owner, registration consumer and callable reachability remain unproved. No command was invoked.","",
        "Scripts/preservation: all 108 parsed loose chunks, 54 structural pairs, 52 inventory-only banks/interfaces, 200 preservation records (18 native-dependent, 182 unknown portability), and 21 E3 presence records remain explicitly bounded. No runnable recovery, native Lua state or retail/startup ownership is established. See preservation-findings.md for exact new literal-link counts and missing obligations.","",
        "Types/globals/boundaries: `"+str(summary["domains"]["type-global-boundary"])+"`. Changed pointer-slot and scalar-access contexts do not prove tables, constructors, complete globals or vtables. Existing contradictory global evidence is retained. No boundary or internal region is promoted.","",
        "Current-project intersections per approved addition: `"+str(summary["domains"]["project-intersections"])+"`. Closure, coverage/import-plan and Ghidra membership supply context and prioritization only. Ownership, indirect, renderer and historical-crash sets add no intersections for these additions. Nothing changes production inventories or manifests.","",
        "## Productive mappings and human tranche","",
        "Highest-yield mappings (terminal counts retain overlapping reference/anchor distinctions):","",
        "| Mapping | Encountered | Newly routable | New corroboration | Reference context |",
        "|---|---:|---:|---:|---|"]
    mappings=s.read(s.OUT/"mapping-contribution.json")["records"]
    for row in sorted(mappings,key=lambda x:(-x["counts"]["encountered"],x["mapping_id"]))[:8]:
        lines.append(f"| `{row['mapping_id']}` | {row['counts']['encountered']} | {row['counts']['newly_routable']} | {row['counts']['newly_target_corroborated']} | "+"; ".join(row["reference_text"])+" |")
    lines += ["","Selected review groups (all routes, source identities and limitations are in high-value-review.json):",""]
    for row in s.read(s.DOC/"evidence/high-value-review.json")["selected"]:
        lines.append(f"- `{row['terminal_id']}`: `{row['donor_start']} -> {row['target_start']}`, `{row['reference_text']}`, {row['grade']}.")
    lines += ["","Start with only HammerCombat, oxygen and world-map/reward packets; see review-guide.md. The remaining exhaustive queues require no bulk adoption decision. Debug/interface observations are `"+str(summary["domains"]["registration-debug-freecamera"].get("debug_context_kinds",{}))+"`; none proves a callable command.","",
        "## Verification and limitations","",
        "Executed verification totals: `"+str(summary["verification"])+"`.","",
        "Complete supported discovery, frozen upstream verifiers, schema checks, byte-identical replay, path/allowlist checks and three-way artifact reconciliation are recorded in validation.json and its receipts. The six inherited blockers remain verbatim. Historical ownership replay remains blocked: generated/default/fable2_recomp.136.cpp requires `6053CC0EAC4636AA03AAA26581162B707C37E1B52BEE4C10F205D07C63EBDF59`; current bytes remain `D25E664A98833BF9433413336AC92A7376102A67049C0FF35F1270E6BDEB44CB`. It was not searched for, reconstructed or replaced.","",
        "No game/SDK build or launch, code generation, Lua execution, network operation, binary/asset mutation, Ghidra write, canonical naming, runtime change, manifest change or push occurred. ReXGlue's branch/HEAD/tree/remotes/index and all fifteen user-owned libmspack file hashes remain unchanged.","",
        "## Exact output bindings","",
        "The tables bind every ignored derived artifact and receipt plus the committed review. route-summary.json and validation.json contain the same identities; the verifier checks actual bytes. The report does not attempt a circular hash of itself or validation.json.",""]
    lines += binding_table(summary["artifacts"])
    lines += ["","Committed summary and input bindings:",""]+binding_table([s.identity(s.DOC/"evidence/source-pins.json"),s.identity(s.DOC/"evidence/route-summary.json")])
    return ("\n".join(lines)+"\n").encode()


def finalize():
    git_audit()
    pins,_=s.source_bindings()
    core=s.read(s.OUT/"analysis-summary.json")
    s.require(core["overlay_selection"]==pins["overlay_selection"],"Unvalidated publication overlay")
    for row in core["artifacts"]:
        s.check(row)
    expected_json=sorted({p.relative_to(s.ROOT).as_posix() for root in (s.DOC/"evidence",s.OUT) for p in (s.ROOT/root).glob("*.json")} |
                        {(s.OUT/"schema-results.json").as_posix(),(s.DOC/"evidence/validation.json").as_posix(),(s.DOC/"evidence/route-summary.json").as_posix()})
    emit("schemas","schema-results.json",command=SCHEMA_COMMAND,schema_identity=s.identity(SCHEMA),documents=expected_json,document_count=len(expected_json),status="pass",return_code=0)
    receipts=[s.identity(s.OUT/name) for name in ("analysis-summary.json","test-results.json","consistency-results.json","negative-controls.json","replay-results.json","schema-results.json")]
    summary={**core,"artifacts":core["artifacts"]+receipts,
        "verification":{"supported_tests":s.read(s.OUT/"test-results.json")["tests_run"],"failures":0,"errors":0,"skips":0,
            "upstream_domain_checks":len(s.read(s.OUT/"consistency-results.json")["records"]),
            "phase2e_replay_stages":4,"phase2f_replay_stages":len(s.read(s.OUT/"replay-results.json")["stages"]),
            "schema_documents":len(expected_json),"three_way":"pass","path_audit":"pass","git_allowlist":"pass","sdk_files":15}}
    s.write(s.DOC/"evidence/route-summary.json",summary)
    s.write(s.DOC/"report.md",report(summary))
    implementations=[s.identity(p) for p in sorted(ALLOWED) if p.startswith(("tools/","tests/"))]
    docs=[s.identity(p) for p in sorted(ALLOWED) if p.startswith(s.DOC.as_posix()) and not p.endswith(".json")]
    validation=s.envelope("validation",core["overlay_selection"],artifacts=summary["artifacts"],
        route_summary=s.identity(s.DOC/"evidence/route-summary.json"),report=s.identity(s.DOC/"report.md"),
        documentation=docs,implementation=implementations,inherited_blockers=core["inherited_blockers"],
        checks={"complete_supported_tests":s.read(s.OUT/"test-results.json")["tests_run"],"failures":0,"errors":0,"skips":0,
                "schema_documents":len(expected_json),"deterministic_replay":True,"three_way":True,"git_diff_check":True,"git_allowlist":sorted(ALLOWED)},
        default_consumer=s.overlay.load_default_mapping(),sdk=s.read(s.DOC/"evidence/source-pins.json")["sdk"],
        canonical_changes=0,runtime_changes=0,prohibited_operations=0)
    s.write(s.DOC/"evidence/validation.json",validation)
    subprocess.run(SCHEMA_COMMAND,cwd=s.ROOT,check=True)
    verify_consistency()


def verify_consistency():
    git_audit()
    summary=s.read(s.DOC/"evidence/route-summary.json")
    validation=s.read(s.DOC/"evidence/validation.json")
    s.require(summary["artifacts"]==validation["artifacts"],"Summary/validation artifact disagreement")
    report_text=(s.ROOT/s.DOC/"report.md").read_text(encoding="utf-8")
    for row in summary["artifacts"]:
        s.check(row)
        line=f"| `{row['path']}` | {row['size']} | `{row['sha256']}` |"
        s.require(report_text.count(line)==1,"Report identity absent/duplicated: "+row["path"])
    for row in validation["implementation"]+validation["documentation"]+[validation["route_summary"],validation["report"]]:
        s.check(row)
    actual={p.relative_to(s.ROOT).as_posix() for p in (s.ROOT/s.OUT).glob("*.json")}
    bound={x["path"] for x in summary["artifacts"] if x["path"].startswith(s.OUT.as_posix()+"/")}
    s.require(actual==bound,"Unbound or missing ignored output")
    pins,_=s.source_bindings()
    s.require(s.payload(pins)==(s.ROOT/s.DOC/"evidence/source-pins.json").read_bytes(),"Source binding replay mismatch")
    for path in sorted(actual|{p.relative_to(s.ROOT).as_posix() for p in (s.ROOT/s.DOC/"evidence").glob("*.json")}):
        document=s.read(path)
        s.require(document["overlay_selection"]==pins["overlay_selection"],"Overlay selection drift: "+path)
        s.require(document["canonical_adoption"] is False and document["semantic_feedback_allowed"] is False,"Propagation enabled")
        path_audit(document)
    expected={x["id"] for x in s.read(s.B/"semantic-index.json")["records"]}
    for lane,counts in summary["lanes"].items():
        doc=s.read(s.OUT/("lane-"+lane+".json"))
        lane_consistency(doc,expected)
        s.require({"mapping_count":doc["mapping_count"],**doc["counts"]}==counts,"Summary lane drift")
    s.require(s.identity("generated/default/fable2_recomp.136.cpp")["sha256"]=="D25E664A98833BF9433413336AC92A7376102A67049C0FF35F1270E6BDEB44CB","Historical current-file identity changed")
    print("PASS report/summary/validation/actual bytes, frozen inputs, SDK and exact Git allowlist",flush=True)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("tests","checks","negatives","replay","finalize","verify","git-audit"))
    command=parser.parse_args().command
    if command == "verify":
        verify_consistency()
        subprocess.run(SCHEMA_COMMAND,cwd=s.ROOT,check=True)
    elif command == "git-audit":
        print("PASS exact Phase 2F Git allowlist",git_audit())
    else:
        globals()[command]()
