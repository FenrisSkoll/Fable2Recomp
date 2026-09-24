# Fable II fault-walk Harvest 003

## Run identity

- Mode: `DISPATCH_ONLY`
- Runtime log: `C:\Dev\Fable2Recomp\fable2-run-010.log`
- Run directory: `C:\Dev\Fable2Recomp\out\fault-walk-runs\iteration-08`
- Report: `fault-walk-report.json`
- Started: `2026-08-27T23:15:41.0831708+01:00`
- Completed: `2026-08-27T23:39:09.9883722+01:00`
- TU1 dump SHA-256:
  `5A6ADBDA1714AABC63BD7F6D52B55BCAAAD9B6F3F81907D93C1FFE830B22E59F`
- Exit: controlled fault-walk guardrail abort, `0xC0000409`

The process reached coherent, user-controlled Bowerstone Old Town gameplay and
progressed through the child-era errands. Captures in the iteration directory
show the magical-items scene, live quest interaction, quest progress, and
continued movement after the first three synthetic returns.

No exact FPS sample was collected in this run; gameplay benchmarking was
reserved to the user. Visual response and progression were materially better
than the previous 4-5 FPS report, but that is qualitative and must not be used
as a numeric benchmark.

## Ordered target list

All four events were invalid/unregistered dispatcher targets. Consequently
there is no generated recomp function/source file, host exception code, access
classification, or host fault address for any entry. Each used diagnostic
policy `RETURN_R3_ZERO`; none is a correctness fix.

### #001 `0x82C8A920`

- TU1 boundary: `[0x82C8A920,0x82C8A93C)`, size `0x1C`
- Generated function/source: none (unregistered)
- Original fatal: `Call to invalid or unregistered function: target=0x82C8A920, ctx.lr=0x82480818, probable caller=0x82480814, ctx.ctr=0x82C8A920`
- First hit: `2026-08-27 23:27:31.014`
- Suppressed invocations: `108`
- Static provenance: `.rdata` address `0x8200E920`, slot `26` of callback table
  `[0x8200E8B8,0x8200E940)`
- Behavior: reads an object at `r3+0x2C`; when its discriminator is `3`, copies
  the field at `+0x20` to `*r4`
- Confidence: **HIGH CONFIDENCE PRIMARY**. It was the first Harvest 003 target,
  before any synthetic return, and independently recurs from Harvest 002.

### #002 `0x82967540`

- TU1 boundary: `[0x82967540,0x82967550)`, size `0x10`
- Generated function/source: none (unregistered)
- Original fatal: `Call to invalid or unregistered function: target=0x82967540, ctx.lr=0x826EE590, probable caller=0x826EE58C, ctx.ctr=0x82967540`
- First hit: `2026-08-27 23:27:45.072`
- Suppressed invocations: `9`
- Static provenance: exact `r3` virtual-dispatch thunk, slot `0x98`,
  materialized at `0x826ECA60/0x826ECA68` and
  `0x82964DCC/0x82964DD4`
- Confidence: **HIGH CONFIDENCE PRIMARY**. It recurred fourteen seconds after
  the first target and has direct static callback-construction evidence.

### #003 `0x82DE2BA8`

- TU1 boundary: `[0x82DE2BA8,0x82DE2BC4)`, size `0x1C`
- Generated function/source: none (unregistered)
- Original fatal: `Call to invalid or unregistered function: target=0x82DE2BA8, ctx.lr=0x82D8E940, probable caller=0x82D8E93C, ctx.ctr=0x82DE2BA8`
- First hit: `2026-08-27 23:27:54.134`
- Suppressed invocations: `327`
- Static/runtime provenance: real adapter thunk that tail-dispatches vtable
  slot `0x24`; reached through the runtime-populated indexed table lookup in
  `0x82E060F8` (`0x82E06168-0x82E06194`)
- Confidence: **LIKELY PRIMARY**. It recurred nine seconds after #002 with only
  two earlier synthetic returns. This substantially supersedes Harvest 002's
  state-corruption-secondary classification, though the table's ultimate
  initialization remains unresolved.

### #004 `0x82E8C8E8`

- TU1 boundary: `[0x82E8C8E8,0x82E8C92C)`, size `0x44`
- Generated function/source: none (unregistered)
- Original fatal: `Call to invalid or unregistered function: target=0x82E8C8E8, ctx.lr=0x82E905B0, probable caller=0x82E905AC, ctx.ctr=0x82E8C8E8`
- First hit: `2026-08-27 23:39:06.433`
- Suppressed invocations: `250000`
- Static provenance: `.rdata` address `0x82002754`, slot `22` of callback table
  `[0x820026FC,0x82002784)`; neighboring entries are generated
- Behavior: scans an object-pointer array and returns whether an entry's
  vtable field at `+0x84` equals `r4`
- Confidence: **LIKELY PRIMARY** as an indirect-discovery miss because its
  boundary and callback-table membership are direct TU1 evidence. The
  subsequent 250,000-iteration loop is **LIKELY STATE-CORRUPTION SECONDARY**:
  synthetic `false` prevented the caller's expected progress.

## Guardrail and totals

- Unique targets: `4`
- Fault hits: `4`
- Suppressed invocations: `250444`
- Maximum unique: `4/32`
- Maximum total suppressions: `250444/1000000`
- Maximum per-function suppressions: `250000/250000`
- Stop reason: `per-function suppression limit reached for invalid target 0x82E8C8E8 (250000)`
- Host `ACCESS_VIOLATION` faults: not enabled in dispatcher-only mode; none
  escaped before the guardrail
- Host `INTEGER_DIVIDE_BY_ZERO` faults: not enabled in dispatcher-only mode;
  none escaped before the guardrail
- Fatal lines: none

The target and first-hit record for `0x82E8C8E8` were written before the
guardrail stopped the process. The exact `0xC0000409` exit is the host result of
the deliberate `std::abort` after report and summary emission, not an unknown
guest failure.

The preserved report's `mode` field correctly says `DISPATCH_ONLY`, but its
generic warning still says that `PPCContext` was restored. Dispatcher-only mode
never executed these missing target bodies and performed no checkpoint restore.
The SDK wording was corrected after this run so future dispatcher reports say
that invalid bodies were not executed and synthetic returns can alter later
guest state; the harvested raw evidence was not rewritten.

## Comparison with Harvest 002

All five new manifest corrections disappeared:

- `0x829675D0`: absent; previous suppressions `5`
- `0x829675C0`: absent; previous suppressions `13919`
- `0x8288ACB0`: absent; previous suppressions `1`
- `0x8288ACC0`: absent; previous suppressions `1`
- `0x82964820`: absent; previous suppressions `1`

Thus all `13927` suppressions associated with the corrected functions
disappeared, including the complete `0x829675C0` storm. Harvest 001's three
corrected targets also remained absent.

The three deferred Harvest 002 targets recurred in the same relative order:

| Target | Harvest 002 | Harvest 003 | Updated assessment |
|---|---:|---:|---|
| `0x82C8A920` | `54` | `108` | high-confidence primary |
| `0x82967540` | `9` | `9` | high-confidence primary |
| `0x82DE2BA8` | `325` | `327` | likely primary |

Harvest 003 then exposed entirely new `0x82E8C8E8`. Total suppressions are not
directly comparable (`14315` versus `250444`) because the new synthetic false
result induced a hot loop and intentionally hit the configured guardrail.

## Assessment

The next correctness pass should add the four TU1-proven functions in ordered
priority `0x82C8A920`, `0x82967540`, `0x82DE2BA8`, `0x82E8C8E8`, regenerate,
and run the normal build first. In particular, fixing `0x82E8C8E8` is necessary
before another long harvest: tolerating it as false produces no useful further
evidence and reaches the per-function guardrail almost immediately.

The run strengthens the systematic-discovery diagnosis. Three targets are in
non-RTTI or runtime-populated callback tables, and one is a code-materialized
callback thunk. Further broad fault-walker optimization is lower priority than
correcting these proven misses and improving reviewed indirect candidate
discovery. FULL host-SEH walking is not yet indicated: both Fable harvests have
continued to expose only invalid dispatcher targets.
