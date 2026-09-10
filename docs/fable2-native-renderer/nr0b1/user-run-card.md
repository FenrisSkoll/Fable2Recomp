# One user-operated configuration run

Status: **PREPARED — USER RUN REQUIRED**. Run once from the accepted developer
PowerShell profile (which defines `Get-Fable2NextRunNumber`):

```powershell
Set-Location C:\Dev\Fable2Recomp
.\tools\Invoke-Fable2GpuConfig.ps1 -SessionRoot .\out\nr0b1\sessions\nr0b1-oakfield-20260910-001
```

The exact staged executable is
`C:\Dev\Fable2Recomp\out\nr0b1\sessions\nr0b1-oakfield-20260910-001\runtime\fable2.exe`.
The helper validates inventories and all staged/baseline hashes, then uses the
normal `Get-Fable2NextRunNumber` allocator and exclusively reserves
`C:\Dev\Fable2Recomp\fable2-run-NNN.log`. `NNN` is determined at launch so it
cannot collide with intervening user runs. It creates a one-use launch claim;
do not delete the claim to repeat the run.

Arguments passed through `ProcessStartInfo.ArgumentList` are:

```text
--game_data_root C:\Dev\Fable2Recomp\assets\runtime
--update_data_root C:\Dev\Fable2Recomp\assets\update
--gpu_plugin=xenos --log_level debug
--log_file C:\Dev\Fable2Recomp\fable2-run-NNN.log
--user_data_root C:\Dev\Fable2Recomp\out\nr0b1\sessions\nr0b1-oakfield-20260910-001\user-data
--cache_root C:\Dev\Fable2Recomp\out\nr0b1\sessions\nr0b1-oakfield-20260910-001\user-data\cache
--gpu_config_report nr0b1-oakfield-20260910-001
```

This is the documented isolated-user-root exception to the normal launch
helper; `fable2-run` is unchanged. It uses Release/Xenos/debug logging and the
same assets/update roots. Do not run against the source or preserved checkpoint.

1. Load the selected save and confirm whether it is the documented Oakfield
   tavern endpoint. If unexpected, report the actual scene; do not navigate to
   another scene to make the report match.
2. Remain briefly in ordinary gameplay so first guest-output state can exist.
   Leave renderer settings/window size alone during this snapshot. No route,
   NPC search, black-dog reproduction or screenshot is required.
3. Exit the game normally and let the PowerShell helper return. Do not close
   the monitor shell or force-kill a healthy game because reporting is complete.

The monitor prints the PID/log path, samples relevant loaded modules only
until all four are observed or 60 seconds elapse, and waits without an exit
deadline on the actual process handle. It records actual start/end/exit status,
OS source, launch arguments and observed CIM command line. Module identity is
the mapped module's absolute file path plus that file's size/hash at observation;
it is not a process-memory digest. Missing/failed observations remain explicit.
Reporting failure never suppresses a renderer failure or kills the process.

Outputs under the session root:

- `preparation.json`: immutable prelaunch inputs, copies, staged artifacts and cache inventory.
- `launch.claim`: prevents reuse.
- `process.json`: actual process/module/termination evidence, or explicit missing fields/errors.
- `effective-report.json`: bounded SDK records, supported title/update log excerpts, integrity checks and remaining review questions.

After return, report only: **loaded scene**, **whether ordinary gameplay loaded
normally**, **any visible symptom noticed without searching**, and **whether
you exited normally**. The actual exit code comes from `process.json`, not the
user's report or `$LASTEXITCODE`. The agent will inspect these files, reconcile
effective/loaded identities and recheck source/preserved/baseline integrity.
Writable save/cache changes are expected and reported separately. If the helper
fails, preserve the session/log and provide the error; no repeated run is implied.

The parser deliberately leaves final scene/normal-exit review pending even
when all machine records are present. NR0B-2 is not authorized by this run card.
