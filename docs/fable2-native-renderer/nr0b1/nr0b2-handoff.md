# NR0B-2 recorder preparation — specification only

NR0B-1 remains **PREPARED**, not runtime-verified. First finish its
[run card](user-run-card.md), reconcile all stages and loaded artifacts, and
review the user-confirmed scene/termination. Do not add the recorder before
this dependency closes. Reuse the same verified configuration and checkpoint
provenance; any later process needs a fresh unique writable root and run ID.

The SDK source below is present at reporting commit
`06c4b7002a449ad4d173ec90c625e490ed03fe74`. These locations and existing values
are **SOURCE-CONFIRMED**; the proposed event joins are **UNRESOLVED** and are
not implemented. The reporting changes do not change these ownership paths.
Paths are relative to `C:\Dev\rexglue-sdk-v0.10`.

| Minimum chain | Source locations / symbols | Existing join value; missing work |
|---|---|---|
| Attempted versus executed decision | `src/graphics/command_processor.cpp:CommandProcessor::ExecutePacketType3`, `ExecutePacketType3_DRAW_INDX`, `ExecutePacketType3_DRAW_INDX_2`; `src/graphics/d3d12/command_processor.cpp:D3D12CommandProcessor::IssueDraw` | Consumer owns packet, predicate and draw state. Add run-local decision serial before suppression plus explicit outcome. Backend calls alone omit earlier suppressed packets; successful IssueDraw is not automatically a host draw (copy/no-op/async-not-ready paths exist). |
| Bound shader identity | `src/graphics/d3d12/pipeline_cache.cpp:PipelineCache::LoadShader`, `ConfigurePipeline`; D3D12 command processor `UpdateBindings` | Bound shader objects/hash and specialization exist on consumer path; label algorithm/stage/length and configuration scope. A pointer is not stable across runs. Associate the actual bound translation/pipeline outcome with the same draw serial. No microcode or constants payload in metadata. |
| Used texture/fetch state | `src/graphics/pipeline/texture/cache.cpp:TextureCache::RequestTextures`, `BindingInfoFromFetchConstant`; D3D12 command processor `UpdateBindings` | Used binding masks and decoded fetch information exist; draw serial and bounded state-change serials are new recorder work. Guest addresses alone do not identify a lifetime or unique resource. Record only used decoded state, no scanning guest objects. |
| Attachment/depth state | `src/graphics/pipeline/render_target/cache.cpp:RenderTargetCache::Update`; `src/graphics/d3d12/render_target_cache.cpp:D3D12RenderTargetCache::Update` | Registers and accepted attachment path exist in consumer; join only after applicable state acceptance. EDRAM base, format, samples and extent are not by themselves proof of earlier contents or producer dependencies. |
| Resolve destination | D3D12 command processor `IssueCopy`; D3D12 render-target cache `Resolve` | Decoded resolve destination/range and selected operation exist; tie copy/resolve outcome to decision and submission. Destination address may alias an input, so missing prior content cannot be assumed zero. |
| Submission / swap relation | D3D12 command processor `EndSubmission`, `CheckSubmissionFence`, `IssueSwap`; common processor `ExecutePacketType3_XE_SWAP`; `src/ui/presenter.cpp:Presenter::RefreshGuestOutput` | Existing submission/frame/fence values are run-local and not a universal frame ID. Add explicit edges from decision to submission and swap output. Host mailbox/presentation can coalesce or drop output; one swap interval is not necessarily one displayed frame. Existing fence observations only, no new wait. |

The minimum useful record joins the consumer decision, accepted state, shader
and resource-view identities, attachment/resolve operation and submission/swap
context. None of the existing IDs supplies this full chain automatically.
NR0B-1's run ID/stage snapshot supplies configuration context only, not those
joins. Initial state must include the carried-in values actually needed by the
chosen interval; omitted producers or overwritten/reused indirect buffers
remain explicit dependency gaps.

Preserve the [NR0A bounds](../nr0a/nr0b-evidence-plan.md): stop **within five
seconds of manual trigger**, at most **three complete consumer XE_SWAP
intervals**, **20,000 draw decisions**, **100,000 metadata records**, or
**32 MiB metadata**, whichever limit occurs first. These are ceilings, not
targets. Mark the initial partial interval, carry-in state, incomplete final
interval, dropped records, high-water marks and missing dependencies. Reserve
terminal/error counters and use bounded buffers. No file I/O on the hot
consumer path, no additional GPU synchronization, no shader/resource payloads.
Stop on recorder error/device loss/fatal failure/user cancellation without
catching guest failures or terminating healthy gameplay.

The GPU consumer cannot recover the original producer's title caller from
its host thread, a current PPC LR, or the most recent present. Producer-to-
consumer correlation would need a separately qualified synchronous emission
boundary, packet spans, ring-wrap epochs, indirect-buffer execution/reuse IDs
and cross-thread ordering. That is a separate gate. SXDK-001 remains a narrow
texture-fetch method with two recovered callers and six general bypass
segments; it is not revived as the recorder entry seam. `sub_82AAC208` remains
a lead, and `sub_82BA34D8` remains a forwarding/presentation correlation lead.
[G2A retirement](../../fable2-gpu-reference/g2a-retirement.md) is unchanged.

Do not expand this into a resource-lifetime recorder without a concrete
candidate dependency that requires it. Metadata hashes cannot reconstruct
shader microcode, texture/vertex/index/constant contents or initial targets.
Any translation/replay payload phase needs separate bounded authorization.
A repeatable save does not promise deterministic scheduling/GPU execution.

Acceptance remains separate for complete metadata, functional behavior,
visual equivalence and performance. Current ReXGlue is the regression baseline;
Canary is a comparison implementation, not an unconditional correctness oracle.
Configuration verification alone neither explains black surfaces nor qualifies
a native renderer or live mixed-target replacement.
