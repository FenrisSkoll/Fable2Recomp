[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repository = Split-Path -Parent $PSScriptRoot
$schema = Join-Path $PSScriptRoot 'schemas/fable2-prototype-semantics-v1.schema.json'
$summaryPath = Join-Path $repository 'docs/fable2-prototype-archaeology/phase2b/evidence/semantic-validation.json'
$summary = Get-Content -LiteralPath $summaryPath -Raw | ConvertFrom-Json
$relativePaths = @(
    'docs/fable2-prototype-archaeology/phase2b/evidence/semantic-source-pins.json'
    'docs/fable2-prototype-archaeology/phase2b/evidence/semantic-validation.json'
) + @($summary.artifacts.path)
foreach ($relativePath in ($relativePaths | Sort-Object)) {
    $path = [IO.Path]::GetFullPath((Join-Path $repository $relativePath))
    if (-not $path.StartsWith($repository + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Evidence path escapes repository: $relativePath"
    }
    $document = Get-Content -LiteralPath $path -Raw
    if (-not (Test-Json -Json $document -SchemaFile $schema -ErrorAction Stop)) {
        throw "Schema validation failed: $relativePath"
    }
    Write-Output "PASS schema: $relativePath"
}
