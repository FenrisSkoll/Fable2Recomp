#!/usr/bin/env python3
"""Validate a Fable II entrypoint-closure report against its TU1 contract."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROVENANCE = REPO_ROOT / "tools" / "fable2-entrypoint-closure-evidence.json"


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"could not read JSON file '{path}': {error}") from error

    if not isinstance(value, dict):
        raise ValueError(f"JSON root in '{path}' is not an object")
    return value


def address_value(value: str) -> int:
    return int(value, 0)


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def sorted_unique(values: list[Any]) -> bool:
    return values == sorted(set(values))


def validate_entry_register_domains(
    site: dict[str, Any], dataflow: dict[str, Any], errors: list[str]
) -> None:
    site_address = site["site"]
    domains = dataflow.get("entry_register_domains")
    require(
        isinstance(domains, list),
        f"schema-3 site {site_address} has no entry-register-domain array",
        errors,
    )
    if not isinstance(domains, list):
        return

    domain_keys = [
        (address_value(domain["entry_address"]), domain.get("register"))
        for domain in domains
    ]
    require(
        domain_keys == sorted(domain_keys),
        f"entry-register domains are not sorted at {site_address}",
        errors,
    )
    require(
        len(domain_keys) == len(set(domain_keys)),
        f"entry-register domains are not unique at {site_address}",
        errors,
    )

    for domain in domains:
        entry_address = domain.get("entry_address")
        register = domain.get("register")
        domain_name = f"{site_address}/{entry_address}/r{register}"
        require(
            entry_address == site.get("owner_address"),
            f"entry-domain owner differs from its site at {domain_name}",
            errors,
        )
        require(
            isinstance(register, int) and 0 <= register < 32,
            f"entry-domain register is invalid at {domain_name}",
            errors,
        )

        finite_values = domain.get("finite_values")
        direct_calls = domain.get("direct_call_sites")
        rejected_references = domain.get("rejected_reference_sites")
        reference_rejections = domain.get("reference_rejections")
        callsites = domain.get("callsites")
        for name, values in (
            ("finite values", finite_values),
            ("direct calls", direct_calls),
            ("rejected references", rejected_references),
            ("reference rejections", reference_rejections),
            ("callsites", callsites),
        ):
            require(isinstance(values, list), f"entry-domain {name} missing at {domain_name}", errors)
        if not all(
            isinstance(values, list)
            for values in (
                finite_values,
                direct_calls,
                rejected_references,
                reference_rejections,
                callsites,
            )
        ):
            continue

        require(
            sorted_unique(finite_values),
            f"entry-domain finite values are not sorted and unique at {domain_name}",
            errors,
        )
        require(
            direct_calls == sorted(set(direct_calls), key=address_value),
            f"entry-domain direct calls are not sorted and unique at {domain_name}",
            errors,
        )
        require(
            rejected_references == sorted(set(rejected_references), key=address_value),
            f"entry-domain rejected references are not sorted and unique at {domain_name}",
            errors,
        )
        require(
            len(rejected_references) == len(reference_rejections),
            f"entry-domain rejected-reference reasons differ in count at {domain_name}",
            errors,
        )

        callsite_keys = [
            (address_value(callsite["caller_address"]), address_value(callsite["call_address"]))
            for callsite in callsites
        ]
        require(
            callsite_keys == sorted(callsite_keys),
            f"entry-domain callsites are not sorted at {domain_name}",
            errors,
        )
        require(
            len(callsite_keys) == len(set(callsite_keys)),
            f"entry-domain callsites are not unique at {domain_name}",
            errors,
        )

        for callsite in callsites:
            call_address = callsite.get("call_address")
            call_name = f"{domain_name}/{call_address}"
            require(
                callsite.get("target_address") == entry_address,
                f"entry-domain call targets a different entry at {call_name}",
                errors,
            )
            require(
                callsite.get("register") == register,
                f"entry-domain call uses a different register at {call_name}",
                errors,
            )
            call_values = callsite.get("finite_values")
            definitions = callsite.get("definition_addresses")
            rejections = callsite.get("rejections")
            require(
                isinstance(call_values, list) and sorted_unique(call_values),
                f"callsite finite values are not sorted and unique at {call_name}",
                errors,
            )
            require(
                isinstance(definitions, list)
                and definitions == sorted(set(definitions), key=address_value),
                f"callsite definitions are not sorted and unique at {call_name}",
                errors,
            )
            require(
                isinstance(rejections, list),
                f"callsite rejections are missing at {call_name}",
                errors,
            )
            if callsite.get("complete") is True:
                require(bool(call_values), f"complete callsite has no finite values at {call_name}", errors)
                require(
                    isinstance(callsite.get("proof_kind"), str)
                    and bool(callsite["proof_kind"]),
                    f"complete callsite has no proof kind at {call_name}",
                    errors,
                )
                require(not rejections, f"complete callsite has rejections at {call_name}", errors)
                require(
                    callsite.get("limit_hit") is False,
                    f"complete callsite still records a limit at {call_name}",
                    errors,
                )
            else:
                require(bool(rejections), f"incomplete callsite has no rejection at {call_name}", errors)

            exhausted_budget = callsite.get("exhausted_budget")
            if exhausted_budget is not None:
                budget_limit = callsite.get("budget_limit")
                budget_observed = callsite.get("budget_observed")
                require(
                    callsite.get("limit_hit") is True,
                    f"callsite budget exhaustion lacks limit status at {call_name}",
                    errors,
                )
                require(
                    isinstance(budget_limit, int)
                    and budget_limit > 0
                    and isinstance(budget_observed, int)
                    and budget_observed >= budget_limit,
                    f"callsite budget evidence is invalid at {call_name}",
                    errors,
                )

        all_direct = domain.get("all_references_direct_calls") is True
        if all_direct:
            require(
                not rejected_references and not reference_rejections,
                f"all-direct entry domain retains rejected references at {domain_name}",
                errors,
            )

        finite_dense = domain.get("finite_dense_domain") is True
        if finite_dense:
            call_values = sorted(
                {
                    value
                    for callsite in callsites
                    for value in callsite.get("finite_values", [])
                }
            )
            require(all_direct, f"finite entry domain is not all-direct at {domain_name}", errors)
            require(bool(callsites), f"finite entry domain has no callsites at {domain_name}", errors)
            require(
                all(callsite.get("complete") is True for callsite in callsites),
                f"finite entry domain includes an incomplete callsite at {domain_name}",
                errors,
            )
            require(
                set(direct_calls) == {callsite.get("call_address") for callsite in callsites},
                f"finite entry domain does not account for every direct call at {domain_name}",
                errors,
            )
            require(
                finite_values == call_values,
                f"finite entry-domain union differs from its callsites at {domain_name}",
                errors,
            )
            require(
                bool(finite_values) and finite_values == list(range(finite_values[-1] + 1)),
                f"finite entry domain is not dense from zero at {domain_name}",
                errors,
            )
            require(
                domain.get("rejection") is None,
                f"finite entry domain retains a rejection at {domain_name}",
                errors,
            )
        else:
            require(
                isinstance(domain.get("rejection"), str) and bool(domain["rejection"]),
                f"incomplete entry domain has no rejection at {domain_name}",
                errors,
            )

    entry_bounds = [
        bound
        for bound in dataflow.get("bound_candidates", [])
        if bound.get("interprocedural_entry_domain") is True
    ]
    if dataflow.get("merge_shape") == "interprocedural_entry_domain":
        require(
            bool(entry_bounds),
            f"interprocedural site {site_address} has no entry-domain bound",
            errors,
        )
    for bound in entry_bounds:
        matching = [
            domain
            for domain in domains
            if domain.get("entry_address") == site.get("owner_address")
            and domain.get("register") == bound.get("index_register")
            and domain.get("finite_dense_domain") is True
            and domain.get("finite_values") == bound.get("finite_values")
        ]
        require(
            len(matching) == 1,
            f"entry-domain bound lacks one exact complete domain at {site_address}",
            errors,
        )
        require(
            site.get("selected_table") is not None,
            f"validated entry-domain bound remains unresolved at {site_address}",
            errors,
        )
        finite_values = bound.get("finite_values", [])
        require(
            bool(finite_values)
            and bound.get("value") == finite_values[-1]
            and bound.get("case_count") == len(finite_values),
            f"entry-domain bound metadata differs from its finite values at {site_address}",
            errors,
        )


def validate_jump_table_recovery(jump: dict[str, Any], errors: list[str]) -> None:
    jump_schema = jump.get("schema_version")
    require(
        jump_schema in {1, 2, 3},
        f"unsupported jump-table schema {jump_schema}",
        errors,
    )
    expected_analyzer = {1: "1.0.0", 2: "2.0.0", 3: "3.0.0"}.get(jump_schema)
    require(
        jump.get("analyzer_version") == expected_analyzer,
        (
            f"jump-table schema {jump_schema} requires analyzer "
            f"{expected_analyzer}, got {jump.get('analyzer_version')}"
        ),
        errors,
    )

    sites = jump.get("indirect_sites", [])
    site_keys = [
        (address_value(site["site"]), address_value(site["owner_address"]))
        for site in sites
    ]
    require(site_keys == sorted(site_keys), "jump-table sites are not sorted", errors)
    relevant = [site for site in sites if site.get("uses_ctr") and not site.get("link")]
    unresolved = [site for site in relevant if site.get("selected_table") is None]
    require(
        all(site.get("failures") for site in unresolved),
        "an unresolved relevant CTR site has no explicit failure reason",
        errors,
    )

    stats = jump.get("stats", {})
    require(
        stats.get("indirect_sites") == len(sites),
        "jump-table indirect-site count does not match the array",
        errors,
    )
    require(
        stats.get("unresolved_relevant_ctr_sites") == len(unresolved),
        "jump-table unresolved count does not match the array",
        errors,
    )
    require(
        stats.get("recovered_tables")
        == sum(site.get("selected_table") is not None for site in relevant),
        "jump-table recovered count does not match relevant selected tables",
        errors,
    )

    if jump_schema not in {2, 3}:
        return

    limits = jump.get("limits", {})
    require(
        isinstance(limits.get("max_cfg_topology_nodes"), int)
        and limits["max_cfg_topology_nodes"] > 0,
        "schema-2 report has no positive max_cfg_topology_nodes limit",
        errors,
    )
    allowed_likelihoods = {
        "resolved_switch",
        "confirmed_switch_miss",
        "probable_switch_miss",
        "plausible_switch_candidate",
        "virtual_or_callback_dispatch",
        "computed_tail_dispatch",
        "opaque_non_table_dispatch",
        "insufficient_static_evidence",
        "rejected_false_positive",
    }
    blocking_likelihoods = {
        "confirmed_switch_miss",
        "probable_switch_miss",
        "plausible_switch_candidate",
    }
    cluster_census: dict[str, dict[str, Any]] = {}
    for site in relevant:
        dataflow = site.get("dataflow")
        require(
            isinstance(dataflow, dict),
            f"relevant CTR site {site['site']} has no schema-2 dataflow evidence",
            errors,
        )
        if not isinstance(dataflow, dict):
            continue
        if jump_schema == 3:
            validate_entry_register_domains(site, dataflow, errors)
        cluster_id = dataflow.get("cluster_id")
        likelihood = dataflow.get("switch_likelihood")
        require(
            isinstance(cluster_id, str) and bool(cluster_id),
            f"relevant CTR site {site['site']} has no structural cluster",
            errors,
        )
        require(
            likelihood in allowed_likelihoods,
            f"relevant CTR site {site['site']} has invalid likelihood {likelihood}",
            errors,
        )
        selected = site.get("selected_table") is not None
        require(
            (likelihood == "resolved_switch") == selected,
            f"site {site['site']} selected-table and likelihood dispositions differ",
            errors,
        )
        if not selected:
            require(
                likelihood not in blocking_likelihoods,
                f"credible switch candidate remains unresolved at {site['site']}",
                errors,
            )
            probe = dataflow.get("diagnostic_probe", {})
            require(
                probe.get("report_only") is True,
                f"diagnostic probe is not report-only at {site['site']}",
                errors,
            )
            require(
                not (
                    probe.get("hypothesis_complete") is True
                    and probe.get("all_targets_valid") is True
                ),
                f"complete valid diagnostic table remains unresolved at {site['site']}",
                errors,
            )
        retry = site.get("limit_retry")
        if retry and retry.get("accepted") is True:
            require(selected, f"accepted retry has no selected table at {site['site']}", errors)
            require(
                retry.get("exhausted_budget") == "max_states",
                f"accepted retry changed a non-state budget at {site['site']}",
                errors,
            )
            require(
                retry.get("initial_failures") == ["analysis_limit"],
                f"accepted retry masks a non-limit initial failure at {site['site']}",
                errors,
            )
            require(
                retry.get("exact_prior_table_match") is True,
                f"accepted retry lacks an exact prior-table match at {site['site']}",
                errors,
            )

        if not isinstance(cluster_id, str) or not cluster_id:
            continue
        census = cluster_census.setdefault(
            cluster_id,
            {
                "sites": [],
                "recovered": 0,
                "unresolved": 0,
                "likelihoods": Counter(),
            },
        )
        census["sites"].append(site["site"])
        census["recovered" if selected else "unresolved"] += 1
        census["likelihoods"][likelihood] += 1

    clusters = jump.get("structural_clusters", [])
    cluster_ids = [cluster.get("cluster_id") for cluster in clusters]
    require(
        cluster_ids == sorted(cluster_ids),
        "jump-table structural clusters are not deterministically sorted",
        errors,
    )
    require(
        len(cluster_ids) == len(set(cluster_ids)),
        "jump-table structural cluster identifiers are not unique",
        errors,
    )
    require(
        set(cluster_ids) == set(cluster_census),
        "jump-table structural cluster summary does not cover every relevant CTR site",
        errors,
    )
    for cluster in clusters:
        cluster_id = cluster.get("cluster_id")
        census = cluster_census.get(cluster_id)
        if census is None:
            continue
        require(
            cluster.get("site_count") == len(census["sites"]),
            f"cluster {cluster_id} site count differs from its members",
            errors,
        )
        require(
            cluster.get("recovered_count") == census["recovered"],
            f"cluster {cluster_id} recovered count differs from its members",
            errors,
        )
        require(
            cluster.get("unresolved_count") == census["unresolved"],
            f"cluster {cluster_id} unresolved count differs from its members",
            errors,
        )
        require(
            cluster.get("switch_likelihood_counts") == dict(census["likelihoods"]),
            f"cluster {cluster_id} likelihood census differs from its members",
            errors,
        )
        require(
            cluster.get("representative_sites") == census["sites"][:5],
            f"cluster {cluster_id} representatives are not the stable first members",
            errors,
        )
        expected_blocking = any(
            census["likelihoods"].get(likelihood, 0) for likelihood in blocking_likelihoods
        )
        require(
            cluster.get("blocks_phase3_closure") is expected_blocking,
            f"cluster {cluster_id} has an inconsistent closure disposition",
            errors,
        )
    require(
        not any(cluster.get("blocks_phase3_closure") for cluster in clusters),
        "a structural cluster still blocks Phase 3 closure",
        errors,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the authoritative Fable II TU1 entrypoint-closure JSON "
            "without changing the manifest or report."
        )
    )
    parser.add_argument(
        "--provenance",
        type=Path,
        default=DEFAULT_PROVENANCE,
        help="versioned Fable II evidence contract",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help=(
            "authoritative entrypoint-closure JSON; defaults to "
            "out/analysis/<expected-patched-sha256>/entrypoint-closure.json"
        ),
    )
    args = parser.parse_args()

    try:
        provenance = load_json(args.provenance.resolve())
        expected_identity = provenance["expected_image_identity"]
        expected_fixtures = provenance["acceptance_fixtures"]
        patched_sha256 = expected_identity["patched_image_sha256"]
        report_path = args.report or (
            REPO_ROOT
            / "out"
            / "analysis"
            / patched_sha256
            / "entrypoint-closure.json"
        )
        report = load_json(report_path.resolve())
    except (KeyError, TypeError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1

    errors: list[str] = []
    schema_version = report.get("schema_version")
    analyzer_version = report.get("analyzer_version")
    require(schema_version in {1, 2, 3}, f"unsupported schema_version {schema_version}", errors)
    expected_analyzer = {1: "1.0.0", 2: "1.1.0", 3: "2.0.0"}.get(schema_version)
    require(
        analyzer_version == expected_analyzer,
        f"schema {schema_version} requires analyzer {expected_analyzer}, got {analyzer_version}",
        errors,
    )

    actual_identity = report.get("image_identity", {})
    identity_keys = [key for key in expected_identity if key != "executable_sections"]
    for key in identity_keys:
        if schema_version == 1 and key.startswith("executable_memory_"):
            continue
        expected = expected_identity[key]
        report_key = (
            "executable_memory_fingerprint"
            if key == "executable_memory_sha256"
            else key
        )
        actual = actual_identity.get(report_key)
        require(actual == expected, f"identity {key}: expected {expected}, got {actual}", errors)
    if schema_version in {2, 3}:
        expected_sections = expected_identity.get("executable_sections", [])
        actual_sections = [
            {
                "name": section["name"],
                "start": section["range"]["start"],
                "end": section["range"]["end"],
                "size": section["range"]["size"],
                "permissions": "".join(
                    (
                        "r" if section.get("readable") else "-",
                        "w" if section.get("writable") else "-",
                        "x" if section.get("executable") else "-",
                    )
                ),
                "sha256": section["sha256"],
            }
            for section in report.get("sections", [])
            if section.get("executable")
        ]
        require(
            actual_sections == expected_sections,
            "identity executable_sections differ from the versioned evidence contract",
            errors,
        )

    if schema_version == 3:
        jump = report.get("jump_table_recovery", {})
        validate_jump_table_recovery(jump, errors)

    safety = report.get("safety", {})
    require(safety.get("mode") == "report_only", "report mode is not report_only", errors)
    require(
        safety.get("manifest_mutation_attempted") is False,
        "report records a manifest mutation attempt",
        errors,
    )
    require(
        safety.get("review_toml_is_non_authoritative") is True,
        "review TOML is not marked non-authoritative",
        errors,
    )

    fixpoint = report.get("fixpoint", {})
    require(fixpoint.get("reached") is True, "analysis did not reach a fixpoint", errors)
    limit_diagnostics = report.get("limit_diagnostics", [])
    exhausted_limits = [
        diagnostic
        for diagnostic in limit_diagnostics
        if str(diagnostic.get("limit", "")).startswith("max_")
    ]
    require(not exhausted_limits, f"analysis exhausted limits: {exhausted_limits}", errors)

    candidates = report.get("candidates", [])
    candidate_addresses = [address_value(candidate["address"]) for candidate in candidates]
    require(
        candidate_addresses == sorted(candidate_addresses),
        "candidates are not sorted by guest address",
        errors,
    )
    for candidate in candidates:
        evidence_keys = [
            (
                address_value(evidence["target_address"]),
                evidence["kind"],
                address_value(evidence["storage_address"])
                if evidence.get("storage_address")
                else 0,
                address_value(evidence["source_address"])
                if evidence.get("source_address")
                else 0,
                evidence.get("source_section") or "",
                evidence.get("provenance") or "",
                tuple(sorted(evidence.get("attributes", {}).items())),
            )
            for evidence in candidate.get("evidence", [])
        ]
        require(
            evidence_keys == sorted(evidence_keys),
            f"evidence is not deterministically sorted for {candidate['address']}",
            errors,
        )

    review_classes = {
        "strong_new_function",
        "probable_new_function",
        "ambiguous_code_pointer",
    }
    review_ranges = [
        (
            address_value(candidate["proposed_range"]["start"]),
            address_value(candidate["proposed_range"]["end"]),
        )
        for candidate in candidates
        if candidate.get("classification") in review_classes
        and candidate.get("proposed_range") is not None
    ]
    overlap_pairs = 0
    active_ranges: list[tuple[int, int]] = []
    for start, end in review_ranges:
        active_ranges = [active for active in active_ranges if active[1] > start]
        overlap_pairs += sum(1 for active in active_ranges if active[0] < end)
        active_ranges.append((start, end))

    actual_fixtures = {
        fixture["expected"]["address"]: fixture
        for fixture in report.get("fixture_results", [])
    }
    for expected in expected_fixtures:
        address = expected["address"]
        expected_size = address_value(expected["size"])
        fixture = actual_fixtures.get(address)
        require(fixture is not None, f"fixture {address} is missing", errors)
        if fixture is None:
            continue
        actual_size = address_value(fixture["expected"]["size"])
        require(actual_size == expected_size, f"fixture {address} size mismatch", errors)
        require(
            fixture["expected"]["verified_classification"]
            == expected["verified_classification"],
            f"fixture {address} verified classification mismatch",
            errors,
        )
        require(fixture.get("result") == "pass", f"fixture {address} did not pass", errors)
        require(fixture.get("present") is True, f"fixture {address} is absent", errors)
        require(fixture.get("range_matches") is True, f"fixture {address} range differs", errors)
        require(
            fixture.get("independently_rediscovered") is True,
            f"fixture {address} was not independently rediscovered",
            errors,
        )
        require(
            bool(fixture.get("independent_evidence")),
            f"fixture {address} has no independent static evidence",
            errors,
        )

    counts = report.get("counts", {})
    require(
        counts.get("candidates") == len(candidates),
        "candidate count does not match candidate array length",
        errors,
    )
    require(
        counts.get("candidate_overlap_pairs") == overlap_pairs,
        "candidate overlap count does not match proposed ranges",
        errors,
    )

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print(
        f"PASS: schema={schema_version} analyzer={analyzer_version} "
        f"image={patched_sha256} candidates={counts.get('candidates')} "
        f"strong={counts.get('strong_new_functions')} "
        f"probable={counts.get('probable_new_functions')} fixtures={len(expected_fixtures)}"
    )
    for expected in expected_fixtures:
        fixture = actual_fixtures[expected["address"]]
        storage = ",".join(fixture.get("storage_addresses", [])) or "none"
        materialization = ",".join(fixture.get("materialization_sites", [])) or "none"
        evidence = ",".join(fixture.get("independent_evidence", []))
        print(
            f"  {expected['address']} size={expected['size']} evidence={evidence} "
            f"storage={storage} materialization={materialization}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
