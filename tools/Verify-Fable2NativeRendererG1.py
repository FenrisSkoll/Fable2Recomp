#!/usr/bin/env python3
"""Validate the byte-free Fable II native-renderer G1 evidence package."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


SCHEMA = "fable2-native-renderer-hook-inventory"
PATCHED_IMAGE_SHA256 = (
    "BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00"
)
CONFIDENCE = {"confirmed", "strong_hypothesis", "weak_hypothesis"}
ADDRESS_RE = re.compile(r"0x[0-9A-F]{8}\Z")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
REQUIRED_FIELDS = {
    "guest_address",
    "exclusive_end",
    "size",
    "generated_name",
    "confidence",
    "role",
    "provenance",
    "direct_callers",
    "indirect_callers_or_refs",
    "observed_arguments_and_layout",
    "distinguishing_evidence",
    "forwarding",
    "expected_side_effects_and_risks",
    "seam_disposition",
}
REQUIRED_OPERATIONS = {
    "device_create",
    "device_destroy",
    "resource_surface_create",
    "texture_vertex_index_lock_unlock",
    "render_target_depth_surface",
    "vertex_declaration_stream_source",
    "shader_create_bind",
    "shader_constants",
    "textures_sampler_state",
    "render_blend_depth_raster_viewport_scissor_state",
    "clear",
    "primitive_indexed_draw",
    "resolve_copy",
    "query_predication_synchronization",
    "swap_present",
    "engine_render_command_queue",
}
REQUIRED_DOCS = (
    "00-workstream-scope.md",
    "01-current-gpu-data-path.md",
    "02-unleashed-recompiled-reference.md",
    "03-candidate-hook-inventory.md",
    "04-architecture-options.md",
    "05-shadow-capture-design.md",
    "06-risk-register.md",
    "g1-completion.md",
)


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def parse_hex(value: str, field: str) -> int:
    require(isinstance(value, str), f"{field} must be a string")
    try:
        return int(value, 16)
    except ValueError as exc:
        raise ValidationError(f"{field} is not hexadecimal: {value}") from exc


def validate_generated_boundary(
    generated_dir: Path, candidate: dict[str, object]
) -> None:
    name = str(candidate["generated_name"])
    address = str(candidate["guest_address"])
    definition = f"DEFINE_REX_FUNC({name}, {address}, false)"
    matches: list[tuple[Path, str]] = []

    for path in sorted(generated_dir.glob("*.cpp")):
        text = path.read_text(encoding="utf-8")
        if definition in text:
            matches.append((path, text))

    require(len(matches) == 1, f"{definition}: expected one generated body")
    path, text = matches[0]
    start = text.index(definition)
    next_definition = text.find("DEFINE_REX_FUNC(", start + len(definition))
    body = text[start : next_definition if next_definition >= 0 else len(text)]
    instruction_comments = sum(
        1 for line in body.splitlines() if re.match(r"^\s*//\s+\S", line)
    )
    expected = parse_hex(str(candidate["size"]), f"{name}.size") // 4
    require(
        instruction_comments == expected,
        f"{name}: {instruction_comments} generated instructions in {path.name}, "
        f"expected {expected}",
    )


def validate(args: argparse.Namespace) -> Counter[str]:
    repo = args.repo.resolve()
    doc_dir = repo / "docs" / "fable2-native-renderer"
    inventory_path = doc_dir / "candidate-hook-inventory.json"
    data = json.loads(inventory_path.read_text(encoding="utf-8"))

    require(data.get("schema") == SCHEMA, "unexpected inventory schema")
    require(data.get("schema_version") == 1, "unexpected schema version")
    require(data.get("result") == "PASS WITH LIMITATIONS", "unexpected result")
    require(
        data.get("target", {}).get("patched_image_sha256") == PATCHED_IMAGE_SHA256,
        "patched-image identity mismatch",
    )

    candidates = data.get("candidates")
    require(isinstance(candidates, list) and candidates, "candidate list is empty")
    addresses: list[int] = []
    names: set[str] = set()
    counts: Counter[str] = Counter()

    inventory_doc = (doc_dir / "03-candidate-hook-inventory.md").read_text(
        encoding="utf-8"
    )
    for index, candidate in enumerate(candidates):
        require(isinstance(candidate, dict), f"candidate {index} is not an object")
        missing = REQUIRED_FIELDS - candidate.keys()
        require(not missing, f"candidate {index} missing fields: {sorted(missing)}")

        address_text = candidate["guest_address"]
        end_text = candidate["exclusive_end"]
        require(ADDRESS_RE.fullmatch(address_text) is not None, f"bad address {address_text}")
        require(ADDRESS_RE.fullmatch(end_text) is not None, f"bad end {end_text}")
        address = parse_hex(address_text, "guest_address")
        end = parse_hex(end_text, "exclusive_end")
        size = parse_hex(candidate["size"], "size")
        require(size > 0 and size % 4 == 0, f"{address_text}: invalid PPC size")
        require(address + size == end, f"{address_text}: exclusive end mismatch")
        require(address_text in inventory_doc, f"{address_text}: absent from Markdown inventory")

        name = candidate["generated_name"]
        require(name == f"sub_{address_text[2:]}", f"{address_text}: generated name mismatch")
        require(name not in names, f"duplicate generated name {name}")
        names.add(name)
        addresses.append(address)

        confidence = candidate["confidence"]
        require(confidence in CONFIDENCE, f"{address_text}: invalid confidence")
        counts[confidence] += 1
        require(candidate["provenance"], f"{address_text}: provenance is empty")

        if not args.skip_generated:
            validate_generated_boundary(args.generated_dir.resolve(), candidate)

    require(addresses == sorted(addresses), "candidates are not sorted by guest address")
    require(len(addresses) == len(set(addresses)), "duplicate guest address")
    require(dict(counts) == data.get("confidence_counts"), "confidence counts mismatch")

    coverage = data.get("operation_coverage")
    require(isinstance(coverage, list), "operation coverage must be a list")
    operation_names = [row.get("operation") for row in coverage]
    require(len(operation_names) == len(set(operation_names)), "duplicate operation coverage")
    require(set(operation_names) == REQUIRED_OPERATIONS, "operation coverage is incomplete")
    known_addresses = {candidate["guest_address"] for candidate in candidates}
    for row in coverage:
        for address in row.get("candidates", []):
            require(address in known_addresses, f"coverage references unknown {address}")

    for filename in REQUIRED_DOCS:
        path = doc_dir / filename
        require(path.is_file(), f"missing documentation: {filename}")
        text = path.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK_RE.findall(text):
            if target.startswith(("http://", "https://", "#")):
                continue
            relative_target = target.split("#", 1)[0].strip("<>")
            require(
                (path.parent / relative_target).resolve().exists(),
                f"{filename}: broken local link {target}",
            )

    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument(
        "--generated-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "generated" / "default",
    )
    parser.add_argument(
        "--skip-generated",
        action="store_true",
        help="Skip local ignored generated-body instruction-count checks.",
    )
    args = parser.parse_args()

    try:
        counts = validate(args)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    rendered_counts = ", ".join(
        f"{name}={counts[name]}"
        for name in ("confirmed", "strong_hypothesis", "weak_hypothesis")
    )
    print(f"Validated 11 G1 candidates: {rendered_counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
