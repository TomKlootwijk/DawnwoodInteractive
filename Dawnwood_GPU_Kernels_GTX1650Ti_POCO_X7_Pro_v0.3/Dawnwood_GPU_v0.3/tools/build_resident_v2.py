#!/usr/bin/env python3
"""Build DWI-RESIDENT-0.2 separately, preserving N1/D1 and XIR artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', type=Path)
    parser.add_argument('--sdk', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'bin/windows-resident-v2')
    args = parser.parse_args()
    cached = REPO / 'tmp/rtx-toolchain'
    compiler = args.compiler or Path(shutil.which('clang++') or
        cached / 'llvm-mingw-20260922-ucrt-x86_64/bin/clang++.exe')
    sdk = args.sdk or Path(os.environ.get('VULKAN_SDK', cached / 'VulkanSDK'))
    glslc, validator = sdk / 'Bin/glslc.exe', sdk / 'Bin/spirv-val.exe'
    vulkan = sdk / 'Lib/vulkan-1.lib'
    for path in (compiler, glslc, validator, vulkan):
        if not path.is_file():
            parser.error(f'Required build dependency missing: {path}')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    shader, binary = output / 'resident_v2.spv', output / 'dawnwood-resident-v2.exe'
    sources = {name: ROOT / name for name in (
        'include/resident_v2.inc', 'include/source_math_v2.inc', 'include/numeric_types.inc', 'include/numeric_math.inc',
        'src/resident_v2_cli.cpp', 'shaders/resident_v2.comp', 'tools/build_resident_v2.py')}
    sources['repo:docs/RESIDENT_V2_ABI.md'] = REPO / 'docs/RESIDENT_V2_ABI.md'
    initial_hashes = {name: digest(path) for name, path in sources.items()}
    commands = [
        [str(glslc), '--target-env=vulkan1.1', f'-I{ROOT / "include"}',
         str(ROOT / 'shaders/resident_v2.comp'), '-o', str(shader)],
        [str(validator), '--target-env', 'vulkan1.1', str(shader)],
        [str(compiler), '-std=c++17', '-O2', '-Wall', '-Wextra', '-Wpedantic',
         '-ffp-contract=off', '-fno-fast-math', '-static',
         f'-I{ROOT / "include"}', f'-I{sdk / "Include"}',
         str(ROOT / 'src/resident_v2_cli.cpp'), str(vulkan), '-o', str(binary)],
    ]
    receipts = []
    for i, command in enumerate(commands):
        completed = subprocess.run(command, cwd=ROOT, capture_output=True,
                                   text=True, encoding='utf-8', errors='replace')
        (output / f'build-{i}.stdout.txt').write_text(completed.stdout, encoding='utf-8')
        (output / f'build-{i}.stderr.txt').write_text(completed.stderr, encoding='utf-8')
        receipts.append({'command': command, 'exit_code': completed.returncode})
        if completed.returncode:
            (output / 'build.json').write_text(json.dumps({
                'profile': 'DWI-RESIDENT-0.2', 'completed': False,
                'commands': receipts, 'source_sha256': initial_hashes}, indent=2) + '\n', encoding='utf-8')
            print(completed.stderr, file=sys.stderr)
            return completed.returncode
    final_hashes = {name: digest(path) for name, path in sources.items()}
    if initial_hashes != final_hashes:
        failure = {'profile': 'DWI-RESIDENT-0.2', 'completed': False,
                   'error': 'Build inputs changed during compilation; rebuild before use',
                   'commands': receipts, 'initial_source_sha256': initial_hashes,
                   'source_sha256': final_hashes}
        (output / 'build.json').write_text(json.dumps(failure, indent=2) + '\n', encoding='utf-8')
        raise RuntimeError(failure['error'])
    report = {'profile': 'DWI-RESIDENT-0.2', 'completed': True,
              'scope': 'Finite resident mutation/action component; not the full eight-stage source cycle',
              'commands': receipts, 'source_sha256': final_hashes,
              'artifacts': {p.name: {'bytes': p.stat().st_size, 'sha256': digest(p)}
                            for p in (binary, shader)}}
    (output / 'build.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
