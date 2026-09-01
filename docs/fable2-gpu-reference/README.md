# Fable II GPU reference corpus

This is the permanent G1.5A-D source and Fable-evidence reference for the
ReXGlue and pinned Xenia Canary Xenos GPU architectures, extended by the G1.6A
static TU1 method-recovery result. Each implementation is documented first on
its own terms, compared through source and primary history, then reassessed
against exact Fable evidence, purpose-specific boundaries, renderer ownership
and one recovered title/XDK texture-fetch operation. The reference architecture
remains a hypothesis, not implementation authorization. The corpus contains no
capture or runtime changes.

The source baseline is ReXGlue
`956c6a8b5da4c54b9899a2593e9c67c26de30194`. The active Release artifact is
`rexgpu-xenos.dll`, SHA-256
`8232051BED6E5CE99CF37B2EF581C824F58875C140A4D3C75DE14E8A5DF4AA99`.
The Fable branch was created directly from accepted G1 commit
`c44e8c16f4422f9a828caf30899ac989170b8a8c`; paused G2A source was not merged.
The independent Canary baseline is
`3a44f20c7bc66db1da583e8a6f0ab740e31908e9`, tree
`c343b0a5796590fadc3b78c993bfada51e7e9148`.

## Reading order

1. [Scope, evidence rules and immutable pins](00-scope-and-pins.md)
2. [End-to-end ReXGlue overview](01-rexglue-overview.md)
3. [Plugin and runtime boundary](rexglue/01-plugin-runtime-boundary.md)
4. [Command processor and register state](rexglue/02-command-processor-and-register-state.md)
5. [Shader pipeline](rexglue/03-shader-pipeline.md)
6. [Textures, vertex fetch and samplers](rexglue/04-textures-vertex-fetch-and-samplers.md)
7. [Render targets, EDRAM and resolves](rexglue/05-render-targets-edram-resolves.md)
8. [Draw and pipeline state](rexglue/06-draw-and-pipeline-state.md)
9. [Resources, memory and synchronization](rexglue/07-resources-memory-and-synchronization.md)
10. [Presentation, backends, system UI and errors](rexglue/08-presentation-backends-and-errors.md)
11. [G1.5A completion and handoff](g1.5a-completion.md)
12. [End-to-end pinned Xenia Canary overview](02-xenia-canary-overview.md)
13. [Canary initialization and command processor](xenia-canary/01-initialization-and-command-processor.md)
14. [Canary register state and draw](xenia-canary/02-register-state-and-draw.md)
15. [Canary shader pipeline](xenia-canary/03-shader-pipeline.md)
16. [Canary textures, vertex fetch and samplers](xenia-canary/04-textures-vertex-fetch-and-samplers.md)
17. [Canary render targets, EDRAM and resolves](xenia-canary/05-render-targets-edram-resolves.md)
18. [Canary pipeline backends and caches](xenia-canary/06-pipeline-backends-and-caches.md)
19. [Canary resources, memory and synchronization](xenia-canary/07-resources-memory-and-synchronization.md)
20. [Canary presentation, errors and configuration](xenia-canary/08-presentation-errors-and-configuration.md)
21. [G1.5B completion and handoff](g1.5b-completion.md)
22. [ReXGlue and Canary divergence](03-rexglue-canary-divergence.md)
23. [Divergence history and rationale](04-divergence-history-and-rationale.md)
24. [Accuracy, performance and architecture classification](05-accuracy-performance-architecture-classification.md)
25. [G1.5C completion and handoff](g1.5c-completion.md)
26. [Fable II relevance assessment](06-fable2-relevance-assessment.md)
27. [Boundary and ownership reassessment](07-boundary-and-ownership-reassessment.md)
28. [System-UI and presentation contract](08-system-ui-and-presentation-contract.md)
29. [Evidence gaps and experiment plan](09-evidence-gaps-and-experiment-plan.md)
30. [Custom-renderer reference architecture](10-custom-renderer-reference-architecture.md)
31. [G2A re-entry decision](11-g2a-reentry-decision.md)
32. [Open questions](open-questions.md)
33. [G1.5D completion and handoff](g1.5d-completion.md)
34. [G1.6A static XDK method recovery](12-static-xdk-method-recovery.md)
35. [G1.6A static method inventory](evidence/static-xdk-method-inventory.json)
36. [G1.6A completion and handoff](g1.6a-completion.md)
37. [G1.6B static seam qualification and coverage](13-static-xdk-seam-coverage.md)
38. [G1.6B static seam coverage evidence](evidence/static-xdk-seam-coverage.json)
39. [G1.6B completion and handoff](g1.6b-completion.md)

Machine-readable provenance is in
[the source inventory](evidence/rexglue-source-inventory.json) and
[the subsystem map](evidence/rexglue-subsystem-map.json). Their schemas are
[source-inventory v1](../../tools/schemas/fable2-gpu-source-inventory-v1.schema.json)
and [subsystem-map v1](../../tools/schemas/fable2-gpu-subsystem-map-v1.schema.json).

The Canary indexes are
[the Canary source inventory](evidence/canary-source-inventory.json) and
[the Canary subsystem map](evidence/canary-subsystem-map.json), validated by
[Canary source-inventory v1](../../tools/schemas/fable2-gpu-canary-source-inventory-v1.schema.json)
and [Canary subsystem-map v1](../../tools/schemas/fable2-gpu-canary-subsystem-map-v1.schema.json).

The G1.5C comparison is represented by
[the divergence matrix](evidence/divergence-matrix.json) and
[the primary-history index](evidence/divergence-history.json), validated by
[divergence-matrix v1](../../tools/schemas/fable2-gpu-divergence-matrix-v1.schema.json)
and [divergence-history v1](../../tools/schemas/fable2-gpu-divergence-history-v1.schema.json).
The matrix is authoritative for classifications, counts, preliminary Fable
relevance, renderer implications, and open questions; the Markdown chapters
are review views.

## G1.5D evidence index

The G1.5D synthesis is represented by:

- [the Fable relevance matrix](evidence/fable2-relevance-matrix.json), validated
  by [Fable relevance v1](../../tools/schemas/fable2-gpu-fable-relevance-v1.schema.json);
- [the purpose-specific boundary assessment](evidence/boundary-assessment.json),
  validated by [boundary assessment v1](../../tools/schemas/fable2-gpu-boundary-assessment-v1.schema.json);
- [the staged replacement-seam and ownership decisions](evidence/replacement-seams.json),
  validated by [replacement seams v1](../../tools/schemas/fable2-gpu-replacement-seams-v1.schema.json);
- [the minimum experiment backlog](evidence/experiment-backlog.json), validated
  by [experiment backlog v1](../../tools/schemas/fable2-gpu-experiment-backlog-v1.schema.json);
- [the two-part G2 decision](evidence/g2a-decision.json), validated by
  [G2A decision v1](../../tools/schemas/fable2-gpu-g2a-decision-v1.schema.json).

The G1.5D JSON records are authoritative for classifications, counts, stable
IDs, cross-links and decisions. Chapters 06-11 and the open-question ledger
are review views. Existing local Run 047/048 logs and screenshots remain
ignored or external; only their paths, sizes, hashes and bounded findings are
committed.

## G1.6A evidence index

The G1.6A result is represented by the
[static XDK method inventory](evidence/static-xdk-method-inventory.json),
validated by
[static XDK method inventory v1](../../tools/schemas/fable2-gpu-static-xdk-method-inventory-v1.schema.json).
The inventory is authoritative for candidate boundaries, ABI fields, object
offsets, call/import relationships, ownership, side effects, coverage,
classifications and the phase decision. The [G1.6A report](12-static-xdk-method-recovery.md)
and [completion record](g1.6a-completion.md) are review and handoff views.

`SXDK-001` / `sub_82BA77D0` is a **QUALIFIED REPRESENTATIVE METHOD**
for one six-dword texture-fetch binding operation. Its coverage is explicitly
narrow; this result does not authorize interception or renderer work.

## G1.6B evidence index

The G1.6B result is represented by the
[static XDK seam coverage evidence](evidence/static-xdk-seam-coverage.json),
validated by [static XDK seam coverage
v1](../../tools/schemas/fable2-gpu-static-xdk-seam-coverage-v1.schema.json).
The evidence is authoritative for the exhaustive `SXDK-001` route census,
recoverable texture-producer inventory, bounded `SXDK-002`/`SXDK-003`
contracts, five-stage lifetime model, bypass accounting, title-system unknown
bucket and phase decision. The [G1.6B report](13-static-xdk-seam-coverage.md)
and [completion record](g1.6b-completion.md) are review and handoff views.

G1.6B returns **STATIC COVERAGE NARROW**. `SXDK-001` remains technically
qualified but is refined to **QUALIFIED NARROW METHOD** for architectural use:
it has exactly two direct callers, while an independent confirmed texture
producer and six common state-to-draw roots bypass it. This does not authorize
interception, instrumentation, G2A work or renderer implementation.

Validate the corpus from the repository root with:

```powershell
python .\tools\Verify-Fable2GpuReference.py `
    --sdk-root C:\Dev\rexglue-sdk-v0.10 `
    --canary-root C:\Dev\Fable2NativeRendererResearch\xenia-canary `
    --verify-artifacts
```

Omit `--verify-artifacts` on a machine without the ignored local build, SDK
package, cited Run 047/048 evidence and local G1.6A/G1.6B static-analysis
reports.
Source, generated mapping, JSON-schema, history, pin, cross-link, count, phase
hygiene and Markdown-link checks still run. Omit `--canary-root` to use the path
recorded in the evidence.

## Evidence language

- `CONFIRMED`: directly present in the pinned source, binary, accepted G1
  evidence, or an identified existing runtime log.
- `PROBABLE`: multiple indicators agree, but the exact runtime route has not
  been observed.
- `BOUNDED INFERENCE`: exact observations bound the interpretation, but do not
  establish the source-level name, runtime path or frequency.
- `PLAUSIBLE`: a possible interpretation lacking enough evidence for a bounded
  conclusion.
- `UNKNOWN`: the static corpus cannot establish the claim.
- `REJECTED`: available evidence contradicts the claim or is insufficient in a
  way that has been explicitly tested.
- `NOT APPLICABLE`: the path exists in source but is excluded from the current
  artifact or scope.

Unless a Fable connection is explicitly `CONFIRMED`, the documents state the
needed evidence and an existing later observation point. Source availability
alone never proves title use.

G1.5D further separates `CONFIRMED SOURCE`, Fable reachability and causal
relevance. Broad subsystem execution never upgrades a divergent sub-behaviour
to existing runtime execution, and no row is causally confirmed without a
controlled result.
