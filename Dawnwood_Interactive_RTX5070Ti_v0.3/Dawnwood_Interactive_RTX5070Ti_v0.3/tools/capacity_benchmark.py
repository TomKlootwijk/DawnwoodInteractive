"""Repeat the measured capacity configuration without exporting gigabyte snapshots."""
import argparse
import json
import math
import time
from pathlib import Path
from benchmark_optimization import Session, compare_reports, summarize_pairs, sha256


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--repeats', type=int, default=3)
    p.add_argument('--page-fraction', type=float, default=0.75, help='Fraction of observed maximum pages; default leaves room for driver variation')
    a = p.parse_args()
    if a.repeats < 1:
        p.error('repeats must be positive')
    if not math.isfinite(a.page_fraction) or not 0 < a.page_fraction <= 1:
        p.error('page-fraction must be in (0,1]')
    root = Path(__file__).resolve().parents[1]
    folder = a.out.resolve()
    folder.mkdir(parents=True, exist_ok=False)
    bindir=root/'build'
    if not (bindir/'dawnwood.exe').exists():
        bindir=bindir/'Release'
    executables = {'reference': bindir/'dawnwood_reference.exe', 'optimized': bindir/'dawnwood.exe'}
    session = Session(folder, executables, 180)
    result = {'status': 'running', 'page_fraction': a.page_fraction, 'scope': 'Fixed fraction of page count from preceding automatic capacity run; circulation timing excludes allocation. No full snapshots at capacity.',
              'executables': {k: {'path': str(v), 'sha256': sha256(v)} for k, v in executables.items()}, 'performance': {}, 'runs': session.runs}
    try:
        for codec in ('bc5', 'rg8'):
            capacity = json.loads((root/f'results/optimization/capacity_{codec}.json').read_text())
            pages=max(1,int(capacity['pages']*a.page_fraction))
            args = ['--codec', codec, '--pages', str(pages), '--page-side', '4096',
                    '--fill', '0.98', '--reserve-mib', '256', '--blocks-per-step', '65536', '--steps', '8192', '--batch', '32']
            pairs = []
            for trial in range(a.repeats):
                pair = {'trial': trial}
                order = ('reference', 'optimized') if trial % 2 == 0 else ('optimized', 'reference')
                for variant in order:
                    time.sleep(1)  # Allow WDDM to finish releasing the preceding process.
                    pair[variant] = session.invoke(variant, f'{codec}_{trial}_{variant}', args)
                    if pair[variant]['report']['complete_sweeps_this_run'] < 1:
                        raise AssertionError('Capacity run did not cover a complete sweep')
                compare_reports(pair['reference']['report'], pair['optimized']['report'], f'capacity_{codec}_{trial}')
                pairs.append(pair)
            result['performance'][codec] = {'pairs': pairs, 'summary': summarize_pairs(pairs)}
        result['status'] = 'passed'
    except Exception as exc:
        result['status'] = 'failed'
        result['error'] = str(exc)
        raise
    finally:
        (folder/'benchmark.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
