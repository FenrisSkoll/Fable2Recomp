from __future__ import annotations

import copy
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


def entry_callsite(call_address: str, caller_address: str, value: int) -> dict:
    definition = f"0x{int(call_address, 0) - 4:08X}"
    return {
        "caller_address": caller_address,
        "call_address": call_address,
        "target_address": "0x00001000",
        "compare_address": None,
        "guard_address": None,
        "register": 3,
        "definition_addresses": [definition],
        "finite_values": [value],
        "proof_kind": "dominating_immediate_constant",
        "rejections": [],
        "exhausted_budget": None,
        "budget_limit": 0,
        "budget_observed": 0,
        "complete": True,
        "limit_hit": False,
    }


def schema_three_report() -> dict:
    report = copy.deepcopy(schema_two_report())
    report["schema_version"] = 3
    report["analyzer_version"] = "3.0.0"
    for indirect_site in report["indirect_sites"]:
        indirect_site["dataflow"]["entry_register_domains"] = []

    resolved = report["indirect_sites"][0]
    first_call = entry_callsite("0x00002004", "0x00002000", 0)
    second_call = entry_callsite("0x00003004", "0x00003000", 1)
    resolved["dataflow"].update(
        {
            "merge_shape": "interprocedural_entry_domain",
            "bound_candidates": [
                {
                    "interprocedural_entry_domain": True,
                    "index_register": 3,
                    "finite_values": [0, 1],
                    "value": 1,
                    "case_count": 2,
                }
            ],
            "entry_register_domains": [
                {
                    "entry_address": "0x00001000",
                    "register": 3,
                    "finite_values": [0, 1],
                    "direct_call_sites": ["0x00002004", "0x00003004"],
                    "rejected_reference_sites": [],
                    "reference_rejections": [],
                    "callsites": [first_call, second_call],
                    "all_references_direct_calls": True,
                    "finite_dense_domain": True,
                    "rejection": None,
                }
            ],
        }
    )
    return report


class JumpTableSchemaValidationTests(unittest.TestCase):
    def validate(self, report: dict) -> list[str]:
        errors: list[str] = []
        VERIFY.validate_jump_table_recovery(report, errors)
        return errors

    def test_schema_two_cluster_census_is_accepted(self) -> None:
        self.assertEqual(self.validate(schema_two_report()), [])

    def test_schema_three_complete_entry_domain_is_accepted(self) -> None:
        self.assertEqual(self.validate(schema_three_report()), [])

    def test_schema_three_entry_domain_cannot_mask_an_incomplete_callsite(self) -> None:
        report = schema_three_report()
        callsite = report["indirect_sites"][0]["dataflow"]["entry_register_domains"][0][
            "callsites"
        ][1]
        callsite.update(
            {
                "finite_values": [],
                "proof_kind": None,
                "rejections": ["callsite_bound_analysis_limit"],
                "complete": False,
                "limit_hit": True,
            }
        )
        errors = self.validate(report)
        self.assertTrue(any("includes an incomplete callsite" in error for error in errors))
        self.assertTrue(any("union differs from its callsites" in error for error in errors))

    def test_schema_three_entry_domain_call_must_target_the_exact_owner(self) -> None:
        report = schema_three_report()
        callsite = report["indirect_sites"][0]["dataflow"]["entry_register_domains"][0][
            "callsites"
        ][0]
        callsite["target_address"] = "0x00001010"
        self.assertTrue(
            any("call targets a different entry" in error for error in self.validate(report))
        )

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
