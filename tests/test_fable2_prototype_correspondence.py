from __future__ import annotations

import importlib.util
import json
import struct
import sys
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
MODULE_PATH = TOOLS / "Fable2PrototypeCorrespondence.py"
SPEC = importlib.util.spec_from_file_location("prototype_correspondence", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
correspondence = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = correspondence
SPEC.loader.exec_module(correspondence)


class BranchNormalizationTests(unittest.TestCase):
    def test_b_and_bl_clear_only_li(self) -> None:
        self.assertEqual(0x48000000, correspondence.normalize_branch_word(0x49FFFFFC))
        self.assertEqual(0x48000001, correspondence.normalize_branch_word(0x49FFFFFD))
        self.assertEqual(0x48000002, correspondence.normalize_branch_word(0x49FFFFFE))
        self.assertEqual(0x48000003, correspondence.normalize_branch_word(0x49FFFFFF))

    def test_bc_clears_only_bd_and_preserves_bo_bi_aa_lk(self) -> None:
        word = 0x4182FFFD
        self.assertEqual(word & 0xFFFF0003, correspondence.normalize_branch_word(word))
        self.assertEqual(word & 0xFFFF0003, correspondence.normalize_branch_word(word ^ 0x00007FFC))

    def test_non_branch_instruction_is_unchanged(self) -> None:
        self.assertEqual(0x3863FFFF, correspondence.normalize_branch_word(0x3863FFFF))

    def test_relative_branch_targets(self) -> None:
        self.assertEqual(0x1020, correspondence.direct_branch_target(0x48000020, 0x1000))
        self.assertEqual(0x0FE0, correspondence.direct_branch_target(0x4BFFFFE0, 0x1000))
        self.assertEqual(0x1020, correspondence.direct_branch_target(0x41820020, 0x1000))


class SyntheticFixtureTests(unittest.TestCase):
    EXPECTED_FIXTURES = {
        "identical-functions-relocated-as-block",
        "branch-normalized-with-exact-neighbour-delta",
        "b-bl-bc-displacement-normalization",
        "duplicate-tiny-leaves-and-thunks",
        "changed-direct-call-target",
        "reordered-neighbouring-functions",
        "one-to-many-and-many-to-one-ambiguity",
        "split-merged-shifted-pdata-boundary",
        "opcode-similar-semantically-different",
        "materialized-string-data-addresses-move",
    }

    def test_all_required_fixtures_pass(self) -> None:
        fixtures = correspondence.run_synthetic_fixtures()
        self.assertEqual(self.EXPECTED_FIXTURES, {fixture["name"] for fixture in fixtures})
        for fixture in fixtures:
            with self.subTest(fixture=fixture["name"]):
                self.assertTrue(fixture["passed"])

    def test_fixture_results_are_deterministic(self) -> None:
        first = correspondence.canonical_json_bytes(correspondence.run_synthetic_fixtures())
        second = correspondence.canonical_json_bytes(correspondence.run_synthetic_fixtures())
        self.assertEqual(first, second)

    def test_duplicate_fingerprints_do_not_accept_many_to_one(self) -> None:
        blr = 0x4E800020
        left = correspondence.synthetic_analysis(
            "left", [(0x1000, [0x38600001, blr]), (0x1010, [0x38600001, blr])]
        )
        right = correspondence.synthetic_analysis("right", [(0x2000, [0x38600001, blr])])
        result = correspondence.match_builds(left, right)
        self.assertEqual([], result["accepted"])

    def test_opcode_only_is_never_accepted(self) -> None:
        blr = 0x4E800020
        left = correspondence.synthetic_analysis(
            "left", [(0x1000, [0x38600001, 0x38800002, 0x38A00003, 0x38C00004, blr])]
        )
        right = correspondence.synthetic_analysis(
            "right", [(0x2000, [0x38600009, 0x3880000A, 0x38A0000B, 0x38C0000C, blr])]
        )
        result = correspondence.match_builds(left, right)
        self.assertEqual([], result["accepted"])
        self.assertEqual("candidate-structural", result["index"][0]["status"])

    def test_materialized_address_pair_is_preserved_as_reference_evidence(self) -> None:
        words = [0x3C60820B, 0x38637FFC, 0x4E800020]
        function = correspondence.synthetic_function(0x1000, words, 0)
        self.assertEqual([(0, 0x820B7FFC)], correspondence.materialized_addresses(words))
        self.assertEqual(1, function.materialized_reference_count)

    def test_executable_fingerprint_uses_versioned_noncontiguous_spans(self) -> None:
        first = correspondence.MemoryBlock(
            ".text", 0x1000, b"AAAA", True, False, True, "a", ""
        )
        adjacent = correspondence.MemoryBlock(
            "tail", 0x1004, b"BBBB", True, False, True, "b", ""
        )
        separated = correspondence.MemoryBlock(
            "other", 0x2000, b"CCCC", True, False, True, "c", ""
        )
        actual = correspondence.executable_fingerprint([first, adjacent, separated])
        digest = correspondence.hashlib.sha256()
        digest.update(b"FABLE2_EXECUTABLE_MEMORY_V1\0")
        digest.update(struct.pack(">I", 2))
        digest.update(struct.pack(">QQB", 0x1000, 8, 5))
        digest.update(b"AAAABBBB")
        digest.update(struct.pack(">QQB", 0x2000, 4, 5))
        digest.update(b"CCCC")
        self.assertEqual(digest.hexdigest().upper(), actual)


if __name__ == "__main__":
    unittest.main()
