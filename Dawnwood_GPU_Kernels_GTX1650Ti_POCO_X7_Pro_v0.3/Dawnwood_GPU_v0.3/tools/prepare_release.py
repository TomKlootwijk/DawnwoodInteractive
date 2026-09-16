"""Build, run tests, record actual availability, and prepare a source-faithful release.

This script never assigns a passed device test merely because a build succeeded.
"""
from pathlib import Path
import datetime, hashlib, json, os, platform, shutil, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
RESULTS=ROOT/'results';RESULTS.mkdir(exist_ok=True)
records=[]
def command(name,args,cwd=ROOT,timeout=180):
    record={'name':name,'command':[str(x) for x in args],'cwd':str(cwd),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        r=subprocess.run([str(x) for x in args],cwd=cwd,capture_output=True,text=True,timeout=timeout)
        (RESULTS/f'{name}.stdout').write_text(r.stdout);(RESULTS/f'{name}.stderr').write_text(r.stderr)
        record['exit_code']=r.returncode
    except Exception as e:record['error']=str(e);record['exit_code']=None
    records.append(record);(RESULTS/'build_commands.json').write_text(json.dumps(records,indent=2)+'\n')
    print(name,record.get('exit_code'),record.get('error',''),flush=True)
    return record.get('exit_code')==0

def read_json(path):
    try:return json.loads(path.read_text())
    except Exception:return None

def main():
    environment={'platform':platform.platform(),'machine':platform.machine(),'python':sys.version,'tools':{x:shutil.which(x) for x in ['cmake','g++','clang++','glslangValidator','glslc','spirv-val','vulkaninfo','adb','java','gradle','nvidia-smi']}}
    (RESULTS/'build_environment.json').write_text(json.dumps(environment,indent=2)+'\n')
    shaders=command('release_shaders',[sys.executable,ROOT/'tools/build_shaders.py'])
    configured=shaders and command('release_configure',['cmake','-S',ROOT,'-B',ROOT/'build','-DCMAKE_BUILD_TYPE=Release'])
    compiled=configured and command('release_compile',['cmake','--build',ROOT/'build','-j2'])
    binary=ROOT/'build'/('dawnwood.exe' if os.name=='nt' else 'dawnwood')
    cpu_pass=claims_pass=False
    if compiled:
        cpu_pass=command('release_ctest',['ctest','--test-dir',ROOT/'build','--output-on-failure'])
        claims_pass=command('release_claims',[sys.executable,ROOT/'tools/run_claims.py','--binary',binary,'--allow-software','--bench'],timeout=240)
        # Verify a resumed GPU run separately from the epoch-by-epoch comparison.
        command('release_cpu_reference',[binary,'run','--backend','cpu','--count','64','--steps','32','--checkpoint',RESULTS/'cpu_32.dwk','--out',RESULTS/'cpu_32.json'])
        command('release_vulkan_batch',[binary,'run','--count','64','--steps','32','--batch','8','--allow-software','--checkpoint',RESULTS/'vulkan_32.dwk','--out',RESULTS/'vulkan_32.json'])
        if cpu_pass:
            destination=ROOT/'bin'/f'{sys.platform}-{platform.machine()}'
            destination.mkdir(parents=True,exist_ok=True);shutil.copy2(binary,destination/binary.name)
    sdk_candidates=[Path(x) for x in [os.environ.get('ANDROID_SDK_ROOT',''),os.environ.get('ANDROID_HOME','')] if x]
    sdk_candidates += [Path('/opt/android-sdk'),Path('/opt/android'),Path('/usr/lib/android-sdk'),Path('/usr/local/lib/android/sdk')]
    sdk=next((x for x in sdk_candidates if (x/'ndk').exists()),None)
    toolchains=list(sdk.glob('ndk/*/build/cmake/android.toolchain.cmake')) if sdk else []
    android_native=False;apk_built=False;android_reason='No installed Android SDK/NDK toolchain found in this build environment.'
    if toolchains:
        toolchain=sorted(toolchains)[-1]
        android_config=command('release_android_configure',['cmake','-S',ROOT,'-B',ROOT/'build-android',f'-DCMAKE_TOOLCHAIN_FILE={toolchain}','-DANDROID_ABI=arm64-v8a','-DANDROID_PLATFORM=android-28','-DCMAKE_BUILD_TYPE=Release'])
        android_native=android_config and command('release_android_compile',['cmake','--build',ROOT/'build-android','-j2'])
        android_reason='Native build attempted with '+str(toolchain)
        if android_native:
            so=ROOT/'build-android/libdawnwood_jni.so'
            if so.exists():(ROOT/'bin/android-arm64-v8a').mkdir(parents=True,exist_ok=True);shutil.copy2(so,ROOT/'bin/android-arm64-v8a'/so.name)
        if (sdk/'platforms/android-35').exists() and (sdk/'ndk/27.2.12479018').exists() and shutil.which('java'):
            envline='sdk.dir='+str(sdk).replace('\\','\\\\')+'\n';(ROOT/'android/local.properties').write_text(envline)
            wrapper=ROOT/'android'/('gradlew.bat' if os.name=='nt' else 'gradlew')
            apk_built=command('release_apk',[wrapper,'--no-daemon','assembleDebug'],cwd=ROOT/'android',timeout=240)
            apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk'
            if apk_built and apk.exists():(ROOT/'bin/android').mkdir(parents=True,exist_ok=True);shutil.copy2(apk,ROOT/'bin/android/Dawnwood_GPU_debug.apk')
    adb=shutil.which('adb')
    if adb:command('release_adb_devices',[adb,'devices','-l'],timeout=20)
    nvidia=shutil.which('nvidia-smi')
    if nvidia:command('release_nvidia_identity',[nvidia,'--query-gpu=name,memory.total,driver_version','--format=csv'],timeout=20)
    summary=read_json(RESULTS/'claims/summary.json') or {}
    status={'release':'0.3.0','profile':'DWI-N1','shaders_compiled':shaders,'desktop_compiled':compiled,'cpu_ctest_passed':cpu_pass,'source_claim_suite_passed':claims_pass,'claims':summary,'android_native_compiled':bool(android_native),'android_apk_built':bool(apk_built),'android_build_note':android_reason,'POCO_hardware_test_executed':False,'GTX_1650_Ti_hardware_test_executed':bool(summary.get('real_GTX_1650_Ti_test',False)),'original_source_present':(ROOT/'source/double-slit-theory.pdf').exists()}
    (RESULTS/'release_status.json').write_text(json.dumps(status,indent=2)+'\n')
    device=summary.get('vulkan_device',{})
    lines=['# Actual build and test status — Dawnwood GPU 0.3','',
           '| Stage | Recorded result |','|---|---|',
           f'| SPIR-V compilation | {shaders} |',f'| Desktop C++ compilation | {compiled} |',
           f'| CPU CTest suite | {cpu_pass} |',f'| Combined source-claim suite | {claims_pass} |',
           f'| Vulkan device used | {device.get("name","No completed Vulkan probe")} |',
           f'| Software Vulkan device | {device.get("software_device","not established")} |',
           f'| Every-epoch CPU/Vulkan comparison | {summary.get("vulkan_comparison_passed","not executed")} |',
           f'| Numerical operator-body coverage | {summary.get("body_coverage_passed","not executed")} |',
           f'| Checkpoint replay | {summary.get("checkpoint_replay_passed","not executed")} |',
           f'| Android arm64 native compilation | {bool(android_native)} |',f'| Android APK build | {bool(apk_built)} |',
           f'| Actual GTX 1650 Ti test | {status["GTX_1650_Ti_hardware_test_executed"]} |',
           '| Actual POCO X7 Pro test | Not executed in this environment |','',android_reason,'',
           'False means the stage was not successfully completed; consult the corresponding command record and stderr to distinguish an unavailable toolchain from a failed test. Nothing is promoted from compiled to device-tested.',
           '', 'The full command/exit-code record is `build_commands.json`. Numerical claim evidence is under `claims/`. `CLAIMS.md` distinguishes numerical fixtures, counterexamples, hardware measurements and physical/formal evidence still to be supplied.']
    (RESULTS/'STATUS.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:v for k,v in status.items() if k!='claims'},indent=2),flush=True)
    return 0 if compiled and cpu_pass and claims_pass else 2
if __name__=='__main__':raise SystemExit(main())
