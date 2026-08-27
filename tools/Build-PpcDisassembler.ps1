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
$disasmSource = Join-Path $disasmInclude 'disasm.c'
$ppcDisasmSource = Join-Path $disasmInclude 'ppc-dis.c'

New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null

foreach ($requiredSource in @($disasmSource, $ppcDisasmSource)) {
    if (-not (Test-Path -LiteralPath $requiredSource -PathType Leaf)) {
        throw "ReXGlue disassembler source was not found: $requiredSource"
    }
}

$compiler = Get-Command clang-cl.exe -ErrorAction Stop
$compilerArguments = @(
    '/nologo'
    '/std:c++20'
    '/EHsc'
    '/O2'
    "/I$disasmInclude"
    $sourcePath
    $disasmSource
    $ppcDisasmSource
    "/Fe:$outputPath"
)
& $compiler.Source @compilerArguments

if ($LASTEXITCODE -ne 0) {
    throw "ppc-disasm build failed with exit code $LASTEXITCODE"
}

Write-Output $outputPath
