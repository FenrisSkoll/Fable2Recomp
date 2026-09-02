# Xenia indirect-target collection and reviewed bulk manifest import

## Current outcome

Phase 4 is implemented, and the September 2026 aggregation/footer repair is
complete in source, schemas, automated tests and synthetic Xenia execution.
The repaired collector:

- aggregates repeated indirect transfers in fixed per-guest-thread dirty maps;
- persists only deltas changed since the previous durable batch;
- uses time, dirty-pair, capacity, thread-exit, explicit-flush and shutdown
  triggers instead of a tiny hit-count trigger;
- explicitly finalizes from Xenia's window-close lifecycle before
  `std::quick_exit`;
- emits raw schema 2 with checkpoint-committed delta semantics;
- retains parser compatibility with schema 1 and usable footerless captures;
- keeps runtime dispatch sites distinct from retained historical/manual
  corroboration;
- leaves manifest planning dry-run-only by default.

The collector repair itself performed no gameplay. The user subsequently
created `fable2-tu1-manual-002`, and the compact summary confirms a normal
schema-2 run with one footer and zero drops, I/O errors, count overflows or
aggregate-limit failures. The summary schema does not retain the footer's
`flush_reason`, so `window_close` is not inferred from compact evidence alone.
The September 2026 summary-merge work also launched no Xenia process.

The earlier private run `fable2-tu1-manual-001` remains accepted evidence. Its
stored label remains verbatim:

```text
Fable II GOTY TU1 manual gameplay through first successful save
```

The old artifact is not rewritten to claim different metadata. User-confirmed
coverage is recorded separately below. Its compact summary and import plan
remain usable, but the old collector generated about 90.9 GiB of raw JSONL and
Xenia's normal window close produced no footer. The raw file was intentionally
deleted only after the compact evidence was preserved.

The canonical `fable2_manifest.toml` was not changed. The merged dry-run plan
for manual-001 and manual-002 contains 16,143 observed non-return targets, no
range proposals, no ambiguous or conflicting targets and no automatically
applicable candidates.

Closeout also materializes a deterministic, report-only static-ownership queue
for the 567 targets contributed only by manual-002. The queue contains 42
existing-function internal entries, 114 known jump-table cases and 411
existing effective registrations. It is deferred evidence, not a manifest
proposal; native save-write parity remains the next active development phase.

## Repair baseline and repository state

The repair began in the canonical worktree `C:\Dev\Fable2Recomp`, not the
stale `C:\Dev\Fable2Phase4Capture` worktree.

| Repository | Repair starting state | Repair implementation state |
| --- | --- | --- |
| Fable2Recomp | branch `fable2-phase4-xenia-media-correction`, commit `112d16d07d4f6d220a923e34ec4ab9938702b3be` | code/schema/fixture commit `9c46998a993ea2046b1e9a873d7d9521eb2f44ad` |
| Xenia Canary | branch `fable2-phase4-indirect-targets`, commit `006830ee34596ce94f5ff9ac5b10ee5569a2c1e2` | repair commit `6b6715b029d442ff6ed5a89773f119400b1c19b5`, tree `e79833e62b875e0ce23201a2cc4d31529b4cbaf7` |
| ReXGlue SDK | `C:\Dev\rexglue-sdk-v0.10`, branch `fable2-v0.10-migration`, commit `956c6a8b5da4c54b9899a2593e9c67c26de30194` | unchanged by this repair; expected unstaged `thirdparty/libmspack` materialisation preserved |

The Fable documentation/provenance synchronization commit is the commit
containing this file. Obtain it with:

```powershell
git log -1 --format=%H -- docs/fable2-discovery-pipeline/05-xenia-indirect-targets.md
```

Xenia remains a separate checkout. No complete Xenia tree is vendored into
Fable2Recomp.

Repair components are:

- Xenia `indirect_target_collector.{h,cc}` and `cpu_flags.{h,cc}` for dirty
  aggregation, persistence policy, schema 2 and footer accounting;
- Xenia `processor.{h,cc}`, `emulator.{h,cc}` and `app/xenia_main.cc` for the
  explicit normal-shutdown lifecycle;
- Xenia `indirect_target_collector_test.cc` for real synthetic PPC,
  concurrency, failure, stress and performance coverage;
- Fable `Fable2IndirectTargets.py`, raw schema 2, Phase 4 fixtures and tests for
  committed-batch recovery and deterministic summaries;
- shared evidence/function-map support for schema 5 provenance separation;
- the GPU-reference provenance verifier, which pins the immutable G1.6 blob
  separately from the new current shared-evidence blob.

## Identity layers and launch media

The gameplay launch and analysis identity are deliberately different concepts.

| Layer | Exact value and use |
| --- | --- |
| complete launch media | `D:\Fable2-Recomp\disc\Fable II - Game of the Year Edition.iso`; final positional Xenia argument; not hashed as the analysis image |
| analysis base XEX | `D:\Fable2-Recomp\tu1\default.xex` |
| base XEX SHA-256 | `88C4EF2E18E65409444D1B068EFF921D1F7E180A5AE64EDC64BA6B0872372662` |
| adjacent XEXP SHA-256 | `046A05693B4DA4437083C784000A850858B3BF992955C7DB30D518FB3E53E41C` |
| patched TU1 analysis-image SHA-256 | `BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00` |
| TU content directory | `C:\Dev\Fable2Phase4Xenia\content\0000000000000000\4D5307F1\000B0000` |
| title / media / version | `0x4D5307F1` / `0x716F0A0D` / `0.0.1.26` |
| image base | `0x82000000` |
| executable range | `0x82170000`-`0x832D0000` |
| observed loaded-executable fingerprint | SHA-1 `341151E9932EC14CB4F520AA9DE35BCF7169BFE1` |

The wrapper passes `--content_root=C:\Dev\Fable2Phase4Xenia\content` and
`--apply_title_update=true`, and passes the GOTY ISO last. It never substitutes
the ISO SHA-256 for the patched executable-image SHA-256. A standalone
`.xex`/`.elf` is rejected as normal gameplay launch media.

## Xenia source, licence and existing tracing audit

The collector checkout is:

| Property | Value |
| --- | --- |
| path | `C:\Dev\Fable2Phase4Xenia\xenia-canary` |
| origin | `https://github.com/xenia-canary/xenia-canary.git` |
| upstream base used for Phase 4 | `3a44f20c7bc66db1da583e8a6f0ab740e31908e9` |
| pre-repair collector/metrics head | `006830ee34596ce94f5ff9ac5b10ee5569a2c1e2` |
| repaired collector head | `6b6715b029d442ff6ed5a89773f119400b1c19b5` |
| repaired tree | `e79833e62b875e0ce23201a2cc4d31529b4cbaf7` |
| licence | BSD 3-Clause, root `LICENSE` |
| licence SHA-256 / bytes | `3D58F25C15634B6EC01D1F133EF798209AE06626AB8D2227B6223D5A9F5113F4` / 1,505 |
| repaired Release executable | 17,271,808 bytes; SHA-256 `A8107146A41CE9020C790F208937D247372989DB88337E8D313B03B8C94DB0C4` |

The original Phase 4 audit inspected `trace_functions`,
`trace_function_coverage`, `trace_function_references` and
`trace_function_data_path` in current Canary source. Those facilities do not
provide the complete runtime tuple required here: resolved guest source and
target, branch form and link state, source/target module, stable guest thread,
run identity, ordinary-return filtering, durable aggregate counts, ordering
and drop/error state. The custom collector remains necessary.

PPC `bcctrx` and `bclrx` lower through common HIR. Existing Phase 4 hooks in the
x64 and AArch64 backends call the collector only after the guest target is
resolved and before the transfer. The repair does not alter those HIR/backend
hooks, guest registers, condition state, memory or target selection.

Public dependencies and their prior Phase 4 pins remain as recorded:

| Dependency | Pin / identity | Licence |
| --- | --- | --- |
| Xenia Canary | `https://github.com/xenia-canary/xenia-canary.git`, base `3a44f20c7bc66db1da583e8a6f0ab740e31908e9` | BSD-3-Clause |
| SPIRV-Tools | `33e02568181e3312f49a3cf33df470bf96ef293a` | Apache-2.0 |
| SPIRV-Headers | `2a611a970fdbc41ac2e3e328802aed9985352dca` | MIT |
| glslang | `a57276bf558f5cf94d3a9854ebdf5a2236849a5a` | project licence bundle including BSD-3-Clause |
| LunarG Vulkan SDK | Windows x64 1.4.357.0 | component licences in the SDK |
| GNU binutils | Xenia-pinned 2.24 archive | GPLv3+ |

No additional public dependency was downloaded for this repair.

## Confirmed root causes

### Raw amplification

Schema-1 buffers were flushed and cleared every 4,096 indirect hits. A hot game
loop reached that threshold continuously. Every flush serialized every pair in
that small interval and emitted a checkpoint, even when the same pair was the
only thing that changed. The completed capture therefore contained:

| Metric | Old capture |
| --- | ---: |
| indirect hits | 24,555,201,598 |
| unique summary pairs | 26,632 |
| unique pair/thread observations in the compact summary | 31,448 |
| raw pair records | 253,054,385 |
| checkpoints | 6,142,998 |
| raw size | about 90.9 GiB |
| dropped hits / I/O errors / count overflows | 0 / 0 / 0 |

This was not one record per hit. It was repeated delta serialization driven by
a hit threshold that was far too small for a branch-dense title.

### Missing clean footer

Xenia's window close calls
`EmulatorApp::ShutdownEmulatorThreadFromUIThread` and then
`std::quick_exit`. Before the repair that function did not finalize the
collector. The only collector shutdown was reached from
`Processor::~Processor`, but `quick_exit` bypasses ordinary destructor
ordering. The user's normal close therefore left a complete checkpointed tail
with no footer:

```text
flush_status:          abnormal_or_unknown_no_footer
corrupt_tail:          false
missing_final_newline: false
integrity_warnings:    []
```

The repair hooks explicit collector finalization into the window-close path.
The destructor remains an emergency/idempotent fallback; normal correctness no
longer depends on it.

### Jump-table fixture provenance

The old acceptance fixture treated Run 047's retained historical/manual source
sites as if every new Xenia capture had to observe them as live dispatch
instructions. The new capture correctly saw the local switch instruction
`0x821746BC -> 0x82174734`. Run 047's `0x823DCAD8` and `0x82403720` are
corroborating historical path/source evidence, not required live source PCs in
every trace.

Shared evidence schema 5 and runtime-indirect evidence schema 2 now encode
those provenance categories separately.

## Repaired aggregation architecture

```text
resolved indirect transfer in generated code
  -> disabled fast rejection, or guest-thread fixed dirty map
  -> cache-local atomic gate (no per-hit global file lock)
  -> dirty-pair / capacity / timer / explicit / thread-exit trigger
  -> sorted delta pair batch under the writer lock
  -> matching checkpoint + fflush
  -> offline deterministic cross-batch/run aggregation
```

Collection remains disabled by default. With an empty
`--indirect_target_trace_path` the Processor creates no collector, ThreadState
allocates no buffer, generated JIT code contains no collector callback and no
file is created.

When enabled, one preallocated open-addressed map belongs to each live guest
ThreadState. The recording path:

- performs no JSON formatting, console output, filesystem access or allocation;
- never takes the registry or global writer mutex for an ordinary hit;
- takes only the buffer's cache-local atomic gate;
- aggregates by guest thread, source PC, target PC and branch flags;
- preserves a 64-bit delta hit count plus exact first/last per-thread sequence;
- saturates only at `UINT64_MAX` and increments `count_overflows` explicitly;
- excludes ordinary `blr` by default;
- retains `bctr`, `bctrl` and relevant non-standard `bclr`;
- keeps cross-module targets and validity instead of treating them as Fable
  manifest candidates.

Production defaults are:

| Setting | Default | Bound / meaning |
| --- | ---: | --- |
| `indirect_target_trace_buffer_pairs` | 4,096 | per-thread fixed dirty-map capacity; clamped 16-65,536 |
| `indirect_target_trace_dirty_pairs` | 3,072 | persist before the table is full |
| `indirect_target_trace_flush_interval_ms` | 300,000 | five-minute durability timer; zero disables timer; clamped to 24 hours |
| `indirect_target_trace_max_unique_aggregates` | 1,000,000 | bound for footer-only unique pair/thread accounting |

A production-size 4,096-entry buffer measured 196,680 bytes. The four-thread
stress allocation was 786,720 bytes. The separate footer unique-key set is
bounded at one million entries. Reaching that bound does not discard pair
evidence; it sets `unique_aggregate_count_complete=false` and increments
`aggregate_limit_exceeded`.

Flush reasons are explicit:

```text
buffer_capacity
dirty_pair_high_water
periodic_time
explicit_flush
thread_exit
shutdown_drain
```

The timer emits nothing for a clean buffer. A checkpoint is written only after
a non-empty delta batch. Thus repeated hot hits consume a counter update but do
not create repeated raw records until a durability boundary is reached.
High-water/capacity flushes protect bounded memory when many genuinely new
pairs appear.

Lock ordering is always:

```text
buffer registry -> buffer local gate -> writer
```

Thread-buffer destruction, periodic draining and shutdown follow the same
order. Tests exercise concurrent recording/shutdown without deadlock or
use-after-free.

## Clean shutdown and footer guarantees

The explicit normal path is:

```text
window OnDestroy
  -> ShutdownEmulatorThreadFromUIThread
  -> Emulator::ShutdownIndirectTargetCollector
  -> Processor::ShutdownIndirectTargetCollector("window_close")
  -> active=false
  -> stop/join periodic flusher
  -> hold registry and drain every live buffer
  -> write final footer
  -> fflush + fclose
  -> existing std::quick_exit
```

The setup/shutdown mutex also protects an early UI close while the Processor is
being created. Shutdown is atomic and idempotent, so duplicate lifecycle calls
write exactly one footer. Setting `active=false` before acquiring buffer gates
closes the race with recorders: a recorder rechecks active after taking its
gate and cannot add data behind the final drain. Holding the registry through
file close prevents a thread-exit flush after the footer.

The schema-2 footer contains:

- run ID, raw schema and collector version;
- `shutdown_status=normal` and the external flush reason;
- batch/checkpoint sequence and checkpoint record count;
- final total hits and pair/delta record count;
- final unique pair/thread aggregate count and completeness flag;
- maximum per-thread final sequence;
- dropped-hit, I/O-error, overflow and aggregate-limit counters;
- explicit `delta_since_previous_persistence` semantics.

A write failure sets the collector failed state, reports the I/O error, counts
the affected batch as dropped and does not forge a clean footer. Collector
failure never changes guest CPU state.

## Raw schema 2 and compatibility

Committed raw schemas are:

```text
tools/schemas/xenia-indirect-targets-raw-v1.schema.json
tools/schemas/xenia-indirect-targets-raw-v2.schema.json
```

Schema 2 keeps append-safe JSONL records:

```text
header
module (zero or more, including refreshed post-update identity)
pair delta(s) for batch N
checkpoint committing batch N
...
footer
```

Every schema-2 pair says:

```json
"count_semantics": "delta_since_previous_persistence"
```

The header repeats that semantic and records buffer/dirty/timer/unique bounds.
A pair batch is not considered durable by the offline parser until its matching
consecutive checkpoint is read. Checkpoints reconcile batch record count,
cumulative total pair records and cumulative total hits. Footer batch,
checkpoint and collector-version fields are also reconciled.

Recovery behavior is deliberate:

| Tail state | Result |
| --- | --- |
| normal footer, counters reconcile, final newline present | `normal` |
| complete checkpointed tail, no footer | usable; `abnormal_or_unknown_no_footer` |
| complete uncheckpointed schema-2 pair batch | batch discarded with an integrity warning; prior checkpoints retained |
| partial final JSON object | prior checkpoints retained; `abnormal_truncated_tail` |
| complete normal footer without final newline | `invalid_normal_footer` |
| corrupt JSON in the middle | rejected |
| unsupported raw version | rejected with the supported version list |

Schema-1 traces remain readable with their legacy delta behavior. Schema-1
records are never silently reinterpreted as schema-2 committed batches. Old
compact summary files remain consumable because summary and plan schemas stay
at version 1.

Stable summary and plan content is deterministically sorted. JSON/CSV writes
use a same-directory temporary file, flush/fsync and atomic replace. Duplicate
run IDs and duplicate raw hashes are rejected. Image/module mismatches are
quarantined and do not contribute evidence.

## Summary-to-summary merging

Raw aggregation already supported multiple simultaneous raw inputs, and an
internal summary merger existed, but the old command was not a complete
preserved-evidence workflow. It accepted one input, exposed only generic
`--output`/`--csv` paths, did not reject duplicate canonical input paths and
did not revalidate each compact run against the current shared TU1 identity.
There was consequently no documented safe way to combine independently
post-processed captures after a raw trace had been deleted.

Tool version 1.3.0 provides the production interface:

```powershell
python .\tools\Fable2IndirectTargets.py merge `
    --summary .\out\indirect-targets\fable2-tu1-manual-001\review\xenia-indirect-targets.summary.json `
    --summary .\out\indirect-targets\fable2-tu1-manual-002\review\xenia-indirect-targets.summary.json `
    --output-directory .\out\indirect-targets\fable2-tu1-manual-001-002-merged
```

`--summary` must occur at least twice. `--output-directory` atomically writes
the conventional `xenia-indirect-targets.summary.json` and
`xenia-indirect-targets.summary.csv` names. The previous explicit `--output`
and optional `--csv` form remains available for compatibility. Neither form
opens, searches for or requires a referenced raw trace.

Before aggregation, the command validates summary schema and internal
accounting, then revalidates every run against
`tools/fable2-entrypoint-closure-evidence.json`. This includes patched image,
title/media/version, image base, executable coverage and the pinned loaded
module fingerprint. Accepted/quarantined counts, run counters, pair totals,
run hit counts and thread hit counts must reconcile. Duplicate canonical input
paths, run IDs, recorded raw hashes and aggregate keys fail before output is
written. Summary-level identity mismatch is rejected; already quarantined run
records remain quarantined and retain their reasons.

Summary schema 1 already models multiple runs correctly, so it remains at
version 1. Aggregate identity is unchanged: source module/address, target
module/address, branch kind and link state. `run_hit_counts`, `observed_runs`
and `(run_id, thread_key)` observations preserve per-run provenance. Sequence
numbers remain independent per-run, per-guest-thread domains; the merger never
takes a minimum or maximum across different runs. Run termination is likewise
per-run. `abnormal_or_truncated_runs=1` alongside two accepted runs means a
mixed collection, not that both runs are abnormal or both are clean.

The schema documentation was clarified without changing its version or
rewriting existing summaries. Legacy schema-1 summaries, including a null
`raw_schema_version` from tool 1.1.0, remain readable. Information absent from
an old compact summary is not invented: in particular, a recorded footer count
can prove presence, while a missing `flush_reason` cannot prove
`window_close`.

## Import planning and evidence integration

The planner continues to compare every non-return target with:

- the canonical manifest and exact generated registrations;
- `.pdata` and exception ownership;
- Phase 1 entrypoint closure;
- exact and related-build Ghidra records;
- Phase 3 jump-table dispatch/case ownership;
- known functions and callable internal entries;
- manual, runtime and fault-walker provenance;
- title executable, import, kernel and cross-module ranges.

Classifications remain:

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

For backward compatibility, `existing_manifest_function` means an existing
effective generated registration. That includes far more than the 80 explicit
canonical manifest overrides. Renaming it would break existing consumers and
is deferred; the plan evidence says whether the registration came from a
canonical override.

Runtime observation proves an executed entry address, not a function boundary
or size. Related-build Ghidra data cannot authorize an exact-TU1 edit by
itself. A `bctr`-only target remains guarded unless independent evidence
distinguishes a callable computed tail from a switch case. No code path creates
`RETURN_R3_ZERO`, a placeholder implementation or a fault-walker stub.

Dry-run is the default. Explicit apply still requires `--apply` plus reviewed
candidate IDs, validates the plan and manifest hashes, preserves comments and
line endings, writes atomically with a recovery backup, rejects overlap/stale
plans and is idempotent.

## Repaired mandatory fixtures

The real capture and shared evidence now verify these concepts separately:

| Target / range | Live Xenia evidence | Result |
| --- | --- | --- |
| `0x829647F0`-`0x82964800`, size `0x10` | `0x829641C4` `bctrl`, 2,849 hits | `existing_manifest_function`; no proposal/change |
| `0x82C03B28`-`0x82C03B44`, size `0x1C` | `0x821907A4` `bctrl`, 13 hits | `existing_manifest_function`; no proposal/change |
| `0x829675E0`-`0x829675F0`, size `0x10` | `0x82966EE4` `bctrl`, 3,257 hits | `existing_manifest_function`; no proposal/change |
| `0x82174734` | live `0x821746BC` `bctr`, 16,635 hits | `known_jump_table_case` owned by `0x821746A8`; no proposal/change |

For `0x82174734` the acceptance report now contains:

```text
expected_runtime_dispatch_sites:                  0x821746BC
observed_runtime_dispatch_sites:                  0x821746BC
expected_historical_corroborating_source_sites:   0x823DCAD8, 0x82403720
retained_historical_corroborating_source_sites:   0x823DCAD8, 0x82403720
owner:                                             0x821746A8
classification:                                    known_jump_table_case
manifest_change:                                   false
passed:                                            true
```

Controlled fixtures with a wrong runtime source, owner or classification fail.
Raising the case hit count to 10,000,000,000 still cannot produce a standalone
function proposal. Historical sites are retained but are no longer falsely
required to execute in every new capture.

The schema-2 fixture also proves two deltas merge to 4,294,967,307 hits, above
`UINT32_MAX`, with exact first/last sequences and no overflow.

## Preserved private capture evidence and real merge

The two accepted run summaries are under their original `review` directories.
Their embedded labels remain unchanged. User-confirmed coverage is recorded
separately:

```text
fable2-tu1-manual-001
  New game, childhood progression and creation of the first save.

fable2-tu1-manual-002
  Loading the manual-001 save, continuing gameplay, visiting shops and
  performing another save.
```

The approximately 95 GB manual-001 raw JSONL was intentionally deleted after
its compact evidence was preserved. This merge did not look for, open, copy,
reconstruct or rehash it. The manual-001 summary retains the recorded raw hash
`05E6344E2992089A9F7B7F509D8099D7E8851D130F2769BE9B9A8F72F20E03D0`;
this value was confirmed from the summary and was not recomputed.

Input summary identities are:

| Run | Summary bytes | Summary SHA-256 | Recorded raw SHA-256 |
| --- | ---: | --- | --- |
| manual-001 | 19,725,922 | `F943DA466653278DED408B3AD7CD462392E74E50FC9521BF4F75FE0F95543BA4` | `05E6344E2992089A9F7B7F509D8099D7E8851D130F2769BE9B9A8F72F20E03D0` |
| manual-002 | 16,906,107 | `09A7CA95CC804CCC088A793DE6131D680D6C05184F656F15DDA80F2CF4382B97` | `83DAA210412E6941AC0EE44D69EAED19C244FACC3D3637E93F4647132E67BD4D` |

Both runs revalidated against patched SHA-256
`BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00`,
title `0x4D5307F1`, media `0x716F0A0D`, version `0.0.1.26`, image base
`0x82000000`, executable coverage `0x82170000`-`0x832D0000` and loaded
fingerprint `341151E9932EC14CB4F520AA9DE35BCF7169BFE1`.

Termination remains per-run:

| Run | Collector / raw schema | Status | Footer count | Errors |
| --- | --- | --- | ---: | --- |
| manual-001 | collector 1; preserved `raw_schema_version=null` from tool 1.1.0 | `abnormal_or_unknown_no_footer` | 0 | no corrupt tail, missing newline, integrity warning, drop, I/O error or overflow |
| manual-002 | collector 2; raw schema 2 | `normal` | 1 | no corrupt tail, missing newline, integrity warning, drop, I/O error, overflow or aggregate-limit failure |

The manual-002 summary proves exactly one accepted clean footer. Summary schema
1 does not retain the footer reason, so the expected `window_close` reason
cannot be independently verified without the raw file and is not claimed here.
Manual-001 is not relabelled as clean.

The real merged artifacts are:

```text
C:\Dev\Fable2Recomp\out\indirect-targets\fable2-tu1-manual-001-002-merged\xenia-indirect-targets.summary.json
C:\Dev\Fable2Recomp\out\indirect-targets\fable2-tu1-manual-001-002-merged\xenia-indirect-targets.summary.csv
C:\Dev\Fable2Recomp\out\indirect-targets\fable2-tu1-manual-001-002-merged\fable2-indirect-targets.import-plan.json
```

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| merged summary JSON | 27,377,874 | `AE4670BAFDF6FC8AB719F81CCE14C5BD63FDD4EAA8262D0CDAB79B0E39F83A29` |
| merged summary CSV | 5,534,648 | `39D4600C006C84465612D70043E84B09DA8DE0075389AEFBBF28D8803CBC3D82` |
| merged dry-run plan | 58,501,469 | `82C262178A386CB4F519B9CF72D71C946948EB6AF06454349E060C41830AB6F6` |

Aggregate-key and target coverage are deliberately reported separately:

| Metric | Count |
| --- | ---: |
| input aggregate records | 49,746 |
| merged unique aggregate keys | 27,785 |
| aggregate keys only in manual-001 / only in manual-002 / in both | 4,671 / 1,153 / 21,961 |
| manual-001 / manual-002 / combined hits | 24,555,201,598 / 19,275,373,582 / 43,830,575,180 |
| non-return targets in manual-001 / manual-002 / merged | 15,576 / 14,050 / 16,143 |
| targets only in manual-001 / only in manual-002 / in both | 2,093 / 567 / 13,483 |

Manual-002 added 567 targets to combined coverage: 411 existing effective
registrations, 42 existing-function internal entries and 114 known jump-table
cases. It introduced no proposal and changed no classification for a target
already present in manual-001.

The merged dry-run classifications are:

| Classification | Targets |
| --- | ---: |
| existing effective registrations (`existing_manifest_function`) | 13,087 |
| existing function internal entries | 1,486 |
| known jump-table cases | 1,561 |
| known import/kernel targets | 9 |
| invalid/non-executable | 0 |
| ambiguous / conflicting | 0 / 0 |
| total non-return targets | 16,143 |
| range proposals / automatically applicable | 0 / 0 |

Known-positive merged observations remain no-ops:

| Target | manual-001 | manual-002 | Combined | Result |
| --- | --- | --- | ---: | --- |
| `0x829647F0`, size `0x10` | `0x829641C4` `bctrl`, 2,849 | `0x829641C4` `bctrl`, 1,903 | 4,752 | `existing_manifest_function`; no proposal |
| `0x82C03B28`, size `0x1C` | `0x821907A4` `bctrl`, 13 | `0x821907A4` `bctrl`, 4 | 17 | `existing_manifest_function`; no proposal |
| `0x829675E0`, size `0x10` | `0x82966EE4` `bctrl`, 3,257 | `0x82966EE4` `bctrl`, 2,358 | 5,615 | `existing_manifest_function`; no proposal |
| `0x82174734` | `0x821746BC` `bctr`, 16,635 | `0x821746BC` `bctr`, 85,787 | 102,422 | `known_jump_table_case`, owner `0x821746A8`; no proposal |

The jump-table plan also retains historical corroboration at `0x823DCAD8` and
`0x82403720`; neither address is falsely required to execute in both captures.
Every acceptance fixture passed and `canonical_manifest_modified=false`.

## Deferred static-ownership follow-up

`ownership-follow-up` turns the real compact summaries and merged dry-run plan
into a deterministic review queue without opening either raw trace:

```powershell
python .\tools\Fable2IndirectTargets.py ownership-follow-up `
    --baseline-summary .\out\indirect-targets\fable2-tu1-manual-001\review\xenia-indirect-targets.summary.json `
    --contributing-summary .\out\indirect-targets\fable2-tu1-manual-002\review\xenia-indirect-targets.summary.json `
    --merged-summary .\out\indirect-targets\fable2-tu1-manual-001-002-merged\xenia-indirect-targets.summary.json `
    --plan .\out\indirect-targets\fable2-tu1-manual-001-002-merged\fable2-indirect-targets.import-plan.json `
    --output-directory .\out\indirect-targets\fable2-tu1-manual-001-002-merged `
    --expect-targets 567 `
    --expect-existing-registrations 411 `
    --expect-internal-entries 42 `
    --expect-jump-table-cases 114
```

The authoritative JSON follows
`tools/schemas/fable2-phase4-static-ownership-follow-up-v1.schema.json`.
It records exact input hashes, identity, per-run termination provenance,
priority, target, source/kind/hits, current owner and range, effective
registration or jump-table provenance, conflicts, static corroboration and the
reason no manifest proposal exists. CSV is an address-review view and Markdown
is a concise handoff. All three omit generation timestamps and use canonical
sorting, so regeneration from identical compact inputs is byte-identical.

Run metadata is normalized once for validation and report generation. Missing
legacy fields remain missing evidence rather than guessed facts:

- manual-001 has collector schema 1, `raw_schema_version=null` with status
  `unavailable_in_legacy_summary`, no footer and
  `abnormal_or_unknown_no_footer`;
- manual-002 has collector schema 2 and explicit `raw_schema_version=2`, with
  one normal footer;
- neither compact summary records `flush_reason`, so both queue records use
  `flush_reason=null` with status `unavailable_in_compact_summary`;
- in particular, the queue does not invent `window_close` for manual-001 or
  infer a raw schema from its collector version.

The closeout outputs are:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `phase4-static-ownership-follow-up.json` | 1,197,339 | `9DF543E67C4E0EE121BDAD9142E57138C3D5823B2FE72D25E02B17CB19C2C987` |
| `phase4-static-ownership-follow-up.csv` | 217,426 | `DFCABBF4E36DF9ED3E962E946011A1C9E2489C0C2F9A9542D2C7DA062BC414EE` |
| `phase4-static-ownership-follow-up.md` | 75,498 | `713A73C703B847504AC79BC214F13B2CE8321FBC2EEA1D652D36E30E3E70A016` |

The JSON report ID is `P4OWN-64AD322EA200BCB401C0`. Its exact split is:

| Priority | Classification | Targets | Required future review |
| --- | --- | ---: | --- |
| 1 | existing function internal entry | 42 | Distinguish ordinary basic blocks, callable mid-function entries, exception landings, incorrect boundaries and unresolved cases. |
| 2 | known jump-table case | 114 | Confirm owner, dispatch/table identity, recovered target set, CFG ownership and manual-annotation equivalence. |
| 3 | existing effective registration | 411 | Treat as runtime corroboration unless static ownership or registration provenance disagrees. |

Every item is present in manual-002 and absent from manual-001. The report has
zero range proposals, zero manifest proposals and zero automatically applicable
items. It cannot split/promote a function, turn a switch case into a function,
apply a manifest edit or generate a placeholder implementation. Regeneration
left `fable2_manifest.toml` at SHA-256
`E3EB39CA153E396D5DC53E6F943ED8FF7AF1D6B0704EB860836BD7D21A3F87B0`.

The JSON, CSV and Markdown are stored beside the merged compact evidence in the
ignored output tree, copied into the Phase 4 local archive and included in the
allowlisted merged evidence ZIP. They are intentionally not added as bulk data
to normal Git history.

## Automated validation

Commands used for this repair include:

```powershell
# Fable parser/schema/planner tests
python -m unittest tests.test_fable2_indirect_targets
python -m unittest tests.test_fable2_indirect_targets tests.test_fable2_function_map
python -m unittest discover -s tests -p "test_*.py"
python -m compileall -q tools tests

# Existing compact summary -> repaired dry-run plan
python .\tools\Fable2IndirectTargets.py plan `
    --summary .\out\indirect-targets\fable2-tu1-manual-001\review\xenia-indirect-targets.summary.json `
    --output .\out\indirect-targets\phase4-repair-validation\fable2-indirect-targets.import-plan.json

# Xenia style/build/tests, from its checkout
python .\xenia-build.py lint
python .\xenia-build.py build --config=release --build-tests
.\build\bin\Windows\Release\xenia-cpu-tests.exe '[collector]'
.\build\bin\Windows\Release\xenia-cpu-tests.exe
.\build\bin\Windows\Release\xenia-base-tests.exe
.\build\bin\Windows\Release\xenia-kernel-tests.exe
.\build\bin\Windows\Release\xenia-vfs-tests.exe
```

Exact results:

| Validation | Result |
| --- | --- |
| Phase 4 Python module | 21/21 PASS in 0.269 s |
| Phase 4 + function-map focused set | 31/31 PASS in 0.341 s |
| full repository Python suite | 49/49 PASS in 2.818 s (final rerun) |
| Python compileall | PASS |
| direct GPU provenance verifier | PASS; 0 warnings |
| schema-1 and schema-2 committed raw fixtures | PASS |
| real compact-summary dry-run plan | 15,576 targets; 0 proposals; 0 applicable; manifest false |
| `fable2-build` | PASS; codegen 0 written; Release linked; 105,042,944 bytes; SHA-256 `18F926D96930B1CC2470F63FA59421FE34BA8A081F7C6BD58EF49CFF13E7E6F4` |
| Xenia clang-format lint | PASS |
| Xenia Release configure/build with tests | PASS |
| Xenia collector + hidden benchmark filter | 20,327 assertions / 13 cases PASS |
| Xenia full CPU suite | 21,032 assertions / 258 cases PASS |
| Xenia base | 3,561 assertions / 75 cases PASS |
| Xenia kernel | 267 assertions / 5 cases PASS |
| Xenia VFS | 1 assertion / 1 case PASS |
| PowerShell parser / full help | 0 syntax errors; help loaded PASS |
| real-input `phase4-repair-preflight-20260902` | PASS without launch; ISO final; schema 2; expected hashes/TU/content/storage verified |

The collector tests cover actual synthetic `bctr`, `bctrl` and linked
non-standard `bclr` PPC execution, ordinary-return exclusion/inclusion,
disabled output, exact aggregation, capacity flush, periodic dirty-only
checkpoints, explicit/idempotent shutdown, pending live buffers, concurrent
recording/shutdown, injected I/O failure, count saturation and a 2.02-million
event stress run.

No manual game session was launched or claimed during the repair.

The later preserved-summary merge validation used:

```powershell
python -m unittest tests.test_fable2_indirect_targets
python -m unittest tests.test_fable2_indirect_targets tests.test_fable2_function_map
python -m unittest discover -s tests -p "test_*.py"
python -m compileall -q tools tests
python .\tools\Fable2IndirectTargets.py --help
python .\tools\Fable2IndirectTargets.py merge --help

python .\tools\Fable2IndirectTargets.py merge `
    --summary .\out\indirect-targets\fable2-tu1-manual-001\review\xenia-indirect-targets.summary.json `
    --summary .\out\indirect-targets\fable2-tu1-manual-002\review\xenia-indirect-targets.summary.json `
    --output-directory .\out\indirect-targets\fable2-tu1-manual-001-002-merged

python .\tools\Fable2IndirectTargets.py plan `
    --summary .\out\indirect-targets\fable2-tu1-manual-001-002-merged\xenia-indirect-targets.summary.json `
    --output .\out\indirect-targets\fable2-tu1-manual-001-002-merged\fable2-indirect-targets.import-plan.json
```

Focused tests cover compatible and run-unique aggregates, counts above
`UINT32_MAX`, run-qualified sequences, mixed termination, duplicate path/run/
raw-hash rejection, canonical image/fingerprint/range rejection, input-order
determinism, idempotent atomic JSON/CSV replacement, legacy summary reading,
merged planning, manifest non-mutation and the no-stub invariant. The real
merge and plan results are recorded above. Xenia was not launched.

Final results for this summary-merge change were 25/25 Phase 4 tests in 0.406
seconds, 35/35 Phase 4 plus function-map tests in 0.405 seconds and 53/53 full
repository Python tests in 2.887 seconds. Python `compileall`, top-level help
and merge help also passed.

## Performance and output-size projection

### Collector hot path

The isolated benchmark executes seven paired samples of 200,000 resolved PPC
transfers through the real x64 JIT.

| Metric | Result |
| --- | ---: |
| disabled ns/transfer, min / median / max / mean / population SD | 21.896 / 22.196 / 25.744 / 22.958 / 1.311 |
| enabled ns/transfer, min / median / max / mean / population SD | 31.839 / 33.312 / 33.955 / 33.095 / 0.781 |
| enabled/disabled median ratio | 1.500788 |
| final flush median / max | 0.0178 / 0.0255 ms |
| one repeated-pair raw file after 200,000 transfers | 2,509 bytes |
| 10,000 unique events | 766,066.326 events/s; 4,273,708 raw bytes |
| four-thread repeated-pair lane | 1,000,000 events at 128,748,181.432 events/s |

The 50.1% enabled ratio is a synthetic worst-shaped microbenchmark in which
nearly all useful work is an indirect transfer and collector callback.
Disabled collection still removes the callback, buffer and file entirely.
This is not a gameplay frame-time claim. No gameplay-overhead timing was
retained with manual-002, and it cannot be derived from the compact summary.

### High-volume stress

The deterministic stress test uses four guest threads, 5,000 unique pairs plus
500,000 repeated hot hits per thread, mixed `bctr`/`bctrl`/`bclr` and
cross-module/unknown targets.

| Metric | Result |
| --- | ---: |
| events | 2,020,000 |
| unique pair/thread aggregates | 20,004 |
| wall time | 0.027464 s |
| throughput | 73,550,830.178 events/s |
| raw bytes | 8,450,646 |
| raw bytes per unique pair/thread | 422.448 |
| pair/delta records | 20,004 |
| checkpoints | 8 |
| guest threads | 4 |
| production buffer bytes/thread | 196,680 |
| bounded four-buffer bytes | 786,720 |
| drops / I/O errors / count overflows | 0 / 0 / 0 |
| footer | exactly one, final newline present |

The test verifies exact hit totals, exact hot-pair first/last sequence
`5001`/`505000` and footer reconciliation. An abnormal/footerless form remains
recoverable through its last checkpoint.

### Offline summary

The actual 8,450,646-byte collector stress output was parsed, aggregated and
written twice:

| Iteration | Parse | Aggregate | JSON+CSV write |
| --- | ---: | ---: | ---: |
| 1 | 0.805986 s | 1.092709 s | 0.987260 s |
| 2 | 0.849592 s | 1.192367 s | 0.952874 s |

Both 13,870,596-byte JSON summaries and both 2,914,067-byte CSV summaries were
byte-identical. Python `tracemalloc` peak was 105,056,358 bytes. The summary
retained all 2,020,000 hits and 20,004 pairs.

Planning the real 15,576-target compact summary took about 7.9 seconds in the
recorded validation command and produced the repaired plan above.

### Preserved-summary merge performance

The manual-001/manual-002 merge excludes the deleted 95 GB raw trace. A normal
unprofiled in-memory measurement separated the compact workflow as follows:

| Stage | Time |
| --- | ---: |
| load and canonical validation of both summaries | 0.503788 s |
| merge and reconciliation | 0.945327 s |
| deterministic JSON generation | 0.134434 s |
| deterministic CSV generation | 0.082207 s |
| total in-memory work | 1.665756 s |

The complete atomic CLI took 1.960820 seconds. Repeating it with reversed input
order took 1.922074 seconds and produced byte-identical JSON and CSV. The
merged dry-run plan took 5.288126 seconds.

An allocation-instrumented `tracemalloc` pass reported a 219,170,061-byte peak.
Instrumentation increased the same in-memory workflow to 44.560792 seconds, so
its timing is not comparable to the unprofiled result; it is retained only as
a Python allocation-peak measurement.

### Conservative old-capture projection

The old compact summary contains 31,448 distinct pair/thread observations and
39 guest-thread keys. Its run duration was approximately 46 minutes 14 seconds.
A deliberately conservative model assumes every one of those pair/thread
aggregates becomes dirty in every one of ten five-minute durability windows
and uses the measured 422.448 bytes per stress record:

```text
31,448 aggregates * 10 windows = 314,480 pair records
314,480 * 422.448 bytes       = 132,851,448 bytes
                              = about 126.7 MiB
```

Compared with about 90.9 GiB, that model is roughly a 735x reduction and
comfortably below 1 GiB. It is not an exact full-game prediction: thread
lifetime, genuinely new pairs, high-water flushes, module records and JSON
field lengths vary. It nevertheless uses the real run's pair/thread
cardinality and duration and exceeds the required 100x amplification reduction
without discarding evidence. Timer-only checkpoints would be bounded near
dirty live threads per interval rather than the old 6,142,998 checkpoints.

## Future user gameplay workflow

Use a new run ID. Do not reuse or overwrite `fable2-tu1-manual-001` or
`fable2-tu1-manual-002`.

### Preflight only

```powershell
Set-Location C:\Dev\Fable2Recomp

.\tools\Invoke-Fable2XeniaIndirectTrace.ps1 `
    -Action Preflight `
    -RunId fable2-tu1-manual-003 `
    -Label 'Fable II GOTY TU1 additional manual gameplay coverage' `
    -GamePath 'D:\Fable2-Recomp\disc\Fable II - Game of the Year Edition.iso' `
    -AnalysisImagePath 'D:\Fable2-Recomp\tu1\default.xex' `
    -ContentRoot 'C:\Dev\Fable2Phase4Xenia\content' `
    -StorageRoot 'C:\Dev\Fable2Phase4Xenia\storage'
```

Preflight must print and verify:

- complete launch-media path/type, with the ISO not hashed as the analysis image;
- analysis base XEX, adjacent XEXP and expected patched SHA-256;
- content root and exact installed TU directory;
- storage/output writability;
- title `0x4D5307F1`, media `0x716F0A0D` and version `0.0.1.26`;
- raw schema 2 and the 4,096 / 3,072 / 300,000 ms / 1,000,000 persistence
  settings;
- the GOTY ISO as the final quoted argument.

### Launch

```powershell
.\tools\Invoke-Fable2XeniaIndirectTrace.ps1 `
    -Action Launch `
    -RunId fable2-tu1-manual-003 `
    -Label 'Fable II GOTY TU1 additional manual gameplay coverage' `
    -GamePath 'D:\Fable2-Recomp\disc\Fable II - Game of the Year Edition.iso' `
    -AnalysisImagePath 'D:\Fable2-Recomp\tu1\default.xex' `
    -ContentRoot 'C:\Dev\Fable2Phase4Xenia\content' `
    -StorageRoot 'C:\Dev\Fable2Phase4Xenia\storage'
```

The emitted argument tail must be:

```text
--indirect_target_trace_buffer_pairs=4096
--indirect_target_trace_dirty_pairs=3072
--indirect_target_trace_flush_interval_ms=300000
--indirect_target_trace_max_unique_aggregates=1000000
--content_root=C:\Dev\Fable2Phase4Xenia\content
--apply_title_update=true
--storage_root=C:\Dev\Fable2Phase4Xenia\storage
--log_file=...
D:\Fable2-Recomp\disc\Fable II - Game of the Year Edition.iso
```

The ISO must remain the final positional argument.

Useful manual coverage is boot/title flow, save load, Bowerstone Market and
region transitions, dialogue/crowd AI, shops/inventory/equipment, melee/ranged/
Will combat, quests/scripted scenes/cutscenes and a user-selected safe
save/reload. This is a subsystem checklist, not control or menu automation.

Close Xenia through the ordinary window-close path.

### Confirm the footer before PostRun

```powershell
$rawPath = 'C:\Dev\Fable2Recomp\out\indirect-targets\fable2-tu1-manual-003\xenia-indirect-targets.raw.jsonl'
$footer = Get-Content -LiteralPath $rawPath -Tail 1 | ConvertFrom-Json

$footer | Select-Object `
    record, run_id, raw_schema_version, collector_version, `
    shutdown_status, flush_reason, total_hits, total_pair_records, `
    checkpoint_records, final_unique_aggregates, `
    unique_aggregate_count_complete, dropped_hits, io_errors, `
    count_overflows, aggregate_limit_exceeded
```

Expected values include `record=footer`, `run_id=fable2-tu1-manual-003`,
`raw_schema_version=2`, `collector_version=2`,
`shutdown_status=normal` and `flush_reason=window_close`. The file must end in
a newline. If the footer is absent, preserve the raw file and Xenia log; do not
invent or patch a footer. PostRun will keep usable checkpointed data clearly
marked incomplete.

### PostRun

```powershell
.\tools\Invoke-Fable2XeniaIndirectTrace.ps1 `
    -Action PostRun `
    -RunId fable2-tu1-manual-003
```

PostRun summarizes, validates identity and emits a dry-run plan. It never
applies a manifest change.

### Safe-before-delete checklist

Do not delete a future raw trace merely because PostRun created a JSON file.
First verify all of the following:

1. PostRun exits zero.
2. The summary run has `flush_status=normal`, no integrity warnings,
   `corrupt_tail=false` and `missing_final_newline=false`.
3. `accepted_runs=1`, `quarantined_runs=0` and
   `module_fingerprint_match=true`.
4. Dropped hits, I/O errors, count overflows and aggregate-limit errors are
   acceptable (normally zero), and `unique_aggregate_count_complete=true`.
5. Summary JSON, summary CSV and import plan all exist and can be reopened.
6. The summary records the raw trace SHA-256 and exact run ID.
7. The import plan says `canonical_manifest_modified=false` and has been
   reviewed.
8. Hash/copy the compact review artifacts to the user's chosen backup location
   if the raw evidence will not be retained.

Only after those checks should the user decide whether the exact raw file can
be removed. This repair does not delete it automatically.

## Troubleshooting

- Summary merge asks for at least two inputs: repeat `--summary`; do not pass a
  deleted raw JSONL path. The command consumes compact summary JSON only.
- Duplicate input path, run ID or recorded raw SHA-256: stop and identify the
  duplicated evidence. A missing underlying raw file does not weaken this
  guard because the preserved hash is authoritative for duplicate detection.
- Canonical identity rejection: inspect the summary's patched hash,
  title/media/version, selected title-module range and loaded fingerprint. Do
  not edit the compact artifact to force acceptance.
- A schema-1 summary may preserve `raw_schema_version=null`; this is compatible
  legacy metadata, not evidence that the raw file is required. Unsupported
  non-null versions are rejected.
- A normal run with one footer but no retained footer reason may be described
  as clean, but its reason must remain unknown. Do not infer `window_close`.
- Missing footer with complete newline/checkpoints: treat as
  `abnormal_or_unknown_no_footer`, retain the Xenia log and check whether the
  build identifies itself as `6b6715b02`. An older build still has the
  `quick_exit` lifecycle defect.
- Missing final newline or partial final object: preserve the file. The parser
  will retain only complete checkpointed batches and mark the tail abnormal.
- Millions of checkpoints: inspect the header. Schema 2 must report the
  five-minute timer and delta semantics; a schema-1/collector-1 binary still
  uses the obsolete hit policy.
- `aggregate_limit_exceeded > 0`: pair evidence is still retained, but the
  footer unique count is a lower bound; do not call the footer aggregate count
  complete.
- Identity quarantine: never replace the patched image SHA-256 with an ISO
  hash. Verify title-update application, title/media/version, module range and
  loaded-module fingerprint.
- Loose XEX rejection: use the GOTY ISO for gameplay and reserve
  `-AnalysisImagePath` for identity preflight only.

## Remaining limitations and boundary

- Manual-002 is a real post-repair private-TU1 capture and its summary proves
  one clean footer. The schema-1 summary did not retain the footer reason, so
  `window_close` cannot be revalidated from compact evidence alone.
- No real-game collector-overhead sample was retained; performance numbers in
  this document remain synthetic or offline-tool measurements.
- The old accepted capture is evidence from real gameplay but used collector
  schema 1 and cannot validate schema-2 volume or footer behavior.
- The current real evidence has no proposed, ambiguous or conflicting target,
  so explicit apply remains verified only on temporary manifests.
- Phase 3 still contains 711 unresolved relevant non-link CTR sites. Runtime
  collection should prioritize useful gameplay systems rather than assuming
  those sites are functions.
- The classification name `existing_manifest_function` is broader than the 80
  explicit manifest overrides; changing it is deferred for compatibility.
- Run 047's black dog and black player skin/head remain a separate
  GPU/skinned-material or texture issue. Saving in that run remains untested,
  not failed.

Phase 4 closeout preserves the merged compact artifacts and the deterministic
567-target queue. Static ownership review is deferred backlog, not discarded
work and not a prerequisite for beginning native save-write parity. Another
capture is optional and should use manual-003 or another unique run ID; it is
not required for ownership analysis or Phase 4 completion.

## Commit and publication policy

Local repair commits:

```text
Xenia Canary     6b6715b029d442ff6ed5a89773f119400b1c19b5
Fable2Recomp     9c46998a993ea2046b1e9a873d7d9521eb2f44ad
documentation    commit containing this file
summary merge    commit containing tool version 1.3.0
```

The ReXGlue SDK was not modified by this repair, and its expected local
`thirdparty/libmspack` state was preserved.

The earlier implementation and repair commits were local when their validation
sections were written. The authorized closeout publishes the full feature
history, an explicit `main` merge boundary, the separate Xenia collector branch
and an allowlisted compact-evidence release. Publication details and archive
identities are recorded in `06-phase4-closeout.md` and the archive manifest.
No private XEX, ISO, XEXP, STFS package, save, memory dump, raw gameplay trace,
content/storage/cache state, credential or compiled binary belongs in a commit
or evidence asset.
