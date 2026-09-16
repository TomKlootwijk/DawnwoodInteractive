#!/usr/bin/env python3
"""Edit the exact 31 x 64-byte operator field as JSON; standard library only."""
from __future__ import annotations
import argparse
import json
import struct
from pathlib import Path

NAMES = ['klein','hadamard','phi','rk4','phyllotaxis','pinion','double_dot','T_shape',
         'pyramid','circle','cone','sphere','apex','delta_phi','blend','wavefront',
         'y_up','crystal','inverse_T','T_transform','jitter','bst','return',
         'phase_history','dichromatic','bayer','bc5','split','parity','psi','mutation']
OPS = ['MOV','ADD','SUB','MUL_Q16','XOR','AND','OR','ROL16','HAD_PLUS','HAD_MINUS',
       'MIN','MAX','BLEND','IMM','ADDI','PARITY_SELECT']
FIELDS = ['location','support','links','coeff','last_rg','history','inverse_t','route']


def unsigned(value: object, bits: int, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < 1 << bits:
        raise ValueError(f'{label} must be an unsigned {bits}-bit integer')
    return value


def decode(data: bytes) -> dict:
    if len(data) != 31 * 64:
        raise ValueError('Operator image must contain exactly 1984 bytes')
    result = {'schema': 'dawnwood-operator-image-v0.3', 'byte_order': 'little', 'operators': []}
    for index, words in enumerate(struct.iter_unpack('<16I', data)):
        record = {'index': index, 'name': NAMES[index]}
        for k, field in enumerate(FIELDS[:4]):
            record[field] = words[k]
        record['body'] = [{'op': OPS[w & 15], 'dst': (w >> 4) & 7, 'a': (w >> 7) & 7,
                           'b': (w >> 10) & 7, 'reserved': (w >> 13) & 7,
                           'imm': w >> 16} for w in words[4:12]]
        for k, field in enumerate(FIELDS[4:]):
            record[field] = words[k + 12]
        result['operators'].append(record)
    return result


def encode(document: dict) -> bytes:
    if document.get('schema') != 'dawnwood-operator-image-v0.3':
        raise ValueError('Unsupported operator-image schema')
    if document.get('byte_order') != 'little':
        raise ValueError('The native image uses little-endian words')
    records = document.get('operators', [])
    if len(records) != 31:
        raise ValueError('This ABI contains 31 operator records')
    output = bytearray()
    for index, record in enumerate(records):
        if record.get('index') != index:
            raise ValueError('Records must remain in implicit-tree index order')
        body = record['body']
        if len(body) != 8:
            raise ValueError(f'Operator {index} requires eight executable words')
        words = [unsigned(record[k], 32, k) for k in FIELDS[:4]]
        for instruction in body:
            opcode = OPS.index(instruction['op'])
            dst = unsigned(instruction['dst'], 3, 'dst')
            a = unsigned(instruction['a'], 3, 'a')
            b = unsigned(instruction['b'], 3, 'b')
            reserved = unsigned(instruction.get('reserved', 0), 3, 'reserved')
            imm = unsigned(instruction['imm'], 16, 'imm')
            words.append(opcode | (dst << 4) | (a << 7) | (b << 10) | (reserved << 13) | (imm << 16))
        words += [unsigned(record[k], 32, k) for k in FIELDS[4:]]
        output.extend(struct.pack('<16I', *words))
    return bytes(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['dump', 'pack'])
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error('Input and output must be distinct paths')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.action == 'dump':
        args.output.write_text(json.dumps(decode(args.input.read_bytes()), indent=2) + '\n', encoding='utf-8')
    else:
        args.output.write_bytes(encode(json.loads(args.input.read_text(encoding='utf-8'))))
    print(args.output)


if __name__ == '__main__':
    main()
