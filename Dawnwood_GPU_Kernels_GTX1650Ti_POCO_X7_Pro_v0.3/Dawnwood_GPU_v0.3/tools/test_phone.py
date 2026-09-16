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
    metadata={'model':run('shell','getprop','ro.product.model').stdout.strip(),'manufacturer':run('shell','getprop','ro.product.manufacturer').stdout.strip(),'adb_serial':run('get-serialno').stdout.strip()}
    (args.out/'device.json').write_text(json.dumps(metadata,indent=2)+'\n')
    success=True
    for command,count,steps in [('probe',1,0),('selftest',64,0),('verify',128,16),('run',4096,64)]:
        identifier=f'{command}_{time.time_ns()}'
        run('shell','am','force-stop','nl.dawnwood.kernel')
        launch=run('shell','am','start','-n','nl.dawnwood.kernel/.MainActivity','--ez','autorun','true','--es','command',command,'--es','run_id',identifier,'--ei','count',str(count),'--ei','steps',str(steps))
        (args.out/f'{command}_launch.txt').write_text(launch.stdout+launch.stderr)
        stop=time.monotonic()+args.timeout
        while time.monotonic()<stop:
            result=run('shell','run-as','nl.dawnwood.kernel','cat',f'files/reports/{identifier}.json',check=False)
            if result.returncode==0:
                try:data=json.loads(result.stdout)
                except json.JSONDecodeError:time.sleep(1);continue
                (args.out/f'{command}.json').write_text(json.dumps(data,indent=2)+'\n')
                runtime=data.get('runtime',{});success &= 'error' not in runtime and runtime.get('passed',True)
                device=runtime.get('device',{})
                if device.get('software_device'):success=False
                break
            time.sleep(1)
        else:
            (args.out/f'{command}_timeout.txt').write_text('No completed report before timeout. Inspect logcat; this is not a passed test.\n');success=False
        logs=run('logcat','-d','-t','500',check=False);(args.out/f'{command}_logcat.txt').write_text(logs.stdout+logs.stderr)
    print(json.dumps({'real_phone_test_completed':True,'successful':bool(success),'report_directory':str(args.out)},indent=2))
    raise SystemExit(0 if success else 2)
if __name__=='__main__':main()
