# One user-operated metadata capture

Prepared run ID: `nr0b2-oakfield-20260910-002`.
No launch claim/log/process/capture exists yet. Do not recreate or reuse this
session, delete claims, or run preparation again after a failure.
The preserved, unused `nr0b2-oakfield-20260910-001` preparation was superseded
during final review. Launch only `002` below.

From the accepted developer PowerShell profile:

```powershell
Set-Location C:\Dev\Fable2Recomp
.\tools\Invoke-Fable2GpuMetadata.ps1 -SessionRoot .\out\nr0b2\sessions\nr0b2-oakfield-20260910-002
```

1. Wait for **ARMED** in the monitor shell. Load the selected save and confirm
   the actual scene. Expected checkpoint: outside Oakfield Inn/tavern. If the
   scene differs, report what loaded; do not navigate to force a match.
2. Keep a stationary ordinary-gameplay view. Include player/dog only if
   naturally visible. Leave renderer/window settings unchanged.
3. With the **game window foreground**, press **Ctrl+Shift+F10 once**. This
   triggers metadata collection; no focus switch is required. Keep the view
   stationary during the short window.
4. Wait for the **rising two-tone sound**, which means **STOPPED and flushed**.
   The shell and session `capture\status.txt` also report STOPPED. If sound is
   unavailable, wait at least five seconds before checking the shell; switching
   away after the deadline cannot extend recording. A recording/error sound
   alone is not the stopped indication.
5. Exit the game normally and let the helper return. Capture completion does
   not exit the game. The helper records actual process exit status.

**Cancel:** Ctrl+Shift+F11 while this game is foreground stops only the recorder.
It may leave a partial/no interval. A repeated trigger or trigger while another
process is foreground is inert. If hotkey registration conflicts or the recorder
reports ERROR, preserve the session/log and exit normally. No silent retry.

The window stops at the first of five seconds from trigger, three complete
consumer XE_SWAP intervals, 20,000 decisions, 100,000 records or 32 MiB. The
initial partial interval does not count as complete. Usually the interval
bound may stop it well before five seconds. Flush may finish later without
extending observation or blocking rendering. There is no screenshot, route,
NPC search, fault reproduction or gameplay automation.

## Exact isolation and launch

Executable:
`C:\Dev\Fable2Recomp\out\nr0b2\sessions\nr0b2-oakfield-20260910-002\runtime\fable2.exe`.
User data: that session's `user-data`; cache: `user-data\cache`; capture:
`capture` (must not already exist). A new preserved copy lives at
`out\nr0b2\checkpoints\nr0b2-oakfield-20260910-002\user-data` and is never writable
by the game. The source is the protected NR0B-1 checkpoint, not its post-run save.

The helper exclusively claims this session and reserves the next
`C:\Dev\Fable2Recomp\fable2-run-NNN.log` using `Get-Fable2NextRunNumber` at launch.
It retains the normal Release/Xenos/debug pattern and passes these arguments
through `ProcessStartInfo.ArgumentList`:

```text
--game_data_root C:\Dev\Fable2Recomp\assets\runtime
--update_data_root C:\Dev\Fable2Recomp\assets\update
--gpu_plugin=xenos --log_level debug
--log_file C:\Dev\Fable2Recomp\fable2-run-NNN.log
--user_data_root C:\Dev\Fable2Recomp\out\nr0b2\sessions\nr0b2-oakfield-20260910-002\user-data
--cache_root C:\Dev\Fable2Recomp\out\nr0b2\sessions\nr0b2-oakfield-20260910-002\user-data\cache
--gpu_config_report nr0b2-oakfield-20260910-002
```

Only the child process receives:

```text
REX_GPU_METADATA_RUN=nr0b2-oakfield-20260910-002
REX_GPU_METADATA_OUTPUT=C:\Dev\Fable2Recomp\out\nr0b2\sessions\nr0b2-oakfield-20260910-002\capture
```

The normal `fable2-run` helper is unchanged. Preflight verifies source/copy,
baseline/staged/runtime-input hashes and absent exe-adjacent configuration.
Module observations require the EXE, runtime and GPU DLL; Tracy is optional
because these exact Release images have no Tracy imports. The monitor waits
on the actual process with no gameplay timeout or forced kill.

After the helper returns, report **loaded scene**, **whether gameplay loaded
normally**, **whether the stopped indication occurred**, **any naturally noticed
visual or pacing issue**, and **whether you exited normally**. No capture upload
is needed in this shared workspace. The agent will inspect `process.json`,
`analysis.json`, the allocated log and `capture\metadata.bin`. User reports do
not substitute for process/module/terminal evidence or identify a dog's draw.
