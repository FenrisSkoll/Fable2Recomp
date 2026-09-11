# NR0B-2 — bounded GPU metadata

**RECORDER CORRECTED — USER CAPTURE REQUIRED.** Session 002 remains a preserved
capacity-limited capture. The corrected recorder and durable READY, STARTED and
STOPPED notification path are staged in fresh session 003; it has passed
preflight and has never been launched. ReXGlue remains the sole renderer.

- [Reading and provenance](reading-and-provenance.md): accepted NR0B-1 lineage, source evidence and protected checkpoint.
- [Recorder design](recorder-design.md) and [event contract](event-contract.md): compact immutable state, consumer ordering, explicit outcomes, durable transitions, bounds and limitations.
- [Session 002 diagnosis](session-002-diagnosis.md): preserved failure evidence and the two independent demonstrated causes.
- [Implementation and validation](implementation-and-validation.md): measured density reduction, focused tests, Release build, staged identities and preservation results.
- [User run card](user-run-card.md): fresh one-use session 003, exact launch, cues, trigger/cancel and normal exit.
- [Candidate and remaining gates](candidate-and-gates.md): no selection before actual capture; later dependencies remain separate.
- [Completion and continuation](completion-and-handoff.md): use existing preparation after the user returns; do not recreate the session.

Original [NR0B-1 evidence](../nr0b1/README.md) and session 002 evidence remain
unchanged. Configuration verification is accepted; this phase observes existing
rendering and does not implement a native renderer, visual fix, payload capture
or live switching.
