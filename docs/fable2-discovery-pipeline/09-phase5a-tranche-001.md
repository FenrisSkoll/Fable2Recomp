# Phase 5A tranche 001: Market to Oakfield

## Status and scope

2026-09-09: reference processing, conservative review, one justified thunk
import, regeneration, normal build and isolated save handoff are complete.
**Phase 5A tranche 001 is complete.** The user confirmed the transferred
Oakfield endpoint loaded, control/basic interaction and saving worked, and
normal exit succeeded, with no additional problem noticed. The identified
native log supports startup and the normal shutdown path. Gameplay success
is user-observed, not inferred from compilation or log duration.

The authoritative reference boundaries are **Bowerstone Market → Oakfield
tavern**. Childhood was already completed. The starting fountain wait of
approximately five minutes was expected game behaviour; no hang or progression
blocker was reported. The user performed all gameplay and chose the route.

Earlier events were **reference-covered and statically/build validated but
not immediately replay-validated in the native recompilation**. The agreed
forward-only strategy requires only a short endpoint test. This is neither
end-to-end native parity nor a whole-game completion claim.

Durable evidence:

- [Reference session manifest and verbatim user coverage report](coverage/phase5a-reference-001.json).
- [All 479 new target dispositions](coverage/phase5a-reference-001-targets.csv).
- [155 rejected promotions: ownership ledger](coverage/phase5a-reference-001-ownership/ownership-ledger.json),
  [readable table](coverage/phase5a-reference-001-ownership/ownership-ledger.md),
  [annotation-only reviewed companion](coverage/phase5a-reference-001-ownership/ownership-reviewed-import-plan.json).
- [Individually reviewed thunk](coverage/phase5a-825E28B0-review.json).
- [Completed native endpoint session](coverage/phase5a-native-001.json).
- [Reusable workflow and session contract](coverage/README.md) and
  [baseline reconstruction/preparation](08-phase5a-runtime-coverage.md).

## User-confirmed coverage matrix

Only the user's completed-session report supplies this matrix. The Market
start and Oakfield tavern endpoint supersede any earlier checkpoint assumption.

| Category | Confirmed exercise in `phase5a-reference-001` |
| --- | --- |
| Adult regions and transitions | Bowerstone Market; Bowerstone Old Town; cellar; Rookridge; Hobbe Cave; Rookridge to Oakfield; Oakfield tavern endpoint |
| Scripted scenes | Relevant cutscene/scripted sequence completed; working killcam |
| Dialogue and quest state | Quest conversations/scripted dialogue; `Find the abbot in Oakfield`; monk conversation; accepted Rookridge bandit-elimination quest |
| Minigame | Blacksmithing |
| Exploration and rewards | Cellar chest; dig spot |
| Crime | Vandalism/crime event and fine paid |
| NPC event handling | Dave accidentally killed |
| Melee | Bandit combat |
| Ranged | Bandit combat |
| Will | Bandit combat |
| Save and exit | Saved at Oakfield tavern and quit normally |

Shops, inventory/equipment menus, a separate reload, profile-menu coverage and
precise crowd density are not independently confirmed. Timed/scripted quest
progression completed, but no exact NPC appearance latency was measured.
The Old Town visit was forward progression from the adult Market checkpoint,
not a replay of childhood.

The separate native endpoint coverage is deliberately narrower:

| Category | User-confirmed `phase5a-native-001` result |
| --- | --- |
| Transferred save loading | Oakfield tavern save loaded successfully |
| Control and basic interaction | Worked |
| Saving | Worked according to user; no fresh payload write independently demonstrated |
| Normal exit | Worked; runtime log also reaches window-close/title-termination path |

No nearby transition or preceding Market-to-Oakfield event is claimed as
native-covered. No additional problem was noticed during this short test.

## Reference provenance and shutdown

Session `phase5a-reference-001` used the prepared isolated content/storage roots
and the instrumented Xenia Canary binary:

```text
checkout: C:\Dev\Fable2Phase4Xenia\xenia-canary
branch: fable2-indirect-target-collector
HEAD: 32460b5d887dcde6622bb17983b70752fa5f13b3
tree: 114cb589291e2c87fcbcabc949a730ca5d1f6cad
embedded/raw/log build: 6b6715b029d442ff6ed5a89773f119400b1c19b5
exe SHA-256: 8DCD8FEA50BF971B4710C45494C47DB84EF77E9D04C60657EB3FE9311B49E65E
patched TU1 image: BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00
observed executable SHA-1: 341151E9932EC14CB4F520AA9DE35BCF7169BFE1
raw: out/indirect-targets/phase5a-reference-001/xenia-indirect-targets.raw.jsonl
raw bytes: 1280153418
raw SHA-256: 59CD5C1A985A46AFC211D9B550E82E36F12AC304A6B256684713496DC15EE298
log: out/indirect-targets/phase5a-reference-001/xenia-indirect-targets.raw.xenia.log
```

The checkout differs from the embedded build commit only in collector
documentation. The executable hash still matches the preflight pin. Raw
schema/collector version 2, module fingerprint, configured SHA-256, title
`4D5307F1`, media `716F0A0D`, and log-confirmed patch to `0.0.1.26` agree.
The configured SHA-256 is metadata, not a fresh runtime full-image hash;
the collector's observed executable-memory fingerprint supplies independent
runtime corroboration. The manifest retains base XEX, XEXP and TU-container
identities without their contents.

The persisted before/after configuration is byte-identical, SHA-256
`EE3400A5F70E8082657455DB16164CA740E3B99D83CCA526CDFE31FCE12352BB`.
It still has an empty trace path. Explicit launch arguments enabled 4096
buffer pairs, 3072 dirty pairs, 300000 ms persistence, a 1000000 aggregate
cap, ordinary returns excluded and all-modules false. The raw header confirms
these effective values; configuration defaults alone are not launch proof.

Validation found exactly one normal footer with `flush_reason=window_close`,
1113 checkpoints, 2960760 persisted pair records, 28657174372 hits and
32155 final thread/pair aggregates. Coalescing threads gives 27665 distinct
source/target/kind pairs. Dropped hits, I/O errors, count overflows,
aggregate-limit events and uncommitted records are all zero. There is no
corrupt tail or missing final newline. The log ends with `Cheap-skate exit!`;
the preceding `undefined extern call to 832BA424 XNetLogonGetTitleID` is not
treated as a demonstrated fatal failure in this cleanly completed session.

The header's `1788981320793517100` Unix ns is
`2026-09-09T19:15:20.793517100Z`; final raw write is
`2026-09-09T20:04:44.3685104Z`. Approximately 49m24s elapsed between those
events. This includes loading/saving/shutdown and is not a measured gameplay
window or exact process lifetime. Coverage is not inferred from that duration.

## Reconciliation and reviewed change

| Population | Targets | Pairs | Hits |
| --- | ---: | ---: | ---: |
| Accepted runs 001–002 | 16143 | 27785 | 43830575180 |
| This reference session | 16039 | 27665 | 28657174372 |
| Merged runs 001–002 plus Phase 5A | 16622 | 28743 | 72487749552 |

There are **15560 repeat targets, 479 genuinely new targets and 958 new
pairs**. The merged summary retains the previously accepted footerless legacy
run 001: its one legacy abnormal/truncated marker is not a defect in this
new, complete schema-2 session. No run is quarantined.

The 479 new observations resolve as follows:

| Reviewed disposition | Count | Action |
| --- | ---: | --- |
| Already registered entry | 323 | Retain registration |
| Conditional-return continuation | 68 | Retain existing owner; no promotion |
| Ordinary switch block | 73 | Retain block |
| Shared switch body | 8 | Retain block |
| Switch default case | 6 | Retain block |
| Missing callable tail-dispatch thunk | 1 | Add exact reviewed entry |

All 155 internal/switch entries passed TU1 section-byte checks, `.pdata`,
exact-image Ghidra, actual body ownership, call/LR or table/bound evidence and
generated-source checks. The switch proofs cover 41 dispatchers. No owner
correction or switch-to-function promotion was justified. LR values in return
proofs are derived from decoded link semantics, not direct register captures.

The initial planner incorrectly called `0x825E28B0` internal to the preliminary
gap-fill extent `[0x825E28A0,0x825E2A34)`. Its actual body ends at
`0x825E28B0`; generated `sub_825E28A0` terminates at its `bctr`. Ownership
corroboration correctly stopped with:

```text
FAIL: overlapping/wrong target ownership 0x825E28B0
```

Independent review established `[0x825E28B0,0x825E28C0)`, size `0x10`:

```text
0x825E28B0  lwz r11,0(r3)
0x825E28B4  lwz r10,116(r11)
0x825E28B8  mtctr r10
0x825E28BC  bctr
```

Five observed `bctrl` calls from `0x822665B4` in
`sub_82266518 [0x82266518,0x822665CC)` establish callable use, with decoded
LR after the call `0x822665B8`. The exact-image analyzer already had a complete
strong candidate traversal and read-only callback slot `0x82007370`.
The preceding thunk ends with `bctr` at `0x825E28AC`; the next `.pdata`
function begins at `0x825E28C0`. There is no owning recovered/Ghidra body,
exact `.pdata` start, or jump-table membership at the target. Absence from
`.pdata` and Ghidra is recorded, not invented as corroboration.

The planner fix requires actual basic-block membership before attributing
ownership to a preliminary extent. It supplies no boundary itself. The
existing strong static candidate then produced one guarded proposal:
`P4-FF74FACDEA53A5E8`. After the independent review, the supported importer
applied only:

```toml
"0x825E28B0" = { size = 0x10 }
```

The manifest now has 81 overrides; generated `sub_825E28B0` performs the
decoded dispatch and is registered. No SDK runtime change, stub, placeholder,
manual-table edit or setjmp/longjmp change was made. The importer-created
backup was preserved as `out/phase5a/tranche-001/manifest-before.toml`.

The final merged plan has 0 proposals, 0 conflicts and 0 ambiguous targets:
13411 registered entries, 1554 internal entries, 1648 switch destinations and
9 imports. Its registration total includes the new thunk. The static
non-link CTR reservoir is **711 before, 712 after**: registering the thunk
exposes `0x825E28BC`, classified `computed_tail_bctr` with `missing_bound`.
Its five observed transfers go to already registered `0x82676398`. No switch
table is implied by its virtual tail dispatch. This is additional static
visibility, not an unresolved observed function target or a quota to reduce.
The 878 recovered tables and manual-table authority remain intact.

## Processing and verification

Commands below ran from `C:\Dev\Fable2Recomp` unless stated otherwise. Logs
and repeated outputs are retained under `out/phase5a/tranche-001/`.

| Command/check | Exact result |
| --- | --- |
| Supported collector `Preflight`, explicit isolated roots | Preparation exit 0; pinned build/content/config accepted |
| `tools/Invoke-Fable2XeniaIndirectTrace.ps1 -Action PostRun -RunId phase5a-reference-001` | exit 0; valid complete session, initial dry-run plan only |
| Repeated `Fable2IndirectTargets.py post-run`, separate output directory | exit 0; summary JSON, CSV and initial dry-run plan byte-identical |
| `Fable2IndirectTargets.py merge`, accepted merged baseline plus new compact summary; repeated in reverse input order | exit 0 twice; JSON/CSV byte-identical; 3 accepted, 0 quarantined runs |
| Reviewed pre-application `plan` | exit 0; 1 proposal, 1 applicable after review |
| `Fable2IndirectTargets.py apply --plan out/phase5a/tranche-001/pre-application.import-plan.json --select P4-FF74FACDEA53A5E8 --apply` | exit 0; only `0x825E28B0` added |
| `tools/Build-PpcDisassembler.ps1 -SdkRoot C:\Dev\rexglue-sdk-v0.10` | exit 0; canonical disassembler; two C compiler unused `/std:c++20` warnings |
| `fable2-codegen` | exit 0; 5 written, 588 unchanged, 0 deleted; 98.0 s |
| `fable2-build` | exit 0; normal Release executable linked; dependency codegen 0 written, 1 module up to date |
| `tools/Invoke-Fable2EntrypointClosure.ps1 -OutputDirectory out/phase5a/tranche-001/closure-after` | exit 0; 35626 candidates, 54 strong, 180 probable |
| `python tools/Verify-Fable2EntrypointClosure.py --report out/phase5a/tranche-001/closure-after/entrypoint-closure.json` | exit 0; schema 3/analyzer 2.0.0, all 3 acceptance fixtures pass |
| Final `plan`, using regenerated closure; repeated against reversed merge | exit 0 twice; byte-identical; no proposal/conflict/ambiguity |
| `ownership-follow-up`, both baseline runs, expected counts 479/324/68/87 | exit 0; report `P4OWN-36EDC80959AAF5726018` |
| `Fable2OwnershipCorroboration.py` and `--check` with regenerated closure | exit 0; 155 exact body proofs, 41 dispatchers, 0 unresolved; byte-identical reconstruction |
| Original v1 follow-up regenerated from accepted 001/002 inputs | JSON, CSV and Markdown byte-identical; all 16143 baseline target records unchanged by planner fix |
| `python -m unittest discover -s tests -p 'test_*.py'` | exit 0; 98 tests, 7.842 s, OK; includes 8 new coverage regression tests |
| SDK: `ctest --preset win-amd64-release --output-on-failure --parallel 8` | exit 0; 1764 passed, 4 established BitStream skips, 0 failures; 1768 registered, 10.90 s |
| Coverage session schema checks | reference, prepared native and template pass |
| Save copy verification | exact reference checkpoint copy, seven exact payload hashes/path sets, native non-payload metadata unchanged |
| Native launch script PowerShell parser | pass; script not executed by agent |
| `git diff --check` and index review | required again immediately before evidence commit; result recorded in final-state audit |

Generation retains the known large-function warning for `0x82242F10`
(2533663 bytes, limit 1048576); generation/build succeeded. SDK tests retain
only established skips 51, 127, 163 and 164. No validator was weakened.

The only workflow changes are support for all accepted baseline runs in the
existing follow-up reporter (schema v2; v1 preserved), its ownership consumer,
and correction of preliminary extent/body confusion. Existing commands remain
authoritative. `PostRun` never applies changes; explicit reviewed selection is
still mandatory. A queue containing new proposals still rejects them until
the full plan is separately reviewed; that threshold was not relaxed.

Artifact hashes are retained in
[the session manifest](coverage/phase5a-reference-001.json). Large raw captures,
executable images, saves and analysis databases remain local and uncommitted.
The initial plans deliberately retain the pre-import state; a later plan using
the new manifest/registration/closure must differ from those initial plans.
Repeat raw processing into a new output directory rather than overwriting that
historical review. The final ownership reconstruction uses these exact inputs:

```powershell
python tools/Fable2IndirectTargets.py plan `
    --summary out/phase5a/tranche-001/merged/xenia-indirect-targets.summary.json `
    --closure out/phase5a/tranche-001/closure-after/entrypoint-closure.json `
    --ghidra-map out/analysis/BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00/ghidra-function-map.json `
    --output out/phase5a/tranche-001/merged/fable2-indirect-targets.import-plan.json

python tools/Fable2IndirectTargets.py ownership-follow-up `
    --baseline-summary out/indirect-targets/fable2-tu1-manual-001-002-merged/xenia-indirect-targets.summary.json `
    --contributing-summary out/indirect-targets/phase5a-reference-001/review/xenia-indirect-targets.summary.json `
    --merged-summary out/phase5a/tranche-001/merged/xenia-indirect-targets.summary.json `
    --plan out/phase5a/tranche-001/merged/fable2-indirect-targets.import-plan.json `
    --closure out/phase5a/tranche-001/closure-after/entrypoint-closure.json `
    --output-directory out/phase5a/tranche-001/merged `
    --expect-targets 479 --expect-existing-registrations 324 `
    --expect-internal-entries 68 --expect-jump-table-cases 87

python tools/Fable2OwnershipCorroboration.py `
    --phase4-directory out/phase5a/tranche-001/merged `
    --closure out/phase5a/tranche-001/closure-after/entrypoint-closure.json `
    --guest-snapshot out/phase3-regression-closure-final-smoke/iteration-01/tu1-text-0x82000000.bin `
    --output-directory docs/fable2-discovery-pipeline/coverage/phase5a-reference-001-ownership `
    --check
```

## Endpoint handoff and completed native run

Source, preserved endpoint and destination are explicit:

```text
source Xenia content:
C:\Dev\Fable2Recomp\out\phase5a\sessions\phase5a-reference-001\content
preserved closed endpoint:
C:\Dev\Fable2Recomp\out\phase5a\checkpoints\end-001\xenia-content
native metadata source (copy only):
C:\Dev\Fable2Recomp\out\phase5a\checkpoints\start-001\native-save
native writable root:
C:\Dev\Fable2Recomp\out\phase5a\sessions\phase5a-native-001\user-data
```

The seven `E03000002168622D\4D5307F1\00000001\Hero000` payload files were
copied into `B13EBABEBABEBABE\4D5307F1\00000001\Hero000` inside the new
native root. Its accepted native header/profile and all other files remain
equal to the preserved native metadata source. The endpoint mainsave is
415039 bytes, SHA-256
`13FC340F6869DA73CB958BA36CB50905E29B8FBEA073CEFF46490DB4A9812489`.
Original working roots, the Market checkpoint, and both protected backup roots
were preserved. No runtime was launched against a source or checkpoint.

**Completed native session `phase5a-native-001`:** the user ran this command
in developer PowerShell. It is retained as provenance, not a request to rerun:

```powershell
& 'C:\Dev\Fable2Recomp\out\phase5a\sessions\phase5a-native-001\Launch.ps1'
```

The requested scope was to load the copied **Oakfield tavern** save, confirm control and one basic
interaction, optionally try one nearby transition or interaction, save and
exit normally. The user confirmed load, control/basic interaction, saving and
normal exit; no additional problem was noticed. No Market-to-Oakfield replay
was performed or requested, and no additional run is required for closeout.

The session-local command card follows `fable2-run`'s normal argument pattern
and `Get-Fable2NextRunNumber`, adding the required explicit `--user_data_root`.
It does not change the global helper or copy/select any root at launch. It
verifies the prepared executable/save hashes, rejects reuse of this session,
and supplies no input. It selected `C:\Dev\Fable2Recomp\fable2-run-002.log` and
`out/phase5a/sessions/phase5a-native-001/invocation.json` with arguments,
timestamps, log path and an **uncaptured (null) exit code**. The script's
identity is in the native manifest; it was executed by the user.

Normal executable SHA-256:
`1642ED03BD8B117A8FED6E9FF912AD49CBF0E91A4E1D226B20C266925E3FF2C9`.
Both fault-walk switches are OFF. The normal helper's debug logging is retained;
no fault walker or generated boundary instrumentation is enabled. The
executable hash is unchanged from the successfully tested build and agrees
with the invocation record and original launch-time hash guard.

### Native evidence review and limitations

`invocation.json` records launch preparation at
`2026-09-09T20:51:00.9939640Z`, `process_end_utc` at
`2026-09-09T20:51:01.0320820Z`, and `exit_code: null`. That alleged end time
precedes the first native log entry; it is **not a valid process termination
timestamp**. The launch card returned without capturing the GUI process's
lifetime/status. The original invocation is preserved unchanged. No exit code
or process lifetime is manufactured from it, and no repeat run is required.

The 9332-line native log spans local timestamps
`2026-09-09 21:51:01.059` through `2026-09-09 21:52:23.294` (82.235 seconds of
logged activity, not a gameplay benchmark). It independently establishes:

- The intended isolated user-data and cache roots, runtime/update roots and
  `xenos` plugin were used.
- TU1 patching reached `0.0.1.26`; 60918 functions were registered with
  0 duplicates and 0 rejected entries.
- No fatal/critical log entry, invalid/unregistered function-target failure,
  unhandled exception or access-violation diagnostic was found. Filesystem
  `Unregistered symbolic link`/`Unregistered device` entries are ordinary
  content unmounting, not function-target failures.
- Line 9320: `Window closing, shutting down...`; line 9321:
  `KernelState::TerminateTitle`; line 9332:
  `Title terminated; hard-exiting process.` The pinned SDK's
  `src/ui/rex_app.cpp:498` normal `ReXApp::OnClosing` path flushes logging and
  calls `std::_Exit(0)` after that last message. This corroborates the user's
  normal-exit observation but does not supply a captured OS exit code.

There are 3856 instances of the established non-blocking
`BaseHeap::AllocFixed attempting to reserve an already reserved range` message.
The 13 warnings concern the missing controller database, denied optional
`D:\lhdebug.log` write (`0xc0000022`) and missing build-version, episodic or
language probes (`0xc000000f`). These are retained rather than describing the
log as warning-free; execution proceeds through the supported shutdown path.
Nothing found contradicts the successful user-observed endpoint result.

The user supplies the location, control/interaction and game-level saving
observations. All seven save payloads, including their timestamps, are
unchanged from the transferred starting endpoint; the log does not identify
a fresh `mainsave.bin` write. Saving therefore remains **user-confirmed**,
not independently proven as a new persisted payload by this short session.
No failed-save diagnostic was found and no save regression is inferred.

The complete closed native root was copied, without replacing any source, to
`C:\Dev\Fable2Recomp\out\phase5a\checkpoints\end-001-native\user-data`.
Its path set and all file hashes match the runtime root. The mainsave remains
415039 bytes with SHA-256
`13FC340F6869DA73CB958BA36CB50905E29B8FBEA073CEFF46490DB4A9812489`.
Only the shader pipeline-cache file changed relative to the initial native
inventory. The original reference endpoint, reference writable content and
earlier native checkpoint still match their preserved inventories.

New evidence hashes:

```text
invocation.json SHA-256:
947D7823B04D8CEB774A9D29EEA30EE060EFF4ED5079F37904FA33B5422AB64B
fable2-run-002.log SHA-256:
2F214CC13C482A5B35FD70265DBF0CF047F8BA675C0F35FC4396E5E13316D516
```

The session manifest references the log review and complete private endpoint
inventory under `out/phase5a/tranche-001/closeout/`. Raw logs and saves remain
uncommitted.

### Closeout checks and integration readiness

The closeout changes only documentation/session metadata. The executable hash
matches the previously generated and built binary; SDK source/identity and
tested Python tools remain unchanged. The successful regeneration, normal
build, 98 Python tests and SDK 1764 passes/4 established skips above are reused.
No expensive build or full test rerun was performed solely for these edits.
Closeout checks validate session schemas, the exact unchanged reference totals,
new native artifact hashes, source/binary identity, preserved save inventories,
SDK dirt, Git whitespace and the staged file list.

A pre-existing worktree edit removes one blank line before the thunk in
`fable2_manifest.toml`. It is preserved and excluded from the closeout commit.
Parsed TOML equals the tested committed manifest, including all 81 overrides.
Its working-file SHA-256 is
`EF1656D77D270F207C4A16D3B92D5B86C4414CE38292D079AEF52B120CE778E1`;
historical byte-bound plans still identify the original manifest hash, so
their stale-input guards must not be bypassed against this reformatted file.
This is not another function or runtime change.

The committed Phase 5A branch is ready for local integration into `main`.
The local `main` remains `07184adfeab7018670c3205bbef9087caa960dd5` and is an
ancestor of the topic; no integration was performed. Preserve the unrelated
manifest formatting edit during any later integration. The index is clean
after closeout; that manifest edit and the SDK's original libmspack dirt are
the only worktree changes. Exact checks and final identities are recorded in
`out/phase5a/tranche-001/closeout/final-state.json` after the closeout commit.

## Rendering and performance observations

The user reported three non-blocking visual defects: distant Spire hard cutoff
at **20:23**, extremely elongated dog shadows in Old Town at **20:26**, and
excessive/improperly blended moon bloom at **20:30**. Rookridge terrain rendered
correctly, unlike the other recompilation attempt. These are reference-runtime
rendering observations, not native results or performance faults.
All three visual defects remain outstanding. A successful native endpoint
test does not establish that the Spire cutoff, dog shadows or moon bloom were fixed.

Assuming the reported clock is the workstation's Europe/London timezone, those
observations fall about 7m39s, 10m39s and 14m39s after the collector header.
That timezone mapping is an inference. The Xenia log uses thread prefixes
without wall-clock timestamps; no precise log-line association or renderer
root cause is established.

The user reported no separate sustained low FPS, stutter or progressive
slowdown complaint. This subjective absence of a complaint is not an FPS or
frame-time measurement. No controlled collector-off/on gameplay comparison
exists, so actual gameplay tracing overhead remains unmeasured. The earlier
seven-pair synthetic JIT benchmark (22.828 ns disabled, 31.546 ns enabled,
median ratio 1.381899) is only a transfer microbenchmark. Fresh isolated Xenia
caches further limit any comparison. The historical instrumented 4–5 FPS
figure is not assigned to the current normal build. No optimization phase or
additional tracing was started.
The user's native report likewise contains no additional problem, but the
brief smoke test provides no quantitative FPS, frame-time or tracing-overhead
measurement. Gameplay tracing overhead remains **unmeasured**.

## Next tranche and repository state

The successful native endpoint has been preserved. A future separately
authorized tranche may copy its compatible payload into a newly named isolated
reference root. Start from the latest **Oakfield tavern endpoint**, not Market
or childhood. The user may continue the already accepted Rookridge
bandit-elimination quest and naturally reachable content. Prioritize a new
area/transition and, where naturally available, shops, inventory/equipment
and a distinct reload session, which remain unconfirmed here. No quest route
or control sequence is prescribed. Finish the next bounded run with save and
orderly exit, then process it before requesting further collection.

No tranche-001 completion gate remains. No native failure justifies fault
walking, another gameplay run or x-high investigation. No next tranche or
renderer work was begun during closeout. Full native replay parity, the three
visual defects and quantitative performance/overhead remain outside this
completed endpoint validation.

Starting Fable branch/commit/tree: `main`,
`07184adfeab7018670c3205bbef9087caa960dd5`,
`d6119205ffd5fac37f99917f99121dbf268d6853`, clean.
Current topic: `fable2-phase5a-runtime-coverage`.

Both starting and final SDK identities: `main`,
`fc5a00b31f702e82377aa1010395af7ba8cff4f7`,
`903af44f9aab5684443ddb22e505b0ea811d45d2`; only the exact pre-existing
`thirdparty/libmspack` dirt is retained, index clean. No SDK branch/change.

Local implementation commits:

```text
6ce2de57d7f499a8c99cc3e1370d03c6d61ea0b6
tree 851e38b9cd6d8870af4a033b9fe87fa287c89d00
fix(coverage): reconcile merged baselines and preliminary body ownership

6760651b01e4a1b1caefc3f00e5a6d0d5d2c5e02
tree 2b0ee576bf8a564d6f05e1f0003cd804e4b6adc7
fix(recomp): register traced TU1 tail-dispatch thunk 825E28B0
```

The prior preparation commits are `4221ee1a4824934548c285b14b68fe3b50d42849`,
`93c69d4af821059d9e2fa5e107a332e1b510764e`, and
`dd169a16093e512d127ac831cd7fd0dc9a535fb5`. Exact final Fable commit/tree,
index/worktree states, complete local commit list and preservation checks for
the pre-smoke evidence commit are retained in
`out/phase5a/tranche-001/final-state.json`. Completed closeout identities and
the preserved pre-existing manifest edit are recorded separately in
`out/phase5a/tranche-001/closeout/final-state.json`; a tracked report cannot
contain its own resulting commit hash. Recover its committed identity with
`git log -1 --format='%H %T' -- docs/fable2-discovery-pipeline/09-phase5a-tranche-001.md`.
Nothing has been pushed, pulled, remotely merged, tagged, uploaded, released,
published or otherwise remotely modified.
