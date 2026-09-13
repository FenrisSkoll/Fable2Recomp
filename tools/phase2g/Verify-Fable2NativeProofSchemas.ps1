$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$schemaPath = Join-Path $repositoryRoot 'tools\schemas\phase2g\fable2-native-semantic-proof-v1.schema.json'
$documentRoots = @(
    (Join-Path $repositoryRoot 'docs\fable2-prototype-archaeology\phase2g\evidence'),
    (Join-Path $repositoryRoot 'out\prototype-archaeology\phase2g')
)
$files = @()
foreach ($documentRoot in $documentRoots) {
    if (Test-Path -LiteralPath $documentRoot) {
        $files += Get-ChildItem -LiteralPath $documentRoot -File -Filter '*.json' -Recurse
    }
}
foreach ($file in ($files | Sort-Object FullName)) {
    $document = [IO.File]::ReadAllText($file.FullName)
    if (-not (Test-Json -Json $document -SchemaFile $schemaPath -ErrorAction Stop)) {
        throw "Phase 2G schema validation failed: $($file.FullName)"
    }
    Write-Output "PASS schema: $($file.Name)"
}
Write-Output "PASS Phase 2G schema documents: $($files.Count)"
