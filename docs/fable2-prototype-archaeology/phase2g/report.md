# Phase 2G high-value native semantic proof report

## Outcome

The exact Phase 2F branch, commit, tree, subject, five-commit sequence, ten trust roots, 32 ignored artifacts, 51,657 terminal lanes, overlay/default selections, 83 noncanonical additions, 66 reservations, three suppressions, exclusions, propagation flags, six blockers, remotes, ReXGlue state and fifteen libmspack hashes matched before branching. The same identities are revalidated fail-closed by every Phase 2G analytical invocation.

| Packet | Primary disposition | Mapping | Reservation | Contextual label |
|---|---|---|---|---|
| A | `independently-corroborated-role` | `unchanged` | retained: `internal-code-region-dependent` | provisional: byte-state query with HammerCombat equality exclusion guard |
| B | `behaviorally-corresponding-role-reserved` | `unchanged` | retained: `single-independent-support-class` | provisional: keyed oxygen-field load plus 32-bit current-from-maximum initialization |
| C | `independently-corroborated-role` | `review-triggered` | retained: `single-independent-support-class` | human-review candidate: conditional keyed reward/world-map field materializer |

All canonical-name dispositions are `not-authorized`.

## Packet A — HammerCombat exclusion guard

The donor owner `[0x8229B308,0x8229B484)` and TU1 owner `[0x8229B038,0x8229B1B4)` are complete 0x17C-byte, 95-instruction `.pdata` bodies and are byte-identical (SHA-256 `7DC8302D7AFF26667F1C4C429DC837D7874A00B2F26231B19F5E3389C3B0B240`). That equivalence and the `HammerCombat` `r4` reference were consumed by Phase 2A.

The reserved donor/TU1 callees `[0x8229B488,0x8229B504)` and `[0x8229B1B8,0x8229B234)` are 0x7C bytes. Only the relocated empty-string low half and comparator branch differ. They read a nullable 32-bit guest-pointer slot from `r3`; a non-null slot leads to another 32-bit byte-string pointer, while null selects the proven empty strings at `0x82000CA4`/`0x82000CA0`. The signed-byte comparator returns -1/0/1; the callee normalizes this to exactly zero for equality and one for inequality. This callee is generic and is not named `HammerCombat`.

The owner passes `object+8` in `r3` and `HammerCombat` in `r4`. Equality returns zero, so the first branch is an exclusion guard. Inequality reads `object+4`, tests bit 0 of nested byte `+0x24`, then uses either a selector byte at `+0x18` or a lower-bound search over 8-byte records between nested `+0x48/+0x4C` for signed key 24. It follows the selected record's `+4` pointer and returns byte `+0x3C`; failure paths return zero. The result is byte-valued, not proven strict Boolean.

The comparator intervals `[0x8226DB80,0x8226DBD4)` and `[0x8226D7F8,0x8226D84C)` are byte-identical 21-instruction internal regions (SHA-256 `75D59403DCA922941AF9DE2C4FCD6ACCC10FC50F291BBB78FC2BD047BB4DBD5E`) with no `.pdata` owner. They remain internal regions.

Independent target-native evidence comes from TU1 callers, treated as one consumer family. At `0x8285CB30`, the owner result is immediately `stb` to the same `r26+0x24` at `0x8285CB38`; a neighboring virtual result goes to `+0x25`. At `0x822757A4`, the low byte of the owner result is compared with cached `r31+0x24`, and mismatch invokes indirect slot `+0x64`. These target-only def-use facts were absent from the mapping gates. Donor mirrors, body equivalence, the literal, callee and comparator remain consumed or correlated.

## Packet B — oxygen fields

Donor `[0x82406F98,0x82407030)` and TU1 `[0x82405868,0x82405900)` are complete 0x98-byte, 38-instruction bodies. Thirty-one words match and seven changes are relocated calls/literal lows; canonical SHA-256 is `04BAAB6EA6005344343106826998B73AD4F14A296012A1DB390D266A8955CF19`.

Both preserve `r3` as object and `r4` as nullable source/context, call an attachment helper with `r3=lwz object+4,r4=object`, then conditionally call the keyed helper with `r3=context,r4=complete key start,r5=field address`. The helper hashes the NUL-terminated key from seed `0x811C9DC5` with prime `0x01000193`, performs a nullable lookup, copies one 32-bit word only on success, and returns 1/0. Finally the owner unconditionally copies the word at `+0x38` to `+0x34`. No stable owner return is constructed.

| Key/context | Donor instruction | TU1 instruction | Offset | Width | Operation | Evidence class |
|---|---|---|---:|---:|---|---|
| `MaxOxygen` | `0x82406FD8` | `0x824058A8` | `+0x38` | 4 | conditional keyed word write | mapping-consumed |
| `OxygenConsumptionRate` | `0x82406FEC` | `0x824058BC` | `+0x3C` | 4 | conditional keyed word write | mapping-consumed |
| `OxygenRecoveryRate` | `0x82407000` | `0x824058D0` | `+0x40` | 4 | conditional keyed word write | mapping-consumed |
| maximum-to-shadow copy | `0x82407004/08` | `0x824058D4/D8` | `+0x38 -> +0x34` | 4 | unconditional copy | mapping-consumed |

The words are not proven integer or float. There is no time, arithmetic, clamping or depletion/recovery state transition. The code is keyed load/deserialization-style population plus initialization, not registration, outbound serialization or runtime oxygen logic. The complete `.pdata` scan found no direct owner callers; indirect ownership and downstream consumption remain unresolved. The adjacent same-key bodies use a different field-visitor topology, proving that identical strings do not establish identical roles. No material independent positive vote was found.

## Packet C — reward and world-map fields

Donor `[0x825240E8,0x82524188)` and TU1 `[0x82522C10,0x82522CB0)` are complete 160-byte, 40-instruction bodies. Only three string lows and six branches relocate; canonical SHA-256 is `D67ADBEEC8AD31A0F02EA0043912AB5072E92EECA363F3C44F26C45153C7EADE`.

Both copy two source-handle words from `r4+0/+4` to destination `r3+4/+8`, branch on the first copied word, and on the populated path resolve that two-word handle. Two keyed scalar lookups return a word or zero; a keyed Boolean lookup normalizes a found word to 0/1. Stores are:

| Key | Donor actual consumer/store | TU1 actual consumer/store | Offset | Width | Meaning proved |
|---|---|---|---:|---:|---|
| `RewardRenown` | `0x82524134/38` | `0x82522C5C/60` | `+0x20` | 4 | opaque keyed scalar |
| `RewardMoney` | `0x82524150/54` | `0x82522C78/7C` | `+0x24` | 4 | opaque keyed scalar |
| `AppearOnWorldMap` | `0x82524168/6C` | `0x82522C90/94` | `+0x4D` | 1 | normalized Boolean-like byte |

Zero source handles skip the stores; a present source with missing keys supplies zero/false. Return residue differs by path and both direct callers ignore it.

The independent TU1 caller `[0x825237C8,0x82524454)` revisits the same destination fields through distinct visitor helpers: `+0x20` at `0x82523A50`, `+0x24` at `0x82523A8C`, and `+0x4D` at `0x82523CFC`. This separately owned field-address data flow is one independent target-native consumer vote. The visitors are highly generic; direction remains unresolved. The smaller TU1 caller allocates 0x9C bytes, populates an object and ignores the owner return, supporting a population context but no constructor or type identity.

Four terminals reconcile to three genuine keys. `S-26C37A0D8DC5C81610D44E94` (`SetObjectiveTag`) is a rejected donor-only high-half alias: H1 reads none of `r5/r6/r7`, and TU1 `0x820C0000` is interior to different text. Phase 2F also calls H1 a `literal-consumer-callee` for the reward keys, but H1 only resolves the handle; the subsequent scalar helper receives the key in `r4`. These are material semantic-attribution contradictions, not owner-body conflicts. They trigger review without mapping mutation.

The code materializes property fields. It does not register descriptors, grant rewards, perform reward arithmetic, construct map markers, update visibility, prove serialization direction, or identify a complete quest object.

## Cross-packet and adversarial conclusions

Packets B and C both use complete keys, the `0x811C9DC5` key transform and generic nullable property access, but their helper topology differs. B directly supplies `(context,key,&field)`; C resolves a handle and uses scalar-return/Boolean-return helpers, while its alternate caller visits field addresses. This is generic property/reflection machinery with Fable-specific key context, not independent mapping support shared between packets.

Synthetic controls reject prefix, interior, empty, writable, unterminated and circular support. Same-string/different-role and compatible-body/incompatible-caller fixtures quarantine the semantic claim. The real suppressions remain `0x82631A30 -> 0x82950A98` (`Navigator`/`Controlled`), `0x828EA448 -> 0x82681198` (`TROLL_FOOTSTEP`/`DESTROY_ENTITY`) and `0x83062950 -> 0x83060C30` (`__vspltb`/`__vcfsx`); corrected route `0x83062950 -> 0x83060CD8` remains separate. Both physics candidates, three held strong mappings and all 715 probable mappings remain excluded.

## Evidence independence and limitations

The exhaustive ledger contains each observation once. Owner bodies, strings, canonicalized XREFs, approved helper pairs and duplicate populations are mapping-consumed or correlated. Only A's TU1 byte-result consumer family and C's distinct TU1 field-visitor family are positive independent votes. B's no-direct-caller finding is independent but non-material. Packet C's two attribution failures are contradictory. Object identities, scalar types, visitor direction, runtime gameplay roles and indirect ownership remain unresolved.

## Verification and artifact envelope

The close-out verifier checks schemas, deterministic replay, report/summary/validation/actual bytes, repository-relative paths, output confinement, the exact Git delta, `git diff --check`, all supported tests, the Phase 2F envelope, default/overlay isolation, exclusions, blockers, ReXGlue/remotes/index and fifteen libmspack identities. The exact ignored-artifact table is inserted below at close-out.

Complete supported discovery passed 408 tests with zero failures, errors or skips. Before branching, the documented Phase 2F source check, semantic audit, verifier, Git audit and `git diff --check` all passed. On Phase 2G, `Fable2NativeProof.py --check`, the 16-document schema pass, receipt replay, the three-way verifier and the Git/SDK audit are the exact close-out commands shown in `README.md`.

| Ignored artifact | Bytes | SHA-256 |
|---|---:|---|
| `out/prototype-archaeology/phase2g/consumed-evidence/independence-ledger.json` | 27016 | `7FB8EAF55189600EE3CEA2134EC58D9B19F1E3CAAAF7AB86967B848859CF9EE8` |
| `out/prototype-archaeology/phase2g/expanded-function-scope.json` | 13628 | `41D9AACCC5145271EF60A56B6DBD5AEC1A62C0CBADEDB58279F463523E975885` |
| `out/prototype-archaeology/phase2g/hammercombat/native-proof-packet.json` | 41276 | `3D0BEF602EE24E045C39B9CE4C4D75B50B40DEA1E4DEA9893659F3F0D921557F` |
| `out/prototype-archaeology/phase2g/negative-controls/results.json` | 12160 | `1875411154B79AFE651DA215D958D1C4FC52B5EF2724479772C7A5FF9087D52E` |
| `out/prototype-archaeology/phase2g/oxygen/native-proof-packet.json` | 58393 | `E80632572F17C376ADED14F5AB1218034F4C2FCCE78F077B7F2E69008C42CB56` |
| `out/prototype-archaeology/phase2g/receipts/checks.json` | 1702 | `E66C05E6A3EAFBE8105DBE2DA664AE6FDD0707A51AB28BFFCDE339D9725C111F` |
| `out/prototype-archaeology/phase2g/receipts/consistency.json` | 1859 | `286020C8CD39837DFB8F91AF5E9F43BE3D9E9DDE19E651EF4DE318218E874E1B` |
| `out/prototype-archaeology/phase2g/receipts/replay.json` | 1950 | `BFFA2FC074A8D520A4C6BD8359B42A03C91BF33D773910F7345F41D3FB1F3C9F` |
| `out/prototype-archaeology/phase2g/receipts/schemas.json` | 1532 | `2E33A47C8091E56328BD921B21EC7EA6B9CA7060D90868B08AA03C57334C9643` |
| `out/prototype-archaeology/phase2g/receipts/tests.json` | 1552 | `BA411A44A3E09BE2A65010AB7E7772C96A37B3E2AC8E2BFC29F093AF21FC3245` |
| `out/prototype-archaeology/phase2g/review-selection.json` | 11393 | `775A9DF6CC53549446DAA3B46645DEFCCA3E666ACC8C42B249B5BE55AEAAFC06` |
| `out/prototype-archaeology/phase2g/shared-helper/property-pattern.json` | 10691 | `588B54584FB86A61AFB9ED6BF836762B2CA581B6832AA7A830BD5B1BB0E418AB` |
| `out/prototype-archaeology/phase2g/world-map-reward/native-proof-packet.json` | 95473 | `F54BAFD8DCD8C834A0C46FE3DFA745B5CBE1C698852783E15B1CB40D87995C00` |
