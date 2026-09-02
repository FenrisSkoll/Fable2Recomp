# Fable II native-save write-parity checkpoint

## Status and stop boundary

This checkpoint prepares a single isolated runtime capture that can answer the
first outstanding question: after content creation, does the TU1 guest attempt
to create or write the missing `Hero000` payload files?

Native-save parity is **not** claimed. A fresh native slot has not yet been
created, restarted, enumerated, loaded, or updated with this build. Interactive
runtime validation stops at the user save trigger.

## Exact provenance

### Fable2Recomp

- Repository: `C:\Dev\Fable2Recomp`
- Verified starting branch: `main`
- Verified starting commit:
  `0c3d452e6bde5773743e67c041812ad2e333db45`
- Verified starting tree:
  `fcf2dbfd5c54cd57633e7c8e1b6b4a75c1a1077b`
- Working branch: `fable2-native-save-write-parity`
- Native-save workflow commit:
  `ecc81424f9d8663b0ae0af98f14df60040bdc6b4`
- Final ReXGlue SDK pin commit:
  `1d8bc00ba54900ece279957d6ae500b4fa6067ab`
- The final checkpoint commit is the commit containing this document. Resolve
  it with `git rev-parse HEAD` after checkout.

The verified starting commit was also `origin/main`, `main`, and the immutable
`phase4-evidence-2026-09-02` tag. No Phase 4 branch, tag, release, archive,
collector output, or final report was modified.

### ReXGlue

- Repository: `C:\Dev\rexglue-sdk-v0.10`
- Verified starting branch: `fable2-v0.10-migration`
- Verified starting commit:
  `956c6a8b5da4c54b9899a2593e9c67c26de30194`
- Verified starting tree:
  `b78b06b8ac650467372236a3a262864e069a9382`
- Working branch: `fable2-native-save-write-parity`
- Native-save diagnostics commit:
  `1f4bda8ba5dc60df063174595bb7575bce4e21df`
- Parallel filesystem-test isolation commit:
  `e2ffe70a41dcebbbcd8fb2dd6f1a185173154918`
- Parallel save-trace-test isolation commit:
  `39a35ab3d60dac6f2ba3f41515d0790b58b9b3d5`
- Current tree:
  `a36d189cf5b16042a1a907476b52cac14b3d96d3`
- Installed SDK identity: `0.10.0.46-dev.g39a35ab`
- Installed package root:
  `C:\Dev\rexglue-sdk-v0.10\out\install\win-amd64-native-save`

The pre-existing modified `thirdparty/libmspack` submodule was preserved and
excluded from the ReXGlue commit. Its nested worktree still has the same 15
modified files under `cabextract/mspack/`.

### Xenia Canary comparison reference

- Repository: `C:\Dev\Fable2Phase4Xenia\xenia-canary`
- Branch: `fable2-indirect-target-collector`
- Commit: `32460b5d887dcde6622bb17983b70752fa5f13b3`
- Tree: `114cb589291e2c87fcbcabc949a730ca5d1f6cad`
- Worktree was clean and remained read-only.

### Target executable

- Title: Fable II Game of the Year Edition, Xbox 360 TU1
- Title ID: `0x4D5307F1`
- Media ID: `0x716F0A0D`
- Base version: `0.0.0.26`
- Patched version: `0.0.1.26`
- Image base: `0x82000000`
- Executable range: `[0x82170000,0x832D0000)`
- Contiguous loaded post-patch image SHA-256:
  `BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00`

## Private-data safety and isolated states

The following originals were inventoried read-only and were never used as a
writable root:

- `C:\Users\Fenris\Documents\fable2.backup`
- `C:\Dev\Fable2XeniaSaves`

The first contains only the known partial native slot: an 8-byte
`Hero000\saveuid.bin` and a 328-byte `Hero000.header`, both timestamped
`2026-08-27 13:40:26`. The second retains the Xenia profile XUID
`E03000002168622D` and a 40,960-byte Xenia `Hero000.header` at
`content\E03000002168622D\4D5307F1\Headers\00000001\Hero000.header`.
`executable_addr_flags.bin` was excluded as unrelated cache data.

All writable states are below this ignored root:

```text
C:\Dev\Fable2Recomp\out\native-save-diagnostic
```

Prepared states:

| State | Exact root | Prepared contents | Intended future use |
| --- | --- | --- | --- |
| A | `...\A-empty` | 0 files, 0 directories | immutable empty baseline |
| B | `...\B-fresh-native` | 0 files, 0 directories | tomorrow's fresh native attempt |
| C | `...\C-xenia-copy` | isolated reference snapshot | Xenia-origin payload in confirmed native-loadable layout |
| D | `...\D-xenia-update` | independent copy of C | later native update-in-place attempt |

State C was copied from the already confirmed native-loadable working tree at
`C:\Users\Fenris\Documents\fable2`; it contains the seven Xenia-origin payload
files under the native XUID plus a 328-byte ReXGlue header. It is not a direct
copy of Xenia's profile/content root. State D is the only future writable copy.
The source tree's timestamps were rechecked after preparation and were not
changed.

The baseline and reference reports are ignored, payload-free inventories:

```text
out\native-save-diagnostic\state-A-before.json
out\native-save-diagnostic\state-C-reference.json
```

They contain relative paths, sizes, SHA-256 values, nanosecond mtimes, and
modification order, but never file contents.

## Prior runtime evidence

The preserved `fable2-run-001.log` is not a new run. It records:

- line 3: user data `C:\Users\Fenris\Documents\fable2`;
- line 5333: `XamContentCreateEnumerator: added 1 items to enumerator`;
- lines 5334-5336: profile settings `63E83FFF`, `63E83FFE`, `63E83FFD`;
- lines 5380-5381: ordinal `0271`, `XamContentCreateInternal`, thunk
  `0x832CA03C`;
- lines 5388-5769: successful `Save:` mounts on
  `\Device\Content\1\` through `\Device\Content\4\` and matching unmounts.

Together with the complete Xenia-origin payload tree and the established
interactive result, this confirms that existing-save enumeration, open, read,
and deserialization substantially work. That does not prove write or restart
parity.

## Static save-path map

All addresses below are Xbox guest addresses. A trace event's
`caller_guest_pc` is `guest_lr - 4`; the event records both values and labels
this basis explicitly.

### Guest entrypoints and wrappers

| Guest function / callsite | Imported target | Established behavior |
| --- | --- | --- |
| `sub_82CC2EB8` | `XamShowDeviceSelectorUI` at `0x832B9B04` | tail wrapper for content-device selection |
| `sub_82CC3A08` | `XamContentCreateEnumerator` at `0x832B9BE4` | tail wrapper for save enumeration |
| `sub_82CC3968`, call `0x82CC39CC`, LR `0x82CC39D0` | `XamContentCreateEx` at `0x832B9BA4` | validates arguments/flags, then creates or opens content; exact TU1 boundary `[0x82CC3968,0x82CC39EC)` |
| dynamic ordinal `0x0271` | `XamContentCreateInternal`, observed thunk `0x832CA03C` | internal content create/open used in the preserved run |
| `sub_82CC39F0` | `XamContentClose` at `0x832B9BB4` | tail wrapper for content finalisation/unmount |
| `sub_82CC39F8` | `XamContentGetCreator` at `0x832B9BC4` | tail wrapper for creator/profile metadata |
| `sub_82CC6FB8`, calls `0x82CC7028` / `0x82CC7074`, LRs `0x82CC702C` / `0x82CC7078` | `NtWriteFile` at `0x832B9ED4` | common write wrapper; handles caller-supplied async state or waits on `X_STATUS_PENDING` |
| `sub_82CC9F30`, call `0x82CC9F7C`, LR `0x82CC9F80` | `NtWriteFile` at `0x832B9ED4` | another write-and-pending-wait path |
| `sub_82CC7630`, call `0x82CC768C`, LR `0x82CC7690` | `NtCreateFile` at `0x832B9EF4` | create/open helper; passes access `0x00100001`, attributes `0x80`, share `3`, disposition `2`, options `0x4021`, then closes |
| `sub_82CC7AA8`, call `0x82CC7AB8`, LR `0x82CC7ABC` | `NtFlushBuffersFile` at `0x832B9F44` | explicit flush helper, converts negative status to guest boolean failure |
| `sub_82CC7760`, call `0x82CC77D4`, LR `0x82CC77D8` | `NtSetInformationFile` at `0x832BA0F4` | delete-on-close (`XFileDispositionInformation`, class 13) |
| `sub_82CC7D28`, calls `0x82CC7D74` / `0x82CC7D9C`, LRs `0x82CC7D78` / `0x82CC7DA0` | `NtSetInformationFile` at `0x832BA0F4` | allocation/end-of-file length changes (classes 20 and 19) |
| `sub_82CCBCE8`, call `0x82CCBDA4`, LR `0x82CCBDA8` | `NtSetInformationFile` at `0x832BA0F4` | end-of-file length change (class 20) |
| `sub_8300BA00`, call `0x8300BA8C`, LR `0x8300BA90` | `NtSetInformationFile` at `0x832BA0F4` | rename information (class 10), then `NtClose` |

The imports also include `XamContentGetLicenseMask` at `0x832B9BD4`,
`XamContentGetDeviceState` at `0x832B9BF4`, and `NtClose` at `0x832B9D84`.
Fable II does not import `XamContentFlush` in the current generated TU1
registration; its demonstrated explicit filesystem flush path is
`NtFlushBuffersFile`.

The wrapper purposes above are limited to directly generated instructions and
API contracts. Broader Lionhead semantic names have not been invented.

### End-to-end host path and operation flow

1. `--user_data_root` enters `ReXApp`, then `Runtime`, then `KernelState`, which
   constructs `ContentManager` with the absolute root.
2. `UserProfile` currently supplies XUID `B13EBABEBABEBABE`. The selected HDD
   device is ID `1`, reporting 20 GiB total and 3 GiB free. The XUID difference
   from Xenia's `E03000002168622D` is policy, not evidence of a defect.
3. `XamContentCreateEnumerator` lists saved-game content under the current and
   common profiles and returns an enumerator handle and item count.
4. `XamContentCreate*` resolves title ID `0xFFFFFFFF` to `0x4D5307F1`, applies
   create disposition from the low flag nibble (`1` new, `2` always, `3`
   existing, `4` open-always, `5` truncate-existing), and returns disposition
   `1` create or `2` open.
5. ReXGlue calculates payload root
   `<user-root>\B13EBABEBABEBABE\4D5307F1\00000001\Hero000` and header
   `<user-root>\B13EBABEBABEBABE\4D5307F1\Headers\00000001\Hero000.header`.
   New content creates the payload directory and the 328-byte aggregate
   header, then mounts a writable `HostPathDevice` at
   `\Device\Content\N\` with `Save:` as the symbolic link.
6. `NtCreateFile` normalizes guest paths through the VFS, enforces directory vs
   non-directory options, applies dispositions `0..5`, creates missing parent
   paths/entries, returns a file handle, and writes status plus `FileAction` to
   the I/O status block. The guest `share_access` value is accepted and traced
   but is not enforced by the VFS open interface. Host handles currently share
   read/write, plus delete when the content device requests it.
7. `NtWriteFile` resolves the handle, uses either the explicit byte offset or
   the `XFile` position, performs the host write synchronously, reports actual
   bytes in the I/O status block, queues an APC when requested, signals the
   supplied event and file wait object, and returns `X_STATUS_PENDING` for a
   nonsynchronous handle. The guest wrappers wait or consume their caller-owned
   completion state. Explicit-offset/current-position behavior matches the
   compared Canary source, including its current-position update convention.
8. `NtSetInformationFile` handles position, allocation length, end-of-file
   truncation/extension, delete-on-close, and rename. Host rename uses
   `std::filesystem::rename`; replace-existing is not a separate atomic
   contract in the current implementation.
9. `NtFlushBuffersFile` now reaches `XFile::Flush`, `HostPathFile::Flush`, and
   Windows `FlushFileBuffers` (POSIX `fsync`). `XamContentFlush` now flushes all
   open non-directory handles under its mounted content root while retaining
   the prior success result when no root is mounted.
10. `NtClose` releases the individual object handle. `XamContentClose` closes
    open file handles beneath the mounted prefix, unregisters `Save:` and its
    device, and destroys the package.
11. A later process reconstructs the same root/profile/title/content path;
    enumeration reads the header and returns `Hero000`. This restart step is
    not yet tested for a fresh native slot.

### Synchronous and overlapped results

- `XamContentCreate*` with an overlapped pointer records the request, queues a
  deferred operation, immediately returns `X_ERROR_IO_PENDING` (`997`), then
  writes final result, extended HRESULT, disposition length, event state, and
  callback/APC state to the overlapped structure.
- `XamContentClose` and `XamContentFlush` complete an overlapped request
  immediately and return `X_ERROR_IO_PENDING` to the caller.
- `NtWriteFile` performs the operation synchronously in the current runtime
  even for a nonsynchronous handle. Its immediate return may be
  `X_STATUS_PENDING`, while the I/O status block contains the completed host
  result and actual length. This is the same broad behavior as the compared
  Canary source.
- The trace correlates requests/results with `request_sequence` and tracks XAM
  overlapped completion by guest pointer. Missing completion is a reportable
  anomaly.

### Host implementation source index

| Area | ReXGlue implementation | Compared Xenia Canary implementation |
| --- | --- | --- |
| content APIs and completion | `src/kernel/xam/xam_content.cpp` | `src/xenia/kernel/xam/xam_content.cc` |
| device selector | `src/kernel/xam/xam_ui.cpp` | `src/xenia/kernel/xam/xam_content_device.cc` |
| content roots, headers, mounts | `src/system/xam/content_manager.cpp` | `src/xenia/kernel/xam/content_manager.cc`, `src/xenia/kernel/xam/xcontent/xcontent_package_directory.cc` |
| create/write/flush I/O | `src/kernel/xboxkrnl/xboxkrnl_io.cpp` | `src/xenia/kernel/xboxkrnl/xboxkrnl_io.cc` |
| truncate/rename information | `src/kernel/xboxkrnl/xboxkrnl_io_info.cpp` | `src/xenia/kernel/xboxkrnl/xboxkrnl_io_info.cc` |
| close/handle lifetime | `src/kernel/xboxkrnl/xboxkrnl_ob.cpp` | `src/xenia/kernel/xboxkrnl/xboxkrnl_ob.cc` |
| file offsets and flushing | `src/system/xfile.cpp` | `src/xenia/kernel/xfile.cc` |
| host-path operations | `src/filesystem/devices/host_path_file.cpp`, `src/core/filesystem_win.cpp` | `src/xenia/vfs/devices/host_path_file.cc` |

The Canary paths refer to the read-only comparison commit recorded above.
ReXGlue source, generated TU1 instructions, the preserved runtime log, and the
compared Canary source were treated as separate evidence; matching structure
was not assumed to prove behavioral parity.

## ReXGlue versus current Xenia Canary

| Contract | Static comparison | Classification |
| --- | --- | --- |
| Profile identity | ReXGlue has one native profile with XUID `B13EBABEBABEBABE`; Canary resolves configured user profiles such as `E03000002168622D` | confirmed policy difference; not a defect by itself |
| Content path | Both use XUID/title/content-type/name hierarchy and mount a host-path device for directory packages | confirmed substantial parity |
| Content metadata structure | Canary accepts `XCONTENT_DATA`, aggregate, and richer `XCONTENT_DATA_INTERNAL`; ReXGlue's internal entry currently reads `XCONTENT_AGGREGATE_DATA` | confirmed divergence; runtime relevance unknown |
| Create validation | Canary rejects missing users, empty root/name, and already registered root links more explicitly | confirmed divergence; no captured failing input yet |
| Header lifecycle | Canary's directory package writes a 40,960-byte padded header on package destruction; ReXGlue writes a 328-byte aggregate header immediately after create | confirmed divergence; ReXGlue can enumerate its own format and load the prepared Xenia-origin payload |
| Header error propagation | ReXGlue now detects header create/write/close errors, but `xeXamContentCreate` still ignores `WriteContentHeaderFile`'s returned error | confirmed gap; not proven to be reached |
| File dispositions | Both route the same `NtCreateFile` disposition/access/options into closely related VFS logic | confirmed substantial parity |
| Write/offset/completion | Both perform the current host write immediately, fill the I/O status block, signal completion, and return pending for nonsynchronous handles | confirmed substantial parity |
| Share flags | Both accept the guest argument but do not carry it into the generic VFS `OpenFile` contract | confirmed shared limitation, not a Canary differential |
| Flush | Compared Canary stubs both `NtFlushBuffersFile` and `XamContentFlush` as success. ReXGlue did the same before this branch; ReXGlue now performs real host flushes | confirmed ReXGlue correctness fix; cannot explain a guest that never attempts payload writes |
| Rename/replace | Both use their VFS/file rename paths; atomic replace and all Xbox sharing interactions are not fully modeled | confirmed evidence gap |
| Close | Both close content-owned handles and unmount the root/device | confirmed substantial parity |
| Async XAM failure result | Canary converts a failing overlapped create callback's result to `X_ERROR_FUNCTION_FAILED` while preserving extended error; ReXGlue currently leaves the raw result as the final result | confirmed divergence; runtime relevance unknown |

## Findings by evidence level

### CONFIRMED

- Existing Xenia-origin save enumeration and loading substantially work in the
  native recompilation.
- A prior fresh native attempt produced the slot directory, `saveuid.bin`, and
  `Hero000.header`, but not the remaining payload.
- The guest has concrete paths to device selection, content creation,
  filesystem create/write/truncate/flush/close, and overlapped waiting.
- The preserved old runtime log does not contain enough ordered, structured
  file-operation evidence to say whether the guest attempted the missing
  payload.
- ReXGlue's old `NtFlushBuffersFile` and `XamContentFlush` returned success
  without flushing. Commit `1f4bda8...` implements actual host flushing and
  propagates failure.
- The new trace is disabled unless `--save_trace_dir` names an absolute output
  directory. It writes no payload bytes, refuses to overwrite an existing
  capture, and flushes each NDJSON event.
- No XUID override, fake success, empty payload fabrication, game-specific
  runtime bypass, or generated-code patch was added.

### INFERRED

- `sub_82CC6FB8` and `sub_82CC9F30` are general Lionhead write adapters used by
  multiple callers; the trace is needed to identify their save-path callers.
- Because content/header creation succeeds but payload does not appear, the
  earliest useful split is whether any expected payload `NtCreateFile` or
  `NtWriteFile` occurs after `XamContentCreate` completion.
- The flush correction improves durability if the guest reaches finalisation,
  but is unlikely to create missing payload files that the guest never opened.

### HYPOTHESES requiring the runtime trace

1. `guest_never_attempted_payload_save`: the immediately preceding content or
   device state causes guest save logic to stop after `saveuid.bin`.
2. `content_create_result_mismatch`, `content_metadata_mismatch`, or
   `overlapped_completion_mismatch`: ReXGlue returns a subtly different final
   state even though it creates the directory/header.
3. `file_create_semantics_mismatch` or `write_semantics_mismatch`: payload is
   attempted and the first create, offset, status, or byte count diverges.
4. `flush_or_close_mismatch` or `rename_or_replace_mismatch`: payload reaches a
   temporary/intermediate state but finalisation fails.
5. `reload_enumeration_mismatch`: only relevant after a structurally complete
   slot exists and a new process fails to enumerate it.

The current root-cause classification remains `unknown`. No hypothesis has
been promoted without runtime evidence.

## Diagnostic instrumentation

ReXGlue commit `1f4bda8...` adds the payload-free trace in
`include/rex/system/save_trace.h` and `src/system/save_trace.cpp`, with hooks in
XAM content/device selection, `ContentManager`, overlapped completion,
`NtCreateFile`, `NtWriteFile`, directory query, `NtSetInformationFile`,
`NtFlushBuffersFile`, `NtClose`, and content close/flush.

Schemas are versioned independently:

- event stream: `save-trace-events-v1.ndjson`, schema version 1;
- run metadata: `save-trace-run-v1.json`, schema version 1;
- diagnostic report: `save-diagnostic-report-v1.json`, schema version 1.

Deterministic event data is separate from run metadata. Events include, where
applicable: sequence, relative monotonic nanoseconds, guest thread ID, LR,
caller PC, operation/phase, guest and host paths, root/file handles, handle
type, device/profile/title/content state, access/share/disposition/options,
offset/current-offset marker, requested/actual bytes, operation/immediate/I/O
results, synchronous/async state, event/APC/callback state, flush, close,
length, and rename target. Payload buffers, XML text, and save contents are
never recorded.

`tools/Fable2SaveTrace.py` validates continuity and schemas, snapshots trees,
compares paths/sizes/hashes/mtimes/modification order, and reports the first
failed, incomplete, escaped-root, or structurally inconsistent operation using
the requested classification vocabulary.

`tools/Invoke-Fable2NativeSaveDiagnostic.ps1` validates all write destinations
under the ignored diagnostic root, refuses nonempty fresh state and existing
capture artifacts, and exposes `Status`, `Prepare`, `Launch`, and `Report`.
`FreshNative` selects A/B/capture-001; `XeniaUpdate` selects C/D/capture-D-001.
It contains no input automation.

## Exact diagnostic build

```text
Executable:
C:\Dev\Fable2Recomp\out\build\win-amd64-native-save-diagnostic-release\fable2.exe

Size:
105042944 bytes

SHA-256:
E90F192FF212FC835CACB36E9B06E91CC2DC6C6843104CE983D0460A34E6ED0A
```

The dedicated cache resolved exactly:

```text
Found ReXGlue SDK 0.10.0.46-dev.g39a35ab at C:/Dev/rexglue-sdk-v0.10/out/install/win-amd64-native-save/lib/cmake/rexglue
```

Code generation reapplied TU1 successfully and wrote no generated source
changes. The full diagnostic executable linked successfully. One attempted
concurrent normal/diagnostic build caused the two code-generation targets to
contend on manifest stamping; the normal target printed `Failed to open
manifest for stamping` and `Failed to stamp manifest sdkVersion` but returned
success. Both builds were immediately rerun sequentially and passed without
that warning. Do not run code generation from the two build caches
concurrently.

The windowed executable does not implement a safe `--help` exit: two attempted
help-only compile checks emitted
`cvar: CLI11  parse error: This should be caught in your main function, see examples`
and left GUI-subsystem processes alive. Both exact `--help` PIDs were terminated
immediately. Their only filesystem effects were ignored
`out\build\win-amd64-native-save-diagnostic-release\logs\fable2_001.log` and
`fable2_002.log`, each containing only `--game_data_root was not provided.` No
game data root was supplied, no module/runtime was launched, and a timestamp
audit found no change under either private original or the isolated save
states. Do not use `fable2.exe --help` as a preflight.

## Files changed

Fable2Recomp commit `ecc81424...`:

- `CMakeLists.txt`
- `tests/test_fable2_save_trace.py`
- `tools/Fable2SaveTrace.py`
- `tools/Invoke-Fable2NativeSaveDiagnostic.ps1`
- `tools/schemas/fable2-save-diagnostic-report-v1.schema.json`
- `tools/schemas/fable2-save-trace-event-v1.schema.json`
- `tools/schemas/fable2-save-trace-run-v1.schema.json`

Commit `1d8bc00...` updates only the audited ReXGlue version pin. This document
is the only additional file in the final checkpoint commit.

ReXGlue commits `1f4bda8...`, `e2ffe70...`, and `39a35ab...`:

- `include/rex/filesystem.h`
- `include/rex/filesystem/devices/host_path_file.h`
- `include/rex/filesystem/file.h`
- `include/rex/system/save_trace.h`
- `include/rex/system/xam/content_manager.h`
- `include/rex/system/xfile.h`
- `src/core/filesystem_posix.cpp`
- `src/core/filesystem_win.cpp`
- `src/filesystem/devices/host_path_file.cpp`
- `src/kernel/xam/xam_content.cpp`
- `src/kernel/xam/xam_ui.cpp`
- `src/kernel/xboxkrnl/xboxkrnl_io.cpp`
- `src/kernel/xboxkrnl/xboxkrnl_io_info.cpp`
- `src/kernel/xboxkrnl/xboxkrnl_ob.cpp`
- `src/system/CMakeLists.txt`
- `src/system/kernel_state.cpp`
- `src/system/save_trace.cpp`
- `src/system/xam/content_manager.cpp`
- `src/system/xfile.cpp`
- `tests/unit/CMakeLists.txt`
- `tests/unit/core/filesystem_test.cpp`
- `tests/unit/system/save_trace_test.cpp`

## Commands and validation record

Tool baseline:

```text
cmake version 4.4.2
ninja 1.13.2
Python 3.14.3
clang version 22.1.8
```

ReXGlue configure, build, install, and test:

```powershell
cmake --preset win-amd64 `
    -DREXGLUE_BUILD_TESTS=ON `
    -DCMAKE_INSTALL_PREFIX=C:/Dev/rexglue-sdk-v0.10/out/install/win-amd64-native-save
cmake --build --preset win-amd64-release --target install
ctest --preset win-amd64-release --output-on-failure -j 8
```

Result: configure/build/install passed; `1767/1767` tests passed (`306` unit,
`1458` PPC, `3` fault-walk). Four BitStream cases were expected skips, not
failures. The closing parallel run exposed two synthetic-test temporary-name
collisions because CTest executes cases in separate processes; commits
`e2ffe70...` and `39a35ab...` include the process ID in those test-only names.
The full parallel suite then passed cleanly.

Fable2Recomp baseline and regression commands:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q tools tests
python .\tools\Verify-Fable2MigrationLedger.py
python .\tools\Verify-Fable2EntrypointClosure.py
python .\tools\Verify-Fable2NativeRendererG1.py
fable2-codegen
fable2-build
python .\tools\Fable2SaveTrace.py validate-schemas `
    .\tools\schemas\fable2-save-trace-event-v1.schema.json `
    .\tools\schemas\fable2-save-trace-run-v1.schema.json `
    .\tools\schemas\fable2-save-diagnostic-report-v1.schema.json
python .\tools\Fable2SaveTrace.py --help
python .\tools\Fable2SaveTrace.py report --help
.\tools\Invoke-Fable2NativeSaveDiagnostic.ps1 -Action Status
```

The starting baseline passed `58/58` Python tests, compile checks, all three
verifiers, TU1 code generation, and the normal release build. The migration
ledger reported 32 records, 60,425 total functions, `setjmp` `0x83006C90`, and
`longjmp` `0x82CAFA30`. Entrypoint closure reported schema 3, analyzer `2.0.0`,
35,626 candidates, 55 strong, 180 probable, and 3 fixtures. Native renderer G1
reported 11 checks. The post-change full Python count and final rerun results
were `68/68` passed. The compile check, all three verifiers, both code-generation
paths, the normal release build, the diagnostic release build, all three schema
checks, Python CLI help checks, both guarded diagnostic status checks, and the
PowerShell syntax check passed. The CMake test inventory contains no additional
Fable2Recomp CTest cases.

Exact diagnostic configuration and build:

```powershell
cmake --preset win-amd64-release `
    -B C:/Dev/Fable2Recomp/out/build/win-amd64-native-save-diagnostic-release `
    -Drexglue_DIR=C:/Dev/rexglue-sdk-v0.10/out/install/win-amd64-native-save/lib/cmake/rexglue
cmake --build C:/Dev/Fable2Recomp/out/build/win-amd64-native-save-diagnostic-release `
    --target fable2_codegen
cmake --build C:/Dev/Fable2Recomp/out/build/win-amd64-native-save-diagnostic-release `
    --config Release
```

All three commands passed. No game or emulator smoke run was used.

## Overnight closure assertions

- Fable2Recomp ends on `fable2-native-save-write-parity`; after the checkpoint
  commit its tracked and untracked worktree is clean.
- ReXGlue ends on `fable2-native-save-write-parity`; its only worktree status is
  the pre-existing modified `thirdparty/libmspack` submodule.
- No Fable II game module/runtime, Xenia, or Xenia Canary gameplay session was
  launched. The two exact diagnostic-executable `--help` process attempts are
  disclosed above; neither received game/update/user roots, and both were
  terminated after emitting only the missing-root diagnostic.
- No user-triggered save, autosave, native save creation, restart/load check,
  update-existing-save check, or interactive gameplay regression was run.
- Neither `C:\Users\Fenris\Documents\fable2.backup` nor
  `C:\Dev\Fable2XeniaSaves` was modified. The working reference source at
  `C:\Users\Fenris\Documents\fable2` was read and copied into ignored State C
  and State D without changing its source timestamps.
- No save, profile, raw XEX, extracted/decrypted executable image, private
  payload trace, or credentials were staged or committed.
- No commit was pushed; no tag, remote branch, pull request, release, asset, or
  external upload was created or changed.

## Tomorrow: one fresh native save-trigger capture

Before launch, State B must still be empty and `Capture already used` must be
`False`:

```powershell
Set-Location C:\Dev\Fable2Recomp
.\tools\Invoke-Fable2NativeSaveDiagnostic.ps1 -Action Status -State FreshNative
```

The exact launch command is:

```powershell
.\tools\Invoke-Fable2NativeSaveDiagnostic.ps1 -Action Launch -State FreshNative
```

It expands to the diagnostic executable with these roots:

```text
--game_data_root=C:\Dev\Fable2Recomp\assets\runtime
--update_data_root=C:\Dev\Fable2Recomp\assets\update
--user_data_root=C:\Dev\Fable2Recomp\out\native-save-diagnostic\B-fresh-native
--cache_root=C:\Dev\Fable2Recomp\out\native-save-diagnostic\cache-001
--gpu_plugin=xenos
--log_level=debug
--log_file=C:\Dev\Fable2Recomp\out\native-save-diagnostic\capture-001\fable2-native-save-001.log
--save_trace_dir=C:\Dev\Fable2Recomp\out\native-save-diagnostic\capture-001
```

Expected before the trigger: no files under State B and no trace/report files
under `capture-001`.

Use normal gameplay only. Select **New Game**, choose the normal saving/storage
path rather than the previously documented **Continue Without Saving** path,
and progress through childhood until the game's first normal save indicator
completes. Fable II uses its normal save/autosave flow; no unverified manual-save
menu is assumed.

After the indicator completes, exit cleanly if possible. If the program hangs
or crashes, record that fact and preserve the process result; do not retry and
do not relaunch. The helper waits for the process and prints its exit code.

Expected complete structural output after the trigger:

```text
B13EBABEBABEBABE\4D5307F1\00000001\Hero000\chaptersave.bin
B13EBABEBABEBABE\4D5307F1\00000001\Hero000\Fable2PubInfo.xml
B13EBABEBABEBABE\4D5307F1\00000001\Hero000\failquestsave.bin
B13EBABEBABEBABE\4D5307F1\00000001\Hero000\herosave.bin
B13EBABEBABEBABE\4D5307F1\00000001\Hero000\mainsave.bin
B13EBABEBABEBABE\4D5307F1\00000001\Hero000\saveuid.bin
B13EBABEBABEBABE\4D5307F1\00000001\Hero000\texturemorphs.bin
B13EBABEBABEBABE\4D5307F1\Headers\00000001\Hero000.header
```

The known failure may instead leave only `saveuid.bin` and the header. Do not
create or copy any missing file by hand.

Without relaunching anything, generate the report:

```powershell
.\tools\Invoke-Fable2NativeSaveDiagnostic.ps1 -Action Report -State FreshNative
```

Capture outputs:

```text
C:\Dev\Fable2Recomp\out\native-save-diagnostic\capture-001\save-trace-events-v1.ndjson
C:\Dev\Fable2Recomp\out\native-save-diagnostic\capture-001\save-trace-run-v1.json
C:\Dev\Fable2Recomp\out\native-save-diagnostic\capture-001\fable2-native-save-001.log
C:\Dev\Fable2Recomp\out\native-save-diagnostic\capture-001\save-diagnostic-report-v1.json
```

Do not perform the restart/enumeration test until the first capture has been
inspected. A complete-looking directory is not proof of parity.

## Ready-to-paste continuation prompt

```text
Continue the Fable II native-save write-parity investigation from
docs/fable2-native-save-write-parity.md. Do not launch Fable2Recomp, Xenia, or
Xenia Canary yet. First inspect the existing ignored State B save tree and all
four capture-001 artifacts under
C:\Dev\Fable2Recomp\out\native-save-diagnostic. Run the payload-free report if
it has not already been generated. Identify the earliest trace sequence where
native behavior fails, is missing, or differs semantically from the pinned
Xenia Canary source. Preserve exact guest LR/caller PC, handles, paths, flags,
offsets, byte counts, result codes, IOSB values, completion state, and log
locations. Classify the failure using the documented vocabulary. Reproduce the
contract with a focused synthetic test before changing code. Do not retry or
perform restart/load/update validation until the first capture is preserved
and explained. Keep both repositories on fable2-native-save-write-parity;
preserve the pre-existing dirty ReXGlue thirdparty/libmspack submodule; do not
push or upload anything.
```

## Work blocked only on the save trigger

- capture whether the guest attempts each missing payload file;
- identify the first bad XAM/content/VFS/write/completion/finalisation result;
- add a focused regression and the smallest evidence-backed correction if
  needed;
- create a complete fresh native slot;
- terminate and start a genuinely new process;
- enumerate and load that slot;
- update the isolated existing-save copy in State D and verify no corruption;
- repeat restart/load verification after update.

No native-save parity claim is valid until those restart and update checks pass.
