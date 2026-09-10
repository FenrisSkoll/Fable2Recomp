# NR0B-2 — bounded GPU metadata

**RECORDER PREPARED — USER CAPTURE REQUIRED.** No Fable process has been
launched for NR0B-2. No runtime draw, shader pair, resource combination or
candidate workload has yet been observed. ReXGlue remains the sole renderer.

- [Reading and provenance](reading-and-provenance.md): accepted NR0B-1 lineage, source evidence and protected checkpoint.
- [Recorder design](recorder-design.md) and [event contract](event-contract.md): consumer ordering, explicit outcomes, used bindings, native invocation/submission joins, bounds and limitations.
- [Implementation and validation](implementation-and-validation.md): focused tests, Release build, staged identities, regression/preservation results.
- [User run card](user-run-card.md): the prepared one-use session, exact launch, trigger/cancel and normal exit.
- [Candidate and remaining gates](candidate-and-gates.md): no selection before actual capture; later dependencies remain separate.
- [Completion and continuation](completion-and-handoff.md): use existing preparation after the user returns; do not recreate the session.

Original [NR0B-1 evidence](../nr0b1/README.md) remains unchanged. Configuration
verification is accepted; this phase observes existing rendering and does not
implement a native renderer, visual fix, payload capture or live switching.
