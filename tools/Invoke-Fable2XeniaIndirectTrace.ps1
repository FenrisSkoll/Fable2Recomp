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

    [string]$TitlePath,

    [string]$RunRoot,

    [string]$ContentRoot = "C:\Dev\Fable2Phase4Xenia\content",

    [string]$StorageRoot = "C:\Dev\Fable2Phase4Xenia\storage"
)

$ErrorActionPreference = "Stop"

$fable2Root = [IO.Path]::GetFullPath($Fable2Repository)
$xeniaRoot = [IO.Path]::GetFullPath($XeniaRepository)

if ([string]::IsNullOrWhiteSpace($TitlePath)) {
    $TitlePath = Join-Path $fable2Root "assets\tu1\default.xex"
}

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
    "--title"
    ([IO.Path]::GetFullPath($TitlePath))
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
