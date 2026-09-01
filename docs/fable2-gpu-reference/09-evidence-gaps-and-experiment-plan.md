# Evidence gaps and minimum experiment plan

## Decision

Do not run this backlog in G1.5D. The next primary gate is the static experiment `EXP-STATIC-XDK-001`. It asks whether a representative TU1 draw/resource/shader/target seam is recoverable before the project pays the cost and risk of runtime metadata.

The authoritative plan is [`experiment-backlog.json`](evidence/experiment-backlog.json). It specifies required fields, forbidden data, default-off/fail-open behavior, controls, user action, pass/fail/inconclusive criteria, rollback, dependencies, risk/privacy and estimated ladder level for every item.

## Dependency order

| Order | Experiment | Type | Question | Dependencies | Estimated level |
|---:|---|---|---|---|---|
| 1 | `EXP-STATIC-XDK-001` | STATIC | Can exact TU1 static analysis recover representative draw, resource, shader and render-target methods with a stable ABI, or is recovery currently blocked? | — | L1 |
| 2 | `EXP-G2A-LINK-001` | BUILD/ABI | Can a revised minimal sub_82BA34D8 wrapper link in the production Release binary and forward exactly once with disabled/enabled and recursion guards intact? | — | L1 |
| 3 | `EXP-CONFIG-CAP-001` | RUNTIME METADATA | What effective GPU configuration and D3D12 host capabilities apply to the exact active DLL and RTX 5080? | — | L1 |
| 4 | `EXP-SWAP-CORRELATION-001` | RUNTIME METADATA | How do TU1 sub_82BA34D8 calls relate to VdSwap, XE_SWAP, guest-output mailbox refresh and DXGI Present? | `EXP-G2A-LINK-001` | L2 |
| 5 | `EXP-DRAW-DECISION-001` | RUNTIME METADATA | For each bounded draw, did ReXGlue render, produce no effect, reject zero extent, wait/skip for a pending pipeline, or fail? | `EXP-STATIC-XDK-001`, `EXP-CONFIG-CAP-001` | L3 |
| 6 | `EXP-SHADER-IDENTITY-001` | RUNTIME METADATA | Which privacy-preserving shader and pipeline identities belong to affected draws, and do they contain candidate operation classes? | `EXP-DRAW-DECISION-001` | L3 |
| 7 | `EXP-VERTEX-FETCH-001` | RUNTIME METADATA | Do affected draws exercise VTX-001, VTX-002 or VTX-003? | `EXP-DRAW-DECISION-001`, `EXP-SHADER-IDENTITY-001` | L4 |
| 8 | `EXP-TEXTURE-METADATA-001` | RUNTIME METADATA | Do affected draws exercise TEX-002 through TEX-007, and which resource lifetime supplies each fetch? | `EXP-DRAW-DECISION-001`, `EXP-SHADER-IDENTITY-001`, `EXP-MEM-LIFECYCLE-001` | L4 |
| 9 | `EXP-EDRAM-RESOLVE-001` | RUNTIME METADATA | Do affected passes exercise RT-002 through RT-005 and how are their results consumed? | `EXP-DRAW-DECISION-001` | L4 |
| 10 | `EXP-ZPD-REPORT-001` | RUNTIME METADATA | Does Fable use EVENT_WRITE_ZPD in the scene and does any report span submissions or reuse a slot before retirement? | `EXP-DRAW-DECISION-001` | L3 |
| 11 | `EXP-REGISTER-RESET-001` | RUNTIME METADATA | Does TU1 read any Canary-seeded reset register before its first write, and does an affected draw consume it? | `EXP-DRAW-DECISION-001` | L3 |
| 12 | `EXP-MEM-LIFECYCLE-001` | RUNTIME METADATA | Do affected resource ranges undergo unwatched decommit/release/protect-to-writable transitions before GPU cache consumption? | `EXP-DRAW-DECISION-001` | L4 |
| 13 | `EXP-CHARACTER-PAIR-001` | USER CHECKPOINT | Can capture-off and capture-on runs reproduce the same affected character/dog scene without observable perturbation and join affected draws/resources? | `EXP-DRAW-DECISION-001`, `EXP-SHADER-IDENTITY-001`, `EXP-TEXTURE-METADATA-001`, `EXP-EDRAM-RESOLVE-001` | L4 |
| 14 | `EXP-CANDIDATE-AB-001` | CONTROLLED A/B | Does one L4-qualified divergent behavior cause or clear the observed black surfaces? | `EXP-CHARACTER-PAIR-001` | L5 |
| 15 | `EXP-KEYBOARD-UI-001` | USER CHECKPOINT | Does the naturally reached Fable keyboard flow preserve focus, async completion, z-order, repaint, resize and cancellation? | — | L1 |
| 16 | `EXP-ACHIEVEMENT-UI-001` | USER CHECKPOINT | Does a naturally earned Fable achievement preserve guest write routing, persistence/event delivery, toast queue, z-order and shutdown? | — | L1 |

Ordering is a design constraint, not authorization. Items with no dependency may be scheduled independently only in a later phase.

## First gate: static method recovery

`EXP-STATIC-XDK-001` is complete if either:

- at least one representative TU1 method has exact boundary, ABI, threading, ownership, side effects and operation meaning; or
- static recovery is reproducibly blocked and the exact blocker is recorded.

A function name, renderer label, string, broad call graph or similarity to another title is not a pass. This gate decides whether the high-semantic route is viable and whether low-level correlation should become primary.

## Separate mechanism gate

`EXP-G2A-LINK-001` is independent. It proves or rejects the revised minimal `sub_82BA34D8` wrapper in a linked Release production binary. It must retain the distinct original body and exact-once fixtures while removing or deferring generalized capture infrastructure.

This experiment remains L1. A safe present wrapper is not a draw diagnostic.

## Smallest later runtime chain

If later authorized, evidence collection should expand only when the preceding record selects it:

1. `EXP-CONFIG-CAP-001` freezes effective settings and RTX 5080 capability inputs.
2. `EXP-DRAW-DECISION-001` emits one terminal outcome for each bounded draw.
3. `EXP-SHADER-IDENTITY-001` attaches hashes and analysis flags only.
4. Select one or more of vertex, texture, EDRAM, ZPD, register or memory-lifecycle metadata based on those affected draw IDs.
5. `EXP-CHARACTER-PAIR-001` validates capture transparency and joins the affected L4 set.
6. Only then may `EXP-CANDIDATE-AB-001` change one qualified behavior to seek L5.

Swap correlation is optional for presentation/frame identity and does not precede draw diagnosis unless the selected schema needs a frame key.

## Data minimization

All runtime items prefer identifiers, enums, bitsets, ranges, generations and hashes. They forbid:

- shader bodies, disassembly and translated shader output;
- textures, render targets, depth, EDRAM, vertex/index buffers or other payloads;
- broad packet/register/memory dumps;
- XEX/XEXP bytes, saves or assets;
- keyboard text, keystrokes, profile data and unrelated paths;
- new screenshots except under separate explicit user authorization.

Every future record must live beneath a per-run directory under `out/gpu-evidence-runs`, after `git check-ignore -v` proves the exact path is ignored. A later phase must check bounded size/file count and repository status before and after. This document does not create that directory.

## Candidate-specific stop conditions

- `REG-001`: stop after the finite seeded-register set is classified first-read/first-write; do not trace all registers.
- `DRW-002`: stop after ZPD slot/submission/retirement/reuse is classified; do not capture query results.
- `VTX-001..003`: stop once topology, bounds mask and XPS address class are known for affected draws.
- `TEX-002..007`: stop once every predicate is computable from fetch/layout/validity metadata; never dump a texture.
- `RT-002..005`: stop once `ResolveInfo`, pass/alias, format, range and consumer joins are complete; never dump a surface.
- `SHD-002`: stop at hash, operation-class flags and value classification; do not persist microcode.
- `PIP-002`: stop at effective async setting, readiness and exact terminal draw outcome.
- `PIP-003`: stop at capability plus affected blend registers/values.
- `MEM-002`: stop at mapping/watch/invalidation generation and next hashed consumer.

A candidate that is not reachable in the affected bounded set is cleared only for that set; it is not globally disproved.

## User checkpoints

The user remains in control of every gameplay action.

`EXP-CHARACTER-PAIR-001` defines a two-run checkpoint: the same existing TU1 save, shortest route to the exact Run 047 character/dog viewpoint, stationary matching camera for five seconds, then exit; capture-off first and capture-on second. It is not “play around.”

Keyboard and achievement validation are separate and later. The keyboard experiment waits for the natural naming flow and forbids text/keystroke recording. The achievement experiment cannot be scheduled until the user names a natural, not-yet-unlocked checkpoint; it may not manufacture an unlock or require grinding.

## Controls and rollback

Every runtime-metadata experiment is default-off and fail-open. A record failure drops metadata, never rendering or guest completion. Each has an identical capture-off control. Rollback disables its single switch and removes only its exact verified ignored directory.

The controlled A/B is intentionally higher risk: A is the unchanged oracle, B changes exactly one L4-qualified behavior, and both use identical artifact lineage, configuration, save and checkpoint. A multi-fix patch is an automatic failure.

## Decisions unlocked

The backlog is optimized for decision value:

- static method recovery selects the semantic seam strategy;
- linked G2A proof settles mechanism only;
- draw decisions select the smallest resource evidence;
- L4 joins identify the affected character path;
- a single controlled A/B can establish or clear causal relevance at L5;
- natural UI checkpoints validate presenter compatibility independently of renderer defect work.
