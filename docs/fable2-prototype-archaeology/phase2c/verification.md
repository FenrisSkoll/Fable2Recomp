# Provisional Phase 2C verification

This is a checkpoint verification record, not a completed Phase 2C gate.
The generator and report keep `phase_complete=false`.

The exact supplied Phase 2B branch, HEAD and tree were verified before the
Phase 2C branch was created. Phase 1 verification and section/report consistency,
Phase 2A verification with tool commit
`5f96fcf81bf9511dabadc63326468d9de94f87da`, both exhaustive artifact checks,
and full Phase 2B semantic replay passed before consuming the evidence. All
three closed schema verifiers passed. Closed Phase 2B's branch restriction was
not weakened to run its generator on Phase 2C. Its input/output identities are
instead rehashed by every Phase 2C command.

Completed checkpoint checks:

| Check | Result |
| --- | --- |
| `python -m unittest discover -s tests -q` | 227 tests passed, including 39 Phase 2C tests |
| `verify-audit` | byte-identical full 15,299-pair audit |
| `verify-candidates` | byte-identical 21,350-context candidate application |
| `verify-september` | byte-identical 45,707 terminals and 9,600 original-policy accepted pairs |
| `verify-freeze` | byte-identical six-artifact mapping freeze; effective count 15,382 |
| `verify-semantics` | byte-identical semantic, registration, script, type/global, preservation and intersection outputs |
| Phase 2C PowerShell schema verifier | 17 JSON documents passed local schema validation |
| Phase 1 close-out recheck | 1,184 immutable files, ten artifacts, three builds, fifteen section aliases |
| Phase 2A exhaustive consistency recheck | both exhaustive artifact identities preserved |
| Canonical function-map validator | 42,462 functions, exact-image match |
| Current closure verifier | 35,626 candidates, 54 strong, 180 probable, three fixtures |
| Both committed ownership ledgers | existing `Fable2OwnershipCorroboration.validate` passed |
| Manual-001, manual-002 and current merged compact summaries | existing `Fable2IndirectTargets.validate_summary` passed |
| Current coverage/import plan | existing `Fable2IndirectTargets.validate_plan` passed |
| Forbidden-path / SDK audit | only Phase 2C paths; SDK branch/HEAD/tree/remotes/status and fifteen libmspack hashes preserved |

The full discovery command includes the supported function-map, closure,
ownership, coverage and indirect-target regression suites. It executes no game.

One historical reproduction command failed, and remains failed:

```powershell
python tools/Fable2OwnershipCorroboration.py --phase4-directory out/ownership-corroboration/phase4-run1 --closure out/ownership-corroboration/closure-run1/entrypoint-closure.json --guest-snapshot out/phase3-regression-closure-final-smoke/iteration-01/tu1-text-0x82000000.bin --output-directory docs/fable2-discovery-pipeline/ownership --check
```

Exit code 1: `FAIL: stale manifest`. That historical plan binds the old
80-entry manifest SHA-256
`E3EB39CA153E396D5DC53E6F943ED8FF7AF1D6B0704EB860836BD7D21A3F87B0`.
The unchanged Phase 2B starting checkout's current manifest hashes to
`EF1656D77D270F207C4A16D3B92D5B86C4414CE38292D079AEF52B120CE778E1`.
The old plan was neither rebound nor regenerated, and the invariant was not
weakened. Passing ledger validation is recorded separately from this failed
historical reconstruction.

The required fixture matrix is not yet complete. In particular, complete
compiler-transformation recovery, feature-class ablation, typed-object
discrimination and native Lua-state ownership remain unfinished. Do not infer
cross-build accuracy from passing synthetic fixtures or schema validation.
