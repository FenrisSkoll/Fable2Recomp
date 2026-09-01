# Render targets, EDRAM and resolves

All locators refer to ReXGlue commit
`956c6a8b5da4c54b9899a2593e9c67c26de30194`.

## Two host models of Xenos EDRAM

Common `RenderTargetCache` is declared in
`include/rex/graphics/pipeline/render_target/cache.h` and implemented in
`src/graphics/pipeline/render_target/cache.cpp`. It models Xenos render-target
and depth/stencil state in EDRAM tiles, including aliasing when different guest
attachments occupy the same tiles.

The D3D12 implementation supports two paths:

| Path | Source type | Host representation | Baseline characteristic |
|---|---|---|---|
| `Path::kHostRenderTargets` | `D3D12RenderTargetCache` | ordinary D3D12 color/depth resources plus ownership transfers | faster, approximate fixed-function mapping |
| `Path::kPixelShaderInterlock` | `D3D12RenderTargetCache` + shader OM translation | scaled raw EDRAM buffer with rasterizer-ordered-view access | custom Xenos output merger, generally slower |

`D3D12RenderTargetCache::Initialize` in
`src/graphics/d3d12/render_target_cache.cpp` reads
`render_target_path_d3d12`: `rtv` forces host targets and `rov` requests pixel
shader interlock. With an empty value, the pinned policy selects ROV on Intel
and host render targets elsewhere; a requested/selected ROV path falls back to
host targets if rasterizer-ordered views are unsupported. Thus the existing
NVIDIA initialization makes host targets the source-default, but the actual
Fable run's cvar value was not captured by G1.5A.

## Draw-time target update and aliasing

`D3D12CommandProcessor::IssueDraw` obtains normalized depth/color state and
calls `D3D12RenderTargetCache::Update`, which delegates common decisions to
`RenderTargetCache::Update`.

Inputs include `RB_SURFACE_INFO`, color/depth target registers, EDRAM mode,
MSAA, normalized write masks, depth control, draw extents and shader export
information. Common update code determines:

- whether rasterization can modify color or depth;
- the used EDRAM pitch, tile ranges and attachment formats;
- attachment height/extents and draw-resolution scale;
- current tile ownership and overlap with existing targets; and
- whether ownership transfer/resolve/clear work is required.

`GetOrCreateRenderTarget` owns cached host attachments.
`WouldOwnershipChangeRequireTransfers` and `ChangeOwnership` maintain tile
aliasing. On the host-render-target path,
`D3D12RenderTargetCache::PerformTransfersAndResolveClears` moves/reinterprets
data between host resources and the EDRAM buffer as ownership changes, then
`SetCommandListRenderTargets` binds D3D12 RTVs/DSVs. On the interlock path,
pixel shaders access the EDRAM UAV and the cache enforces full EDRAM/UAV
barriers where required.

Persistent state includes the EDRAM buffer, tile ownership map, host target
objects, their submission use, transfer/clear pipelines, descriptor state and
the last-update bound formats used in PSO keys.

## Formats, depth/stencil and MSAA

Format helpers choose storage, draw, transfer, SRV/DSV and resolve
representations separately. This permits reinterpretation and gamma/fixed-point
handling when a single DXGI format cannot express all Xenos behavior.
`IsHostDepthEncodingDifferent` and related shader modification state handle
depth representations such as Xenos float24.

MSAA affects tile extents, sample addressing, host resource sample count and
resolve shader choice. Source contains native and emulated paths for 1x/2x/4x
cases and generated resolve/load shaders for scaled variants. It also contains
explicit fallback TODOs, including some unsupported host sample-count
combinations; G1.5A does not generalize this to perfect Xenos MSAA parity.

## Copy, resolve and clear

When `RB_MODECONTROL.edram_mode` is `kCopy`,
`D3D12CommandProcessor::IssueDraw` calls `IssueCopy` rather than emitting a
normal draw. `draw_util::GetResolveInfo` in `src/graphics/util/draw.cpp` derives
a `ResolveInfo` from current registers, guest resolve vertices, formats,
coordinates, sample selection and destination layout.

`D3D12RenderTargetCache::Resolve` then:

1. validates source/destination and EDRAM tile spans;
2. attempts a constrained direct host resolve where legal;
3. otherwise selects generated compute resolve/copy pipelines;
4. performs format/sample/endian conversion into shared or scaled-resolve
   memory;
5. applies requested color/depth clears; and
6. marks destination ranges resolved and GPU-written so texture/shared-memory
   watches invalidate consumers.

`IssueCopy_ReadbackResolvePath` is a configuration-dependent alternate path for
guest CPU visibility. Default common `readback_resolve` is `none`, and D3D12's
legacy `d3d12_readback_resolve` switch is false. The exact selected behavior
must be established from the run configuration and operation.

## Synchronization and lifetime

The EDRAM buffer and host targets participate in D3D12 transition, UAV and
aliasing barriers submitted by the command processor. Cached targets are
retired only after relevant submission completion. `BeginSubmission`,
`CompletedSubmissionUpdated`, `BeginFrame`, `ClearCache` and `Shutdown` connect
the cache to command-list/fence lifetime.

Failures to allocate resources, build pipelines, derive a supported resolve or
request destination memory return failure/log an exact error. Source also logs
unsupported resolve commands and vertex-buffer formats rather than fabricating
an unverified copy.

## Fable connection and unknowns

`UNKNOWN FOR FABLE II`

Evidence required: the draw/copy trigger; complete RB/COPY register snapshot;
selected `render_target_path_d3d12`; source/destination tile spans; formats;
MSAA; chosen direct/compute/readback path; and result/invalidation range.

Suggested later observation points: `D3D12RenderTargetCache::Update`,
`draw_util::GetResolveInfo` and `D3D12RenderTargetCache::Resolve`.

No static G1.5A evidence identifies Fable's EDRAM aliasing pattern, MSAA mode,
resolve formats, clear behavior or runtime target path.
