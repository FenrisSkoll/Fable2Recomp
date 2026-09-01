#!/usr/bin/env python3
"""Summarize Xenia indirect targets and plan reviewed Fable II manifest imports.

All stable JSON output is deterministic. Trace collection and manifest planning
are disabled/dry-run by default; manifest mutation exists only in the explicit
``apply --apply --select ...`` workflow.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import gc
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import Fable2FunctionMap as function_map


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE = REPO_ROOT / "tools" / "fable2-entrypoint-closure-evidence.json"
DEFAULT_MANIFEST = REPO_ROOT / "fable2_manifest.toml"
DEFAULT_GENERATED_INIT = REPO_ROOT / "generated" / "default" / "fable2_init.cpp"

RAW_SCHEMA_NAME = "xenia_indirect_targets_raw"
RAW_SCHEMA_VERSION = 2
SUPPORTED_RAW_SCHEMA_VERSIONS = {1, 2}
SUMMARY_SCHEMA_NAME = "fable2-xenia-indirect-target-summary"
SUMMARY_SCHEMA_VERSION = 1
PLAN_SCHEMA_NAME = "fable2-indirect-target-import-plan"
PLAN_SCHEMA_VERSION = 1
TOOL_VERSION = "1.2.0"
UINT64_MAX = (1 << 64) - 1

COMPLETE_GAME_MEDIA_TYPES = {
    ".iso": "xbox_360_disc_image",
    ".zar": "xenia_disc_archive",
    ".xcp": "xbox_content_package",
}
LOOSE_EXECUTABLE_SUFFIXES = {".xex", ".elf"}
DEFAULT_COLLECTOR_BUFFER_PAIRS = 4096
DEFAULT_COLLECTOR_DIRTY_PAIRS = 3072
DEFAULT_COLLECTOR_FLUSH_INTERVAL_MS = 300_000
DEFAULT_COLLECTOR_MAX_UNIQUE_AGGREGATES = 1_000_000

CLASSIFICATIONS = {
    "existing_manifest_function",
    "existing_function_internal_entry",
    "known_jump_table_case",
    "known_exception_landing_pad",
    "known_import_or_kernel_target",
    "strong_new_function",
    "probable_new_function",
    "ambiguous_target",
    "invalid_or_non_executable_target",
    "conflicting_range",
}


class Phase4Error(ValueError):
    """Raised when a trace, plan, identity, or apply guard is invalid."""


def address(value: Any, location: str) -> int:
    try:
        parsed = function_map.parse_address(value, location)
    except function_map.MapValidationError as error:
        raise Phase4Error(str(error)) from error
    if parsed > 0xFFFFFFFF:
        raise Phase4Error(f"{location} is not a 32-bit guest address: {value!r}")
    return parsed


def address_text(value: int) -> str:
    return f"0x{value:08X}"


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    try:
        with temporary.open("wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_bytes(path, canonical_json_bytes(value))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def saturating_add(left: int, right: int) -> tuple[int, bool]:
    if left < 0 or right < 0:
        raise Phase4Error("negative counters are invalid")
    if right > UINT64_MAX - left:
        return UINT64_MAX, True
    return left + right, False


def require_object(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise Phase4Error(f"{location} must be an object")
    return value


def require_string(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value:
        raise Phase4Error(f"{location} must be a non-empty string")
    return value


def require_counter(value: Any, location: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise Phase4Error(f"{location} must be a non-negative integer")
    return min(value, UINT64_MAX)


def stable_pair_key(pair: dict[str, Any]) -> tuple[Any, ...]:
    return (
        pair["source_module"],
        address(pair["source"], "pair.source"),
        pair["target_module"],
        address(pair["target"], "pair.target"),
        pair["branch_kind"],
        pair["link"],
    )


def assess_run_identity(
    run: dict[str, Any],
    expected_image_sha256: str,
    expected_identity: dict[str, Any] | None,
) -> dict[str, Any]:
    header_identity = run["header"]["identity"]
    configured_hash = header_identity["expected_image_sha256"].upper()
    reasons: list[str] = []
    warnings: list[str] = []
    module_fingerprint_match = False
    if configured_hash != expected_image_sha256:
        reasons.append("configured_patched_image_sha256_mismatch")

    title_module: dict[str, Any] | None = None
    if expected_identity is not None:
        for key in ("title_id", "media_id", "version"):
            expected_value = str(expected_identity.get(key, ""))
            observed_value = str(header_identity.get(key, ""))
            if expected_value and observed_value != expected_value:
                reasons.append(f"{key}_mismatch")

        title_modules = [
            module for module in run["modules"] if module.get("title_module")
        ]
        if not title_modules:
            reasons.append("title_module_record_missing")
        else:
            # Module records are append ordered. CaptureModules may emit an
            # initial snapshot followed by a post-patch fingerprint refresh,
            # so select the last populated title-module snapshot. Falling
            # back to the last record preserves useful range diagnostics when
            # fingerprinting failed.
            title_module = next(
                (
                    module
                    for module in reversed(title_modules)
                    if module.get("fingerprint", {}).get("value")
                ),
                title_modules[-1],
            )
            expected_base = address(
                expected_identity["image_base"], "expected image base"
            )
            observed_base = address(title_module["image_base"], "module image base")
            if observed_base != expected_base:
                reasons.append("title_module_image_base_mismatch")
            sections = expected_identity.get("executable_sections", [])
            if sections:
                expected_start = min(
                    address(section["start"], "expected executable start")
                    for section in sections
                )
                expected_end = max(
                    address(section["end"], "expected executable end")
                    for section in sections
                )
                observed_start = address(
                    title_module["executable_start"], "module executable start"
                )
                observed_end = address(
                    title_module["executable_end"], "module executable end"
                )
                if observed_start > expected_start or observed_end < expected_end:
                    reasons.append("title_module_does_not_contain_executable_sections")
            if not title_module.get("fingerprint", {}).get("value"):
                warnings.append("post_patch_title_module_fingerprint_missing")

            expected_fingerprint_algorithm = str(
                expected_identity.get("xenia_module_fingerprint_algorithm", "")
            )
            expected_fingerprint = str(
                expected_identity.get("xenia_module_fingerprint", "")
            ).upper()
            observed_fingerprint = title_module.get("fingerprint", {})
            observed_fingerprint_algorithm = str(
                observed_fingerprint.get("algorithm", "")
            )
            observed_fingerprint_value = str(
                observed_fingerprint.get("value", "")
            ).upper()
            if expected_fingerprint_algorithm or expected_fingerprint:
                if not re.fullmatch(r"[0-9A-F]{40}", expected_fingerprint):
                    reasons.append("configured_xenia_module_fingerprint_is_malformed")
                if observed_fingerprint_algorithm != expected_fingerprint_algorithm:
                    reasons.append("xenia_module_fingerprint_algorithm_mismatch")
                if observed_fingerprint_value != expected_fingerprint:
                    reasons.append("xenia_module_fingerprint_mismatch")
                module_fingerprint_match = (
                    bool(expected_fingerprint_algorithm)
                    and bool(expected_fingerprint)
                    and observed_fingerprint_algorithm
                    == expected_fingerprint_algorithm
                    and observed_fingerprint_value == expected_fingerprint
                )
            elif observed_fingerprint_value:
                warnings.append("observed_xenia_module_fingerprint_is_not_pinned")

    if module_fingerprint_match:
        strength = "configured_sha256_metadata_ranges_and_pinned_observed_module_fingerprint"
    elif title_module and title_module.get("fingerprint", {}).get("value"):
        strength = "configured_sha256_metadata_ranges_with_unpinned_observed_module_fingerprint"
    elif expected_identity is not None:
        strength = "configured_sha256_metadata_and_module_ranges"
    else:
        strength = "configured_expected_sha256_only"
    return {
        "match": not reasons,
        "configured_expected_image_sha256": configured_hash,
        "observed_image_sha256": None,
        "reasons": sorted(reasons),
        "warnings": sorted(warnings),
        "strength": strength,
        "module_fingerprint_match": module_fingerprint_match,
        "selected_title_module": title_module,
    }


def merge_raw_pair_record(
    pair_aggregate: dict[tuple[Any, ...], dict[str, Any]],
    record: dict[str, Any],
) -> bool:
    """Merge one committed delta record, returning whether its count saturated."""
    source = address(record["source"], "pair.source")
    target = address(record["target"], "pair.target")
    pair_key = (
        record["source_module"],
        source,
        record["target_module"],
        target,
        record["branch_kind"],
        record["link"],
        record["ordinary_return"],
        record["thread_key"],
        record["target_validity"],
    )
    aggregate = pair_aggregate.get(pair_key)
    if aggregate is None:
        aggregate = dict(record)
        aggregate["source"] = address_text(source)
        aggregate["target"] = address_text(target)
        pair_aggregate[pair_key] = aggregate
        return False

    aggregate["hit_count"], overflow = saturating_add(
        aggregate["hit_count"], record["hit_count"]
    )
    aggregate["first_thread_sequence"] = min(
        aggregate["first_thread_sequence"], record["first_thread_sequence"]
    )
    aggregate["last_thread_sequence"] = max(
        aggregate["last_thread_sequence"], record["last_thread_sequence"]
    )
    return overflow


def parse_raw_trace(path: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    header: dict[str, Any] | None = None
    footer: dict[str, Any] | None = None
    checkpoint: dict[str, Any] | None = None
    modules: list[dict[str, Any]] = []
    pair_aggregate: dict[tuple[Any, ...], dict[str, Any]] = {}
    record_counts: Counter[str] = Counter()
    corrupt_tail = False
    missing_final_newline = False
    parser_count_overflows = 0
    raw_schema_version: int | None = None
    pending_batch_id: int | None = None
    pending_pairs: list[dict[str, Any]] = []
    committed_pair_records = 0
    committed_hits = 0
    last_checkpoint_sequence = 0
    parser_integrity_warnings: list[str] = []

    try:
        stream = path.open("rb")
    except OSError as error:
        raise Phase4Error(f"could not open raw trace '{path}': {error}") from error

    with stream:
        for line_number, raw_line in enumerate(stream, 1):
            digest.update(raw_line)
            has_newline = raw_line.endswith(b"\n")
            if not has_newline:
                missing_final_newline = True
            try:
                text = raw_line.decode("utf-8")
                record = json.loads(text)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                if not has_newline:
                    corrupt_tail = True
                    break
                raise Phase4Error(
                    f"raw trace '{path}' has corrupt JSON at line {line_number}: {error}"
                ) from error
            if not isinstance(record, dict):
                raise Phase4Error(
                    f"raw trace '{path}' line {line_number} is not an object"
                )
            kind = require_string(record.get("record"), f"raw line {line_number}.record")
            record_counts[kind] += 1
            if footer is not None:
                raise Phase4Error(
                    f"raw trace '{path}' has a record after its footer at line {line_number}"
                )
            if kind == "header":
                if header is not None or line_number != 1:
                    raise Phase4Error(f"raw trace '{path}' has a misplaced/duplicate header")
                header = record
                if record.get("schema") != RAW_SCHEMA_NAME:
                    raise Phase4Error(
                        f"raw trace '{path}' schema is {record.get('schema')!r}, "
                        f"expected {RAW_SCHEMA_NAME!r}"
                    )
                raw_schema_version = require_counter(
                    record.get("schema_version"), "header.schema_version"
                )
                if raw_schema_version not in SUPPORTED_RAW_SCHEMA_VERSIONS:
                    raise Phase4Error(
                        f"raw trace '{path}' schema version is "
                        f"{raw_schema_version!r}; supported versions are "
                        f"{sorted(SUPPORTED_RAW_SCHEMA_VERSIONS)}"
                    )
                require_string(record.get("run_id"), "header.run_id")
                require_string(record.get("xenia_commit"), "header.xenia_commit")
                require_counter(record.get("collector_version"), "header.collector_version")
                require_counter(record.get("started_unix_ns"), "header.started_unix_ns")
                identity = require_object(record.get("identity"), "header.identity")
                expected_hash = require_string(
                    identity.get("expected_image_sha256"),
                    "header.identity.expected_image_sha256",
                ).upper()
                if not re.fullmatch(r"[0-9A-F]{64}", expected_hash):
                    raise Phase4Error("header expected image SHA-256 is malformed")
                identity["expected_image_sha256"] = expected_hash
                settings = require_object(record.get("settings"), "header.settings")
                for key in ("include_returns", "all_modules"):
                    if not isinstance(settings.get(key), bool):
                        raise Phase4Error(f"header.settings.{key} must be boolean")
                if raw_schema_version == 1:
                    for key in ("buffer_pairs", "flush_hits"):
                        require_counter(settings.get(key), f"header.settings.{key}")
                else:
                    for key in (
                        "buffer_pairs",
                        "dirty_pair_limit",
                        "flush_interval_ms",
                        "max_unique_aggregates",
                    ):
                        require_counter(settings.get(key), f"header.settings.{key}")
                    if settings["dirty_pair_limit"] > settings["buffer_pairs"]:
                        raise Phase4Error(
                            "header.settings.dirty_pair_limit exceeds buffer_pairs"
                        )
                    if settings.get("pair_count_semantics") != (
                        "delta_since_previous_persistence"
                    ):
                        raise Phase4Error(
                            "schema-2 pair_count_semantics must be "
                            "delta_since_previous_persistence"
                        )
            elif kind == "module":
                if header is None:
                    raise Phase4Error(
                        f"raw trace '{path}' contains a module before its header"
                    )
                if record.get("run_id") != header["run_id"]:
                    raise Phase4Error(
                        f"raw trace '{path}' module run ID disagrees with header"
                    )
                require_string(record.get("name"), "module.name")
                image_base = address(record.get("image_base"), "module.image_base")
                executable_start = address(
                    record.get("executable_start"), "module.executable_start"
                )
                executable_end = address(
                    record.get("executable_end"), "module.executable_end"
                )
                if not isinstance(record.get("executable"), bool) or not isinstance(
                    record.get("title_module"), bool
                ):
                    raise Phase4Error(
                        "module.executable and module.title_module must be boolean"
                    )
                if executable_end < executable_start:
                    raise Phase4Error("module executable range is inverted")
                if record["title_module"] and executable_end == executable_start:
                    raise Phase4Error("title module executable range must be non-empty")
                if executable_end == executable_start and executable_start != 0:
                    raise Phase4Error(
                        "empty unresolved module ranges must use the zero sentinel"
                    )
                if image_base and executable_start and image_base > executable_start:
                    raise Phase4Error("module image base is above its executable start")
                fingerprint = require_object(record.get("fingerprint"), "module.fingerprint")
                if not isinstance(fingerprint.get("algorithm"), str) or not isinstance(
                    fingerprint.get("value"), str
                ):
                    raise Phase4Error(
                        "module fingerprint algorithm and value must be strings"
                    )
                modules.append(record)
            elif kind == "pair":
                if header is None:
                    raise Phase4Error(f"raw trace '{path}' contains a pair before its header")
                if record.get("run_id") != header["run_id"]:
                    raise Phase4Error(f"raw trace '{path}' pair run ID disagrees with header")
                batch_id = require_counter(record.get("batch_id"), "pair.batch_id")
                address(record.get("source"), "pair.source")
                address(record.get("target"), "pair.target")
                branch_kind = require_string(record.get("branch_kind"), "pair.branch_kind")
                if branch_kind not in {"bctr", "bctrl", "bclr", "blr"}:
                    raise Phase4Error(f"unsupported branch kind {branch_kind!r}")
                if not isinstance(record.get("link"), bool):
                    raise Phase4Error("pair.link must be boolean")
                require_string(record.get("source_module"), "pair.source_module")
                require_string(record.get("target_module"), "pair.target_module")
                thread_key = require_string(record.get("thread_key"), "pair.thread_key")
                hit_count = require_counter(record.get("hit_count"), "pair.hit_count")
                first_sequence = require_counter(
                    record.get("first_thread_sequence"),
                    "pair.first_thread_sequence",
                )
                last_sequence = require_counter(
                    record.get("last_thread_sequence"),
                    "pair.last_thread_sequence",
                )
                if hit_count and last_sequence < first_sequence:
                    raise Phase4Error(
                        "pair.last_thread_sequence is below first_thread_sequence"
                    )
                ordinary_return = record.get("ordinary_return")
                if not isinstance(ordinary_return, bool):
                    raise Phase4Error("pair.ordinary_return must be boolean")
                if branch_kind == "bctrl" and not record["link"]:
                    raise Phase4Error("bctrl pair must have link=true")
                if branch_kind == "bctr" and record["link"]:
                    raise Phase4Error("bctr pair must have link=false")
                if branch_kind == "blr" and (
                    record["link"] or not ordinary_return
                ):
                    raise Phase4Error(
                        "blr pair must have link=false and ordinary_return=true"
                    )
                if ordinary_return and branch_kind != "blr":
                    raise Phase4Error(
                        "ordinary_return may only be set for branch_kind=blr"
                    )
                validity = require_string(
                    record.get("target_validity"), "pair.target_validity"
                )
                if raw_schema_version == 2:
                    if record.get("count_semantics") != (
                        "delta_since_previous_persistence"
                    ):
                        raise Phase4Error(
                            "schema-2 pair.count_semantics must be "
                            "delta_since_previous_persistence"
                        )
                    if pending_batch_id is None:
                        pending_batch_id = batch_id
                    elif batch_id != pending_batch_id:
                        raise Phase4Error(
                            f"raw trace '{path}' starts batch {batch_id} before "
                            f"checkpointing batch {pending_batch_id}"
                        )
                    pending_pairs.append(record)
                else:
                    parser_count_overflows += int(
                        merge_raw_pair_record(pair_aggregate, record)
                    )
            elif kind == "checkpoint":
                if header is None or record.get("run_id") != header["run_id"]:
                    raise Phase4Error(
                        f"raw trace '{path}' checkpoint run ID disagrees with header"
                    )
                checkpoint_batch_id = require_counter(
                    record.get("batch_id"), "checkpoint.batch_id"
                )
                for key in (
                    "total_hits",
                    "total_pair_records",
                    "dropped_hits",
                    "io_errors",
                    "count_overflows",
                ):
                    require_counter(record.get(key), f"checkpoint.{key}")
                if raw_schema_version == 2:
                    checkpoint_sequence = require_counter(
                        record.get("checkpoint_sequence"),
                        "checkpoint.checkpoint_sequence",
                    )
                    if checkpoint_sequence != checkpoint_batch_id:
                        raise Phase4Error(
                            "schema-2 checkpoint sequence must equal its batch ID"
                        )
                    if checkpoint_sequence != last_checkpoint_sequence + 1:
                        raise Phase4Error(
                            f"schema-2 checkpoint sequence {checkpoint_sequence} is "
                            f"not consecutive after {last_checkpoint_sequence}"
                        )
                    require_counter(
                        record.get("collector_version"),
                        "checkpoint.collector_version",
                    )
                    if record["collector_version"] != header["collector_version"]:
                        raise Phase4Error(
                            "schema-2 checkpoint collector version disagrees with header"
                        )
                    require_string(
                        record.get("flush_reason"), "checkpoint.flush_reason"
                    )
                    batch_pair_records = require_counter(
                        record.get("batch_pair_records"),
                        "checkpoint.batch_pair_records",
                    )
                    require_counter(
                        record.get("persisted_aggregate_count"),
                        "checkpoint.persisted_aggregate_count",
                    )
                    require_counter(
                        record.get("aggregate_limit_exceeded"),
                        "checkpoint.aggregate_limit_exceeded",
                    )
                    if pending_batch_id != checkpoint_batch_id:
                        raise Phase4Error(
                            f"schema-2 checkpoint {checkpoint_batch_id} does not "
                            f"commit pending batch {pending_batch_id}"
                        )
                    if batch_pair_records != len(pending_pairs):
                        raise Phase4Error(
                            f"schema-2 checkpoint {checkpoint_batch_id} claims "
                            f"{batch_pair_records} pair records but {len(pending_pairs)} "
                            "precede it"
                        )
                    for pending_pair in pending_pairs:
                        parser_count_overflows += int(
                            merge_raw_pair_record(pair_aggregate, pending_pair)
                        )
                        committed_hits, overflow = saturating_add(
                            committed_hits, pending_pair["hit_count"]
                        )
                        parser_count_overflows += int(overflow)
                    committed_pair_records += len(pending_pairs)
                    if record["total_pair_records"] != committed_pair_records:
                        raise Phase4Error(
                            f"schema-2 checkpoint {checkpoint_batch_id} total pair "
                            "record count does not reconcile"
                        )
                    if record["total_hits"] != committed_hits:
                        raise Phase4Error(
                            f"schema-2 checkpoint {checkpoint_batch_id} total hit "
                            "count does not reconcile"
                        )
                    pending_pairs.clear()
                    pending_batch_id = None
                    last_checkpoint_sequence = checkpoint_sequence
                checkpoint = record
            elif kind == "footer":
                if header is None or record.get("run_id") != header["run_id"]:
                    raise Phase4Error(
                        f"raw trace '{path}' footer run ID disagrees with header"
                    )
                require_string(record.get("shutdown_status"), "footer.shutdown_status")
                for key in (
                    "total_hits",
                    "total_pair_records",
                    "dropped_hits",
                    "io_errors",
                    "count_overflows",
                ):
                    require_counter(record.get(key), f"footer.{key}")
                if raw_schema_version == 2:
                    if pending_pairs:
                        raise Phase4Error(
                            "schema-2 footer follows an uncheckpointed pair batch"
                        )
                    if require_counter(
                        record.get("raw_schema_version"),
                        "footer.raw_schema_version",
                    ) != 2:
                        raise Phase4Error("schema-2 footer raw schema version disagrees")
                    require_counter(
                        record.get("collector_version"),
                        "footer.collector_version",
                    )
                    if record["collector_version"] != header["collector_version"]:
                        raise Phase4Error(
                            "schema-2 footer collector version disagrees with header"
                        )
                    require_string(record.get("flush_reason"), "footer.flush_reason")
                    batches = require_counter(record.get("batches"), "footer.batches")
                    footer_sequence = require_counter(
                        record.get("checkpoint_sequence"),
                        "footer.checkpoint_sequence",
                    )
                    checkpoint_records = require_counter(
                        record.get("checkpoint_records"),
                        "footer.checkpoint_records",
                    )
                    if footer_sequence != last_checkpoint_sequence:
                        raise Phase4Error(
                            "schema-2 footer checkpoint sequence does not reconcile"
                        )
                    if checkpoint_records != record_counts["checkpoint"]:
                        raise Phase4Error(
                            "schema-2 footer checkpoint record count does not reconcile"
                        )
                    if batches != footer_sequence or batches != checkpoint_records:
                        raise Phase4Error(
                            "schema-2 footer batch/checkpoint counts do not reconcile"
                        )
                    for key in (
                        "final_unique_aggregates",
                        "final_sequence",
                        "aggregate_limit_exceeded",
                    ):
                        require_counter(record.get(key), f"footer.{key}")
                    if not isinstance(
                        record.get("unique_aggregate_count_complete"), bool
                    ):
                        raise Phase4Error(
                            "footer.unique_aggregate_count_complete must be boolean"
                        )
                    if record.get("sequence_scope") != (
                        "maximum_per_thread_sequence"
                    ):
                        raise Phase4Error("unsupported schema-2 footer sequence scope")
                    if record.get("pair_count_semantics") != (
                        "delta_since_previous_persistence"
                    ):
                        raise Phase4Error("unsupported schema-2 footer count semantics")
                footer = record
            else:
                raise Phase4Error(f"raw trace '{path}' has unknown record kind {kind!r}")

    if header is None:
        raise Phase4Error(f"raw trace '{path}' has no complete header")

    uncommitted_pair_records = 0
    if raw_schema_version == 2 and pending_pairs:
        uncommitted_pair_records = len(pending_pairs)
        parser_integrity_warnings.append(
            "schema-2 trailing pair batch has no checkpoint and was discarded"
        )

    final_counters = footer or checkpoint or {}
    counters = {
        key: require_counter(final_counters.get(key, 0), f"final.{key}")
        for key in (
            "total_hits",
            "total_pair_records",
            "dropped_hits",
            "io_errors",
            "count_overflows",
            "aggregate_limit_exceeded",
        )
    }
    counters["count_overflows"], _ = saturating_add(
        counters["count_overflows"], parser_count_overflows
    )
    pairs = sorted(
        pair_aggregate.values(),
        key=lambda pair: (
            *stable_pair_key(pair),
            pair["thread_key"],
            pair["target_validity"],
        ),
    )
    integrity_warnings = list(parser_integrity_warnings)
    if footer and footer.get("shutdown_status") == "normal" and missing_final_newline:
        integrity_warnings.append("normal footer is not newline-terminated")
    if footer and footer.get("shutdown_status") == "normal" and not corrupt_tail:
        durable_pair_records = (
            committed_pair_records
            if raw_schema_version == 2
            else record_counts["pair"]
        )
        if footer.get("total_pair_records") != durable_pair_records:
            integrity_warnings.append(
                "normal footer total_pair_records disagrees with parsed pair records"
            )
        parsed_hits = 0
        for pair in pairs:
            parsed_hits, _ = saturating_add(parsed_hits, pair["hit_count"])
        if footer.get("total_hits") != parsed_hits:
            integrity_warnings.append(
                "normal footer total_hits disagrees with parsed pair hit counts"
            )
        if raw_schema_version == 2:
            parsed_aggregate_keys = {
                (
                    pair["thread_key"],
                    pair["source"],
                    pair["target"],
                    pair["branch_kind"],
                    pair["link"],
                )
                for pair in pairs
            }
            if (
                footer.get("unique_aggregate_count_complete")
                and footer.get("final_unique_aggregates")
                != len(parsed_aggregate_keys)
            ):
                integrity_warnings.append(
                    "normal footer final_unique_aggregates disagrees with parsed "
                    "pair/thread aggregates"
                )
            parsed_final_sequence = max(
                (pair["last_thread_sequence"] for pair in pairs), default=0
            )
            if footer.get("final_sequence") != parsed_final_sequence:
                integrity_warnings.append(
                    "normal footer final_sequence disagrees with parsed thread "
                    "sequences"
                )
    normal_footer = bool(
        footer
        and footer.get("shutdown_status") == "normal"
        and not corrupt_tail
        and not integrity_warnings
    )
    if normal_footer:
        flush_status = "normal"
    elif corrupt_tail:
        flush_status = "abnormal_truncated_tail"
    elif footer:
        if integrity_warnings:
            flush_status = "invalid_normal_footer"
        else:
            flush_status = str(footer.get("shutdown_status") or "abnormal_or_unknown")
    else:
        flush_status = "abnormal_or_unknown_no_footer"

    return {
        "path": path,
        "file_name": path.name,
        "sha256": digest.hexdigest().upper(),
        "header": header,
        "modules": modules,
        "pairs": pairs,
        "counters": counters,
        "record_counts": dict(sorted(record_counts.items())),
        "raw_schema_version": raw_schema_version,
        "uncommitted_pair_records": uncommitted_pair_records,
        "flush_status": flush_status,
        "corrupt_tail": corrupt_tail,
        "missing_final_newline": missing_final_newline,
        "integrity_warnings": integrity_warnings,
    }


def aggregate_raw_runs(
    runs: list[dict[str, Any]],
    expected_image_sha256: str,
    expected_identity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    expected_image_sha256 = expected_image_sha256.upper()
    seen_hashes: set[str] = set()
    seen_run_ids: set[str] = set()
    run_records: list[dict[str, Any]] = []
    quarantined: list[dict[str, Any]] = []
    aggregate: dict[tuple[Any, ...], dict[str, Any]] = {}
    overflow_count = 0

    for run in sorted(runs, key=lambda item: (item["header"]["run_id"], item["sha256"])):
        run_id = run["header"]["run_id"]
        if run["sha256"] in seen_hashes:
            raise Phase4Error(f"duplicate raw trace content: SHA-256 {run['sha256']}")
        if run_id in seen_run_ids:
            raise Phase4Error(f"duplicate run ID: {run_id}")
        seen_hashes.add(run["sha256"])
        seen_run_ids.add(run_id)

        identity_assessment = assess_run_identity(
            run, expected_image_sha256, expected_identity
        )
        configured_identity = identity_assessment["configured_expected_image_sha256"]
        identity_match = identity_assessment["match"]
        run_record = {
            "run_id": run_id,
            "label": run["header"].get("label", ""),
            "raw_file_name": run["file_name"],
            "raw_sha256": run["sha256"],
            "xenia_commit": run["header"]["xenia_commit"],
            "collector_version": run["header"].get("collector_version"),
            "raw_schema_version": run["raw_schema_version"],
            "configured_expected_image_sha256": configured_identity,
            "observed_image_sha256": None,
            "identity_match": identity_match,
            "identity_assessment": identity_assessment,
            "flush_status": run["flush_status"],
            "corrupt_tail": run["corrupt_tail"],
            "missing_final_newline": run["missing_final_newline"],
            "integrity_warnings": run["integrity_warnings"],
            "record_counts": run["record_counts"],
            "uncommitted_pair_records": run["uncommitted_pair_records"],
            "counters": run["counters"],
            "modules": sorted(
                run["modules"],
                key=lambda item: (
                    item.get("name", ""),
                    item.get("executable_start", ""),
                    item.get("executable_end", ""),
                ),
            ),
        }
        run_records.append(run_record)
        if not identity_match:
            quarantined.append(
                {
                    "kind": "image_or_module_identity_mismatch",
                    "run_id": run_id,
                    "raw_sha256": run["sha256"],
                    "expected_image_sha256": expected_image_sha256,
                    "configured_expected_image_sha256": configured_identity,
                    "observed_image_sha256": None,
                    "reasons": identity_assessment["reasons"],
                }
            )
            continue

        for pair in run["pairs"]:
            key = stable_pair_key(pair)
            item = aggregate.setdefault(
                key,
                {
                    "source": address_text(address(pair["source"], "pair.source")),
                    "target": address_text(address(pair["target"], "pair.target")),
                    "branch_kind": pair["branch_kind"],
                    "link": pair["link"],
                    "ordinary_return": bool(pair.get("ordinary_return", False)),
                    "source_module": pair["source_module"],
                    "target_module": pair["target_module"],
                    "hit_count": 0,
                    "run_hit_counts": {},
                    "observed_runs": [],
                    "thread_observations": {},
                    "target_validity": [],
                },
            )
            hit_count = require_counter(pair["hit_count"], "pair.hit_count")
            item["hit_count"], overflow = saturating_add(item["hit_count"], hit_count)
            overflow_count += int(overflow)
            previous_run_count = item["run_hit_counts"].get(run_id, 0)
            item["run_hit_counts"][run_id], overflow = saturating_add(
                previous_run_count, hit_count
            )
            overflow_count += int(overflow)
            if run_id not in item["observed_runs"]:
                item["observed_runs"].append(run_id)
            thread_key = pair["thread_key"]
            thread_observation_key = (run_id, thread_key)
            observation = item["thread_observations"].setdefault(
                thread_observation_key,
                {
                    "run_id": run_id,
                    "thread_key": thread_key,
                    "first_sequence": pair["first_thread_sequence"],
                    "last_sequence": pair["last_thread_sequence"],
                    "hit_count": 0,
                },
            )
            observation["first_sequence"] = min(
                observation["first_sequence"], pair["first_thread_sequence"]
            )
            observation["last_sequence"] = max(
                observation["last_sequence"], pair["last_thread_sequence"]
            )
            observation["hit_count"], overflow = saturating_add(
                observation["hit_count"], hit_count
            )
            overflow_count += int(overflow)
            validity = str(pair.get("target_validity") or "unknown")
            if validity not in item["target_validity"]:
                item["target_validity"].append(validity)

    pairs: list[dict[str, Any]] = []
    for item in aggregate.values():
        item["observed_runs"].sort()
        item["run_hit_counts"] = dict(sorted(item["run_hit_counts"].items()))
        item["thread_observations"] = [
            value
            for _, value in sorted(item["thread_observations"].items())
        ]
        item["target_validity"].sort()
        pairs.append(item)
    pairs.sort(key=stable_pair_key)

    total_hits = 0
    dropped_hits = 0
    io_errors = 0
    aggregate_limit_exceeded = 0
    count_overflows = overflow_count
    for run in run_records:
        if not run["identity_match"]:
            continue
        total_hits, overflow = saturating_add(total_hits, run["counters"]["total_hits"])
        count_overflows += int(overflow)
        dropped_hits, overflow = saturating_add(
            dropped_hits, run["counters"]["dropped_hits"]
        )
        count_overflows += int(overflow)
        io_errors, overflow = saturating_add(io_errors, run["counters"]["io_errors"])
        count_overflows += int(overflow)
        aggregate_limit_exceeded, overflow = saturating_add(
            aggregate_limit_exceeded,
            run["counters"]["aggregate_limit_exceeded"],
        )
        count_overflows += int(overflow)
        count_overflows, _ = saturating_add(
            count_overflows, run["counters"]["count_overflows"]
        )

    return {
        "schema": {"name": SUMMARY_SCHEMA_NAME, "version": SUMMARY_SCHEMA_VERSION},
        "tool": {"name": "Fable2IndirectTargets", "version": TOOL_VERSION},
        "identity": {
            "expected_image_sha256": expected_image_sha256,
            "identity_strength": (
                "configured_sha256_metadata_ranges_and_pinned_observed_module_fingerprint"
                if expected_identity
                and expected_identity.get("xenia_module_fingerprint")
                else (
                    "configured_sha256_metadata_and_module_ranges"
                    if expected_identity is not None
                    else "configured_expected_sha256_only"
                )
            ),
            "expected_title_id": (
                expected_identity.get("title_id") if expected_identity else None
            ),
            "expected_media_id": (
                expected_identity.get("media_id") if expected_identity else None
            ),
            "expected_version": (
                expected_identity.get("version") if expected_identity else None
            ),
        },
        "counts": {
            "accepted_runs": sum(run["identity_match"] for run in run_records),
            "quarantined_runs": len(quarantined),
            "unique_pairs": len(pairs),
            "total_hits": total_hits,
            "dropped_hits": dropped_hits,
            "io_errors": io_errors,
            "count_overflows": count_overflows,
            "aggregate_limit_exceeded": aggregate_limit_exceeded,
            "abnormal_or_truncated_runs": sum(
                run["flush_status"] != "normal"
                for run in run_records
                if run["identity_match"]
            ),
        },
        "runs": run_records,
        "quarantine": quarantined,
        "pairs": pairs,
        "determinism": {
            "volatile_metadata_omitted": True,
            "sort_key": [
                "source_module",
                "source",
                "target_module",
                "target",
                "branch_kind",
                "link",
            ],
        },
    }


def validate_summary(document: dict[str, Any]) -> dict[str, Any]:
    schema = require_object(document.get("schema"), "summary.schema")
    if schema != {"name": SUMMARY_SCHEMA_NAME, "version": SUMMARY_SCHEMA_VERSION}:
        raise Phase4Error(f"unsupported summary schema: {schema!r}")
    require_object(document.get("identity"), "summary.identity")
    if not isinstance(document.get("runs"), list) or not isinstance(
        document.get("pairs"), list
    ):
        raise Phase4Error("summary runs and pairs must be arrays")
    for index, pair in enumerate(document["pairs"]):
        require_object(pair, f"summary.pairs[{index}]")
        stable_pair_key(pair)
    return document


def read_summary(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            document = json.load(stream)
    except (OSError, json.JSONDecodeError) as error:
        raise Phase4Error(f"could not read summary '{path}': {error}") from error
    return validate_summary(require_object(document, "summary"))


def merge_summaries(documents: list[dict[str, Any]]) -> dict[str, Any]:
    if not documents:
        raise Phase4Error("no summaries were supplied")
    expected = documents[0]["identity"]["expected_image_sha256"]
    seen_run_ids: set[str] = set()
    seen_raw_hashes: set[str] = set()
    runs: list[dict[str, Any]] = []
    quarantine: list[dict[str, Any]] = []
    aggregate: dict[tuple[Any, ...], dict[str, Any]] = {}
    overflow_count = 0

    for document in documents:
        if document["identity"]["expected_image_sha256"] != expected:
            raise Phase4Error("summary image identities disagree")
        for run in document["runs"]:
            run_id = run["run_id"]
            raw_hash = run["raw_sha256"]
            if run_id in seen_run_ids:
                raise Phase4Error(f"duplicate run ID while merging summaries: {run_id}")
            if raw_hash in seen_raw_hashes:
                raise Phase4Error(f"duplicate raw trace while merging summaries: {raw_hash}")
            seen_run_ids.add(run_id)
            seen_raw_hashes.add(raw_hash)
            runs.append(run)
        quarantine.extend(document.get("quarantine", []))
        for pair in document["pairs"]:
            key = stable_pair_key(pair)
            if key not in aggregate:
                aggregate[key] = json.loads(json.dumps(pair))
                continue
            item = aggregate[key]
            item["hit_count"], overflow = saturating_add(
                item["hit_count"], pair["hit_count"]
            )
            overflow_count += int(overflow)
            for run_id, hit_count in pair["run_hit_counts"].items():
                if run_id in item["run_hit_counts"]:
                    raise Phase4Error(
                        f"pair contains duplicate run accounting for {run_id}"
                    )
                item["run_hit_counts"][run_id] = hit_count
            item["observed_runs"] = sorted(
                set(item["observed_runs"]) | set(pair["observed_runs"])
            )
            threads = {
                (thread["run_id"], thread["thread_key"]): thread
                for thread in item["thread_observations"]
            }
            for thread in pair["thread_observations"]:
                key_thread = (thread["run_id"], thread["thread_key"])
                if key_thread not in threads:
                    threads[key_thread] = thread
                else:
                    existing = threads[key_thread]
                    existing["first_sequence"] = min(
                        existing["first_sequence"], thread["first_sequence"]
                    )
                    existing["last_sequence"] = max(
                        existing["last_sequence"], thread["last_sequence"]
                    )
                    existing["hit_count"], overflow = saturating_add(
                        existing["hit_count"], thread["hit_count"]
                    )
                    overflow_count += int(overflow)
            item["thread_observations"] = [threads[key] for key in sorted(threads)]
            item["target_validity"] = sorted(
                set(item["target_validity"]) | set(pair["target_validity"])
            )

    pairs = sorted(aggregate.values(), key=stable_pair_key)
    runs.sort(key=lambda item: (item["run_id"], item["raw_sha256"]))
    quarantine.sort(key=lambda item: (item.get("kind", ""), item.get("run_id", "")))
    total_hits = 0
    dropped_hits = 0
    io_errors = 0
    aggregate_limit_exceeded = 0
    count_overflows = overflow_count
    for run in runs:
        if not run["identity_match"]:
            continue
        total_hits, overflow = saturating_add(total_hits, run["counters"]["total_hits"])
        count_overflows += int(overflow)
        dropped_hits, overflow = saturating_add(
            dropped_hits, run["counters"]["dropped_hits"]
        )
        count_overflows += int(overflow)
        io_errors, overflow = saturating_add(io_errors, run["counters"]["io_errors"])
        count_overflows += int(overflow)
        aggregate_limit_exceeded, overflow = saturating_add(
            aggregate_limit_exceeded,
            run["counters"].get("aggregate_limit_exceeded", 0),
        )
        count_overflows += int(overflow)
        count_overflows, _ = saturating_add(
            count_overflows, run["counters"]["count_overflows"]
        )

    return {
        "schema": {"name": SUMMARY_SCHEMA_NAME, "version": SUMMARY_SCHEMA_VERSION},
        "tool": {"name": "Fable2IndirectTargets", "version": TOOL_VERSION},
        "identity": documents[0]["identity"],
        "counts": {
            "accepted_runs": sum(run["identity_match"] for run in runs),
            "quarantined_runs": len(quarantine),
            "unique_pairs": len(pairs),
            "total_hits": total_hits,
            "dropped_hits": dropped_hits,
            "io_errors": io_errors,
            "count_overflows": count_overflows,
            "aggregate_limit_exceeded": aggregate_limit_exceeded,
            "abnormal_or_truncated_runs": sum(
                run["flush_status"] != "normal"
                for run in runs
                if run["identity_match"]
            ),
        },
        "runs": runs,
        "quarantine": quarantine,
        "pairs": pairs,
        "determinism": documents[0]["determinism"],
    }


def write_summary_csv(path: Path, summary: dict[str, Any]) -> None:
    rows: list[list[str]] = []
    for pair in summary["pairs"]:
        rows.append(
            [
                pair["source_module"],
                pair["source"],
                pair["target_module"],
                pair["target"],
                pair["branch_kind"],
                str(pair["link"]).lower(),
                str(pair["ordinary_return"]).lower(),
                str(pair["hit_count"]),
                ";".join(pair["observed_runs"]),
                ";".join(
                    f'{observation["run_id"]}:{observation["thread_key"]}'
                    for observation in pair["thread_observations"]
                ),
                ";".join(pair["target_validity"]),
            ]
        )
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with temporary.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(
                [
                    "source_module",
                    "source",
                    "target_module",
                    "target",
                    "branch_kind",
                    "link",
                    "ordinary_return",
                    "hit_count",
                    "observed_runs",
                    "thread_keys",
                    "target_validity",
                ]
            )
            writer.writerows(rows)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def executable_ranges(contract: dict[str, Any]) -> list[tuple[int, int, str]]:
    result = []
    for item in contract["expected_image_identity"].get("executable_sections", []):
        result.append(
            (
                address(item["start"], "executable section start"),
                address(item["end"], "executable section end"),
                item["name"],
            )
        )
    return sorted(result)


def contains_range(ranges: Iterable[tuple[int, int, str]], value: int) -> bool:
    return any(start <= value < end for start, end, _ in ranges)


def load_generated_registrations(path: Path | None) -> dict[int, str]:
    if path is None or not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        int(match.group(1), 16): match.group(2)
        for match in re.finditer(
            r"\{\s*0x([0-9A-Fa-f]{8})\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}",
            text,
        )
    }


def load_closure_indices(path: Path) -> dict[str, Any]:
    try:
        document = function_map.read_json(path)
    except function_map.MapValidationError as error:
        raise Phase4Error(str(error)) from error
    ranges: dict[int, dict[str, Any]] = {}
    exception_entries: dict[int, int] = {}
    labels: dict[int, int] = {}
    for item in document.get("function_ranges", []):
        value = item["range"]
        start = address(value["start"], "closure range start")
        end = address(value["end"], "closure range end")
        record = {
            "start": start,
            "end": end,
            "size": end - start,
            "authority": item.get("authority"),
            "boundary_provenance": item.get("boundary_provenance", []),
            "trusted": bool(item.get("trusted")),
            "preliminary": bool(item.get("preliminary")),
            "manifest": bool(item.get("manifest")),
            "exception_function": bool(item.get("exception_function")),
            "basic_blocks": item.get("basic_blocks", []),
        }
        ranges[start] = record
        for entry in item.get("exception_entries", []):
            exception_entries[address(entry, "closure exception entry")] = start
        for label in item.get("labels", []):
            labels[address(label, "closure label")] = start

    candidates: dict[int, dict[str, Any]] = {}
    for item in document.get("candidates", []):
        candidates[address(item["address"], "closure candidate")] = item

    jump_cases: dict[int, list[dict[str, Any]]] = defaultdict(list)
    callable_cases = {
        address(case, "callable jump case")
        for effect in document.get("jump_table_recovery", {}).get(
            "boundary_effects", []
        )
        for case in effect.get("independently_callable_cases", [])
    }
    for site in document.get("jump_table_recovery", {}).get("indirect_sites", []):
        table = site.get("selected_table")
        if not table:
            continue
        for target_text in table.get("targets", []):
            target = address(target_text, "jump-table target")
            jump_cases[target].append(
                {
                    "dispatch": site["site"],
                    "owner_address": site["owner_address"],
                    "table_kind": table.get("kind"),
                    "table_address": table.get("table_address"),
                    "origin": table.get("origin"),
                    "confidence": table.get("confidence"),
                    "independently_callable": target in callable_cases,
                }
            )

    result = {
        "schema_version": document.get("schema_version"),
        "analyzer_version": document.get("analyzer_version"),
        "image_identity": document.get("image_identity"),
        "ranges": ranges,
        "starts": sorted(ranges),
        "candidates": candidates,
        "jump_cases": dict(jump_cases),
        "exception_entries": exception_entries,
        "labels": labels,
        "sha256": sha256_file(path),
        "file_name": path.name,
    }
    del document
    gc.collect()
    return result


def load_ghidra_indices(
    paths: list[Path], contract: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[int, list[dict[str, Any]]], dict[int, list[dict[str, Any]]]]:
    sources: list[dict[str, Any]] = []
    functions: dict[int, list[dict[str, Any]]] = defaultdict(list)
    internal_entries: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for path in paths:
        try:
            document = function_map.validate_map(function_map.read_json(path))
            identity = function_map.assess_identity(document, contract)
        except function_map.MapValidationError as error:
            raise Phase4Error(str(error)) from error
        source = {
            "file_name": path.name,
            "sha256": sha256_file(path),
            "artifact_id": document["source_artifact"]["id"],
            "identity_state": identity["state"],
            "automatic_tu1_use_allowed": identity["automatic_tu1_use_allowed"],
            "function_count": len(document["functions"]),
        }
        sources.append(source)
        for item in document["functions"]:
            entry = address(item["entry"], "Ghidra function entry")
            functions[entry].append(
                {
                    "source": source,
                    "body_ranges": item["body_ranges"],
                    "body_size": item["body_size"],
                    "contiguous_body": item["contiguous_body"],
                    "pdata_records": item.get("pdata_records", []),
                    "inbound_references": item.get("inbound_references", []),
                    "overlapping_function_entries": item.get(
                        "overlapping_function_entries", []
                    ),
                    "other_function_entries_in_body": item.get(
                        "other_function_entries_in_body", []
                    ),
                }
            )
            for label in item.get("callable_internal_labels", []):
                internal_entries[address(label["address"], "Ghidra internal entry")].append(
                    {
                        "owner_address": item["entry"],
                        "label": label,
                        "source": source,
                    }
                )
        del document
        gc.collect()
    sources.sort(key=lambda item: (item["identity_state"], item["artifact_id"]))
    return sources, dict(functions), dict(internal_entries)


def containing_range(
    value: int, ranges: dict[int, dict[str, Any]], starts: list[int]
) -> dict[str, Any] | None:
    index = bisect.bisect_right(starts, value) - 1
    if index < 0:
        return None
    candidate = ranges[starts[index]]
    return candidate if candidate["start"] <= value < candidate["end"] else None


def proposed_range_from_candidate(candidate: dict[str, Any] | None) -> tuple[int, int] | None:
    if not candidate or not candidate.get("proposed_range"):
        return None
    value = candidate["proposed_range"]
    return (
        address(value["start"], "candidate range start"),
        address(value["end"], "candidate range end"),
    )


def runtime_evidence(contract: dict[str, Any]) -> dict[int, dict[str, Any]]:
    result = {}
    for item in contract.get("runtime_indirect_evidence", {}).get("observations", []):
        result[address(item["target"], "runtime evidence target")] = item
    return result


def manual_evidence(contract: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {
        address(item["address"], "manual evidence address"): item
        for item in contract.get("manual_evidence", [])
    }


def group_target_observations(summary: dict[str, Any]) -> tuple[dict[int, list[dict[str, Any]]], list[dict[str, Any]]]:
    targets: dict[int, list[dict[str, Any]]] = defaultdict(list)
    ignored_returns: list[dict[str, Any]] = []
    for pair in summary["pairs"]:
        if pair["branch_kind"] == "blr" or pair.get("ordinary_return"):
            ignored_returns.append(
                {
                    "source": pair["source"],
                    "target": pair["target"],
                    "hit_count": pair["hit_count"],
                    "observed_runs": pair["observed_runs"],
                    "reason": "ordinary_blr_excluded_from_manifest_candidates",
                }
            )
            continue
        targets[address(pair["target"], "summary target")].append(pair)
    ignored_returns.sort(key=lambda item: (item["source"], item["target"]))
    return dict(targets), ignored_returns


def candidate_identifier(target: int, classification: str, proposal: Any) -> str:
    identity = {
        "target": address_text(target),
        "classification": classification,
        "proposal": proposal,
    }
    return "P4-" + sha256_bytes(canonical_json_bytes(identity))[:16]


def classify_target(
    target: int,
    observations: list[dict[str, Any]],
    manifest: dict[int, dict[str, Any]],
    generated: dict[int, str],
    closure: dict[str, Any],
    ghidra_functions: dict[int, list[dict[str, Any]]],
    ghidra_internal: dict[int, list[dict[str, Any]]],
    runtime_known: dict[int, dict[str, Any]],
    manual_known: dict[int, dict[str, Any]],
    executable: list[tuple[int, int, str]],
    title_module_names: set[str],
) -> dict[str, Any]:
    sources = sorted({pair["source"] for pair in observations})
    branch_kinds = sorted({pair["branch_kind"] for pair in observations})
    runs = sorted({run for pair in observations for run in pair["observed_runs"]})
    hit_count = 0
    hit_overflow = False
    for pair in observations:
        hit_count, overflow = saturating_add(hit_count, pair["hit_count"])
        hit_overflow |= overflow

    evidence: list[dict[str, Any]] = [
        {
            "kind": "xenia_runtime_indirect_target",
            "conclusion": "address executed as a resolved guest control-flow target",
            "source_sites": sources,
            "branch_kinds": branch_kinds,
            "observed_runs": runs,
            "hit_count": hit_count,
            "hit_count_saturated": hit_overflow,
        }
    ]
    conflicts: list[str] = []
    rejection_reasons: list[str] = []
    ownership: dict[str, Any] | None = None
    size_candidates: list[dict[str, Any]] = []
    automatic_allowed = False
    proposal: dict[str, Any] | None = None

    valid_alignment = target % 4 == 0
    in_executable = contains_range(executable, target)
    known_external_module = any(
        pair["target_module"] != "unknown"
        and pair["target_module"] not in title_module_names
        for pair in observations
    )

    containing_manifest = next(
        (
            item
            for entry, item in manifest.items()
            if entry < target
            < address(item["range"]["end"], "manifest range end")
        ),
        None,
    )
    owner_range = containing_range(target, closure["ranges"], closure["starts"])
    exact_range = closure["ranges"].get(target)
    closure_candidate = closure["candidates"].get(target)
    jump_case = closure["jump_cases"].get(target)
    exception_owner = closure["exception_entries"].get(target)
    known_runtime = runtime_known.get(target)
    generated_symbol = generated.get(target)
    internal_records = ghidra_internal.get(target, [])
    exact_internal_records = [
        item
        for item in internal_records
        if item["source"]["automatic_tu1_use_allowed"]
    ]
    related_internal_records = [
        item
        for item in internal_records
        if not item["source"]["automatic_tu1_use_allowed"]
    ]

    if not valid_alignment:
        classification = "invalid_or_non_executable_target"
        confidence = "CONFIRMED"
        rejection_reasons.append("target_is_not_four_byte_aligned")
    elif generated_symbol and generated_symbol.startswith("__imp__"):
        classification = "known_import_or_kernel_target"
        confidence = "CONFIRMED"
        evidence.append(
            {
                "kind": "generated_import_registration",
                "address": address_text(target),
                "symbol": generated_symbol,
            }
        )
        rejection_reasons.append("generated_import_registration_no_manifest_change")
    elif known_external_module and not in_executable:
        classification = "known_import_or_kernel_target"
        confidence = "CONFIRMED"
        evidence.append(
            {
                "kind": "cross_module_runtime_transfer",
                "target_modules": sorted(
                    {pair["target_module"] for pair in observations}
                ),
            }
        )
        rejection_reasons.append("target_is_outside_fable_executable_ranges")
    elif not in_executable:
        classification = "invalid_or_non_executable_target"
        confidence = "CONFIRMED"
        rejection_reasons.append("target_is_outside_known_executable_ranges")
    elif target in manifest or generated_symbol:
        classification = "existing_manifest_function"
        confidence = "CONFIRMED"
        evidence.append(
            {
                "kind": "existing_effective_registration",
                "canonical_manifest_override": target in manifest,
                "current_generated_registration": bool(generated_symbol),
                "generated_symbol": generated_symbol,
                "manifest": manifest.get(target),
            }
        )
        if target in manual_known:
            evidence.append(
                {
                    "kind": "shared_manual_or_fault_walker_evidence",
                    "record": manual_known[target],
                }
            )
        rejection_reasons.append("already_registered_no_manifest_change")
    elif known_runtime and known_runtime.get("classification") == "known_jump_table_case":
        classification = "known_jump_table_case"
        confidence = known_runtime.get("evidence_level", "CONFIRMED")
        owner = address(known_runtime["owner_address"], "runtime owner")
        ownership = {
            "owner_address": address_text(owner),
            "kind": "internal_switch_case",
            "manifest_policy": known_runtime.get("manifest_policy"),
        }
        evidence.append({"kind": "retained_runtime_manual_evidence", **known_runtime})
        rejection_reasons.append("owned_switch_case_not_a_standalone_function")
    elif jump_case and not any(item["independently_callable"] for item in jump_case):
        classification = "known_jump_table_case"
        confidence = "CONFIRMED"
        ownership = {
            "owner_address": jump_case[0]["owner_address"],
            "kind": "recovered_jump_table_case",
        }
        evidence.append({"kind": "phase3_jump_table_ownership", "records": jump_case})
        rejection_reasons.append("owned_switch_case_not_a_standalone_function")
    elif exception_owner is not None:
        classification = "known_exception_landing_pad"
        confidence = "CONFIRMED"
        ownership = {
            "owner_address": address_text(exception_owner),
            "kind": "pdata_exception_entry",
        }
        evidence.append(
            {
                "kind": "phase1_exception_entry",
                "owner_address": address_text(exception_owner),
            }
        )
        rejection_reasons.append("exception_landing_pad_not_a_standalone_function")
    elif exact_internal_records:
        classification = "existing_function_internal_entry"
        confidence = "PROBABLE"
        ownership = {
            "kind": "ghidra_callable_internal_label",
            "records": exact_internal_records,
        }
        evidence.append(
            {"kind": "ghidra_callable_internal_entry", "records": exact_internal_records}
        )
        if related_internal_records:
            evidence.append(
                {
                    "kind": "related_build_ghidra_internal_entry_quarantined",
                    "records": related_internal_records,
                    "may_authorize_tu1_ownership": False,
                }
            )
        rejection_reasons.append("target_is_an_internal_entry")
    elif (owner_range and owner_range["start"] != target) or containing_manifest:
        classification = "existing_function_internal_entry"
        confidence = "CONFIRMED" if owner_range and owner_range["trusted"] else "PROBABLE"
        owner_start = (
            owner_range["start"]
            if owner_range
            else address(containing_manifest["range"]["start"], "manifest owner")
        )
        ownership = {
            "owner_address": address_text(owner_start),
            "kind": "known_function_range_internal_entry",
        }
        evidence.append(
            {
                "kind": "known_function_ownership",
                "owner_range": (
                    {
                        "start": address_text(owner_range["start"]),
                        "end": address_text(owner_range["end"]),
                        "authority": owner_range["authority"],
                        "trusted": owner_range["trusted"],
                    }
                    if owner_range
                    else containing_manifest["range"]
                ),
            }
        )
        rejection_reasons.append("target_is_inside_an_existing_function")
    else:
        if related_internal_records:
            evidence.append(
                {
                    "kind": "related_build_ghidra_internal_entry_quarantined",
                    "records": related_internal_records,
                    "may_authorize_tu1_ownership": False,
                }
            )
        if exact_range:
            evidence.append(
                {
                    "kind": "phase1_exact_function_range",
                    "range": {
                        "start": address_text(exact_range["start"]),
                        "end": address_text(exact_range["end"]),
                        "size": address_text(exact_range["size"]),
                    },
                    "authority": exact_range["authority"],
                    "boundary_provenance": exact_range["boundary_provenance"],
                    "trusted": exact_range["trusted"],
                }
            )
            if exact_range["trusted"] and not exact_range["preliminary"]:
                size_candidates.append(
                    {
                        "start": target,
                        "end": exact_range["end"],
                        "size": exact_range["size"],
                        "source": "exact_tu1_closure_range",
                        "authority": exact_range["authority"],
                    }
                )
        candidate_range = proposed_range_from_candidate(closure_candidate)
        if closure_candidate:
            evidence.append(
                {
                    "kind": "phase1_entrypoint_candidate",
                    "classification": closure_candidate.get("classification"),
                    "confidence": closure_candidate.get("confidence"),
                    "boundary_provenance": closure_candidate.get(
                        "boundary_provenance", []
                    ),
                    "conflicts": closure_candidate.get("conflicts", []),
                    "rejection_reasons": closure_candidate.get(
                        "rejection_reasons", []
                    ),
                }
            )
            conflicts.extend(closure_candidate.get("conflicts", []))
            if candidate_range and not closure_candidate.get("conflicts"):
                size_candidates.append(
                    {
                        "start": candidate_range[0],
                        "end": candidate_range[1],
                        "size": candidate_range[1] - candidate_range[0],
                        "source": "phase1_candidate_proposed_range",
                        "authority": closure_candidate.get("confidence"),
                    }
                )

        exact_ghidra = []
        related_ghidra = []
        for item in ghidra_functions.get(target, []):
            (exact_ghidra if item["source"]["automatic_tu1_use_allowed"] else related_ghidra).append(item)
        if exact_ghidra:
            evidence.append({"kind": "exact_image_ghidra", "records": exact_ghidra})
            for item in exact_ghidra:
                if item["contiguous_body"] and len(item["body_ranges"]) == 1:
                    body = item["body_ranges"][0]
                    start = address(body["start"], "Ghidra body start")
                    end = address(body["end"], "Ghidra body end")
                    if start == target:
                        size_candidates.append(
                            {
                                "start": start,
                                "end": end,
                                "size": end - start,
                                "source": "exact_image_ghidra_body",
                                "authority": (
                                    "pdata_associated"
                                    if item["pdata_records"]
                                    else "analyzer_body"
                                ),
                            }
                        )
        if related_ghidra:
            evidence.append(
                {
                    "kind": "related_build_ghidra_quarantined",
                    "records": related_ghidra,
                    "may_authorize_tu1_size": False,
                }
            )

        distinct_ranges = sorted({(item["start"], item["end"]) for item in size_candidates})
        if len(distinct_ranges) > 1:
            classification = "conflicting_range"
            confidence = "CONFIRMED"
            conflicts.append(
                "independent exact boundary sources disagree: "
                + ", ".join(
                    f"[{address_text(start)},{address_text(end)})"
                    for start, end in distinct_ranges
                )
            )
            rejection_reasons.append("size_sources_disagree")
        else:
            candidate_class = str(
                (closure_candidate or {}).get("classification") or ""
            ).lower()
            candidate_confidence = str(
                (closure_candidate or {}).get("confidence") or ""
            ).lower()
            has_exact_pdata = any(
                item.get("authority") in {"pdata", "pdata_associated"}
                or "pdata" in str(item.get("authority", ""))
                for item in size_candidates
            )
            strong_static = bool(
                exact_range
                and exact_range["trusted"]
                and not exact_range["preliminary"]
            ) or has_exact_pdata or "strong" in candidate_class or "strong" in candidate_confidence
            probable_static = bool(size_candidates) or "probable" in candidate_class or "probable" in candidate_confidence
            if strong_static:
                classification = "strong_new_function"
                confidence = "CONFIRMED" if has_exact_pdata else "PROBABLE"
            elif probable_static:
                classification = "probable_new_function"
                confidence = "PROBABLE"
            else:
                classification = "ambiguous_target"
                confidence = "HYPOTHESIS"
                rejection_reasons.append("runtime_observation_does_not_establish_boundary")

            if distinct_ranges:
                start, end = distinct_ranges[0]
                proposal = {
                    "entry": address_text(start),
                    "end": address_text(end),
                    "size": address_text(end - start),
                    "size_value": end - start,
                    "size_provenance": [
                        {
                            key: (address_text(value) if key in {"start", "end"} else value)
                            for key, value in item.items()
                        }
                        for item in size_candidates
                        if (item["start"], item["end"]) == (start, end)
                    ],
                }
            else:
                rejection_reasons.append("no_independent_exact_size_evidence")

            if proposal:
                proposal_start = address(proposal["entry"], "proposal entry")
                proposal_end = address(proposal["end"], "proposal end")
                manifest_overlaps = [
                    {
                        "start": address_text(entry),
                        "end": item["range"]["end"],
                    }
                    for entry, item in manifest.items()
                    if proposal_start
                    < address(item["range"]["end"], "manifest range end")
                    and entry < proposal_end
                ]
                if manifest_overlaps:
                    classification = "conflicting_range"
                    confidence = "CONFIRMED"
                    conflicts.append(
                        "proposed range overlaps existing manifest ranges: "
                        + ", ".join(
                            f"[{item['start']},{item['end']})"
                            for item in manifest_overlaps
                        )
                    )
                    rejection_reasons.append("proposal_overlaps_existing_manifest")

            only_ctr = set(branch_kinds) == {"bctr"}
            automatic_allowed = bool(
                classification == "strong_new_function"
                and proposal
                and not conflicts
                and (has_exact_pdata or not only_ctr)
            )
            if only_ctr and not has_exact_pdata:
                rejection_reasons.append(
                    "bctr_only_observation_requires_stronger_switch_vs_tail_review"
                )

    if classification not in CLASSIFICATIONS:
        raise AssertionError(f"unknown classification {classification}")
    record = {
        "target": address_text(target),
        "classification": classification,
        "confidence": confidence,
        "runtime": {
            "source_sites": sources,
            "branch_kinds": branch_kinds,
            "observed_runs": runs,
            "hit_count": hit_count,
            "observations": observations,
        },
        "ownership": ownership,
        "evidence": evidence,
        "conflicts": sorted(set(conflicts)),
        "rejection_reasons": sorted(set(rejection_reasons)),
        "proposal": proposal,
        "automatic_application_permitted": automatic_allowed,
    }
    record["candidate_id"] = candidate_identifier(target, classification, proposal)
    return record


def build_plan(
    summary: dict[str, Any],
    summary_path: Path,
    manifest_path: Path,
    closure_path: Path,
    evidence_path: Path,
    generated_init: Path | None,
    ghidra_paths: list[Path],
) -> dict[str, Any]:
    validate_summary(summary)
    try:
        contract = function_map.load_contract(evidence_path)
        manifest = function_map.load_manifest(manifest_path)
    except function_map.MapValidationError as error:
        raise Phase4Error(str(error)) from error

    expected_image = contract["expected_image_identity"]["patched_image_sha256"].upper()
    if summary["identity"]["expected_image_sha256"].upper() != expected_image:
        raise Phase4Error(
            "summary image identity does not match the canonical shared evidence contract"
        )
    closure = load_closure_indices(closure_path)
    closure_image = str(closure["image_identity"].get("patched_image_sha256", "")).upper()
    if closure_image != expected_image:
        raise Phase4Error("closure report image identity does not match the trace")

    generated = load_generated_registrations(generated_init)
    ghidra_sources, ghidra_functions, ghidra_internal = load_ghidra_indices(
        ghidra_paths, contract
    )
    target_groups, ignored_returns = group_target_observations(summary)
    executable = executable_ranges(contract)
    runtime_known = runtime_evidence(contract)
    manual_known = manual_evidence(contract)
    title_module_names = {
        module["name"]
        for run in summary["runs"]
        if run.get("identity_match", True)
        for module in run.get("modules", [])
        if module.get("title_module")
    }
    targets = [
        classify_target(
            target,
            target_groups[target],
            manifest,
            generated,
            closure,
            ghidra_functions,
            ghidra_internal,
            runtime_known,
            manual_known,
            executable,
            title_module_names,
        )
        for target in sorted(target_groups)
    ]

    ranged_targets = [item for item in targets if item["proposal"]]
    for left_index, left in enumerate(ranged_targets):
        left_start = address(left["proposal"]["entry"], "left proposal entry")
        left_end = address(left["proposal"]["end"], "left proposal end")
        for right in ranged_targets[left_index + 1 :]:
            right_start = address(right["proposal"]["entry"], "right proposal entry")
            right_end = address(right["proposal"]["end"], "right proposal end")
            if left_start < right_end and right_start < left_end:
                for item, other in ((left, right), (right, left)):
                    item["classification"] = "conflicting_range"
                    item["confidence"] = "CONFIRMED"
                    item["automatic_application_permitted"] = False
                    item["conflicts"] = sorted(
                        set(item["conflicts"])
                        | {
                            "proposed range overlaps observed candidate "
                            f"{other['target']} {other['proposal']['entry']}–"
                            f"{other['proposal']['end']}"
                        }
                    )
                    item["rejection_reasons"] = sorted(
                        set(item["rejection_reasons"])
                        | {"proposal_overlaps_another_observed_candidate"}
                    )
                    item["candidate_id"] = candidate_identifier(
                        address(item["target"], "overlapping proposal target"),
                        item["classification"],
                        item["proposal"],
                    )

    by_classification = Counter(item["classification"] for item in targets)
    proposals = [item for item in targets if item["proposal"]]
    fixture_results: list[dict[str, Any]] = []
    by_target = {item["target"]: item for item in targets}
    for fixture in contract.get("acceptance_fixtures", []):
        result = by_target.get(fixture["address"])
        fixture_results.append(
            {
                "address": fixture["address"],
                "expected_size": fixture["size"],
                "expected_classification": "existing_manifest_function",
                "actual_classification": result["classification"] if result else None,
                "manifest_change": bool(result and result["proposal"]),
                "passed": bool(
                    result
                    and result["classification"] == "existing_manifest_function"
                    and not result["proposal"]
                ),
            }
        )
    for target, evidence_item in sorted(runtime_known.items()):
        result = by_target.get(address_text(target))
        expected_owner = evidence_item.get(
            "acceptance_expected_owner_address", evidence_item["owner_address"]
        )
        expected_classification = evidence_item.get(
            "acceptance_expected_classification",
            evidence_item["classification"],
        )
        expected_runtime_sources = sorted(
            evidence_item.get(
                "acceptance_runtime_dispatch_sites",
                # Schema-1 contracts used source_sites for both concepts. Keep
                # them readable, while schema 2 makes the provenance explicit.
                evidence_item.get("source_sites", []),
            )
        )
        historical_sources = sorted(
            evidence_item.get(
                "historical_corroborating_source_sites",
                evidence_item.get("source_sites", []),
            )
        )
        observed_runtime_sources = (
            result["runtime"]["source_sites"] if result else []
        )
        retained_record = next(
            (
                item
                for item in (result or {}).get("evidence", [])
                if item.get("kind") == "retained_runtime_manual_evidence"
            ),
            {},
        )
        retained_historical_sources = sorted(
            retained_record.get(
                "historical_corroborating_source_sites",
                retained_record.get("source_sites", []),
            )
        )
        fixture_results.append(
            {
                "address": address_text(target),
                "expected_owner": expected_owner,
                "expected_runtime_dispatch_sites": expected_runtime_sources,
                "observed_runtime_dispatch_sites": observed_runtime_sources,
                "expected_historical_corroborating_source_sites": (
                    historical_sources
                ),
                "retained_historical_corroborating_source_sites": (
                    retained_historical_sources
                ),
                "expected_classification": expected_classification,
                "actual_classification": result["classification"] if result else None,
                "manifest_change": bool(result and result["proposal"]),
                "passed": bool(
                    result
                    and evidence_item["classification"]
                    == expected_classification
                    and evidence_item["owner_address"] == expected_owner
                    and result["classification"] == expected_classification
                    and result["ownership"]
                    and result["ownership"]["owner_address"]
                    == expected_owner
                    and set(expected_runtime_sources).issubset(
                        observed_runtime_sources
                    )
                    and retained_historical_sources == historical_sources
                    and not result["proposal"]
                ),
            }
        )

    manifest_bytes = manifest_path.read_bytes()
    inputs = {
        "summary": {
            "file_name": summary_path.name,
            "sha256": sha256_file(summary_path),
            "run_ids": [run["run_id"] for run in summary["runs"]],
            "raw_trace_sha256": [run["raw_sha256"] for run in summary["runs"]],
        },
        "manifest": {
            "file_name": manifest_path.name,
            "sha256": sha256_bytes(manifest_bytes),
            "function_count": len(manifest),
        },
        "closure": {
            "file_name": closure["file_name"],
            "sha256": closure["sha256"],
            "schema_version": closure["schema_version"],
            "analyzer_version": closure["analyzer_version"],
        },
        "shared_evidence": {
            "file_name": evidence_path.name,
            "sha256": sha256_file(evidence_path),
            "schema_version": contract["schema_version"],
        },
        "generated_registration": {
            "file_name": generated_init.name if generated_init else None,
            "sha256": sha256_file(generated_init) if generated_init and generated_init.exists() else None,
            "registration_count": len(generated),
            "recompiled_function_count": sum(
                symbol.startswith("sub_") for symbol in generated.values()
            ),
            "import_count": sum(
                symbol.startswith("__imp__") for symbol in generated.values()
            ),
            "runtime_helper_count": sum(
                not symbol.startswith(("sub_", "__imp__"))
                for symbol in generated.values()
            ),
        },
        "ghidra_maps": ghidra_sources,
    }
    plan: dict[str, Any] = {
        "schema": {"name": PLAN_SCHEMA_NAME, "version": PLAN_SCHEMA_VERSION},
        "tool": {"name": "Fable2IndirectTargets", "version": TOOL_VERSION},
        "mode": "dry_run",
        "inputs": inputs,
        "counts": {
            "observed_non_return_targets": len(targets),
            "ignored_ordinary_returns": len(ignored_returns),
            "by_classification": dict(sorted(by_classification.items())),
            "range_proposals": len(proposals),
            "automatically_applicable_after_review": sum(
                item["automatic_application_permitted"] for item in proposals
            ),
            "ambiguous": by_classification["ambiguous_target"],
            "rejected_no_op": sum(
                item["classification"]
                in {
                    "existing_manifest_function",
                    "existing_function_internal_entry",
                    "known_jump_table_case",
                    "known_exception_landing_pad",
                    "known_import_or_kernel_target",
                    "invalid_or_non_executable_target",
                }
                for item in targets
            ),
            "conflicting": by_classification["conflicting_range"],
        },
        "fixture_results": fixture_results,
        "ignored_ordinary_returns": ignored_returns,
        "targets": targets,
        "proposals": [
            {
                "candidate_id": item["candidate_id"],
                "target": item["target"],
                "classification": item["classification"],
                "confidence": item["confidence"],
                "proposal": item["proposal"],
                "evidence": item["evidence"],
                "runtime": item["runtime"],
                "conflicts": item["conflicts"],
                "rejection_reasons": item["rejection_reasons"],
                "automatic_application_permitted": item[
                    "automatic_application_permitted"
                ],
            }
            for item in proposals
        ],
        "safety": {
            "canonical_manifest_modified": False,
            "dry_run_is_default": True,
            "explicit_apply_flag_required": True,
            "reviewed_candidate_selection_required": True,
            "stale_manifest_rejected": True,
            "atomic_replace": True,
            "placeholder_implementations_supported": False,
            "runtime_observation_establishes_size": False,
            "related_build_evidence_can_authorize_tu1_edit": False,
            "switch_cases_are_functions_by_default": False,
        },
    }
    plan["plan_id"] = "P4PLAN-" + sha256_bytes(canonical_json_bytes(plan))[:20]
    return plan


def validate_plan(document: dict[str, Any]) -> dict[str, Any]:
    schema = require_object(document.get("schema"), "plan.schema")
    if schema != {"name": PLAN_SCHEMA_NAME, "version": PLAN_SCHEMA_VERSION}:
        raise Phase4Error(f"unsupported plan schema: {schema!r}")
    require_string(document.get("plan_id"), "plan.plan_id")
    if document.get("mode") != "dry_run":
        raise Phase4Error("only a dry-run review plan may be applied")
    if not isinstance(document.get("proposals"), list):
        raise Phase4Error("plan.proposals must be an array")
    unsigned = dict(document)
    supplied_plan_id = unsigned.pop("plan_id")
    expected_plan_id = "P4PLAN-" + sha256_bytes(canonical_json_bytes(unsigned))[:20]
    if supplied_plan_id != expected_plan_id:
        raise Phase4Error(
            f"plan integrity check failed: {supplied_plan_id!r} does not match "
            f"{expected_plan_id!r}"
        )
    candidate_ids: set[str] = set()
    for index, proposal in enumerate(document["proposals"]):
        proposal = require_object(proposal, f"plan.proposals[{index}]")
        candidate_id = require_string(
            proposal.get("candidate_id"), f"plan.proposals[{index}].candidate_id"
        )
        if candidate_id in candidate_ids:
            raise Phase4Error(f"plan has duplicate candidate ID {candidate_id}")
        candidate_ids.add(candidate_id)
    return document


def read_plan(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            document = json.load(stream)
    except (OSError, json.JSONDecodeError) as error:
        raise Phase4Error(f"could not read plan '{path}': {error}") from error
    return validate_plan(require_object(document, "plan"))


def render_manifest_additions(selected: list[dict[str, Any]], newline: str) -> str:
    lines = []
    for item in sorted(selected, key=lambda value: value["target"]):
        proposal = item["proposal"]
        size = proposal["size_value"]
        lines.append(
            f'"{item["target"]}" = {{ size = 0x{size:X} }} '
            f'# Phase 4 reviewed {item["candidate_id"]}'
        )
    return newline.join(lines) + newline


def insert_manifest_lines(original: bytes, additions: str) -> bytes:
    try:
        text = original.decode("utf-8")
    except UnicodeDecodeError as error:
        raise Phase4Error("manifest is not UTF-8") from error
    newline = "\r\n" if "\r\n" in text else "\n"
    marker = "[entrypoint.functions]"
    marker_index = text.find(marker)
    if marker_index < 0:
        raise Phase4Error("manifest has no [entrypoint.functions] table")
    table_content_start = marker_index + len(marker)
    next_section = re.search(r"(?m)^\[[^\r\n]+\]\s*$", text[table_content_start:])
    insert_at = (
        table_content_start + next_section.start() if next_section else len(text)
    )
    prefix = text[:insert_at]
    suffix = text[insert_at:]
    if prefix and not prefix.endswith(("\n", "\r")):
        prefix += newline
    if prefix and not prefix.endswith(newline * 2):
        prefix += newline
    rendered = additions
    if suffix and not rendered.endswith(newline * 2):
        rendered += newline
    return (prefix + rendered + suffix).encode("utf-8")


def apply_reviewed_plan(
    plan: dict[str, Any], manifest_path: Path, selected_ids: set[str]
) -> dict[str, Any]:
    if not selected_ids:
        raise Phase4Error("at least one reviewed candidate ID must be selected")
    proposals = {item["candidate_id"]: item for item in plan["proposals"]}
    unknown = selected_ids - proposals.keys()
    if unknown:
        raise Phase4Error(f"unknown candidate IDs: {', '.join(sorted(unknown))}")
    selected = [proposals[candidate_id] for candidate_id in sorted(selected_ids)]
    forbidden = [
        item["candidate_id"]
        for item in selected
        if not item.get("automatic_application_permitted")
    ]
    if forbidden:
        raise Phase4Error(
            "selected candidates are not permitted for guarded apply: "
            + ", ".join(forbidden)
        )

    original = manifest_path.read_bytes()
    try:
        current_manifest = function_map.load_manifest(manifest_path)
    except function_map.MapValidationError as error:
        raise Phase4Error(str(error)) from error

    all_already_applied = True
    for item in selected:
        target = address(item["target"], "selected target")
        expected_size = item["proposal"]["size_value"]
        existing = current_manifest.get(target)
        if existing:
            actual_size = address(existing["range"]["size"], "existing size")
            if actual_size != expected_size:
                raise Phase4Error(
                    f"manifest already has conflicting entry {item['target']}: "
                    f"0x{actual_size:X} vs planned 0x{expected_size:X}"
                )
        else:
            all_already_applied = False
    if all_already_applied:
        return {
            "status": "already_applied",
            "manifest_modified": False,
            "manifest_sha256": sha256_bytes(original),
            "selected": sorted(selected_ids),
        }

    expected_manifest_hash = plan["inputs"]["manifest"]["sha256"]
    actual_manifest_hash = sha256_bytes(original)
    if actual_manifest_hash != expected_manifest_hash:
        raise Phase4Error(
            "stale plan: manifest SHA-256 is "
            f"{actual_manifest_hash}, expected {expected_manifest_hash}"
        )

    additions = [
        item for item in selected if address(item["target"], "target") not in current_manifest
    ]
    occupied_ranges = [
        (
            entry,
            address(item["range"]["end"], "existing manifest end"),
        )
        for entry, item in current_manifest.items()
    ]
    for item in additions:
        start = address(item["target"], "proposal target")
        proposal_start = address(item["proposal"]["entry"], "proposal entry")
        end = address(item["proposal"]["end"], "proposal end")
        if start != proposal_start or end <= start:
            raise Phase4Error(
                f"proposal for {item['target']} has an invalid or mismatched range"
            )
        for existing_start, existing_end in occupied_ranges:
            if start < existing_end and existing_start < end:
                raise Phase4Error(
                    f"proposal [{address_text(start)},{address_text(end)}) overlaps "
                    f"manifest [{address_text(existing_start)},{address_text(existing_end)})"
                )
        occupied_ranges.append((start, end))

    newline = "\r\n" if b"\r\n" in original else "\n"
    rendered = render_manifest_additions(additions, newline)
    updated = insert_manifest_lines(original, rendered)
    backup_path = manifest_path.with_name(manifest_path.name + ".phase4.bak")
    atomic_write_bytes(backup_path, original)
    atomic_write_bytes(manifest_path, updated)
    return {
        "status": "applied",
        "manifest_modified": True,
        "manifest_sha256_before": actual_manifest_hash,
        "manifest_sha256_after": sha256_bytes(updated),
        "backup_path": str(backup_path),
        "selected": sorted(selected_ids),
        "added": [item["target"] for item in additions],
    }


def powershell_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def complete_game_media_type(game_path: Path) -> str:
    suffix = game_path.suffix.lower()
    if suffix in LOOSE_EXECUTABLE_SUFFIXES:
        raise Phase4Error(
            "standalone XEX/ELF launch targets are forbidden for the normal "
            "gameplay collector workflow; pass complete game media such as an "
            "ISO with --game-path and use --analysis-image-path for the base XEX"
        )
    media_type = COMPLETE_GAME_MEDIA_TYPES.get(suffix)
    if media_type is None:
        supported = ", ".join(sorted(COMPLETE_GAME_MEDIA_TYPES))
        raise Phase4Error(
            f"unsupported complete-game launch media extension {suffix!r}; "
            f"supported extensions are: {supported}"
        )
    return media_type


def preflight(
    xenia: Path,
    game_path: Path,
    analysis_image_path: Path,
    output: Path,
    run_id: str,
    label: str,
    evidence_path: Path,
    content_root: Path,
    storage_root: Path,
    title_update_package: Path | None = None,
) -> dict[str, Any]:
    if not xenia.is_file():
        raise Phase4Error(f"Xenia executable does not exist: {xenia}")
    if not game_path.is_file():
        raise Phase4Error(f"complete-game launch media does not exist: {game_path}")
    media_type = complete_game_media_type(game_path)
    if not analysis_image_path.is_file():
        raise Phase4Error(
            f"analysis base XEX does not exist: {analysis_image_path}"
        )
    if analysis_image_path.suffix.lower() != ".xex":
        raise Phase4Error(
            "analysis image path must name the base XEX used with the adjacent XEXP"
        )
    if output.exists():
        raise Phase4Error(f"collector output already exists: {output}")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", run_id):
        raise Phase4Error("run ID must contain only letters, digits, dot, dash, underscore")
    contract = function_map.load_contract(evidence_path)
    identity = contract["expected_image_identity"]
    base_hash = sha256_file(analysis_image_path)
    if base_hash != identity["base_xex_sha256"].upper():
        raise Phase4Error(
            f"analysis base XEX SHA-256 is {base_hash}, "
            f"expected {identity['base_xex_sha256']}"
        )
    patch_path = analysis_image_path.with_suffix(".xexp")
    if not patch_path.is_file():
        raise Phase4Error(f"extracted title-update XEXP does not exist: {patch_path}")
    patch_hash = sha256_file(patch_path)
    if patch_hash != identity["title_update_sha256"].upper():
        raise Phase4Error(
            f"title-update XEXP SHA-256 is {patch_hash}, "
            f"expected {identity['title_update_sha256']}"
        )

    content_root = content_root.resolve()
    if not content_root.is_dir():
        raise Phase4Error(f"Xenia content root does not exist: {content_root}")
    title_id = identity["title_id"].removeprefix("0x").upper()
    title_update_directory = (
        content_root / "0000000000000000" / title_id / "000B0000"
    )
    if not title_update_directory.is_dir():
        raise Phase4Error(
            f"Xenia title-update content directory does not exist: "
            f"{title_update_directory}"
        )
    expected_package = (
        title_update_directory / identity["title_update_container_file"]
    )
    supplied_package = (
        title_update_package.resolve()
        if title_update_package is not None
        else expected_package
    )
    try:
        supplied_package.relative_to(content_root)
    except ValueError as error:
        raise Phase4Error(
            "title-update package must be inside the configured content root"
        ) from error
    if supplied_package != expected_package:
        raise Phase4Error(
            f"title-update package must use Xenia's exact installer path: "
            f"{expected_package}"
        )
    if not supplied_package.is_file():
        raise Phase4Error(
            f"title-update STFS package does not exist: {supplied_package}"
        )
    package_hash = sha256_file(supplied_package)
    if package_hash != identity["title_update_container_sha256"].upper():
        raise Phase4Error(
            f"title-update STFS SHA-256 is {package_hash}, "
            f"expected {identity['title_update_container_sha256']}"
        )
    content_record = {
        "root": str(content_root),
        "title_update_directory": str(title_update_directory),
        "package": str(supplied_package),
        "package_sha256": package_hash,
        "package_layout_valid": True,
    }

    storage_root = storage_root.resolve()
    storage_root.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.NamedTemporaryFile(dir=storage_root, delete=True):
            pass
    except OSError as error:
        raise Phase4Error(f"Xenia storage root is not writable: {error}") from error
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, delete=True):
            pass
    except OSError as error:
        raise Phase4Error(f"collector output directory is not writable: {error}") from error

    arguments = [
        str(xenia.resolve()),
        f"--indirect_target_trace_path={output.resolve()}",
        f"--indirect_target_trace_run_id={run_id}",
        f"--indirect_target_trace_label={label}",
        "--indirect_target_trace_image_sha256="
        + identity["patched_image_sha256"].upper(),
        f"--indirect_target_trace_title_id={identity['title_id']}",
        f"--indirect_target_trace_media_id={identity['media_id']}",
        f"--indirect_target_trace_version={identity['version']}",
    ]
    arguments.extend(
        [
            f"--indirect_target_trace_buffer_pairs={DEFAULT_COLLECTOR_BUFFER_PAIRS}",
            f"--indirect_target_trace_dirty_pairs={DEFAULT_COLLECTOR_DIRTY_PAIRS}",
            "--indirect_target_trace_flush_interval_ms="
            f"{DEFAULT_COLLECTOR_FLUSH_INTERVAL_MS}",
            "--indirect_target_trace_max_unique_aggregates="
            f"{DEFAULT_COLLECTOR_MAX_UNIQUE_AGGREGATES}",
            f"--content_root={content_root}",
            "--apply_title_update=true",
            f"--storage_root={storage_root}",
        ]
    )
    arguments.append(f"--log_file={output.with_suffix('.xenia.log').resolve()}")
    arguments.append(str(game_path.resolve()))
    command = "& " + " `\n    ".join(powershell_quote(value) for value in arguments)
    return {
        "status": "ready",
        "collection_enabled": True,
        "run_id": run_id,
        "output": str(output.resolve()),
        "output_parent_writable": True,
        "xenia": {
            "path": str(xenia.resolve()),
            "sha256": sha256_file(xenia),
        },
        "launch_media": {
            "path": str(game_path.resolve()),
            "media_type": media_type,
            "final_positional_argument": True,
            "sha256_calculated": False,
            "identity_role": "complete_game_media_only",
        },
        "analysis_image": {
            "base_xex_path": str(analysis_image_path.resolve()),
            "base_xex_sha256": base_hash,
            "title_update_xexp": str(patch_path.resolve()),
            "title_update_xexp_sha256": patch_hash,
            "expected_patched_image_sha256": identity[
                "patched_image_sha256"
            ].upper(),
            "identity_role": (
                "base_xex_plus_adjacent_xexp_validate_post_patch_loaded_guest_image"
            ),
        },
        "title_identity": {
            "title_id": identity["title_id"],
            "media_id": identity["media_id"],
            "version": identity["version"],
            "expected_analysis_image_sha256": identity[
                "patched_image_sha256"
            ].upper(),
        },
        "content": content_record,
        "storage_root": str(storage_root),
        "collector_persistence": {
            "raw_schema_version": RAW_SCHEMA_VERSION,
            "pair_count_semantics": "delta_since_previous_persistence",
            "buffer_pairs": DEFAULT_COLLECTOR_BUFFER_PAIRS,
            "dirty_pair_limit": DEFAULT_COLLECTOR_DIRTY_PAIRS,
            "flush_interval_ms": DEFAULT_COLLECTOR_FLUSH_INTERVAL_MS,
            "max_unique_aggregates": DEFAULT_COLLECTOR_MAX_UNIQUE_AGGREGATES,
        },
        "arguments": arguments,
        "powershell_command": command,
        "warning": (
            "The complete-game launch media is intentionally not used as the "
            "executable-image identity. Preflight verifies the analysis base XEX, "
            "extracted XEXP, and installed STFS package. Confirm the Xenia log "
            "says the title update was applied before treating gameplay evidence "
            "as exact TU1."
        ),
    }


def load_expected_identity(evidence_path: Path) -> dict[str, Any]:
    try:
        contract = function_map.load_contract(evidence_path)
    except function_map.MapValidationError as error:
        raise Phase4Error(str(error)) from error
    return contract["expected_image_identity"]


def load_expected_hash(evidence_path: Path) -> str:
    return load_expected_identity(evidence_path)["patched_image_sha256"].upper()


def command_summarize(args: argparse.Namespace) -> int:
    expected_identity = load_expected_identity(args.evidence)
    expected = expected_identity["patched_image_sha256"].upper()
    summary = aggregate_raw_runs(
        [parse_raw_trace(path) for path in args.raw], expected, expected_identity
    )
    atomic_write_json(args.output, summary)
    if args.csv:
        write_summary_csv(args.csv, summary)
    print(
        f"PASS: runs={summary['counts']['accepted_runs']} "
        f"quarantined={summary['counts']['quarantined_runs']} "
        f"pairs={summary['counts']['unique_pairs']} output={args.output}"
    )
    return 0


def command_merge(args: argparse.Namespace) -> int:
    summary = merge_summaries([read_summary(path) for path in args.summary])
    atomic_write_json(args.output, summary)
    if args.csv:
        write_summary_csv(args.csv, summary)
    print(
        f"PASS: runs={summary['counts']['accepted_runs']} "
        f"pairs={summary['counts']['unique_pairs']} output={args.output}"
    )
    return 0


def command_plan(args: argparse.Namespace) -> int:
    summary = read_summary(args.summary)
    plan = build_plan(
        summary,
        args.summary,
        args.manifest,
        args.closure,
        args.evidence,
        args.generated_init,
        args.ghidra_map,
    )
    atomic_write_json(args.output, plan)
    print(
        f"PASS: dry-run targets={plan['counts']['observed_non_return_targets']} "
        f"proposals={plan['counts']['range_proposals']} "
        f"applicable_after_review={plan['counts']['automatically_applicable_after_review']} "
        f"manifest_modified=false output={args.output}"
    )
    return 0


def command_apply(args: argparse.Namespace) -> int:
    if not args.apply:
        raise Phase4Error("apply mode requires the explicit --apply flag")
    selected = set(args.select)
    if args.selection_file:
        for line in args.selection_file.read_text(encoding="utf-8").splitlines():
            value = line.strip()
            if value and not value.startswith("#"):
                selected.add(value)
    result = apply_reviewed_plan(read_plan(args.plan), args.manifest, selected)
    print(json.dumps(result, sort_keys=True))
    return 0


def command_preflight(args: argparse.Namespace) -> int:
    result = preflight(
        args.xenia,
        args.game_path,
        args.analysis_image_path,
        args.output,
        args.run_id,
        args.label,
        args.evidence,
        args.content_root,
        args.storage_root,
        args.title_update_package,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def command_post_run(args: argparse.Namespace) -> int:
    args.output_directory.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_directory / "xenia-indirect-targets.summary.json"
    summary_csv = args.output_directory / "xenia-indirect-targets.summary.csv"
    plan_path = args.output_directory / "fable2-indirect-targets.import-plan.json"
    expected_identity = load_expected_identity(args.evidence)
    expected = expected_identity["patched_image_sha256"].upper()
    summary = aggregate_raw_runs(
        [parse_raw_trace(args.raw)], expected, expected_identity
    )
    atomic_write_json(summary_path, summary)
    write_summary_csv(summary_csv, summary)
    plan = build_plan(
        summary,
        summary_path,
        args.manifest,
        args.closure,
        args.evidence,
        args.generated_init,
        args.ghidra_map,
    )
    atomic_write_json(plan_path, plan)
    print(
        json.dumps(
            {
                "status": "dry_run_complete",
                "summary": str(summary_path),
                "summary_csv": str(summary_csv),
                "plan": str(plan_path),
                "manifest_modified": False,
                "counts": plan["counts"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def default_analysis_path(file_name: str) -> Path:
    contract = function_map.load_contract(DEFAULT_EVIDENCE)
    digest = contract["expected_image_identity"]["patched_image_sha256"]
    return REPO_ROOT / "out" / "analysis" / digest / file_name


def add_evidence_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)


def add_planner_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--closure",
        type=Path,
        default=default_analysis_path("entrypoint-closure.json"),
    )
    parser.add_argument(
        "--generated-init", type=Path, default=DEFAULT_GENERATED_INIT
    )
    parser.add_argument(
        "--ghidra-map",
        type=Path,
        action="append",
        default=[],
        help="repeat for exact and related maps; related identities are quarantined",
    )
    add_evidence_arguments(parser)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=TOOL_VERSION)
    subparsers = parser.add_subparsers(dest="command", required=True)

    summarize = subparsers.add_parser(
        "summarize", help="stream one or more crash-tolerant raw JSONL traces"
    )
    summarize.add_argument("--raw", type=Path, action="append", required=True)
    summarize.add_argument("--output", type=Path, required=True)
    summarize.add_argument("--csv", type=Path)
    add_evidence_arguments(summarize)
    summarize.set_defaults(handler=command_summarize)

    merge = subparsers.add_parser(
        "merge", help="deterministically merge summaries without double counting"
    )
    merge.add_argument("--summary", type=Path, action="append", required=True)
    merge.add_argument("--output", type=Path, required=True)
    merge.add_argument("--csv", type=Path)
    merge.set_defaults(handler=command_merge)

    plan = subparsers.add_parser(
        "plan", help="emit a dry-run evidence import plan; never edits the manifest"
    )
    plan.add_argument("--summary", type=Path, required=True)
    plan.add_argument("--output", type=Path, required=True)
    add_planner_arguments(plan)
    plan.set_defaults(handler=command_plan)

    apply = subparsers.add_parser(
        "apply", help="atomically apply explicitly reviewed, guarded candidates"
    )
    apply.add_argument("--plan", type=Path, required=True)
    apply.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    apply.add_argument("--select", action="append", default=[])
    apply.add_argument("--selection-file", type=Path)
    apply.add_argument("--apply", action="store_true")
    apply.set_defaults(handler=command_apply)

    preflight_parser = subparsers.add_parser(
        "preflight", help="verify identities/output and print the private launch command"
    )
    preflight_parser.add_argument("--xenia", type=Path, required=True)
    preflight_parser.add_argument(
        "--game-path",
        type=Path,
        required=True,
        help="complete game media passed as Xenia's final positional argument",
    )
    preflight_parser.add_argument(
        "--analysis-image-path",
        type=Path,
        required=True,
        help="base XEX whose adjacent XEXP validates the post-patch identity",
    )
    preflight_parser.add_argument("--output", type=Path, required=True)
    preflight_parser.add_argument("--run-id", required=True)
    preflight_parser.add_argument("--label", default="Fable II TU1 manual coverage")
    preflight_parser.add_argument(
        "--content-root",
        type=Path,
        required=True,
        help="Xenia content root containing the installed title update",
    )
    preflight_parser.add_argument(
        "--storage-root",
        type=Path,
        required=True,
        help="writable Xenia storage root",
    )
    preflight_parser.add_argument("--title-update-package", type=Path)
    add_evidence_arguments(preflight_parser)
    preflight_parser.set_defaults(handler=command_preflight)

    post_run = subparsers.add_parser(
        "post-run", help="summarize, validate, and dry-run plan a private trace"
    )
    post_run.add_argument("--raw", type=Path, required=True)
    post_run.add_argument("--output-directory", type=Path, required=True)
    add_planner_arguments(post_run)
    post_run.set_defaults(handler=command_post_run)
    return parser


def main() -> int:
    args = build_argument_parser().parse_args()
    return args.handler(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, Phase4Error, function_map.MapValidationError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
