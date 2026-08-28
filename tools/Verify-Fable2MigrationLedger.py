#!/usr/bin/env python3
"""Verify the durable Harvest 001-003 function-registration ledger."""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LedgerEntry:
    harvest: str
    start: int
    end: int

    @property
    def size(self) -> int:
        return self.end - self.start


LEDGER = (
    LedgerEntry("001", 0x82C03B28, 0x82C03B44),
    LedgerEntry("001", 0x829647F0, 0x82964800),
    LedgerEntry("001", 0x829675E0, 0x829675F0),
    LedgerEntry("002", 0x829675D0, 0x829675E0),
    LedgerEntry("002", 0x829675C0, 0x829675D0),
    LedgerEntry("002", 0x8288ACB0, 0x8288ACC0),
    LedgerEntry("002", 0x8288ACC0, 0x8288ACD0),
    LedgerEntry("002", 0x82964820, 0x82964830),
    LedgerEntry("002/003", 0x82C8A920, 0x82C8A93C),
    LedgerEntry("002/003", 0x82967540, 0x82967550),
    LedgerEntry("002/003", 0x82DE2BA8, 0x82DE2BC4),
    LedgerEntry("003", 0x82E8C8E8, 0x82E8C92C),
    LedgerEntry("sibling", 0x82C00A98, 0x82C00AA8),
    LedgerEntry("sibling", 0x826EE730, 0x826EE740),
    LedgerEntry("sibling", 0x82964800, 0x82964810),
    LedgerEntry("sibling", 0x82964810, 0x82964820),
    LedgerEntry("sibling", 0x82967530, 0x82967540),
    LedgerEntry("sibling", 0x82967550, 0x82967560),
    LedgerEntry("sibling", 0x82967570, 0x82967580),
    LedgerEntry("sibling", 0x82967580, 0x82967590),
    LedgerEntry("sibling", 0x82967590, 0x829675A0),
    LedgerEntry("sibling", 0x829675A0, 0x829675B0),
    LedgerEntry("sibling", 0x8305DA68, 0x8305DA78),
    LedgerEntry("sibling", 0x8305DA78, 0x8305DA88),
    LedgerEntry("sibling", 0x8305DA88, 0x8305DA98),
    LedgerEntry("sibling", 0x8305DA98, 0x8305DAA8),
    LedgerEntry("sibling", 0x8305DAA8, 0x8305DAB8),
    LedgerEntry("sibling", 0x8305DAB8, 0x8305DAC8),
    LedgerEntry("sibling", 0x8305DAC8, 0x8305DAD8),
    LedgerEntry("sibling", 0x8305DAD8, 0x8305DAE8),
    LedgerEntry("sibling", 0x8305DAE8, 0x8305DAF8),
    LedgerEntry("sibling", 0x8305DAF8, 0x8305DB08),
)

DEFINE_RE = re.compile(
    r"DEFINE_REX_FUNC\(sub_([0-9A-F]{8}),\s*0x([0-9A-F]{8}),"
)
MAPPING_RE = re.compile(r"\{\s*0x([0-9A-F]{8}),\s*sub_([0-9A-F]{8})\s*\},")
REGISTER_RE = re.compile(
    r"SetFunction\(0x([0-9A-F]{8}),\s*sub_([0-9A-F]{8})\);"
)
DECLARE_RE = re.compile(r"DECLARE_REX_FUNC\(sub_([0-9A-F]{8})\);")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("fable2_manifest.toml"))
    parser.add_argument(
        "--generated-dir", type=Path, default=Path("generated/default")
    )
    return parser.parse_args()


def matched_addresses(pattern: re.Pattern[str], text: str) -> set[int]:
    addresses: set[int] = set()
    for match in pattern.finditer(text):
        first = int(match.group(1), 16)
        if match.lastindex == 2 and first != int(match.group(2), 16):
            raise ValueError(f"address/name mismatch in: {match.group(0)}")
        addresses.add(first)
    return addresses


def main() -> int:
    args = parse_args()
    with args.manifest.open("rb") as manifest_file:
        manifest = tomllib.load(manifest_file)

    generated_dir = args.generated_dir
    init_text = (generated_dir / "fable2_init.cpp").read_text(encoding="utf-8")
    register_text = (generated_dir / "fable2_register.cpp").read_text(
        encoding="utf-8"
    )
    funcs_text = (generated_dir / "fable2_funcs.h").read_text(encoding="utf-8")

    definitions: set[int] = set()
    hot_predicate_body = ""
    for source_path in sorted(generated_dir.glob("fable2_recomp.*.cpp")):
        source_text = source_path.read_text(encoding="utf-8")
        definitions.update(matched_addresses(DEFINE_RE, source_text))
        marker = "DEFINE_REX_FUNC(sub_82E8C8E8, 0x82E8C8E8, false)"
        marker_offset = source_text.find(marker)
        if marker_offset >= 0:
            next_offset = source_text.find("\nDEFINE_REX_FUNC(", marker_offset + 1)
            hot_predicate_body = source_text[
                marker_offset : None if next_offset < 0 else next_offset
            ]

    mappings = matched_addresses(MAPPING_RE, init_text)
    registrations = matched_addresses(REGISTER_RE, register_text)
    declarations = matched_addresses(DECLARE_RE, funcs_text)
    manifest_functions = manifest["entrypoint"]["functions"]

    failures: list[str] = []
    entries_by_start = {entry.start: entry for entry in LEDGER}
    if len(entries_by_start) != len(LEDGER):
        failures.append("ledger contains duplicate starts")

    ordered = sorted(LEDGER, key=lambda entry: entry.start)
    for left, right in zip(ordered, ordered[1:]):
        if left.end > right.start:
            failures.append(
                f"ledger overlap: 0x{left.start:08X}-0x{left.end:08X} and "
                f"0x{right.start:08X}-0x{right.end:08X}"
            )

    print("harvest      start        end        size manifest body decl map register")
    for entry in LEDGER:
        address = f"0x{entry.start:08X}"
        manifest_entry = manifest_functions.get(address)
        manifest_ok = (
            isinstance(manifest_entry, dict)
            and manifest_entry.get("size") == entry.size
        )
        checks = (
            manifest_ok,
            entry.start in definitions,
            entry.start in declarations,
            entry.start in mappings,
            entry.start in registrations,
        )
        print(
            f"{entry.harvest:<11} 0x{entry.start:08X} 0x{entry.end:08X} "
            f"0x{entry.size:02X} " + " ".join("yes" if check else "NO " for check in checks)
        )
        if not all(checks):
            failures.append(f"0x{entry.start:08X} failed one or more ledger checks")

    entrypoint = manifest["entrypoint"]
    if entrypoint.get("setjmp_address") != 0x83006C90:
        failures.append("setjmp_address is not 0x83006C90")
    if entrypoint.get("longjmp_address") != 0x82CAFA30:
        failures.append("longjmp_address is not 0x82CAFA30")

    predicate_markers = (
        "ctx.r3.s64 = 0;",
        "ctx.r3.s64 = 1;",
        "goto loc_82E8C8FC;",
    )
    if not hot_predicate_body or not all(
        marker in hot_predicate_body for marker in predicate_markers
    ):
        failures.append("0x82E8C8E8 real boolean-search body was not preserved")

    print(
        f"\nTotals: definitions={len(definitions)} declarations={len(declarations)} "
        f"mappings={len(mappings)} registrations={len(registrations)}"
    )
    print(
        "setjmp=0x83006C90 longjmp=0x82CAFA30; "
        "0x82E8C8E8 real 0/1 search semantics preserved"
    )

    if failures:
        print("\nFAILED:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(f"PASS: all {len(LEDGER)} Harvest 001-003 and sibling entries verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
