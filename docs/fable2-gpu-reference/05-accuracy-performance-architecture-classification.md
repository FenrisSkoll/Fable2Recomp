# Accuracy, performance, and architecture classification

## Interpretation

Classification describes the primary nature of each source-backed divergence;
it does not rank ReXGlue and Canary. A Canary-only accuracy correction may be
irrelevant to Fable II, a ReXGlue-only boundary may be mandatory for this
project, and a performance policy may change guest-visible output. Secondary
categories and the evidence behind every assignment are in
[divergence-matrix.json](evidence/divergence-matrix.json).

The 37 records have these primary categories:

| Primary classification | Count | Record IDs | Preliminary implication |
|---|---:|---|---|
| **XENOS ACCURACY CORRECTION** | 9 | `DRW-002`, `REG-001`, `RT-002`, `RT-003`, `RT-004`, `RT-005`, `TEX-003`, `TEX-004`, `VTX-002` | These are the highest-value hardware-contract candidates, but G1.5D must first show affected Fable packets, state, formats, or shader operations. |
| **TITLE COMPATIBILITY FIX** | 6 | `SHD-002`, `TEX-005`, `TEX-006`, `TEX-007`, `VTX-001`, `VTX-003` | Their motivating titles are generally not Fable II. Treat the underlying behavior as a candidate, never the title workaround as portable policy. |
| **ARCHITECTURE REFACTOR** | 11 | `BND-002`, `CMD-001`, `CMD-002`, `DRW-001`, `MEM-001`, `PIP-001`, `PRE-001`, `REG-002`, `RT-001`, `SHD-001`, `TEX-001` | Ten retain the same broad behavior through different structure; `BND-002` materially changes hosting and ownership. Structure alone does not select a renderer design. |
| **HOST BACKEND/API ADAPTATION** | 2 | `BCK-001`, `BCK-002` | The active artifact is D3D12 only. Vulkan, null, and MoltenVK findings are boundary evidence, not active Fable behavior. |
| **HOST CAPABILITY OR CONFIGURATION PATH** | 3 | `CFG-001`, `PIP-003`, `PRE-002` | Effective cvars, adapter capability, and pacing policy must be pinned before behavior can be compared. |
| **DIAGNOSTIC/ROBUSTNESS CHANGE** | 3 | `DIA-002`, `MEM-002`, `TEX-002` | Stale-state and mapping-lifecycle guards may protect correctness; broad assertions/TODO differences remain insufficiently resolved. |
| **PERFORMANCE OPTIMIZATION** | 1 | `PIP-002` | Async compilation can skip draws, so the performance policy is guest-visible and cannot be adopted without correctness criteria. |
| **REMOVED OR DISABLED BEHAVIOUR** | 1 | `DIA-001` | Trace capture is a host diagnostic difference, not guest behavior or authority to add instrumentation. |
| **REXGLUE-SPECIFIC INTEGRATION** | 1 | `BND-001` | The plugin ABI and lifecycle are mandatory project constraints even though Canary has no equivalent. |

No record has primary category **UNKNOWN**. This does not eliminate uncertainty:
`DIA-002` has **INSUFFICIENT EVIDENCE** direction, 21 records have
**UNKNOWN FOR FABLE II** relevance, and exact hardware fidelity remains open
for several paths.

## Direction and confidence

| Dimension | Counts |
|---|---|
| Direction | 14 **CANARY-ONLY**; 1 **REXGLUE-ONLY**; 11 **SEMANTICALLY DIFFERENT**; 10 **SAME BEHAVIOUR, DIFFERENT STRUCTURE**; 1 **INSUFFICIENT EVIDENCE** |
| Source confidence | 36 **CONFIRMED**; 1 **PROBABLE** |
| Rationale confidence | 23 **CONFIRMED RATIONALE**; 4 **INFERRED RATIONALE**; 9 **NOT APPLICABLE**; 1 **RATIONALE UNKNOWN** |
| Preliminary Fable relevance | 13 **CONFIRMED RELEVANT**; 1 **PROBABLE RELEVANT**; 21 **UNKNOWN FOR FABLE II**; 2 **NOT APPLICABLE TO FABLE II** |

The 13 **CONFIRMED RELEVANT** labels mostly mean that a broad boundary or
pipeline is demonstrably exercised: `BCK-001`, `BND-001`, `BND-002`,
`CMD-001`, `DRW-001`, `MEM-001`, `PIP-001`, `PRE-001`, `PRE-002`, `REG-002`,
`RT-001`, `SHD-001`, and `TEX-001`. They do not assert that a divergence causes
the black-surface symptom. `CFG-001` is **PROBABLE RELEVANT** because the active
DLL consumes some set of configuration values, but the full effective Run 047
snapshot is absent. `BCK-002` and `DIA-001` are **NOT APPLICABLE TO FABLE II**
for the current artifact/scope.

## Consequential accuracy candidates

The following clusters are consequential because they change guest-visible
values, addresses, lifetimes, or whether work executes. Their Fable relevance
is still preliminary.

### State and query lifetime

- `REG-001` changes read-before-write register state from zero to measured
  hardware reset values.
- `DRW-002` changes ZPD from a single synchronous host-query lifetime to a
  segmented logical report that can cross submissions and handle same-slot
  reuse.
- `PIP-002` changes how long draws may be skipped while D3D12 pipeline creation
  remains pending.

G1.5D needs register ordering, `EVENT_WRITE_ZPD` packets/report addresses, and
effective async/pipeline readiness respectively. None is established by the
black surfaces.

### Fetch and texture semantics

- `VTX-002` zeroes vertex words beyond the declared fetch size.
- `TEX-002` keeps invalid backing data outdated instead of marking it current.
- `TEX-003` applies per-component integer `num_format` scales.
- `TEX-004` rounds filtered normalized unsigned-fixed samples.
- `TEX-005` preserves a separate base allocation under nonzero
  `mip_min_level`.
- `TEX-006` retains actual 1D layout for promoted fetch instructions.
- `TEX-007` preserves binding dimensions when swizzles are all literal.

These are plausible classes for a texture/material investigation, but accepted
evidence does not identify the affected dog/player resource, fetch constant,
shader instruction, numeric format, sampler state, or invalidation event.

### Addressing, EDRAM, and numeric conversion

- `VTX-003` supplies XPS backing and L2 wrapping.
- `RT-002` applies one canonical EDRAM sample-addressing scheme everywhere.
- `RT-003` changes scaled-resolve readback extents, interpretation, validity,
  and tails.
- `RT-004` changes gamma resolve and fixed destination packing.
- `RT-005` implements Xenos extended-range float16 pack/unpack semantics.

Required title evidence includes address ranges, RT and resolve formats,
sample counts, bases/pitches, alias state, copy parameters, value ranges, and
downstream consumers. Without it these records remain **UNKNOWN FOR FABLE II**.

### Shader and host-capability semantics

- `SHD-002` replaces a title-specific tessellation workaround with generalized
  scalar rounding, while the pinned commit explicitly says the exact hardware
  model is unconfirmed.
- `PIP-003` changes constant-alpha behavior only on a host without native
  alpha-factor support.

Both require exact Fable shader/state and runtime capability evidence. Neither
is an implementation recommendation.

## Architecturally equivalent areas

The comparison found no material semantic delta at the audited level for:

- ring and PM4 decoding (`CMD-001`) and wait/event/coherency dispatch
  (`CMD-002`);
- ordinary draw normalization (`DRW-001`) and register dirty propagation
  (`REG-002`);
- the broad texture/cache/watch model (`TEX-001`) and broad render-target,
  EDRAM ownership, clear/copy/resolve model (`RT-001`);
- shader analysis, translation, hashes, and caches (`SHD-001`);
- broad pipeline descriptions, bindings, keys, and invalidation (`PIP-001`);
- shared-memory watch/upload/fence/resource lifetime (`MEM-001`); and
- guest swap through mailbox publication and host present (`PRE-001`).

These equivalences are useful decomposition evidence. They do not prove every
packet, register, instruction, format, barrier, or driver path identical, and
they do not require a future renderer to copy either code structure.

## Preliminary renderer constraints, not a design

The audit supports only behavioral constraints:

- satisfy ReXGlue's plugin ABI, callback, interrupt, ownership, presenter, and
  shutdown contract (`BND-001`, `BND-002`, `PRE-001`);
- specify guest-visible state, packet, fetch, numeric-format, EDRAM, query, and
  vblank behavior independently from host API implementation;
- include semantic configuration and host capabilities in validation and cache
  keys where they change output (`CFG-001`, `PIP-003`);
- make memory validity and mapping-lifecycle invalidation explicit
  (`TEX-002`, `MEM-002`); and
- define correctness behavior for asynchronous work before pursuing frame-time
  optimization (`PIP-002`).

This phase does not select D3D12 versus Vulkan, reuse versus replacement,
translation architecture, cache design, or any implementation sequence. Those
choices would be premature before G1.5D maps exact Fable behavior.
