# Fable II native renderer G1 completion

Completion date: `2026-09-01`

## Result

**PASS WITH LIMITATIONS**

The exact TU1 program contains a hookable static Xbox graphics boundary before
rendering collapses into raw Xenos packets. Device/engine lifecycle and
swap/present functions are confirmed, and generated functions can in principle
be wrapped while their original implementations continue to feed the validated
ReXGPU path. The full resource/state/shader/draw API inventory and a stable
Lionhead engine command ABI remain unconfirmed. No native renderer or capture
mode was implemented.

## Repository identities

| Point | Repository identity | State |
|---|---|---|
| G1 start | `C:\Dev\Fable2Recomp`, branch `fable2-phase4-indirect-targets`, HEAD `a60603f737ff5da65d9a643e8a24de0907bd997d`, tree `98a88d6c74fd6535be899905b1b3f463b4b37488` | clean; validated Phase 4 completion |
| G1 work branch | `C:\Dev\Fable2Recomp`, branch `fable2-native-renderer-g1-audit`, parent/runtime baseline `a60603f737ff5da65d9a643e8a24de0907bd997d`, tree `98a88d6c74fd6535be899905b1b3f463b4b37488` | only this documentation/evidence package and its read-only verifier change the committed tree |
| SDK start/end | `C:\Dev\rexglue-sdk-v0.10`, branch `fable2-v0.10-migration`, HEAD `956c6a8b5da4c54b9899a2593e9c67c26de30194`, tree `b78b06b8ac650467372236a3a262864e069a9382` | unchanged; pre-existing nested `thirdparty/libmspack` symlink materialization preserved at pin `305907723a4e7ab2018e58040059ffb5e77db837` |

The ending Fable HEAD is the local commit containing this document on
`fable2-native-renderer-g1-audit`. A Git commit cannot embed its own SHA-1; the
exact full ending commit and tree are therefore recorded by the final session
handoff and are directly reproducible with:

```powershell
git rev-parse HEAD
git rev-parse 'HEAD^{tree}'
```

No branch, commit, or file was created in the SDK. No push, merge, tag, pull
request, upload, or release occurred.

## Commands and analyses performed

Repository/instruction audit:

```powershell
rg --files -g AGENTS.md C:\Dev\Fable2Recomp C:\Dev\rexglue-sdk-v0.10
git status --porcelain=v2 --branch
git rev-parse HEAD
git rev-parse 'HEAD^{tree}'
git remote -v
git submodule status
git log -8 --date=iso-strict --pretty=format:'%H%x09%ad%x09%s'
git switch -c fable2-native-renderer-g1-audit
```

All applicable `AGENTS.md` files and current bring-up, ReXGlue 0.10, GPU,
runtime-validation, fault-walker, static closure, Ghidra, jump-table, and Phase
4 completion/handoff documentation were read. The Fable CMake integration and
ReXGlue plugin ABI, loader, runtime, graphics interfaces, command processor,
video HLE, D3D12/Vulkan backends, presenter, CMake helpers, and packaging paths
were inspected with targeted `rg` and `Get-Content` searches.

Exact TU1/generated analysis:

- searched all generated bodies and import callsites for `Vd*`, swap, ring,
  shader, draw, resource, state, and renderer evidence;
- counted PPC instructions for all 11 inventory ranges and checked exclusive
  ends;
- built direct-caller lists from generated output;
- queried the existing exact-image Ghidra project read-only, without analysis
  mutation, for `.pdata`, code/data xrefs, renderer labels, and containing
  functions;
- inspected private TU1 metadata under ignored `out/` paths; no executable or
  payload bytes were copied into documentation;
- traced `VdSwap` packet construction through ReXGlue `CommandProcessor` and
  D3D12/Vulkan `IssueDraw`, `IssueCopy`, `IssueSwap`, and presentation paths.

External references were shallow-cloned outside the tracked repositories using
the equivalent of:

```powershell
git clone --depth 200 --no-tags <repository-url> `
    C:\Dev\Fable2NativeRendererResearch\<repository-name>
```

Their exact branches, HEADs, trees, commit dates, working state, source, history,
submodule pins, and licences were inspected. The pinned identities are in
[`00-workstream-scope.md`](00-workstream-scope.md).

Validation commands:

```powershell
python .\tools\Verify-Fable2NativeRendererG1.py
python -m py_compile .\tools\Verify-Fable2NativeRendererG1.py
git diff --check
git status --short
git diff --name-only
git check-ignore .\out\renderer-captures\probe
```

The verifier checks the schema, exact TU1 identity, sorted/unique address
inventory, range arithmetic, confidence counts, required operation coverage,
Markdown coverage, and generated-body instruction counts. Final validation
results before staging were:

```text
Validated 11 G1 candidates: confirmed=5, strong_hypothesis=4, weak_hypothesis=2
```

`py_compile` and `git diff --check` succeeded. `git check-ignore` confirmed
`.\out\renderer-captures\probe` is ignored. The exact commit identity is
recorded in the session handoff after commit creation.

## Confirmed rendering boundary

The strongest evidence is exact TU1 range
`[0x82BA34D8,0x82BA3BFC)`, size `0x724`, generated name
`sub_82BA34D8`. Its 457-instruction body directly calls
`VdGetSystemCommandBuffer` and `VdSwap`. Direct generated callers are
`0x82B6EA60`, `0x82B6F1D0`, `0x82B6FA48`, and `0x82BA5D08`;
exact-image Ghidra records `.pdata` at `0x821377C0` and a call reference at
`0x82B6FB00`. Callers pass a device-like object in `r3`, a
front-buffer/surface-like object in `r4`, and flags in `r5`.

This function retains presentation/resource meaning and is callable before
ReXGlue's `VdSwap` serializes the operation into a Type-0 texture-fetch packet,
`PM4_XE_SWAP`, front-buffer physical address, dimensions, and NOPs. It is
therefore distinguishable from the raw command processor and is the first safe
shadow-capture proof target.

`sub_82BA6990` at `[0x82BA6990,0x82BA6C18)` confirms device/engine
initialization; `sub_82BA2830` at `[0x82BA2830,0x82BA2CA0)` confirms ring
transport setup; and `sub_82BA6968` / `sub_82BA6C18` confirm shutdown. The
device-like allocation is observed as `0x5E80` bytes and the initialization
block as `0x7C` bytes.

## Architecture decision

- **Primary seam:** statically linked Xbox D3D/XDK methods before command
  generation, initially operated only as forwarding shadow hooks.
- **Fallback seam:** the Lionhead async render-command layer around
  `sub_82AAC208`, but only if G2 proves its command ABI and complete coverage.
- **Oracle:** unchanged `rexgpu-xenos.dll` plus optional raw packet/register
  correlation.
- **Rejected primary:** replacing GPU ABI version 1, because it begins after
  semantic collapse and requires emulator-scale Xenos implementation.

## Candidate counts

| Confidence | Count |
|---|---:|
| CONFIRMED | 5 |
| STRONG HYPOTHESIS | 4 |
| WEAK HYPOTHESIS | 2 |
| Total | 11 |

The operation inventory deliberately reports resource/surface creation,
texture/VB/IB lock/unlock, targets, input layout/streams, shaders/constants,
textures/samplers, render state, clear, draws, and semantic resolves/queries as
unknown. Raw PM4 handlers do not convert those unknowns into confirmed API
hooks.

## Open questions and risks

1. Which exact TU1 device/function-table entries implement draw, resource,
   state, shader, resolve, query, and synchronization operations?
2. Does every material rendering operation traverse one static Xbox method
   layer, or do some subsystems emit ring packets directly?
3. Is `sub_82AAC208` an enqueue boundary, a consumer, or only an aggregate
   timing wrapper, and are its command structures stable and self-contained?
4. What are the complete device/resource layouts, alias rules, reference
   counts, endian/format rules, and asynchronous lifetime contracts?
5. Which TU1 shaders require features absent or title-specific in
   XenosRecomp?
6. Can wrapper capture remain packet-, guest-state-, and presentation-equivalent
   under multi-threaded gameplay workloads?

The full risk register is [`06-risk-register.md`](06-risk-register.md).

## Exact prerequisites for G2

1. Start from the exact ending commit on
   `fable2-native-renderer-g1-audit`; re-audit both worktrees and preserve the
   SDK state above.
2. Keep `rexgpu-xenos.dll`, its ABI, backend selection, and packaging canonical.
   G2 is not authorized to implement a native backend.
3. Restrict the first code change to a default-off, metadata-only forwarding
   proof for confirmed `0x82BA34D8`, with a separately callable original body,
   recursion protection, synthetic ABI tests, and fail-open recorder behaviour.
4. Before expanding hooks, establish exact boundaries, caller arguments, and
   packet consequences for at least one draw, one resource create/update, one
   shader bind, one target/resolve, and their lifetime paths.
5. Version the byte-free schema and keep all captures under verified ignored
   `out/renderer-captures/` paths. Do not commit private payloads.
6. Complete an initial Fable shader-feature census against the pinned
   XenosRecomp omissions before proposing conversion.
7. Pass capture OFF tests before requesting a user run. Then provide the exact
   environment/launch command, paired OFF control, capture limits, and the short
   manual checkpoint checklist. The user performs all gameplay.
8. Treat UnleashedRecomp as GPL architectural evidence only unless the project
   makes an explicit licensing decision.

## Fresh-session handoff

G1 found a real pre-packet boundary and recommends static Xbox D3D/XDK hooks in
forwarding shadow mode. Begin G2 at `sub_82BA34D8` (`0x82BA34D8`, size `0x724`,
exclusive end `0x82BA3BFC`), preserve its original body, record bounded
metadata, and prove unchanged ReXGPU consequences. In parallel with that narrow
proof, recover representative draw/resource/shader/target methods by tracing
backward from raw packet effects and outward from the `0x5E80` device object's
function tables. Do not implement shader conversion, replay, or a native
backend until hook coverage and equivalence are demonstrated.
