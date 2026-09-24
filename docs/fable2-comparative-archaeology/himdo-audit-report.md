# Pinned comparative archaeology audit

## Result and scope

**COMPARATIVE AUDIT COMPLETE.** The highest-value result is **VERIFIED CONSISTENT**
codegen/runtime image provenance for the canonical installed SDK and inputs.
Three useful contextual knowledge groups were independently established or
refined: Lua registration, gated keyed lookup fields, and presentation-interval
flow. Four story-labelled functions reduce to already represented virtual-slot
thunks. No new callable function, ownership closure, canonical function name,
prototype identity, renderer fix, or save-format change is accepted.

The external work provides useful practical coverage and diagnostic ideas.
Much overlaps existing discovery, allocator, rendering and input work. Its
campaign-completion claim exceeds our documented gameplay coverage, but is an
author report without a pinned completion trace/save in this audit. Runtime
progress with enabled overrides is not evidence of vanilla parity.

The audit changed only this comparison area, isolated validation tools and their
tests. No external implementation was copied. No guest code ran for the new
probe; no autonomous gameplay or external build was attempted. Full historical
test discovery fails its frozen branch/source contracts; the current subset,
closure validator, provenance check and normal build pass. Those limits are
recorded explicitly below, not hidden by weakening tests.

## Repository identity and initial reading

| Repository | Starting branch | HEAD | Tree |
| --- | --- | --- | --- |
| Fable2Recomp | `main` | `a87f6e549f157e1eacfcc7fa1d41049c6c23e88a` | `f22f8610b7560fe6a23cea39ebfdceed2c827935` |
| SDK | `fable2-native-renderer-nr0c2b1gv-validation-closeout` | `18130a95c7790b4a9d3a2b30f601f247b1a7a864` | `c659bfaf3ff8fb32f5a17774ecabc6a9aa508544` |

Fable started clean. SDK had only the existing `thirdparty/libmspack` dirty
submodule: HEAD `305907723a4e7ab2018e58040059ffb5e77db837`, fifteen materialized
files. [Starting state](evidence/starting-state.json) retains every dirty-file
hash and all configured remotes. None was reset, stashed, discarded or absorbed.

The read-only external clone is `C:\Dev\comparison\himdo-Fable-2-Recomp`,
branch `master`, commit `2bdf8f93a0edcec599023ce9382ca284a7e92c06`, tree
`d6fc3b0dc98033c706fbc857f7b50936adb3880c`. Its 58-commit history was inspected
selectively for naming/build evolution. No commit, edit or remote configuration
was made inside it. All external references below mean this pin, not current
GitHub HEAD. [Source hashes](evidence/external-source-pins.json) bind the principal
files inspected.

Canonical reading preceded external evaluation: README/current status;
prototype phase 1/2A results and 2B–2I reports, particularly reserved identities,
reviewed semantics and frozen witnesses; discovery phases 1–5A, jump-table
regression closure and ownership ledgers; native save parity; fault-walker and
performance reports; GPU/Xenia reference architecture, NR0A, NR0B-1 closeout and
NR0B-2 handoff; migration history. SDK reading covered README, fault walking,
GPU configuration/metadata contracts and the relevant loader/codegen/GPU
implementation. These are evidence at their own phase pins, not assertions that
every old report describes the present checkout.

Current application CMake requires installed SDK `0.10.0.51-dev.gfc5a00b`, commit
`fc5a00b31f702e82377aa1010395af7ba8cff4f7`. The SDK source checkout is newer.
It was neither rebuilt nor substituted for the installed runtime. Relevant
loader/codegen and graphics-system source files are unchanged between these
pins; command_processor.cpp has twenty later metadata lines. Architectural
claims about the installed build use the installed pin, not its branch name.

## Method and evidence limits

External source/report → own base bytes where identity permits → TU1 candidate
→ own control/data-flow inspection → existing evidence comparison. Full-image
hashes precede all binary comparisons. `.pdata` defines the primary bounded
candidate population; absence from `.pdata` does not imply absence of code.
Exact/branch-masked body fingerprints only narrow candidates. Reviewed Lua,
gate, timing and thunk results add control/data-flow evidence. No prototype
semantic gate is relaxed.

The census covers every external manifest entry and explicit size, all switch
hints, and all requested architectural categories. It does not pretend to
recover semantics for 4,970 names or semantically rebase every switch. Residual
leads remain explicit. External generated C++, runtime captures and the exact
tools involved in the reported byte mismatch were not available in the clone.
Their historical mismatch cannot be diagnosed conclusively from prose.

## Revision comparison

| Input | Identity |
| --- | --- |
| External README ISO | SHA-256 `685a0d3bea9718812f17bcd155907a5359a548b6d3d8342dd2a6c944f45e35ff`; ISO identity, not XEX identity |
| External expected XEX / our base | 21,217,280 bytes; `88C4EF2E18E65409444D1B068EFF921D1F7E180A5AE64EDC64BA6B0872372662` |
| Our TU1 delta | 2,992,128 bytes; `046A05693B4DA4437083C784000A850858B3BF992955C7DB30D518FB3E53E41C` |
| Own base loaded image | `B8F294DDAE3DA4A01DE455F5003CD1452D7C838EDC3DE1C166F3CAB9008B77A8` |
| Own patched loaded image | `BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00` |

The external manifest describes unpatched code; `$SystemUpdate` is not proof of
the title delta being active. Its setjmp/longjmp addresses are `0x83000200` /
`0x82CA9260`, versus canonical TU1 `0x83006C90` / `0x82CAFA30`. Shared base XEX
identity does not make guest addresses interchangeable after TU1 patching.
External startup verification caches successful XEX validation using size and
mtime; it does not establish codegen/runtime/tool/patch identity as a set.

## External architecture inventory

**Foundation/build.** ReXGlue v0.10.0; source SDK setup pins official
`f5337cdc947ff6d4c4196737e2c807a48f2a1fc2`. CMake drives codegen and generated
C++ translation units; README reports approximately 60,462 functions / 291
units, not independently countable from ignored generated output. Application
links prebuilt imports. An alternate source-built runtime/plugin supports
D3D12 and experimental Vulkan; `tools/fable2.cmd` copies matching DLLs into
place. SDK modifications are carried as local patch/build machinery, including
renderer diagnostics and API adjustments. The tracked patch is evidence of
source edits, not of which DLL a particular user ran.

**Function coverage.** The pinned manifest has **4,970 named entries**, **86
explicit sizes**, **7 mid-asm hooks**, and **846 manual switch hints** imported
from XenonAnalyse. `FUNCTION_NAMES.md` still says 520. Naming combines
disassembly/import/shape analysis and observed gameplay triggers; 2,624 names
start `ProcessAndProcess`. Other automatically discovered entries remain
address-based generated functions. Explicit ranges include build-driven
overlap trimming (for example `0x82BE9668`, `0x82C89840`, `0x82C898B8`,
`0x82C8D3F0`). Those comments are not independent boundary proofs. Invalid
instruction regions and manual table labels are additional discovery inputs.
No equivalent to our finite-domain, owner, rejected-candidate and corroboration
ledger was found. This does not imply every external boundary is wrong.

**Behavior changes.** `fable2_hooks.cpp` changes the FPS register at
`0x82B9C8E8`; website gates at `0x8256E384`, `0x8256E3AC`; CE gates at
`0x824B3540`, `0x824B3568`; grant/availability results at `0x8256D9E4`,
`0x824ACAE0`. FPS and both content-unlock options default true. Runtime image
patches distinguish data writes from inert `.text` writes in a static recomp.
CMake also invokes a generated-source text patcher, but **its current `PATCHES`
list is empty**. Diagnostic strong wrappers mostly forward, while optional
modes suppress calls, replace strings or rewrite heap data. F5 executes guest
Lua through a captured callable. These are different mechanisms and cannot all
be called observational tracing. Save roots are managed near the executable;
there is no independently demonstrated save-format interoperability fix.

**Rendering.** Stock/prebuilt Xenos D3D12 and an alternate source runtime/plugin;
Vulkan smoke test and game experiments, not demonstrated completed Vulkan
support. The SDK patch contains gamma staging/readback diagnostics, a proposed
host-visible/device-local coherency explanation, waits, sentinel writes,
detached diagnostic work and deliberately retained temporary resources. These
need isolation and measurements before any correctness conclusion. Shader/
pipeline diagnostics identify investigation points, not a proven translation
fix. Higher resolution, widescreen, improved graphics and hero/dog texture
repair remain unfinished/proposed. Window sizing is not internal resolution.
No reproducible, hardware-matched performance comparison is available.

**Input.** SDL gamepad plus custom keyboard driver with OR-merged buttons,
mouse deltas converted to right-stick deflection, configurable mappings and
local TCP port 8791 for timed input. Draw counters and a button latch infer
menu state; they do not recover an authoritative guest state machine. Canonical
ReXGlue already supplies gamepad/MNK facilities and our deterministic bring-up
automation. Keyboard-specific in-game prompts remain unfinished externally.

**Diagnostics.** Thread/function traces, run-length summaries, periodically
sorted call counts, FPS probes, state/list/heap/font/glyph/text probes, allocation
watches, Lua invocation and automated input. Some are passive, some alter data
or returns, and frequent atomic checks/logging can perturb timing. Canonical
coverage, fault walking, PDB mappings, save traces, effective GPU configuration
and bounded metadata recording already cover much of the need. Bounded whole-
call frequency summaries are a distinct potential addition, only for a specific
question. A live Lua console is a controlled experiment, not a read-only probe.

**Other systems.** Story annotations mention loading, warehouse/child combat,
swimming, jobs, ranged aiming and later Spire progression, usually attached to
generic thunks. No verified hero/dog structure layout, quest state machine,
world-transition invariant, physics/animation timing contract or audio fix was
found. The sample Lua script accesses hero position through an existing guest
API, not a recovered native entity layout. CE/website patches expose gate
mechanics but do not establish entitlement ownership, DLC correctness or
persistence semantics. Menu crash notes expose allocator/error-reporting risks,
not an unsolved canonical kernel requirement.

## Names, control flow and prototype comparison

### Lua: accepted registration relationship, reserved function names

External `LuaBind_RunScript_82806168` has a unique branch-normalized candidate
at TU1 `[0x8254B670,0x8254B6EC)`. Independent TU1 registration code at
`0x8245BA1C..0x8245BA78` constructs an eight-byte callable payload: self at
`+0`, method **`0x82459928`** at `+4`; creates a closure with adapter
**`0x8254B670`** and one captured value; then registers using literal
**`RunScript` at `0x820B7424`**. Helper `0x8219AA80` stores the callback in the
closure and copies captured values; `0x82A246C8` constructs the string key and
sets a table value. The adapter reads the payload and calls its method at
`0x8254B6C4`, passing self and converted string argument. Seven code references
reuse this adapter, so its unique `RunScript` name is too specific.

The corresponding base registration at `0x825AFC34/0x825AFC40` materializes
**`0x825ADB40`** (`lis 0x825B`, signed low `0xDB40`), not `0x825BDB40`.
The external manifest calls this `LuaScriptError_FormatMessage_825ADB40`.
TU1 method `[0x82459928,0x82459A98)` does contain Lua error-string construction,
but its explicit registration makes “only an error formatter” too narrow.
We accept the `RunScript`-associated method/adapter relationship, not a recovered
original C++ class name, a complete interpreter contract or safe host invocation.
No default prototype correspondence for this pair was found in the 2A accepted
records; this finding neither creates a donor mapping nor unblocks a phase gate.

### Gated keyed lookup: mechanics confirmed, content role reserved

Base `[0x8256E368,0x8256E4F4)` exactly matches TU1
`[0x8253B058,0x8253B1E4)`: nullable object, byte `+0x90` bit 6, **halfword**
`+0x40` bit 0; key `0xF0` selected via optional `+0x8C` lookup or search of
eight-byte entries described by `+0x48/+0x4C`. Callback comes from incoming
`r3+8` and executes at `0x8253B1BC`. This is not sufficient evidence of a
particular class vtable, chest owner, or entitlement source.

Base `[0x824B3528,0x824B36A0)` exactly matches TU1
`[0x824EDBB0,0x824EDD28)`: byte `+0x90` bit 6, **word** `+0x28` bit 25,
key `0x39`. Distinct field widths matter. The external website/CE labels remain
external hypotheses; the flag/search mechanics are confirmed. Prototype 2A
already maps donor `0x8253C4F0` and `0x824EF888` to these respective TU1 bodies,
without assigning those content names.

### Generic thunks and UI queue

Own base/TU1 executable scans yield exact unique 16-byte matches:

| External name/address | TU1 | Independently established role |
| --- | --- | --- |
| Warehouse `0x8274B738` | `0x82967540` | r3 object, virtual slot 38 |
| Swimming `0x8297EB28` | `0x82964800` | r3 object, slot 23 |
| First child combat `0x8297EB48` | `0x82964820` | r3 object, slot 25 |
| Ranged aiming `0x82988EE8` | `0x82967570` | r4 object, slot 23 |

All are already represented. These instructions establish dispatch structure,
not exclusive story semantics. Observing a generic thunk during swimming does
not establish a swimming implementation.

External `UIText_FrameRenderIter` `0x82190760` corresponds to TU1
`[0x82190728,0x821907F8)`: queue/callback iteration with `+0x18` flag and
`+0x108/+0x10C/+0x110` array fields. Its call at `0x821907A4` already has canonical
harvest evidence to `0x82C03B28`; prototype donor `0x821903F0` is already accepted.
The body alone does not prove text specificity. Prompt/render-element candidates
`0x82C4B118` / `0x82C4AF78` remain follow-ups, not names to import.

### Coverage and ownership

The exhaustive census finds 240 names with raw-body candidates, 1,464 with
branch-masked candidates, 1,915 unmatched `.pdata` bodies and 1,351 without a
`.pdata` start. **1,368** have reciprocal-unique body candidates, all already
registered in canonical output. These categories do not count newly recovered
functions. Canonical has 81 explicit overrides,
60,918 registrations and 60,662 closure function ranges: different populations.
Raw address overlap is only 162 external manifest starts; subtracting these
revision-dependent sets would give a meaningless coverage comparison.

Every external explicit size is preserved in the boundary inventory with own
base `.pdata` comparison and same-address TU1 context. No boundary is imported.
Only one of the 86 sizes starts at an own-base `.pdata` entry; it disagrees:
external `0x82BE9680` size `0x08BC` ends at `0x82BE9F3C`, while `.pdata` gives
`0x0BF0`, ending `0x82BEA270`. Independently decoded branch `0x82BE9F38` reaches
shared epilogue `0x82BEA25C`, beyond the external range. This confirms the supplied
range is not a closed body, not how unavailable external generated output treats
it. TU1 `0x82BEFC68` remains only a similarity candidate. The other 85 missing
`.pdata` starts need separate boundary evidence; they are not automatically wrong.

Switch-hint comments call the supplied address a `bctr`; own base bytes at
`0x821775DC`, for example, begin pointer materialization, with actual `bctr` at
`0x821775F0`. A bounded 32-byte check finds one `bctr` for 720/846 hints; 707
have relative case-layout candidates among our already recovered tables.
Relative shape does not establish table contents, finite index domain or owner.
126 hints need a broader dispatch decode; 139 have no recovered relative-shape
candidate under this method. Neither number means missing TU1 functions.

Current jump report: **878 tables**, **711 unresolved non-link CTR records at
710 distinct addresses** (`0x8305DA44` is represented twice). Unique body
projections of external named owners close none of these; there is no verified
new ownership result. Existing 42 internal continuations, 114 cases, Phase 5A
155 reviewed rejections and accepted thunk `0x825E28B0` remain unchanged.
The restored `0x821746BC`/`0x82174734` case is already solved, not a new lead.

Prototype default 15,299 correspondences and opt-in 15,379-pair overlay retain
their distinct contracts. No external name changes Packet A HammerCombat
exclusion, Packet B oxygen reservation, or Packet C contextual materializer
role at `0x82522C10` (scalar fields via `0x823BF820`, Boolean via `0x82310290`,
handle resolver `0x821B24F8`). The six inherited witness/gate blockers remain;
in particular the missing historical `fable2_recomp.136.cpp` hash is not
reconstructed from current generated output. There is no demonstrated
contradiction of accepted canonical archaeology.

## Rendering and timing evidence

The external FPS patch points to a real constant but overstates what changing
it proves. Candidate base owner `0x82B9C7F8` rebases to TU1
`[0x82BA2F68,0x82BA3144)`. At `0x82BA3058` it selects 2, shifts it into packed
bits starting at 8, and passes the value in r7 to `0x821F6050`, with callback
`0x82BA2DB8`. The callback extracts four bits at `0x82BA2E00` and advances device
field `+0x40AC` at `0x82BA2E6C/0x82BA2ED8`. This independently supports a
presentation interval. It does not prove all animation/physics/UI/audio/
streaming/scheduler consumers remain correct at altered cadence.

External `MainRenderLoop_82B9CD68` maps provisionally to already documented G1
`0x82BA34D8..0x82BA3BFC`; wait helper `0x82242628` maps to `0x82242668`.
Vblank-related base candidates `0x82B9B8D8` / `0x82B9BA58` correspond to
`0x82BA26B0` / `0x82BA2830`. Our existing boundary interpretation is more
limited than “main game loop.” Entry frequency is not a frame rate.

Installed SDK `GraphicsSystem` uses guest refresh-rate cadence with `vsync`
enabled, and `max(1, guest_tick_frequency/1000)` otherwise, advancing its vblank
counter through `MarkVblank`. This is a guest-visible timing change; it is not
just host swap-chain pacing. It does not guarantee a measured 1,000 Hz wall-clock
rate. `WAIT_REG_MEM` still evaluates its condition; changing yield/sleep behavior
is not proof that waits can be skipped. Neither the r11 override, a one-unit-
early wait, nor doubling guest vblank is accepted as a correctness fix.

Both projects report hero/dog surface defects. Canonical D3D12 RTV, bindless/
tiled 1× configuration is validated on RTX 5080; the external gamma/Vulkan
experiments do not establish their cause. Shader, MSAA, texture morphing,
resolution and widescreen proposals require separate evidence. No renderer
workload or replacement backend was implemented by this audit.

## XEX/codegen provenance investigation

The external report asserts generated word `0xD9009510` versus runtime
`0xD8089510` at base `0x8233AEB4`, also mentioning `0x8233AE54/0x8233AE98`.
Its register/displacement decodes are incorrect: `0xD8089510` is
`stfd f0,-27376(r8)`; `0xD9009510` selects f8/r0 with the same signed offset.
Our independently loaded base words are `0x48967D85`, `0xD8099518`,
`0xD8089510` at those three respective locations. The corresponding raw TU1
addresses contain unrelated instructions. The original external producing
tool, generated files and live capture are missing; enum-layout or decompression
causation remains **UNVERIFIED**.

Our pipeline was tested directly:

1. Both configured input roots have identical intended XEX and XEXP hashes.
2. Codegen creates a tool-mode Runtime and calls `LoadXexImage`; `UserModule`
   resolves sibling `path + "p"`, applies the delta, then completes loading.
   `BinaryView::fromModule` copies the loaded sections. Runtime uses the same
   loader. Encryption/decompression were exercised by loading the actual inputs,
   rather than reimplemented in an audit parser.
3. A new isolated probe uses public runtime APIs in tool and ordinary runtime
   modes, with separate user/cache/metadata directories. It loads only. Both
   complete contiguous images are **23,199,744 bytes**, base `0x82000000`, entry
   `0x82CC21C0`, SHA-256 **`BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00`**.
   Sections and header layout match. `be<encryption>` and `be<compression>` are
   two bytes each; compression-info offset is 8 in this build.
4. Actual loaded probe runtime, installed runtime and normal staged runtime DLL
   all hash **`71BB1BA29413773226245B1D05F40379561C974F8E2EA4E5BB994D6DC3591793`**.
   Installed CLI identity is in the receipt. No inference from DLL filename alone.
5. A fresh isolated codegen, preserving the canonical partition and all options
   except absolute input/output paths, reproduces **all 591 C++/header files
   byte-for-byte**, including matching file census. Normal `fable2-build` then
   reports zero generated writes / 593 unchanged artifacts and succeeds.
6. Independent canonical Ghidra exports match `.text`, `BINK`, `.pdata` and
   eleven other sections. `.rdata` differs in exactly 50 bytes across 13 import
   slots: encoded variable-import ordinals become runtime guest pointers during
   `SetupLibraryImports`. This expected pre-/post-import-resolution difference
   is recorded, not silently ignored or mistaken for a code mismatch.

Executable section SHA-256 values:

| Range | Hash |
| --- | --- |
| `.text` `[0x82170000,0x832BABBC)` | `1B9F2E80280637FE2287286ED3FE18B367F378E24A695A2B8AB50B9ACD8FC724` |
| `BINK` `[0x832BAC00,0x832CA03C)` | `D715B7B4F3E7912489DBBBA3FF2642B1907479CBEDBDF974CD043827DB707146` |

**VERIFIED CONSISTENT** applies to these pinned inputs, installed binaries,
fresh loads and generation. It is not proof of translation correctness, arbitrary
future incremental builds, or image immutability after guest execution. The
verifier hashes recorded module paths immediately after the experiment; it is
not a process-memory attestation against concurrent DLL replacement.

One concrete remaining prerequisite: generated `codegen.d` lists the base XEX
and manifest but omits sibling XEXP. Current freshness is proved by isolated
regeneration; future title-delta-only invalidation needs a dedicated regression
and dependency-key review. We did not alter SDK build behavior speculatively.

## Accepted knowledge, exclusions and follow-ups

Accepted here: contextual `RunScript` registration/self-method layout, exact
gated lookup fields/control flow, presentation-interval packing, structurally
confirmed thunk rebases, and load/generation provenance. Existing names,
ownership and prototype artifacts remain intact. These are metadata/documentation
results, not new runtime capabilities.

Rejected: all seven register/result overrides, wait/branch bypasses, instruction
NOPs as recomp fixes, post-codegen patch architecture, semantic diagnostic
wrappers, guessed content/state gates, allocator-success fabrication and
unproven renderer changes. The [risk register](architectural-risk-register.md)
records why each can aid short-term experiments and why it cannot define parity.

Follow-ups are grouped by [objective category](follow-ups.md): correctness
prerequisites, coverage improvement, renderer investigation, tooling enhancement
and later quality-of-life work. External functionality and its evidence limits
are compared in the [feature matrix](feature-comparison.md).

## Validation

Exact commands, outputs and scope are retained in [validation.json](evidence/validation.json).

| Check | Result |
| --- | --- |
| Standard `python -B -X utf8 -m unittest discover -s tests -v` | **FAIL**: final run 449 tests, 11 errors from historical source/branch/SDK guards (initial run before the four additions: 445 tests, same 11 errors). No assertion failure is hidden as PASS. |
| All top-level tests plus Phase 2I (explicit current subset, including four new negative controls) | **PASS**: 350 tests. This is not the complete frozen historical suite. |
| `python -B -X utf8 tools/Verify-Fable2EntrypointClosure.py` | **PASS**: schema 3 / analyzer 2.0.0, expected image, 35,626 candidates, fixtures pass. |
| Probe configure/build, tool/runtime snapshots, isolated regeneration and verifier | **PASS**: full-image/DLL/source checks above. |
| `fable2-build` | **PASS**; normal release build. Existing oversized generated-function warning remains diagnostic, not suppressed. |
| Manifest / function / ownership checks | **PASS** in closure validation and current tests; manifest byte-identical to starting HEAD, no new entry or owner. |
| Old Phase 2E–2H full witness replay | **BLOCKED** on their intentional frozen README/branch/delta/SDK contracts; not required to approve a semantic change because none was made. |
| New gameplay / renderer regression run | **NOT APPLICABLE**: no runtime/gameplay/renderer changes; loader-only experiment does not claim gameplay validation. |

Full-discovery errors include `Bound size mismatch: README.md`,
`Git delta escaped Phase 2G allowlist`, `Phase 2G branch required`,
`Input identity changed: README.md`, `Phase 2H branch required`, and
`SDK branch mismatch`. The historical contracts are left intact. An initial
subset runner omitted the repository from Python's path and had one import
error; fixing the runner's path produced the reported 350-test PASS. The test
run marked the manifest stat cache dirty, but its bytes exactly matched
`git show HEAD:fable2_manifest.toml`; there was no manifest-content change.

No pushes, tags, releases, PRs, remote merges, external uploads or external
repository modifications occurred. Logical local commits contain the isolated
validation tooling and this audit's evidence/documentation.
