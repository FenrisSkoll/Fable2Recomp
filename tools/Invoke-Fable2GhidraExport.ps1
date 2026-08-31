<#
.SYNOPSIS
Exports a deterministic, byte-free Fable II function map with Ghidra/XEXLoader.

.DESCRIPTION
Imports the audited private GOTY TU1 XEX/XEXP pair, processes an existing
Ghidra project, or restores a supported project archive. The stable map is
written under out/analysis by default. Volatile paths and timing are kept in a
separate run-metadata file. The canonical manifest is never modified.

.EXAMPLE
.\tools\Invoke-Fable2GhidraExport.ps1

.EXAMPLE
.\tools\Invoke-Fable2GhidraExport.ps1 -NoAnalysis -OverwriteProgram

.EXAMPLE
.\tools\Invoke-Fable2GhidraExport.ps1 -ProjectDirectory C:\analysis -ProjectName fable2 -ProgramPath default.xex

.EXAMPLE
.\tools\Invoke-Fable2GhidraExport.ps1 -ProjectArchive C:\downloads\fable2-project.zip -ProgramPath default.xex
#>
[CmdletBinding(DefaultParameterSetName = "RawXex")]
param(
    [Parameter(ParameterSetName = "RawXex")]
    [string]$Xex = "assets/tu1/default.xex",

    [Parameter(ParameterSetName = "RawXex")]
    [string]$Xexp = "assets/tu1/default.xexp",

    [Parameter(Mandatory, ParameterSetName = "ExistingProject")]
    [Parameter(ParameterSetName = "ProjectArchive")]
    [string]$ProgramPath,

    [Parameter(Mandatory, ParameterSetName = "ProjectArchive")]
    [string]$ProjectArchive,

    [string]$ProjectDirectory,
    [string]$ProjectName = "fable2-tu1",
    [string]$Output,
    [string]$GhidraRoot,
    [string]$JavaHome,
    [string]$SourceArtifact = "local-private-fable2-goty-tu1",
    [string]$SourceUrl,
    [string]$SourceVersion,
    [string]$ClaimedEdition = "Fable II Game of the Year Edition",
    [string]$ClaimedRegion,
    [string]$ClaimedTitleUpdate = "TU1",
    [string]$ImageBase,
    [string]$BaseXexSha256,
    [string]$TitleUpdateSha256,
    [string]$PatchedImageSha256,
    [switch]$NoAnalysis,
    [switch]$OverwriteProgram,
    [switch]$AllowRelatedBuild,
    [switch]$AllowVersionMismatch
)

$ErrorActionPreference = "Stop"

$expectedGhidraVersion = "12.1.2"
$expectedBaseXexSha256 = "88C4EF2E18E65409444D1B068EFF921D1F7E180A5AE64EDC64BA6B0872372662"
$expectedTitleUpdateSha256 = "046A05693B4DA4437083C784000A850858B3BF992955C7DB30D518FB3E53E41C"
$expectedPatchedImageSha256 = "BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00"
$expectedXexLoaderTag = "12.1.2"
$expectedXexLoaderCommit = "d0af801aee083c86950b90c3db78b2e1c642067f"
$loaderSelector = "XEXLoaderWVLoader"
$loaderDisplayName = "XEX Loader by Warranty Voider"
$operationMode = $PSCmdlet.ParameterSetName

$repoRoot = Split-Path -Parent $PSScriptRoot
$scriptDirectory = Join-Path $PSScriptRoot "ghidra"
$exporterScript = Join-Path $scriptDirectory "ExportFable2FunctionMap.java"
$loaderPatchScript = Join-Path $PSScriptRoot "Install-Fable2XEXLoaderHeadlessPatch.ps1"
$manifestPath = Join-Path $repoRoot "fable2_manifest.toml"
$manifestHashBefore = (Get-FileHash -Algorithm SHA256 -LiteralPath $manifestPath).Hash

function Resolve-ExistingPath {
    param(
        [Parameter(Mandatory)]
        [string]$Path,
        [Parameter(Mandatory)]
        [string]$Description,
        [ValidateSet("Leaf", "Container")]
        [string]$PathType = "Leaf"
    )

    $candidate = $Path
    if (-not [IO.Path]::IsPathRooted($candidate)) {
        $candidate = Join-Path $repoRoot $candidate
    }
    $candidate = [IO.Path]::GetFullPath($candidate)
    if (-not (Test-Path -LiteralPath $candidate -PathType $PathType)) {
        throw "$Description was not found at '$candidate'."
    }
    return $candidate
}

function Read-PropertiesFile {
    param([Parameter(Mandatory)][string]$Path)

    $properties = @{}
    foreach ($line in Get-Content -LiteralPath $Path) {
        if ($line.StartsWith("#") -or -not $line.Contains("=")) {
            continue
        }
        $parts = $line.Split("=", 2)
        $properties[$parts[0].Trim()] = $parts[1].Trim()
    }
    return $properties
}

if (-not (Test-Path -LiteralPath $exporterScript -PathType Leaf)) {
    throw "Ghidra exporter script was not found at '$exporterScript'."
}

if (-not $GhidraRoot) {
    $GhidraRoot = $env:GHIDRA_HOME
}
if (-not $GhidraRoot) {
    $toolInstallRoot = "C:/Dev/Fable2GhidraTools/install"
    if (Test-Path -LiteralPath $toolInstallRoot -PathType Container) {
        $candidate = Get-ChildItem -LiteralPath $toolInstallRoot -Directory |
            Where-Object { $_.Name -like "ghidra_*_PUBLIC" } |
            Sort-Object Name -Descending |
            Select-Object -First 1
        if ($null -ne $candidate) {
            $GhidraRoot = $candidate.FullName
        }
    }
}
if (-not $GhidraRoot) {
    throw "Ghidra was not located. Pass -GhidraRoot or set GHIDRA_HOME. See docs/fable2-discovery-pipeline/02-ghidra-function-map.md."
}
$GhidraRoot = Resolve-ExistingPath -Path $GhidraRoot -Description "Ghidra root" -PathType Container

$applicationPropertiesPath = Join-Path $GhidraRoot "Ghidra/application.properties"
$applicationPropertiesPath = Resolve-ExistingPath `
    -Path $applicationPropertiesPath `
    -Description "Ghidra application.properties"
$applicationProperties = Read-PropertiesFile -Path $applicationPropertiesPath
$actualGhidraVersion = $applicationProperties["application.version"]
if (-not $AllowVersionMismatch -and $actualGhidraVersion -ne $expectedGhidraVersion) {
    throw "Ghidra $expectedGhidraVersion is required; found '$actualGhidraVersion'. Pass -AllowVersionMismatch only for an explicit migration test."
}

$headlessPath = Join-Path $GhidraRoot "support/analyzeHeadless.bat"
$headlessPath = Resolve-ExistingPath -Path $headlessPath -Description "Ghidra headless launcher"
$extensionCandidates = @(
    (Join-Path $GhidraRoot "Ghidra/Extensions/XEXLoaderWV/extension.properties")
    (Join-Path $env:APPDATA (
        "ghidra/ghidra_{0}_PUBLIC/Extensions/XEXLoaderWV/extension.properties" -f
            $actualGhidraVersion))
)
$extensionPropertiesPath = $extensionCandidates |
    Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } |
    Select-Object -First 1
if (-not $extensionPropertiesPath) {
    $packagedExtension = Join-Path $GhidraRoot "Extensions/Ghidra/XEXLoaderWV/extension.properties"
    $hint = if (Test-Path -LiteralPath $packagedExtension -PathType Leaf) {
        "The extension is unpacked only in Ghidra's distribution directory; install it with File > Install Extensions or copy the XEXLoaderWV directory to the per-user Ghidra Extensions directory."
    }
    else {
        "Install the pinned XEXLoaderWV 12.1.2 release."
    }
    throw "An active XEXLoaderWV extension was not found. $hint"
}
$extensionProperties = Read-PropertiesFile -Path $extensionPropertiesPath
$extensionVersion = $extensionProperties["version"]

if (-not $JavaHome) {
    $JavaHome = $env:JAVA_HOME
}
if (-not $JavaHome) {
    $siblingInstallRoot = Split-Path -Parent $GhidraRoot
    $candidate = Get-ChildItem -LiteralPath $siblingInstallRoot -Directory |
        Where-Object { $_.Name -like "jdk-21*" } |
        Sort-Object Name -Descending |
        Select-Object -First 1
    if ($null -ne $candidate) {
        $JavaHome = $candidate.FullName
    }
}
if (-not $JavaHome) {
    throw "JDK 21 was not located. Pass -JavaHome or set JAVA_HOME."
}
$JavaHome = Resolve-ExistingPath -Path $JavaHome -Description "JDK 21 root" -PathType Container
$javaPath = Resolve-ExistingPath `
    -Path (Join-Path $JavaHome "bin/java.exe") `
    -Description "JDK Java executable"
$javaVersionOutput = & $javaPath -version 2>&1
if ($LASTEXITCODE -ne 0 -or $javaVersionOutput[0] -notmatch 'version "21\.') {
    throw "Ghidra $expectedGhidraVersion requires JDK 21; '$javaPath' reported: $($javaVersionOutput -join ' ')"
}
$env:JAVA_HOME = $JavaHome

if (-not (Test-Path -LiteralPath $loaderPatchScript -PathType Leaf)) {
    throw "XEXLoader compatibility verifier was not found at '$loaderPatchScript'."
}
& $loaderPatchScript -GhidraRoot $GhidraRoot -JavaHome $JavaHome -CheckOnly
if ($LASTEXITCODE -ne 0) {
    throw "XEXLoader compatibility verification failed."
}

if (-not $ProjectDirectory) {
    $ProjectDirectory = Join-Path $repoRoot "out/ghidra/projects"
}
elseif (-not [IO.Path]::IsPathRooted($ProjectDirectory)) {
    $ProjectDirectory = Join-Path $repoRoot $ProjectDirectory
}
$ProjectDirectory = [IO.Path]::GetFullPath($ProjectDirectory)

if ($PSCmdlet.ParameterSetName -eq "ProjectArchive") {
    $archivePath = Resolve-ExistingPath -Path $ProjectArchive -Description "Ghidra project archive"
    $archiveExtension = [IO.Path]::GetExtension($archivePath).ToLowerInvariant()
    if ($archiveExtension -eq ".zip") {
        $archiveName = [IO.Path]::GetFileNameWithoutExtension($archivePath)
        $extractDirectory = Join-Path $ProjectDirectory ("archive-" + $archiveName)
        if (Test-Path -LiteralPath $extractDirectory) {
            throw "Archive extraction target '$extractDirectory' already exists. Choose a new -ProjectDirectory to avoid overwriting a database."
        }
        New-Item -ItemType Directory -Force -Path $extractDirectory | Out-Null
        Expand-Archive -LiteralPath $archivePath -DestinationPath $extractDirectory
        $projectFiles = @(Get-ChildItem -LiteralPath $extractDirectory -Recurse -File -Filter "*.gpr")
        if ($projectFiles.Count -ne 1) {
            throw "Expected one .gpr in '$archivePath'; found $($projectFiles.Count). Restore the project manually if this is not a standard zipped .gpr/.rep pair."
        }
        $ProjectDirectory = $projectFiles[0].DirectoryName
        $ProjectName = [IO.Path]::GetFileNameWithoutExtension($projectFiles[0].Name)
        if (-not $ProgramPath) {
            throw "Pass -ProgramPath with the domain path of the program to export from '$archivePath'."
        }
    }
    elseif ($archiveExtension -eq ".gzf") {
        New-Item -ItemType Directory -Force -Path $ProjectDirectory | Out-Null
        $operationMode = "GzfImport"
    }
    else {
        throw "Unsupported archive '$archivePath'. Use a .zip containing one .gpr/.rep pair or a Ghidra .gzf export. GUI-only .gar restoration is not automated."
    }
}

if (-not $Output) {
    $Output = Join-Path $repoRoot (
        "out/analysis/{0}/ghidra-function-map.json" -f $expectedPatchedImageSha256)
}
elseif (-not [IO.Path]::IsPathRooted($Output)) {
    $Output = Join-Path $repoRoot $Output
}
$Output = [IO.Path]::GetFullPath($Output)
$outputDirectory = Split-Path -Parent $Output
New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null

$gitCommit = (& git -C $repoRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0) {
    throw "Unable to determine the Fable2Recomp exporter commit."
}

$headlessArguments = [System.Collections.Generic.List[string]]::new()
$sourceKind = "ghidra_project"

if ($operationMode -eq "RawXex") {
    $xexPath = Resolve-ExistingPath -Path $Xex -Description "Fable II XEX"
    $xexpPath = Resolve-ExistingPath -Path $Xexp -Description "Fable II XEXP"
    $actualBaseHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $xexPath).Hash
    $actualTitleUpdateHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $xexpPath).Hash
    if (-not $AllowRelatedBuild -and (
            $actualBaseHash -ne $expectedBaseXexSha256 -or
            $actualTitleUpdateHash -ne $expectedTitleUpdateSha256)) {
        throw "Private inputs are not the exact audited GOTY TU1 pair. Base=$actualBaseHash XEXP=$actualTitleUpdateHash. Use -AllowRelatedBuild only for quarantined comparative analysis."
    }
    $BaseXexSha256 = $actualBaseHash
    $TitleUpdateSha256 = $actualTitleUpdateHash
    if ($actualBaseHash -eq $expectedBaseXexSha256 -and
            $actualTitleUpdateHash -eq $expectedTitleUpdateSha256) {
        $PatchedImageSha256 = $expectedPatchedImageSha256
        if (-not $ImageBase) {
            $ImageBase = "0x82000000"
        }
    }
    else {
        $PatchedImageSha256 = $null
        $SourceArtifact = "local-private-related-build"
    }
    $sourceKind = "raw_xex_with_xexp"
    New-Item -ItemType Directory -Force -Path $ProjectDirectory | Out-Null
    $headlessArguments.Add($ProjectDirectory)
    $headlessArguments.Add($ProjectName)
    $headlessArguments.Add("-import")
    $headlessArguments.Add($xexPath)
    $headlessArguments.Add("-loader")
    $headlessArguments.Add($loaderSelector)
    $headlessArguments.Add("-loader-xexp")
    $headlessArguments.Add($xexpPath)
    if ($OverwriteProgram) {
        $headlessArguments.Add("-overwrite")
    }
}
elseif ($operationMode -eq "GzfImport") {
    $headlessArguments.Add($ProjectDirectory)
    $headlessArguments.Add($ProjectName)
    $headlessArguments.Add("-import")
    $headlessArguments.Add($archivePath)
    $sourceKind = "ghidra_gzf"
}
else {
    $ProjectDirectory = Resolve-ExistingPath `
        -Path $ProjectDirectory `
        -Description "Ghidra project directory" `
        -PathType Container
    $projectFile = Join-Path $ProjectDirectory ($ProjectName + ".gpr")
    $null = Resolve-ExistingPath -Path $projectFile -Description "Ghidra project file"
    $headlessArguments.Add($ProjectDirectory)
    $headlessArguments.Add($ProjectName)
    $headlessArguments.Add("-process")
    $headlessArguments.Add($ProgramPath)
    $sourceKind = if ($operationMode -eq "ProjectArchive") {
        "zipped_ghidra_project"
    }
    else {
        "ghidra_project"
    }
}

if ($NoAnalysis) {
    $headlessArguments.Add("-noanalysis")
}
$headlessArguments.Add("-scriptPath")
$headlessArguments.Add($scriptDirectory)
$headlessArguments.Add("-postScript")
$headlessArguments.Add("ExportFable2FunctionMap.java")
$headlessArguments.Add("--output=$Output")
$headlessArguments.Add("--source-artifact=$SourceArtifact")
$headlessArguments.Add("--source-kind=$sourceKind")
$headlessArguments.Add("--source-url=$SourceUrl")
$headlessArguments.Add("--source-version=$SourceVersion")
$headlessArguments.Add("--claimed-edition=$ClaimedEdition")
$headlessArguments.Add("--claimed-region=$ClaimedRegion")
$headlessArguments.Add("--claimed-title-update=$ClaimedTitleUpdate")
$headlessArguments.Add("--image-base=$ImageBase")
$headlessArguments.Add("--base-xex-sha256=$BaseXexSha256")
$headlessArguments.Add("--title-update-sha256=$TitleUpdateSha256")
$headlessArguments.Add("--patched-image-sha256=$PatchedImageSha256")
$headlessArguments.Add("--exporter-commit=$gitCommit")
$headlessArguments.Add(
    "--xexloader-version=tag-$expectedXexLoaderTag-commit-$expectedXexLoaderCommit-extension-$extensionVersion")
$headlessArguments.Add("--loader-name=$loaderDisplayName")

$started = Get-Date
& $headlessPath @headlessArguments
$exitCode = $LASTEXITCODE
$elapsed = (Get-Date) - $started
if ($exitCode -ne 0) {
    throw "Ghidra headless export failed with exit code $exitCode. Review the headless log above; no map should be trusted from this run."
}
if (-not (Test-Path -LiteralPath $Output -PathType Leaf)) {
    throw "Ghidra reported success but did not create '$Output'."
}

$manifestHashAfter = (Get-FileHash -Algorithm SHA256 -LiteralPath $manifestPath).Hash
if ($manifestHashAfter -ne $manifestHashBefore) {
    throw "Report-only invariant failed: fable2_manifest.toml changed during export."
}

$runMetadataPath = Join-Path $outputDirectory "ghidra-export-run.json"
$runMetadata = [ordered]@{
    schema_version = 1
    stable_map = $Output
    completed_utc = (Get-Date).ToUniversalTime().ToString("o")
    elapsed_milliseconds = [long]$elapsed.TotalMilliseconds
    ghidra_root = $GhidraRoot
    java_home = $JavaHome
    project_directory = $ProjectDirectory
    project_name = $ProjectName
    command_mode = $operationMode
}
$runMetadata |
    ConvertTo-Json -Depth 4 |
    Set-Content -LiteralPath $runMetadataPath -Encoding utf8NoBOM

Write-Output "Ghidra function map: $Output"
Write-Output "Volatile export metadata: $runMetadataPath"
Write-Output ("Elapsed: {0:N1} s" -f $elapsed.TotalSeconds)
