# Focused ownership corroboration: Phase 4 P1/P2

## Accepted outcome

All **42 internal-entry targets** and **114 switch-case destinations** retain
their existing recovered owners. There are **zero new functions/thunks, zero
corrected owners, zero manifest changes, zero generated-code changes and zero
unresolved ownership cases**. No further gameplay or Astra x-high investigation
is justified for this population. This is a code-ownership result, not campaign
coverage or proof of overall runtime correctness.

Authoritative outputs, in stable priority/address order:

- [Per-target JSON ledger](ownership/ownership-ledger.json): exact owner extents
  and body fragments, all observed sources/run/thread provenance, independent
  boundary checks, call/LR evidence, table membership, disposition and rationale.
- [Generated human-readable ledger](ownership/ownership-ledger.md).
- [Reviewed import-plan companion](ownership/ownership-reviewed-import-plan.json):
  semantic annotations bound to the exact regenerated Phase 4 plan and ledger
  hashes. This is deliberately **not an applicable manifest fragment**.

| Phase 4 population | Final code classification | Count |
| --- | --- | ---: |
| internal entry | conditional-return continuation | 42 |
| switch case | ordinary case block | 91 |
| switch case | shared case body | 20 |
| switch case | default case | 1 |
| switch case | immediate tail transfer from a case block | 2 |
| **Total** | **retained internal blocks/cases** | **156** |

All 156 hypothetical promotions are rejected: every target is strictly inside
exactly one current recovered body. This does **not** mean Phase 4 proposed 156
bad functions: its original and regenerated plans both propose **zero** ranges.
No new overlapping/duplicate function range is introduced. The 411 already
registered targets in the same deferred queue remain outside this phase.

## Reconstructed baseline and integration history

Before target investigation, repository instructions, root READMEs and all
current project narrative documentation in both canonical repositories were
read, including bring-up/baseline, fault walking, closure, Ghidra/XEXLoader,
shared evidence, manual/automatic tables, Phase 3 regressions, Phase 4 collector,
merger/import/validation/integration and accepted G1–G1.6 reference research.
Associated Phase 4 schemas, compact fixtures, tests and generated evidence were
also inspected/validated. Bundled generic ISA PDFs were inventoried, not used
as evidence of title-specific ownership. No renderer or Xenia Edge work was
undertaken; retired renderer conclusions were not reopened.

| Repository | Starting branch | Starting HEAD | Starting tree | Starting status |
| --- | --- | --- | --- | --- |
| `C:\Dev\Fable2Recomp` | `main` | `3574787eb660a690a4eec0724c9f7b311432539b` | `3ac5200a85c16d7d7e43e39e8742aef9a1328660` | clean |
| `C:\Dev\rexglue-sdk-v0.10` | `main` | `fc5a00b31f702e82377aa1010395af7ba8cff4f7` | `903af44f9aab5684443ddb22e505b0ea811d45d2` | pre-existing ` m thirdparty/libmspack` |

These match the supplied orientation. No reset, stash, cleanup or remote
operation was needed. Fable work uses local topic branch
`fable2-focused-ownership-corroboration`. The SDK is read-only and remains on
`main` at the same commit/tree with the same pre-existing submodule dirt.

Accepted Phase 4 integration provenance:

- Fable merge `0c3d452e6bde5773743e67c041812ad2e333db45`, tree
  `fcf2dbfd5c54cd57633e7c8e1b6b4a75c1a1077b`.
- Feature/archive tip `f24b1e3f2e69707845ff6c1cd26e5b31dad0f6cd`, same tree.
- Deferred queue `5121e0ec61c621630f93be6e10dcea5f2d211306`.
- Compact merger `1f8dccb799e790878a0d1ab0b9d0c702680d0d5e`.
- Collector/contract repair `9c46998a993ea2046b1e9a873d7d9521eb2f44ad`.
- Initial Fable pipeline `f14cec668e94dbf6014a2c829b5ec1b0cc9c4a0f`.
- SDK runtime-evidence contract `956c6a8b5da4c54b9899a2593e9c67c26de30194`;
  schema-5 support is present in current `fc5a00b31f702e82377aa1010395af7ba8cff4f7`.
- Read-only collector reference
  `C:\Dev\Fable2Phase4Xenia\xenia-canary`, commit
  `32460b5d887dcde6622bb17983b70752fa5f13b3`, tree
  `114cb589291e2c87fcbcabc949a730ca5d1f6cad`.

## Authoritative inputs and exact reconciliation

Preserved compact inputs:

```text
out/indirect-targets/fable2-tu1-manual-001/review/xenia-indirect-targets.summary.json
F943DA466653278DED408B3AD7CD462392E74E50FC9521BF4F75FE0F95543BA4
out/indirect-targets/fable2-tu1-manual-002/review/xenia-indirect-targets.summary.json
09A7CA95CC804CCC088A793DE6131D680D6C05184F656F15DDA80F2CF4382B97
out/indirect-targets/fable2-tu1-manual-001-002-merged/phase4-static-ownership-follow-up.json
9DF543E67C4E0EE121BDAD9142E57138C3D5823B2FE72D25E02B17CB19C2C987
P4OWN-64AD322EA200BCB401C0
```

The same directory contains the accepted queue's CSV/Markdown review views.
The supported merger accepts two runs, quarantines zero, and reproduces
27,785 source/target/transfer pairs and 16,143 distinct planned targets.
Set subtraction is by run-qualified observation provenance: manual-002 targets
absent from manual-001. This independently yields 567 targets, partitioned
42 internal + 114 case + 411 registered. Counts are not forced by CLI options.

Current outputs in `out/ownership-corroboration/phase4-run1` and `phase4-run2`:

| Artifact | SHA-256 / identity |
| --- | --- |
| merged summary | `AE4670BAFDF6FC8AB719F81CCE14C5BD63FDD4EAA8262D0CDAB79B0E39F83A29` |
| reviewed source plan | `446EF1C3EE0899AF1EF6278AD52D79E0538B4E72703940EBDE23550FD25C18AA` |
| plan ID | `P4PLAN-EF5A9BE6D31FDB8BD309` |
| ownership queue | `1A3C33C0A807101E67390E8B3F9546C27ED575B94D5E4EDE56DA507C9532869B` |
| queue ID | `P4OWN-A60D13B0F6FF4AC96B02` |
| focused ledger | `2854BA326303C813148792D4D830444B2879FE294756B99C82D3C50D42B3328E` |
| ownership reviewed-plan companion | `B52B3BB11AB77B9F51D8DE0135B0BBA17AC66E86D5587E87641813343A70D045` |
| human ledger | `D7C709F695FAB1CB4A8C3F819F6E8CDAF1C3B2B44603EC830217CDC539ACC34E` |

**Baseline difference, not target drift:** the archived plan
`P4PLAN-0F8624F3F02D21D74775` has SHA-256
`82C262178A386CB4F519B9CF72D71C946948EB6AF06454349E060C41830AB6F6`.
Recursive comparison finds exactly two differing fields: derived `plan_id`
and `inputs.shared_evidence.sha256`. All target records are identical.
The latter changed from archived
`B06A32893BC6BE6BF821C242D7BECC586FB8119C4D257D57BA3A2C3777AEB5FF`
to current worktree
`54C6A14EA06EA217B09E784026B2C9A11A5AC325EE838B003A1DDFC8E6BAB02E`.
That propagates into the queue ID/hash. The accepted feature tip and current
HEAD contain the same committed shared-evidence blob
`cd5b4eb924ca4a566ea231c284ab04a696dfc618`, whose LF bytes hash to
`0737E31730C5703BD2DB44F7BECDFA8EC8A85A71E2612BE0B462ED1AF2C9FB68`.
The current CRLF checkout is not byte-identical to that Git blob. The exact
historical byte serialization producing `B06A32893BC6BE6BF821C242D7BECC586FB8119C4D257D57BA3A2C3777AEB5FF`
was not recovered; do not assert that LF/CRLF alone explains it. This limited
provenance uncertainty changes no target or ownership result and is not an
x-high ownership case. Original artifacts and the shared record remain intact.

## TU1 and independent evidence

```text
base XEX SHA-256:
88C4EF2E18E65409444D1B068EFF921D1F7E180A5AE64EDC64BA6B0872372662
TU1 XEXP SHA-256:
046A05693B4DA4437083C784000A850858B3BF992955C7DB30D518FB3E53E41C
contiguous loaded post-patch image SHA-256:
BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00
executable-memory fingerprint:
5C8B78B84C93028D166E3DF347206E6642BA40BF374AD1AF8D958B2211320357
image base: 0x82000000; size: 0x01620000; entry: 0x82CC21C0
title: 0x4D5307F1; media: 0x716F0A0D; version: 0.0.1.26
```

Closure was regenerated twice through the normal release cache's installed
`0.10.0.51-dev.gfc5a00b` SDK. Its authoritative JSON is byte-identical to
the accepted Phase 4/Phase 3 closure:
`665CA2AE7ED65632B2E9F368063D3D9EE260E8DEF6F276B455CD62A9F2DCC397`.
Schema 3/analyzer 2.0.0 reports 60,662 recovered functions, 334,465 direct-edge
records and 35,626 candidates (55 strong, 180 probable). These global counts
are not a claim that every other function/indirect site is resolved.

Exact-image Ghidra input:
`out/analysis/BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00/ghidra-function-map.json`,
SHA-256 `03516B3A1F33433E493739418C9939D4FF1AEB0989F4ACEF2FD4D8204A077F58`,
42,462 function records and 46,180 `.pdata` entries.

Existing private snapshot, not newly captured:
`out/phase3-regression-closure-final-smoke/iteration-01/tu1-text-0x82000000.bin`,
19,922,944 bytes, base `0x82000000`. Before any opcode/table use, the generator
checks these complete immutable sections against the exact-image evidence:

| Section [start, exclusive end) | SHA-256 |
| --- | --- |
| `.text` `[0x82170000,0x832BABBC)` | `1B9F2E80280637FE2287286ED3FE18B367F378E24A695A2B8AB50B9ACD8FC724` |
| `BINK` `[0x832BAC00,0x832CA03C)` | `D715B7B4F3E7912489DBBBA3FF2642B1907479CBEDBDF974CD043827DB707146` |
| `.pdata` `[0x8210B800,0x82165B20)` | `FE6A61E508AD67FC39BEA85372A06DA1CAF40C5F1E7BB2B52FF37471FE44AB3C` |

The runtime snapshot's other data need not equal pristine loaded memory; its
whole-file hash is **not** presented as the contiguous loaded-image identity.
The `.pdata` decoder follows SDK `src/codegen/phase_register.cpp`: two
big-endian words, entry then packed unwind fields; length is bits 8–29 times
four. All decoded starts reconcile exactly to the map's 46,180 starts.

131 target rows have owner `.pdata` records, all matching the claimed end.
120 have a Ghidra owner entry; only 44 are included in that entry's exported
body. Ghidra's incomplete bodies are not promoted above exact TU1 call/table
control flow, unwind boundaries and current recovered body evidence. The
ledger explicitly records these negative map results, rather than claiming
universal map agreement. None of the 156 targets is an exact `.pdata` start,
Ghidra function start, exact closure direct-edge target or effective registration.
Pointer/table candidates remain visible in the ledger; table storage is not
treated as independent callback/vtable evidence.

## Internal-entry findings

All 42 targets are **confirmed code-level return continuations**. Every target
immediately follows a linking call. For 38, TU1 `bl` decoding resolves directly
to the owner of the observed conditional LR-return source. Four follow `bctrl`:

```text
0x821BD8A8
0x827A59F0
0x828DD4C8
0x82990A0C
```

For these, manual-002 also records the preceding `bctrl` site resolving to the
observed return-source owner. Across 42 targets there are 44 observed return
source pairs; none is omitted. The ledger preserves the additional call pairs,
source owners, source instructions and generated function/file locations.
Generated caller code sets `ctx.lr` to the continuation, and generated callee
code implements the matching conditional mnemonic with a C++ return.

The collector's `src/xenia/cpu/ppc/ppc_emit_control.cc:351` marks only exact
`0x4E800020` (`blr`) with `CALL_INDIRECT_ORDINARY_RETURN`; conditional `bclr`
returns remain collected. Therefore Phase 4's historical “non-return target”
terminology means *ordinary-return-filtered*, not proof that conditional
returns are excluded. This is explanatory corroboration, not a request to
discard all `bclr` evidence or change collector filtering.

`lr_after_call` is established by PPC link semantics. The original compact
records do not provide direct LR register snapshots; the ledger explicitly
sets `lr_value_observed_directly=false`. Run/thread pair correlation is not
an event-by-event stack trace. Those limitations do not turn the caller's
instruction after its call into a new independently callable function.
No alternate entry, callback dispatch, virtual dispatch entry or standalone
leaf/tail thunk is independently proven at these target addresses. The
existing generated call/return path does not establish a need for any new
dispatcher registration.

## Switch-case findings

114 targets reconcile to 42 dispatchers in 41 owners. Destination encodings
are absolute pointers for 102 targets and relative offsets for 12 targets.
For every dispatcher, all selected table storage is independently decoded
from verified TU1 bytes, including signedness, element width, anchor and
scale. Every instruction cited by the table proof matches the same image.
Each target retains its complete matching index list and default membership;
dispatcher records preserve bounds, guard addresses, index transformations,
target expression and selected origin. Existing manual definitions retain
their authority; none was replaced or changed. Generated owner `goto`
references corroborate internal block membership.

Subtype precedence is immediate external tail transfer, then default, then
shared indices, then ordinary case. These are mutually exclusive reporting
labels; they do not deny that a default may also serve multiple indices or
that a longer case body may eventually make a tail call.

The default case is `0x82995E7C`. The two immediate tail-transfer cases are:

| Case address | Owner | Dispatcher/table | Existing tail destination/range |
| --- | --- | --- | --- |
| `0x826AE7B4` | `0x826AE760` | `0x826AE780` / `0x826AE784` | `0x826D58F0` / `[0x826D58F0,0x826D59C4)` |
| `0x826AE7B8` | `0x826AE760` | `0x826AE780` / `0x826AE784` | `0x826D5A60` / `[0x826D5A60,0x826D5AEC)` |

The table has 12 entries with indices 0–11, transformed from `r4 - 26`;
`0x826AE764` supplies the upper-bound comparison and `0x826AE768` the
out-of-range conditional return. Indices 10 and 11 select those two cases.
Each case is a non-linking `b` to an already registered `.pdata` function.
The branch destination is a function; the switch case address is not thereby
a separately callable thunk. No source-level names are invented.

## Implementation and representation

`tools/Fable2OwnershipCorroboration.py` consumes supported Phase 4 outputs,
the exact-image function map, closure, generated units and verified private
snapshot. It independently reconstructs the selected target set, checks
stale input hashes, duplicate/overlapping body ownership, all observed source
sets, PPC call/return semantics, and exact table bytes/instructions. `--check`
performs the same reconstruction and compares every output byte.

The semantic validator rejects omissions, duplicates, owner conflicts,
unsupported promotion, missing source pairs, incorrect LR, table membership,
default/subtype contradictions and miscounted outputs. Two versioned schemas
and 18 focused tests cover the committed metadata corpus and adversarial
mutations, without requiring private game files. The existing schema-checking
test helper is reused; no validator or threshold is weakened.

The reviewed companion adds the missing semantic disposition without changing
the Phase 4 category contract. Shared-evidence schema 5, canonical manifest,
Ghidra map, Phase 4 raw/compact observations and import application logic remain
unchanged. No runtime fix or instrumentation is introduced.

`.gitattributes` pins only the three generated ownership artifacts to LF for
cross-checkout byte comparisons. `Build-PpcDisassembler.ps1` gains optional
`-SdkRoot`, preserving its previous default. This phase explicitly builds it
from the canonical v0.10 SDK rather than changing global helper configuration.

## Reproduction and verification

Run from `C:\Dev\Fable2Recomp` in the established developer PowerShell.
The original private snapshot and compact summaries must remain available;
the new tool neither launches gameplay nor reconstructs missing private assets.

```powershell
.\tools\Build-PpcDisassembler.ps1 -SdkRoot C:\Dev\rexglue-sdk-v0.10
.\tools\Invoke-Fable2EntrypointClosure.ps1 -OutputDirectory out/ownership-corroboration/closure-run1
python tools/Verify-Fable2EntrypointClosure.py --report out/ownership-corroboration/closure-run1/entrypoint-closure.json
python tools/Fable2FunctionMap.py validate out/analysis/BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00/ghidra-function-map.json

python tools/Fable2IndirectTargets.py merge `
    --summary out/indirect-targets/fable2-tu1-manual-001/review/xenia-indirect-targets.summary.json `
    --summary out/indirect-targets/fable2-tu1-manual-002/review/xenia-indirect-targets.summary.json `
    --output-directory out/ownership-corroboration/phase4-run1

python tools/Fable2IndirectTargets.py plan `
    --summary out/ownership-corroboration/phase4-run1/xenia-indirect-targets.summary.json `
    --closure out/ownership-corroboration/closure-run1/entrypoint-closure.json `
    --output out/ownership-corroboration/phase4-run1/fable2-indirect-targets.import-plan.json

python tools/Fable2IndirectTargets.py ownership-follow-up `
    --baseline-summary out/indirect-targets/fable2-tu1-manual-001/review/xenia-indirect-targets.summary.json `
    --contributing-summary out/indirect-targets/fable2-tu1-manual-002/review/xenia-indirect-targets.summary.json `
    --merged-summary out/ownership-corroboration/phase4-run1/xenia-indirect-targets.summary.json `
    --plan out/ownership-corroboration/phase4-run1/fable2-indirect-targets.import-plan.json `
    --closure out/ownership-corroboration/closure-run1/entrypoint-closure.json `
    --output-directory out/ownership-corroboration/phase4-run1

python tools/Fable2OwnershipCorroboration.py `
    --phase4-directory out/ownership-corroboration/phase4-run1 `
    --closure out/ownership-corroboration/closure-run1/entrypoint-closure.json `
    --guest-snapshot out/phase3-regression-closure-final-smoke/iteration-01/tu1-text-0x82000000.bin `
    --output-directory docs/fable2-discovery-pipeline/ownership --check

python -m unittest discover -s tests -p 'test_*.py'
fable2-build
```

To emit a fresh review rather than check the committed corpus, omit `--check`
and use an ignored `--output-directory out/ownership-corroboration/review`.
Do not overwrite the accepted corpus when a stronger/new input yields an
unreviewed difference. Full regeneration is tied to input byte hashes,
including the current shared-evidence checkout form, not merely Git contents.

The second pass used the same commands with `closure-run2` and `phase4-run2`.
All six Phase 4 outputs and all seven deterministic closure/jump-table outputs
were byte-identical across runs. Only `entrypoint-closure-run.json` and
`jump-table-recovery-run.json` differ, as expected for operational run metadata.
The second pass's ownership `--check` passed against the three committed
outputs, both before and after the canonical disassembler rebuild.

| Check | Exact outcome |
| --- | --- |
| closure regeneration, twice | exit 0; schema 3/analyzer 2.0.0; accepted closure unchanged |
| closure verifier | exit 0; fixtures `0x829647F0`, `0x82C03B28`, `0x829675E0` pass |
| function-map validation | exit 0; schema 1, 42,462 functions, `exact_image_match` |
| compact merge, twice | exit 0; 2 accepted, 0 quarantined, 27,785 pairs |
| import plan, twice | exit 0; 16,143 targets, 0 proposals, 0 applicable |
| follow-up queue, twice | exit 0; 567 = 42 + 114 + 411; `raw_traces_accessed=false` |
| ownership generation/check | exit 0; 156 covered exactly once, 0 unresolved, 42 dispatchers |
| Python suite | exit 0; `Ran 90 tests in 3.157s`, `OK` (72 existing + 18 new) |
| disassembler build | exit 0; two `clang-cl: warning: argument unused during compilation: '/std:c++20' [-Wunused-command-line-argument]` warnings from C compilation |
| `fable2-build` | exit 0; `Build completed successfully.`; codegen `0 written, 0 unchanged, 0 deleted, 1 module(s) up to date` |
| SDK CTest | exit 0; 1,764 passed, 4 established skips, 0 failures |
| Git whitespace validation | `git diff --check` and `git diff --cached --check`: exit 0 |

The Fable build was the supported incremental/up-to-date build, not a claimed
clean-room rebuild. No SDK C++ target changed; its already built test suite was
executed using the supported preset:

```powershell
Set-Location C:\Dev\rexglue-sdk-v0.10
ctest --preset win-amd64-release --output-on-failure --parallel 8 --output-log C:/Dev/Fable2Recomp/out/ownership-corroboration/sdk-ctest.log
```

CTest reported `100% tests passed out of 1768`, total time `9.66 sec`.
The four established skips are exactly:

```text
51 - unit.BitStream Write preserves surrounding bits (Skipped)
127 - unit.BitStream Write 16-bit value (Skipped)
163 - unit.BitStream Write byte-aligned (Skipped)
164 - unit.BitStream Write non-byte-aligned (Skipped)
```

The manifest remains SHA-256
`E3EB39CA153E396D5DC53E6F943ED8FF7AF1D6B0704EB860836BD7D21A3F87B0`.
No explicit codegen regeneration was necessary; the normal build's dependency
check wrote no generated code. Identical closure/jump-table output and target
records exclude unrelated discovery drift in this phase. Compilation/tests
are not asserted to prove guest runtime correctness.

## Limitations, evidence levels and handoff

**CONFIRMED:** current target coverage, unique recovered body membership,
decoded call/link/conditional-return shape, exact table/index/bound evidence,
map/unwind presence or absence, generated representation and no manifest action.

**Strong inference, not a new function fact:** aggregated call/return pairs are
consistent with normal dynamic return pairing. No per-invocation stack history
or directly captured LR value is claimed. Source-level compiler naming and
high-level semantics are not established by this phase.

**Weak hypotheses:** none used to decide ownership. **Unresolved ownership:**
none. The historical shared-file byte-serialization uncertainty above is kept
separate from ownership. It does not justify x-high analysis or a gameplay run.

Raw manual-001 data was previously deleted by the accepted workflow; this
phase used preserved compact evidence and did not delete anything. Manual-001
retains `abnormal_or_unknown_no_footer`; manual-002 retains schema-2 normal
footer provenance. No new capture, fault walking, controller automation or
screenshots were performed. No runtime instrumentation was added. Ignored
read-only scratch audits `out/ownership-corroboration/inspect.py` and `audit.py`
remain local; supported reproduction is the commands above.

Smallest future target: a genuinely new ownership conflict from additional
user-supplied gameplay evidence, not re-review of these 156 proven internal
destinations. All other Phase 3/4 coverage limitations remain as documented.

## Local commits and final identities

Implementation/evidence commit:
`98c5e0872a93e56469a32d1b2e63892d949de15c`, tree
`c7c41a0aa27ee0fc3ad8a2fa1097afbd9aff962c`.
It includes the generator, two schemas, portable tests, three evidence outputs,
LF attributes and explicit disassembler SDK selection.

The following logical documentation commit contains this report and navigation
updates. A tracked report cannot contain its own commit/tree hash without
changing that hash. Its exact closing commit/tree is recoverable without
ambiguity from:

```powershell
git log -1 --format='%H %T' -- docs/fable2-discovery-pipeline/07-focused-ownership-corroboration.md
git -C C:\Dev\rexglue-sdk-v0.10 rev-parse HEAD 'HEAD^{tree}'
```

The completed local copy
`out/ownership-corroboration/final-phase-report.md` appends the literal final
identities and worktree states after that documentation commit; the session
handoff also records them. No SDK commit is needed because its files were not
changed. Task-owned worktrees are clean at handoff; SDK pre-existing
`thirdparty/libmspack` dirt is preserved. No push, pull, merge, tag, upload,
release, PR or other remote modification was performed.
