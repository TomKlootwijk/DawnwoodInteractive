#!/usr/bin/env python3
"""Compare reference/optimized CUDA builds with complete snapshots and paired timings.

Example (use a new output directory on every run):
  python tools/benchmark_optimization.py build/Release/dawnwood_reference.exe \
      build/Release/dawnwood.exe --out work/optimization_01

For a larger field, add --pages 32 --page-side 2048 (192 MiB BC5 payload or
320 MiB RG8 payload). Keep active blocks, steps and recurrence options unchanged
across builds. Defaults use 1,024 timed intervals to amortize launch overhead.
To isolate kernel changes at a common cache preference, add
--reference-cache-policy balanced --optimized-cache-policy balanced.

This launches bounded GPU work. It does not fill VRAM automatically, measure cache
hits, or establish a physical double-slit experiment. Both executables receive
identical recurrence parameters. CUDA-event time includes launch gaps; process
wall time additionally includes context creation, allocation and initialization.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import time


REPORT_INVARIANTS = (
    'device', 'compute_capability', 'cuda_runtime', 'cuda_driver', 'codec',
    'total_device_bytes', 'pages', 'page_side', 'token_pairs',
    'blocks_per_interval', 'payload_bytes', 'start_epoch', 'end_epoch',
    'visited_blocks_this_run', 'complete_sweeps_this_run', 'total_complete_sweeps',
    'software_codec_mean_absolute_token_error', 'operator_digest_fnv1a64',
)
METRICS = (
    'cuda_event_ms_including_launch_gaps',
    'circulation_wall_ms',
    'process_wall_ms',
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def dispersion(values: list[float]) -> dict:
    if not values or any(not math.isfinite(v) or v <= 0 for v in values):
        raise ValueError('Timing and speedup samples must be finite and positive')
    median = statistics.median(values)
    mean = statistics.mean(values)
    stdev = statistics.stdev(values) if len(values) > 1 else None
    return {
        'samples': values,
        'count': len(values),
        'median': median,
        'min': min(values),
        'max': max(values),
        'median_absolute_deviation': statistics.median(abs(v - median) for v in values),
        'mean': mean,
        'sample_standard_deviation': stdev,
        'coefficient_of_variation': stdev / mean if stdev is not None else None,
    }


def compare_reports(reference: dict, optimized: dict, label: str) -> None:
    differences = {
        key: {'reference': reference.get(key), 'optimized': optimized.get(key)}
        for key in REPORT_INVARIANTS
        if key not in reference or key not in optimized or reference[key] != optimized[key]
    }
    if differences:
        raise AssertionError(f'{label}: report invariants differ: {differences}')


def check_snapshot_pair(reference: dict, optimized: dict, label: str) -> None:
    compare_reports(reference['report'], optimized['report'], label)
    if reference['snapshot_sha256'] != optimized['snapshot_sha256']:
        raise AssertionError(f'{label}: full snapshot SHA256 mismatch')


def summarize_pairs(pairs: list[dict]) -> dict:
    result = {}
    for metric in METRICS:
        ref = [pair['reference'][metric] for pair in pairs]
        opt = [pair['optimized'][metric] for pair in pairs]
        reference = dispersion(ref)
        optimized = dispersion(opt)
        result[metric] = {
            'reference': reference,
            'optimized': optimized,
            'reference_over_optimized_ratio_of_medians': reference['median'] / optimized['median'],
            'paired_reference_over_optimized_speedup': dispersion([r / o for r, o in zip(ref, opt)]),
        }
    result['token_pair_updates_per_second'] = {
        variant: dispersion([pair[variant]['report']['token_pair_updates_per_second'] for pair in pairs])
        for variant in ('reference', 'optimized')
    }
    return result


def capture_environment_command(command: list[str]) -> dict:
    resolved = shutil.which(command[0])
    result = {'command': command, 'resolved_executable': resolved}
    if resolved is None:
        return {**result, 'available': False}
    try:
        done = subprocess.run(command, text=True, encoding='utf-8', errors='replace',
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=20)
        return {**result, 'available': True, 'returncode': done.returncode, 'output': done.stdout}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {**result, 'available': True, 'error': str(exc)}


class Session:
    def __init__(self, folder: Path, executables: dict[str, Path], timeout: float,
                 cache_policies: dict[str, str | None] | None = None):
        self.folder = folder
        self.executables = executables
        self.timeout = timeout
        self.cache_policies = cache_policies or {}
        self.runs: list[dict] = []

    def invoke(self, variant: str, label: str, arguments: list[str], *,
               report: bool = True, snapshot: bool = False) -> dict:
        report_path = self.folder / f'{label}.json'
        snapshot_path = self.folder / f'{label}.snapshot'
        command = [str(self.executables[variant]), *arguments]
        cache_policy = self.cache_policies.get(variant)
        if report and cache_policy is not None:
            command.extend(['--cache-policy', cache_policy])
        if report:
            command.extend(['--report', str(report_path)])
        if snapshot:
            command.extend(['--snapshot', str(snapshot_path)])
        entry = {'variant': variant, 'label': label, 'command': command,
                 'working_directory': str(self.folder), 'started_at_utc': utc_now(),
                 'log_path': str(self.folder / f'{label}.log')}
        self.runs.append(entry)
        print(f'[{len(self.runs)}] {label}', flush=True)
        started = time.perf_counter()
        try:
            completed = subprocess.run(command, cwd=self.folder, text=True, encoding='utf-8',
                                       errors='replace', stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, timeout=self.timeout)
        except subprocess.TimeoutExpired as exc:
            entry['status'] = 'timeout'
            entry['process_wall_ms'] = (time.perf_counter() - started) * 1000
            output = exc.stdout or ''
            if isinstance(output, bytes):
                output = output.decode('utf-8', errors='replace')
            Path(entry['log_path']).write_text(output, encoding='utf-8')
            raise RuntimeError(f'{label}: exceeded {self.timeout} seconds') from exc
        entry['process_wall_ms'] = (time.perf_counter() - started) * 1000
        entry['ended_at_utc'] = utc_now()
        entry['returncode'] = completed.returncode
        Path(entry['log_path']).write_text(completed.stdout, encoding='utf-8')
        if completed.returncode:
            entry['status'] = 'failed'
            raise RuntimeError(f'{label}: exit {completed.returncode}; read {entry["log_path"]}')
        if report:
            entry['report_path'] = str(report_path)
            entry['report'] = json.loads(report_path.read_text(encoding='utf-8'))
            if cache_policy is not None and entry['report'].get('cache_policy') != cache_policy:
                raise AssertionError(f'{label}: reported cache policy does not match requested {cache_policy}')
            entry['cuda_event_ms_including_launch_gaps'] = entry['report']['cuda_event_ms_including_launch_gaps']
            entry['circulation_wall_ms'] = entry['report']['wall_seconds'] * 1000
            for metric in METRICS:
                value = entry[metric]
                if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                    raise AssertionError(f'{label}: invalid {metric}: {value}')
        if snapshot:
            entry['snapshot_path'] = str(snapshot_path)
            entry['snapshot_bytes'] = snapshot_path.stat().st_size
            entry['snapshot_sha256'] = sha256(snapshot_path)
        entry['status'] = 'passed'
        return entry


def equivalence_cases() -> list[dict]:
    # A 16x16 page contains 16 blocks: the active=7 rolling window crosses page
    # boundaries and wraps around the 48-block field. 257 also leaves a partial
    # CUDA block and exceeds the 256-block size of a 64x64 texture page.
    partial = ['--pages', '3', '--page-side', '16', '--blocks-per-step', '7', '--steps', '20']
    return [
        {'name': 'partial_page_wrap', 'arguments': partial},
        {'name': 'partial_cta_page_wrap', 'arguments': ['--pages', '3', '--page-side', '64',
             '--blocks-per-step', '257', '--steps', '9']},
        {'name': 'whole_field', 'arguments': ['--pages', '2', '--page-side', '16',
             '--blocks-per-step', '32', '--steps', '5']},
        {'name': 'one_block', 'arguments': ['--pages', '1', '--page-side', '4',
             '--blocks-per-step', '1', '--steps', '3']},
        {'name': 'freeze_operators', 'arguments': partial + ['--freeze-operators']},
        {'name': 'no_jitter', 'arguments': partial + ['--no-jitter']},
        {'name': 'inverse_zero', 'arguments': partial + ['--inverse-gain', '0']},
        {'name': 'hops_zero', 'arguments': partial + ['--hops', '0']},
    ]


def run_equivalence(session: Session, codecs: list[str], common: list[str]) -> list[dict]:
    checks = []
    for codec in codecs:
        for index, case in enumerate(equivalence_cases()):
            name = f'{codec}_{case["name"]}'
            arguments = common + ['--codec', codec, '--batch', '1'] + case['arguments']
            order = ('reference', 'optimized') if index % 2 == 0 else ('optimized', 'reference')
            pair = {
                variant: session.invoke(variant, f'equivalence_{name}_{variant}', arguments, snapshot=True)
                for variant in order
            }
            check_snapshot_pair(pair['reference'], pair['optimized'], name)
            checks.append({'name': name, 'status': 'passed',
                           'reference_label': pair['reference']['label'],
                           'optimized_label': pair['optimized']['label'],
                           'full_snapshot_sha256': pair['reference']['snapshot_sha256'],
                           'snapshot_bytes': pair['reference']['snapshot_bytes']})
            if case['name'] == 'partial_page_wrap':
                for variant in ('reference', 'optimized'):
                    sequential = session.invoke(variant, f'equivalence_{name}_{variant}_no_graph',
                                                arguments + ['--no-graph'], snapshot=True)
                    check_snapshot_pair(pair[variant], sequential, f'{name}_{variant}_graph_vs_sequential')
                    checks.append({'name': f'{name}_{variant}_graph_vs_sequential', 'status': 'passed',
                                   'full_snapshot_sha256': sequential['snapshot_sha256'],
                                   'graph_label': pair[variant]['label'],
                                   'sequential_label': sequential['label']})
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('reference', type=Path)
    parser.add_argument('optimized', type=Path)
    parser.add_argument('--out', type=Path, required=True, help='New output directory; existing paths are refused')
    parser.add_argument('--codecs', nargs='+', choices=['bc5', 'rg8'], default=['bc5', 'rg8'])
    parser.add_argument('--pages', type=int, default=2)
    parser.add_argument('--page-side', type=int, default=1024)
    parser.add_argument('--blocks-per-step', type=int, default=65536)
    parser.add_argument('--steps', type=int, default=1024)
    parser.add_argument('--batch', type=int, default=32)
    parser.add_argument('--repeats', type=int, default=5)
    parser.add_argument('--warmups', type=int, default=1, help='Excluded full process runs per build and codec')
    parser.add_argument('--device', type=int, default=0)
    parser.add_argument('--seed', type=int, default=756)
    parser.add_argument('--dt', type=float, default=0.015625)
    parser.add_argument('--hops', type=int, default=2)
    parser.add_argument('--inverse-gain', type=float, default=0.25)
    parser.add_argument('--no-jitter', action='store_true')
    parser.add_argument('--freeze-operators', action='store_true')
    parser.add_argument('--operators', type=Path)
    parser.add_argument('--no-graph', action='store_true', help='Time sequential launches; small equivalence checks still cover both')
    parser.add_argument('--reference-cache-policy', choices=['l1', 'balanced', 'shared'], default=None,
                        help='Override reference cache preference in equivalence/warmup/timed runs; omitted uses executable default')
    parser.add_argument('--optimized-cache-policy', choices=['l1', 'balanced', 'shared'], default=None,
                        help='Override optimized cache preference in equivalence/warmup/timed runs; omitted uses executable default')
    parser.add_argument('--timeout-seconds', type=float, default=300)
    parser.add_argument('--equivalence-only', action='store_true')
    parser.add_argument('--skip-equivalence', action='store_true', help='Only use after saving a successful equivalence run')
    args = parser.parse_args(argv)
    for name in ('pages', 'page_side', 'blocks_per_step', 'steps', 'batch', 'repeats'):
        if getattr(args, name) <= 0:
            parser.error(f'--{name.replace("_", "-")} must be positive')
    if args.page_side % 4 or args.warmups < 0 or args.device < 0 or args.seed < 0 or args.hops < 0:
        parser.error('Page side must be a multiple of four and counts/seed/device cannot be negative')
    if not math.isfinite(args.dt) or args.dt <= 0 or not math.isfinite(args.inverse_gain):
        parser.error('dt must be finite and positive; inverse gain must be finite')
    if not math.isfinite(args.timeout_seconds) or args.timeout_seconds <= 0:
        parser.error('timeout must be finite and positive')
    if args.equivalence_only and args.skip_equivalence:
        parser.error('--equivalence-only and --skip-equivalence are incompatible')
    if len(set(args.codecs)) != len(args.codecs):
        parser.error('Do not repeat codecs')
    executables = {'reference': args.reference.resolve(), 'optimized': args.optimized.resolve()}
    for executable in executables.values():
        if not executable.is_file():
            parser.error(f'Executable does not exist: {executable}')
    if executables['reference'] == executables['optimized']:
        parser.error('Reference and optimized must be separate executable paths')
    if args.operators and not args.operators.is_file():
        parser.error(f'Operator image does not exist: {args.operators}')
    folder = args.out.resolve()
    folder.mkdir(parents=True, exist_ok=False)
    session = Session(folder, executables, args.timeout_seconds,
                      {'reference': args.reference_cache_policy, 'optimized': args.optimized_cache_policy})
    result = {
        'schema_version': 1,
        'status': 'running', 'started_at_utc': utc_now(),
        'harness_path': str(Path(__file__).resolve()), 'harness_sha256': sha256(Path(__file__)),
        'invocation_argv': [sys.executable, str(Path(__file__).resolve()), *(argv if argv is not None else sys.argv[1:])],
        'configuration': {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()},
        'executables': {key: {'path': str(value), 'sha256': sha256(value)} for key, value in executables.items()},
        'environment': {
            'platform': platform.platform(), 'python_version': sys.version,
            'python_executable': sys.executable, 'cpu': platform.processor(), 'cpu_count': os.cpu_count(),
            'cuda_visible_devices': os.environ.get('CUDA_VISIBLE_DEVICES'),
            'nvidia_smi_before': capture_environment_command(['nvidia-smi']),
            'nvcc': capture_environment_command(['nvcc', '--version']),
            'git_revision': capture_environment_command(['git', '-C', str(Path(__file__).resolve().parents[1]), 'rev-parse', 'HEAD']),
        },
        'measurement_notes': [
            'All builds receive identical recurrence arguments for each comparison.',
            'Cache policy affects cache/shared-memory allocation preference and scheduling, not the recurrence definition; differing policies combine policy and kernel effects in the speedup.',
            'Explicit per-build cache preferences apply to full-field equivalence checks, warmups and timed runs; omitted preferences retain executable defaults.',
            'Full snapshot SHA256 checks cover field bytes, auxiliary history/inverse-T, both operator banks and control state.',
            'Warmups are separate excluded processes, not uncounted recurrence steps inside measured runs.',
            'Timed pairs alternate reference-first and optimized-first; no snapshot is exported during performance trials.',
            'CUDA-event and circulation-wall timings include host launch gaps and batch synchronization.',
            'Process wall includes CUDA context creation, allocation, initialization, report writing and teardown.',
            'A speedup above one means optimized was faster; medians and sample dispersion are descriptive, not a significance test.',
            'Small snapshot agreement is evidence for exercised inputs only, not a proof over all possible states.',
            'Allocated bytes are not cache occupancy, physical residency, achieved DRAM bandwidth or a physical double-slit observation.',
        ],
        'equivalence': [], 'performance': {}, 'runs': session.runs,
    }
    if args.operators:
        result['operator_image'] = {'path': str(args.operators.resolve()), 'sha256': sha256(args.operators)}
    report_path = folder / 'benchmark.json'

    def save() -> None:
        temporary = report_path.with_suffix('.json.partial')
        temporary.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
        temporary.replace(report_path)

    common = ['--device', str(args.device), '--seed', str(args.seed), '--dt', str(args.dt),
              '--hops', str(args.hops), '--inverse-gain', str(args.inverse_gain)]
    if args.no_jitter:
        common.append('--no-jitter')
    if args.freeze_operators:
        common.append('--freeze-operators')
    if args.operators:
        common.extend(['--operators', str(args.operators.resolve())])
    try:
        save()
        for variant in executables:
            session.invoke(variant, f'{variant}_probe', ['--device', str(args.device), '--probe'], report=False)
            session.invoke(variant, f'{variant}_self_test', ['--device', str(args.device), '--self-test'], report=False)
        if not args.skip_equivalence:
            result['equivalence'] = run_equivalence(session, args.codecs, common)
        else:
            result['equivalence_status'] = 'skipped_by_request; no full-field equivalence assertion in this run'
        save()
        if not args.equivalence_only:
            for codec_index, codec in enumerate(args.codecs):
                arguments = common + ['--codec', codec, '--pages', str(args.pages),
                    '--page-side', str(args.page_side), '--blocks-per-step', str(args.blocks_per_step),
                    '--steps', str(args.steps), '--batch', str(args.batch)]
                if args.no_graph:
                    arguments.append('--no-graph')
                for warmup in range(args.warmups):
                    for variant in ('reference', 'optimized'):
                        session.invoke(variant, f'warmup_{codec}_{warmup}_{variant}', arguments)
                pairs = []
                result['performance'][codec] = {'pairs': pairs}
                for trial in range(args.repeats):
                    order = ('reference', 'optimized') if (trial + codec_index) % 2 == 0 else ('optimized', 'reference')
                    pair = {'trial': trial, 'order': list(order)}
                    for variant in order:
                        pair[variant] = session.invoke(variant, f'timed_{codec}_{trial}_{variant}', arguments)
                    compare_reports(pair['reference']['report'], pair['optimized']['report'], f'timed_{codec}_{trial}')
                    if pairs:
                        for variant in ('reference', 'optimized'):
                            compare_reports(pairs[0][variant]['report'], pair[variant]['report'], f'{codec}_{variant}_repeat')
                    pairs.append(pair)
                    result['performance'][codec]['summary'] = summarize_pairs(pairs)
                    save()
        result['status'] = 'passed'
    except (Exception, KeyboardInterrupt) as exc:
        result['status'] = 'failed'
        result['error'] = f'{type(exc).__name__}: {exc}'
        print(result['error'], file=sys.stderr)
    finally:
        result['environment']['nvidia_smi_after'] = capture_environment_command(['nvidia-smi'])
        result['ended_at_utc'] = utc_now()
        save()
        print(report_path, flush=True)
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
