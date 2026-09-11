# Prototype Archaeology Phase 2A report

Generated evidence timestamp: `2026-09-11T00:00:00Z`

Generator: `Fable2PrototypeCorrespondence.py` version `1.0.2`, policy
`precision-first-v1`, commit `f5836c4736b370e8e7b027fb6a602f2dad1d0992`

## Executive result

Phase 2A establishes a **viable precision-first binary-correspondence core** from the July 2009 /
build `23.12.02.0330` development image to canonical post-patch Fable II GOTY TU1. It accepts
15,299 of 46,179 donor `.pdata` functions: 2,779 reciprocal unique raw-byte pairs and 12,520
reciprocal unique branch-normalized pairs with independent corroboration. The remaining 30,880
functions are explicitly classified rather than forced into mappings.

The byte-identical July/build-23 positive control accepted 46,025 of 46,179 oracle pairs, with
zero false accepted cross-address pairs, precision `1.0`, and recall `0.996665150826`. Precision is
defined here only against that exact-image same-start oracle. It does not estimate donor-to-TU1
correctness and it says nothing about semantic identity.

No semantic TU1 names were assigned. No manifest entry, function override, generated source,
runtime code, renderer code, or canonical input was changed. An accepted record is a binary
correspondence claim, not a source symbol or proof of what the function means.

## Input binding

Every output repeats an input bundle with exact provenance. A mixed, stale, missing, or differently
hashed input causes generation or verification to fail.

| Identity | Exact value |
| --- | --- |
| Preferred donor container | `Fable II July 10 2009 23.12.02.0330/default.xex` |
| Preferred donor container SHA-256 | `0686A9F292A3F6777BEB6E8D4924F96247D1E8E3E2370323572F797E6637A4AA` |
| July container alias SHA-256 | `0AAA3C8EF72ECBB607C9D8A50C42022F3E0BDE759A462CB14148621790C0E348` |
| Donor initialized executable-memory fingerprint | `AE15F6D9AF8C76B3643A0CB5EF7B108E686794250F6822C2A71C78FE3D0BE956` |
| Donor `.text` | start `0x82170000`, size `18132124`, SHA-256 `A49213732D2E64610939BBBAE6985F9248457DFE46278E3215F11CB68A071878` |
| Donor `.pdata` | start `0x8210B800`, size `369432`, SHA-256 `1805B91295ACEAEC07CE437A84DFF25E75A8B69B155C764838E3864E26C0BCB9`, 46,179 functions |
| Canonical base XEX SHA-256 | `88C4EF2E18E65409444D1B068EFF921D1F7E180A5AE64EDC64BA6B0872372662` |
| Retail XEXP SHA-256 | `046A05693B4DA4437083C784000A850858B3BF992955C7DB30D518FB3E53E41C` |
| Post-patch image SHA-256 | `BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00` |
| Target initialized executable-memory fingerprint | `5C8B78B84C93028D166E3DF347206E6642BA40BF374AD1AF8D958B2211320357` |
| Target `.text` | start `0x82170000`, size `18131900`, SHA-256 `1B9F2E80280637FE2287286ED3FE18B367F378E24A695A2B8AB50B9ACD8FC724` |
| Target `.pdata` | start `0x8210B800`, size `369440`, SHA-256 `FE6A61E508AD67FC39BEA85372A06DA1CAF40C5F1E7BB2B52FF37471FE44AB3C`, 46,180 functions |
| Target entry/version | `0x82CC21C0`, `0.0.1.26` |
| Closure SHA-256 | `665CA2AE7ED65632B2E9F368063D3D9EE260E8DEF6F276B455CD62A9F2DCC397` |
| Generator runtime | `CPython 3.14.3`, cache tag `cpython-314` |
| Input bundle SHA-256 | `8A3C3C25DFDAA856BA848C408B4677B719217449C7BE111F42D40F08B3F07194` |

The July and build-23 containers have different hashes, but all 15 initialized derived sections,
their `.pdata`, and the resulting executable-memory fingerprint are byte-identical. The preferred
donor is therefore build `23.12.02.0330`; July is retained as an exact-image alias and positive
control rather than analysed twice.

The Phase 1 `.text` inconsistency was resolved before correspondence generation. Direct hashes of
the ignored section bytes agree with the authoritative machine evidence: September is
`B13E8571539FCD74735A16F3F4E434EDDB6F9ECF09E970CC725E78756192FFB3` and
July/build-23 is `A49213732D2E64610939BBBAE6985F9248457DFE46278E3215F11CB68A071878`.
The former human-report values were stale transcription errors, not hashes of a different byte
domain. A cross-artifact validator now checks the derived bytes, XEX metadata, TU1 relationship
evidence, alias sections, and report table together.

## Correspondence model

The primary unit is each exact big-endian `.pdata` interval. Every donor interval occurs exactly
once in the committed status index. The engine records:

- raw-byte SHA-256;
- branch-normalized SHA-256, clearing only `b`/`bl` LI or `bc` BD displacement fields while
  preserving AA, LK, BO, BI, and unrelated instruction bits;
- opcode/XO structure, used only to generate weak candidates;
- size, instruction count, conditional/direct-call/return/indirect shape;
- deterministic control-flow block/edge shape;
- direct caller/callee topology after provisional reciprocal mappings;
- ordered and exact-address-delta local neighbourhood evidence;
- filtered readable string references and 16-byte content hashes for materialized `.data`,
  `.rdata`, or `.edata` addresses; and
- boundary flags plus normalized-prefix evidence for possible split, merge, shifted, overlap, or
  truncation review.

The accepted mapping is reciprocal and injective. A raw-byte pair must also be unique, boundary
valid, one-to-one, and free of shape, neighbourhood, and topology contradictions. A normalized
pair must be reciprocal unique, have equal CFG/branch shape, and carry at least one additional
sound class from exact address-delta neighbourhood, mapped call topology, string content, or data
content. Tiny leaves, common thunks/idioms, padding-dominated records, and boundary-risk cases are
corroborated or quarantined. Opcode/XO equality and same guest address are never acceptance rules.

The documented review score is a ranking aid only. Acceptance does not compare a score with a
threshold, and each accepted record exposes its features and contradiction checks.

## Positive-control calibration

The July/build-23 initialized images and `.pdata` are identical, so the oracle correspondence is
the same start and boundary.

| Metric | Result |
| --- | ---: |
| Functions represented | 46,179 |
| Accepted correct same-start pairs | 46,025 |
| False accepted cross-address pairs | 0 |
| Precision (`correct accepted / all accepted`) | `1.0` |
| Recall (`correct accepted / all oracle functions`) | `0.996665150826` |
| Ambiguous | 138 |
| Quarantined | 16 |
| Unmatched | 0 |

The 154 conservative non-acceptances are intentional: 138 duplicated fingerprints and 16 risky
tiny/common functions. By shape, 33,193 of 33,263 direct-call functions and 12,480 of 12,548
indirect-branch functions were accepted. Only one of 17 tiny leaves was accepted; the other 16
were quarantined. No cross-address false acceptance was tolerated before the TU1 run.

Ten deterministic synthetic fixtures also passed: relocated identical blocks; changed `b`, `bl`,
and `bc` displacements; a normalized pair with exact-neighbour corroboration; duplicate tiny
leaves/thunks; changed direct-call targets; reordered neighbours; one-to-many/many-to-one sets;
split/merged or shifted `.pdata`; opcode-similar but different bodies; and relocated materialized
string/data addresses.

## Donor to canonical TU1 results

| Terminal status | Count | Interpretation |
| --- | ---: | --- |
| `accepted-exact-unique` | 2,779 | Confirmed byte-level binary correspondence under the stated boundary and contradiction policy |
| `accepted-normalized-corroborated` | 12,520 | Strongly supported relocation-aware binary correspondence |
| `candidate-structural` | 15,337 | A unique structural candidate exists but lacks acceptance evidence |
| `ambiguous` | 15,331 | More than one fingerprint-derived candidate remains |
| `quarantined` | 210 | Risk, contradiction, or compiler-idiom guardrail prevents acceptance |
| `boundary-change` | 0 | No reciprocal unique changed-size prefix case survived primary review rules |
| `unmatched` | 2 | No shared fingerprint candidate |
| **Total** | **46,179** | One terminal record per donor `.pdata` function |

The two unmatched donor functions are `0x826E3720-0x826E3B34` (1,044 bytes) and
`0x82BAD3B8-0x82BAE038` (3,200 bytes). The lack of primary `boundary-change` records is a negative
finding, not evidence that no boundary changes exist: normalized 16-byte prefixes created
92,491,129 potential edges, most dominated by common prologues, and were deliberately barred from
automatic acceptance.

Only 24 accepted pairs have the same guest start. Thus the accepted core is not an address-copying
result. Corroborating evidence across accepted records includes:

| Feature class | Accepted records carrying it |
| --- | ---: |
| Equal CFG and branch shape | 15,299 |
| Exact relative-neighbour deltas | 14,967 |
| Mapped direct-call topology | 8,929 |
| Local ordering without exact delta | 254 |
| Stable nontrivial data-content anchor | 97 |
| Distinctive string-content anchor | 1 |

The one accepted string-bearing pair is donor `0x8229B308-0x8229B484` to target
`0x8229B038-0x8229B1B4`. Both raw bytes and the string `HammerCombat` match; this is evidence for
the binary pair, not authorization to name either function. The mapping also has equal 22-block /
31-edge CFG shape and a stable `.rdata` content anchor at `0x8200131C`.

The complete candidate statistics explain why weak matches were retained rather than accepted:
raw fingerprints yield 2,971 reciprocal unique pairs and 3,630 candidate edges; branch-normalized
fingerprints yield 16,523 reciprocal unique pairs and 236,293 edges; opcode/XO structure yields
27,578 reciprocal unique pairs but 9,048,713 edges. The last figure demonstrates that opcode-only
similarity is far too permissive for automatic correspondence.

## Review surfaces and exhaustive evidence

The committed review queue contains 45 deterministic records, five each for accepted exact,
accepted normalized, ambiguous, structural, quarantine, tiny-leaf, indirect-branch, string, and
data-anchor strata. It is a bounded audit surface, not a second acceptance source. The complete
status index retains candidate counts, ambiguity classes, an accepted target where applicable,
and up to three ranked candidates. It never silently discards the total ambiguity count.

Lossless exhaustive material remains ignored because it is reproducible and substantially larger:

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `out/prototype-archaeology/phase2a/prototype-correspondence-candidate-groups.json` | 9,638,474 | `99F3DB1F430A1D540D05067891795E1A5CD35C9A98A9F9DD83468298B50B3AB2` |
| `out/prototype-archaeology/phase2a/prototype-correspondence-function-features.json` | 136,999,129 | `9D165A7F2A43BF662CB25317AC0EF71C581A175A141D28260CCE6E65CA64A312` |

For each shared fingerprint, the exhaustive group file is lossless because its donor and target
members define the full Cartesian candidate edge set. The committed summary binds both ignored
files by path, byte size, and SHA-256.

## Independent September robustness study

September 2008 is not a ground-truth oracle. The study therefore reports reciprocal consistency
and failure classes, not accuracy. From 45,707 September functions to 46,179 build-23 functions,
the same precision policy accepted 9,600 pairs (1,847 raw, 7,753 normalized), retained 14,884
ambiguous and 16,243 structural candidates, quarantined 162, found 33 boundary-review cases, and
left 4,785 unmatched. The substantially larger unmatched/boundary tail is consistent with a more
distant image and shows that the engine does not depend on July/TU1 proximity alone.

## Evidence grades and limitations

**Confirmed:** all bound hashes and function boundaries; July/build-23 initialized-image identity;
raw bytes of the 2,779 exact accepted pairs; positive-control outcomes; deterministic status and
aggregate counts.

**Strongly supported:** the 12,520 normalized accepted correspondences, under reciprocal
uniqueness, injectivity, equal CFG/shape, independent corroboration, and contradiction checks.

**Candidates/hypotheses:** all `candidate-structural`, `ambiguous`, `boundary-change`, and review
records. They must not be treated as identities or symbols.

Important negative findings and limitations:

- no semantic function name was inferred or propagated;
- no opcode/XO-only or same-address-only pair was accepted;
- no primary changed-boundary hypothesis met the intentionally narrow review criterion;
- only one accepted pair retained a filtered string-content anchor, so textual semantics cannot
  drive broad correspondence;
- indirect control-flow topology remains structural; unresolved targets are not invented;
- a perfect control result cannot prove cross-build correctness;
- `.pdata` describes the chosen function units but may not express every compiler chunk/split; and
- September has no complete oracle, so its 9,600 accepted pairs are coverage, not measured
  correctness.

## Outputs

All committed JSON documents use the artifact-specific names in the
`fable2-prototype-correspondence` schema family, version `1`, and validate against
`tools/schemas/fable2-prototype-correspondence-v1.schema.json`.

| File | Purpose |
| --- | --- |
| `evidence/prototype-correspondence-index.json` | Complete 46,179-function status/candidate index |
| `evidence/prototype-correspondence-accepted.json` | Accepted records with explicit evidence and contradiction checks |
| `evidence/prototype-correspondence-review.json` | Bounded, stratified 45-record manual queue |
| `evidence/prototype-correspondence-validation.json` | Positive control, ten synthetic fixtures, and September robustness |
| `evidence/prototype-correspondence-summary.json` | Input binding, policy, counts, aggregates, candidate and exhaustive hashes |

Reproduction commands are in [README.md](README.md). The recommended semantics-only continuation
is in [phase2b-handoff.md](phase2b-handoff.md).

## Verification ledger

The final evidence passed the following checks from the repository root:

- Phase 2A generation with `--check-determinism`: byte-identical committed outputs, 46,179 donor
  functions, 15,299 accepted mappings, and 45 review records;
- `Fable2PrototypeCorrespondence.py verify`: all functions represented once, accepted boundaries
  valid, reciprocal/injective mappings, terminal totals reconciled, no opcode-only acceptance, and
  all bound identities/hashes current;
- `Verify-Fable2PrototypeCorrespondenceJson.ps1`: five artifacts schema-valid;
- `test_fable2_prototype_correspondence.py`: 12 tests passed, including all ten synthetic fixtures;
- Phase 1 generation with `--check-determinism`: 11 artifacts byte-identical;
- Phase 1 immutable verification: 1,184 files and ten evidence artifacts verified;
- Phase 1 cross-artifact consistency: three XEX builds and 15 initialized-section aliases
  verified against actual bytes;
- Phase 1 JSON validation: ten artifacts schema-valid;
- Phase 1 unit suites: nine tests passed;
- existing function-map, closure, indirect-target, ownership, and coverage-baseline suites: 71 tests
  passed;
- canonical Ghidra function-map validation: schema 1, 42,462 functions,
  `identity=exact_image_match`; and
- authoritative entrypoint-closure validation: schema 3, analyzer `2.0.0`, image
  `BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00`, 35,626 candidates,
  55 strong, 180 probable, and three fixtures.

The final path audit found no modified prototype source, `fable2_manifest.toml`, semantic-name
source, generated recompilation source, renderer/runtime code, or proprietary binary.
