"""Read-only, explicit-opt-in consumer for the Phase 2H reviewed semantic layer."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import Fable2ReviewedSemantics as layer


EXACT_PATHS = {
    "source_pins": layer.SOURCE_PINS_PATH.as_posix(),
    "decision": layer.DECISION_PATH.as_posix(),
    "delta": layer.DELTA_PATH.as_posix(),
    "view": layer.VIEW_PATH.as_posix(),
}


def exact_identity(path: str, expected_path: str, sha256: str) -> dict[str, Any]:
    layer.require(path == expected_path, "Explicit opt-in requires the exact repository-relative path")
    actual = layer.identity(path)
    layer.require(sha256 == actual["sha256"], "Explicit opt-in hash mismatch: " + path)
    return actual


def select(arguments: argparse.Namespace) -> dict[str, Any]:
    opt_in_values = [
        arguments.opt_in,
        arguments.source_pins,
        arguments.source_pins_sha256,
        arguments.decision,
        arguments.decision_sha256,
        arguments.delta,
        arguments.delta_sha256,
        arguments.view,
        arguments.view_sha256,
    ]
    if not any(value is not None for value in opt_in_values):
        layer.load_layer()
        return layer.build_default_view()

    layer.require(all(value is not None for value in opt_in_values),
                  "Partial Phase 2H opt-in refused")
    layer.require(arguments.opt_in == layer.LAYER_VERSION, "Wrong Phase 2H layer version")
    exact_identity(arguments.source_pins, EXACT_PATHS["source_pins"], arguments.source_pins_sha256)
    exact_identity(arguments.decision, EXACT_PATHS["decision"], arguments.decision_sha256)
    exact_identity(arguments.delta, EXACT_PATHS["delta"], arguments.delta_sha256)
    exact_identity(arguments.view, EXACT_PATHS["view"], arguments.view_sha256)
    _, _, _, view = layer.load_layer()
    return view


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--opt-in")
    result.add_argument("--source-pins")
    result.add_argument("--source-pins-sha256")
    result.add_argument("--decision")
    result.add_argument("--decision-sha256")
    result.add_argument("--delta")
    result.add_argument("--delta-sha256")
    result.add_argument("--view")
    result.add_argument("--view-sha256")
    return result


def main(argv: list[str] | None = None) -> int:
    try:
        document = select(parser().parse_args(argv))
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        print("REFUSED:", error, file=sys.stderr)
        return 2
    sys.stdout.buffer.write(layer.payload(document))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
