# Phase 5A: first forward-only coverage tranche

## Status: reference processed; native endpoint smoke pending

Preparation date: 2026-09-09. **Phase 5A is not complete.** The completed
Bowerstone Market-to-Oakfield tavern reference session, reviewed thunk import,
coverage matrix, save handoff and current native run card are recorded in the
[tranche report](09-phase5a-tranche-001.md). That report supersedes the pending
items in this historical preparation record. Only the short native endpoint
load/control/basic-interaction/save/exit smoke test remains; no full replay is
required. The sections below preserve the pre-run baseline and preparation.

## Reconstructed baseline

Before analysis/build/editing, the applicable root `AGENTS.md`, both root
READMEs and current narrative documentation were read completely, including
bring-up/input, fault-walker harvests, migration, save parity, discovery phases,
focused ownership and the historical GPU/native-renderer corpus. SDK
contribution/release and PPC text documentation were reviewed; the two generic
PPC ISA PDFs were inventoried as reference material. Associated machine-readable
evidence, schemas, fixtures and generated summaries are checked through the
existing validators and full Python suite. No historical renderer gate is
reactivated. No nested instruction governs the new documentation/schema paths.

Starting identities were verified before changes; no reset was performed:

| Repository | Starting branch | HEAD | Tree | Index/worktree |
| --- | --- | --- | --- | --- |
| `C:\Dev\Fable2Recomp` | `main` | `07184adfeab7018670c3205bbef9087caa960dd5` | `d6119205ffd5fac37f99917f99121dbf268d6853` | clean |
| `C:\Dev\rexglue-sdk-v0.10` | `main` | `fc5a00b31f702e82377aa1010395af7ba8cff4f7` | `903af44f9aab5684443ddb22e505b0ea811d45d2` | index clean; existing `thirdparty/libmspack` dirt only |

Fable topic branch `fable2-phase5a-runtime-coverage` was created directly from
that verified baseline. No SDK branch is needed. The private
`out/phase5a/preparation/starting-inventory.json` records identities immediately
after topic-branch creation, 93 documentation/reference file identities and
all 15 existing libmspack symlink-materialization paths with hashes. The
initial Fable branch in the table above precedes that branch-only operation.

Accepted integration history includes Fable ownership implementation
`98c5e0872a93e56469a32d1b2e63892d949de15c` and its closeout
`07184adfeab7018670c3205bbef9087caa960dd5`, Fable integrated SDK pin
`18f9652e3b864637db7d6525b6ce1964c92f4447`, SDK save integration
`3ee1722b1b287744e1a4dbde631691713c722de2` and schema-5 contract
`fc5a00b31f702e82377aa1010395af7ba8cff4f7`. Recent histories in both
repositories were inspected. Native gameplay through Old Town and Market,
normal exit, save creation/reload and both interoperability directions remain
accepted. No save-system regression is inferred or reopened.

## Reference session and save isolation

The prepared record is
[phase5a-reference-001.json](coverage/phase5a-reference-001.json). The reusable
[workflow and contract](coverage/README.md),
[template](coverage/session-template.json) and
[schema](../../tools/schemas/fable2-coverage-session-v1.schema.json) distinguish
planned work from user-confirmed coverage, raw termination from user reports,
and source commits from executable identities.

Selected start: **Bowerstone Market, Hero000 from the accepted State D native
update/restart and Xenia reload checkpoint of 2026-09-08**. The user confirms
that childhood/prologue content in Bowerstone Old Town is already completed.
The current objective is to meet the blind woman from the Guild at the fountain
in the middle of Bowerstone Market. These are user-reported checkpoint facts,
not inferred save semantics or evidence of an already completed traced run.
The latest documented
native-updated `mainsave.bin` is 359,742 bytes, SHA-256
`1643F56CADC91A75CAF7D6620DFCEC4323BEDF079AF663B7BA3758A62685A9D4`.
The older current reference root still contained the 356,173-byte pre-update
main save, so its payload was not selected as the campaign endpoint.

The user reports an expected approximately five-minute wait for the NPC to
appear. This is expected game behaviour, not automatically a hang or
progression failure. It becomes suspicious only if the expected conditions
are met and she still fails to appear substantially beyond the normal wait.
No automatic timeout or arbitrary failure threshold is introduced. Waiting,
interaction and all subsequent gameplay remain user-controlled.

After the correction, all seven isolated Hero000 payloads were rechecked
against State D and the preserved launch checkpoint. No save replacement or
modification was needed. The ordinary working root at
`C:\Users\Fenris\Documents\fable2` still has the earlier 356,173-byte main
save dated `2026-09-02T17:10:02.8185507Z`; selected State D and its isolated
copy have the 359,742-byte main save dated `2026-09-08T17:25:00.6841654Z`.
Timestamps are corroboration; the exact payload hashes establish copy identity.

| Role | Exact local path |
| --- | --- |
| Working source, read-only during preparation | `C:\Dev\Fable2Recomp\out\native-save-diagnostic\D-xenia-update` |
| Copied native checkpoint, never a writable runtime root | `C:\Dev\Fable2Recomp\out\phase5a\checkpoints\start-001\native-save` |
| Copied reference profile/header/TU source | `C:\Dev\Fable2Phase4Xenia\content` |
| Preserved reference source before payload handoff | `C:\Dev\Fable2Recomp\out\phase5a\checkpoints\start-001\xenia-content` |
| Preserved exact launch content | `C:\Dev\Fable2Recomp\out\phase5a\checkpoints\start-001\xenia-launch-content` |
| **Writable Xenia content** | `C:\Dev\Fable2Recomp\out\phase5a\sessions\phase5a-reference-001\content` |
| **Writable Xenia storage/config/cache** | `C:\Dev\Fable2Recomp\out\phase5a\sessions\phase5a-reference-001\storage` |

All seven Hero000 payload files were copied unchanged from the preserved native
profile `B13EBABEBABEBABE` into the disposable reference profile
`E03000002168622D`. The existing Xenia header/profile was retained. Exact
payload path sets and hashes agree. Both source roots remain unchanged.
Neither `C:\Users\Fenris\Documents\fable2.backup` nor
`C:\Dev\Fable2XeniaSaves` was accessed or made writable.

The copied reference configuration and `xconfig.settings` come from
`C:\Dev\Fable2Phase4Xenia\storage`. Configuration is pinned before launch
at `out/phase5a/preparation/reference-config-before.toml`, SHA-256
`EE3400A5F70E8082657455DB16164CA740E3B99D83CCA526CDFE31FCE12352BB`.
Resolution scaling remains 1x1. Caches are fresh and isolated, a material
limitation for interpreting first-use performance symptoms. The base config
keeps collection disabled; explicit launch arguments enable it only for this
session, with 4,096 buffer pairs, 3,072 dirty pairs, 300,000 ms persistence,
1,000,000 unique aggregates, ordinary returns excluded and all-modules false.

Collector checkout: `C:\Dev\Fable2Phase4Xenia\xenia-canary`, branch
`fable2-indirect-target-collector`, commit
`32460b5d887dcde6622bb17983b70752fa5f13b3`, tree
`114cb589291e2c87fcbcabc949a730ca5d1f6cad`, clean. Its only difference from
embedded build commit `6b6715b029d442ff6ed5a89773f119400b1c19b5` is
`docs/fable2-indirect-target-collector.md`. The executable contains that full
build commit. Supported incremental Release build reports no work to do.
Actual executable: 17,271,808 bytes, SHA-256
`8DCD8FEA50BF971B4710C45494C47DB84EF77E9D04C60657EB3FE9311B49E65E`.
This actual artifact is recorded separately from the older Phase 4 documented
binary hash; no unsupported claim of binary identity is made.

## Preparation run card (completed; do not reuse this RunId)

From `C:\Dev\Fable2Recomp` in developer PowerShell:

```powershell
.\tools\Invoke-Fable2XeniaIndirectTrace.ps1 `
    -Action Launch `
    -RunId phase5a-reference-001 `
    -Label 'Phase 5A forward-only tranche 001' `
    -ContentRoot C:\Dev\Fable2Recomp\out\phase5a\sessions\phase5a-reference-001\content `
    -StorageRoot C:\Dev\Fable2Recomp\out\phase5a\sessions\phase5a-reference-001\storage
```

This is **Xenia Canary reference collection**, not native recompilation. Load
the copied Bowerstone Market Hero000 checkpoint above and choose your own
forward route. Do not return to completed childhood content. Aim for
a bounded 30–60 minute session where practical; a valid longer session is not
discarded. The initial planned categories are Market crowds/NPC AI, timed
quest-state progression, scripted NPC appearance, dialogue and whatever
transition follows. Allow the expected approximately five-minute fountain
wait. These are planned categories, not claimed coverage or a walkthrough.
Save normally, wait for saving to finish, then close the Xenia
window and allow the command to return.

Raw JSONL and Xenia log are under
`C:\Dev\Fable2Recomp\out\indirect-targets\phase5a-reference-001\`:
`xenia-indirect-targets.raw.jsonl` and
`xenia-indirect-targets.raw.xenia.log`. Report the starting/ending areas,
categories actually exercised, whether the NPC appeared and dialogue/progression
continued, whether saving and clean exit succeeded, and any blocker or
performance symptom with approximate session time if known.
Partial symptom reports are useful; no FPS measurement is required.

## First-tranche coverage matrix at preparation time

Only user-confirmed exercised categories will be added here.

| Session | Runtime | Confirmed areas | Confirmed exercised categories | Outcome |
| --- | --- | --- | --- | --- |

**No confirmed rows yet.** Reference run, orderly footer, new-target analysis,
end-save transfer and native endpoint smoke test all remain pending. Native
performance, crashes, hangs, rendering, progression and save/exit outcomes for
this phase are unknown, not passing by inference from compilation.

## Accepted evidence reconciliation

Two new merges in opposite input order reproduce the accepted Phase 4 outputs
byte-for-byte. Inputs are the preserved manual-001 and manual-002 compact
summaries. No raw manual-001 file was reconstructed.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| merged JSON | 27,377,874 | `AE4670BAFDF6FC8AB719F81CCE14C5BD63FDD4EAA8262D0CDAB79B0E39F83A29` |
| merged CSV | 5,534,648 | `39D4600C006C84465612D70043E84B09DA8DE0075389AEFBBF28D8803CBC3D82` |
| current baseline dry-run plan | 58,501,469 | `446EF1C3EE0899AF1EF6278AD52D79E0538B4E72703940EBDE23550FD25C18AA` |

Baseline: 2 accepted runs, 0 quarantined, 27,785 pairs, 16,143 targets.
Classification: 13,087 effective registrations (`existing_manifest_function`),
1,486 internal entries, 1,561 switch cases, 9 import/kernel targets; zero
ambiguous, conflicting, proposed or applicable targets. These are **known
baseline counts**, not Phase 5A observations. New target/pair counts remain
unknown until the reference run is processed.

The focused 156-target ledger remains authoritative: 42 conditional-return
continuations; 91 ordinary cases, 20 shared bodies, one default and two case
blocks immediately tail-branching to existing functions. None is promoted.
The current documented unresolved static population remains 711 relevant
non-link CTR sites, a coverage reservoir rather than a quota.

No manifest, runtime, SDK, collector, generated-code or normal-helper change is
justified during preparation. Manifest SHA-256 remains
`E3EB39CA153E396D5DC53E6F943ED8FF7AF1D6B0704EB860836BD7D21A3F87B0`.

## Preparation verification

All operational outputs are ignored under `out/phase5a/preparation/`.

| Command/check | Result |
| --- | --- |
| supported collector `-Action Preflight` with run-card roots | exit 0; exact base XEX/XEXP/STFS identities, writable isolated roots, ISO final positional argument |
| `python -m unittest discover -s tests -p 'test_*.py'` | exit 0; 90 tests in 5.264 s, OK |
| SDK `ctest --preset win-amd64-release --output-on-failure --parallel 8` | exit 0; 1,764 passed, 4 established skips, 0 failures; 1,768 registered |
| `fable2-build` | exit 0; SDK `0.10.0.51-dev.gfc5a00b`; codegen 0 written, 0 unchanged, 0 deleted, 1 module up to date |
| Xenia `python .\xenia-build.py build --config=release --build-tests --no_premake` | exit 0; existing configured build, `ninja: no work to do.`, Success |
| Xenia `xenia-cpu-tests.exe '[collector]'` | exit 0; 20,327 assertions in 13 cases, including synthetic enabled/disabled checks |
| `python tools/Verify-Fable2EntrypointClosure.py` | exit 0; schema 3/analyzer 2.0.0; 35,626 candidates, 55 strong, 180 probable, all 3 fixtures |
| `python tools/Verify-Fable2GpuReference.py --sdk-root C:\Dev\rexglue-sdk-v0.10 --canary-root C:\Dev\Fable2NativeRendererResearch\xenia-canary` | exit 0; complete accepted GPU evidence corpus, 0 warnings; no attempt to recover deleted historical logs |
| supported compact merge, twice with reversed inputs | exit 0; byte-identical to accepted JSON and CSV |
| supported dry-run `plan` on regenerated baseline | exit 0; all target records and full plan hash equal accepted ownership-phase plan; 0 proposals |
| `python tools/Fable2OwnershipCorroboration.py --phase4-directory out/ownership-corroboration/phase4-run1 --closure out/ownership-corroboration/closure-run1/entrypoint-closure.json --guest-snapshot out/phase3-regression-closure-final-smoke/iteration-01/tu1-text-0x82000000.bin --output-directory docs/fable2-discovery-pipeline/ownership --check` | exit 0; full exact-byte reconstruction equals accepted ledger and companion; 156 targets, 42 dispatchers, 0 unresolved/owner corrections/functions/manifest changes |
| coverage template and prepared record | pass existing schema-checking helper; empty user-confirmation fields verified |
| save copying | exact source/copy inventories and hashes agree; originals unchanged |
| `git diff --check` | exit 0; only Git checkout LF/CRLF notices, no whitespace errors |

Current normal native executable: 105,042,944 bytes, SHA-256
`150F420CFC6217FD6F55F5B46690E21FEA80035E93D79CF6471E63D5ABC4D81A`.
Current staged GPU plugin: 2,770,944 bytes, SHA-256
`70492C8612DEF79C9E3946817F424111FAB2155A3BE63CEA6E717CA73893ADC5`.
Both fault-walk CMake switches are OFF. Recheck these identities after any
later reviewed change and before the native endpoint run.

## Performance evidence and limits

At preparation time no Phase 5A gameplay performance observation existed. The optional
collector test's seven paired 200,000-transfer synthetic JIT samples measured
disabled median 22.828 ns/transfer, enabled median 31.546 ns/transfer, median
ratio 1.381899. This is a microbenchmark, not a gameplay-overhead estimate or
FPS result. Full data is retained in `collector-tests.log`.

No controlled same-scene gameplay collector-off/on comparison has been made.
Normal native FPS and collector gameplay overhead therefore remain unknown.
The earlier instrumented 4–5 FPS observation is not assigned to the normal
build. User performance reports will be correlated with this session's logs,
with subjective values and uncertain causes labelled explicitly. No broad
optimization or new performance instrumentation is introduced.

## Remaining gate and next forward-only tranche

Reference processing and the isolated endpoint handoff are now complete.
The remaining dependency is the short Oakfield tavern native smoke test in
the [tranche report](09-phase5a-tranche-001.md). Do not repeat the reference
run card above or replay its complete gameplay section.

The earlier Xenia events will be **reference-covered and statically/build
validated but not immediately replay-validated in the recompilation**. This
is the deliberate strategy, not proof of end-to-end native parity. Any actual
endpoint failure must be localized and fixed/revalidated or left as an exact
remaining blocker. No x-high blocker is currently justified.

The next tranche will start at the latest compatible preserved endpoint and
sample user-reported unexercised categories or a naturally reachable new area.
A precise region/quest recommendation awaits the first coverage report;
none is guessed now.

## Local history and state recording

Preparation changes are documentation, a session schema/template and byte-free
session metadata only. Logical local commit identities and the final tree are
recorded after committing under `out/phase5a/preparation/final-state.json`;
a tracked report cannot embed its own resulting commit hash. Recover the
preparation commit with `git log -1 --format='%H %T' --
docs/fable2-discovery-pipeline/08-phase5a-runtime-coverage.md`.

SDK branch/HEAD/tree remain the starting values above; its existing libmspack
dirt must compare byte-for-byte to the starting inventory. No push, pull,
merge, tag, PR, upload, release or other remote mutation is authorized or
performed. Phase completion will be recorded only after the manual evidence
and native endpoint result have been analysed.
