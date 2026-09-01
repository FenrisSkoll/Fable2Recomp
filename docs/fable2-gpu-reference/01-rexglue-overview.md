# ReXGlue GPU overview

## Concrete ownership chain

The active route, expressed only with source-confirmed symbols, is:

```text
Fable TU1 sub_82BA34D8
  -> xboxkrnl VdGetSystemCommandBuffer
  -> xboxkrnl VdSwap
  -> Type-0 texture fetch + PM4_XE_SWAP in the guest ring
  -> CommandProcessor::WorkerThreadMain
  -> CommandProcessor::ExecutePrimaryBuffer
  -> CommandProcessor::ExecutePacketType3_XE_SWAP
  -> D3D12CommandProcessor::IssueSwap
  -> D3D12TextureCache::RequestSwapTexture (fetch constant 0)
  -> Presenter::RefreshGuestOutput
  -> D3D12Presenter::RefreshGuestOutputImpl
  -> Presenter guest-output mailbox
  -> D3D12Presenter::PaintAndPresentImpl
  -> guest-output effects into the DXGI back buffer
  -> Presenter::ExecuteUIDrawersFromUIThread (when host UI is registered)
  -> IDXGISwapChain::Present
```

The first three Fable/XDK edges are `CONFIRMED` by accepted G1 and pinned
ReXGlue source. The remaining edges are `CONFIRMED` as ReXGlue source call
paths. One correlated runtime event through the entire sequence is still
`UNKNOWN FOR FABLE II`; source existence is not proof that every edge
completed for a particular frame.

## Semantic boundary

Fable and the emulated XDK still own title-level rendering semantics: object
lifetime, material selection, scene traversal, draw ordering and the decision
to swap. By `VdSwap`, the operation has become front-buffer metadata plus raw
packet/register state. ReXGlue does not receive a semantic Fable scene.

The ownership split is:

| Owner | Responsibilities in the active route |
|---|---|
| Fable2Recomp generated/runtime integration | recompiled PPC execution, imports, plugin selection and staging |
| `rexruntime.dll` | Runtime/KernelState, guest memory and threads, XDK/XAM handlers, presenter/UI infrastructure |
| `rexgpu-xenos.dll` common layer | Xenos ring decoding, register state, shader/texture/EDRAM abstractions |
| `rexgpu-xenos.dll` D3D12 layer | resources, translations, PSOs, descriptors, command lists, barriers and swap output refresh |
| ReXGlue D3D12 UI provider/presenter | host device/direct queue, guest-output mailbox, swap chain, host UI composition and DXGI Present |

`rexgpu-xenos.dll` imports common services from `rexruntime.dll`; consumers do
not link the plugin. The runtime owns the `IGraphicsSystem` instance, while the
loader retains the DLL itself for process lifetime.

## Draw route

For normal draws, the base processor parses `DRAW_INDX`/`DRAW_INDX_2` into
primitive and index metadata and calls `D3D12CommandProcessor::IssueDraw`.
That function:

1. recognizes copy mode and redirects to `IssueCopy`;
2. analyses the loaded shaders and may discard a draw with no observable
   effect;
3. begins a D3D12 submission;
4. runs `PrimitiveProcessor::Process`;
5. updates render-target/EDRAM ownership;
6. obtains shader modifications and calls `PipelineCache::ConfigurePipeline`;
7. requests textures, vertex/shared-memory ranges, descriptors and constants;
8. emits `DrawInstanced` or `DrawIndexedInstanced`; and
9. marks memexport/resolve ranges and later submits/fences the command list.

Every step is source-confirmed for ReXGlue. Which variants Fable exercises is
unknown without later observation.

## State flow

The ring does not carry a complete draw object. Type 0/1/3 packets mutate a
persistent `RegisterFile`; draw packets trigger interpretation of the current
snapshot. Shader analysis recovers resource usage from Xenos microcode, texture
fetch constants become `TextureKey` values, and RB/COPY registers become EDRAM
attachments or resolve descriptions. Host pipeline descriptions are then
hashed and cached.

This is the point where surviving semantic information is lowest-level:
primitive type, shader microcode, fetch layouts, render state and memory ranges
remain; Fable object and material identities do not.

## Backend split

Common code implements PM4, registers, shader analysis, texture keys/cache
policy, primitive conversion, shared-memory validity and EDRAM ownership.
D3D12 code implements DXBC, resources/views, compute conversion and resolves,
PSOs/root signatures, barriers, queue submissions and presentation resources.
Vulkan has parallel implementations and SPIR-V translation in the source tree,
but is `NOT APPLICABLE` to the pinned DLL.

## Static limits

Static source cannot establish:

- Fable's packet mix, draw count or indirect-buffer shape;
- its shader hashes, formats, cache behavior or active EDRAM path;
- whether asynchronous PSO creation skips visible title draws;
- the one-to-one relationship between a Fable swap call, mailbox output and
  host Present;
- observed frame pacing, frame replacement, device-loss behavior or error
  relevance; or
- whether title flows use the host system-UI paths described in the
  presentation chapter.

The machine-readable subsystem map records the exact later evidence and source
observation point for each unknown.
