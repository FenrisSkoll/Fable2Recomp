# Fable II fault-walker verified baseline

Closeout date: `2026-08-28`

This document is the durable handoff for the experimental Fable II fault-walker
work through Harvest 003. Exact per-run evidence remains in
`docs/fault-walk-harvest-001.md`, `docs/fault-walk-harvest-002.md`,
`docs/fault-walk-harvest-003.md`, and the referenced numbered logs/reports.

## Evidence labels

- **CONFIRMED** means demonstrated by TU1 bytes, generated output, source,
  saved runtime evidence, or a reproducible build/test.
- **STRONG INFERENCE** means several confirmed observations support the
  conclusion, but the game has not directly identified the semantic type.
- **UNRESOLVED** means the evidence is insufficient for a correctness change.

## Project and executable identity

- Canonical project: `C:\Dev\Fable2Recomp`, branch `fault-walker`, closeout
  starting HEAD `f0b7f1397326a6bface2c4f1d9d491d40853f20c`.
- ReXGlue SDK: `C:\Dev\rexglue-sdk`, branch `fable2-fault-walker`, closeout
  HEAD `3e61c63f3acaa37b7ac485b06d33b8a6efa5afbc`.
- Integrated SDK version reported by codegen/build:
  `0.9.0.2-dev.ga30cf01`. The branch descends from ReXGlue SDK v0.9.0 commit
  `3eb9b511b4140d2769e27be63eae57d41bfa2afa` and preserves diagnostic commit
  `e464cb3bcf20da4531ae4f909735dae8dd459505`.
- Target: Fable II Game of the Year Edition, Xbox 360 TU1, Title ID
  `4D5307F1`, Media ID `716F0A0D`, patched version `0.0.1.26`.
- Base executable: `assets\tu1\default.xex`, SHA-256
  `88C4EF2E18E65409444D1B068EFF921D1F7E180A5AE64EDC64BA6B0872372662`.
- Title-update patch: `assets\tu1\default.xexp`, SHA-256
  `046A05693B4DA4437083C784000A850858B3BF992955C7DB30D518FB3E53E41C`.
- Codegen and Run 011 both reported:
  `XEX patch applied successfully: base version: 0.0.0.26, new version: 0.0.1.26`.
  **CONFIRMED:** analysis/codegen must use the XEX after applying this TU1
  patch, not the unpatched base executable.
- The Harvest 003 loaded-image capture is
  `out\fault-walk-runs\iteration-08\tu1-text-0x82000000.bin`, SHA-256
  `5A6ADBDA1714AABC63BD7F6D52B55BCAAAD9B6F3F81907D93C1FFE830B22E59F`.
  This is a runtime loaded-image capture, not a replacement hash for either
  source XEX file.
- Loaded image base: `0x82000000`. Analyzer-confirmed executable ranges are
  `.text [0x82170000,0x832BAC00)` and `BINK [0x832BAC00,0x832CA200)`.
- Xenia/Xenia Canary is a behavioural reference only. Comparisons must use the
  same title/media and demonstrably active TU1; base-game behaviour is not proof
  of TU1 behaviour.

## Verified historical baseline

### TU1 patching and non-local jumps

The manifest maps guest `setjmp` to `0x83006C90` and guest `longjmp` to
`0x82CAFA30`. Commit `5e59aa0b0f83f78ebca9195a8a22a20505a1890d`
restored these values before the title-screen/TU1 bring-up fixes.

**CONFIRMED:** ReXGlue uses these addresses to recognize guest non-local
control flow. FULL fault-walk tests additionally verify that longjmp unwinds the
generated wrapper stack and reconciles its TLS depth. Treating these entries as
ordinary calls would not preserve setjmp/longjmp control-flow semantics.

### Normal gameplay baseline

Before this closeout, normal non-fault-walk Run 007 reached controllable
Bowerstone Old Town childhood gameplay and exited gracefully with code
`0x00000000`, with no `[FATAL]` or `[FWT]` line. Evidence:

- `C:\Dev\Fable2Recomp\fable2-run-007.log`
- `C:\Dev\Fable2Recomp\out\normal-validation-runs\iteration-01\result.json`

The Harvest 003 closeout normal run is Run 011. Its final result is recorded in
the validation section below.

### Correctness versus diagnostic tolerance

A manifest entry backed by a confirmed TU1 function boundary, followed by a
real generated body and dispatcher registration, is a correctness-oriented
repair for the discovery omission. A poisoned target or synthetic
`RETURN_R3_ZERO` is never a fix.

- `DISPATCH_ONLY` remains the preferred Fable gameplay harvesting mode. It
  intercepts only invalid/unregistered dispatcher targets and does not wrap
  valid generated functions.
- `FULL` retains the generated-function boundary, complete `PPCContext`
  checkpoint/restore, innermost TLS attribution, guest-SEH precedence, and the
  allowlist for host `0xC0000005` and `0xC0000094` faults.
- FULL restores registers only. Guest-memory writes before a suppressed host
  fault are not rolled back. DISPATCH_ONLY never executes an invalid body, but
  its synthetic result can still divert later guest state.
- Harvests 001–003 found only invalid/unregistered targets. No Fable harvest
  recorded a host access violation or integer divide-by-zero fault.

## Harvest ledger

Ranges use exclusive ends. `body+reg` means a generated `DEFINE_REX_FUNC` body
and an entry in `generated\default\fable2_init.cpp` were both verified after
the closeout codegen. The normal column records validation at or beyond the
relevant gameplay path without an invalid-dispatch fatal; it does not claim
that every function has a dedicated execution counter.

| Harvest | TU1 range | Size | Final classification | Indirect path and pointer evidence | Runtime caller / LR | Manifest and generated status | Normal validation |
|---|---|---:|---|---|---|---|---|
| 001 | `[0x82C03B28,0x82C03B44)` | `0x1C` | **HIGH CONFIDENCE PRIMARY; CONFIRMED omission** | Exact `.rdata` pointer at `0x8200A190`, slot 42 of `[0x8200A0E8,0x8200A328)`; conditional leaf/tail branch | caller `0x821907A4`, LR `0x821907A8` | `"0x82C03B28" = { size = 0x1C }`; body+reg | Run 007 passed; Run 011 passed |
| 001 | `[0x829647F0,0x82964800)` | `0x10` | **HIGH CONFIDENCE PRIMARY; CONFIRMED omission** | `r3` virtual thunk, slot `0x4C`; materialized at `0x82961254/0x8296125C`, `0x82964B6C/0x82964B74`, and `0x8296571C/0x82965730` | caller `0x829641C4`, LR `0x829641C8` | `"0x829647F0" = { size = 0x10 }`; body+reg | Run 007 passed; Run 011 passed |
| 001 | `[0x829675E0,0x829675F0)` | `0x10` | **LIKELY PRIMARY; CONFIRMED omission** | `r3` virtual thunk, slot `0xB4`; materialized at `0x829650C4/0x829650CC` and `0x82966B4C/0x82966B60` | caller `0x82966EE4`, LR `0x82966EE8` | `"0x829675E0" = { size = 0x10 }`; body+reg | Run 007 passed; Run 011 passed |
| 002 | `[0x829675D0,0x829675E0)` | `0x10` | **HIGH CONFIDENCE PRIMARY; CONFIRMED omission** | `r3` virtual thunk, slot `0x94`; materialized at `0x826ECA14/0x826ECA1C` and `0x82964E18/0x82964E20` | caller `0x822D2A9C`, LR `0x822D2AA0` | `"0x829675D0" = { size = 0x10 }`; body+reg | Run 011 passed |
| 002 | `[0x829675C0,0x829675D0)` | `0x10` | **HIGH CONFIDENCE PRIMARY; CONFIRMED omission** | `r3` virtual thunk, slot `0x44`; materialized at `0x82964B20/0x82964B28` and passed to `0x82965500` | caller `0x822D2A9C`, LR `0x822D2AA0` | `"0x829675C0" = { size = 0x10 }`; body+reg | Run 011 passed; its former `13919` suppressions were absent from Harvest 003 |
| 002 | `[0x8288ACB0,0x8288ACC0)` | `0x10` | **LIKELY PRIMARY; CONFIRMED omission** | `r3` virtual thunk, slot `0x14`; `.rdata` `0x82009548`, slot 20 of `[0x820094F8,0x8200954C)` | caller `0x8288BBB0`, LR `0x8288BBB4` | `"0x8288ACB0" = { size = 0x10 }`; body+reg | Run 011 passed |
| 002 | `[0x8288ACC0,0x8288ACD0)` | `0x10` | **LIKELY PRIMARY; CONFIRMED omission** | `r3` virtual thunk, slot `0x08`; `.rdata` `0x8200953C`, slot 17 of the same table | caller `0x8288B318`, LR `0x8288B31C` | `"0x8288ACC0" = { size = 0x10 }`; body+reg | Run 011 passed |
| 002 | `[0x82964820,0x82964830)` | `0x10` | **CONFIRMED omission; original fault quality POSSIBLE SECONDARY** | `r3` virtual thunk, slot `0x64`; materialized at `0x82961170/0x82961178` and passed to `0x82962858` | caller `0x8227DD3C`, LR `0x8227DD40` | `"0x82964820" = { size = 0x10 }`; body+reg | Run 011 passed; absent from Harvest 003 |
| 002, 003 | `[0x82C8A920,0x82C8A93C)` | `0x1C` | **HIGH CONFIDENCE PRIMARY; CONFIRMED omission** | Conditional type-3 copier; `.rdata` `0x8200E920`, slot 26 of callback table `[0x8200E8B8,0x8200E940)`; runtime object-vtable slot `0x20` | caller `0x82480814`, LR `0x82480818` | `"0x82C8A920" = { size = 0x1C }`; body `fable2_recomp.93.cpp`, body+reg | Run 011 passed |
| 002, 003 | `[0x82967540,0x82967550)` | `0x10` | **HIGH CONFIDENCE PRIMARY; CONFIRMED omission** | `r3` virtual thunk, slot `0x98`; materialized at `0x826ECA60/0x826ECA68` and `0x82964DCC/0x82964DD4` | caller `0x826EE58C`, LR `0x826EE590` | `"0x82967540" = { size = 0x10 }`; body `fable2_recomp.67.cpp`, body+reg | Run 011 passed |
| 002, 003 | `[0x82DE2BA8,0x82DE2BC4)` | `0x1C` | **LIKELY PRIMARY; CONFIRMED omission** | Argument adapter, then vtable slot `0x24`; selected by runtime-populated table in `0x82E060F8` at `0x82E06168-0x82E06194` | direct caller `0x82D8E93C -> 0x82E060F8`; preserved LR `0x82D8E940` across the tail dispatch | `"0x82DE2BA8" = { size = 0x1C }`; body `fable2_recomp.105.cpp`, body+reg | Run 011 passed |
| 003 | `[0x82E8C8E8,0x82E8C92C)` | `0x44` | **LIKELY PRIMARY and immediate H3 blocker; CONFIRMED omission** | Boolean search predicate; `.rdata` `0x82002754`, slot 22 of callback table `[0x820026FC,0x82002784)`; runtime vtable slot `0x28` | caller `0x82E905AC`, LR `0x82E905B0` | `"0x82E8C8E8" = { size = 0x44 }`; body `fable2_recomp.112.cpp`, body+reg | Run 011 passed; no synthetic suppression loop |

## `0x82E8C8E8` conclusion

**CONFIRMED boundary:** `[0x82E8C8E8,0x82E8C92C)`, size `0x44` (17 PPC
instructions). `0x82E8C92C` is zero padding and the next generated function
starts at `0x82E8C930`.

**CONFIRMED table evidence:** exact pointer `0x82E8C8E8` is stored at
`.rdata` address `0x82002754`, slot 22 of
`[0x820026FC,0x82002784)`. The surrounding executable entries are registered
functions.

**CONFIRMED semantics:** the function reads an element count at `r3+8` and an
array at `r3+4`. For each object pointer it loads that object's field at
`+0x84` and compares it with `r4`. It returns `r3=1` at the first match and
`r3=0` only if the array is empty or no element matches.

At `0x82E905AC`, the caller invokes vtable slot `0x28`, then tests the low byte
of `r3` at `0x82E905B0`. On true, and when the matched entry's `+0x88` flag is
set, it invokes another object method through slot `0x54`. The enclosing code
continues while state at `r27+0x74` remains nonzero.

**STRONG INFERENCE:** diagnostic `RETURN_R3_ZERO` skipped the true-path method
that advances or clears this state, so the enclosing loop repeatedly queried
the same condition. Harvest 003 stopped at exactly `250000` suppressions for
this target. The closeout generated the real TU1 predicate; Run 011 was an OFF
build with no poisoning/suppression path and did not enter that artificial
loop.

## Reviewed indirect-function candidates

Every promoted row below has a confirmed 16-byte, four-instruction virtual
thunk boundary, no fallthrough/overlap conflict, and explicit table or callback
construction evidence. Analyzer confidence alone was not used as proof.

| Confirmed TU1 range | Independent evidence | Result |
|---|---|---|
| `[0x82C00A98,0x82C00AA8)` | `r3` thunk slot `0x04`; exact pointer at `0x82009538`, slot 16 of `[0x820094F8,0x8200954C)`; slots 17–20 are confirmed neighboring thunks | **CONFIRMED; promoted** |
| `[0x826EE730,0x826EE740)` | `r3` thunk slot `0x50`; materialized at `0x826EC9C8/0x826EC9D0`, passed in `r6` to `0x826EC9DC -> 0x826ED7C0`; between registered thunks `0x826EE720` and `0x826EE740` | **CONFIRMED; promoted** |
| `[0x82964800,0x82964810)` | `r3` thunk slot `0x5C`; materialized at `0x829610D8/0x829610E0`, passed in `r6` to `0x829610EC -> 0x82962858`; member of contiguous `0x829647C0-0x82964830` thunk family | **CONFIRMED; promoted** |
| `[0x82964810,0x82964820)` | `r4` thunk slot `0x88`; materialized at `0x829611BC/0x829611C4`, passed in `r6` to `0x829611D0 -> 0x82962A18`; bounded by confirmed sibling thunks | **CONFIRMED; promoted** |
| `[0x82967530,0x82967540)` | `r4` thunk slot `0x54`; materialized at `0x82964BB8/0x82964BC0`, passed in `r6` to `0x82964BCC -> 0x82965910` | **CONFIRMED; promoted** |
| `[0x82967550,0x82967560)` | `r4` thunk slot `0xA4`; materialized at `0x82964EB0/0x82964EB8`, passed in `r6` to `0x82964EC4 -> 0x82966730` | **CONFIRMED; promoted** |
| `[0x82967570,0x82967580)` | `r4` thunk slot `0x5C`; materialized at `0x82964C04/0x82964C0C`, passed in `r6` to `0x82964C18 -> 0x82965910` | **CONFIRMED; promoted** |
| `[0x82967580,0x82967590)` | `r3` thunk slot `0x90`; materialized at `0x82964D80/0x82964D88`, passed in `r6` to `0x82964D94 -> 0x82966320` | **CONFIRMED; promoted** |
| `[0x82967590,0x829675A0)` | `r3` thunk slot `0xA0`; materialized at `0x82964E64/0x82964E6C`, passed in `r6` to `0x82964E78 -> 0x82965B10` | **CONFIRMED; promoted** |
| `[0x829675A0,0x829675B0)` | `r3` thunk slot `0xB0`; materialized at `0x8296502C/0x82965034`, passed in `r6` to `0x82965040 -> 0x82965B10` | **CONFIRMED; promoted** |
| `[0x8305DA68,0x8305DA78)` | `r3` thunk slot `0x258`; materialized at `0x83066F44/0x83066F54` and `0x83067024/0x83067034`, then passed in `r4` to common helper `0x830667B8` | **CONFIRMED; promoted** |
| `[0x8305DA78,0x8305DA88)` | `r3` thunk slot `0x278`; materialized at `0x83066B5C/0x83066B6C`, call `0x83066B74 -> 0x830667B8` | **CONFIRMED; promoted** |
| `[0x8305DA88,0x8305DA98)` | `r3` thunk slot `0x26C`; materialized at `0x83066E0C/0x83066E1C`, call `0x83066E24 -> 0x830667B8` | **CONFIRMED; promoted** |
| `[0x8305DA98,0x8305DAA8)` | `r3` thunk slot `0x27C`; materialized at `0x83066E5C/0x83066E6C`, call `0x83066E74 -> 0x830667B8` | **CONFIRMED; promoted** |
| `[0x8305DAA8,0x8305DAB8)` | `r3` thunk slot `0x260`; materialized at `0x83067224/0x83067234`, call `0x8306723C -> 0x830667B8` | **CONFIRMED; promoted** |
| `[0x8305DAB8,0x8305DAC8)` | `r3` thunk slot `0x270`; materialized at `0x830669E4/0x830669F4`, call `0x830669FC -> 0x830667B8` | **CONFIRMED; promoted** |
| `[0x8305DAC8,0x8305DAD8)` | `r3` thunk slot `0x280`; materialized at `0x8306743C/0x8306744C`, call `0x83067454 -> 0x830667B8` | **CONFIRMED; promoted** |
| `[0x8305DAD8,0x8305DAE8)` | `r3` thunk slot `0x264`; materialized at `0x83066C3C/0x83066C4C`, call `0x83066C54 -> 0x830667B8` | **CONFIRMED; promoted** |
| `[0x8305DAE8,0x8305DAF8)` | `r3` thunk slot `0x274`; materialized at `0x83066A34/0x83066A44`, call `0x83066A4C -> 0x830667B8` | **CONFIRMED; promoted** |
| `[0x8305DAF8,0x8305DB08)` | `r3` thunk slot `0x284`; materialized at `0x83066EAC/0x83066EBC`, call `0x83066EC4 -> 0x830667B8` | **CONFIRMED; promoted** |

### Inspected but not promoted

- `[0x8305DA48,0x8305DA68)` is valid PPC and resembles an alternate adapter
  entry beside generated `sub_8305DA28` and the existing callable internal
  entry `0x8305DA34`. The current analyzer found no exact pointer or conservative
  materialization for `0x8305DA48`. **UNRESOLVED / callable-internal-entry
  possibility:** not promoted because table/reference provenance is
  insufficient and overlap semantics need dedicated control-flow evidence.
  Promotion would require an executable-pointer reference or runtime target,
  plus confirmation that it is independently callable rather than only an
  alternate internal entry.
- The analyzer's global `confidence=REVIEW` materialization list was not bulk
  investigated or added. Those entries are not high-confidence findings:
  materialization alone does not prove a function boundary or callback-table
  role. Each still requires the same boundary, overlap, and pointer-provenance
  review used above.

No named high-confidence candidate from the requested review list remained
unpromoted: each was independently bounded and tied to a proven table or
callback-construction site.

## Commands and closeout validation

Candidate analysis (the `--target` option was repeated for each reviewed
address group):

```powershell
python .\tools\Find-IndirectFunctionCandidates.py `
    --dump .\out\fault-walk-runs\iteration-08\tu1-text-0x82000000.bin `
    --manifest .\fable2_manifest.toml `
    --generated-init .\generated\default\fable2_init.cpp `
    --target 0x82C8A920 `
    --target 0x82967540 `
    --target 0x82DE2BA8 `
    --target 0x82E8C8E8
```

Codegen, builds, and normal run:

```powershell
fable2-codegen
fable2-build
cmake --build --preset win-amd64-fault-walk-dispatch-release
cmake --build --preset win-amd64-fault-walk-release
fable2-run
```

Generated-body and dispatcher checks used exact patterns equivalent to:

```powershell
rg -n 'DEFINE_REX_FUNC\(sub_82E8C8E8, 0x82E8C8E8, false\)' .\generated\default
rg -n '\{ 0x82E8C8E8, sub_82E8C8E8 \},' .\generated\default\fable2_init.cpp
```

The check was repeated for all 24 closeout manifest additions and failed the
task if either pattern was absent. Result: `24/24` bodies and `24/24`
registrations present. Generated instruction counts for the four Harvest 003
functions were `7`, `4`, `7`, and `17`, matching sizes `0x1C`, `0x10`, `0x1C`,
and `0x44`.

ReXGlue synthetic tests:

```powershell
cmake --build --preset win-amd64-release --target fault_walk_synthetic_enabled fault_walk_synthetic_disabled fault_walk_dispatch
ctest --preset win-amd64-release -L fault_walk --output-on-failure
```

Result on `2026-08-28`: `3/3` passed:

- `fault_walk.synthetic_enabled` — passed
- `fault_walk.synthetic_disabled` — passed
- `fault_walk.dispatch_only` — passed

Normal, DISPATCH_ONLY, and FULL Fable release builds all linked successfully.
No FULL gameplay harvest was run.

### Normal Run 011

- Command: `fable2-run`
- Log: `C:\Dev\Fable2Recomp\fable2-run-011.log`
- Mode: OFF / normal non-fault-walk
- XEX patch: `0.0.0.26 -> 0.0.1.26`
- Observable progression: coherent user-controlled gameplay, at least the
  previously verified normal gameplay baseline
- Preserved captures:
  `out\normal-validation-runs\harvest-003-closeout-current.png` and
  `out\normal-validation-runs\harvest-003-closeout-final-state.png`
- `[FWT]`: none
- `[FATAL]`: none
- Invalid/unregistered target fatal: none
- Host AV/divide diagnostic: none
- `0x82E8C8E8` synthetic suppressions: impossible in OFF mode; no artificial
  250000-call loop observed
- Shutdown: normal `CloseMainWindow`, followed by
  `Window closing, shutting down...` and
  `Title terminated; hard-exiting process.`
- Exit code: `0x00000000`
- First new blocker: none observed

## Current remaining state

- First new normal blocker: none in Run 011. The process reached coherent
  gameplay and exited normally with `0x00000000`.
- The known Harvest 001–003 discovery omissions and the 20 proven sibling
  candidates are now explicit manifest functions with generated bodies and
  dispatcher registrations.
- The wider systematic discovery gap remains: non-RTTI callback arrays,
  code-materialized callbacks, and runtime-populated dispatch tables are not
  all automatically fed into function discovery. The reviewed manifest remains
  safer than speculative global insertion.
- `[0x8305DA48,0x8305DA68)` remains unresolved as described above.
- State-corruption warning remains essential for future harvesting: synthetic
  returns can redirect state, and FULL does not roll back guest memory.
- Harvest 004 was not started during this closeout.
- Closeout source changes are `fable2_manifest.toml` and this document.
  Generated files are regenerated build artifacts and are ignored by Git.
- Preserve unrelated existing SDK worktree state under `thirdparty/libmspack`;
  the fault-walker work did not modify it.
- No commit or push was made by this closeout.
