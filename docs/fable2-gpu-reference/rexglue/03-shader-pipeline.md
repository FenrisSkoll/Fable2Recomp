# Shader pipeline

All locators refer to ReXGlue commit
`956c6a8b5da4c54b9899a2593e9c67c26de30194`.

## Load and identity

`CommandProcessor::ExecutePacketType3_IM_LOAD` and
`ExecutePacketType3_IM_LOAD_IMMEDIATE` in
`src/graphics/command_processor.cpp` parse shader type, address and dword count,
then call virtual `LoadShader`. The active override is
`D3D12CommandProcessor::LoadShader`, which delegates to
`PipelineCache::LoadShader` in `src/graphics/d3d12/pipeline_cache.cpp`.

The cache hashes the exact guest microcode bytes with XXH3 and keys the shader
by type and hash. `Shader::Shader` in
`src/graphics/pipeline/shader/shader.cpp` copies the microcode into owned host
storage with the expected Xenos endian normalization. `Shader` owns multiple
translations under distinct 64-bit modification keys; the guest shader and a
host specialization are not the same identity.

Inputs are guest microcode, type/address/length and register/topology/render
target state. Persistent outputs are analysed `Shader` objects, translated
bytecode variants, D3D12 PSOs and optional persistent cache records.

## Microcode analysis

`Shader::AnalyzeUcode` in `src/graphics/pipeline/shader/translator.cpp` decodes
pairs of Xenos control-flow instructions and builds:

- control-flow labels and parsed exec blocks;
- ALU, vertex-fetch and texture-fetch instruction information;
- constant and interpolator use;
- vertex and texture resource bindings;
- memory-export streams and written components; and
- disassembly and translation diagnostics.

The key gathering functions are `GatherExecInformation`,
`GatherVertexFetchInformation`, `GatherTextureFetchInformation`,
`GatherAluInstructionInformation` and the operand/result gatherers. Analysis is
common and backend-independent. It recovers low-level Xenos semantics, not
Fable shader/material names.

## Modification and host translation

Before a draw, `PipelineCache::GetCurrentVertexShaderModification` and
`GetCurrentPixelShaderModification` combine register state, primitive/host
vertex shader type, render-target path and other specialization decisions.
`Shader::GetOrCreateTranslation` returns the corresponding translation object.

`ShaderTranslator::TranslateAnalyzedShader` walks the analysed control flow and
dispatches fetch/ALU/export operations to a concrete translator. In the current
artifact, `DxbcShaderTranslator` is built from:

- `pipeline/shader/dxbc_translator.cpp`;
- `_alu.cpp`;
- `_fetch.cpp`;
- `_memexport.cpp`; and
- `_om.cpp`.

It emits DXBC vertex/domain/hull/pixel variants, resource and sampler access,
memory export and, for the pixel-shader-interlock EDRAM path, custom
output-merger logic. SPIR-V translator files exist but are excluded because
`REXGLUE_USE_VULKAN=OFF`.

Translation errors are recorded by `ShaderTranslator::EmitTranslationError`.
Some cases are non-fatal approximations; unsupported host shader types or
instructions can make a translation unusable. Examples present in source
include incomplete `getBCF`, LOD/gradient/filter TODOs and unsupported patch
types. Their relevance to Fable is not known.

## Pipeline and persistent caches

`PipelineCache::ConfigurePipeline` obtains translations, builds a deterministic
description of shaders and fixed state, hashes it with XXH3, and looks up the
D3D12 PSO cache. `PipelineCache::CreateD3D12Pipeline` creates the host PSO and
root-signature-compatible shader combination. Generated helper shaders cover
topology conversion, tessellation, texture loads, resolves, clears and guest
output; 110 D3D12 Shader Model 5.1 bytecode headers are pinned in the source
inventory.

`InitializeShaderStorage` uses the title ID and cache root. The pinned source
stores shareable shader analysis/translation data beneath
`shaders/shareable/<title>.xsh` and D3D12 pipeline state beneath a title/mode
file such as `<title>.<rov|rtv>.d3d12.xpso`. Headers contain magic/version/hash
checks before reuse. Storage writes and PSO creation use dedicated queues and
threads; shutdown drains/joins their work.

With `async_shader_compilation=true`, missing translations/pipelines may be
queued. `D3D12CommandProcessor::IssueDraw` treats a still-pending pipeline as a
temporary non-rendering draw and returns success so execution can continue.
The source comments acknowledge a brief artifact. This is behavior to preserve
when describing the baseline, not evidence of acceptable Fable parity.

## Invalidation and lifetime

Shaders are retained in the pipeline cache by guest hash. Register changes do
not mutate analysed microcode; they select or invalidate modification/pipeline
state. `PipelineCache::EndSubmission` advances completion and creation work.
`ClearCaches` and shutdown release PSOs/translations subject to submission
lifetime.

Optional `dump_shaders`, `d3d12_dxbc_disasm` and DXIL-conversion disassembly are
diagnostics. The existing log reports absent `dxcompiler.dll`, meaning converted
DXIL disassembly is unavailable; it does not mean normal DXBC execution failed.

No dedicated first-party shader translator/pipeline tests were found in the
pinned ReXGlue test tree. Generated bytecode presence is not a functional test.

## Fable connection and unknowns

`UNKNOWN FOR FABLE II`

Evidence required: `IM_LOAD` type/address/length, microcode XXH3, analysis
result, modification key, translation status and pipeline hash for observed
Fable draws.

Suggested later observation points: `PipelineCache::LoadShader`,
`Shader::AnalyzeUcode`, `PipelineCache::TranslateAnalyzedShader` and
`PipelineCache::ConfigurePipeline`.

Without those events, no G1.5A claim identifies a Fable shader, a translation
failure, a cache hit or an asynchronously skipped title draw.
