import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("gpu_config", Path(__file__).resolve().parents[1] / "tools/Fable2GpuConfig.py")
gpu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gpu)


class GpuConfigTests(unittest.TestCase):
    def test_copy_refuses_existing_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, dest = root / "source", root / "dest"
            source.mkdir()
            (source / "save").write_bytes(b"private synthetic test")
            before = gpu.inventory(source)
            gpu.guarded_copy(source, dest, before)
            self.assertEqual(gpu.inventory(dest), before)
            with self.assertRaises(ValueError):
                gpu.guarded_copy(source, dest, before)
            self.assertEqual(gpu.inventory(source), before)

    def test_copy_detects_changed_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            before = gpu.inventory(source)
            (source / "changed").write_bytes(b"x")
            with self.assertRaises(ValueError):
                gpu.guarded_copy(source, Path(tmp) / "dest", before)
            self.assertFalse((Path(tmp) / "dest").exists())

    def records(self):
        return [gpu.PREFIX + json.dumps({"schema": "rex-gpu-config-v1", "run_id": "test",
                 "stage": stage, "fields": {key: "unavailable" for key in gpu.REQUIRED[stage]}})
                for stage in sorted(gpu.STAGES)]

    def test_partial_and_unknown_are_distinct(self):
        records, errors = gpu.parse_records(self.records(), "test")
        self.assertEqual(errors, [])
        self.assertEqual(records["device"]["rov_supported"], "unavailable")
        self.assertTrue(gpu.parse_records(self.records()[:-1], "test")[1])
        self.assertTrue(gpu.parse_records(self.records(), "wrong-run")[1])

    def test_duplicates_and_missing_fields_fail(self):
        lines = self.records()
        self.assertTrue(gpu.parse_records(lines + lines[:1], "test")[1])
        record = json.loads(lines[0].split(gpu.PREFIX)[1])
        record["fields"] = {}
        lines[0] = gpu.PREFIX + json.dumps(record)
        self.assertTrue(gpu.parse_records(lines, "test")[1])

    def test_loaded_identity_mismatch_and_missing_exit_fail(self):
        expected = {"path": "C:/test/rexruntime.dll", "bytes": 20, "sha256": "ABC"}
        prep = {"run_id": "test", "staged": {"rexruntime.dll": expected}}
        process = {"run_id": "test", "pid": 42, "start_utc": "start", "end_utc": "end",
                   "exit_code": 0, "modules": {"rexruntime.dll": dict(expected)}}
        self.assertEqual(gpu.validate_loaded(prep, process), [])
        process["modules"]["rexruntime.dll"]["sha256"] = "wrong"
        self.assertTrue(gpu.validate_loaded(prep, process))
        process["modules"]["rexruntime.dll"] = dict(expected)
        process["exit_code"] = None
        self.assertTrue(gpu.validate_loaded(prep, process))

    def test_existing_session_rejected_before_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "out/nr0b1/sessions/test").mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, "already exists"):
                gpu.prepare(repo, repo, "test")


if __name__ == "__main__":
    unittest.main()
