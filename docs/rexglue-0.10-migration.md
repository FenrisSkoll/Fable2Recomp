# ReXGlue v0.10.0 migration and parity handoff

Validation date: `2026-08-28`

## Outcome

**CONFIRMED:** the canonical Fable2Recomp integration has been migrated from
the audited ReXGlue v0.9.0 fork state to exact official ReXGlue `v0.10.0` plus
five explicitly recorded local fork commits. Normal non-fault-walk execution
reached controllable Bowerstone Old Town childhood gameplay, all 32 Harvest
001-003 and proven-sibling functions remained generated and registered, and no
new fatal, invalid target, host exception, assertion, or fault-walker activity
occurred.

This migration did not run a fault-walker harvest and did not begin static
entrypoint, Ghidra, jump-table, or Xenia-target discovery. No push, remote
merge, tag, release, upload, or publication of private executable material was
performed.

Evidence labels in this document have their normal project meanings:

- **CONFIRMED:** demonstrated directly by repository state, source, generated
  output, build/test output, retained runtime evidence, or hashes.
- **PROBABLE:** supported by consistent evidence but not directly exercised.
- **UNRESOLVED:** not sufficiently tested to claim a result.

## Repository and branch identities

### Fable2Recomp parent

- Repository: `C:\Dev\Fable2Recomp`
- Pre-migration branch: `fault-walker`
- Frozen parent baseline:
  `c11c60e7f9865c82623b0e07f491227ab745fed4`
  (`Document fault-walker Harvest 001-003 baseline`)
- Required migration branch: `fable2-rexglue-0.10-migration`
- Initial migration-branch commit:
  `c11c60e7f9865c82623b0e07f491227ab745fed4`
- Integration commit:
  `c8a2264500ea32a68d747808d52b7e7820c81b72`
  (`Migrate Fable2Recomp integration to ReXGlue 0.10`)
- Exact-package pin commit:
  `5620e3eafd1e6553d3bd020022a2b782c9a6955c`
  (`Pin audited ReXGlue 0.10 fork build`)
- The final documentation commit is the commit containing this file. Resolve
  it without ambiguity with
  `git log -1 --format=%H -- docs/rexglue-0.10-migration.md`.

The baseline worktree was clean. The completed Harvest 001-003 closeout was
already committed as `c11c60e7`; no extra baseline commit was needed. The
migration branch did not exist before this work and was created normally from
that exact commit without reset, deletion, or history rewriting.

### ReXGlue SDK

The integration is an installed CMake package, not a parent submodule or
vendored copy. The parent resolves `rexglueConfig.cmake` through `rexglue_DIR`.

Original 0.9 checkout:

- Path: `C:\Dev\rexglue-sdk`
- Branch: `fable2-fault-walker`
- Source HEAD: `3e61c63f3acaa37b7ac485b06d33b8a6efa5afbc`
- Installed package used by the frozen baseline:
  `C:\Dev\rexglue-sdk\out\install\win-amd64`
- Installed CLI identity: `0.9.0.2-dev.ga30cf01`
- The installed identity ended at `a30cf015`; the source branch also contained
  later dispatch-only commit `3e61c63f`. This distinction is preserved rather
  than presenting the installed package as the source HEAD.

Migration checkout:

- Path: `C:\Dev\rexglue-sdk-v0.10`
- Companion branch: `fable2-v0.10-migration`
- Base: exact official `v0.10.0`
  `f5337cdc947ff6d4c4196737e2c807a48f2a1fc2`
- Final SDK HEAD:
  `8f853c394b12cad7022086047981e861dd0efbea`
- Installed package:
  `C:\Dev\rexglue-sdk-v0.10\out\install\win-amd64`
- Installed CLI and exported CMake identity:
  `0.10.0.5-dev.g8f853c3`

Only one remote was configured in either SDK checkout:

```text
origin  https://github.com/rexglue/rexglue-sdk.git
```

That remote is official upstream. There was no separately configured fork
remote; the three 0.9 fork commits and their v0.10 descendants are local
canonical fork history. Authorship was preserved while carrying them.

The original SDK checkout was not reset or modified by the migration. Both SDK
worktrees report `m thirdparty/libmspack`: Windows materialized 15 upstream
symlinks as ordinary files. The original dirty state was preserved. In the
v0.10 worktree the same files were made buildable by copying their exact target
contents after the first compile exposed the materialized-symlink problem.
Those environmental files are not staged or committed; all SDK root commits
are otherwise clean and reviewable.

## Exact official versions and sources

The official tags are lightweight tags pointing directly at commits:

| Version | Exact commit |
| --- | --- |
| `v0.9.0` | `3eb9b511b4140d2769e27be63eae57d41bfa2afa` |
| `v0.10.0` | `f5337cdc947ff6d4c4196737e2c807a48f2a1fc2` |

The current 0.9 fork merge-base with official v0.10.0 is exact v0.9.0,
`3eb9b511b4140d2769e27be63eae57d41bfa2afa`. The ranges are:

```text
v0.9.0...3e61c63f: 0 upstream-only, 3 fork-only
v0.9.0...v0.10.0: 0 v0.9-only, 63 v0.10-only
```

Primary sources inspected:

- [official repository](https://github.com/rexglue/rexglue-sdk)
- [official v0.10.0 release](https://github.com/rexglue/rexglue-sdk/releases/tag/v0.10.0)
- [official v0.9.0...v0.10.0 comparison](https://github.com/rexglue/rexglue-sdk/compare/v0.9.0...v0.10.0)

The local tag contents, complete 63-commit range, headers, generated templates,
CMake, tests, runtime, kernel/XAM/XGI, SDL/audio/input, GPU, and platform source
were inspected rather than relying on the release summary.

Notable audit targets:

| Change | Exact upstream commit | Fable/Windows disposition |
| --- | --- | --- |
| Guest-thread lost-wakeup fix | `96bee614792ef316871a7658a211def34688cf02` | **CONFIRMED present**, but it changes `threading_posix.cpp`; Windows builds `threading_win.cpp`, so this run did not exercise it. |
| SDL audio timer policy | `f5c85215174c9dcd67b4c77227a979c4fc33197a` | **CONFIRMED present and path exercised**. It removes the forced `SDL_HINT_TIMER_RESOLUTION=0`; Fable initialized the SDL endpoint and ran audio callbacks through gameplay without a new failure. |
| `XGISessionJoinRemote` assert removal | `90e496e2bddf2ef60614dff8ec515d8fc6d4cce3` | **CONFIRMED present**. `xuid_array_ptr` now distinguishes local and remote logging without `assert_zero`. No JoinLocal/JoinRemote call appeared in Run 013, so the specific branch remains unexercised. |
| Windows DXGI/DXGUID link fix | `509ed5bffcffefbdf77ad7132db8dbc2dd570b32` | **CONFIRMED present and build-exercised** by all three Windows configurations and xenos D3D12 staging/loading. |
| macOS support | `df2743b069d0db19f8ecad2688eecb14e23e1565` | Present but not applicable to this Windows target. |
| MoltenVK xenos work | `5f5d7f6fe9ff62c57f1b7d225379b54e485fec2c` | Present; Vulkan was intentionally `OFF`, so it was not exercised. |
| Mouse/platform input refactor | `1c1f54c8fac1d44113a2d9e6882ad2707406af5c`, `b458afe56c0e28a13b09ab2503ae3ac057ce872b` | **CONFIRMED exercised** through `--mnk_mode`, calibrated selection input, and sustained gameplay input. |

Other material v0.10 surfaces include public API/header additions, CVar and
runtime lifecycle changes, value-initialized PPC thread context, removal of
`REX_WEAK_FUNC`, generated-code partitioning and PCH support, incremental
depfile/stamp codegen, object-library wiring, asynchronous Windows exception
mode, line-table-only generated debug data, Vulkan dependency refactoring, and
logging-level changes. Existing manifest syntax remains valid; v0.10 adds
configuration capabilities including register-sharing and codegen dependency
tracking without invalidating the Fable manifest.

## Frozen 0.9 baseline

### Toolchain and build configuration

- PowerShell 7 workflow on Windows
- CMake `4.4.2`
- Ninja `1.13.2`
- Clang/clang++ `22.1.8`, LLVM commit
  `ca7933e47d3a3451d81e72ac174dcb5aa28b59d1`
- Compiler target: `x86_64-pc-windows-msvc`
- MSVC tools: `14.44.35207`
- Windows SDK: `10.0.26100.0`
- Parent generator: `Ninja`, `Release`
- SDK generator: `Ninja Multi-Config`, `Debug;Release;RelWithDebInfo`
- Baseline package cache:
  `rexglue_DIR=C:/Dev/rexglue-sdk/out/install/win-amd64/lib/cmake/rexglue`
- v0.10 package cache:
  `rexglue_DIR=C:/Dev/rexglue-sdk-v0.10/out/install/win-amd64/lib/cmake/rexglue`
- `REXSDK_DIR` remained empty; package mode was used throughout.

The v0.10 SDK was configured with D3D12 enabled and Vulkan disabled. Most
third-party identities were unchanged. Exact changed/additional dependencies
were:

| Dependency | v0.9 | v0.10 |
| --- | --- | --- |
| SPIR-V Headers | `04f10f650d514df88b76d25e83db360142c7b174` | `29981f65241605e08b0ede4cfeb999fe3b723c6a` |
| SPIR-V Tools | `04d0b166dcd62e29509bf2aac3ca0c5ccdcb6929` | `9a49b0883b9b635689a85b5647dbfcb223268151` |
| Vulkan Headers | `49f1a381e2aec33ef32adf4a377b5a39ec016ec4` | `e3b1eec08173d6b825cd3ac88c885a63b621504a` |
| Vulkan Loader | absent | `5f157b62e333c63260d05d81bf66faa216ab0fb8` |
| MoltenVK | absent | `db445ff2042d9ce348c439ad8451112f354b8d2a` |
| Snappy | `6af9287fbdb913f0794d0148c6aa43b58e63c8e3` | removed |

Unchanged important pins include SDL3
`8bf3b7215ad9fc3deb583c6a3a37c6c67f2e24e4`, FFmpeg
`0604b464c7cb4ebc94940cf1f324a3b26b87717c`, fmt
`407c905e45ad75fc29bf0f9bb7c5c2fd3475976f`, inja
`7d1b4600b68595085a949743331c2e5673f511ea`, libmspack
`305907723a4e7ab2018e58040059ffb5e77db837`, and xxHash
`e626a72bc2321cd320e953a0ccf1584cad60f363`.

### TU1 and configuration identity

- Target: Fable II Game of the Year Edition, Xbox 360 TU1
- Title ID: `4D5307F1`
- Media ID: `716F0A0D`
- Base version: `0.0.0.26`
- Patched version: `0.0.1.26`
- Patched file time: `2009-07-07 22:12:42 UTC`
- Base XEX: `assets\tu1\default.xex`
- Base XEX SHA-256:
  `88C4EF2E18E65409444D1B068EFF921D1F7E180A5AE64EDC64BA6B0872372662`
- TU1 patch: `assets\tu1\default.xexp`
- TU1 patch SHA-256:
  `046A05693B4DA4437083C784000A850858B3BF992955C7DB30D518FB3E53E41C`
- Loaded image base: `0x82000000`
- Analyzer executable ranges: `.text [0x82170000,0x832BAC00)` and
  `BINK [0x832BAC00,0x832CA200)`

Baseline hashes:

| File/output | SHA-256 |
| --- | --- |
| `fable2_manifest.toml` | `119D239E1A631E5CE7DC4368FB7C6DC008D41C2208A08EC3717963B3502F8948` |
| `CMakeLists.txt` | `1DC100710263CD55392864AE7642DA7DBC43338D785A24F0665E6949DB2B8D1A` |
| `CMakePresets.json` | `7968388DB02F161438AAF23C780EB25977204A67FA80D916FECDC6CBEBC7C2BD` |
| `generated/rexglue.cmake` | `583DE712ECF9BD130ADA21B5DA55B85F4A1648F5B3E5682B2BD68EEA895E2F1A` |
| generated v0.9 tree, 152 files / 313,737,070 bytes | `0B8DE9DEF7D52DAC43A5001F1E6A420A06C9D1092336DF24885ADCFA50BDE1A3` |

The frozen baseline codegen was run before branching and produced a
byte-identical generated tree. It contained 60,416 `DEFINE_REX_FUNC` bodies
and 60,416 dispatcher registrations. Runtime setup registered 60,908 total
recompiled/runtime functions with zero duplicates and zero rejected in both
Run 011 and Run 013.

### Baseline tests and runtime

- SDK focused fault-walk build: no work, `0.114 s`
- SDK `ctest --preset win-amd64-release -L fault_walk --output-on-failure`:
  `3/3` passed in `0.132 s`
- `fable2-codegen`: passed in `43.275 s`
- normal release build: passed in `52.343 s` (incremental after regeneration;
  not a clean-build comparison)
- DISPATCH_ONLY release build: passed in `100.732 s`
- FULL release build: passed in `113.081 s`

Frozen normal evidence:

- Log: `C:\Dev\Fable2Recomp\fable2-run-011.log`
- Length: `628249`
- SHA-256:
  `7DAA59086F83E416951CF87C6B4DC6CE5F3C65C09AE2106F03A40A06E718F1CB`
- Mode: OFF / normal non-fault-walk
- Milestone: coherent controllable Bowerstone Old Town childhood gameplay
- Exit: graceful, `0x00000000`
- `[FWT]`: none
- `[FATAL]`: none
- Invalid/unregistered dispatch: none

The authoritative prior ledger and its forensic classifications remain in
[`docs/fable2-fault-walker-baseline.md`](fable2-fault-walker-baseline.md).

## Fork-patch ledger

No original fork patch was dropped and none had an upstream-equivalent patch in
v0.10.0.

| Original 0.9 commit | v0.10 commit | Classification | Disposition |
| --- | --- | --- | --- |
| `e464cb3bcf20da4531ae4f909735dae8dd459505` | `e45db0fedc9bc62c63757c8dc480572bcbdbb516` | `still_required_unchanged` | Invalid-call diagnostics retained. Stable patch ID is identical: `deaa95dccf9a482287ca1b30826118142ce6689d`. |
| `a30cf01507854df7fa55c2bd8646a64132515144` | `4b3e08caedce0943dcc680d2bac9149394641bfa` | `still_required_but_needs_port` | Fault walker retained; generated wrapper hooks moved into v0.10 `pch_h.inja` while preserving the new thin init/template split and Apple weak-thunk form. |
| `3e61c63f3acaa37b7ac485b06d33b8a6efa5afbc` | `2ba63a7c439b0d016a0ebd8bf16baea3ddb745b1` | `still_required_unchanged` | Preferred DISPATCH_ONLY mode retained. Stable patch ID is identical: `2ceefeb68b172617b9f5c748c5a543a4ce51eedf`. |

Additional migration commits:

| Commit | Purpose | Classification |
| --- | --- | --- |
| `4fa3da1616e052971aebe47286035b7a81909b81` | Ports fault-walker/test weak aliases after upstream removed `REX_WEAK_FUNC`; preserves v0.10 explicit linkage syntax. | `still_required_but_needs_port`, completed |
| `8f853c394b12cad7022086047981e861dd0efbea` | Makes the public `rex/hash.h` xxHash dependency public and corrects invalid C++ escapes in v0.10 depfile tests. | `conflicts_with_upstream` test/package defect, fixed; plausible upstream-quality, not Fable-specific |

The final SDK pin is therefore exact official
`f5337cdc947ff6d4c4196737e2c807a48f2a1fc2` plus, in order:

```text
e45db0fedc9bc62c63757c8dc480572bcbdbb516
4b3e08caedce0943dcc680d2bac9149394641bfa
2ba63a7c439b0d016a0ebd8bf16baea3ddb745b1
4fa3da1616e052971aebe47286035b7a81909b81
8f853c394b12cad7022086047981e861dd0efbea
```

## Migration changes

### SDK files and APIs

The carried commits affect:

- `src/system/function_dispatcher.cpp`: exact target/LR/caller/CTR invalid-call
  diagnostics and dispatch fault-walk hook
- `include/rex/fault_walk.h`, `src/system/fault_walk.cpp`: OFF,
  DISPATCH_ONLY, and FULL state/recovery/reporting
- `resources/templates/codegen/pch_h.inja`: FULL generated-function wrappers,
  setjmp/longjmp capture/completion, and v0.10 weak linkage compatibility
- `resources/templates/test/ppc_config_h.inja`: test wrapper compatibility
- `src/codegen/function_graph.cpp`: generated fault-walk participation
- `tests/fault_walk/*`: enabled, disabled, and dispatch-only synthetic tests
- `src/system/CMakeLists.txt`: fault-walk runtime source and public xxHash
  transitive dependency
- `tests/unit/codegen/output_stamp_test.cpp`: literal backslashes that actually
  exercise escaped spaces and `#` in depfiles

No Xbox kernel, filesystem, graphics, audio, input, or XAM behavior was locally
reimplemented to bypass v0.10.

### Parent files

Commit `c8a22645` changes exactly:

- `fable2_manifest.toml`: generated header and `sdk_version` from `0.9.0` to
  `0.10.0`; all TU1 and explicit-function data preserved
- `generated/rexglue.cmake`: official/fork v0.10 generated project template,
  including exact v0.10 package discovery, generated OBJECT library/PCH,
  async Windows exception mode, line-table-only generated debug info, and
  depfile/stamp incremental codegen
- `CMakeLists.txt`: applies FULL instrumentation to the new `fable2_recomp`
  OBJECT target as well as the host
- `CMakePresets.json`: isolated v0.10 normal, DISPATCH_ONLY, and FULL build
  directories without overwriting the 0.9 builds
- `tools/Verify-Fable2MigrationLedger.py`: deterministic manifest, body,
  declaration, mapping, registration, overlap, non-local-jump, and
  `0x82E8C8E8` semantic validation

Commit `5620e3ea` adds an exact exported-package check in `CMakeLists.txt`:

```text
FABLE2_REXGLUE_VERSION_STRING=0.10.0.5-dev.g8f853c3
```

This enforces the audited v0.10.0-plus-five-commit package while leaving its
filesystem location configurable. A different 0.10 build is rejected rather
than silently accepted.

Final tracked-input hashes before this document:

| File | SHA-256 |
| --- | --- |
| `fable2_manifest.toml` | `E3EB39CA153E396D5DC53E6F943ED8FF7AF1D6B0704EB860836BD7D21A3F87B0` |
| `CMakeLists.txt` | `69F02BB8902A11910CA9F0AB2D4420CDD18EF9179001B9D135DB42D7D5C88602` |
| `CMakePresets.json` | `D65B687B5B531B493415FE353E5FF0DAB3A4AECAC402302DE7FEB75F0C93473B` |
| `generated/rexglue.cmake` | `A2252FFCFE7D09E30095E408C18920F1B05047B6BA82F046B4BFF538BA8B2FC6` |

## Regeneration and executable identity

The first v0.10 regeneration used the same private XEX/XEXP hashes above and
reported the same title, media, file time, and exact
`0.0.0.26 -> 0.0.1.26` patch transition. It wrote 592 files, left one
unchanged, deleted none, and completed analysis/codegen in `50.430 s`.

The v0.10 generated layout is intentionally more highly partitioned:

| Set | Files | Bytes | Deterministic tree SHA-256 |
| --- | ---: | ---: | --- |
| `.cpp`, `.h`, `.cmake` | 592 | 318,051,458 | `7FB9F55E91CC9A21944F32250785C2B5C055C8FB852DFFDF2157F6D47172120B` |
| Complete generated directory | 596 | 319,318,650 | `83027E123703C635D652DF96283FDE09740C4CFABB52139C8F921BD7BB083A56` |

Semantic counts are unchanged:

```text
DEFINE_REX_FUNC definitions: 60416
generated declarations:      60416
PPCFuncMappings:              60416
SetFunction registrations:   60416
runtime registrations:       60908 (0 duplicates, 0 rejected)
```

Fresh isolated outputs:

| Mode | Preset | Size | SHA-256 |
| --- | --- | ---: | --- |
| OFF / normal | `win-amd64-rexglue-0.10-release` | 105,045,504 | `3140A5D8150F189086B7EBF75FE040A9D07CE505759869C5F59843BA0019E8F5` |
| DISPATCH_ONLY | `win-amd64-rexglue-0.10-fault-walk-dispatch-release` | 105,045,504 | `4DC84FB22EA4AF488CCAF951AC1F16719BFD5BEB50C8374F874A28DA6E2033F2` |
| FULL | `win-amd64-rexglue-0.10-fault-walk-release` | 109,618,688 | `07BC9356794670F29A23E4A8FC161391EEB7DBEF044EF24E659F364D7C2B00C7` |

Compile-command inspection confirmed `REXGLUE_ENABLE_FAULT_WALK=1` on generated
FULL source, including the partition containing `sub_82E8C8E8`, and confirmed
it absent in DISPATCH_ONLY. Both modes use the v0.10 PCH, async exception mode,
and expected generated-code flags.

## Harvest 001-003 regression ledger

All entries below are **CONFIRMED TU1 boundaries** and exact manifest entries.
`tools/Verify-Fable2MigrationLedger.py` found a manifest record, real
`DEFINE_REX_FUNC` body, declaration, mapping, and `SetFunction` dispatcher
registration for every row, with no overlap. `PASS` means all five checks
passed on v0.10. Full semantic evidence and original caller/LR information are
retained in the authoritative baseline document linked above.

| Group | Range | Size | Exact manifest entry | v0.10 |
| --- | --- | --- | --- | --- |
| 001 | `[0x82C03B28,0x82C03B44)` | `0x1C` | `"0x82C03B28" = { size = 0x1C }` | PASS |
| 001 | `[0x829647F0,0x82964800)` | `0x10` | `"0x829647F0" = { size = 0x10 }` | PASS |
| 001 | `[0x829675E0,0x829675F0)` | `0x10` | `"0x829675E0" = { size = 0x10 }` | PASS |
| 002 | `[0x829675D0,0x829675E0)` | `0x10` | `"0x829675D0" = { size = 0x10 }` | PASS |
| 002 | `[0x829675C0,0x829675D0)` | `0x10` | `"0x829675C0" = { size = 0x10 }` | PASS |
| 002 | `[0x8288ACB0,0x8288ACC0)` | `0x10` | `"0x8288ACB0" = { size = 0x10 }` | PASS |
| 002 | `[0x8288ACC0,0x8288ACD0)` | `0x10` | `"0x8288ACC0" = { size = 0x10 }` | PASS |
| 002 | `[0x82964820,0x82964830)` | `0x10` | `"0x82964820" = { size = 0x10 }` | PASS |
| 002/003 | `[0x82C8A920,0x82C8A93C)` | `0x1C` | `"0x82C8A920" = { size = 0x1C }` | PASS |
| 002/003 | `[0x82967540,0x82967550)` | `0x10` | `"0x82967540" = { size = 0x10 }` | PASS |
| 002/003 | `[0x82DE2BA8,0x82DE2BC4)` | `0x1C` | `"0x82DE2BA8" = { size = 0x1C }` | PASS |
| 003 | `[0x82E8C8E8,0x82E8C92C)` | `0x44` | `"0x82E8C8E8" = { size = 0x44 }` | PASS |
| sibling | `[0x82C00A98,0x82C00AA8)` | `0x10` | `"0x82C00A98" = { size = 0x10 }` | PASS |
| sibling | `[0x826EE730,0x826EE740)` | `0x10` | `"0x826EE730" = { size = 0x10 }` | PASS |
| sibling | `[0x82964800,0x82964810)` | `0x10` | `"0x82964800" = { size = 0x10 }` | PASS |
| sibling | `[0x82964810,0x82964820)` | `0x10` | `"0x82964810" = { size = 0x10 }` | PASS |
| sibling | `[0x82967530,0x82967540)` | `0x10` | `"0x82967530" = { size = 0x10 }` | PASS |
| sibling | `[0x82967550,0x82967560)` | `0x10` | `"0x82967550" = { size = 0x10 }` | PASS |
| sibling | `[0x82967570,0x82967580)` | `0x10` | `"0x82967570" = { size = 0x10 }` | PASS |
| sibling | `[0x82967580,0x82967590)` | `0x10` | `"0x82967580" = { size = 0x10 }` | PASS |
| sibling | `[0x82967590,0x829675A0)` | `0x10` | `"0x82967590" = { size = 0x10 }` | PASS |
| sibling | `[0x829675A0,0x829675B0)` | `0x10` | `"0x829675A0" = { size = 0x10 }` | PASS |
| sibling | `[0x8305DA68,0x8305DA78)` | `0x10` | `"0x8305DA68" = { size = 0x10 }` | PASS |
| sibling | `[0x8305DA78,0x8305DA88)` | `0x10` | `"0x8305DA78" = { size = 0x10 }` | PASS |
| sibling | `[0x8305DA88,0x8305DA98)` | `0x10` | `"0x8305DA88" = { size = 0x10 }` | PASS |
| sibling | `[0x8305DA98,0x8305DAA8)` | `0x10` | `"0x8305DA98" = { size = 0x10 }` | PASS |
| sibling | `[0x8305DAA8,0x8305DAB8)` | `0x10` | `"0x8305DAA8" = { size = 0x10 }` | PASS |
| sibling | `[0x8305DAB8,0x8305DAC8)` | `0x10` | `"0x8305DAB8" = { size = 0x10 }` | PASS |
| sibling | `[0x8305DAC8,0x8305DAD8)` | `0x10` | `"0x8305DAC8" = { size = 0x10 }` | PASS |
| sibling | `[0x8305DAD8,0x8305DAE8)` | `0x10` | `"0x8305DAD8" = { size = 0x10 }` | PASS |
| sibling | `[0x8305DAE8,0x8305DAF8)` | `0x10` | `"0x8305DAE8" = { size = 0x10 }` | PASS |
| sibling | `[0x8305DAF8,0x8305DB08)` | `0x10` | `"0x8305DAF8" = { size = 0x10 }` | PASS |

The three required fixtures retain their established interpretations:

- `[0x829647F0,0x82964800)`, size `0x10`: `r3` virtual-dispatch leaf thunk,
  slot `0x4C`
- `[0x82C03B28,0x82C03B44)`, size `0x1C`: conditional callback leaf reached
  through callback-table `bctrl`
- `[0x829675E0,0x829675F0)`, size `0x10`: `r3` virtual-dispatch leaf thunk,
  slot `0xB4`

### `0x82E8C8E8` return semantics

**CONFIRMED:** `[0x82E8C8E8,0x82E8C92C)`, size `0x44`, is a boolean search
predicate. Its generated v0.10 body returns `1` on a matching entry and `0`
only for empty/no-match completion. The verifier checks both return paths and
the loop structure. It is a real 17-instruction body, not a synthetic return.

The prior `RETURN_R3_ZERO` fault action forced every call down the no-match
path, prevented intended state progress, and caused the exact guardrail stop:

```text
per-function suppression limit reached for invalid target 0x82E8C8E8 (250000)
```

Run 013 contained no FWT line and no address mention for `0x82E8C8E8`; the
artificial 250,000-call loop did not recur.

## Compatibility checks

### setjmp/longjmp and Lua control flow

The exact manifest mappings remain:

```text
setjmp_address  = 0x83006C90
longjmp_address = 0x82CAFA30
```

Generated v0.10 output contains `ppc_setjmp` and `ppc_longjmp` call sites and
the PCH retains `FaultWalkCaptureSetjmp` / completion integration in FULL mode.
The FULL synthetic test passed its host exception, divide, and longjmp wrapper
reconciliation paths. Normal Run 013 progressed through script-driven startup
and gameplay with no native C++ escape, fatal, or host exception. Therefore the
restored non-local-jump mapping remains **CONFIRMED present and functional for
the exercised path**; no attempt was made to replace it with ordinary calls.

### GPU, input, audio, window, and storage

- `rexgpu-xenos.dll` was built, staged, selected by `--gpu_plugin=xenos`, and
  loaded successfully.
- The same NVIDIA GeForce RTX 5080 adapter (`vendor 0x10DE`, `device 0x2C02`)
  and D3D12 feature path initialized.
- Both runs registered 60,908 functions with zero duplicate/rejected entries.
- SDL `3.5.0` initialized. The v0.10 run selected
  `Beyond TV (NVIDIA High Definition Audio)`, 2 channels, 48 kHz, and delivered
  audio callbacks without a new assertion or failure.
- MnK input initialized. The calibrated selection sequence and a sustained
  one-second D-Pad-left input were foreground-verified; the latter changed the
  player/camera state and exposed the objective-trail tutorial.
- `assets\runtime`, `assets\update`, achievements, profile settings, and
  content enumeration remained operational.
- Window close produced `Window closing, shutting down...` followed by
  `Title terminated; hard-exiting process.` and exit `0x00000000`.

### Fault-walker modes

- OFF normal, preferred DISPATCH_ONLY, and FULL all configure and link.
- DISPATCH_ONLY remains separately selectable with
  `REXGLUE_ENABLE_FAULT_WALK_DISPATCH=ON`.
- FULL remains separately selectable with
  `REXGLUE_ENABLE_FAULT_WALK=ON`, including generated OBJECT code.
- Synthetic enabled/FULL, disabled/OFF, and dispatch-only tests pass.
- No test, guardrail, rollback warning, or fault-walker action was weakened or
  removed.
- No FULL gameplay run and no new harvest was performed during migration.

## Commands and results

### SDK configure, build, install, and tests

```powershell
cmake --preset win-amd64
cmake --preset win-amd64 -DREXGLUE_BUILD_TESTS=ON
cmake --build --preset win-amd64-release
cmake --install .\out\build\win-amd64 --config Release
ctest --preset win-amd64-release --output-on-failure -j 8
```

Results:

- Fresh SDK configure: pass, `65.082 s`
- SDK default Release build after resolving the local materialized-symlink
  checkout: pass, `43.315 s`
- Focused test-target build: pass, `60.700 s`
- Install: pass, `5.191 s`
- Final complete CTest: `1674/1674` passed, `7.250 s`
- Test composition: 213 unit tests, 3 fault-walk synthetic tests, 1,458 PPC
  tests
- Four known `BitStream::Write` cases explicitly reported Catch2 SKIP because
  the upstream write implementation is marked broken; they are not failures:
  `unit.BitStream Write non-byte-aligned`,
  `unit.BitStream Write byte-aligned`,
  `unit.BitStream Write preserves surrounding bits`, and
  `unit.BitStream Write 16-bit value`.
- A stale `LastTestsFailed.log` names the depfile-literal failure from before
  commit `8f853c3`; its timestamp predates the final successful run and it is
  not a current result.

### Parent configure, codegen, builds, and checks

The exact installed SDK path was supplied explicitly on first configure; the
exported identity check then pins the commit independently of that path.

```powershell
cmake --preset win-amd64-rexglue-0.10-release `
    -Drexglue_DIR=C:/Dev/rexglue-sdk-v0.10/out/install/win-amd64/lib/cmake/rexglue
cmake --build --preset win-amd64-rexglue-0.10-release --target fable2_codegen
cmake --build --preset win-amd64-rexglue-0.10-release

cmake --preset win-amd64-rexglue-0.10-fault-walk-dispatch-release `
    -Drexglue_DIR=C:/Dev/rexglue-sdk-v0.10/out/install/win-amd64/lib/cmake/rexglue
cmake --build --preset win-amd64-rexglue-0.10-fault-walk-dispatch-release

cmake --preset win-amd64-rexglue-0.10-fault-walk-release `
    -Drexglue_DIR=C:/Dev/rexglue-sdk-v0.10/out/install/win-amd64/lib/cmake/rexglue
cmake --build --preset win-amd64-rexglue-0.10-fault-walk-release

python .\tools\Verify-Fable2MigrationLedger.py
ctest --test-dir .\out\build\win-amd64-rexglue-0.10-release `
    -C Release --output-on-failure
```

Results:

- Normal configure: pass, `1.837 s`
- Initial v0.10 codegen: pass, `50.430 s`
- Fresh normal build: pass, `119.702 s`
- DISPATCH_ONLY configure/build: pass, `1.831 s` / `121.055 s`
- FULL configure/build: pass, `1.855 s` / `124.348 s`
- Final incremental codegen: pass, module up to date, `0.266 s`
- Final no-op normal/DISPATCH_ONLY/FULL builds: pass, approximately `0.27 s`
  each
- Ledger verifier: `PASS`, all 32 rows and all 60,416 semantic counts
- Parent CMake has no CTest preset. The attempted preset command correctly
  reported `No such test preset`; direct configured-directory CTest returned
  `0` with `No tests were found`. Tests are supplied and run by the SDK.

### Normal runtime parity

Command:

```powershell
.\tools\Invoke-Fable2BringUpIteration.ps1 `
    -Iteration 2 `
    -RunDirectory .\out\rexglue-0.10-normal-validation `
    -BuildPreset win-amd64-rexglue-0.10-release `
    -SkipCodegen `
    -SkipBuild `
    -MonitorSeconds 240 `
    -ManualInput `
    -GracefulStop
```

The first automated attempt was Run 012 and stopped before input because a
different window had focus. Its exact classification was
`InputAutomationFailure`, with
`The Fable II window is not foreground.` No guest fatal occurred. This was an
environmental input-focus failure, not a ReXGlue regression.

Run 013 used the same calibrated sequence after explicit window activation:
three Xbox A presses, a six-second wait, D-Pad left, and a final Xbox A press.
Every injected press reported `ForegroundVerified=True`. After gameplay was
visible, an additional one-second D-Pad-left press also reported
`ForegroundVerified=True` and produced direct control evidence.

Retained Run 013 evidence:

| Artifact | Length | SHA-256 |
| --- | ---: | --- |
| `fable2-run-013.log` | 947,240 | `BAB33B24A0465D43770F62EC0BEF352A791EE8B64038F80F2288F9ED71F78296` |
| `out\rexglue-0.10-normal-validation\iteration-02\result.json` | 1,446 | `ADBD2C1FAEBBAEF0B4E541C7C6160600529430E43D44181287B7B8AD04B03162` |
| `current-state.png` | 2,872,856 | `DAB9F4392DC585A4D8DDEAC3020680D7227F6E62C68C2C4022E020057DCE3FE4` |
| `final-state.png` | 7,830,092 | `A242E4DD60F599F01E9A0776F65773AF950364652CA0AD474CB68D82FB88635E` |
| `post-control-state.png` | 7,606,279 | `CEE59CDE895742B9EA384567AF758DEF29397743A626757BF137B8802E955812` |

Result:

- Mode: OFF / normal non-fault-walk
- Classification: `PostInputTimeout` after the requested observation window,
  followed by graceful stop
- Exit: `0x00000000`
- Same GOTY TU1 identity and successful patch transition
- Observable milestone: controllable Bowerstone Old Town childhood gameplay
- Direct control evidence: changed player/camera state and objective-trail UI
- `[FWT]`: 0
- `[FATAL]`: 0
- Invalid/unregistered function: 0
- Host AV/divide exception: 0
- Assertion: 0
- `0x82E8C8E8` synthetic hot loop: absent
- All 32 ledger addresses: zero mentions in the complete Run 013 log

The runtime loaded-image dump is a live capture, not a replacement hash for the
source XEX/XEXP. Run 012 captured baseline-known hash
`5A6ADBDA1714AABC63BD7F6D52B55BCAAAD9B6F3F81907D93C1FFE830B22E59F`;
Run 013 captured
`D62B59EFC8AD96BC262E85DABAD8825929FAF4961ACD3FCDA715A2B2951D1AC9`.
The difference reflects capture timing after guest writes; codegen and both
runtime logs independently confirm the same source hashes, title/media,
version, image/ranges, and patch success.

## 0.9 versus 0.10 behavior

The complete ordered warning/error/fatal streams were parsed after removing
only timestamps and host thread IDs.

| Level | Run 011 / v0.9 | Run 013 / v0.10 |
| --- | ---: | ---: |
| warning | 14 | 14 |
| error | 3,856 | 3,856 |
| critical | 0 | 0 |
| fatal | 0 | 0 |

The message multiset is exactly identical. All 3,856 errors are the established
bounded `BaseHeap::AllocFixed attempting to reserve an already reserved range`
search that subsequently succeeds. The same 14 warnings comprise the missing
controller database, attempted `D:\lhdebug.log` write, optional build/episodic
and language probes, and one extended GPU register warning.

The ordered sequences differ only at index 3,862: in v0.9 the GPU extended
register warning precedes the seven language-file probes; in v0.10 it follows
them. No message was added or removed. This is classified
`environment_or_nondeterministic_difference`, consistent with asynchronous GPU
and guest filesystem threads.

Other classified differences:

- `expected_migration_change`: several startup/mount/runtime messages move from
  INFO to DEBUG in v0.10; command-line debug logging retained their visibility.
- `expected_migration_change`: v0.10 adds guest-arena and codegen-config
  diagnostics and emits an SDL audio-endpoint line.
- `expected_migration_change`: generated files are split into 293 recompilation
  translation units and a PCH/object library instead of the v0.9 monolithic
  partitioning.
- `confirmed_0.10_improvement`: none claimed from one runtime sample.
- `confirmed_0.10_regression`: none found.
- `fork_patch_porting_error`: none found.
- `stale_generated_or_build_artifact`: ruled out by fresh build directories,
  exact package identity, regeneration, semantic counts, and no-op reruns.
- `unresolved`: XGI remote-join behavior and POSIX lost-wakeup behavior were not
  exercised by this Windows milestone; Vulkan/MoltenVK was out of scope.

## Performance and size observations

| Measurement | v0.9 | v0.10 | Delta | Qualification |
| --- | ---: | ---: | ---: | --- |
| Codegen/analyzer | 43.275 s | 50.430 s | +16.534% | Same patched TU1 input; repeatable initial regeneration |
| DISPATCH_ONLY build | 100.732 s | 121.055 s | +20.175% | Separate release directories |
| FULL build | 113.081 s | 124.348 s | +9.964% | Separate release directories |
| Normal build | 52.343 s | 119.702 s | +128.688% | **Not comparable**: v0.9 was incremental, v0.10 was fresh |
| Normal executable | 195,810,304 | 105,045,504 | -46.353% | Primarily v0.10 line-table-only generated debug data/build layout |
| DISPATCH_ONLY executable | 102,764,032 | 105,045,504 | +2.220% | Comparable mode |
| FULL executable | 107,328,000 | 109,618,688 | +2.134% | Comparable mode |
| Generated source bytes | 313,737,070 | 318,051,458 | +1.375% | 152 v0.9 files versus 592 v0.10 source/config files |
| Final incremental codegen | n/a | 0.266 s | n/a | Module up to date |
| Fault-walk disabled runtime overhead | n/a | not independently measured | n/a | OFF compile commands contain neither fault-walk define; normal and dispatch executables have identical length, but that is not a runtime benchmark |

Cached shader initialization was comparable but not treated as a benchmark:
v0.9 translated 176 shaders in 11 ms and created 403 pipelines in 65 ms;
v0.10 reported 8 ms and 27 ms. Cache/OS scheduling makes a single sample
nondeterministic, so no improvement claim is made.

At a late Run 013 screenshot the process had accumulated `432.15625 s` CPU,
working set `1,156,018,176` bytes, and private bytes `2,177,581,056`. No
equivalent timestamped v0.9 process sample exists, so this is retained as a
future reference and not a comparison. The user reported no new audio symptom;
no automated audio-quality metric exists.

## Final state, limitations, and safe continuation

### Confirmed

- Exact official `v0.10.0` is the SDK merge base and final dependency base.
- All three local 0.9 fork patches are retained with provenance.
- Required v0.10 ports and two focused SDK/test fixes are committed.
- Parent CMake rejects any installed SDK other than
  `0.10.0.5-dev.g8f853c3`.
- Same private GOTY TU1 XEX/XEXP and exact patch transition were used.
- Image base, executable ranges, manifest functions, and non-local jumps remain
  intact.
- All 32 Harvest/complete-sibling ledger functions have real generated bodies
  and registrations.
- Normal, DISPATCH_ONLY, and FULL builds pass; SDK tests pass.
- Normal gameplay parity through controllable Bowerstone Old Town is
  established.
- No new runtime blocker or 250,000-call synthetic-return loop appeared.

### Limitations and unresolved hypotheses

- No broad manual gameplay beyond the established milestone was attempted.
- `XGISessionJoinRemote`, POSIX threading, and Vulkan/MoltenVK changes remain
  unexercised, as classified above.
- Run 012's foreground failure was environmental. It caused no guest failure
  and was superseded by foreground-verified Run 013.
- Runtime loaded-image capture hashes can differ after guest writes; the
  private source hashes and codegen patch identity are the reproducible input
  authority.
- The nested libmspack Windows symlink materialization remains visible as a
  dirty submodule in both SDK worktrees; no SDK source commit is dirty.
- The existing unresolved candidate `[0x8305DA48,0x8305DA68)` remains exactly as
  documented in the fault-walker baseline. Migration did not promote it.

At handoff, the parent branch is expected clean after committing this document.
The SDK branch has no uncommitted root-source change apart from the explicitly
described nested libmspack materialization. No raw XEX, XEXP, byte-equivalent
image, bulky log, trace, screenshot, or build output is tracked by the
migration commits.

No `git push`, remote merge, tag, release, release asset, pull request, or
external upload occurred.

Because v0.10 parity is established, the next safe action in a fresh chat is
the static entrypoint-closure prompt. Start from parent branch
`fable2-rexglue-0.10-migration` after the documentation commit and SDK branch
`fable2-v0.10-migration` at exact
`8f853c394b12cad7022086047981e861dd0efbea`. Re-run
`python .\tools\Verify-Fable2MigrationLedger.py` before making discovery
changes. Do not start Harvest 004 implicitly.
