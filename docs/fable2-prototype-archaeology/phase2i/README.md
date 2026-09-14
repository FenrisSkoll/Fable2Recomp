# Phase 2I — opt-in analyst annotations

Phase 2I generates and previews read-only analyst annotations from the frozen
Phase 2A/2E mapping and Phase 2F–2H semantic evidence. It never opens a Ghidra
project, emits a name, changes a mapping, or modifies runtime/production data.

The safe default has mapping view `none` and semantic view `none`. No annotation
or export is produced without an explicit selection. The closed 15,299-pair map
is queryable only as `closed-phase2a-default`; the 15,379-pair overlay is usable
only as `phase2e-v1` with its exact three paths and SHA-256 values. Phase 2F and
Phase 2H semantics are separately selected. Exact commands are added alongside
the implemented query/export interface in the next logical commit.

Source binding is offline and read-only:

```powershell
python -B tools/phase2i/Fable2AnalystSources.py --check
```

All writes are physically confined to
`docs/fable2-prototype-archaeology/phase2i/` and
`out/prototype-archaeology/phase2i/`.
