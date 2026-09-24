"""Offline lift of validated resident plans into an editable named source graph.

Frame registers and argument packing are exporter implementation details. COPY
becomes an immutable value alias; record selectors, named call arguments and
returned fields become the graph. The runtime graph compiler must independently
lower this graph and must not use the original plans or their physical layout.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import struct

try:
    from . import source_ir_v2 as ir
    from . import source_resident_v2 as resident
    from . import source_graph_types as graph_types
except ImportError:
    import source_ir_v2 as ir
    import source_resident_v2 as resident
    import source_graph_types as graph_types


PROFILE = "DWI-SOURCE-GRAPH-0.1"
TYPE_PROFILE = "DWI-GRAPH-TYPES-0.1"
RECORD_HEADER = ("body", "field", "placement", "generation")
SLOTS = ("body", "field", "placement")


@dataclass
class _Value:
    reference: dict
    literal_types: set[str] = field(default_factory=set)


def _safe_name(value):
    return re.sub(r"[^A-Za-z0-9_]", "_", str(value))


class _Contracts:
    def __init__(self, definition):
        self.definition = definition
        self.states = graph_types.state_types(definition)
        self.record_fields = graph_types.record_types(definition)

    def helper(self, name):
        return graph_types.function_contract(self.definition, name)

    def record(self, key, slot, role):
        if key is not None:
            return graph_types.record_contract(self.definition, key, slot, role)
        contracts = [graph_types.record_contract(self.definition, record["key"], slot, role)
                     for record in self.definition["records"]]
        if not contracts or any(contract != contracts[0] for contract in contracts[1:]):
            raise ValueError("TARGET call lacks one common nominal contract across all records")
        return contracts[0]


class _Lift:
    def __init__(self, definition, mutation, contracts, phase_ranges=None):
        self.definition = definition
        self.mutation = mutation
        self.contracts = contracts
        self.functions = list(definition["functions"].items())
        self.records = definition["records"]
        self.families = definition["families"]
        self.state_names = definition["state_names"]
        self.record_names = [*RECORD_HEADER, *definition["record_value_names"]]
        if len(self.record_names) != resident.RECORD_WORDS or len(set(self.record_names)) != len(self.record_names):
            raise ValueError("Graph export requires 24 unique named record fields")
        self.frame = {}
        self.nodes = []
        self.phase_nodes = {name: [] for name, start, stop in (phase_ranges or [])}
        self.phase_ranges = phase_ranges or []
        self.returns = {}
        self.serial = 0
        self.literal_values = []

    def read(self, register, step):
        if type(register) is not int or register not in self.frame:
            raise ValueError(f"Plan step {step}: uninitialized frame read during graph export")
        return self.frame[register]

    def write(self, register, value, step):
        if type(register) is not int or not 0 <= register < resident.FRAME_WORDS:
            raise ValueError(f"Plan step {step}: frame destination is outside the resident limit")
        self.frame[register] = value

    def _phase(self, step):
        matches = [name for name, start, stop in self.phase_ranges if start <= step < stop]
        if len(matches) != 1:
            raise ValueError(f"Action step {step}: executable node is outside exactly one source phase")
        return matches[0]

    def emit(self, step, operation, label, payload, outputs):
        phase = "mutation" if self.mutation else self._phase(step)
        prefix = "mutation" if self.mutation else "action_" + _safe_name(phase)
        self.serial += 1
        identity = f"{prefix}_{_safe_name(label)}_{self.serial}"
        node = {"id": identity, "op": operation, **payload}
        if self.mutation:
            self.nodes.append(node)
        else:
            self.phase_nodes[phase].append(node)
        return [_Value({"node": identity, "output": name}) for name in outputs]

    def use(self, value, expected_type):
        if "literal" in value.reference:
            value.literal_types.add(expected_type)
        return value

    def selector(self, selector, dynamic, step):
        if dynamic:
            value = self.use(self.read(selector, step), self.contracts.states["selected_index"])
            return {"source_index": value}, None
        if selector == resident.TARGET:
            if not self.mutation:
                raise ValueError("TARGET record selector cannot appear in an action graph")
            return {"target": True}, None
        if type(selector) is not int or not 0 <= selector < len(self.records):
            raise ValueError(f"Plan step {step}: record ordinal is outside the definition")
        key = self.records[selector]["key"]
        return {"key": key}, key

    def binding_for_record(self, key, slot, role, signature):
        records = self.records if key is None else [record for record in self.records if record["key"] == key]
        candidates = []
        for record in records:
            if slot == "body":
                family = self.families[record[slot]]
                name = family["methods"].get(str(role))
                if name is None:
                    continue
            else:
                if role != 0:
                    raise ValueError("Field and placement calls must use role zero")
                name = record[slot]
            function = self.definition["functions"][name]
            if function["signature"] == signature:
                candidates.append(function["binding"])
        if not candidates:
            raise ValueError(f"No named contract for {key!r}.{slot}.role{role} signature {signature}")
        first = candidates[0]
        if any(binding["inputs"] != first["inputs"] or list(binding["outputs"]) != list(first["outputs"])
               for binding in candidates[1:]):
            raise ValueError("One resident call signature has conflicting named source contracts")
        return first

    def call(self, step, row):
        opcode = row[0]
        if opcode == 3:
            handle, argument_base, output_base = row[1:4]
            if not 0 <= handle < len(self.functions):
                raise ValueError("Helper function handle outside the definition")
            name, function = self.functions[handle]
            binding = function["binding"]
            contract = self.contracts.helper(name)
            operation, label = "call_helper", name
            payload = {"function": name}
        else:
            selector, slot_number, bank, argument_base, output_base, signature, role = row[1:8]
            if slot_number >= len(SLOTS):
                raise ValueError("Record call has an invalid slot")
            slot = SLOTS[slot_number]
            if bank != (0 if self.mutation else 1):
                raise ValueError("Record calls must use old mutation records or published action records")
            selected, key = self.selector(selector, opcode == 11, step)
            payload = {"record": selected, "bank": "old" if bank == 0 else "published",
                       "slot": slot, "role": role}
            if opcode == 11:
                contract_key = "circle"
                binding = self.binding_for_record(contract_key, slot, role, signature)
                contract = self.contracts.record(contract_key, slot, role)
                payload["contract"] = {"key": contract_key, "slot": slot, "role": role}
            else:
                binding = self.binding_for_record(key, slot, role, signature)
                contract = self.contracts.record(key, slot, role)
            operation = "call_record"
            label = f"{key or ('selected' if opcode == 11 else 'target')}_{slot}_role{role}"
        if list(contract["inputs"]) != binding["inputs"] or list(contract["outputs"]) != list(binding["outputs"]):
            raise ValueError(f"Plan step {step}: named numerical and nominal type contracts disagree")
        payload["args"] = {name: self.use(self.read(argument_base + index, step), contract["inputs"][name])
                           for index, name in enumerate(binding["inputs"])}
        outputs = self.emit(step, operation, label, payload, list(binding["outputs"]))
        for index, value in enumerate(outputs):
            self.write(output_base + index, value, step)

    def run(self, plan):
        used_words = {0: 3, 1: 4, 2: 6, 3: 4, 4: 8, 5: 4, 6: 4, 9: 2, 10: 4, 11: 8, 12: 6}
        for step, row in enumerate(plan):
            if (not isinstance(row, list) or len(row) != 8 or
                    any(type(word) is not int or not 0 <= word <= ir.UINT32_MAX for word in row)):
                raise ValueError(f"Plan step {step}: expected eight uint32 words")
            opcode = row[0]
            if opcode not in used_words:
                raise ValueError(f"Plan step {step}: unsupported graph-export opcode {opcode}")
            if any(row[used_words[opcode]:]):
                raise ValueError(f"Plan step {step}: reserved operand words are not zero")
            if opcode == 0:
                number = struct.unpack("<f", struct.pack("<I", row[2]))[0]
                ir.fp32(number, "graph literal")
                value = _Value({"literal": number})
                self.literal_values.append(value)
                self.write(row[1], value, step)
            elif opcode == 1:
                destination, source, width = row[1:4]
                if width == 0 or source + width > len(self.state_names):
                    raise ValueError("Old-state read exceeds the named state schema")
                for offset in range(width):
                    self.write(destination + offset, _Value({"state": self.state_names[source + offset]}), step)
            elif opcode in (2, 12):
                destination, selector, word, width, bank = row[1:6]
                if bank not in (0, 1) or (self.mutation and bank != 0):
                    raise ValueError("Record read has an invalid old/published bank")
                if width == 0 or word + width > len(self.record_names):
                    raise ValueError("Record read exceeds the named record schema")
                selected, key = self.selector(selector, opcode == 12, step)
                names = self.record_names[word:word + width]
                payload = {"record": selected, "bank": "old" if bank == 0 else "published", "fields": names}
                values = self.emit(step, "read_record", f"{key or ('selected' if opcode == 12 else 'target')}_{names[0]}", payload, names)
                for offset, value in enumerate(values):
                    self.write(destination + offset, value, step)
            elif opcode in (3, 4, 11):
                self.call(step, row)
            elif opcode == 9:
                if not self.mutation:
                    raise ValueError("Target source-index load is mutation-only")
                self.write(row[1], _Value({"target_index": True}), step)
            elif opcode == 10:
                destination, source, width = row[1:4]
                if width == 0:
                    raise ValueError("COPY must have a nonempty span")
                # Capture before writes: COPY has memmove/snapshot semantics.
                values = [self.read(source + offset, step) for offset in range(width)]
                for offset, value in enumerate(values):
                    self.write(destination + offset, value, step)
            elif opcode in (5, 6):
                if (opcode == 5) != self.mutation:
                    raise ValueError("Return instruction is in the wrong plan")
                destination, source, width = row[1:4]
                names = self.record_names if self.mutation else self.state_names
                if width == 0 or destination + width > len(names):
                    raise ValueError("Return instruction exceeds its named destination schema")
                for offset in range(width):
                    name = names[destination + offset]
                    if name in self.returns:
                        raise ValueError(f"Duplicate named return {name!r}")
                    expected = self.contracts.record_fields[name] if self.mutation else self.contracts.states[name]
                    self.returns[name] = self.use(self.read(source + offset, step), expected)
        names = self.record_names if self.mutation else self.state_names
        if set(self.returns) != set(names):
            raise ValueError("Plan does not return every named field exactly once")
        # Canonical field order is independent of the physical write schedule.
        self.returns = {name: self.returns[name] for name in names}
        for value in self.literal_values:
            if len(value.literal_types) != 1:
                raise ValueError(f"Literal {value.reference['literal']!r} has ambiguous or conflicting nominal uses: {sorted(value.literal_types)}")


def _materialize(value):
    if isinstance(value, _Value):
        result = dict(value.reference)
        if "literal" in result:
            result["type"] = next(iter(value.literal_types))
        return result
    if isinstance(value, dict):
        return {key: _materialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_materialize(item) for item in value]
    return value


def export_graph(definition, cycle):
    """Export both plans without retaining physical registers or opcode tapes."""
    if definition.get("profile") != resident.PROFILE:
        raise ValueError("Graph export requires a DWI-RESIDENT-0.2 definition")
    phases = cycle.get("phases") if isinstance(cycle, dict) else None
    boundaries = definition.get("source", {}).get("stage_boundaries")
    if not isinstance(phases, list) or not phases or len(set(phases)) != len(phases):
        raise ValueError("Source cycle must provide unique ordered phase names")
    if not isinstance(boundaries, list) or [stage.get("phase") for stage in boundaries] != phases:
        raise ValueError("Definition stage boundaries do not match the declared source cycle")
    ranges, previous = [], 0
    for stage in boundaries:
        start, stop = stage.get("action_step_start"), stage.get("action_step_end_exclusive")
        if (type(start) is not int or type(stop) is not int or start < previous
                or not start <= stop <= len(definition["action_plan"])):
            raise ValueError("Definition contains invalid or overlapping source-phase boundaries")
        ranges.append((stage["phase"], start, stop)); previous = stop
    if previous != len(definition["action_plan"]):
        raise ValueError("Source phase boundaries do not cover the final action plan")
    contracts = _Contracts(definition)
    mutation = _Lift(definition, True, contracts)
    action = _Lift(definition, False, contracts, ranges)
    mutation.run(definition["mutation_plan"])
    action.run(definition["action_plan"])
    graph = {
        "profile": PROFILE, "type_profile": TYPE_PROFILE, "functions": {},
        "mutation": {"nodes": mutation.nodes, "returns": mutation.returns},
        "phases": [{"name": name, "nodes": action.phase_nodes[name]} for name in phases],
        "returns": action.returns,
        "source": {"origin": "Offline value-flow export from a declared numerical edition; the named graph is the subsequent application-wiring source.",
                   "exporter_sha256": ir.sha256(Path(__file__).read_bytes()),
                   "origin_definition_semantic_sha256": ir.sha256(ir.json_bytes(definition)),
                   "model_semantic_sha256": definition.get("source", {}).get("model_semantic_sha256"),
                   "cycle_semantic_sha256": ir.sha256(ir.json_bytes(cycle)),
                   "capture_semantics": "Every plan read/call is retained in order. COPY is an immutable alias. Return values are captured at their original writes and named independently of later frame reuse; the graph compiler publishes only within the whole epoch transaction."},
        "meaning": "Complete old-snapshot operator mutation and ordered source phases with named record calls, helper calls, data dependencies and complete state/record returns.",
        "status": "Authored source graph; independent graph lowering and numerical evidence required.",
    }
    return _materialize(graph)
