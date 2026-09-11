# Bounded human review

First run deterministic and schema verification from the [README](README.md).
Do not interpret a file that is missing, has a different hash, or belongs to a
different Phase 2A bundle. Load `semantic-review.json` from the ignored output
root. Its strata report both selected and available counts; empty accepted
strata are an explicit result, not a missing review deliverable.

For each selected association:

1. Resolve `association_id` in `semantic-index.json`, then `anchor_id` in
   `semantic-inventory.json`. Inspect exact spelling, filters, every source
   location and exact versus terminal-only occurrences. Community headers do
   not establish a namespace in native code.
2. Resolve each donor XREF ID. Check the referring instruction, definition
   chain, source section and `.pdata` record. Disassemble only those bounded
   functions from the hash-bound initialized section. A data pointer with no
   native consumer is insufficient.
3. For a registration, inspect both fields, exact callback entry, repeated
   consumer role, constructor stores and any bound/backedge proof. Reject
   adjacency or interior-entry assumptions. Keep caller and callback separate.
4. Resolve the original Phase 2A accepted record by index and compare the
   entire row. A candidate/ambiguous donor is blocked; do not promote it here.
5. Independently inspect the TU1 XREF or descriptor and accepted callee/caller
   joins. Different literals, argument roles, stores or call roles remain
   contradictions even when body matching is accepted.
6. Inspect the recorded closure/coverage/map/ownership/renderer membership.
   Membership is review priority, not semantic proof. Record a recommendation
   outside canonical naming sources; do not add manifest entries.

## High-value starting examples

`HammerCombat`: donor `[0x8229B308,0x8229B484)` calls `0x8229B488` at
`0x8229B328` with the literal in r4. Its exact accepted target is
`[0x8229B038,0x8229B1B4)`; r4 reaches `0x8229B1B8` at `0x8229B058`.
Matching literals alone do not close the callee-role requirement. Review the
two callee bodies statically; do not create a new Phase 2A mapping in place.

`CECPhysicsSimulationCharacterNavigator`: donor
`[0x82631A30,0x82631A6C)` passes its literal at `0x82631A50` in r4 to
`0x8222D118`. The accepted normalized target
`[0x82950A98,0x82950AD4)` passes
`CECPhysicsSimulationCharacterControlled` at `0x82950AB8` to `0x8222CED0`.
Both construct `0x820C9344`, but that address has different full strings.
The shared prefix is insufficient semantic evidence. This is a quarantined
association and mapping-review item, not a changed binary mapping.

`TROLL_FOOTSTEP` in donor `[0x828EA448,0x828EA5A4)` at `0x828EA560`
corresponds to a `DESTROY_ENTITY` argument at `0x826812B0` in target
`[0x82681198,0x826812F4)`. `__vspltb(%s, %d)` in donor `0x83062950`
corresponds to `__vcfsx(%s, %d)` in target `0x83060C30`. The generated report
contains their full mapping and XREF chains; inspect those rather than relying
on lexical labels as established function names.

The intermediate `lis` value `0x820C0000` can coincide with the address of
`SetObjectiveTag` before the low half constructs a different address. The
scanner deliberately does not report that intermediate value as a native use.
This is an important negative example for manual reviews too.

No real accepted or conclusively rejected semantic record is available in this
run. The report includes an ambiguous generic-context example and a no-native-
reference quarantine. Synthetic fixtures demonstrate positive descriptor gates
and rejected hypotheses, not real semantic accuracy. Keep these populations
separate in any review notes.

The existing read-only disassembler used to corroborate the physics pair was
`out/tools/ppc-disasm.exe`, SHA-256
`D850AB1F3DBD43FA11CD56E17E29F3AAFDF82B9271A89C4AAC707C4FE5C65A4D`.
No executable was rebuilt or launched as a game.
