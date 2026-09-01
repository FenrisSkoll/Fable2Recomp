# Presentation, backends, system UI and errors

All ReXGlue locators refer to commit
`956c6a8b5da4c54b9899a2593e9c67c26de30194`.

## Active D3D12 backend

`rex_gpu_create` in `src/graphics/plugin_main.cpp` returns
`D3D12GraphicsSystem` for `backend=any` in the active build.
`D3D12GraphicsSystem::CreateProvider` delegates to `D3D12Provider::Create`.

`D3D12Provider::Initialize` in `src/ui/d3d12/d3d12_provider.cpp` dynamically
loads DXGI/D3D12 entry points, enumerates/selects an adapter, creates a feature
level 11.0 D3D12 device and a direct queue, then queries binding, ROV,
programmable-sample, tiled-resource and related capabilities. The current DLL
does not statically import D3D12/DXGI for this reason.

Existing `fable2-run-048.log` is runtime evidence that this artifact loaded the
xenos plugin, selected `NVIDIA GeForce RTX 5080` and enumerated Direct3D 12
features. It does not prove any later Fable draw, resolve or present.

Vulkan common-boundary peers exist under `src/graphics/vulkan`,
`src/ui/vulkan` and the SPIR-V translator. They are `NOT APPLICABLE` to the
pinned DLL because its SDK cache has `REXGLUE_USE_VULKAN=OFF`. G1.5A makes no
Vulkan parity claim.

## Swap packet to guest output

The exact source path is:

1. `VdSwap_entry` in `src/kernel/xboxkrnl/xboxkrnl_video.cpp` emits a Type-0
   texture fetch and `PM4_XE_SWAP`.
2. `CommandProcessor::ExecutePacketType3_XE_SWAP` validates the signature and
   calls virtual `IssueSwap`.
3. `D3D12CommandProcessor::IssueSwap` begins a submission and calls
   `D3D12TextureCache::RequestSwapTexture` using fetch constant 0.
4. It calls `Presenter::RefreshGuestOutput` with dimensions and a backend
   refresh callback.
5. `D3D12Presenter::RefreshGuestOutputImpl` allocates/reuses an
   `R10G10B10A2` UAV mailbox texture and the command processor renders the
   selected texture through gamma/post-effect work into it.
6. `IssueSwap` ends a swap submission with `EndSubmission(true)`.

`Presenter::RefreshGuestOutput` owns a three-entry producer/consumer mailbox.
It publishes the refreshed resource and requests painting; when output arrives
faster than consumption, older ready output may be replaced to keep latency
low. Consequently one `PM4_XE_SWAP` is not statically guaranteed to produce one
host Present.

## Host back buffer and Present

`D3D12Presenter::PaintAndPresentImpl` in
`src/ui/d3d12/d3d12_presenter.cpp` consumes the newest mailbox texture, computes
letterbox/output rectangles and selected guest-output effects, and renders into
the swap-chain back buffer. The D3D12 swap chain uses three
`B8G8R8A8_UNORM` flip-discard buffers. Resize waits for outstanding swap-chain
usage before releasing/recreating buffers.

After guest-output effects, the function optionally executes registered
`UIDrawer` objects into the same back buffer, transitions it to `PRESENT`,
executes the paint command list and calls DXGI Present with interval 0. When
supported/configured, variable-refresh/tearing flags are allowed. Presenter
state handles surface connect/disconnect, monitor change, resize, UI-requested
painting and submission-tracked resource lifetime.

## Frame boundaries and pacing

Three notions must remain separate:

- `PM4_XE_SWAP` / `EndSubmission(true)` is the emulated GPU swap submission;
- `Presenter::RefreshGuestOutput` publishes a mailbox image; and
- DXGI Present displays the currently consumed image after host composition.

`GraphicsSystem::SetupGuestGpu` also runs a separate guest `GPU VSync`
`XHostThread`. It uses `VdQueryVideoMode` refresh rate when `vsync=true`, or a
1 kHz interval when false, and calls `MarkVblank`. This is guest-visible vblank
timing, not DXGI's present interval. Host UI drawers force an appropriate UI
thread paint mode; otherwise the presenter may paint guest output from a
non-UI thread when configured and safe.

Static source cannot determine Fable's observed pacing, mailbox replacement,
host display scheduling or whether one title swap was actually shown.

## Bounded Xbox system-UI integration

This section is intentionally limited to the GPU/presentation join. It does not
audit XAM generally, reproduce title logic, or invoke the flows.

Fable's `src/fable2_app.h` at the accepted G1 commit subclasses `ReXApp` but
does not override the default overlay/achievement-notification factories.
Therefore the default ReXGlue host UI described below is the configured owner
if the guest reaches these handlers; this still does not prove title use.

### Keyboard/text entry

`CONFIRMED` — XAM export table ordinal `0x000002C1` names
`XamShowKeyboardUI`; `src/kernel/xam/xam_ui.cpp` exports it as
`XamShowKeyboardUI_entry`. When the runtime has an `ImGuiDrawer`, the handler
creates a `KeyboardInputDialog` host dialog. The dialog accepts host window
text/key input and the direct handler route writes its result back to the guest
buffer through the existing dialog completion path.

This dialog is not rendered through guest Xenos packets. `ReXApp::SetupOverlays`
creates an `ImGuiDrawer` and D3D12 `ImmediateDrawer`; `ImGuiDrawer::AddDialog`
registers the drawer with `Presenter` at z-order 64 and as a window input
listener. `D3D12Presenter::PaintAndPresentImpl` paints the guest output first,
then calls `ExecuteUIDrawersFromUIThread`, then transitions/presents the host
back buffer. The keyboard therefore bypasses the command processor, shader
translation, guest textures and EDRAM, joining only at host back-buffer
composition. While active, its ImGui input requests host text input on the UI
thread and continuous UI repaint.

`UNKNOWN FOR FABLE II` — static source does not prove the dog-naming flow calls
this export.

Evidence required: a pinned-TU1 title call to `XamShowKeyboardUI_entry`, its
guest output buffer/completion, and a correlated host UI draw.

Suggested later observation point: `XamShowKeyboardUI_entry`.

`G1.5D REQUIREMENT`: establish whether dog naming uses this path and ensure a
future renderer integration preserves the host-overlay composition and guest
result contract. Do not infer it from the dialog's existence.

### Achievement notification

`CONFIRMED` — the short direct source trace finds XGI app message
`0x000B0008` in `src/kernel/xam/apps/xgi_app.cpp`, logged as
`XGIUserWriteAchievements`. It reads achievement IDs and calls
`KernelState::UnlockAchievement`. `AchievementManager::UnlockAchievement` owns
the persistent unlock and notification callbacks. `ReXApp::LaunchModule`
registers a notification callback to `AchievementToastDialog::Push`, whose
thread-safe queue is drawn by `AchievementToastDialog::OnDraw`.

Like the keyboard, the toast is a host ImGui overlay, not guest Xenos work. It
joins the same `ImGuiDrawer` -> `Presenter::ExecuteUIDrawersFromUIThread` host
composition stage after guest output and before DXGI Present.

`UNKNOWN` — the bounded trace did not establish a named ReXGlue XAM export that
maps a guest Fable achievement API call to XGI message `0x000B0008`.

`UNKNOWN FOR FABLE II` — no static or existing G1 evidence proves Fable reaches
that message or a toast.

Evidence required: the guest-facing Fable achievement call, resulting XGI
message/ID, notification callback and correlated host overlay draw.

Suggested later observation point: `XgiApp::DispatchMessageSync` case
`0x000B0008`.

`G1.5D REQUIREMENT`: identify that guest-facing route and preserve achievement
toast composition in renderer integration. This is an open requirement, not a
G1.5A implementation task.

## Diagnostics, fallbacks and unsupported behavior

The active implementation exposes cvars for plugin/backend selection, vsync,
async compilation, readback, bindless descriptors, EDRAM path, shared-memory
tiling, texture budgets, post/present effects, tearing/VRR, adapter selection,
debug layers and shader diagnostics. They are implementation inputs and must be
recorded with any later runtime claim.

Important source-confirmed limitations include:

- unknown PM4 packets are logged/asserted and skipped;
- immediate indices and some primitive/shader/fetch cases are unsupported;
- coherency/invalidate paths contain incomplete TODOs;
- host render targets approximate Xenos EDRAM while ROV has performance and
  capability constraints;
- some sampler, LOD, gradient, format and MSAA behavior is approximate;
- asynchronous compilation may temporarily skip a draw;
- host queries may be disabled/faked;
- unsupported texture format use is aggregated and logged; and
- host device loss calls `GraphicsSystem::OnHostGpuLossFromAnyThread`, which
  fatally terminates because recovery is TODO.

Missing optional `dxcompiler.dll` only disables converted DXIL disassembly in
the observed log. It is not evidence of the present blocker or a failed DXBC
renderer.

No dedicated first-party GPU functional tests were found at the pinned commit.
Achievement-manager tests exist, but they do not test GPU/presenter
composition and are not counted as GPU validation.

## Fable presentation unknown

`CONFIRMED` — accepted G1 reaches `VdSwap`; existing runtime initialization
reaches the active D3D12 provider.

`UNKNOWN FOR FABLE II`

Evidence required: one correlated identity carried from
`sub_82BA34D8`/`VdSwap_entry` through `ExecutePacketType3_XE_SWAP`, `IssueSwap`,
mailbox publication/consumption, optional system-UI composition and
`D3D12Presenter::PaintAndPresentImpl` result.

Suggested later observation points: the existing symbols named above. G1.5A
adds no instrumentation and makes no claim that this end-to-end event has been
observed.
