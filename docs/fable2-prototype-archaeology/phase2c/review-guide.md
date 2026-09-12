# Manual review of the provisional layer

Run the read-only replay and schema checks from README.md. Verify the validation
manifest against actual ignored bytes and the report table. Do not use a stale
semantic result with a different mapping-freeze hash.

For a mapping:

1. Resolve the original record index and hash in closed Phase 2A. Inspect the
   complete original row, not only the current grade.
2. Inspect `trust-audit.json`: complete anchor boundaries and contents, native
   definition/use chains, exact instruction offsets, argument/access roles and
   contradictions. All three suppressions must remain effective.
3. In `reference-candidates.json`, inspect both sides' full bytes and .pdata
   boundaries using the bound section exports. The canonical fingerprint is a
   candidate comparison, not a substitute for reviewing the instructions.
4. Separate facts consumed by canonicalization from independent support. Follow
   every caller, callee or neighbourhood dependency to retained closed evidence
   or a strictly earlier proposal generation. Check competing candidates across
   the complete donor/target signature populations.
5. Check unresolved calls and tails, target ownership and effective-view
   injectivity. A probable pairing cannot be promoted merely because it appears
   in a semantic or preservation inventory.

For a semantic context, resolve its Phase 2B record ID, original anchor, donor
XREF and target XREF. For September inspect both hops and the intermediate
literal/callee role. A target-corroborated argument role is not a function name.
The HammerCombat context is an exclusion guard involving object offset +8;
the comparator ranges have no .pdata ownership.

Inspect all four physics wrappers and their 0xA0 immediate helpers in
`known-cases.json`. The same-name proposals remain candidates under the strict
independent-support gate. Their code/data similarity is useful evidence, but
does not close the helper's changed global/call relationships.

`review.json` reports selected and available counts, including empty strata.
Strata overlap; their totals must not be added as distinct observations.
Registration disassembly is bounded to explicit ends, and absence of proof in
that slice is not a claim of absence in the binary. Pointer runs are not proven
vtables. Current-runtime startup scripts are separately pinned and their path
category does not establish a runtime Lua state or a callable TU1 feature.

For completion, start with `completion/completion-review.json`: every retained
strong proposal is selected, alongside stratified lower-grade and intersection
examples. Follow its packet into `completion/feature-ablation.json`. Compare
exact boundaries and instruction offsets, competing and reciprocal candidates,
reference tokens, external seed dependencies, behavior summaries, eleven
counterfactuals and minimal support alternatives. Machine selection is not human
approval. A mandatory-gate dependency is not an independent corroborating vote.

Use `completion/boundary-completion.json` and `completion/typed-completion.json`
for per-record negative reasons and alternate explanations. Do not turn exact
fragments into invented functions, pointer runs into vtables, or type references
into constructor names. Consult completion-matrix.json for all 187 requirement
bindings and all 39 fixture categories, including exact evidenced blockers.

`completion/ownership-verification.json` separates unchanged current validators
from blocked historical byte replay. Resolve the specified missing input before
an all-green close-out; do not modify the manifest or regenerate code.
