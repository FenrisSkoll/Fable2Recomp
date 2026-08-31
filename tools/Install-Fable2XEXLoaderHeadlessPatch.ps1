<#
.SYNOPSIS
Installs or verifies the pinned Fable II headless compatibility patch for XEXLoaderWV.

.DESCRIPTION
Validates the public XEXLoaderWV 12.1.2 source, makes its XEXP path available
to analyzeHeadless, and replaces an overlap-unsafe XEXP copy with
System.arraycopy. No Fable II executable bytes are read or written.

.EXAMPLE
.\tools\Install-Fable2XEXLoaderHeadlessPatch.ps1 -GhidraRoot C:\Tools\ghidra_12.1.2_PUBLIC -JavaHome C:\Tools\jdk-21

.EXAMPLE
.\tools\Install-Fable2XEXLoaderHeadlessPatch.ps1 -GhidraRoot C:\Tools\ghidra_12.1.2_PUBLIC -JavaHome C:\Tools\jdk-21 -CheckOnly
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$GhidraRoot,

    [Parameter(Mandatory)]
    [string]$JavaHome,

    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"

$expectedSourceZipSha256 = "AB33C3C364357E1C1DCBDF7B3120CCA345EB00F6D16675BE099B293FAD9A5FF9"
$expectedUpstreamClassSha256 = "DA1D311FAF3D45595190C1AA7BEBD1B9EFB5C9D1240BA1C7814AA725DA26B367"
$expectedPatchedClassSha256 = "C0ACB6B1A4F8DF7638A96E8CDF97CC47C7B30447D43E725028F087FE5FAE124C"
$classEntry = "xexloaderwv/XEXLoaderWVLoader.class"

function Resolve-RequiredPath {
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

function Get-JarEntryHash {
    param(
        [Parameter(Mandatory)][string]$JarPath,
        [Parameter(Mandatory)][string]$Entry,
        [Parameter(Mandatory)][string]$JarTool,
        [Parameter(Mandatory)][string]$TemporaryRoot
    )

    $extractRoot = Join-Path $TemporaryRoot "entry"
    New-Item -ItemType Directory -Path $extractRoot | Out-Null
    Push-Location $extractRoot
    try {
        & $JarTool --extract --file $JarPath $Entry
        if ($LASTEXITCODE -ne 0) {
            throw "Could not extract '$Entry' from '$JarPath'."
        }
    }
    finally {
        Pop-Location
    }
    $entryPath = Join-Path $extractRoot ($Entry.Replace("/", [IO.Path]::DirectorySeparatorChar))
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $entryPath).Hash
}

$GhidraRoot = Resolve-RequiredPath -Path $GhidraRoot -Description "Ghidra root" -PathType Container
$JavaHome = Resolve-RequiredPath -Path $JavaHome -Description "JDK root" -PathType Container
$jarTool = Resolve-RequiredPath -Path (Join-Path $JavaHome "bin/jar.exe") -Description "JDK jar tool"
$javacTool = Resolve-RequiredPath -Path (Join-Path $JavaHome "bin/javac.exe") -Description "JDK compiler"
$extensionRoot = Join-Path $GhidraRoot "Ghidra/Extensions/XEXLoaderWV"
$loaderJar = Resolve-RequiredPath -Path (Join-Path $extensionRoot "lib/XEXLoaderWV.jar") -Description "XEXLoaderWV jar"
$sourceZip = Resolve-RequiredPath -Path (Join-Path $extensionRoot "lib/XEXLoaderWV-src.zip") -Description "XEXLoaderWV source archive"

$sourceZipHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $sourceZip).Hash
if ($sourceZipHash -ne $expectedSourceZipSha256) {
    throw "Unsupported XEXLoaderWV source archive: expected $expectedSourceZipSha256, got $sourceZipHash. Install the pinned 12.1.2 release."
}

$temporaryRoot = Join-Path ([IO.Path]::GetTempPath()) ("fable2-xexloader-patch-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $temporaryRoot | Out-Null
try {
    $currentClassHash = Get-JarEntryHash `
        -JarPath $loaderJar `
        -Entry $classEntry `
        -JarTool $jarTool `
        -TemporaryRoot $temporaryRoot
    if ($currentClassHash -eq $expectedPatchedClassSha256) {
        Write-Output "PASS: XEXLoaderWV Fable II headless patch is installed ($currentClassHash)."
        exit 0
    }
    if ($currentClassHash -ne $expectedUpstreamClassSha256) {
        throw "Unsupported XEXLoaderWV loader class: expected upstream $expectedUpstreamClassSha256 or patched $expectedPatchedClassSha256, got $currentClassHash."
    }
    if ($CheckOnly) {
        throw "The pinned XEXLoaderWV is unpatched. Run this command again without -CheckOnly before exporting TU1."
    }

    $sourceRoot = Join-Path $temporaryRoot "source"
    Expand-Archive -LiteralPath $sourceZip -DestinationPath $sourceRoot
    $sourcePath = Join-Path $sourceRoot "src/main/java/xexloaderwv/XEXLoaderWVLoader.java"
    $sourceText = Get-Content -Raw -LiteralPath $sourcePath

    $oldOption = 'new Option("Path to xexp", "")'
    $newOption = 'new Option("Path to xexp", "", String.class, "-loader-xexp")'
    $copyPattern = '(?m)^\s*for \(int i = 0; i < delta_patch\.uncompressed_len; i\+\+\)\r?\n\s*buffROM\[headerSize \+ delta_patch\.new_addr \+ i\] = buffROM\[headerSize \+ delta_patch\.old_addr\r?\n\s*\+ i\];'
    $newCopy = "`t`t`t`t`t`tSystem.arraycopy(buffROM, headerSize + delta_patch.old_addr, buffROM,`n`t`t`t`t`t`t`t`theaderSize + delta_patch.new_addr, delta_patch.uncompressed_len);"

    if (-not $sourceText.Contains($oldOption)) {
        throw "Pinned source no longer contains the expected headless XEXP option."
    }
    if ([regex]::Matches($sourceText, $copyPattern).Count -ne 1) {
        throw "Pinned source no longer contains exactly one expected overlap-unsafe XEXP copy."
    }
    $sourceText = $sourceText.Replace($oldOption, $newOption)
    $sourceText = [regex]::Replace($sourceText, $copyPattern, $newCopy)
    Set-Content -LiteralPath $sourcePath -Value $sourceText -Encoding utf8NoBOM

    $compileRoot = Join-Path $temporaryRoot "classes"
    New-Item -ItemType Directory -Path $compileRoot | Out-Null
    $classPathJars = @(
        Get-ChildItem -LiteralPath $GhidraRoot -Recurse -File -Filter "*.jar" |
            Select-Object -ExpandProperty FullName
    )
    $classPath = $classPathJars -join ";"
    & $javacTool -proc:none -encoding UTF-8 -classpath $classPath -d $compileRoot $sourcePath
    if ($LASTEXITCODE -ne 0) {
        throw "Compilation of the compatibility-patched XEXLoaderWV loader failed."
    }
    $patchedClass = Join-Path $compileRoot ($classEntry.Replace("/", [IO.Path]::DirectorySeparatorChar))
    $patchedClassHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $patchedClass).Hash
    if ($patchedClassHash -ne $expectedPatchedClassSha256) {
        throw "Patched class hash mismatch: expected $expectedPatchedClassSha256, got $patchedClassHash."
    }

    $backupPath = "$loaderJar.upstream-$expectedUpstreamClassSha256.bak"
    if (-not (Test-Path -LiteralPath $backupPath -PathType Leaf)) {
        Copy-Item -LiteralPath $loaderJar -Destination $backupPath
    }
    & $jarTool --update --file $loaderJar -C $compileRoot $classEntry
    if ($LASTEXITCODE -ne 0) {
        throw "Updating '$loaderJar' failed; the upstream backup is '$backupPath'."
    }

    $verifyRoot = Join-Path $temporaryRoot "verify"
    New-Item -ItemType Directory -Path $verifyRoot | Out-Null
    $installedHash = Get-JarEntryHash `
        -JarPath $loaderJar `
        -Entry $classEntry `
        -JarTool $jarTool `
        -TemporaryRoot $verifyRoot
    if ($installedHash -ne $expectedPatchedClassSha256) {
        throw "Installed loader class hash mismatch: expected $expectedPatchedClassSha256, got $installedHash. Restore '$backupPath'."
    }
    Write-Output "Installed XEXLoaderWV Fable II headless patch ($installedHash)."
    Write-Output "Upstream backup: $backupPath"
}
finally {
    $resolvedTemporaryRoot = [IO.Path]::GetFullPath($temporaryRoot)
    $resolvedSystemTemp = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if ($resolvedTemporaryRoot.StartsWith($resolvedSystemTemp, [StringComparison]::OrdinalIgnoreCase)) {
        Remove-Item -LiteralPath $resolvedTemporaryRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
