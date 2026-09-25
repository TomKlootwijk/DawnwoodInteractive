"""Local authoring and causal inspection of the existing Dawnwood GPU profile.

This tool never substitutes a new dynamical system for the supplied kernel.
It prepares explicit checkpoint interventions, runs the existing executable,
and compares complete returned records. Python 3.10+; standard library only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import threading
import time
import uuid
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / 'local_lab'
NATIVE = ROOT / 'Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3'
BINARY = NATIVE / 'bin/windows-rtx5070ti/dawnwood.exe'
RUNS = LAB / 'runs'
DEVICE = 'RTX 5070 Ti'
STATE = struct.Struct('<24f4I4f')
OPERATOR = struct.Struct('<12f4I')
CONFIG = struct.Struct('<4I4f4I4f')
STATE_FIELDS = ['u', 'v', 'rho', 'theta', 'ar', 'ai', 'br', 'bi', 'history',
                'inv00', 'inv01', 'inv10', 'inv11', 'field', 'delta', 'energy',
                'px', 'py', 'pz', 'pw', 'k1v', 'k2v', 'k3v', 'k4v', 'rng',
                'orientation', 'route', 'alpha_ref', 'previousTheta',
                'previousPreviousTheta', 'phaseResponse', 'lastJitter']
OP_FIELDS = ['u', 'v', 'radius', 'height', 'phase', 'gain', 'coupling', 'shear',
             'du', 'dv', 'mutationRate', 'reserved', 'program', 'seed', 'kind', 'flags']
OP_NAMES = ['klein', 'hadamard', 'phi', 'rk4', 'phyllotaxis', 'pinion', 'double_dot',
            'T_shape', 'pyramid', 'circle', 'cone', 'sphere', 'apex', 'delta_phi',
            'blend', 'wavefront', 'y_up', 'crystal', 'inverse_T', 'T_transform',
            'jitter', 'bst', 'return', 'phase_history', 'dichromatic', 'bayer',
            'bc5', 'split', 'parity', 'psi', 'mutation']
CONFIG_FIELDS = ['count', 'operators', 'epoch', 'depth', 'dt', 'yup', 'epsilon',
                 'mutation', 'jitter', 'feedback', 'reserved0', 'reserved1',
                 'phaseRate', 'radialRate', 'historyWeight', 'fieldScale']
spec = importlib.util.spec_from_file_location('dawnwood_checkpoint', NATIVE / 'tools/edit_checkpoint.py')
checkpoint_tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checkpoint_tools)


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save_json(path, value):
    temporary = path.with_name(path.name + '.partial')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    temporary.replace(path)


def request_settings(source):
    if not isinstance(source, dict):
        raise ValueError('Run settings must be an object')
    allowed = {'count', 'epochs', 'stride', 'mode', 'operator_index', 'program', 'shift_u', 'shift_v'}
    if set(source) - allowed:
        raise ValueError('Unknown run setting')
    defaults = dict(count=4096, epochs=32, stride=4, mode='compare', operator_index=30,
                    program='0x342', shift_u=0.2, shift_v=0.1)
    result = {**defaults, **source}
    for key, low, high in [('count', 1, 65536), ('epochs', 1, 128), ('stride', 1, 32),
                           ('operator_index', 0, 30)]:
        if type(result[key]) is not int or not low <= result[key] <= high:
            raise ValueError(f'{key} must be an integer from {low} to {high}')
    if math.ceil(result['epochs'] / result['stride']) > 32:
        raise ValueError('Choose a stride giving at most 32 recorded intervals')
    if result['mode'] not in ('single', 'compare', 'fidelity'):
        raise ValueError('Mode must be single, compare or fidelity')
    try:
        word = int(str(result['program']), 0)
    except ValueError as error:
        raise ValueError('Program must be a hexadecimal instruction word, such as 0x342') from error
    if not 0 <= word <= 0xffffffff or any((word >> (4 * k)) & 15 > 8 for k in range(8)):
        raise ValueError('Program must contain eight or fewer instruction nibbles, each 0 through 8')
    result['program'] = f'0x{word:08x}'
    for key in ('shift_u', 'shift_v'):
        if type(result[key]) not in (int, float) or not math.isfinite(result[key]) or abs(result[key]) > 2:
            raise ValueError(f'{key} must be a finite chart displacement between -2 and 2')
    return result


def unpack(data):
    count, operators = checkpoint_tools.validate_checkpoint(data)
    config = dict(zip(CONFIG_FIELDS, CONFIG.unpack_from(data, 16)))
    states = [STATE.unpack_from(data, 80 + i * 128) for i in range(count)]
    offset = 80 + count * 128
    ops = [OPERATOR.unpack_from(data, offset + i * 64) for i in range(operators)]
    return config, states, ops


def intervention(initial, variant, settings):
    data = bytearray(initial)
    count, operators = checkpoint_tools.validate_checkpoint(data)
    index = settings['operator_index']
    offset = 80 + count * 128 + index * 64
    if variant == 'frozen':
        struct.pack_into('<I', data, 16 + 9 * 4, 0)
        description = 'Set Config.feedback=0 in the initial checkpoint; the kernel freezes the entire operator field.'
    elif variant == 'edited':
        word = int(settings['program'], 0)
        old = struct.unpack_from('<I', data, offset + 48)[0]
        if old == word:
            raise ValueError('The edited program equals the initial program. Choose a different instruction word.')
        struct.pack_into('<I', data, offset + 48, word)
        description = f'Changed only operator {index} ({OP_NAMES[index]}) program from 0x{old:08x} to 0x{word:08x}.'
    elif variant == 'shifted':
        op = list(OPERATOR.unpack_from(data, offset))
        u, v = op[0] + settings['shift_u'], op[1] + settings['shift_v']
        turns = math.floor(u)
        u -= turns
        if turns % 2:
            v = -v
            op[15] ^= 1
        v -= math.floor(v)
        # Prevent a value just below one from rounding to an invalid FP32 one.
        op[0], op[1] = min(u, 0.9999999403953552), min(v, 0.9999999403953552)
        OPERATOR.pack_into(data, offset, *op)
        description = f'Shifted only operator {index} anchor by ({settings["shift_u"]}, {settings["shift_v"]}), applying the Klein seam/orientation rule.'
    elif variant == 'phase':
        for i in range(count):
            position = 80 + i * 128
            # Exact sign-bit flips give a pi phase shift without trigonometric rounding.
            for word in (4, 5):
                value = struct.unpack_from('<I', data, position + word * 4)[0]
                struct.pack_into('<I', data, position + word * 4, value ^ 0x80000000)
        description = 'Applied an exact pi phase shift to channel a in every initial state by flipping ar/ai sign bits. Stored energy and all non-amplitude words are unchanged.'
    else:
        description = 'Unchanged initial state and live mutable operator field.'
    checkpoint_tools.validate_checkpoint(data)
    return bytes(data), description


def frame(data, initial_ops, sample_limit=512):
    config, states, ops = unpack(data)
    sample_count = min(len(states), sample_limit)
    indices = [i * len(states) // sample_count for i in range(sample_count)]
    samples = []
    for i in indices:
        s = dict(zip(STATE_FIELDS, states[i]))
        s['index'] = i
        samples.append(s)
    records = []
    for i, op in enumerate(ops):
        record = dict(zip(OP_FIELDS, op))
        record.update(index=i, name=OP_NAMES[i] if i < len(OP_NAMES) else f'operator_{i}')
        record['program'] = f'0x{op[12]:08x}'
        records.append(record)
    return {'epoch': config['epoch'], 'states': samples, 'operators': records,
            'metrics': {'mean_energy': sum(s[15] for s in states) / len(states),
                        'max_energy_error': max(abs(s[15] - 5) for s in states),
                        'mean_history': sum(s[8] for s in states) / len(states),
                        'changed_operator_bodies': sum(a[12] != b[12] for a, b in zip(ops, initial_ops)),
                        'changed_operator_records': sum(OPERATOR.pack(*a) != OPERATOR.pack(*b) for a, b in zip(ops, initial_ops))}}


def compare(left, right):
    lc, ls, lo = unpack(left)
    rc, rs, ro = unpack(right)
    if (lc['count'], lc['operators'], lc['epoch']) != (rc['count'], rc['operators'], rc['epoch']):
        raise ValueError('Comparison requires equal population, operator count and epoch')
    changed_states = changed_words = changed_amplitudes = changed_non_amplitude = 0
    maximum = 0.0
    for i, (a, b) in enumerate(zip(ls, rs)):
        start = 80 + i * 128
        au = struct.unpack_from('<32I', left, start)
        bu = struct.unpack_from('<32I', right, start)
        differences = [x != y for x, y in zip(au, bu)]
        changed_states += any(differences)
        changed_words += sum(differences)
        changed_amplitudes += sum(differences[4:8])
        # Energy belongs to the amplitude subsystem. All other numerical and
        # control words are counted independently, including the returned history.
        changed_non_amplitude += sum(v for k, v in enumerate(differences) if k not in (4, 5, 6, 7, 15))
        maximum = max(maximum, max(abs(a[k] - b[k]) for k in list(range(24)) + list(range(28, 32))))
    op_offset = 80 + lc['count'] * 128
    op_words = sum(a != b for a, b in zip(struct.unpack_from('<' + 'I' * (lc['operators'] * 16), left, op_offset),
                                         struct.unpack_from('<' + 'I' * (lc['operators'] * 16), right, op_offset)))
    return {'changed_state_records': changed_states, 'changed_state_words': changed_words,
            'changed_amplitude_words': changed_amplitudes, 'changed_non_amplitude_state_words': changed_non_amplitude,
            'changed_operator_records': sum(OPERATOR.pack(*a) != OPERATOR.pack(*b) for a, b in zip(lo, ro)), 'changed_operator_words': op_words,
            'max_absolute_state_float_difference': maximum}


class Cancelled(Exception):
    pass


class Job:
    def __init__(self, settings, folder=None):
        self.id = datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8]
        self.settings = request_settings(settings)
        self.folder = folder or RUNS / self.id
        self.folder.mkdir(parents=True, exist_ok=False)
        self.stop = threading.Event()
        self.status, self.progress, self.message = 'running', 0.0, 'Preparing a common initial checkpoint'
        self.created_at = utc()
        self.binary_hash = digest(BINARY.read_bytes())
        self.result_url = None
        self.command_count = 0
        self.save_status()

    def summary(self):
        return dict(id=self.id, status=self.status, progress=self.progress, message=self.message,
                    created_at=self.created_at, result_url=self.result_url, label=f'{self.settings["mode"]} / {self.settings["count"]:,} states')

    def save_status(self):
        save_json(self.folder / 'job.json', {**self.summary(), 'request': self.settings})

    def command(self, name, arguments):
        if self.stop.is_set():
            raise Cancelled('Stopped before starting the next kernel command')
        target = self.folder / 'commands'
        target.mkdir(exist_ok=True)
        argv = [str(BINARY), *map(str, arguments)]
        env = os.environ.copy()
        # Run the shipped profile's defaults. Remove ambient tuning overrides so
        # they cannot silently change this experiment; record every override removed.
        removed = {}
        for key in list(env):
            if key.startswith('DAWNWOOD_') or key in ('VK_LAYER_VALIDATE_SYNC', 'VK_INSTANCE_LAYERS'):
                removed[key] = env.pop(key)
        record = dict(command=argv, cwd=str(ROOT), utc=utc(), executable_sha256=self.binary_hash,
                      removed_ambient_overrides=removed)
        save_json(target / (name + '.command.json'), record)
        start = time.perf_counter()
        error = None
        with (target / (name + '.stdout')).open('wb') as stdout, (target / (name + '.stderr')).open('wb') as stderr:
            process = subprocess.Popen(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            while process.poll() is None:
                if self.stop.wait(0.1):
                    error = Cancelled('Stopped the active kernel command; partial evidence was retained')
                    process.terminate()
                    break
                if time.perf_counter() - start > 180:
                    error = RuntimeError('Kernel command exceeded the 180-second bound; partial evidence was retained')
                    process.terminate()
                    break
            try:
                code = process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                code = process.wait()
        record.update(exit_code=code, process_wall_seconds=time.perf_counter() - start)
        save_json(target / (name + '.command.json'), record)
        self.command_count += 1
        if error:
            raise error
        if code:
            detail = (target / (name + '.stderr')).read_text(encoding='utf-8', errors='replace')[-1200:]
            raise RuntimeError(f'{name} exited {code}: {detail}')
        report = json.loads((target / (name + '.stdout')).read_text(encoding='utf-8'))
        if report.get('passed') is False or report.get('health', {}).get('passed') is False:
            raise RuntimeError(f'{name} returned a failing numerical report; raw evidence retained')
        return report, record['process_wall_seconds']

    def run(self):
        try:
            self.perform()
            self.status, self.progress, self.message = 'completed', 1.0, 'Complete returned states compared; reports and checkpoints are ready'
            self.result_url = str(self.folder / 'result.json')
        except Cancelled as error:
            self.status, self.message = 'cancelled', str(error)
        except Exception as error:
            self.status, self.message = 'failed', f'{type(error).__name__}: {error}'
        finally:
            self.save_status()

    def perform(self):
        s = self.settings
        variants = ['live'] if s['mode'] == 'single' else (['live', 'frozen', 'edited'] if s['mode'] == 'compare' else ['live', 'shifted', 'phase'])
        labels = {'live': 'Live operator field', 'frozen': 'Frozen operator field', 'edited': 'Edited operator body',
                  'shifted': 'Shifted operator anchor', 'phase': 'Changed amplitude phase'}
        initial_path = self.folder / 'common-initial.dwk'
        self.command('initialize', ['run', '--backend', 'cpu', '--count', s['count'], '--steps', 0,
                                    '--checkpoint', initial_path])
        initial = initial_path.read_bytes()
        _, _, initial_ops = unpack(initial)
        outputs, checkpoints = [], {}
        total = len(variants) * (math.ceil(s['epochs'] / s['stride']) + 1)
        completed = 0
        device_name = ''
        for variant in variants:
            directory = self.folder / variant
            directory.mkdir()
            changed, description = intervention(initial, variant, s)
            previous = directory / 'epoch-0000.dwk'
            previous.write_bytes(changed)
            save_json(directory / 'intervention.json', dict(description=description, source_sha256=digest(initial),
                      result_sha256=digest(changed), initial_comparison=compare(initial, changed)))
            self.message = f'{labels[variant]}: CPU/GPU comparison from the actual intervention'
            self.save_status()
            verification, _ = self.command(variant + '-verify', ['verify', '--device', DEVICE, '--resume', previous,
                                                                 '--steps', min(4, s['epochs'])])
            completed += 1
            frames = [frame(changed, initial_ops)]
            saved = {0: changed}
            gpu_seconds = process_seconds = 0.0
            reports = []
            for epoch in range(s['stride'], s['epochs'] + s['stride'], s['stride']):
                end = min(epoch, s['epochs'])
                steps = end - frames[-1]['epoch']
                destination = directory / f'epoch-{end:04}.dwk'
                self.message = f'{labels[variant]}: computing epoch {end}/{s["epochs"]}'
                self.progress = completed / total
                self.save_status()
                report, wall = self.command(f'{variant}-{end:04}', ['run', '--device', DEVICE, '--resume', previous,
                    '--steps', steps, '--batch', 8, '--checkpoint', destination])
                data = destination.read_bytes()
                frames.append(frame(data, initial_ops))
                saved[end] = data
                gpu_seconds += report['seconds']
                process_seconds += wall
                device_name = report['device']['name']
                reports.append(report)
                previous = destination
                completed += 1
            final = saved[s['epochs']]
            config = dict(zip(CONFIG_FIELDS, CONFIG.unpack_from(final, 16)))
            count = config['count']
            base_url = str(self.folder / variant) + '/'
            output = dict(id=variant, label=labels[variant], intervention=description, config=config, frames=frames,
                verification={'passed': verification['passed'], 'bitwise_equal': verification['aggregate']['bitwise_equal'],
                              'epochs_checked': verification['epochs_checked'],
                              'validation_layer_enabled': verification['device']['validation_layer_enabled']},
                metrics=dict(gpu_seconds=gpu_seconds, process_wall_seconds=process_seconds,
                    state_digest=digest(final[80:80 + count * 128]), operator_digest=digest(final[80 + count * 128:]),
                    checkpoint_sha256=digest(final), health_passed=all(r['health']['passed'] for r in reports),
                    completed_epochs=config['epoch']),
                exports=dict(csv=base_url + 'operator-changes.csv', checkpoint=base_url + previous.name,
                             report=str(self.folder / 'report.md')))
            with (directory / 'operator-changes.csv').open('w', newline='', encoding='utf-8') as handle:
                writer = csv.writer(handle)
                writer.writerow(['epoch', 'operator', 'name', 'field', 'previous', 'current'])
                for before, after in zip(frames, frames[1:]):
                    for a, b in zip(before['operators'], after['operators']):
                        for field_name in OP_FIELDS:
                            if a[field_name] != b[field_name]:
                                writer.writerow([after['epoch'], b['index'], b['name'], field_name, a[field_name], b[field_name]])
            outputs.append(output)
            checkpoints[variant] = saved
        comparisons = []
        for variant in variants[1:]:
            trace = [{'epoch': epoch, **compare(data, checkpoints[variant][epoch])}
                     for epoch, data in checkpoints['live'].items()]
            item = dict(left='live', right=variant, **trace[-1], trace=trace,
                        first_observed_operator_difference_epoch=next((r['epoch'] for r in trace if r['changed_operator_words']), None),
                        first_observed_non_amplitude_difference_epoch=next((r['epoch'] for r in trace if r['changed_non_amplitude_state_words']), None))
            comparisons.append(item)
        notes = [
            'These runs execute the unchanged DWI-N1-0.5 / 0.5.1-rtx1 numerical kernel. They do not replace it with a separate simulation.',
            'Every variant starts from one common checkpoint, with only the recorded intervention. Complete states are compared; JSON inspection samples are bounded to 512 records.',
            'Recorded frames are checkpoint boundaries. Kernel setup/readback occurs at each boundary, so this authoring tool is not a throughput benchmark.',
            'First observed differences refer to recorded checkpoint boundaries, not necessarily the first divergent native epoch when stride exceeds one.',
            'Program and anchor changes are interventions in the acting definition. An observed effect establishes influence, not useful learning or complete architectural closure.',
            'Core/synchronization validation is not enabled by this tool. Per-variant CPU/GPU comparison executes the actual intervention; the separate RTX campaign records validation-layer evidence.',
            'No application performance claim follows from a changed trajectory. Proposed constraint, memory and planning applications have separate contracts in the roadmap.'
        ]
        if s['mode'] == 'fidelity':
            c = next(r for r in comparisons if r['right'] == 'phase')
            notes.append(f'The exact amplitude-phase intervention changed {c["changed_amplitude_words"]} final amplitude words, '
                         f'{c["changed_non_amplitude_state_words"]} other non-energy state words, and {c["changed_operator_words"]} operator words. '
                         'This is a finite-run witness for the amplitude-to-operator feedback question, not an all-input proof.')
        result = dict(schema_version=1, id=self.id, created_at=self.created_at, profile='DWI-N1-0.5',
                      runtime_version='0.5.1-rtx1', device_name=device_name, binary_sha256=self.binary_hash,
                      request=s, states_sampled=min(512, s['count']), population=s['count'], variants=outputs,
                      comparisons=comparisons, notes=notes, command_count=self.command_count)
        save_json(self.folder / 'result.json', result)
        lines = ['# Dawnwood situated-operator experiment', '', f'Run `{self.id}`; {self.created_at}.', '',
                 f'Kernel **0.5.1-rtx1**, profile **DWI-N1-0.5**, device **{device_name}**.', '',
                 f'Executable SHA-256: `{self.binary_hash}`.', '',
                 f'{s["count"]:,} states; {s["epochs"]} epochs; recorded stride {s["stride"]}.', '']
        for output in outputs:
            lines.extend([f'## {output["label"]}', '', output['intervention'], '',
                          f'CPU/GPU verification: {output["verification"]}.', '',
                          f'Final state SHA-256: `{output["metrics"]["state_digest"]}`.', '',
                          f'Final operator SHA-256: `{output["metrics"]["operator_digest"]}`.', ''])
        lines.extend(['## Complete-record comparisons', '', '| Variant against live | Changed states | Changed state words | Changed operators | Changed operator words |',
                      '|---|---:|---:|---:|---:|'])
        for c in comparisons:
            lines.append(f'| {c["right"]} | {c["changed_state_records"]} | {c["changed_state_words"]} | {c["changed_operator_records"]} | {c["changed_operator_words"]} |')
        lines.extend(['', '## Interpretation', ''] + ['- ' + note for note in notes])
        (self.folder / 'report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experiment', choices=['single', 'compare', 'fidelity'], required=True)
    parser.add_argument('--count', type=int, default=4096)
    parser.add_argument('--epochs', type=int, default=32)
    parser.add_argument('--stride', type=int, default=4)
    parser.add_argument('--operator-index', type=int, default=30)
    parser.add_argument('--program', default='0x342')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not BINARY.is_file():
        raise SystemExit(f'RTX runtime not found: {BINARY}')
    job = Job(dict(mode=args.experiment, count=args.count, epochs=args.epochs, stride=args.stride,
                   operator_index=args.operator_index, program=args.program), args.output)
    job.run()
    print(json.dumps(job.summary(), indent=2))
    raise SystemExit(0 if job.status == 'completed' else 1)

if __name__ == '__main__':
    main()
