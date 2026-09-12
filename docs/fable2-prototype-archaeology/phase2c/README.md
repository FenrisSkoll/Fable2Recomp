# Phase 2C completion pass

Run from the repository root on `fable2-prototype-archaeology-phase2c`.
Checkpoint: `e784beeab1a372cc3f71e2cd1af2dfa18b58f321`. Immutable inputs and SDK
identity remain in `evidence/source-pins.json`. Do not rebind changed inputs.

Read [report.md](report.md), [completion-matrix.md](completion-matrix.md),
[policy.md](policy.md), [verification.md](verification.md) and the handoff.
Historical ownership replay remains blocked; no proposal is canonical or
human-approved. No game, build, code generation or network operation is needed.

Generation order on identical validated inputs:

```powershell
python tools/Fable2PrototypeCompletion.py ablation
python tools/Fable2PrototypeCompletion.py boundaries
python tools/Fable2PrototypeCompletion.py typed
python tools/Fable2PrototypeCompletion.py recon
python tools/Fable2PrototypeCompletion.py ownership
python tools/Fable2PrototypeCompletion.py mapping
python tools/Fable2PrototypeCompletion.py semantics
python tools/Fable2PrototypeCompletion.py review
python tools/Fable2PrototypeCompletion.py tests
python tools/Fable2PrototypeCompletion.py checks
python tools/Fable2PrototypeCompletion.py schemas
python tools/Fable2PrototypeCompletion.py replay
python tools/Fable2PrototypeCompletion.py summary
```

Mapping freezes completed ablation, boundaries, effective map and September inputs
before semantics. Cached profiles bind source and algorithm hashes. `replay`
recomputes all original Phase 2C mapping/September/downstream populations, full
profiles and completion stages, comparing bytes. It writes only its replay
receipt; closed phases are never regenerated.

Final verification:

```powershell
python tools/Fable2PrototypeCompletion.py verify-summary
./tools/Verify-Fable2PrototypeTrust.ps1
python tools/Fable2PrototypeCompletion.py tests
python tools/Fable2PrototypeCompletion.py checks
python tools/Fable2PrototypeCompletion.py schemas
git diff --check
```

`checks` invokes existing Phase 1/2A, function-map, closure, ownership, indirect
and coverage verifiers and validates all bound Phase 2B artifacts. The closed
Phase 2B generator remains branch-restricted; its pre-Phase-2C replay is preserved.
Do not weaken its guard or regenerate it under new provenance.

Ignored completion artifacts: `out/prototype-archaeology/phase2c/completion/`.
Original Phase 2C artifacts remain unchanged in the parent directory. Completion
effective-map and semantic-final supersede the provisional consumer view only
within this non-canonical analysis family. `evidence/validation.json` binds every
artifact, implementation, schema and report. Use Completion `summary` /
`verify-summary` now; the older Trust summary describes the checkpoint and must
not overwrite the completion report.

Schemas: `tools/schemas/fable2-prototype-trust-v1.schema.json` and
`tools/schemas/fable2-prototype-completion-v1.schema.json`. The PowerShell checker
validates both recursively. Paths in evidence are repository/corpus relative.
