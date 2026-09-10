"""NR0B-1 isolated preparation and bounded configuration-report validation.

Never launches the game. Private inventories live only in ignored output roots.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

PREFIX = "REX_GPU_CONFIG_V1 "
MAIN = "B13EBABEBABEBABE/4D5307F1/00000001/Hero000/mainsave.bin"
MAIN_ID = {"bytes": 415039, "sha256": "13FC340F6869DA73CB958BA36CB50905E29B8FBEA073CEFF46490DB4A9812489"}
TITLE_INPUTS = {
    "default.xex": {"bytes": 21217280, "sha256": "88C4EF2E18E65409444D1B068EFF921D1F7E180A5AE64EDC64BA6B0872372662"},
    "default.xexp": {"bytes": 2992128, "sha256": "046A05693B4DA4437083C784000A850858B3BF992955C7DB30D518FB3E53E41C"},
}
STAGES = {"runtime-paths", "device", "requested", "context", "shared-memory",
          "pipeline-policy", "shader-storage", "guest-output", "host-present"}
REQUIRED = {
    "runtime-paths": {"game_data_root", "user_data_root", "update_data_root", "cache_root"},
    "device": {"api", "adapter_description", "adapter_luid", "vendor_id", "device_id",
               "driver_version", "driver_source", "driver_hresult", "options_hresult",
               "device_create_feature_level", "rov_supported", "resource_binding_tier",
               "tiled_resources_tier", "alpha_blend_factor_supported", "alpha_options13_hresult"},
    "context": {"render_target_path", "bindless_effective", "draw_resolution_scale_x",
                "draw_resolution_scale_y", "internal_extent", "anisotropy_effective"},
    "shared-memory": {"tiled_requested", "tiled_effective", "selection_reason"},
    "pipeline-policy": {"async_shader_compilation_requested", "pipeline_threads_created", "async_effective_policy"},
    "shader-storage": {"cache_root", "title_id", "shader_file", "pipeline_file", "storage_initialized"},
    "guest-output": {"width", "height", "scope"},
    "host-present": {"width", "height", "sync_interval", "allow_tearing", "hresult"},
    "requested": {name + suffix for name in (
        "gpu_plugin", "d3d12_adapter", "render_target_path_d3d12", "d3d12_bindless",
        "d3d12_tiled_shared_memory", "draw_resolution_scale_x", "draw_resolution_scale_y",
        "anisotropic_override", "clear_memory_page_state", "async_shader_compilation",
        "d3d12_pipeline_creation_threads", "vsync") for suffix in ("", "_source")},
}


def identity(path):
    path = Path(path)
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest().upper()
    return {"bytes": path.stat().st_size, "sha256": digest}


def inventory(root):
    root = Path(root)
    if not root.is_dir():
        raise ValueError(f"Missing inventory root: {root}")
    result = {}
    for path in [root, *sorted(root.rglob("*"))]:
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            raise ValueError(f"Refusing redirected inventory path: {path}")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = identity(path)
    return result


def write_new(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def repository(root):
    return {"root": str(root), "head": git(root, "rev-parse", "HEAD"),
            "tree": git(root, "rev-parse", "HEAD^{tree}"),
            "branch": git(root, "branch", "--show-current"),
            "status": git(root, "status", "--porcelain=v1")}


def guarded_copy(source, destination, expected):
    if Path(destination).exists():
        raise ValueError(f"Refusing existing copy destination: {destination}")
    if inventory(source) != expected:
        raise ValueError("Source inventory changed before copy")
    shutil.copytree(source, destination, copy_function=shutil.copy2)
    if inventory(destination) != expected or inventory(source) != expected:
        raise ValueError("Copy/inventory mismatch; preserve both for investigation")


def prepare(repo, sdk, run_id):
    if not run_id or len(run_id) > 64 or any(c not in
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_." for c in run_id):
        raise ValueError("Invalid run ID")
    session = repo / "out/nr0b1/sessions" / run_id
    preserved = repo / "out/nr0b1/checkpoints" / run_id / "user-data"
    if session.exists() or preserved.parent.exists():
        raise ValueError("Session/checkpoint already exists; never reuse a session")
    for target in (session, preserved):
        subprocess.run(["git", "-C", str(repo), "check-ignore", "-q", str(target)], check=True)
    initial = json.loads((repo / "out/nr0b1/initial-state.json").read_text())
    source = Path(initial["save_source"])
    files = inventory(source)
    if files != initial["save_inventory"] or files.get(MAIN) != MAIN_ID:
        raise ValueError("Checkpoint differs from accepted source; request selection")
    baseline = repo / "out/build/win-amd64-release"
    for name, expected in initial["baseline_artifacts"].items():
        if identity(baseline / name) != expected:
            raise ValueError(f"Baseline changed: {name}")
    session.mkdir(parents=True, exist_ok=False)
    preserved.parent.mkdir(parents=True, exist_ok=False)
    guarded_copy(source, preserved, files)
    writable = session / "user-data"
    guarded_copy(preserved, writable, files)
    runtime = session / "runtime"
    runtime.mkdir()
    staged = {}
    for name in initial["baseline_artifacts"]:
        origin = (sdk / "out/win-amd64/Release" if name in
                  ("rexruntime.dll", "rexgpu-xenos.dll") else baseline) / name
        expected = identity(origin)
        shutil.copy2(origin, runtime / name)
        if identity(runtime / name) != expected:
            raise ValueError(f"Staging mismatch: {name}")
        staged[name] = {**expected, "path": str(runtime / name), "source": str(origin)}
    config = baseline / "fable2.toml"
    config_id = None
    if config.exists():
        shutil.copy2(config, runtime / config.name)
        config_id = identity(config)
        if identity(runtime / config.name) != config_id:
            raise ValueError("Configuration copy mismatch")
    report = {"schema": "fable2-nr0b1-preparation-v1", "run_id": run_id,
              "status": "PREPARED — USER RUN REQUIRED", "session": str(session),
              "fable": repository(repo), "sdk": repository(sdk),
              "sdk_build_configuration": "win-amd64-release; D3D12 ON; Vulkan OFF",
              "source": str(source), "preserved": str(preserved), "writable": str(writable),
              "save_inventory": files, "staged": staged,
              "baseline": str(baseline), "baseline_artifacts": initial["baseline_artifacts"],
              "configuration": {"path": str(runtime / "fable2.toml"), "identity": config_id},
              "cache": {"root": str(writable / "cache"), "isolated": True,
                        "existed_before_launch": True, "state": "copied baseline material",
                        "files": {k: v for k, v in files.items() if k.startswith("cache/")},
                        "driver_cache": "unavailable; no isolated driver-cache mechanism"}}
    write_new(session / "preparation.json", report)
    check_preflight(report)
    print(session)


def check_preflight(prep, after=False):
    for name, expected in TITLE_INPUTS.items():
        if identity(Path(prep["fable"]["root"]) / "assets/runtime" / name) != expected:
            raise ValueError(f"Accepted runtime title input changed: {name}")
    for key in ("source", "preserved") + (() if after else ("writable",)):
        if inventory(prep[key]) != prep["save_inventory"]:
            raise ValueError(f"{key} inventory changed")
    for name, expected in prep["baseline_artifacts"].items():
        if identity(Path(prep["baseline"]) / name) != expected:
            raise ValueError(f"Baseline artifact changed: {name}")
    for name, item in prep["staged"].items():
        if identity(item["path"]) != {k: item[k] for k in ("bytes", "sha256")}:
            raise ValueError(f"Staged artifact changed: {name}")
    config = prep["configuration"]
    actual = identity(config["path"]) if Path(config["path"]).exists() else None
    if actual != config["identity"]:
        raise ValueError("Staged configuration changed")


def parse_records(lines, run_id):
    records, errors = {}, []
    for line in lines:
        if "REX_GPU_CONFIG_REPORT_ERROR" in line:
            errors.append("SDK reporting error")
        if PREFIX not in line:
            continue
        raw = line.split(PREFIX, 1)[1].strip()
        if len(raw.encode("utf-8")) > 16384:
            errors.append("Oversized configuration record")
            continue
        try:
            record = json.loads(raw)
            stage = record["stage"]
            fields = record["fields"]
            if (record["schema"] != "rex-gpu-config-v1" or record["run_id"] != run_id
                    or stage not in STAGES or stage in records or not isinstance(fields, dict)
                    or len(fields) > 32 or not REQUIRED[stage] <= fields.keys()
                    or not all(isinstance(v, str) for v in fields.values())):
                raise ValueError("Invalid/duplicate/incomplete record")
            records[stage] = fields
        except (ValueError, KeyError, TypeError):
            errors.append("Malformed, wrong-run or incomplete configuration record")
    errors.extend(f"Missing stage: {stage}" for stage in sorted(STAGES - records.keys()))
    return records, errors


def validate_loaded(prep, process):
    errors = []
    for name, expected in prep["staged"].items():
        observed = process.get("modules", {}).get(name)
        if not observed or any(observed.get(k) != expected[k] for k in ("bytes", "sha256")):
            errors.append(f"Loaded artifact missing/mismatch: {name}")
        elif os.path.normcase(os.path.abspath(observed["path"])) != os.path.normcase(os.path.abspath(expected["path"])):
            errors.append(f"Loaded path mismatch: {name}")
    if (not process.get("pid") or not process.get("start_utc") or not process.get("end_utc")
            or process.get("exit_code") is None or process.get("run_id") != prep["run_id"]):
        errors.append("Process identity/termination incomplete")
    if process.get("exit_code") not in (None, 0):
        errors.append("Process exited unsuccessfully")
    return errors


def analyse(session):
    prep = json.loads((session / "preparation.json").read_text(encoding="utf-8-sig"))
    check_preflight(prep, after=True)
    process = json.loads((session / "process.json").read_text(encoding="utf-8-sig"))
    title_lines = []
    def observed_lines(stream):
        for line in stream:
            if len(title_lines) < 16 and any(marker in line for marker in (
                    "XEX patch applied successfully:", "Initializing shader storage for title",
                    "Loading XEX image:")):
                title_lines.append(line.strip()[:2048])
            yield line
    with Path(process["log"]).open(encoding="utf-8-sig", errors="replace") as stream:
        records, errors = parse_records(observed_lines(stream), prep["run_id"])
    errors += validate_loaded(prep, process)
    errors += ["Launcher reporting error: " + item for item in process.get("reporting_errors", [])]
    roots = records.get("runtime-paths", {})
    for field, expected in (("user_data_root", prep["writable"]), ("cache_root", prep["cache"]["root"])):
        if os.path.normcase(os.path.abspath(roots.get(field, ""))) != os.path.normcase(os.path.abspath(expected)):
            errors.append(f"Effective isolated root missing/mismatch: {field}")
    if records.get("device", {}).get("api") != "d3d12":
        errors.append("Expected D3D12 device not observed")
    if records.get("requested", {}).get("gpu_plugin") != "xenos":
        errors.append("Expected Xenos plugin not observed")
    if records.get("shader-storage", {}).get("title_id") != "0x4D5307F1":
        errors.append("Expected Fable title identity not observed")
    errors.append("User scene/load and normal-exit confirmation requires handoff review")
    output = {"run_id": prep["run_id"], "status": "PARTIAL SNAPSHOT — SPECIFIC EVIDENCE REQUIRED",
              "records": records, "remaining": errors,
              "source_and_preserved_unchanged": True,
              "supported_title_log_observations": title_lines,
              "verified_disk_title_inputs": TITLE_INPUTS,
              "writable_after": inventory(prep["writable"]),
              "post_patch_runtime_hash": "unavailable; no process-memory inspection"}
    write_new(session / "effective-report.json", output)
    print(json.dumps({"status": output["status"], "remaining": errors}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "preflight", "analyse"))
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--sdk", type=Path, default=Path("C:/Dev/rexglue-sdk-v0.10"))
    parser.add_argument("--run-id")
    parser.add_argument("--session", type=Path)
    args = parser.parse_args()
    if args.action == "prepare":
        prepare(args.repo.resolve(), args.sdk.resolve(), args.run_id)
    elif args.action == "preflight":
        check_preflight(json.loads((args.session / "preparation.json").read_text()))
        print("Preflight integrity PASS")
    else:
        analyse(args.session)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"NR0B1 preparation/reporting error: {error}", file=sys.stderr)
        sys.exit(1)
