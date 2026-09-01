<#
.SYNOPSIS
Preflights, launches, or post-processes a Fable II Xenia indirect-target trace.

.DESCRIPTION
GamePath is complete game media passed to Xenia as its final positional
argument. AnalysisImagePath is the base XEX used with its adjacent XEXP only
to verify the configured post-patch TU1 analysis-image identity. The analysis
XEX is never used as the normal gameplay launch target.
#>
[CmdletBinding()]
param(
    [ValidateSet("Preflight", "Launch", "PostRun")]
    [string]$Action = "Preflight",

    [Parameter(Mandatory = $true)]
    [ValidatePattern("^[A-Za-z0-9_.-]+$")]
    [string]$RunId,

    [string]$Label = "Fable II GOTY TU1 manual coverage",

    [string]$XeniaRepository = "C:\Dev\Fable2Phase4Xenia\xenia-canary",

    [string]$Fable2Repository = "C:\Dev\Fable2Recomp",

    [string]$GamePath = "D:\Fable2-Recomp\disc\Fable II - Game of the Year Edition.iso",

    [string]$AnalysisImagePath = "D:\Fable2-Recomp\tu1\default.xex",

    [string]$RunRoot,

    [string]$ContentRoot = "C:\Dev\Fable2Phase4Xenia\content",

    [string]$StorageRoot = "C:\Dev\Fable2Phase4Xenia\storage"
)

$ErrorActionPreference = "Stop"

$fable2Root = [IO.Path]::GetFullPath($Fable2Repository)
$xeniaRoot = [IO.Path]::GetFullPath($XeniaRepository)

if ([string]::IsNullOrWhiteSpace($RunRoot)) {
    $RunRoot = Join-Path $fable2Root "out\indirect-targets"
}

$toolPath = Join-Path $fable2Root "tools\Fable2IndirectTargets.py"
$evidencePath = Join-Path $fable2Root "tools\fable2-entrypoint-closure-evidence.json"
$manifestPath = Join-Path $fable2Root "fable2_manifest.toml"
$generatedInitPath = Join-Path $fable2Root "generated\default\fable2_init.cpp"
$xeniaPath = Join-Path $xeniaRoot "build\bin\Windows\Release\xenia_canary.exe"
$runDirectory = Join-Path ([IO.Path]::GetFullPath($RunRoot)) $RunId
$rawPath = Join-Path $runDirectory "xenia-indirect-targets.raw.jsonl"
$reviewDirectory = Join-Path $runDirectory "review"

if (-not (Test-Path -LiteralPath $toolPath -PathType Leaf)) {
    throw "Phase 4 tool was not found: $toolPath"
}

if ($Action -eq "PostRun") {
    if (-not (Test-Path -LiteralPath $rawPath -PathType Leaf)) {
        throw "Collector raw trace was not found: $rawPath"
    }

    $contract = Get-Content -LiteralPath $evidencePath -Raw | ConvertFrom-Json
    $patchedImageHash = $contract.expected_image_identity.patched_image_sha256
    $analysisDirectory = Join-Path $fable2Root "out\analysis\$patchedImageHash"
    $closurePath = Join-Path $analysisDirectory "entrypoint-closure.json"
    $ghidraPath = Join-Path $analysisDirectory "ghidra-function-map.json"

    $arguments = @(
        $toolPath
        "post-run"
        "--raw"
        $rawPath
        "--output-directory"
        $reviewDirectory
        "--manifest"
        $manifestPath
        "--closure"
        $closurePath
        "--evidence"
        $evidencePath
        "--generated-init"
        $generatedInitPath
    )

    if (Test-Path -LiteralPath $ghidraPath -PathType Leaf) {
        $arguments += "--ghidra-map"
        $arguments += $ghidraPath
    }

    & python @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Phase 4 post-run validation failed with exit code $LASTEXITCODE."
    }
    return
}

$preflightArguments = @(
    $toolPath
    "preflight"
    "--xenia"
    $xeniaPath
    "--game-path"
    ([IO.Path]::GetFullPath($GamePath))
    "--analysis-image-path"
    ([IO.Path]::GetFullPath($AnalysisImagePath))
    "--output"
    $rawPath
    "--run-id"
    $RunId
    "--label"
    $Label
    "--content-root"
    ([IO.Path]::GetFullPath($ContentRoot))
    "--storage-root"
    ([IO.Path]::GetFullPath($StorageRoot))
    "--evidence"
    $evidencePath
)

$preflightText = & python @preflightArguments
if ($LASTEXITCODE -ne 0) {
    throw "Phase 4 preflight failed with exit code $LASTEXITCODE."
}

$preflight = $preflightText | ConvertFrom-Json
$preflight | ConvertTo-Json -Depth 8

if ($Action -eq "Launch") {
    $launchArguments = @($preflight.arguments)
    $launchExecutable = $launchArguments[0]
    $launchParameters = $launchArguments[1..($launchArguments.Count - 1)]
    & $launchExecutable @launchParameters
    if ($LASTEXITCODE -ne 0) {
        throw "Xenia exited with code $LASTEXITCODE. The raw trace may still be recoverable."
    }
}
