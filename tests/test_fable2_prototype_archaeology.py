from __future__ import annotations

import importlib.util
import struct
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "Fable2PrototypeArchaeology.py"
SPEC = importlib.util.spec_from_file_location("fable2_prototype_archaeology", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
arch = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = arch
SPEC.loader.exec_module(arch)


class PrototypeArchaeologyTests(unittest.TestCase):
    def test_magic_takes_precedence_over_extension(self) -> None:
        magic = arch.detect_magic(b"XEX2" + bytes(60))
        self.assertEqual("XEX2", magic["name"])
        self.assertEqual("executable", arch.classify_file(Path("misnamed.txt"), magic))

    def test_debug_category_routing(self) -> None:
        categories = arch.debug_categories(r"D:\build\fable\renderer\Shader.cpp")
        self.assertIn("source-file", categories)
        self.assertIn("source-build-path", categories)
        self.assertIn("subsystem-terminology", categories)
        self.assertIn("pdb-codeview", arch.debug_categories(r"D:\symbols\fable2.pdb"))
        self.assertEqual({"Debug.SetDrawGameFPS"}, arch.api_names("Debug.SetDrawGameFPS(), toggle:true"))

    def test_xex_metadata_parser(self) -> None:
        data = bytearray(0x500)
        data[:4] = b"XEX2"
        struct.pack_into(">IIIII", data, 4, 1, 0x400, 0, 0x100, 6)
        headers = (
            (0x00010201, 0x82000000),
            (0x00010100, 0x82123450),
            (0x00040006, 0x300),
            (0x000003FF, 0x340),
            (0x00018002, 0x350),
            (0x000183FF, 0x360),
        )
        for index, (key, value) in enumerate(headers):
            struct.pack_into(">II", data, 0x18 + index * 8, key, value)
        struct.pack_into(">II", data, 0x100, 0x184, 0x01620000)
        struct.pack_into(">II", data, 0x100 + 0x10C, 0x00000400, 0x82000000)
        struct.pack_into(">I", data, 0x100 + 0x180, 0)
        struct.pack_into(">IIII4B I", data, 0x300, 0x716F0A0D, 0x0000011A, 0x0000001A, 0x4D5307F1, 0, 0, 1, 1, 0)
        struct.pack_into(">IHH", data, 0x340, 8, 1, 2)
        struct.pack_into(">II", data, 0x350, 0x12345678, 0x4A53C85A)
        pe_name = b"fable2.exe\0"
        struct.pack_into(">I", data, 0x360, 4 + len(pe_name))
        data[0x364 : 0x364 + len(pe_name)] = pe_name

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "default.xex"
            path.write_bytes(data)
            record = arch.parse_xex(path, "test", "test/default.xex")

        self.assertEqual("0x82000000", record["image_base"])
        self.assertEqual("0x82123450", record["entry_point"])
        self.assertEqual("0x4D5307F1", record["execution_info"]["title_id"])
        self.assertEqual("0.0.1.26", record["execution_info"]["version"]["display"])
        self.assertEqual("normal", record["file_format"]["encryption"]["name"])
        self.assertEqual("normal", record["file_format"]["compression"]["name"])
        self.assertEqual("fable2.exe", record["original_pe_name"])

    def test_explicit_generation_timestamp_is_stable(self) -> None:
        first = arch.artifact("test", "2026-09-11T00:00:00Z", value=1)
        second = arch.artifact("test", "2026-09-11T00:00:00Z", value=1)
        self.assertEqual(first, second)

    def test_windows_filetime_epoch_is_representable(self) -> None:
        value = arch.iso_timestamp_ns(-11_644_473_600 * 1_000_000_000)
        self.assertEqual("1601-01-01T00:00:00.000000000Z", value)

    def test_ppc_address_materialization_recovers_lis_pairs(self) -> None:
        lis_r11 = (15 << 26) | (11 << 21) | 0x820B
        addi_r3_r11 = (14 << 26) | (3 << 21) | (11 << 16) | 0x7FFC
        lis_r12 = (15 << 26) | (12 << 21) | 0x8210
        ori_r3_r12 = (24 << 26) | (12 << 21) | (3 << 16) | 0x1A50
        self.assertEqual(
            [0x820B7FFC, 0x82101A50],
            arch.materialized_addresses([lis_r11, addi_r3_r11, lis_r12, ori_r3_r12]),
        )


if __name__ == "__main__":
    unittest.main()
