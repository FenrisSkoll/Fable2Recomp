# Xenia Canary initialization and command processor

## Evidence basis

All source locators in this document refer to
`xenia-canary/xenia-canary@3a44f20c7bc66db1da583e8a6f0ab740e31908e9`.
No runtime or title-use claim is made.

## Initialization and ownership

| Stage | Concrete symbols and result | Confidence |
|---|---|---|
| Backend selection | `src/xenia/app/xenia_main.cc:EmulatorApp::CreateGraphicsSystem` reads `gpu`. On Windows, `any` tries `D3D12GraphicsSystem`, then `VulkanGraphicsSystem`; explicit `null` creates `NullGraphicsSystem`. | CONFIRMED |
| System construction | `src/xenia/emulator.cc:Emulator::Setup` establishes Memory, Processor, APU, GraphicsSystem, input, and KernelState dependencies and calls `GraphicsSystem::Setup`. | CONFIRMED |
| GPU common setup | `src/xenia/gpu/graphics_system.cc:GraphicsSystem::Setup` creates the presenter and command processor, initializes the latter, installs the MMIO range, and starts the limiter thread. | CONFIRMED |
| D3D12 setup | `src/xenia/gpu/d3d12/d3d12_graphics_system.cc:D3D12GraphicsSystem::Setup` creates a `D3D12Provider`; `CreateCommandProcessor` creates `D3D12CommandProcessor`. | CONFIRMED |
| Vulkan setup | `src/xenia/gpu/vulkan/vulkan_graphics_system.cc:VulkanGraphicsSystem::Setup` creates a `VulkanProvider`; `CreateCommandProcessor` creates `VulkanCommandProcessor`. | CONFIRMED |
| Shader storage | `src/xenia/emulator.cc:Emulator::Setup` dispatches `GraphicsSystem::InitializeShaderStorage` asynchronously during title startup. Its source comment permits skipped draws until loading finishes. | CONFIRMED source behavior/comment |
| Shutdown | `src/xenia/gpu/graphics_system.cc:GraphicsSystem::Shutdown` shuts the command processor before destroying limiter, presenter, and provider state; `Emulator` then continues reverse dependency teardown. | CONFIRMED |

`GraphicsSystem` receives `Memory`, and later the `Processor` and
`KernelState`. Its owned `RegisterFile` is reserved in guest-addressable
memory by `RegisterFile::Initialize`. The graphics MMIO mapping begins at
`0x7FC80000`, uses mask `0xFFFF0000`, and a size mask of `0x0000FFFF`
(`GraphicsSystem::Setup`). MMIO writes reach
`GraphicsSystem::WriteRegister`; kernel exports supply interrupt and ring
callbacks.

The persistent common state is declared by
`src/xenia/gpu/graphics_system.h:GraphicsSystem`: provider, presenter,
register file, command processor, interrupt callback/user data, vblank event and
thread. Device loss enters `GraphicsSystem::OnHostGpuLoss`; it reports a
fatal error. Recreation is a source TODO.

## Ring entry points

The Xbox kernel boundary is in
`src/xenia/kernel/xboxkrnl/xboxkrnl_video.cc`.

- `VdSetGraphicsInterruptCallback` installs the guest callback through
  `GraphicsSystem::SetInterruptCallback`.
- `VdInitializeRingBuffer` delegates the physical base and size exponent to
  `GraphicsSystem::InitializeRingBuffer`.
- the write-pointer export delegates to
  `GraphicsSystem::UpdateRingBufferWritePointer`.
- `VdSwap_entry` validates the front-buffer fetch, byte-swaps its six dwords,
  converts its address to physical form, validates dimensions/format, clears the
  command buffer, writes a type 0 fetch-constant update, then emits
  `PM4_XE_SWAP` with `kSwapSignature`, address, width, and height. Remaining
  slots are type 2 packets.

**CONFIRMED.** `VdSwap_entry` constructs guest GPU work; it does not call the
host presenter itself.

`CommandProcessor::InitializeRingBuffer` calculates byte capacity as
`1 << (size_log2 + 3)`, stores the physical read/write state, and wakes the
worker. `UpdateWritePointer` publishes the guest write pointer and signals the
worker event.

## Command thread

`src/xenia/gpu/command_processor.cc:CommandProcessor::WorkerThreadMain`
runs on the `GPU Commands` `XHostThread`. It owns execution ordering for:

1. queued host callbacks;
2. primary-ring packet consumption;
3. read-pointer writeback; and
4. backend submission and cache maintenance triggered by packets.

The ring reader uses guest physical memory. An indirect-buffer packet calls
`ExecuteIndirectBuffer`, temporarily swaps the reader to the sub-ring, runs
the requested dword span recursively, and restores the previous reader.

The separate `GPU Frame limiter` thread lives in `GraphicsSystem`. It
provides vblank/limiting behavior; it is not the D3D12 `Present` or Vulkan
`vkQueuePresentKHR` call.

## PM4 decoder

The implementations are generated through
`src/xenia/gpu/pm4_command_processor_implement.h` for each concrete command
processor.

| Packet | Transformation | State/output | Confidence |
|---|---|---|---|
| Type 0 | Writes sequential register indices through `WriteRegister`. | Register file and write side effects. | CONFIRMED |
| Type 1 | Writes two explicit registers. | Register file and write side effects. | CONFIRMED |
| Type 2 | Consumes a no-op packet. | No guest state transformation. | CONFIRMED |
| Type 3 | Decodes opcode/count/predicate and dispatches a named handler. | Draw, copy, shader load, waits, events, queries, indirect buffers, coherency, interrupts, or swap. | CONFIRMED |

Predicated type 3 packets use `bin_select_` and `bin_mask_`. Predicated
swaps are explicitly skipped rather than conditionally presented. Draw packet
handlers parse the initiator and DMA/auto-index fields, reject unsupported
immediate-index forms, and call backend `IssueDraw`.

### Operations with immediate architectural effects

- `WAIT_REG_MEM` polls a register or memory value and may sleep according to
  wait/vsync behavior.
- `PM4_INTERRUPT` dispatches the installed callback to a selected guest CPU
  index.
- `EVENT_WRITE_SHD` writes guest data/counter values.
- `EVENT_WRITE_EXT` synthesizes full-screen extent values.
- `COHER_STATUS_HOST` reaches `CommandProcessor::MakeCoherent`.
- `IM_LOAD` and `IM_LOAD_IMMEDIATE` call backend `LoadShader` and update
  the active vertex or pixel shader.
- `XE_SWAP` calls backend `IssueSwap`.

### Incomplete or synthetic behavior

- **CONFIRMED.** `INVALIDATE_STATE` reads its mask but has no implemented
  invalidation action and carries a TODO.
- **CONFIRMED.** `VIZ_QUERY` writes a synthetic visible result; it is not a
  complete host conditional-rendering implementation.
- **CONFIRMED.** `EVENT_WRITE_EXT` uses a synthetic full-screen extent.
- **UNKNOWN.** Static inspection cannot determine whether a guest relies on
  these incomplete/synthetic paths or what packet stream it produces.

## Interrupt and shutdown ordering

The guest installs the graphics callback through the kernel video export.
`GraphicsSystem::DispatchInterruptCallback` schedules the callback on the
selected guest processor. Vblank state is independently produced by the
graphics-system thread.

Shutdown first prevents further backend command work through
`CommandProcessor::Shutdown`, then stops limiter/presenter/provider state.
Backend command-processor shutdown waits for or retires its queue-owned
resources as required by that API. Static source establishes ordering, not the
latency or deadlock behavior on a concrete host.
