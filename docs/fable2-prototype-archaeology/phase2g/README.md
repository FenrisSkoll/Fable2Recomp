# Phase 2G — high-value native semantic proof

Phase 2G performs a static, offline, instruction-level review of exactly three Phase 2F packet groups. It does not feed semantics into mappings or names. It changes no Phase 1–2F artifact, ReXGlue state, manifest, generated source, runtime, binary, asset or Ghidra database.

The frozen base is commit `d348952f780d47b47368792a1b6587a2f574ddfe`, tree `b002fd60ae678597faf5fde8b9f39908d376e51f`. The analysis requires the explicit noncanonical `phase2e-v1` overlay at 15,379 pairs and separately verifies the unchanged 15,299-pair default consumer. Every invocation rehashes the ten Phase 2F trust roots, all 32 ignored Phase 2F artifacts, the complete bound source population, ReXGlue and the fifteen libmspack files before native inspection.

## Offline reproduction

From `C:\Dev\Fable2Recomp` on branch `fable2-prototype-archaeology-phase2g`:

```powershell
python -B tools/phase2g/Fable2NativeProofSources.py --check
python -B tools/phase2g/Fable2NativeProof.py --check
python -B tools/phase2g/VerifyFable2NativeProof.py verify
python -B tools/phase2g/VerifyFable2NativeProof.py git-audit
pwsh -NoProfile -File tools/phase2g/Verify-Fable2NativeProofSchemas.ps1
python -B -m unittest discover -s tests -p "test*.py"
git diff --check
```

To recreate ignored evidence in a clean Phase 2G checkout, omit `--check` from the first two commands, run the verifier receipt commands documented in `report.md`, then run `verify`. Replay uses canonical JSON, stable ordering and exact byte comparison. No command launches or builds the game or SDK, performs code generation, executes game scripts, accesses the network, or mutates a frozen input.

The exact clean-checkout generation sequence is:

```powershell
python -B tools/phase2g/Fable2NativeProofSources.py --check
python -B tools/phase2g/Fable2NativeProof.py
python -B tools/phase2g/VerifyFable2NativeProof.py receipts
python -B tools/phase2g/VerifyFable2NativeProof.py summary --check
python -B tools/phase2g/VerifyFable2NativeProof.py validation --check
python -B tools/phase2g/VerifyFable2NativeProof.py verify
python -B tools/phase2g/VerifyFable2NativeProof.py git-audit
```

## Results

- Packet A: `independently-corroborated-role`; reservation retained.
- Packet B: `behaviorally-corresponding-role-reserved`; reservation retained.
- Packet C: `independently-corroborated-role`; mapping review-triggered only for a semantic edge-attribution error; reservation retained.

These are contextual role dispositions, not function names. See `report.md`, `policy.md`, `review-guide.md` and `next-phase-handoff.md`. Machine-readable committed results are `evidence/source-pins.json`, `evidence/packet-summary.json` and `evidence/validation.json`; exhaustive derived evidence remains ignored under `out/prototype-archaeology/phase2g/`.
