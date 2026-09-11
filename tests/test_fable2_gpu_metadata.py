"""Synthetic metadata, not gameplay/equivalence evidence."""
import copy
import json
import importlib.util
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import Fable2GpuMetadata as gpu


def event(name, fields, decision=0, submission=7):
    type_id = next(k for k, (n, _) in gpu.FIELDS.items() if n == name)
    return [decision, submission, type_id, fields]


def fixture(events, reason=6):
    count = len(events)
    decisions = sum(e[2] == 2 for e in events)
    swaps = sum(e[2] == 21 for e in events)
    hosts = sum(e[2] == 17 for e in events)
    header = gpu.HEADER.pack(b'REXMETA1', b'synthetic', 42, 256, 100000,
                             gpu.MAX_BYTES, 20000, 3, 5000000000, 25600000, 200, bytes(112))
    records = []
    for seq, (decision, submission, type_id, fields) in enumerate(events, 1):
        records.append(gpu.RECORD.pack(seq, decision, submission, 100 + seq, type_id,
                                       len(fields), *(fields + [0] * (27 - len(fields)))))
    fields = [reason, 100, 100 + count, count, decisions, swaps, max(0, swaps - 1),
              (count + 2) * 256, 0, 0, 0, hosts, 25600000]
    records.append(gpu.RECORD.pack(count + 1, 0, 0, 100 + count, 1, len(fields),
                                   *(fields + [0] * (27 - len(fields)))))
    return header + b''.join(records)


def fixture_v2(events, reason=6):
    wire, definitions, bundles, state_references = [], {}, {}, []
    definition_reuses = bundle_reuses = logical_references = 0

    def append(item):
        wire.append(item)
        return len(wire)

    for item in events:
        decision, submission, type_id, fields = item
        if type_id in gpu.STATE_TYPES:
            key = (type_id, tuple(fields))
            if key in definitions:
                definition_reuses += 1
            else:
                definitions[key] = append([0, submission, type_id, fields])
            state_references.append(definitions[key])
            continue
        if type_id == 3 and state_references:
            key = tuple(state_references)
            if key in bundles:
                bundle_reuses += 1
                bundle_id = bundles[key]
            else:
                bundle_id = len(wire) + 1
                bundles[key] = bundle_id
                chunks = (len(key) + 22) // 23
                for chunk in range(chunks):
                    references = list(key[chunk * 23:(chunk + 1) * 23])
                    append([0, submission, 29,
                            [bundle_id, len(key), chunk, chunks] + references])
            append([decision, submission, 30, [bundle_id]])
            logical_references += len(state_references)
            state_references = []
        append(item)
    self_contained = len(definitions)
    decisions = sum(item[2] == 2 for item in wire)
    swaps = sum(item[2] == 21 for item in wire)
    hosts = sum(item[2] == 17 for item in wire)
    storage = 25600000
    recorder_owned = storage + (128 + 64) * 4 + 64 * 8 + 200
    header = gpu.HEADER_V2.pack(
        b'REXMETA2', b'synthetic', 42, 256, 100000, gpu.MAX_BYTES, 20000, 3,
        5000000000, storage, 200, 2, 128, 64, 64, recorder_owned, 32, 2048,
        bytes(56))
    records = []
    for sequence, (decision, submission, type_id, fields) in enumerate(wire, 1):
        records.append(gpu.RECORD.pack(
            sequence, decision, submission, 100 + sequence, type_id, len(fields),
            *(fields + [0] * (27 - len(fields)))))
    terminal = [reason, 100, 100 + len(wire), len(wire), decisions, swaps,
                max(0, swaps - 1), (len(wire) + 2) * 256, 0, 0, 0, hosts,
                storage, self_contained, definition_reuses, len(bundles),
                bundle_reuses, logical_references, recorder_owned, 42]
    records.append(gpu.RECORD.pack(
        len(wire) + 1, 0, 0, 100 + len(wire), 1, len(terminal),
        *(terminal + [0] * (27 - len(terminal)))))
    return header + b''.join(records)


def ordinary():
    return [event('swap', [4096, 1280, 720]),
            event('decision', [34, 0], 1),
            event('geometry', [4, 3, 0, 0, 0, 0, 0, 0, 0], 1),
            event('shader', [0, 1, 111, 48], 1), event('shader', [1, 1, 222, 48], 1),
            event('shader_selection', [1, 1, 1, 0, 0, 1, 1, 0, 0, 2, 2, 0, 0], 1),
            event('index', [8192, 6, 3, 0, 0], 1),
            event('processed', [4, 0, 3, 3, 1, 8192, 0, 0, 0], 1),
            event('targets', [1280, 0, 15, 1, 3, 0, 7, 0], 1),
            event('depth', [0] * 22, 1),
            event('pipeline', [0, 0, 0, 0], 1), event('pipeline', [3, 0, 0, 1234], 1),
            event('texture_requested', [0, 0, 1, 0] + [0] * 22, 1),
            event('texture', [0, 0, 1, 0, 1, 4096, 0, 6, 0, 4, 64, 64, 1, 0, 0, 0, 0, 0, 555, 16384, 0, 0, 0, 99, 0], 1),
            event('viewport', [0, 0, 1280, 720, 0, 0, 0, 0, 1280, 720], 1),
            event('bindings', [1], 1),
            event('host', [3, 0, 8], 1), event('host', [2, 1, 16], 1),
            event('outcome', [10], 1),
            event('execute', [3, 8, 1]), event('execute', [2, 16, 1]),
            event('submit', [0, 1, 0, 0]), event('swap', [4096, 1280, 720])]


class MetadataTests(unittest.TestCase):
    def parse(self, data, **kwargs):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'synthetic.bin'
            path.write_bytes(data)
            return gpu.parse_capture(path, **kwargs)

    def test_complete_interval_carry_in_and_candidate_is_not_qualified(self):
        result = self.parse(fixture(ordinary()))
        self.assertEqual(result['structural_validity'], 'VALID')
        self.assertEqual(result['intervals']['complete'], 1)
        self.assertEqual(result['candidate']['decision'], 1)
        self.assertIn('further evidence', result['candidate']['qualification'])
        self.assertEqual(result['open_edges']['completion_unobserved'], [7])
        self.assertEqual(result['host_operation_counts'], {'dispatch': 1, 'indexed_draw': 1})

    def test_v2_dictionary_bundle_and_candidate_preserve_v1_semantics(self):
        result = self.parse(fixture_v2(ordinary()))
        self.assertEqual(result['format'], {'magic': 'REXMETA2', 'version': 2})
        self.assertEqual(result['intervals']['complete'], 1)
        self.assertEqual(result['candidate']['decision'], 1)
        self.assertGreater(result['dictionary']['logical_state_references'], 0)
        self.assertEqual(result['dictionary']['bundle_reference_records'], 1)
        self.assertEqual(result['decision_outcomes'], {'deferred_main_draw_recorded': 1})

    def test_v2_unknown_reference_and_duplicate_equal_definition_rejected(self):
        data = bytearray(fixture_v2(ordinary()))
        for offset in range(256, len(data) - 256, 256):
            if struct.unpack_from('<I', data, offset + 32)[0] == 30:
                struct.pack_into('<Q', data, offset + 40, 999999)
                break
        with self.assertRaisesRegex(ValueError, 'unknown|Missing'):
            self.parse(data)

        data = bytearray(fixture_v2(ordinary()))
        shader_offsets = [offset for offset in range(256, len(data) - 256, 256)
                          if struct.unpack_from('<I', data, offset + 32)[0] == 5]
        data[shader_offsets[1] + 40:shader_offsets[1] + 72] = \
            data[shader_offsets[0] + 40:shader_offsets[0] + 72]
        with self.assertRaisesRegex(ValueError, 'Duplicate equal'):
            self.parse(data)

    def test_unsupported_format_version_is_explicit(self):
        data = bytearray(fixture([]))
        data[:8] = b'REXMETA9'
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            self.parse(data)

    def test_wrong_session_and_pid_rejected(self):
        data = fixture([])
        with self.assertRaises(ValueError): self.parse(data, run_id='wrong')
        with self.assertRaises(ValueError): self.parse(data, pid=43)

    def test_truncated_or_missing_terminal(self):
        data = fixture(ordinary())
        with self.assertRaises(ValueError): self.parse(data[:-1])
        with self.assertRaises(ValueError): self.parse(data[:-256])

    def test_missing_duplicate_invalid_references(self):
        events = ordinary()
        with self.assertRaises(ValueError): self.parse(fixture(events[:1] + events[2:]))
        with self.assertRaises(ValueError): self.parse(fixture(events[:4] + [events[3]] + events[4:]))
        events[3][0] = 999
        with self.assertRaises(ValueError): self.parse(fixture(events))

    def test_duplicate_or_incompatible_host_join(self):
        events = ordinary()
        with self.assertRaises(ValueError): self.parse(fixture(events[:18] + [events[17]] + events[18:]))
        events[20][3][0] = 1
        with self.assertRaises(ValueError): self.parse(fixture(events))

    def test_open_decision_and_external_execution_are_explicit(self):
        events = [event('execute', [2, 80, 1]), event('decision', [34, 0], 1)]
        result = self.parse(fixture(events))
        self.assertEqual(result['open_edges']['decisions'], [1])
        self.assertEqual(result['open_edges']['deferred_recording_before_window_or_external'], [[7, 80]])
        self.assertIsNone(result['candidate'])

    def test_initial_partial_does_not_count(self):
        result = self.parse(fixture([event('swap', [0, 1, 1])]))
        self.assertEqual(result['intervals']['complete'], 0)
        with self.assertRaises(ValueError): self.parse(fixture([event('swap', [0, 1, 1])], reason=2))
        result = self.parse(fixture([event('swap', [0, 1, 1])] * 4, reason=2))
        self.assertEqual(result['intervals']['complete'], 3)
        self.assertFalse(result['intervals']['final_partial'])

    def test_outcomes_and_missing_main_draw(self):
        events = []
        for decision, outcome in enumerate(range(10), 1):
            events.extend([event('decision', [34, 0], decision), event('outcome', [outcome], decision)])
        result = self.parse(fixture(events))
        self.assertEqual(len(result['decision_outcomes']), 10)
        with self.assertRaises(ValueError):
            self.parse(fixture([event('decision', [34, 0], 1), event('outcome', [10], 1)]))

    def test_accounting_and_deadline_violation(self):
        data = bytearray(fixture(ordinary()))
        struct.pack_into('<Q', data, 256 + 24, 99)
        with self.assertRaises(ValueError): self.parse(data)
        data = bytearray(fixture(ordinary()))
        struct.pack_into('<Q', data, len(data) - 256 + 40 + 3 * 8, 999)
        with self.assertRaises(ValueError): self.parse(data)

    def test_reuse_refused_before_any_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'out/nr0b2/sessions/synthetic').mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, 'already exists'):
                gpu.prepare(root, root, 'synthetic')

    def test_durable_transition_replay_after_delayed_polling(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            transitions = root / 'transitions'
            transitions.mkdir()
            records = []
            for sequence, (kind, monotonic, reason, flushed) in enumerate([
                    ('READY', 100, 0, False), ('STARTED', 200, 0, False),
                    ('STOPPED', 240, 2, True)], 1):
                record = {
                    'schema': 'rex-gpu-metadata-transition-v1', 'run_id': 'synthetic',
                    'pid': 42, 'sequence': sequence, 'transition': kind,
                    'recorder_monotonic_ns': monotonic,
                    'wall_utc_unix_ns': 1000000000 + sequence,
                    'correlation_monotonic_ns': monotonic + 1,
                    'clock_correlation': 'consecutive control-worker samples; scheduler precision only',
                    'foreground_pid': 42 if kind == 'STARTED' else 0,
                    'trigger_accepted': kind == 'STARTED', 'terminal_reason': reason,
                    'terminal_reason_name': 'swaps' if kind == 'STOPPED' else 'none',
                    'output_flushed': flushed, 'error': ''}
                (transitions / f'{sequence:016d}-{kind}.json').write_text(
                    json.dumps(record) + '\n', encoding='utf-8')
                records.append(record)
            # The reader starts only after all three short-lived states have occurred.
            self.assertEqual(gpu.parse_transitions(transitions, 'synthetic', 42), records)
            bad = copy.deepcopy(records[1]); bad['sequence'] = 9
            (transitions / '0000000000000002-STARTED.json').write_text(
                json.dumps(bad), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'sequence'):
                gpu.parse_transitions(transitions, 'synthetic', 42)


if __name__ == '__main__': unittest.main()
