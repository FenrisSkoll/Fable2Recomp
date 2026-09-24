# Feature comparison at the audited pins

External: [himdo/Fable-2-Recomp, `2bdf8f93a0edcec599023ce9382ca284a7e92c06`](https://github.com/himdo/Fable-2-Recomp/tree/2bdf8f93a0edcec599023ce9382ca284a7e92c06).
Canonical: starting `a87f6e549f157e1eacfcc7fa1d41049c6c23e88a`, installed SDK `.51`.

`SUPPORTED` means evidence exists for the stated scope, not full parity.
External authored claims are marked explicitly; their build was not executed.
`UNKNOWN` means no adequate evidence, not absence of implementation.
The external project's enabled content/FPS overrides qualify its progression
claims even where the relevant feature is not itself implemented by a hook.

| Capability | External pin | Canonical evidence / limit |
| --- | --- | --- |
| Boot | SUPPORTED — author reports/source | SUPPORTED — repeated bounded validation |
| Main menu | SUPPORTED — author reports; allocator investigation | SUPPORTED — regression path validated |
| New game | SUPPORTED — author report | SUPPORTED — native new-game/childhood evidence |
| Childhood | SUPPORTED — author report and named trigger observations | SUPPORTED — native prologue milestones |
| Bowerstone | SUPPORTED — author report | SUPPORTED — Old Town and Market evidence |
| Oakfield | PARTIAL evidence — implied by campaign report, no pinned endpoint trace | SUPPORTED endpoint — load/control/basic interaction/save/normal exit; full native Market→Oakfield replay unmeasured |
| Later-game progression | SUPPORTED — author report, Spire annotations | UNKNOWN beyond documented endpoint |
| Full-game completion | SUPPORTED — explicit author report, not independently validated here | UNKNOWN — not claimed |
| Save/load | SUPPORTED — persisted save-folder workflow reported; no detailed parity protocol | SUPPORTED for tested Hero000 create/load/update/restart workflow |
| Xenia save interoperability | UNKNOWN — folder advice does not prove round trip | SUPPORTED for tested Xenia→native→restart→Xenia sequence |
| Gamepad | SUPPORTED — SDL driver | SUPPORTED — SDK/native validation |
| Keyboard | SUPPORTED — custom synthetic gamepad | SUPPORTED SDK capability; calibrated automation used; full remapping UX not audited |
| Mouse | SUPPORTED — mouse-to-right-stick source | PARTIAL — SDK MNK capability; this audit did not validate Fable camera UX |
| Keyboard-aware prompts | NOT IMPLEMENTED — README unchecked | NOT IMPLEMENTED as an enhancement |
| Uncapped FPS | WORKAROUND-BASED — author reports vsync-off guest cadence change | NOT IMPLEMENTED as validated game behavior; SDK toggle is not a parity claim |
| 60 FPS | WORKAROUND-BASED — r11 override plus timing configuration | NOT IMPLEMENTED as validated game behavior |
| Higher internal resolutions | NOT IMPLEMENTED — README unchecked; window sizing exists | NOT IMPLEMENTED as validated enhancement; renderer scale settings are separate capability |
| Widescreen enhancement | UNKNOWN — proposals/patch knowledge, no validated implementation | NOT IMPLEMENTED as enhancement; original game's aspect behavior retained |
| Vulkan | EXPERIMENTAL — source plugin/smoke/gamma work; README unchecked | UNKNOWN for Fable gameplay; Windows D3D12 is validated target |
| D3D12 | SUPPORTED — prebuilt or source plugin choices | SUPPORTED — effective Xenos/D3D12 RTV on RTX 5080, 1× bindless/tiled |
| Linux | NOT IMPLEMENTED — README unchecked | NOT IMPLEMENTED as validated Fable target |
| Debug tooling | SUPPORTED — many probes, heterogeneous isolation | SUPPORTED — static closure, ownership, fault walking, dumps, saves, GPU metadata |
| Lua inspection/execution | EXPERIMENTAL — F5 runs a user Lua file through captured method | NOT IMPLEMENTED as interactive host execution; static binding knowledge added by audit |
| Function tracing | SUPPORTED — generic entry/RLE/count tracing; overhead unmeasured | PARTIAL — indirect-target coverage and focused diagnostics; no equivalent broad live frequency UI |
| Renderer customization | EXPERIMENTAL — source runtime/plugin patch and launcher | EXPERIMENTAL research/instrumentation; no replacement renderer in installed application |
| CE / website content | WORKAROUND-BASED — gates/returns forced, author reports unlocked chest | UNKNOWN entitlement/content parity; no gate bypass |
| Hero/dog graphical defects | PARTIAL rendering — texture repair unchecked | PARTIAL rendering — black/blank surfaces independently observed, cause unresolved |
| Text/font findings | EXPERIMENTAL probes and external names | PARTIAL — queue/callback evidence; specific glyph path remains a lead |
| Performance | UNKNOWN comparative result — increased-FPS claims, no controlled benchmark | PARTIAL measurement — build/fault-walk timings; no matched cross-project gameplay benchmark |
| Deterministic input automation | SUPPORTED source — local TCP timed controls; inferred state | SUPPORTED — established calibrated bring-up harness |
| Physics/animation/audio parity | UNKNOWN across enabled timing changes | PARTIAL original-runtime bring-up; no complete subsystem parity proof |

Canonical evidence: [current README](../../README.md),
[save parity](../fable2-native-save/fable2-native-save-write-parity.md),
[Phase 5A](../fable2-discovery-pipeline/09-phase5a-tranche-001.md),
[GPU runtime closeout](../fable2-native-renderer/nr0b1/runtime-closeout.md),
[renderer handoff](../fable2-native-renderer/nr0b2/completion-and-handoff.md),
[fault-walk performance](../fable2-fault-walker/fault-walk-performance.md).
External source attribution for individual claims is in
[external-leads.json](external-leads.json) and the pinned source inventory.

The practical gaps exposed are campaign coverage, convenient live Lua execution,
general call-frequency summaries and configurable enhancement experiments.
They are opportunities to ask better questions, not a reason to reproduce the
external mechanism. Core input, save interoperability, systematic discovery and
bounded diagnostics should not be duplicated merely to match another UI.
