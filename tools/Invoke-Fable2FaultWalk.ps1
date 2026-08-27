[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateRange(1, 1000)]
    [int] $Iteration,

    [Parameter(Mandatory = $true)]
    [string] $RunDirectory,

    [ValidateRange(1, 3600)]
    [int] $MonitorSeconds = 120,

    [ValidateRange(1, 1024)]
    [int] $MaxUnique = 32,

    [ValidateRange(1, [long]::MaxValue)]
    [long] $MaxTotalSuppressions = 1000000,

    [ValidateRange(1, [long]::MaxValue)]
    [long] $MaxFunctionSuppressions = 250000,

    [switch] $SkipCodegen,

    [switch] $SkipBuild,

    [switch] $ManualInput
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$resolvedRunDirectory = [IO.Path]::GetFullPath($RunDirectory)
$iterationName = 'iteration-{0:D2}' -f $Iteration
$reportPath = Join-Path $resolvedRunDirectory "$iterationName\fault-walk-report.json"
$bringUpScript = Join-Path $PSScriptRoot 'Invoke-Fable2BringUpIteration.ps1'

$savedMaxUnique = $env:REXGLUE_FAULT_WALK_MAX_UNIQUE
$savedMaxTotal = $env:REXGLUE_FAULT_WALK_MAX_TOTAL_SUPPRESSIONS
$savedMaxFunction = $env:REXGLUE_FAULT_WALK_MAX_FUNCTION_SUPPRESSIONS

try {
    $env:REXGLUE_FAULT_WALK_MAX_UNIQUE = [string] $MaxUnique
    $env:REXGLUE_FAULT_WALK_MAX_TOTAL_SUPPRESSIONS = [string] $MaxTotalSuppressions
    $env:REXGLUE_FAULT_WALK_MAX_FUNCTION_SUPPRESSIONS = [string] $MaxFunctionSuppressions

    & $bringUpScript `
        -Iteration $Iteration `
        -RunDirectory $resolvedRunDirectory `
        -BuildPreset 'win-amd64-fault-walk-release' `
        -MonitorSeconds $MonitorSeconds `
        -FaultWalkReportPath $reportPath `
        -SkipCodegen:$SkipCodegen `
        -SkipBuild:$SkipBuild `
        -ManualInput:$ManualInput `
        -GracefulStop

    exit $LASTEXITCODE
} finally {
    $env:REXGLUE_FAULT_WALK_MAX_UNIQUE = $savedMaxUnique
    $env:REXGLUE_FAULT_WALK_MAX_TOTAL_SUPPRESSIONS = $savedMaxTotal
    $env:REXGLUE_FAULT_WALK_MAX_FUNCTION_SUPPRESSIONS = $savedMaxFunction
}
