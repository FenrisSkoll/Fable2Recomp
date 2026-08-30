# Phase 3 jump-table regression closure

## Outcome

The original `0x8223FD7C` failure is **CONFIRMED to be a Phase 3 regression**.
The coherent pre-Phase-3 pair completed three matched observations without an
invalid dispatch, while the starting Phase 3 pair failed three times at the
same target. The actual transfer is the non-link `bctr` at `0x8223FBAC` in
owner `0x8223F988`. It selects an eight-entry relative halfword table at
`0x820110E0`; raw entry `0x01CC`, anchored at `0x8223FBB0`, resolves exactly to
`0x8223FD7C`. The target is a switch case, not a function, exception fragment,
or corrupted address.

Generic loop, re-entry, merged-index, case-expansion retention, and stack-load
lineage corrections now recover this table and the later runtime-implicated
tables at `0x822DDA18` and `0x82CB8D6C`. No case was registered as a function,
and `fable2_manifest.toml` remains byte-identical.

The avoidable performance regression is also closed. Phase 3 made ubiquitous
address-containment queries scan exact block vectors before a cheap range
rejection. Caching the exact-block envelope and rejecting addresses outside it
removed the demonstrated quadratic component. A controlled instrumented run
dropped from `85.348 s` to `67.805 s`; its gap-fill component dropped from
`54.944 s` to `34.284 s`. The final authoritative pipeline completed in
`58.163 s`, despite analyzing 6,359 unique cases rather than the starting
3,170.

The overall regression closure is nevertheless **not complete**. The one final
runtime matrix deterministically exposed another old-heuristic table that the
new conservative analysis still rejects: source `0x82CB6154`, target
`0x82CB6158`, owner `0x82CB6060`. It is a 12-entry relative byte state-machine
switch at `0x820116E0`, anchored at `0x82CB6158`. The old coherent output emits
all 12 case labels; the final report rejects the site only as
`ambiguous_reaching_definition`. This is the next focused correction. No
second closure/install/codegen/build/runtime cycle was started.

Evidence labels below use the project meanings of **CONFIRMED**, **PROBABLE**,
and **HYPOTHESIS**.

## Repository and image identity

| State | Fable2Recomp | ReXGlue SDK | Installed identity |
| --- | --- | --- | --- |
| coherent pre-Phase-3 A | `a8601e9469dd316c4618b23dd0415009f89453f1` | `fe1ae388007b17670e0386fce920d9e60bb2ab6e` | `0.10.0.8-dev.gfe1ae38` |
| starting Phase 3 B | `05e6ecb53ab5fd450d04e5f80001af423a71474b` | `b228ae46d93b26e1ff7aca201102d6cb62d56318` | `0.10.0.14-dev.gb228ae4` |
| final SDK analysis | parent starting Phase 3 tree | `32deea2910986a6898e29c797d61b5c0f9008033` | `0.10.0.29-dev.g32deea2` |
| final parent integration | `dbbc9e5e263b6a0de867ea6dc69f26acb6d41392` | `32deea2910986a6898e29c797d61b5c0f9008033` | `0.10.0.29-dev.g32deea2` |

The documentation commit is the commit containing this file; its full hash is
reported in the session closeout because a commit cannot contain its own hash.

All static and runtime work used the exact private GOTY TU1 input:

| Property | Value |
| --- | --- |
| patched image SHA-256 | `BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00` |
| image base / size | `0x82000000` / `0x01620000` |
| entry point | `0x82CC21C0` |
| title / media ID | `0x4D5307F1` / `0x716F0A0D` |
| version | `0.0.1.26` |
| manifest SHA-256 before and after | `E3EB39CA153E396D5DC53E6F943ED8FF7AF1D6B0704EB860836BD7D21A3F87B0` |

The initial audit found the canonical parent on
`fable2-rexglue-0.10-migration`, tracking its same-named origin with no local
change. The SDK was on `fable2-v0.10-migration`, tracking its same-named origin;
its only status entry was and remains the documented materialized
`thirdparty/libmspack` state. No canonical worktree was switched between A and
B. The parent is now ahead by the local integration and documentation commits;
the SDK is ahead by the 15 local Phase 3 closure commits listed below.

The audit also located the established behavioral records:

- ReXGlue v0.10 normal Run 013: `fable2-run-013.log`, SHA-256
  `BAB33B24A0465D43770F62EC0BEF352A791EE8B64038F80F2288F9ED71F78296`,
  reached controllable Bowerstone Old Town with no invalid dispatch;
- Phase 2 Run 015: a 564,050-byte log with no `REX_FATAL`, invalid function,
  unhandled exception, or fatal match;
- Phase 3 Run 016: `fable2-run-016.log:477`, target `0x8223FD7C`.

## Isolated A/B layout and commands

The coherent configurations were kept under `C:\Dev\Fable2Phase3Closure`:

```text
sdk-a       fe1ae388007b17670e0386fce920d9e60bb2ab6e
sdk-b       b228ae46d93b26e1ff7aca201102d6cb62d56318
install-a   exported 0.10.0.8-dev.gfe1ae38
install-b   exported 0.10.0.14-dev.gb228ae4
parent-a    a8601e9469dd316c4618b23dd0415009f89453f1
parent-b    05e6ecb53ab5fd450d04e5f80001af423a71474b
```

The reproducible command shape was:

```powershell
git -C C:\Dev\Fable2Recomp worktree add --detach `
    C:\Dev\Fable2Phase3Closure\parent-a `
    a8601e9469dd316c4618b23dd0415009f89453f1
git -C C:\Dev\Fable2Recomp worktree add --detach `
    C:\Dev\Fable2Phase3Closure\parent-b `
    05e6ecb53ab5fd450d04e5f80001af423a71474b
git -C C:\Dev\rexglue-sdk-v0.10 worktree add --detach `
    C:\Dev\Fable2Phase3Closure\sdk-a `
    fe1ae388007b17670e0386fce920d9e60bb2ab6e
git -C C:\Dev\rexglue-sdk-v0.10 worktree add --detach `
    C:\Dev\Fable2Phase3Closure\sdk-b `
    b228ae46d93b26e1ff7aca201102d6cb62d56318

Push-Location C:\Dev\Fable2Phase3Closure\sdk-a
cmake --preset win-amd64 `
    -DCMAKE_INSTALL_PREFIX=C:\Dev\Fable2Phase3Closure\install-a
cmake --build --preset win-amd64-release
cmake --install C:\Dev\Fable2Phase3Closure\sdk-a\out\build\win-amd64 `
    --config Release --prefix C:\Dev\Fable2Phase3Closure\install-a
Pop-Location

Push-Location C:\Dev\Fable2Phase3Closure\sdk-b
cmake --preset win-amd64 `
    -DCMAKE_INSTALL_PREFIX=C:\Dev\Fable2Phase3Closure\install-b
cmake --build --preset win-amd64-release
cmake --install C:\Dev\Fable2Phase3Closure\sdk-b\out\build\win-amd64 `
    --config Release --prefix C:\Dev\Fable2Phase3Closure\install-b
Pop-Location

Push-Location C:\Dev\Fable2Phase3Closure\parent-a
cmake --preset win-amd64-rexglue-0.10-release `
    -Drexglue_DIR=C:\Dev\Fable2Phase3Closure\install-a\lib\cmake\rexglue
cmake --build --preset win-amd64-rexglue-0.10-release `
    --target fable2_codegen
cmake --build --preset win-amd64-rexglue-0.10-release
Pop-Location

Push-Location C:\Dev\Fable2Phase3Closure\parent-b
cmake --preset win-amd64-rexglue-0.10-release `
    -Drexglue_DIR=C:\Dev\Fable2Phase3Closure\install-b\lib\cmake\rexglue
cmake --build --preset win-amd64-rexglue-0.10-release `
    --target fable2_codegen
cmake --build --preset win-amd64-rexglue-0.10-release
Pop-Location
```

Both caches record the explicit `rexglue_DIR`; both SDK caches record their
separate install prefix. Generated directories and native build directories
were separate. Both runtime configurations used the same private assets,
Release toolchain, launch arguments, no-input sequence, 19-second setup, and
30-second observation request:

```powershell
.\tools\Invoke-Fable2BringUpIteration.ps1 `
    -Iteration <1..3> `
    -RunDirectory .\out\phase3-regression-ab `
    -BuildPreset win-amd64-rexglue-0.10-release `
    -MonitorSeconds 30 `
    -SkipCodegen -SkipBuild -ManualInput -GracefulStop
```

## Coherent A/B artifact hashes

| Artifact | A | B |
| --- | --- | --- |
| installed `rexglue.exe` | `E0E7716B52A34707DC282AA70D761BCE21012E739A06B791D811F2CADAE9FC98` | `DE8CE19D4AE7C65AA5FC541A19079443CF7E644240E2C43ABECF7B144BFE3EE4` |
| `CMakeLists.txt` | `DB01F6E5802A7C6072C3072A88860252BA2760263A4B6D3A70E64DF065112D70` | `B491930432FF15E529045E8D06FF50AECA3A714D6AC80C149675D39D8CA6D29D` |
| configured `CMakeCache.txt` | `0CD4F4E54015F2973B7E09B4962B02F274523304DB7D0B1AA1A3264C563C533A` | `6CA8EFF5F16510543C72189949F174225E400FE9128E1B777729946E9EACB4B0` |
| generated `fable2_init.cpp` | `D72B8D9BC46C9C338427EA11D38FC9175B2E2487FCD9434D94A29FC941FC70F0` | `5087CA20DE30558F0876BD0DE068CB339B469961EE9108DF4538C3C1CE4617FD` |
| generated `fable2_register.cpp` | `F2D5418D375616462763222C9863BDF1BDA486F80DEA5D640BBDEFFC0BE985D5` | `4CE466A720988CD27BD6BB508F44F92A718A46CF5156B164E4ACFCA4D669587B` |
| generated partition report | `DD987285BBC3591A91516E382C31522A918F193702BCA71FD949C7009A0952FC` | `8D2662068DD1BFC6ADCCF981A234881AD8962D67EF344FC2D6B060CF873AF0FB` |
| native `fable2.exe` | `48AAAB0FD85E5A1A672A5092FCFF7787FEC2588F689A85617D7B7DAFCCAE8DFB` | `4CE8C0A75F2BB133D5E79C0F50A31689B5DFDDB4D27EA2BF32D7E2746D513733` |
| measured-01 closure JSON | `04EDF9873F5B06A46A8C959AA7ED62899816762F695A03BCBB62A9D4851C4ADD` | `DDE1365F3A54F932EEDBF18B54731CB253FCAB1E251722BE67D46F8E9460D868` |
| manifest | `E3EB39CA153E396D5DC53E6F943ED8FF7AF1D6B0704EB860836BD7D21A3F87B0` | same |

The early captured guest mapping hash was also identical in both configurations:
`5A6ADBDA1714AABC63BD7F6D52B55BCAAAD9B6F3F81907D93C1FFE830B22E59F`.

## A/B runtime matrix

| Config | Attempt | Start / end, local | Classification | Exit | Milestone / relevant match |
| --- | ---: | --- | --- | --- | --- |
| B | 1 | `2026-08-29 23:02:31` / `23:02:50` | `InvalidUnregisteredFunction` | `0xC0000409` | `0x8223FD7C` |
| A | 1 | `2026-08-29 23:03:11` / `23:04:01` | `PostInputTimeout` | `0x00000000` | responsive, no fatal |
| B | 2 | `2026-08-29 23:04:10` / `23:04:29` | `InvalidUnregisteredFunction` | `0xC0000409` | `0x8223FD7C` |
| A | 2 | `2026-08-29 23:04:38` / `23:05:27` | `PostInputTimeout` | `0x00000000` | responsive, no fatal |
| B | 3 | `2026-08-29 23:05:52` / `23:06:11` | `InvalidUnregisteredFunction` | `0xC0000409` | `0x8223FD7C` |
| A | 3 | `2026-08-29 23:06:16` / `23:07:06` | `PostInputTimeout` | `0x00000000` | responsive, no fatal |

All six runs had `ManualInput=true` and an empty input-event list. There was no
FWT, host exception, assertion, or suppression-loop match. The B process exited
on the fatal before the observation timeout; A was gracefully stopped after the
requested observation.

This matrix is coherent and causal: the image, assets, build type, launch
arguments, capture point, and input sequence match, while the paired parent and
SDK commits change together. The baseline emits the switch and does not fail;
starting Phase 3 does not emit it and fails 3/3.

## Exact `0x8223FD7C` transfer and classification

The runtime diagnostic recorded target and CTR `0x8223FD7C`, LR
`0x8223FAD8`, probable caller `0x8223FAD4`, and the guest thread in each log.
LR was not the switch source. Static control flow identifies:

```text
owner                 0x8223F988 [.pdata: 0x8223F988-0x822404FC)
source                 0x8223FBAC
instruction            0x4E800420, bcctr/bctr, LK=0
CTR definition         0x8223FBA4, mtctr r12
target construction    r12 = 0x8223FBB0 + zero_extend_u16(table[r11])
index normalization    srawi/rlwinm to r11
bound                  cmplwi r11,7; unsigned r11 <= 7
default                0x822404A4
storage                0x820110E0-0x820110F0
entry width/sign       2 bytes, unsigned
target scale           1
raw target entry       0x01CC at 0x820110E0
resolved target        0x8223FBB0 + 0x01CC = 0x8223FD7C
```

All eight decoded targets validate:

```text
0x8223FD7C  0x8223FBB0  0x8223FBD0  0x8223FC20
0x8223FC6C  0x8223FC74  0x8223FCAC  0x8223FDCC
```

At the starting Phase 3 state, `0x8223FD7C` was outside the owner's then-exact
fragments `[0x8223F988,0x8223FBB0)` and `[0x822404A4,0x822404FC)`, absent from
the manifest, closure candidates, recovered cases, and exact Ghidra functions.
That evidence correctly rejected it as a callable function, but did not prove
it was invalid. Final generic recovery adds the target to the owner's CFG as a
case. It remains absent from function registration. Final classification:
**CONFIRMED Phase 3 regression; unrecovered switch/case landing pad**.

## Batch static audit and generic corrections

The repeated runtime cycle was paused and every unresolved non-link CTR site
was classified from the authoritative report. The final batch artifact is
`C:\Dev\Fable2Phase3Closure\batch-audit-32deea2`; its source report hash is
`5CF2648FB089EF48522F0A8AC13DBD9FE707392FC446CD3556206E9A468091FB`.

### Final failure census

| Exact reason | Sites |
| --- | ---: |
| `missing_bound` | 726 |
| `ambiguous_reaching_definition` | 58 |
| `analysis_limit` | 45 |
| `unknown_table_base` | 7 |
| `mixed_validity_targets` | 2 |
| `ambiguous_bound` | 1 |
| `non_switch_indirect` | 1 |
| `target_out_of_range` | 1 |
| `unknown_index` | 1 |
| total | 842 |

| Normalized dataflow family | Sites |
| --- | ---: |
| `pointer_chain_tail_dispatch` | 644 |
| `absolute_indexed_lwzx_scaled` | 95 |
| `single_loaded_pointer_tail_dispatch` | 47 |
| `relative_indexed_lhzx` | 25 |
| `relative_indexed_lbzx` | 19 |
| `indexed_lwzx_unscaled` | 6 |
| `unresolved_register_tail_dispatch` | 3 |
| `relative_indexed_lwzx` | 2 |
| `register_copy_tail_dispatch` | 1 |

Twenty-one unresolved sites are in case-expanded CFGs, 814 are in owners with
no recovered table, and seven are in preliminary/shared contexts. Twenty-eight
sites across 14 owners are in recovered owners. The residual clusters retain
their exact reasons; no mixed-validity prefix was accepted. The 45 remaining
`analysis_limit` sites are not the corrected stack-lineage pattern. In
particular, case-expanded sites `0x82C96730` and `0x82C9AB68` remain rejected.

The generic corrections were developed with single-site/single-owner probes and
byte-free synthetic tests. Full closure/build/runtime work was deferred until
the batch fixpoint. The corrections cover:

- loop-carried and re-entrant switches;
- delayed guards, including VMX128 stores that do not clobber the guard;
- locally transformed and conservatively merged indices;
- preservation of incomplete paths without accepting partial tables;
- retention of the exact prior automatic table after case expansion, only when
  the initial failure is exactly `analysis_limit` and a bounded retry validates
  identical metadata, storage, raw entries, and targets;
- stable `r1+offset+width` load lineage without recursively exploring the
  entire function merely to resolve the PPC stack pointer.

No address-specific SDK rule was added.

### `0x822DDA18` retention lifecycle

The focused byte-free fixture proves the required lifecycle exactly:

1. preliminary analysis validates the automatic table with no failures;
2. case-expanded analysis with `max_states=64` has no selected table and the
   exact failure set `[analysis_limit]`;
3. a direct retry changing only `max_states` to `2048` validates the exact same
   table with no failures;
4. `max_backward_instructions`, `max_predecessors`, and `max_entries` remain
   unchanged;
5. changing one prior raw-entry target by four bytes causes rejection, retains
   `[analysis_limit]`, and reports `exact_prior_table_match=false`.

The structured evidence fields are:

```text
exhausted_budget          max_states
initial_budget_value      64
retry_budget_value        2048
initial_failures          [analysis_limit]
retry_failures            []
exact_prior_table_match   true
accepted                  true
```

The real TU1 site is `0x822DDA18`, owner `0x822DD908`, an absolute 38-entry
word table at `[0x822DDA1C,0x822DDAB4)`. Its unsigned index bound is 37 and its
default is `0x822DD99C`. Targeted probing established that 512, 4,096, and 8,192
states fail only with `analysis_limit`, while 16,384 validates. Production
therefore changes only `max_states`, from 512 to 16,384, and reports:

```text
initial_failures=[] before expansion
expanded initial_failures=[analysis_limit]
retry_failures=[]
exact_prior_table_match=true
accepted=true
confidence=validated_after_expanded_cfg_limit_retry
```

This restores case `0x822DDB50`; it does not register it as a function.
Temporary `fprintf` diagnostics used to identify the exhausted budget were
removed before commit.

### `0x82CB8D6C` stack-lineage state explosion

The next runtime target `0x82CB9210` came from source `0x82CB8D6C`, not the
stale LR-derived `0x82CB8CD8`. The exact switch is:

```text
owner        0x82CB8888
source       0x82CB8D6C, 0x4E800420, bctr, LK=0
index        r11 = r19 - 99
bound        unsigned r11 <= 24
storage      0x82011960-0x82011992
kind         relative unsigned halfword, 25 cases
anchor       0x82CB8D70
target       raw 0x04A0 -> 0x82CB9210
```

Increasing only `max_states` through one million still failed because the
resolver enumerated redundant CFG states while resolving `r1` for a
stack-relative reload. The correction represents a direct load based on `r1`
as stable `InputRegister(1)` lineage, retaining the offset and width. It does
not increase a budget. The synthetic fixture recovers a 25-case relative
halfword switch at 512 states; changing only the load base to unknown `r2`
fails exactly with `[analysis_limit]`.

## Authoritative TU1 delta audit

The final closure was run once after the batch fixpoint:

```powershell
rexglue entrypoint-closure `
    C:\Dev\Fable2Recomp\fable2_manifest.toml `
    --provenance .\tools\fable2-entrypoint-closure-evidence.json `
    --output C:\Dev\Fable2Phase3Closure\closure-32deea2-final
```

An accidentally started CLI still identified itself as `.28`; it was stopped
immediately before report completion and produced no retained authoritative
report. The completed `.29` report is the only final report.

| Count | starting Phase 3 | `.28` pre-stack fix | final `.29` |
| --- | ---: | ---: | ---: |
| tables | 342 | 721 | 726 |
| owners / boundary effects | 331 | 613 | 618 |
| unique cases | 3,170 | 6,276 | 6,359 |
| absolute / relative | 306 / 36 | 647 / 74 | 647 / 79 |
| byte / halfword / word | 31 / 5 / 306 | 47 / 27 / 647 | 48 / 31 / 647 |
| static candidates reclassified | 2,672 | 5,089 | 5,095 |
| unresolved non-link CTR | 1,162 | 847 | 842 |
| recovery-decoded instructions | 14,684 | 29,156 | 30,450 |
| maximum function fixpoint | 5 | 4 | 4 |

The 384 net tables since the starting Phase 3 report break down as +341
absolute tables and +43 relative tables. The width census changes by +17 byte,
+26 halfword, and +341 word tables. These are the loop/re-entry, transformed
index, conservative merge, exact retry, and stack-lineage categories above;
they are not manifest additions.

The exact `.28 -> .29` audit found five added, zero removed, and 16
metadata-only changed tables. Every added site previously failed exactly with
`analysis_limit` and validates completely after stable stack lineage:

| Site | Owner | Form | Cases / unique | Storage |
| --- | --- | --- | ---: | --- |
| `0x82CB8D6C` | `0x82CB8888` | relative halfword | 25 / 10 | `0x82011960-0x82011992` |
| `0x82F89828` | `0x82F88F48` | relative halfword | 11 / 9 | `0x820430B0-0x820430C6` |
| `0x82F8AA4C` | `0x82F8A150` | relative halfword | 11 / 9 | `0x820430C8-0x820430DE` |
| `0x831A8C34` | `0x831A8A58` | relative byte | 14 / 10 | `0x820808B8-0x820808C6` |
| `0x8320D2F0` | `0x8320C7D0` | relative halfword | 88 / 45 | `0x8208E7F8-0x8208E8A8` |

Two other former `analysis_limit` sites remain rejected with more precise
reasons: `0x822E1CE0` is `ambiguous_reaching_definition`, and `0x831AD334` is
`ambiguous_bound`.

The 16 existing tables below retain identical table kind, address, range,
bound, default, raw entries, and targets. Ten changed only confidence text and
six changed only instruction evidence because stack-load lineage is now
explicit:

```text
0x822EB468  0x822FB42C  0x8258C794  0x82A3C11C
0x82BE3AAC  0x82C00248  0x82C91468  0x82D87B7C
0x82D8FFD0  0x82DA78E4  0x82DA8714  0x82DA8BBC
0x830CE790  0x83239C8C  0x8323A564  0x8323AE60
```

The final stable hashes are:

| Artifact | SHA-256 |
| --- | --- |
| entrypoint closure JSON | `7BDD03267CEA981A6112CA670E8BD98266C4C1A675CED5C6FACA0C90431C069C` |
| jump-table recovery JSON | `5CF2648FB089EF48522F0A8AC13DBD9FE707392FC446CD3556206E9A468091FB` |
| exact Ghidra diff JSON | `0172880221B4E3A9BD5C9C0FF5F0914B944123ACB73FF4689347F22BD4AE1C77` |

## Performance attribution

The original comparable observation was `54,684 ms -> 80,591 ms`, a
`25,907 ms` (`47.37%`) increase, while the dedicated recovery pass was only
`145,221 us`. The isolated A/B repetition showed the same direction with
machine-load noise:

| Configuration | Warm-up | Measured 1 | Measured 2 | Measured 3 | Median | Peak range |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A pre-Phase-3 | 54,528 ms | 60,540 ms | 80,933 ms | 54,590 ms | 60,540 ms | 1,065,459,712-1,067,139,072 B |
| B starting Phase 3 | 86,894 ms | 75,851 ms | 107,795 ms | 95,638 ms | 95,638 ms | 1,175,367,680-1,176,809,472 B |

The B median is 35,098 ms slower, but the large run-to-run spread makes the
original 25,907 ms pair the cleaner magnitude. Both sets rule out the 145 ms
dedicated pass as the main cause.

Instrumentation identified repeated exact-block containment work in the
gap-fill/discovery path. With thousands of added blocks, addresses outside an
owner's real body still scanned the full block vector. `FunctionNode` now
caches the exact block envelope, preserves declared CONFIG/PDATA semantics,
rejects addresses outside both declared range and envelope in constant time,
and scans exact fragments only when necessary. Deterministic ordering and
exact membership are unchanged.

The controlled pre/post instrumented result was:

| Measurement | before | after | change |
| --- | ---: | ---: | ---: |
| pipeline | 85.348 s | 67.805 s | -17.543 s |
| gap-fill | 54.944 s | 34.284 s | -20.660 s |

The final `.29` authoritative run took 58,163 ms and peaked at 1,191,489,536
bytes. Its stage evidence is:

| Stage | Time |
| --- | ---: |
| image/XEX loading | 143,652 us |
| identity verification | 161,879 us |
| decode/cache population | 203,140 us |
| register phase | 13,295,205 us |
| scan | 5,310 us |
| discovery | 6,463,567 us |
| gap-fill | 27,105,835 us |
| final ownership/boundary | 15,554 us |
| validate | 88,243 us |
| preliminary CFG | 893,402 us |
| indirect classification | 632 us |
| jump-table dataflow recovery | 373,884 us |
| case CFG expansion | 52,532 us |
| per-function fixpoint | 1,428,689 us |
| fixpoint bookkeeping | 147 us |
| function seed construction | 165,301 us |
| jump-table report construction | 67,444 us |
| closure integration | 10,397,067 us |
| section hashing | 50,566 us |
| JSON/CSV/Markdown/TOML serialization | 7,623,144 us |

Some stages are nested and therefore must not be summed as independent wall
time. The attribution is still clear: legitimate register/gap-fill/closure and
serialization work dominates; recovery itself is below 0.4 s. The demonstrated
avoidable containment scan was removed. Remaining memory growth is consistent
with retaining exact evidence for 6,359 owned cases and 69,016 classified
indirect sites rather than weakening analysis.

## Tests, build, and runtime validation

### Focused and SDK validation

- exact lifecycle fixture: 441 assertions passed;
- stack-lineage fixture: 900 assertions passed;
- focused `[codegen][jump-table]`: 37 test cases, 5,112 assertions passed;
- full SDK Release suite: 1,728/1,728 passed;
- installed CLI: `0.10.0.29-dev.g32deea2`;
- installed CLI SHA-256:
  `5B95B037E3A8E7C37A423CDCE11E3831977423B9BF34FCDD065593463F50917E`.

### Parent static and build validation

The final commands and results were:

```powershell
python -m unittest discover -s .\tests -v
python .\tools\Fable2FunctionMap.py catalog
python .\tools\Verify-Fable2MigrationLedger.py
python .\tools\Verify-Fable2EntrypointClosure.py
python .\tools\Fable2FunctionMap.py validate $map
python .\tools\Fable2FunctionMap.py diff $map `
    --mode exact --closure $closure --output-directory $analysis
fable2-codegen
fable2-build
```

Results:

- Python/schema: 10/10 passed;
- artifact catalogue: nine records passed;
- migration ledger: all 32 entries passed, with 60,729 definitions,
  declarations, mappings, and registrations; `setjmp=0x83006C90`,
  `longjmp=0x82CAFA30`, and real `0x82E8C8E8` semantics retained;
- closure verifier: schema 3, 35,626 candidates, 55 strong, 202 probable, all
  three known-positive fixtures exact;
- exact Ghidra map: 42,462 functions validated;
- exact diff: 52,994 differences, manifest unchanged;
- codegen: 54.988 s, 8 files written, 585 unchanged, zero deleted;
- Release build: 2.535 s, successful link against `.29`.

The final generated/native hashes are:

| Artifact | SHA-256 |
| --- | --- |
| `CMakeLists.txt` | `023F0F61834CBE579F4E0BD2EA9A0811761FFCB146784AD4E1186C42F5E269C8` |
| Release `CMakeCache.txt` | `2EE31454656F380DDBB7BCB6A46F9161D37C25937100BFF58560BEA4461B6991` |
| `fable2_init.cpp` | `96C02EA3D76C91BE0CE22AEC18780FEA834ABC5C24C920032387769AD8F026DA` |
| `fable2_register.cpp` | `D0B209A98118254713E84877829FFF4CF9531532A65BA2499271B29D64B9E01F` |
| `codegen.partition.json` | `3B2EBFFD2F8B85B7599E3064BE70551322CD9181D452439B167010998D2137C6` |
| `codegen.stamp` | `A843ECDB87A5D1ACCB95D42CD0117BA1F48CFCC021D07408D2B7C6F8AAE7D581` |
| final `fable2.exe` | `70BD511B553AD686A4B993B8C2117C6C3987762AF460AE2D38492F68A7E68DBF` |

The known-positive fixtures remain exact functions, not cases:

```text
0x829647F0-0x82964800  size 0x10
0x82C03B28-0x82C03B44  size 0x1C
0x829675E0-0x829675F0  size 0x10
```

### Final matched runtime validation

The one permitted final matrix reused the final binary with no codegen or build:

```powershell
.\tools\Invoke-Fable2BringUpIteration.ps1 `
    -Iteration <1..3> `
    -RunDirectory .\out\phase3-regression-closure-32deea2-final-runtime `
    -BuildPreset win-amd64-release `
    -MonitorSeconds 30 `
    -SkipCodegen -SkipBuild -ManualInput -GracefulStop
```

| Attempt / run | Start / end, local | Classification | Exit | Fatal |
| --- | --- | --- | --- | --- |
| 1 / 024 | `2026-08-30 04:27:28` / `04:27:48` | `InvalidUnregisteredFunction` | `0xC0000409` | `0x82CB6158` |
| 2 / 025 | `2026-08-30 04:27:59` / `04:28:18` | `InvalidUnregisteredFunction` | `0xC0000409` | `0x82CB6158` |
| 3 / 026 | `2026-08-30 04:28:22` / `04:28:42` | `InvalidUnregisteredFunction` | `0xC0000409` | `0x82CB6158` |

All three record `LR=0x82CB6068`, `CTR=0x82CB6158`, no input events, and no
other FWT, assertion, host exception, or suppression-loop match. Result JSON
hashes are, in attempt order:

```text
96C24594615E444DB3D0FA4664049514D56126E3BA47D261C18A741EB2B3947E
7CC70A27D7DE613C9528A14F0F4AAE692F1E8A240589EEB620C3D7EE07ABD79D
13B8C149C61E21BC6C5D45310D829C63FDE508B259F1FFC2D2630F228E28685D
```

No normal progression attempt was run after this deterministic early fatal; it
would exercise the same binary and path. Therefore this work does not claim
current gameplay parity or controllable Bowerstone Old Town.

## Newly exposed `0x82CB6158` blocker

**CONFIRMED static/runtime facts:**

```text
owner                    0x82CB6060 [.pdata: 0x82CB6060-0x82CB69E8)
actual source             0x82CB6154
source opcode             0x4E800420, bcctr/bctr, LK=0
CTR definition            0x82CB614C, mtctr r12
index                     r11, unsigned bound <= 11
table storage             0x820116E0-0x820116EC
element                   unsigned byte
target scale              4
anchor                    0x82CB6158
runtime target            0x82CB6158, the zero-offset case
final failure reason      ambiguous_reaching_definition
final recovered table     none
```

The table dispatch sequence is `lbzx -> rlwinm(scale 4) -> add anchor ->
mtctr -> bctr`. `r11` is a loop-carried parser state: it starts at zero and is
changed by case bodies before branching back to the dispatcher. This explains
why a single reaching definition is ambiguous without making the table itself
invalid.

The coherent A generated output contains exactly:

```text
case 0  -> 0x82CB6158    case 1  -> 0x82CB61CC
case 2  -> 0x82CB624C    case 3  -> 0x82CB62CC
case 4  -> 0x82CB633C    case 5  -> 0x82CB63B0
case 6  -> 0x82CB63D0    case 7  -> 0x82CB6454
case 8  -> 0x82CB6418    case 9  -> 0x82CB64AC
case 10 -> 0x82CB64A0    case 11 -> 0x82CB646C
```

Current generated output instead calls the generic invalid dispatcher at
`0x82CB6154`. The closure has an address-materialization xref for the anchor at
`0x82CB6140/0x82CB6144`, but rejects a candidate function at `0x82CB6158` as
inside the trusted `.pdata` owner. Ghidra defines only `0x82CB6060-0x82CB6068`
at this location and has no exact function at the target. Runtime proves the
case was selected; baseline output proves the old heuristic recognized the
same table. None of this is independent callable evidence.

Final classification: **CONFIRMED remaining Phase 3 regression; unrecovered
loop-carried state-machine switch target**. It is not a manifest function,
landing-pad function, or corruption workaround.

## Files/components and local commits

The Phase 3 closure SDK commits are:

```text
fef16aea07cc279aee0b26903d74173d193e34cc  Fix looped PPC jump-table recovery
46907a0c105eef9d1153be42e3cffb6a79a9e26a  Profile and reduce closure analysis overhead
99aba91c26f3779440436a04703ffa4eb3669e3a  Recover delayed and reentrant PPC switches
7d9c86c441612a1c52732a3a9a0f12f63baff1a6  Preserve delayed guards across VMX128 stores
1295fd87d27c3df31be6a1ed3f4810c3e537eeb7  Recover switches from locally transformed indices
5187e78fbdd977c2e88c846b5eea84763711daf0  Recover bounded merged PPC switch indices
635760f30065d17d18bbd47e435159ab74b7feab  Preserve validated loop tables at analysis limits
589709a203ecf56fd40cd697952c67cf16abe91d  Retain prior tables across precise incomplete merges
29c626383bc3025455b428bbb41ecf70d0f92a2d  Narrow merged-index recovery after TU1 audit
9a088e331f30e1ce195dc03ee57ec6964e3f0e93  Preserve incomplete paths in local index recovery
5ba1ef331cfc3e8e467de380b0ab0f075d401f53  Retry validated switches after CFG limit growth
34b7b43e54be0d7a714f5b4ecdf1a1041c52bbcf  Bound retry for large case-expanded switches
de545749fdf0f420519de3204821368995cff8dd  Isolate state-limited switch retries
44faac6bc2ef79367deda21774776b8b1fd74761  Size switch retry from targeted state evidence
32deea2910986a6898e29c797d61b5c0f9008033  Avoid stack-lineage state explosions in switch recovery
```

The durable SDK components are `jump_table_recovery.cpp` and its public input,
result, retry-evidence types; `FunctionNode` exact-block envelope maintenance;
entrypoint-closure stage/serialization timing; command run metadata; and the
byte-free jump-table/unit fixtures. No temporary diagnostic print remains.

Parent integration commit
`dbbc9e5e263b6a0de867ea6dc69f26acb6d41392` pins the exact final SDK. This
document and the cross-reference in `03-jump-table-recovery.md` are the only
other tracked parent changes.

## Invariants, limitations, and exact next action

- `fable2_manifest.toml` is unchanged; no `RETURN_R3_ZERO` entry exists.
- No case target is registered as a function without independent callable
  evidence.
- All unresolved non-link CTR sites retain explicit reasons.
- No target was accepted from a partial or mixed-validity table.
- TU1 patching, `setjmp`/`longjmp`, the fault walker, and the three known
  callable fixtures pass their static gates.
- Xenia was not rerun. The coherent ReXGlue baseline is sufficient to prove the
  Phase 3 codegen difference, but equivalent Xenia source-PC capture remains
  optional corroboration.
- Person-controlled gameplay was not attempted after the deterministic final
  fatal.

The exact next action is a focused, byte-free state-machine fixture for
`0x82CB6154`: prove that the unsigned bound dominates every path into the
dispatch while the index has a finite loop-carried set of case-state
assignments, recover the complete 12-entry byte table generically, and reject
an otherwise identical fixture with an out-of-range or unknown state. Run only
the focused jump-table tests while developing it. Do not change the manifest,
register `0x82CB6158`, weaken target validation, or start another full TU1,
install, codegen, build, or smoke cycle until that focused lifecycle passes and
the remaining `ambiguous_reaching_definition` cluster has been re-audited.

No push, merge, tag, pull request, release, asset upload, private executable
upload, or raw memory upload occurred.
