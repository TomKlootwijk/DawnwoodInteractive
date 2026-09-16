import importlib.util
import json
import random
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

image = load('operator_image')
packing = load('packing')

class ToolTests(unittest.TestCase):
    def test_default_image_roundtrip(self):
        data = (ROOT / 'model/operators.bin').read_bytes()
        self.assertEqual(image.encode(image.decode(data)), data)

    def test_arbitrary_bits_roundtrip(self):
        r = random.Random(756)
        for _ in range(20):
            data = r.randbytes(1984)
            self.assertEqual(image.encode(image.decode(data)), data)

    def test_bad_length(self):
        with self.assertRaises(ValueError):
            image.decode(bytes(32))

    def test_named_edit_changes_instruction_word(self):
        document = image.decode((ROOT / 'model/operators.bin').read_bytes())
        before = image.encode(document)
        document['operators'][1]['body'][0]['op'] = 'XOR'
        after = image.encode(document)
        self.assertNotEqual(before, after)
        self.assertEqual(len(after), 1984)

    def test_operand_range(self):
        document = image.decode((ROOT / 'model/operators.bin').read_bytes())
        document['operators'][0]['body'][0]['a'] = 8
        with self.assertRaises(ValueError):
            image.encode(document)

    def test_json_matches_binary(self):
        document = json.loads((ROOT / 'model/operators.json').read_text())
        self.assertEqual(image.encode(document), (ROOT / 'model/operators.bin').read_bytes())

    def test_bc5_page_bytes(self):
        p = packing.plan(11264, 512, .96, 4096, 'bc5')
        self.assertEqual(p['texture_bytes_per_page'], 16 * 2**20)
        self.assertEqual(p['aux_bytes_per_page'], 8 * 2**20)
        self.assertLessEqual(p['payload_bytes'], p['budget_bytes'])

    def test_exact_page_bytes(self):
        p = packing.plan(11264, 512, .96, 4096, 'rg8')
        self.assertEqual(p['texture_bytes_per_page'], 32 * 2**20)
        self.assertEqual(p['aux_bytes_per_page'], 8 * 2**20)

    def test_maximum_fill_is_not_disabled(self):
        p = packing.plan(12288, 0, 1, 4096, 'bc5')
        self.assertEqual(p['budget_bytes'], 12 * 2**30)
        self.assertEqual(p['pages_before_array_padding'], 511)

    def test_complete_sweep_rounding(self):
        p = packing.plan(11264, 512, .96, 4096, 'bc5', 65536)
        self.assertEqual(p['intervals_to_visit_every_block_once'], p['pages_before_array_padding'] * 16)

if __name__ == '__main__':
    unittest.main(verbosity=2)
