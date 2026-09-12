[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repository = Split-Path -Parent $PSScriptRoot
$schemaPath = Join-Path $PSScriptRoot 'schemas/fable2-prototype-trust-v1.schema.json'
$evidenceRoots = @(
    (Join-Path $repository 'docs/fable2-prototype-archaeology/phase2c/evidence'),
    (Join-Path $repository 'out/prototype-archaeology/phase2c')
)
$files = Get-ChildItem -LiteralPath $evidenceRoots -Filter '*.json' -File -Recurse | Sort-Object FullName
foreach ($file in $files) {
    $document = Get-Content -LiteralPath $file.FullName -Raw
    $schemaName = ($document | ConvertFrom-Json -Depth 100).schema.name
    $selectedSchema = $schemaPath
    if ($schemaName.StartsWith('fable2-prototype-completion-')) {
        $selectedSchema = Join-Path $PSScriptRoot 'schemas/fable2-prototype-completion-v1.schema.json'
    }
    if (-not (Test-Json -Json $document -SchemaFile $selectedSchema -ErrorAction Stop)) {
        throw "Phase 2C schema validation failed: $($file.FullName)"
    }
    Write-Output "PASS schema: $($file.Name)"
}
