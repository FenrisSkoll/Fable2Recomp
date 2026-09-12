# Phase 2D reproduction

Run offline from the repository root on `fable2-prototype-archaeology-phase2d`.
The unchanged private corpus and ignored Phase 1/2A/2B/2C artifacts are required.
No network, game, build, code generation or script execution is part of this workflow.

The source binder authenticates frozen committed envelopes against commit
`f13ee49c94db48d979de1346b7f67d2d82257ea2`, rehashes all closed inputs and checks
the SDK at its Phase 1 pin, including all fifteen libmspack modifications. Changed
frozen inputs are errors. Never repair, regenerate or rebind them from Phase 2D.

```powershell
python tools/Fable2PrototypeReview.py bind --check
python tools/Fable2PrototypeReview.py reconstruct
python tools/Fable2PrototypeReviewDecision.py review
python tools/VerifyFable2PrototypeReview.py checks
python tools/VerifyFable2PrototypeReview.py tests
python tools/VerifyFable2PrototypeReview.py replay
python tools/VerifyFable2PrototypeReview.py finalize
.\tools\Verify-Fable2PrototypeReview.ps1
python tools/VerifyFable2PrototypeReview.py verify
git diff --check
```

Use `reconstruct --check` and `review --check` for read-only analytical replay.
They compare all output bytes rather than updating the independent result. `replay`
invokes both and writes only the Phase 2D replay receipt. `checks` runs documented
read-only earlier-phase consistency/schema/domain checks; it writes only a Phase
2D receipt. `tests` runs complete supported discovery and records exact test IDs
without wall-clock output. It is equivalent in test scope to:

```powershell
python -m unittest discover -s tests -q
```

`finalize` binds every ignored JSON artifact by path, size and SHA-256 into both
report and validation. `verify` repeats that construction with byte comparisons.
All JSON uses the committed `fable2-prototype-review-v1.schema.json` family with
explicit artifact names and version 1. PowerShell 7's existing local `Test-Json`
validates it; no package installation or remote schema retrieval is required.

The original Phase 2C `verify-summary` passed before the branch was created.
Its branch-specific runner and all closed generators retain their original guards.
Phase 2D rehashes their artifacts and invokes pure terminal/domain validators;
it does not change guards or write historical replay receipts. The absent historical
ownership input remains an inherited blocker and must not be searched for here.

The independently frozen reconstruction consists of donor-only selection, full raw
profiles and blinded target sets. Decision processing consumes that freeze and
cannot modify its files. Source-bound shared low-level parsers are declared; no
psychological independence or measured cross-build accuracy is claimed.

See [report.md](report.md), [policy.md](policy.md), [review-guide.md](review-guide.md),
[human-decision-guide.md](human-decision-guide.md), [adoption-plan.md](adoption-plan.md)
and [next-phase-handoff.md](next-phase-handoff.md). Local attributes preserve LF
only for new Phase 2D files; frozen Phase 2C attributes remain byte-identical.
