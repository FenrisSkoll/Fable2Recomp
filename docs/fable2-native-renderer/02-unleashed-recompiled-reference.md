# Unleashed Recompiled renderer reference

## Pinned precedent and licence boundary

This analysis uses UnleashedRecomp commit
`cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c` dated
`2026-06-29T14:05:43+03:00`. Its implementation is GPL-3.0. It is evidence that
a statically recompiled Xbox 360 title can replace high-level guest rendering
functions; G1 copied no implementation. Separately pinned XenosRecomp and Plume
are MIT-licensed and may be evaluated as components without inheriting the
UnleashedRecomp implementation's GPL terms.

The primary inspected sources were
[`gpu/video.cpp`](https://github.com/hedge-dev/UnleashedRecomp/blob/cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c/UnleashedRecomp/gpu/video.cpp),
[`gpu/video.h`](https://github.com/hedge-dev/UnleashedRecomp/blob/cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c/UnleashedRecomp/gpu/video.h), and
[`kernel/function.h`](https://github.com/hedge-dev/UnleashedRecomp/blob/cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c/UnleashedRecomp/kernel/function.h).

## How Unleashed hooks rendering

`GUEST_FUNCTION_HOOK(subroutine, function)` defines the generated guest
function symbol as a host adapter using `HostToGuestFunction`. The hook body
replaces the guest implementation at link time; it is not an inline detour and
does not call the original function. The renderer uses title-specific addresses
for Xbox D3D-style methods, including:

| Operation group | Sonic Unleashed guest addresses at the pinned revision |
|---|---|
| Device/resource lifetime | CreateDevice `0x82BD99B0`; DestructResource `0x82BE6230`; CreateTexture `0x82BE9498`; CreateVertexBuffer `0x82BE6AD0`; CreateIndexBuffer `0x82BE6BF8`; CreateSurface `0x82BE95B8` |
| Locks | Texture Lock/Unlock `0x82BE9300` / `0x82BE7780`; vertex buffer `0x82BE6B98` / `0x82BE6BE8`; index buffer `0x82BE6CA8` / `0x82BE6CF0` |
| Targets/state | SetRenderTarget `0x82BDD9F0`; SetDepthStencilSurface `0x82BDDD38`; SetViewport `0x82BDD8C0`; SetTexture `0x82BE9818`; SetScissorRect `0x82BDCFB0` |
| Clear/draw | Clear `0x82BFE4C8`; DrawPrimitive `0x82BE5900`; DrawIndexedPrimitive `0x82BE5CF0`; DrawPrimitiveUP `0x82BE52F8` |
| Input/shaders | Create/SetVertexDeclaration `0x82BE0428` / `0x82BE02E0`; Create/SetVertexShader `0x82BE1A80` / `0x82BE0110`; SetStreamSource `0x82BDD0F8`; SetIndices `0x82BDD218`; Create/SetPixelShader `0x82BE1990` / `0x82BDFE58` |
| Copy/present | StretchRect `0x82BF6400`; Present `0x82BDA8C0` |

These are **not** Fable II addresses. They prove the architectural pattern and
the expected operation families only. Address transfer between titles would be
incorrect.

## Guest objects and render-command queue

Unleashed models guest-facing device/resources while attaching native state:

- `GuestDevice` has a title-specific fixed size of `0x5E00`, function/state
  tables, sampler state, shader constants, and other layout assumptions.
- Guest textures, buffers, surfaces, shaders, and vertex declarations carry
  enough metadata to map guest identity and lifetime to host objects.
- Lock/unlock hooks capture uploads and perform format/endian conversion at
  the point where resource intent is still explicit.
- The device hooks enqueue a `RenderCommand` rather than immediately issuing
  every host command. Command variants cover target/depth binding, clear,
  viewport/scissor, textures/samplers, constants, draws, declarations,
  shaders, streams/indices, and resource updates.
- Dirty-state tracking translates the Xbox-style state machine into host
  pipeline/resource bindings before a draw.

This validates the shape proposed for Fable's normalized IR, but the concrete
guest layouts and function contracts are Sonic-specific. Fable's observed
device-like allocation is `0x5E80`, already proving that Unleashed's
`GuestDevice` layout cannot be adopted unchanged.

## Shaders, formats, resolves, and presentation

Unleashed preconverts a known shader corpus using XenosRecomp. Runtime hooks
hash guest shader microcode with XXH3-64 and look up embedded converted shaders
and reflection. The renderer converts vertex declarations/fetch information,
texture and buffer formats, byte order, and resource uploads. It implements
title-specific resource copies/resolves and finally presents through the native
backend.

This strategy depends on a finite, discoverable shader set and on hashes that
are stable for the exact game revision. A Fable implementation would need its
own TU1 shader inventory, collision-safe identity (hash plus size/stage and
preferably a second digest), reflection checks, dynamic-shader policy, and
format/endian validation. No Fable shader payload or hash corpus was collected
or committed in G1.

## Plume's role

At Plume commit `d890ac899e505fb30040e037a4037cdeca68f033`, Plume is a native render
abstraction over devices, queues, command lists, buffers/textures, views,
pipelines, samplers, queries, and swapchains, with D3D12/Vulkan/Metal backend
work. It is not an Xbox D3D or Xenos semantic translator. Unleashed supplies
the guest object model, state translation, shader selection, endian/format
logic, and game-specific workarounds above Plume.

Consequently, adopting Plume would answer only the native-backend abstraction
question. It would not locate Fable hooks or make Fable shaders/resources
correct automatically.

## XenosRecomp support audit

XenosRecomp commit `990d03b28a27b50277ee5d8d942e1c5f873869d1`
explicitly states that it was built for Sonic Unleashed and should not be
expected to work out of the box for other games. Its documented gaps and
title-specific assumptions include:

- incomplete handling of dynamic constant operands and special floating-point
  values;
- no dynamic register indexing and little testing of complex control flow;
- conversion failure when required reflection cannot be derived;
- missing integer constants and only 16 boolean constants despite a possible
  128;
- Sonic-specific vertex endian swizzle and some vertex semantic/type choices;
- game-specific instancing and hard-coded Vulkan vertex-input locations;
- missing mini vertex fetch/binding support and 1D texture support;
- incomplete LOD/filter behaviour and unsupported sampler cases;
- cube-texture optimization assumptions;
- missing memory export and point-size behaviour;
- shader container reverse engineering sufficient for its original title, not
  a general compatibility guarantee.

Each item is a Fable qualification test, not merely a future enhancement. TU1
may use a documented omission even if Sonic does not. XenosRecomp is therefore
a promising conversion starting point only after a Fable shader-feature census
and validation against ReXGPU/Xenia output.

## Reusable architecture versus title-specific behaviour

| Reusable concept | Must be rebuilt/validated for Fable II |
|---|---|
| Static guest-function interception | exact TU1 addresses, boundaries, ABI, caller population, forwarding-safe detour mechanism |
| Guest-to-host resource identity | Fable device/resource layouts, allocation paths, aliasing, lock rules, lifetime and reference counts |
| Versioned render-command queue | Fable threading, pass/frame boundaries, ordering, resolve/present semantics |
| Native backend abstraction | required D3D12 features, resource/state model, eventual Vulkan parity |
| Offline shader conversion/cache | Fable shader corpus, hashes, Xenos feature coverage, reflection, dynamic creation and legal/private-data policy |
| State-to-pipeline translation | Fable state usage, vertex formats, texture formats, endian conversion, EDRAM resolves, predication and synchronization |

The accurate precedent is therefore: high-level hooks can work when their exact
title ABI and content assumptions are reconstructed. It is not evidence that
Fable can reuse Sonic addresses, object layouts, converted shaders, state
tables, or workarounds.
