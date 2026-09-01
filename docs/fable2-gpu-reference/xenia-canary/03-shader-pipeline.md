# Xenia Canary shader pipeline

## Evidence basis

All source locators refer to
`xenia-canary/xenia-canary@3a44f20c7bc66db1da583e8a6f0ab740e31908e9`.
Descriptions of intent are marked separately from implemented behavior.

## Loading and identity

`IM_LOAD` and `IM_LOAD_IMMEDIATE` handlers in
`src/xenia/gpu/pm4_command_processor_implement.h` select a vertex or pixel
shader and call the concrete pipeline cache's `LoadShader`.

The D3D12 `PipelineCache::LoadShader` and Vulkan
`VulkanPipelineCache::LoadShader` hash the guest ucode bytes with XXH3 and
look up a `Shader` by hash. `src/xenia/gpu/shader.cc:Shader::Shader` copies
the ucode into owned storage. A `Shader` may own multiple
`Shader::Translation` instances for different backend modifications.

This makes the persistent identity:

```text
guest physical shader bytes
  -> XXH3 ucode hash
  -> Shader (copied ucode + shared analysis)
  -> Translation modification
  -> backend binary and pipeline use
```

This identity and ownership are **CONFIRMED**. Hash collision behavior or
runtime cache effectiveness is **UNKNOWN**.

## Xenos ucode analysis

`src/xenia/gpu/shader_translator.cc:Shader::AnalyzeUcode` begins from the
paired control-flow instruction region at the head of ucode. It identifies
labels and the reachable/control-flow range, then analyzes:

- exec sequences and vertex/pixel allocation;
- ALU scalar/vector operations and constant usage;
- vertex fetches, texture fetches, and their bindings;
- bool, loop, float, fetch, and system constant maps;
- interpolator and point/rectangle expansion requirements;
- kills and color/depth exports; and
- memory-export instructions and their control-flow reachability.

The results are stored on `Shader` and consumed by both backends. This stage
does not emit a host shader.

**CONFIRMED limitation.** Analyzer comments contain deliberate conservative
approximations. For example, calls can be treated as potentially affecting all
memory-export address registers. Such comments establish implementation policy,
not exact hardware behavior.

## Shared translation

`ShaderTranslator::TranslateAnalyzedShader` walks the analyzed control-flow
graph and dispatches translation of Xenos control-flow, ALU, fetch, export, and
memory-export semantics. `ShaderTranslator` also assigns the binding layout
expected by backend command processors.

Inputs:

- analyzed `Shader`;
- shader type and guest bindings;
- a `Shader::Translation::Modification`;
- host feature and output-merger requirements.

Outputs:

- generated backend instructions and metadata;
- texture, sampler, vertex, constant, export, and memexport binding
  requirements;
- validation errors and optional disassembly/dump data.

## D3D12 translation

`src/xenia/gpu/dxbc_shader_translator.cc:DxbcShaderTranslator::StartTranslation`
and `DxbcShaderTranslator::CompleteTranslation` frame creation of DXBC. The
base `ShaderTranslator::TranslateAnalyzedShader` invokes the backend hooks
while traversing the shared analysis and emitting
Direct3D tokens and resource declarations.

Material backend-specific choices include:

- root-signature-compatible constant-buffer, SRV, UAV, and sampler mapping;
- bindless versus bindful resource access;
- host render-target versus ROV output-merger modifications;
- vertex/index/primitive expansion helpers;
- memory-export and shared-memory access;
- system constants and interpolator mapping; and
- a `dxbc_switch` strategy with a documented Intel-specific exception path.

These branches are **CONFIRMED source behavior**. Their relative driver
performance and equivalence are **UNKNOWN**.

## Vulkan translation

`src/xenia/gpu/spirv_shader_translator.cc:SpirvShaderTranslator::StartTranslation`
and `SpirvShaderTranslator::CompleteTranslation` frame creation of SPIR-V.
The base `ShaderTranslator::TranslateAnalyzedShader` invokes the backend hooks
during shared traversal.

Material capability branches include:

- supported SPIR-V version;
- float-control modes;
- fragment shader interlock for the EDRAM FSI path;
- demote-to-helper support;
- descriptor and push/system-constant layout;
- manual vertex fetch, texture fetch, and memory-export access; and
- render-pass/output specialization.

The `VulkanDevice` capability selection supplies these inputs. A feature
being implemented in source does not prove a particular device exposes it.

## Constants, fetches, and memory export

Shader analysis records which float, bool, loop, fetch, and system constants
are used. Backend `IssueDraw` paths upload and bind only the ranges required
by the active translation and current register state.

Vertex fetch is not materialized as a separate fixed-function Xbox vertex
buffer declaration. The translated host shader reads the shared guest-memory
view using analyzed vertex-fetch instructions and constants, including format
and endian transformations.

Texture fetches become texture/sampler bindings prepared by `TextureCache`
and `SamplerInfo`. Memory exports become shader writes to shared-memory-backed
resources; readback policy controls CPU visibility. All are **CONFIRMED**
architectural relationships.

## Translation and persistent caches

Both pipeline caches maintain:

- ucode-hash to `Shader` maps;
- modification-specific translations;
- title/configuration-keyed persistent shader storage;
- pipeline-description lookup; and
- optional creation workers.

Vulkan additionally loads/saves a native Vulkan pipeline-cache blob named from
the title, alongside Canary's own storage. D3D12 stores its corresponding
translated/pipeline data through its pipeline storage implementation.

Asynchronous compilation does not authorize use of an unfinished host
pipeline. The backends queue creation and wait before a submission that needs
the pipeline is actually sent. Startup code separately comments that draws may
be skipped until shader storage initialization is ready. These are two
different conditions and must not be conflated.

## Diagnostics and static unknowns

- Translation errors, optional ucode/host disassembly, and shader dumps are
  controlled by diagnostic cvars. They do not by themselves alter guest state.
- Exact Xenos precision, undefined-input, and corner-case semantics are
  **UNKNOWN** unless directly encoded and validated.
- Host compiler and driver decisions after DXBC/SPIR-V creation are **UNKNOWN**.
- Pipeline and translation cache hit rates are **UNKNOWN** statically.
- Which shader features a title uses is **NOT APPLICABLE** to G1.5B.

The pinned commit
`3a44f20c7bc66db1da583e8a6f0ab740e31908e9` has primary rationale for
replacing a title-specific ground workaround with scalar approximation
rounding. Its commit message explicitly leaves exact precision and halfway
behavior unconfirmed. This is **CONFIRMED rationale** and an **UNKNOWN hardware
equivalence**, not evidence about Fable II.
