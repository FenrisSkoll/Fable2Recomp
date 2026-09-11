#!/usr/bin/env python3
"""Cross-check Phase 2A exhaustive artifacts, summary identities, and report rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_RELATIVE_PATH = Path(
    "docs/fable2-prototype-archaeology/phase2a/evidence/"
    "prototype-correspondence-summary.json"
)
REPORT_RELATIVE_PATH = Path("docs/fable2-prototype-archaeology/phase2a/report.md")
ARTIFACTS = {
    "exhaustive_candidate_groups": Path(
        "out/prototype-archaeology/phase2a/"
        "prototype-correspondence-candidate-groups.json"
    ),
    "exhaustive_function_features": Path(
        "out/prototype-archaeology/phase2a/"
        "prototype-correspondence-function-features.json"
    ),
}
REPORT_ROW = re.compile(
    r"^\| `(?P<path>out/prototype-archaeology/phase2a/"
    r"prototype-correspondence-(?:candidate-groups|function-features)\.json)` "
    r"\| (?P<size>[0-9,]+) \| `(?P<sha256>[0-9A-F]{64})` \|$"
)


class ConsistencyError(ValueError):
    """Raised when Phase 2A exhaustive identities disagree."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise ConsistencyError(f"could not hash exhaustive artifact {path}: {error}") from error
    return digest.hexdigest().upper()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConsistencyError(f"could not read Phase 2A summary {path}: {error}") from error
    if not isinstance(value, dict):
        raise ConsistencyError(f"Phase 2A summary root must be an object: {path}")
    return value


def parse_report_rows(report_path: Path) -> dict[str, dict[str, Any]]:
    try:
        lines = report_path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ConsistencyError(f"could not read Phase 2A report {report_path}: {error}") from error
    records: dict[str, dict[str, Any]] = {}
    for line in lines:
        match = REPORT_ROW.fullmatch(line)
        if match is None:
            continue
        relative_path = match.group("path")
        if relative_path in records:
            raise ConsistencyError(f"duplicate exhaustive-artifact report row: {relative_path}")
        records[relative_path] = {
            "size": int(match.group("size").replace(",", "")),
            "sha256": match.group("sha256"),
        }
    return records


def validate(
    repository_root: Path,
    summary_path: Path,
    report_path: Path,
) -> int:
    root = repository_root.resolve()
    summary = read_json(summary_path)
    report_rows = parse_report_rows(report_path)
    checked = 0
    for summary_key, expected_relative_path in ARTIFACTS.items():
        identity = summary.get(summary_key)
        if not isinstance(identity, dict):
            raise ConsistencyError(f"summary is missing object {summary_key}")
        relative_text = expected_relative_path.as_posix()
        if identity.get("ignored_repository_relative_path") != relative_text:
            raise ConsistencyError(
                f"summary path mismatch for {summary_key}: "
                f"{identity.get('ignored_repository_relative_path')} != {relative_text}"
            )
        actual_path = (root / expected_relative_path).resolve()
        try:
            actual_path.relative_to(root)
        except ValueError as error:
            raise ConsistencyError(
                f"exhaustive artifact escapes repository root: {actual_path}"
            ) from error
        if not actual_path.is_file():
            raise ConsistencyError(f"exhaustive artifact is missing: {actual_path}")
        actual = {"size": actual_path.stat().st_size, "sha256": sha256_file(actual_path)}
        summary_identity = {"size": identity.get("size"), "sha256": identity.get("sha256")}
        if summary_identity != actual:
            raise ConsistencyError(
                f"summary identity mismatch for {relative_text}: "
                f"{summary_identity} != {actual}"
            )
        report_identity = report_rows.get(relative_text)
        if report_identity is None:
            raise ConsistencyError(f"report has no exhaustive-artifact row for {relative_text}")
        if report_identity != actual:
            raise ConsistencyError(
                f"report identity mismatch for {relative_text}: {report_identity} != {actual}"
            )
        checked += 1
    unexpected = sorted(set(report_rows) - {path.as_posix() for path in ARTIFACTS.values()})
    if unexpected:
        raise ConsistencyError(
            f"report contains unexpected exhaustive-artifact rows: {', '.join(unexpected)}"
        )
    return checked


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--repository-root", type=Path, default=REPOSITORY_ROOT)
    result.add_argument("--summary", type=Path)
    result.add_argument("--report", type=Path)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = args.repository_root.resolve()
    summary = args.summary.resolve() if args.summary else root / SUMMARY_RELATIVE_PATH
    report = args.report.resolve() if args.report else root / REPORT_RELATIVE_PATH
    try:
        checked = validate(root, summary, report)
    except ConsistencyError as error:
        print(f"ERROR: {error}")
        return 1
    print(f"Verified Phase 2A exhaustive artifact consistency: {checked} artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
