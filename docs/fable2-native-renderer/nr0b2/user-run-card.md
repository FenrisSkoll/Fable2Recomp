# One corrected user-operated metadata capture

Prepared run ID: `nr0b2-oakfield-20260911-003`.
This session passed preflight and has never been launched. Do not recreate it,
reuse sessions 001/002, delete a launch claim or run preparation again after a
failure.

From the accepted developer PowerShell profile, run exactly:

```powershell
Set-Location C:\Dev\Fable2Recomp
.\tools\Invoke-Fable2GpuMetadata.ps1 -SessionRoot .\out\nr0b2\sessions\nr0b2-oakfield-20260911-003
```

The cues are deliberately distinct and do not require viewing the console:

- **READY:** two tones rising. Both shortcuts registered and the recorder can
  accept the trigger.
- **STARTED:** one high tone. F10 was accepted for the foreground game process
  and the five-second maximum window began.
- **STOPPED:** three tones rising. Recording ended and metadata flushed.
- **CANCELLED:** two tones falling. Recorder cancellation was accepted and
  partial metadata flushed.
- **ERROR:** three tones falling. Preserve the session and exit normally.

The console prints the same READY, STARTED and final transition after draining
the durable sequence. Even if recording begins and ends between its 250 ms
polls, both STARTED and STOPPED must still be printed. The durable transition
files are authoritative machine evidence; console visibility and sound
perception are user observations.

## User steps

1. Launch the prepared helper with the command above.
2. Wait for the **READY** cue: two rising tones.
3. Load the documented checkpoint. Expected save position is outside the
   Oakfield Inn/tavern. If it loads elsewhere, report that; do not navigate to
   force a match.
4. Hold a stationary ordinary-gameplay view. The player or dog need only be
   present if naturally visible.
5. With the game foreground, press **Ctrl+Shift+F10 once**.
6. Confirm the **STARTED** cue: one high tone.
7. Wait for **STOPPED**: three rising tones.
8. Exit the game normally.
9. Allow the helper to finish and report its final result.

If READY never occurs, do not press F10; exit normally and preserve the session.
If STARTED does not follow the single F10 press, do not press it repeatedly;
exit normally and preserve the session. If ERROR occurs, exit normally and
preserve the evidence. Ctrl+Shift+F11 cancels the recorder without terminating
the game; use it only if cancellation is needed.

The capture stops at the first of five seconds from accepted STARTED, three
complete consumer XE_SWAP intervals, 20,000 decisions, 100,000 total records or
32 MiB. The initial partial interval does not count as complete. Capture timeout
stops only recording; it never exits or force-kills the game. Leave renderer and
window settings unchanged. No screenshot, fault reproduction, NPC search, route
replay or special visual target is needed.

## Isolation and launch contract

Executable:
`C:\Dev\Fable2Recomp\out\nr0b2\sessions\nr0b2-oakfield-20260911-003\runtime\fable2.exe`.
The session has separate `user-data`, `user-data\cache` and one-use `capture`
roots. Its immutable checkpoint is
`out\nr0b2\checkpoints\nr0b2-oakfield-20260911-003\user-data`. The source was the
protected NR0B-1 Oakfield checkpoint, not a mutable working or session 002 save.

The helper exclusively claims the session and reserves the next numbered
`C:\Dev\Fable2Recomp\fable2-run-NNN.log` at launch. It retains the accepted
Release/Xenos/debug pattern and passes:

```text
--game_data_root C:\Dev\Fable2Recomp\assets\runtime
--update_data_root C:\Dev\Fable2Recomp\assets\update
--gpu_plugin=xenos --log_level debug
--log_file C:\Dev\Fable2Recomp\fable2-run-NNN.log
--user_data_root C:\Dev\Fable2Recomp\out\nr0b2\sessions\nr0b2-oakfield-20260911-003\user-data
--cache_root C:\Dev\Fable2Recomp\out\nr0b2\sessions\nr0b2-oakfield-20260911-003\user-data\cache
--gpu_config_report nr0b2-oakfield-20260911-003
```

Only the child process receives:

```text
REX_GPU_METADATA_RUN=nr0b2-oakfield-20260911-003
REX_GPU_METADATA_OUTPUT=C:\Dev\Fable2Recomp\out\nr0b2\sessions\nr0b2-oakfield-20260911-003\capture
```

After the helper returns, report:

- whether READY occurred before any trigger;
- whether STARTED followed the single F10 press;
- which final cue occurred;
- the loaded scene and whether gameplay loaded normally;
- any naturally noticed pacing or visual issue;
- whether the game exited normally and the helper's final status.

No upload is required in this shared workspace. The later analysis will use the
preserved process evidence, durable transitions, allocated log and binary
metadata; a user report does not identify any object's draw.
