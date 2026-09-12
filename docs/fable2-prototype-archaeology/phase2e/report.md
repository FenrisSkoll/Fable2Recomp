# Phase 2E approved non-canonical mapping overlay

## Decision and immutable baseline

The exact Phase 2D commit `6db4b4374c6e5cac180b92e23fb0bbeec86c4500`, tree `23f28f9d3ba2e4acf0365bcf7e4e1f065ea47ecb` and terminal subject were verified before branching. All frozen Phase 1-2D bytes, 20 Phase 2D bound artifacts, 30 protected Phase 2C artifacts, 187 Phase 2C gates, 39 fixture categories, ReXGlue state and fifteen libmspack hashes remain unchanged.

Owner `FenrisSkoll` supplied decision `approve` at `2026-09-12T22:00:00+01:00`, external record `P2D-OWNER-DECISION-001`, for `reversible non-canonical semantic-transport and mapping overlay only`. The Phase 2D ledger remains byte-identical with 91 pending rows, `human_approval: false` and `canonical_adoption: false`. Phase 2E records the exact-scope approval separately; canonical adoption remains false.

Approved batches and independently recomputed hashes:

| Batch | Actions | SHA-256 |
| --- | ---: | --- |
| `B00-semantic-suppressions` | 3 | `0386951B064C2F7FCDBD70FCD44BCFA7479BE4435EEDD30EF833B1D1BCDE7E6E` |
| `B01-unreserved` | 17 | `6C2DBAAED2887ACD57E9A2123601E514611B8D39A70A40D08723F86ADE3525B1` |
| `B02-multiple-references-reserved` | 5 | `1365725CBD2B5130F16C2004E347E3C9497F8AF457D4E72E171B54E9E8413A96` |
| `B04-callee-only-reserved` | 60 | `AD7AE0056AEBB9A903B51E75123BD196EE764B88743DADB33E78D5E1F399D4BF` |
| `B05-internal-region-reserved` | 1 | `FBB88D754E43B8B6035E9CC3D267861E08321FEDAC4F5086DADB3F3C491E4124` |

The selected 86-ID set hash is `8E9CBB93751C0F0B13FF04F1809207D72C0C96587369FEEA0C528F0A9EEE2363`. The global 91-record Phase 2D ledger proposal-set hash remains `7576AB812DEA66388C4CA1BF2BE9FB5C32B06E9C7F9C1C0E1C9CF283E731CCD4`.

## Effective population

The approved delta contains three mandatory semantic-transport suppressions, 17 unreserved additions and 66 additions with preserved reservations: 83 mapping additions and 86 actions total.

```text
15,299 closed Phase 2A pairs
-     3 semantic-transport suppressions
+    83 Phase 2D-reviewed mapping additions
= 15,379 unique effective mapping pairs
```

The net delta from Phase 2A is +80 and from the frozen Phase 2C proposed view is -3. Donor and target starts are independently injective. Every dependency is closed, earlier-generation, unsuppressed and hash-consistent.

The suppressions are `0x82631A30 -> 0x82950A98`, `0x828EA448 -> 0x82681198` and `0x83062950 -> 0x83060C30`. Suppression precedence passes for primary, dependency, fallback, September and consumer-merge routes. Corrected vector-wrapper mappings `0x83060A80 -> 0x83060C30` and `0x83062950 -> 0x83060CD8` are present.

All 66 reservations remain attached verbatim in the delta, effective map, machine reservation inventory and `reservation-inventory.md`. The HammerCombat-context mapping `[0x8229B488,0x8229B504) -> [0x8229B1B8,0x8229B234)` retains `internal-code-region-dependent`; neither function is named HammerCombat and the comparator regions remain internal non-functions.

Both physics candidates, all three held original-strong proposals and all 715 probable proposals remain excluded. They are not relabelled as rejected.

## Consumer and rollback

No existing consumer changed. The dedicated adapter defaults to the exact 15,299-pair Phase 2A map. Overlay use requires the explicit version plus exact decision, delta and effective-map paths and SHA-256 values. Missing, stale, tampered or unknown data refuses opt-in without fallback, and selected hashes are emitted in provenance. The compatibility exercise loaded 15,379 rows without mutating original artifacts.

Rollback is the default adapter command documented in `rollback.md`; it restores the exact pre-Phase-2E analysis selection without rewriting frozen evidence.

## Limitations and inherited blockers

This is analysis-only correspondence evidence, not source semantics, a canonical name map or runtime authorization. Reference text remains context. The six inherited Phase 2C blockers are unchanged. Historical ownership replay still requires `generated/default/fable2_recomp.136.cpp` SHA-256 `6053CC0EAC4636AA03AAA26581162B707C37E1B52BEE4C10F205D07C63EBDF59`; current bytes remain `D25E664A98833BF9433413336AC92A7376102A67049C0FF35F1270E6BDEB44CB`.

## Durable and exhaustive artifact identities

Committed owner decision: `docs/fable2-prototype-archaeology/phase2e/evidence/owner-decision.json`, 42203 bytes, `7905EDD55A1DDA53C7FDD1D36635FFC7E6315F1BA66F2CB88393A3E5F6F766BD`.

Committed approved delta: `docs/fable2-prototype-archaeology/phase2e/evidence/approved-overlay-delta.json`, 260564 bytes, `BD53722F709EB2BB287482DE09E2D6953EAD19DDA675E1B1C34DEBA55D2D52BC`.

Ignored effective map: `out/prototype-archaeology/phase2e/effective-map.json`, 8975363 bytes, `E3EE02E659ADCBD79823B3343A542505B45B8B902BAADD158A2A75D577E71663`.

| Repository-relative path | Bytes | SHA-256 |
| --- | ---: | --- |
| `out/prototype-archaeology/phase2e/selected-actions.json` | 50971 | `3EC1A1350B9DA3EA47E93B7B5140C05598F43C32F8DE26681E445CC5F6F112B4` |
| `out/prototype-archaeology/phase2e/effective-map.json` | 8975363 | `E3EE02E659ADCBD79823B3343A542505B45B8B902BAADD158A2A75D577E71663` |
| `out/prototype-archaeology/phase2e/overlay-application-receipt.json` | 1653 | `433FEAEF491AF0866E6764A0CF3CF6CDC70F26CAFDCD8FFA40EDAC706CA888D1` |
| `out/prototype-archaeology/phase2e/suppression-route-audit.json` | 1976 | `A9E6E32383519E02B36EA3A54B4B3B15E6E2AA5242F90F7BE4EB8BB350B53F58` |
| `out/prototype-archaeology/phase2e/reservation-inventory.json` | 35968 | `838E57DDEC1750F5B390FFA15140EB7EC2668C7D4459FE38CFE6980F5B224A44` |
| `out/prototype-archaeology/phase2e/exclusion-audit.json` | 145615 | `2B0907F00CBA2FF3BFF0ECC6937B12ED47402FCCDB32B65612391D2077E23120` |
| `out/prototype-archaeology/phase2e/dependency-injectivity-verification.json` | 655 | `782CEE71DDD3FC500AF834B7DF9097B457873C6A3A72C37CB2A038D9373C14E9` |
| `out/prototype-archaeology/phase2e/consumer-compatibility.json` | 1835 | `9E18C96664ED7B4AB5C3A44EB5CBA11852A1D1A62A9A4C1F459F8D4C93ACC9FB` |
| `out/prototype-archaeology/phase2e/rollback-verification.json` | 1627 | `38F21DE96F717438EF97CC82B52C3D1E66A7F7005D10D62E93B8132E53C71381` |
| `out/prototype-archaeology/phase2e/consistency-results.json` | 4939 | `F6E1DA511B683C69C7A3EA6470782FF56FE1441E6E68439384733C1ED599967F` |
| `out/prototype-archaeology/phase2e/test-results.json` | 40194 | `8A251F4378BA05B61AAA800AFF9FB7750B35EF3EA2CF1B912E13C36D727C27EF` |
| `out/prototype-archaeology/phase2e/replay-results.json` | 511 | `699F7FE1142B00A510E95EE1CCEEA42F72B4863CC4E8FC6519348EE11B003313` |
| `out/prototype-archaeology/phase2e/schema-results.json` | 1680 | `44DBF55B230F6A0E2D48F3CECAE87D826123890584C2DA6E3DE33B518785CB69` |
