# Phase 2F offline reproduction

Run from the repository root on `fable2-prototype-archaeology-phase2f`. The exact prebranch state was verified before any Phase 2F edit: Phase 2E `1f9c0088bdc6f056ab62c63f7e044d06dcda4e03`, tree `d22010cae1109d07a3fe77aa1a1369ca667bebde`, clean index/worktree, terminal subject `Document Phase 2E opt-in rollback and handoff`. Source pins preserve the remote sets and exact SDK state. Do not recreate or move the frozen Phase 2E branch.

Every analysis invocation rehashes the frozen source graph and invokes the exact Phase 2E programmatic opt-in contract with its version, three repository-relative paths and all three expected hashes. Invalid selection refuses without fallback. No network is used. No game, SDK build, code generation, Lua execution or production change is part of this workflow.

Generate only Phase 2F derived evidence, then run the complete supported verifiers, test discovery and replay:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
python -B tools/phase2f/Fable2SemanticSources.py
python -B tools/phase2f/Fable2SemanticAudit.py
python -B tools/phase2f/VerifyFable2SemanticAudit.py checks
python -B tools/phase2f/VerifyFable2SemanticAudit.py tests
python -B tools/phase2f/VerifyFable2SemanticAudit.py negatives
python -B tools/phase2f/VerifyFable2SemanticAudit.py replay
python -B tools/phase2f/VerifyFable2SemanticAudit.py finalize
```

Read-only verification of an existing result:

```powershell
python -B tools/phase2f/Fable2SemanticSources.py --check
python -B tools/phase2f/Fable2SemanticAudit.py --check
python -B tools/phase2f/VerifyFable2SemanticAudit.py verify
python -B tools/phase2f/VerifyFable2SemanticAudit.py git-audit
git diff --check
```

The existing default adapter remains unchanged:

```powershell
python -B tools/phase2e/Fable2PrototypeOverlayConsumer.py default
python -B tools/phase2e/Fable2PrototypeOverlayConsumer.py opt-in `
    --overlay-version phase2e-v1 `
    --decision docs/fable2-prototype-archaeology/phase2e/evidence/owner-decision.json `
    --decision-sha256 7905EDD55A1DDA53C7FDD1D36635FFC7E6315F1BA66F2CB88393A3E5F6F766BD `
    --delta docs/fable2-prototype-archaeology/phase2e/evidence/approved-overlay-delta.json `
    --delta-sha256 BD53722F709EB2BB287482DE09E2D6953EAD19DDA675E1B1C34DEBA55D2D52BC `
    --effective-map out/prototype-archaeology/phase2e/effective-map.json `
    --effective-map-sha256 E3EE02E659ADCBD79823B3343A542505B45B8B902BAADD158A2A75D577E71663
```

`checks` reruns the closed Phase 1–2D verifier suite and read-only Phase 2E decision/delta/binding/materialization/finalization checks. Only the historical Git-delta query is scoped to its frozen end commit; every descendant path is separately checked against the exact Phase 2F allowlist. No frozen generator, parser, schema or expected evidence is edited. `tests` discovers the entire supported `tests` tree, including frozen regressions. The six inherited blockers are retained rather than converted into passing historical ownership replay.

`analysis-summary.json` freezes the analytical stage; committed `route-summary.json` adds deterministic verification receipts. The report, summary, validation envelope and actual ignored bytes are checked three ways. The validation envelope binds implementation, documentation and receipts without circularly hashing itself. Input junctions remain lexical repository-relative, authenticated to their frozen byte hashes; physical output paths must remain under the two Phase 2F evidence roots.

The tooling assumes the ignored, already-bound corpus exists. A missing or changed Phase 1–2E input is a stop condition, not permission to regenerate or rebind it. Analysis can take several minutes and produces large ignored JSON indexes. No proprietary payload is committed.
