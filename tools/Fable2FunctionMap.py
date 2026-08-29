#!/usr/bin/env python3
"""Validate, import, catalogue, and diff Fable II Ghidra function maps.

Stable outputs deliberately omit timestamps and local acquisition paths. The
canonical manifest is opened read-only and is never rewritten by this tool.
"""

from __future__ import annotations

import argparse
import bisect
import ctypes
import csv
import gc
import hashlib
import json
import sys
import time
import tomllib
import urllib.request
import urllib.error
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE = REPO_ROOT / "tools" / "fable2-entrypoint-closure-evidence.json"
DEFAULT_CATALOG = REPO_ROOT / "tools" / "fable2-ghidra-artifacts.json"
MAP_SCHEMA_NAME = "fable2-ghidra-function-map"
MAP_SCHEMA_VERSIONS = {1}
SHARED_SCHEMA_NAME = "fable2-shared-function-evidence"
SHARED_SCHEMA_VERSION = 2
DIFF_SCHEMA_NAME = "fable2-function-map-diff"
DIFF_SCHEMA_VERSION = 1
IDENTITY_STATES = {
    "exact_image_match",
    "matching_executable_memory",
    "probable_same_build",
    "related_build_or_title_update",
    "identity_incomplete",
    "confirmed_mismatch",
}
DIFF_CLASSES = {
    "exact_match",
    "name_only_difference",
    "size_mismatch",
    "ghidra_missing_from_manifest",
    "manifest_missing_from_ghidra",
    "ghidra_thunk_missing",
    "callable_internal_entry",
    "range_overlap",
    "ghidra_false_positive_suspected",
    "manifest_manual_only",
    "conflicting_boundaries",
    "related_build_candidate",
    "unresolved_identity",
    "pdata_missing_from_ghidra",
    "ghidra_missing_from_pdata",
}


class MapValidationError(ValueError):
    """Raised when a map cannot safely enter the shared evidence model."""


def read_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, json.JSONDecodeError) as error:
        raise MapValidationError(f"could not read JSON '{path}': {error}") from error
    if not isinstance(value, dict):
        raise MapValidationError(f"JSON root in '{path}' is not an object")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False)
        stream.write("\n")
    temporary.replace(path)


def parse_address(value: Any, location: str) -> int:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise MapValidationError(f"{location} must be a 0x-prefixed hexadecimal string")
    try:
        result = int(value, 16)
    except ValueError as error:
        raise MapValidationError(f"{location} is not hexadecimal: {value!r}") from error
    if result < 0 or result > 0xFFFFFFFFFFFFFFFF:
        raise MapValidationError(f"{location} is outside the unsigned 64-bit address space")
    return result


def address_text(value: int) -> str:
    width = 8 if value <= 0xFFFFFFFF else 16
    return f"0x{value:0{width}X}"


def validate_range(
    value: Any, location: str, *, allow_empty: bool = False
) -> tuple[int, int]:
    if not isinstance(value, dict):
        raise MapValidationError(f"{location} must be an object")
    start = parse_address(value.get("start"), f"{location}.start")
    end = parse_address(value.get("end"), f"{location}.end")
    if start > end or (start == end and not allow_empty):
        qualifier = "valid" if allow_empty else "non-empty"
        raise MapValidationError(f"{location} must be a {qualifier} half-open range")
    size = parse_address(value.get("size"), f"{location}.size")
    if size != end - start:
        raise MapValidationError(
            f"{location}.size is {address_text(size)}, expected {address_text(end - start)}"
        )
    return start, end


def require_object(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MapValidationError(f"{location} must be an object")
    return value


def require_list(value: Any, location: str) -> list[Any]:
    if not isinstance(value, list):
        raise MapValidationError(f"{location} must be an array")
    return value


def validate_hash(value: Any, location: str, allow_null: bool = True) -> None:
    if value is None and allow_null:
        return
    if not isinstance(value, str) or len(value) != 64:
        raise MapValidationError(f"{location} must be null or a 64-character SHA-256")
    try:
        int(value, 16)
    except ValueError as error:
        raise MapValidationError(f"{location} is not a SHA-256") from error
    if value != value.upper():
        raise MapValidationError(f"{location} must use uppercase hexadecimal")


def validate_map(document: dict[str, Any]) -> dict[str, Any]:
    schema = require_object(document.get("schema"), "schema")
    if schema.get("name") != MAP_SCHEMA_NAME:
        raise MapValidationError(
            f"schema.name must be {MAP_SCHEMA_NAME!r}, got {schema.get('name')!r}"
        )
    version = schema.get("version")
    if version not in MAP_SCHEMA_VERSIONS:
        raise MapValidationError(
            f"unsupported map schema {version!r}; supported versions are {sorted(MAP_SCHEMA_VERSIONS)}"
        )

    source = require_object(document.get("source_artifact"), "source_artifact")
    if not isinstance(source.get("id"), str) or not source["id"].strip():
        raise MapValidationError("source_artifact.id must be a non-empty string")
    identity = require_object(document.get("identity_evidence"), "identity_evidence")
    for key in (
        "base_xex_sha256",
        "title_update_sha256",
        "patched_image_sha256",
        "executable_memory_fingerprint",
    ):
        validate_hash(identity.get(key), f"identity_evidence.{key}")
    parse_address(identity.get("image_base"), "identity_evidence.image_base")
    blocks = require_list(identity.get("memory_blocks"), "identity_evidence.memory_blocks")
    previous_block_start = -1
    for index, block_value in enumerate(blocks):
        block = require_object(block_value, f"identity_evidence.memory_blocks[{index}]")
        start, _ = validate_range(block.get("range"), f"identity_evidence.memory_blocks[{index}].range")
        if start < previous_block_start:
            raise MapValidationError("memory blocks are not deterministically sorted by address")
        previous_block_start = start
        permissions = require_object(
            block.get("permissions"), f"identity_evidence.memory_blocks[{index}].permissions"
        )
        for key in ("read", "write", "execute"):
            if not isinstance(permissions.get(key), bool):
                raise MapValidationError(
                    f"identity_evidence.memory_blocks[{index}].permissions.{key} must be boolean"
                )
        validate_hash(block.get("sha256"), f"identity_evidence.memory_blocks[{index}].sha256")

    functions = require_list(document.get("functions"), "functions")
    previous_entry = -1
    seen_entries: set[int] = set()
    for index, function_value in enumerate(functions):
        location = f"functions[{index}]"
        function = require_object(function_value, location)
        entry = parse_address(function.get("entry"), f"{location}.entry")
        if entry in seen_entries:
            raise MapValidationError(f"duplicate function entry {address_text(entry)}")
        if entry < previous_entry:
            raise MapValidationError("functions are not deterministically sorted by entry")
        seen_entries.add(entry)
        previous_entry = entry
        body_ranges = require_list(function.get("body_ranges"), f"{location}.body_ranges")
        parsed_ranges: list[tuple[int, int]] = []
        for range_index, range_value in enumerate(body_ranges):
            current = validate_range(range_value, f"{location}.body_ranges[{range_index}]")
            if parsed_ranges and current[0] < parsed_ranges[-1][1]:
                raise MapValidationError(f"{location}.body_ranges overlap or are unsorted")
            parsed_ranges.append(current)
        body_size = parse_address(function.get("body_size"), f"{location}.body_size")
        if body_size != sum(end - start for start, end in parsed_ranges):
            raise MapValidationError(f"{location}.body_size differs from exact body membership")
        extent = validate_range(
            function.get("extent"),
            f"{location}.extent",
            allow_empty=not parsed_ranges,
        )
        if parsed_ranges:
            expected_extent = (parsed_ranges[0][0], parsed_ranges[-1][1])
            if extent != expected_extent:
                raise MapValidationError(f"{location}.extent differs from body min/max")
            if not any(start <= entry < end for start, end in parsed_ranges):
                raise MapValidationError(f"{location}.entry is not a member of its function body")
        elif extent != (entry, entry):
            raise MapValidationError(f"{location}.empty body must have an empty extent at its entry")
        if function.get("contiguous_body") is not (len(parsed_ranges) <= 1):
            raise MapValidationError(f"{location}.contiguous_body is inconsistent")
        primary_name = require_object(function.get("primary_name"), f"{location}.primary_name")
        if not isinstance(primary_name.get("name"), str):
            raise MapValidationError(f"{location}.primary_name.name must be a string")
        aliases = require_list(function.get("aliases"), f"{location}.aliases")
        for alias_index, alias_value in enumerate(aliases):
            alias = require_object(alias_value, f"{location}.aliases[{alias_index}]")
            if not isinstance(alias.get("name"), str) or not isinstance(alias.get("source_type"), str):
                raise MapValidationError(f"{location}.aliases[{alias_index}] has invalid name provenance")
        pdata_records = require_list(function.get("pdata_records"), f"{location}.pdata_records")
        for pdata_index, address in enumerate(pdata_records):
            parse_address(address, f"{location}.pdata_records[{pdata_index}]")
        references = require_list(function.get("inbound_references"), f"{location}.inbound_references")
        for reference_index, reference_value in enumerate(references):
            reference = require_object(reference_value, f"{location}.inbound_references[{reference_index}]")
            parse_address(reference.get("from"), f"{location}.inbound_references[{reference_index}].from")
            parse_address(reference.get("to"), f"{location}.inbound_references[{reference_index}].to")
            if reference.get("category") not in {"code", "data"}:
                raise MapValidationError(f"{location}.inbound_references[{reference_index}].category is invalid")
        labels = require_list(
            function.get("callable_internal_labels"), f"{location}.callable_internal_labels"
        )
        for label_index, label_value in enumerate(labels):
            label = require_object(label_value, f"{location}.callable_internal_labels[{label_index}]")
            parse_address(label.get("address"), f"{location}.callable_internal_labels[{label_index}].address")
            if not isinstance(label.get("name"), str) or not isinstance(label.get("source_type"), str):
                raise MapValidationError(f"{location}.callable_internal_labels[{label_index}] has invalid provenance")
            require_list(
                label.get("inbound_code_references"),
                f"{location}.callable_internal_labels[{label_index}].inbound_code_references",
            )
        for key in ("other_function_entries_in_body", "overlapping_function_entries"):
            entries = require_list(function.get(key), f"{location}.{key}")
            for entry_index, other_entry in enumerate(entries):
                parse_address(other_entry, f"{location}.{key}[{entry_index}]")
        thunk = function.get("thunk")
        if thunk is not None:
            thunk = require_object(thunk, f"{location}.thunk")
            if thunk.get("is_thunk") is not True:
                raise MapValidationError(f"{location}.thunk.is_thunk must be true")
            for key in ("direct_target", "terminal_target"):
                if thunk.get(key) is not None:
                    parse_address(thunk[key], f"{location}.thunk.{key}")

    pdata_functions = document.get("pdata_functions", [])
    pdata_functions = require_list(pdata_functions, "pdata_functions")
    previous_pdata_entry = -1
    for index, pdata_value in enumerate(pdata_functions):
        pdata = require_object(pdata_value, f"pdata_functions[{index}]")
        pdata_entry = parse_address(pdata.get("entry"), f"pdata_functions[{index}].entry")
        if pdata_entry <= previous_pdata_entry:
            raise MapValidationError("pdata_functions entries are duplicated or unsorted")
        previous_pdata_entry = pdata_entry
        addresses = require_list(
            pdata.get("record_addresses"), f"pdata_functions[{index}].record_addresses"
        )
        if not addresses:
            raise MapValidationError(f"pdata_functions[{index}] has no record addresses")
        parsed_addresses = [
            parse_address(address, f"pdata_functions[{index}].record_addresses[{address_index}]")
            for address_index, address in enumerate(addresses)
        ]
        if parsed_addresses != sorted(set(parsed_addresses)):
            raise MapValidationError(
                f"pdata_functions[{index}].record_addresses are duplicated or unsorted"
            )

    overlaps = require_list(document.get("overlaps"), "overlaps")
    for index, overlap_value in enumerate(overlaps):
        overlap = require_object(overlap_value, f"overlaps[{index}]")
        entries = require_list(overlap.get("entries"), f"overlaps[{index}].entries")
        if len(entries) != 2:
            raise MapValidationError(f"overlaps[{index}].entries must contain two entries")
        for entry_index, entry_value in enumerate(entries):
            parse_address(entry_value, f"overlaps[{index}].entries[{entry_index}]")
        for range_index, range_value in enumerate(
            require_list(overlap.get("body_ranges"), f"overlaps[{index}].body_ranges")
        ):
            validate_range(range_value, f"overlaps[{index}].body_ranges[{range_index}]")
    program = require_object(document.get("program"), "program")
    if program.get("function_count") != len(functions):
        raise MapValidationError(
            f"program.function_count is {program.get('function_count')!r}, expected {len(functions)}"
        )
    return document


def normalize_hash(value: Any) -> str | None:
    return value.upper() if isinstance(value, str) and value else None


def assess_identity(document: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    actual = document["identity_evidence"]
    source = document["source_artifact"]
    expected = contract["expected_image_identity"]
    comparisons: dict[str, str] = {}
    for actual_key, expected_key in (
        ("base_xex_sha256", "base_xex_sha256"),
        ("title_update_sha256", "title_update_sha256"),
        ("patched_image_sha256", "patched_image_sha256"),
        ("executable_memory_fingerprint", "executable_memory_sha256"),
    ):
        left = normalize_hash(actual.get(actual_key))
        right = normalize_hash(expected.get(expected_key))
        comparisons[actual_key] = "missing" if left is None else ("match" if left == right else "mismatch")

    algorithm = actual.get("executable_memory_fingerprint_algorithm")
    expected_algorithm = expected.get("executable_memory_fingerprint_algorithm")
    fingerprint_complete = actual.get("executable_memory_fingerprint_status") == "complete"
    fingerprint_matches = (
        algorithm == expected_algorithm
        and fingerprint_complete
        and comparisons["executable_memory_fingerprint"] == "match"
    )
    exact_hashes = all(
        comparisons[key] == "match"
        for key in ("base_xex_sha256", "title_update_sha256", "patched_image_sha256")
    )

    expected_sections = {
        (item["start"], item["end"], item["permissions"]): item["sha256"]
        for item in expected.get("executable_sections", [])
    }
    actual_sections: dict[tuple[str, str, str], str] = {}
    for block in actual.get("memory_blocks", []):
        permissions = block.get("permissions", {})
        if not permissions.get("execute") or not block.get("sha256"):
            continue
        permission_text = "".join(
            (
                "r" if permissions.get("read") else "-",
                "w" if permissions.get("write") else "-",
                "x" if permissions.get("execute") else "-",
            )
        )
        block_range = block.get("range", {})
        actual_sections[(block_range.get("start"), block_range.get("end"), permission_text)] = block["sha256"]
    section_match = bool(expected_sections) and all(
        actual_sections.get(key) == value for key, value in expected_sections.items()
    )

    claimed_title = " ".join(
        str(source.get(key) or "")
        for key in ("id", "claimed_edition", "claimed_title_update")
    ).lower()
    appears_related = "fable" in claimed_title or any(
        value == "match" for key, value in comparisons.items() if key != "executable_memory_fingerprint"
    )
    explicit_hash_mismatch = any(value == "mismatch" for value in comparisons.values())
    exact_claim_contradicted = exact_hashes and fingerprint_complete and not fingerprint_matches

    if exact_hashes and fingerprint_matches:
        state = "exact_image_match"
    elif fingerprint_matches:
        state = "matching_executable_memory"
    elif exact_claim_contradicted:
        state = "confirmed_mismatch"
    elif section_match:
        state = "probable_same_build"
    elif explicit_hash_mismatch and appears_related:
        state = "related_build_or_title_update"
    elif explicit_hash_mismatch:
        state = "confirmed_mismatch"
    else:
        state = "identity_incomplete"
    assert state in IDENTITY_STATES
    return {
        "state": state,
        "comparisons": comparisons,
        "fingerprint_algorithm": algorithm,
        "fingerprint_status": actual.get("executable_memory_fingerprint_status"),
        "executable_section_hashes_match": section_match,
        "automatic_tu1_use_allowed": state in {"exact_image_match", "matching_executable_memory"},
        "source_artifact_id": source["id"],
    }


def load_contract(path: Path) -> dict[str, Any]:
    contract = read_json(path)
    if contract.get("schema_version") not in {1, 2}:
        raise MapValidationError(
            f"unsupported shared evidence contract schema {contract.get('schema_version')!r}"
        )
    if not isinstance(contract.get("expected_image_identity"), dict):
        raise MapValidationError("shared evidence contract has no expected_image_identity")
    return contract


def imported_evidence(document: dict[str, Any], identity: dict[str, Any]) -> dict[str, Any]:
    source = document["source_artifact"]
    functions = []
    for function in document["functions"]:
        functions.append(
            {
                "aliases": function["aliases"],
                "body_ranges": function["body_ranges"],
                "body_size": function["body_size"],
                "callable_internal_labels": function["callable_internal_labels"],
                "entry": function["entry"],
                "extent": function["extent"],
                "inbound_references": function["inbound_references"],
                "name": function["primary_name"],
                "overlapping_function_entries": function["overlapping_function_entries"],
                "pdata_records": function["pdata_records"],
                "source_artifact_id": source["id"],
                "source_identity_state": identity["state"],
                "thunk": function["thunk"],
            }
        )
    return {
        "schema": {"name": SHARED_SCHEMA_NAME, "version": SHARED_SCHEMA_VERSION},
        "identity_assessment": identity,
        "map_schema": document["schema"],
        "source_artifact": source,
        "toolchain": document["toolchain"],
        "functions": functions,
        "pdata_functions": document.get("pdata_functions", []),
        "overlaps": document["overlaps"],
    }


def load_manifest(path: Path) -> dict[int, dict[str, Any]]:
    try:
        with path.open("rb") as stream:
            root = tomllib.load(stream)
        values = root["entrypoint"]["functions"]
    except (OSError, KeyError, tomllib.TOMLDecodeError) as error:
        raise MapValidationError(f"could not read manifest '{path}': {error}") from error
    result: dict[int, dict[str, Any]] = {}
    for key, value in values.items():
        entry = int(key, 0)
        size = value.get("size")
        if not isinstance(size, int) or size <= 0:
            raise MapValidationError(f"manifest function {key} has invalid size {size!r}")
        result[entry] = {
            "entry": address_text(entry),
            "range": range_record(entry, entry + size),
            "name": value.get("name"),
            "provenance": "canonical_manifest",
        }
    return result


def range_record(start: int, end: int) -> dict[str, str]:
    return {
        "start": address_text(start),
        "end": address_text(end),
        "size": address_text(end - start),
    }


def compact_closure(path: Path) -> tuple[dict[int, dict[str, Any]], dict[int, dict[str, Any]], dict[str, Any]]:
    document = read_json(path)
    ranges: dict[int, dict[str, Any]] = {}
    for item in document.get("function_ranges", []):
        value = item["range"]
        entry = parse_address(value["start"], "closure.function_ranges.start")
        ranges[entry] = {
            "range": value,
            "authority": item.get("authority"),
            "boundary_provenance": item.get("boundary_provenance", []),
            "trusted": item.get("trusted"),
            "preliminary": item.get("preliminary"),
            "manifest": item.get("manifest"),
            "exception_function": item.get("exception_function"),
            "basic_blocks": item.get("basic_blocks", []),
        }
    candidates: dict[int, dict[str, Any]] = {}
    for item in document.get("candidates", []):
        entry = parse_address(item["address"], "closure.candidates.address")
        candidates[entry] = {
            "proposed_range": item.get("proposed_range"),
            "classification": item.get("classification"),
            "confidence": item.get("confidence"),
            "boundary_provenance": item.get("boundary_provenance"),
            "evidence": item.get("evidence", []),
            "conflicts": item.get("conflicts", []),
            "rejection_reasons": item.get("rejection_reasons", []),
        }
    metadata = {
        "schema_version": document.get("schema_version"),
        "analyzer_version": document.get("analyzer_version"),
        "image_identity": document.get("image_identity"),
        "safety": document.get("safety"),
    }
    del document
    gc.collect()
    return ranges, candidates, metadata


def exact_body(function: dict[str, Any]) -> list[tuple[int, int]]:
    return [
        (parse_address(item["start"], "body.start"), parse_address(item["end"], "body.end"))
        for item in function["body_ranges"]
    ]


def default_ghidra_name(name: str, entry: int) -> bool:
    lowered = name.lower()
    return lowered in {
        f"function_{entry:08x}",
        f"fun_{entry:08x}",
        f"sub_{entry:08x}",
    }


def surrounding_boundaries(
    entry: int, ranges: dict[int, dict[str, Any]], starts: list[int]
) -> dict[str, Any]:
    index = bisect.bisect_left(starts, entry)
    before = ranges[starts[index - 1]]["range"] if index else None
    after_index = index + 1 if index < len(starts) and starts[index] == entry else index
    after = ranges[starts[after_index]]["range"] if after_index < len(starts) else None
    containing: list[dict[str, Any]] = []
    for candidate_index in {index - 1, index}:
        if candidate_index < 0 or candidate_index >= len(starts):
            continue
        start = starts[candidate_index]
        item = ranges[start]
        end = parse_address(item["range"]["end"], "closure range end")
        if start <= entry < end:
            containing.append(item["range"])
    return {"previous": before, "containing": containing, "next": after}


def make_source_ghidra(
    function: dict[str, Any], source: dict[str, Any], identity_state: str
) -> dict[str, Any]:
    return {
        "source_artifact_id": source["id"],
        "identity_state": identity_state,
        "entry": function["entry"],
        "body_ranges": function["body_ranges"],
        "body_size": function["body_size"],
        "extent": function["extent"],
        "contiguous_body": function["contiguous_body"],
        "primary_name": function["primary_name"],
        "aliases": function["aliases"],
        "thunk": function["thunk"],
        "pdata_records": function["pdata_records"],
        "inbound_references": function["inbound_references"],
        "other_function_entries_in_body": function["other_function_entries_in_body"],
        "overlapping_function_entries": function["overlapping_function_entries"],
    }


def difference_record(
    entry: int | None,
    classifications: Iterable[str],
    sources: dict[str, Any],
    conflicts: list[str],
    recommendation: str,
    automatic_safe: bool,
    surroundings: dict[str, Any] | None,
) -> dict[str, Any]:
    classes = sorted(set(classifications))
    unknown = set(classes) - DIFF_CLASSES
    if unknown:
        raise AssertionError(f"unknown diff classes: {sorted(unknown)}")
    return {
        "address": address_text(entry) if entry is not None else None,
        "classifications": classes,
        "sources": sources,
        "conflicts": sorted(set(conflicts)),
        "surrounding_trusted_boundaries": surroundings,
        "recommended_validation": recommendation,
        "automatic_action_safe": automatic_safe,
    }


def build_diff(
    map_document: dict[str, Any],
    identity: dict[str, Any],
    manifest: dict[int, dict[str, Any]],
    closure_ranges: dict[int, dict[str, Any]],
    closure_candidates: dict[int, dict[str, Any]],
    closure_metadata: dict[str, Any],
    contract: dict[str, Any],
    mode: str,
) -> dict[str, Any]:
    ghidra = {
        parse_address(item["entry"], "functions.entry"): item
        for item in map_document["functions"]
    }
    manual = {
        parse_address(item["address"], "manual_evidence.address"): item
        for item in contract.get("manual_evidence", [])
    }
    pdata: dict[int, dict[str, Any]] = {
        parse_address(item["entry"], "pdata_functions.entry"): item
        for item in map_document.get("pdata_functions", [])
    }
    if not pdata:
        for function in map_document["functions"]:
            if function.get("pdata_records"):
                entry = parse_address(function["entry"], "functions.entry")
                pdata[entry] = {
                    "entry": function["entry"],
                    "record_addresses": function["pdata_records"],
                    "compatibility_source": "function_association_from_map_without_pdata_functions",
                }
    closure_starts = sorted(closure_ranges)
    differences: list[dict[str, Any]] = []
    if identity["state"] == "related_build_or_title_update":
        differences.append(
            difference_record(
                None,
                ["related_build_candidate"],
                {"ghidra_identity": identity},
                ["map identity is not exact TU1"],
                "Use only in explicit comparative mode; validate addresses and bytes against TU1.",
                False,
                None,
            )
        )
    elif identity["state"] not in {"exact_image_match", "matching_executable_memory"}:
        differences.append(
            difference_record(
                None,
                ["unresolved_identity"],
                {"ghidra_identity": identity},
                [f"identity state is {identity['state']}"],
                "Acquire complete hashes or reproduce the executable-memory fingerprint.",
                False,
                None,
            )
        )

    all_entries = sorted(
        set(ghidra) | set(manifest) | set(closure_ranges) | set(manual) | set(pdata)
    )
    for entry in all_entries:
        gfun = ghidra.get(entry)
        mfun = manifest.get(entry)
        rfun = closure_ranges.get(entry)
        candidate = closure_candidates.get(entry)
        manual_item = manual.get(entry)
        pdata_item = pdata.get(entry)
        classes: list[str] = []
        conflicts: list[str] = []
        sources: dict[str, Any] = {}
        if gfun:
            sources["ghidra"] = make_source_ghidra(
                gfun, map_document["source_artifact"], identity["state"]
            )
        if mfun:
            sources["manifest"] = mfun
        if rfun:
            sources["rexglue_analysis"] = rfun
        if candidate:
            sources["entrypoint_closure"] = candidate
        if manual_item:
            sources["manual_and_fault_walker"] = manual_item
        if pdata_item:
            sources["pdata"] = pdata_item

        if gfun and rfun:
            gbody = exact_body(gfun)
            rrange = rfun["range"]
            rex_range = (
                parse_address(rrange["start"], "rex range start"),
                parse_address(rrange["end"], "rex range end"),
            )
            primary_name = gfun["primary_name"]["name"]
            other_name = mfun.get("name") if mfun else None
            if len(gbody) == 1 and gbody[0] == rex_range:
                if other_name and primary_name != other_name:
                    classes.append("name_only_difference")
                else:
                    classes.append("exact_match")
            elif len(gbody) == 1 and gbody[0][0] == rex_range[0]:
                classes.append("size_mismatch")
                conflicts.append(
                    f"Ghidra ends {address_text(gbody[0][1])}; ReXGlue ends {address_text(rex_range[1])}"
                )
            else:
                classes.append("conflicting_boundaries")
                conflicts.append("Ghidra body membership differs from the ReXGlue function range")
        elif gfun and mfun:
            gbody = exact_body(gfun)
            manifest_range = (
                parse_address(mfun["range"]["start"], "manifest range start"),
                parse_address(mfun["range"]["end"], "manifest range end"),
            )
            if len(gbody) == 1 and gbody[0] == manifest_range:
                classes.append("exact_match")
            elif len(gbody) == 1 and gbody[0][0] == manifest_range[0]:
                classes.append("size_mismatch")
            else:
                classes.append("conflicting_boundaries")

        if gfun and not mfun:
            classes.append("ghidra_missing_from_manifest")
            if gfun.get("thunk"):
                classes.append("ghidra_thunk_missing")
            name_info = gfun.get("primary_name", {})
            if (
                not gfun.get("pdata_records")
                and not gfun.get("inbound_references")
                and not rfun
                and name_info.get("source_type") == "analysis"
                and default_ghidra_name(name_info.get("name", ""), entry)
            ):
                classes.append("ghidra_false_positive_suspected")
        if mfun and not gfun:
            classes.append("manifest_missing_from_ghidra")
            if manual_item:
                classes.append("manifest_manual_only")
        if pdata_item and not gfun:
            classes.append("pdata_missing_from_ghidra")
        if gfun and not pdata_item:
            classes.append("ghidra_missing_from_pdata")
        if gfun and (
            gfun.get("overlapping_function_entries")
            or gfun.get("other_function_entries_in_body")
        ):
            classes.append("range_overlap")
            conflicts.append("Ghidra reports overlapping or multiple function entries")

        if classes:
            strict_identity = identity["state"] in {
                "exact_image_match",
                "matching_executable_memory",
            }
            automatic_safe = bool(
                strict_identity
                and mode == "exact"
                and gfun
                and not mfun
                and not rfun
                and gfun.get("contiguous_body")
                and pdata_item
                and not gfun.get("thunk")
                and not conflicts
                and not gfun.get("overlapping_function_entries")
            )
            recommendation = (
                "Boundary-only TU1 disassembly validation; compare exact body membership, .pdata, and callers."
                if not automatic_safe
                else "Eligible only for review-fragment proposal; verify TU1 control flow before manifest adoption."
            )
            differences.append(
                difference_record(
                    entry,
                    classes,
                    sources,
                    conflicts,
                    recommendation,
                    automatic_safe,
                    surrounding_boundaries(entry, closure_ranges, closure_starts),
                )
            )

        if gfun:
            for label in gfun.get("callable_internal_labels", []):
                label_address = parse_address(label["address"], "callable_internal_labels.address")
                differences.append(
                    difference_record(
                        label_address,
                        ["callable_internal_entry"],
                        {
                            "ghidra_parent_function": make_source_ghidra(
                                gfun, map_document["source_artifact"], identity["state"]
                            ),
                            "internal_label": label,
                        },
                        [f"callable label lies inside function {gfun['entry']}"],
                        "Validate whether this is a true multiple entry or an internal branch label.",
                        False,
                        surrounding_boundaries(label_address, closure_ranges, closure_starts),
                    )
                )

    differences.sort(
        key=lambda item: (
            -1 if item["address"] is None else parse_address(item["address"], "diff address"),
            item["classifications"],
        )
    )
    counts = Counter(
        classification
        for item in differences
        for classification in item["classifications"]
    )
    fixtures = []
    for fixture in contract.get("acceptance_fixtures", []):
        entry = parse_address(fixture["address"], "fixture.address")
        size = parse_address(fixture["size"], "fixture.size")
        gfun = ghidra.get(entry)
        body_matches = False
        if gfun:
            body = exact_body(gfun)
            body_matches = len(body) == 1 and body[0] == (entry, entry + size)
        fixtures.append(
            {
                "address": fixture["address"],
                "expected_end": address_text(entry + size),
                "expected_size": fixture["size"],
                "verified_classification": fixture["verified_classification"],
                "map_status": "exact_match" if body_matches else ("boundary_mismatch" if gfun else "omitted"),
                "ghidra_body_ranges": gfun["body_ranges"] if gfun else [],
                "identity_state": identity["state"],
            }
        )

    return {
        "schema": {"name": DIFF_SCHEMA_NAME, "version": DIFF_SCHEMA_VERSION},
        "shared_evidence_schema": {
            "name": SHARED_SCHEMA_NAME,
            "version": SHARED_SCHEMA_VERSION,
        },
        "mode": mode,
        "identity_assessment": identity,
        "source_artifact": map_document["source_artifact"],
        "toolchain": map_document["toolchain"],
        "inputs": {
            "map_schema": map_document["schema"],
            "closure_schema_version": closure_metadata.get("schema_version"),
            "closure_analyzer_version": closure_metadata.get("analyzer_version"),
            "manifest_function_count": len(manifest),
            "ghidra_function_count": len(ghidra),
            "rexglue_function_range_count": len(closure_ranges),
            "pdata_function_count": len(pdata),
        },
        "counts": {
            "differences": len(differences),
            "by_classification": dict(sorted(counts.items())),
            "review_fragment_entries": sum(
                1 for item in differences if item["automatic_action_safe"]
            ),
        },
        "fixture_results": fixtures,
        "differences": differences,
        "safety": {
            "mode": "report_only",
            "canonical_manifest_modified": False,
            "review_fragment_is_non_authoritative": True,
            "related_or_incomplete_evidence_quarantined": not identity[
                "automatic_tu1_use_allowed"
            ],
        },
    }


def write_csv_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=(
                "address",
                "classifications",
                "ghidra_ranges",
                "manifest_range",
                "rexglue_range",
                "ghidra_name",
                "name_source_type",
                "pdata_records",
                "inbound_reference_count",
                "identity_state",
                "automatic_action_safe",
                "conflicts",
                "recommended_validation",
            ),
            lineterminator="\n",
        )
        writer.writeheader()
        for item in report["differences"]:
            sources = item["sources"]
            ghidra = sources.get("ghidra") or sources.get("ghidra_parent_function") or {}
            primary = ghidra.get("primary_name", {})
            writer.writerow(
                {
                    "address": item["address"] or "",
                    "classifications": ";".join(item["classifications"]),
                    "ghidra_ranges": json.dumps(ghidra.get("body_ranges", []), sort_keys=True),
                    "manifest_range": json.dumps(
                        sources.get("manifest", {}).get("range"), sort_keys=True
                    ),
                    "rexglue_range": json.dumps(
                        sources.get("rexglue_analysis", {}).get("range"), sort_keys=True
                    ),
                    "ghidra_name": primary.get("name", ""),
                    "name_source_type": primary.get("source_type", ""),
                    "pdata_records": ";".join(ghidra.get("pdata_records", [])),
                    "inbound_reference_count": len(ghidra.get("inbound_references", [])),
                    "identity_state": report["identity_assessment"]["state"],
                    "automatic_action_safe": str(item["automatic_action_safe"]).lower(),
                    "conflicts": ";".join(item["conflicts"]),
                    "recommended_validation": item["recommended_validation"],
                }
            )


def write_markdown_report(path: Path, report: dict[str, Any]) -> None:
    identity = report["identity_assessment"]
    lines = [
        "# Fable II Ghidra function-map diff",
        "",
        f"- Mode: `{report['mode']}`",
        f"- Identity: `{identity['state']}`",
        f"- Source artifact: `{report['source_artifact']['id']}`",
        f"- Ghidra functions: {report['inputs']['ghidra_function_count']}",
        f"- `.pdata` function entries: {report['inputs']['pdata_function_count']}",
        f"- ReXGlue ranges: {report['inputs']['rexglue_function_range_count']}",
        f"- Manifest overrides: {report['inputs']['manifest_function_count']}",
        f"- Difference records: {report['counts']['differences']}",
        "- Canonical manifest modified: no",
        "",
        "## Classification counts",
        "",
        "| Classification | Count |",
        "|---|---:|",
    ]
    for name, count in report["counts"]["by_classification"].items():
        lines.append(f"| `{name}` | {count} |")
    lines.extend(
        [
            "",
            "## Acceptance fixtures",
            "",
            "| Address | Expected range | Expected role | Ghidra map |",
            "|---|---|---|---|",
        ]
    )
    for fixture in report["fixture_results"]:
        lines.append(
            f"| `{fixture['address']}` | `{fixture['address']}–{fixture['expected_end']}` "
            f"(`{fixture['expected_size']}`) | {fixture['verified_classification']} | "
            f"`{fixture['map_status']}` |"
        )
    lines.extend(
        [
            "",
            "## Review guidance",
            "",
            "The JSON report is authoritative and retains exact body fragments, names/source types, "
            "identity, `.pdata`, xrefs, conflicts, and source provenance. CSV is a compact review view. "
            "The TOML fragment is non-authoritative and is never applied automatically.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def write_review_fragment(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Non-authoritative Ghidra review fragment.",
        "# Generated report-only; do not merge without TU1 boundary validation.",
        "[entrypoint.functions]",
    ]
    for item in report["differences"]:
        if not item["automatic_action_safe"] or item["address"] is None:
            continue
        function = item["sources"]["ghidra"]
        ranges = function["body_ranges"]
        if len(ranges) != 1:
            continue
        lines.append(
            f'"{item["address"]}" = {{ size = {ranges[0]["size"]} }} '
            f'# review-only: {report["source_artifact"]["id"]}'
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest().upper()


def peak_working_set_bytes() -> int | None:
    if sys.platform != "win32":
        return None

    class ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong),
            ("PageFaultCount", ctypes.c_ulong),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    counters = ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    ctypes.windll.kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    ctypes.windll.psapi.GetProcessMemoryInfo.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ProcessMemoryCounters),
        ctypes.c_ulong,
    ]
    ctypes.windll.psapi.GetProcessMemoryInfo.restype = ctypes.c_int
    process = ctypes.windll.kernel32.GetCurrentProcess()
    if not ctypes.windll.psapi.GetProcessMemoryInfo(
        process, ctypes.byref(counters), counters.cb
    ):
        return None
    return int(counters.PeakWorkingSetSize)


def validate_catalog(document: dict[str, Any]) -> list[dict[str, Any]]:
    schema = document.get("schema", {})
    if schema != {"name": "fable2-public-analysis-artifact-catalog", "version": 1}:
        raise MapValidationError("unsupported public-artifact catalogue schema")
    artifacts = require_list(document.get("artifacts"), "artifacts")
    ids: set[str] = set()
    for index, artifact_value in enumerate(artifacts):
        artifact = require_object(artifact_value, f"artifacts[{index}]")
        identifier = artifact.get("id")
        if not isinstance(identifier, str) or not identifier or identifier in ids:
            raise MapValidationError(f"artifacts[{index}].id is missing or duplicated")
        ids.add(identifier)
        if not isinstance(artifact.get("url"), str):
            raise MapValidationError(f"artifacts[{index}].url must be a string")
        if artifact.get("sha256") is not None:
            validate_hash(artifact["sha256"], f"artifacts[{index}].sha256")
            if not isinstance(artifact.get("size"), int) or artifact["size"] <= 0:
                raise MapValidationError(
                    f"artifacts[{index}].size must accompany a downloadable hash"
                )
    return artifacts


def catalog_command(args: argparse.Namespace) -> int:
    document = read_json(args.catalog.resolve())
    artifacts = validate_catalog(document)
    if args.output:
        write_json(args.output.resolve(), document)
    if args.download_directory:
        destination = args.download_directory.resolve()
        destination.mkdir(parents=True, exist_ok=True)
        for artifact in artifacts:
            download_url = artifact.get("download_url")
            expected_hash = artifact.get("sha256")
            filename = artifact.get("filename")
            if not download_url or not expected_hash or not filename:
                continue
            output = destination / filename
            if not output.exists():
                print(f"Downloading {artifact['id']} -> {output}")
                urllib.request.urlretrieve(download_url, output)
            actual_hash = sha256_file(output)
            actual_size = output.stat().st_size
            if actual_size != artifact["size"]:
                raise MapValidationError(
                    f"catalog artifact {artifact['id']} size mismatch: "
                    f"expected {artifact['size']}, got {actual_size}"
                )
            if actual_hash != expected_hash:
                raise MapValidationError(
                    f"catalog artifact {artifact['id']} hash mismatch: expected {expected_hash}, got {actual_hash}"
                )
    for artifact in artifacts:
        print(
            f"{artifact['id']}: {artifact['disposition']} "
            f"identity={artifact['identity_state']} url={artifact['url']}"
        )
    print(f"PASS: catalogued {len(artifacts)} artifacts/search records")
    return 0


def validate_command(args: argparse.Namespace) -> int:
    started = time.perf_counter()
    document = validate_map(read_json(args.map.resolve()))
    contract = load_contract(args.evidence.resolve())
    identity = assess_identity(document, contract)
    elapsed = time.perf_counter() - started
    peak_memory = peak_working_set_bytes()
    print(
        f"PASS: schema={document['schema']['version']} functions={len(document['functions'])} "
        f"identity={identity['state']} elapsed={elapsed:.3f}s "
        f"peak_working_set_bytes={peak_memory}"
    )
    return 0


def import_command(args: argparse.Namespace) -> int:
    document = validate_map(read_json(args.map.resolve()))
    contract = load_contract(args.evidence.resolve())
    identity = assess_identity(document, contract)
    if args.mode == "exact" and not identity["automatic_tu1_use_allowed"]:
        raise MapValidationError(
            f"exact import rejects identity state {identity['state']}; use --mode comparative to quarantine it"
        )
    output = args.output or args.map.with_name(args.map.stem + ".imported.json")
    write_json(output.resolve(), imported_evidence(document, identity))
    print(f"Imported {len(document['functions'])} functions -> {output.resolve()}")
    print(f"Identity: {identity['state']} (mode={args.mode})")
    return 0


def diff_command(args: argparse.Namespace) -> int:
    started = time.perf_counter()
    manifest_path = args.manifest.resolve()
    manifest_hash_before = sha256_file(manifest_path)
    contract = load_contract(args.evidence.resolve())
    expected_hash = contract["expected_image_identity"]["patched_image_sha256"]
    closure_path = args.closure or (
        REPO_ROOT / "out" / "analysis" / expected_hash / "entrypoint-closure.json"
    )
    closure_ranges, closure_candidates, closure_metadata = compact_closure(closure_path.resolve())
    document = validate_map(read_json(args.map.resolve()))
    identity = assess_identity(document, contract)
    if args.mode == "exact" and not identity["automatic_tu1_use_allowed"]:
        raise MapValidationError(
            f"exact diff rejects identity state {identity['state']}; use --mode comparative to quarantine it"
        )
    manifest = load_manifest(manifest_path)
    report = build_diff(
        document,
        identity,
        manifest,
        closure_ranges,
        closure_candidates,
        closure_metadata,
        contract,
        args.mode,
    )
    output_directory = args.output_directory or (
        REPO_ROOT / "out" / "analysis" / expected_hash
    )
    output_directory = output_directory.resolve()
    json_path = output_directory / "function-map-diff.json"
    csv_path = output_directory / "function-map-diff.csv"
    markdown_path = output_directory / "function-map-diff.md"
    fragment_path = output_directory / "function-map-diff-review.toml"
    write_json(json_path, report)
    write_csv_report(csv_path, report)
    write_markdown_report(markdown_path, report)
    write_review_fragment(fragment_path, report)
    manifest_hash_after = sha256_file(manifest_path)
    if manifest_hash_after != manifest_hash_before:
        raise MapValidationError("report-only invariant failed: canonical manifest changed")
    elapsed = time.perf_counter() - started
    peak_memory = peak_working_set_bytes()
    if args.run_metadata:
        write_json(
            args.run_metadata.resolve(),
            {
                "schema_version": 1,
                "elapsed_milliseconds": round(elapsed * 1000),
                "peak_working_set_bytes": peak_memory,
                "map_path": str(args.map.resolve()),
                "closure_path": str(closure_path.resolve()),
                "output_directory": str(output_directory),
            },
        )
    print(
        f"PASS: identity={identity['state']} differences={report['counts']['differences']} "
        f"elapsed={elapsed:.3f}s peak_working_set_bytes={peak_memory} manifest_unchanged=true"
    )
    print(f"JSON: {json_path}")
    print(f"CSV: {csv_path}")
    print(f"Markdown: {markdown_path}")
    print(f"Review fragment: {fragment_path}")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description="Production Ghidra/XEXLoader function-map workflow for Fable II GOTY TU1."
    )
    commands = root.add_subparsers(dest="command", required=True)

    catalog = commands.add_parser(
        "catalog", help="validate, print, optionally copy/download the public artifact catalogue"
    )
    catalog.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    catalog.add_argument("--output", type=Path, help="write a deterministic catalogue copy")
    catalog.add_argument(
        "--download-directory",
        type=Path,
        help="download only entries with pinned download_url, filename, and SHA-256",
    )
    catalog.set_defaults(handler=catalog_command)

    validate = commands.add_parser("validate", help="strictly validate a byte-free map and identity")
    validate.add_argument("map", type=Path)
    validate.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    validate.set_defaults(handler=validate_command)

    import_map = commands.add_parser(
        "import-map", help="import a map into version 2 of the shared evidence model"
    )
    import_map.add_argument("map", type=Path)
    import_map.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    import_map.add_argument("--mode", choices=("exact", "comparative"), default="exact")
    import_map.add_argument("--output", type=Path)
    import_map.set_defaults(handler=import_command)

    diff = commands.add_parser(
        "diff", help="produce deterministic JSON/CSV/Markdown and review-only TOML"
    )
    diff.add_argument("map", type=Path)
    diff.add_argument("--mode", choices=("exact", "comparative"), default="exact")
    diff.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    diff.add_argument("--manifest", type=Path, default=REPO_ROOT / "fable2_manifest.toml")
    diff.add_argument("--closure", type=Path)
    diff.add_argument("--output-directory", type=Path)
    diff.add_argument(
        "--run-metadata",
        type=Path,
        help="optional volatile timing/path JSON kept separate from stable reports",
    )
    diff.set_defaults(handler=diff_command)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        return args.handler(args)
    except (MapValidationError, OSError, urllib.error.URLError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
