# Fault-walk performance checkpoint

This checkpoint distinguishes source-level hot-path evidence from gameplay FPS
measurement. Gameplay benchmarking remains external to this document.

## Confirmed Harvest 002 workload

Harvest 002 recorded `8` invalid/unregistered dispatcher targets and `14,315`
repeat suppressions. It recorded zero host `ACCESS_VIOLATION` faults and zero
host `INTEGER_DIVIDE_BY_ZERO` faults. Nevertheless, its FULL build wrapped every
generated guest-function invocation for host-fault recovery.

## Previous FULL normal-call cost

Inspection of the generated boundary and runtime showed the following work on
every ordinary generated-function call:

- initialize/active-state checks;
- two global-mutex acquisitions and two poison-table lookups;
- a TLS guest-frame push and pop;
- one complete entry checkpoint copy;
- Windows SEH setup/teardown around the generated body.

`sizeof(PPCContext)` is compile-time confirmed as `2688` bytes. Before the
current changes, clearing the captured-exception object also cleared a second
embedded `PPCContext`, adding another full-context store at entry. TLS frame
storage reserves `64` frames in one allocation on a guest thread's first fault-
walk access; entries are then constructed only when that thread reaches a new
maximum nesting depth, while push/pop bookkeeping remains per call. Rich
logging/string creation and JSON serialization occurred on faults/suppression
milestones rather than every valid generated call, so they do not explain the
general slowdown by themselves.

The mismatch is decisive: Harvest 002 paid this boundary on every generated
call while all useful discoveries came from the much narrower invalid-target
trap.

## Current paths

`Dispatch` mode compiles generated functions exactly like the normal build. Its
only diagnostic branch is in `InvalidFunctionTrap`, after an indirect lookup
has already failed. Consequently it has no checkpoint, TLS-stack, poison-map,
or SEH overhead on registered generated-function calls.

On the invalid-target path, the first unique target retains the exact target,
LR/caller, CTR, `r1`, `r2`, `r3-r10`, thread ID, policy, order, and a complete
context snapshot. Repeated hits perform a map lookup under the existing mutex,
increment primitive counters, apply the policy, and return. They no longer
format a fatal string, copy a rich `FaultRecord`, emit milestone logs, or
rewrite JSON. Full report generation is deferred to explicit reporting,
guardrail stop, or process exit.

`Full` mode retains its required generated boundary. Its no-fault fast path now
uses an atomic check to avoid poison-map locks until the first generated host
fault, removes the redundant context clear/copy, and makes repeated
initialization a single atomic early return. It must still copy `2688` bytes,
push/pop TLS state, and establish nested SEH on every generated call. After the
first generated host fault, the current poison lookup again requires the global
mutex; this is the main remaining FULL-mode optimization opportunity if FULL
gameplay harvesting becomes necessary.

## Separate expected effects

- Correctness: registering `0x829675C0` removes the `13,919` recorded repeat
  suppressions and executes the real guest thunk.
- Instrumentation: `Dispatch` removes FULL boundary work even when no invalid
  targets occur.
- Tolerance: any future synthetic return may enable progression, but it is not
  a correctness or performance fix.

Do not attribute a gameplay speed change to instrumentation without measuring
it separately from the removal of the hot `0x829675C0` miss.
