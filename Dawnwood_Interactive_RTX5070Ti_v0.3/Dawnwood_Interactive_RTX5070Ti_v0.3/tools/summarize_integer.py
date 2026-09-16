"""Assemble current integer-edition evidence; no historical float measurements."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import io
import json
import statistics

ROOT=Path(__file__).resolve().parents[1];EV=ROOT/'results/integer'
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
bench=read(EV/'benchmark_large/benchmark.json')
validation=read(EV/'validation_fast_masks/validation.json')
assert bench['status']==validation['status']=='passed'
rows=[]
for codec,values in bench['performance'].items():
    timings=values['summary']['timings'];reference=timings['reference_balanced']['circulation_wall_ms']['median']
    for name in ('reference_balanced','shared_balanced','texture_balanced','cached_balanced','cached_l1'):
        data=timings[name];variant,policy=name.rsplit('_',1);seconds=data['circulation_wall_ms']['median']/1000
        rows.append({'variant':variant,'codec':codec,'cache_policy':policy,
                     'median_pair_updates_per_second':data['token_pair_updates_per_second']['median'],
                     'median_wall_seconds':seconds,'speedup_vs_reference':reference/(seconds*1000),
                     'median_process_seconds':data['process_wall_ms']['median']/1000,
                     'mean_interval_ms':seconds*1000/256,
                     'derived_sweep_ms':32*2048*2048/data['token_pair_updates_per_second']['median']*1000})
profiles={}
for path in (EV/'profiles').glob('*.csv'):
    text=path.read_text(encoding='utf-8-sig');data=csv.DictReader(io.StringIO(text[text.index('"ID"'):]))
    metrics={}
    for row in data:
        raw=row['Metric Value']
        # Nsight on this host exports Dutch decimal/grouping punctuation.
        value=float(raw.replace('.','').replace(',','.'))
        metrics.setdefault(row['Metric Name'],[]).append(value)
    profiles[path.stem]={k:statistics.median(v) for k,v in metrics.items()}
audits=read(EV/'instructions/build_audits.json')
counts={}
for record in audits:
    audit=read(ROOT/record['audit']);assert audit['status']=='passed'
    assert hashlib.sha256((ROOT/record['executable']).read_bytes()).hexdigest()==record['sha256']
    counts[Path(record['executable']).stem]={'ptx_instructions':audit['ptx']['instruction_count'],
        'sass_instructions':audit['sass']['instruction_count'],
        'hfma2_constant_materialization':len(audit['sass']['constant_materialization_instructions']),
        'forbidden_instructions':audit['sass']['forbidden_instruction_count']}
san=read(EV/'sanitizer/commands.json');assert all(r['returncode']==0 for r in san)
capacity=[{'variant':'cached / balanced','report':read(EV/'capacity'/f'{c}.json')} for c in ('bc5','rg8')]
for row in capacity:assert row['report']['complete_sweeps_this_run']>=1
summary={
 'edition':'integer-1','created_at_utc':datetime.now(timezone.utc).isoformat(),
 'source_sha256':hashlib.sha256((ROOT/'source/double-slit-theory.pdf').read_bytes()).hexdigest(),
 'recommended_executable':'build/dawnwood_integer_cached.exe',
 'performance':rows,
 'benchmark_scope':'RTX 5070 Ti Laptop, CUDA 12.8; 32 x 2048-square pages; W=65,536 blocks; 256 intervals; batch=32; seed=756; dt=1024 and gain=16384 Q16; hops=2; mutation/jitter on. Three rotated sequential trials after one excluded warmup per variant. Clocks not locked. Wall time excludes allocation, initialization, snapshots and report output.',
 'performance_evidence':'results/integer/benchmark_large/benchmark.json',
 'additional_benchmarks':['results/integer/benchmark_fast_masks/benchmark.json','results/integer/benchmark_compact/benchmark.json','results/integer/benchmark_final/benchmark.json'],
 'validation':{
     'Complete snapshots':f"{validation['comparison_count']} passing equality/rejection checks across four variants, two codecs, partial windows, graph/sequential and continuation; includes v3 rejection.",
     'CPU numerical suites':'Math 1,483,985 assertions; core 296,554; D4 cache 1,253,890; predicates 187,164 exact comparisons + 3,598 coverage assertions.',
     'GPU component checks':'All 65,536 D4 pairs exactly match direct GPU charts; all 3,840 live support bits match CPU signed SDF; complete 64-byte stages and all 31 mutated records match CPU in self-tests.',
     'Sanitizers':'8 passing runs: memcheck, racecheck, synccheck, initcheck for both codecs; 3 pages, W=37, 17 intervals, 5 hops.',
     'Decoder scope':'RG8 tokens exact; native BC5 differs from software palette by at most one token in tested reads. CPU stage oracle starts with actual native decoded bytes.',
     'Quantum component scope':'H and phase interference tested directly; LP8 quotient loss measured separately. No entangled-state model or full-recurrence quantum fidelity claim.',
     'Evidence location':'results/integer/validation_fast_masks/validation.json; independent tests and sanitizer logs retained.'},
 'instruction_audits':{
     'Actual executable audit':'All four shipped executables pass PTX and SASS checks; binary SHA-256 matched before summary.',
     'Permitted boundaries':'Native f32 sampler/bit transfers and strictly constant-only HFMA2 materialization are listed separately. No data-dependent floating arithmetic/conversion/SFU found.',
     'Audit record':'results/integer/instructions/build_audits.json; no zero-floating-opcode or driver-internals claim.'},
 'instruction_counts':counts,
 'profiles':{
     'Cached balanced':f"Median evolve {profiles['cached_balanced']['gpu__time_duration.sum']/1000:.2f} us; L1/TEX hit {profiles['cached_balanced']['l1tex__t_sector_hit_rate.pct']:.2f}%; active warps {profiles['cached_balanced']['sm__warps_active.avg.pct_of_peak_sustained_active']:.2f}%; DRAM/peak {profiles['cached_balanced']['dram__throughput.avg.pct_of_peak_sustained_elapsed']:.2f}%.",
     'Cached L1 preference':f"L1/TEX hit {profiles['cached_l1']['l1tex__t_sector_hit_rate.pct']:.2f}%; evolve {profiles['cached_l1']['gpu__time_duration.sum']/1000:.2f} us. Hits aggregate all evolve traffic, not just the LUT.",
     'Profiler scope':'BC5, same 32-page field and W; three evolve launches after eight skipped, no graph; replay counters, unlocked clocks and uncontrolled caches. Not the circulation benchmark.'},
 'profile_metrics':profiles,'capacity':capacity,
 'capacity_scope':'Fresh automatic allocation runs, fill=0.92 with at least 768 MiB reserved; page side4096, W=65,536, 8,192 intervals. Both initialized and swept. This is exercised large-field capacity with desktop headroom, not maximum allocation or DRAM bandwidth saturation.',
 'quantum_evidence':'results/integer/quantum_mechanism_checks.json',
 'source_requirements':'docs/INTEGER_REQUIREMENTS.md',
 'limits':['The supplied PDF is an architectural conversation, not a fully specified numerical quantum theory.','All pure-state fidelity and probability readouts are component diagnostics, not features of the nonlinear full-field recurrence.','Four kilobytes and 69,540 bytes describe hot data only, not machine code or total memory.','Signed local supports on a Klein quotient are defined explicitly; no global three-dimensional Klein signed distance is claimed.','The source literal 756 label is bound to a deterministic seed; no Fourier relation was supplied or inferred.']
}
(EV/'final_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print('Wrote',EV/'final_summary.json')
