# Next-phase handoff: targeted static follow-up, not symbol adoption

Phase 2B's bounded semantic pipeline has no accepted real associations. Do not
mass-rename, adopt a proposed name, or infer that the 15,299 Phase 2A body pairs
are named functions. The exact terminal counts and byte bindings are in
[report.md](report.md) and [semantic-validation.json](evidence/semantic-validation.json).

## Smallest next target

Review only the `CECPhysicsSimulationCharacterNavigator` donor pair
`0x82631A30 -> 0x82950A98` and its differing r4 literals first. The donor call
is `0x82631A50 -> 0x8222D118`; target is
`0x82950AB8 -> 0x8222CED0`. Both literal addresses are `0x820C9344`, but target
spelling is `CECPhysicsSimulationCharacterControlled`. Establish whether this
is legitimate body reuse with changed semantic data, a matching-policy
collision, or another role distinction. Those explanations remain hypotheses.
The Phase 2B mapping-review record is the correct starting point; do not edit
the closed Phase 2A accepted set during review.

Then examine the exact `HammerCombat` caller pair
`0x8229B308 -> 0x8229B038` and callee candidates
`0x8229B488 -> 0x8229B1B8`. Native literal passing is confirmed; independent
callee-role correspondence remains unaccepted. A reviewed follow-up may produce
a separate mapping revision proposal, not retroactive Phase 2B acceptance.

## What remains unresolved

- No real repeated native registration descriptor/loop passed the narrow
  recognizer. This is limited coverage, not evidence that Lua callbacks do not
  exist. A next recognizer should be driven by a disassembled, bounded real
  initialization routine, with negative fixtures before broader scanning.
- September has independent native XREFs, but the closed secondary acceptance
  is aggregate-only. An explicit separately versioned secondary pair dataset
  would be needed before semantic routing; do not recreate it silently under
  Phase 2A provenance.
- No accepted association intersects an open indirect/ownership/crash or
  renderer set. The four joined contexts have current map/closure/coverage
  review links, not runtime fixes. Historical crash entries are resolved.
- Scalar content/access agreement does not prove object boundaries or aliases;
  none is accepted as a stable semantic global.
- Generic/external-only filters and single-block constant recovery deliberately
  leave substantial native evidence unresolved. No completeness or measured
  semantic precision claim follows from the synthetic controls.

## Preservation contract

Start with root `AGENTS.md`, this handoff, the generated report and exact source
pins. Preserve the closed commit `6ce54cbdcaa9fef23c6cd13e86fe46d3783cf3fd`, tree
`774c4f401bd44f8de1ea8f95c7344988ad12773c`, input bundle
`DA77AF8D9345C684F81FDD342CDB1E95E48CC826A374D783EEC561F1EDE42B2F`, all Phase 1/2A
evidence and canonical inputs. Keep ReXGlue at
`fa10315ff88ca56b2d0b380de40bad5b59b542bd` with its exact pre-existing libmspack
state. No temporary runtime instrumentation is present. No game, capture,
runtime, renderer or manifest work is part of this handoff.

Find Phase 2B local commits without embedding a self-referential final hash:

```powershell
git log --format='%H %s' 6ce54cbdcaa9fef23c6cd13e86fe46d3783cf3fd..fable2-prototype-archaeology-phase2b
git rev-parse fable2-prototype-archaeology-phase2b
git rev-parse 'fable2-prototype-archaeology-phase2b^{tree}'
```

Canonical adoption requires a later explicit decision after evidence review.
No automatic propagation or symbol-import command is supplied.
