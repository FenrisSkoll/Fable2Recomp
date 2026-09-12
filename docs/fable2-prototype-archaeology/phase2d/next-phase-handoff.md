# Phase 2D handoff: owner review precedes adoption

The Phase 2D dossier is an analysis-only recommendation layer over frozen Phase 2C.
No mapping or name is canonical and every human decision remains pending.

Start with root AGENTS.md, Phase 2D README, report, policy, review guide, source pins,
validation and human decision ledger. Verify their exact bytes before using ignored
evidence. The full independent reconstruction, 803 packets, adversarial challenges,
715-proposal blocker index, known cases, seed graph, risk strata and simulations
remain under `out/prototype-archaeology/phase2d/`.

The 86 strong proposals independently recover the same target uniquely. The review
recommends 17 without reservation and 66 with reservation; three are held. All 715
probable proposals remain held, with no promotions. Both physics candidates remain
held. HammerCombat is an exclusion-guard context and has an internal-region
reservation, not a function name.

Smallest unresolved mapping-review targets:

- `0x82BC43E8 -> 0x82BC3FA8`: indirect call at +0x8C, TU1 `0x82BC4034`, writable target slot `0x83314BBC`.
- `0x82E510E0 -> 0x82E515D0`: indirect call at +0x40, TU1 `0x82E51610`, object/table slot +0x10.
- `0x82FB6620 -> 0x82FB6C50`: common `XBOX360 8,0,0,0` reference and non-distinctive mapped helper support.

The six frozen Phase 2C blockers remain unchanged. Required historical
`generated/default/fable2_recomp.136.cpp` SHA-256 is
`6053CC0EAC4636AA03AAA26581162B707C37E1B52BEE4C10F205D07C63EBDF59`; current SHA-256 is
`D25E664A98833BF9433413336AC92A7376102A67049C0FF35F1270E6BDEB44CB`. Phase 2D does
not authorize searching for, reconstructing or replacing it. No temporary runtime
instrumentation was introduced.

The next step is the external owner decision described in human-decision-guide.md.
Only a separately authorized task may construct or adopt an approved overlay.
Preserve suppression precedence, injectivity and exact approved-set dependencies.
Canonical naming, Ghidra database changes and runtime integration require their own
explicit scope. The adoption plan specifies reversible consumer switches and rollback.

Obtain exact local commit and ending tree identities without a self-referential hash:

```powershell
git log --format='%H %s' f13ee49c94db48d979de1346b7f67d2d82257ea2..fable2-prototype-archaeology-phase2d
git rev-parse fable2-prototype-archaeology-phase2d
git rev-parse 'fable2-prototype-archaeology-phase2d^{tree}'
git status --porcelain=v2
```
