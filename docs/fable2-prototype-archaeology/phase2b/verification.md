# Phase 2B verification record

All checks below completed with exit code 0 against the implementation commit
`e351c205b2875e898c678bbc9064016f0a97a164` and the final evidence bytes. No test
executes a prototype or the retail game.

| Check | Result |
| --- | --- |
| `python -m unittest discover -s tests -q` | 188 tests passed, including 37 new Phase 2B tests; no existing invariant changed. |
| `python tools/Fable2PrototypeSemantics.py generate` | 1,409 source identities verified; nine exhaustive artifacts, summary and report generated; terminal reconciliation and forbidden-path/SDK audit passed. |
| `python tools/Fable2PrototypeSemantics.py verify` | Independent complete replay matched all analytical JSON, summary and report bytes; no writes. |
| `.\tools\Verify-Fable2PrototypeSemantics.ps1` | All eleven JSON artifacts passed the committed version-1 schema. |
| `python tools/Fable2PrototypeArchaeology.py verify` | 1,184 immutable corpus files and ten Phase 1 artifacts verified before analysis. |
| `python tools/VerifyFable2PrototypePhase1Consistency.py` | Three XEX builds and fifteen aliased initialized sections verified before analysis and at close-out. |
| `python tools/Fable2PrototypeCorrespondence.py verify --tool-commit 5f96fcf81bf9511dabadc63326468d9de94f87da` | Closed Phase 2A verified before consumption: 46,179 donor functions, 15,299 accepted pairs; no regeneration. |
| `python tools/VerifyFable2PrototypePhase2AConsistency.py` | Both exhaustive Phase 2A hashes/report identities verified before consumption and at close-out. |
| Canonical `Fable2FunctionMap.py validate` | Schema 1, 42,462 functions, exact image match. |
| Current `Verify-Fable2EntrypointClosure.py --report .../closure-after/entrypoint-closure.json` | Schema 3, analyzer 2.0.0; 35,626 candidates, 54 strong, 180 probable, three positive fixtures. |
| Git whitespace and Phase 2B-only delta audit | Passed; only analysis/test/schema/documentation and narrowly scoped LF attributes changed. |
| ReXGlue state comparison | Branch, full HEAD/tree, remotes, porcelain status and fifteen materialized libmspack file hashes unchanged. |

The complete test discovery includes existing Phase 1, Phase 2A, function-map,
closure, ownership, indirect-target and coverage suites. An initial invocation
by package-qualified module names failed to import the ownership/coverage
helper module; their supported discovery invocation passed without changing
those suites. A draft schema had a missing closing delimiter; it was corrected
before validation. Neither development error was hidden by weakening a test.

New fixtures cover signed high/low carry, readonly base-relative indirection,
direct pointer/callback descriptors, repeated fixed strides, counted loops,
aliases, unknown writes, writable-pointer rejection, interior/non-executable
callbacks, adjacency-only rejection, intermediate-high-half false references,
stripped target descriptors with three accepted pairs, contradictory roles,
generic ambiguity, absent correspondence, external-only evidence, graph bounds,
incompatible scalar accesses, forbidden output paths, duplicate/omitted terminal
records, accepted-subset drift, review availability drift, report/provenance
regression and no semantic propagation. These controls test implementation
properties; they do not estimate semantic accuracy on retail functions.

## Final evidence identities

| Committed artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `report.md` | 43,008 | `1D3AA0A8EBC83ACB12C61841AA6F18ACF3E337432FF6028F68704EDD32D2BE0E` |
| `evidence/semantic-validation.json` | 5,798 | `44AA74E385EC64A0EC21837FF527B5ECD672FF71293FCD41B6FB15B4F3C78D5E` |
| `evidence/semantic-source-pins.json` | 311,969 | `4B3165E637A56A7FF2C0F06F78281D1FDF033A85CB36F8A360B8B8F8134890F1` |

The validation artifact contains exact sizes/hashes for all nine ignored
outputs and all five implementation/test/schema files. There are 69 selected
review rows with explicit stratum availability and 21,350 separate mapping-
review rows. No mapping-review row changes Phase 2A.

## Repository preservation

Fable2Recomp started clean on `fable2-prototype-archaeology-phase2a`, HEAD
`6ce54cbdcaa9fef23c6cd13e86fe46d3783cf3fd`, tree
`774c4f401bd44f8de1ea8f95c7344988ad12773c`. The new branch was created from that
exact commit. Only logical local commits were made; the final evidence commit
is the commit containing this record, obtainable using the handoff commands.

ReXGlue remained on `fable2-prototype-archaeology-phase1`, HEAD
`fa10315ff88ca56b2d0b380de40bad5b59b542bd`, tree
`ec06d4e7e56beb81551c6089e9768b7588606f20`, with only the original
`thirdparty/libmspack` materialized-file modification. Initial remotes/status
and exact modified-file hashes are retained in the source pins.

No canonical names, manifest, overrides, generated C++, runtime, renderer, SDK
code/dependency, prototype, update or derived executable input changed. No
private executable bytes or bulk script content were committed. No game launch,
input automation, capture, screenshot, build/codegen or shader-bank parsing
occurred. The only network operation was the explicitly authorized, hash-checked
pinned community raw-file download. No push, Git fetch/pull, merge, tag, PR,
upload or release occurred.
