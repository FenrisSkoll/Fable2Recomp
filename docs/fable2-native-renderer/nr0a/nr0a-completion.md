# NR0A completion and validation

Result: **CONDITIONAL ARCHITECTURE — DYNAMIC EVIDENCE REQUIRED**.
Source inspection began 2026-09-09; closeout validation is dated 2026-09-10.

The [decision](architecture-decision.md) selects a Fable-specific adapter as the
preferred endpoint, developed through isolated workloads/separate runs with
ReXGlue retained for observation and regression. A broad static API boundary
remains an alternative if its coverage and lifetime contract can be proved.
D3D12 first with a small interface is conditional on ownership and shader gates;
Plume is assessed, not integrated. PGR4 is planned-only at the inspected public
pin. Skate provides an implemented title-reconstruction precedent with a modified
SDK, retained PM4 and title-specific suppression; it does not prove a safe Fable
dual-renderer transition.

The [NR0B specification](nr0b-evidence-plan.md) is the exact next bounded action:
effective configuration/capability snapshot first, then a short user-operated
capture from one identified isolated save copy. No complete frame contract,
material association or payload corpus exists as a result of NR0A. No current
Fable address is promoted to a production renderer seam. The first real workload
must be selected from that evidence and initially isolated unless all pass
dependencies close.

## Validation record

Invocations are from `C:\Dev\Fable2Recomp`; local root overrides make the new
source verifier usable without modifying existing reference checkouts.

| Check | Result and limitation |
|---|---|
| `python tools/Verify-Fable2NativeRendererNR0A.py --verify-preserved-state` | PASS: ten repository pins and their recorded gitlinks, 44 source-symbol records, 68 local package links and 19 immutable source links; JSON contract, accepted ancestry and preserved manifest/libmspack bytes checked. Literal source presence is not proof of semantic accuracy. |
| `python -m unittest discover -s tests -p test_verify_fable2_native_renderer_nr0a.py` | PASS, seven failure-oriented synthetic tests: immutable object lookup, absent symbol, wrong blob, mutable URL, broken link, duplicate pin and path traversal. Only temporary synthetic Git repositories are created. |
| `python tools/Verify-Fable2NativeRendererG1.py` | PASS: 11 candidates, `confirmed=5`, `strong_hypothesis=4`, `weak_hypothesis=2`. Inherited classifications are not upgraded. |
| `python -m unittest discover -s tests -p test_verify_fable2_gpu_reference.py` | PASS, ten existing verifier tests. |
| `python tools/Verify-Fable2GpuReference.py --sdk-root C:\Dev\rexglue-sdk-v0.10 --canary-root C:\Dev\Fable2NativeRendererResearch\xenia-canary` | PASS, zero errors/warnings through G1.5A-D/G1.6A-B under the current documented default policy. |
| Same GPU verifier with `--verify-artifacts` | Exit 1: seven errors, zero warnings. Three missing historical logs and four historical/current artifact-equality errors, detailed below. No policy weakening or reconstructed evidence. |
| `git diff --check`, reviewed staged diffs and path allowlist | PASS for reviewed in-scope changes; no unrelated manifest or SDK materialization staged. Git's LF/CRLF notices are normalization notices, not whitespace errors. |
| Documentation indexes | PASS: 13 local links in root README and 73 in the GPU index, in addition to the package links. |
| Canonical/reference state audit | PASS against initial reference HEAD/tree/index/worktree/gitlinks and dirty-file hashes. Testing Canary separately matches its documented HEAD/tree with clean status. Exact ending Fable commit/tree belong to the final response, outside this document's own commit. |

The historical artifact verifier failures are exactly:

1. G1.5 active `rexgpu-xenos.dll` SHA mismatch: expected
   `8232051BED6E5CE99CF37B2EF581C824F58875C140A4D3C75DE14E8A5DF4AA99`,
   current `70492C8612DEF79C9E3946817F424111FAB2155A3BE63CEA6E717CA73893ADC5`.
2. Historical `fable2.exe` SHA mismatch: expected
   `EEACEAA8DB38E728B79F4F78B0298B7036E13EB4903518C503199697FA64AE6F`,
   current `1642ED03BD8B117A8FED6E9FF912AD49CBF0E91A4E1D226B20C266925E3FF2C9`.
3. Missing `fable2-run-047.1.log`.
4. Missing `fable2-run-047.log`.
5. Missing `fable2-run-048.log`.
6. G1.6A active GPU hash equality fails against the same historical DLL hash.
7. G1.6B active GPU hash equality fails against the same historical DLL hash.

These are inherited missing evidence and current-versus-historical rebuild
identity differences, not failures introduced by NR0A code. The current DLL has
the same 2770944-byte size but different bytes. Source/structure validation
passes without asserting that historical artifacts are present. The optional
strict check truthfully fails. No logs were recreated, substituted or deleted.

The new verifier intentionally does not fetch web links or verify runtime
behavior. External repositories were publicly checked separately; cited files
are checked against local immutable objects. Component license retrieval URLs
and hashes are recorded, but unaudited transitive components, Skate/PGR4 source
reuse permission, and bundled compiler/generated-output distribution remain
unresolved. No schema framework, source-code import or reference build was added.

## Git and documentation boundary

The branch is `fable2-native-renderer-nr0a-architecture`, based on accepted main
`9936fd1839da4286a9d09530ae0bb6ac11b5eda4`, tree
`814f96b0ad58c891032233452027cfee5f5bad2a`. The first logical change contains
source/provenance evidence and the read-only verifier/tests; the second records
the architecture/ownership/NR0B gates, completion and current-status links.
The source/provenance commit is
`a282686ac01aa7a8aa21a74280cb14d882d69578`, tree
`294f1e3230d2147cac5a526a39cb6112eafc1b09`. The following architecture/closeout
commit identity is reported after it exists; it does not attempt to contain
its own final hash.

The pre-existing `fable2_manifest.toml` blank-line deletion remains unstaged,
byte-for-byte unchanged. SDK main stays
`fc5a00b31f702e82377aa1010395af7ba8cff4f7`, tree
`903af44f9aab5684443ddb22e505b0ea811d45d2`, with its original 15 libmspack
materializations and clean index. Existing references were not fetched into,
switched or edited. New separate shallow reference checkouts remain clean.

No game/reference build or execution, gameplay automation, runtime/GPU change,
instrumentation, hook, generated-source/manifest/codegen change, save access or
modification, shader/asset extraction/conversion, GPU DLL replacement, SDK
implementation/dependency/build change, G2A restoration, merge, push, tag or
history rewrite was performed. Disk executable hashes and source Git objects
were read only. NR0B and renderer implementation have not started.
