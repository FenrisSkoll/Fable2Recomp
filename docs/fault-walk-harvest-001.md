# Fault-walk harvest checkpoint 001

Date: `2026-08-27`

This is diagnostic evidence, not a correctness result. Fault walking returns
synthetic values and does not roll back guest-memory writes. Later discoveries
can therefore be secondary.

## Run

- Fault-walk iteration: `iteration-06`
- Process: `fable2.exe`, PID `20048`
- Runtime log: `C:\Dev\Fable2Recomp\fable2-run-006.log`
- Machine report:
  `C:\Dev\Fable2Recomp\out\fault-walk-runs\iteration-06\fault-walk-report.json`
- Run result:
  `C:\Dev\Fable2Recomp\out\fault-walk-runs\iteration-06\result.json`
- TU1 capture SHA-256:
  `DCBE6C06F6BD186C08D6C867782781E201072A120DE078D8666BFE4E9CCB11D9`
- Furthest observed state: controllable childhood gameplay in Bowerstone Old
  Town, after the opening cinematic.
- Stop reason: user-requested graceful close.
- Exit code: `0x00000000`
- Guardrail state: no guardrail reached (`3/32` unique, `161/1000000`
  suppressions, maximum per-function suppression `101/250000`).

The run proved that three independent invalid/unregistered guest targets could
be recorded and bypassed in one process without rebuilding or restarting.
No allowlisted host SEH exception occurred in this Fable II harvest.

## Ordered findings

### #001 `0x82C03B28` — HIGH CONFIDENCE PRIMARY

- Kind: `invalid_unregistered_function`
- Generated function/source: not generated; the target was unregistered
- First seen: `2026-08-27 20:57:41.540`
- Original fatal:
  `Call to invalid or unregistered function: target=0x82C03B28, ctx.lr=0x821907A8, probable caller=0x821907A4, ctx.ctr=0x82C03B28`
- Previous guest function: `0x82190728`
- Thread: `13284`
- `r1=0x000000007033FDB0`
- `r2=0x0000000000000000`
- `r3=0x00000000442B99B0`
- `r4=0x0000000000000000`
- `r5=0x0000000000000000`
- `r6=0x0000000000000000`
- `r7=0x01DD365E00000000`
- `r8=0x0000000051DE37AB`
- `r9=0x0000000082C03B28`
- `r10=0x000000008200A188`
- Guest stack: `0x82CD0C60 -> 0x82B3D8E8 -> 0x82C0E360 -> 0x82C03BD0 -> 0x82C03860 -> 0x82190728`
- Policy: `RETURN_R3_ZERO`
- Fault hits: `1`
- Suppressed invocations: `0`
- Confidence basis: this was the first tolerated event, before any accumulated
  fault-walk side effects.

### #002 `0x829647F0` — HIGH CONFIDENCE PRIMARY

- Kind: `invalid_unregistered_function`
- Generated function/source: not generated; the target was unregistered
- TU1 boundary: already confirmed as `0x829647F0` through exclusive end
  `0x82964800` (`size = 0x10`); the exact prospective manifest line is
  `"0x829647F0" = { size = 0x10 }`
- First seen: `2026-08-27 20:57:41.557`
- Original fatal:
  `Call to invalid or unregistered function: target=0x829647F0, ctx.lr=0x829641C8, probable caller=0x829641C4, ctx.ctr=0x829647F0`
- Previous guest function: `0x82964078`
- Thread: `1812`
- `r1=0x00000000701BEF30`
- `r2=0x0000000000000000`
- `r3=0x0000000040695D10`
- `r4=0x000000004294FC70`
- `r5=0x000000004F640220`
- `r6=0x000000004F72C890`
- `r7=0x0000000000000001`
- `r8=0x000000004F72C898`
- `r9=0x0000000000000001`
- `r10=0x00000000829647F0`
- Guest stack: `0x822F4CE8 -> 0x82313278 -> 0x82276D10 -> 0x821C8FB0 -> 0x821762C0 -> 0x821D4628 -> 0x82281FE0 -> 0x8219A758 -> 0x8219A840 -> 0x82277C38 -> 0x82A24808 -> 0x82228B70 -> 0x822DD908 -> 0x82228730 -> 0x82465B50 -> 0x82964078`
- Policy: `RETURN_R3_ZERO`
- Fault hits: `1`
- Suppressed invocations: `60`
- Confidence basis: this exact fatal was independently reproduced in
  `fable2-run-005.log` before invalid-target tolerance was enabled. It occurred
  only 17 ms after finding #001 in this run.

### #003 `0x829675E0` — LIKELY PRIMARY

- Kind: `invalid_unregistered_function`
- Generated function/source: not generated; the target was unregistered
- First seen: `2026-08-27 20:58:41.994`
- Original fatal:
  `Call to invalid or unregistered function: target=0x829675E0, ctx.lr=0x82966EE8, probable caller=0x82966EE4, ctx.ctr=0x829675E0`
- Previous guest function: `0x82966D80`
- Thread: `1812`
- `r1=0x00000000701BEF00`
- `r2=0x0000000000000000`
- `r3=0x00000000429AE750`
- `r4=0x0000000000000002`
- `r5=0x0000000000000002`
- `r6=0x000000004F6DC728`
- `r7=0x0000000000000001`
- `r8=0x000000004C7BC010`
- `r9=0x0000000000000020`
- `r10=0x00000000429AE750`
- Guest stack: `0x822F4CE8 -> 0x82313278 -> 0x82276D10 -> 0x821C8FB0 -> 0x821762C0 -> 0x821D4628 -> 0x821B9258 -> 0x821AC8B0 -> 0x8219A840 -> 0x82277C38 -> 0x82A24808 -> 0x82228B70 -> 0x822DD908 -> 0x82228730 -> 0x8281E050 -> 0x82966D80`
- Policy: `RETURN_R3_ZERO`
- Fault hits: `1`
- Suppressed invocations: `101`
- Confidence basis: the target is a genuine missing registration, but its
  discovery followed approximately one minute of synthetic execution. Whether
  this exact path is normally reached still needs a correctness run after the
  earlier primary issues are fixed.

## Continuation

When work resumes, preserve the already-confirmed `0x829647F0` boundary and
perform boundary-only TU1 disassembly for `0x82C03B28` and `0x829675E0`.
Establish their exact starts, sizes, and exclusive ends before adding manifest
entries. Do not infer sizes from the call targets alone. Then regenerate and
validate both ordinary and fault-walk builds before the next numbered harvest.

The fault walker itself remains experimental tolerance. A manifest entry is
also only the correct remedy if TU1 bytes prove that the target is a real,
missing PPC function boundary.
