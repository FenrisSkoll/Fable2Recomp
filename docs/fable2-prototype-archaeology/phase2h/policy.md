# Phase 2H policy

## Authority

The sole new authority is owner record `P2G-OWNER-DECISION-001`, approver `FenrisSkoll`, decision date `2026-09-13`, source `owner-supplied-chat-statement`. Its exact normalized 477-byte UTF-8 statement and SHA-256 are binding. No approval time is inferred or fabricated.

The statement authorizes only Packet C, terminal `S-202449BD00F31D43FE6EBBA4`, owner mapping `0x825240E8 -> 0x82522C10`, and contextual role “conditional keyed reward/world-map field materializer” with status “owner-reviewed non-canonical contextual role.” The phrase is an analyst annotation, not a function or symbol name.

## Semantic correction

- `0x821B2528 -> 0x821B24F8` resolves a two-word handle. It reads none of parked `r5`/`r6`/`r7` and does not consume `RewardMoney` or `RewardRenown`.
- `0x823C0588 -> 0x823BF820` receives each scalar key in `r4`, performs its lookup, and returns the 32-bit word stored at object `+0x20` for `RewardRenown` or `+0x24` for `RewardMoney`. Signedness and numeric representation remain unresolved.
- `0x82310448 -> 0x82310290` remains the separate Boolean-like route for `AppearOnWorldMap`, stored at object `+0x4D` as one normalized 0/1 byte.
- `SetObjectiveTag`, terminal `S-26C37A0D8DC5C81610D44E94`, is `rejected-false-high-half-alias`: the handle resolver reads none of the parked values and TU1 `0x820C0000` points inside different text. It is not a Packet C key and supplies no semantic vote.

## Preservation and non-propagation

Mapping `0x825240E8 -> 0x82522C10` remains unchanged, non-canonical, and represented only as a preserved reference. Reservation `single-independent-support-class` remains exact. The independent TU1 visitor `[0x825237C8,0x82524454)` corroborates `+0x20`, `+0x24`, and `+0x4D`; its direction remains unresolved.

Phase 2H does not approve Packet A, Packet B, another Phase 2F row, any held/probable/physics mapping, canonical naming, reservation removal, or mapping mutation. It does not claim reward granting or arithmetic, map-marker creation, visibility updates, constructor identity, serialization direction, or complete quest-object ownership.

No Phase 2H annotation may propagate to a production symbol table, manifest, Ghidra database, runtime, renderer, generated source, mapping record, or semantic feedback loop. Bulk labels, free-camera, Lua, script-bank, E3/demo, and game integration remain outside scope.

## Consumer rule

The default is closed and exposes no new reviewed annotation. An opt-in is valid only when `phase2h-v1` and the exact repository-relative source-pins, decision, delta, and materialized-view identities are supplied. Invalid opt-in refuses; it never falls back while claiming opt-in success.
