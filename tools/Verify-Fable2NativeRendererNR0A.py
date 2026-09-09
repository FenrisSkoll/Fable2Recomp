"""Read-only NR0A pin, citation, link and optional preserved-state checks.

Uses local Git objects only. Never fetches, checks out, launches a game or reads
saves. Literal symbol checks establish citation integrity, not semantic truth.
"""

import argparse
import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = Path('docs/fable2-native-renderer/nr0a')
SHA1 = re.compile(r'[0-9a-f]{40}')
SHA256 = re.compile(r'[0-9A-F]{64}')
LINK = re.compile(r'\[[^\]\n]+\]\(([^)\n]+)\)')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def relative_path(value):
    path = PurePosixPath(value)
    require(bool(value) and not path.is_absolute() and '..' not in path.parts
            and '\\' not in value and ':' not in value,
            f'Unsafe relative path: {value!r}')
    return value


def git(root, *args):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True)
    require(result.returncode == 0,
            f'Git object unavailable at {root}: {args}: '
            + result.stderr.decode('utf-8', errors='replace').strip())
    return result.stdout.decode('utf-8', errors='replace').strip()


def validate_contract(data):
    require(data['format_version'] == 1, 'Unsupported NR0A format_version')
    datetime.date.fromisoformat(data['inspection_date'])
    require(data['result'] == 'CONDITIONAL ARCHITECTURE — DYNAMIC EVIDENCE REQUIRED',
            'Unexpected NR0A result')
    repositories = data['repositories']
    ids = [p['id'] for p in repositories]
    require(len(ids) == len(set(ids)), 'Duplicate repository ID')
    require({'fable', 'sdk', 'skate', 'skate-sdk', 'unleashed', 'xenosrecomp',
             'plume', 'plume-unleashed', 'pgr4', 'canary'} <= set(ids),
            'Missing required comparison pin')
    for pin in repositories:
        require(SHA1.fullmatch(pin['commit']) and SHA1.fullmatch(pin['tree']),
                f'Invalid commit/tree: {pin["id"]}')
        require(pin['url'].startswith('https://github.com/'), 'Invalid repository URL')
        require(pin['branch'] and pin['local_path'], 'Missing branch/root provenance')
        require(pin['shallow'] in ('true', 'false') and pin['available_commit_count'] > 0,
                'Missing history-depth provenance')
        datetime.date.fromisoformat(pin['inspection_date'])
        license_info = pin['license']
        require(bool(license_info['assessment']), 'Missing license assessment')
        if license_info['path']:
            relative_path(license_info['path'])
            require(SHA1.fullmatch(license_info['blob']), 'Invalid license blob')
        for dep in pin['dependencies']:
            relative_path(dep['path'])
            require(SHA1.fullmatch(dep['commit']), 'Invalid dependency pin')
            require(dep['url'] and dep['license_status'], 'Missing dependency provenance')
            evidence = dep.get('license_evidence', {})
            if 'sha256' in evidence:
                require(SHA256.fullmatch(evidence['sha256']) and evidence['bytes'] > 0,
                        'Invalid license retrieval identity')
                require(dep['commit'] in evidence['url'], 'License URL is not pinned')
    citation_ids = [c['id'] for c in data['citations']]
    require(len(citation_ids) == len(set(citation_ids)), 'Duplicate citation ID')
    for citation in data['citations']:
        require(citation['repository'] in ids, 'Unknown citation repository')
        relative_path(citation['path'])
        require(SHA1.fullmatch(citation['blob']), 'Invalid citation blob')
        require(citation['symbols'] and all(isinstance(s, str) and s for s in citation['symbols']),
                'Missing literal source symbols')
    require(SHA256.fullmatch(data['preserved_manifest_sha256']), 'Invalid manifest hash')
    for path, digest in data['libmspack_worktree_sha256'].items():
        relative_path(path)
        require(SHA256.fullmatch(digest), 'Invalid materialization hash')
    for artifact in data['current_disk_artifacts']:
        relative_path(artifact['path'])
        require(SHA256.fullmatch(artifact['sha256']) and artifact['bytes'] > 0,
                'Invalid current disk identity')
    history = data['historical_identities']
    for key in ('g1', 'g16b', 'g2a_retirement', 'research_integration', 'sdk_reference'):
        require(SHA1.fullmatch(history[key]), f'Invalid historical anchor: {key}')
    for key in ('tu1_post_patch_sha256', 'gpu_dll_sha256', 'exe_sha256'):
        require(SHA256.fullmatch(history[key]), f'Invalid historical hash: {key}')
    require(len(history['missing_logs']) == len(set(history['missing_logs'])),
            'Duplicate historical log')


def check_citation(citation, pin, root):
    spec = pin['commit'] + ':' + relative_path(citation['path'])
    require(git(root, 'rev-parse', spec) == citation['blob'],
            f'Citation blob mismatch: {citation["id"]}')
    expected_url = f'{pin["url"]}/blob/{pin["commit"]}/{citation["path"]}'
    require(citation['url'] == expected_url, f'Citation URL mismatch: {citation["id"]}')
    content = git(root, 'show', spec)
    for symbol in citation['symbols']:
        require(symbol in content, f'Missing source symbol: {citation["id"]}: {symbol}')


def check_links(path):
    """Check local Markdown file targets, excluding fenced examples and web URLs."""
    text = re.sub(r'```.*?```', '', path.read_text(encoding='utf-8'), flags=re.S)
    count = 0
    for target in LINK.findall(text):
        target = target.strip('<>')
        parsed = urlsplit(target)
        if parsed.scheme or not parsed.path:
            continue
        resolved = path.parent / unquote(parsed.path)
        require(resolved.is_file(), f'Broken Markdown link in {path.name}: {target}')
        count += 1
    return count


def check_pins(data, roots):
    pins = {pin['id']: pin for pin in data['repositories']}
    for pin in pins.values():
        root = roots[pin['id']]
        require(git(root, 'rev-parse', pin['commit'] + '^{tree}') == pin['tree'],
                f'Pinned tree mismatch: {pin["id"]}')
        license_info = pin['license']
        if license_info['path']:
            require(git(root, 'rev-parse', pin['commit'] + ':' + license_info['path'])
                    == license_info['blob'], f'License blob mismatch: {pin["id"]}')
        for dep in pin['dependencies']:
            tree_entry = git(root, 'ls-tree', pin['commit'], '--', dep['path'])
            require(tree_entry.startswith('160000 commit ' + dep['commit'] + '\t'),
                    f'Dependency gitlink mismatch: {pin["id"]}: {dep["path"]}')
    for citation in data['citations']:
        check_citation(citation, pins[citation['repository']], roots[citation['repository']])
    for key in ('g1', 'g16b', 'g2a_retirement', 'research_integration'):
        git(roots['fable'], 'merge-base', '--is-ancestor',
            data['historical_identities'][key], pins['fable']['commit'])


def check_immutable_links(package, data, roots):
    """Validate every external source-file link belonging to a catalog pin."""
    count = 0
    for path in package.glob('*.md'):
        for target in LINK.findall(path.read_text(encoding='utf-8')):
            for pin in data['repositories']:
                prefix = pin['url'] + '/blob/' + pin['commit'] + '/'
                if target.startswith(prefix):
                    source = relative_path(unquote(target[len(prefix):].split('#')[0]))
                    git(roots[pin['id']], 'cat-file', '-e', pin['commit'] + ':' + source)
                    count += 1
    return count


def check_preserved_state(data, roots):
    checks = [(roots['fable'] / 'fable2_manifest.toml', data['preserved_manifest_sha256'])]
    checks.extend((roots['sdk'] / 'thirdparty/libmspack' / name, digest)
                  for name, digest in data['libmspack_worktree_sha256'].items())
    for path, digest in checks:
        require(hashlib.sha256(path.read_bytes()).hexdigest().upper() == digest,
                f'Preserved worktree file changed: {path}')
    dirty = set(git(roots['sdk'] / 'thirdparty/libmspack', 'diff', '--name-only').splitlines())
    require(dirty == set(data['libmspack_worktree_sha256']), 'Materialization dirty path set changed')
    require(not git(roots['sdk'], 'diff', '--cached', '--name-only'), 'SDK index changed')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', action='append', default=[], metavar='ID=PATH')
    parser.add_argument('--verify-preserved-state', action='store_true',
                        help='Also compare the originally dirty manifest/libmspack bytes')
    args = parser.parse_args(argv)
    try:
        package = ROOT / PACKAGE
        data = json.loads((package / 'evidence/reference-pins.json').read_text(encoding='utf-8'))
        validate_contract(data)
        roots = {p['id']: Path(p['local_path']) for p in data['repositories']}
        for override in args.root:
            key, separator, value = override.partition('=')
            require(separator and key in roots and value, f'Invalid root override: {override}')
            roots[key] = Path(value)
        check_pins(data, roots)
        links = sum(check_links(path) for path in package.glob('*.md'))
        sources = check_immutable_links(package, data, roots)
        if args.verify_preserved_state:
            check_preserved_state(data, roots)
        print(f'PASS NR0A: {len(data["repositories"])} pins, '
              f'{len(data["citations"])} source-symbol records, '
              f'{links} local links, {sources} immutable source links')
        print('Historical artifact equality and runtime behavior are not asserted by this check.')
        return 0
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f'FAIL NR0A: {error}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
