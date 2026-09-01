from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "tools" / "Verify-Fable2GpuReference.py"
SPEC = importlib.util.spec_from_file_location("verify_fable2_gpu_reference", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)

CLEANUP_TIP = "7e8d9e92fff5ca766f9aa12506b6205868e34f62"
PRE_RESEARCH_MAIN = "efd625d0b9635119df85d61d005d754714c2205e"


class MilestoneLineageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory(
            prefix="fable2-gpu-lineage-test-"
        )
        cls.repository = Path(cls.temporary.name) / "lineage.git"
        result = subprocess.run(
            [
                "git",
                "clone",
                "--bare",
                "--shared",
                "--quiet",
                str(REPO_ROOT),
                str(cls.repository),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            raise RuntimeError(f"unable to create lineage fixture: {result.stderr}")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def git(self, *args: str) -> str:
        result = VERIFY.run_git(self.repository, *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.rstrip("\r\n")

    def select_head(self, commit: str, branch: str | None) -> None:
        if branch is None:
            self.git("update-ref", "--no-deref", "HEAD", commit)
            self.assertEqual(self.git("branch", "--show-current"), "")
            return
        reference = f"refs/heads/{branch}"
        self.git("update-ref", reference, commit)
        self.git("symbolic-ref", "HEAD", reference)
        self.assertEqual(self.git("branch", "--show-current"), branch)

    def validate_lineage(self) -> VERIFY.Validation:
        validation = VERIFY.Validation()
        VERIFY.validate_required_milestone(
            self.repository,
            "HEAD",
            VERIFY.G16A_ACCEPTED_COMMIT,
            VERIFY.G16A_ACCEPTED_TREE,
            "G1.6A",
            validation,
        )
        VERIFY.validate_required_milestone(
            self.repository,
            "HEAD",
            VERIFY.G16B_ACCEPTED_COMMIT,
            VERIFY.G16B_ACCEPTED_TREE,
            "G1.6B",
            validation,
        )
        VERIFY.reject_forbidden_ancestor(
            self.repository,
            "HEAD",
            VERIFY.RETIRED_G2A_COMMIT,
            "G1.6",
            validation,
        )
        return validation

    def test_exact_historical_g16b_state_is_accepted(self) -> None:
        self.select_head(
            VERIFY.G16B_ACCEPTED_COMMIT,
            "fable2-native-renderer-g1.6b-static-seam-coverage",
        )
        self.assertEqual(self.validate_lineage().errors, [])

    def test_descendant_integration_branch_is_accepted(self) -> None:
        self.select_head(
            CLEANUP_TIP,
            "fable2-native-renderer-research-integration",
        )
        self.assertEqual(self.validate_lineage().errors, [])

    def test_integrated_main_like_descendant_is_accepted(self) -> None:
        self.select_head(CLEANUP_TIP, "main")
        self.assertEqual(self.validate_lineage().errors, [])

    def test_detached_valid_descendant_is_accepted(self) -> None:
        self.select_head(CLEANUP_TIP, None)
        self.assertEqual(self.validate_lineage().errors, [])

    def test_ref_without_required_lineage_is_rejected_precisely(self) -> None:
        self.select_head(PRE_RESEARCH_MAIN, "pre-research")
        errors = self.validate_lineage().errors
        self.assertTrue(
            any(
                f"G1.6B required accepted milestone {VERIFY.G16B_ACCEPTED_COMMIT} "
                "is not an ancestor" in error
                for error in errors
            ),
            errors,
        )

    def test_retired_checkpoint_is_not_a_milestone_substitute(self) -> None:
        self.select_head(VERIFY.RETIRED_G2A_COMMIT, "checkpoint-substitute")
        errors = self.validate_lineage().errors
        self.assertTrue(
            any("G1.6B required accepted milestone" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any("retired checkpoint" in error for error in errors),
            errors,
        )

    def test_historical_branch_name_alone_cannot_grant_acceptance(self) -> None:
        self.select_head(
            PRE_RESEARCH_MAIN,
            "fable2-native-renderer-g1.6b-static-seam-coverage",
        )
        errors = self.validate_lineage().errors
        self.assertTrue(
            any("required accepted milestone" in error for error in errors),
            errors,
        )

    def test_tampered_evidence_and_milestone_tree_are_rejected(self) -> None:
        coverage_path = (
            REPO_ROOT
            / "docs"
            / "fable2-gpu-reference"
            / "evidence"
            / "static-xdk-seam-coverage.json"
        )
        schema_path = (
            REPO_ROOT
            / "tools"
            / "schemas"
            / "fable2-gpu-static-xdk-seam-coverage-v1.schema.json"
        )
        coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        tampered = copy.deepcopy(coverage)
        tampered["primary_result"] = "TAMPERED"
        schema_validation = VERIFY.Validation()
        VERIFY.validate_with_schema(
            tampered,
            schema,
            "tampered static XDK seam coverage",
            schema_validation,
        )
        self.assertTrue(schema_validation.errors)

        self.select_head(CLEANUP_TIP, "tampered-tree")
        tree_validation = VERIFY.Validation()
        VERIFY.validate_required_milestone(
            self.repository,
            "HEAD",
            VERIFY.G16B_ACCEPTED_COMMIT,
            "0" * 40,
            "G1.6B",
            tree_validation,
        )
        self.assertTrue(
            any("accepted milestone tree mismatch" in error for error in tree_validation.errors),
            tree_validation.errors,
        )

    def test_retired_checkpoint_object_is_not_required(self) -> None:
        self.select_head(CLEANUP_TIP, "checkpoint-object-optional")
        validation = VERIFY.Validation()
        VERIFY.reject_forbidden_ancestor(
            self.repository,
            "HEAD",
            "f" * 40,
            "G1.6",
            validation,
        )
        self.assertEqual(validation.errors, [])

    def test_committed_provenance_uses_git_blob_and_clean_filters(self) -> None:
        validation = VERIFY.Validation()
        VERIFY.validate_committed_entrypoint_provenance(REPO_ROOT, validation)
        self.assertEqual(validation.errors, [])


if __name__ == "__main__":
    unittest.main()
