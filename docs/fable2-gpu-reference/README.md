# Fable II GPU reference corpus

This is the permanent G1.5A/G1.5B/G1.5C source reference for the ReXGlue and
pinned Xenia Canary Xenos GPU architectures. Each implementation is documented
first on its own terms, then compared through source and primary history. The
corpus is not a renderer proposal and contains no capture or runtime changes.

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

Validate the corpus from the repository root with:

```powershell
python .\tools\Verify-Fable2GpuReference.py `
    --sdk-root C:\Dev\rexglue-sdk-v0.10 `
    --canary-root C:\Dev\Fable2NativeRendererResearch\xenia-canary `
    --verify-artifacts
```

Omit `--verify-artifacts` on a machine without the ignored local build and SDK
package. Source, symbol, JSON-schema, history, pin, cleanliness and link checks
still run. Omit `--canary-root` to use the path recorded in the evidence.

## Evidence language

- `CONFIRMED`: directly present in the pinned source, binary, accepted G1
  evidence, or an identified existing runtime log.
- `PROBABLE`: multiple indicators agree, but the exact runtime route has not
  been observed.
- `UNKNOWN`: the static corpus cannot establish the claim.
- `NOT APPLICABLE`: the path exists in source but is excluded from the current
  artifact or scope.

Unless a Fable connection is explicitly `CONFIRMED`, the documents state the
needed evidence and an existing later observation point. Source availability
alone never proves title use.
