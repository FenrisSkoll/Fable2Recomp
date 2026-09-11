#!/usr/bin/env python3
"""Bounded, fail-closed PPC semantic-reference recovery. No runtime execution.

Only explicitly modelled instructions preserve abstract register values. Values
never cross a basic-block entrance, call, unknown instruction, or 32-step chain.
Initialized writable memory is reported as storage, never assumed immutable.
"""
from __future__ import annotations

import bisect
import hashlib
import json
import struct
from collections import defaultdict
from dataclasses import dataclass


VERSION = "1.0.0"
MAX_CHAIN = 32


def hx(value):
    return f"0x{value:08X}"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest().upper()


def signed(value, bits=16):
    return (value ^ (1 << (bits - 1))) - (1 << (bits - 1))


def branch(word, pc):
    op = word >> 26
    if op not in (16, 18):
        return None
    delta = signed(word & (0x03FFFFFC if op == 18 else 0xFFFC), 26 if op == 18 else 16)
    return (delta if word & 2 else pc + delta) & 0xFFFFFFFF


@dataclass(frozen=True)
class Value:
    number: int
    chain: tuple
    slots: tuple = ()


class Image:
    def __init__(self, build, blocks):
        self.build = build
        self.blocks = sorted(blocks, key=lambda b: b.start)
        self.starts = [b.start for b in self.blocks]
        self.functions = []
        pdata = next(b for b in self.blocks if b.name == ".pdata")
        if len(pdata.data) % 8:
            raise ValueError("unaligned .pdata size")
        for offset in range(0, len(pdata.data), 8):
            start, unwind = struct.unpack_from(">II", pdata.data, offset)
            size = ((unwind >> 8) & 0x3FFFFF) * 4
            code = self.block(start, size)
            if not size or start % 4 or code is None or not code.execute:
                raise ValueError("invalid executable .pdata boundary")
            self.functions.append({"start": start, "end": start + size,
                                   "pdata": pdata.start + offset})
        if self.functions != sorted(self.functions, key=lambda f: f["start"]):
            raise ValueError("unsorted .pdata")
        for a, b in zip(self.functions, self.functions[1:]):
            if a["end"] > b["start"]:
                raise ValueError("overlapping .pdata")
        self.by_start = {f["start"]: f for f in self.functions}
        self.function_starts = sorted(self.by_start)

    def block(self, address, width=1):
        index = bisect.bisect_right(self.starts, address) - 1
        if index >= 0:
            block = self.blocks[index]
            if address + width <= block.start + len(block.data):
                return block
        return None

    def read(self, address, width):
        block = self.block(address, width)
        if block is None:
            return None
        offset = address - block.start
        return block.data[offset:offset + width]

    def owner(self, address):
        index = bisect.bisect_right(self.function_starts, address) - 1
        if index >= 0:
            result = self.by_start[self.function_starts[index]]
            if address < result["end"]:
                return result
        return None


def boundary(function):
    return {"start": hx(function["start"]), "end_exclusive": hx(function["end"]),
            "size": function["end"] - function["start"], "pdata_record": hx(function["pdata"])}


def scan_function(image, function, anchors, *, prefix_end=None):
    start = function["start"]
    end = function["end"] if prefix_end is None else prefix_end
    if not start < end <= function["end"] or end % 4:
        raise ValueError("invalid bounded prefix")
    words = list(struct.unpack(f">{(end - start) // 4}I", image.read(start, end - start)))
    leaders = {start}
    for index, word in enumerate(words):
        pc = start + index * 4
        target = branch(word, pc)
        if target is not None and start <= target < end:
            leaders.add(target)
        if word >> 26 in (16, 18, 19):
            leaders.add(pc + 4)
    registers = {}
    references, accesses, calls = [], [], []
    seen = set()

    def emit(value, pc, role, operand, width=0, destination=None):
        if value is None or value.number not in anchors or image.block(value.number) is None:
            return
        key = (value.number, pc, role, operand)
        if key in seen:
            return
        seen.add(key)
        references.append({"build": image.build, "anchor_address": hx(value.number),
                           "instruction": hx(pc), "function": boundary(function),
                           "method": "bounded-def-use", "role": role, "operand": operand,
                           "width": width, "destination": destination,
                           "definition_instructions": [hx(x) for x in value.chain],
                           "readonly_pointer_slots": [hx(x) for x in value.slots],
                           "checks": ["exact-pdata", "initialized-anchor", "single-block",
                                      "explicit-instruction-semantics", "bounded-chain"]})

    def assign(reg, number, pc, parents=(), slots=()):
        chain = tuple(sorted({pc} | {x for v in parents for x in v.chain}))
        if len(chain) > MAX_CHAIN:
            registers.pop(reg, None)
            return
        value = Value(number & 0xFFFFFFFF, chain,
                      tuple(sorted(set(slots) | {x for v in parents for x in v.slots})))
        registers[reg] = value

    for index, word in enumerate(words):
        pc = start + index * 4
        if pc in leaders:
            registers.clear()
        op, rt, ra, rb = word >> 26, (word >> 21) & 31, (word >> 16) & 31, (word >> 11) & 31
        imm, xo = signed(word & 0xFFFF), (word >> 1) & 1023
        if op in (14, 15):
            base = Value(0, ()) if ra == 0 else registers.get(ra)
            if base is None:
                registers.pop(rt, None)
            else:
                assign(rt, base.number + (imm << 16 if op == 15 else imm), pc, (base,))
        elif op in (24, 25):
            source = registers.get(rt)
            if source is None:
                registers.pop(ra, None)
            else:
                assign(ra, source.number | ((word & 65535) << (16 if op == 25 else 0)), pc, (source,))
        elif op == 31 and xo == 444:  # or, including mr
            left, right = registers.get(rt), registers.get(rb)
            if left is None or right is None:
                registers.pop(ra, None)
            else:
                assign(ra, left.number | right.number, pc, (left, right))
        elif op in (32, 34, 40, 42, 36, 38, 44) or (op == 31 and xo in (23, 87, 279, 343, 151, 215, 407)):
            indexed = op == 31
            load = op in (32, 34, 40, 42) or (indexed and xo in (23, 87, 279, 343))
            width = ({32: 4, 34: 1, 40: 2, 42: 2, 36: 4, 38: 1, 44: 2}.get(op)
                     if not indexed else {23: 4, 87: 1, 279: 2, 343: 2, 151: 4, 215: 1, 407: 2}[xo])
            base = Value(0, ()) if ra == 0 else registers.get(ra)
            index_value = registers.get(rb) if indexed else Value(imm, ())
            address = None if base is None or index_value is None else (base.number + index_value.number) & 0xFFFFFFFF
            block = image.block(address, width) if address is not None else None
            if block is not None:
                address_value = Value(address, tuple(sorted(set(base.chain + index_value.chain))),
                                      tuple(sorted(set(base.slots + index_value.slots))))
                emit(address_value, pc, "memory-read" if load else "memory-write", "effective-address", width)
                accesses.append({"instruction": hx(pc), "address": hx(address), "width": width,
                                 "mode": "read" if load else "write", "section": block.name,
                                 "function": boundary(function)})
                if not load:
                    emit(registers.get(rt), pc, "store", f"r{rt}", width, hx(address))
            if load:
                if block is not None and not block.write and not block.execute:
                    number = int.from_bytes(image.read(address, width), "big", signed=op == 42 or (indexed and xo == 343))
                    assign(rt, number, pc, (base, index_value), (address,))
                else:
                    registers.pop(rt, None)
        elif op == 18 and word & 1:
            target = branch(word, pc)
            arguments = {f"r{r}": {"value": hx(v.number), "chain": [hx(x) for x in v.chain],
                                   "slots": [hx(x) for x in v.slots]}
                         for r, v in sorted(registers.items()) if 3 <= r <= 10}
            calls.append({"instruction": hx(pc), "target": hx(target), "arguments": arguments,
                          "constant_registers": {f"r{r}": hx(v.number) for r, v in sorted(registers.items())},
                          "function": boundary(function)})
            for reg in range(3, 11):
                emit(registers.get(reg), pc, "call-argument", f"r{reg}", destination=hx(target))
            registers.clear()
        elif op in (10, 11):  # compares alter CR, not GPRs
            pass
        elif op == 31 and xo in (0, 32, 144):  # cmp, cmpl, mtcrf
            pass
        else:
            registers.clear()
    return references, accesses, calls


def scan_image(image, anchors):
    references, accesses, calls, pointers = [], [], [], []
    for block in image.blocks:
        if block.execute or block.name not in (".rdata", ".data"):
            continue
        for offset in range((-block.start) % 4, len(block.data) - 3, 4):
            value = struct.unpack_from(">I", block.data, offset)[0]
            if value in anchors:
                pointers.append({"build": image.build, "slot": hx(block.start + offset),
                                 "anchor_address": hx(value), "section": block.name,
                                 "method": "direct-big-endian-pointer", "function": None,
                                 "limitation": "Data storage has no containing executable .pdata function."})
    for function in image.functions:
        refs, uses, edges = scan_function(image, function, anchors)
        references.extend(refs)
        accesses.extend(uses)
        calls.extend(edges)
    return {"references": references, "accesses": accesses, "calls": calls, "pointers": pointers}


def table_candidates(image, anchor_addresses, calls):
    """Recover repeated name/callback fields; never infer registration from layout.

    Consumer proof is deliberately separate. Even a table with observed field
    loads stays candidate until the registration callee/store role is proved.
    """
    result = []
    slot_calls = defaultdict(list)
    for call in calls:
        slots = {s for arg in call["arguments"].values() for s in arg["slots"]}
        for slot in sorted(slots):
            slot_calls[slot].append(call["instruction"])
    for block in image.blocks:
        if block.execute or block.name not in (".rdata", ".data"):
            continue
        for offset in range((-block.start) % 4, len(block.data) - 7, 4):
            name, callback = struct.unpack_from(">II", block.data, offset)
            if name not in anchor_addresses:
                continue
            owner = image.owner(callback)
            slot = block.start + offset
            repeated = False
            for delta in (-8, 8):
                other = offset + delta
                if 0 <= other <= len(block.data) - 8:
                    next_name, next_callback = struct.unpack_from(">II", block.data, other)
                    repeated |= next_name in anchor_addresses and next_callback in image.by_start
            shared_calls = sorted(set(slot_calls[hx(slot)]) & set(slot_calls[hx(slot + 4)]))
            reasons = []
            if owner is None:
                reasons.append("nonexecutable-or-no-pdata-callback")
            elif callback not in image.by_start:
                reasons.append("interior-callback-without-entry-proof")
            if not repeated:
                reasons.append("isolated-pointer-coincidence")
            if not shared_calls:
                reasons.append("name-and-callback-not-proven-loaded-together")
            reasons.append("registration-callee-role-unproved")
            result.append({"build": image.build, "slot": hx(slot), "stride_candidate": 8,
                           "name_address": hx(name), "callback": hx(callback),
                           "callback_boundary": boundary(owner) if owner else None, "repeated_layout": repeated,
                           "joint_field_load_calls": shared_calls, "status": "quarantined",
                           "reasons": reasons})
    return result


def compatible_access(left, right):
    return left["width"] == right["width"] and left["mode"] == right["mode"]


def descriptor_stores(image, entry):
    """Prove straight-line stores of incoming arguments into an incoming object.

    This establishes a descriptor layout only, not a Lua API identity. Stop at
    every transfer or unknown operation. No ABI TOC value is assumed.
    """
    function = image.by_start.get(entry)
    if function is None:
        return []
    values = {r: (r, 0) for r in range(3, 11)}
    stores = []
    data = image.read(entry, min(function["end"] - entry, 128))
    for index, (word,) in enumerate(struct.iter_unpack(">I", data)):
        pc = entry + index * 4
        op, rt, ra, rb = word >> 26, (word >> 21) & 31, (word >> 16) & 31, (word >> 11) & 31
        xo = (word >> 1) & 1023
        if op == 36:
            base, source = values.get(ra), values.get(rt)
            if base is not None and source is not None and source[1] == 0:
                stores.append({"instruction": hx(pc), "object_argument": f"r{base[0]}",
                               "value_argument": f"r{source[0]}",
                               "offset": base[1] + signed(word & 65535), "width": 4})
        elif op == 14 and ra in values:
            arg, offset = values[ra]
            values[rt] = (arg, offset + signed(word & 65535))
        elif op == 31 and xo == 444 and rt == rb:
            if rt in values:
                values[ra] = values[rt]
            else:
                values.pop(ra, None)
        elif word == 0x60000000:
            pass
        else:
            break
    return stores


def constructor_registrations(image, anchor_addresses, calls):
    """Repeated calls + exact argument flow + callee paired field stores.

    Each result is a native descriptor registration association. Lua namespace
    and signature are deliberately not inferred from an unqualified string.
    """
    candidates = []
    layouts = {}
    for call in calls:
        entry = int(call["target"], 16)
        if entry not in layouts:
            layouts[entry] = descriptor_stores(image, entry)
        stores = layouts[entry]
        for name_store in stores:
            name_arg = call["arguments"].get(name_store["value_argument"])
            if name_arg is None or int(name_arg["value"], 16) not in anchor_addresses:
                continue
            for callback_store in stores:
                if (callback_store["object_argument"] != name_store["object_argument"]
                        or abs(callback_store["offset"] - name_store["offset"]) < 4
                        or name_store["object_argument"] in (name_store["value_argument"], callback_store["value_argument"])):
                    continue
                callback_arg = call["arguments"].get(callback_store["value_argument"])
                if callback_arg is None:
                    continue
                callback = int(callback_arg["value"], 16)
                if callback not in image.by_start:
                    continue
                candidates.append({"build": image.build, "kind": "constructor-descriptor",
                                   "name_address": name_arg["value"], "callback": hx(callback),
                                   "callback_boundary": boundary(image.by_start[callback]),
                                   "registration_function": call["function"],
                                   "call_instruction": call["instruction"], "callee": hx(entry),
                                   "name_definition": name_arg, "callback_definition": callback_arg,
                                   "name_store": name_store, "callback_store": callback_store,
                                   "namespace_proven": False})
    grouped = defaultdict(list)
    for row in candidates:
        key = (row["callee"], row["name_store"]["object_argument"],
               row["name_store"]["value_argument"], row["name_store"]["offset"],
               row["callback_store"]["value_argument"], row["callback_store"]["offset"])
        grouped[key].append(row)
    result = []
    for key, rows in sorted(grouped.items()):
        distinct = len({(r["name_address"], r["call_instruction"]) for r in rows})
        for row in sorted(rows, key=lambda r: (r["call_instruction"], r["name_address"], r["callback"])):
            row["compatible_repetitions"] = distinct
            row["status"] = "proven-native-descriptor" if distinct >= 2 else "quarantined"
            row["reasons"] = [] if distinct >= 2 else ["isolated-constructor-call"]
            result.append(row)
    return result


def counted_registration_loops(image, anchor_addresses, calls):
    """Recognize only a strict counted descriptor loop, not arbitrary CFGs.

    After the paired-field call: addi cursor,cursor,8; cmplw cursor,end;
    blt same-field-loads. Cursor/end must be materialized nonvolatile GPRs.
    The leaf callee must contain only the paired stw operations and blr.
    Complete immutable table bounds and every callback are verified together.
    """
    results = []
    for call in calls:
        callee = int(call["target"], 16)
        function = image.by_start.get(callee)
        stores = descriptor_stores(image, callee)
        if function is None or len(stores) != 2 or stores[0]["object_argument"] != stores[1]["object_argument"]:
            continue
        code = image.read(callee, function["end"] - callee)
        callee_words = [w[0] for w in struct.iter_unpack(">I", code)]
        if len(callee_words) != 3 or callee_words[-1] != 0x4E800020 or any(w >> 26 != 36 for w in callee_words[:2]):
            continue
        pc = int(call["instruction"], 16)
        tail = image.read(pc + 4, 12)
        if tail is None or pc + 16 > int(call["function"]["end_exclusive"], 16):
            continue
        increment, compare, test = struct.unpack(">III", tail)
        cursor = (increment >> 21) & 31
        endreg = (compare >> 11) & 31
        cr = (compare >> 23) & 7
        loop_start = branch(test, pc + 12)
        if not (increment >> 26 == 14 and ((increment >> 16) & 31) == cursor and
                signed(increment & 65535) == 8 and cursor >= 14 and endreg >= 14 and
                compare >> 26 == 31 and ((compare >> 1) & 1023) == 32 and
                ((compare >> 16) & 31) == cursor and not (compare & (1 << 21)) and
                test >> 26 == 16 and ((test >> 21) & 31) == 12 and
                ((test >> 16) & 31) == cr * 4 and not (test & 3) and
                loop_start is not None and int(call["function"]["start"], 16) <= loop_start < pc):
            continue
        constants = call["constant_registers"]
        if f"r{cursor}" not in constants or f"r{endreg}" not in constants:
            continue
        table, end = int(constants[f"r{cursor}"], 16), int(constants[f"r{endreg}"], 16)
        if not 16 <= end - table <= 1024 or (end - table) % 8:
            continue
        block = image.block(table, end - table)
        if block is None or block.write or block.execute:
            continue
        name_arg = next((a for a, v in call["arguments"].items() if v["slots"] == [hx(table)]), None)
        callback_arg = next((a for a, v in call["arguments"].items() if v["slots"] == [hx(table + 4)]), None)
        if name_arg is None or callback_arg is None:
            continue
        # The backedge must restart at the exact cursor-relative name load;
        # the next instruction must load its callback, with no competing path.
        loop_bytes = image.read(loop_start, pc - loop_start)
        loop_words = [w[0] for w in struct.iter_unpack(">I", loop_bytes)]
        if len(loop_words) != 2:
            continue
        expected = [(name_arg, 0), (callback_arg, 4)]
        if any(w >> 26 != 32 or ((w >> 16) & 31) != cursor or
               ((w >> 21) & 31) != int(arg[1:]) or signed(w & 65535) != offset
               for w, (arg, offset) in zip(loop_words, expected)):
            continue
        by_arg = {s["value_argument"]: s for s in stores}
        if name_arg not in by_arg or callback_arg not in by_arg or by_arg[name_arg]["offset"] == by_arg[callback_arg]["offset"]:
            continue
        entries = []
        for slot in range(table, end, 8):
            name, callback = struct.unpack(">II", image.read(slot, 8))
            if name not in anchor_addresses or callback not in image.by_start:
                entries = []
                break
            entries.append({"build": image.build, "kind": "counted-descriptor-loop",
                            "name_address": hx(name), "callback": hx(callback),
                            "callback_boundary": boundary(image.by_start[callback]),
                            "registration_function": call["function"], "call_instruction": call["instruction"],
                            "callee": hx(callee), "name_store": by_arg[name_arg], "callback_store": by_arg[callback_arg],
                            "table_start": hx(table), "table_end_exclusive": hx(end), "slot": hx(slot), "stride": 8,
                            "loop_instructions": [hx(loop_start), hx(loop_start + 4), hx(pc), hx(pc + 4), hx(pc + 8), hx(pc + 12)],
                            "compatible_repetitions": (end - table) // 8, "namespace_proven": False,
                            "status": "proven-native-descriptor", "reasons": []})
        results.extend(entries)
    return results


def recover_counted_registration_loops(image, anchor_addresses):
    candidates = []
    for function in image.functions:
        size = function["end"] - function["start"]
        if size > 256:
            continue
        words = [w[0] for w in struct.iter_unpack(">I", image.read(function["start"], size))]
        for index, word in enumerate(words[:-3]):
            if word >> 26 != 18 or not (word & 1):
                continue
            # This is only the provable first-entry path to a strict loop.
            # All references from this speculative prefix are discarded.
            if any(w >> 26 not in (14, 15, 24, 25, 32) for w in words[:index]):
                continue
            _, _, calls = scan_function(image, function, anchor_addresses,
                                        prefix_end=function["start"] + (index + 1) * 4)
            candidates.extend(calls)
    return counted_registration_loops(image, anchor_addresses, candidates)


def expand(seeds, edges, depth=1, fanout=8):
    """Return review-only edges, with explicit fan-out and cycle boundaries."""
    result = []
    for seed in sorted(set(seeds)):
        visited, frontier = {seed}, [seed]
        for level in range(depth):
            following = []
            for source in sorted(frontier):
                targets = sorted(set(edges.get(source, [])))
                if len(targets) > fanout:
                    result.append({"seed": seed, "source": source, "target": None,
                                   "depth": level + 1, "reason": "fanout-limit", "available": len(targets),
                                   "semantic_acceptance": False})
                    continue
                for target in targets:
                    cycle = target in visited
                    result.append({"seed": seed, "source": source, "target": target,
                                   "depth": level + 1, "reason": "cycle" if cycle else "call-neighbour-only",
                                   "available": len(targets), "semantic_acceptance": False})
                    if not cycle:
                        visited.add(target)
                        following.append(target)
            frontier = following
    return result
