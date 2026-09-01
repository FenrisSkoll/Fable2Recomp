# Scope, source pins and provenance

## Resulting scope

G1.5A is a read-only reconstruction of the ReXGlue GPU implementation loaded
by the current Fable II Release build. The audit includes the plugin ABI,
runtime and XDK boundary, all common Xenos GPU code, the selected D3D12
backend, the presentation/UI layer, generated helper-shader tables, build and
staging definitions, configuration, diagnostics and tests. Vulkan is inspected
only enough to locate the shared-backend boundary because it is not compiled
into the active DLL.

It does not modify or execute G2A, add instrumentation, compare behavior with
Canary, play the title, or change any runtime/build/package behavior.

G1.5B independently reconstructs the exact pinned Canary GPU implementation,
including its common Xenos model, D3D12 and Vulkan backends, presenter, primary
history available in the clone, configuration, incomplete behavior and static
unknowns. It does not compare with ReXGlue, infer Fable II use, run a title, or
change any reference/runtime/build/package behavior.

## Repository relationship

| Role | Branch | Commit | Tree | State at audit start |
|---|---|---|---|---|
| Accepted G1 | `fable2-native-renderer-g1-audit` | `c44e8c16f4422f9a828caf30899ac989170b8a8c` | `f5bde8e945f2d2ab6764c4d9c38f0f3550cac40c` | clean |
| Paused G2A | `fable2-native-renderer-g2a-forwarding-proof` | `47c2ea2b7d9e14b09fd942c4b5f1bd11c46e2f51` | `910e80108c2d9e7d8474866506f1c9e23ede601c` | clean checkpoint |
| G1.5A start | `fable2-native-renderer-g1.5-reference` | `c44e8c16f4422f9a828caf30899ac989170b8a8c` | `f5bde8e945f2d2ab6764c4d9c38f0f3550cac40c` | created directly from G1 |

`git merge-base` is G1 and the G1/G2A left/right count is `0 1`. G2A is one
commit beyond G1. Its checkpoint reports a provisional forwarding hook at
`sub_82BA34D8` and an unresolved Debug link mismatch. G1.5A read that checkpoint
with read-only Git operations and inherited none of its source.

The authoritative Fable remote is
`https://github.com/FenrisSkoll/Fable2Recomp.git`; upstream is
`https://github.com/Fable2Recomp/Fable2Recomp.git`.

## Fable target pin

| Identity | Value |
|---|---|
| Edition/update | Fable II: Game of the Year Edition, Xbox 360 TU1 |
| Title ID / Media ID | `0x4D5307F1` / `0x716F0A0D` |
| Version | `0.0.1.26` |
| Base XEX SHA-256 | `88C4EF2E18E65409444D1B068EFF921D1F7E180A5AE64EDC64BA6B0872372662` |
| XEXP SHA-256 | `046A05693B4DA4437083C784000A850858B3BF992955C7DB30D518FB3E53E41C` |
| Patched image SHA-256 | `BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00` |
| Executable fingerprint | `5C8B78B84C93028D166E3DF347206E6642BA40BF374AD1AF8D958B2211320357` |
| Manifest SHA-256 | `E3EB39CA153E396D5DC53E6F943ED8FF7AF1D6B0704EB860836BD7D21A3F87B0` |
| Image base / size / entry | `0x82000000` / `0x01620000` / `0x82CC21C0` |

Accepted G1 proves `sub_82BA34D8` is
`[0x82BA34D8, 0x82BA3BFC)`, size `0x724`, with 457 PPC instructions and direct
calls to `VdGetSystemCommandBuffer` and `VdSwap`. That proves a title
swap-command emitter, not a semantic PC renderer boundary.

## ReXGlue source pin

| Identity | Value |
|---|---|
| Local repository | `C:\Dev\rexglue-sdk-v0.10` |
| Remote / upstream | `https://github.com/FenrisSkoll/rexglue-sdk.git` / `https://github.com/rexglue/rexglue-sdk.git` |
| Branch | `fable2-v0.10-migration` |
| Commit | `956c6a8b5da4c54b9899a2593e9c67c26de30194` |
| Tree | `b78b06b8ac650467372236a3a262864e069a9382` |
| Commit date | `2026-09-01T02:42:15+01:00` |
| SDK version | `0.10.0.43-dev.g956c6a8` |
| License | BSD-3-Clause; `LICENSE` SHA-256 `8E065BE1DA2FF9A16B1F063D4636D8B67E6A654BB90583EA4332E66AC421BB18` |

The superproject was clean. The pre-existing Windows materialization of
`thirdparty/libmspack` at Gitlink
`305907723a4e7ab2018e58040059ffb5e77db837` was preserved exactly and is not a
G1.5A change.

The official ReXGlue `v0.10.0` tag points to
`f5337cdc947ff6d4c4196737e2c807a48f2a1fc2`, tree
`93d1bc10733b23e1c16475eb5c62e3bb2a68daa1`, dated
`2026-08-20T17:17:15-04:00`. Official `main` release commit
`c94f5ebdcb3c9d1a460ca48e04f9758448f8d518` has the same tree. The diff from
the tag to the local commit is empty for `src/graphics`,
`include/rex/graphics`, the GPU ABI/runtime/UI boundary and applicable build
files. Therefore the audited GPU implementation is source-identical to the
official v0.10 GPU surface even though the local SDK contains later Fable
discovery/fault-walker work elsewhere.

The license and `src/graphics/CMakeLists.txt` identify Xenia-derived GPU code.
An exact historical Xenia source commit was not recoverable from this short
provenance chain: `UNKNOWN`. That historical unknown does not weaken the exact
identity of the current ReXGlue implementation.

## Active DLL and build provenance

The Fable Release cache selects installed SDK package
`C:\Dev\Fable2Phase4Xenia\rexglue-install-956c6a8`. Its package version is
`0.10.0.43-dev.g956c6a8`. Fable's `CMakeLists.txt` pins that version and calls
`rexglue_setup_target(fable2 GPU_PLUGINS xenos)`; the imported target staging
rule copies the DLL beside `fable2.exe`.

| Property | Active staged DLL |
|---|---|
| Path | `C:\Dev\Fable2Recomp\out\build\win-amd64-release\rexgpu-xenos.dll` |
| Package source | `C:\Dev\Fable2Phase4Xenia\rexglue-install-956c6a8\bin\rexgpu-xenos.dll` |
| Size | `2770944` bytes |
| SHA-256 | `8232051BED6E5CE99CF37B2EF581C824F58875C140A4D3C75DE14E8A5DF4AA99` |
| PE | AMD64, 7 sections, timestamp `0x6A962D91` (`2026-09-01T01:42:41Z`) |
| Image base / size | `0x180000000` / `2793472` (`0x2AA000`) |
| Entry RVA | `0x141B50` |

The package DLL, SDK build output and staged DLL have the same size and hash.
The Fable consumer is `fable2.exe`, size `105042944`, SHA-256
`EEACEAA8DB38E728B79F4F78B0298B7036E13EB4903518C503199697FA64AE6F`.

Exports are:

| Ordinal | Export | RVA |
|---:|---|---:|
| 1 | `AmdPowerXpressRequestHighPerformance` | `0x28D7F8` |
| 2 | `NvOptimusEnablement` | `0x28D7F4` |
| 3 | `rex_gpu_abi_version` | `0x1000` |
| 4 | `rex_gpu_create` | `0x1010` |

Static import modules and symbol counts are: `rexruntime.dll` 103,
`KERNEL32.dll` 45, `ole32.dll` 1, `MSVCP140.dll` 50, `VCRUNTIME140.dll` 14,
and UCRT API-set modules totalling 56 symbols. D3D12/DXGI are intentionally not
static imports: `D3D12Provider::Initialize` loads `dxgi.dll`, `D3D12.dll`,
`D3DCompiler_47.dll`, `dxilconv.dll` and `dxcompiler.dll` dynamically.

The SDK build cache has `REXGLUE_USE_D3D12=ON` and
`REXGLUE_USE_VULKAN=OFF`. Existing `fable2-run-048.log` confirms the xenos
plugin loaded and a Direct3D 12 device was created on
`NVIDIA GeForce RTX 5080`; G1.5A did not start a new title run.

## Xenia Canary reference pin

G1.5A pinned Xenia Canary at repository
`https://github.com/xenia-canary/xenia-canary.git`, branch
`canary_experimental`, commit
`3a44f20c7bc66db1da583e8a6f0ab740e31908e9`, tree
`c343b0a5796590fadc3b78c993bfada51e7e9148`, dated
`2026-08-28T20:19:01-07:00`. G1.5B verified rather than advanced that pin.

| Identity | Verified value |
|---|---|
| Local clone | `C:\Dev\Fable2NativeRendererResearch\xenia-canary` |
| Remote | `https://github.com/xenia-canary/xenia-canary.git` |
| Branch/upstream | `canary_experimental` / `origin/canary_experimental`; ahead `0`, behind `0` |
| Commit / tree | `3a44f20c7bc66db1da583e8a6f0ab740e31908e9` / `c343b0a5796590fadc3b78c993bfada51e7e9148` |
| Parent | `22708301ba76d10aae6f7d7caac8b1cac9e4a8e6` |
| Author / committer date | `2026-08-28T20:19:01-07:00` / `2026-08-31T22:07:04+02:00` |
| Subject | `[GPU] Replace AC6 ground hack with scalar approximation rounding` |
| State | clean; HEAD exactly equals the pin |
| Licence | BSD-3-Clause; `LICENSE` SHA-256 `3D58F25C15634B6EC01D1F133EF798209AE06626AB8D2227B6223D5A9F5113F4` |
| History availability | shallow clone, 200 commits; boundary `049a55f03679b204379b17996bd032ce54bff156` |

The reference clone has no applicable `AGENTS.md`. No fetch, reset, checkout,
source edit, build, or execution was performed. The shallow boundary limits
older historical rationale; it does not weaken the exact source identity at
the pin.

## G1.5B starting repository state

G1.5B started on `fable2-native-renderer-g1.5-reference` at accepted G1.5A
ending commit `a0d663fc600f74df8e7e87dcf7f18776e23339c9`, tree
`a622e93e586be117a9be0ba9b6554ef3a099636c`, with a clean worktree. The
ReXGlue SDK remained at
`956c6a8b5da4c54b9899a2593e9c67c26de30194`; its pre-existing
`thirdparty/libmspack` materialization was preserved. Paused G2A remained only
read context at `47c2ea2b7d9e14b09fd942c4b5f1bd11c46e2f51`.
