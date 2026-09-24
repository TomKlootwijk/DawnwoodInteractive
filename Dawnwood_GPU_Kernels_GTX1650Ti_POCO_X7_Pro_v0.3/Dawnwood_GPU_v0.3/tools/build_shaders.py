#!/usr/bin/env python3
"""Compile both real Vulkan kernels and embed their SPIR-V for desktop/Android."""
from pathlib import Path
import argparse, hashlib, json, shutil, struct, subprocess, tempfile
ROOT=Path(__file__).resolve().parents[1]
def preserve_math_functions(data, interpreter=False):
    """Add standard DontInline hints; device compilers may ignore these hints."""
    words=list(struct.unpack('<'+'I'*(len(data)//4),data))
    names={};offset=5
    while offset<len(words):
        count=words[offset]>>16;opcode=words[offset]&0xffff
        if count==0 or offset+count>len(words):raise ValueError('Invalid SPIR-V instruction size')
        if opcode==5: # OpName
            names[words[offset+1]]=struct.pack('<'+'I'*(count-2),*words[offset+2:offset+count]).split(b'\0',1)[0].decode('utf-8')
        offset+=count
    math_prefixes=('dw_sin(', 'dw_cos(', 'dw_exp(', 'dw_trig_reduce(', 'dw_div(', 'dw_sqrt(')
    prefixes=math_prefixes + (('dw_apply(', 'dw_field(', 'dw_shape(', 'dw_body(', 'dw_geometry(', 'dw_derivative(') if interpreter else ())
    preserved=[];offset=5
    while offset<len(words):
        count=words[offset]>>16;opcode=words[offset]&0xffff
        if opcode==54 and names.get(words[offset+2],'').startswith(prefixes): # OpFunction
            words[offset+3]=(words[offset+3]&~1)|2 # clear Inline, set DontInline
            preserved.append(names[words[offset+2]])
        offset+=count
    if sum(name.startswith(math_prefixes) for name in preserved)!=len(math_prefixes):raise ValueError(f'Expected {len(math_prefixes)} named portable math functions, found {preserved}')
    return struct.pack('<'+'I'*len(words),*words),preserved

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--validate-only',action='store_true');parser.add_argument('--optimize',action='store_true',help='Optimize offline to reduce device compiler work (glslc -O / glslang -Os).');parser.add_argument('--preserve-math-functions',action='store_true',help='Keep portable sin/cos/exp/reducer/division/sqrt function boundaries during spirv-opt optimization; requires --optimize and spirv-opt.');parser.add_argument('--preserve-interpreter-functions',action='store_true',help='Also retain field/body/evolution helper boundaries; requires --preserve-math-functions.');args=parser.parse_args()
    compiler=shutil.which('glslangValidator') or shutil.which('glslc')
    validator=shutil.which('spirv-val')
    optimizer=shutil.which('spirv-opt')
    if args.preserve_math_functions and (not args.optimize or not optimizer or args.validate_only):parser.error('--preserve-math-functions requires --optimize, spirv-opt, and a fresh compilation')
    if args.preserve_interpreter_functions and not args.preserve_math_functions:parser.error('--preserve-interpreter-functions requires --preserve-math-functions')
    if not args.validate_only and not compiler:raise SystemExit('Install glslangValidator or glslc (Vulkan SDK).')
    arrays=['#pragma once\n#include <cstdint>\n#include <cstddef>\n']
    rows=[]
    for name in ['mutate','evolve','prepare','slope','combine','geometry','finish']:
        src=ROOT/'shaders'/f'{name}.comp';out=src.with_suffix('.spv')
        preserved=[]
        if not args.validate_only:
            if 'glslangValidator' in Path(compiler).name:
                command=[compiler,'-V','--target-env','vulkan1.1',f'-I{ROOT/"include"}',str(src),'-o',str(out)]
            else:command=[compiler,'--target-env=vulkan1.1',f'-I{ROOT/"include"}',str(src),'-o',str(out)]
            if args.optimize and not args.preserve_math_functions:command.insert(1,'-Os' if 'glslangValidator' in Path(compiler).name else '-O')
            subprocess.run(command,check=True)
            if args.preserve_math_functions:
                hinted,preserved=preserve_math_functions(out.read_bytes(),args.preserve_interpreter_functions)
                with tempfile.TemporaryDirectory(prefix='dawnwood-math-') as temporary:
                    intermediate=Path(temporary)/'hinted.spv';intermediate.write_bytes(hinted)
                    subprocess.run([optimizer,'-O',str(intermediate),'-o',str(out)],check=True)
        if validator:subprocess.run([validator,'--target-env','vulkan1.1',str(out)],check=True)
        data=out.read_bytes();assert len(data)%4==0
        words=struct.unpack('<'+'I'*(len(data)//4),data)
        arrays.append(f'inline const uint32_t {name}_spv[] = {{\n'+',\n'.join(','.join(hex(w)+'u' for w in words[i:i+12]) for i in range(0,len(words),12))+'\n};\n')
        rows.append({'shader':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'spirv_validation_executed':bool(validator),'preserved_math_functions':preserved})
    if not args.validate_only:
        (ROOT/'src/spirv.hpp').write_text(''.join(arrays))
        source_paths=['include/numeric_types.inc','include/numeric_math.inc','include/numeric_evolve.inc','shaders/mutate.comp','shaders/evolve.comp','shaders/operator_texture.inc','shaders/state_buffers.inc','shaders/evolution_pass.inc','shaders/prepare.comp','shaders/slope.comp','shaders/combine.comp','shaders/geometry.comp','shaders/finish.comp']
        fingerprint=hashlib.sha256(''.join(hashlib.sha256((ROOT/x).read_bytes()).hexdigest() for x in source_paths).encode()).hexdigest()
        (ROOT/'shaders/source.sha256').write_text(fingerprint+'\n')
    (ROOT/'results/shader_build.json').write_text(json.dumps({'compiler':compiler,'validator':validator,'optimizer':optimizer,'offline_optimization_requested':args.optimize,'preserve_math_functions':args.preserve_math_functions,'preserve_interpreter_functions':args.preserve_interpreter_functions,'validation_only':args.validate_only,'shaders':rows},indent=2)+'\n')
    print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
