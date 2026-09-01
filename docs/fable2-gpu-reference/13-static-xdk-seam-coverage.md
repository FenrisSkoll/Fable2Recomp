# G1.6B static XDK seam qualification and coverage

## Result

**STATIC COVERAGE NARROW**

`EXP-STATIC-XDK-002` preserves the technical qualification of `SXDK-001` /
`sub_82BA77D0`, but refines its architectural classification to **QUALIFIED
NARROW METHOD**. Exactly two direct calls reach it. One independent confirmed
texture-fetch producer bypasses it in the same lifecycle/present cluster, and
six recovered state-to-draw segments use a separate metadata-driven state
family without calling it. No static chain connects `SXDK-001` to ordinary
title material/mesh rendering broadly enough to support a title-semantic
interception contract.

This is a coverage result, not an implementation authorization. Static
reachability below is not runtime execution or frequency.

The authoritative record is [static XDK seam coverage
v1](evidence/static-xdk-seam-coverage.json), validated by the [versioned
schema](../../tools/schemas/fable2-gpu-static-xdk-seam-coverage-v1.schema.json).

## Starting state and identities

The phase began clean on required branch
`fable2-native-renderer-g1.6a-static-xdk-recovery`, commit
`9af33118bcfbf00f8b446f05e90d18de193410c1`, tree
`fd91d6931e81108d4a619d3875c28b4d66e05187`. The working branch
`fable2-native-renderer-g1.6b-static-seam-coverage` was created directly from
that commit. G1.5D commit
`78c5d66807abf19f67966bd0c3d8301c29990ae4` is an ancestor. Paused G2A commit
`47c2ea2b7d9e14b09fd942c4b5f1bd11c46e2f51` is not an ancestor and was not
copied or otherwise incorporated.

The following identities were independently rechecked before analysis:

| Item | Verified identity |
|---|---|
| TU1 loaded image | SHA-256 `BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00`; base `0x82000000`; size `0x01620000`; entry `0x82CC21C0` |
| ReXGlue | commit `956c6a8b5da4c54b9899a2593e9c67c26de30194`; tree `b78b06b8ac650467372236a3a262864e069a9382` |
| Xenia Canary | commit `3a44f20c7bc66db1da583e8a6f0ab740e31908e9`; tree `c343b0a5796590fadc3b78c993bfada51e7e9148` |
| Active `rexgpu-xenos.dll` | SHA-256 `8232051BED6E5CE99CF37B2EF581C824F58875C140A4D3C75DE14E8A5DF4AA99`; `2770944` bytes; D3D12-only |

ReXGlue retained only the accepted pre-existing
` m thirdparty/libmspack` materialization. Canary was clean. Neither reference
was changed.

## Reading gate and inputs used

All repository instructions were read first. The investigation then read the
complete GPU-reference corpus requested for G1.6B: README, scope/pins,
relevance, boundary/ownership, experiment plan, renderer architecture, G2A
decision, G1.5D and G1.6A completion records, the G1.6A report, open questions,
and all cited boundary/backlog/relevance/G2A/replacement/static-method JSON. It
also read the native-renderer workstream scope, G1 completion and accepted hook
inventory.

The Phase 4 discovery inputs actually used were the discovery-pipeline chapters
01 through 05, 03a, the indirect-function-discovery record, loaded-image
provenance, generated-source provenance, function maps, entrypoint-closure
records, jump-table recovery and accepted TU1/G1 reverse-engineering notes.
The local records were:

| Input | Size | SHA-256 / provenance |
|---|---:|---|
| `tools/fable2-entrypoint-closure-evidence.json` | 4,768 | `10F9411631AE08D653FB1CDCA192E364CF499BB56948A6E72F93384632786CC7` |
| `entrypoint-closure.json` | 341,019,731 | `665CA2AE7ED65632B2E9F368063D3D9EE260E8DEF6F276B455CD62A9F2DCC397` |
| `ghidra-function-map.json` | 96,710,692 | `03516B3A1F33433E493739418C9939D4FF1AEB0989F4ACEF2FD4D8204A077F58` |
| `jump-table-recovery.json` | 81,223,154 | `B1FE26FB9119DAF7E7E0196CBDBA8CCA087BE190BF156FE0B12DF116379ED89A` |
| `generated/default/fable2_recomp.*.cpp` | 293 files | Exact pinned generation described by the committed provenance record |

The pinned ReXGlue and Canary source trees were used only to decode Xenos
packet and fetch-register semantics. Similarity to either reference was never
used as proof of Fable reachability.

## Covered static corpus and blind spots

The generated-source pass parsed 60,425 guest functions and 4,497,828 PPC
instructions. Its union covers 17,989,684 of 18,194,424 executable bytes
(`98.8747101859%`). The accepted closure has 60,662 function ranges whose union
covers 18,069,800 bytes (`99.3150428945%`). The exact executable ranges are
`.text [0x82170000,0x832BABBC)` and `BINK
[0x832BAC00,0x832CA03C)`.

The explicit static blind spots are:

- 124,624 executable bytes outside the closure union and 204,740 outside the
  generated-function union;
- 4,526 accepted-closure indirect sites;
- selector values in two runtime metadata streams;
- payloads submitted by the two recovered indirect-buffer builders
  `sub_822866E0` and `sub_8219CD68`;
- runtime-generated/mutated packet data and all execution frequency.

Those buckets are not treated as zero, as confirmed producers, or as a basis
for a percentage.

The temporary query helper lived only under the pre-verified ignored directory
`out/gpu-evidence-runs/g1.6b-static-seam-coverage`. Git identified the governing
ignore rule as `.gitignore:34:[Oo]ut/`. It was bounded to one small text script
during analysis (1 file, 24,790 bytes) and removed before the final commit; no
temporary output is in the evidence corpus.

## Exhaustive search strategy

The census used independent strategies rather than symbol xrefs alone:

1. exact direct branches, tail branches, thunks and generated call sites for
   `0x82BA77D0`;
2. closure, Ghidra, code-materialization, pointer-run, callback/table and
   jump-table references;
3. whole-generated-corpus Type 3 `PM4_SET_CONSTANT`,
   `PM4_LOAD_ALU_CONSTANT`, `PM4_SET_CONSTANT2`,
   `PM4_SET_SHADER_CONSTANTS`, `PM4_LOAD_CONSTANT_CONTEXT` and
   `PM4_SET_STATE` header construction;
4. Type 0 headers covering Xenos fetch registers `0x4800..0x48FF`, followed by
   descriptor-type decoding;
5. selector arithmetic at every direct call to the shared
   `LOAD_ALU_CONSTANT` helpers;
6. state-to-draw paths and downstream `DRAW_INDX` construction;
7. pinned ReXGlue and Canary consumer semantics as independent semantic
   cross-checks.

False opcode/constant hits were rejected unless both a valid packet header and
a following command-buffer store were present. The scan found no actual
`SET_CONSTANT2`, `SET_SHADER_CONSTANTS` or `LOAD_CONSTANT_CONTEXT` constructor.

## `SXDK-001` reachability

There are exactly two direct call sites and two unique direct callers:

| Caller | Call site | Slot/descriptor evidence |
|---|---|---|
| `sub_82BA7B28` | `0x82BA81CC` | Loop slot in `r30`; six-dword stack descriptor |
| `sub_82BA83C0` | `0x82BA85D8` | Slot zero; descriptor at `r24+0x1C` |

No exact-target thunk, wrapper, tail branch, vtable entry, callback-table entry,
dispatch-table entry, pointer run, generated address materialization or direct
Xbox import was recovered for `0x82BA77D0`.

Two routes expose those callers:

```text
accepted G1 callers
  -> sub_82BA34D8 @ 0x82BA3A98
  -> sub_82BA95E0 @ 0x82BA9670
  -> sub_82BA8EF8 @ 0x82BA95C0
  -> sub_82BA83C0 @ 0x82BA85D8
  -> SXDK-001
```

This route is **CONFIRMED** as a direct static chain and conditionally
reachable. It is not proof that the chain executes at runtime.

```text
accepted G1 callers
  -> sub_82BA34D8 @ 0x82BA3BE4
  -> sub_82BAAA28 @ 0x82BAACC0
  -> sub_82BAA2B8 registers sub_82BA8928
  -> unresolved dispatcher/callback invocation
  -> sub_82BA8928 @ 0x82BA8C78
  -> sub_82BA7B28 @ 0x82BA81CC
  -> SXDK-001
```

The registration exposure is **CONFIRMED**. Later callback invocation,
selection, queue and scheduling are a **BOUNDED INFERENCE**. The four accepted
direct callers of `sub_82BA34D8` remain `sub_82B6F1D0@0x82B6F408`,
`sub_82BA5D08@0x82BA5E0C`, `sub_82B6FA48@0x82B6FB00` and
`sub_82B6EA60@0x82B6EB9C`.

## Texture-fetch producer inventory

The recoverable method-level lower bound is two confirmed texture producers.
Including two metadata-driven methods that can select texture FETCH yields an
upper bound of four for decoded producer methods. Opaque indirect-buffer
contents prevent an absolute whole-image upper bound.

| ID | Method/range | Mechanism | Reachability | Classification |
|---|---|---|---|---|
| `FETCH-SXDK-001` | `sub_82BA77D0 [0x82BA77D0,0x82BA7894)` | Explicit `SET_CONSTANT` FETCH type 1, six dwords | Conditional; two direct callers | **QUALIFIED NARROW METHOD** |
| `FETCH-DIRECT-002` | `sub_82BAC718 [0x82BAC718,0x82BAD028)` | Direct Type 0 texture descriptor at `0x4800`; shader and `DRAW_INDX_2` follow | Conditional through `sub_82BAD028` | **STRONG STATIC CANDIDATE** |
| `FETCH-DYNAMIC-003` | `sub_82221B90 [0x82221B90,0x82221CE8)` | Metadata-driven `LOAD_ALU_CONSTANT` | Two sites in `sub_82221858`; selector type unknown | **UNRESOLVED INDIRECT PRODUCER** |
| `FETCH-DYNAMIC-004` | `sub_8222BFA0 [0x8222BFA0,0x8222C0E4)` | Metadata-driven `LOAD_ALU_CONSTANT` | Three sites in `sub_8221B010`; selector type unknown | **UNRESOLVED INDIRECT PRODUCER** |

`sub_82BAC718` is the decisive same-cluster bypass:
`sub_82BA34D8@0x82BA36CC -> sub_82BAD028@0x82BAD100 ->
sub_82BAC718`. It writes a six-dword Type 0 texture descriptor without calling
`SXDK-001`, loads shader state, and emits `DRAW_INDX_2` at `0x82BACD94`.
Calling this a present/copy/display operation is a **BOUNDED INFERENCE** from
the accepted cluster and state sequence; its public name remains unknown.

Four plausible writers were rejected as texture producers:

- `sub_821EFAC0` and `sub_82206888` emit Type 0 descriptors with low type bits
  3, which the pinned references define as vertex FETCH;
- `sub_82205F68` emits slot-31 entries with types 1, 1 and 3
  (invalid-vertex/vertex), not texture type 2;
- all ten direct calls to `sub_8227D150` resolve to
  `LOAD_ALU_CONSTANT` type 0 rather than texture FETCH type 1.

Three `PM4_SET_STATE` record builders at `0x831BA458`, `0x831BA630` and
`0x831BA810` were not promoted: their opaque payloads are built through a
separate allocator/callback family, no fetch selector was proved, and neither
pinned command processor implements a `SET_STATE` executor. The two indirect
buffer builders remain explicit blind spots rather than producers.

## `SXDK-002` complete bounded contract

`SXDK-002` is `sub_82BA7B28 [0x82BA7B28,0x82BA83C0)`, size `0x898`, 550 PPC
instructions. Its sole direct caller is `SXDK-003` at `0x82BA8C78`. Boundary,
call and use-site evidence agree across trusted pdata, closure and generated
source.

| Input | Recovered meaning | Status |
|---|---|---|
| `r3` | device-state pointer | **CONFIRMED** |
| `r4` | page-relative byte offset, bounded below `0x4000` | **BOUNDED INFERENCE**; exact protocol name unknown |
| `r5` | borrowed pointer to 32-bit guest page/address entries | **CONFIRMED** |
| `r6` | remaining entry count | **CONFIRMED** |
| `r7` | translated resource record `+0x10` dimension bound | **CONFIRMED**; source unit unknown |
| `r8` | translated resource record `+0x14` dimension bound | **CONFIRMED**; source unit unknown |
| `r9`, `r10` | overwritten before use | **CONFIRMED** |
| stack | no arguments | **CONFIRMED** |
| return | void-like; sole caller consumes no value | **CONFIRMED** |

Persistent device state:

| Offset | Access | Meaning/status |
|---|---|---|
| `+0x10`, `+0x20` | read/write | dirty masks, **BOUNDED INFERENCE** |
| `+0x30` | read/write | PM4 cursor, **CONFIRMED** |
| `+0x38` | read | PM4 boundary, **CONFIRMED** |
| `+0x29C0` | read/write | cached flags, **BOUNDED INFERENCE** |
| `+0x3098` | read | four-entry resource array, **BOUNDED INFERENCE** |

The method builds each six-dword descriptor on its own stack and calls
`SXDK-001` synchronously, so the descriptor pointer is no longer required when
that call returns. It also invokes fixed draw-state/draw method
`sub_82BA79D0@0x82BA7F5C`, vertex/draw setup
`sub_82206888@0x82BA8338`, capacity helper
`sub_821E8EC0@0x82BA7E08`, and an order/submission helper
`sub_82BA2748@0x82BA83AC`. No direct Xbox import is present.

It saves, mutates and restores cached state while emitting texture, vertex,
shader and draw work. It runs synchronously on the unknown `SXDK-003` callback
thread; the PM4 consumer is asynchronous. No direct or recovered indirect
recursion exists, but reentrancy safety is **UNKNOWN** because shared device
state is mutated without a proved lock. Guest resource retention, coherency and
retirement remain **UNKNOWN**. Those gaps keep the classification **STRONG
STATIC CANDIDATE**, with narrow copy/scale coverage.

## `SXDK-003` complete bounded contract

`SXDK-003` is `sub_82BA8928 [0x82BA8928,0x82BA8D2C)`, size `0x404`, 257 PPC
instructions. It has no direct caller. `sub_82BAA2B8` materializes its address
at `0x82BAA338/0x82BAA358` and places it at offset `+0x3C` of a 64-byte stack
block whose cleared 60-byte payload begins at `+4`. The block includes device
context at `+0`. A global `0x82000910` object dispatches virtual slot `+0x18`
with `r3=82` and the record pointer. Registration is **CONFIRMED**; copying,
retention, later invocation and thread/queue are **UNKNOWN**.

| Input | Recovered meaning | Status |
|---|---|---|
| `r3` | device-state pointer | **CONFIRMED** |
| `r4` | flags; bit zero selects 1536-byte table reset and early status 0 | **CONFIRMED** |
| `r5` | borrowed 32-bit guest page/address entry array | **CONFIRMED** |
| `r6` | entry count | **CONFIRMED** |
| `r7` | page-relative byte offset, advanced by `0x1000` and wrapped below `0x4000` | **BOUNDED INFERENCE** |
| `r8` | borrowed output pointer | **CONFIRMED** |
| `r9` | output capacity, clamped to 1560 bytes | **CONFIRMED** |
| `r10` | overwritten before use | **CONFIRMED** |
| stack | no arguments | **CONFIRMED** |
| return | exact status `0`, `6` or `7`; enum names unknown | **CONFIRMED** |

It rejects a translated record with nonzero `+0x04` or type/range `+0x08 > 2`
as status 6, and rejects dimensions `+0x10/+0x14` exceeding device
`+0x54B4/+0x54B8` as status 7. Device `+0x5420` is a mode field by bounded
inference. G1.6A recorded the containing table record at `+0x5528`; G1.6B
refines the exact 1536-byte payload start to `+0x5530`. `+0x5B30` is the
table-present flag. This refines field granularity rather than changing the
accepted operation.

The method may update that table through `sub_82BAEA88@0x82BA8AD0`, delegates
the copy/scale sequence to `SXDK-002@0x82BA8C78`, writes at most 1560 output
bytes, and then calls `sub_821D1508@0x82BA8D1C`. The cleanup operation's source
type, transfer semantics and resource retirement are unknown. No recursion was
recovered; reentrancy remains unknown. It therefore remains **STRONG STATIC
CANDIDATE**.

## Descriptor and resource lifetime model

The five lifetimes must not be collapsed:

| Stage | What static evidence proves | What remains unknown |
|---|---|---|
| Borrowed six-dword descriptor | `SXDK-001` synchronously copies it; r5 need not survive return | Source allocator and mutation outside the call |
| Copied PM4 words | Stored in the device buffer; cursor advances; words persist for consumer ownership | Exact submission/overwrite retirement |
| Referenced guest resource | Encoded guest address survives in the packet; `SXDK-001` performs no retain | Resource identity, mapping/coherency lifetime, release-to-fence join |
| ReXGlue/Xenos cache | FETCH writes update register state and dirty texture constants for later binding | Which exact Fable draw consumes them; title invalidation join |
| Submission/retirement | Capacity/order helpers and an asynchronous consumer exist | Exact fence, interrupt, decommit, release and teardown join |

A future forwarding wrapper would need to preserve immediate copy semantics,
the descriptor transformation, cursor/capacity effects, ordering, fetch-slot
replacement, dirty/cache behavior, guest-memory coherency, invalidation and
retirement. The synchronous descriptor copy alone proves none of the deferred
resource obligations.

## Coverage, bypasses and title systems

The exact method accounting is:

- confirmed texture producers: 2;
- metadata-driven texture-capable unresolved producers: 2;
- confirmed producers implemented by `SXDK-001`: 1, with 2 call sites and 2
  unique callers;
- confirmed texture producers bypassing `SXDK-001`: 1;
- rejected vertex/ALU producer-like methods: 4;
- unresolved indirect-buffer builders: 2;
- common state-to-draw roots bypassing `SXDK-001`: 6.

The six bypass roots call `sub_8221B010` and subsequently construct a draw:

| Caller | State call | Draw site |
|---|---|---|
| `sub_8221C3E8` | `0x8221C470` | `0x8221C6B4` |
| `sub_82217DB8` | `0x82217E9C` | `0x8221819C` |
| `sub_82205F68` | `0x82206034` | `0x822062E8` |
| `sub_82207AF8` | `0x82207C68` | `0x82207F20` |
| `sub_8221C898` | `0x8221C984` | `0x8221CBA8` |
| `sub_8221DFC0` | `0x8221E04C` | `0x8221E2FC` |

Calling these general or ordinary draw preparation is a **BOUNDED INFERENCE**
from the common state-to-draw structure. No static evidence identifies these
roots as character, terrain, particles, UI, video, post-processing or shadow.
Every one of those title-system labels remains **UNKNOWN**. Resolve/EDRAM
coverage also remains unknown. The only bounded system connection for the
qualified family is the specialised copy/scale/present cluster.

No relation to the black dog or player-skin defects is established.

## Adjacent method assessment and negative findings

`sub_82BAC718` is a new **STRONG STATIC CANDIDATE**, not a qualified adjacent
method. Its exact texture packet and draw meaning are confirmed, but complete
ABI, persistent-object ownership, thread identity and retirement are not.
Expanding beyond that one-caller bypass would no longer answer the phase's
coverage question, so no wider renderer audit was performed.

Rejected hypotheses:

- `SXDK-001` is not a title-wide binding entry point merely because its contract
  is exact;
- dynamic selector helpers are not confirmed texture producers;
- not every write near `0x4800` is a texture write;
- opaque `SET_STATE` records are not confirmed state restore or fetch packets;
- a stack-local callback record cannot safely be assumed borrowed by a deferred
  dispatcher—copy behavior remains unknown;
- static reachability does not establish runtime frequency or affected-character
  causality.

## Revised boundary and replacement-seam decision

The high-semantic boundary exists but is supplemental and narrow. A design that
made `SXDK-001` the primary title-semantic renderer owner would miss at least
one confirmed texture producer and the recovered common draw-state family.
Consequently G1.6C interception/single-owner contract design is not selected.
`sub_82BA34D8` remains the separate paused G2A mechanism boundary, not evidence
of semantic coverage.

The next selected experiment is `EXP-CONFIG-CAP-001`: obtain the smallest
effective configuration/capability snapshot before designing bounded
draw-decision correlation. Static analysis cannot join the unresolved dynamic
selector records to affected draws or determine which host decisions consume
them. No probes are added here.

## Historical artifact limitation

The following user-confirmed deleted historical files were not searched for,
recreated, recovered or substituted:

- `C:\Dev\Fable2Recomp\fable2-run-047.1.log`
- `C:\Dev\Fable2Recomp\fable2-run-047.log`
- `C:\Dev\Fable2Recomp\fable2-run-048.log`

The aggregate `--verify-artifacts` command may continue to report exactly those
older G1.5D absences. Focused G1.6B evidence verification is independent of
them, and the prior documentation was not weakened.
