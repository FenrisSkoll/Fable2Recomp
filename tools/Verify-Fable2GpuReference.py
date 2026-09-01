#!/usr/bin/env python3
"""Read-only validator for the Fable II G1.5A GPU reference corpus."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DOC_ROOT = ROOT / "docs" / "fable2-gpu-reference"
EVIDENCE_ROOT = DOC_ROOT / "evidence"
SCHEMA_ROOT = ROOT / "tools" / "schemas"

INVENTORY_PATH = EVIDENCE_ROOT / "rexglue-source-inventory.json"
MAP_PATH = EVIDENCE_ROOT / "rexglue-subsystem-map.json"
INVENTORY_SCHEMA_PATH = SCHEMA_ROOT / "fable2-gpu-source-inventory-v1.schema.json"
MAP_SCHEMA_PATH = SCHEMA_ROOT / "fable2-gpu-subsystem-map-v1.schema.json"

REQUIRED_DOCUMENTS = (
    "README.md",
    "00-scope-and-pins.md",
    "01-rexglue-overview.md",
    "rexglue/01-plugin-runtime-boundary.md",
    "rexglue/02-command-processor-and-register-state.md",
    "rexglue/03-shader-pipeline.md",
    "rexglue/04-textures-vertex-fetch-and-samplers.md",
    "rexglue/05-render-targets-edram-resolves.md",
    "rexglue/06-draw-and-pipeline-state.md",
    "rexglue/07-resources-memory-and-synchronization.md",
    "rexglue/08-presentation-backends-and-errors.md",
    "evidence/rexglue-source-inventory.json",
    "evidence/rexglue-subsystem-map.json",
    "g1.5a-completion.md",
)

CONFIDENCE = ("CONFIRMED", "PROBABLE", "UNKNOWN", "NOT APPLICABLE")
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


class Validation:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)


def load_json(path: Path, validation: Validation) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        validation.error(f"unable to read JSON {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        validation.error(f"JSON root is not an object: {path}")
        return {}
    return value


def run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def git_text(repo: Path, *args: str) -> str | None:
    result = run_git(repo, *args)
    if result.returncode != 0:
        return None
    return result.stdout.rstrip("\r\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def validate_with_schema(
    instance: dict[str, Any], schema: dict[str, Any], label: str, validation: Validation
) -> None:
    try:
        import jsonschema  # type: ignore[import-not-found]
    except ImportError:
        validate_schema_node(instance, schema, schema, label, validation)
        return

    validator = jsonschema.Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.path) or "<root>"
        validation.error(f"{label}:{location}: {error.message}")


def validate_schema_node(
    instance: Any,
    node: dict[str, Any],
    root_schema: dict[str, Any],
    location: str,
    validation: Validation,
) -> None:
    """Validate the schema features used by this corpus without dependencies."""
    reference = node.get("$ref")
    if isinstance(reference, str):
        if not reference.startswith("#/"):
            validation.error(f"{location}: unsupported non-local schema reference {reference!r}")
            return
        target: Any = root_schema
        for component in reference[2:].split("/"):
            component = component.replace("~1", "/").replace("~0", "~")
            if not isinstance(target, dict) or component not in target:
                validation.error(f"{location}: unresolved schema reference {reference!r}")
                return
            target = target[component]
        if not isinstance(target, dict):
            validation.error(f"{location}: schema reference is not an object {reference!r}")
            return
        validate_schema_node(instance, target, root_schema, location, validation)
        return

    expected_type = node.get("type")
    type_checks = {
        "object": lambda value: isinstance(value, dict),
        "array": lambda value: isinstance(value, list),
        "string": lambda value: isinstance(value, str),
        "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
        "number": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": lambda value: isinstance(value, bool),
        "null": lambda value: value is None,
    }
    if isinstance(expected_type, str):
        checker = type_checks.get(expected_type)
        if checker is None:
            validation.error(f"{location}: unsupported schema type {expected_type!r}")
            return
        if not checker(instance):
            validation.error(f"{location}: expected {expected_type}, got {type(instance).__name__}")
            return

    if "const" in node and instance != node["const"]:
        validation.error(f"{location}: value does not match schema const {node['const']!r}")
    if "enum" in node and instance not in node["enum"]:
        validation.error(f"{location}: value is outside schema enum {node['enum']!r}")
    pattern = node.get("pattern")
    if isinstance(pattern, str) and isinstance(instance, str) and re.search(pattern, instance) is None:
        validation.error(f"{location}: value does not match pattern {pattern!r}")
    if node.get("format") == "date" and isinstance(instance, str):
        try:
            datetime.date.fromisoformat(instance)
        except ValueError:
            validation.error(f"{location}: value is not an ISO date")

    if isinstance(instance, dict):
        for key in node.get("required", []):
            if key not in instance:
                validation.error(f"{location}: missing required key {key!r}")
        properties = node.get("properties", {})
        if isinstance(properties, dict):
            for key, child_schema in properties.items():
                if key in instance and isinstance(child_schema, dict):
                    validate_schema_node(
                        instance[key], child_schema, root_schema, f"{location}.{key}", validation
                    )

    if isinstance(instance, list):
        minimum = node.get("minItems")
        if isinstance(minimum, int) and len(instance) < minimum:
            validation.error(f"{location}: expected at least {minimum} item(s)")
        item_schema = node.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(instance):
                validate_schema_node(
                    item, item_schema, root_schema, f"{location}[{index}]", validation
                )


def repository_roots(
    inventory: dict[str, Any], sdk_override: Path | None, validation: Validation
) -> tuple[dict[str, Path], dict[str, str]]:
    roots: dict[str, Path] = {"fable2": ROOT}
    commits: dict[str, str] = {}

    for key, name in (("fable_repository", "fable2"), ("rexglue_repository", "rexglue")):
        entry = inventory.get(key, {})
        if not isinstance(entry, dict):
            validation.error(f"{key} is not an object")
            continue
        commit = entry.get("commit")
        if isinstance(commit, str):
            commits[name] = commit
        if name == "rexglue" and sdk_override is not None:
            roots[name] = sdk_override.resolve()
        elif name == "rexglue":
            roots[name] = Path(str(entry.get("path", "")))

    for name, repo in roots.items():
        if not repo.is_dir():
            validation.error(f"{name} repository is unavailable: {repo}")
            continue
        commit = commits.get(name)
        if not commit:
            validation.error(f"{name} repository commit is not recorded")
            continue
        if run_git(repo, "cat-file", "-e", f"{commit}^{{commit}}").returncode != 0:
            validation.error(f"{name} commit is unavailable in {repo}: {commit}")
    return roots, commits


def validate_source_inventory(
    inventory: dict[str, Any], roots: dict[str, Path], commits: dict[str, str], validation: Validation
) -> None:
    for scope in inventory.get("source_scopes", []):
        repository = scope.get("repository")
        repo = roots.get(repository)
        commit = commits.get(repository)
        path = scope.get("path")
        if repo is None or commit is None or not isinstance(path, str):
            validation.error(f"invalid source scope repository/path: {scope!r}")
            continue
        actual_object = git_text(repo, "rev-parse", f"{commit}:{path}")
        if actual_object != scope.get("git_object_sha1"):
            validation.error(
                f"source scope object mismatch {repository}:{path}: "
                f"recorded {scope.get('git_object_sha1')}, actual {actual_object}"
            )
        names = git_text(repo, "ls-tree", "-r", "--name-only", commit, "--", path)
        actual_count = 0 if names is None or names == "" else len(names.splitlines())
        if actual_count != scope.get("file_count"):
            validation.error(
                f"source scope count mismatch {repository}:{path}: "
                f"recorded {scope.get('file_count')}, actual {actual_count}"
            )

    for entry in inventory.get("key_files", []):
        repository = entry.get("repository")
        repo = roots.get(repository)
        commit = commits.get(repository)
        path = entry.get("path")
        if repo is None or commit is None or not isinstance(path, str):
            validation.error(f"invalid key file repository/path: {entry!r}")
            continue
        actual_object = git_text(repo, "rev-parse", f"{commit}:{path}")
        if actual_object != entry.get("blob_sha1"):
            validation.error(
                f"key file blob mismatch {repository}:{path}: "
                f"recorded {entry.get('blob_sha1')}, actual {actual_object}"
            )
            continue
        actual_size_text = git_text(repo, "cat-file", "-s", actual_object)
        actual_size = int(actual_size_text) if actual_size_text is not None else None
        if actual_size != entry.get("size"):
            validation.error(
                f"key file size mismatch {repository}:{path}: "
                f"recorded {entry.get('size')}, actual {actual_size}"
            )
        source = git_text(repo, "show", f"{commit}:{path}")
        if source is None:
            validation.error(f"unable to read key file {repository}:{path}")
            continue
        for symbol in entry.get("symbols", []):
            if symbol not in source:
                validation.error(f"missing inventory symbol {symbol!r} in {repository}:{path}")


def validate_subsystem_map(
    subsystem_map: dict[str, Any], roots: dict[str, Path], commits: dict[str, str], validation: Validation
) -> None:
    identifiers: set[str] = set()
    for subsystem in subsystem_map.get("subsystems", []):
        identifier = subsystem.get("id")
        if not isinstance(identifier, str) or not identifier:
            validation.error(f"invalid subsystem identifier: {identifier!r}")
        elif identifier in identifiers:
            validation.error(f"duplicate subsystem identifier: {identifier}")
        else:
            identifiers.add(identifier)

        for symbol in subsystem.get("symbols", []):
            confidence = symbol.get("confidence")
            if confidence not in CONFIDENCE:
                validation.error(f"invalid confidence {confidence!r} in subsystem {identifier}")
            repository = symbol.get("repository")
            repo = roots.get(repository)
            commit = commits.get(repository)
            path = symbol.get("path")
            name = symbol.get("symbol")
            if repo is None or commit is None or not isinstance(path, str) or not isinstance(name, str):
                validation.error(f"invalid symbol locator in subsystem {identifier}: {symbol!r}")
                continue
            source = git_text(repo, "show", f"{commit}:{path}")
            if source is None:
                validation.error(f"missing symbol source {repository}:{path} for {identifier}")
            elif name not in source:
                validation.error(f"missing symbol {name!r} in {repository}:{path} for {identifier}")

    for relationship in subsystem_map.get("relationships", []):
        source_id = relationship.get("from")
        target_id = relationship.get("to")
        if source_id not in identifiers:
            validation.error(f"relationship source is not a subsystem: {source_id!r}")
        if target_id not in identifiers:
            validation.error(f"relationship target is not a subsystem: {target_id!r}")


def validate_markdown_links(validation: Validation) -> None:
    for markdown in sorted(DOC_ROOT.rglob("*.md")):
        text = markdown.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK_RE.finditer(text):
            target = match.group(1).strip()
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            target = target.split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            candidate = (markdown.parent / target).resolve()
            if not candidate.exists():
                validation.error(f"broken Markdown link in {markdown.relative_to(ROOT)}: {target}")


def validate_artifacts(inventory: dict[str, Any], validation: Validation) -> None:
    for artifact in inventory.get("artifacts", []):
        path = Path(str(artifact.get("path", "")))
        if not path.is_file():
            validation.error(f"artifact is unavailable: {path}")
            continue
        actual_size = path.stat().st_size
        if actual_size != artifact.get("size"):
            validation.error(
                f"artifact size mismatch {path}: recorded {artifact.get('size')}, actual {actual_size}"
            )
        actual_hash = sha256(path)
        if actual_hash != artifact.get("sha256"):
            validation.error(
                f"artifact hash mismatch {path}: recorded {artifact.get('sha256')}, actual {actual_hash}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sdk-root",
        type=Path,
        help="Override the pinned local ReXGlue repository path used for Git verification",
    )
    parser.add_argument(
        "--verify-artifacts",
        action="store_true",
        help="Also require and hash the ignored local build/package artifacts",
    )
    args = parser.parse_args()

    validation = Validation()
    for relative in REQUIRED_DOCUMENTS:
        if not (DOC_ROOT / relative).is_file():
            validation.error(f"required corpus file is missing: docs/fable2-gpu-reference/{relative}")

    inventory = load_json(INVENTORY_PATH, validation)
    subsystem_map = load_json(MAP_PATH, validation)
    inventory_schema = load_json(INVENTORY_SCHEMA_PATH, validation)
    map_schema = load_json(MAP_SCHEMA_PATH, validation)
    if inventory and inventory_schema:
        validate_with_schema(inventory, inventory_schema, "source inventory", validation)
    if subsystem_map and map_schema:
        validate_with_schema(subsystem_map, map_schema, "subsystem map", validation)

    if inventory:
        roots, commits = repository_roots(inventory, args.sdk_root, validation)
        validate_source_inventory(inventory, roots, commits, validation)
        if subsystem_map:
            validate_subsystem_map(subsystem_map, roots, commits, validation)
        if args.verify_artifacts:
            validate_artifacts(inventory, validation)

    validate_markdown_links(validation)

    for warning in validation.warnings:
        print(f"WARNING: {warning}")
    for error in validation.errors:
        print(f"ERROR: {error}")
    if validation.errors:
        print(f"FAIL: {len(validation.errors)} error(s), {len(validation.warnings)} warning(s)")
        return 1
    print(f"PASS: G1.5A GPU reference validated ({len(validation.warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
