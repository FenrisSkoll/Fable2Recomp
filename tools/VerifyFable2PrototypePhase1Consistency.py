#!/usr/bin/env python3
"""Cross-check Phase 1 prototype section identities against bytes and prose.

This verifier is intentionally read-only. It treats prototype-xex-metadata.json
as the authoritative section-identity record, rehashes the ignored Ghidra
exports, checks the TU1 relationship artifact, and verifies the small identity
table in the human report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


TOOL_NAME = "VerifyFable2PrototypePhase1Consistency.py"
TOOL_VERSION = "1.0.0"
FULL_BUILD_IDS = ("sep-2008", "jul-2009", "build-23.12.02.0330")
REPORT_ROW_RE = re.compile(
    r"^\| (?P<label>September|July / build 23) \| `(?P<start>0x[0-9A-Fa-f]+)` "
    r"\| (?P<size>[0-9,]+) \| `(?P<sha256>[0-9A-Fa-f]{64})` \|$"
)


class ConsistencyError(ValueError):
    """Raised when Phase 1 evidence no longer describes one byte domain."""


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ConsistencyError(f"required file is missing: {path}") from error
    except json.JSONDecodeError as error:
        raise ConsistencyError(f"invalid JSON in {path}: {error}") from error
    if not isinstance(value, dict):
        raise ConsistencyError(f"expected a JSON object in {path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
                digest.update(chunk)
    except FileNotFoundError as error:
        raise ConsistencyError(f"derived section is missing: {path}") from error
    return digest.hexdigest().upper()


def memory_blocks(value: dict[str, Any], source: Path) -> list[dict[str, Any]]:
    blocks = value.get("memory_blocks")
    if not isinstance(blocks, list) or not blocks:
        raise ConsistencyError(f"no memory_blocks in {source}")
    if not all(isinstance(block, dict) for block in blocks):
        raise ConsistencyError(f"invalid memory_blocks in {source}")
    return blocks


def block_by_name(blocks: list[dict[str, Any]], name: str, source: Path) -> dict[str, Any]:
    matches = [block for block in blocks if block.get("name") == name]
    if len(matches) != 1:
        raise ConsistencyError(
            f"expected one {name} block in {source}; found {len(matches)}"
        )
    return matches[0]


def load_derived_manifests(derived_root: Path) -> dict[str, dict[str, Any]]:
    manifests: dict[str, dict[str, Any]] = {}
    for build_id in FULL_BUILD_IDS:
        manifest_path = derived_root / build_id / "derived-image.json"
        manifests[build_id] = read_json(manifest_path)
    return manifests


def authoritative_xex_records(evidence_root: Path) -> dict[str, dict[str, Any]]:
    path = evidence_root / "prototype-xex-metadata.json"
    value = read_json(path)
    records = value.get("records")
    if not isinstance(records, list):
        raise ConsistencyError(f"invalid records array in {path}")
    by_id = {
        record.get("artifact_id"): record
        for record in records
        if isinstance(record, dict) and record.get("artifact_id") in FULL_BUILD_IDS
    }
    missing = sorted(set(FULL_BUILD_IDS) - set(by_id))
    if missing:
        raise ConsistencyError(f"missing full-XEX metadata records: {', '.join(missing)}")
    return by_id


def report_rows(report_path: Path) -> dict[str, dict[str, Any]]:
    try:
        lines = report_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as error:
        raise ConsistencyError(f"Phase 1 report is missing: {report_path}") from error
    rows: dict[str, dict[str, Any]] = {}
    for line in lines:
        match = REPORT_ROW_RE.match(line)
        if not match:
            continue
        label = match.group("label")
        rows[label] = {
            "start": match.group("start").upper().replace("0X", "0x"),
            "size": int(match.group("size").replace(",", "")),
            "sha256": match.group("sha256").upper(),
        }
    expected = {"September", "July / build 23"}
    if set(rows) != expected:
        raise ConsistencyError(
            f"expected report .text rows {sorted(expected)}; found {sorted(rows)}"
        )
    return rows


def relationship_text_rows(evidence_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    path = evidence_root / "prototype-tu1-relationship.json"
    value = read_json(path)

    def unique_text(key: str) -> dict[str, Any]:
        rows = value.get(key)
        if not isinstance(rows, list):
            raise ConsistencyError(f"invalid {key} array in {path}")
        matches = [row for row in rows if isinstance(row, dict) and row.get("section") == ".text"]
        if len(matches) != 1:
            raise ConsistencyError(f"expected one .text record in {key}; found {len(matches)}")
        return matches[0]

    return unique_text("july_vs_build_23_sections"), unique_text(
        "build_23_vs_canonical_tu1_sections"
    )


def validate(evidence_root: Path, derived_root: Path, report_path: Path) -> dict[str, Any]:
    records = authoritative_xex_records(evidence_root)
    manifests = load_derived_manifests(derived_root)
    identities: dict[str, dict[str, Any]] = {}

    for build_id in FULL_BUILD_IDS:
        record = records[build_id]
        embedded = record.get("derived_image")
        if not isinstance(embedded, dict):
            raise ConsistencyError(f"missing embedded derived image for {build_id}")
        embedded_text = block_by_name(memory_blocks(embedded, evidence_root), ".text", evidence_root)
        manifest_path = derived_root / build_id / "derived-image.json"
        manifest_text = block_by_name(
            memory_blocks(manifests[build_id], manifest_path), ".text", manifest_path
        )
        relative = manifest_text.get("derived_relative_path")
        if not isinstance(relative, str):
            raise ConsistencyError(f"missing .text derived_relative_path for {build_id}")
        section_path = derived_root / build_id / Path(relative)
        actual_size = section_path.stat().st_size if section_path.is_file() else -1
        actual_hash = sha256_file(section_path)
        for source_name, block in (("XEX evidence", embedded_text), ("derived manifest", manifest_text)):
            if block.get("size") != actual_size:
                raise ConsistencyError(
                    f"{build_id} .text size mismatch: {source_name}={block.get('size')} "
                    f"actual={actual_size} ({section_path})"
                )
            if str(block.get("sha256", "")).upper() != actual_hash:
                raise ConsistencyError(
                    f"{build_id} .text SHA-256 mismatch: {source_name}={block.get('sha256')} "
                    f"actual={actual_hash} ({section_path})"
                )
            if block.get("start") != manifest_text.get("start"):
                raise ConsistencyError(f"{build_id} .text start mismatch between artifacts")
        identities[build_id] = {
            "start": manifest_text["start"],
            "size": actual_size,
            "sha256": actual_hash,
        }

    jul_blocks = memory_blocks(
        manifests["jul-2009"], derived_root / "jul-2009" / "derived-image.json"
    )
    build_blocks = memory_blocks(
        manifests["build-23.12.02.0330"],
        derived_root / "build-23.12.02.0330" / "derived-image.json",
    )
    if len(jul_blocks) != len(build_blocks):
        raise ConsistencyError("July/build-23 initialized-section counts differ")
    for index, (left, right) in enumerate(zip(jul_blocks, build_blocks, strict=True)):
        fields = ("name", "start", "size", "sha256")
        if any(left.get(field) != right.get(field) for field in fields):
            raise ConsistencyError(f"July/build-23 section metadata differs at index {index}")
        for build_id, block in (("jul-2009", left), ("build-23.12.02.0330", right)):
            section_path = derived_root / build_id / str(block["derived_relative_path"])
            actual_hash = sha256_file(section_path)
            if actual_hash != str(block["sha256"]).upper():
                raise ConsistencyError(
                    f"{build_id} actual section SHA-256 differs at index {index}: {section_path}"
                )

    july_relationship, tu1_relationship = relationship_text_rows(evidence_root)
    donor = identities["build-23.12.02.0330"]
    july = identities["jul-2009"]
    relationship_checks = (
        ("July relationship left", july_relationship.get("left_sha256"), july["sha256"]),
        ("July relationship right", july_relationship.get("right_sha256"), donor["sha256"]),
        ("TU1 relationship donor", tu1_relationship.get("left_sha256"), donor["sha256"]),
    )
    for label, actual, expected in relationship_checks:
        if str(actual).upper() != expected:
            raise ConsistencyError(f"{label} SHA-256 mismatch: {actual} != {expected}")

    rows = report_rows(report_path)
    expected_rows = {
        "September": identities["sep-2008"],
        "July / build 23": donor,
    }
    if identities["jul-2009"] != donor:
        raise ConsistencyError("July/build-23 .text identities are not exact aliases")
    for label, expected in expected_rows.items():
        if rows[label] != expected:
            raise ConsistencyError(
                f"report {label} .text identity mismatch: {rows[label]} != {expected}"
            )

    return {
        "tool": {"name": TOOL_NAME, "version": TOOL_VERSION},
        "full_xex_builds_checked": len(FULL_BUILD_IDS),
        "july_build_23_initialized_sections_checked": len(jul_blocks),
        "text_identities": identities,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "--evidence-root",
        type=Path,
        default=Path("docs/fable2-prototype-archaeology/phase1/evidence"),
    )
    result.add_argument(
        "--derived-root", type=Path, default=Path("out/prototype-archaeology/derived")
    )
    result.add_argument(
        "--report",
        type=Path,
        default=Path("docs/fable2-prototype-archaeology/phase1/report.md"),
    )
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        result = validate(args.evidence_root, args.derived_root, args.report)
    except ConsistencyError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        "Verified Phase 1 section/report consistency: "
        f"{result['full_xex_builds_checked']} XEX builds, "
        f"{result['july_build_23_initialized_sections_checked']} aliased initialized sections"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
