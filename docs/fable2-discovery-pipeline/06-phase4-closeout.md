# Phase 4 closeout and deferred ownership backlog

## Outcome and boundary

Phase 4 delivers a disabled-by-default Xenia indirect-control-flow collector,
schema-1/schema-2 crash-tolerant parsing, deterministic raw and compact-summary
merging, evidence classification, dry-run planning, guarded explicit apply and
a report-only ownership backlog. This closeout preserves and publishes only
compact address/evidence artifacts. It publishes no game executable, title
content, asset, save, raw trace, memory dump, cache or credential.

The two real private-TU1 compact summaries merge to 16,143 non-return targets.
All are explained by existing effective registrations, existing-function
internal entries, recovered jump-table cases or import/kernel ownership. The
merged plan has zero range proposals, zero ambiguous/conflicting/invalid
targets and zero automatically applicable candidates. The canonical manifest
remains unchanged at SHA-256
`E3EB39CA153E396D5DC53E6F943ED8FF7AF1D6B0704EB860836BD7D21A3F87B0`.

Static review of the 567 targets added by manual-002 is explicitly deferred.
Another gameplay capture could expand coverage but is optional. Native
save-write parity is the next active development phase.

## Exact TU1 identity

| Field | Value |
| --- | --- |
| patched executable SHA-256 | `BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00` |
| title ID | `0x4D5307F1` |
| media ID | `0x716F0A0D` |
| version | `0.0.1.26` |
| image base | `0x82000000` |
| executable range | `0x82170000`-`0x832D0000` |
| loaded executable fingerprint | SHA-1 `341151E9932EC14CB4F520AA9DE35BCF7169BFE1` |

The launch-media ISO and patched executable identity are different identity
layers. The ISO is the final positional Xenia argument; its hash is never used
as the analysis-image identity.

## Preserved runs and compact merge

The user-confirmed coverage, recorded separately from immutable embedded run
labels, is:

- `fable2-tu1-manual-001`: new game, childhood progression and first save;
- `fable2-tu1-manual-002`: load that save, continue gameplay, visit shops and
  perform another save.

Manual-001 remains collector schema 1,
`abnormal_or_unknown_no_footer`, zero footers/errors/drops/overflows and an
unavailable raw-schema value. Its approximately 95 GB raw trace was
intentionally deleted after compact preservation. Its recorded raw SHA-256,
`05E6344E2992089A9F7B7F509D8099D7E8851D130F2769BE9B9A8F72F20E03D0`,
is historical provenance read from the summary, not a closeout recomputation.

Manual-002 remains collector/raw schema 2, normal with exactly one footer and
zero errors, drops, overflows, aggregate-limit failures or integrity warnings.
Its preserved recorded raw SHA-256 is
`83DAA210412E6941AC0EE44D69EAED19C244FACC3D3637E93F4647132E67BD4D`.
Neither raw trace is read or published. Compact summary schema 1 omits
`flush_reason`; the closeout does not invent `window_close` for either compact
run record.

| Metric | Value |
| --- | ---: |
| input aggregate records | 49,746 |
| merged source/target keys | 27,785 |
| manual-001 only / manual-002 only / both keys | 4,671 / 1,153 / 21,961 |
| manual-001 / manual-002 / combined hits | 24,555,201,598 / 19,275,373,582 / 43,830,575,180 |
| merged non-return targets | 16,143 |
| manual-001 only / manual-002 only / both targets | 2,093 / 567 / 13,483 |

Merged classifications are 13,087 `existing_manifest_function` records, 1,486
existing-function internal entries, 1,561 known jump-table cases and 9 known
import/kernel targets. `existing_manifest_function` means an effective
generated registration, not necessarily one of the hand-authored manifest
overrides.

## Ownership-follow-up schema and command

The version-1 schema is
`tools/schemas/fable2-phase4-static-ownership-follow-up-v1.schema.json`. The
authoritative JSON selects exactly the target-set difference
`manual-002 - manual-001`; CSV and Markdown are deterministic review views.
The command and exact output identities are documented in
`05-xenia-indirect-targets.md`.

Legacy summary metadata is normalized through one validation path. Missing
`raw_schema_version` is preserved as JSON `null` plus
`unavailable_in_legacy_summary`; it is never inferred from collector schema.
An explicit schema-2 value remains `2` plus `recorded`. An absent compact
`flush_reason` remains JSON `null` plus `unavailable_in_compact_summary`.

Queue priority and counts are:

1. 42 existing-function internal entries: determine basic-block, callable
   internal entry, exception landing, incorrect boundary or unresolved status.
2. 114 known jump-table cases: verify owner, dispatch/table identity, target
   set, CFG ownership and manual-annotation equivalence.
3. 411 existing effective registrations: review only when static ownership or
   provenance disagrees.

All 567 records state that they were absent from manual-001, retain their
manual-002 sources/kinds/hits and known ownership, and explain why they are not
manifest proposals. The generator is report-only, deterministic and atomic. It
does not apply, split, promote, infer a range from runtime spacing, convert a
switch case into a function or produce a stub.

## Acceptance observations

| Target/range | manual-001 | manual-002 | Combined | Classification |
| --- | ---: | ---: | ---: | --- |
| `0x829647F0`-`0x82964800`, source `0x829641C4`, `bctrl` | 2,849 | 1,903 | 4,752 | existing function, size `0x10`; no proposal |
| `0x82C03B28`-`0x82C03B44`, source `0x821907A4`, `bctrl` | 13 | 4 | 17 | existing function, size `0x1C`; no proposal |
| `0x829675E0`-`0x829675F0`, source `0x82966EE4`, `bctrl` | 3,257 | 2,358 | 5,615 | existing function, size `0x10`; no proposal |
| `0x821746BC -> 0x82174734`, `bctr` | 16,635 | 85,787 | 102,422 | jump-table case owned by `0x821746A8`; no proposal |

Historical `0x823DCAD8` and `0x82403720` observations remain separate earlier
evidence and are not misrepresented as runtime sources in either merged run.

## Durable archive and publication

The authoritative local archive is:

```text
C:\Dev\Fable2Phase4Archive\2026-09-02-phase4-closeout
```

It contains a self-describing README, versioned archive manifest, explicit
SHA-256 allowlist, verified Fable2Recomp and Xenia Git bundles, compact source
artifacts and three deterministic ZIP packages. ZIPs are constructed from
explicit member allowlists, inspected for path traversal/unexpected content,
extracted into fresh temporary directories and rehashed before publication.

The evidence publication uses:

```text
tag:     phase4-evidence-2026-09-02
title:   Phase 4 indirect-target evidence — 2026-09-02
release: https://github.com/FenrisSkoll/Fable2Recomp/releases/tag/phase4-evidence-2026-09-02
```

Only these assets are authorized:

```text
phase4-manual-001-compact.zip
phase4-manual-002-compact.zip
phase4-manual-001-002-merged.zip
archive-manifest.json
SHA256SUMS.txt
```

The release is analysis evidence, not an end-user game/software release. The
archive manifest and release API provide final commit/tree, bundle, asset-size,
hash and remote-ref identities without introducing the 27 MB summary or 58 MB
plan into normal Git history.

## Recovery and next work

The Git bundles allow recovery of the complete Phase 4 feature/main history and
the separate collector branch without relying on a working directory. Compact
summaries are sufficient for deterministic remerge and planning; the deleted
manual-001 raw trace is not damage to preserved compact evidence.

The next active work is native save-write parity. The 567-target ownership
queue remains a prioritized future static-analysis backlog. A new capture is
optional and, if desired later, must use a new run ID and the ISO/TU-content
workflow in `05-xenia-indirect-targets.md`.
