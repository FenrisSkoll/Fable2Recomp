# Source-backed implementation audit

## Inspection boundary

All five starting repositories were publicly readable on 2026-09-09. Read-only
`git ls-remote` for each `main` matched the examined pin. Existing references
were located from [G1 scope](../00-workstream-scope.md), under
`C:\Dev\Fable2NativeRendererResearch`; none was fetched into, switched or edited.
Skate, its exact SDK dependency and PGR4 were newly cloned under that directory's
`nr0a` child, outside both canonical repositories, without initializing submodules.
No reference was compiled or executed. These are source audits, not runtime tests.

The [pin catalog](evidence/reference-pins.json) records full URLs, local paths,
branches, commits, trees, inspection date, available history, all direct gitlinks,
license evidence and 44 source records with exact blobs and literal symbols.
Each link below is immutable. Existing G1/G1.5 pins remain separate from NR0A pins.

| Reference / examined branch | Exact commit | Exact tree | Available history |
|---|---|---|---|
| Skate3Recomp / main | `f6e0ae87fdfecbadb5c1e36c55d66a744187a3cd` | `1ccdb51bf28cace9ee9ece928e47f43a938bc438` | shallow, 1 commit |
| rexglue-skate3 / skate3-sdk-clean | `7eb0faf7787f5e01333c228b8e3f03c32f7295ea` | `70080ed29377a18d38474aa035c6bc0f76245fd9` | shallow, 1 commit; exact Skate gitlink |
| UnleashedRecomp / main | `cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c` | `14f1bd3756796aa78aa05efebe68b79c31edb2da` | shallow, 200 commits |
| XenosRecomp / main | `990d03b28a27b50277ee5d8d942e1c5f873869d1` | `27947117fe04e325d4fe923c6fa2afe11d79d836` | full, 35 reachable commits |
| Plume / main | `d890ac899e505fb30040e037a4037cdeca68f033` | `4102793d5b646ab164a42fc1b1692f173477581d` | full, 70 reachable commits |
| PGR4-Recomp / main | `464cc5b62527755d6a365b36a0e40ff843d722e9` | `d8fc528f5bc37f2ceb2fe9e7ddb2b7ac123c2d8c` | shallow, 1 commit |

Unleashed actually pins Plume `11926860e878e68626ea99ec88562ce2b8badc4f`;
its tree/history/license are separately recorded from available Git objects in
the existing Plume clone. The newer standalone Plume is not silently attributed
to Unleashed. Shallow inspection cannot establish earlier development rationale.

## Skate: implemented title-specific reconstruction with retained GPU services

The renderer is executable implementation included in
[CMakeLists.txt](https://github.com/mchughalex/skate3recomp/blob/f6e0ae87fdfecbadb5c1e36c55d66a744187a3cd/CMakeLists.txt).
Its path is:

```text
Skate guest scene traversal / original graphics calls
 -> title mesh and sorted-list hooks + XDK state/draw hooks
 -> BuildFrameScene: Skate structures, constants, resources, per-frame scene
 -> immutable FrameScene publication
 -> forked ReXGlue IssueSwap / presenter refresh callback
 -> RenderScene: native meshes, material shaders, targets and passes
 -> existing command-processor submission and guest-output mailbox
 -> ReXGlue host composition / presentation
```

**SOURCE-CONFIRMED entry and correlation.**
[skate3_native_render.cpp](https://github.com/mchughalex/skate3recomp/blob/f6e0ae87fdfecbadb5c1e36c55d66a744187a3cd/src/skate3_native_render.cpp)
defines link-time overrides. `sub_82795AD8` calls its original before collecting
mesh state; its draw-sequence comparison distinguishes immediate from deferred
draws. `sub_827FAF50` walks sorted scene entries, with a conditional native
occlusion dispatch filter. `sub_82B82E08` calls `OnFrameEnd` before original
swap. Other hooks collect shader bindings, constants, streams, indices, draw
completion, APT/UI brackets, cloth and movie state. This is a combination of
title structures and lower graphics observations, not one XDK texture setter
and not a new general PM4 renderer.

**SOURCE-CONFIRMED scene recovery.**
[skate3_native_scene.cpp](https://github.com/mchughalex/skate3recomp/blob/f6e0ae87fdfecbadb5c1e36c55d66a744187a3cd/src/skate3_native_scene.cpp)
`BuildFrameScene` uses `kViewCameraFromView`, mesh contexts, guest vertex/index
objects, material channels including `AttribulatorMaterialName`, light/shadow
state and captured transform/bone constants. It publishes a
`shared_ptr<const FrameScene>` under `g_scene_mutex`, with a generation.
[DrawItem](https://github.com/mchughalex/skate3recomp/blob/f6e0ae87fdfecbadb5c1e36c55d66a744187a3cd/src/skate3_native_scene.h)
holds material families, guest buffer addresses, texture references and per-draw
lighting. Deferred palette matching and entity identity stores are Skate-specific.
These layouts, offsets and family classifications cannot be transferred to Fable.

**SOURCE-CONFIRMED shader strategy; accuracy PROJECT-REPORTED.**
[scene.hlsl](https://github.com/mchughalex/skate3recomp/blob/f6e0ae87fdfecbadb5c1e36c55d66a744187a3cd/src/native/shaders/scene.hlsl)
and its included material files implement `vs_main`/`ps_main` with explicit
family selection. They contain hand-ported shading and empirical/fallback
branches, including a water approximation. Comments describing exact ports or
numeric agreement are reports, not NR0A differential tests. The build embeds
HLSL; the SDK fork's
[native_rhi_d3d12.cpp](https://github.com/mchughalex/rexglue-skate3/blob/7eb0faf7787f5e01333c228b8e3f03c32f7295ea/src/graphics/d3d12/native_rhi_d3d12.cpp)
`CreateShader` uses `D3DCompile` and cached DXBC. Vulkan shader headers also
exist. This is not evidence that arbitrary Fable microcode translates, nor that
all of Skate's shaders are automatically translated offline with XenosRecomp.

**SOURCE-CONFIRMED resources and passes.**
[skate3_native_scene_gpu.cpp](https://github.com/mchughalex/skate3recomp/blob/f6e0ae87fdfecbadb5c1e36c55d66a744187a3cd/src/skate3_native_scene_gpu.cpp)
`EnsureGuestTextureFromWords` validates six fetch words, uses SDK `TextureInfo`
and format helpers, and decodes/uploads supported textures. `ComputeItemFingerprint`
in the scene builder samples mesh content; cache paths revalidate texture/mesh
data, maintain routes and staged uploads, and defer release using submission
indices (`ReleaseRetiredAndFlushCaches`). These are implemented lifetime
strategies, not proof that sampled fingerprints cover every concurrent guest
mutation or alias. Prewarm and render threads still read guest backing memory;
an immutable scene descriptor does not freeze its referenced payload.

`RenderScene`, `RenderShadowAtlas`, `RenderOutlineMask`, pipeline/target helpers
and [post-processing](https://github.com/mchughalex/skate3recomp/blob/f6e0ae87fdfecbadb5c1e36c55d66a744187a3cd/src/skate3_native_scene_post.cpp)
implement native depth/shadows, opaque and transparent material work, resolves,
post effects, captured 2D replay and movie-plane composition. Menu, photo and
editor yield/warmup decisions remain in code. Read the actual branches and
configuration; names like `YieldForMenus` and stale explanatory comments do not
prove that every menu is currently emulated. The README's broad coverage and
speed claims remain PROJECT-REPORTED. It also reports customization, Hall of
Meat and park parity issues. No dedicated automated renderer correctness suite
was found in the examined top-level tree; debug stress/capture controls are not
equivalent to such a suite.

### The ownership cost behind Skate's live switch

The fork adds
[NativeGuestOutputRenderContext](https://github.com/mchughalex/rexglue-skate3/blob/7eb0faf7787f5e01333c228b8e3f03c32f7295ea/include/rex/graphics/native_guest_renderer.h),
a native RHI, D3D12/Vulkan implementations and command-processor integration.
The context lends a stable device adapter, frame-scoped command recorder and
resize-sensitive guest-output texture. The texture must return to
`kGuestOutput`; the command processor owns the underlying recording/submission.
The title renderer owns native caches and pass resources. It does not create a
second ordinary swapchain for the same window.

In the fork's
[D3D12 command processor](https://github.com/mchughalex/rexglue-skate3/blob/7eb0faf7787f5e01333c228b8e3f03c32f7295ea/src/graphics/d3d12/command_processor.cpp),
`IssueSwap` calls `NativeRhiBeginFrame` and `TryRenderNativeGuestOutput` inside
the existing presenter refresh; success ends a submission. Failure can use
the emulated blit, or retain the previous image when the output was widened.
The [Vulkan processor](https://github.com/mchughalex/rexglue-skate3/blob/7eb0faf7787f5e01333c228b8e3f03c32f7295ea/src/graphics/vulkan/command_processor.cpp)
has the corresponding integration.

[native_guest_renderer.cpp](https://github.com/mchughalex/rexglue-skate3/blob/7eb0faf7787f5e01333c228b8e3f03c32f7295ea/src/graphics/native_guest_renderer.cpp)
tracks whether the previous callback produced native output.
`ShouldSuppressEmulatedDraws` and `ShouldSuppressPassAtPitch` gate later
emulated draw/resolve work using title-driven pitch classes. PM4 parsing,
register updates, interrupts/vblank and memory-export paths remain. Exempt
passes and their resolves can still populate guest resources. The D3D12 query
path substitutes positive visibility while suppression is active. This is a
material compatibility policy, not a portable parity technique.

`ToggleSceneEnabled` has an implemented path: it requires the hook layer
enabled at startup, flips the scene setting, clears stale scene/2D state,
resets sticky pipeline failure and arms warmup/retention reset. The mode is
re-evaluated around frames; Graphics API changes require restart. Native and
emulated caches are not a single complete mirrored state. A false callback does
not undo prior guest mutations, recover suppressed EDRAM contents, rewind GPU
submission or guarantee a correct same-frame fallback. No general transaction
or device-loss rollback proof was found. For Fable, safe hot switching and
automatic recovery remain **UNRESOLVED**.

**Portable ideas:** recover title intent plus draw-time state, publish bounded
scene descriptions, assign generations, retire resources by completion, and
keep one composition owner. **Non-portable assumptions:** Skate layouts,
material ports, constant banks, asset GUIDs, surface-pitch suppression, positive
query substitution, retained-pass selection, editor/movie special cases and
motion retiming. The canonical Fable SDK contains neither this output callback
nor `native_rhi`; adopting it would be separate SDK implementation and review.

## Unleashed: broad static graphics API replacement

The accepted [G1 analysis](../02-unleashed-recompiled-reference.md) remains the
foundation, checked against actual
[video.cpp](https://github.com/hedge-dev/UnleashedRecomp/blob/cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c/UnleashedRecomp/gpu/video.cpp),
[video.h](https://github.com/hedge-dev/UnleashedRecomp/blob/cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c/UnleashedRecomp/gpu/video.h)
and [GUEST_FUNCTION_HOOK](https://github.com/hedge-dev/UnleashedRecomp/blob/cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c/UnleashedRecomp/kernel/function.h).
The implementation path is SOURCE-CONFIRMED:

```text
Sonic guest renderer / title patches
 -> replaced static D3D methods, GuestDevice / GuestResource
 -> RenderCommand queue
 -> g_renderThread and Proc* handlers / dirty-state assembly
 -> Plume pipelines, resource barriers and host command lists
 -> executeCommandLists, fence/semaphore coordination
 -> Video::Present / Plume swapchain, host UI
```

| Question | Source-backed result and Fable implication |
|---|---|
| Entry | Hook table replaces creation/destruction, locks, textures, surfaces, targets, shader/state binding, draw, StretchRect and Present. This is executable API replacement, not PM4 parsing. Coverage across operation families is the precedent; addresses are Sonic-only. |
| Scene | Guest code still chooses much of scene/pass order. The host translates device state; it need not rebuild every mesh/camera/light as named scene entities. Additional SWA/title-specific patches and shader/material identities exist. Fable could prefer this route if a comparably complete method contract is proved. |
| Shaders | `CreateShader` hashes the guest container bytes with XXH3-64, calls `FindShaderCacheEntry`, and selects preconverted data or explicit replacements. `GetOrLinkShader` handles host specialization variants; constants flow through `FlushRenderStateForMainThread`. Runtime DXIL specialization/linking differs from offline microcode translation. An unknown cache hash can create an empty `GuestShader`; it does not invoke a general Xenos fallback. |
| Resources | `GuestDevice` is `0x5E00`, whereas Fable's recovered allocation is `0x5E80`. `LockTextureRect`/`ProcUnlockTextureRect` and buffer unlock handlers stage host uploads and endian conversion. Title resource creation/texture loading paths supply layout and format information. `ProcDestructResource` places objects in frame-retired storage; fences guard reuse. None establishes Fable allocation, aliasing or CPU/GPU coherency. |
| Passes | Target/depth binding, clears, draw handlers and `ProcExecutePendingStretchRectCommands` preserve/translate the title sequence, including copy/resolve and depth/MSAA work. Custom movie, UI, blur and other shader paths coexist. This is not a general EDRAM emulator or proof of arbitrary alias compatibility. |
| Ownership | Video owns Plume device, direct/copy queues, command lists, fences/semaphores, resources and swapchain; `Video::Present` waits on CPU render progress and frame fences. Its own guest runtime/kernel/window integration remains; Unleashed does not use Fable's ReXGlue GPU plugin contract. |
| Switching | Host API selection exists. No native-to-Xenos renderer switch or general partial-submission recovery was found in the inspected renderer path. An unavailable shader is not evidence of an emulated fallback. |
| Cost/validation | Broad address hooks, guest structure definitions, XenonRecomp tooling, SWA and title patches, shader corpus and Plume integration. Existing source contains specialized behavior and asserts. NR0A performed no build, full-game coverage or parity test; the inspected path supplies no reusable Fable acceptance suite. |

The useful precedent is a complete device/resource/state contract with explicit
uploads and an ordered host command stream. Sonic-specific structures, shader
specializations, content handling, UI and timing patches are not portable.

## XenosRecomp and Plume answer component questions

[XenosRecomp](https://github.com/hedge-dev/XenosRecomp/blob/990d03b28a27b50277ee5d8d942e1c5f873869d1/README.md)
is an implemented microcode/container-to-HLSL tool, with DXC paths for DXIL and
SPIR-V and a directory-scanned, hashed shader-cache mode. It is not a renderer,
resource system or fallback emulator. Its documented reflection dependence,
integer/dynamic indexing, mini-fetch, memory-export, complex-control-flow and
numeric limitations prevent assuming Fable coverage. Read
`XenosRecomp/shader_recompiler.cpp`, `main.cpp`, `shader_common.h` and
`dxc_compiler.cpp` at the catalog pin. First obtain Fable feature/identity
metadata; any payload-based translator proof requires its own authorization.

[Plume](https://github.com/renderbag/plume/blob/d890ac899e505fb30040e037a4037cdeca68f033/README.md)
provides host devices, resources, command lists, queues, barriers and swapchains.
`plume_d3d12.cpp:D3D12CommandList::barriers` and
`plume_vulkan.cpp:VulkanCommandList::barriers` demonstrate executable backends;
`CMakeLists.txt` includes Vulkan and platform-specific D3D12/Metal code.
The project explicitly withholds a stable-API/production-ready claim pending
barrier and transition refinement. It brings no Fable semantics or shader
compiler. Its portability benefit is real source structure; its suitability for
the Fable presenter/device integration remains UNRESOLVED.

## PGR4 stopping rule

**PROJECT-REPORTED planned native renderer; SOURCE-CONFIRMED absence of a
native renderer implementation in the examined tracked tree.**
[Future-plans.md](https://github.com/beatrixzy/PGR4-Recomp/blob/464cc5b62527755d6a365b36a0e40ff843d722e9/Future-plans.md)
lists an unchecked Plume-based renderer;
[Status.md](https://github.com/beatrixzy/PGR4-Recomp/blob/464cc5b62527755d6a365b36a0e40ff843d722e9/Status.md)
assigns it to a future v2.1. The small public tree contains application setup,
manifest and documentation, with `rexglue_setup_target` in CMake. This audit
does not assert anything about private work or other revisions. No further
renderer-architecture investigation of PGR4 is warranted in NR0A.

## License and integration boundary

Actual root license files and pinned component license texts were inspected;
the catalog records paths, blobs or retrieval URLs/hashes. This is a provenance
assessment, not a decision to redistribute or integrate anything.

| Component | Inspected evidence / bounded assessment |
|---|---|
| Skate3Recomp | No root/component license file found in tracked tree; reuse permission **UNRESOLVED**. Public source availability is not permission to transplant it. |
| Skate SDK fork; canonical ReXGlue; research Canary | `LICENSE`: BSD-3-Clause text. Submodule and per-file notices remain separate; the fork's root license does not license Skate's title code. |
| Unleashed | `COPYING`: GPL version 3 text. Architectural study does not require Fable to adopt GPL. Direct code reuse would require a distinct licensing decision and compliance assessment. |
| SWA / ddspp | Exact pinned `LICENSE.md` / `LICENSE`: MIT; not a license for Unleashed as a whole. |
| concurrentqueue | `LICENSE.md`: simplified BSD/Boost alternatives with exceptions, including blocking-queue semaphore zlib terms. Do not flatten the component set to one label. |
| XenosRecomp | `LICENSE.md`: MIT; translator implementation and shared header reuse remain distinct from rights in input shaders and generated output. |
| Xenos dependencies | Exact pinned xxHash, zstd and fmt root texts inspected: BSD-2-Clause, BSD and MIT respectively. `dxc-bin` and smol-v had no root license at the five tried names: component reuse and bundled compiler redistribution terms remain unresolved in this audit. This limited search does not establish that no license exists elsewhere in those trees. |
| Plume | `LICENSE`: MIT, including the separately checked Unleashed dependency pin. D3D12MemoryAllocator/VulkanMemoryAllocator/volk license texts are MIT; Vulkan-Headers lists per-file Apache-2.0/MIT; bundled metal-cpp `LICENSE.txt` is Apache-2.0. |
| PGR4 | No license file in the examined tracked tree; direct reuse **UNRESOLVED**. |

All direct gitlinks are pinned separately in JSON. Transitive components not
needed to decide this architecture retain an explicit unaudited-license status;
this package is not a redistribution bill of materials. SDK multimedia, window
and other dependency inventories are not imported into Fable by this phase.

Keep five decisions separate: study architecture; reuse implementation source;
integrate a dependency; reuse a shader translator/shared support header; and
redistribute generated output. Generated shaders may incorporate translator
support code and proprietary input. Their permissions do not automatically
equal the translator's license and are **UNRESOLVED** until the actual output
and intended distribution are reviewed. No implementation code, shader payload,
license source copy, dependency or reference binary was copied into Fable.
