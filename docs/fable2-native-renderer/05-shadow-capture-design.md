# Non-invasive shadow-capture design

## Purpose and invariant

Shadow capture observes confirmed high-level operations while the existing
guest implementation and `rexgpu-xenos.dll` remain the only rendering path.
For every hooked call:

```text
validate and decode bounded metadata
  -> append a versioned observation
  -> call the exact original generated function once
  -> record return/outcome metadata
```

The invariant is stronger than “the game still runs”: with capture enabled,
the guest receives the same return values, memory writes, exceptions,
callbacks, command packets, interrupts, synchronization, and presentation as
with capture disabled. A recorder failure disables capture and forwards; it
must never fabricate a guest result or suppress a fault.

G1 designs this mode only. None of the switches or commands below is
implemented yet.

## Hook wiring and recursion

Prefer code-generation/link wiring over patching private executable bytes:

1. Preserve each generated implementation under an unambiguous symbol such as
   `sub_82BA34D8_original`.
2. Register the wrapper under the guest entry `0x82BA34D8` while keeping the
   original callable only by a host direct call.
3. Install the capture table before guest worker threads start. Publish the
   complete immutable table atomically; never patch entries piecemeal while
   guest code is running.
4. At shutdown, stop accepting new recorder events, wait for active wrappers,
   flush/recover the trace, restore registrations if runtime lifetime requires
   it, and then allow normal GPU shutdown.

Each wrapper uses a per-thread, per-hook forwarding guard. Re-entry into the
same wrapper calls the original directly without recording again. Calls from
one hooked operation into a different hooked operation remain visible because
they are genuine nested guest operations. Recorder code must not dispatch guest
functions, allocate through guest heaps, emit graphics work, or invoke the
presenter.

The wrapper preserves the complete guest ABI: `PPCContext`, nonvolatile state,
stack alignment, return registers, condition state, guest exceptions, and
out-parameters. The forward path is direct and never resolves the wrapper
again through the guest dispatcher.

## Guest pointers and endian handling

- Perform unsigned overflow-safe `address + length` validation before every
  read.
- Translate guest virtual/physical addresses only through existing ReXGlue
  memory facilities. Validate the complete range and intended access; do not
  assume the first byte proves the final page is mapped.
- Decode Xbox big-endian scalars explicitly. Preserve the raw numeric guest
  address separately from decoded values.
- Read only fields proven for the exact function/version. Unknown tail bytes
  are not copied “for later”.
- Treat mutable input as a point-in-time observation. If a method semantically
  consumes data during forwarding, optionally record bounded pre- and
  post-forward digests, not an unbounded memory dump.
- A bad optional pointer produces an event decode status and still forwards.
  A pointer required by the guest implementation is not pre-emptively changed
  or sanitized by capture.

## Object and resource identity

Guest addresses are reusable, so address alone is not an identity. Maintain a
capture-only table keyed by:

```text
(capture_epoch, inferred_type, guest_address, generation)
```

Creation increments the generation for an address. Destruction closes it.
Record parent/device, allocation size, dimensions/format/usage only when those
fields are proven, plus alias/view relationships and reference events. Unknown
types use an opaque identity and are never coerced to texture/buffer/surface.

Lock/unlock payloads, once their hooks are confirmed, belong to the resource
generation and lock sequence. Overlapping locks, partial rectangles/ranges,
renames, shared backing, and address aliasing must remain explicit. Resource
metadata changes are events rather than in-place rewrites of earlier history.

## Ordering, frames, and operation model

Every observation receives:

- a process capture epoch;
- a global monotonically increasing `event_sequence` assigned at hook entry;
- guest thread identity and per-thread sequence;
- hook guest address and call depth;
- entry/exit status and original return registers;
- an optional frame, command-list, resource-generation, and parent-event ID.

Do not infer total execution order from timestamps. Use the global sequence for
observation order and record synchronization edges when confirmed APIs expose
them. Timestamps are diagnostic metadata only.

`present_begin` at confirmed `0x82BA34D8` opens/closes frame attribution only
after correlation proves its exact timing. Draws, clears, target changes,
resolves/copies, queries, waits, and nested command-list events retain their
individual sequence numbers. Operations outside any known frame use `null`
frame identity rather than being silently attached to the nearest present.

The normalized IR is descriptive in the first capture versions. It records
what the guest requested, including redundant state changes. Optimization and
state coalescing are forbidden in capture.

## Shader, pipeline, and payload identity

- Shader identity includes stage, guest address/generation, byte length,
  `SHA-256`, and optionally XXH3-64 for comparison with existing tools. Hashes
  never substitute for stage/size and collision checks.
- Pipeline identity is a canonical hash over schema-versioned normalized state,
  shader identities, vertex declaration, targets, and formats. Preserve the
  contributing fields so a hash is auditable.
- Do not commit shader bytes. Captured shader or resource payloads are private
  local chunks.
- Default payload capture is metadata plus hashes. An explicit bounded-data
  profile may copy only the ranges required for resource-update validation.
- Configure hard per-event, per-frame, and per-run byte limits. On overflow,
  emit a deterministic `payload_omitted` record with requested size and reason,
  then continue forwarding.

## Versioned trace format

Use an append-only directory, for example:

```text
out/renderer-captures/<patched-image-sha256>/<capture-id>/
  capture.json
  events-000000.jsonl.partial
  chunks/
    <sha256>.bin.partial
```

`capture.json` records schema `fable2-render-shadow`, schema version, exact TU1
and repository identities, hook inventory digest, configuration, limits,
backend/plugin identity, start/end state, and segment hashes. JSON uses UTF-8,
sorted keys where objects are canonicalized, decimal JSON numbers for logical
values, and uppercase `0xXXXXXXXX` strings for guest addresses. Large binary
payloads are content-addressed chunks with an explicit byte order, logical
range, size, SHA-256, and compression version.

Each JSONL event has a length-delimited or independently checksummed envelope.
Segments are finalized by flush, hash, and atomic rename from `.partial` only
at a known durable boundary. On crash, a read-only recovery scanner accepts
complete checksummed records, reports the truncated tail, and never invents an
`end` or `present_complete` event. A final manifest marks the capture
`complete`, `crashed`, `aborted`, `limit_reached`, or `recorder_error`.

Schema changes are additive within a version. Meaning changes increment the
major schema. Readers reject unknown major versions and retain unknown fields
when rewriting is ever supported.

## Performance and failure containment

- Use bounded per-thread producer buffers and one host-only writer thread.
- Never block a guest rendering thread on file I/O. If buffers fill, emit a
  counter/omission marker through reserved capacity and continue forwarding.
- Allocate recorder memory from host facilities before or outside hooks.
- Metadata-only mode is the default. Payload capture, raw packet correlation,
  and screenshot checks are separate explicit profiles.
- Measure wrapper-only, encode, queue, flush, bytes/frame, dropped events, and
  high-water marks. Record these in the footer.
- Catch only recorder-owned host failures. Do not catch or transform exceptions
  raised by the original guest implementation.
- After a recorder failure, atomically set capture state to `failed-open`; all
  wrappers become direct forwarders for the rest of the process.

## Privacy and repository policy

All captures are private game-derived data. Store them only under the already
ignored `out/renderer-captures/` hierarchy or an explicit external directory.
Before G2 enables capture, verify with:

```powershell
git check-ignore .\out\renderer-captures\probe
```

If a future output path is outside an already ignored tree, add a narrow
`.gitignore` rule before use. Never stage event traces, chunks, shader payloads,
screenshots, saves, XEX-derived dumps, or Ghidra databases. Committable evidence
is limited to schemas, tools using synthetic fixtures, hashes, addresses,
ranges, counts, and provenance metadata.

## Explicit off switch

Capture is off by default in every build. The proposed runtime contract is:

- unset or `FABLE2_RENDER_SHADOW_CAPTURE=0`: wrappers are not installed;
- `FABLE2_RENDER_SHADOW_CAPTURE=metadata`: confirmed wrappers record metadata;
- `FABLE2_RENDER_SHADOW_CAPTURE=bounded`: metadata plus explicitly limited
  payload chunks;
- invalid values: log one error and stay off.

An additional build option may omit capture code entirely, but runtime default
off is still required in capture-capable builds. No normal helper changes its
default behaviour.

## Behavioural-equivalence proof

Capture is accepted only after all of the following pass:

1. Synthetic ABI tests compare wrapper-off and wrapper-on register, stack,
   return, exception, and out-parameter behaviour for success/failure paths.
2. An OFF build/run proves no wrapper registration, recorder thread, file, or
   packet change.
3. Each hook has entry/exit counters proving one original invocation per outer
   call; recursion tests prove nested different hooks remain visible.
4. ReXGPU correlation records identical ordered draw/copy/query/wait/swap
   packet counts and relevant register/payload hashes at a controlled manual
   checkpoint, excluding only explicitly documented volatile timing fields.
5. Capture ON/OFF runs from the same TU1 inputs and user checkpoint have the
   same guest-visible result, present count, fatal/warning outcome, shutdown,
   and stable-frame image hashes or a reviewed pixel-difference tolerance.
6. Repeating the same controlled capture produces a deterministic normalized
   event stream after removal of declared volatile fields.
7. Recorder fault injection (disk full, limit, malformed optional pointer,
   writer failure, process crash) yields a recoverable partial trace while the
   original renderer either continues unchanged or fails for the same guest
   reason as capture-off.

Merely reaching gameplay is not equivalence proof.

## Proposed future manual collection command

After G2 implements and documents the environment contract, the user would run
this from `C:\Dev\Fable2Recomp` in the established developer PowerShell:

```powershell
$captureRoot = Join-Path `
    (Resolve-Path '.\out').Path `
    'renderer-captures\g2-manual-checkpoint-001'

$env:FABLE2_RENDER_SHADOW_CAPTURE = 'metadata'
$env:FABLE2_RENDER_SHADOW_OUTPUT = $captureRoot
$env:FABLE2_RENDER_SHADOW_MAX_MIB = '256'

fable2-run

Remove-Item Env:FABLE2_RENDER_SHADOW_CAPTURE
Remove-Item Env:FABLE2_RENDER_SHADOW_OUTPUT
Remove-Item Env:FABLE2_RENDER_SHADOW_MAX_MIB
```

This command is a reserved design, not a currently valid G1 feature. The user,
not automation, controls gameplay. The short checkpoint checklist is:

1. Load the agreed TU1 save/checkpoint and wait for a stable scene.
2. Perform one agreed camera motion and one menu-free scene transition, then
   exit through the normal close path.
3. Report the numbered `fable2-run-NNN.log`, capture directory, visible result,
   and whether input/pacing differed from the capture-off control.

G2 must provide a matching capture-off command and exact scene/checkpoint
description before asking for this manual run.
