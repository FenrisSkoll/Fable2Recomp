# ReXGlue and Xenia Canary divergence

## Scope and result

This is the G1.5C source comparison between these immutable baselines:

| Implementation | Repository | Commit | Tree |
|---|---|---|---|
| ReXGlue | `C:\Dev\rexglue-sdk-v0.10` | `956c6a8b5da4c54b9899a2593e9c67c26de30194` | `b78b06b8ac650467372236a3a262864e069a9382` |
| Xenia Canary | `C:\Dev\Fable2NativeRendererResearch\xenia-canary` | `3a44f20c7bc66db1da583e8a6f0ab740e31908e9` | `c343b0a5796590fadc3b78c993bfada51e7e9148` |

The exact active ReXGlue artifact remains the D3D12-only
`rexgpu-xenos.dll`, 2,770,944 bytes, SHA-256
`8232051BED6E5CE99CF37B2EF581C824F58875C140A4D3C75DE14E8A5DF4AA99`.
No source or artifact pin was advanced.

The authoritative, deterministic record set is
[divergence-matrix.json](evidence/divergence-matrix.json). It contains 37
behaviors. Each row below follows equivalent call chains rather than relying
on filenames or textual diffs. “Same” means no material difference was found
at this static-source granularity; it is not a claim of complete Xenos parity.
Canary-only behavior is not automatically better or Fable-relevant.

## Method and evidence boundary

For each behavior, the audit established the pinned ReXGlue path, the pinned
Canary path, the material semantic delta, primary history where available,
preliminary Fable evidence, and a renderer implication. Exact paths, types,
symbols, call relationships, history links, confidence labels, evidence still
required, and open questions are retained in the matrix. The independent
[ReXGlue](01-rexglue-overview.md) and
[Canary](02-xenia-canary-overview.md) descriptions were not rewritten to make
them agree.

The only accepted title-specific observations are the existing G1 evidence:
`sub_82BA34D8` at `[0x82BA34D8,0x82BA3BFC)`, size `0x724`, calls
`VdGetSystemCommandBuffer` and `VdSwap`; Run 047 presents frames in which the
dog and player skin/head are black while environment, UI, lighting, and some
clothing render normally. That symptom does not establish any cause below.

## 1. Plugin/runtime boundary

| ID | ReXGlue, Canary, and material result | History and preliminary Fable/renderer result |
|---|---|---|
| `BND-001` | ReXGlue loads `rexgpu-xenos.dll` and creates an `IGraphicsSystem` through its plugin ABI; Canary owns an in-process backend factory. The runtime-loaded ABI is **REXGLUE-ONLY**, not a guest-GPU correction. | Plugin extraction and routing are confirmed by `REX-c22a33e2` and `REX-55a836fb`. Fable use is **CONFIRMED RELEVANT** because the accepted run loads this boundary. A future renderer must satisfy it regardless of which GPU internals it uses. |
| `BND-002` | ReXGlue splits presentation setup from guest-GPU setup, embeds its register file, and connects memory and interrupts through runtime callbacks. Canary has a combined setup and puts its register file in fixed guest-addressable memory under emulator ownership. This is **SEMANTICALLY DIFFERENT** host architecture. | `REX-506eee89` and `REX-55a836fb` give **CONFIRMED RATIONALE**. The lifecycle is reached by Fable, but whether any difference affects title behavior remains for G1.5D. Canary ownership must not be transplanted across the ReXGlue ABI. |

## 2. Ring and system command buffers

| ID | ReXGlue, Canary, and material result | History and preliminary Fable/renderer result |
|---|---|---|
| `CMD-001` | Both run the guest ring, decode PM4 types 0–3, enter indirect buffers, and dispatch `XE_SWAP`. ReXGlue is largely monolithic; Canary splits templated handlers into a separate implementation header. This is **SAME BEHAVIOUR, DIFFERENT STRUCTURE**. | Historical rationale is **NOT APPLICABLE**. `XE_SWAP` reachability is **CONFIRMED RELEVANT** through `sub_82BA34D8`; use of other opcodes needs packet or guest-code evidence. Packet semantics, not Canary's file organization, are the renderer obligation. |
| `CMD-002` | Both implement waits, events, interrupt callbacks, coherency requests, and operation triggers, including materially similar incomplete useful-cache invalidation. This is **SAME BEHAVIOUR, DIFFERENT STRUCTURE**. | Fable relevance is **UNKNOWN FOR FABLE II** until the affected packets are shown. Shared incompleteness is a renderer requirement to investigate, not a divergence to port. |

## 3. Registers, dirty state, and triggers

| ID | ReXGlue, Canary, and material result | History and preliminary Fable/renderer result |
|---|---|---|
| `REG-001` | ReXGlue zeroes the register file. Canary then seeds measured nonzero retail-hardware context-register reset values, excluding uncertain tessellation levels. Reads before guest writes therefore differ. This is **CANARY-ONLY**, classified **XENOS ACCURACY CORRECTION**. | `CAN-e20f2696` gives **CONFIRMED RATIONALE**. Fable relevance is **UNKNOWN FOR FABLE II** until TU1 write/read ordering for affected registers is established. Reset state is a candidate guest contract, not an automatic implementation choice. |
| `REG-002` | Register writes and dirty propagation to shader, texture, sampler, and fixed-function consumers are materially equivalent through reorganized code. | Broad execution is **CONFIRMED RELEVANT** from rendered output. A renderer must preserve dependency-level invalidation; container layout is not significant. |

## 4. Draws, extents, predication, and queries

| ID | ReXGlue, Canary, and material result | History and preliminary Fable/renderer result |
|---|---|---|
| `DRW-001` | Both normalize primitive, endian-aware index, extent, predicate, and query state before backend submission. Later special cases are separate records. This is **SAME BEHAVIOUR, DIFFERENT STRUCTURE**. | Geometry in Run 047 makes broad draw execution **CONFIRMED RELEVANT**. Exact topology and predicate use still require G1.5D evidence. |
| `DRW-002` | ReXGlue's active D3D12 path owns one synchronous host ZPD query and may return a fixed fake count. Canary models shared logical reports with segments across passes/submissions, same-slot reuse, asynchronous retirement, D3D12/Vulkan mechanisms, and fast/strict/fake modes. This is **SEMANTICALLY DIFFERENT**. | `CAN-fbd620c2`, `REX-e6407f3a`, `REX-25f2501b`, and `REX-8e6baaec` establish the implementation history; the ReXGlue port origin remains unknown. Fable relevance is **UNKNOWN FOR FABLE II** pending `EVENT_WRITE_ZPD` and report-lifetime evidence. Query behavior should be specified in guest report terms before choosing host mechanisms. |

## 5. Vertex fetch and primitive conversion

| ID | ReXGlue, Canary, and material result | History and preliminary Fable/renderer result |
|---|---|---|
| `VTX-001` | ReXGlue rejects tessellated triangle strips and fans. Canary converts them to triangle lists, creating a runtime conversion buffer when necessary. This is **CANARY-ONLY**, classified **TITLE COMPATIBILITY FIX**. | `CAN-3eab2b8b` gives **CONFIRMED RATIONALE**, but no Fable topology evidence. The shared Fable quad-patch comment concerns a different case. Relevance is **UNKNOWN FOR FABLE II**. |
| `VTX-002` | ReXGlue translators may load complete words beyond the fetch-constant size; Canary returns zero at or beyond the declared size. This is **CANARY-ONLY**, classified **XENOS ACCURACY CORRECTION**. | `CAN-9e9d3cdd` explicitly states hardware behavior. No affected Fable fetch is known. Fetch bounds should be an explicit guest contract, independent of host memory safety. |
| `VTX-003` | ReXGlue labels the `0x7F` region as possible XPS but neither backs it as a physical heap nor wraps GPU L2 fetch/index addresses. Canary backs `0x7F000000..0x7FC7FFFF` and masks affected addresses. | `CAN-22708301` gives **CONFIRMED RATIONALE**. Relevance is **UNKNOWN FOR FABLE II** until an allocation or GPU address reaches that range. XPS responsibilities span runtime memory ownership and rendering. |

## 6. Textures, formats, samplers, and invalidation

| ID | ReXGlue, Canary, and material result | History and preliminary Fable/renderer result |
|---|---|---|
| `TEX-001` | The broad texture-key, layout, tiling, endian, cache, residency, alias, watch, upload, and sampler-binding architecture is materially equivalent through reorganized code. | Correct environment/UI textures make broad use **CONFIRMED RELEVANT**. The dog/skin resources and fetch constants remain unidentified. |
| `TEX-002` | ReXGlue may mark texture data current and install a watch without first proving the backing shared-memory range valid. Canary leaves invalid data outdated for a later reload. | `CAN-9781a75a` gives **CONFIRMED RATIONALE**. Relevance is **UNKNOWN FOR FABLE II**; symptom similarity is not evidence of stale texture state. Addresses, invalidation timing, and later cache state are required. |
| `TEX-003` | ReXGlue has no equivalent of Canary's authoritative per-component integer `num_format` scaling in both translators. Integer samples can therefore differ by format-specific scale factors. | `CAN-d1195052` gives **CONFIRMED RATIONALE**. The black-surface symptom makes format decoding a candidate class only; the exact Fable fetch, format, `num_format`, values, and consumer are required. |
| `TEX-004` | Canary rounds filtered normalized unsigned fixed samples at Q16-sensitive boundaries; ReXGlue does not. Signed and integer fetches are unchanged by this path. | `CAN-0c843efb` gives **CONFIRMED RATIONALE** for non-Fable titles. Fable relevance remains **UNKNOWN FOR FABLE II** pending a rounding-sensitive fetch and comparison. |
| `TEX-005` | ReXGlue can suppress a separately allocated base map when `mip_min_level` is nonzero and fold the base page into the mip page. Canary preserves separate allocation and clamps the base sampler to LOD 0. | `CAN-4a863a0e` gives **CONFIRMED RATIONALE**. No affected Fable fetch constant is known. Allocation identity and LOD policy must remain separate. |
| `TEX-006` | ReXGlue uses a promoted coordinate dimension for affected `tfetch1D`; Canary retains runtime knowledge of the actual one-dimensional layout and limits rows accordingly. | `CAN-7cd47947` gives **CONFIRMED RATIONALE** for other titles. Affected Fable shader and layout evidence is absent. Coordinate semantics and storage dimensionality should be modeled separately. |
| `TEX-007` | ReXGlue can discard an all-literal zero/one swizzle binding. Canary preserves the declared dimensions and literal swizzles through a dummy header. | `CAN-ec5e0f40` gives **CONFIRMED RATIONALE**. Fable relevance is **UNKNOWN FOR FABLE II** until such a fetch constant and its binding-layout use are identified. |

## 7. Render targets, EDRAM, resolves, copies, and clears

| ID | ReXGlue, Canary, and material result | History and preliminary Fable/renderer result |
|---|---|---|
| `RT-001` | Host-RT/interlock paths, tile ownership, overlap transfer, depth/color clears, resolves, and EDRAM alias tracking remain materially equivalent at the architectural level. | Rendered color/depth content makes broad use **CONFIRMED RELEVANT**. Per-pass formats, sample counts, and resolves are needed for the black surfaces. |
| `RT-002` | ReXGlue retains the older sample layout and pair-specific transfers. Canary uses one canonical 4x4-block addressing model for 1x/2x/4x across resolves, clears, transfers, dumps, and interlock paths. | `CAN-437a7280` gives equations and **CONFIRMED RATIONALE**. Fable relevance is **UNKNOWN FOR FABLE II** pending MSAA, alias, pitch/base, and resolve-coordinate evidence. All operations should share one validated EDRAM address model. |
| `RT-003` | Canary scaled-resolve readback uses `ResolveInfo`, written extents, group and committed-range guards, and whole-tile tail rules. ReXGlue uses older range/length handling plus a configurable pre-mask. | `CAN-a635ac64` and `REX-bb4a536c` give **CONFIRMED RATIONALE** for their changes. Fable relevance is **UNKNOWN FOR FABLE II** until a scaled resolve and consumer are identified. |
| `RT-004` | ReXGlue lacks Canary's piecewise-linear decode for full `8_8_8_8_GAMMA` resolves and `copy_dest_number`-dependent fixed packing. Pinned Canary enables the decode unconditionally. | `CAN-d1195052` and `CAN-fc48d37c` give **CONFIRMED RATIONALE**, not Fable reachability. Required evidence is source/destination formats, `copy_dest_number`, and consumer. |
| `RT-005` | ReXGlue follows host float16 behavior in affected paths and retains an extended-range TODO. Canary treats Xenos exponent 31 as finite through 131008 for RT and memexport pack/unpack. | `CAN-3ff230d2` gives **CONFIRMED RATIONALE**. Fable relevance is **UNKNOWN FOR FABLE II** until affected formats and value ranges are shown. Guest numeric formats need explicit bit semantics. |

## 8. Shaders

| ID | ReXGlue, Canary, and material result | History and preliminary Fable/renderer result |
|---|---|---|
| `SHD-001` | Microcode hashing and analysis, control flow, constants, fetches, exports, host translation/compilation, and shader/pipeline caching remain materially equivalent in broad architecture. | Shader execution is **CONFIRMED RELEVANT** from Run 047. The affected character shader identities are still required. |
| `SHD-002` | ReXGlue retains a title-ID-specific quad-domain input workaround. Canary removes that workaround and rounds results of an EXP/LOG/RCP/RSQ/SQRT scalar family to 21 mantissa bits in translators and interpreter. These modify different operations. | `CAN-3a44f20c` gives **CONFIRMED RATIONALE** but explicitly leaves exact Xenos precision and halfway rules uncertain. Named cases are not Fable II; relevance is **UNKNOWN FOR FABLE II**. Neither policy should become Fable behavior without shader/value evidence. |

## 9. Pipeline and state assembly

| ID | ReXGlue, Canary, and material result | History and preliminary Fable/renderer result |
|---|---|---|
| `PIP-001` | Pipeline descriptions, hashes, render/fixed-function inputs, descriptor and root bindings, specialization, cache keys, and invalidation are materially equivalent at broad architectural level. | Pipeline execution is **CONFIRMED RELEVANT**. Cache keys must include every semantic and host-capability input, but no affected Fable key is known. |
| `PIP-002` | ReXGlue may skip the initiating draw, then drains work and waits for creation threads at submission end. Canary leaves creation running across submissions and skips every draw whose pipeline remains unavailable. | Pinned Canary source provides **CONFIRMED RATIONALE** for avoiding frame-time spikes; its origin commit is unavailable in the shallow history. Fable relevance is **UNKNOWN FOR FABLE II** pending the effective async setting and pipeline readiness for affected draws. This performance policy is guest-visible when it skips draws. |
| `PIP-003` | On D3D12 hosts without alpha-factor support, Canary emulates alpha-only constant blend factors through the common factor. ReXGlue has no provider-capability branch and supplies independent blend values directly. | `CAN-4cc584f4` supports **INFERRED RATIONALE** because its body is empty. Host capability and affected Fable blend state are both unknown. Capability-dependent semantics must participate in pipeline behavior and keys. |

## 10. Guest/shared memory and synchronization

| ID | ReXGlue, Canary, and material result | History and preliminary Fable/renderer result |
|---|---|---|
| `MEM-001` | Physical-page validity and watches, upload/download ownership, D3D12 transitions, submissions, fences, and deferred release remain materially equivalent at broad level. | `REX-6124b362` explains ReXGlue's removal of double-buffered validity flags. Broad resource execution is **CONFIRMED RELEVANT**; exact transitions are not implicated. Coherency ownership must cross the plugin boundary explicitly. |
| `MEM-002` | ReXGlue's callback path can return when no watch is armed. Canary also invalidates GPU consumers on unwatched decommit, release, and protect-to-writable changes and validates system-page access. | `CAN-aed81ca9` gives **CONFIRMED RATIONALE**. No Fable resource is tied to this lifecycle, so relevance is **UNKNOWN FOR FABLE II**. Mapping lifecycle invalidation must not depend only on armed write watches. |

## 11. Shared architecture and backend boundaries

| ID | ReXGlue, Canary, and material result | History and preliminary Fable/renderer result |
|---|---|---|
| `BCK-001` | ReXGlue source contains D3D12 and Vulkan, but the verified Fable DLL contains only D3D12. Canary source exposes D3D12, Vulkan, and null factories. The executable comparison is therefore narrower than source inventory. | Active D3D12 identity is **CONFIRMED RELEVANT**. `REX-c22a33e2` explains plugin extraction; exact backend inclusion is artifact evidence and the broader intent is inferred. Vulkan cannot be used to describe the active Fable artifact. |
| `BCK-002` | Both separate common guest-GPU modeling from host backends. ReXGlue adds MoltenVK-specific adaptations and has no Canary null backend; current Fable packaging excludes its Vulkan implementation. | `REX-5f5d7f6f` gives **CONFIRMED RATIONALE** for MoltenVK work. Vulkan/null differences are **NOT APPLICABLE TO FABLE II** at the pinned artifact. No backend expansion or selection follows from this audit. |

## 12. Swap, presentation, frame boundaries, and pacing

| ID | ReXGlue, Canary, and material result | History and preliminary Fable/renderer result |
|---|---|---|
| `PRE-001` | Both route `XE_SWAP` through backend swap and texture-cache output into a mailbox-style presenter, then refresh and present. UI ownership and file structure differ without a material guest-swap delta. | Reachability is **CONFIRMED RELEVANT** through `sub_82BA34D8` and Run 047. The ReXGlue presenter/UI boundary must remain compatible; this equivalence does not implicate presentation in black surfaces. |
| `PRE-002` | ReXGlue has a guest VSync thread derived from video mode and catches up missed intervals. Canary combines title gating, counters, cvars, and sleep/spin host limiting. Timing source, counter, configuration, and catch-up policy differ. | `REX-75e339bd` confirms ReXGlue catch-up intent; the broader comparison has **INFERRED RATIONALE**. The thread runs for Fable, but no current visual symptom is attributed to it. Guest vblank and optional host pacing should remain distinct policies. |

## 13. Diagnostics, fallbacks, configuration, and TODOs

| ID | ReXGlue, Canary, and material result | History and preliminary Fable/renderer result |
|---|---|---|
| `DIA-001` | ReXGlue intentionally removed its partially intact Snappy GPU trace system; Canary retains trace reader/writer/player infrastructure. This is **CANARY-ONLY** host diagnostic capability. | `REX-71782a3b` gives **CONFIRMED RATIONALE**. It is **NOT APPLICABLE TO FABLE II** guest behavior, and this phase added no capture or instrumentation. |
| `DIA-002` | Both contain assertions, unsupported-operation paths, fallbacks, device-loss reporting, and TODOs, but exhaustive semantic comparison of this broad category was not proven. Direction is **INSUFFICIENT EVIDENCE**. | ReXGlue query device-removal history is confirmed by `REX-25f2501b`; a general rationale is **RATIONALE UNKNOWN**. No current first blocker is a GPU device-loss or unsupported-operation diagnostic. Investigation should start only from a specific title failure. |
| `CFG-001` | ReXGlue defaults `anisotropic_override=3` and `clear_memory_page_state=true`; Canary defaults them to `-1` and `false`, and the sets of compatibility/performance/capability controls differ. | Effective defaults make this **PROBABLE RELEVANT**, but Run 047 did not record every effective value. `REX-6124b362` and `REX-bb4a536c` supply partial history; the overall rationale is inferred. Comparisons must pin configuration as well as source. |

## Cross-check summary

The 10 **SAME BEHAVIOUR, DIFFERENT STRUCTURE** records cover PM4 execution,
wait/event/coherency dispatch, dirty propagation, common draw normalization,
the broad texture and EDRAM architectures, broad shader and pipeline assembly,
shared-memory synchronization, and swap/present. Those common areas remain
important, but they do not explain the known Fable visual symptom by
themselves.

The strongest confirmed semantic differences are reset-register defaults;
ZPD report lifetime; vertex bounds and XPS addressing; texture validity,
numeric conversion, base/mip, promoted-1D, and literal-only bindings; canonical
EDRAM addressing and resolve conversion/readback; extended Xenos float16;
scalar approximation handling; asynchronous pipeline completion; constant
alpha fallback; unwatched mapping invalidation; vblank policy; and the ReXGlue
plugin boundary. Their classification and limits are summarized in
[the classification chapter](05-accuracy-performance-architecture-classification.md).
Their primary provenance is in
[the history chapter](04-divergence-history-and-rationale.md).

For G1.5D, the largest evidence gap is title reachability: exact Fable shaders,
fetch constants, texture and render-target formats, pass topology, EDRAM
sample/alias state, query packets, resource lifecycle, pipeline readiness, and
host capability. Until those are tied to a record, the black dog and player
surfaces remain an observation, not evidence for a specific divergence.
