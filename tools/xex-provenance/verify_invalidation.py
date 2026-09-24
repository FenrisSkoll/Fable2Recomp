"""Bounded real-loader/codegen incremental test. All writes stay in a NEW fixture.

Uses the normal generated CMake rule and an isolated copy of the tool. Inputs
are privately supplied; no executable bytes are committed. Logs and a receipt
are retained even on failure. Requires CMake, Ninja and the SDK toolchain.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def census(directory):
    return {p.name: digest(p) for p in sorted(directory.iterdir()) if p.suffix in ('.cpp', '.h')}


def verify_removal(work, delta):
    """TU1 overrides cannot compile the base revision: require a failed build,
    never successful stale reuse. Generic base-only emission has SDK coverage.
    """
    receipt_path = work / 'receipt.json'
    receipt = json.loads(receipt_path.read_text())
    assert receipt['status'] == 'PASS'
    receipt['status'] = 'INCOMPLETE'
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    output = work / 'generated/default'
    original = census(output)
    patch = work / 'game/default.xexp'
    assert digest(patch) == digest(delta)
    command = ['cmake', '--build', str(work / 'build'), '--target', 'fable2_codegen', '--', '-d', 'explain']
    patch.unlink()
    try:
        failed = subprocess.run(command, cwd=work, capture_output=True, text=True, encoding='utf-8', errors='replace')
        text = failed.stdout + failed.stderr
        (work / 'real-delta-removed.log').write_text(text, encoding='utf-8')
        assert failed.returncode != 0, 'TU1 manifest unexpectedly accepted the base revision'
        assert 'Validation failed' in text, text[-2000:]
        assert 'module(s) up to date' not in text
        assert original == census(output)
    finally:
        shutil.copyfile(delta, patch)
    for label in ('real-delta-restored', 'real-restored-noop'):
        result = subprocess.run(command, cwd=work, capture_output=True, text=True, encoding='utf-8', errors='replace')
        text = result.stdout + result.stderr
        (work / (label + '.log')).write_text(text, encoding='utf-8')
        assert result.returncode == 0, text
        if label.endswith('noop'):
            assert 'Codegen summary:' not in text
        assert original == census(output)
    receipt['real_removal'] = {'status': 'PASS', 'removed_build': 'EXPECTED VALIDATION FAILURE',
                               'restored_build': 'PASS', 'restored_noop': 'PASS'}
    receipt['status'] = 'PASS'
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print('PASS: real removal fails closed; restoration and no-op pass', flush=True)


def verify(repo, sdk, fixed_tool, delta, work):
    work.mkdir(parents=True, exist_ok=False)
    game = work / 'game'
    game.mkdir()
    output = work / 'generated/default'
    output.mkdir(parents=True)
    tool = work / 'tool'
    tool.mkdir()
    for p in (sdk / 'bin').iterdir():
        shutil.copyfile(p, tool / p.name)
    original_tool = digest(tool / 'rexglue.exe')
    shutil.copyfile(fixed_tool, tool / 'rexglue.exe')
    for name in ('default.xex', 'default.xexp'):
        shutil.copyfile(repo / 'assets/tu1' / name, game / name)
    shutil.copyfile(repo / 'generated/default/codegen.partition.json', output / 'codegen.partition.json')
    # Keep the normal output graph from the outset; otherwise a cold bootstrap
    # first discovers sources.cmake and legitimately changes CMake's output list.
    shutil.copyfile(repo / 'generated/default/sources.cmake', output / 'sources.cmake')
    shutil.copyfile(repo / 'generated/rexglue.cmake', work / 'generated/rexglue.cmake')
    manifest = (repo / 'fable2_manifest.toml').read_text().replace('assets/tu1', 'game')
    (work / 'fable2_manifest.toml').write_text(manifest, encoding='utf-8')
    (work / 'CMakeLists.txt').write_text('''cmake_minimum_required(VERSION 3.25)
project(fable2 LANGUAGES CXX)
include(generated/rexglue.cmake)
set_property(TARGET rex::rexglue PROPERTY IMPORTED_LOCATION_RELEASE "${CMAKE_CURRENT_SOURCE_DIR}/tool/rexglue.exe")
''', encoding='utf-8')
    receipt = {'commands': [], 'states': {}, 'original_installed_tool': original_tool,
               'tested_tool': digest(tool / 'rexglue.exe'), 'status': 'INCOMPLETE'}

    def save():
        (work / 'receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')

    def run(label, args, expect_codegen=None):
        command = list(map(str, args))
        process = subprocess.run(command, cwd=work, capture_output=True, text=True,
                                 encoding='utf-8', errors='replace')
        text = process.stdout + process.stderr
        (work / (label + '.log')).write_text(text, encoding='utf-8')
        receipt['commands'].append({'label': label, 'command': command, 'returncode': process.returncode,
                                    'log_sha256': digest(work / (label + '.log'))})
        save()
        print(label, process.returncode, text[-250:], flush=True)
        assert process.returncode == 0, label
        if expect_codegen is not None:
            assert ('Codegen summary:' in text) == expect_codegen, (label, text)
        return text

    def state(label):
        entry = {'xex': digest(game / 'default.xex'),
                 'xexp': digest(game / 'default.xexp') if (game / 'default.xexp').exists() else None,
                 'manifest': digest(work / 'fable2_manifest.toml'),
                 'tool': digest(tool / 'rexglue.exe'),
                 'runtime': digest(tool / 'rexruntime.dll'),
                 'stamp': (output / 'codegen.stamp').read_text(),
                 'build_stamp': (output / 'codegen.build.stamp').read_text(),
                 'depfile': (output / 'codegen.d').read_text(), 'census': census(output)}
        receipt['states'][label] = entry
        save()
        return entry

    run('configure', ['cmake', '-S', work, '-B', work / 'build', '-G', 'Ninja',
        '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_CXX_COMPILER=clang-cl',
        f'-Drexglue_DIR={sdk}/lib/cmake/rexglue'])
    build = ['cmake', '--build', work / 'build', '--target', 'fable2_codegen', '--', '-d', 'explain']
    run('initial', build, True)
    first = state('initial')
    run('initial-noop', build, False)
    assert first == state('initial-noop')
    shutil.copyfile(delta, game / 'default.xexp')
    text = run('delta-changed', build, True)
    assert '0 module(s) up to date' in text
    changed = state('delta-changed')
    assert first['xex'] == changed['xex']
    assert first['xexp'] != changed['xexp']
    assert first['manifest'] == changed['manifest']
    assert first['tool'] == changed['tool']
    assert first['stamp'] != changed['stamp']
    assert first['census'] != changed['census']
    # The known isolated delta changes exactly lwz r11,152(r12) -> lwz r11,92(r12).
    changed_files = [name for name in first['census'] if first['census'][name] != changed['census'][name]]
    receipt['changed_generated_files'] = changed_files
    run('changed-noop', build, False)
    assert changed == state('changed-noop')
    # PE permits an overlay after its mapped image. This simulates a different
    # packaged binary identity without modifying the codegen algorithm/game.
    with (tool / 'rexglue.exe').open('ab') as stream:
        stream.write(b'\nrexglue-invalidation-tool-identity-negative-control\n')
    run('tool-changed', build, True)
    tool_changed = state('tool-changed')
    assert tool_changed['tool'] != changed['tool']
    assert tool_changed['stamp'] != changed['stamp']
    assert tool_changed['census'] == changed['census']
    assert tool_changed['xex'] == changed['xex'] and tool_changed['xexp'] == changed['xexp']
    run('tool-noop', build, False)
    assert tool_changed == state('tool-noop')
    with (tool / 'rexruntime.dll').open('ab') as stream:
        stream.write(b'\nrexglue-invalidation-runtime-identity-negative-control\n')
    run('runtime-changed', build, True)
    runtime_changed = state('runtime-changed')
    assert runtime_changed['runtime'] != tool_changed['runtime']
    assert runtime_changed['stamp'] != tool_changed['stamp']
    assert runtime_changed['census'] == tool_changed['census']
    assert runtime_changed['tool'] == tool_changed['tool']
    run('runtime-noop', build, False)
    assert runtime_changed == state('runtime-noop')
    receipt['status'] = 'PASS'
    save()
    verify_removal(work, delta)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('repo', 'sdk', 'fixed-tool', 'delta', 'work'):
        parser.add_argument('--' + name, type=lambda p: Path(p).resolve(), required=True)
    parser.add_argument('--resume-removal', action='store_true')
    args = vars(parser.parse_args())
    if args.pop('resume_removal'):
        verify_removal(args['work'], args['delta'])
    else:
        verify(**args)
