# Prototype Archaeology Phase 2B handoff

Phase 2B should attach semantic evidence to selected high-confidence binary correspondences. It
must consume Phase 2A mappings as evidence, not convert coverage into names automatically. Keep
shader-bank and proprietary resource-container parsing on a separate future track.

## Ranked work

1. **Native XREF recovery from distinctive semantic anchors.** Start with Phase 1 prototype debug
   strings, RTTI/type strings, assertions, source-file paths, subsystem/profiling strings, and the
   curated script-symbol set. Recover the exact donor instruction/data XREFs and registration or
   call context. Join only through Phase 2A `accepted-exact-unique` or
   `accepted-normalized-corroborated` records, retaining the original source path/string offset,
   XREF instruction address, donor/target pair, evidence grade, and every contradiction.

2. **Debug-command and Lua registration-table recovery.** Replace Phase 1's unsuccessful simple
   pointer-window heuristic with static structure recovery: locate string arrays, materialized
   address construction, table stride/repetition, constructors, registration loops, and callback
   stores/calls. Require an executable-boundary callback plus table/loop structure; a nearby data
   pointer or script spelling alone is insufficient.

3. **Mapped direct-call neighbourhood expansion.** Seed a labelled evidence graph only from
   distinctive anchors established in steps 1–2. Expand over Phase 2A's mapped call observations,
   reciprocal accepted pairs, and local ordering/delta records. Rank candidates by independent
   anchor agreement and graph consistency, while retaining ambiguity instead of greedily naming
   neighbours.

4. **Stable data/global anchors.** Exploit Phase 1's `99.02%` same-address `.data` similarity by
   content-hashing bounded objects, recovering prototype and TU1 XREFs, and testing structure/use
   consistency. Same address or matching 16-byte content is corroboration only; acceptance should
   require compatible access pattern and mapped call neighbourhood.

5. **Target current recompilation problems.** Produce reviewable evidence for unresolved indirect
   ownership/targets, crash-address interpretation, and renderer subsystem boundaries. Prioritize
   anchors that connect to the authoritative entrypoint closure and existing ownership schemas.
   Do not mass-rename functions or edit the manifest as part of evidence generation.

## Proposed schema and algorithm boundary

Add a versioned semantic-anchor dataset keyed by donor and canonical image identities plus the
Phase 2A input-bundle hash. Each record should contain the literal anchor, source evidence identity
and offset/line, donor XREF instructions, recovered registration/table context, linked accepted
correspondence record, target XREF/use context, evidence grade, negative/contradictory evidence,
and a terminal review status. Keep proposed names separate from accepted binary mappings and from
canonical symbol sources.

A useful staged algorithm is: exact anchor deduplication -> donor XREF/materialization recovery ->
registration/data-structure proof -> Phase 2A accepted-pair join -> target-side structural/XREF
verification -> call/data graph corroboration -> bounded human review. Generic strings, source
paths without XREFs, opcode-only pairs, and same-address globals should remain below acceptance.

## Pinned external candidate evidence

Record the following only as **unverified external/community runtime evidence**:

- repository file:
  `https://github.com/JustSomeGuy1234/Fable2Modding/blob/main/Functions%20and%20Tables%20I%20found.txt`
- pinned commit: `8ba7f3d9807e8566475afb5e54f478b235fc309a`
- reported provenance: a hand-typed, incomplete catalogue produced by enumerating a live Fable II
  Lua environment;
- limitations: it contains no native guest addresses and does not authorize correspondence,
  TU1 renaming, manifest changes, or Phase 2A acceptance-score changes.

Potential anchors include `Debug.ReloadShaderBank`, `Debug.StartLoggingShadersInUse`,
`Debug.FlushMeshes`, `Debug.ProfileEngine`, `Kynapse`, `Navigation`, `Perception`, `GDB`,
`GraphicAppearance`, and `EnvironmentTheme`, plus argument/behaviour observations. It also reports
that `gamescripts.bnk` retains debug information while `gamescripts_r.bnk` contains smaller,
stripped runtime scripts.

Phase 2B should provenance-pin and locally parse the exact committed file, deduplicate its entries,
and cross-reference them against prototype scripts, TU1/prototype strings, native XREFs, and proven
registration-table structures before accepting any semantic association. This source was not
fetched, ingested, validated, or used by Phase 2A.
