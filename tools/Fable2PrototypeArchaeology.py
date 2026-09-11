#!/usr/bin/env python3
"""Deterministic Phase 1 evidence generator for the Fable II prototype corpus.

The prototype root is read-only. Derived XEX images and STFS extraction results
are consumed from repository-owned output directories created by the documented
Ghidra and ReXGlue helpers.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import os
import re
import struct
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator


TOOL_NAME = "Fable2PrototypeArchaeology.py"
TOOL_VERSION = "1.0.0"
SCHEMA_VERSION = 1
HASH_CHUNK_SIZE = 4 * 1024 * 1024
ASCII_RE = re.compile(rb"[\x20-\x7e]{4,}")
UTF16LE_RE = re.compile(rb"(?:[\x20-\x7e]\x00){4,}")
API_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*(?:[.:][A-Za-z_][A-Za-z0-9_]*)+\b")
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{3,}$")
SOURCE_EXTENSION_RE = re.compile(r"\.(?:cpp|cxx|cc|c|hpp|hxx|hh|h|inl)(?:\b|$)", re.I)


@dataclass(frozen=True)
class BuildSpec:
    build_id: str
    directory_name: str
    label: str


BUILD_SPECS = (
    BuildSpec("sep-2008", "Fable II (Sep 13, 2008 prototype)", "September 13, 2008 prototype"),
    BuildSpec("jul-2009", "Fable II (Jul 10, 2009 prototype)", "July 10, 2009 prototype"),
    BuildSpec(
        "build-23.12.02.0330",
        "Fable II July 10 2009 23.12.02.0330",
        "Build 23.12.02.0330",
    ),
    BuildSpec("patch-data", "Fable II (Patch Data prototype)", "Patch Data prototype"),
)
FULL_XEX_BUILD_IDS = ("sep-2008", "jul-2009", "build-23.12.02.0330")
DERIVED_BUILD_IDS = FULL_XEX_BUILD_IDS + ("canonical-tu1",)

IDENTITY_FILENAMES = {
    "build_version.txt",
    "serverinfo.txt",
    "!submissioninfo.txt",
    "dir.manifest",
    "tu1_data.manifest",
    "4d5307f1.ini",
}
SCRIPT_NAMES = {
    "debugmenu.txt",
    "debugmenulevellist.txt",
    "mydebugmenu_gdc2008.txt",
    "mydebugmenu_template.txt",
    "startupconsolescript.lua",
    "featurecompletestartupconsolescript.lua",
    "gdcstartupconsolescript.lua",
    "e3startupconsolescript.lua",
    "mystartup.lua",
    "mystartup_e32008.lua",
    "gdc2008startup.lua",
    "gdcstartup.lua",
    "e3startup.lua",
    "luaplus_ai_test.lua",
}
RESOURCE_EXTENSIONS = {
    ".gdb",
    ".list",
    ".adb",
    ".bnk",
    ".sbk",
    ".animation_toc",
    ".animation_data",
}

XEX_OPTIONAL_NAMES = {
    0x000002FF: "resource_info",
    0x000003FF: "file_format_info",
    0x00000405: "base_reference",
    0x000005FF: "delta_patch_descriptor",
    0x000080FF: "bounding_path",
    0x00008105: "device_id",
    0x00010001: "original_base_address",
    0x00010100: "entry_point",
    0x00010201: "image_base_address",
    0x000103FF: "import_libraries",
    0x00018002: "checksum_timestamp",
    0x00018102: "enabled_for_callcap",
    0x00018200: "enabled_for_fastcap",
    0x000183FF: "original_pe_name",
    0x000200FF: "static_libraries",
    0x00020104: "tls_info",
    0x00020200: "default_stack_size",
    0x00020301: "default_filesystem_cache_size",
    0x00020401: "default_heap_size",
    0x00028002: "page_heap_size_and_flags",
    0x00030000: "system_flags",
    0x00040006: "execution_info",
    0x00040201: "title_workspace_size",
    0x00040310: "game_ratings",
    0x00040404: "lan_key",
    0x000405FF: "xbox360_logo",
    0x000406FF: "multidisc_media_ids",
    0x000407FF: "alternate_title_ids",
    0x00040801: "additional_title_memory",
    0x00E10402: "exports_by_name",
}
MODULE_FLAGS = {
    0x00000001: "title",
    0x00000002: "exports_to_title",
    0x00000004: "system_debugger",
    0x00000008: "dll_module",
    0x00000010: "module_patch",
    0x00000020: "patch_full",
    0x00000040: "patch_delta",
    0x00000080: "user_mode",
}
IMAGE_FLAGS = {
    0x00000008: "xgd2_media_only",
    0x00000100: "cardea_key",
    0x00000200: "xeika_key",
    0x00000400: "usermode_title",
    0x00000800: "usermode_system",
    0x10000000: "page_size_4kb",
    0x20000000: "region_free",
    0x40000000: "revocation_check_optional",
    0x80000000: "revocation_check_required",
}
COMPRESSION_NAMES = {0: "none", 1: "basic", 2: "normal", 3: "delta"}
ENCRYPTION_NAMES = {0: "none", 1: "normal"}


def sha_file(path: Path, algorithm: str = "sha256") -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(HASH_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def iso_timestamp_ns(value: int) -> str:
    seconds, nanoseconds = divmod(value, 1_000_000_000)
    stamp = dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc) + dt.timedelta(seconds=seconds)
    return stamp.strftime("%Y-%m-%dT%H:%M:%S") + f".{nanoseconds:09d}Z"


def hex32(value: int) -> str:
    return f"0x{value:08X}"


def version_record(value: int) -> dict[str, Any]:
    major = (value >> 28) & 0xF
    minor = (value >> 24) & 0xF
    build = (value >> 8) & 0xFFFF
    qfe = value & 0xFF
    return {
        "raw": hex32(value),
        "major": major,
        "minor": minor,
        "build": build,
        "qfe": qfe,
        "display": f"{major}.{minor}.{build}.{qfe}",
    }


def flags_record(value: int, names: dict[int, str]) -> dict[str, Any]:
    return {
        "raw": hex32(value),
        "set": [name for bit, name in names.items() if value & bit],
    }


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", dir=path.parent, delete=False
    ) as stream:
        stream.write(data)
        temporary = Path(stream.name)
    os.replace(temporary, path)


def artifact(name: str, generated_at: str, **values: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema": {"name": name, "version": SCHEMA_VERSION},
        "generator": {"name": TOOL_NAME, "version": TOOL_VERSION},
        "generated_at_utc": generated_at,
    }
    result.update(values)
    return result


def detect_magic(head: bytes) -> dict[str, Any]:
    signatures = (
        (b"XEX2", "XEX2", "Xbox 360 executable"),
        (b"XEX1", "XEX1", "Xbox 360 executable"),
        (b"LIVE", "LIVE", "Xbox 360 LIVE/STFS package"),
        (b"PIRS", "PIRS", "Xbox 360 PIRS/STFS package"),
        (b"CON ", "CON", "Xbox 360 CON/STFS package"),
        (b"\x1bLua", "Lua bytecode", "Lua bytecode"),
        (b"RIFF", "RIFF", "RIFF container"),
        (b"BKHD", "BKHD", "Wwise bank"),
        (b"OggS", "OggS", "Ogg container"),
        (b"bik", "Bink", "Bink video"),
    )
    for signature, name, description in signatures:
        if head.startswith(signature):
            return {"name": name, "hex": head[: len(signature)].hex().upper(), "description": description}
    if head.startswith(b"PK\x03\x04"):
        return {"name": "ZIP", "hex": "504B0304", "description": "ZIP archive"}
    if head and all(value in b"\t\n\r" or 0x20 <= value <= 0x7E for value in head):
        return {"name": "text", "hex": head[:8].hex().upper(), "description": "printable text"}
    return {"name": "unknown", "hex": head[:8].hex().upper(), "description": "unrecognised"}


def classify_file(path: Path, magic: dict[str, Any]) -> str:
    lower_name = path.name.lower()
    suffix = path.suffix.lower()
    parts = {part.lower() for part in path.parts}
    magic_name = magic["name"]
    if magic_name in {"XEX1", "XEX2"}:
        return "executable"
    if magic_name in {"LIVE", "PIRS", "CON"}:
        return "patch executable/data"
    if lower_name.endswith(".xexp"):
        return "patch executable/data"
    if suffix in {".lua"} or magic_name == "Lua bytecode":
        return "script"
    if lower_name.startswith("debugmenu") or lower_name.startswith("mydebugmenu"):
        return "debug script"
    if suffix == ".log" or any(part.endswith("_logs") for part in parts):
        return "log"
    if suffix == ".manifest" or lower_name in {"4d5307f1.ini", "startup.vfsconfig"}:
        return "manifest"
    if suffix in {".gdb", ".adb"}:
        return "database"
    if suffix == ".sbk":
        return "shader bank"
    if suffix == ".bnk":
        return "resource bank"
    if suffix in {".wav", ".xma", ".ogg"}:
        return "audio"
    if suffix in {".bik", ".wmv"} or magic_name == "Bink":
        return "video"
    if suffix in {".xml", ".txt", ".csv", ".ini"}:
        return "filesystem metadata" if "manifest" in lower_name else "unknown"
    if suffix in {".big", ".bin", ".toc", ".animation_data", ".animation_toc"}:
        return "resource bank"
    return "unknown"


def inventory_corpus(prototype_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    build_summaries: dict[str, Any] = {}
    for spec in BUILD_SPECS:
        root = prototype_root / spec.directory_name
        if not root.is_dir():
            raise FileNotFoundError(f"prototype build directory not found: {root}")
        build_records: list[dict[str, Any]] = []
        for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda p: p.as_posix().lower()):
            relative = path.relative_to(root).as_posix()
            stat = path.stat()
            with path.open("rb") as stream:
                head = stream.read(64)
            magic = detect_magic(head)
            record = {
                "build_id": spec.build_id,
                "source_root_id": "fable2-prototype-corpus",
                "absolute_source_path": str(path.resolve()),
                "relative_path": relative,
                "filename": path.name,
                "extension": path.suffix.lower(),
                "size": stat.st_size,
                "sha256": sha_file(path, "sha256"),
                "sha1": sha_file(path, "sha1"),
                "timestamps": {
                    "created_utc": iso_timestamp_ns(stat.st_ctime_ns),
                    "modified_utc": iso_timestamp_ns(stat.st_mtime_ns),
                },
                "magic": magic,
                "classification": classify_file(path, magic),
            }
            records.append(record)
            build_records.append(record)
        counts = collections.Counter(record["classification"] for record in build_records)
        build_summaries[spec.build_id] = {
            "directory_name": spec.directory_name,
            "label": spec.label,
            "file_count": len(build_records),
            "total_size": sum(record["size"] for record in build_records),
            "classification_counts": dict(sorted(counts.items())),
        }
    records.sort(key=lambda record: (record["build_id"], record["relative_path"].lower(), record["relative_path"]))
    return records, build_summaries


def read_text_exact(path: Path, maximum: int = 2 * 1024 * 1024) -> tuple[str | None, str | None]:
    if path.stat().st_size > maximum:
        return None, None
    data = path.read_bytes()
    if b"\x00" in data:
        return None, None
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return None, None


def parse_xex(path: Path, artifact_id: str, relative_path: str) -> dict[str, Any]:
    data = path.read_bytes()
    if len(data) < 0x18 or data[:4] not in {b"XEX2", b"XEX1"}:
        raise ValueError(f"not an XEX file: {path}")
    if data[:4] != b"XEX2":
        raise ValueError(f"XEX1 parsing is not implemented: {path}")

    def u16(offset: int) -> int:
        if offset < 0 or offset + 2 > len(data):
            raise ValueError(f"out-of-range XEX u16 at 0x{offset:X}")
        return struct.unpack_from(">H", data, offset)[0]

    def u32(offset: int) -> int:
        if offset < 0 or offset + 4 > len(data):
            raise ValueError(f"out-of-range XEX u32 at 0x{offset:X}")
        return struct.unpack_from(">I", data, offset)[0]

    def bytes_at(offset: int, size: int) -> bytes:
        if offset < 0 or size < 0 or offset + size > len(data):
            raise ValueError(f"out-of-range XEX data at 0x{offset:X} size 0x{size:X}")
        return data[offset : offset + size]

    module_flags = u32(4)
    header_size = u32(8)
    security_offset = u32(0x10)
    header_count = u32(0x14)
    if 0x18 + header_count * 8 > len(data):
        raise ValueError("XEX optional header table exceeds the source file")

    headers: dict[int, tuple[int, int | None]] = {}
    header_records: list[dict[str, Any]] = []
    for index in range(header_count):
        key = u32(0x18 + index * 8)
        value = u32(0x1C + index * 8)
        low = key & 0xFF
        offset = None if low <= 1 else value
        headers[key] = (value, offset)
        record: dict[str, Any] = {
            "key": hex32(key),
            "name": XEX_OPTIONAL_NAMES.get(key, "unknown"),
            "raw_value": hex32(value),
            "storage": "immediate" if offset is None else "offset",
        }
        if offset is not None:
            record["offset"] = hex32(offset)
            if low == 0xFF and offset + 4 <= len(data):
                record["declared_size"] = u32(offset)
            elif low != 0:
                record["declared_size"] = low * 4
        header_records.append(record)

    def immediate(key: int) -> int | None:
        value = headers.get(key)
        return value[0] if value is not None else None

    def offset_of(key: int) -> int | None:
        value = headers.get(key)
        return value[1] if value is not None else None

    execution = None
    execution_offset = offset_of(0x00040006)
    if execution_offset is not None:
        execution = {
            "media_id": hex32(u32(execution_offset)),
            "version": version_record(u32(execution_offset + 4)),
            "base_version": version_record(u32(execution_offset + 8)),
            "title_id": hex32(u32(execution_offset + 12)),
            "platform": data[execution_offset + 16],
            "executable_table": data[execution_offset + 17],
            "disc_number": data[execution_offset + 18],
            "disc_count": data[execution_offset + 19],
            "savegame_id": hex32(u32(execution_offset + 20)),
        }

    file_format = None
    format_offset = offset_of(0x000003FF)
    if format_offset is not None:
        encryption = u16(format_offset + 4)
        compression = u16(format_offset + 6)
        file_format = {
            "info_size": u32(format_offset),
            "encryption": {"value": encryption, "name": ENCRYPTION_NAMES.get(encryption, "unknown")},
            "compression": {"value": compression, "name": COMPRESSION_NAMES.get(compression, "unknown")},
        }

    security = None
    if security_offset and security_offset + 0x184 <= len(data):
        page_count = u32(security_offset + 0x180)
        pages = []
        page_cursor = 0
        for index in range(page_count):
            descriptor_offset = security_offset + 0x184 + index * 0x18
            if descriptor_offset + 0x18 > len(data):
                break
            descriptor = u32(descriptor_offset)
            count = descriptor >> 4
            section_type = descriptor & 0xF
            pages.append(
                {
                    "index": index,
                    "page_start": page_cursor,
                    "page_count": count,
                    "section_type": section_type,
                    "digest_sha1": bytes_at(descriptor_offset + 4, 20).hex().upper(),
                }
            )
            page_cursor += count
        security = {
            "header_size": u32(security_offset),
            "image_size": u32(security_offset + 4),
            "image_flags": flags_record(u32(security_offset + 0x10C), IMAGE_FLAGS),
            "load_address": hex32(u32(security_offset + 0x110)),
            "section_digest_sha1": bytes_at(security_offset + 0x114, 20).hex().upper(),
            "import_table_count": u32(security_offset + 0x128),
            "import_table_digest_sha1": bytes_at(security_offset + 0x12C, 20).hex().upper(),
            "xgd2_media_id": bytes_at(security_offset + 0x140, 16).hex().upper(),
            "export_table": hex32(u32(security_offset + 0x160)),
            "header_digest_sha1": bytes_at(security_offset + 0x164, 20).hex().upper(),
            "region": hex32(u32(security_offset + 0x178)),
            "allowed_media_types": hex32(u32(security_offset + 0x17C)),
            "page_descriptor_count": page_count,
            "page_descriptors_parsed": len(pages),
            "page_descriptors": pages,
        }

    checksum_timestamp = None
    checksum_offset = offset_of(0x00018002)
    if checksum_offset is not None:
        timestamp = u32(checksum_offset + 4)
        checksum_timestamp = {
            "checksum": hex32(u32(checksum_offset)),
            "pe_timestamp": hex32(timestamp),
            "pe_timestamp_utc": dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
        }

    tls_info = None
    tls_offset = offset_of(0x00020104)
    if tls_offset is not None:
        tls_info = {
            "slot_count": u32(tls_offset),
            "raw_data_address": hex32(u32(tls_offset + 4)),
            "data_size": u32(tls_offset + 8),
            "raw_data_size": u32(tls_offset + 12),
        }

    original_pe_name = None
    pe_name_offset = offset_of(0x000183FF)
    if pe_name_offset is not None:
        size = u32(pe_name_offset)
        original_pe_name = bytes_at(pe_name_offset + 4, max(0, size - 4)).split(b"\0", 1)[0].decode(
            "ascii", "replace"
        )

    static_libraries = []
    libraries_offset = offset_of(0x000200FF)
    if libraries_offset is not None:
        size = u32(libraries_offset)
        for cursor in range(libraries_offset + 4, libraries_offset + size, 0x10):
            if cursor + 0x10 > len(data):
                break
            static_libraries.append(
                {
                    "name": bytes_at(cursor, 8).split(b"\0", 1)[0].decode("ascii", "replace"),
                    "version": f"{u16(cursor + 8)}.{u16(cursor + 10)}.{u16(cursor + 12)}.{data[cursor + 15]}",
                    "approval_type": data[cursor + 14],
                }
            )

    resources = []
    resources_offset = offset_of(0x000002FF)
    if resources_offset is not None:
        size = u32(resources_offset)
        for cursor in range(resources_offset + 4, resources_offset + size, 0x10):
            if cursor + 0x10 > len(data):
                break
            resources.append(
                {
                    "name": bytes_at(cursor, 8).split(b"\0", 1)[0].decode("ascii", "replace"),
                    "address": hex32(u32(cursor + 8)),
                    "size": u32(cursor + 12),
                }
            )

    imports = []
    imports_offset = offset_of(0x000103FF)
    if imports_offset is not None:
        total_size = u32(imports_offset)
        strings_size = u32(imports_offset + 4)
        strings_count = u32(imports_offset + 8)
        strings = []
        cursor = imports_offset + 12
        strings_end = cursor + strings_size
        while cursor < strings_end and len(strings) < strings_count:
            end = data.find(b"\0", cursor, min(strings_end, len(data)))
            if end < 0:
                break
            strings.append(data[cursor:end].decode("ascii", "replace"))
            cursor = (end + 4) & ~3
        library_cursor = imports_offset + 12 + strings_size
        while library_cursor + 0x28 <= min(imports_offset + total_size, len(data)):
            size = u32(library_cursor)
            if size < 0x28 or library_cursor + size > len(data):
                break
            name_index = u16(library_cursor + 0x24) & 0xFF
            count = u16(library_cursor + 0x26)
            addresses = [u32(library_cursor + 0x28 + index * 4) for index in range(count)]
            imports.append(
                {
                    "name": strings[name_index] if name_index < len(strings) else None,
                    "id": hex32(u32(library_cursor + 0x18)),
                    "version": version_record(u32(library_cursor + 0x1C)),
                    "minimum_version": version_record(u32(library_cursor + 0x20)),
                    "record_count": count,
                    "record_addresses": [hex32(value) for value in addresses],
                }
            )
            library_cursor += size

    delta = None
    delta_offset = offset_of(0x000005FF)
    if delta_offset is not None:
        delta = {
            "size": u32(delta_offset),
            "target_version": version_record(u32(delta_offset + 4)),
            "source_version": version_record(u32(delta_offset + 8)),
            "source_digest_sha1": bytes_at(delta_offset + 0x0C, 20).hex().upper(),
            "size_of_target_headers": u32(delta_offset + 0x30),
            "delta_headers_source_offset": hex32(u32(delta_offset + 0x34)),
            "delta_headers_source_size": u32(delta_offset + 0x38),
            "delta_headers_target_offset": hex32(u32(delta_offset + 0x3C)),
            "delta_image_source_offset": hex32(u32(delta_offset + 0x40)),
            "delta_image_source_size": u32(delta_offset + 0x44),
            "delta_image_target_offset": hex32(u32(delta_offset + 0x48)),
        }

    return {
        "artifact_id": artifact_id,
        "relative_path": relative_path,
        "size": len(data),
        "sha256": sha_bytes(data),
        "sha1": hashlib.sha1(data).hexdigest().upper(),
        "format": data[:4].decode("ascii"),
        "module_flags": flags_record(module_flags, MODULE_FLAGS),
        "header_size": header_size,
        "security_offset": hex32(security_offset),
        "optional_header_count": header_count,
        "optional_headers": header_records,
        "image_base": hex32(immediate(0x00010201)) if immediate(0x00010201) is not None else None,
        "entry_point": hex32(immediate(0x00010100)) if immediate(0x00010100) is not None else None,
        "original_base_address": hex32(immediate(0x00010001))
        if immediate(0x00010001) is not None
        else None,
        "system_flags": hex32(immediate(0x00030000)) if immediate(0x00030000) is not None else None,
        "default_stack_size": immediate(0x00020200),
        "execution_info": execution,
        "file_format": file_format,
        "security_info": security,
        "checksum_timestamp": checksum_timestamp,
        "tls_info": tls_info,
        "original_pe_name": original_pe_name,
        "static_libraries": static_libraries,
        "resources": resources,
        "import_libraries": imports,
        "delta_patch_descriptor": delta,
    }


def load_derived(derived_root: Path, build_id: str) -> dict[str, Any]:
    path = derived_root / build_id / "derived-image.json"
    if not path.is_file():
        raise FileNotFoundError(f"derived XEX metadata not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def iter_encoded_strings(data: bytes) -> Iterator[tuple[str, int, str]]:
    for match in ASCII_RE.finditer(data):
        yield "ASCII", match.start(), match.group().decode("ascii")
    for match in UTF16LE_RE.finditer(data):
        yield "UTF-16LE", match.start(), match.group().decode("utf-16le")


def debug_categories(value: str) -> list[str]:
    lower = value.lower()
    categories: list[str] = []
    if ".pdb" in lower or "codeview" in lower or value in {"RSDS", "NB10"}:
        categories.append("pdb-codeview")
    if len(value) >= 8 and re.search(r"[A-Za-z]{3}", value) and SOURCE_EXTENSION_RE.search(value):
        categories.append("source-file")
    if len(value) >= 8 and (
        re.match(r"^[A-Za-z]:\\", value)
        or any(marker in lower for marker in ("/src/", "\\src\\", "\\source\\", "\\build\\", "\\code\\"))
    ):
        categories.append("source-build-path")
    if "assert" in lower or "__file__" in lower or "__function__" in lower:
        categories.append("assertion-residue")
    if value.startswith((".?AV", ".?AU", ".?AT")):
        categories.append("rtti-type")
    if any(marker in lower for marker in ("visual c++", "msvc", "xdk", "compiler", "linker")):
        categories.append("compiler-linker")
    if re.search(
        r"\b(?:Debug|EngineConfig|PhysicsControlled|Player|Stats|Entity|AIManager|LuaPlus)[.:][A-Za-z_]",
        value,
    ):
        categories.append("debug-script-interface")
    if any(
        marker in lower
        for marker in (
            "renderer",
            "rendering",
            "shader",
            "physics",
            "animation",
            "audiom",
            "lua",
            "resource loader",
            "virtual file",
            "memory allocator",
            "profil",
            "telemetry",
            "debug draw",
            "job system",
        )
    ) and len(value) <= 300:
        categories.append("subsystem-terminology")
    return sorted(set(categories))


def scan_debug_strings(
    prototype_root: Path, derived_root: Path
) -> tuple[list[dict[str, Any]], dict[str, dict[str, list[dict[str, Any]]]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    indexes: dict[str, dict[str, list[dict[str, Any]]]] = {}
    scan_summary: dict[str, Any] = {}
    spec_by_id = {spec.build_id: spec for spec in BUILD_SPECS}
    for build_id in FULL_XEX_BUILD_IDS:
        spec = spec_by_id[build_id]
        source = prototype_root / spec.directory_name / "default.xex"
        derived = load_derived(derived_root, build_id)
        build_index: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
        ascii_count = 0
        utf16_count = 0

        sources: list[tuple[str, Path, int | None, str | None]] = [
            ("source-xex", source, None, "default.xex")
        ]
        for block in derived["memory_blocks"]:
            relative = block.get("derived_relative_path")
            if relative:
                sources.append(
                    (
                        "derived-block",
                        derived_root / build_id / relative,
                        int(block["start"], 16),
                        block["name"],
                    )
                )

        for source_kind, path, base_address, block_name in sources:
            data = path.read_bytes()
            for encoding, offset, value in iter_encoded_strings(data):
                if encoding == "ASCII":
                    ascii_count += 1
                else:
                    utf16_count += 1
                location = {
                    "source_kind": source_kind,
                    "block": block_name,
                    "offset": hex32(offset),
                    "guest_address": hex32(base_address + offset) if base_address is not None else None,
                    "encoding": encoding,
                }
                if len(build_index[value]) < 20:
                    build_index[value].append(location)
                categories = debug_categories(value)
                if source_kind == "source-xex" and not any(
                    category in categories
                    for category in (
                        "pdb-codeview",
                        "compiler-linker",
                        "assertion-residue",
                        "source-build-path",
                    )
                ):
                    categories = []
                if categories:
                    records.append(
                        {
                            "build_id": build_id,
                            "source_file": f"{spec.directory_name}/default.xex",
                            "derived_image": f"{build_id}/{path.relative_to(derived_root / build_id).as_posix()}"
                            if source_kind == "derived-block"
                            else None,
                            "block": block_name,
                            "encoding": encoding,
                            "offset": hex32(offset),
                            "guest_address": hex32(base_address + offset)
                            if base_address is not None
                            else None,
                            "string": value,
                            "categories": categories,
                            "evidence_notes": "decrypted loaded image"
                            if source_kind == "derived-block"
                            else "original XEX file bytes",
                        }
                    )

            for signature in (b"RSDS", b"NB10"):
                cursor = 0
                while True:
                    cursor = data.find(signature, cursor)
                    if cursor < 0:
                        break
                    value = signature.decode("ascii")
                    categories = ["pdb-codeview"]
                    record = {
                        "build_id": build_id,
                        "source_file": f"{spec.directory_name}/default.xex",
                        "derived_image": f"{build_id}/{path.relative_to(derived_root / build_id).as_posix()}"
                        if source_kind == "derived-block"
                        else None,
                        "block": block_name,
                        "encoding": "binary-signature",
                        "offset": hex32(cursor),
                        "guest_address": hex32(base_address + cursor)
                        if base_address is not None
                        else None,
                        "string": value,
                        "categories": categories,
                        "evidence_notes": "literal CodeView signature search",
                    }
                    if signature == b"RSDS" and cursor + 24 <= len(data):
                        path_end = data.find(b"\0", cursor + 24, min(len(data), cursor + 24 + 1024))
                        if path_end >= 0:
                            pdb_path = data[cursor + 24 : path_end].decode("utf-8", "replace")
                            record["codeview"] = {
                                "signature": "RSDS",
                                "guid": str(uuid.UUID(bytes_le=data[cursor + 4 : cursor + 20])).upper(),
                                "age": struct.unpack_from("<I", data, cursor + 20)[0],
                                "pdb_path": pdb_path,
                            }
                    if record not in records:
                        records.append(record)
                    cursor += len(signature)

        indexes[build_id] = dict(build_index)
        scan_summary[build_id] = {
            "ascii_strings_scanned": ascii_count,
            "utf16le_strings_scanned": utf16_count,
            "curated_occurrences": sum(1 for record in records if record["build_id"] == build_id),
        }
    records.sort(
        key=lambda record: (
            record["build_id"],
            record["derived_image"] or "",
            record["offset"],
            record["encoding"],
            record["string"],
        )
    )
    return records, indexes, scan_summary


def build_identity_artifact(
    prototype_root: Path, inventory: list[dict[str, Any]], generated_at: str
) -> dict[str, Any]:
    by_build: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for record in inventory:
        by_build[record["build_id"]].append(record)
    builds = []
    for spec in BUILD_SPECS:
        identities = []
        for record in by_build[spec.build_id]:
            name = record["filename"].lower()
            if name not in IDENTITY_FILENAMES and name != "4d5307f1":
                continue
            path = prototype_root / spec.directory_name / record["relative_path"]
            content, encoding = read_text_exact(path)
            identities.append(
                {
                    "relative_path": record["relative_path"],
                    "size": record["size"],
                    "sha256": record["sha256"],
                    "magic": record["magic"],
                    "text_encoding": encoding,
                    "exact_text": content,
                }
            )
        default_xex = next(
            (record for record in by_build[spec.build_id] if record["relative_path"].lower() == "default.xex"),
            None,
        )
        builds.append(
            {
                "build_id": spec.build_id,
                "label": spec.label,
                "directory_name": spec.directory_name,
                "default_xex": {
                    key: default_xex[key] for key in ("size", "sha256", "sha1", "timestamps")
                }
                if default_xex
                else None,
                "identity_files": identities,
            }
        )

    hash_groups: dict[str, list[dict[str, str]]] = collections.defaultdict(list)
    for record in inventory:
        hash_groups[record["sha256"]].append(
            {"build_id": record["build_id"], "relative_path": record["relative_path"]}
        )
    duplicates = []
    for digest, members in hash_groups.items():
        if len({member["build_id"] for member in members}) < 2:
            continue
        duplicates.append({"sha256": digest, "members": sorted(members, key=lambda item: (item["build_id"], item["relative_path"]))})
    duplicates.sort(key=lambda group: (group["members"][0]["relative_path"].lower(), group["sha256"]))
    return artifact(
        "fable2-prototype-builds",
        generated_at,
        source_root={"id": "fable2-prototype-corpus", "path": str(prototype_root.resolve())},
        builds=builds,
        cross_build_identical_files=duplicates,
    )


def xex_metadata_artifact(
    prototype_root: Path, derived_root: Path, canonical_root: Path, stfs_root: Path, generated_at: str
) -> dict[str, Any]:
    specs = {spec.build_id: spec for spec in BUILD_SPECS}
    records = []
    for build_id in FULL_XEX_BUILD_IDS:
        spec = specs[build_id]
        source = prototype_root / spec.directory_name / "default.xex"
        record = parse_xex(source, build_id, f"{spec.directory_name}/default.xex")
        derived = load_derived(derived_root, build_id)
        record["derived_image"] = {
            "schema": derived["schema"],
            "exporter": derived["exporter"],
            "toolchain": derived["toolchain"],
            "program": derived["program"],
            "memory_blocks": derived["memory_blocks"],
            "external_symbols": [symbol for symbol in derived.get("symbols", []) if symbol.get("is_external")],
        }
        records.append(record)

    canonical_base = canonical_root / "default.xex"
    canonical_xexp = canonical_root / "default.xexp"
    records.append(parse_xex(canonical_base, "canonical-retail-base", "canonical-tu1/default.xex"))
    records.append(parse_xex(canonical_xexp, "canonical-retail-tu1-xexp", "canonical-tu1/default.xexp"))
    patch_xexp = stfs_root / "default.xexp"
    if patch_xexp.is_file():
        records.append(parse_xex(patch_xexp, "patch-data-xexp", "Patch Data prototype/4D5307F1:default.xexp"))

    derived_canonical = load_derived(derived_root, "canonical-tu1")
    for record in records:
        if record["artifact_id"] == "canonical-retail-base":
            record["derived_post_patch_image"] = {
                "source_xexp_sha256": sha_file(canonical_xexp),
                "program": derived_canonical["program"],
                "memory_blocks": derived_canonical["memory_blocks"],
            }

    records.sort(key=lambda record: record["artifact_id"])
    return artifact(
        "fable2-prototype-xex-metadata",
        generated_at,
        parsers={
            "xex_header": "bounded stdlib big-endian metadata parser based on ReXGlue xex2_info.h",
            "derived_image": "Ghidra 12.1.2 + pinned XEXLoaderWV d0af801aee083c86950b90c3db78b2e1c642067f",
        },
        records=records,
    )


def decode_menu_quotes(line: str) -> list[str]:
    values = []
    for match in re.finditer(r'"((?:[^"\\]|\\.)*)"', line):
        value = match.group(1).replace(r'\"', '"').replace(r"\\", "\\")
        values.append(value)
    return values


def symbol_xex_matches(
    name: str, index: dict[str, list[dict[str, Any]]]
) -> list[dict[str, Any]]:
    results = []
    candidates = [(name, "exact")]
    final = re.split(r"[.:]", name)[-1]
    if final != name and len(final) >= 8:
        candidates.append((final, "terminal-component"))
    for candidate, match_kind in candidates:
        for location in index.get(candidate, []):
            result = dict(location)
            result["matched_string"] = candidate
            result["match_kind"] = match_kind
            results.append(result)
    return results


def api_names(value: str) -> set[str]:
    names = set(API_RE.findall(value))
    return {
        name
        for name in names
        if "." in name or (":" in name and not name.lower().startswith("toggle:"))
    }


def make_pointer_correlator(derived_root: Path, build_id: str):
    blocks = derived_blocks(derived_root, build_id)
    executable_ranges = [
        (int(metadata["start"], 16), int(metadata["start"], 16) + len(data))
        for metadata, data in blocks.values()
        if metadata.get("execute")
    ]
    cache: dict[int, list[dict[str, Any]]] = {}

    def is_executable(address: int) -> bool:
        return any(start <= address < end for start, end in executable_ranges)

    def correlate(target: int) -> list[dict[str, Any]]:
        if target in cache:
            return cache[target]
        needle = struct.pack(">I", target)
        references = []
        for metadata, data in blocks.values():
            block_start = int(metadata["start"], 16)
            cursor = 0
            while len(references) < 20:
                cursor = data.find(needle, cursor)
                if cursor < 0:
                    break
                reference_address = block_start + cursor
                if reference_address % 4 == 0 and not metadata.get("execute"):
                    callback_candidates = []
                    window_start = max(0, cursor - 0x20)
                    window_end = min(len(data) - 3, cursor + 0x24)
                    for field_offset in range(window_start, window_end, 4):
                        value = struct.unpack_from(">I", data, field_offset)[0]
                        if is_executable(value):
                            callback_candidates.append(
                                {
                                    "field_delta": field_offset - cursor,
                                    "guest_address": hex32(value),
                                }
                            )
                    references.append(
                        {
                            "reference_address": hex32(reference_address),
                            "block": metadata["name"],
                            "nearby_executable_pointer_candidates": callback_candidates,
                        }
                    )
                cursor += 1
        cache[target] = references
        return references

    return correlate


def script_artifacts(
    prototype_root: Path,
    derived_root: Path,
    inventory: list[dict[str, Any]],
    xex_indexes: dict[str, dict[str, list[dict[str, Any]]]],
    generated_at: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    specs = {spec.build_id: spec for spec in BUILD_SPECS}
    script_records = []
    menu_entries = []
    by_build_path = {(record["build_id"], record["relative_path"].lower()): record for record in inventory}
    correlators = {
        build_id: make_pointer_correlator(derived_root, build_id) for build_id in FULL_XEX_BUILD_IDS
    }

    def enriched_matches(build_id: str, name: str) -> list[dict[str, Any]]:
        matches = symbol_xex_matches(name, xex_indexes[build_id])
        for match in matches:
            address = match.get("guest_address")
            match["pointer_references"] = (
                correlators[build_id](int(address, 16)) if address is not None else []
            )
        return matches

    for build_id in FULL_XEX_BUILD_IDS:
        spec = specs[build_id]
        build_records = [record for record in inventory if record["build_id"] == build_id]
        relevant = [
            record
            for record in build_records
            if record["filename"].lower() in SCRIPT_NAMES
            or (record["extension"] == ".lua" and "scripts" in record["relative_path"].lower())
        ]
        for source_record in relevant:
            path = prototype_root / spec.directory_name / source_record["relative_path"]
            data = path.read_bytes()
            is_lua_bytecode = data.startswith(b"\x1bLua")
            if not is_lua_bytecode:
                text, encoding = read_text_exact(path, maximum=8 * 1024 * 1024)
            else:
                text, encoding = None, None

            if text is not None and "debugmenu" in path.name.lower():
                for line_number, line in enumerate(text.splitlines(), 1):
                    quoted = decode_menu_quotes(line)
                    if len(quoted) < 2:
                        continue
                    expression, label = quoted[0], quoted[1]
                    names = sorted(api_names(expression))
                    entry = {
                        "build_id": build_id,
                        "source_path": source_record["relative_path"],
                        "source_line": line_number,
                        "expression": expression,
                        "label": label,
                        "names": names,
                    }
                    menu_entries.append(entry)
                    for name in names:
                        matches = enriched_matches(build_id, name)
                        script_records.append(
                            {
                                "name": name,
                                "kind": "debug-menu-command",
                                "build_id": build_id,
                                "source_path": source_record["relative_path"],
                                "source_line": line_number,
                                "source_offset": None,
                                "xex_string_matches": matches,
                                "notes": "Menu expression; execution may resolve through Lua or a native binding.",
                                "confidence": "strongly-supported" if matches else "confirmed",
                            }
                        )

            string_values: list[tuple[int, str]] = []
            if is_lua_bytecode:
                string_values = [(offset, value) for enc, offset, value in iter_encoded_strings(data) if enc == "ASCII"]
            elif text is not None and path.suffix.lower() == ".lua":
                string_values = [(match.start(), match.group(0)) for match in re.finditer(r"[^\s'\"]+", text)]

            seen_for_file: set[str] = set()
            for offset, value in string_values:
                names = api_names(value)
                if IDENTIFIER_RE.match(value) and any(
                    value.startswith(prefix)
                    for prefix in (
                        "Debug",
                        "Engine",
                        "Entity",
                        "Physics",
                        "Player",
                        "Stats",
                        "State",
                        "Register",
                        "Create",
                        "Save",
                        "Load",
                        "Lua",
                        "Environment",
                        "Quest",
                        "Gameflow",
                    )
                ):
                    names.add(value)
                for name in sorted(names):
                    if name in seen_for_file:
                        continue
                    seen_for_file.add(name)
                    matches = enriched_matches(build_id, name)
                    script_records.append(
                        {
                            "name": name,
                            "kind": "native-binding-candidate" if matches else "lua-symbol",
                            "build_id": build_id,
                            "source_path": source_record["relative_path"],
                            "source_line": None,
                            "source_offset": hex32(offset),
                            "xex_string_matches": matches,
                            "notes": "Compiled Lua constant" if is_lua_bytecode else "Lua source token",
                            "confidence": "possible" if matches else "confirmed",
                        }
                    )

    script_records.sort(
        key=lambda record: (
            record["build_id"],
            record["source_path"].lower(),
            record["source_line"] or 0,
            record["name"],
        )
    )
    menu_entries.sort(key=lambda record: (record["build_id"], record["source_path"].lower(), record["source_line"]))

    tree_comparisons = []
    for build_id in FULL_XEX_BUILD_IDS:
        scripts = {
            path[len("data/scripts/") :]: record
            for (record_build, path), record in by_build_path.items()
            if record_build == build_id and path.startswith("data/scripts/")
        }
        scripts_r = {
            path[len("data/scripts_r/") :]: record
            for (record_build, path), record in by_build_path.items()
            if record_build == build_id and path.startswith("data/scripts_r/")
        }
        names = sorted(set(scripts) | set(scripts_r))
        pairs = []
        for name in names:
            left = scripts.get(name)
            right = scripts_r.get(name)
            pairs.append(
                {
                    "relative_name": name,
                    "scripts": {"size": left["size"], "sha256": left["sha256"]} if left else None,
                    "scripts_r": {"size": right["size"], "sha256": right["sha256"]} if right else None,
                    "identical": bool(left and right and left["sha256"] == right["sha256"]),
                    "size_delta_scripts_r_minus_scripts": right["size"] - left["size"] if left and right else None,
                }
            )
        tree_comparisons.append(
            {
                "build_id": build_id,
                "scripts_count": len(scripts),
                "scripts_r_count": len(scripts_r),
                "paired_count": sum(1 for item in pairs if item["scripts"] and item["scripts_r"]),
                "identical_pair_count": sum(1 for item in pairs if item["identical"]),
                "different_pair_count": sum(
                    1 for item in pairs if item["scripts"] and item["scripts_r"] and not item["identical"]
                ),
                "pairs": pairs,
                "interpretation": {
                    "grade": "probable",
                    "finding": "scripts_r compiled Lua files are systematically smaller, while several text/menu files are byte-identical; the expansion of '_r' is not established.",
                },
            }
        )

    script_output = artifact(
        "fable2-prototype-script-symbols",
        generated_at,
        records=script_records,
        summary={
            "record_count": len(script_records),
            "native_binding_candidate_count": sum(
                1 for record in script_records if record["kind"] == "native-binding-candidate"
            ),
            "records_with_data_pointer_references": sum(
                1
                for record in script_records
                if any(
                    match.get("pointer_references") for match in record["xex_string_matches"]
                )
            ),
            "records_with_nearby_executable_pointer_candidates": sum(
                1
                for record in script_records
                if any(
                    reference.get("nearby_executable_pointer_candidates")
                    for match in record["xex_string_matches"]
                    for reference in match.get("pointer_references", [])
                )
            ),
        },
    )
    interface_output = artifact(
        "fable2-prototype-debug-interfaces",
        generated_at,
        debug_menu_entries=menu_entries,
        scripts_vs_scripts_r=tree_comparisons,
        native_association_limit="An exact executable string is a candidate anchor, not proof of a registration-table callback.",
    )
    return script_output, interface_output


def log_artifact(
    prototype_root: Path, inventory: list[dict[str, Any]], generated_at: str
) -> dict[str, Any]:
    specs = {spec.build_id: spec for spec in BUILD_SPECS}
    logs = []
    for record in inventory:
        relative_lower = record["relative_path"].lower()
        if record["classification"] != "log" and "fable_ii_r_logs/" not in relative_lower:
            continue
        spec = specs[record["build_id"]]
        path = prototype_root / spec.directory_name / record["relative_path"]
        text, encoding = read_text_exact(path, maximum=16 * 1024 * 1024)
        evidence_lines = []
        if text is not None:
            for line_number, line in enumerate(text.splitlines(), 1):
                if re.search(r"DiscImageCreator|Command|Version|ERROR|WARNING|Fable|Xbox|Drive|Media|build", line, re.I):
                    evidence_lines.append({"line": line_number, "text": line})
                    if len(evidence_lines) == 100:
                        break
        preservation_markers = [
            evidence
            for evidence in evidence_lines
            if "DiscImageCreator" in evidence["text"] or "HL-DT-ST" in evidence["text"]
        ]
        if record["size"] == 0:
            provenance = "empty-file"
            grade = "confirmed"
        elif preservation_markers or "fable_ii_r_logs/" in relative_lower:
            provenance = "disc-preservation-or-extraction-log"
            grade = "confirmed" if preservation_markers else "strongly-supported"
        else:
            provenance = "unknown-log"
            grade = "possible"
        logs.append(
            {
                "build_id": record["build_id"],
                "relative_path": record["relative_path"],
                "size": record["size"],
                "sha256": record["sha256"],
                "text_encoding": encoding,
                "provenance_classification": provenance,
                "confidence": grade,
                "evidence_lines": evidence_lines,
            }
        )
    logs.sort(key=lambda item: (item["build_id"], item["relative_path"].lower()))
    return artifact(
        "fable2-prototype-log-evidence",
        generated_at,
        records=logs,
        conclusions=[
            {
                "grade": "confirmed",
                "finding": "Fable II (Jul 10, 2009 prototype)/lhdebug.log is zero bytes and contains no runtime evidence.",
            },
            {
                "grade": "confirmed",
                "finding": "The September Fable_II_R_logs files are preservation/extraction records, not Lionhead runtime logs.",
            },
        ],
    )


def resource_artifact(
    prototype_root: Path, inventory: list[dict[str, Any]], generated_at: str
) -> dict[str, Any]:
    specs = {spec.build_id: spec for spec in BUILD_SPECS}
    records = []
    for source_record in inventory:
        if source_record["extension"] not in RESOURCE_EXTENSIONS:
            continue
        spec = specs[source_record["build_id"]]
        path = prototype_root / spec.directory_name / source_record["relative_path"]
        scan_limit = 32 * 1024 * 1024
        scanned = min(path.stat().st_size, scan_limit)
        with path.open("rb") as stream:
            data = stream.read(scanned)
        samples = []
        readable_count = 0
        for match in ASCII_RE.finditer(data):
            value = match.group().decode("ascii")
            if len(value) > 160 or not re.search(r"[A-Za-z_]{3}", value):
                continue
            readable_count += 1
            if len(samples) < 80 and (
                re.search(r"shader|render|effect|material|animation|entity|physics|speech|gui|environment", value, re.I)
                or re.match(r"^[A-Za-z_][A-Za-z0-9_./\\:-]{3,}$", value)
            ):
                samples.append({"offset": hex32(match.start()), "string": value})
        records.append(
            {
                "build_id": source_record["build_id"],
                "relative_path": source_record["relative_path"],
                "classification": source_record["classification"],
                "size": source_record["size"],
                "sha256": source_record["sha256"],
                "bytes_scanned": scanned,
                "scan_complete": scanned == source_record["size"],
                "readable_ascii_candidate_count": readable_count,
                "semantic_string_samples": samples,
            }
        )
    records.sort(key=lambda item: (item["relative_path"].lower(), item["build_id"]))
    by_relative: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for record in records:
        by_relative[record["relative_path"].lower()].append(record)
    comparisons = []
    for relative, members in by_relative.items():
        if len(members) < 2:
            continue
        comparisons.append(
            {
                "relative_path": relative,
                "members": [
                    {"build_id": member["build_id"], "size": member["size"], "sha256": member["sha256"]}
                    for member in members
                ],
                "all_identical": len({member["sha256"] for member in members}) == 1,
            }
        )
    comparisons.sort(key=lambda item: item["relative_path"])
    return artifact(
        "fable2-prototype-resource-triage",
        generated_at,
        scan_policy={
            "maximum_bytes_per_file": scan_limit,
            "purpose": "obvious readable metadata triage only; no container reverse engineering",
        },
        records=records,
        cross_build_comparisons=comparisons,
    )


def derived_blocks(derived_root: Path, build_id: str) -> dict[str, tuple[dict[str, Any], bytes]]:
    metadata = load_derived(derived_root, build_id)
    result = {}
    for block in metadata["memory_blocks"]:
        relative = block.get("derived_relative_path")
        if not relative:
            continue
        path = derived_root / build_id / relative
        data = path.read_bytes()
        expected_hash = block.get("sha256")
        if expected_hash and sha_bytes(data) != expected_hash.upper():
            raise ValueError(f"derived block hash mismatch: {path}")
        result[block["name"]] = (block, data)
    return result


def compare_blocks(
    left_id: str, right_id: str, derived_root: Path
) -> list[dict[str, Any]]:
    left = derived_blocks(derived_root, left_id)
    right = derived_blocks(derived_root, right_id)
    comparisons = []
    for name in sorted(set(left) | set(right)):
        if name not in left or name not in right:
            comparisons.append(
                {
                    "section": name,
                    "left_present": name in left,
                    "right_present": name in right,
                    "same_address": False,
                    "same_size": False,
                    "identical": False,
                }
            )
            continue
        left_meta, left_data = left[name]
        right_meta, right_data = right[name]
        left_start = int(left_meta["start"], 16)
        right_start = int(right_meta["start"], 16)
        overlap_start = max(left_start, right_start)
        overlap_end = min(left_start + len(left_data), right_start + len(right_data))
        equal_bytes = 0
        exact_4k_chunks = 0
        chunk_count = 0
        if overlap_end > overlap_start:
            left_slice = left_data[overlap_start - left_start : overlap_end - left_start]
            right_slice = right_data[overlap_start - right_start : overlap_end - right_start]
            equal_bytes = sum(a == b for a, b in zip(left_slice, right_slice))
            for offset in range(0, len(left_slice), 4096):
                left_chunk = left_slice[offset : offset + 4096]
                right_chunk = right_slice[offset : offset + 4096]
                chunk_count += 1
                if left_chunk == right_chunk:
                    exact_4k_chunks += 1
        overlap_size = max(0, overlap_end - overlap_start)
        comparisons.append(
            {
                "section": name,
                "left_start": left_meta["start"],
                "right_start": right_meta["start"],
                "left_size": len(left_data),
                "right_size": len(right_data),
                "left_sha256": sha_bytes(left_data),
                "right_sha256": sha_bytes(right_data),
                "same_address": left_start == right_start,
                "same_size": len(left_data) == len(right_data),
                "identical": left_data == right_data,
                "overlap_start": hex32(overlap_start) if overlap_size else None,
                "overlap_size": overlap_size,
                "same_address_equal_byte_count": equal_bytes,
                "same_address_equal_byte_ratio": round(equal_bytes / overlap_size, 8)
                if overlap_size
                else None,
                "exact_4k_chunk_count": exact_4k_chunks,
                "overlap_4k_chunk_count": chunk_count,
            }
        )
    return comparisons


def inventory_lookup(
    inventory: list[dict[str, Any]], build_id: str, relative_path: str
) -> dict[str, Any] | None:
    relative_lower = relative_path.lower()
    return next(
        (
            record
            for record in inventory
            if record["build_id"] == build_id and record["relative_path"].lower() == relative_lower
        ),
        None,
    )


def tu1_relationship_artifact(
    prototype_root: Path,
    canonical_root: Path,
    stfs_root: Path,
    derived_root: Path,
    inventory: list[dict[str, Any]],
    xex_metadata: dict[str, Any],
    canonical_closure: Path,
    generated_at: str,
) -> dict[str, Any]:
    records_by_id = {record["artifact_id"]: record for record in xex_metadata["records"]}
    jul = records_by_id["jul-2009"]
    build = records_by_id["build-23.12.02.0330"]
    canonical_base = records_by_id["canonical-retail-base"]
    canonical_xexp = records_by_id["canonical-retail-tu1-xexp"]
    patch_xexp = records_by_id.get("patch-data-xexp")

    manifest_source = inventory_lookup(inventory, "build-23.12.02.0330", "tu1_data.manifest")
    extracted_manifest = stfs_root / "tu1_data.manifest"
    extracted_bnk = stfs_root / "data" / "tu1_data.bnk"
    build_bnk = inventory_lookup(inventory, "build-23.12.02.0330", "data/tu1_data.bnk")
    canonical_bnk = canonical_root.parent / "update" / "data" / "tu1_data.bnk"
    closure = json.loads(canonical_closure.read_text(encoding="utf-8"))
    canonical_identity = closure["image_identity"]
    expected_canonical_hash = "BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00"
    if canonical_identity.get("patched_image_sha256") != expected_canonical_hash:
        raise ValueError(
            f"canonical closure identity mismatch: {canonical_identity.get('patched_image_sha256')}"
        )

    source_digest_matches = []
    if patch_xexp and patch_xexp.get("delta_patch_descriptor"):
        digest = patch_xexp["delta_patch_descriptor"]["source_digest_sha1"]
        for candidate_id in ("sep-2008", "jul-2009", "build-23.12.02.0330", "canonical-retail-base"):
            candidate = records_by_id[candidate_id]
            security = candidate.get("security_info") or {}
            source_digest_matches.append(
                {
                    "candidate": candidate_id,
                    "patch_source_digest_sha1": digest,
                    "candidate_header_digest_sha1": security.get("header_digest_sha1"),
                    "candidate_section_digest_sha1": security.get("section_digest_sha1"),
                    "matches_header_digest": digest == security.get("header_digest_sha1"),
                    "matches_section_digest": digest == security.get("section_digest_sha1"),
                }
            )

    conclusions = [
        {
            "grade": "confirmed",
            "finding": "The July 2009 and 23.12.02.0330 default.xex files are different XEX containers but decrypt to byte-identical initialized PE sections.",
            "evidence": {
                "jul_xex_sha256": jul["sha256"],
                "build_23_xex_sha256": build["sha256"],
                "all_derived_sections_identical": all(
                    comparison["identical"]
                    for comparison in compare_blocks("jul-2009", "build-23.12.02.0330", derived_root)
                ),
            },
        },
        {
            "grade": "confirmed",
            "finding": "The Patch Data STFS package carries build_version.txt 23.12.02.0330 and a tu1_data.manifest byte-identical to the loose 23.12.02.0330 manifest.",
            "evidence": {
                "loose_manifest_sha256": manifest_source["sha256"] if manifest_source else None,
                "package_manifest_sha256": sha_file(extracted_manifest) if extracted_manifest.is_file() else None,
            },
        },
        {
            "grade": "confirmed",
            "finding": "The loose build, Patch Data package, and canonical retail TU1 tu1_data.bnk files are three distinct payloads.",
            "evidence": {
                "loose_build": {"size": build_bnk["size"], "sha256": build_bnk["sha256"]}
                if build_bnk
                else None,
                "patch_package": {"size": extracted_bnk.stat().st_size, "sha256": sha_file(extracted_bnk)}
                if extracted_bnk.is_file()
                else None,
                "canonical_retail_tu1": {
                    "size": canonical_bnk.stat().st_size,
                    "sha256": sha_file(canonical_bnk),
                }
                if canonical_bnk.is_file()
                else None,
            },
        },
        {
            "grade": "strongly-supported",
            "finding": "Build 23.12.02.0330 is a development build in the retail-TU1 development lineage, not a byte-identical retail TU1 executable or asset set.",
            "basis": "matching build/package identity and close section layout, combined with distinct XEX, code-section, XEXP, and tu1_data.bnk hashes",
        },
        {
            "grade": "confirmed",
            "finding": "The July/23 development PE timestamp 0x4A571818 (2009-07-10T10:29:44Z) is later than canonical retail TU1 timestamp 0x4A53C85A (2009-07-07T22:12:42Z).",
            "basis": "prototype XEX checksum/timestamp optional header and canonical entrypoint-closure image identity",
        },
    ]

    return artifact(
        "fable2-prototype-tu1-relationship",
        generated_at,
        canonical_identity=canonical_identity,
        canonical_identity_source={
            "relative_path": canonical_closure.as_posix(),
            "sha256": sha_file(canonical_closure),
        },
        july_vs_build_23_sections=compare_blocks("jul-2009", "build-23.12.02.0330", derived_root),
        build_23_vs_canonical_tu1_sections=compare_blocks(
            "build-23.12.02.0330", "canonical-tu1", derived_root
        ),
        patch_xexp_source_digest_tests=source_digest_matches,
        patch_application_observations=[
            {
                "base": "build-23.12.02.0330/default.xex",
                "result": "Ghidra XEXLoaderWV import failed before producing a patched image",
                "confidence": "confirmed",
                "interpretation": "The extracted XEXP is not demonstrated compatible with this development XEX container.",
            },
            {
                "base": "canonical retail base/default.xex",
                "result": "Ghidra XEXLoaderWV import failed before producing a patched image",
                "confidence": "confirmed",
                "interpretation": "The extracted beta XEXP is not demonstrated compatible with the canonical GOTY retail base XEX.",
            },
        ],
        conclusions=conclusions,
        relationship_answer={
            "same_executable_generation_as_tu1": "strongly-supported related lineage, not binary equivalent",
            "pre_or_post_tu1": "confirmed later PE timestamp than canonical retail TU1; exact source-control ancestry remains unproven",
            "development_build_incorporating_tu_data": "confirmed",
            "patch_data_exactly_retail_tu1": "confirmed false for the XEXP and tu1_data.bnk hashes",
            "addresses_layout_preserved": "strongly-supported; major sections share addresses and sizes are very close",
        },
    )


def read_function_bytes(
    blocks: dict[str, tuple[dict[str, Any], bytes]], start: int, size: int
) -> bytes | None:
    for metadata, data in blocks.values():
        block_start = int(metadata["start"], 16)
        if block_start <= start and start + size <= block_start + len(data):
            return data[start - block_start : start - block_start + size]
    return None


def pdata_functions(derived_root: Path, build_id: str) -> list[dict[str, Any]]:
    blocks = derived_blocks(derived_root, build_id)
    pdata_metadata, pdata = blocks[".pdata"]
    functions = []
    for offset in range(0, len(pdata) - 7, 8):
        start, unwind = struct.unpack_from(">II", pdata, offset)
        size = ((unwind >> 8) & 0x3FFFFF) * 4
        if start == 0 or size == 0:
            continue
        code = read_function_bytes(blocks, start, size)
        if code is None or len(code) % 4:
            continue
        words = list(struct.unpack(f">{len(code) // 4}I", code))
        normalized = []
        structural = []
        direct_calls = 0
        indirect_branches = 0
        conditional_branches = 0
        for word in words:
            opcode = word >> 26
            normalized_word = word
            if opcode == 18:
                normalized_word = word & 0xFC000003
                if word & 1:
                    direct_calls += 1
            elif opcode == 16:
                normalized_word = word & 0xFFFF0003
                conditional_branches += 1
            if opcode == 19 and ((word >> 1) & 0x3FF) == 528:
                indirect_branches += 1
            normalized.append(normalized_word)
            extended = (word >> 1) & 0x3FF if opcode in {19, 31, 59, 63} else 0
            structural.append(struct.pack(">HH", opcode, extended))
        normalized_bytes = b"".join(struct.pack(">I", word) for word in normalized)
        functions.append(
            {
                "start": start,
                "start_hex": hex32(start),
                "size": size,
                "end_exclusive": hex32(start + size),
                "raw_sha256": sha_bytes(code),
                "branch_normalized_sha256": sha_bytes(normalized_bytes),
                "opcode_structure_sha256": sha_bytes(b"".join(structural)),
                "instruction_count": len(words),
                "direct_call_count": direct_calls,
                "conditional_branch_count": conditional_branches,
                "indirect_branch_count": indirect_branches,
                "pdata_record_address": hex32(int(pdata_metadata["start"], 16) + offset),
            }
        )
    functions.sort(key=lambda function: function["start"])
    return functions


def unique_hash_map(functions: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for function in functions:
        grouped[function[key]].append(function)
    return {digest: members[0] for digest, members in grouped.items() if len(members) == 1}


def crossbuild_pair(
    left_id: str,
    right_id: str,
    functions_by_build: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    left = functions_by_build[left_id]
    right = functions_by_build[right_id]
    left_addresses = {function["start"]: function for function in left}
    right_addresses = {function["start"]: function for function in right}
    shared_addresses = sorted(set(left_addresses) & set(right_addresses))
    same_address_exact = sum(
        left_addresses[address]["raw_sha256"] == right_addresses[address]["raw_sha256"]
        and left_addresses[address]["size"] == right_addresses[address]["size"]
        for address in shared_addresses
    )
    same_address_normalized = sum(
        left_addresses[address]["branch_normalized_sha256"]
        == right_addresses[address]["branch_normalized_sha256"]
        and left_addresses[address]["size"] == right_addresses[address]["size"]
        for address in shared_addresses
    )

    unique_results = {}
    match_pairs_by_kind: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {}
    for key in ("raw_sha256", "branch_normalized_sha256", "opcode_structure_sha256"):
        left_unique = unique_hash_map(left, key)
        right_unique = unique_hash_map(right, key)
        shared = sorted(set(left_unique) & set(right_unique))
        pairs = [(left_unique[digest], right_unique[digest]) for digest in shared]
        match_pairs_by_kind[key] = pairs
        deltas = collections.Counter(right_fn["start"] - left_fn["start"] for left_fn, right_fn in pairs)
        unique_results[key] = {
            "left_unique_fingerprint_count": len(left_unique),
            "right_unique_fingerprint_count": len(right_unique),
            "unique_matches": len(pairs),
            "same_address_matches": sum(left_fn["start"] == right_fn["start"] for left_fn, right_fn in pairs),
            "most_common_address_deltas": [
                {"delta": delta, "delta_hex": f"{delta:+#x}", "count": count}
                for delta, count in sorted(deltas.items(), key=lambda item: (-item[1], item[0]))[:12]
            ],
        }

    samples = []
    selected: set[tuple[int, int]] = set()

    def add_sample(category: str, pair: tuple[dict[str, Any], dict[str, Any]] | None) -> None:
        if pair is None or (pair[0]["start"], pair[1]["start"]) in selected:
            return
        selected.add((pair[0]["start"], pair[1]["start"]))
        samples.append({"category": category, "left": pair[0], "right": pair[1]})

    raw_pairs = match_pairs_by_kind["raw_sha256"]
    add_sample("tiny-leaf-exact", next((pair for pair in raw_pairs if pair[0]["size"] <= 0x10), None))
    add_sample("large-exact", next((pair for pair in sorted(raw_pairs, key=lambda pair: -pair[0]["size"]) if pair[0]["size"] >= 0x1000), None))
    add_sample("relocated-exact", next((pair for pair in raw_pairs if pair[0]["start"] != pair[1]["start"]), None))
    add_sample(
        "indirect-dispatch-exact",
        next((pair for pair in raw_pairs if pair[0]["indirect_branch_count"] >= 2), None),
    )
    normalized_only = next(
        (
            pair
            for pair in match_pairs_by_kind["branch_normalized_sha256"]
            if pair[0]["raw_sha256"] != pair[1]["raw_sha256"]
        ),
        None,
    )
    add_sample("branch-relocation-normalized", normalized_only)
    structure_only = next(
        (
            pair
            for pair in match_pairs_by_kind["opcode_structure_sha256"]
            if pair[0]["branch_normalized_sha256"] != pair[1]["branch_normalized_sha256"]
            and pair[0]["size"] >= 0x40
        ),
        None,
    )
    add_sample("opcode-structure-only", structure_only)
    changed_same_address = next(
        (
            (left_addresses[address], right_addresses[address])
            for address in shared_addresses
            if left_addresses[address]["raw_sha256"] != right_addresses[address]["raw_sha256"]
            and left_addresses[address]["size"] == right_addresses[address]["size"]
        ),
        None,
    )
    add_sample("changed-same-address", changed_same_address)

    return {
        "left_build": left_id,
        "right_build": right_id,
        "left_function_count": len(left),
        "right_function_count": len(right),
        "shared_start_address_count": len(shared_addresses),
        "same_address_exact_function_count": same_address_exact,
        "same_address_branch_normalized_count": same_address_normalized,
        "fingerprint_matching": unique_results,
        "representative_samples": samples,
    }


def crossbuild_artifact(derived_root: Path, generated_at: str) -> dict[str, Any]:
    functions = {build_id: pdata_functions(derived_root, build_id) for build_id in DERIVED_BUILD_IDS}
    pairs = [
        crossbuild_pair("sep-2008", "jul-2009", functions),
        crossbuild_pair("jul-2009", "canonical-tu1", functions),
        crossbuild_pair("build-23.12.02.0330", "canonical-tu1", functions),
    ]
    return artifact(
        "fable2-prototype-crossbuild-feasibility",
        generated_at,
        method={
            "boundary_source": "big-endian IMAGE_CE_RUNTIME_FUNCTION records from each derived .pdata block",
            "raw_fingerprint": "SHA-256 of exact function bytes",
            "branch_normalized_fingerprint": "SHA-256 after clearing PPC b/bl LI and bc BD displacement fields",
            "opcode_structure_fingerprint": "SHA-256 of primary opcode plus XO for opcodes 19/31/59/63",
            "limitation": "Phase 1 feasibility only; fingerprints are candidates and do not authorize TU1 renames.",
        },
        comparisons=pairs,
        assessment={
            "grade": "strongly-supported",
            "phase2_matcher_practical": True,
            "recommended_features": [
                "exact .pdata boundaries",
                "unique raw or branch-normalized PPC fingerprints",
                "address delta neighbourhood",
                "direct-call topology",
                "string and constant references",
                "CFG verification before accepting non-exact matches",
            ],
            "do_not_trust_alone": [
                "function size",
                "opcode-only structure",
                "same guest address",
                "prototype semantic name",
            ],
        },
    )


def inventory_summary_markdown(inventory_artifact: dict[str, Any]) -> str:
    lines = [
        "# Prototype corpus inventory",
        "",
        "Authoritative data: `prototype-inventory.json`.",
        "",
        "| Build | Files | Bytes |",
        "|---|---:|---:|",
    ]
    for build_id, summary in inventory_artifact["build_summaries"].items():
        lines.append(f"| `{build_id}` | {summary['file_count']} | {summary['total_size']} |")
    lines.extend(["", f"Total files: **{inventory_artifact['totals']['file_count']}**.", ""])
    return "\n".join(lines)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", dir=path.parent, delete=False
    ) as stream:
        stream.write(text)
        temporary = Path(stream.name)
    os.replace(temporary, path)


def generate(args: argparse.Namespace) -> int:
    prototype_root = args.prototype_root.resolve()
    derived_root = args.derived_root.resolve()
    stfs_root = args.stfs_root.resolve()
    canonical_root = args.canonical_root.resolve()
    output = args.output.resolve()
    existing_hashes = {}
    if args.check_determinism:
        if not output.is_dir():
            print(f"ERROR: deterministic baseline does not exist: {output}", file=sys.stderr)
            return 1
        existing_hashes = {
            path.name: sha_file(path)
            for path in sorted(output.iterdir(), key=lambda item: item.name.casefold())
            if path.is_file() and path.suffix.lower() in {".json", ".md"}
        }

    inventory, build_summaries = inventory_corpus(prototype_root)
    inventory_output = artifact(
        "fable2-prototype-inventory",
        args.generated_at,
        source_root={"id": "fable2-prototype-corpus", "path": str(prototype_root)},
        totals={
            "file_count": len(inventory),
            "total_size": sum(record["size"] for record in inventory),
        },
        build_summaries=build_summaries,
        files=inventory,
    )
    builds_output = build_identity_artifact(prototype_root, inventory, args.generated_at)
    xex_output = xex_metadata_artifact(
        prototype_root, derived_root, canonical_root, stfs_root, args.generated_at
    )
    debug_records, xex_indexes, scan_summary = scan_debug_strings(prototype_root, derived_root)
    debug_output = artifact(
        "fable2-prototype-debug-strings",
        args.generated_at,
        search_encodings=["ASCII", "UTF-16LE"],
        category_definitions=[
            "pdb-codeview",
            "source-file",
            "source-build-path",
            "assertion-residue",
            "rtti-type",
            "compiler-linker",
            "debug-script-interface",
            "subsystem-terminology",
        ],
        scan_summary=scan_summary,
        records=debug_records,
    )
    script_output, interface_output = script_artifacts(
        prototype_root, derived_root, inventory, xex_indexes, args.generated_at
    )
    log_output = log_artifact(prototype_root, inventory, args.generated_at)
    resource_output = resource_artifact(prototype_root, inventory, args.generated_at)
    relationship_output = tu1_relationship_artifact(
        prototype_root,
        canonical_root,
        stfs_root,
        derived_root,
        inventory,
        xex_output,
        args.canonical_closure.resolve(),
        args.generated_at,
    )
    crossbuild_output = crossbuild_artifact(derived_root, args.generated_at)

    outputs = {
        "prototype-inventory.json": inventory_output,
        "prototype-builds.json": builds_output,
        "prototype-xex-metadata.json": xex_output,
        "prototype-debug-strings.json": debug_output,
        "prototype-debug-interfaces.json": interface_output,
        "prototype-script-symbols.json": script_output,
        "prototype-log-evidence.json": log_output,
        "prototype-tu1-relationship.json": relationship_output,
        "prototype-crossbuild-feasibility.json": crossbuild_output,
        "prototype-resource-triage.json": resource_output,
    }
    for filename, value in outputs.items():
        atomic_json(output / filename, value)
    write_text(output / "prototype-inventory-summary.md", inventory_summary_markdown(inventory_output))
    if args.check_determinism:
        regenerated_hashes = {
            path.name: sha_file(path)
            for path in sorted(output.iterdir(), key=lambda item: item.name.casefold())
            if path.is_file() and path.suffix.lower() in {".json", ".md"}
        }
        if existing_hashes != regenerated_hashes:
            changed = sorted(set(existing_hashes) | set(regenerated_hashes))
            for filename in changed:
                if existing_hashes.get(filename) != regenerated_hashes.get(filename):
                    print(f"ERROR: non-deterministic artifact: {filename}", file=sys.stderr)
            return 1
        print(f"Verified byte-identical regeneration of {len(regenerated_hashes)} artifacts")
    print(f"Generated {len(outputs)} JSON artifacts and inventory summary in {output}")
    return 0


def verify(args: argparse.Namespace) -> int:
    prototype_root = args.prototype_root.resolve()
    evidence = args.evidence.resolve()
    inventory_path = evidence / "prototype-inventory.json"
    stored = json.loads(inventory_path.read_text(encoding="utf-8"))
    actual_records, _ = inventory_corpus(prototype_root)
    actual_by_key = {
        (record["build_id"], record["relative_path"]): record for record in actual_records
    }
    errors = []
    for record in stored["files"]:
        key = (record["build_id"], record["relative_path"])
        actual = actual_by_key.get(key)
        if actual is None:
            errors.append(f"missing source file: {key}")
        elif actual["sha256"] != record["sha256"] or actual["size"] != record["size"]:
            errors.append(f"source identity changed: {key}")
    if len(actual_by_key) != len(stored["files"]):
        errors.append(
            f"file count changed: stored={len(stored['files'])} actual={len(actual_by_key)}"
        )

    required = (
        "prototype-inventory.json",
        "prototype-builds.json",
        "prototype-xex-metadata.json",
        "prototype-debug-strings.json",
        "prototype-debug-interfaces.json",
        "prototype-script-symbols.json",
        "prototype-log-evidence.json",
        "prototype-tu1-relationship.json",
        "prototype-crossbuild-feasibility.json",
        "prototype-resource-triage.json",
    )
    for filename in required:
        path = evidence / filename
        if not path.is_file():
            errors.append(f"missing evidence artifact: {filename}")
            continue
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("schema", {}).get("version") != SCHEMA_VERSION:
            errors.append(f"unexpected schema version: {filename}")
        if value.get("generator", {}).get("version") != TOOL_VERSION:
            errors.append(f"unexpected generator version: {filename}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Verified {len(actual_records)} immutable prototype files and {len(required)} artifacts")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subcommands = result.add_subparsers(dest="command", required=True)
    generate_parser = subcommands.add_parser("generate", help="generate all stable Phase 1 evidence")
    generate_parser.add_argument(
        "--prototype-root", type=Path, default=Path(r"D:\Fable2-Recomp\prototypes")
    )
    generate_parser.add_argument(
        "--derived-root", type=Path, default=Path("out/prototype-archaeology/derived")
    )
    generate_parser.add_argument(
        "--stfs-root", type=Path, default=Path("out/prototype-archaeology/stfs/patch-data")
    )
    generate_parser.add_argument("--canonical-root", type=Path, default=Path("assets/tu1"))
    generate_parser.add_argument(
        "--canonical-closure",
        type=Path,
        default=Path(
            "out/analysis/BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00/entrypoint-closure.json"
        ),
    )
    generate_parser.add_argument(
        "--output", type=Path, default=Path("docs/fable2-prototype-archaeology/phase1/evidence")
    )
    generate_parser.add_argument(
        "--generated-at",
        default="2026-09-11T00:00:00Z",
        help="explicit stable generation timestamp; reuse it for deterministic reruns",
    )
    generate_parser.add_argument(
        "--check-determinism",
        action="store_true",
        help="require regenerated JSON and Markdown to match the existing artifacts byte for byte",
    )
    generate_parser.set_defaults(action=generate)

    verify_parser = subcommands.add_parser("verify", help="rehash sources and validate stable artifacts")
    verify_parser.add_argument(
        "--prototype-root", type=Path, default=Path(r"D:\Fable2-Recomp\prototypes")
    )
    verify_parser.add_argument(
        "--evidence", type=Path, default=Path("docs/fable2-prototype-archaeology/phase1/evidence")
    )
    verify_parser.set_defaults(action=verify)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    return args.action(args)


if __name__ == "__main__":
    raise SystemExit(main())
