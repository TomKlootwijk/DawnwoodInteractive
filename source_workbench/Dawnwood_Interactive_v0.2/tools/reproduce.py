"""Compare fresh and checkpointed symbolic execution with the shipped session."""
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from dawnwood.kernel import Kernel

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def advance(kernel, count, session):
    for _ in range(count):
        n=kernel.epoch
        kernel.step(session['jitter_bits'][n%len(session['jitter_bits'])],
                    session['route_bits'],session['neck_bits'][n%len(session['neck_bits'])],
                    bayer=session.get('bayer',False))
    return kernel

session=read(ROOT/'examples/session.json')
reference=read(ROOT/'results/source_session/summary.json')
model=read(ROOT/'model/substrate.json');cycle=read(ROOT/'model/cycle.json')
steps=reference['epochs']
fresh=advance(Kernel(model,cycle),steps,session)
split=steps//2
continued=advance(Kernel(model,cycle),split,session)
continued=Kernel.from_snapshot(json.loads(json.dumps(continued.snapshot())))
advance(continued,steps-split,session)
a=fresh.g.digest(fresh.state);b=continued.g.digest(continued.state)
report={'kind':'symbolic expression reproduction','steps':steps,
        'shipped':reference['state_sha256'],'fresh':a,'checkpointed':b,
        'matches':a==b==reference['state_sha256']}
(ROOT/'results/reproduction.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
raise SystemExit(0 if report['matches'] else 1)
