# Fable II prototype archaeology

This directory contains reproducible, read-only analysis of the prototype corpus at
`D:\Fable2-Recomp\prototypes`. Prototype material is evidence only; the canonical target remains
Fable II GOTY TU1.

The committed outputs contain hashes, format metadata, curated strings, script symbols and
comparisons. Decrypted executable sections, extracted STFS contents and Ghidra projects remain
under the ignored `out/prototype-archaeology` tree. No prototype executable or asset bytes are
committed.

## Phase 1

- [Technical report](phase1/report.md)
- [Machine-readable evidence](phase1/evidence/)
- [Inventory summary](phase1/evidence/prototype-inventory-summary.md)

The evidence envelope schema is
[`tools/schemas/fable2-prototype-archaeology-v1.schema.json`](../../tools/schemas/fable2-prototype-archaeology-v1.schema.json).

## Phase 2A

- [Correspondence engine, reproduction guide and outputs](phase2a/README.md)
- [Technical report](phase2a/report.md)
- [Phase 2B handoff](phase2a/phase2b-handoff.md)
- [Machine-readable evidence](phase2a/evidence/)

Phase 2A maps binary function correspondence only. It does not assign or propagate semantic names,
change the TU1 manifest, add overrides, or alter generated recompilation/runtime sources.

## Reproduction

Requirements:

- the unchanged corpus at `D:\Fable2-Recomp\prototypes`;
- the canonical private TU1 inputs under `assets/tu1`;
- the existing canonical entrypoint-closure result for image
  `BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00`;
- Ghidra 12.1.2 with the repository-pinned XEXLoader extension; and
- a release build of the companion ReXGlue repository containing `rexglue stfs-extract`.

Extract the patch package into a new output directory. The command refuses an existing output
directory and never writes to the package source:

```powershell
C:\Dev\rexglue-sdk-v0.10\out\win-amd64\Release\rexglue.exe `
    stfs-extract `
    "D:\Fable2-Recomp\prototypes\Fable II (Patch Data prototype)\4D5307F1" `
    .\out\prototype-archaeology\stfs\patch-data
```

Export each full prototype XEX and the canonical TU1 image. The wrapper validates source hashes,
stages inputs below `out`, invokes the pinned Ghidra/XEXLoader path and records block hashes and
the exact command metadata:

```powershell
.\tools\Invoke-Fable2PrototypeXexExport.ps1 `
    -BuildId sep-2008 `
    -SourceXex "D:\Fable2-Recomp\prototypes\Fable II (Sep 13, 2008 prototype)\default.xex"

.\tools\Invoke-Fable2PrototypeXexExport.ps1 `
    -BuildId jul-2009 `
    -SourceXex "D:\Fable2-Recomp\prototypes\Fable II (Jul 10, 2009 prototype)\default.xex"

.\tools\Invoke-Fable2PrototypeXexExport.ps1 `
    -BuildId build-23.12.02.0330 `
    -SourceXex "D:\Fable2-Recomp\prototypes\Fable II July 10 2009 23.12.02.0330\default.xex"

.\tools\Invoke-Fable2PrototypeXexExport.ps1 -CanonicalTu1
```

Generate and verify the committed evidence:

```powershell
python .\tools\Fable2PrototypeArchaeology.py generate `
    --generated-at 2026-09-11T00:00:00Z `
    --check-determinism

python .\tools\Fable2PrototypeArchaeology.py verify
python .\tools\VerifyFable2PrototypePhase1Consistency.py
.\tools\Verify-Fable2PrototypeArchaeologyJson.ps1
python -m unittest .\tests\test_fable2_prototype_archaeology.py -v
python -m unittest .\tests\test_fable2_prototype_phase1_consistency.py -v
```

`--generated-at` is deliberately explicit. Reusing the same value and unchanged inputs produces
byte-identical JSON and Markdown outputs. `verify` rehashes every source file and checks the
required evidence artifacts without writing beneath the prototype root.

## Evidence files

| File | Purpose |
| --- | --- |
| `prototype-inventory.json` | Complete corpus inventory, source-relative identity, hashes, timestamps, magic and classification |
| `prototype-builds.json` | Build identity files, exact text and duplicate relationships |
| `prototype-xex-metadata.json` | XEX headers, execution/security/load data, libraries, derived sections and CodeView metadata |
| `prototype-debug-strings.json` | Curated ASCII/UTF-16LE debug, path, type, assert, compiler and subsystem strings |
| `prototype-debug-interfaces.json` | Debug-menu entries and `scripts`/`scripts_r` comparisons |
| `prototype-script-symbols.json` | Script constants, command names, XEX string matches and bounded pointer correlation |
| `prototype-log-evidence.json` | Log provenance and selected exact evidence lines |
| `prototype-tu1-relationship.json` | Patch-package, section and canonical TU1 relationship evidence |
| `prototype-crossbuild-feasibility.json` | `.pdata` function fingerprints and bounded representative matches |
| `prototype-resource-triage.json` | Shader/resource hashes, readable-name triage and cross-build comparisons |

These outputs are evidence indices, not symbol declarations. In particular, a script name matching
an XEX terminal string is not proof that a nearby guest function implements that command.
