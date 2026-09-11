# NR0B-2 event contract and interpretation

The [pre-implementation design](recorder-design.md) sets the scope. The SDK's
`docs/gpu-metadata-recorder.md` describes the implemented writer and hotkey
transport. The strict field-order reader is
[Fable2GpuMetadata.py](../../../tools/Fable2GpuMetadata.py), `FIELDS`, with
independent [synthetic tests](../../../tests/test_fable2_gpu_metadata.py).

Wire format: little-endian, 256-byte header and 256-byte records. Corrected
captures use magic `REXMETA2` and explicit format version 2; the analyzer keeps
the frozen `REXMETA1` reader for preserved session 002 and rejects any other
magic/version. The v2 header carries run ID, PID, hard limits and bounded
dictionary/workspace/control capacities. Event fields are decoded uint64
metadata; signed values use two's-complement and explicitly named float-bit
fields use IEEE-754. Unused fields/padding must be zero. No raw shader,
register, packet, constant, texture, geometry or attachment arrays occur. A
terminal record is mandatory.

| Record family | Identity and later decision |
|---|---|
| Decision / outcome / geometry / index / processed / vertex layout / vertex fetch | Decision begins before predicate filtering. Opcode, primitive/count/source, query request and rejection indicators distinguish ordinary work from query/copy/no-op paths. Existing processed geometry, fetch addresses/ranges/endian and analyzed stride/attribute count identify geometry needs; actual vertex attributes and index contents remain absent |
| Shader / selection / pipeline | Stage + XXH3-64 + microcode byte length identify original bound shaders. Selection separates bound from applicable stages. Existing interpolation/output/depth/memexport/constant-count/dynamic-addressing fields flag complexity. Specialization bits and pipeline handle are build/run scoped. Result 0=request, 1=unavailable, 2=not-ready, 3=existing readiness gate passed; no new shader analysis or hashing |
| Texture requested / texture prepared / sampler / bindings | Only translated shader-used views/slots. Requested decoded fetch metadata includes address, dimension, format/layout, mip, signs/swizzle and LOD fields. Prepared cache key/size/descriptor/sign state distinguishes available, incompatible, null and unobserved special views. Sampler parameters are effective decoded cache parameters. UpdateBindings success is separate from preparation and later residency/host recording |
| Targets / color / depth / viewport / fixed state | Accepted EDRAM pitch/sample/path/masks and formats, normalized depth/stencil and color masks, blend operations, host formats, viewport/scissor and dynamic fixed-function values identify required input/output semantics. Raster culling/mode and index offset/bounds support candidate interpretation. Initial contents and polygon-offset magnitudes are not supplied |
| Resolve / resolve result | Existing GetResolveInfo result supplies source tile region/sample/format, decoded destination extent/format/endian/pitch, sample choice and clear intent, including depth-clear source. Result status 0=info failure, 1=empty/no-op, 2=completed path with copy/clear success and written range. No new memory read or GPU readback |
| Host / execute | One-to-many auxiliary and main operations. Join `(submission, deferred byte offset)`; main_guest_draw distinguishes the primary guest draw. Execute separately states whether the native command was invoked under the existing pipeline-null branch. Native invocation does not prove submission/completion |
| Submission / submit / completion / swap | Existing current/open/completed/frame context supplies carry-in. Submit records existing Reset/Close/Signal HRESULTs after ExecuteCommandLists. Completion comes only from already existing fence observations. Swap is the consumer boundary and frontbuffer metadata, not a displayed frame |
| State bundle / state-bundle reference (v2) | Decision-zero bundle records contain ordered immutable definition IDs in chunks of at most 23. The bundle's first sequence is its ID. One decision-local reference applies the complete bundle before the main draw/outcome. Definitions and every chunk must precede first reference |

Sequence is immutable record ID. In v2 the first exact reusable state record is
an immutable decision-zero definition whose sequence is its run-local ID. Exact
equal definitions and equal ordered bundles reuse IDs. A bundle reference does
not collapse or reorder the decision, outcome, resolve, deferred operation,
native execution, submit, completion or swap records. The analyzer expands the
referenced state for the decision while retaining the definition and bundle
reference sequences.

The analyzer rejects missing/unknown definitions, decision-local definitions,
duplicate conflicting definitions, missing or reordered chunks, duplicate
decision bundle references, invalid sizes, truncated records and nonzero
padding. Definitions must precede first use. There is no external-definition
table in v2; an unavailable observation remains encoded in the existing state
fields rather than through an unresolved numeric ID. A zero decision on ordered
operation records still marks unobserved pre-window/partial context. An operation
execution without a recorded offset is external, not silently attributed to
another draw.

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

The v2 terminal adds immutable-definition/reuse, bundle-definition/reuse,
logical-reference, bounded-owned-storage and accepted foreground-PID counters.
The analyzer verifies these totals against the wire representation. A records,
bytes or dictionary-capacity stop remains incomplete even when every retained
reference is structurally valid. Dictionary exhaustion must report loss and
cannot publish a dangling reference.

The logical deadline is five seconds from the accepted STARTED steady-clock
timestamp. A worker stops acceptance without waiting for another GPU event;
each append also enforces the cutoff. Scheduled worker notification/flush can
finish later, and observed service lag is reported. Zero rejected records means
no admitted metadata loss; it does not mean complete intervals, complete
dependencies or negligible cost. Abrupt process failure or writer error can
leave incomplete/no output and fails structural validation. Healthy game
execution is never terminated by capture.

Version 2 also requires the bounded `rex-gpu-metadata-transition-v1` history.
Files are atomically published in sequence and scoped by run ID/PID. READY must
precede an accepted STARTED. STOPPED requires a matching terminal reason/time and
successful flush. CANCELLED requires the cancelled terminal and successful
partial flush; ERROR explicitly reports unsuccessful completion. Bounded
REJECTED records describe wrong-foreground or repeated control attempts without
changing state. The helper's recorded replay must equal the complete history,
so states that occur between polls remain observable after the fact.
Wall/monotonic pairs correlate clock domains without claiming exact audible or
console-delivery time.

Original NR0B-1 configuration reporting is reused unchanged. Recurring presenter
metadata, producer/resource lifetimes, title associations and payloads are not
included. A candidate is only a next evidence target; no replay-ready label or
native-renderer qualification follows from a structurally valid capture.
