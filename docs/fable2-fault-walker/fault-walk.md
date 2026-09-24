# Experimental Fable II fault-walk workflow

Fault walking is a diagnostic build mode. It is intentionally incorrect, is
disabled by default, and must never be treated as a Fable II correctness fix.

Two diagnostic modes are available:

- `Dispatch` (the helper default) intercepts only invalid/unregistered
  `FunctionDispatcher` targets. Generated guest functions are not wrapped, so
  this mode has no per-generated-function checkpoint, TLS-stack, or Windows SEH
  cost and cannot recover host access violations or divide-by-zero faults.
- `Full` retains generated-function boundaries, complete `PPCContext`
  checkpoints, nested attribution, legitimate guest-SEH precedence, and the
  conservative host exception allowlist.

Build the lightweight configuration with:

```powershell
cmake --build --preset win-amd64-fault-walk-dispatch-release
```

Build the full configuration with:

```powershell
cmake --build --preset win-amd64-fault-walk-release
```

Run the established calibrated input sequence and harvest into a numbered
iteration directory with:

```powershell
.\tools\Invoke-Fable2FaultWalk.ps1 `
    -Iteration 1 `
    -RunDirectory .\out\fault-walk-runs
```

Select the full generated-function boundary explicitly when it is needed:

```powershell
.\tools\Invoke-Fable2FaultWalk.ps1 `
    -Mode Full `
    -Iteration 1 `
    -RunDirectory .\out\fault-walk-runs
```

After codegen and the fault-walk executable have already been validated, reuse
them for another runtime-only harvesting iteration with:

```powershell
.\tools\Invoke-Fable2FaultWalk.ps1 `
    -Iteration 2 `
    -RunDirectory .\out\fault-walk-runs `
    -SkipCodegen `
    -SkipBuild
```

For a user-controlled harvest, disable the calibrated input sequence while
retaining process monitoring, guardrails, reporting, and graceful shutdown:

```powershell
.\tools\Invoke-Fable2FaultWalk.ps1 `
    -Iteration 7 `
    -RunDirectory .\out\fault-walk-runs `
    -MonitorSeconds 1800 `
    -SkipCodegen `
    -SkipBuild `
    -ManualInput
```

The helper reuses `Invoke-Fable2BringUpIteration.ps1`, the calibrated keyboard
input helper, numbered `fable2-run-NNN.log` files, and the existing TU1 guest
byte capture. Its additional output is:

```text
out\fault-walk-runs\iteration-NN\fault-walk-report.json
```

Optional parameters expose the runtime guardrails:

- `-Mode Dispatch|Full` (default `Dispatch`)
- `-MaxUnique` (default `32`)
- `-MaxTotalSuppressions` (default `1000000`)
- `-MaxFunctionSuppressions` (default `250000`)
- `-MonitorSeconds` (default `120` after calibrated input)
- `-ManualInput` (do not inject the calibrated input sequence)

The gameplay-thread hot path records rich evidence only for the first hit of a
new target. Repeat suppressions update primitive counters without formatting,
logging, or rewriting JSON. The complete JSON report is deferred until an
explicit report request, guardrail stop, or graceful process exit. First-hit
records still allocate bounded diagnostic strings and a guest-stack snapshot;
there is no worker thread in v1.

The helper first requests a graceful window close so the end-of-run summary can
be emitted, then force-stops only if the process does not exit within five
seconds.

## Warning

Full fault walking restores `PPCContext` but does not roll back guest-memory
writes. Dispatch mode returns before an invalid target body can execute, but its
synthetic return can still alter later program state. Later faults in either
mode may therefore be secondary. A poisoned function and `r3=0` return are
tolerances for harvesting, not real fixes.
