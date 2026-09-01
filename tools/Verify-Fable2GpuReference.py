#!/usr/bin/env python3
"""Read-only validator for the Fable II G1.5A/G1.5B GPU reference corpus."""

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
CANARY_INVENTORY_PATH = EVIDENCE_ROOT / "canary-source-inventory.json"
CANARY_MAP_PATH = EVIDENCE_ROOT / "canary-subsystem-map.json"
CANARY_INVENTORY_SCHEMA_PATH = (
    SCHEMA_ROOT / "fable2-gpu-canary-source-inventory-v1.schema.json"
)
CANARY_MAP_SCHEMA_PATH = SCHEMA_ROOT / "fable2-gpu-canary-subsystem-map-v1.schema.json"

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
    "02-xenia-canary-overview.md",
    "xenia-canary/01-initialization-and-command-processor.md",
    "xenia-canary/02-register-state-and-draw.md",
    "xenia-canary/03-shader-pipeline.md",
    "xenia-canary/04-textures-vertex-fetch-and-samplers.md",
    "xenia-canary/05-render-targets-edram-resolves.md",
    "xenia-canary/06-pipeline-backends-and-caches.md",
    "xenia-canary/07-resources-memory-and-synchronization.md",
    "xenia-canary/08-presentation-errors-and-configuration.md",
    "evidence/canary-source-inventory.json",
    "evidence/canary-subsystem-map.json",
    "g1.5b-completion.md",
)

CONFIDENCE = ("CONFIRMED", "PROBABLE", "UNKNOWN", "NOT APPLICABLE")
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
CANARY_SOURCE_LOCATOR_RE = re.compile(
    r"\x60(src/xenia/[^\s\x60:]+)(?::([A-Za-z_][A-Za-z0-9_:]*))?\x60"
)


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
    all_of = node.get("allOf")
    if isinstance(all_of, list):
        for index, child_schema in enumerate(all_of):
            if isinstance(child_schema, dict):
                validate_schema_node(
                    instance,
                    child_schema,
                    root_schema,
                    f"{location}.allOf[{index}]",
                    validation,
                )

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
            recorded_commit = symbol.get("commit")
            path = symbol.get("path")
            name = symbol.get("symbol")
            if repo is None or commit is None or not isinstance(path, str) or not isinstance(name, str):
                validation.error(f"invalid symbol locator in subsystem {identifier}: {symbol!r}")
                continue
            if recorded_commit is not None and recorded_commit != commit:
                validation.error(
                    f"symbol commit mismatch in subsystem {identifier}: "
                    f"recorded {recorded_commit!r}, expected {commit!r}"
                )
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

    for branch in subsystem_map.get("configuration_branches", []):
        path = branch.get("path")
        symbol = branch.get("symbol")
        repo = roots.get("canary")
        commit = commits.get("canary")
        if (
            repo is None
            or commit is None
            or not isinstance(path, str)
            or not isinstance(symbol, str)
        ):
            validation.error(f"invalid configuration branch locator: {branch!r}")
            continue
        source = git_text(repo, "show", f"{commit}:{path}")
        if source is None:
            validation.error(f"missing configuration source canary:{path}")
        elif symbol not in source:
            validation.error(
                f"missing configuration symbol {symbol!r} in canary:{path}"
            )


def validate_canary_repository(
    inventory: dict[str, Any],
    canary_override: Path | None,
    validation: Validation,
) -> tuple[dict[str, Path], dict[str, str]]:
    fable_entry = inventory.get("fable_repository")
    if not isinstance(fable_entry, dict):
        validation.error("Canary inventory fable_repository is not an object")
    else:
        fable_commit = fable_entry.get("commit")
        if not isinstance(fable_commit, str):
            validation.error("Canary inventory Fable start commit is not recorded")
        elif run_git(ROOT, "cat-file", "-e", f"{fable_commit}^{{commit}}").returncode != 0:
            validation.error(
                f"Canary inventory Fable start commit is unavailable: {fable_commit}"
            )
        else:
            actual_fable_tree = git_text(ROOT, "rev-parse", f"{fable_commit}^{{tree}}")
            if actual_fable_tree != fable_entry.get("tree"):
                validation.error(
                    "Canary inventory Fable start tree mismatch: "
                    f"recorded {fable_entry.get('tree')!r}, "
                    f"actual {actual_fable_tree!r}"
                )

    entry = inventory.get("canary_repository")
    if not isinstance(entry, dict):
        validation.error("canary_repository is not an object")
        return {}, {}

    repo = (
        canary_override.resolve()
        if canary_override is not None
        else Path(str(entry.get("path", "")))
    )
    commit = entry.get("commit")
    if not repo.is_dir():
        validation.error(f"canary repository is unavailable: {repo}")
        return {}, {}
    if not isinstance(commit, str):
        validation.error("canary repository commit is not recorded")
        return {}, {}
    if run_git(repo, "cat-file", "-e", f"{commit}^{{commit}}").returncode != 0:
        validation.error(f"canary commit is unavailable in {repo}: {commit}")
        return {}, {}

    exact_checks = (
        ("HEAD", git_text(repo, "rev-parse", "HEAD"), commit),
        ("tree", git_text(repo, "rev-parse", "HEAD^{tree}"), entry.get("tree")),
        ("branch", git_text(repo, "branch", "--show-current"), entry.get("branch")),
        (
            "upstream",
            git_text(
                repo,
                "rev-parse",
                "--abbrev-ref",
                "--symbolic-full-name",
                "@{upstream}",
            ),
            entry.get("upstream"),
        ),
        ("remote", git_text(repo, "remote", "get-url", "origin"), entry.get("remote")),
        ("parent", git_text(repo, "rev-parse", "HEAD^"), entry.get("parent")),
        ("author date", git_text(repo, "show", "-s", "--format=%aI", "HEAD"), entry.get("author_date")),
        (
            "committer date",
            git_text(repo, "show", "-s", "--format=%cI", "HEAD"),
            entry.get("committer_date"),
        ),
        ("subject", git_text(repo, "show", "-s", "--format=%s", "HEAD"), entry.get("subject")),
    )
    for label, actual, expected in exact_checks:
        if actual != expected:
            validation.error(
                f"canary {label} mismatch: recorded {expected!r}, actual {actual!r}"
            )

    left_right = git_text(repo, "rev-list", "--left-right", "--count", "HEAD...@{upstream}")
    if left_right is None:
        validation.error("unable to calculate canary upstream ahead/behind counts")
    else:
        parts = left_right.split()
        actual_ahead = int(parts[0]) if len(parts) == 2 else None
        actual_behind = int(parts[1]) if len(parts) == 2 else None
        if actual_ahead != entry.get("ahead") or actual_behind != entry.get("behind"):
            validation.error(
                "canary upstream relationship mismatch: "
                f"recorded ahead/behind {entry.get('ahead')!r}/{entry.get('behind')!r}, "
                f"actual {actual_ahead!r}/{actual_behind!r}"
            )

    status = git_text(repo, "status", "--short", "--untracked-files=all")
    if status != "":
        validation.error(f"canary worktree is not clean: {status!r}")

    shallow_text = git_text(repo, "rev-parse", "--is-shallow-repository")
    actual_shallow = shallow_text == "true"
    if actual_shallow != entry.get("is_shallow"):
        validation.error(
            f"canary shallow state mismatch: recorded {entry.get('is_shallow')!r}, "
            f"actual {actual_shallow!r}"
        )

    commit_count_text = git_text(repo, "rev-list", "--count", "HEAD")
    commit_count = int(commit_count_text) if commit_count_text is not None else None
    if commit_count != entry.get("available_commit_count"):
        validation.error(
            f"canary commit count mismatch: recorded {entry.get('available_commit_count')!r}, "
            f"actual {commit_count!r}"
        )

    shallow_path_text = git_text(repo, "rev-parse", "--git-path", "shallow")
    if actual_shallow and shallow_path_text is not None:
        shallow_path = Path(shallow_path_text)
        if not shallow_path.is_absolute():
            shallow_path = repo / shallow_path
        try:
            boundaries = {
                line.strip()
                for line in shallow_path.read_text(encoding="ascii").splitlines()
                if line.strip()
            }
        except OSError as exc:
            validation.error(f"unable to read canary shallow boundary file: {exc}")
        else:
            if entry.get("shallow_boundary") not in boundaries:
                validation.error(
                    "recorded canary shallow boundary is not present: "
                    f"{entry.get('shallow_boundary')!r}"
                )

    license_path = repo / "LICENSE"
    if not license_path.is_file():
        validation.error(f"canary LICENSE is unavailable: {license_path}")
    elif sha256(license_path) != entry.get("license_sha256"):
        validation.error(
            "canary LICENSE hash mismatch: "
            f"recorded {entry.get('license_sha256')!r}, actual {sha256(license_path)!r}"
        )

    for history in inventory.get("history_evidence", []):
        history_commit = history.get("commit")
        if not isinstance(history_commit, str):
            validation.error(f"invalid canary history commit: {history!r}")
            continue
        if run_git(repo, "cat-file", "-e", f"{history_commit}^{{commit}}").returncode != 0:
            validation.error(f"canary history commit is unavailable: {history_commit}")
            continue
        actual_date = git_text(repo, "show", "-s", "--format=%aI", history_commit)
        actual_subject = git_text(repo, "show", "-s", "--format=%s", history_commit)
        if actual_date != history.get("date"):
            validation.error(
                f"canary history date mismatch {history_commit}: "
                f"recorded {history.get('date')!r}, actual {actual_date!r}"
            )
        if actual_subject != history.get("subject"):
            validation.error(
                f"canary history subject mismatch {history_commit}: "
                f"recorded {history.get('subject')!r}, actual {actual_subject!r}"
            )

    static_counts = inventory.get("static_counts", {})
    if isinstance(static_counts, dict):
        key_file_count = len(inventory.get("key_files", []))
        if static_counts.get("key_files") != key_file_count:
            validation.error(
                f"canary key-file count mismatch: recorded "
                f"{static_counts.get('key_files')!r}, actual {key_file_count}"
            )
        history_count = len(inventory.get("history_evidence", []))
        if static_counts.get("history_commits") != history_count:
            validation.error(
                f"canary history count mismatch: recorded "
                f"{static_counts.get('history_commits')!r}, actual {history_count}"
            )

    return {"canary": repo}, {"canary": commit}


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


def validate_canary_markdown_locators(
    repo: Path, commit: str, validation: Validation
) -> None:
    markdown_paths = [
        DOC_ROOT / "02-xenia-canary-overview.md",
        DOC_ROOT / "g1.5b-completion.md",
    ]
    markdown_paths.extend(sorted((DOC_ROOT / "xenia-canary").glob("*.md")))
    for markdown in markdown_paths:
        if not markdown.is_file():
            continue
        contents = markdown.read_text(encoding="utf-8")
        for match in CANARY_SOURCE_LOCATOR_RE.finditer(contents):
            path, symbol = match.groups()
            if run_git(repo, "cat-file", "-e", f"{commit}:{path}").returncode != 0:
                validation.error(
                    f"missing Canary source path in {markdown.relative_to(ROOT)}: {path}"
                )
                continue
            if symbol is None:
                continue
            source = git_text(repo, "show", f"{commit}:{path}")
            if source is None or symbol not in source:
                validation.error(
                    f"missing Canary source symbol in {markdown.relative_to(ROOT)}: "
                    f"{path}:{symbol}"
                )


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
    parser.add_argument(
        "--canary-root",
        type=Path,
        help="Override the pinned local Xenia Canary clone used for Git verification",
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
    canary_inventory = load_json(CANARY_INVENTORY_PATH, validation)
    canary_map = load_json(CANARY_MAP_PATH, validation)
    canary_inventory_schema = load_json(CANARY_INVENTORY_SCHEMA_PATH, validation)
    canary_map_schema = load_json(CANARY_MAP_SCHEMA_PATH, validation)
    if inventory and inventory_schema:
        validate_with_schema(inventory, inventory_schema, "source inventory", validation)
    if subsystem_map and map_schema:
        validate_with_schema(subsystem_map, map_schema, "subsystem map", validation)
    if canary_inventory and canary_inventory_schema:
        validate_with_schema(
            canary_inventory,
            canary_inventory_schema,
            "canary source inventory",
            validation,
        )
    if canary_map and canary_map_schema:
        validate_with_schema(canary_map, canary_map_schema, "canary subsystem map", validation)

    if inventory:
        roots, commits = repository_roots(inventory, args.sdk_root, validation)
        validate_source_inventory(inventory, roots, commits, validation)
        if subsystem_map:
            validate_subsystem_map(subsystem_map, roots, commits, validation)
        if args.verify_artifacts:
            validate_artifacts(inventory, validation)

    if canary_inventory:
        canary_roots, canary_commits = validate_canary_repository(
            canary_inventory, args.canary_root, validation
        )
        if canary_roots and canary_commits:
            validate_source_inventory(
                canary_inventory, canary_roots, canary_commits, validation
            )
            if canary_map:
                expected_canary_commit = canary_commits.get("canary")
                if canary_map.get("pinned_canary_commit") != expected_canary_commit:
                    validation.error(
                        "canary subsystem-map pin mismatch: "
                        f"recorded {canary_map.get('pinned_canary_commit')!r}, "
                        f"expected {expected_canary_commit!r}"
                    )
                validate_subsystem_map(
                    canary_map, canary_roots, canary_commits, validation
                )
            validate_canary_markdown_locators(
                canary_roots["canary"], canary_commits["canary"], validation
            )

    validate_markdown_links(validation)

    for warning in validation.warnings:
        print(f"WARNING: {warning}")
    for error in validation.errors:
        print(f"ERROR: {error}")
    if validation.errors:
        print(f"FAIL: {len(validation.errors)} error(s), {len(validation.warnings)} warning(s)")
        return 1
    print(
        f"PASS: G1.5A/G1.5B GPU reference validated "
        f"({len(validation.warnings)} warning(s))"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
