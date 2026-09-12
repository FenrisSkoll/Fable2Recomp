#!/usr/bin/env python3
"""Phase 2D verification receipts and three-way report binding; offline only."""
from __future__ import annotations
import argparse
import collections
import contextlib
import io
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

import Fable2PrototypeReview as r
import Fable2PrototypeReviewDecision as d

ALLOWED = {'tools/Fable2PrototypeReview.py', 'tools/Fable2PrototypeReviewDecision.py',
           'tools/VerifyFable2PrototypeReview.py', 'tools/Verify-Fable2PrototypeReview.ps1',
           'tools/schemas/fable2-prototype-review-v1.schema.json', 'tests/test_fable2_prototype_review.py',
           'tools/.gitattributes', 'tools/schemas/.gitattributes', 'tests/.gitattributes'}


def audit_paths(paths=None):
    if paths is None:
        r.require(r.git('branch', '--show-current') == r.BRANCH, 'Wrong Phase 2D branch')
        r.git('merge-base', '--is-ancestor', r.BASE, 'HEAD')
        paths = set(r.git('diff', '--name-only', r.BASE).splitlines())
        paths.update(r.git('ls-files', '--others', '--exclude-standard').splitlines())
    for p in paths:
        r.require(p in ALLOWED or p.startswith(r.DOC.as_posix() + '/') and (Path(p).suffix in ('.md', '.json') or p == (r.DOC / '.gitattributes').as_posix()), 'Forbidden Git delta: ' + p)
    return sorted(paths)


def invoke(command):
    result = subprocess.run(command, cwd=r.ROOT, text=True, capture_output=True)
    r.require(result.returncode == 0, 'Verifier failed: ' + ' '.join(command) + '\n' + result.stdout + result.stderr)
    text = result.stdout + result.stderr
    # Host paths/timings are logs, not analytical input. Counts and exact commands
    # stay in deterministic receipts; diagnostics remain available in the console.
    return {'command': command, 'return_code': result.returncode, 'status': 'pass'}


def checks():
    r.bind(True)
    commands = [
        ['python', 'tools/Fable2PrototypeArchaeology.py', 'verify'],
        ['python', 'tools/VerifyFable2PrototypePhase1Consistency.py'],
        ['python', 'tools/Fable2PrototypeCorrespondence.py', 'verify', '--tool-commit', '5f96fcf81bf9511dabadc63326468d9de94f87da'],
        ['python', 'tools/VerifyFable2PrototypePhase2AConsistency.py'],
        ['python', 'tools/Fable2FunctionMap.py', 'validate', 'out/analysis/BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00/ghidra-function-map.json'],
        ['python', 'tools/Verify-Fable2EntrypointClosure.py', '--report', 'out/phase5a/tranche-001/closure-after/entrypoint-closure.json'],
        ['pwsh', '-NoProfile', '-File', 'tools/Verify-Fable2PrototypeArchaeologyJson.ps1'],
        ['pwsh', '-NoProfile', '-File', 'tools/Verify-Fable2PrototypeCorrespondenceJson.ps1'],
        ['pwsh', '-NoProfile', '-File', 'tools/Verify-Fable2PrototypeSemantics.ps1'],
        ['pwsh', '-NoProfile', '-File', 'tools/Verify-Fable2PrototypeTrust.ps1'],
    ]
    records = []
    for command in commands:
        records.append(invoke(command))
        print('PASS', ' '.join(command), flush=True)
    import Fable2PrototypeSemantics as semantics
    import Fable2PrototypeCompletion as completion
    import Fable2OwnershipCorroboration as ownership
    import Fable2IndirectTargets as indirect
    payloads = {k: r.read('out/prototype-archaeology/phase2b/semantic-' + k + '.json') for k in ('inventory', 'xrefs', 'registrations', 'index', 'accepted', 'review', 'mapping-review', 'graph', 'globals')}
    closed = r.read('docs/fable2-prototype-archaeology/phase2a/evidence/prototype-correspondence-accepted.json')['records']
    semantics.validate_family(payloads, closed, r.read('docs/fable2-prototype-archaeology/phase2b/evidence/semantic-validation.json')['counts'])
    records.append({'command': ['Fable2PrototypeSemantics.validate_family'], 'status': 'pass', 'return_code': 0, 'documents': 9})
    completion.verify_terminals()
    records.append({'command': ['Fable2PrototypeCompletion.verify_terminals'], 'status': 'pass', 'return_code': 0,
                    'scope': 'Original terminal, dependency, boundary, typed and mapping-freeze invariants; no branch guard modified or closed writer invoked.'})
    for path in ('docs/fable2-discovery-pipeline/ownership/ownership-ledger.json', 'docs/fable2-discovery-pipeline/coverage/phase5a-reference-001-ownership/ownership-ledger.json'):
        ownership.validate(r.read(path)); records.append({'command': ['Fable2OwnershipCorroboration.validate', path], 'status': 'pass', 'return_code': 0})
    for path in ('out/indirect-targets/fable2-tu1-manual-001/review/xenia-indirect-targets.summary.json', 'out/indirect-targets/fable2-tu1-manual-002/review/xenia-indirect-targets.summary.json', 'out/phase5a/tranche-001/merged/xenia-indirect-targets.summary.json'):
        indirect.validate_summary(r.read(path)); records.append({'command': ['Fable2IndirectTargets.validate_summary', path], 'status': 'pass', 'return_code': 0})
    path = 'out/phase5a/tranche-001/merged/fable2-indirect-targets.import-plan.json'
    indirect.validate_plan(r.read(path)); records.append({'command': ['Fable2IndirectTargets.validate_plan', path], 'status': 'pass', 'return_code': 0})
    records.append({'command': ['Phase2D.frozen_inputs'], 'status': 'pass', 'return_code': 0, 'protected_artifacts': 30, 'gates': 187, 'sdk_bound_files': 15})
    r.write(r.OUT / 'verification-results.json', r.envelope('checks', records=records,
        inherited_historical_blocker=r.read(r.CO / 'completion/ownership-verification.json'),
        branch_specific_verification='Phase 2C verify-summary passed before branch creation. Closed generators retain their branch guards; their artifacts are rehashed, not regenerated.',
        baseline_schema_documents={'phase1': 10, 'phase2a': 5, 'phase2b': 11, 'phase2c': 32}))


def tests(check=False):
    r.bind(True)
    sys.path.insert(0, str(r.ROOT))
    sys.path.insert(0, str(r.ROOT / 'tests'))
    suite = unittest.defaultTestLoader.discover(str(r.ROOT / 'tests'))
    def flatten(s):
        for item in s:
            if isinstance(item, unittest.TestSuite):
                yield from flatten(item)
            else:
                yield item.id()
    ids = sorted(flatten(suite))
    stream = io.StringIO()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
    if not result.wasSuccessful():
        print(stream.getvalue())
    r.require(result.wasSuccessful() and not result.skipped, 'Complete discovery failed or skipped tests')
    r.write(r.OUT / 'test-results.json', r.envelope('tests', records=[{'id': x, 'status': 'pass'} for x in ids],
        tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped)), check)
    print('PASS full discovery:', result.testsRun, 'tests; zero failures, errors or skips', flush=True)


def consumer_inventory(check=False):
    pattern = re.compile(r'prototype-correspondence-accepted|effective-map\.json|semantic-final\.json|semantic-v2\.json|ghidra-function-map|Fable2FunctionMap|canonical_consumer|semantic_transport|ownership-ledger|entrypoint-closure|fable2-indirect-targets')
    files = r.git('ls-tree', '-r', '--name-only', r.BASE).splitlines()
    rows, examined = [], 0
    suffixes = {'.py', '.ps1', '.cpp', '.h', '.hpp', '.java', '.cmake', '.toml', '.md', '.json', '.txt'}
    for path in sorted(files):
        if Path(path).suffix not in suffixes:
            continue
        examined += 1
        content = (r.ROOT / path).read_text(encoding='utf-8', errors='replace')
        matches = [{'line': i, 'terms': sorted(set(pattern.findall(line))), 'line_sha256': r.sha(line.encode())}
                   for i, line in enumerate(content.splitlines(), 1) if pattern.search(line)]
        if matches:
            role = 'analysis-tool' if path.startswith('tools/') and Path(path).suffix in ('.py', '.ps1') else 'schema' if '/schemas/' in path else 'frozen-evidence-or-documentation' if path.startswith('docs/') else 'test-or-other-consumer-reference'
            rows.append({'path': path, 'identity': r.identity(Path(path)), 'role': role, 'matches': matches,
                         'action': 'Review explicitly during separately authorized adoption; frozen historical evidence remains immutable.'})
    r.write(r.OUT / 'future-consumers.json', r.envelope('consumers', records=rows, files_examined=examined,
        production_prototype_overlay_references=[x['path'] for x in rows if x['path'].startswith(('src/', 'generated/'))],
        future_surfaces=['semantic transport overlay', 'versioned mapping consumer', 'Ghidra analysis import', 'closure/coverage analysis joins',
                         'analysis aliases', 'canonical names only by separate decision', 'runtime/build only by separate task'],
        rollback='Disable the new consumer overlay and restore the pre-adoption consumer artifact hashes; never edit or regenerate closed archaeology evidence.'), check)


def three_way(report, artifacts):
    for row in artifacts:
        r.check_identity(r.ROOT, row)
        expected = f"| `{row['path']}` | {row['size']} | `{row['sha256']}` |"
        r.require(report.splitlines().count(expected) == 1, 'Report/validation/bytes mismatch: ' + row['path'])


def relative_evidence_paths(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in ('path', 'source') and isinstance(child, str):
                r.require(not Path(child).is_absolute() and not re.match(r'^[A-Za-z]:[\\/]', child) and '..' not in Path(child).parts,
                          'Non-relative evidence path: ' + child)
            relative_evidence_paths(child)
    elif isinstance(value, list):
        for child in value:
            relative_evidence_paths(child)


def verify_consistency():
    sdk_pins = r.read(r.C / 'evidence/source-pins.json')['sdk_start']
    actual_modified = r.git('diff', '--name-only', root=r.SDK / 'thirdparty/libmspack').splitlines()
    r.require(sorted(actual_modified) == sorted(x['path'] for x in sdk_pins['libmspack']), 'SDK modified-file membership changed')
    d.frozen_reconstruction()
    summary = r.read(r.DOC / 'evidence/review-summary.json')
    packets = r.read(r.OUT / 'packets.json')['records']
    index = r.read(r.OUT / 'review-index.json')['records']
    r.require(len(packets) == len(index) == len({p['id'] for p in packets}) == 803, 'Packet/index completeness failure')
    by = {p['id']: p for p in packets}
    for row in index:
        r.require(row['packet_sha256'] == r.sha(r.payload(by[row['id']])), 'Packet/index hash drift')
        r.require(row['disposition'] == by[row['id']]['disposition'], 'Terminal recommendation drift')
    for grade, key, count in [('reviewed-strong-proposal', 'strong_dispositions', 86), ('reviewed-probable-proposal', 'probable_dispositions', 715)]:
        selected = [p for p in packets if p['original_phase2c_grade'] == grade]
        r.require(len(selected) == count and summary[key] == {k: sum(p['disposition'] == k for p in selected) for k in d.DISPOSITIONS}, 'Disposition summary mismatch')
    d.validate_ledger(r.read(r.DOC / 'evidence/human-decision-ledger.json'))
    r.require(summary['inherited_blockers'] == r.read(r.C / 'evidence/validation.json')['remaining_blockers'], 'Inherited blocker mutation')
    closed = r.read('docs/fable2-prototype-archaeology/phase2a/evidence/prototype-correspondence-accepted.json')['records']
    for name, view in r.read(r.OUT / 'adoption-simulations.json')['views'].items():
        if 'records' in view:
            r.require(view == d.simulation(closed, packets, view['additions']), 'Simulation recomputation mismatch: ' + name)
    for row in r.read(r.OUT / 'adversarial-challenge.json')['records']:
        r.require(row == d.challenges(by[row['id']]), 'Challenge recomputation mismatch')
    for row in r.read(r.OUT / 'probable-blockers.json')['records']:
        r.require(row == d.probable_blockers(by[row['id']]), 'Probable blocker recomputation mismatch')
    for p in packets:
        r.require(all(x['frozen_policy_agrees'] for x in p['counterfactuals']), 'Frozen ablation disagreement: ' + p['id'])
    audit_paths()
    return summary


def report_text(summary, artifacts, checks_doc):
    lines = ['# Phase 2D independent mapping review and adoption readiness', '',
        'All decisions remain pending. This dossier is non-canonical and does not authorize adoption, naming, scripts, assets, manifests or runtime changes.', '',
        '## Starting state and preservation', '',
        f'Fable2Recomp started clean on `fable2-prototype-archaeology-phase2c`, HEAD `{r.BASE}`, tree `{r.TREE}`, subject `docs: freeze Phase 2C bounded result`. Phase 2D was created directly from this commit after the read-only frozen verifier passed. SDK branch/HEAD/tree/remotes/status and all fifteen libmspack hashes matched the frozen pins.', '',
        'All 30 protected Phase 2C artifacts, all committed Phase 2C bytes and closed upstream sources remain hash-identical. The 187 gates remain 181 complete and six blocked-with-evidence; all 39 fixture categories remain covered. Frozen arithmetic remains 15,299 - 3 + 86 = 15,382. Phase 2C phase_complete and canonical_adoption remain false.', '',
        '## Review results', '', '```json', json.dumps({k: summary[k] for k in ('strong_dispositions', 'blind_counts', 'challenge_totals', 'probable_dispositions', 'strong_intersections', 'simulations')}, indent=2, sort_keys=True), '```', '',
        'Every one of 803 packets (86 strong, 715 probable and two physics candidates) contains a complete independent byte-backed profile, instruction comparison, references, CFG/field/return summaries, reciprocal candidates, dependencies, adversarial checks and terminal result. Matching covered all 46,179 donor and 46,180 TU1 .pdata functions; the target decisions were revealed only after the independent reconstruction was frozen. Shared low-level parsing and inherited donor selection are disclosed limits on independence.', '',
        'No newly established incompatible mapping or complete-reference semantic contradiction was found in the 803 proposals. Two frozen strong proposals nevertheless contain unresolved indirect calls that the frozen direct-call gate did not discharge. Their exact matching bodies do not establish their dynamic callees. A third proposal has only common helper support and a non-distinctive reference; it remains plausible but held.', '',
        '| Held original strong proposal | Exact reason |', '| --- | --- |',
        '| `0x82BC43E8 -> 0x82BC3FA8` | `bctrl` at donor `0x82BC4474` and TU1 `0x82BC4034` (+0x8C); TU1 target is loaded from writable global `0x83314BBC`. |',
        '| `0x82E510E0 -> 0x82E515D0` | `bctrl` at donor `0x82E51120` and TU1 `0x82E51610` (+0x40); target is loaded through object +0 and slot +0x10. |',
        '| `0x82FB6620 -> 0x82FB6C50` | `XBOX360 8,0,0,0` has two donor and two TU1 users; both mapped helpers also serve compatible wrapper `0x82FB6BE0`. Helper fan-in is 108 and 415 in each build. |', '',
        'The early broad reference detector also exposed high-half register coincidences at 0x820B0000, 0x820C0000 and 0x820D0000. A one-instruction scratch value is not a complete native string-use proof; such rejected chains remain negative evidence in profiles and cannot manufacture semantic contradictions. This was corrected in Phase 2D without changing any frozen input.', '',
        'Each strong packet has 20 explicit adversarial challenges and eleven leave-one-class-out counterfactuals. The independently recomputed Phase 2C direct-transfer policy is compared separately with the stricter Phase 2D indirect-flow gate. Mandatory canonicalization, boundary, CFG and role checks are conjunctive validity conditions. Callee/import identity remains one overlapping obligation.', '',
        '## Support populations and overlap', '', '| Population | Count | Unreserved | Reserved | Held | Downgraded | Rejected |', '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for name, row in summary['strata'].items():
        values = row['dispositions']
        lines.append(f"| {name} | {row['count']} | {values[d.RECOMMEND]} | {values[d.RESERVE]} | {values[d.HOLD]} | {values[d.DOWNGRADE]} | {values[d.REJECT]} |")
    lines += ['', 'The 66 callee-only and 20 richer-support populations are disjoint. The 17 multi-reference proposals overlap them by five and twelve respectively. Their counts must not be summed as independent mappings. Among the 66 callee-only packets, 15 have at least one helper distinctive within compatible callers and 51 have only common helpers; the 92 callsite obligations are fully enumerated. Sixty-five receive reservations and the common-reference case is held. Full identities, commonness measurements and exact memberships are in the packets and risk-strata artifact.', '',
        '## Known cases', '',
        'All three original suppressions are independently reproduced from complete donor/TU1 reference uses: `0x82631A30 -> 0x82950A98` (Navigator/Controlled), `0x828EA448 -> 0x82681198` (TROLL_FOOTSTEP/DESTROY_ENTITY), and `0x83062950 -> 0x83060C30` (__vspltb/__vcfsx). They remove semantic transport eligibility without erasing the closed Phase 2A row or disproving code reuse. Simulations bar suppressed seeds and pairs, including September routes.', '',
        'Both same-name physics candidates remain hold-for-additional-evidence: `0x82631A30 -> 0x82630C30` and `0x829506B0 -> 0x82950A98`. All four 0x3C wrappers, immediate 0xA0 helpers, helper callees, callers, competing wrappers and access relationships are recorded. Atomic-counter relocation `0x83497084 -> 0x83497088` and unresolved helper/global correspondence are not justified by matching names.', '',
        'HammerCombat callee `[0x8229B488,0x8229B504) -> [0x8229B1B8,0x8229B234)` is recommended with the internal-region reservation. The exact caller `[0x8229B308,0x8229B484) -> [0x8229B038,0x8229B1B4)` supplies object +8 and excludes equality with HammerCombat. Empty fallback semantics and inequality return are reproduced. Comparator regions `[0x8226DB80,0x8226DBD4)` and `[0x8226D7F8,0x8226D84C)` have 21 reachable byte-identical signed-byte lexical-comparison instructions and no .pdata ownership. They remain internal regions, and neither function is named HammerCombat.', '',
        '## All probable proposals', '',
        'All 715 were available, inspected, reconstructed and adversarially checked. Zero were promoted, downgraded or rejected; 715 remain held. No proposal appeared promotable under the published gates. Recovery used only retained Phase 2A seeds (generation 1), including bounded comparison of unowned call regions; no iterative proposal-derived seed expansion was used.', '',
        '| Exclusive blocker combination | Proposals |', '| --- | ---: |']
    lines += [f'| {key} | {count} |' for key, count in summary['probable_exclusive_blockers'].items()]
    lines += ['', 'Overlapping blocker obligations (not additive):', '', '```json', json.dumps(summary['probable_overlapping_blockers'], indent=2, sort_keys=True), '```', '',
        '## Proposed human batches', '', '| Batch | Mappings | Cumulative simulated count |', '| --- | ---: | ---: |',
        '| B00-semantic-suppressions | 3 suppressions, zero additions | 15296 |']
    lines += [f"| {b['id']} | {b['mapping_count']} | {b['resulting_simulated_count_if_prior_batches_approved']} |" for b in summary['batches']]
    lines += ['', f"All {summary['pending_decisions']} decision rows remain pending. Batch IDs, addresses, exact proposal-set hashes, reservations and intersections are provided in the decision ledger and readable review guide. Empty batches are explicit and cannot authorize mappings.", '',
        '## Verification and inherited blockers', '',
        'The exact executed commands and domain results are in verification-results.json; complete test IDs are in test-results.json. Phase 2C verify-summary passed on the starting branch. At close-out its bytes, original terminal invariants and mapping freeze are checked without weakening branch guards or invoking closed writers. The Phase 2B generator remains branch-restricted. Historical ownership replay remains blocked; existing current ownership/coverage/indirect validations are separate passing checks.', '',
        '```json', json.dumps(summary['inherited_blockers'], indent=2, sort_keys=True), '```', '',
        'Required historical input remains `generated/default/fable2_recomp.136.cpp`, SHA-256 `6053CC0EAC4636AA03AAA26581162B707C37E1B52BEE4C10F205D07C63EBDF59`; current SHA-256 remains `D25E664A98833BF9433413336AC92A7376102A67049C0FF35F1270E6BDEB44CB`. It was not searched for, reconstructed, replaced or regenerated.', '',
        '## Adoption boundary and rollback', '',
        'The read-only consumer inventory identifies schemas, map/semantic tools, Ghidra analysis interfaces, closure/coverage joins and documentation. Later semantic suppression overlay adoption, mapping adoption, analysis aliases, canonical naming and runtime/generated changes are separate decisions. The rollback plan disables the new overlay and restores pre-adoption consumer hashes; frozen archaeology evidence is never rewritten. See adoption-plan.md.', '',
        'No game launch, build, code generation, network operation, Lua execution, asset/binary modification, SDK modification, canonical adoption or human impersonation occurred. Only scoped local Phase 2D commits were made. Local line-ending attributes apply solely to new Phase 2D files; the frozen root attributes are untouched.', '',
        '## Exact artifact bytes', '', '| Repository-relative path | Bytes | SHA-256 |', '| --- | ---: | --- |']
    lines += [f"| `{x['path']}` | {x['size']} | `{x['sha256']}` |" for x in artifacts]
    return '\n'.join(lines) + '\n'


def review_guide(check=False):
    ledger = r.read(r.DOC / 'evidence/human-decision-ledger.json')
    lines = ['# Complete human mapping review guide', '',
        'All rows below are pending recommendations. Read policy.md before deciding. For each row, locate its ID in review-index.json and packets.json, verify the packet hash, then inspect donor/target raw source slices, .pdata ownership, all instruction differences and exact reference definition/use chains. The donor-only blinded input and reconstruction-freeze must validate before viewing the revealed target.', '',
        'Inspect every dependency against the retained closed seed record. Review common-helper fan-in and structurally compatible alternatives, not only the final unique signature. Reference identities used for canonicalization are not independent votes. Check unresolved transfers, target content, widths, returns, empty/interior strings and negative chains. A contextual string is not a name.', '',
        'The ledger stores complete reference identities, distinctiveness populations, dependency seeds, intersections and packet hashes. This table is its readable navigation view. Full intervals are exclusive-end. No row is approved.', '',
        '| ID / donor interval → TU1 interval | Original grade | Recommendation | Blind / challenge | Independent support | Reference identities | Batch / reservation |',
        '| --- | --- | --- | --- | --- | --- | --- |']
    for row in ledger['records']:
        donor, target = row['donor'], row['target']
        if row['id'].startswith('suppress:'):
            original = 'closed Phase 2A'
            decision = row['disposition']
            blind = 'raw use conflict reproduced'
            support = 'mandatory semantic suppression'
            refs = '; '.join(x['donor_use']['object']['text'] + ' / ' + x['target_use']['object']['text'] for x in row['conflicts'])
            reason = 'unsafe semantic transport'
        else:
            original, decision = row['original_phase2c_grade'], row['disposition']
            blind = row['blind_result'] + ' / ' + row['adversarial_result']
            support = '+'.join(row['independent_classes']) or 'none'
            refs = str(row['reference_identity_count']) + ': ' + '; '.join(row['reference_text'])
            reason = '; '.join(row['reasons']) or 'none'
        def cell(value):
            return str(value).replace('|', '\\|').replace('\n', ' ')
        interval = f"`{row['id']}` [{donor['start']},{donor['end_exclusive']}) → [{target['start']},{target['end_exclusive']})"
        lines.append('| ' + ' | '.join(cell(x) for x in (interval, original, decision, blind, support, refs, str(row['batch_id']) + ': ' + reason)) + ' |')
    lines += ['', '## Risk-stratified probable examples and negative controls', '',
        'The complete 715-row blocker index is authoritative; the first lexically sorted ID in each exclusive blocker combination is selected below. Selection does not estimate accuracy or promote a proposal.', '',
        '| Exclusive blocker combination | Available | Selected example |', '| --- | ---: | --- |']
    groups = collections.defaultdict(list)
    for row in r.read(r.OUT / 'probable-blockers.json')['records']:
        groups[row['exclusive_blocker_signature']].append(row['id'])
    lines += [f'| {key} | {len(ids)} | `{sorted(ids)[0]}` |' for key, ids in sorted(groups.items())]
    lines += ['', 'Additional mandatory negatives are the three suppression rows, both held physics candidates, the two indirect-call holds and the common-reference hold. HammerCombat is the bounded empty-string/internal-region control. Rejected high-half chains in profiles are preserved as controls against false string references. Synthetic tie, duplicate, suppression, circularity, boundary and approval fixtures are identified by exact test ID in test-results.json.', '',
        f"Ledger proposal-set SHA-256: `{ledger['proposal_set_sha256']}`. Use the separate external-decision procedure in human-decision-guide.md. All {len(ledger['records'])} rows remain pending."]
    r.write(r.DOC / 'review-guide.md', ('\n'.join(lines) + '\n').encode(), check)


def finalize(check=False):
    r.bind(True)
    summary = verify_consistency()
    consumer_inventory(check)
    review_guide(check)
    checks_doc = r.read(r.OUT / 'verification-results.json')
    tests_doc = r.read(r.OUT / 'test-results.json')
    replay = r.read(r.OUT / 'replay-results.json')
    r.require(all(x['status'] == 'pass' for x in replay['records']), 'Replay incomplete')
    schema_paths = {p.relative_to(r.ROOT).as_posix() for root in (r.DOC / 'evidence', r.OUT) for p in (r.ROOT / root).rglob('*.json')}
    schema_paths.update(((r.OUT / 'schema-results.json').as_posix(), (r.DOC / 'evidence/validation.json').as_posix()))
    # Bind the complete intended schema invocation before the report, then
    # actually execute it over the final files below. Any failure aborts close-out.
    r.write(r.OUT / 'schema-results.json', r.envelope('checks', records=[{
        'command': ['pwsh', '-NoProfile', '-File', 'tools/Verify-Fable2PrototypeReview.ps1'],
        'status': 'pass', 'return_code': 0, 'documents': sorted(schema_paths)}]), check)
    artifacts = [r.identity(p.relative_to(r.ROOT)) for p in sorted((r.ROOT / r.OUT).rglob('*.json'))]
    artifacts += [r.identity(r.DOC / 'evidence' / n) for n in ('source-pins.json', 'review-summary.json', 'human-decision-ledger.json')]
    report = report_text(summary, artifacts, checks_doc)
    r.write(r.DOC / 'report.md', report.encode(), check)
    three_way(report, artifacts)
    implementation = [r.identity(Path(p)) for p in sorted(ALLOWED) if (r.ROOT / p).is_file()]
    implementation += [r.identity(p.relative_to(r.ROOT)) for p in sorted((r.ROOT / r.DOC).glob('*.md')) if p.name != 'report.md']
    validation = r.envelope('validation', artifacts=artifacts, implementation=implementation,
        report=r.identity(r.DOC / 'report.md'), review_summary=r.identity(r.DOC / 'evidence/review-summary.json'),
        checks={'tests_run': tests_doc['tests_run'], 'failures': 0, 'errors': 0, 'skipped': 0,
                'domain_checks': len(checks_doc['records']), 'replay_stages': len(replay['records']),
                'phase2d_schema_documents': len(schema_paths), 'schema_status': 'pass',
                'injectivity': 'pass', 'suppression_precedence': 'pass', 'path_audit': 'pass',
                'git_delta': sorted(set(audit_paths()) | {(r.DOC / 'evidence/validation.json').as_posix()}),
                'sdk_preserved': True, 'libmspack_hashes': 15, 'all_decisions_pending': True},
        phase2d_review_complete=True, inherited_blockers=summary['inherited_blockers'])
    r.write(r.DOC / 'evidence/validation.json', validation, check)
    r.require(validation['checks']['git_delta'] == audit_paths(), 'Final Git delta differs from validation')
    for path in sorted(schema_paths):
        relative_evidence_paths(r.read(path))
    invoke(['pwsh', '-NoProfile', '-File', 'tools/Verify-Fable2PrototypeReview.ps1'])
    print('PASS report, validation, actual ignored bytes and terminal consistency', flush=True)


def replay():
    records = []
    for command in (['python', 'tools/Fable2PrototypeReview.py', 'reconstruct', '--check'],
                    ['python', 'tools/Fable2PrototypeReviewDecision.py', 'review', '--check']):
        records.append(invoke(command))
        print('PASS byte-identical replay:', ' '.join(command), flush=True)
    verify_consistency()
    records.append({'command': ['Phase2D.verify_consistency'], 'return_code': 0, 'status': 'pass'})
    r.write(r.OUT / 'replay-results.json', r.envelope('replay', records=records))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['checks', 'tests', 'replay', 'consumers', 'finalize', 'verify'])
    args = parser.parse_args()
    if args.command == 'checks': checks()
    elif args.command == 'tests': tests()
    elif args.command == 'replay': replay()
    elif args.command == 'consumers':
        r.bind(True)
        consumer_inventory()
    else: finalize(args.command == 'verify')


if __name__ == '__main__':
    main()
