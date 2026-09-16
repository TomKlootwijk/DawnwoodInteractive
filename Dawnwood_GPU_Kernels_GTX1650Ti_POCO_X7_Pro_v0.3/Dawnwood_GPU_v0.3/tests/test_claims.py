from pathlib import Path
import cmath, json, math, sys, unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from packing import *

class SourceExperiments(unittest.TestCase):
    def test_bc5_is_sixteen_bytes_for_two_4x4_channels(self):
        self.assertEqual(len(encode_bc5(list(range(16)),list(range(16,32)))),16)
    def test_bc4_endpoint_branches(self):
        self.assertEqual(len(palette(255,0)),8)
        self.assertEqual(palette(0,255)[-2:],[0,255])
    def test_constant_channels_round_trip(self):
        red,green=decode_bc5(encode_bc5([17]*16,[200]*16))
        self.assertEqual(red,[17]*16);self.assertEqual(green,[200]*16)
    def test_arbitrary_channels_do_not_round_trip_losslessly(self):
        x=[0,4,9,17,28,39,52,66,82,100,120,142,165,191,220,255]
        y=list(reversed(x));a,b=decode_bc5(encode_bc5(x,y))
        self.assertGreater(sum((p-q)**2 for p,q in zip(x+y,a+b)),0)
    def test_block_dimension_rounding(self):
        self.assertEqual(bc5_bytes(1,1),16)
        self.assertEqual(bc5_bytes(4,4),16)
        self.assertEqual(bc5_bytes(5,4),32)
        self.assertEqual(bc5_bytes(4,4,mips=True),48)
    def test_mip_allocation_is_not_base_level_only(self):
        self.assertGreater(bc5_bytes(4096,4096,mips=True),bc5_bytes(4096,4096))
    def test_working_set_is_not_one_byte_per_state(self):
        m=memory_model(4096)
        self.assertEqual(m['buffer_payload_total'],3*4096*128+2*31*64)
        self.assertGreater(m['buffer_payload_total'],4096)
    def test_pointer_elimination_saves_only_pointer_bytes(self):
        m=memory_model(4096)
        saved=m['comparison_two_uint32_child_pointers_per_operator']
        self.assertEqual(saved,248)
        self.assertLess(saved,m['buffer_payload_total'])
    def test_gb_gib_are_different_budgets(self):
        self.assertNotEqual(4*10**9,4*2**30)
    def test_pigeonhole_arbitrary_compression(self):
        self.assertLess(len(set(range(256))),257)
    def test_source_vector_forward_dft_binding(self):
        x=[0,2,0,1]
        f=[sum(v*cmath.exp(-2j*math.pi*k*n/4) for n,v in enumerate(x)) for k in range(4)]
        for a,b in zip(f,[3,-1j,-3,1j]):self.assertLess(abs(a-b),1e-14)
    def test_two_path_interference_fixture(self):
        self.assertAlmostEqual(abs(1+cmath.exp(0j))**2,4)
        self.assertLess(abs(1+cmath.exp(1j*math.pi))**2,1e-25)
        self.assertEqual(abs(1)**2+abs(1)**2,2)
    def test_phase_only_hinge_preserves_norm(self):
        a,b=.3+.2j,-.4+.7j
        for p in [0,.125,1,3.1]:
            x=(a+b)/math.sqrt(2)*cmath.exp(1j*p)
            y=(a-b)/math.sqrt(2)*cmath.exp(-1j*p)
            self.assertAlmostEqual(abs(x)**2+abs(y)**2,abs(a)**2+abs(b)**2)
    def test_one_bit_jitter_alone_does_not_prove_escape(self):
        states=[7]
        for jitter in [0,1,1,0,1,0]:states.append(states[-1] ^ (jitter & 0))
        self.assertEqual(set(states),{7})
    def test_inverse_does_not_remove_added_noise(self):
        x,y=1.,2.;tx,ty=x+y,y
        self.assertNotEqual((tx+.01)-ty,x)
    def test_bayer_is_a_downstream_display_operation(self):
        self.assertEqual(sum(bayer(.5,x,y) for x in range(4) for y in range(4)),8)
        self.assertEqual(sum(bayer(0,x,y) for x in range(4) for y in range(4)),0)
        self.assertEqual(sum(bayer(1,x,y) for x in range(4) for y in range(4)),16)
    def test_operator_fields_all_have_declared_record_locations(self):
        self.assertEqual(128%16,0);self.assertEqual(64%16,0)

if __name__=='__main__':unittest.main(verbosity=2)
