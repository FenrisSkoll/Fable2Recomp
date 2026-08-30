from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "Verify-Fable2EntrypointClosure.py"
)
SPEC = importlib.util.spec_from_file_location("verify_entrypoint_closure", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


def site(
    address: str,
    cluster_id: str,
    likelihood: str,
    *,
    recovered: bool,
) -> dict:
    return {
        "site": address,
        "owner_address": "0x00001000",
        "uses_ctr": True,
        "link": False,
        "failures": [] if recovered else ["missing_bound"],
        "selected_table": {} if recovered else None,
        "limit_retry": None,
        "dataflow": {
            "cluster_id": cluster_id,
            "switch_likelihood": likelihood,
            "diagnostic_probe": {
                "report_only": True,
                "hypothesis_complete": False,
                "all_targets_valid": False,
            },
        },
    }


def schema_two_report() -> dict:
    resolved_cluster = "dispatch=bctr|form=relative_offset|reason=none"
    unresolved_cluster = "dispatch=bctr|form=unknown|reason=missing_bound"
    sites = [
        site(
            "0x00001010",
            resolved_cluster,
            "resolved_switch",
            recovered=True,
        ),
        site(
            "0x00001020",
            unresolved_cluster,
            "computed_tail_dispatch",
            recovered=False,
        ),
    ]
    return {
        "schema_version": 2,
        "analyzer_version": "2.0.0",
        "limits": {"max_cfg_topology_nodes": 65536},
        "stats": {
            "indirect_sites": 2,
            "recovered_tables": 1,
            "unresolved_relevant_ctr_sites": 1,
        },
        "indirect_sites": sites,
        "structural_clusters": [
            {
                "cluster_id": resolved_cluster,
                "site_count": 1,
                "recovered_count": 1,
                "unresolved_count": 0,
                "representative_sites": ["0x00001010"],
                "switch_likelihood_counts": {"resolved_switch": 1},
                "blocks_phase3_closure": False,
            },
            {
                "cluster_id": unresolved_cluster,
                "site_count": 1,
                "recovered_count": 0,
                "unresolved_count": 1,
                "representative_sites": ["0x00001020"],
                "switch_likelihood_counts": {"computed_tail_dispatch": 1},
                "blocks_phase3_closure": False,
            },
        ],
    }


class JumpTableSchemaValidationTests(unittest.TestCase):
    def validate(self, report: dict) -> list[str]:
        errors: list[str] = []
        VERIFY.validate_jump_table_recovery(report, errors)
        return errors

    def test_schema_two_cluster_census_is_accepted(self) -> None:
        self.assertEqual(self.validate(schema_two_report()), [])

    def test_complete_valid_unresolved_probe_is_rejected(self) -> None:
        report = schema_two_report()
        probe = report["indirect_sites"][1]["dataflow"]["diagnostic_probe"]
        probe["hypothesis_complete"] = True
        probe["all_targets_valid"] = True
        self.assertTrue(
            any(
                "complete valid diagnostic table remains unresolved" in error
                for error in self.validate(report)
            )
        )

    def test_blocking_likelihood_and_cluster_disposition_are_rejected(self) -> None:
        report = schema_two_report()
        report["indirect_sites"][1]["dataflow"]["switch_likelihood"] = (
            "probable_switch_miss"
        )
        report["structural_clusters"][1]["switch_likelihood_counts"] = {
            "probable_switch_miss": 1
        }
        report["structural_clusters"][1]["blocks_phase3_closure"] = True
        errors = self.validate(report)
        self.assertTrue(any("credible switch candidate remains unresolved" in e for e in errors))
        self.assertIn("a structural cluster still blocks Phase 3 closure", errors)

    def test_accepted_retry_cannot_mask_another_failure_or_budget(self) -> None:
        report = schema_two_report()
        retry_site = report["indirect_sites"][0]
        retry_site["limit_retry"] = {
            "accepted": True,
            "exhausted_budget": "max_predecessors",
            "initial_failures": ["analysis_limit", "ambiguous_reaching_definition"],
            "exact_prior_table_match": False,
        }
        errors = self.validate(report)
        self.assertTrue(any("non-state budget" in error for error in errors))
        self.assertTrue(any("masks a non-limit initial failure" in error for error in errors))
        self.assertTrue(any("lacks an exact prior-table match" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
