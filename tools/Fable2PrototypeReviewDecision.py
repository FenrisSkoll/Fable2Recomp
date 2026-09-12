#!/usr/bin/env python3
"""Reconcile a frozen independent reconstruction into pending human review."""
from __future__ import annotations
import argparse
import bisect
import collections
import itertools
import json
import struct

import Fable2PrototypeReview as r

RECOMMEND = 'recommend-human-approval'
RESERVE = 'recommend-human-approval-with-reservation'
HOLD = 'hold-for-additional-evidence'
DOWNGRADE = 'recommend-downgrade'
REJECT = 'recommend-rejection'
DISPOSITIONS = (RECOMMEND, RESERVE, HOLD, DOWNGRADE, REJECT)
CLASSES = ('string-data-canonicalization', 'caller', 'callee', 'neighbourhood-order',
           'cfg-branch', 'boundary-size', 'import-helper-call', 'field-parameter-return-role',
           'September-two-hop', 'boundary-code-region', 'same-generation-derived')
BLOCKERS = ('reciprocal-uniqueness', 'global-injectivity', 'boundary-size', 'cfg-branch',
            'reference-definition-use', 'complete-reference-identity', 'field-parameter-return-role',
            'trusted-caller', 'trusted-callee-helper', 'neighbourhood', 'competing-candidate',
            'unresolved-tail-call-indirect', 'semantic-contradiction', 'low-entropy-common-evidence',
            'boundary-code-region-ambiguity', 'insufficient-independent-corroboration')


def frozen_reconstruction():
    freeze = r.read(r.OUT / 'reconstruction-freeze.json')
    for row in freeze['artifacts'] + [freeze['implementation']]:
        r.check_identity(r.ROOT, row)
    r.require(freeze['semantic_feedback_allowed'] is False, 'Reconstruction semantic feedback')
    return freeze


def dominance(root, edges):
    children, parents = collections.defaultdict(set), collections.defaultdict(set)
    for a, b in edges:
        children[a].add(b); parents[b].add(a)
    reachable, todo = {root}, [root]
    while todo:
        for b in sorted(children[todo.pop()] - reachable):
            reachable.add(b); todo.append(b)
    result = {n: {root} if n == root else set(reachable) for n in reachable}
    for _ in range(len(reachable) + 1):
        changed = False
        for node in sorted(reachable - {root}):
            incoming = parents[node] & reachable
            value = {node} | set.intersection(*(result[p] for p in incoming))
            if result[node] != value:
                result[node] = value; changed = True
        if not changed:
            break
    return [[k, sorted(v)] for k, v in sorted(result.items())]


def behavior(image, start):
    f = image.by_start[int(start, 16)]
    words = r.words_at(image, f)
    size = len(words) * 4
    fields, registers, compares, returns, frames, branches = [], [], [], [], [], []
    leaders, successor = {0}, {}
    for i, w in enumerate(words):
        off, op = i * 4, w >> 26
        rt, ra, rb, xo = (w >> 21) & 31, (w >> 16) & 31, (w >> 11) & 31, (w >> 1) & 1023
        following = off + 4 if off + 4 < size else -1
        succ = [following]
        if op in (16, 18):
            dest = r.native.branch(w, f['start'] + off) - f['start']
            branches.append({'offset': off, 'opcode': op, 'link': bool(w & 1), 'absolute': bool(w & 2),
                             'relative_destination': dest if 0 <= dest < size else 'external',
                             'condition': (w >> 16) & 1023 if op == 16 else None})
            if not w & 1:
                succ = [dest if 0 <= dest < size else -1] + ([following] if op == 16 else [])
        elif op == 19 and xo in (16, 528) and not w & 1:
            succ = [-1] + ([following] if (w >> 21) & 31 != 20 else [])
            returns.append({'offset': off, 'kind': 'LR' if xo == 16 else 'CTR', 'conditional': (w >> 21) & 31 != 20})
        if succ != [following]:
            leaders.update(x for x in succ + [following] if x >= 0)
            successor[off] = succ
        if op in (32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 58, 62):
            width = 8 if op in (50, 51, 54, 55, 58, 62) else 1 if op in (34, 35, 38, 39) else 2 if op in (40, 41, 42, 43, 44, 45) else 4
            read = op in (32, 33, 34, 35, 40, 41, 42, 43, 46, 48, 49, 50, 51, 58)
            fields.append({'offset': off, 'opcode': op, 'base_register': ra, 'value_register': rt,
                           'displacement': r.native.signed(w & (0xFFFC if op in (58, 62) else 0xFFFF)),
                           'width': width, 'role': 'read' if read else 'write'})
        if op == 37 and rt == ra == 1:
            frames.append({'offset': off, 'delta': r.native.signed(w & 65535)})
        if op in (10, 11) or op == 31 and xo in (0, 32):
            compares.append({'offset': off, 'opcode': op, 'operand_bits': w & 0x03FFFFFF})
        registers.append({'offset': off, 'opcode': op, 'rt_rs': rt, 'ra': ra, 'rb_or_immediate_high': rb,
                          'xo_if_extended': xo if op in (19, 31) else None})
    starts = sorted(leaders)
    edges = set()
    exit_node = len(starts)
    for i, first in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else size
        for target in successor.get(end - 4, [end if end < size else -1]):
            edges.add((i, exit_node if target < 0 else bisect.bisect_right(starts, target) - 1))
    return {'fields': fields, 'stack_frames': frames, 'comparisons': compares, 'returns': returns,
            'branches': branches, 'block_starts': starts, 'edges': [list(e) for e in sorted(edges)],
            'dominators': dominance(0, edges), 'postdominators': dominance(exit_node, {(b, a) for a, b in edges}),
            'register_operands': registers,
            'limitation': 'Known direct CFG; calls assumed returning; unresolved indirect transfers are explicit. No source-level types or ABI parameter count inferred.'}


def compatible_behavior(a, b, definition_offsets):
    # The complete instruction signature separately preserves unrelated operands.
    # Address construction's immediate high bits are not parameter registers.
    def strip(v):
        return {k: x for k, x in v.items() if k != 'register_operands'}
    return strip(a) == strip(b)


def internal_region(image, start, maximum=256):
    origin = int(start, 16)
    seen, pending, edges, problems = {}, [origin], [], []
    while pending and len(seen) < maximum:
        pc = pending.pop()
        if pc in seen:
            continue
        block = image.block(pc, 4)
        if block is None or not block.execute or pc % 4 or abs(pc - origin) >= maximum * 4:
            problems.append({'address': r.native.hx(pc), 'reason': 'outside-bounded-executable-region'}); continue
        if pc in image.by_start:
            problems.append({'address': r.native.hx(pc), 'reason': 'independent-pdata-entry'}); continue
        w = int.from_bytes(image.read(pc, 4), 'big')
        seen[pc] = w
        if w == 0x4E800020:
            targets = []
        elif w >> 26 in (16, 18) and not w & 1:
            targets = [r.native.branch(w, pc)] + ([pc + 4] if w >> 26 == 16 else [])
        elif w >> 26 in (16, 18, 19):
            problems.append({'address': r.native.hx(pc), 'reason': 'call-or-unresolved-indirect'}); targets = []
        else:
            targets = [pc + 4]
        for target in targets:
            edges.append([pc - origin, target - origin]); pending.append(target)
    if pending:
        problems.append({'address': start, 'reason': 'bounded-instruction-limit'})
    return {'kind': 'internal-code-region', 'start': start,
            'end_exclusive': r.native.hx(max(seen) + 4) if seen else None,
            'independent_pdata_entry': origin in image.by_start,
            'owner': r.native.boundary(image.owner(origin)) if image.owner(origin) else None,
            'instruction_count': len(seen), 'reachable_sha256': r.sha(r.payload([[pc - origin, w] for pc, w in sorted(seen.items())])),
            'raw_sha256': r.sha(b''.join(struct.pack('>I', w) for _, w in sorted(seen.items()))),
            'edges': sorted(edges), 'problems': problems}


def graph_valid(seeds, proposals):
    mapping = dict(seeds)
    generations = {d: 0 for d in seeds}
    r.require(not set(seeds) & set(r.SUPPRESSIONS), 'Suppressed seed')
    for p in sorted(proposals, key=lambda p: (p['generation'], p['donor_start'], p['target_start'])):
        d, t = p['donor_start'], p['target_start']
        r.require(d not in mapping and t not in mapping.values(), 'Global injectivity conflict')
        r.require(r.SUPPRESSIONS.get(d) != t, 'Suppression conflict')
        for dep in p['dependencies']:
            r.require(dep['donor'] in mapping and mapping[dep['donor']] == dep['target'], 'Dangling or circular dependency')
            r.require(generations[dep['donor']] < p['generation'], 'Same-generation dependency')
        mapping[d] = t; generations[d] = p['generation']
    return mapping


def choose_disposition(facts):
    if facts['contradictions']:
        return REJECT
    if not facts['mandatory_pass']:
        return DOWNGRADE if facts['original_grade'] == 'reviewed-strong-proposal' else HOLD
    if not facts['independent_classes'] or facts['unresolved']:
        return HOLD
    if facts['common_only']:
        return HOLD
    if facts['internal_region'] or len(facts['independent_classes']) == 1 or facts['common_helpers']:
        return RESERVE
    return RECOMMEND


class Review:
    def __init__(self):
        frozen_reconstruction()
        self.images = r.images()
        self.profiles = r.read(r.OUT / 'profiles.json')['builds']
        self.by = {b: {p['start']: p for p in rows} for b, rows in self.profiles.items()}
        self.blind = {p['donor_start']: p for p in r.read(r.OUT / 'blind-results.json')['records']}
        self.closed_rows = r.read('docs/fable2-prototype-archaeology/phase2a/evidence/prototype-correspondence-accepted.json')['records']
        self.closed = {p['donor_start']: p for p in self.closed_rows}
        audit = r.read(r.CO / 'trust-audit.json')['records']
        self.seeds = {p['donor_start']: p['target_start'] for p in audit if p['disposition'].startswith('retained-')}
        r.require(len(self.seeds) == 15296 and not set(self.seeds) & set(r.SUPPRESSIONS), 'Seed population mismatch')
        self.callers = {b: collections.defaultdict(list) for b in self.by}
        self.skeletons = {b: collections.defaultdict(list) for b in self.by}
        self.identities = {b: collections.defaultdict(set) for b in self.by}
        for build, rows in self.profiles.items():
            for p in rows:
                self.skeletons[build][p['reference_erased_sha256']].append(p['start'])
                for call in p['calls']:
                    self.callers[build][call['target']].append({'start': p['start'], 'offset': call['offset']})
                for ref in p['canonical_tokens']:
                    self.identities[build][r.sha(r.payload(ref['identity']))].add(p['start'])
        self.ordered = sorted(self.by[r.DONOR])
        self.behavior = {}
        self.regions = {}
        self.intersections = {p['target_start']: p['intersections'] for p in r.read(r.CO / 'intersections.json')['records']}
        # Intersection producers only supply context after reconstruction is frozen.
        import Fable2PrototypeSemantics as semantic
        self.problem_sets = semantic.problem_sets()
        self.semantic = semantic

    def body(self, build, start):
        key = (build, start)
        if key not in self.behavior:
            self.behavior[key] = behavior(self.images[build], start)
        return self.behavior[key]

    def region(self, build, start):
        key = (build, start)
        if key not in self.regions:
            self.regions[key] = internal_region(self.images[build], start)
        return self.regions[key]

    def support(self, d, t):
        support, conflicts, unresolved, regions, helpers = [], [], [], [], []
        tcalls = {c['offset']: c['target'] for c in t['calls']}
        for c in d['calls']:
            target = tcalls.get(c['offset'])
            donor = c['target']
            if donor in self.seeds:
                if self.seeds[donor] != target:
                    conflicts.append({'kind': 'trusted-callee-conflict', 'donor': donor, 'target': target, 'offset': c['offset']})
                else:
                    support.append({'class': 'callee', 'donor': donor, 'target': target, 'offset': c['offset']})
                    compatible = self.skeletons[r.TARGET][t['reference_erased_sha256']]
                    same_helper = [a for a in compatible if any(x['offset'] == c['offset'] and x['target'] == target for x in self.by[r.TARGET][a]['calls'])]
                    helpers.append({'donor': donor, 'target': target, 'offset': c['offset'],
                                    'donor_total_callers': len(self.callers[r.DONOR][donor]), 'target_total_callers': len(self.callers[r.TARGET][target]),
                                    'compatible_target_callers': same_helper, 'distinctive_within_compatible_callers': len(same_helper) == 1,
                                    'retained_seed_sha256': r.sha(r.payload(self.closed[donor])),
                                    'callee_import_obligation_count': 1})
            elif target is not None and int(donor, 16) not in self.images[r.DONOR].by_start and int(target, 16) not in self.images[r.TARGET].by_start:
                a, b = self.region(r.DONOR, donor), self.region(r.TARGET, target)
                if not a['problems'] and not b['problems'] and a['reachable_sha256'] == b['reachable_sha256']:
                    regions.append({'call_offset': c['offset'], 'donor': a, 'target': b})
                else:
                    unresolved.append({'kind': 'unowned-call-region-not-proven', 'donor': donor, 'target': target, 'offset': c['offset']})
            else:
                unresolved.append({'kind': 'callee-not-retained', 'donor': donor, 'target': target, 'offset': c['offset'], 'suppressed_seed': donor in r.SUPPRESSIONS})
        for call in self.callers[r.DONOR][d['start']]:
            caller = call['start']
            if caller in self.seeds:
                target_caller = self.by[r.TARGET][self.seeds[caller]]
                if any(c['offset'] == call['offset'] and c['target'] == t['start'] for c in target_caller['calls']):
                    support.append({'class': 'caller', 'donor': caller, 'target': target_caller['start'], 'offset': call['offset']})
        position = bisect.bisect_left(self.ordered, d['start'])
        neighbours = []
        for adjacent in self.ordered[max(0, position - 8):position + 9]:
            if adjacent != d['start'] and adjacent in self.seeds:
                delta = int(d['start'], 16) - int(adjacent, 16)
                if int(t['start'], 16) - int(self.seeds[adjacent], 16) == delta:
                    neighbours.append({'donor': adjacent, 'target': self.seeds[adjacent], 'relative_delta': delta})
        if any(n['relative_delta'] < 0 for n in neighbours) and any(n['relative_delta'] > 0 for n in neighbours):
            support.append({'class': 'neighbourhood-order', 'anchors': neighbours})
        if d['start'] in self.seeds and self.seeds[d['start']] != t['start']:
            conflicts.append({'kind': 'retained-donor-owned'})
        if t['start'] in self.seeds.values() and self.seeds.get(d['start']) != t['start']:
            conflicts.append({'kind': 'retained-target-owned'})
        unresolved.extend({'kind': 'external-tail', 'build': build, **tail} for build, p in ((r.DONOR, d), (r.TARGET, t)) for tail in p['tails'])
        unresolved.extend({'kind': 'indirect-flow', 'build': build, **flow} for build, p in ((r.DONOR, d), (r.TARGET, t)) for flow in p['indirect'])
        return support, conflicts, unresolved, regions, helpers, neighbours

    def packet(self, proposal):
        ds, ts = proposal['donor_start'], proposal['target_start']
        d, t = self.by[r.DONOR][ds], self.by[r.TARGET][ts]
        support, contradictions, unresolved, regions, helpers, neighbours = self.support(d, t)
        blind = self.blind[ds]
        outcome = 'unique-same-target' if blind['selected_target'] == ts else 'tied' if ts in blind['targets'] else 'no-candidate' if not blind['targets'] else 'different-target'
        da, ta = self.body(r.DONOR, ds), self.body(r.TARGET, ts)
        equal = compatible_behavior(da, ta, d['definition_offsets'])
        if not equal:
            contradictions.append({'kind': 'field-parameter-return-or-CFG-conflict'})
        if r.SUPPRESSIONS.get(ds) == ts:
            contradictions.append({'kind': 'mandatory-semantic-suppression'})
        # A same-address reference must compare its actual target content even
        # when it was not eligible for canonicalization.
        def references(p):
            return p['references'] + [{'reference': x['reference'], 'object': x['object']} for x in p['rejected_references']]
        target_uses = {(int(x['reference']['instruction'], 16) - int(ts, 16), x['reference']['role'], x['reference']['operand']): x for x in references(t)}
        content_conflicts = []
        for x in references(d):
            key = (int(x['reference']['instruction'], 16) - int(ds, 16), x['reference']['role'], x['reference']['operand'])
            other = target_uses.get(key)
            if other and x['object']['proven'] and other['object']['proven'] and (x['object']['sha256'], x['object'].get('interior_offset')) != (other['object']['sha256'], other['object'].get('interior_offset')):
                content_conflicts.append({'offset': key[0], 'role': key[1], 'operand': key[2], 'donor': x['object'], 'target': other['object']})
        contradictions.extend({'kind': 'contradictory-complete-reference-use', **x} for x in content_conflicts)
        identities = []
        for key in sorted({r.sha(r.payload(x['identity'])) for x in d['canonical_tokens']}):
            identities.append({'identity_hash': key, 'donor_users': sorted(self.identities[r.DONOR][key]),
                               'target_users': sorted(self.identities[r.TARGET][key]),
                               'unique_in_each_population': len(self.identities[r.DONOR][key]) == len(self.identities[r.TARGET][key]) == 1})
        classes = sorted({x['class'] for x in support})
        common_helpers = bool(helpers) and all(not x['distinctive_within_compatible_callers'] for x in helpers)
        common_only = classes == ['callee'] and common_helpers and not any(x['unique_in_each_population'] for x in identities) and len(identities) < 2
        gates = {'reciprocal-uniqueness': blind['selected_target'] == ts,
                 'boundary-size': d['boundary']['size'] == t['boundary']['size'],
                 'reference-definition-use': bool(d['canonical_tokens']) and d['canonical_sha256'] == t['canonical_sha256'],
                 'complete-reference-identity': d['canonical_tokens'] == t['canonical_tokens'],
                 'cfg-branch': da['edges'] == ta['edges'] and da['branches'] == ta['branches'],
                 'field-parameter-return-role': equal,
                 'global-injectivity': not any(x['kind'].startswith('retained-') for x in contradictions)}
        facts = {'original_grade': proposal['grade'], 'mandatory_pass': all(gates.values()),
                 'independent_classes': classes, 'contradictions': contradictions, 'unresolved': unresolved,
                 'internal_region': bool(regions), 'common_helpers': common_helpers, 'common_only': common_only}
        disposition = choose_disposition(facts)
        reasons = [k for k, passed in gates.items() if not passed]
        if unresolved: reasons.append('unresolved-tail-call-indirect')
        if not classes: reasons.append('insufficient-independent-corroboration')
        if common_only: reasons.append('low-entropy-common-evidence')
        if contradictions: reasons.append('semantic-contradiction' if content_conflicts else 'incompatible-evidence')
        if disposition == RESERVE:
            if len(classes) == 1: reasons.append('single-independent-support-class')
            if common_helpers: reasons.append('common-helper-obligation')
            if regions: reasons.append('internal-code-region-dependent')
        dependencies = {}
        for s in support:
            for dep in s.get('anchors', [s]):
                key = (dep['donor'], dep['target'])
                dependencies[key] = {'donor': key[0], 'target': key[1], 'generation': 0,
                                     'closed_record_sha256': r.sha(r.payload(self.closed[key[0]]))}
        dw = r.words_at(self.images[r.DONOR], self.images[r.DONOR].by_start[int(ds, 16)])
        tw = r.words_at(self.images[r.TARGET], self.images[r.TARGET].by_start[int(ts, 16)])
        instructions = [{'offset': i * 4, 'donor': f'0x{a:08X}', 'target': f'0x{b:08X}', 'equal': a == b,
                         'reference_definition': i * 4 in d['definition_offsets'], 'branch': a >> 26 in (16, 18)} for i, (a, b) in enumerate(zip(dw, tw))]
        counterfactuals = []
        for removed in CLASSES:
            remain = [c for c in classes if c != removed and not (removed == 'import-helper-call' and c == 'callee')]
            missing = removed in ('string-data-canonicalization', 'cfg-branch', 'boundary-size', 'field-parameter-return-role')
            missing |= removed in ('callee', 'import-helper-call') and bool(helpers)
            missing |= removed == 'boundary-code-region' and bool(regions)
            counterfactuals.append({'removed': removed, 'strong_policy_survives': all(gates.values()) and not contradictions and not unresolved and bool(remain) and not missing,
                                    'independent_classes_remaining': remain, 'mandatory_obligation_removed': bool(missing)})
        intersections = self.semantic.intersections(t['boundary'], self.problem_sets)
        return {'id': ds + ':' + ts, 'donor_start': ds, 'target_start': ts, 'donor': d['boundary'], 'target': t['boundary'],
                'original_phase2c_grade': proposal['grade'], 'original_phase2c_generation': proposal['generation'],
                'original_proposal_sha256': r.sha(r.payload(proposal)), 'generation': 1,
                'disposition': disposition, 'reasons': sorted(set(reasons)), 'human_decision': 'pending',
                'canonical_adoption': False, 'blind': blind, 'blind_result': outcome,
                'donor_profile': d, 'target_profile': t, 'behavior': {'donor': da, 'target': ta},
                'instructions': instructions, 'gates': gates, 'independent_support': support,
                'independent_classes': classes, 'dependencies': [dependencies[k] for k in sorted(dependencies)],
                'helpers': helpers, 'neighbours': neighbours, 'reference_distinctiveness': identities,
                'reference_identity_count': len(identities), 'internal_regions': regions,
                'unresolved': unresolved, 'contradictions': contradictions, 'counterfactuals': counterfactuals,
                'compatible_donors': self.skeletons[r.DONOR][d['reference_erased_sha256']],
                'compatible_targets': self.skeletons[r.TARGET][t['reference_erased_sha256']],
                'intersections': intersections, 'phase2c_support_combination': sorted({s['class'] for s in proposal['independent_support']})}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['review'])
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    r.bind(True)
    review = Review()
    strong, probable = r.universe()
    source = r.read(r.CO / 'reference-candidates.json')['proposals']
    physics = [p for p in source if (p['donor_start'], p['target_start']) in r.PHYSICS]
    packets = [review.packet(p) for p in sorted(strong + probable + physics, key=lambda p: (p['donor_start'], p['target_start']))]
    r.write(r.OUT / 'packets.json', r.envelope('packets', records=packets, reconstruction_freeze=r.identity(r.OUT / 'reconstruction-freeze.json')), args.check)
    print(json.dumps(collections.Counter(p['disposition'] for p in packets if p['original_phase2c_grade'] == 'reviewed-strong-proposal')), flush=True)


if __name__ == '__main__':
    main()
