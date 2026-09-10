# NR0B-2 recorder design

Design recorded before implementation. ReXGlue remains the only renderer.
This observer is default-off and Windows/D3D12 scoped. Metadata is not replay
data. No title caller, material, character, producer or allocation lifetime is
inferred from a consumer thread, pointer, address or shader hash.

## Minimum observation chain

| Observation | Fields and the decision they support |
|---|---|
| Common type-3 dispatch before size/predicate filtering | Run-local decision ID, opcode, predicate and explicit result: count attempted work without treating successful returns as host draws |
| Common decoded draw and D3D12 IssueDraw | Primitive/index source/count/range, query state; distinguish rejection, no-op, copy, unavailable pipeline, preparation failure and main host command |
| Selected shaders and ConfigurePipeline result | Stage, existing XXH3-64 microcode identity/length, analysis availability, selected specialization, run-local pipeline handle and readiness: choose tractable shader pairs without reading shader bytes |
| Accepted render-target update and fixed function state | EDRAM base/pitch/samples, color/depth format, masks, blend/depth/stencil, viewport/scissor: identify required initial contents and output semantics |
| Used shader fetches and texture cache | Requested decoded fetch/view state and observed prepared/null state, only used slots; actual sampler parameters: identify resource needs and uncertainty across preparation failures |
| Resolve after existing GetResolveInfo | Source EDRAM, destination address/extent/layout/sample choice, clear intent and return/written range: identify aliases and GPU-produced inputs without new guest reads |
| Deferred command list operation methods | One record per draw/dispatch/copy/clear/query command, joined to current decision and submission; auxiliary operations remain distinct from the main guest draw |
| BeginSubmission / EndSubmission / CheckSubmissionFence | Existing current/completed IDs, ExecuteCommandLists and Signal result: distinguish recording, issuing and observed completion without additional waits |
| Consumer XE_SWAP entry | Boundary serial and frontbuffer metadata; initial partial interval ends at first observed boundary, then three complete boundary-to-boundary intervals end at the fourth. A consumer boundary is not a displayed frame |

No recurring presenter-thread observation is necessary for the first census;
reuse NR0B-1's configuration context and retain displayed-frame joins as unknown.
No resource producer/lifetime recorder, new page watch, shader analysis or hash
calculation is introduced. Numeric state fields are individually decoded;
raw packets, register arrays and payloads are excluded.

## Ordering and carry-in

One GPU consumer owns event order, decision context and immutable definitions.
Sequence IDs are record IDs. Definitions are emitted with every applicable
decision, including carried-in shader/fetch/attachment state. This intentionally
avoids an unbounded dictionary and stale cross-draw handles. Repeated values
are not lifetime identity; the analyzer may group equal metadata offline.
No referenced definition is evicted. Missing before-window state, absent
stages, not-applicable paths and unobserved preparation must remain distinct.
An interrupted decision has an explicit open edge, not a fabricated outcome.

The worker owns trigger, monotonic deadline, status and serialization. It never
reads GPU objects. Stop uses atomics and a producer publication handshake;
serialization begins only after recording is disabled and an in-flight append
has finished. No recorder lock, I/O or wait belongs on the consumer path.

## Trigger and state machine

Launch explicitly supplies a unique run ID and a nonexistent capture output
directory. Existing output roots are refused. A worker registers Ctrl+Shift+F10
(trigger) and Ctrl+Shift+F11 (cancel), with repeat suppression. Messages apply
only while this process owns the foreground window. Registration conflict is
an observer error, never permission to target another process. No network or
file polling is used for trigger delivery. Focus stays with the game.

States: disabled -> armed -> recording -> stopping -> stopped; errors produce
error status. Trigger is accepted once. Cancellation and shutdown stop the
observer only. Background status files/log messages and audible indications
report armed/recording/stopped/error. The launcher continues monitoring the
actual process until the user exits normally.

## Bounds and failures

Ceilings: five seconds from trigger (steady clock), three complete consumer
intervals, 20,000 decisions, 100,000 records including framing/terminal, 32 MiB
including framing/terminal. The first applicable ceiling stops acceptance.
The deadline worker expires without subsequent GPU events; each append also
checks the deadline. A terminal record and file header are reserved in advance.
Fixed-size decoded records and preallocated storage enforce a stricter memory
bound where needed; fixed object/thread/serialization bookkeeping is reported
separately. No wraparound, eviction or expanding queue is permitted.

Bounded recording may stop mid-decision/submission. Terminal counters preserve
reason, observations, bytes/high-water, rejection/loss and timing; unresolved
edges are explicit. Flush occurs in the worker after the observation window.
Writer/allocation/trigger failure disables the observer; it does not catch a
renderer exception, modify return values or terminate healthy gameplay. Abrupt
process exit may leave missing output/footer and must fail structural validation.

## Acceptance

Synthetic recorder and independent parser fixtures cover default-off, trigger
identity/repetition, idle deadline, exact capacities/reserved footer, swap
counting, carry-in/references, all result categories, auxiliary operations,
partial submissions, cancellation, writer failure and shutdown. Release builds,
existing configuration/NR0A/GPU checks and preservation preflight precede the
manual run. Synthetic timing is not a gameplay overhead or equivalence claim.
Actual capture validity, interval coverage, dependency completeness, gameplay,
visual correctness and disturbance are reported separately. At most one ordinary
indexed/textured candidate is considered; unresolved dependencies are acceptable.
