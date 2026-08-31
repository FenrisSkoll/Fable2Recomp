[CmdletBinding()]
param(
    [string]$Manifest = "fable2_manifest.toml",
    [string]$Provenance = "tools/fable2-entrypoint-closure-evidence.json",
    [string]$OutputDirectory,
    [switch]$NoReviewToml
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$manifestPath = Join-Path $repoRoot $Manifest
$provenancePath = Join-Path $repoRoot $Provenance
$cmakeCachePath = Join-Path $repoRoot "out/build/win-amd64-release/CMakeCache.txt"

if (-not (Test-Path -LiteralPath $cmakeCachePath -PathType Leaf)) {
    throw "Fable II release CMake cache was not found at '$cmakeCachePath'. Run the normal configure/build workflow first."
}

$rexglueDirectoryLine = Select-String `
    -LiteralPath $cmakeCachePath `
    -Pattern '^rexglue_DIR:PATH=(.+)$'

if ($null -eq $rexglueDirectoryLine) {
    throw "rexglue_DIR was not found in '$cmakeCachePath'."
}

$rexglueCmakeDirectory = $rexglueDirectoryLine.Matches[0].Groups[1].Value
$installedSdkRoot = [IO.Path]::GetFullPath(
    (Join-Path $rexglueCmakeDirectory "../../.."))
$rexgluePath = Join-Path $installedSdkRoot "bin/rexglue.exe"

if (-not (Test-Path -LiteralPath $rexgluePath -PathType Leaf)) {
    throw "Installed ReXGlue CLI was not found at '$rexgluePath'. Configure/build the project or reinstall the canonical SDK first."
}

$arguments = @(
    "entrypoint-closure"
    $manifestPath
    "--provenance"
    $provenancePath
)

if ($OutputDirectory) {
    $arguments += "--output"
    $arguments += (Join-Path $repoRoot $OutputDirectory)
}

if ($NoReviewToml) {
    $arguments += "--no-review-toml"
}

Push-Location $repoRoot
try {
    & $rexgluePath @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Entrypoint-closure analysis failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
