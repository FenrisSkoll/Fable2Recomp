# Fault-walk harvest checkpoint 002

Date: `2026-08-27`

This is diagnostic evidence, not a correctness result. Fault walking returns
synthetic values and does not roll back guest-memory writes. In this run the
dominant poisoned target was suppressed `13919` times, so late discovery paths
must be treated as substantially state-divergent.

## Run

- Fault-walk iteration: `iteration-07`
- Process: `fable2.exe`, PID `15908`
- Manual input: enabled; the helper injected no keys
- Runtime log: `C:\Dev\Fable2Recomp\fable2-run-008.log`
- Machine report:
  `C:\Dev\Fable2Recomp\out\fault-walk-runs\iteration-07\fault-walk-report.json`
- Run result:
  `C:\Dev\Fable2Recomp\out\fault-walk-runs\iteration-07\result.json`
- TU1 capture SHA-256:
  `10D476AFD9F805979C0C008DC2A2DDE7F479DC9DBCF5ADCA60606F3BB71505B1`
- Duration: `2026-08-27T22:00:32.2373039+01:00` through
  `2026-08-27T22:30:52.3656921+01:00`
- Stop reason: configured monitor timeout followed by a graceful close
- Exit code: `0x00000000`
- Guardrail state: no guardrail reached (`8/32` unique, `14315/1000000`
  suppressions, maximum per-function suppression `13919/250000`)
- Recoverable host SEH faults: none
- Unknown/non-allowlisted exceptions: none

None of the three harvest-001 targets recurred after their manifest fixes.

## Ordered findings

Every item below was reached through indirect dispatch and was absent from the
generated function registry. TU1 disassembly confirms that every address is a
real function start rather than an interior, alignment, or corrupt target.
Function/source fields are null in the report because none had been generated.

### #001 `0x829675D0` — HIGH CONFIDENCE PRIMARY

- Exact TU1 range: `[0x829675D0, 0x829675E0)`, size `0x10`
- Form: `lwz r12,0(r3); lwz r11,148(r12); mtctr r11; bctr`
- Original fatal:
  `Call to invalid or unregistered function: target=0x829675D0, ctx.lr=0x822D2AA0, probable caller=0x822D2A9C, ctx.ctr=0x829675D0`
- Previous guest: `0x822D2950`; thread: `26020`
- Entry registers: `r1=0x00000000701BEF10 r2=0x0000000000000000 r3=0x00000000429AE830 r4=0x000000004299EA50 r5=0x0000000000000001 r6=0x000000004F699E40 r7=0x0000000000000001 r8=0x000000004F699E50 r9=0x0000000000000001 r10=0x00000000829675D0`
- Policy: `RETURN_R3_ZERO`; hits: `1`; suppressed: `5`
- Confidence basis: first fault in the run, before synthetic accumulation; it
  is an omitted member of the same thunk table as fixed `0x829675E0`.
- Prospective manifest line: `"0x829675D0" = { size = 0x10 }`

### #002 `0x829675C0` — HIGH CONFIDENCE PRIMARY

- Exact TU1 range: `[0x829675C0, 0x829675D0)`, size `0x10`
- Form: `lwz r12,0(r3); lwz r11,68(r12); mtctr r11; bctr`
- Original fatal:
  `Call to invalid or unregistered function: target=0x829675C0, ctx.lr=0x822D2AA0, probable caller=0x822D2A9C, ctx.ctr=0x829675C0`
- Previous guest: `0x822D2950`; thread: `26020`
- Entry registers: `r1=0x00000000701BEF10 r2=0x0000000000000000 r3=0x00000000429AE830 r4=0x000000004299EA50 r5=0x0000000000000001 r6=0x000000004F699DD8 r7=0x0000000000000001 r8=0x000000004F699DE0 r9=0x0000000000000001 r10=0x00000000829675C0`
- Policy: `RETURN_R3_ZERO`; hits: `1`; suppressed: `13919`
- Confidence basis: discovered 14 ms after #001 and before meaningful synthetic
  accumulation; independently a valid omitted thunk. Its high call volume made
  later execution materially divergent.
- Prospective manifest line: `"0x829675C0" = { size = 0x10 }`

### #003 `0x8288ACB0` — LIKELY PRIMARY

- Exact TU1 range: `[0x8288ACB0, 0x8288ACC0)`, size `0x10`
- Form: virtual dispatch through offset `20`
- Original fatal:
  `Call to invalid or unregistered function: target=0x8288ACB0, ctx.lr=0x8288BBB4, probable caller=0x8288BBB0, ctx.ctr=0x8288ACB0`
- Previous guest: `0x8288BB58`; thread: `26020`
- Entry registers: `r1=0x00000000701BED20 r2=0x0000000000000000 r3=0x00000000407159D0 r4=0x0000000000000002 r5=0x0000000000000002 r6=0x000000004F855B68 r7=0x0000000000000001 r8=0x000000004F855B70 r9=0x000000004F855B60 r10=0x0000000000000010`
- Policy: `RETURN_R3_ZERO`; hits: `1`; suppressed: `1`
- Confidence basis: genuine thunk adjacent to registered `0x8288ACA0`, but
  reached after substantial synthetic execution.
- Prospective manifest line: `"0x8288ACB0" = { size = 0x10 }`

### #004 `0x8288ACC0` — LIKELY PRIMARY

- Exact TU1 range: `[0x8288ACC0, 0x8288ACD0)`, size `0x10`
- Form: virtual dispatch through offset `8`
- Original fatal:
  `Call to invalid or unregistered function: target=0x8288ACC0, ctx.lr=0x8288B31C, probable caller=0x8288B318, ctx.ctr=0x8288ACC0`
- Previous guest: `0x8288B2E8`; thread: `26020`
- Entry registers: `r1=0x00000000701BD7E0 r2=0x0000000000000000 r3=0x00000000407159D0 r4=0x000000008288ACC0 r5=0x000000004F640220 r6=0x000000004F855C00 r7=0x0000000000000001 r8=0x000000004F855C10 r9=0x000000004F855C08 r10=0x0000000000000008`
- Policy: `RETURN_R3_ZERO`; hits: `1`; suppressed: `1`
- Confidence basis: genuine thunk contiguous with #003, but reached after
  substantial synthetic execution.
- Prospective manifest line: `"0x8288ACC0" = { size = 0x10 }`

### #005 `0x82964820` — POSSIBLE SECONDARY

- Exact TU1 range: `[0x82964820, 0x82964830)`, size `0x10`
- Form: virtual dispatch through offset `100`
- Original fatal:
  `Call to invalid or unregistered function: target=0x82964820, ctx.lr=0x8227DD40, probable caller=0x8227DD3C, ctx.ctr=0x82964820`
- Previous guest: `0x8227DBF0`; thread: `26020`
- Entry registers: `r1=0x00000000701BE5E0 r2=0x0000000000000000 r3=0x0000000040864290 r4=0x0000000042B6DAB0 r5=0x0000000000000001 r6=0x000000004F8D2678 r7=0x0000000000000001 r8=0x000000004F8D2680 r9=0x0000000000000001 r10=0x0000000082964820`
- Policy: `RETURN_R3_ZERO`; hits: `1`; suppressed: `1`
- Confidence basis: genuine thunk in the same region as fixed `0x829647F0`,
  but its reachability was observed after thousands of synthetic returns.
- Prospective manifest line: `"0x82964820" = { size = 0x10 }`

### #006 `0x82C8A920` — POSSIBLE SECONDARY

- Exact TU1 range: `[0x82C8A920, 0x82C8A93C)`, size `0x1C`
- Form: conditional leaf; for type `3`, copies offset `32` to `0(r4)`
- Original fatal:
  `Call to invalid or unregistered function: target=0x82C8A920, ctx.lr=0x82480818, probable caller=0x82480814, ctx.ctr=0x82C8A920`
- Previous guest: `0x824807C8`; thread: `26020`
- Entry registers: `r1=0x00000000701BDFF0 r2=0x0000000000000000 r3=0x00000000701BE420 r4=0x0000000042961580 r5=0x0000000000000001 r6=0x0000000000000490 r7=0x0000000000000490 r8=0x0000000000000020 r9=0x0000000000000001 r10=0x0000000082C8A920`
- Policy: `RETURN_R3_ZERO`; hits: `1`; suppressed: `54`
- Confidence basis: valid function between registered `0x82C8A910` and
  `0x82C8A940`, but discovered late after significant state divergence.
- Prospective manifest line: `"0x82C8A920" = { size = 0x1C }`

### #007 `0x82967540` — POSSIBLE SECONDARY

- Exact TU1 range: `[0x82967540, 0x82967550)`, size `0x10`
- Form: virtual dispatch through offset `152`
- Original fatal:
  `Call to invalid or unregistered function: target=0x82967540, ctx.lr=0x826EE590, probable caller=0x826EE58C, ctx.ctr=0x82967540`
- Previous guest: `0x826EE420`; thread: `26020`
- Entry registers: `r1=0x00000000701BDC80 r2=0x0000000000000000 r3=0x00000000427A17D0 r4=0x0000000042B9DC90 r5=0x0000000000000000 r6=0x0000000000000000 r7=0x0000000000000001 r8=0x000000004C7C2578 r9=0x0000000000000001 r10=0x00000000427A17D0`
- Policy: `RETURN_R3_ZERO`; hits: `1`; suppressed: `9`
- Confidence basis: valid member of the `0x829675xx` thunk table, but found
  late after thousands of suppressions.
- Prospective manifest line: `"0x82967540" = { size = 0x10 }`

### #008 `0x82DE2BA8` — LIKELY STATE-CORRUPTION SECONDARY

- Exact TU1 range: `[0x82DE2BA8, 0x82DE2BC4)`, size `0x1C`
- Form: argument adapter and virtual dispatch through offset `36`
- Original fatal:
  `Call to invalid or unregistered function: target=0x82DE2BA8, ctx.lr=0x82D8E940, probable caller=0x82D8E93C, ctx.ctr=0x82DE2BA8`
- Previous guest: `0x82E060F8`; thread: `26020`
- Entry registers: `r1=0x00000000701BA750 r2=0x0000000000000000 r3=0x000000004E2A1F10 r4=0x000000004E2A1F30 r5=0x0000000042618200 r6=0x00000000701BA920 r7=0x0000000000000000 r8=0xFFFFFFFF9E3779B1 r9=0x000000004C1454B0 r10=0x0000000000000128`
- Policy: `RETURN_R3_ZERO`; hits: `1`; suppressed: `325`
- Confidence basis: the boundary is genuine and neighboring adapters are
  registered, but this was the latest discovery after the most accumulated
  synthetic execution. Normal-path reachability is not yet established.
- Prospective manifest line: `"0x82DE2BA8" = { size = 0x1C }`

## Comparison with harvest 001

- Harvest 001: `3` unique targets, `161` suppressions.
- Harvest 002: `8` unique targets, `14315` suppressions.
- Recurring harvest-001 targets: none.
- New allowlisted host faults: none.
- The first two harvest-002 targets are adjacent siblings of corrected
  `0x829675E0`; `0x82964820` is a sibling of corrected `0x829647F0`.
- The repeated pattern is indirect-only leaf/thunk discovery, not a PPC
  translation failure. Exact manifest entries remain safer than speculative
  global gap-filling, which could misclassify data as code.

## Next correctness work

Prioritize normal-build fixes for `0x829675D0` and `0x829675C0`, then rerun the
normal path. Investigate `0x8288ACB0` and `0x8288ACC0` next. Treat the remaining
four as candidates requiring normal-path confirmation after the earlier state
divergence is removed. Do not treat their `RETURN_R3_ZERO` behavior as a fix.
