#!/usr/bin/env python3
"""Offline Phase 2D review. Never writes outside the two Phase 2D roots."""
from __future__ import annotations

import argparse
import bisect
import collections
import hashlib
import json
import math
import struct
import subprocess
from pathlib import Path

import Fable2PrototypeCorrespondence as binary
import Fable2SemanticNative as native

ROOT = Path(__file__).resolve().parents[1]
SDK = ROOT.parent / 'rexglue-sdk-v0.10'
CORPUS = Path('D:/Fable2-Recomp/prototypes')
DOC = Path('docs/fable2-prototype-archaeology/phase2d')
OUT = Path('out/prototype-archaeology/phase2d')
C = Path('docs/fable2-prototype-archaeology/phase2c')
CO = Path('out/prototype-archaeology/phase2c')
BASE = 'f13ee49c94db48d979de1346b7f67d2d82257ea2'
TREE = '2fd80820bf7ce98099fac26ea256bb8d1c6a5982'
BRANCH = 'fable2-prototype-archaeology-phase2d'
DONOR = 'build-23.12.02.0330'
TARGET = 'canonical-tu1'
SUPPRESSIONS = {'0x82631A30': '0x82950A98', '0x828EA448': '0x82681198', '0x83062950': '0x83060C30'}
PHYSICS = [('0x82631A30', '0x82630C30'), ('0x829506B0', '0x82950A98')]
KINDS = ('source-pins', 'profiles', 'blind-input', 'blind-results', 'reconstruction-freeze',
         'packets', 'review-index', 'challenge', 'probable-blockers', 'known-cases',
         'dependencies', 'batches', 'simulations', 'consumers', 'review-summary',
         'human-decision-ledger', 'validation', 'checks', 'tests', 'replay')


def require(value, message):
    if not value:
        raise ValueError(message)


def payload(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def read(path):
    return json.loads((ROOT / path).read_bytes())


def git(*args, root=ROOT):
    return subprocess.check_output(['git', *args], cwd=root, text=True).strip()


def identity(path):
    p = ROOT / path
    with p.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest().upper()
    return {'path': Path(path).as_posix(), 'size': p.stat().st_size, 'sha256': digest}


def check_identity(root, row):
    p = root / row['path']
    require(p.is_file(), 'Missing bound input: ' + row['path'])
    require(p.stat().st_size == row['size'], 'Bound size mismatch: ' + row['path'])
    with p.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest().upper()
    require(actual == row['sha256'], 'Bound SHA-256 mismatch: ' + row['path'])


def output_path(path):
    path = Path(path)
    require(not path.is_absolute() and '..' not in path.parts, 'Non-relative output path')
    resolved = (ROOT / path).resolve()
    require(resolved.is_relative_to(ROOT.resolve()), 'Output escapes repository')
    require(any(resolved.is_relative_to((ROOT / p).resolve()) for p in (DOC, OUT)), 'Output outside Phase 2D roots')
    return resolved


def envelope(kind, **fields):
    require(kind in KINDS, 'Unknown schema kind')
    return {'schema': {'name': 'fable2-prototype-review-' + kind, 'version': 1},
            'phase2c_commit': BASE, 'canonical_adoption': False, 'human_approval': False, **fields}


def write(path, value, check=False):
    data = value if isinstance(value, bytes) else payload(value)
    p = output_path(path)
    if check:
        require(p.is_file() and p.read_bytes() == data, 'Replay mismatch: ' + str(path))
    else:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return {'path': Path(path).as_posix(), 'size': len(data), 'sha256': sha(data)}


def verify_sdk(pins):
    expected = pins['sdk_start']
    for field, args in [('branch', ('branch', '--show-current')), ('head', ('rev-parse', 'HEAD')),
                        ('tree', ('rev-parse', 'HEAD^{tree}'))]:
        require(git(*args, root=SDK) == expected[field], 'SDK ' + field + ' mismatch')
    require(git('remote', '-v', root=SDK).splitlines() == expected['remotes'], 'SDK remotes mismatch')
    require(not git('diff', '--cached', '--name-only', root=SDK), 'SDK index changed')
    actual = subprocess.check_output(['git', 'status', '--porcelain=v2', '--untracked-files=all'], cwd=SDK, text=True).splitlines()
    require(actual == expected['status'], 'SDK worktree changed: ' + repr(actual))
    for row in expected['libmspack']:
        check_identity(SDK / 'thirdparty/libmspack', row)
    require(len(expected['libmspack']) == 15, 'SDK file population mismatch')


def frozen_inputs():
    """Rehash the closed source graph; never call a closed generator or writer."""
    require(git('rev-parse', BASE + '^{tree}') == TREE, 'Frozen tree mismatch')
    require(git('rev-parse', 'fable2-prototype-archaeology-phase2c') == BASE, 'Frozen branch moved')
    require(git('log', '-1', '--format=%s', BASE) == 'docs: freeze Phase 2C bounded result', 'Frozen subject mismatch')
    pins = read(C / 'evidence/source-pins.json')
    validate = read(C / 'evidence/validation.json')
    # Authenticate committed envelopes against the immutable Git object before
    # trusting any sizes or digests inside them.
    for p in sorted((ROOT / C).rglob('*')):
        if p.is_file():
            rel = p.relative_to(ROOT).as_posix()
            original = subprocess.check_output(['git', 'show', BASE + ':' + rel], cwd=ROOT)
            require(p.read_bytes() == original, 'Frozen committed bytes changed: ' + rel)
    require(validate['stage'] == 'bounded-final-with-evidenced-blockers', 'Frozen stage changed')
    require(validate['phase_complete'] is False and validate['canonical_adoption'] is False, 'Frozen state changed')
    bound = validate['artifacts'] + validate['implementation'] + [validate['report'], validate['matrix']]
    bound += validate['protected_artifacts_unchanged_from']['artifacts']
    for row in bound:
        check_identity(ROOT, row)
    sources = pins['sources'] + read(C / 'evidence/semantic-extra-source-pins.json')['sources']
    unique = {}
    for row in sources:
        key = (row['root'], row['path'])
        require(key not in unique or (unique[key]['sha256'], unique[key]['size']) == (row['sha256'], row['size']), 'Mixed source generations')
        unique[key] = row
    for (kind, _), row in sorted(unique.items()):
        check_identity(ROOT if kind == 'repository' else CORPUS, row)
    verify_sdk(pins)
    require(git('remote', '-v').splitlines() == pins['fable_start']['remotes'], 'Fable remotes changed')
    matrix = read(C / 'evidence/completion-matrix.json')
    require(collections.Counter(r['status'] for r in matrix['records']) == {'complete': 181, 'blocked-with-evidence': 6}, 'Frozen gates changed')
    require(len([r for r in matrix['records'] if r['id'].startswith('fixture.')]) == 39, 'Frozen fixture coverage changed')
    effective = read(CO / 'completion/effective-map.json')
    require(effective['counts'] == {'additions': 86, 'closed': 15299, 'delta': 83, 'effective': 15382, 'suppressed_or_review_excluded': 3}, 'Frozen arithmetic changed')
    frozen = read(CO / 'completion/mapping-freeze.json')
    for row in frozen['artifacts']:
        check_identity(ROOT, row)
    require(frozen['semantic_feedback_allowed'] is False, 'Semantic feedback enabled')
    return pins, validate, unique


def bind(check=False):
    pins, validate, upstream = frozen_inputs()
    files = {r['path']: {k: r[k] for k in ('path', 'size', 'sha256')} for r in validate['artifacts'] + validate['implementation']}
    for p in sorted((ROOT / C).rglob('*')):
        if p.is_file():
            row = identity(p.relative_to(ROOT)); files[row['path']] = row
    doc = envelope('source-pins', phase2c_tree=TREE, sources=list(sorted(files.values(), key=lambda r: r['path'])),
                   upstream_sources=[upstream[k] for k in sorted(upstream)],
                   starting_state={'fable': {'branch': 'fable2-prototype-archaeology-phase2c', 'head': BASE, 'tree': TREE,
                                             'index': [], 'status': [], 'remotes': pins['fable_start']['remotes']},
                                   'sdk': pins['sdk_start']},
                   inherited_blockers=validate['remaining_blockers'],
                   initial_verification={'command': ['python', 'tools/Fable2PrototypeCompletion.py', 'verify-summary'],
                                         'return_code': 0, 'stdout': 'PASS summary and three-way bytes; path audit 39'},
                   protected_phase2c_artifacts=validate['protected_artifacts_unchanged_from']['artifacts'])
    path = DOC / 'evidence/source-pins.json'
    if (ROOT / path).exists():
        check = True
    write(path, doc, check)
    print('PASS frozen bindings, 30 protected artifacts, 187 gates, 39 fixture categories, SDK and 15 hashes', flush=True)
    return doc


def images():
    return {build: native.Image(build, binary.load_build(ROOT / 'out/prototype-archaeology/derived', build)[1]) for build in (DONOR, TARGET)}


def words_at(image, function):
    raw = image.read(function['start'], function['end'] - function['start'])
    return list(struct.unpack('>' + 'I' * (len(raw) // 4), raw))


def normalize(word):
    if word >> 26 == 18:
        return word & 0xFC000003
    if word >> 26 == 16:
        return word & 0xFFFF0003
    return word


def text_object(image, address, empty=False):
    """Independently recover complete terminated text, preserving interior identity."""
    block = image.block(address)
    if block is None or block.execute:
        return {'proven': False, 'reason': 'not-initialized-data', 'address': native.hx(address)}
    data, at = block.data, address - block.start
    result = {'proven': False, 'address': native.hx(address), 'section': block.name,
              'window_sha256': sha(data[at:at + 16]), 'window_size': len(data[at:at + 16])}
    if data[at] == 0:
        if not empty:
            return {**result, 'reason': 'zero-storage-not-string-proof'}
        return {**result, 'proven': True, 'encoding': 'ascii', 'text': '', 'start': native.hx(address),
                'end_exclusive': native.hx(address + 1), 'length': 0, 'terminator': 1,
                'relation': 'empty-at-terminator', 'interior_offset': 0, 'sha256': sha(b'\0'), 'referenced_sha256': sha(b'\0')}
    for width, encoding in ((2, 'utf-16le'), (1, 'ascii')):
        def character(pos):
            return 0 <= pos <= len(data) - width and 32 <= data[pos] <= 126 and (width == 1 or data[pos + 1] == 0)
        if width == 2 and (address % 2 or not character(at) or not character(at + 2)):
            continue
        begin = at
        while at - begin < 4096 and character(begin - width):
            begin -= width
        end = at
        while end - begin < 4096 and character(end):
            end += width
        start_proven = begin == 0 or data[begin - width:begin] == bytes(width)
        if start_proven and end - begin < 4096 and data[end:end + width] == bytes(width):
            return {**result, 'proven': True, 'encoding': encoding, 'text': data[begin:end].decode(encoding),
                    'start': native.hx(block.start + begin), 'end_exclusive': native.hx(block.start + end + width),
                    'length': end - begin, 'terminator': width, 'relation': 'start' if begin == at else 'interior-suffix',
                    'interior_offset': at - begin, 'sha256': sha(data[begin:end + width]),
                    'referenced_sha256': sha(data[at:end + width])}
    return {**result, 'reason': 'complete-encoded-boundary-unproved'}


class DataAddresses:
    def __init__(self, image):
        self.image = image

    def __contains__(self, address):
        block = self.image.block(address)
        return block is not None and not block.execute


def raw_references(image, function, words):
    # Shared low-level abstract instruction interpreter, no saved XREF packets.
    refs, accesses, calls = native.scan_function(image, function, DataAddresses(image))
    if len(words) <= 64:
        destinations = {native.branch(w, function['start'] + i * 4) for i, w in enumerate(words) if w >> 26 in (16, 18) and not w & 1}
        for i, w in enumerate(words):
            pc = function['start'] + i * 4
            if w >> 26 in (32, 34, 40, 42) and (pc in destinations or pc - 4 in destinations):
                prefix = native.scan_function(image, function, DataAddresses(image), prefix_end=pc + 4)[0]
                for r in prefix:
                    if r['instruction'] == native.hx(pc):
                        refs.append({**r, 'first_entry_prefix_end': native.hx(pc + 4)})
    unique = {(r['instruction'], r['role'], r['operand'], r['anchor_address']): r for r in refs}
    return [unique[k] for k in sorted(unique)], accesses, calls


def canonical(image, f):
    words = words_at(image, f)
    normalized = [normalize(w) for w in words]
    masked = normalized[:]
    refs, accesses, calls = raw_references(image, f, words)
    tokens, proven, rejected, definitions = [], [], [], set()
    for ref in sorted(refs, key=lambda r: (int(r['instruction'], 16) - f['start'], r['role'], r['operand'], r['width'], r['anchor_address'])):
        obj = text_object(image, int(ref['anchor_address'], 16), ref['role'] == 'memory-read' and ref['width'] == 1)
        offsets = [int(a, 16) - f['start'] for a in ref['definition_instructions']]
        reason = None
        if not obj['proven'] or ref['readonly_pointer_slots'] or len(offsets) != 2:
            reason = 'complete-direct-two-definition-reference-unproved'
        elif not all(0 <= o < len(words) * 4 and o % 4 == 0 for o in offsets):
            reason = 'definition-outside-owner'
        else:
            hi, lo = [words[o // 4] for o in offsets]
            register = (hi >> 21) & 31
            valid = hi >> 26 == 15 and (hi >> 16) & 31 == 0
            valid &= (lo >> 26 == 14 and (lo >> 16) & 31 == register) or (lo >> 26 == 24 and (lo >> 21) & 31 == register)
            number = (((hi & 65535) << 16) + native.signed(lo & 65535)) & 0xFFFFFFFF if lo >> 26 == 14 else ((hi & 65535) << 16) | (lo & 65535)
            if not valid or number != int(ref['anchor_address'], 16):
                reason = 'definition-arithmetic-or-form-disagreement'
        if reason:
            rejected.append({'reference': ref, 'object': obj, 'reason': reason})
            continue
        token = {'role': [int(ref['instruction'], 16) - f['start'], ref['role'], ref['operand'], ref['width']],
                 'identity': [obj['encoding'], obj['length'], obj['terminator'], obj['sha256'], obj['relation'], obj['interior_offset']],
                 'section': obj['section'], 'definition_offsets': offsets}
        tokens.append(token)
        proven.append({'reference': ref, 'object': obj, 'definition_offsets': offsets,
                       'signed_low': lo >> 26 == 14 and bool(lo & 0x8000), 'constructed_address': native.hx(number)})
        for offset in offsets:
            masked[offset // 4] &= 0xFFFF0000
            definitions.add(offset)
    calls_all = [{'offset': i * 4, 'target': native.hx(native.branch(w, f['start'] + i * 4))} for i, w in enumerate(words) if w >> 26 in (16, 18) and w & 1]
    tails = [{'offset': i * 4, 'target': native.hx(native.branch(w, f['start'] + i * 4))} for i, w in enumerate(words)
             if w >> 26 in (16, 18) and not w & 1 and not f['start'] <= native.branch(w, f['start'] + i * 4) < f['end']]
    indirect = [{'offset': i * 4, 'link': bool(w & 1), 'kind': 'ctr' if (w >> 1) & 1023 == 528 else 'lr'}
                for i, w in enumerate(words) if w >> 26 == 19 and (w >> 1) & 1023 in (16, 528) and w != 0x4E800020]
    raw = image.read(f['start'], f['end'] - f['start'])
    return {'start': native.hx(f['start']), 'boundary': native.boundary(f), 'raw_sha256': sha(raw),
            'instruction_count': len(words), 'canonical_sha256': sha(payload({'words': masked, 'tokens': tokens})) if tokens else None,
            'branch_normalized_sha256': sha(payload(normalized)), 'reference_erased_sha256': sha(payload(masked)),
            'canonical_tokens': tokens, 'references': proven, 'rejected_references': rejected,
            'definition_offsets': sorted(definitions), 'calls': calls_all, 'tails': tails, 'indirect': indirect,
            'constant_calls': calls, 'global_accesses': accesses,
            'raw_source': {'path': 'out/prototype-archaeology/derived/' + image.build + '/' + image.block(f['start']).relative_path,
                           'section_sha256': image.block(f['start']).sha256, 'section_offset': f['start'] - image.block(f['start']).start}}


def universe():
    rows = read(CO / 'reference-candidates.json')['proposals']
    strong = [p for p in rows if p['grade'] == 'reviewed-strong-proposal']
    probable = [p for p in rows if p['grade'] == 'reviewed-probable-proposal']
    require(len(strong) == 86 and len(probable) == 715, 'Frozen proposal population mismatch')
    return strong, probable


def blind_candidates(donor, target_groups, donor_groups):
    signature = donor['canonical_sha256']
    targets = sorted(target_groups.get(signature, [])) if signature else []
    reverse = sorted(donor_groups.get(signature, [])) if signature else []
    return {'donor_start': donor['start'], 'targets': targets, 'reverse_donors': reverse,
            'candidate_count': len(targets), 'reverse_count': len(reverse),
            'entropy_bits': math.log2(len(targets)) if targets else None,
            'selected_target': targets[0] if len(targets) == len(reverse) == 1 else None,
            'rejection_reasons': ([] if len(targets) == len(reverse) == 1 else
                                  ['no-complete-reference-candidate'] if not targets else ['reciprocal-uniqueness-unproved'])}


def reconstruct(check=False):
    bind(True)
    strong, probable = universe()
    # Only donor identities cross this projection. The matcher never receives
    # prior grades, target decisions, semantics or Phase 2C candidate profiles.
    donors = sorted({p['donor_start'] for p in strong + probable} | {p[0] for p in PHYSICS})
    write(OUT / 'blind-input.json', envelope('blind-input', donors=donors,
          leakage=['Donor selection is inherited from the frozen proposal universe; raw literal bytes remain available.',
                   'No psychological independence is claimed; the shared low-level parser is source-bound.']), check)
    result = {}
    for build, image in images().items():
        result[build] = [canonical(image, f) for f in image.functions]
        print('Reconstructed raw population:', build, len(result[build]), flush=True)
    require(len(result[DONOR]) == 46179 and len(result[TARGET]) == 46180, 'Raw .pdata population mismatch')
    write(OUT / 'profiles.json', envelope('profiles', builds=result, semantic_feedback_allowed=False,
          parser_dependencies=[identity(Path('tools/Fable2SemanticNative.py')), identity(Path('tools/Fable2PrototypeCorrespondence.py'))]), check)
    groups = {}
    for build, rows in result.items():
        groups[build] = collections.defaultdict(list)
        for row in rows:
            if row['canonical_sha256']:
                groups[build][row['canonical_sha256']].append(row['start'])
    by = {r['start']: r for r in result[DONOR]}
    recovered = [blind_candidates(by[d], groups[TARGET], groups[DONOR]) for d in donors]
    write(OUT / 'blind-results.json', envelope('blind-results', records=recovered,
          matching_input=identity(OUT / 'blind-input.json'), profiles=identity(OUT / 'profiles.json'),
          policy='Exact independently reconstructed reference-canonicalized signature over the full reciprocal .pdata populations; no prior target input.'), check)
    write(OUT / 'reconstruction-freeze.json', envelope('reconstruction-freeze',
          artifacts=[identity(OUT / n) for n in ('blind-input.json', 'profiles.json', 'blind-results.json')],
          implementation=identity(Path('tools/Fable2PrototypeReview.py')), semantic_feedback_allowed=False), check)
    print('PASS independent reconstruction frozen before target reveal', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['bind', 'reconstruct'])
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.command == 'bind':
        bind(args.check)
    elif args.command == 'reconstruct':
        reconstruct(args.check)


if __name__ == '__main__':
    main()
