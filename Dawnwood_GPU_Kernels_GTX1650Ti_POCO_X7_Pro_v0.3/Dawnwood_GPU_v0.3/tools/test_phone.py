"""Execute the actual Vulkan kernel on an authorized ADB-connected Android phone."""
from pathlib import Path
import argparse, json, shutil, subprocess, time
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--serial');p.add_argument('--apk',type=Path);p.add_argument('--out',type=Path,default=ROOT/'results/phone');p.add_argument('--timeout',type=int,default=300);args=p.parse_args()
    adb=shutil.which('adb')
    if not adb:raise SystemExit('Install Android platform-tools; adb was not found.')
    base=[adb]+(['-s',args.serial] if args.serial else [])
    def run(*cmd,check=True):return subprocess.run(base+list(cmd),capture_output=True,text=True,check=check)
    args.out.mkdir(parents=True,exist_ok=True)
    run('get-state')
    if args.apk:run('install','-r',str(args.apk))
    metadata={'model':run('shell','getprop','ro.product.model').stdout.strip(),'manufacturer':run('shell','getprop','ro.product.manufacturer').stdout.strip(),'brand':run('shell','getprop','ro.product.brand').stdout.strip(),'market_name':run('shell','getprop','ro.product.marketname').stdout.strip(),'device':run('shell','getprop','ro.product.device').stdout.strip(),'adb_serial':run('get-serialno').stdout.strip()}
    metadata['POCO_X7_Pro_identified']=metadata['brand'].lower()=='poco' and metadata['market_name'].lower()=='poco x7 pro'
    (args.out/'device.json').write_text(json.dumps(metadata,indent=2)+'\n')
    success=True;completed=0
    for command,count,steps in [('probe',1,0),('selftest',64,0),('verify',128,16),('run',4096,64)]:
        identifier=f'{command}_{time.time_ns()}'
        run('shell','am','force-stop','nl.dawnwood.kernel')
        launch=run('shell','am','start','-n','nl.dawnwood.kernel/.MainActivity','--ez','autorun','true','--es','command',command,'--es','run_id',identifier,'--ei','count',str(count),'--ei','steps',str(steps))
        (args.out/f'{command}_launch.txt').write_text(launch.stdout+launch.stderr)
        started=time.monotonic();stop=started+args.timeout;observed_pids=set();process_failed=False
        while time.monotonic()<stop:
            live=run('shell','pidof','nl.dawnwood.kernel',check=False)
            current_pids={pid for pid in live.stdout.split() if pid.isdigit()}
            observed_pids.update(current_pids)
            result=run('shell','run-as','nl.dawnwood.kernel','cat',f'files/reports/{identifier}.json',check=False)
            if result.returncode==0:
                try:data=json.loads(result.stdout)
                except json.JSONDecodeError:time.sleep(1);continue
                (args.out/f'{command}.json').write_text(json.dumps(data,indent=2)+'\n')
                runtime=data.get('runtime',{});success &= bool(data.get('finished')) and bool(runtime) and 'error' not in runtime and runtime.get('passed',True) and runtime.get('health',{}).get('passed',True)
                completed+=1
                device=runtime.get('device',{})
                if device.get('software_device'):success=False
                break
            if not current_pids and time.monotonic()-started>=10:
                (args.out/f'{command}_process_exit.txt').write_text('The app process disappeared without a completed report; this is not a passed test.\n'+live.stderr)
                exits=run('shell','dumpsys','activity','exit-info','nl.dawnwood.kernel',check=False)
                (args.out/f'{command}_exit_info.txt').write_text(exits.stdout+exits.stderr)
                success=False;process_failed=True;break
            time.sleep(1)
        else:
            (args.out/f'{command}_timeout.txt').write_text('No completed report before timeout. Inspect logcat; this is not a passed test.\n');success=False
        for pid in sorted(observed_pids):
            logs=run('logcat','-d',f'--pid={pid}',check=False)
            (args.out/f'{command}_pid_{pid}_logcat.txt').write_text(logs.stdout+logs.stderr)
        if process_failed:break
    print(json.dumps({'real_phone_test_completed':completed==4,'completed_commands':completed,'successful':bool(success and completed==4),'POCO_X7_Pro_identified':metadata['POCO_X7_Pro_identified'],'report_directory':str(args.out)},indent=2))
    raise SystemExit(0 if success else 2)
if __name__=='__main__':main()
