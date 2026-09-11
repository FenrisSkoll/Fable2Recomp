# Correction implementation, validation and prepared identities

**CONFIRMED, source/build/synthetic/preflight evidence.** Session 002 is the
preserved failed runtime capture described in
[its diagnosis](session-002-diagnosis.md). The corrected runtime has not been
launched. Its actual interval coverage, cue perception and disturbance remain a
fresh user-run gate.

## Demonstrated failure and density basis

Read-only parsing of the original session 002 `REXMETA1` capture confirms the
accepted trigger, first record at 5.508 ms, sole swap at 5.5829 ms and records
stop at 22.7001 ms. It contains exactly 99,998 events plus header and terminal,
2,375 decisions, one swap, zero complete intervals, no rejected records and an
open decision 2375. Submissions 5251–5255 are observed, completion reaches
5254, and submission 5256 remains unresolved. The terminal reason is record
capacity. The backward-compatible parser still reports the original capture as
structurally valid and capacity limited; no historical output was rewritten.

The highest-volume decoded state families and their exact value repetition were:

| Event type | Session 002 records | Distinct exact tuples |
|---|---:|---:|
| texture requested | 15,660 | 686 |
| texture prepared | 15,646 | 686 |
| color attachment | 9,036 | 18 |
| sampler | 7,825 | 101 |
| shader | 4,700 | 88 |
| pipeline | 4,518 | 155 |
| vertex layout | 3,087 | 30 |
| vertex fetch | 3,087 | 738 |
| geometry | 2,350 | 425 |
| submission snapshot | 2,350 | 9 |
| shader selection | 2,259 | 57 |
| processed geometry | 2,259 | 617 |
| targets | 2,259 | 33 |
| depth | 2,259 | 32 |
| viewport | 2,258 | 20 |
| fixed state | 2,258 | 107 |
| binding result | 2,258 | 1 |
| index | 1,792 | 602 |

Exact read-only projection through the v2 representation keeps all 14,137
ordered non-state events and all decisions, while replacing repeated state with
4,405 immutable definitions, 3,893 bundle-definition records and 2,350 bundle
references. The projected capture is 24,785 events plus framing, 6,345,472
bytes, versus 99,998 events and 25,600,000 bytes: 75,213 fewer events, a
**75.215%** reduction. This equality is bounded decoded-metadata reuse, not
resource-lifetime or payload compression.

## Corrected recorder and analyzer

The SDK now writes `REXMETA2`. Reusable geometry, shader, pipeline, binding,
attachment and submission state is published once as an immutable exact
definition. Each decision keeps its ordered definition IDs through a bounded
state bundle and one compact reference. Individual decisions, outcomes,
resolves, deferred/native operations, submissions, completions and swaps remain
ordered records. FNV-1a 64 is only a bounded-table lookup accelerator; exact
type/count/field equality makes collisions safe. Definitions and bundles are
never evicted, mutated or silently overwritten. A transaction that cannot
publish its new definition and valid reference stops cleanly with reported loss.

The hard ceilings remain five seconds, three complete consumer intervals,
20,000 decisions, 100,000 total records and 32 MiB. Binary storage remains
25,600,000 bytes. Fixed dictionary/bundle tables, decision workspace,
bookkeeping and bounded transition history are included in the initialization
budget check. Terminal reservation and initial-partial semantics are unchanged.

The analyzer selects its reader from the magic/version. It retains the frozen
v1 interpretation for session 002, explicitly rejects unknown versions, and for
v2 validates definition-before-reference, exact immutable definitions, complete
ordered bundle chunks, unknown/duplicate references, sizes/padding, terminal
counters, open decisions and partial submissions. Its report separates wire
records, dictionary/reference accounting and logical expanded state. Capacity
never becomes a complete result simply because retained references validate.

## Durable notification contract

The control worker publishes READY only after Ctrl+Shift+F10 and
Ctrl+Shift+F11 both register. An accepted foreground F10 begins capture and
publishes STARTED exactly once with that same monotonic trigger timestamp.
STOPPED appears only after recording ends and `metadata.bin` closes. CANCELLED
and ERROR are distinct final transitions.

Every transition is an immutable, atomically renamed JSON file under
`capture\transitions`, with run/PID, sequence, recorder monotonic timestamp,
nearby wall/monotonic correlation, foreground/acceptance data and final
reason/flush/error fields. The helper drains unseen sequences instead of
sampling the overwritten compatibility status. The validated cue mapping is:

| State | Worker-only cue |
|---|---|
| READY | two rising tones |
| STARTED | one high tone |
| STOPPED | three rising tones |
| CANCELLED | two falling tones |
| ERROR | three falling tones |

Sound failure does not alter the durable state. No cue, file I/O, lock or wait
runs on the GPU consumer. Console visibility and human cue perception remain
runtime observations rather than claims from unit tests.

## Source and build relationship

Both branches are `fable2-native-renderer-nr0b2-metadata`.

- SDK correction: `821aab344f1a3010126f08e9a7d06bf7bd336027`, tree
  `357b341bed4be953755e36e729fd9b299f1c94b1`, descended from the accepted
  NR0B-2 tip `d90c10b49e95fc4098274d3676ea77c68ed44853`.
- Fable durable analyzer/launcher correction:
  `bb190cde7dcd61e9d0989919982cfd0f8779cad9`, tree
  `085ba79a65f7095c1b6c4bb040cf95cb0b706f02`, following diagnostic commit
  `36a64900facf2cb14e0f151c90b39b364c254131`.

Final documentation HEAD/tree values belong in the external handoff, not in
their own commit. SDK Release targets `rexruntime rexgpu-xenos unit_tests` were
built with the existing Windows AMD64 Release configuration, D3D12 enabled and
Vulkan disabled. No Fable executable, ABI or generated source changed, so the
accepted Release `fable2.exe` is staged unchanged.

## Focused validation

| Check | Result |
|---|---|
| SDK Release `rexruntime rexgpu-xenos unit_tests` | PASS |
| SDK `[gpu-metadata],[gpu-config]` tests | PASS, 25 cases / 186 assertions |
| Independent Fable metadata/config/NR0A/GPU tests | PASS, 37 tests |
| Durable local replay after delayed polling | PASS, READY -> STARTED -> STOPPED |
| Preserved session 002 v1 parse and exact v2 projection | PASS |
| Fresh session 003 preparation and preflight | PASS |
| NR0A preserved-state verifier and G1 candidate verifier | PASS, 10 pins / 44 symbols / 70 local links / 19 immutable links; 11 candidates |
| Default GPU-reference verifier | PASS, 0 warnings |
| Strict historical GPU-reference verifier | Expected seven retained failures, 0 warnings; no new failure |

The dense C++ fixture preserves 2,350 decisions, one-to-many host/native
relationships and one complete consumer interval. Its v1-equivalent pattern is
101,051 events; v2 writes 26,816 events plus framing, 6,865,408 bytes, a
**73.463%** event reduction. Its v1-equivalent event demand exceeds session
002's 99,998-event capacity while the v2 result fits the unchanged limits. This
is a synthetic capacity and semantic test, not evidence of a Fable frame or
runtime duration.

Focused tests also cover default-off operation, READY after successful shortcut
registration, READY-before-STARTED, accepted/rejected/repeated triggers, a
capture shorter than 250 ms, polling delayed by 300 ms, deadline without later
GPU events, exact record/byte/decision bounds, terminal reservation,
definition-before-use, equality reuse, conflicting values under a forced hash
collision, dictionary exhaustion, no eviction, carry-in, partial/complete
intervals, open decisions/submissions, one-to-many operations, cancellation,
writer failure, shutdown, cue dispatch mapping and reused-root refusal.

The final synthetic call measurement reported disabled `Emit` at 1.1864
ns/call and enabled `Emit` at 51.81 ns/call, writing 2,560,512 bytes. It excludes
state decoding, rendering, serialization and scheduling and does not establish
gameplay overhead or negligible disturbance.

## Fresh prepared session

Session:
`C:\Dev\Fable2Recomp\out\nr0b2\sessions\nr0b2-oakfield-20260911-003`.
Preparation JSON SHA-256:
`0A3B7FE11E5B0DFB367610A04D54C9A6257CA7FA8034084E52D86D3DE74380CC`.
The session has no launch claim and no capture directory. Session outputs and
the new checkpoint are ignored by Git.

The source is the authoritative protected NR0B-1 checkpoint
`out\nr0b1\checkpoints\nr0b1-oakfield-20260910-001\user-data`. The new protected
and writable copies match all 14 relative paths, sizes and hashes. Main save:
415,039 bytes,
`13FC340F6869DA73CB958BA36CB50905E29B8FBEA073CEFF46490DB4A9812489`.
The copied shader cache is documented; driver-cache state remains unknown.

| Staged file under session `runtime` | Bytes | SHA-256 |
|---|---:|---|
| fable2.exe | 105042944 | `1642ED03BD8B117A8FED6E9FF912AD49CBF0E91A4E1D226B20C266925E3FF2C9` |
| rexruntime.dll | 10380288 | `1CEB686A2D9C704491D45C47DA34701E00CA649AE6177C7E1171C980F1EF56D7` |
| rexgpu-xenos.dll | 2880512 | `C0A38DA1E535669FFC61543A2E6338A8B9D9FC20BBC1CF7D337C8D1A6E477771` |
| TracyClient.dll (optional staged file) | 232960 | `FDBE7A329E1B06A86FE61A2C5BE6B335F32F9BBCA7E05F7B183A35C515D2D1A5` |

`llvm-readobj --coff-imports` inspected the staged EXE, runtime and corrected
GPU plugin. None imports Tracy, so the same three modules remain required and
Tracy stays optional for these binaries. The ignored import report SHA-256 is
`8AF925A9FA83B6EBDD6BE6A6D9124251502B92956DC0B88142DA5C1E5CD943CD`.

The baseline remains EXE
`1642ED03BD8B117A8FED6E9FF912AD49CBF0E91A4E1D226B20C266925E3FF2C9`,
runtime `71BB1BA29413773226245B1D05F40379561C974F8E2EA4E5BB994D6DC3591793`
and GPU `70492C8612DEF79C9E3946817F424111FAB2155A3BE63CEA6E717CA73893ADC5`.
The staged correction is separate and does not replace those files. No
exe-adjacent configuration exists. The requested run retains Xenos/D3D12, RTV,
bindless, tiled shared memory and scale 1x; effective runtime confirmation awaits
the actual process.

Session 002, its capture hash
`9BA5105BBE877B78A7DA47F13D412D6037050595D1D645F08854EC53CCCF5BD9`,
its launch claim and reports remain unchanged. The unused session 001 also
remains untouched.

The final strict historical verifier retained exactly the same seven documented
failures and zero warnings: absent `fable2-run-047.1.log`,
`fable2-run-047.log`, `fable2-run-048.log`; historical baseline EXE and GPU
hash comparisons; and the G1.6A and G1.6B active-GPU comparisons. There was no
new provenance failure. No historical hash or missing log was replaced.
