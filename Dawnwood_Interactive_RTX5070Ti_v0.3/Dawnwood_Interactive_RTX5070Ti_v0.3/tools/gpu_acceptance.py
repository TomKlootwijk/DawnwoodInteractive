#!/usr/bin/env python3
"""Run this on the RTX laptop after compiling. Executes small real GPU tests."""
from __future__ import annotations
import argparse
import json
import hashlib
import subprocess
from pathlib import Path


def invoke(executable: Path, args: list[str], folder: Path, label: str) -> dict:
    completed = subprocess.run([str(executable), *args], cwd=folder, text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    (folder / (label + '.log')).write_text(completed.stdout, encoding='utf-8')
    if completed.returncode:
        raise RuntimeError(f'{label} exited {completed.returncode}; read its log')
    return {'name': label, 'returncode': completed.returncode}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('executable', type=Path)
    p.add_argument('--out', type=Path, default=Path('work/gpu_acceptance'))
    a = p.parse_args()
    exe = a.executable.resolve()
    folder = a.out.resolve()
    folder.mkdir(parents=True, exist_ok=False)
    checks = []
    try:
        checks.append(invoke(exe, ['--probe'], folder, 'probe'))
        checks.append(invoke(exe, ['--self-test'], folder, 'native_self_test'))
        base = ['--pages', '3', '--page-side', '16', '--blocks-per-step', '7', '--batch', '1']
        for codec in ['rg8', 'bc5']:
            for name, steps, extra in [('whole', '20', ['--snapshot', f'{codec}_whole.snapshot']),
                                        ('repeat', '20', ['--snapshot', f'{codec}_repeat.snapshot']),
                                        ('part', '7', ['--snapshot', f'{codec}.snapshot'])]:
                report = f'{codec}_{name}.json'
                checks.append(invoke(exe, base + ['--codec', codec, '--steps', steps,
                    '--report', report] + extra, folder, f'{codec}_{name}'))
            checks.append(invoke(exe, ['--resume', f'{codec}.snapshot', '--steps', '13',
                '--batch', '1', '--snapshot', f'{codec}_resumed.snapshot', '--report', f'{codec}_resumed.json'], folder, f'{codec}_resumed'))
            reports = {name: json.loads((folder / f'{codec}_{name}.json').read_text())
                       for name in ['whole', 'repeat', 'resumed']}
            digests = {r['operator_digest_fnv1a64'] for r in reports.values()}
            if len(digests) != 1:
                raise AssertionError(f'{codec}: repeat/snapshot continuation operator digest mismatch')
            if any(r['end_epoch'] != 20 for r in reports.values()):
                raise AssertionError('Unexpected epoch after continuation')
            checks.append({'name': f'{codec}_operator_repeat_and_resume', 'passed': True})
            full_hashes = {hashlib.sha256((folder / f'{codec}_{name}.snapshot').read_bytes()).hexdigest()
                           for name in ['whole', 'repeat', 'resumed']}
            if len(full_hashes) != 1:
                raise AssertionError(f'{codec}: complete-field snapshot mismatch')
            checks.append({'name': f'{codec}_complete_field_repeat_and_resume', 'passed': True})
            checks.append(invoke(exe, base + ['--codec', codec, '--steps', '20', '--no-graph',
                '--report', f'{codec}_no_graph.json'], folder, f'{codec}_no_graph'))
            simple = json.loads((folder / f'{codec}_no_graph.json').read_text())
            if simple['operator_digest_fnv1a64'] != reports['whole']['operator_digest_fnv1a64']:
                raise AssertionError(f'{codec}: graph / sequential launch mismatch')
            checks.append({'name': f'{codec}_graph_equivalence', 'passed': True})
        result = {'status': 'passed', 'checks': checks}
    except Exception as exc:
        result = {'status': 'failed', 'error': str(exc), 'checks': checks}
        (folder / 'acceptance.json').write_text(json.dumps(result, indent=2) + '\n')
        raise
    (folder / 'acceptance.json').write_text(json.dumps(result, indent=2) + '\n')
    print(folder / 'acceptance.json')


if __name__ == '__main__':
    main()
