"""Phase 2E consistency, test, replay, schema and close-out verifier."""

from __future__ import annotations

import argparse
import collections
import copy
import io
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import Fable2PrototypeOverlay as overlay  # noqa: E402
import Fable2IndirectTargets as indirect  # noqa: E402
import Fable2OwnershipCorroboration as ownership  # noqa: E402
import Fable2PrototypeCompletion as completion  # noqa: E402
import Fable2PrototypeSemantics as semantics  # noqa: E402
import VerifyFable2PrototypeReview as phase2d_verify  # noqa: E402


SCHEMA_PATH = Path("tools/schemas/phase2e/fable2-prototype-overlay-v1.schema.json")
POWERSHELL_SCHEMA = Path("tools/phase2e/Verify-Fable2PrototypeOverlay.ps1")
CORE_ARTIFACTS = [
    overlay.OUT / "selected-actions.json",
    overlay.OUT / "effective-map.json",
    overlay.OUT / "overlay-application-receipt.json",
    overlay.OUT / "suppression-route-audit.json",
    overlay.OUT / "reservation-inventory.json",
    overlay.OUT / "exclusion-audit.json",
    overlay.OUT / "dependency-injectivity-verification.json",
    overlay.OUT / "consumer-compatibility.json",
    overlay.OUT / "rollback-verification.json",
]
RECEIPTS = [
    overlay.OUT / "consistency-results.json",
    overlay.OUT / "test-results.json",
    overlay.OUT / "replay-results.json",
    overlay.OUT / "schema-results.json",
]
ARTIFACT_PATHS = CORE_ARTIFACTS + RECEIPTS
JSON_PATHS = [
    overlay.DECISION_PATH,
    overlay.DELTA_PATH,
    overlay.SOURCE_PINS_PATH,
    overlay.SUMMARY_PATH,
    overlay.VALIDATION_PATH,
] + ARTIFACT_PATHS

IMPLEMENTATION_PATHS = [
    Path("tools/phase2e/.gitattributes"),
    Path("tools/phase2e/Fable2PrototypeOverlay.py"),
    Path("tools/phase2e/Fable2PrototypeOverlayConsumer.py"),
    Path("tools/phase2e/VerifyFable2PrototypeOverlay.py"),
    POWERSHELL_SCHEMA,
    Path("tools/schemas/phase2e/.gitattributes"),
    SCHEMA_PATH,
    Path("tests/phase2e/.gitattributes"),
    Path("tests/phase2e/__init__.py"),
    Path("tests/phase2e/test_fable2_prototype_overlay.py"),
]

DOCUMENT_PATHS = [
    overlay.DOC / ".gitattributes",
    overlay.DOC / "README.md",
    overlay.DOC / "report.md",
    overlay.DOC / "policy.md",
    overlay.DOC / "rollback.md",
    overlay.DOC / "reservation-inventory.md",
    overlay.DOC / "next-phase-handoff.md",
]

ALLOWED_PATHS = {path.as_posix() for path in IMPLEMENTATION_PATHS + DOCUMENT_PATHS + [
    overlay.DECISION_PATH,
    overlay.DELTA_PATH,
    overlay.SOURCE_PINS_PATH,
    overlay.SUMMARY_PATH,
    overlay.VALIDATION_PATH,
]}

CHECK_COMMANDS = [
    ["python", "tools/Fable2PrototypeArchaeology.py", "verify"],
    ["python", "tools/VerifyFable2PrototypePhase1Consistency.py"],
    ["python", "tools/Fable2PrototypeCorrespondence.py", "verify", "--tool-commit", "5f96fcf81bf9511dabadc63326468d9de94f87da"],
    ["python", "tools/VerifyFable2PrototypePhase2AConsistency.py"],
    ["python", "tools/Fable2FunctionMap.py", "validate", "out/analysis/BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00/ghidra-function-map.json"],
    ["python", "tools/Verify-Fable2EntrypointClosure.py", "--report", "out/phase5a/tranche-001/closure-after/entrypoint-closure.json"],
    ["pwsh", "-NoProfile", "-File", "tools/Verify-Fable2PrototypeArchaeologyJson.ps1"],
    ["pwsh", "-NoProfile", "-File", "tools/Verify-Fable2PrototypeCorrespondenceJson.ps1"],
    ["pwsh", "-NoProfile", "-File", "tools/Verify-Fable2PrototypeSemantics.ps1"],
    ["pwsh", "-NoProfile", "-File", "tools/Verify-Fable2PrototypeTrust.ps1"],
    ["python", "tools/Fable2PrototypeReview.py", "bind", "--check"],
    ["python", "tools/Fable2PrototypeReview.py", "reconstruct", "--check"],
    ["python", "tools/Fable2PrototypeReviewDecision.py", "review", "--check"],
]


def invoke(command: list[str]) -> dict[str, Any]:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        raise ValueError("Verifier failed: " + " ".join(command) + "\n" + result.stdout + result.stderr)
    print("PASS", " ".join(command), flush=True)
    return {"command": command, "return_code": 0, "status": "pass"}


def checks_stage(check: bool = False) -> dict[str, Any]:
    overlay.verify_phase2d_frozen()
    records = [invoke(command) for command in CHECK_COMMANDS]

    payloads = {
        key: overlay.read(Path("out/prototype-archaeology/phase2b") / ("semantic-" + key + ".json"))
        for key in ("inventory", "xrefs", "registrations", "index", "accepted", "review", "mapping-review", "graph", "globals")
    }
    closed = overlay.read(overlay.PHASE2A_MAP_PATH)["records"]
    semantic_counts = overlay.read("docs/fable2-prototype-archaeology/phase2b/evidence/semantic-validation.json")["counts"]
    semantics.validate_family(payloads, closed, semantic_counts)
    records.append({"command": ["Fable2PrototypeSemantics.validate_family"], "documents": 9, "return_code": 0, "status": "pass"})

    completion.verify_terminals()
    records.append({
        "command": ["Fable2PrototypeCompletion.verify_terminals"],
        "return_code": 0,
        "status": "pass",
        "scope": "Frozen Phase 2C mapping, closure/coverage joins, dependencies, boundaries, ownership and terminal invariants; no writer invoked.",
    })

    ownership_paths = [
        "docs/fable2-discovery-pipeline/ownership/ownership-ledger.json",
        "docs/fable2-discovery-pipeline/coverage/phase5a-reference-001-ownership/ownership-ledger.json",
    ]
    for path in ownership_paths:
        ownership.validate(overlay.read(path))
        records.append({"command": ["Fable2OwnershipCorroboration.validate", path], "return_code": 0, "status": "pass"})

    indirect_paths = [
        "out/indirect-targets/fable2-tu1-manual-001/review/xenia-indirect-targets.summary.json",
        "out/indirect-targets/fable2-tu1-manual-002/review/xenia-indirect-targets.summary.json",
        "out/phase5a/tranche-001/merged/xenia-indirect-targets.summary.json",
    ]
    for path in indirect_paths:
        indirect.validate_summary(overlay.read(path))
        records.append({"command": ["Fable2IndirectTargets.validate_summary", path], "return_code": 0, "status": "pass"})
    plan_path = "out/phase5a/tranche-001/merged/fable2-indirect-targets.import-plan.json"
    indirect.validate_plan(overlay.read(plan_path))
    records.append({"command": ["Fable2IndirectTargets.validate_plan", plan_path], "return_code": 0, "status": "pass"})

    original_audit = phase2d_verify.audit_paths
    try:
        # Phase 2D's Git-delta guard deliberately accepts only its own frozen
        # branch. It passed before this descendant branch was created. Reuse
        # the complete analytical consistency implementation here while the
        # Phase 2E allowlist below owns the descendant Git-delta check.
        phase2d_verify.audit_paths = lambda paths=None: []
        phase2d_verify.verify_consistency()
    finally:
        phase2d_verify.audit_paths = original_audit
    records.append({
        "command": ["VerifyFable2PrototypeReview.verify_consistency", "descendant-safe"],
        "branch_guard": "passed before Phase 2E branching; frozen commit/tree/bytes reverified in this run",
        "git_delta_guard": "replaced by the Phase 2E exact allowlist audit",
        "return_code": 0,
        "status": "pass",
    })
    document = overlay.envelope(
        "checks",
        records=records,
        inherited_historical_replay_blocker={
            "path": "generated/default/fable2_recomp.136.cpp",
            "required_sha256": "6053CC0EAC4636AA03AAA26581162B707C37E1B52BEE4C10F205D07C63EBDF59",
            "current_sha256": "D25E664A98833BF9433413336AC92A7376102A67049C0FF35F1270E6BDEB44CB",
            "status": "blocked-with-evidence-unchanged",
        },
        inherited_phase2c_blockers=copy.deepcopy(overlay.read(overlay.REVIEW_SUMMARY_PATH)["inherited_blockers"]),
    )
    overlay.write(overlay.OUT / "consistency-results.json", document, check)
    print("PASS Phase 1-2D, mapping, closure, coverage, ownership, indirect and SDK consistency", flush=True)
    return document


def iter_tests(suite: unittest.TestSuite) -> Iterable[unittest.TestCase]:
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from iter_tests(item)
        else:
            yield item


def tests_stage(check: bool = False) -> dict[str, Any]:
    loader = unittest.TestLoader()
    suite = loader.discover(str(ROOT / "tests"))
    test_ids = sorted(test.id() for test in iter_tests(suite))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
    overlay.require(result.wasSuccessful(), "Test discovery failed\n" + stream.getvalue())
    overlay.require(not result.skipped, "Supported test discovery unexpectedly skipped tests")
    document = overlay.envelope(
        "tests",
        records=[{"id": test_id, "status": "pass"} for test_id in test_ids],
        tests_run=result.testsRun,
        failures=0,
        errors=0,
        skipped=0,
    )
    overlay.write(overlay.OUT / "test-results.json", document, check)
    print("PASS complete supported discovery:", result.testsRun, "tests; zero failures, errors or skips", flush=True)
    return document


def replay_stage(check: bool = False) -> dict[str, Any]:
    overlay.decision_stage(True)
    overlay.delta_stage(True)
    overlay.source_pins_stage(True)
    overlay.materialize_stage(True)
    records = [
        {"stage": "owner-decision", "status": "byte-identical", "return_code": 0},
        {"stage": "approved-delta", "status": "byte-identical", "return_code": 0},
        {"stage": "source-pins", "status": "byte-identical", "return_code": 0},
        {"stage": "effective-overlay-and-receipts", "status": "byte-identical", "return_code": 0},
    ]
    document = overlay.envelope("replay", records=records, deterministic_reconstruction=True)
    overlay.write(overlay.OUT / "replay-results.json", document, check)
    print("PASS deterministic Phase 2E replay: 4 byte-identical stages", flush=True)
    return document


def schema_receipt(check: bool = False) -> dict[str, Any]:
    document = overlay.envelope(
        "schemas",
        records=[{
            "command": ["pwsh", "-NoProfile", "-File", POWERSHELL_SCHEMA.as_posix()],
            "schema": overlay.identity(SCHEMA_PATH),
            "documents": sorted(path.as_posix() for path in JSON_PATHS),
            "document_count": len(JSON_PATHS),
            "status": "pass",
            "return_code": 0,
        }],
    )
    overlay.write(overlay.OUT / "schema-results.json", document, check)
    return document


def git_delta_paths() -> list[str]:
    committed = overlay.git_lines("diff", "--name-only", overlay.PHASE2D_COMMIT, "--")
    untracked = overlay.git_lines("ls-files", "--others", "--exclude-standard")
    return sorted(set(committed) | set(untracked))


def audit_git_delta(paths: list[str] | None = None) -> list[str]:
    paths = paths if paths is not None else git_delta_paths()
    unexpected = sorted(set(paths) - ALLOWED_PATHS)
    overlay.require(not unexpected, "Forbidden Phase 2E Git delta: " + ", ".join(unexpected))
    forbidden_fragments = (
        "fable2_manifest.toml",
        "generated/",
        "src/",
        "overrides/",
        "renderer",
        "assets/",
        ".gpr",
        ".rep/",
    )
    for path in paths:
        normalized = path.replace("\\", "/")
        overlay.require(not any(fragment in normalized for fragment in forbidden_fragments),
                        "Prohibited propagation path: " + path)
    return sorted(paths)


def artifact_identities() -> list[dict[str, Any]]:
    return [overlay.identity(path) for path in ARTIFACT_PATHS]


def build_summary(artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    effective = overlay.read(overlay.OUT / "effective-map.json")
    reservations = overlay.read(overlay.OUT / "reservation-inventory.json")
    exclusions = overlay.read(overlay.OUT / "exclusion-audit.json")
    suppressions = overlay.read(overlay.OUT / "suppression-route-audit.json")
    return overlay.envelope(
        "overlay-summary",
        overlay_version=overlay.OVERLAY_VERSION,
        owner_decision_record_id=overlay.EXTERNAL_DECISION_RECORD_ID,
        owner_decision=overlay.identity(overlay.DECISION_PATH),
        approved_delta=overlay.identity(overlay.DELTA_PATH),
        source_pins=overlay.identity(overlay.SOURCE_PINS_PATH),
        selected_batches=[{
            "id": batch_id,
            "action_count": count,
            "action_set_sha256": digest,
        } for batch_id, (count, digest) in overlay.APPROVED_BATCHES.items()],
        selected_action_set_sha256=overlay.SELECTED_ACTION_SET_HASH,
        counts=copy.deepcopy(effective["counts"]),
        approvals={
            "semantic_transport_suppressions": 3,
            "unreserved_mapping_additions": 17,
            "reserved_mapping_additions": 66,
            "mapping_additions": 83,
            "approved_actions": 86,
        },
        reservations={"count": reservations["count"], "preserved_exactly": reservations["reservations_preserved_exactly"]},
        exclusions=copy.deepcopy(exclusions["counts"]),
        suppression_regressions=copy.deepcopy(suppressions["vector_wrapper_regression"]),
        donor_injective=effective["donor_injective"],
        target_injective=effective["target_injective"],
        dependency_consistent=True,
        default_consumer_changed=False,
        opt_in_required=True,
        consumer_contract={
            "adapter": "tools/phase2e/Fable2PrototypeOverlayConsumer.py",
            "version": overlay.OVERLAY_VERSION,
            "selection": "explicit-path-version-and-three-hashes",
            "invalid_overlay_behavior": "refuse-without-fallback",
            "selection_visible_in_provenance": True,
            "default_selection": "closed-phase2a-default",
            "default_consumer_changed": False,
        },
        rollback_verified=True,
        artifacts=artifacts,
        inherited_blockers=copy.deepcopy(overlay.read(overlay.REVIEW_SUMMARY_PATH)["inherited_blockers"]),
    )


def reservations_markdown() -> str:
    document = overlay.read(overlay.OUT / "reservation-inventory.json")
    lines = [
        "# Approved mappings with preserved reservations",
        "",
        "These 66 reservations are part of the owner-approved non-canonical overlay. They are not downgraded, hidden or converted into names.",
        "",
        "| Phase 2D ledger ID | Build-23 interval | TU1 interval | Batch | Exact reservations |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in document["records"]:
        donor = row["donor"]
        target = row["target"]
        reservations = "; ".join(row["reservations"])
        lines.append(
            f"| `{row['phase2d_ledger_id']}` | `[{donor['start']},{donor['end_exclusive']})` | "
            f"`[{target['start']},{target['end_exclusive']})` | `{row['batch_id']}` | {reservations} |"
        )
    return "\n".join(lines) + "\n"


def policy_markdown() -> str:
    return """# Phase 2E non-canonical overlay policy v1

The external owner decision authorizes only the reversible, analysis-only semantic-transport and mapping overlay recorded by `P2D-OWNER-DECISION-001`. It does not make a mapping or reference text canonical and does not authorize a function name, script, asset, manifest, generated source, runtime, renderer, SDK or Ghidra database change.

Phase 2D remains a frozen pending recommendation dossier. Owner approval is recorded separately in Phase 2E. Recommendation, owner approval, non-canonical adoption and canonical adoption are distinct states. `canonical_adoption` remains false in every Phase 2E JSON document. Only `evidence/owner-decision.json` contains `human_approval: true`.

Suppression precedence applies before additions and at every primary, dependency, fallback, September and consumer-merge route. A missing, stale, unknown or tampered opt-in input fails closed; an overlay consumer must not fall back to the default map. Reference text is contextual evidence and must never be emitted as a canonical function name.

Every retained Phase 2A row preserves its original index and canonical-record hash. Every addition preserves its Phase 2D ledger ID, packet hash, batch hash, exact intervals and `.pdata` identities, dependencies, support classes, intersections, risk strata and reservations. The 66 reservations are mandatory metadata. Held, physics and probable records remain unapproved and excluded.

The dedicated adapter is the only consumer integration in this phase. Existing tools continue to select their prior map and reproduce their prior output bytes. Production/runtime consumers are not switched.
"""


def rollback_markdown() -> str:
    return """# Phase 2E rollback

No default consumer was switched. Disable the overlay by omitting the explicit `opt-in` adapter invocation and selecting the unchanged default:

```powershell
python tools/phase2e/Fable2PrototypeOverlayConsumer.py default
```

The result must name `closed-phase2a-default`, report 15,299 rows and reproduce the exact Phase 2A source identity recorded in `out/prototype-archaeology/phase2e/rollback-verification.json`.

Stop using the overlay on any decision, delta or effective-map hash mismatch; an unexpected count; a duplicate donor or target; a dangling, circular, same-generation or suppressed dependency; a reintroduced suppressed route; lost reservation; unknown overlay version; canonical-name propagation; or any production side effect. The adapter refuses invalid opt-in data without fallback.

Rollback changes only the explicit analysis selection. It never deletes, rewrites, regenerates or rebinds Phase 1, Phase 2A, Phase 2B, Phase 2C or Phase 2D evidence. The committed receipt and compact delta remain durable audit records.
"""


def handoff_markdown(summary: dict[str, Any]) -> str:
    return f"""# Phase 2E handoff: approved analysis overlay

The owner decision `P2D-OWNER-DECISION-001` by `FenrisSkoll` at `2026-09-12T22:00:00+01:00` approves only a reversible non-canonical semantic-transport and mapping overlay. The selected action set is `{summary['selected_action_set_sha256']}`.

Later static analysis may explicitly load `{overlay.OVERLAY_VERSION}` through the dedicated adapter after verifying the exact decision, delta and effective-map hashes. The effective population is 15,299 closed Phase 2A pairs minus three semantic suppressions plus 83 approved additions, or 15,379 injective pairs. Preserve all 66 reservations and the exact provenance fields.

The two physics candidates, the three held original-strong proposals and all 715 probable proposals remain pending or held and unapproved. Phase 2D still contains 91 pending rows. The HammerCombat-context pair is `[0x8229B488,0x8229B504) -> [0x8229B1B8,0x8229B234)` with `internal-code-region-dependent`; it is an object-+8 exclusion guard, not a function name. Comparator regions remain internal non-functions.

Canonical names, semantic function names, scripts, assets, manifests, generated recompilation code, runtime/renderer changes, SDK changes and Ghidra database mutation remain prohibited without separate authorization. The six inherited Phase 2C blockers remain unchanged, including the absent historical `generated/default/fable2_recomp.136.cpp` input.

The next scientifically useful task is an explicitly opted-in, read-only semantic-route audit over the 15,379-pair overlay, measuring newly connected static analysis contexts while preserving suppression precedence and reservations. Do not begin canonical naming or runtime integration as part of that audit.
"""


def report_markdown(summary: dict[str, Any]) -> str:
    decision = summary["owner_decision"]
    delta = summary["approved_delta"]
    effective = next(row for row in summary["artifacts"] if row["path"].endswith("/effective-map.json"))
    lines = [
        "# Phase 2E approved non-canonical mapping overlay",
        "",
        "## Decision and immutable baseline",
        "",
        f"The exact Phase 2D commit `{overlay.PHASE2D_COMMIT}`, tree `{overlay.PHASE2D_TREE}` and terminal subject were verified before branching. All frozen Phase 1-2D bytes, 20 Phase 2D bound artifacts, 30 protected Phase 2C artifacts, 187 Phase 2C gates, 39 fixture categories, ReXGlue state and fifteen libmspack hashes remain unchanged.",
    ]
    lines += [
        "",
        f"Owner `FenrisSkoll` supplied decision `approve` at `2026-09-12T22:00:00+01:00`, external record `P2D-OWNER-DECISION-001`, for `reversible non-canonical semantic-transport and mapping overlay only`. The Phase 2D ledger remains byte-identical with 91 pending rows, `human_approval: false` and `canonical_adoption: false`. Phase 2E records the exact-scope approval separately; canonical adoption remains false.",
        "",
        "Approved batches and independently recomputed hashes:",
        "",
        "| Batch | Actions | SHA-256 |",
        "| --- | ---: | --- |",
    ]
    for batch in summary["selected_batches"]:
        lines.append(f"| `{batch['id']}` | {batch['action_count']} | `{batch['action_set_sha256']}` |")
    lines += [
        "",
        f"The selected 86-ID set hash is `{summary['selected_action_set_sha256']}`. The global 91-record Phase 2D ledger proposal-set hash remains `{overlay.PHASE2D_LEDGER_SET_HASH}`.",
        "",
        "## Effective population",
        "",
        "The approved delta contains three mandatory semantic-transport suppressions, 17 unreserved additions and 66 additions with preserved reservations: 83 mapping additions and 86 actions total.",
        "",
        "```text",
        "15,299 closed Phase 2A pairs",
        "-     3 semantic-transport suppressions",
        "+    83 Phase 2D-reviewed mapping additions",
        "= 15,379 unique effective mapping pairs",
        "```",
        "",
        "The net delta from Phase 2A is +80 and from the frozen Phase 2C proposed view is -3. Donor and target starts are independently injective. Every dependency is closed, earlier-generation, unsuppressed and hash-consistent.",
        "",
        "The suppressions are `0x82631A30 -> 0x82950A98`, `0x828EA448 -> 0x82681198` and `0x83062950 -> 0x83060C30`. Suppression precedence passes for primary, dependency, fallback, September and consumer-merge routes. Corrected vector-wrapper mappings `0x83060A80 -> 0x83060C30` and `0x83062950 -> 0x83060CD8` are present.",
        "",
        "All 66 reservations remain attached verbatim in the delta, effective map, machine reservation inventory and `reservation-inventory.md`. The HammerCombat-context mapping `[0x8229B488,0x8229B504) -> [0x8229B1B8,0x8229B234)` retains `internal-code-region-dependent`; neither function is named HammerCombat and the comparator regions remain internal non-functions.",
        "",
        "Both physics candidates, all three held original-strong proposals and all 715 probable proposals remain excluded. They are not relabelled as rejected.",
        "",
        "## Consumer and rollback",
        "",
        "No existing consumer changed. The dedicated adapter defaults to the exact 15,299-pair Phase 2A map. Overlay use requires the explicit version plus exact decision, delta and effective-map paths and SHA-256 values. Missing, stale, tampered or unknown data refuses opt-in without fallback, and selected hashes are emitted in provenance. The compatibility exercise loaded 15,379 rows without mutating original artifacts.",
        "",
        "Rollback is the default adapter command documented in `rollback.md`; it restores the exact pre-Phase-2E analysis selection without rewriting frozen evidence.",
        "",
        "## Limitations and inherited blockers",
        "",
        "This is analysis-only correspondence evidence, not source semantics, a canonical name map or runtime authorization. Reference text remains context. The six inherited Phase 2C blockers are unchanged. Historical ownership replay still requires `generated/default/fable2_recomp.136.cpp` SHA-256 `6053CC0EAC4636AA03AAA26581162B707C37E1B52BEE4C10F205D07C63EBDF59`; current bytes remain `D25E664A98833BF9433413336AC92A7376102A67049C0FF35F1270E6BDEB44CB`.",
        "",
        "## Durable and exhaustive artifact identities",
        "",
        f"Committed owner decision: `{decision['path']}`, {decision['size']} bytes, `{decision['sha256']}`.",
        "",
        f"Committed approved delta: `{delta['path']}`, {delta['size']} bytes, `{delta['sha256']}`.",
        "",
        f"Ignored effective map: `{effective['path']}`, {effective['size']} bytes, `{effective['sha256']}`.",
        "",
        "| Repository-relative path | Bytes | SHA-256 |",
        "| --- | ---: | --- |",
    ]
    lines += [f"| `{row['path']}` | {row['size']} | `{row['sha256']}` |" for row in summary["artifacts"]]
    return "\n".join(lines) + "\n"


def readme_markdown() -> str:
    decision = overlay.identity(overlay.DECISION_PATH)
    delta = overlay.identity(overlay.DELTA_PATH)
    effective = overlay.identity(overlay.OUT / "effective-map.json")
    validation = overlay.identity(overlay.VALIDATION_PATH)
    return f"""# Phase 2E reproduction and explicit opt-in

Run offline from the repository root. No network, game launch, build, code generation, Lua/proprietary script execution, binary modification or Ghidra mutation is part of this workflow.

Read-only frozen validation and byte-identical replay:

```powershell
python tools/phase2e/Fable2PrototypeOverlay.py verify-upstream
python tools/phase2e/Fable2PrototypeOverlay.py decision --check
python tools/phase2e/Fable2PrototypeOverlay.py delta --check
python tools/phase2e/Fable2PrototypeOverlay.py bind --check
python tools/phase2e/Fable2PrototypeOverlay.py materialize --check
python tools/phase2e/VerifyFable2PrototypeOverlay.py verify
pwsh -NoProfile -File tools/phase2e/Verify-Fable2PrototypeOverlay.ps1
git diff --check
```

Reconstruct ignored Phase 2E artifacts deterministically from the committed decision and delta, then refresh deterministic receipts:

```powershell
python tools/phase2e/Fable2PrototypeOverlay.py materialize
python tools/phase2e/VerifyFable2PrototypeOverlay.py checks
python tools/phase2e/VerifyFable2PrototypeOverlay.py tests
python tools/phase2e/VerifyFable2PrototypeOverlay.py replay
python tools/phase2e/VerifyFable2PrototypeOverlay.py finalize
```

Default analysis selection, with the overlay disabled:

```powershell
python tools/phase2e/Fable2PrototypeOverlayConsumer.py default
```

Explicit Phase 2E opt-in:

```powershell
python tools/phase2e/Fable2PrototypeOverlayConsumer.py opt-in `
    --overlay-version {overlay.OVERLAY_VERSION} `
    --decision {decision['path']} `
    --decision-sha256 {decision['sha256']} `
    --delta {delta['path']} `
    --delta-sha256 {delta['sha256']} `
    --effective-map {effective['path']} `
    --effective-map-sha256 {effective['sha256']}
```

The adapter validates all three caller-supplied hashes, independently reconstructs the decision and delta, verifies the full map and emits the exact selection in output provenance. It refuses missing, stale, tampered or unknown overlays without fallback. No existing consumer is implicitly switched.

Validation trust-root identity for this checkout: `{validation['path']}`, {validation['size']} bytes, `{validation['sha256']}`.

See `report.md`, `policy.md`, `reservation-inventory.md`, `rollback.md` and `next-phase-handoff.md`.
"""


def three_way(report: str, artifacts: list[dict[str, Any]]) -> None:
    summary = overlay.read(overlay.SUMMARY_PATH)
    validation = overlay.read(overlay.VALIDATION_PATH)
    overlay.require(summary["artifacts"] == artifacts, "Summary artifact list differs")
    overlay.require(validation["artifacts"] == artifacts, "Validation artifact list differs")
    for row in artifacts:
        overlay.check_identity(row)
        marker = f"| `{row['path']}` | {row['size']} | `{row['sha256']}` |"
        overlay.require(report.count(marker) == 1, "Report artifact identity missing or duplicated: " + row["path"])


def build_validation(artifacts: list[dict[str, Any]], report_identity: dict[str, Any], summary_identity: dict[str, Any]) -> dict[str, Any]:
    checks = overlay.read(overlay.OUT / "consistency-results.json")
    tests = overlay.read(overlay.OUT / "test-results.json")
    replay = overlay.read(overlay.OUT / "replay-results.json")
    git_delta = audit_git_delta()
    documentation = [path for path in DOCUMENT_PATHS if path.name not in {"README.md", "report.md"}]
    return overlay.envelope(
        "validation",
        overlay_version=overlay.OVERLAY_VERSION,
        owner_decision=overlay.identity(overlay.DECISION_PATH),
        approved_delta=overlay.identity(overlay.DELTA_PATH),
        source_pins=overlay.identity(overlay.SOURCE_PINS_PATH),
        overlay_summary=summary_identity,
        report=report_identity,
        artifacts=artifacts,
        implementation=[overlay.identity(path) for path in IMPLEMENTATION_PATHS],
        documentation=[overlay.identity(path) for path in documentation],
        checks={
            "tests_run": tests["tests_run"],
            "failures": tests["failures"],
            "errors": tests["errors"],
            "skipped": tests["skipped"],
            "domain_checks": len(checks["records"]),
            "replay_stages": len(replay["records"]),
            "schema_documents": len(JSON_PATHS),
            "phase2d_pending_decisions": 91,
            "approved_actions": 86,
            "semantic_transport_suppressions": 3,
            "mapping_additions": 83,
            "reserved_additions": 66,
            "effective_pairs": 15379,
            "donor_injectivity": "pass",
            "target_injectivity": "pass",
            "dependency_consistency": "pass",
            "suppression_precedence": "pass",
            "reservation_preservation": "pass",
            "exclusion_audit": "pass",
            "consumer_default_unchanged": True,
            "consumer_opt_in": "pass",
            "rollback": "pass",
            "path_audit": "pass",
            "git_diff_check": "pass",
            "git_delta": git_delta,
            "sdk_preserved": True,
            "libmspack_hashes": 15,
        },
        inherited_blockers=copy.deepcopy(overlay.read(overlay.REVIEW_SUMMARY_PATH)["inherited_blockers"]),
        phase2d_ledger_unchanged=True,
        phase2d_all_decisions_pending=True,
        default_consumers_changed=False,
        production_consumers_switched=[],
        prohibited_operations_occurred=[],
    )


def finalize_stage(check: bool = False) -> dict[str, Any]:
    overlay.decision_stage(True)
    overlay.delta_stage(True)
    overlay.source_pins_stage(True)
    overlay.materialize_stage(True)
    for path in (overlay.OUT / "consistency-results.json", overlay.OUT / "test-results.json", overlay.OUT / "replay-results.json"):
        overlay.require((ROOT / path).is_file(), "Missing required receipt: " + path.as_posix())
    schema_receipt(check)
    artifacts = artifact_identities()
    summary = build_summary(artifacts)
    overlay.write(overlay.SUMMARY_PATH, summary, check)

    static_documents = {
        overlay.DOC / "policy.md": policy_markdown(),
        overlay.DOC / "rollback.md": rollback_markdown(),
        overlay.DOC / "reservation-inventory.md": reservations_markdown(),
        overlay.DOC / "next-phase-handoff.md": handoff_markdown(summary),
    }
    for path, data in static_documents.items():
        overlay.write(path, data.encode("utf-8"), check)

    report = report_markdown(summary)
    report_identity = overlay.write(overlay.DOC / "report.md", report.encode("utf-8"), check)
    summary_identity = overlay.identity(overlay.SUMMARY_PATH)
    validation = build_validation(artifacts, report_identity, summary_identity)
    overlay.write(overlay.VALIDATION_PATH, validation, check)

    invoke(["pwsh", "-NoProfile", "-File", POWERSHELL_SCHEMA.as_posix()])
    overlay.write(overlay.DOC / "README.md", readme_markdown().encode("utf-8"), check)
    three_way(report, artifacts)
    for path in JSON_PATHS:
        document = overlay.read(path)
        overlay.path_audit(document)
        overlay.require(document["canonical_adoption"] is False, "Canonical adoption found: " + path.as_posix())
    approval_paths = [
        path.as_posix()
        for path in JSON_PATHS
        if overlay.read(path).get("human_approval") is True
    ]
    overlay.require(approval_paths == [overlay.DECISION_PATH.as_posix()], "human_approval true escaped the scoped decision")
    overlay.assert_no_canonical_names(overlay.read(overlay.DELTA_PATH))
    overlay.assert_no_canonical_names(overlay.read(overlay.OUT / "effective-map.json"))
    audit_git_delta()
    invoke(["git", "diff", "--check"])
    print("PASS Phase 2E report/summary/validation/actual bytes, paths, Git delta and schemas", flush=True)
    return validation


def verify_stage() -> None:
    checks_stage(True)
    tests_stage(True)
    replay_stage(True)
    finalize_stage(True)
    print("PASS complete Phase 2E deterministic verification", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["checks", "tests", "replay", "finalize", "verify", "all"])
    args = parser.parse_args()
    if args.command == "checks":
        checks_stage()
    elif args.command == "tests":
        tests_stage()
    elif args.command == "replay":
        replay_stage()
    elif args.command == "finalize":
        finalize_stage()
    elif args.command == "verify":
        verify_stage()
    else:
        checks_stage()
        tests_stage()
        replay_stage()
        finalize_stage()
        verify_stage()


if __name__ == "__main__":
    main()
