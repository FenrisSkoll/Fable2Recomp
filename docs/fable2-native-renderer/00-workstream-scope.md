# Fable II native renderer: workstream scope

## G1 decision

**Result: PASS WITH LIMITATIONS.** Fable II GOTY TU1 has an interception
boundary above ReXGlue's raw Xenos command processor. Static Xbox graphics
functions can be intercepted while the original generated implementation is
retained as the forwarding target. G1 confirms device lifecycle, ring setup,
shutdown, and present-related functions. It does **not** yet identify the full
resource/state/shader/draw method set, and it does not confirm a stable
Lionhead rendering-abstraction boundary.

This is a new native-renderer workstream, not Phase 5 of function discovery.
The validated `rexgpu-xenos.dll` path remains canonical and unchanged.

## Scope and evidence rules

G1 answers whether a safe title-specific interception strategy is feasible. It
does not implement hooks, capture, shader conversion, replay, or a native
backend. Findings use the project evidence labels:

- **CONFIRMED**: demonstrated by exact TU1 generated code, exact-image Ghidra
  metadata, runtime/ReXGlue source, or repository identity.
- **STRONG HYPOTHESIS**: multiple independent observations agree, but the title
  has not established the complete semantic contract.
- **WEAK HYPOTHESIS**: useful discovery lead without enough evidence for a
  hook.
- **UNKNOWN**: no address is assigned. Unknown methods are not renamed to fit
  an expected D3D API.

Function ranges use exclusive ends. Generated instruction comments establish
the contiguous range only where they match TU1 control-flow boundaries; Ghidra
`.pdata` associations corroborate entry identity but are not treated as body
ends. The machine-readable evidence is
[`candidate-hook-inventory.json`](candidate-hook-inventory.json).

## Canonical local identities

The Fable repository was clean before branch creation. The validated
post-Phase-4 starting point was unambiguous from
[`../fable2-discovery-pipeline/05-xenia-indirect-targets.md`](../fable2-discovery-pipeline/05-xenia-indirect-targets.md)
and recent history.

| Repository | Starting branch | Starting HEAD | Starting tree | State |
|---|---|---|---|---|
| `C:\Dev\Fable2Recomp` | `fable2-phase4-indirect-targets` | `a60603f737ff5da65d9a643e8a24de0907bd997d` | `98a88d6c74fd6535be899905b1b3f463b4b37488` | clean; no submodules |
| `C:\Dev\rexglue-sdk-v0.10` | `fable2-v0.10-migration` | `956c6a8b5da4c54b9899a2593e9c67c26de30194` | `b78b06b8ac650467372236a3a262864e069a9382` | tracked tree unchanged; pre-existing nested `thirdparty/libmspack` Windows symlink materialization at pinned `305907723a4e7ab2018e58040059ffb5e77db837` |

G1 work was performed on local Fable branch
`fable2-native-renderer-g1-audit`. No SDK branch was created. SDK source was
read-only. The repositories' remotes, all SDK submodule pins, untracked state,
and recent history were audited before investigation.

## Exact target identity

| Evidence | Exact value |
|---|---|
| Title | Fable II Game of the Year Edition, Xbox 360 TU1 |
| Title / media / version | `0x4D5307F1` / `0x716F0A0D` / `0.0.1.26` |
| Base XEX SHA-256 | `88C4EF2E18E65409444D1B068EFF921D1F7E180A5AE64EDC64BA6B0872372662` |
| XEXP SHA-256 | `046A05693B4DA4437083C784000A850858B3BF992955C7DB30D518FB3E53E41C` |
| Loaded post-patch image SHA-256 | `BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00` |
| Executable-memory fingerprint | `5C8B78B84C93028D166E3DF347206E6642BA40BF374AD1AF8D958B2211320357` |
| Image base / size / entry | `0x82000000` / `0x01620000` / `0x82CC21C0` |
| Executable ranges | `.text [0x82170000,0x832BABBC)`; `BINK [0x832BAC00,0x832CA03C)` |
| Manifest SHA-256 | `E3EB39CA153E396D5DC53E6F943ED8FF7AF1D6B0704EB860836BD7D21A3F87B0` |

These identities come from the versioned discovery evidence contract. See
[`../fable2-discovery-pipeline/01-static-entrypoint-closure.md`](../fable2-discovery-pipeline/01-static-entrypoint-closure.md),
[`../fable2-discovery-pipeline/02-ghidra-function-map.md`](../fable2-discovery-pipeline/02-ghidra-function-map.md),
[`../fable2-discovery-pipeline/03-jump-table-recovery.md`](../fable2-discovery-pipeline/03-jump-table-recovery.md),
and the Phase 4 handoff rather than copying older discovery counts here.

## Pinned external references

Sources were cloned outside both tracked repositories under
`C:\Dev\Fable2NativeRendererResearch`. Dates are commit dates in ISO 8601.

| Source | Branch | Commit | Commit date | Licence and G1 use |
|---|---|---|---|---|
| [UnleashedRecomp](https://github.com/hedge-dev/UnleashedRecomp/tree/cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c) | `main` | `cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c` | `2026-06-29T14:05:43+03:00` | GPL-3.0; architectural evidence only, no code copied |
| [XenosRecomp](https://github.com/hedge-dev/XenosRecomp/tree/990d03b28a27b50277ee5d8d942e1c5f873869d1) | `main` | `990d03b28a27b50277ee5d8d942e1c5f873869d1` | `2025-08-03T16:45:31+03:00` | MIT; potentially reusable subject to title validation |
| [Plume](https://github.com/renderbag/plume/tree/d890ac899e505fb30040e037a4037cdeca68f033) | `main` | `d890ac899e505fb30040e037a4037cdeca68f033` | `2026-07-22T20:03:40-03:00` | MIT; reusable backend abstraction candidate |
| [ReXGlue SDK](https://github.com/rexglue/rexglue-sdk/tree/c94f5ebdcb3c9d1a460ca48e04f9758448f8d518) | `main` | `c94f5ebdcb3c9d1a460ca48e04f9758448f8d518` | `2026-08-21T15:11:28-07:00` | BSD-3-Clause; authoritative public v0.10 reference |
| [Xenia](https://github.com/xenia-project/xenia/tree/95a5c3ee250f80c3b9d139658649d9ffb6db3eec) | `master` | `95a5c3ee250f80c3b9d139658649d9ffb6db3eec` | `2026-02-18T22:40:20+03:00` | BSD-3-Clause; behavioural/packet reference |
| [Xenia Canary](https://github.com/xenia-canary/xenia-canary/tree/3a44f20c7bc66db1da583e8a6f0ab740e31908e9) | `canary_experimental` | `3a44f20c7bc66db1da583e8a6f0ab740e31908e9` | `2026-08-31T22:07:04+02:00` | BSD-3-Clause; behavioural/packet reference |

UnleashedRecomp pins Plume `11926860e878e68626ea99ec88562ce2b8badc4f`
and XenosRecomp `990d03b28a27b50277ee5d8d942e1c5f873869d1`
as submodules. G1 separately inspected current Plume because the objective asks
about its present architecture. Licence compatibility remains a design gate:
do not transplant UnleashedRecomp's GPL implementation into this workstream
without an explicit project licensing decision.

## Non-goals and private-data policy

No proprietary executable bytes, shader bytecode, textures, assets, saves,
captures, or Ghidra databases are part of the deliverables. Private analysis
stayed under ignored `out/` paths or outside the repositories. Metadata such as
addresses, ranges, hashes, string labels, and xrefs is recorded only when it is
needed to reproduce a conclusion.

The remaining G1 documents are:

- [`01-current-gpu-data-path.md`](01-current-gpu-data-path.md)
- [`02-unleashed-recompiled-reference.md`](02-unleashed-recompiled-reference.md)
- [`03-candidate-hook-inventory.md`](03-candidate-hook-inventory.md)
- [`04-architecture-options.md`](04-architecture-options.md)
- [`05-shadow-capture-design.md`](05-shadow-capture-design.md)
- [`06-risk-register.md`](06-risk-register.md)
- [`g1-completion.md`](g1-completion.md)
