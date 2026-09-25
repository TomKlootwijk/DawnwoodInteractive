"""Compile sourced affine domain fields into Dawnwood's native DWI-D1 GPU state.

No service or GUI. Each invocation retains its input, native command receipts,
checkpoints, full-population constraint audit, and returned physical values.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import random
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / 'Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3'
BINARY = NATIVE / 'bin/windows-domain/dawnwood.exe'
KNOWLEDGE = ROOT / 'domain_knowledge/native'
STATE = struct.Struct('<24f4I4f')
OP = struct.Struct('<12f4I')
CFG = struct.Struct('<4I4f4I4f')
KINDS = {'equality': 0, 'halfspace': 1, 'slab': 2}


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def number(value, label):
    if type(value) not in (int, float) or not math.isfinite(value) or abs(value) > 1e6:
        raise ValueError(f'{label}: expected a finite number with magnitude <= 1e6')
    return float(value)


def vector(value, label):
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError(f'{label}: four coordinates required')
    return [number(x, label) for x in value]


def validate(spec):
    if not isinstance(spec, dict):
        raise ValueError('Domain definition must be a JSON object')
    allowed = {'name', 'description', 'coordinates', 'unit', 'scale', 'initial', 'spread',
               'constraints', 'sources', 'assumptions', 'tolerance'}
    if set(spec) - allowed:
        raise ValueError(f'Unknown domain keys: {sorted(set(spec) - allowed)}')
    result = dict(spec)
    if not isinstance(result.get('coordinates'), list) or len(result['coordinates']) != 4 or not all(isinstance(v, str) and v for v in result['coordinates']) or len(set(result['coordinates'])) != 4:
        raise ValueError('Four uniquely named coordinates required')
    for key in ('initial', 'scale', 'spread'):
        result[key] = vector(result.get(key, [0]*4 if key == 'spread' else None), key)
    if any(x <= 0 for x in result['scale']) or any(x < 0 for x in result['spread']):
        raise ValueError('Scales must be positive and spreads nonnegative')
    for x, spread, scale in zip(result['initial'], result['spread'], result['scale']):
        if (abs(x) + spread) / scale > 1e6:
            raise ValueError('Normalized initial coordinate envelope exceeds 1e6')
    laws = result.get('constraints')
    if not isinstance(laws, list) or not 1 <= len(laws) <= 32:
        raise ValueError('Supply 1..32 affine constraints')
    result['constraints'] = []
    identifiers = set()
    for item in laws:
        if not isinstance(item, dict) or set(item) - {'id','kind','normal','offset','halfwidth'}:
            raise ValueError('Unknown constraint structure')
        law = dict(item)
        if not isinstance(law.get('id'), str) or not law['id'] or law['id'] in identifiers:
            raise ValueError('Constraint ids must be unique, nonempty strings')
        identifiers.add(law['id'])
        if law.get('kind') not in KINDS:
            raise ValueError('Kinds are equality, halfspace, slab')
        law['normal'] = vector(law.get('normal'), 'normal')
        norm2 = sum(x*x for x in law['normal'])
        if not 1e-12 <= norm2 <= 1e12:
            raise ValueError('Normal squared length must be in [1e-12,1e12]')
        law['offset'] = number(law.get('offset'), 'offset')
        law['halfwidth'] = number(law.get('halfwidth', 0), 'halfwidth')
        if (law['kind'] == 'slab' and law['halfwidth'] <= 0) or (law['kind'] != 'slab' and law['halfwidth'] != 0):
            raise ValueError('Slabs require positive halfwidth; other kinds require zero halfwidth')
        result['constraints'].append(law)
    result['tolerance'] = number(result.get('tolerance', 2e-5), 'tolerance')
    if not 0 < result['tolerance'] <= 0.01:
        raise ValueError('Declare a tolerance in (0,0.01] in normalized distance units')
    return result


def command(folder, name, args, timeout=300):
    argv = [str(BINARY), *map(str, args)]
    target = folder / name
    env = os.environ.copy()
    removed = {k: env.pop(k) for k in list(env) if k.startswith('DAWNWOOD_') or k in ('VK_INSTANCE_LAYERS','VK_LAYER_VALIDATE_SYNC')}
    record = {'command': argv, 'cwd': str(ROOT), 'binary_sha256': hashlib.sha256(BINARY.read_bytes()).hexdigest(),
              'removed_environment_overrides': removed}
    start = time.perf_counter()
    with target.with_suffix('.stdout').open('wb') as out, target.with_suffix('.stderr').open('wb') as err:
        try:
            process = subprocess.run(argv, cwd=ROOT, env=env, stdout=out, stderr=err, timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            record['exit_code'] = process.returncode
        except subprocess.TimeoutExpired:
            record['timeout_seconds'] = timeout
            raise
        finally:
            record['wall_seconds'] = time.perf_counter() - start
            save(target.with_suffix('.command.json'), record)
    if process.returncode:
        raise RuntimeError(f'{name} failed ({process.returncode}); inspect {target.with_suffix(".stderr")}')
    report = json.loads(target.with_suffix('.stdout').read_text(encoding='utf-8'))
    save(target.with_suffix('.json'), report)
    if report.get('passed') is False or report.get('health', {}).get('passed') is False:
        raise RuntimeError(f'{name} reported numerical failure; raw evidence retained')
    return report


def read_checkpoint(path):
    raw = path.read_bytes()
    if len(raw) < 80 or raw[:8] not in (b'DWKN0003', b'DWKD0001') or struct.unpack_from('<II', raw, 8) != (128, 64):
        raise ValueError('Checkpoint ABI mismatch')
    cfg = CFG.unpack_from(raw, 16)
    if len(raw) != 80 + cfg[0]*128 + cfg[1]*64:
        raise ValueError('Checkpoint length mismatch')
    return raw, cfg


def compile_checkpoint(spec, seed_path, target, controller, seed):
    raw, cfg = read_checkpoint(seed_path)
    data = bytearray(raw)
    data[:8] = b'DWKD0001'
    c = list(cfg)
    c[1] = 31 + len(spec['constraints'])
    if controller in ('frozen','constant'):
        c[9] = 0
    CFG.pack_into(data, 16, *c)
    rng = random.Random(seed)
    for i in range(cfg[0]):
        # Lane zero is precisely the user's proposal; remaining lanes explore its
        # declared neighborhood. Population spread is data, not simulated readings.
        q = [(x + (0 if i == 0 else rng.uniform(-r,r))) / scale
             for x,r,scale in zip(spec['initial'],spec['spread'],spec['scale'])]
        struct.pack_into('<4f', data, 80+i*128+64, *q)
    offset = 80 + cfg[0]*128
    header = list(OP.unpack_from(data, offset))
    header[11] = len(spec['constraints'])
    header[15] |= 0x40000000
    OP.pack_into(data, offset, *header)
    if controller == 'edited':
        struct.pack_into('<I', data, offset + 30*64 + 48, 0x342)
    elif controller == 'constant':
        # 0x3 multiplies by coupling=0 => response zero, relaxation exactly 0.6.
        struct.pack_into('<f', data, offset + 30*64 + 24, 0)
        struct.pack_into('<I', data, offset + 30*64 + 48, 3)
    for law in spec['constraints']:
        a,b,c,d = law['normal']
        data.extend(OP.pack(.5,.5,1,1,a,b,c,d,law['offset'],law['halfwidth'],0,0,0,1,KINDS[law['kind']],0x80000000))
    target.write_bytes(data)


def audit(path, spec, csv_path=None):
    raw,cfg = read_checkpoint(path)
    # Audit the exact FP32 laws executed, not their possibly different JSON doubles.
    offset = 80 + cfg[0]*128
    laws = []
    for i,definition in enumerate(spec['constraints']):
        record = OP.unpack_from(raw, offset+(31+i)*64)
        laws.append((definition['id'],record[14],record[4:8],record[8],record[9]))
    per_law = {law[0]: {'max_violation': 0.0, 'violating_states': 0} for law in laws}
    authored_laws = [(law['id'], KINDS[law['kind']], law['normal'], law['offset'], law['halfwidth'])
                     for law in spec['constraints']]
    authored_per_law = {law[0]: {'max_violation': 0.0, 'violating_states': 0} for law in laws}
    total=0.0
    maximum=0.0
    feasible=0
    authored_feasible=0
    authored_maximum=0.0
    jointly_feasible=0
    lane_zero=None
    rows=[]
    for i in range(cfg[0]):
        q = struct.unpack_from('<4f',raw,80+i*128+64)
        if not all(math.isfinite(x) for x in q):
            raise ValueError('Nonfinite returned domain coordinate')
        worst=0.0
        distances={}
        for name,kind,normal,b,width in laws:
            r = sum(a*x for a,x in zip(normal,q))-b
            norm=math.sqrt(sum(a*a for a in normal))
            d = (abs(r)-width)/norm if kind==2 else r/norm
            v = abs(d) if kind==0 else max(d,0)
            distances[name]=d
            per_law[name]['max_violation']=max(per_law[name]['max_violation'],v)
            per_law[name]['violating_states']+=int(v>spec['tolerance'])
            worst=max(worst,v)
        feasible+=int(worst<=spec['tolerance'])
        authored_worst=0.0
        authored_distances={}
        for name,kind,normal,b,width in authored_laws:
            r=sum(a*x for a,x in zip(normal,q))-b
            norm=math.sqrt(sum(a*a for a in normal))
            d=(abs(r)-width)/norm if kind==2 else r/norm
            v=abs(d) if kind==0 else max(d,0)
            authored_distances[name]=d
            authored_per_law[name]['max_violation']=max(authored_per_law[name]['max_violation'],v)
            authored_per_law[name]['violating_states']+=int(v>spec['tolerance'])
            authored_worst=max(authored_worst,v)
        authored_feasible+=int(authored_worst<=spec['tolerance'])
        authored_maximum=max(authored_maximum,authored_worst)
        jointly_feasible+=int(max(worst,authored_worst)<=spec['tolerance'])
        total+=worst
        maximum=max(maximum,worst)
        physical=[x*s for x,s in zip(q,spec['scale'])]
        if i==0:
            lane_zero={'normalized':list(q),'physical':dict(zip(spec['coordinates'],physical)),
                       'signed_distances':distances,'authored_signed_distances':authored_distances,
                       'max_violation':worst,'authored_max_violation':authored_worst}
        if csv_path:
            rows.append([i,*physical,worst,authored_worst])
    if csv_path:
        with csv_path.open('w',newline='',encoding='utf-8') as f:
            writer=csv.writer(f)
            writer.writerow(['lane',*spec['coordinates'],'maximum_packed_normalized_violation','maximum_authored_normalized_violation'])
            writer.writerows(rows)
    return {'epoch':cfg[2],'count':cfg[0],'feasible_states':jointly_feasible,'all_feasible':jointly_feasible==cfg[0],
            'packed_feasible_states':feasible,'authored_feasible_states':authored_feasible,
            'authored_max_violation':authored_maximum,'authored_per_constraint':authored_per_law,
            'max_violation':maximum,'mean_max_violation':total/cfg[0],
            'tolerance':spec['tolerance'],'per_constraint':per_law,'lane_zero':lane_zero,
            'constraint_record_sha256':hashlib.sha256(raw[offset+31*64:]).hexdigest(),
            'core_operator_sha256':hashlib.sha256(raw[offset:offset+31*64]).hexdigest(),
            'state_sha256':hashlib.sha256(raw[80:offset]).hexdigest()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--example',help='Name in domain_knowledge/native')
    source.add_argument('--spec',type=Path,help='Your four-coordinate affine field definition')
    parser.add_argument('--values',help='JSON array of four proposed physical values, overriding initial')
    parser.add_argument('--count',type=int,default=257)
    parser.add_argument('--epochs',type=int,default=64)
    parser.add_argument('--stride',type=int,default=16)
    parser.add_argument('--seed',type=int,default=756)
    parser.add_argument('--controller',choices=['live','frozen','edited','constant'],default='live')
    parser.add_argument('--backend',choices=['vulkan','cpu'],default='vulkan')
    parser.add_argument('--device',default='RTX 5070 Ti')
    parser.add_argument('--verify-steps',type=int,default=8)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if not 1<=args.count<=1048576 or not 1<=args.epochs<=4096 or not 1<=args.stride<=args.epochs or not 0<=args.verify_steps<=64:
        parser.error('count 1..1048576; epochs 1..4096; stride 1..epochs; verify-steps 0..64')
    if args.example and (Path(args.example).name != args.example or args.example not in {p.stem for p in KNOWLEDGE.glob('*.json')}):
        parser.error('Unknown example; available: '+', '.join(p.stem for p in KNOWLEDGE.glob('*.json')))
    spec_path=args.spec or KNOWLEDGE/(args.example+'.json')
    spec=json.loads(spec_path.read_text(encoding='utf-8'))
    if args.values:
        spec['initial']=json.loads(args.values)
    spec=validate(spec)
    if not BINARY.is_file():
        raise ValueError(f'Build the domain runtime first: {BINARY}')
    folder=args.output.resolve()
    folder.mkdir(parents=True,exist_ok=False)
    save(folder/'definition.json',spec)
    save(folder/'invocation.json',{'argv':sys.argv,'profile':'DWI-D1-0.1','controller':args.controller,
                                  'seed':args.seed,'source_definition':str(spec_path.resolve()),
                                  'compiler_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    command(folder,'seed',['run','--backend','cpu','--count',args.count,'--steps',0,'--checkpoint',folder/'seed.dwk'])
    initial=folder/'initial.dwk'
    compile_checkpoint(spec,folder/'seed.dwk',initial,args.controller,args.seed)
    before=audit(initial,spec)
    verification=None
    if args.verify_steps:
        verification=command(folder,'verify',['verify','--device',args.device,'--resume',initial,'--steps',args.verify_steps])
    frames=[before]
    current=initial
    for epoch in range(args.stride,args.epochs+args.stride,args.stride):
        end=min(epoch,args.epochs)
        output=folder/f'epoch-{end:06d}.dwk'
        command(folder,f'epoch-{end:06d}',['run','--backend',args.backend,'--device',args.device,
                    '--resume',current,'--steps',end-frames[-1]['epoch'],'--checkpoint',output])
        frames.append(audit(output,spec,folder/'solutions.csv' if end==args.epochs else None))
        current=output
        print(f"epoch {end}: {frames[-1]['feasible_states']}/{args.count} feasible, max packed violation {frames[-1]['max_violation']:.8g}, max authored violation {frames[-1]['authored_max_violation']:.8g}",flush=True)
    immutable=all(x['constraint_record_sha256']==before['constraint_record_sha256'] for x in frames)
    report={'profile':'DWI-D1-0.1','name':spec.get('name',spec_path.stem),'backend':args.backend,
            'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),
            'controller':args.controller,'verification':verification,'laws_unchanged':immutable,
            'controller_field_changed':frames[-1]['core_operator_sha256']!=before['core_operator_sha256'],
            'initial':before,'final':frames[-1],'frames':frames,
            'notes':['Each analytic affine field is an exact SDF in declared normalized coordinates, evaluated in FP32 on device.',
                     'Feasibility requires separate float64 audits of both packed FP32 laws and original authored JSON coefficients to pass.',
                     'Feasibility is measured at the declared tolerance, not proof of dynamics, optimality or physical validity.',
                     'Scientific law records are protected; mutable executable controller records determine relaxation.']}
    save(folder/'result.json',report)
    if not immutable:
        raise RuntimeError('Protected domain laws changed')
    print(json.dumps({'output':str(folder),'all_feasible':report['final']['all_feasible'],
                      'lane_zero':report['final']['lane_zero']},indent=2))
    # Nonconvergence stays a completed observation, with distinct nonzero status.
    return 0 if report['final']['all_feasible'] else 2


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f'{type(error).__name__}: {error}',file=sys.stderr)
        raise SystemExit(1)
