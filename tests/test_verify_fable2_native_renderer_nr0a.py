"""Failure-oriented checks for the small read-only NR0A citation verifier."""

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'nr0a_verifier', ROOT / 'tools/Verify-Fable2NativeRendererNR0A.py')
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class CitationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run_git('init', '-q')
        (self.root / 'source.cpp').write_text('void ActualEntry() {}\n', encoding='utf-8')
        self.run_git('add', 'source.cpp')
        self.run_git('-c', 'user.name=NR0A fixture', '-c', 'user.email=fixture@invalid',
                     'commit', '-qm', 'Synthetic source')
        self.pin = {'commit': self.run_git('rev-parse', 'HEAD'),
                    'url': 'https://github.com/example/synthetic'}
        self.citation = {
            'id': 'synthetic', 'path': 'source.cpp', 'symbols': ['ActualEntry'],
            'blob': self.run_git('rev-parse', 'HEAD:source.cpp'),
            'url': self.pin['url'] + '/blob/' + self.pin['commit'] + '/source.cpp',
        }

    def run_git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args],
                                       text=True, encoding='utf-8', stderr=subprocess.PIPE).strip()

    def test_reads_pinned_object_even_if_worktree_changes(self):
        (self.root / 'source.cpp').write_text('different uncommitted source\n', encoding='utf-8')
        verifier.check_citation(self.citation, self.pin, self.root)

    def test_missing_symbol_is_failure(self):
        self.citation['symbols'] = ['InventedEntry']
        with self.assertRaisesRegex(ValueError, 'Missing source symbol'):
            verifier.check_citation(self.citation, self.pin, self.root)

    def test_changed_blob_is_failure(self):
        self.citation['blob'] = '0' * 40
        with self.assertRaisesRegex(ValueError, 'blob mismatch'):
            verifier.check_citation(self.citation, self.pin, self.root)

    def test_mutable_url_is_failure(self):
        self.citation['url'] = self.pin['url'] + '/blob/main/source.cpp'
        with self.assertRaisesRegex(ValueError, 'URL mismatch'):
            verifier.check_citation(self.citation, self.pin, self.root)


class DocumentTests(unittest.TestCase):
    def test_broken_link_is_failure_and_examples_are_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'README.md'
            path.write_text('```text\n[example](absent.md)\n```\n', encoding='utf-8')
            self.assertEqual(verifier.check_links(path), 0)
            path.write_text('[real](absent.md)\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Broken Markdown link'):
                verifier.check_links(path)

    def test_duplicate_pin_is_failure(self):
        data = json.loads((ROOT / verifier.PACKAGE / 'evidence/reference-pins.json').read_text())
        data['repositories'].append(data['repositories'][0])
        with self.assertRaisesRegex(ValueError, 'Duplicate repository ID'):
            verifier.validate_contract(data)

    def test_source_path_cannot_escape_pin(self):
        for path in ('../source.cpp', '/source.cpp', 'C:/source.cpp', 'dir\\source.cpp'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                verifier.relative_path(path)


if __name__ == '__main__':
    unittest.main()
