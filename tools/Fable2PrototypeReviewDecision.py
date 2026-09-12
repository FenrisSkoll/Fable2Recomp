#!/usr/bin/env python3
"""Reconcile a frozen independent reconstruction into pending human review."""
from __future__ import annotations
import argparse
import bisect
import collections
import datetime
import itertools
import json
import re
import struct
import subprocess

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


def lexical_subsystems(profile):
    text = '\n'.join(x['object']['text'] for x in profile['references']).lower()
    patterns = {'physics': r'physics|havok|collision', 'combat': r'combat|damage|attack|weapon',
                'ai-navigation': r'navigat|pathfind|kynapse|behaviour|behavior|perception',
                'audio': r'audio|sound|music', 'debug': r'debug|profil|assert', 'lua': r'lua|script',
                'renderer': r'render|shader|graphic|d3d|texture', 'assertions': r'assert|invalid|cannot|can not|error',
                'source-paths': r'\.(?:cpp|hpp|h)(?:$|\s)|sourcecode'}
    return sorted(k for k, pattern in patterns.items() if re.search(pattern, text)) or ['unassigned']


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


def cfg_signature(image, start):
    f = image.by_start[int(start, 16)]
    code = r.words_at(image, f)
    shape = []
    for i, w in enumerate(code):
        if w >> 26 in (16, 18):
            target = r.native.branch(w, f['start'] + i * 4)
            shape.append([i * 4, r.normalize(w), target - f['start'] if f['start'] <= target < f['end'] else 'external'])
        elif w >> 26 == 19 and (w >> 1) & 1023 in (16, 528):
            shape.append([i * 4, w, 'indirect-or-return'])
    return r.sha(r.payload([len(code), shape]))


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


def validate_ledger(ledger, external_decisions=None, require_pending=True):
    external_decisions = external_decisions or {}
    ids = [x['id'] for x in ledger['records']]
    r.require(len(ids) == len(set(ids)), 'Duplicate ledger identity')
    expected_hash = r.sha(r.payload(sorted(ids)))
    r.require(ledger['proposal_set_sha256'] == expected_hash, 'Ledger proposal-set hash mismatch')
    for row in ledger['records']:
        r.require(row['human_decision'] in ('pending', 'approved', 'rejected'), 'Invalid human decision')
        if row['human_decision'] == 'pending':
            r.require(row.get('human_decision_evidence') is None, 'Pending row has decision evidence')
            continue
        r.require(not require_pending, 'Phase 2D decisions must remain pending')
        evidence = row.get('human_decision_evidence') or {}
        for key in ('external_decision_id', 'timestamp', 'approver', 'proposal_set_sha256', 'batch_id'):
            r.require(isinstance(evidence.get(key), str) and bool(evidence[key].strip()), 'Missing explicit human ' + key)
        supplied = datetime.datetime.fromisoformat(evidence['timestamp'].replace('Z', '+00:00'))
        r.require(supplied.tzinfo is not None, 'Human timestamp must include a timezone')
        r.require(evidence['proposal_set_sha256'] == expected_hash and evidence['batch_id'] == row['batch_id'], 'Human decision batch/set mismatch')
        external = external_decisions.get(evidence['external_decision_id'])
        r.require(external is not None and external == {**evidence, 'decision': row['human_decision']}, 'Explicit external human decision not supplied')


def simulation(closed, packets, included):
    rows = {p['id']: p for p in packets}
    r.require(len(included) == len(set(included)), 'Duplicate simulation proposal')
    selected = [rows[i] for i in sorted(included)]
    r.require(all(p['disposition'] in (RECOMMEND, RESERVE) for p in selected), 'Held or rejected proposal in simulation')
    seeds = {p['donor_start']: p['target_start'] for p in closed if p['donor_start'] not in r.SUPPRESSIONS}
    result = graph_valid(seeds, selected)
    r.require(all(result.get(a) != b for a, b in r.SUPPRESSIONS.items()), 'Suppression precedence failure')
    return {'records': [{'donor_start': a, 'target_start': b} for a, b in sorted(result.items())],
            'additions': sorted(included), 'count': len(result), 'delta_from_phase2a': len(result) - 15299,
            'delta_from_phase2c': len(result) - 15382, 'human_approval': False, 'canonical_consumer_enabled': False}


def challenges(packet):
    p = packet
    ds, ts = p['donor_profile'], p['target_profile']
    dependencies = p['dependencies']
    # Each challenge carries its actual observed evidence in the full packet.
    tests = [
        ('reverse-direction-uniqueness', p['blind']['reverse_count'] == 1, 'blind.reverse_donors'),
        ('full-target-population-uniqueness', p['blind']['candidate_count'] == 1, 'blind.targets'),
        ('global-injectivity', p['gates']['global-injectivity'], 'gates.global-injectivity'),
        ('same-size-CFG-competitors', p['blind']['selected_target'] == p['target_start'], 'compatible_targets'),
        ('reference-entropy', any(x['unique_in_each_population'] for x in p['reference_distinctiveness']) or p['reference_identity_count'] >= 2, 'reference_distinctiveness'),
        ('helper-commonness', not p['helpers'] or any(x['distinctive_within_compatible_callers'] for x in p['helpers']), 'helpers'),
        ('duplicate-wrapper-boilerplate', len(p['compatible_targets']) == 1, 'compatible_targets'),
        ('same-address-changed-content', not any(x['kind'] == 'contradictory-complete-reference-use' for x in p['contradictions']), 'contradictions'),
        ('complete-definition-use', p['gates']['reference-definition-use'], 'donor_profile.references'),
        ('prefix-interior-empty-window', all(x['object']['proven'] for x in ds['references'] + ts['references']), 'donor_profile.references;target_profile.references;rejected_references'),
        ('caller-callee-role', not any(x['kind'] == 'trusted-callee-conflict' for x in p['contradictions']), 'independent_support'),
        ('same-generation-circular-support', all(x['generation'] < p['generation'] for x in dependencies), 'dependencies'),
        ('suppressed-seed', not any(x['donor'] in r.SUPPRESSIONS for x in dependencies), 'dependencies'),
        ('code-region-not-function', all(not x[side]['independent_pdata_entry'] for x in p['internal_regions'] for side in ('donor', 'target')), 'internal_regions'),
        ('boundary-disagreement', p['gates']['boundary-size'], 'donor;target'),
        ('field-width-argument-return-CFG', p['gates']['field-parameter-return-role'], 'behavior'),
        ('unresolved-control-flow', not p['unresolved'], 'unresolved'),
        ('target-use-semantic-conflict', not p['contradictions'], 'contradictions'),
        ('canonicalization-not-independent-vote', all(x not in ('string', 'reference') for x in p['independent_classes']), 'independent_classes'),
        ('callee-import-overlap', all(x['callee_import_obligation_count'] == 1 for x in p['helpers']), 'helpers'),
    ]
    return {'id': p['id'], 'tests': [{'challenge': name, 'result': 'satisfied' if passed else 'risk-or-failure', 'evidence_field': path} for name, passed, path in tests],
            'counterfactuals': p['counterfactuals'], 'material_contradictions': p['contradictions'],
            'unresolved_transfers': p['unresolved'], 'disposition': p['disposition'], 'packet_sha256': r.sha(r.payload(p))}


def probable_blockers(p):
    states = {key: 'satisfied' for key in BLOCKERS}
    for gate, passed in p['gates'].items():
        if not passed:
            states[gate] = 'blocking'
    classes = set(p['independent_classes'])
    states['trusted-caller'] = 'present' if 'caller' in classes else 'absent-alternative'
    states['trusted-callee-helper'] = 'blocking' if any(x['kind'] in ('callee-not-retained', 'unowned-call-region-not-proven') for x in p['unresolved']) else 'present' if 'callee' in classes else 'absent-alternative'
    states['neighbourhood'] = 'present' if 'neighbourhood-order' in classes else 'absent-alternative'
    if len(p['blind']['targets']) != 1 or len(p['blind']['reverse_donors']) != 1:
        states['competing-candidate'] = 'blocking'
    if p['unresolved']:
        states['unresolved-tail-call-indirect'] = 'blocking'
    if p['contradictions']:
        states['semantic-contradiction'] = 'blocking'
    if 'low-entropy-common-evidence' in p['reasons']:
        states['low-entropy-common-evidence'] = 'blocking'
    if any(x['kind'] == 'unowned-call-region-not-proven' for x in p['unresolved']):
        states['boundary-code-region-ambiguity'] = 'blocking'
    if not classes:
        states['insufficient-independent-corroboration'] = 'blocking'
    blocking = sorted(k for k, v in states.items() if v == 'blocking')
    transfer_classes = sorted({x['kind'] for x in p['unresolved']})
    return {'id': p['id'], 'disposition': p['disposition'], 'blockers': blocking, 'obligation_states': states,
            'exclusive_blocker_signature': '+'.join(blocking) if blocking else 'none',
            'transfer_classes': transfer_classes, 'unresolved': p['unresolved'],
            'bounded_recovery': {'raw_full_population_reconstruction': True, 'non_pdata_region_comparison_attempted': True,
                                 'retained_seed_support_recomputed': True, 'generations_attempted': [1],
                                 'proposal_derived_seeds_used': False, 'promotable': p['disposition'] in (RECOMMEND, RESERVE)},
            'packet_sha256': r.sha(r.payload(p)), 'intersections': p['intersections']}


def known_cases(review, packets):
    suppressions = []
    for ds, ts in sorted(r.SUPPRESSIONS.items()):
        d, t = review.by[r.DONOR][ds], review.by[r.TARGET][ts]
        def key(ref, start):
            v = ref['reference']
            return (int(v['instruction'], 16) - int(start, 16), v['role'], v['operand'])
        targets = {key(x, ts): x for x in t['references']}
        conflicts = []
        for x in d['references']:
            other = targets.get(key(x, ds))
            if other and x['object']['sha256'] != other['object']['sha256']:
                conflicts.append({'donor_use': x, 'target_use': other})
        r.require(conflicts, 'Suppression conflict not reproduced: ' + ds)
        suppressions.append({'id': 'suppress:' + ds + ':' + ts, 'donor_start': ds, 'target_start': ts,
                             'donor': d['boundary'], 'target': t['boundary'], 'conflicts': conflicts,
                             'disposition': 'retain-mandatory-semantic-transport-suppression',
                             'original_phase2a_record_sha256': r.sha(r.payload(review.closed[ds])),
                             'human_decision': 'pending', 'canonical_adoption': False})
    requests = [(r.DONOR, '0x82631A30'), (r.TARGET, '0x82630C30'), (r.DONOR, '0x829506B0'), (r.TARGET, '0x82950A98'),
                (r.DONOR, '0x8222D118'), (r.TARGET, '0x8222CED0'), (r.DONOR, '0x82207A68'), (r.TARGET, '0x822078A0'),
                (r.DONOR, '0x82215000'), (r.TARGET, '0x821C6768'),
                (r.DONOR, '0x8229B308'), (r.TARGET, '0x8229B038'), (r.DONOR, '0x8229B488'), (r.TARGET, '0x8229B1B8')]
    functions = []
    for build, start in requests:
        profile = review.by[build][start]
        block = review.images[build].block(int(start, 16))
        command = ['out/tools/ppc-disasm.exe', profile['raw_source']['path'], r.native.hx(block.start), start, profile['boundary']['end_exclusive']]
        assembly = subprocess.check_output(command, cwd=r.ROOT, text=True).splitlines()
        functions.append({'build': build, 'profile': profile, 'disassembly': assembly, 'command': command,
                          'callers': review.callers[build][start], 'body': review.body(build, start),
                          'retained_correspondence': review.seeds.get(start) if build == r.DONOR else None,
                          'branch_normalized_competitors': [p['start'] for p in review.profiles[build] if p['branch_normalized_sha256'] == profile['branch_normalized_sha256']]})
    regions = [review.region(build, start) for build, start in ((r.DONOR, '0x8226DB80'), (r.TARGET, '0x8226D7F8'))]
    r.require(all(x['instruction_count'] == 21 and not x['independent_pdata_entry'] and x['owner'] is None and not x['problems'] for x in regions), 'Hammer comparator ownership/reachability changed')
    r.require(regions[0]['raw_sha256'] == regions[1]['raw_sha256'], 'Hammer comparator bytes differ')
    hammer = next(p for p in packets if p['donor_start'] == '0x8229B488')
    # Bind specific semantic claims to the independently read words, not names.
    caller = review.by[r.TARGET]['0x8229B038']
    caller_words = r.words_at(review.images[r.TARGET], review.images[r.TARGET].by_start[0x8229B038])
    r.require(any(w == 0x38630008 or w >> 26 == 14 and ((w >> 21) & 31) == 3 and w & 65535 == 8 for w in caller_words), 'Hammer caller object +8 not reproduced')
    callee_words = r.words_at(review.images[r.TARGET], review.images[r.TARGET].by_start[0x8229B1B8])
    r.require(callee_words[0x54 // 4] >> 26 == 18 and callee_words[0x68 // 4] == 0x5543DFFE, 'Hammer inequality return shape changed')
    secondary = r.read(r.CO / 'september-pairs.json')['original_pairs']
    routes = [{'september_start': p['donor_start'], 'build23_start': p['target_start'], 'blocked_by_suppression': p['target_start'] in r.SUPPRESSIONS} for p in secondary if p['target_start'] in r.SUPPRESSIONS]
    return r.envelope('known-cases', suppressions=suppressions, functions=functions, comparator_regions=regions,
                      physics=[{'id': p['id'], 'disposition': p['disposition'], 'reasons': p['reasons']} for p in packets if (p['donor_start'], p['target_start']) in r.PHYSICS],
                      physics_helper_obligations={'donor_global': '0x83497084', 'target_global': '0x83497088',
                        'role': 'atomic increment via lwarx/stwcx.; matching access shape does not prove global identity',
                        'unproven_global_identity': True, 'changed_call_pair': ['0x82215000', '0x821C6768'],
                        'missing_evidence': 'Independent full helper correspondence, mutable global identity and all helper call/tail obligations; wrapper spelling supplies none.'},
                      hammer={'id': hammer['id'], 'disposition': hammer['disposition'], 'semantic_role': 'exclusion guard involving HammerCombat and object offset +8; no function name assigned',
                              'caller_raw_sha256': caller['raw_sha256'], 'comparator_role': 'signed-byte lexical comparison returning -1, 0 or 1',
                              'callee_return_role': 'inequality; caller returns zero on equality with HammerCombat',
                              'empty_fallbacks': [x['object'] for p in (hammer['donor_profile'], hammer['target_profile']) for x in p['references'] if x['object']['relation'] == 'empty-at-terminator']},
                      blocked_september_routes=routes, disassembler=r.identity(r.Path('out/tools/ppc-disasm.exe')))


def package(review, packets, check=False):
    strong = [p for p in packets if p['original_phase2c_grade'] == 'reviewed-strong-proposal']
    probable = [p for p in packets if p['original_phase2c_grade'] == 'reviewed-probable-proposal']
    r.require(len(strong) == 86 and len(probable) == 715 and len(packets) == 803, 'Terminal population mismatch')
    r.require(len({p['id'] for p in packets}) == len(packets), 'Duplicate packet')
    graph_valid(review.seeds, [p for p in packets if p['disposition'] in (RECOMMEND, RESERVE)])
    known = known_cases(review, packets)
    r.write(r.OUT / 'known-cases.json', known, check)
    challenge = [challenges(p) for p in packets]
    r.write(r.OUT / 'adversarial-challenge.json', r.envelope('challenge', records=challenge), check)
    blockers = [probable_blockers(p) for p in probable]
    r.write(r.OUT / 'probable-blockers.json', r.envelope('probable-blockers', records=blockers,
          exclusive_distribution=dict(sorted(collections.Counter(p['exclusive_blocker_signature'] for p in blockers).items())),
          overlapping_distribution={k: sum(p['obligation_states'][k] == 'blocking' for p in blockers) for k in BLOCKERS}), check)
    used = sorted({(x['donor'], x['target']) for p in strong for x in p['dependencies']})
    r.write(r.OUT / 'dependency-seeds.json', r.envelope('dependencies', records=[{'donor_start': a, 'target_start': b, 'generation': 0,
          'closed_record': review.closed[a], 'raw_donor': review.by[r.DONOR][a]['raw_sha256'], 'raw_target': review.by[r.TARGET][b]['raw_sha256']} for a, b in used],
          edges=[{'id': p['id'], 'generation': p['generation'], 'dependencies': p['dependencies']} for p in packets]), check)
    callee = {p['id'] for p in strong if p['phase2c_support_combination'] == ['trusted-mapped-callee']}
    rich = {p['id'] for p in strong} - callee
    multi = {p['id'] for p in strong if p['reference_identity_count'] >= 2}
    r.require(len(callee) == 66 and len(rich) == 20 and len(multi) == 17, 'Frozen support strata mismatch')
    strata = {'callee-only': sorted(callee), 'richer-support': sorted(rich), 'multi-reference': sorted(multi),
              'callee-only-and-multi-reference': sorted(callee & multi), 'richer-and-multi-reference': sorted(rich & multi)}
    batches, assigned = [], {}
    rules = [('B01-unreserved', lambda p: p['disposition'] == RECOMMEND),
             ('B02-multiple-references-reserved', lambda p: p['disposition'] == RESERVE and p['id'] in multi),
             ('B03-richer-support-reserved', lambda p: p['disposition'] == RESERVE and p['id'] in rich and not p['internal_regions']),
             ('B04-callee-only-reserved', lambda p: p['disposition'] == RESERVE and p['id'] in callee),
             ('B05-internal-region-reserved', lambda p: p['disposition'] == RESERVE and bool(p['internal_regions'])),
             ('B06-former-probable', lambda p: p in probable and p['disposition'] in (RECOMMEND, RESERVE))]
    cumulative = []
    for batch_id, predicate in rules:
        selected = [p for p in packets if p['id'] not in assigned and predicate(p)]
        for p in selected:
            assigned[p['id']] = batch_id
        ids = sorted(p['id'] for p in selected)
        cumulative += ids
        batches.append({'id': batch_id, 'mapping_ids': ids, 'mapping_count': len(ids), 'proposal_set_sha256': r.sha(r.payload(ids)),
                        'resulting_simulated_count_if_prior_batches_approved': 15296 + len(cumulative), 'human_decision': 'pending'})
    unreserved = [p['id'] for p in packets if p['disposition'] == RECOMMEND and p not in probable]
    reserved = [p['id'] for p in strong if p['disposition'] in (RECOMMEND, RESERVE)]
    promotions = [p['id'] for p in probable if p['disposition'] in (RECOMMEND, RESERVE)]
    simulations = {'unreserved': simulation(review.closed_rows, packets, unreserved),
                   'unreserved-plus-reservations': simulation(review.closed_rows, packets, reserved),
                   'former-probable-only': simulation(review.closed_rows, packets, promotions),
                   'all-recommended-including-former-probable': simulation(review.closed_rows, packets, reserved + promotions)}
    frozen = r.read(r.CO / 'completion/effective-map.json')
    simulations['frozen-phase2c-comparison'] = {'count': len(frozen['records']), 'delta_from_phase2a': 83, 'delta_from_phase2c': 0,
        'source': r.identity(r.CO / 'completion/effective-map.json'), 'human_approval': False, 'canonical_consumer_enabled': False,
        'limitation': 'Unchanged frozen comparison includes proposals that Phase 2D may hold; it is not a Phase 2D adoption recommendation.'}
    r.write(r.OUT / 'adoption-simulations.json', r.envelope('simulations', views=simulations), check)
    r.write(r.OUT / 'risk-strata-and-batches.json', r.envelope('batches', strata=strata, records=batches,
          mandatory_suppression_batch={'id': 'B00-semantic-suppressions', 'mapping_count': 3, 'mapping_ids': [x['id'] for x in known['suppressions']], 'human_decision': 'pending'},
          overlap={'callee_plus_rich': 86, 'callee_intersection_rich': 0, 'callee_intersection_multi': len(callee & multi), 'rich_intersection_multi': len(rich & multi)}), check)
    index = []
    for p in packets:
        index.append({k: p[k] for k in ('id', 'donor_start', 'target_start', 'donor', 'target', 'original_phase2c_grade', 'original_phase2c_generation',
            'disposition', 'reasons', 'human_decision', 'blind_result', 'independent_classes', 'dependencies', 'reference_identity_count', 'intersections', 'lexical_subsystems')} |
            {'batch_id': assigned.get(p['id']), 'packet_sha256': r.sha(r.payload(p)), 'competitor_count': len(p['blind']['targets']),
             'reference_identities': [{'identity': x['identity'], 'role': x['role']} for x in p['donor_profile']['canonical_tokens']],
             'reference_distinctiveness': p['reference_distinctiveness'],
             'reference_text': sorted({x['object']['text'] for x in p['donor_profile']['references']}),
             'risk_strata': sorted(name for name, ids in strata.items() if p['id'] in ids), 'adversarial_result': 'hold-or-rejection' if p['disposition'] not in (RECOMMEND, RESERVE) else 'survives-with-reservation' if p['disposition'] == RESERVE else 'survives'})
    r.write(r.OUT / 'review-index.json', r.envelope('review-index', records=index), check)
    ledger = [dict(x, human_decision_evidence=None) for x in index if x['original_phase2c_grade'] != 'reviewed-probable-proposal' or x['id'] in promotions]
    ledger += [{**x, 'batch_id': 'B00-semantic-suppressions', 'human_decision_evidence': None} for x in known['suppressions']]
    ledger.sort(key=lambda x: x['id'])
    decision = r.envelope('human-decision-ledger', records=ledger, proposal_set_sha256=r.sha(r.payload([x['id'] for x in ledger])))
    validate_ledger(decision)
    r.write(r.DOC / 'evidence/human-decision-ledger.json', decision, check)
    summary = r.envelope('review-summary', strong_dispositions={k: sum(p['disposition'] == k for p in strong) for k in DISPOSITIONS},
          blind_counts={k: sum(p['blind_result'] == k for p in strong) for k in ('unique-same-target', 'tied', 'different-target', 'no-candidate')},
          probable_dispositions={k: sum(p['disposition'] == k for p in probable) for k in DISPOSITIONS},
          probable_exclusive_blockers=dict(sorted(collections.Counter(p['exclusive_blocker_signature'] for p in blockers).items())),
          probable_overlapping_blockers={k: sum(p['obligation_states'][k] == 'blocking' for p in blockers) for k in BLOCKERS},
          probable_promotions=promotions, strata={name: {'ids': ids, 'count': len(ids), 'dispositions': {k: sum(p['id'] in ids and p['disposition'] == k for p in strong) for k in DISPOSITIONS}} for name, ids in strata.items()},
          probable_priority_populations={name: {'available': sum(name in p['lexical_subsystems'] or any(x['set'] == name for x in p['intersections']) for p in probable),
              'inspected': sum(name in p['lexical_subsystems'] or any(x['set'] == name for x in p['intersections']) for p in probable),
              'recommended': sum(p['disposition'] in (RECOMMEND, RESERVE) and (name in p['lexical_subsystems'] or any(x['set'] == name for x in p['intersections'])) for p in probable)}
              for name in ('physics', 'combat', 'ai-navigation', 'audio', 'debug', 'lua', 'renderer', 'assertions', 'source-paths', 'closure', 'coverage', 'ghidra', 'ownership', 'indirect', 'historical-crash')},
          strong_intersections={name: sum(any(x['set'] == name for x in p['intersections']) for p in strong) for name in review.problem_sets},
          challenge_totals=dict(sorted(collections.Counter(x['result'] for p in challenge if p['id'] in {s['id'] for s in strong} for x in p['tests']).items())),
          material_contradictions=[{'id': p['id'], 'contradictions': p['contradictions']} for p in packets if p['contradictions']],
          unresolved_strong=[{'id': p['id'], 'transfers': p['unresolved']} for p in strong if p['unresolved']],
          simulations={name: {k: v[k] for k in ('count', 'delta_from_phase2a', 'delta_from_phase2c')} for name, v in simulations.items()},
          batches=batches, pending_decisions=len(ledger), inherited_blockers=r.read(r.C / 'evidence/validation.json')['remaining_blockers'])
    r.write(r.DOC / 'evidence/review-summary.json', summary, check)
    print(json.dumps(summary['strong_dispositions']), flush=True)
    print('Probable:', json.dumps(summary['probable_dispositions']), flush=True)


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
        self.cfg_groups = {b: collections.defaultdict(list) for b in self.by}
        self.cfg_keys = {}
        self.identities = {b: collections.defaultdict(set) for b in self.by}
        for build, rows in self.profiles.items():
            for p in rows:
                cfg = cfg_signature(self.images[build], p['start'])
                self.cfg_keys[(build, p['start'])] = cfg
                self.cfg_groups[build][cfg].append(p['start'])
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
        self.frozen_ablation = {p['id']: p for p in r.read(r.CO / 'completion/feature-ablation.json')['proposal_packets']}

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
        unresolved.extend({**flow, 'transfer_register': flow['kind'], 'kind': 'indirect-flow', 'build': build} for build, p in ((r.DONOR, d), (r.TARGET, t)) for flow in p['indirect'])
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
            # Content at a high-half scratch value is not proof of a string use.
            # Rejected definition chains stay in the packet as negative evidence.
            return p['references']
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
            comparable_survives = all(gates.values()) and not contradictions and not any(x['kind'] != 'indirect-flow' for x in unresolved) and bool(remain) and not missing
            frozen_result = next(x['semantic_transport'] for x in self.frozen_ablation[ds + ':' + ts]['counterfactuals'] if x['removed'] == [removed])
            counterfactuals.append({'removed': removed, 'strong_policy_survives': all(gates.values()) and not contradictions and not unresolved and bool(remain) and not missing,
                                    'phase2c_direct_transfer_policy_reproduced': comparable_survives,
                                    'frozen_phase2c_policy_result': frozen_result,
                                    'frozen_policy_agrees': comparable_survives == frozen_result,
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
                'same_size_cfg_targets': self.cfg_groups[r.TARGET][self.cfg_keys[(r.DONOR, ds)]],
                'same_size_cfg_donors': self.cfg_groups[r.DONOR][self.cfg_keys[(r.TARGET, ts)]],
                'intersections': intersections, 'lexical_subsystems': lexical_subsystems(d),
                'phase2c_support_combination': sorted({s['class'] for s in proposal['independent_support']})}


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
    package(review, packets, args.check)


if __name__ == '__main__':
    main()
