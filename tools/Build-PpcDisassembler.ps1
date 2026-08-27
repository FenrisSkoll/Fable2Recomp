[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$sourcePath = Join-Path $PSScriptRoot 'ppc-disasm.cpp'
$outputDirectory = Join-Path $repositoryRoot 'out\tools'
$outputPath = Join-Path $outputDirectory 'ppc-disasm.exe'
$sdkRoot = 'C:\Dev\rexglue-sdk'
$disasmInclude = Join-Path $sdkRoot 'thirdparty\disasm'
$disasmLibrary = Join-Path $sdkRoot 'out\install\win-amd64\lib\disasm.lib'

New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null

if (-not (Test-Path -LiteralPath $disasmLibrary -PathType Leaf)) {
    throw "ReXGlue disassembler library was not found: $disasmLibrary"
}

$compiler = Get-Command clang-cl.exe -ErrorAction Stop
$compilerArguments = @(
    '/nologo'
    '/std:c++20'
    '/EHsc'
    '/O2'
    "/I$disasmInclude"
    $sourcePath
    "/Fe:$outputPath"
    '/link'
    $disasmLibrary
)
& $compiler.Source @compilerArguments

if ($LASTEXITCODE -ne 0) {
    throw "ppc-disasm build failed with exit code $LASTEXITCODE"
}

Write-Output $outputPath
