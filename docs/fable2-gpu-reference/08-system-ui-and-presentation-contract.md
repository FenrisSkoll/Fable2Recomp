# System UI and presentation contract

## Scope and result

This contract is bounded to renderer/presenter integration. It does not audit general XAM behavior or infer title semantics from import names.

Pinned static source proves that guest output and host system UI are separate composition layers. Exact TU1 generated evidence and Run 047 additionally prove that Fable executes the keyboard import and the XGI achievement-write route. The evidence does **not** prove that the recorded keyboard event was specifically dog naming, which gameplay event caused achievement IDs 11 or 60, or that a toast was visually displayed correctly.

## Composition order

For the active D3D12 path:

1. the graphics provider supplies guest output to `Presenter::RefreshGuestOutput`;
2. `D3D12Presenter::PaintAndPresentImpl` draws that guest output into the host back buffer;
3. the presenter prepares the back buffer as a render target;
4. `Presenter::ExecuteUIDrawersFromUIThread` draws host UI from lower to higher z-order;
5. the back buffer transitions to present state and DXGI `Present` runs.

Therefore keyboard dialogs and achievement toasts do not traverse Xenos packets, guest textures, guest shader translation or EDRAM. Correct guest rendering must be available **before** UI composition. A future renderer may change styling, but must not invert this ordering or create a second swap-chain owner.

Evidence: ReXGlue `src/ui/presenter.cpp:Presenter::RefreshGuestOutput`, `Presenter::ExecuteUIDrawersFromUIThread`, and `src/ui/d3d12/d3d12_presenter.cpp:D3D12Presenter::PaintAndPresentImpl`.

## Fable keyboard route

### Confirmed TU1 static reachability

The exact current generated output contains:

- `generated/default/fable2_funcs.15.h`: `DECLARE_REX_FUNC(__imp__XamShowKeyboardUI)`;
- `generated/default/fable2_init.cpp`: import address `0x832B9AC4`;
- `generated/default/fable2_register.cpp`: registration of `0x832B9AC4 -> __imp__XamShowKeyboardUI`;
- `generated/default/fable2_recomp.15.cpp`: `sub_82CC2E90` is a direct thunk to the import;
- `generated/default/fable2_recomp.8.cpp`: a direct title call at guest address `0x826CDF60`, with LR `0x826CDF64`, to `sub_82CC2E90`.

This proves TU1 static reachability to the keyboard import. It does not assign a Lionhead semantic name to the caller.

Pinned ReXGlue exports `__imp__XamShowKeyboardUI` to `XamShowKeyboardUI_entry`. In non-headless mode it creates a `KeyboardInputDialog` through `xeXamDispatchDialogEx`, converts guest strings for presentation, and completes the guest overlapped request on confirm or cancellation. A headless fallback copies the default text or clears the result buffer and also completes asynchronously.

### Confirmed existing runtime execution

`fable2-run-047.1.log:42673` records:

`XamShowKeyboardUI(00000000, 20000004, 422E5352, 409BCC90, 42D6F3B0, 422E5352, 00000011, 422E537C)`

This confirms that Fable reached the import in existing runtime evidence. It does not, by itself, prove dog-naming semantics, correct focus behavior, correct entered text, cancellation, resize, or shutdown handling.

## Fable achievement route

### Confirmed TU1 static reachability

`sub_82CC27F8` in `generated/default/fable2_recomp.123.cpp` constructs an `XMsgStartIORequest` call with:

- app `0xFB`;
- message `0x000B0008`;
- buffer length `8`;
- the guest request buffer in r6 and overlapped state in r5.

Confirmed direct TU1 callers include call instructions at `0x8233ED04` (LR `0x8233ED08`) and `0x822EAAA4` (LR `0x822EAAA8`).

Pinned ReXGlue routes `XMsgStartIORequest_entry` through `AppManager` to `XgiApp`, whose app ID is `0xFB`. `XgiApp::DispatchMessageSync` handles message `0x000B0008`, validates the bounded count/range, reads the ID at entry offset 4 with stride 8, and calls `KernelState::UnlockAchievement`. The kernel requests `AchievementNotification::kShow`; `AchievementManager` owns persistence/notification and ReXApp registers a callback to its achievement notification dialog.

### Confirmed existing runtime execution

`fable2-run-047.log` records:

- lines 9–11: message `0x000B0008`, achievement ID `11`, and `Achievement unlocked: 0000000B`;
- lines 18587–18589: message `0x000B0008`, achievement ID `60`, and `Achievement unlocked: 0000003C`.

This proves the Fable guest-facing route and unlock call executed. It does not prove which title events earned them, persistence after a fresh restart beyond the existing store logs, toast timing/z-order, duplicate suppression, or shutdown behavior.

## Fable-specific overrides

`src/fable2_app.h` contains only commented customization examples for `CreateAchievementsOverlay` and `CreateAchievementNotificationDialog`. No active Fable override of ReXGlue overlay, keyboard or achievement factories exists. Current behavior uses the ReXGlue defaults.

## Minimum compatibility contract

| Contract item | Required behavior | Current evidence | Remaining validation |
|---|---|---|---|
| Guest output first | One authoritative guest-output producer is composed before host UI. | CONFIRMED SOURCE; Run 047 shows both guest output and UI. | Correlate mailbox generation only if presentation work needs it. |
| Host UIDrawers afterwards | Execute from lower to higher z-order, at most once per UI draw generation, before Present. | CONFIRMED SOURCE. | Runtime z-order not separately observed for Fable. |
| Keyboard focus | Dialog owns appropriate input focus while open and releases it on close. | Source-connected UI design. | Natural user checkpoint; never log text/keys. |
| Async guest result | Confirm/cancel/headless paths complete the guest overlapped result exactly once with correct result/extended error. | CONFIRMED SOURCE; Fable execution confirmed. | Confirm and cancellation outcomes not both validated. |
| Achievement persistence/event | A valid guest write unlocks once, persists, and emits the notification event. | Static route and two Run 047 unlocks confirmed. | Fresh-restart persistence and duplicate handling are not controlled. |
| Toast queue | Notification callback queues and displays bounded host UI without blocking guest GPU work. | CONFIRMED SOURCE. | Fable toast visual/timing behavior not observed as a controlled checkpoint. |
| Thread/UI ownership | UIDrawer add/remove/draw and UI composition stay on the UI thread; graphics provider/mailbox synchronization stays with ReXGlue. | CONFIRMED SOURCE. | Any future producer interface remains unproved. |
| Z-order/repaint | Drawer changes preserve ordered iteration; UI requests repaint without creating a second present owner. | CONFIRMED SOURCE. | Runtime correlation only if a defect appears. |
| Resize/safe area | Guest output aspect/letterbox/safe-area transform and UI dimensions follow current presenter size. | CONFIRMED SOURCE. | Keyboard/toast behavior across resize not validated. |
| Shutdown/cancellation | Pending dialogs, callbacks, notification listeners, GPU output and presenter resources cancel/unregister/retire once in order. | Partial source evidence. | Natural shutdown during open dialog/toast remains untested. |

## Compatibility versus styling

Compatibility behavior includes ordering, focus, async completion, persistence/events, z-order, repaint, resize/safe-area and shutdown. These requirements survive any renderer or presenter replacement.

A Fable-styled keyboard or achievement popup is a replaceable frontend possibility only. It cannot change guest results, timing/ownership contracts, unlock persistence, or the “guest output then host UI” order, and it is not authorized by G1.5D.

## Exact open questions and later gates

- Was Run 047's keyboard call the dog-naming flow? Static evidence cannot establish that title semantic quickly; observe only at a later natural checkpoint, `EXP-KEYBOARD-UI-001`.
- Do confirm and cancel each complete exactly once with correct focus and resize/shutdown behavior? `EXP-KEYBOARD-UI-001`.
- Which natural title events correspond to IDs 11 and 60, and did the toast render correctly? The IDs' gameplay meaning is outside this bounded audit. A future user must name a natural not-yet-unlocked checkpoint before `EXP-ACHIEVEMENT-UI-001`.
- Can a future renderer feed the existing guest-output mailbox without taking presenter/UI ownership? The pinned corpus provides no proved producer interface; see `OQ-OWNERSHIP-INTERFACE`.

No wider XAM or Lionhead title-logic audit was performed.
