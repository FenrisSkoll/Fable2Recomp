# NR0B-1 — effective configuration and capture preparation

**PREPARED — USER RUN REQUIRED** (2026-09-10).

One isolated Oakfield test is prepared. The optional SDK snapshot compiles in
Release and its focused tests pass. No game has been launched in this phase;
selected adapter/capabilities/paths, loaded-module identities, lazy extents and
actual exit remain **unobserved**. EXP-CONFIG-CAP-001 is not runtime-complete.

- [Preparation and provenance](preparation-and-provenance.md): inputs, source/build/staged identities, save/cache isolation.
- [Effective configuration](effective-configuration.md): reporting gap table, record contract and limitations.
- [User run card](user-run-card.md): exact isolated launch and the few required observations.
- [NR0B-2 handoff](nr0b2-handoff.md): source locations and bounded recorder dependencies; no events implemented.
- [Completion](nr0b1-completion.md): validation, preserved state and local Git boundary.
- [Preparation evidence](evidence/preparation-summary.json): reviewed metadata only; full private inventories remain ignored.

[NR0A's conditional architecture](../nr0a/architecture-decision.md) is unchanged.
ReXGlue retains ring/register state, memory tracking, shader translation, host
GPU resources, queues/fences, EDRAM/resolve, interrupts/vblank and presentation.
Window/input, host overlay composition/focus/completion, shutdown, saves, XAM,
audio and the remaining runtime services retain their existing owners.
No renderer seam is qualified by this preparation. G2A remains retired.
