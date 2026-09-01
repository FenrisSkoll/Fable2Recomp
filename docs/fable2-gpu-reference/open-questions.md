# G1.6B open questions

This ledger is generated from the authoritative [Fable relevance matrix](evidence/fable2-relevance-matrix.json), ownership and G2 decisions, the [G1.6A static XDK method inventory](evidence/static-xdk-method-inventory.json), and the [G1.6B seam-coverage evidence](evidence/static-xdk-seam-coverage.json). An unknown remains unknown until its stated minimum evidence exists.

Current supersession: **G2A RETIRED — DO NOT RESUME.** Historical G2A
questions and experiment IDs are retained for provenance, but no G2A gate is
active. See the [G2A retirement record](g2a-retirement.md).

## Cross-cutting questions

### `OQ-STATIC-XDK-METHODS`

**RESOLVED by `EXP-STATIC-XDK-001`: YES, narrowly.** `SXDK-001` / `sub_82BA77D0` has an exact TU1 boundary, bounded ABI, texture-fetch operation semantics, synchronous producer/asynchronous consumer ownership, state effects, resource-lifetime obligations and honest narrow coverage. See the [G1.6A report](12-static-xdk-method-recovery.md). This does not prove systemic coverage.

### `OQ-STATIC-XDK-COVERAGE`

**RESOLVED by `EXP-STATIC-XDK-002`: STATIC COVERAGE NARROW.** The exact
method-level lower bound is two confirmed texture producers; two additional
metadata-driven methods are texture-capable but unresolved. `SXDK-001` has two
direct callers, while `sub_82BAC718` and six common state-to-draw segments
bypass it. No ordinary material/mesh or named character, terrain, particle, UI,
video, post-processing or shadow root is statically connected to it. See the
[G1.6B report](13-static-xdk-seam-coverage.md).

- Remaining missing fact: Which dynamic selector records and indirect-buffer
  payloads feed the affected ordinary draws, and which host decision consumes
  them.
- Minimum evidence: The effective configuration/capability snapshot, followed
  by bounded draw-decision correlation that joins selector/binding identity
  without payload capture.
- Observation point: begin with `EXP-CONFIG-CAP-001`, then
  `EXP-DRAW-DECISION-001` if separately authorized.
- Static analysis: EXHAUSTED FOR THIS DECISION; later tooling: yes; user
  gameplay: only under a separately authorized bounded runtime phase.
- Decision unlocked: Rejects G1.6C interception-contract design as the next
  phase and retains `SXDK-001` only as a narrow supplemental seam.

### `OQ-LIONHEAD-ASYNC-ABI`

Does `sub_82AAC208` have a stable queue ABI, known producer/consumer threads, ownership, recursion behavior and representative operation coverage? Until proved, it is discovery-only.

### `OQ-SXDK-CALLBACK-OWNERSHIP`

- Exact missing fact: Whether the global `0x82000910` dispatcher copies the
  `sub_82BAA2B8` stack registration block, which thread invokes `SXDK-003`, and
  how `sub_821D1508` joins cleanup to guest-resource retirement.
- Minimum evidence: Exact dispatcher registration/invocation ABI, record
  retention proof, callback thread/queue identity and release-to-submission
  retirement join.
- Observation point: `sub_82BAA2B8` materialization
  `0x82BAA338/0x82BAA358`, dispatcher virtual slot `+0x18`,
  `sub_82BA8928`, `sub_821D1508`.
- Static analysis: PARTIAL; later tooling: yes if this narrow seam is revisited;
  user gameplay: no for ABI recovery.
- Decision unlocked: Could promote `SXDK-002`/`SXDK-003` technically, but would
  not reverse the proved narrow title-coverage decision by itself.

### `OQ-OWNERSHIP-INTERFACE`

Is there a single-owner interface—present in or validly added to ReXGlue—that lets a title renderer retain required guest GPU services without a second ring consumer, register/resource owner, renderer or presenter? The pinned corpus proves none.

### `OQ-G2A-LINKED-PROOF`

**CLOSED BY RETIREMENT, NOT PROVED.** The revised minimal
`sub_82BA34D8`/`__imp__sub_82BA34D8` Release proof was never performed.
Historical gate `EXP-G2A-LINK-001` is retired and must not be resumed.

### `OQ-SWAP-CORRELATION`

The mapping between `sub_82BA34D8`, `VdSwap_entry`, `XE_SWAP`, mailbox refresh
and DXGI Present remains unknown. Historical gate
`EXP-SWAP-CORRELATION-001` is retired with G2A. Any future presentation-only
question requires a new, separately authorized design that does not resurrect
the abandoned implementation.

### `OQ-DRAW-PROVENANCE`

Which bounded draw IDs produce the black dog and player-skin surfaces, and what are their terminal outcomes, shader/pipeline identities, bindings, EDRAM passes and resource lifetimes? Gates begin at `EXP-DRAW-DECISION-001`.

## Divergence questions

### `OQ-BCK-001` — `BCK-001`

- Exact missing fact: No missing fact for active backend identity; individual behavior rows carry causal questions.
- Minimum evidence: Retain the exact DLL hash and D3D12 provider identity with every later result.
- Observation point: `Runtime::CreateGraphicsSystem / rexgpu-xenos.dll`
- Static analysis: YES; later tooling: no; user gameplay: no.
- Decision unlocked: Keeps later evidence scoped to the deployed D3D12 artifact.
- Experiments: none.

### `OQ-BCK-002` — `BCK-002`

- Exact missing fact: Vulkan behavior is outside the D3D12-only artifact.
- Minimum evidence: A separately pinned Vulkan-capable artifact would be required for any future claim.
- Observation point: `Plugin manifest and CreateGraphicsSystem`
- Static analysis: YES; later tooling: no; user gameplay: no.
- Decision unlocked: None for the current artifact.
- Experiments: none.

### `OQ-BND-001` — `BND-001`

- Exact missing fact: The corpus does not provide a second composable graphics owner beside IGraphicsSystem.
- Minimum evidence: Static proof of a new ownership interface or a complete replacement provider contract.
- Observation point: `rex::graphics::IGraphicsSystem`
- Static analysis: YES; later tooling: no; user gameplay: no.
- Decision unlocked: Determines whether eventual replacement can avoid implementing the current GPU ABI.
- Experiments: none.

### `OQ-BND-002` — `BND-002`

- Exact missing fact: Which lifecycle services could be retained if rendering ownership changes.
- Minimum evidence: An ownership table tied to setup, memory callbacks, interrupts, vblank, presenter and shutdown interfaces.
- Observation point: `IGraphicsSystem::Setup / Shutdown`
- Static analysis: YES; later tooling: no; user gameplay: no.
- Decision unlocked: Gates any ownership transition.
- Experiments: none.

### `OQ-CFG-001` — `CFG-001`

- Exact missing fact: The complete effective Run 047/048 GPU CVar snapshot, including anisotropic_override=effective value, clear_memory_page_state, async_shader_compilation and relevant host-capability branches.
- Minimum evidence: A metadata-only configuration/capability snapshot from the exact DLL and RTX 5080; existing logs prove only adapter and listed D3D12 features.
- Observation point: `async_shader_compilation / anisotropic_override / clear_memory_page_state`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: no.
- Decision unlocked: Separates code identity from configuration-dependent behavior.
- Experiments: `EXP-CONFIG-CAP-001`.

### `OQ-CMD-001` — `CMD-001`

- Exact missing fact: Runtime ordering and identity of packets beyond the statically proven XE_SWAP operation.
- Minimum evidence: Only packet opcode, ring sequence ID and submission ID for a bounded scene.
- Observation point: `CommandProcessor::ExecutePacketType3`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Determines which detailed observation records are reachable.
- Experiments: `EXP-DRAW-DECISION-001`.

### `OQ-CMD-002` — `CMD-002`

- Exact missing fact: Whether TU1 emits the specific wait/event/coherency/interrupt operations in the affected scene.
- Minimum evidence: Opcode and ordering metadata for only those packet classes.
- Observation point: `CommandProcessor::ExecutePacketType3`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Determines whether synchronization divergence analysis is needed.
- Experiments: `EXP-DRAW-DECISION-001`.

### `OQ-DIA-001` — `DIA-001`

- Exact missing fact: No guest-behavior fact is missing; diagnostic tooling is deferred.
- Minimum evidence: A later tooling authorization and privacy review.
- Observation point: `Canary trace infrastructure`
- Static analysis: YES; later tooling: no; user gameplay: no.
- Decision unlocked: None for current compatibility.
- Experiments: none.

### `OQ-DIA-002` — `DIA-002`

- Exact missing fact: No exact Fable GPU failure has selected an unsupported/fallback/device-loss path.
- Minimum evidence: The first exact diagnostic, source branch and outcome if such a failure occurs.
- Observation point: `REX_FATAL / unsupported packet branches`
- Static analysis: NO; later tooling: yes; user gameplay: yes.
- Decision unlocked: Narrows robustness work to a demonstrated failure.
- Experiments: none.

### `OQ-DRW-001` — `DRW-001`

- Exact missing fact: The topology, predication and outcome of the affected character draws.
- Minimum evidence: One per-draw decision record with draw ID, primitive/index counts, extents, predication and outcome.
- Observation point: `D3D12CommandProcessor::IssueDraw`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Raises evidence from broad draw execution to L3.
- Experiments: `EXP-DRAW-DECISION-001`.

### `OQ-DRW-002` — `DRW-002`

- Exact missing fact: Whether EVENT_WRITE_ZPD is used, which report slots are opened/closed across submissions, and whether a slot is reused before retirement.
- Minimum evidence: Opcode, report slot, begin/end sequence, submission ID and retirement/reuse result; no query payload.
- Observation point: `D3D12CommandProcessor::ExecutePacketType3_EVENT_WRITE_ZPD / EndSubmission`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Tests whether ZPD lifetime can affect the scene.
- Experiments: `EXP-ZPD-REPORT-001`, `EXP-CANDIDATE-AB-001`.

### `OQ-MEM-001` — `MEM-001`

- Exact missing fact: Which guest resource ranges and cache consumers back the affected draws.
- Minimum evidence: Hashed resource identity, range, validity transition and submission ordering.
- Observation point: `SharedMemory::RequestRanges / RangeWrittenByGpu`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Provides resource lifetime context without payloads.
- Experiments: `EXP-MEM-LIFECYCLE-001`.

### `OQ-MEM-002` — `MEM-002`

- Exact missing fact: Whether an affected range is decommitted, released or protected writable while unwatched and later consumed from a GPU cache.
- Minimum evidence: Mapping operation, range, watch state, validity generation and hashed cache consumer identity.
- Observation point: `PhysicalHeap::TriggerCallbacks / SharedMemory::RequestRanges`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Confirms or clears the unwatched invalidation path.
- Experiments: `EXP-MEM-LIFECYCLE-001`, `EXP-CANDIDATE-AB-001`.

### `OQ-PIP-001` — `PIP-001`

- Exact missing fact: Which pipeline hashes and binding layout correspond to the affected character draws.
- Minimum evidence: Draw ID, VS/PS hashes, pipeline hash, root/binding layout hash and readiness.
- Observation point: `PipelineCache::ConfigurePipeline / UpdateBindings`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Correlates draw outcomes without shader bodies.
- Experiments: `EXP-DRAW-DECISION-001`.

### `OQ-PIP-002` — `PIP-002`

- Exact missing fact: The effective async setting, pipeline readiness at each affected draw, exact skip reason and readiness by EndSubmission.
- Minimum evidence: Draw ID, pipeline hash, async setting, configure result, ready/pending state, skip outcome and submission-end wait state.
- Observation point: `PipelineCache::ConfigurePipeline / D3D12CommandProcessor::IssueDraw / EndSubmission`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Confirms or clears missing draws caused by pipeline readiness.
- Experiments: `EXP-CONFIG-CAP-001`, `EXP-DRAW-DECISION-001`, `EXP-SHADER-IDENTITY-001`, `EXP-CANDIDATE-AB-001`.

### `OQ-PIP-003` — `PIP-003`

- Exact missing fact: Whether RTX 5080 exposes alpha-factor support and whether an affected draw uses constant-alpha blend factors with divergent alpha/color constants.
- Minimum evidence: Capability bit plus RB_BLENDCONTROL, RB_BLEND_ALPHA and color values for the affected draw.
- Observation point: `PipelineCache::ConfigurePipeline / D3D12CommandProcessor::IssueDraw`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Confirms applicability of constant-alpha fallback.
- Experiments: `EXP-CONFIG-CAP-001`, `EXP-DRAW-DECISION-001`, `EXP-CANDIDATE-AB-001`.

### `OQ-PRE-001` — `PRE-001`

- Exact missing fact: The exact one-to-one or many-to-one relation between title swap requests, mailbox publication, refresh and DXGI Present.
- Minimum evidence: Monotonic IDs and timestamps only at sub_82BA34D8, VdSwap_entry, RefreshGuestOutput and PaintAndPresentImpl.
- Observation point: `sub_82BA34D8 / VdSwap_entry / Presenter::RefreshGuestOutput / D3D12Presenter::PaintAndPresentImpl`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Establishes presentation correlation; it does not diagnose black surfaces.
- Experiments: historical `EXP-SWAP-CORRELATION-001` is retired; no active
  replacement experiment is selected.

### `OQ-PRE-002` — `PRE-002`

- Exact missing fact: No timing-sensitive link to the localized black surfaces is demonstrated.
- Minimum evidence: Vblank counter and swap correlation only if a later timing hypothesis arises.
- Observation point: `GraphicsSystem::VsyncWorker`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Determines whether pacing investigation is justified.
- Experiments: none.

### `OQ-REG-001` — `REG-001`

- Exact missing fact: For every Canary-seeded register, whether TU1 reads it before the first guest write and which draw consumes that value.
- Minimum evidence: Register index, seeded value, first read sequence, first write sequence and consuming draw ID.
- Observation point: `D3D12CommandProcessor::WriteRegister / D3D12CommandProcessor::IssueDraw`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Confirms or clears reset-default relevance.
- Experiments: `EXP-REGISTER-RESET-001`, `EXP-DRAW-DECISION-001`, `EXP-CANDIDATE-AB-001`.

### `OQ-REG-002` — `REG-002`

- Exact missing fact: The exact register writes consumed by the affected character draws.
- Minimum evidence: Draw ID plus changed-register indices and hashed state snapshot; no broad register dump.
- Observation point: `D3D12CommandProcessor::WriteRegister / IssueDraw`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Links guest state to a draw decision.
- Experiments: `EXP-DRAW-DECISION-001`.

### `OQ-RT-001` — `RT-001`

- Exact missing fact: Which render-target passes, aliases and resolves produce or consume the affected character surfaces.
- Minimum evidence: Draw/pass ID, EDRAM base/pitch, formats, MSAA, alias generation and resolve ID.
- Observation point: `D3D12RenderTargetCache::Update / Resolve`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Identifies the relevant EDRAM subpath.
- Experiments: `EXP-EDRAM-RESOLVE-001`.

### `OQ-RT-002` — `RT-002`

- Exact missing fact: Whether an affected pass uses a divergent 1x/2x/4x canonical EDRAM pattern.
- Minimum evidence: Pass ID, EDRAM bases/pitches, MSAA, alias IDs, sample coordinates and resolve coordinates.
- Observation point: `D3D12RenderTargetCache::Update / GetResolveInfo / Resolve`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Confirms canonical-addressing applicability.
- Experiments: `EXP-EDRAM-RESOLVE-001`, `EXP-CANDIDATE-AB-001`.

### `OQ-RT-003` — `RT-003`

- Exact missing fact: Whether an affected scaled resolve is read back and consumed from shared memory.
- Minimum evidence: ResolveInfo identity, scale, written extent, destination range/hash and later consumer ID.
- Observation point: `draw_util::GetResolveInfo / D3D12RenderTargetCache::Resolve / SharedMemory::RangeWrittenByGpu`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Confirms scaled-readback applicability.
- Experiments: `EXP-EDRAM-RESOLVE-001`, `EXP-CANDIDATE-AB-001`.

### `OQ-RT-004` — `RT-004`

- Exact missing fact: Whether an affected resolve uses 8_8_8_8_GAMMA or fixed-number conversion and the copy_dest_number consumed.
- Minimum evidence: Source/destination formats, copy_dest_number, coordinates, destination hash and consumer ID.
- Observation point: `draw_util::GetResolveInfo / D3D12RenderTargetCache::Resolve`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Confirms gamma/fixed-number conversion applicability.
- Experiments: `EXP-EDRAM-RESOLVE-001`, `EXP-CANDIDATE-AB-001`.

### `OQ-RT-005` — `RT-005`

- Exact missing fact: Whether affected render-target or memexport values use extended float16 encodings above 65504 or exponent 31.
- Minimum evidence: Format, pass/shader hash, min/max/classified value range and consumer ID; no pixel or buffer payload.
- Observation point: `D3D12RenderTargetCache::Resolve / Shader::AnalyzeUcode`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Confirms extended-float16 applicability.
- Experiments: `EXP-EDRAM-RESOLVE-001`, `EXP-CANDIDATE-AB-001`.

### `OQ-SHD-001` — `SHD-001`

- Exact missing fact: The VS/PS identities and pipeline decisions for the affected character draws.
- Minimum evidence: Draw ID, stage hashes, pipeline hash, analysis flags and outcome; no microcode body.
- Observation point: `PipelineCache::LoadShader / Shader::AnalyzeUcode / ConfigurePipeline`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Identifies shaders safely enough for focused static analysis.
- Experiments: `EXP-SHADER-IDENTITY-001`.

### `OQ-SHD-002` — `SHD-002`

- Exact missing fact: Whether an affected Fable shader executes EXP/LOG/RCP/RSQ/SQRT-family scalar operations on precision-sensitive values; the hardware precision model remains unresolved.
- Minimum evidence: Shader hash, operation-class bitset, operand/result classification or controlled hash comparison; no shader body.
- Observation point: `Shader::AnalyzeUcode / translated scalar ALU path`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Confirms applicability and scopes a later controlled precision test.
- Experiments: `EXP-SHADER-IDENTITY-001`, `EXP-CANDIDATE-AB-001`.

### `OQ-TEX-001` — `TEX-001`

- Exact missing fact: Which fetches and resource identities feed the affected character draws.
- Minimum evidence: Draw ID, shader hash, fetch slot, binding hash, resource range hash and validity generation.
- Observation point: `D3D12CommandProcessor::UpdateBindings / D3D12TextureCache::RequestTextures`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Identifies affected resources without texture payloads.
- Experiments: `EXP-TEXTURE-METADATA-001`.

### `OQ-TEX-002` — `TEX-002`

- Exact missing fact: Whether an affected base/mip range is invalid when MakeUpToDateAndWatch declares it current and whether the cached texture is consumed.
- Minimum evidence: Hashed resource ID, base/mip ranges, validity before/after, watch state and consuming draw ID.
- Observation point: `TextureCache::Texture::MakeUpToDateAndWatch / SharedMemory::RequestRanges`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Confirms or clears stale texture currency.
- Experiments: `EXP-TEXTURE-METADATA-001`, `EXP-CANDIDATE-AB-001`.

### `OQ-TEX-003` — `TEX-003`

- Exact missing fact: Whether an affected fetch uses integer num_format scaling and which components/format are consumed.
- Minimum evidence: Shader hash, fetch slot, format, num_format, component bits/scales and draw ID.
- Observation point: `Shader::AnalyzeUcode / D3D12TextureCache::RequestTextures`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Confirms integer-scaling applicability.
- Experiments: `EXP-TEXTURE-METADATA-001`, `EXP-CANDIDATE-AB-001`.

### `OQ-TEX-004` — `TEX-004`

- Exact missing fact: Whether an affected fetch is filtered normalized unsigned fixed and rounding-sensitive.
- Minimum evidence: Shader hash, fetch slot, format, num_format, filter/sampler state and value-class boundary flag.
- Observation point: `Shader::AnalyzeUcode / D3D12TextureCache::RequestTextures`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Confirms normalized-rounding applicability.
- Experiments: `EXP-TEXTURE-METADATA-001`, `EXP-CANDIDATE-AB-001`.

### `OQ-TEX-005` — `TEX-005`

- Exact missing fact: Whether an affected fetch has distinct base/mip pages with nonzero mip_min_level and samples base LOD 0.
- Minimum evidence: Fetch slot, base_page, mip_page, mip_min_level, dimensions, sampler LOD and draw ID.
- Observation point: `D3D12TextureCache::RequestTextures / UpdateBindings`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Confirms base-map selection applicability.
- Experiments: `EXP-TEXTURE-METADATA-001`, `EXP-CANDIDATE-AB-001`.

### `OQ-TEX-006` — `TEX-006`

- Exact missing fact: Whether an affected shader contains promoted tfetch1D and the bound resource layout/dimensions differ.
- Minimum evidence: Shader hash, instruction slot, source dimension, runtime layout, width/height and draw ID.
- Observation point: `Shader::AnalyzeUcode / D3D12TextureCache::RequestTextures`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Confirms 1D-layout applicability.
- Experiments: `EXP-TEXTURE-METADATA-001`, `EXP-CANDIDATE-AB-001`.

### `OQ-TEX-007` — `TEX-007`

- Exact missing fact: Whether an affected fetch header contains only literal swizzles and whether binding existence changes the layout.
- Minimum evidence: Fetch slot, literal swizzle tuple, declared dimensions, binding-present flag and layout hash.
- Observation point: `D3D12TextureCache::RequestTextures / UpdateBindings`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Confirms dummy-header applicability.
- Experiments: `EXP-TEXTURE-METADATA-001`, `EXP-CANDIDATE-AB-001`.

### `OQ-VTX-001` — `VTX-001`

- Exact missing fact: Whether an affected Fable draw emits a tessellated triangle strip or fan and whether processing rejects it.
- Minimum evidence: Draw ID, guest topology, tessellation mode, primitive-processing result and exact no-draw outcome.
- Observation point: `PrimitiveProcessor::Process / D3D12CommandProcessor::IssueDraw`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Confirms topology-conversion applicability.
- Experiments: `EXP-VERTEX-FETCH-001`, `EXP-CANDIDATE-AB-001`.

### `OQ-VTX-002` — `VTX-002`

- Exact missing fact: Whether an affected vertex fetch addresses lanes at or beyond its fetch-constant size.
- Minimum evidence: Shader hash, fetch slot, base, size, element index, lane byte offsets and out-of-range mask.
- Observation point: `Shader::AnalyzeUcode / PrimitiveProcessor::Process / IssueDraw`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Confirms bounds-zeroing applicability.
- Experiments: `EXP-VERTEX-FETCH-001`, `EXP-CANDIDATE-AB-001`.

### `OQ-VTX-003` — `VTX-003`

- Exact missing fact: Whether any affected allocation or vertex/index address enters 0x7F000000..0x7FC7FFFF or requires L2 wrapping.
- Minimum evidence: Allocation/range class, masked and unmasked address, fetch/index use and draw ID.
- Observation point: `Memory::LookupHeap / PrimitiveProcessor::Process`
- Static analysis: PARTIAL; later tooling: yes; user gameplay: yes.
- Decision unlocked: Confirms XPS applicability.
- Experiments: `EXP-VERTEX-FETCH-001`, `EXP-CANDIDATE-AB-001`.
