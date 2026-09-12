# Phase 2C static archaeology checkpoint

**Phase 2C is not complete.** This is a reproducible provisional evidence layer; no canonical adoption is authorized.

Build 23 and TU1 remain very closely related, but are not byte-identical semantic layouts. One semantic collision does not invalidate all 15,299 Phase 2A mappings. Phase 2A exact-image precision was a control result, not measured cross-build precision.

The bounded audit retains 15296 closed pairs and suppresses 3. The provisional effective view adds 86 policy-strong proposals, giving 15382 pairs (delta +83).

A `reviewed-strong-proposal` is a machine policy disposition with explicit `not-human-reviewed` state. It is not an accepted Phase 2A mapping or a source-lineage claim.

## Exact reconciled counts

```json
{
  "boundary_classes": {
    "inline": 0,
    "merge": 0,
    "outline": 0,
    "shared-body": 51,
    "split": 0,
    "tail": 0,
    "thunk": 0,
    "unresolved-boundary": 662
  },
  "effective_map": {
    "additions": 86,
    "closed": 15299,
    "delta": 83,
    "effective": 15382,
    "suppressed_or_review_excluded": 3
  },
  "intersections": {
    "closure": 4781,
    "coverage": 2188,
    "ghidra": 12959,
    "historical-crash": 0,
    "indirect": 0,
    "ownership": 21,
    "renderer": 1
  },
  "mapping_review_grade_presence": {
    "ambiguous": 114,
    "candidate": 1858,
    "rejected-proposal": 49,
    "reviewed-probable-proposal": 1546,
    "reviewed-strong-proposal": 119
  },
  "mapping_review_subsystem_grade_presence": {
    "ai-navigation:candidate": 5,
    "ai-navigation:reviewed-probable-proposal": 5,
    "audio:reviewed-probable-proposal": 7,
    "combat:ambiguous": 2,
    "combat:candidate": 132,
    "combat:reviewed-probable-proposal": 46,
    "combat:reviewed-strong-proposal": 3,
    "debug:reviewed-probable-proposal": 4,
    "physics:candidate": 10,
    "physics:reviewed-probable-proposal": 8,
    "renderer:candidate": 18,
    "renderer:reviewed-probable-proposal": 37,
    "unassigned:ambiguous": 112,
    "unassigned:candidate": 1693,
    "unassigned:rejected-proposal": 49,
    "unassigned:reviewed-probable-proposal": 1439,
    "unassigned:reviewed-strong-proposal": 116
  },
  "original_evidence_strata": {
    "cfg-and-branch-shape": 23,
    "cfg-and-branch-shape+data-content-anchor": 1,
    "cfg-and-branch-shape+direct-call-topology": 54,
    "cfg-and-branch-shape+local-address-delta-neighbourhood": 6251,
    "cfg-and-branch-shape+local-address-delta-neighbourhood+data-content-anchor": 26,
    "cfg-and-branch-shape+local-address-delta-neighbourhood+direct-call-topology": 8622,
    "cfg-and-branch-shape+local-address-delta-neighbourhood+direct-call-topology+data-content-anchor": 67,
    "cfg-and-branch-shape+local-address-delta-neighbourhood+string-content-anchor+data-content-anchor": 1,
    "cfg-and-branch-shape+local-ordering-neighbourhood": 68,
    "cfg-and-branch-shape+local-ordering-neighbourhood+direct-call-topology": 184,
    "cfg-and-branch-shape+local-ordering-neighbourhood+direct-call-topology+data-content-anchor": 2
  },
  "preservation": {
    "portability": {
      "native-dependent": 18,
      "unknown": 182
    },
    "records": 200
  },
  "proposal_intersections": {
    "closure": 68,
    "coverage": 11,
    "ghidra": 85,
    "historical-crash": 0,
    "indirect": 0,
    "ownership": 0,
    "renderer": 0
  },
  "reference_candidates": {
    "processed_contexts": 21350,
    "processed_donor_functions": 24455,
    "proposal_grades": {
      "ambiguous": 145,
      "candidate": 1780,
      "rejected-proposal": 35,
      "reviewed-probable-proposal": 715,
      "reviewed-strong-proposal": 86
    },
    "reciprocal_donor_population": 46179,
    "reciprocal_target_population": 46180,
    "results": {
      "multiple-candidates": 116,
      "no-candidate": 17711,
      "one-candidate": 3523
    }
  },
  "registration_calls": {
    "calls_with_complete_name_and_callback": 2647,
    "constructor_calls": 2662,
    "proven_tu1_command_chains": 0,
    "shape_candidates": 206
  },
  "registration_inspected": 6,
  "registration_recognizer_candidates": {
    "build-23.12.02.0330": 69,
    "canonical-tu1": 69,
    "sep-2008": 68
  },
  "registration_structures": 1,
  "scripts": {
    "identical_executable_structure": 54,
    "inventoried": 160,
    "paired": 54,
    "parsed": 108
  },
  "semantic_v2": {
    "newly_joined": 118,
    "records": 51657,
    "september_corroborated": 0,
    "september_routed": 0,
    "statuses": {
      "filtered-corroborated-context": 112,
      "joined-target-unconfirmed": 4,
      "mapping-blocked": 51537,
      "target-corroborated-context": 4
    }
  },
  "september": {
    "anchor_classifications": {},
    "audited": 9600,
    "counterfactually_dependent_on_partial_data": 0,
    "data_anchor_supported_pairs": 0,
    "data_only_non_cfg": 0,
    "data_pairs_retained_independently": 0,
    "dispositions": {
      "retained-independent-evidence": 9600
    },
    "interior_pointer_anchor_pairs": 0,
    "original_status": {
      "accepted-exact-unique": 1847,
      "accepted-normalized-corroborated": 7753
    }
  },
  "september_boundary_review": 33,
  "september_two_hop_function_routes": 9284,
  "strong_proposal_evidence_combinations": {
    "trusted-mapped-callee": 66,
    "trusted-mapped-callee+trusted-mapped-caller": 2,
    "trusted-mapped-callee+trusted-mapped-caller+trusted-two-sided-exact-delta-neighbourhood": 1,
    "trusted-mapped-callee+trusted-two-sided-exact-delta-neighbourhood": 16,
    "trusted-mapped-caller+trusted-two-sided-exact-delta-neighbourhood": 1
  },
  "strong_proposals_with_multiple_reference_identities": 17,
  "trust_audit": {
    "anchor_classifications": {
      "full-string-match": 9,
      "non-string-bounded-window": 103,
      "same-address-different-full-string": 1
    },
    "audited": 15299,
    "counterfactually_dependent_on_partial_data": 1,
    "data_anchor_supported_pairs": 97,
    "data_only_non_cfg": 1,
    "data_pairs_retained_independently": 96,
    "dispositions": {
      "retained-independent-evidence": 15296,
      "suppressed-semantic-collision": 3
    },
    "interior_pointer_anchor_pairs": 1,
    "original_status": {
      "accepted-exact-unique": 2779,
      "accepted-normalized-corroborated": 12520
    }
  },
  "types_globals": {
    "global_contexts": 2479,
    "new_global_contexts": 10,
    "pointer_runs": 4939,
    "proven_global_objects": 0,
    "proven_vtables": 0,
    "type_contexts": 425
  }
}
```

Anchor-classification counts count windows; 97 distinct accepted pairs carry 113 shared windows. Full-string comparison requires terminated content; zero-filled storage is not automatically an empty string. Only a proven byte-read context may tokenize an empty terminator.

## Suppressions

```json
[
  {
    "donor": "0x82631A30",
    "target": "0x82950A98",
    "audit_id": "T-03503"
  },
  {
    "donor": "0x828EA448",
    "target": "0x82681198",
    "audit_id": "T-05080"
  },
  {
    "donor": "0x83062950",
    "target": "0x83060C30",
    "audit_id": "T-13251"
  }
]
```

The conflicts are Navigator versus Controlled, TROLL_FOOTSTEP versus DESTROY_ENTITY, and __vspltb(%s, %d) versus __vcfsx(%s, %d). Suppression bars semantic transport; it does not conclusively disprove generic code/body reuse.

## Known-case dispositions

```json
[
  {
    "donor": "0x8229B488",
    "target": "0x8229B1B8",
    "grade": "reviewed-strong-proposal",
    "generation": 1
  },
  {
    "donor": "0x82631A30",
    "target": "0x82630C30",
    "grade": "candidate",
    "generation": 1
  },
  {
    "donor": "0x829506B0",
    "target": "0x82950A98",
    "grade": "candidate",
    "generation": 1
  }
]
```

All four physics wrappers are exact 0x3C .pdata intervals. The donor Navigator wrapper is [0x82631A30,0x82631A6C), TU1 Navigator [0x82630C30,0x82630C6C), donor Controlled [0x829506B0,0x829506EC), TU1 Controlled [0x82950A98,0x82950AD4). Their r4 literal role and r5=-1 agree; this alone is insufficient independent correspondence support.

HammerCombat: exact caller [0x8229B308,0x8229B484) -> [0x8229B038,0x8229B1B4). The 0x7C callee compares string-like content and returns inequality. The caller passes object offset +8, returns zero when equal to HammerCombat, and otherwise evaluates remaining field-dependent logic. This is an exclusion-guard context, not a function named HammerCombat.

The comparator regions [0x8226DB80,0x8226DBD4) and [0x8226D7F8,0x8226D84C) have 21 reachable instructions and identical bytes. Neither has .pdata ownership or an independent .pdata entry. They remain internal code regions.

## Limits and unfinished completion gates

- The transport audit uses bounded instruction recovery. It does not prove complete semantic equivalence of every retained function.
- Physics same-name pairs remain candidates because the strict matcher has no independent trusted caller/callee or two-sided exact-delta support for them. Their immediate helpers also contain a changed global reference and different call destinations.
- Boundary reconnaissance retains exact shared windows and all 33 September boundary-review rows, but does not resolve split/merge/outline/inline/thunk/tail lineage. The two unmatched primary functions remain unexplained at function level.
- One native four-byte callback-payload construction chain is demonstrated. Its narrow recognizer returns 206 shape candidates across three builds, each retaining unverified callee/state obligations. No complete frozen TU1 registration chain or callable command is claimed.
- RTTI/type names and pointer runs do not prove constructors, vtables or stable global objects. This pass supplies candidates and negative gates, not a complete typed reconstruction.
- No validated script-bank entry parser or distinct native Lua-state ownership chain was recovered. Loose standard Lua 5.1 chunks were parsed without execution; current-runtime file provenance is separate from authenticated retail-disc provenance.
- The requested full compiler-transformation recovery, exhaustive feature-ablation audit, broader mapping features, and complete required fixture matrix are not complete. This checkpoint must not be represented as completed Phase 2C.

## Native registration reconnaissance

CONFIRMED: build-23 callsite 0x82484E58 passes SetUseFreeCamera at 0x820BA1FC in r4 and callback 0x82482298 in r5 to 0x82309378. The helper constructs a four-byte callback payload and adapter closure, then supplies the name to a key consumer. This is an interprocedural runtime layout, which the old adjacent-pointer recognizer did not cover.

The callback [0x82482298,0x824822A4) stores the low byte of r3 at 0x83496BE9 and returns. It has no .pdata owner. The narrow constructor recognizer retains every callee, adapter and state/namespace obligation; it does not establish callable TU1 commands. Full evidence is in registration.json.

## Unfiltered TU1-corroborated contexts

- `S-12BC57D54F752C90D2876FE7`: `Virtual filesystem can not be null` — corresponding literal argument and trusted callee at TU1 `0x82C02CD0`. This is a contextual role, not a function name.
- `S-2446137A06BE22408008696B`: `Invalid table index` — corresponding literal argument and trusted callee at TU1 `0x82BC3FA8`. This is a contextual role, not a function name.
- `S-6F63464AA6C04DC23857B40D`: `MaxComboAnimationSpeedMultiplier` — corresponding literal argument and trusted callee at TU1 `0x82763A30`. This is a contextual role, not a function name.
- `S-FCEF3DCAA6D1D5FB2EF8AB8F`: `HammerCombat` — corresponding literal argument and trusted callee at TU1 `0x8229B038`. This is a contextual role, not a function name.

The historical ownership reconstruction fails with `FAIL: stale manifest`; the old plan is preserved. Current ledger/plan validation is separate. See verification.md for exact inputs and results.


## Exact artifact bytes

| Path | Bytes | SHA-256 |
| --- | ---: | --- |
| `out/prototype-archaeology/phase2c/boundaries.json` | 636862 | `4BFF685E8BED00E6412CC1E62A3E634C34BCA4EACE1544112F8239A03358B257` |
| `out/prototype-archaeology/phase2c/effective-map.json` | 3657026 | `0C801C9AC0DB10FDA1FC9A36A9D88488C1200311F1597CCFA749910E3A9BAD00` |
| `out/prototype-archaeology/phase2c/intersections.json` | 6262669 | `CACB81039B9B7D096E81A64FAEDEC7D245561D24967924F9848D62678C1FAD5C` |
| `out/prototype-archaeology/phase2c/known-cases.json` | 47797 | `F3A09E42401BCA65A5064526A37D4C5526B31C07032DBF212CAEA17377F43CD0` |
| `out/prototype-archaeology/phase2c/mapping-freeze.json` | 1337 | `A438B7FC652EA12EE5D0393495785BD2E9F5720313B651579058296409C3EF15` |
| `out/prototype-archaeology/phase2c/preservation.json` | 709919 | `BB108D03C92D003E5A96983FE36124EAAA5769593852566D2940C6F666C9FBE1` |
| `out/prototype-archaeology/phase2c/reference-candidates.json` | 21154445 | `A248E25E3542F6A2A51066625D92D5F1ADAE3A30BC2D03AA9BAF9F9CE3D999CE` |
| `out/prototype-archaeology/phase2c/registration.json` | 4946960 | `0D65F679CB2262CD96EE9BB2D390735E5B22CF79BE664260D2720688A2645E75` |
| `out/prototype-archaeology/phase2c/review.json` | 7859 | `50B5FA8F70E0799E514966D5BD4A0EE94087071F4077F40E83DD66D70684BF73` |
| `out/prototype-archaeology/phase2c/scripts.json` | 683313 | `43F5DBC55033333144461BB5FD182BDB2A447BD797F2FBDA4F83E38151352E96` |
| `out/prototype-archaeology/phase2c/semantic-v2.json` | 23348436 | `171AE06191CB8A91991C5119BDA84BFB220C1F7AAAD0D3A398D2300AC855374B` |
| `out/prototype-archaeology/phase2c/september-pairs.json` | 94890858 | `C3ED4ACA5613487F2DC3BF28D19B147801AAA8F4FB9ECEB17613399A48074186` |
| `out/prototype-archaeology/phase2c/trust-audit.json` | 11230700 | `C21DD1BA0C4D4EB6701657A709D0891D44B761DDAB220143142ACFB1ED3242B0` |
| `out/prototype-archaeology/phase2c/types-globals.json` | 4376285 | `7D5D346B07A5AE6F679B8C59926CE23E0FE7F1CD6A740D94BEF4485B94CCEB53` |

Closed phases and SDK inputs are rehashed before every analysis command. The mapping freeze is checked before and after semantic analysis. All analytical outputs omit the clock and current HEAD. Exact commands are in README.md.

Neither game was executed. No build, codegen, runtime, renderer, manifest, generated-code, canonical naming, binary modification, push, fetch, pull, merge, tag, PR, upload or release operation was performed.
