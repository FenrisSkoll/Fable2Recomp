# Native-renderer architecture options

## Recommendation

**Primary seam:** intercept the statically linked Xbox D3D/XDK layer before it
generates Xenos commands. Introduce it first in the hybrid forwarding mode:
capture a normalized operation, then call the original generated body so
`rexgpu-xenos.dll` renders unchanged.

**Fallback seam:** investigate the Lionhead render-command abstraction around
`sub_82AAC208`. Use it only if G2 proves stable command structures, object
lifetimes, and enqueue/consume ordering. Until then, raw ring/PM4
instrumentation is a correlation oracle, not a replacement renderer seam.

## Comparative summary

| Seam | Evidence it exists | Semantics retained | Scope / principal risk | Verdict |
|---|---|---|---|---|
| 1. Reimplement GPU plugin ABI | **CONFIRMED** ABI and packet processor | Xenos packets, registers, shader microcode, EDRAM and swap; original API/object intent mostly gone | General command processor, shader translator, EDRAM, formats, sync and presenters; emulator-scale correctness burden | Reject as primary; retain existing implementation as oracle |
| 2. Static Xbox D3D/XDK functions | **CONFIRMED** for lifecycle/present; other operations unknown | API operation, device/resource identity, arguments and order before packet collapse | Exact title ABI, object layouts, indirect method recovery and safe forwarding | **Primary seam** |
| 3. Lionhead renderer abstraction | **STRONG HYPOTHESIS** for async queue; renderer labels confirmed, operation ABI unconfirmed | Potential pass/material intent and engine resource identity | Unknown command format, thread ownership, coverage and registration methods | Conditional fallback |
| 4. Higher capture + ReXGPU oracle | **CONFIRMED feasible** wherever a static hook is proven | Same high-level semantics as hook plus exact current output for comparison | Trace overhead and forwarding correctness; cannot render independently | Required G2/G3 development mode |

## 1. Reimplement `rexgpu-xenos.dll` ABI

- **Evidence and scope:** ABI version 1, loader, `IGraphicsSystem`, ring/MMIO
  interfaces, and D3D12/Vulkan plugin implementations are confirmed in SDK
  source. A substitute must consume guest physical rings and implement PM4,
  Xenos state registers, shaders, vertex/texture fetch, EDRAM, queries,
  synchronization, copies/resolves, interrupts, swap, and presentation.
- **Semantic information:** sufficient for GPU emulation, insufficient to
  recover original API call boundaries, object identity/lifetime, lock intent,
  redundant state, or engine pass meaning.
- **ABI/guest-memory risk:** highest. It directly owns guest physical memory,
  MMIO, callbacks, writeback, interrupts, and scheduling.
- **Forwarding:** plugin selection could retain the current plugin or choose a
  replacement, but the ABI does not compose two implementations. Mirroring
  would require new multiplexing infrastructure and strict ownership rules.
- **Capture/replay:** packet capture can be deterministic with complete memory
  snapshots and timing, but raw packets reference mutable guest memory. Replay
  is substantially more complex than a semantic command trace.
- **Shader strategy:** requires general Xenos shader translation or embedding
  the existing translator. XenosRecomp alone does not implement the full GPU.
- **Title work and portability:** title-neutral in theory, emulator-scale in
  practice. Backend portability is good only after the entire Xenos model is
  correct.
- **Licensing:** ReXGlue/Xenia are BSD-style and can inform implementation;
  provenance must be retained. GPL Unleashed implementation cannot be copied
  casually. XenosRecomp/Plume are MIT.
- **Validation:** packet/register/EDRAM differential tests against current
  ReXGPU and Xenia, plus exact frame comparisons and synchronization tests.
- **Failure modes:** hangs from waits/interrupts, guest-memory corruption,
  shader mistranslation, EDRAM/resolve errors, backend divergence, and an
  unbounded compatibility workload.

This seam is rejected because it discards the exact high-level information the
title-specific renderer is meant to exploit.

## 2. Intercept static Xbox D3D/XDK functions

- **Evidence and scope:** `0x82BA34D8` reaches `VdSwap` while still receiving a
  device and front-buffer/surface-like object. `0x82BA6990`, `0x82BA2830`,
  `0x82BA6968`, and `0x82BA6C18` prove lifecycle and transport boundaries. The
  remaining resource/state/shader/draw functions must be recovered.
- **Semantic information:** expected to retain operation kind, guest objects,
  arguments, state intent, lock/unlock, and order. Engine pass/material purpose
  may already be lost.
- **ABI/guest-memory risk:** moderate to high but localized. Each method needs
  exact PPC ABI, object layout, pointer validation, endian rules, aliases,
  reference counts, and all side effects.
- **Forwarding:** strong. A wrapper can record and call a separately preserved
  original generated body. This requires intentional symbol/dispatcher wiring
  to avoid recursion.
- **Capture/replay:** good. A versioned operation IR plus resource identities
  and bounded payloads can be replayed after the trace becomes complete.
- **Shader strategy:** capture exact creation/bind events and stable hashes;
  preconvert a validated TU1 corpus, with a defined policy for unseen/dynamic
  shaders and XenosRecomp omissions.
- **Title work and portability:** significant one-time TU1 reverse engineering,
  then a backend-neutral IR can target D3D12 and later Vulkan.
- **Licensing:** clean-room/title-specific implementation can remain under the
  project's chosen licence; Plume/XenosRecomp are optional MIT components.
  Do not copy GPL Unleashed code.
- **Validation:** shadow-forward against unmodified ReXGPU, correlate hook
  events with PM4/interrupt/present observations, and compare state/screens at
  manual checkpoints.
- **Failure modes:** a method is missed, misbounded, misnamed, or called through
  an unhooked pointer; forwarding changes ABI/state; object alias/lifetime is
  wrong; a hidden packet emitter bypasses the layer.

This is the primary production seam because it balances retained meaning with
an observable path to the existing renderer.

## 3. Intercept a Lionhead engine rendering abstraction

- **Evidence and scope:** TU1 contains named renderers and
  `ProcessAsyncCommandQueues`; `sub_82AAC208` is a bounded strong hypothesis.
  G1 has not established the enqueue API, command format, per-operation
  dispatch, object layout, or completeness.
- **Semantic information:** potentially best: frame/pass, material, scene,
  resource, and asynchronous-command intent could remain.
- **ABI/guest-memory risk:** unknown and potentially high because custom
  queues may be multi-threaded, variable-sized, self-modifying, pooled, or
  consumed by indirect dispatch.
- **Forwarding:** possible if interception occurs before consumption and the
  original queue path receives unchanged data. Consumer replacement is much
  riskier.
- **Capture/replay:** potentially excellent if commands are self-contained;
  poor if they contain transient pointers/callbacks or implicit global state.
- **Shader strategy:** may expose engine shader identities but still needs
  exact Xbox shader binaries and state translation below.
- **Title work and portability:** most title-specific, but could yield the
  smallest normalized IR and cleanest backend split.
- **Licensing:** title-derived structure metadata may be documented without
  committing private payloads; external component rules remain unchanged.
- **Validation:** prove enqueue/consume pairs, queue ownership, frame coverage,
  and one-to-one/downstream PM4 correlation while forwarding.
- **Failure modes:** hook is only registration/timing, queues omit immediate
  calls, captured pointers expire, async ordering changes, or a subset of
  passes bypasses the abstraction.

This is the fallback only after its contract is confirmed. It must not displace
the known-good static Xbox seam based on renderer labels alone.

## 4. Hybrid high-level instrumentation with ReXGPU retained

- **Evidence and scope:** generated functions can be wrapped while their
  original bodies remain callable. ReXGPU already provides the validated
  D3D12/Vulkan output and raw command observability.
- **Semantic information:** all information at the selected high hook, plus a
  lower observable consequence for correlation.
- **ABI/guest-memory risk:** lower than replacement because guest execution and
  renderer ownership remain unchanged, but a faulty wrapper can still alter
  registers, memory, exceptions, timing, or recursion.
- **Forwarding:** defining characteristic. Capture must be fail-open and must
  never synthesize guest results.
- **Capture/replay:** deterministic semantic traces are the goal; raw packet
  markers and present counts validate coverage. Replay is deferred until the
  schema and hook inventory are complete.
- **Shader strategy:** identify/hash only in G2; continue rendering the original
  shader through ReXGPU. Conversion happens later and is differential-tested.
- **Title work and portability:** initially title-specific instrumentation;
  versioned IR isolates later D3D12/Vulkan backends.
- **Licensing:** can be implemented within Fable/ReXGlue's existing licence
  boundaries without copying GPL code.
- **Validation:** off/on A/B runs on the exact executable, event-to-packet
  correlation, frame/present/resource counts, trace determinism, and manual
  image/state checkpoints.
- **Failure modes:** instrumentation overhead changes timing, recorder I/O
  re-enters hooks, partial traces are mistaken for complete frames, or capture
  faults disturb guest execution.

This is the mandatory development architecture for the primary seam, not the
eventual renderer itself.

## Decision gates

The primary seam remains viable only if G2 can:

1. forward `0x82BA34D8` without behavioural change;
2. identify at least one draw, one resource create/update, one shader bind, and
   one target/resolve method with exact TU1 boundaries and arguments;
3. correlate those operations with ReXGPU packets in correct thread/frame
   order; and
4. demonstrate that no material rendering path bypasses the intercepted layer
   in the manual checkpoint trace.

If method recovery fails but `sub_82AAC208` yields a complete stable command
ABI, promote the Lionhead seam. If neither higher boundary reaches coverage,
G2 must report the precise gap; it must not silently fall back to implementing
a general Xenos emulator.
