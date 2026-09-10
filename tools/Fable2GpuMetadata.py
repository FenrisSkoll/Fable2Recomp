"""NR0B-2 payload-free metadata validation and isolated preparation. Never launches gameplay."""
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
from datetime import datetime, timezone
import Fable2GpuConfig as config

RECORD = struct.Struct('<QQQQII27Q')
HEADER = struct.Struct('<8s64s9Q112s')
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
}
FIELDS = {key: (name, fields.split()) for key, (name, fields) in FIELDS.items()}
OUTCOMES = ['packet_failure', 'predicate_rejected', 'query_rejected', 'unsupported_source',
            'preparation_failure', 'no_op', 'copy_succeeded', 'copy_failed',
            'pipeline_unavailable', 'pipeline_not_ready', 'deferred_main_draw_recorded']
REASONS = ['none', 'deadline', 'swaps', 'decisions', 'records', 'bytes', 'cancelled',
           'shutdown', 'writer_error', 'device_lost', 'invalid_record']
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
        magic, raw_run, process_id, record_bytes, max_records, max_bytes, max_decisions, max_intervals, duration, storage, bookkeeping, reserved = HEADER.unpack(stream.read(256))
        run = raw_run.split(b'\0', 1)[0].decode('ascii')
        if (magic != b'REXMETA1' or not run or len(run) > 63 or not process_id or any(reserved)
                or any(raw_run[len(run):]) or record_bytes != 256
                or not 3 <= max_records <= 100000 or not 768 <= max_bytes <= MAX_BYTES
                or not 1 <= max_decisions <= 20000 or not 1 <= max_intervals <= 3
                or not 1 <= duration <= 5000000000 or size > max_bytes or size // 256 > max_records
                or storage != min(max_records, max_bytes // 256) * 256
                or (run_id is not None and run != run_id) or (pid is not None and process_id != pid)):
            raise ValueError('Invalid/wrong-session metadata header')
        events = []
        for sequence in range(1, size // 256):
            seq, decision, submission, timestamp, type_id, count, *values = RECORD.unpack(stream.read(256))
            if seq != sequence or type_id not in FIELDS or count > 27 or any(values[count:]):
                raise ValueError('Invalid sequence, event type, fields or padding')
            name, names = FIELDS[type_id]
            expected = len(names)
            if count != expected and not (name == 'texture' and count == 5 and values[4] == 0):
                raise ValueError(f'Invalid field count for {name}')
            event = dict(sequence=seq, decision=decision, submission=submission, time_ns=timestamp,
                         type=name, fields=dict(zip(names[:count], values[:count])))
            events.append(event)
    if events[-1]['type'] != 'terminal' or any(e['type'] == 'terminal' for e in events[:-1]):
        raise ValueError('Missing/duplicate terminal')
    terminal = events.pop()
    t = terminal['fields']
    if (terminal['decision'] or terminal['submission'] or t['reason'] not in range(1, len(REASONS))
            or t['event_records'] != len(events) or t['bytes'] != size or t['storage_bytes'] != storage
            or t['decisions'] > max_decisions or t['complete_intervals'] > max_intervals
            or terminal['time_ns'] != t['stop_observed_ns'] or t['stop_observed_ns'] < t['trigger_ns']):
        raise ValueError('Invalid terminal accounting')
    cutoff = min(t['stop_observed_ns'], t['trigger_ns'] + duration) if t['trigger_ns'] else t['stop_observed_ns']
    decisions, hosts, executions, submissions = {}, {}, {}, {}
    intervals, swaps, external = 0, [], Counter()
    active_decision = 0
    previous_time = t['trigger_ns']
    for e in events:
        name, f, d = e['type'], e['fields'], e['decision']
        if not t['trigger_ns'] or not previous_time <= e['time_ns'] <= cutoff:
            raise ValueError('Event outside monotonic observation window')
        previous_time = e['time_ns']
        if name == 'decision':
            if active_decision or d != len(decisions) + 1 or f['opcode'] not in (34, 54) or f['predicate'] not in (0, 1):
                raise ValueError('Invalid/duplicate decision definition')
            decisions[d] = {'id': d, 'interval': intervals, 'begin': e['sequence'], 'events': [], 'outcome': None}
            active_decision = d
        elif d and (d not in decisions or active_decision != d):
            raise ValueError('Missing/closed decision reference')
        elif not d and name not in ('swap', 'completion', 'execute', 'submit', 'submission'):
            external[name] += 1  # Explicit carry-in operation lacking a before-window decision.
        if d:
            decisions[d]['events'].append(e)
        if name == 'outcome':
            if not d or f['outcome'] >= len(OUTCOMES) or decisions[d]['outcome'] is not None:
                raise ValueError('Invalid/duplicate outcome')
            decisions[d]['outcome'] = OUTCOMES[f['outcome']]
            active_decision = 0
        if name in ('shader', 'texture', 'texture_requested', 'sampler') and f['stage'] not in (0, 1):
            raise ValueError('Invalid shader stage')
        if name in ('texture', 'texture_requested', 'sampler') and f['slot'] >= 32:
            raise ValueError('Invalid used texture slot')
        if name == 'shader' and (f['present'] not in (0, 1) or (not f['present'] and (f['xxh3_64'] or f['microcode_bytes'])) or f['microcode_bytes'] % 4):
            raise ValueError('Invalid shader definition')
        if name == 'pipeline' and f['result'] not in range(4):
            raise ValueError('Invalid pipeline result')
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
    if (t['decisions'] != len(decisions) or t['swaps'] != len(swaps)
            or t['complete_intervals'] != max(0, len(swaps) - 1) or t['host_operations'] != len(hosts)):
        raise ValueError('Terminal count mismatch')
    if t['reason'] == 2 and len(swaps) != max_intervals + 1:
        raise ValueError('Swap stop without complete interval bound')
    if t['reason'] == 3 and len(decisions) != max_decisions:
        raise ValueError('Decision stop without decision bound')
    if t['reason'] in (4, 5) and size != storage:
        raise ValueError('Capacity stop without full bounded storage')
    for decision in decisions.values():
        seen = set()
        selected = None
        pipeline = None
        requested_views, prepared_views = set(), set()
        bindings_ok = False
        for e in decision['events']:
            name, f = e['type'], e['fields']
            if name in ('shader', 'texture', 'texture_requested', 'sampler', 'vertex_fetch', 'vertex_layout', 'color', 'depth', 'targets', 'viewport', 'bindings', 'geometry', 'index', 'processed', 'shader_selection', 'fixed_state'):
                key = (name, f.get('stage'), f.get('slot'), f.get('dimension'), f.get('signed'), f.get('binding_index'))
                if key in seen: raise ValueError('Duplicate immutable decision-local definition')
                seen.add(key)
            if name == 'shader_selection':
                selected = f
                for stage, field in ((0, 'vertex_selected'), (1, 'pixel_selected')):
                    if f[field] not in (0, 1): raise ValueError('Invalid shader selection')
                    definition = next((x['fields'] for x in decision['events'] if x['type'] == 'shader' and x['fields']['stage'] == stage), None)
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
        main = [e for e in decision['events'] if e['type'] == 'host' and e['fields']['main_guest_draw']]
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
        for e in d['events']: by_type.setdefault(e['type'], []).append(e)
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
    return {'schema': 'fable2-nr0b2-analysis-v1', 'run_id': run, 'pid': process_id,
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
        recorder_status = (Path(prep['capture']) / 'status.txt').read_text()
        if not recorder_status.startswith('STOPPED:'):
            errors.append('Recorder did not report successful output flush: ' + recorder_status[:1024])
        if not capture['intervals']['complete']: errors.append('No complete consumer interval captured')
        if capture['terminal']['rejected']: errors.append('Recorder reported rejected/lost metadata')
        if capture['terminal']['reason_name'] in ('writer_error', 'device_lost', 'shutdown', 'invalid_record'):
            errors.append('Capture stopped on recorder/device/shutdown failure path')
    except (OSError, ValueError, UnicodeError, struct.error) as error:
        capture = {'structural_validity': 'INVALID OR MISSING', 'error': str(error)}
        errors.append(str(error))
    output = {'schema': 'fable2-nr0b2-session-review-v1', 'run_id': prep['run_id'],
              'process': process, 'configuration': records, 'nr0b1_comparison': comparisons,
              'capture': capture, 'errors': errors, 'user_report': None,
              'supported_title_log_observations': title_lines,
              'writable_after': config.inventory(prep['writable']),
              'source_preserved_baseline_unchanged': True,
              'status': 'CAPTURE INCOMPLETE — SPECIFIC EVIDENCE REQUIRED' if errors else 'CAPTURE PARSED — USER OBSERVATIONS AND REVIEW REQUIRED'}
    config.write_new(session / 'analysis.json', output)
    print(json.dumps({'status': output['status'], 'errors': errors}, indent=2))
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'preflight', 'analyse', 'parse', 'preserve'])
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
    else:
        result = parse_capture(args.capture, args.run_id)
        if args.output: config.write_new(args.output, result)
        else: print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try: main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'NR0B-2 error: {error}', file=sys.stderr)
        sys.exit(1)
