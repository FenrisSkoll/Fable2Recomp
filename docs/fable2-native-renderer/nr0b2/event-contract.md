# NR0B-2 event contract and interpretation

The [pre-implementation design](recorder-design.md) sets the scope. The SDK's
`docs/gpu-metadata-recorder.md` describes the implemented writer and hotkey
transport. The strict field-order reader is
[Fable2GpuMetadata.py](../../../tools/Fable2GpuMetadata.py), `FIELDS`, with
independent [synthetic tests](../../../tests/test_fable2_gpu_metadata.py).

Wire format: little-endian, 256-byte header and 256-byte records; header magic
`REXMETA1`, run ID and PID. Event fields are decoded uint64 metadata; signed
values use two's-complement and explicitly named float-bit fields use IEEE-754.
Unused fields/padding must be zero. No raw shader, register, packet, constant,
texture, geometry or attachment arrays occur. A terminal record is mandatory.

| Record family | Identity and later decision |
|---|---|
| Decision / outcome / geometry / index / processed / vertex layout / vertex fetch | Decision begins before predicate filtering. Opcode, primitive/count/source, query request and rejection indicators distinguish ordinary work from query/copy/no-op paths. Existing processed geometry, fetch addresses/ranges/endian and analyzed stride/attribute count identify geometry needs; actual vertex attributes and index contents remain absent |
| Shader / selection / pipeline | Stage + XXH3-64 + microcode byte length identify original bound shaders. Selection separates bound from applicable stages. Existing interpolation/output/depth/memexport/constant-count/dynamic-addressing fields flag complexity. Specialization bits and pipeline handle are build/run scoped. Result 0=request, 1=unavailable, 2=not-ready, 3=existing readiness gate passed; no new shader analysis or hashing |
| Texture requested / texture prepared / sampler / bindings | Only translated shader-used views/slots. Requested decoded fetch metadata includes address, dimension, format/layout, mip, signs/swizzle and LOD fields. Prepared cache key/size/descriptor/sign state distinguishes available, incompatible, null and unobserved special views. Sampler parameters are effective decoded cache parameters. UpdateBindings success is separate from preparation and later residency/host recording |
| Targets / color / depth / viewport / fixed state | Accepted EDRAM pitch/sample/path/masks and formats, normalized depth/stencil and color masks, blend operations, host formats, viewport/scissor and dynamic fixed-function values identify required input/output semantics. Raster culling/mode and index offset/bounds support candidate interpretation. Initial contents and polygon-offset magnitudes are not supplied |
| Resolve / resolve result | Existing GetResolveInfo result supplies source tile region/sample/format, decoded destination extent/format/endian/pitch, sample choice and clear intent, including depth-clear source. Result status 0=info failure, 1=empty/no-op, 2=completed path with copy/clear success and written range. No new memory read or GPU readback |
| Host / execute | One-to-many auxiliary and main operations. Join `(submission, deferred byte offset)`; main_guest_draw distinguishes the primary guest draw. Execute separately states whether the native command was invoked under the existing pipeline-null branch. Native invocation does not prove submission/completion |
| Submission / submit / completion / swap | Existing current/open/completed/frame context supplies carry-in. Submit records existing Reset/Close/Signal HRESULTs after ExecuteCommandLists. Completion comes only from already existing fence observations. Swap is the consumer boundary and frontbuffer metadata, not a displayed frame |

Sequence is immutable record ID. Decision-local definitions are keyed by family,
stage and applicable slot/view; they are emitted afresh rather than maintained
in a growing dictionary. The analyzer rejects missing, duplicate, changed-kind,
closed-decision and invalid reference relationships. A zero decision explicitly
marks unobserved pre-window/partial decision context. An operation execution
without a recorded offset is external, not silently attributed to another draw.

Known absence differs from missing observation: shader `present=0` is bound
absence; selected pixel stage 0 means not applicable to that draw; missing shader
or selection records mean unobserved, including early returns. Texture state 0
has only its five identity/state fields, state 1 is compatible, state 2
incompatible. UINT32_MAX ordinary descriptor means null fallback; UINT64_MAX
special descriptor or host format means unavailable/not applicable as specified
by that path. Cached-resource pointer existence alone does not prove a bound
texture. No address or pointer establishes an allocation generation.

First swap ends the initial partial interval (interval 0). Intervals 1–3 are
complete only between successive observed boundaries; the fourth boundary
stops capture. A deadline/capacity/cancel stop may leave a final partial interval,
open decision and unresolved native/submission/completion edges. Terminal totals
include exactly one header and terminal. Default preallocation is 25,600,000
bytes, below the 32 MiB ceiling because 100,000 fixed records is stricter.
Fixed object bookkeeping and thread/path/FILE overhead are reported separately.

The logical deadline is five seconds from steady-clock trigger. A worker stops
acceptance without waiting for another GPU event; each append also enforces
the cutoff. Scheduled worker notification/flush can finish later, and observed
service lag is reported. Zero rejected records means no admitted metadata loss;
it does not mean complete intervals, complete dependencies or negligible cost.
Abrupt process failure or writer error can leave incomplete/no output and fails
structural validation. Healthy game execution is never terminated by capture.

Original NR0B-1 configuration reporting is reused unchanged. Recurring presenter
metadata, producer/resource lifetimes, title associations and payloads are not
included. A candidate is only a next evidence target; no replay-ready label or
native-renderer qualification follows from a structurally valid capture.
