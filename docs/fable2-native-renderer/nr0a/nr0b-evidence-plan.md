# NR0B: bounded configuration and frame-contract evidence

**Specification only. No observer, hook, capture switch or launcher described
here has been implemented by NR0A.** NR0B requires separate authorization for
its exact instrumentation, build, user-operated run and safe working-copy
preparation. Shader/resource payload capture remains a later, separately
bounded authorization even after metadata collection is approved.

## First decision: effective configuration

Begin with G1.6B's selected `EXP-CONFIG-CAP-001`, as recorded in
[static seam coverage](../../fable2-gpu-reference/evidence/static-xdk-seam-coverage.json)
and the [experiment plan](../../fable2-gpu-reference/09-evidence-gaps-and-experiment-plan.md).
The newer testing documents do not complete it. Configuration files and requested
values are insufficient: record effective selections after initialization and
capability fallback. Do this before attributing any shader/material fault.

Use one native checkpoint first. Prefer the latest documented Oakfield endpoint
if preflight confirms its identity and the user recognizes the loaded scene.
The Market fountain report is a fallback candidate, not proof of a present save
or a requirement to replay gameplay. See the exact
[save/testing handoff](reading-and-provenance.md). If neither checkpoint can be
identified, request the user's choice; do not search through gameplay.

Future preparation must inventory the selected seven Hero000 payloads and
platform metadata, preserve their relative paths/sizes/SHA-256, and make a new
preserved checkpoint and a distinct writable `user_data_root`. The documented
endpoint source is
`C:\Dev\Fable2Recomp\out\phase5a\checkpoints\end-001-native\user-data`;
`mainsave.bin` expected from that handoff is 415039 bytes,
`13FC340F6869DA73CB958BA36CB50905E29B8FBEA073CEFF46490DB4A9812489`.
Mismatch is a new identity to review, not permission to overwrite it. Do not
reuse an existing session root, modify backups, import/export saves or combine
native/Xenia headers. NR0A has not verified save-file presence.

The accepted testing exception to `fable2-run` uses its release/xenos/debug
arguments and numbered-log allocation through `Get-Fable2NextRunNumber`, adding
an explicit isolated `--user_data_root`; the normal helper currently cannot
take that root. NR0B should document its exact command/run card using the
[session contract](../../fable2-discovery-pipeline/coverage/README.md) and
[completed tranche](../../fable2-discovery-pipeline/09-phase5a-tranche-001.md),
without silently changing the normal helper. Wait for the actual process handle;
record real start/end/exit status independently of user reports. The user
launches, loads, positions the camera and exits. No controller sequence,
navigation automation or timed NPC-wait experiment is needed.

## One short collection window

After the user confirms the scene is loaded, request a stationary view containing
ordinary world rendering and the player/dog if naturally visible. Record what is
actually on screen; do not require finding a particular character or reproducing
an intermittent fault. Avoid menus during the window. The user arms collection
and remains in control. One optional capture-off comparison at the same checkpoint
may assess disturbance; no long route or repeated multi-scene gameplay is required.

Proposed hard upper bounds, subject to the NR0B implementation review:

- Arm timeout: 5 seconds for the first complete swap interval after the manual
  trigger. Stop collection within 5 seconds of triggering regardless of progress.
- At most three complete consumer `XE_SWAP` intervals: one target interval and
  at most two adjacent intervals for carry-in/output-consumer context. Record
  initial state needed for the target; do not infer its resource producers from
  an arbitrary earlier frame. Missing prehistory stays unknown.
- At most 20,000 draw decisions, 100,000 metadata records and 32 MiB of metadata,
  whichever comes first. These are safety bounds, not measured Fable counts or
  promises of sufficient coverage. No full register dumps or payload arrays.
- Bounded host buffers and reserved terminal/drop counters; no file I/O or
  blocking waits on the guest/GPU consumer thread. Observer failure disables
  recording and preserves original execution; it must not catch guest faults.

Stop on the first limit, observer error, device loss, fatal failure or user
cancel. Record incomplete/limit/dropped state explicitly. Do not force-kill a
healthy game merely because recording ended; the user exits normally and the
monitor waits for real termination. A truncated frame cannot pass a coverage
gate. If the cap is insufficient, review a narrower target before expanding it.
Do not claim the capture is non-disturbing until overhead is measured.

## Proposed metadata fields and actual observation sites

All SDK sites below are source-confirmed at
`fc5a00b31f702e82377aa1010395af7ba8cff4f7`; exact files/blobs and principal
symbols are in the [catalog](evidence/reference-pins.json). “Available” means
available to source code or existing logs, **not** that a joined NR0B event
already exists. Overhead descriptions are expectations to measure. All new
observation code is outside NR0A.

| Fields | Where actually observable / available now | Decision value and required work | Expected disturbance / stability |
|---|---|---|---|
| Run ID, Fable/SDK commit/tree/dirty state, EXE/runtime/GPU DLL full path/size/SHA-256, loaded module identity, TU1/base/update identity | Read-only launch preflight plus actual process module list and existing runtime title logs; current disk hashes documented separately | Detect wrong executable/DLL/TU/config; add run metadata, no guest hook. Post-patch loaded-image identity needs a supported loader identity path or existing verified evidence with its limitation stated | File hashing outside capture window; loaded identity once. Hash stable for same bytes; source commit alone cannot prove loaded artifact |
| Save relative paths/sizes/hashes, source/preserved/writable roots, selected profile/slot, before/after copy inventories | Future save preflight using accepted testing policy; not accessed in NR0A | Establish exact inputs and no source overwrite; metadata only, not file content | Once outside timed window. File hashes stable until a save update; user scene description is not a hash |
| Adapter name/LUID/vendor/device, driver/OS, selected GPU plugin/API, feature level, ROV/binding/tiled-resource tiers and applicable alpha blend-factor capability | `src/ui/d3d12/d3d12_provider.cpp:D3D12Provider::Initialize`, selected device/capability objects and backend initialization; logs expose only a subset | Effective device snapshot once; add narrowly bounded capability reporting where absent. If current headers/device query do not expose a capability, report unavailable, not false | Initialization queries/log metadata, outside timed draw loop. LUID is machine/session scoped, vendor/device not unique; driver/API version explicit |
| Requested and effective anisotropy, `clear_memory_page_state`, async shader compilation, scale X/Y, internal/output extent, RT path RTV/ROV, bindless/tiled choices, vsync/present mode and relevant config file hashes | Final CVar values plus actual selected paths: `d3d12/render_target_cache.cpp` (`render_target_path_d3d12`), provider, pipeline/texture cache and presenter setup | Complete `EXP-CONFIG-CAP-001`; report selected behavior and reasons, not just config defaults. Add one post-selection snapshot; no behavior changes | Small once-per-run metadata. Stable only for same config/capabilities; resize creates a new extent epoch |
| Cache paths/state, existing/new cache, shader translation/PSO readiness/miss counters, warmup conditions | Runtime cache configuration; `d3d12/pipeline_cache.cpp:LoadShader/ConfigurePipeline`; existing logs partial | Distinguish cache/async misses from semantic absence. Inventory/report current isolated cache; no clearing user caches or forced warmup | Counts/metadata; first-time shader hashing/analysis may add work. Cache keys can be driver/build-specific; record scope |
| Capture epoch, consumer event sequence, packet location/ring-wrap epoch, IB execution instance and parent, opcode, draw decision/outcome, predication, primitive/count/index source, skip reason | `src/graphics/command_processor.cpp:ExecutePacketType3` before predicates and draw dispatch, plus `d3d12/command_processor.cpp:IssueDraw` outcomes | Map actual attempted and executed work, including suppressed/no-op/zero-count/pipeline-not-ready/copy routes. Add bounded consumer metadata and explicit joins. `IssueDraw` alone misses earlier filtered packets | Per-operation CPU work/buffer writes; no packet payload copy. Sequences/addresses are run-local, IB addresses reusable; timestamps do not define ordering |
| Vertex/pixel shader stage, microcode length and content identity, feature mask, translation/specialization identity, constant-bank identity/change serial, PSO result | `PipelineCache::LoadShader/ConfigurePipeline`, `pipeline/shader/translator.cpp:Shader::AnalyzeUcode`, `D3D12CommandProcessor::UpdateBindings` | Census original shader needs and unsupported features; join bound shader to actual draw. Existing internal hashes need algorithm/length labeling; compute SHA-256 only once per new shader if required. Constants metadata/digests, no constant payload in NR0B | Deduplicate expensive hashing outside repeated draw path where safe. Same bytes/stage/length stable; host specialization/PSO key build/config scoped; mutation requires new identity |
| Used vertex/texture fetch slots, decoded address/span/layout/format/pitch/mip/endian/swizzle, sampler state, vertex/index stride/range and index bounds where already decoded | `pipeline/texture/cache.cpp:RequestTextures/BindingInfoFromFetchConstant`, shader used-binding masks, `IssueDraw`/`UpdateBindings` and existing primitive-processing state | Identify necessary inputs and distinguish aliases/views; bounded decoded numeric fields only. Add draw-linked records; do not reread arbitrary guest structures or scan resource payloads | Per-used-binding metadata; deduplicate by state serial. Guest address is not cross-run resource identity; decoded layout hash stable only for same fields |
| RT/depth formats, EDRAM base/pitch/extent/sample state, viewport/scissor, masks, depth/stencil/blend state, active RT path and ownership change | `pipeline/render_target/cache.cpp:Update/ChangeOwnership`, D3D12 draw/RT-cache selected state | Reconstruct attachment dependency and required output behavior; capture relevant typed fields plus actual accepted outcome. No whole register dump | Per-change/event work. EDRAM region/host handle only run-local; semantic state hashes include canonical fields |
| Resolve source regions/format/sample choice, destination guest ranges/layout, clear/copy outcome and ordering | `src/graphics/util/draw.cpp:GetResolveInfo`, `d3d12/render_target_cache.cpp:Resolve`, resulting shared-memory write notifications | Separate real resolve outputs from draw rendering and locate later consumers; add span-level metadata, no image | Per-resolve metadata. Resolve event ID run-local; destination address alone not durable identity |
| Guest-range validity, CPU invalidation serial, GPU-write serial, host-cache generation/retirement, alias overlap | `shared_memory.cpp:RequestRanges/RangeWrittenByGpu/MemoryInvalidationCallback`, texture/RT cache creation and invalidation paths | Establish observed coherency edges. Add observer serials to existing notifications without altering synchronization. These are observation generations, not proof of guest allocation/destruction; escalate to a specific allocator/resource site only if necessary | Page/range events may burst; coalesce only while preserving dependency edges and counts. Avoid new guest page watches by default. All generations run-local |
| Submission ID, record/submit/completion relation, actual fence value/completed value, swap interval and output generation | `D3D12CommandProcessor::EndSubmission/CheckSubmissionFence`, `CommandProcessor::ExecutePacketType3_XE_SWAP`, `Presenter::RefreshGuestOutput` | Associate work with completion and visible output rather than CPU timestamps. Record existing fence observations; do not add waits/readbacks. Presentation metadata only if needed to disambiguate output | Per-submit/swap metadata; fences and IDs run-local. One swap is not necessarily one submission or one displayed frame; mailbox can drop/coalesce output |
| User scene, camera description, visible player/dog, symptom present/absent/intermittent, resolution and subjective pacing | User report linked to run/capture interval; existing log/presentation extent | Establish what was actually observed, without semantic inference from a save name. No automatic character detection or screenshot/image readback required | No GPU cost from report; observation not deterministic or a content identity |
| Optional title callsite/thread/sequence and produced packet-span correlation | A separately qualified synchronous producer boundary, with TU1 ABI and exact emitted ring/IB spans; no such complete interface is currently qualified | Needed only if consumer map cannot discriminate A/B. Must join producer spans to consumer ring-wrap and IB execution instances. `sub_82BA34D8` can be a forwarding/present correlation lead only; SXDK-001 covers its narrow fetch operation only | Additional hook/guest-path disturbance; scope separately reviewed after configuration/frame metadata. Guest addresses stable for identical TU1 code; LR/thread/event associations run-local |

The asynchronous GPU consumer has host command-processor state, not the original
title caller's live PPC LR/stack. Reading its current thread or tagging the next
draw with the most recent present would invent ancestry. A valid producer join
needs bounded synchronous emission records, exact packet spans, ring wrap and
indirect-buffer reuse identities, and ordering across producer threads. If this
cannot be shown, title association remains null. Do not install a speculative
`sub_82AAC208` hook on the strength of a name.

## Metadata is not replay data

NR0B should yield a joined draw/resolve/submission map, a shader feature census,
resource-view identities and explicit missing producer/lifetime edges. It does
not reconstruct shader microcode, constants, textures, vertices or the initial
contents of color/depth/history targets. Hashes alone cannot supply those bytes.

A later translation/replay phase would need separately authorized, local,
bounded payloads for the selected workload: exact shader microcode and support
metadata, constants, vertex/index ranges, texture subresources, and any required
initial attachment/history contents. It must define capture-time consistency,
byte order, format, readback cost and private storage. NR0B metadata may show
that GPU-produced inputs make this substantially harder. Do not perform shader
extraction, asset conversion, screenshots/readbacks or payload capture under the
metadata specification. Only non-payload provenance/summary evidence belongs in
Git; future private output belongs under an explicitly ignored local directory.

## Acceptance and decision output

NR0B passes its configuration gate when actual loaded identities, effective
paths/capabilities and cache state are recorded with no invented defaults.
Unknown capabilities remain explicit and block only decisions that need them.

Its frame gate requires at least one complete bounded interval with recorded
drop/limit state, explicit attempted-versus-executed draw decisions, shader/fetch/
attachment associations, resolve destinations and observed submission ordering.
Report unobserved prehistory, resource-generation gaps and title joins as null.
Do not label the interval complete for replay unless its dependencies close.

Select at most one candidate workload and list its input/output dependencies,
shader feature needs, CPU/GPU writes, aliasing, queries/memexport, and required
next evidence. Prefer an ordinary indexed/textured draw with tractable shaders
and no unaccounted feedback; do not select a specialized copy because SXDK-001
is already named. This can justify an isolated translation proof even if no
live pass replacement is safe. If no candidate qualifies, return an explicit
blocked implementation gate and the smallest missing observation.

Measure recorder time/bytes/drop counts/high-water marks and compare user-visible
behavior with capture off where practical. A repeatable save does not imply
deterministic GPU order, animation, asynchronous compilation or scheduling.
Do not require byte-identical whole-frame streams or claim full equivalence
from one successful load.

An expandable future matrix can add terrain/world opaque, skinned characters,
shadows, alpha/effects, UI and video as coverage needs arise. Those scenes are
not prerequisites for this first short capture. Visual equivalence, functional
compatibility and performance remain separate questions.
