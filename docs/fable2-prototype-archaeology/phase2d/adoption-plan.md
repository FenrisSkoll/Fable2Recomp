# Later adoption and rollback

This is a non-mutating plan. None of the following steps is authorized by Phase 2D.
Every mapping, suppression and known-case human decision remains pending. The
complete read-only consumer inventory is `out/prototype-archaeology/phase2d/future-consumers.json`.

## Separate decision surfaces

| Surface | Preconditions for a later task | Intended change | Rollback |
| --- | --- | --- | --- |
| Semantic-transport suppressions | Owner approves B00 and an explicit overlay consumer | Versioned exclusion overlay for the three unsafe pairs, with suppression precedence at every route | Disable the new overlay consumer; restore its prior configuration hashes. Do not rewrite the original Phase 2A rows. |
| Mapping additions | Owner names exact approved batches and set hashes; all dependencies remain validated | Versioned analysis map containing only the approved rows and three exclusions | Switch consumers back to their pinned pre-adoption map; retain the withdrawn overlay as audit evidence. |
| Contextual semantic roles | Independent TU1 use evidence and approved mapping dependencies remain valid | Analysis annotations explicitly labelled as contextual roles | Remove the annotation overlay/import transaction and restore the prior analysis export. |
| Analysis-only aliases | Separate approval of alias text and provenance | Optional Ghidra or report aliases that remain visibly non-canonical | Restore the pre-import project copy/export and its hashes. |
| Canonical function names | Separate naming review with stronger source-level evidence | Only the explicitly authorized name layer | Revert only that naming transaction against its pre-change export. |
| Runtime, manifest, generated code or renderer | Separate implementation request and title-correctness evidence | No change is implied by a mapping recommendation | Follow the separately reviewed implementation rollback; Phase 2D is not its authority. |

Current archaeology tools that read closed accepted maps or effective maps require
explicit versioned consumer selection. The old closed datasets must continue to
reproduce their original results. Do not replace paths in the Phase 2B/2C generators
and call it adoption. New consumers need a separate schema/version with exact
input identities, allowed approved-set hash and explicit noncanonical/canonical state.

Ghidra imports, function-map exports, closure and coverage joins, ownership reports
and documentation are potential downstream analysis surfaces. Membership in a
closure, coverage or Ghidra dataset is review context, not permission to modify it.
Prototype mappings are not runtime address overrides. Indirect-call destinations
must not be invented from the two held strong proposals.

## Reversible order

First record the external owner decision, supplied timestamp and approver identity
against exact ledger and batch hashes. Then capture the current consumer artifact
hashes and any affected analysis-project backup. Construct an isolated overlay,
verify its exact expected map count and dependencies, and test it against a copied
analysis consumer. Only after these checks may the specifically authorized consumer
be switched. Each switch is a separate auditable step with its previous path/hash.

B00 is a precondition for every mapping consumer view. B01 contains the unreserved
recommendations. B02 and B04 explicitly carry callee-only reservations; B05 carries
the unowned comparator-region reservation. B03 and B06 are empty. The owner can
approve batches independently; the cumulative counts assume all preceding nonempty
batches, but no dependency requires a held proposal.

Stop and roll back the consumer switch on stale input hashes, changed byte identity,
unexpected map count, duplicate donor/target, suppressed route, dangling dependency,
new contradiction, unsupported naming, changed scope or any production side effect.
Disable the new consumer overlay and restore the recorded pre-adoption artifacts.
Never regenerate frozen archaeology evidence to accommodate a consumer failure.
