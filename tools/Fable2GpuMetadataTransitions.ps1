function Read-Fable2GpuMetadataTransitions {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$TransitionRoot,
        [Parameter(Mandatory)][string]$RunId,
        [Parameter(Mandatory)][int]$ProcessId,
        [Parameter(Mandatory)][long]$AfterSequence
    )

    if (-not (Test-Path -LiteralPath $TransitionRoot -PathType Container)) {
        return @()
    }
    $files = @(Get-ChildItem -LiteralPath $TransitionRoot -File -Filter '*.json' |
        Sort-Object -Property Name)
    if ($files.Count -gt 64) {
        throw 'Transition history exceeds its 64-record validation ceiling.'
    }
    $result = [Collections.Generic.List[object]]::new()
    $expected = $AfterSequence + 1
    foreach ($file in $files) {
        if ($file.Length -gt 4096) {
            throw "Oversized transition record: $($file.Name)"
        }
        $record = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json
        if ([long]$record.sequence -le $AfterSequence) {
            continue
        }
        $expectedName = '{0:D16}-{1}.json' -f [long]$record.sequence, $record.transition
        if ([long]$record.sequence -ne $expected -or $file.Name -ne $expectedName -or
            $record.schema -ne 'rex-gpu-metadata-transition-v1' -or
            $record.run_id -ne $RunId -or [int]$record.pid -ne $ProcessId) {
            throw "Invalid, wrong-session or non-contiguous transition: $($file.Name)"
        }
        $result.Add($record)
        $expected++
    }
    return @($result)
}

function Format-Fable2GpuMetadataTransition {
    [CmdletBinding()]
    param([Parameter(Mandatory)][object]$Record)

    switch ($Record.transition) {
        'READY' { return 'READY: two rising tones; recorder can accept Ctrl+Shift+F10.' }
        'STARTED' { return 'STARTED: one high tone; five-second capture window began.' }
        'STOPPED' { return "STOPPED: three rising tones; flushed; reason=$($Record.terminal_reason_name)." }
        'CANCELLED' { return 'CANCELLED: two falling tones; partial metadata flushed.' }
        'ERROR' { return "ERROR: three falling tones; preserve the session; $($Record.error)." }
        'REJECTED' { return "REJECTED: control input did not target the enabled foreground process (PID $($Record.foreground_pid))." }
        default { throw "Unsupported transition type: $($Record.transition)" }
    }
}
