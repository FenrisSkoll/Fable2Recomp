[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repository = Split-Path -Parent $PSScriptRoot
$schemaPath = Join-Path $PSScriptRoot 'schemas/fable2-prototype-review-v1.schema.json'
$evidenceRoots = @(
    (Join-Path $repository 'docs/fable2-prototype-archaeology/phase2d/evidence'),
    (Join-Path $repository 'out/prototype-archaeology/phase2d')
)
$files = Get-ChildItem -LiteralPath $evidenceRoots -Filter '*.json' -File -Recurse | Sort-Object FullName
foreach ($file in $files) {
    $document = [IO.File]::ReadAllText($file.FullName)
    if (-not (Test-Json -Json $document -SchemaFile $schemaPath -ErrorAction Stop)) {
        throw "Phase 2D schema validation failed: $($file.Name)"
    }
    Write-Output "PASS schema: $($file.Name)"
}
Write-Output "PASS Phase 2D schema documents: $($files.Count)"
