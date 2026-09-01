# Draw and pipeline state

All locators refer to ReXGlue commit
`956c6a8b5da4c54b9899a2593e9c67c26de30194`.

## Draw initiation

`CommandProcessor::ExecutePacketType3Draw` in
`src/graphics/command_processor.cpp` parses `DRAW_INDX` and `DRAW_INDX_2`,
primitive type, index count/source/format/endian and major-mode state into
`IndexBufferInfo`, then calls the backend `IssueDraw`.

The current backend implementation is
`D3D12CommandProcessor::IssueDraw` in
`src/graphics/d3d12/command_processor.cpp`. Its source-confirmed sequence is:

1. inspect `RB_MODECONTROL`; redirect copy mode to `IssueCopy`;
2. require and analyse the current vertex shader;
3. determine whether rasterization/pixel shader/memexport can have an effect;
4. return success without host work for source-proven no-effect cases;
5. call `BeginSubmission(true)`;
6. call `PrimitiveProcessor::Process` and discard zero-extent output;
7. normalize depth/color state and update render targets/EDRAM;
8. derive vertex/pixel shader modification keys;
9. call `PipelineCache::ConfigurePipeline`;
10. request translated texture resources;
11. update viewport, scissor, blend/stencil and system constants;
12. update constant buffers, root parameters and descriptors;
13. make vertex and memexport guest ranges resident;
14. bind converted indices/topology; and
15. emit D3D12 `DrawInstanced` or `DrawIndexedInstanced`.

This order matters because target update and texture conversion may bind their
own compute/graphics pipelines; the guest pipeline is rebound after those
operations.

## Primitive processing and extents

Common `PrimitiveProcessor::Process` interprets reset indices, topology,
tessellation and multi-primitive ranges. It returns host primitive type, vertex
count, optional converted index data, line-loop closing index and host shader
variant information. `D3D12PrimitiveProcessor` supplies per-frame GPU buffers
for conversions and built-in expansion data.

`draw_util` in `src/graphics/util/draw.cpp` normalizes viewport, scissor,
depth/color masks, rasterization relevance and memexport ranges. The command
processor caches viewport calculation against all relevant register values.
Immediate-index extent/conversion remains unsupported in common source, and
not every tessellated primitive type is accepted by the D3D12 switch.

## Pipeline description and cache

`PipelineCache::ConfigurePipeline` in
`src/graphics/d3d12/pipeline_cache.cpp` combines:

- vertex and optional pixel translation identities;
- processed topology/tessellation form;
- normalized depth/stencil and color masks;
- host render-target formats/path;
- rasterizer, blend and sample state; and
- shader modifications coupled to the above.

`GetCurrentStateDescription` produces the hashable description.
`CreateD3D12Pipeline` turns it into a PSO, using generated geometry/hull/domain
helpers when needed. PSOs, root signatures and shader translations are cached.
Creation may occur on background threads configured by
`d3d12_pipeline_creation_threads`.

If `async_shader_compilation` is enabled and the configured handle has no ready
PSO, `IssueDraw` returns success without emitting the draw. This is a
source-confirmed baseline behavior and an important later visibility check.

## Bindings and constants

`D3D12CommandProcessor::UpdateSystemConstantValues` translates the current
Xenos register snapshot into host system constants, including viewport/depth,
texture masks, normalized color/depth state, primitive conversion and
memexport information.

`UpdateBindings` uploads guest float/bool/loop constants and system constants,
binds shared-memory/EDRAM resources, texture SRVs and samplers, and selects
bindless or bindful root parameters. `RequestViewBindfulDescriptors` and
`RequestSamplerBindfulDescriptors` allocate transient descriptor ranges;
persistent bindless descriptors are separately allocated and retired.

Register writes in `D3D12CommandProcessor::WriteRegister` invalidate the
smallest derived state it knows about. Pipeline descriptions still provide a
content key so an invalidation can lead to a cache hit rather than PSO
recreation.

## Queries and predication

Common packet state tracks bin masks and query operations. D3D12 optionally
allocates host occlusion queries through `BeginGuestOcclusionQuery` and
`EndGuestOcclusionQuery`, resolves their result and writes guest memory after
normalization. Allocation/device limitations call
`DisableHostOcclusionQueries`; the configured common fallback may use a fake
sample count.

This is partial behavioral coverage. Predication/query semantics are not fully
implemented, and G1.5A does not claim that Fable relies on or avoids them.

## Submission interaction and errors

`OnPrimaryBufferEnd` may call `EndSubmission(false)` under
`d3d12_submit_on_primary_buffer_end`. Swap always drives a swap submission.
The command processor limits active frame contexts, waits for fences before
reusing allocators/descriptors, drains deferred commands, executes the direct
queue and retires cache entries against completed submission indices.

A false return from required shader, primitive, resource, pipeline or binding
work propagates as draw failure. Other cases deliberately return true while
doing no draw (no observable effect, zero vertices, pending async PSO). Those
categories must not be conflated in later diagnostics.

## Fable connection and unknowns

`UNKNOWN FOR FABLE II`

Evidence required: a Fable draw packet and register snapshot correlated with
the `IssueDraw` decision, primitive result, shader/pipeline hashes, target path,
binding mode and final D3D12 draw or skip reason.

Suggested later observation points: `D3D12CommandProcessor::IssueDraw`,
`PrimitiveProcessor::Process`, `PipelineCache::ConfigurePipeline` and the final
`DrawInstanced`/`DrawIndexedInstanced` branch.
