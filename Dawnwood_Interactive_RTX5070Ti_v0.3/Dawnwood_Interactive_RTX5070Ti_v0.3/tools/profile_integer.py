"""Sequential Nsight Compute measurements; no timing claims from replay runs."""
from pathlib import Path
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/integer/profiles'
OUT.mkdir(parents=True,exist_ok=True)
NCU='C:/Program Files/NVIDIA Corporation/Nsight Compute 2025.1.0/ncu.bat'
metrics=['gpu__time_duration.sum','sm__warps_active.avg.pct_of_peak_sustained_active',
         'l1tex__t_sector_hit_rate.pct','lts__t_sector_hit_rate.pct',
         'l1tex__throughput.avg.pct_of_peak_sustained_elapsed',
         'dram__throughput.avg.pct_of_peak_sustained_elapsed','dram__bytes_read.sum','dram__bytes_write.sum']
records=[]
for variant in ('reference','texture','cached'):
    for policy in (('balanced','l1') if variant=='cached' else ('balanced',)):
        label=variant+'_'+policy
        command=[NCU,'--target-processes','all','--kernel-name-base','demangled','--kernel-name','regex:.*evolve_window.*',
                 '--launch-skip','8','--launch-count','3','--cache-control','none','--clock-control','none',
                 '--metrics',','.join(metrics),'--csv','--log-file',str(OUT/(label+'.csv')),
                 str(ROOT/'build'/('dawnwood_integer_'+variant+'.exe')),'--no-graph','--pages','32','--page-side','2048',
                 '--blocks-per-step','65536','--steps','12','--batch','12','--codec','bc5','--cache-policy',policy,
                 '--report',str(OUT/(label+'.json'))]
        p=subprocess.run(command,capture_output=True,text=True)
        (OUT/(label+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8')
        records.append({'label':label,'command':command,'returncode':p.returncode})
        print(label,p.returncode,flush=True)
(OUT/'commands.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
sys.exit(int(any(r['returncode'] for r in records)))
