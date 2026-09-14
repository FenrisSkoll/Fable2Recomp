# Phase 2I analyst annotation/export report

Phase 2I implements a read-only, explicit-opt-in query and export layer.
It does not open or mutate Ghidra, emit a function/symbol name, alter an
archaeology decision, or change production/runtime data.

<!-- PHASE2I_RESULTS_BEGIN -->
## Result

The frozen Phase 2H and SDK inputs validated. The normalized index contains
16,226 evidence records. The explicit closed mapping view has
15,299 active correspondences; the explicit Phase 2E
view has 15,379. Its delta is exactly
83 additions minus 3 suppressions, with
66 reserved and 17 unreserved additions.
All 720 excluded proposals remain warnings only.

Phase 2F contributes 116 unreviewed analysis contexts:
115 newly routed and one separately strengthened context.
Packet C is the sole owner-reviewed contextual role. The role is
`conditional keyed reward/world-map field materializer`; it is explicitly
CONTEXTUAL ROLE — NOT A FUNCTION NAME and retains reservation
`single-independent-support-class`.

The branch-guarded close-out reran the Phase 2F source/audit/publication/schema
checks, the complete 408-test supported discovery on frozen Phase 2G, and all
37 Phase 2H tests. Together with 44 Phase 2I tests, 489 distinct supported
tests passed with zero failures, errors, or skips.

## Selection and profile results

No mapping or semantic view is selected by default, and no export is written
without an explicit profile and confined output path. `all-correspondences`
additionally requires the deliberate bulk flag.

| Profile | Selected | Filtered | Deduplicated | Suppressed | Excluded | Reserved | Unreserved | Approved role | Unreviewed context | Rejected alias |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| address | 3 | 16104 | 0 | 0 | 0 | 2 | 1 | 1 | 0 | 1 |
| phase2h-approved | 6 | 16101 | 0 | 0 | 0 | 2 | 4 | 1 | 0 | 1 |
| overlay-review | 86 | 16016 | 0 | 3 | 0 | 69 | 17 | 0 | 0 | 0 |
| project-relevant | 82 | 16020 | 0 | 0 | 0 | 65 | 17 | 0 | 0 | 0 |
| semantic-review | 116 | 16102 | 0 | 0 | 0 | 75 | 41 | 0 | 116 | 0 |
| all-correspondences | 15379 | 723 | 0 | 0 | 0 | 66 | 15313 | 0 | 0 | 0 |

## Mandatory known cases

Packet C maps donor `0x825240E8` to TU1 owner `0x82522C10`. The
owner-reviewed annotation states `CONTEXTUAL ROLE — NOT A FUNCTION NAME`,
retains visitor range `[0x825237C8,0x82524454)` with direction unresolved,
and makes no reward-granting/arithmetic, map-marker creation, visibility
update, constructor, serialization-direction, or complete quest-object
ownership claim.

The correction annotations are:

- `0x821B24F8`: handle resolver; does not consume RewardMoney/RewardRenown.
- `0x823BF820`: scalar key consumer; `r4`; RewardRenown -> `+0x20/4`, RewardMoney -> `+0x24/4`.
- `0x82310290`: Boolean-like key consumer; AppearOnWorldMap -> `+0x4D/1` normalized byte.
- terminal `S-26C37A0D8DC5C81610D44E94`, SetObjectiveTag, is a rejected alias; interior `0x820C0000` is not a Packet C string.

The overlay tombstones are:

- `0x82631A30 -> 0x82950A98` Navigator -> Controlled.
- `0x828EA448 -> 0x82681198` TROLL_FOOTSTEP -> DESTROY_ENTITY.
- `0x83062950 -> 0x83060C30` __vspltb -> __vcfsx.

The corrected active vector mappings remain `0x83060A80 -> 0x83060C30`
(__vcfsx) and `0x83062950 -> 0x83060CD8` (__vspltb), with their exact
reservations preserved.

## Output contract and limitations

Each profile has canonical JSON, UTF-8/LF TSV, a preview-only Ghidra plan,
an exact rollback manifest, a bounded text preview, and an export receipt.
Comments are additive `[F2PA:phase2i:<annotation-id>]` blocks. Existing analyst
text/bookmarks are never owned; identical blocks are idempotent; stale same-ID
blocks conflict; exact removal preserves surrounding user bytes.

Transported strings remain evidence, not names. Packet A/HammerCombat and
Packet B/oxygen remain unapproved. Physics candidates, held mappings, probable
mappings, and suppressed routes are inactive. Visitor direction and all six
inherited blockers remain unresolved. No apply, mutation, database-save, rename,
function-creation, entry-point, comment, bookmark, or transaction API path exists.

## Actual ignored artifact identities

This table is mechanically compared with `evidence/annotation-summary.json`
and with the actual bytes. The validation envelope separately binds this report
and the summary, avoiding circular self-hashing.

<!-- PHASE2I_ARTIFACTS_BEGIN -->
| Repository-relative path | Bytes | SHA-256 |
|---|---:|---|
| `out/prototype-archaeology/phase2i/normalized-annotation-index.json` | 27884204 | `EF5F054E2B42878F07F25A6ED5BA8CF2D7C101B1EBFA642CD00A66AE972D7E61` |
| `out/prototype-archaeology/phase2i/profiles/address/annotations.json` | 9202 | `5C05FF7BE9F0C74041868DBD03914D5B7D114F58449E8AE7EECC33D3058BD32D` |
| `out/prototype-archaeology/phase2i/profiles/address/annotations.tsv` | 2424 | `9C0773429E921CD6FC0A5BE4A06B6CB3F7EDF3CCE6FAD81FDE0F0DCD41FC1B04` |
| `out/prototype-archaeology/phase2i/profiles/address/export-receipt.json` | 3873 | `F7ACCFBBF765E5B5EF315CBF2B71371691EA39BCF615BF50A2C5CEA529D09603` |
| `out/prototype-archaeology/phase2i/profiles/address/ghidra-plan.json` | 6141 | `839A31A0A1F508CBA0649F7AFA340DFC6FE26ADA718C91C361E75BF464164E1D` |
| `out/prototype-archaeology/phase2i/profiles/address/preview.txt` | 1468 | `D4041535B2F839273F769FD683E87D49078BAE0C7136A494D57A5809119E0096` |
| `out/prototype-archaeology/phase2i/profiles/address/rollback-manifest.json` | 4991 | `34529CF1F8014D432392A79CB4D369B0A7D3B151F1CEC2A765F3F00B00BC1811` |
| `out/prototype-archaeology/phase2i/profiles/all-correspondences/annotations.json` | 26432135 | `E32ED9B4DEC35FB7B37695C88C67F81F6228B5076899DA594D659D5F05FC70DE` |
| `out/prototype-archaeology/phase2i/profiles/all-correspondences/annotations.tsv` | 9661117 | `B384B40C922E1C753402814A8CCE5C7F410BCD86A43432BFE8FE85A6150E8DD7` |
| `out/prototype-archaeology/phase2i/profiles/all-correspondences/export-receipt.json` | 3217 | `FD893F4ED998990C3F9C6799F2FE82F2E72B386FB987604FFD585FB2A9030453` |
| `out/prototype-archaeology/phase2i/profiles/all-correspondences/ghidra-plan.json` | 14961558 | `7236DCB4BA67071D2037B9FCBEE62CF746CFF4802C011A0E9FF5842562F239C9` |
| `out/prototype-archaeology/phase2i/profiles/all-correspondences/preview.txt` | 36828 | `1BAC75F0245DDA71871DE345C6A880E3BE216933442CF3BD5506755A6FB52C52` |
| `out/prototype-archaeology/phase2i/profiles/all-correspondences/rollback-manifest.json` | 9890270 | `AB3D962F816D87F26051FCF53E3D961A4CC8A6D3554A20EFA54C4DDC697EF637` |
| `out/prototype-archaeology/phase2i/profiles/overlay-review/annotations.json` | 189223 | `30BF2A69E1C75FB57A0AB4E9474CF05EAE36270CF35A9CA4C34F780BB317784D` |
| `out/prototype-archaeology/phase2i/profiles/overlay-review/annotations.tsv` | 72180 | `F0736C21F95EF7CBF986714239400FEC3FCF795B6EFE758DBA766FB0E5ED3042` |
| `out/prototype-archaeology/phase2i/profiles/overlay-review/export-receipt.json` | 3158 | `7B4624A9558F3098BF64052CD6FE909CE9C81E7790D44B0BC08D3E66D41F66CC` |
| `out/prototype-archaeology/phase2i/profiles/overlay-review/ghidra-plan.json` | 90901 | `A05220B9E7E20BAA23DF8806A4FAC8EB163E18F2E7F21E369013EA08390CC1B5` |
| `out/prototype-archaeology/phase2i/profiles/overlay-review/preview.txt` | 36614 | `F72A941D1F7FFC95286D88ECA0715FE688F7C51D355ABF7D816E4381AD60E9DA` |
| `out/prototype-archaeology/phase2i/profiles/overlay-review/rollback-manifest.json` | 56838 | `C08D2328017DAFB6E9F077D2FA671EB4927CE44A5918E4ED1682B9F9613561EC` |
| `out/prototype-archaeology/phase2i/profiles/phase2h-approved/annotations.json` | 14275 | `186F53214D95521B943D1515E2059A5F1ED2B6720C9B2C9773D49AFA476B8703` |
| `out/prototype-archaeology/phase2i/profiles/phase2h-approved/annotations.tsv` | 4138 | `FFD71F61F1EB5E9370B96439886612BF0BE7B67FF8619A7FFE1B4CDC0CB208A9` |
| `out/prototype-archaeology/phase2i/profiles/phase2h-approved/export-receipt.json` | 3937 | `60C4B25881FBBB2B0D47CC9BFCEA29A95DDEABC917F2B1F94A90B73EE39549CF` |
| `out/prototype-archaeology/phase2i/profiles/phase2h-approved/ghidra-plan.json` | 8893 | `582834A56090633F1E6351AC72EEF05D4A213BD2A8D7F662A48F0D956B9EEBED` |
| `out/prototype-archaeology/phase2i/profiles/phase2h-approved/preview.txt` | 2399 | `B00A915D9DF26AA185764165CA5FF281B31ABDF77BC0E9B761D403AB70CBBB40` |
| `out/prototype-archaeology/phase2i/profiles/phase2h-approved/rollback-manifest.json` | 6926 | `C64C3A2C09508FE9DE849CE90902E292FF37ACBD1B5BCB751C7A338835224C22` |
| `out/prototype-archaeology/phase2i/profiles/project-relevant/annotations.json` | 181970 | `4D9FBB1A30E9571C223835B662201A4A01B2141E21ADD55729276A88BBEB4A9A` |
| `out/prototype-archaeology/phase2i/profiles/project-relevant/annotations.tsv` | 69670 | `64FD8B5165786E9F12FCA88CE4B5135302CF90F34B2F3F89A5A8F804D2675932` |
| `out/prototype-archaeology/phase2i/profiles/project-relevant/export-receipt.json` | 3172 | `C23301E053EB1B92D580349FD63BE0D3D0D8D3018019A048CA804C332DE99EDD` |
| `out/prototype-archaeology/phase2i/profiles/project-relevant/ghidra-plan.json` | 87227 | `2F1AD0705344A4CE1FB0A91765F8B883C8828DE59755DF73C54D5BC683F5FD47` |
| `out/prototype-archaeology/phase2i/profiles/project-relevant/preview.txt` | 35368 | `A90D694B73A75002610A65769AD978649344FDC5E18D255FA40AC5B6F61AADE8` |
| `out/prototype-archaeology/phase2i/profiles/project-relevant/rollback-manifest.json` | 54295 | `A3B89F13723D4990E9236C1B264774065E1E2F73660C13BF83D185B5686FC366` |
| `out/prototype-archaeology/phase2i/profiles/semantic-review/annotations.json` | 219341 | `F89EC7DC2AD67FA3D0FA24DD38E25E5C4A941DA4A80B2089C919769607A81D59` |
| `out/prototype-archaeology/phase2i/profiles/semantic-review/annotations.tsv` | 81152 | `E39AC273C4E17DDDE763CA0F937E731BB740BF7CE562A5605CFAB427DD66C76C` |
| `out/prototype-archaeology/phase2i/profiles/semantic-review/export-receipt.json` | 3235 | `B7561C6F40A32619BA941509E2235495920DF559C03F7C01B5F9C51036B48E68` |
| `out/prototype-archaeology/phase2i/profiles/semantic-review/ghidra-plan.json` | 118706 | `4F37BE439BEA7D1D88D07CB11B27E5D4C69F5CABCBB7C3ABBC93AA98E485955F` |
| `out/prototype-archaeology/phase2i/profiles/semantic-review/preview.txt` | 39413 | `8EF2AD7E6A74E071249FA5C835102A0A3E2871584D262CD4F2FEE1CF3AFE5E33` |
| `out/prototype-archaeology/phase2i/profiles/semantic-review/rollback-manifest.json` | 77309 | `9148999D3EA38FE38765EC99A83C9D895BEAB1C03DEA51E51AA10F7CD54EA3D2` |
| `out/prototype-archaeology/phase2i/receipts/collision-controls.json` | 1146 | `8956DB0789E226E776C98A994ED3DDAF0A8344713BABBDFD8D7FA8334CE4C7D5` |
| `out/prototype-archaeology/phase2i/receipts/consistency.json` | 2910 | `150FB3C31A57CEF1F9344F2C7844EBF3CA880C19847EE820A21EF86A28BC9992` |
| `out/prototype-archaeology/phase2i/receipts/git-delta.json` | 3016 | `FFAE0C32F4297D2938421B320BB39F718B9C1FBE3C785886131E4DFCA21BEA42` |
| `out/prototype-archaeology/phase2i/receipts/negative-controls.json` | 875 | `DFA47E9A25D5C83CA04F4B347F9EEFBE7054C5D69E567E35113FAD469B948262` |
| `out/prototype-archaeology/phase2i/receipts/path-audit.json` | 712 | `288EFC829844ED2B35A84D7C919BC61EE155ABE027D73B7B4DAAC01BE8E5202B` |
| `out/prototype-archaeology/phase2i/receipts/replay.json` | 5937 | `C44CC2E3911BCBE9984E3420F6DDE56D2970A5DCD8667BCAD0B409D584100E20` |
| `out/prototype-archaeology/phase2i/receipts/schemas.json` | 838 | `886B98BCDAA8AC959AEF5DCB37982AB485CF965A4E60F329F38BE946D55AEC80` |
| `out/prototype-archaeology/phase2i/receipts/sdk-preservation.json` | 3242 | `8569128FEE00FDBC46C8648D5AF9AA63FF4BBC1BECA61703DA89695E65C4B1C7` |
| `out/prototype-archaeology/phase2i/receipts/source-inspection.json` | 958 | `40F3EDE1C8362167BA4BEFD2416BA004647B65311E3B77F35FDFB5A4CBBEF72B` |
| `out/prototype-archaeology/phase2i/receipts/tamper-controls.json` | 674 | `91DEE5189D5FBA069FC14442F814DFDAB5EC77591D35E31DFE45B8DC8F4EABDE` |
| `out/prototype-archaeology/phase2i/receipts/tests.json` | 666 | `AC162A2EEE027E64990838F1425334FD97B7CA27D0BD86E39405D4C8C5DE6C46` |
<!-- PHASE2I_ARTIFACTS_END -->
<!-- PHASE2I_RESULTS_END -->
