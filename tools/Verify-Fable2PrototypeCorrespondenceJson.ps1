param(
    [string] $EvidenceDirectory = "docs/fable2-prototype-archaeology/phase2a/evidence",
    [string] $SchemaPath = "tools/schemas/fable2-prototype-correspondence-v1.schema.json"
)

$ErrorActionPreference = "Stop"

$required = @(
    "prototype-correspondence-index.json",
    "prototype-correspondence-accepted.json",
    "prototype-correspondence-review.json",
    "prototype-correspondence-validation.json",
    "prototype-correspondence-summary.json"
)

foreach ($filename in $required) {
    $path = Join-Path $EvidenceDirectory $filename
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required Phase 2A artifact is missing: $path"
    }
    $valid = Test-Json -Path $path -SchemaFile $SchemaPath
    if (-not $valid) {
        throw "Phase 2A schema validation failed: $path"
    }
}

Write-Host "Validated $($required.Count) Phase 2A correspondence artifacts against $SchemaPath."
