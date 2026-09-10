# Effective GPU configuration: reporting gap assessment

Status: **CONFIGURATION VERIFIED — READY FOR NR0B-2**. Actual results and
scoped limitations are in the [runtime closeout](runtime-closeout.md).
The following historical gap table was
produced before implementing reporting. It carries forward `EXP-CONFIG-CAP-001`
from [NR0A](../nr0a/nr0b-evidence-plan.md). No requested setting below is changed
to attempt a visual fix. Paths in the source column are relative to canonical
ReXGlue `src/`, baseline `fc5a00b31f702e82377aa1010395af7ba8cff4f7`.

| Required field | Existing source/log; present evidence kind | Sufficient? Minimal addition | Authoritative time |
|---|---|---|---|
| Source HEAD/tree, dirty state, build configuration | Git and release CMake cache; source/disk provenance | Yes; helper inventories exact inputs, keeps source/build/staged/loaded identities separate | Before build and staging, rechecked before launch |
| EXE and loaded GPU/runtime paths, size/hash, PID/start/end/exit/arguments | Accepted launcher does not reliably wait on the GUI process; historical disk hashes only | No; actual process handle, module enumeration and exact file-hash comparison in isolated launcher, no memory dump | EXE at process start; DLLs when observed loaded; termination after handle signals |
| Title, media, TU, post-patch image | Existing loader/title logs and accepted generated-image identity | Supported title logs retained and parsed where available; no process memory hash. Post-patch SHA remains supported static identity chain, not newly measured loaded memory | Runtime title load, with explicit post-patch-hash limitation |
| Adapter description/vendor/device | `ui/d3d12/d3d12_provider.cpp:Initialize`, DXGI adapter log | Existing values are selected, but machine-readable join missing; include in one device record | Successful selected-device initialization |
| LUID and driver | Selected adapter/device available in provider; not logged | Add LUID and selected adapter `CheckInterfaceSupport` driver query, with HRESULT/unavailable; never query another adapter as substitute | Selected adapter, after device creation |
| OS | Launcher host OS query | Add exact OS/version/source to process report, separate from device capability | Launch preflight |
| Host API and selected feature level | D3D12 provider creates feature-level 11_0 device | Report actual API/create feature level, not maximum advertised feature level | Successful device creation |
| ROV/binding/tiled tiers | Provider queries OPTIONS; existing log prints conservative values even if query failed | Preserve OPTIONS HRESULT; null/unavailable capability on query failure while separately retaining runtime's conservative selection | Existing OPTIONS query completes |
| Alpha blend-factor capability | Accepted PIP-003 divergence; canonical provider lacks the query | Default-off OPTIONS13 query supported by installed Windows SDK headers; HRESULT and null if unavailable. No behavior change | Selected device reporting stage |
| RTV/ROV requested/effective/fallback | `graphics/d3d12/render_target_cache.cpp:Initialize`, actual `path_` | Report final cache path after initialization; distinguish explicit request, vendor default and unavailable-ROV fallback | Successful command-processor context setup |
| Bindless requested/effective | `graphics/d3d12/command_processor.cpp:SetupContext`, `bindless_resources_used_` | Report actual member and binding-tier requirement | Successful context setup |
| Tiled shared memory requested/effective | `graphics/d3d12/shared_memory.cpp:Initialize`, reserved/committed allocation branch | Report actual sparse allocation state and capability/PIX policy reason | Successful shared-memory initialization |
| Resolution scale X/Y | Context setup clamps requested scale through common and D3D12 texture-cache limits | Report request and resulting local scale values, clamp indication | Successful context setup |
| Output extent / internal extent | `IssueSwap` derives guest output; presenter owns actual swapchain extent | One first valid guest-output record and one first successful host-present record. No global internal resolution: multiple render targets; report that limitation | Lazy first swap/output and host present, pending beforehand |
| Anisotropy | `pipeline/texture/cache.cpp` policy; `d3d12/texture_cache.cpp` applies only to eligible samplers | Snapshot policy and source; effective per-sampler filtering is NOT observed in this phase, not one global setting | Context setup policy; per-sampler choice remains outside scope |
| `clear_memory_page_state` | GPU CVar read at existing frame-end behavior | Snapshot configured policy/source, no new per-frame observation | Context setup; later console changes outside snapshot |
| Async shader/pipeline policy | `d3d12/pipeline_cache.cpp:Initialize/ConfigurePipeline`: worker count plus CVar and non-null pixel shader condition | Report actual created worker count and conditional policy; do not report every pipeline or shader miss | Worker initialization; per-pipeline decisions outside scope |
| Vsync/presentation | `graphics/command_processor.cpp` guest wait policy; presenter calls `Present(0, RESTART | optional ALLOW_TEARING)` | Report guest policy separately from actual first host-present flags/result | Context setup and successful first host present |
| Config sources and precedence | CVar registry tracks default/config/environment/command-line/runtime; app loads executable-adjacent `fable2.toml` | Snapshot only relevant names/values/sources; inventory config path/hash/presence in staging and before/after launch | After config/environment/CLI application; effective component selections later |
| Cache roots and baseline material | `ui/rex_app.cpp:SetupEnvironment`, explicit `cache_root`; pipeline storage under `shaders/shareable` | Reuse explicit root and existing root log; inventory only narrow cache files/counts. Copy documented small baseline cache into new writable root, keep sources unchanged | Prelaunch identity plus runtime root/storage initialization |
| Driver-managed cache | Owned by driver/OS; no SDK isolation contract found | Report unmanaged/unisolated/unknown contents; do not clear or inventory an entire user/driver cache | Availability limitation, not a warmed-performance claim |

Only missing reporting is implemented. Records are initialization/one-time
completion metadata joined by explicit run ID and stage. Missing stages and
failed capability queries remain unknown. The normal renderer retains ownership;
there are no draw/packet/resource events, GPU waits/readbacks, payloads or guest
hooks. The companion preparation/run documents will record build and runtime
status separately.

## Implemented record contract

The SDK's default-empty, init-only switch is `--gpu_config_report <run-id>`.
Nine stage records use the existing log and prefix `REX_GPU_CONFIG_V1 `:
`runtime-paths`, `device`, `shared-memory`, `pipeline-policy`, `requested`,
`context`, `shader-storage`, `guest-output`, `host-present`. The last two are
lazy one-time completion records, not recurring telemetry. Each stage is
attempted once at its existing owning thread/site. No common snapshot lock,
GPU wait/readback or new guest-memory access was added. The only ongoing cost
after the first attempt is a boolean guard at swap/present, not per-draw work.

JSON fields are strings and use the literal `unavailable` for unknown
capabilities (the table's null/unavailable distinction is represented by this
explicit value). Limits are 64 ASCII ID characters, 32 fields per stage,
2048 bytes per string, 16 KiB per record: at most nine records / 144 KiB,
normally much smaller, plus bounded error markers. Existing debug-log volume
is separate and unchanged. Records are joined by run ID and stage, not log
arrival order. The Python parser rejects wrong-run, malformed, duplicate and
missing-field records, and reports missing stages. It never marks the whole
experiment verified automatically: scene/exit and semantic field review remain.

Actual initialized device/RT/bindless/scales/shared-memory choices and worker
count are read from existing selected state. Failed OPTIONS/OPTIONS13 queries
remain unavailable while the renderer's conservative fallback is unchanged.
An adapter LUID is local/session scoped, not stable across machines/reboots.
Driver version is explicitly sourced from selected adapter
`CheckInterfaceSupport(IDXGIDevice)` (Microsoft documents D3D9 UMD version;
WDDM 2.3+ shares package components), not mislabeled a D3D12 module version.
See [the API contract](https://learn.microsoft.com/en-us/windows/win32/api/dxgi/nf-dxgi-idxgiadapter-checkinterfacesupport).
Installed headers already declare
[OPTIONS13](https://learn.microsoft.com/en-us/windows/win32/api/d3d12/ns-d3d12-d3d12_feature_data_d3d12_options13);
support at runtime remains a query result, not a header-version inference.

The requested snapshot preserves each relevant CVar's source. `vsync` is a
guest wait policy, separate from the observed host `Present` arguments.
Anisotropy remains per-eligible-sampler policy, and async compilation remains
conditional on actual workers and an eligible pixel-shader pipeline. Later
console/settings edits are outside this immutable initialization snapshot;
leave them unchanged in the short run. One global internal extent is explicitly
unavailable because multiple target extents exist. First guest swap output and
first successful host-present extents are separately scoped, may differ and
may precede gameplay. Resizes after these records are not captured.

## Preparation-stage evidence status (historical)

| Group | Prepared/verified now | Requires the user-operated process |
|---|---|---|
| Artifacts | Exact baseline and staged file identities; source revision and build invocation | Actual loaded EXE/runtime/GPU/Tracy paths, PID/start/end/exit, observed command line |
| Device | Reporting compiles against current headers; D3D12-only SDK build | Selected adapter/LUID/driver/OS, API/create feature level, capability query outcomes |
| Effective configuration | Existing selection branches reviewed; no GPU settings changed | Actual RTV/ROV, bindless/tiled, final scale, async policy and first output/present records |
| Inputs/config | Source/copies match, runtime XEX/XEXP match accepted hashes; exe-adjacent config absent | Title/patch log corroboration and effective paths/CVar sources |
| Caches | Explicit isolated root with two copied baseline files | Actual cache root/storage initialization and selected path compatibility |

Unavailable capabilities block only conclusions that need them. Missing
effective selections cannot be filled from defaults. Actual scene, visual
symptoms and rendering correctness remain unobserved in NR0B-1 preparation.
