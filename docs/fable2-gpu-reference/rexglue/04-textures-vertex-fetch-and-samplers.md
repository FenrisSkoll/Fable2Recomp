# Textures, vertex fetch and samplers

All locators refer to ReXGlue commit
`956c6a8b5da4c54b9899a2593e9c67c26de30194`.

## Vertex fetch and index data

`Shader::GatherVertexFetchInformation` in
`src/graphics/pipeline/shader/translator.cpp` records which Xenos vertex fetch
constants and formats a shader consumes. At draw time,
`D3D12CommandProcessor::UpdateBindings` in
`src/graphics/d3d12/command_processor.cpp` reads those fetch constants, derives
guest ranges, requests them from `D3D12SharedMemory`, and emits bindful or
bindless SRV descriptors.

Xenos fetch constants specify base/size/stride, format, signed/scaled behavior
and endian conversion. ReXGlue's Xenos format utilities supply host layout and
swizzle/conversion rules. The D3D12 shader translator performs format/endian
loads against the shared-memory buffer; this is not a separate semantic vertex
object layer.

Draw packets provide index source, size, endian and reset information.
`PrimitiveProcessor::Process` in `src/graphics/primitive_processor.cpp` maps
Xenos topology to a host topology and, when needed, expands line loops,
triangle fans, quads and multi-primitive/reset forms. It maintains a conversion
cache watched against guest memory. `D3D12PrimitiveProcessor` owns built-in and
per-frame converted D3D12 index buffers. Immediate indices are explicitly not
supported by the current common path.

Inputs are shader fetch analysis, current fetch constants and guest physical
ranges; outputs are shared-memory SRVs, converted index buffers and a host
primitive topology. Persistent state is fetch residency and the watched
primitive-conversion cache.

## Texture key and layout

Common `TextureCache` is declared in
`include/rex/graphics/pipeline/texture/cache.h` and implemented in
`src/graphics/pipeline/texture/cache.cpp`. `BindingInfoFromFetchConstant`
interprets a `xe_gpu_texture_fetch_t`; the resulting `TextureKey` captures:

- base and mip pages;
- dimension, width, height, depth/array and pitch;
- tiled/linear layout and packed mip status;
- Xenos texture format;
- endian, signedness, exponent/scaling and swizzle-relevant state; and
- draw-resolution scaling/resolve compatibility.

Layout helpers in the `pipeline/texture` and Xenos format layers calculate
subresources, packed mip offsets and tiled addresses. Those layouts are
Xenos-generic. Cache budgets, object identity, host format selection and load
shader choice are ReXGlue policies.

## Cache, coherency and residency

`TextureCache::RequestTextures` receives the used-texture mask produced by
shader analysis. It derives bindings, finds or creates `Texture` objects,
batches shared-memory range requests and calls `MakeUpToDateAndWatch`.
Physical-memory invalidation callbacks reach `TextureCache::WatchCallback`,
which invalidates affected content. Resolved ranges have separate global-watch
handling for scaled resolves.

The cache tracks use and host memory for LRU pressure. Common cvars define a
render-to-texture allowance, soft/hard memory limits, soft lifetime and optional
3D-to-2D handling. `BeginSubmission`, `CompletedSubmissionUpdated` and
`BeginFrame` constrain destruction/reuse against in-flight work.

## D3D12 texture conversion and views

`D3D12TextureCache::CreateTexture` selects a host resource format/layout.
`LoadTextureDataFromResidentMemoryImpl` uses generated compute shaders to
untile, endian-convert, decompress or expand unsupported native layouts and
formats. The active corpus pins generated load shaders for 8/16/32/64/128-bpp,
depth, DXT and packed formats, including scaled variants.

`UpdateTextureBindingsImpl` and descriptor helpers create SRVs for the current
draw. Bindless descriptors are used when the D3D12 binding tier and
`d3d12_bindless` allow it; otherwise descriptor tables come from the command
processor's bindful pools. `RequestSwapTexture` is a specialized route that
reads texture fetch constant `0` for presentation.

Unsupported format features are accumulated in
`unsupported_format_features_used_` and reported per frame. This is a
diagnostic/fallback path, not proof that Fable uses the format.

## Sampler translation

Common `SamplerInfo` and texture fetch state preserve Xenos filtering, LOD,
anisotropy, border and clamp modes. `D3D12TextureCache::GetSamplerParameters`
builds D3D12 sampler keys and `WriteSampler` emits descriptors.
`NormalizeClampMode` maps modes D3D12 cannot represent exactly to available
addressing behavior. Shader translator source also retains TODOs for some
fetch LOD, gradient and filter semantics. These approximations are part of the
current baseline.

## Backend boundary

Backend-independent behavior:

- fetch constant parsing and `TextureKey`;
- guest layout/tiling calculations;
- memory-watch invalidation and LRU policy;
- shader resource-use analysis; and
- primitive/index conversion algorithms.

D3D12-specific behavior:

- resource and view formats;
- compute load/conversion shaders;
- descriptor allocation/bindless policy;
- sampler approximation; and
- D3D12 resource states/submission lifetime.

Vulkan supplies parallel texture and primitive classes but is
`NOT APPLICABLE` to the active DLL.

## Fable connection and unknowns

`CONFIRMED` — the accepted Fable swap path ultimately asks
`D3D12TextureCache::RequestSwapTexture` to interpret fetch constant 0, as a
ReXGlue source edge after `PM4_XE_SWAP`. A fully correlated Fable runtime event
is still absent.

`UNKNOWN FOR FABLE II`

Evidence required: used vertex/texture fetch indices, raw constants,
`TextureKey`, guest ranges, format/endian conversion, cache hit/load result,
sampler key and primitive-conversion result for representative Fable draws.

Suggested later observation points: `D3D12CommandProcessor::UpdateBindings`,
`D3D12TextureCache::RequestTextures`,
`D3D12TextureCache::RequestSwapTexture` and
`PrimitiveProcessor::Process`.
