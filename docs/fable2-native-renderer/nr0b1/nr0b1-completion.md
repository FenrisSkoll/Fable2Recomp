# NR0B-1 preparation closeout

Result: **PREPARED — USER RUN REQUIRED**, dated 2026-09-10.
EXP-CONFIG-CAP-001 reporting/preparation is delivered; its runtime evidence
gate remains open. No game process was started, so PID/start/end/exit, actual
loaded modules, adapter/capabilities/effective selections and scene confirmation
are null/unobserved. This is not a native-renderer seam or correctness result.

## Delivered and validated

The [gap table](effective-configuration.md) preceded implementation. Nine
default-off SDK stages now expose owning components' initialized state and
first output/present completion. The isolated preparation/launch/parser helpers
preserve the normal launch helper, use the accepted log allocator, refuse root
reuse, compare copies and artifacts, and monitor the actual process handle.
One new preserved Oakfield checkpoint and separate writable root match all 14
source files. Runtime files are separately staged; baseline EXE/DLLs and source
saves are unchanged. No installed SDK/baseline runtime replacement occurred.

Commands actually used (from the indicated canonical root):

```powershell
# SDK
cmake --build --preset win-amd64-release --target rexruntime rexgpu-xenos unit_tests
.\out\win-amd64\Release\unit_tests.exe "[gpu-config]"
git diff --check

# Fable
python tools/Fable2GpuConfig.py prepare --run-id nr0b1-oakfield-20260910-001
python tools/Fable2GpuConfig.py preflight --session out/nr0b1/sessions/nr0b1-oakfield-20260910-001
python -m unittest discover -s tests -p test_fable2_gpu_config.py
python -m unittest discover -s tests -p test_verify_fable2_gpu_reference.py
python -m unittest discover -s tests -p test_verify_fable2_native_renderer_nr0a.py
python -m py_compile tools/Fable2GpuConfig.py tests/test_fable2_gpu_config.py
python tools/Verify-Fable2NativeRendererG1.py
python tools/Verify-Fable2NativeRendererNR0A.py --verify-preserved-state
python tools/Verify-Fable2GpuReference.py --sdk-root C:\Dev\rexglue-sdk-v0.10 --canary-root C:\Dev\Fable2NativeRendererResearch\xenia-canary
python tools/Verify-Fable2GpuReference.py --sdk-root C:\Dev\rexglue-sdk-v0.10 --canary-root C:\Dev\Fable2NativeRendererResearch\xenia-canary --verify-artifacts
git diff --check
```

Results:

- Affected SDK Release build: PASS; existing compiler warnings remain. No Debug repair, dependency update, Fable build or install.
- SDK snapshot tests: PASS, 3 cases / 16 assertions (default off, failed report contained/once, bounds/escaping, unknown retained).
- Fable preparation/parser tests: PASS, 6 tests (existing destination/session refusal, source mismatch, partial/wrong-run/duplicate/missing fields, loaded hash mismatch and absent termination).
- Existing GPU-reference tests: PASS, 10. Existing NR0A tests: PASS, 7.
- Python compilation and PowerShell AST syntax check: PASS. The PowerShell game-launch/GUI-process path itself awaits the user run; syntax checking is not runtime validation.
- G1 verifier: PASS, 11 candidates (5 confirmed, 4 strong hypotheses, 2 weak hypotheses).
- NR0A immutable source/pin/link and preserved-state verifier: PASS, 10 pins / 44 source-symbol records / 69 local links / 19 immutable source links.
- Default G1.5/G1.6 GPU reference verifier after SDK commit: PASS, zero warnings.
- Strict historical-artifact verifier after SDK commit: expected FAIL, **7 errors / 0 warnings**, detailed below.
- Preparation preflight: PASS; source/preserved/writable inventories and all four baseline/staged artifact hashes match. Runtime base XEX/XEXP hashes match accepted inputs.
- New Markdown links, JSON metadata, SDK source blobs/symbols, output ignore policy, staged-path/hunk review and `git diff --check`: checked during final closeout. Raw outputs remain ignored under `out/nr0b1`; no game log has been allocated yet.

## Historical limitations and new failures

Strict verification still reports the missing historical logs
`fable2-run-047.1.log`, `fable2-run-047.log`, `fable2-run-048.log` and four
historical/current hash comparisons: the historical executable comparison,
the historical GPU artifact comparison and the repeated G1.6A/G1.6B GPU checks.
Actual unchanged baseline hashes are in [provenance](preparation-and-provenance.md).
No logs were recreated, historical hashes replaced, evidence substituted or
checks weakened. The strict output is `out/nr0b1/gpu-strict-final.log`.

An earlier pre-commit run also reported two SDK worktree-status failures
because the authorized reporting sources were uncommitted. These disappeared
after the reviewed SDK commit. They were new transient checks, not historical
exceptions. Current default output is `out/nr0b1/gpu-default-final.log`.
Optional/missing capabilities and runtime stage completeness remain untested
on the selected device until the user run; no defaults fill that gap.

## Local Git and documentation boundary

SDK branch `fable2-native-renderer-nr0b1-config-reporting`:

```text
06c4b7002a449ad4d173ec90c625e490ed03fe74
tree 5feea2389d0ce264ab970bf7807ee4ae6bd7960d
Add opt-in one-time effective GPU configuration reporting
```

Fable branch `fable2-native-renderer-nr0b1-preparation`, tooling commit:

```text
e2fd89acca684a7f4437d2bb510bd9d59ba25d6b
tree 7c2be7d08800529ab668c2977ce1c4d09a487c51
Prepare isolated GPU configuration sessions and process identity reports
```

The following documentation commit records that SDK/tool relationship and
prepared artifact identities. Its own ending HEAD/tree is reported in the
final response, not embedded recursively in this document. Both indexes end
empty; only the exact pre-existing manifest whitespace edit and SDK libmspack
materializations remain. No reference repository was changed.

Next action is precisely the [one-run card](user-run-card.md), followed by
review of process/configuration records and the short user scene/normal-exit
confirmation. Do not repeat completed preparation. If initialization fails,
preserve actual errors/artifacts and diagnose that failure without assuming
renderer correctness or authorizing another run. A healthy process is never
force-killed merely because reporting completed.

No native renderer, per-draw/per-packet/per-resource recorder, GPU payload
capture, screenshots/readbacks, guest hooks, G2A restoration, source-save
modification, baseline runtime replacement, gameplay automation, reference
edit or push occurred. NR0B-2 remains a [bounded handoff](nr0b2-handoff.md),
not an implementation started here.
