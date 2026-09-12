# Phase 2D independent mapping review and adoption readiness

All decisions remain pending. This dossier is non-canonical and does not authorize adoption, naming, scripts, assets, manifests or runtime changes.

## Starting state and preservation

Fable2Recomp started clean on `fable2-prototype-archaeology-phase2c`, HEAD `f13ee49c94db48d979de1346b7f67d2d82257ea2`, tree `2fd80820bf7ce98099fac26ea256bb8d1c6a5982`, subject `docs: freeze Phase 2C bounded result`. Phase 2D was created directly from this commit after the read-only frozen verifier passed. SDK branch/HEAD/tree/remotes/status and all fifteen libmspack hashes matched the frozen pins.

All 30 protected Phase 2C artifacts, all committed Phase 2C bytes and closed upstream sources remain hash-identical. The 187 gates remain 181 complete and six blocked-with-evidence; all 39 fixture categories remain covered. Frozen arithmetic remains 15,299 - 3 + 86 = 15,382. Phase 2C phase_complete and canonical_adoption remain false.

## Review results

```json
{
  "blind_counts": {
    "different-target": 0,
    "no-candidate": 0,
    "tied": 0,
    "unique-same-target": 86
  },
  "challenge_totals": {
    "risk-or-failure": 118,
    "satisfied": 1602
  },
  "probable_dispositions": {
    "hold-for-additional-evidence": 715,
    "recommend-downgrade": 0,
    "recommend-human-approval": 0,
    "recommend-human-approval-with-reservation": 0,
    "recommend-rejection": 0
  },
  "simulations": {
    "all-recommended-including-former-probable": {
      "count": 15379,
      "delta_from_phase2a": 80,
      "delta_from_phase2c": -3
    },
    "former-probable-only": {
      "count": 15296,
      "delta_from_phase2a": -3,
      "delta_from_phase2c": -86
    },
    "frozen-phase2c-comparison": {
      "count": 15382,
      "delta_from_phase2a": 83,
      "delta_from_phase2c": 0
    },
    "unreserved": {
      "count": 15313,
      "delta_from_phase2a": 14,
      "delta_from_phase2c": -69
    },
    "unreserved-plus-reservations": {
      "count": 15379,
      "delta_from_phase2a": 80,
      "delta_from_phase2c": -3
    }
  },
  "strong_dispositions": {
    "hold-for-additional-evidence": 3,
    "recommend-downgrade": 0,
    "recommend-human-approval": 17,
    "recommend-human-approval-with-reservation": 66,
    "recommend-rejection": 0
  },
  "strong_intersections": {
    "closure": 68,
    "coverage": 11,
    "ghidra": 85,
    "historical-crash": 0,
    "indirect": 0,
    "ownership": 0,
    "renderer": 0
  }
}
```

Every one of 803 packets (86 strong, 715 probable and two physics candidates) contains a complete independent byte-backed profile, instruction comparison, references, CFG/field/return summaries, reciprocal candidates, dependencies, adversarial checks and terminal result. Matching covered all 46,179 donor and 46,180 TU1 .pdata functions; the target decisions were revealed only after the independent reconstruction was frozen. Shared low-level parsing and inherited donor selection are disclosed limits on independence.

No newly established incompatible mapping or complete-reference semantic contradiction was found in the 803 proposals. Two frozen strong proposals nevertheless contain unresolved indirect calls that the frozen direct-call gate did not discharge. Their exact matching bodies do not establish their dynamic callees. A third proposal has only common helper support and a non-distinctive reference; it remains plausible but held.

| Held original strong proposal | Exact reason |
| --- | --- |
| `0x82BC43E8 -> 0x82BC3FA8` | `bctrl` at donor `0x82BC4474` and TU1 `0x82BC4034` (+0x8C); TU1 target is loaded from writable global `0x83314BBC`. |
| `0x82E510E0 -> 0x82E515D0` | `bctrl` at donor `0x82E51120` and TU1 `0x82E51610` (+0x40); target is loaded through object +0 and slot +0x10. |
| `0x82FB6620 -> 0x82FB6C50` | `XBOX360 8,0,0,0` has two donor and two TU1 users; both mapped helpers also serve compatible wrapper `0x82FB6BE0`. Helper fan-in is 108 and 415 in each build. |

The early broad reference detector also exposed high-half register coincidences at 0x820B0000, 0x820C0000 and 0x820D0000. A one-instruction scratch value is not a complete native string-use proof; such rejected chains remain negative evidence in profiles and cannot manufacture semantic contradictions. This was corrected in Phase 2D without changing any frozen input.

Each strong packet has 20 explicit adversarial challenges and eleven leave-one-class-out counterfactuals. The independently recomputed Phase 2C direct-transfer policy is compared separately with the stricter Phase 2D indirect-flow gate. Mandatory canonicalization, boundary, CFG and role checks are conjunctive validity conditions. Callee/import identity remains one overlapping obligation.

## Support populations and overlap

| Population | Count | Unreserved | Reserved | Held | Downgraded | Rejected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| callee-only | 66 | 0 | 65 | 1 | 0 | 0 |
| callee-only-and-multi-reference | 5 | 0 | 5 | 0 | 0 | 0 |
| multi-reference | 17 | 11 | 5 | 1 | 0 | 0 |
| richer-and-multi-reference | 12 | 11 | 0 | 1 | 0 | 0 |
| richer-support | 20 | 17 | 1 | 2 | 0 | 0 |

The 66 callee-only and 20 richer-support populations are disjoint. The 17 multi-reference proposals overlap them by five and twelve respectively. Their counts must not be summed as independent mappings. Among the 66 callee-only packets, 15 have at least one helper distinctive within compatible callers and 51 have only common helpers; the 92 callsite obligations are fully enumerated. Sixty-five receive reservations and the common-reference case is held. Full identities, commonness measurements and exact memberships are in the packets and risk-strata artifact.

## Known cases

All three original suppressions are independently reproduced from complete donor/TU1 reference uses: `0x82631A30 -> 0x82950A98` (Navigator/Controlled), `0x828EA448 -> 0x82681198` (TROLL_FOOTSTEP/DESTROY_ENTITY), and `0x83062950 -> 0x83060C30` (__vspltb/__vcfsx). They remove semantic transport eligibility without erasing the closed Phase 2A row or disproving code reuse. Simulations bar suppressed seeds and pairs, including September routes.

Both same-name physics candidates remain hold-for-additional-evidence: `0x82631A30 -> 0x82630C30` and `0x829506B0 -> 0x82950A98`. All four 0x3C wrappers, immediate 0xA0 helpers, helper callees, callers, competing wrappers and access relationships are recorded. Atomic-counter relocation `0x83497084 -> 0x83497088` and unresolved helper/global correspondence are not justified by matching names.

HammerCombat callee `[0x8229B488,0x8229B504) -> [0x8229B1B8,0x8229B234)` is recommended with the internal-region reservation. The exact caller `[0x8229B308,0x8229B484) -> [0x8229B038,0x8229B1B4)` supplies object +8 and excludes equality with HammerCombat. Empty fallback semantics and inequality return are reproduced. Comparator regions `[0x8226DB80,0x8226DBD4)` and `[0x8226D7F8,0x8226D84C)` have 21 reachable byte-identical signed-byte lexical-comparison instructions and no .pdata ownership. They remain internal regions, and neither function is named HammerCombat.

## All probable proposals

All 715 were available, inspected, reconstructed and adversarially checked. Zero were promoted, downgraded or rejected; 715 remain held. No proposal appeared promotable under the published gates. Recovery used only retained Phase 2A seeds (generation 1), including bounded comparison of unowned call regions; no iterative proposal-derived seed expansion was used.

| Exclusive blocker combination | Proposals |
| --- | ---: |
| boundary-code-region-ambiguity+insufficient-independent-corroboration+trusted-callee-helper+unresolved-tail-call-indirect | 3 |
| boundary-code-region-ambiguity+low-entropy-common-evidence+trusted-callee-helper+unresolved-tail-call-indirect | 6 |
| boundary-code-region-ambiguity+trusted-callee-helper+unresolved-tail-call-indirect | 209 |
| insufficient-independent-corroboration | 22 |
| insufficient-independent-corroboration+trusted-callee-helper+unresolved-tail-call-indirect | 22 |
| low-entropy-common-evidence+trusted-callee-helper+unresolved-tail-call-indirect | 6 |
| trusted-callee-helper+unresolved-tail-call-indirect | 439 |
| unresolved-tail-call-indirect | 8 |

Overlapping blocker obligations (not additive):

```json
{
  "boundary-code-region-ambiguity": 218,
  "boundary-size": 0,
  "cfg-branch": 0,
  "competing-candidate": 0,
  "complete-reference-identity": 0,
  "field-parameter-return-role": 0,
  "global-injectivity": 0,
  "insufficient-independent-corroboration": 47,
  "low-entropy-common-evidence": 12,
  "neighbourhood": 0,
  "reciprocal-uniqueness": 0,
  "reference-definition-use": 0,
  "semantic-contradiction": 0,
  "trusted-callee-helper": 685,
  "trusted-caller": 0,
  "unresolved-tail-call-indirect": 693
}
```

## Proposed human batches

| Batch | Mappings | Cumulative simulated count |
| --- | ---: | ---: |
| B00-semantic-suppressions | 3 suppressions, zero additions | 15296 |
| B01-unreserved | 17 | 15313 |
| B02-multiple-references-reserved | 5 | 15318 |
| B03-richer-support-reserved | 0 | 15318 |
| B04-callee-only-reserved | 60 | 15378 |
| B05-internal-region-reserved | 1 | 15379 |
| B06-former-probable | 0 | 15379 |

All 91 decision rows remain pending. Batch IDs, addresses, exact proposal-set hashes, reservations and intersections are provided in the decision ledger and readable review guide. Empty batches are explicit and cannot authorize mappings.

## Verification and inherited blockers

Complete supported discovery: 302 tests, zero failures, errors or skips. Read-only domain checks: 19 passed. Deterministic replay: 3 stages passed. Local schemas: 21 Phase 2D documents and 58 earlier-phase documents passed. Injectivity, suppression precedence, dependency consistency, relative/output paths, explicit Git-delta allowlist and SDK preservation pass; all fifteen libmspack files remain bound.

The exact executed commands and domain results are in verification-results.json; complete test IDs are in test-results.json. Phase 2C verify-summary passed on the starting branch. At close-out its bytes, original terminal invariants and mapping freeze are checked without weakening branch guards or invoking closed writers. The Phase 2B generator remains branch-restricted. Historical ownership replay remains blocked; existing current ownership/coverage/indirect validations are separate passing checks.

```json
[
  {
    "id": "L.script-bank-parser-or-blocker",
    "reason": "Bounded inventory completed; validated proprietary bank-entry layout is unavailable in the existing supported parsers."
  },
  {
    "id": "L.game-GUI-startup-states",
    "reason": "Path categories are preserved, but a native Lua-state lifetime/namespace ownership chain is absent."
  },
  {
    "id": "L.retail-provenance",
    "reason": "Current-runtime script inventory is not an authenticated retail-disc bank and dependency inventory."
  },
  {
    "id": "M.complete-chain-or-blocker",
    "reason": "The native callback payload is proven, but helper/adapter, native state and corresponding TU1 registration obligations remain unresolved."
  },
  {
    "id": "validation.baseline-bound-ownership",
    "reason": "Exact historical generated/default/fable2_recomp.136.cpp bytes with SHA-256 6053CC0EAC4636AA03AAA26581162B707C37E1B52BEE4C10F205D07C63EBDF59 are absent; only three baseline-bound provenance fields differ."
  },
  {
    "id": "validation.all-existing-verifiers",
    "reason": "Current validators pass; exact historical ownership JSON replay remains blocked by the hash-bound generated input. The closed Phase 2B generator retains its branch guard and is not rebound."
  }
]
```

Required historical input remains `generated/default/fable2_recomp.136.cpp`, SHA-256 `6053CC0EAC4636AA03AAA26581162B707C37E1B52BEE4C10F205D07C63EBDF59`; current SHA-256 remains `D25E664A98833BF9433413336AC92A7376102A67049C0FF35F1270E6BDEB44CB`. It was not searched for, reconstructed, replaced or regenerated.

## Adoption boundary and rollback

The read-only consumer inventory identifies schemas, map/semantic tools, Ghidra analysis interfaces, closure/coverage joins and documentation. Later semantic suppression overlay adoption, mapping adoption, analysis aliases, canonical naming and runtime/generated changes are separate decisions. The rollback plan disables the new overlay and restores pre-adoption consumer hashes; frozen archaeology evidence is never rewritten. See adoption-plan.md.

No game launch, build, code generation, network operation, Lua execution, asset/binary modification, SDK modification, canonical adoption or human impersonation occurred. Only scoped local Phase 2D commits were made. Local line-ending attributes apply solely to new Phase 2D files; the frozen root attributes are untouched.

## Exact artifact bytes

| Repository-relative path | Bytes | SHA-256 |
| --- | ---: | --- |
| `out/prototype-archaeology/phase2d/adoption-simulations.json` | 3503663 | `C52D14B0C2A7D528C9DBB28562E502501FE3CCB157DFC7E6D6E8CB70BA0CD8C7` |
| `out/prototype-archaeology/phase2d/adversarial-challenge.json` | 4693971 | `3C145919773F455F20110AC64BCA2A17C262E56E3B9EC3CFC211A4AC46853EFB` |
| `out/prototype-archaeology/phase2d/blind-input.json` | 10833 | `2F041FB85C2CD7746970EAD4ACB1468D09E29C475B501554DA7F54E2E1219112` |
| `out/prototype-archaeology/phase2d/blind-results.json` | 158863 | `30F75A339946E8CEE040D0793E295783347B356C1B018582DE3D3941D6086A12` |
| `out/prototype-archaeology/phase2d/dependency-seeds.json` | 1071548 | `9B2DF46CC12393B77F8B89E0F3554AA72693BF99BBC81C8DFA6B5093EFEDB82A` |
| `out/prototype-archaeology/phase2d/future-consumers.json` | 76448 | `4427C9FAAE4AD3F6887CDDFABEFBF603EF72CA05D8DB637C5F77009894A81A35` |
| `out/prototype-archaeology/phase2d/known-cases.json` | 1418058 | `4BE9DF15353F01C1253A81EB0584140802DDF5FA8EA6D0511D1BFBEB2CBF45EF` |
| `out/prototype-archaeology/phase2d/packets.json` | 51654630 | `6E07A0FC1BF1BA909A61C33266F81CB04D8A2F14377149DF4B9625DA708948CF` |
| `out/prototype-archaeology/phase2d/probable-blockers.json` | 1664532 | `76445776353B77E1CC8419B62D40D1DC779130D873107EC5A22AEF732F121CF2` |
| `out/prototype-archaeology/phase2d/profiles.json` | 374181628 | `647F122BE55D6066D8D84963C4D9329AAA0B2424DFC43104ED8A908FEA2D70D8` |
| `out/prototype-archaeology/phase2d/reconstruction-freeze.json` | 843 | `5DC4EC41B058EB747D9C415CAB95337C86FC66BD4AB678C76D4708EF945D5D0A` |
| `out/prototype-archaeology/phase2d/replay-results.json` | 489 | `DC33375212C6DD72CDCCC7ABF50D0638B2A77395875E2D25213EED936B006B9D` |
| `out/prototype-archaeology/phase2d/review-index.json` | 2674393 | `651D8A77CC170B0DD0158D6BFE13DEC927FAA4293E9AA3488209E5E890EA6EC7` |
| `out/prototype-archaeology/phase2d/risk-strata-and-batches.json` | 7008 | `AA628D89C94543A78D59D23CCDC0C37CE30C678E1515D4EBF7B48E1DC95101FE` |
| `out/prototype-archaeology/phase2d/schema-results.json` | 1578 | `F975324F3709BC5871A4C19969D90F8E63B652EDEF5C233DBC39A9F59A7D729D` |
| `out/prototype-archaeology/phase2d/test-results.json` | 39375 | `91ADC2504A2AE888E9885F0330B9CE2976E161D6B369F61ADF22E8BCC1B5B8E0` |
| `out/prototype-archaeology/phase2d/verification-results.json` | 6169 | `DE7C13408C377F222AD8FEE680FFBBDEAA987EDF82C0E7E0339E3EEBAF59EAB4` |
| `docs/fable2-prototype-archaeology/phase2d/evidence/source-pins.json` | 341305 | `D08AB43ACE00652D56D78592C80DA87C53760D6026DB6FD08013DFDE36513F6C` |
| `docs/fable2-prototype-archaeology/phase2d/evidence/review-summary.json` | 12589 | `2DFF44302FC8CCAAA8FD1E7C4A912738768180CD0ED8344B398E970A11701BA2` |
| `docs/fable2-prototype-archaeology/phase2d/evidence/human-decision-ledger.json` | 217799 | `442159DFE7F6F0D7D23DEF2367AEAC2DAE9B4467619049C5F456F437DE433B15` |
