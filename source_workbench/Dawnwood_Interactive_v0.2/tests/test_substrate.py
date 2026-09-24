from pathlib import Path
import copy
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from dawnwood.terms import Graph, Ref
from dawnwood.native import bit, parity, even_odd, child, route
from dawnwood.kernel import Kernel

MODEL = json.loads((ROOT/'model/substrate.json').read_text())
CYCLE = json.loads((ROOT/'model/cycle.json').read_text())

def new_kernel():
    return Kernel(copy.deepcopy(MODEL), copy.deepcopy(CYCLE))

def ancestors(graph, root):
    visited, pending = set(), [root.id]
    while pending:
        idx = pending.pop()
        if idx not in visited:
            visited.add(idx)
            pending.extend(graph.nodes[idx].get('args', []))
    return visited

class NativeRelations(unittest.TestCase):
    def test_source_parity(self):
        self.assertEqual((parity(7), parity(54)), (1, 0))
    def test_source_even_odd(self):
        self.assertEqual((even_odd(7), even_odd(54)), (1, 0))
    def test_two_named_relations(self):
        self.assertEqual((parity(3), even_odd(3)), (0, 1))
    def test_source_child_formula(self):
        self.assertEqual((child(0,0), child(0,1), child(12,0), child(12,1)), (1,2,25,26))
    def test_route_and_reversal(self):
        self.assertEqual(route([0,1]), (4,[0,1,4]))
        self.assertEqual(route([0,1],1), (5,[0,2,5]))
    def test_root(self):
        self.assertEqual(route([]), (0,[0]))
    def test_large_integer_index(self):
        i=2**160
        self.assertEqual(child(i,1), 2*i+2)
    def test_deep_route(self):
        self.assertEqual(route([1]*130)[0], 2**131-2)
    def test_bit_type(self):
        for value in [-1,2,1.5,True]:
            with self.assertRaises(ValueError): bit(value)

class ExpressionGraph(unittest.TestCase):
    def test_literal_interning(self):
        g=Graph();self.assertEqual(g.literal([0,2,0,1]),g.literal([0,2,0,1]))
    def test_literal_ownership(self):
        g=Graph();value={'a':[1]};ref=g.literal(value);value['a'].append(2)
        self.assertEqual(g.nodes[ref.id]['value'],{'a':[1]})
    def test_symbol_interning(self):
        g=Graph();self.assertEqual(g.symbol('PSI'),g.symbol('PSI'))
    def test_call_interning(self):
        g=Graph();x=g.symbol('X');self.assertEqual(g.call('F',x),g.call('F',x))
    def test_content_identity(self):
        a,b=Graph(),Graph();x=a.symbol('X');b.symbol('Unused');y=b.symbol('X')
        self.assertEqual(a.digest(a.call('F',x)), b.digest(b.call('F',y)))
    def test_graph_round_trip(self):
        g=Graph();ref=g.call('Field',g.literal([0,2,0,1]),g.symbol('PSI'))
        restored=Graph.from_json(g.to_json());self.assertEqual(restored.digest(ref),g.digest(ref))
    def test_graph_hash_check(self):
        g=Graph();g.symbol('PSI');rows=copy.deepcopy(g.to_json());rows[0]['name']='OTHER'
        with self.assertRaises(ValueError):Graph.from_json(rows)

class UnifiedCycle(unittest.TestCase):
    def test_source_seed(self):
        k=new_kernel();deps=ancestors(k.g,k.state)
        self.assertTrue(any(k.g.nodes[i].get('value')==[0,2,0,1] for i in deps))
    def test_full_catalogue(self):
        k=new_kernel();self.assertEqual(len(k.operators),31)
        self.assertEqual({o.index for o in k.operators.values()},set(range(31)))
    def test_operator_body_field_anchor_mutate_together(self):
        k=new_kernel();before={key:(o.body,o.field,o.anchor) for key,o in k.operators.items()}
        k.step(1,[0,1])
        for key,o in k.operators.items():
            self.assertNotEqual(before[key],(o.body,o.field,o.anchor))
            self.assertNotEqual(before[key][0],o.body)
            self.assertNotEqual(before[key][1],o.field)
            self.assertNotEqual(before[key][2],o.anchor)
    def test_operator_field_in_returned_state(self):
        k=new_kernel();k.step(1,[0,1]);deps=ancestors(k.g,k.state)
        self.assertIn(k.lut.id,deps)
        for o in k.operators.values():
            self.assertTrue({o.body.id,o.field.id,o.anchor.id,o.record.id}<=deps)
    def test_source_primitives_are_applied(self):
        k=new_kernel();k.step(1,[0,1])
        applications={n['args'][0] for n in k.g.nodes if n.get('head')=='Apply_SDF_operator'}
        for key in ('T_shape','pyramid','circle','cone','sphere','apex','delta_phi','blend','double_dot'):
            self.assertIn(k.operators[key].record.id,applications)
    def test_two_y_up_actions_in_fourth_slot(self):
        k=new_kernel();k.step(1,[0,1]);r=k.operators['y_up'].record.id
        uses=[n for n in k.g.nodes if n.get('head')=='Apply_SDF_operator' and n['args'][0]==r]
        self.assertEqual(len(uses),2)
        self.assertEqual(uses[1]['args'][1],uses[0]['id'])
    def test_inverse_T_in_state(self):
        k=new_kernel();k.step(1,[0,1]);r=k.operators['inverse_T'].record.id
        deps=ancestors(k.g,k.state)
        uses=[n for n in k.g.nodes if n.get('head')=='Apply_SDF_operator' and n['args'][0]==r]
        self.assertEqual(len(uses),1);self.assertIn(uses[0]['id'],deps)
    def test_inverse_role_is_editable(self):
        model=copy.deepcopy(MODEL);model['symbols']['T_inverse_role']='time';k=Kernel(model)
        k.step(1,[0,1]);self.assertTrue(any(n.get('head')=='T_time' for n in k.g.nodes))
    def test_history_contains_previous_history(self):
        k=new_kernel();old=k.B;k.step(1,[0,1]);self.assertIn(old.id,ancestors(k.g,k.B))
    def test_feedback_is_whole_returned_state(self):
        k=new_kernel();a=k.step(0,[0,1]);old=k.state;b=k.step(1,[0,1])
        self.assertEqual(a['state_after_sha256'],b['state_before_sha256'])
        self.assertIn(old.id,ancestors(k.g,k.operators['double_dot'].body))
        self.assertEqual(k.feedback,k.state)
    def test_route_selects_current_record(self):
        k=new_kernel();r=k.step(1,[0,1]);self.assertEqual(r['selected_index'],4)
        self.assertEqual(r['selected_key'],'phyllotaxis')
    def test_reversal_changes_route(self):
        k=new_kernel();r=k.step(1,[0,1],1);self.assertEqual(r['implicit_path'],[0,2,5])
    def test_unbound_address_remains_named(self):
        k=new_kernel();r=k.step(1,[1]*70)
        self.assertEqual(r['selected_index'],2**71-2)
        self.assertTrue(any(n.get('head')=='LUT_read' for n in k.g.nodes))
    def test_bayer_is_downstream(self):
        a,b=new_kernel(),new_kernel()
        for j in [0,1,1,0]:
            ra=a.step(j,[0,1],bayer=False);rb=b.step(j,[0,1],bayer=True)
            self.assertEqual(ra['state_after_sha256'],rb['state_after_sha256'])
            self.assertIsNotNone(rb['readout_ref'])
            self.assertNotIn(rb['readout_ref'],ancestors(b.g,b.state))
    def test_live_body_edit_changes_returned_state(self):
        a,b=new_kernel(),new_kernel();b.set_body('double_dot',{'symbol':'edited_body','x':[1,2,3]})
        self.assertNotEqual(a.step(1,[0,1])['state_after_sha256'],b.step(1,[0,1])['state_after_sha256'])
    def test_arbitrary_operator_body_and_large_address(self):
        k=new_kernel();o=k.add_operator('extra','Extra',{'call':'my_field','args':['anything']},2**100)
        old=o.body;k.step(1,[0,1]);self.assertNotEqual(old,k.operators['extra'].body)
        self.assertEqual(o.index,2**100)
    def test_snapshot_continue(self):
        a=new_kernel();a.step(0,[0,1]);a.step(1,[0,1],1)
        b=Kernel.from_snapshot(json.loads(json.dumps(a.snapshot())))
        self.assertEqual(a.step(1,[0,1])['state_after_sha256'],b.step(1,[0,1])['state_after_sha256'])
    def test_addition_and_body_edit_survive_snapshot(self):
        a=new_kernel();a.add_operator('extra','Extra',{'symbol':'extra'});a.set_body('circle',{'symbol':'changed'})
        b=Kernel.from_snapshot(a.snapshot())
        self.assertEqual(a.step(1,[0,1])['state_after_sha256'],b.step(1,[0,1])['state_after_sha256'])
    def test_epoch_has_no_fixed_width_wrap(self):
        k=new_kernel();k.epoch=2**80;k.step(0,[]);self.assertEqual(k.epoch,2**80+1)
    def test_mutation_record_references_prior_field(self):
        k=new_kernel();old=k.operators['mutation'].record;k.step(1,[])
        for op in k.operators.values():self.assertIn(old.id,ancestors(k.g,op.body))

if __name__=='__main__':
    unittest.main()
