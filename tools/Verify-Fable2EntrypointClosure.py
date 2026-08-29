#!/usr/bin/env python3
"""Validate a Fable II entrypoint-closure report against its TU1 contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROVENANCE = REPO_ROOT / "tools" / "fable2-entrypoint-closure-evidence.json"


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"could not read JSON file '{path}': {error}") from error

    if not isinstance(value, dict):
        raise ValueError(f"JSON root in '{path}' is not an object")
    return value


def address_value(value: str) -> int:
    return int(value, 0)


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the authoritative Fable II TU1 entrypoint-closure JSON "
            "without changing the manifest or report."
        )
    )
    parser.add_argument(
        "--provenance",
        type=Path,
        default=DEFAULT_PROVENANCE,
        help="versioned Fable II evidence contract",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help=(
            "authoritative entrypoint-closure JSON; defaults to "
            "out/analysis/<expected-patched-sha256>/entrypoint-closure.json"
        ),
    )
    args = parser.parse_args()

    try:
        provenance = load_json(args.provenance.resolve())
        expected_identity = provenance["expected_image_identity"]
        expected_fixtures = provenance["acceptance_fixtures"]
        patched_sha256 = expected_identity["patched_image_sha256"]
        report_path = args.report or (
            REPO_ROOT
            / "out"
            / "analysis"
            / patched_sha256
            / "entrypoint-closure.json"
        )
        report = load_json(report_path.resolve())
    except (KeyError, TypeError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1

    errors: list[str] = []
    schema_version = report.get("schema_version")
    analyzer_version = report.get("analyzer_version")
    require(schema_version in {1, 2}, f"unsupported schema_version {schema_version}", errors)
    expected_analyzer = {1: "1.0.0", 2: "1.1.0"}.get(schema_version)
    require(
        analyzer_version == expected_analyzer,
        f"schema {schema_version} requires analyzer {expected_analyzer}, got {analyzer_version}",
        errors,
    )

    actual_identity = report.get("image_identity", {})
    identity_keys = [key for key in expected_identity if key != "executable_sections"]
    for key in identity_keys:
        if schema_version == 1 and key.startswith("executable_memory_"):
            continue
        expected = expected_identity[key]
        report_key = (
            "executable_memory_fingerprint"
            if key == "executable_memory_sha256"
            else key
        )
        actual = actual_identity.get(report_key)
        require(actual == expected, f"identity {key}: expected {expected}, got {actual}", errors)
    if schema_version == 2:
        expected_sections = expected_identity.get("executable_sections", [])
        actual_sections = [
            {
                "name": section["name"],
                "start": section["range"]["start"],
                "end": section["range"]["end"],
                "size": section["range"]["size"],
                "permissions": "".join(
                    (
                        "r" if section.get("readable") else "-",
                        "w" if section.get("writable") else "-",
                        "x" if section.get("executable") else "-",
                    )
                ),
                "sha256": section["sha256"],
            }
            for section in report.get("sections", [])
            if section.get("executable")
        ]
        require(
            actual_sections == expected_sections,
            "identity executable_sections differ from the versioned evidence contract",
            errors,
        )

    safety = report.get("safety", {})
    require(safety.get("mode") == "report_only", "report mode is not report_only", errors)
    require(
        safety.get("manifest_mutation_attempted") is False,
        "report records a manifest mutation attempt",
        errors,
    )
    require(
        safety.get("review_toml_is_non_authoritative") is True,
        "review TOML is not marked non-authoritative",
        errors,
    )

    fixpoint = report.get("fixpoint", {})
    require(fixpoint.get("reached") is True, "analysis did not reach a fixpoint", errors)
    limit_diagnostics = report.get("limit_diagnostics", [])
    exhausted_limits = [
        diagnostic
        for diagnostic in limit_diagnostics
        if str(diagnostic.get("limit", "")).startswith("max_")
    ]
    require(not exhausted_limits, f"analysis exhausted limits: {exhausted_limits}", errors)

    candidates = report.get("candidates", [])
    candidate_addresses = [address_value(candidate["address"]) for candidate in candidates]
    require(
        candidate_addresses == sorted(candidate_addresses),
        "candidates are not sorted by guest address",
        errors,
    )
    for candidate in candidates:
        evidence_keys = [
            (
                address_value(evidence["target_address"]),
                evidence["kind"],
                address_value(evidence["storage_address"])
                if evidence.get("storage_address")
                else 0,
                address_value(evidence["source_address"])
                if evidence.get("source_address")
                else 0,
                evidence.get("source_section") or "",
                evidence.get("provenance") or "",
                tuple(sorted(evidence.get("attributes", {}).items())),
            )
            for evidence in candidate.get("evidence", [])
        ]
        require(
            evidence_keys == sorted(evidence_keys),
            f"evidence is not deterministically sorted for {candidate['address']}",
            errors,
        )

    review_classes = {
        "strong_new_function",
        "probable_new_function",
        "ambiguous_code_pointer",
    }
    review_ranges = [
        (
            address_value(candidate["proposed_range"]["start"]),
            address_value(candidate["proposed_range"]["end"]),
        )
        for candidate in candidates
        if candidate.get("classification") in review_classes
        and candidate.get("proposed_range") is not None
    ]
    overlap_pairs = 0
    active_ranges: list[tuple[int, int]] = []
    for start, end in review_ranges:
        active_ranges = [active for active in active_ranges if active[1] > start]
        overlap_pairs += sum(1 for active in active_ranges if active[0] < end)
        active_ranges.append((start, end))

    actual_fixtures = {
        fixture["expected"]["address"]: fixture
        for fixture in report.get("fixture_results", [])
    }
    for expected in expected_fixtures:
        address = expected["address"]
        expected_size = address_value(expected["size"])
        fixture = actual_fixtures.get(address)
        require(fixture is not None, f"fixture {address} is missing", errors)
        if fixture is None:
            continue
        actual_size = address_value(fixture["expected"]["size"])
        require(actual_size == expected_size, f"fixture {address} size mismatch", errors)
        require(
            fixture["expected"]["verified_classification"]
            == expected["verified_classification"],
            f"fixture {address} verified classification mismatch",
            errors,
        )
        require(fixture.get("result") == "pass", f"fixture {address} did not pass", errors)
        require(fixture.get("present") is True, f"fixture {address} is absent", errors)
        require(fixture.get("range_matches") is True, f"fixture {address} range differs", errors)
        require(
            fixture.get("independently_rediscovered") is True,
            f"fixture {address} was not independently rediscovered",
            errors,
        )
        require(
            bool(fixture.get("independent_evidence")),
            f"fixture {address} has no independent static evidence",
            errors,
        )

    counts = report.get("counts", {})
    require(
        counts.get("candidates") == len(candidates),
        "candidate count does not match candidate array length",
        errors,
    )
    require(
        counts.get("candidate_overlap_pairs") == overlap_pairs,
        "candidate overlap count does not match proposed ranges",
        errors,
    )

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print(
        f"PASS: schema={schema_version} analyzer={analyzer_version} "
        f"image={patched_sha256} candidates={counts.get('candidates')} "
        f"strong={counts.get('strong_new_functions')} "
        f"probable={counts.get('probable_new_functions')} fixtures={len(expected_fixtures)}"
    )
    for expected in expected_fixtures:
        fixture = actual_fixtures[expected["address"]]
        storage = ",".join(fixture.get("storage_addresses", [])) or "none"
        materialization = ",".join(fixture.get("materialization_sites", [])) or "none"
        evidence = ",".join(fixture.get("independent_evidence", []))
        print(
            f"  {expected['address']} size={expected['size']} evidence={evidence} "
            f"storage={storage} materialization={materialization}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
