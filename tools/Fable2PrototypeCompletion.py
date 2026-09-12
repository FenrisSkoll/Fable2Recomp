#!/usr/bin/env python3
"""Complete the existing Phase 2C static evidence layer; no production adoption."""
from __future__ import annotations
import argparse
import collections
import itertools
import json
import re
import struct
import copy
import inspect
import io
import subprocess
import ast
import unittest
import contextlib
import sys
from types import SimpleNamespace
from pathlib import Path
import Fable2PrototypeTrust as t

CHECKPOINT = 'e784beeab1a372cc3f71e2cd1af2dfa18b58f321'
OUT = t.OUT / 'completion'
SCHEMA = 'tools/schemas/fable2-prototype-completion-v1.schema.json'

FIXTURES = '''Navigator/Controlled collision
Shared first sixteen bytes
Same address different full strings
Relocated identical full string
Interior and suffix pointers
UTF16LE ASCII boundaries terminators
Zero padding common headers
Unbounded non-string objects
Partial-data-only loss of trust
Independent topology/neighbourhood retention
Signed-low address carry
Proven definition/consumption scope
Unrelated immediate significance
String evidence double counting
Circular same-generation support
Deterministic multigeneration expansion
Reciprocal crossed-wrapper injectivity
Contradictory literal roles
HammerCombat empty relocation and caller use
Unowned identical comparator regions
Overlay suppression precedence
Duplicate conflicting overlays
Community-only nonacceptance
Registration positive and adversarial layouts
Deterministic review availability
Report summary ignored-byte consistency
Forbidden canonical propagation
September aggregate reconciliation
Non-oracular two-hop routing
Split merge outline inline thunk tail internal regions
Shifted boundaries and both unmatched donors
Vtable discrimination
Type strings insufficient for constructor names
Same-address incompatible globals
Scripts/scripts_r structure and debug metadata
Separate game GUI startup provenance
Community-only free camera spelling
Preservation presence and dependencies
Mapping freeze prevents semantic feedback'''.splitlines()

REQUIREMENTS = {
 'A': 'all-15299-dispositions|all-97-data-anchors|original-status-provenance|full-object-boundaries-encoding|same-address-prefix-interior-padding|role-contradictions|feature-ablation-counterfactuals|exact-totals',
 'B': 'versioned-policy|no-address-or-prefix-identity|nonstring-object-proof|wrapper-disambiguation|suppression-not-lineage-disproof|distinct-dispositions',
 'C': 'four-physics-wrapper-bounds|instruction-differences|literal-argument-role|immediate-callees|reciprocal-competitors|global-assignment|same-name-dispositions',
 'D': 'exact-caller|callee-0x7C|empty-strings|reachable-comparators|object-offset8-return-use|proposal-gates|context-not-name',
 'E': 'full-21350-review-population|typed-reference-canonicalization|preserve-unrelated-bits|independent-evidence|no-double-counting|generation-dependencies|no-circularity|reciprocity-injectivity|feature-combinations|subsystem-problem-priority|negative-terminal-counts|broader-supported-features',
 'F': 'closed-minus-suppressions-plus-reviewed-additions|original-identities|conflicts-cycles|noncanonical-consumer|exact-delta|adoption-plan',
 'G': 'bounded-native-selection|real-disassembly|failure-explanation|structure-before-recognizer|positive-negative-fixtures|first-party-freecamera',
 'H': '9600-pair-materialization|complete-original-aggregate|45707-terminals|hardened-trust|two-hop-dependencies|no-oracle-or-July-vote',
 'I': '713-primary-population|33-September-boundaries|both-unmatched|strong-probable-boundary-disagreement|entry-exit-ownership|all-transformation-classes|no-invented-functions',
 'J': 'frozen-mapping-before-semantic|51657-terminal-reconciliation|independent-TU1-check|changed-status-reasons|no-feedback|role-name-separation',
 'K': '425-type-contexts|4939-pointer-runs|2479-global-contexts|terminal-object-dispositions|bounds-alignment-slots|writers-readers|constructor-alternatives|cross-build-slots|false-positive-controls',
 'L': '160-file-inventory|108-loose-chunks|54-pair-reconciliation|script-bank-parser-or-blocker|game-GUI-startup-states|debug-info-vs-identity|no-Lua-execution|retail-provenance',
 'M': '206-shapes|2662-calls|2647-name-callback-candidates|per-layout-terminal-obligations|complete-chain-or-blocker|recognizer-fixtures',
 'N': '200-preservation-records|prototype-retail-presence|dependency-evidence|portability-grade|freecamera-E3-demo|no-runnable-claims',
 'O': 'closure|coverage|indirect|ownership|historical-crashes|renderer|Ghidra-manifest|exact-paths-pointers|priority-only',
 'safety': 'exact-checkpoint|SDK-fifteen-hashes|closed-phases-immutable|no-network|no-runtime-build-codegen|local-commits-only|relative-paths|output-root-guards|allowlisted-Git-delta|clean-ending-tree',
 'validation': 'schema-every-artifact|full-test-discovery|all39-fixture-categories|full-deterministic-replay|three-way-hash-consistency|baseline-bound-ownership|all-existing-verifiers|complete-matrix',
 'outputs': 'source-pins|trust-audit|ablation|proposal-packets|effective-map|candidate-index|known-cases|registration|semantic-v2|review-all-strong|September|boundaries|types-globals|scripts|preservation|validation|README|report|policy|review-guide|handoff',
}

def env(kind, **fields):
    return {'schema':{'name':'fable2-prototype-completion-'+kind,'version':1},
            'checkpoint_commit':CHECKPOINT,'canonical_adoption':False,**fields}

def write(path, obj, check=False):
    return t.write(path,obj,check)

def matrix_initial():
    rows=[]
    for group,names in REQUIREMENTS.items():
        for name in names.split('|'):
            rows.append({'id':group+'.'+name,'requirement':name,'mandatory':True,
                         'status':'incomplete','code':[],'evidence':[],'schema':SCHEMA,
                         'tests':[],'verifiers':[],'report_section':'Completion gates',
                         'reason':'Completion-pass evidence binding and validation pending.'})
    assert len(FIXTURES)==39
    for i,name in enumerate(FIXTURES,1):
        rows.append({'id':f'fixture.{i:02d}','requirement':name,'mandatory':True,
                     'status':'incomplete','code':[],'evidence':[],'schema':SCHEMA,
                     'tests':[],'verifiers':[],'report_section':'Fixture coverage',
                     'reason':'Exact positive/adversarial fixture binding pending; aggregate test count is insufficient.'})
    doc=env('matrix',stage='initial',records=rows,counts={'incomplete':len(rows)},phase_complete=False)
    write(t.DOC/'evidence/completion-matrix.json',doc)
    text=['# Phase 2C completion matrix','','Initial dependency checklist. Every row requires implementation, evidence, schema and validation bindings before closure.','',
          '| Gate | Requirement | Status |','| --- | --- | --- |']
    text += [f"| {r['id']} | {r['requirement']} | {r['status']} |" for r in rows]
    write(t.DOC/'completion-matrix.md',('\n'.join(text)+'\n').encode())
    print(json.dumps(doc['counts']))

CLASSES = ('string-data-canonicalization','caller','callee','neighbourhood-order',
           'cfg-branch','boundary-size','import-helper-call','field-parameter-return-role',
           'September-two-hop','boundary-code-region','same-generation-derived')
SUPPORT_CLASS = {'trusted-mapped-caller':'caller','trusted-mapped-callee':'callee',
                 'trusted-two-sided-exact-delta-neighbourhood':'neighbourhood-order'}

def profile_function(image, f, refs):
    canonical=t.canonicalize(image,f,refs)
    words=[w[0] for w in struct.iter_unpack('>I',image.read(f['start'],f['end']-f['start']))]
    normalized=[t.old.normalize_branch_word(w) for w in words]
    masked=list(normalized)
    for change in canonical['changed_instructions']:
        masked[change['offset']//4] &= 0xFFFF0000
    tokens=canonical['canonicalized_references']
    no_roles=[{k:v for k,v in r.items() if k!='role'} for r in tokens]
    return {'start':t.native.hx(f['start']),'boundary':t.native.boundary(f),
            'baseline':canonical['fingerprint'] if tokens else None,
            'string-data-canonicalization':t.digest(t.payload(normalized)),
            'field-parameter-return-role':t.digest(t.payload({'words':masked,'tokens':no_roles})) if tokens else None,
            'cfg-branch':t.digest(t.payload({'words':[w for w in masked if w>>26 not in (16,18,19)],'tokens':tokens})) if tokens else None,
            'canonical':canonical,'raw_sha256':t.digest(image.read(f['start'],f['end']-f['start']))}

def profiles(images, check=False):
    source=t.old.sha256_file(t.ROOT/t.PINS)
    algorithm=t.digest((inspect.getsource(profile_function)+inspect.getsource(t.canonicalize)+inspect.getsource(t.function_refs)).encode())
    path=OUT/'candidate-profiles.json'
    if (t.ROOT/path).exists() and not check:
        cached=t.read(path)
        t.require(cached['source_pins_sha256']==source and cached['algorithm_sha256']==algorithm,'stale profile cache; explicit replay required')
        return cached
    refs=t.read(t.semantic.OUT/'semantic-xrefs.json')['references']
    indexed=collections.defaultdict(list)
    for r in refs:
        indexed[(r['build'],r['function']['start'])].append(r)
    result={}
    for build in (t.PRIMARY,t.TARGET):
        result[build]=[]
        for f in images[build].functions:
            rr=t.function_refs(images[build],f)+indexed[(build,t.native.hx(f['start']))]
            unique={(r['instruction'],r['role'],r['operand'],r['anchor_address']):r for r in rr}
            result[build].append(profile_function(images[build],f,list(unique.values())))
        print('Profiled',build,len(result[build]),flush=True)
    doc=env('profiles',builds=result,source_pins_sha256=source,algorithm_sha256=algorithm)
    write(path,doc,check)
    return doc

def support_dependencies(s):
    return s.get('anchors',[s])

def expand_dependencies(seeds, nodes, maximum=3):
    trusted={d:(v,0) for d,v in seeds.items()}
    accepted=[]
    for generation in range(1,maximum+1):
        batch=[]
        for node in sorted(nodes,key=lambda n:(n['donor'],n['target'])):
            if not node['eligible'] or node.get('community_only') or node['donor'] in trusted:
                continue
            if node['target'] in {r[0] for r in trusted.values()}:
                continue
            options=[deps for deps in node['support_options'] if deps and all(d in trusted and trusted[d][0]==v and trusted[d][1]<generation for d,v in deps)]
            if options:
                batch.append({**node,'generation':generation,'sufficient_dependencies':options})
        donors=collections.Counter(n['donor'] for n in batch)
        targets=collections.Counter(n['target'] for n in batch)
        batch=[n for n in batch if donors[n['donor']]==targets[n['target']]==1]
        if not batch:
            break
        for node in batch:
            trusted[node['donor']]=(node['target'],generation)
        accepted.extend(batch)
    return accepted

def evaluate_proposal(p, removed, candidates, reverse, seed_pairs):
    """Independent gate evaluation; absent gates never become positive facts."""
    removed=set(removed)
    reasons=[]
    support=[]
    for s in p['independent_support']:
        cls=SUPPORT_CLASS[s['class']]
        if cls in removed or cls=='callee' and 'import-helper-call' in removed:
            continue
        dependencies=support_dependencies(s)
        valid=all(seed_pairs.get(d['donor'])==d['target'] for d in dependencies)
        if valid:
            support.append(cls)
    reciprocal=len(candidates)==len(reverse)==1 and p['target_start'] in candidates and p['donor_start'] in reverse
    injective=not any(r.get('class') in ('retained-target-already-owned','retained-donor-already-mapped') for r in p['contradictions'])
    if p['contradictions'] or not injective:
        grade='rejected-proposal'; reasons.append('contradiction-retained-under-ablation')
    elif p['target_start'] not in candidates:
        grade='candidate'; reasons.append('pair-not-in-counterfactual-candidate-set')
    elif not reciprocal:
        grade='ambiguous'; reasons.append('counterfactual-reciprocity-not-unique')
    else:
        mandatory={'string-data-canonicalization','cfg-branch','boundary-size','field-parameter-return-role'}
        if p['internal_region_support']:
            mandatory.add('boundary-code-region')
        missing=mandatory & removed
        if not p['boundary_valid'] or not p['shape_equal']:
            reasons.append('incompatible-boundary-or-shape')
        if missing:
            reasons.extend('required-gate-removed:'+c for c in sorted(missing))
        if p['unproved_calls'] or p['unproved_external_tail_transfers']:
            reasons.append('unresolved-call-or-tail')
        if ('callee' in removed or 'import-helper-call' in removed) and any(s['class']=='trusted-mapped-callee' for s in p['independent_support']):
            reasons.append('mapped-call-behavior-proof-removed')
        if not support:
            reasons.append('no-independent-noncanonicalization-support')
        grade='reviewed-strong-proposal' if not reasons else 'reviewed-probable-proposal' if support or p['internal_region_support'] else 'candidate'
    return {'grade':grade,'semantic_transport':grade=='reviewed-strong-proposal',
            'reciprocal_unique':reciprocal,'injective':injective,'candidate_count':len(candidates),
            'reverse_candidate_count':len(reverse),'candidate_targets':candidates,'reverse_donors':reverse,
            'surviving_independent_classes':sorted(set(support)),'reasons':reasons}

def ablation_stage(images, check=False):
    cache=profiles(images)
    by={b:{r['start']:r for r in rows} for b,rows in cache['builds'].items()}
    groups={}
    for variant in ('baseline','string-data-canonicalization','cfg-branch','field-parameter-return-role'):
        groups[variant]={}
        for build,rows in cache['builds'].items():
            g=collections.defaultdict(list)
            for r in rows:
                if r[variant] is not None:
                    g[r[variant]].append(r['start'])
            groups[variant][build]=g
    audit=t.read(t.OUT/'trust-audit.json')['records']
    seeds={r['donor_start']:r['target_start'] for r in audit if r['disposition'].startswith('retained-')}
    proposals=t.read(t.OUT/'reference-candidates.json')['proposals']
    selected=[p for p in proposals if p['grade'] in ('reviewed-strong-proposal','reviewed-probable-proposal') or p['donor_start'] in ('0x82631A30','0x829506B0')]
    packets=[]
    for p in selected:
        guarded=copy.deepcopy(p)
        region_call_obligations=[]
        for support in p['internal_region_support']:
            for build,key in ((t.PRIMARY,'donor_region'),(t.TARGET,'target_region')):
                region=support[key]
                summary=flow(images[build],int(region['start'],16),int(region['end_exclusive'],16))
                if summary['calls']:
                    region_call_obligations.append({'build':build,'region':region['start'],'calls':summary['calls']})
        guarded['unproved_calls'] += region_call_obligations
        d,tar=by[t.PRIMARY][p['donor_start']],by[t.TARGET][p['target_start']]
        def evaluate(removed):
            variant=next((r for r in ('string-data-canonicalization','field-parameter-return-role','cfg-branch') if r in removed),'baseline')
            dg,tg=groups[variant][t.PRIMARY],groups[variant][t.TARGET]
            return evaluate_proposal(guarded,removed,tg.get(d[variant],[]),dg.get(tar[variant],[]),seeds)
        baseline=evaluate([])
        experiments=[{'removed':[c],**evaluate([c])} for c in CLASSES]
        # Enumerate all combinations of independent classes, keeping required
        # identity/ownership/behavior gates. This exposes alternatives, not scores.
        sufficient=[]
        for count in range(1,4):
            for subset in itertools.combinations(('caller','callee','neighbourhood-order'),count):
                removed=set(('caller','callee','neighbourhood-order'))-set(subset)
                if evaluate(removed)['semantic_transport'] and not any(set(s)<=set(subset) for s in sufficient):
                    sufficient.append(list(subset))
        differences=[]
        df=images[t.PRIMARY].by_start[int(p['donor_start'],16)]
        tf=images[t.TARGET].by_start[int(p['target_start'],16)]
        dw=images[t.PRIMARY].read(df['start'],df['end']-df['start'])
        tw=images[t.TARGET].read(tf['start'],tf['end']-tf['start'])
        for offset in range(0,min(len(dw),len(tw)),4):
            if dw[offset:offset+4]!=tw[offset:offset+4]:
                differences.append({'offset':offset,'donor_instruction_sha256':t.digest(dw[offset:offset+4]),'target_instruction_sha256':t.digest(tw[offset:offset+4]),
                                    'reference_definition':offset in {r['offset'] for r in d['canonical']['changed_instructions']}})
        packets.append({'id':p['donor_start']+':'+p['target_start'],'original_proposal_sha256':t.digest(t.payload(p)),
                        'original_grade':p['grade'],'donor':d['boundary'],'target':tar['boundary'],
                        'generation':p['generation'],'reference_evidence':d['canonical'],
                        'target_reference_evidence':tar['canonical'],'instruction_differences':differences,
                        'independent_support':p['independent_support'],'contradictions':p['contradictions'],
                        'internal_region_support':p['internal_region_support'],'baseline':baseline,
                        'region_call_obligations':region_call_obligations,
                        'counterfactuals':experiments,'minimal_independent_support_sets':sufficient,
                        'minimal_sufficient_evidence_sets':[sorted(set(s)|{'string-data-canonicalization','cfg-branch','boundary-size','field-parameter-return-role'}|({'boundary-code-region'} if p['internal_region_support'] else set())) for s in sufficient],
                        'single_point_dependencies':[e['removed'][0] for e in experiments if baseline['semantic_transport'] and not e['semantic_transport']],
                        'boundary_class':'ordinary-function-pair','human_review_state':'not-human-reviewed','canonical_adoption':False})
    closed=[]
    occupied_targets={r['target_start']:r['donor_start'] for r in audit if r['disposition'].startswith('retained-')}
    feature_rows=t.read(t.semantic.consistency.ARTIFACTS['exhaustive_function_features'])['builds']
    features={b:{r['start']:r for r in rows} for b,rows in feature_rows.items()}
    ordered=sorted(features[t.PRIMARY])
    for r in audit:
        if not r['anchors'] and not r['conflicts']:
            continue
        recomputed,topology_conflicts,_=t.independent_support(features[t.PRIMARY][r['donor_start']],features[t.TARGET][r['target_start']],features,seeds,{})
        position=t.bisect.bisect_left(ordered,r['donor_start'])
        neighbours=[]
        for adjacent in ordered[max(0,position-8):position+9]:
            if adjacent!=r['donor_start'] and adjacent in seeds and int(r['donor_start'],16)-int(adjacent,16)==int(r['target_start'],16)-int(seeds[adjacent],16):
                neighbours.append({'donor':adjacent,'target':seeds[adjacent]})
        independent_recheck={'mapped_callees':recomputed,'neighbours':neighbours,'topology_conflicts':topology_conflicts}
        if r['independent_without_data']:
            t.require(r['raw_equal'] or recomputed or neighbours,'original data-anchor independence no longer reproducible: '+r['id'])
        experiments=[]
        for removed in CLASSES:
            dp,tp=by[t.PRIMARY][r['donor_start']],by[t.TARGET][r['target_start']]
            variant=removed if removed in groups else 'baseline'
            if dp[variant] is None or tp[variant] is None:
                variant='string-data-canonicalization'
            available_targets=groups[variant][t.TARGET].get(dp[variant],[])
            available_donors=groups[variant][t.PRIMARY].get(tp[variant],[])
            viable_targets=[a for a in available_targets if a not in occupied_targets or occupied_targets[a]==r['donor_start']]
            viable_donors=[a for a in available_donors if a not in seeds or seeds[a]==r['target_start']]
            raw=r['raw_equal']
            cls=set(r['feature_classes'])
            if not recomputed:
                cls.discard('direct-call-topology')
            if not neighbours:
                cls.discard('local-address-delta-neighbourhood')
            if removed in ('callee','import-helper-call'):
                cls.discard('direct-call-topology')
            if removed=='neighbourhood-order':
                cls-={'local-address-delta-neighbourhood','local-ordering-neighbourhood'}
            independent=bool(cls & {'direct-call-topology','local-address-delta-neighbourhood'})
            full=any(x['full_identity_equal'] for x in r['reference_comparisons']) and removed!='string-data-canonicalization'
            disposition=t.trust_disposition(raw,independent,full,r['conflicts'],bool(r['anchors']))
            if removed in ('cfg-branch','boundary-size') and not r['conflicts']:
                disposition='review-required-independent-evidence'
            experiments.append({'removed':[removed],'raw_identity_retained':raw,'surviving_feature_classes':sorted(cls),
                                'disposition':disposition,'semantic_transport':disposition.startswith('retained-'),
                                'reason':'Contradictions persist; bounded windows never independently authorize transport.',
                                'candidate_profile':variant,'unconstrained_candidate_targets':available_targets,
                                'candidate_targets':viable_targets,'reverse_donors':viable_donors,
                                'reciprocal_unique':len(viable_targets)==len(viable_donors)==1,
                                'injective':occupied_targets.get(r['target_start'],r['donor_start'])==r['donor_start'],
                                'candidate_policy':'Recomputed instruction-key population followed by independent retained-peer occupancy; historical disposition remains distinct from candidate matching.'})
        minimal=[]
        if not r['conflicts']:
            if r['raw_equal']:
                minimal.append(['raw-byte-identity','cfg-branch','boundary-size','no-literal-contradiction'])
            for cls,feature,present in (('callee','direct-call-topology',bool(recomputed)),('neighbourhood-order','local-address-delta-neighbourhood',bool(neighbours))):
                if feature in r['feature_classes'] and present:
                    minimal.append([cls,'cfg-branch','boundary-size','no-literal-contradiction'])
        closed.append({'audit_id':r['id'],'original_record_sha256':r['original_record_sha256'],
                       'donor_start':r['donor_start'],'target_start':r['target_start'],
                       'baseline_disposition':r['disposition'],'counterfactuals':experiments,
                       'anchors':r['anchors'],'contradictions':r['conflicts'],'raw_equal':r['raw_equal'],
                       'independent_recheck':independent_recheck,
                       'minimal_sufficient_evidence_sets':minimal,
                       'single_point_dependencies':[e['removed'][0] for e in experiments if r['disposition'].startswith('retained-') and not e['semantic_transport']],
                       'partial_window_without_independent_support':t.trust_disposition(False,False,False,[],True)})
    t.require(len([p for p in packets if p['original_grade']=='reviewed-strong-proposal'])==86,'strong checkpoint population mismatch')
    t.require(len([p for p in packets if p['original_grade']=='reviewed-probable-proposal'])==715,'probable checkpoint population mismatch')
    t.require(sum(bool(r['anchors']) for r in closed)==97,'data-anchor ablation omission')
    doc=env('ablation',proposal_packets=packets,closed_records=closed,
            profile_sha256=t.old.sha256_file(t.ROOT/OUT/'candidate-profiles.json'),
            counts={'proposal_packets':len(packets),'closed_records':len(closed),
                    'grades':dict(sorted(collections.Counter(p['baseline']['grade'] for p in packets).items())),
                    'single_point_dependencies':dict(sorted(collections.Counter(c for p in packets for c in p['single_point_dependencies']).items()))},
            absent_classes={'September-two-hop':'not a primary mapping acceptance input',
                            'same-generation-derived':'baseline cross-check consumes retained closed seeds only'},
            policy='Required gate removal may preserve candidates while removing permission to transport; canonicalized strings are never independent support.')
    write(OUT/'feature-ablation.json',doc,check)
    print(json.dumps(doc['counts']),flush=True)
    return doc

def flow(image, start, end):
    calls,tails,returns,edges,unknown=[],[],[],[],[]
    for offset,(word,) in enumerate(struct.iter_unpack('>I',image.read(start,end-start))):
        pc=start+offset*4
        op=word>>26
        dest=t.native.branch(word,pc)
        if op in (16,18):
            item={'instruction':t.native.hx(pc),'destination':t.native.hx(dest),'relative_offset':pc-start}
            if word & 1:
                calls.append(item)
            elif not start<=dest<end:
                tails.append(item)
            else:
                edges.append([pc-start,dest-start])
        elif op==19 and ((word>>1)&1023)==16:
            returns.append({'instruction':t.native.hx(pc),'conditional':word!=0x4E800020})
        elif word==0:
            unknown.append(t.native.hx(pc))
    return {'calls':calls,'external_nonlink_transfers':tails,'returns':returns,
            'internal_edges':edges,'zero_words':unknown,'instruction_count':(end-start)//4}

def relation_class(facts):
    """Conservative relation policy; complete entry/exit evidence is mandatory.

    Similar fragments alone produce shared-body, never compiler lineage.
    """
    if not facts['executable'] or not facts['aligned']:
        return 'unresolved-boundary'
    if facts.get('internal_callable') and not facts.get('independent_pdata'):
        return 'internal-code-region'
    if facts.get('single_nonlink_transfer') and facts.get('target_has_owner'):
        return 'thunk' if facts.get('whole_body_transfer') else 'tail'
    if not facts.get('exact_shared_regions'):
        return 'unresolved-boundary'
    complete=all(facts.get(k,False) for k in ('coverage_complete','entry_exit_compatible','external_edges_correspond'))
    if complete:
        d,n=facts['donor_owner_count'],facts['target_owner_count']
        if d==n==1 and facts.get('equal_bounds'):
            return 'ordinary-function-pair'
        if d==1 and n>1:
            return 'split'
        if d>1 and n==1:
            return 'merge'
        if facts.get('call_boundary_change')=='outlined-call':
            return 'outline'
        if facts.get('call_boundary_change')=='inlined-call':
            return 'inline'
    return 'shared-body'

def extend_match(left,right,df,da,ta,width=32):
    owner=right.owner(ta)
    block=right.block(ta,width)
    if block is None or not block.execute or ta%4:
        return None
    lower=owner['start'] if owner else block.start
    upper=owner['end'] if owner else block.start+len(block.data)
    if owner is None:
        position=t.bisect.bisect_right(right.function_starts,ta)
        if position<len(right.function_starts):
            upper=min(upper,right.function_starts[position])
        if position:
            lower=max(lower,right.by_start[right.function_starts[position-1]]['end'])
    if ta+width>upper:
        return None
    dl,tl=da,ta
    dh,th=da+width,ta+width
    while dl>df['start'] and tl>lower and left.read(dl-4,4)==right.read(tl-4,4):
        dl-=4; tl-=4
    while dh<df['end'] and th<upper and left.read(dh,4)==right.read(th,4):
        dh+=4; th+=4
    return {'donor_start':t.native.hx(dl),'donor_end_exclusive':t.native.hx(dh),
            'target_start':t.native.hx(tl),'target_end_exclusive':t.native.hx(th),
            'size':dh-dl,'byte_sha256':t.digest(left.read(dl,dh-dl)),
            'target_owner':t.native.boundary(owner) if owner else None,
            'donor_flow':flow(left,dl,dh),'target_flow':flow(right,tl,th)}

def boundary_completion(images, check=False):
    prior=t.read(t.OUT/'boundaries.json')
    seed_pairs={r['donor_start']:r['target_start'] for r in t.read(t.OUT/'trust-audit.json')['records'] if r['disposition'].startswith('retained-')}
    records=[]
    # Every instruction-aligned 32-byte window is searched for the entire
    # declared primary population. Repeated windows are counted but cannot
    # establish unique lineage; only up to two positions need materialization.
    needles=collections.defaultdict(list)
    for row in prior['records']:
        f=images[t.PRIMARY].by_start[int(row['donor']['start'],16)]
        data=images[t.PRIMARY].read(f['start'],f['end']-f['start'])
        for offset in range(0,len(data)-31,4):
            needles[data[offset:offset+32]].append((f['start'],offset))
    matches=collections.defaultdict(list)
    frequencies=collections.Counter()
    donor_frequencies=collections.Counter()
    for build in (t.PRIMARY,t.TARGET):
        for block in images[build].blocks:
            if not block.execute:
                continue
            for offset in range(0,len(block.data)-31,4):
                window=block.data[offset:offset+32]
                if window in needles:
                    if build==t.PRIMARY:
                        donor_frequencies[window]+=1
                    else:
                        frequencies[window]+=1
                        if len(matches[window])<2:
                            matches[window].append(block.start+offset)
    unique_by_donor=collections.defaultdict(list)
    for window,locations in needles.items():
        if len(locations)==1 and donor_frequencies[window]==frequencies[window]==1:
            start,offset=locations[0]
            unique_by_donor[start].append((offset,matches[window][0]))
    for index,row in enumerate(prior['records']):
        f=images[t.PRIMARY].by_start[int(row['donor']['start'],16)]
        regions={}
        for offset,target in unique_by_donor[f['start']]:
            if any(int(r['donor_start'],16)<=f['start']+offset<int(r['donor_end_exclusive'],16) and
                   int(r['target_start'],16)-int(r['donor_start'],16)==target-(f['start']+offset) for r in regions.values()):
                continue
            r=extend_match(images[t.PRIMARY],images[t.TARGET],f,f['start']+offset,target)
            if r:
                regions[(r['donor_start'],r['target_start'])]=r
        ff=flow(images[t.PRIMARY],f['start'],f['end'])
        facts={'executable':True,'aligned':True,'exact_shared_regions':bool(regions),
               'donor_owner_count':1,'target_owner_count':len({r['target_owner']['start'] for r in regions.values() if r['target_owner']}),
               'coverage_complete':False,'entry_exit_compatible':False,'external_edges_correspond':False,
               'single_nonlink_transfer':len(ff['external_nonlink_transfers'])==1 and not ff['calls'],
               'whole_body_transfer':ff['instruction_count']==1,
               'target_has_owner':len(ff['external_nonlink_transfers'])==1 and images[t.PRIMARY].owner(int(ff['external_nonlink_transfers'][0]['destination'],16)) is not None}
        for region in regions.values():
            owner=region['target_owner']
            whole=owner is not None and region['donor_start']==row['donor']['start'] and region['donor_end_exclusive']==row['donor']['end_exclusive'] and region['target_start']==owner['start'] and region['target_end_exclusive']==owner['end_exclusive']
            if whole:
                dflow,tflow=region['donor_flow'],region['target_flow']
                external=True
                for field in ('calls','external_nonlink_transfers'):
                    targets={r['relative_offset']:r['destination'] for r in tflow[field]}
                    external &= len(targets)==len(dflow[field]) and all(seed_pairs.get(r['destination'])==targets.get(r['relative_offset']) for r in dflow[field])
                facts.update(coverage_complete=True,entry_exit_compatible=True,external_edges_correspond=external,equal_bounds=True)
        kind=relation_class(facts)
        records.append({'id':f'primary:{index:04d}','source_index':index,'build':t.PRIMARY,
                        'donor':row['donor'],'prior_relation':row['relation'],'population':row['population'],
                        'flow':ff,'regions':list(regions.values()),'facts':facts,'relation':kind,
                        'reason':'Native nonlink transfer into an owned executable body; cross-build lineage remains unproven.' if kind in ('tail','thunk') else 'Exact shared code is bounded by actual ownership; complete entry/exit and external-edge checks govern any ordinary-pair classification.' if regions else 'No reciprocal unique exact 32-byte region in the complete aligned-window search.',
                        'semantic_transport':False,'source_lineage_proven':False})
    for i,row in enumerate(prior['september_boundary_review']):
        old=row['record']; df=images['sep-2008'].by_start[int(old['donor_start'],16)]
        comparisons=[]
        for candidate in old['top_candidates']:
            tf=images[t.PRIMARY].by_start.get(int(candidate['target_start'],16))
            if tf:
                a,b=images['sep-2008'].read(df['start'],df['end']-df['start']),images[t.PRIMARY].read(tf['start'],tf['end']-tf['start'])
                equal=0
                while equal+4<=min(len(a),len(b)) and a[equal:equal+4]==b[equal:equal+4]: equal+=4
                comparisons.append({'target':t.native.boundary(tf),'equal_start_prefix_bytes':equal,
                                    'target_flow':flow(images[t.PRIMARY],tf['start'],tf['end']),
                                    'original_contradictions':candidate['contradictions']})
        records.append({'id':f'september:{i:03d}','source_index':row['original_terminal_index'],'build':'sep-2008',
                        'donor':t.native.boundary(df),'flow':flow(images['sep-2008'],df['start'],df['end']),
                        'comparisons':comparisons,'relation':'unresolved-boundary','semantic_transport':False,
                        'reason':'Changed .pdata size/control flow: common prefix does not prove entry/exit, split, merge, outline or inline correspondence.'})
    for i,region in enumerate(prior['internal_code_regions']):
        records.append({'id':f'internal:{i}','region':region,'relation':'internal-code-region','semantic_transport':False,
                        'reason':'Reachable byte-identical comparator region has no independent .pdata entry or owner.'})
    t.require(len(prior['records'])==713 and len(prior['september_boundary_review'])==33,'boundary population drift')
    doc=env('boundaries',records=records,counts=dict(sorted(collections.Counter(r['relation'] for r in records).items())),
            populations={'primary':713,'september':33,'comparators':2},
            strong_probable_boundary_disagreements=[{'donor':p['donor_start'],'target':p['target_start'],'grade':p['grade']} for p in t.read(t.OUT/'reference-candidates.json')['proposals'] if p['grade'] in ('reviewed-strong-proposal','reviewed-probable-proposal') and not p['boundary_valid']],
            exact_window_policy={'width':32,'stride':4,'target_search':'all-executable-sections','lineage_requires_complete_entry_exit_edges':True})
    write(OUT/'boundary-completion.json',doc,check)
    print('Boundary terminals',doc['counts'],flush=True)
    return doc

def typed_disposition(facts):
    if facts.get('incompatible_access') or facts.get('incompatible_content'):
        return 'rejected-incompatible-object-or-access'
    if facts.get('type_string_only'):
        return 'type-context-not-constructor'
    if facts.get('table_kind') in ('jump-table','callback-array','import-table','mixed-data'):
        return 'rejected-vtable-alternative'
    if not facts.get('bounds_proven') or facts.get('interior') or facts.get('overlap'):
        return 'unresolved-object-boundary'
    if facts.get('table_kind')=='vtable':
        required=('aligned','executable_slots','typed_descriptor_proven','object_vptr_writer_proven','slot_correspondence_proven')
        return 'proposed-vtable' if all(facts.get(k) for k in required) else 'unresolved-vtable-chain'
    return 'proposed-stable-global' if facts.get('mapped_access_roles') and facts.get('complete_content_equal') else 'unresolved-global-chain'

def typed_completion(images, check=False):
    old=t.read(t.OUT/'types-globals.json')
    cache=t.read(OUT/'candidate-profiles.json')
    refs=collections.defaultdict(list)
    for build,rows in cache['builds'].items():
        for row in rows:
            for rejection in row['canonical']['rejected_references']:
                ref=rejection['reference']
                refs[(build,ref['anchor_address'])].append({'function':row['boundary'],'instruction':ref['instruction'],
                    'role':ref['role'],'operand':ref['operand'],'width':ref['width'],'destination':ref['destination'],
                    'definition_instructions':ref['definition_instructions']})
    tables=[]
    for i,row in enumerate(old['pointer_runs']):
        image=images[row['build']]
        start,end=int(row['start'],16),int(row['end_exclusive'],16)
        slots=[]
        for slot in row['slots']:
            address=int(slot['entry'],16)
            owner=image.by_start.get(address)
            t.require(owner is not None and image.read(int(slot['slot'],16),4)==struct.pack('>I',address),'pointer-run byte/ownership drift')
            slots.append({**slot,'exact_pdata_owner':t.native.boundary(owner)})
        before=image.read(start-4,4)
        after=image.read(end,4)
        facts={'table_kind':'undetermined-executable-pointer-run','bounds_proven':False,
               'aligned':start%4==0,'executable_slots':True,'typed_descriptor_proven':False,
               'object_vptr_writer_proven':False,'slot_correspondence_proven':len(row.get('matching_target_pointer_runs',[]))==1}
        tables.append({'id':f'pointer-run:{i:04d}','source_index':i,'build':row['build'],'section':row['section'],
                       'start':row['start'],'end_exclusive':row['end_exclusive'],'alignment':4,'slots':slots,
                       'surrounding_word_hashes':[t.digest(x) if x else None for x in (before,after)],
                       'native_readers_writers':refs[(row['build'],row['start'])],
                       'matching_target_pointer_runs':row.get('matching_target_pointer_runs',[]),
                       'facts':facts,'disposition':typed_disposition(facts),
                       'alternatives':['vtable','callback-array','adjacent-mixed-data','multiple-adjacent-tables'],
                       'reason':'Maximal executable-pointer run has observed storage bounds, not a proven object/table allocation boundary; no validated RTTI descriptor/vptr writer chain.',
                       'canonical_adoption':False})
    original_globals={r['id']:r for r in t.read(t.semantic.OUT/'semantic-globals.json')['records']}
    globals_rows=[]
    for i,row in enumerate(old['globals']):
        source=original_globals[row['prior_global_id']] if 'prior_global_id' in row else row
        d,tuse=source['donor_access'],source['target_access']
        facts={'bounds_proven':False,'mapped_access_roles':row.get('mapping_retained',True),
               'incompatible_access':not t.native.compatible_access(d,tuse),
               'incompatible_content':not row['compatible_access_and_content']}
        globals_rows.append({'id':f'global:{i:04d}','source_index':i,'prior_global_id':row.get('prior_global_id'),
                             'donor_access':d,'target_access':tuse,'observed_width_is_object_bound':False,
                             'same_address':d['address']==tuse['address'],'facts':facts,
                             'disposition':typed_disposition(facts),
                             'reason':'Access width bounds a scalar read/write only; complete storage/object extent and interprocedural writer ownership remain unproven.',
                             'canonical_adoption':False})
    types=[]
    for i,row in enumerate(old['type_contexts']):
        objects=[]
        for occurrence in row['occurrences']:
            im=images[occurrence['build']]; address=int(occurrence['address'],16)
            objects.append({'build':occurrence['build'],'literal':t.object_at(im,address),
                            'preceding_8_bytes_sha256':t.digest(im.read(address-8,8)) if im.read(address-8,8) else None,
                            'descriptor_layout_proven':False})
        facts={'type_string_only':True}
        types.append({'id':row['anchor_id'],'source_index':i,'objects':objects,'native_xref_ids':row['native_xref_ids'],
                      'disposition':typed_disposition(facts),'constructor_identity_proven':False,
                      'reason':'Complete decorated type spelling does not identify a constructor or prove preceding bytes are a validated RTTI descriptor.',
                      'canonical_adoption':False})
    t.require((len(types),len(tables),len(globals_rows))==(425,4939,2479),'typed population drift')
    doc=env('typed',type_contexts=types,pointer_runs=tables,globals=globals_rows,
            counts={name:dict(sorted(collections.Counter(r['disposition'] for r in rows).items())) for name,rows in [('types',types),('pointer_runs',tables),('globals',globals_rows)]},
            recognizers='No undocumented native RTTI layout introduced. Typed gates consume explicit proven descriptor/writer/boundary facts; real rows lack those facts.')
    write(OUT/'typed-completion.json',doc,check)
    print('Typed terminals',doc['counts'],flush=True)
    return doc

class GitBlobInput:
    """Read-only byte stream for an immutable historical file; no hash override."""
    def __init__(self, data):
        self.data=data
    def open(self, mode):
        t.require(mode=='rb','historical input is read-only binary')
        return io.BytesIO(self.data)

def ownership_verification(check=False):
    import Fable2OwnershipCorroboration as owner
    historical='c8a2264500ea32a68d747808d52b7e7820c81b72'
    blob=subprocess.check_output(['git','show',historical+':fable2_manifest.toml'],cwd=t.ROOT)
    baseline=subprocess.check_output(['git','show',t.BASE+':fable2_manifest.toml'],cwd=t.ROOT)
    plan=t.read('out/ownership-corroboration/phase4-run1/fable2-indirect-targets.import-plan.json')
    expected=plan['inputs']['manifest']['sha256']
    t.require(t.digest(blob)==expected,'historical manifest blob does not match immutable plan')
    t.require(t.digest(baseline)==t.old.sha256_file(t.ROOT/'fable2_manifest.toml'),'baseline manifest differs from unchanged current input')
    args=SimpleNamespace(phase4_directory=t.ROOT/'out/ownership-corroboration/phase4-run1',
          closure=t.ROOT/'out/ownership-corroboration/closure-run1/entrypoint-closure.json',
          ghidra_map=t.ROOT/'out/analysis/BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00/ghidra-function-map.json',
          guest_snapshot=t.ROOT/'out/phase3-regression-closure-final-smoke/iteration-01/tu1-text-0x82000000.bin',
          guest_base=0x82000000,disassembler=t.ROOT/'out/tools/ppc-disasm.exe')
    original=owner.p4.DEFAULT_MANIFEST
    try:
        # Only select the input byte stream. The historical verifier's expected
        # hashes, reconstruction, semantic validation and output comparison stay intact.
        owner.p4.DEFAULT_MANIFEST=GitBlobInput(blob)
        outputs=owner.build(args)
    finally:
        owner.p4.DEFAULT_MANIFEST=original
    serialized={'ownership-ledger.json':owner.p4.canonical_json_bytes(outputs),
                'ownership-ledger.md':owner.markdown(outputs),
                'ownership-reviewed-import-plan.json':owner.p4.canonical_json_bytes(owner.reviewed_plan(outputs))}
    comparisons=[]
    for name,data in serialized.items():
        path=Path('docs/fable2-discovery-pipeline/ownership')/name
        comparisons.append({'path':path.as_posix(),'regenerated_sha256':t.digest(data),
                            'committed_sha256':t.old.sha256_file(t.ROOT/path),'equal':data==(t.ROOT/path).read_bytes()})
    differences=[]
    def compare(a,b,path=''):
        if type(a)!=type(b):
            differences.append({'pointer':path,'historical':a,'current':b}); return
        if isinstance(a,dict):
            for key in sorted(set(a)|set(b)):
                compare(a.get(key),b.get(key),path+'/'+str(key))
        elif isinstance(a,list):
            if len(a)!=len(b):
                differences.append({'pointer':path,'historical_count':len(a),'current_count':len(b)})
            for i,(x,y) in enumerate(zip(a,b)): compare(x,y,path+'/'+str(i))
        elif a!=b:
            differences.append({'pointer':path,'historical':a,'current':b})
    compare(t.read('docs/fable2-discovery-pipeline/ownership/ownership-ledger.json'),outputs)
    doc=env('ownership',historical_commit=historical,historical_manifest_sha256=t.digest(blob),
            phase2b_manifest_sha256=t.digest(baseline),current_manifest_unchanged=True,
            inherited_current_input_failure='FAIL: stale manifest',
            input_selection='Immutable Git blob read through rb stream; original validator hashes stream normally. No manifest written or edited.',
            reconstruction='byte-identical-three-outputs' if all(r['equal'] for r in comparisons) else 'semantic-validation-passed-output-drift',
            comparisons=comparisons,counts=outputs['counts'],differences=differences,
            current_generated_input=identity(Path('generated/default/fable2_recomp.136.cpp')),
            missing_historical_input={'path':'generated/default/fable2_recomp.136.cpp','sha256':'6053CC0EAC4636AA03AAA26581162B707C37E1B52BEE4C10F205D07C63EBDF59',
                'search':'Only current file found under repository generated/out; no history for this path in local Git refs.',
                'effect':'Historical JSON byte reconstruction remains blocked; semantic ledger and human Markdown reconstruction pass.'})
    write(OUT/'ownership-verification.json',doc,check)
    print(json.dumps({'reconstruction':doc['reconstruction'],'differences':differences[:8],'difference_count':len(differences)}),flush=True)
    return outputs,doc

def identity(path):
    p=t.ROOT/path
    return {'path':path.as_posix(),'size':p.stat().st_size,'sha256':t.old.sha256_file(p)}

def mapping_final(check=False):
    ablation=t.read(OUT/'feature-ablation.json')
    by={(p['donor']['start'],p['target']['start']):p for p in ablation['proposal_packets']}
    candidates=t.read(t.OUT/'reference-candidates.json')
    proposals=copy.deepcopy(candidates['proposals'])
    for p in proposals:
        packet=by.get((p['donor_start'],p['target_start']))
        if packet:
            p['grade']=packet['baseline']['grade']
            p['completion_packet_id']=packet['id']
    pairs=t.read(t.semantic.P2/'prototype-correspondence-accepted.json')['records']
    effective=t.effective_view(pairs,t.read(t.OUT/'trust-audit.json')['records'],proposals)
    seeds={r['donor_start']:r['target_start'] for r in effective['records'] if r['source']=='closed-phase2a-retained'}
    nodes=[{'donor':p['donor_start'],'target':p['target_start'],'eligible':True,
            'support_options':[[(d['donor'],d['target']) for d in support_dependencies(s)] for s in p['independent_support']]}
           for p in effective['additions']]
    replay=expand_dependencies(seeds,nodes)
    t.require({(r['donor'],r['target']) for r in replay}=={(r['donor'],r['target']) for r in nodes},'independent generation/injectivity cross-check failed')
    effective['dependency_cross_check']=replay
    write(OUT/'effective-map.json',effective,check)
    artifacts=[identity(p) for p in (OUT/'candidate-profiles.json',OUT/'feature-ablation.json',OUT/'boundary-completion.json',
               OUT/'effective-map.json',t.OUT/'trust-audit.json',t.OUT/'september-pairs.json',t.OUT/'known-cases.json',t.PINS)]
    frozen=env('freeze',artifacts=artifacts,semantic_feedback_allowed=False,
               consumer_paths={'effective_map':(OUT/'effective-map.json').as_posix(),'september':(t.OUT/'september-pairs.json').as_posix()},
               no_semantic_result_used_for_acceptance=True)
    write(OUT/'mapping-freeze.json',frozen,check)
    print('Final mapping arithmetic',effective['counts'],flush=True)
    return frozen

def state_provenance(category, native_chain=None):
    return {'path_category':category,'runtime_state_proven':native_chain is not None,
            'native_chain':native_chain,'reason':'Native lifetime/namespace chain required; path or structural pairing alone cannot establish a Lua state.'}

def preservation_disposition(presence, dependencies, runtime_chain=False, community_only=False):
    if community_only or not presence:
        return 'insufficient-first-party-presence'
    if not dependencies:
        return 'presence-only-dependencies-unresolved'
    return 'dependency-linked-preservation-candidate' if not runtime_chain else 'reviewable-chain-not-integrated'

def recon_completion(check=False):
    registration=t.read(t.OUT/'registration.json')
    records=[]
    for i,r in enumerate(registration['constructor_uses']):
        complete=r['name'] is not None and t.identity_token(r['name']) is not None and r['callback'] is not None
        records.append({'id':f'call:{i:04d}','source_index':i,'build':r['build'],
                        'helper':r['helper'],'caller':r['caller'],'callsite':r['call']['instruction'],
                        'disposition':'native-name-callback-state-unresolved' if complete else 'incomplete-name-or-callback',
                        'name_hash':r['name'].get('full_sha256') if r['name'] else None,
                        'blockers':r['blockers'],'tu1_callable':False,
                        'reason':'Constructor shape does not prove all callee semantics, state/namespace ownership and frozen donor/TU1 callback correspondence.'})
    shapes=[{'source_index':i,'build':r['build'],'boundary':r['boundary'],'disposition':'shape-recognized-callee-obligations-unresolved',
             'blockers':r['shape']['unverified_obligations']} for i,r in enumerate(registration['recognizer_candidates'])]
    scripts=t.read(t.OUT/'scripts.json')
    script_rows=[]
    for i,r in enumerate(scripts['records']):
        parsed='parsed' in r
        script_rows.append({'source_index':i,'build':r['build'],'path':r['path'],'sha256':r['sha256'],'size':r['size'],
                            'state':state_provenance(r['state_path_category']),
                            'disposition':'parsed-loose-chunk-state-unresolved' if parsed else 'bank-or-interface-inventory-only',
                            'blocker':r.get('blocker','Native Lua-state lifetime and binding provenance absent from parsed chunk metadata.'),
                            'canonical_adoption':False})
    preservation=[]
    for i,r in enumerate(t.read(t.OUT/'preservation.json')['records']):
        disposition=preservation_disposition(True,r['dependencies'])
        preservation.append({'source_index':i,'build':r['build'],'path':r['path'],'disposition':disposition,
                             'dependency_count':len(r['dependencies']),'retail_presence':r['retail_presence'],
                             'current_runtime_presence':r['current_runtime_presence'],'grade':r['grade'],
                             'portability_class':r['portability_class'],'runnable_recovery_proven':False,
                             'reason':'First-party file/interface presence is bound; dependency names are requirements, not proven callable runtime chains.'})
    t.require((len(shapes),len(records),sum(r['disposition']=='native-name-callback-state-unresolved' for r in records))==(206,2662,2647),'registration populations drift')
    t.require((len(script_rows),len(scripts['script_pairs']),len(preservation))==(160,54,200),'recon population drift')
    doc=env('recon',registration_shapes=shapes,registration_calls=records,scripts=script_rows,
            script_pairs=scripts['script_pairs'],preservation=preservation,
            sources=[identity(t.OUT/(name+'.json')) for name in ('registration','scripts','preservation')],
            counts={'registration':dict(sorted(collections.Counter(r['disposition'] for r in records).items())),
                    'scripts':dict(sorted(collections.Counter(r['disposition'] for r in script_rows).items())),
                    'preservation':dict(sorted(collections.Counter(r['disposition'] for r in preservation).items()))},
            blocked_inputs=[{'id':'bank-format','evidence':'scripts records lacking parsed metadata','needed':'Validated bank entry format/offset/decompression contract; loose Lua header parser does not parse unrelated banks.'},
                            {'id':'state-provenance','evidence':'All native constructor calls retain state-and-namespace obligation','needed':'Static state lifetime/namespace ownership and corresponding TU1 chain.'},
                            {'id':'retail-content-provenance','evidence':'Current-runtime extraction is separately pinned but not authenticated retail-disc content identity','needed':'Authenticated retail bank entry inventory and dependency closure.'}])
    write(OUT/'recon-completion.json',doc,check)
    print('Recon terminals',doc['counts'],flush=True)
    return doc

def two_hop(start, secondary, primary):
    first=secondary.get(start)
    if first is None or not first['trusted']:
        return None
    second=primary.get(first['target'])
    if second is None or not second['trusted']:
        return None
    return [(start,first['target']),(first['target'],second['target'])]

FIXTURE_BINDINGS = '''test_production_physics_spellings_share_prefix_but_not_identity
test_synthetic_shared_sixteen_byte_prefix
test_same_virtual_address_different_content
test_relocated_complete_string
test_interior_and_suffix_are_explicit
test_utf16_boundaries_and_terminator,test_ascii_terminator_required
test_common_zero_is_not_independent_support,test_empty_byte_string_requires_explicit_use_context
test_binary_header_has_no_invented_boundary
test_partial_data_only_loses_trust
test_independent_evidence_survives_anchor_removal
test_signed_low_carry_and_only_proven_immediates
test_signed_low_carry_and_only_proven_immediates
test_relocation_canonicalizes_but_unrelated_constant_does_not
test_ablation_removes_support_without_double_counting
test_fixed_point_is_seeded_non_circular_and_order_independent
test_fixed_point_is_seeded_non_circular_and_order_independent
test_crossed_targets_and_community_do_not_bootstrap,test_duplicate_target_rejected,test_production_ablation_populations_physics_and_hammer
test_literal_contradiction_overrides_exact_bytes,test_removed_gate_recomputes_reciprocity_and_grade
test_hammer_callee_diff_is_only_empty_pointer_and_comparator_call,test_production_ablation_populations_physics_and_hammer
test_comparators_are_equal_reachable_unowned_regions
test_closed_collision_is_suppressed_in_effective_consumer_view
test_duplicate_donor_rejected,test_duplicate_target_rejected
test_unsupported_community_class_cannot_create_mapping
test_payload_shape_exposes_unproven_callees,test_adversarial_payload_width_source_and_name_flow,test_adjacency_and_truncated_layout_do_not_match
test_review_selection_positive_negative_and_deterministic
test_bound_artifacts_detect_mutations
test_output_roots_fail_closed,test_forbidden_paths_are_not_allowlisted
test_secondary_pair_level_result_matches_closed_aggregate
test_two_hop_requires_each_trusted_non_oracular_hop
test_all_transformation_classes_positive_and_adversarial,test_thunk_tail_internal_and_unresolved_have_distinct_bounds
test_unmatched_and_boundary_population_is_exhaustive,test_all_transformation_classes_positive_and_adversarial
test_vtable_positive_requires_complete_typed_chain
test_global_identity_needs_boundaries_roles_and_compatible_content
test_global_identity_needs_boundaries_roles_and_compatible_content
test_stripped_debug_information_preserves_executable_pair,test_lua_invalid_or_unrelated_container_fails_closed
test_script_state_categories_do_not_prove_runtime_identity
test_preservation_needs_first_party_presence_and_dependencies
test_preservation_needs_first_party_presence_and_dependencies
test_frozen_hash_prevents_semantic_feedback,test_frozen_mapping_files_remain_byte_bound'''.splitlines()

def check_identity(path,row):
    t.require(path.stat().st_size==row['size'] and t.old.sha256_file(path)==row['sha256'],'bound artifact bytes differ')

def fixture_coverage(check=False):
    tests={}
    for path in sorted((t.ROOT/'tests').glob('test_fable2_prototype*.py')):
        tree=ast.parse(path.read_text())
        for cls in tree.body:
            if isinstance(cls,ast.ClassDef):
                for fn in cls.body:
                    if isinstance(fn,ast.FunctionDef) and fn.name.startswith('test_'):
                        tests[fn.name]={'path':path.relative_to(t.ROOT).as_posix(),'test_id':path.stem+'.'+cls.name+'.'+fn.name,'line':fn.lineno}
    t.require(len(FIXTURE_BINDINGS)==len(FIXTURES)==39,'fixture catalog drift')
    rows=[]
    for i,(name,bindings) in enumerate(zip(FIXTURES,FIXTURE_BINDINGS),1):
        refs=[]
        for method in bindings.split(','):
            t.require(method in tests,'missing required fixture '+method)
            refs.append(tests[method])
        rows.append({'id':f'fixture.{i:02d}','category':name,'tests':refs,
                     'evidence_contract':'Positive and adversarial assertions in the named test bodies; runtime execution is prohibited.'})
    doc=env('fixtures',records=rows,category_count=39,
            sources=[identity(Path(p)) for p in sorted({r['path'] for row in rows for r in row['tests']})])
    write(OUT/'fixture-coverage.json',doc,check)
    return doc

def test_run():
    if str(t.ROOT) not in sys.path:
        sys.path.insert(0,str(t.ROOT))
    suite=unittest.defaultTestLoader.discover(str(t.ROOT/'tests'))
    def ids(s):
        result=[]
        for item in s:
            result.extend(ids(item) if isinstance(item,unittest.TestSuite) else [item.id()])
        return result
    names=ids(suite)
    stream=io.StringIO()
    with contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
        result=unittest.TextTestRunner(stream=stream,verbosity=0).run(suite)
    t.require(result.wasSuccessful(),stream.getvalue())
    coverage=fixture_coverage()
    executed=set(names)
    t.require(all(r['test_id'] in executed for row in coverage['records'] for r in row['tests']),'fixture catalog references unexecuted tests')
    doc=env('tests',tests=sorted(names),run=result.testsRun,failures=len(result.failures),errors=len(result.errors),
            skipped=[{'test':test.id(),'reason':reason} for test,reason in result.skipped],
            fixture_categories=39,all_required_fixture_methods_executed=True)
    write(OUT/'test-results.json',doc)
    print('Tests:',result.testsRun,'failures:',len(result.failures),'errors:',len(result.errors),flush=True)
    return doc

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['matrix-initial','ablation','verify-ablation','boundaries','verify-boundaries','typed','verify-typed','ownership','verify-ownership','mapping','verify-mapping','recon','verify-recon','semantics','verify-semantics','tests'])
    args=parser.parse_args()
    if args.command=='matrix-initial':
        matrix_initial()
    elif args.command=='tests':
        test_run()
    elif 'ownership' in args.command:
        ownership_verification(args.command.startswith('verify-'))
    elif 'mapping' in args.command:
        t.binding()
        mapping_final(args.command.startswith('verify-'))
    elif 'recon' in args.command:
        t.binding()
        recon_completion(args.command.startswith('verify-'))
    else:
        _,images,_,_=t.load_inputs()
        if 'boundaries' in args.command:
            boundary_completion(images,args.command.startswith('verify-'))
        elif 'typed' in args.command:
            typed_completion(images,args.command.startswith('verify-'))
        elif 'semantics' in args.command:
            doc=t.semantic_stage(images,OUT)
            write(OUT/'semantic-final.json',doc,args.command.startswith('verify-'))
            print(doc['counts'],flush=True)
        else:
            ablation_stage(images,args.command=='verify-ablation')

if __name__=='__main__':
    main()
