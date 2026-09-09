# Forward-only coverage sessions

Use one versioned JSON manifest per process session. Copy
`session-template.json`, assign a unique identifier, and validate its structure
against `tools/schemas/fable2-coverage-session-v1.schema.json`. The manifest
records evidence; it neither launches a runtime nor applies an import.

## Evidence contract

- `status` is `prepared`, `awaiting_analysis`, `analysed`, or `blocked`.
  Prepared sessions have no claimed runtime outcome or exercised categories.
- `runtime` identifies the reference collector, reference without collection,
  normal native runtime, or native diagnostics. Record exact repository,
  executable and configuration identities separately. A source commit alone
  does not establish a binary identity.
- `starting_checkpoint` records descriptive metadata and explicit source,
  preserved copy and writable roots. Do not commit payloads. Never launch
  against a backup or preserved checkpoint. Copy rather than move.
- `user_coverage` contains **only user-confirmed** areas/categories. Preserve
  the session-associated user report verbatim in `confirmation`. Empty arrays
  mean unconfirmed, not failed or unexercised. Planned categories belong in the
  run card, not this field.
- `timing` separates process lifetime from the gameplay sampling window.
  Use null without reliable evidence. Collector sequences are per-thread
  counters, not timestamps or frame counts.
  The native tranche-001 launch card returned before the GUI application's
  first log entry: its recorded `process_end_utc` is not a process-exit time
  and `exit_code` is null. Preserve the original invocation record, annotate
  those fields as unusable, and use the identified runtime log for lifecycle
  evidence. A future launcher must wait on an actual process handle before
  claiming process duration or exit status; `$LASTEXITCODE` alone is not proof.
- `shutdown` separates user-reported clean exit from validated raw footer
  evidence. Require exactly one normal schema-2 footer, matching run/build,
  complete checkpoint accounting, newline termination and zero loss/error
  counters before claiming a complete clean collector session. Record the
  actual `flush_reason`; do not infer it from a compact summary that omits it.
- `artifacts` records local paths, byte sizes, SHA-256 and roles. Preserve raw
  reference JSONL locally; commit only metadata and concise reviewed evidence.
  Check all hashes again after the process exits, since launch-time files may
  change. Keep pre-run configuration as a separate immutable artifact.
- `target_review` distinguishes repeat targets, new targets, new source/target
  pairs and missing functions. Unknown counts are null. Runtime observation
  proves execution as a target, not an independent callable boundary.
- `outcome` keeps invalid targets, fatal/guest exceptions, hangs, transitions,
  interactions, rendering-only defects, performance and save/exit distinct.
  Record exact guest addresses, owners, LR and log references when available.
- `performance_observations` accepts partial user reports. Identify subjective
  FPS/latency reports and measurement sources. Do not manufacture averages or
  distributions. Log correlation may support, but does not alone prove, a
  compilation, asset, renderer, synchronization or leak explanation.
- `handoff` records the end-save source, preserved endpoint, native destination
  and next session. No native root becomes writable until the exact destination
  and launch command have been supplied to the user.

## Supported processing sequence

From `C:\Dev\Fable2Recomp`, use the existing wrapper with explicit isolated
`-ContentRoot` and `-StorageRoot` for `Preflight` and `Launch`. It takes complete
game media as the final positional argument; the analysis XEX/XEXP is separate.
Use a new `-RunId` for every process, including a later reload if it requires
relaunch. Finish normal saving before closing the Xenia window; allow the
launch command to return. Do not terminate the process to obtain a clean exit.

After the user reports completion:

```powershell
.\tools\Invoke-Fable2XeniaIndirectTrace.ps1 -Action PostRun -RunId phase5a-reference-001

python tools/Fable2IndirectTargets.py merge `
    --summary out/indirect-targets/fable2-tu1-manual-001-002-merged/xenia-indirect-targets.summary.json `
    --summary out/indirect-targets/phase5a-reference-001/review/xenia-indirect-targets.summary.json `
    --output-directory out/phase5a/tranche-001/merged

python tools/Fable2IndirectTargets.py plan `
    --summary out/phase5a/tranche-001/merged/xenia-indirect-targets.summary.json `
    --ghidra-map out/analysis/BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00/ghidra-function-map.json `
    --output out/phase5a/tranche-001/merged/fable2-indirect-targets.import-plan.json

python tools/Fable2IndirectTargets.py ownership-follow-up `
    --baseline-summary out/indirect-targets/fable2-tu1-manual-001-002-merged/xenia-indirect-targets.summary.json `
    --contributing-summary out/indirect-targets/phase5a-reference-001/review/xenia-indirect-targets.summary.json `
    --merged-summary out/phase5a/tranche-001/merged/xenia-indirect-targets.summary.json `
    --plan out/phase5a/tranche-001/merged/fable2-indirect-targets.import-plan.json `
    --output-directory out/phase5a/tranche-001/review
```

`PostRun` summarizes/validates one raw session and creates a dry-run plan;
cross-session merging is the separate supported command above. Repeat
PostRun, merge and planning into separate review locations (and reverse merge
input order) to compare deterministic artifact bytes. Retain command exit
codes and output hashes. Never merge an accepted summary together with one of
its already-included constituent runs.

Inspect all new targets with the existing planner and exact-image evidence.
For an accepted baseline containing multiple sessions, `ownership-follow-up`
uses schema v2 (`baseline_run_ids`, `absent_from_baseline_runs`); every baseline
run and raw hash must be present in the merged plan. A target seen in any
baseline run is known. Single-baseline-run reports retain schema v1 and its
existing serialization. The contributor remains exactly one new run.

A preliminary gap-fill enclosing extent is not an exact function body. The
planner now requires recovered basic-block membership before calling a target
internal to such an extent. Outside that body, the ordinary independent static
boundary rules still apply; absence of a body alone cannot authorize a size or
an import. Phase 5A target `0x825E28B0` exposed this distinction.

The Phase 4 `ownership-follow-up` reporter deliberately accepts only its
supported already-owned categories. If a new function proposal or conflict
falls outside those categories, preserve that explicit rejection and review
the full plan directly; do not weaken the reporter or discard the target.
Use TU1 bytes/control flow, pdata, exact Ghidra ranges, registration/owner
ranges, manual/automatic tables and source link semantics. Conditional return
continuations and switch blocks stay internal. Apply only individually proven
missing callable boundaries through the existing reviewed importer. Its
default remains dry-run; use explicit reviewed selection and `--apply` only
after the evidence review. This phase authorizes justified local application.

After accepted changes, run canonical disassembler/codegen where required,
all relevant tests, SDK CTest when relied upon, and `fable2-build`. Without
manifest/codegen changes, the normal build's dependency check is sufficient;
do not force regeneration. Preserve manual tables and setjmp/longjmp behaviour.

## Save handoff and native endpoint

After fully processing the reference evidence, preserve a copy of its closed
end-of-session content root under `out/phase5a/checkpoints/end-001/`. Record
payload inventories/hashes locally. Create a new native root under
`out/phase5a/sessions/phase5a-native-001/user-data/`; retain the established
native profile/container metadata from a copy of the accepted native working
root, then copy the reference Hero000 payload set into its native Hero000
container. Check the exact path sets and hashes; never leave stale extra
payload files silently. Existing interoperability is accepted, not a new save
research task. Never modify either runtime's original working save or backups.

Supply the exact native command with explicit `--user_data_root`, normal
Release executable, game/update roots, GPU plugin and numbered log. The
current `fable2-run` has no root parameter, so this required isolated-root
launch uses its documented argument pattern and `Get-Fable2NextRunNumber`
without altering the global helper. Request only load, control/basic
interaction, an optional nearby transition, save and orderly exit. Preserve
the resulting native endpoint for the next tranche. Do not prepare a writable
native session automatically from an unprocessed or unvalidated reference run.

Earlier events are **reference-covered and statically/build validated but not
immediately replay-validated in the recompilation**. The short native endpoint
smoke test is deliberately narrower. If it fails, localize that exact failure;
fault walking is a diagnostic fallback only when justified. Request a narrow
event replay only when it supplies missing discriminating evidence.

## Performance observations

For any useful symptom accept the available subset of: approximate session
time, runtime/build, location/activity, symptom/duration, one-off/periodic/
constant, first-use/repeatable, audio and input responsiveness, recovery, FPS
before/during and notes. Correlate approximate times with logs and preserve
uncertainty. Distinguish first-use hitches, persistent hitches, visuals-only
freezes, wider blocking and gradual degradation only where evidence permits.

No full-section replay or paired performance run is mandatory. Without a
controlled same-scene collector-off/on measurement, gameplay collector overhead
is unknown. Synthetic JIT transfer costs are not gameplay FPS. The historical
4–5 FPS instrumentation observation is not normal-build performance.
