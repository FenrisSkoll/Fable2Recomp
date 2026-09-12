$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$schemaPath = Join-Path $repositoryRoot 'tools\schemas\phase2e\fable2-prototype-overlay-v1.schema.json'
$documentRoots = @(
    (Join-Path $repositoryRoot 'docs\fable2-prototype-archaeology\phase2e\evidence'),
    (Join-Path $repositoryRoot 'out\prototype-archaeology\phase2e')
)

$files = @()
foreach ($documentRoot in $documentRoots) {
    if (-not (Test-Path -LiteralPath $documentRoot -PathType Container)) {
        throw "Missing Phase 2E JSON root: $documentRoot"
    }
    $files += Get-ChildItem -LiteralPath $documentRoot -Filter '*.json' -File
}

$files = $files | Sort-Object FullName
foreach ($file in $files) {
    $document = [IO.File]::ReadAllText($file.FullName)
    if (-not (Test-Json -Json $document -SchemaFile $schemaPath -ErrorAction Stop)) {
        throw "Phase 2E schema validation failed: $($file.FullName)"
    }
    Write-Output "PASS schema: $($file.Name)"
}

Write-Output "PASS Phase 2E schema documents: $($files.Count)"
