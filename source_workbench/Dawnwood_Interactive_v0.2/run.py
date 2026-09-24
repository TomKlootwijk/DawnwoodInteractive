#!/usr/bin/env python3
"""Run and edit Dawnwood's unified symbolic circulation using Python 3.10+."""
from pathlib import Path
import argparse
import csv
import json
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from dawnwood.kernel import Kernel

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    r = sub.add_parser('run', help='Build a recurrent expression graph and write its live state')
    r.add_argument('--steps', type=int, default=16)
    r.add_argument('--model', type=Path, default=ROOT/'model/substrate.json')
    r.add_argument('--cycle', type=Path, default=ROOT/'model/cycle.json')
    r.add_argument('--session', type=Path, default=ROOT/'examples/session.json')
    r.add_argument('--resume', type=Path)
    r.add_argument('--body-edit', type=Path)
    r.add_argument('--out', type=Path, default=ROOT/'work/session')
    r.add_argument('--bayer', action='store_true')
    cat = sub.add_parser('catalogue', help='Print the editable operator array')
    cat.add_argument('--model', type=Path, default=ROOT/'model/substrate.json')
    ins = sub.add_parser('inspect', help='Inspect an expression node or live SDF operator')
    ins.add_argument('snapshot', type=Path)
    ins.add_argument('--node', type=int)
    ins.add_argument('--operator')
    pack = sub.add_parser('packing', help='Evaluate bytes/element arithmetic for an editable budget')
    pack.add_argument('--bytes', type=int, default=12*(2**30))
    args = p.parse_args()
    if args.command == 'catalogue':
        for o in read(args.model)['operators']:
            print(f"{o['index']:>3}  {o['key']:<16} {o['label']}")
    elif args.command == 'packing':
        if args.bytes < 0:
            p.error('The byte budget must be nonnegative')
        data = read(ROOT/'model/packing_scenarios.json')
        rows = [dict(name=x['name'], byte_budget=args.bytes,
                     bytes_per_element=x['bytes_per_element'],
                     element_count=args.bytes//x['bytes_per_element']) for x in data['rows']]
        print(json.dumps({'calculation': 'floor(byte_budget / bytes_per_element)',
                          'rows': rows, 'source_implicit_range': data['implicit_tree_source_range']},indent=2))
    elif args.command == 'inspect':
        data = read(args.snapshot)
        if args.operator:
            op = next(o for o in data['operators'] if o['key'] == args.operator)
            print(json.dumps({'operator': op, 'body_node': data['graph'][op['body']],
                              'field_node': data['graph'][op['field']],
                              'anchor_node': data['graph'][op['anchor']]}, indent=2))
        else:
            idx = args.node if args.node is not None else data['refs']['state']
            print(json.dumps(data['graph'][idx], indent=2))
    else:
        if args.steps < 0:
            p.error('The step count must be nonnegative')
        session = read(args.session)
        for name in ('jitter_bits', 'neck_bits'):
            if not session[name]:
                p.error(f'{name} requires at least one example bit')
        kernel = Kernel.from_snapshot(read(args.resume)) if args.resume else Kernel(read(args.model),read(args.cycle))
        if args.body_edit:
            edit = read(args.body_edit)
            kernel.set_body(edit['key'], edit['body'])
        args.out.mkdir(parents=True, exist_ok=True)
        with (args.out/'trace.jsonl').open('w',encoding='utf-8') as f:
            for _ in range(args.steps):
                epoch = kernel.epoch
                j = session['jitter_bits'][epoch % len(session['jitter_bits'])]
                neck = session['neck_bits'][epoch % len(session['neck_bits'])]
                row = kernel.step(j, session['route_bits'], neck,
                                  bayer=args.bayer or session.get('bayer',False))
                f.write(json.dumps(row,ensure_ascii=False)+'\n')
        snap = kernel.snapshot()
        (args.out/'snapshot.json').write_text(json.dumps(snap,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
        summary = {'kind':'symbolic substrate execution','epochs':kernel.epoch,
                   'new_steps':args.steps,'operators':len(kernel.operators),
                   'expression_nodes':len(kernel.g.nodes),'state_sha256':snap['state_sha256'],
                   'files':['trace.jsonl','snapshot.json','summary.json']}
        (args.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(summary,indent=2))

if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        print(f'Dawnwood: {exc}', file=sys.stderr)
        sys.exit(1)
