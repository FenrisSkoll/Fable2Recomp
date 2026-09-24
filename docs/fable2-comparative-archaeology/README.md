# Independent comparative archaeology: himdo/Fable-2-Recomp

Audit date: 2026-09-24. External commit:
[`2bdf8f93a0edcec599023ce9382ca284a7e92c06`](https://github.com/himdo/Fable-2-Recomp/tree/2bdf8f93a0edcec599023ce9382ca284a7e92c06).

The audit is complete within its stated evidence limits. It adds contextual TU1
knowledge and a repeatable provenance check, without changing game behavior,
function ownership, manifests, generated code, renderer, or the SDK.

- [Audit report](himdo-audit-report.md): findings, revision rebasing, provenance and validation.
- [Curated leads](external-leads.json): 35 attributed findings; confidence applies to the delimited local evidence.
- [Exhaustive name inventory](evidence/external-functions.csv): all 4,970 external manifest names, candidate rebases and unresolved status.
- [Coverage/boundary inventory](evidence/inventory.json): all 86 explicit sizes, 846 switch hints and comparison counts.
- [Feature comparison](feature-comparison.md), [risk register](architectural-risk-register.md), [follow-ups](follow-ups.md).
- [Starting state](evidence/starting-state.json), [source pins](evidence/external-source-pins.json),
  [independent boundaries/sections](evidence/independent-boundaries.json),
  [provenance receipt](evidence/provenance.json), [validation](evidence/validation.json).

External names are leads, not canonical symbols. Branch-masked or relative-table
matches are candidates, not ownership or semantic proofs. `CONFIRMED` local
mechanics can coexist with `PARTIALLY_CORROBORATED` external claims. A raw
address match never establishes equivalence across the base/TU1 boundary.

Only metadata is tracked here. Private images, regenerated sources, disassembly
and large logs remain in ignored `out/comparative-audit/`. The external clone
is outside both canonical repositories and is not a dependency.

Reproduce the provenance experiment using [the probe instructions](../../tools/xex-provenance/README.md).
The exhaustive census is read-only with respect to all inputs:

```powershell
python -B -X utf8 tools/Fable2ComparativeInventory.py `
    --external C:\Dev\comparison\himdo-Fable-2-Recomp `
    --commit 2bdf8f93a0edcec599023ce9382ca284a7e92c06 `
    --base-snapshot out/comparative-audit/base-image `
    --tu1-snapshot out/comparative-audit/tool-final `
    --output out/comparative-audit/inventory
```

The base snapshot was produced with the same load-only probe, tool mode, and an
isolated directory containing only our hash-verified base `default.xex`, with
no sibling XEXP. It is not an external project's generated image. The census
requires exact expected image hashes and a clean external checkout at the pin.
It never proposes executable changes automatically.
