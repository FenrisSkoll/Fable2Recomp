#!/usr/bin/env python3
"""Create and verify the allowlisted Fable II Phase 4 closeout archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

import Fable2IndirectTargets as phase4


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE_ROOT = Path(
    r"C:\Dev\Fable2Phase4Archive\2026-09-02-phase4-closeout"
)
DEFAULT_XENIA_REPOSITORY = Path(r"C:\Dev\Fable2Phase4Xenia\xenia-canary")
DEFAULT_VALIDATION_RESULTS = (
    REPO_ROOT
    / "out"
    / "indirect-targets"
    / "fable2-tu1-manual-001-002-merged"
    / "phase4-closeout-validation.json"
)
FEATURE_BRANCH = "fable2-phase4-xenia-media-correction"
MAIN_BRANCH = "main"
XENIA_BRANCH = "fable2-indirect-target-collector"
RELEASE_TAG = "phase4-evidence-2026-09-02"
RELEASE_URL = (
    "https://github.com/FenrisSkoll/Fable2Recomp/releases/tag/"
    + RELEASE_TAG
)
MANIFEST_SHA256 = (
    "E3EB39CA153E396D5DC53E6F943ED8FF7AF1D6B0704EB860836BD7D21A3F87B0"
)
PATCHED_IMAGE_SHA256 = (
    "BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00"
)
LOADED_FINGERPRINT = "341151E9932EC14CB4F520AA9DE35BCF7169BFE1"
MANUAL_001_RAW_SHA256 = (
    "05E6344E2992089A9F7B7F509D8099D7E8851D130F2769BE9B9A8F72F20E03D0"
)
MANUAL_002_RAW_SHA256 = (
    "83DAA210412E6941AC0EE44D69EAED19C244FACC3D3637E93F4647132E67BD4D"
)
MERGED_EXPECTED = {
    "xenia-indirect-targets.summary.json": (
        27_377_874,
        "AE4670BAFDF6FC8AB719F81CCE14C5BD63FDD4EAA8262D0CDAB79B0E39F83A29",
    ),
    "xenia-indirect-targets.summary.csv": (
        5_534_648,
        "39D4600C006C84465612D70043E84B09DA8DE0075389AEFBBF28D8803CBC3D82",
    ),
    "fable2-indirect-targets.import-plan.json": (
        58_501_469,
        "82C262178A386CB4F519B9CF72D71C946948EB6AF06454349E060C41830AB6F6",
    ),
}
EXPECTED_FOLLOW_UP_COUNTS = {
    "existing_function_internal_entry": 42,
    "existing_manifest_function": 411,
    "known_jump_table_case": 114,
}
ZIP_TIMESTAMP = (2026, 9, 2, 0, 0, 0)
FORBIDDEN_MEMBER_SUFFIXES = {
    ".bin",
    ".dll",
    ".dmp",
    ".exe",
    ".iso",
    ".jsonl",
    ".lib",
    ".obj",
    ".pdb",
    ".sav",
    ".xex",
    ".xexp",
}
FORBIDDEN_MEMBER_COMPONENTS = {
    "cache_host",
    "content",
    "credentials",
    "saves",
    "storage",
}


class ArchiveError(RuntimeError):
    """Raised for a closeout safety or integrity failure."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def run_command(
    arguments: list[str], *, cwd: Path, capture: bool = True
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        arguments,
        cwd=cwd,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
    )
    if result.returncode:
        output = result.stdout.strip() if result.stdout else ""
        raise ArchiveError(
            f"command failed ({result.returncode}): {' '.join(arguments)}"
            + (f"\n{output}" if output else "")
        )
    return result


def git(repo: Path, *arguments: str) -> str:
    return run_command(["git", *arguments], cwd=repo).stdout.strip()


def repository_record(repo: Path, branches: list[str]) -> dict[str, Any]:
    if not (repo / ".git").exists():
        raise ArchiveError(f"not a Git repository: {repo}")
    status = git(repo, "status", "--porcelain=v1")
    if status:
        raise ArchiveError(f"repository is not clean: {repo}\n{status}")

    branch_records: list[dict[str, str]] = []
    for branch in branches:
        reference = f"refs/heads/{branch}"
        commit = git(repo, "rev-parse", "--verify", reference)
        tree = git(repo, "rev-parse", f"{commit}^{{tree}}")
        subject = git(repo, "show", "-s", "--format=%s", commit)
        branch_records.append(
            {
                "name": branch,
                "commit": commit,
                "tree": tree,
                "subject": subject,
            }
        )

    remotes: list[dict[str, str]] = []
    for line in git(repo, "remote", "-v").splitlines():
        fields = line.split()
        if len(fields) == 3:
            remotes.append(
                {
                    "name": fields[0],
                    "url": fields[1],
                    "direction": fields[2].strip("()"),
                }
            )
    remotes.sort(key=lambda value: (value["name"], value["direction"], value["url"]))
    return {
        "path": str(repo),
        "branches": branch_records,
        "remotes": remotes,
        "status": "clean",
    }


def file_record(path: Path, *, source_path: Path | None = None) -> dict[str, Any]:
    record: dict[str, Any] = {
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }
    if source_path is not None:
        record["source_path"] = str(source_path)
    return record


def ensure_safe_member(name: str) -> PurePosixPath:
    member = PurePosixPath(name)
    if (
        member.is_absolute()
        or not member.parts
        or ".." in member.parts
        or "\\" in name
        or ":" in member.parts[0]
    ):
        raise ArchiveError(f"unsafe ZIP member path: {name!r}")
    if any(part.startswith(".") for part in member.parts):
        raise ArchiveError(f"hidden ZIP member is not allowlisted: {name!r}")
    lowered_parts = {part.lower() for part in member.parts}
    if lowered_parts & FORBIDDEN_MEMBER_COMPONENTS:
        raise ArchiveError(f"private runtime component in ZIP member: {name!r}")
    if member.suffix.lower() in FORBIDDEN_MEMBER_SUFFIXES:
        raise ArchiveError(f"forbidden private-data suffix in ZIP member: {name!r}")
    lowered_name = member.name.lower()
    if any(
        token in lowered_name
        for token in ("credential", "private-key", "private_key", "cookie", "token")
    ):
        raise ArchiveError(f"credential-like ZIP member name: {name!r}")
    return member


def zip_info(name: str) -> zipfile.ZipInfo:
    ensure_safe_member(name)
    information = zipfile.ZipInfo(name, ZIP_TIMESTAMP)
    information.compress_type = zipfile.ZIP_DEFLATED
    information.create_system = 3
    information.external_attr = 0o100644 << 16
    return information


def create_deterministic_zip(
    path: Path,
    members: dict[str, Path | bytes],
) -> list[dict[str, Any]]:
    path.parent.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    with zipfile.ZipFile(
        path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for name in sorted(members):
            value = members[name]
            information = zip_info(name)
            digest = hashlib.sha256()
            byte_count = 0
            with archive.open(information, "w", force_zip64=True) as destination:
                if isinstance(value, bytes):
                    destination.write(value)
                    digest.update(value)
                    byte_count = len(value)
                else:
                    with value.open("rb") as source:
                        for block in iter(lambda: source.read(1024 * 1024), b""):
                            destination.write(block)
                            digest.update(block)
                            byte_count += len(block)
            records.append(
                {
                    "name": name,
                    "bytes": byte_count,
                    "sha256": digest.hexdigest().upper(),
                }
            )
    return records


def verify_zip(path: Path, expected: list[dict[str, Any]]) -> None:
    expected_by_name = {record["name"]: record for record in expected}
    expected_names = sorted(expected_by_name)
    with zipfile.ZipFile(path, "r") as archive:
        actual_names = archive.namelist()
        if actual_names != expected_names:
            raise ArchiveError(f"ZIP member allowlist mismatch: {path}")
        for information in archive.infolist():
            ensure_safe_member(information.filename)
            if information.is_dir():
                raise ArchiveError(f"unexpected directory entry: {information.filename}")

        with tempfile.TemporaryDirectory(prefix="fable2-phase4-zip-verify-") as temporary:
            extraction_root = Path(temporary).resolve()
            for name in actual_names:
                member = ensure_safe_member(name)
                destination = extraction_root.joinpath(*member.parts).resolve()
                if extraction_root not in destination.parents:
                    raise ArchiveError(f"ZIP extraction escapes root: {name}")
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(name, "r") as source, destination.open("wb") as target:
                    shutil.copyfileobj(source, target, length=1024 * 1024)
                expected_record = expected_by_name[name]
                if destination.stat().st_size != expected_record["bytes"]:
                    raise ArchiveError(f"extracted size mismatch: {path}!{name}")
                if sha256_file(destination) != expected_record["sha256"]:
                    raise ArchiveError(f"extracted hash mismatch: {path}!{name}")


def copy_artifact(source: Path, destination: Path) -> dict[str, Any]:
    if not source.is_file():
        raise ArchiveError(f"missing compact artifact: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    if sha256_file(source) != sha256_file(destination):
        raise ArchiveError(f"archive copy hash mismatch: {source}")
    record = file_record(destination, source_path=source)
    record["archive_path"] = destination.as_posix()
    return record


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ArchiveError(f"could not read JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise ArchiveError(f"JSON document must be an object: {path}")
    return value


def accepted_run(summary: dict[str, Any], run_id: str) -> dict[str, Any]:
    matches = [
        run
        for run in summary["runs"]
        if run["run_id"] == run_id and run["identity_match"]
    ]
    if len(matches) != 1:
        raise ArchiveError(f"expected exactly one accepted run {run_id}")
    return matches[0]


def target_observation(
    plan: dict[str, Any], target: str, source: str, classification: str
) -> dict[str, Any]:
    records = [value for value in plan["targets"] if value["target"] == target]
    if len(records) != 1:
        raise ArchiveError(f"expected one plan target {target}")
    record = records[0]
    if record["classification"] != classification or record.get("proposal") is not None:
        raise ArchiveError(f"acceptance classification/proposal mismatch for {target}")
    matching = [
        observation
        for observation in record["runtime"]["observations"]
        if observation["source"] == source
    ]
    if not matching:
        raise ArchiveError(f"acceptance source {source} missing for {target}")
    run_hits = {
        run_id: sum(item["run_hit_counts"].get(run_id, 0) for item in matching)
        for run_id in ("fable2-tu1-manual-001", "fable2-tu1-manual-002")
    }
    return {
        "target": target,
        "source": source,
        "branch_kinds": sorted({item["branch_kind"] for item in matching}),
        "run_hits": run_hits,
        "combined_hits": sum(run_hits.values()),
        "classification": classification,
        "owner": (record.get("ownership") or {}).get("owner_address"),
        "proposal": None,
    }


def compact_provenance_text(
    title: str,
    run_lines: list[str],
    member_records: list[dict[str, Any]],
) -> bytes:
    lines = [
        f"# {title}",
        "",
        *run_lines,
        "",
        "## Included files",
        "",
    ]
    for record in member_records:
        lines.append(
            f"- `{record['name']}` — {record['bytes']} bytes — "
            f"SHA-256 `{record['sha256']}`"
        )
    lines.extend(
        [
            "",
            "Raw traces, executable images, game assets, saves, memory dumps, "
            "content/storage/cache state and credentials are not included.",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def bundle_record(
    repository: Path,
    bundle_path: Path,
    references: list[str],
) -> dict[str, Any]:
    run_command(
        ["git", "bundle", "create", str(bundle_path), *references],
        cwd=repository,
    )
    verify = run_command(
        ["git", "bundle", "verify", str(bundle_path)], cwd=repository
    ).stdout.strip()
    heads = git(repository, "bundle", "list-heads", str(bundle_path))
    return {
        "archive_path": bundle_path.as_posix(),
        **file_record(bundle_path),
        "references": references,
        "heads": sorted(heads.splitlines()),
        "verification": verify.splitlines(),
    }


def validate_real_evidence(
    fable_repo: Path,
) -> tuple[dict[str, Path], dict[str, Any]]:
    root = fable_repo / "out" / "indirect-targets"
    paths = {
        "manual_001_summary": root
        / "fable2-tu1-manual-001"
        / "review"
        / "xenia-indirect-targets.summary.json",
        "manual_001_csv": root
        / "fable2-tu1-manual-001"
        / "review"
        / "xenia-indirect-targets.summary.csv",
        "manual_001_plan": root
        / "fable2-tu1-manual-001"
        / "review"
        / "fable2-indirect-targets.import-plan.json",
        "manual_002_summary": root
        / "fable2-tu1-manual-002"
        / "review"
        / "xenia-indirect-targets.summary.json",
        "manual_002_csv": root
        / "fable2-tu1-manual-002"
        / "review"
        / "xenia-indirect-targets.summary.csv",
        "manual_002_plan": root
        / "fable2-tu1-manual-002"
        / "review"
        / "fable2-indirect-targets.import-plan.json",
        "merged_summary": root
        / "fable2-tu1-manual-001-002-merged"
        / "xenia-indirect-targets.summary.json",
        "merged_csv": root
        / "fable2-tu1-manual-001-002-merged"
        / "xenia-indirect-targets.summary.csv",
        "merged_plan": root
        / "fable2-tu1-manual-001-002-merged"
        / "fable2-indirect-targets.import-plan.json",
        "follow_up_json": root
        / "fable2-tu1-manual-001-002-merged"
        / "phase4-static-ownership-follow-up.json",
        "follow_up_csv": root
        / "fable2-tu1-manual-001-002-merged"
        / "phase4-static-ownership-follow-up.csv",
        "follow_up_markdown": root
        / "fable2-tu1-manual-001-002-merged"
        / "phase4-static-ownership-follow-up.md",
    }
    for path in paths.values():
        if not path.is_file():
            raise ArchiveError(f"missing expected compact input: {path}")

    expected_identity = phase4.load_expected_identity(
        fable_repo / "tools" / "fable2-entrypoint-closure-evidence.json"
    )
    if expected_identity["patched_image_sha256"].upper() != PATCHED_IMAGE_SHA256:
        raise ArchiveError("canonical evidence has an unexpected patched-image hash")
    manual_001 = phase4.read_summary(paths["manual_001_summary"], expected_identity)
    manual_002 = phase4.read_summary(paths["manual_002_summary"], expected_identity)
    merged = phase4.read_summary(paths["merged_summary"], expected_identity)
    plan = phase4.read_plan(paths["merged_plan"])
    follow_up = phase4.validate_static_ownership_follow_up(
        load_json(paths["follow_up_json"])
    )

    run_001 = accepted_run(manual_001, "fable2-tu1-manual-001")
    run_002 = accepted_run(manual_002, "fable2-tu1-manual-002")
    if run_001["raw_sha256"] != MANUAL_001_RAW_SHA256:
        raise ArchiveError("manual-001 preserved raw hash is unexpected")
    if run_002["raw_sha256"] != MANUAL_002_RAW_SHA256:
        raise ArchiveError("manual-002 preserved raw hash is unexpected")
    normalized_001 = phase4.normalize_summary_run_metadata(run_001, "manual-001")
    normalized_002 = phase4.normalize_summary_run_metadata(run_002, "manual-002")
    if normalized_001["raw_schema_version"] is not None:
        raise ArchiveError("manual-001 raw schema must remain unavailable")
    if normalized_002["raw_schema_version"] != 2:
        raise ArchiveError("manual-002 must retain raw schema 2")
    if normalized_001["flush_reason"] is not None:
        raise ArchiveError("manual-001 compact evidence must not invent a flush reason")

    for name, (expected_bytes, expected_hash) in MERGED_EXPECTED.items():
        path = paths[
            {
                "xenia-indirect-targets.summary.json": "merged_summary",
                "xenia-indirect-targets.summary.csv": "merged_csv",
                "fable2-indirect-targets.import-plan.json": "merged_plan",
            }[name]
        ]
        if path.stat().st_size != expected_bytes or sha256_file(path) != expected_hash:
            raise ArchiveError(f"merged artifact identity mismatch: {path}")

    expected_counts = {
        "accepted_runs": 2,
        "quarantined_runs": 0,
        "unique_pairs": 27_785,
        "total_hits": 43_830_575_180,
    }
    for key, value in expected_counts.items():
        if merged["counts"].get(key) != value:
            raise ArchiveError(f"merged count mismatch for {key}")
    if follow_up["counts"]["targets"] != 567:
        raise ArchiveError("ownership follow-up does not contain 567 targets")
    if follow_up["counts"]["by_classification"] != EXPECTED_FOLLOW_UP_COUNTS:
        raise ArchiveError("ownership follow-up classification split is unexpected")
    if any(
        follow_up["counts"].get(key) != 0
        for key in ("range_proposals", "manifest_proposals", "automatically_applicable")
    ):
        raise ArchiveError("ownership follow-up unexpectedly contains applicable work")
    if plan["safety"].get("canonical_manifest_modified") is not False:
        raise ArchiveError("merged plan reports canonical manifest mutation")
    if plan.get("proposals"):
        raise ArchiveError("merged plan unexpectedly contains proposals")

    acceptance = [
        target_observation(
            plan,
            "0x829647F0",
            "0x829641C4",
            "existing_manifest_function",
        ),
        target_observation(
            plan,
            "0x82C03B28",
            "0x821907A4",
            "existing_manifest_function",
        ),
        target_observation(
            plan,
            "0x829675E0",
            "0x82966EE4",
            "existing_manifest_function",
        ),
        target_observation(
            plan,
            "0x82174734",
            "0x821746BC",
            "known_jump_table_case",
        ),
    ]
    expected_hits = (4_752, 17, 5_615, 102_422)
    if tuple(item["combined_hits"] for item in acceptance) != expected_hits:
        raise ArchiveError("acceptance observation hit counts are unexpected")
    if acceptance[3]["owner"] != "0x821746A8":
        raise ArchiveError("jump-table acceptance owner is unexpected")

    evidence = {
        "identity": {
            "patched_image_sha256": PATCHED_IMAGE_SHA256,
            "title_id": "0x4D5307F1",
            "media_id": "0x716F0A0D",
            "version": "0.0.1.26",
            "image_base": "0x82000000",
            "executable_range": {"start": "0x82170000", "end": "0x832D0000"},
            "loaded_fingerprint": {"algorithm": "SHA-1", "value": LOADED_FINGERPRINT},
        },
        "runs": [
            {
                "run_id": run_001["run_id"],
                "embedded_label": run_001["label"],
                "collector_schema": run_001["collector_version"],
                "raw_schema": normalized_001["raw_schema_version"],
                "raw_schema_status": normalized_001["raw_schema_version_status"],
                "recorded_raw_sha256": run_001["raw_sha256"],
                "raw_hash_provenance": "historical_preserved_not_recomputed",
                "termination": run_001["flush_status"],
                "footer_records": normalized_001["footer_records"],
                "flush_reason": normalized_001["flush_reason"],
                "integrity_warnings": run_001["integrity_warnings"],
                "counters": run_001["counters"],
            },
            {
                "run_id": run_002["run_id"],
                "embedded_label": run_002["label"],
                "collector_schema": run_002["collector_version"],
                "raw_schema": normalized_002["raw_schema_version"],
                "raw_schema_status": normalized_002["raw_schema_version_status"],
                "recorded_raw_sha256": run_002["raw_sha256"],
                "raw_hash_provenance": "preserved_summary_metadata_not_recomputed",
                "termination": run_002["flush_status"],
                "footer_records": normalized_002["footer_records"],
                "flush_reason": normalized_002["flush_reason"],
                "integrity_warnings": run_002["integrity_warnings"],
                "counters": run_002["counters"],
            },
        ],
        "merged": {
            "input_aggregate_records": 49_746,
            "unique_aggregate_keys": 27_785,
            "manual_001_only_keys": 4_671,
            "manual_002_only_keys": 1_153,
            "keys_in_both": 21_961,
            "manual_001_hits": 24_555_201_598,
            "manual_002_hits": 19_275_373_582,
            "combined_hits": 43_830_575_180,
            "non_return_targets": 16_143,
            "manual_001_only_targets": 2_093,
            "manual_002_only_targets": 567,
            "targets_in_both": 13_483,
            "classifications": {
                "existing_manifest_function": 13_087,
                "existing_function_internal_entry": 1_486,
                "known_jump_table_case": 1_561,
                "known_import_or_kernel_target": 9,
                "invalid_ambiguous_conflicting": 0,
            },
            "range_proposals": 0,
            "automatically_applicable": 0,
        },
        "acceptance_observations": acceptance,
        "ownership_follow_up": {
            "report_id": follow_up["report_id"],
            "targets": follow_up["counts"]["targets"],
            "by_classification": follow_up["counts"]["by_classification"],
            "range_proposals": 0,
            "manifest_proposals": 0,
            "automatically_applicable": 0,
        },
    }
    return paths, evidence


def create_archive(args: argparse.Namespace) -> dict[str, Any]:
    archive_root = args.archive_root.resolve()
    fable_repo = args.fable_repository.resolve(strict=True)
    xenia_repo = args.xenia_repository.resolve(strict=True)
    validation_path = args.validation_results.resolve(strict=True)
    if archive_root.exists():
        raise ArchiveError(
            f"archive target already exists; audit it instead of replacing it: {archive_root}"
        )
    archive_root.parent.mkdir(parents=True, exist_ok=True)
    staging = archive_root.parent / (
        f".{archive_root.name}.creating-{os.getpid()}"
    )
    if staging.exists():
        raise ArchiveError(f"staging directory already exists: {staging}")
    staging.mkdir()

    try:
        fable_record = repository_record(
            fable_repo, [FEATURE_BRANCH, MAIN_BRANCH]
        )
        xenia_record = repository_record(xenia_repo, [XENIA_BRANCH])
        feature_commit = fable_record["branches"][0]["commit"]
        main_commit = fable_record["branches"][1]["commit"]
        run_command(
            ["git", "merge-base", "--is-ancestor", feature_commit, main_commit],
            cwd=fable_repo,
        )
        validation_results = load_json(validation_path)
        if validation_results.get("schema") != {
            "name": "fable2-phase4-closeout-validation",
            "version": 1,
        }:
            raise ArchiveError("unexpected validation-results schema")

        manifest_path = fable_repo / "fable2_manifest.toml"
        if sha256_file(manifest_path) != MANIFEST_SHA256:
            raise ArchiveError("canonical manifest SHA-256 changed")
        source_paths, evidence = validate_real_evidence(fable_repo)

        for directory in ("artifacts", "bundles", "release-assets"):
            (staging / directory).mkdir()

        artifact_layout = {
            "manual_001_summary": "artifacts/manual-001/xenia-indirect-targets.summary.json",
            "manual_001_csv": "artifacts/manual-001/xenia-indirect-targets.summary.csv",
            "manual_001_plan": "artifacts/manual-001/fable2-indirect-targets.import-plan.json",
            "manual_002_summary": "artifacts/manual-002/xenia-indirect-targets.summary.json",
            "manual_002_csv": "artifacts/manual-002/xenia-indirect-targets.summary.csv",
            "manual_002_plan": "artifacts/manual-002/fable2-indirect-targets.import-plan.json",
            "merged_summary": "artifacts/merged/xenia-indirect-targets.summary.json",
            "merged_csv": "artifacts/merged/xenia-indirect-targets.summary.csv",
            "merged_plan": "artifacts/merged/fable2-indirect-targets.import-plan.json",
            "follow_up_json": "artifacts/merged/phase4-static-ownership-follow-up.json",
            "follow_up_csv": "artifacts/merged/phase4-static-ownership-follow-up.csv",
            "follow_up_markdown": "artifacts/merged/phase4-static-ownership-follow-up.md",
        }
        artifact_records: dict[str, dict[str, Any]] = {}
        for key, relative in artifact_layout.items():
            destination = staging / relative
            artifact_records[key] = copy_artifact(source_paths[key], destination)
            artifact_records[key]["archive_path"] = relative

        validation_destination = staging / "artifacts" / "phase4-closeout-validation.json"
        validation_record = copy_artifact(validation_path, validation_destination)
        validation_record["archive_path"] = "artifacts/phase4-closeout-validation.json"

        fable_bundle = staging / "bundles" / "Fable2Recomp-phase4.bundle"
        xenia_bundle = staging / "bundles" / "xenia-fable2-indirect-target-collector.bundle"
        bundle_records = [
            bundle_record(
                fable_repo,
                fable_bundle,
                [f"refs/heads/{FEATURE_BRANCH}", f"refs/heads/{MAIN_BRANCH}"],
            ),
            bundle_record(
                xenia_repo,
                xenia_bundle,
                [f"refs/heads/{XENIA_BRANCH}"],
            ),
        ]
        bundle_records[0]["archive_path"] = "bundles/Fable2Recomp-phase4.bundle"
        bundle_records[1]["archive_path"] = (
            "bundles/xenia-fable2-indirect-target-collector.bundle"
        )

        manual_001_members: dict[str, Path | bytes] = {
            "xenia-indirect-targets.summary.json": source_paths["manual_001_summary"],
            "xenia-indirect-targets.summary.csv": source_paths["manual_001_csv"],
            "fable2-indirect-targets.import-plan.json": source_paths["manual_001_plan"],
        }
        manual_002_members: dict[str, Path | bytes] = {
            "xenia-indirect-targets.summary.json": source_paths["manual_002_summary"],
            "xenia-indirect-targets.summary.csv": source_paths["manual_002_csv"],
            "fable2-indirect-targets.import-plan.json": source_paths["manual_002_plan"],
        }
        merged_members: dict[str, Path | bytes] = {
            "xenia-indirect-targets.summary.json": source_paths["merged_summary"],
            "xenia-indirect-targets.summary.csv": source_paths["merged_csv"],
            "fable2-indirect-targets.import-plan.json": source_paths["merged_plan"],
            "phase4-static-ownership-follow-up.json": source_paths["follow_up_json"],
            "phase4-static-ownership-follow-up.csv": source_paths["follow_up_csv"],
            "phase4-static-ownership-follow-up.md": source_paths["follow_up_markdown"],
        }

        zip_definitions = [
            (
                "phase4-manual-001-compact.zip",
                manual_001_members,
                [
                    "Accepted collector-schema-1 compact evidence.",
                    "Termination remains abnormal_or_unknown_no_footer with zero footers.",
                    "The recorded raw hash is historical and was not recomputed.",
                ],
            ),
            (
                "phase4-manual-002-compact.zip",
                manual_002_members,
                [
                    "Accepted collector/raw-schema-2 compact evidence.",
                    "Termination is normal with exactly one footer.",
                    "The compact summary does not retain a flush reason.",
                ],
            ),
            (
                "phase4-manual-001-002-merged.zip",
                merged_members,
                [
                    "Deterministic merge of the two accepted compact summaries.",
                    "The dry-run plan has zero proposals and made no manifest change.",
                    "The ownership queue contains exactly 567 deferred targets (411 / 42 / 114).",
                ],
            ),
        ]
        zip_records: list[dict[str, Any]] = []
        for name, members, run_lines in zip_definitions:
            preliminary = [
                {
                    "name": member_name,
                    "bytes": (
                        len(value) if isinstance(value, bytes) else value.stat().st_size
                    ),
                    "sha256": (
                        hashlib.sha256(value).hexdigest().upper()
                        if isinstance(value, bytes)
                        else sha256_file(value)
                    ),
                }
                for member_name, value in sorted(members.items())
            ]
            members["README.md"] = compact_provenance_text(
                name.removesuffix(".zip"), run_lines, preliminary
            )
            zip_path = staging / "release-assets" / name
            member_records = create_deterministic_zip(zip_path, members)
            verify_zip(zip_path, member_records)
            zip_records.append(
                {
                    "name": name,
                    "archive_path": f"release-assets/{name}",
                    **file_record(zip_path),
                    "members": member_records,
                    "verification": "allowlist_path_safety_extract_and_rehash_passed",
                }
            )

        archive_readme = (
            "# Fable II Phase 4 closeout archive\n\n"
            "This archive preserves the source history and allowlisted compact "
            "indirect-target evidence for Phase 4. Read `archive-manifest.json` "
            "for exact identities, provenance, counts, tests and exclusions.\n\n"
            "Raw traces, original or patched executables, game assets, saves, "
            "memory dumps, Xenia content/storage/cache state and credentials are "
            "intentionally excluded. The manifest remained unchanged.\n"
        ).encode("utf-8")
        atomic_write(staging / "README.md", archive_readme)

        manifest = {
            "schema": {"name": "fable2-phase4-closeout-archive", "version": 1},
            "creation_metadata": {
                "created_utc": args.created_utc,
                "volatile_fields_separated": True,
            },
            "archive_path": str(archive_root),
            "repositories": {
                "fable2recomp": fable_record,
                "xenia_collector": xenia_record,
                "xenia_upstream": {
                    "url": "https://github.com/xenia-canary/xenia-canary.git",
                    "pinned_commit": "3a44f20c7bc66db1da583e8a6f0ab740e31908e9",
                    "license": "BSD-3-Clause",
                    "publication_policy": "upstream_only_not_pushed",
                },
            },
            "tu1_identity": evidence["identity"],
            "canonical_manifest": {
                "path": str(manifest_path),
                "sha256_before_and_after": MANIFEST_SHA256,
                "modified": False,
            },
            "raw_trace_provenance": evidence["runs"],
            "merged_evidence": evidence["merged"],
            "acceptance_observations": evidence["acceptance_observations"],
            "ownership_follow_up": {
                **evidence["ownership_follow_up"],
                "files": {
                    key: artifact_records[key]
                    for key in (
                        "follow_up_json",
                        "follow_up_csv",
                        "follow_up_markdown",
                    )
                },
                "status": "deferred_static_ownership_backlog",
                "another_gameplay_capture_required": False,
            },
            "compact_artifacts": artifact_records,
            "validation": {
                **validation_results,
                "archive_copy": validation_record,
            },
            "git_bundles": bundle_records,
            "release": {
                "tag": RELEASE_TAG,
                "title": "Phase 4 indirect-target evidence — 2026-09-02",
                "url": RELEASE_URL,
                "kind": "analysis_evidence_prerelease",
                "tag_target": main_commit,
                "asset_allowlist": [
                    "phase4-manual-001-compact.zip",
                    "phase4-manual-002-compact.zip",
                    "phase4-manual-001-002-merged.zip",
                    "archive-manifest.json",
                    "SHA256SUMS.txt",
                ],
                "packages": zip_records,
            },
            "files_intentionally_excluded": [
                "raw indirect-target traces",
                "original/patched/extracted executable images and sections",
                "original game assets and title-update packages",
                "save files and save backups",
                "memory dumps",
                "Xenia content, storage and cache_host state",
                "compiled binaries",
                "credentials, tokens, cookies and private keys",
            ],
            "checksum_policy": {
                "algorithm": "SHA-256",
                "path": "SHA256SUMS.txt",
                "self_exclusion": [
                    "SHA256SUMS.txt",
                    "release-assets/SHA256SUMS.txt",
                ],
            },
            "next_active_phase": "native save-write parity",
        }
        manifest_bytes = canonical_json_bytes(manifest)
        atomic_write(staging / "archive-manifest.json", manifest_bytes)
        shutil.copyfile(
            staging / "archive-manifest.json",
            staging / "release-assets" / "archive-manifest.json",
        )

        release_notes = (
            "# Phase 4 indirect-target evidence — 2026-09-02\n\n"
            f"Exact patched TU1 SHA-256: `{PATCHED_IMAGE_SHA256}`. Title/media/version: "
            "`0x4D5307F1` / `0x716F0A0D` / `0.0.1.26`. Image base/range: "
            "`0x82000000`, `0x82170000`-`0x832D0000`. Loaded fingerprint: "
            f"`{LOADED_FINGERPRINT}`.\n\n"
            f"Fable2Recomp tag target: `{main_commit}`. Xenia collector: "
            f"`{xenia_record['branches'][0]['commit']}` atop pinned Xenia Canary "
            "`3a44f20c7bc66db1da583e8a6f0ab740e31908e9` (BSD-3-Clause).\n\n"
            "The merge contains 27,785 aggregate keys, 43,830,575,180 hits and "
            "16,143 non-return targets: 13,087 existing effective registrations, "
            "1,486 internal entries, 1,561 jump-table cases and 9 import/kernel "
            "targets. There are zero invalid, ambiguous or conflicting targets, "
            "zero range proposals and zero automatic manifest changes.\n\n"
            "Acceptance observations: `0x829647F0` has 4,752 hits and its trusted "
            "size remains `0x10`; `0x82C03B28` has 17 hits and size `0x1C`; "
            "`0x829675E0` has 5,615 hits and size `0x10`; "
            "`0x821746BC -> 0x82174734` has 102,422 `bctr` hits and remains a "
            "jump-table case owned by `0x821746A8`. None has a proposal.\n\n"
            "Manual-002 contributes 567 new targets: 411 effective registrations, "
            "42 internal entries and 114 jump-table cases. Static ownership review "
            "is deferred; another gameplay capture is optional. Native save-write "
            "parity is the next active phase.\n\n"
            f"Manual-001 raw provenance `{MANUAL_001_RAW_SHA256}` is historical and "
            "was not rehashed. Raw traces are not included. No executable, game "
            "asset or save is included. See the archive manifest and SHA256SUMS for "
            "the compact artifact/package hashes.\n"
        ).encode("utf-8")
        atomic_write(staging / "release-notes.md", release_notes)

        checksum_exclusions = {
            "SHA256SUMS.txt",
            "release-assets/SHA256SUMS.txt",
        }
        checksum_lines: list[str] = []
        for path in sorted(staging.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(staging).as_posix()
            if relative in checksum_exclusions:
                continue
            checksum_lines.append(f"{sha256_file(path)}  {relative}")
        checksum_bytes = ("\n".join(checksum_lines) + "\n").encode("ascii")
        atomic_write(staging / "SHA256SUMS.txt", checksum_bytes)
        shutil.copyfile(
            staging / "SHA256SUMS.txt",
            staging / "release-assets" / "SHA256SUMS.txt",
        )

        for line in checksum_bytes.decode("ascii").splitlines():
            digest, relative = line.split("  ", 1)
            if sha256_file(staging / relative) != digest:
                raise ArchiveError(f"checksum verification failed for {relative}")
        if (staging / "SHA256SUMS.txt").read_bytes() != (
            staging / "release-assets" / "SHA256SUMS.txt"
        ).read_bytes():
            raise ArchiveError("release checksum copy differs from archive checksum")

        os.replace(staging, archive_root)
        result = {
            "status": "phase4_archive_created_and_verified",
            "archive_root": str(archive_root),
            "archive_manifest_sha256": sha256_file(
                archive_root / "archive-manifest.json"
            ),
            "sha256sums_sha256": sha256_file(archive_root / "SHA256SUMS.txt"),
            "release_assets": {
                path.name: file_record(path)
                for path in sorted((archive_root / "release-assets").iterdir())
                if path.is_file()
            },
        }
        return result
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create the deterministic, allowlisted Fable II Phase 4 closeout "
            "archive and verify ZIP extraction, hashes and Git bundles."
        )
    )
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    parser.add_argument("--fable-repository", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--xenia-repository", type=Path, default=DEFAULT_XENIA_REPOSITORY
    )
    parser.add_argument(
        "--validation-results", type=Path, default=DEFAULT_VALIDATION_RESULTS
    )
    parser.add_argument(
        "--created-utc",
        required=True,
        help="explicit ISO-8601 archive creation timestamp (the only volatile field)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = create_archive(args)
    except (ArchiveError, OSError, phase4.Phase4Error) as error:
        parser.exit(1, f"ERROR: {error}\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
