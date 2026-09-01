#!/usr/bin/env python3
"""Read-only validator for the Fable II G1.5A-D and G1.6A GPU reference corpus."""

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
DIVERGENCE_MATRIX_PATH = EVIDENCE_ROOT / "divergence-matrix.json"
DIVERGENCE_HISTORY_PATH = EVIDENCE_ROOT / "divergence-history.json"
DIVERGENCE_MATRIX_SCHEMA_PATH = (
    SCHEMA_ROOT / "fable2-gpu-divergence-matrix-v1.schema.json"
)
DIVERGENCE_HISTORY_SCHEMA_PATH = (
    SCHEMA_ROOT / "fable2-gpu-divergence-history-v1.schema.json"
)
FABLE_RELEVANCE_PATH = EVIDENCE_ROOT / "fable2-relevance-matrix.json"
BOUNDARY_ASSESSMENT_PATH = EVIDENCE_ROOT / "boundary-assessment.json"
REPLACEMENT_SEAMS_PATH = EVIDENCE_ROOT / "replacement-seams.json"
EXPERIMENT_BACKLOG_PATH = EVIDENCE_ROOT / "experiment-backlog.json"
G2A_DECISION_PATH = EVIDENCE_ROOT / "g2a-decision.json"
FABLE_RELEVANCE_SCHEMA_PATH = (
    SCHEMA_ROOT / "fable2-gpu-fable-relevance-v1.schema.json"
)
BOUNDARY_ASSESSMENT_SCHEMA_PATH = (
    SCHEMA_ROOT / "fable2-gpu-boundary-assessment-v1.schema.json"
)
REPLACEMENT_SEAMS_SCHEMA_PATH = (
    SCHEMA_ROOT / "fable2-gpu-replacement-seams-v1.schema.json"
)
EXPERIMENT_BACKLOG_SCHEMA_PATH = (
    SCHEMA_ROOT / "fable2-gpu-experiment-backlog-v1.schema.json"
)
G2A_DECISION_SCHEMA_PATH = (
    SCHEMA_ROOT / "fable2-gpu-g2a-decision-v1.schema.json"
)
G1_CANDIDATE_PATH = ROOT / "docs" / "fable2-native-renderer" / "candidate-hook-inventory.json"
STATIC_XDK_PATH = EVIDENCE_ROOT / "static-xdk-method-inventory.json"
STATIC_XDK_SCHEMA_PATH = (
    SCHEMA_ROOT / "fable2-gpu-static-xdk-method-inventory-v1.schema.json"
)
STATIC_XDK_REPORT_PATH = DOC_ROOT / "12-static-xdk-method-recovery.md"
STATIC_XDK_COMPLETION_PATH = DOC_ROOT / "g1.6a-completion.md"

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
    "03-rexglue-canary-divergence.md",
    "04-divergence-history-and-rationale.md",
    "05-accuracy-performance-architecture-classification.md",
    "evidence/divergence-matrix.json",
    "evidence/divergence-history.json",
    "g1.5c-completion.md",
    "06-fable2-relevance-assessment.md",
    "07-boundary-and-ownership-reassessment.md",
    "08-system-ui-and-presentation-contract.md",
    "09-evidence-gaps-and-experiment-plan.md",
    "10-custom-renderer-reference-architecture.md",
    "11-g2a-reentry-decision.md",
    "open-questions.md",
    "evidence/fable2-relevance-matrix.json",
    "evidence/boundary-assessment.json",
    "evidence/replacement-seams.json",
    "evidence/experiment-backlog.json",
    "evidence/g2a-decision.json",
    "g1.5d-completion.md",
    "12-static-xdk-method-recovery.md",
    "evidence/static-xdk-method-inventory.json",
    "g1.6a-completion.md",
)

CONFIDENCE = ("CONFIRMED", "PROBABLE", "UNKNOWN", "NOT APPLICABLE")
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
CANARY_SOURCE_LOCATOR_RE = re.compile(
    r"\x60(src/xenia/[^\s\x60:]+)(?::([A-Za-z_][A-Za-z0-9_:]*))?\x60"
)
RATIONALE_CONFIDENCE = (
    "CONFIRMED RATIONALE",
    "INFERRED RATIONALE",
    "RATIONALE UNKNOWN",
    "NOT APPLICABLE",
)
FABLE_RELEVANCE = (
    "CONFIRMED RELEVANT",
    "PROBABLE RELEVANT",
    "UNKNOWN FOR FABLE II",
    "NOT OBSERVED FOR FABLE II",
    "NOT APPLICABLE TO FABLE II",
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


def counted(values: list[str]) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        result[value] = result.get(value, 0) + 1
    return dict(sorted(result.items()))


def validate_record_locators(
    implementation: dict[str, Any],
    roots: dict[str, Path],
    commits: dict[str, str],
    label: str,
    validation: Validation,
) -> None:
    repository = implementation.get("repository")
    repo = roots.get(repository)
    expected_commit = commits.get(repository)
    recorded_commit = implementation.get("commit")
    if repo is None or expected_commit is None:
        validation.error(f"{label}: unknown repository {repository!r}")
        return
    if recorded_commit != expected_commit:
        validation.error(
            f"{label}: commit mismatch: recorded {recorded_commit!r}, "
            f"expected {expected_commit!r}"
        )
        return
    for locator in implementation.get("paths", []):
        path = locator.get("path")
        if not isinstance(path, str):
            validation.error(f"{label}: invalid source path {path!r}")
            continue
        source = git_text(repo, "show", f"{expected_commit}:{path}")
        if source is None:
            validation.error(f"{label}: missing source {repository}:{path}")
            continue
        for symbol in locator.get("symbols", []):
            if symbol not in source:
                validation.error(
                    f"{label}: missing symbol {symbol!r} in {repository}:{path}"
                )


def validate_divergence_evidence(
    matrix: dict[str, Any],
    history: dict[str, Any],
    roots: dict[str, Path],
    commits: dict[str, str],
    validation: Validation,
) -> None:
    records = matrix.get("records", [])
    if not isinstance(records, list):
        validation.error("divergence matrix records is not an array")
        return
    record_ids = [record.get("record_id") for record in records]
    if record_ids != sorted(record_ids):
        validation.error("divergence matrix records are not sorted by record_id")
    if len(record_ids) != len(set(record_ids)):
        validation.error("divergence matrix contains duplicate record_id values")
    record_id_set = set(record_ids)

    pin_names = {
        "fable_repository": "fable2",
        "rexglue_repository": "rexglue",
        "canary_repository": "canary",
    }
    for pin_key, repository in pin_names.items():
        pin = matrix.get("pins", {}).get(pin_key, {})
        repo = roots.get(repository)
        baseline_commit = commits.get(repository)
        recorded_commit = pin.get("commit") if isinstance(pin, dict) else None
        expected_commit = (
            recorded_commit if repository == "fable2" else baseline_commit
        )
        if (
            not isinstance(pin, dict)
            or repo is None
            or not isinstance(expected_commit, str)
        ):
            validation.error(f"invalid divergence pin {pin_key}")
            continue
        if repository != "fable2" and recorded_commit != expected_commit:
            validation.error(
                f"divergence pin mismatch {pin_key}: recorded {recorded_commit!r}, "
                f"expected {expected_commit!r}"
            )
        if run_git(repo, "cat-file", "-e", f"{expected_commit}^{{commit}}").returncode != 0:
            validation.error(f"divergence pin {pin_key} is unavailable: {expected_commit}")
            continue
        actual_tree = git_text(repo, "rev-parse", f"{expected_commit}^{{tree}}")
        if pin.get("tree") != actual_tree:
            validation.error(
                f"divergence tree mismatch {pin_key}: recorded {pin.get('tree')!r}, "
                f"actual {actual_tree!r}"
            )

    for record in records:
        record_id = record.get("record_id")
        label = f"divergence record {record_id}"
        validate_record_locators(record.get("rexglue", {}), roots, commits, label, validation)
        validate_record_locators(record.get("canary", {}), roots, commits, label, validation)
        direction = record.get("direction")
        divergences = record.get("material_divergences", [])
        if direction == "SAME BEHAVIOUR, DIFFERENT STRUCTURE" and divergences:
            validation.error(f"{label}: equivalence record has material divergences")
        if direction != "SAME BEHAVIOUR, DIFFERENT STRUCTURE" and not divergences:
            validation.error(f"{label}: non-equivalence record lacks a material divergence")
        if record.get("rationale_confidence") not in RATIONALE_CONFIDENCE:
            validation.error(f"{label}: invalid rationale confidence")
        preliminary_fable = record.get("preliminary_fable", {})
        if preliminary_fable.get("relevance") not in FABLE_RELEVANCE:
            validation.error(f"{label}: invalid preliminary Fable relevance")

    expected_matrix_counts = {
        "records": len(records),
        "by_direction": counted([str(record.get("direction")) for record in records]),
        "by_primary_classification": counted(
            [str(record.get("classification", {}).get("primary")) for record in records]
        ),
        "by_source_confidence": counted(
            [str(record.get("source_confidence")) for record in records]
        ),
        "by_rationale_confidence": counted(
            [str(record.get("rationale_confidence")) for record in records]
        ),
        "by_fable_relevance": counted(
            [str(record.get("preliminary_fable", {}).get("relevance")) for record in records]
        ),
    }
    if matrix.get("counts") != expected_matrix_counts:
        validation.error(
            "divergence matrix counts mismatch: "
            f"recorded {matrix.get('counts')!r}, expected {expected_matrix_counts!r}"
        )

    history_records = history.get("history_records", [])
    if not isinstance(history_records, list):
        validation.error("divergence history records is not an array")
        return
    history_ids = [entry.get("history_id") for entry in history_records]
    if history_ids != sorted(history_ids):
        validation.error("divergence history records are not sorted by history_id")
    if len(history_ids) != len(set(history_ids)):
        validation.error("divergence history contains duplicate history_id values")
    history_by_id = {entry.get("history_id"): entry for entry in history_records}

    for record in records:
        record_id = record.get("record_id")
        for history_id in record.get("historical_provenance", {}).get("history_ids", []):
            history_entry = history_by_id.get(history_id)
            if history_entry is None:
                validation.error(
                    f"divergence record {record_id}: unknown history_id {history_id!r}"
                )
            elif record_id not in history_entry.get("affected_record_ids", []):
                validation.error(
                    f"divergence record {record_id}: history {history_id} lacks reciprocal link"
                )

    for entry in history_records:
        history_id = entry.get("history_id")
        repository = entry.get("repository")
        repo = roots.get(repository)
        pinned_commit = commits.get(repository)
        commit = entry.get("commit")
        if repo is None or pinned_commit is None or not isinstance(commit, str):
            validation.error(f"history {history_id}: invalid repository or commit")
            continue
        if run_git(repo, "cat-file", "-e", f"{commit}^{{commit}}").returncode != 0:
            validation.error(f"history {history_id}: unavailable commit {commit}")
            continue
        if run_git(repo, "merge-base", "--is-ancestor", commit, pinned_commit).returncode != 0:
            validation.error(f"history {history_id}: commit is not an ancestor of the pin")
        actual_parent = git_text(repo, "rev-parse", f"{commit}^")
        if entry.get("parent") != actual_parent:
            validation.error(
                f"history {history_id}: parent mismatch: recorded {entry.get('parent')!r}, "
                f"actual {actual_parent!r}"
            )
        if entry.get("provenance_kind") == "COMMIT":
            metadata_checks = (
                ("author_date", git_text(repo, "show", "-s", "--format=%aI", commit)),
                ("author", git_text(repo, "show", "-s", "--format=%an", commit)),
                ("subject", git_text(repo, "show", "-s", "--format=%s", commit)),
            )
            for field, actual in metadata_checks:
                if entry.get(field) != actual:
                    validation.error(
                        f"history {history_id}: {field} mismatch: "
                        f"recorded {entry.get(field)!r}, actual {actual!r}"
                    )
        primary_url = entry.get("primary_url")
        if not isinstance(primary_url, str) or commit not in primary_url:
            validation.error(f"history {history_id}: primary URL is not commit-pinned")
        implementation = {
            "repository": repository,
            "commit": pinned_commit,
            "paths": entry.get("locators", []),
        }
        validate_record_locators(implementation, roots, commits, f"history {history_id}", validation)
        for record_id in entry.get("affected_record_ids", []):
            if record_id not in record_id_set:
                validation.error(
                    f"history {history_id}: unknown affected record {record_id!r}"
                )

    expected_history_counts = {
        "records": len(history_records),
        "by_repository": counted(
            [str(entry.get("repository")) for entry in history_records]
        ),
        "by_provenance_kind": counted(
            [str(entry.get("provenance_kind")) for entry in history_records]
        ),
        "by_rationale_confidence": counted(
            [str(entry.get("rationale_confidence")) for entry in history_records]
        ),
    }
    if history.get("counts") != expected_history_counts:
        validation.error(
            "divergence history counts mismatch: "
            f"recorded {history.get('counts')!r}, expected {expected_history_counts!r}"
        )

    prose = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            DOC_ROOT / "03-rexglue-canary-divergence.md",
            DOC_ROOT / "05-accuracy-performance-architecture-classification.md",
        )
        if path.is_file()
    )
    for record_id in record_ids:
        if isinstance(record_id, str) and record_id not in prose:
            validation.error(f"divergence record {record_id} is absent from G1.5C prose")
    record_prefixes = sorted(
        {
            str(record_id).split("-", 1)[0]
            for record_id in record_ids
            if isinstance(record_id, str) and "-" in record_id
        }
    )
    prose_record_ids = set(
        re.findall(
            rf"\b(?:{'|'.join(re.escape(prefix) for prefix in record_prefixes)})-[0-9]{{3}}\b",
            prose,
        )
    )
    for record_id in sorted(prose_record_ids - record_id_set):
        validation.error(f"G1.5C prose references unknown divergence record {record_id}")

    history_prose_path = DOC_ROOT / "04-divergence-history-and-rationale.md"
    history_prose = (
        history_prose_path.read_text(encoding="utf-8")
        if history_prose_path.is_file()
        else ""
    )
    for history_id in history_ids:
        if isinstance(history_id, str) and history_id not in history_prose:
            validation.error(f"history record {history_id} is absent from G1.5C prose")
    prose_history_ids = set(
        re.findall(r"\b(?:CAN|REX)-(?:[0-9a-f]{8}|source-[a-z0-9-]+)\b", history_prose)
    )
    for history_id in sorted(prose_history_ids - set(history_ids)):
        validation.error(f"G1.5C prose references unknown history record {history_id}")


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
        DOC_ROOT / "03-rexglue-canary-divergence.md",
        DOC_ROOT / "04-divergence-history-and-rationale.md",
        DOC_ROOT / "05-accuracy-performance-architecture-classification.md",
        DOC_ROOT / "g1.5c-completion.md",
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


def validate_g15d_artifacts(
    relevance: dict[str, Any], validation: Validation
) -> None:
    for artifact in relevance.get("fable_evidence", []):
        if artifact.get("status") not in ("IGNORED LOCAL", "EXTERNAL LOCAL"):
            continue
        path = Path(str(artifact.get("path", "")))
        if not path.is_absolute():
            path = ROOT / path
        if not path.is_file():
            validation.error(f"G1.5D cited local evidence is unavailable: {path}")
            continue
        expected_size = artifact.get("size")
        if expected_size is not None and path.stat().st_size != expected_size:
            validation.error(
                f"G1.5D evidence size mismatch {path}: "
                f"recorded {expected_size!r}, actual {path.stat().st_size!r}"
            )
        expected_hash = artifact.get("sha256")
        if isinstance(expected_hash, str):
            actual_hash = sha256(path)
            if actual_hash != expected_hash:
                validation.error(
                    f"G1.5D evidence hash mismatch {path}: "
                    f"recorded {expected_hash!r}, actual {actual_hash!r}"
                )


def validate_g15d_evidence(
    relevance: dict[str, Any],
    boundary_assessment: dict[str, Any],
    replacement_seams: dict[str, Any],
    experiment_backlog: dict[str, Any],
    g2a_decision: dict[str, Any],
    divergence_matrix: dict[str, Any],
    g1_candidates: dict[str, Any],
    validation: Validation,
) -> None:
    source_records = divergence_matrix.get("records", [])
    relevance_records = relevance.get("records", [])
    if not isinstance(source_records, list) or not isinstance(relevance_records, list):
        validation.error("G1.5D relevance records are unavailable")
        return

    source_by_id = {record.get("record_id"): record for record in source_records}
    relevance_ids = [record.get("record_id") for record in relevance_records]
    expected_ids = sorted(source_by_id)
    if relevance_ids != expected_ids:
        validation.error(
            "G1.5D relevance IDs must contain the 37 authoritative IDs once and sorted: "
            f"actual {relevance_ids!r}"
        )
    if len(relevance_ids) != 37 or len(set(relevance_ids)) != 37:
        validation.error("G1.5D relevance matrix must contain exactly 37 unique records")

    source_confidence_map = {
        "CONFIRMED": "CONFIRMED SOURCE",
        "PROBABLE": "PROBABLE SOURCE",
        "UNKNOWN": "UNKNOWN SOURCE",
        "NOT APPLICABLE": "NOT APPLICABLE",
    }
    evidence_ids = {
        entry.get("evidence_id") for entry in relevance.get("fable_evidence", [])
    }
    if None in evidence_ids or len(evidence_ids) != len(relevance.get("fable_evidence", [])):
        validation.error("G1.5D Fable evidence IDs are invalid or duplicated")

    record_boundary_refs: set[str] = set()
    record_experiment_refs: set[str] = set()
    record_open_question_refs: set[str] = set()
    for record in relevance_records:
        record_id = record.get("record_id")
        source_record = source_by_id.get(record_id)
        if source_record is None:
            continue
        identity = record.get("source_identity", {})
        expected_identity = {
            "direction": source_record.get("direction"),
            "rexglue": source_record.get("rexglue"),
            "canary": source_record.get("canary"),
            "material_divergences": source_record.get("material_divergences"),
            "historical_provenance": source_record.get("historical_provenance"),
        }
        if identity != expected_identity:
            validation.error(
                f"G1.5D relevance {record_id}: source identity/provenance changed"
            )
        expected_source_confidence = source_confidence_map.get(
            source_record.get("source_confidence")
        )
        if record.get("source_confidence") != expected_source_confidence:
            validation.error(
                f"G1.5D relevance {record_id}: source confidence mismatch"
            )
        for dimension in ("fable_reachability", "causal_relevance"):
            for evidence_id in record.get(dimension, {}).get("evidence_refs", []):
                if evidence_id not in evidence_ids:
                    validation.error(
                        f"G1.5D relevance {record_id}: unknown evidence ID {evidence_id!r}"
                    )
        causal = record.get("causal_relevance", {}).get("classification")
        if causal == "CAUSALLY CONFIRMED":
            validation.error(
                f"G1.5D relevance {record_id}: causal confirmation lacks an existing controlled A/B"
            )
        record_boundary_refs.update(record.get("later_observation_boundaries", []))
        record_experiment_refs.update(record.get("experiment_ids", []))
        record_open_question_refs.update(record.get("open_question_ids", []))

    expected_relevance_counts = {
        "records": len(relevance_records),
        "by_source_confidence": counted(
            [str(record.get("source_confidence")) for record in relevance_records]
        ),
        "by_fable_reachability": counted(
            [
                str(record.get("fable_reachability", {}).get("classification"))
                for record in relevance_records
            ]
        ),
        "by_causal_relevance": counted(
            [
                str(record.get("causal_relevance", {}).get("classification"))
                for record in relevance_records
            ]
        ),
        "by_applicability": counted(
            [
                str(value)
                for record in relevance_records
                for value in record.get("applicability", [])
            ]
        ),
    }
    if relevance.get("counts") != expected_relevance_counts:
        validation.error(
            "G1.5D relevance counts mismatch: "
            f"recorded {relevance.get('counts')!r}, "
            f"expected {expected_relevance_counts!r}"
        )

    ladder = relevance.get("evidence_ladder", [])
    ladder_levels = [entry.get("level") for entry in ladder]
    ladder_status = [entry.get("status") for entry in ladder]
    if ladder_levels != ["L0", "L1", "L2", "L3", "L4", "L5"]:
        validation.error(f"G1.5D evidence ladder is invalid: {ladder_levels!r}")
    if ladder_status != [
        "REACHED",
        "REACHED",
        "NOT REACHED",
        "NOT REACHED",
        "NOT REACHED",
        "NOT REACHED",
    ]:
        validation.error(
            "G1.5D existing evidence must not be promoted beyond L1"
        )

    boundaries = boundary_assessment.get("boundaries", [])
    boundary_ids = [entry.get("boundary_id") for entry in boundaries]
    if len(boundary_ids) != 29 or len(set(boundary_ids)) != 29:
        validation.error("G1.5D boundary assessment must contain 29 unique boundaries")
    boundary_id_set = set(boundary_ids)
    if not record_boundary_refs.issubset(boundary_id_set):
        validation.error(
            "G1.5D relevance references unknown boundaries: "
            f"{sorted(record_boundary_refs - boundary_id_set)!r}"
        )

    expected_g1_addresses = {
        candidate.get("guest_address") for candidate in g1_candidates.get("candidates", [])
    }
    actual_g1_addresses = [
        entry.get("g1_candidate_address")
        for entry in boundaries
        if entry.get("origin") == "G1_CANDIDATE"
    ]
    if (
        len(actual_g1_addresses) != 11
        or len(set(actual_g1_addresses)) != 11
        or set(actual_g1_addresses) != expected_g1_addresses
    ):
        validation.error(
            "G1.5D boundary assessment must contain every G1 candidate exactly once"
        )

    expected_observation_symbols = {
        "VdSwap_entry",
        "CommandProcessor::ExecutePacketType3",
        "D3D12CommandProcessor::WriteRegister",
        "D3D12CommandProcessor::IssueDraw",
        "PrimitiveProcessor::Process",
        "PipelineCache::LoadShader",
        "Shader::AnalyzeUcode",
        "PipelineCache::ConfigurePipeline",
        "D3D12CommandProcessor::UpdateBindings",
        "D3D12TextureCache::RequestTextures",
        "D3D12RenderTargetCache::Update",
        "draw_util::GetResolveInfo",
        "D3D12RenderTargetCache::Resolve",
        "SharedMemory::RequestRanges",
        "SharedMemory::RangeWrittenByGpu",
        "D3D12CommandProcessor::EndSubmission",
        "Presenter::RefreshGuestOutput",
        "D3D12Presenter::PaintAndPresentImpl",
    }
    observation_symbols = [
        entry.get("exact_address_or_symbol")
        for entry in boundaries
        if entry.get("origin") == "REXGLUE_OBSERVATION"
    ]
    if (
        len(observation_symbols) != 18
        or len(set(observation_symbols)) != 18
        or set(observation_symbols) != expected_observation_symbols
    ):
        validation.error(
            "G1.5D boundary assessment must contain every required ReXGlue "
            "observation surface exactly once"
        )
    rexglue_pin = relevance.get("pins", {}).get("rexglue_repository", {})
    rexglue_path = Path(str(rexglue_pin.get("path", "")))
    rexglue_commit = rexglue_pin.get("commit")
    if not rexglue_path.is_dir() or not isinstance(rexglue_commit, str):
        validation.error("G1.5D ReXGlue boundary source pin is unavailable")
    else:
        for entry in boundaries:
            if entry.get("origin") != "REXGLUE_OBSERVATION":
                continue
            source_path = entry.get("source_location")
            symbol = entry.get("exact_address_or_symbol")
            if not isinstance(source_path, str) or not isinstance(symbol, str):
                validation.error(
                    f"G1.5D boundary has invalid source locator: {entry!r}"
                )
                continue
            source = git_text(
                rexglue_path, "show", f"{rexglue_commit}:{source_path}"
            )
            if source is None:
                validation.error(
                    f"G1.5D boundary {entry.get('boundary_id')}: "
                    f"missing ReXGlue source {source_path}"
                )
            elif symbol not in source:
                validation.error(
                    f"G1.5D boundary {entry.get('boundary_id')}: "
                    f"missing symbol {symbol!r} in {source_path}"
                )

    expected_boundary_counts = {
        "boundaries": len(boundaries),
        "g1_candidate_hooks": len(actual_g1_addresses),
        "rexglue_observation_surfaces": len(observation_symbols),
        "by_disposition": counted(
            [str(entry.get("stage_disposition")) for entry in boundaries]
        ),
    }
    if boundary_assessment.get("counts") != expected_boundary_counts:
        validation.error(
            "G1.5D boundary counts mismatch: "
            f"recorded {boundary_assessment.get('counts')!r}, "
            f"expected {expected_boundary_counts!r}"
        )

    stages = replacement_seams.get("stages", [])
    if [stage.get("stage_id") for stage in stages] != [
        "STAGE-A",
        "STAGE-B",
        "STAGE-C",
    ]:
        validation.error("G1.5D ownership stages must be A, B and C in order")
    if replacement_seams.get("ownership_transition_conclusion", {}).get(
        "classification"
    ) != "MORE EVIDENCE REQUIRED":
        validation.error(
            "G1.5D must not claim a proved incremental ownership transition"
        )

    experiments = experiment_backlog.get("experiments", [])
    experiment_ids = [entry.get("experiment_id") for entry in experiments]
    if len(experiment_ids) != len(set(experiment_ids)):
        validation.error("G1.5D experiment IDs are duplicated")
    experiment_id_set = set(experiment_ids)
    orders = [entry.get("order") for entry in experiments]
    if orders != list(range(1, len(experiments) + 1)):
        validation.error(
            f"G1.5D experiments are not in dependency order: {orders!r}"
        )
    experiment_order = {
        entry.get("experiment_id"): entry.get("order") for entry in experiments
    }
    for experiment in experiments:
        experiment_id = experiment.get("experiment_id")
        for dependency in experiment.get("dependencies", []):
            if dependency not in experiment_id_set:
                validation.error(
                    f"G1.5D experiment {experiment_id}: unknown dependency {dependency!r}"
                )
            elif experiment_order[dependency] >= experiment.get("order"):
                validation.error(
                    f"G1.5D experiment {experiment_id}: dependency {dependency!r} "
                    "does not precede it"
                )
    all_experiment_refs = set(record_experiment_refs)
    for entry in boundaries:
        all_experiment_refs.update(entry.get("experiment_ids", []))
    for entry in relevance.get("evidence_ladder", []):
        all_experiment_refs.update(entry.get("experiment_ids", []))
    all_experiment_refs.update(
        g2a_decision.get("part_a", {}).get("experiment_ids", [])
    )
    first_experiment = g2a_decision.get("part_b", {}).get("first_experiment_id")
    if isinstance(first_experiment, str):
        all_experiment_refs.add(first_experiment)
    if not all_experiment_refs.issubset(experiment_id_set):
        validation.error(
            "G1.5D evidence references unknown experiments: "
            f"{sorted(all_experiment_refs - experiment_id_set)!r}"
        )
    expected_experiment_counts = {
        "experiments": len(experiments),
        "by_type": counted([str(entry.get("type")) for entry in experiments]),
        "by_estimated_evidence_level": counted(
            [str(entry.get("estimated_evidence_level")) for entry in experiments]
        ),
    }
    if experiment_backlog.get("counts") != expected_experiment_counts:
        validation.error(
            "G1.5D experiment counts mismatch: "
            f"recorded {experiment_backlog.get('counts')!r}, "
            f"expected {expected_experiment_counts!r}"
        )

    if g2a_decision.get("part_a", {}).get("decision") != (
        "REVISE G2A BEFORE RESUMING"
    ):
        validation.error("G1.5D Part A decision changed")
    if g2a_decision.get("part_b", {}).get("decision") != (
        "STATIC XDK METHOD RECOVERY"
    ):
        validation.error("G1.5D Part B decision changed")
    if g2a_decision.get("part_b", {}).get("timing_relative_to_part_a") != (
        "INDEPENDENTLY"
    ):
        validation.error("G1.5D Part B relationship to Part A changed")

    replacement_open_questions = {
        question_id
        for seam in replacement_seams.get("seam_decisions", [])
        for question_id in seam.get("open_question_ids", [])
    }
    all_open_question_refs = record_open_question_refs | replacement_open_questions
    open_questions_path = DOC_ROOT / "open-questions.md"
    open_question_text = (
        open_questions_path.read_text(encoding="utf-8")
        if open_questions_path.is_file()
        else ""
    )
    open_question_ids = set(re.findall(r"\bOQ-[A-Z0-9-]+\b", open_question_text))
    if not all_open_question_refs.issubset(open_question_ids):
        validation.error(
            "G1.5D evidence references undocumented open questions: "
            f"{sorted(all_open_question_refs - open_question_ids)!r}"
        )

    prose_checks = (
        ("06-fable2-relevance-assessment.md", relevance_ids),
        ("07-boundary-and-ownership-reassessment.md", boundary_ids),
        ("09-evidence-gaps-and-experiment-plan.md", experiment_ids),
    )
    for relative_path, stable_ids in prose_checks:
        path = DOC_ROOT / relative_path
        contents = path.read_text(encoding="utf-8") if path.is_file() else ""
        for stable_id in stable_ids:
            if isinstance(stable_id, str) and stable_id not in contents:
                validation.error(
                    f"G1.5D stable ID {stable_id} is absent from {relative_path}"
                )

    pin_checks = (
        (
            ROOT,
            relevance.get("pins", {}).get("g1", {}),
            "G1.5D G1 pin",
        ),
        (
            ROOT,
            relevance.get("pins", {}).get("paused_g2a", {}),
            "G1.5D paused G2A pin",
        ),
    )
    for repo, pin, label in pin_checks:
        commit = pin.get("commit")
        if not isinstance(commit, str):
            validation.error(f"{label} has no commit")
            continue
        if run_git(repo, "cat-file", "-e", f"{commit}^{{commit}}").returncode != 0:
            validation.error(f"{label} commit is unavailable: {commit}")
            continue
        actual_tree = git_text(repo, "rev-parse", f"{commit}^{{tree}}")
        if actual_tree != pin.get("tree"):
            validation.error(
                f"{label} tree mismatch: recorded {pin.get('tree')!r}, "
                f"actual {actual_tree!r}"
            )


def validate_g16a_evidence(
    inventory: dict[str, Any],
    sdk_override: Path | None,
    canary_override: Path | None,
    verify_artifacts: bool,
    validation: Validation,
) -> None:
    expected_loaded_image = (
        "BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00"
    )
    expected_classifications = [
        "QUALIFIED REPRESENTATIVE METHOD",
        "STRONG STATIC CANDIDATE",
        "DISCOVERY LEAD ONLY",
        "REJECTED AS SEMANTIC SEAM",
        "RECOVERY BLOCKED",
    ]
    expected_candidates = {
        "SXDK-001": (
            "sub_82BA77D0",
            "0x82BA77D0",
            "0x82BA7894",
            "0xC4",
            49,
            "QUALIFIED REPRESENTATIVE METHOD",
            "generated/default/fable2_recomp.110.cpp",
            1035313,
            "4168294DC783D211919D0D178732E50A8014CF8E750187BF66491437E7473C10",
            20979,
            21103,
        ),
        "SXDK-002": (
            "sub_82BA7B28",
            "0x82BA7B28",
            "0x82BA83C0",
            "0x898",
            550,
            "STRONG STATIC CANDIDATE",
            "generated/default/fable2_recomp.265.cpp",
            1023903,
            "4928C6367157ACD1B414E0A2709FB2F10FC5F105E1C977641C5D9FC185ADC5B0",
            21165,
            22453,
        ),
        "SXDK-003": (
            "sub_82BA8928",
            "0x82BA8928",
            "0x82BA8D2C",
            "0x404",
            257,
            "STRONG STATIC CANDIDATE",
            "generated/default/fable2_recomp.130.cpp",
            1024438,
            "0A6CD19DD979846B81C967F81DE1FD317983968F37E1235F0FA7E1B5DB00A625",
            21039,
            21616,
        ),
        "SXDK-004": (
            "sub_82AAC208",
            "0x82AAC208",
            "0x82AAC54C",
            "0x344",
            209,
            "DISCOVERY LEAD ONLY",
            "generated/default/fable2_recomp.85.cpp",
            1056093,
            "44D379173BD4C2D525FF55F90BDD9A33E3F3D30FFEAF5A2942EDA82077EC9F3C",
            18657,
            19135,
        ),
        "SXDK-005": (
            "sub_82BA34D8",
            "0x82BA34D8",
            "0x82BA3BFC",
            "0x724",
            457,
            "REJECTED AS SEMANTIC SEAM",
            "generated/default/fable2_recomp.22.cpp",
            1023789,
            "4714D7C3B08CBB01F0E9A41D087E2E1033ABECC3C11AA773940AC14F377D38F3",
            21478,
            22516,
        ),
        "SXDK-006": (
            "sub_82BA6990",
            "0x82BA6990",
            "0x82BA6C18",
            "0x288",
            162,
            "REJECTED AS SEMANTIC SEAM",
            "generated/default/fable2_recomp.161.cpp",
            1024073,
            "61E087C55D11D54F92D83356DD2C8AD8BBE45082846167C57A9F20866CCAD10B",
            21718,
            22093,
        ),
    }

    if inventory.get("primary_result") != "STATIC SEAM QUALIFIED":
        validation.error("G1.6A primary result must be STATIC SEAM QUALIFIED")
    if inventory.get("strongest_candidate_id") != "SXDK-001":
        validation.error("G1.6A strongest candidate must be SXDK-001")
    if inventory.get("classifications") != expected_classifications:
        validation.error("G1.6A classification vocabulary or order changed")

    pins = inventory.get("pins", {})
    expected_pin_fields = {
        ("fable_start", "branch"): "fable2-native-renderer-g1.5-reference",
        ("fable_start", "commit"): "78c5d66807abf19f67966bd0c3d8301c29990ae4",
        ("fable_start", "tree"): "e1881f9de89824feb051b58300374c924747605b",
        (
            "fable_start",
            "working_branch",
        ): "fable2-native-renderer-g1.6a-static-xdk-recovery",
        ("g1_accepted_base", "commit"): "c44e8c16f4422f9a828caf30899ac989170b8a8c",
        (
            "paused_g2a",
            "commit",
        ): "47c2ea2b7d9e14b09fd942c4b5f1bd11c46e2f51",
        ("paused_g2a", "tree"): "910e80108c2d9e7d8474866506f1c9e23ede601c",
        ("tu1", "loaded_image_sha256"): expected_loaded_image,
        ("tu1", "loaded_image_base"): "0x82000000",
        ("tu1", "loaded_image_size"): "0x01620000",
        ("tu1", "entry_point"): "0x82CC21C0",
        (
            "rexglue",
            "commit",
        ): "956c6a8b5da4c54b9899a2593e9c67c26de30194",
        ("rexglue", "tree"): "b78b06b8ac650467372236a3a262864e069a9382",
        (
            "canary",
            "commit",
        ): "3a44f20c7bc66db1da583e8a6f0ab740e31908e9",
        ("canary", "tree"): "c343b0a5796590fadc3b78c993bfada51e7e9148",
        (
            "active_gpu_plugin",
            "sha256",
        ): "8232051BED6E5CE99CF37B2EF581C824F58875C140A4D3C75DE14E8A5DF4AA99",
        ("active_gpu_plugin", "size"): 2770944,
        ("active_gpu_plugin", "backend"): "D3D12_ONLY",
    }
    for (group, field), expected in expected_pin_fields.items():
        actual = pins.get(group, {}).get(field)
        if actual != expected:
            validation.error(
                f"G1.6A pin mismatch {group}.{field}: "
                f"recorded {actual!r}, expected {expected!r}"
            )
    if pins.get("paused_g2a", {}).get("incorporated") is not False:
        validation.error("G1.6A must record paused G2A as not incorporated")

    fable_start = expected_pin_fields[("fable_start", "commit")]
    g1_base = expected_pin_fields[("g1_accepted_base", "commit")]
    paused_g2a = expected_pin_fields[("paused_g2a", "commit")]
    git_checks = (
        (fable_start, expected_pin_fields[("fable_start", "tree")], "G1.6A start"),
        (paused_g2a, expected_pin_fields[("paused_g2a", "tree")], "paused G2A"),
    )
    for commit, expected_tree, label in git_checks:
        if run_git(ROOT, "cat-file", "-e", f"{commit}^{{commit}}").returncode != 0:
            validation.error(f"{label} commit is unavailable: {commit}")
            continue
        actual_tree = git_text(ROOT, "rev-parse", f"{commit}^{{tree}}")
        if actual_tree != expected_tree:
            validation.error(
                f"{label} tree mismatch: expected {expected_tree!r}, "
                f"actual {actual_tree!r}"
            )
    if run_git(ROOT, "merge-base", "--is-ancestor", g1_base, fable_start).returncode != 0:
        validation.error("G1 accepted base is not an ancestor of the G1.6A start")
    if run_git(ROOT, "merge-base", "--is-ancestor", fable_start, "HEAD").returncode != 0:
        validation.error("G1.6A HEAD does not descend from the required start")
    if run_git(ROOT, "merge-base", "--is-ancestor", paused_g2a, "HEAD").returncode == 0:
        validation.error("paused G2A is an ancestor of G1.6A HEAD")
    current_branch = git_text(ROOT, "branch", "--show-current")
    expected_branch = expected_pin_fields[("fable_start", "working_branch")]
    if current_branch != expected_branch:
        validation.error(
            f"G1.6A working branch mismatch: expected {expected_branch!r}, "
            f"actual {current_branch!r}"
        )

    changed_paths: set[str] = set()
    changed_text = git_text(ROOT, "diff", "--name-only", fable_start, "--")
    if changed_text is not None:
        changed_paths.update(line.replace("\\", "/") for line in changed_text.splitlines())
    status = run_git(
        ROOT, "status", "--porcelain=v1", "--untracked-files=all"
    ).stdout
    for line in status.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        changed_paths.add(path.replace("\\", "/"))
    exact_allowed_paths = {
        "tools/Verify-Fable2GpuReference.py",
        "tools/schemas/fable2-gpu-static-xdk-method-inventory-v1.schema.json",
    }
    required_phase_paths = {
        "docs/fable2-gpu-reference/12-static-xdk-method-recovery.md",
        "docs/fable2-gpu-reference/evidence/static-xdk-method-inventory.json",
        "docs/fable2-gpu-reference/g1.6a-completion.md",
        "docs/fable2-gpu-reference/README.md",
        "docs/fable2-gpu-reference/open-questions.md",
        *exact_allowed_paths,
    }
    for path in sorted(changed_paths):
        allowed = path.startswith("docs/fable2-gpu-reference/") or path in exact_allowed_paths
        if not allowed:
            validation.error(f"G1.6A phase hygiene rejects changed path: {path}")
        candidate_path = ROOT / path
        if candidate_path.is_file() and candidate_path.stat().st_size > 1024 * 1024:
            validation.error(f"G1.6A changed file exceeds bounded evidence size: {path}")
        if Path(path).suffix.lower() in {
            ".xex",
            ".xexp",
            ".dll",
            ".exe",
            ".bin",
            ".png",
            ".jpg",
            ".jpeg",
            ".sav",
            ".dmp",
        }:
            validation.error(f"G1.6A forbidden payload type changed: {path}")
    missing_phase_paths = required_phase_paths - changed_paths
    if missing_phase_paths:
        validation.error(
            f"G1.6A required phase paths are absent from the start diff: "
            f"{sorted(missing_phase_paths)!r}"
        )

    candidates = inventory.get("candidates", [])
    candidate_ids = [candidate.get("candidate_id") for candidate in candidates]
    if candidate_ids != list(expected_candidates):
        validation.error(
            f"G1.6A candidates must be unique and ordered: {list(expected_candidates)!r}; "
            f"actual {candidate_ids!r}"
        )
    actual_counts = {
        "candidates": len(candidates),
        "by_classification": {
            classification: sum(
                candidate.get("classification", {}).get("value") == classification
                for candidate in candidates
            )
            for classification in expected_classifications
        },
    }
    if inventory.get("counts") != actual_counts:
        validation.error(
            f"G1.6A counts mismatch: recorded {inventory.get('counts')!r}, "
            f"actual {actual_counts!r}"
        )

    generated_chunks: dict[str, str] = {}
    for candidate in candidates:
        candidate_id = candidate.get("candidate_id")
        expected = expected_candidates.get(str(candidate_id))
        if expected is None:
            continue
        (
            expected_name,
            expected_start,
            expected_end,
            expected_size,
            expected_instruction_count,
            expected_classification,
            expected_path,
            expected_file_size,
            expected_file_hash,
            expected_start_line,
            expected_end_line,
        ) = expected
        boundary = candidate.get("boundary", {})
        actual_identity = (
            candidate.get("generated_name"),
            boundary.get("start"),
            boundary.get("end"),
            boundary.get("size"),
            boundary.get("instruction_count"),
            candidate.get("classification", {}).get("value"),
        )
        expected_identity = expected[:6]
        if actual_identity != expected_identity:
            validation.error(
                f"G1.6A {candidate_id} identity mismatch: "
                f"recorded {actual_identity!r}, expected {expected_identity!r}"
            )
        try:
            start = int(str(boundary.get("start")), 16)
            end = int(str(boundary.get("end")), 16)
            size = int(str(boundary.get("size")), 16)
            instruction_count = int(boundary.get("instruction_count"))
        except (TypeError, ValueError):
            validation.error(f"G1.6A {candidate_id} has an invalid boundary")
        else:
            if end - start != size or instruction_count * 4 != size:
                validation.error(
                    f"G1.6A {candidate_id} boundary arithmetic is inconsistent"
                )
            for relationship in candidate.get("call_relationships", {}).get(
                "direct_callees", []
            ):
                try:
                    site = int(str(relationship.get("site")), 16)
                except (TypeError, ValueError):
                    validation.error(
                        f"G1.6A {candidate_id} has an invalid callee site"
                    )
                else:
                    if not start <= site < end:
                        validation.error(
                            f"G1.6A {candidate_id} callee site lies outside its boundary: "
                            f"{relationship.get('site')!r}"
                        )
            for imported in candidate.get("call_relationships", {}).get(
                "xbox_graphics_imports", []
            ):
                try:
                    site = int(str(imported.get("site")), 16)
                except (TypeError, ValueError):
                    validation.error(
                        f"G1.6A {candidate_id} has an invalid import site"
                    )
                else:
                    if not start <= site < end:
                        validation.error(
                            f"G1.6A {candidate_id} import site lies outside its boundary: "
                            f"{imported.get('site')!r}"
                        )

        provenance = candidate.get("provenance", {})
        if provenance.get("loaded_image_sha256") != expected_loaded_image:
            validation.error(f"G1.6A {candidate_id} loaded-image pin mismatch")
        mapping = provenance.get("generated_mapping", {})
        actual_mapping = (
            mapping.get("path"),
            mapping.get("size"),
            mapping.get("sha256"),
            mapping.get("start_line"),
            mapping.get("end_line"),
            mapping.get("generated_name"),
        )
        expected_mapping = (
            expected_path,
            expected_file_size,
            expected_file_hash,
            expected_start_line,
            expected_end_line,
            expected_name,
        )
        if actual_mapping != expected_mapping:
            validation.error(
                f"G1.6A {candidate_id} generated mapping mismatch: "
                f"recorded {actual_mapping!r}, expected {expected_mapping!r}"
            )
        generated_path = ROOT / expected_path
        if not generated_path.is_file():
            validation.error(
                f"G1.6A {candidate_id} generated source is unavailable: {generated_path}"
            )
        else:
            if generated_path.stat().st_size != expected_file_size:
                validation.error(
                    f"G1.6A {candidate_id} generated source size mismatch"
                )
            if sha256(generated_path) != expected_file_hash:
                validation.error(
                    f"G1.6A {candidate_id} generated source hash mismatch"
                )
            lines = generated_path.read_text(encoding="utf-8").splitlines()
            if expected_end_line > len(lines):
                validation.error(
                    f"G1.6A {candidate_id} generated line range exceeds the file"
                )
            else:
                first_line = lines[expected_start_line - 1].strip()
                expected_definition = (
                    f"DEFINE_REX_FUNC({expected_name}, {expected_start}, false) {{"
                )
                if first_line != expected_definition:
                    validation.error(
                        f"G1.6A {candidate_id} generated definition mismatch: "
                        f"{first_line!r}"
                    )
                chunk_lines = lines[expected_start_line - 1 : expected_end_line]
                comment_count = sum(line.startswith("\t// ") for line in chunk_lines)
                if comment_count != expected_instruction_count:
                    validation.error(
                        f"G1.6A {candidate_id} generated instruction count mismatch: "
                        f"expected {expected_instruction_count}, actual {comment_count}"
                    )
                generated_chunks[str(candidate_id)] = "\n".join(chunk_lines)

        registers = [
            entry.get("register")
            for entry in candidate.get("abi", {}).get("register_arguments", [])
        ]
        expected_registers = [f"r{index}" for index in range(3, 11)]
        if registers != expected_registers:
            validation.error(
                f"G1.6A {candidate_id} must classify r3-r10 exactly once and in order"
            )
        classification = candidate.get("classification", {})
        if not classification.get("evidence"):
            validation.error(f"G1.6A {candidate_id} classification lacks evidence")
        if not classification.get("missing_facts"):
            validation.error(f"G1.6A {candidate_id} lacks explicit missing facts")
        if not classification.get("minimum_evidence_to_change"):
            validation.error(
                f"G1.6A {candidate_id} lacks minimum reclassification evidence"
            )

    strongest = next(
        (candidate for candidate in candidates if candidate.get("candidate_id") == "SXDK-001"),
        {},
    )
    strongest_callers = {
        (entry.get("address"), entry.get("site"))
        for entry in strongest.get("call_relationships", {}).get("direct_callers", [])
    }
    if strongest_callers != {
        ("0x82BA7B28", "0x82BA81CC"),
        ("0x82BA83C0", "0x82BA85D8"),
    }:
        validation.error("G1.6A SXDK-001 direct caller evidence changed")
    strongest_callees = {
        (entry.get("address"), entry.get("site"))
        for entry in strongest.get("call_relationships", {}).get("direct_callees", [])
    }
    if strongest_callees != {("0x821E8EC0", "0x82BA77FC")}:
        validation.error("G1.6A SXDK-001 direct callee evidence changed")
    if strongest.get("call_relationships", {}).get("xbox_graphics_imports") != []:
        validation.error("G1.6A SXDK-001 must not claim a direct Xbox import")
    strongest_chunk = generated_chunks.get("SXDK-001", "")
    for required_text in (
        "ctx.lr = 0x82BA7800;",
        "sub_821E8EC0(ctx, base);",
        "// oris r11,r11,49158",
        "// ori r11,r11,11520",
        "// li r9,1",
        "// rlwimi r10,r9,16,0,20",
    ):
        if required_text not in strongest_chunk:
            validation.error(
                f"G1.6A SXDK-001 generated evidence lacks {required_text!r}"
            )
    caller_chunk = generated_chunks.get("SXDK-002", "")
    for required_text in ("ctx.lr = 0x82BA81D0;", "sub_82BA77D0(ctx, base);"):
        if required_text not in caller_chunk:
            validation.error(
                f"G1.6A SXDK-002 caller evidence lacks {required_text!r}"
            )

    expected_imports = {
        "SXDK-005": {
            ("VdGetSystemCommandBuffer", "0x832BA774", "0x82BA36D8"),
            ("VdSwap", "0x832BA784", "0x82BA373C"),
            ("VdSetDisplayMode", "0x832BA834", "0x82BA3854"),
            ("VdGetCurrentDisplayInformation", "0x832BA7D4", "0x82BA385C"),
            ("VdPersistDisplay", "0x832BA764", "0x82BA3B04"),
        },
        "SXDK-006": {
            ("VdInitializeEngines", "0x832BA7F4", "0x82BA69E4"),
            ("VdSetGraphicsInterruptCallback", "0x832BA814", "0x82BA6A28"),
            ("VdIsHSIOTrainingSucceeded", "0x832BA824", "0x82BA6BD4"),
        },
    }
    candidates_by_id = {
        candidate.get("candidate_id"): candidate for candidate in candidates
    }
    for candidate_id, expected in expected_imports.items():
        actual = {
            (entry.get("name"), entry.get("address"), entry.get("site"))
            for entry in candidates_by_id.get(candidate_id, {})
            .get("call_relationships", {})
            .get("xbox_graphics_imports", [])
        }
        if actual != expected:
            validation.error(
                f"G1.6A {candidate_id} Xbox graphics import evidence changed"
            )

    phase_decision = inventory.get("phase_decision", {})
    if phase_decision.get("result") != inventory.get("primary_result"):
        validation.error("G1.6A phase decision disagrees with the primary result")
    if phase_decision.get("next_phase") != (
        "G1.6B - Static Seam Qualification and Coverage"
    ):
        validation.error("G1.6A next phase must be G1.6B static qualification/coverage")
    if phase_decision.get("next_experiment_id") != "EXP-STATIC-XDK-002":
        validation.error("G1.6A next experiment must be EXP-STATIC-XDK-002")

    prose = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (STATIC_XDK_REPORT_PATH, STATIC_XDK_COMPLETION_PATH)
        if path.is_file()
    )
    for required_text in (
        "STATIC SEAM QUALIFIED",
        "EXP-STATIC-XDK-001",
        "EXP-STATIC-XDK-002",
        "0x82BA77D0",
        "0x82BA7894",
        *expected_candidates,
    ):
        if required_text not in prose:
            validation.error(f"G1.6A prose lacks required evidence {required_text!r}")

    input_records = {
        record.get("input_id"): record for record in inventory.get("analysis_inputs", [])
    }
    expected_inputs = {
        "INPUT-PROVENANCE": (
            "tools/fable2-entrypoint-closure-evidence.json",
            4768,
            "10F9411631AE08D653FB1CDCA192E364CF499BB56948A6E72F93384632786CC7",
        ),
        "INPUT-CLOSURE": (
            "out/analysis/BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00/entrypoint-closure.json",
            341019731,
            "665CA2AE7ED65632B2E9F368063D3D9EE260E8DEF6F276B455CD62A9F2DCC397",
        ),
        "INPUT-GHIDRA": (
            "out/analysis/BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00/ghidra-function-map.json",
            96710692,
            "03516B3A1F33433E493739418C9939D4FF1AEB0989F4ACEF2FD4D8204A077F58",
        ),
        "INPUT-JUMPS": (
            "out/analysis/BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00/jump-table-recovery.json",
            81223154,
            "B1FE26FB9119DAF7E7E0196CBDBA8CCA087BE190BF156FE0B12DF116379ED89A",
        ),
    }
    for input_id, (relative, expected_size, expected_hash) in expected_inputs.items():
        record = input_records.get(input_id, {})
        if record.get("path") != relative:
            validation.error(f"G1.6A analysis input path changed for {input_id}")
        provenance = str(record.get("provenance", ""))
        if str(expected_size) not in provenance or expected_hash not in provenance:
            validation.error(f"G1.6A analysis input provenance changed for {input_id}")
        path = ROOT / relative
        must_verify = input_id == "INPUT-PROVENANCE" or verify_artifacts
        if must_verify:
            if not path.is_file():
                validation.error(f"G1.6A analysis input is unavailable: {path}")
            else:
                if path.stat().st_size != expected_size:
                    validation.error(f"G1.6A analysis input size mismatch: {path}")
                if sha256(path) != expected_hash:
                    validation.error(f"G1.6A analysis input hash mismatch: {path}")
        if record.get("status") == "IGNORED LOCAL READ-ONLY":
            ignored = run_git(ROOT, "check-ignore", "-q", "--", relative)
            if ignored.returncode != 0:
                validation.error(f"G1.6A local input is not ignored: {relative}")

    sdk_pin = pins.get("rexglue", {})
    sdk_repo = (
        sdk_override.resolve()
        if sdk_override is not None
        else Path(str(sdk_pin.get("path", "")))
    )
    if not sdk_repo.is_dir():
        validation.error(f"G1.6A ReXGlue repository is unavailable: {sdk_repo}")
    else:
        sdk_checks = (
            ("HEAD", git_text(sdk_repo, "rev-parse", "HEAD"), sdk_pin.get("commit")),
            (
                "tree",
                git_text(sdk_repo, "rev-parse", "HEAD^{tree}"),
                sdk_pin.get("tree"),
            ),
            (
                "branch",
                git_text(sdk_repo, "branch", "--show-current"),
                sdk_pin.get("branch"),
            ),
        )
        for label, actual, expected in sdk_checks:
            if actual != expected:
                validation.error(
                    f"G1.6A ReXGlue {label} mismatch: expected {expected!r}, "
                    f"actual {actual!r}"
                )
        sdk_status_text = git_text(
            sdk_repo, "status", "--short", "--untracked-files=all"
        )
        sdk_status = [] if sdk_status_text in (None, "") else sdk_status_text.splitlines()
        if sdk_status != sdk_pin.get("allowed_preexisting_status"):
            validation.error(
                f"G1.6A ReXGlue status mismatch: expected "
                f"{sdk_pin.get('allowed_preexisting_status')!r}, actual {sdk_status!r}"
            )

    canary_pin = pins.get("canary", {})
    canary_repo = (
        canary_override.resolve()
        if canary_override is not None
        else Path(str(canary_pin.get("path", "")))
    )
    if not canary_repo.is_dir():
        validation.error(f"G1.6A Canary repository is unavailable: {canary_repo}")
    else:
        canary_checks = (
            ("HEAD", git_text(canary_repo, "rev-parse", "HEAD"), canary_pin.get("commit")),
            (
                "tree",
                git_text(canary_repo, "rev-parse", "HEAD^{tree}"),
                canary_pin.get("tree"),
            ),
            (
                "branch",
                git_text(canary_repo, "branch", "--show-current"),
                canary_pin.get("branch"),
            ),
        )
        for label, actual, expected in canary_checks:
            if actual != expected:
                validation.error(
                    f"G1.6A Canary {label} mismatch: expected {expected!r}, "
                    f"actual {actual!r}"
                )
        canary_status = git_text(
            canary_repo, "status", "--short", "--untracked-files=all"
        )
        if canary_status != "":
            validation.error(f"G1.6A Canary worktree is not clean: {canary_status!r}")

    if verify_artifacts:
        plugin = pins.get("active_gpu_plugin", {})
        plugin_path = ROOT / str(plugin.get("path", ""))
        if not plugin_path.is_file():
            validation.error(f"G1.6A active GPU plugin is unavailable: {plugin_path}")
        else:
            if plugin_path.stat().st_size != plugin.get("size"):
                validation.error("G1.6A active GPU plugin size mismatch")
            if sha256(plugin_path) != plugin.get("sha256"):
                validation.error("G1.6A active GPU plugin hash mismatch")


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
    divergence_matrix = load_json(DIVERGENCE_MATRIX_PATH, validation)
    divergence_history = load_json(DIVERGENCE_HISTORY_PATH, validation)
    divergence_matrix_schema = load_json(DIVERGENCE_MATRIX_SCHEMA_PATH, validation)
    divergence_history_schema = load_json(DIVERGENCE_HISTORY_SCHEMA_PATH, validation)
    fable_relevance = load_json(FABLE_RELEVANCE_PATH, validation)
    boundary_assessment = load_json(BOUNDARY_ASSESSMENT_PATH, validation)
    replacement_seams = load_json(REPLACEMENT_SEAMS_PATH, validation)
    experiment_backlog = load_json(EXPERIMENT_BACKLOG_PATH, validation)
    g2a_decision = load_json(G2A_DECISION_PATH, validation)
    fable_relevance_schema = load_json(FABLE_RELEVANCE_SCHEMA_PATH, validation)
    boundary_assessment_schema = load_json(
        BOUNDARY_ASSESSMENT_SCHEMA_PATH, validation
    )
    replacement_seams_schema = load_json(REPLACEMENT_SEAMS_SCHEMA_PATH, validation)
    experiment_backlog_schema = load_json(EXPERIMENT_BACKLOG_SCHEMA_PATH, validation)
    g2a_decision_schema = load_json(G2A_DECISION_SCHEMA_PATH, validation)
    g1_candidates = load_json(G1_CANDIDATE_PATH, validation)
    static_xdk_inventory = load_json(STATIC_XDK_PATH, validation)
    static_xdk_schema = load_json(STATIC_XDK_SCHEMA_PATH, validation)
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
    if divergence_matrix and divergence_matrix_schema:
        validate_with_schema(
            divergence_matrix,
            divergence_matrix_schema,
            "divergence matrix",
            validation,
        )
    if divergence_history and divergence_history_schema:
        validate_with_schema(
            divergence_history,
            divergence_history_schema,
            "divergence history",
            validation,
        )
    if fable_relevance and fable_relevance_schema:
        validate_with_schema(
            fable_relevance,
            fable_relevance_schema,
            "Fable relevance matrix",
            validation,
        )
    if boundary_assessment and boundary_assessment_schema:
        validate_with_schema(
            boundary_assessment,
            boundary_assessment_schema,
            "boundary assessment",
            validation,
        )
    if replacement_seams and replacement_seams_schema:
        validate_with_schema(
            replacement_seams,
            replacement_seams_schema,
            "replacement seams",
            validation,
        )
    if experiment_backlog and experiment_backlog_schema:
        validate_with_schema(
            experiment_backlog,
            experiment_backlog_schema,
            "experiment backlog",
            validation,
        )
    if g2a_decision and g2a_decision_schema:
        validate_with_schema(
            g2a_decision,
            g2a_decision_schema,
            "G2A decision",
            validation,
        )
    if static_xdk_inventory and static_xdk_schema:
        validate_with_schema(
            static_xdk_inventory,
            static_xdk_schema,
            "static XDK method inventory",
            validation,
        )

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
            if divergence_matrix and divergence_history and inventory:
                combined_roots = dict(roots)
                combined_roots.update(canary_roots)
                combined_commits = dict(commits)
                combined_commits.update(canary_commits)
                validate_divergence_evidence(
                    divergence_matrix,
                    divergence_history,
                    combined_roots,
                    combined_commits,
                    validation,
                )

    if all(
        (
            fable_relevance,
            boundary_assessment,
            replacement_seams,
            experiment_backlog,
            g2a_decision,
            divergence_matrix,
            g1_candidates,
        )
    ):
        validate_g15d_evidence(
            fable_relevance,
            boundary_assessment,
            replacement_seams,
            experiment_backlog,
            g2a_decision,
            divergence_matrix,
            g1_candidates,
            validation,
        )
        if args.verify_artifacts:
            validate_g15d_artifacts(fable_relevance, validation)

    if static_xdk_inventory:
        validate_g16a_evidence(
            static_xdk_inventory,
            args.sdk_root,
            args.canary_root,
            args.verify_artifacts,
            validation,
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
        f"PASS: G1.5A/G1.5B/G1.5C/G1.5D/G1.6A GPU reference validated "
        f"({len(validation.warnings)} warning(s))"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
