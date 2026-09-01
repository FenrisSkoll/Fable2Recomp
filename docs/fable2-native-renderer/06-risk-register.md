# Native-renderer risk register

Likelihood and impact are planning judgements, not evidence confidence. A risk
whose underlying fact is unknown stays explicitly unknown.

| ID | Risk / evidence state | Likelihood | Impact | Mitigation and gate |
|---|---|---:|---:|---|
| G1-R01 | **CONFIRMED gap:** lifecycle/present are bounded, but resource, state, shader, draw, resolve, and query methods are not identified. | High | Critical | G2 must recover and validate representative methods across each required family. Do not start backend replacement on present-only coverage. |
| G1-R02 | A bounded function is assigned the wrong semantic contract or PPC ABI. `.pdata` and names are not proof. | Medium | Critical | Require TU1 bytes/control flow, caller arguments, observed side effects, packet correlation, and forwarding tests for every hook. Unknowns remain unknown. |
| G1-R03 | Wrapper forwarding recurses, invokes the original twice, or hides legitimate nested calls. | Medium | Critical | Preserve a separate original symbol, direct-call it, use per-thread/per-hook recursion state, and test entry/exit/original counters. |
| G1-R04 | Guest device/resource addresses are reused or aliased, causing wrong native lifetime. `0x5E80` proves Fable differs from Unleashed's `0x5E00` device. | High | Critical | Use address generations and explicit alias/view relations. Validate construction, destruction, reference counts, lock renames, and failure cleanup before native ownership. |
| G1-R05 | `sub_82AAC208` is asynchronous queue processing, but queue ownership/order/coverage is unconfirmed. | Medium | High | Treat as discovery-only. Prove enqueue/consume ABI, threading, synchronization edges, and complete downstream coverage before promoting the engine seam. |
| G1-R06 | Big-endian fields, tiled resources, packed formats, vertex fetch, or EDRAM resolves are decoded incorrectly. | High | Critical | Capture proven fields plus hashes, correlate with ReXGPU/Xenia, build format-specific synthetic tests, and defer optimization. |
| G1-R07 | Fable shaders use XenosRecomp omissions or title-specific assumptions. XenosRecomp documents missing integer constants, dynamic indexing, mini fetch, memory export, and other gaps. | High | Critical | Complete a TU1 shader-feature census; fail conversion explicitly; differential-test converted shaders; retain ReXGPU for unsupported cases during qualification. |
| G1-R08 | Some guest path emits ring/PM4 directly and bypasses intercepted static methods. | Medium | Critical | Correlate all raw draw/copy/query/swap events to high-level event ancestry. Any unexplained material packet is a G2 coverage failure. |
| G1-R09 | Capture overhead changes scheduling, async I/O, frame pacing, or race outcomes while appearing visually correct. | Medium | High | Bounded host-only buffers, no guest-thread I/O, performance counters, repeated OFF/ON manual checkpoints, packet-order comparison, and fault-injection. |
| G1-R10 | Capture files contain proprietary shaders, textures, assets, or save-derived payloads. | High without controls | Critical | Store only under ignored `out/renderer-captures/` or external paths; metadata-only default; hard limits; staging audit; never commit payloads. |
| G1-R11 | A crash or disk limit leaves a trace that is silently treated as complete. | Medium | High | Checksummed append-only records, `.partial` segments, recovery scanner, explicit terminal status, and no inferred completion events. |
| G1-R12 | ReXGlue local SDK and public upstream drift changes ABI/packet behaviour. Local SDK HEAD is `956c6a8b5da4c54b9899a2593e9c67c26de30194`; public v0.10 reference is `c94f5ebdcb3c9d1a460ca48e04f9758448f8d518`. | Medium | High | Pin both identities in each trace; review SDK changes before replay/renderer work; keep G1 SDK read-only. |
| G1-R13 | GPL-covered UnleashedRecomp implementation is copied into a differently licensed project. | Low with current policy | Critical | Use it as architectural evidence only. Implement independently or make an explicit project licensing decision. MIT XenosRecomp/Plume and BSD-style ReXGlue/Xenia remain separately reviewable. |
| G1-R14 | A backend-specific IR locks the workstream to D3D12 and makes Vulkan impractical. | Medium | Medium | Normalize guest rendering intent and resource/state semantics; isolate D3D12 translation; include Vulkan capability review in schema changes. |
| G1-R15 | Ghidra merges/splits or prologue-only `.pdata` associations are mistaken for boundaries. Existing discovery documentation confirms these behaviours. | Medium | Critical | Continue the evidence hierarchy: TU1 bytes/control flow, generated output, runtime evidence, then Ghidra/historical corroboration. Validate exclusive ends independently. |
| G1-R16 | Automated gameplay introduces a new uncontrolled variable or wastes investigation time. | Low | Medium | User performs all interactive checkpoints. G2 supplies only exact launch/collection commands and a short manual checklist. |
| G1-R17 | The current plugin ABI is chosen for convenience and grows into a second general Xenos emulator. | Medium | Critical | Architecture gate rejects low-level replacement as the primary seam. Escalate only if higher boundaries are disproved with precise evidence. |

## Highest-priority G2 gates

1. Transparent forwarding at confirmed present `0x82BA34D8`.
2. Exact recovery of representative draw, resource update, shader bind, target,
   and resolve methods.
3. Complete correlation from those events to raw ReXGPU consequences.
4. Proven object generation/lifetime and endian-safe bounded decoding.
5. Capture OFF/ON behavioural equivalence and private-data containment.

Failure of any gate keeps native-backend implementation out of scope.
