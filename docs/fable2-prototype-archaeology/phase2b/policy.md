# Semantic policy v1

## Concepts and terminal records

A binary correspondence relates two exact bodies under Phase 2A's policy. An
anchor is an exact spelling with all its source locations; its casefolded,
whitespace-normalized lookup key never merges distinct spellings. A semantic
association relates an anchor to a function context with native evidence.
Proposed human-readable naming and canonical adoption are separate decisions:
this implementation leaves every `proposed_name` null and every
`canonical_adoption` false.

The native-context key is `(anchor_id, build, containing .pdata start)`. An
anchor without a recovered instruction XREF gets exactly one null-owner
terminal per donor build. A descriptor callback has a separate key including
its registration ID; the callback is not confused with the registration caller.
Each registered structure, data slot and native instruction has its own
content-derived ID. IDs hash sorted-key UTF-8 JSON, truncated to 24 hexadecimal
characters; collisions/duplicates fail generation, never overwrite records.

| Terminal status | Required interpretation |
| --- | --- |
| accepted-registered-callback | Distinctive exact donor name, repeated native descriptor/loop proof, exact callback .pdata entry, accepted callback/callee/caller pairs, corresponding TU1 descriptor role, no contradiction. Does not prove a complete Lua namespace. |
| accepted-xref-corroborated | Distinctive exact donor XREF, accepted body pair, exact TU1 literal use at corresponding call offset and argument, accepted callee pair, no contradiction. |
| candidate-target-unconfirmed | Donor native evidence and accepted body pair exist; independent target support is insufficient. |
| candidate-donor-only | Native evidence exists but no closed accepted donor-to-TU1 pair can be used. |
| ambiguous | A generic spelling has multiple native locations and a recovered use; location/meaning cannot safely be collapsed. |
| quarantined | Filtered/generic/external-only anchor, no native use, unsafe structure, or conflicting target evidence. |
| rejected | A tested association is conclusively disproven. Reserved in this version; production unsafe structures are retained as quarantine rather than overstating disproof. |

Precedence is contradiction, ambiguity, filtering, absence of native evidence,
missing accepted pair, missing target support, then acceptance. A blocked pair
status is recorded independently even when filtering gives a quarantine grade.
Only `accepted-exact-unique` and `accepted-normalized-corroborated` can join.
The complete original mapping row and its zero-based accepted-artifact index
are retained; mapping status, grade, bounds and provenance are not recreated.

## Native proof boundary

All code units come from validated, nonoverlapping big-endian `.pdata` entries.
The scanner is a deliberately small PPC abstract interpreter, not a full
decompiler. Address arithmetic wraps to 32 bits; signed low-half carry is
explicit. Basic-block leaders, direct calls, unsupported instructions and a
32-instruction definition limit prevent speculative propagation. Register r2
has no special assumed TOC value; an r2/base-relative load works only when its
base is explicitly proven in the instruction context. Initialized writable
pointers are never treated as runtime constants.

An instruction XREF records the consumed address, instruction, exact owner,
operand/width, role, definition instructions, readonly pointer slots and checks.
An intermediate high-half constant is never an XREF merely because it equals
the address of another string. Direct aligned BE32 data pointers are separate
records without a containing code owner; they alone cannot satisfy semantic
acceptance. ASCII and UTF-16LE NUL-terminated occurrences are matched in data
and rdata, not executable bytes. No non-ASCII completeness claim is made.

An 8-byte table candidate records both field values, potential stride,
compatible neighbour, joint loads, callback boundary and every rejection
reason. Isolated or merely adjacent values always quarantine. Constructor
recognition proves repeated incoming argument stores into disjoint fields of
the same incoming object. The counted-loop recognizer additionally requires a
materialized immutable table, nonvolatile cursor/end, stride 8, unsigned compare,
exact backward branch to the two loads, and a two-store leaf constructor.
It handles only functions up to 256 bytes and tables up to 1,024 bytes. Larger,
interprocedural, writable-initialization or different-layout cases are not
claimed resolved. Exact entries are required; interior callbacks are not
invented thunks. Aliases may share one callback.

Descriptor target support checks accepted callback, constructor and caller
pairs, matching field widths/offsets/argument roles and caller-relative callsite.
An exact target name or explicitly null stripped name can qualify; missing or
unmodeled values cannot. Synthetic fixtures exercise this path even though no
real descriptor reaches proof in this dataset. A callback store is established
native structure, not proof that a Lua VM actually invokes it.

## Secondary evidence and non-propagation

Subsystem categories are lexical review buckets, not established subsystem
membership. RTTI/type strings and source paths remain contextual anchors, not
automatic constructor/type/function identities. Qualified-to-terminal string
matches are marked `terminal-candidate` and cannot prove the qualification.
All original spellings and provenance are preserved even for filtered anchors.

September is scanned independently but is not silently routed through an
unretained aggregate secondary mapping. July contributes source provenance only
as an alias. Graph expansion requires mapped direct-call agreement in TU1,
depth 1 and fan-out at most 8; even a compatible neighbour never gets an
accepted name. Cycles and fan-out limits are explicit. No graph records survive
the current seed/edge constraints, so there are no competing propagated roles
to adjudicate in this run.

Stable scalar candidates compare exact instruction-relative donor/target
accesses, content hashes, widths and read/write modes through accepted pairs.
Same address and even matching content do not establish an object's boundary
or meaning. All scalar candidates have `semantic_acceptance=false`. No score,
adjacency, community observation or Phase 2A acceptance alone creates semantics.

The review queue selects the first three content IDs per terminal status,
subsystem, category, donor build and problem-intersection stratum. Every stratum
reports availability, including zero; overlap across strata is intentional.
This deterministic sample is for inspection, not an accuracy estimate. Mapping
review is exhaustive for native primary contexts blocked by mapping and for
target conflicts; it never modifies Phase 2A.
