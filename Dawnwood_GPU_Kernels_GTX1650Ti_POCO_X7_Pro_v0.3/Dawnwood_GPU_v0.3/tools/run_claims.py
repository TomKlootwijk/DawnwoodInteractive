"""Run source-linked numerical experiments; never relabel an unavailable device as tested."""
from pathlib import Path
import argparse, csv, hashlib, io, json, math, os, platform, shutil, subprocess, sys, time, unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from packing import encode_bc5,decode_bc5,memory_model,bc5_bytes

def main():
    p=argparse.ArgumentParser();p.add_argument('--binary',type=Path,default=ROOT/'build/dawnwood');p.add_argument('--device',default='');p.add_argument('--allow-software',action='store_true');p.add_argument('--out',type=Path,default=ROOT/'results/claims');p.add_argument('--bench',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    binary=a.binary.resolve();commands=[]
    def run(name,args,timeout=180):
        cmd=[str(binary)]+args;start=time.monotonic()
        try:
            r=subprocess.run(cmd,text=True,capture_output=True,timeout=timeout)
            (a.out/f'{name}.stdout').write_text(r.stdout);(a.out/f'{name}.stderr').write_text(r.stderr)
            record={'name':name,'command':cmd,'exit_code':r.returncode,'wall_seconds':time.monotonic()-start}
            try:data=json.loads(r.stdout)
            except json.JSONDecodeError:data={'error':'No JSON report','stderr':r.stderr[-2000:]}
            record['report']=data
        except Exception as e:record={'name':name,'command':cmd,'error':str(e),'report':{'error':str(e)}}
        commands.append(record);(a.out/f'{name}.json').write_text(json.dumps(record,indent=2)+'\n');return record
    stream=io.StringIO();suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    (a.out/'python_tests.txt').write_text(stream.getvalue())
    python_summary={'tests_run':tests.testsRun,'failures':len(tests.failures),'errors':len(tests.errors),'passed':tests.wasSuccessful()}
    (a.out/'python_tests.json').write_text(json.dumps(python_summary,indent=2)+'\n')
    cpu=run('cpu_selftest',['selftest'])
    extra=(['--device',a.device] if a.device else [])+(['--allow-software'] if a.allow_software else [])
    probe=run('device_probe',['probe','--count','1']+extra)
    gpu_available='error' not in probe['report']
    verify=None
    if gpu_available:verify=run('cpu_vulkan_every_epoch',['verify','--count','128','--steps','16']+extra)
    baseline=run('baseline',['run','--backend','cpu','--count','16','--steps','8'])
    coverage=[]
    for i in range(31):
        if i in (25,26):continue
        changed=run(f'body_{i:02d}',['run','--backend','cpu','--count','16','--steps','8','--program',f'{i}:0x2'])
        base_hash=baseline['report'].get('state_and_operator_fnv1a64')
        # The full digest includes operators, so a separate state-only result is preferred when provided.
        effect=changed['report'].get('state_only_fnv1a64')!=baseline['report'].get('state_only_fnv1a64') if baseline['report'].get('state_only_fnv1a64') else None
        coverage.append({'operator_index':i,'body_edit_record_changed':changed['report'].get('state_and_operator_fnv1a64')!=base_hash,'numerical_state_changed':effect})
    (a.out/'body_coverage.json').write_text(json.dumps(coverage,indent=2)+'\n')
    checkpoint=a.out/'checkpoint.dwk'
    first=run('checkpoint_first',['run','--backend','cpu','--count','16','--steps','4','--checkpoint',str(checkpoint)])
    second=run('checkpoint_continue',['run','--backend','cpu','--resume',str(checkpoint),'--steps','4'])
    same=baseline['report'].get('state_and_operator_fnv1a64')==second['report'].get('state_and_operator_fnv1a64') and 'error' not in baseline['report']
    red=[0,4,9,17,28,39,52,66,82,100,120,142,165,191,220,255];green=red[::-1]
    coded=encode_bc5(red,green);rr,gg=decode_bc5(coded)
    error=math.sqrt(sum((x-y)**2 for x,y in zip(red+green,rr+gg))/32)
    packing={'kind':'CPU BC5 format/approximation experiment','encoded_block_bytes':len(coded),'two_raw_UNORM8_channels_bytes':32,'rmse_UNORM8_units':error,'arbitrary_input_lossless':error==0,'bc5_4096_base_bytes':bc5_bytes(4096,4096),'working_set_4096':memory_model(4096),'raw_budget_examples':{str(b):{'rgba32f_elements':b//16,'rgba8_elements':b//4,'bc5_aligned_average_texels':b} for b in [4*10**9,4*2**30,12*2**30]}}
    (a.out/'packing.json').write_text(json.dumps(packing,indent=2)+'\n')
    benchmarks=[]
    if a.bench:
        for backend in (['cpu','vulkan'] if gpu_available else ['cpu']):
            for count in [256,1024,4096]:
                samples=[]
                for repeat in range(3):
                    rec=run(f'bench_{backend}_{count}_{repeat}',['run','--backend',backend,'--count',str(count),'--steps','16','--batch','8']+(extra if backend=='vulkan' else []))
                    if 'seconds' in rec['report']:samples.append(rec['report']['seconds'])
                if samples:benchmarks.append({'backend':backend,'count':count,'epochs':16,'seconds_samples':samples,'median_seconds':sorted(samples)[len(samples)//2]})
        (a.out/'benchmark_scaling.json').write_text(json.dumps(benchmarks,indent=2)+'\n')
    device=probe['report'].get('device',{})
    report={'profile':'DWI-N1-0.3','environment':{'python':sys.version,'platform':platform.platform()},'python_tests':python_summary,'cpu_tests_passed':cpu['report'].get('passed',False),'vulkan_device':device,'vulkan_comparison_executed':verify is not None,'vulkan_comparison_passed':verify['report'].get('passed',False) if verify else None,'checkpoint_replay_passed':same,'body_coverage_passed':all(x['numerical_state_changed'] is True for x in coverage),'body_coverage':coverage,'packing_rmse':error,'real_GTX_1650_Ti_test':bool(device.get('vendor_id')==0x10de and '1650 Ti' in device.get('name','') and verify),'real_POCO_test':False,'phone_note':'Only tools/test_phone.py can populate a connected-phone report; no phone result is inferred from shader compilation.'}
    (a.out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    passed=tests.wasSuccessful() and cpu['report'].get('passed',False) and same and all(x['numerical_state_changed'] is True for x in coverage)
    if verify:passed &= verify['report'].get('passed',False)
    raise SystemExit(0 if passed else 2)
if __name__=='__main__':main()
