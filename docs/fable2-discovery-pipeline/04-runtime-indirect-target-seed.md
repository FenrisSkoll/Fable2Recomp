# Runtime indirect-target seed: `0x82174734`

## Outcome

Static investigation and implementation are complete. Runtime closure is
**pending the two person-controlled checks described at the end of this
handoff**.

`0x82174734` is **CONFIRMED to be an internal switch case/basic block**, not a
function, callable internal entry, thunk, callback, virtual method, exception
fragment, or corrupted pointer. Both reported outer callsites make ordinary
linked direct calls to `0x821746A8`. That common function loads an absolute
target from its inline 29-entry table and executes a non-linking `bctr` at
`0x821746BC`. Twenty-three entries target `0x82174734`; six target the sibling
case `0x8217473C`.

The omission is a **CONFIRMED Phase 3 regression**. Retained coherent
pre-Phase-3 generated output emits the exact 29-case switch and both internal
labels. Phase 3 output instead emitted `REX_CALL_INDIRECT_FUNC` and, through
gap fill, incorrectly exposed sibling case `0x8217473C` as a standalone
registration. The generic Phase 3 entry-domain proof saw four callers in their
preliminary CFGs, but two further callers became reachable only through
independently validated local switch edges. Rejecting that incomplete inbound
census left dispatch `0x821746BC` unresolved as `missing_bound`.

ReXGlue now performs a side-effect-free local caller reanalysis only when the
direct callsite is absent from the caller's preliminary CFG. That reanalysis
may consume independently validated local/manual tables, but receives no
entry-domain evidence and therefore cannot circularly prove the downstream
table. The complete six-caller census proves the exact dense domain
`r3=0..28`. Existing conservative validation then selects the exact table.

No Fable address is special-cased. No manifest entry, manual table,
`RETURN_R3_ZERO`, stub, suppression, callable registration, or weakened
validation was added. The manifest remains byte-identical. The final generated
owner contains explicit case edges; neither case is declared or registered as
a function.

This address is a Phase 4 golden **classification/negative-import** case: a
future Xenia collector/importer should preserve the runtime observation,
resolve the actual indirect dispatch, recognize the recovered owner case, and
refuse to import `0x82174734` as a callable function. It is not a golden
positive manifest-function import.

Evidence labels below use **CONFIRMED**, **INFERRED**, and **HYPOTHESISED** in
the project-defined sense.

## Repository, image, and analyzer identity

The audit began from these clean canonical identities:

| Component | Branch | Starting full commit | Tracking state at start |
| --- | --- | --- | --- |
| Fable2Recomp | `fable2-rexglue-0.10-migration` | `52e7d12073d41901020b2962d33f7d021e410605` | tracking `origin/fable2-rexglue-0.10-migration`, ahead 5, behind 0; clean |
| ReXGlue | `fable2-v0.10-migration` | `98e1898b43a14727af507241aacecf290ddc9d8e` | tracking `origin/fable2-v0.10-migration`, ahead 26, behind 0; only documented `thirdparty/libmspack` materialisation |

Final implementation identities are:

| Component/state | Full commit or identity |
| --- | --- |
| ReXGlue generic correction | `ec277f6bb51705cbe3da618acd9516e387acd265` |
| ReXGlue bounded fast-path correction | `16d7915550676121667a5155a96216e9e42bbad8` |
| installed ReXGlue identity | `0.10.0.42-dev.g16d7915` |
| parent SDK integration | `f6bfb534cd872265e1b0311b5acb36be6fcc1605` |
| documentation commit | obtain with `git log -1 --format=%H -- docs/fable2-discovery-pipeline/04-runtime-indirect-target-seed.md` |

The installed SDK is isolated at:

```text
C:\Dev\Fable2Phase4Seed\install-final-16d7915
```

The exact private TU1 identity is unchanged:

| Property | Value |
| --- | --- |
| patched image SHA-256 | `BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00` |
| executable-memory fingerprint | `5C8B78B84C93028D166E3DF347206E6642BA40BF374AD1AF8D958B2211320357` |
| image base / size / entry | `0x82000000` / `0x01620000` / `0x82CC21C0` |
| title / media / version | `0x4D5307F1` / `0x716F0A0D` / `0.0.1.26` |
| manifest SHA-256 before/after | `E3EB39CA153E396D5DC53E6F943ED8FF7AF1D6B0704EB860836BD7D21A3F87B0` |
| entrypoint-closure schema/analyzer | schema 3 / analyzer `2.0.0` |
| jump-table schema/analyzer | schema 3 / analyzer `3.0.0` |

The context reconstruction read every repository `AGENTS.md`, inventoried all
Markdown under `docs`, and read the relevant complete handoffs:

```text
docs/rexglue-0.10-migration.md
docs/fable2-fault-walker-baseline.md
docs/fault-walk.md
docs/fault-walk-performance.md
docs/fault-walk-harvest-001.md
docs/fault-walk-harvest-002.md
docs/fault-walk-harvest-003.md
docs/indirect-function-discovery.md
docs/fable2-discovery-pipeline/01-static-entrypoint-closure.md
docs/fable2-discovery-pipeline/02-ghidra-function-map.md
docs/fable2-discovery-pipeline/03-jump-table-recovery.md
docs/fable2-discovery-pipeline/03a-jump-table-regression-closure.md
```

No prior `04*` document or Phase 4 implementation existed. The authoritative
Phase 3 reports are the retained commit-exact pair under
`C:\Dev\Fable2Phase3Closure\closure-98e1898-final-run{1,2}`. The similarly
named report in the canonical ignored `out\analysis` directory is an older
726-table intermediate and was not used as the baseline.

## Original runtime records

The source records remain verbatim.

Crash A, after the dog-protection fight while walking toward the first missing
warrant, from `fable2-run-045.log` (SHA-256
`FAA80072BEDAA3048B838052625F5D157EB6D5809379546CA4F5E4A22934074F`):

```text
[2026-08-31 18:44:29.911] [critical] [core] [t27556] [FATAL] Call to invalid or unregistered function: target=0x82174734, ctx.lr=0x823DCADC, probable caller=0x823DCAD8, ctx.ctr=0x82174734
```

Crash B, pressing Start during the intro, from `fable2-run-046.log` (SHA-256
`688BA5F6B86FD76E79F110AB823DA0CDA100EDD6DE65E243287166E85DA1187A`):

```text
[2026-08-31 19:15:32.502] [critical] [core] [t28200] [FATAL] Call to invalid or unregistered function: target=0x82174734, ctx.lr=0x82403724, probable caller=0x82403720, ctx.ctr=0x82174734
```

The diagnostic's `probable caller` is LR-derived. In this case each address is
a real linked caller, but neither is the indirect dispatch PC.

## Both callers and the actual indirect transfer

### Crash A caller

| Field | Exact result |
| --- | --- |
| owner | `0x823DC9D8` |
| source PC | `0x823DCAD8` |
| raw instruction | `0x4BD97BD1` |
| decoded instruction | `bl 0x821746A8` |
| branch kind / LK | direct branch with link / `LK=1` |
| resulting LR | `0x823DCADC` |

The bounded dataflow is:

```text
0x823DC9E4  caller argument r4 -> r29
0x823DCACC  cmplwi cr6,r29,28
0x823DCAD0  bgt cr6,0x823DCAE0
0x823DCAD4  mr r3,r29
0x823DCAD8  bl 0x821746A8
```

Thus every path to the call proves unsigned `r3 <= 28`; the call passes an
exact copy of the guarded value.

### Crash B caller

| Field | Exact result |
| --- | --- |
| owner | `0x824036E0` |
| source PC | `0x82403720` |
| raw instruction | `0x4BD70F89` |
| decoded instruction | `bl 0x821746A8` |
| branch kind / LK | direct branch with link / `LK=1` |
| resulting LR | `0x82403724` |

Its bounded value comes through a global/object chain:

```text
0x824036F8  lis r31,-31927
0x8240370C  lwz r11,27400(r31)   ; global 0x83496B08
0x82403710  lwz r11,56(r11)
0x82403714  lwz r3,4(r11)
0x82403718  cmplwi cr6,r3,28
0x8240371C  bgt cr6,...
0x82403720  bl 0x821746A8
```

The two runtime paths therefore obtain their indices differently, but both
call the same exact dispatcher and use the same inline target table. They do
not load `0x82174734` independently from two vtables or callback structures.

### Common dispatcher

The actual CTR-producing sequence is:

```text
0x821746A8  0x3D808217  lis    r12,-32233
0x821746AC  0x398C46C0  addi   r12,r12,18112   ; r12 = 0x821746C0
0x821746B0  0x5460103A  rlwinm r0,r3,2,0,29    ; unsigned index * 4
0x821746B4  0x7C0C002E  lwzx   r0,r12,r0
0x821746B8  0x7C0903A6  mtctr  r0
0x821746BC  0x4E800420  bctr                       ; LK=0
```

The `bctr` preserves the LR created by the outer `bl`, so each case's `blr`
returns directly to the corresponding outer caller. This reconciles the two
linked runtime records with an internal switch-case classification.

Whole-image direct-call enumeration found six static callers of
`0x821746A8`:

| Callsite | Owner | Domain proof | CFG source |
| --- | --- | --- | --- |
| `0x8229AD88` | `0x8229ABD8` | unsigned adjacent guard, `r3=0..28` | preliminary |
| `0x823DCAD8` | `0x823DC9D8` | unsigned dominating exact-copy guard, `r3=0..28` | preliminary |
| `0x82403720` | `0x824036E0` | unsigned adjacent guard, `r3=0..28` | preliminary |
| `0x82403850` | `0x82403810` | unsigned adjacent guard, `r3=0..28` | preliminary |
| `0x82404F90` | `0x82404ED0` | unsigned adjacent guard, `r3=0..28` | validated case expansion at `0x82404F30` |
| `0x824050F0` | `0x82405030` | unsigned adjacent guard, `r3=0..28` | validated case expansion at `0x82405090` |

All six callsites are complete, target exactly `0x821746A8`, and have no
rejection or exhausted-budget evidence.

## Static evidence reconciliation

| Question | Confirmed answer |
| --- | --- |
| Manifest function? | No. |
| Ghidra function start? | No. Ghidra's relevant exact function is `FUN_821746a8`. |
| Contained by another Ghidra body? | No. The exact Ghidra body is `[0x821746A8,0x821746C0)` and stops before the inline table. |
| Exact `.pdata` entry? | No. |
| Inside an exact pre-recovery body fragment? | No. |
| Closure candidate before correction? | Yes: `probable_new_function`, based on `readonly_code_pointer`/`pointer_table_run`, but overlapping the table candidate and without callable evidence. |
| Closure result after correction? | `jump_table_case`, confirmed. |
| Jump-table case? | Yes, after the generic fix. |
| Recovered table targets it? | Yes: dispatch `0x821746BC`, owner `0x821746A8`. |
| Prior unresolved site? | `0x821746BC`, `missing_bound`, `insufficient_static_evidence`. |
| Explicit shared/manual evidence entry? | No. The shared provenance file contains no address-specific promotion for this target. |
| Generated code before correction? | The bytes at the target were not emitted in owner `sub_821746A8`; the owner used invalid-function dispatch. No `sub_82174734` existed. |
| Registration-only defect? | No. Correct owner code was missing as well as case reachability. |
| Static analyzer encountered it? | Yes: as table-like pointer evidence and as the unresolved dispatch's provisional target, but without a complete finite bound proof. |
| Exact static pointer occurrences? | 23 big-endian occurrences, all entries of this one inline table; no independent vtable/callback/global pointer occurrence. |
| Direct incoming branch? | None. |
| Exception/unwind/cold evidence? | None. |

This rules out an independently callable function, callable mid-function entry,
shared thunk, virtual method, callback, exception fragment, registration-only
failure, runtime-only discovery case, and corrupted target.

## Exact table, cases, and boundary

The selected table is:

| Field | Exact value |
| --- | --- |
| owner / dispatch | `0x821746A8` / `0x821746BC` |
| kind | absolute pointer |
| table storage | `[0x821746C0,0x82174734)` |
| element | unsigned 32-bit, width 4 |
| index / scale | `r3` / 4-byte address scale (`target_scale=1`) |
| finite domain | dense `0..28`, inclusive |
| case count | 29 |
| confidence | `validated_interprocedural_entry_domain_all_targets` |
| bound semantics | `interprocedural_entry_domain_zero_based_dense` |
| raw storage SHA-256 | `62A0E366AE26F726089F368AFA832E1677DB45ACEE22866866CA634FF6CB6A1D` |
| report raw-entry semantic SHA-256 | `E75BA5C9AAC3DD4681250427ADFA629F1176B53770AF40E664BF0DF26618CA07` |

Indices `4`, `5`, `9`, `11`, `12`, and `13` target `0x8217473C`; the other
23 entries target `0x82174734`. Table length comes solely from the complete
finite caller domain, never from an observed target, storage coincidence,
plausible decoding, or an unbounded memory probe.

The target blocks are:

```text
0x82174734  0x38600001  li r3,1
0x82174738  0x4E800020  blr
0x8217473C  0x38600000  li r3,0
0x82174740  0x4E800020  blr
```

The corrected owner has exact blocks `[0x821746A8,0x821746C0)` and
`[0x82174734,0x82174744)`, with labels `0x82174734` and `0x8217473C`.
The table storage is excluded from executable body membership. The block
boundary is justified by the validated table edge and each terminating `blr`,
not by numeric adjacency or Ghidra alone. Neither address has a callable
prologue or independent callability evidence.

## Phase 3 causality and generated-output comparison

The retained coherent pre-Phase-3 parent at
`C:\Dev\Fable2Phase3Closure\parent-a`, commit
`a8601e9469dd316c4618b23dd0415009f89453f1`, emits an explicit 29-case
switch in `sub_821746A8`, contains both case labels, and registers neither
case. Its relevant generated source SHA-256 is:

```text
fable2_recomp.78.cpp
AF2F46315FD962AFE0B5A92A2F557C0BA35C4AF19657C5E456892E636AC10914
```

The retained Phase 3 B output at
`C:\Dev\Fable2Phase3Closure\parent-b` emits:

```text
0x821746BC bctr -> REX_CALL_INDIRECT_FUNC(ctx.ctr.u32)
```

It omits both case bodies from `sub_821746A8`, then exposes
`sub_8217473C` through gap fill in both the initialization map and registration
table. It does not expose `0x82174734`. Its relevant SHA-256 is:

```text
fable2_recomp.78.cpp
A86C488DF79C3F6AB826A8B0C8F503A36AFF2A722B732A767DF8641829B9A2EF
```

The corrected canonical output again has SHA-256
`AF2F46315FD962AFE0B5A92A2F557C0BA35C4AF19657C5E456892E636AC10914`,
byte-identical to the retained pre-Phase-3 TU. It contains explicit case edges
and no `sub_82174734` or `sub_8217473C` declaration, definition, map entry, or
registration.

The inspected codegen cache fingerprints were:

```text
pre-Phase-3 parent A     6f38051e59deb8f3f5c4c62afc2c3795
Phase 3 parent B         845384defd0e74ee4aa688d982416bc6
canonical current        0679bda258702cf5cf9aa8df0fce9bcc
```

After changing SDK semantics, the first `fable2-codegen` invocation reported
the current module up to date. The canonical pre-regeneration
`codegen.stamp` and the newly regenerated stamp have the same fingerprint and
SHA-256
`0F79C865895467251FB8719FB72842D8F5DE93FB6CEB5057B8564E980238443D`;
the development SDK commit is not part of that cache identity. The exact
stale `codegen.stamp` and `codegen.build.stamp` were moved, not deleted, to
`C:\Dev\Fable2Phase4Seed\stale-codegen-stamps-pre-16d7915`. Only then was
normal codegen rerun. Making development codegen stamps commit-sensitive
remains a separate integration-hygiene task; it was not broadened into this
analyzer correction.

These facts satisfy the `phase3_regression` classification. They rule out
latent pre-existing omission and stale/mixed runtime binaries as the cause of
the original two failures. The stale codegen stamp was a separate integration
risk discovered and controlled before producing the test build.

## Generic correction and tests

Tracked SDK changes are limited to:

```text
include/rex/codegen/function_types.h
src/codegen/entrypoint_closure.cpp
src/codegen/phase_discover.cpp
tests/unit/codegen/jump_table_recovery_test.cpp
```

Structured callsite evidence now records:

```text
caller_cfg_kind
caller_cfg_jump_table_sites
reachable_only_after_case_expansion
```

The correction preserves the preliminary caller CFG as the fast path. It
attempts bounded local expansion only when that preliminary CFG does not
contain the exact callsite. Local expansion receives manual tables and
independently recoverable automatic tables, but no interprocedural entry-domain
input. A table may therefore expose a downstream callsite, but the downstream
entry domain cannot be used to prove the upstream table that exposed it.

The byte-free `[case-expanded-caller]` fixture contains a bounded upstream
absolute table whose validated case reaches a guarded direct call to a
downstream table owner. The positive control recovers the exact downstream
table only after validated case expansion. Its negative control corrupts the
upstream target; the downstream call remains unreachable and unresolved.
Existing entry-domain negatives continue to reject incomplete inbound
censuses, non-dominating/unrelated guards, transformed or incompatible copies,
invalid targets, altered raw entries, and circular/partial proofs.

Final focused commands and results:

```powershell
& .\out\win-amd64\Release\unit_tests.exe '[case-expanded-caller]'
# 557 assertions / 1 case, PASS

& .\out\win-amd64\Release\unit_tests.exe '[entry-domain]'
# 7,086 assertions / 7 cases, PASS

& .\out\win-amd64\Release\unit_tests.exe '[codegen][jump-table]'
# 35,371 assertions / 70 cases, PASS

ctest --test-dir .\out\build\win-amd64 -C Release --output-on-failure
# 1,761/1,761 PASS in 38.87 s; four pre-existing BitStream skips
```

The external targeted-owner harness permanently uses CMake
`TARGET_RUNTIME_DLLS`. It was relinked as AMD64 Release from the exact final SDK
tree, staged the matching `rexruntime.dll`, and was run non-interactively with
the canonical manifest:

```text
targeted_owner.exe SHA-256
7CE3F10CF017455450A1B0E91714BE861C5FAF2888DA6D248C7C533631E42B9F

staged rexruntime.dll SHA-256
2959A872AD32DA5528114DF14475E0C347D7E3E1B4D365539B73284BE42E2D00

exit code 0
stdout SHA-256 C72AC1E56EB691ED17909E3B87DEBE8FA6C54AC5F7944A9F5EC913A073DD35BA
stderr SHA-256 E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855
```

Its owner-only output confirms all six finite callers, expansion only through
`0x82404F30` and `0x82405090`, exact table `[0x821746C0,0x82174734)`, 29
cases, and first raw/target entry `0x821746C0 -> 0x82174734`. An earlier
invocation without the required manifest argument exited 2 with only
`usage: targeted_owner <project-manifest>`; it did not enter analyzer code and
is not a test failure.

## Commit-exact TU1 reports and delta

Final reports were generated after the SDK commits and final CLI relink:

```powershell
C:\Dev\Fable2Phase4Seed\install-final-16d7915\bin\rexglue.exe `
    entrypoint-closure C:\Dev\Fable2Recomp\fable2_manifest.toml `
    --provenance C:\Dev\Fable2Recomp\tools\fable2-entrypoint-closure-evidence.json `
    --output C:\Dev\Fable2Phase4Seed\closure-final-16d7915-run<1|2>
```

CLI identity and SHA-256:

```text
0.10.0.42-dev.g16d7915
AC29A12A3D94697E21378F02168F1AEA160F5F25F215965C9FE0F1C1D88021FA
```

All stable artifacts are byte-identical across the pair:

| Artifact | SHA-256 |
| --- | --- |
| `jump-table-recovery.json` | `B1FE26FB9119DAF7E7E0196CBDBA8CCA087BE190BF156FE0B12DF116379ED89A` |
| `jump-table-recovery.csv` | `9A72B6ACA134C8547EF28CEF001B9560A9AB012B52CC637C6D70E15CB7B6B043` |
| `jump-table-recovery.md` | `5606CD90D38E50A639406B67A5E649BD25D29E23C82C185C4BBADE6B53439980` |
| `entrypoint-closure.json` | `665CA2AE7ED65632B2E9F368063D3D9EE260E8DEF6F276B455CD62A9F2DCC397` |
| `entrypoint-closure.csv` | `BE3FBDCC70A3D1669072D586CDBA3B0EFA8A2919D93FDAF2CB68AA056E700DB2` |
| `entrypoint-closure.md` | `01EA27C1AE976662536ABF364A7B0AD9F5179931AE30115352C71577F5F399BF` |
| review TOML | `75453408A313F645C5FA683E00665BD81BBC153FCD766A2A73385D7D0DEAC473` |

Semantic delta against the true commit-exact Phase 3 final report:

| Metric | Phase 3 final | Corrected | Delta |
| --- | ---: | ---: | ---: |
| decoded recovery instructions | 38,041 | 38,049 | +8 |
| indirect sites | 69,279 | 69,280 | +1 |
| recovered tables | 877 | 878 | +1 |
| unique case targets | 9,000 | 9,002 | +2 |
| unresolved non-link CTR | 712 | 711 | -1 |
| maximum function fixpoint | 11 | 11 | 0 |
| manual tables | 0 | 0 | 0 |

Exact table audit:

```text
added                         0x821746BC
removed                       none
semantically changed existing none
case targets added            0x82174734, 0x8217473C
case targets removed          none
```

Unresolved reasons change only as expected:

```text
missing_bound          704 -> 703
unknown_table_base       7 -> 7
non_switch_indirect      1 -> 1
```

Classifications change only as expected:

```text
computed_tail_dispatch          602 -> 602
insufficient_static_evidence    109 -> 108
opaque_non_table_dispatch         1 -> 1
```

There remain zero confirmed, probable, plausible, or blocking switch misses,
and no complete valid unresolved diagnostic probe. Closure probable candidates
fall from 182 to 180 because `0x82174734` and `0x8217473C` become confirmed
cases; totals are 35,626 candidates, 55 strong, and 180 probable.

## Performance

The first unbounded implementation reanalyzed every caller through the full
local jump-table fixpoint. Commit `16d7915...` demonstrated and removed that
avoidable work: four already reachable callsites remain on cached preliminary
blocks, and only the two genuinely case-hidden callsites expand. The two
pre-optimization semantic runs took 91,185 ms and 109,450 ms. The final
commit-exact pair took 67,055 ms and 71,773 ms, reducing the median from
100,317.5 ms to 69,414 ms (-30.8%).

Comparison with the retained final Phase 3 pair:

| Measurement | Phase 3 runs | Corrected runs | Median change |
| --- | --- | --- | ---: |
| pipeline wall | 59,536 / 59,263 ms | 67,055 / 71,773 ms | +10,014.5 ms (+16.9%) |
| peak working set | 1,221,926,912 / 1,221,849,088 B | 1,221,320,704 / 1,220,747,264 B | -854,016 B (-0.07%) |
| jump-table dataflow recovery | 1,441,707 / 1,440,453 us | 1,430,064 / 1,465,103 us | +6,503.5 us (+0.45%) |
| discover phase | 8,354,877 / 8,364,458 us | 9,449,774 / 10,450,690 us | +1,590,564.5 us |
| gap-fill phase | 26,207,872 / 26,021,571 us | 32,199,203 / 35,004,654 us | +7,487,207 us |
| serialization total | 8,714,935 / 8,740,526 us | 9,019,234 / 8,998,852 us | +281,312.5 us |

The affected recovery stage is effectively flat and peak memory is slightly
lower. Most observed end-to-end variation is in downstream gap fill despite a
semantic delta of only one table/two blocks; no repeated whole-caller recovery
remains. The exact-block containment optimization is preserved. No limit was
raised and no analysis was weakened for speed.

## Parent validation, generated census, and build

Parent validation commands and results:

```powershell
python -m unittest discover -s .\tests -v
# 17/17 PASS

python .\tools\Fable2FunctionMap.py catalog
# 9 records, PASS

python .\tools\Verify-Fable2MigrationLedger.py
# all 32 harvest/sibling entries, PASS

python .\tools\Verify-Fable2EntrypointClosure.py `
    --report C:\Dev\Fable2Phase4Seed\closure-final-16d7915-run1\entrypoint-closure.json
# schema 3, 35,626 candidates, 55 strong, 180 probable, 3 fixtures, PASS

python .\tools\Fable2FunctionMap.py validate `
    .\out\analysis\BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00\ghidra-function-map.json
# 42,462 functions, exact image, PASS

python .\tools\Fable2FunctionMap.py diff <same-map> `
    --mode exact `
    --closure C:\Dev\Fable2Phase4Seed\closure-final-16d7915-run1\entrypoint-closure.json `
    --output-directory C:\Dev\Fable2Phase4Seed\ghidra-diff-final-16d7915
# 52,994 differences, manifest unchanged, PASS
```

Normal codegen initially no-op'd because of the stale commit-insensitive stamp.
After preserving only the two exact stamps externally, `fable2-codegen`
completed in 67.8 seconds: 6 files written, 587 unchanged, 0 deleted. The known
non-fatal `0x82242F10` maximum-file-size diagnostic remained.

The corrected generated census has 60,425 unique exact sub-address
definitions/declarations/mappings/registrations according to the migration
verifier. The broader raw generated macros contain 60,662 definitions and
60,917 registrations, exactly one fewer of each than the pre-correction output
because the accidental standalone `sub_8217473C` is gone. All 80 explicit
manifest entries remain registered. The three confirmed fixtures remain exact
functions:

```text
0x829647F0-0x82964800  size 0x10
0x82C03B28-0x82C03B44  size 0x1C
0x829675E0-0x829675F0  size 0x10
```

The final generated hashes include:

| Artifact | SHA-256 |
| --- | --- |
| `fable2_recomp.78.cpp` | `AF2F46315FD962AFE0B5A92A2F557C0BA35C4AF19657C5E456892E636AC10914` |
| `fable2_init.cpp` | `926FD29BBFE32FCAA314571E6EA4DEB86773C7383B5BA681C1DEF8EDE5CEB6BE` |
| `fable2_register.cpp` | `003A67FB8765C771413EF6535FDF8D8336544229FC2193F6DBD9C969E7952686` |

The first Release link was rejected as final evidence after audit found that
`rexglue_DIR` was current but cached `fmt_DIR`, `spdlog_DIR`, `SDL3_DIR`, and
`utf8cpp_DIR` still named the old Phase 3 prefix. That rejected executable was
SHA-256 `B2EFC7544BE5027C9382FF5EB818DDF6E05CDD4E4A122BE80C12217507FBDAC9`.
All five package paths were then explicitly reconfigured to the one final
install and the full 301-step Release build was repeated successfully.

The coherent test build is:

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `fable2.exe` | 105,042,944 B | `B8822AA5051FA64DE8EF008808E86F93B219C2AAC3A4839D4043F3CAD7C2A9F0` |
| `rexruntime.dll` | 10,198,528 B | `2959A872AD32DA5528114DF14475E0C347D7E3E1B4D365539B73284BE42E2D00` |
| `rexgpu-xenos.dll` | 2,770,944 B | `10CEF6D2B601D20F8BF75E87B807D899FB6E5D9012CC73A3072F4DA04D204A12` |
| `TracyClient.dll` | 232,960 B | `FDBE7A329E1B06A86FE61A2C5BE6B335F32F9BBCA7E05F7B183A35C515D2D1A5` |

All three DLL hashes match their exact files under
`install-final-16d7915\bin`. LLVM PE inspection reports `COFF-x86-64`,
`x86_64`, `IMAGE_FILE_MACHINE_AMD64` for the executable and all DLLs.
`CMAKE_BUILD_TYPE=Release`; `REXGLUE_ENABLE_FAULT_WALK=OFF` and
`REXGLUE_ENABLE_FAULT_WALK_DISPATCH=OFF`.

## Runtime gates and next action

No autonomous gameplay or gameplay automation was attempted. Static analysis,
tests, codegen, and the coherent Release build are complete. Runtime status is:

| Gate | Exact path | Status |
| --- | --- | --- |
| 1 | Press Start during the intro; prior failure `0x82403720 -> 0x82174734` | pending user validation |
| 2 | Progress beyond the dog-protection fight and walk toward the first missing warrant; prior failure `0x823DCAD8 -> 0x82174734` | not yet requested; run only after Gate 1 is understood |

The next action is for the user to run Gate 1 with the coherent build above and
return the numbered log or the exact failure diagnostic. Passing means only
that the exercised Start path passed its previous failure point without an
invalid/unregistered target, FWT intervention, fatal, assertion, host
exception, or suppression loop. Gate 2 requires a separate explicit result.

If either path reaches a new unrelated blocker, preserve it verbatim for a
subsequent task. Do not convert that unrelated address into another target in
this task unless evidence proves the same generic caller-domain root cause.

## Commits, worktree policy, and retained limitations

Local commits created so far:

```text
ec277f6bb51705cbe3da618acd9516e387acd265  Recover entry domains through validated caller cases
16d7915550676121667a5155a96216e9e42bbad8  Limit caller case expansion to unreachable callsites
f6bfb534cd872265e1b0311b5acb36be6fcc1605  Pin ReXGlue indirect case recovery
```

The SDK worktree retains only the pre-existing materialized
`thirdparty/libmspack` status. The parent tracked tree is clean before this
documentation change. Generated sources, reports, harness logs, patched-image
data, and other private-adjacent artifacts remain ignored or external.

Known limitations:

- Runtime closure remains pending both user-owned gameplay gates.
- The development codegen cache fingerprint is not SDK-commit-sensitive; the
  exact stamp must be invalidated after analyzer-only development changes until
  a separate generic cache-identity fix is designed.
- The 711 unresolved non-link CTR transfers remain conservatively classified;
  this correction does not claim they are functions or switches.
- Ghidra has no body/function/unwind evidence at either case. Its omission is
  consistent with the internal-case result but was not used alone to prove it.
- Xenia comparison was not needed to establish this exact table and was not
  performed.

Nothing was pushed, merged, tagged, released, uploaded, or opened as a pull
request. No private executable, executable-derived byte dump, raw memory dump,
bulk report, screenshot, credential, or raw runtime trace was committed.
