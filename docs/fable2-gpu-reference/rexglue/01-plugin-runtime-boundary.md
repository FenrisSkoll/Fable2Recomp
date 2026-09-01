# Plugin and runtime boundary

All ReXGlue locators in this chapter refer to repository
`https://github.com/rexglue/rexglue-sdk.git` at local pinned commit
`956c6a8b5da4c54b9899a2593e9c67c26de30194`.

## Build and load

`CONFIRMED` — Fable's `CMakeLists.txt` at
`c44e8c16f4422f9a828caf30899ac989170b8a8c` calls
`rexglue_setup_target(fable2 GPU_PLUGINS xenos)`. In
`cmake/rexglue_helpers.cmake`, function `rexglue_configure_target` resolves the
in-tree `rexgpu-xenos` or installed `rex::gpu-xenos` target and copies it next
to the consumer after linking. The application passes `--gpu_plugin=xenos` in
the established run helper.

`ReXApp::SetupPresentation` in `src/ui/rex_app.cpp` reads the init-only
`gpu_plugin` cvar, calls `rex::system::LoadGpuPlugin`, then calls
`IGraphicsSystem::SetupPresentation` before creating and attaching the window.
Failure to load or set up graphics is fatal to application initialization; it
does not silently choose a headless renderer.

`LoadGpuPlugin` in `src/system/gpu_plugin_loader.cpp`:

1. constructs `rexgpu-xenos.dll` beside the executable for Release;
2. loads it with immediate symbol resolution;
3. requires `rex_gpu_abi_version` and `rex_gpu_create`;
4. compares the returned ABI with `kGpuPluginAbiVersion` (`1`);
5. sends `GpuCreateInfo { struct_size, backend }`; and
6. stores the `DynamicLibrary` in a process-lifetime vector before returning a
   `unique_ptr<IGraphicsSystem>`.

The DLL is intentionally not unloaded during normal graphics shutdown because
guest threads may still have plugin code pages in use. The runtime, not the
loader, owns the returned graphics object.

## Exported ABI and backend construction

The source contract is in `include/rex/system/gpu_plugin.h`, types
`GpuCreateInfo`, `GpuAbiVersionFn`, `GpuCreateFn` and interface
`IGraphicsSystem` in `include/rex/system/interfaces/graphics.h`.

`plugin_main.cpp` validates ABI and structure size. For `backend="any"`, its
compile-time order is D3D12 then Vulkan. The active build has
`REX_HAS_D3D12` and no Vulkan, so `rex_gpu_create` returns a newly allocated
`D3D12GraphicsSystem`. A named unavailable backend returns null after an error.

The PE independently confirms ABI exports `rex_gpu_abi_version` at RVA
`0x1000` and `rex_gpu_create` at RVA `0x1010`. The two power-selection exports
are host adapter hints, not GPU ABI functions.

## Initialization and ownership

`Runtime::Setup` in `src/system/runtime.cpp` moves the application-supplied
graphics object into `graphics_system_` and calls `IGraphicsSystem::Setup`.
That convenience function calls presentation setup if required, then
`GraphicsSystem::SetupGuestGpu`.

`GraphicsSystem::SetupGuestGpu` in `src/graphics/graphics_system.cpp` owns the
following transition:

| Input | Transformation | Persistent output |
|---|---|---|
| `FunctionDispatcher` | obtains guest `Memory` | `memory_`, `function_dispatcher_` |
| `KernelState` | provides interrupts, XDK state and guest threads | `kernel_state_` |
| provider from presentation setup | reused; otherwise a headless provider is created | `provider_`, presentation-capability flag |
| backend factory | `CreateCommandProcessor` then `Initialize` | command processor and worker thread |
| guest virtual address `0x7FC80000` | `Memory::AddVirtualMappedRange` for 64 KiB | register read/write MMIO callbacks |
| `VdQueryVideoMode` and `vsync` | creates `XHostThread` named `GPU VSync` | guest vblank timing/interrupt source |

Setup also forwards the parsed `swap_post_effect` to the processor. A provider
created headlessly cannot later be upgraded to presentation; reversed call
order is rejected.

`GraphicsSystem::Shutdown` first shuts down the command processor, then stops
and joins the vblank guest host-thread, destroys the presenter on the UI thread
when required, and releases the provider. `Runtime::Shutdown` calls this before
destroying other runtime systems. The DLL handle remains loaded as described
above.

## XDK services, ring and interrupts

`src/kernel/xboxkrnl/xboxkrnl_video.cpp` owns the guest-facing exports:

| Guest export handler | ReXGlue callee/effect | Confidence |
|---|---|---|
| `VdSetGraphicsInterruptCallback_entry` | `IGraphicsSystem::SetInterruptCallback` | `CONFIRMED` |
| `VdInitializeRingBuffer_entry` | `IGraphicsSystem::InitializeRingBuffer` | `CONFIRMED` |
| `VdEnableRingBufferRPtrWriteBack_entry` | `IGraphicsSystem::EnableReadPointerWriteBack` | `CONFIRMED` |
| `VdGetSystemCommandBuffer_entry` | clears a `0x94`-byte guest buffer and writes `0xBEEF0000`, `0xBEEF0001` | `CONFIRMED` |
| `VdSwap_entry` | validates/physicalizes the front buffer and emits fetch plus `PM4_XE_SWAP` packets | `CONFIRMED` |

The first three delegate through `IGraphicsSystem` to `GraphicsSystem`, which
then updates `CommandProcessor`. If no graphics object exists, they warn and
return without inventing a local GPU implementation.

`VdSwap_entry` reads six big-endian dwords from the request, validates the
front-buffer virtual address, clears 64 ring dwords, writes a Type-0 texture
fetch describing the front buffer, writes `PM4_XE_SWAP` with signature,
physical address and dimensions, and terminates with a Type-2 NOP. It does not
call DXGI Present.

## Errors and tests

Loader failures distinguish absent file, dynamic-load failure, absent exports,
ABI mismatch and factory failure. Setup failures propagate `X_STATUS` to
`ReXApp`. `GraphicsSystem::OnHostGpuLossFromAnyThread` is a separate fatal path
with recovery still TODO.

No dedicated first-party GPU plugin/ABI tests were found under `tests` at the
pinned commit. This chapter is validated through source/blob identity, symbol
existence, PE exports/imports and the existing load log, not an ABI test suite.

## Fable connection and unknowns

`CONFIRMED` — accepted G1 proves `sub_82BA34D8`
`[0x82BA34D8, 0x82BA3BFC)` calls `VdGetSystemCommandBuffer` and `VdSwap`.
Existing `fable2-run-048.log` confirms the plugin loader and D3D12 provider
initialized.

`UNKNOWN FOR FABLE II`

Evidence required: one correlated initialization and swap event showing the
specific Fable call, emitted packet, processor receipt and presenter refresh.

Suggested later observation points: `VdSwap_entry` and
`CommandProcessor::ExecutePacketType3_XE_SWAP`.
