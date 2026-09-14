$ErrorActionPreference = "Stop"

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$schemaPath = Join-Path $repositoryRoot "tools\schemas\phase2h\fable2-reviewed-semantic-layer-v1.schema.json"
$documentRoots = @(
    (Join-Path $repositoryRoot "docs\fable2-prototype-archaeology\phase2h\evidence"),
    (Join-Path $repositoryRoot "out\prototype-archaeology\phase2h")
)

$documents = @()

foreach ($documentRoot in $documentRoots) {
    if (Test-Path -LiteralPath $documentRoot) {
        $documents += Get-ChildItem -LiteralPath $documentRoot -Filter "*.json" -File -Recurse
    }
}

if ($documents.Count -eq 0) {
    throw "No Phase 2H JSON documents were found."
}

foreach ($document in ($documents | Sort-Object FullName)) {
    $json = Get-Content -LiteralPath $document.FullName -Raw

    if (-not ($json | Test-Json -SchemaFile $schemaPath)) {
        throw "Schema validation failed: $($document.FullName)"
    }
}

Write-Host "PASS Phase 2H schemas: $($documents.Count) documents"
