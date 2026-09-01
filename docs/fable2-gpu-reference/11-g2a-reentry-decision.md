# G2A re-entry decision

> **Superseded current status:** **G2A RETIRED — DO NOT RESUME.** This chapter
> and its JSON companion preserve the dated G1.5D decision and the evidence
> available at that time; they no longer authorize a revision or later
> mechanism proof. See the [G2A retirement record](g2a-retirement.md).

The authoritative two-part decision is [`g2a-decision.json`](evidence/g2a-decision.json). This document does not resume G2A or authorize implementation.

## Part A — **REVISE G2A BEFORE RESUMING**

### Preserved-original design

The checkpoint at `47c2ea2b7d9e14b09fd942c4b5f1bd11c46e2f51` has a source-valid mechanism:

```text
sub_82BA34D8 wrapper
-> DispatchForwardInvocation
-> distinct __imp__sub_82BA34D8 preserved original
```

The generated original body is not hand-edited. Default-off, metadata, exception and recursion synthetic tests passed with exact-once forwarding. That evidence is CONFIRMED SOURCE and CONFIRMED SYNTHETIC, not linked production behavior.

No production executable containing the hook linked. Release execution, benchmarks, runtime forwarding equivalence and user gameplay were not performed. The Debug final link failed with the exact mismatch:

```text
lld-link: error: /failifmismatch: mismatch detected for '_ITERATOR_DEBUG_LEVEL':
>>> fable2_g2a_capture.lib(g2a_capture.cpp.obj) has value 2
>>> spdlog.lib(spdlog.cpp.obj) has value 0
```

This mismatch is a checkpoint/build-packaging fact only.

### Why a linked proof remains useful

A linked Release production target can still prove that the strong wrapper and weak/generated original resolve as distinct symbols and that all disabled/enabled/recursion/fail-open paths execute the original exactly once. This validates a reusable mechanism and can later support swap-ID correlation.

It does not identify a character draw or test a Canary divergence. `sub_82BA34D8` has enough information for mechanism and swap correlation—device/front-buffer-like r3/r4 plus flags—but not shader, texture, register, pipeline, EDRAM or resource lifetime.

### Required revision

Retain:

- strong `sub_82BA34D8` wrapper;
- distinct `__imp__sub_82BA34D8` original;
- untouched generated body;
- default-off, fail-open exact forwarding;
- synthetic disabled/enabled/exception/recursion fixtures;
- source verification and bounded counts sufficient for exact-once proof.

Remove or defer:

- generalized session/capture writer;
- extensible metadata records and r3/r4 capture;
- rotation, summaries and lifecycle state unrelated to exact-once;
- filesystem/logging work in `noexcept` paths;
- benchmarks, runtime capture and gameplay;
- Debug packaging work undertaken solely to clear the current mismatch.

Validate first through the normal Release production link and synthetic/default-off routes. Fixing Debug package consistency may be legitimate later, but it should not expand this mechanism proof.

This decision is based on proportionate evidence value, not sunk cost.

## Part B — **STATIC XDK METHOD RECOVERY**

This is the primary next evidence-acquisition gate.

G1 proved creation, ring, interrupt, swap and shutdown functions, but not representative draw, resource, shader or render-target methods. One exact static recovery result can answer whether the preferred high-semantic seam is real, what information it retains, and whether an optional title IR is justified. If recovery is blocked, the blocker can justify designing targeted low-level correlation.

The first experiment is `EXP-STATIC-XDK-001`.

## Relationship between the decisions

Part B proceeds **independently** of Part A and is the higher-priority evidence decision. Part A may later settle safe wrapper mechanics. Part B tests useful semantic coverage.

A safe present hook and a useful defect boundary are separate claims:

| Question | Boundary/gate | Decision |
|---|---|---|
| Can a confirmed title call forward exactly once? | `sub_82BA34D8`, `EXP-G2A-LINK-001` | Revise G2A, then mechanism proof only. |
| Can title semantics support diagnosis/replacement planning? | representative static XDK methods, `EXP-STATIC-XDK-001` | Primary next gate. |
| Why are character surfaces black? | later affected draw/resource/pass evidence | Unknown; no causal claim. |

## Authorization boundary

G1.5D authorizes neither path's implementation. Do not check out, resume, cherry-pick, repair, build or run the paused G2A code. Do not add static-XDK wrappers or low-level probes. A fresh session should begin with `EXP-STATIC-XDK-001` only after the user explicitly authorizes that next static phase.
