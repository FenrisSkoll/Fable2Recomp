# Phase 2H report

## Result

Owner decision `P2G-OWNER-DECISION-001` approves only Packet C's non-canonical contextual role **conditional keyed reward/world-map field materializer**. This append-only semantic annotation does not name a function and does not alter the approved mapping, any reservation, or any frozen Phase 1–2G evidence.

The handle resolver `0x821B2528 -> 0x821B24F8` resolves the two-word handle and consumes none of the parked reward-key registers. The subsequent scalar helper `0x823C0588 -> 0x823BF820` receives `RewardRenown` and `RewardMoney` in `r4`, returning the 32-bit words stored at object `+0x20` and `+0x24`; signedness and numeric representation remain unresolved. The separate Boolean-like helper `0x82310448 -> 0x82310290` retains `AppearOnWorldMap` at object `+0x4D` as one normalized 0/1 byte.

`SetObjectiveTag` (`S-26C37A0D8DC5C81610D44E94`) is rejected as `rejected-false-high-half-alias`: the handle resolver reads none of parked `r5`/`r6`/`r7`, and TU1 address `0x820C0000` is an interior pointer to different text. It is neither a Packet C key nor a semantic vote.

## Preserved limits

- Owner mapping `0x825240E8 -> 0x82522C10` remains unchanged and non-canonical.
- Reservation remains exactly `single-independent-support-class`.
- Independent visitor `[0x825237C8,0x82524454)` corroborates `+0x20`, `+0x24`, and `+0x4D`; direction remains unresolved.
- Packet A, Packet B, and every other semantic row remain unapproved.
- No reward granting/arithmetic, map-marker creation, visibility update, constructor identity, serialization direction, or complete quest-object ownership is claimed.
- Canonical naming and mapping/manifest/Ghidra/runtime/renderer/generated-code propagation remain prohibited.

## Consumer behavior

Default selection exposes zero Phase 2H roles or corrections. Exact explicit `phase2h-v1` opt-in binds source-pins, decision, delta, and materialized-view paths and SHA-256 values, then exposes only Packet C. Missing, partial, stale, wrong-version, wrong-path, wrong-hash, altered, or over-broad input refuses closed; no refusal is reported as a successful fallback.

## Ignored-artifact envelope

| Repository-relative path | Bytes | SHA-256 |
| --- | ---: | --- |
| `out/prototype-archaeology/phase2h/materialized-reviewed-semantic-view.json` | 3305 | `68BB58AB87D064F28C5616DEB3BE18749DE0D58BF3FAB5B161035E76650748EA` |
| `out/prototype-archaeology/phase2h/receipts/consistency.json` | 1863 | `D8DBCDB8B8109F332DD0439042BDBFDF1BD56BAA55F8F1AC14E7B41D22739A9E` |
| `out/prototype-archaeology/phase2h/receipts/decision.json` | 1298 | `5246B9F95C4C9209367C61A6945D57A55F61EB1DF25C932BFA5B8CCECF913A83` |
| `out/prototype-archaeology/phase2h/receipts/default.json` | 1069 | `C0F1F385001ADCE9DF34C19DA4FC1B918898EAD3A480C67140E924758B5D9997` |
| `out/prototype-archaeology/phase2h/receipts/delta.json` | 687 | `DE96D57E705B8CBAFC12A750227EE172F354288915FF640D9242497FA1A78226` |
| `out/prototype-archaeology/phase2h/receipts/git-delta.json` | 1605 | `A99447F8912930284F5E83855D74AF08BF0D6C69E34847E856046CB2F845D30B` |
| `out/prototype-archaeology/phase2h/receipts/negative-controls.json` | 579 | `6EA4106AC174363E176F3C9BF55B4F12EAAB58D56A864A4FC1CE74FCB8A0C973` |
| `out/prototype-archaeology/phase2h/receipts/opt-in.json` | 1392 | `066DE090733893440550F70558A0CDECE1B972E40CD828FD04820C74298EF08B` |
| `out/prototype-archaeology/phase2h/receipts/path-audit.json` | 539 | `4A86C3BF1D2BA418E16EE87A590D97472223AC3795E3AA73515BD21D453C0CD4` |
| `out/prototype-archaeology/phase2h/receipts/replay.json` | 671 | `1CE2A542CA2ACCFB7A7680F686838601162549DD48854253A012013E41848F44` |
| `out/prototype-archaeology/phase2h/receipts/schemas.json` | 575 | `AD327A81FA0163910E2F00E2411EBD3E1A8797C2D0BE3E0D54B5D8DABB901208` |
| `out/prototype-archaeology/phase2h/receipts/tamper-controls.json` | 574 | `01F5DFDE33AB84FD65AF300AE34A60B7B1F7BFA9001499A7152B5A42787AC3E0` |
| `out/prototype-archaeology/phase2h/receipts/tests.json` | 713 | `3887675D165DFDF3E8D34362365A9F7FB4C2C71720849AC007A0A78B8CB4406A` |
