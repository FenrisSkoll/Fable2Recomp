# Architectural risk register

Attribution: external source paths refer to
[`2bdf8f93a0edcec599023ce9382ca284a7e92c06`](https://github.com/himdo/Fable-2-Recomp/tree/2bdf8f93a0edcec599023ce9382ca284a7e92c06).
These patterns can accelerate practical exploration. This register describes
their engineering trade-offs, not the quality or intent of their authors.

| Pattern and concrete evidence | Why it helps short-term | Risk at scale | Canonical protection / guardrail |
| --- | --- | --- | --- |
| Address-specific register/return rewriting: seven `src/core/fable2_hooks.cpp` hooks | Tests a suspected gate or interval quickly | Changes downstream state and persistence; tightly coupled to revision and exact register liveness | No hooks imported. Require TU1 condition/data-flow proof and original behavior as acceptance criterion |
| Patch accretion: hooks plus `config/fable2_patches.toml` plus optional diagnostic overrides | Allows independent A/B experiments | Interactions obscure the earliest incorrect state; enabled defaults become an undocumented alternate game | Keep diagnostics default-off, narrow and removable; manifest/guest semantics remain unchanged |
| Post-codegen source patching: CMake invokes `tools/apply_recomp_patches.py` (currently empty list) | Changes output without waiting for generator support | Source anchors drift, partial patching and provenance loss; generated code stops being reproducible output | Regenerate normally; change generator only after generic cause established. Do not misreport empty patch list as active patches |
| Revision-coupled addresses/names: unpatched manifest vs TU1 | Direct addressing is easy to instrument | Same address may be unrelated code; plausible names silently migrate across versions | Hash both image and update; independent body/control/data-flow rebase; raw census remains REVISION_MISMATCH |
| Build-driven boundary trimming and imported switch labels | Satisfies codegen/build constraints, extends playability | Case blocks become callable functions, owners overlap, bounds disappear; runtime success cannot prove ownership | Existing owner/finite-domain/corroboration framework; no manual range/table import from this audit |
| Trigger-based semantics: Swimming/warehouse/first-fight thunk names | Useful bookmarks for reproduction | Generic virtual dispatch is mistaken for a subsystem or exclusive event handler | Preserve slot identity and external trigger as separate facts; reserve semantic names |
| Inferred menu state: draw-count/button latch in state/remote probes | Enables simple automation when state is unknown | Timing or presentation changes alter inferred state; false classification starts affecting runtime logic | Established deterministic input with observed milestones; never use host heuristic as replacement guest state |
| Diagnostics mutate semantics: heap/string replacement, suppressed calls, F5 invocation | Controlled experiments can localize causes and inspect live state | Tool becomes required for progress; altered heap, thread or GC state contaminates evidence | Separate observation from experiment; default-off budgets, no guest writes in provenance probe, no Lua executor added |
| Tool/runtime drift: launcher swaps source and prebuilt DLL pairs | Fast backend experimentation | Same executable filename hides different loader/renderer behavior and ABI/provenance | Installed SDK version pin, effective configuration, actual module hashes, fresh generated comparison. Current SDK source HEAD is not runtime identity |
| Incremental dependency gaps: canonical `codegen.d` omits XEXP | Fast no-op builds | A changed title delta may leave stale source; current correctness does not prove future invalidation | Fresh isolated reproduction passed. Dedicated XEXP/tool identity regression remains a follow-up; do not claim this guardrail already complete |
| Guest cadence conflated with host presentation: vsync-off/early wait proposals | Raises observed frame rate | Vblank counter users, animation, simulation, UI, audio and scheduler assumptions may change | Preserve original cadence; isolate host presentation research from guest timing and measure multiple clocks |
| SDK renderer diagnostic fork: gamma staging/readback, sentinel and retained temporary resources | Makes otherwise invisible GPU state inspectable | Overhead/leaks/synchronization changes can mask or cause defects; fork diverges without a generic abstraction | Existing bounded metadata/effective-config reports; minimal upstreamable fixes only after an independently reproduced cause |
| Fabricated allocation success: reverted AllocFixed experiment in menu-crash report | Removes repeated warnings and seems to advance initialization | Guest believes reservation succeeded, corrupting allocator structures later | Canonical already treats bounded retries as non-blocking; retain actual failure contract |
| Post-link PE rewriting: `tools/repro/clean_pe.py` | Produces consistent packaging fields and smaller export surface | Changes debug identity/exports after linking; reproducible-looking metadata can hide real binary differences | Hash final executable and PDB together; preserve native RIP→RVA→generated source mapping; no PE mutation imported |
| Completion claims replace structured coverage | A full playthrough finds many missing paths cheaply | Does not enumerate revision, saves, enabled overrides, untouched branches or parity | Human-led play remains valuable; preserve session/image/save/owner provenance and distinguish endpoint smoke from full-tranche replay |

The concrete inherited allocator lesson is particularly useful: the external
report associates forced reservation success with base path
`0x83231BE8 -> 0x832304E8`, faulting read through a small invalid pointer
(reported guest `0x0000001C`, LR `0x83231C3C`). Our exact body match at
`0x83236D60..0x83236DE0` corroborates the low-level routine shape, not the
external runtime crash. It does not justify reopening our established benign
fixed-address search observation without a new blocking failure.
