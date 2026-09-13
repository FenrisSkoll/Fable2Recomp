$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$schemaPath = Join-Path $repositoryRoot 'tools\schemas\phase2f\fable2-semantic-routes-v1.schema.json'
$documentRoots = @(
    (Join-Path $repositoryRoot 'docs\fable2-prototype-archaeology\phase2f\evidence'),
    (Join-Path $repositoryRoot 'out\prototype-archaeology\phase2f')
)
$files = @()
foreach ($documentRoot in $documentRoots) {
    $files += Get-ChildItem -LiteralPath $documentRoot -File -Filter '*.json'
}
foreach ($file in ($files | Sort-Object FullName)) {
    $document = [IO.File]::ReadAllText($file.FullName)
    if (-not (Test-Json -Json $document -SchemaFile $schemaPath -ErrorAction Stop)) {
        throw "Phase 2F schema validation failed: $($file.Name)"
    }
    Write-Output "PASS schema: $($file.Name)"
}
Write-Output "PASS Phase 2F schema documents: $($files.Count)"
