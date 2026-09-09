# Implementation gates after NR0A

This roadmap is conditional and does not authorize its steps. Current accepted
ReXGlue rendering stays the default. Each phase needs an explicit scope and
reviewable acceptance record; discovering a shader or a function address does
not satisfy the next gate automatically.

| Gate | Dependency and bounded action | Required acceptance | Stop / unresolved result |
|---|---|---|---|
| NR0B — effective configuration and frame contract | Authorize the [evidence plan](nr0b-evidence-plan.md); first configuration snapshot, then one short user-operated native-save capture | Exact loaded identities and capabilities; complete bounded draw/state/resolve/submission map with explicit unknowns and measured collection limits; choose at most one real workload | No complete interval or unclosed dependencies means narrower evidence follow-up; no renderer implementation based on missing fields |
| Selection/lifecycle skeleton | After NR0B identifies a plausible integration boundary, separately authorize a small default-off startup selector and isolated lifecycle prototype | Default path preserves accepted behavior; native selection occurs before GPU work; ownership, resize, fences, UI completion/focus, close and device-loss failure reporting are explicit; no unsafe competing owners | If canonical interfaces cannot lend output/device safely, keep a separate process/device prototype; do not silently import Skate's SDK fork |
| Shader/resource translation proof | After the metadata census, separately authorize bounded payload capture or another legitimate exact input source for the one selected workload | Original shader identity/features, constants and bindings; known layout/endian/swizzle/format/sample behavior; independent decode cases and meaningful numerical/output checks; explicit rejection of unsupported inputs; retired resources survive completion | Missing shader feature or GPU-produced initial resource prevents claiming proof. Hash-only records are insufficient. No hand-authored approximation promoted to parity |
| First independently testable native workload | Translation proof plus closed inputs/outputs for one real Fable indexed/textured draw, or a minimal complete pass if that is the actual bounded unit | Isolated replay or separate-run rendering executes the original workload semantics; documents initial color/depth inputs, draw state, output and consumer requirements; validation references and tolerances declared before judging output | If only a draw is closed, qualify only that draw, not its enclosing pass. If inputs remain live/mutable or feedback unclear, keep collecting evidence |
| Production selectable integration | Workload proof plus a separately reviewed ownership interface and sufficient coverage for the selected mode | Explicit guest completion/interrupt/vblank/query/resource-write compatibility; one presenter/device contract; default-off startup selection; failure before submission may select baseline, failure after submission ends native run safely | No automatic same-frame rollback, hot switch, partial pass mixing or positive-query substitution without independent proof |
| Parity expansion | Add one proved family/pass at a time and expand the test matrix only as required | Ordinary materials/textures, depth/shadows, transparency, resolves, UI/video and resource lifetime covered in representative scenarios; keep functional, visual and performance results separate | Missing families stay unsupported or require a whole-run baseline mode; do not conceal them with a “native” label |

The lifecycle skeleton may use clear/present as a synthetic test. That validates
device, resize, synchronization and output lifetime only. Displaying a copy of
ReXGlue's completed frame validates presentation integration only. Neither is
the first native replacement of Fable rendering and neither qualifies material
or shader fidelity.

The first rendering workload is intentionally not assigned a guest address in
NR0A. SXDK-001 is a fetch setter, not a complete workload; the presentation
cluster does not establish ordinary material coverage. NR0B must supply the
actual shader pair, resource spans/generations, attachment state, required
initial contents, output and downstream consumers before selection. Prefer an
isolated ordinary draw over a live pass whose consumers are unknown.

For a live pass replacement, prove all inputs, outputs, aliases, CPU/GPU writes,
queries, resolve destinations, fence/order edges and subsequent readers. A
separate image that looks right is not evidence that the game's later passes
receive correct data. If this dossier cannot be closed, use replay/separate
runs. No composable incremental dual-renderer handoff has been established.

## Three separate validation gates

**Visual equivalence:** compare the selected workload against original hardware
when available, or a known-correct observation with exact provenance. Current
ReXGlue is a regression baseline; Canary is a comparative implementation. A
matching bug in both does not prove fidelity. Use declared tolerances for
numerical/AA differences and identify temporal variability. Keep the black
dog/player issue unproved until causal evidence identifies its shader/resource/
configuration origin.

**Functional compatibility:** validate guest-visible results and dependencies,
including resolves/readbacks, queries, completion/fences, resize, input/UI focus
and orderly failure. A visually correct frame does not demonstrate these.
For standalone replay, guest-runtime compatibility is NOT APPLICABLE and remains
an explicit later gate rather than a silently passed one.

**Performance:** measure separately after correctness evidence. Report adapter,
driver, effective configuration, cache/warmup, capture disturbance, CPU/GPU time
and pacing method. No numerical effort estimate, speed guarantee or parity
claim is derived from another title's README.

## Future requirements retained outside initial parity

Resolution scaling and ultrawide need target sizes, projection/aspect, viewport,
screen-space effects and UI layout policies. Improved AA/filtering changes need
coverage and sampling correctness first. Temporal upscaling needs motion/depth,
jitter, exposure/masks where required, history lifetime/reset and appropriate
quality references; it cannot be bolted on merely by choosing D3D12.

Unlocked rendering framerate must be separated from game simulation timing.
Proving a renderer can present more frames does not prove animation, physics,
scripts or input are timing-independent. None of these enhancements is part of
NR0A, NR0B metadata collection or the first vanilla workload acceptance.
