# NR0B-2 reading and accepted provenance

Both canonical repositories were inspected before edits. Fable began on
`fable2-native-renderer-nr0b1-preparation`, HEAD
`d292ccc36cc4b97d4171431308cedec7e5591a28`, tree
`2d9f9d3e7454e587b7fe96ccd0eed486dd6050f4`. SDK
`C:\Dev\rexglue-sdk-v0.10` began on
`fable2-native-renderer-nr0b1-config-reporting`, HEAD
`06c4b7002a449ad4d173ec90c625e490ed03fe74`, tree
`5feea2389d0ce264ab970bf7807ee4ae6bd7960d`. No newer accepted checkout changes
were present. Neither NR0B-2 branch existed; dedicated local branches named
`fable2-native-renderer-nr0b2-metadata` were created from those exact heads.

The root AGENTS.md and supplied instructions apply. No additional applicable
SDK/ancestor instructions were found. The initial preservation audit is
`out/nr0b2/initial-state.json`: full source/preserved inventories, baseline
artifacts, historical NR0B-1 document identities, manifest and 15 libmspack files.
The manifest raw SHA-256 remains
`EF1656D77D270F207C4A16D3B92D5B86C4414CE38292D079AEF52B120CE778E1`.
Libmspack gitlink remains `305907723a4e7ab2018e58040059ffb5e77db837`.
Neither unrelated change is part of an NR0B-2 commit.

## Consulted authority

- [Project index](../../../README.md), [GPU index](../../fable2-gpu-reference/README.md), SDK README and existing GPU reporting documentation.
- [NR0A index](../nr0a/README.md), [architecture](../nr0a/architecture-decision.md), [ownership](../nr0a/ownership-and-transition-contract.md), [evidence plan](../nr0a/nr0b-evidence-plan.md), [gates](../nr0a/implementation-gates.md).
- [NR0B-1 index](../nr0b1/README.md), [preparation](../nr0b1/preparation-and-provenance.md), [configuration](../nr0b1/effective-configuration.md), [runtime closeout](../nr0b1/runtime-closeout.md), [handoff](../nr0b1/nr0b2-handoff.md), [run card](../nr0b1/user-run-card.md), [completion](../nr0b1/nr0b1-completion.md), reviewed runtime ledger.
- [Save contract](../../fable2-native-save-write-parity.md), [session/log contract](../../fable2-discovery-pipeline/coverage/README.md), [accepted Oakfield endpoint](../../fable2-discovery-pipeline/09-phase5a-tranche-001.md), [G2A retirement](../../fable2-gpu-reference/g2a-retirement.md).
- Existing `Fable2GpuConfig.py`, `Invoke-Fable2GpuConfig.ps1`, their tests, SDK configuration reporter source/call sites, live numbered-log allocator, Release caches/build wiring and actual consumer GPU paths.

Accepted starting runtime evidence is PID 27668, `fable2-run-004.log`, actual
exit 0; log 003 is excluded. RTX 5080 / `32.0.16.1664`, Xenos/D3D12, RTV,
bindless/tiled enabled, scale 1x, ROV supported, binding tier 3, tiled tier 4,
alpha blend-factor supported. First guest output 1280x720 and first host present
3840x2160 do not establish one global internal resolution. Release binaries did
not require Tracy. Black/blank character and dog surfaces remain unexplained.
NR0B-1 is complete and its reports are not rewritten or rerun.

## Source-confirmed joins added

Common type-3 handling filters predicates before IssueDraw and additionally
rejects visibility-query draws. IssueDraw has successful no-op/copy/not-ready
returns. Render-target/texture preparation can produce auxiliary operations.
DeferredCommandList::Execute can suppress draw/dispatch when its pipeline is
null. These findings require separate decision, deferred operation, native
invocation, submit and completion records. The existing deferred stream offset
plus submission ID provides a bounded join without a resource-lifetime map.

Initial shader and fetch state is sampled from applicable consumer objects;
it may predate the window. Existing analysis/translation results are reused.
No producer/title caller can be recovered from these records. The G1.6
limitations inherited through NR0A/NR0B-1 remain sufficient: no external survey,
broad historical corpus reconstruction or retired G2A code was needed.

## Protected checkpoint

Authoritative preserved source for the new copy:
`C:\Dev\Fable2Recomp\out\nr0b1\checkpoints\nr0b1-oakfield-20260910-001\user-data`.
It matches all 14 files of
`C:\Dev\Fable2Recomp\out\phase5a\checkpoints\end-001-native\user-data`.
Main save: 415039 bytes,
`13FC340F6869DA73CB958BA36CB50905E29B8FBEA073CEFF46490DB4A9812489`.
The mutable post-NR0B-1 working save is excluded. New preserved and writable
copies retain all seven Hero000 payloads, native/platform/profile metadata and
the two small existing cache files. Driver-cache contents remain unknown.
