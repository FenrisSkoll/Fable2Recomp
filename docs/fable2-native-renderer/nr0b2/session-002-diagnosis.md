# Session 002: notification and capacity diagnosis

Investigation only, 2026-09-11. Result remains **CAPTURE INCOMPLETE — SPECIFIC
EVIDENCE REQUIRED**. This note supplements the prepared-state handoff; original
preparation, capture, reports, log and launch claim remain unchanged. No new run,
preparation, build, runtime fix or workload selection was performed.

## Evidence and identity

Session: `C:\Dev\Fable2Recomp\out\nr0b2\sessions\nr0b2-oakfield-20260910-002`.
PID **29300**, actual process exit **0**, log `C:\Dev\Fable2Recomp\fable2-run-005.log`.
Fable inspected HEAD `e2c359c98a9c5019b307945618a14c0c723f7aec`; SDK inspected
HEAD `d90c10b49e95fc4098274d3676ea77c68ed44853`. Both branches are
`fable2-native-renderer-nr0b2-metadata`. Preparation pins SDK at that same HEAD
and Fable tooling at `58df26c7a0a39f56b71ecf36f4c0f4fda1517fc2`.

| Original evidence | Bytes | SHA-256 |
|---|---:|---|
| capture/metadata.bin | 25600000 | `9BA5105BBE877B78A7DA47F13D412D6037050595D1D645F08854EC53CCCF5BD9` |
| process.json | 3500 | `231E7DC0F293F45CE755A9222B28681224E4ACAA327200FC3E74FD305ACB0B7D` |
| analysis.json | 4922728 | `F9CA1C467F9A2EA7B2B186DF81796FE875C5917DBC96926F98C8C13009E8DD59` |
| preparation.json | 6937 | `E716D49723C1851FA6949DA0D473BC2F569257C5BECD50372EE721936943199C` |
| capture/status.txt | 77 | `E5398D7C3D54BF8554DBC5B20B04A35BFDB0A7CC7C45CBA81FF4BAD2E4649DF1` |
| fable2-run-005.log | 919414 | `6B71B134E444CA790AE36759C0D5CFE9587F9D39B60F27B0FDC15BF4C0A73490` |

The launch claim remains the original empty file. Loaded EXE/runtime/GPU module
paths and on-disk hashes match staging; read-only post-run preservation checks
pass. Configuration reparsing matches the original report. Device, RTV path,
bindless, tiled memory, 1x scale and async policy match NR0B-1. First host present
is **3440x1440**, versus NR0B-1's **3840x2160**; first guest output is **1280x720**.
Host extent is outside the analyzer's compared policy stages and is not proof
of an internal-resolution change or scene identity. Tracy remains optional.

## Internal state versus visible notification

User observation, accepted without reinterpretation:

> ARMED appeared in the console only AFTER I pressed Ctrl+Shift+F10.
> Before pressing it, I could see only “Wait for ARMED”.

The SDK `src/graphics/d3d12/command_processor.cpp:1657` initializes the observer
at the end of SetupContext. `src/graphics/metadata_recorder.cpp:29` preallocates
storage and sets Armed before starting the control worker. The worker registers
both hotkeys, then writes and closes ARMED in `status.txt` at line 195, before
polling any hotkey messages. F10 does not arm the recorder or write ARMED.

At lines 198–204, a queued hotkey is handled only if the foreground PID returned
by Windows matches the capture PID. An accepted F10 transitions Armed to
Recording, saves the steady-clock trigger time, writes RECORDING, and requests
a system MessageBeep. A populated capture with a nonzero trigger establishes
that this acceptance path ran. It implies the foreground check passed at message
handling; it does not establish focus at physical key-down or throughout the
window, nor which save or scene was visible.

[The helper](../../../tools/Invoke-Fable2GpuMetadata.ps1) polls a single mutable
status file. It retries unreadable/partial writes and prints changed text through
Write-Host. Its `observed_utc` is taken **after Write-Host returns**, not when the
console pixels become visible. There is no delivery acknowledgment, console
rendering timestamp, focus history or durable sequence of worker transitions.
The worker closes each status write; it is not retaining ARMED in its stdio
buffer until F10. The helper does not wait for F10 before polling/output.

| UTC evidence, 2026-09-10 | Meaning and limit |
|---|---|
| 23:17:00.4053688 | Process start recorded from the actual process |
| 23:17:00.5775533–00.5903532 | Required module paths/hashes observed; initial CIM query and required hashing had finished by this point |
| 23:17:01.063364 | Status file creation time; filesystem evidence, not exact Armed-transition time |
| 23:17:01.1173783 | Helper recorded its ARMED Write-Host return, about 0.712 seconds after process start; not proof the user saw it |
| 23:17:53.277029–53.286565 | Metadata file creation/last-write timestamps; output activity after capture stopped, not exact trigger/stop times |
| 23:17:53.4499939 | Helper recorded its STOPPED Write-Host return |
| 23:18:11.9863733 | Actual process exit, code 0 |

No UTC/steady-clock pair was recorded. Do not subtract capture timestamps from
UTC or assign the trigger an exact wall-clock time from output-file times.
The recorded polling/output attempt does not contradict the user's later
visibility observation. The exact cause of that visibility delay remains
**unknown**: console host delivery/visibility and physical shortcut timing were
not recorded. There is no evidence for a shortcut-dependent arming mechanism
or a long initial module-query delay in this session. The user's console-host
and continuous-visibility observation was requested to narrow this gap.

The normal monitor polls every 250 ms. RECORDING is overwritten by STOPPED after
recording and flush; it is absent from the helper's observed status list. A
22.7 ms recording can therefore finish between polls. This is a confirmed
notification-design weakness, although individual poll/write times are absent.
ARMED has no audible cue. The current implementation does **not** ensure the
required user-visible readiness before F10 or reliably deliver every explicit
start/stop transition.

## Why there is no complete interval

Independent binary unpacking and read-only `parse_capture` agree with the
unchanged original analysis. Structural validation passes; interval coverage
does not. The analyzer's complete-interval calculation is correct.

Header: `REXMETA1`, correct run ID/PID, 256-byte framing/records, maximum
100000 records, 33554432 bytes, 20000 decisions, three complete intervals,
5000000000 ns. Allocation: 25600000 bytes, with 200 bytes fixed object bookkeeping
reported separately. Header and terminal reserve two slots, leaving 99998 events.

| Steady-clock evidence | Absolute ns | Relative to trigger |
|---|---:|---:|
| Accepted trigger | 161136999692100 | 0 |
| First record, decision 1, submission 5251 | 161137005200100 | 5.508 ms |
| Sole XE_SWAP, sequence 492, submission 5251 | 161137005275000 | 5.5829 ms |
| Last event, sequence 99998, decision 2375, submission 5256 | 161137022392100 | 22.7000 ms |
| Stop observed / terminal | 161137022392200 | 22.7001 ms |
| Configured deadline | 161141999692100 | 5000 ms |

Terminal reason **4 = records**. Counts: **99998 events + header + terminal =
100000**, **2375 decisions**, **4322 deferred host operations**, **one swap**,
**zero complete intervals**, **25600000 bytes**, **zero rejected records**.
Reported append time is 1691700 ns total, 300 ns maximum; it excludes decoding,
rendering, scheduling and writer cost and is not a gameplay overhead result.

The first swap ends the initial partial interval: 25 decisions before it.
Another 2350 decisions and 99506 events follow, but no second boundary fits.
The final event is a requested-texture definition in decision 2375; its outcome
and remaining state are explicitly open. Zero rejection means no admitted
record was discarded; it does not describe the uncaptured tail as complete.

`Recorder::Emit` stops immediately after filling event slot 99998 and preserves
the reserved terminal. This is **record-capacity exhaustion**, not deadline,
cancellation, decision limit, 32 MiB limit, writer failure, shutdown or an analyzer
off-by-one. Common XE_SWAP instrumentation at `command_processor.cpp:968`
emitted the observed boundary. Consumer frame context changes from 1472 to 1473
and remains 1473 through the last draw. The observed stop already explains the
missing second boundary; there is no evidence requiring a missing-swap theory.
Scene suitability is unknown and unnecessary to explain this result.

Outcomes: 2258 deferred main draws recorded, 58 successful copy routes,
33 no-ops, 25 predicate rejections, one open decision. There are 4846 native
operation invocations, including 1532 whose deferred records precede the window
or are external. 1008 recorded operations lack in-window native execution.
Submissions 5251–5255 have issued records with zero Reset/Close/Signal HRESULTs;
5256 remains unissued in the capture. Existing fence observations reach 5254,
so completion of 5255 is unobserved. No GPU waits were added or inferred.

The design re-emits full state every decision. Exact decoded-field repetition
in this capture provides a concrete compaction target:

| State family | Emitted records | Distinct exact field tuples |
|---|---:|---:|
| Requested texture views | 15660 | 686 |
| Prepared texture views | 15646 | 686 |
| Samplers | 7825 | 101 |
| Color attachment state | 9036 | 18 |
| Shaders | 4700 | 88 |

These are metadata-equality counts, not resource lifetimes or proof that any
particular dictionary would capture a whole future interval. No candidate is
selected from the incomplete interval.

## Relationship and correction disposition

Capacity exhaustion and late **ARMED visibility** are independently assessed;
no causal connection is established. Capacity exhaustion does make the missing
**RECORDING notification** easier to explain: the state can be shorter than one
helper polling interval. Waiting longer or changing the analyzer cannot recover
the absent interval.

The diagnosis proposed the following bounded correction:

1. Give the control worker a distinct documented READY cue after successful
   registration, distinct STARTED and STOPPED cues, and preserve a fixed bounded
   sequence of control transitions for the helper to drain in order. Include
   run/PID, transition sequence, steady/UTC timestamp pairs, and stop reason.
   Keep all control output off the consumer path. Do not treat a console write
   as proof of user receipt. Verify the chosen cue is perceivable with game
   focus; merely polling faster or adding a flush cannot establish that.
2. Reduce repeated **existing metadata**, retaining the same five hard bounds:
   reuse immutable decoded state definitions through a fixed bounded state
   cache and packed per-decision references. References must reduce record
   count as well as bytes; one replacement record per old record is insufficient.
   Preserve carry-in, requested/prepared distinctions, handle/view changes,
   all decision outcomes and operation/submission joins. Budget all bookkeeping
   and definitions; no eviction or silent loss. No payloads or broader observation.
3. Validate independently with a synthetic host: delayed monitor polling and
   capture shorter than 250 ms must still deliver ordered READY/STARTED/STOPPED;
   test wrong foreground PID, repeated trigger, cancellation and output errors.
   Validate bounded state reuse/change/carry-in/references, exact record/byte
   limits and terminal reservation using a dense synthetic fixture informed by
   these observed counts. Retain idle deadline and partial-swap tests. Existing
   tests directly call Trigger and do not prove console delivery or real
   notification usability; rerunning them cannot settle the visibility gap.

A **fresh user-operated capture is necessary** after correction and focused
validation to obtain a complete interval. Neither a successful compact synthetic
fixture nor these partial records proves it will fit. Keep session 002 and the
unused session 001 intact; do not reuse either.

Only read-only parsing, source review and post-run preservation/configuration
checks were executed for this diagnosis. No historical results were edited.
ReXGlue remains the sole renderer. No renderer replacement, payload capture,
G2A restoration, source-save or baseline change, manifest/generated-source edit,
merge or push occurred. Unrelated manifest whitespace and libmspack changes
remain preserved.

Correction status, 2026-09-11: the bounded dictionary/bundle representation,
durable READY/STARTED/final transition history, distinct cues and delayed-poll
replay described above are implemented and synthetically validated. Fresh
session 003 is prepared and unlaunched. See
[implementation and validation](implementation-and-validation.md) and the
[new run card](user-run-card.md). This forward status does not change any
session 002 fact, hash, report or incomplete result.
