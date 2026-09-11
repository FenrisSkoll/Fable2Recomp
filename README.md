# Fable II Recomp

**Fable2Recomp** is a native static-recompilation project for the Xbox 360 release of **Fable II: Game of the Year Edition with Title Update 1**. It uses the [required ReXGlue fork](https://github.com/FenrisSkoll/rexglue-sdk) for the Xbox 360 runtime and the Xenos graphics path.

The project aims for accurate, vanilla game behaviour first. Higher resolutions, frame rates, graphics enhancements and other PC-specific features come after the original game is stable.

Fable2Recomp does not distribute Fable II, its executable, title update or game assets. You must supply files from your own legally obtained copy.

## Current status

The Windows AMD64 build currently:

- boots successfully, passes the main menu and reaches controllable childhood gameplay in Bowerstone Old Town through the established normal runtime path;
- can create, enumerate, load and update the tested `Hero000` save; and
- has validated save interoperability through `Xenia -> native -> native restart -> Xenia`.

![Fable II title screen](docs/images/fable2-title-screen.jpg)

This is meaningful bring-up progress, not a claim that the full game is playable or release-ready. The whole campaign, every quest and every gameplay system have not been validated.

The save investigation and its exact evidence are recorded in [Native-save write parity](docs/fable2-native-save-write-parity.md). A historical native attempt that produced only three files was not reproduced during the validated workflow, so its original cause remains unproved.

## Required ReXGlue fork

Fable2Recomp currently requires the project fork at [FenrisSkoll/rexglue-sdk](https://github.com/FenrisSkoll/rexglue-sdk), not an unmodified upstream SDK release. The build checks the SDK's exported identity and currently pins:

```text
commit:  fc5a00b31f702e82377aa1010395af7ba8cff4f7
version: 0.10.0.51-dev.gfc5a00b
```

[Upstream ReXGlue](https://github.com/rexglue/rexglue-sdk) remains the originating project. Fable II-specific runtime, code-generation and save-path work is carried by the required fork until it is available upstream.

Fable2Recomp consumes an installed ReXGlue CMake package through `rexglue_DIR`. `REXSDK` is not used. `REXSDK_DIR` remains available for deliberate source-tree integration, but package mode is the established configuration.

## Building on Windows

Windows AMD64 with the D3D12-backed Xenos plugin is the currently validated host configuration. The repository also contains other CMake presets, but they do not imply equivalent runtime validation.

### Prerequisites

- Windows on x86-64 with a D3D12-capable GPU and current drivers;
- Git, including submodule support;
- CMake 3.25 or newer and Ninja;
- a recent Clang/LLVM toolchain usable with the Windows SDK and MSVC libraries;
- PowerShell 7 and Python 3 for the repository's analysis and verification helpers; and
- a legally obtained Fable II GOTY executable, TU1 patch and extracted game data.

### 1. Build and install the required ReXGlue revision

```powershell
git clone --recursive https://github.com/FenrisSkoll/rexglue-sdk.git
Set-Location .\rexglue-sdk
git checkout fc5a00b31f702e82377aa1010395af7ba8cff4f7

cmake --preset win-amd64 `
    -DREXGLUE_USE_D3D12=ON `
    -DREXGLUE_USE_VULKAN=OFF
cmake --build --preset win-amd64-release --target install
```

The default install tree is `out/install/win-amd64`. If you set a different `CMAKE_INSTALL_PREFIX`, use that location in the next step.

### 2. Prepare private Fable II inputs

Clone Fable2Recomp, then create the ignored `assets` directories:

```powershell
git clone https://github.com/FenrisSkoll/Fable2Recomp.git
Set-Location .\Fable2Recomp

New-Item -ItemType Directory -Force .\assets\tu1 | Out-Null
New-Item -ItemType Directory -Force .\assets\runtime | Out-Null
New-Item -ItemType Directory -Force .\assets\update | Out-Null
```

Supply these private inputs from your own copy:

```text
assets/tu1/default.xex   base executable used by code generation
assets/tu1/default.xexp  sibling TU1 executable patch applied during code generation
assets/runtime/          extracted GOTY game filesystem used at runtime
assets/update/           extracted TU1 data overlay used at runtime
```

Keep the filenames exactly as shown. ReXGlue discovers `default.xexp` as the sibling patch for `default.xex`; the generated program therefore targets the TU1-patched executable, not the unpatched base image. Do not commit any of these inputs.

### 3. Configure, generate and build

Point `rexglue_DIR` at the installed package from step 1. Replace the example path if the two repositories are elsewhere:

```powershell
cmake --preset win-amd64-release `
    -Drexglue_DIR=C:/Dev/rexglue-sdk/out/install/win-amd64/lib/cmake/rexglue

cmake --build --preset win-amd64-release --target fable2_codegen
cmake --build --preset win-amd64-release
```

Code generation is also a dependency of the normal build, so it reruns when an input changes. Running the target explicitly makes TU1 input or analysis failures visible before compilation.

The executable and graphics plugin are staged under:

```text
out/build/win-amd64-release/fable2.exe
out/build/win-amd64-release/rexgpu-xenos.dll
```

## Running

Use an isolated user-data directory while testing so saves cannot be written into the game-data tree or an existing profile:

```powershell
New-Item -ItemType Directory -Force .\out\user-data | Out-Null

.\out\build\win-amd64-release\fable2.exe `
    --game_data_root .\assets\runtime `
    --update_data_root .\assets\update `
    --user_data_root .\out\user-data `
    --gpu_plugin=xenos
```

Back up important saves before testing development builds. Save-path tracing is disabled by default; the controlled diagnostic procedure is documented in [Native-save write parity](docs/fable2-native-save-write-parity.md).

## Technical status and contributor tooling

- **TU1 recompilation:** the base XEX and sibling XEXP are loaded together, and code generation operates on the patched image.
- **Discovery:** the project includes static entrypoint closure, function-map, jump-table and indirect-target analysis. See the [discovery pipeline](docs/fable2-discovery-pipeline/01-static-entrypoint-closure.md), [Phase 4 closeout](docs/fable2-discovery-pipeline/06-phase4-closeout.md) and [focused ownership corroboration](docs/fable2-discovery-pipeline/07-focused-ownership-corroboration.md). All 42 reviewed internal entries and 114 switch destinations retain their existing owners; none was promoted to a new function.
- **Runtime diagnosis:** dispatch-only and full fault-walker configurations are experimental, opt-in tools for contributors. See [Fault walking](docs/fault-walk.md).
- **Extended coverage:** [Phase 5A tranche 001](docs/fable2-discovery-pipeline/09-phase5a-tranche-001.md) is complete: Bowerstone Market-to-Oakfield reference coverage, one reviewed thunk import and a successful native Oakfield endpoint smoke test. Full-tranche native replay parity and gameplay tracing overhead remain unmeasured; the [session contract](docs/fable2-discovery-pipeline/coverage/README.md) preserves those limits.
- **Rendering:** the normal build uses ReXGlue's Xenos plugin with the validated D3D12 path. The [NR0A architecture gate](docs/fable2-native-renderer/nr0a/README.md) conditionally recommends a Fable-specific renderer developed through isolated workloads; bounded frame-contract evidence remains required after NR0B-1 configuration verification. The accepted [G1 research](docs/fable2-native-renderer/g1-completion.md) and [GPU reference](docs/fable2-gpu-reference/README.md) remain its foundation. No replacement renderer is enabled.
- **Saves:** the tested `Hero000` workflow supports native creation, restart loading, updating and Xenia interoperability. Payload-free, opt-in traces and synthetic filesystem/flush tests support further diagnosis.
- **GPU configuration:** [NR0B-1](docs/fable2-native-renderer/nr0b1/README.md) is verified from the user-operated Oakfield run: RTX 5080, Xenos/D3D12 RTV, bindless/tiled resources, 1× scale and actual exit 0. Black/blank character and dog surfaces remain unexplained.
- **GPU metadata:** [NR0B-2](docs/fable2-native-renderer/nr0b2/README.md) has a default-off bounded consumer recorder, validated Release staging and a fresh isolated Oakfield session. **Recorder prepared — user capture required.** No runtime workload is selected and no native renderer is implemented.
- **Prototype archaeology:** [Phase 1](docs/fable2-prototype-archaeology/phase1/report.md) inventories the read-only prototype corpus, recovers CodeView/PDB and source-path evidence, establishes the `23.12.02.0330` development-TU relationship and validates relocation-aware cross-build matching feasibility. Prototype evidence does not override canonical TU1 bytes.

## Near-term priorities

- Extend ordinary gameplay validation beyond the current checkpoints and fix the first evidence-backed runtime divergence.
- Continue conservative function and indirect-target discovery when new gameplay coverage requires it.
- Improve Xenos rendering correctness and performance without replacing working guest behaviour speculatively.
- Broaden save validation across slots, profiles, long-running updates and interruption/failure cases.
- Revisit wider platforms and PC-specific enhancements only after vanilla correctness is substantially stronger.

## Known limitations

- Full-game progression and broad quest, combat, economy, DLC and long-duration save coverage remain incomplete.
- Rendering correctness and performance are still bring-up work. Preserved captures include black dog and exposed-player surfaces whose cause remains unproved; the project should not be treated as an optimized PC port.
- Static discovery explains the validated target set, but unresolved indirect call sites and additional gameplay-dependent targets remain investigation areas.
- Windows AMD64/D3D12 is the validated host path. Linux, ARM64, Vulkan and wider hardware coverage are not currently established for Fable II.
- The experimental fault walker and renderer-research paths are diagnostic only and are disabled in the normal build.
- Native save parity is established only for the tested GOTY TU1 `Hero000` workflow; broader slot, profile and failure-recovery coverage still needs validation.

## Reporting issues and contributing

Use the [issue tracker](https://github.com/FenrisSkoll/Fable2Recomp/issues) for reproducible problems. Include the Fable2Recomp commit, exact ReXGlue version, host/GPU details, title-update state, relevant log lines and reproduction steps. Never attach copyrighted executable or game data, private saves, credentials, memory dumps containing private content, or raw payload traces.

Correctness fixes and narrowly scoped diagnostic improvements are welcome. Preserve exact guest addresses and result codes in technical reports, distinguish confirmed evidence from hypotheses, and keep experimental work clearly separated from the normal runtime path.

## License and attribution

Fable2Recomp is distributed under the [MIT License](LICENSE). It builds on [ReXGlue](https://github.com/rexglue/rexglue-sdk) and the Xbox 360 research and implementation lineage credited by that project.

Fable II and related names and assets are property of their respective owners. This repository is an independent technical project and does not distribute or authorize obtaining copyrighted game files.
