# Conditional architecture decision

**CONDITIONAL ARCHITECTURE — DYNAMIC EVIDENCE REQUIRED.** Prefer a
Fable-specific adapter that recovers rendering intent and the state consumed
by each submission, backed initially by a small D3D12 implementation. Develop
it through isolated workloads and separate comparison runs with ReXGlue. This
selects an investigative direction and an ownership discipline, not a qualified
Fable hook or permission to implement it.

Option D is the development strategy; Option A is the preferred eventual
boundary. A sufficiently complete Option B remains a credible alternative.
NR0B must decide whether title intent can be correlated to real draws and
whether a bounded workload has recoverable inputs and lifetimes. No current
guest address is selected as the production adapter.

## What the Fable evidence actually establishes

The [G1.6B record](../../fable2-gpu-reference/13-static-xdk-seam-coverage.md)
qualifies SXDK-001 as a narrow operation:
`sub_82BA77D0 [0x82BA77D0,0x82BA7894)`, size `0xC4`. It emits six fetch
dwords with PM4 header `0xC0062D00 | device[0x31AC]` and selector
`0x00010000 | ((slot * 6) & 0x7FF)`. Inputs are device in r3, slot in r4,
borrowed descriptor in r5. Copying the descriptor into PM4 does not retain the
resource to which it refers. Device offsets `+0x30` and `+0x38` participate in
command cursor/capacity handling.

The two recovered direct callers are `sub_82BA7B28 @ 0x82BA81CC` and
`sub_82BA83C0 @ 0x82BA85D8`. Their copy/scale/present cluster does not establish
ordinary material coverage. The direct-fetch path through
`sub_82BA34D8 @ 0x82BA36CC -> sub_82BAD028 @ 0x82BAD100 -> sub_82BAC718`
bypasses this setter; `sub_82BAC718 [0x82BAC718,0x82BAD028)` emits a draw at
`0x82BACD94`.

Six recovered state-to-draw segments through `sub_8221B010` also bypass it:

| Root | State call | Draw call |
|---|---|---|
| `sub_8221C3E8` | `0x8221C470` | `0x8221C6B4` |
| `sub_82217DB8` | `0x82217E9C` | `0x8221819C` |
| `sub_82205F68` | `0x82206034` | `0x822062E8` |
| `sub_82207AF8` | `0x82207C68` | `0x82207F20` |
| `sub_8221C898` | `0x8221C984` | `0x8221CBA8` |
| `sub_8221DFC0` | `0x8221E04C` | `0x8221E2FC` |

This is static TU1/control-flow evidence, not runtime observation of six
materials. `sub_82AAC208 [0x82AAC208,0x82AAC54C)` remains a discovery lead.
`sub_82BA34D8 [0x82BA34D8,0x82BA3BFC)` remains a presentation/forwarding
correlation boundary. Neither provides a proved scene graph, material identity
or ownership handoff. Descriptor, PM4 storage, guest backing, host cache and
submission-retirement lifetimes remain distinct.

## Options

The table is a **BOUNDED INFERENCE** from the accepted evidence and the
[implemented references](reference-implementation-audit.md), not an effort
estimate. No completion date or numerical cost is inferred.

| Criterion | A — title-level replacement | B — broad static XDK/API replacement | C — command-stream backend | D — observation plus isolated replacement development |
|---|---|---|---|---|
| Fable evidence / missing coverage | Title submission candidates exist; semantic structures and ordinary draw associations unqualified | One narrow setter qualified; six bypasses defeat single-setter coverage; full method families missing | Existing ReXGlue already consumes actual PM4; no title semantics needed for decoding | Existing renderer supplies observation points; observer and joins still need separate implementation |
| Shader/material access | Best potential access to material/camera/skin intent; no proved Fable mapping | Shader binds/constants accessible if full method contract recovered; named materials optional | Microcode/constants/fetch available; material purpose usually absent | First identify feature/state census; defer claims of semantic mapping |
| Resource/lifetime recovery | Must bridge title object lifetime to mutable guest backing and completed host work | Must recover create/destroy/lock/alias/coherency across all used methods | Must preserve shared memory, page invalidation, EDRAM and memexport semantics | Metadata can expose missing generation edges before any replacement owns resources |
| Ownership complexity | Large eventual change; can start with independent replay | Device-wide replacement with compatibility duties, as in Unleashed | Full emulated GPU execution contract; duplicate work unless reusing SDK internals | Low initial interference if read-only; does not by itself solve production handoff |
| ReXGlue reuse | Runtime/window/UI and suitable decode/format services retained | Runtime retained; GPU/kernel completion bridge must be defined | Maximum reuse if modifying existing backend, least if rewriting it | Retain all current rendering responsibilities during observation |
| Portability | Isolate title adapter from backend resource/pipeline API | Host abstraction can be portable; guest device contract stays title-specific | Xenos execution semantics must work on every host backend | Separate runs/replay isolate backend comparison |
| Testing/failure isolation | Replay a bounded draw/pass; reject incomplete dependencies | Full API coverage difficult to validate incrementally inside live game | Compare packet semantics, resolves and synchronization; high regression exposure | Start with one scene; failure does not imply switching a partially submitted frame |
| Temporal inputs | Potential access to transforms, camera and object history; still unproved | May reconstruct from constants; correspondence/history still needed | No automatic motion/object history just because state is decoded | Evidence must first locate actual usable temporal signals |
| Engineering risk | High semantic recovery risk; clean long-term ownership if qualified | High coverage/ABI and resource alias risk | High correctness/maintenance risk of a second general GPU translator | Best containment strategy, but not an independent production renderer architecture |

Retaining PM4/register/Xenos shader/EDRAM execution in C remains **GPU
emulation/translation**, even with native D3D12 calls or a new intermediate
representation. It is not title-level replacement merely because the CPU is
recompiled. The current runtime already has that execution path. A second
command-stream implementation needs a demonstrated architectural benefit.

Skate makes A plus lower-level state observations a concrete precedent. Its
title hooks, hand-ported material families and selective suppression are major
prerequisites, not a drop-in seam. Unleashed makes B concrete: a wide static API
and resource contract can preserve guest pass decisions without reconstructing
an entire named scene graph. Neither establishes Fable's coverage.

### Evidence that could change the recommendation

Choose B over A if actual draw/resolve work maps to a tractable, complete set of
static API methods with proved resource and synchronization contracts, while
title structure recovery adds no needed information. Do not require named
meshes/lights merely for architectural elegance.

Defer A if consumer metadata cannot be joined to title submissions without
intrusive or unreliable correlation. Consider C only if higher boundaries are
demonstrably unsuitable and maintaining Xenos semantics through existing SDK
facilities is the defensible requirement. A missing convenient hook alone does
not qualify that escalation. If no bounded workload's dependencies close, the
next step is more narrowly targeted evidence, not a larger renderer skeleton.

## Backend decision

**Conditional recommendation: D3D12 first with a small internal interface.**
The validated project host is Windows AMD64/D3D12; the canonical runtime already
owns a D3D12 provider/presenter and established debugging points. NR0A adds no
dependency and creates no RHI. This decision should be revisited at the
lifecycle gate if the required owner/device integration cannot be made small.

| Choice | Assessment | Decision gate |
|---|---|---|
| D3D12 first | Mature host API and matches accepted host path; avoids immediately integrating another device/swapchain stack. Explicit transitions, UAV/alias barriers, command allocator reuse and fence retirement remain our responsibility. PIX/debug-layer/GPU validation can inspect future prototypes. | Prove exclusive device/queue/output ownership, required resource/format support and shader binding contract. An independently owned replay device is simpler than borrowing undocumented live internals. |
| Plume | Implemented D3D12/Vulkan/Metal abstractions and queues/barriers/resources; MIT root, separately pinned dependencies. Reduces future backend duplication, but its own README does not claim a stable production API. No Fable or canonical ReXGlue adapter exists. It still needs shader compilation and all guest semantics. | Show a smaller integration/maintenance burden than the small D3D12 boundary, including external-device/presenter support or a separately owned device. Assess barrier behavior at the actual chosen pin; Unleashed uses an older pin. |
| Existing SDK/project abstractions | Reuse ReXGlue memory, texture format/layout utilities, shader analysis and window/UI/presenter contracts where suitable. The raw plugin ABI and `IGraphicsSystem` are GPU-runtime integration interfaces, not a high-semantic RHI. Canonical SDK has no Skate native-output callback. | Review concrete public access and lifetime contracts before borrowing device/command objects. Do not fork/duplicate facilities to avoid that review. Existing DXBC translator output depends on shared memory, system constants and output-merger conventions; it is not automatically a standalone shader. |

D3D12 applications are responsible for resource-state/alias synchronization;
validation catches only a subset of mistakes. See Microsoft's
[resource barrier contract](https://learn.microsoft.com/en-us/windows/win32/direct3d12/using-resource-barriers-to-synchronize-resource-states-in-direct3d-12).
[PIX](https://devblogs.microsoft.com/pix/introduction/) is a future debugging and
capture option, not a capture performed here.

The small interface should eventually describe owned resources, views, pipeline
inputs, barriers, command recording, completion and output images. Keep Fable
addresses/material identities outside backend types. Avoid storing D3D12
descriptor handles as permanent title identifiers. Preserve format, subresource,
alias and queue semantics explicitly so a later Vulkan implementation is
possible. Do not design or implement simultaneous backends now.

Shader choice remains gated: investigate reuse of original microcode translation
before hand-reconstructing Fable materials. XenosRecomp coverage is not assumed;
ReXGlue's translator also carries runtime binding assumptions. A supported,
bounded shader pair must prove constants, fetch semantics, specialization and
numeric behavior against evidence. Skate's approximations do not satisfy the
initial vanilla-parity goal merely because they look plausible.

Temporal upscaling is not a backend-selection shortcut. Any future integration
needs correctly scaled color/depth, motion in a specified space, jitter,
exposure where required, masks, frame time and history reset/disocclusion policy.
Neither D3D12 nor Plume supplies Fable's temporal inputs. A vendor SDK would
require its own capability/license/dependency decision.

## Compact claim ledger

| Claim | Classification | Exact evidence | Consequence for Fable | Remaining unknown |
|---|---|---|---|---|
| SXDK-001 emits a texture-fetch operation, not a broad renderer seam | SOURCE-CONFIRMED (inherited static) | [G1.6A](../../fable2-gpu-reference/12-static-xdk-method-recovery.md), [G1.6B JSON](../../fable2-gpu-reference/evidence/static-xdk-seam-coverage.json), `sub_82BA77D0` | Do not build renderer coverage on it | Runtime frequency and named material association |
| Six recovered general state/draw paths bypass SXDK-001 | SOURCE-CONFIRMED (static paths); “general” purpose remains inherited bounded interpretation | G1.6B JSON `sub_8221B010` path records, addresses above | Broader contract needed | Runtime scene coverage |
| Presentation and async candidate are not semantic renderer interfaces | SOURCE-CONFIRMED boundary; UNRESOLVED semantic coverage | [Boundary assessment](../../fable2-gpu-reference/evidence/boundary-assessment.json), `sub_82BA34D8`, `sub_82AAC208` | No convenient-address promotion | Submission/object ABI and producer correlation |
| Current ReXGlue owns emulated GPU execution and host composition | SOURCE-CONFIRMED | Catalog SDK `IssueDraw`, `EndSubmission`, `SetupGuestGpu`, `RefreshGuestOutput`, `PaintAndPresentImpl` | One owner per mutable state; reuse runtime | Native interface and completion bridge |
| Accepted Fable rendering has executed | RUNTIME-CONFIRMED at inherited broad L1 level only | [G1.5D relevance](../../fable2-gpu-reference/06-fable2-relevance-assessment.md) and identified historical run references | Baseline exists | Deleted historical logs cannot be independently rehashed; no per-draw L2-L4 proof |
| Current Oakfield endpoint works for basic interaction | PROJECT-REPORTED, with accepted testing artifacts | [Phase 5A closeout](../../fable2-discovery-pipeline/09-phase5a-tranche-001.md) | One practical checkpoint for new capture | Current save availability, exact visual workload |
| Skate reconstructs a native scene and supports mode toggling | SOURCE-CONFIRMED implementation | Catalog Skate `BuildFrameScene`, `RenderScene`, `ToggleSceneEnabled`; fork `TryRenderNativeGuestOutput` | Useful A/hybrid precedent | Fable structures and safe switch semantics |
| Skate provides a portable, rollback-safe dual renderer | UNRESOLVED; not established by inspected implementation | Fork `ShouldSuppressEmulatedDraws`, `IssueSwap`; audit ownership section | Do not promise hot switch or partial-submit fallback | Suppressed-work restoration and ownership transaction |
| Unleashed replaces broad static graphics APIs | SOURCE-CONFIRMED | `UnleashedRecomp/gpu/video.cpp`: `CreateDevice`, `CreateShader`, `g_renderThread`, `Video::Present` at catalog pin | B is feasible in another title | Fable method/resource coverage |
| PGR4 native renderer is planned, absent from inspected public tree | PROJECT-REPORTED plan; SOURCE-CONFIRMED tree inspection | PGR4 pinned `Future-plans.md`, `Status.md`, `CMakeLists.txt` | Not an implemented precedent | Private/other-revision work outside audit |
| A plus D and D3D12 first fit current evidence | BOUNDED INFERENCE | Option/backend comparison above | Conditional direction and NR0B gate | Frame dependencies, translator coverage, ownership integration |
| Native rendering fixes black surfaces | UNRESOLVED | [Relevance assessment](../../fable2-gpu-reference/06-fable2-relevance-assessment.md), user reports of intermittent Canary symptoms | No fix claim or symptom-driven shader rewrite | Causal shader/resource/configuration evidence |

This recommendation supersedes only the old priority to start by wrapping
present or expanding SXDK-001 into a primary seam. The original G1 design is a
historical proposal; its deterministic-stream aspiration is not established by
a repeatable save. G1.6B's configuration-first decision remains the immediate
gate. Retired G2A code, its branch and even availability of its historical Git
object are unnecessary to NR0A and NR0B.
