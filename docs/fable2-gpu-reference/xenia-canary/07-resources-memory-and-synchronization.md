# Xenia Canary resources, memory, and synchronization

## Evidence basis

All source locators refer to
`xenia-canary/xenia-canary@3a44f20c7bc66db1da583e8a6f0ab740e31908e9`.

## Shared guest-memory model

`src/xenia/gpu/shared_memory.h:SharedMemory` exposes a
`kBufferSize` 512 MiB GPU-visible mirror of guest physical memory. It owns
per-system-page bitmaps for:

- whether the host mirror contains valid guest data; and
- whether a page has been written by the host GPU and may require download
  before CPU observation.

It also owns a physical-memory invalidation callback, global watches, and range
watches. These are **CONFIRMED** persistent structures.

## Upload path

`src/xenia/gpu/shared_memory.cc:SharedMemory::RequestRange`:

1. validates and page-aligns the requested guest range;
2. ensures the corresponding host backing exists;
3. finds invalid page spans;
4. requests backend upload of those spans; and
5. marks successfully uploaded pages valid.

D3D12 implements the backend operation in
`D3D12SharedMemory::UploadRanges`; Vulkan implements it in
`VulkanSharedMemory::UploadRanges`. Textures, vertex fetches, indices,
memory export, and resolve paths all request ranges through this model.

The cvar that permits invalid upload ranges can relax validation. It is a
diagnostic/compatibility choice, not a statement that out-of-range access is
valid hardware behavior.

## Guest writes and watches

Guest CPU writes reach the Memory invalidation callback. Shared memory clears
validity for overlapping pages and calls range/global watchers. Texture cache
entries, converted-index data, and other clients mark derived resources stale.

Primary history commit
`aed81ca93a1f3e8dd043107babd33438379f379d`,
`[Memory] Rework guest access resolution and unwatched invalidation`, is
**CONFIRMED** primary context for
the current invalidation design within the shallow history.

`SharedMemory::RangeWrittenByGpu` marks GPU-written ranges, fires relevant
watches, and retains them as valid on the GPU side. When CPU visibility is
required, backend download/readback and submission completion must precede CPU
use.

## D3D12 resource strategy

`src/xenia/gpu/d3d12/d3d12_shared_memory.cc` can represent shared memory as:

- a tiled/reserved resource with pages mapped as needed, if enabled and
  supported; or
- a committed resource fallback.

`D3D12SharedMemory::Use` transitions resource state and provides UAV ordering.
The command processor and caches additionally issue:

- explicit state transitions;
- UAV barriers for unordered writes;
- alias barriers for reinterpreted resources; and
- copy/resolve synchronization.

The direct queue is ordered by command list submission. A D3D12 fence and
`D3D12GPUCompletionTimeline` expose completion. Descriptor heaps, allocators,
temporary buffers, cache items, and other objects are retired only after their
submission is complete.

## Vulkan resource strategy

`src/xenia/gpu/vulkan/vulkan_shared_memory.cc` can represent shared memory as:

- a sparse buffer with memory bound for requested pages, if enabled and
  supported; or
- a fully allocated buffer fallback.

Sparse binding introduces queue-bind operations and semaphores before consumers
use the new pages. `VulkanSharedMemory::Use` derives source/destination stage
and access masks for buffer barriers.

The wider backend also tracks image layouts and image barriers for textures,
render targets, resolve images, and presenter resources. Queue submissions use
semaphores for dependencies and `VkFence` through
`VulkanGPUCompletionTimeline` for host completion and retirement.

## Submissions and frame synchronization

Both command processors group work with `BeginSubmission` and
`EndSubmission`.

```text
packet operations
  -> begin or continue backend submission
  -> resource transitions/barriers and command recording
  -> wait for required asynchronous pipeline creation
  -> submit queue work
  -> assign completion value/fence
  -> retire resources when completed
```

IssueSwap ends a submission with presentation significance even when no host
present immediately follows. The presenter then uses backend synchronization
for guest-output refresh and host swapchain work.

Frames-in-flight and completion values protect resources from reuse while the
host GPU may still access them. Exact queue latency and stalls are **UNKNOWN**
without a runtime trace.

## Coherency boundaries

The code has several distinct coherency mechanisms:

| Mechanism | Scope | Confidence |
|---|---|---|
| guest Memory invalidation callback | CPU write invalidates mirrored/derived GPU data | CONFIRMED |
| SharedMemory validity bitmaps | page upload/download ownership | CONFIRMED |
| range/global watches | invalidate textures, conversions, and other derived users | CONFIRMED |
| RenderTargetCache ownership | EDRAM alias and target representation | CONFIRMED |
| D3D12 barriers / Vulkan barriers and layouts | host API ordering and visibility | CONFIRMED |
| `MakeCoherent` | guest coherency register handling | PARTIAL: resource-cache notification TODO |

The primary-history texture fix
`9781a75a22ba789124d7f34c6bdb4a85c78b2532` confirms that validity must be
rechecked before installing a texture watch, preventing stale state across that
boundary.

## Resource lifetime

Texture caches enforce soft/hard budgets and MRU eviction. Pipeline caches own
shader translations and host pipelines. Render-target caches own EDRAM
representations and transfers. Descriptor allocators/pools and temporary
resources are submission-scoped or completion-retired.

Host device loss is not recovered: it reaches
`GraphicsSystem::OnHostGpuLoss` and is fatal. Resource recreation is a TODO.

Static source cannot determine memory pressure, sparse residency success,
barrier cost, race manifestation, or device-specific correctness. Fable II use
is **NOT APPLICABLE** in this phase.
