from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.Fable2SaveTrace import (
    CaptureError,
    EXPECTED_PAYLOAD,
    NATIVE_XUID,
    SLOT,
    TITLE_ID,
    build_report,
    compare_snapshots,
    expected_header_path,
    load_events,
    snapshot_tree,
)


def event(sequence: int, operation: str, phase: str, **fields: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": 1,
        "sequence": sequence,
        "relative_ns": sequence * 100,
        "guest_thread_id": 7,
        "guest_lr": 0x82CC702C,
        "caller_guest_pc": 0x82CC7028,
        "caller_pc_basis": "lr_minus_4",
        "operation": operation,
        "phase": phase,
    }
    value.update(fields)
    return value


class SaveTraceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.save_root = self.root / "save-root"
        self.save_root.mkdir()
        self.trace = self.root / "save-trace-events-v1.ndjson"
        self.metadata = self.root / "save-trace-run-v1.json"
        self.baseline = self.root / "before.json"
        self.metadata.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "event_schema_version": 1,
                    "started_utc": "2026-09-02T00:00:00Z",
                    "process_id": 123,
                    "trace_directory": str(self.root),
                    "contains_payload_bytes": False,
                }
            ),
            encoding="utf-8",
        )
        self.baseline.write_text(json.dumps(snapshot_tree(self.save_root)), encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_events(self, events: list[dict[str, object]]) -> None:
        self.trace.write_text(
            "".join(json.dumps(item) + "\n" for item in events), encoding="utf-8"
        )

    def create_complete_slot(self) -> None:
        slot = self.save_root / NATIVE_XUID / TITLE_ID / "00000001" / SLOT
        slot.mkdir(parents=True)
        for index, name in enumerate(EXPECTED_PAYLOAD, start=1):
            (slot / name).write_bytes(bytes([index]) * (index + 3))
        self.create_header()

    def create_header(self) -> None:
        header = self.save_root / NATIVE_XUID / TITLE_ID / "Headers" / "00000001"
        header.mkdir(parents=True)
        (header / f"{SLOT}.header").write_bytes(b"header")

    def content_events(self, *, with_completion: bool = True) -> list[dict[str, object]]:
        result = [
            event(
                1,
                "XamContentCreate",
                "request",
                profile_xuid=NATIVE_XUID,
                device_id=1,
                title_id=int(TITLE_ID, 16),
                file_name=SLOT,
                overlapped=0x1000,
            ),
            event(
                2,
                "XamContentCreate",
                "operation_result",
                request_sequence=1,
                result=0,
            ),
        ]
        if with_completion:
            result.append(
                event(
                    3,
                    "XamContentCreate",
                    "overlapped_completion",
                    request_sequence=1,
                    result=0,
                )
            )
        return result

    def test_snapshot_hashes_files_without_embedding_payload(self) -> None:
        payload = self.save_root / "example.bin"
        payload.write_bytes(b"private payload marker")
        snapshot = snapshot_tree(self.save_root)
        self.assertEqual(snapshot["files"][0]["path"], "example.bin")
        self.assertEqual(snapshot["files"][0]["size"], 22)
        self.assertNotIn("private payload marker", json.dumps(snapshot))
        self.assertEqual(snapshot["modification_order"], ["example.bin"])

    def test_snapshot_comparison_reports_timestamp_only_changes(self) -> None:
        before = {
            "files": [
                {"path": "same.bin", "size": 4, "sha256": "A", "mtime_ns": 1}
            ]
        }
        after = {
            "files": [
                {"path": "same.bin", "size": 4, "sha256": "A", "mtime_ns": 2}
            ]
        }
        comparison = compare_snapshots(before, after)
        self.assertEqual(comparison["changed"], [])
        self.assertEqual(comparison["metadata_changed"], ["same.bin"])

    def test_complete_structural_capture_remains_unknown_until_restart(self) -> None:
        self.create_complete_slot()
        events = self.content_events()
        next_sequence = len(events) + 1
        events.append(
            event(
                next_sequence,
                "NtWriteFile",
                "request",
                guest_path="Save:\\Hero000\\mainsave.bin",
                requested_bytes=16,
                overlapped=0,
            )
        )
        events.append(
            event(
                next_sequence + 1,
                "NtWriteFile",
                "result",
                request_sequence=next_sequence,
                requested_bytes=16,
                actual_bytes=16,
                operation_result=0,
            )
        )
        self.write_events(events)
        report = build_report(
            self.trace, self.metadata, self.save_root, self.baseline
        )
        self.assertEqual(report["classifications"], ["unknown"])
        self.assertIn("restart", " ".join(report["notes"]).lower())

    def test_fresh_slot_does_not_require_later_conditional_payloads(self) -> None:
        slot = self.save_root / NATIVE_XUID / TITLE_ID / "00000001" / SLOT
        slot.mkdir(parents=True)
        for name in (
            "chaptersave.bin",
            "herosave.bin",
            "mainsave.bin",
            "saveuid.bin",
            "texturemorphs.bin",
        ):
            (slot / name).write_bytes(b"synthetic")
        self.create_header()

        events = self.content_events()
        events.extend(
            [
                event(
                    4,
                    "NtWriteFile",
                    "request",
                    guest_path="Save:\\mainsave.bin",
                    requested_bytes=9,
                    overlapped=0,
                ),
                event(
                    5,
                    "NtWriteFile",
                    "result",
                    request_sequence=4,
                    requested_bytes=9,
                    actual_bytes=9,
                    operation_result=0,
                ),
            ]
        )
        self.write_events(events)

        report = build_report(
            self.trace, self.metadata, self.save_root, self.baseline
        )
        notes = " ".join(report["notes"]).lower()
        self.assertEqual(report["classifications"], ["unknown"])
        self.assertNotIn("missing expected files", notes)
        self.assertIn("conditional", notes)
        self.assertEqual(
            report["payload_contract"]["required_fresh_slot"],
            [
                "chaptersave.bin",
                "herosave.bin",
                "mainsave.bin",
                "saveuid.bin",
                "texturemorphs.bin",
            ],
        )
        self.assertEqual(
            report["payload_contract"]["conditional_later_state"],
            ["Fable2PubInfo.xml", "failquestsave.bin"],
        )

    def test_reload_capture_reports_enumeration_and_payload_opens(self) -> None:
        slot = self.save_root / NATIVE_XUID / TITLE_ID / "00000001" / SLOT
        slot.mkdir(parents=True)
        required = (
            "chaptersave.bin",
            "herosave.bin",
            "mainsave.bin",
            "saveuid.bin",
            "texturemorphs.bin",
        )
        for name in required:
            (slot / name).write_bytes(b"synthetic")
        self.create_header()

        events = [
            event(1, "XamContentCreateEnumerator", "request"),
            event(
                2,
                "XamContentCreateEnumerator",
                "result",
                request_sequence=1,
                item_count=1,
                result=0,
            ),
            event(
                3,
                "XamContentCreate",
                "request",
                profile_xuid=NATIVE_XUID,
                device_id=1,
                file_name=SLOT,
                title_id=int(TITLE_ID, 16),
                flags=3,
            ),
            event(
                4,
                "XamContentCreate",
                "operation_result",
                request_sequence=3,
                result=0,
            ),
        ]
        sequence = 5
        for name in required:
            events.extend(
                [
                    event(
                        sequence,
                        "NtCreateFile",
                        "request",
                        guest_path=f"Save:\\{name}",
                        desired_access=0x80100080,
                        creation_disposition=1,
                    ),
                    event(
                        sequence + 1,
                        "NtCreateFile",
                        "result",
                        request_sequence=sequence,
                        guest_path=f"Save:\\{name}",
                        file_action=1,
                        result=0,
                    ),
                ]
            )
            sequence += 2
        self.write_events(events)

        report = build_report(
            self.trace, self.metadata, self.save_root, self.baseline
        )
        observation = report["restart_observation"]
        self.assertEqual(observation["enumerated_item_count_max"], 1)
        self.assertTrue(observation["all_required_payload_opened"])
        self.assertFalse(observation["nt_read_file_traced"])
        notes = " ".join(report["notes"]).lower()
        self.assertIn("enumeration succeeded", notes)
        self.assertIn("ntreadfile is not traced", notes)
        self.assertNotIn("restart enumeration/loading remains required", notes)

    def test_update_capture_reports_complete_payload_writes(self) -> None:
        self.create_complete_slot()
        events = self.content_events()
        events[0]["flags"] = 4
        events.extend(
            [
                event(
                    4,
                    "NtWriteFile",
                    "request",
                    guest_path="Save:\\mainsave.bin",
                    requested_bytes=2048,
                    offset=0,
                ),
                event(
                    5,
                    "NtWriteFile",
                    "result",
                    request_sequence=4,
                    requested_bytes=2048,
                    actual_bytes=2048,
                    operation_result=0,
                    io_status=0,
                    io_information=2048,
                ),
                event(
                    6,
                    "NtReadFile",
                    "request",
                    guest_path="Save:\\Fable2PubInfo.xml",
                    requested_bytes=4096,
                ),
                event(
                    7,
                    "NtReadFile",
                    "result",
                    request_sequence=6,
                    requested_bytes=4096,
                    actual_bytes=0,
                    operation_result=0xC0000011,
                    io_status=0xC0000011,
                    io_information=0,
                ),
            ]
        )
        self.write_events(events)

        report = build_report(
            self.trace, self.metadata, self.save_root, self.baseline
        )
        observation = report["update_observation"]
        self.assertEqual(observation["first_content_write_mount_sequence"], 1)
        self.assertEqual(observation["first_write_sequence"], 4)
        self.assertEqual(observation["files_written"], ["mainsave.bin"])
        self.assertEqual(observation["write_request_count"], 1)
        self.assertEqual(observation["requested_write_bytes"], 2048)
        self.assertEqual(observation["actual_write_bytes"], 2048)
        self.assertEqual(observation["missing_write_result_count"], 0)
        self.assertEqual(observation["short_write_count"], 0)
        self.assertEqual(observation["failed_write_count"], 0)
        self.assertTrue(observation["all_writes_completed"])
        self.assertEqual(observation["end_of_file_read_count"], 1)
        self.assertEqual(observation["non_eof_read_failure_count"], 0)

    def test_content_create_without_payload_attempt_is_classified(self) -> None:
        slot = self.save_root / NATIVE_XUID / TITLE_ID / "00000001" / SLOT
        slot.mkdir(parents=True)
        (slot / "saveuid.bin").write_bytes(b"12345678")
        self.create_header()
        self.write_events(self.content_events())
        report = build_report(
            self.trace, self.metadata, self.save_root, self.baseline
        )
        self.assertIn("guest_never_attempted_payload_save", report["classifications"])
        self.assertEqual(report["first_anomaly"]["sequence"], 2)

    def test_missing_header_is_content_metadata_mismatch(self) -> None:
        self.write_events(self.content_events())
        report = build_report(
            self.trace, self.metadata, self.save_root, self.baseline
        )
        self.assertIn("content_metadata_mismatch", report["classifications"])
        self.assertIn(expected_header_path(), " ".join(report["notes"]))

    def test_short_write_is_classified_at_first_write_result(self) -> None:
        self.create_header()
        events = self.content_events()
        events.extend(
            [
                event(
                    4,
                    "NtWriteFile",
                    "request",
                    guest_path="Save:\\Hero000\\herosave.bin",
                    requested_bytes=512,
                    overlapped=0,
                ),
                event(
                    5,
                    "NtWriteFile",
                    "result",
                    request_sequence=4,
                    requested_bytes=512,
                    actual_bytes=128,
                    operation_result=0,
                ),
            ]
        )
        self.write_events(events)
        report = build_report(
            self.trace, self.metadata, self.save_root, self.baseline
        )
        self.assertIn("write_semantics_mismatch", report["classifications"])
        self.assertEqual(report["first_anomaly"]["sequence"], 5)

    def test_host_path_outside_root_is_rejected_by_report(self) -> None:
        self.create_header()
        events = self.content_events()
        events.append(
            event(
                4,
                "NtCreateFile",
                "result",
                guest_path="Save:\\Hero000\\mainsave.bin",
                host_path=str(self.root / "outside" / "mainsave.bin"),
                result=0,
            )
        )
        self.write_events(events)
        report = build_report(
            self.trace, self.metadata, self.save_root, self.baseline
        )
        self.assertIn("path_translation_failure", report["classifications"])
        self.assertEqual(report["first_anomaly"]["sequence"], 4)

    def test_missing_overlapped_completion_is_classified(self) -> None:
        self.create_header()
        self.write_events(self.content_events(with_completion=False))
        report = build_report(
            self.trace, self.metadata, self.save_root, self.baseline
        )
        self.assertIn("overlapped_completion_mismatch", report["classifications"])
        self.assertEqual(report["first_anomaly"]["sequence"], 1)

    def test_non_contiguous_trace_is_rejected(self) -> None:
        self.write_events([event(2, "XamContentCreate", "request")])
        with self.assertRaisesRegex(CaptureError, "not contiguous"):
            load_events(self.trace)

    def test_launcher_is_guarded_and_contains_no_input_automation(self) -> None:
        launcher = (
            Path(__file__).parents[1] / "tools" / "Invoke-Fable2NativeSaveDiagnostic.ps1"
        ).read_text(encoding="utf-8")
        self.assertIn("Assert-DiagnosticPath", launcher)
        self.assertIn("Assert-NoFiles", launcher)
        self.assertIn("Start-Process", launcher)
        self.assertIn("-Wait", launcher)
        self.assertIn("--save_trace_dir=$captureRoot", launcher)
        for forbidden in ("SendKeys", "mouse_event", "keybd_event"):
            self.assertNotIn(forbidden, launcher)

    def test_launcher_has_guarded_fresh_restart_capture(self) -> None:
        launcher = (
            Path(__file__).parents[1] / "tools" / "Invoke-Fable2NativeSaveDiagnostic.ps1"
        ).read_text(encoding="utf-8")
        self.assertIn(
            'ValidateSet("FreshNative", "FreshNativeReload", "XeniaUpdate")',
            launcher,
        )
        self.assertIn('"capture-002"', launcher)
        self.assertIn('"cache-002"', launcher)
        self.assertIn('"state-B-after-write.json"', launcher)
        self.assertIn("Assert-HasFiles -Path $nativeSaveRoot", launcher)


if __name__ == "__main__":
    unittest.main()
