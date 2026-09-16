#!/usr/bin/env python3
"""Sequential validation and repeated timing of the integer-1 device variants.

  python tools/measure_integer.py --mode validate --out results/integer/validation
  python tools/measure_integer.py --mode bench --out results/integer/benchmark
  python tools/measure_integer.py --mode bench --include-l1 --steps 128 --out work/tuning
  python tools/measure_integer.py --mode validate --include-cached --out results/integer/validation_final

Every subprocess completes before the next starts. Existing output directories
are refused. Validation compares complete v4 state; timing compares the same
integer law across variants, not against the semantically different float v0.3.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import shutil
import statistics
import struct
import subprocess
import sys
import time


VARIANTS = ('shared', 'texture', 'reference')
NAMES = {'shared': 'dawnwood_integer', 'texture': 'dawnwood_integer_texture',
         'reference': 'dawnwood_integer_reference', 'cpu_math': 'dawnwood_integer_math_tests',
         'cpu_core': 'dawnwood_integer_core_tests', 'cached': 'dawnwood_integer_cached',
         'cpu_pair': 'dawnwood_integer_pair_cache_tests'}
VARIANT_LABELS = {'shared': 'shared-masked', 'texture': 'texture-direct',
                  'reference': 'shared-reference', 'cached': 'texture-cached'}
FINAL_INVARIANTS = (
    'edition', 'version', 'device', 'compute_capability', 'cuda_runtime', 'cuda_driver',
    'codec', 'pages', 'page_side', 'payload_bytes', 'token_pairs', 'blocks_per_interval',
    'end_epoch', 'total_complete_sweeps', 'operator_digest_fnv1a64',
    'seed', 'dt_q16', 'inverse_gain_q16', 'hops', 'jitter', 'mutation',
)
RUN_INVARIANTS = FINAL_INVARIANTS + (
    'start_epoch', 'visited_blocks_this_run', 'complete_sweeps_this_run',
    'software_codec_mean_absolute_token_error',
)
METRICS = ('cuda_event_ms_including_launch_gaps', 'circulation_wall_ms', 'process_wall_ms')
SNAPSHOT_MAGIC = 0x3149545257445744
LEGACY_MAGIC = 0x3358545257445744


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def stats(values):
    if not values or any(not math.isfinite(value) or value <= 0 for value in values):
        raise AssertionError('Timing, rate and speedup samples must be finite and positive')
    median = statistics.median(values)
    return {'samples': values, 'count': len(values), 'median': median, 'min': min(values),
            'max': max(values), 'median_absolute_deviation': statistics.median(abs(value - median) for value in values),
            'sample_standard_deviation': statistics.stdev(values) if len(values) > 1 else None}


def compare_reports(left, right, label, continuation=False):
    fields = FINAL_INVARIANTS if continuation else RUN_INVARIANTS
    differences = {key: [left.get(key), right.get(key)] for key in fields
                   if key not in left or key not in right or left[key] != right[key]}
    if differences:
        raise AssertionError(f'{label}: integer-law report mismatch: {differences}')


def compare_snapshots(left, right, label, continuation=False):
    compare_reports(left['report'], right['report'], label, continuation)
    if left['snapshot_sha256'] != right['snapshot_sha256']:
        raise AssertionError(f'{label}: complete v4 snapshot SHA256 mismatch')
    return {'name': label, 'status': 'passed', 'left': left['label'], 'right': right['label'],
            'snapshot_sha256': left['snapshot_sha256'], 'snapshot_bytes': left['snapshot_bytes']}


def check_fresh_parameters(report, *, codec, pages, side, active, steps, seed, hops,
                           dt_q16=1024, inverse_gain_q16=16384, jitter=1, mutation=1):
    total_blocks = pages * (side // 4) ** 2
    effective_active = min(active, total_blocks)
    expected = {'codec': codec, 'pages': pages, 'page_side': side, 'blocks_per_interval': effective_active,
                'start_epoch': 0, 'end_epoch': steps, 'visited_blocks_this_run': steps * effective_active,
                'seed': seed, 'hops': hops, 'dt_q16': dt_q16, 'inverse_gain_q16': inverse_gain_q16,
                'jitter': jitter, 'mutation': mutation}
    differences = {key: [value, report.get(key)] for key, value in expected.items() if report.get(key) != value}
    if differences:
        raise AssertionError(f'Requested recurrence arguments were not honored: {differences}')


def inspect_snapshot(path, report):
    size = path.stat().st_size
    with path.open('rb') as stream:
        header = stream.read(40)
    if len(header) != 40:
        raise AssertionError(f'Truncated snapshot header: {path}')
    magic, version, side, pages, exact, control_bytes, operator_bytes = struct.unpack('<QIIIIQQ', header)
    expected = 40 + control_bytes + 2 * operator_bytes + report['payload_bytes']
    if (magic != SNAPSHOT_MAGIC or version != 4 or side != report['page_side']
            or pages != report['pages'] or exact != int(report['codec'] == 'rg8')
            or operator_bytes != 1984 or control_bytes != 96 or size != expected):
        raise AssertionError(f'Unexpected v4 snapshot dimensions/format/length: {path}')
    return {'snapshot_bytes': size, 'snapshot_sha256': sha256(path),
            'snapshot_header': {'magic': hex(magic), 'version': version, 'control_bytes': control_bytes,
                                'operator_bytes_per_bank': operator_bytes}}


def capture(command):
    if shutil.which(command[0]) is None:
        return {'command': command, 'available': False}
    try:
        process = subprocess.run(command, text=True, encoding='utf-8', errors='replace',
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=20)
        return {'command': command, 'returncode': process.returncode, 'output': process.stdout}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'command': command, 'error': str(error)}


class Runner:
    def __init__(self, folder, executables, timeout, result, save):
        self.folder, self.executables, self.timeout = folder, executables, timeout
        self.result, self.save = result, save

    def run(self, variant, label, arguments, *, report=True, snapshot=False,
            expected_failure=None, cache_policy='balanced'):
        command = [str(self.executables[variant]), *arguments]
        report_path, snapshot_path = self.folder/f'{label}.json', self.folder/f'{label}.snapshot'
        if report:
            command.extend(['--cache-policy', cache_policy, '--report', str(report_path)])
        if snapshot:
            command.extend(['--snapshot', str(snapshot_path)])
        entry = {'variant': variant, 'label': label, 'command': command, 'cwd': str(self.folder),
                 'started_at_utc': utc_now(), 'log_path': str(self.folder/f'{label}.log'), 'status': 'running'}
        self.result['runs'].append(entry)
        self.save()
        print(f'[{len(self.result["runs"])}] {label}', flush=True)
        start = time.perf_counter()
        try:
            process = subprocess.run(command, cwd=self.folder, text=True, encoding='utf-8', errors='replace',
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=self.timeout)
        except subprocess.TimeoutExpired as error:
            entry['status'] = 'timeout'
            entry['process_wall_ms'] = (time.perf_counter() - start) * 1000
            output = error.stdout or ''
            if isinstance(output, bytes):
                output = output.decode('utf-8', errors='replace')
            Path(entry['log_path']).write_text(output, encoding='utf-8')
            entry['log_sha256'] = sha256(entry['log_path'])
            self.save()
            raise RuntimeError(f'{label}: exceeded {self.timeout} seconds') from error
        entry['process_wall_ms'] = (time.perf_counter() - start) * 1000
        entry['returncode'] = process.returncode
        entry['ended_at_utc'] = utc_now()
        Path(entry['log_path']).write_text(process.stdout, encoding='utf-8')
        entry['log_sha256'] = sha256(entry['log_path'])
        entry['status'] = 'failed'
        if expected_failure is not None:
            entry['expected_failure'] = expected_failure
            if not process.returncode or expected_failure not in process.stdout:
                self.save()
                raise AssertionError(f'{label}: expected explicit rejection {expected_failure!r}, got exit {process.returncode}')
            entry['status'] = 'passed_expected_rejection'
            self.save()
            return entry
        if process.returncode:
            self.save()
            raise RuntimeError(f'{label}: exit {process.returncode}; read {entry["log_path"]}')
        if report:
            measured = json.loads(report_path.read_text(encoding='utf-8'))
            entry.update({'report': measured, 'report_path': str(report_path), 'report_sha256': sha256(report_path),
                          'cuda_event_ms_including_launch_gaps': measured['cuda_event_ms_including_launch_gaps'],
                          'circulation_wall_ms': measured['wall_seconds'] * 1000})
            if measured.get('edition') != 'integer-1' or measured.get('kernel_variant') != VARIANT_LABELS[variant]:
                raise AssertionError(f'{label}: executable reports an unexpected edition or variant')
            if measured.get('cache_policy') != cache_policy:
                raise AssertionError(f'{label}: cache-policy override was not honored')
            for metric in METRICS:
                if not math.isfinite(entry[metric]) or entry[metric] <= 0:
                    raise AssertionError(f'{label}: invalid timing {metric}')
        if snapshot:
            entry['snapshot_path'] = str(snapshot_path)
            entry.update(inspect_snapshot(snapshot_path, entry['report']))
        entry['status'] = 'passed'
        self.save()
        return entry


def validation_cases():
    return [
        {'name': 'evolving_partial37', 'side': 32, 'active': 37, 'seed': 756, 'hops': 2, 'extra': []},
        {'name': 'frozen_partial127', 'side': 32, 'active': 127, 'seed': 757, 'hops': 3, 'extra': ['--freeze-operators']},
        {'name': 'nojitter_partial127', 'side': 64, 'active': 127, 'seed': 991, 'hops': 1, 'extra': ['--no-jitter']},
        {'name': 'zero_hops_and_gain', 'side': 32, 'active': 37, 'seed': 1021, 'hops': 0,
         'extra': ['--inverse-gain-q16', '0']},
    ]


def run_validation(runner, args, result):
    variants = VARIANTS + (('cached',) if args.include_cached else ())
    for variant in ('cpu_math', 'cpu_core') + (('cpu_pair',) if args.include_cached else ()):
        runner.run(variant, variant, [], report=False)
    runner.run('shared', 'gpu_probe', ['--device', str(args.device), '--probe'], report=False)
    for variant in variants:
        runner.run(variant, f'{variant}_self_test', ['--device', str(args.device), '--self-test'], report=False)
    checks = result['checks']
    for codec in args.codecs:
        for case in validation_cases():
            common = ['--device', str(args.device), '--codec', codec, '--pages', '3',
                      '--page-side', str(case['side']), '--blocks-per-step', str(case['active']),
                      '--batch', '1', '--seed', str(case['seed']), '--hops', str(case['hops']),
                      '--dt-q16', '1024', '--inverse-gain-q16', '16384', *case['extra']]
            whole = {variant: runner.run(variant, f'{codec}_{case["name"]}_{variant}',
                                          common + ['--steps', '13'], snapshot=True) for variant in variants}
            for run in whole.values():
                check_fresh_parameters(run['report'], codec=codec, pages=3, side=case['side'], active=case['active'],
                    steps=13, seed=case['seed'], hops=case['hops'],
                    inverse_gain_q16=0 if '--inverse-gain-q16' in case['extra'] else 16384,
                    jitter=int('--no-jitter' not in case['extra']), mutation=int('--freeze-operators' not in case['extra']))
            for variant in variants[1:]:
                checks.append(compare_snapshots(whole['shared'], whole[variant], f'{codec}_{case["name"]}_shared_vs_{variant}'))
            if case['name'] != 'evolving_partial37':
                runner.save()
                continue
            for variant in variants:
                sequential = runner.run(variant, f'{codec}_{variant}_no_graph',
                                        common + ['--steps', '13', '--no-graph'], snapshot=True)
                checks.append(compare_snapshots(whole[variant], sequential, f'{codec}_{variant}_graph_vs_sequential'))
            pieces = {variant: runner.run(variant, f'{codec}_{variant}_split6',
                                         common + ['--steps', '6'], snapshot=True) for variant in variants}
            for index, source in enumerate(variants):
                destination = variants[(index + 1) % len(variants)]
                resumed = runner.run(destination, f'{codec}_resume_{source}_to_{destination}',
                    ['--device', str(args.device), '--resume', pieces[source]['snapshot_path'], '--steps', '7', '--batch', '1'], snapshot=True)
                checks.append(compare_snapshots(whole[destination], resumed,
                                               f'{codec}_6_plus_7_cross_resume_{source}_to_{destination}', continuation=True))
            resumed = runner.run('shared', f'{codec}_resume_shared_to_shared',
                ['--device', str(args.device), '--resume', pieces['shared']['snapshot_path'], '--steps', '7', '--batch', '1'], snapshot=True)
            checks.append(compare_snapshots(whole['shared'], resumed, f'{codec}_6_plus_7_same_variant_resume', continuation=True))
            runner.save()
    # A real historical header, when supplied, is sufficient: rejection must
    # occur at magic/version validation before any legacy control can be read.
    legacy_path = runner.folder/'historical_v3_header.snapshot'
    legacy_source = args.legacy_snapshot
    if legacy_source:
        with legacy_source.open('rb') as stream:
            header = stream.read(40)
        if len(header) != 40 or struct.unpack_from('<QI', header) != (LEGACY_MAGIC, 3):
            raise AssertionError('Provided legacy snapshot does not have the historical v3 header')
        legacy_path.write_bytes(header)
        result['legacy_fixture'] = {'source_path': str(legacy_source.resolve()), 'source_sha256': sha256(legacy_source),
                                    'fixture_scope': 'first 40 bytes of supplied historical snapshot'}
    else:
        legacy_path.write_bytes(struct.pack('<QIIIIQQ', LEGACY_MAGIC, 3, 4, 1, 1, 96, 1984))
        result['legacy_fixture'] = {'fixture_scope': 'synthetic historical v3 header with valid legacy magic/version'}
    result['legacy_fixture'].update({'path': str(legacy_path), 'sha256': sha256(legacy_path)})
    for variant in variants:
        rejection = runner.run(variant, f'{variant}_reject_v3',
                               ['--device', str(args.device), '--resume', str(legacy_path), '--steps', '1'], report=False,
                               expected_failure='Invalid or incompatible integer-1 snapshot v4')
        checks.append({'name': f'{variant}_rejects_historical_v3', 'status': 'passed', 'run': rejection['label']})
    result['comparison_count'] = len(checks)


def summarize_benchmark(trials, configurations):
    summary = {'timings': {}, 'speedups_over_reference_balanced': {}}
    for configuration in configurations:
        name = configuration['name']
        summary['timings'][name] = {metric: stats([trial['runs'][name][metric] for trial in trials]) for metric in METRICS}
        summary['timings'][name]['token_pair_updates_per_second'] = stats([
            trial['runs'][name]['report']['token_pair_updates_per_second'] for trial in trials])
        if name != 'reference_balanced':
            summary['speedups_over_reference_balanced'][name] = {}
            for metric in METRICS:
                reference = summary['timings'].get('reference_balanced', {}).get(metric)
                # Reference is first in configurations, independent of execution order.
                if reference is None:
                    reference = stats([trial['runs']['reference_balanced'][metric] for trial in trials])
                summary['speedups_over_reference_balanced'][name][metric] = {
                    'ratio_of_medians': reference['median'] / summary['timings'][name][metric]['median'],
                    'paired_ratios': stats([trial['runs']['reference_balanced'][metric] / trial['runs'][name][metric]
                                           for trial in trials]),
                }
    return summary


def run_benchmark(runner, args, result):
    variants = ('reference', 'shared', 'texture') + (('cached',) if args.include_cached else ())
    configurations = [{'name': f'{variant}_balanced', 'variant': variant, 'cache_policy': 'balanced'}
                      for variant in variants]
    if args.include_l1:
        configurations += [{'name': f'{variant}_l1', 'variant': variant, 'cache_policy': 'l1'}
                           for variant in ('shared', 'texture') + (('cached',) if args.include_cached else ())]
    result['benchmark_configurations'] = configurations
    for codec in args.codecs:
        common = ['--device', str(args.device), '--codec', codec, '--pages', str(args.pages),
                  '--page-side', str(args.page_side), '--blocks-per-step', str(args.blocks_per_step),
                  '--steps', str(args.steps), '--batch', str(args.batch), '--seed', str(args.seed),
                  '--dt-q16', str(args.dt_q16), '--inverse-gain-q16', str(args.inverse_gain_q16), '--hops', str(args.hops)]
        if args.no_jitter:
            common.append('--no-jitter')
        if args.freeze_operators:
            common.append('--freeze-operators')
        if args.no_graph:
            common.append('--no-graph')
        for warmup in range(args.warmups):
            for config in configurations:
                runner.run(config['variant'], f'{codec}_warmup{warmup}_{config["name"]}', common,
                           cache_policy=config['cache_policy'])
        trials = []
        result['performance'][codec] = {'trials': trials}
        for trial_index in range(args.repeats):
            offset = trial_index % len(configurations)
            order = configurations[offset:] + configurations[:offset]
            trial = {'trial': trial_index, 'order': [config['name'] for config in order], 'runs': {}}
            trials.append(trial)
            for config in order:
                run = runner.run(config['variant'], f'{codec}_trial{trial_index}_{config["name"]}', common,
                                 cache_policy=config['cache_policy'])
                trial['runs'][config['name']] = run
            reference = trial['runs']['reference_balanced']['report']
            for name, run in trial['runs'].items():
                check_fresh_parameters(run['report'], codec=codec, pages=args.pages, side=args.page_side,
                    active=args.blocks_per_step, steps=args.steps, seed=args.seed, hops=args.hops,
                    dt_q16=args.dt_q16, inverse_gain_q16=args.inverse_gain_q16,
                    jitter=int(not args.no_jitter), mutation=int(not args.freeze_operators))
                compare_reports(reference, run['report'], f'{codec}_{trial_index}_{name}')
                if trial_index:
                    compare_reports(trials[0]['runs'][name]['report'], run['report'], f'{codec}_{name}_repeat')
            result['performance'][codec]['summary'] = summarize_benchmark(trials, configurations)
            runner.save()


def resolve_executables(build_dir, mode, include_cached=False):
    keys = VARIANTS + (('cached',) if include_cached else ())
    if mode == 'validate':
        keys += ('cpu_math', 'cpu_core') + (('cpu_pair',) if include_cached else ())
    names = {key: NAMES[key] for key in keys}
    result = {}
    for key, name in names.items():
        candidates = [directory / (name + suffix) for directory in (build_dir, build_dir/'Release')
                      for suffix in ('.exe', '')]
        executable = next((candidate.resolve() for candidate in candidates if candidate.is_file()), None)
        if executable is None:
            raise FileNotFoundError(f'Build target {name} was not found in {build_dir} or its Release directory')
        result[key] = executable
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--mode', choices=['validate', 'bench'], default='validate')
    parser.add_argument('--build-dir', type=Path, default=Path(__file__).resolve().parents[1]/'build')
    parser.add_argument('--codecs', nargs='+', choices=['bc5', 'rg8'], default=['bc5', 'rg8'])
    parser.add_argument('--device', type=int, default=0)
    parser.add_argument('--legacy-snapshot', type=Path, help='Optional real historical v3 snapshot; only its header is copied')
    parser.add_argument('--pages', type=int, default=4)
    parser.add_argument('--page-side', type=int, default=1024)
    parser.add_argument('--blocks-per-step', type=int, default=16384)
    parser.add_argument('--steps', type=int, default=64)
    parser.add_argument('--batch', type=int, default=32)
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--warmups', type=int, default=1)
    parser.add_argument('--seed', type=int, default=756)
    parser.add_argument('--dt-q16', type=int, default=1024)
    parser.add_argument('--inverse-gain-q16', type=int, default=16384)
    parser.add_argument('--hops', type=int, default=2)
    parser.add_argument('--no-jitter', action='store_true')
    parser.add_argument('--freeze-operators', action='store_true')
    parser.add_argument('--no-graph', action='store_true')
    parser.add_argument('--include-l1', action='store_true')
    parser.add_argument('--include-cached', action='store_true',
                        help='Add the fourth texture-cached variant and its CPU pair-cache test; requires those targets built')
    parser.add_argument('--timeout-seconds', type=float, default=300)
    args = parser.parse_args(argv)
    if any(getattr(args, key) <= 0 for key in ('pages', 'page_side', 'blocks_per_step', 'steps', 'batch', 'repeats')):
        parser.error('Dimensions, active window, steps, batch and repeats must be positive')
    if args.page_side < 4 or args.page_side & (args.page_side - 1) or args.page_side > 131072:
        parser.error('Page side must be a power of two in [4,131072]')
    if args.warmups < 0 or args.device < 0 or args.seed < 0 or args.hops < 0:
        parser.error('Warmups, device, seed and hops cannot be negative')
    if not 1 <= args.dt_q16 <= 65536 or not 0 <= args.inverse_gain_q16 <= 65536:
        parser.error('dt-q16 must be in [1,65536] and inverse-gain-q16 in [0,65536]')
    if not math.isfinite(args.timeout_seconds) or args.timeout_seconds <= 0:
        parser.error('Timeout must be finite and positive')
    if len(set(args.codecs)) != len(args.codecs):
        parser.error('Do not repeat codecs')
    if args.legacy_snapshot and not args.legacy_snapshot.is_file():
        parser.error('Legacy snapshot path does not exist')
    try:
        executables = resolve_executables(args.build_dir, args.mode, args.include_cached)
    except FileNotFoundError as error:
        parser.error(str(error))
    folder = args.out.resolve()
    folder.mkdir(parents=True, exist_ok=False)
    report_path = folder / ('validation.json' if args.mode == 'validate' else 'benchmark.json')
    result = {
        'schema_version': 1, 'edition': 'integer-1', 'mode': args.mode, 'status': 'running',
        'started_at_utc': utc_now(), 'harness_sha256': sha256(__file__),
        'invocation_argv': [sys.executable, str(Path(__file__).resolve()), *(argv if argv is not None else sys.argv[1:])],
        'configuration': {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()},
        'selected_variants': list(VARIANTS) + (['cached'] if args.include_cached else []),
        'executables': {key: {'path': str(value), 'sha256': sha256(value)} for key, value in executables.items()},
        'environment': {'platform': platform.platform(), 'python': sys.version,
                        'nvidia_smi_before': capture(['nvidia-smi']), 'nvcc': capture(['nvcc', '--version'])},
        'notes': [
            'All CPU/GPU subprocesses run sequentially; benchmark configuration order rotates between trials.',
            'Validation uses complete snapshots including both operator banks, Control and every field/auxiliary byte; masks are rebuilt on resume.',
            'Native BC5 decoder tolerance is checked in self-test; no tolerance is allowed between full GPU variant snapshots.',
            'Bench mode assumes separate successful validation of these executable hashes; timing alone is not full-state equivalence.',
            'Bench warmups are separate excluded processes; measured initial state and recurrence parameters are identical.',
            'CUDA-event and circulation wall include launch gaps/synchronization; full process wall also includes allocation, initialization and teardown.',
            'L1 tuning rows change scheduling preference; reference-balanced speedups then combine implementation and policy effects.',
            'These are comparisons within integer-1; historical float v0.3 timings do not establish same-law integer speedups.',
            'Integer device-arithmetic claims require the separate PTX/SASS audit and explicit native sampler boundary.',
        ],
        'runs': [], 'checks': [], 'performance': {},
    }

    def save():
        temporary = report_path.with_suffix('.json.partial')
        temporary.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
        temporary.replace(report_path)

    runner = Runner(folder, executables, args.timeout_seconds, result, save)
    try:
        save()
        if args.mode == 'validate':
            run_validation(runner, args, result)
        else:
            run_benchmark(runner, args, result)
        result['status'] = 'passed'
    except (Exception, KeyboardInterrupt) as error:
        result['status'] = 'failed'
        result['error'] = f'{type(error).__name__}: {error}'
        print(result['error'], file=sys.stderr)
    finally:
        result['environment']['nvidia_smi_after'] = capture(['nvidia-smi'])
        result['ended_at_utc'] = utc_now()
        save()
        print(report_path, flush=True)
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
