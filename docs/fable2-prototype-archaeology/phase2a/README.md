# Prototype archaeology Phase 2A

Phase 2A establishes binary function correspondences from the byte-identical July 2009 / build
`23.12.02.0330` development image to canonical post-patch Fable II GOTY TU1. It does not propagate
semantic names, edit the TU1 manifest, add overrides, or change generated/runtime code.

The generator uses exact `.pdata` records as function units. Its accepted core is precision-first;
all remaining donor functions retain an explicit terminal status and candidate count. The lossless
fingerprint candidate groups remain under ignored `out/prototype-archaeology/phase2a`, while a
bounded top-candidate surface is committed.

Normalized-prefix boundary groups are retained exhaustively, but only reciprocal-unique prefix
pairs enter the per-function boundary review queue. Common prologues therefore remain measurable
ambiguity evidence without expanding into misleading millions of split/merge suggestions.

## Reproduction

Run from the repository root after reproducing and verifying Phase 1:

```powershell
python .\tools\Fable2PrototypeArchaeology.py verify
python .\tools\VerifyFable2PrototypePhase1Consistency.py

python .\tools\Fable2PrototypeCorrespondence.py generate `
    --tool-commit f5836c4736b370e8e7b027fb6a602f2dad1d0992 `
    --generated-at 2026-09-11T00:00:00Z

python .\tools\Fable2PrototypeCorrespondence.py verify `
    --tool-commit f5836c4736b370e8e7b027fb6a602f2dad1d0992

.\tools\Verify-Fable2PrototypeCorrespondenceJson.ps1
python -m unittest .\tests\test_fable2_prototype_correspondence.py -v
```

Re-run `generate` with `--check-determinism` and the same timestamp after the committed outputs
exist. Input identity changes fail closed.

## Outputs

The committed `evidence` directory contains the complete donor status index, detailed accepted
records, a bounded stratified review queue, positive-control/synthetic/September validation, and
the aggregate policy and result summary. Every artifact repeats the same hash-bound input bundle.

The ignored exhaustive candidate representation is lossless: for each shared fingerprint, its
candidate edges are the Cartesian product of the recorded donor and target member sets. Its exact
path, size, and SHA-256 are recorded in the committed summary.

## Results and handoff

- [Phase 2A technical report](report.md)
- [Phase 2B handoff](phase2b-handoff.md)
- [Machine-readable evidence](evidence/)

The five committed JSON artifacts validate against
[`fable2-prototype-correspondence-v1.schema.json`](../../../tools/schemas/fable2-prototype-correspondence-v1.schema.json).
They contain no prototype or canonical executable bytes.
