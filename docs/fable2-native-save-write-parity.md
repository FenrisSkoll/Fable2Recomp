# Fable II native-save write-parity checkpoint

## Status and stop boundary

Captures 001 and 002 are preserved and explained. Capture 001 proves that the
TU1 guest created and wrote the required fresh-slot payload. Capture 002 proves
that a genuinely new process enumerated `Hero000` and entered the existing-slot
load path: all required payload files were opened successfully, the slot was
closed successfully, execution continued, and the process exited cleanly. No
save payload or header changed during reload.

There is no failing or semantically divergent save-trace event in capture 002
sequences `1..72`. The capture predates `NtReadFile` tracing, so byte-level read
counts and meaningful-state restoration cannot be proved from the payload-free
artifacts alone. Native-save parity is **not** claimed. Update-in-place and a
subsequent restart/load remain untested. Interactive runtime validation stops
before any retry or State D update.

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
- Capture-001 parser and guarded-reload workflow commit:
  `bbb47f42fd6d5656ba098fbf15e7a14e55f7cdb7`
- Capture-002 restart-observation report commit:
  `a2b7349916bbcbd24fcded85f3422aaf126c820a`
- ReXGlue read-trace pin commit:
  `748cff0b04875efb1e60e73b805ef4a089c54f6c`
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
- Save-path read-trace commit:
  `b1bf7701dfd778f0b61d8a599cbb6e4690cf547a`
- Current committed tree:
  `f9defaac5be8d76c613441fc0aa9264eb5bdf9d4`
- Installed SDK identity: `0.10.0.47-dev.gb1bf770`
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
| B | `...\B-fresh-native` | preserved capture-001 native slot and profile files | next-process enumeration/load attempt |
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
out\native-save-diagnostic\state-B-after-write.json
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

### Hypotheses before capture 001

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

Capture 001 rules out hypotheses 1 through 4 for the operations it contains;
the detailed post-capture result below supersedes this pre-capture list.
Restart enumeration remains untested.

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
under the ignored diagnostic root, refuses an invalid source state and existing
capture artifacts, and exposes `Status`, `Prepare`, `Launch`, and `Report`.
`FreshNative` selects A/B/capture-001; `FreshNativeReload` selects the preserved
State B snapshot, State B, cache-002, and capture-002; `XeniaUpdate` selects
C/D/cache-D-001/capture-D-001. It contains no input automation.

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

Fable2Recomp capture-analysis commit `bbb47f42...`:

- `tests/test_fable2_save_trace.py`
- `tools/Fable2SaveTrace.py`
- `tools/Invoke-Fable2NativeSaveDiagnostic.ps1`
- `tools/schemas/fable2-save-diagnostic-report-v1.schema.json`

The subsequent capture-analysis checkpoint commit updates only this document.

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

## Capture-001 analysis checkpoint (2026-09-03)

### Immutable capture and derived report

The four original artifacts were inspected in place and not rewritten:

| Artifact under `out\native-save-diagnostic\capture-001` | Bytes | SHA-256 |
| --- | ---: | --- |
| `fable2-native-save-001.log` | 4,020,079 | `4642F1F87324F0140FFC87E40144B643E3E76D89E4342C5AA9B347A95F57CCB5` |
| `save-diagnostic-report-v1.json` | 5,647 | `3AF62D2A0094945EBF467D61958D2759D32920F4D169D27B022FF58F5F382FC8` |
| `save-trace-events-v1.ndjson` | 316,052 | `9070A4EB8C7ACF589234F47437E976C048D05C1FCA09413938FECAFA77E72826` |
| `save-trace-run-v1.json` | 242 | `C6197487727C98EAB3B39BA5F8360C6C5192266B8B8E2E09FAA8D510231C0FE1` |

The metadata identifies schema 1/event schema 1, PID `31164`, start time
`2026-09-03T16:40:59Z`, and `contains_payload_bytes: false`. The original
report is retained as evidence even though its old all-seven-files expectation
is now known to be too strict. The corrected payload-free derived report is:

```text
C:\Dev\Fable2Recomp\out\native-save-diagnostic\analysis-capture-001\save-diagnostic-report-v1.json
size:    6004 bytes
SHA-256: 0DBCC541E1E924D419635EB230678DC01EF74B8F11C0405504450B30FFCCC8F0
```

### Preserved State B tree

`state-B-after-write.json` is a payload-free, immutable pre-reload inventory:

```text
C:\Dev\Fable2Recomp\out\native-save-diagnostic\state-B-after-write.json
size:    3514 bytes
SHA-256: 3FA6858C6FA1986523492DEF1BFED6A817D74FAD206EA7A68809EAFAE2C0E498
```

The captured slot is:

| Relative path below `B-fresh-native` | Bytes | SHA-256 |
| --- | ---: | --- |
| `B13EBABEBABEBABE/4D5307F1/00000001/Hero000/chaptersave.bin` | 550 | `2D8DF1EC261325A6B4DC0224A7878212940B00C153E389FD137DD8921166CF6D` |
| `B13EBABEBABEBABE/4D5307F1/00000001/Hero000/Fable2PubInfo.xml` | 554 | `51DF9E516AA2D3FA35F4CA3C90760D5D0CB20F250EA3F4C6B80746EC1A9179DC` |
| `B13EBABEBABEBABE/4D5307F1/00000001/Hero000/herosave.bin` | 1,521 | `610562CC3179C1F32108E539851987914D1C891378F9D0301E5D73A11C7FAA32` |
| `B13EBABEBABEBABE/4D5307F1/00000001/Hero000/mainsave.bin` | 166,760 | `F31FE0EC07A58C1777CA127C6937F53625EDA82208BDCEF0710B675D021FF330` |
| `B13EBABEBABEBABE/4D5307F1/00000001/Hero000/saveuid.bin` | 8 | `28DD9A921926D55D2360D4F3DC5C508DF96A7685D32CC16E7694E98E03398F32` |
| `B13EBABEBABEBABE/4D5307F1/00000001/Hero000/texturemorphs.bin` | 29,479 | `F7F1595ED15202D462634B38A5220F787DC9EBBC20636D8887123C1F0D56F00D` |
| `B13EBABEBABEBABE/4D5307F1/Headers/00000001/Hero000.header` | 328 | `9BE20BAE420598D3D42766ACDD8557FFD0F0C70D98A8085F03E0475E257B6EFE` |

State B also contains the three native profile-setting files and the native
achievements TOML recorded in the snapshot. No `failquestsave.bin` is present.

That absence is not a fresh-slot failure. In the read-only pinned Xenia save,
`saveuid.bin` was created at `2026-09-01 20:10:42 UTC`, the four core payloads
at `20:10:48..20:10:49`, `Fable2PubInfo.xml` at `20:31:37`, and
`failquestsave.bin` at `20:46:10`. Therefore the first Xenia save also existed
without the latter two files. The fresh required payload is `saveuid.bin`,
`mainsave.bin`, `herosave.bin`, `chaptersave.bin`, and `texturemorphs.bin`;
`Fable2PubInfo.xml` and `failquestsave.bin` are conditional later-state files.

### Earliest failure or semantic divergence

There is **no such sequence in capture 001**. Events `1..618` are contiguous.
The corrected report classification is `unknown`, meaning no category in the
failure vocabulary was observed, and `first_anomaly` is `null`. There are zero
non-success final operation results, zero short writes, zero missing overlapped
completions, and zero host paths outside State B. `unknown` is not a parity
claim; it preserves the remaining untested restart-enumeration/load question.

Exact trace landmarks:

| Sequences | Guest LR / caller PC | Operation and result |
| --- | --- | --- |
| `1..2` | `0x82443354` / `0x82443350` | initial saved-game enumeration; handle `0xF80001AC`, item count `0`, result `0` |
| `3..6` | `0x82441D84` / `0x82441D80` | device selector for 8,617,984 bytes; overlapped `0x701BF9C0`; immediate `997`; device `1`; final `0`; event `0xF80001C0` signaled; no callback/APC |
| `13..18` | `0x82CC4264` / `0x82CC4260` | create `Save`/`Hero000`, user `254`, device `1`, type `1`, title `0x4D5307F1`, XUID `B13EBABEBABEBABE`, flags `0x802`, size `8617984`, overlapped `0x701BF610`; immediate `997`; disposition `1`; final/extended `0`; length `1`; event `0xF80001F4` signaled |
| `15..16` | worker thread `5` | wrote the 328-byte `Hero000.header`; actual `328`, result `0` |
| `19..32` | see below | created, sized, wrote, flushed, and closed `saveuid.bin` successfully |
| `33..35` | `0x82445330` / `0x8244532C` | initial content close; overlapped `0x701BF610`; operation/final/extended `0`; event `0xF80001F4` signaled |
| `36..212` | create `0x82CC4264` / `0x82CC4260`; close `0x82449C3C` / `0x82449C38` | first payload cycle through `\Device\Content\2\`; flags `4`, immediate `997`, disposition `2`, final `0`, completed close |
| `213..415` | same | second payload cycle through `\Device\Content\3\`; all captured operations completed |
| `416..618` | same | final payload cycle through `\Device\Content\4\`; all captured operations completed |

The `saveuid.bin` contract is exact: sequence `19` used root handle
`0xFFFFFFFD`, access `0xC0100080`, attributes/share `0`, disposition `5`, and
options `0x64`; sequence `20` returned synchronous file handle `0xF8000200`,
action `2`, result `0`. Sequences `21/22`, `23/24`, and `27/28` applied
information class `14`, length/information `8`, result `0`. Sequences `25/26`
wrote at current position (`offset = UINT64_MAX`) with requested/actual `8`,
immediate/operation/IOSB status `0`, IOSB information `8`, and no pending/event
completion. Sequences `29/30` flushed with result `0`; `31/32` closed with
result `0`. Their guest callsites are respectively `0x82CC35F4/0x82CC35F0`,
`0x82CC7A54/0x82CC7A50`, `0x82CC7078/0x82CC7074`,
`0x82CC7ABC/0x82CC7AB8`, and `0x82CC27D0/0x82CC27CC`.

The final cycle opened each binary once for existing access and once for
replacement/write. `mainsave.bin` used handles `0xF8000304` and `0xF8000308`
at `420..423`; accesses were `0x80100080`/`0x40100080`, attributes `0x80`,
share `3`, dispositions `5`/`1`, options `0x48`/`0x40`, actions `3`/`1`, and
both handles were asynchronous. Writes `424..573` made 75 explicit-offset
requests totaling 174,459 bytes and returned exactly 174,459 bytes; overlap in
the guest offsets yields the final 166,760-byte file. Every result returned
immediate `259` (`X_STATUS_PENDING`), operation result `0`, IOSB status `0`,
IOSB information equal to the request, event `0xF800030C` signaled, no APC,
and `returns_pending: true`. The exact request/result, offset, and byte triples
are retained verbatim here:

```text
424/425:0+2048=2048, 426/427:2048+2048=2048, 428/429:4096+1642=1642,
430/431:5738+2737=2737, 432/433:8192+2048=2048, 434/435:10240+2048=2048,
436/437:12288+2048=2048, 438/439:14336+2048=2048, 440/441:16384+2048=2048,
442/443:18432+2048=2048, 444/445:20480+2048=2048, 446/447:22528+2048=2048,
448/449:24576+2048=2048, 450/451:26624+2048=2048, 452/453:28672+2048=2048,
454/455:30720+2048=2048, 456/457:32768+2048=2048, 458/459:34816+2048=2048,
460/461:36864+2048=2048, 462/463:38912+2048=2048, 464/465:40960+2048=2048,
466/467:43008+2048=2048, 468/469:45056+2048=2048, 470/471:47104+2048=2048,
472/473:49152+2048=2048, 474/475:51200+2048=2048, 476/477:53248+1936=1936,
478/479:55184+8162=8162, 480/481:61440+1914=1914, 482/483:63354+8202=8202,
484/485:69632+1932=1932, 486/487:71564+8122=8122, 488/489:77824+1870=1870,
490/491:79694+6464=6464, 492/493:86016+2048=2048, 494/495:88064+2048=2048,
496/497:90112+2048=2048, 498/499:92160+2048=2048, 500/501:94208+1827=1827,
502/503:96035+2509=2509, 504/505:98304+544=544, 506/507:98304+2048=2048,
508/509:100352+2048=2048, 510/511:102400+2048=2048,
512/513:104448+2048=2048, 514/515:106496+2048=2048,
516/517:108544+2048=2048, 518/519:110592+2048=2048,
520/521:112640+2048=2048, 522/523:114688+2048=2048,
524/525:116736+2048=2048, 526/527:118784+2048=2048,
528/529:120832+2048=2048, 530/531:122880+2048=2048,
532/533:124928+2048=2048, 534/535:126976+2048=2048,
536/537:129024+2048=2048, 538/539:131072+2048=2048,
540/541:133120+2048=2048, 542/543:135168+2048=2048,
544/545:137216+1509=1509, 546/547:138725+2806=2806,
548/549:141312+2048=2048, 550/551:143360+2048=2048,
552/553:145408+1980=1980, 554/555:147388+2695=2695,
556/557:149504+2048=2048, 558/559:151552+2048=2048,
560/561:153600+2048=2048, 562/563:155648+2048=2048,
564/565:157696+2048=2048, 566/567:159744+2048=2048,
568/569:161792+2048=2048, 570/571:163840+2048=2048,
572/573:165888+872=872
```

The remaining final-cycle writes used the same success semantics:

| File | Create/write/close sequences | Write contract |
| --- | --- | --- |
| `Fable2PubInfo.xml` | `578..585`, handle `0xF8000304` | synchronous create access `0x40100080`, attrs `0x80`, share `0`, disposition `5`, options `0x60`, action `3`; current-position writes `580/581` = `2/2` and `582/583` = `552/552`; result/IOSB `0`, information exact |
| `herosave.bin` | `586..595`, handles `0xF8000304`/`0xF8000308` | write `590/591`, offset `0`, requested/actual/IOSB information `1521`, pending `259`, final/IOSB `0`, event `0xF800030C` signaled |
| `chaptersave.bin` | `596..605`, handles `0xF8000304`/`0xF8000308` | write `600/601`, offset `0`, requested/actual/IOSB information `550`, pending `259`, final/IOSB `0`, event signaled |
| `texturemorphs.bin` | `606..615`, handles `0xF8000304`/`0xF8000308` | write `610/611`, offset `0`, requested/actual/IOSB information `29479`, pending `259`, final/IOSB `0`, event signaled |

All binary open pairs use the same accesses, attributes, sharing,
dispositions, options, actions, and async state as the `mainsave.bin` pair.
Every file-handle close returned `0`. Finally, `XamContentClose` sequences
`616..618` used guest LR `0x82449C3C`, caller PC `0x82449C38`, overlapped
`0x701BF680`, and event `0xF8000300`; operation/final/extended error were `0`,
length was `0`, the event was signaled, and no callback/APC was queued.

All `NtCreateFile` events use guest LR/caller `0x82CC35F4/0x82CC35F0`;
asynchronous `NtWriteFile` uses `0x82CC702C/0x82CC7028`; synchronous writes use
`0x82CC7078/0x82CC7074`; `NtClose` uses
`0x82CC27D0/0x82CC27CC`. Current generated owner ranges are respectively
`sub_82CC3490 [0x82CC3490,0x82CC3684)`,
`sub_82CC6FB8 [0x82CC6FB8,0x82CC70E0)`, and
`sub_82CC27B0 [0x82CC27B0,0x82CC27F8)`. The content-create owner is
`sub_82CC4138 [0x82CC4138,0x82CC427C)`; the final close owner is
`sub_82449BD8 [0x82449BD8,0x82449C88)`.

The runtime log independently records `Save:` registration/unregistration for
devices 1, 2, 3, and 4 at lines `4821/4825`, `5763/5772`, `32717/32736`, and
`34113/34130`. Lines `34312` and `34320` record clean window shutdown and
`Title terminated; hard-exiting process.` No fatal, invalid/unregistered guest
function, or native exception is present.

### Pinned Canary comparison and conclusion

The captured success path matches the broad contract in pinned Canary commit
`32460b5d887dcde6622bb17983b70752fa5f13b3`: content create/open maps the same
dispositions and completes overlapped work; `NtCreateFile` returns a handle and
file action; nonsynchronous `NtWriteFile` performs the host operation, fills
the IOSB, signals the event, and returns pending; close releases each handle
and unmounts content. The compared implementations are ReXGlue
`src/kernel/xam/xam_content.cpp:140`, `src/kernel/xboxkrnl/xboxkrnl_io.cpp:104`
and `:430`, versus Canary `src/xenia/kernel/xam/xam_content.cc:281` and
`src/xenia/kernel/xboxkrnl/xboxkrnl_io.cc:39` and `:304`.

The known static differences (internal content-data shape, validation, header
lifecycle, async failing-result translation, and Canary's stubbed flush) were
not exercised as failures in this capture. ReXGlue's real
`NtFlushBuffersFile` succeeded. Therefore no runtime correction is justified
from capture 001. The original partial-write root cause is not statically
established and did not reproduce; current classification remains `unknown`.

### Focused reproduction and diagnostic correction

Before changing the report contract, the new synthetic test
`test_fresh_slot_does_not_require_later_conditional_payloads` reproduced the
false positive. Its first run failed because the report still emitted
`missing expected files` for `Fable2PubInfo.xml` and `failquestsave.bin`. After
the Xenia timestamp evidence was applied, the same test passed. Commit
`bbb47f42fd6d5656ba098fbf15e7a14e55f7cdb7` records:

- separate required-fresh and conditional-later payload contracts in the
  schema-1 report;
- the focused synthetic regression;
- a guarded `FreshNativeReload` state with separate `cache-002`, `capture-002`,
  State B baseline, log, and report paths;
- refusal to run reload from an empty State B or overwrite an existing capture;
- no runtime/ReXGlue behavior change.

The focused test initially failed as intended, then passed. The full Python
suite passed `70/70`; `python -m compileall -q tools tests`, three-schema
validation, PowerShell syntax parsing, corrected report generation, and guarded
reload `Status` passed. The first reload `Prepare` wrote the ignored State B
snapshot; a second invocation correctly failed with
`Refusing to overwrite the preserved State B snapshot`. The four capture-001
hashes were rechecked afterward and remained identical. Code generation and a
native rebuild were unnecessary because only Python, PowerShell, schema, tests,
and documentation changed; the diagnostic executable was re-hashed unchanged:

```text
C:\Dev\Fable2Recomp\out\build\win-amd64-native-save-diagnostic-release\fable2.exe
size:    105042944 bytes
SHA-256: E90F192FF212FC835CACB36E9B06E91CC2DC6C6843104CE983D0460A34E6ED0A
```

No Fable2Recomp, Xenia, or Xenia Canary process was launched during this
continuation. No original or isolated save payload was written by the analysis;
only ignored payload-free derived JSON/directories were created. No commit was
pushed and nothing was uploaded.

## Capture-002 reload analysis checkpoint (2026-09-03)

### Immutable artifacts and State B comparison

The original capture artifacts and the pre-reload snapshot were inspected in
place and not rewritten:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `state-B-after-write.json` | 3,514 | `3FA6858C6FA1986523492DEF1BFED6A817D74FAD206EA7A68809EAFAE2C0E498` |
| `capture-002/fable2-native-reload-002.log` | 816,890 | `2FC30522ECE26F8D4B5CA6626E58B2770605D23201D4E5E7B40E4E9F08B335D6` |
| `capture-002/save-diagnostic-report-v1.json` | 5,384 | `1599447A789D04376CAF22B29B195750581320F21820E7B956C0AB5F8E503767` |
| `capture-002/save-trace-events-v1.ndjson` | 26,978 | `C37C9AC23ECBA4386EC7456D180813B2FE1EB166C56B1998AFF8E3AC0DE8C799` |
| `capture-002/save-trace-run-v1.json` | 242 | `32EBC4417739787F71C9458EE2FC1D1AD65DB698FB4F8329545E9FF90F041A4D` |

The metadata records schema 1/event schema 1, PID `33844`, start time
`2026-09-03T17:40:38Z`, and `contains_payload_bytes: false`. A corrected,
payload-free derived report was written separately, without altering capture
002:

```text
C:\Dev\Fable2Recomp\out\native-save-diagnostic\analysis-capture-002\save-diagnostic-report-v1.json
size:    5937 bytes
SHA-256: 1DAB72936CBA11F7AD551B68166F616CD7972BEC11C30F3E6F83BBC0D437320F
```

An independent current-tree snapshot agrees with that report: no path was
added, removed, or content-changed. Every payload and header size/hash in the
State B table above is unchanged. Only three profile-setting mtimes changed:

| Relative path | Pre-reload `mtime_ns` | Post-reload `mtime_ns` | Size / SHA-256 |
| --- | ---: | ---: | --- |
| `4D5307F1/profile/User/63E83FFD` | `1788453659777578100` | `1788457238593603100` | `0` / `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` |
| `4D5307F1/profile/User/63E83FFE` | `1788453659776579800` | `1788457238592614700` | `0` / `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` |
| `4D5307F1/profile/User/63E83FFF` | `1788454808661876200` | `1788457238591605400` | `40` / `D625031097FE61E6CA97A975F3A5BB1EA1AE5832DE0DC2D41BF00AA0FB57DEBB` |

Runtime log lines `4713..4715` independently explain those metadata-only
changes as three `XamUserWriteProfileSettings` calls. They are not save-slot
payload updates.

### Enumeration and load result

**CONFIRMED:** a genuinely new process enumerated `Hero000`. Trace sequences
`1/2` return `item_count: 1`, `result: 0`, and enumerator handle
`0xF80001A4` from guest LR/caller `0x82443354/0x82443350` on guest thread 7.
After device selection, sequences `7/8` again return `item_count: 1`,
`result: 0`, and handle `0xF80001B8` from
`0x82443134/0x82443130`. Log lines `4712` and `4746` both say
`XamContentCreateEnumerator: added 1 items to enumerator`.

**CONFIRMED:** the process entered and completed the observable existing-slot
load path. It mounted `Hero000`, opened every required fresh-slot payload with
read access, closed every handle, closed the content root, continued into later
guest work, and exited cleanly. This is sufficient to rule out
`reload_enumeration_mismatch` and an observable create/open/close failure.

**PROBABLE, not artifact-proven:** the guest deserialized and restored the
meaningful saved state. Capture 002 predates `NtReadFile` tracing, and no user
visual observation was supplied with the capture. The trace therefore proves
the load path and file-open contract, not the byte counts consumed by the guest
or the resulting in-game state.

### Exact trace sequence

Events `1..72` are contiguous. Every captured final result is `0`; every
overlapped event is signaled; no APC or completion callback is requested. No
write, truncate, flush, rename, or replace operation occurs in the save trace.

| Sequences | Guest LR / caller PC | Exact operation and completion |
| --- | --- | --- |
| `1..2` | `0x82443354` / `0x82443350` | enum user `0`, device `0`, type `1`, flags `0`, 150 items/request, XUID `B13EBABEBABEBABE`; handle `0xF80001A4`, item count `1`, result `0` |
| `3..6` | `0x82441D84` / `0x82441D80` | selector user `0`, type `1`, flags `0`, requested `0`, overlapped `0x701BF9C0`; immediate `997`; device `1`; operation/final/extended `0`, length `0`; event `0xF80001B8` signaled, callback `0`, no APC |
| `7..8` | `0x82443134` / `0x82443130` | enum device `1`; handle `0xF80001B8`, item count `1`, result `0` |
| `9..12` | `0x82CC4264` / `0x82CC4260` | open `Save`/`Hero000`, user `254`, device `1`, type `1`, title `0x4D5307F1`, content/profile XUID `B13EBABEBABEBABE`, flags `3`, cache/size `0`, overlapped `0x701BF810`; immediate `997`; host disposition `2`; operation/final/extended `0`, length `2`; event `0xF80001BC` signaled |
| `13..16` | create `0x82CC35F4/0x82CC35F0`; close `0x82CC27D0/0x82CC27CC` | open `save:\chaptersave.bin`, root `0xFFFFFFFD`, access `0x80100080`, attrs `0x80`, share `1`, disposition `1`, options `0x48`; host `...\Hero000\chaptersave.bin`; handle `0xF80001C8`, action `1`, asynchronous, result `0`; close result `0` |
| `17..19` | `0x82449C3C` / `0x82449C38` | close content 1, overlapped `0x701BF810`; operation/final/extended `0`, length `0`; event `0xF80001BC` signaled |
| `20..30` | same create/open/close callsites | repeat chapter probe through `\Device\Content\2\`; content overlapped/event `0x701BFB50/0xF800024C`; chapter handle `0xF8000250`; all operation/final/close results `0` |
| `31..41` | same create/open/close callsites | repeat chapter probe through `\Device\Content\3\`; content overlapped/event `0x701BFA80/0xF8000250`; chapter handle `0xF8000254`; all operation/final/close results `0` |
| `42..45` | `0x82CC4264` / `0x82CC4260` | final `Hero000` mount through `\Device\Content\4\`; flags `3`, overlapped `0x701BF910`, immediate `997`, disposition `2`; operation/final/extended `0`, length `2`; event `0xF8000250` signaled |
| `46..49` | create/close callsites above | `save:\saveuid.bin`; handle `0xF8000254`, result/action `0/1`; close `0` |
| `50..53` | same | `save:\herosave.bin`; handle `0xF8000254`, result/action `0/1`; close `0` |
| `54..57` | same | first `Save:\Fable2PubInfo.xml` open: access `0x00100080`, attrs `0`, share `1`, disposition `1`, options `0x64`, synchronous; handle `0xF8000254`, result/action `0/1`; close `0` |
| `58..61` | same | second `Save:\Fable2PubInfo.xml` open: access `0x80100080`, attrs `0x80`, share `3`, disposition `1`, options `0x60`, synchronous; handle `0xF8000254`, result/action `0/1`; close `0` |
| `62..65` | same | `save:\texturemorphs.bin`; access `0x80100080`, attrs `0x80`, share `1`, disposition `1`, options `0x48`, asynchronous; handle `0xF8000254`, result/action `0/1`; close `0` |
| `66..69` | same | `save:\mainsave.bin`; same access/attrs/share/disposition/options/async contract; handle `0xF8000254`, result/action `0/1`; close `0` |
| `70..72` | `0x82449C3C` / `0x82449C38` | close content 4, overlapped `0x701BF910`; operation/final/extended `0`, length `0`; event `0xF8000250` signaled, callback `0`, no APC |

All resolved host paths are below exactly:

```text
C:\Dev\Fable2Recomp\out\native-save-diagnostic\B-fresh-native\B13EBABEBABEBABE\4D5307F1\00000001\Hero000
```

The trace records `NtCreateFile` result and IOSB-equivalent `file_action`, but
capture 002 does not record the raw create IOSB pointer/status. It contains no
`NtReadFile` event, so read offsets, requested/actual byte counts, read IOSB
status/information, read event handles, and pending state are unavailable. The
earliest such diagnostic-coverage gap is between successful chapter open
sequence `14` and close sequence `15`; it is not a demonstrated runtime
failure. The final payload-load opens have the same gap between each successful
open and close (`47/48`, `51/52`, `55/56`, `59/60`, `63/64`, and `67/68`).

Current generated owners are `sub_82443308 [0x82443308,0x824433A8)` for the
initial enum caller, `sub_82443048 [0x82443048,0x824431E8)` for the second enum,
`sub_82441CB8 [0x82441CB8,0x82441DE0)` for the selector,
`sub_82CC4138 [0x82CC4138,0x82CC427C)` for content open,
`sub_82CC3490 [0x82CC3490,0x82CC3684)` for file open,
`sub_82CC27B0 [0x82CC27B0,0x82CC27F8)` for handle close, and
`sub_82449BD8 [0x82449BD8,0x82449C88)` for content close.

### Exact log evidence and classification

The significant runtime log lines are:

```text
4711:[2026-09-03 18:40:38.587] [info] [sys] [t34028] Save-path trace enabled in 'C:\Dev\Fable2Recomp\out\native-save-diagnostic\capture-002' (schema v1)
4712:[2026-09-03 18:40:38.587] [debug] [krnl] [t34028] XamContentCreateEnumerator: added 1 items to enumerator
4713:[2026-09-03 18:40:38.591] [debug] [krnl] [t34028] XamUserWriteProfileSettings: setting index [0]: from=2 setting_id=63E83FFF data.type=6
4714:[2026-09-03 18:40:38.592] [debug] [krnl] [t34028] XamUserWriteProfileSettings: setting index [0]: from=2 setting_id=63E83FFE data.type=6
4715:[2026-09-03 18:40:38.593] [debug] [krnl] [t34028] XamUserWriteProfileSettings: setting index [0]: from=2 setting_id=63E83FFD data.type=6
4737:[2026-09-03 18:40:40.186] [debug] [krnl] [t34028] XamShowDeviceSelectorUI(00000000, 00000001, 00000000, 0000000000000000, 701BF9B4, 701BF9C0)
4743:[2026-09-03 18:40:40.287] [debug] [sys] [t25744] Deferred overlapped 701BF9C0: running completion
4744:[2026-09-03 18:40:40.287] [debug] [sys] [t25744] Deferred overlapped 701BF9C0: completing with result 00000000
4745:[2026-09-03 18:40:40.287] [debug] [sys] [t25744] Deferred overlapped 701BF9C0: running post_callback
4746:[2026-09-03 18:40:40.287] [debug] [krnl] [t34028] XamContentCreateEnumerator: added 1 items to enumerator
4747:[2026-09-03 18:40:40.287] [debug] [sys] [t34028] GetProcAddressByOrdinal: searching registry for '__imp__XamContentCreateInternal'
4748:[2026-09-03 18:40:40.287] [debug] [sys] [t34028] GetProcAddressByOrdinal: XamContentCreateInternal (0271) in xam -> thunk at 832CA03C
4761:[2026-09-03 18:40:40.488] [debug] [fs] [t25744] Registered symbolic link: Save: => \Device\Content\1\
4765:[2026-09-03 18:40:40.489] [debug] [fs] [t34028] Unregistered symbolic link: Save: => \Device\Content\1\
4876:[2026-09-03 18:40:47.864] [debug] [fs] [t25744] Registered symbolic link: Save: => \Device\Content\2\
4880:[2026-09-03 18:40:47.866] [debug] [fs] [t34028] Unregistered symbolic link: Save: => \Device\Content\2\
4886:[2026-09-03 18:40:47.967] [debug] [fs] [t25744] Registered symbolic link: Save: => \Device\Content\3\
4890:[2026-09-03 18:40:47.967] [debug] [fs] [t34028] Unregistered symbolic link: Save: => \Device\Content\3\
4947:[2026-09-03 18:40:48.841] [debug] [fs] [t25744] Registered symbolic link: Save: => \Device\Content\4\
5184:[2026-09-03 18:40:50.450] [debug] [fs] [t34028] Unregistered symbolic link: Save: => \Device\Content\4\
5186:[2026-09-03 18:40:50.450] [debug] [krnl] [t34028] XamContentCreateEnumerator: added 0 items to enumerator
5190:[2026-09-03 18:40:50.642] [debug] [krnl] [t34028] XGIUserSetContextEx(00000000, 00000004, 0000000E)
5191:[2026-09-03 18:40:50.642] [debug] [krnl] [t34028] XGIUserSetContextEx(00000000, 00000005, 0000000E)
5192:[2026-09-03 18:40:50.642] [debug] [krnl] [t34028] XGIUserSetContextEx(00000000, 00008001, 00000000)
6914:[2026-09-03 18:41:23.786] [info] [core] [t35532] Window closing, shutting down...
6926:[2026-09-03 18:41:23.987] [info] [core] [t35532] Title terminated; hard-exiting process.
```

The later `added 0 items` line is a separate content query after the successful
saved-game enumeration/load sequence; it does not negate sequences `1/2` and
`7/8`. No fatal, invalid/unregistered function, native exception, access
violation, or save failure occurs after trace activation.

Classification remains `unknown` with `first_anomaly: null`: the vocabulary has
no success classification, and no failure category was observed. In particular,
this is not `reload_enumeration_mismatch`, `path_translation_failure`,
`file_create_semantics_mismatch`, `overlapped_completion_mismatch`, or
`flush_or_close_mismatch`.

### Pinned Canary comparison and diagnostic gap

Pinned Canary commit `32460b5d887dcde6622bb17983b70752fa5f13b3`
performs the same observable existing-content and file-open contract. Its
`NtReadFile_entry` at
`src/xenia/kernel/xboxkrnl/xboxkrnl_io.cc:125` performs the host read, writes
IOSB status/information, queues an eligible APC, signals the event, and returns
`X_STATUS_PENDING` for a nonsynchronous handle except on end-of-file. Current
ReXGlue has the same broad behavior. No trace or log event exposes a semantic
divergence from that pinned source.

The confirmed defect was diagnostic coverage, not runtime semantics: ReXGlue
traced save-file create/write/flush/close but not `NtReadFile`. Before changing
the reporter, the focused synthetic reload test failed with
`KeyError: 'restart_observation'`. After the report change it proves one-item
enumeration plus successful required payload opens and preserves the absence of
read evidence. No runtime correction was made because capture 002 contains no
runtime failure to reproduce.

ReXGlue commit `b1bf7701dfd778f0b61d8a599cbb6e4690cf547a` adds disabled-by-default,
payload-free `NtReadFile` request/result events for save paths. Future captures
now retain guest path, resolved host path, handle, event/APC/IOSB addresses,
explicit/current offset, requested/actual counts, operation/immediate result,
IOSB status/information, event signaling, APC queuing, synchronous state, and
pending state. The schema remains event schema v1 because the versioned event
format already permits operation-specific fields. A focused unit test verifies
the metadata and absence of payload bytes.

Fable2Recomp commit `a2b7349916bbcbd24fcded85f3422aaf126c820a`
adds `restart_observation` to report schema v1 and teaches the parser to report
successful enumeration, required read-access payload opens, and whether
`NtReadFile` evidence exists. Commit
`748cff0b04875efb1e60e73b805ef4a089c54f6c` pins installed SDK
`0.10.0.47-dev.gb1bf770`.

The exact rebuilt diagnostic executable is:

```text
C:\Dev\Fable2Recomp\out\build\win-amd64-native-save-diagnostic-release\fable2.exe
size:    105042944 bytes
SHA-256: 187892D793E6E14DEF0E2D38ADB96F25BEDB2957C58778CCF9C1F48CA677565A

C:\Dev\Fable2Recomp\out\build\win-amd64-native-save-diagnostic-release\rexruntime.dll
size:    10332160 bytes
SHA-256: 226556412EFFA824343A4C3C112BB339FC00D1527642F70D7E5CBEB22A6B5D47
```

Validation completed without launching the title:

- The focused parser test first failed with
  `KeyError: 'restart_observation'`, then passed after implementation.
  `python -m unittest discover -s tests -p "test_*.py"` passed all 71 tests.
- `python -m compileall -q .\tools .\tests` passed. The first
  `validate-schemas` invocation omitted its required positional paths and
  printed the CLI usage error; the corrected command with all three save schema
  paths reported `Validated 3 schema files.` PowerShell `Test-Json -SchemaFile`
  reported `Schema instance valid: True` for the derived capture-002 report.
  An optional `jsonschema` Python check was unavailable because that third-party
  module is not installed; no package was installed.
- ReXGlue `cmake --build --preset win-amd64-release --target unit_tests`
  passed, and `unit_tests.exe "[save_trace]"` passed 5 test cases with 24
  assertions. After the ReXGlue commit, configuration and install succeeded as
  SDK `0.10.0.47-dev.gb1bf770`.
- `ctest --preset win-amd64-release --output-on-failure -j 8` passed 1,768
  of 1,768 ReXGlue tests; four pre-existing BitStream cases were skipped.
- Diagnostic `fable2_codegen` passed with `0 written, 0 unchanged, 0 deleted,
  1 module(s) up to date`; the exact diagnostic build linked successfully.
  The normal `fable2-build` helper also completed successfully against the
  same installed SDK.
- `Verify-Fable2EntrypointClosure.py` passed schema 3/analyzer 2.0.0 with
  35,626 candidates, 55 strong, 180 probable, and three fixtures;
  `Verify-Fable2MigrationLedger.py` passed all 32 Harvest/sibling entries; and
  `Verify-Fable2NativeRendererG1.py` validated all 11 candidates.
- `Invoke-Fable2NativeSaveDiagnostic.ps1 -Action Status -State XeniaUpdate`
  passed: State D and its baseline exist, `capture-D-001` is unused, and its
  configured paths match the next-procedure section below.

The exact payload-free report command was:

```powershell
python .\tools\Fable2SaveTrace.py report `
    --trace .\out\native-save-diagnostic\capture-002\save-trace-events-v1.ndjson `
    --metadata .\out\native-save-diagnostic\capture-002\save-trace-run-v1.json `
    --save-root .\out\native-save-diagnostic\B-fresh-native `
    --baseline .\out\native-save-diagnostic\state-B-after-write.json `
    --output .\out\native-save-diagnostic\analysis-capture-002\save-diagnostic-report-v1.json
```

It reported `Classification: unknown`, `event_count: 72`,
`first_anomaly: null`, maximum enumerated item count `1`, all required payloads
opened, and no `NtReadFile` event in this older capture.

No Fable2Recomp, Xenia, or Xenia Canary process was launched during this
analysis/rebuild continuation. The capture and State B payload were not
rewritten. Neither original backup was modified. Nothing was pushed or
uploaded.

## Next user procedure: isolated Xenia-origin update

Capture 002 is preserved and explained, so the next permitted interactive run
is the independent State D update. Do not reuse `FreshNative` or
`FreshNativeReload`; captures 001 and 002 are sealed.

1. Open PowerShell and verify the guarded state:

   ```powershell
   Set-Location C:\Dev\Fable2Recomp
   .\tools\Invoke-Fable2NativeSaveDiagnostic.ps1 -Action Status -State XeniaUpdate
   ```

   Confirm selected root `...\D-xenia-update`, baseline
   `...\state-C-reference.json`, trace directory `...\capture-D-001`, and
   `Capture already used: False`.

2. Launch exactly once through the helper:

   ```powershell
   .\tools\Invoke-Fable2NativeSaveDiagnostic.ps1 -Action Launch -State XeniaUpdate
   ```

3. Choose the existing `Hero000`/continue path through normal game UI. Confirm
   the Xenia-origin state loads, then play normally until one ordinary autosave
   is visibly triggered and its indicator completes. Fable II's normal
   autosave is the trigger; do not invent or use a manual-save menu path.

4. Exit cleanly if possible. If it hangs or crashes, record that fact and do
   not retry. Do not relaunch yet.

5. Generate the payload-free comparison report:

   ```powershell
   .\tools\Invoke-Fable2NativeSaveDiagnostic.ps1 -Action Report -State XeniaUpdate
   ```

6. Preserve `state-C-reference.json`, all files under `capture-D-001`, and the
   current ignored `D-xenia-update` tree. Resume the investigation before any
   restart/load attempt.

## Ready-to-paste continuation prompt

```text
Continue the Fable II native-save write-parity investigation from
docs/fable2-native-save-write-parity.md. Do not launch Fable2Recomp, Xenia, or
Xenia Canary. First inspect state-C-reference.json, every capture-D-001
artifact, and the current D-xenia-update tree under
C:\Dev\Fable2Recomp\out\native-save-diagnostic. Compare State D to its
pre-update State C snapshot before changing or launching anything. Identify the
first attempted update operation and the earliest failed, missing, short, or
semantically divergent event against pinned Xenia Canary commit
32460b5d887dcde6622bb17983b70752fa5f13b3. Preserve exact guest LR/caller PC,
handles, paths, flags, offsets, requested/actual byte counts, results, IOSB,
event/APC/completion state, and log lines. Determine whether the Xenia-origin
slot remained coherent after the update, but do not launch a restart/load until
the update capture is preserved and explained. Keep both repositories on
fable2-native-save-write-parity, preserve ReXGlue's pre-existing dirty
thirdparty/libmspack submodule, and do not push or upload anything.
```

## Remaining work blocked solely on runtime interaction

- obtain or record the user's visual confirmation that capture 002 restored
  the expected meaningful State B gameplay state;
- update the isolated Xenia-origin State D and prove complete, non-corrupting
  update semantics;
- restart after that update and prove enumeration/load durability;
- perform a native-origin update-in-place and another full-process reload;
- retain tracing disabled by default and rerun the interactive gameplay
  regression.

No native-save parity claim is valid until meaningful restart/load and safe
update/restart checks pass.
