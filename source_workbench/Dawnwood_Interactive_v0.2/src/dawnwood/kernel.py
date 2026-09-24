"""One operator field, one recurrent state, one editable PSI circulation.

This workbench executes the source's named relationships as expression-DAG updates.
A body is editable JSON; its evolving SDF, surface position and use travel together.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .terms import Graph, Ref
from .native import bit, route

@dataclass
class Operator:
    index: int
    key: str
    label: str
    body: Ref
    field: Ref
    anchor: Ref
    record: Ref

class Kernel:
    PHASES = ('operator_mutation', 'log_polar', 'split_and_hinge', 'selected_operator',
              'rk4_four_slots', 'geometry_divergence', 'rgba_crystal', 'surface_return')

    def __init__(self, model: dict[str, Any], cycle: dict[str, Any] | None = None):
        self.model = model
        self.cycle = dict(cycle or {})
        self.phases = list(self.cycle.get('phases', self.PHASES))
        self.g = Graph()
        self.epoch = 0
        self.psi = self.g.symbol('PSI')
        self.K = self.g.symbol('Klein_surface')
        self.feedback = self.g.call('Source_wavefront_FT',
                                   self.g.literal(model['seed']['wavefront']))
        self.B = self.g.symbol('B_initial')
        self.operators: dict[str, Operator] = {}
        for item in model['operators']:
            self.add_operator(item['key'], item['label'], item['body'], item['index'],
                              item.get('field'), refresh=False)
        self.lut = self._lut()
        self.state = self.g.call('Substrate_state', self.K, self.feedback, self.lut, self.B)
        self.feedback = self.state

    def _record(self, key: str, body: Ref, field: Ref, anchor: Ref) -> Ref:
        return self.g.call('SDF_operator_record', self.g.literal(key), body, field, anchor)

    def _lut(self) -> Ref:
        entries = []
        for op in sorted(self.operators.values(), key=lambda x: x.index):
            entries.append(self.g.call('Implicit_entry', self.g.literal(op.index), op.record))
        return self.g.call('LUT_BST', *entries)

    def add_operator(self, key: str, label: str, body: Any, index: int | None = None,
                     field: Any = None, *, refresh: bool = True) -> Operator:
        if key in self.operators:
            raise ValueError(f'Operator {key!r} already exists; use set_body to edit it')
        occupied = {o.index for o in self.operators.values()}
        index = (max(occupied, default=-1) + 1) if index is None else index
        if type(index) is not int or index < 0 or index in occupied:
            raise ValueError('Choose an unused nonnegative implicit index')
        b = self.g.literal(body)
        anchor = self.g.call('Phyllotaxis_on_Klein', self.K, self.g.literal(index), self.psi)
        f = self.g.call('SDF_definition', self.g.literal(field), b, anchor, self.K)
        op = Operator(index, key, label, b, f, anchor, self._record(key, b, f, anchor))
        self.operators[key] = op
        if refresh:
            self.lut = self._lut()
        return op

    def set_body(self, key: str, expression: Any) -> None:
        """Replace a live operator body; subsequent circulation uses the new record."""
        op = self.operators[key]
        op.body = self.g.literal(expression)
        op.field = self.g.call('Rebind_SDF', op.field, op.body, op.anchor, self.K)
        op.record = self._record(key, op.body, op.field, op.anchor)
        self.lut = self._lut()

    def apply(self, key: str, *args: Ref) -> Ref:
        return self.g.call('Apply_SDF_operator', self.operators[key].record, *args)

    def _operator_mutation(self, c: dict) -> None:
        old_lut = self.lut
        mutation = self.operators['mutation'].record
        pinion = self.operators['pinion'].record
        for op in self.operators.values():
            body = self.g.call('Mutate_operator_body', mutation, op.body, op.field,
                               self.feedback, old_lut, c['jitter'], self.psi)
            anchor = self.g.call('Double_pinion_surface_position', pinion, self.K,
                                 op.anchor, self.feedback, c['jitter'], self.psi)
            field = self.g.call('Mutate_operator_SDF', op.field, body, anchor, self.K)
            op.body, op.anchor, op.field = body, anchor, field
            op.record = self._record(op.key, body, field, anchor)
        self.lut = self._lut()
        c['surface'] = self.apply('klein', self.K, self.lut, self.feedback)
        c['working'] = self.feedback

    def _log_polar(self, c: dict) -> None:
        c['encoded'] = self.apply('phi', c['working'], self.g.symbol('phi'), self.lut)

    def _split_and_hinge(self, c: dict) -> None:
        split = self.apply('split', c['encoded'], c['jitter'])
        c['parity'] = self.apply('parity', split, c['neck'])
        c['working'] = self.apply('hadamard', split, c['parity'], self.lut)

    def _selected_operator(self, c: dict) -> None:
        target, path = route(c['route_bits'], c['neck_bit'])
        by_index = {op.index: op for op in self.operators.values()}
        c['route_path'], c['selected_index'] = path, target
        routing = self.apply('bst', self.lut, self.g.literal(path), c['surface'], c['jitter'])
        if target in by_index:
            selected = by_index[target]
            c['selected_key'] = selected.key
            record = selected.record
        else:
            # Preserve a named address without aliasing it onto an occupied slot.
            c['selected_key'] = f'LUT[{target}]'
            record = self.g.call('LUT_read', self.lut, self.g.literal(target))
        c['working'] = self.g.call('Apply_SDF_operator', record, c['working'], routing)

    def _rk4_four_slots(self, c: dict) -> None:
        slots = [self.apply('rk4', self.g.literal(k), c['working'], self.psi, c['jitter'])
                 for k in (1, 2, 3, 4)]
        for _ in range(self.cycle.get('fourth_rk4_slot', {}).get('y_up_applications', 2)):
            slots[3] = self.apply('y_up', slots[3])
        c['slots'] = slots
        c['working'] = self.apply('rk4', *slots, self.psi)

    def _geometry_divergence(self, c: dict) -> None:
        primitives = [self.apply(k, c['working'], c['surface']) for k in
                      ('T_shape', 'pyramid', 'circle', 'cone', 'sphere', 'apex')]
        geometric_lut = self.g.call('Geometric_LUT', *primitives)
        delta = self.apply('delta_phi', c['encoded'], c['jitter'], self.psi)
        growth = self.apply('phyllotaxis', delta, geometric_lut, self.lut, self.psi)
        coupling = self.apply('double_dot', c['working'], growth, c['surface'])
        c['working'] = self.apply('blend', coupling, growth, geometric_lut)

    def _rgba_crystal(self, c: dict) -> None:
        crystal = self.apply('crystal', c['working'], self.lut)
        pair = self.apply('dichromatic', crystal, c['parity'])
        R = self.g.call('Channel_R', pair)
        G = self.g.call('Channel_G', pair)
        self.B = self.apply('phase_history', self.B, c['jitter'], *c['slots'])
        role = self.model.get('symbols', {}).get('T_inverse_role', 'transformation')
        T = (self.apply('T_transform', c['working'], crystal) if role == 'transformation'
             else self.g.call('T_' + role, c['working'], self.psi))
        A = self.apply('inverse_T', T)
        c['rgba'] = self.g.call('RGBA', R, G, self.B, A)
        c['working'] = c['rgba']

    def _surface_return(self, c: dict) -> None:
        carried = self.apply('pinion', c['surface'], c['working'], self.lut)
        returned = self.apply('return', carried, c['neck'], c['parity'], self.psi)
        self.state = self.g.call('Substrate_state', c['surface'], returned, self.lut, self.B)
        self.K, self.feedback = c['surface'], self.state

    def step(self, jitter: int, route_bits: list[int] | None = None,
             neck: int = 0, *, bayer: bool = False) -> dict[str, Any]:
        """Construct one complete cycle and update the live operator field."""
        jitter, neck = bit(jitter), bit(neck)
        bits = list(route_bits or [])
        for b in bits:
            bit(b)
        before = self.g.digest(self.state)
        c = {'jitter': self.g.literal(jitter), 'neck': self.g.literal(neck),
             'neck_bit': neck, 'route_bits': bits}
        for phase in self.phases:
            method = getattr(self, '_' + phase, None)
            if method is None:
                c['working'] = self.g.call(phase, c.get('working', self.feedback), self.lut)
            else:
                method(c)
        readout = self.apply('bayer', self.state) if bayer else None
        row = {'epoch': self.epoch, 'PSI': 'PSI', 'jitter': jitter, 'neck': neck,
               'route_bits': bits, 'implicit_path': c.get('route_path', []),
               'selected_key': c.get('selected_key'), 'selected_index': c.get('selected_index'),
               'state_before_sha256': before, 'state_after_sha256': self.g.digest(self.state),
               'state_ref': self.state.id, 'lut_ref': self.lut.id,
               'readout_ref': readout.id if readout else None,
               'operator_count': len(self.operators), 'expression_node_count': len(self.g.nodes)}
        self.epoch += 1
        return row

    def snapshot(self) -> dict[str, Any]:
        return {'format': 'dawnwood-symbolic-0.2', 'model': self.model, 'cycle': self.cycle, 'phases': self.phases,
                'epoch': self.epoch, 'refs': {k: getattr(self, k).id for k in
                                            ('psi', 'K', 'feedback', 'B', 'lut', 'state')},
                'operators': [{'index': o.index, 'key': o.key, 'label': o.label,
                               **{k: getattr(o, k).id for k in ('body', 'field', 'anchor', 'record')}}
                              for o in self.operators.values()], 'graph': self.g.to_json(),
                'state_sha256': self.g.digest(self.state)}

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> 'Kernel':
        if data['format'] != 'dawnwood-symbolic-0.2':
            raise ValueError('Snapshot format does not match this workbench')
        obj = cls.__new__(cls)
        obj.model, obj.phases, obj.epoch = data['model'], data['phases'], data['epoch']
        obj.cycle = data.get('cycle', {})
        obj.g = Graph.from_json(data['graph'])
        for key, value in data['refs'].items():
            setattr(obj, key, Ref(value))
        obj.operators = {}
        for row in data['operators']:
            op = Operator(row['index'], row['key'], row['label'],
                          *(Ref(row[k]) for k in ('body', 'field', 'anchor', 'record')))
            obj.operators[op.key] = op
        if obj.g.digest(obj.state) != data['state_sha256']:
            raise ValueError('State digest does not match snapshot')
        return obj
