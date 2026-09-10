# NR0A — native renderer architecture gate

**CONDITIONAL ARCHITECTURE — DYNAMIC EVIDENCE REQUIRED**

Prefer a Fable-specific scene/submission adapter with a small D3D12 backend,
developed through isolated workloads and separate comparison runs. Keep the
accepted ReXGlue/Xenos renderer as the default and as the observation and
regression baseline. Neither a Fable scene interface nor an incremental
replacement contract is qualified yet. NR0B must establish the effective
configuration and a bounded frame/resource dependency map before implementation.

This is an architecture decision with unresolved gates, dated **2026-09-09**.
It authorizes no implementation or experiment. The original G1–G1.6 evidence
retains its own classifications, dates and pins.

Follow-on status: [NR0B-1](../nr0b1/README.md) is **PREPARED — USER RUN REQUIRED**.
Its separately authorized configuration reporting and isolated run card do not
complete NR0A's dynamic frame-contract gate or qualify a renderer seam.

## Decision package

1. [Reading and provenance](reading-and-provenance.md): accepted lineage,
   current artifacts, save/testing handoffs and consulted evidence.
2. [Implementation audit](reference-implementation-audit.md): Skate,
   Unleashed, XenosRecomp, Plume and PGR4, including licensing boundaries.
3. [Architecture decision](architecture-decision.md): options, backend choice
   and compact claim ledger.
4. [Ownership contract](ownership-and-transition-contract.md): current,
   isolated prototype and production responsibilities.
5. [NR0B evidence specification](nr0b-evidence-plan.md): minimal dynamic gate,
   fields, collection bounds and stop conditions; **not implemented**.
6. [Implementation gates](implementation-gates.md): selection, lifecycle,
   translation, first workload and parity acceptance.
7. [Completion](nr0a-completion.md): validation, limitations and Git boundary.
8. [Exact pins and source-symbol catalog](evidence/reference-pins.json).

## Evidence vocabulary

| Classification | Meaning in NR0A |
|---|---|
| SOURCE-CONFIRMED | Direct source, Git object, static TU1/generated evidence or file/hash observation; does not imply runtime execution |
| RUNTIME-CONFIRMED | An identified runtime artifact demonstrates the particular claim; inherited evidence is explicitly attributed |
| PROJECT-REPORTED | README, comment, handoff or user reports an outcome that this audit has not independently reproduced |
| BOUNDED INFERENCE | Recommendation or interpretation constrained by identified evidence |
| UNRESOLVED | Missing proof, coverage, permission or dynamic observation |
| NOT APPLICABLE | Outside this component or phase; not a negative runtime result |

Source confirms that an implementation contains an algorithm. Assertions of
accuracy in its comments remain PROJECT-REPORTED. This audit ran no reference
renderer. Black dog/player surfaces remain unexplained; Canary's similar and
intermittent symptoms do not make it a correctness oracle.

## Repeatable checks

From the Fable repository root:

```powershell
python tools/Verify-Fable2NativeRendererNR0A.py
python -m unittest discover -s tests -p test_verify_fable2_native_renderer_nr0a.py
python tools/Verify-Fable2NativeRendererG1.py
python tools/Verify-Fable2GpuReference.py --sdk-root C:\Dev\rexglue-sdk-v0.10 --canary-root C:\Dev\Fable2NativeRendererResearch\xenia-canary
git diff --check
```

The NR0A verifier reads pinned Git objects; it does not fetch, switch, build,
launch, inspect saves or capture payloads. The compact JSON contract is checked
directly, without adding another schema framework. Local root overrides are
available through `--root ID=PATH`. Presence of source symbols verifies citation
integrity, not the architectural interpretation. Historical artifact checks and
their current failures are reported in the completion record without weakening
the existing verifier.
