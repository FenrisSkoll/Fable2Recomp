# Load-only XEX provenance probe

This isolated executable links the installed SDK selected by the release CMake
cache. It calls `Runtime::Setup` and `LoadXexImage`, then exits without preparing
or launching guest execution. It writes private executable bytes under `out/`;
never commit or distribute the snapshots. It does not modify the inputs, saves,
normal runtime cache, manifest, generated source, or SDK.

From the developer PowerShell environment, with a new output directory:

```powershell
cmake -S tools/xex-provenance -B out/comparative-audit/probe-build -G Ninja `
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=clang-cl `
    -Drexglue_DIR=C:/Dev/rexglue-sdk-v0.10/out/install/win-amd64/lib/cmake/rexglue
cmake --build out/comparative-audit/probe-build
.\out\comparative-audit\probe-build\fable2_xex_provenance.exe tool `
    C:\Dev\Fable2Recomp\assets\tu1 'game:\default.xex' `
    C:\Dev\Fable2Recomp\out\comparative-audit\tool-final
.\out\comparative-audit\probe-build\fable2_xex_provenance.exe runtime `
    C:\Dev\Fable2Recomp\assets\runtime 'game:\default.xex' `
    C:\Dev\Fable2Recomp\out\comparative-audit\runtime-final `
    C:\Dev\Fable2Recomp\assets\update
```

Use distinct new snapshot directories for subsequent runs. Copy the current
manifest to `out/comparative-audit/regenerate.toml`; change only `game_root` and
`file_path` to their absolute original paths and `out_directory_path` to a NEW
isolated `out/comparative-audit/regenerated` directory. Copy the current
`generated/default/codegen.partition.json` into that directory. Then run:

```powershell
& C:\Dev\rexglue-sdk-v0.10\out\install\win-amd64\bin\rexglue.exe codegen `
    .\out\comparative-audit\regenerate.toml
python -B -X utf8 tools/Verify-Fable2XexProvenance.py `
    --tool-snapshot out/comparative-audit/tool-final `
    --runtime-snapshot out/comparative-audit/runtime-final `
    --regenerated out/comparative-audit/regenerated
```

The verifier requires the full loaded image and executable sections to match the
existing closure evidence, checks both XEX/XEXP input pairs, compares actual
loaded DLL identity with the normal staged and installed DLL, and requires an
identical census and bytes of every generated C++/header file. It fails closed.
The result is a provenance check at load time and generation time, not proof of
PPC translation correctness, later guest writes, presentation, or gameplay.
Run snapshots and verification consecutively without replacing DLLs in between;
the verifier hashes the recorded DLL path at verification time.

The temporary manifest must retain every other option and the partition file.
The canonical provenance workflow uses no `--force`, guest instruction patches,
external source, or generated-source editing. The normal build does not depend
on this probe.

## Private incremental-invalidation fixture

The probe also writes `headers.bin` for the controlled fixture builder. Treat it
as private executable material, exactly like `image.bin`; never commit it.
`make_delta_fixture.py` requires `cryptography` and writes only a new destination.
It verifies the original encrypted block chain and appends a bounded copy-delta.
The resulting unsigned loader fixture must never be used for gameplay.

```powershell
python -m venv out/xexp-invalidation/venv
./out/xexp-invalidation/venv/Scripts/python.exe -m pip install cryptography
./out/xexp-invalidation/venv/Scripts/python.exe -B tools/xex-provenance/make_delta_fixture.py `
    --source assets/tu1/default.xexp `
    --headers out/xexp-invalidation/canonical-headers/headers.bin `
    --image out/xexp-invalidation/canonical-headers/image.bin `
    --destination out/xexp-invalidation/mutated.xexp `
    --old-offset 0x964804 --new-offset 0x967544
python -B -X utf8 tools/xex-provenance/verify_invalidation.py `
    --repo . --sdk C:/Dev/rexglue-sdk-v0.10/out/install/win-amd64 `
    --fixed-tool C:/Dev/rexglue-sdk-v0.10/out/win-amd64/Release/rexglue.exe `
    --delta out/xexp-invalidation/mutated.xexp `
    --work out/xexp-invalidation/new-contract-run
```

First create `canonical-headers` with the load-only probe above, using the
canonical TU1 game root and that new output directory. The integration runner
requires a new work directory, copies all inputs, invokes the normal generated
CMake codegen target and retains command logs, invocation evidence, stamps and
file censuses in `receipt.json`. It changes only copied XEXP/tool files. It also
checks that real patch removal under the TU1-specific manifest fails closed;
generic base-only add/remove emission is covered by the SDK's
`codegen_dependency_scheduler` integration test. `--resume-removal` runs only
the removal/restoration checks on an already successful fixture.

See [CP-1 closeout](../../docs/fable2-comparative-archaeology/xexp-invalidation-closeout.md)
for the recorded hashes, expected instruction delta and coverage limits.
