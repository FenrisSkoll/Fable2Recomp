# Prototype archaeology Phase 2B — static semantic evidence

Generated report; regenerate with `python tools/Fable2PrototypeSemantics.py generate`.

## Result and interpretation

**CONFIRMED:** 0 semantic associations satisfy this version's full acceptance policy. This is a bounded static-analysis result, not proof that the binaries contain no recoverable semantics.

The 15,299 Phase 2A binary correspondences are **not 15,299 semantic names**. Their 2,779 exact and 12,520 normalized acceptances remain closed and unchanged. September's 9,600 secondary mappings are not a semantic-accuracy measurement. The closed artifacts retain that secondary result as aggregate validation, not an exhaustive reusable pair index; this pipeline therefore reports September native evidence without inventing secondary joins. July is only an exact-image alias/control.

Community observations are unverified live-Lua-environment reports with unknown executable version. Their spelling, namespace headers and line provenance are candidate material, never native callback proof.

## Exact identities

Phase 2A close-out commit: `6ce54cbdcaa9fef23c6cd13e86fe46d3783cf3fd`; tree: `774c4f401bd44f8de1ea8f95c7344988ad12773c`.

Phase 2A input bundle: `DA77AF8D9345C684F81FDD342CDB1E95E48CC826A374D783EEC561F1EDE42B2F`.

Source inventory SHA-256: `4B3165E637A56A7FF2C0F06F78281D1FDF033A85CB36F8A360B8B8F8134890F1`. [Source pins](evidence/semantic-source-pins.json) bind every input's relative path, size, hash, available schema/producer metadata, collection counts, initial repository states and the pre-existing SDK modification hashes. [Validation](evidence/semantic-validation.json) binds implementation and exhaustive output bytes.

Preferred donor container: `0686A9F292A3F6777BEB6E8D4924F96247D1E8E3E2370323572F797E6637A4AA`; initialized executable fingerprint: `AE15F6D9AF8C76B3643A0CB5EF7B108E686794250F6822C2A71C78FE3D0BE956`.

TU1 post-patch image: `BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00`; initialized executable fingerprint: `5C8B78B84C93028D166E3DF347206E6642BA40BF374AD1AF8D958B2211320357`.

## Reconciled counts

Counts below are generated from the actual terminal index. Category/source totals overlap when an anchor has multiple provenance records. An association is one anchor/build/containing-function context (or one no-XREF terminal); callback-descriptor contexts are separate. Instruction references and direct data slots are different evidence kinds. Quarantined table records are not structurally proven registrations. Blocked-by-status counts overlap terminal grades; they are not additional associations.

```json
{
  "accepted": 0,
  "accepted_by_subsystem": {},
  "accepted_mapping_status": {},
  "accepted_problem_intersections": {
    "closure": 0,
    "coverage": 0,
    "ghidra": 0,
    "historical-crash": 0,
    "indirect": 0,
    "ownership": 0,
    "renderer": 0
  },
  "accepted_with_september_pair_corroboration": 0,
  "all_problem_intersections": {
    "closure": 3,
    "coverage": 2,
    "ghidra": 4,
    "historical-crash": 0,
    "indirect": 0,
    "ownership": 0,
    "renderer": 0
  },
  "anchors": 17510,
  "anchors_by_category": {
    "assertion-diagnostic": 218,
    "distinctive-debug-lua-command": 443,
    "external-only-observation": 334,
    "generic-string": 15292,
    "renderer-debug-label": 472,
    "rtti-type-name": 425,
    "source-path-filename": 187,
    "subsystem-profiling-label": 371
  },
  "anchors_by_source": {
    "docs/fable2-prototype-archaeology/phase1/evidence/prototype-debug-interfaces.json": 347,
    "docs/fable2-prototype-archaeology/phase1/evidence/prototype-debug-strings.json": 1132,
    "docs/fable2-prototype-archaeology/phase1/evidence/prototype-script-symbols.json": 459,
    "out/prototype-archaeology/phase2a/prototype-correspondence-function-features.json": 16149,
    "out/prototype-archaeology/phase2b/external/community-lua.txt": 334
  },
  "anchors_by_subsystem": {
    "ai-navigation": 75,
    "audio": 100,
    "combat": 293,
    "debug": 423,
    "physics": 77,
    "renderer": 505,
    "unassigned": 16037
  },
  "associations_by_build": {
    "build-23.12.02.0330": 26009,
    "sep-2008": 25648
  },
  "blocked_by_status": {
    "ambiguous": 8539,
    "candidate-structural": 12808,
    "no-closed-secondary-pair-record": 20701
  },
  "contradictory_associations": 3,
  "data_pointer_xrefs": 1948,
  "data_pointer_xrefs_by_build": {
    "build-23.12.02.0330": 643,
    "canonical-tu1": 662,
    "sep-2008": 643
  },
  "filtered_anchors": 15397,
  "graph_records": 0,
  "instruction_xrefs": 59769,
  "instruction_xrefs_by_build": {
    "build-23.12.02.0330": 20712,
    "canonical-tu1": 20060,
    "sep-2008": 18997
  },
  "investigated_associations": 51657,
  "joins": 4,
  "joins_by_mapping_status": {
    "accepted-exact-unique": 1,
    "accepted-normalized-corroborated": 3
  },
  "mapping_review_records": 21350,
  "problem_set_availability": {
    "closure": 35626,
    "coverage": 16622,
    "ghidra": 42462,
    "historical-crash": 3,
    "indirect": 712,
    "ownership": 311,
    "renderer": 11
  },
  "proven_native_descriptors": 0,
  "registration_records": 1948,
  "scalar_data_candidates": 2469,
  "sources": 1409,
  "sources_by_kind": {
    "external-community": 1,
    "immutable-corpus": 1184,
    "repository-evidence": 224
  },
  "statuses": {
    "accepted-registered-callback": 0,
    "accepted-xref-corroborated": 0,
    "ambiguous": 2303,
    "candidate-donor-only": 2991,
    "candidate-target-unconfirmed": 1,
    "quarantined": 46362,
    "rejected": 0
  },
  "target_corroborated": 0,
  "xref_resolved_anchors": 12934
}
```

## Evidence family

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `out/prototype-archaeology/phase2b/semantic-accepted.json` | 443 | `8C20CFE9982E101F18B9340774512C0094F20E81DB708D3C5CF222EDEC03749C` |
| `out/prototype-archaeology/phase2b/semantic-globals.json` | 2172037 | `1C7634FBC77C4B9FCC1104B0D3F8D1F04530A9152E5585821F965196FED9F899` |
| `out/prototype-archaeology/phase2b/semantic-graph.json` | 440 | `5564E2F6458D9E3ED8DCBFA4B105E28368E8585C19D0FA55D02F9DA8803E9C23` |
| `out/prototype-archaeology/phase2b/semantic-index.json` | 26113581 | `E8371499F62DFEE9CD9FB2B4695AA72E72DA15652EEB01B8A4391CCB97ABD4A4` |
| `out/prototype-archaeology/phase2b/semantic-inventory.json` | 31823433 | `EFFDCC1FEB733693DFCD09AB6DA0DF50B118C82CDFD53A2CC9B170F15FBCEE04` |
| `out/prototype-archaeology/phase2b/semantic-mapping-review.json` | 18159143 | `BBAFA29D6E1B1F065AB0166B5917F7B8B171E0241CC17B75799FE6FEB882CC03` |
| `out/prototype-archaeology/phase2b/semantic-registrations.json` | 814373 | `A3C72CC69DB2C2B5FA91E55A57B133520CC368F6689BD9A77857678D195F5A66` |
| `out/prototype-archaeology/phase2b/semantic-review.json` | 7946 | `8B4156D9F3929D0FE4DEF424691F92B31CCC433946B44804412DEF4B58ACC54A` |
| `out/prototype-archaeology/phase2b/semantic-xrefs.json` | 31210357 | `394C0BF95DF6F4D46602E1994AABB0CE88DA842C99EFAEE3ABB3EEB1297B87DD` |

All eleven JSON documents use `tools/schemas/fable2-prototype-semantics-v1.schema.json`, with distinct schema names and version 1. The nine exhaustive outputs remain ignored; only byte bindings and review-sized documentation are committed. No executable bytes or script-bank contents are embedded in committed evidence.

## Bounded policy and limitations

CONFIRMED XREFs require exact .pdata ownership and a consumed address at a call argument, store or memory access. An intermediate `lis` value is not a string reference. Address construction models signed addis/addi, ori/oris, mr/or and selected byte/halfword/word direct/indexed loads and stores. Unknown operations, basic-block boundaries and calls kill constants; chains are bounded to 32 instructions. Only initialized read-only non-executable pointers are propagated. No ABI TOC constant, writable initial pointer, interprocedural state or cross-CFG value is assumed.

A call-argument XREF proves that the value reaches that argument register at the call, not that the callee interprets it as a Lua name. Distinctive literal acceptance additionally requires the exact target literal, matching argument/call offset, accepted callee correspondence and no competing target evidence. Source filenames remain context, not proposed function names.

Registration recovery tests 8-byte name/callback layouts, repeated joint loads, bounded constructor stores and a strict counted descriptor loop. A layout alone always remains quarantined. Constructor proof requires repeated exact argument flow into nonoverlapping fields of the same object; the loop additionally proves cursor, unsigned bound, stride, exact backedge and every callback boundary. A proven descriptor is not proof of a complete Lua namespace or invocation lifetime. Target acceptance requires three accepted pairs (callback, constructor and containing caller), corresponding callsite and field roles. An explicitly null target name may use this structural support; an unknown value may not. Other layouts, complex registration routines and larger loops remain outside this recognizer's coverage.

Graph expansion is depth 1/fan-out 8, with cycles and fan-out truncation recorded. Edges require donor direct calls and corresponding TU1 calls through accepted pairs. Neighbours receive no semantic names. Scalar data candidates require exact mapped accesses and content hashes; width/read-write conflicts quarantine them. No scalar candidate is accepted as a global object: complete object boundaries and aliasing remain unproved. The approximately 99.02% same-address data observation is not an acceptance rule.

## Current recompilation intersections

Current closure source: `out/phase5a/tranche-001/closure-after/entrypoint-closure.json`. Current coverage/import source: `out/phase5a/tranche-001/merged/fable2-indirect-targets.import-plan.json`. These are distinct from the older closure retained in Phase 2A. Exact source hashes are pinned; the latter is not silently substituted for current problem evidence. Ownership rows retain both authoritative ledgers and their dispositions. Renderer boundaries are the eleven existing review candidates, not newly established renderer identities. Historical crash addresses `0x82174734`, `0x8223FD7C` and `0x825E28B0` are explicitly resolved historical intersections, not asserted open failures.

The aggregate intersection counts above and each association's `intersections` provide exact review links. No intersection by itself raises a semantic grade or authorizes a manifest/runtime fix.

## Representative evidence chains

All joined contexts are shown below, followed by a bounded ambiguous and no-XREF example. The complete mapping record is retained; XREF definitions identify exact donor/target instruction addresses. Only one provenance row is displayed here; the inventory preserves all original spellings and provenance. Literal conflicts are confirmed differences at corresponding argument sites, not automatic disproof of the closed binary mapping.

### quarantined: `TROLL_FOOTSTEP`

```json
{
  "anchor": "TROLL_FOOTSTEP",
  "anchor_id": "A-22A0F167EA485047D58F2D7D",
  "association": {
    "anchor_id": "A-22A0F167EA485047D58F2D7D",
    "build": "build-23.12.02.0330",
    "canonical_adoption": false,
    "contradictions": [
      {
        "donor_xref": "X-631C8A797901B3BDD223C78E",
        "interpretation": "semantic-conflict-for-review-not-disproof-of-binary-correspondence",
        "kind": "different-literal-in-corresponding-call-argument",
        "target_xref": "X-D2E31D74D400F4E67997B418"
      }
    ],
    "correspondence_block": null,
    "donor_function": {
      "end_exclusive": "0x828EA5A4",
      "pdata_record": "0x8212BBF0",
      "size": 348,
      "start": "0x828EA448"
    },
    "donor_xrefs": [
      "X-631C8A797901B3BDD223C78E"
    ],
    "id": "S-3A6B45DA40B1C0AB0A7EBFDA",
    "intersections": [
      {
        "address": "0x82681198",
        "disposition": "confirmed_existing_function",
        "json_pointer": "/candidates/7517",
        "set": "closure",
        "source": "out/phase5a/tranche-001/closure-after/entrypoint-closure.json"
      },
      {
        "address": "0x82681198",
        "disposition": "existing_manifest_function",
        "json_pointer": "/targets/4470",
        "set": "coverage",
        "source": "out/phase5a/tranche-001/merged/fable2-indirect-targets.import-plan.json"
      },
      {
        "address": "0x82681198",
        "disposition": "map-entry-not-semantic-proof",
        "json_pointer": "/functions/10106",
        "set": "ghidra",
        "source": "out/analysis/BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00/ghidra-function-map.json"
      }
    ],
    "kind": "native-xref-context",
    "mapping": {
      "record": {
        "acceptance_policy": "precision-first-v1",
        "contradiction_checks": {
          "boundary_valid": true,
          "contradictions_absent": true,
          "one_to_one": true,
          "reciprocal_unique": true
        },
        "donor_end_exclusive": "0x828EA5A4",
        "donor_start": "0x828EA448",
        "evidence": {
          "boundaries": {
            "donor_boundary_flags": [],
            "same_size": true,
            "target_boundary_flags": []
          },
          "contradictions": [],
          "corroborating_feature_classes": [
            "cfg-and-branch-shape",
            "local-ordering-neighbourhood",
            "direct-call-topology"
          ],
          "fingerprints": {
            "branch_normalized": {
              "equal": true,
              "shared_sha256": "FE7250770EE3E31C997B010864AF2BAE5994299DAE09A8D4CDDC61A05F25B4A9"
            },
            "constant_signature": {
              "equal": true,
              "shared_sha256": "35DC9AA9451469BC1316E2EE3DC9D5A9FA168C6D32E5E2499B48BF3F2735D65F"
            },
            "opcode_structure": {
              "equal": true,
              "shared_sha256": "2DA0C6BDAB002CC85E88BBB5EB8A239BCD605DA3F496740687DC33D177091577"
            },
            "raw": {
              "donor_sha256": "F2FCABA58470FFFFF410BB9676BFABFEE20A2E2BDACA5C7CB6AC31CCB789119D",
              "equal": false,
              "target_sha256": "9C479BA8DD000A6487F7BE15CB8904E401F809C9FDEA01AC17952303B5F24F19"
            }
          },
          "neighbourhood": {
            "anchor_count": 2,
            "anchors": [
              {
                "donor_anchor": "0x828EABF8",
                "exact_relative_delta": false,
                "ordering_consistent": true,
                "target_anchor": "0x828EAF68"
              },
              {
                "donor_anchor": "0x828EB570",
                "exact_relative_delta": false,
                "ordering_consistent": true,
                "target_anchor": "0x828EB8E0"
              }
            ],
            "exact_delta_support": 0,
            "ordering_contradictions": 0,
            "ordering_support": 2
          },
          "references": {
            "shared_data_anchor_count": 0,
            "shared_data_anchors": [],
            "shared_string_count": 0,
            "shared_strings": []
          },
          "shape": {
            "cfg_equal": true,
            "donor": null,
            "equal": true,
            "shared": {
              "block_count": 22,
              "conditional_branches": 10,
              "direct_calls": 4,
              "edge_count": 31,
              "indirect_branches": 0,
              "indirect_calls": 0,
              "instruction_count": 87,
              "returns": 1,
              "shape_class": "direct-call",
              "unconditional_branches": 3
            },
            "target": null
          },
          "topology": {
            "contradictions": 0,
            "observation_count": 1,
            "observations": [
              {
                "consistent": true,
                "donor_callee": "0x8226C9B0",
                "instruction_offset": "0x0000001C",
                "mapped_donor_callee": "0x8226C700",
                "target_callee": "0x8226C700"
              }
            ],
            "support": 1
          }
        },
        "evidence_grade": "strongly-supported",
        "semantic_name_assigned": false,
        "size": 348,
        "status": "accepted-normalized-corroborated",
        "target_end_exclusive": "0x826812F4",
        "target_start": "0x82681198"
      },
      "record_index": 5080,
      "source": "docs/fable2-prototype-archaeology/phase2a/evidence/prototype-correspondence-accepted.json"
    },
    "proposed_name": null,
    "reason": "contradictory-target-context",
    "status": "quarantined",
    "target_corroboration": []
  },
  "complete_reference_count": 2,
  "provenance_example": {
    "build": "build-23.12.02.0330",
    "json_pointer": "/builds/build-23.12.02.0330/16510/references/strings/0",
    "location": {},
    "source": "out/prototype-archaeology/phase2a/prototype-correspondence-function-features.json"
  },
  "reference_display_limit": 6,
  "references": [
    {
      "anchor_address": "0x820C2F50",
      "build": "build-23.12.02.0330",
      "checks": [
        "exact-pdata",
        "initialized-anchor",
        "single-block",
        "explicit-instruction-semantics",
        "bounded-chain"
      ],
      "definition_instructions": [
        "0x828EA550",
        "0x828EA558"
      ],
      "destination": "0x8222D118",
      "function": {
        "end_exclusive": "0x828EA5A4",
        "pdata_record": "0x8212BBF0",
        "size": 348,
        "start": "0x828EA448"
      },
      "id": "X-631C8A797901B3BDD223C78E",
      "instruction": "0x828EA560",
      "method": "bounded-def-use",
      "operand": "r4",
      "readonly_pointer_slots": [],
      "role": "call-argument",
      "width": 0
    },
    {
      "anchor_address": "0x820C2F50",
      "build": "canonical-tu1",
      "checks": [
        "exact-pdata",
        "initialized-anchor",
        "single-block",
        "explicit-instruction-semantics",
        "bounded-chain"
      ],
      "definition_instructions": [
        "0x826812A0",
        "0x826812A8"
      ],
      "destination": "0x8222CED0",
      "function": {
        "end_exclusive": "0x826812F4",
        "pdata_record": "0x82121FC8",
        "size": 348,
        "start": "0x82681198"
      },
      "id": "X-D2E31D74D400F4E67997B418",
      "instruction": "0x826812B0",
      "method": "bounded-def-use",
      "operand": "r4",
      "readonly_pointer_slots": [],
      "role": "call-argument",
      "width": 0
    }
  ]
}
```

### quarantined: `CECPhysicsSimulationCharacterNavigator`

```json
{
  "anchor": "CECPhysicsSimulationCharacterNavigator",
  "anchor_id": "A-FA59AEA60D63B6FFF8C677A8",
  "association": {
    "anchor_id": "A-FA59AEA60D63B6FFF8C677A8",
    "build": "build-23.12.02.0330",
    "canonical_adoption": false,
    "contradictions": [
      {
        "donor_xref": "X-555458A3D1D5DFBF5C99C28F",
        "interpretation": "semantic-conflict-for-review-not-disproof-of-binary-correspondence",
        "kind": "different-literal-in-corresponding-call-argument",
        "target_xref": "X-9081ADAC5DE27110150B0238"
      }
    ],
    "correspondence_block": null,
    "donor_function": {
      "end_exclusive": "0x82631A6C",
      "pdata_record": "0x8211FF58",
      "size": 60,
      "start": "0x82631A30"
    },
    "donor_xrefs": [
      "X-555458A3D1D5DFBF5C99C28F"
    ],
    "id": "S-9849E725C594340F77ACF10F",
    "intersections": [
      {
        "address": "0x82950A98",
        "disposition": "confirmed_existing_function",
        "json_pointer": "/candidates/11765",
        "set": "closure",
        "source": "out/phase5a/tranche-001/closure-after/entrypoint-closure.json"
      },
      {
        "address": "0x82950A98",
        "disposition": "existing_manifest_function",
        "json_pointer": "/targets/6832",
        "set": "coverage",
        "source": "out/phase5a/tranche-001/merged/fable2-indirect-targets.import-plan.json"
      },
      {
        "address": "0x82950A98",
        "disposition": "map-entry-not-semantic-proof",
        "json_pointer": "/functions/15258",
        "set": "ghidra",
        "source": "out/analysis/BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00/ghidra-function-map.json"
      }
    ],
    "kind": "native-xref-context",
    "mapping": {
      "record": {
        "acceptance_policy": "precision-first-v1",
        "contradiction_checks": {
          "boundary_valid": true,
          "contradictions_absent": true,
          "one_to_one": true,
          "reciprocal_unique": true
        },
        "donor_end_exclusive": "0x82631A6C",
        "donor_start": "0x82631A30",
        "evidence": {
          "boundaries": {
            "donor_boundary_flags": [],
            "same_size": true,
            "target_boundary_flags": []
          },
          "contradictions": [],
          "corroborating_feature_classes": [
            "cfg-and-branch-shape",
            "data-content-anchor"
          ],
          "fingerprints": {
            "branch_normalized": {
              "equal": true,
              "shared_sha256": "BE56FC913014F10EA479952E1AF86CD9F5476877F948B9054A2D2CC05845D8D8"
            },
            "constant_signature": {
              "equal": true,
              "shared_sha256": "D02C69BAE275B3019BFCE90BAF16FD01DCF86BA11852D2BED62A5112076C9CB6"
            },
            "opcode_structure": {
              "equal": true,
              "shared_sha256": "C03AE3DC46EA62E844608567A11430275C408389F42BC6BD527F139C5C92FFEF"
            },
            "raw": {
              "donor_sha256": "9EC5083CAF2C4CE844B9D3EDA6473481FB79D84155A5A128E8CB93BEF91288D1",
              "equal": false,
              "target_sha256": "BA68006B8C759778B7FF35FB74DE718E857991067F4E8E3D598D9F10BFD13FDF"
            }
          },
          "neighbourhood": {
            "anchor_count": 0,
            "anchors": [],
            "exact_delta_support": 0,
            "ordering_contradictions": 0,
            "ordering_support": 0
          },
          "references": {
            "shared_data_anchor_count": 1,
            "shared_data_anchors": [
              ".rdata:0x820C9344:A57CFBA0F420FDE4BD9CC6AE191BFEA1AEC89D15FB2C0BD8F4DCE50873C31B77"
            ],
            "shared_string_count": 0,
            "shared_strings": []
          },
          "shape": {
            "cfg_equal": true,
            "donor": null,
            "equal": true,
            "shared": {
              "block_count": 1,
              "conditional_branches": 0,
              "direct_calls": 1,
              "edge_count": 0,
              "indirect_branches": 0,
              "indirect_calls": 0,
              "instruction_count": 15,
              "returns": 1,
              "shape_class": "direct-call",
              "unconditional_branches": 0
            },
            "target": null
          },
          "topology": {
            "contradictions": 0,
            "observation_count": 0,
            "observations": [],
            "support": 0
          }
        },
        "evidence_grade": "strongly-supported",
        "semantic_name_assigned": false,
        "size": 60,
        "status": "accepted-normalized-corroborated",
        "target_end_exclusive": "0x82950AD4",
        "target_start": "0x82950A98"
      },
      "record_index": 3503,
      "source": "docs/fable2-prototype-archaeology/phase2a/evidence/prototype-correspondence-accepted.json"
    },
    "proposed_name": null,
    "reason": "contradictory-target-context",
    "status": "quarantined",
    "target_corroboration": []
  },
  "complete_reference_count": 2,
  "provenance_example": {
    "build": "build-23.12.02.0330",
    "json_pointer": "/builds/build-23.12.02.0330/10475/references/strings/0",
    "location": {},
    "source": "out/prototype-archaeology/phase2a/prototype-correspondence-function-features.json"
  },
  "reference_display_limit": 6,
  "references": [
    {
      "anchor_address": "0x820C9344",
      "build": "build-23.12.02.0330",
      "checks": [
        "exact-pdata",
        "initialized-anchor",
        "single-block",
        "explicit-instruction-semantics",
        "bounded-chain"
      ],
      "definition_instructions": [
        "0x82631A40",
        "0x82631A48"
      ],
      "destination": "0x8222D118",
      "function": {
        "end_exclusive": "0x82631A6C",
        "pdata_record": "0x8211FF58",
        "size": 60,
        "start": "0x82631A30"
      },
      "id": "X-555458A3D1D5DFBF5C99C28F",
      "instruction": "0x82631A50",
      "method": "bounded-def-use",
      "operand": "r4",
      "readonly_pointer_slots": [],
      "role": "call-argument",
      "width": 0
    },
    {
      "anchor_address": "0x820C9344",
      "build": "canonical-tu1",
      "checks": [
        "exact-pdata",
        "initialized-anchor",
        "single-block",
        "explicit-instruction-semantics",
        "bounded-chain"
      ],
      "definition_instructions": [
        "0x82950AA8",
        "0x82950AB0"
      ],
      "destination": "0x8222CED0",
      "function": {
        "end_exclusive": "0x82950AD4",
        "pdata_record": "0x8212D998",
        "size": 60,
        "start": "0x82950A98"
      },
      "id": "X-9081ADAC5DE27110150B0238",
      "instruction": "0x82950AB8",
      "method": "bounded-def-use",
      "operand": "r4",
      "readonly_pointer_slots": [],
      "role": "call-argument",
      "width": 0
    }
  ]
}
```

### quarantined: `__vspltb(%s, %d)`

```json
{
  "anchor": "__vspltb(%s, %d)",
  "anchor_id": "A-67662DC8C5BE31F600674377",
  "association": {
    "anchor_id": "A-67662DC8C5BE31F600674377",
    "build": "build-23.12.02.0330",
    "canonical_adoption": false,
    "contradictions": [
      {
        "donor_xref": "X-0CA09CE24703F7FBA5094245",
        "interpretation": "semantic-conflict-for-review-not-disproof-of-binary-correspondence",
        "kind": "different-literal-in-corresponding-call-argument",
        "target_xref": "X-88EC486C6922126CA5E969C4"
      }
    ],
    "correspondence_block": null,
    "donor_function": {
      "end_exclusive": "0x83062984",
      "pdata_record": "0x82153938",
      "size": 52,
      "start": "0x83062950"
    },
    "donor_xrefs": [
      "X-0CA09CE24703F7FBA5094245"
    ],
    "id": "S-B30B0F30239F50B70D12FBA4",
    "intersections": [
      {
        "address": "0x83060C30",
        "disposition": "confirmed_existing_function",
        "json_pointer": "/candidates/25083",
        "set": "closure",
        "source": "out/phase5a/tranche-001/closure-after/entrypoint-closure.json"
      },
      {
        "address": "0x83060C30",
        "disposition": "map-entry-not-semantic-proof",
        "json_pointer": "/functions/33453",
        "set": "ghidra",
        "source": "out/analysis/BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00/ghidra-function-map.json"
      }
    ],
    "kind": "native-xref-context",
    "mapping": {
      "record": {
        "acceptance_policy": "precision-first-v1",
        "contradiction_checks": {
          "boundary_valid": true,
          "contradictions_absent": true,
          "one_to_one": true,
          "reciprocal_unique": true
        },
        "donor_end_exclusive": "0x83062984",
        "donor_start": "0x83062950",
        "evidence": {
          "boundaries": {
            "donor_boundary_flags": [],
            "same_size": true,
            "target_boundary_flags": []
          },
          "contradictions": [],
          "corroborating_feature_classes": [
            "cfg-and-branch-shape",
            "direct-call-topology"
          ],
          "fingerprints": {
            "branch_normalized": {
              "equal": true,
              "shared_sha256": "3C83C5DBDE8A9B30F58A4625748FCDD436A6BBDE56964EA124C61746D74BCE8A"
            },
            "constant_signature": {
              "equal": true,
              "shared_sha256": "F2EE18C8D1D6F2611AD704D075C015BC4E687D2F4623B7464AF0889999B331E4"
            },
            "opcode_structure": {
              "equal": true,
              "shared_sha256": "B59A1C28D045440EFC5C26BD1491BF7C1D10DE43C5589C36B5FB85ACAA496AB7"
            },
            "raw": {
              "donor_sha256": "D2AC214A61CB8799F662C58F6FDBEAB35C1116FD4281838A4ECF98971E2003BA",
              "equal": false,
              "target_sha256": "16F64249B7C5991A98A1DB6055BC1B587B0562570937B4166D1383537C965589"
            }
          },
          "neighbourhood": {
            "anchor_count": 0,
            "anchors": [],
            "exact_delta_support": 0,
            "ordering_contradictions": 0,
            "ordering_support": 0
          },
          "references": {
            "shared_data_anchor_count": 0,
            "shared_data_anchors": [],
            "shared_string_count": 0,
            "shared_strings": []
          },
          "shape": {
            "cfg_equal": true,
            "donor": null,
            "equal": true,
            "shared": {
              "block_count": 1,
              "conditional_branches": 0,
              "direct_calls": 1,
              "edge_count": 0,
              "indirect_branches": 0,
              "indirect_calls": 0,
              "instruction_count": 13,
              "returns": 1,
              "shape_class": "direct-call",
              "unconditional_branches": 0
            },
            "target": null
          },
          "topology": {
            "contradictions": 0,
            "observation_count": 1,
            "observations": [
              {
                "consistent": true,
                "donor_callee": "0x8305DB18",
                "instruction_offset": "0x00000020",
                "mapped_donor_callee": "0x8305DCC8",
                "target_callee": "0x8305DCC8"
              }
            ],
            "support": 1
          }
        },
        "evidence_grade": "strongly-supported",
        "semantic_name_assigned": false,
        "size": 52,
        "status": "accepted-normalized-corroborated",
        "target_end_exclusive": "0x83060C64",
        "target_start": "0x83060C30"
      },
      "record_index": 13251,
      "source": "docs/fable2-prototype-archaeology/phase2a/evidence/prototype-correspondence-accepted.json"
    },
    "proposed_name": null,
    "reason": "contradictory-target-context",
    "status": "quarantined",
    "target_corroboration": []
  },
  "complete_reference_count": 2,
  "provenance_example": {
    "build": "build-23.12.02.0330",
    "json_pointer": "/builds/build-23.12.02.0330/36903/references/strings/0",
    "location": {},
    "source": "out/prototype-archaeology/phase2a/prototype-correspondence-function-features.json"
  },
  "reference_display_limit": 6,
  "references": [
    {
      "anchor_address": "0x8205AE2C",
      "build": "build-23.12.02.0330",
      "checks": [
        "exact-pdata",
        "initialized-anchor",
        "single-block",
        "explicit-instruction-semantics",
        "bounded-chain"
      ],
      "definition_instructions": [
        "0x83062960",
        "0x83062968"
      ],
      "destination": "0x8305DB18",
      "function": {
        "end_exclusive": "0x83062984",
        "pdata_record": "0x82153938",
        "size": 52,
        "start": "0x83062950"
      },
      "id": "X-0CA09CE24703F7FBA5094245",
      "instruction": "0x83062970",
      "method": "bounded-def-use",
      "operand": "r4",
      "readonly_pointer_slots": [],
      "role": "call-argument",
      "width": 0
    },
    {
      "anchor_address": "0x8205AE2C",
      "build": "canonical-tu1",
      "checks": [
        "exact-pdata",
        "initialized-anchor",
        "single-block",
        "explicit-instruction-semantics",
        "bounded-chain"
      ],
      "definition_instructions": [
        "0x83060C40",
        "0x83060C48"
      ],
      "destination": "0x8305DCC8",
      "function": {
        "end_exclusive": "0x83060C64",
        "pdata_record": "0x82153810",
        "size": 52,
        "start": "0x83060C30"
      },
      "id": "X-88EC486C6922126CA5E969C4",
      "instruction": "0x83060C50",
      "method": "bounded-def-use",
      "operand": "r4",
      "readonly_pointer_slots": [],
      "role": "call-argument",
      "width": 0
    }
  ]
}
```

### candidate-target-unconfirmed: `HammerCombat`

```json
{
  "anchor": "HammerCombat",
  "anchor_id": "A-6BE754F7078C766B2FED9075",
  "association": {
    "anchor_id": "A-6BE754F7078C766B2FED9075",
    "build": "build-23.12.02.0330",
    "canonical_adoption": false,
    "contradictions": [],
    "correspondence_block": null,
    "donor_function": {
      "end_exclusive": "0x8229B484",
      "pdata_record": "0x8210F8B8",
      "size": 380,
      "start": "0x8229B308"
    },
    "donor_xrefs": [
      "X-EEC53598FE2882E540A235A8"
    ],
    "id": "S-FCEF3DCAA6D1D5FB2EF8AB8F",
    "intersections": [
      {
        "address": "0x8229B038",
        "disposition": "map-entry-not-semantic-proof",
        "json_pointer": "/functions/1984",
        "set": "ghidra",
        "source": "out/analysis/BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00/ghidra-function-map.json"
      }
    ],
    "kind": "native-xref-context",
    "mapping": {
      "record": {
        "acceptance_policy": "precision-first-v1",
        "contradiction_checks": {
          "boundary_valid": true,
          "contradictions_absent": true,
          "one_to_one": true,
          "reciprocal_unique": true
        },
        "donor_end_exclusive": "0x8229B484",
        "donor_start": "0x8229B308",
        "evidence": {
          "boundaries": {
            "donor_boundary_flags": [],
            "same_size": true,
            "target_boundary_flags": []
          },
          "contradictions": [],
          "corroborating_feature_classes": [
            "cfg-and-branch-shape",
            "local-address-delta-neighbourhood",
            "string-content-anchor",
            "data-content-anchor"
          ],
          "fingerprints": {
            "branch_normalized": {
              "equal": true,
              "shared_sha256": "9EF1F0FF3E1ACB6D3C0CA2B85EDC756B7E2D929E16080354BA1F0CCE26FA07E9"
            },
            "constant_signature": {
              "equal": true,
              "shared_sha256": "5AFADB7786ADF6FD2DFCFA2A900566B113920F73BF2CF9BB95B3556A6C8F3501"
            },
            "opcode_structure": {
              "equal": true,
              "shared_sha256": "ACCBD2CA325B930471CB218E356E25DCBD952B66E6E7FED05F9A6D3A08618B7E"
            },
            "raw": {
              "equal": true,
              "shared_sha256": "7DC8302D7AFF26667F1C4C429DC837D7874A00B2F26231B19F5E3389C3B0B240"
            }
          },
          "neighbourhood": {
            "anchor_count": 3,
            "anchors": [
              {
                "donor_anchor": "0x8229B220",
                "exact_relative_delta": true,
                "ordering_consistent": true,
                "target_anchor": "0x8229AF50"
              },
              {
                "donor_anchor": "0x8229B508",
                "exact_relative_delta": true,
                "ordering_consistent": true,
                "target_anchor": "0x8229B238"
              }
            ],
            "exact_delta_support": 3,
            "ordering_contradictions": 0,
            "ordering_support": 3
          },
          "references": {
            "shared_data_anchor_count": 1,
            "shared_data_anchors": [
              ".rdata:0x8200131C:844CF9439BC8E680EA3AB96D157BB1F17AC6BE786798B0C7CB7FD4D30EC3BA25"
            ],
            "shared_string_count": 1,
            "shared_strings": [
              "HammerCombat"
            ]
          },
          "shape": {
            "cfg_equal": true,
            "donor": null,
            "equal": true,
            "shared": {
              "block_count": 22,
              "conditional_branches": 11,
              "direct_calls": 1,
              "edge_count": 31,
              "indirect_branches": 0,
              "indirect_calls": 0,
              "instruction_count": 95,
              "returns": 2,
              "shape_class": "direct-call",
              "unconditional_branches": 4
            },
            "target": null
          },
          "topology": {
            "contradictions": 0,
            "observation_count": 0,
            "observations": [],
            "support": 0
          }
        },
        "evidence_grade": "confirmed",
        "semantic_name_assigned": false,
        "size": 380,
        "status": "accepted-exact-unique",
        "target_end_exclusive": "0x8229B1B4",
        "target_start": "0x8229B038"
      },
      "record_index": 809,
      "source": "docs/fable2-prototype-archaeology/phase2a/evidence/prototype-correspondence-accepted.json"
    },
    "proposed_name": null,
    "reason": "target-semantic-support-insufficient",
    "status": "candidate-target-unconfirmed",
    "target_corroboration": []
  },
  "complete_reference_count": 1,
  "provenance_example": {
    "build": "build-23.12.02.0330",
    "json_pointer": "/builds/build-23.12.02.0330/15216/references/strings/0",
    "location": {},
    "source": "out/prototype-archaeology/phase2a/prototype-correspondence-function-features.json"
  },
  "reference_display_limit": 6,
  "references": [
    {
      "anchor_address": "0x8200131C",
      "build": "build-23.12.02.0330",
      "checks": [
        "exact-pdata",
        "initialized-anchor",
        "single-block",
        "explicit-instruction-semantics",
        "bounded-chain"
      ],
      "definition_instructions": [
        "0x8229B31C",
        "0x8229B324"
      ],
      "destination": "0x8229B488",
      "function": {
        "end_exclusive": "0x8229B484",
        "pdata_record": "0x8210F8B8",
        "size": 380,
        "start": "0x8229B308"
      },
      "id": "X-EEC53598FE2882E540A235A8",
      "instruction": "0x8229B328",
      "method": "bounded-def-use",
      "operand": "r4",
      "readonly_pointer_slots": [],
      "role": "call-argument",
      "width": 0
    }
  ]
}
```

### ambiguous: `StartTimeInSeconds`

```json
{
  "anchor": "StartTimeInSeconds",
  "anchor_id": "A-368BC35E549E7DFC6F868E20",
  "association": {
    "anchor_id": "A-368BC35E549E7DFC6F868E20",
    "build": "sep-2008",
    "canonical_adoption": false,
    "contradictions": [],
    "correspondence_block": "no-closed-secondary-pair-record",
    "donor_function": {
      "end_exclusive": "0x832235B0",
      "pdata_record": "0x82156EE0",
      "size": 64,
      "start": "0x83223570"
    },
    "donor_xrefs": [
      "X-0F9B5B6C237829BD945715E8"
    ],
    "id": "S-006AF51093E09FECF58C1E92",
    "intersections": [],
    "kind": "native-xref-context",
    "mapping": null,
    "proposed_name": null,
    "reason": "multiple-native-meanings-or-field-roles",
    "status": "ambiguous",
    "target_corroboration": []
  },
  "complete_reference_count": 1,
  "provenance_example": {
    "build": "build-23.12.02.0330",
    "json_pointer": "/builds/build-23.12.02.0330/40656/references/strings/0",
    "location": {},
    "source": "out/prototype-archaeology/phase2a/prototype-correspondence-function-features.json"
  },
  "reference_display_limit": 6,
  "references": [
    {
      "anchor_address": "0x8208F6D0",
      "build": "sep-2008",
      "checks": [
        "exact-pdata",
        "initialized-anchor",
        "single-block",
        "explicit-instruction-semantics",
        "bounded-chain"
      ],
      "definition_instructions": [
        "0x8322357C",
        "0x83223584"
      ],
      "destination": "0x8222E7B0",
      "function": {
        "end_exclusive": "0x832235B0",
        "pdata_record": "0x82156EE0",
        "size": 64,
        "start": "0x83223570"
      },
      "id": "X-0F9B5B6C237829BD945715E8",
      "instruction": "0x83223590",
      "method": "bounded-def-use",
      "operand": "r4",
      "readonly_pointer_slots": [],
      "role": "call-argument",
      "width": 0
    }
  ]
}
```

### quarantined: `Warning: no user event handler interface is installed; Mouse.hide failed.`

```json
{
  "anchor": "Warning: no user event handler interface is installed; Mouse.hide failed.",
  "anchor_id": "A-5EB9867ACEDE4CA914D8FF3E",
  "association": {
    "anchor_id": "A-5EB9867ACEDE4CA914D8FF3E",
    "build": "sep-2008",
    "canonical_adoption": false,
    "contradictions": [],
    "correspondence_block": null,
    "donor_function": null,
    "donor_xrefs": [],
    "id": "S-0026627D91ABB206B1E94E57",
    "intersections": [],
    "kind": "native-xref-context",
    "mapping": null,
    "proposed_name": null,
    "reason": "no-proven-native-donor-reference",
    "status": "quarantined",
    "target_corroboration": []
  },
  "complete_reference_count": 0,
  "provenance_example": {
    "build": "build-23.12.02.0330",
    "json_pointer": "/builds/build-23.12.02.0330/34768/references/strings/0",
    "location": {},
    "source": "out/prototype-archaeology/phase2a/prototype-correspondence-function-features.json"
  },
  "reference_display_limit": 6,
  "references": []
}
```

There are no accepted real examples to promote and no real `rejected` terminal assertions in this run. Rejection fixtures instead demonstrate disproven hypotheses (non-executable/interior callbacks, wrong loop backedges and incompatible access roles); production retains these unsafe candidates as quarantined records. Synthetic positive descriptor/stripped-name fixtures validate implemented gates, not retail semantic accuracy.

## Verification and safety

Generation rehashes all sources, runs the closed Phase 2A consistency verifier before consumption, checks the closed document invariants, reconciles exact terminal coverage, accepted subsets and review availability, and audits the complete Git delta against a Phase 2B-only allowlist. SDK branch/HEAD/tree/status and modified libmspack bytes must equal the initial capture. Verification repeats analysis and compares every JSON and this report byte-for-byte; timestamps and current HEAD are not analytical inputs. Schema checking is a separate required command documented in the README. Mutation tests cover omitted/duplicated records, unsupported acceptance, review drift and forbidden propagation.

No canonical names, manifest entries, overrides, generated source, runtime code, renderer code, SDK code or binary inputs were changed. Neither prototype nor TU1 was launched. No gameplay, input automation, screenshots, build/codegen or shader/resource parsing was performed. The only network operation was the authorized pinned community raw-file retrieval. No push, fetch, pull, merge, tag, PR, upload or release operation was performed.

Next step: review the mapped literal conflicts and the HammerCombat callee boundary/context statically; do not adopt symbols yet. See [review guide](review-guide.md), [handoff](phase2c-handoff.md) and [reproduction commands](README.md).
