#!/usr/bin/env python3
"""Deterministic Phase 2A cross-build function correspondence analysis.

The tool consumes hash-bound, ignored section exports. It never writes beneath
the prototype source root and never changes the TU1 manifest or generated code.
Function units come only from exact big-endian IMAGE_CE_RUNTIME_FUNCTION
records in each image's .pdata section.
"""

from __future__ import annotations

import argparse
import bisect
import collections
import hashlib
import json
import platform
import re
import struct
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import VerifyFable2PrototypePhase1Consistency as phase1_consistency


TOOL_NAME = "Fable2PrototypeCorrespondence.py"
TOOL_VERSION = "1.0.1"
SCHEMA_VERSION = 1
POLICY_VERSION = "precision-first-v1"
SCORE_VERSION = "review-ranking-v1"
TOP_CANDIDATE_LIMIT = 3
NEIGHBOUR_WINDOW = 8

EXPECTED = {
    "sep_container": "9997088F23FEFA2C700F18DA2CCB614AAE221C6F39B3BE9BA7AAAA059DB6BFAF",
    "jul_container": "0AAA3C8EF72ECBB607C9D8A50C42022F3E0BDE759A462CB14148621790C0E348",
    "donor_container": "0686A9F292A3F6777BEB6E8D4924F96247D1E8E3E2370323572F797E6637A4AA",
    "donor_text": "A49213732D2E64610939BBBAE6985F9248457DFE46278E3215F11CB68A071878",
    "donor_pdata": "1805B91295ACEAEC07CE437A84DFF25E75A8B69B155C764838E3864E26C0BCB9",
    "target_base": "88C4EF2E18E65409444D1B068EFF921D1F7E180A5AE64EDC64BA6B0872372662",
    "target_xexp": "046A05693B4DA4437083C784000A850858B3BF992955C7DB30D518FB3E53E41C",
    "target_postpatch": "BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00",
    "target_executable": "5C8B78B84C93028D166E3DF347206E6642BA40BF374AD1AF8D958B2211320357",
    "target_text": "1B9F2E80280637FE2287286ED3FE18B367F378E24A695A2B8AB50B9ACD8FC724",
    "target_pdata": "FE6A61E508AD67FC39BEA85372A06DA1CAF40C5F1E7BB2B52FF37471FE44AB3C",
    "closure": "665CA2AE7ED65632B2E9F368063D3D9EE260E8DEF6F276B455CD62A9F2DCC397",
}

TERMINAL_STATUSES = (
    "accepted-exact-unique",
    "accepted-normalized-corroborated",
    "candidate-structural",
    "ambiguous",
    "quarantined",
    "boundary-change",
    "unmatched",
)
ACCEPTED_STATUSES = set(TERMINAL_STATUSES[:2])
FINGERPRINT_KEYS = ("raw_sha256", "branch_normalized_sha256", "opcode_structure_sha256")
ASCII_RE = re.compile(rb"[\x20-\x7e]{8,}")
UTF16_RE = re.compile(rb"(?:[\x20-\x7e]\x00){8,}")
IMMEDIATE_OPCODES = frozenset(range(7, 16)) | frozenset(range(20, 30)) | frozenset(
    range(32, 48)
)


class CorrespondenceError(ValueError):
    """Raised when inputs or outputs fail the Phase 2A contract."""


def address_text(value: int) -> str:
    return f"0x{value:08X}"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise CorrespondenceError(f"could not hash {path}: {error}") from error
    return digest.hexdigest().upper()


def python_runtime_identity() -> dict[str, str]:
    return {
        "implementation": platform.python_implementation(),
        "version": platform.python_version(),
        "cache_tag": sys.implementation.cache_tag,
    }


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CorrespondenceError(f"could not read JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise CorrespondenceError(f"JSON root must be an object: {path}")
    return value


def write_json(path: Path, value: Any, *, compact: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        if compact:
            json.dump(value, stream, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False)
        stream.write("\n")
    temporary.replace(path)


def require_hash(actual: str, expected_key: str, label: str) -> None:
    expected = EXPECTED[expected_key]
    if actual.upper() != expected:
        raise CorrespondenceError(f"{label} SHA-256 mismatch: {actual.upper()} != {expected}")


def sign_extend(value: int, bits: int) -> int:
    sign = 1 << (bits - 1)
    return (value ^ sign) - sign


def normalize_branch_word(word: int) -> int:
    """Clear only PPC b/bl LI or bc BD displacement bits."""
    opcode = word >> 26
    if opcode == 18:
        return word & 0xFC000003
    if opcode == 16:
        return word & 0xFFFF0003
    return word


def direct_branch_target(word: int, address: int) -> int | None:
    opcode = word >> 26
    if opcode == 18:
        displacement = sign_extend(word & 0x03FFFFFC, 26)
    elif opcode == 16:
        displacement = sign_extend(word & 0x0000FFFC, 16)
    else:
        return None
    if word & 2:
        return displacement & 0xFFFFFFFF
    return (address + displacement) & 0xFFFFFFFF


def instruction_structure(word: int) -> bytes:
    opcode = word >> 26
    extended = (word >> 1) & 0x3FF if opcode in {19, 31, 59, 63} else 0
    return struct.pack(">HH", opcode, extended)


def materialized_addresses(words: list[int]) -> list[tuple[int, int]]:
    """Recover conservative lis/addi and lis/ori 32-bit address pairs.

    Returns (instruction-index, address). The consumer still verifies that the
    recovered address lies in an initialized image block.
    """
    result: set[tuple[int, int]] = set()
    for index, word in enumerate(words):
        if word >> 26 != 15 or ((word >> 16) & 0x1F) != 0:
            continue
        register = (word >> 21) & 0x1F
        high_imm = word & 0xFFFF
        signed_high = high_imm if high_imm < 0x8000 else high_imm - 0x10000
        high = (signed_high << 16) & 0xFFFFFFFF
        for following_index in range(index + 1, min(index + 6, len(words))):
            candidate = words[following_index]
            opcode = candidate >> 26
            if opcode == 14 and ((candidate >> 16) & 0x1F) == register:
                low = candidate & 0xFFFF
                signed_low = low if low < 0x8000 else low - 0x10000
                result.add((index, (high + signed_low) & 0xFFFFFFFF))
            elif opcode == 24 and ((candidate >> 21) & 0x1F) == register:
                result.add((index, high | (candidate & 0xFFFF)))
    return sorted(result)


@dataclass(frozen=True)
class MemoryBlock:
    name: str
    start: int
    data: bytes
    read: bool
    write: bool
    execute: bool
    relative_path: str
    sha256: str

    @property
    def end(self) -> int:
        return self.start + len(self.data)


@dataclass
class FunctionEvidence:
    start: int
    size: int
    pdata_record: int
    index: int
    code: bytes
    raw_sha256: str = ""
    branch_normalized_sha256: str = ""
    opcode_structure_sha256: str = ""
    constant_signature_sha256: str = ""
    boundary_prefix_sha256: str = ""
    instruction_count: int = 0
    direct_calls: list[tuple[int, int]] = field(default_factory=list)
    conditional_branches: int = 0
    unconditional_branches: int = 0
    returns: int = 0
    indirect_branches: int = 0
    indirect_calls: int = 0
    block_count: int = 0
    edge_count: int = 0
    cfg_sha256: str = ""
    shape_class: str = ""
    string_references: set[str] = field(default_factory=set)
    data_anchors: set[str] = field(default_factory=set)
    materialized_reference_count: int = 0
    boundary_flags: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)

    @property
    def end(self) -> int:
        return self.start + self.size


@dataclass
class BuildAnalysis:
    build_id: str
    manifest_path: Path
    manifest_sha256: str
    manifest: dict[str, Any]
    blocks: list[MemoryBlock]
    functions: list[FunctionEvidence]
    executable_fingerprint: str


def load_build(derived_root: Path, build_id: str) -> tuple[dict[str, Any], list[MemoryBlock], Path]:
    manifest_path = derived_root / build_id / "derived-image.json"
    manifest = read_json(manifest_path)
    raw_blocks = manifest.get("memory_blocks")
    if not isinstance(raw_blocks, list) or not raw_blocks:
        raise CorrespondenceError(f"no memory blocks in {manifest_path}")
    blocks: list[MemoryBlock] = []
    for index, raw in enumerate(raw_blocks):
        if not isinstance(raw, dict):
            raise CorrespondenceError(f"invalid block {index} in {manifest_path}")
        relative = raw.get("derived_relative_path")
        if not isinstance(relative, str):
            raise CorrespondenceError(f"block {index} has no derived path in {manifest_path}")
        path = derived_root / build_id / relative
        try:
            data = path.read_bytes()
        except OSError as error:
            raise CorrespondenceError(f"could not read derived section {path}: {error}") from error
        actual_hash = sha256_bytes(data)
        expected_hash = str(raw.get("sha256", "")).upper()
        if actual_hash != expected_hash:
            raise CorrespondenceError(
                f"derived section hash mismatch for {build_id}/{relative}: "
                f"{actual_hash} != {expected_hash}"
            )
        if len(data) != raw.get("size"):
            raise CorrespondenceError(
                f"derived section size mismatch for {build_id}/{relative}: "
                f"{len(data)} != {raw.get('size')}"
            )
        blocks.append(
            MemoryBlock(
                name=str(raw.get("name")),
                start=int(str(raw.get("start")), 16),
                data=data,
                read=bool(raw.get("read")),
                write=bool(raw.get("write")),
                execute=bool(raw.get("execute")),
                relative_path=relative,
                sha256=actual_hash,
            )
        )
    blocks.sort(key=lambda block: (block.start, block.name))
    for previous, current in zip(blocks, blocks[1:]):
        if previous.end > current.start:
            raise CorrespondenceError(
                f"overlapping initialized blocks in {build_id}: {previous.name}/{current.name}"
            )
    return manifest, blocks, manifest_path


def executable_fingerprint(blocks: list[MemoryBlock]) -> str:
    executable = [block for block in blocks if block.execute and block.data]
    spans: list[tuple[int, bytearray, int]] = []
    for block in executable:
        permissions = (1 if block.read else 0) | (2 if block.write else 0) | 4
        if spans and spans[-1][0] + len(spans[-1][1]) == block.start and spans[-1][2] == permissions:
            spans[-1][1].extend(block.data)
        else:
            spans.append((block.start, bytearray(block.data), permissions))
    digest = hashlib.sha256()
    digest.update(b"FABLE2_EXECUTABLE_MEMORY_V1\0")
    digest.update(struct.pack(">I", len(spans)))
    for start, data, permissions in spans:
        digest.update(struct.pack(">QQB", start, len(data), permissions))
        digest.update(data)
    return digest.hexdigest().upper()


def extract_string_map(blocks: list[MemoryBlock]) -> dict[int, str]:
    result: dict[int, str] = {}

    def useful(value: str) -> bool:
        if not 8 <= len(value) <= 160 or not any(character.isalpha() for character in value):
            return False
        counts = collections.Counter(value)
        return len(counts) >= 4 and counts.most_common(1)[0][1] * 2 < len(value)

    for block in blocks:
        if block.execute:
            continue
        for match in ASCII_RE.finditer(block.data):
            value = match.group().decode("ascii")
            if useful(value):
                result[block.start + match.start()] = value
        for match in UTF16_RE.finditer(block.data):
            value = match.group().decode("utf-16le")
            if useful(value):
                result.setdefault(block.start + match.start(), value)
    return result


def block_for_address(blocks: list[MemoryBlock], address: int) -> MemoryBlock | None:
    starts = [block.start for block in blocks]
    index = bisect.bisect_right(starts, address) - 1
    if index >= 0 and address < blocks[index].end:
        return blocks[index]
    return None


def compute_cfg(words: list[int], start: int) -> tuple[int, int, str]:
    leaders = {0}
    instruction_count = len(words)
    for index, word in enumerate(words):
        opcode = word >> 26
        target = direct_branch_target(word, start + index * 4)
        lk = bool(word & 1)
        if opcode in {16, 18} and not lk and target is not None:
            target_index = (target - start) // 4
            if start <= target < start + instruction_count * 4 and target % 4 == 0:
                leaders.add(target_index)
            if opcode == 16 and index + 1 < instruction_count:
                leaders.add(index + 1)
            elif opcode == 18 and index + 1 < instruction_count:
                leaders.add(index + 1)
        elif opcode == 19 and ((word >> 1) & 0x3FF) in {16, 528} and index + 1 < instruction_count:
            leaders.add(index + 1)
    ordered = sorted(leader for leader in leaders if 0 <= leader < instruction_count)
    leader_to_block = {leader: index for index, leader in enumerate(ordered)}
    edges: set[tuple[int, int, str]] = set()
    block_lengths: list[int] = []
    for block_index, leader in enumerate(ordered):
        end = ordered[block_index + 1] if block_index + 1 < len(ordered) else instruction_count
        block_lengths.append(end - leader)
        last_index = end - 1
        word = words[last_index]
        opcode = word >> 26
        target = direct_branch_target(word, start + last_index * 4)
        lk = bool(word & 1)
        if opcode in {16, 18} and not lk and target is not None:
            target_index = (target - start) // 4
            target_block = leader_to_block.get(target_index)
            if target_block is not None:
                edges.add((block_index, target_block, "branch"))
            if opcode == 16 and block_index + 1 < len(ordered):
                edges.add((block_index, block_index + 1, "fallthrough"))
        elif opcode == 19 and ((word >> 1) & 0x3FF) in {16, 528}:
            pass
        elif block_index + 1 < len(ordered):
            edges.add((block_index, block_index + 1, "fallthrough"))
    shape = {
        "block_instruction_counts": block_lengths,
        "edges": [list(edge) for edge in sorted(edges)],
    }
    return len(ordered), len(edges), sha256_bytes(canonical_json_bytes(shape))


def analyze_function(
    start: int,
    code: bytes,
    pdata_record: int,
    index: int,
    blocks: list[MemoryBlock],
    strings: dict[int, str],
) -> FunctionEvidence:
    words = list(struct.unpack(f">{len(code) // 4}I", code))
    normalized = b"".join(struct.pack(">I", normalize_branch_word(word)) for word in words)
    structure = b"".join(instruction_structure(word) for word in words)
    direct_calls: list[tuple[int, int]] = []
    conditional = 0
    unconditional = 0
    returns = 0
    indirect = 0
    indirect_calls = 0
    constants: list[int] = []
    for word_index, word in enumerate(words):
        address = start + word_index * 4
        opcode = word >> 26
        lk = bool(word & 1)
        if opcode == 16:
            conditional += 1
            if lk:
                target = direct_branch_target(word, address)
                if target is not None:
                    direct_calls.append((word_index * 4, target))
        elif opcode == 18:
            target = direct_branch_target(word, address)
            if lk and target is not None:
                direct_calls.append((word_index * 4, target))
            elif not lk:
                unconditional += 1
        elif opcode == 19 and ((word >> 1) & 0x3FF) in {16, 528}:
            if lk:
                indirect_calls += 1
            elif ((word >> 1) & 0x3FF) == 16:
                returns += 1
            else:
                indirect += 1
        if opcode in IMMEDIATE_OPCODES:
            constants.append(word & 0xFFFF)
    block_count, edge_count, cfg_sha256 = compute_cfg(words, start)
    string_references: set[str] = set()
    data_anchors: set[str] = set()
    materialized = materialized_addresses(words)
    for _, address in materialized:
        value = strings.get(address)
        if value is not None:
            string_references.add(value)
        block = block_for_address(blocks, address)
        if block is not None and block.name in {".data", ".rdata", ".edata"}:
            offset = address - block.start
            sample = block.data[offset : min(offset + 16, len(block.data))]
            if len(sample) == 16 and len(set(sample)) >= 4:
                data_anchors.add(
                    f"{block.name}:{address_text(address)}:{sha256_bytes(sample)}"
                )
    padding_words = sum(word in {0, 0x60000000, 0xFFFFFFFF} for word in words)
    risk_flags: list[str] = []
    if len(code) <= 16:
        risk_flags.append("tiny-leaf")
    if len(code) <= 32 and (indirect or indirect_calls):
        risk_flags.append("short-indirect-thunk")
    if words and padding_words * 2 >= len(words):
        risk_flags.append("padding-dominated")
    if len(code) <= 32 and len(direct_calls) == 1 and returns <= 1:
        risk_flags.append("short-direct-thunk")
    if len(code) <= 16 and conditional == 0 and not direct_calls and not indirect:
        shape_class = "tiny-leaf"
    elif indirect or indirect_calls:
        shape_class = "indirect-branch"
    elif direct_calls:
        shape_class = "direct-call"
    elif conditional or unconditional:
        shape_class = "branching"
    else:
        shape_class = "linear"
    return FunctionEvidence(
        start=start,
        size=len(code),
        pdata_record=pdata_record,
        index=index,
        code=code,
        raw_sha256=sha256_bytes(code),
        branch_normalized_sha256=sha256_bytes(normalized),
        opcode_structure_sha256=sha256_bytes(structure),
        constant_signature_sha256=sha256_bytes(
            b"".join(struct.pack(">H", constant) for constant in constants)
        ),
        boundary_prefix_sha256=sha256_bytes(normalized[:16]) if len(normalized) >= 16 else "",
        instruction_count=len(words),
        direct_calls=direct_calls,
        conditional_branches=conditional,
        unconditional_branches=unconditional,
        returns=returns,
        indirect_branches=indirect,
        indirect_calls=indirect_calls,
        block_count=block_count,
        edge_count=edge_count,
        cfg_sha256=cfg_sha256,
        shape_class=shape_class,
        string_references=string_references,
        data_anchors=data_anchors,
        materialized_reference_count=len(materialized),
        risk_flags=sorted(set(risk_flags)),
    )


def analyze_build(derived_root: Path, build_id: str) -> BuildAnalysis:
    manifest, blocks, manifest_path = load_build(derived_root, build_id)
    by_name = {block.name: block for block in blocks}
    if ".pdata" not in by_name or ".text" not in by_name:
        raise CorrespondenceError(f"{build_id} does not have required .pdata/.text blocks")
    pdata = by_name[".pdata"]
    text = by_name[".text"]
    executable_blocks = [block for block in blocks if block.execute]
    if len(pdata.data) % 8:
        raise CorrespondenceError(f"{build_id} .pdata size is not divisible by 8")
    strings = extract_string_map(blocks)
    raw_records: list[tuple[int, int, int]] = []
    for offset in range(0, len(pdata.data), 8):
        start, unwind = struct.unpack_from(">II", pdata.data, offset)
        size = ((unwind >> 8) & 0x3FFFFF) * 4
        if start == 0 or size == 0:
            raise CorrespondenceError(
                f"{build_id} invalid .pdata record at {address_text(pdata.start + offset)}"
            )
        code_block = block_for_address(executable_blocks, start)
        if (
            start % 4
            or size % 4
            or code_block is None
            or start + size > code_block.end
        ):
            raise CorrespondenceError(
                f"{build_id} out-of-range .pdata function {address_text(start)}+{size:#x}"
            )
        raw_records.append((start, size, pdata.start + offset))
    if raw_records != sorted(raw_records):
        raise CorrespondenceError(f"{build_id} .pdata functions are not sorted")
    starts = [record[0] for record in raw_records]
    if len(starts) != len(set(starts)):
        raise CorrespondenceError(f"{build_id} .pdata has duplicate function starts")
    functions: list[FunctionEvidence] = []
    for index, (start, size, record_address) in enumerate(raw_records):
        code_block = block_for_address(executable_blocks, start)
        assert code_block is not None
        offset = start - code_block.start
        code = code_block.data[offset : offset + size]
        function = analyze_function(start, code, record_address, index, blocks, strings)
        if index and functions[-1].end > function.start:
            functions[-1].boundary_flags.append("overlaps-next-pdata-function")
            function.boundary_flags.append("overlaps-previous-pdata-function")
        functions.append(function)
    declared_count = manifest.get("program", {}).get("function_count")
    if declared_count != len(functions):
        raise CorrespondenceError(
            f"{build_id} function count mismatch: manifest={declared_count} pdata={len(functions)}"
        )
    return BuildAnalysis(
        build_id=build_id,
        manifest_path=manifest_path,
        manifest_sha256=sha256_file(manifest_path),
        manifest=manifest,
        blocks=blocks,
        functions=functions,
        executable_fingerprint=executable_fingerprint(blocks),
    )


def groups(functions: list[FunctionEvidence], key: str) -> dict[str, list[FunctionEvidence]]:
    result: dict[str, list[FunctionEvidence]] = collections.defaultdict(list)
    for function in functions:
        result[getattr(function, key)].append(function)
    return dict(result)


def shape_values(function: FunctionEvidence) -> dict[str, Any]:
    return {
        "instruction_count": function.instruction_count,
        "conditional_branches": function.conditional_branches,
        "unconditional_branches": function.unconditional_branches,
        "direct_calls": len(function.direct_calls),
        "returns": function.returns,
        "indirect_branches": function.indirect_branches,
        "indirect_calls": function.indirect_calls,
        "block_count": function.block_count,
        "edge_count": function.edge_count,
        "shape_class": function.shape_class,
    }


def pair_evidence(
    donor: FunctionEvidence,
    target: FunctionEvidence,
    accepted: dict[int, int],
    donor_functions: list[FunctionEvidence],
    target_by_start: dict[int, FunctionEvidence],
) -> dict[str, Any]:
    raw_equal = donor.raw_sha256 == target.raw_sha256
    normalized_equal = donor.branch_normalized_sha256 == target.branch_normalized_sha256
    opcode_equal = donor.opcode_structure_sha256 == target.opcode_structure_sha256
    shape_equal = shape_values(donor) == shape_values(target)
    cfg_equal = donor.cfg_sha256 == target.cfg_sha256
    constant_equal = donor.constant_signature_sha256 == target.constant_signature_sha256
    neighbour_delta_support = 0
    neighbour_order_support = 0
    neighbour_order_contradictions = 0
    anchors: list[dict[str, Any]] = []
    low = max(0, donor.index - NEIGHBOUR_WINDOW)
    high = min(len(donor_functions), donor.index + NEIGHBOUR_WINDOW + 1)
    for neighbour in donor_functions[low:high]:
        mapped = accepted.get(neighbour.start)
        if mapped is None or neighbour.start == donor.start:
            continue
        relative = donor.start - neighbour.start
        predicted = mapped + relative
        delta_equal = predicted == target.start
        order_ok = (relative > 0 and mapped < target.start) or (relative < 0 and mapped > target.start)
        if delta_equal:
            neighbour_delta_support += 1
        if order_ok:
            neighbour_order_support += 1
        else:
            neighbour_order_contradictions += 1
        anchors.append(
            {
                "donor_anchor": address_text(neighbour.start),
                "target_anchor": address_text(mapped),
                "exact_relative_delta": delta_equal,
                "ordering_consistent": order_ok,
            }
        )
    topology_support = 0
    topology_contradictions = 0
    topology_observations: list[dict[str, Any]] = []
    target_calls = {offset: call_target for offset, call_target in target.direct_calls}
    for offset, donor_callee in donor.direct_calls:
        mapped_callee = accepted.get(donor_callee)
        target_callee = target_calls.get(offset)
        if mapped_callee is None or target_callee not in target_by_start:
            continue
        consistent = mapped_callee == target_callee
        if consistent:
            topology_support += 1
        else:
            topology_contradictions += 1
        topology_observations.append(
            {
                "instruction_offset": address_text(offset),
                "donor_callee": address_text(donor_callee),
                "mapped_donor_callee": address_text(mapped_callee),
                "target_callee": address_text(target_callee),
                "consistent": consistent,
            }
        )
    shared_strings = sorted(donor.string_references & target.string_references)
    shared_data = sorted(donor.data_anchors & target.data_anchors)
    classes: list[str] = []
    if shape_equal and cfg_equal:
        classes.append("cfg-and-branch-shape")
    if neighbour_delta_support:
        classes.append("local-address-delta-neighbourhood")
    elif neighbour_order_support:
        classes.append("local-ordering-neighbourhood")
    if topology_support:
        classes.append("direct-call-topology")
    if shared_strings:
        classes.append("string-content-anchor")
    if shared_data:
        classes.append("data-content-anchor")
    contradictions: list[str] = []
    if donor.size != target.size:
        contradictions.append("function-size-differs")
    if not shape_equal:
        contradictions.append("branch-shape-differs")
    if not cfg_equal:
        contradictions.append("cfg-shape-differs")
    if neighbour_order_contradictions:
        contradictions.append("mapped-neighbour-order-contradiction")
    if topology_contradictions:
        contradictions.append("mapped-direct-call-contradiction")
    return {
        "fingerprints": {
            "raw_equal": raw_equal,
            "branch_normalized_equal": normalized_equal,
            "opcode_structure_equal": opcode_equal,
            "constant_signature_equal": constant_equal,
            "donor_raw_sha256": donor.raw_sha256,
            "target_raw_sha256": target.raw_sha256,
            "donor_branch_normalized_sha256": donor.branch_normalized_sha256,
            "target_branch_normalized_sha256": target.branch_normalized_sha256,
            "donor_opcode_structure_sha256": donor.opcode_structure_sha256,
            "target_opcode_structure_sha256": target.opcode_structure_sha256,
            "donor_constant_signature_sha256": donor.constant_signature_sha256,
            "target_constant_signature_sha256": target.constant_signature_sha256,
        },
        "boundaries": {
            "same_size": donor.size == target.size,
            "donor_boundary_flags": donor.boundary_flags,
            "target_boundary_flags": target.boundary_flags,
        },
        "shape": {
            "equal": shape_equal,
            "cfg_equal": cfg_equal,
            "donor": shape_values(donor),
            "target": shape_values(target),
        },
        "neighbourhood": {
            "exact_delta_support": neighbour_delta_support,
            "ordering_support": neighbour_order_support,
            "ordering_contradictions": neighbour_order_contradictions,
            "anchor_count": len(anchors),
            "anchors": anchors[:4],
        },
        "topology": {
            "support": topology_support,
            "contradictions": topology_contradictions,
            "observation_count": len(topology_observations),
            "observations": topology_observations[:4],
        },
        "references": {
            "shared_strings": shared_strings[:8],
            "shared_string_count": len(shared_strings),
            "shared_data_anchors": shared_data[:8],
            "shared_data_anchor_count": len(shared_data),
        },
        "corroborating_feature_classes": classes,
        "contradictions": contradictions,
    }


def has_required_corroboration(evidence: dict[str, Any]) -> bool:
    classes = set(evidence["corroborating_feature_classes"])
    required = {
        "local-address-delta-neighbourhood",
        "direct-call-topology",
        "string-content-anchor",
        "data-content-anchor",
    }
    return len(classes) >= 2 and bool(classes & required)


def candidate_score(evidence: dict[str, Any], donor: FunctionEvidence, target: FunctionEvidence) -> int:
    fingerprints = evidence["fingerprints"]
    score = 0
    score += 100 if fingerprints["raw_equal"] else 0
    score += 60 if fingerprints["branch_normalized_equal"] else 0
    score += 10 if fingerprints["opcode_structure_equal"] else 0
    score += 10 if evidence["shape"]["equal"] else 0
    score += 15 if evidence["shape"]["cfg_equal"] else 0
    score += min(2, evidence["neighbourhood"]["exact_delta_support"]) * 12
    score += min(2, evidence["topology"]["support"]) * 15
    score += 25 if evidence["references"]["shared_string_count"] else 0
    score += min(3, evidence["references"]["shared_data_anchor_count"]) * 5
    score -= len(evidence["contradictions"]) * 50
    score -= 25 if donor.risk_flags or target.risk_flags else 0
    return score


def compact_accepted_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    source = evidence["fingerprints"]

    def fingerprint_pair(name: str) -> dict[str, Any]:
        equal = source[f"{name}_equal"]
        donor_hash = source[f"donor_{name}_sha256"]
        target_hash = source[f"target_{name}_sha256"]
        if equal:
            return {"equal": True, "shared_sha256": donor_hash}
        return {"equal": False, "donor_sha256": donor_hash, "target_sha256": target_hash}

    shape = evidence["shape"]
    shared_shape = shape["donor"] if shape["equal"] else None
    return {
        "fingerprints": {
            "raw": fingerprint_pair("raw"),
            "branch_normalized": fingerprint_pair("branch_normalized"),
            "opcode_structure": fingerprint_pair("opcode_structure"),
            "constant_signature": fingerprint_pair("constant_signature"),
        },
        "boundaries": evidence["boundaries"],
        "shape": {
            "equal": shape["equal"],
            "cfg_equal": shape["cfg_equal"],
            "shared": shared_shape,
            "donor": None if shared_shape is not None else shape["donor"],
            "target": None if shared_shape is not None else shape["target"],
        },
        "neighbourhood": evidence["neighbourhood"]
        | {"anchors": evidence["neighbourhood"]["anchors"][:2]},
        "topology": evidence["topology"]
        | {"observations": evidence["topology"]["observations"][:2]},
        "references": {
            "shared_strings": evidence["references"]["shared_strings"][:4],
            "shared_string_count": evidence["references"]["shared_string_count"],
            "shared_data_anchors": evidence["references"]["shared_data_anchors"][:4],
            "shared_data_anchor_count": evidence["references"]["shared_data_anchor_count"],
        },
        "corroborating_feature_classes": evidence["corroborating_feature_classes"],
        "contradictions": evidence["contradictions"],
    }


def fingerprint_groups(
    donor_functions: list[FunctionEvidence], target_functions: list[FunctionEvidence]
) -> tuple[dict[str, dict[str, list[FunctionEvidence]]], dict[str, dict[str, list[FunctionEvidence]]]]:
    return (
        {key: groups(donor_functions, key) for key in FINGERPRINT_KEYS},
        {key: groups(target_functions, key) for key in FINGERPRINT_KEYS},
    )


def boundary_change_candidate(donor: FunctionEvidence, target: FunctionEvidence | None) -> bool:
    if target is None or donor.size == target.size:
        return False
    common = min(donor.size, target.size)
    if common < 8:
        return False
    donor_prefix = donor.code[:common]
    target_prefix = target.code[:common]
    if donor_prefix == target_prefix:
        return True
    donor_words = struct.unpack(f">{common // 4}I", donor_prefix[: common - common % 4])
    target_words = struct.unpack(f">{common // 4}I", target_prefix[: common - common % 4])
    return all(
        normalize_branch_word(left) == normalize_branch_word(right)
        for left, right in zip(donor_words, target_words)
    )


def normalized_prefix_boundary_candidate(
    donor: FunctionEvidence, target: FunctionEvidence
) -> bool:
    if donor.size == target.size or min(donor.size, target.size) < 16:
        return False
    length = min(32, donor.size, target.size)
    donor_words = struct.unpack(f">{length // 4}I", donor.code[:length])
    target_words = struct.unpack(f">{length // 4}I", target.code[:length])
    return all(
        normalize_branch_word(left) == normalize_branch_word(right)
        for left, right in zip(donor_words, target_words)
    )


def unique_pairs(
    key: str,
    donor_groups: dict[str, dict[str, list[FunctionEvidence]]],
    target_groups: dict[str, dict[str, list[FunctionEvidence]]],
) -> list[tuple[FunctionEvidence, FunctionEvidence]]:
    result = []
    for digest in sorted(set(donor_groups[key]) & set(target_groups[key])):
        left = donor_groups[key][digest]
        right = target_groups[key][digest]
        if len(left) == 1 and len(right) == 1:
            result.append((left[0], right[0]))
    return result


def match_builds(
    donor_analysis: BuildAnalysis,
    target_analysis: BuildAnalysis,
    *,
    include_index: bool = True,
    include_exhaustive: bool = True,
) -> dict[str, Any]:
    donor_functions = donor_analysis.functions
    target_functions = target_analysis.functions
    donor_by_start = {function.start: function for function in donor_functions}
    target_by_start = {function.start: function for function in target_functions}
    donor_groups, target_groups = fingerprint_groups(donor_functions, target_functions)
    donor_boundary_groups = groups(
        [function for function in donor_functions if function.boundary_prefix_sha256],
        "boundary_prefix_sha256",
    )
    target_boundary_groups = groups(
        [function for function in target_functions if function.boundary_prefix_sha256],
        "boundary_prefix_sha256",
    )
    accepted: dict[int, int] = {}
    accepted_status: dict[int, str] = {}
    rejected_reason: dict[int, str] = {}

    raw_pairs = unique_pairs("raw_sha256", donor_groups, target_groups)
    provisional = {
        donor.start: target.start
        for donor, target in raw_pairs
        if not donor.risk_flags
        and not target.risk_flags
        and donor.size == target.size
        and not donor.boundary_flags
        and not target.boundary_flags
        and shape_values(donor) == shape_values(target)
        and donor.cfg_sha256 == target.cfg_sha256
    }
    for donor, target in raw_pairs:
        if donor.start not in provisional:
            continue
        evidence = pair_evidence(
            donor, target, provisional, donor_functions, target_by_start
        )
        if evidence["contradictions"]:
            rejected_reason[donor.start] = "contradictory-exact-evidence"
            continue
        accepted[donor.start] = target.start
        accepted_status[donor.start] = "accepted-exact-unique"

    used_targets = set(accepted.values())
    for donor, target in raw_pairs:
        if donor.start in accepted or target.start in used_targets:
            continue
        if not (donor.risk_flags or target.risk_flags):
            continue
        evidence = pair_evidence(donor, target, accepted, donor_functions, target_by_start)
        if not evidence["contradictions"] and has_required_corroboration(evidence):
            accepted[donor.start] = target.start
            accepted_status[donor.start] = "accepted-exact-unique"
            used_targets.add(target.start)
        else:
            rejected_reason[donor.start] = "risky-idiom-without-corroboration"

    normalized_pairs = unique_pairs(
        "branch_normalized_sha256", donor_groups, target_groups
    )
    changed = True
    while changed:
        changed = False
        for donor, target in normalized_pairs:
            if donor.start in accepted or target.start in used_targets:
                continue
            if donor.risk_flags or target.risk_flags or donor.boundary_flags or target.boundary_flags:
                rejected_reason.setdefault(donor.start, "normalized-risk-or-boundary-quarantine")
                continue
            evidence = pair_evidence(donor, target, accepted, donor_functions, target_by_start)
            if (
                evidence["fingerprints"]["raw_equal"]
                or evidence["contradictions"]
                or not has_required_corroboration(evidence)
            ):
                continue
            accepted[donor.start] = target.start
            accepted_status[donor.start] = "accepted-normalized-corroborated"
            used_targets.add(target.start)
            changed = True

    audit_changed = True
    while audit_changed:
        audit_changed = False
        for donor_start, target_start in sorted(list(accepted.items())):
            donor = donor_by_start[donor_start]
            target = target_by_start[target_start]
            evidence = pair_evidence(donor, target, accepted, donor_functions, target_by_start)
            if evidence["contradictions"]:
                del accepted[donor_start]
                del accepted_status[donor_start]
                used_targets.remove(target_start)
                rejected_reason[donor_start] = "final-contradiction-audit"
                audit_changed = True

    if len(accepted) != len(set(accepted.values())):
        raise CorrespondenceError("acceptance policy produced a non-injective mapping")

    accepted_records: list[dict[str, Any]] = []
    for donor_start, target_start in sorted(accepted.items()):
        donor = donor_by_start[donor_start]
        target = target_by_start[target_start]
        evidence = pair_evidence(donor, target, accepted, donor_functions, target_by_start)
        status = accepted_status[donor_start]
        accepted_records.append(
            {
                "donor_start": address_text(donor.start),
                "donor_end_exclusive": address_text(donor.end),
                "target_start": address_text(target.start),
                "target_end_exclusive": address_text(target.end),
                "size": donor.size,
                "status": status,
                "evidence_grade": "confirmed" if status == "accepted-exact-unique" else "strongly-supported",
                "semantic_name_assigned": False,
                "acceptance_policy": POLICY_VERSION,
                "evidence": compact_accepted_evidence(evidence),
                "contradiction_checks": {
                    "boundary_valid": not donor.boundary_flags and not target.boundary_flags,
                    "reciprocal_unique": True,
                    "one_to_one": True,
                    "contradictions_absent": not evidence["contradictions"],
                },
            }
        )

    group_statistics: dict[str, Any] = {}
    exhaustive_groups: dict[str, list[dict[str, Any]]] = {}
    for key in FINGERPRINT_KEYS:
        shared = sorted(set(donor_groups[key]) & set(target_groups[key]))
        records = []
        edge_count = 0
        for digest in shared:
            donor_members = donor_groups[key][digest]
            target_members = target_groups[key][digest]
            edge_count += len(donor_members) * len(target_members)
            if include_exhaustive:
                records.append(
                    {
                        "fingerprint": digest,
                        "donor_members": [address_text(item.start) for item in donor_members],
                        "target_members": [address_text(item.start) for item in target_members],
                    }
                )
        exhaustive_groups[key] = records if include_exhaustive else []
        group_statistics[key] = {
            "donor_unique_fingerprints": sum(len(value) == 1 for value in donor_groups[key].values()),
            "target_unique_fingerprints": sum(len(value) == 1 for value in target_groups[key].values()),
            "shared_fingerprint_groups": len(shared),
            "reciprocal_unique_pairs": sum(
                len(donor_groups[key][digest]) == 1 and len(target_groups[key][digest]) == 1
                for digest in shared
            ),
            "candidate_edge_count_within_feature": edge_count,
        }
    boundary_shared = sorted(set(donor_boundary_groups) & set(target_boundary_groups))
    boundary_edge_count = sum(
        len(donor_boundary_groups[digest]) * len(target_boundary_groups[digest])
        for digest in boundary_shared
    )
    group_statistics["boundary_normalized_prefix16_sha256"] = {
        "donor_unique_fingerprints": sum(len(value) == 1 for value in donor_boundary_groups.values()),
        "target_unique_fingerprints": sum(len(value) == 1 for value in target_boundary_groups.values()),
        "shared_fingerprint_groups": len(boundary_shared),
        "reciprocal_unique_pairs": sum(
            len(donor_boundary_groups[digest]) == 1
            and len(target_boundary_groups[digest]) == 1
            for digest in boundary_shared
        ),
        "candidate_edge_count_within_feature": boundary_edge_count,
        "acceptance_eligible": False,
        "purpose": "possible split/merge or shifted-boundary review only",
    }
    exhaustive_groups["boundary_normalized_prefix16_sha256"] = (
        [
            {
                "fingerprint": digest,
                "donor_members": [
                    address_text(item.start) for item in donor_boundary_groups[digest]
                ],
                "target_members": [
                    address_text(item.start) for item in target_boundary_groups[digest]
                ],
            }
            for digest in boundary_shared
        ]
        if include_exhaustive
        else []
    )

    index_records: list[dict[str, Any]] = []
    status_counts: collections.Counter[str] = collections.Counter()
    for donor in donor_functions:
        candidates: set[int] = set()
        per_feature_counts: dict[str, int] = {}
        for key in FINGERPRINT_KEYS:
            members = target_groups[key].get(getattr(donor, key), [])
            per_feature_counts[key] = len(members)
            candidates.update(member.start for member in members)
        donor_boundary_members = donor_boundary_groups.get(donor.boundary_prefix_sha256, [])
        target_boundary_members = target_boundary_groups.get(donor.boundary_prefix_sha256, [])
        boundary_members = (
            target_boundary_members
            if len(donor_boundary_members) == 1 and len(target_boundary_members) == 1
            else []
        )
        boundary_targets = {
            member.start
            for member in boundary_members
            if normalized_prefix_boundary_candidate(donor, member)
        }
        candidates.update(boundary_targets)
        same_start = target_by_start.get(donor.start)
        boundary_change = bool(boundary_targets) or boundary_change_candidate(donor, same_start)
        if boundary_change and same_start is not None:
            candidates.add(same_start.start)
        accepted_target = accepted.get(donor.start)
        if accepted_target is not None:
            status = accepted_status[donor.start]
            ambiguity_class = "accepted-reciprocal-one-to-one"
        elif boundary_change:
            status = "boundary-change"
            ambiguity_class = "same-start-prefix-with-changed-pdata-boundary"
        elif donor.risk_flags and candidates:
            status = "quarantined"
            ambiguity_class = rejected_reason.get(donor.start, "risky-compiler-idiom")
        elif donor.start in rejected_reason:
            status = "quarantined"
            ambiguity_class = rejected_reason[donor.start]
        elif not candidates:
            status = "unmatched"
            ambiguity_class = "no-shared-fingerprint-candidate"
        elif len(candidates) > 1:
            status = "ambiguous"
            ambiguity_class = "multiple-fingerprint-candidates"
        else:
            status = "candidate-structural"
            ambiguity_class = "unique-candidate-below-acceptance-threshold"
        status_counts[status] += 1
        if include_index:
            scored: list[tuple[int, int, dict[str, Any]]] = []
            if accepted_target is None:
                for candidate_start in candidates:
                    target = target_by_start[candidate_start]
                    evidence = pair_evidence(donor, target, accepted, donor_functions, target_by_start)
                    scored.append((candidate_score(evidence, donor, target), candidate_start, evidence))
            scored.sort(key=lambda item: (-item[0], item[1]))
            top_candidates = []
            for score, candidate_start, evidence in scored[:TOP_CANDIDATE_LIMIT]:
                top_candidates.append(
                    {
                        "target_start": address_text(candidate_start),
                        "score": score,
                        "matching_features": [
                            name
                            for name, present in (
                                ("raw", evidence["fingerprints"]["raw_equal"]),
                                ("branch-normalized", evidence["fingerprints"]["branch_normalized_equal"]),
                                ("opcode-structure", evidence["fingerprints"]["opcode_structure_equal"]),
                                ("cfg", evidence["shape"]["cfg_equal"]),
                                ("local-delta", evidence["neighbourhood"]["exact_delta_support"] > 0),
                                ("call-topology", evidence["topology"]["support"] > 0),
                                ("string", evidence["references"]["shared_string_count"] > 0),
                                ("data", evidence["references"]["shared_data_anchor_count"] > 0),
                                (
                                    "boundary-prefix",
                                    candidate_start in boundary_targets,
                                ),
                            )
                            if present
                        ],
                        "contradictions": evidence["contradictions"],
                    }
                )
            index_records.append(
                {
                    "donor_start": address_text(donor.start),
                    "donor_end_exclusive": address_text(donor.end),
                    "size": donor.size,
                    "pdata_record": address_text(donor.pdata_record),
                    "fingerprints": {
                        "raw_sha256": donor.raw_sha256,
                        "branch_normalized_sha256": donor.branch_normalized_sha256,
                        "opcode_structure_sha256": donor.opcode_structure_sha256,
                        "constant_signature_sha256": donor.constant_signature_sha256,
                    },
                    "shape": shape_values(donor)
                    | {"cfg_sha256": donor.cfg_sha256},
                    "references": {
                        "materialized_address_count": donor.materialized_reference_count,
                        "string_count": len(donor.string_references),
                        "data_anchor_count": len(donor.data_anchors),
                    },
                    "boundary_flags": donor.boundary_flags,
                    "risk_flags": donor.risk_flags,
                    "status": status,
                    "candidate_count": len(candidates),
                    "candidate_counts_by_feature": per_feature_counts,
                    "ambiguity_class": ambiguity_class,
                    "accepted_target": address_text(accepted_target) if accepted_target is not None else None,
                    "top_candidates": top_candidates,
                }
            )

    return {
        "accepted": accepted_records,
        "accepted_map": accepted,
        "index": index_records,
        "status_counts": {status: status_counts.get(status, 0) for status in TERMINAL_STATUSES},
        "fingerprint_groups": group_statistics,
        "exhaustive_groups": exhaustive_groups,
    }


def size_bucket(size: int) -> str:
    if size <= 16:
        return "0001-0016"
    if size <= 32:
        return "0017-0032"
    if size <= 64:
        return "0033-0064"
    if size <= 256:
        return "0065-0256"
    if size <= 1024:
        return "0257-1024"
    return "1025-plus"


def aggregate_index(index: list[dict[str, Any]]) -> dict[str, Any]:
    by_size: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    by_shape: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    by_region: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    for record in index:
        status = record["status"]
        by_size[size_bucket(record["size"])][status] += 1
        by_shape[record["shape"]["shape_class"]][status] += 1
        address = int(record["donor_start"], 16)
        region = f"0x{address >> 20:03X}00000-0x{((address >> 20) + 1):03X}00000"
        by_region[region][status] += 1

    def serialize(values: dict[str, collections.Counter[str]]) -> list[dict[str, Any]]:
        return [
            {"bucket": bucket, "total": sum(counts.values()), "status_counts": dict(sorted(counts.items()))}
            for bucket, counts in sorted(values.items())
        ]

    return {
        "by_size_bucket": serialize(by_size),
        "by_function_shape": serialize(by_shape),
        "by_one_megabyte_donor_region": serialize(by_region),
    }


def compact_index(index: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the committed index complete but move verbose features to ignored output."""
    keys = (
        "donor_start",
        "donor_end_exclusive",
        "size",
        "status",
        "candidate_count",
        "ambiguity_class",
        "accepted_target",
        "top_candidates",
    )
    return [{key: row[key] for key in keys} for row in index]


def exhaustive_function_features(analysis: BuildAnalysis) -> list[dict[str, Any]]:
    return [
        {
            "start": address_text(function.start),
            "end_exclusive": address_text(function.end),
            "size": function.size,
            "pdata_record": address_text(function.pdata_record),
            "fingerprints": {
                "raw_sha256": function.raw_sha256,
                "branch_normalized_sha256": function.branch_normalized_sha256,
                "opcode_structure_sha256": function.opcode_structure_sha256,
                "constant_signature_sha256": function.constant_signature_sha256,
                "boundary_normalized_prefix16_sha256": function.boundary_prefix_sha256,
            },
            "shape": shape_values(function) | {"cfg_sha256": function.cfg_sha256},
            "direct_calls": [
                {"instruction_offset": address_text(offset), "target": address_text(target)}
                for offset, target in function.direct_calls
            ],
            "references": {
                "materialized_address_count": function.materialized_reference_count,
                "strings": sorted(function.string_references),
                "data_anchors": sorted(function.data_anchors),
            },
            "boundary_flags": function.boundary_flags,
            "risk_flags": function.risk_flags,
        }
        for function in analysis.functions
    ]


def build_review_queue(index: list[dict[str, Any]]) -> list[dict[str, Any]]:
    strata = collections.OrderedDict(
        (
            ("accepted-exact", lambda row: row["status"] == "accepted-exact-unique"),
            ("accepted-normalized", lambda row: row["status"] == "accepted-normalized-corroborated"),
            ("candidate-structural", lambda row: row["status"] == "candidate-structural"),
            ("ambiguous", lambda row: row["status"] == "ambiguous"),
            ("quarantined", lambda row: row["status"] == "quarantined"),
            ("boundary-change", lambda row: row["status"] == "boundary-change"),
            ("tiny-leaf", lambda row: "tiny-leaf" in row["risk_flags"]),
            ("indirect-branch", lambda row: row["shape"]["indirect_branches"] > 0),
            ("string-reference", lambda row: row["references"]["string_count"] > 0),
            ("data-anchor", lambda row: row["references"]["data_anchor_count"] > 0),
        )
    )
    selected: set[str] = set()
    queue: list[dict[str, Any]] = []
    for stratum, predicate in strata.items():
        candidates = [row for row in index if predicate(row) and row["donor_start"] not in selected]
        candidates.sort(
            key=lambda row: (
                -row["size"],
                -row["candidate_count"],
                row["donor_start"],
            )
        )
        for row in candidates[:5]:
            selected.add(row["donor_start"])
            queue.append(
                {
                    "stratum": stratum,
                    "donor_start": row["donor_start"],
                    "donor_end_exclusive": row["donor_end_exclusive"],
                    "size": row["size"],
                    "status": row["status"],
                    "candidate_count": row["candidate_count"],
                    "ambiguity_class": row["ambiguity_class"],
                    "accepted_target": row["accepted_target"],
                    "top_candidates": row["top_candidates"],
                    "review_reason": f"deterministic {stratum} stratum sample",
                }
            )
    return queue


def positive_control(result: dict[str, Any], total: int) -> dict[str, Any]:
    accepted = result["accepted"]
    correct = sum(record["donor_start"] == record["target_start"] for record in accepted)
    false = len(accepted) - correct
    if false:
        raise CorrespondenceError(
            f"positive control produced {false} false accepted cross-address pairs"
        )
    by_size: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    by_shape: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    for row in result["index"]:
        correct_status = row["accepted_target"] == row["donor_start"]
        by_size[size_bucket(row["size"])]["accepted_correct" if correct_status else "not_accepted"] += 1
        by_shape[row["shape"]["shape_class"]]["accepted_correct" if correct_status else "not_accepted"] += 1
    return {
        "oracle": "byte-identical July 2009 and build-23 initialized images; true pair is identical .pdata start and boundary",
        "total_functions_represented": total,
        "status_counts": result["status_counts"],
        "accepted_pairs": len(accepted),
        "correct_same_start_accepted_pairs": correct,
        "false_accepted_cross_address_pairs": false,
        "precision_definition": "correct same-start accepted pairs / all accepted pairs",
        "precision": round(correct / len(accepted), 12) if accepted else None,
        "recall_definition": "correct same-start accepted pairs / all oracle .pdata functions",
        "recall": round(correct / total, 12),
        "by_size_bucket": [
            {"bucket": bucket, **dict(counts)} for bucket, counts in sorted(by_size.items())
        ],
        "by_function_shape": [
            {"bucket": bucket, **dict(counts)} for bucket, counts in sorted(by_shape.items())
        ],
    }


def synthetic_function(start: int, words: Iterable[int], index: int) -> FunctionEvidence:
    code = b"".join(struct.pack(">I", word & 0xFFFFFFFF) for word in words)
    block = MemoryBlock(".text", start, code, True, False, True, "synthetic", sha256_bytes(code))
    return analyze_function(start, code, 0x81000000 + index * 8, index, [block], {})


def synthetic_analysis(build_id: str, specs: list[tuple[int, list[int]]]) -> BuildAnalysis:
    functions = [synthetic_function(start, words, index) for index, (start, words) in enumerate(specs)]
    return BuildAnalysis(build_id, Path("synthetic"), "0" * 64, {}, [], functions, "0" * 64)


def run_synthetic_fixtures() -> list[dict[str, Any]]:
    blr = 0x4E800020
    nop = 0x60000000
    fixtures: list[dict[str, Any]] = []

    branch_words = {
        "b": (0x48000020, 0x48000120),
        "bl": (0x48000021, 0x48000121),
        "bc": (0x41820020, 0x41820120),
    }
    branch_pass = all(
        normalize_branch_word(left) == normalize_branch_word(right) and left != right
        for left, right in branch_words.values()
    )
    fixtures.append({"name": "b-bl-bc-displacement-normalization", "passed": branch_pass})

    relocated_left = synthetic_analysis(
        "left",
        [
            (0x1000, [0x38600001, 0x38800002, 0x38A00003, 0x38C00004, blr]),
            (0x1020, [0x38600002, 0x38800003, 0x38A00004, 0x38C00005, 0x38E00006, blr]),
        ],
    )
    relocated_right = synthetic_analysis(
        "right",
        [
            (0x2000, [0x38600001, 0x38800002, 0x38A00003, 0x38C00004, blr]),
            (0x2020, [0x38600002, 0x38800003, 0x38A00004, 0x38C00005, 0x38E00006, blr]),
        ],
    )
    relocated = match_builds(relocated_left, relocated_right)
    fixtures.append(
        {
            "name": "identical-functions-relocated-as-block",
            "passed": len(relocated["accepted"]) == 2
            and {record["target_start"] for record in relocated["accepted"]} == {"0x00002000", "0x00002020"},
        }
    )

    normalized_left = synthetic_analysis(
        "left",
        [
            (0x1000, [0x38600001, 0x38800002, 0x38A00003, 0x38C00004, blr]),
            (
                0x1020,
                [0x48000101, 0x38600001, 0x38800002, 0x38A00003, 0x38C00004, 0x38E00005, 0x39000006, 0x39200007, blr],
            ),
        ],
    )
    normalized_right = synthetic_analysis(
        "right",
        [
            (0x2000, [0x38600001, 0x38800002, 0x38A00003, 0x38C00004, blr]),
            (
                0x2020,
                [0x48000301, 0x38600001, 0x38800002, 0x38A00003, 0x38C00004, 0x38E00005, 0x39000006, 0x39200007, blr],
            ),
        ],
    )
    normalized_result = match_builds(normalized_left, normalized_right)
    normalized_row = next(
        row for row in normalized_result["index"] if row["donor_start"] == "0x00001020"
    )
    fixtures.append(
        {
            "name": "branch-normalized-with-exact-neighbour-delta",
            "passed": normalized_row["status"] == "accepted-normalized-corroborated",
        }
    )

    duplicates_left = synthetic_analysis(
        "left", [(0x1000, [blr]), (0x1010, [blr]), (0x1020, [0x7C0802A6, blr])]
    )
    duplicates_right = synthetic_analysis(
        "right", [(0x2000, [blr]), (0x2010, [blr]), (0x2020, [0x7C0802A6, blr])]
    )
    duplicates = match_builds(duplicates_left, duplicates_right)
    duplicate_statuses = {row["status"] for row in duplicates["index"][:2]}
    fixtures.append(
        {
            "name": "duplicate-tiny-leaves-and-thunks",
            "passed": not duplicates["accepted"] and duplicate_statuses <= {"ambiguous", "quarantined"},
        }
    )

    split_left = synthetic_analysis("left", [(0x1000, [0x38600001, nop, blr])])
    split_right = synthetic_analysis("right", [(0x1000, [0x38600001, nop]), (0x1008, [blr])])
    split = match_builds(split_left, split_right)
    fixtures.append(
        {
            "name": "split-merged-shifted-pdata-boundary",
            "passed": split["index"][0]["status"] == "boundary-change",
        }
    )

    opcode_left = synthetic_analysis(
        "left",
        [(0x1000, [0x38600001, 0x38800002, 0x38A00003, 0x38C00004, 0x38E00005, blr])],
    )
    opcode_right = synthetic_analysis(
        "right",
        [(0x2000, [0x38600009, 0x3880000A, 0x38A0000B, 0x38C0000C, 0x38E0000D, blr])],
    )
    opcode = match_builds(opcode_left, opcode_right)
    fixtures.append(
        {
            "name": "opcode-similar-semantically-different",
            "passed": not opcode["accepted"]
            and opcode["index"][0]["status"] == "candidate-structural",
        }
    )

    reordered_left = synthetic_analysis(
        "left",
        [(0x1000, [0x38600001, blr]), (0x1010, [0x48000011, blr]), (0x1020, [0x38600002, 0x38800003, blr])],
    )
    reordered_right = synthetic_analysis(
        "right",
        [(0x2000, [0x38600002, 0x38800003, blr]), (0x2010, [0x48000021, blr]), (0x2020, [0x38600001, blr])],
    )
    reordered = match_builds(reordered_left, reordered_right)
    fixtures.append(
        {
            "name": "reordered-neighbouring-functions",
            "passed": all(
                record["status"] != "accepted-normalized-corroborated"
                for record in reordered["index"]
            ),
        }
    )

    one_many_left = synthetic_analysis("left", [(0x1000, [0x38600001, blr])])
    one_many_right = synthetic_analysis(
        "right", [(0x2000, [0x38600001, blr]), (0x2010, [0x38600001, blr])]
    )
    one_many = match_builds(one_many_left, one_many_right)
    many_one = match_builds(one_many_right, one_many_left)
    fixtures.append(
        {
            "name": "one-to-many-and-many-to-one-ambiguity",
            "passed": not one_many["accepted"] and not many_one["accepted"],
        }
    )

    caller_left = synthetic_analysis(
        "left",
        [
            (0x1000, [0x48000101, 0x38600003, 0x38800004, 0x38A00005, 0x38C00006, 0x38E00007, 0x39000008, 0x39200009, blr]),
            (0x1100, [0x38600001, 0x38800002, 0x38A00003, 0x38C00004, blr]),
            (0x1120, [0x38600002, 0x38800003, 0x38A00004, 0x38C00005, 0x38E00006, blr]),
        ],
    )
    caller_right = synthetic_analysis(
        "right",
        [
            (0x2000, [0x48000121, 0x38600003, 0x38800004, 0x38A00005, 0x38C00006, 0x38E00007, 0x39000008, 0x39200009, blr]),
            (0x2100, [0x38600001, 0x38800002, 0x38A00003, 0x38C00004, blr]),
            (0x2120, [0x38600002, 0x38800003, 0x38A00004, 0x38C00005, 0x38E00006, blr]),
        ],
    )
    calls = match_builds(caller_left, caller_right)
    caller_row = next(row for row in calls["index"] if row["donor_start"] == "0x00001000")
    fixtures.append(
        {
            "name": "changed-direct-call-target",
            "passed": caller_row["status"] != "accepted-normalized-corroborated",
        }
    )

    address_left = synthetic_analysis(
        "left", [(0x1000, [0x3C608200, 0x38631000, 0x38800001, 0x38A00002, 0x38C00003, blr])]
    )
    address_right = synthetic_analysis(
        "right", [(0x2000, [0x3C608300, 0x38632000, 0x38800001, 0x38A00002, 0x38C00003, blr])]
    )
    address_result = match_builds(address_left, address_right)
    fixtures.append(
        {
            "name": "materialized-string-data-addresses-move",
            "passed": not address_result["accepted"]
            and address_result["index"][0]["status"] == "candidate-structural",
        }
    )

    if not all(fixture["passed"] for fixture in fixtures):
        failed = [fixture["name"] for fixture in fixtures if not fixture["passed"]]
        raise CorrespondenceError(f"synthetic fixtures failed: {', '.join(failed)}")
    return fixtures


def input_binding(
    phase1_evidence: Path,
    derived_root: Path,
    prototype_root: Path,
    closure_path: Path,
    base_xex: Path,
    title_update: Path,
    tool_commit: str,
    rexglue_commit: str,
) -> tuple[dict[str, Any], dict[str, BuildAnalysis]]:
    phase1_consistency.validate(
        phase1_evidence,
        derived_root,
        phase1_evidence.parent / "report.md",
    )
    xex_path = phase1_evidence / "prototype-xex-metadata.json"
    xex = read_json(xex_path)
    records = {
        record["artifact_id"]: record
        for record in xex.get("records", [])
        if isinstance(record, dict) and "artifact_id" in record
    }
    source_expectations = {
        "sep-2008": "sep_container",
        "jul-2009": "jul_container",
        "build-23.12.02.0330": "donor_container",
    }
    sources = {}
    for build_id, expected_key in source_expectations.items():
        record = records.get(build_id)
        if not isinstance(record, dict):
            raise CorrespondenceError(f"missing Phase 1 XEX record {build_id}")
        source = prototype_root / str(record.get("relative_path"))
        actual_hash = sha256_file(source)
        require_hash(actual_hash, expected_key, build_id)
        if actual_hash != str(record.get("sha256", "")).upper():
            raise CorrespondenceError(f"{build_id} source differs from Phase 1 XEX evidence")
        sources[build_id] = {
            "source_root_id": "fable2-prototype-corpus",
            "relative_path": record["relative_path"],
            "size": source.stat().st_size,
            "sha256": actual_hash,
        }
    require_hash(sha256_file(base_xex), "target_base", "canonical base XEX")
    require_hash(sha256_file(title_update), "target_xexp", "canonical retail TU1 XEXP")
    closure_hash = sha256_file(closure_path)
    require_hash(closure_hash, "closure", "entrypoint closure")
    closure = read_json(closure_path)
    identity = closure.get("image_identity")
    if not isinstance(identity, dict):
        raise CorrespondenceError("entrypoint closure has no image_identity")
    expected_identity = {
        "base_xex_sha256": EXPECTED["target_base"],
        "title_update_sha256": EXPECTED["target_xexp"],
        "patched_image_sha256": EXPECTED["target_postpatch"],
        "executable_memory_fingerprint": EXPECTED["target_executable"],
        "image_base": "0x82000000",
        "image_size": "0x01620000",
        "entry_point": "0x82CC21C0",
        "title_id": "0x4D5307F1",
        "media_id": "0x716F0A0D",
        "version": "0.0.1.26",
    }
    for key, expected in expected_identity.items():
        if identity.get(key) != expected:
            raise CorrespondenceError(
                f"canonical closure identity mismatch for {key}: {identity.get(key)} != {expected}"
            )
    if closure.get("schema_version") != 3 or closure.get("analyzer_version") != "2.0.0":
        raise CorrespondenceError("unsupported canonical closure schema/analyzer version")

    analyses = {
        build_id: analyze_build(derived_root, build_id)
        for build_id in ("sep-2008", "jul-2009", "build-23.12.02.0330", "canonical-tu1")
    }
    by_name = {
        build_id: {block.name: block for block in analysis.blocks}
        for build_id, analysis in analyses.items()
    }
    require_hash(by_name["build-23.12.02.0330"][".text"].sha256, "donor_text", "donor .text")
    require_hash(by_name["build-23.12.02.0330"][".pdata"].sha256, "donor_pdata", "donor .pdata")
    require_hash(by_name["canonical-tu1"][".text"].sha256, "target_text", "canonical TU1 .text")
    require_hash(by_name["canonical-tu1"][".pdata"].sha256, "target_pdata", "canonical TU1 .pdata")
    if analyses["canonical-tu1"].executable_fingerprint != EXPECTED["target_executable"]:
        raise CorrespondenceError(
            "canonical derived executable-memory fingerprint does not match the closure"
        )
    july = analyses["jul-2009"]
    donor = analyses["build-23.12.02.0330"]
    if len(july.blocks) != len(donor.blocks) or any(
        (left.name, left.start, left.data, left.read, left.write, left.execute)
        != (right.name, right.start, right.data, right.read, right.write, right.execute)
        for left, right in zip(july.blocks, donor.blocks, strict=True)
    ):
        raise CorrespondenceError("July/build-23 initialized images are no longer identical")
    if [(fn.start, fn.size, fn.code) for fn in july.functions] != [
        (fn.start, fn.size, fn.code) for fn in donor.functions
    ]:
        raise CorrespondenceError("July/build-23 .pdata function or byte domains differ")
    if len(donor.functions) != 46179 or len(analyses["canonical-tu1"].functions) != 46180:
        raise CorrespondenceError("unexpected donor or canonical .pdata function count")
    if not re.fullmatch(r"[0-9a-f]{40}", tool_commit):
        raise CorrespondenceError("--tool-commit must be a full lowercase 40-hex Git commit")
    if not re.fullmatch(r"[0-9a-f]{40}", rexglue_commit):
        raise CorrespondenceError("--rexglue-commit must be a full lowercase 40-hex Git commit")

    donor_manifest = donor.manifest
    target_manifest = analyses["canonical-tu1"].manifest
    binding = {
        "donor": {
            "preferred_id": "build-23.12.02.0330",
            "container": sources["build-23.12.02.0330"],
            "exact_image_alias": sources["jul-2009"],
            "derived_manifest_sha256": donor.manifest_sha256,
            "text": {
                "start": "0x82170000",
                "size": len(by_name["build-23.12.02.0330"][".text"].data),
                "sha256": by_name["build-23.12.02.0330"][".text"].sha256,
            },
            "pdata": {
                "start": address_text(by_name["build-23.12.02.0330"][".pdata"].start),
                "size": len(by_name["build-23.12.02.0330"][".pdata"].data),
                "sha256": by_name["build-23.12.02.0330"][".pdata"].sha256,
                "function_count": len(donor.functions),
            },
            "executable_memory_fingerprint_algorithm": "fable2-executable-memory-sha256-v1",
            "executable_memory_fingerprint": donor.executable_fingerprint,
        },
        "target": {
            "id": "canonical-fable2-goty-tu1-postpatch",
            "base_xex_sha256": EXPECTED["target_base"],
            "retail_xexp_sha256": EXPECTED["target_xexp"],
            "postpatch_image_sha256": EXPECTED["target_postpatch"],
            "executable_memory_fingerprint_algorithm": "fable2-executable-memory-sha256-v1",
            "executable_memory_fingerprint": EXPECTED["target_executable"],
            "derived_manifest_sha256": analyses["canonical-tu1"].manifest_sha256,
            "text": {
                "start": "0x82170000",
                "size": len(by_name["canonical-tu1"][".text"].data),
                "sha256": by_name["canonical-tu1"][".text"].sha256,
            },
            "pdata": {
                "start": address_text(by_name["canonical-tu1"][".pdata"].start),
                "size": len(by_name["canonical-tu1"][".pdata"].data),
                "sha256": by_name["canonical-tu1"][".pdata"].sha256,
                "function_count": len(analyses["canonical-tu1"].functions),
            },
            "image_base": identity["image_base"],
            "image_size": identity["image_size"],
            "entry_point": identity["entry_point"],
            "version": identity["version"],
        },
        "secondary": {
            "id": "sep-2008",
            "container": sources["sep-2008"],
            "derived_manifest_sha256": analyses["sep-2008"].manifest_sha256,
            "text_sha256": by_name["sep-2008"][".text"].sha256,
            "pdata_sha256": by_name["sep-2008"][".pdata"].sha256,
            "function_count": len(analyses["sep-2008"].functions),
        },
        "closure": {
            "repository_relative_path": closure_path.as_posix(),
            "sha256": closure_hash,
            "schema_version": closure["schema_version"],
            "analyzer_version": closure["analyzer_version"],
        },
        "phase1_evidence": {
            "xex_metadata_sha256": sha256_file(xex_path),
            "tu1_relationship_sha256": sha256_file(
                phase1_evidence / "prototype-tu1-relationship.json"
            ),
            "crossbuild_feasibility_sha256": sha256_file(
                phase1_evidence / "prototype-crossbuild-feasibility.json"
            ),
        },
        "toolchain": {
            "generator": {"name": TOOL_NAME, "version": TOOL_VERSION, "commit": tool_commit},
            "python_runtime": python_runtime_identity(),
            "fable2_repository_commit": tool_commit,
            "rexglue_repository_commit": rexglue_commit,
            "ghidra_exporter": donor_manifest.get("exporter"),
            "ghidra_toolchain": donor_manifest.get("toolchain"),
            "target_ghidra_exporter": target_manifest.get("exporter"),
            "target_ghidra_toolchain": target_manifest.get("toolchain"),
        },
    }
    binding["input_bundle_sha256"] = sha256_bytes(canonical_json_bytes(binding))
    return binding, analyses


def envelope(name: str, generated_at: str, binding: dict[str, Any], **values: Any) -> dict[str, Any]:
    return {
        "schema": {"name": name, "version": SCHEMA_VERSION},
        "generator": {"name": TOOL_NAME, "version": TOOL_VERSION},
        "generated_at_utc": generated_at,
        "input_binding": binding,
        **values,
    }


def secondary_study(result: dict[str, Any], left_count: int, right_count: int) -> dict[str, Any]:
    return {
        "left_build": "sep-2008",
        "right_build": "build-23.12.02.0330",
        "left_function_count": left_count,
        "right_function_count": right_count,
        "policy_status_counts": result["status_counts"],
        "reciprocal_fingerprint_statistics": result["fingerprint_groups"],
        "accepted_by_precision_policy": len(result["accepted"]),
        "accuracy_reported": False,
        "reason_accuracy_not_reported": "No complete ground-truth correspondence exists for the independent September image.",
        "failure_classes": [
            "duplicate fingerprints",
            "risk/quarantine rules",
            "changed or split .pdata boundaries",
            "structural candidates without corroboration",
            "no shared fingerprint candidate",
        ],
    }


def validate_documents(documents: dict[str, dict[str, Any]], binding_hash: str) -> None:
    for filename, document in documents.items():
        schema = document.get("schema")
        if not isinstance(schema, dict) or schema.get("version") != SCHEMA_VERSION:
            raise CorrespondenceError(f"invalid schema envelope in {filename}")
        binding = document.get("input_binding")
        if not isinstance(binding, dict) or binding.get("input_bundle_sha256") != binding_hash:
            raise CorrespondenceError(f"input binding mismatch in {filename}")
    index = documents["prototype-correspondence-index.json"]["functions"]
    accepted = documents["prototype-correspondence-accepted.json"]["records"]
    if len(index) != 46179:
        raise CorrespondenceError(f"correspondence index has {len(index)} functions, expected 46179")
    starts = [row["donor_start"] for row in index]
    if starts != sorted(starts) or len(starts) != len(set(starts)):
        raise CorrespondenceError("correspondence index starts are duplicated or unsorted")
    statuses = collections.Counter(row["status"] for row in index)
    if set(statuses) - set(TERMINAL_STATUSES):
        raise CorrespondenceError("correspondence index has an unknown terminal status")
    if sum(statuses.values()) != 46179:
        raise CorrespondenceError("terminal status counts do not cover every donor function")
    accepted_index = {
        row["donor_start"]: row["accepted_target"]
        for row in index
        if row["status"] in ACCEPTED_STATUSES
    }
    accepted_records = {row["donor_start"]: row["target_start"] for row in accepted}
    if accepted_index != accepted_records:
        raise CorrespondenceError("accepted index and accepted evidence records disagree")
    if len(accepted_records.values()) != len(set(accepted_records.values())):
        raise CorrespondenceError("accepted target addresses are not injective")
    for row in accepted:
        evidence = row["evidence"]
        raw_equal = evidence["fingerprints"]["raw"]["equal"]
        normalized_equal = evidence["fingerprints"]["branch_normalized"]["equal"]
        if row["status"] == "accepted-normalized-corroborated":
            if raw_equal or not has_required_corroboration(evidence):
                raise CorrespondenceError("normalized acceptance lacks required corroboration")
        if not raw_equal and not normalized_equal:
            raise CorrespondenceError("opcode/XO-only candidate was accepted")
        if evidence["contradictions"]:
            raise CorrespondenceError("accepted record retains contradictory evidence")


def generate(args: argparse.Namespace) -> int:
    binding, analyses = input_binding(
        args.phase1_evidence.resolve(),
        args.derived_root.resolve(),
        args.prototype_root.resolve(),
        args.closure.resolve(),
        args.base_xex.resolve(),
        args.title_update.resolve(),
        args.tool_commit,
        args.rexglue_commit,
    )
    fixtures = run_synthetic_fixtures()
    positive_result = match_builds(
        analyses["build-23.12.02.0330"],
        analyses["jul-2009"],
        include_exhaustive=False,
    )
    calibration = positive_control(positive_result, 46179)
    del positive_result
    primary = match_builds(
        analyses["build-23.12.02.0330"], analyses["canonical-tu1"]
    )
    secondary = match_builds(
        analyses["sep-2008"],
        analyses["build-23.12.02.0330"],
        include_index=False,
        include_exhaustive=False,
    )

    exhaustive = envelope(
        "fable2-prototype-correspondence-candidate-groups",
        args.generated_at,
        binding,
        representation={
            "lossless": True,
            "meaning": "Each donor-target candidate edge is the Cartesian product of donor_members and target_members within a fingerprint group.",
            "feature_edge_counts_overlap": True,
        },
        groups=primary["exhaustive_groups"],
    )
    exhaustive_path = args.scratch_output.resolve() / "prototype-correspondence-candidate-groups.json"
    write_json(exhaustive_path, exhaustive, compact=True)
    exhaustive_hash = sha256_file(exhaustive_path)
    feature_output = envelope(
        "fable2-prototype-correspondence-function-features",
        args.generated_at,
        binding,
        representation={
            "lossless": True,
            "function_unit": "exact .pdata start and encoded length",
            "builds": ["build-23.12.02.0330", "canonical-tu1"],
        },
        builds={
            "build-23.12.02.0330": exhaustive_function_features(
                analyses["build-23.12.02.0330"]
            ),
            "canonical-tu1": exhaustive_function_features(analyses["canonical-tu1"]),
        },
    )
    feature_path = args.scratch_output.resolve() / "prototype-correspondence-function-features.json"
    write_json(feature_path, feature_output, compact=True)
    feature_hash = sha256_file(feature_path)

    review = build_review_queue(primary["index"])
    aggregate = aggregate_index(primary["index"])
    status_counts = primary["status_counts"]
    accepted_counts = collections.Counter(record["status"] for record in primary["accepted"])
    documents = {
        "prototype-correspondence-index.json": envelope(
            "fable2-prototype-correspondence-index",
            args.generated_at,
            binding,
            terminal_status_vocabulary=list(TERMINAL_STATUSES),
            top_candidate_limit=TOP_CANDIDATE_LIMIT,
            functions=compact_index(primary["index"]),
        ),
        "prototype-correspondence-accepted.json": envelope(
            "fable2-prototype-correspondence-accepted",
            args.generated_at,
            binding,
            semantics_propagated=False,
            records=primary["accepted"],
        ),
        "prototype-correspondence-review.json": envelope(
            "fable2-prototype-correspondence-review",
            args.generated_at,
            binding,
            selection_policy="up to five deterministic, non-overlapping records per documented review stratum",
            records=review,
        ),
        "prototype-correspondence-validation.json": envelope(
            "fable2-prototype-correspondence-validation",
            args.generated_at,
            binding,
            positive_control=calibration,
            synthetic_fixtures=fixtures,
            september_robustness_study=secondary_study(
                secondary,
                len(analyses["sep-2008"].functions),
                len(analyses["build-23.12.02.0330"].functions),
            ),
        ),
        "prototype-correspondence-summary.json": envelope(
            "fable2-prototype-correspondence-summary",
            args.generated_at,
            binding,
            policy={
                "version": POLICY_VERSION,
                "precision_first": True,
                "exact_acceptance": "reciprocal unique raw bytes, exact valid boundaries, injective, shape/CFG consistent, and no final neighbourhood/topology contradiction",
                "normalized_acceptance": "reciprocal unique branch-normalized bytes plus at least two corroborating classes including exact address-delta neighbourhood, direct-call topology, or a sound string/data anchor; injective and contradiction-free",
                "risk_policy": "tiny leaves, short thunks, padding-dominated functions, overlaps, and duplicate fingerprints require corroboration or quarantine",
                "never_automatic": [
                    "opcode/XO structure only",
                    "same guest address",
                    "function size",
                    "prototype script/debug/PDB/source-path name",
                    "split/merge or changed-boundary hypothesis",
                ],
            },
            review_score={
                "version": SCORE_VERSION,
                "formula": {
                    "raw_equal": 100,
                    "branch_normalized_equal": 60,
                    "opcode_structure_equal": 10,
                    "shape_equal": 10,
                    "cfg_equal": 15,
                    "neighbour_delta_support_each_max_2": 12,
                    "topology_support_each_max_2": 15,
                    "shared_string": 25,
                    "shared_data_anchor_each_max_3": 5,
                    "contradiction_each": -50,
                    "risk_present": -25,
                },
                "acceptance_uses_score": False,
            },
            status_counts=status_counts,
            accepted_counts={status: accepted_counts.get(status, 0) for status in TERMINAL_STATUSES[:2]},
            fingerprint_candidate_statistics=primary["fingerprint_groups"],
            aggregate=aggregate,
            exhaustive_candidate_groups={
                "ignored_repository_relative_path": exhaustive_path.relative_to(Path.cwd()).as_posix()
                if exhaustive_path.is_relative_to(Path.cwd())
                else exhaustive_path.as_posix(),
                "sha256": exhaustive_hash,
                "size": exhaustive_path.stat().st_size,
                "lossless": True,
                "committed_index_top_candidate_limit": TOP_CANDIDATE_LIMIT,
            },
            exhaustive_function_features={
                "ignored_repository_relative_path": feature_path.relative_to(Path.cwd()).as_posix()
                if feature_path.is_relative_to(Path.cwd())
                else feature_path.as_posix(),
                "sha256": feature_hash,
                "size": feature_path.stat().st_size,
                "lossless": True,
                "builds": ["build-23.12.02.0330", "canonical-tu1"],
            },
            conclusions={
                "crossbuild_feasibility": "viable with a precision-first accepted core and an explicit ambiguity/quarantine tail",
                "semantic_names_assigned": False,
                "same_address_used_as_acceptance_evidence": False,
            },
        ),
    }
    validate_documents(documents, binding["input_bundle_sha256"])
    output = args.output.resolve()
    if args.check_determinism and output.is_dir():
        existing = {
            path.name: sha256_file(path)
            for path in output.glob("prototype-correspondence-*.json")
        }
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            for filename, document in documents.items():
                write_json(
                    temporary_root / filename,
                    document,
                    compact=filename.endswith(("-index.json", "-accepted.json")),
                )
            regenerated = {path.name: sha256_file(path) for path in temporary_root.glob("*.json")}
        if existing != regenerated:
            changed = sorted(set(existing) | set(regenerated))
            differences = [name for name in changed if existing.get(name) != regenerated.get(name)]
            raise CorrespondenceError(
                f"determinism check failed for: {', '.join(differences)}"
            )
    for filename, document in documents.items():
        write_json(
            output / filename,
            document,
            compact=filename.endswith(("-index.json", "-accepted.json")),
        )
    print(
        f"Generated Phase 2A: {len(primary['index'])} donor functions, "
        f"{len(primary['accepted'])} accepted, {len(review)} review records"
    )
    return 0


def verify(args: argparse.Namespace) -> int:
    binding, analyses = input_binding(
        args.phase1_evidence.resolve(),
        args.derived_root.resolve(),
        args.prototype_root.resolve(),
        args.closure.resolve(),
        args.base_xex.resolve(),
        args.title_update.resolve(),
        args.tool_commit,
        args.rexglue_commit,
    )
    output = args.output.resolve()
    filenames = (
        "prototype-correspondence-index.json",
        "prototype-correspondence-accepted.json",
        "prototype-correspondence-review.json",
        "prototype-correspondence-validation.json",
        "prototype-correspondence-summary.json",
    )
    documents = {filename: read_json(output / filename) for filename in filenames}
    validate_documents(documents, binding["input_bundle_sha256"])
    summary = documents["prototype-correspondence-summary.json"]
    exhaustive_info = summary["exhaustive_candidate_groups"]
    exhaustive_path = Path(exhaustive_info["ignored_repository_relative_path"])
    if sha256_file(exhaustive_path) != exhaustive_info["sha256"]:
        raise CorrespondenceError("ignored exhaustive candidate-group artifact hash mismatch")
    feature_info = summary["exhaustive_function_features"]
    feature_path = Path(feature_info["ignored_repository_relative_path"])
    if sha256_file(feature_path) != feature_info["sha256"]:
        raise CorrespondenceError("ignored exhaustive function-feature artifact hash mismatch")
    validation = documents["prototype-correspondence-validation.json"]
    if validation["positive_control"]["false_accepted_cross_address_pairs"] != 0:
        raise CorrespondenceError("positive control no longer has zero false accepted pairs")
    if not all(item["passed"] for item in validation["synthetic_fixtures"]):
        raise CorrespondenceError("a recorded synthetic fixture failed")
    target_starts = {function.start for function in analyses["canonical-tu1"].functions}
    donor_starts = {function.start for function in analyses["build-23.12.02.0330"].functions}
    for row in documents["prototype-correspondence-accepted.json"]["records"]:
        if int(row["donor_start"], 16) not in donor_starts or int(row["target_start"], 16) not in target_starts:
            raise CorrespondenceError("accepted mapping address is not an exact .pdata start")
    print(
        f"Verified Phase 2A correspondence: {len(donor_starts)} donor functions, "
        f"{len(documents['prototype-correspondence-accepted.json']['records'])} accepted mappings"
    )
    return 0


def add_common_arguments(command: argparse.ArgumentParser) -> None:
    command.add_argument(
        "--phase1-evidence",
        type=Path,
        default=Path("docs/fable2-prototype-archaeology/phase1/evidence"),
    )
    command.add_argument(
        "--derived-root", type=Path, default=Path("out/prototype-archaeology/derived")
    )
    command.add_argument(
        "--prototype-root", type=Path, default=Path(r"D:\Fable2-Recomp\prototypes")
    )
    command.add_argument(
        "--closure",
        type=Path,
        default=Path(
            "out/analysis/BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00/entrypoint-closure.json"
        ),
    )
    command.add_argument("--base-xex", type=Path, default=Path("assets/tu1/default.xex"))
    command.add_argument("--title-update", type=Path, default=Path("assets/tu1/default.xexp"))
    command.add_argument(
        "--output",
        type=Path,
        default=Path("docs/fable2-prototype-archaeology/phase2a/evidence"),
    )
    command.add_argument("--tool-commit", required=True)
    command.add_argument(
        "--rexglue-commit", default="fa10315ff88ca56b2d0b380de40bad5b59b542bd"
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    generate_command = commands.add_parser("generate", help="generate Phase 2A evidence")
    add_common_arguments(generate_command)
    generate_command.add_argument(
        "--scratch-output",
        type=Path,
        default=Path("out/prototype-archaeology/phase2a"),
    )
    generate_command.add_argument("--generated-at", default="2026-09-11T00:00:00Z")
    generate_command.add_argument("--check-determinism", action="store_true")
    generate_command.set_defaults(action=generate)
    verify_command = commands.add_parser("verify", help="verify committed Phase 2A evidence")
    add_common_arguments(verify_command)
    verify_command.set_defaults(action=verify)
    synthetic_command = commands.add_parser("synthetic", help="run deterministic synthetic fixtures")
    synthetic_command.set_defaults(
        action=lambda _args: (print(f"Passed {len(run_synthetic_fixtures())} synthetic fixtures") or 0)
    )
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.action(args)
    except (CorrespondenceError, phase1_consistency.ConsistencyError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
