[CmdletBinding()]
param(
    [ValidateSet("Status", "Prepare", "Launch", "Report")]
    [string]$Action = "Status",

    [ValidateSet("FreshNative", "FreshNativeReload", "XeniaUpdate")]
    [string]$State = "FreshNative",

    [string]$ReferenceSaveRoot = "C:\Users\Fenris\Documents\fable2"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$diagnosticRoot = [IO.Path]::GetFullPath(
    (Join-Path $repoRoot "out\native-save-diagnostic")
)
$emptyStateRoot = [IO.Path]::GetFullPath((Join-Path $diagnosticRoot "A-empty"))
$nativeSaveRoot = [IO.Path]::GetFullPath((Join-Path $diagnosticRoot "B-fresh-native"))
$xeniaCopyRoot = [IO.Path]::GetFullPath((Join-Path $diagnosticRoot "C-xenia-copy"))
$xeniaUpdateRoot = [IO.Path]::GetFullPath((Join-Path $diagnosticRoot "D-xenia-update"))
$freshCaptureRoot = [IO.Path]::GetFullPath((Join-Path $diagnosticRoot "capture-001"))
$reloadCaptureRoot = [IO.Path]::GetFullPath((Join-Path $diagnosticRoot "capture-002"))
$updateCaptureRoot = [IO.Path]::GetFullPath((Join-Path $diagnosticRoot "capture-D-001"))
$freshCacheRoot = [IO.Path]::GetFullPath((Join-Path $diagnosticRoot "cache-001"))
$reloadCacheRoot = [IO.Path]::GetFullPath((Join-Path $diagnosticRoot "cache-002"))
$updateCacheRoot = [IO.Path]::GetFullPath((Join-Path $diagnosticRoot "cache-D-001"))
$baselinePath = [IO.Path]::GetFullPath((Join-Path $diagnosticRoot "state-A-before.json"))
$nativeAfterWriteSnapshotPath = [IO.Path]::GetFullPath(
    (Join-Path $diagnosticRoot "state-B-after-write.json")
)
$referenceSnapshotPath = [IO.Path]::GetFullPath(
    (Join-Path $diagnosticRoot "state-C-reference.json")
)

switch ($State) {
    "FreshNative" {
        $selectedSaveRoot = $nativeSaveRoot
        $selectedBaselinePath = $baselinePath
        $captureRoot = $freshCaptureRoot
        $cacheRoot = $freshCacheRoot
        $logName = "fable2-native-save-001.log"
    }
    "FreshNativeReload" {
        $selectedSaveRoot = $nativeSaveRoot
        $selectedBaselinePath = $nativeAfterWriteSnapshotPath
        $captureRoot = $reloadCaptureRoot
        $cacheRoot = $reloadCacheRoot
        $logName = "fable2-native-reload-002.log"
    }
    "XeniaUpdate" {
        $selectedSaveRoot = $xeniaUpdateRoot
        $selectedBaselinePath = $referenceSnapshotPath
        $captureRoot = $updateCaptureRoot
        $cacheRoot = $updateCacheRoot
        $logName = "fable2-native-update-D-001.log"
    }
}
$tracePath = [IO.Path]::GetFullPath(
    (Join-Path $captureRoot "save-trace-events-v1.ndjson")
)
$metadataPath = [IO.Path]::GetFullPath(
    (Join-Path $captureRoot "save-trace-run-v1.json")
)
$logPath = [IO.Path]::GetFullPath(
    (Join-Path $captureRoot $logName)
)
$reportPath = [IO.Path]::GetFullPath(
    (Join-Path $captureRoot "save-diagnostic-report-v1.json")
)
$captureArtifactPaths = @($tracePath, $metadataPath, $logPath, $reportPath)
$executablePath = [IO.Path]::GetFullPath(
    (Join-Path $repoRoot "out\build\win-amd64-native-save-diagnostic-release\fable2.exe")
)
$gameDataRoot = [IO.Path]::GetFullPath((Join-Path $repoRoot "assets\runtime"))
$updateDataRoot = [IO.Path]::GetFullPath((Join-Path $repoRoot "assets\update"))
$analysisTool = [IO.Path]::GetFullPath((Join-Path $repoRoot "tools\Fable2SaveTrace.py"))

function Test-PathWithin {
    param(
        [Parameter(Mandatory)]
        [string]$Path,

        [Parameter(Mandatory)]
        [string]$Root
    )

    $resolvedPath = [IO.Path]::GetFullPath($Path).TrimEnd('\')
    $resolvedRoot = [IO.Path]::GetFullPath($Root).TrimEnd('\')
    return $resolvedPath.StartsWith(
        $resolvedRoot + '\',
        [StringComparison]::OrdinalIgnoreCase
    )
}

function Assert-DiagnosticPath {
    param(
        [Parameter(Mandatory)]
        [string]$Path
    )

    if (-not (Test-PathWithin -Path $Path -Root $diagnosticRoot)) {
        throw "Refusing path outside isolated diagnostic root: $Path"
    }
}

function Assert-NoFiles {
    param(
        [Parameter(Mandatory)]
        [string]$Path,

        [Parameter(Mandatory)]
        [string]$Purpose
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        throw "$Purpose directory does not exist; run -Action Prepare first: $Path"
    }
    $firstFile = Get-ChildItem -LiteralPath $Path -File -Recurse | Select-Object -First 1
    if ($null -ne $firstFile) {
        throw "$Purpose must contain no files: $Path"
    }
}

function Assert-HasFiles {
    param(
        [Parameter(Mandatory)]
        [string]$Path,

        [Parameter(Mandatory)]
        [string]$Purpose
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        throw "$Purpose directory does not exist: $Path"
    }
    $firstFile = Get-ChildItem -LiteralPath $Path -File -Recurse | Select-Object -First 1
    if ($null -eq $firstFile) {
        throw "$Purpose must contain the preserved files from the preceding state: $Path"
    }
}

function Show-Paths {
    Write-Host "Diagnostic state:      $State"
    Write-Host "Diagnostic executable: $executablePath"
    Write-Host "Selected save root:    $selectedSaveRoot"
    Write-Host "Trace directory:       $captureRoot"
    Write-Host "Runtime log:           $logPath"
    Write-Host "Baseline snapshot:     $selectedBaselinePath"
    Write-Host "Post-run report:       $reportPath"
}

foreach ($path in @(
        $emptyStateRoot,
        $nativeSaveRoot,
        $xeniaCopyRoot,
        $xeniaUpdateRoot,
        $freshCaptureRoot,
        $reloadCaptureRoot,
        $updateCaptureRoot,
        $captureRoot,
        $freshCacheRoot,
        $reloadCacheRoot,
        $updateCacheRoot,
        $cacheRoot,
        $baselinePath,
        $nativeAfterWriteSnapshotPath,
        $referenceSnapshotPath,
        $tracePath,
        $metadataPath,
        $logPath,
        $reportPath
    )) {
    Assert-DiagnosticPath -Path $path
}

if ($Action -eq "Prepare") {
    New-Item -ItemType Directory -Force -Path $diagnosticRoot | Out-Null
    New-Item -ItemType Directory -Force -Path $emptyStateRoot | Out-Null
    New-Item -ItemType Directory -Force -Path $nativeSaveRoot | Out-Null
    New-Item -ItemType Directory -Force -Path $xeniaCopyRoot | Out-Null
    New-Item -ItemType Directory -Force -Path $xeniaUpdateRoot | Out-Null
    New-Item -ItemType Directory -Force -Path $freshCaptureRoot | Out-Null
    New-Item -ItemType Directory -Force -Path $reloadCaptureRoot | Out-Null
    New-Item -ItemType Directory -Force -Path $updateCaptureRoot | Out-Null
    New-Item -ItemType Directory -Force -Path $cacheRoot | Out-Null

    Assert-NoFiles -Path $emptyStateRoot -Purpose "State A"
    if ($State -eq "FreshNative") {
        Assert-NoFiles -Path $nativeSaveRoot -Purpose "State B"
        & python $analysisTool snapshot --root $emptyStateRoot --output $baselinePath
        if ($LASTEXITCODE -ne 0) {
            throw "State A snapshot failed with exit code $LASTEXITCODE."
        }
    }
    elseif ($State -eq "FreshNativeReload") {
        Assert-HasFiles -Path $nativeSaveRoot -Purpose "State B after capture 001"
        if (Test-Path -LiteralPath $nativeAfterWriteSnapshotPath) {
            throw "Refusing to overwrite the preserved State B snapshot: $nativeAfterWriteSnapshotPath"
        }
        & python $analysisTool snapshot `
            --root $nativeSaveRoot `
            --output $nativeAfterWriteSnapshotPath
        if ($LASTEXITCODE -ne 0) {
            throw "State B snapshot failed with exit code $LASTEXITCODE."
        }
    }
    elseif (-not (Test-Path -LiteralPath $referenceSnapshotPath -PathType Leaf)) {
        if (-not (Test-Path -LiteralPath $ReferenceSaveRoot -PathType Container)) {
            throw "Reference save root does not exist: $ReferenceSaveRoot"
        }
        $resolvedReference = [IO.Path]::GetFullPath($ReferenceSaveRoot)
        if (Test-PathWithin -Path $resolvedReference -Root $diagnosticRoot) {
            throw "Reference save root must be outside the writable diagnostic root."
        }
        Assert-NoFiles -Path $xeniaCopyRoot -Purpose "State C"
        Assert-NoFiles -Path $xeniaUpdateRoot -Purpose "State D"

        foreach ($destination in @($xeniaCopyRoot, $xeniaUpdateRoot)) {
            Get-ChildItem -LiteralPath $resolvedReference | ForEach-Object {
                Copy-Item -LiteralPath $_.FullName -Destination $destination -Recurse
            }
        }
        Write-Host "Copied the read-only reference into isolated states C and D."
        & python $analysisTool snapshot `
            --root $xeniaCopyRoot `
            --output $referenceSnapshotPath
        if ($LASTEXITCODE -ne 0) {
            throw "State C snapshot failed with exit code $LASTEXITCODE."
        }
    }

    Write-Host "Prepared isolated native-save diagnostic state."
    Show-Paths
    exit 0
}

if ($Action -eq "Launch") {
    if (-not (Test-Path -LiteralPath $executablePath -PathType Leaf)) {
        throw "Diagnostic executable was not found: $executablePath"
    }
    if (-not (Test-Path -LiteralPath $gameDataRoot -PathType Container)) {
        throw "Game-data root was not found: $gameDataRoot"
    }
    if (-not (Test-Path -LiteralPath $updateDataRoot -PathType Container)) {
        throw "Update-data root was not found: $updateDataRoot"
    }
    if ($State -eq "FreshNative") {
        Assert-NoFiles -Path $nativeSaveRoot -Purpose "State B"
    }
    elseif ($State -eq "FreshNativeReload") {
        Assert-HasFiles -Path $nativeSaveRoot -Purpose "State B after capture 001"
    }
    else {
        Assert-HasFiles -Path $xeniaUpdateRoot -Purpose "State D"
    }
    if (-not (Test-Path -LiteralPath $selectedBaselinePath -PathType Leaf)) {
        throw "Selected baseline does not exist; run -Action Prepare first: $selectedBaselinePath"
    }
    Assert-NoFiles -Path $cacheRoot -Purpose "$State cache root"
    foreach ($outputPath in $captureArtifactPaths) {
        if (Test-Path -LiteralPath $outputPath) {
            throw "Refusing to overwrite an existing capture artifact: $outputPath"
        }
    }

    Show-Paths
    Write-Host "Launching one interactive diagnostic run. Do not relaunch before analysis."
    $launchArguments = @(
        "--game_data_root=$gameDataRoot",
        "--update_data_root=$updateDataRoot",
        "--user_data_root=$selectedSaveRoot",
        "--cache_root=$cacheRoot",
        "--gpu_plugin=xenos",
        "--log_level=debug",
        "--log_file=$logPath",
        "--save_trace_dir=$captureRoot"
    )
    $process = Start-Process `
        -FilePath $executablePath `
        -ArgumentList $launchArguments `
        -WorkingDirectory $repoRoot `
        -Wait `
        -PassThru
    $exitCode = $process.ExitCode
    Write-Host "Diagnostic process exit code: $exitCode"
    Write-Host "Do not launch again before running -Action Report and inspecting the capture."
    exit $exitCode
}

if ($Action -eq "Report") {
    if (-not (Test-Path -LiteralPath $tracePath -PathType Leaf)) {
        throw "Save trace does not exist: $tracePath"
    }
    if (-not (Test-Path -LiteralPath $metadataPath -PathType Leaf)) {
        throw "Save trace metadata does not exist: $metadataPath"
    }
    if (-not (Test-Path -LiteralPath $selectedBaselinePath -PathType Leaf)) {
        throw "Selected baseline does not exist: $selectedBaselinePath"
    }

    & python $analysisTool report `
        --trace $tracePath `
        --metadata $metadataPath `
        --save-root $selectedSaveRoot `
        --baseline $selectedBaselinePath `
        --output $reportPath
    exit $LASTEXITCODE
}

Show-Paths
Write-Host "State A exists:        $(Test-Path -LiteralPath $emptyStateRoot)"
Write-Host "State B exists:        $(Test-Path -LiteralPath $nativeSaveRoot)"
Write-Host "State C exists:        $(Test-Path -LiteralPath $xeniaCopyRoot)"
Write-Host "State D exists:        $(Test-Path -LiteralPath $xeniaUpdateRoot)"
$captureAlreadyUsed = $null -ne (
    $captureArtifactPaths |
        Where-Object { Test-Path -LiteralPath $_ } |
        Select-Object -First 1
)
Write-Host "Capture already used:  $captureAlreadyUsed"
