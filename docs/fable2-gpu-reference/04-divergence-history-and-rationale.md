# Divergence history and rationale

## Evidence model

This chapter records only primary provenance: commits and their parents in the
two pinned repositories, plus one checked-in source comment whose origin commit
is outside the available shallow history. The authoritative records are in
[divergence-history.json](evidence/divergence-history.json); they include full
commit and parent identities, author and timestamp, source locators, affected
divergence IDs, ancestry relationship, rationale text, and explicit limits.

All 29 commit records below are ancestors of the corresponding pinned head.
The Xenia Canary clone is clean and shallow to 200 commits, with boundary
`049a55f03679b204379b17996bd032ce54bff156`. Nothing older than that boundary
is reconstructed from memory. Commit subjects and bodies establish intent only
where they say so; a newer implementation is never treated as intrinsically
more accurate or more suitable for ReXGlue.

Rationale labels mean:

- **CONFIRMED RATIONALE**: an exact commit body/subject or pinned source comment
  explicitly explains the affected behavior.
- **INFERRED RATIONALE**: source and commit identity establish the change, but
  intent is only partially explicit.
- **RATIONALE UNKNOWN**: the available primary provenance does not establish
  why the design was selected.

## Canary history

| History ID and primary source | Date / author | Affected behavior and rationale boundary |
|---|---|---|
| `CAN-fbd620c2` — [`fbd620c22b44638b66a70bba80d6f30d55a10924`](https://github.com/xenia-canary/xenia-canary/commit/fbd620c22b44638b66a70bba80d6f30d55a10924) | 2026-05-01, bomabomabomaboma | `DRW-002`: explicit shared ZPD reports, cross-submission segments, same-slot reuse, asynchronous retirement, backend mechanisms, and fast/strict/fake modes. **CONFIRMED RATIONALE**; configured fake-only ranges remain. |
| `CAN-9781a75a` — [`9781a75a22ba789124d7f34c6bdb4a85c78b2532`](https://github.com/xenia-canary/xenia-canary/commit/9781a75a22ba789124d7f34c6bdb4a85c78b2532) | 2026-06-29, Michael Oliver | `TEX-002`: validity must be proved before texture state becomes current and watched. **CONFIRMED RATIONALE**. |
| `CAN-d1195052` — [`d119505289d540f61ae3d4ba6168f1145625277a`](https://github.com/xenia-canary/xenia-canary/commit/d119505289d540f61ae3d4ba6168f1145625277a) | 2026-06-30, goldislead | `TEX-003`, `RT-004`: CPU-derived integer scaling is called authoritative and its translator ordering is specified; PWL gamma resolve and `copy_dest_number` packing are separately explained. **CONFIRMED RATIONALE**, not proof of Fable use. |
| `CAN-a635ac64` — [`a635ac64f5ca37c0b789e8b4166b53dc673b213f`](https://github.com/xenia-canary/xenia-canary/commit/a635ac64f5ca37c0b789e8b4166b53dc673b213f) | 2026-07-06, goldislead | `RT-003`: explicit scaled-block unpacking, written extent, `ResolveInfo`, containment/alignment checks, and tail truncation. **CONFIRMED RATIONALE**. An Edge approach is credited, but no unrecorded external provenance is claimed here. |
| `CAN-e20f2696` — [`e20f26963fbebd57209b8356ec6da0f27343e333`](https://github.com/xenia-canary/xenia-canary/commit/e20f26963fbebd57209b8356ec6da0f27343e333) | 2026-07-11, SaveEditors | `REG-001`: retail-console reads, AMD/Mesa corroboration, and intentional exclusion of uncertain tessellation factors are explicit. **CONFIRMED RATIONALE**; Fable read-before-write behavior is not. |
| `CAN-aed81ca9` — [`aed81ca93a1f3e8dd043107babd33438379f379d`](https://github.com/xenia-canary/xenia-canary/commit/aed81ca93a1f3e8dd043107babd33438379f379d) | 2026-08-01, goldislead | `MEM-002`: explicit system-page access, unwatched write-fault validation, and invalidation for unwatched mapping lifecycle changes. **CONFIRMED RATIONALE**. The commit says it combines three Edge commits, but their immutable IDs are unavailable locally. |
| `CAN-3ff230d2` — [`3ff230d23be454b39a9a2904ad0d8a5156e3aa10`](https://github.com/xenia-canary/xenia-canary/commit/3ff230d23be454b39a9a2904ad0d8a5156e3aa10) | 2026-08-02, goldislead | `RT-005`: Xenos exponent 31 is described as finite through 131008, correcting host-IEEE clamp and unpack behavior. **CONFIRMED RATIONALE**. |
| `CAN-437a7280` — [`437a7280cf95310d518a2f68087aab61403956ac`](https://github.com/xenia-canary/xenia-canary/commit/437a7280cf95310d518a2f68087aab61403956ac) | 2026-08-07, goldislead | `RT-002`: canonical 1x/2x/4x EDRAM addressing equations explain coordinated changes to resolve, clear, transfer, dump, and interlock paths. **CONFIRMED RATIONALE**; no Fable pass is identified. |
| `CAN-9e9d3cdd` — [`9e9d3cdd3f59ec61afb1115bdd95e3a67e20559e`](https://github.com/xenia-canary/xenia-canary/commit/9e9d3cdd3f59ec61afb1115bdd95e3a67e20559e) | 2026-08-07, goldislead | `VTX-002`: real hardware is stated to return zero at or beyond vertex-fetch size. **CONFIRMED RATIONALE**. |
| `CAN-3eab2b8b` — [`3eab2b8b39442e32537610c955fbb8db0c2a6561`](https://github.com/xenia-canary/xenia-canary/commit/3eab2b8b39442e32537610c955fbb8db0c2a6561) | 2026-08-08, goldislead | `VTX-001`: strips/fans are normalized to lists and conversion buffers are created when needed. **CONFIRMED RATIONALE**; no Fable topology evidence. |
| `CAN-fc48d37c` — [`fc48d37cdc76c21f20b3dbd8b2e15b035139868d`](https://github.com/xenia-canary/xenia-canary/commit/fc48d37cdc76c21f20b3dbd8b2e15b035139868d) | 2026-08-10, bomabomabomaboma | `RT-004`: num-format/decode switches are removed after being judged probably safe/correct, leaving full `8_8_8_8_GAMMA` PWL decode enabled. **CONFIRMED RATIONALE**, with the commit's own probabilistic wording preserved. |
| `CAN-7cd47947` — [`7cd47947b07de30b649fb4224418a659890eab73`](https://github.com/xenia-canary/xenia-canary/commit/7cd47947b07de30b649fb4224418a659890eab73) | 2026-08-13, goldislead | `TEX-006`: runtime selection preserves one title's 2D case while fixing another's wide 1D bindings. **CONFIRMED RATIONALE**; neither title proves Fable relevance. |
| `CAN-4cc584f4` — [`4cc584f47d310c95d3686d8f4c9ffb052ee38fcc`](https://github.com/xenia-canary/xenia-canary/commit/4cc584f47d310c95d3686d8f4c9ffb052ee38fcc) | 2026-08-15, Clippy95 | `PIP-003`: the subject says constant-alpha RTV blending is fixed; the source diff establishes the capability fallback, but the commit has no body. **INFERRED RATIONALE**. |
| `CAN-4a863a0e` — [`4a863a0e1a69c88591b46564e637b9a817c70a9a`](https://github.com/xenia-canary/xenia-canary/commit/4a863a0e1a69c88591b46564e637b9a817c70a9a) | 2026-08-22, goldislead | `TEX-005`: `mip_min_level` is sampler state; separate base allocation is retained and sampled at LOD 0. **CONFIRMED RATIONALE** for a non-Fable regression. |
| `CAN-0c843efb` — [`0c843efb3279341eefe9dcec2a60885fd14937e1`](https://github.com/xenia-canary/xenia-canary/commit/0c843efb3279341eefe9dcec2a60885fd14937e1) | 2026-08-25, goldislead | `TEX-004`: two other titles compare filtered unsigned-fixed samples to Q16, motivating rounding while leaving signed/integer fetches unchanged. **CONFIRMED RATIONALE**, not Fable evidence. |
| `CAN-22708301` — [`22708301ba76d10aae6f7d7caac8b1cac9e4a8e6`](https://github.com/xenia-canary/xenia-canary/commit/22708301ba76d10aae6f7d7caac8b1cac9e4a8e6) | 2026-08-26, goldislead | `VTX-003`: initial XPS support makes `0x7F000000` a physical heap and wraps L2 addresses. **CONFIRMED RATIONALE**; it is the direct parent of the pin and does not prove Fable use. |
| `CAN-ec5e0f40` — [`ec5e0f40e750ff1e8c8634bc9fef2951747648c5`](https://github.com/xenia-canary/xenia-canary/commit/ec5e0f40e750ff1e8c8634bc9fef2951747648c5) | 2026-08-27, goldislead | `TEX-007`: declared dimensions and literal swizzles are preserved for dummy headers. **CONFIRMED RATIONALE**. |
| `CAN-3a44f20c` — [`3a44f20c7bc66db1da583e8a6f0ab740e31908e9`](https://github.com/xenia-canary/xenia-canary/commit/3a44f20c7bc66db1da583e8a6f0ab740e31908e9) | 2026-08-28, goldislead | `SHD-002`: the pinned commit replaces an AC6-specific workaround with 21-mantissa-bit scalar rounding while explicitly leaving exact precision and halfway behavior unconfirmed. **CONFIRMED RATIONALE**, not confirmed hardware accuracy. |
| `CAN-source-async` — [`3a44f20…:PipelineCache::EndSubmission`](https://github.com/xenia-canary/xenia-canary/blob/3a44f20c7bc66db1da583e8a6f0ab740e31908e9/src/xenia/gpu/d3d12/pipeline_cache.cc) | pinned source, goldislead | `PIP-002`: the checked-in comment explicitly says not to wait at submission end so work can continue without frame-time spikes. **CONFIRMED RATIONALE** from immutable source; the exact origin commit is beyond/unidentified in the shallow history. |

## ReXGlue history

| History ID and primary source | Date / author | Affected behavior and rationale boundary |
|---|---|---|
| `REX-e6407f3a` — [`e6407f3a63e532365629ffb3176f863773d885ac`](https://github.com/rexglue/rexglue-sdk/commit/e6407f3a63e532365629ffb3176f863773d885ac) | 2026-03-01, Ryan Fisher | `DRW-002`: the subject says D3D12 backend/runtime changes were ported but identifies neither source revision nor ZPD design intent. **RATIONALE UNKNOWN**. |
| `REX-25f2501b` — [`25f2501b8da9dd2c57dbd93e2c92d9393ab96e19`](https://github.com/rexglue/rexglue-sdk/commit/25f2501b8da9dd2c57dbd93e2c92d9393ab96e19) | 2026-03-01, Tom | `DRW-002`, `DIA-002`: two `EndQuery` operations for one `BeginQuery` caused `DXGI_ERROR_INVALID_CALL`; state-clear ordering was fixed. **CONFIRMED RATIONALE**, but not proof of full ZPD accuracy. |
| `REX-75e339bd` — [`75e339bd338a762a1942fff1593258232ca6dc8f`](https://github.com/rexglue/rexglue-sdk/commit/75e339bd338a762a1942fff1593258232ca6dc8f) | 2026-04-02, Mystixor | `PRE-002`: the source change establishes catch-up pacing for the guest vblank counter. **CONFIRMED RATIONALE** for ReXGlue's change, not for Canary's different limiter ancestry. |
| `REX-bb4a536c` — [`bb4a536c78130175a55ae74e86f4a952071099ae`](https://github.com/rexglue/rexglue-sdk/commit/bb4a536c78130175a55ae74e86f4a952071099ae) | 2026-04-03, Tom | `RT-003`, `CFG-001`: a cvar gates pre-masking of scaled-resolve L2 blocks for an Armored Core For Answer USA issue. **CONFIRMED RATIONALE** for that non-Fable control only. |
| `REX-506eee89` — [`506eee89145340412ce2896aa6092b7f8bff81e6`](https://github.com/rexglue/rexglue-sdk/commit/506eee89145340412ce2896aa6092b7f8bff81e6) | 2026-04-19, Tom | `BND-002`: the subject explicitly records splitting presentation and guest-GPU setup. **CONFIRMED RATIONALE** as architecture, with no guest-visible claim. |
| `REX-55a836fb` — [`55a836fb9a1dc94a0f6b71aeacd6e2c72b3e86f7`](https://github.com/rexglue/rexglue-sdk/commit/55a836fb9a1dc94a0f6b71aeacd6e2c72b3e86f7) | 2026-06-12, Tom | `BND-001`, `BND-002`: kernel and application GPU access is routed through `IGraphicsSystem`. **CONFIRMED RATIONALE** from subject and diff. |
| `REX-c22a33e2` — [`c22a33e2e000128b3f71a1c3148f572a76b48fd4`](https://github.com/rexglue/rexglue-sdk/commit/c22a33e2e000128b3f71a1c3148f572a76b48fd4) | 2026-06-12, Tom | `BND-001`, `BCK-001`: Xenos GPU code is extracted into the runtime-loaded plugin. **CONFIRMED RATIONALE** for integration, with no guest-semantic claim. |
| `REX-8e6baaec` — [`8e6baaecf3298de193f29b3c30cdcfcb80838511`](https://github.com/rexglue/rexglue-sdk/commit/8e6baaecf3298de193f29b3c30cdcfcb80838511) | 2026-08-02, bomabomabomaboma | `DRW-002`: an outdated pairwise ZPD sentinel assumption is changed. **CONFIRMED RATIONALE** for the local test, with no broader report-lifecycle explanation. |
| `REX-71782a3b` — [`71782a3bc15cd1994381757fae7d616242f22e6a`](https://github.com/rexglue/rexglue-sdk/commit/71782a3bc15cd1994381757fae7d616242f22e6a) | 2026-08-04, Tom | `DIA-001`: Snappy and a partially intact GPU trace system with no working viewer are removed; Xenia is named as the capture tool. **CONFIRMED RATIONALE** for diagnostic removal. |
| `REX-6124b362` — [`6124b3629d13a8c5b59c43d1515a19dcb505b9c9`](https://github.com/rexglue/rexglue-sdk/commit/6124b3629d13a8c5b59c43d1515a19dcb505b9c9) | 2026-08-13, Tom | `MEM-001`, `CFG-001`: double-buffered page-valid flags are removed so frame-end refresh is coherent; issue 341 is referenced. **CONFIRMED RATIONALE**. |
| `REX-5f5d7f6f` — [`5f5d7f6fe9ff62c57f1b7d225379b54e485fec2c`](https://github.com/rexglue/rexglue-sdk/commit/5f5d7f6fe9ff62c57f1b7d225379b54e485fec2c) | 2026-08-14, Rien G | `BCK-002`: MoltenVK-specific shader, culling, texture fallback, and packaging changes are explicit. **CONFIRMED RATIONALE**; Vulkan is excluded from the active Fable DLL. |

## Counts and history limits

The history corpus contains 30 records: 19 Canary and 11 ReXGlue; 29 are
commits and one is a pinned source comment. Rationale is **CONFIRMED** for 28,
**INFERRED** for one (`CAN-4cc584f4`), and **UNKNOWN** for one
(`REX-e6407f3a`). The matrix separately marks nine equivalent/no-history
behaviors **NOT APPLICABLE**, because structural movement did not justify an
invented rationale.

The main historical limitations handed forward are:

- the exact source and ancestry of ReXGlue's `REX-e6407f3a` port are unknown;
- the origin commit for Canary's cross-submission async policy cannot be found
  within the shallow boundary, although its current rationale is explicit;
- external Edge commits mentioned by `CAN-aed81ca9` and the Edge approach
  credited by `CAN-a635ac64` were not assigned identities absent local primary
  evidence;
- title names in commit messages explain why a change was made but never prove
  Fable II reaches it; and
- the exact Xenos scalar approximation model remains expressly uncertain in
  the pinned Canary commit.

These gaps do not block a source-backed comparison. They prohibit stronger
claims about origin, hardware truth, or Fable relevance.
