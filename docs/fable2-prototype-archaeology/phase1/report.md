# Prototype Archaeology Phase 1 report

## Executive summary

Phase 1 establishes that the corpus is useful for TU1 archaeology and justifies a bounded Phase 2
matcher.

- **Confirmed:** no standalone `.pdb`, `.map`, `.xdb` or `.xexp` file is present in the original
  1,184-file corpus. The patch package contains `default.xexp`, but only inside its STFS container.
- **Confirmed:** all three full prototype XEXs retain an `RSDS` CodeView record, exact PDB path,
  GUID and age. They also retain source paths, RTTI/type names, assertion/compiler residue and
  subsystem terminology. This is useful symbol/debug evidence even though the PDB files themselves
  are absent.
- **Confirmed:** the debug menus and Lua 5.1 bytecode expose thousands of names and constants,
  including renderer, AI, physics, entity, quest/gameflow, profiling and debug interfaces. Numerous
  terminal command components also occur in decrypted XEX data.
- **Confirmed:** the July 2009 and `23.12.02.0330` XEX containers are different, but every
  initialized decrypted PE section is byte-identical. Their shared internal image is therefore the
  same executable build.
- **Strongly supported:** `23.12.02.0330` is a development build in the retail-TU1 development
  lineage. It is not binary-equivalent to canonical retail TU1 and its update payloads are not the
  retail payloads.
- **Strongly supported:** cross-build function matching is practical. Unique branch-normalized PPC
  fingerprints produce 16,523 candidates between the July image and canonical TU1, while exact
  address identity succeeds for only two functions. Phase 2 must be relocation-aware and validate
  candidates with topology, CFG and semantic references.

No names have been propagated into TU1 and no manifest entries have been changed.

## Scope and evidence grades

The analysis was static and offline. Original files were opened for inventory, hashing and reading;
all extracted or decrypted material was written below the ignored
`out/prototype-archaeology` directory.

This report uses the following grades:

- **Confirmed:** directly demonstrated by file bytes, hashes, parsed metadata or deterministic tool
  output.
- **Strongly supported:** multiple independent confirmed observations support the finding, but
  exact build ancestry or semantics are not directly proved.
- **Probable:** the balance of evidence supports the interpretation.
- **Possible:** plausible and worth testing later.
- **Speculative:** insufficient evidence for operational use.

## Immutable corpus inventory

The final inventory contains 1,184 files and 17,314,927,472 bytes:

| Build ID | Source directory | Files | Bytes |
| --- | --- | ---: | ---: |
| `sep-2008` | `Fable II (Sep 13, 2008 prototype)` | 419 | 7,041,501,697 |
| `jul-2009` | `Fable II (Jul 10, 2009 prototype)` | 352 | 3,196,842,380 |
| `build-23.12.02.0330` | `Fable II July 10 2009 23.12.02.0330` | 412 | 7,068,784,611 |
| `patch-data` | `Fable II (Patch Data prototype)` | 1 | 7,798,784 |

Every record includes build identity, source-root-relative and build-relative paths, filename,
extension, size, SHA-256, SHA-1, timestamps, bounded magic/signature classification and content
classification. Classification gives detected magic precedence over filename extension. Absolute
paths are retained only as contextual source-root metadata; relative identities and hashes are the
portable keys.

## Prototype matrix

| Build | Embedded identity | `default.xex` identity | Debug and script evidence | TU/update evidence | Archaeological value |
| --- | --- | --- | --- | --- | --- |
| September 2008 | `build_version.txt`: `23.09.13.0304`; PE time `0x48CC2207` / `2008-09-13T20:26:47Z`; `ServerInfo.txt` references the February 2008 XNA Live test lab | 20,758,528 bytes; SHA-256 `9997088F23FEFA2C700F18DA2CCB614AAE221C6F39B3BE9BA7AAAA059DB6BFAF`; entry `0x82C7F020` | Release-branch PDB identity, source paths, debug menus, 18 `scripts` plus 18 `scripts_r`; 13 pairs differ | None established | High: older independent build useful for matcher robustness and branch-history semantics |
| July 2009 | `DailyBuild 0400.07-07-2009.2145`; PE time `0x4A571818` / `2009-07-10T10:29:44Z` | 21,282,816 bytes; SHA-256 `0AAA3C8EF72ECBB607C9D8A50C42022F3E0BDE759A462CB14148621790C0E348`; entry `0x82CC21F0` | EpisodicBranch_v2 PDB identity, source paths, 19 `scripts` plus 19 `scripts_r`; 15 pairs differ; `lhdebug.log` is empty | No loose TU manifest/bank | Very high: internal executable is identical to build 23 and structurally close to TU1 |
| `23.12.02.0330` | `build_version.txt`: `23.12.02.0330`; same PE time and CodeView identity as July | 21,282,816 bytes; SHA-256 `0686A9F292A3F6777BEB6E8D4924F96247D1E8E3E2370323572F797E6637A4AA`; entry `0x82CC21F0` | Same internal PE/debug residue as July; 18 `scripts` plus 18 `scripts_r`; 13 pairs differ | Loose `tu1_data.manifest` and `data/tu1_data.bnk` | Highest: named development-TU package identity plus direct canonical-TU1 comparison |
| Patch Data | Single LIVE/STFS file `4D5307F1`, 7,798,784 bytes, SHA-256 `9C38172140A61D0A1013AF1639E404B1AFCCC0B26A98748F417BA2C29BAD7187` | No full XEX; package contains `default.xexp` | No script/debug tree | Package build `23.12.02.0330`, beta update metadata, `default.xexp`, manifest and bank | High for update provenance; not a substitute for retail TU1 |

The three full XEX source hashes are all different. The July and build-23 containers differ in
execution/container fields (`5.0.0.0`, media `0x00000000` versus `0.0.4.1`, media `0x6473199D`),
but their derived initialized PE sections and CodeView record are byte-identical. September is a
different executable generation.

## XEX and build metadata

All three prototype images have image base `0x82000000`, title ID `0x4D5307F1`, basic compression
and devkit encryption. The extracted `.text` identities are:

| Build | `.text` start | Size | SHA-256 |
| --- | --- | ---: | --- |
| September | `0x82170000` | 17,858,716 | `B13E857C468951B8D22F6D042AF04DE41BB4CC7CD315D3476E1418E7F9D68E75` |
| July / build 23 | `0x82170000` | 18,132,124 | `A4921375A74DC0E7178313910739410901E780810478077743B15850357401656` |
| Canonical TU1 | `0x82170000` | 18,131,900 | `1B9F2E80280637FE2287286ED3FE18B367F378E24A695A2B8AB50B9ACD8FC724` |

The prototype original PE name is `Fable2_xfr.exe`. Static-library metadata consistently names
XDK `2.0.7645.0` libraries (`LIBCMT`, `XAPILIB`, `XAUD`, `XMP`, `X3DAUD`, `XBOXKRNL`, `XONLINE`,
`XHV`, `D3DX9`, `XRNMS`, `XGRAPHC`) and `D3D9LTCG` `2.0.7645.1`.

## Embedded symbol and debug archaeology

### CodeView and source paths

**Confirmed:** the September image has an `RSDS` record at guest address `0x820FB148`:

```text
GUID: 1C2C3336-05E2-4642-AA2A-B68E87440795
age: 1
PDB: D:\dev\Fable2\ReleaseBranch\Deploy\Fable2_xbox360\Fable2_xfr.pdb
```

**Confirmed:** the July and build-23 images have the same `RSDS` record at guest address
`0x82101A38`:

```text
GUID: CB843FAD-A745-40DD-AB88-1E3B58FD0ED2
age: 2
PDB: E:\dev\Fable2\EpisodicBranch_v2\Deploy\Fable2_xbox360\Fable2_xfr.pdb
```

The July/build-23 `.rdata` also contains, at `0x8200B5F8`, the exact source path:

```text
E:\dev\Fable2\EpisodicBranch_v2\SourceCode\ctg\lhcomponents\lhaudio\Plugins\SourcePrograms\Splitter\CSplitter.cpp
```

The corresponding September path at `0x8200B560` names `ReleaseBranch`. The curated evidence also
retains Havok source filenames, class/type strings, assertions, compiler-runtime strings and terms
for audio, renderer, shader, physics, AI, animation, memory, resource and task/job systems. These
are semantic anchors, not proven TU1 function names.

### Debug menus, console scripts and Lua

The `.lua` files begin with Lua 5.1 bytecode (`1B 4C 75 61 51`) rather than plaintext source. The
analysis conservatively harvests constants and identifiers from the bytecode without pretending to
decompile Lua control flow. Plain-text debug menus provide exact line-oriented command expressions.

Representative confirmed script-to-XEX anchors from build 23 are:

| Script expression/name | Source | XEX terminal string address | Interpretation |
| --- | --- | --- | --- |
| `Debug.SetUseFreeCamera` | `data/scripts/Startup/DebugMenu.txt:3` | `SetUseFreeCamera` at `0x820BA1FC` | Strongly supported semantic anchor |
| `Debug.SetDrawBehaviourNames` | `data/scripts/Startup/DebugMenu.txt:5` | `SetDrawBehaviourNames` at `0x820B7278` | Strongly supported semantic anchor |
| `Debug.SetDrawGameFPS` | debug menu | `SetDrawGameFPS` at `0x820AAD8C` | Strongly supported semantic anchor |
| `PhysicsControlled.SetMaxSlopeDegrees` | startup material | `SetMaxSlopeDegrees` at `0x820E7D3C` | Strongly supported semantic anchor |
| `Stats.SetHeroAbilityLevel` | startup material | `SetHeroAbilityLevel` at `0x820BE240` | Strongly supported semantic anchor |

Other high-value constants expose `EngineConfig` controls including `EnablePRT`, `Lightmaps`,
`ToneMapping`, `Shadows` and `UseWhiteTexture`, plus AI material in `luaplus_ai_test.lua`.

`scripts` and `scripts_r` are demonstrably not simple duplicate trees: 13 of 18 pairs differ in
September and build 23, and 15 of 19 differ in July. **Possible:** `_r` denotes a release-oriented
transformation or configuration. Phase 1 does not establish that expansion, so it remains unnamed
in machine-readable conclusions.

The bounded static association pass found data pointers for only six harvested records, all for the
generic name `Load`, and found zero nearby executable-pointer candidates. **Confirmed:** Phase 1
does not associate a command-registration string with a callback pointer. The absence of a simple
table signature is negative evidence, not evidence that the commands are purely scripted.

## Log provenance

- **Confirmed:** `Fable II (Jul 10, 2009 prototype)/lhdebug.log` is zero bytes, SHA-256
  `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`. It contains no runtime
  engine evidence.
- **Confirmed/strongly supported:** `Fable_II_R_logs` is preservation/extraction metadata, not a
  contemporary Lionhead runtime log. The exact command in
  `Fable_II_R_20210401T101950.txt:1` invokes `DiscImageCreator.exe`; `Fable_II_R.dat` records the ISO
  size and hashes. `Fable_II_R_mainError.txt` is empty.
- **Confirmed:** `!submissionInfo.txt` is later disc-preservation metadata. Its `Review` label is
  useful provenance for the physical image, but it is not embedded build-system evidence.

## `23.12.02.0330` and canonical TU1

The relationship is strong but not equivalence.

### Confirmed links

The Patch Data STFS package extracts to five files. Its exact build identity is `23.12.02.0330`, and
its `tu1_data.manifest` is byte-identical to the loose build-23 manifest:

```text
tu1_data.manifest
size: 27751
SHA-256: 40900170279BE16B4B5958957A2BC596E6C4942446DC9BE06EF51E646F7C0E4A
mappings: 162
internal prefix: fable2_title_update\fable2_live\deltas\
```

`4D5307F1.ini` records `XLAST.EXE` `2.0.7978.3`, content type `0x000B0000`, title
`0x4D5307F1`, base version `0x00000001`, update version `0x00000301` and `BetaUpdate=1`. The package
`default.xexp` has:

```text
size: 7337984
SHA-256: 47156DAEA44999B5AB7F964B71442F98186D932BB946C73057799D51B43CA821
source version: 0.0.0.1
target version: 0.0.3.1
source digest: BEC82E452CBA84EE282E4AF91774AAF3A8CB961E
```

That source digest matches neither the header nor section digest of the three prototype XEXs or the
canonical retail base XEX. Applying it to the build-23 or canonical base with the available Ghidra
loader failed at import. This is a confirmed observation for those exact attempted inputs, not a
claim that the package is universally unusable.

### Confirmed differences

The update banks are three distinct files:

| Source | Size | SHA-256 |
| --- | ---: | --- |
| Loose build 23 | 441,667 | `8C50A9C550ECD3C03A1B776FB0F3395AD777E7BDFD82B959F60E8A08139753FA` |
| Patch Data package | 307,180 | `636BCA63EE5C0B02C906AAC1E3762555C1BD30DECB6A0CDF1E2B762E4AAAC020` |
| Canonical retail TU1 | 94,535 | `C7D7F14C45096EA7760E07839DA51EBDBCC5F77672A6CFFEF560BDBBB0EA3310` |

The canonical post-patch image identity remains authoritative:

```text
base XEX SHA-256: 88C4EF2E18E65409444D1B068EFF921D1F7E180A5AE64EDC64BA6B0872372662
retail XEXP SHA-256: 046A05693B4DA4437083C784000A850858B3BF992955C7DB30D518FB3E53E41C
post-patch SHA-256: BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00
entry point: 0x82CC21C0
version: 0.0.1.26
media ID: 0x716F0A0D
PE timestamp: 0x4A53C85A / 2009-07-07T22:12:42Z
```

The July/build-23 development PE timestamp `0x4A571818` is later than the canonical retail-TU1
timestamp. The development `.text` is 224 bytes larger and has a different hash. Major section
addresses remain close, but only about 10.75% of same-address code bytes match; `.data` is about
99.02% equal at corresponding addresses.

### Relationship conclusion

- **Confirmed:** build 23 is a development build packaged with development TU data.
- **Confirmed:** its XEXP and `tu1_data.bnk` are not the canonical retail TU1 files.
- **Strongly supported:** its internal executable belongs to the retail-TU1 development lineage and
  is close enough to be the primary Phase 2 donor build.
- **Probable:** the shared July/build-23 PE represents a nearby post-branch build around the retail
  TU1 integration period.
- **Speculative:** its exact source-control parent/child relationship to retail TU1. Timestamp order
  alone does not prove ancestry.

## Cross-build matching feasibility

The feasibility pass uses exact `.pdata` function boundaries and three fingerprints: exact bytes,
PPC bytes with `b`/`bl`/`bc` displacement fields normalized, and opcode/XO structure. It measures
candidate counts and representative functions; it does not publish a TU1 name map.

| Comparison | Functions | Shared starts | Same-address exact | Unique exact fingerprints | Unique branch-normalized | Unique opcode structure |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| September -> July | 45,707 -> 46,179 | 1,035 | 0 | 1,991 | 12,176 | 24,080 |
| July -> canonical TU1 | 46,179 -> 46,180 | 2,900 | 2 | 2,971 | 16,523 | 27,578 |
| Build 23 -> canonical TU1 | 46,179 -> 46,180 | 2,900 | 2 | 2,971 | 16,523 | 27,578 |

Representative results include a relocated exact 100-byte function at development `0x82854508`
and TU1 `0x82853250`, and a normalized 80-byte call-bearing function at development `0x82542BC8`
and TU1 `0x82541598`. Tiny leaves, large functions, indirect-branch functions, changed functions and
same-address divergences are retained in the JSON.

**Recommendation:** Phase 2 is justified. Use exact `.pdata` boundaries, unique exact or
branch-normalized candidates, local address-delta neighbourhoods, direct-call topology, referenced
strings/constants/globals and final CFG/instruction review. Treat opcode-only matches as candidate
generation, not acceptance. Never trust function size, same guest address, a generic string or a
prototype semantic name alone.

## Rendering and proprietary-resource triage

Both shader banks are identical across all three full builds:

| File | Size | SHA-256 |
| --- | ---: | --- |
| `Shaders.sbk` | 731,123 | `60D1E468C909C1403758F54EE1DF50DE500C28604ADE01ACF174A79106621FA7` |
| `ShadersRelease.sbk` | 653,060 | `C2732102A0AEDB8C7A950E5781FA15092A3C12C2721380944C4E717DADE5E736` |

The two variants are different from each other and both begin with `ShaderBankFile`. The fuller bank
contains 3,856 readable-name candidates versus 2,496 in the release bank. Examples include
`m_BetaRayleigh`, `m_BetaMie`, `ScreenSpaceShadowMask`, `SpotLightShadowMask` and
`m_FresnelBias`. This is confirmed inventory evidence for future renderer research, not a renderer
implementation finding.

The resource triage covers 613 proprietary-format files and 222 cross-build equivalent-path
comparisons, with bounded readable-string extraction. `.gdb`, `.list`, `.adb`, `.bnk`, `.sbk`,
`.animation_toc` and `.animation_data` remain opaque containers except for obvious signatures and
strings. `enginetestresources.gdb` and `e3physicsmeshes.txt` are small, identical across applicable
builds and semantically promising. Dedicated container reverse engineering is deferred.

## Negative findings and limits

- No standalone PDB, MAP, XDB or source XEXP file was found in the original corpus.
- No `NB10` CodeView record was found; the useful records are `RSDS`.
- `lhdebug.log` contains no lines, addresses, asserts or subsystem startup order.
- The September `Fable_II_R_logs` contain no Lionhead runtime trace.
- The available names do not establish native callback addresses or TU1 function identity.
- `_r` is not expanded to “release” because the corpus only proves that the trees differ.
- The development Patch Data XEXP was not successfully applied to an identified matching base.
- No claim is made that RTTI/source-path coverage is complete; the output deliberately curates
  high-value strings rather than committing an unbounded `strings` dump.
- No prototype was executed and no gameplay/debug menu was operated.

## Phase 2 inputs and procedure

Phase 2 should consume these exact inputs:

1. `prototype-xex-metadata.json` and the hash-linked ignored `.text`, `.pdata`, `.rdata` exports for
   `jul-2009`/`build-23.12.02.0330` and `sep-2008`.
2. The canonical TU1 `.pdata`/`.text` export and
   `out/analysis/BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00/entrypoint-closure.json`.
3. `prototype-crossbuild-feasibility.json` as the fingerprint method and benchmark, not as a final
   correspondence map.
4. `prototype-debug-strings.json`, `prototype-script-symbols.json` and
   `prototype-debug-interfaces.json` as semantic evidence after code correspondence is established.
5. The exact CodeView identities as provenance and, if a lawful symbol source is later available,
   lookup keys: `1C2C3336-05E2-4642-AA2A-B68E87440795` age 1 and
   `CB843FAD-A745-40DD-AB88-1E3B58FD0ED2` age 2.

The implementation should extend the repository's existing function-map/discovery schemas. Start
with July/build-23 to canonical TU1; use September as an independent confidence/cross-era test.
Produce candidate mappings with per-feature evidence and ambiguity sets. Accept exact unique matches
first, then branch-normalized matches corroborated by neighbourhood/call topology, then CFG-assisted
matches. Quarantine tiny duplicate leaves, generic API strings and opcode-only matches. Require
manual review before any TU1 semantic rename, manifest change or symbol propagation.

Phase 2 should not infer a name from a PDB path, copy addresses between builds, or treat build number
coincidence as executable identity. Canonical TU1 bytes, boundaries and runtime evidence remain
authoritative whenever prototype evidence conflicts.

## Reproducibility and evidence locations

The exact commands and tool prerequisites are in the [prototype archaeology README](../README.md).
Machine-readable details are under [`evidence/`](evidence/). The analysis generator is deterministic
for unchanged inputs and an explicit generation timestamp; `verify` rehashes the 1,184-file source
corpus and validates required artifacts. Derived binary material is linked to source hashes but is
kept out of Git.
