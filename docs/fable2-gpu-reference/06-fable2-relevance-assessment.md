# Fable II relevance assessment

## Decision

G1.5D reaches **L1**, not L2. The exact D3D12 artifact initializes, TU1 has a confirmed swap-command emitter, and Run 047 has presented Fable output. Existing evidence does **not** identify the exact packet/draw/copy/query stream, any affected character draw, or a causal divergence.

The authoritative record is [`fable2-relevance-matrix.json`](evidence/fable2-relevance-matrix.json). It preserves every ReXGlue and Canary source locator from the accepted [G1.5C divergence matrix](evidence/divergence-matrix.json), whose SHA-256 at synthesis was `B4BED324837E092BE29BE91D2C5E55CCA6CEFC9884FAFE150CE04F8F02DC261C`.

## Pins and scope

This assessment uses:

- Fable G1.5C `3cef954120e062974f3fcdf707ac302aa0e2d44e`, tree `e5bcb4029052927c01f0895ac945fb3baa722496`;
- G1 `c44e8c16f4422f9a828caf30899ac989170b8a8c`;
- paused G2A `47c2ea2b7d9e14b09fd942c4b5f1bd11c46e2f51`;
- ReXGlue `956c6a8b5da4c54b9899a2593e9c67c26de30194`;
- Canary `3a44f20c7bc66db1da583e8a6f0ab740e31908e9`;
- D3D12-only `rexgpu-xenos.dll`, 2,770,944 bytes, SHA-256 `8232051BED6E5CE99CF37B2EF581C824F58875C140A4D3C75DE14E8A5DF4AA99`.

No Vulkan conclusion is made. Configuration and host capability remain part of source identity: Run 047/048 identify NVIDIA GeForce RTX 5080, vendor `0x10DE`, device `0x2C02`, and several D3D12 feature tiers, but not every effective GPU CVar or the D3D12 alpha-factor capability used by `PIP-003`.

## Three independent dimensions

Counts are deliberately independent:

| Dimension | Counts |
|---|---|
| Source confidence | 36 CONFIRMED SOURCE; 1 PROBABLE SOURCE |
| Fable reachability | 8 CONFIRMED EXISTING RUNTIME EXECUTION; 1 CONFIRMED TU1 STATIC REACHABILITY; 5 PROBABLE FOR FABLE II; 20 UNKNOWN FOR FABLE II; 1 NOT OBSERVED IN RUN 047/048; 2 NOT APPLICABLE |
| Causal relevance | 0 CAUSALLY CONFIRMED; 0 SUPPORTED CANDIDATE; 19 PLAUSIBLE BUT UNCORRELATED; 8 UNKNOWN; 10 NOT RELEVANT |

The absence of a `SUPPORTED CANDIDATE` row is intentional. The screenshots plus a source difference make several classes plausible, but screenshots contain no draw/resource provenance. Treating that visual symptom as a second causal measurement would silently promote correlation that does not exist.

## Evidence ladder

| Level | Status | Existing proof | Gap |
|---|---|---|---|
| L0 | REACHED | Exact plugin/D3D12/RTX 5080 initialization in Run 047/048. | None for the active artifact. |
| L1 | REACHED | TU1 `sub_82BA34D8` reaches `VdSwap`; Run 047 presents Fable output. | No exact packet/draw/copy/query identity. |
| L2 | NOT REACHED | Source observation points exist. | A source call graph is not a runtime stream. |
| L3 | NOT REACHED | Logs contain uncorrelated shader/pipeline hashes. | Per-draw state, bindings, readiness and terminal outcome. |
| L4 | NOT REACHED | Two images localize black dog and player skin/head surfaces. | Affected draw, shader, texture, EDRAM pass and lifetime identity. |
| L5 | NOT REACHED | No controlled A/B exists. | Exactly one qualified divergent behavior changed under an identical paired checkpoint. |

Run 047 proves that environment, UI, lighting and some clothing render while dog and exposed player skin/head surfaces are black. It does not prove a shader, texture, draw, EDRAM pass, resource-lifetime event or cause. Reaching Bowerstone and presenting frames prove progress and output, not renderer correctness.

## Record-by-record reclassification

`RUNTIME` refers to broad existing path execution only. It does not imply execution of every divergent sub-branch named by the row.

| ID | Source | Fable reachability | Black-surface causality | Minimum linked experiment |
|---|---|---|---|---|
| `BCK-001` | CONFIRMED | RUNTIME | NOT RELEVANT | None |
| `BCK-002` | CONFIRMED | N/A CURRENT | NOT RELEVANT | None |
| `BND-001` | CONFIRMED | RUNTIME | NOT RELEVANT | None |
| `BND-002` | CONFIRMED | RUNTIME | NOT RELEVANT | None |
| `CFG-001` | CONFIRMED | NOT OBSERVED 047/048 | UNKNOWN | `EXP-CONFIG-CAP-001` |
| `CMD-001` | CONFIRMED | TU1 STATIC | NOT RELEVANT | `EXP-DRAW-DECISION-001` |
| `CMD-002` | CONFIRMED | UNKNOWN | NOT RELEVANT | `EXP-DRAW-DECISION-001` |
| `DIA-001` | CONFIRMED | N/A CURRENT | NOT RELEVANT | None |
| `DIA-002` | PROBABLE | UNKNOWN | NOT RELEVANT | None |
| `DRW-001` | CONFIRMED | RUNTIME | UNKNOWN | `EXP-DRAW-DECISION-001` |
| `DRW-002` | CONFIRMED | UNKNOWN | PLAUSIBLE / UNCORRELATED | `EXP-ZPD-REPORT-001`, `EXP-CANDIDATE-AB-001` |
| `MEM-001` | CONFIRMED | PROBABLE | UNKNOWN | `EXP-MEM-LIFECYCLE-001` |
| `MEM-002` | CONFIRMED | UNKNOWN | PLAUSIBLE / UNCORRELATED | `EXP-MEM-LIFECYCLE-001`, `EXP-CANDIDATE-AB-001` |
| `PIP-001` | CONFIRMED | RUNTIME | UNKNOWN | `EXP-DRAW-DECISION-001` |
| `PIP-002` | CONFIRMED | PROBABLE | PLAUSIBLE / UNCORRELATED | `EXP-CONFIG-CAP-001`, `EXP-DRAW-DECISION-001`, `EXP-SHADER-IDENTITY-001`, `EXP-CANDIDATE-AB-001` |
| `PIP-003` | CONFIRMED | UNKNOWN | PLAUSIBLE / UNCORRELATED | `EXP-CONFIG-CAP-001`, `EXP-DRAW-DECISION-001`, `EXP-CANDIDATE-AB-001` |
| `PRE-001` | CONFIRMED | RUNTIME | NOT RELEVANT | `EXP-SWAP-CORRELATION-001` |
| `PRE-002` | CONFIRMED | RUNTIME | NOT RELEVANT | None |
| `REG-001` | CONFIRMED | UNKNOWN | PLAUSIBLE / UNCORRELATED | `EXP-REGISTER-RESET-001`, `EXP-DRAW-DECISION-001`, `EXP-CANDIDATE-AB-001` |
| `REG-002` | CONFIRMED | PROBABLE | UNKNOWN | `EXP-DRAW-DECISION-001` |
| `RT-001` | CONFIRMED | PROBABLE | UNKNOWN | `EXP-EDRAM-RESOLVE-001` |
| `RT-002` | CONFIRMED | UNKNOWN | PLAUSIBLE / UNCORRELATED | `EXP-EDRAM-RESOLVE-001`, `EXP-CANDIDATE-AB-001` |
| `RT-003` | CONFIRMED | UNKNOWN | PLAUSIBLE / UNCORRELATED | `EXP-EDRAM-RESOLVE-001`, `EXP-CANDIDATE-AB-001` |
| `RT-004` | CONFIRMED | UNKNOWN | PLAUSIBLE / UNCORRELATED | `EXP-EDRAM-RESOLVE-001`, `EXP-CANDIDATE-AB-001` |
| `RT-005` | CONFIRMED | UNKNOWN | PLAUSIBLE / UNCORRELATED | `EXP-EDRAM-RESOLVE-001`, `EXP-CANDIDATE-AB-001` |
| `SHD-001` | CONFIRMED | RUNTIME | UNKNOWN | `EXP-SHADER-IDENTITY-001` |
| `SHD-002` | CONFIRMED | UNKNOWN | PLAUSIBLE / UNCORRELATED | `EXP-SHADER-IDENTITY-001`, `EXP-CANDIDATE-AB-001` |
| `TEX-001` | CONFIRMED | PROBABLE | UNKNOWN | `EXP-TEXTURE-METADATA-001` |
| `TEX-002` | CONFIRMED | UNKNOWN | PLAUSIBLE / UNCORRELATED | `EXP-TEXTURE-METADATA-001`, `EXP-CANDIDATE-AB-001` |
| `TEX-003` | CONFIRMED | UNKNOWN | PLAUSIBLE / UNCORRELATED | `EXP-TEXTURE-METADATA-001`, `EXP-CANDIDATE-AB-001` |
| `TEX-004` | CONFIRMED | UNKNOWN | PLAUSIBLE / UNCORRELATED | `EXP-TEXTURE-METADATA-001`, `EXP-CANDIDATE-AB-001` |
| `TEX-005` | CONFIRMED | UNKNOWN | PLAUSIBLE / UNCORRELATED | `EXP-TEXTURE-METADATA-001`, `EXP-CANDIDATE-AB-001` |
| `TEX-006` | CONFIRMED | UNKNOWN | PLAUSIBLE / UNCORRELATED | `EXP-TEXTURE-METADATA-001`, `EXP-CANDIDATE-AB-001` |
| `TEX-007` | CONFIRMED | UNKNOWN | PLAUSIBLE / UNCORRELATED | `EXP-TEXTURE-METADATA-001`, `EXP-CANDIDATE-AB-001` |
| `VTX-001` | CONFIRMED | UNKNOWN | PLAUSIBLE / UNCORRELATED | `EXP-VERTEX-FETCH-001`, `EXP-CANDIDATE-AB-001` |
| `VTX-002` | CONFIRMED | UNKNOWN | PLAUSIBLE / UNCORRELATED | `EXP-VERTEX-FETCH-001`, `EXP-CANDIDATE-AB-001` |
| `VTX-003` | CONFIRMED | UNKNOWN | PLAUSIBLE / UNCORRELATED | `EXP-VERTEX-FETCH-001`, `EXP-CANDIDATE-AB-001` |

## Candidate-cluster findings

### Reset, queries and vertex processing

- `REG-001`: unknown until every Canary-seeded reset register is classified by first read versus first TU1 write and joined to a consuming draw. GPU initialization alone is insufficient.
- `DRW-002`: unknown until `EVENT_WRITE_ZPD` report slots, begin/end sequence, submission spanning, retirement and same-slot reuse are observed. A query result payload is unnecessary.
- `VTX-001` through `VTX-003`: require the actual affected topology/tessellation result, fetch bounds and address class. The existing Fable title-ID quad-patch comment does not prove strip/fan conversion, and no accepted address lies in `0x7F000000..0x7FC7FFFF`.

### Texture and resource lifetime

`TEX-002` through `TEX-007` remain plausible but uncorrelated. The minimum record is per affected draw and binding: shader hash/fetch slot, format, `num_format`, base/mip pages, dimensions, instruction dimension, literal swizzles, sampler/LOD, hashed resource ranges, validity generation and watch/current state. It must not contain pixels or shader bodies.

`MEM-002` is separable: for the same hashed ranges, record only mapping operation, watch state, callback result, validity generation and next cache consumer. Source confirms a divergent invalidation gate; it does not prove an affected Fable mapping lifecycle.

### EDRAM and resolve

`RT-002` through `RT-005` require pass IDs, EDRAM bases/pitches, MSAA, aliases, resolve coordinates, `ResolveInfo`, source/destination formats, `copy_dest_number`, scale, written range, consumer, and only classified value ranges for extended float16. No surface payload is required. Rendered scene color/depth proves broad RT use, not these exact branches.

### Shader and pipeline

- `SHD-002`: the named non-Fable title fixes do not establish TU1 relevance. A Fable shader hash plus scalar operation-class flags and precision-sensitive value classification is the minimum; the hardware precision model remains open.
- `PIP-002`: Run logs show many pipeline hashes and host threads, but not the effective `async_shader_compilation` setting, readiness at an affected draw, its exact skip outcome, or readiness by `EndSubmission`.
- `PIP-003`: the RTX 5080 adapter is confirmed, but alpha-factor support is not logged. Applicability requires that capability plus the affected `RB_BLENDCONTROL`, `RB_BLEND_ALPHA` and color values.

### Configuration

For `CFG-001`, source defaults are not an effective run snapshot. Existing logs recover the active DLL, backend, adapter and reported D3D12 features only. A future one-shot record must include effective `anisotropic_override`, `clear_memory_page_state`, `async_shader_compilation`, draw-resolution/ROV selection, present/vsync mode and alpha-factor capability.

## Evidence priority

The first decision-unlocking step is static, not a broad capture: [`EXP-STATIC-XDK-001`](evidence/experiment-backlog.json) tests whether representative TU1 draw/resource/shader/target methods can retain title semantics. If runtime evidence is later authorized, the smallest useful low-level chain begins with one terminal record at `D3D12CommandProcessor::IssueDraw`, then attaches only shader/pipeline identities and the specific texture or EDRAM metadata selected by that draw.

Ranking by upstream fix count is rejected. Collection cost and discrimination favor the draw-decision join, then the smallest candidate-specific metadata record.
