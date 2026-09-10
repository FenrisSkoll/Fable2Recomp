<#
User-operated NR0B-2 metadata launch. Preserves numbered logs and the actual process
handle. Ctrl+Shift+F10 starts one bounded capture while this game is foreground.
Ctrl+Shift+F11 cancels recording. Neither stops the game. No gameplay input is sent.
#>
[CmdletBinding()]
param([Parameter(Mandatory)][string]$SessionRoot)

$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$session = (Resolve-Path -LiteralPath $SessionRoot).Path
$prep = Get-Content -LiteralPath (Join-Path $session 'preparation.json') -Raw | ConvertFrom-Json
if ($prep.session -ne $session.Replace('\', '/')) {
    # Path comparison below also accepts the native Windows spelling.
    if ([IO.Path]::GetFullPath($prep.session) -ne [IO.Path]::GetFullPath($session)) {
        throw 'Session identity mismatch'
    }
}
if (-not (Get-Command Get-Fable2NextRunNumber -ErrorAction SilentlyContinue)) {
    throw 'Use the accepted developer PowerShell profile: Get-Fable2NextRunNumber is required.'
}
if ([IO.Path]::GetFullPath($global:Fable2Repo) -ne [IO.Path]::GetFullPath($repo)) {
    throw 'The accepted numbered-log allocator points at another repository.'
}
python (Join-Path $PSScriptRoot 'Fable2GpuMetadata.py') preflight --session $session
if ($LASTEXITCODE -ne 0) { throw 'Preflight failed; nothing launched.' }

# Exclusive creation prevents accidental repeated launches or log reuse.
$marker = [IO.File]::Open((Join-Path $session 'launch.claim'), 'CreateNew', 'Write', 'None')
$marker.Dispose()
$runNumber = Get-Fable2NextRunNumber
$log = Join-Path $repo ('fable2-run-{0:D3}.log' -f $runNumber)
$reservation = [IO.File]::Open($log, 'CreateNew', 'Write', 'None')
$reservation.Dispose()

$launch = [Diagnostics.ProcessStartInfo]::new()
$launch.FileName = $prep.staged.'fable2.exe'.path
$launch.WorkingDirectory = $repo
$launch.UseShellExecute = $false
$launch.Environment['REX_GPU_METADATA_RUN'] = $prep.run_id
$launch.Environment['REX_GPU_METADATA_OUTPUT'] = $prep.capture
$arguments = @(
    '--game_data_root', (Join-Path $repo 'assets/runtime'),
    '--update_data_root', (Join-Path $repo 'assets/update'),
    '--gpu_plugin=xenos', '--log_level', 'debug', '--log_file', $log,
    '--user_data_root', $prep.writable,
    '--cache_root', $prep.cache.root,
    '--gpu_config_report', $prep.run_id
)
foreach ($argument in $arguments) { $launch.ArgumentList.Add($argument) }
$process = [Diagnostics.Process]::new()
$process.StartInfo = $launch
$report = [ordered]@{
    run_id = $prep.run_id
    executable = $launch.FileName
    arguments = $arguments
    working_directory = $repo
    log = $log
    os = [Environment]::OSVersion.VersionString
    os_source = 'System.Environment.OSVersion'
    pid = $null
    start_utc = $null
    end_utc = $null
    exit_code = $null
    command_line_observed = $null
    modules = @{}
    recorder_environment = @{
        REX_GPU_METADATA_RUN = $prep.run_id
        REX_GPU_METADATA_OUTPUT = $prep.capture
    }
    recorder_status = [Collections.Generic.List[object]]::new()
    reporting_errors = [Collections.Generic.List[string]]::new()
}
$script:lastMetadataStatus = ''
function Show-MetadataStatus {
    $statusPath = Join-Path $prep.capture 'status.txt'
    if (-not (Test-Path -LiteralPath $statusPath -PathType Leaf)) { return }
    try {
        $status = [IO.File]::ReadAllText($statusPath)
        # The worker writes a tiny status file; ignore a transient partial write.
        if ($status.Length -gt 1024 -or -not $status.EndsWith("`n")) { return }
        if ($status -ne $script:lastMetadataStatus) {
            $script:lastMetadataStatus = $status
            Write-Host $status.Trim()
            if ($report.recorder_status.Count -lt 16) {
                $report.recorder_status.Add(@{
                    observed_utc = [DateTime]::UtcNow.ToString('o')
                    text = $status.Trim()
                })
            }
        }
    } catch {
        # Transient status-file sharing failures are retried; never affect gameplay.
    }
}
try {
    if (-not $process.Start()) { throw 'Process.Start returned false' }
    $report.pid = $process.Id
    $report.start_utc = $process.StartTime.ToUniversalTime().ToString('o')
    Write-Host "PID $($process.Id); log $log"
    Write-Host 'Wait for ARMED. Load the save, keep a stationary ordinary-gameplay view, then press Ctrl+Shift+F10 once.'
    Write-Host 'Keep game focus. A rising two-tone sound means STOPPED and flushed. Then exit normally; let this helper return.'
    try {
        $instance = Get-CimInstance Win32_Process -Filter "ProcessId = $($process.Id)"
        $report.command_line_observed = $instance.CommandLine
    } catch {
        $report.reporting_errors.Add("Command line query: $($_.Exception.Message)")
    }
    $deadline = [DateTime]::UtcNow.AddSeconds(60)
    $moduleError = $null
    while (-not $process.HasExited -and [DateTime]::UtcNow -lt $deadline) {
        Show-MetadataStatus
        try {
            $process.Refresh()
            foreach ($module in $process.Modules) {
                $name = $module.ModuleName
                if ($prep.staged.PSObject.Properties.Name -contains $name -and
                    -not $report.modules.ContainsKey($name)) {
                    $file = Get-Item -LiteralPath $module.FileName
                    $report.modules[$name] = @{
                        path = $file.FullName
                        bytes = $file.Length
                        sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
                        observed_utc = [DateTime]::UtcNow.ToString('o')
                        identity_kind = 'loaded module path plus on-disk file hash; not process memory'
                    }
                }
            }
        } catch {
            $moduleError = $_.Exception.Message
        }
        $missingRequired = @($prep.required_modules | Where-Object { -not $report.modules.ContainsKey($_) })
        if ($missingRequired.Count -eq 0) { break }
        Start-Sleep -Milliseconds 250
    }
    if ($moduleError) { $report.reporting_errors.Add("Module observation: $moduleError") }
    # No deadline or forced termination: wait on the launched process itself.
    while (-not $process.WaitForExit(250)) { Show-MetadataStatus }
    Show-MetadataStatus
    $report.end_utc = $process.ExitTime.ToUniversalTime().ToString('o')
    $report.exit_code = $process.ExitCode
} catch {
    $report.reporting_errors.Add($_.Exception.Message)
    # Reporting failure does not terminate or detach from a healthy game.
    if ($report.pid) {
        while (-not $process.WaitForExit(1000)) { }
        $report.end_utc = $process.ExitTime.ToUniversalTime().ToString('o')
        $report.exit_code = $process.ExitCode
    }
} finally {
    $json = $report | ConvertTo-Json -Depth 8
    $output = [IO.File]::Open((Join-Path $session 'process.json'), 'CreateNew', 'Write', 'None')
    $writer = [IO.StreamWriter]::new($output)
    try { $writer.WriteLine($json) } finally { $writer.Dispose() }
    $process.Dispose()
}
Write-Host "Actual process exit: $($report.exit_code)"
python (Join-Path $PSScriptRoot 'Fable2GpuMetadata.py') analyse --session $session
if ($LASTEXITCODE -ne 0) { throw 'Post-run integrity/report analysis failed; preserve this session for review.' }
