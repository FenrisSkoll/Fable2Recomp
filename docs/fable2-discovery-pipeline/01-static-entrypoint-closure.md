# Fable II static entrypoint closure

This is the durable implementation and validation checkpoint for the first
version of the Fable II discovery pipeline. It is self-contained so a fresh
investigation can resume without chat history.

## Status and evidence level

As of 2026-08-29, a production, report-only static code-pointer and entrypoint
closure analyser is implemented in the canonical ReXGlue fork and wired into
the canonical Fable2Recomp repository.

CONFIRMED:

- the analyser consumes the same XEX plus sibling XEXP patch path as normal
  ReXGlue codegen;
- it hashes the source XEX, source XEXP, and the contiguous loaded post-patch
  guest image independently;
- the Fable provenance sidecar rejects the wrong executable or update before
  the expensive FunctionGraph pass;
- the command does not call a code writer or mutate `fable2_manifest.toml`;
- authoritative output is stable JSON sorted by guest address and evidence;
- two final runs emitted byte-identical authoritative JSON;
- all three required fixtures were independently rediscovered by static
  address-taken evidence at their exact existing ranges;
- positive, negative, determinism, limit, overlap, and non-mutation tests pass;
- current codegen, build, migration-ledger, ReXGlue, and fault-walk tests pass.

PROBABLE:

- the 55 `strong_new_function` and 178 `probable_new_function` records are a
  useful review queue for omitted functions;
- none of those 233 records is confirmed merely by being in that queue.

HYPOTHESIS:

- semantic interpretations beyond the recorded evidence remain hypotheses
  until TU1 disassembly/control flow or reproducible runtime behaviour confirms
  them.

No manifest entry was added, removed, resized, or stubbed. No
`RETURN_R3_ZERO` implementation was generated or proposed.

The next report-only evidence stage is documented in
[`02-ghidra-function-map.md`](02-ghidra-function-map.md). It adds the shared
schema-2 executable-memory fingerprint and imports Ghidra/XEXLoader maps
without treating Ghidra names or boundaries as authoritative.

## Canonical repositories and commits

Fable2Recomp:

- path: `C:\Dev\Fable2Recomp`
- branch: `fable2-rexglue-0.10-migration`
- baseline: `f5b20ed2280d1b20a83522db82baeffa8301731f`
- integration: `a440a11b104e167909f6b497df2595f869106ed1`
- final SDK pin: `726200562358e603a8de9ff098fa7078402960ec`

ReXGlue SDK:

- path: `C:\Dev\rexglue-sdk-v0.10`
- branch: `fable2-v0.10-migration`
- baseline: `8f853c394b12cad7022086047981e861dd0efbea`
- analyser foundation: `4ba01162de12608835ce76a3d6bf69473d4c3417`
- conservative evidence refinement:
  `5a7ceb644e2e752c0666b91457848e821fae14de`
- installed version: `0.10.0.7-dev.g5a7ceb6`
- installed root:
  `C:\Dev\rexglue-sdk-v0.10\out\install\win-amd64`

The pre-existing dirty ReXGlue submodule state at `thirdparty/libmspack` was
not modified, staged, or committed.

The documentation commit containing this file can always be recovered without
self-referential hash editing:

```powershell
git log -1 --format=%H -- docs/fable2-discovery-pipeline/01-static-entrypoint-closure.md
```

## Exact TU1 image identity

Identity method:

```text
SHA-256 of source XEX, sibling XEXP and contiguous loaded post-patch guest image
```

| Property | Exact value |
|---|---|
| Base XEX SHA-256 | `88C4EF2E18E65409444D1B068EFF921D1F7E180A5AE64EDC64BA6B0872372662` |
| Title-update XEXP SHA-256 | `046A05693B4DA4437083C784000A850858B3BF992955C7DB30D518FB3E53E41C` |
| Contiguous loaded post-patch image SHA-256 | `BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00` |
| Image base | `0x82000000` |
| Image size | `0x01620000` |
| XEX entry point | `0x82CC21C0` |
| Title ID | `0x4D5307F1` |
| Media ID | `0x716F0A0D` |
| Patched version | `0.0.1.26` |
| Base version reported during patching | `0.0.0.26` |
| PE timestamp | `0x4A53C85A` |
| Timestamp as UTC | `2009-07-07 22:12:42 UTC` |

The earlier hash
`5A6A...` in historical investigation material described a partial
`0x01300000`-byte capture. It is not the full contiguous loaded-image identity
and must not replace the hash above.

### Loaded sections

Ranges use exclusive ends.

| Section | Range | Size | R | W | X |
|---|---|---:|:---:|:---:|:---:|
| `.rdata` | `0x82000600-0x8210B670` | `0x0010B070` | yes | no | no |
| `.pdata` | `0x8210B800-0x82165B20` | `0x0005A320` | yes | no | no |
| `BINKBSS` | `0x82165C00-0x82168508` | `0x00002908` | yes | no | no |
| `.text` | `0x82170000-0x832BABBC` | `0x0114ABBC` | yes | no | yes |
| `BINK` | `0x832BAC00-0x832CA03C` | `0x0000F43C` | yes | no | yes |
| `.data` | `0x832D0000-0x834FB98C` | `0x0022B98C` | yes | yes | no |
| `.lhmem` | `0x834FBA00-0x834FBA0C` | `0x0000000C` | yes | yes | no |
| `.XBMOVIE` | `0x834FBC00-0x834FBC0C` | `0x0000000C` | yes | yes | no |
| `.tls` | `0x834FBE00-0x834FBE19` | `0x00000019` | yes | yes | no |
| `.lhtrc` | `0x834FC000-0x834FC008` | `0x00000008` | yes | yes | no |
| `BINKDATA` | `0x834FC200-0x834FFF48` | `0x00003D48` | yes | yes | no |
| `.edata` | `0x83500000-0x83501D1D` | `0x00001D1D` | yes | no | no |
| `.idata` | `0x83510000-0x835104A6` | `0x000004A6` | yes | yes | no |
| `.XBLD` | `0x83520000-0x835200C0` | `0x000000C0` | yes | no | no |
| `.reloc` | `0x83520200-0x8361C968` | `0x000FC768` | yes | no | no |

The executable ranges are exactly:

```text
0x82170000-0x832BABBC  .text
0x832BAC00-0x832CA03C  BINK
```

Private XEX, XEXP, guest dump, section bytes, and byte-equivalent
reconstructions remain local and ignored. The committed sidecar contains only
hashes, guest addresses, sizes, classifications, and provenance.

## Architecture

The analyser extends ReXGlue instead of building a parallel loader or decoder:

```text
fable2_manifest.toml
  -> CodegenPipeline::CreateEntrypoint
  -> normal Runtime/XexModule load
  -> sibling XEXP TU1 patch application
  -> section/export/TLS/relocation metadata
  -> CodegenPipeline::RunAnalyze
  -> BinaryView + cached DecodedBinary + FunctionGraph
  -> entrypoint evidence producers
  -> bounded candidate CFG validation
  -> closure fixpoint
  -> deterministic reports only
```

Reused production components include:

- `XexModule` for XEX loading and XEXP patching;
- `BinaryView` for loaded guest sections and address permissions;
- `DecodedBinary` and the production PPC decoder;
- `FunctionGraph`, function authorities, basic blocks, labels, direct calls,
  tail calls, jump-table targets, and exception metadata;
- `VTableScanner` for RTTI-backed virtual tables;
- the manifest parser and normal game-root/module setup.

`CodegenPipeline::CreateEntrypoint` creates the same loaded project context but
does not create a `ProjectRecompiler` writer. The production overload of
`AnalyzeEntrypointClosure` reuses the decoder cache already populated by
`RunAnalyze`; it does not decode the TU1 image a second time.

### ReXGlue files

The two SDK commits change or add:

- `include/rex/codegen/entrypoint_closure.h`
- `src/codegen/entrypoint_closure.cpp`
- `src/rexglue/commands/entrypoint_closure_command.h`
- `src/rexglue/commands/entrypoint_closure_command.cpp`
- `include/rex/codegen/binary_view.h`
- `src/codegen/binary_view.cpp`
- `include/rex/codegen/codegen.h`
- `src/codegen/codegen.cpp`
- `include/rex/system/binary_types.h`
- `include/rex/system/xex_module.h`
- `src/system/xex_module.cpp`
- `src/codegen/CMakeLists.txt`
- `src/rexglue/CMakeLists.txt`
- `src/rexglue/main.cpp`
- `tests/unit/CMakeLists.txt`
- `tests/unit/codegen/entrypoint_closure_test.cpp`

### Fable2Recomp files

- `CMakeLists.txt` pins `0.10.0.7-dev.g5a7ceb6`;
- `tools/Invoke-Fable2EntrypointClosure.ps1` resolves the installed SDK from
  the normal release CMake cache and runs the CLI;
- `tools/fable2-entrypoint-closure-evidence.json` is schema-1 Fable identity,
  manual evidence, and fixture metadata;
- `tools/Verify-Fable2EntrypointClosure.py` checks the authoritative report;
- this document is the durable architecture and validation checkpoint.

The local `AGENTS.md` operational command reference also contains the helper
invocation, but that file is intentionally excluded by this checkout's
`.git/info/exclude`. This versioned document is the portable source of truth.

## Evidence schema and API contract

The authoritative model is:

```text
schema_version  = 1
analyzer_version = 1.0.0
```

The C++ API is declared by `rex/codegen/entrypoint_closure.h`:

```cpp
EntrypointClosureReport AnalyzeEntrypointClosure(
    const BinaryView& binary,
    EntrypointClosureInput input);

EntrypointClosureReport AnalyzeEntrypointClosure(
    const CodegenContext& context,
    EntrypointClosureInput input);

Result<void> WriteEntrypointClosureReports(
    const EntrypointClosureReport& report,
    const EntrypointClosureRunMetadata& runMetadata,
    const std::filesystem::path& outputDirectory,
    bool writeReviewToml = true);

std::string SerializeEntrypointClosureJson(
    const EntrypointClosureReport& report);
```

The versioned JSON contains:

- exact image identity and identity method;
- section permission records and executable ranges;
- configured limits;
- trusted and preliminary function ranges, authority, boundary provenance,
  blocks, labels, jump-table targets, exception entries, and direct edges;
- global direct edges and indirect sites;
- every candidate, proposed range, classification, confidence, decoded first
  instruction, known-range relationship, boundary provenance, blocks, edges,
  indirect sites, evidence, conflicts, rejections, and limit flags;
- fixpoint iterations;
- analysis-limit and producer diagnostics;
- fixture results and manifest comparison counts;
- report-only safety assertions.

Volatile command line, elapsed time, and peak working set are deliberately kept
in `entrypoint-closure-run.json` and do not affect stable JSON.

### Evidence identifiers

Implemented identifiers:

```text
xex_entrypoint
pe_export
tls_callback
pdata_function
pdata_exception
direct_branch_link
inter_function_tail_branch
relocation_backed_pointer
readonly_code_pointer
writable_code_pointer
pointer_table_run
rtti_vtable
callback_table
code_materialization_xref
existing_manifest
manual_verified
fault_walker_verified
abi_helper
rexglue_discovered
```

Reserved, non-producing extension identifiers:

```text
reserved_ghidra_import
reserved_jump_table_recovery
reserved_xenia_trace
reserved_runtime_bulk_import
```

Every evidence record retains kind, target address, optional source and storage
addresses, source section, producer provenance, and structured attributes.
Candidate order is ascending guest address. Evidence order is deterministic by
target, kind, storage, source, section, provenance, and attributes.

## Discovery and validation policy

### Trusted and preliminary seeds

The FunctionGraph bridge carries:

- current manifest functions;
- `.pdata` functions and exception information;
- XEX entrypoint, PE exports, and TLS callbacks;
- direct `bl` targets and resolved/unresolved inter-function tail branches;
- ReXGlue-discovered, RTTI-vtable, and ABI-helper functions;
- manual and fault-walker evidence from the versioned sidecar;
- `GAP_FILL` ranges as preliminary, never trusted boundaries.

Ordinary intra-function branch targets are not seeded as functions.

### Static address-taken producers

The analyser scans aligned readable storage as big-endian 32-bit values and
requires four-byte alignment plus membership in an executable range. It scans
read-only and writable storage. Inline executable-section pointer runs require
at least three contiguous entries; other runs require at least two.

Generic raw-pointer scanning excludes `.pdata`, `.reloc`, `.edata`, `.idata`,
and `.XBLD` so PE/XEX metadata is handled by its semantic producer rather than
double-counted as arbitrary pointers.

For every retained pointer it records storage, target, section permissions,
neighbouring values, run start/end/slot, relocation status, RTTI status, and
code xrefs where available. A singleton raw pointer is not enough for a strong
function classification.

`callback_table` is emitted only for a non-RTTI, non-executable pointer run
whose table address is itself materialized by PPC code. A raw non-RTTI run
without a code xref remains `pointer_table_run` evidence and does not receive a
callback label.

PPC `lis` plus bounded `addi` or `ori` materialization is recognized within the
configured instruction window. Destination register, high site, low site, and
form are recorded. Materializations may target executable code directly or
pointer/table storage.

### Candidate CFG traversal

For unowned candidates, bounded traversal uses the production decoder and:

- rejects unaligned or non-executable addresses;
- rejects immediately invalid first instructions;
- does not require a conventional prologue;
- records predecessor fallthrough into owned blocks;
- records direct and indirect sites;
- stops at returns, indirect transfers, external tail branches, trusted
  boundaries, invalid instructions/data, and configured limits;
- derives a range from visited blocks and termination evidence, never merely
  from the next arbitrary candidate;
- rejects overlaps with trusted functions and non-boundary mid-block targets;
- recognizes owned labels/basic-block starts, jump-table cases, and exception
  landing pads;
- cross-links every overlap among strong/probable/ambiguous proposed ranges.

The 407 proposed-range overlap pairs in the current TU1 report are preserved as
candidate conflicts. They are not automatically resolved because shared tails,
callable internal entries, and incorrect preliminary ownership require review;
the report does not choose an arbitrary winner.

### Classifications

| Classification | Policy |
|---|---|
| `confirmed_existing_function` | Exact existing FunctionGraph entry plus independently collected candidate evidence; range comes from the existing graph and records that provenance. |
| `strong_new_function` | Complete bounded traversal plus reliable entry/call evidence, RTTI or relocation evidence, or at least two distinct corroborating kinds. |
| `probable_new_function` | Complete bounded traversal plus tail-call or one corroborating kind. |
| `callable_mid_function_entry` | Address-taken owned label or block start inside an existing trusted function. |
| `jump_table_case` | Address is an owned target from the existing jump-table model. |
| `exception_landing_pad` | Address is owned exception/filter/handler landing code. |
| `ambiguous_code_pointer` | Code pointer remains plausible but traversal/evidence cannot support a function classification. |
| `rejected_non_code` | Production PPC decoder rejects the first instruction. |
| `rejected_overlap` | Target is mid-block, predecessor fallthrough disproves a boundary, or its proposed range overlaps trusted ownership. |
| `rejected_out_of_range` | Address is unaligned or outside executable ranges. |

Manual or fault-walker metadata does not by itself satisfy fixture independence.
Fixture rediscovery requires static address-taken evidence from relocation,
read-only/writable pointer, pointer run, RTTI vtable, callback table, or code
materialization. Existing-manifest evidence is excluded from that decision.

### Fixpoint and limits

Each iteration:

1. validates all current candidates;
2. exposes direct-call and inter-function tail targets from traversal;
3. merges new targets and evidence;
4. reclassifies affected candidates;
5. stops only when candidate count, evidence, and classifications are stable.

Current defaults:

| Limit | Value |
|---|---:|
| iterations | `12` |
| candidates | `100000` |
| instructions per candidate | `4096` |
| traversal depth | `256` |
| pointer-run entries | `4096` |
| materialization window | `8` instructions |

Exhausting any `max_*` limit produces a diagnostic and a non-zero CLI result.
The current production graph already exposes its direct targets before closure,
so the private TU1 input reached a stable fixpoint in iteration 1 with zero new
targets/evidence during that iteration. Synthetic tests require multiple
iterations and prove new direct-call discovery and reclassification.

## CLI and reports

Normal command:

```powershell
.\tools\Invoke-Fable2EntrypointClosure.ps1
python .\tools\Verify-Fable2EntrypointClosure.py
```

Direct equivalent:

```powershell
C:\Dev\rexglue-sdk-v0.10\out\install\win-amd64\bin\rexglue.exe `
    entrypoint-closure `
    .\fable2_manifest.toml `
    --provenance .\tools\fable2-entrypoint-closure-evidence.json
```

Output:

```text
out/analysis/BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00/
  entrypoint-closure.json
  entrypoint-closure.csv
  entrypoint-closure.md
  entrypoint-closure-review.toml
  entrypoint-closure-run.json
```

`entrypoint-closure.json` is authoritative. CSV and Markdown are review views.
The TOML file starts with an explicit review-only warning and is never loaded or
applied. `--no-review-toml` suppresses it. `--output` changes only the report
directory. Limit switches are visible in `entrypoint-closure --help`.

Final stable output identities:

| File | Bytes | SHA-256 |
|---|---:|---|
| `entrypoint-closure.json` | `287901675` | `CF6C89A6D4750E95A1FA261F372B53FA39937A3885D5DC44C9F6818D2E7C7334` |
| `entrypoint-closure.csv` | `11291999` | `BE4402B859FADB952A8A507ECB16B2F8C1957BF2AFAFAA215C77D5903B1A15B6` |
| `entrypoint-closure.md` | `29202` | `7237AD0D40FC8CCF494C5B243BF4FFBC892413ECF5C375661D01060124A3B08C` |
| `entrypoint-closure-review.toml` | `14253` | `F38F72D48C1A0961B5A831CC9348FA3447ECB989E4EB568F7B47701D7C587248` |

The manifest remained:

```text
fable2_manifest.toml SHA-256 E3EB39CA153E396D5DC53E6F943ED8FF7AF1D6B0704EB860836BD7D21A3F87B0
```

The command hashes the manifest before and after report generation and fails if
the bytes differ. The unit suite also writes a sentinel manifest outside the
output directory and proves report generation leaves it unchanged.

## Private TU1 results

### Counts

| Record | Count |
|---|---:|
| trusted function ranges | `51327` |
| preliminary `GAP_FILL` ranges | `9326` |
| candidate entrypoints | `35626` |
| pointer storage sites | `58676` |
| pointer runs | `2715` |
| relocation-backed storage sites | `0` |
| PE exports | `175` |
| TLS callbacks | `0` |
| indirect sites | `2201` |
| proposed candidate-range overlap pairs | `407` |

Classification totals:

| Classification | Count |
|---|---:|
| `confirmed_existing_function` | `27840` |
| `strong_new_function` | `55` |
| `probable_new_function` | `178` |
| `callable_mid_function_entry` | `86` |
| `jump_table_case` | `6085` |
| `exception_landing_pad` | `113` |
| `ambiguous_code_pointer` | `7` |
| aggregate rejected candidates | `1262` |
| `rejected_non_code` | `16` |
| `rejected_overlap` | `997` |
| `rejected_out_of_range` | `249` |

The `55 + 178` review queue is not a manifest patch. Each proposed boundary and
each of the 407 conflicts must be reviewed against TU1 control flow before any
separate manifest edit.

### Acceptance fixture: `0x829647F0`

Verified range and meaning:

```text
0x829647F0-0x82964800  size 0x10  virtual-dispatch leaf thunk
JSON size: 0x00000010
```

Report classification:

```text
confirmed_existing_function
confidence: confirmed
known range: exact_existing_entry
boundary: existing_function_graph_range+independent_address_taken_evidence
```

Independent static chain (`code_materialization_xref`):

| High site | Low site | Form | Destination |
|---|---|---|---|
| `0x82961254` | `0x8296125C` | `lis/addi` | `r6` |
| `0x82964B6C` | `0x82964B74` | `lis/addi` | `r6` |
| `0x8296571C` | `0x82965730` | `lis/addi` | `r29` |

The candidate also retains `existing_manifest`, `manual_verified`, and
`fault_walker_verified`; those records corroborate history but are excluded
from the independent-static pass condition. There is no pointer storage address
for this fixture.

### Acceptance fixture: `0x829675E0`

Verified range and meaning:

```text
0x829675E0-0x829675F0  size 0x10  virtual-dispatch leaf thunk
JSON size: 0x00000010
```

Report classification and boundary provenance are the same as the prior
fixture. Independent static chain (`code_materialization_xref`):

| High site | Low site | Form | Destination |
|---|---|---|---|
| `0x829650C4` | `0x829650CC` | `lis/addi` | `r6` |
| `0x82966B4C` | `0x82966B60` | `lis/addi` | `r29` |

The candidate also retains `existing_manifest`, `manual_verified`, and
`fault_walker_verified`. There is no pointer storage address for this fixture.

### Acceptance fixture: `0x82C03B28`

Verified range and meaning:

```text
0x82C03B28-0x82C03B44  size 0x1C
conditional callback leaf reached through callback-table bctrl
JSON size: 0x0000001C
```

Report classification:

```text
confirmed_existing_function
confidence: confirmed
known range: exact_existing_entry
boundary: existing_function_graph_range+independent_address_taken_evidence
```

Independent pointer/table chain:

- big-endian target `0x82C03B28` is stored at `0x8200A190` in read-only
  `.rdata`;
- previous value: `0x828F75F8`;
- next value: `0x82C53A80`;
- pointer run: `0x8200A0E8-0x8200A328`;
- entries: `144`;
- fixture slot: `42`;
- evidence kinds: `readonly_code_pointer`, `pointer_table_run`, and
  xref-backed `callback_table`.

PPC materializations of the table start `0x8200A0E8`:

| High site | Low site | Form |
|---|---|---|
| `0x82C04364` | `0x82C0436C` | `lis/addi` |
| `0x82C044C4` | `0x82C044CC` | `lis/addi` |
| `0x82C04804` | `0x82C0480C` | `lis/addi` |
| `0x82C051FC` | `0x82C05204` | `lis/addi` |
| `0x82C0A11C` | `0x82C0A124` | `lis/addi` |
| `0x82C53A94` | `0x82C53A9C` | `lis/addi` |
| `0x82C5BEB0` | `0x82C5BEB4` | `lis/addi` |

The candidate also retains `existing_manifest`, `manual_verified`, and
`fault_walker_verified`. Its fixture result is `pass` only because the exact
range exists and the independent pointer/table chain is non-empty.

## Tests and validation record

### Initial baseline before editing

| Command | Result |
|---|---|
| `python .\tools\Verify-Fable2MigrationLedger.py` | PASS, all 32 Harvest 001-003 and sibling entries; `60416` definitions/declarations/mappings/registrations; `setjmp=0x83006C90`, `longjmp=0x82CAFA30`; `2.274 s` |
| `fable2-codegen` | PASS, zero generated writes; helper `0.982 s`, ReXGlue `0.2 s` |
| `fable2-build` | PASS, 301 steps; `40.265 s` |
| SDK `ctest -L fault_walk` | PASS, 3/3; `0.53 s` |
| `python .\tools\Find-IndirectFunctionCandidates.py ...` | PASS for all three historical fixtures; `4.068 s` |

The historical Python helper was baseline corroboration only. The production
fixture results above come from the new ReXGlue analyser and full live patched
image.

### Final SDK tests

```powershell
cmake --preset win-amd64
cmake --build --preset win-amd64-release
ctest --test-dir .\out\build\win-amd64 `
    -C Release `
    --output-on-failure `
    --parallel 8
```

Final result at `5a7ceb644e2e752c0666b91457848e821fae14de`:

```text
100% tests passed out of 1688
unit: 227
fault_walk/synthetic: 3
ppc: 1458
four pre-existing BitStream cases skipped
real test time: 8.19 s
```

Focused entrypoint-closure tests: 14/14 passed in `0.33 s`. They cover:

- big-endian singleton pointer handling;
- writable pointers, relocation metadata, and pointer runs;
- xref-required callback-table classification;
- PPC high/low materialization;
- exclusion of data-like PE metadata;
- prologue-free leaf thunks;
- direct-call fixpoint discovery and evidence-driven reclassification;
- XEX entrypoint, export, and TLS seeds;
- callable internal entries, jump-table cases, and exception landing pads;
- invalid, out-of-range, mid-block, trusted-range, and candidate-range
  overlaps;
- deterministic serialization and candidate truncation;
- safety-limit diagnostics;
- report-only manifest non-mutation.

### Final Fable checks

```powershell
python .\tools\Verify-Fable2MigrationLedger.py
fable2-codegen
fable2-build
python .\tools\Verify-Fable2EntrypointClosure.py
```

Results:

- migration ledger: PASS, all 32 records and `60416` generated symbols;
- final codegen: PASS in `0.489 s`;
- final incremental normal release build: PASS in `2.686 s`;
- report verifier: PASS, schema 1, analyser 1.0.0, exact identity, sorted
  candidates/evidence, fixpoint reached, no exhausted `max_*` limits, all
  three fixtures passed.

The private analyser was run twice after the final evidence refinement:

| Run | Wall time | Analysed time | Peak working set |
|---|---:|---:|---:|
| source-tree CLI, canonical output | `57.3 s` | `50971 ms` | `1066553344` bytes (`1017.145 MiB`) |
| installed SDK CLI, separate output | `57.453 s` | `51149 ms` | `1065979904` bytes (`1016.598 MiB`) |

Both authoritative JSON files have SHA-256
`CF6C89A6D4750E95A1FA261F372B53FA39937A3885D5DC44C9F6818D2E7C7334`.
Only `entrypoint-closure-run.json` differs, as intended.

Wrong-image validation used a temporary metadata-only sidecar with an all-zero
base-XEX hash. Exact result:

```text
Failed: Wrong image: base_xex_sha256 expected 0000000000000000000000000000000000000000000000000000000000000000, found 88C4EF2E18E65409444D1B068EFF921D1F7E180A5AE64EDC64BA6B0872372662 (after 0.3s)
wrong_image_exit_code=1
wrong_output_exists=False
```

### Runtime smoke

The established dispatch helper was run before the final report-only
xref/overlap refinement, which touched only analyser code and its tests:

```powershell
.\tools\Invoke-Fable2FaultWalk.ps1 `
    -Iteration 1 `
    -RunDirectory .\out\entrypoint-closure-validation
```

Exact result:

```text
run: fable2-run-014.log
build preset: win-amd64-fault-walk-dispatch-release
classification: PostInputTimeout
exit_code: 0x00000000
fault-walk mode: DISPATCH_ONLY
unique_faults: 0
poisoned_functions: 0
total_fault_hits: 0
total_suppressed_invocations: 0
```

The process was stopped gracefully after the configured post-input monitoring
window. Final SDK CTest subsequently passed all three fault-walk/synthetic tests
at commit `5a7ceb644e2e752c0666b91457848e821fae14de`.

This session did not perform a person-controlled interactive gameplay
regression and does not claim that it did. Xenia was not run because Xenia
tracing was explicitly out of scope for this stage.

## Known limitations and unresolved work

1. `.reloc` producer limitation: the loaded `.reloc` section at `0x83520200`,
   size `1034088` (`0x000FC768`), contains no structurally valid PE base-
   relocation blocks under the supported little- or big-endian layouts.
   `relocation_storage_sites=0`. The report records
   `pe_base_relocation_parse`; it does not fabricate relocation evidence.
2. The authoritative JSON is large (`287901675` bytes, `274.564 MiB`) because it
   retains 60,653 function ranges, 334,465 direct edges, per-function blocks,
   all candidates, and full structured evidence. Peak working set is about
   `1.0 GiB`. Persistent cross-run caching is not implemented; the in-process
   decoder is reused and output is keyed by exact image SHA/analyser version.
3. The 407 overlaps among proposed new ranges are recorded but deliberately not
   auto-resolved. They may represent callable internal entries, shared tails,
   or a wrong preliminary owner. Review TU1 CFG evidence before selecting a
   range.
4. Raw pointer-table membership is not semantic proof. Callback-table evidence
   now additionally requires a PPC code xref to the non-RTTI table. Manual
   dispatch structure semantics beyond this remain for review.
5. The analyser uses ReXGlue's existing jump-table model to classify known
   cases. It does not add new jump-table recovery.
6. No Ghidra import, Xenia trace import, runtime bulk import, or new jump-table
   producer exists. Their evidence IDs are reserved only.
7. The review TOML is intentionally non-authoritative. It must not be applied in
   bulk, and this pipeline has no manifest-writing API.

## Safest next integration point

Do not begin bulk manifest import. The next safe discovery step is a separate,
review-only triage tool over the authoritative JSON that:

1. selects `strong_new_function` records with no candidate-overlap conflict;
2. groups remaining records by pointer table and preliminary owner;
3. presents TU1 disassembly, block termination, xrefs, and conflicts for one
   candidate at a time;
4. requires an explicit reviewed boundary decision before producing any
   separate manifest patch;
5. preserves the existing report and provenance as immutable evidence.

That is the stable extension point for later work. Ghidra import, new
jump-table recovery, Xenia tracing, and runtime bulk import remain out of scope
until separately authorized and designed against schema 1.
