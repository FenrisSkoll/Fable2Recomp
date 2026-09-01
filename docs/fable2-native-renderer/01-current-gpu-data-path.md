# Current Fable II GPU data path

## Conclusion

The current `rexgpu-xenos.dll` ABI is below the semantic interception point
needed for a title-specific renderer. By the time the plugin command processor
handles a draw, it is reconstructing state from a physical ring buffer, PM4
packets, Xenos registers, and guest shader microcode. Replacing that ABI would
therefore reproduce a substantial Xenos emulator, not translate a normalized
Fable render-command stream.

The confirmed higher boundary is inside Fable's statically linked Xbox
graphics implementation. Device setup and presentation still carry device,
front-buffer/resource, dimensions, and lifecycle meaning before they call the
`Vd*` kernel imports and emit packets. The complete high-level method table is
not yet recovered.

## End-to-end path

```text
recompiled Fable/Lionhead code
  -> statically linked Xbox D3D/XDK functions in exact TU1 image
     -> device object and state/resource/shader methods (partly unmapped)
     -> command/ring construction and Vd* imports
        -> ReXGlue xboxkrnl Vd HLE + guest physical memory/MMIO
           -> IGraphicsSystem / Xenos CommandProcessor
              -> PM4 packet dispatch + Xenos register/shader interpretation
                 -> D3D12 or Vulkan backend resources/commands
                    -> ReXGlue presenter and host swapchain
```

### 1. Recompiled guest and static Xbox graphics layer

The exact generated TU1 output contains direct calls to the imported video
services:

| Generated function | Confirmed direct imports / role |
|---|---|
| `sub_82BA2830` | `VdInitializeRingBuffer`, `VdEnableRingBufferRPtrWriteBack`, `VdSetSystemCommandBufferGpuIdentifierAddress`; allocates/configures guest command transport |
| `sub_82BA34D8` | `VdGetSystemCommandBuffer`, `VdSwap`; constructs the final swap-related command sequence |
| `sub_82BA6990` | `VdInitializeEngines`, `VdSetGraphicsInterruptCallback`; initializes the device and calls `sub_82BA2830` |
| `sub_82BA6C18` | `VdSetGraphicsInterruptCallback`, `VdShutdownEngines`; shutdown path |
| `sub_82BA6968` | `VdShutdownEngines`; compact shutdown helper |

`sub_82B6F6C0` allocates `0x5E80` bytes and passes that object plus a
`0x7C`-byte initialization/presentation block into `sub_82BA6990`.
`sub_82B6EA60` is a title-level orchestration caller. `sub_82B6FA48` coordinates
a frame/present call into `sub_82BA34D8`. These roles are strong hypotheses,
not confirmed public API names.

This establishes two separate layers in TU1:

- high-level/title wrappers with object and presentation meaning; and
- lower Xbox graphics functions that initialize and feed raw command
  transport.

Observed guest structures remain deliberately partial. The device-like
allocation is exactly `0x5E80` bytes; `sub_82BA6990` initializes critical
sections at offsets `0x3A60` and `0x3A7C`; its initialization/presentation
input block is `0x7C` bytes. Generated calls reach the `__imp__Vd*` import
thunks directly. A guest graphics interrupt callback is installed through
`VdSetGraphicsInterruptCallback`, and the command-ring/writeback addresses are
guest-visible. ReXGlue also exposes `VdGlobalDevice`, but SDK source notes that
the runtime does not use that guest-visible device value as a host semantic
device object.

The title necessarily uses object/function tables for the remaining static
graphics methods, and generated indirect dispatch is visible in the wider
program, but G1 did not establish the exact device vtable base, slot map, or
resource class layouts. Those fields are not inferred from the UnleashedRecomp
layout. Callback/function-table recovery is a G2 discovery task and remains
subject to the existing Phase 4 evidence rules.

### 2. ReXGlue imports, guest memory, and interrupts

ReXGlue's `xboxkrnl_video.cpp` implements the `Vd*` services used above.
`VdInitializeRingBuffer` and related calls connect guest physical buffers and
writeback state to `IGuestGpu`. Graphics MMIO is registered around
`0x7FC80000`, and the graphics system owns vblank/interrupt delivery and the
guest callback configured by `VdSetGraphicsInterruptCallback`.

`VdSwap` does not call a semantic host `Present`. It decodes a six-dword guest
texture fetch and writes 64 dwords into the primary ring, including a Type-0
fetch packet, `PM4_XE_SWAP`, a signature, physical front-buffer address,
dimensions, and a NOP. This is direct proof that the semantic front-buffer
operation has already been serialized into Xenos commands at this boundary.

Ring writeback, interrupt callbacks, and guest memory lifetime are observable
side effects that any forwarding hook must preserve. The shadow-capture design
therefore forwards to the original guest implementation rather than attempting
to reproduce those effects in G1/G2.

### 3. Plugin ABI and loader

`include/rex/system/gpu_plugin.h` defines GPU ABI version 1. The plugin exports
`rex_gpu_abi_version` and `rex_gpu_create`; `GpuCreateInfo` contains only
`struct_size` and a requested backend (`any`, `d3d12`, or `vulkan`). The
returned `IGraphicsSystem` supplies:

- presentation setup;
- the guest GPU/command-processor interface;
- presenter/provider access;
- ring-buffer, interrupt, writeback, shader-storage, and shutdown operations.

`src/system/gpu_plugin_loader.cpp` loads `rexgpu-xenos.dll` beside the
executable, verifies the ABI, and retains the library for process lifetime.
`src/system/runtime.cpp` wires it into runtime setup and shuts graphics down
before other systems. A null graphics plugin is described by source as native
rendering mode, but no Fable-native renderer is supplied by that switch.

### 4. Raw Xenos command processing

`CommandProcessor` consumes the guest physical ring and decodes Type 0, Type 1,
and PM4 packets. Its opcode paths handle register writes, draws, indexed draws,
copies/resolves, shader loads, queries, waits, synchronization, and
`PM4_XE_SWAP`. D3D12 and Vulkan command processors derive a host draw from the
current Xenos register file, fetched guest shader microcode, vertex fetch
state, textures, samplers, EDRAM configuration, and packet arguments.

This layer possesses enough information to emulate the resulting GPU command,
but not the original API call boundaries, object lifetimes, redundant state
changes, lock/unlock intent, engine pass identity, or the caller that requested
the operation. It is the behavioural oracle, not the preferred semantic seam.

### 5. Host backend, swap, and packaging

On Windows, `backend=any` attempts D3D12 first when compiled, then Vulkan as a
fallback. `IssueSwap` copies or resolves the emulated front buffer into the
presenter path; the D3D12/Vulkan presenter owns the host swapchain and final
presentation. `IssueCopy` implements the Xenos EDRAM copy/resolve operation,
not a generic high-level resource copy.

Fable's top-level build calls:

```cmake
rexglue_setup_target(fable2 GPU_PLUGINS xenos)
```

ReXGlue CMake helpers build/stage/install the selected plugin beside the game
executable. G1 did not modify this selection or packaging behaviour.

## Where semantics are retained

| Boundary | Information retained | Information already lost | G1 disposition |
|---|---|---|---|
| Lionhead renderer functions | pass/queue/engine intent may exist | exact contracts and most addresses are unknown | discovery lead only |
| Static Xbox D3D/XDK methods | guest device/resource identities, API operation, arguments, ordering, lock/unlock and state intent | engine-level reason for operation | **primary seam** |
| `Vd*` functions / ring setup | transport lifecycle; `VdSwap` still sees a front-buffer fetch and dimensions | most earlier API-call and object semantics | correlation/oracle seam |
| Xenos PM4 command processor | packets, register state, shaders, resolves, draws and synchronization | API boundaries, object methods, redundant calls, engine identity | retain as behavioural oracle |
| Backend presenter | host image and swap timing | nearly all guest rendering meaning | validation only |

## Seam verdict

Replacing `rexgpu-xenos.dll` at ABI version 1 is technically possible but is
not a title-specific native renderer: it requires implementing ring parsing,
Xenos registers, shaders, EDRAM, formats, synchronization, and presentation.
The proposition is rejected as the primary architecture.

The evidence instead supports intercepting confirmed static Xbox graphics
functions before command generation and forwarding them to their original
generated bodies. The current plugin then remains unchanged as both renderer
and oracle while the semantic inventory is expanded. See
[`03-candidate-hook-inventory.md`](03-candidate-hook-inventory.md) and
[`04-architecture-options.md`](04-architecture-options.md).
