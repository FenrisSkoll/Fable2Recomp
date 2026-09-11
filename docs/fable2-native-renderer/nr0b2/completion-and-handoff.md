# Corrected recorder closeout and continuation

Result: **RECORDER CORRECTED — USER CAPTURE REQUIRED**.

Session 002 remains the authoritative failed runtime evidence: it accepted the
trigger, filled the 100,000-record capacity in 22.7001 ms, captured one boundary
and no complete interval. Its notification record could not establish when the
user saw ARMED, and its mutable status design lost the entire RECORDING state
between polls. The [diagnosis](session-002-diagnosis.md) and original binary,
reports, log, hashes and launch claim are unchanged.

The correction interns repeated decoded state through immutable definitions and
bounded per-decision bundles while retaining every admitted decision and
ordered operation/outcome edge. The session 002 event pattern projects to 24,785
events, 75.215% fewer. A dense synthetic fixture writes 26,816 events, retains
2,350 decisions and one-to-many relationships and reaches one complete interval
under the unchanged limits. This proves the corrected bounded representation in
the fixture only; runtime interval coverage is pending.

READY, STARTED and final STOPPED/CANCELLED/ERROR are immutable, sequence-numbered
transition records. READY follows successful shortcut registration. STARTED
uses the accepted-trigger time. STOPPED follows successful binary flush. The
launcher replays every unseen sequence even after delayed polling, and distinct
worker-only cues let the user keep game focus. The real run must still establish
that the user perceives those cues.

Implementation, focused validation, affected Release compilation, isolated
staging, checkpoint copying and configuration preflight are complete. Fresh
session 003 has no launch claim or capture directory. The
[run card](user-run-card.md) is the exact next action. No Fable process was
launched during correction or preparation.

## Resume after user operation

Use only:
`C:\Dev\Fable2Recomp\out\nr0b2\sessions\nr0b2-oakfield-20260911-003`.
Do not call prepare again, reuse sessions 001/002, delete a claim, allocate a
replacement run or overwrite an analyzer result.

After the user returns, read `process.json`, `preparation.json`, the immutable
files under `capture\transitions`, `capture\metadata.bin`, compatibility
`capture\status.txt`, `analysis.json` and the exact log recorded by
`process.json`. Verify PID/start/end/actual exit, loaded EXE/runtime/GPU paths and
hashes, transition order, output flush, configuration stages and preservation.
Correlate monotonic and wall time only through the recorded correlation pairs;
do not equate a cue or console-render time with its worker timestamp.

Report structural validity, complete/partial consumer intervals, resource/input
dependency completeness, functional gameplay, visual correctness and recorder
disturbance separately. Review all decision outcomes, wire/dictionary/reference
counts, terminal/loss status, state combinations, resolves, deferred/native/
submit/completion joins and open edges. A valid reference graph or normal
process exit does not make a capacity-limited or partial capture complete.

Consider at most one candidate under [remaining gates](candidate-and-gates.md).
If none qualifies, record the smallest missing observation rather than expanding
the experiment. No payload or translation proof begins in NR0B-2.

Both topic branches are `fable2-native-renderer-nr0b2-metadata`. Exact committed
source/build relationships are in
[implementation and validation](implementation-and-validation.md); final
documentation HEAD/tree values are reported externally. The pre-existing Fable
manifest whitespace edit and SDK libmspack materializations remain outside the
NR0B-2 commits.

ReXGlue retains all rendering/runtime ownership. No native draw replacement,
shader/resource payload capture, G2A restoration, guest hook, manifest/codegen
change, source-save change, baseline replacement, dependency update, merge,
push or history rewrite occurred. Stop after the fresh NR0B-2 capture; later
payload or native-renderer work requires its own bounded scope.
