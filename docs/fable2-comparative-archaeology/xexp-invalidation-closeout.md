# CP-1: XEXP-only incremental invalidation

## Result

**PASS — generic fix implemented. CONFIRMED.** The original build could retain
stale generated source after a valid XEXP-only instruction change. Both its
filesystem dependency list and module content fingerprint omitted the patch.
The corrected SDK tracks executable inputs, optional-file existence and actual
tool/runtime file identities. Unchanged canonical inputs still reproduce all
591 generated C++/header files byte-for-byte.

This closes CP-1, a future incremental-correctness risk. It does not revise the
historical audit's finding that its canonical generated source was correct.
No gameplay, manifest, function ownership, renderer or loader behavior changed.
All commits are local; no push, remote merge, PR, tag, release or upload occurred.

## Repository and installed identities

Starting repositories:

| Repository | Branch | HEAD | Tree |
| --- | --- | --- | --- |
| Fable2Recomp | `main` | `eb222bd5fe94c00a6d77826b654ae96d09610475` | `e33f86d709f2793bf4e78c15028bd5c8427369f9` |
| SDK | `fable2-native-renderer-nr0c2b1gv-validation-closeout` | `18130a95c7790b4a9d3a2b30f601f247b1a7a864` | `c659bfaf3ff8fb32f5a17774ecabc6a9aa508544` |

Fable started clean. SDK started with only dirty `thirdparty/libmspack`, at
submodule HEAD `305907723a4e7ab2018e58040059ffb5e77db837`. Its fifteen dirty-file
SHA-256 values and status were captured before work and compared afterward.
All are unchanged. No submodule file was staged, reset, cleaned, stashed or
recommitted. The new [receipt](evidence/xexp-invalidation.json) retains starting
state, remotes, preservation checks and validation identities. Historical
`provenance.json`, `validation.json` and other audit evidence remain unchanged.

SDK local commits:

* `15cb43b6c0b3014598cdb0a343b76b5344041778` — Fix codegen invalidation for optional title deltas and tool identity.
* `3e1a37aa50a84a5f841305ec65a25b217805153d` — Fail closed when codegen dependency metadata is missing.
* `d30122381144fb341e447ee7b0862e330d1af252` — Bind codegen identity to the loaded runtime DLL rather than a static thunk.

Final SDK tree: `85ecee5c3ecb2212153c9ea7eb1ff0ef49abeccb`; branch unchanged,
only the same dirty submodule remains. The application closeout commit contains
this report, reproduced SDK-generated CMake glue and private-fixture tooling.
Its final commit/tree identity is provided in the handoff rather than embedding
a circular self-hash in this report.

The canonical installation received a **CLI-only update**, not a complete SDK
install. `out/install/win-amd64/bin/rexglue.exe` changed from
`D123A6AB2DC3C15EF0B2398E0ED6F4583C71948F3043A582B777BDBD9BDBBD52`
(`0.10.0.51-dev.gfc5a00b`) to
`F13E6E5AA6EFDC9AF6CC387E15977DFEDF81E15BFBEE123C76932E8DEA939AFF`
(`0.10.0.65-dev.gd301223`). Transient `.63` and `.64` tools were tested before
the metadata-loss and runtime-identity corrections; final validation and normal
builds use `.65`.

The package configuration, import libraries, installed/staged/probe runtime and
renderer DLLs were not replaced. The package pin remains
`0.10.0.51-dev.gfc5a00b`; this is intentional and must not be mistaken for the
serviced CLI's identity. Installed, probe-loaded and app-staged `rexruntime.dll`
remain `71BB1BA29413773226245B1D05F40379561C974F8E2EA4E5BB994D6DC3591793`.
The newly built SDK runtime was used by SDK unit tests but was not installed or
substituted into the canonical application. No full `cmake --install` ran.

## Actual dependency path

Normal `fable2-codegen` builds target `fable2_codegen`; normal `fable2-build`
orders the application and recompilation object library after that target.
`generated/rexglue.cmake` owns the custom command. Its first output is
`generated/default/codegen.build.stamp`, followed by generated compilation
sources. The command is `$<TARGET_FILE:rex::rexglue> codegen fable2_manifest.toml`.
CMake consumes `codegen.d` through `DEPFILE` and transforms it for Ninja.

`src/codegen/project_recompiler.cpp` collects inputs and calls
`src/codegen/output_stamp.cpp` to emit the depfile and stamps. Originally the
list covered configured XEX, manifest, loaded configuration files and custom
templates. It did not cover the sibling patch. `UserModule::LoadFromFile`
discovers the sibling dynamically by appending `p` to the resolved XEX path;
`XexModule::ApplyPatch` constructs the loaded executable image before analysis.

`codegen.stamp` originally hashed the incomplete file list, codegen flags,
embedded templates and SDK floor/channel (`0.10.0-dev`). It did **not** hash the
complete loaded image or actual tool/runtime binaries. `codegen.build.stamp`
contained module fingerprints and was rewritten after a successful invocation;
it was not a separate patched-image identity. The original CMake invocation
named the tool target but did not declare a tool file dependency.

These contracts are distinct:

| Contract | Corrected mechanism |
| --- | --- |
| Declared filesystem dependency | Existing inputs in `codegen.d`; explicit CMake `DEPENDS` |
| Optional input existence | Generated `codegen.inputs.cmake` exact-path `CONFIGURE_DEPENDS` globs |
| Loaded executable inputs | Resolved XEX plus append-`p` sibling, including an absent marker |
| Codegen semantic identity | File-content fingerprints, flags, templates and implementation binaries |
| Tool implementation | OS-identified executable and actual loaded runtime library content and file dependencies |
| Manifest/configuration | Existing manifest/config/template dependencies; unchanged version stamp no longer rewrites manifest |

All loaded modules' executable inputs participate in each module fingerprint
because they share the export resolver. The correction is in the SDK's generic
codegen and generated CMake template; it contains no Fable filename or address.
The application CMake diff is normal regeneration from that template.

## Reproduction and correction

Private fixtures live under ignored `out/xexp-invalidation/`. They copy base
XEX, delta, manifest, partition and codegen tool; canonical assets are never
mutated. `sources.cmake` seeds the normal output graph in the final integration
fixture. A completely cold graph otherwise legitimately gains generated
outputs after its first configure, causing one cached invocation as the build
graph settles. This bootstrap is distinct from the unchanged-input control.

The available prototype delta
`47156DAEA44999B5AB7F964B71442F98186D932BB946C73057799D51B43CA821`
was unsuitable: its source digest does not match this base, as already recorded
in Phase 1. It was not accepted as a valid mutation witness.

The controlled fixture verifies and decrypts the canonical delta's block chain,
appends one existing loader-supported copy-delta record, recomputes block links
and hashes, and emits an unencrypted patch body supported by the same loader.
Loaded headers/image snapshots remain private; no keys or binary bytes are
committed. It is a loader-test fixture, not a signed Xbox update.

| Identity | SHA-256 |
| --- | --- |
| Unchanged base XEX | `88C4EF2E18E65409444D1B068EFF921D1F7E180A5AE64EDC64BA6B0872372662` |
| Original XEXP | `046A05693B4DA4437083C784000A850858B3BF992955C7DB30D518FB3E53E41C` |
| Mutated XEXP | `CF5A17147BC5C2ABBD17A7254E6B2022D3224E0052F3EF3E08CD60005EA15F74` |
| Original loaded image | `BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00` |
| Mutated loaded image | `351FFD0C1BE5319B1F3D1595AE95530477ACAD95FFCC89DB07554EDBFDF46190` |
| Base-only loaded image | `B8F294DDAE3DA4A01DE455F5003CD1452D7C838EDC3DE1C166F3CAB9008B77A8` |

The copy changes instruction `0x82967544` in `sub_82967540` from `816c0098`
(`lwz r11,152(r12)`) to `816c005c` (`lwz r11,92(r12)`). Only private fixtures
contain this change. No guest instruction is executed by these tests.

**Original behavior: stale output reused.** Ninja invoked codegen because the
old CLI rewrote the manifest version stamp after every run, leaving it newer
than its completion stamp. That incidental invocation did not save correctness:
the loader applied the changed patch, but codegen reported
`0 written, 0 unchanged, 0 deleted, 1 module(s) up to date`. The source census
and semantic stamp were unchanged. A direct CLI invocation also skipped it.
The omission was therefore not harmless, even though invocation occurred.

**Corrected behavior:** Ninja identifies `game/default.xexp` as the dirty
dependency; codegen reports zero modules up to date and changes the semantic
stamp and only `fable2_recomp.291.cpp`. The changed generated instruction agrees
with the new loaded bytes. Subsequent unchanged builds perform no codegen
invocation and preserve source, manifest and stamp bytes.

Tool and runtime replacement are separately checked using valid PE overlays
appended only to private copies. This changes binary identity without changing the
algorithm: Ninja invokes codegen, the semantic stamp changes, sources remain
identical, and the next build is a no-op. This is a controlled binary-identity
test, not a claim to have rebuilt historical SDK implementations. The real
installed `.51` to fixed `.65` upgrade also regenerates unchanged canonical
source rather than trusting the old module stamp.

The synthetic SDK scheduler integration uses the production dependency,
fingerprint and output-stamp functions with private-free bytes. It proves
patch change, removal, absent no-op, re-addition and restored no-op using actual
invocation/generation counters and semantic output identities. Base-only loading
is independently confirmed with the real XEX. Removing the real patch under the
TU1-specific manifest must fail validation, rather than accept stale TU1 output;
restoration and its following no-op are also tested. A generic manifest without
TU1 overrides did not compile this title (eight unresolved calls), so no base
game codegen/parity claim is made and no guard was weakened.

A parent-directory depfile watch was experimentally rejected: Windows Ninja
missed patch creation. The CMake existence watch fixes that case without an
always-rebuild rule. Deleting its metadata now fails configuration explicitly;
direct codegen restores it. No-op codegen no longer replaces an already matching
manifest SDK stamp. Unreadable file identities cannot produce a reusable stamp.

The final review also rejected a function-address runtime locator: the anchor
resolved to a static copy/import thunk in the CLI. The corrected Windows path
uses CMake's configuration-specific runtime target filename to obtain the actual
loaded DLL handle and path. A regression now requires distinct executable and
runtime files, and the bounded integration separately changes a private runtime
DLL identity. No runtime loader implementation was changed to obtain this data.

## Validation and provenance

The [receipt](evidence/xexp-invalidation.json) contains exact commands, log hashes,
states and preservation evidence. Principal checks:

| Check | Result |
| --- | --- |
| SDK `[output_stamp]` tests | PASS: 21 cases, 48 assertions |
| SDK `codegen_dependency_scheduler` CTest | PASS: patch change/remove/add/no-op and metadata-loss recovery |
| SDK full `unit_tests.exe` | PASS: 361 passed, four existing explicit skips; 365 cases, 144449 passed assertions |
| Real loader/codegen XEXP-only integration | PASS |
| Private tool/runtime replacement and no-op | PASS |
| Current descendant Python subset | PASS: 350 tests |
| Comparative provenance negative controls | PASS: four tests |
| `python -B -X utf8 tools\Verify-Fable2EntrypointClosure.py` | PASS |
| Fresh tool/runtime load snapshots and provenance verifier | VERIFIED CONSISTENT |
| Fresh isolated generated comparison | PASS: all 591 files identical |
| `fable2-codegen`, `fable2-build`, unchanged `fable2-codegen` | PASS |
| Full historical Python discovery | FAIL: 449 tests, the same 11 frozen Phase 2E–2H errors |
| Gameplay execution / renderer behavior tests | NOT APPLICABLE: no gameplay/runtime/renderer behavior changes |

The historical failures remain README-bound sizes/identities, Phase 2G delta
allowlist and branch requirements, Phase 2H branch and SDK branch contracts.
They were not weakened or relabeled as passed. The current subset is explicitly
not the full historical suite.

Canonical loaded image remains
`BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00` in both
tool and runtime modes. The 591-file source inventory remains
`8506ED30A4021E7D735C344B237334315B551E6E7DA5CF3AA9ADB260093572FF`.
Canonical XEX, XEXP, manifest, partition, gameplay sources and historical audit
evidence are unchanged. Generated differences are dependency glue/metadata and
input stamps only, not C++/header output.

## Scope limits and handoff

Executed scheduler coverage is Windows/Ninja; POSIX implementation-path discovery
is implemented but not executed here. Filesystem scheduling follows normal
CMake/Ninja change detection, not adversarial same-size content replacement with
all timestamps restored. Direct CLI use compares content hashes. Private fixtures
and snapshots are intentionally not committed or distributable; their small
reproduction tools and public metadata are committed.

No remaining CP-1 blocker is identified. There is no new gameplay, translation,
renderer or full base-game parity claim. Next runtime work remains the existing
human progression/renderer capture plan, not a dependency workaround.

**XEXP INVALIDATION CONTRACT VERIFIED**
