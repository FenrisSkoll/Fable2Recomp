# Resources, memory and synchronization

All locators refer to ReXGlue commit
`956c6a8b5da4c54b9899a2593e9c67c26de30194`.

## Common shared-memory model

`SharedMemory` in `include/rex/graphics/shared_memory.h` and
`src/graphics/shared_memory.cpp` represents the Xbox 360 physical address
space as a 512 MiB host-GPU-visible buffer. It does not own guest RAM; it owns
the validity/coherency metadata and backend mirror through which GPU consumers
access it.

Persistent common state includes:

- system-page validity and GPU-written bitmaps;
- optional sparse-host allocation information;
- physical-memory invalidation callback registration;
- per-range watches used by textures, primitives and other caches; and
- global watches used for scaled-resolve interaction.

`RequestRanges`/`RequestRange` merge and validate requested spans, ensure host
GPU allocation, and call the backend upload implementation for pages not
current on the GPU. `MemoryInvalidationCallback` receives CPU writes from guest
memory, clears validity and fires affected watches. `RangeWrittenByGpu` marks
pages as GPU-produced and fires watches with the GPU-invalidated distinction.

These watches are the main concrete resource coherency bridge. They are
separate from `CommandProcessor::MakeCoherent`, whose source retains an
incomplete cache-notification TODO.

## D3D12 mirror and uploads

`D3D12SharedMemory::Initialize` in
`src/graphics/d3d12/shared_memory.cpp` creates the 512 MiB raw buffer. If
`d3d12_tiled_shared_memory` and device support permit, it uses a reserved tiled
resource and commits ranges through `AllocateSparseHostGpuMemoryRange`;
otherwise it creates a fully committed resource.

`D3D12SharedMemory::UploadRanges` requests staging space from the provider's
upload pool, copies guest bytes, records D3D12 buffer copies and restores the
required state. Sparse tile mapping updates are direct-queue operations and
must be ordered with command-list work. Raw and power-of-two typed SRV/UAV
descriptor helpers expose the buffer to translated shaders and system compute
pipelines.

`CommitUAVWritesAndTransitionBuffer` places a UAV barrier when pending writes
exist and transitions to the requested state. The command processor collects
transition, aliasing and UAV barriers through `PushTransitionBarrier`,
`PushAliasingBarrier`, `PushUAVBarrier` and `SubmitBarriers`.

## GPU writes and readback

Memexport and resolves may write the shared-memory resource. After recording
the operation, the relevant path calls `SharedMemory::RangeWrittenByGpu`, which
invalidates dependent host resources and records that the guest CPU copy may
need readback.

Readback behavior is configuration-dependent:

- common `readback_resolve` defaults to `none`;
- common `readback_memexport` defaults true and
  `readback_memexport_fast` defaults true;
- D3D12 legacy aliases `d3d12_readback_resolve` and
  `d3d12_readback_memexport` default false; and
- `IssueDraw_MemexportReadbackFastPath` and `FullPath`, plus
  `IssueCopy_ReadbackResolvePath`, implement the alternatives.

`RequestReadbackBuffer` pools appropriately sized D3D12 readback resources.
Readback completion waits for the relevant submission before copying results
into guest memory. G1.5A records the branching behavior but does not assert a
Fable-selected path.

## Submission, queues and fences

`D3D12CommandProcessor::SetupContext` creates the direct command list,
allocators, fence/event, descriptor pools and GPU caches. The provider owns the
D3D12 device and direct queue. `BeginSubmission` selects a frame context,
reclaims resources against completed fences and begins cache submission state.

`EndSubmission`:

1. flushes deferred commands and barriers;
2. ends per-submission cache work;
3. closes and executes command lists on the direct queue;
4. signals the submission fence;
5. records resource/descriptor lifetime against that submission; and
6. rotates to the next frame context.

There are three frame contexts. Allocators and per-frame objects are reused
only after their fence has completed. `CheckSubmissionFence` updates completed
indices across SharedMemory, TextureCache, PrimitiveProcessor,
RenderTargetCache, descriptor/upload pools and deferred destruction.

`EndSubmission(true)` is the swap boundary. `OnPrimaryBufferEnd` may submit a
non-swap batch when `d3d12_submit_on_primary_buffer_end` is true. Thus a host
queue submission is not necessarily a guest frame, and a guest frame may
contain multiple submissions.

The presenter uses the same provider direct queue but has separate submission
trackers for guest-output refresh, UI and swap-chain painting. Resource
references and tracker waits bridge textures produced by the command processor
to the present command list without assuming CPU completion.

## Resource lifetime by subsystem

| Resource | Owner | Invalidation/retirement |
|---|---|---|
| guest physical mirror | `D3D12SharedMemory` | CPU invalidation callbacks, submission fence |
| converted textures/SRVs | `D3D12TextureCache` | watched guest ranges, LRU, submission completion |
| converted indices | `D3D12PrimitiveProcessor` | watched guest ranges, per-frame/submission completion |
| render targets/EDRAM | `D3D12RenderTargetCache` | ownership changes, cache clear, submission completion |
| PSOs/translations | `PipelineCache` | hash identity, async queues, storage and shutdown |
| transient descriptors/uploads/scratch | command processor/provider pools | explicit release index and completed fence |
| guest-output mailbox textures | `D3D12Presenter` | mailbox replacement and refresh/paint submission trackers |

`ClearCaches` is coordinated through the command processor and does not mean
guest memory is discarded. `ShutdownContext` waits/tears down in an order that
keeps in-flight resources valid, then releases caches, pools, lists, fences and
optional diagnostics.

## Errors and static limits

Failed allocation, upload, residency, transition-dependent setup or device
operation returns false/logs an exact GPU error. Device removal is logged with
`LogDeviceRemovalDiagnostics` and escalated through the fatal graphics-system
loss callback; automatic device recreation is TODO.

Static source establishes ownership and ordering, but not actual contention,
barrier sufficiency for a particular title sequence, upload/readback volume,
fence latency or cache pressure.

## Fable connection and unknowns

`UNKNOWN FOR FABLE II`

Evidence required: guest range requests/invalidations, resource keys,
GPU-written/readback spans, recorded barriers, queue submissions and completed
fence values correlated to a Fable frame.

Suggested later observation points: `SharedMemory::RequestRanges`,
`SharedMemory::RangeWrittenByGpu`, `D3D12SharedMemory::UploadRanges` and
`D3D12CommandProcessor::EndSubmission`.
