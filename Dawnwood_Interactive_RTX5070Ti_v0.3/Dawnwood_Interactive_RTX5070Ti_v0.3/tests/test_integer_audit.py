"""Adversarial offline fixtures for device-instruction claims; no GPU is used."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('verify_integer_device_code', ROOT / 'tools' / 'verify_integer_device_code.py')
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def kernel(body, name='integer_evolve'):
    return '.version 8.7\n.target sm_120\n.address_size 64\n.visible .entry ' + name + '()\n{\n' + body + '\n}\n'


class IntegerAuditTests(unittest.TestCase):
    def test_integer_memory_pointer_and_texture_instructions_pass(self):
        result = AUDIT.audit_ptx(kernel('''
            .reg .b32 %r<5>;
            .reg .b64 %rd<4>;
            ld.param.u64 %rd1, [pointer];
            cvta.to.global.u64 %rd2, %rd1;
            cvt.u64.u32 %rd3, %r0;
            tex.2d.v4.u32.s32 {%r1, %r2, %r3, %r4}, [tex, {%r0, %r0}];
            mul.wide.u32 %rd3, %r1, 16;
            add.u64 %rd2, %rd2, %rd3;
            st.global.u32 [%rd2], %r4;
            ret;
        '''), ['evolve'])
        self.assertEqual(result['status'], 'passed', result['violations'])
        self.assertEqual(result['instruction_count'], 8)
        self.assertEqual(len(result['texture_instructions']), 1)

    def test_comments_declarations_names_and_constants_are_not_float_opcodes(self):
        result = AUDIT.audit_ptx(kernel('''
            .reg .f32 %f<5>;
            // fma.rn.f32 %f1, %f2, %f3, %f4;
            /* ex2.approx.f32 %f1, %f2; */
            .loc 1 99 0
            .pragma "add.f32 is text, not code";
        label_f32:
            mov.b32 %r1, 0f3F800000; add.u32 %r2, %r1, 0xF32;
            ret;
        ''', 'float_f32_name_is_not_an_opcode'))
        self.assertEqual(result['status'], 'passed', result['violations'])
        self.assertEqual(result['instruction_count'], 3)

    def test_float_arithmetic_conversion_comparison_sfu_matrix_and_texture_fail(self):
        opcodes = [
            'add.f32', 'fma.rn.f64', 'cvt.rzi.u32.f32', 'setp.nan.f32',
            'ex2.approx.f32', 'sqrt.approx.f32', 'add.bf16x2', 'cvt.e4m3x2.f32',
            'mma.sync.aligned.m16n8k16.row.col.f32.f16.f16.f32',
            'tex.2d.v4.f32.s32', 'tex.2d.v4.u32.f32', 'add.f128',
        ]
        for opcode in opcodes:
            with self.subTest(opcode=opcode):
                result = AUDIT.audit_ptx(kernel(opcode + ' %r1, %r2;\nret;'))
                self.assertEqual(result['status'], 'failed')
                forbidden = [entry for entry in result['violations'] if entry['kind'] == 'floating_instruction']
                self.assertEqual(len(forbidden), 1)
                self.assertEqual(forbidden[0]['opcode'], opcode)
                self.assertEqual(forbidden[0]['line'], 6)

    def test_native_sampler_boundary_is_explicit_and_narrow(self):
        code = kernel('''
            mov.f32 %f1, %f2;
            ld.param.f32 %f2, [coords];
            tex.2d.v4.f32.f32 {%f1,%f2,%f3,%f4}, [tex, {%f5,%f6}];
            tex.2d.v4.u32.f32 {%r1,%r2,%r3,%r4}, [rawtex, {%f5,%f6}];
            st.local.f32 [transfer], %f1;
            ret;
        ''')
        self.assertEqual(AUDIT.audit_ptx(code)['status'], 'failed')
        allowed = AUDIT.audit_ptx(code, allow_native_unorm_boundary=True)
        self.assertEqual(allowed['status'], 'passed', allowed['violations'])
        self.assertEqual(len(allowed['permitted_boundary_instructions']), 5)
        for forbidden in ('cvt.u32.f32', 'mul.f32', 'setp.eq.f32', 'ex2.approx.f32', 'mov.f64'):
            result = AUDIT.audit_ptx(kernel(forbidden + ' %r1, %r2;'), allow_native_unorm_boundary=True)
            self.assertEqual(result['status'], 'failed', forbidden)

    def test_all_defined_functions_are_scanned_even_when_unreachable(self):
        code = kernel('ret;') + '.func unused_float_helper() { add.f32 %f1, %f2, %f3; ret; }\n'
        result = AUDIT.audit_ptx(code)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['violations'][0]['function'], 'unused_float_helper')

    def test_direct_integer_helper_call_resolves(self):
        helper = '.func (.param .b32 retval) helper(.param .b32 input) { .reg .b32 %r; ld.param.u32 %r, [input]; ret; }\n'
        result = AUDIT.audit_ptx(helper + kernel('call.uni (result), helper, (input); ret;'))
        self.assertEqual(result['status'], 'passed', result['violations'])
        self.assertTrue(result['calls'][0]['resolved'])
        self.assertEqual(result['calls'][0]['target'], 'helper')

    def test_external_and_indirect_calls_fail_conservatively(self):
        for call in ('call.uni (result), __nv_sin, (input);', 'call %rd1, (input);'):
            code = '.extern .func (.param .b32 retval) __nv_sin(.param .b32 arg);\n' + kernel(call + ' ret;')
            result = AUDIT.audit_ptx(code)
            self.assertEqual(result['status'], 'failed')
            self.assertTrue(any(error['kind'] == 'unresolved_call' for error in result['violations']))

    def test_required_entries_unknown_opcode_and_invalid_input_fail(self):
        cases = [('', []), (kernel('future.unknown %r1; ret;'), []),
                 (kernel('ret;'), ['initialize']), (kernel('ret;')[:-3], []),
                 (kernel('!invalid statement; ret;'), [])]
        for code, required in cases:
            with self.subTest(code=code):
                self.assertEqual(AUDIT.audit_ptx(code, required)['status'], 'failed')

    def test_sass_integer_names_are_not_mistaken_for_floating(self):
        code = '''
            Function : integer_evolve
            /*0000*/ MOV R1, c[0x0][0x28]; /* 0x000f0000 */
            /*0010*/ FLO.U32 R2, R3;
            /*0020*/ @!P0 IMAD.WIDE.U32 R4, R2, R3, R4;
            /*0030*/ FENCE.SC.GPU;
            /*0040*/ I2I.U32.U16 R2, R4;
            /*0050*/ TEX.NODEP.LZ R4, R2, R3, R4, 2D;
            /*0060*/ EXIT;
        '''
        result = AUDIT.audit_sass(code)
        self.assertEqual(result['status'], 'passed', result['violations'])
        self.assertEqual(result['instruction_count'], 7)
        self.assertEqual(len(result['texture_instructions']), 1)

    def test_sass_float_and_unknown_opcodes_fail(self):
        for opcode in ('FADD', 'FSETP', 'MUFU.RCP', 'UI2F', 'F2I', 'HMMA', 'VHMNMX', 'FUTURE'):
            with self.subTest(opcode=opcode):
                result = AUDIT.audit_sass('Function : integer_evolve\n/*0000*/ ' + opcode + ' R0, R1;\n')
                self.assertEqual(result['status'], 'failed')
                self.assertEqual(result['violations'][0]['opcode'], opcode)

    def test_integer_ptx_with_float_sass_lowering_fails_final_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            ptx, sass, output = folder/'input.ptx', folder/'input.sass', folder/'audit.json'
            ptx.write_text(kernel('div.u32 %r1, %r2, %r3; ret;'), encoding='utf-8')
            sass.write_text('Function : integer_evolve\n/*0000*/ MUFU.RCP R1, R2;\n/*0010*/ EXIT;\n', encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()):
                code = AUDIT.main([str(ptx), '--sass', str(sass), '--require-entry', 'evolve', '--out', str(output)])
            report = json.loads(output.read_text(encoding='utf-8'))
        self.assertEqual(code, 1)
        self.assertEqual(report['ptx']['status'], 'passed')
        self.assertEqual(report['sass']['status'], 'failed')
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(len(report['ptx_input']['sha256']), 64)
        self.assertIn('audit failed', report['claim'])

    def test_constant_materialization_is_narrow_and_reported(self):
        prefix = 'Function : integer_evolve\n/*0000*/ '
        const = 'HFMA2 R11, -RZ, RZ, 0, 5.9604644775390625e-08 ?trans1;'
        self.assertEqual(AUDIT.audit_sass(prefix + const)['status'], 'failed')
        result = AUDIT.audit_sass(prefix + const, True)
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(len(result['constant_materialization_instructions']), 1)
        for bad in ('HFMA2 R11, -RZ, R1, 0, 0;', 'HFMA2 R11, R1, RZ, 0, 0;',
                    'HFMA2 R11, -RZ, RZ, R2, 0;', 'HFMA2 R11, -RZ, RZ, 0, nan;',
                    'HFMA2.SAT R11, -RZ, RZ, 0, 0;'):
            self.assertEqual(AUDIT.audit_sass(prefix + bad, True)['status'], 'failed')

    def test_blackwell_integer_vector_and_control_opcodes(self):
        code = 'Function : integer_evolve\n' + '\n'.join([
            'LDCU.64 UR4, c[0][0];', 'BMOV.32.CLEAR R4, B0;',
            'BREAK.RELIABLE B0;', 'REDG.E.ADD.64.STRONG.GPU [R4], R6;',
            'VIMNMX.U16x2 R4, R5, R6, PT;'])
        self.assertEqual(AUDIT.audit_sass(code)['status'], 'passed')


if __name__ == '__main__':
    unittest.main(verbosity=2)
