"""Exercise partial windows, page hops and mutation under Compute Sanitizer."""
from pathlib import Path
import json
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/integer/sanitizer'
OUT.mkdir(parents=True,exist_ok=True)
SAN='C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.8/bin/compute-sanitizer.bat'
records=[]
for codec in ('bc5','rg8'):
    for tool in ('memcheck','racecheck','synccheck','initcheck'):
        label=codec+'_'+tool
        command=[SAN,'--tool',tool,'--error-exitcode','9',str(ROOT/'build/dawnwood_integer_cached.exe'),
                 '--pages','3','--page-side','16','--blocks-per-step','37','--steps','17','--hops','5',
                 '--codec',codec,'--report',str(OUT/(label+'.json'))]
        p=subprocess.run(command,capture_output=True,text=True)
        (OUT/(label+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8')
        records.append({'label':label,'command':command,'returncode':p.returncode})
        print(label,p.returncode,flush=True)
(OUT/'commands.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
sys.exit(int(any(r['returncode'] for r in records)))
