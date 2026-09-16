"""Audit PTX and SASS extracted from the actual shipped integer executables."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/integer/instructions'
CUOBJDUMP=Path('C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.8/bin/cuobjdump.exe')
OUT.mkdir(parents=True,exist_ok=True)
records=[]
for variant in ('', '_texture', '_reference', '_cached'):
    name='dawnwood_integer'+variant
    exe=ROOT/'build'/(name+'.exe')
    record={'executable':str(exe.relative_to(ROOT)), 'sha256':hashlib.sha256(exe.read_bytes()).hexdigest()}
    for kind in ('ptx','sass'):
        command=[str(CUOBJDUMP),'--dump-'+kind,str(exe)]
        result=subprocess.run(command,capture_output=True,text=True,check=True)
        target=OUT/(name+'.'+kind)
        target.write_text(result.stdout,encoding='utf-8')
        record[kind+'_command']=command
    audit=OUT/(name+'.json')
    command=[sys.executable,str(ROOT/'tools/verify_integer_device_code.py'),str(OUT/(name+'.ptx')),
             '--sass',str(OUT/(name+'.sass')),'--allow-native-unorm-boundary','--allow-constant-materialization',
             '--require-entry','initialize_page','--require-entry','evolve_window','--require-entry','commit_window',
             '--require-entry','mutate_operators','--require-entry','rebuild_next_masks','--require-entry','advance_interval',
             '--out',str(audit)]
    result=subprocess.run(command,capture_output=True,text=True)
    print(result.stdout,end='')
    record['audit']=str(audit.relative_to(ROOT));record['audit_returncode']=result.returncode
    record['binary_unchanged']=record['sha256']==hashlib.sha256(exe.read_bytes()).hexdigest()
    records.append(record)
(OUT/'build_audits.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
sys.exit(int(any(r['audit_returncode'] or not r['binary_unchanged'] for r in records)))
