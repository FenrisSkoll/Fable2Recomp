# Preparation and provenance

This is the historical preparation record. The subsequent user-operated run
and recreated-session provenance are reconciled in [runtime closeout](runtime-closeout.md),
which now completes the configuration gate. Original preparation identities
below and `evidence/preparation-summary.json` are retained unchanged.

Date: 2026-09-10. Evidence below is **SOURCE-CONFIRMED** (code/Git) or direct
file/inventory verification, never a claim that the game ran. Planned scene
identity is **PROJECT-REPORTED** from the accepted handoff. Runtime selections
are **UNRESOLVED** until the run card is completed.

## Fresh input index

The root `AGENTS.md` and user scope were read. No additional ancestor/SDK-root
or applicable nested instruction file was found for the edited paths.

| Consulted input, relative to Fable unless SDK named | Role in this phase |
|---|---|
| [Root README](../../../README.md), [GPU index](../../fable2-gpu-reference/README.md), [G1 completion](../g1-completion.md) | Current status and documented verifier policy |
| All NR0A documents: [README](../nr0a/README.md), [reading/provenance](../nr0a/reading-and-provenance.md), [reference audit](../nr0a/reference-implementation-audit.md), [decision](../nr0a/architecture-decision.md), [ownership](../nr0a/ownership-and-transition-contract.md), [evidence plan](../nr0a/nr0b-evidence-plan.md), [gates](../nr0a/implementation-gates.md), [completion](../nr0a/nr0a-completion.md), [pins](../nr0a/evidence/reference-pins.json) | Reuse accepted architecture; configuration first, no external survey repeated |
| [G1.6B](../../fable2-gpu-reference/13-static-xdk-seam-coverage.md), [coverage evidence](../../fable2-gpu-reference/evidence/static-xdk-seam-coverage.json), [experiment plan](../../fable2-gpu-reference/09-evidence-gaps-and-experiment-plan.md), [divergence](../../fable2-gpu-reference/03-rexglue-canary-divergence.md) | EXP-CONFIG-CAP-001 and alpha blend-factor capability; static evidence does not establish runtime coverage |
| [Ownership reassessment](../../fable2-gpu-reference/07-boundary-and-ownership-reassessment.md), [UI contract](../../fable2-gpu-reference/08-system-ui-and-presentation-contract.md), source-symbol catalog in NR0A | Current GPU consumer and host-composition boundaries |
| [Retirement](../../fable2-gpu-reference/g2a-retirement.md), [research integration](../../fable2-gpu-reference/g1-g1.6-research-completion.md) | Retired implementation stays retired; accepted lineage is retained |
| [Native save parity](../../fable2-native-save-write-parity.md), [testing contract](../../fable2-discovery-pipeline/coverage/README.md), [completed Phase 5A](../../fable2-discovery-pipeline/09-phase5a-tranche-001.md) | Latest Oakfield checkpoint, seven payloads/platform metadata, isolated-root exception, actual-process monitoring |
| Live PowerShell definitions `Get-Fable2NextRunNumber`, `fable2-run` | Preserve numbered logs and Release/Xenos/debug arguments; do not edit normal helper |
| SDK `src/ui/rex_app.cpp`, `src/system/runtime.cpp`, `src/system/gpu_plugin_loader.cpp`, `src/system/xex_module.cpp`; SDK source sites in [gap table](effective-configuration.md) | Final path/config precedence, exe-adjacent plugin loading, supported title-update log, selected capability and rendering branches |
| SDK `CMakePresets.json`, `tests/unit/CMakeLists.txt`, existing Release CMake cache; Fable `src/fable2_app.h` | Narrow build, unchanged consumer ABI/application sources and test integration |

The initial read-only audit is retained as `out/nr0b1/initial-state.json` with
hashes of all NR0A inputs, baseline binaries, source save inventory, manifest
and 15 libmspack materializations. It is not replaced by later results.

## Accepted lineage and build boundary

| Repository | Starting HEAD / tree | New local branch |
|---|---|---|
| `C:\Dev\Fable2Recomp` | `e2d496779e34c49a1e99ce786a4e4931f289f6ce` / `f233b89b8b80ad7ed233a879b1f0d8f8289f332a` | `fable2-native-renderer-nr0b1-preparation` |
| `C:\Dev\rexglue-sdk-v0.10` | `fc5a00b31f702e82377aa1010395af7ba8cff4f7` / `903af44f9aab5684443ddb22e505b0ea811d45d2` | `fable2-native-renderer-nr0b1-config-reporting` |

Both indexes were initially empty; branches did not already exist. NR0A and
accepted save/testing ancestry remain present. No newer accepted changes
superseded NR0A at entry. Worktree/submodule states were inspected. The only
unrelated edits are the Fable manifest blank-line deletion (raw SHA-256
`EF1656D77D270F207C4A16D3B92D5B86C4414CE38292D079AEF52B120CE778E1`)
and 15 SDK libmspack materializations at gitlink
`305907723a4e7ab2018e58040059ffb5e77db837`. They remain byte-for-byte preserved.

SDK reporting source is committed as
`06c4b7002a449ad4d173ec90c625e490ed03fe74`, tree
`5feea2389d0ce264ab970bf7807ee4ae6bd7960d`. The successful Release build used
the same source content immediately before that commit, plus the explicitly
preserved libmspack files. A baked version string alone does not establish this
build identity. Existing `out/build/win-amd64` selected Ninja Multi-Config,
Clang, D3D12 ON, Vulkan OFF, tests ON. Only `rexruntime`, `rexgpu-xenos` and
`unit_tests` with their required dependencies were built. No install target,
Fable build, codegen, manifest/generated change or dependency update occurred.

ReXApp implementation is compiled into the consumer executable; it was not
changed. The added runtime constructor body and report calls introduce no
public object-layout, virtual-method or GPU-plugin ABI change. Reusing the
baseline EXE with the reporting runtime/GPU DLLs is source-supported, with
actual module/initialization compatibility still awaiting the run. Plugin
loading uses `GetExecutableFolder() / PluginFileName(name)`, not the working
directory's baseline DLL. Windows module observation must confirm this.

## Baseline versus staged artifacts

Baseline directory: `C:\Dev\Fable2Recomp\out\build\win-amd64-release`.
Staged directory: `C:\Dev\Fable2Recomp\out\nr0b1\sessions\nr0b1-oakfield-20260910-001\runtime`.
These are **disk identities**, not loaded-process observations.

| File | Baseline size / SHA-256 | Staged size / SHA-256 |
|---|---|---|
| `fable2.exe` | 105042944 / `1642ED03BD8B117A8FED6E9FF912AD49CBF0E91A4E1D226B20C266925E3FF2C9` | Identical copy; not rebuilt |
| `rexruntime.dll` | 10332160 / `71BB1BA29413773226245B1D05F40379561C974F8E2EA4E5BB994D6DC3591793` | 10380288 / `D325FA4296577565137AD9480A258CE65AD071D9C538C0362783F89725B111B6` |
| `rexgpu-xenos.dll` | 2770944 / `70492C8612DEF79C9E3946817F424111FAB2155A3BE63CEA6E717CA73893ADC5` | 2817024 / `6DBD1336DC219D8181DF65D4AB179512400ED6A7BF5FDAEACE29A7162EDD3BB8` |
| `TracyClient.dll` | 232960 / `FDBE7A329E1B06A86FE61A2C5BE6B335F32F9BBCA7E05F7B183A35C515D2D1A5` | Identical copy |

Historical G1/G1.6 executable/GPU hashes remain in their original evidence;
they are not replaced with these values. Fable's current source HEAD is a
provenance checkpoint, not proof of the exact compilation invocation that
produced the reused EXE. Its unchanged bytes are the accepted baseline identity.

The explicit runtime input files were independently hashed: `assets/runtime/default.xex`
is 21217280 bytes, SHA-256
`88C4EF2E18E65409444D1B068EFF921D1F7E180A5AE64EDC64BA6B0872372662`;
its sibling `default.xexp` is 2992128 bytes, SHA-256
`046A05693B4DA4437083C784000A850858B3BF992955C7DB30D518FB3E53E41C`.
Preflight and post-run integrity checks repeat these two hashes. Supported
loader logging (`XexModule::ApplyPatch`, successful base/new version record)
and shader-storage title ID will supply runtime corroboration. Accepted title
and media are `0x4D5307F1` / `0x716F0A0D`, TU1 `0.0.1.26`.
Post-patch contiguous image SHA-256
`BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00`
remains inherited static evidence: this reporter does not hash loaded guest
memory or independently recover runtime media identity.

## Save and cache isolation

Selected source:
`C:\Dev\Fable2Recomp\out\phase5a\checkpoints\end-001-native\user-data`.
The latest accepted Phase 5A handoff identifies **Oakfield tavern**; this
supersedes the earlier user-reported Market fountain context. Source presence
and main-save identity were verified; the new load/scene is not yet confirmed.
`mainsave.bin` is 415039 bytes with SHA-256
`13FC340F6869DA73CB958BA36CB50905E29B8FBEA073CEFF46490DB4A9812489`.

Preserved copy:
`out/nr0b1/checkpoints/nr0b1-oakfield-20260910-001/user-data`.
Writable test copy:
`out/nr0b1/sessions/nr0b1-oakfield-20260910-001/user-data`.
All roots are distinct. Both copies match the full 14-file relative-path,
size and SHA-256 inventory, including seven `Hero000` payloads, the native
328-byte header, three profile files, achievements metadata and two cache
files. Full metadata is in the ignored `preparation.json` and the reviewed
[evidence summary](evidence/preparation-summary.json). Directory structure and
file metadata are preserved with `copytree` / `copy2`; no native/Xenia header
mixing, conversion, import/export or repair occurred. Existing destinations
are refused. Output ignore policy was verified before copies were written.

The test explicitly uses its writable root's `cache` directory. It exists
before launch and contains copied baseline material: shareable `.rtv.d3d12.xpso`
(46956 bytes) and `.xsh` (246884 bytes), not a fresh empty cache. This narrow
inventory is sufficient; no large cache tree was hashed. Only the writable
copy may be updated by normal runtime validation/storage. The reporting change
does not modify cache formats, translator behavior or pipeline descriptions;
actual path/header acceptance still depends on selected RT path and current
runtime checks. Copied material is not proof of a fully warmed run. Driver/OS
caches have no established isolation mechanism and remain unisolated with
unknown contents. No performance benchmark is claimed.

Baseline and staged exe-adjacent `fable2.toml` are absent. Presence/identity is
checked again before launch and after exit; the CVar snapshot distinguishes
default, config, environment, command-line and runtime sources. No GPU-setting
override is added except enabling reporting; user/cache roots are explicitly
isolated. CLI arguments and effective runtime paths are recorded separately.
