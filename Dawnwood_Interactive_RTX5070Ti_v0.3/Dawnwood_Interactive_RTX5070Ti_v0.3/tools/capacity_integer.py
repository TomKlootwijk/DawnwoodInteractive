"""Initialize and traverse large integer fields with explicit desktop headroom."""
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/integer/capacity'
OUT.mkdir(parents=True,exist_ok=True)
records=[]
for codec in ('bc5','rg8'):
    command=[str(ROOT/'build/dawnwood_integer_cached.exe'),'--codec',codec,
             '--fill','0.92','--reserve-mib','768','--page-side','4096',
             '--blocks-per-step','65536','--steps','8192','--batch','32',
             '--report',str(OUT/(codec+'.json'))]
    p=subprocess.run(command,capture_output=True,text=True)
    (OUT/(codec+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8')
    record={'codec':codec,'command':command,'returncode':p.returncode}
    if not p.returncode:
        report=json.loads((OUT/(codec+'.json')).read_text())
        record['complete_sweeps']=report['complete_sweeps_this_run']
        record['full_sweep_passed']=record['complete_sweeps']>=1
    records.append(record)
    print(codec,record,flush=True)
(OUT/'commands.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
sys.exit(int(any(r['returncode'] or not r.get('full_sweep_passed') for r in records)))
