# Xenia indirect-target collection and reviewed bulk manifest import

## Outcome and validation boundary

Phase 4 implementation is complete. A pinned Xenia Canary build records actual
resolved guest indirect transfers, and Fable2Recomp now turns one or more raw
traces into deterministic summaries and a dry-run evidence import plan. The
canonical manifest is changed only by a separate, explicit, reviewed, guarded
apply command.

The implementation has five distinct validation levels:

| Level | Status |
| --- | --- |
| Collector and tools implemented and unit-tested | complete |
| Collector exercised by minimal PPC under Xenia's real JIT | complete |
| Collector exercised by two bounded legacy loose-XEX boots with TU1 applied | complete, collector evidence only |
| Corrected complete-media ISO workflow preflight | complete; launch pending user gameplay |
| Collector exercised through interactive private-TU1 gameplay coverage | pending user gameplay |

The two private-title runs are **not** described as gameplay. They booted the
loose base XEX with Xenia reporting title-update application from `0.0.0.26`
to `0.0.1.26`, then were deliberately terminated after bounded non-interactive
collection. They remain valid collector/identity evidence, but they do not
validate complete disc-media mounting. Both raw streams therefore have a
usable final checkpoint but no footer and are correctly classified as
`abnormal_or_unknown_no_footer`. The corrected ISO workflow has been
preflighted without launching Xenia and awaits the next user gameplay run.

The merged automated evidence contains 6,358 stable source/target/branch pairs,
279,936 hits and 6,039 distinct non-return targets. All 6,039 targets are
explained by current function, internal-entry, switch-case or import evidence.
There are zero proposed ranges, zero automatically applicable candidates, zero
ambiguous targets and zero conflicts. The manifest remained byte-identical at
SHA-256
`E3EB39CA153E396D5DC53E6F943ED8FF7AF1D6B0704EB860836BD7D21A3F87B0`.

The required golden addresses were not reached during these bounded boots.
They are instead exercised by a committed address-only raw fixture through the
same production closure, Ghidra, generated-registration and manifest inputs.
That distinction prevents synthetic evidence from being presented as gameplay
observation.

## Starting audit and exact identities

Before source changes, every applicable `AGENTS.md` was read in the two
canonical repositories and the external Xenia checkout. Every Markdown file
under `C:\Dev\Fable2Recomp\docs` was enumerated and read, including all Phase
1-3 discovery documents, the fault-walker baseline and the Run 047 handoff.
The referenced schemas, analyzers, generated registration tables, manifest
parser, fixtures, tests and wrappers were then inspected directly.

The fixed Fable2Recomp starting point was verified exactly:

| Property | Value |
| --- | --- |
| repository | `C:\Dev\Fable2Recomp` |
| origin | `https://github.com/FenrisSkoll/Fable2Recomp.git` |
| starting branch | `main` |
| starting commit | `efd625d0b9635119df85d61d005d754714c2205e` |
| starting tree | `2363af6698bbc2e1ade01bfe19e49ca37814e73a` |
| first parent | `564c2adb3e281f15ee03593e966355c8138a15a7` |
| second parent | `ed16e1ec208b27e9f4af6832eb8d732b7d688f1f` |
| Phase 4 branch | `fable2-phase4-indirect-targets` |
| Phase 4 implementation commit | `f14cec668e94dbf6014a2c829b5ec1b0cc9c4a0f` |
| implementation tree | `bdb754aee4b95421612a7b51419b351566eac6b4` |

`git diff efd625d0^2 efd625d0` was empty, as required. The Phase 4 branch was
created from that exact merge; `main` was not changed.

The ReXGlue starting and final integration identities are:

| Property | Value |
| --- | --- |
| repository | `C:\Dev\rexglue-sdk-v0.10` |
| origin | `https://github.com/FenrisSkoll/rexglue-sdk.git` |
| branch | `fable2-v0.10-migration` |
| starting commit | `16d7915550676121667a5155a96216e9e42bbad8` |
| starting identity | `0.10.0.42-dev.g16d7915` |
| Phase 4 commit | `956c6a8b5da4c54b9899a2593e9c67c26de30194` |
| Phase 4 tree | `b78b06b8ac650467372236a3a262864e069a9382` |
| installed identity | `0.10.0.43-dev.g956c6a8` |
| isolated install | `C:\Dev\Fable2Phase4Xenia\rexglue-install-956c6a8` |
| installed CLI SHA-256 | `4AD185FA7642BB39CD8F3E0C529BC5A155224A869E09B83FE81A1F659EB43E5D` |

The SDK change is deliberately generic and limited to accepting shared
entrypoint-evidence contract schema 4. It changes one source file and does not
add a Fable-specific runtime facility. The locally materialised, unstaged
`thirdparty/libmspack` state was never cleaned, reset, staged or committed.

The exact private title identity remains:

| Property | Value |
| --- | --- |
| complete-game launch media | `D:\Fable2-Recomp\disc\Fable II - Game of the Year Edition.iso` |
| analysis base XEX | `D:\Fable2-Recomp\tu1\default.xex` |
| base XEX SHA-256 | `88C4EF2E18E65409444D1B068EFF921D1F7E180A5AE64EDC64BA6B0872372662` |
| extracted XEXP SHA-256 | `046A05693B4DA4437083C784000A850858B3BF992955C7DB30D518FB3E53E41C` |
| STFS container file | `TU_16L61VH_0000038000000.000000000008Q` |
| STFS container SHA-256 | `B36EB38CE1DB9E1195DEA494C8E75D5AB4BE737DCEF10565EF16A415DE27524C` |
| contiguous loaded post-patch image SHA-256 | `BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00` |
| executable-memory fingerprint | `5C8B78B84C93028D166E3DF347206E6642BA40BF374AD1AF8D958B2211320357` |
| Xenia loaded-module fingerprint algorithm | `sha1_contiguous_loaded_executable_memory` |
| pinned Xenia loaded-module fingerprint | `341151E9932EC14CB4F520AA9DE35BCF7169BFE1` |
| image base / size / entry | `0x82000000` / `0x01620000` / `0x82CC21C0` |
| title / media / version | `0x4D5307F1` / `0x716F0A0D` / `0.0.1.26` |

The launch-media and analysis-image identities are separate layers. The ISO is
complete game media and is passed only as Xenia's final positional argument;
preflight deliberately does not calculate or substitute its SHA-256. The
analysis base XEX and adjacent XEXP establish the inputs for the canonical
post-patch image SHA-256. The loaded-module SHA-1 is likewise not relabelled as
that SHA-256. The trace header retains the configured canonical post-patch
SHA-256, and post-run validation independently requires the repeatable observed
Xenia module fingerprint, title metadata and executable ranges.

The validated pre-Phase-4 native host executable remains:

```text
B8822AA5051FA64DE8EF008808E86F93B219C2AAC3A4839D4043F3CAD7C2A9F0
```

The newly linked Phase 4 Release executable is the same size, 105,042,944
bytes, but has SHA-256:

```text
EEACEAA8DB38E728B79F4F78B0298B7036E13EB4903518C503199697FA64AE6F
```

This is recorded as a new build identity, not relabelled as the prior validated
binary. The full fault-walk and dispatch-only binaries are respectively:

```text
C0734DB44DB26813FC981EDB15B8548995F69FD5D03FB3E4F98AE5E6594CE442
02F14F87BCFD047FAD14A132DE862FBE6A93258164B2D33C374B5D62D5148B6C
```

`Get-Command caveman -ErrorAction SilentlyContinue` found the installed
PowerShell function. The requested literal `caveman --help` was not a help
mode for that function and failed by trying to resolve `--help` as a path.
Caveman was not used, so no exact evidence or source was compressed.

## Analysis baseline consumed by Phase 4

The production planner consumes the existing shared evidence contract rather
than maintaining a disconnected Phase 4 database. The verified current inputs
are:

| Input | Exact result |
| --- | --- |
| entrypoint-closure schema/analyzer | schema 3 / `2.0.0` |
| entrypoint candidates | 35,626 |
| strong / probable candidates | 55 / 180 |
| closure JSON SHA-256 | `665CA2AE7ED65632B2E9F368063D3D9EE260E8DEF6F276B455CD62A9F2DCC397` |
| Phase 3 jump-table schema/analyzer | schema 3 / `3.0.0` |
| recovered switch sites / distinct case targets | 878 / 9,002 |
| unresolved relevant non-link CTR sites | 711 |
| jump-table JSON SHA-256 | `B1FE26FB9119DAF7E7E0196CBDBA8CCA087BE190BF156FE0B12DF116379ED89A` |
| Ghidra catalog / exact functions | 9 records / 42,462 functions |
| exact Ghidra map SHA-256 | `03516B3A1F33433E493739418C9939D4FF1AEB0989F4ACEF2FD4D8204A077F58` |
| migration ledger | 32 entries |
| exact generated recomp registrations | 60,425 |

The 342-table / 3,170-case result in the original Phase 3 report was verified,
but it is a historical stage result rather than the final current input. The
durable Phase 3 document explicitly supersedes it first with 877 / 9,000 and
then, after the generic Run 047 correction, with 878 / 9,002. Phase 4 uses the
current corrected report and preserves the 711 remaining non-link CTR sites as
unresolved static coverage rather than silently claiming closure.

Shared evidence schema 4 adds only Phase 4 provenance: STFS identity, the
pinned Xenia module fingerprint and the Run 047 source/target ownership record.
Closure reports remain schema 3. Both the Python verifier and ReXGlue CLI ignore
container-only fields when checking a schema 1-3 report, so the old report
contract is not retroactively changed.

## Xenia selection, source and licences

Current primary repositories were inspected rather than assuming a historic
URL:

- Xenia master: `https://github.com/xenia-project/xenia`
- Xenia Canary: `https://github.com/xenia-canary/xenia-canary`

Canary was selected because it is the maintained behavioural-reference fork
used for this title and its current title-update path was needed for the
private TU1 validation. It was checked out separately; no Xenia source was
vendored into Fable2Recomp.

| Property | Value |
| --- | --- |
| checkout | `C:\Dev\Fable2Phase4Xenia\xenia-canary` |
| origin | `https://github.com/xenia-canary/xenia-canary.git` |
| pinned upstream base | `3a44f20c7bc66db1da583e8a6f0ab740e31908e9` |
| local collector branch | `fable2-phase4-indirect-targets` |
| production collector commit | `59cfa2b2d8748e1144a4090fcdbc1227fefdf3ec` |
| final test/benchmark head | `006830ee34596ce94f5ff9ac5b10ee5569a2c1e2` |
| final tree | `a60624c54d07b780f2fd4b951a8bc46076d1af79` |
| licence | BSD 3-Clause, root `LICENSE` |
| licence SHA-256 | `3D58F25C15634B6EC01D1F133EF798209AE06626AB8D2227B6223D5A9F5113F4` |
| final Release executable SHA-256 | `25EA275AF5CD8A3EFB781C4AD2142032DCD13A6E71CC1541761E0EA752BFC446` |

The collector commit changes 15 files with 1,575 insertions and 6 deletions.
It adds the collector, HIR branch flags, x64 and AArch64 backend hooks, module
fingerprints, thread buffers, configuration, lifecycle integration and 650
lines of collector/synthetic-PPC tests.

Public build dependencies acquired outside the canonical repositories were:

| Dependency | Pin or artifact | Licence / exact identity |
| --- | --- | --- |
| LunarG Vulkan SDK | `https://vulkan.lunarg.com/sdk/home`, Windows x64 `1.4.357.0` installer | component licences in the official SDK licence registry; installer SHA-256 `81F474711E9042F4CD22B31B2F7A8870DB2E428B21586FB43DD80150BE97310D` |
| SPIRV-Tools | `https://github.com/KhronosGroup/SPIRV-Tools.git` at `33e02568181e3312f49a3cf33df470bf96ef293a` | Apache-2.0; `LICENSE` SHA-256 `3DDF9BE5C28FE27DAD143A5DC76EEA25222AD1DD68934A047064E56ED2FA40C5` |
| SPIRV-Headers | `https://github.com/KhronosGroup/SPIRV-Headers.git` at `2a611a970fdbc41ac2e3e328802aed9985352dca` | MIT; `LICENSE` SHA-256 `841A6E68E16BFC98DB8ECA98D7002D4F2B508C56CE865FD6F1726BE30ED489EB` |
| glslang | `https://github.com/KhronosGroup/glslang.git` at `a57276bf558f5cf94d3a9854ebdf5a2236849a5a` | project licence bundle including BSD-3-Clause; `LICENSE.txt` SHA-256 `7D4C1655BE3A4D99E8A4859335E28C8950F2E7F72DCF3EED3379846120F5BF47` |
| Cygwin setup | `https://cygwin.com/setup-x86_64.exe`, setup `2.937` | GPL-family setup sources at `https://sourceware.org/cygwin-apps/setup.html`; SHA-256 `2C9F2FB56E1FB687B5D9680AFA8F8B06E6214F0E483096AF0EAE1946431226C5` |
| GNU binutils source | Xenia-pinned `third_party/binutils/binutils-2.24.tar.gz` | GPLv3+; archive SHA-256 `4930B2886309112C00A279483EAEF2F0F8E1B1B62010E0239C16B22AF7C346D4` |

The reproducible source pinning pattern was:

```powershell
git clone https://github.com/xenia-canary/xenia-canary.git `
    C:\Dev\Fable2Phase4Xenia\xenia-canary
git -C C:\Dev\Fable2Phase4Xenia\xenia-canary checkout `
    3a44f20c7bc66db1da583e8a6f0ab740e31908e9
git -C C:\Dev\Fable2Phase4Xenia\xenia-canary switch -c `
    fable2-phase4-indirect-targets
```

The ignored extracted binutils source needed one local current-Cygwin
compatibility condition in `libiberty/pex-unix.c`:

```c
#if defined(HAVE_SPAWNVE) && defined(HAVE_SPAWNVPE)
```

The resulting file SHA-256 is
`4AC66FAB1D735B3FCCEE85CA0A4BDBEB88A061B570979487E89ECC0E8A4788B7`.
This build-only external patch is not in either canonical repository or the
Xenia collector commit.

No private executable, title update, raw trace, save, memory dump or compiled
artifact was uploaded or added to Git.

## Existing Xenia tracing audit

At the pinned Canary base, the following facilities were inspected in source
and configuration:

```text
trace_functions
trace_function_coverage
trace_function_references
trace_function_data
trace_function_data_path
```

They provide function statistics, coverage, references or function data, but
not the required runtime tuple. In particular, no existing output preserves
all of resolved guest source PC, resolved guest target PC, `bctr` / `bctrl` /
non-standard `bclr`, link state, source and target module, stable guest thread,
run provenance, return filtering, aggregate ordering, drop/error state and a
crash-tolerant checkpoint. Existing tracing was therefore insufficient.

Current Xenia has no separate production PPC interpreter backend to patch.
PPC control instructions lower through common HIR into x64 or AArch64 JIT
backends. Phase 4 adds branch-kind flags at PPC lowering and equivalent hooks
in both backends at the point where the resolved guest target is available and
before control is transferred. The hook does not change guest registers,
condition state, memory or target selection.

## Collector architecture

```text
PPC bcctrx / bclrx lowering
  -> HIR indirect-call flags (CTR/LR, link, ordinary-return)
  -> x64 or AArch64 resolved-target hook
  -> guest-thread-local fixed-capacity aggregate table
  -> bounded flush under the output lock
  -> append-safe JSONL pair records + checkpoint
  -> final footer on orderly Processor shutdown
```

Collection is disabled by default. An empty
`--indirect_target_trace_path` means the Processor creates no collector,
ThreadState allocates no collector buffer, and generated JIT code contains no
collector callback. Enabling must happen before title code is compiled.

The hot path uses one fixed-size open-addressed table per guest thread. It does
not allocate, perform filesystem I/O or take a contended global lock per
transfer. The default capacity is 256 unique pairs per guest thread and the
default flush interval is 4,096 hits; both are bounded by validation. A flush
aggregates/writes under one output lock. Guest thread keys use Xenia's guest
ThreadState ID, for example `guest:00001234`.

Default capture includes actual resolved:

- non-linking `bctr`;
- linked `bctrl`;
- relevant linked or non-standard `bclr` forms.

Ordinary `blr` is omitted by default and can be included only with
`--indirect_target_trace_include_returns=true`. Default module filtering keeps
title-module source sites while still retaining cross-module target identity.
`--indirect_target_trace_all_modules=true` enables diagnostic source capture
outside the title.

Each aggregate retains source and target guest PCs, branch kind, link state,
ordinary-return status, module names, guest thread, hit count, first/last
per-thread sequence and target validity. Counter addition saturates at
`UINT64_MAX` and increments an overflow counter. Buffer exhaustion, dropped
hits, I/O errors and count overflows are surfaced in checkpoints and the final
footer.

The collector refuses to overwrite an existing raw path. A header is flushed
before execution; module records are appended after module discovery and after
title-update application; every completed batch is followed by a checkpoint;
and normal shutdown appends a footer. The parser accepts a missing footer and
an incomplete final JSON line, but rejects corruption in the middle of a
stream. Thus an abnormal process stop loses at most the unflushed in-memory
batch and incomplete final line, with dropped/error status preserved through
the last complete checkpoint.

## Versioned schemas and deterministic reports

Committed schemas are:

```text
tools/schemas/xenia-indirect-targets-raw-v1.schema.json
tools/schemas/fable2-indirect-target-summary-v1.schema.json
tools/schemas/fable2-indirect-target-import-plan-v1.schema.json
```

The raw JSONL record schema is `xenia_indirect_targets_raw` version 1. Record
kinds are `header`, `module`, `pair`, `checkpoint` and `footer`. The summary
and import plan are independently named and versioned at 1.

`tools/Fable2IndirectTargets.py` streams raw input line by line. Stable summary
content is sorted by source module, source PC, target module, target PC, branch
kind and link state. Run IDs, raw SHA-256 values and per-run hit counts remain
attached to every pair. Volatile wall-clock metadata is not added during
summary or plan generation.

Multi-run merge rejects duplicate run IDs, duplicate raw hashes and different
expected image identities. A raw run whose configured SHA-256, title metadata,
module ranges or pinned loaded-module fingerprint disagrees is quarantined and
does not contribute pairs. Equivalent forward and reverse merges are
byte-identical.

The standard files are:

```text
xenia-indirect-targets.raw.jsonl
xenia-indirect-targets.summary.json
xenia-indirect-targets.summary.csv
fable2-indirect-targets.import-plan.json
```

JSON and CSV writes use a same-directory temporary file, `fsync` and atomic
replace. Raw data and per-run reports live under ignored `out\indirect-targets`.

## Planner, classifications and size policy

The planner compares every non-return runtime target with:

- the canonical manifest and current generated registration table;
- exact trusted function ranges and `.pdata`/exception entries;
- Phase 1 candidates and boundary provenance;
- exact-image and related-build Ghidra records;
- Phase 3 dispatch/case ownership;
- callable internal labels and known range interiors;
- shared manual, fault-walker and Run 047 provenance;
- executable, import, kernel and module ranges.

Every conclusion retains its contributing evidence, source PCs, branch kinds,
run IDs, counts, conflicts and rejection reasons. It uses exactly these public
classifications:

```text
existing_manifest_function
existing_function_internal_entry
known_jump_table_case
known_exception_landing_pad
known_import_or_kernel_target
strong_new_function
probable_new_function
ambiguous_target
invalid_or_non_executable_target
conflicting_range
```

An observed target proves execution at that address. It does not prove a
function boundary or size. A range is proposed only from independent exact-TU1
boundary evidence: a trusted non-preliminary closure range, exact `.pdata`, an
exact-image contiguous Ghidra body or agreeing strong sources. Related-build
Ghidra records are retained but marked unable to authorise TU1 size or
ownership. Disagreeing exact sources produce `conflicting_range`.

A target owned by another function remains an internal entry. A recovered
switch target remains `known_jump_table_case` unless separate callable
evidence exists. A `bctr`-only target cannot be automatically applied without
exact `.pdata`; this prevents switch-like dispatch from receiving the policy
used for virtual/callback `bctrl` evidence. Runtime targets are never sized by
distance to another runtime target.

## Dry-run and guarded apply

`summarize`, `merge`, `plan` and `post-run` never mutate the manifest. The
canonical workflow is:

```text
raw traces -> deterministic summaries -> merge -> dry-run plan
           -> human review/selection -> explicit guarded apply
```

Apply requires all of:

- the `apply` subcommand;
- literal `--apply`;
- one or more reviewed stable candidate IDs, directly or in a selection file;
- a plan whose integrity-derived plan ID validates;
- a candidate whose independent evidence permits guarded application;
- the exact manifest SHA-256 stored in the plan;
- no existing duplicate, conflicting entry or overlapping range.

The edit is formatting-preserving for the existing file and adds only a TOML
function-size line plus the reviewed candidate ID. It writes a
`fable2_manifest.toml.phase4.bak` recovery copy and atomically replaces the
manifest. Reapplying an already present identical selection is a no-op. A stale
manifest, modified plan, unknown candidate, ambiguous candidate or overlap is
rejected with a non-zero exit. No code path writes C++, a placeholder body,
`RETURN_R3_ZERO` or any other stub.

Example review/apply syntax, not an instruction to accept any current target:

```powershell
python .\tools\Fable2IndirectTargets.py apply `
    --plan .\out\indirect-targets\RUN\review\fable2-indirect-targets.import-plan.json `
    --manifest .\fable2_manifest.toml `
    --select P4-REVIEWED-CANDIDATE-ID `
    --apply
```

No canonical candidate was applied in Phase 4 because the automated private
trace produced no proposals.

## Synthetic acceptance and mandatory cases

The Xenia test executes minimal big-endian PPC through the real host JIT. A
host-supplied `r5` prevents constant propagation from turning the transfer
direct. The workload records:

```text
0x80000004 bctr  -> 0x80000020
0x80000008 bctrl -> 0x80000020
0x80000008 bclr  -> 0x80000020
```

All enabled and disabled variants return `r3=42` and preserve
`r4=0x1122334455667788`. Default collection contains no `blr`; optional-return
mode records it with `ordinary_return=true`. This directly verifies that
instrumentation does not alter the workload's register/control-flow result.

The committed address-only fixtures and Xenia tests cover all required cases:

| Requirement | Verification |
| --- | --- |
| virtual and callback `bctrl` | synthetic pairs plus the two known leaf fixtures |
| switch and computed-tail `bctr` | Run 047 fixture remains a case; synthetic computed tail is not auto-applicable |
| non-standard `bclr` | real synthetic linked PPC plus no-op manifest fixture |
| ordinary `blr` | absent by default, retained only in diagnostic mode, ignored by planner |
| cross-module/import | external module and generated `__imp__` registrations classify as import/kernel |
| repeated pairs and guest threads | deterministic per-run/thread aggregation and hit counts |
| buffer limits/drop/I/O/overflow | Xenia capacity tests and Python saturating-counter fixtures |
| normal/abnormal/truncated data | normal footer, missing footer, incomplete tail and corrupt-middle tests |
| disabled collection | no callback buffer and no output file |
| duplicate/schema/image guards | duplicate content/run IDs rejected; mismatches quarantined |
| related-build evidence | retained but cannot authorise exact TU1 edit |
| deterministic merge | forward/reverse bytes identical |
| all ten classifications | exact synthetic ownership/range fixtures |
| size hierarchy/ambiguity/conflict | `.pdata`, exact Ghidra, CFG, disagreement and no-size cases |
| dry-run/stale/atomic/idempotent apply | temporary CRLF manifests with comment and backup verification |
| stub prohibition | source assertion and post-apply byte assertion |

The exact mandatory production-fixture result is:

| Runtime evidence | Production classification | Result |
| --- | --- | --- |
| `0x829647F0–0x82964800`, size `0x10` | `existing_manifest_function` | no proposal, no change |
| `0x82C03B28–0x82C03B44`, size `0x1C` | `existing_manifest_function` | no proposal, no change |
| `0x829675E0–0x829675F0`, size `0x10` | `existing_manifest_function` | no proposal, no change |
| `0x823DCAD8 -> 0x82174734` | source retained for `known_jump_table_case` | no proposal, no change |
| `0x82403720 -> 0x82174734` | source retained for `known_jump_table_case` | no proposal, no change |
| target `0x82174734` | internal switch case owned by `0x821746A8` | manifest entry forbidden absent independent callable evidence |

Two independent production runs of the canonical fixture produced identical
bytes:

| Artifact | SHA-256 |
| --- | --- |
| summary JSON | `96FF1C62F21EC57BDFC3D797DE06447990C4AC9B9453D34827528F9572F22BAD` |
| summary CSV | `C399154E89F174490D54EE3A3C993C82025EF4C0C5B282D03CD378C71454E667` |
| import plan | `E2E1FFA0F842BAA1E5002DE9FE6F88D94D94C6BB5D0125A6C1B2D2E0B73E0CC0` |

The plan contains four targets from five pairs: three
`existing_manifest_function`, one `known_jump_table_case`, no range proposal
and no manifest mutation.

## Automated private-TU1 collection

Two ignored local raw streams from the original loose-XEX workflow were
retained for collector review. They are not evidence that the corrected ISO
launch path works:

| Run | Raw bytes / SHA-256 | Last complete checkpoint |
| --- | --- | --- |
| `phase4-automated-smoke-001` | 6,072,773 / `75C8DE3C1A88DCEA6F023CB329E622C36EE224CFEA5D81EF310A0C1441EA169D` | 157,184 hits; 15,789 pair records; 0 dropped; 0 I/O errors; 0 overflows |
| `phase4-fingerprint-repeat-002` | 5,341,451 / `E507DF33DDA98D213516B5C30F7DC6FB68AAE2C5AE0428D6D222DEBCFBA0DD5E` | 122,752 hits; 13,836 pair records; 0 dropped; 0 I/O errors; 0 overflows |

Both logs identify build `fable2-phase4-indirect-targets@59cfa2b2d` and contain:

```text
XEX patch applied successfully: base version: 0.0.0.26, new version: 0.0.1.26
```

Both runs independently observed the pinned module fingerprint
`341151E9932EC14CB4F520AA9DE35BCF7169BFE1`. Neither run was quarantined.
Their stable pair set was identical even though hit counts and thread ordering
differed. These traces exercise production collector commit `59cfa2b2d...`.
The final Xenia head adds only the periodic-flush benchmark; the production
collector implementation is byte-identical.

Merged classification is:

| Classification | Targets |
| --- | ---: |
| `existing_manifest_function` | 5,897 |
| `existing_function_internal_entry` | 108 |
| `known_jump_table_case` | 29 |
| `known_import_or_kernel_target` | 5 |
| proposed / ambiguous / conflicting | 0 / 0 / 0 |
| total | 6,039 |

The five exact generated import targets were:

| Target / symbol | Hits | Source PCs |
| --- | ---: | --- |
| `0x832B9CE4` / `__imp__KeTlsGetValue` | 11 | `0x82CB2CE4`, `0x82CB2E34` |
| `0x832B9CF4` / `__imp__KeTlsSetValue` | 2 | `0x82CB2D74`, `0x82CB3148` |
| `0x832B9D84` / `__imp__NtClose` | 14 | `0x82CC27CC` |
| `0x832B9EF4` / `__imp__NtCreateFile` | 8 | `0x82CC35F0` |
| `0x832BA114` / `__imp__NtQueryInformationFile` | 2 | `0x82CC7BE4`, `0x82CC7CEC` |

Forward and reverse merges have the same hashes:

| Artifact | Bytes / SHA-256 |
| --- | --- |
| summary JSON | 6,386,327 / `91C82761E8078C6D861AE88C4388357D594A49DC1037939F56BDD297FD1184C0` |
| summary CSV | 1,436,586 / `8ACF2505F85CB1BB1677DEE4D96614FA8A57C6DEC7BC0517CA31441A34166FCD` |
| import plan | 16,598,359 / `154F3BAE45216B5CA9913F16F26E10B54A244EE1CCC0A635EE3196D2819BB9B9` |

The four golden targets above were not present in either bounded boot. Their
required results come from the canonical committed fixture and Run 047 shared
evidence, not from these two runs.

## Builds and automated validation

Key commands used were:

```powershell
# Fable2Recomp Phase 4 tests
python -m unittest discover -s tests -p 'test_*.py'
python -m compileall -q tools tests

# Existing analysis verification
.\tools\Invoke-Fable2EntrypointClosure.ps1
python .\tools\Verify-Fable2EntrypointClosure.py
python .\tools\Fable2FunctionMap.py validate-catalog
python .\tools\Fable2FunctionMap.py validate-ledger
python .\tools\Fable2FunctionMap.py validate-map
python .\tools\Fable2FunctionMap.py diff

# Fable code generation and builds
fable2-codegen
fable2-build
cmake --build --preset win-amd64-fault-walk-release
cmake --build --preset win-amd64-fault-walk-dispatch-release
fable2-run
fable2-log

# ReXGlue
ctest --test-dir .\out\build\win-amd64 -C Release -j 8 --output-on-failure

# Xenia Canary
.\xb.ps1 build --config release --build-tests
.\xb.ps1 build --config release --target xenia_canary.exe
.\build\bin\Windows\Release\xenia-base-tests.exe
.\build\bin\Windows\Release\xenia-cpu-tests.exe
.\build\bin\Windows\Release\xenia-cpu-tests.exe '[collector]~[.benchmark]'
.\build\bin\Windows\Release\xenia-cpu-tests.exe '[.benchmark][collector]'
.\build\bin\Windows\Release\xenia-kernel-tests.exe
.\build\bin\Windows\Release\xenia-vfs-tests.exe
.\build\bin\Windows\Release\xenia-cpu-ppc-tests.exe
```

Exact results:

| Validation | Result |
| --- | --- |
| current Fable Python repository suite | 45/45 tests PASS in 2.462 s on the final no-launch preflight regression |
| Phase 4 indirect-target module | 17/17 tests PASS in 0.273 s, including four launch-media regressions |
| raw JSON schema | 40/40 committed JSONL records PASS |
| summary/plan schemas | both production fixture artifacts PASS |
| closure verifier | schema 3; 35,626 candidates; 55 strong; 180 probable; all mandatory fixtures PASS |
| Ghidra catalog | 9/9 records PASS |
| exact Ghidra map | 42,462 functions PASS; 0.727 s; peak working set about 370 MB |
| Ghidra diff | 52,994 differences; report-only; manifest unchanged; 11.608 s; peak about 1.776 GB |
| migration ledger / registrations | 32/32 entries; 60,425 exact recomp registrations |
| Fable codegen | 0 written, 0 unchanged, 0 deleted; 0.2 s |
| Fable Release build | 301 steps PASS; 113.143 s; subsequent no-op build 0.286 s |
| fault-walk builds | full and dispatch Release builds PASS |
| ReXGlue CTest | exit 0; 1,761/1,761 test records PASS in 10.6 s; four intentional BitStream skips |
| Xenia base | 3,562 assertions / 75 cases PASS |
| Xenia CPU | 933 assertions / 253 cases PASS |
| Xenia collector-only | 108 assertions / 7 cases PASS |
| Xenia kernel | 267 assertions / 5 cases PASS |
| Xenia VFS | 1 assertion / 1 case PASS |
| Xenia collector benchmark test | 170 assertions / 1 case PASS |

The official Xenia PPC fixture corpus discovered and loaded 568/568 suites.
Across 141,726 comparisons, 141,725 passed and 28,687 cases were skipped. The
single failure was the pre-existing `frsp_12_GEN` NaN-payload comparison and
does not execute the new indirect branch path. Runtime was approximately 9 min
37 s. This is reported as a failure, not converted into a pass.

A bounded post-build native Run 048 used `fable2-run`, reached asynchronous
loading and was deliberately terminated without claiming an exit code. Exact
log identity:

```text
C:\Dev\Fable2Recomp\fable2-run-048.log
631,212 bytes
5,311 lines
SHA-256 893C6143A43598DE0F79D3B9370C70E11182ECE803D8828F27CEE4BBD6A5FD6D
```

It contains zero matches for invalid/unregistered dispatch, fault-walker
activity, `REX_FATAL`, fatal/critical diagnostics, assertions, host exceptions,
access violations or `0xC0000005`. This is a bounded no-input smoke test, not
Run 047 gameplay revalidation.

## Performance

The Xenia microbenchmark executes the same minimal dynamic PPC transfer through
the real x64 JIT for seven paired samples of 200,000 transfers. Disabled samples
compile without the collector callback and produce no raw file. Enabled samples
use a huge flush interval to measure the aggregate hot path, then time final
flush separately.

Final measured result:

| Metric | Result |
| --- | ---: |
| disabled ns/transfer, min / median / max / mean / population SD | 21.595 / 21.945 / 22.290 / 21.923 / 0.211 |
| enabled ns/transfer, min / median / max / mean / population SD | 26.062 / 27.301 / 35.962 / 28.168 / 3.252 |
| median enabled/disabled ratio | 1.244036 |
| enabled with periodic flush, min / median / max / mean / population SD | 26.840 / 27.052 / 28.712 / 27.405 / 0.628 ns |
| default periodic flush interval / observed median delta | 4,096 hits / -0.249 ns per transfer, not resolved above sample noise |
| final flush, median / max | 0.0219 ms / 0.0315 ms |
| repeated-pair raw size | 1,841 bytes |
| periodically flushed repeated-pair raw size | 28,555 bytes for 200,000 hits |
| 10,000 unique-pair throughput / raw size | 917,826.953 events/s / 3,735,707 bytes |
| per-thread fixed buffer allocation | 12,368 bytes |
| four-thread aggregate workload | 1,000,000 events at 637,795,777.792 events/s |

The four-thread number measures independent thread-local hot paths plus one
final flush per worker; it is evidence against per-event global lock
contention, not a gameplay frame-time claim. The measured 24.4% median enabled
cost applies to this deliberately branch-dense synthetic workload. Real-game
overhead remains to be measured during user gameplay. The periodic-flush lane
was slightly faster at the median than the no-periodic-flush lane; its -0.249
ns difference is smaller than the sample variation and is therefore reported
as unresolved, not as a speedup. Its output-size effect is measurable.

The deterministic merge of both private summaries took 418.0151 ms. Planning
all 6,039 targets against the closure, generated registrations and exact
Ghidra map took 5,187.4663 ms. A second forward/reverse run reproduced the
exact output hashes above.

Guarded apply was benchmarked for 21 measured iterations after three warmups on
a 201-byte CRLF temporary manifest:

| Operation | Min / median / max / mean / population SD |
| --- | --- |
| first atomic apply | 6.1503 / 6.5947 / 77.9491 / 13.3279 / 20.8700 ms |
| idempotent reapply | 0.5835 / 0.7016 / 1.3708 / 0.7565 / 0.1878 ms |

Every iteration verified backup creation, comment/CRLF preservation,
idempotence and absence of a stub marker. Fable codegen produced no changed
files because Phase 4 adds analysis tooling rather than manifest entries.

## Reproducible collection workflow

The checked-in wrapper uses the exact Canary checkout/build, validates the
private inputs and leaves output under the ignored Fable2Recomp `out` tree.
`-GamePath` is complete game media and defaults to the GOTY ISO.
`-AnalysisImagePath` is the base XEX used with its adjacent XEXP to validate
the expected post-patch analysis identity; it is never appended to Xenia's
normal gameplay argument list. The former conflated `-TitlePath` parameter was
removed so an old command fails visibly rather than silently launching a loose
XEX.

Preflight requires a supported complete-media extension, rejects standalone
`.xex`/`.elf` launch targets, verifies collection is enabled, verifies the raw
path does not exist, and checks that its parent and Xenia storage are writable.
It validates the base XEX/XEXP/STFS hashes and requires this exact installed TU
directory:

```text
C:\Dev\Fable2Phase4Xenia\content\0000000000000000\4D5307F1\000B0000
```

Its JSON report separately prints launch media, analysis image inputs, content
root, TU directory/package, storage root, title ID, media ID, version and
expected patched analysis-image SHA-256.

From `C:\Dev\Fable2Recomp`:

```powershell
.\tools\Invoke-Fable2XeniaIndirectTrace.ps1 `
    -Action Preflight `
    -RunId fable2-tu1-manual-001 `
    -Label 'Fable II GOTY TU1 manual gameplay coverage' `
    -GamePath 'D:\Fable2-Recomp\disc\Fable II - Game of the Year Edition.iso' `
    -AnalysisImagePath 'D:\Fable2-Recomp\tu1\default.xex' `
    -ContentRoot 'C:\Dev\Fable2Phase4Xenia\content' `
    -StorageRoot 'C:\Dev\Fable2Phase4Xenia\storage'
```

Read the emitted command and identity report. Then launch:

```powershell
.\tools\Invoke-Fable2XeniaIndirectTrace.ps1 `
    -Action Launch `
    -RunId fable2-tu1-manual-001 `
    -Label 'Fable II GOTY TU1 manual gameplay coverage' `
    -GamePath 'D:\Fable2-Recomp\disc\Fable II - Game of the Year Edition.iso' `
    -AnalysisImagePath 'D:\Fable2-Recomp\tu1\default.xex' `
    -ContentRoot 'C:\Dev\Fable2Phase4Xenia\content' `
    -StorageRoot 'C:\Dev\Fable2Phase4Xenia\storage'
```

The emitted Xenia array retains, among the other collector arguments, this
ordering and identity separation:

```text
--indirect_target_trace_image_sha256=BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00
--content_root=C:\Dev\Fable2Phase4Xenia\content
--apply_title_update=true
--storage_root=C:\Dev\Fable2Phase4Xenia\storage
D:\Fable2-Recomp\disc\Fable II - Game of the Year Edition.iso
```

The ISO is the final positional argument. PowerShell invokes the executable
with an argument array, and the printed reproducible command single-quotes
every argument, so spaces in the GOTY filename are preserved.

The no-launch `phase4-media-correction-preflight` run passed against the real
local inputs. It reported `sha256_calculated=false` for the ISO, validated the
base XEX, XEXP and installed STFS hashes, printed title `0x4D5307F1`, media
`0x716F0A0D`, version `0.0.1.26`, and placed the GOTY ISO last in the generated
argument array. No raw collector file was created and Xenia was not launched.

Committed tests additionally prove that hashing the ISO is an error, the
collector image argument remains
`BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00`,
standalone XEX/ELF launch media is rejected, a missing installed-TU directory
is rejected, and the spaced ISO path remains one quoted argument.

After closing Xenia, validate, summarize and dry-run the importer:

```powershell
.\tools\Invoke-Fable2XeniaIndirectTrace.ps1 `
    -Action PostRun `
    -RunId fable2-tu1-manual-001
```

Post-run never applies a proposal. Review these files:

```text
out\indirect-targets\fable2-tu1-manual-001\xenia-indirect-targets.raw.jsonl
out\indirect-targets\fable2-tu1-manual-001\review\xenia-indirect-targets.summary.json
out\indirect-targets\fable2-tu1-manual-001\review\xenia-indirect-targets.summary.csv
out\indirect-targets\fable2-tu1-manual-001\review\fable2-indirect-targets.import-plan.json
```

Before accepting the trace, confirm the adjacent Xenia log contains the exact
title-update success line and the summary reports
`module_fingerprint_match=true`, zero quarantine, and acceptable
drop/I/O/overflow counters.

Useful manual coverage is:

- boot, title flow and an existing save load;
- childhood and adult-era paths where safely available;
- Bowerstone Market and region transitions;
- dialogue, crowd/NPC AI, shops and inventory/equipment;
- melee, ranged and Will combat;
- quests, scripted scenes and cutscenes;
- save and reload only if the user chooses a safe slot.

This is a subsystem checklist, not input automation. No controls were
discovered, no menu/gamepad bot was created, and no story progress is claimed.

## Limitations and next investigation boundary

- Interactive private-TU1 gameplay collection and gameplay-overhead sampling
  remain pending user action.
- The corrected complete-game ISO workflow has passed preflight but has not yet
  launched Xenia. The earlier automated streams used the loose-XEX workflow
  and must not be described as complete-media validation.
- Both automated private boot streams ended without a footer. Their last
  checkpoints are valid and error-free, but an orderly-shutdown sample is
  still desirable.
- The two automated runs observed the same boot pair set; they do not imply
  whole-game indirect-target coverage.
- The static Phase 3 report still contains 711 unresolved relevant non-link CTR
  sites. Runtime evidence should prioritize new gameplay systems and runs,
  then correlate only newly observed targets rather than treating all 711 as
  functions.
- No currently observed target is proposed, ambiguous or conflicting. There is
  therefore no real candidate on which canonical explicit apply should be
  demonstrated.
- The microbenchmark is repeatable and branch-dense but is not a substitute for
  gameplay frame-time measurement.
- The black dog and black player skin/head from Run 047 remain a separate
  GPU/skinned-character material or texture-path defect. Saving remains
  untested, not failed. Neither was investigated in Phase 4.

The safest next action is the three-command Preflight / Launch / PostRun manual
workflow above. Review its dry-run plan before considering any manifest edit.

## Commits and worktree policy

Local commits created for Phase 4 are:

```text
Fable2Recomp  f14cec668e94dbf6014a2c829b5ec1b0cc9c4a0f
ReXGlue SDK   956c6a8b5da4c54b9899a2593e9c67c26de30194
Xenia Canary  59cfa2b2d8748e1144a4090fcdbc1227fefdf3ec
Xenia metrics 006830ee34596ce94f5ff9ac5b10ee5569a2c1e2
```

The documentation commit is the commit containing this file; obtain its full
identity with:

```powershell
git log -1 --format=%H -- docs/fable2-discovery-pipeline/05-xenia-indirect-targets.md
```

At the implementation checkpoint, Fable2Recomp and Xenia had clean tracked
worktrees. ReXGlue was ahead of its branch by the one Phase 4 commit and had
only the required unstaged `thirdparty/libmspack` materialisation. External
Xenia build/dependency outputs and private trace data remain outside Git or in
ignored output directories.

Nothing was pushed. No remote branch, pull request, tag, release, asset or
external upload was created. Neither repository's `main` branch was updated.
