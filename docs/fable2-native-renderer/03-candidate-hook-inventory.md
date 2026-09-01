# Candidate hook inventory

## Scope and counts

This inventory applies only to the exact TU1 identity in
[`00-workstream-scope.md`](00-workstream-scope.md). It records 11 bounded
functions: 5 confirmed, 4 strong hypotheses, and 2 weak hypotheses. The counts
describe confidence in each recorded role, not readiness to replace the
function. The deterministic companion is
[`candidate-hook-inventory.json`](candidate-hook-inventory.json).

No candidate was added merely because an expected D3D operation should exist.
The absent resource/state/shader/draw addresses remain `UNKNOWN`.

## Boundary method

Generated ReXGlue output was searched for exact direct imports and calls.
Boundaries were counted from the generated PPC instruction comments and checked
against the next contiguous function where available. Exact-image Ghidra
`.pdata`, call/data xrefs, and TU1 string references were used as corroboration.
`.pdata` prologue ranges were not used as complete body sizes. No generated
source or manifest was edited.

## Confirmed functions

All facts in this table are **CONFIRMED**. Descriptive roles are deliberately
limited to what the named `Vd*` calls prove.

| TU1 range / function | Provenance and callers | Arguments/layout and distinction | Forwarding and risks |
|---|---|---|---|
| `[0x82BA2830,0x82BA2CA0)`, size `0x470`, `sub_82BA2830` | 284 PPC instructions; Ghidra `.pdata` `0x82137788`; direct callers `0x821C3858`, `0x82B6EBC0`, `0x82B6F4C0`, `0x82BA6990`, `0x82BA6C18` | Device-object operation that allocates/configures physical ring buffers, read-pointer writeback, and GPU identifier storage. Direct calls to `VdInitializeRingBuffer`, `VdEnableRingBufferRPtrWriteBack`, and `VdSetSystemCommandBufferGpuIdentifierAddress` distinguish raw transport setup from a semantic rendering method. | Forwarding is possible but mandatory. Capturing here is useful for ring correlation only; bypassing it would change allocations, MMIO-visible addresses, ownership, and writeback. |
| `[0x82BA34D8,0x82BA3BFC)`, size `0x724`, `sub_82BA34D8` | 457 PPC instructions; Ghidra `.pdata` `0x821377C0`; Ghidra call xref `0x82B6FB00`; direct callers `0x82B6EA60`, `0x82B6F1D0`, `0x82B6FA48`, `0x82BA5D08` | Callers use `r3` as a device-like object, `r4` as a front-buffer/surface-like object, and `r5` as flags. Direct calls to `VdGetSystemCommandBuffer` and `VdSwap` prove a swap/present command emitter, not a thunk. | **Strongest confirmed shadow hook.** Forward to the original body. Preserve command writes, front-buffer metadata, pacing, callbacks, synchronization, errors, and return value. |
| `[0x82BA6968,0x82BA6990)`, size `0x28`, `sub_82BA6968` | 10 PPC instructions; Ghidra `.pdata` `0x821378C0`; no generated direct caller identified | Direct `VdShutdownEngines` call proves a compact shutdown helper. Invocation may be indirect or through a function table. | Forward exactly once. Hook installation must not turn indirect shutdown into duplicate teardown. Useful for lifecycle capture, not rendering IR. |
| `[0x82BA6990,0x82BA6C18)`, size `0x288`, `sub_82BA6990` | 162 PPC instructions; Ghidra `.pdata` `0x821378C8`; Ghidra call xref `0x82B6F928`; direct caller `0x82B6F6C0` | Receives the device-like allocation and `0x7C` initialization block, initializes critical sections at object offsets `0x3A60` and `0x3A7C`, calls `VdInitializeEngines`/`VdSetGraphicsInterruptCallback`, then `sub_82BA2830`. This proves GPU/device lifecycle initialization; the public XDK name is unknown. | Forwarding is required. Record only validated scalar/metadata fields until the rest of the `0x5E80` object layout is established. Preserve partial-failure cleanup and interrupt ordering. |
| `[0x82BA6C18,0x82BA6EB8)`, size `0x2A0`, `sub_82BA6C18` | 168 PPC instructions; Ghidra `.pdata` `0x821378D0`; direct callers `0x82A4DB78`, `0x82A8A840`, `0x82B6F9D0`, `0x82BA2218` | Device cleanup path that removes the graphics callback and reaches `VdShutdownEngines`. Its size and cleanup work distinguish it from the compact helper/thunk. | Forward after recording lifecycle intent. Ordering against in-flight GPU work, callback removal, ring teardown, allocations, and references is renderer-critical. |

## Strong hypotheses

These ranges and call relationships are confirmed; the semantic names in this
section are **STRONG HYPOTHESES**.

| TU1 range / function | Evidence and callers | Wrapper/thunk distinction, arguments, forwarding risk |
|---|---|---|
| `[0x82AAC208,0x82AAC54C)`, size `0x344`, `sub_82AAC208` | 209 PPC instructions; Ghidra `.pdata` `0x82133E70`; data ref `0x82AAA2E8`; TU1 label reference at `0x82AAC254` identifies `ProcessAsyncCommandQueues` timing; no direct caller recognized | Likely Lionhead async render-command queue processing, but G1 did not establish a public queue/command layout or whether this is enqueue versus consume. It is not a thunk. Hooking may recurse into graphics functions, alter queue ownership/order, or disturb synchronization. Treat as an engine-boundary discovery lead, not a G2 hook prerequisite. |
| `[0x82B6EA60,0x82B6EBC0)`, size `0x160`, `sub_82B6EA60` | 88 PPC instructions; direct caller `0x82A1AC98`; calls `sub_82B6F6C0` and later reaches presentation | Likely title-level graphics creation orchestration. It remains distinct from the Xbox initializer because it prepares title/global state. Forwarding can capture lifecycle arguments, but global publication, first-present behaviour, error cleanup, and return ABI must remain exact. |
| `[0x82B6F6C0,0x82B6F9CC)`, size `0x30C`, `sub_82B6F6C0` | 195 PPC instructions; Ghidra `.pdata` `0x82136A80`; direct caller `0x82B6EA60`; allocates `0x5E80`, forwards it and a `0x7C` block to `sub_82BA6990` | Likely device allocation/create bridge rather than a thunk. The `0x5E80` object and `0x7C` input block are observed layouts, not named public structures. Forwarding must retain allocation identity, tables, constructor order, references, and failure paths. |
| `[0x82B6FA48,0x82B6FBE0)`, size `0x198`, `sub_82B6FA48` | 102 PPC instructions; Ghidra `.pdata` `0x82136A90`; direct caller `0x82A1B560`; calls `sub_82BA34D8` | Likely title frame/present coordinator. It loads the global device, manages related object references, and supplies the device plus front-buffer/surface-like object to the confirmed emitter. It is above raw command construction, but is not proven to be the only engine frame boundary. Preserve references, pacing, callbacks, errors, and re-entrancy when forwarding. |

## Weak hypotheses

These functions prove named engine renderer concepts exist, but do not prove a
render-operation ABI. They must not be hooked in G2 without more evidence.

| TU1 range / function | Exact evidence | Why confidence is weak / risk |
|---|---|---|
| `[0x8328D6F8,0x8328D744)`, size `0x4C`, `sub_8328D6F8` | 19 PPC instructions; Ghidra `.pdata` `0x82162C00`; exact label reference `0x8328D70C` to `Outline Renderer`; data ref `0x832D5504`; no direct caller recognized | Likely registration/construction. No renderer object layout, draw call, or command structure is known. Hooking it could corrupt startup/type registration while capturing no frame operations. |
| `[0x83290138,0x83290184)`, size `0x4C`, `sub_83290138` | 19 PPC instructions; Ghidra `.pdata` `0x82162EE8`; exact label reference `0x8329014C` to `LightingManager Renderer`; data ref `0x832D57C4`; no direct caller recognized | Likely registration/construction. The label is not evidence of a draw or enqueue method. Same registration and startup risk as above. |

Additional title metadata supports a real Lionhead renderer subsystem without
yet yielding hookable functions: labels include `Lighting Buffer Effect
Renderer`, `GUI Renderer`, `Nested Scene Renderer`, a `DestroyCommandBuffer`
diagnostic, `D3DRS_CULLMODE`, `PixelShader`, `VertexShader`, and texture-renderer
diagnostics. These labels are discovery seeds only. Private image bytes and
payloads are not part of this repository.

## Required operation coverage

| Operation family | G1 result | Evidence-backed next step |
|---|---|---|
| Device creation/destruction | initialization/shutdown confirmed; title create wrappers strong | Capture call order and validate the `0x5E80` device plus `0x7C` input block. Do not assign a public API name yet. |
| Resource/surface creation | **UNKNOWN** | Work outward from confirmed device/function tables and correlate allocations with raw resource packets. |
| Texture/VB/IB lock/unlock | **UNKNOWN** | Identify guest resource classes, lock flag patterns, and upload/endian effects before naming. |
| Render target/depth surface | **UNKNOWN** | Correlate high-level candidate calls with EDRAM target-register transitions. |
| Vertex declarations/streams | **UNKNOWN** | Correlate device virtual calls with vertex-fetch register writes and exact guest arguments. |
| Shader create/bind/constants | **UNKNOWN** | Start from `PixelShader`/`VertexShader` diagnostics and shader-load packets; retain stage/hash/size evidence. |
| Texture/sampler state | **UNKNOWN** | Correlate texture-fetch and sampler register groups with device methods. |
| Render/blend/depth/rasterizer/viewport/scissor | **UNKNOWN** | Use register-delta correlation; do not equate one register packet with one API call. |
| Clear | **UNKNOWN** | Correlate a controlled manual frame with EDRAM/color/depth operations. |
| Primitive/indexed draws | **UNKNOWN** | Correlate PM4 draw packet sequence with indirect device calls; prove primitive/count/index arguments. |
| Resolves/copies | semantic method **UNKNOWN**; raw `IssueCopy` known | Trace backward from PM4 copy/resolve into static Xbox methods. |
| Queries/predication/synchronization | semantic method **UNKNOWN**; raw PM4 handlers known | Correlate wait/query packets and callbacks without changing scheduling. |
| Swap/present | **CONFIRMED** at `0x82BA34D8`; title coordinator strong at `0x82B6FA48` | First shadow-capture proof target. |

## Hookability verdict

Generated functions are link-time symbols, so a wrapper can call a separately
named original body if code generation/runtime wiring deliberately preserves
it. This is feasible but is not the same mechanism as UnleashedRecomp's
replacement-only macro. A forwarding design must avoid symbol recursion and
must leave dispatcher registrations and guest function pointers coherent.

Only `0x82BA34D8` is both semantically useful and confirmed enough for the first
shadow proof. Lifecycle candidates may be captured alongside it. No draw,
resource, shader, or state function is approved for hook implementation by G1.
