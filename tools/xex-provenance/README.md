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
No `--force`, guest instruction patch, external source, or generated-source
editing is involved. The normal build does not depend on this probe.
