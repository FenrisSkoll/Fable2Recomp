# Follow-ups by objective category

These are bounded investigation tasks, not authorization to import external
code. All external evidence is pinned in [the lead ledger](external-leads.json).
No follow-up requires replaying the entire audit.

## Correctness prerequisites

**CP-1 — CLOSED: title-delta and tool invalidation.** `PROV-03`; the isolated
valid-XEXP mutation reproduced stale reuse. The generic SDK dependency/cache fix
now tracks patches, optional-file existence and actual tool/runtime identity.
Changed-input and unchanged-input controls pass, and all 591 canonical generated
files remain byte-identical. See the [closeout](xexp-invalidation-closeout.md)
for evidence, local commits, the CLI-only installed update and coverage limits.

**CP-2 — Recover external mismatch witnesses, only if investigating its cause.**
`PROV-01`; request exact generated file at base `0x8233AE50`, producing CLI and
runtime DLL hashes/builds, source XEX hash and pre-write runtime capture. Decode
the three disputed instructions independently. Without these, keep the external
diagnosis unresolved. Our pipeline already passes its own check; this is not a
blocker for canonical work.

**CP-3 — Preserve subsystem timing contracts.** `TIM-01/02`; model TU1
`0x82BA2F68 -> 0x821F6050 -> 0x82BA2DB8`, packed interval bits and device
`+0x40AC`, together with SDK vblank counter and WAIT_REG_MEM. Observe guest
ticks, vblank, guest swaps and host presentation separately at vanilla settings.
Any later higher-FPS proposal needs animation, physics, UI, audio, streaming and
scheduler evidence; r11=1, early waits and 120 Hz guest-vblank forcing are not
acceptable substitutes.

## Coverage improvement

**CV-1 — Residual switch hints.** `CTR-01/02`; start with the 139 hints lacking
an already recovered relative-shape candidate, including 126 outside the
bounded unique-bctr scan. This is a review population, not a missing-function
count. Recover the base dispatch/table boundary, semantically rebase to TU1,
then intersect the 710 distinct unresolved CTR addresses. Require canonical
finite-domain, table-entry and owner proofs. Close only a demonstrated gap;
never register cases as functions. Keep the duplicate report record at
`0x8305DA44` visible when counting results.

**CV-2 — Named candidates with real evidence.** Use the 1,368 reciprocal-unique
body candidates as a search index, prioritizing external string/RTTI/call evidence
over generic `ProcessAndProcess` labels. Keep every unreviewed row marked
REVISION_MISMATCH. Validate any new indirect leaf/thunk with current boundary,
ownership and corroboration tools before adding a manifest line. No candidate
from this audit currently warrants such an addition.

**CV-3 — Later-game coverage.** `FEAT-01`; human operator chooses later-game
saves/progression. Preserve exact image/update/save identity and disabled
behavioral overrides. Use the existing coverage contract, bounded native
validation and Xenia reference where equivalent. External campaign success
suggests useful scenarios; it does not supply a correctness baseline or authorize
autonomous gameplay.

**CV-4 — Entitlement semantics.** `GATE-01/02`; trace actual TU1 flag producers
for byte `+0x90`, halfword `+0x40`, word `+0x28`, and keys `0xF0/0x39` only when
the content question is relevant. Recover owning objects, grant status and save
persistence before naming fields or diagnosing missing content. Do not force
gates or grant returns.

## Renderer investigation

**RI-1 — Hero/dog surfaces.** `GPU-03`; continue existing NR0B capture plan with
the validated effective configuration. Record textures/fetches, shaders, render
targets and resolved/presented surfaces for hero/dog and a working comparison.
The external symptom is corroboration, not a gamma/MSAA/texture-morphing cause.

**RI-2 — Vulkan gamma/presentation.** `GPU-02`; if Vulkan becomes an explicit
target, reproduce on a pinned adapter/driver/runtime pair. Separate memory
type/coherency, flush/invalidate, image transitions, submission and presentation.
Require a minimal failing test before changing allocations. Do not import
sentinels, forced waits, detached probes or retained command-buffer leaks.

**RI-3 — Text callbacks.** `UI-01/02`; inspect candidate
`0x82C4B118/0x82C4AF78` and existing iterator `0x82190728` with TU1 callbacks,
strings and glyph/texture references. Acceptance is a bounded role relationship,
not adoption of external `UIText_*` names from apparent screen effects.

## Tooling enhancement

**TE-1 — Default-off function frequency summaries.** `DBG-01`; only add if a
specific question is not answered by existing indirect traces, GPU metadata or
fault diagnostics. Design bounded counters with explicit sampling/output limits,
thread identity and measured disabled/enabled overhead. Calls are not frames.

**TE-2 — Lua inspection safety.** `LUA-01/02`, `DBG-03`; static registration now
identifies method `0x82459928`, adapter `0x8254B670`, self/method payload offsets
0/4 and RunScript string `0x820B7424`. Investigate owner-thread scheduling,
lifetime, string ownership, reentrancy and GC before an interactive tool. The
external first-`.lua` heuristic is unnecessary for identity and insufficient for
safety. Lua execution is a state-changing diagnostic experiment even when used
to display position.

**TE-3 — Frozen test envelopes.** Keep historical Phase 2E–2H guards intact.
If a current unified test command is desired, define descendant-safe tests and
explicit archival replay commands without altering old witness manifests or
calling excluded tests passed. The audit's validation receipt distinguishes the
350-test current subset from failed full discovery.

## Quality-of-life features, after vanilla stability

Host Lua UI, keyboard-aware prompts, new mappings, high FPS, resolution,
widescreen and platform expansion remain separate product work. Prefer existing
ReXGlue input/presentation APIs. None is a prerequisite for accepting the
verified archaeology in this audit.

## Durable checkpoint

Canonical path: original TU1 manifest/owners → installed `.51` loader → identical
load-time image and deterministic regenerated source → existing native gameplay
baseline. No canonical codegen/runtime byte discrepancy was found. The original
incremental XEXP dependency omission is corrected by CP-1's generic SDK fix;
the `.51` runtime is retained with the documented `.65` codegen CLI. External mismatch cause,
content labels and timing safety remain unresolved. No temporary instrumentation
is present in the game or SDK. The isolated probe exists only under
`tools/xex-provenance`; private runs are in `out/comparative-audit`.

CP-1's isolated delta-only invalidation test and generic correction are complete.
Existing renderer capture and human progression plans remain the appropriate
runtime next steps. Historical reports, prototype gates and SDK dirty files
remain untouched.
