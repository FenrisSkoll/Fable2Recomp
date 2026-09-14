# Phase 2I authority and non-propagation policy

## Evidence hierarchy

Closed Phase 2A records prove Build-23↔TU1 correspondence provenance only.
Phase 2E additions are owner-approved, non-canonical correspondences with exact
reservations. Phase 2E suppressions are tombstones and can never route evidence.
Phase 2F transported contexts are unreviewed analysis evidence. Phase 2G
corroboration is static review evidence, not owner approval. Phase 2H approves
only Packet C's non-canonical contextual role. Held, probable and physics rows
are excluded proposals and can be displayed only as inactive warnings.

A transported string is not a function name. An approved correspondence is not
an approved semantic label. A contextual role is not a canonical name.

## Selections

Mapping and semantic selections are independent and fail closed. Mapping views
are exactly `none`, `closed-phase2a-default`, and `phase2e-v1`. Semantic views
are exactly `none`, `phase2f-evidence`, and `phase2h-v1`. A semantic selection
cannot add, suppress or change a correspondence.

The no-selection default validates or reports help/lookup absence only. It does
not expose overlay additions, semantic contexts or reviewed roles, and it does
not write. Bulk correspondence export requires both the explicit profile and a
separate deliberate bulk flag.

## Prohibited propagation

Every record states that it has no canonical-name, production-mapping or runtime
authority. The schema prohibits name/rename fields. Phase 2I does not modify a
manifest, production mapping, symbol table, generated source, runtime, renderer,
SDK, proprietary asset, or Ghidra database. Evidence grades and reservations are
preserved verbatim and never converted into authorization.
