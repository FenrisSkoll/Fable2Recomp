[CmdletBinding()]
param(
    [string]$EvidenceDirectory = (Join-Path $PSScriptRoot '..\docs\fable2-prototype-archaeology\phase1\evidence'),
    [string]$SchemaPath = (Join-Path $PSScriptRoot 'schemas\fable2-prototype-archaeology-v1.schema.json')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$resolvedEvidence = Resolve-Path -LiteralPath $EvidenceDirectory
$resolvedSchema = Resolve-Path -LiteralPath $SchemaPath
$artifacts = @(Get-ChildItem -LiteralPath $resolvedEvidence.Path -Filter '*.json' -File | Sort-Object Name)

if ($artifacts.Count -eq 0) {
    throw "No JSON artifacts were found in $($resolvedEvidence.Path)."
}

foreach ($artifact in $artifacts) {
    $document = Get-Content -LiteralPath $artifact.FullName -Raw
    $valid = $document | Test-Json -SchemaFile $resolvedSchema.Path

    if (-not $valid) {
        throw "Schema validation failed for $($artifact.FullName)."
    }
}

Write-Host "Validated $($artifacts.Count) prototype archaeology JSON artifacts against $($resolvedSchema.Path)."
