#!/usr/bin/env python3
"""Report evidence-backed indirect PPC function candidates from a loaded TU1 image.

The tool is deliberately read-only. It does not alter the manifest and does not
declare every aligned executable pointer to be a function. Candidates are
reported only from pointer tables that contain a requested, runtime-observed
target, with PE section provenance, exact references, neighboring entries, and
a conservative PPC code-shape classification for review.
"""

from __future__ import annotations

import argparse
import dataclasses
import pathlib
import re
import struct
import sys
from collections.abc import Iterable


IMAGE_SCN_MEM_EXECUTE = 0x20000000
PPC_BCTR = 0x4E800420
PPC_BLR = 0x4E800020
PPC_MTCTR_MASK = 0xFC1FFFFF
PPC_MTCTR_OPCODE = 0x7C0903A6


@dataclasses.dataclass(frozen=True)
class Section:
    name: str
    start: int
    end: int
    characteristics: int

    @property
    def executable(self) -> bool:
        return bool(self.characteristics & IMAGE_SCN_MEM_EXECUTE)

    def contains(self, address: int) -> bool:
        return self.start <= address < self.end


@dataclasses.dataclass(frozen=True)
class PointerTable:
    start: int
    entries: tuple[int, ...]
    section: Section

    @property
    def end(self) -> int:
        return self.start + len(self.entries) * 4


def parse_address(text: str) -> int:
    value = int(text, 0)
    if not 0 <= value <= 0xFFFFFFFF:
        raise argparse.ArgumentTypeError(f"not a 32-bit address: {text}")
    return value


def u16le(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def u32le(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def u32be(data: bytes, offset: int) -> int:
    return struct.unpack_from(">I", data, offset)[0]


def parse_loaded_pe_sections(data: bytes, image_base: int) -> list[Section]:
    if len(data) < 0x40 or data[:2] != b"MZ":
        raise ValueError("dump does not begin with an in-memory PE image")
    pe_offset = u32le(data, 0x3C)
    if pe_offset + 24 > len(data) or data[pe_offset : pe_offset + 4] != b"PE\0\0":
        raise ValueError("loaded PE header was not found in the dump")

    section_count = u16le(data, pe_offset + 6)
    optional_header_size = u16le(data, pe_offset + 20)
    section_table = pe_offset + 24 + optional_header_size
    sections: list[Section] = []
    for index in range(section_count):
        offset = section_table + index * 40
        if offset + 40 > len(data):
            raise ValueError("loaded PE section table is truncated")
        raw_name = data[offset : offset + 8].split(b"\0", 1)[0]
        name = raw_name.decode("ascii", errors="replace")
        virtual_size = u32le(data, offset + 8)
        virtual_address = u32le(data, offset + 12)
        raw_size = u32le(data, offset + 16)
        characteristics = u32le(data, offset + 36)
        size = max(virtual_size, raw_size)
        start = image_base + virtual_address
        dump_end = image_base + len(data)
        end = min(start + size, dump_end)
        if start < end:
            sections.append(Section(name, start, end, characteristics))
    return sections


def section_for(sections: Iterable[Section], address: int) -> Section | None:
    return next((section for section in sections if section.contains(address)), None)


def executable_address(sections: Iterable[Section], address: int) -> bool:
    section = section_for(sections, address)
    return bool(section and section.executable and address % 4 == 0)


def load_generated_addresses(path: pathlib.Path) -> set[int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        int(match.group(1), 16)
        for match in re.finditer(r"\{\s*0x([0-9A-Fa-f]{8})\s*,\s*(?:sub_|xstart)", text)
    }


def load_manifest_addresses(path: pathlib.Path) -> set[int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        int(match.group(1), 16)
        for match in re.finditer(r'^\s*"0x([0-9A-Fa-f]{8})"\s*=\s*\{', text, re.MULTILINE)
    }


def read_word(data: bytes, image_base: int, address: int) -> int | None:
    offset = address - image_base
    if offset < 0 or offset + 4 > len(data):
        return None
    return u32be(data, offset)


def classify_code_shape(data: bytes, image_base: int, address: int) -> str:
    words = [read_word(data, image_base, address + index * 4) for index in range(8)]
    if any(word is None for word in words[:4]):
        return "unmapped"
    first, second, third, fourth = words[:4]
    assert first is not None and second is not None and third is not None and fourth is not None

    first_lwz = first >> 26 == 32
    second_lwz = second >> 26 == 32
    mtctr = third & PPC_MTCTR_MASK == PPC_MTCTR_OPCODE
    if first_lwz and second_lwz and mtctr and fourth == PPC_BCTR:
        receiver = (first >> 16) & 0x1F
        slot = second & 0xFFFF
        return f"virtual-dispatch thunk (receiver=r{receiver}, slot=0x{slot:X}, size=0x10)"

    opcode = first >> 26
    link = first & 1
    if opcode == 18 and link == 0:
        return "unconditional branch thunk (size=0x4)"

    for index, word in enumerate(words):
        if word == PPC_BLR:
            return f"leaf/control-flow candidate (first blr at +0x{index * 4:X})"
        if word is not None and word >> 26 == 18 and word & 1 == 0:
            return f"tail-branch candidate (first tail branch at +0x{index * 4:X})"
    return "unclassified executable bytes"


def exact_literal_references(data: bytes, image_base: int, target: int) -> list[int]:
    needle = struct.pack(">I", target)
    references: list[int] = []
    for offset in range(0, len(data) - 3, 4):
        if data[offset : offset + 4] == needle:
            references.append(image_base + offset)
    return references


def code_materializations(
    data: bytes, image_base: int, sections: list[Section], target: int
) -> list[tuple[int, int, int, str]]:
    results: list[tuple[int, int, int, str]] = []
    for section in sections:
        if not section.executable:
            continue
        start_offset = section.start - image_base
        end_offset = section.end - image_base
        for offset in range(start_offset, max(start_offset, end_offset - 4), 4):
            word = u32be(data, offset)
            if word >> 26 != 15 or ((word >> 16) & 0x1F) != 0:
                continue
            register = (word >> 21) & 0x1F
            high = (word & 0xFFFF) << 16
            for distance in range(1, 9):
                low_offset = offset + distance * 4
                if low_offset + 4 > end_offset:
                    break
                low_word = u32be(data, low_offset)
                opcode = low_word >> 26
                if opcode == 14 and ((low_word >> 16) & 0x1F) == register:
                    low = struct.unpack(">h", struct.pack(">H", low_word & 0xFFFF))[0]
                    value = (high + low) & 0xFFFFFFFF
                    kind = "lis/addi"
                elif opcode == 24 and ((low_word >> 21) & 0x1F) == register:
                    value = high | (low_word & 0xFFFF)
                    kind = "lis/ori"
                else:
                    continue
                if value == target:
                    results.append(
                        (image_base + offset, image_base + low_offset, register, kind)
                    )
    return results


def reviewed_materialized_candidates(
    data: bytes,
    image_base: int,
    sections: list[Section],
    generated: set[int],
) -> dict[int, list[tuple[int, int, int, int, str]]]:
    """Find code addresses passed as near-term call arguments.

    This is intentionally narrower than ReXGlue's disabled whole-image
    lis/addi function-pointer scanner. The combined address must land in an
    executable PE section, the destination must be an ABI argument register,
    and a direct call must follow within four instructions. The report still
    requires boundary/code-shape review and never edits the manifest.
    """

    candidates: dict[int, list[tuple[int, int, int, int, str]]] = {}
    for section in sections:
        if not section.executable:
            continue
        start_offset = section.start - image_base
        end_offset = section.end - image_base
        for offset in range(start_offset, max(start_offset, end_offset - 4), 4):
            word = u32be(data, offset)
            if word >> 26 != 15 or ((word >> 16) & 0x1F) != 0:
                continue
            high_register = (word >> 21) & 0x1F
            high = (word & 0xFFFF) << 16
            for distance in range(1, 9):
                low_offset = offset + distance * 4
                if low_offset + 4 > end_offset:
                    break
                low_word = u32be(data, low_offset)
                opcode = low_word >> 26
                if opcode == 14 and ((low_word >> 16) & 0x1F) == high_register:
                    destination = (low_word >> 21) & 0x1F
                    low = struct.unpack(">h", struct.pack(">H", low_word & 0xFFFF))[0]
                    value = (high + low) & 0xFFFFFFFF
                    kind = "lis/addi"
                elif opcode == 24 and ((low_word >> 21) & 0x1F) == high_register:
                    destination = (low_word >> 16) & 0x1F
                    value = high | (low_word & 0xFFFF)
                    kind = "lis/ori"
                else:
                    continue
                if not 3 <= destination <= 10 or not executable_address(sections, value):
                    continue
                call_site = 0
                for call_distance in range(1, 5):
                    call_offset = low_offset + call_distance * 4
                    if call_offset + 4 > end_offset:
                        break
                    call_word = u32be(data, call_offset)
                    if call_word >> 26 == 18 and call_word & 1:
                        call_site = image_base + call_offset
                        break
                if not call_site or value in generated:
                    continue
                candidates.setdefault(value, []).append(
                    (
                        image_base + offset,
                        image_base + low_offset,
                        call_site,
                        destination,
                        kind,
                    )
                )
    return candidates


def pointer_table_at(
    data: bytes,
    image_base: int,
    sections: list[Section],
    reference: int,
    max_entries: int = 256,
) -> PointerTable | None:
    source_section = section_for(sections, reference)
    if not source_section or source_section.executable:
        return None

    start = reference
    while start - 4 >= source_section.start:
        previous = read_word(data, image_base, start - 4)
        if previous is None or not executable_address(sections, previous):
            break
        start -= 4

    entries: list[int] = []
    address = start
    while address < source_section.end and len(entries) < max_entries:
        value = read_word(data, image_base, address)
        if value is None or not executable_address(sections, value):
            break
        entries.append(value)
        address += 4
    if len(entries) < 2:
        return None
    return PointerTable(start, tuple(entries), source_section)


def format_status(address: int, manifest: set[int], generated: set[int]) -> str:
    if address in manifest:
        return "manifest+generated" if address in generated else "manifest-only"
    return "generated" if address in generated else "MISSING"


def print_target_report(
    target: int,
    data: bytes,
    image_base: int,
    sections: list[Section],
    manifest: set[int],
    generated: set[int],
) -> set[PointerTable]:
    target_section = section_for(sections, target)
    print(f"\n0x{target:08X}")
    print(f"  status: {format_status(target, manifest, generated)}")
    print(
        "  code: "
        + (classify_code_shape(data, image_base, target) if target_section else "unmapped")
    )
    if target_section:
        print(
            f"  section: {target_section.name} "
            f"[0x{target_section.start:08X},0x{target_section.end:08X}) "
            f"executable={str(target_section.executable).lower()}"
        )

    tables: set[PointerTable] = set()
    references = exact_literal_references(data, image_base, target)
    if references:
        print("  exact big-endian references:")
        for reference in references:
            source = section_for(sections, reference)
            source_name = source.name if source else "<headers/unmapped>"
            table = pointer_table_at(data, image_base, sections, reference)
            if table:
                tables.add(table)
                index = (reference - table.start) // 4
                print(
                    f"    0x{reference:08X} section={source_name} "
                    f"table=[0x{table.start:08X},0x{table.end:08X}) slot={index}"
                )
            else:
                print(f"    0x{reference:08X} section={source_name} table=not-proven")
    else:
        print("  exact big-endian references: none")

    materializations = code_materializations(data, image_base, sections, target)
    if materializations:
        print("  code materializations:")
        for high_site, low_site, register, kind in materializations:
            print(
                f"    {kind} r{register} at 0x{high_site:08X} / 0x{low_site:08X}"
            )
    else:
        print("  code materializations: none found by conservative lis/addi-or-ori scan")
    return tables


def print_table_candidates(
    tables: set[PointerTable],
    data: bytes,
    image_base: int,
    manifest: set[int],
    generated: set[int],
) -> None:
    print("\nINDIRECT FUNCTION CANDIDATES")
    if not tables:
        print("  No pointer table containing a requested target was proven.")
        return

    seen: set[int] = set()
    for table in sorted(tables, key=lambda item: item.start):
        print(
            f"\nTABLE {table.section.name} "
            f"[0x{table.start:08X},0x{table.end:08X}) entries={len(table.entries)}"
        )
        generated_neighbors = sum(entry in generated for entry in table.entries)
        for index, entry in enumerate(table.entries):
            if entry in seen:
                continue
            seen.add(entry)
            status = format_status(entry, manifest, generated)
            shape = classify_code_shape(data, image_base, entry)
            if status == "MISSING" and shape.startswith("virtual-dispatch thunk"):
                confidence = "HIGH" if generated_neighbors else "MEDIUM"
            elif status == "MISSING":
                confidence = "REVIEW"
            else:
                confidence = "REGISTERED"
            print(
                f"  [{index:03}] 0x{entry:08X} {status} confidence={confidence}\n"
                f"        {shape}"
            )


def print_materialized_candidates(
    candidates: dict[int, list[tuple[int, int, int, int, str]]],
    data: bytes,
    image_base: int,
) -> None:
    print("\nREVIEWED MATERIALIZED-POINTER CANDIDATES")
    printed = 0
    for address in sorted(candidates):
        shape = classify_code_shape(data, image_base, address)
        if shape.startswith("virtual-dispatch thunk"):
            confidence = "HIGH"
        elif shape.startswith(("leaf/control-flow", "tail-branch", "unconditional branch")):
            confidence = "REVIEW"
        else:
            continue
        printed += 1
        print(f"\n0x{address:08X} confidence={confidence}")
        print(f"  boundary evidence: {shape}")
        for high_site, low_site, call_site, destination, kind in candidates[address]:
            print(
                f"  source: {kind} -> r{destination} at "
                f"0x{high_site:08X}/0x{low_site:08X}; direct call=0x{call_site:08X}"
            )
    if not printed:
        print("  No missing candidates passed the conservative review filter.")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", required=True, type=pathlib.Path)
    parser.add_argument("--dump-base", type=parse_address, default=0x82000000)
    parser.add_argument("--manifest", required=True, type=pathlib.Path)
    parser.add_argument("--generated-init", required=True, type=pathlib.Path)
    parser.add_argument(
        "--target", action="append", required=True, type=parse_address, help="repeatable"
    )
    return parser


def main() -> int:
    args = build_argument_parser().parse_args()
    data = args.dump.read_bytes()
    sections = parse_loaded_pe_sections(data, args.dump_base)
    manifest = load_manifest_addresses(args.manifest)
    generated = load_generated_addresses(args.generated_init)

    print("FABLE II TU1 INDIRECT FUNCTION EVIDENCE")
    print(f"dump: {args.dump}")
    print(f"dump_base: 0x{args.dump_base:08X}")
    print(f"manifest_entries: {len(manifest)}")
    print(f"generated_functions: {len(generated)}")
    print("sections:")
    for section in sections:
        print(
            f"  {section.name:8} [0x{section.start:08X},0x{section.end:08X}) "
            f"executable={str(section.executable).lower()}"
        )

    tables: set[PointerTable] = set()
    for target in args.target:
        tables.update(
            print_target_report(
                target, data, args.dump_base, sections, manifest, generated
            )
        )
    print_table_candidates(tables, data, args.dump_base, manifest, generated)
    print_materialized_candidates(
        reviewed_materialized_candidates(data, args.dump_base, sections, generated),
        data,
        args.dump_base,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
