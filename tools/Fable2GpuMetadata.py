"""NR0B-2 payload-free metadata validation and isolated preparation. Never launches gameplay."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import sys
from datetime import datetime, timezone
import Fable2GpuConfig as config

RECORD = struct.Struct('<QQQQII27Q')
HEADER_V1 = struct.Struct('<8s64s9Q112s')
HEADER_V2 = struct.Struct('<8s64s16Q56s')
HEADER = HEADER_V1  # Frozen synthetic-fixture compatibility for REXMETA1.
MAX_BYTES = 32 * 1024 * 1024
FIELDS = {
    1: ('terminal', 'reason trigger_ns stop_observed_ns event_records decisions swaps complete_intervals bytes rejected append_ns append_max_ns host_operations storage_bytes'),
    2: ('decision', 'opcode predicate'),
    3: ('outcome', 'outcome'),
    4: ('geometry', 'primitive count source index_format major_mode query_enabled query_kill query_id query_condition_requested'),
    5: ('shader', 'stage present xxh3_64 microcode_bytes'),
    6: ('pipeline', 'result vertex_modification pixel_modification run_local_handle'),
    7: ('targets', 'pitch_pixels msaa_enum normalized_color_mask host_rtv bound_bits alpha_test alpha_function alpha_to_mask'),
    8: ('color', 'slot edram_base format exponent_bias normalized_mask color_source color_destination color_operation alpha_source alpha_destination alpha_operation host_format'),
    9: ('depth', 'edram_base format enabled write_enabled function stencil_enabled backface_enabled stencil_function stencil_fail stencil_zpass stencil_zfail back_function back_fail back_zpass back_zfail reference read_mask write_mask back_reference back_read_mask back_write_mask host_format'),
    10: ('viewport', 'x y width height z_min_float_bits z_max_float_bits scissor_x scissor_y scissor_width scissor_height'),
    11: ('texture', 'stage slot dimension signed state base_address mip_address format endian pitch_units32 width height depth tiled packed_mips mip_max host_swizzle swizzled_signs run_local_cached_resource base_bytes mip_bytes scaled_resolve outdated_mask descriptor_index special_view'),
    12: ('sampler', 'stage slot binding_index clamp_x clamp_y clamp_z border_color mag_linear min_linear mip_linear anisotropy mip_min mip_base_map'),
    13: ('vertex_fetch', 'slot type address bytes endian'),
    14: ('bindings', 'succeeded'),
    15: ('resolve', 'depth source_base_tiles source_pitch_tiles msaa_enum source_format width height source_x source_y destination_base destination_address destination_bytes destination_format destination_endian destination_pitch destination_height sample_select clear_color clear_depth clear_depth_base_tiles clear_depth_pitch_tiles clear_depth_format'),
    16: ('resolve_result', 'status copied cleared written_address written_bytes'),
    17: ('host', 'kind main_guest_draw offset'),
    18: ('submission', 'open completed frame'),
    19: ('submit', 'signal_hresult is_swap reset_hresult close_hresult'),
    20: ('completion', 'completed awaited'),
    21: ('swap', 'address width height'),
    22: ('shader_selection', 'vertex_selected pixel_selected rasterization vertex_memexport pixel_memexport interpolators color_targets writes_depth active_host_query vertex_float_constants pixel_float_constants vertex_dynamic_constants pixel_dynamic_constants'),
    23: ('index', 'address bytes count format endian'),
    24: ('processed', 'host_primitive host_vertex_shader_type guest_count host_count index_type guest_index_base host_index_format host_index_endian primitive_reset'),
    25: ('texture_requested', 'stage slot dimension signed type base_address mip_address format endian pitch_units32 tiled packed_mips swizzle mip_min mip_max exponent_bias lod_bias width height depth numeric_format sign_x sign_y sign_z sign_w fetch_dimension'),
    26: ('execute', 'kind offset invoked'),
    27: ('fixed_state', 'blend_r_float_bits blend_g_float_bits blend_b_float_bits blend_a_float_bits alpha_ref_float_bits cull_front cull_back clockwise polygon_mode front_polygon_type back_polygon_type offset_front offset_back index_offset index_min index_max'),
    28: ('vertex_layout', 'binding_index slot stride_bytes attribute_count'),
    29: ('state_bundle', ''),
    30: ('state_bundle_ref', 'bundle_id'),
}
FIELDS = {key: (name, fields.split()) for key, (name, fields) in FIELDS.items()}
OUTCOMES = ['packet_failure', 'predicate_rejected', 'query_rejected', 'unsupported_source',
            'preparation_failure', 'no_op', 'copy_succeeded', 'copy_failed',
            'pipeline_unavailable', 'pipeline_not_ready', 'deferred_main_draw_recorded']
REASONS = ['none', 'deadline', 'swaps', 'decisions', 'records', 'bytes', 'cancelled',
           'shutdown', 'writer_error', 'device_lost', 'invalid_record', 'dictionary_capacity']
TERMINAL_V1 = ('reason trigger_ns stop_observed_ns event_records decisions swaps '
               'complete_intervals bytes rejected append_ns append_max_ns host_operations '
               'storage_bytes').split()
TERMINAL_V2 = TERMINAL_V1 + ('dictionary_definitions dictionary_reuses bundle_definitions '
                             'bundle_reuses state_references recorder_owned_bytes '
                             'accepted_foreground_pid').split()
STATE_TYPES = {4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 18, 22, 23, 24, 25, 27, 28}
KINDS = ['invalid', 'draw', 'indexed_draw', 'dispatch', 'copy_buffer', 'copy_resource',
         'copy_texture_region', 'copy_texture', 'clear_color', 'clear_depth', 'clear_uav',
         'begin_query', 'end_query', 'resolve_query']
GAPS = [
    'Shader/resource/geometry/constant payloads and initial attachment contents were not captured.',
    'Pre-window producers and allocation lifetimes are unobserved; guest ranges and handles may alias or be reused.',
    'No title/material/character association or displayed-frame join exists.',
    'Auxiliary operations have kind/order joins; their full resource state is outside this minimum census.',
    'Special texture views may have an unknown descriptor identity; prepared metadata is not a payload validity proof.',
    'Append timing excludes state decoding, renderer execution, worker serialization and scheduler disturbance.',
]


def parse_capture(path, run_id=None, pid=None):
    """Strict framing and immutable decision-local definition checks, with explicit external edges."""
    path = Path(path)
    size = path.stat().st_size
    if size < 512 or size > MAX_BYTES or size % 256:
        raise ValueError('Invalid metadata size/framing')
    with path.open('rb') as stream:
        header_bytes = stream.read(256)
        magic = header_bytes[:8]
        if magic == b'REXMETA1':
            (magic, raw_run, process_id, record_bytes, max_records, max_bytes, max_decisions,
             max_intervals, duration, storage, bookkeeping, reserved) = HEADER_V1.unpack(header_bytes)
            version = 1
            dictionary_slots = bundle_slots = state_reference_capacity = recorder_owned = 0
            transition_capacity = transition_max_bytes = 0
        elif magic == b'REXMETA2':
            (magic, raw_run, process_id, record_bytes, max_records, max_bytes, max_decisions,
             max_intervals, duration, storage, bookkeeping, format_version, dictionary_slots,
             bundle_slots, state_reference_capacity, recorder_owned, transition_capacity,
             transition_max_bytes, reserved) = HEADER_V2.unpack(header_bytes)
            version = 2
        else:
            raise ValueError('Unsupported metadata format magic/version')
        run = raw_run.split(b'\0', 1)[0].decode('ascii')
        if (not run or len(run) > 63 or not process_id or any(reserved)
                or any(raw_run[len(run):]) or record_bytes != 256
                or not 3 <= max_records <= 100000 or not 768 <= max_bytes <= MAX_BYTES
                or not 1 <= max_decisions <= 20000 or not 1 <= max_intervals <= 3
                or not 1 <= duration <= 5000000000 or size > max_bytes or size // 256 > max_records
                or storage != min(max_records, max_bytes // 256) * 256
                or (run_id is not None and run != run_id) or (pid is not None and process_id != pid)):
            raise ValueError('Invalid/wrong-session metadata header')
        if version == 2 and (format_version != 2 or dictionary_slots < 1
                or dictionary_slots > 131072 or dictionary_slots & (dictionary_slots - 1)
                or bundle_slots < 1 or bundle_slots > 32768 or bundle_slots & (bundle_slots - 1)
                or not 1 <= state_reference_capacity <= 512
                or not 5 <= transition_capacity <= 64 or not 512 <= transition_max_bytes <= 4096
                or recorder_owned != storage + (dictionary_slots + bundle_slots) * 4
                                           + state_reference_capacity * 8 + bookkeeping
                or recorder_owned + transition_capacity * transition_max_bytes > MAX_BYTES):
            raise ValueError('Invalid REXMETA2 bounded-storage header')
        events = []
        for sequence in range(1, size // 256):
            seq, decision, submission, timestamp, type_id, count, *values = RECORD.unpack(stream.read(256))
            if seq != sequence or type_id not in FIELDS or count > 27 or any(values[count:]):
                raise ValueError('Invalid sequence, event type, fields or padding')
            name, names = FIELDS[type_id]
            if name == 'terminal':
                names = TERMINAL_V2 if version == 2 else TERMINAL_V1
            expected = len(names)
            dynamic_bundle = version == 2 and name == 'state_bundle' and 5 <= count <= 27
            if (count != expected and not dynamic_bundle
                    and not (name == 'texture' and count == 5 and values[4] == 0)):
                raise ValueError(f'Invalid field count for {name}')
            if name == 'state_bundle':
                names = ['bundle_id', 'total_references', 'chunk_index', 'chunk_count'] + [
                    f'reference_{index}' for index in range(count - 4)]
            event = dict(sequence=seq, decision=decision, submission=submission, time_ns=timestamp,
                         type=name, fields=dict(zip(names[:count], values[:count])))
            events.append(event)
    if events[-1]['type'] != 'terminal' or any(e['type'] == 'terminal' for e in events[:-1]):
        raise ValueError('Missing/duplicate terminal')
    terminal = events.pop()
    t = terminal['fields']
    reason_limit = 11 if version == 1 else len(REASONS)
    if (terminal['decision'] or terminal['submission'] or t['reason'] not in range(1, reason_limit)
            or t['event_records'] != len(events) or t['bytes'] != size or t['storage_bytes'] != storage
            or t['decisions'] > max_decisions or t['complete_intervals'] > max_intervals
            or terminal['time_ns'] != t['stop_observed_ns'] or t['stop_observed_ns'] < t['trigger_ns']):
        raise ValueError('Invalid terminal accounting')
    if version == 2 and (t['recorder_owned_bytes'] != recorder_owned
                         or t['accepted_foreground_pid'] not in (0, process_id)):
        raise ValueError('Invalid REXMETA2 terminal storage/process accounting')
    cutoff = min(t['stop_observed_ns'], t['trigger_ns'] + duration) if t['trigger_ns'] else t['stop_observed_ns']
    decisions, hosts, executions, submissions = {}, {}, {}, {}
    definitions, definition_signatures, bundles, bundle_build = {}, {}, {}, {}
    bundle_reference_records = serialized_bundle_records = 0
    intervals, swaps, external = 0, [], Counter()
    active_decision = 0
    previous_time = t['trigger_ns']
    def validate_state(name, fields):
        if name in ('shader', 'texture', 'texture_requested', 'sampler') and fields['stage'] not in (0, 1):
            raise ValueError('Invalid shader stage')
        if name in ('texture', 'texture_requested', 'sampler') and fields['slot'] >= 32:
            raise ValueError('Invalid used texture slot')
        if name == 'shader' and (fields['present'] not in (0, 1)
                or (not fields['present'] and (fields['xxh3_64'] or fields['microcode_bytes']))
                or fields['microcode_bytes'] % 4):
            raise ValueError('Invalid shader definition')
        if name == 'pipeline' and fields['result'] not in range(4):
            raise ValueError('Invalid pipeline result')
    for e in events:
        name, f, d = e['type'], e['fields'], e['decision']
        if not t['trigger_ns'] or not previous_time <= e['time_ns'] <= cutoff:
            raise ValueError('Event outside monotonic observation window')
        previous_time = e['time_ns']
        type_id = next(key for key, value in FIELDS.items() if value[0] == name)
        if version == 2 and type_id in STATE_TYPES:
            if d:
                raise ValueError('REXMETA2 state definition is decision-local instead of immutable')
            validate_state(name, f)
            signature = (name, tuple(f.items()))
            if signature in definition_signatures:
                raise ValueError('Duplicate equal state definition did not reuse its ID')
            definition_signatures[signature] = e['sequence']
            definitions[e['sequence']] = e
            continue
        if version == 2 and name == 'state_bundle':
            if d:
                raise ValueError('State bundle definition is decision-local')
            serialized_bundle_records += 1
            bundle_id, total = f['bundle_id'], f['total_references']
            chunk, chunks = f['chunk_index'], f['chunk_count']
            references = [f[f'reference_{index}'] for index in range(len(f) - 4)]
            expected_chunks = (total + 22) // 23
            expected_in_chunk = min(23, total - chunk * 23) if chunk < expected_chunks else 0
            if (not total or total > state_reference_capacity or chunks != expected_chunks
                    or chunk >= chunks or len(references) != expected_in_chunk
                    or any(reference not in definitions or reference >= e['sequence']
                           for reference in references)):
                raise ValueError('Invalid or unknown state bundle reference')
            if chunk == 0:
                if bundle_id != e['sequence'] or bundle_id in bundles or bundle_id in bundle_build:
                    raise ValueError('Duplicate/conflicting state bundle definition')
                bundle_build[bundle_id] = []
            elif (bundle_id not in bundle_build or e['sequence'] != bundle_id + chunk
                  or len(bundle_build[bundle_id]) != chunk * 23):
                raise ValueError('Missing, reordered or conflicting state bundle chunk')
            bundle_build[bundle_id].extend(references)
            if chunk + 1 == chunks:
                if len(bundle_build[bundle_id]) != total:
                    raise ValueError('Truncated state bundle definition')
                bundles[bundle_id] = bundle_build.pop(bundle_id)
            continue
        if name == 'decision':
            if active_decision or d != len(decisions) + 1 or f['opcode'] not in (34, 54) or f['predicate'] not in (0, 1):
                raise ValueError('Invalid/duplicate decision definition')
            decisions[d] = {'id': d, 'interval': intervals, 'begin': e['sequence'],
                            'events': [], 'state_events': [], 'outcome': None}
            active_decision = d
        elif d and (d not in decisions or active_decision != d):
            raise ValueError('Missing/closed decision reference')
        elif not d and name not in ('swap', 'completion', 'execute', 'submit', 'submission'):
            external[name] += 1  # Explicit carry-in operation lacking a before-window decision.
        if d:
            decisions[d]['events'].append(e)
        if version == 2 and name == 'state_bundle_ref':
            bundle_id = f['bundle_id']
            if not d or bundle_id not in bundles or decisions[d].get('bundle_id') is not None:
                raise ValueError('Missing, unknown or duplicate decision state bundle reference')
            decisions[d]['bundle_id'] = bundle_id
            bundle_reference_records += 1
            for reference in bundles[bundle_id]:
                definition = definitions[reference]
                decisions[d]['state_events'].append({**definition, 'decision': d,
                    'submission': e['submission'], 'time_ns': e['time_ns'],
                    'definition_sequence': reference,
                    'bundle_reference_sequence': e['sequence']})
        if name == 'outcome':
            if not d or f['outcome'] >= len(OUTCOMES) or decisions[d]['outcome'] is not None:
                raise ValueError('Invalid/duplicate outcome')
            decisions[d]['outcome'] = OUTCOMES[f['outcome']]
            active_decision = 0
        if version == 1 and type_id in STATE_TYPES:
            validate_state(name, f)
        if name == 'swap':
            if d: raise ValueError('Swap nested inside a decision')
            swaps.append(e)
            intervals += 1
        if name in ('host', 'execute'):
            if f['kind'] not in range(1, len(KINDS)) or not e['submission'] or f['offset'] % 8:
                raise ValueError('Invalid operation identity')
            target = hosts if name == 'host' else executions
            key = (e['submission'], f['offset'])
            if key in target: raise ValueError('Duplicate operation identity')
            target[key] = e
            if name == 'execute' and key in hosts and hosts[key]['fields']['kind'] != f['kind']:
                raise ValueError('Operation kind changed across deferred/native join')
        if name == 'submit':
            if not e['submission'] or e['submission'] in submissions:
                raise ValueError('Invalid/duplicate submission issue')
            submissions[e['submission']] = e
    if bundle_build:
        raise ValueError('Truncated state bundle at capture end')
    if (t['decisions'] != len(decisions) or t['swaps'] != len(swaps)
            or t['complete_intervals'] != max(0, len(swaps) - 1) or t['host_operations'] != len(hosts)):
        raise ValueError('Terminal count mismatch')
    if version == 2:
        referenced_state = sum(len(bundles[e['fields']['bundle_id']])
                               for e in events if e['type'] == 'state_bundle_ref')
        if (t['dictionary_definitions'] != len(definitions)
                or t['bundle_definitions'] != len(bundles)
                or t['bundle_reuses'] != bundle_reference_records - len(bundles)
                or t['state_references'] != referenced_state
                or t['dictionary_reuses'] + t['dictionary_definitions'] < referenced_state):
            raise ValueError('REXMETA2 dictionary/reference terminal mismatch')
    if t['reason'] == 2 and len(swaps) != max_intervals + 1:
        raise ValueError('Swap stop without complete interval bound')
    if t['reason'] == 3 and len(decisions) != max_decisions:
        raise ValueError('Decision stop without decision bound')
    if t['reason'] in (4, 5) and size != storage and (version == 1 or not t['rejected']):
        raise ValueError('Capacity stop without full bounded storage')
    if version == 2 and t['reason'] == 11 and not t['rejected']:
        raise ValueError('Dictionary-capacity stop without reported loss')
    def semantic_events(decision):
        return decision['state_events'] + decision['events']
    for decision in decisions.values():
        seen = set()
        selected = None
        pipeline = None
        requested_views, prepared_views = set(), set()
        bindings_ok = False
        for e in semantic_events(decision):
            name, f = e['type'], e['fields']
            if name in ('shader', 'texture', 'texture_requested', 'sampler', 'vertex_fetch', 'vertex_layout', 'color', 'depth', 'targets', 'viewport', 'bindings', 'geometry', 'index', 'processed', 'shader_selection', 'fixed_state'):
                key = (name, f.get('stage'), f.get('slot'), f.get('dimension'), f.get('signed'), f.get('binding_index'))
                if key in seen: raise ValueError('Duplicate immutable decision-local definition')
                seen.add(key)
            if name == 'shader_selection':
                selected = f
                for stage, field in ((0, 'vertex_selected'), (1, 'pixel_selected')):
                    if f[field] not in (0, 1): raise ValueError('Invalid shader selection')
                    definition = next((x['fields'] for x in semantic_events(decision) if x['type'] == 'shader' and x['fields']['stage'] == stage), None)
                    if f[field] and (not definition or not definition['present']):
                        raise ValueError('Selected shader has no present definition')
            if name == 'pipeline':
                if (pipeline is None and f['result'] != 0) or (pipeline is not None and (pipeline['result'] != 0 or f['result'] == 0)):
                    raise ValueError('Invalid pipeline result ordering')
                pipeline = f
            if name == 'bindings':
                if f['succeeded'] not in (0, 1): raise ValueError('Invalid binding result')
                bindings_ok = bool(f['succeeded'])
            if name in ('texture', 'texture_requested', 'sampler'):
                if ('shader', f['stage'], None, None, None, None) not in seen or not selected or not selected['vertex_selected' if f['stage'] == 0 else 'pixel_selected']:
                    raise ValueError('Used binding lacks selected shader definition')
                if not pipeline or pipeline['result'] != 3:
                    raise ValueError('Used binding before successful pipeline preparation')
                view = (f['stage'], f['slot'], f.get('dimension'), f.get('signed'))
                if name == 'texture_requested': requested_views.add(view)
                if name == 'texture':
                    if view not in requested_views: raise ValueError('Prepared view without requested definition')
                    if f['state'] not in (0, 1, 2): raise ValueError('Invalid prepared view state')
                    prepared_views.add(view)
            if name == 'host' and f['main_guest_draw']:
                if f['kind'] not in (1, 2) or not selected or not pipeline or pipeline['result'] != 3 or not bindings_ok:
                    raise ValueError('Main draw lacks pipeline/shader selection')
                if requested_views != prepared_views: raise ValueError('Main draw has incomplete prepared view definitions')
                for required in ('geometry', 'processed', 'targets', 'depth', 'viewport', 'bindings'):
                    if not any(k[0] == required for k in seen):
                        raise ValueError(f'Main draw lacks carry-in {required}')
        main = [e for e in semantic_events(decision) if e['type'] == 'host' and e['fields']['main_guest_draw']]
        if decision['outcome'] == OUTCOMES[10] and not main:
            raise ValueError('Main-draw outcome without recorded operation')
        if main and decision['outcome'] not in (None, OUTCOMES[10]):
            raise ValueError('Main draw contradicts decision outcome')
    completions = [e for e in events if e['type'] == 'completion']
    outcome_counts = Counter(d['outcome'] or 'open_at_stop' for d in decisions.values())
    missing_execution = [list(k) for k in hosts if k not in executions]
    external_execution = [list(k) for k in executions if k not in hosts]
    shader_pairs = Counter()
    combinations = Counter()
    candidates = []
    for d in decisions.values():
        by_type = {}
        for e in semantic_events(d): by_type.setdefault(e['type'], []).append(e)
        shader = {e['fields']['stage']: e['fields'] for e in by_type.get('shader', [])}
        selection = by_type.get('shader_selection', [{}])[0].get('fields', {})
        pair = tuple(f"{shader[s]['xxh3_64']:016X}" if s in shader and selection.get('vertex_selected' if s == 0 else 'pixel_selected') else 'unselected_or_unobserved' for s in (0, 1))
        shader_pairs[' / '.join(pair)] += 1
        textures = [e['fields'] for e in by_type.get('texture', [])]
        geometry = by_type.get('geometry', [{}])[0].get('fields', {})
        target = [e['fields'] for e in by_type.get('targets', [])]
        combination = json.dumps({'shaders': pair, 'views': [{k: v for k, v in f.items() if k not in ('run_local_cached_resource', 'descriptor_index', 'outdated_mask')} for f in textures], 'targets': target}, sort_keys=True)
        combinations[combination] += 1
        if (d['outcome'] == OUTCOMES[10] and 1 <= d['interval'] < len(swaps)
                and by_type.get('index') and textures and selection.get('pixel_selected')
                and not geometry.get('query_enabled', 1) and not geometry.get('query_condition_requested', 1)
                and all(f['state'] == 1 and f.get('run_local_cached_resource') and not f.get('special_view')
                        and f.get('descriptor_index') not in (2**32-1, 2**64-1) for f in textures)
                and not any(selection.get(k, 1) for k in ('vertex_memexport', 'pixel_memexport', 'active_host_query'))):
            main = [e for e in by_type.get('host', []) if e['fields']['main_guest_draw']]
            joins = [(e['submission'], e['fields']['offset']) for e in main]
            if all(k in executions and executions[k]['fields']['invoked'] and k[0] in submissions for k in joins):
                candidates.append((len(textures), d['id'], by_type))
    candidate = None
    if candidates and not t['rejected']:
        _, decision_id, by_type = min(candidates, key=lambda item: (item[0], item[1]))
        candidate = {'run_id': run, 'decision': decision_id, 'interval': decisions[decision_id]['interval'],
                     'qualification': 'further evidence collection only; payload/initial-content/lifetime dependencies unresolved',
                     'records': by_type, 'remaining': GAPS}
    result = {'schema': 'fable2-nr0b2-analysis-v1', 'run_id': run, 'pid': process_id,
            'capture_identity': config.identity(path), 'structural_validity': 'VALID',
            'terminal': {**t, 'reason_name': REASONS[t['reason']], 'logical_cutoff_ns': cutoff,
                         'deadline_service_lag_ns': max(0, t['stop_observed_ns'] - (t['trigger_ns'] + duration))},
            'storage': {'preallocated_bytes': storage, 'fixed_object_bookkeeping_bytes': bookkeeping,
                        'external_overhead': 'one standard-library thread/OS stack, bounded <=1024-character paths and FILE buffering; no metadata queue or dictionary'},
            'intervals': {'initial_partial': True, 'complete': max(0, len(swaps) - 1),
                          'final_partial': t['reason'] != 2, 'boundaries': swaps},
            'decision_outcomes': dict(outcome_counts), 'external_decision_events': dict(external),
            'shader_pairs': dict(shader_pairs), 'binding_attachment_combinations': [{'metadata': json.loads(k), 'decisions': v} for k, v in combinations.most_common()],
            'host_operation_counts': dict(Counter(KINDS[e['fields']['kind']] for e in hosts.values())),
            'native_operations_invoked': sum(e['fields']['invoked'] for e in executions.values()),
            'submissions': list(submissions.values()), 'completion_observations': completions,
            'resolves': [e for e in events if e['type'].startswith('resolve')],
            'open_edges': {'decisions': [d['id'] for d in decisions.values() if d['outcome'] is None],
                           'native_execution_unobserved': missing_execution,
                           'deferred_recording_before_window_or_external': external_execution,
                           'submission_unobserved': sorted({k[0] for k in hosts} - submissions.keys()),
                           'completion_unobserved': sorted(s for s in submissions if not any(e['fields']['completed'] != 2**64-1 and e['fields']['completed'] >= s for e in completions))},
            'candidate': candidate, 'dependency_completeness': 'UNRESOLVED',
            'gameplay': 'USER REPORT REQUIRED', 'visual_correctness': 'NOT ESTABLISHED',
            'disturbance': 'UNMEASURED IN GAMEPLAY', 'gaps': GAPS}
    if version == 2:
        result['schema'] = 'fable2-nr0b2-analysis-v2'
        result['format'] = {'magic': 'REXMETA2', 'version': 2}
        result['storage'] = {
            'serialized_capacity_bytes': storage,
            'fixed_object_bookkeeping_bytes': bookkeeping,
            'definition_lookup_bytes': dictionary_slots * 4,
            'bundle_lookup_bytes': bundle_slots * 4,
            'decision_reference_workspace_bytes': state_reference_capacity * 8,
            'recorder_owned_bytes': recorder_owned,
            'transition_history_max_bytes': transition_capacity * transition_max_bytes,
            'external_overhead': ('one standard-library thread/OS stack, bounded paths and '
                                  'FILE buffering; transition history is bounded separately')}
        serialized_state = len(definitions) + serialized_bundle_records + bundle_reference_records
        result['dictionary'] = {
            'immutable_definitions': len(definitions),
            'definition_reuses': t['dictionary_reuses'],
            'state_bundles': len(bundles),
            'bundle_definition_records': serialized_bundle_records,
            'bundle_reference_records': bundle_reference_records,
            'bundle_reuses': t['bundle_reuses'],
            'logical_state_references': t['state_references'],
            'serialized_state_records': serialized_state,
            'definition_record_savings': t['state_references'] - serialized_state,
            'scope': ('exact decoded metadata equality within this run; no resource lifetime or '
                      'cross-run identity claim')}
        result['record_accounting'] = {
            'event_records': t['event_records'], 'total_records': t['event_records'] + 2,
            'bytes': t['bytes'], 'max_records': max_records, 'max_bytes': max_bytes}
    return result


def parse_transitions(path, run_id, pid, capture=None):
    """Read the bounded atomically published control history in sequence order."""
    path = Path(path)
    if not path.is_dir():
        raise ValueError('Missing transition history')
    if any(path.glob('*.tmp')):
        raise ValueError('Incomplete transition publication')
    files = sorted(path.glob('*.json'))
    if not files or len(files) > 64:
        raise ValueError('Missing or oversized transition history')
    transitions = []
    allowed = {'READY', 'STARTED', 'STOPPED', 'ERROR', 'CANCELLED', 'REJECTED'}
    for sequence, item in enumerate(files, 1):
        if item.stat().st_size > 4096:
            raise ValueError('Oversized transition record')
        try:
            record = json.loads(item.read_text(encoding='utf-8'))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError('Malformed transition record') from error
        transition = record.get('transition')
        expected_name = f'{sequence:016d}-{transition}.json'
        if (item.name != expected_name or record.get('schema') != 'rex-gpu-metadata-transition-v1'
                or record.get('run_id') != run_id or record.get('pid') != pid
                or record.get('sequence') != sequence or transition not in allowed
                or not isinstance(record.get('recorder_monotonic_ns'), int)
                or not isinstance(record.get('wall_utc_unix_ns'), int)
                or not isinstance(record.get('correlation_monotonic_ns'), int)
                or record.get('clock_correlation') !=
                    'consecutive control-worker samples; scheduler precision only'
                or record.get('wall_utc_unix_ns', 0) <= 0
                or record.get('correlation_monotonic_ns', 0) <= 0):
            raise ValueError('Invalid, wrong-session or out-of-sequence transition')
        transitions.append(record)
    kinds = [record['transition'] for record in transitions]
    if any(now['recorder_monotonic_ns'] < before['recorder_monotonic_ns']
           for before, now in zip(transitions, transitions[1:])):
        raise ValueError('Transition monotonic order regressed')
    initialization_error = kinds == ['ERROR']
    if (not initialization_error and
            (kinds[0] != 'READY' or kinds.count('READY') != 1 or kinds.count('STARTED') > 1)):
        raise ValueError('Invalid READY/STARTED transition order')
    final = kinds[-1]
    if final not in ('STOPPED', 'CANCELLED', 'ERROR') or any(
            kind in ('STOPPED', 'CANCELLED', 'ERROR') for kind in kinds[:-1]):
        raise ValueError('Invalid final control transition')
    started = next((record for record in transitions if record['transition'] == 'STARTED'), None)
    if started:
        if (kinds.index('STARTED') <= kinds.index('READY')
                or started.get('foreground_pid') != pid
                or started.get('trigger_accepted') is not True):
            raise ValueError('Invalid accepted STARTED transition')
    if final == 'STOPPED' and transitions[-1].get('output_flushed') is not True:
        raise ValueError('STOPPED was published without successful flush')
    if final == 'CANCELLED' and (transitions[-1].get('output_flushed') is not True
                                 or transitions[-1].get('terminal_reason_name') != 'cancelled'):
        raise ValueError('Invalid CANCELLED transition')
    if final == 'ERROR' and transitions[-1].get('output_flushed') is not False:
        raise ValueError('ERROR incorrectly claims successful flush')
    if capture is not None:
        terminal = capture['terminal']
        if not started or started['recorder_monotonic_ns'] != terminal['trigger_ns']:
            raise ValueError('STARTED does not match accepted capture trigger')
        if final != ('CANCELLED' if terminal['reason_name'] == 'cancelled' else 'STOPPED'):
            raise ValueError('Final transition disagrees with capture terminal')
        if (transitions[-1]['recorder_monotonic_ns'] != terminal['stop_observed_ns']
                or transitions[-1].get('terminal_reason') != terminal['reason']
                or transitions[-1].get('terminal_reason_name') != terminal['reason_name']):
            raise ValueError('Final transition does not match capture stop')
    return transitions


def estimate_v2_density_from_v1(path):
    """Project exact REXMETA1 event order through the v2 state interning rules."""
    path = Path(path)
    parse_capture(path)  # Require a structurally valid frozen input first.
    data = path.read_bytes()
    if data[:8] != b'REXMETA1':
        raise ValueError('Density projection requires REXMETA1 input')
    records = list(struct.iter_unpack(RECORD.format, data[256:-256]))
    definitions, bundles, pending = {}, {}, []
    type_counts, distinct = Counter(), {}
    non_state = bundle_definition_records = bundle_references = 0
    for record in records:
        type_id, count = record[4], record[5]
        values = tuple(record[6:6 + count])
        type_counts[FIELDS[type_id][0]] += 1
        if type_id in STATE_TYPES:
            key = (type_id, values)
            distinct.setdefault(FIELDS[type_id][0], set()).add(values)
            definitions.setdefault(key, len(definitions) + 1)
            pending.append(definitions[key])
        else:
            if type_id == 3 and pending:
                bundle = tuple(pending)
                if bundle not in bundles:
                    bundles[bundle] = len(bundles) + 1
                    bundle_definition_records += math.ceil(len(bundle) / 23)
                bundle_references += 1
                pending = []
            non_state += 1
    if pending:
        bundle = tuple(pending)
        if bundle not in bundles:
            bundle_definition_records += math.ceil(len(bundle) / 23)
        bundle_references += 1
    projected = len(definitions) + bundle_definition_records + bundle_references + non_state
    original = len(records)
    return {
        'schema': 'fable2-nr0b2-v1-to-v2-density-projection-v1',
        'source': config.identity(path), 'original_event_records': original,
        'projected_event_records': projected, 'projected_total_records': projected + 2,
        'event_record_reduction': original - projected,
        'event_record_reduction_percent': round((original - projected) * 100 / original, 3),
        'immutable_definitions': len(definitions), 'distinct_state_bundles': len(bundles),
        'bundle_definition_records': bundle_definition_records,
        'bundle_reference_records': bundle_references, 'ordered_non_state_records': non_state,
        'event_type_counts': dict(type_counts),
        'distinct_exact_state_tuples': {name: len(values) for name, values in distinct.items()},
        'scope': ('exact offline projection of retained metadata events; no runtime timing, '
                  'resource lifetime or payload claim')}


def initial(repo):
    return json.loads((repo / 'out/nr0b2/initial-state.json').read_text())


def preserve_check(repo, sdk):
    before = initial(repo)
    if config.identity(repo / 'fable2_manifest.toml') != before['manifest']:
        raise ValueError('Unrelated manifest edit changed')
    for path, identity in before['libmspack'].items():
        if config.identity(sdk / 'thirdparty/libmspack' / path) != identity:
            raise ValueError(f'Unrelated libmspack file changed: {path}')
    for path, identity in before['historical_reports'].items():
        if config.identity(repo / path) != identity:
            raise ValueError(f'Historical NR0B-1 report changed: {path}')
    for key in ('source', 'preserved'):
        if config.inventory(before[key]) != before['save_inventory']:
            raise ValueError(f'Original {key} checkpoint changed')


def prepare(repo, sdk, run_id):
    if not run_id or len(run_id) > 63 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.' for c in run_id):
        raise ValueError('Invalid run ID')
    session = repo / 'out/nr0b2/sessions' / run_id
    preserved = repo / 'out/nr0b2/checkpoints' / run_id / 'user-data'
    if session.exists() or preserved.parent.exists():
        raise ValueError('Session/checkpoint already exists; no reuse')
    preserve_check(repo, sdk)
    before = initial(repo)
    source = Path(before['preserved'])
    baseline = repo / 'out/build/win-amd64-release'
    for target in (session, preserved):
        subprocess.run(['git', '-C', str(repo), 'check-ignore', '-q', str(target)], check=True)
    for name, expected in before['baseline_artifacts'].items():
        if config.identity(baseline / name) != expected: raise ValueError('Baseline changed: ' + name)
    session.mkdir(parents=True)
    preserved.parent.mkdir(parents=True)
    config.guarded_copy(source, preserved, before['save_inventory'])
    writable = session / 'user-data'
    config.guarded_copy(preserved, writable, before['save_inventory'])
    runtime = session / 'runtime'
    runtime.mkdir()
    staged = {}
    for name in before['baseline_artifacts']:
        origin = (sdk / 'out/win-amd64/Release' if name in ('rexruntime.dll', 'rexgpu-xenos.dll') else baseline) / name
        expected = config.identity(origin)
        shutil.copy2(origin, runtime / name)
        if config.identity(runtime / name) != expected: raise ValueError('Staging mismatch')
        staged[name] = {**expected, 'path': str(runtime / name), 'source': str(origin)}
    if (baseline / 'fable2.toml').exists(): raise ValueError('Unexpected baseline config; preserve session for review')
    prep = {'schema': 'fable2-nr0b2-preparation-v1', 'run_id': run_id,
            'prepared_utc': datetime.now(timezone.utc).isoformat(), 'session': str(session),
            'fable': config.repository(repo), 'sdk': config.repository(sdk),
            'source': str(source), 'preserved': str(preserved), 'writable': str(writable),
            'save_inventory': before['save_inventory'], 'baseline': str(baseline),
            'baseline_artifacts': before['baseline_artifacts'], 'staged': staged,
            'required_modules': ['fable2.exe', 'rexruntime.dll', 'rexgpu-xenos.dll'],
            'optional_modules': {'TracyClient.dll': 'Release import audit required; staged only'},
            'configuration': {'path': str(runtime / 'fable2.toml'), 'identity': None},
            'capture': str(session / 'capture'),
            'cache': {'root': str(writable / 'cache'), 'state': 'copied protected checkpoint cache',
                      'driver_cache': 'unknown, unmanaged'},
            'build': {'configuration': 'win-amd64-release; D3D12 ON; Vulkan OFF',
                      'targets': ['rexruntime', 'rexgpu-xenos', 'unit_tests'],
                      'executable': 'unchanged accepted Release EXE; no Fable C++/ABI/codegen input change'}}
    config.write_new(session / 'preparation.json', prep)
    preflight(session)
    return prep


def preflight(session, after=False):
    prep = json.loads((session / 'preparation.json').read_text(encoding='utf-8-sig'))
    if Path(prep['session']).resolve() != session.resolve(): raise ValueError('Session root mismatch')
    if not after and ((session / 'launch.claim').exists() or Path(prep['capture']).exists()):
        raise ValueError('Used session/capture root; refuse relaunch')
    config.check_preflight(prep, after=after)
    preserve_check(Path(prep['fable']['root']), Path(prep['sdk']['root']))
    if (Path(prep['baseline']) / 'fable2.toml').exists(): raise ValueError('Baseline configuration changed')
    return prep


def analyse(session):
    prep = preflight(session, after=True)
    process = json.loads((session / 'process.json').read_text(encoding='utf-8-sig'))
    required = {**prep, 'staged': {k: v for k, v in prep['staged'].items() if k in prep['required_modules']}}
    errors = config.validate_loaded(required, process)
    errors += process.get('reporting_errors', [])
    title_lines = []
    def log_lines(stream):
        for line in stream:
            if len(title_lines) < 16 and any(marker in line for marker in ('XEX patch applied successfully:', 'Initializing shader storage for title', 'Loading XEX image:')):
                title_lines.append(line.strip()[:2048])
            yield line
    with Path(process['log']).open(encoding='utf-8-sig', errors='replace') as stream:
        records, config_errors = config.parse_records(log_lines(stream), prep['run_id'])
    errors += config_errors
    if records.get('shader-storage', {}).get('title_id') != '0x4D5307F1':
        errors.append('Fable title identity missing')
    if not any('0.0.0.26' in line and '0.0.1.26' in line for line in title_lines):
        errors.append('Successful TU1 patch transition requires review')
    accepted = json.loads((Path(prep['fable']['root']) / 'out/nr0b1/sessions/nr0b1-oakfield-20260910-001/effective-report.json').read_text())['records']
    comparisons = {}
    for stage in ('device', 'context', 'shared-memory', 'pipeline-policy', 'requested'):
        before, now = accepted.get(stage, {}), records.get(stage, {})
        differences = {k: {'nr0b1': v, 'nr0b2': now.get(k)} for k, v in before.items() if now.get(k) != v}
        comparisons[stage] = differences
        if differences: errors.append(f'Configuration differences require review: {stage}')
    roots = records.get('runtime-paths', {})
    for field, expected in (('user_data_root', prep['writable']), ('cache_root', prep['cache']['root']),
                            ('game_data_root', str(Path(prep['fable']['root']) / 'assets/runtime')),
                            ('update_data_root', str(Path(prep['fable']['root']) / 'assets/update'))):
        if Path(roots.get(field, '')).resolve() != Path(expected).resolve(): errors.append(f'Effective root mismatch: {field}')
    try:
        capture = parse_capture(Path(prep['capture']) / 'metadata.bin', prep['run_id'], process['pid'])
        transition_history = None
        if capture.get('format', {}).get('version') == 2:
            transition_history = parse_transitions(
                Path(prep['capture']) / 'transitions', prep['run_id'], process['pid'], capture)
            observed = [item.get('record') for item in process.get('recorder_transitions', [])]
            if observed != transition_history:
                errors.append('Helper did not durably replay every recorder transition')
        status_path = Path(prep['capture']) / 'status.txt'
        if capture.get('format', {}).get('version') != 2:
            recorder_status = status_path.read_text()
            if not recorder_status.startswith('STOPPED:'):
                errors.append('Recorder did not report successful output flush: ' + recorder_status[:1024])
        if not capture['intervals']['complete']: errors.append('No complete consumer interval captured')
        if capture['terminal']['rejected']: errors.append('Recorder reported rejected/lost metadata')
        if capture['terminal']['reason_name'] in ('records', 'bytes', 'dictionary_capacity'):
            errors.append('Capture ended on metadata capacity rather than an interval/deadline bound')
        if capture['terminal']['reason_name'] in ('writer_error', 'device_lost', 'shutdown', 'invalid_record'):
            errors.append('Capture stopped on recorder/device/shutdown failure path')
    except (OSError, ValueError, UnicodeError, struct.error) as error:
        capture = {'structural_validity': 'INVALID OR MISSING', 'error': str(error)}
        transition_history = None
        errors.append(str(error))
    output = {'schema': 'fable2-nr0b2-session-review-v1', 'run_id': prep['run_id'],
              'process': process, 'configuration': records, 'nr0b1_comparison': comparisons,
              'capture': capture, 'transition_history': transition_history,
              'errors': errors, 'user_report': None,
              'supported_title_log_observations': title_lines,
              'writable_after': config.inventory(prep['writable']),
              'source_preserved_baseline_unchanged': True,
              'status': 'CAPTURE INCOMPLETE — SPECIFIC EVIDENCE REQUIRED' if errors else 'CAPTURE PARSED — USER OBSERVATIONS AND REVIEW REQUIRED'}
    config.write_new(session / 'analysis.json', output)
    print(json.dumps({'status': output['status'], 'errors': errors}, indent=2))
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'preflight', 'analyse', 'parse', 'preserve', 'density'])
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--sdk', type=Path, default=Path('C:/Dev/rexglue-sdk-v0.10'))
    parser.add_argument('--session', type=Path)
    parser.add_argument('--run-id')
    parser.add_argument('--capture', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare': print(prepare(args.repo, args.sdk, args.run_id)['session'])
    elif args.action == 'preflight': preflight(args.session); print('NR0B-2 preflight PASS')
    elif args.action == 'preserve': preserve_check(args.repo, args.sdk); print('Preservation PASS')
    elif args.action == 'analyse': analyse(args.session)
    elif args.action == 'density':
        print(json.dumps(estimate_v2_density_from_v1(args.capture), indent=2))
    else:
        result = parse_capture(args.capture, args.run_id)
        if args.output: config.write_new(args.output, result)
        else: print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try: main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'NR0B-2 error: {error}', file=sys.stderr)
        sys.exit(1)
