# NR0B-1 runtime closeout

**CONFIGURATION VERIFIED — READY FOR NR0B-2**, reviewed 2026-09-10.
EXP-CONFIG-CAP-001 is complete for this launch and its one-time initialization
snapshot. The user loaded ordinary gameplay outside Oakfield Inn and exited
normally; the process handle independently recorded exit code **0**.
No renderer seam, rendering correctness or frame-contract recorder is qualified.

The reviewed [metadata ledger](evidence/runtime-review.json) retains actual
records, identities, the user report verbatim and the two explicit dispositions
of the original parser's partial result. Raw files were read, never rewritten.

## Latest launch identity, including the recreated folder

Use this complete launch identity, not the reused run-ID string alone:

| Item | Latest launch evidence |
|---|---|
| Run ID | `nr0b1-oakfield-20260910-001` |
| Recreated preparation timestamp | `2026-09-10T15:11:27.574326+00:00` |
| PID | `27668` |
| Actual start UTC | `2026-09-10T17:24:23.5099166Z` |
| Actual end UTC | `2026-09-10T17:25:34.4411796Z` |
| Exit code | `0`, from the launched process handle |
| Allocated log | `C:\Dev\Fable2Recomp\fable2-run-004.log` |
| Log size / SHA-256 | 989466 / `C36B71B578DB40DDDFE5612A8DA90DACEA268AB9CD07EBA50CF240A7F457A04D` |
| `process.json` SHA-256 | `682CF50A6F88668E0C140BB3652F10DA314265A511A01E4B2FD54E520F4EA9B5` |
| Original `effective-report.json` SHA-256 | `24EEF5462E7C1085249B7177634B396DCD55E998A95D7AEAE854F58C9FE59829` |

`process.json` names log 004 in its log field, launch arguments and observed
CIM command line. All nine records reparsed directly from **004** exactly match
`effective-report.json`. Their run IDs match the recreated preparation, and
all timestamped log lines fall inside the recorded process lifetime using the
log's +01:00 offset (Europe/London in September). The first log timestamp is
18:24:23.572; shutdown records appear at 18:25:34.099 and 18:25:34.300 before
the process terminates. This fixes the historical early-return ambiguity.

The preceding attempt's `fable2-run-003.log` is excluded from runtime findings.
It still matches the restoration record: 654415 bytes, SHA-256
`882EB89739B465230EB91693B86684E0C54ED853BE4B4DD407D5C29FFB4EC5EF`.
The folder was recreated at the user's explicit request; the latest run is
distinguished by PID/start time/log identity and the recreated preparation hash,
not by assuming that a reused directory or run ID is globally unique.

## Loaded images and Tracy disposition

The process monitor observed these three images in the session's `runtime`
directory. Full absolute paths and observation times are in the ledger.
All match staging and the unchanged files rechecked during closeout.

| Loaded image | Bytes | SHA-256 |
|---|---|---|
| `fable2.exe` | 105042944 | `1642ED03BD8B117A8FED6E9FF912AD49CBF0E91A4E1D226B20C266925E3FF2C9` |
| `rexruntime.dll` | 10380288 | `D325FA4296577565137AD9480A258CE65AD071D9C538C0362783F89725B111B6` |
| `rexgpu-xenos.dll` | 2817024 | `6DBD1336DC219D8181DF65D4AB179512400ED6A7BF5FDAEACE29A7162EDD3BB8` |

These are **RUNTIME-CONFIRMED** module paths with contemporaneous on-disk
size/hash observations, not hashes of process memory. Source identity remains
separate: Fable launch preparation HEAD
`12c0a4b1e97abd624d431e65a60c1812b3456dc6`, tree
`7cab501505edd1c30de0d8bfbd129b729130dd93`; reporting SDK
`06c4b7002a449ad4d173ec90c625e490ed03fe74`, tree
`5feea2389d0ce264ab970bf7807ee4ae6bd7960d`.

`TracyClient.dll` was staged but **not observed loaded** during the monitor's
bounded observation. It is **NOT APPLICABLE as a required loaded module for
these audited Release images**. Read-only `llvm-readobj --coff-imports` on all
three exact images shows no Tracy imports. SDK `CMakeLists.txt` at the reporting
commit excludes `REXGLUE_ENABLE_PROFILING` from Release;
`include/rex/perf/counter.h` gates Tracy calls on that define.
`thirdparty/CMakeLists.txt` builds the library, while
`cmake/rexglue_helpers.cmake` can stage it even when the final image does not
import it. Exact source blobs and import lists are retained in the ledger.
The staged Tracy file remains 232960 bytes, SHA-256
`FDBE7A329E1B06A86FE61A2C5BE6B335F32F9BBCA7E05F7B183A35C515D2D1A5`.

The parser initially assumed every staged DLL must be observed loaded. Its
`Loaded artifact missing/mismatch: TracyClient.dll` finding is resolved by
this source/binary review, without inventing a loaded identity or relaxing
checks on the actual EXE/runtime/GPU images. The original report and strict
parser remain unchanged. This is not a general exemption for future builds:
profiling-enabled builds need their own dependency/loaded-module assessment.
The second pending item is resolved by the user's explicit scene/load/normal-
exit confirmation, independently corroborated by process termination evidence.

## Effective device and configuration

All values below are **RUNTIME-CONFIRMED** records from log 004, with the
scopes shown. Capability query success does not imply the rendering path uses
every advertised feature or that a visual symptom's cause has been found.

| Field | Observation / requested-versus-effective distinction |
|---|---|
| Plugin / host API | Requested `xenos` from command line; plugin load logged; selected device `d3d12` |
| Adapter | NVIDIA GeForce RTX 5080; requested index `-1`, selected index `0`; vendor `0x10DE`, device `0x2C02` |
| LUID | `00000000:0000C6A4`, machine/session scoped, not persistent across reboots/machines |
| Driver | `32.0.16.1664`, selected adapter `CheckInterfaceSupport(IDXGIDevice)`, HRESULT `0x00000000`; API source caveat retained from the [report contract](effective-configuration.md) |
| OS / create feature level | `Microsoft Windows NT 10.0.26200.0` from `System.Environment.OSVersion`; device creation level `11_0`, not maximum supported feature level |
| OPTIONS | HRESULT `0x00000000`; ROV support `true`, resource-binding tier `3`, tiled-resource tier `4` |
| OPTIONS13 | HRESULT `0x00000000`; alpha blend-factor support `true` |
| PIX | Not attached at initialization |
| RT path | Requested empty/vendor default; effective **RTV**. ROV capability exists but was not selected; no unavailable-ROV fallback occurred |
| Bindless | Requested `true`, effective `true` |
| Tiled shared memory | Requested `true`, effective `true`, reserved resource created |
| Resolution scale | Requested X/Y `1`/`1`; effective `1`/`1`, not clamped |
| First guest output | `1280 × 720`, first valid swap output only |
| First host present | `3840 × 2160`, successful HRESULT `0x00000000`; may precede gameplay |
| Internal extent | Unavailable as one global value: multiple target extents |
| Anisotropy | Policy `anisotropic_override=3` (source maps this to 4× for eligible textures); actual per-sampler filtering unobserved |
| Page-state clearing | `clear_memory_page_state=true`, policy snapshot |
| Async compilation | Requested `true`; worker request `-1`, actual count `15`; async policy applies to eligible pipelines with pixel shaders |
| Vsync / presentation | Guest `vsync=true`; separate host `Present` sync interval `0`, RESTART `true`, ALLOW_TEARING `true` |

All recorded rendering CVars above have source `default`; `gpu_plugin` has
source `command_line`. No configuration-file identity was silently substituted:
baseline and staged exe-adjacent `fable2.toml` remain absent. Runtime root
records match the explicit isolated user/cache roots and canonical game/update
roots. These records do not describe later resizes, every gameplay target or
individual draw-time policies. A 4K first host present does not establish 4K
internal rendering or spatial parity.

Supported loader logs report successful patch application from `0.0.0.26` to
`0.0.1.26`, and shader storage identifies title `0x4D5307F1`. Base XEX/XEXP
disk hashes still match the accepted chain in [provenance](preparation-and-provenance.md).
Runtime media identity and a freshly measured post-patch memory hash remain
unavailable; the inherited TU1 image hash is not upgraded to runtime evidence.

## Saves, cache and visible symptoms

Source and preserved checkpoint still match the complete 14-file inventory.
The writable copy contains two changes, both isolated from those roots:

- `B13EBABEBABEBABE/4D5307F1/00000001/Hero000/mainsave.bin`: 415039 → 420928 bytes; new SHA-256 `D2783E257A5866BF7AD122D80961DDA7673C94F8C39E34F35FBAB183CE7E7888`.
- `4D5307F1/profile/User/63E83FFF`: still 40 bytes; new SHA-256 `78C4EBF61DDB6DAEB09BA8D55DA9244E0564A589CF80D28CCBED35C8302F71A9`.

Full before/after hashes are in the ledger; all other files, including the
native header and both cache files, are unchanged. No source save, preserved
copy, baseline runtime or staged runtime was modified during closeout.

The effective cache root and shader/pipeline paths point into the writable
session. It began with copied baseline `.xsh` and `.rtv.d3d12.xpso` material;
the log reports creation of 652 graphics pipelines from storage, corroborating
use of that material. No benchmark is inferred from the logged initialization
timing. Driver-cache contents/isolation remain unknown; a fully warmed gameplay
cache is not proved. Missing optional DXIL-disassembly support is logged, not
proof of a shader translation or texture fault.

User confirmation (**PROJECT-REPORTED**, retained verbatim):

> Loaded scene: Stood outside Oakfield Inn
>
> Gameplay loaded normally: yes
>
> Visible symptoms noticed: Character and dog textures not loaded / black / blank
>
> Exited normally: yes
>
> PowerShell helper returned: yes

Black/blank surfaces are an observed user symptom. “Textures not loaded” is
not promoted to a diagnosed resource-loading failure. There is no per-draw
shader/fetch/material evidence here, and no proof that RTV/ROV selection,
cache state, alpha blend capability or a future native renderer explains or
fixes the symptom. Known non-blocking log warnings do not invalidate the
configuration records, but successful initialization/exit is not visual parity.

## Validation and boundary

The read-only reconciliation (`out/nr0b1/review-run-004.py`) reparsed only log
004 with the existing parser, checked all raw-report equality, launch timing,
module identities, selected paths, title corroboration and post-run integrity.
Raw session files and both existing logs retain their hashes. No parser output
was overwritten to obtain a pass. The reviewed ledger is the explicit closeout
disposition; historical preparation evidence remains intact.

Existing G1, NR0A/preserved-state and default GPU-reference checks, relevant
Python tests, Markdown links, JSON/source-blob checks and Git hygiene were run
for closeout. Strict GPU artifact verification retains the same three missing
historical logs and four historical/current hash comparisons; no new exception
is assigned to those checks. Detailed results are appended to
[completion](nr0b1-completion.md).

No second run, session recreation, rebuild, runtime/GPU source change,
architecture survey, NR0B-2 implementation, merge or push occurred during this
closeout. Next is separately authorized NR0B-2 metadata work under the unchanged
[limits and dependency requirements](nr0b2-handoff.md). ReXGlue retains current
renderer/runtime ownership. The new writable endpoint is retained as run
evidence, not silently promoted over the protected source checkpoint.
