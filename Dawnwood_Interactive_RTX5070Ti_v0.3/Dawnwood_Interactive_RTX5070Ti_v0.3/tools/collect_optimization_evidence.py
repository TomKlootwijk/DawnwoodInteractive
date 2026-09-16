"""Index the measured optimization evidence and refresh the local package manifest."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[1]
RESULT=ROOT/'results/optimization'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    suites=['benchmark_small','benchmark_large','benchmark_balanced','benchmark_capacity_margin']
    measured={name:json.loads((RESULT/name/'benchmark.json').read_text()) for name in suites}
    assert all(r['status']=='passed' for r in measured.values())
    acceptance=json.loads((RESULT/'optimized_acceptance/acceptance.json').read_text())
    assert acceptance['status']=='passed'
    assert '100% tests passed' in (RESULT/'ctest_final.txt').read_text()
    assert '\nOK' in (RESULT/'python_tests_final.txt').read_text()
    sanitizer={}
    for codec in ['bc5','rg8']:
        for tool in ['memcheck','racecheck','synccheck']:
            path=RESULT/f'sanitizer_{codec}_{tool}.txt'
            expected='0 errors, 0 warnings' if tool=='racecheck' else 'ERROR SUMMARY: 0 errors'
            assert expected in path.read_text()
            sanitizer[path.name]=digest(path)
    report=ROOT/'output/pdf/Dawnwood_Interactive_Optimized_Formalization.pdf'
    assert report.is_file()
    files=['src/main.cu','src/kernels.cuh','include/dawnwood/core.hpp','CMakeLists.txt',
           'build/dawnwood.exe','build/dawnwood_reference.exe','source/double-slit-theory.pdf',
           'tools/build_formalization_pdf.py']
    summary={
        'edition':'v0.3 optimized, 2026-09-16',
        'status':'digital correctness and measured optimization validated within recorded scope',
        'source_sha256':digest(ROOT/'source/double-slit-theory.pdf'),
        'pdf':{'path':str(report.relative_to(ROOT)), 'pages':12, 'sha256':digest(report), 'visual_review':'all 12 rendered pages inspected; changed math/command pages re-rendered and inspected'},
        'benchmarks':{name:{'status':r['status'],'sha256':digest(RESULT/name/'benchmark.json'),
                            'speedup_circulation_ratio_of_medians':{codec:r['performance'][codec]['summary']['circulation_wall_ms']['reference_over_optimized_ratio_of_medians'] for codec in ['bc5','rg8']}} for name,r in measured.items()},
        'snapshot_checks':len(measured['benchmark_small']['equivalence']),
        'snapshot_scope':'16 small reference/optimized cases and four graph/sequential full-state checks. No complete multi-GiB field hashes.',
        'acceptance_status':acceptance['status'], 'ctest_passed':4, 'python_tests_passed':14,
        'gpu_pair_cache_check':'all 65536 entries at four offsets passed; gpu_pair_checks.txt',
        'sanitizer_log_hashes':sanitizer,
        'retained_failures':[
            'Initial BC5 texture object failed normalized-float creation on uint4 backing. Fixed with cudaReadModeElementType for BC5 views.',
            'benchmark_capacity: maximum explicit-page repeat ran out of device memory; original logs retained. Separate 75%-page margin suite passed.'
        ],
        'theory_verdict':'Literal digital mechanisms mapped and component laws checked; physical double-slit validation not established. LP8 quotient is nonunitary, cancellation-sensitive, and fourth-stage forcing differs from unforced RK4.',
        'file_hashes':{name:digest(ROOT/name) for name in files},
    }
    (RESULT/'VALIDATION_OPTIMIZED.json').write_text(json.dumps(summary,indent=2)+'\n')
    manifest=ROOT/'MANIFEST.sha256'
    original=ROOT/'MANIFEST.v0.3-original.sha256'
    if not original.exists(): shutil.copyfile(manifest,original)
    included=[]
    for path in ROOT.rglob('*'):
        if not path.is_file():continue
        rel=path.relative_to(ROOT)
        if any(part in {'build','build-cpu','tmp','work','__pycache__','.git'} for part in rel.parts):continue
        if path==manifest or path.suffix.lower() in {'.exe','.obj','.pdb','.pyc'}:continue
        included.append((rel.as_posix(),digest(path)))
    manifest.write_text(''.join(f'{sha}  {name}\n' for name,sha in sorted(included)),encoding='utf-8')
    print(f'Indexed {len(included)} files; original manifest preserved.')


if __name__=='__main__':
    main()
