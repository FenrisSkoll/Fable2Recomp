#!/usr/bin/env python3
"""Phase 2C static trust analysis; never alters closed evidence or consumers."""
from __future__ import annotations

import argparse
import bisect
import collections
import hashlib
import json
import platform
import struct
import subprocess
from pathlib import Path

import Fable2PrototypeCorrespondence as old
import Fable2PrototypeSemantics as semantic
import Fable2SemanticNative as native

ROOT = Path(__file__).resolve().parents[1]
DOC = Path('docs/fable2-prototype-archaeology/phase2c')
OUT = Path('out/prototype-archaeology/phase2c')
BASE = '31d8693ca486758a63221346ce4d376b8865fd20'
TREE = '0d5537ffce89d5283d30d8b278909c2122580cdb'
BRANCH = 'fable2-prototype-archaeology-phase2c'
PRIMARY = 'build-23.12.02.0330'
TARGET = 'canonical-tu1'
PINS = DOC / 'evidence/source-pins.json'
EXTRA_PINS = DOC / 'evidence/semantic-extra-source-pins.json'
HASHES = {
    'docs/fable2-prototype-archaeology/phase2b/report.md': '1D3AA0A8EBC83ACB12C61841AA6F18ACF3E337432FF6028F68704EDD32D2BE0E',
    'docs/fable2-prototype-archaeology/phase2b/evidence/semantic-validation.json': '44AA74E385EC64A0EC21837FF527B5ECD672FF71293FCD41B6FB15B4F3C78D5E',
    'docs/fable2-prototype-archaeology/phase2b/evidence/semantic-source-pins.json': '4B3165E637A56A7FF2C0F06F78281D1FDF033A85CB36F8A360B8B8F8134890F1',
}


def read(path):
    return json.loads((ROOT / path).read_bytes())


def payload(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8')


def digest(data):
    return hashlib.sha256(data).hexdigest().upper()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def envelope(kind, **fields):
    return {'schema': {'name': 'fable2-prototype-trust-' + kind, 'version': 1},
            'generator': {'name': 'Fable2PrototypeTrust.py', 'version': '0.1.0'},
            'phase2b_commit': BASE, 'canonical_adoption': False, **fields}


def output(path):
    resolved = (ROOT / path).resolve()
    require(resolved.is_relative_to(ROOT.resolve()), 'output escapes repository through a link')
    require(any(resolved.is_relative_to((ROOT / root).resolve()) for root in (DOC, OUT)), 'output outside Phase 2C roots')
    return resolved


def write(path, value, check=False):
    data = value if isinstance(value, bytes) else payload(value)
    target = output(path)
    if check:
        require(target.is_file() and target.read_bytes() == data, f'determinism mismatch: {path}')
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return {'path': Path(path).as_posix(), 'size': len(data), 'sha256': digest(data)}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode().strip()


def audit_paths():
    require(git('branch', '--show-current') == BRANCH, 'wrong Phase 2C branch')
    require(git('rev-parse', BASE + '^{tree}') == TREE, 'closed Phase 2B tree mismatch')
    git('merge-base', '--is-ancestor', BASE, 'HEAD')
    allowed = {'tools/Fable2PrototypeTrust.py', 'tests/test_fable2_prototype_trust.py',
               'tools/schemas/fable2-prototype-trust-v1.schema.json', 'tools/Verify-Fable2PrototypeTrust.ps1', '.gitattributes',
               'tools/Fable2PrototypeCompletion.py', 'tests/test_fable2_prototype_completion.py',
               'tools/schemas/fable2-prototype-completion-v1.schema.json'}
    expected_attributes = git('show', BASE + ':.gitattributes').splitlines() + [
        '', '# Phase 2C hashes only its own implementation and evidence bytes.',
        '/docs/fable2-prototype-archaeology/phase2c/** text eol=lf',
        '/tools/Fable2PrototypeTrust.py text eol=lf',
        '/tools/Verify-Fable2PrototypeTrust.ps1 text eol=lf',
        '/tools/schemas/fable2-prototype-trust-v1.schema.json text eol=lf',
        '/tests/test_fable2_prototype_trust.py text eol=lf',
        '/tools/Fable2PrototypeCompletion.py text eol=lf',
        '/tests/test_fable2_prototype_completion.py text eol=lf',
        '/tools/schemas/fable2-prototype-completion-v1.schema.json text eol=lf']
    require((ROOT / '.gitattributes').read_text().splitlines() == expected_attributes,
            'attributes delta extends beyond exact Phase 2C LF rules')
    paths = set(git('diff', '--name-only', BASE).splitlines())
    paths.update(git('ls-files', '--others', '--exclude-standard').splitlines())
    require(all(p in allowed or (p.startswith(DOC.as_posix() + '/') and Path(p).suffix in ('.md','.json')) for p in paths),
            f'forbidden changed paths: {sorted(paths - allowed)}')
    prior = read(semantic.PIN_FILE)
    require(semantic.sdk_state() == prior['sdk_start'], 'SDK preservation mismatch')
    require(git('remote', '-v').splitlines() == prior['fable_start']['remotes'], 'Fable remotes changed')


def binding():
    audit_paths()
    for path, expected in HASHES.items():
        require(old.sha256_file(ROOT / path) == expected, f'closed hash mismatch: {path}')
    prior = read(semantic.PIN_FILE)
    require(prior['python_runtime'] == {'implementation': platform.python_implementation(), 'version': platform.python_version()}, 'Python runtime mismatch')
    sources = list(prior['sources'])
    extra = set(HASHES)
    for root in ('docs/fable2-prototype-archaeology/phase1', 'docs/fable2-prototype-archaeology/phase2a', 'docs/fable2-prototype-archaeology/phase2b'):
        extra.update(p.relative_to(ROOT).as_posix() for p in (ROOT / root).rglob('*') if p.is_file())
    validation = read('docs/fable2-prototype-archaeology/phase2b/evidence/semantic-validation.json')
    for item in validation['artifacts'] + validation['implementation']:
        path = ROOT / item['path']
        require(path.stat().st_size == item['size'] and old.sha256_file(path) == item['sha256'], f'closed Phase 2B identity mismatch: {item["path"]}')
        extra.add(item['path'])
    extra.update(('AGENTS.md', 'out/tools/ppc-disasm.exe', 'tools/Fable2PrototypeArchaeology.py',
                  'tools/VerifyFable2PrototypePhase1Consistency.py', 'tests/test_fable2_prototype_correspondence.py',
                  'tests/test_fable2_prototype_phase2a_consistency.py'))
    keys = {(r['root'], r['path']) for r in sources}
    for path in sorted(extra):
        if ('repository', path) not in keys:
            sources.append(semantic.identity(Path(path)))
    for row in sources:
        root = ROOT if row['root'] == 'repository' else semantic.CORPUS
        path = root / row['path']
        require(path.is_file() and path.stat().st_size == row['size'] and old.sha256_file(path) == row['sha256'], f'bound input mismatch: {row["root"]}/{row["path"]}')
    return envelope('source-pins', sources=sorted(sources, key=lambda r: (r['root'], r['path'])),
                    fable_start={'branch': 'fable2-prototype-archaeology-phase2b', 'head': BASE, 'tree': TREE,
                                 'remotes': prior['fable_start']['remotes'], 'index': [], 'status': []},
                    sdk_start=prior['sdk_start'], phase2a_input_bundle_sha256=semantic.BUNDLE,
                    python_runtime=prior['python_runtime'])


def load_inputs():
    pins = binding()
    require(read(PINS) == pins, 'Phase 2C source binding changed')
    images = {build: native.Image(build, old.load_build(ROOT / semantic.DERIVED, build)[1])
              for build in (PRIMARY, TARGET, 'sep-2008')}
    features = read(semantic.consistency.ARTIFACTS['exhaustive_function_features'])['builds']
    pairs = read(semantic.P2 / 'prototype-correspondence-accepted.json')['records']
    return pins, images, features, pairs


def object_at(image, address, limit=4096, allow_empty=False):
    """Bounded terminated text, explicit interior relation; otherwise a window.

    This proves encoded byte boundaries, not language-level object allocation.
    No binary structure is assigned an invented length.
    """
    block = image.block(address)
    require(block is not None, 'reference outside initialized sections')
    offset = address - block.start
    window = block.data[offset:offset + 16]
    result = {'address': native.hx(address), 'section': block.name, 'alignment_mod4': address % 4,
              'window_size': len(window), 'window_sha256': digest(window),
              'kind': 'bounded-byte-window', 'boundary_proven': False}
    data = block.data
    if data[offset] == 0 and allow_empty:
        # A pointer at a terminator denotes an empty byte string, but is not
        # proof of a separately allocated object or of UTF-16 encoding.
        result.update(kind='terminated-string', boundary_proven=True, encoding='ascii',
                      start=native.hx(address), end_exclusive=native.hx(address + 1),
                      pointer_relation='empty-at-terminator', pointer_byte_offset=0,
                      length_bytes=0, terminator_bytes=1, full_sha256=digest(b'\0'),
                      full_text='', referenced_sha256=digest(b'\0'), referenced_length_bytes=0)
        return result
    if data[offset] == 0:
        return result
    for encoding, width in (('utf-16le', 2), ('ascii', 1)):
        if width == 2 and (address % 2 or offset + 3 >= len(data) or not (32 <= data[offset] <= 126 and data[offset + 1] == 0 and 32 <= data[offset + 2] <= 126 and data[offset + 3] == 0)):
            continue
        def printable(pos):
            return 0 <= pos <= len(data) - width and 32 <= data[pos] <= 126 and (width == 1 or data[pos + 1] == 0)
        begin = offset
        while begin >= width and offset - begin < limit and printable(begin - width):
            begin -= width
        end = offset
        while end < len(data) and end - begin < limit and printable(end):
            end += width
        terminated = data[end:end + width] == b'\0' * width
        # Empty references are explicit. A preceding NUL is required to infer
        # a string start instead of an unbounded suffix of unknown storage.
        start_known = begin == 0 or data[begin - width:begin] == b'\0' * width
        if terminated and start_known and end - begin < limit:
            full = data[begin:end + width]
            result.update(kind='terminated-string', boundary_proven=True, encoding=encoding,
                          start=native.hx(block.start + begin), end_exclusive=native.hx(block.start + end + width),
                          pointer_relation='start' if begin == offset else 'interior-suffix',
                          pointer_byte_offset=offset - begin, length_bytes=end - begin, terminator_bytes=width,
                          full_sha256=digest(full), full_text=data[begin:end].decode(encoding),
                          referenced_sha256=digest(data[offset:end + width]), referenced_length_bytes=end - offset)
            return result
    return result


def identity_token(obj):
    if obj['kind'] != 'terminated-string' or not obj['boundary_proven']:
        return None
    return (obj['encoding'], obj['length_bytes'], obj['terminator_bytes'], obj['full_sha256'],
            obj['pointer_relation'], obj['pointer_byte_offset'])


def trust_disposition(raw, independent, full_support, conflicts, partial):
    if conflicts:
        return 'suppressed-semantic-collision'
    if raw or independent:
        return 'retained-independent-evidence'
    if full_support:
        return 'retained-full-object-corroborated'
    return 'review-required-partial-anchor' if partial else 'review-required-independent-evidence'


def role_key(ref):
    return (int(ref['instruction'], 16) - int(ref['function']['start'], 16), ref['role'], ref['operand'], ref['width'])


def function_refs(image, function):
    code = image.read(function['start'], function['end'] - function['start'])
    words = [w[0] for w in struct.iter_unpack('>I', code)]
    addresses = {a for _, a in old.materialized_addresses(words) if image.block(a) and not image.block(a).execute}
    result = native.scan_function(image, function, addresses)[0]
    # A loop's first fallthrough traversal can consume an initialized pointer
    # that cannot remain constant across its backedge. Recover that bounded
    # prefix separately and label it; never propagate a constant around a loop.
    if len(code) <= 256:
        for index, word in enumerate(words):
            if word >> 26 not in (32, 34, 40, 42):
                continue
            pc = function['start'] + index * 4
            has_later_backedge = any(w >> 26 in (16, 18) and not w & 1 and native.branch(w, function['start'] + j * 4) == pc
                                    for j, w in enumerate(words[index + 1:], index + 1))
            # The pointer load may be the second instruction of the loop.
            has_later_backedge |= any(w >> 26 in (16, 18) and not w & 1 and native.branch(w, function['start'] + j * 4) == pc - 4
                                     for j, w in enumerate(words[index + 1:], index + 1))
            if has_later_backedge:
                prefix = native.scan_function(image, function, addresses, prefix_end=pc + 4)[0]
                for ref in prefix:
                    if ref['instruction'] == native.hx(pc):
                        ref['first_entry_prefix_end'] = native.hx(pc + 4)
                        result.append(ref)
    return result


def audit_pairs(images, features, pairs):
    left, right = images[PRIMARY], images[TARGET]
    by_start = {b: {r['start']: r for r in rows} for b, rows in features.items()}
    records = []
    for index, pair in enumerate(pairs):
        d = left.by_start[int(pair['donor_start'], 16)]
        t = right.by_start[int(pair['target_start'], 16)]
        require(native.hx(d['end']) == pair['donor_end_exclusive'] and native.hx(t['end']) == pair['target_end_exclusive'], 'closed boundary mismatch')
        df, tf = by_start[PRIMARY][pair['donor_start']], by_start[TARGET][pair['target_start']]
        raw = left.read(d['start'], pair['size']) == right.read(t['start'], pair['size'])
        require(raw == pair['evidence']['fingerprints']['raw']['equal'], 'raw-byte evidence mismatch')
        classes = pair['evidence']['corroborating_feature_classes']
        independent = bool(set(classes) & {'local-address-delta-neighbourhood', 'direct-call-topology'})
        shared = sorted(set(df['references']['data_anchors']) & set(tf['references']['data_anchors']))
        require(len(shared) == pair['evidence']['references']['shared_data_anchor_count'], 'data anchor count mismatch')
        anchors = []
        for anchor in shared:
            section, address_text, expected = anchor.split(':')
            address = int(address_text, 16)
            a, b = object_at(left, address), object_at(right, address)
            require(a['section'] == b['section'] == section and a['window_sha256'] == b['window_sha256'] == expected, 'data anchor bytes mismatch')
            ta, tb = identity_token(a), identity_token(b)
            classification = 'non-string-bounded-window'
            if ta is not None and tb is not None:
                classification = 'full-string-match' if ta == tb else 'same-address-different-full-string'
            anchors.append({'original_anchor': anchor, 'donor': a, 'target': b, 'classification': classification,
                            'prefix_only': ta is not None and tb is not None and ta != tb,
                            'independently_authorizes_transport': False})
        drefs, trefs = function_refs(left, d), function_refs(right, t)
        targets = collections.defaultdict(list)
        for ref in trefs:
            targets[role_key(ref)].append(ref)
        comparisons, conflicts = [], []
        for ref in drefs:
            a = object_at(left, int(ref['anchor_address'], 16))
            for other in targets[role_key(ref)]:
                b = object_at(right, int(other['anchor_address'], 16))
                ta, tb = identity_token(a), identity_token(b)
                conflict = ta is not None and tb is not None and ta != tb
                item = {'donor_reference': ref, 'target_reference': other, 'donor_object': a, 'target_object': b,
                        'full_identity_equal': ta is not None and ta == tb, 'semantic_conflict': conflict}
                comparisons.append(item)
                if conflict:
                    conflicts.append(len(comparisons) - 1)
        full_support = any(r['full_identity_equal'] for r in comparisons)
        disposition = trust_disposition(raw, independent, full_support, conflicts, bool(shared))
        records.append({'id': f'T-{index:05d}', 'original_record_index': index,
                        'original_record_sha256': digest(payload(pair)), 'donor_start': pair['donor_start'],
                        'target_start': pair['target_start'], 'original_status': pair['status'],
                        'feature_classes': classes, 'raw_equal': raw, 'size': pair['size'],
                        'risk_flags': sorted(set(df['risk_flags'] + tf['risk_flags'])),
                        'one_call_wrapper_shape': pair['size'] <= 128 and len(df['direct_calls']) == 1,
                        'independent_without_data': raw or independent,
                        'data_only_non_cfg': set(classes) <= {'cfg-and-branch-shape', 'data-content-anchor'} and bool(shared),
                        'counterfactual_without_data': raw or independent or full_support,
                        'anchors': anchors, 'reference_comparisons': comparisons, 'conflicts': conflicts,
                        'disposition': disposition, 'code_lineage_disproven': False, 'canonical_adoption': False})
    return records


def audit_counts(rows):
    return {'audited': len(rows), 'original_status': dict(sorted(collections.Counter(r['original_status'] for r in rows).items())),
            'dispositions': dict(sorted(collections.Counter(r['disposition'] for r in rows).items())),
            'data_anchor_supported_pairs': sum(bool(r['anchors']) for r in rows),
            'data_only_non_cfg': sum(r['data_only_non_cfg'] for r in rows),
            'counterfactually_dependent_on_partial_data': sum(bool(r['anchors']) and not r['counterfactual_without_data'] for r in rows),
            'anchor_classifications': dict(sorted(collections.Counter(a['classification'] for r in rows for a in r['anchors']).items())),
            'data_pairs_retained_independently': sum(bool(r['anchors']) and r['independent_without_data'] for r in rows),
            'interior_pointer_anchor_pairs': sum(any(a['donor'].get('pointer_relation') == 'interior-suffix' or a['target'].get('pointer_relation') == 'interior-suffix' for a in r['anchors']) for r in rows)}


def code_region(image, start, maximum=256):
    """Reachable non-call instructions; no independent function is invented."""
    todo, seen, edges = [start], {}, []
    owner = image.owner(start)
    blocked = []
    while todo and len(seen) < maximum:
        pc = todo.pop()
        if pc in seen:
            continue
        block = image.block(pc, 4)
        if block is None or not block.execute or pc % 4:
            blocked.append({'address': native.hx(pc), 'reason': 'not-executable-aligned'})
            continue
        if pc != start and pc in image.by_start:
            blocked.append({'address': native.hx(pc), 'reason': 'different-pdata-entry'})
            continue
        if abs(pc - start) > maximum * 4:
            blocked.append({'address': native.hx(pc), 'reason': 'region-distance-bound'})
            continue
        word = int.from_bytes(image.read(pc, 4), 'big')
        seen[pc] = word
        op, xo = word >> 26, (word >> 1) & 1023
        targets = []
        if op in (16, 18) and not word & 1:
            targets.append(native.branch(word, pc))
            if op == 16:
                targets.append(pc + 4)
        elif word == 0x4E800020:
            pass
        elif op == 19 and xo in (16, 528):
            blocked.append({'address': native.hx(pc), 'reason': 'unresolved-indirect-transfer'})
        else:
            targets.append(pc + 4)
        for target in sorted(targets):
            edges.append([pc - start, target - start])
            if target not in seen:
                todo.append(target)
    if todo:
        blocked.append({'address': native.hx(start), 'reason': 'instruction-limit'})
    content = [[pc - start, word] for pc, word in sorted(seen.items())]
    return {'kind': 'pdata-function-region' if start in image.by_start else 'internal-code-region',
            'build': image.build, 'start': native.hx(start),
            'end_exclusive': native.hx(max(seen) + 4) if seen else None,
            'containing_owner': native.boundary(owner) if owner else None,
            'independent_pdata_entry': start in image.by_start,
            'instruction_count': len(seen), 'reachable_instruction_sha256': digest(payload(content)),
            'reachable_byte_sha256': digest(b''.join(struct.pack('>I', word) for _, word in sorted(seen.items()))),
            'edges': sorted(edges), 'blockers': blocked, 'canonical_adoption': False}


def canonicalize(image, function, refs):
    start, end = function['start'], function['end']
    original = [w[0] for w in struct.iter_unpack('>I', image.read(start, end - start))]
    words = [old.normalize_branch_word(w) for w in original]
    tokens, changes, rejected = [], {}, []
    for ref in sorted(refs, key=lambda r: (role_key(r), r['anchor_address'])):
        obj = object_at(image, int(ref['anchor_address'], 16), allow_empty=ref['role'] == 'memory-read' and ref['width'] == 1)
        token = identity_token(obj)
        chain = [int(pc, 16) for pc in ref['definition_instructions']]
        if token is None or ref['readonly_pointer_slots'] or len(chain) != 2:
            rejected.append({'reference': ref, 'reason': 'not-a-direct-two-instruction-complete-string-reference'})
            continue
        if not all(start <= pc < end and pc % 4 == 0 for pc in chain):
            raise ValueError('definition outside owning function')
        hi, lo = [original[(pc - start) // 4] for pc in chain]
        register = (hi >> 21) & 31
        valid = hi >> 26 == 15 and ((hi >> 16) & 31) == 0
        valid &= (lo >> 26 == 14 and ((lo >> 16) & 31) == register) or (lo >> 26 == 24 and ((lo >> 21) & 31) == register)
        if not valid:
            rejected.append({'reference': ref, 'reason': 'unsupported-definition-form'})
            continue
        tokens.append({'role': list(role_key(ref)), 'identity': list(token), 'section': obj['section'],
                       'definition_offsets': [pc - start for pc in chain]})
        for pc in chain:
            index = (pc - start) // 4
            words[index] = words[index] & 0xFFFF0000
            changes[pc - start] = {'offset': pc - start, 'preserved_mask': '0xFFFF0000',
                                   'original_instruction_sha256': digest(struct.pack('>I', original[index]))}
    canonical = {'words': words, 'tokens': tokens}
    return {'fingerprint': digest(payload(canonical)), 'canonicalized_references': tokens,
            'changed_instructions': [changes[k] for k in sorted(changes)], 'rejected_references': rejected}


def independent_support(donor, target, features, seeds, callers):
    support, conflicts, unproved_calls = [], [], []
    dcalls = {c['instruction_offset']: c['target'] for c in donor['direct_calls']}
    tcalls = {c['instruction_offset']: c['target'] for c in target['direct_calls']}
    for offset, dcallee in sorted(dcalls.items()):
        tcallee = tcalls.get(offset)
        if dcallee in seeds:
            if seeds[dcallee] == tcallee:
                support.append({'class': 'trusted-mapped-callee', 'donor': dcallee, 'target': tcallee, 'offset': offset})
            else:
                conflicts.append({'class': 'trusted-callee-conflict', 'donor': dcallee, 'target': tcallee, 'offset': offset})
        else:
            unproved_calls.append({'donor': dcallee, 'target': tcallee, 'offset': offset})
    for caller, offset in callers.get(donor['start'], []):
        if caller not in seeds:
            continue
        target_caller = features[TARGET][seeds[caller]]
        matching = any(c['instruction_offset'] == offset and c['target'] == target['start'] for c in target_caller['direct_calls'])
        if matching:
            support.append({'class': 'trusted-mapped-caller', 'donor': caller, 'target': target_caller['start'], 'offset': offset})
    return support, conflicts, unproved_calls


def candidate_stage(images, feature_rows, audit, pairs):
    reviews = read(semantic.OUT / 'semantic-mapping-review.json')['records']
    require(len(reviews) == 21350, 'mapping-review population drift')
    populations = {r['donor_function']['start'] for r in reviews}
    # All target .pdata functions participate in reciprocal uniqueness, including
    # functions with empty references absent from Phase 2B's curated inventory.
    populations.update(r['donor_start'] for r in pairs)
    features = {b: {r['start']: r for r in rows} for b, rows in feature_rows.items()}
    exact_callers = {r['donor_start'] for r in pairs if r['status'] == 'accepted-exact-unique'}
    for start in sorted(exact_callers):
        populations.update(c['target'] for c in features[PRIMARY][start]['direct_calls'] if c['target'] in features[PRIMARY])
    refs = read(semantic.OUT / 'semantic-xrefs.json')['references']
    indexed = collections.defaultdict(list)
    for ref in refs:
        indexed[(ref['build'], ref['function']['start'])].append(ref)
    fingerprints, analyses = {}, {}
    for build in (PRIMARY, TARGET):
        groups = collections.defaultdict(list)
        analyses[build] = {}
        for f in images[build].functions:
            start = native.hx(f['start'])
            # Existing references are reused; a bounded per-function extension
            # supplies short/empty literals excluded by the Phase 2B inventory.
            existing = indexed[(build, start)]
            extra = function_refs(images[build], f)
            unique = {(r['instruction'], r['role'], r['operand'], r['anchor_address']): r for r in extra + existing}
            result = canonicalize(images[build], f, list(unique.values()))
            analyses[build][start] = result
            if result['canonicalized_references']:
                groups[result['fingerprint']].append(start)
        fingerprints[build] = groups
        print(f'Canonicalized {build}: {len(analyses[build])} functions', flush=True)
    seeds = {r['donor_start']: r['target_start'] for r in audit if r['disposition'].startswith('retained-')}
    seed_reverse = {t: d for d, t in seeds.items()}
    callers = collections.defaultdict(list)
    for row in feature_rows[PRIMARY]:
        for call in row['direct_calls']:
            callers[call['target']].append((row['start'], call['instruction_offset']))
    candidates = {}
    ordered_donors = sorted(features[PRIMARY])
    for start in sorted(populations):
        sig = analyses[PRIMARY][start]
        viable = fingerprints[TARGET].get(sig['fingerprint'], []) if sig['canonicalized_references'] else []
        rows = []
        for target in viable:
            d, t = features[PRIMARY][start], features[TARGET][target]
            support, conflicts, unproved = independent_support(d, t, features, seeds, callers)
            position = bisect.bisect_left(ordered_donors,start)
            neighbours = []
            for adjacent in ordered_donors[max(0,position-8):position+9]:
                if adjacent == start or adjacent not in seeds:
                    continue
                delta = int(start,16) - int(adjacent,16)
                if int(seeds[adjacent],16) + delta == int(target,16):
                    neighbours.append({'donor':adjacent,'target':seeds[adjacent],'relative_delta':delta})
            if any(n['relative_delta'] < 0 for n in neighbours) and any(n['relative_delta'] > 0 for n in neighbours):
                support.append({'class':'trusted-two-sided-exact-delta-neighbourhood','anchors':neighbours})
            if target in seed_reverse and seed_reverse[target] != start:
                conflicts.append({'class': 'retained-target-already-owned', 'donor': seed_reverse[target], 'target': target})
            if start in seeds and seeds[start] != target:
                conflicts.append({'class': 'retained-donor-already-mapped', 'donor': start, 'target': seeds[start]})
            reciprocal = len(fingerprints[PRIMARY][sig['fingerprint']]) == len(viable) == 1
            boundary = d['size'] == t['size'] and not (d['boundary_flags'] or t['boundary_flags'])
            shape = d['shape'] == t['shape']
            region_support = []
            for call in unproved:
                if call['target'] is None:
                    continue
                da, ta = int(call['donor'], 16), int(call['target'], 16)
                if da not in images[PRIMARY].by_start and ta not in images[TARGET].by_start:
                    a, b = code_region(images[PRIMARY], da), code_region(images[TARGET], ta)
                    if not a['blockers'] and not b['blockers'] and a['reachable_instruction_sha256'] == b['reachable_instruction_sha256']:
                        region_support.append({'call': call, 'donor_region': a, 'target_region': b})
            remaining = [c for c in unproved if not any(r['call'] == c for r in region_support)]
            tail_transfers = []
            for build, feature in ((PRIMARY,d),(TARGET,t)):
                entry = int(feature['start'],16)
                end = int(feature['end_exclusive'],16)
                words = struct.iter_unpack('>I', images[build].read(entry,end-entry))
                for i,(word,) in enumerate(words):
                    destination = native.branch(word,entry + i*4)
                    if word >> 26 in (16,18) and not word & 1 and destination is not None and not entry <= destination < end:
                        tail_transfers.append({'build':build,'offset':i*4,'destination':native.hx(destination)})
            grade = 'candidate'
            if conflicts or not boundary or not shape:
                grade = 'rejected-proposal'
            elif not reciprocal:
                grade = 'ambiguous'
            elif support and not remaining and not tail_transfers:
                grade = 'reviewed-strong-proposal'
            elif support or region_support:
                grade = 'reviewed-probable-proposal'
            rows.append({'donor_start': start, 'target_start': target, 'grade': grade,
                         'reciprocal_unique': reciprocal, 'boundary_valid': boundary, 'shape_equal': shape,
                         'canonicalized_reference_evidence': sig, 'independent_support': support,
                         'internal_region_support': region_support, 'unproved_calls': remaining,
                         'unproved_external_tail_transfers':tail_transfers,
                         'contradictions': conflicts, 'generation': 1, 'human_review_state': 'not-human-reviewed',
                         'canonical_adoption': False})
        candidates[start] = rows
    # Fixed-point expansion uses a snapshot of the preceding generation only.
    # New mappings cannot validate each other during the generation that creates
    # them, and every prerequisite is retained as an explicit dependency.
    for generation in range(2,4):
        available = dict(seeds)
        generations = {d:0 for d in seeds}
        for rs in candidates.values():
            for proposal in rs:
                if proposal['grade'] == 'reviewed-strong-proposal' and proposal['generation'] < generation:
                    available[proposal['donor_start']] = proposal['target_start']
                    generations.setdefault(proposal['donor_start'],proposal['generation'])
        pending = []
        for start, rs in sorted(candidates.items()):
            if len(rs) != 1:
                continue
            row = rs[0]
            if row['grade'] not in ('candidate','reviewed-probable-proposal') or row['unproved_external_tail_transfers']:
                continue
            support, conflicts, unproved = independent_support(features[PRIMARY][start], features[TARGET][row['target_start']], features, available, callers)
            unproved = [c for c in unproved if not any(s['call'] == c for s in row['internal_region_support'])]
            if conflicts or unproved or not support:
                continue
            dependencies = [{'donor':s['donor'],'target':s['target'],'generation':generations[s['donor']]} for s in support]
            require(all(d['generation'] < generation for d in dependencies), 'same-generation circular dependency')
            pending.append((row,support,dependencies))
        if not pending:
            break
        for row,support,dependencies in pending:
            row.update(grade='reviewed-strong-proposal',generation=generation,
                       independent_support=support, proposal_dependencies=dependencies, unproved_calls=[])
    terminal = []
    for original in reviews:
        rows = candidates[original['donor_function']['start']]
        terminal.append({'original_mapping_review_id': original['id'], 'association_id': original['association_id'],
                         'donor_start': original['donor_function']['start'], 'candidates': rows,
                         'candidate_count': len(rows), 'result': 'no-candidate' if not rows else 'one-candidate' if len(rows) == 1 else 'multiple-candidates'})
    require(len({r['original_mapping_review_id'] for r in terminal}) == len(reviews), 'duplicate mapping-review terminal')
    proposals = [r for start in sorted(candidates) for r in candidates[start] if seeds.get(start) != r['target_start']]
    return envelope('candidates', records=terminal, proposals=proposals,
                    fixed_point_generation_bound=3, same_generation_support_permitted=False,
                    counts={'processed_contexts': len(terminal), 'processed_donor_functions': len(populations),
                            'reciprocal_donor_population': len(analyses[PRIMARY]), 'reciprocal_target_population': len(analyses[TARGET]),
                            'results': dict(sorted(collections.Counter(r['result'] for r in terminal).items())),
                            'proposal_grades': dict(sorted(collections.Counter(r['grade'] for r in proposals).items()))})


def secondary_stage():
    # Closed generator is called as a library. Its generate/write entry points
    # are never called; this is a new Phase 2C materialization and provenance.
    left = old.analyze_build(ROOT / semantic.DERIVED, 'sep-2008')
    right = old.analyze_build(ROOT / semantic.DERIVED, PRIMARY)
    result = old.match_builds(left, right, include_index=True, include_exhaustive=True)
    expected = read(semantic.P2 / 'prototype-correspondence-validation.json')['september_robustness_study']
    actual = old.secondary_study(result, len(left.functions), len(right.functions))
    require(actual == expected, 'September original-policy aggregate mismatch')
    trust = audit_pairs({PRIMARY: native.Image('sep-2008', left.blocks), TARGET: native.Image(PRIMARY, right.blocks)},
                        {PRIMARY: old.exhaustive_function_features(left), TARGET: old.exhaustive_function_features(right)},
                        result['accepted'])
    return envelope('september', original_policy='precision-first-v1', original_aggregate=actual,
                    original_pairs=result['accepted'], original_terminals=result['index'],
                    original_candidates=result['exhaustive_groups'],
                    trust_dispositions=trust, trust_counts=audit_counts(trust),
                    trust_dispositions_complete=True, canonical_routing_enabled=False)


def effective_view(pairs, audit, proposals):
    require(len(pairs) == len(audit), 'audit does not cover closed pairs')
    suppressions = [r for r in audit if not r['disposition'].startswith('retained-')]
    suppressed = {r['original_record_index'] for r in suppressions}
    rows = [{'donor_start': p['donor_start'], 'target_start': p['target_start'],
             'original_record_index': i, 'original_record_sha256': digest(payload(p)),
             'source': 'closed-phase2a-retained', 'generation': 0}
            for i, p in enumerate(pairs) if i not in suppressed]
    additions = [p for p in proposals if p['grade'] == 'reviewed-strong-proposal']
    trusted = {r['donor_start']:(r['target_start'],0) for r in rows}
    for generation in range(1,4):
        batch = [p for p in additions if p['generation'] == generation]
        for p in batch:
            require(p['reciprocal_unique'] and p['boundary_valid'] and p['shape_equal'], 'proposal lacks structural gates')
            require(bool(p['canonicalized_reference_evidence']['canonicalized_references']), 'proposal lacks canonicalized reference evidence')
            require(not (p['contradictions'] or p['unproved_calls'] or p['unproved_external_tail_transfers']), 'proposal has unresolved behavior')
            require(bool(p['independent_support']), 'canonical string evidence double-counted as independent support')
            for support in p['independent_support']:
                if support['class'] == 'trusted-two-sided-exact-delta-neighbourhood':
                    dependencies = support['anchors']
                else:
                    require(support['class'] in ('trusted-mapped-callee','trusted-mapped-caller'), 'unsupported independent class')
                    dependencies = [support]
                for dep in dependencies:
                    require(dep['donor'] in trusted and trusted[dep['donor']][0] == dep['target'] and trusted[dep['donor']][1] < generation,
                            'dangling or circular same-generation support')
        for p in batch:
            trusted[p['donor_start']] = (p['target_start'],generation)
    rows.extend({'donor_start': p['donor_start'], 'target_start': p['target_start'],
                 'source': 'phase2c-proposal', 'generation': p['generation'],
                 'proposal_sha256': digest(payload(p))} for p in additions)
    require(len({r['donor_start'] for r in rows}) == len(rows), 'duplicate effective donor')
    require(len({r['target_start'] for r in rows}) == len(rows), 'duplicate effective target')
    return envelope('effective-map', records=sorted(rows, key=lambda r: r['donor_start']),
                    suppressions=suppressions, additions=additions,
                    counts={'closed': len(pairs), 'suppressed_or_review_excluded': len(suppressions),
                            'additions': len(additions), 'effective': len(rows), 'delta': len(rows) - len(pairs)},
                    canonical_consumer_enabled=False)


def disassemble(image, start, end):
    block = image.block(start, end - start)
    require(block is not None and block.execute, 'disassembly outside executable bounds')
    path = ROOT / semantic.DERIVED / image.build / block.relative_path
    return subprocess.check_output([str(ROOT / 'out/tools/ppc-disasm.exe'), str(path), native.hx(block.start),
                                    native.hx(start), native.hx(end)], cwd=ROOT).decode().splitlines()


def known_cases(images, pairs, candidates):
    requests = [(PRIMARY, 0x82631A30), (TARGET, 0x82630C30), (PRIMARY, 0x829506B0), (TARGET, 0x82950A98),
                (PRIMARY, 0x8222D118), (TARGET, 0x8222CED0), (PRIMARY, 0x8229B308), (TARGET, 0x8229B038),
                (PRIMARY, 0x8229B488), (TARGET, 0x8229B1B8)]
    records = []
    for build, start in requests:
        image = images[build]
        f = image.by_start.get(start)
        require(f is not None, f'known-case address lacks .pdata entry: {build}/{native.hx(start)}')
        refs = function_refs(image, f)
        records.append({'build': build, 'boundary': native.boundary(f),
                        'body_sha256': digest(image.read(start, f['end'] - start)),
                        'disassembly': disassemble(image, start, f['end']),
                        'references': refs,
                        'objects': [object_at(image, int(r['anchor_address'], 16), allow_empty=r['role'] == 'memory-read' and r['width'] == 1) for r in refs],
                        'closed_pairs': [p for p in pairs if p['donor_start' if build == PRIMARY else 'target_start'] == native.hx(start)],
                        'proposals': [p for p in candidates['proposals'] if p['donor_start' if build == PRIMARY else 'target_start'] == native.hx(start)]})
    regions = [code_region(images[b], s) for b, s in ((PRIMARY, 0x8226DB80), (TARGET, 0x8226D7F8))]
    for region in regions:
        region['disassembly'] = disassemble(images[region['build']], int(region['start'], 16), int(region['end_exclusive'], 16))
    require(all(not r['independent_pdata_entry'] and not r['blockers'] and r['instruction_count'] == 21 for r in regions), 'comparator boundary/reachability evidence differs')
    require(regions[0]['reachable_byte_sha256'] == regions[1]['reachable_byte_sha256'], 'comparator reachable bytes differ')
    return envelope('known-cases', functions=records, comparator_regions=regions,
                    semantic_role='Caller/callee exclusion guard involving HammerCombat; no function name assigned.',
                    comparator_role='Signed-byte lexical comparison with returns -1, 0, 1; internal code regions without .pdata ownership.')


def boundary_stage(images, candidates, september, known):
    original = read(semantic.P2 / 'prototype-correspondence-index.json')['functions']
    unmatched = [r for r in original if r['status'] == 'unmatched']
    require(len(unmatched) == 2, 'unmatched donor population drift')
    anchors = {r['id']: r for r in read(semantic.OUT / 'semantic-inventory.json')['anchors']}
    contexts = {r['id']: r for r in read(semantic.OUT / 'semantic-index.json')['records']}
    population = {r['donor_start']: {'prior_status': 'unmatched', 'full_windows': True} for r in unmatched}
    for row in candidates['records']:
        context = contexts[row['association_id']]
        if row['result'] == 'no-candidate' and not anchors[context['anchor_id']]['filters']:
            population.setdefault(row['donor_start'], {'prior_status': 'high-value-no-reference-candidate', 'full_windows': False})
    target_block = next(b for b in images[TARGET].blocks if b.name == '.text')
    donor_block = next(b for b in images[PRIMARY].blocks if b.name == '.text')
    records = []
    for start, reason in sorted(population.items()):
        f = images[PRIMARY].by_start[int(start, 16)]
        size = f['end'] - f['start']
        offsets = range(0, size - 31, 32) if reason['full_windows'] else sorted({0, max(0, (size - 32) // 4 * 4)})
        windows = []
        for offset in offsets:
            if size < 32:
                continue
            data = images[PRIMARY].read(f['start'] + offset, 32)
            first = target_block.data.find(data)
            donor_first = donor_block.data.find(data)
            unique = first >= 0 and target_block.data.find(data, first + 1) < 0 and donor_block.data.find(data, donor_first + 1) < 0
            owner = images[TARGET].owner(target_block.start + first) if first >= 0 else None
            windows.append({'donor_start': native.hx(f['start'] + offset), 'size': 32, 'sha256': digest(data),
                            'reciprocal_unique_exact_window': unique,
                            'target_start': native.hx(target_block.start + first) if unique and first % 4 == 0 else None,
                            'target_owner': native.boundary(owner) if unique and owner else None})
        records.append({'donor': native.boundary(f), 'population': reason['prior_status'],
                        'relation': 'shared-body' if any(w['target_start'] for w in windows) else 'unresolved-boundary',
                        'grade': 'candidate', 'windows': windows, 'semantic_transport_permitted': False,
                        'limitation': 'Exact 32-byte instruction windows do not establish a split, merge, inline, outline, or complete function correspondence.'})
    prior = [{'original_terminal_index': i, 'record': r, 'relation': 'unresolved-boundary', 'semantic_transport_permitted': False}
             for i, r in enumerate(september['original_terminals']) if r['status'] == 'boundary-change']
    return envelope('boundaries', records=records, september_boundary_review=prior,
                    internal_code_regions=known['comparator_regions'],
                    classes={kind: sum(r['relation'] == kind for r in records) for kind in ('split','merge','outline','inline','thunk','tail','shared-body','unresolved-boundary')},
                    limitations=['No compiler-transformation lineage inferred from shared windows.',
                                 'September boundary rows retain original-policy evidence and remain unresolved.',
                                 'This bounded window pass does not resolve all changed-boundary relationships.'])


def freeze_stage(images, pairs, check=False):
    audit = read(OUT / 'trust-audit.json')
    candidates = read(OUT / 'reference-candidates.json')
    september = read(OUT / 'september-pairs.json')
    require(candidates['audit_sha256'] == old.sha256_file(ROOT / OUT / 'trust-audit.json'), 'candidate audit binding mismatch')
    effective = effective_view(pairs, audit['records'], candidates['proposals'])
    known = known_cases(images, pairs, candidates)
    boundary = boundary_stage(images, candidates, september, known)
    for name, doc in (('effective-map', effective), ('known-cases', known), ('boundaries', boundary)):
        write(OUT / (name + '.json'), doc, check)
    names = ['trust-audit', 'reference-candidates', 'september-pairs', 'effective-map', 'known-cases', 'boundaries']
    identities = [{'path': (OUT / (name + '.json')).as_posix(), 'size': (ROOT / OUT / (name + '.json')).stat().st_size,
                   'sha256': old.sha256_file(ROOT / OUT / (name + '.json'))} for name in names]
    frozen = envelope('mapping-freeze', artifacts=identities, source_pins_sha256=old.sha256_file(ROOT / PINS),
                      semantic_feedback_allowed=False, stage_status='frozen-provisional-proposal')
    write(OUT / 'mapping-freeze.json', frozen, check)
    return effective['counts']


def verified_freeze(mapping_root=None):
    frozen = read((mapping_root or OUT) / 'mapping-freeze.json')
    for row in frozen['artifacts']:
        p = ROOT / row['path']
        require(p.stat().st_size == row['size'] and old.sha256_file(p) == row['sha256'], f'frozen mapping bytes changed: {row["path"]}')
    return frozen


def bind_extra_inputs():
    require(not (ROOT / EXTRA_PINS).exists(), 'semantic extra pins already exist; no implicit rebind')
    paths = [p for p in (ROOT / 'assets/runtime/data').rglob('*') if p.is_file() and ('script' in p.relative_to(ROOT / 'assets/runtime/data').as_posix().lower() or p.suffix.lower() == '.lua')]
    sources = [semantic.identity(p.relative_to(ROOT), kind='current-runtime-script-corpus') for p in sorted(paths)]
    write(EXTRA_PINS, envelope('semantic-extra-source-pins', sources=sources,
                              provenance='Current runtime extraction; file identity alone does not establish untouched retail-disc provenance.'))
    return len(sources)


def extra_inputs():
    pins = read(EXTRA_PINS)
    for row in pins['sources']:
        p = ROOT / row['path']
        require(p.is_file() and p.stat().st_size == row['size'] and old.sha256_file(p) == row['sha256'], f'extra semantic source changed: {row["path"]}')
    return pins['sources']


def semantic_stage(images, mapping_root=None):
    mapping_root = mapping_root or OUT
    frozen = verified_freeze(mapping_root)
    consumer_paths = frozen.get('consumer_paths', {})
    effective = read(Path(consumer_paths.get('effective_map', (mapping_root / 'effective-map.json').as_posix())))
    primary = {r['donor_start']: r for r in effective['records']}
    september_doc = read(Path(consumer_paths.get('september', (mapping_root / 'september-pairs.json').as_posix())))
    september = {r['donor_start']: r for r in september_doc['trust_dispositions'] if r['disposition'].startswith('retained-')}
    prior = read(semantic.OUT / 'semantic-index.json')['records']
    anchors = {r['id']: r for r in read(semantic.OUT / 'semantic-inventory.json')['anchors']}
    refs = read(semantic.OUT / 'semantic-xrefs.json')['references']
    by_id = {r['id']: r for r in refs}
    by_function = collections.defaultdict(list)
    for r in refs:
        by_function[(r['build'], r['function']['start'], role_key(r))].append(r)
    records = []
    for row in prior:
        start = row['donor_function']['start'] if row['donor_function'] else None
        secondary = september.get(start) if row['build'] == 'sep-2008' else None
        mid = secondary['target_start'] if secondary else start if row['build'] == PRIMARY else None
        pair = primary.get(mid)
        chain = ([{'kind': 'september-trust', 'record_id': secondary['id'], 'donor': start, 'target': mid}] if secondary else [])
        if pair:
            chain.append({'kind': pair['source'], 'donor': mid, 'target': pair['target_start']})
        support, conflicts = [], []
        for ref_id in row['donor_xrefs'] if pair else []:
            ref = by_id[ref_id]
            mids = by_function[(PRIMARY, mid, role_key(ref))] if secondary else [ref]
            a = object_at(images[row['build']], int(ref['anchor_address'], 16))
            for middle in mids:
                m = object_at(images[PRIMARY], int(middle['anchor_address'], 16))
                if identity_token(a) is None or identity_token(a) != identity_token(m):
                    continue
                for target in by_function[(TARGET, pair['target_start'], role_key(ref))]:
                    b = object_at(images[TARGET], int(target['anchor_address'], 16))
                    if identity_token(b) is not None and identity_token(a) != identity_token(b):
                        conflicts.append({'donor_xref': ref_id, 'target_xref': target['id'], 'reason': 'different-complete-literal-at-corresponding-role'})
                    elif identity_token(a) == identity_token(b):
                        callee = primary.get(middle['destination'])
                        callee_ok = ref['role'] == 'call-argument' and callee and callee['target_start'] == target['destination']
                        if secondary and ref['role'] == 'call-argument':
                            sc = september.get(ref['destination'])
                            callee_ok = callee_ok and sc is not None and sc['target_start'] == middle['destination']
                        if callee_ok:
                            support.append({'donor_xref': ref_id, 'middle_xref': middle['id'], 'target_xref': target['id'],
                                            'kind': 'same-complete-literal-role-and-trusted-callee',
                                            'callee_dependency': {'donor': middle['destination'], 'target': target['destination']}})
        status = 'mapping-blocked' if pair is None else 'joined-target-unconfirmed'
        if support:
            status = 'target-corroborated-context' if not anchors[row['anchor_id']]['filters'] else 'filtered-corroborated-context'
        if conflicts:
            status = 'semantic-conflict'
        records.append({'prior_record_id': row['id'], 'anchor_id': row['anchor_id'], 'build': row['build'],
                        'prior_status': row['status'], 'prior_joined': row['mapping'] is not None,
                        'mapping_dependencies': chain, 'target_start': pair['target_start'] if pair else None,
                        'status': status, 'target_corroboration': support, 'contradictions': conflicts,
                        'prior_mapping_suppressed': row['mapping'] is not None and pair is None,
                        'reason': 'No trusted route through the frozen mapping proposal.' if pair is None else 'Independent target role and callee checked; filters and conflicts retain precedence.',
                        'semantic_role': 'Literal passed in corresponding argument to a trusted corresponding callee.' if support else None,
                        'proposed_name': None, 'canonical_adoption': False})
    require(len(records) == 51657 and len({r['prior_record_id'] for r in records}) == len(records), 'semantic terminal reconciliation failed')
    verified_freeze(mapping_root)
    return envelope('semantic-v2', mapping_freeze_sha256=old.sha256_file(ROOT / mapping_root / 'mapping-freeze.json'), records=records,
                    counts={'records': len(records), 'statuses': dict(sorted(collections.Counter(r['status'] for r in records).items())),
                            'newly_joined': sum(r['target_start'] is not None and not r['prior_joined'] for r in records),
                            'september_routed': sum(r['build'] == 'sep-2008' and r['target_start'] is not None for r in records),
                            'september_corroborated': sum(r['build'] == 'sep-2008' and bool(r['target_corroboration']) for r in records)})


class LuaChunk:
    """Strict Lua 5.1 standard chunk parser; metadata only, never executes code."""
    def __init__(self, data):
        require(len(data) >= 12 and data[:6] == b'\x1bLua\x51\x00', 'unsupported Lua signature/version/format')
        endian, self.int_size, self.size_size, instruction_size, self.number_size, self.integral = data[6:12]
        require(endian in (0,1) and self.int_size in (4,8) and self.size_size in (4,8) and instruction_size == 4 and self.number_size in (4,8) and self.integral in (0,1), 'unsupported Lua scalar layout')
        self.order = 'little' if endian else 'big'
        self.data, self.offset, self.prototypes = data, 12, []

    def take(self, count):
        require(0 <= count <= len(self.data) - self.offset, f'Lua truncated at offset {self.offset}')
        value = self.data[self.offset:self.offset + count]
        self.offset += count
        return value

    def integer(self, size=None):
        value = int.from_bytes(self.take(size or self.int_size), self.order)
        require(value <= len(self.data) * 8, 'Lua count exceeds file bound')
        return value

    def string(self):
        size = self.integer(self.size_size)
        data = self.take(size)
        require(not data or data[-1] == 0, 'Lua string lacks terminator')
        return data[:-1] if data else b''

    def prototype(self, path='0', depth=0):
        require(depth < 128, 'Lua prototype recursion bound')
        begin = self.offset
        source = self.string()
        line_start, line_end = self.integer(), self.integer()
        nups, params, vararg, stack = self.take(4)
        code_count = self.integer()
        code = self.take(code_count * 4)
        constants = []
        strings = []
        for _ in range(self.integer()):
            tag = self.take(1)[0]
            if tag == 0:
                value = b''
            elif tag == 1:
                value = self.take(1)
                require(value in (b'\0',b'\1'), 'invalid Lua boolean')
            elif tag == 3:
                value = self.take(self.number_size)
            elif tag == 4:
                value = self.string()
                strings.append({'length': len(value), 'sha256': digest(value)})
            else:
                raise ValueError(f'unsupported Lua constant tag {tag} at {self.offset - 1}')
            constants.append({'type': tag, 'sha256': digest(value), 'length': len(value)})
        children = [self.prototype(path + '.' + str(i), depth + 1) for i in range(self.integer())]
        line_count = self.integer()
        self.take(line_count * self.int_size)
        locals_count = self.integer()
        for _ in range(locals_count):
            self.string()
            self.integer()
            self.integer()
        upvalue_count = self.integer()
        for _ in range(upvalue_count):
            self.string()
        executable = {'nups': nups, 'parameters': params, 'vararg': vararg, 'stack': stack,
                      'code_sha256': digest(code), 'constants': constants, 'children': children}
        result = digest(payload(executable))
        self.prototypes.append({'path': path, 'offset': begin, 'end_exclusive': self.offset,
                                'instruction_count': code_count, 'constant_count': len(constants), 'string_constants': strings,
                                'source_sha256': digest(source), 'source_length': len(source),
                                'line_start': line_start, 'line_end': line_end, 'line_info_count': line_count,
                                'local_debug_count': locals_count, 'upvalue_debug_count': upvalue_count,
                                'executable_structure_sha256': result})
        return result

    def parse(self):
        fingerprint = self.prototype()
        require(self.offset == len(self.data), f'Lua trailing bytes at offset {self.offset}')
        return {'executable_structure_sha256': fingerprint, 'prototypes': sorted(self.prototypes, key=lambda r:r['path']),
                'header_sha256': digest(self.data[:12]), 'endianness': self.order}


def script_stage():
    inventory = read(semantic.P1 / 'prototype-inventory.json')
    records = []
    sources = [(i,row,semantic.CORPUS / inventory['build_summaries'][row['build_id']]['directory_name'] / row['relative_path']) for i,row in enumerate(inventory['files'])]
    for i,row in enumerate(extra_inputs()):
        sources.append((i,{'build_id':'current-runtime','relative_path':row['path'].removeprefix('assets/runtime/'),'size':row['size'],'sha256':row['sha256']},ROOT / row['path']))
    for i, row, source in sources:
        path = row['relative_path']
        lower = path.lower()
        if 'script' not in lower and not lower.endswith('.lua'):
            continue
        item = {'build': row['build_id'], 'path': path, 'source_json_pointer': f'/files/{i}',
                'size': row['size'], 'sha256': row['sha256'], 'runtime_state_proven': False,
                'state_path_category': 'gui' if 'gui' in lower else 'startup' if 'startup' in lower else 'game-or-unknown',
                'canonical_adoption': False}
        item['source'] = EXTRA_PINS.as_posix() if row['build_id'] == 'current-runtime' else (semantic.P1 / 'prototype-inventory.json').as_posix()
        if row['build_id'] == 'current-runtime':
            item['source_json_pointer'] = f'/sources/{i}'
        if lower.endswith('.lua'):
            data = source.read_bytes()
            require(digest(data) == row['sha256'], 'script source changed')
            try:
                item['parsed'] = LuaChunk(data).parse()
                item['status'] = 'parsed-lua51-metadata'
            except ValueError as error:
                item['status'] = 'unsupported-or-invalid-format'
                item['blocker'] = str(error)
        else:
            item['status'] = 'inventory-only'
            item['blocker'] = 'No validated bank-entry parser or native Lua-state ownership proof in the consumed evidence.'
        records.append(item)
    by_path = {(r['build'], r['path'].lower()):r for r in records}
    pairs = []
    for row in records:
        lower = row['path'].lower()
        if 'data/scripts/' not in lower or 'parsed' not in row:
            continue
        other = by_path.get((row['build'], lower.replace('data/scripts/', 'data/scripts_r/', 1)))
        if other is not None and 'parsed' in other:
            pairs.append({'build': row['build'], 'scripts': row['path'], 'scripts_r': other['path'],
                          'same_executable_structure': row['parsed']['executable_structure_sha256'] == other['parsed']['executable_structure_sha256'],
                          'scripts_debug_rows': sum(p['line_info_count'] + p['local_debug_count'] + p['upvalue_debug_count'] for p in row['parsed']['prototypes']),
                          'scripts_r_debug_rows': sum(p['line_info_count'] + p['local_debug_count'] + p['upvalue_debug_count'] for p in other['parsed']['prototypes'])})
    return envelope('scripts', records=records, script_pairs=pairs, extra_source_pins_sha256=old.sha256_file(ROOT / EXTRA_PINS),
                    counts={'inventoried': len(records), 'parsed': sum('parsed' in r for r in records), 'paired': len(pairs),
                            'identical_executable_structure': sum(r['same_executable_structure'] for r in pairs)},
                    limitations=['Path categories do not prove distinct runtime Lua states.', 'No script executed.',
                                 'No native binding or callable TU1 command is established by bytecode constants.'])


def type_global_stage(images):
    anchors = read(semantic.OUT / 'semantic-inventory.json')['anchors']
    refs = read(semantic.OUT / 'semantic-xrefs.json')['references']
    types = []
    for anchor in anchors:
        if 'rtti-type-name' not in anchor['categories']:
            continue
        locations = {(r['build'], r['address']) for r in anchor['occurrences']}
        types.append({'anchor_id': anchor['id'], 'spelling': anchor['spelling'],
                      'occurrences': anchor['occurrences'],
                      'native_xref_ids': [r['id'] for r in refs if (r['build'], r['anchor_address']) in locations],
                      'status': 'type-name-context-only', 'constructor_identity_proven': False,
                      'blocker': 'A type name and a native reference do not establish a complete RTTI descriptor, constructor, or vtable relationship.'})
    tables = []
    for build, image in sorted(images.items()):
        for block in image.blocks:
            if block.name not in ('.rdata','.data') or block.execute:
                continue
            run = []
            def finish():
                if len(run) >= 3:
                    tables.append({'build': build, 'section': block.name, 'start': native.hx(run[0][0]),
                                   'end_exclusive': native.hx(run[-1][0] + 4),
                                   'slots': [{'slot': native.hx(slot), 'entry': native.hx(entry)} for slot,entry in run],
                                   'candidate_kind': 'contiguous-exact-pdata-pointer-run', 'object_boundary_proven': False,
                                   'vtable_proven': False, 'alternatives': ['callback-array','adjacent-mixed-data','vtable-or-multiple-vtables'],
                                   'canonical_adoption': False})
            for offset in range(0, len(block.data) - 3, 4):
                value = int.from_bytes(block.data[offset:offset + 4], 'big')
                if value in image.by_start:
                    run.append((block.start + offset, value))
                else:
                    finish()
                    run = []
            finish()
    effective = {r['donor_start']: r for r in read(OUT / 'effective-map.json')['records']}
    globals_rows = []
    for row in read(semantic.OUT / 'semantic-globals.json')['records']:
        start = row['donor_access']['function']['start']
        retained = start in effective and effective[start]['target_start'] == row['target_access']['function']['start']
        globals_rows.append({'prior_global_id': row['id'], 'mapping_retained': retained,
                             'compatible_access_and_content': row['content_equal'] and row['compatible_width_and_direction'],
                             'object_boundary_proven': False, 'semantic_acceptance': False,
                             'status': 'bounded-scalar-candidate' if retained and row['content_equal'] and row['compatible_width_and_direction'] else 'rejected-or-suppressed-scalar-context'})
    new_global_count = 0
    for mapping in effective.values():
        if mapping['source'] != 'phase2c-proposal':
            continue
        d = images[PRIMARY].by_start[int(mapping['donor_start'],16)]
        t = images[TARGET].by_start[int(mapping['target_start'],16)]
        _, uses, _ = native.scan_function(images[PRIMARY],d,set())
        _, target_uses, _ = native.scan_function(images[TARGET],t,set())
        indexed = {int(r['instruction'],16)-t['start']:r for r in target_uses}
        for use in uses:
            target_use = indexed.get(int(use['instruction'],16)-d['start'])
            if target_use is None:
                continue
            equal = native.compatible_access(use,target_use) and images[PRIMARY].read(int(use['address'],16),use['width']) == images[TARGET].read(int(target_use['address'],16),target_use['width'])
            globals_rows.append({'mapping':mapping,'donor_access':use,'target_access':target_use,
                                 'compatible_access_and_content':equal,'object_boundary_proven':False,
                                 'semantic_acceptance':False,'status':'new-bounded-scalar-candidate' if equal else 'rejected-scalar-access-or-content'})
            new_global_count += 1
    target_runs = collections.defaultdict(list)
    for table in tables:
        if table['build'] == TARGET:
            target_runs[tuple(s['entry'] for s in table['slots'])].append(table['start'])
    for table in tables:
        if table['build'] != PRIMARY:
            continue
        mapped = [effective.get(s['entry']) for s in table['slots']]
        table['trusted_slot_count'] = sum(m is not None for m in mapped)
        table['matching_target_pointer_runs'] = target_runs.get(tuple(m['target_start'] for m in mapped),[]) if all(mapped) else []
    return envelope('types-globals', type_contexts=types, pointer_runs=tables, globals=globals_rows,
                    counts={'type_contexts': len(types), 'pointer_runs': len(tables), 'proven_vtables': 0,
                            'global_contexts': len(globals_rows), 'new_global_contexts':new_global_count,'proven_global_objects': 0},
                    limitations=['Pointer runs alone cannot distinguish vtables from callback arrays.',
                                 'Interior jump-table targets are excluded, but exact function pointers still have competing interpretations.',
                                 'No complete RTTI-object parser or native constructor ownership proof was recovered in this bounded pass.'])


def callback_payload_shape(words, start):
    """One demonstrated constructor shape, not a generic Lua API recognizer.

    The fixed instructions prove register flow and payload size. Calls and the
    adapter address are returned as obligations, never assumed equivalent.
    """
    fixed = {0:0x7D8802A6,2:0x9421FF80,3:0x7C7E1B78,4:0x7C9F2378,
             5:0x7CBD2B78,6:0x817E0000,7:0x2B0B0000,8:0x419A006C,
             9:0x838B0000,10:0x3880D8F0,11:0x80AB0004,12:0x7F83E378,
             14:0x38800004,15:0x7F83E378,17:0x7C6B1B78,19:0x38A00001,
             21:0x7F83E378,22:0x93AB0000,24:0x7FE5FB78,25:0x7F84E378,
             26:0x7FC3F378,28:0x7FE5FB78,29:0x3880FFFE,30:0x7F83E378,
             32:0x817C0008,33:0x392BFFF8,34:0x913C0008,35:0x38210080}
    if len(words) != 37 or any(words[i] != w for i,w in fixed.items()):
        return None
    calls = (1,13,16,23,27,31)
    if any(words[i] & 0xFC000003 != 0x48000001 for i in calls):
        return None
    if words[36] & 0xFC000003 != 0x48000000:
        return None
    if words[18] >> 16 != 0x3D40 or words[20] >> 16 != 0x388A:
        return None
    return {'calls':{str(i*4):native.hx(native.branch(words[i],start+i*4)) for i in calls},
            'adapter':native.hx(((words[18] & 0xFFFF)*65536 + native.signed(words[20] & 0xFFFF)) & 0xFFFFFFFF),
            'payload_size':4,'callback_store_offset':0,'callback_store_width':4,
            'incoming_name_register':4,'incoming_callback_register':5,'capture_count':1,
            'unverified_obligations':['allocation-callee','closure-callee','adapter','key-consumer','state-and-namespace']}


def registration_stage(images):
    anchors = read(semantic.OUT / 'semantic-inventory.json')['anchors']
    refs = read(semantic.OUT / 'semantic-xrefs.json')['references']
    candidates = []
    for anchor in anchors:
        if anchor['filters'] or 'distinctive-debug-lua-command' not in anchor['categories']:
            continue
        occurrences = {(o['build'], o['address']) for o in anchor['occurrences']}
        found = [r for r in refs if r['build'] == PRIMARY and (r['build'], r['anchor_address']) in occurrences]
        for ref in found:
            candidates.append((0 if 'freecam' in anchor['spelling'].lower() else 1,
                               -len(found), anchor['id'], ref['function']['start'], ref, anchor))
    selected, seen = [], set()
    for _, _, _, start, ref, anchor in sorted(candidates, key=lambda r:r[:4]):
        if start in seen:
            continue
        seen.add(start)
        image = images[PRIMARY]
        f = image.by_start[int(start,16)]
        # Small documented reconnaissance set, with an explicit byte bound.
        end = min(f['end'], f['start'] + 2048)
        _,_,calls = native.scan_function(image, f, set())
        callees = []
        for address in sorted({int(c['target'],16) for c in calls})[:4]:
            callee = image.by_start.get(address)
            if callee:
                limit = min(callee['end'], address + 512)
                callees.append({'boundary': native.boundary(callee), 'inspected_end': native.hx(limit),
                                'disassembly': disassemble(image, address, limit),
                                'incoming_argument_stores': native.descriptor_stores(image,address)})
        selected.append({'anchor_id': anchor['id'], 'spelling': anchor['spelling'], 'xref': ref,
                         'boundary': native.boundary(f), 'inspected_end': native.hx(end),
                         'disassembly': disassemble(image,f['start'],end), 'callees': callees,
                         'result': 'structure-not-proven', 'new_recognizer_authorized_by_evidence': False,
                         'blocker': 'No complete repeated name/callback descriptor, field-flow and registration consumer chain has been established from this inspected slice.'})
        if len(selected) == 6:
            break
    original = read(semantic.OUT / 'semantic-registrations.json')['records']
    layouts = []
    population = collections.Counter()
    for build,image in sorted(images.items()):
        for f in image.functions:
            population[build] += 1
            if f['end']-f['start'] != 148:
                continue
            shape = callback_payload_shape(struct.unpack('>37I',image.read(f['start'],148)),f['start'])
            if shape:
                layouts.append({'build':build,'boundary':native.boundary(f),'shape':shape,
                                'grade':'candidate-native-construction-shape','semantic_transport':False})
    # Manually inspected first-party chain. These addresses select evidence;
    # they do not create a mapping or exempt a candidate from the recognizer.
    image = images[PRIMARY]
    proof = []
    for address in (0x82309378,0x82227B88,0x8219A600,0x822CA4F0,0x82A23F08,0x823CFC10):
        f = image.by_start[address]
        proof.append({'boundary':native.boundary(f),
                      'disassembly':disassemble(image,address,f['end']),
                      'body_sha256':digest(image.read(address,f['end']-address))})
    callback = code_region(image,0x82482298)
    callback['disassembly'] = disassemble(image,0x82482298,0x824822A4)
    structure = {'build':PRIMARY,'grade':'confirmed-native-payload-construction',
                 'interpretation_grade':'probable-script-registration; state/namespace-unproven',
                 'caller':'0x82484E28','callsite':'0x82484E58','helper':'0x82309378',
                 'name':object_at(image,0x820BA1FC),'callback_region':callback,
                 'payload':{'requested_size':4,'callback_offset':0,'callback_width':4},
                 'adapter':'0x822CA4F0','adapter_behavior':'loads captured callback, obtains an argument, invokes through CTR, returns zero',
                 'callback_behavior':'stores incoming r3 low byte at 0x83496BE9 and returns',
                 'closure_behavior':'stores adapter at object+16 and captures one eight-byte stack value',
                 'key_behavior':'measures complete name, constructs tag-4 key, supplies key and top value to a consumer',
                 'evidence':proof,'semantic_transport':False,'canonical_adoption':False,
                 'blockers':['No frozen primary pair chain for this caller/helper/adapter/internal callback.',
                             'Game/GUI/startup state and Debug namespace ownership remain unproven.']}
    require(any(r['build']==PRIMARY and r['boundary']['start']==structure['helper'] for r in layouts),
            'documented native constructor no longer satisfies the recognizer')
    layout_by_build = collections.defaultdict(dict)
    for layout in layouts:
        layout_by_build[layout['build']][layout['boundary']['start']] = layout
    cached = read(semantic.consistency.ARTIFACTS['exhaustive_function_features'])['builds']
    uses = []
    for build,image in sorted(images.items()):
        helpers = layout_by_build[build]
        if build in cached:
            callers = [image.by_start[int(f['start'],16)] for f in cached[build]
                       if any(c['target'] in helpers for c in f['direct_calls'])]
        else:
            callers = []
            destinations = {int(a,16) for a in helpers}
            for f in image.functions:
                for i,(word,) in enumerate(struct.iter_unpack('>I',image.read(f['start'],f['end']-f['start']))):
                    if word & 0xFC000003 == 0x48000001 and native.branch(word,f['start']+i*4) in destinations:
                        callers.append(f)
                        break
        for f in callers:
            _,_,calls = native.scan_function(image,f,set())
            for call in calls:
                if call['target'] not in helpers:
                    continue
                name,callback_arg = (call['arguments'].get(r) for r in ('r4','r5'))
                record = {'build':build,'caller':native.boundary(f),'call':call,
                          'helper':call['target'],'layout_grade':'constructor-shape-only',
                          'name':None,'callback':None,'semantic_transport':False,
                          'blockers':list(helpers[call['target']]['shape']['unverified_obligations'])}
                if name and image.block(int(name['value'],16)):
                    record['name'] = object_at(image,int(name['value'],16))
                if callback_arg:
                    address = int(callback_arg['value'],16)
                    block = image.block(address,4)
                    if block is not None and block.execute and address % 4 == 0:
                        owner = image.by_start.get(address)
                        record['callback'] = {'kind':'pdata-function','boundary':native.boundary(owner)} if owner else code_region(image,address)
                if record['name'] is None or identity_token(record['name']) is None:
                    record['blockers'].append('complete-native-name-not-recovered')
                if record['callback'] is None:
                    record['blockers'].append('native-callback-not-recovered')
                uses.append(record)
    return envelope('registration', inspected=selected, available_native_contexts=len(candidates),
                    prior_layout_records=len(original), prior_rejection_reasons=dict(sorted(collections.Counter(reason for r in original for reason in r['reasons']).items())),
                    recovered_structures=[structure], new_recognizers=['four-byte-callback-payload-v1'],
                    recognizer_population=dict(sorted(population.items())),recognizer_candidates=layouts,
                    constructor_uses=uses,
                    counts={'shape_candidates':len(layouts),'constructor_calls':len(uses),
                            'calls_with_complete_name_and_callback':sum(r['name'] is not None and identity_token(r['name']) is not None and r['callback'] is not None for r in uses),
                            'proven_tu1_command_chains':0},
                    phase2b_failure='Runtime payload construction spans callees; it is not an adjacent static name/callback descriptor. The old incoming-store recognizer also stops at the prologue.',
                    limitation='This is bounded reconnaissance. It does not prove the absence of native registration or identify the general engine registration architecture.')


def preservation_stage(semantic_v2):
    inventory = read(semantic.P1 / 'prototype-inventory.json')
    menu = read(semantic.P1 / 'prototype-debug-interfaces.json')['debug_menu_entries']
    symbols = read(semantic.P1 / 'prototype-script-symbols.json')['records']
    anchors = read(semantic.OUT / 'semantic-inventory.json')['anchors']
    anchor_by_name = {a['spelling']: a['id'] for a in anchors}
    semantic_by_anchor = collections.defaultdict(list)
    for row in semantic_v2['records']:
        if row['target_corroboration']:
            semantic_by_anchor[row['anchor_id']].append(row['prior_record_id'])
    groups = collections.defaultdict(list)
    terms = ('freecam','camera','teleport','spawn','shader','render','profil','environment','lighting','e3','demo','presentation','tutorial','quest','cutscene','region','level')
    for i,row in enumerate(menu):
        if any(term in (row['expression'] + ' ' + row['label']).lower() for term in terms):
            groups[('debug-interface', row['build_id'], row['source_path'])].append({'source': (semantic.P1 / 'prototype-debug-interfaces.json').as_posix(),
                'json_pointer': f'/debug_menu_entries/{i}', 'line': row['source_line'], 'label': row['label'],
                'required_command_names': row['names'],
                'corroborated_contexts': sorted({r for name in row['names'] for r in semantic_by_anchor[anchor_by_name.get(name)]})})
    records = [{'kind': kind, 'build': build, 'path': path, 'grade': 'confirmed-first-party-interface-presence',
                'portability_class': 'native-dependent', 'dependencies': rows, 'tu1_callable': False,
                'retail_presence': 'not-established-by-interface-presence', 'canonical_adoption': False}
               for (kind,build,path),rows in sorted(groups.items())]
    for i,row in enumerate(inventory['files']):
        if any(term in row['relative_path'].lower() for term in ('e3','demo','presentation','tutorial','quest','cutscene','region','level')):
            records.append({'kind': 'historical-content-path', 'build': row['build_id'], 'path': row['relative_path'],
                            'grade': 'confirmed-file-presence-candidate-purpose', 'sha256': row['sha256'], 'size': row['size'],
                            'source': (semantic.P1 / 'prototype-inventory.json').as_posix(), 'json_pointer': f'/files/{i}',
                            'portability_class': 'unknown', 'dependencies': [],
                            'blocker': 'Path alone does not establish a runnable entry or content dependency closure.',
                            'retail_presence': 'unresolved-container-content', 'canonical_adoption': False})
    runtime = {r['path'].removeprefix('assets/runtime/').lower():r for r in extra_inputs()}
    for row in records:
        current = runtime.get(row['path'].lower())
        row['current_runtime_presence'] = {'status':'same-path-present','identity':current,
            'identical_to_prototype_file':row.get('sha256') == current['sha256']} if current else {'status':'not-in-bound-runtime-script-inventory'}
    return envelope('preservation', records=records, counts={'records':len(records),
                    'portability':dict(sorted(collections.Counter(r['portability_class'] for r in records).items()))},
                    community_only_free_camera_acceptance=False,
                    limitations=['No demo or debug feature integrated or executed.', 'Container content and retail resource dependencies remain unproved.',
                                 'Presence candidates are not claims of recoverability.'])


def intersection_stage(images, semantic_v2):
    sets = semantic.problem_sets()
    indexes = {key: [r[0] for r in rows] for key,rows in sets.items()}
    effective = read(OUT / 'effective-map.json')
    records = []
    for mapping in effective['records']:
        f = images[TARGET].by_start[int(mapping['target_start'],16)]
        links = []
        for key, rows in sets.items():
            lo, hi = bisect.bisect_left(indexes[key],f['start']), bisect.bisect_left(indexes[key],f['end'])
            links.extend({'set': key,'address':native.hx(a),'source':p,'json_pointer':j,'disposition':s} for a,p,j,s in rows[lo:hi])
        records.append({'donor_start':mapping['donor_start'], 'target_start':mapping['target_start'],
                        'mapping_source':mapping['source'],'intersections':links})
    return envelope('intersections',records=records,
                    counts={key:sum(any(x['set']==key for x in r['intersections']) for r in records) for key in sets},
                    limitation='Membership affects priority only. Historical crash entries retain their resolved dispositions.')


def select_review(strata, limit=3):
    records, counts = [], {}
    for name, ids in sorted(strata.items()):
        available = sorted(set(ids))
        selected = available[:limit]
        counts[name] = {'available':len(available),'selected':len(selected)}
        records.extend({'stratum':name,'record_id':key} for key in selected)
    return records, counts


def summarize(check=False):
    verified_freeze()
    audit = read(OUT / 'trust-audit.json')
    candidates = read(OUT / 'reference-candidates.json')
    effective = read(OUT / 'effective-map.json')
    september = read(OUT / 'september-pairs.json')
    semantics_v2 = read(OUT / 'semantic-v2.json')
    scripts = read(OUT / 'scripts.json')
    types = read(OUT / 'types-globals.json')
    preservation = read(OUT / 'preservation.json')
    registration = read(OUT / 'registration.json')
    boundaries = read(OUT / 'boundaries.json')
    intersections = read(OUT / 'intersections.json')
    strata = {name:[] for name in ('retained-independent-evidence','retained-full-object-corroborated','suppressed-semantic-collision','review-required-partial-anchor',
                                     'reviewed-strong-proposal','reviewed-probable-proposal','candidate','ambiguous','rejected-proposal','registration-proven','registration-unproved')}
    for row in audit['records']:
        strata.setdefault(row['disposition'],[]).append('trust-audit:' + row['id'])
    for row in candidates['proposals']:
        strata[row['grade']].append('reference-candidates:' + row['donor_start'] + ':' + row['target_start'])
    anchors = {r['id']:r for r in read(semantic.OUT / 'semantic-inventory.json')['anchors']}
    for row in semantics_v2['records']:
        strata.setdefault('semantic:'+row['status'],[]).append('semantic-v2:'+row['prior_record_id'])
        strata.setdefault('subsystem:'+anchors[row['anchor_id']]['subsystem'],[]).append('semantic-v2:'+row['prior_record_id'])
    for row in registration['inspected']:
        strata['registration-unproved'].append('registration:'+row['boundary']['start'])
    for row in intersections['records']:
        for link in row['intersections']:
            strata.setdefault('intersection:'+link['set'],[]).append('intersections:'+row['target_start'])
    queue, availability = select_review(strata)
    write(OUT / 'review.json',envelope('review',records=queue,availability=availability,selection_policy='first-three-sorted-unique-identifiers-per-stratum; overlapping strata'),check)
    artifacts = [{'path':p.relative_to(ROOT).as_posix(),'size':p.stat().st_size,'sha256':old.sha256_file(p)} for p in sorted((ROOT / OUT).glob('*.json'))]
    counts = {'trust_audit':audit['counts'],'reference_candidates':candidates['counts'],'effective_map':effective['counts'],
              'september':september['trust_counts'],'semantic_v2':semantics_v2['counts'],'types_globals':types['counts'],
              'scripts':scripts['counts'],'preservation':preservation['counts'],'boundary_classes':boundaries['classes'],
              'september_boundary_review':len(boundaries['september_boundary_review']), 'registration_inspected':len(registration['inspected']),
              'registration_structures':len(registration['recovered_structures']), 'intersections':intersections['counts']}
    primary_by_donor = {r['donor_start']:r for r in effective['records']}
    counts['september_two_hop_function_routes'] = sum(r['disposition'].startswith('retained-') and r['target_start'] in primary_by_donor for r in september['trust_dispositions'])
    counts['strong_proposal_evidence_combinations'] = dict(sorted(collections.Counter(
        '+'.join(sorted({s['class'] for s in p['independent_support']})) for p in effective['additions']).items()))
    counts['strong_proposals_with_multiple_reference_identities'] = sum(len({tuple(r['identity']) for r in p['canonicalized_reference_evidence']['canonicalized_references']}) > 1 for p in effective['additions'])
    counts['proposal_intersections'] = {key:sum(r['mapping_source']=='phase2c-proposal' and any(x['set']==key for x in r['intersections']) for r in intersections['records']) for key in intersections['counts']}
    counts['registration_recognizer_candidates'] = dict(sorted(collections.Counter(r['build'] for r in registration['recognizer_candidates']).items()))
    counts['registration_calls'] = registration['counts']
    counts['original_evidence_strata'] = dict(sorted(collections.Counter('+'.join(r['feature_classes']) for r in audit['records']).items()))
    counts['mapping_review_grade_presence'] = {grade:sum(any(p['grade']==grade for p in r['candidates']) for r in candidates['records']) for grade in candidates['counts']['proposal_grades']}
    semantic_by_id = {r['prior_record_id']:r for r in semantics_v2['records']}
    subsystem_grades = collections.Counter()
    for row in candidates['records']:
        subsystem = anchors[semantic_by_id[row['association_id']]['anchor_id']]['subsystem']
        for grade in sorted({p['grade'] for p in row['candidates']}):
            subsystem_grades[subsystem+':'+grade] += 1
    counts['mapping_review_subsystem_grade_presence'] = dict(sorted(subsystem_grades.items()))
    suppressed = [{'donor':r['donor_start'],'target':r['target_start'],'audit_id':r['id']} for r in audit['records'] if r['disposition']=='suppressed-semantic-collision']
    known = [{'donor':p['donor_start'],'target':p['target_start'],'grade':p['grade'],'generation':p['generation']} for p in candidates['proposals'] if p['donor_start'] in ('0x82631A30','0x829506B0','0x8229B488')]
    limitations = [
        'The transport audit uses bounded instruction recovery. It does not prove complete semantic equivalence of every retained function.',
        'Physics same-name pairs remain candidates because the strict matcher has no independent trusted caller/callee or two-sided exact-delta support for them. Their immediate helpers also contain a changed global reference and different call destinations.',
        'Boundary reconnaissance retains exact shared windows and all 33 September boundary-review rows, but does not resolve split/merge/outline/inline/thunk/tail lineage. The two unmatched primary functions remain unexplained at function level.',
        'One native four-byte callback-payload construction chain is demonstrated. Its narrow recognizer returns 206 shape candidates across three builds, each retaining unverified callee/state obligations. No complete frozen TU1 registration chain or callable command is claimed.',
        'RTTI/type names and pointer runs do not prove constructors, vtables or stable global objects. This pass supplies candidates and negative gates, not a complete typed reconstruction.',
        'No validated script-bank entry parser or distinct native Lua-state ownership chain was recovered. Loose standard Lua 5.1 chunks were parsed without execution; current-runtime file provenance is separate from authenticated retail-disc provenance.',
        'The requested full compiler-transformation recovery, exhaustive feature-ablation audit, broader mapping features, and complete required fixture matrix are not complete. This checkpoint must not be represented as completed Phase 2C.',
    ]
    lines = ['# Phase 2C static archaeology checkpoint', '', '**Phase 2C is not complete.** This is a reproducible provisional evidence layer; no canonical adoption is authorized.', '',
             'Build 23 and TU1 remain very closely related, but are not byte-identical semantic layouts. One semantic collision does not invalidate all 15,299 Phase 2A mappings. Phase 2A exact-image precision was a control result, not measured cross-build precision.', '',
             f"The bounded audit retains {effective['counts']['closed'] - effective['counts']['suppressed_or_review_excluded']} closed pairs and suppresses {effective['counts']['suppressed_or_review_excluded']}. The provisional effective view adds {effective['counts']['additions']} policy-strong proposals, giving {effective['counts']['effective']} pairs (delta {effective['counts']['delta']:+d}).", '',
             'A `reviewed-strong-proposal` is a machine policy disposition with explicit `not-human-reviewed` state. It is not an accepted Phase 2A mapping or a source-lineage claim.', '',
             '## Exact reconciled counts', '', '```json', json.dumps(counts,sort_keys=True,indent=2), '```', '',
             'Anchor-classification counts count windows; 97 distinct accepted pairs carry 113 shared windows. Full-string comparison requires terminated content; zero-filled storage is not automatically an empty string. Only a proven byte-read context may tokenize an empty terminator.', '',
             '## Suppressions', '', '```json',json.dumps(suppressed,indent=2),'```','',
             'The conflicts are Navigator versus Controlled, TROLL_FOOTSTEP versus DESTROY_ENTITY, and __vspltb(%s, %d) versus __vcfsx(%s, %d). Suppression bars semantic transport; it does not conclusively disprove generic code/body reuse.', '',
             '## Known-case dispositions', '', '```json',json.dumps(known,indent=2),'```','',
             'All four physics wrappers are exact 0x3C .pdata intervals. The donor Navigator wrapper is [0x82631A30,0x82631A6C), TU1 Navigator [0x82630C30,0x82630C6C), donor Controlled [0x829506B0,0x829506EC), TU1 Controlled [0x82950A98,0x82950AD4). Their r4 literal role and r5=-1 agree; this alone is insufficient independent correspondence support.', '',
             'HammerCombat: exact caller [0x8229B308,0x8229B484) -> [0x8229B038,0x8229B1B4). The 0x7C callee compares string-like content and returns inequality. The caller passes object offset +8, returns zero when equal to HammerCombat, and otherwise evaluates remaining field-dependent logic. This is an exclusion-guard context, not a function named HammerCombat.', '',
             'The comparator regions [0x8226DB80,0x8226DBD4) and [0x8226D7F8,0x8226D84C) have 21 reachable instructions and identical bytes. Neither has .pdata ownership or an independent .pdata entry. They remain internal code regions.', '',
             '## Limits and unfinished completion gates', '']
    lines.extend('- '+s for s in limitations)
    lines += ['', '## Native registration reconnaissance', '',
              'CONFIRMED: build-23 callsite 0x82484E58 passes SetUseFreeCamera at 0x820BA1FC in r4 and callback 0x82482298 in r5 to 0x82309378. The helper constructs a four-byte callback payload and adapter closure, then supplies the name to a key consumer. This is an interprocedural runtime layout, which the old adjacent-pointer recognizer did not cover.', '',
              'The callback [0x82482298,0x824822A4) stores the low byte of r3 at 0x83496BE9 and returns. It has no .pdata owner. The narrow constructor recognizer retains every callee, adapter and state/namespace obligation; it does not establish callable TU1 commands. Full evidence is in registration.json.', '',
              '## Unfiltered TU1-corroborated contexts', '']
    for row in semantics_v2['records']:
        if row['status'] == 'target-corroborated-context':
            lines.append('- `' + row['prior_record_id'] + '`: `' + anchors[row['anchor_id']]['spelling'] + '` — corresponding literal argument and trusted callee at TU1 `' + row['target_start'] + '`. This is a contextual role, not a function name.')
    lines += ['', 'The historical ownership reconstruction fails with `FAIL: stale manifest`; the old plan is preserved. Current ledger/plan validation is separate. See verification.md for exact inputs and results.', '']
    lines += ['', '## Exact artifact bytes', '', '| Path | Bytes | SHA-256 |', '| --- | ---: | --- |']
    lines.extend(f"| `{r['path']}` | {r['size']} | `{r['sha256']}` |" for r in artifacts)
    lines += ['', 'Closed phases and SDK inputs are rehashed before every analysis command. The mapping freeze is checked before and after semantic analysis. All analytical outputs omit the clock and current HEAD. Exact commands are in README.md.', '',
              'Neither game was executed. No build, codegen, runtime, renderer, manifest, generated-code, canonical naming, binary modification, push, fetch, pull, merge, tag, PR, upload or release operation was performed.', '']
    report = ('\n'.join(lines)).encode()
    report_identity = write(DOC / 'report.md',report,check)
    implementation_paths = ['tools/Fable2PrototypeTrust.py','tools/Verify-Fable2PrototypeTrust.ps1','tools/schemas/fable2-prototype-trust-v1.schema.json','tests/test_fable2_prototype_trust.py']
    implementation_paths += [(DOC/name).as_posix() for name in ('README.md','policy.md','review-guide.md','next-phase-handoff.md','verification.md')]
    implementation = [semantic.identity(Path(p),kind='phase2c-implementation') for p in implementation_paths]
    validation = envelope('validation',phase_complete=False,counts=counts,suppressions=suppressed,known_dispositions=known,
                          artifacts=artifacts,report=report_identity,implementation=implementation,limitations=limitations,
                          source_pins_sha256=old.sha256_file(ROOT / PINS),extra_source_pins_sha256=old.sha256_file(ROOT / EXTRA_PINS))
    write(DOC / 'evidence/validation.json',validation,check)
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('bind', 'bind-semantic-inputs', 'audit', 'verify-audit', 'candidates', 'verify-candidates', 'september', 'verify-september', 'freeze', 'verify-freeze', 'semantics', 'verify-semantics','summarize','verify-summary'))
    args = parser.parse_args()
    if args.command == 'bind':
        require(not (ROOT / PINS).exists(), 'source pins already exist; refusing rebind')
        result = binding()
        write(PINS, result)
        print(f'Bound {len(result["sources"])} source files')
        return
    pins, images, features, pairs = load_inputs()
    if args.command in ('summarize','verify-summary'):
        print(json.dumps(summarize(args.command == 'verify-summary'),indent=2))
        return
    if args.command == 'bind-semantic-inputs':
        print(f'Bound {bind_extra_inputs()} additional current-runtime script inputs')
        return
    if 'freeze' in args.command:
        print(json.dumps(freeze_stage(images, pairs, args.command == 'verify-freeze'), indent=2))
        return
    if 'semantics' in args.command:
        v2 = semantic_stage(images)
        results = {'semantic-v2': v2, 'types-globals': type_global_stage(images), 'scripts': script_stage(),
                   'registration': registration_stage(images), 'preservation': preservation_stage(v2),
                   'intersections': intersection_stage(images, v2)}
        for name, value in sorted(results.items()):
            identity = write(OUT / (name + '.json'), value, args.command == 'verify-semantics')
            print(json.dumps({'artifact': identity, 'counts': value.get('counts')}, sort_keys=True), flush=True)
        verified_freeze()
        return
    if 'september' in args.command:
        result = secondary_stage()
        identity = write(OUT / 'september-pairs.json', result, args.command == 'verify-september')
        print(json.dumps({'aggregate': result['original_aggregate'], 'artifact': identity}, indent=2))
        return
    if 'candidates' in args.command:
        audit = read(OUT / 'trust-audit.json')
        require(audit['source_pins_sha256'] == old.sha256_file(ROOT / PINS), 'audit binding mismatch')
        result = candidate_stage(images, features, audit['records'], pairs)
        result['audit_sha256'] = old.sha256_file(ROOT / OUT / 'trust-audit.json')
        identity = write(OUT / 'reference-candidates.json', result, args.command == 'verify-candidates')
        print(json.dumps({'counts': result['counts'], 'artifact': identity}, indent=2))
        audit_paths()
        return
    rows = audit_pairs(images, features, pairs)
    counts = audit_counts(rows)
    artifact = envelope('audit', source_pins_sha256=old.sha256_file(ROOT / PINS), records=rows, counts=counts)
    identity = write(OUT / 'trust-audit.json', artifact, args.command == 'verify-audit')
    print(json.dumps({'counts': counts, 'artifact': identity}, indent=2))
    audit_paths()


if __name__ == '__main__':
    main()
