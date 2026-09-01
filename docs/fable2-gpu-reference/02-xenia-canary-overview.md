# Pinned Xenia Canary GPU architecture overview

## Scope and provenance

This document describes Xenia Canary on its own terms. It does not compare
Canary with ReXGlue, infer use by Fable II, or recommend implementation work.

Unless a row says otherwise, every source claim is for:

- repository: `https://github.com/xenia-canary/xenia-canary.git`
- branch: `canary_experimental`
- commit: `3a44f20c7bc66db1da583e8a6f0ab740e31908e9`
- tree: `c343b0a5796590fadc3b78c993bfada51e7e9148`

The evidence JSON records the same identity plus blob and tree objects. The
confidence words have their project meanings: `CONFIRMED`, `PROBABLE`,
`UNKNOWN`, and `NOT APPLICABLE`.

## Architectural result

**CONFIRMED — source architecture.** Canary separates a shared guest-facing
GPU model from D3D12 and Vulkan host implementations:

```text
xboxkrnl!VdSwap / guest ring write pointer
  -> GraphicsSystem
  -> CommandProcessor::WorkerThreadMain
  -> ExecutePacket / PM4 type handlers
  -> RegisterFile + active Shader state
  -> backend IssueDraw / IssueCopy / IssueSwap
     -> PrimitiveProcessor + DrawExtentEstimator
     -> Shader analysis and DXBC or SPIR-V translation
     -> TextureCache + SharedMemory
     -> RenderTargetCache + EDRAM ownership/resolve
     -> backend pipeline, descriptors, barriers, and queue
  -> Presenter::RefreshGuestOutput
  -> Presenter::PaintAndPresent
  -> D3D12Presenter or VulkanPresenter
```

The concrete chain is anchored by
`xboxkrnl_video.cc:VdSwap_entry`,
`command_processor.cc:CommandProcessor::WorkerThreadMain`,
`pm4_command_processor_implement.h:COMMAND_PROCESSOR::ExecutePacket`,
`d3d12_command_processor.cc:D3D12CommandProcessor::IssueDraw`,
`vulkan_command_processor.cc:VulkanCommandProcessor::IssueDraw`, and
`presenter.cc:Presenter::RefreshGuestOutput`.

## Ownership and thread boundaries

| Concern | Owner and boundary | Confidence |
|---|---|---|
| Top-level lifetime | `emulator.cc:Emulator::Setup` creates systems in dependency order. `Emulator` owns `GraphicsSystem`. | CONFIRMED |
| GPU lifetime | `graphics_system.h:GraphicsSystem` owns the provider, presenter, register file, command processor, interrupt state, and vblank thread. | CONFIRMED |
| Command execution | `command_processor.cc:CommandProcessor::WorkerThreadMain` runs on the `GPU Commands` `XHostThread`; guest ring updates wake it. | CONFIRMED |
| Frame limiter | `graphics_system.cc:GraphicsSystem::Setup` starts a separate `GPU Frame limiter` thread. This is distinct from host presentation. | CONFIRMED |
| Pipeline compilation | The D3D12 `PipelineCache` and `VulkanPipelineCache` optionally use creation threads. Submission waits before work requiring unfinished pipelines is sent. | CONFIRMED |
| Presentation | `Presenter` can paint on the GPU thread when allowed, or request the UI thread when composition/window state requires it. | CONFIRMED |
| Completion | D3D12 uses a fence-backed completion timeline; Vulkan uses fence/semaphore-backed submission completion. | CONFIRMED |

## Shared Xenos model

**CONFIRMED — source behavior.** The common layer owns or implements:

- PM4 type 0/1/2/3 decoding, indirect buffers, waits, events, interrupts,
  shader loads, draw/copy dispatch, and swap dispatch
  (`pm4_command_processor_implement.h`);
- a `0x5003`-dword register file, generated metadata, and reset defaults
  (`register_file.h:RegisterFile::kRegisterCount`,
  `register_file.cc:RegisterFile::RegisterFile`);
- Xenos shader ucode ownership and analysis
  (`shader.h:Shader`, `shader_translator.cc:Shader::AnalyzeUcode`);
- texture keys, guest tiled layout, fetch/sampler interpretation, memory watches,
  cache policy, and residency accounting
  (`texture_cache.cc`, `texture_util.cc`, `sampler_info.cc`);
- primitive/index conversion and draw extent estimation
  (`primitive_processor.cc:PrimitiveProcessor::Process`,
  `draw_extent_estimator.cc:DrawExtentEstimator::Estimate`);
- render-target normalization, EDRAM ownership, alias transfers, and resolve
  interpretation
  (`render_target_cache.cc:RenderTargetCache::Update`,
  `draw_util.cc:GetResolveInfo`);
- the 512 MiB guest-memory mirror validity/watch model
  (`shared_memory.h:SharedMemory::kBufferSize`,
  `shared_memory.cc:SharedMemory::RequestRange`); and
- shared presenter mailbox and UI-composition scheduling
  (`presenter.cc:Presenter::RefreshGuestOutput` and
  `Presenter::PaintAndPresent`).

## Host API compensation

**CONFIRMED — source behavior, not a hardware-equivalence finding.** D3D12 and
Vulkan implement host-specific:

- devices, queues, command lists/buffers, swapchains, fences, and semaphores;
- root signatures or descriptor-set layouts and descriptor allocation;
- DXBC or SPIR-V generation and host pipeline construction;
- resource heaps or Vulkan memory, sparse mappings, views, layouts, barriers,
  and lifetime retirement;
- EDRAM as host render targets or as a buffer accessed through rasterizer
  ordered views / fragment shader interlock;
- texture untile, endian, format conversion, resolve, and downscale compute
  paths; and
- swapchain mode selection, resize/reconnection, composition, and capture
  readback.

The host-render-target EDRAM path is an approximation where host fixed-function
output merging cannot represent every Xenos operation. The ROV/fragment-shader
interlock paths execute more output-merger behavior manually but require host
capabilities and have different cost. These statements are grounded in
`render_target_cache.h:RenderTargetCache::Path`,
`d3d12_render_target_cache.cc`, and
`vulkan_render_target_cache.cc`. They do not establish which path is best for
any title.

## Configuration and capability pivots

| Pivot | Material effect | Provenance | Confidence |
|---|---|---|---|
| `gpu` | Chooses `any`, `d3d12`, `vulkan`, or `null`; Windows `any` tries D3D12 then Vulkan. | `xenia_main.cc:EmulatorApp::CreateGraphicsSystem` | CONFIRMED |
| D3D12 render-target path | Selects host RTV or ROV, with device/vendor capability logic and fallback. | `d3d12_command_processor.cc:D3D12CommandProcessor::SetupContext` | CONFIRMED |
| Vulkan render-target path | Selects FBO or fragment shader interlock, with required feature checks and fallback. | `vulkan_command_processor.cc:VulkanCommandProcessor::SetupContext` | CONFIRMED |
| Occlusion mode | Selects `fake`, `fast`, `fast-alt`, or `strict` ZPD handling. | `command_processor.cc:GetZPDMode` and pinned history commit `fbd620c22b44638b66a70bba80d6f30d55a10924` | CONFIRMED |
| Async compilation | Changes pipeline creation scheduling and submission waits. | both backend pipeline caches and command processors | CONFIRMED |
| Sparse shared memory | Selects sparse/tiled allocation only where the backend and device support it. | both backend `SharedMemory` implementations | CONFIRMED |
| Resolve/memexport readback | Changes when GPU-produced data becomes available through guest memory. | render-target cache and command processor cvars | CONFIRMED |
| Presentation modes | D3D12 tearing and Vulkan present-mode availability change swap behavior. | backend presenters | CONFIRMED |

## Important limitations

- **UNKNOWN — runtime selection.** Static source does not prove which adapter,
  backend, capability path, pipeline variation, cache hit, or present mode a
  concrete run selects.
- **UNKNOWN — exact hardware parity.** Source comments and algorithms show
  intended modeling, but do not prove exact Xenos behavior for every precision,
  format, query, alias, or synchronization case.
- **CONFIRMED — incomplete behavior.**
  `CommandProcessor::MakeCoherent` has a resource-cache notification TODO;
  `INVALIDATE_STATE` has no implemented cache action; traditional
  `VIZ_QUERY` returns a synthetic visible result; device loss is fatal and
  recreation is a TODO.
- **UNKNOWN — older rationale.** The verified clone is shallow with 200 commits
  and boundary `049a55f03679b204379b17996bd032ce54bff156`. Rationale older than
  that boundary and unlinked external PR/issue context was not claimed.
- **NOT APPLICABLE — Fable II path use.** Establishing what Fable II exercises is
  reserved for a later phase.

## Corpus navigation

- [Initialization and command processor](xenia-canary/01-initialization-and-command-processor.md)
- [Register state and draw](xenia-canary/02-register-state-and-draw.md)
- [Shader pipeline](xenia-canary/03-shader-pipeline.md)
- [Textures, vertex fetch, and samplers](xenia-canary/04-textures-vertex-fetch-and-samplers.md)
- [Render targets, EDRAM, and resolves](xenia-canary/05-render-targets-edram-resolves.md)
- [Pipeline backends and caches](xenia-canary/06-pipeline-backends-and-caches.md)
- [Resources, memory, and synchronization](xenia-canary/07-resources-memory-and-synchronization.md)
- [Presentation, errors, and configuration](xenia-canary/08-presentation-errors-and-configuration.md)
- [Source inventory](evidence/canary-source-inventory.json)
- [Subsystem map](evidence/canary-subsystem-map.json)
