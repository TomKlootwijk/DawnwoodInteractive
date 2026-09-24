"""Audit the completed RTX campaign and package its exact runtime and evidence."""
from pathlib import Path
import csv
import datetime as dt
import hashlib
import json
import re
import shutil
import statistics
import struct
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / 'Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3'
EVIDENCE = ROOT / 'output/rtx5070ti_laptop_2026-09-24'
PACKAGE = ROOT / 'output/Dawnwood_RTX5070Ti_v0.5.1'
BINARY = KERNEL / 'bin/windows-rtx5070ti/dawnwood.exe'


def read(name):
    return json.loads((EVIDENCE / name).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if PACKAGE.exists():
        raise SystemExit('Package already exists; inspect it before rebuilding')
    binary_hash = sha(BINARY)
    claims = read('final_claims_r2/summary.json')
    assert claims['python_tests']['passed'] and claims['python_tests']['tests_run'] == 17
    for key in ['cpu_tests_passed', 'checkpoint_replay_passed', 'body_coverage_passed', 'vulkan_comparison_passed']:
        assert claims[key], key
    assert read('final_claims_r2/cpu_selftest.stdout')['tests_run'] == 30
    checks = []
    for name in ['final_verify_257_4096', 'final_verify_4096_256', 'final_verify_1048577_2',
                 'final_verify_paged_lut', 'final_verify_paged_split']:
        report, command = read(name + '.stdout'), read(name + '.command.json')
        assert command['exit_code'] == 0 and command['executable_sha256'] == binary_hash
        assert report['passed'] and report['aggregate']['bitwise_equal']
        assert report['epochs_checked'] == report['epochs_requested']
        assert len(report['trace']) == report['epochs_requested']
        assert all(x['comparison']['bitwise_equal'] for x in report['trace'])
        device = report['device']
        assert device['validation_layer_enabled'] and device['synchronization_validation_enabled']
        assert device['validation_errors'] == device['validation_warnings'] == 0
        checks.append({'name': name, 'count': report['config']['count'], 'operators': report['config']['operators'],
                       'epochs': report['epochs_checked'], 'bitwise_equal': True})
    capacity = read('capacity/summary.json')
    assert capacity['binary_sha256'] == binary_hash
    point = capacity['points'][-1]
    assert point['count'] == capacity['highest_completed_count']
    for item in capacity['points']:
        command = read('capacity/' + item['command_record'])
        assert command['exit_code'] == 0 and command['report']['health']['passed']
        assert command['report']['health']['checked_state_records'] == item['count']
        assert command['report']['device']['completed_epochs'] == 4
    alternate = read('large_page_layout_identity.json')
    assert alternate['identical_full_population_digest'] and alternate['alternate_sync_validation']
    assert alternate['errors'] == alternate['warnings'] == 0
    assert read('final_large_alternate_page.command.json')['executable_sha256'] == binary_hash
    launcher = read('final_launcher_r2.stdout')
    assert read('final_launcher_r2.command.json')['exit_code'] == 0
    assert launcher['runtime_version'] == '0.5.1-rtx1' and launcher['health']['passed']
    final_checkpoint = sha(EVIDENCE / 'final_launcher.dwk')
    assert set(read('paged_checkpoint_identity.json').values()) == {final_checkpoint}
    sustained, run = read('final_sustained.stdout'), read('final_sustained.command.json')
    assert run['exit_code'] == 0 and not run.get('stopped') and run['executable_sha256'] == binary_hash
    assert sustained['health']['passed'] and sustained['health']['checked_state_records'] == point['count']
    assert sustained['config']['count'] == point['count'] and sustained['new_epochs'] == 177
    assert sustained['device']['completed_epochs'] == 177 and sustained['seconds'] >= 600
    rows = []
    with (EVIDENCE / 'final_sustained.telemetry.csv').open(newline='') as handle:
        for row in csv.DictReader(handle, skipinitialspace=True):
            rows.append(row)
    busy = [r for r in rows if float(r['utilization.gpu [%]']) >= 95]
    assert len(busy) >= 600 and max(float(r['utilization.gpu [%]']) for r in rows) == 100
    assert max(float(r['temperature.gpu']) for r in rows) < 88
    paired = read('final_paired_bench.json')
    assert len(paired) == 6 and len({r['digest'] for r in paired}) == 1
    for item in paired:
        command = read(item['name'] + '.command.json')
        assert command['exit_code'] == 0
        if item['variant'] == 'rtx':
            assert command['executable_sha256'] == binary_hash
    medians = {variant: statistics.median(r['seconds'] for r in paired if r['variant'] == variant)
               for variant in ['baseline', 'rtx']}
    assert medians['rtx'] < medians['baseline'], 'Final measured optimization must improve throughput'
    sources = ['include/numeric_types.inc','include/numeric_math.inc','include/numeric_evolve.inc',
               'shaders/mutate.comp','shaders/evolve.comp','shaders/operator_texture.inc','shaders/state_buffers.inc',
               'shaders/evolution_pass.inc','shaders/prepare.comp','shaders/slope.comp','shaders/combine.comp',
               'shaders/geometry.comp','shaders/finish.comp']
    fingerprint = hashlib.sha256(''.join(sha(KERNEL / p) for p in sources).encode()).hexdigest()
    assert fingerprint == (KERNEL / 'shaders/source.sha256').read_text().strip()
    embedded = (KERNEL / 'src/spirv.hpp').read_text()
    shader_hashes = {}
    for name in ['mutate','evolve','prepare','slope','combine','geometry','finish']:
        body = re.search(r'\b' + name + r'_spv\[\] = \{(.*?)\};', embedded, re.S).group(1)
        words = [int(v, 16) for v in re.findall(r'0x([0-9a-fA-F]+)u', body)]
        payload = struct.pack('<' + 'I' * len(words), *words)
        assert payload == (KERNEL / 'shaders' / (name + '.spv')).read_bytes()
        shader_hashes[name] = hashlib.sha256(payload).hexdigest()
    subprocess.run([sys.executable, '-B', str(KERNEL / 'tools/verify_manifest.py')], check=True)
    summary = {'edition': '0.5.1-rtx1', 'profile': 'DWI-N1-0.5', 'binary_sha256': binary_hash,
        'shader_source_fingerprint': fingerprint, 'embedded_shader_hashes': shader_hashes,
        'final_launcher_checkpoint_sha256': final_checkpoint,
        'validation': checks, 'capacity_count': point['count'], 'capacity_state_payload_bytes': point['state_payload_bytes'],
        'capacity_ping_pong_bytes': point['state_ping_pong_bytes'], 'capacity_policy': capacity['stop_reason'],
        'sustained_epochs': sustained['new_epochs'], 'sustained_state_updates': point['count'] * sustained['new_epochs'],
        'sustained_gpu_seconds': sustained['seconds'], 'sustained_process_seconds': run['process_wall_seconds'],
        'sustained_updates_per_second': sustained['state_epochs_per_second'], 'telemetry': run['telemetry'],
        'busy_samples_95_percent_or_more': len(busy), 'busy_sample_mean_utilization': statistics.mean(float(r['utilization.gpu [%]']) for r in busy),
        'process_memory': run.get('process_memory'), 'benchmark_medians_seconds': medians,
        'throughput_improvement_percent': (medians['baseline'] / medians['rtx'] - 1) * 100,
        'previous_candidate_improvement_percent': 10.54001721401208,
        'all_release_gates_passed': True}
    (EVIDENCE / 'completion_audit.json').write_text(json.dumps(summary, indent=2) + '\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    times = [dt.datetime.strptime(r['timestamp'], '%Y/%m/%d %H:%M:%S.%f') for r in rows]
    minutes = [(t - times[0]).total_seconds() / 60 for t in times]
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True, constrained_layout=True)
    fig.suptitle('Dawnwood · RTX 5070 Ti Laptop · sustained full-population run', fontsize=13)
    axes[0].plot(minutes, [float(r['utilization.gpu [%]']) for r in rows], color='#0f766e')
    axes[0].set(ylabel='GPU busy (%)', ylim=(0, 105))
    axes[1].plot(minutes, [float(r['temperature.gpu']) for r in rows], color='#c2410c')
    axes[1].axhline(88, color='#991b1b', linestyle='--', linewidth=1, label='Stop threshold')
    axes[1].set(ylabel='GPU temperature (°C)'); axes[1].legend(loc='lower right')
    axes[2].plot(minutes, [float(r['power.draw [W]']) for r in rows], color='#1d4ed8')
    axes[2].set(ylabel='Reported power (W)', xlabel='Minutes since first telemetry sample')
    for axis in axes:axis.grid(alpha=.2)
    fig.savefig(EVIDENCE / 'sustained_load.png', dpi=160)
    plt.close(fig)
    peak_temp = summary['telemetry']['temperature.gpu']['max']
    peak_power = summary['telemetry']['power.draw']['max']
    thermal_samples = summary['telemetry']['clocks_event_reasons.sw_thermal_slowdown']['active_samples']
    resident_mib = summary['process_memory']['peak_working_set_bytes'] / (1 << 20)
    private_commit_gib = summary['process_memory']['max_sampled_private_commit_bytes'] / (1 << 30)
    validation_rows = '\n'.join(f"| {x['count']:,} | {x['operators']:,} | {x['epochs']:,} | Zero bit differences; zero layer errors/warnings |" for x in checks)
    report = f'''# Dawnwood RTX 5070 Ti Laptop — completed campaign

24 September 2026 · Runtime **0.5.1-rtx1** · Numerical profile **DWI-N1-0.5**.

The RTX edition is built, numerically checked, capacity-tested and sustained-load
tested on the physical MSI Vector 16 HX AI A2XWHG. NVIDIA reports an RTX 5070 Ti
Laptop GPU, 12,227 MiB framebuffer and driver 591.59. The host has
16,558,415,872 bytes of system RAM. No clock, power-limit or cooling setting was
changed. The firmware's observed power/thermal controls remained active.

## Measured results

| Measurement | Result |
|---|---:|
| Final binary versus baseline, median GPU time, 1,048,576 states × 64 epochs | {medians['rtx']:.6f} s versus {medians['baseline']:.6f} s |
| Throughput improvement in that paired comparison | **{summary['throughput_improvement_percent']:.2f}%** |
| Largest completed single connected population | **{point['count']:,} full 128-byte states** |
| State ping-pong payload | {point['state_ping_pong_bytes']/(1<<30):.3f} GiB |
| Sustained run | **{sustained['new_epochs']:,} epochs; {summary['sustained_state_updates']:,} state updates** |
| Sustained device time | **{sustained['seconds']/60:.2f} minutes** |
| Sustained whole-process time | {run['process_wall_seconds']/60:.2f} minutes |
| Sustained throughput | {sustained['state_epochs_per_second']/1e6:.3f} million state updates/s |
| Peak sampled GPU utilization | 100% |
| Samples at ≥95% GPU utilization | {len(busy):,}, sampled approximately once per second |
| Peak reported VRAM usage | {summary['telemetry']['memory.used']['max']:,.0f} MiB |
| Peak sampled temperature / power | {peak_temp:.0f}°C / {peak_power:.2f} W |
| Measured child-process peak host working set | {resident_mib:.2f} MiB |
| Maximum sampled child-process private commit | {private_commit_gib:.3f} GiB |

The final sustained run completed successfully and read back and health-checked
all {point['count']:,} records: no nonfinite state values or invalid records.
The maximum energy deviation from the source norm of five was
{sustained['health']['max_energy_error_from_source_seed_5']:.8g}. Health is distinct
from CPU/GPU numerical equivalence.

The host working set measures resident pages. Windows still reports substantial
private commit during the large Vulkan allocation; bounded application staging
does not mean the driver needs only the resident working-set amount of backing
store. Both measurements are retained above and in the raw receipt.

**Cooling limits sustained performance.** Software thermal slowdown was active
in {thermal_samples:,} samples. The firmware reduced clocks and power while the
GPU remained busy. The raw trace retains this behavior; the short paired
benchmark is not represented as an indefinitely sustainable rate. The earlier
selection campaign measured a 10.54% throughput improvement on its workload;
`final_paired_bench.json` records the exact shipped executable's subsequent
paired comparison under the post-stress laptop conditions.

![Sustained utilization, temperature and power](sustained_load.png)

## Correctness and storage evidence

The existing 17 Python checks, 30 CPU fixtures, 29 active-operator sensitivity
checks and checkpoint replay pass. The final executable compares every state
and operator word after every epoch in these workloads:

| States | Operators | Epochs | Result |
|---:|---:|---:|---|
{validation_rows}

All listed comparisons enable Khronos core and explicitly requested
synchronization validation. They retain the original `atol=1e-5`, `rtol=2e-5`
and exact integer checks; zero bit differences are separately measured.
Forced page boundaries cover mutation feedback and both monolithic/staged
evolution. The 1,048,577-state comparison crosses the new dispatch boundary.

Normal, streamed and preceding-build 8,190-state × 16-epoch checkpoints are
byte-identical (`paged_checkpoint_identity.json`), as is the final executable's
`final_launcher.dwk`. At the full capacity count,
default and alternate page layouts produce the same full-population digest,
with zero core/synchronization errors and warnings
(`large_page_layout_identity.json`). That digest comparison is not a full-size
CPU reference comparison.

## What changed

- Measured RTX defaults: 32 lanes per workgroup and 1,048,576 states per dispatch.
- Two physical pages represent one logical state buffer. All pages share one
  mutation and one changed LUT per epoch. This removes the previous ~8 GiB
  ping-pong storage limit; it does not create independent populations.
- Initialization and full readback use an 8 MiB host-state chunk instead of a
  full host-state snapshot. Vulkan staging remains bounded at 16 MiB; driver,
  compiler, executable and operator storage are additional.
- The numerical equations, source vector, operator bodies, topology, fourth-slot
  double Y-up, inverse/history semantics, tolerances and checkpoint ABI remain
  unchanged. The profile remains DWI-N1-0.5.

## Scope and limits

Capacity stopped at the **current Vulkan-budget policy**: 98% of reported free
budget minus a 32 MiB reserve. It is not an absolute hardware maximum. The
operating system and driver reserve part of physical VRAM. Every capacity
candidate performs four real epochs and complete readback; allocation alone is
not counted as success. The sustained run uses the same largest population.

GPU timestamps exclude initialization, upload, full readback and host gaps.
Whole-process time includes them. Streamed readback includes incremental hash
and health work; its reported analysis time is an overlapping subinterval.
NVML telemetry is device-wide at approximately one-second intervals. Busy
percentage does not establish instruction-unit occupancy, cache residence,
memory bandwidth saturation, or peak theoretical FLOPS. Ordinary desktop load,
dynamic clocks and cooling are uncontrolled and retained in the evidence.

The sustained run has layers disabled for timing; the identified correctness
and full-size alternate-layout runs have them enabled. No device reset, thermal
stop or kernel failure occurred in the completed sustained run. This finite
campaign is not indefinite endurance qualification or an all-input proof.
The new edition is tested on this RTX laptop; old GTX/phone artifacts remain
historical. Physical and universality claims are not extended by these results.

The first final-suite launch failed in its Python memory-accounting helper,
which still assumed a 65,536-state dispatch cap. The helper was updated to the
runtime's actual configurable bound; `final_claims_r2/` passes. The failed
attempt is retained under `final_claims/` and `final_claims.stderr`.

The first launcher check was rejected by Windows PowerShell's existing script
execution policy before starting the runtime. PowerShell 7 runs the launcher
successfully (`final_launcher_r2.*`). No execution policy was changed. Direct
execution of the supplied `.exe` is also supported.

## Identity and reproduction

Executable SHA-256: `{binary_hash}`.

Shader-source fingerprint: `{fingerprint}`.

`completion_audit.json` records the executable, every embedded shader, the exact
verification scope and measured metrics. Commands, environment, exit codes,
stdout/stderr, capacity policies, timings and telemetry are retained here.
The package root manifest covers source, binary, tools, documentation and these
records. Build inputs are documented in `WORKING.md` and the build receipts.

From the standalone package root:

```powershell
.\\kernel\\bin\\windows-rtx5070ti\\dawnwood.exe run --device 'RTX 5070 Ti' --stream --count 1048576 --steps 64 --batch 8 --budget-fraction .98
.\\kernel\\bin\\windows-rtx5070ti\\dawnwood.exe verify --device 'RTX 5070 Ti' --count 257 --steps 4096
python kernel\\tools\\measure_capacity.py --binary kernel\\bin\\windows-rtx5070ti\\dawnwood.exe --device 'RTX 5070 Ti' --stream --budget-fraction .98 --reserve-mib 32 --steps 4 --out my_capacity
python tools\\verify_manifest.py
```

Use a new capacity output directory. The runtime guide explains validation-layer
setup, checkpoint/resume, tuning overrides and the CMake/LLVM build commands.
'''
    (EVIDENCE / 'REPORT.md').write_text(report, encoding='utf-8')
    with (EVIDENCE / 'WORKING.md').open('a', encoding='utf-8') as handle:
        handle.write('\n## Completion\n\nThe sustained run completed. `REPORT.md` and `completion_audit.json` supersede the in-progress status above and identify the finished results.\n')
    PACKAGE.mkdir()
    # Include current native sources and their controlling references; omit
    # historical binaries/results, local dependencies and unrelated user files.
    for directory in ['include','src','shaders','profiles','docs','source','tests','tools','scripts']:
        shutil.copytree(KERNEL / directory, PACKAGE / 'kernel' / directory,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in ['CMakeLists.txt','README.md','AGENTS.md']:
        shutil.copy2(KERNEL / name, PACKAGE / 'kernel' / name)
    (PACKAGE / 'kernel/results').mkdir()
    shutil.copy2(KERNEL / 'results/shader_build.json', PACKAGE / 'kernel/results/shader_build.json')
    (PACKAGE / 'kernel/results/STATUS.md').write_text(
        '# RTX edition evidence\n\nThe current hardware campaign is in '
        '[evidence/REPORT.md](../../evidence/REPORT.md). Historical result files '
        'referenced by older kernel documentation remain in the original repository. '
        'This standalone package includes the current shader-build record here.\n', encoding='utf-8')
    (PACKAGE / 'kernel/bin/windows-rtx5070ti').mkdir(parents=True)
    shutil.copy2(BINARY, PACKAGE / 'kernel/bin/windows-rtx5070ti/dawnwood.exe')
    shutil.copytree(EVIDENCE, PACKAGE / 'evidence')
    (PACKAGE / 'tools').mkdir()
    for name in ['record_gpu_run.py','build_rtx.ps1']:
        shutil.copy2(ROOT / 'tools' / name, PACKAGE / 'tools' / name)
    shutil.copy2(KERNEL / 'tools/verify_manifest.py', PACKAGE / 'tools/verify_manifest.py')
    compiler = ROOT / 'tmp/rtx-toolchain/llvm-mingw-20260922-ucrt-x86_64'
    licenses = PACKAGE / 'third_party_licenses'
    licenses.mkdir()
    shutil.copy2(compiler / 'LICENSE.TXT', licenses / 'LLVM-LICENSE.TXT')
    for path in (compiler / 'x86_64-w64-mingw32/share/mingw32').glob('COPYING*'):
        shutil.copy2(path, licenses / path.name)
    (PACKAGE / 'README.md').write_text('''# Dawnwood RTX 5070 Ti Laptop edition

Runtime **0.5.1-rtx1** · Numerical profile **DWI-N1-0.5**.

Run this command from the package root for a streamed one-million-state workload:

```powershell
.\\kernel\\bin\\windows-rtx5070ti\\dawnwood.exe run --device 'RTX 5070 Ti' --stream --count 1048576 --steps 64 --batch 8 --budget-fraction .98
```

`kernel/scripts/run_rtx5070ti.ps1` also runs this workload in PowerShell 7.
Its `-Count`, `-Steps`, `-Output` and `-Checkpoint` parameters
select a different run. The executable is
`kernel/bin/windows-rtx5070ti/dawnwood.exe`.

If your shell disables scripts, use the direct executable command above.

- [Measured results and sustained-load trace](evidence/REPORT.md)
- [Runtime changes and build/run instructions](kernel/docs/RTX5070TI_v0.5.1.md)
- [Audited metrics and identities](evidence/completion_audit.json)

The installed NVIDIA Vulkan driver is used. Python is needed only for optional
measurement/manifest tools; it is not needed to run the executable. The source,
seven generated compute shaders, original source references and measurement
records are included. LLVM/MinGW runtime notices are in `third_party_licenses/`.

Verify the package with `python tools/verify_manifest.py`. To reproduce the
portable LLVM build, supply Python, Compiler, VulkanSDK, Binary, Evidence and
Name paths to `tools/build_rtx.ps1`. CMake is also supported from `kernel/`.
''', encoding='utf-8')
    files = sorted(p for p in PACKAGE.rglob('*') if p.is_file())
    (PACKAGE / 'MANIFEST.sha256').write_text(''.join(sha(p) + '  ' + p.relative_to(PACKAGE).as_posix() + '\n' for p in files))
    subprocess.run([sys.executable,'-B',str(PACKAGE / 'tools/verify_manifest.py')],check=True)
    archive = PACKAGE.parent / (PACKAGE.name + '.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as output:
        for path in sorted(PACKAGE.rglob('*')):
            if path.is_file():output.write(path, PACKAGE.name + '/' + path.relative_to(PACKAGE).as_posix())
    with zipfile.ZipFile(archive) as check:
        assert check.testzip() is None
        for line in (PACKAGE / 'MANIFEST.sha256').read_text().splitlines():
            expected,name=line.split('  ',1)
            assert hashlib.sha256(check.read(PACKAGE.name+'/'+name)).hexdigest()==expected
    receipt={'archive':str(archive),'archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,
             'manifest_files':len(files),'archive_entries_verified':True,'binary_sha256':binary_hash,
             'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
    (ROOT / 'output/Dawnwood_RTX5070Ti_v0.5.1_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__ == '__main__':
    main()
