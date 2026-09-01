# Command processor and register state

All locators refer to ReXGlue commit
`956c6a8b5da4c54b9899a2593e9c67c26de30194`.

## Inputs, worker and owned state

`CommandProcessor` is declared in
`include/rex/graphics/command_processor.h` and implemented in
`src/graphics/command_processor.cpp`. It receives the initialized ring base and
size, MMIO write-pointer updates, guest memory, the register file and the
graphics-system interrupt callback.

Its persistent state includes:

- ring read/write pointers, optional read-pointer writeback and update
  frequency;
- worker thread, write-pointer event, pause controls and call queue;
- `RegisterFile`, vertex and pixel shader pointers, gamma state and swap count;
- ME initialization data, bin select/mask and bin-render predicate state; and
- query/conditional state used by packet handlers.

`CommandProcessor::WorkerThreadMain` waits for write-pointer work, consumes the
current span through `ExecutePrimaryBuffer`, updates the read pointer and guest
writeback, executes queued host calls, and invokes `OnPrimaryBufferEnd`.
Indirect buffers are translated from guest GPU/CPU addresses and recursively
passed to packet execution.

## Packet decoding

`ExecutePacket` separates the four packet types:

| Packet | Function | Effect |
|---|---|---|
| Type 0 | `ExecutePacketType0` | sequential register writes |
| Type 1 | `ExecutePacketType1` | two register writes |
| Type 2 | `ExecutePacketType2` | NOP |
| Type 3 | `ExecutePacketType3` | opcode-specific operations and triggers |

The pinned Type-3 dispatcher has source-confirmed handlers for `ME_INIT`,
`NOP`, `INTERRUPT`, `XE_SWAP`, `INDIRECT_BUFFER`/`PFD`, `WAIT_REG_MEM`,
`REG_RMW`, `REG_TO_MEM`, `MEM_WRITE`, `COND_WRITE`, event-write variants,
`DRAW_INDX`, `DRAW_INDX_2`, constant loads, `IM_LOAD`,
`IM_LOAD_IMMEDIATE`, `INVALIDATE_STATE`, `VIZ_QUERY`, bin select/mask and idle
wait behavior. Unrecognized opcodes are logged/asserted and their remaining
payload is skipped; source presence must not be interpreted as complete Xenos
coverage.

`ExecutePacketType3_INTERRUPT` asks `GraphicsSystem::DispatchInterruptCallback`
to enter the configured guest callback. `XE_SWAP` validates the swap signature,
passes front-buffer address/dimensions to virtual `IssueSwap`, and increments
the swap counter. Draw handlers build an `IndexBufferInfo` and call virtual
`IssueDraw`. `IM_LOAD`/`IM_LOAD_IMMEDIATE` call virtual `LoadShader`.

## Register file and side effects

`RegisterFile` in `include/rex/graphics/register_file.h` owns `0x5003` dwords.
`CommandProcessor` separately owns `extended_register_values_` for indices
outside the fixed table. The generated
`include/rex/graphics/register_table.inc` supplies names and type metadata;
typed accessors expose fetch constants and other structures.

`CommandProcessor::WriteRegister` stores the value and performs common side
effects such as write-pointer/gamma behavior. Bulk constant handlers use the
same register ranges. `D3D12CommandProcessor::WriteRegister` in
`src/graphics/d3d12/command_processor.cpp` adds backend invalidation: vertex
fetch residency, current pipeline, bindings and other derived state are marked
dirty according to the written register.

This division is important: the register file is backend-independent Xenos
state, while the meaning of a write for host cache reuse is backend-specific.

## Coherency, waits and invalidation

`ExecutePacketType3_WAIT_REG_MEM` supports memory or register comparison and
uses `PrepareForWait`, host sleep/yield, then `ReturnFromWait`. A wait involving
`COHER_STATUS_HOST` calls `CommandProcessor::MakeCoherent`.

`MakeCoherent` logs the range and clears the coherency status. A source TODO
still calls for notifying the resource cache; G1.5A therefore does not claim
full coherency parity. `INVALIDATE_STATE` consumes the packet but the base
handler currently discards the mask before calling no general invalidation
implementation. Backend-specific memory watches provide additional, separate
cache invalidation described later.

## Draw, copy and query triggers

The packet layer does not construct host graphics objects. It forwards current
state at trigger time:

- `DRAW_INDX` and `DRAW_INDX_2` -> `IssueDraw`;
- copy-mode draw -> D3D12 `IssueCopy` after backend inspection;
- `PM4_XE_SWAP` -> `IssueSwap`;
- shader loads -> backend shader cache; and
- `VIZ_QUERY`/event writes -> query handling or configured fallback.

Immediate-index draws are explicitly unsupported by the common path and are
discarded after logging. Occlusion query handling may use host D3D12 queries;
when unavailable/disabled the common configuration can write a fake sample
count (`query_occlusion_fake_sample_count`, default `1000`). Predication parity
is incomplete.

## Configuration and failure paths

Relevant common cvars in `src/graphics/command_processor.cpp` include `vsync`,
`occlusion_query_enable`, `readback_resolve`, `readback_memexport`,
`readback_memexport_fast`, `query_occlusion_fake_sample_count` and
`async_shader_compilation`. D3D12 adds `d3d12_bindless`, readback toggles and
`d3d12_submit_on_primary_buffer_end`.

Errors may log and skip a packet/draw, return failure to the worker, or reach
the host-GPU fatal path. The exact consequence must be read at each call site;
there is no single universal unsupported-feature policy.

## Fable connection and unknowns

`CONFIRMED` — Fable reaches the `PM4_XE_SWAP` input through accepted G1's
`sub_82BA34D8` -> `VdSwap` call.

`UNKNOWN FOR FABLE II`

Evidence required: bounded packet/opcode and register-write events for the
pinned TU1 image, including indirect-buffer addresses and the first failing or
skipped operation.

Suggested later observation points: `CommandProcessor::ExecutePacketType3`,
`D3D12CommandProcessor::WriteRegister` and
`D3D12CommandProcessor::IssueDraw`.
