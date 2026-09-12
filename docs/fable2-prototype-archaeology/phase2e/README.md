# Phase 2E reproduction and explicit opt-in

Run offline from the repository root. No network, game launch, build, code generation, Lua/proprietary script execution, binary modification or Ghidra mutation is part of this workflow.

Read-only frozen validation and byte-identical replay:

```powershell
python tools/phase2e/Fable2PrototypeOverlay.py verify-upstream
python tools/phase2e/Fable2PrototypeOverlay.py decision --check
python tools/phase2e/Fable2PrototypeOverlay.py delta --check
python tools/phase2e/Fable2PrototypeOverlay.py bind --check
python tools/phase2e/Fable2PrototypeOverlay.py materialize --check
python tools/phase2e/VerifyFable2PrototypeOverlay.py verify
pwsh -NoProfile -File tools/phase2e/Verify-Fable2PrototypeOverlay.ps1
git diff --check
```

Reconstruct ignored Phase 2E artifacts deterministically from the committed decision and delta, then refresh deterministic receipts:

```powershell
python tools/phase2e/Fable2PrototypeOverlay.py materialize
python tools/phase2e/VerifyFable2PrototypeOverlay.py checks
python tools/phase2e/VerifyFable2PrototypeOverlay.py tests
python tools/phase2e/VerifyFable2PrototypeOverlay.py replay
python tools/phase2e/VerifyFable2PrototypeOverlay.py finalize
```

Default analysis selection, with the overlay disabled:

```powershell
python tools/phase2e/Fable2PrototypeOverlayConsumer.py default
```

Explicit Phase 2E opt-in:

```powershell
python tools/phase2e/Fable2PrototypeOverlayConsumer.py opt-in `
    --overlay-version phase2e-v1 `
    --decision docs/fable2-prototype-archaeology/phase2e/evidence/owner-decision.json `
    --decision-sha256 7905EDD55A1DDA53C7FDD1D36635FFC7E6315F1BA66F2CB88393A3E5F6F766BD `
    --delta docs/fable2-prototype-archaeology/phase2e/evidence/approved-overlay-delta.json `
    --delta-sha256 BD53722F709EB2BB287482DE09E2D6953EAD19DDA675E1B1C34DEBA55D2D52BC `
    --effective-map out/prototype-archaeology/phase2e/effective-map.json `
    --effective-map-sha256 E3EE02E659ADCBD79823B3343A542505B45B8B902BAADD158A2A75D577E71663
```

The adapter validates all three caller-supplied hashes, independently reconstructs the decision and delta, verifies the full map and emits the exact selection in output provenance. It refuses missing, stale, tampered or unknown overlays without fallback. No existing consumer is implicitly switched.

Validation trust-root identity for this checkout: `docs/fable2-prototype-archaeology/phase2e/evidence/validation.json`, 8620 bytes, `B0CB8CFB053A2E982CC663AAF77F3705D7574552975EB933C6825F04462900A5`.

See `report.md`, `policy.md`, `reservation-inventory.md`, `rollback.md` and `next-phase-handoff.md`.
