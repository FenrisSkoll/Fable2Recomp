# Reading and provenance

Inspection date: 2026-09-09. The user-supplied instructions and the applicable
local `C:\Dev\Fable2Recomp\AGENTS.md` were read before architectural work.
No additional ancestor/nested instruction file was found for the changed paths;
no SDK `AGENTS.md` was found. Canonical roots are Fable2Recomp and
`C:\Dev\rexglue-sdk-v0.10`. The similarly named other SDK worktree was not
selected as canonical.

## Accepted starting lineage

| Repository | Starting branch / HEAD | Tree | Preserved state |
|---|---|---|---|
| `C:\Dev\Fable2Recomp` | main / `9936fd1839da4286a9d09530ae0bb6ac11b5eda4` | `814f96b0ad58c891032233452027cfee5f5bad2a` | Index clean; one pre-existing blank-line deletion in `fable2_manifest.toml` |
| `C:\Dev\rexglue-sdk-v0.10` | main / `fc5a00b31f702e82377aa1010395af7ba8cff4f7` | `903af44f9aab5684443ddb22e505b0ea811d45d2` | Index clean; existing libmspack materialization only |

Current Fable main contains each historical research anchor, verified with
`git merge-base --is-ancestor`: G1
`c44e8c16f4422f9a828caf30899ac989170b8a8c`, G1.6B
`cd440652451e558b88ba50402721e4cbe82b9a90`, retirement
`7e8d9e92fff5ca766f9aa12506b6205868e34f62`, integration
`8d1b10d9f56905b0aa518621614d51beda60c962`. Recent main history also includes
accepted save integration, ownership work and completed Phase 5A testing.
The NR0A branch did not exist and was created directly from this verified main.
The unrelated manifest whitespace does not conflict with documentation/tooling.
No stash, reset or inclusion of that edit was necessary.

The [pin catalog](evidence/reference-pins.json) records starting identities
after branch creation, not the ending documentation commit. It includes the
manifest worktree SHA-256
`EF1656D77D270F207C4A16D3B92D5B86C4414CE38292D079AEF52B120CE778E1`
and hashes for all 15 existing libmspack materialized files. The SDK gitlink is
`305907723a4e7ab2018e58040059ffb5e77db837`. Worktree lists and recursive
submodule states were inspected; linked fault-walker/closure/capture worktrees
were not used or modified. Fable has no submodules.

SDK history from the G1.5 reference
`956c6a8b5da4c54b9899a2593e9c67c26de30194` to current HEAD changes save,
filesystem/XAM content/device-selector diagnostics and closure work. A scoped
Git comparison reports no changes under `src/graphics`, `include/rex/graphics`,
`src/ui` or `include/rex/ui`. Current source was still checked directly. This
supports carrying forward GPU ownership evidence, not equating rebuilt DLLs.
The current release CMake cache selects
`C:/Dev/rexglue-sdk-v0.10/out/install/win-amd64/lib/cmake/rexglue`.

## Current versus historical artifacts

These current files were read and hashed, never launched. A present file is not
proof that it was loaded by a process, nor a reproducible-build attestation.

| Identity | Current observation | Historical research identity |
|---|---|---|
| `out/build/win-amd64-release/fable2.exe` | 105042944 bytes; `1642ED03BD8B117A8FED6E9FF912AD49CBF0E91A4E1D226B20C266925E3FF2C9` | `EEACEAA8DB38E728B79F4F78B0298B7036E13EB4903518C503199697FA64AE6F` |
| `out/build/win-amd64-release/rexgpu-xenos.dll` | 2770944 bytes; `70492C8612DEF79C9E3946817F424111FAB2155A3BE63CEA6E717CA73893ADC5` | 2770944 bytes; `8232051BED6E5CE99CF37B2EF581C824F58875C140A4D3C75DE14E8A5DF4AA99` |
| `out/build/win-amd64-release/rexruntime.dll` | 10332160 bytes; `71BB1BA29413773226245B1D05F40379561C974F8E2EA4E5BB994D6DC3591793` | Not substituted into old evidence |
| TU1 post-patch contiguous image | Inherited accepted `BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00` | Same evidence target; no new load performed |

Title/media are `0x4D5307F1` / `0x716F0A0D`, TU1 `0.0.1.26`.
Accepted base XEX hash is
`88C4EF2E18E65409444D1B068EFF921D1F7E180A5AE64EDC64BA6B0872372662`;
XEXP hash is
`046A05693B4DA4437083C784000A850858B3BF992955C7DB30D518FB3E53E41C`.
NR0B must reacquire actual loaded identities. Newer accepted builds explain why
historical artifact-equality checks no longer pass; equal DLL size is not equal
content. Historical evidence is preserved unchanged.

## Reading index

Paths below are relative to Fable2Recomp unless a repository is named. This is a
decision-oriented index of substantive reading, not a second historical corpus.

| Consulted source | Role in NR0A |
|---|---|
| [Root README](../../../README.md), [GPU index](../../fable2-gpu-reference/README.md), [G1 completion](../g1-completion.md) | Current status, documentation entrypoints, original G1 scope and verification instructions |
| [G1 scope](../00-workstream-scope.md), [GPU path](../01-current-gpu-data-path.md), [Unleashed study](../02-unleashed-recompiled-reference.md) | Discover existing reference roots; original integration and license analysis |
| [Hook inventory](../03-candidate-hook-inventory.md), [machine inventory](../candidate-hook-inventory.json), [options](../04-architecture-options.md) | Distinguish qualified ABI/boundary evidence from semantic leads |
| [Shadow design](../05-shadow-capture-design.md), [risk register](../06-risk-register.md) | Historical unimplemented forwarding/privacy/ordering ideas; obsolete G2 next-step priority is not resumed |
| [G1.5 pins](../../fable2-gpu-reference/00-scope-and-pins.md), [ReXGlue overview](../../fable2-gpu-reference/01-rexglue-overview.md), `docs/fable2-gpu-reference/rexglue/01-...08-*.md` | Plugin, ring/register, shaders, fetch, EDRAM, draws, memory, fences, presentation and UI ownership; chapter paths enumerated by the GPU index |
| [Canary overview](../../fable2-gpu-reference/02-xenia-canary-overview.md), `docs/fable2-gpu-reference/xenia-canary/01-...08-*.md` | Independent implementation/capability comparison at retained pin, not a correctness oracle |
| [Divergence](../../fable2-gpu-reference/03-rexglue-canary-divergence.md), [history](../../fable2-gpu-reference/04-divergence-history-and-rationale.md), [classification](../../fable2-gpu-reference/05-accuracy-performance-architecture-classification.md) | Distinguish backend differences, performance choices and unproved Fable symptom causes |
| [Fable relevance](../../fable2-gpu-reference/06-fable2-relevance-assessment.md), [boundaries](../../fable2-gpu-reference/07-boundary-and-ownership-reassessment.md), [UI](../../fable2-gpu-reference/08-system-ui-and-presentation-contract.md) | Purpose-qualified seams, completion/focus and exclusive GPU ownership |
| [Experiments](../../fable2-gpu-reference/09-evidence-gaps-and-experiment-plan.md), [reference architecture](../../fable2-gpu-reference/10-custom-renderer-reference-architecture.md), [dated G2A decision](../../fable2-gpu-reference/11-g2a-reentry-decision.md) | Configuration-first gate and limits on live replacement; re-entry decision subsequently retired |
| [G1.6A recovery](../../fable2-gpu-reference/12-static-xdk-method-recovery.md), [G1.6B coverage](../../fable2-gpu-reference/13-static-xdk-seam-coverage.md) | TU1 operation, exact callers, six bypasses and five distinct lifetimes |
| [Retirement](../../fable2-gpu-reference/g2a-retirement.md), [integration completion](../../fable2-gpu-reference/g1-g1.6-research-completion.md), phase completion records and [open questions](../../fable2-gpu-reference/open-questions.md) | Accepted handoff, ancestry and prohibition on restoring retired implementation |
| `docs/fable2-gpu-reference/evidence/`: `rexglue-source-inventory.json`, `rexglue-subsystem-map.json`, `canary-source-inventory.json`, `canary-subsystem-map.json`, `divergence-matrix.json`, `divergence-history.json`, `fable2-relevance-matrix.json`, `boundary-assessment.json`, `replacement-seams.json`, `experiment-backlog.json`, `g2a-decision.json`, `static-xdk-method-inventory.json`, `static-xdk-seam-coverage.json` | Machine-readable sources, classifications, selected experiment and coverage counterexamples; checked with the existing verifier |
| [GPU verifier](../../../tools/Verify-Fable2GpuReference.py), schemas linked by the GPU index, [G1 verifier](../../../tools/Verify-Fable2NativeRendererG1.py) | Default source/structure versus optional historical-artifact policy; no weakening for missing logs |
| [Save parity](../../fable2-native-save/fable2-native-save-write-parity.md), [testing contract](../../fable2-discovery-pipeline/coverage/README.md), [Phase 5A preparation](../../fable2-discovery-pipeline/08-phase5a-runtime-coverage.md), [completed tranche](../../fable2-discovery-pipeline/09-phase5a-tranche-001.md) | Accepted save isolation, user-operated workflow and newer Oakfield handoff |
| Canonical SDK root README; source paths/symbols in [catalog](evidence/reference-pins.json); Fable `src/fable2_app.h` | Current integration and source ownership, absence of Skate callback/RHI in canonical SDK |
| External immutable sources in [implementation audit](reference-implementation-audit.md) and catalog | Actual renderer execution paths, component boundaries, licenses, backend limitations |

## Save/testing handoff that supersedes the older checkpoint

The prompt's Market fountain/Theresa checkpoint is **PROJECT-REPORTED** user
context. The completed Phase 5A tranche is newer: its documented endpoint is
Oakfield tavern. Neither establishes that an arbitrarily selected save exists
today. NR0A read documentation, not save directories or payloads.

The accepted interoperability test is `Xenia -> native -> native restart ->
Xenia` for tested `Hero000`; broader slots/profiles/failure recovery remain
unproved. The latest documented preserved native endpoint is
`C:\Dev\Fable2Recomp\out\phase5a\checkpoints\end-001-native\user-data`.
Its documented `mainsave.bin` is 415039 bytes, SHA-256
`13FC340F6869DA73CB958BA36CB50905E29B8FBEA073CEFF46490DB4A9812489`.
The historical writable session is
`C:\Dev\Fable2Recomp\out\phase5a\sessions\phase5a-native-001\user-data`.
Future collection must make a new separately authorized working copy, never
reuse that session or write into preserved checkpoints, normal profiles,
`C:\Users\Fenris\Documents\fable2.backup` or `C:\Dev\Fable2XeniaSaves`.

Seven native payloads belong under
`B13EBABEBABEBABE\4D5307F1\00000001\Hero000`. Reference XUID is
`E03000002168622D`; native/Xenia headers differ (328 versus 40960 bytes).
The established workflow preserves platform metadata; do not transplant
headers. Selecting the existing native endpoint avoids a new cross-platform
save conversion merely to collect a frame.

The latest endpoint smoke is user-confirmed load/control/basic interaction/
save/exit. Payloads were unchanged, so that smoke alone does not independently
prove a fresh payload write. It does not prove full native Market-to-Oakfield
replay parity. Its `fable2-run-002.log` is recorded in the tranche with SHA-256
`2F214CC13C482A5B35FD70265DBF0CF047F8BA675C0F35FC4396E5E13316D516`.
The old launcher reported an end before log start and a null exit code; future
collection must wait for the actual process handle and distinguish user exit
report, process termination and GPU completion.

The testing Canary checkout is separately documented at
`C:\Dev\Fable2Phase4Xenia\xenia-canary`, branch
`fable2-indirect-target-collector`, commit
`32460b5d887dcde6622bb17983b70752fa5f13b3`, tree
`114cb589291e2c87fcbcabc949a730ca5d1f6cad`. Its documented executable embeds
`6b6715b029d442ff6ed5a89773f119400b1c19b5`, with SHA-256
`8DCD8FEA50BF971B4710C45494C47DB84EF77E9D04C60657EB3FE9311B49E65E`.
These are distinct from the research Canary pin
`3a44f20c7bc66db1da583e8a6f0ab740e31908e9`. NR0A does not need a new Canary
run. The newer testing records do not complete `EXP-CONFIG-CAP-001` or supply
a native GPU frame/resource contract.
