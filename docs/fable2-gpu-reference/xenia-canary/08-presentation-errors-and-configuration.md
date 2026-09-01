# Xenia Canary presentation, errors, and configuration

## Evidence basis

All source locators refer to
`xenia-canary/xenia-canary@3a44f20c7bc66db1da583e8a6f0ab740e31908e9`.

## End-to-end swap chain

The concrete source chain is:

```text
xboxkrnl_video.cc:VdSwap_entry
  -> PM4_XE_SWAP
  -> COMMAND_PROCESSOR::ExecutePacketType3_XE_SWAP
  -> D3D12CommandProcessor::IssueSwap
     or VulkanCommandProcessor::IssueSwap
  -> backend TextureCache::RequestSwapTexture
  -> backend guest-output gamma/post-processing
  -> Presenter::RefreshGuestOutput
  -> Presenter::PaintAndPresent
  -> D3D12Presenter::PaintAndPresentImpl
     or VulkanPresenter::PaintAndPresentImpl
```

Every arrow is **CONFIRMED** from the pinned source.

`IssueSwap` begins/continues a backend submission, requests the current
front-buffer texture (including resolution-scaled representation where
applicable), transforms it into presenter-owned guest output, publishes it, and
ends the submission with swap significance. It does this even if a window/UI
condition means no immediate host present.

## Presenter ownership and threading

`src/xenia/ui/presenter.cc:Presenter::RefreshGuestOutput` publishes into a
three-entry guest-output mailbox. When a newer completed image supersedes a
queued one, the older queued image may be dropped to reduce latency.

`Presenter::PaintAndPresent` composes guest output with UI drawing. It may
record/present from the GPU thread when the backend and UI state permit, or
request work on the UI thread.

The mailbox is a host presentation mechanism, not a guest ring. Guest vblank
and frame limiting are maintained by the graphics system and are separate from
host swapchain presentation.

## D3D12 presentation

`src/xenia/ui/d3d12/d3d12_presenter.cc` owns a three-buffer flip-discard
swapchain. `D3D12Presenter::PaintAndPresentImpl`:

- acquires the current back buffer;
- records transitions, guest-output sampling, and UI composition;
- submits to the direct queue with fence tracking;
- calls `Present(0, flags)`, using tearing flags when configured/supported;
  and
- handles resize/reconnection of swapchain resources.

Device removal/loss is reported through the graphics system and is fatal.
Static source cannot establish a window's tearing support or present latency.

## Vulkan presentation

`src/xenia/ui/vulkan/vulkan_presenter.cc` creates a surface swapchain and
selects an available present mode in this preference family:

1. immediate when requested/available;
2. mailbox;
3. FIFO relaxed;
4. FIFO.

`VulkanPresenter::PaintAndPresentImpl` acquires an image, records layout
transitions and composition, submits with acquire/render-complete semaphores,
and calls `vkQueuePresentKHR`. Out-of-date or suboptimal surface results
trigger swapchain reconnection/recreation. The source also contains a
configuration-controlled semaphore workaround for affected host behavior.

Mode availability and actual selection are **UNKNOWN** without a concrete
surface/device.

## Gamma, scaling, and capture

The swap refresh path applies the guest gamma/post-processing representation
before publishing presenter output. Primary history commit
`d119505289d540f61ae3d4ba6168f1145625277a`,
`[GPU] Texture integer scaling fetches; 8_8_8_8_GAMMA resolve`, confirms the
fixed-format scale and piecewise-linear gamma design.

Backend presenters implement `CaptureGuestOutput`-related readback used by
architecturally relevant screenshot/capture services. This audit inspected the
path but created no capture. Capture does not define a frame boundary.

## Configuration classification

| Branch | Class | Material behavior | Confidence |
|---|---|---|---|
| `gpu` | architecture | selects null, D3D12, Vulkan, or ordered auto selection | CONFIRMED |
| `render_target_path_d3d12` | accuracy/capability | host RTV versus ROV EDRAM path | CONFIRMED |
| `render_target_path_vulkan` | accuracy/capability | framebuffer versus fragment-interlock EDRAM path | CONFIRMED |
| `occlusion_query` | accuracy/performance | fake/fast/alternative/strict report behavior | CONFIRMED |
| `readback_resolve` | accuracy/performance | `none`, `fast`, or `full` guest-memory visibility of resolves | CONFIRMED |
| `readback_memexport` | accuracy/performance | guest-memory visibility of memory exports | CONFIRMED |
| `async_shader_compilation` and thread counts | scheduling/performance | inline versus queued pipeline creation | CONFIRMED |
| `d3d12_bindless` | capability/performance | root signature and descriptor architecture | CONFIRMED |
| sparse/tiled shared memory cvars | capability/resource | sparse versus fully allocated mirror | CONFIRMED |
| texture memory budgets | resource/performance | cache eviction pressure | CONFIRMED |
| resolution scale | enhancement/resource | scaled render targets, EDRAM, textures, and resolves | CONFIRMED |
| invalid fetch/upload allowances | validation/compatibility | reject versus continue after invalid state | CONFIRMED |
| vsync/frame limit | pacing | wait and limiter behavior | CONFIRMED |
| tearing/present-mode options | host presentation | host swapchain scheduling | CONFIRMED |
| shader/register/command dumps | diagnostics | logs or derived dumps; no intended guest-semantic change | CONFIRMED |

Capability fallback is part of the implementation. It is not an assertion that
fallback paths have identical precision or performance.

## Errors, assertions, and unsupported behavior

**CONFIRMED source cases include:**

- malformed packet sizes/opcodes, invalid registers, invalid shader/fetch
  state, and unsupported immediate indices produce assertions, warnings, or
  failure returns according to the call site;
- shader translation or host pipeline creation failure can skip/fail a draw;
- invalid fetch constants may be permitted by configuration;
- `INVALIDATE_STATE` is parsed but its cache action is TODO;
- `MakeCoherent` does not yet notify resource caches;
- `VIZ_QUERY` and some event extent behavior are synthetic;
- capability checks select fallback render-target/resource paths;
- host device loss is fatal and recreation is TODO; and
- backend shutdown waits for queue-owned work/resources before destruction.

These outcomes must be read individually. An assertion documents a presumed
invariant; a warning documents detection; neither alone proves hardware
behavior.

## Historical rationale boundary

The following rationale is **CONFIRMED** from commits available in the verified
clone:

- `fbd620c22b44638b66a70bba80d6f30d55a10924` — ZPD query lifecycle and modes;
- `9781a75a22ba789124d7f34c6bdb4a85c78b2532` — stale texture prevention;
- `d119505289d540f61ae3d4ba6168f1145625277a` — integer scale and PWL gamma;
- `a635ac64f5ca37c0b789e8b4166b53dc673b213f` — scaled resolve downsampling;
- `aed81ca93a1f3e8dd043107babd33438379f379d` — memory invalidation;
- `437a7280cf95310d518a2f68087aab61403956ac` — unified EDRAM layout;
- `3eab2b8b39442e32537610c955fbb8db0c2a6561` — tessellated topology conversion;
- `3a44f20c7bc66db1da583e8a6f0ab740e31908e9` — scalar approximation rounding.

The clone is shallow at
`049a55f03679b204379b17996bd032ce54bff156`. Older ancestry and unlinked
primary PR/issue rationale are **UNKNOWN**. No secondary claim was promoted to
confirmed rationale.

## Static unknowns

- selected adapter, backend, surface mode, capabilities, and effective cvars;
- real packet/state use by any title;
- device-specific shader compilation, synchronization, pacing, and loss;
- exact Xenos parity of approximation, precision, query, EDRAM, and resolve
  edge cases.

Fable II relevance assessment and divergence analysis are **NOT APPLICABLE** to
G1.5B.
