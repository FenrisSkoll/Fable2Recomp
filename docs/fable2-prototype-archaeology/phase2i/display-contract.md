# Phase 2I display and interchange contract

## Owned block

Each annotation has an evidence-derived ID and marker:

```text
[F2PA:phase2i:A-<24 uppercase hexadecimal digits>]
```

The marker and a single normalized comment line form the exact owned block.
Comments visibly distinguish `MAPPING` from `SEMANTIC EVIDENCE`, active from
`SUPPRESSED`/`EXCLUDED`, `UNREVIEWED` from `OWNER-REVIEWED`, and `RESERVED` from
unreserved. Packet C includes `CONTEXTUAL ROLE — NOT A FUNCTION NAME`.

Evidence text is normalized to a single line. Control characters, tabs, line
breaks and non-printing characters become deterministic escaped text. Literal
namespace-marker fragments are escaped, so evidence cannot forge an owned block
or inject another comment line.

## Additive plan

The Ghidra-compatible plan contains addresses, `PRE_COMMENT`, a namespaced
bookmark category, exact block text/hash and rollback identity. It contains no
mutation instruction or executable Ghidra code. A later separately authorized
importer must append exact blocks without replacing user text.

An identical owned block is idempotent. A stale block with the same ID and a
different hash is a conflict. User comments and unrelated bookmarks are never
owned, overwritten or deleted. Removal selects only the exact marker, exact
content and exact SHA-256; surrounding bytes must remain unchanged.
