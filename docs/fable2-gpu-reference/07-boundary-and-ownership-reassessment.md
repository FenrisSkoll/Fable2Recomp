# Boundary and ownership reassessment

## Outcome

There is no single “best boundary.” The answer changes with purpose:

- `sub_82BA34D8` is the strongest confirmed transparent-forwarding and title-swap correlation boundary.
- `sub_82B6FA48` is a title-level presentation-coordinator hypothesis, not a draw seam.
- `sub_82AAC208` remains discovery-only because queue ABI, threading, ownership, recursion and coverage are unproved.
- `D3D12CommandProcessor::IssueDraw` and adjacent ReXGlue surfaces are the highest-value low-level diagnosis points, but they are internal state owners and are not promoted to replacement seams.
- representative static Xbox D3D/XDK draw/resource/shader/target methods remain the preferred replacement-seam research target.

The authoritative purpose-specific record is [`boundary-assessment.json`](evidence/boundary-assessment.json); staged seam and ownership decisions are in [`replacement-seams.json`](evidence/replacement-seams.json).

## Purpose matrix

Values are not an overall score. Each column answers a different question.

| Boundary | Exact address/symbol | Forwarding proof | Present correlation | Defect diagnosis | Replacement | Disposition |
|---|---|---:|---:|---:|---:|---|
| `G1-HOOK-82AAC208` | `sub_82AAC208 0x82AAC208 [0x82AAC208, 0x82AAC54C) size 0x344` | LOW | LOW | MEDIUM | UNKNOWN | STATIC METHOD RECOVERY TARGET |
| `G1-HOOK-82B6EA60` | `sub_82B6EA60 0x82B6EA60 [0x82B6EA60, 0x82B6EBC0) size 0x160` | MEDIUM | LOW | NONE | LOW | REJECT AS PRIMARY SEAM |
| `G1-HOOK-82B6F6C0` | `sub_82B6F6C0 0x82B6F6C0 [0x82B6F6C0, 0x82B6F9CC) size 0x30C` | MEDIUM | NONE | NONE | LOW | REJECT AS PRIMARY SEAM |
| `G1-HOOK-82B6FA48` | `sub_82B6FA48 0x82B6FA48 [0x82B6FA48, 0x82B6FBE0) size 0x198` | MEDIUM | HIGH | LOW | LOW | PRESENT CORRELATION LATER |
| `G1-HOOK-82BA2830` | `sub_82BA2830 0x82BA2830 [0x82BA2830, 0x82BA2CA0) size 0x470` | MEDIUM | NONE | NONE | NONE | RETAIN AS ORACLE |
| `G1-HOOK-82BA34D8` | `sub_82BA34D8 0x82BA34D8 [0x82BA34D8, 0x82BA3BFC) size 0x724` | HIGH | HIGH | LOW | LOW | FORWARDING PROOF ONLY |
| `G1-HOOK-82BA6968` | `sub_82BA6968 0x82BA6968 [0x82BA6968, 0x82BA6990) size 0x28` | MEDIUM | NONE | NONE | LOW | RETAIN AS ORACLE |
| `G1-HOOK-82BA6990` | `sub_82BA6990 0x82BA6990 [0x82BA6990, 0x82BA6C18) size 0x288` | MEDIUM | NONE | NONE | LOW | RETAIN AS ORACLE |
| `G1-HOOK-82BA6C18` | `sub_82BA6C18 0x82BA6C18 [0x82BA6C18, 0x82BA6EB8) size 0x2A0` | MEDIUM | NONE | NONE | LOW | RETAIN AS ORACLE |
| `G1-HOOK-8328D6F8` | `sub_8328D6F8 0x8328D6F8 [0x8328D6F8, 0x8328D744) size 0x4C` | LOW | NONE | LOW | UNKNOWN | REJECT AS PRIMARY SEAM |
| `G1-HOOK-83290138` | `sub_83290138 0x83290138 [0x83290138, 0x83290184) size 0x4C` | LOW | NONE | LOW | UNKNOWN | REJECT AS PRIMARY SEAM |
| `REX-VD-SWAP` | `VdSwap_entry` | MEDIUM | HIGH | LOW | NONE | PRESENT CORRELATION LATER |
| `REX-EXECUTE-PACKET3` | `CommandProcessor::ExecutePacketType3` | LOW | MEDIUM | MEDIUM | LOW | TARGETED OBSERVATION LATER |
| `REX-WRITE-REGISTER` | `D3D12CommandProcessor::WriteRegister` | NONE | LOW | HIGH | LOW | TARGETED OBSERVATION LATER |
| `REX-ISSUE-DRAW` | `D3D12CommandProcessor::IssueDraw` | NONE | LOW | HIGH | LOW | TARGETED OBSERVATION LATER |
| `REX-PRIMITIVE-PROCESS` | `PrimitiveProcessor::Process` | NONE | NONE | HIGH | LOW | TARGETED OBSERVATION LATER |
| `REX-LOAD-SHADER` | `PipelineCache::LoadShader` | NONE | NONE | HIGH | MEDIUM | TARGETED OBSERVATION LATER |
| `REX-ANALYZE-UCODE` | `Shader::AnalyzeUcode` | NONE | NONE | HIGH | MEDIUM | TARGETED OBSERVATION LATER |
| `REX-CONFIGURE-PIPELINE` | `PipelineCache::ConfigurePipeline` | NONE | NONE | HIGH | LOW | TARGETED OBSERVATION LATER |
| `REX-UPDATE-BINDINGS` | `D3D12CommandProcessor::UpdateBindings` | NONE | NONE | HIGH | LOW | TARGETED OBSERVATION LATER |
| `REX-REQUEST-TEXTURES` | `D3D12TextureCache::RequestTextures` | NONE | NONE | HIGH | MEDIUM | TARGETED OBSERVATION LATER |
| `REX-RT-UPDATE` | `D3D12RenderTargetCache::Update` | NONE | LOW | HIGH | MEDIUM | TARGETED OBSERVATION LATER |
| `REX-GET-RESOLVE-INFO` | `draw_util::GetResolveInfo` | NONE | LOW | HIGH | MEDIUM | TARGETED OBSERVATION LATER |
| `REX-RT-RESOLVE` | `D3D12RenderTargetCache::Resolve` | NONE | LOW | HIGH | LOW | TARGETED OBSERVATION LATER |
| `REX-SHARED-REQUEST-RANGES` | `SharedMemory::RequestRanges` | NONE | NONE | HIGH | LOW | TARGETED OBSERVATION LATER |
| `REX-SHARED-RANGE-WRITTEN` | `SharedMemory::RangeWrittenByGpu` | NONE | NONE | HIGH | LOW | TARGETED OBSERVATION LATER |
| `REX-END-SUBMISSION` | `D3D12CommandProcessor::EndSubmission` | NONE | MEDIUM | HIGH | LOW | TARGETED OBSERVATION LATER |
| `REX-PRESENTER-REFRESH` | `Presenter::RefreshGuestOutput` | NONE | HIGH | NONE | MEDIUM | PRESENT CORRELATION LATER |
| `REX-D3D12-PAINT-PRESENT` | `D3D12Presenter::PaintAndPresentImpl` | NONE | HIGH | NONE | MEDIUM | PRESENT CORRELATION LATER |

## G1 title boundaries

### Confirmed swap and lifecycle cluster

`sub_82BA34D8 [0x82BA34D8, 0x82BA3BFC)`, size `0x724`, retains device/front-buffer-like inputs and reaches `VdGetSystemCommandBuffer` and `VdSwap`. The paused G2A wrapper therefore tests a real title call, and a monotonic ID could later join it to presentation. All contributing draw, register, shader, binding, texture, EDRAM and resource-lifetime semantics have already been lost, so the same boundary has low defect-diagnostic and replacement value.

`sub_82BA2830`, `sub_82BA6990`, `sub_82BA6968` and `sub_82BA6C18` are transport/lifecycle oracles. Their guest ring, interrupt callback, engine and shutdown side effects make them requirements to preserve, not title renderer operations to replace.

`sub_82B6EA60` and `sub_82B6F6C0` preserve title creation and object-allocation context, including the `0x5E80` device-like allocation and `0x7C` initialization block, but no frame operation coverage.

### Presentation coordinator and Lionhead discovery leads

`sub_82B6FA48 [0x82B6FA48, 0x82B6FBE0)` remains a strong title presentation coordinator hypothesis. It retains title object references above the confirmed swap emitter. It is useful only if a later correlation question needs title-level frame identity; it does not identify why a surface is black.

`sub_82AAC208 [0x82AAC208, 0x82AAC54C)` has the `ProcessAsyncCommandQueues` timing label and a strong queue-processing hypothesis. G1.5D found no new proof of command layout, producer/consumer threads, ownership, coverage or direct callers. It is not authorized for wrapping.

`sub_8328D6F8` and `sub_83290138` prove the presence of “Outline Renderer” and “LightingManager Renderer” labels only. The short functions may register or construct subsystems; they are not established rendering methods.

## Complementary ReXGlue observation surfaces

The smallest later low-level diagnosis chain is:

1. `D3D12CommandProcessor::IssueDraw` assigns one terminal outcome: rendered, no-effect, zero-extent, pending-pipeline or failure.
2. `PipelineCache::LoadShader`, `Shader::AnalyzeUcode` and `PipelineCache::ConfigurePipeline` attach hashes, operation flags and readiness without bodies.
3. `UpdateBindings` and `D3D12TextureCache::RequestTextures` attach only affected fetch/layout/validity metadata.
4. `D3D12RenderTargetCache::Update`, `draw_util::GetResolveInfo` and `Resolve` attach affected pass/resolve metadata.
5. `SharedMemory::RequestRanges`, `RangeWrittenByGpu` and `EndSubmission` establish lifetime and ordering.

These points retain discriminating state precisely because ReXGlue owns it. That makes them good observation points and risky replacement points. A second mutable register file, resource cache, EDRAM owner, submission queue or presenter would create dual ownership.

## Reconciling G1 and G1.5C

The two earlier statements concern different layers and stages:

- G1 rejected GPU ABI version 1 as the **primary semantic seam** for a Fable-specific renderer because implementing its obligations from raw PM4/register/memory behavior is emulator-scale.
- G1.5C confirmed that the same ABI and `rexgpu-xenos.dll` are **mandatory operational constraints** for the currently deployed renderer.

Both are true. Mandatory today does not imply the eventual title renderer must expose raw GPU ABI semantics; high semantic value does not imply ReXGlue services can be removed.

## Stage A — current compatibility/oracle mode

ReXGlue plus `rexgpu-xenos.dll` solely own `IGraphicsSystem`, guest-ring consumption, register state, memory callbacks/watches, interrupts, vblank, command submission, the D3D12 presenter/swap chain and shutdown. ReXApp/UIDrawers own host UI. Original TU1 Xbox graphics behavior is unchanged.

Fallback is simply the oracle path. There is no second renderer.

Entry is already satisfied by the exact pins and artifact. Existing evidence reaches L1.

## Stage B — hybrid observation and incremental-replacement research

During evidence acquisition, ownership remains exactly as in Stage A. Proven title wrappers may emit bounded metadata or a shadow normalized description, but their preserved original executes once and only ReXGlue renders. Low-level observations read minimal state from the current owner.

Unimplemented operations fall back before native side effects by taking the preserved original title path. This rule is source-valid for a single wrapper but a production incremental renderer is **not yet proved**: the pinned sources expose no interface to combine native output with oracle output without double rendering, and no composable dual-GPU ABI exists.

Stage B observation requires static method ABI proof, linked forwarding proof for each wrapper used, default-off/fail-open metadata, and verified ignored output paths. Incremental rendering requires an additional single-owner integration interface not present in this corpus.

## Stage C — eventual title-specific native-renderer mode

The planning preference is recovered Fable/Lionhead intent or static Xbox D3D/XDK operations, optionally normalized into backend-neutral title IR, then translated by a host backend. D3D12 capability choices must remain below guest semantics.

Ownership is intentionally unresolved. Exactly one component must own each of ring consumption, register state, resource/memory visibility, interrupts, vblank, queries, command submission, guest-output mailbox, presenter/swap chain and shutdown. `rexgpu-xenos.dll` remains the oracle until one validated model covers every retained service. It is eventually replaceable only if that model exists; removal is not assumed.

## Boundary decisions by purpose

- Mechanism: **FORWARDING PROOF ONLY** for `sub_82BA34D8`.
- Presentation: **PRESENT CORRELATION LATER** at the title swap, `VdSwap_entry`, mailbox refresh and D3D12 Present only if the correlation decision needs it.
- Diagnosis: **TARGETED OBSERVATION LATER** at `IssueDraw` and the minimum attached shader/resource/EDRAM/lifetime points.
- Replacement: **STATIC METHOD RECOVERY TARGET** for representative static XDK operations; no current raw observation point is a validated replacement seam.
- Oracle: ring, lifecycle, memory visibility, interrupts, vblank, queries, presenter and host-UI behavior remain ReXGlue contracts.

The corpus cannot yet prove a viable incremental ownership transition. That is a result, not an invitation to invent one.
