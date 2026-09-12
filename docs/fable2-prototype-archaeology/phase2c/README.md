# Phase 2C static archaeology checkpoint

This work is **not a completed Phase 2C close-out**. Read the generated
[report](report.md), [policy](policy.md), [review guide](review-guide.md), and
[handoff](next-phase-handoff.md) before interpreting its provisional results.
No proposal is canonical and no production consumer uses the effective view.

Run from `C:\Dev\Fable2Recomp` on `fable2-prototype-archaeology-phase2c`.
ReXGlue remains at `C:\Dev\rexglue-sdk-v0.10`. Do not rebuild, regenerate
closed phases, launch a game, or rebind changed inputs.

The existing pins were created once with these commands. Do not repeat them:

```powershell
python tools/Fable2PrototypeTrust.py bind
python tools/Fable2PrototypeTrust.py bind-semantic-inputs
```

Generation order, for the same bound inputs:

```powershell
python tools/Fable2PrototypeTrust.py audit
python tools/Fable2PrototypeTrust.py candidates
python tools/Fable2PrototypeTrust.py september
.\tools\Verify-Fable2PrototypeTrust.ps1
python tools/Fable2PrototypeTrust.py freeze
python tools/Fable2PrototypeTrust.py semantics
python tools/Fable2PrototypeTrust.py summarize
```

The mapping freeze must precede semantics. Do not regenerate mapping artifacts
while treating a previous semantic pass as current. A later mapping revision
requires a separately reviewed new freeze and replay; semantics cannot validate
the mapping that produced it.

Complete read-only analytical replay and consistency commands:

```powershell
python tools/Fable2PrototypeTrust.py verify-audit
python tools/Fable2PrototypeTrust.py verify-candidates
python tools/Fable2PrototypeTrust.py verify-september
python tools/Fable2PrototypeTrust.py verify-freeze
python tools/Fable2PrototypeTrust.py verify-semantics
python tools/Fable2PrototypeTrust.py verify-summary
.\tools\Verify-Fable2PrototypeTrust.ps1
python -m unittest discover -s tests -q
git diff --check
```

Each command hashes the closed input family and SDK preservation state before
analysis. The `verify-*` commands compare bytes without writing analytical
outputs. The existing Phase 2B verifier requires the Phase 2B branch; it passed
before creating Phase 2C. Its source, report and exhaustive output hashes remain
bound and checked without weakening its branch invariant.

Large machine artifacts remain under ignored
`out/prototype-archaeology/phase2c/`. Committed
`evidence/validation.json` binds their exact paths, sizes and hashes, the
implementation hashes and generated report. The initial repository state and
all fifteen materialized SDK libmspack identities are in `evidence/source-pins.json`.
Current-runtime script files have separate `semantic-extra-source-pins.json`:
they are not silently asserted to have authenticated retail-disc provenance.

The schema is `tools/schemas/fable2-prototype-trust-v1.schema.json`.
Schema validity alone does not certify scientific completeness. The report
explicitly retains the unfinished completion gates.
