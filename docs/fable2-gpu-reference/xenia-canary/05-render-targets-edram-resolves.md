# Xenia Canary render targets, EDRAM, and resolves

## Evidence basis

All source locators refer to
`xenia-canary/xenia-canary@3a44f20c7bc66db1da583e8a6f0ab740e31908e9`.

## Two EDRAM strategies

`src/xenia/gpu/render_target_cache.h:Path`, nested in `RenderTargetCache`,
defines two
architectural strategies:

| Path | Xenos work | Host compensation | Confidence |
|---|---|---|---|
| `kHostRenderTargets` | Shared code tracks EDRAM ranges, formats, MSAA, depth/stencil, and alias ownership. | Backend uses host color/depth targets and fixed-function output merging, transferring data when aliased ranges change owner. Some Xenos behavior is approximate. | CONFIRMED |
| `kPixelShaderInterlock` | Shared code retains the same guest state and ownership model. | Pixel shaders access an EDRAM buffer and implement output merging manually through D3D12 ROV or Vulkan fragment shader interlock. | CONFIRMED |

“More explicit” does not prove complete hardware parity. Exact accuracy remains
**UNKNOWN** for unvalidated corner cases.

## Target assembly and ownership

At draw time, `src/xenia/gpu/render_target_cache.cc:RenderTargetCache::Update`
reads:

- surface pitch and MSAA mode;
- color target bases, formats, write masks, and blend requirements;
- depth/stencil base, format, tests, writes, and stencil state;
- draw extent; and
- resolution scaling.

It normalizes attachment descriptions, detects conflicts such as incompatible
attachments at the same EDRAM base, calculates affected EDRAM ranges, and
establishes ownership. `RenderTargetCache::ChangeOwnership` transfers or
reinterprets overlapping ranges when an alias becomes active.

State leaving `Update` is a backend-ready set of attachments or an
interlock/ROV EDRAM binding plus ownership transfers and barriers.

## Backend path selection

### D3D12

`D3D12CommandProcessor::SetupContext` selects the D3D12 path.

- Explicit `rtv` requests host render targets.
- Explicit `rov` requests rasterizer ordered views if supported.
- `any` normally selects host RTV; the pinned code contains vendor/generation
  capability logic that may select ROV for pre-Arc Intel devices.
- Missing ROV support falls back to host render targets.

Concrete resources, transfers, resolves, clears, and EDRAM shaders live in
`src/xenia/gpu/d3d12/d3d12_render_target_cache.cc`.

### Vulkan

`VulkanCommandProcessor::SetupContext` selects the Vulkan path.

- `fbo` selects host framebuffer/render-pass targets.
- `fsi` requests fragment shader interlock.
- `any` selects FBO at this pin.
- FSI requires the relevant fragment interlock, stores/atomics, sample-rate
  shading, standard sample locations, and descriptor capacity. Missing
  capability falls back to FBO.

Concrete image/buffer resources, render passes, resolves, clears, transfers,
and barriers live in
`src/xenia/gpu/vulkan/vulkan_render_target_cache.cc`.

All choices above are **CONFIRMED source branches**. The branch taken on a
specific adapter is **UNKNOWN**.

## Copy-mode draws and resolve

When `RB_MODECONTROL` selects copy mode, backend `IssueDraw` redirects to
`IssueCopy` rather than issuing a normal draw.
`src/xenia/gpu/draw_util.cc:GetResolveInfo` decodes:

- source EDRAM surface, rectangle, format, and MSAA samples;
- destination base, pitch, dimensions, tiled layout, format, and endian;
- copy/resolve command and conversion;
- color or depth clear requests and values; and
- scaling/readback requirements.

The concrete backend `RenderTargetCache::Resolve` then:

1. makes the source EDRAM range current;
2. maps Xenos tile/sample coordinates;
3. applies MSAA sample selection/combination and format conversion;
4. writes the destination through host compute/copy operations;
5. performs requested EDRAM clears;
6. updates shared-memory and texture-cache validity/alias state; and
7. optionally schedules readback so guest CPU memory sees the result.

This chain is **CONFIRMED**. Individual format precision and edge cases are
**UNKNOWN** without targeted validation.

## Scaled EDRAM and resolves

Resolution scaling enlarges EDRAM-related host storage. Scaled resolves can be
kept in separate/sparse host resources. When guest-memory visibility is needed,
a compute path downsamples to the guest representation.

Primary history commit
`a635ac64f5ca37c0b789e8b4166b53dc673b213f`,
`[GPU] Scaled resolve readback through downscale CS`, confirms this
rationale. It is a host compensation for scaled rendering, not a Xenos feature.

Primary history commit
`437a7280cf95310d518a2f68087aab61403956ac`,
`[GPU] Use EDRAM layout with a single sample addressing scheme`, confirms the
a common EDRAM sample-addressing convention across rendering and resolve
paths.

## Clears, formats, depth/stencil, and blending

Host-render-target paths use host format/view mappings and host
depth/stencil/blend state when representable. Aliased or incompatible
representations require transfers/conversions.

ROV/FSI paths manually load, unpack, test, blend, and store EDRAM values in
shader code, including depth/stencil and MSAA sample addressing. Backend shader
collections in `src/xenia/gpu/shaders` support these operations.

- Implemented packing/conversion paths are **CONFIRMED**.
- A blanket claim of bit-exact behavior across every Xenos format is
  **UNKNOWN**.

## Memory and synchronization boundary

EDRAM ownership is separate from the 512 MiB shared-memory mirror. A resolve or
memory export crossing into guest memory must update `SharedMemory` validity,
fire cache watches, and obey backend resource barriers/submission completion.
`readback_resolve` and resolution-scaling choices materially alter when and
how this occurs.

No runtime capture or proprietary texture data was used for this audit.
Fable II usage is **NOT APPLICABLE** to G1.5B.
