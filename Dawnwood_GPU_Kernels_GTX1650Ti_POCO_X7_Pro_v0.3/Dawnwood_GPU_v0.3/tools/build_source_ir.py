#!/usr/bin/env python3
"""Build the separate DWI-XIR expression evaluator and its matching Vulkan shader.

This does not rebuild or change the N1/D1 recurrence executables.
"""
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
    parser.add_argument('--output', type=Path, default=ROOT / 'bin/windows-source')
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
    shader = output / 'source_ir.spv'
    binary = output / 'dawnwood-source-ir.exe'
    sources = [ROOT / name for name in (
        'include/source_ir.inc', 'include/numeric_types.inc',
        'include/numeric_math.inc', 'src/source_ir_cli.cpp',
        'shaders/source_ir.comp', 'tools/build_source_ir.py')]
    initial_hashes = {str(path.relative_to(ROOT)): digest(path) for path in sources}
    commands = [
        [str(glslc), '--target-env=vulkan1.1', f'-I{ROOT / "include"}',
         str(ROOT / 'shaders/source_ir.comp'), '-o', str(shader)],
        [str(validator), '--target-env', 'vulkan1.1', str(shader)],
        [str(compiler), '-std=c++17', '-O2', '-Wall', '-Wextra', '-Wpedantic',
         '-ffp-contract=off', '-fno-fast-math', '-static',
         f'-I{ROOT / "include"}', f'-I{sdk / "Include"}',
         str(ROOT / 'src/source_ir_cli.cpp'), str(vulkan), '-o', str(binary)],
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
                'completed': False, 'commands': receipts,
                'source_sha256': initial_hashes}, indent=2) + '\n', encoding='utf-8')
            print(completed.stderr, file=sys.stderr)
            return completed.returncode
    final_hashes = {str(path.relative_to(ROOT)): digest(path) for path in sources}
    if initial_hashes != final_hashes:
        raise RuntimeError('Build inputs changed during compilation; rebuild before using outputs')
    report = {'profile': 'DWI-XIR-0.1', 'completed': True,
              'scope': 'Numerical expression evaluator, not the full source circulation',
              'commands': receipts, 'source_sha256': final_hashes,
              'artifacts': {p.name: {'bytes': p.stat().st_size, 'sha256': digest(p)}
                            for p in (binary, shader)}}
    (output / 'build.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
