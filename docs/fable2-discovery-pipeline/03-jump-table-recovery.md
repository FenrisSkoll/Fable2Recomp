# Idiom-aware Xenon/PPC jump-table recovery

## Status and scope

> **Regression-closure update (2026-08-30):** The original `0x8223FD7C`
> result below is superseded by
> [`03a-jump-table-regression-closure.md`](03a-jump-table-regression-closure.md).
> Coherent A/B runs prove it is a Phase 3-unrecovered switch case, and generic
> recovery plus performance corrections now select 726 tables and 6,359 unique
> cases. Final runtime validation exposed the next old-heuristic state-machine
> switch at `0x82CB6154 -> 0x82CB6158`, so the overall closure remains
> incomplete. No manifest function was added.

This is the durable checkpoint for the third Fable II function-discovery
stage. As of 2026-08-29, generic jump-table recovery is part of the canonical
ReXGlue `FunctionGraph` discovery path and runs before final function ownership,
boundaries, and code generation:

```text
trusted entries
  -> preliminary CFG
  -> indirect-site classification
  -> jump-table recovery
  -> case-edge/CFG expansion
  -> bounded fixpoint
  -> final ownership and boundaries
  -> code generation
```

The private Fable II Game of the Year Edition TU1 image selected 342 validated
tables at 342 dispatch sites owned by 331 functions. Those tables add 3,170
unique case blocks to their owners; none is promoted to a callable function
entry without independent evidence. Every remaining relevant non-link CTR site
has at least one explicit failure reason.

This stage does not change `fable2_manifest.toml`, generate a
`RETURN_R3_ZERO` stub, use IDA, trace Xenia, or import runtime targets. Existing
manual switch tables remain authoritative. The private XEX, XEXP, loaded image,
executable sections, Ghidra database, and raw bytes remain outside version
control.

## Canonical repositories and commits

Fable2Recomp:

- path: `C:\Dev\Fable2Recomp`
- branch: `fable2-rexglue-0.10-migration`
- prerequisite Ghidra commits:
  `2bdba963b89c3f6fcc4a0860593976eb8fb38504`,
  `7816886a5bd329d31dc95a31b67ef459a26229a4`, and
  `a8601e9469dd316c4618b23dd0415009f89453f1`
- shared-evidence integration:
  `21ffec593a2e99b179b5c8cc7811134cd9d68e32`
- final SDK pin:
  `f4b8487ba950240c0705ab2ed3df3807675717f8`

ReXGlue SDK:

- path: `C:\Dev\rexglue-sdk-v0.10`
- branch: `fable2-v0.10-migration`
- indirect classification/dataflow:
  `79f329123f4deea0c3a0a22e4871be555845cbd7`
- pre-boundary recovery/fixpoint:
  `ae12547fe56c985d48bcdab274979c838dc85f7a`
- deterministic reports/tests:
  `233ba7c95a974ba4d1a8d0bf92c363019706b4a3`
- nested relative-anchor correction:
  `e7c03755f83b9cd863a64d1d1c7d8cd79335e87e`
- shared schema-3 compatibility:
  `8d940b5e1abbe8d8d972a4088f4fc37a5b68d34f`
- stable/volatile report separation:
  `b228ae46d93b26e1ff7aca201102d6cb62d56318`
- installed version: `0.10.0.14-dev.gb228ae4`
- installed root: `C:\Dev\rexglue-sdk-v0.10\out\install\win-amd64`

The fork was checked against ReXGlue upstream main
`c94f5ebdcb3c9d1a460ca48e04f9758448f8d518`, upstream development
`e9d44256ba9ff512fa09d3ecfab5659a7d850fa9`, and merge base
`f5337cdc947ff6d4c4196737e2c807a48f2a1fc2`.

The pre-existing dirty SDK submodule state at `thirdparty/libmspack` was not
modified, staged, or committed. Recover the commit containing this document
without a self-referential edit with:

```powershell
git log -1 --format=%H -- docs/fable2-discovery-pipeline/03-jump-table-recovery.md
```

## Exact TU1 identity

| Evidence | Exact value |
|---|---|
| Base XEX SHA-256 | `88C4EF2E18E65409444D1B068EFF921D1F7E180A5AE64EDC64BA6B0872372662` |
| XEXP SHA-256 | `046A05693B4DA4437083C784000A850858B3BF992955C7DB30D518FB3E53E41C` |
| Loaded post-patch image SHA-256 | `BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00` |
| Executable-memory fingerprint | `5C8B78B84C93028D166E3DF347206E6642BA40BF374AD1AF8D958B2211320357` |
| Image base / size / entry | `0x82000000` / `0x01620000` / `0x82CC21C0` |
| Title / media / version | `0x4D5307F1` / `0x716F0A0D` / `0.0.1.26` |
| `.text` | `[0x82170000,0x832BABBC)`, SHA-256 `1B9F2E80280637FE2287286ED3FE18B367F378E24A695A2B8AB50B9ACD8FC724` |
| `BINK` | `[0x832BAC00,0x832CA03C)`, SHA-256 `D715B7B4F3E7912489DBBBA3FF2642B1907479CBEDBDF974CD043827DB707146` |

The byte-free identity and fixture contract is
`tools/fable2-entrypoint-closure-evidence.json`. Its shared schema is now 3;
schemas 1 and 2 remain readable. The manifest remained byte-identical at
SHA-256 `E3EB39CA153E396D5DC53E6F943ED8FF7AF1D6B0704EB860836BD7D21A3F87B0`.

## Dependency audit and baseline

Before editing, the existing schema, Ghidra importer, manifest parser, `.pdata`
ownership, preliminary CFG, code-emitter switch consumption, manual table
configuration, fault-walker evidence, and generated-function pipeline were
verified against the repository. The dependency gate passed:

- Fable2Recomp Python tests: 8/8;
- migration ledger: all 32 entries;
- entrypoint verifier: schema 2/analyser 1.1.0, 35,626 candidates, 55 strong,
  178 probable, all three fixtures;
- ReXGlue entrypoint-closure tests: 14/14.

The pre-change private run is preserved outside the source tree as
`C:\Dev\Fable2JumpTableResearch\baseline\entrypoint-closure-pre-jump-recovery.json`,
SHA-256 `04EDF9873F5B06A46A8C959AA7ED62899816762F695A03BCBB62A9D4851C4ADD`.
It took 54,684 ms with peak working set 1,066,323,968 bytes. The former local
heuristic reported 729 owner functions and 9,026 unique target memberships,
but it used nearby compares, fallback region bases, valid-prefix acceptance,
and late table rediscovery. Those counts are comparative evidence, not a safe
answer set.

There are currently zero Fable-specific manual `[[switch_tables]]` records.
The generic manual path and its precedence were nevertheless retained and
tested. A future manual annotation must remain selected until automatic
recovery proves exact semantic equivalence and a human explicitly removes it.

## Public primary-source research

Research and local checkout acquisition were performed on 2026-08-29. The
checkouts are under `C:\Dev\Fable2JumpTableResearch`, outside both source
repositories. Normal analysis and builds have no dependency on them or on
commercial IDA.

| Source | Pinned revision | Licence | What was checked |
|---|---|---|---|
| [`xdzleo/xenon-jumptables`](https://github.com/xdzleo/xenon-jumptables/tree/019b0c481a924197371c4af03e3418615cea22b2) | `019b0c481a924197371c4af03e3418615cea22b2` | BSD-3-Clause | Xenon absolute/relative idioms, conditional-return bounds, copies/reloads, inline/overlapping tables, and switch-on-CTR proposal |
| [`hedge-dev/XenonRecomp`](https://github.com/hedge-dev/XenonRecomp/tree/ddd128bcca99fe8bfbb99bea583c972351fa6ace) | `ddd128bcca99fe8bfbb99bea583c972351fa6ace` | MIT | current switch-table representation and codegen consumption |
| [XenonRecomp PR 185](https://github.com/hedge-dev/XenonRecomp/pull/185), fork `Uproared/XenonRecomp` | `fce79a7c082ed3f495f122b1ac13435eccd1b4b0` | MIT project | maintained jump-table recovery proposal and integration discussion |
| [`N64Recomp/N64Recomp`](https://github.com/N64Recomp/N64Recomp/tree/ffb39cdad1da5de07eaaa48bd1db4a89a7986771) | `ffb39cdad1da5de07eaaa48bd1db4a89a7986771` | MIT | mature static-recompiler analysis and switch ownership patterns |
| [`xenia-project/xenia`](https://github.com/xenia-project/xenia/tree/95a5c3ee250f80c3b9d139658649d9ffb6db3eec) | `95a5c3ee250f80c3b9d139658649d9ffb6db3eec` | BSD-3-Clause | PPC decode/control-flow semantics used as a reference, not a runtime trace |

Hash-pinned files from `xenon-jumptables` are:

| File | SHA-256 |
|---|---|
| `README.md` | `537EDF15DC58CD8A562FEA92909B0F5F8602DFFBF91F56A0D41820774EFE5310` |
| `docs/idioms.md` | `4286CEDDE812072E44E11199B34D51F61F5FA11A911190DFE7A0D42BC127C72D` |
| `src/ida_jumptables.py` | `85AA49F6D411A5B34BA5498480DE5AFA120CD176022EC082EDAF7033CB0D17DC` |
| `patches/switch-on-ctr.patch` | `CDB771AFDA56E24F86EC7B8D40B0D128E013DB2421CAAD32B0C7C0BCBD37F1B1` |
| `LICENSE` | `98A336B457313CD26760D5A072E953508529B09885D9B89E21860677C10D870F` |

The XenonRecomp MIT licence hash is
`7FD801BAC4A25E8D8BCDAA5A025F02EA245FD4C039B513AB4FC11CB5A0CFD3F7`;
the N64Recomp MIT licence hash is
`8F3594C18CD4F7E551795C2A11D17C460F7DD2C39FFDE0DB82F1DE876AAAC0C4`.
No third-party source was vendored. The implementation uses ReXGlue's own
decoder/CFG and a new bounded dataflow model; the public projects informed the
idiom catalogue, conservative validation policy, and tests.

## Generic implementation

The core API is `AnalyzeIndirectSite` in
`include/rex/codegen/jump_table_recovery.h`. Its model in
`include/rex/codegen/function_types.h` retains:

- dispatch and owning function addresses;
- classification, link/conditional/CTR flags, and explicit failures;
- automatic and selected/manual tables separately;
- storage start/exclusive end, kind, bound value/semantics/inclusivity,
  default target or conditional return, element width/signedness, anchor and
  target scale;
- raw storage address/value/decoded target for every entry;
- exact PPC address/raw word/mnemonic/role evidence;
- confidence, conflicts, and manual comparison;
- preliminary and final body blocks plus boundary effects.

`discoverBlocks` now runs a monotonic outer fixpoint. Each pass discovers all
indirect instructions in all currently owned blocks, analyses them in guest
address order, adds only selected case targets, and repeats so new case bodies
can expose direct edges or more indirect sites. If an automatic table becomes
invalid after CFG expansion, the site is quarantined rather than allowed to
oscillate. Final `FunctionNode` ownership and code emission see the stable
selected table set; the emitter no longer performs late independent recovery.

Cases are labels/basic blocks owned by the dispatch function. An address remains
a separate callable entry only when `knownFunctions` supplies independent
evidence, such as a trusted entry, direct call, `.pdata`, exact Ghidra entry, or
later runtime-call evidence. Body membership is tested against exact blocks;
min/max extent is never treated as a contiguous body.

### Classifications

```text
switch_bctr
computed_tail_bctr
virtual_or_callback_bctrl
indirect_tail_bctrl_or_bctr
ordinary_blr_return
nonstandard_bclr
opaque_indirect_transfer
```

Only a non-link CTR transfer with complete switch evidence becomes
`switch_bctr`. Ordinary `blr` returns and `bctrl` virtual/callback calls never
enter switch recovery. Non-standard `bclr` and opaque transfers remain visible
for review.

### Dataflow and supported idioms

The analyser builds a bounded predecessor graph over preliminary owned blocks
and follows reaching definitions for the CTR source, index lineage, memory
lineage, table base, relative anchor, scaling, and compare CR field. It accepts
a bound only when the corresponding conditional branch/return is on a relevant
dominating path; a nearby compare from another path is not borrowed.

The tested semantics cover:

- bounded absolute big-endian 32-bit target-pointer tables;
- `cmplwi`/related bounds with branch-to-default and `bgelr`-like conditional
  return defaults;
- `rlwinm`/`slwi` index scaling;
- register copies and equivalent memory reloads between compare, load,
  `mtctr`, and dispatch;
- nested `lis`/`addi`, `lis`/`ori`, and equivalent high/low base or anchor
  construction;
- `lwzx`, `lhzx`, `lbzx`, correct signed/unsigned extension, and rejection of
  unsupported element widths;
- byte/halfword relative tables, two-level tables, and
  `anchor + offset * scale`;
- inline executable tables, overlapping/shared storage, duplicate case
  targets, and bounded/default exits;
- case bodies which expose another indirect site at fixpoint;
- manual exact/superset/subset/bound/target conflicts and independent callable
  case promotion.

All table entries must validate together: aligned, executable, readable,
plausibly decodable, and consistent with the recovered bound and exact storage
range. A mixed-validity table is rejected as a whole. The analyser reports
rather than guesses:

```text
missing_bound
ambiguous_bound
unknown_table_base
unknown_index
ambiguous_reaching_definition
unsupported_relative_form
invalid_element_width
target_out_of_range
target_unaligned
mixed_validity_targets
analysis_limit
non_switch_indirect
```

Production defaults are 64 backward instructions, 512 entries, 64
predecessors, 512 dataflow states, and 8 fixpoint iterations. They are exposed
as the `Codegen` CVars `backward_scan_limit`, `max_jump_table_entries`,
`jump_table_max_predecessors`, `jump_table_max_states`, and
`jump_table_fixpoint_iterations`. Limit exhaustion is explicit in the report.

Automatic/manual comparison uses the complete vocabulary:

```text
exact_equivalent
automatic_superset
automatic_subset
conflicting_targets
conflicting_bounds
unsupported_manual_form
new_automatic_table
```

## Shared schema and Ghidra integration

The byte-free shared contract `tools/fable2-entrypoint-closure-evidence.json`
is schema 3. It adds the jump-table report version, pipeline placement,
classifications, failures, manual-comparison vocabulary, manual-authority flag,
and the invariant that case targets are not functions by default. ReXGlue and
the Python tools accept schemas 1, 2, and 3; future/unknown versions fail
closed.

The entrypoint-closure report is now schema 3/analyser 2.0.0 and embeds the
jump-table evidence. The dedicated report is schema 1/analyser 1.0.0. The
Ghidra map remains `fable2-ghidra-function-map` schema 1/exporter 1.1.0. Its
importer reads exact jump-case ownership from the shared closure report. If a
Ghidra function entry is only a recovered case and has no independent callable
evidence, it is quarantined as `ghidra_false_positive_suspected`; Ghidra names
or body extents never promote it.

No canonical manifest operation consumes a report automatically. Review TOML
fragments remain non-authoritative.

## Commands and reports

Run exact TU1 analysis and verify it with:

```powershell
.\tools\Invoke-Fable2EntrypointClosure.ps1
python .\tools\Verify-Fable2EntrypointClosure.py
```

The direct CLI is:

```powershell
C:\Dev\rexglue-sdk-v0.10\out\install\win-amd64\bin\rexglue.exe `
    entrypoint-closure `
    .\fable2_manifest.toml `
    --provenance .\tools\fable2-entrypoint-closure-evidence.json
```

`rexglue entrypoint-closure --help` documents the closure limits and output
override. `rexglue --help` lists the codegen safety CVars. Override one before
the subcommand for an explicit comparative run, for example:

```powershell
rexglue --jump_table_max_states 1024 entrypoint-closure `
    .\fable2_manifest.toml `
    --provenance .\tools\fable2-entrypoint-closure-evidence.json `
    --output .\out\analysis-limit-comparison
```

Exact default reports are written under:

```text
out/analysis/BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00/
  entrypoint-closure.json
  entrypoint-closure.csv
  entrypoint-closure.md
  entrypoint-closure-review.toml
  entrypoint-closure-run.json
  jump-table-recovery.json
  jump-table-recovery.csv
  jump-table-recovery.md
  jump-table-recovery-run.json
```

`jump-table-recovery.json` is authoritative and contains every exact table,
case, raw entry, instruction/dataflow record, preliminary/final block,
boundary effect, indirect site, and unresolved reason sorted by guest address.
CSV and Markdown are review views. Volatile command line, elapsed time, and
peak working set live only in `jump-table-recovery-run.json`; two consecutive
private runs produced byte-identical stable files.

Final stable identities:

| File | Bytes | SHA-256 |
|---|---:|---|
| `entrypoint-closure.json` | 315,391,520 | `DDE1365F3A54F932EEDBF18B54731CB253FCAB1E251722BE67D46F8E9460D868` |
| `entrypoint-closure.csv` | 11,331,568 | `80477CF0CDA06CBA5AF706EE61226AB0F7C9966680CF9C919C7BFB9F481AC1B3` |
| `entrypoint-closure.md` | 31,507 | `35038C90709ED297036DB7664A0CD89ADF39A71E0A2286F02D1A6BADA73D0AFA` |
| `jump-table-recovery.json` | 43,271,919 | `DDE8DA43CF44C2B712D3031430406040ED0E5AA1786D6467A589444662CA09C9` |
| `jump-table-recovery.csv` | 6,840,773 | `9968E6C83E001E6B59706BB7247D7A93438558D911A850BFCE8C7F72B25C391C` |
| `jump-table-recovery.md` | 132,831 | `559BD18FE93CC8B5EEAB9B503D80E6595B330EB1A50D96375587694B52AF6765` |

## Exact private-TU1 results

The following results are locally generated exact-image evidence, not public or
synthetic data.

### Indirect-site census

| Classification | Count |
|---|---:|
| `switch_bctr` | 342 |
| `computed_tail_bctr` | 1,161 |
| `indirect_tail_bctrl_or_bctr` | 1 |
| `virtual_or_callback_bctrl` | 28,090 |
| `ordinary_blr_return` | 36,593 |
| `nonstandard_bclr` | 2,296 |
| `opaque_indirect_transfer` | 0 |
| total | 68,483 |

### Selected tables and cases

| Evidence | Count |
|---|---:|
| selected automatic dispatch tables | 342 |
| selected manual tables | 0 |
| owner functions | 331 |
| absolute pointer tables | 306 |
| relative offset tables | 36 |
| byte / halfword / word elements | 31 / 5 / 306 |
| unique case targets | 3,170 |
| independently callable cases | 0 |
| static candidates reclassified as cases | 2,672 |
| owners with preliminary-to-final block changes | 331 |

All 342 selected tables have `new_automatic_table` manual-comparison status
because the current Fable configuration has no manual table. Multiple dispatch
sites explain why 342 tables belong to 331 owners. Exact dispatch, owner,
storage, bound/default, raw entries, cases, evidence, and preliminary/final
blocks for all tables are preserved in the authoritative JSON and its readable
Markdown view.

Compared by owner with the former heuristic:

| Comparison | Count |
|---|---:|
| `exact_equivalent` | 307 |
| new automatic is a conservative subset | 23 |
| `new_automatic_table` owner | 1 |
| old heuristic only | 399 |

The old set had 729 owners/9,026 targets; the validated set has 331
owners/3,170 targets. The reduction is deliberate: missing bounds, ambiguous
definitions, and mixed validity are no longer accepted. A boundary effect means
exact owned block membership changed; it does not imply a contiguous min/max
resize.

### Unresolved relevant CTR sites

There are 1,162 non-link CTR sites without a selected table. Every one has one
or more exact reasons in `jump-table-recovery.json`; reason counts overlap:

| Reason | Sites |
|---|---:|
| `missing_bound` | 727 |
| `ambiguous_reaching_definition` | 420 |
| `analysis_limit` | 159 |
| `ambiguous_bound` | 3 |
| `unknown_table_base` | 3 |
| `non_switch_indirect` | 1 |

`analysis_limit_hit` is therefore true, but no partial table is selected. The
report also classifies all link-register returns and callback/virtual calls;
their routine `non_switch_indirect` marker is not part of the 1,162 unresolved
CTR count.

### Static/Ghidra reconciliation

The final closure verifier passed schema 3/analyser 2.0.0 with 35,631
candidates, 55 `strong_new_function`, 198 `probable_new_function`, and all
three fixtures. The jump stage reclassified 2,672 former static candidates as
owned cases instead of omitted functions.

The exact locally generated Ghidra map was rerun in exact mode against 80
manifest overrides, 60,995 final ReXGlue ranges, 46,180 `.pdata` entries, and
3,170 jump cases. It produced 52,994 review differences in 11.652 s with peak
working set 1,665,273,856 bytes. Identity remained `exact_image_match`.
No exact Ghidra function entry overlapped a recovered case, so zero cases had
independent callable promotion from Ghidra. The canonical manifest was not
changed.

### Required fixtures

| Exact range | Role | Final result |
|---|---|---|
| `0x829647F0-0x82964800`, size `0x10` | virtual-dispatch leaf thunk | confirmed existing function; not a jump case; exact materializations `0x82961254`, `0x8296125C`, `0x82964B6C`, `0x82964B74`, `0x8296571C`, `0x82965730` |
| `0x82C03B28-0x82C03B44`, size `0x1C` | conditional callback leaf reached through callback-table `bctrl` | confirmed existing function; not a jump case; pointer storage `0x8200A190` |
| `0x829675E0-0x829675F0`, size `0x10` | virtual-dispatch leaf thunk | confirmed existing function; not a jump case; exact materializations `0x829650C4`, `0x829650CC`, `0x82966B4C`, `0x82966B60` |

The exact Ghidra map omits all three. No Ghidra match was forced; manifest,
manual/fault-walker, ReXGlue, and static evidence preserve their exact ranges.

## Synthetic and regression validation

The repository-integrated synthetic fixture uses PPC instruction words and
small in-memory regions only; it contains no Fable bytes. Its 25 test cases and
2,495 assertions cover all required idioms, classifications, failure codes,
CFG-safe bound selection, mixed validity, limits, fixpoint, oscillation
quarantine, manual comparisons, shared/overlapping tables, and independent
callable-case promotion.

Final commands/results on 2026-08-29:

```powershell
# ReXGlue
.\out\win-amd64\Release\unit_tests.exe "[jump-table]" --reporter compact
ctest --preset win-amd64-release -L unit --output-on-failure
ctest --preset win-amd64-release --output-on-failure

# Fable2Recomp
python -m unittest discover -s .\tests -v
python .\tools\Verify-Fable2MigrationLedger.py
python .\tools\Verify-Fable2EntrypointClosure.py
fable2-codegen
fable2-build
```

- focused jump-table suite: 25/25 cases, 2,495/2,495 assertions;
- SDK unit label: 252/252 passed in 3.75 s; four pre-existing BitStream tests
  retained their configured skipped status;
- complete SDK suite: 1,713/1,713 passed in 35.56 s, including 1,458 PPC and
  three fault-walk tests; the same four BitStream skips remained;
- Fable2Recomp Python suite: 10/10 passed in 0.038 s;
- migration ledger: all 32 entries, with 60,758 definitions, declarations,
  mappings, and registrations; `setjmp=0x83006C90`,
  `longjmp=0x82CAFA30`, and `0x82E8C8E8` search semantics preserved;
- closure verifier: PASS with the exact counts and fixture evidence above;
- full exact codegen: PASS in 84.1 s, 52 files written, 541 unchanged, zero
  deleted;
- full release build: PASS and linked `fable2.exe` against
  `0.10.0.14-dev.gb228ae4`.

Codegen retained pre-existing non-fatal diagnostics: function `0x82242F10` is
2,533,663 bytes versus the 1,048,576 warning threshold; unresolved conditional
branches remain around `0x82C90070` from `0x82C90190`, `0x82C932D0`,
`0x82C937E0`, and `0x82C93738`; unresolved direct targets include
`0x82C93FF8` from `0x82C94044` and `0x82DACA04` from `0x82DACA28`. Codegen and
the build complete despite those existing warnings.

## Performance

| Measurement | Baseline | Final | Change |
|---|---:|---:|---:|
| exact entrypoint pipeline | 54,684 ms | 80,591 ms | +25,907 ms (+47.4%) |
| peak working set | 1,066,323,968 B | 1,175,814,144 B | +109,490,176 B (+10.3%) |
| dedicated recovery pass | not present | 145,221 us | n/a |
| recovery-decoded instructions | not recorded | 14,684 | n/a |
| max per-function fixpoint iterations | not present | 5 | below limit 8 |

The dedicated pass is about 145 ms; most end-to-end growth comes from the
larger exact CFG/closure/report data. Full codegen after invalidating only the
ignored codegen stamp took 84.1 s. Historical 43.275 s frozen and 50.430 s
initial-v0.10 codegen measurements used different SDK revisions and are not
treated as controlled before/after results.

## Smoke result

A bounded post-build run used:

```powershell
.\tools\Invoke-Fable2BringUpIteration.ps1 `
    -Iteration 1 `
    -RunDirectory .\out\jump-table-smoke `
    -SkipCodegen -SkipBuild -ManualInput -GracefulStop -MonitorSeconds 30
```

Run `016` exited early with the existing discovery-class failure at
`fable2-run-016.log:477`:

```text
[FATAL] Call to invalid or unregistered function: target=0x8223FD7C, ctx.lr=0x8223FAD8, probable caller=0x8223FAD4, ctx.ctr=0x8223FD7C
```

`0x8223FD7C` is not a recovered jump case, closure candidate, or exact Ghidra
function. It lies in `.pdata` owner `[0x8223F988,0x822404FC)`, whose exact final
body fragments are `[0x8223F988,0x8223FBB0)` and
`[0x822404A4,0x822404FC)`. The target is inside the owner's min/max extent but
outside body membership, so this smoke failure is not a switch-case
misregistration. No manifest entry was guessed. This was a startup smoke test,
not gameplay validation.

## Limitations and next integration point

- The 1,162 unresolved CTR sites are deliberately conservative. Increase
  predecessor/state/backward limits only in a measured comparative run; do not
  turn valid-prefix or nearby-compare heuristics back on.
- Current recovery covers the Xenon idioms observed and tested here, not every
  possible computed transfer. Opaque arithmetic, path-dependent bases, or
  unsupported relative encodings remain reported for manual review.
- Manual tables are supported and authoritative, but the exact Fable TU1
  configuration presently has none, so real manual equivalence/conflict counts
  are zero; synthetic tests prove those paths.
- `analysis_limit_hit=true` records bounded incompleteness, not acceptance of a
  partial result.
- Ghidra remains evidence only. `.pdata` establishes entry association, not a
  contiguous body, and Ghidra names never establish boundaries.
- The ignored `out/analysis/.../jump-table-recovery.json` is the only sensible
  full list of 68,483 classified sites and 1,162 exact unresolved records; its
  SHA-256 above protects that uncompressed local evidence without committing
  private-adjacent bulk reports.

The precise next boundary-validation input is the schema-3 closure plus exact
Ghidra diff, after subtracting the 3,170 owned cases. Start with narrow runtime
call evidence such as `0x8223FD7C`, determine exact body membership versus a
callable internal/separate entry from TU1 control flow, and feed only confirmed
entry evidence back into the shared model. Xenia tracing and runtime bulk
import are later stages and were not started here.
