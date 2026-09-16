"""Offline checks of benchmark evidence handling; these never launch GPU work."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('benchmark_optimization', ROOT / 'tools' / 'benchmark_optimization.py')
BENCH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BENCH)


def fake_cuda_run(command, **kwargs):
    """Produce reports/snapshots without invoking a shell, process or CUDA."""
    if '--report' not in command:
        return SimpleNamespace(returncode=0, stdout='offline fixture\n')
    options = {}
    index = 1
    while index < len(command):
        key = command[index]
        if index + 1 < len(command) and not command[index + 1].startswith('--'):
            options[key] = command[index + 1]
            index += 2
        else:
            options[key] = True
            index += 1
    side = int(options['--page-side'])
    pages = int(options['--pages'])
    total = pages * (side // 4) ** 2
    active = min(int(options['--blocks-per-step']), total)
    steps = int(options['--steps'])
    elapsed = 10.0 if Path(command[0]).name == 'reference.exe' else 5.0
    report = {
        'device': 'offline fixture', 'compute_capability': '12.0', 'cuda_runtime': 12080,
        'cuda_driver': 12080, 'codec': options['--codec'], 'total_device_bytes': 123456789,
        'pages': pages, 'page_side': side, 'token_pairs': total * 16,
        'blocks_per_interval': active, 'payload_bytes': total * 24, 'start_epoch': 0,
        'end_epoch': steps, 'visited_blocks_this_run': steps * active,
        'complete_sweeps_this_run': steps * active // total,
        'total_complete_sweeps': steps * active // total,
        'software_codec_mean_absolute_token_error': 0,
        'operator_digest_fnv1a64': 'same-operator-hash-even-if-field-differs',
        'cache_policy': options.get('--cache-policy', 'executable_default'),
        'cuda_event_ms_including_launch_gaps': elapsed,
        'wall_seconds': elapsed / 1000,
        'token_pair_updates_per_second': steps * active * 16 * 1000 / elapsed,
    }
    Path(options['--report']).write_text(json.dumps(report), encoding='utf-8')
    if '--snapshot' in options:
        state = {key: value for key, value in options.items()
                 if key not in ('--report', '--snapshot', '--no-graph', '--cache-policy')}
        Path(options['--snapshot']).write_text(json.dumps(state, sort_keys=True), encoding='utf-8')
    return SimpleNamespace(returncode=0, stdout='offline fixture\n')


class BenchmarkEvidenceTests(unittest.TestCase):
    def run_fixture(self, folder, runner=fake_cuda_run, extra=None):
        reference = folder / 'reference.exe'
        optimized = folder / 'optimized.exe'
        reference.write_bytes(b'reference fixture, not executable')
        optimized.write_bytes(b'optimized fixture, not executable')
        output = folder / 'result'
        arguments = [str(reference), str(optimized), '--out', str(output), '--codecs', 'rg8',
                     '--repeats', '3', '--warmups', '1', *(extra or [])]
        with patch.object(BENCH.subprocess, 'run', side_effect=runner), \
             patch.object(BENCH, 'capture_environment_command', return_value={'offline_fixture': True}), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = BENCH.main(arguments)
        return code, json.loads((output / 'benchmark.json').read_text(encoding='utf-8'))

    def test_alternating_trials_warmup_exclusion_and_speedup(self):
        with tempfile.TemporaryDirectory() as directory:
            code, report = self.run_fixture(Path(directory))
        self.assertEqual(code, 0)
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(len(report['equivalence']), 10)
        pairs = report['performance']['rg8']['pairs']
        self.assertEqual([pair['order'] for pair in pairs],
                         [['reference', 'optimized'], ['optimized', 'reference'], ['reference', 'optimized']])
        summary = report['performance']['rg8']['summary']['cuda_event_ms_including_launch_gaps']
        self.assertEqual(summary['reference']['count'], 3)
        self.assertEqual(summary['reference_over_optimized_ratio_of_medians'], 2)
        self.assertEqual(summary['paired_reference_over_optimized_speedup']['median'], 2)
        self.assertEqual(summary['optimized']['median_absolute_deviation'], 0)
        timed = [run for run in report['runs'] if run['label'].startswith('timed_')]
        self.assertEqual(len(timed), 6)
        self.assertTrue(all('--snapshot' not in run['command'] for run in timed))
        self.assertTrue(all('command' in run and 'process_wall_ms' in run for run in report['runs']))
        self.assertTrue(all('--cache-policy' not in run['command'] for run in report['runs']))

    def test_cache_policies_are_independent_and_do_not_change_state_comparisons(self):
        with tempfile.TemporaryDirectory() as directory:
            code, report = self.run_fixture(Path(directory), extra=[
                '--reference-cache-policy', 'l1', '--optimized-cache-policy', 'balanced'])
        self.assertEqual(code, 0)
        self.assertEqual(report['configuration']['reference_cache_policy'], 'l1')
        self.assertEqual(report['configuration']['optimized_cache_policy'], 'balanced')
        for run in report['runs']:
            command = run['command']
            if 'report' in run:
                expected = 'l1' if run['variant'] == 'reference' else 'balanced'
                self.assertEqual(command[command.index('--cache-policy') + 1], expected)
                self.assertEqual(run['report']['cache_policy'], expected)
            else:
                self.assertNotIn('--cache-policy', command)

    def test_full_field_difference_fails_even_when_operator_digest_matches(self):
        def corrupt_snapshot(command, **kwargs):
            result = fake_cuda_run(command, **kwargs)
            if Path(command[0]).name == 'optimized.exe' and '--snapshot' in command:
                path = Path(command[command.index('--snapshot') + 1])
                path.write_bytes(path.read_bytes() + b'changed field, identical operators')
            return result
        with tempfile.TemporaryDirectory() as directory:
            code, report = self.run_fixture(Path(directory), corrupt_snapshot)
        self.assertEqual(code, 1)
        self.assertEqual(report['status'], 'failed')
        self.assertIn('full snapshot SHA256 mismatch', report['error'])
        self.assertFalse(report['performance'])
        self.assertTrue(any('snapshot_sha256' in run for run in report['runs']))

    def test_timing_report_recurrence_mismatch_fails(self):
        def alter_report(command, **kwargs):
            result = fake_cuda_run(command, **kwargs)
            if Path(command[0]).name == 'optimized.exe' and '--report' in command:
                path = Path(command[command.index('--report') + 1])
                report = json.loads(path.read_text(encoding='utf-8'))
                report['visited_blocks_this_run'] -= 1
                path.write_text(json.dumps(report), encoding='utf-8')
            return result
        with tempfile.TemporaryDirectory() as directory:
            code, report = self.run_fixture(Path(directory), alter_report,
                                            ['--skip-equivalence', '--warmups', '0'])
        self.assertEqual(code, 1)
        self.assertIn('report invariants differ', report['error'])
        self.assertIn('visited_blocks_this_run', report['error'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
