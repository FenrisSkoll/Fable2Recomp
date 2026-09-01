#!/usr/bin/env python3
"""Repeatable synthetic benchmark for guarded Phase 4 manifest application."""

from __future__ import annotations

import argparse
import json
import statistics
import tempfile
import time
from pathlib import Path

import Fable2IndirectTargets as phase4


MANIFEST = (
    "# Phase 4 synthetic apply benchmark\r\n"
    "[entrypoint]\r\n"
    'file_path = "synthetic.xex"\r\n'
    "\r\n"
    "[entrypoint.functions]\r\n"
    "# preserve this comment\r\n"
    '"0x82190000" = { size = 0x10 }\r\n'
    "\r\n"
    "[analysis]\r\n"
    'marker = "preserve me"\r\n'
).encode("utf-8")


def benchmark_plan(manifest_bytes: bytes) -> tuple[dict, str]:
    candidate_id = "P4-BENCHMARK-REVIEWED"
    proposal = {
        "candidate_id": candidate_id,
        "target": "0x82191000",
        "classification": "strong_new_function",
        "confidence": "CONFIRMED",
        "proposal": {
            "entry": "0x82191000",
            "end": "0x82191020",
            "size": "0x00000020",
            "size_value": 0x20,
            "size_provenance": [
                {
                    "source": "synthetic_benchmark_pdata",
                    "authority": "pdata",
                    "start": "0x82191000",
                    "end": "0x82191020",
                    "size": 0x20,
                }
            ],
        },
        "evidence": [
            {
                "kind": "synthetic_benchmark",
                "conclusion": "benchmark-only reviewed range",
            }
        ],
        "runtime": {
            "source_sites": ["0x82180000"],
            "branch_kinds": ["bctrl"],
            "observed_runs": ["synthetic-benchmark"],
            "hit_count": 1,
            "observations": [],
        },
        "conflicts": [],
        "rejection_reasons": [],
        "automatic_application_permitted": True,
    }
    plan = {
        "schema": {
            "name": phase4.PLAN_SCHEMA_NAME,
            "version": phase4.PLAN_SCHEMA_VERSION,
        },
        "tool": {"name": "Phase4ApplyBenchmark", "version": 1},
        "mode": "dry_run",
        "inputs": {
            "manifest": {"sha256": phase4.sha256_bytes(manifest_bytes)}
        },
        "proposals": [proposal],
    }
    plan["plan_id"] = (
        "P4PLAN-" + phase4.sha256_bytes(phase4.canonical_json_bytes(plan))[:20]
    )
    phase4.validate_plan(plan)
    return plan, candidate_id


def measurements(samples: list[float]) -> dict[str, float]:
    return {
        "minimum_ms": min(samples),
        "median_ms": statistics.median(samples),
        "maximum_ms": max(samples),
        "mean_ms": statistics.mean(samples),
        "population_sd_ms": statistics.pstdev(samples),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=11)
    parser.add_argument("--warmup", type=int, default=2)
    args = parser.parse_args()
    if args.iterations < 1 or args.warmup < 0:
        parser.error("--iterations must be positive and --warmup non-negative")

    plan, candidate_id = benchmark_plan(MANIFEST)
    apply_samples: list[float] = []
    idempotent_samples: list[float] = []
    total_iterations = args.warmup + args.iterations
    with tempfile.TemporaryDirectory(prefix="fable2-phase4-apply-benchmark-") as root:
        root_path = Path(root)
        for index in range(total_iterations):
            manifest_path = root_path / f"manifest-{index:03d}.toml"
            manifest_path.write_bytes(MANIFEST)

            start = time.perf_counter_ns()
            first = phase4.apply_reviewed_plan(
                plan, manifest_path, {candidate_id}
            )
            applied_ns = time.perf_counter_ns() - start
            if first["status"] != "applied":
                raise RuntimeError(f"unexpected first apply status: {first!r}")

            start = time.perf_counter_ns()
            second = phase4.apply_reviewed_plan(
                plan, manifest_path, {candidate_id}
            )
            idempotent_ns = time.perf_counter_ns() - start
            if second["status"] != "already_applied":
                raise RuntimeError(f"unexpected second apply status: {second!r}")

            updated = manifest_path.read_bytes()
            if b"# preserve this comment\r\n" not in updated:
                raise RuntimeError("manifest comment was not preserved")
            if b"RETURN_R3_ZERO" in updated:
                raise RuntimeError("forbidden stub marker appeared")
            if index >= args.warmup:
                apply_samples.append(applied_ns / 1_000_000)
                idempotent_samples.append(idempotent_ns / 1_000_000)

    output = {
        "schema": {"name": "fable2-phase4-apply-benchmark", "version": 1},
        "workload": {
            "iterations": args.iterations,
            "warmup": args.warmup,
            "selected_candidates": 1,
            "input_manifest_bytes": len(MANIFEST),
            "filesystem": "temporary_directory",
        },
        "first_apply": measurements(apply_samples),
        "idempotent_reapply": measurements(idempotent_samples),
        "verification": {
            "atomic_apply_status": "applied",
            "idempotent_status": "already_applied",
            "crlf_and_comment_preserved": True,
            "stub_marker_absent": True,
        },
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
