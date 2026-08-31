# Ghidra/XEXLoader function-map acquisition, import, and diff

## Status and scope

This is the durable checkpoint for the report-only Ghidra stage of the Fable II
function-discovery pipeline. It targets the exact Fable II Game of the Year
Edition TU1 image established by the preceding static-entrypoint-closure stage.
Ghidra is evidence, not authority: this workflow never overwrites the manifest,
`.pdata`, ReXGlue analysis, or manual/fault-walker evidence.

The implementation deliberately excludes jump-table recovery, Xenia tracing,
and runtime bulk import. Projects, databases, private executable bytes and
generated reports remain outside the source tree or ignored under `out/`.

Jump-table recovery was subsequently implemented in
[`03-jump-table-recovery.md`](03-jump-table-recovery.md). The importer now
accepts shared contract/closure schemas 1-3 and consumes schema-3 exact case
ownership: a Ghidra entry that is only a recovered case, without independent
callable evidence, is quarantined as `ghidra_false_positive_suspected`. The
schema-2 counts below remain the reproducible Ghidra-stage baseline.

Durable implementation commits:

- ReXGlue SDK `fe1ae38`: versioned executable-memory identity and
  entrypoint-closure schema 2.
- Fable2Recomp `2bdba963`: exporter, headless wrapper, XEXLoader compatibility
  installer, schema-2 evidence contract, and SDK pin.
- Fable2Recomp `7816886a`: strict importer, identity states, artifact catalogue,
  deterministic diff and review reports.
- The commit containing this document adds standalone `.pdata` preservation,
  tests, final real-map validation, and this handoff.

## Exact target identity

| Evidence | Exact value |
|---|---|
| Base XEX SHA-256 | `88C4EF2E18E65409444D1B068EFF921D1F7E180A5AE64EDC64BA6B0872372662` |
| XEXP SHA-256 | `046A05693B4DA4437083C784000A850858B3BF992955C7DB30D518FB3E53E41C` |
| Loaded post-patch image SHA-256 | `BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00` |
| Executable-memory fingerprint | `5C8B78B84C93028D166E3DF347206E6642BA40BF374AD1AF8D958B2211320357` |
| Image base / size / entry | `0x82000000` / `0x01620000` / `0x82CC21C0` |
| Title / media / version | `0x4D5307F1` / `0x716F0A0D` / `0.0.1.26` |
| PE timestamp | `0x4A53C85A` |
| `.text` | `[0x82170000,0x832BABBC)`, `0x0114ABBC`, SHA-256 `1B9F2E80280637FE2287286ED3FE18B367F378E24A695A2B8AB50B9ACD8FC724` |
| `BINK` | `[0x832BAC00,0x832CA03C)`, `0x0000F43C`, SHA-256 `D715B7B4F3E7912489DBBBA3FF2642B1907479CBEDBDF974CD043827DB707146` |

The versioned, byte-free contract is
`tools/fable2-entrypoint-closure-evidence.json`.

## Public-artifact acquisition

Research was performed on `2026-08-29` before designing the local-project
fallback. GitHub repositories, releases, issues/attachments, all nine public
`Fable2Recomp/Fable2Recomp` forks, modding projects, Xenia patch repositories,
general web results and archive-oriented searches were inspected. Exact-address
queries included `0x829647F0`, `0x82C03B28`, and `0x829675E0`.

No public Fable II Ghidra `.gpr/.rep`, `.gzf`, project archive, function-map
JSON or symbol map was located. This is a search result, not proof that none
exists. `tools/fable2-ghidra-artifacts.json` is the authoritative catalogue of
queries, repositories, URLs, versions, identities, licences, sizes and hashes.

Useful or plausible public files were downloaded outside the repository:

| Artifact | Commit/release | SHA-256 | Identity/use | Licence |
|---|---|---|---|---|
| [Historical Fable2Recomp config](https://github.com/Fable2Recomp/Fable2Recomp/blob/1e25911172f8e30458099eda96a1ad7b8992ed60/Fable2_config.toml), 50,412 bytes | `1e25911172f8e30458099eda96a1ad7b8992ed60` | `EC64D0D49150FFC1584B4E7EA634F554FA6720A005180F7BE9E261F93B96F277` | `identity_incomplete`; comparative only | MIT |
| [XenonRecomp issue 77 config](https://github.com/hedge-dev/XenonRecomp/issues/77), 4,486 bytes | attachment `19214777` | `F36D012953E14119CADC1CAC80EFD1A26A127C59C0316C62038A0B3B90F5B780` | `identity_incomplete`; comparative only | no explicit attachment licence |
| [Xenia GOTY TU1 patch](https://github.com/xenia-canary/game-patches/blob/5c3b70e92c1c050dafd9e35a6c57e1edf4fb1a47/patches/4D5307F1%20-%20Fable%20II%20(GOTY_Platinum%20Edition%2C%20TU1).patch.toml), 768 bytes | `5c3b70e92c1c050dafd9e35a6c57e1edf4fb1a47` | `91C7AAAC4D792E9AE24BE3F752A662B92C517BF183A6314FE6405DBE6F1B8ECA` | `probable_same_build`; title `0x4D5307F1`, media `0x716F0A0D`, module `0xEE56F849188A6A20`; not a map | no explicit repository licence |
| Xenia GOTY non-TU1 patch, 2,690 bytes | same | `BB34B928C4A1E9437AF3944BE6CDA571EC8048C4661019E15D91382AECF18EC9` | related build | no explicit repository licence |
| Xenia Fable II `(1)`, 1,506 bytes | same | `F1A537C47DD2D8F14B448873C09D874A89BACA07C93E325C5ABCB8832706517B` | related build | no explicit repository licence |
| Xenia Fable II `(2)`, 889 bytes | same | `91874297DBEDD1FF1D6750A0838B8C923B0063B9F20C172738AD24BC96671D1D` | related build | no explicit repository licence |

`JustSomeGuy1234/Fable2Modding@911f014f` and
`JustSomeGuy1234/xenia-fable2-patches@29729a7f` contained no function map and
had no explicit licence. No related artifact was relabelled as TU1.

Repeat the hash-pinned catalogue workflow with:

```powershell
python .\tools\Fable2FunctionMap.py catalog
python .\tools\Fable2FunctionMap.py catalog `
    --download-directory C:\Dev\Fable2GhidraTools\downloads
```

Stable evidence excludes acquisition timestamps and local download paths.

## Supported toolchain and loader repair

| Tool | Public ZIP SHA-256 | Version/provenance | Licence |
|---|---|---|---|
| [Ghidra](https://github.com/NationalSecurityAgency/ghidra/releases/tag/Ghidra_12.1.2_build), `ghidra_12.1.2_PUBLIC_20260605.zip`, 572,803,866 bytes | `B62E81A0390618466C019C60D8C2F796CED2509C4C1AEA4A37644A77272CF99D` | 12.1.2, revision `c0f584bf229fffba61b36431f3ce30c0c3e4e682` | Apache-2.0 |
| [XEXLoaderWV](https://github.com/zeroKilo/XEXLoaderWV/releases/tag/12.1.2), `ghidra_12.1.2_PUBLIC_20260802_XEXLoaderWV.zip`, 248,763 bytes | `3030B51D585998D3BA7A7E28CFF9C0D589C7E6E0B5D545D8647E7FAD975A79DC` | tag 12.1.2, commit `d0af801aee083c86950b90c3db78b2e1c642067f`, extension property `13.0.0` | no explicit repository/release licence; do not redistribute patch |
| [Temurin JDK](https://github.com/adoptium/temurin21-binaries/releases/tag/jdk-21.0.11%2B10), 205,073,954 bytes | `D3625E7CADF23787EA540229544B6E2AB494B3B54DA1801879E583E1DFEE0A64` | 21.0.11+10 | GPL-2.0 with Classpath Exception |

Ghidra is not vendored. Keep installations and databases outside the repo.

The pinned XEXLoader needs a local compatibility build because its `Path to
xexp` option has no headless command name and its `compressed_len == 1` XEXP
copy loop corrupts overlapping TU1 copies. The installer exposes
`-loader-xexp` and substitutes overlap-safe `System.arraycopy`.

```powershell
.\tools\Install-Fable2XEXLoaderHeadlessPatch.ps1 `
    -GhidraRoot C:\Dev\Fable2GhidraTools\install\ghidra_12.1.2_PUBLIC `
    -JavaHome C:\Dev\Fable2GhidraTools\install\jdk-21.0.11+10

.\tools\Install-Fable2XEXLoaderHeadlessPatch.ps1 `
    -GhidraRoot C:\Dev\Fable2GhidraTools\install\ghidra_12.1.2_PUBLIC `
    -JavaHome C:\Dev\Fable2GhidraTools\install\jdk-21.0.11+10 `
    -CheckOnly
```

Validation constants are public source ZIP
`AB33C3C364357E1C1DCBDF7B3120CCA345EB00F6D16675BE099B293FAD9A5FF9`,
upstream class
`DA1D311FAF3D45595190C1AA7BEBD1B9EFB5C9D1240BA1C7814AA725DA26B367`,
and patched class
`C0ACB6B1A4F8DF7638A96E8CDF97CC47C7B30447D43E725028F087FE5FAE124C`.
The patched JAR hash is not a contract because `jar --update` changes ZIP
metadata; one observed rebuild was
`6DE000F8D8DC2165BABC7F6BCEDDFA821281F7B08EF245BBD36B77C8A10D8011`.
The installer makes an upstream backup, reads no game bytes, and rejects
unknown public source/classes. No patched binary is committed.

## Export commands

Create and fully analyse the exact local project:

```powershell
.\tools\Invoke-Fable2GhidraExport.ps1 `
    -ProjectDirectory C:\Dev\Fable2GhidraResearch\full-analysis-project `
    -ProjectName fable2-tu1-ghidra-12.1.2
```

Export an already analysed project without rerunning analysis:

```powershell
.\tools\Invoke-Fable2GhidraExport.ps1 `
    -ProjectDirectory C:\Dev\Fable2GhidraResearch\full-analysis-project `
    -ProjectName fable2-tu1-ghidra-12.1.2 `
    -ProgramPath default.xex -NoAnalysis -ImageBase 0x82000000 `
    -BaseXexSha256 88C4EF2E18E65409444D1B068EFF921D1F7E180A5AE64EDC64BA6B0872372662 `
    -TitleUpdateSha256 046A05693B4DA4437083C784000A850858B3BF992955C7DB30D518FB3E53E41C `
    -PatchedImageSha256 BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00
```

The wrapper also restores `.zip` archives containing exactly one `.gpr/.rep`
pair (with `-ProgramPath`) and imports `.gzf`. Existing databases are not
overwritten. Restore GUI-only `.gar` archives manually. Preserve an original
archive before Ghidra migration and re-export afterward. `-AllowVersionMismatch`
is only for explicit migration tests; `-AllowRelatedBuild` creates quarantined
comparative evidence, never an exact identity.

The wrapper validates paths, Ghidra/JDK/loader versions and class hash, raw
input hashes, language and manifest non-mutation. `ghidra-export-run.json`
contains volatile timing/local paths separately from the stable map.

## Schema and fingerprint

`tools/ghidra/ExportFable2FunctionMap.java` emits
`fable2-ghidra-function-map` schema 1, exporter 1.1.0. It records:

- exporter/toolchain/project/source identity and hashes;
- image base and provenance, language/processor/compiler spec;
- exact block ranges, permissions, load/init/overlay status and hashes;
- the versioned executable fingerprint;
- all standalone `.pdata` entries and record addresses;
- each function entry, exact ordered body fragments, body-membership size,
  min/max extent and contiguity;
- primary name, aliases and source types; external/import/entry/no-return,
  calling convention and signature provenance;
- thunk direct/terminal targets, `.pdata` associations, inbound code/data
  xrefs, callable internal labels, multiple entries and exact overlaps.

Extent is never treated as size for a fragmented function. Names never define
boundaries. Exporter 1.0.0 maps lacking root `pdata_functions` are read through
a controlled compatibility fallback using per-function associations; exporter
1.1.0 preserves `.pdata` entries merged or deleted by analysis. Unknown schema
versions fail closed.

The common fingerprint algorithm is
`fable2-executable-memory-sha256-v1`:

1. select non-empty executable sections (Ghidra: initialized, loaded,
   non-overlay);
2. sort by unsigned start, reject overlaps, merge adjacency only for identical
   R/W/X bits, and never synthesize gap bytes;
3. hash ASCII `FABLE2_EXECUTABLE_MEMORY_V1` plus NUL, BE32 span count, then for
   each span BE64 start, BE64 size, one permission byte (`R=1,W=2,X=4`) and all
   bytes in address order.

Padding inside executable sections and TU1 patches are included. ReXGlue and
Ghidra reproduce the exact fingerprint above.

## Import, identity and diff

Routine operations require only Python after export:

```powershell
$map = '.\out\analysis\BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00\ghidra-function-map.json'
python .\tools\Fable2FunctionMap.py validate $map
python .\tools\Fable2FunctionMap.py import-map $map
python .\tools\Fable2FunctionMap.py diff $map `
    --run-metadata C:\Dev\Fable2GhidraResearch\function-map-diff-run.json
```

Import uses `fable2-shared-function-evidence` version 2 and attaches every item
to its source artifact and identity state:

| State | Meaning/use |
|---|---|
| `exact_image_match` | All source/update/patched hashes and executable fingerprint match; exact mode allowed. |
| `matching_executable_memory` | Fingerprint matches while container evidence is absent/different; exact code comparison allowed with provenance retained. |
| `probable_same_build` | Exact executable layouts/section hashes match, but the canonical fingerprint is incomplete; review only. |
| `related_build_or_title_update` | Fable II is indicated but explicit build evidence differs; comparative mode only. |
| `identity_incomplete` | Insufficient evidence; comparative mode only. |
| `confirmed_mismatch` | Strong claims conflict or explicit evidence is incompatible; no TU1 conclusion. |

Exact mode accepts only the first two. `--mode comparative` is required for
the other four and quarantines every conclusion.

Stable output convention:

```text
out/analysis/BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00/
  ghidra-function-map.json
  function-map-diff.json
  function-map-diff.csv
  function-map-diff.md
  function-map-diff-review.toml
```

The JSON retains exact fragments/ranges, names/source types, source identity,
`.pdata`, ReXGlue/static closure, manifest/manual/fault-walker provenance,
xrefs, conflicts, surrounding trusted boundaries, recommendations and the
automatic-safety decision. CSV/Markdown are review views. TOML is explicitly
non-authoritative and is never applied.

Classifications are `exact_match`, `name_only_difference`, `size_mismatch`,
`ghidra_missing_from_manifest`, `manifest_missing_from_ghidra`,
`ghidra_thunk_missing`, `callable_internal_entry`, `range_overlap`,
`ghidra_false_positive_suspected`, `manifest_manual_only`,
`conflicting_boundaries`, `related_build_candidate`, `unresolved_identity`,
`pdata_missing_from_ghidra`, and `ghidra_missing_from_pdata`.

An automatic action is considered safe only for exact/strong identity in exact
mode, a contiguous non-overlapping non-thunk body with `.pdata`, no current
manifest or ReXGlue range, and no conflict. It still produces only a review
fragment. The real report has zero eligible entries.

## Real and synthetic validation

A fresh private project was created outside the repository. This is a locally
generated exact map, not a public artifact.

- XEXLoader initially defined `46,180` `.pdata` functions.
- Full analysis succeeded in `348` analyzer seconds; wrapper
  import/analysis/export elapsed `399.4 s`.
- The analysed map contains `42,462` Ghidra functions and `46,180` standalone
  `.pdata` entries. It was `96,710,692` bytes before the final
  exporter-version-only refresh.
- Identity is `exact_image_match` with fingerprint
  `5C8B78B84C93028D166E3DF347206E6642BA40BF374AD1AF8D958B2211320357`.
- Validation took `0.711 s`, peak working set `370,143,232` bytes.
- Existing-project export took `8.5–9.3 s`. The raw no-analysis `.pdata`
  baseline took about `49.7 s` and contained `46,180` functions.
- Diff against `80` manifest overrides, `60,653` ReXGlue ranges, `46,180`
  `.pdata` entries and schema-2 closure took `11.349 s`, peak
  `1,543,155,712` bytes. JSON was about `344 MB`; CSV about `25.6 MB`.

Initial exact-diff classification counts were:

| Classification | Count |
|---|---:|
| `exact_match` | 17,372 |
| `size_mismatch` | 23,834 |
| `conflicting_boundaries` | 1,123 |
| `ghidra_missing_from_manifest` | 42,462 |
| `manifest_missing_from_ghidra` | 80 |
| `manifest_manual_only` | 3 |
| `ghidra_thunk_missing` | 75 |
| `callable_internal_entry` | 4,303 |
| `pdata_missing_from_ghidra` | 6,149 |
| `ghidra_missing_from_pdata` | 2,431 |

These are review evidence, not manifest-growth proposals. Ghidra merged/deleted
many `.pdata` definitions and expanded many bodies; the report preserves both
sides rather than choosing Ghidra.

Acceptance fixtures in the fully analysed exact map:

| Exact expected range | Verified role | Ghidra | Exact non-Ghidra evidence |
|---|---|---|---|
| `0x829647F0–0x82964800`, size `0x10` | virtual-dispatch leaf thunk | omitted | manifest/manual/fault walker/ReXGlue closure exact |
| `0x82C03B28–0x82C03B44`, size `0x1C` | conditional callback leaf through callback-table `bctrl` | omitted | manifest/manual/fault walker/ReXGlue closure exact |
| `0x829675E0–0x829675F0`, size `0x10` | virtual-dispatch leaf thunk | omitted | manifest/manual/fault walker/ReXGlue closure exact |

No Ghidra match was forced. The omissions are retained as
`manifest_missing_from_ghidra` plus `manifest_manual_only`.

No real public related-build Ghidra map was available. Historical configs and
Xenia patches remain incomplete/related/probable metadata only. Synthetic
tests cover all six identities, malformed/future schemas, contiguous and
fragmented bodies, thunks, aliases, multiple/internal entries, overlaps, every
diff class, deterministic idempotence and manifest non-mutation. No fixture
contains game bytes.

Focused validation commands:

```powershell
python -m unittest discover -s .\tests -v
python .\tools\Fable2FunctionMap.py catalog
python .\tools\Verify-Fable2MigrationLedger.py
.\tools\Invoke-Fable2EntrypointClosure.ps1
python .\tools\Verify-Fable2EntrypointClosure.py
```

Legacy closure schema 1/analyzer 1.0.0 remains accepted without fingerprint
fields. Schema 2/analyzer 1.1.0 requires exact fingerprint and executable
section ranges/permissions/hashes. The real schema-2 run completed in `57.4 s`
with `35,626` candidates, `55` strong, `178` probable and all three fixtures
independently rediscovered. The migration ledger remained `60,416`
definitions/declarations/mappings/registrations; all 32 entries passed.

Final regression results on `2026-08-29`:

- `python -m unittest discover -s .\tests -v`: 8/8 passed in `0.017 s`;
- full ReXGlue `ctest --preset win-amd64-release --output-on-failure`: 100%
  suite success in `35.64 s`; 1,684 executed tests passed and four pre-existing
  BitStream cases reported their configured `Skipped` status;
- `fable2-codegen`: success, exact TU1 recognized, zero generated changes;
- `fable2-build`: success with ReXGlue `0.10.0.8-dev.gfe1ae38`;
- `fable2-run` smoke run `015`: process remained responsive, completed ongoing
  asynchronous I/O, and its 564,050-byte log contained no `REX_FATAL`, invalid
  or unregistered-function, unhandled-exception, or fatal match. The verified
  `fable2.exe` process was then stopped after the smoke observation.

## Troubleshooting, limitations, next integration

- `Skipping unsupported -loader-Path to xexp` means the public loader is not
  compatibility-patched.
- The unmodified loader produced corrupt `.text` SHA-256
  `77968F4DCE4FEC2A2220AAE7E3C85B1765AC524F40DAF7CEA3D11B16FA4B90CA`
  and fingerprint
  `6A5FE7B9C0CED28727A672A4DDFCC0E97225CAE8ECC7F079E0046E877BCACE5D`.
  A map claiming exact inputs with that fingerprint is a confirmed mismatch.
- Ghidra's project image base may be zero despite absolute blocks. Exact raw
  import passes `0x82000000`; existing projects should pass `-ImageBase` or
  retain the exporter's recorded 64-KiB-aligned inference provenance.
- Individual p-code-constructor and embedded-media warnings did not abort the
  validated run, but affected functions still require boundary review.
- `.pdata` proves entry association, not arbitrary Ghidra body ends.
- Allow roughly `1.6 GB` memory for the full diff.
- A public database may embed executable bytes. Keep it ignored/outside the
  repo and export metadata only; do not upload or redistribute without licence
  and byte-content audits.

The completed next consumer reads `function-map-diff.json` with shared
contract schemas 1-3 and subtracts recovered switch cases before selecting a
narrow exact-identity boundary-validation queue. See
[`03-jump-table-recovery.md`](03-jump-table-recovery.md) for the current schema,
exact private-TU1 results, remaining unresolved indirect sites and the next
integration point. Preserve manual/fault-walker evidence and validate TU1
bytes/control flow before any manifest edit.
