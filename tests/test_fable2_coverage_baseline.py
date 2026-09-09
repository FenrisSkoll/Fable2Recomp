"""A coverage campaign must exclude targets seen in any accepted prior run."""
import copy
import json
from pathlib import Path
import unittest
import tempfile

from test_fable2_indirect_targets import (
    p4, rename_summary_run, replace_summary_pairs, schema_errors,
    synthetic_follow_up_inputs, PlannerFixture, write_json,
)


class PreliminaryOwnershipTests(unittest.TestCase):
    def test_gap_extent_requires_actual_body_and_cannot_authorize_import(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = PlannerFixture(Path(temporary))
            closure = json.loads(fixture.closure.read_text())
            row = next(r for r in closure['function_ranges']
                       if r['range']['start'] == '0x82191000')
            row.update(authority='gap_fill', preliminary=True, trusted=False)
            row['basic_blocks'] = [{'start': '0x82191000', 'end': '0x82191004', 'size': '0x00000004'}]
            write_json(fixture.closure, closure)
            result = next(r for r in fixture.plan()['targets'] if r['target'] == '0x82191004')
            self.assertEqual('ambiguous_target', result['classification'])
            self.assertIsNone(result['proposal'])
            self.assertFalse(result['automatic_application_permitted'])
            self.assertTrue(any(e['kind'] == 'preliminary_extent_without_body_ownership' for e in result['evidence']))
            closure['candidates'].append({
                'address': '0x82191004', 'classification': 'strong_new_function',
                'confidence': 'strong', 'proposed_range': {
                    'start': '0x82191004', 'end': '0x82191008', 'size': '0x00000004'},
                'boundary_provenance': 'synthetic_independent_boundary',
                'conflicts': [], 'rejection_reasons': [],
            })
            write_json(fixture.closure, closure)
            result = next(r for r in fixture.plan()['targets'] if r['target'] == '0x82191004')
            self.assertEqual('strong_new_function', result['classification'])
            self.assertEqual(4, result['proposal']['size_value'])
            row['basic_blocks'][0]['end'] = '0x82191008'
            row['basic_blocks'][0]['size'] = '0x00000008'
            write_json(fixture.closure, closure)
            result = next(r for r in fixture.plan()['targets'] if r['target'] == '0x82191004')
            self.assertEqual('existing_function_internal_entry', result['classification'])
            self.assertFalse(result['automatic_application_permitted'])


def signed(document, key, prefix):
    document.pop(key, None)
    document[key] = prefix + p4.sha256_bytes(p4.canonical_json_bytes(document))[:20]
    return document


def cohort_fixture(reverse=False):
    baseline, contributing, _, plan, closure, inputs = synthetic_follow_up_inputs()
    previous = copy.deepcopy(contributing)
    rename_summary_run(previous, 'previous-extra')
    previous['runs'][0]['raw_sha256'] = '9' * 64
    replace_summary_pairs(previous, [(0x82180000, 'existing_function_internal_entry')], legacy_metadata=False)
    baseline = p4.merge_summaries([previous, baseline] if reverse else [baseline, previous])
    merged = p4.merge_summaries([baseline, contributing])
    plan['inputs']['summary']['run_ids'] = sorted(r['run_id'] for r in merged['runs'])
    plan['inputs']['summary']['raw_trace_sha256'] = sorted(r['raw_sha256'] for r in merged['runs'])
    grouped, _ = p4.group_target_observations(merged)
    for row in plan['targets']:
        row['runtime']['observations'] = grouped[int(row['target'], 16)]
    signed(plan, 'plan_id', 'P4PLAN-')
    return baseline, contributing, merged, plan, closure, inputs


class CoverageBaselineTests(unittest.TestCase):
    def test_union_excludes_target_seen_only_in_second_baseline(self):
        report = p4.build_static_ownership_follow_up(*cohort_fixture())
        self.assertEqual(report['schema']['version'], 2)
        self.assertEqual(report['counts']['targets'], 566)
        self.assertNotIn('0x82180000', {r['target'] for r in report['targets']})
        self.assertEqual(len(report['run_provenance']), 3)
        path = Path(__file__).resolve().parents[1] / 'tools/schemas/fable2-phase4-static-ownership-follow-up-v2.schema.json'
        self.assertEqual(schema_errors(report, json.loads(path.read_text())), [])

    def test_input_order_determinism(self):
        inputs = list(cohort_fixture())
        expected = p4.canonical_json_bytes(p4.build_static_ownership_follow_up(*inputs))
        self.assertEqual(expected, p4.canonical_json_bytes(p4.build_static_ownership_follow_up(*cohort_fixture(reverse=True))))

    def test_single_baseline_preserves_v1_contract(self):
        report = p4.build_static_ownership_follow_up(*synthetic_follow_up_inputs())
        self.assertEqual(report['schema']['version'], 1)
        self.assertEqual(report['counts']['targets'], 567)
        self.assertNotIn('baseline_run_ids', report['scope'])

    def test_omitted_or_duplicate_baseline_provenance_rejected(self):
        original = p4.build_static_ownership_follow_up(*cohort_fixture())
        for mutation in ('omit', 'duplicate', 'target_scope'):
            report = copy.deepcopy(original)
            if mutation == 'omit':
                report['run_provenance'].pop(0)
            elif mutation == 'duplicate':
                report['scope']['baseline_run_ids'][1] = report['scope']['baseline_run_ids'][0]
            else:
                report['targets'][0]['baseline_run_ids'] = ['invented', 'previous-extra']
            signed(report, 'report_id', 'P4OWN-')
            with self.subTest(mutation=mutation), self.assertRaises(p4.Phase4Error):
                p4.validate_static_ownership_follow_up(report)

    def test_plan_missing_one_baseline_run_rejected(self):
        inputs = list(cohort_fixture())
        inputs[3]['inputs']['summary']['run_ids'].remove('previous-extra')
        signed(inputs[3], 'plan_id', 'P4PLAN-')
        with self.assertRaisesRegex(p4.Phase4Error, 'run IDs disagree'):
            p4.build_static_ownership_follow_up(*inputs)

    def test_multiple_contributing_runs_still_rejected(self):
        inputs = list(cohort_fixture())
        inputs[1] = inputs[2]
        with self.assertRaisesRegex(p4.Phase4Error, 'exactly one'):
            p4.build_static_ownership_follow_up(*inputs)

    def test_proposals_still_require_independent_review(self):
        inputs = list(cohort_fixture())
        inputs[3]['proposals'] = [copy.deepcopy(inputs[3]['targets'][0])]
        signed(inputs[3], 'plan_id', 'P4PLAN-')
        with self.assertRaisesRegex(p4.Phase4Error, 'no manifest proposals'):
            p4.build_static_ownership_follow_up(*inputs)


if __name__ == '__main__':
    unittest.main()
