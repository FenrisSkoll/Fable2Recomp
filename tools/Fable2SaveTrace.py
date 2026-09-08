#!/usr/bin/env python3
"""Snapshot and diagnose Fable II native save captures without reading payload data."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


EVENT_SCHEMA_VERSION = 1
REPORT_SCHEMA_VERSION = 1
SNAPSHOT_SCHEMA_VERSION = 1
NATIVE_XUID = "B13EBABEBABEBABE"
TITLE_ID = "4D5307F1"
SLOT = "Hero000"
FRESH_REQUIRED_PAYLOAD = (
    "chaptersave.bin",
    "herosave.bin",
    "mainsave.bin",
    "saveuid.bin",
    "texturemorphs.bin",
)
CONDITIONAL_PAYLOAD = (
    "Fable2PubInfo.xml",
    "failquestsave.bin",
)
EXPECTED_PAYLOAD = FRESH_REQUIRED_PAYLOAD + CONDITIONAL_PAYLOAD
FAILURE_CLASSES = (
    "guest_never_attempted_payload_save",
    "incorrect_profile_or_device_state",
    "content_create_result_mismatch",
    "content_metadata_mismatch",
    "path_translation_failure",
    "file_create_semantics_mismatch",
    "write_semantics_mismatch",
    "overlapped_completion_mismatch",
    "flush_or_close_mismatch",
    "rename_or_replace_mismatch",
    "reload_enumeration_mismatch",
    "unknown",
)


class CaptureError(ValueError):
    """A capture or command-line contract is invalid."""


def canonical(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def is_within(path: Path, root: Path) -> bool:
    try:
        canonical(path).relative_to(canonical(root))
        return True
    except ValueError:
        return False


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest().upper()


def snapshot_tree(root: Path) -> dict[str, Any]:
    root = canonical(root)
    if not root.is_dir():
        raise CaptureError(f"save root is not a directory: {root}")

    files: list[dict[str, Any]] = []
    directories: list[str] = []
    for path in sorted(root.rglob("*"), key=lambda value: value.as_posix().casefold()):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise CaptureError(f"save root contains a symbolic link: {path}")
        if path.is_dir():
            directories.append(relative)
        elif path.is_file():
            stat = path.stat()
            files.append(
                {
                    "path": relative,
                    "size": stat.st_size,
                    "sha256": sha256_file(path),
                    "mtime_ns": stat.st_mtime_ns,
                }
            )
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "root": str(root),
        "directories": directories,
        "files": files,
        "modification_order": [
            item["path"]
            for item in sorted(
                files, key=lambda item: (item["mtime_ns"], item["path"].casefold())
            )
        ],
    }


def write_json(path: Path, value: dict[str, Any]) -> None:
    path = canonical(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, json.JSONDecodeError) as error:
        raise CaptureError(f"could not read JSON '{path}': {error}") from error
    if not isinstance(value, dict):
        raise CaptureError(f"JSON root is not an object: {path}")
    return value


def load_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError as error:
                    raise CaptureError(
                        f"invalid NDJSON at {path}:{line_number}: {error}"
                    ) from error
                if not isinstance(event, dict):
                    raise CaptureError(f"event at {path}:{line_number} is not an object")
                validate_event(event, path, line_number)
                events.append(event)
    except OSError as error:
        raise CaptureError(f"could not read trace '{path}': {error}") from error

    sequences = [event["sequence"] for event in events]
    if sequences != list(range(1, len(events) + 1)):
        raise CaptureError(
            "trace sequence numbers are not contiguous from 1; capture may be truncated "
            "or combined from multiple runs"
        )
    return events


def validate_event(event: dict[str, Any], path: Path, line_number: int) -> None:
    required = {
        "schema_version": int,
        "sequence": int,
        "relative_ns": int,
        "guest_thread_id": int,
        "guest_lr": int,
        "caller_guest_pc": int,
        "caller_pc_basis": str,
        "operation": str,
        "phase": str,
    }
    for name, expected_type in required.items():
        if name not in event or not isinstance(event[name], expected_type):
            raise CaptureError(
                f"event at {path}:{line_number} has invalid or missing '{name}'"
            )
    if event["schema_version"] != EVENT_SCHEMA_VERSION:
        raise CaptureError(
            f"unsupported event schema {event['schema_version']} at {path}:{line_number}"
        )
    if event["caller_pc_basis"] != "lr_minus_4":
        raise CaptureError(f"unknown caller_pc_basis at {path}:{line_number}")


def event_result(event: dict[str, Any]) -> int | None:
    for key in ("operation_result", "result"):
        value = event.get(key)
        if isinstance(value, int):
            return value & 0xFFFFFFFF
    return None


def normalized_host_path(value: Any) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    return canonical(Path(value))


def first_event(events: Iterable[dict[str, Any]], predicate: Any) -> dict[str, Any] | None:
    return next((event for event in events if predicate(event)), None)


def compare_snapshots(before: dict[str, Any] | None, after: dict[str, Any]) -> dict[str, Any]:
    before_files = {item["path"]: item for item in (before or {}).get("files", [])}
    after_files = {item["path"]: item for item in after.get("files", [])}
    added = sorted(set(after_files) - set(before_files), key=str.casefold)
    removed = sorted(set(before_files) - set(after_files), key=str.casefold)
    changed = sorted(
        (
            path
            for path in set(before_files) & set(after_files)
            if before_files[path]["sha256"] != after_files[path]["sha256"]
            or before_files[path]["size"] != after_files[path]["size"]
        ),
        key=str.casefold,
    )
    metadata_changed = sorted(
        (
            path
            for path in set(before_files) & set(after_files)
            if before_files[path]["sha256"] == after_files[path]["sha256"]
            and before_files[path]["size"] == after_files[path]["size"]
            and before_files[path].get("mtime_ns") != after_files[path].get("mtime_ns")
        ),
        key=str.casefold,
    )
    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "metadata_changed": metadata_changed,
    }


def slot_paths(names: Iterable[str]) -> tuple[str, ...]:
    base = f"{NATIVE_XUID}/{TITLE_ID}/00000001/{SLOT}"
    return tuple(f"{base}/{name}" for name in names)


def expected_slot_paths() -> tuple[str, ...]:
    return slot_paths(FRESH_REQUIRED_PAYLOAD)


def conditional_slot_paths() -> tuple[str, ...]:
    return slot_paths(CONDITIONAL_PAYLOAD)


def expected_header_path() -> str:
    return f"{NATIVE_XUID}/{TITLE_ID}/Headers/00000001/{SLOT}.header"


def observe_restart(events: list[dict[str, Any]]) -> dict[str, Any]:
    successful_enumerations = [
        event
        for event in events
        if event["operation"] == "XamContentCreateEnumerator"
        and event["phase"] == "result"
        and event_result(event) == 0
        and isinstance(event.get("item_count"), int)
    ]
    enumerated_item_count_max = max(
        (int(event["item_count"]) for event in successful_enumerations),
        default=0,
    )

    requests = {
        event["sequence"]: event
        for event in events
        if event["operation"] == "NtCreateFile" and event["phase"] == "request"
    }
    opened_names: set[str] = set()
    for event in events:
        if (
            event["operation"] != "NtCreateFile"
            or event["phase"] != "result"
            or event_result(event) != 0
            or event.get("file_action") != 1
        ):
            continue
        request = requests.get(event.get("request_sequence"))
        if not request or int(request.get("desired_access", 0)) & 0x80000000 == 0:
            continue
        guest_path = str(request.get("guest_path", "")).replace("\\", "/")
        opened_names.add(guest_path.rsplit("/", 1)[-1].casefold())

    required_payload_opened = [
        name for name in FRESH_REQUIRED_PAYLOAD if name.casefold() in opened_names
    ]
    return {
        "enumerated_item_count_max": enumerated_item_count_max,
        "required_payload_opened": required_payload_opened,
        "all_required_payload_opened": len(required_payload_opened)
        == len(FRESH_REQUIRED_PAYLOAD),
        "nt_read_file_traced": any(
            event["operation"] == "NtReadFile" for event in events
        ),
    }


def observe_update(
    events: list[dict[str, Any]], comparison: dict[str, Any]
) -> dict[str, Any]:
    content_write_mounts = [
        event
        for event in events
        if event["operation"] == "XamContentCreate"
        and event["phase"] == "request"
        and int(event.get("flags", 0)) & 4
    ]
    write_requests = [
        event
        for event in events
        if event["operation"] == "NtWriteFile" and event["phase"] == "request"
    ]
    write_results = {
        event.get("request_sequence"): event
        for event in events
        if event["operation"] == "NtWriteFile" and event["phase"] == "result"
    }

    files_written: list[str] = []
    seen_written: set[str] = set()
    for request in write_requests:
        guest_path = str(request.get("guest_path", "")).replace("\\", "/")
        name = guest_path.rsplit("/", 1)[-1]
        folded_name = name.casefold()
        if name and folded_name not in seen_written:
            files_written.append(name)
            seen_written.add(folded_name)

    missing_write_results = [
        request
        for request in write_requests
        if request["sequence"] not in write_results
    ]
    completed_writes = [
        write_results[request["sequence"]]
        for request in write_requests
        if request["sequence"] in write_results
    ]
    short_writes = [
        event
        for event in completed_writes
        if event.get("actual_bytes") != event.get("requested_bytes")
    ]
    failed_writes = [
        event
        for event in completed_writes
        if int(event.get("operation_result", 0)) & 0xFFFFFFFF
        or int(event.get("io_status", 0)) & 0xFFFFFFFF
    ]

    read_requests = [
        event
        for event in events
        if event["operation"] == "NtReadFile" and event["phase"] == "request"
    ]
    read_results = {
        event.get("request_sequence"): event
        for event in events
        if event["operation"] == "NtReadFile" and event["phase"] == "result"
    }
    completed_reads = [
        read_results[request["sequence"]]
        for request in read_requests
        if request["sequence"] in read_results
    ]
    end_of_file_reads = [
        event
        for event in completed_reads
        if int(event.get("operation_result", 0)) & 0xFFFFFFFF == 0xC0000011
        and int(event.get("io_status", 0)) & 0xFFFFFFFF == 0xC0000011
        and event.get("actual_bytes") == 0
        and event.get("io_information") == 0
    ]
    non_eof_read_failures = [
        event
        for event in completed_reads
        if int(event.get("operation_result", 0)) & 0xFFFFFFFF
        not in (0, 0xC0000011)
        or int(event.get("io_status", 0)) & 0xFFFFFFFF not in (0, 0xC0000011)
    ]

    return {
        "first_content_write_mount_sequence": (
            content_write_mounts[0]["sequence"] if content_write_mounts else None
        ),
        "first_write_sequence": write_requests[0]["sequence"] if write_requests else None,
        "files_written": files_written,
        "write_request_count": len(write_requests),
        "requested_write_bytes": sum(
            int(event.get("requested_bytes", 0)) for event in write_requests
        ),
        "actual_write_bytes": sum(
            int(event.get("actual_bytes", 0)) for event in completed_writes
        ),
        "missing_write_result_count": len(missing_write_results),
        "short_write_count": len(short_writes),
        "failed_write_count": len(failed_writes),
        "all_writes_completed": bool(write_requests)
        and not missing_write_results
        and not short_writes
        and not failed_writes,
        "read_request_count": len(read_requests),
        "missing_read_result_count": len(read_requests) - len(completed_reads),
        "end_of_file_read_count": len(end_of_file_reads),
        "non_eof_read_failure_count": len(non_eof_read_failures),
        "content_changed_paths": list(comparison.get("changed", [])),
        "metadata_changed_paths": list(comparison.get("metadata_changed", [])),
    }


def classify_capture(
    events: list[dict[str, Any]], save_root: Path, snapshot: dict[str, Any]
) -> tuple[list[str], dict[str, Any] | None, list[str], dict[str, Any]]:
    classifications: list[str] = []
    notes: list[str] = []
    first_anomaly: dict[str, Any] | None = None
    restart_observation = observe_restart(events)

    def add(classification: str, event: dict[str, Any] | None, note: str) -> None:
        nonlocal first_anomaly
        if classification not in classifications:
            classifications.append(classification)
        if event is not None and (
            first_anomaly is None or event["sequence"] < first_anomaly["sequence"]
        ):
            first_anomaly = event
        notes.append(note)

    content_requests = [
        event
        for event in events
        if event["operation"] == "XamContentCreate" and event["phase"] == "request"
    ]
    content_results = [
        event
        for event in events
        if event["operation"] == "XamContentCreate"
        and event["phase"] == "operation_result"
    ]
    if not content_requests:
        add(
            "guest_never_attempted_payload_save",
            None,
            "No XamContentCreate saved-game request was captured.",
        )
    else:
        request = content_requests[0]
        if request.get("profile_xuid") != NATIVE_XUID or request.get("device_id") not in (0, 1):
            add(
                "incorrect_profile_or_device_state",
                request,
                "Captured profile XUID or content device differs from the native contract.",
            )
        if request.get("file_name") != SLOT or request.get("title_id") not in (
            0xFFFFFFFF,
            int(TITLE_ID, 16),
        ):
            add(
                "content_metadata_mismatch",
                request,
                "Saved-game slot name or title ID differs from the expected Hero000/TU1 contract.",
            )

    failed_content = first_event(
        content_results, lambda event: event_result(event) not in (None, 0)
    )
    if failed_content:
        add(
            "content_create_result_mismatch",
            failed_content,
            "XamContentCreate completed with a non-success result.",
        )

    pending_requests = {
        event["sequence"]: event
        for event in events
        if event["phase"] == "request"
        and isinstance(event.get("overlapped"), int)
        and not isinstance(event.get("overlapped"), bool)
        and event["overlapped"] != 0
    }
    completed_requests = {
        event.get("request_sequence")
        for event in events
        if event["phase"] == "overlapped_completion"
    }
    missing_completion = next(
        (event for sequence, event in pending_requests.items() if sequence not in completed_requests),
        None,
    )
    if missing_completion:
        add(
            "overlapped_completion_mismatch",
            missing_completion,
            "An overlapped save/content request has no captured completion.",
        )

    for event in events:
        host_path = normalized_host_path(event.get("host_path"))
        if host_path and not is_within(host_path, save_root):
            add(
                "path_translation_failure",
                event,
                f"Resolved host path escapes the configured save root: {host_path}",
            )
            break

    failed_create = first_event(
        events,
        lambda event: event["operation"] == "NtCreateFile"
        and event["phase"] == "result"
        and event_result(event) not in (None, 0),
    )
    if failed_create:
        add(
            "file_create_semantics_mismatch",
            failed_create,
            "NtCreateFile returned a failing status for a save path.",
        )

    bad_write = first_event(
        events,
        lambda event: event["operation"] == "NtWriteFile"
        and event["phase"] == "result"
        and (
            (event.get("operation_result", 0) & 0xFFFFFFFF) != 0
            or event.get("actual_bytes", 0) != event.get("requested_bytes", 0)
        ),
    )
    if bad_write:
        add(
            "write_semantics_mismatch",
            bad_write,
            "NtWriteFile failed or completed fewer bytes than requested.",
        )

    failed_flush_close = first_event(
        events,
        lambda event: event["operation"] in ("NtFlushBuffersFile", "XamContentFlush", "NtClose", "XamContentClose")
        and event["phase"] in ("result", "operation_result")
        and event_result(event) not in (None, 0),
    )
    if failed_flush_close:
        add(
            "flush_or_close_mismatch",
            failed_flush_close,
            "A save flush or close operation returned failure.",
        )

    rename_requests = {
        event.get("request_sequence")
        for event in events
        if event["operation"] == "NtSetInformationFile"
        and event["phase"] == "rename_target"
    }
    failed_rename = first_event(
        events,
        lambda event: event["operation"] == "NtSetInformationFile"
        and event["phase"] == "result"
        and event.get("request_sequence") in rename_requests
        and event_result(event) not in (None, 0),
    )
    if failed_rename:
        add(
            "rename_or_replace_mismatch",
            failed_rename,
            "A save metadata/rename/truncate operation returned failure.",
        )

    file_paths = {item["path"] for item in snapshot["files"]}
    if content_requests and expected_header_path() not in file_paths:
        add(
            "content_metadata_mismatch",
            content_results[-1] if content_results else content_requests[-1],
            f"Expected native content header is missing: {expected_header_path()}",
        )
    missing_required = [path for path in expected_slot_paths() if path not in file_paths]
    missing_conditional = [
        path for path in conditional_slot_paths() if path not in file_paths
    ]
    missing_required_names = {
        Path(path).name.casefold() for path in missing_required
    }
    missing_required_attempts = [
        event
        for event in events
        if event["operation"] in ("NtCreateFile", "NtWriteFile")
        and any(
            name in str(event.get("guest_path", "")).casefold()
            for name in missing_required_names
        )
    ]
    if missing_required and content_requests and not missing_required_attempts:
        add(
            "guest_never_attempted_payload_save",
            content_results[-1] if content_results else content_requests[-1],
            "Content creation occurred, but no missing required fresh-slot payload "
            "file was created or written.",
        )
    if missing_required:
        notes.append("Missing required fresh-slot files: " + ", ".join(missing_required))
    if missing_conditional:
        notes.append(
            "Conditional payload files not present (not a fresh-slot failure): "
            + ", ".join(missing_conditional)
        )
    if restart_observation["enumerated_item_count_max"] > 0:
        notes.append(
            "Restart saved-game enumeration succeeded with maximum item_count "
            f"{restart_observation['enumerated_item_count_max']}."
        )
    if restart_observation["all_required_payload_opened"]:
        if restart_observation["nt_read_file_traced"]:
            notes.append(
                "All required fresh-slot payload files were opened with read access, "
                "and NtReadFile activity was captured."
            )
        else:
            notes.append(
                "All required fresh-slot payload files were opened with read access; "
                "NtReadFile is not traced in this capture, so byte-level reads and "
                "meaningful in-game state require runtime observation."
            )

    if not classifications:
        classifications.append("unknown")
        if not missing_required and restart_observation["enumerated_item_count_max"] == 0:
            notes.append(
                "The captured slot contains the required fresh-slot payload; restart "
                "enumeration/loading remains required."
            )
        elif not missing_required:
            notes.append(
                "No save-path semantic mismatch was identified during restart "
                "enumeration and payload open."
            )
        else:
            notes.append("No decisive semantic mismatch was identified from this capture.")

    classifications.sort(key=FAILURE_CLASSES.index)
    return classifications, first_anomaly, notes, restart_observation


def build_report(
    trace_path: Path,
    metadata_path: Path,
    save_root: Path,
    baseline_path: Path | None,
) -> dict[str, Any]:
    events = load_events(trace_path)
    metadata = load_json(metadata_path)
    if metadata.get("schema_version") != 1 or metadata.get("event_schema_version") != 1:
        raise CaptureError("unsupported or missing save trace run metadata schema")
    if metadata.get("contains_payload_bytes") is not False:
        raise CaptureError("trace metadata does not affirm payload-free capture")

    save_root = canonical(save_root)
    after = snapshot_tree(save_root)
    before = load_json(baseline_path) if baseline_path else None
    if before and before.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
        raise CaptureError("unsupported baseline snapshot schema")
    comparison = compare_snapshots(before, after)
    classifications, first_anomaly, notes, restart_observation = classify_capture(
        events, save_root, after
    )
    update_observation = observe_update(events, comparison)
    if update_observation["all_writes_completed"]:
        notes.append(
            "All captured payload writes completed successfully: "
            f"{update_observation['write_request_count']} requests, "
            f"{update_observation['actual_write_bytes']} bytes returned."
        )
    if update_observation["end_of_file_read_count"]:
        notes.append(
            "Observed expected end-of-file read completions: "
            f"{update_observation['end_of_file_read_count']}."
        )

    operations = Counter(event["operation"] for event in events)
    phases = Counter(event["phase"] for event in events)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "trace_event_schema_version": EVENT_SCHEMA_VERSION,
        "save_root": str(save_root),
        "trace_path": str(canonical(trace_path)),
        "metadata_path": str(canonical(metadata_path)),
        "baseline_path": str(canonical(baseline_path)) if baseline_path else None,
        "event_count": len(events),
        "operations": dict(sorted(operations.items())),
        "phases": dict(sorted(phases.items())),
        "classifications": classifications,
        "first_anomaly": first_anomaly,
        "notes": notes,
        "restart_observation": restart_observation,
        "update_observation": update_observation,
        "tree_comparison": comparison,
        "payload_contract": {
            "required_fresh_slot": list(FRESH_REQUIRED_PAYLOAD),
            "conditional_later_state": list(CONDITIONAL_PAYLOAD),
        },
        "save_snapshot": after,
    }


def command_snapshot(args: argparse.Namespace) -> int:
    write_json(args.output, snapshot_tree(args.root))
    print(f"Wrote save snapshot: {canonical(args.output)}")
    return 0


def command_report(args: argparse.Namespace) -> int:
    report = build_report(args.trace, args.metadata, args.save_root, args.baseline)
    write_json(args.output, report)
    print(f"Wrote save diagnostic report: {canonical(args.output)}")
    print("Classification: " + ", ".join(report["classifications"]))
    anomaly = report["first_anomaly"]
    if anomaly:
        print(
            "First anomaly: sequence "
            f"{anomaly['sequence']} {anomaly['operation']}/{anomaly['phase']}"
        )
    return 0


def command_validate_schemas(args: argparse.Namespace) -> int:
    for path in args.schemas:
        schema = load_json(path)
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise CaptureError(f"schema lacks the expected draft identifier: {path}")
        if not isinstance(schema.get("$id"), str) or not schema.get("$id"):
            raise CaptureError(f"schema lacks a stable $id: {path}")
        if schema.get("type") != "object":
            raise CaptureError(f"schema root must describe an object: {path}")
    print(f"Validated {len(args.schemas)} schema files.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Snapshot and diagnose payload-free Fable II native-save captures."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot = subparsers.add_parser("snapshot", help="hash a save tree without copying data")
    snapshot.add_argument("--root", type=Path, required=True)
    snapshot.add_argument("--output", type=Path, required=True)
    snapshot.set_defaults(func=command_snapshot)

    report = subparsers.add_parser("report", help="summarize a trace and compare its save tree")
    report.add_argument("--trace", type=Path, required=True)
    report.add_argument("--metadata", type=Path, required=True)
    report.add_argument("--save-root", type=Path, required=True)
    report.add_argument("--baseline", type=Path)
    report.add_argument("--output", type=Path, required=True)
    report.set_defaults(func=command_report)

    validate = subparsers.add_parser(
        "validate-schemas", help="check checked-in schema documents"
    )
    validate.add_argument("schemas", type=Path, nargs="+")
    validate.set_defaults(func=command_validate_schemas)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except CaptureError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
