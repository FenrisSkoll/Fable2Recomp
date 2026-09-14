# Phase 2I rollback and collision model

Phase 2I does not apply changes. Its rollback proof models how a later,
separately authorized importer could remove only Phase 2I-owned blocks.

Ownership requires the exact `[F2PA:phase2i:<annotation-id>]` marker, exact
two-line namespaced block bytes, exact SHA-256 in the rollback manifest, and the
matching TU1 address and comment/bookmark kind.

No pre-existing analyst text or bookmark is owned by Phase 2I. A planned block
is appended after user text. Identical owned bytes are idempotent. The same ID
with different bytes is a stale conflict and is neither overwritten nor removed.
A later replacement would require separate authorization and the exact old hash.

The controls cover an empty comment, existing user comment, unrelated bookmark,
identical owned block, stale same-ID block, multiple records at one address, a
suppression tombstone sharing `0x83060C30` with the corrected active route, and
exact removal. Removal restores surrounding UTF-8 user bytes byte-for-byte,
including line breaks and trailing spaces.

Every `rollback-manifest.json` contains annotation ID, target address,
comment/bookmark kinds, exact block hash, expected removal selector and collision
disposition. It is a preview contract, not executable removal code.
