# Ownership and transition contract

Three states are deliberately separate: **current accepted emulation**, a
**future isolated prototype**, and a **future production title renderer**.
Only the first exists in Fable. Proposed owners below are design constraints,
not evidence of implemented interfaces.

The initial prototype should consume separately authorized replay inputs in a
separate process/device or separate run. It must not issue native work against
targets concurrently owned by the running Xenos renderer. A later in-game
default-off skeleton needs a separately reviewed lifecycle integration before
it borrows ReXGlue objects. No second window swapchain or competing queue owner
is assumed to be safe.

Current ownership is SOURCE-CONFIRMED by the SDK sources in the
[pin catalog](evidence/reference-pins.json), supplemented by the accepted
[ownership reassessment](../../fable2-gpu-reference/07-boundary-and-ownership-reassessment.md)
and [host-UI contract](../../fable2-gpu-reference/08-system-ui-and-presentation-contract.md).
Proposed allocations are BOUNDED INFERENCE; transitions are UNRESOLVED unless
explicitly noted. “Prototype” below means isolated replay; it is not a mixed
live frame.

| Responsibility | Current accepted owner | Isolated prototype | Eventual production owner | Transition requirement / unresolved risk |
|---|---|---|---|---|
| Guest ring and indirect buffers | Guest produces; ReXGlue command processor consumes PM4 through runtime GPU setup | No live ring access; replay consumes its own ordered records | Guest-facing compatibility path must consume/acknowledge remaining obligations, or prove unused; title adapter supplies native work | SOURCE-CONFIRMED current. UNRESOLVED suppression/retirement of legacy work; cannot stop ring consumption because images look native |
| Register/fetch state | ReXGlue register file/command processor and texture/pipeline caches | Snapshot normalized required state, with explicit missing fields | Title adapter owns rendering state; compatibility owner retains any guest-visible emulated state | Prove complete state coverage, predication and direct writers; no shared mutable register ownership |
| Guest memory and resource tracking | ReXGlue Memory plus SharedMemory/page watches; guest owns allocation semantics | Owned immutable replay copies, explicit range/generation metadata | ReXGlue retains guest memory facilities; renderer tracks native views/uploads and fences; adapter proves object generations | Guest address reuse, aliasing, CPU changes, GPU writes and lifetime must be joined; an invalidation generation is not an allocation generation |
| Shader translation and identity | ReXGlue shader analysis, backend translator and pipeline cache | Explicit shader pair/feature set, original identity and translator version | Native shader system, preferably original-microcode fidelity; reuse suitable SDK/tool components only after binding/license qualification | Original bytes, constants, fetch, specialization and numeric behavior required; no arbitrary unsupported-shader success |
| Host textures and buffers | ReXGlue texture/shared-memory/RT caches | Prototype owns all replay resources | Native renderer owns rendering caches; ReXGlue still owns resources for retained GPU services if any | Prove resource-producing guest work, upload visibility, alias handling and destruction after completion; duplicated caches need an explicit coherence policy |
| EDRAM/resolve equivalents | ReXGlue RT cache owns EDRAM paths, alias ownership and resolves to guest memory | Explicit initial color/depth and resolve outputs for bounded workload | Native pass graph/targets plus compatibility adapter for guest-visible resolves | Must prove producer/consumer dependencies including future reads; discarding EDRAM is unsafe without coverage |
| Submission queues and fences | Provider supplies host device/direct queue; command processor records/submits/retires guest work; presenter has its own composition coordination | Prototype owns queue/command allocators/fences on isolated device | One documented queue/submission owner, either a reviewed ReXGlue service or native owner; presenter coordination explicit | Do not double-submit borrowed command lists; allocators/resources survive fence completion; partial submission has no rollback |
| Interrupts, completion, vblank | ReXGlue GraphicsSystem/command processor and runtime GPU/kernel services | NOT APPLICABLE to isolated replay; host completion only | ReXGlue services retained with a proved native-completion bridge where guest waits depend on it | Guest events cannot be satisfied from CPU enqueue alone; queries/memexport/readback must preserve behavior; no invented visibility results |
| Swapchain, resize, presentation | ReXGlue presenter/provider owns host output, guest-output mailbox and composition | Own independent output; no live guest mailbox writes | Prefer existing presenter and one explicit native output handoff | Need device/queue compatibility, image state, extent/format lifetime, resize drain and mailbox completion contract; current plugin ABI does not provide a semantic handoff |
| Window and input | ReXGlue ReXApp/window/input, title application configuration | Minimal separate prototype window/input for viewing only | Retain ReXGlue window/input | Preserve thread affinity, focus, resize and close delivery; native renderer does not replace input/runtime services |
| Keyboard and achievement overlays | ReXGlue host UI drawers/composition and XAM completion plumbing | NOT APPLICABLE to replay validation | Retain ReXGlue UI after guest image and before present | Preserve focus/modal completion and achievement callbacks; no false completion from missing overlay, no duplicate composition. No broad XAM redesign |
| Shutdown and device loss | ReXGlue GraphicsSystem/presenter callbacks; normal ReXApp close currently calls `std::_Exit(0)` after logging | Prototype explicitly stops recording, waits/handles failure and destroys owned resources | Coordinated native teardown plus existing runtime close/device-loss contract | Current normal exit is not proof of complete asynchronous GPU destruction. Device loss must stop safely/report failure; automatic renderer fallback remains unproved |

For current source navigation: `graphics_system.cpp:SetupGuestGpu/Shutdown`,
`command_processor.cpp:ExecutePacketType3`,
`d3d12/command_processor.cpp:IssueDraw/EndSubmission/CheckSubmissionFence`,
`shared_memory.cpp:RequestRanges/RangeWrittenByGpu/MemoryInvalidationCallback`,
`pipeline/render_target/cache.cpp:Update/ChangeOwnership`,
`ui/d3d12/d3d12_provider.cpp:D3D12Provider::Initialize`,
`ui/presenter.cpp:RefreshGuestOutput/ExecuteUIDrawersFromUIThread`,
`ui/d3d12/d3d12_presenter.cpp:PaintAndPresentImpl`, and
`ui/rex_app.cpp:SetupPresentation/OnClosing`. Paths are under SDK `src/` and
resolved exactly by the catalog. The accepted chapters retain details beyond
this ownership gate.

## Selection and failure contract to qualify later

Start with startup selection, defaulting to the accepted Xenos renderer.
Selection precedes guest GPU initialization and native recording. Unsupported
configuration may choose the default before work begins, with an explicit
reason. It must not silently switch after suppressing guest operations or
submitting native work. Runtime services for saves, XAM, input, audio, threading
and guest memory remain ReXGlue responsibilities.

A renderer-neutral output image alone solves presentation plumbing. It does
not transfer ring, cache, EDRAM, interrupts or guest-visible resource ownership.
The Skate callback is useful precedent for a bounded borrowed output context,
but the canonical SDK lacks that callback and its suppression policy is
title-specific. An SDK API change would require separate authorization.

A future live transition would need an explicit stop point, drained queues,
closed guest work, resource reconstruction/coherence, restored legacy targets,
valid query/completion state and a newly published output. None is proved here.
For early development, failure means abandon the isolated workload or end the
native run cleanly and restart the accepted backend. It does not mean execute
the original guest rendering retroactively in the same partially submitted frame.

If a pass is proposed for live replacement, its acceptance dossier must identify
every input and prior writer, output and later reader, alias/view, guest-memory
write, query and submission edge. Lack of any required edge keeps that pass in
isolated replay/separate-run comparison. “Independent” means dependency closure,
not merely a convenient function boundary or a visually separate effect.
