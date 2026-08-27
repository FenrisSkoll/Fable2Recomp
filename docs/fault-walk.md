# Experimental Fable II fault-walk workflow

Fault walking is a diagnostic build mode. It is intentionally incorrect, is
disabled by default, and must never be treated as a Fable II correctness fix.

Build the dedicated configuration with:

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

After codegen and the fault-walk executable have already been validated, reuse
them for another runtime-only harvesting iteration with:

```powershell
.\tools\Invoke-Fable2FaultWalk.ps1 `
    -Iteration 2 `
    -RunDirectory .\out\fault-walk-runs `
    -SkipCodegen `
    -SkipBuild
```

The helper reuses `Invoke-Fable2BringUpIteration.ps1`, the calibrated keyboard
input helper, numbered `fable2-run-NNN.log` files, and the existing TU1 guest
byte capture. Its additional output is:

```text
out\fault-walk-runs\iteration-NN\fault-walk-report.json
```

Optional parameters expose the runtime guardrails:

- `-MaxUnique` (default `32`)
- `-MaxTotalSuppressions` (default `1000000`)
- `-MaxFunctionSuppressions` (default `250000`)
- `-MonitorSeconds` (default `120` after calibrated input)

The helper first requests a graceful window close so the end-of-run summary can
be emitted, then force-stops only if the process does not exit within five
seconds.

## Warning

Fault walking restores `PPCContext` but does not roll back guest-memory writes.
Later faults may be caused by accumulated mutations or synthetic returns and
must be classified accordingly. A poisoned function and `r3=0` return are
tolerances for harvesting, not real fixes.
