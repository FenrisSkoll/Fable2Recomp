# Implementation, validation and prepared identities

**CONFIRMED, source/build/synthetic/preflight evidence only.** No NR0B-2 game
process or runtime capture has occurred. Configuration/scene/loaded-artifact
verification for the new run is pending user operation.

The SDK implements a default-off preallocated recorder and independent control/
deadline/writer thread. Narrow consumer sites record decisions and explicit
returns, bound/selected shader identities, used decoded texture/fetch/sampler
state, accepted attachment/depth/output state, resolve results, auxiliary/main
deferred operations, native invocation and submission/completion/swap edges.
No renderer return value, original branch, GPU wait or guest work is changed.
In particular, native deferred replay suppression is observed rather than
mistaken for successful GPU execution.

Fable adds preparation/preflight, exclusive launch/log claims, process/module
monitoring, strict offline parsing and at-most-one conservative nomination for
later evidence collection. NR0B-1 helpers and reports remain unchanged. The
existing source-save, session and log allocation contracts are reused.

## Local source/build relationship

SDK implementation: `ab602bd70a6edee877496359e19f7510c19cc83a`, tree
`cad179a4c273f1172e5994ea90696d520018b0bd`, on
`fable2-native-renderer-nr0b2-metadata`, directly descended from accepted
NR0B-1 `06c4b7002a449ad4d173ec90c625e490ed03fe74`.

Final SDK source includes the reviewed submission carry-in correction:
`d90c10b49e95fc4098274d3676ea77c68ed44853`, tree
`e970f5670a143b1c1a209b765c717ac98398502e`. It keeps the recorder's current
submission synchronized while armed, including a trigger immediately after
EndSubmission. Affected Release targets rebuilt successfully, recorded in
SDK `out/nr0b2-build-carry-in.log`.

Fable tooling/preparation source:
`58df26c7a0a39f56b71ecf36f4c0f4fda1517fc2`, tree
`6cdee8a32b95c4f7bbe4174ca6a7b7c59eaad7e4`, on the same branch name, directly
descended from accepted `d292ccc36cc4b97d4171431308cedec7e5591a28`.
The subsequent prepared-state documentation commit does not require recreating
the session. Exact final HEAD/tree values belong in the final handoff, not in
their own commit.

SDK Release build used the existing Ninja Multi-Config/Clang configuration,
D3D12 ON, Vulkan OFF. Targets: `rexruntime rexgpu-xenos unit_tests`. The
post-commit build confirms no work remains. Artifacts describe exact compiled
source content and disk bytes; a baked SDK version string alone is not evidence
of that content. The existing accepted Release Fable EXE is copied unchanged:
no Fable C++/application ABI/codegen input changed, and GPU-private recorder
classes remain inside the plugin. No Fable build/codegen, install or baseline
replacement is needed for these affected SDK targets.

Private build logs are SDK `out/nr0b2-build-final.log` and
`out/nr0b2-build-committed.log`; final test output is
`out/nr0b2-tests-final.log`. The first compile identified an enum conversion
and unsigned bitfield-expression narrowing in new metadata initializers; those
were corrected and all affected sources compiled successfully. Existing
unrelated compiler warnings were retained.

## Prepared session

Session: `C:\Dev\Fable2Recomp\out\nr0b2\sessions\nr0b2-oakfield-20260910-002`.
Preparation JSON SHA-256:
`E716D49723C1851FA6949DA0D473BC2F569257C5BECD50372EE721936943199C`.
Initial preservation audit SHA-256:
`E503E7DD80E47096C11E20799AD2843A3035480D19BAAA5211BDC9FA24BF090A`.

The earlier unused `nr0b2-oakfield-20260910-001` preparation and checkpoint
remain preserved. They were superseded before user handoff by `002` after the
final carry-in correction. Neither session was launched; no claim was removed,
root reused or prior artifact overwritten. Only `002` is the run-card target.

| Staged file under session `runtime` | Bytes | SHA-256 |
|---|---:|---|
| fable2.exe | 105042944 | `1642ED03BD8B117A8FED6E9FF912AD49CBF0E91A4E1D226B20C266925E3FF2C9` |
| rexruntime.dll | 10380288 | `1CEB686A2D9C704491D45C47DA34701E00CA649AE6177C7E1171C980F1EF56D7` |
| rexgpu-xenos.dll | 2846208 | `584474C1C25D4D68DC49B856F827B3021788F29A29B8D2C4CF46DE25B3EA9B3A` |
| TracyClient.dll (optional staged file) | 232960 | `FDBE7A329E1B06A86FE61A2C5BE6B335F32F9BBCA7E05F7B183A35C515D2D1A5` |

`llvm-readobj --coff-imports` inspected the exact EXE/runtime/GPU images. None
imports Tracy, so only those three images are required loaded modules. The
preparation's “Release import audit required” note is discharged by this
specific audit, not a general exemption. Audit output:
`out/nr0b2/release-imports-final.txt`, SHA-256
`FBC6E936854EF65FE1BC5324A76F3C5C88F20C4387E913D16FFB757948EEE761`.
Loaded paths/hashes remain unobserved until the actual process.

The source and both new copies match all 14 relative-path/size/hash entries.
The independent Phase 5A and NR0B-1 preserved checkpoints remain unchanged.
The writable cache is distinct and copied, not empty: `.rtv.d3d12.xpso` 46956
bytes / `B84C25906C3E0C5F3560E436BA1954AC0A536651E28CEB10346458A1C0123D22`;
`.xsh` 246884 bytes /
`72DB0BC95A784DD65BB1621AFCA6638708D4CDD60900ED05202FA6E7FCC5CD32`.
Driver-cache state remains unknown. Exe-adjacent `fable2.toml` remains absent.
No RTV/ROV, scale, async, readback or other rendering setting is overridden.
The original nine-stage report supplies fresh effective context for comparison.

Preflight independently checks the accepted runtime XEX/XEXP identities from
NR0B-1. The inherited post-patch guest-image SHA remains static evidence,
not a newly measured process-memory identity. No payload or private build
artifact is added to Git.

## Focused validation

| Check | Result |
|---|---|
| SDK affected Release compilation and post-commit dependency check | PASS |
| Recorder + existing configuration tests | PASS, 17 cases / 119 assertions; 14 metadata, 3 configuration |
| Independent Python metadata tests | PASS, 10 synthetic tests |
| Existing NR0B-1 preparation/parser tests | PASS, 6 |
| Existing GPU-reference tests | PASS, 10 |
| Existing NR0A tests | PASS, 7 |
| G1 verifier | PASS, 11 candidates |
| NR0A verifier with preserved state | PASS, 10 pins / 44 symbols / 70 local links / 19 immutable links |
| Default GPU-reference verifier | PASS, 0 warnings |
| Strict historical artifact verifier | 7 known failures, 0 warnings; exact comparison below |
| Python compilation / PowerShell AST | PASS; actual GUI launch remains user-run validation |
| Fresh-session preflight, protected inputs, baseline and unrelated edit preservation | PASS |
| New document links and git diff --check | Checked at final prepared closeout |

Tests cover default-off allocation, wrong PID and repeated trigger, exact
deadline/record/byte/decision ceilings, terminal reservation and invalid record
failure, initial partial/complete swaps, outcomes, carry-in definitions,
one-to-many operations, missing/duplicate/invalid references, partial execution/
submission/completion, cancellation, writer failure, shutdown, output/session
reuse refusal and continued healthy host execution. The real worker expired
with **no subsequent producer event** and flushed a 512-byte synthetic capture.
Independent Python accepted it as zero complete intervals. It also accepted
the C++-written 8192-byte synthetic ordinary-work fixture as one complete
interval, with joined native invocation/submission/completion. Neither fixture
is Fable rendering or visual-equivalence evidence.

One final synthetic sample measured disabled `Emit` at 1.1853 ns/call over
1,000,000 calls and enabled `Emit` at 46.2 ns/call over 10,000 calls (2,560,512
output bytes). These are recorder-call microbenchmarks, not default-off frame
cost or gameplay overhead. Source inspection finds pointer guards at consumer
sites, one recorder-state check when enabled, no allocation/thread/output when
disabled, and no new hash/analysis/I/O/wait on hot paths. State decoding and
extra memory traffic are outside the append timing. No negligible-overhead
claim is made; disturbance remains unmeasured in gameplay.

## Strict historical limitations

The actual strict output has exactly the same seven limitations retained by
NR0B-1: missing `fable2-run-047.1.log`, `fable2-run-047.log`,
`fable2-run-048.log`; historical baseline EXE comparison; historical GPU artifact
comparison; repeated G1.6A and G1.6B GPU comparisons. Current baseline hashes
remain EXE `1642ED03BD8B117A8FED6E9FF912AD49CBF0E91A4E1D226B20C266925E3FF2C9`
and GPU `70492C8612DEF79C9E3946817F424111FAB2155A3BE63CEA6E717CA73893ADC5`.
No new provenance failure is accepted as an exception; no logs/hashes/checks
were replaced or weakened.

`out/nr0b2/gpu-default.log` SHA-256:
`F368075FF5E8B8616DC5F5608BBFE013604BCD603B386D129BE667DFCBBB49E0`.
`out/nr0b2/gpu-strict.log` SHA-256:
`CB02FB2F5A3B95B660E3A8233A85E60991BCCB631EF0EFA09AB6A0B8A4032750`.
