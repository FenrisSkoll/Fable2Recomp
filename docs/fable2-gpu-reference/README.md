# Fable II GPU reference corpus

This is the permanent G1.5A source reference for the ReXGlue Xenos GPU path
currently staged beside Fable II. It documents the implementation as found;
it is not a proposal for a new renderer and contains no capture or runtime
changes.

The source baseline is ReXGlue
`956c6a8b5da4c54b9899a2593e9c67c26de30194`. The active Release artifact is
`rexgpu-xenos.dll`, SHA-256
`8232051BED6E5CE99CF37B2EF581C824F58875C140A4D3C75DE14E8A5DF4AA99`.
The Fable branch was created directly from accepted G1 commit
`c44e8c16f4422f9a828caf30899ac989170b8a8c`; paused G2A source was not merged.

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

Machine-readable provenance is in
[the source inventory](evidence/rexglue-source-inventory.json) and
[the subsystem map](evidence/rexglue-subsystem-map.json). Their schemas are
[source-inventory v1](../../tools/schemas/fable2-gpu-source-inventory-v1.schema.json)
and [subsystem-map v1](../../tools/schemas/fable2-gpu-subsystem-map-v1.schema.json).

Validate the corpus from the repository root with:

```powershell
python .\tools\Verify-Fable2GpuReference.py `
    --sdk-root C:\Dev\rexglue-sdk-v0.10 `
    --verify-artifacts
```

Omit `--verify-artifacts` on a machine without the ignored local build and SDK
package. Source, symbol, JSON-schema and link checks still run.

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
