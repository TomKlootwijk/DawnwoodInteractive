#!/usr/bin/env python3
"""Compile both real Vulkan kernels and embed their SPIR-V for desktop/Android."""
from pathlib import Path
import argparse, hashlib, json, shutil, struct, subprocess
ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--validate-only',action='store_true');args=parser.parse_args()
    compiler=shutil.which('glslangValidator') or shutil.which('glslc')
    validator=shutil.which('spirv-val')
    if not args.validate_only and not compiler:raise SystemExit('Install glslangValidator or glslc (Vulkan SDK).')
    arrays=['#pragma once\n#include <cstdint>\n#include <cstddef>\n']
    rows=[]
    for name in ['mutate','evolve']:
        src=ROOT/'shaders'/f'{name}.comp';out=src.with_suffix('.spv')
        if not args.validate_only:
            if 'glslangValidator' in Path(compiler).name:
                command=[compiler,'-V','--target-env','vulkan1.1',f'-I{ROOT/"include"}',str(src),'-o',str(out)]
            else:command=[compiler,'--target-env=vulkan1.1',f'-I{ROOT/"include"}',str(src),'-o',str(out)]
            subprocess.run(command,check=True)
        if validator:subprocess.run([validator,'--target-env','vulkan1.1',str(out)],check=True)
        data=out.read_bytes();assert len(data)%4==0
        words=struct.unpack('<'+'I'*(len(data)//4),data)
        arrays.append(f'inline const uint32_t {name}_spv[] = {{\n'+',\n'.join(','.join(hex(w)+'u' for w in words[i:i+12]) for i in range(0,len(words),12))+'\n};\n')
        rows.append({'shader':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'spirv_validation_executed':bool(validator)})
    if not args.validate_only:
        (ROOT/'src/spirv.hpp').write_text(''.join(arrays))
        source_paths=['include/numeric_types.inc','include/numeric_evolve.inc','shaders/mutate.comp','shaders/evolve.comp']
        fingerprint=hashlib.sha256(''.join(hashlib.sha256((ROOT/x).read_bytes()).hexdigest() for x in source_paths).encode()).hexdigest()
        (ROOT/'shaders/source.sha256').write_text(fingerprint+'\n')
    (ROOT/'results/shader_build.json').write_text(json.dumps({'compiler':compiler,'validator':validator,'shaders':rows},indent=2)+'\n')
    print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
