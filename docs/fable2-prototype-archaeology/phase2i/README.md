# Phase 2I — opt-in analyst annotations

Phase 2I generates and previews read-only analyst annotations from frozen
Phase 2A/2E mapping and Phase 2F–2H semantic evidence. It never opens a Ghidra
project, emits a function/symbol name, changes a mapping, or modifies
runtime/production data.

## Validation and safe default

Run from `C:\Dev\Fable2Recomp` on
`fable2-prototype-archaeology-phase2i`:

```powershell
python -B tools/phase2i/Fable2AnalystSources.py --check
python -B tools/phase2i/Fable2AnalystAnnotations.py index --check
python -B tools/phase2i/VerifyFable2AnalystAnnotations.py verify
pwsh -NoProfile -File tools/phase2i/Verify-Fable2AnalystAnnotationSchemas.ps1
python -B -m unittest discover -s tests/phase2i -p "test_*.py"
git diff --check d9721cd72a98420eaa06548ee54a01c5a076fa62
```

With no command, the annotation tool prints help and writes nothing. Query
defaults are mapping `none` and semantics `none`; they expose no annotations:

```powershell
python -B tools/phase2i/Fable2AnalystAnnotations.py
python -B tools/phase2i/Fable2AnalystAnnotations.py query --address 0x82522C10
```

Exit codes are `0` for success with records (or a validation/help command), `1`
for a successful query/export with no records, `2` for invalid/partial/tampered
selection, and `3` for an internal frozen-evidence validation failure.

## Explicit mapping views

The unchanged closed Phase 2A map must be named explicitly:

```powershell
python -B tools/phase2i/Fable2AnalystAnnotations.py query `
    --mapping-view closed-phase2a-default `
    --address 0x8229B038
```

The Phase 2E view requires the exact version implied by `phase2e-v1`, paths and
hashes. The CLI spelling is:

```powershell
$p2eDecision = "docs/fable2-prototype-archaeology/phase2e/evidence/owner-decision.json"
$p2eDelta = "docs/fable2-prototype-archaeology/phase2e/evidence/approved-overlay-delta.json"
$p2eMap = "out/prototype-archaeology/phase2e/effective-map.json"

python -B tools/phase2i/Fable2AnalystAnnotations.py query `
    --mapping-view phase2e-v1 `
    --phase2e-decision $p2eDecision `
    --phase2e-decision-sha256 7905EDD55A1DDA53C7FDD1D36635FFC7E6315F1BA66F2CB88393A3E5F6F766BD `
    --phase2e-delta $p2eDelta `
    --phase2e-delta-sha256 BD53722F709EB2BB287482DE09E2D6953EAD19DDA675E1B1C34DEBA55D2D52BC `
    --phase2e-effective-map $p2eMap `
    --phase2e-effective-map-sha256 E3EE02E659ADCBD79823B3343A542505B45B8B902BAADD158A2A75D577E71663 `
    --address 0x82522C10
```

Use `--format json` for canonical machine-readable query output. Multiple
`--address` values are deduplicated and sorted. Exact and containing-range
matches are reported separately; donor addresses are never treated as TU1
identity merely because the same number occurs in both builds.

## Explicit semantic views

`phase2f-evidence` requires the exact Phase 2E selection above, then adds the
116 review contexts (115 newly routed plus the separate HammerCombat
strengthening). Every row remains `unreviewed-analysis-evidence`, including the
three rows with later Phase 2G static review dispositions.

`phase2h-v1` also requires the Phase 2E selection, plus all four exact Phase 2H
identities:

```powershell
$p2hPins = "docs/fable2-prototype-archaeology/phase2h/evidence/source-pins.json"
$p2hDecision = "docs/fable2-prototype-archaeology/phase2h/evidence/owner-decision.json"
$p2hDelta = "docs/fable2-prototype-archaeology/phase2h/evidence/semantic-correction-delta.json"
$p2hView = "out/prototype-archaeology/phase2h/materialized-reviewed-semantic-view.json"

# Append these arguments to the exact Phase 2E query above:
--semantic-view phase2h-v1 `
--phase2h-source-pins $p2hPins `
--phase2h-source-pins-sha256 81C38C88DB1B41E70AEC2B499B0378F1B5A9A3F2F95E3B9FC7CD751FB676B810 `
--phase2h-decision $p2hDecision `
--phase2h-decision-sha256 C08DD7C73BB790ED6BE7F113A32ED21EBD44FF9CA4523199B4128622C895D4D1 `
--phase2h-delta $p2hDelta `
--phase2h-delta-sha256 0D5DCA939AF9F0A2FD7B2DDC603FCE4BBFCE6B56A8EA67BB4C9985C6CCCF4F3F `
--phase2h-view $p2hView `
--phase2h-view-sha256 68BB58AB87D064F28C5616DEB3BE18749DE0D58BF3FAB5B161035E76650748EA
```

Partial, missing, wrong-path, wrong-version, wrong-hash, stale, altered, or
over-broad opt-ins refuse. No refusal is reported as a successful fallback.

## Profiles and export

Every export requires both `--profile` and a repository-relative `--output`
under `out/prototype-archaeology/phase2i/`. The committed driver reproduces all
required bound profiles with exact hashes:

```powershell
pwsh -NoProfile -File tools/phase2i/Invoke-Fable2AnalystExports.ps1
```

Profiles are:

- `address`: one or more explicit TU1 addresses;
- `phase2h-approved`: Packet C mapping, role, three corrections and rejection;
- `overlay-review`: 83 additions plus three suppression tombstones;
- `project-relevant`: the deduplicated closure/coverage/Ghidra union;
- `semantic-review`: all 116 Phase 2F review contexts;
- `all-correspondences`: every active selected mapping, requiring `--bulk`;
- `excluded-review`: optional warning-only view of 720 inactive proposals.

Each export directory contains `annotations.json`, `annotations.tsv`,
`ghidra-plan.json`, `rollback-manifest.json`, `preview.txt`, and
`export-receipt.json`. `--preview-limit` defaults to 100 and is constrained to
0–1000. The JSON bundle is canonical; TSV uses UTF-8 and LF; the Ghidra plan is
data-only and preview-only.

All writes are physically confined to Phase 2I documentation and ignored output
roots. No Phase 1–2H file is rewritten.
