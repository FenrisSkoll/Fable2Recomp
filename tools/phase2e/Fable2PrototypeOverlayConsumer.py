"""Explicit analysis-only consumer adapter for the Phase 2E overlay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import Fable2PrototypeOverlay as overlay


def repository_input(value: str) -> Path:
    path = Path(value)
    overlay.require(not path.is_absolute() and ".." not in path.parts, "Consumer input path must be repository-relative")
    resolved = (overlay.ROOT / path).resolve()
    overlay.require(resolved.is_relative_to(overlay.ROOT.resolve()), "Consumer input escapes repository")
    return resolved


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("default", help="Report the unchanged closed Phase 2A default selection")
    opt_in = subparsers.add_parser("opt-in", help="Validate and select an exact Phase 2E overlay")
    opt_in.add_argument("--overlay-version", required=True)
    opt_in.add_argument("--decision", required=True)
    opt_in.add_argument("--decision-sha256", required=True)
    opt_in.add_argument("--delta", required=True)
    opt_in.add_argument("--delta-sha256", required=True)
    opt_in.add_argument("--effective-map", required=True)
    opt_in.add_argument("--effective-map-sha256", required=True)
    args = parser.parse_args()

    if args.command == "default":
        provenance = overlay.load_default_mapping()
    else:
        _, provenance = overlay.load_opt_in_mapping(
            args.overlay_version,
            repository_input(args.decision),
            args.decision_sha256,
            repository_input(args.delta),
            args.delta_sha256,
            repository_input(args.effective_map),
            args.effective_map_sha256,
        )
    print(json.dumps(provenance, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
