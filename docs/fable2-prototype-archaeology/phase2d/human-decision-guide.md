# Human decision guide

No approval is recorded by this task. The machine recommendations and human decisions
are separate fields. `evidence/human-decision-ledger.json` contains every original
strong proposal, both physics candidates, all three suppressions and any newly
recommended former-probable proposal. All rows are pending.

Read the report and inspect the deterministic batches in
`out/prototype-archaeology/phase2d/risk-strata-and-batches.json`. The readable review
guide lists the mapping rows. Each ledger row binds exact intervals, evidence tier,
reservations, dependency seeds, reference identities, competitor count and downstream
intersections to its packet hash. A transported label is not a proposed function name.

For a later decision, the owner must supply:

- the selected batch IDs and an explicit approve/reject decision;
- the exact proposal-set hash from the ledger and the selected batch hashes;
- an approver identity chosen by the owner;
- a decision timestamp supplied as data, not obtained from the current clock;
- an external decision record identifier; and
- the precise adoption surface authorized for the follow-up task.

The ledger validator rejects a changed decision without a matching separately
supplied external decision record, approver, timestamp, batch and proposal-set hash.
The Phase 2D schema and final verification additionally require every row to remain
pending. A later adoption task must retain this frozen pending dossier and create a
separate decision record; it must not impersonate the owner or rewrite this evidence.

The decision requested before any adoption task begins is:

> Which nonempty batches do you explicitly approve for a separately scoped,
> reversible semantic-transport and mapping overlay: B00-semantic-suppressions,
> B01-unreserved, B02-multiple-references-reserved, B04-callee-only-reserved and
> B05-internal-region-reserved? Supply your approver identity, decision timestamp,
> external decision record and exact ledger/batch hashes. This approval would not
> authorize names, scripts, assets, manifests, generated code or runtime changes.

The owner may approve none, reject a batch, request further evidence or approve a
strict subset with a newly enumerated exact set hash. No decision is inferred from
requesting or reading this dossier.
