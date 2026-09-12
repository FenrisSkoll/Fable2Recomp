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
    if p['contradictions'] or not injective or not p['boundary_valid'] or not p['shape_equal']:
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

def behavior_features(image,f):
    start,end=f['start'],f['end']
    words=[w[0] for w in struct.iter_unpack('>I',image.read(start,end-start))]
    leaders={0}; successors={}; fields=[]; frames=[]; returns=[]
    for i,word in enumerate(words):
        offset=i*4; op=word>>26; rt=(word>>21)&31; ra=(word>>16)&31
        if op in (32,34,36,38,40,42,44,48,50,52,54,58,62):
            displacement=t.native.signed(word & (0xFFFC if op in (58,62) else 0xFFFF))
            fields.append({'offset':offset,'opcode':op,'base_register':ra,'value_register':rt,'displacement':displacement,
                           'role':'read' if op in (32,34,40,42,48,50,58) else 'write',
                           'width':{32:4,34:1,36:4,38:1,40:2,42:2,44:2,48:4,50:8,52:4,54:8,58:8,62:8}[op]})
        if op==37 and rt==ra==1:
            frames.append({'offset':offset,'stack_delta':t.native.signed(word&0xFFFF)})
        if op==14 and rt==3 and ra==0:
            returns.append({'offset':offset,'literal_return_register_definition':t.native.signed(word&0xFFFF)})
        next_offset=offset+4 if offset+4<end-start else -1
        succ=[next_offset]
        if op in (16,18) and not word&1:
            dest=t.native.branch(word,start+offset)-start
            dest=dest if 0<=dest<end-start else -1
            succ=[dest]+([next_offset] if op==16 else [])
        elif op==19 and ((word>>1)&1023) in (16,528) and not word&1:
            succ=[-1]+([next_offset] if (word>>21)&31!=20 else [])
        if succ!=[next_offset] or op==19 and ((word>>1)&1023) in (16,528):
            leaders.update(x for x in succ+[next_offset] if x>=0)
            successors[offset]=succ
    starts=sorted(leaders)
    edges=set(); exit_node=len(starts)
    for i,a in enumerate(starts):
        stop=starts[i+1] if i+1<len(starts) else end-start
        last=stop-4
        targets=successors.get(last,[stop if stop<end-start else -1])
        for target in targets:
            edges.add((i,exit_node if target<0 else t.bisect.bisect_right(starts,target)-1))
    def dominance(root,links):
        children=collections.defaultdict(set); predecessors=collections.defaultdict(set)
        for a,b in links: children[a].add(b); predecessors[b].add(a)
        reachable={root}; pending=[root]
        while pending:
            for child in children[pending.pop()]-reachable:
                reachable.add(child); pending.append(child)
        dom={v:({root} if v==root else set(reachable)) for v in reachable}
        for _ in range(len(reachable)+1):
            changed=False
            for v in sorted(reachable-{root}):
                incoming=predecessors[v]&reachable
                value={v}|set.intersection(*(dom[p] for p in incoming))
                if value!=dom[v]: dom[v]=value; changed=True
            if not changed: break
        return [[v,sorted(dom[v])] for v in sorted(dom)]
    return {'field_accesses':fields,'stack_frames':frames,'return_register_constants':returns,
            'block_starts':starts,'edges':sorted([list(e) for e in edges]),
            'dominators':dominance(0,edges),'postdominators':dominance(exit_node,{(b,a) for a,b in edges}),
            'interpretation':'Known direct CFG; calls modeled as returning, unresolved indirect nonlink transfers treated as exits. No source-level parameter/type claim.'}

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
        behavioral={build:behavior_features(images[build],images[build].by_start[int(p[key],16)]) for build,key in ((t.PRIMARY,'donor_start'),(t.TARGET,'target_start'))}
        behavioral_equal=behavioral[t.PRIMARY]==behavioral[t.TARGET]
        if not behavioral_equal:
            guarded['shape_equal']=False
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
                        'behavior_features':behavioral,'behavior_features_equal':behavioral_equal,
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
    baseline_inputs=t.read('docs/fable2-discovery-pipeline/ownership/ownership-ledger.json')['inputs']
    for key,path in [('import_plan',args.phase4_directory/'fable2-indirect-targets.import-plan.json'),
                     ('phase4_queue',args.phase4_directory/'phase4-static-ownership-follow-up.json'),
                     ('summary',args.phase4_directory/'xenia-indirect-targets.summary.json'),
                     ('closure',args.closure),('ghidra_map',args.ghidra_map)]:
        t.require(t.old.sha256_file(path)==baseline_inputs[key]['sha256'],'historical ownership input drift: '+key)
    t.require(t.old.sha256_file(t.ROOT/'generated/default/fable2_recomp.136.cpp')=='D25E664A98833BF9433413336AC92A7376102A67049C0FF35F1270E6BDEB44CB','current generated verification input changed')
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
    expected_drift={'/targets/20/current_owner/generated/file_sha256','/targets/20/current_owner/generated/line','/targets/20/return_checks/0/generated_lr_assignment_lines/0'}
    t.require({d['pointer'] for d in differences}==expected_drift,'unexplained historical ownership drift')
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

def review_final(check=False):
    packets=t.read(OUT/'feature-ablation.json')['proposal_packets']
    originals=t.read(t.OUT/'reference-candidates.json')['proposals']
    strata=collections.defaultdict(list)
    lookup={}
    for i,p in enumerate(packets):
        key=p['id']; strata[p['baseline']['grade']].append(key)
        lookup[key]={'path':(OUT/'feature-ablation.json').as_posix(),'pointer':f'/proposal_packets/{i}'}
    for i,p in enumerate(originals):
        key=p['donor_start']+':'+p['target_start']
        if key not in lookup:
            strata[p['grade']].append(key)
            lookup[key]={'path':(t.OUT/'reference-candidates.json').as_posix(),'pointer':f'/proposals/{i}'}
    prior_review=t.read(t.OUT/'review.json')
    rows=[]; available={}
    for group,values in sorted(strata.items()):
        ids=sorted(set(values)); selected=ids if group=='reviewed-strong-proposal' else ids[:3]
        available[group]={'available':len(ids),'selected':len(selected)}
        rows += [{'stratum':group,'id':key,'evidence':lookup[key],'human_review_state':'not-human-reviewed'} for key in selected]
    for row in prior_review['records']:
        if row['stratum'].startswith(('subsystem:','intersection:')):
            rows.append({'stratum':row['stratum'],'id':row['record_id'],'evidence':{'path':(t.OUT/'review.json').as_posix(),'record_id':row['record_id']},'human_review_state':'not-human-reviewed'})
            available[row['stratum']]=prior_review['availability'][row['stratum']]
    t.require(sum(r['stratum']=='reviewed-strong-proposal' for r in rows)==sum(p['baseline']['semantic_transport'] for p in packets),'strong review omission')
    doc=env('review',records=rows,availability=available,all_strong_included=True,human_approval=False)
    write(OUT/'completion-review.json',doc,check)
    return doc

def verify_terminals():
    ablation=t.read(OUT/'feature-ablation.json')
    originals={p['donor_start']+':'+p['target_start']:p for p in t.read(t.OUT/'reference-candidates.json')['proposals']}
    t.require(len({p['id'] for p in ablation['proposal_packets']})==803,'duplicate proposal packet')
    for p in ablation['proposal_packets']:
        t.require(t.digest(t.payload(originals[p['id']]))==p['original_proposal_sha256'],'dangling original proposal')
        t.require({e['removed'][0] for e in p['counterfactuals']}==set(CLASSES),'missing ablation class')
        expected=[e['removed'][0] for e in p['counterfactuals'] if p['baseline']['semantic_transport'] and not e['semantic_transport']]
        t.require(expected==p['single_point_dependencies'],'single-point dependency mismatch')
        t.require(p['baseline']['semantic_transport']==(p['baseline']['grade']=='reviewed-strong-proposal'),'grade/transport conflict')
    mapping=t.read(OUT/'effective-map.json')
    t.require(len({r['donor_start'] for r in mapping['records']})==len({r['target_start'] for r in mapping['records']})==len(mapping['records']),'effective injectivity failure')
    t.require(len(mapping['records'])==mapping['counts']['closed']-mapping['counts']['suppressed_or_review_excluded']+mapping['counts']['additions'],'effective arithmetic failure')
    boundary=t.read(OUT/'boundary-completion.json')
    t.require(len({r['id'] for r in boundary['records']})==748,'boundary terminal omission')
    for r in boundary['records']:
        for region in r.get('regions',[]):
            owner=region['target_owner']
            if owner:
                t.require(int(owner['start'],16)<=int(region['target_start'],16)<int(region['target_end_exclusive'],16)<=int(owner['end_exclusive'],16),'region escapes claimed owner')
    for name,count in [('type_contexts',425),('pointer_runs',4939),('globals',2479)]:
        rows=t.read(OUT/'typed-completion.json')[name]
        t.require(len(rows)==count and len({r['id'] for r in rows})==count and all(r['disposition'] for r in rows),'typed terminal mismatch')
    t.verified_freeze(OUT)
    return True

def closed_checks():
    commands=[['python','tools/Fable2PrototypeArchaeology.py','verify'],
              ['python','tools/VerifyFable2PrototypePhase1Consistency.py'],
              ['python','tools/Fable2PrototypeCorrespondence.py','verify','--tool-commit','5f96fcf81bf9511dabadc63326468d9de94f87da'],
              ['python','tools/VerifyFable2PrototypePhase2AConsistency.py'],
              ['python','tools/Fable2FunctionMap.py','validate','out/analysis/BF7300F7E0DEEE91444ACD50FBE69752F5CFD3CF51358186F1B849DF25A8CB00/ghidra-function-map.json'],
              ['python','tools/Verify-Fable2EntrypointClosure.py','--report','out/phase5a/tranche-001/closure-after/entrypoint-closure.json']]
    checks=[]
    for command in commands:
        result=subprocess.run(command,cwd=t.ROOT,capture_output=True,text=True)
        t.require(result.returncode==0,result.stdout+result.stderr)
        checks.append({'command':command,'return_code':0,'status':'pass'})
        print('PASS',' '.join(command),flush=True)
    payloads={key:t.read(t.semantic.OUT/('semantic-'+key+'.json')) for key in ('inventory','xrefs','registrations','index','accepted','review','mapping-review','graph','globals')}
    t.semantic.validate_family(payloads,t.read(t.semantic.P2/'prototype-correspondence-accepted.json')['records'],t.read(t.semantic.DOC/'evidence/semantic-validation.json')['counts'])
    checks.append({'command':['Fable2PrototypeSemantics.validate_family'],'return_code':0,'status':'pass','scope':'All nine bound Phase 2B artifacts and closed counts; branch-specific generator is not rebound.'})
    import Fable2OwnershipCorroboration as owner
    import Fable2IndirectTargets as indirect
    for path in ('docs/fable2-discovery-pipeline/ownership/ownership-ledger.json','docs/fable2-discovery-pipeline/coverage/phase5a-reference-001-ownership/ownership-ledger.json'):
        owner.validate(t.read(path)); checks.append({'command':['Fable2OwnershipCorroboration.validate',path],'return_code':0,'status':'pass'})
    for path in ('out/indirect-targets/fable2-tu1-manual-001/review/xenia-indirect-targets.summary.json','out/indirect-targets/fable2-tu1-manual-002/review/xenia-indirect-targets.summary.json','out/phase5a/tranche-001/merged/xenia-indirect-targets.summary.json'):
        indirect.validate_summary(t.read(path)); checks.append({'command':['Fable2IndirectTargets.validate_summary',path],'return_code':0,'status':'pass'})
    path='out/phase5a/tranche-001/merged/fable2-indirect-targets.import-plan.json'
    indirect.validate_plan(t.read(path)); checks.append({'command':['Fable2IndirectTargets.validate_plan',path],'return_code':0,'status':'pass'})
    t.binding(); t.extra_inputs()
    doc=env('verification',checks=checks,closed_unchanged=True,sdk_preserved=True,
            historical_ownership_result=identity(OUT/'ownership-verification.json'))
    write(OUT/'verification-results.json',doc)
    return doc

GATE_BINDINGS = {
 'A': ('audit_pairs,ablation_stage', 'trust-audit.json,completion/feature-ablation.json', [1,2,3,5,6,7,8,9,10]),
 'B': ('trust_disposition,evaluate_proposal', 'trust-audit.json,completion/feature-ablation.json', [2,3,9,14,18]),
 'C': ('known_cases,ablation_stage', 'known-cases.json,completion/feature-ablation.json', [1,17,18]),
 'D': ('known_cases,ablation_stage', 'known-cases.json,completion/feature-ablation.json', [19,20]),
 'E': ('candidate_stage,profile_function,evaluate_proposal,behavior_features,expand_dependencies', 'reference-candidates.json,completion/feature-ablation.json', [11,12,13,14,15,16,17]),
 'F': ('effective_view,mapping_final', 'completion/effective-map.json,completion/mapping-freeze.json', [21,22,39]),
 'G': ('registration_stage,recon_completion', 'registration.json,completion/recon-completion.json', [24,37]),
 'H': ('secondary_stage,two_hop', 'september-pairs.json,completion/semantic-final.json', [28,29]),
 'I': ('boundary_completion,extend_match,relation_class', 'completion/boundary-completion.json', [20,30,31]),
 'J': ('semantic_stage,verified_freeze', 'completion/semantic-final.json,completion/mapping-freeze.json', [29,39]),
 'K': ('typed_completion,typed_disposition', 'completion/typed-completion.json', [32,33,34]),
 'L': ('script_stage,state_provenance,recon_completion', 'scripts.json,completion/recon-completion.json', [35,36]),
 'M': ('registration_stage,recon_completion', 'registration.json,completion/recon-completion.json', [24,37]),
 'N': ('preservation_stage,preservation_disposition,recon_completion', 'preservation.json,completion/recon-completion.json', [37,38]),
 'O': ('intersection_stage', 'intersections.json,completion/completion-review.json', [25]),
 'safety': ('binding,audit_paths,final_summary', 'completion/verification-results.json', [27,39]),
 'validation': ('closed_checks,verify_terminals,final_summary,ownership_verification,replay_all', 'completion/verification-results.json,completion/ownership-verification.json,completion/replay-results.json', [26,27,28,39]),
 'outputs': ('final_summary,verify_terminals', 'completion/effective-map.json,completion/semantic-final.json,completion/replay-results.json', [26,39]),
}


def code_reference(name):
    for module in (sys.modules[__name__],t):
        fn=getattr(module,name,None)
        if fn is not None:
            path=Path(inspect.getsourcefile(fn)).relative_to(t.ROOT).as_posix()
            return {'path':path,'function':name,'line':inspect.getsourcelines(fn)[1]}
    raise ValueError('Unbound implementing function: '+name)


def final_matrix(check=False):
    coverage=t.read(OUT/'fixture-coverage.json')
    executed=set(t.read(OUT/'test-results.json')['tests'])
    blockers={
      'validation.baseline-bound-ownership':'Exact historical generated/default/fable2_recomp.136.cpp bytes with SHA-256 6053CC0EAC4636AA03AAA26581162B707C37E1B52BEE4C10F205D07C63EBDF59 are absent; only three baseline-bound provenance fields differ.',
      'validation.all-existing-verifiers':'Current validators pass; exact historical ownership JSON replay remains blocked by the hash-bound generated input. The closed Phase 2B generator retains its branch guard and is not rebound.',
      'L.script-bank-parser-or-blocker':'Bounded inventory completed; validated proprietary bank-entry layout is unavailable in the existing supported parsers.',
      'L.game-GUI-startup-states':'Path categories are preserved, but a native Lua-state lifetime/namespace ownership chain is absent.',
      'L.retail-provenance':'Current-runtime script inventory is not an authenticated retail-disc bank and dependency inventory.',
      'M.complete-chain-or-blocker':'The native callback payload is proven, but helper/adapter, native state and corresponding TU1 registration obligations remain unresolved.'}
    rows=[]
    for group,names in REQUIREMENTS.items():
        funcs,files,categories=GATE_BINDINGS[group]
        refs=[identity(t.OUT/p) for p in files.split(',')]
        for name in names.split('|'):
            key=group+'.'+name
            tests=[r for i in categories for r in coverage['records'][i-1]['tests']]
            rows.append({'id':key,'requirement':name,'mandatory':True,
              'status':'blocked-with-evidence' if key in blockers else 'complete',
              'code':[code_reference(f) for f in funcs.split(',')], 'evidence':refs,
              'schema':[{'path':SCHEMA,'applies_to':'completion envelopes'},{'path':'tools/schemas/fable2-prototype-trust-v1.schema.json','applies_to':'original trust envelopes'}],
              'tests':tests,'verifiers':['Fable2PrototypeCompletion.verify_terminals','Fable2PrototypeCompletion.final_summary','Verify-Fable2PrototypeTrust.ps1'],
              'report_section':{'A':'Trust and ablation','C':'Known-case dispositions','D':'Known-case dispositions','I':'Boundary and typed populations','K':'Boundary and typed populations','L':'Registration scripts and preservation','M':'Registration scripts and preservation','N':'Registration scripts and preservation','validation':'Verification and blockers'}.get(group,'Reconciled evidence'),
              'reason':blockers.get(key,'Bound implementation, population evidence and executed controls reconcile this bounded requirement; a negative terminal is not a positive recovery claim.')})
    for row in coverage['records']:
        t.require(all(r['test_id'] in executed for r in row['tests']),'unexecuted matrix fixture')
        rows.append({'id':row['id'],'requirement':row['category'],'mandatory':True,'status':'complete',
                     'code':row['tests'],'evidence':[identity(OUT/'fixture-coverage.json'),identity(OUT/'test-results.json')],
                     'schema':SCHEMA,'tests':row['tests'],'verifiers':['Fable2PrototypeCompletion.test_run'],
                     'report_section':'Fixture coverage','reason':row['evidence_contract']})
    t.require(len(rows)==187 and len({r['id'] for r in rows})==187,'gate population drift')
    doc=env('matrix',stage='final-bounded-blocker-checkpoint',records=rows,
            counts=dict(sorted(collections.Counter(r['status'] for r in rows).items())),phase_complete=False)
    write(t.DOC/'evidence/completion-matrix.json',doc,check)
    lines=['# Phase 2C completion matrix','','187 reconciled gates, including 39 explicit fixture categories. No incomplete or silently omitted rows. Blocked rows name exact missing evidence; they are not passes. Machine bindings are in `evidence/completion-matrix.json`.','',
           '| Gate | Status | Implementing functions / fixtures | Evidence |','| --- | --- | --- | --- |']
    for r in rows:
        lines.append('| '+r['id']+' | '+r['status']+' | '+', '.join(x.get('function',x.get('test_id','')) for x in r['code'])+' | '+', '.join('`'+x['path']+'`' for x in r['evidence'])+' |')
    lines += ['', '## Evidenced blockers','']+[f"- `{r['id']}`: {r['reason']}" for r in rows if r['status']=='blocked-with-evidence']
    write(t.DOC/'completion-matrix.md',('\n'.join(lines)+'\n').encode(),check)
    return doc


def path_audit():
    bad=[]
    pattern=re.compile(r'(?i)(?:[A-Z]:[\\/]+(?:Dev|Users)[\\/]|/C:/Dev/|/tmp/|AppData[\\/]+Local[\\/]+Temp)')
    paths=list((t.ROOT/t.DOC).rglob('*.md'))+list((t.ROOT/t.DOC/'evidence').glob('*.json'))+list((t.ROOT/t.OUT).rglob('*.json'))
    for path in sorted(paths):
        if pattern.search(path.read_text(encoding='utf-8')):
            bad.append(path.relative_to(t.ROOT).as_posix())
    t.require(not bad,'environment-specific evidence paths: '+repr(bad))
    t.audit_paths()
    return len(paths)


def final_summary(check=False):
    verify_terminals()
    t.binding(); t.extra_inputs()
    matrix=final_matrix(check)
    baseline=json.loads(subprocess.check_output(['git','show',CHECKPOINT+':'+(t.DOC/'evidence/validation.json').as_posix()],cwd=t.ROOT))
    counts=copy.deepcopy(baseline['counts'])
    counts.update(effective_map=t.read(OUT/'effective-map.json')['counts'],semantic_v2=t.read(OUT/'semantic-final.json')['counts'],
                  feature_ablation=t.read(OUT/'feature-ablation.json')['counts'],boundary_classes=t.read(OUT/'boundary-completion.json')['counts'],
                  typed_completion=t.read(OUT/'typed-completion.json')['counts'],recon_completion=t.read(OUT/'recon-completion.json')['counts'],
                  completion_gates=matrix['counts'],tests=t.read(OUT/'test-results.json')['run'])
    # Never reuse a provisional total without reconciling the actual population.
    t.require(counts['trust_audit']==t.read(t.OUT/'trust-audit.json')['counts'],'audit summary drift')
    t.require(counts['reference_candidates']==t.read(t.OUT/'reference-candidates.json')['counts'],'candidate summary drift')
    t.require(counts['september']==t.read(t.OUT/'september-pairs.json')['trust_counts'],'secondary summary drift')
    retained={r['donor_start'] for r in t.read(OUT/'effective-map.json')['records']}
    counts['september_two_hop_function_routes']=sum(r['disposition'].startswith('retained-') and r['target_start'] in retained for r in t.read(t.OUT/'september-pairs.json')['trust_dispositions'])
    packets=t.read(OUT/'feature-ablation.json')['proposal_packets']
    counts['proposal_grade_changes']=dict(sorted(collections.Counter(p['original_grade']+' -> '+p['baseline']['grade'] for p in packets).items()))
    artifacts=[identity(p.relative_to(t.ROOT)) for p in sorted((t.ROOT/t.OUT).rglob('*.json'))]
    artifacts += [identity(t.PINS),identity(t.EXTRA_PINS),identity(t.DOC/'evidence/completion-matrix.json')]
    checkpoint_report=subprocess.check_output(['git','show',CHECKPOINT+':'+(t.DOC/'report.md').as_posix()],cwd=t.ROOT).decode()
    known=checkpoint_report.split('## Known-case dispositions\n',1)[1].split('## Limits',1)[0]
    native=checkpoint_report.split('## Native registration reconnaissance\n',1)[1].split('The historical ownership reconstruction',1)[0]
    lines=['# Phase 2C bounded completion pass','',
      '**Phase 2C remains blocked for an unqualified close-out by a precisely identified historical ownership input.** Independent completion work is implemented, terminally reconciled and replayed. No Phase 2D was started. No mapping or name is canonical.','',
      'Build 23 and TU1 are extremely close relatives but are not byte-identical semantic layouts. The three discovered semantic collisions do not invalidate the whole map. Phase 2A exact-image precision was a control result, not measured cross-build precision.','',
      '## Trust and ablation','',
      'All 15,299 mappings have dispositions: 15,296 retained, three suppressed, zero unresolved audit rows. Of 97 data-anchor-supported pairs, 96 retain independently reproduced support and one loses trust without its partial window. The 113 windows comprise nine full-string matches, 103 bounded non-string windows and one same-address/full-string collision; one pair has an interior pointer. A bounded window cannot prove object identity.','',
      'Post-ablation arithmetic: **15,299 - 3 + 86 = 15,382**, a proposed increase of 83 over Phase 2A and no change from the provisional effective count. All 86 strong and 715 probable proposals retain their grades; both same-name physics pairs remain candidates. Every strong entry has an evidence packet and a second machine-policy cross-check, not human approval.','',
      'Ablation covers 803 proposal packets and 99 closed records (97 data-anchor records and the other two suppressions), each across 11 removal classes. Each strong proposal loses transport eligibility without canonicalization, boundary/size, CFG/branch or reference-role gates. Callee and import/helper removal each affect the same 85 proposals; these are overlapping obligations, not independent votes. Internal-region support is a single-point dependency for HammerCombat. Caller, neighbourhood, September and same-generation removal alone downgrade zero strong proposals. All actual additions are generation 1 from retained external seeds. No literal is counted both as normalization and corroboration.','',
      '## Suppressions','',
      '- `0x82631A30 -> 0x82950A98`: Navigator versus Controlled (`T-03503`).\n- `0x828EA448 -> 0x82681198`: TROLL_FOOTSTEP versus DESTROY_ENTITY (`T-05080`).\n- `0x83062950 -> 0x83060C30`: __vspltb versus __vcfsx (`T-13251`).','',
      'Suppression bars semantic transport; it does not disprove generic code reuse or rewrite the original accepted record.','',
      '## Known-case dispositions','',known.strip(),'',
      '## Boundary and typed populations','',
      'All 713 primary contexts (including the prior 51 shared windows, 662 unresolved contexts and both unmatched donors), 33 September cases and two comparator regions have terminal records. Whole-body aligned-window search with reciprocal uniqueness, maximal owner-bounded extension and external control-flow checks yields 480 shared-body evidence records, 266 unresolved-boundary records and two internal-code-region records. Split, merge, outline, inline, thunk and tail recoveries are zero; synthetic positive and adversarial controls distinguish each class. Shared-body here means a bounded exact fragment, not source-lineage confirmation. No boundary relation independently transports semantics.','',
      'Neither unmatched donor `[0x826E3720,0x826E3B34)` nor `[0x82BAD3B8,0x82BAE038)` is explained at function level. No strong/probable proposal has a boundary-size disagreement.','',
      'All 425 type contexts remain insufficient to name constructors. All 4,939 executable-pointer runs lack a proven complete typed object boundary; none is promoted to a vtable. Of 2,479 global contexts, 102 have incompatible object/access evidence and 2,377 lack proven boundaries. Zero complete globals are proposed. Rows bind section/alignment, slots or access roles, readers/writers where proven, cross-build targets and alternate jump-table/callback/import/mixed-data interpretations. Descriptor layout, vptr writers and complete object extent are missing evidence, not inferred facts.','',
      '## Registration scripts and preservation','',native.strip(),'',
      'All 206 constructor shapes retain explicit obligations. Of 2,662 calls, 2,647 have complete names/callback candidates and 15 do not. Zero TU1 command chains are proven: callback payload construction does not prove native state, namespace lifetime or corresponding TU1 consumers.','',
      'All 160 script/interface files are inventoried: 108 supported loose Lua chunks parsed statically, 52 banks/interfaces remain inventory-only. The 54 scripts/scripts_r structural pairs compare bytecode structure and debug information, not semantic identity. Game, runtime, GUI and startup path categories remain separate; native Lua-state ownership is unproven. No supported proprietary bank-entry parser or authenticated retail bank inventory is present.','',
      'All 200 preservation candidates have presence, dependency, grade and portability records: 18 dependency-linked native-dependent candidates, 182 presence-only candidates of unknown portability. E3/demo lexical markers and current-runtime absence are not proof of recoverable historical content or retail absence. SetUseFreeCamera is first-party native evidence; community-only Debug.ToggleFreeCam remains non-accepting. No runnable recovery is claimed.','',
      '## Reconciled evidence','',
      'The frozen semantic pass processes all 51,657 terminals: 118 newly joined versus Phase 2B, 112 filtered corroborations, four unfiltered contextual roles, four target-unconfirmed joins and 51,537 mapping-blocked records. Status totals are exclusive; newly-joined is a comparison count. All 9,600 September pairs are materialized and retained, including 1,847 exact and 7,753 normalized; 9,284 have two-hop function routes, but zero September semantic terminals gain a route. July remains only an implementation control.','',
      'The four unfiltered roles are filesystem assertion, table-index diagnostic, combo-animation parameter and HammerCombat exclusion guard. The frozen mapping hashes are checked before and after semantics; no semantic outcome feeds a mapping grade. There are no upgrades or downgrades from the provisional semantic result.','',
      'Proposal intersections remain 68 closure, 11 coverage and 85 Ghidra; zero ownership, renderer, indirect or historical-crash proposal intersections. Membership prioritizes review only. The complete effective view intersects 4,781 closure, 2,188 coverage, 12,959 Ghidra, 21 ownership and one renderer records. Historical crash membership is not a claim of an open crash. Exact paths and JSON pointers remain in intersections.json.','',
      'The review queue includes all 86 strong proposals and three sorted examples per available lower-grade/subsystem stratum, with explicit available and selected totals and no human approval.','',
      '```json',json.dumps(counts,indent=2,sort_keys=True),'```','',
      '## Fixture coverage','',
      'All 39 required categories bind named executed tests in completion-matrix.json and fixture-coverage.json. Full discovery runs 246 tests with zero failures, errors or skips. Positive synthetic typed/transformation policies do not assert that a real object or transformation was recovered.','',
      '## Verification and blockers','',
      'Full analytical replay is byte-identical across the original and completion evidence populations. Schema validation, terminal counts, injectivity, closed evidence hashes, report/summary/ignored bytes, relative-path and allowlisted Git-delta checks are required by the commands in README.md. The completion matrix has 181 complete and six blocked-with-evidence rows; no incomplete or unclassified row. Four scientific blockers concern parser/state/retail/registration evidence; two verification gates refer to the same missing historical input.','',
      'Historical ownership: the Phase 2B and completion-checkpoint manifests are identical. The original current-input invocation fails `FAIL: stale manifest`. The immutable manifest at `c8a2264500ea32a68d747808d52b7e7820c81b72:fable2_manifest.toml` passes the unchanged input validator when supplied as a read-only Git blob. The human ledger reproduces exactly; JSON differs only in three provenance fields for sub_8279E818. Missing `generated/default/fable2_recomp.136.cpp` SHA-256 `6053CC0EAC4636AA03AAA26581162B707C37E1B52BEE4C10F205D07C63EBDF59` is required for exact historical replay. Current bytes hash to `D25E664A98833BF9433413336AC92A7376102A67049C0FF35F1270E6BDEB44CB`; line references shifted 11964→11977 and 12207→12220. Current ledger/plan semantic validation passes. This is explicitly not an all-green result.','',
      'Neither game was executed. No build, codegen, runtime, renderer, manifest, generated-code, canonical naming, binary, asset, SDK or network operation occurred. Only local Phase 2C analysis/documentation commits were made. The SDK branch, HEAD, tree, remotes, status and fifteen libmspack file hashes remain bound to source-pins.json.','',
      '## Exact artifact bytes','', '| Repository-relative path | Bytes | SHA-256 |','| --- | ---: | --- |']
    lines += [f"| `{r['path']}` | {r['size']} | `{r['sha256']}` |" for r in artifacts]
    write(t.DOC/'report.md',('\n'.join(lines)+'\n').encode(),check)
    implementation=[identity(p.relative_to(t.ROOT)) for p in sorted((t.ROOT/'tools').glob('*PrototypeCompletion.py'))]
    implementation += [identity(Path(p)) for p in ('tools/Fable2PrototypeTrust.py','tools/Verify-Fable2PrototypeTrust.ps1',SCHEMA,'tools/schemas/fable2-prototype-trust-v1.schema.json','tests/test_fable2_prototype_completion.py','tests/test_fable2_prototype_trust.py')]
    implementation += [identity(t.DOC/p) for p in ('README.md','policy.md','review-guide.md','verification.md','next-phase-handoff.md','completion-matrix.md')]
    validation=env('validation',artifacts=artifacts,implementation=implementation,counts=counts,
                   report=identity(t.DOC/'report.md'),phase_complete=False,
                   remaining_blockers=[{'id':r['id'],'reason':r['reason']} for r in matrix['records'] if r['status']=='blocked-with-evidence'],
                   matrix=identity(t.DOC/'evidence/completion-matrix.json'))
    write(t.DOC/'evidence/validation.json',validation,check)
    for r in artifacts+implementation+[validation['report'],validation['matrix']]:
        check_identity(t.ROOT/r['path'],r)
    print('PASS summary and three-way bytes; path audit',path_audit(),flush=True)
    return validation


def replay_all():
    _,images,features,pairs=t.load_inputs()
    rows=t.audit_pairs(images,features,pairs)
    write(t.OUT/'trust-audit.json',t.envelope('audit',source_pins_sha256=t.old.sha256_file(t.ROOT/t.PINS),records=rows,counts=t.audit_counts(rows)),True)
    candidates=t.candidate_stage(images,features,rows,pairs)
    candidates['audit_sha256']=t.old.sha256_file(t.ROOT/t.OUT/'trust-audit.json')
    write(t.OUT/'reference-candidates.json',candidates,True)
    print('PASS replay: closed-map audit and complete candidate population',flush=True)
    write(t.OUT/'september-pairs.json',t.secondary_stage(),True)
    t.freeze_stage(images,pairs,True)
    print('PASS replay: September and original mapping freeze',flush=True)
    v2=t.semantic_stage(images)
    for name,value in {'semantic-v2':v2,'types-globals':t.type_global_stage(images),'scripts':t.script_stage(),
                       'registration':t.registration_stage(images),'preservation':t.preservation_stage(v2),
                       'intersections':t.intersection_stage(images,v2)}.items():
        write(t.OUT/(name+'.json'),value,True)
    print('PASS replay: original downstream populations',flush=True)
    profiles(images,True)
    ablation_stage(images,True)
    boundary_completion(images,True)
    typed_completion(images,True)
    recon_completion(True)
    mapping_final(True)
    write(OUT/'semantic-final.json',t.semantic_stage(images,OUT),True)
    review_final(True)
    fixture_coverage(True)
    ownership_verification(True)
    verify_terminals()
    paths=sorted(p.relative_to(t.ROOT) for p in (t.ROOT/t.OUT).rglob('*.json') if p.name not in ('replay-results.json',))
    doc=env('verification',checks=[{'path':p.as_posix(),'status':'byte-identical'} for p in paths],
            closed_unchanged=True,sdk_preserved=True,scope='Full original mapping/September/downstream and completion analysis recomputed; tests and closed verifier reports separately validated.',
            artifacts=[identity(p) for p in paths])
    write(OUT/'replay-results.json',doc)
    print('PASS full analytical replay',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['matrix-initial','ablation','verify-ablation','boundaries','verify-boundaries','typed','verify-typed','ownership','verify-ownership','mapping','verify-mapping','recon','verify-recon','semantics','verify-semantics','tests','review','checks','summary','verify-summary','replay'])
    args=parser.parse_args()
    if args.command=='matrix-initial':
        matrix_initial()
    elif args.command=='tests':
        test_run()
    elif args.command=='review':
        review_final()
    elif args.command=='checks':
        closed_checks()
    elif args.command in ('summary','verify-summary'):
        final_summary(args.command=='verify-summary')
    elif args.command=='replay':
        replay_all()
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
