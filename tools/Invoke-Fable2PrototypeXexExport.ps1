<#
.SYNOPSIS
Imports one prototype XEX with the pinned Ghidra/XEXLoader toolchain and exports
its initialized image into a repository-owned analysis directory.

.DESCRIPTION
The source XEX is opened read-only by Ghidra. The Ghidra project, decrypted
memory blocks, metadata, and volatile run metadata are written beneath this
repository. The prototype source tree and fable2_manifest.toml are never
modified.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Xex,

    [Parameter(Mandatory)]
    [string]$BuildId,

    [Parameter(Mandatory)]
    [string]$RelativePath,

    [string]$Xexp,
    [string]$Output,
    [string]$ProjectDirectory,
    [string]$GhidraRoot,
    [string]$JavaHome,
    [switch]$CanonicalTu1,
    [switch]$RelatedTitleUpdate,
    [switch]$OverwriteProgram
)

$ErrorActionPreference = "Stop"

$expectedGhidraVersion = "12.1.2"
$expectedXexLoaderCommit = "d0af801aee083c86950b90c3db78b2e1c642067f"
$repoRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$prototypeRoot = [IO.Path]::GetFullPath("D:\Fable2-Recomp\prototypes")
$scriptDirectory = Join-Path $PSScriptRoot "ghidra"
$exporterScript = Join-Path $scriptDirectory "ExportFable2PrototypeImage.java"
$loaderVerifier = Join-Path $PSScriptRoot "Install-Fable2XEXLoaderHeadlessPatch.ps1"
$manifestPath = Join-Path $repoRoot "fable2_manifest.toml"

function Resolve-ExistingPath {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Description,
        [ValidateSet("Leaf", "Container")][string]$PathType = "Leaf"
    )

    $resolved = [IO.Path]::GetFullPath($Path)
    if (-not (Test-Path -LiteralPath $resolved -PathType $PathType)) {
        throw "$Description was not found at '$resolved'."
    }
    return $resolved
}

function Assert-PathBelow {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][string]$Description
    )

    $resolvedPath = [IO.Path]::GetFullPath($Path)
    $resolvedRoot = [IO.Path]::GetFullPath($Root).TrimEnd('\') + '\'
    if (-not $resolvedPath.StartsWith($resolvedRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw "$Description '$resolvedPath' must be beneath '$resolvedRoot'."
    }
    return $resolvedPath
}

$xexPath = Resolve-ExistingPath -Path $Xex -Description "Prototype XEX"
$sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $xexPath).Hash
$sourceSize = (Get-Item -LiteralPath $xexPath).Length
$titleUpdateHash = $null
$titleUpdateSize = $null
if ($CanonicalTu1 -and $RelatedTitleUpdate) {
    throw "-CanonicalTu1 and -RelatedTitleUpdate are mutually exclusive."
}
if ($CanonicalTu1) {
    $null = Assert-PathBelow -Path $xexPath -Root $repoRoot -Description "Canonical TU1 XEX"
    if ($sourceHash -ne "88C4EF2E18E65409444D1B068EFF921D1F7E180A5AE64EDC64BA6B0872372662") {
        throw "Canonical TU1 base XEX has unexpected SHA-256 $sourceHash."
    }
    if (-not $Xexp) {
        throw "-CanonicalTu1 requires -Xexp."
    }
    $xexpPath = Resolve-ExistingPath -Path $Xexp -Description "Canonical TU1 XEXP"
    $null = Assert-PathBelow -Path $xexpPath -Root $repoRoot -Description "Canonical TU1 XEXP"
    $titleUpdateHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $xexpPath).Hash
    $titleUpdateSize = (Get-Item -LiteralPath $xexpPath).Length
    if ($titleUpdateHash -ne "046A05693B4DA4437083C784000A850858B3BF992955C7DB30D518FB3E53E41C") {
        throw "Canonical TU1 XEXP has unexpected SHA-256 $titleUpdateHash."
    }
}
elseif ($RelatedTitleUpdate) {
    if ($sourceHash -eq "88C4EF2E18E65409444D1B068EFF921D1F7E180A5AE64EDC64BA6B0872372662") {
        $null = Assert-PathBelow -Path $xexPath -Root $repoRoot -Description "Canonical base XEX"
    }
    else {
        $null = Assert-PathBelow -Path $xexPath -Root $prototypeRoot -Description "Prototype XEX"
    }
    if (-not $Xexp) {
        throw "-RelatedTitleUpdate requires -Xexp."
    }
    $xexpPath = Resolve-ExistingPath -Path $Xexp -Description "Related XEXP"
    $null = Assert-PathBelow -Path $xexpPath -Root $repoRoot -Description "Related XEXP"
    $titleUpdateHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $xexpPath).Hash
    $titleUpdateSize = (Get-Item -LiteralPath $xexpPath).Length
}
else {
    $null = Assert-PathBelow -Path $xexPath -Root $prototypeRoot -Description "Prototype XEX"
    if ($Xexp) {
        throw "-Xexp is supported only with -CanonicalTu1."
    }
}
$safeBuildId = $BuildId -replace '[^A-Za-z0-9_.-]', '_'
$relativePathBase64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($RelativePath))

if (-not $Output) {
    $Output = Join-Path $repoRoot "out/prototype-archaeology/derived/$safeBuildId"
}
$Output = Assert-PathBelow -Path $Output -Root $repoRoot -Description "Output"

if (-not $ProjectDirectory) {
    $ProjectDirectory = Join-Path $repoRoot "out/prototype-archaeology/ghidra-projects"
}
$ProjectDirectory = Assert-PathBelow `
    -Path $ProjectDirectory `
    -Root $repoRoot `
    -Description "Ghidra project directory"

if (-not $GhidraRoot) {
    $candidate = Get-ChildItem -LiteralPath "C:\Dev\Fable2GhidraTools\install" -Directory |
        Where-Object { $_.Name -eq "ghidra_${expectedGhidraVersion}_PUBLIC" } |
        Select-Object -First 1
    if ($null -ne $candidate) {
        $GhidraRoot = $candidate.FullName
    }
}
$GhidraRoot = Resolve-ExistingPath -Path $GhidraRoot -Description "Ghidra root" -PathType Container

if (-not $JavaHome) {
    $candidate = Get-ChildItem -LiteralPath (Split-Path -Parent $GhidraRoot) -Directory |
        Where-Object { $_.Name -like "jdk-21*" } |
        Sort-Object Name -Descending |
        Select-Object -First 1
    if ($null -ne $candidate) {
        $JavaHome = $candidate.FullName
    }
}
$JavaHome = Resolve-ExistingPath -Path $JavaHome -Description "JDK 21 root" -PathType Container
$env:JAVA_HOME = $JavaHome

$applicationProperties = Join-Path $GhidraRoot "Ghidra\application.properties"
$versionLine = Get-Content -LiteralPath $applicationProperties |
    Where-Object { $_ -like "application.version=*" } |
    Select-Object -First 1
$actualGhidraVersion = $versionLine.Split("=", 2)[1].Trim()
if ($actualGhidraVersion -ne $expectedGhidraVersion) {
    throw "Ghidra $expectedGhidraVersion is required; found '$actualGhidraVersion'."
}

& $loaderVerifier -GhidraRoot $GhidraRoot -JavaHome $JavaHome -CheckOnly
if ($LASTEXITCODE -ne 0) {
    throw "XEXLoader compatibility verification failed."
}

$headless = Resolve-ExistingPath `
    -Path (Join-Path $GhidraRoot "support\analyzeHeadless.bat") `
    -Description "Ghidra headless launcher"
$null = Resolve-ExistingPath -Path $exporterScript -Description "Prototype exporter"
$manifestHashBefore = (Get-FileHash -Algorithm SHA256 -LiteralPath $manifestPath).Hash
$gitCommit = (& git -C $repoRoot rev-parse HEAD).Trim()

New-Item -ItemType Directory -Force -Path $Output | Out-Null
New-Item -ItemType Directory -Force -Path $ProjectDirectory | Out-Null
$stagedSourceDirectory = Join-Path $Output "source"
New-Item -ItemType Directory -Force -Path $stagedSourceDirectory | Out-Null
$stagedXexPath = Join-Path $stagedSourceDirectory "default.xex"
if (Test-Path -LiteralPath $stagedXexPath -PathType Leaf) {
    $stagedHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $stagedXexPath).Hash
    if ($stagedHash -ne $sourceHash) {
        throw "Existing staged XEX '$stagedXexPath' does not match source hash $sourceHash."
    }
}
else {
    Copy-Item -LiteralPath $xexPath -Destination $stagedXexPath
    $stagedHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $stagedXexPath).Hash
    if ($stagedHash -ne $sourceHash) {
        throw "Staged XEX hash $stagedHash does not match source hash $sourceHash."
    }
}
$stagedXexpPath = $null
if ($CanonicalTu1 -or $RelatedTitleUpdate) {
    $stagedXexpPath = Join-Path $stagedSourceDirectory "default.xexp"
    if (Test-Path -LiteralPath $stagedXexpPath -PathType Leaf) {
        $stagedXexpHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $stagedXexpPath).Hash
        if ($stagedXexpHash -ne $titleUpdateHash) {
            throw "Existing staged XEXP does not match source hash $titleUpdateHash."
        }
    }
    else {
        Copy-Item -LiteralPath $xexpPath -Destination $stagedXexpPath
    }
}
$projectName = "prototype-$safeBuildId"
$arguments = [System.Collections.Generic.List[string]]::new()
$arguments.Add($ProjectDirectory)
$arguments.Add($projectName)
$arguments.Add("-import")
$arguments.Add($stagedXexPath)
$arguments.Add("-loader")
$arguments.Add("XEXLoaderWVLoader")
if ($CanonicalTu1 -or $RelatedTitleUpdate) {
    $arguments.Add("-loader-xexp")
    $arguments.Add($stagedXexpPath)
}
$arguments.Add("-noanalysis")
if ($OverwriteProgram) {
    $arguments.Add("-overwrite")
}
$arguments.Add("-scriptPath")
$arguments.Add($scriptDirectory)
$arguments.Add("-postScript")
$arguments.Add("ExportFable2PrototypeImage.java")
$arguments.Add("--output-directory=$Output")
$arguments.Add("--build-id=$BuildId")
$arguments.Add("--relative-path-base64=$relativePathBase64")
$arguments.Add("--source-sha256=$sourceHash")
$arguments.Add("--source-size=$sourceSize")
if ($CanonicalTu1 -or $RelatedTitleUpdate) {
    $arguments.Add("--title-update-sha256=$titleUpdateHash")
    $arguments.Add("--title-update-size=$titleUpdateSize")
}
$arguments.Add("--exporter-commit=$gitCommit")
$arguments.Add("--xexloader-version=ghidra-$expectedGhidraVersion-commit-$expectedXexLoaderCommit")

$started = Get-Date
& $headless @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Ghidra prototype export failed with exit code $LASTEXITCODE."
}

$derivedMetadata = Join-Path $Output "derived-image.json"
if (-not (Test-Path -LiteralPath $derivedMetadata -PathType Leaf)) {
    throw "Ghidra did not create '$derivedMetadata'."
}
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $manifestPath).Hash -ne $manifestHashBefore) {
    throw "Report-only invariant failed: fable2_manifest.toml changed during export."
}

$elapsed = (Get-Date) - $started
$runMetadata = [ordered]@{
    schema = [ordered]@{ name = "fable2-prototype-xex-export-run"; version = 1 }
    completed_utc = (Get-Date).ToUniversalTime().ToString("o")
    elapsed_milliseconds = [long]$elapsed.TotalMilliseconds
    source_path = $xexPath
    source_sha256 = $sourceHash
    staged_source_path = $stagedXexPath
    staged_source_sha256 = $stagedHash
    title_update_path = $xexpPath
    title_update_sha256 = $titleUpdateHash
    staged_title_update_path = $stagedXexpPath
    output_directory = $Output
    project_directory = $ProjectDirectory
    project_name = $projectName
}
$runMetadata |
    ConvertTo-Json -Depth 4 |
    Set-Content -LiteralPath (Join-Path $Output "derived-image-run.json") -Encoding utf8NoBOM

Write-Output "Prototype image metadata: $derivedMetadata"
Write-Output ("Elapsed: {0:N1} s" -f $elapsed.TotalSeconds)
