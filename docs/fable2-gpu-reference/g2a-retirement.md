# G2A retirement record

## Status

**G2A RETIRED — DO NOT RESUME**

This record supersedes the G1.5D proposal to revise the G2A forwarding proof.
It retires the abandoned implementation without changing the factual G1,
G1.5 or G1.6 record. It is a repository-hygiene decision, not renderer work.

Evidence labels in this record follow the repository convention. Git object,
tree, ancestry, path and content comparisons below are **CONFIRMED**.

## Protected identities

The retirement began from this exact clean Fable state:

| Item | Exact identity |
|---|---|
| Active starting branch | `fable2-native-renderer-g1.6b-static-seam-coverage` |
| Active starting commit | `cd440652451e558b88ba50402721e4cbe82b9a90` |
| Active starting tree | `6a87058d1ef47473e8fa80e9e2882d6cde6b8a7b` |
| Cleanup branch | `fable2-native-renderer-g2a-retirement`, created directly from the active starting commit |
| Accepted G1 / merge base | `c44e8c16f4422f9a828caf30899ac989170b8a8c`, tree `f5bde8e945f2d2ab6764c4d9c38f0f3550cac40c` |
| Obsolete local branch | `fable2-native-renderer-g2a-forwarding-proof` |
| Obsolete checkpoint | `47c2ea2b7d9e14b09fd942c4b5f1bd11c46e2f51` |
| Obsolete checkpoint tree | `910e80108c2d9e7d8474866506f1c9e23ede601c` |

The checkpoint is a single child of accepted G1. `git merge-base HEAD
47c2ea2b7d9e14b09fd942c4b5f1bd11c46e2f51` returned the accepted G1 commit.
`git merge-base --is-ancestor 47c2ea2b7d9e14b09fd942c4b5f1bd11c46e2f51
HEAD` returned exit code `1`: the active lineage does **not** contain the
checkpoint. The reverse ancestry test also returned exit code `1`.

Before cleanup, only the exact obsolete local branch contained the checkpoint.
No linked worktree used that branch. No same or similar remote-tracking ref
existed.

## Authoritative checkpoint delta

The direct parent of the checkpoint is accepted G1, so the authoritative
inventory is the exact diff
`c44e8c16f4422f9a828caf30899ac989170b8a8c..47c2ea2b7d9e14b09fd942c4b5f1bd11c46e2f51`:
16 changed paths, 2,888 insertions and no deletions.

| Checkpoint path | Checkpoint-only content | Active-lineage classification |
|---|---|---|
| `.gitignore` | Five-line explicit `/out/native-renderer-captures/` rule | `SHARED/NON-G2A INFRASTRUCTURE`; active blob is accepted G1 and the G2A hunk is `ABSENT FROM ACTIVE LINEAGE` |
| `CMakeLists.txt` | G2A Git/build identity, `fable2_g2a_capture`, hook integration, test target and compile definitions | `SHARED/NON-G2A INFRASTRUCTURE`; active blob is accepted G1 and every G2A hunk is `ABSENT FROM ACTIVE LINEAGE` |
| `src/fable2_app.h` | Capture initialization, ready, close and shutdown callbacks | `SHARED/NON-G2A INFRASTRUCTURE`; active blob is accepted G1 and every G2A hunk is `ABSENT FROM ACTIVE LINEAGE` |
| `src/native_renderer/g2a_capture.cpp` | Session writer, bounded queue, records, counters, recursion and forwarding state | `ABSENT FROM ACTIVE LINEAGE` |
| `src/native_renderer/g2a_capture.h` | G2A capture/forwarding API and record types | `ABSENT FROM ACTIVE LINEAGE` |
| `src/native_renderer/g2a_hook.cpp` | Strong `sub_82BA34D8` wrapper, preserved-original dispatch and four CVar definitions | `ABSENT FROM ACTIVE LINEAGE` |
| `tests/test_g2a_capture.cpp` | Synthetic forwarding/capture tests | `ABSENT FROM ACTIVE LINEAGE` |
| `tests/test_g2a_capture_validator.py` | Validator unit tests | `ABSENT FROM ACTIVE LINEAGE` |
| `tests/fixtures/g2a/events.jsonl.partial` | Synthetic invocation fixture | `ABSENT FROM ACTIVE LINEAGE` |
| `tests/fixtures/g2a/session.json.partial` | Synthetic session fixture | `ABSENT FROM ACTIVE LINEAGE` |
| `tools/Validate-Fable2G2ACapture.py` | Capture/session validator | `ABSENT FROM ACTIVE LINEAGE` |
| `tools/Verify-Fable2G2A.py` | Hook, boundary, ancestry and hygiene verifier | `ABSENT FROM ACTIVE LINEAGE` |
| `tools/schemas/fable2-g2a-invocation-v1.schema.json` | Provisional invocation schema | `ABSENT FROM ACTIVE LINEAGE` |
| `tools/schemas/fable2-g2a-session-v1.schema.json` | Provisional session schema | `ABSENT FROM ACTIVE LINEAGE` |
| `docs/fable2-native-renderer/g2a-paused-checkpoint.md` | Human-readable paused checkpoint | `HISTORICAL EVIDENCE — RETAIN`; read directly from the checkpoint and preserved by this superseding record and the dated corpus |
| `docs/fable2-native-renderer/g2a-paused-checkpoint.json` | Machine-readable paused checkpoint | `HISTORICAL EVIDENCE — RETAIN`; read directly from the checkpoint and preserved by this superseding record and the dated corpus |

The checkpoint's exact implementation identifiers included
`fable2_g2a_capture`, `fable2_g2a_tests`, `fable2_g2a_forwarding`,
`FABLE2_G2A_*`, `fable2_renderer_capture*`,
`out/native-renderer-captures/g2a`,
`fable2-native-renderer-g2a-invocation`,
`fable2-native-renderer-g2a-session`, `DispatchForwardInvocation`,
`CaptureSession`, and the strong `sub_82BA34D8` wrapper's dispatch to the
distinct `__imp__sub_82BA34D8` original.

## Active-lineage remnant audit

Every checkpoint-touched active path was compared to accepted G1. The 13
checkpoint-added paths are absent. The active `.gitignore`, `CMakeLists.txt`
and `src/fable2_app.h` blobs are exactly their accepted-G1 blobs. The base-to-
active diff restricted to all 16 checkpoint paths is empty.

The active source, build, test, configuration, manifest and generated surfaces
contain none of the G2A-specific implementation relationships above. In
particular there is no forwarding wrapper, preserved-original dispatch glue,
capture/session writer, serializer, counter/rotation/lifecycle state, feature
switch, source-list entry, CMake target, fixture, G2A validator, G2A schema or
generated wrapper. ReXGlue's shared generated public/original symbol mechanism,
the unmodified title function and historical references to `sub_82BA34D8` are
not G2A remnants.

Active-lineage classification counts, using checkpoint path/hunk provenance as
the audit unit, are:

| Classification | Count | Disposition |
|---|---:|---|
| `OBSOLETE IMPLEMENTATION REMNANT` | 0 | Nothing to remove from the active lineage |
| `SHARED/NON-G2A INFRASTRUCTURE` | 3 paths | Retain accepted-G1 `.gitignore`, `CMakeLists.txt` and `src/fable2_app.h`; their G2A hunks are absent |
| `HISTORICAL EVIDENCE — RETAIN` | 28 pre-retirement tracked paths, plus this record | Retain dated documents, JSON evidence, schemas and verifier support |
| `UNRELATED — PRESERVE` | 0 tracked paths | No unrelated tracked change was present |
| `ABSENT FROM ACTIVE LINEAGE` | 13 added paths and 3 exact hunks | No cleanup deletion required |

The 28 pre-retirement tracked G2A matches classified as `HISTORICAL EVIDENCE —
RETAIN` are exactly:

```text
docs/fable2-gpu-reference/00-scope-and-pins.md
docs/fable2-gpu-reference/06-fable2-relevance-assessment.md
docs/fable2-gpu-reference/07-boundary-and-ownership-reassessment.md
docs/fable2-gpu-reference/09-evidence-gaps-and-experiment-plan.md
docs/fable2-gpu-reference/11-g2a-reentry-decision.md
docs/fable2-gpu-reference/12-static-xdk-method-recovery.md
docs/fable2-gpu-reference/13-static-xdk-seam-coverage.md
docs/fable2-gpu-reference/README.md
docs/fable2-gpu-reference/evidence/boundary-assessment.json
docs/fable2-gpu-reference/evidence/experiment-backlog.json
docs/fable2-gpu-reference/evidence/fable2-relevance-matrix.json
docs/fable2-gpu-reference/evidence/g2a-decision.json
docs/fable2-gpu-reference/evidence/replacement-seams.json
docs/fable2-gpu-reference/evidence/rexglue-source-inventory.json
docs/fable2-gpu-reference/evidence/static-xdk-method-inventory.json
docs/fable2-gpu-reference/evidence/static-xdk-seam-coverage.json
docs/fable2-gpu-reference/g1.5a-completion.md
docs/fable2-gpu-reference/g1.5b-completion.md
docs/fable2-gpu-reference/g1.5c-completion.md
docs/fable2-gpu-reference/g1.5d-completion.md
docs/fable2-gpu-reference/g1.6a-completion.md
docs/fable2-gpu-reference/g1.6b-completion.md
docs/fable2-gpu-reference/open-questions.md
tools/Verify-Fable2GpuReference.py
tools/schemas/fable2-gpu-fable-relevance-v1.schema.json
tools/schemas/fable2-gpu-g2a-decision-v1.schema.json
tools/schemas/fable2-gpu-static-xdk-method-inventory-v1.schema.json
tools/schemas/fable2-gpu-static-xdk-seam-coverage-v1.schema.json
```

Ten ignored local Debug build/test artefacts from the abandoned attempt still
exist. Eight are `OBSOLETE IMPLEMENTATION REMNANT` local artefacts:

```text
tools/__pycache__/Validate-Fable2G2ACapture.cpython-314.pyc (18,710 bytes)
tests/__pycache__/test_g2a_capture_validator.cpython-314.pyc (6,008 bytes)
out/build/win-amd64-debug/CMakeFiles/fable2_g2a_tests.dir/tests/test_g2a_capture.cpp.obj (1,241,866 bytes)
out/build/win-amd64-debug/CMakeFiles/fable2_g2a_capture.dir/src/native_renderer/g2a_capture.cpp.obj (1,148,588 bytes)
out/build/win-amd64-debug/CMakeFiles/fable2.dir/src/native_renderer/g2a_hook.cpp.obj (1,070,881 bytes)
out/build/win-amd64-debug/fable2_g2a_tests.pdb (2,981,888 bytes)
out/build/win-amd64-debug/fable2_g2a_tests.exe (586,240 bytes)
out/build/win-amd64-debug/fable2_g2a_capture.lib (1,304,682 bytes)
```

Two generic consumer objects whose build paths name the external G2A SDK
install are `UNRELATED — PRESERVE` with respect to implementation provenance:

```text
out/build/win-amd64-debug/CMakeFiles/fable2.dir/C_/Dev/Fable2G2A/rexglue-install-debug-956c6a8/share/rexglue/windowed_app_main_sdl.cpp.obj (832,932 bytes)
out/build/win-amd64-debug/CMakeFiles/fable2.dir/C_/Dev/Fable2G2A/rexglue-install-debug-956c6a8/share/rexglue/rex_app.cpp.obj (2,200,600 bytes)
```

All ten are ignored, not tracked or staged, and not part of the active lineage.
They are preserved because this cleanup does not authorize deleting binaries
or ignored output. The accepted active Release `fable2.exe` remains 105,042,944
bytes with SHA-256
`EEACEAA8DB38E728B79F4F78B0298B7036E13EB4903518C503199697FA64AE6F`;
a direct string scan found none of the G2A target, CVar, dispatcher, log or
capture-root identifiers.

No active-lineage path was removed.

## Historical evidence retained

The dated G1, G1.5 and G1.6 findings and machine-readable records remain
intact. Only concise current-supersession annotations are added to the index,
historical plan/decision and open-question surfaces. In particular:

- [`11-g2a-reentry-decision.md`](11-g2a-reentry-decision.md) and
  [`g2a-decision.json`](evidence/g2a-decision.json) preserve what was proposed
  at G1.5D and why the boundary was insufficient for defect diagnosis;
- [`07-boundary-and-ownership-reassessment.md`](07-boundary-and-ownership-reassessment.md),
  [`09-evidence-gaps-and-experiment-plan.md`](09-evidence-gaps-and-experiment-plan.md)
  and [`10-custom-renderer-reference-architecture.md`](10-custom-renderer-reference-architecture.md)
  preserve the boundary, ownership and experiment context;
- the G1.5D, G1.6A and G1.6B completion records preserve the proof that the
  accepted lineage did not incorporate the checkpoint;
- the checkpoint commit/tree, exact path inventory, failed
  `_ITERATOR_DEBUG_LEVEL` link, source/synthetic-only exact-once result and
  lack of production/gameplay proof remain recorded here.

These records prevent the abandoned mechanism from being mistaken for linked
or runtime evidence and prevent the same insufficient boundary work from being
repeated. Their historical phrases such as “REVISE G2A BEFORE RESUMING” are
dated findings, now superseded by **G2A RETIRED — DO NOT RESUME**.

## Pre-deletion validation

The documentation and active-lineage audit passed these read-only checks:

- `python .\tools\Verify-Fable2NativeRendererG1.py`: all 11 G1 candidates
  validated (`confirmed=5`, `strong_hypothesis=4`, `weak_hypothesis=2`);
- `python .\tools\Verify-Fable2EntrypointClosure.py`: schema 3, analyser
  2.0.0, exact loaded-image identity, 35,626 candidates, 55 strong and 180
  probable additions, and all three fixtures passed;
- `python .\tools\Verify-Fable2GpuReference.py --sdk-root
  C:\Dev\rexglue-sdk-v0.10 --canary-root
  C:\Dev\Fable2NativeRendererResearch\xenia-canary`: G1.5A through G1.6B,
  Markdown links and the new retirement links passed with zero warnings;
- the same GPU-reference verifier with `--verify-g16b-artifacts`: passed with
  zero warnings;
- the same verifier with aggregate `--verify-artifacts`: failed only for the
  three previously documented, user-confirmed deleted historical logs
  `fable2-run-047.1.log`, `fable2-run-047.log` and `fable2-run-048.log` (three
  errors, zero warnings); none was recreated or substituted;
- deterministic checks verified every protected hash, the checkpoint parent
  and tree, both ancestry results, all 16 checkpoint paths, the empty
  base-to-active diff on those paths and absence of all G2A-specific active
  implementation patterns;
- `git diff --check` passed.

The GPU-reference verifier has an intentional phase-branch-name guard. Its
content and artifact checks were therefore run with this same documentation
worktree temporarily on the required G1.6B ref while both refs still named the
same starting commit, then the worktree was returned to the cleanup branch.
Neither branch tip changed.

## Branch deletion guardrails and result

Deletion is limited to the explicit local ref
`refs/heads/fable2-native-renderer-g2a-forwarding-proof`. It is authorized only
after all of the following are rechecked:

- the ref still names checkpoint
  `47c2ea2b7d9e14b09fd942c4b5f1bd11c46e2f51` and tree
  `910e80108c2d9e7d8474866506f1c9e23ede601c`;
- no worktree uses it;
- this retirement record and all permitted documentation changes are
  committed;
- the cleanup worktree is clean;
- local-branch and remote-tracking-ref inventories are recorded;
- no remote deletion or other destructive maintenance is involved.

**Deletion result: PENDING FINAL GUARDRAIL CHECK.** The post-deletion result is
recorded in a follow-up documentation commit only after the exact local ref is
deleted and all immediate verification passes.

The full checkpoint hash is recorded, and the commit object must remain
immediately readable after deletion. Once the only local ref is gone, the
checkpoint may remain recoverable temporarily by its hash and reflogs. It is
not a permanent backup: ordinary future Git maintenance may eventually prune
an unreachable object. No tag, archive, bundle, replacement branch or hidden
backup is created, and no garbage collection, prune or reflog expiration is
run.

## Repository and behavior boundary

Before the local-ref deletion, the cleanup branch contains documentation only.
Fable runtime source, build behavior, tests, fixtures, schemas, generated
source, manifest, packages, assets, executables and GPU DLLs are unchanged.
ReXGlue remains at commit/tree
`956c6a8b5da4c54b9899a2593e9c67c26de30194` /
`b78b06b8ac650467372236a3a262864e069a9382` with only its previously audited
`thirdparty/libmspack` materialization. Pinned Canary remains clean at
`3a44f20c7bc66db1da583e8a6f0ab740e31908e9` /
`c343b0a5796590fadc3b78c993bfada51e7e9148`.

No G2A code is resumed, salvaged, compiled, linked, executed, archived or
copied. No game build or execution, runtime change, push, merge, cherry-pick,
tag, release, remote-ref deletion, worktree deletion, garbage collection or
history rewrite is part of this retirement.
