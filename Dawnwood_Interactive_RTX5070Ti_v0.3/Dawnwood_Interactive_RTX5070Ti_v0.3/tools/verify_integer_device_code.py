#!/usr/bin/env python3
"""Audit every PTX function, optionally plus cuobjdump SASS, for integer arithmetic.

Examples:
  nvcc -ptx -arch=compute_120 -std=c++17 -Iinclude src/integer_main.cu -o work/integer.ptx
  cuobjdump --dump-sass build/dawnwood_integer.exe > work/integer.sass
  python tools/verify_integer_device_code.py work/integer.ptx --sass work/integer.sass \
      --require-entry initialize --require-entry evolve --out work/integer_audit.json

Use the same defines, options and source revision as the executable build. The
tool records hashes but cannot prove that independently supplied PTX and SASS
come from the same build. No compiler or GPU process is launched by this tool.

The audit is conservative: unknown instructions, unparsed executable statements,
and unresolved PTX calls fail. All defined functions are scanned, even if unused.
Floating declarations, comments and bit constants alone are not instructions.
--allow-native-unorm-boundary permits f32 texture coordinates/results and f32
bit transfers (mov/ld/st), reporting each one separately. It never permits
floating arithmetic, numeric conversion, comparison or transcendental opcodes.
Passing PTX alone does not establish absence of floating instructions in SASS:
integer division can be lowered through floating reciprocal instructions.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys


SOURCES = [
    'https://docs.nvidia.com/cuda/parallel-thread-execution/index.html',
    'https://docs.nvidia.com/cuda/cuda-binary-utilities/index.html',
]
FLOAT_TYPES = {
    'f16', 'f16x2', 'f32', 'f32x2', 'f64', 'bf16', 'bf16x2', 'tf32',
    'e4m3', 'e4m3x2', 'e4m3x4', 'e5m2', 'e5m2x2', 'e5m2x4',
    'e2m1', 'e2m1x2', 'e2m1x4', 'e2m1x8', 'e2m3', 'e2m3x2', 'e2m3x4',
    'e3m2', 'e3m2x2', 'e3m2x4', 'ue8m0', 'ue8m0x2',
    'f8', 'f6', 'f4', 'mxf8f6f4', 'mxf4', 'mxf4nvf4',
}
FLOAT_TYPE_PATTERN = r'(?:b?f|tf)[0-9]+(?:x[0-9]+)?|u?e[0-9]+m[0-9]+(?:x[0-9]+)?'
# Known PTX roots that admit integer/bit/predicate execution. Types are checked
# separately, including on memory, texture, conversion and matrix operations.
PTX_ROOTS = set('''
abs activemask add addc and applypriority atom bar barrier bfe bfi bfind bmsk
bra brev brkpt brx call clz cnot copysign cp createpolicy cvt cvta discard div
elect exit fence fns getctarank griddepcontrol isspacep ld ldmatrix mad mad24
madc match max mbarrier membar min mma mov mul mul24 multimem nanosleep neg
nop not or pmevent popc prefetch prefetchu prmt red redux rem ret sad selp set
setmaxnreg setp shf shfl shl shr slct st stackrestore stacksave stmatrix sub
subc suld suq sured sust szext testp tex tld4 trap txq vabsdiff vabsdiff2
vabsdiff4 vadd vadd2 vadd4 vmax vmax2 vmax4 vmin vmin2 vmin4 vote vset vset2
vset4 vshl vshr vsub vsub2 vsub4 wgmma wmma xor
'''.split())
PTX_FLOAT_ONLY_ROOTS = set('''
cos ex2 fma lg2 rcp rsqrt sin sqrt tanh
'''.split())
# The documented floating instructions are listed explicitly so e.g. FLO (find
# leading one) and FENCE are not mistaken for floating arithmetic by a prefix.
SASS_FLOAT_ROOTS = set('''
FADD FADD2 FADD32I FCHK FCMP FFMA FFMA2 FFMA32I FHADD FHFMA FMNMX FMNMX3
FMUL FMUL2 FMUL32I FSEL FSET FSETP FSWZADD MUFU RRO HADD2 HADD2_32I
HFMA2 HFMA2_32I HMMA HMNMX2 HMUL2 HMUL2_32I HSET2 HSETP2 DADD DFMA
DMMA DMUL DMNMX DSET DSETP OMMA QMMA VHMNMX F2F F2FP F2I F2IP I2F I2FP FRND
'''.split())
SASS_FLOAT_ROOTS |= {'U' + opcode for opcode in SASS_FLOAT_ROOTS}
SASS_INTEGER_ROOTS = set('''
ATOM ATOMS B2R BAR BFE BFI BMMA BMSK BPT BRA BREV BRK BRX BRXU BSSY BSYNC CALL CCTL
CCTLL CCTLT CCTLU CS2R DEPBAR ERRBAR EXIT FENCE FLO GETLMEMBASE I2I I2IP
IABS IADD IADD3 IADD32I IDP IDP4A IMAD IMMA IMNMX IMUL IMUL32I ISCADD
ISCADD32I ISETP JCAL JMP JMX JMXU KILL LD LDC LDG LDGDEPBAR LDGMC LDGSTS
LDL LDS LDSM LEA LEPC LOP LOP3 LOP32I MATCH MEMBAR MOV MOV32I MOV64IUR
MOVM NANOSLEEP NOP P2R PBK PCNT PEXIT PLOP3 PMTRIG POPC PRET PRMT PSETP
QSPC R2P R2UR RED REDUX RET RPCMOV RTTCALL S2R S2UR SEL SETCTAID
SETLMEMBASE SGXT SHF SHFL SHL SHR SSY ST STG STL STS SUATOM SULD SURED
SUST SYNC TEX TEXS TLD TLD4 TLD4S TLDS TRAP TXQ VABSDIFF VABSDIFF4
VIADD VIADDMNMX VIMNMX VIMNMX3 VOTE WARPGROUP WARPSYNC YIELD
'''.split())
SASS_INTEGER_ROOTS |= {'U' + opcode for opcode in SASS_INTEGER_ROOTS}
SASS_INTEGER_ROOTS |= {'UP2UR', 'UR2UP', 'UCGABAR_ARV', 'UCGABAR_WAIT', 'UCLEA',
                      'LDCU', 'BMOV', 'BREAK', 'REDG', 'VOTEU'}
TEXTURE_ROOTS = {'tex', 'tld4', 'TEX', 'TEXS', 'TLD', 'TLD4', 'TLD4S', 'TLDS'}


def blank(text: str) -> str:
    return ''.join('\n' if char == '\n' else ' ' for char in text)


def strip_noncode(text: str) -> str:
    """Keep byte offsets/line numbers while removing strings and both comments."""
    pattern = r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/'
    return re.sub(pattern, lambda match: blank(match.group()), text)


def line_number(text: str, offset: int) -> int:
    return text.count('\n', 0, offset) + 1


def violation(kind: str, function: str, line: int, opcode: str, detail: str) -> dict:
    return {'kind': kind, 'function': function, 'line': line, 'opcode': opcode, 'detail': detail}


def balanced_end(text: str, begin: int, opening: str, closing: str) -> int:
    depth = 0
    for offset in range(begin, len(text)):
        if text[offset] == opening:
            depth += 1
        elif text[offset] == closing:
            depth -= 1
            if depth == 0:
                return offset
    raise ValueError(f'Unclosed {opening!r} at line {line_number(text, begin)}')


def functions_in_ptx(clean: str) -> tuple[list[dict], list[dict]]:
    definitions, declarations = [], []
    position = 0
    while match := re.search(r'\.(entry|func)\b', clean[position:]):
        begin = position + match.start()
        cursor = position + match.end()
        kind = match.group(1)
        while cursor < len(clean) and clean[cursor].isspace():
            cursor += 1
        if cursor < len(clean) and clean[cursor] == '(':
            cursor = balanced_end(clean, cursor, '(', ')') + 1
        name_match = re.match(r'\s*([A-Za-z_$][\w.$]*)\s*\(', clean[cursor:])
        if not name_match:
            raise ValueError(f'Cannot parse .{kind} header at line {line_number(clean, begin)}')
        name = name_match.group(1)
        params_begin = cursor + name_match.end() - 1
        params_end = balanced_end(clean, params_begin, '(', ')')
        terminator = re.search(r'[;{]', clean[params_end + 1:])
        if not terminator:
            raise ValueError(f'Function {name} has no body or declaration terminator')
        body_begin = params_end + 1 + terminator.start()
        record = {'name': name, 'kind': kind, 'line': line_number(clean, begin)}
        if clean[body_begin] == ';':
            declarations.append(record)
            position = body_begin + 1
            continue
        body_end = balanced_end(clean, body_begin, '{', '}')
        record.update({'body_begin': body_begin + 1, 'body_end': body_end})
        definitions.append(record)
        position = body_end + 1
    return definitions, declarations


def floating_opcode_types(opcode: str) -> list[str]:
    # Splitting both dot and namespace separators covers .kind::f16 forms.
    parts = set(re.split(r'[.:]+', opcode.lower()))
    return sorted(token for token in parts
                  if token in FLOAT_TYPES or re.fullmatch(FLOAT_TYPE_PATTERN, token))


def ptx_statements(clean: str, function: dict) -> tuple[list[dict], list[dict]]:
    body_begin = function['body_begin']
    body = clean[body_begin:function['body_end']]
    # Declarations are data, not executable opcodes. Skip them without losing
    # source offsets. .loc has no semicolon; .pragma does have one.
    body = re.sub(r'(?<![\w.])\.(?:reg|local|shared|param|const|global|pragma)\b[^;]*;',
                  lambda match: blank(match.group()), body)
    body = re.sub(r'(?m)^[ \t]*\.(?:loc|file)\b[^\n]*',
                  lambda match: blank(match.group()), body)
    body = re.sub(r'(?<![\w%.])[$A-Za-z_][\w.$]*:(?!:)\s*',
                  lambda match: blank(match.group()), body)
    statements, errors = [], []
    cursor = 0
    for terminator in re.finditer(';', body):
        fragment = body[cursor:terminator.start()]
        start = re.search(r'[^\s{}]', fragment)
        if start:
            offset = cursor + start.start()
            code = fragment[start.start():].strip()
            match = re.match(r'(?:@!?%?[\w.$]+\s+)?([A-Za-z][\w.:]*)(?:\s+(.*))?$', code, re.S)
            source_line = line_number(clean, body_begin + offset)
            if match:
                statements.append({'opcode': match.group(1), 'operands': (match.group(2) or '').strip(),
                                   'line': source_line, 'function': function['name']})
            else:
                errors.append(violation('unparsed_statement', function['name'], source_line,
                                        '', code[:300]))
        cursor = terminator.end()
    tail = body[cursor:].strip(' \t\r\n{}')
    if tail:
        errors.append(violation('unterminated_statement', function['name'],
                                line_number(clean, body_begin + cursor), '', tail[:300]))
    return statements, errors


def call_target(operands: str) -> str | None:
    arguments = operands.lstrip()
    if arguments.startswith('('):
        try:
            arguments = arguments[balanced_end(arguments, 0, '(', ')') + 1:].lstrip()
        except ValueError:
            return None
        if not arguments.startswith(','):
            return None
        arguments = arguments[1:].lstrip()
    target = re.match(r'([A-Za-z_$][\w.$]*)(?:\s*,|\s*$)', arguments)
    return target.group(1) if target else None


def audit_ptx(text: str, required_entries: list[str] | None = None,
              allow_native_unorm_boundary: bool = False) -> dict:
    clean = strip_noncode(text)
    errors, statements, functions, declarations = [], [], [], []
    try:
        functions, declarations = functions_in_ptx(clean)
        for function in functions:
            parsed, invalid = ptx_statements(clean, function)
            statements.extend(parsed)
            errors.extend(invalid)
    except ValueError as exc:
        errors.append(violation('parse_error', '', 0, '', str(exc)))
    names = {function['name'] for function in functions}
    entries = [function['name'] for function in functions if function['kind'] == 'entry']
    if not entries:
        errors.append(violation('missing_entry', '', 0, '', 'No defined .entry kernels were found'))
    for required in required_entries or []:
        if not any(required in name for name in entries):
            errors.append(violation('missing_required_entry', '', 0, '', required))
    if not statements:
        errors.append(violation('no_instructions', '', 0, '', 'No executable PTX instructions were parsed'))
    counts = Counter()
    per_function = {name: Counter() for name in names}
    calls, textures, permitted_boundary = [], [], []
    for instruction in statements:
        opcode = instruction['opcode']
        root = opcode.split('.')[0]
        counts[opcode] += 1
        per_function[instruction['function']][opcode] += 1
        types = floating_opcode_types(opcode)
        native_boundary = (allow_native_unorm_boundary and types == ['f32']
                           and root in {'tex', 'tld4', 'mov', 'ld', 'st'})
        if native_boundary:
            permitted_boundary.append({**instruction,
                'boundary_kind': 'native_sampler' if root in {'tex', 'tld4'} else 'bit_representation_transfer'})
        elif types or root in PTX_FLOAT_ONLY_ROOTS:
            errors.append(violation('floating_instruction', instruction['function'], instruction['line'],
                                    opcode, f'Floating opcode types {types}' if types else 'Floating-only opcode'))
        elif root not in PTX_ROOTS:
            errors.append(violation('unknown_opcode', instruction['function'], instruction['line'],
                                    opcode, 'Conservative audit does not classify this opcode'))
        if root == 'call':
            target = call_target(instruction['operands'])
            calls.append({**instruction, 'target': target, 'resolved': target in names})
            if target not in names:
                errors.append(violation('unresolved_call', instruction['function'], instruction['line'],
                                        opcode, target or 'Indirect or unparseable call target'))
        if root in TEXTURE_ROOTS:
            textures.append({**instruction, 'floating_types': types})
    function_reports = []
    for function in functions:
        counter = per_function[function['name']]
        function_reports.append({key: value for key, value in function.items()
                                 if key not in ('body_begin', 'body_end')} |
                                {'instruction_count': sum(counter.values()), 'opcode_counts': dict(sorted(counter.items()))})
    return {
        'format': 'PTX', 'status': 'passed' if not errors else 'failed',
        'scope': 'All defined entries and device functions, including unreachable functions',
        'ptx_version': (re.search(r'(?m)^\s*\.version\s+([^\n]+)', clean).group(1).strip()
                        if re.search(r'(?m)^\s*\.version\s+([^\n]+)', clean) else None),
        'entries': entries, 'functions': function_reports, 'declarations': declarations,
        'instruction_count': sum(counts.values()), 'opcode_counts': dict(sorted(counts.items())),
        'calls': calls, 'texture_instructions': textures, 'violations': errors,
        'native_unorm_boundary_permitted': allow_native_unorm_boundary,
        'permitted_boundary_instructions': permitted_boundary,
        'forbidden_instruction_count': sum(error['kind'] == 'floating_instruction' for error in errors),
    }


def audit_sass(text: str, allow_constant_materialization: bool = False) -> dict:
    """Parse cuobjdump --dump-sass text, retaining function and source line."""
    clean = strip_noncode(text)
    function = None
    counts, per_function = Counter(), {}
    errors, textures, constants = [], [], []
    for number, line in enumerate(clean.splitlines(), 1):
        header = re.search(r'\bFunction\s*:\s*(\S+)', line)
        if header:
            function = header.group(1)
            per_function.setdefault(function, Counter())
            continue
        if ';' not in line:
            continue
        if function is None:
            errors.append(violation('unscoped_sass', '', number, '', line.strip()[:300]))
            continue
        code = line.split(';', 1)[0].strip()
        if not code or code.startswith('.'):
            continue
        match = re.match(r'(?:@!?[A-Z0-9]+\s+)?([A-Z][A-Za-z0-9_.:]*)(?:\s+(.*))?$', code)
        if not match:
            errors.append(violation('unparsed_sass', function, number, '', code[:300]))
            continue
        opcode = match.group(1)
        root = opcode.split('.')[0]
        counts[opcode] += 1
        per_function[function][opcode] += 1
        # ptxas on sm_120 uses HFMA2 dst,-RZ,RZ,imm,imm to materialize
        # constant bit patterns on a spare issue pipe. Admit ONLY this form,
        # with literal finite immediates and no state-dependent source operand.
        operands = re.split(r'\s+[?&]', match.group(2) or '', maxsplit=1)[0].strip()
        literal = r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'
        constant_form = opcode == 'HFMA2' and re.fullmatch(
            rf'R\d+,\s*-RZ,\s*RZ,\s*{literal}\s*,\s*{literal}', operands)
        if allow_constant_materialization and constant_form:
            constants.append({'function': function, 'line': number, 'opcode': opcode,
                              'operands': operands, 'note': 'Floating instruction used solely to materialize constants; no evolving data operand'})
        elif root in SASS_FLOAT_ROOTS or floating_opcode_types(opcode):
            errors.append(violation('floating_instruction', function, number, opcode,
                                    'Floating arithmetic, comparison, conversion or matrix opcode'))
        elif root not in SASS_INTEGER_ROOTS:
            errors.append(violation('unknown_opcode', function, number, opcode,
                                    'Conservative audit does not classify this SASS opcode'))
        if root in TEXTURE_ROOTS:
            textures.append({'function': function, 'line': number, 'opcode': opcode,
                             'note': 'Sampler result/coordinate type must be corroborated by matching PTX and resource configuration'})
    if not counts:
        errors.append(violation('no_instructions', '', 0, '', 'No cuobjdump SASS instructions were parsed'))
    return {
        'format': 'cuobjdump SASS', 'status': 'passed' if not errors else 'failed',
        'scope': 'All functions in supplied disassembly; texture types require PTX corroboration',
        'instruction_count': sum(counts.values()), 'opcode_counts': dict(sorted(counts.items())),
        'functions': [{'name': name, 'instruction_count': sum(counter.values()),
                       'opcode_counts': dict(sorted(counter.items()))} for name, counter in per_function.items()],
        'texture_instructions': textures, 'violations': errors,
        'constant_materialization_permitted': allow_constant_materialization,
        'constant_materialization_instructions': constants,
        'forbidden_instruction_count': sum(error['kind'] == 'floating_instruction' for error in errors),
    }


def file_record(path: Path) -> dict:
    data = path.read_bytes()
    return {'path': str(path.resolve()), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('ptx', type=Path)
    parser.add_argument('--sass', type=Path, help='Optional cuobjdump --dump-sass output from the matching executable')
    parser.add_argument('--require-entry', action='append', default=[],
                        help='Require an entry name containing this fragment; repeat for init/evolve/commit/etc.')
    parser.add_argument('--allow-native-unorm-boundary', action='store_true',
                        help='Permit/report f32 native texture boundaries and mov/ld/st bit transfers, but no floating arithmetic')
    parser.add_argument('--allow-constant-materialization', action='store_true',
                        help='Permit/report only HFMA2 dst,-RZ,RZ,literal,literal constant construction in SASS')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    for path in (args.ptx, args.sass):
        if path is not None and not path.is_file():
            parser.error(f'Input does not exist: {path}')
    report = {
        'schema_version': 1, 'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'tool': file_record(Path(__file__)), 'instruction_references': SOURCES,
        'policy': {
            'floating_opcode_type_tokens': sorted(FLOAT_TYPES),
            'floating_opcode_type_pattern': FLOAT_TYPE_PATTERN,
            'ptx_floating_only_roots': sorted(PTX_FLOAT_ONLY_ROOTS),
            'sass_floating_roots': sorted(SASS_FLOAT_ROOTS),
            'unknown_opcode_action': 'fail', 'unresolved_ptx_call_action': 'fail',
            'floating_declarations_and_constants': 'not executable instructions; ignored',
            'native_unorm_boundary_permitted': args.allow_native_unorm_boundary,
            'constant_materialization_permitted': args.allow_constant_materialization,
            'permitted_boundary_roots_when_enabled': ['tex', 'tld4', 'mov', 'ld', 'st'],
        },
        'limitations': [
            'Static instruction audit is not numerical-correctness, physics, convergence or performance validation.',
            'Independent PTX/SASS inputs must originate from the same build; hashes record identity, not provenance.',
            'PTX-only success is not proof of integer-only machine instructions after ptxas lowering.',
            'Texture interpretation still requires resource configuration review; this tool does not inspect host descriptors.',
            'When permitted, native UNORM decoding and f32 texture coordinates/results remain a sampler boundary, not an all-bit-only hardware pipeline.',
            'Host code, driver internals and physical texture-unit implementation are outside the device-instruction claim.',
        ],
        'ptx_input': file_record(args.ptx),
        'ptx': audit_ptx(args.ptx.read_text(encoding='utf-8-sig', errors='strict'), args.require_entry,
                         args.allow_native_unorm_boundary),
    }
    if args.sass:
        report['sass_input'] = file_record(args.sass)
        report['sass'] = audit_sass(args.sass.read_text(encoding='utf-8-sig', errors='strict'), args.allow_constant_materialization)
    checks = [report['ptx']] + ([report['sass']] if args.sass else [])
    report['status'] = 'passed' if all(check['status'] == 'passed' for check in checks) else 'failed'
    report['claim'] = ('No forbidden floating arithmetic instructions found in supplied PTX and SASS'
                       if args.sass else 'No forbidden floating arithmetic instructions found in supplied PTX; SASS unverified')
    if args.allow_native_unorm_boundary:
        report['claim'] += '; native UNORM sampler and f32 bit-transfer boundary permitted'
    if args.allow_constant_materialization:
        report['claim'] += '; HFMA2 constant materialization permitted and counted, so this is not a zero-floating-opcode claim'
    if report['status'] != 'passed':
        report['claim'] = 'Integer execution audit failed; inspect every violation'
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'{report["status"]}: {args.out.resolve()}')
    for check in checks:
        print(f'{check["format"]}: {check["instruction_count"]} instructions, {len(check["violations"])} violations')
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
