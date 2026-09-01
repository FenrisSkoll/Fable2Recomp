# Xenia Canary register state and draw processing

## Evidence basis

All source locators refer to
`xenia-canary/xenia-canary@3a44f20c7bc66db1da583e8a6f0ab740e31908e9`.
The document describes source behavior only.

## Register file and metadata

`src/xenia/gpu/register_file.h:RegisterFile` owns a fixed
`kRegisterCount == 0x5003` dword array.
`src/xenia/gpu/register_file.cc:RegisterFile::RegisterFile` installs reset
defaults. `RegisterFile::GetRegisterInfo` exposes metadata generated from
`src/xenia/gpu/register_table.inc`. These are **CONFIRMED** source facts.

The command processor transforms PM4 register writes through:

```text
ExecutePacketType0 / ExecutePacketType1 / SET_* handlers
  -> CommandProcessor::WriteRegister
     -> RegisterFile storage
     -> common scratch, coherency, and gamma side effects
     -> backend binding invalidation
```

`CommandProcessor::WriteRegister` handles common state. D3D12's optimized
`WriteRegisterForceinline` additionally invalidates affected constant-buffer
bindings and reports fetch-constant changes to the texture cache. Vulkan's
`WriteRegister` performs its own constant-buffer mask and texture-fetch
invalidation. Therefore there is no single universal “all GPU state dirty” bit;
host state is lazily reassembled by subsystem at draw time.

### Coherency

`COHER_STATUS_HOST` invokes `CommandProcessor::MakeCoherent`.
**CONFIRMED:** the function clears the requested status. **CONFIRMED
limitation:** its source TODO says resource caches should also be notified; that
notification is absent at the pin. This corpus does not infer the runtime impact.

## Draw packet initiation

`COMMAND_PROCESSOR::ExecutePacketType3Draw` handles `DRAW_INDX` and
`DRAW_INDX_2`-style payloads. It decodes primitive type, index source,
endianness, count, visibility predicate, and initiator state. DMA-indexed and
auto-index forms proceed to backend `IssueDraw`; immediate-index data is
reported unsupported.

Both backend draw implementations follow the same high-level dependency chain:

```text
IssueDraw
  -> copy mode? IssueCopy / Resolve
  -> validate pitch and active shaders
  -> Shader::AnalyzeUcode-derived requirements
  -> begin submission
  -> PrimitiveProcessor::Process
  -> RenderTargetCache::Update
  -> translate/configure pipeline
  -> request textures, samplers, vertex/index ranges, and constants
  -> bind descriptors/resources
  -> host indexed or non-indexed draw
```

The concrete endpoints are
`D3D12CommandProcessor::IssueDraw` in
`src/xenia/gpu/d3d12/d3d12_command_processor.cc` and
`VulkanCommandProcessor::IssueDraw` in
`src/xenia/gpu/vulkan/vulkan_command_processor.cc`.

## Primitive processor

`src/xenia/gpu/primitive_processor.cc:PrimitiveProcessor::Process` takes the
guest primitive, tessellation state, index format/endian/reset state, and host
capabilities. It returns `PrimitiveProcessor::ProcessingResult`, including the
host topology, converted index range, and expansion requirements.

**CONFIRMED transformations include:**

- triangle fan, line loop, and quad-family conversion where the host path needs
  normalized indices;
- point and rectangle expansion in the translated vertex path;
- supported tessellation cases and normalization of tessellated strip/fan
  output to triangle lists;
- 16/32-bit index handling, guest endian conversion, reset-index behavior, and
  24-bit index treatment; and
- a converted-index cache watched for guest-memory invalidation.

The current tessellated strip/fan normalization is also explained by primary
history commit `3eab2b8b39442e32537610c955fbb8db0c2a6561`,
`[GPU] Handle tessellated triangle strip and fan draws`. That rationale is
**CONFIRMED** within the available pinned-clone history.

## Draw extents

`src/xenia/gpu/draw_extent_estimator.cc:DrawExtentEstimator::Estimate`
calculates the affected region used by downstream render-target work. It may
interpret enough of the analyzed vertex shader on the CPU to estimate maximum
Y; when it cannot, it falls back to register/scissor-derived bounds.

- The implementation and fallback are **CONFIRMED**.
- Exact bounds for a concrete shader are **UNKNOWN** without running its state.

## Predication and conditional behavior

Type 3 predicate gating uses the command processor's bin select/mask state.
This is separate from a fully general host conditional-rendering facility.

- Predicated packet execution is **CONFIRMED** in
  `COMMAND_PROCESSOR::ExecutePacket`.
- Predicated swaps are **CONFIRMED** to be skipped.
- `VIZ_QUERY` is **CONFIRMED** to synthesize visible status.
- A claim that Canary provides complete Xenos conditional rendering is
  therefore not supported.

## Occlusion queries

The shared command processor implements a ZPD report lifecycle around
`BeginZPDReport`, `EndZPDReport`, report events, and report resolution. D3D12 and
Vulkan provide host query objects for the traditional render-target paths and
shader-accessed counters for ROV/fragment-shader-interlock paths.

The `occlusion_query` configuration materially changes behavior:

| Mode family | Source-level intent | Confidence |
|---|---|---|
| fake | Avoid relying on host visibility results. | CONFIRMED |
| `fast` / `fast-alt` | Lower-overhead query/counter strategies. | CONFIRMED |
| strict | More conservative report ordering/accuracy strategy. | CONFIRMED |

Primary history commit
`fbd620c22b44638b66a70bba80d6f30d55a10924`,
`[GPU] Implement ZPD occlusion queries`, confirms the report lifecycle, split
segments, D3D12/Vulkan query versus ROV/FSI counter split, selectable modes, and
synthetic QueryBatch behavior. The exact parity and cost of each mode remain
**UNKNOWN** without hardware and runtime evidence.

## What leaves draw processing

- copy mode leaves as a backend resolve/copy transaction;
- ordinary draws leave as a configured backend pipeline plus vertex/index,
  texture, constant, descriptor, render-target, and shared-memory bindings;
- queries leave as host query/counter work and eventual guest report data;
- host calls are `DrawInstanced` / `DrawIndexedInstanced` for D3D12 and
  `CmdVkDraw` / `CmdVkDrawIndexed` for Vulkan.

Which path is taken by Fable II is **NOT APPLICABLE** to G1.5B.
