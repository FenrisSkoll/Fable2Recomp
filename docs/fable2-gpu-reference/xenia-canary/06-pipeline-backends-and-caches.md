# Xenia Canary pipeline backends and caches

## Evidence basis

All source locators refer to
`xenia-canary/xenia-canary@3a44f20c7bc66db1da583e8a6f0ab740e31908e9`.

## Common-to-backend boundary

The common command model enters a backend through concrete
`CommandProcessor` virtual operations. The central draw endpoints are:

- `src/xenia/gpu/d3d12/d3d12_command_processor.cc:D3D12CommandProcessor::IssueDraw`;
- `src/xenia/gpu/vulkan/vulkan_command_processor.cc:VulkanCommandProcessor::IssueDraw`;
- the corresponding `IssueCopy`, `IssueSwap`, `LoadShader`,
  `BeginSubmission`, and `EndSubmission` implementations.

Both draw functions consume shared inputs:

- active analyzed vertex and pixel shaders;
- `RegisterFile` state;
- `PrimitiveProcessor::ProcessingResult`;
- render-target/cache update results;
- texture, sampler, vertex/index, and constant requirements; and
- guest shared-memory ranges.

They leave as API-specific pipeline, descriptor, barrier, and draw commands.

## D3D12 assembly

`src/xenia/gpu/d3d12/pipeline_cache.cc:PipelineCache::ConfigurePipeline`
forms a pipeline description from translated shaders, primitive topology,
rasterizer state, depth/stencil, blending, render-target formats, and the
selected ROV/RTV architecture.

The D3D12 command processor owns or coordinates:

- direct command queue, command allocators, and command lists;
- root signatures for binding strategy and pipeline variation;
- view/sampler descriptor heaps and per-submission allocation;
- system, float, bool/loop, fetch, and descriptor constants;
- shared-memory, texture-cache, render-target-cache, and primitive-processor
  resources;
- D3D12 resource states, UAV barriers, and alias barriers; and
- fence-backed submission completion and deferred destruction.

The final calls are `DrawInstanced` or `DrawIndexedInstanced`.

`d3d12_bindless` materially changes shader/resource layout. ROV versus RTV
changes the output-merger representation and pipeline key. Device capabilities
and vendor/generation checks can disable or redirect paths. All are
**CONFIRMED** branches.

## Vulkan assembly

`src/xenia/gpu/vulkan/vulkan_pipeline_cache.cc:VulkanPipelineCache::ConfigurePipeline`
forms a Vulkan pipeline description from translated SPIR-V, topology,
rasterization, multisampling, depth/stencil, blending, descriptor layout, and
render-pass/FSI requirements.

The Vulkan command processor owns or coordinates:

- queue and command buffers;
- descriptor-set layouts, descriptor pools, and per-submission sets;
- pipeline layouts and push/system constants;
- render passes/framebuffers for the FBO path or EDRAM storage for FSI;
- shared-memory, texture, render-target, and primitive resources;
- image layouts plus buffer/image pipeline barriers;
- sparse-bind semaphores where sparse memory is active; and
- fence-backed submission completion and deferred destruction.

The final calls are `CmdVkDraw` or `CmdVkDrawIndexed`.

Device extensions/features change SPIR-V capabilities, render-target path,
sparse memory, descriptor capacity, sample behavior, and presentation
synchronization. Source expresses the branches; a concrete selection is
**UNKNOWN** without device enumeration.

## Pipeline and shader keys

Both caches use:

- XXH3 of guest ucode for `Shader` identity;
- a translation modification for backend/output/resource differences;
- a pipeline description containing the host-relevant draw state; and
- title/configuration identity for persistent storage.

Vulkan also reads/writes a native `VkPipelineCache` blob named
`{title}.vk.bin`. This is driver-facing cache data, separate from the
high-level shader/pipeline records.

Cache contents are derived host data. This G1.5B corpus records no shader body,
compiled shader, cache blob, source dump, or capture.

## Asynchronous compilation

Pipeline creation can run on worker threads, controlled by
`async_shader_compilation` and backend creation-thread counts.

```text
ConfigurePipeline
  -> cache hit: use ready pipeline
  -> cache miss: create inline or queue creation
  -> command recording may continue with tracked pending pipeline
  -> EndSubmission waits before submitting work that requires completion
```

This scheduling is **CONFIRMED** from the backend pipeline caches and command
processors. It does not mean an unfinished pipeline is submitted.

There is a separate title-startup path:
`Emulator::Setup -> GraphicsSystem::InitializeShaderStorage`. Its source
comment says draws may be skipped until storage is ready. The frequency and
visible effect are **UNKNOWN**.

## Invalidation and lifetime

Pipeline keys cause a new lookup when shader modification, topology,
render-target mode/format, or other key state changes. Register writes
invalidate backend constant/texture bindings as needed. Descriptor allocations
and transient resources are associated with submissions and retired after the
completion timeline passes their use.

Texture and primitive caches have independent guest-memory watches. Render
targets have EDRAM ownership. Shared memory has per-page validity. No single
cache invalidation mechanism owns every category.

## Capability/configuration matrix

| Area | D3D12 | Vulkan | Confidence |
|---|---|---|---|
| Host shader | DXBC | SPIR-V | CONFIRMED |
| Bindings | root signature, descriptor heaps; bindless/bindful | pipeline layout, descriptor sets/pools | CONFIRMED |
| EDRAM exactness path | ROV | fragment shader interlock | CONFIRMED |
| Approximate host RT path | RTV/DSV | framebuffer/render pass | CONFIRMED |
| Shared-memory sparse path | tiled reserved resource when supported/enabled | sparse buffer when supported/enabled | CONFIRMED |
| Completion | direct-queue fence | queue submission with VkFence/semaphores | CONFIRMED |
| Native pipeline cache | D3D/pipeline storage path | additional VkPipelineCache blob | CONFIRMED |
| Device-specific performance/parity | runtime dependent | runtime dependent | UNKNOWN |

No backend recommendation or cross-project divergence conclusion is made.
