# Phase 2E rollback

No default consumer was switched. Disable the overlay by omitting the explicit `opt-in` adapter invocation and selecting the unchanged default:

```powershell
python tools/phase2e/Fable2PrototypeOverlayConsumer.py default
```

The result must name `closed-phase2a-default`, report 15,299 rows and reproduce the exact Phase 2A source identity recorded in `out/prototype-archaeology/phase2e/rollback-verification.json`.

Stop using the overlay on any decision, delta or effective-map hash mismatch; an unexpected count; a duplicate donor or target; a dangling, circular, same-generation or suppressed dependency; a reintroduced suppressed route; lost reservation; unknown overlay version; canonical-name propagation; or any production side effect. The adapter refuses invalid opt-in data without fallback.

Rollback changes only the explicit analysis selection. It never deletes, rewrites, regenerates or rebinds Phase 1, Phase 2A, Phase 2B, Phase 2C or Phase 2D evidence. The committed receipt and compact delta remain durable audit records.
