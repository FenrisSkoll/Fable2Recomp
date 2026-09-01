# G1.6A static XDK method recovery

The authoritative machine-readable result is the
[static XDK method inventory](evidence/static-xdk-method-inventory.json),
validated by the
[static XDK method inventory v1 schema](../../tools/schemas/fable2-gpu-static-xdk-method-inventory-v1.schema.json).

## Phase decision: **STATIC SEAM QUALIFIED**

`EXP-STATIC-XDK-001` recovered one representative title-side Xbox D3D method:
`SXDK-001` / `sub_82BA77D0`. It appends one complete six-dword texture fetch
constant to the title's PM4 stream. Its TU1 boundary, ABI, state accesses,
caller/callee relationships, producer/consumer ownership, resource-lifetime
assumption, side effects and narrow coverage are bounded well enough to qualify
it as a future diagnosis or interception boundary.

This proves that the high-semantic static route is viable. It does not prove
that this method covers ordinary material texture binding, the affected
character draws, or title rendering systemically. It authorizes no hook,
wrapper, renderer implementation or runtime experiment.

## Verified starting state and identities

All Git and artifact checks preceded analysis.

| Item | Verified identity |
|---|---|
| Required Fable start | branch `fable2-native-renderer-g1.5-reference`; commit `78c5d66807abf19f67966bd0c3d8301c29990ae4`; tree `e1881f9de89824feb051b58300374c924747605b` |
| G1 accepted base | `c44e8c16f4422f9a828caf30899ac989170b8a8c`, an ancestor of the required start |
| G1.6A working branch | `fable2-native-renderer-g1.6a-static-xdk-recovery`, created directly from the required start |
| Paused G2A | branch `fable2-native-renderer-g2a-forwarding-proof`; commit `47c2ea2b7d9e14b09fd942c4b5f1bd11c46e2f51`; tree `910e80108c2d9e7d8474866506f1c9e23ede601c`; not incorporated |
| TU1 loaded image | base `0x82000000`; size `0x01620000`; entry `0x82CC21C0`; SHA-256 `BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00` |
| TU1 identity | title `0x4D5307F1`; media `0x716F0A0D`; version `0.0.1.26`; fingerprint `5C8B78B84C93028D166E3DF347206E6642BA40BF374AD1AF8D958B2211320357` |
| Base XEX / XEXP | `88C4EF2E18E65409444D1B068EFF921D1F7E180A5AE64EDC64BA6B0872372662` / `046A05693B4DA4437083C784000A850858B3BF992955C7DB30D518FB3E53E41C` |
| ReXGlue | `C:\Dev\rexglue-sdk-v0.10`; commit `956c6a8b5da4c54b9899a2593e9c67c26de30194`; tree `b78b06b8ac650467372236a3a262864e069a9382` |
| Xenia Canary | `C:\Dev\Fable2NativeRendererResearch\xenia-canary`; commit `3a44f20c7bc66db1da583e8a6f0ab740e31908e9`; tree `c343b0a5796590fadc3b78c993bfada51e7e9148` |
| Active GPU plugin | 2,770,944-byte D3D12-only `rexgpu-xenos.dll`; SHA-256 `8232051BED6E5CE99CF37B2EF581C824F58875C140A4D3C75DE14E8A5DF4AA99` |

ReXGlue was read-only with its previously documented
` m thirdparty/libmspack` materialization. Canary was clean. The two active and
packaged plugin copies agreed. No accepted pin or prior evidence record was
replaced.

## Analysis inputs and provenance

The mandatory reading gate covered this corpus completely: `README.md`,
`00-scope-and-pins.md`, chapters 06, 07, 09, 10 and 11,
`open-questions.md`, all four G1.5 completion records, the five required G1.5D
JSON records, and the three required native-renderer records. Phase 4 discovery
pipeline, generated-source provenance, function-map, entrypoint-closure,
jump-table-recovery and accepted TU1 reverse-engineering documentation were
then inventoried and read where they established boundaries, mappings or call
relationships. The exact input list is retained in the inventory's
`analysis_inputs` array.

The static artifacts actually used were:

| Input | Provenance and use |
|---|---|
| `tools/fable2-entrypoint-closure-evidence.json` | 4,768 bytes; SHA-256 `10F9411631AE08D653FB1CDCA192E364CF499BB56948A6E72F93384632786CC7`; exact image and generation contract |
| `entrypoint-closure.json` | 341,019,731 bytes; SHA-256 `665CA2AE7ED65632B2E9F368063D3D9EE260E8DEF6F276B455CD62A9F2DCC397`; 60,662 function ranges and 334,465 direct edges |
| `ghidra-function-map.json` | 96,710,692 bytes; SHA-256 `03516B3A1F33433E493739418C9939D4FF1AEB0989F4ACEF2FD4D8204A077F58`; independent entries, `.pdata` records and references |
| `jump-table-recovery.json` | 81,223,154 bytes; SHA-256 `B1FE26FB9119DAF7E7E0196CBDBA8CCA087BE190BF156FE0B12DF116379ED89A`; indirect-control-flow checks |
| `generated/default/fable2_recomp.*.cpp` | TU1 generated PPC semantics, registers, calls, imports and object offsets; per-file hashes are recorded with each candidate |
| pinned ReXGlue `xenos.h` and `command_processor.cpp` | independent packet opcode, `SET_CONSTANT` type and fetch-layout interpretation |

The ignored analysis root was
`out/analysis/BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00/`.
The phase's one helper was kept under the separately verified ignored and
bounded `out/g1.6a-static-xdk/` directory during analysis. Neither path is
committed. Before staging, that directory contained one 13,258-byte helper and
was removed in full; the pinned `out/analysis/` reports remain ignored and
unchanged.

## Discovery strategy

The search began at the accepted G1 cluster `sub_82B6EA60`, `sub_82B6F6C0`,
`sub_82B6FA48`, `sub_82BA34D8` and the discovery-only lead
`sub_82AAC208`. Exact TU1 `.pdata` ranges were reconciled with Ghidra entries
and generated definitions. Direct edges, address materializations, callback
records, import thunks and packet producers were followed only far enough to
recover semantic operations.

Packet meaning was not inferred from proximity or inherited names. Immediate
fields and payload shape were compared with the pinned ReXGlue decoder. ABI
claims came from entry-register use and every discovered caller; thread and
ownership claims came from synchronous control flow, callback registration,
buffer mutation and the separate asynchronous ReXGlue consumer.

## Candidate inventory

| ID | TU1 boundary | Classification | Bounded role |
|---|---|---|---|
| `SXDK-001` / `sub_82BA77D0` | `[0x82BA77D0,0x82BA7894)`, `0xC4`, 49 PPC instructions | **QUALIFIED REPRESENTATIVE METHOD** | six-dword texture fetch binding |
| `SXDK-002` / `sub_82BA7B28` | `[0x82BA7B28,0x82BA83C0)`, `0x898`, 550 PPC instructions | **STRONG STATIC CANDIDATE** | internal resource copy/scale draw preparation |
| `SXDK-003` / `sub_82BA8928` | `[0x82BA8928,0x82BA8D2C)`, `0x404`, 257 PPC instructions | **STRONG STATIC CANDIDATE** | address-taken wrapper around the copy/scale route |
| `SXDK-004` / `sub_82AAC208` | `[0x82AAC208,0x82AAC54C)`, `0x344`, 209 PPC instructions | **DISCOVERY LEAD ONLY** | suspected queue processing without a proved graphics ABI |
| `SXDK-005` / `sub_82BA34D8` | `[0x82BA34D8,0x82BA3BFC)`, `0x724`, 457 PPC instructions | **REJECTED AS SEMANTIC SEAM** | present/display control after draw semantics are lost |
| `SXDK-006` / `sub_82BA6990` | `[0x82BA6990,0x82BA6C18)`, `0x288`, 162 PPC instructions | **REJECTED AS SEMANTIC SEAM** | device/engine initialization, not a representative render operation |

There are 1 qualified, 2 strong, 1 discovery-only, 2 rejected and 0
recovery-blocked candidates. Each inventory record states evidence, confidence,
missing facts and the minimum evidence needed to change its classification.

## Strongest candidate: `SXDK-001`

### Boundary and source mapping

**CONFIRMED:** trusted TU1 `.pdata` gives
`[0x82BA77D0,0x82BA7894)`, exclusive size `0xC4`. Ghidra independently records
entry `0x82BA77D0` and `.pdata` record `0x82137908`. The 49 PPC instructions map
to `DEFINE_REX_FUNC(sub_82BA77D0, 0x82BA77D0, false)` in
`generated/default/fable2_recomp.110.cpp`, lines 20979-21103. That file is
1,035,313 bytes with SHA-256
`4168294DC783D211919D0D178732E50A8014CF8E750187BF66491437E7473C10`.

### ABI

| Input/output | Meaning | Evidence/confidence |
|---|---|---|
| `r3` | device-state pointer | Reads `+0x30`, `+0x38`, `+0x31AC`; writes `+0x30`. **CONFIRMED** |
| `r4` | texture fetch slot | Multiplied by six and masked into the fetch constant selector. **CONFIRMED** |
| `r5` | borrowed pointer to one six-dword fetch descriptor | Reads offsets `+0x00`, `+0x04`, `+0x08`, `+0x0C`, `+0x10`, `+0x14`; copied before return. **CONFIRMED** |
| `r6`-`r10` | not entry arguments | Each is overwritten before use. **CONFIRMED** |
| stack arguments | none | No caller-provided stack input is read; the `0x70` frame is local. **CONFIRMED** |
| implicit input | `device[0x31AC]` | ORed into the packet header. Its exact source-level field name is **UNKNOWN**. |
| return | void-like | Both callers ignore the incidental final cursor left in `r3`. **CONFIRMED** |

The stable ABI is therefore bounded to `r3`, `r4` and `r5`. A source-level
Xbox D3D method name is not claimed.

### Persistent object and state offsets

| Base/offset | Access | Bounded meaning | Confidence |
|---|---|---|---|
| device `+0x30` | read/write, 32-bit | PM4 write cursor; updated after the last emitted dword | **CONFIRMED** |
| device `+0x38` | read, 32-bit | PM4 capacity boundary used before calling the recovery helper | **CONFIRMED** |
| device `+0x31AC` | read, 32-bit | header mode/predicate bits ORed with `0xC0062D00` | **PROBABLE** role; exact field type unknown |

No allocation, release, reference-count operation, lock, fence or persistent
descriptor ownership mutation occurs in this body.

### Packet, call and import evidence

**CONFIRMED:** the method emits:

- header `0xC0062D00 | device[0x31AC]`;
- selector `0x00010000 | ((slot * 6) & 0x7FF)`;
- six descriptor dwords, with exact address-field normalization in dwords 1
  and 5;
- a final write-cursor update at device `+0x30`.

Pinned ReXGlue independently decodes `SET_CONSTANT` type 1 as `FETCH` and a
texture fetch constant as six dwords. This establishes meaningful texture
resource/sampler state rather than merely a graphics-looking constant.

Direct callers are `sub_82BA7B28` at `0x82BA81CC` and `sub_82BA83C0` at
`0x82BA85D8`. The only direct semantic callee is command-buffer
capacity/advance helper `sub_821E8EC0` at `0x82BA77FC`. `SXDK-001` calls no
Xbox import directly; its semantics are the statically linked packet emission
itself.

An address-taken route is independently visible:

```text
sub_82BAA2B8 materializes 0x82BA8928 at 0x82BAA338
-> callback record
-> sub_82BA8928
-> sub_82BA7B28 at 0x82BA8C78
-> sub_82BA77D0 at 0x82BA81CC
```

The alternate direct route is
`sub_82BA95E0 -> sub_82BA8EF8 -> sub_82BA83C0 -> sub_82BA77D0`.

### Threading, queue ownership, ordering and lifetime

**CONFIRMED:** `SXDK-001` executes synchronously on its caller's thread and
appends one packet immediately. It does not enqueue a title command or hand
work to another thread. One upstream route is an address-taken callback, but
the callback registrar and the exact invoking thread name remain **UNKNOWN**.

The title/XDK caller owns PM4 production and cursor/capacity state. ReXGlue's
Xenos command processor owns asynchronous consumption and applies the fetch
register state. Packet order relative to surrounding shader, draw and restore
packets is externally visible and must remain exact.

`r5` is borrowed and copied synchronously, so a future observer must not retain
it. The referenced guest resource backing the descriptor is not owned here;
its lifetime must remain valid through later GPU consumption. That external
lifetime join is visible as an obligation, but its owner is **UNKNOWN**.

### Retained and lost semantics

Retained at this boundary are the fetch slot, all six texture-fetch words
(therefore address/format/dimension/mip and sampler-like fields), device stream
and ordering. Already lost are the Lionhead resource/material identity, shader
stage and instruction, draw/pass association, allocation/release owner and any
affected-character association.

The operation family is **texture / sampler / resource binding**. It is useful
for both targeted diagnosis and eventual renderer-replacement planning because
it preserves a complete Xbox fetch descriptor before ReXGlue applies it.

Coverage is **narrow but representative**: it covers calls from
`sub_82BA7B28` and `sub_82BA83C0`, which static evidence associates with an
internal copy/scale route. It demonstrably does not cover other
`SET_CONSTANT`/`LOAD` producers, normal binds that bypass these callers,
vertex/shader/RT/EDRAM/draw/query/present operations, or any path not yet
reached from the two direct callers. No title-wide coverage percentage is
claimed.

### Future forwarding obligations

Any later, separately authorized forwarding wrapper would have to preserve:

- original execution exactly once until ownership deliberately changes;
- the header, slot calculation, all six descriptor words and address
  normalization;
- capacity recovery, cursor mutation and ordering relative to neighboring
  packets;
- deferred guest resource lifetime through consumer use;
- borrowed-pointer behavior, without retaining `r5`.

G1.6A implements none of these obligations.

## Other candidates and negative findings

`SXDK-002` has a trusted boundary, exact graph and clear fetch/shader/draw
packet production. It appears to be internal copy/scale draw preparation, but
the exact `r4`/`r5` types, callback thread, helper lifetime effects and wider
coverage remain unresolved. It is therefore strong, not qualified.

`SXDK-003` is a 60-byte callback-record target with a bounded device/flags/input
list/count/page/output/capacity ABI and return codes `0`, `6` and `7`. Its
registrar contract, input/output types, thread and lifetime joins remain
unproved. It is strong, not qualified.

`SXDK-004` (`sub_82AAC208`) retains its accepted discovery-only status. The
static body proves repeated helper calls and an atomic global counter; it does
not prove an Xbox graphics import, device/PM4 object, command schema, producer,
consumer, recursion model or representative operation coverage. The
`ProcessAsyncCommandQueues` resemblance is insufficient to promote it.

`SXDK-005` (`sub_82BA34D8`) directly reaches `VdGetSystemCommandBuffer`,
`VdSwap`, `VdSetDisplayMode`, `VdGetCurrentDisplayInformation` and
`VdPersistDisplay`. This confirms display/present behavior, but shader,
resource, draw and EDRAM semantics have already been lowered or lost. It is a
future G2A mechanism boundary only, not a semantic renderer seam.

`SXDK-006` (`sub_82BA6990`) reaches `VdInitializeEngines`,
`VdSetGraphicsInterruptCallback` and `VdIsHSIOTrainingSucceeded`. It is device
lifecycle/configuration rather than a representative render operation.

No exact static evidence connected any candidate to the black dog or
player-skin surfaces. No public XDK symbol name was recovered. No fully typed
draw, shader, render-target, resolve or EDRAM method was qualified in this
experiment. Those are negative findings, not evidence that such methods are
absent.

## Revised boundary and replacement-seam decision

The preferred future semantic route changes from an unproved category to an
evidence-backed, narrow route: recover individual title/XDK methods that still
carry complete operation descriptors before ReXGlue consumes their PM4.
`SXDK-001` proves feasibility for one texture-fetch operation.

It does not establish a single systemic replacement interface, authorize a
second graphics owner, or change the accepted single-owner ReXGlue model. The
present wrapper remains an independent exact-once mechanism question and gives
no evidence about the affected draw/resource/shader/EDRAM chain.

## Exact next experiment

Select **G1.6B - Static Seam Qualification and Coverage**, experiment
**`EXP-STATIC-XDK-002`**:

1. enumerate every TU1 producer of texture fetch state and every direct or
   indirect caller of `SXDK-001`;
2. recover the public/callback wrapper contracts and resource-lifetime joins
   for the `SXDK-002`/`SXDK-003` route;
3. classify ordinary material/render paths that use or bypass it;
4. quantify coverage without hooks, runtime instrumentation or payload capture.

This is the smallest bounded next step because systemic usefulness, rather
than operation meaning, is now the unresolved static question.
