$ErrorActionPreference = "Stop"

$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$tool = Join-Path $repositoryRoot "tools\phase2i\Fable2AnalystExport.py"

$phase2eDecision = "docs/fable2-prototype-archaeology/phase2e/evidence/owner-decision.json"
$phase2eDelta = "docs/fable2-prototype-archaeology/phase2e/evidence/approved-overlay-delta.json"
$phase2eEffectiveMap = "out/prototype-archaeology/phase2e/effective-map.json"
$phase2hSourcePins = "docs/fable2-prototype-archaeology/phase2h/evidence/source-pins.json"
$phase2hDecision = "docs/fable2-prototype-archaeology/phase2h/evidence/owner-decision.json"
$phase2hDelta = "docs/fable2-prototype-archaeology/phase2h/evidence/semantic-correction-delta.json"
$phase2hView = "out/prototype-archaeology/phase2h/materialized-reviewed-semantic-view.json"

function Get-RepositoryHash {
    param([Parameter(Mandatory)][string] $Path)

    $fullPath = Join-Path $repositoryRoot $Path
    return (Get-FileHash -LiteralPath $fullPath -Algorithm SHA256).Hash
}

$phase2eArguments = @(
    "--mapping-view", "phase2e-v1",
    "--phase2e-decision", $phase2eDecision,
    "--phase2e-decision-sha256", (Get-RepositoryHash $phase2eDecision),
    "--phase2e-delta", $phase2eDelta,
    "--phase2e-delta-sha256", (Get-RepositoryHash $phase2eDelta),
    "--phase2e-effective-map", $phase2eEffectiveMap,
    "--phase2e-effective-map-sha256", (Get-RepositoryHash $phase2eEffectiveMap)
)

$phase2hArguments = @(
    "--semantic-view", "phase2h-v1",
    "--phase2h-source-pins", $phase2hSourcePins,
    "--phase2h-source-pins-sha256", (Get-RepositoryHash $phase2hSourcePins),
    "--phase2h-decision", $phase2hDecision,
    "--phase2h-decision-sha256", (Get-RepositoryHash $phase2hDecision),
    "--phase2h-delta", $phase2hDelta,
    "--phase2h-delta-sha256", (Get-RepositoryHash $phase2hDelta),
    "--phase2h-view", $phase2hView,
    "--phase2h-view-sha256", (Get-RepositoryHash $phase2hView)
)

function Invoke-Phase2IExport {
    param(
        [Parameter(Mandatory)][string] $Profile,
        [Parameter(Mandatory)][string] $Output,
        [string] $SemanticView = "none",
        [string[]] $AdditionalArguments = @()
    )

    $arguments = @(
        "-B", $tool,
        "--profile", $Profile,
        "--output", $Output
    )
    $arguments += $phase2eArguments
    if ($SemanticView -eq "phase2f-evidence") {
        $arguments += @("--semantic-view", "phase2f-evidence")
    }
    elseif ($SemanticView -eq "phase2h-v1") {
        $arguments += $phase2hArguments
    }
    $arguments += $AdditionalArguments

    & python @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Phase 2I export failed for profile $Profile with exit code $LASTEXITCODE."
    }
}

Push-Location $repositoryRoot
try {
    Invoke-Phase2IExport `
        -Profile "address" `
        -Output "out/prototype-archaeology/phase2i/profiles/address" `
        -SemanticView "phase2h-v1" `
        -AdditionalArguments @("--address", "0x82522C10")

    Invoke-Phase2IExport `
        -Profile "phase2h-approved" `
        -Output "out/prototype-archaeology/phase2i/profiles/phase2h-approved" `
        -SemanticView "phase2h-v1"

    Invoke-Phase2IExport `
        -Profile "overlay-review" `
        -Output "out/prototype-archaeology/phase2i/profiles/overlay-review"

    Invoke-Phase2IExport `
        -Profile "project-relevant" `
        -Output "out/prototype-archaeology/phase2i/profiles/project-relevant"

    Invoke-Phase2IExport `
        -Profile "semantic-review" `
        -Output "out/prototype-archaeology/phase2i/profiles/semantic-review" `
        -SemanticView "phase2f-evidence"

    Invoke-Phase2IExport `
        -Profile "all-correspondences" `
        -Output "out/prototype-archaeology/phase2i/profiles/all-correspondences" `
        -AdditionalArguments @("--bulk")
}
finally {
    Pop-Location
}
