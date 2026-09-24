"""Lower a named, typed source recurrence graph to versioned resident call plans.

Graph nodes own both old-snapshot mutation wiring and published-record action
wiring. Register allocation and argument packing are compiler details, never
source graph operands. Numerical body laws remain explicit resident bindings.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from pathlib import Path

try:
    from . import source_ir_v2 as ir
    from . import source_resident_v2 as resident
    from . import source_graph_types as nominal
    from . import source_graph_fidelity as fidelity
except ImportError:
    import source_ir_v2 as ir
    import source_resident_v2 as resident
    import source_graph_types as nominal
    import source_graph_fidelity as fidelity


PROFILE = "DWI-SOURCE-GRAPH-0.1"
ARGUMENT_BASE = 192
VALUE_REGISTERS = 192
MAX_NODES = 2048


def _name(value, where):
    if not isinstance(value, str) or not value or len(value) > 160:
        raise ValueError(f"{where}: expected a nonempty name of at most160 characters")
    return value


def _type(value, where, profile=nominal.TYPE_PROFILE):
    kinds = nominal.EXTENDED_TYPES if profile == nominal.EXTENDED_TYPE_PROFILE else nominal.TYPES
    if value not in kinds:
        raise ValueError(f"{where}: unknown nominal type {value!r}")
    return value


def _pointer(value):
    return str(value).replace("~", "~0").replace("/", "~1")


class Lowering:
    def __init__(self, definition, graph, mutation, extra_contracts, resident_backend=resident):
        self.definition, self.graph, self.mutation = definition, graph, mutation
        self.extra_contracts = extra_contracts
        self.resident_backend = resident_backend
        self.states = nominal.state_types(definition)
        self.record_fields = nominal.record_types(definition)
        self.records = {record["key"]: (index, record) for index, record in enumerate(definition["records"])}
        self.values = {}
        self.nodes = []
        self.by_id = {}
        self.uses = Counter()
        self.registers = {}
        self.occupied = set()
        self.words = []
        self.calls = []
        self.provenance = []
        self.input_reads = []
        self.high_water = 0
        self.phase_ranges = []

    def emit(self, op, *args):
        if len(args) > 7:
            raise ValueError("Internal graph lowering error: too many plan operands")
        self.words.append([op, *args, *([0] * (7 - len(args)))])
        if len(self.words) > self.resident_backend.MAX_STEPS:
            raise ValueError("Source graph exceeds the resident plan-instruction limit")

    def allocate(self, width):
        start = next((start for start in range(VALUE_REGISTERS - width + 1)
                      if not any(index in self.occupied for index in range(start, start + width))), None)
        if start is None:
            raise ValueError("Source graph's live values exceed the192-register value arena")
        self.occupied.update(range(start, start + width))
        self.high_water = max(self.high_water, len(self.occupied))
        return start

    def reference(self, ref, where, expected=None):
        if not isinstance(ref, dict):
            raise ValueError(f"{where}: use an explicit state, node-output, literal or target-index reference")
        if set(ref) == {"state"}:
            name = ref["state"]
            if name not in self.states:
                raise ValueError(f"{where}: unknown old-state input {name!r}")
            key, kind = ("state", name), self.states[name]
        elif set(ref) == {"node", "output"}:
            node, output = ref["node"], ref["output"]
            if not isinstance(node, str) or not isinstance(output, str):
                raise ValueError(f"{where}: node and output must be names")
            key = ("node", node, output)
            if key not in self.values:
                raise ValueError(f"{where}: unknown/future node output {node!r}.{output!r}")
            kind = self.values[key]["type"]
        elif set(ref) == {"literal", "type"}:
            kind = _type(ref["type"], where + ".type", self.graph["type_profile"])
            value, bits = ir.fp32(ref["literal"], where + ".literal")
            if kind == "bit" and value not in (0, 1):
                raise ValueError(f"{where}: a bit literal must be zero or one")
            if kind in {"index", "body_handle", "field_handle", "placement_handle", "generation",
                        "program_opcode", "program_index", "program_size", "program_revision"}:
                if not 0 <= value <= resident.EXACT_LIMIT or int(value) != value:
                    raise ValueError(f"{where}: this literal requires an exact bounded nonnegative integer")
            key = ("literal", kind, bits)
        elif set(ref) == {"target_index"} and ref["target_index"] is True:
            if not self.mutation:
                raise ValueError(f"{where}: a mutation target is unavailable in the action graph")
            key, kind = ("target_index",), "index"
        else:
            raise ValueError(f"{where}: malformed reference")
        if expected is not None and kind != expected:
            raise ValueError(f"{where}: nominal type {kind!r} does not match {expected!r}")
        self.values.setdefault(key, {"type": kind, "reference": deepcopy(ref)})
        return key

    def record(self, selector, where):
        if not isinstance(selector, dict):
            raise ValueError(f"{where}: expected a record selector")
        if set(selector) == {"key"}:
            if selector["key"] not in self.records:
                raise ValueError(f"{where}: unknown record key")
            return {"ordinal": self.records[selector["key"]][0], "key": selector["key"]}
        if set(selector) == {"target"} and selector["target"] is True:
            if not self.mutation:
                raise ValueError(f"{where}: target record exists only in mutation")
            return {"ordinal": resident.TARGET, "target": True}
        if set(selector) == {"source_index"}:
            ref = self.reference(selector["source_index"], where + ".source_index", "index")
            return {"dynamic": ref}
        raise ValueError(f"{where}: malformed record selector")

    def contract(self, name):
        return self.extra_contracts.get(name) or nominal.function_contract(self.definition, name)

    def bank(self, value, where, call):
        if value not in {"old", "published"}:
            raise ValueError(f"{where}: bank must be old or published")
        if self.mutation and value != "old":
            raise ValueError(f"{where}: mutation reads the common old snapshot only")
        if not self.mutation and call and value != "published":
            raise ValueError(f"{where}: action calls must resolve published definitions")
        return 0 if value == "old" else 1

    def collect(self, raw, path, phase):
        if len(self.nodes) >= MAX_NODES:
            raise ValueError("Source graph exceeds its2048-node-per-plan limit")
        if not isinstance(raw, dict):
            raise ValueError(f"{path}: expected a graph node")
        op = raw.get("op")
        keys = {"id", "op"}
        if op == "read_record": keys |= {"record", "bank", "fields"}
        elif op == "call_record": keys |= {"record", "bank", "slot", "role", "args"}
        elif op == "call_helper": keys |= {"function", "args"}
        else: raise ValueError(f"{path}: unsupported graph node operation {op!r}")
        ir.exact_keys(raw, keys | ({"contract"} if op == "call_record" else set()), keys, path)
        identity = _name(raw["id"], path + ".id")
        if identity in self.by_id:
            raise ValueError(f"{path}: duplicate node identity {identity!r}")
        node = {"id": identity, "op": op, "path": path, "phase": phase, "dependencies": []}
        if op != "call_helper":
            node["record"] = self.record(raw["record"], path + ".record")
            node["bank"] = self.bank(raw["bank"], path + ".bank", op == "call_record")
            if "dynamic" in node["record"]:
                node["dependencies"].append(node["record"]["dynamic"])
        if op == "read_record":
            fields = raw["fields"]
            if (not isinstance(fields, list) or not fields or len(fields) > resident.RECORD_WORDS
                    or any(not isinstance(name, str) or name not in self.record_fields for name in fields)
                    or len(set(fields)) != len(fields)):
                raise ValueError(f"{path}.fields: expected unique named resident record fields")
            node["fields"] = fields
            outputs = {name: self.record_fields[name] for name in fields}
        else:
            if op == "call_helper":
                function_name = raw["function"]
                if function_name not in self.definition["functions"]:
                    raise ValueError(f"{path}: unknown helper function {function_name!r}")
                if any(function_name in family["methods"].values() for family in self.definition["families"].values()):
                    raise ValueError(f"{path}: use a current-record call for a resident body method")
            else:
                slot, role = raw["slot"], raw["role"]
                if slot not in {"body", "field", "placement"} or type(role) is not int or not 0 <= role <= ir.UINT32_MAX:
                    raise ValueError(f"{path}: invalid slot/role")
                if slot != "body" and role != 0:
                    raise ValueError(f"{path}: field and placement calls use role0")
                node.update(slot=slot, role=role)
                selector = node["record"]
                if "dynamic" in selector or "target" in selector:
                    if slot == "body" and "contract" not in raw:
                        raise ValueError(f"{path}: computed/target body calls require a named contract")
                    if "contract" in raw:
                        contract = raw["contract"]
                        ir.exact_keys(contract, {"key", "slot", "role"}, {"key", "slot", "role"}, path + ".contract")
                        if contract["slot"] != slot or contract["role"] != role or contract["key"] not in self.records:
                            raise ValueError(f"{path}: contract does not match this computed call")
                        record = self.records[contract["key"]][1]
                    else:
                        record = self.definition["records"][0]
                else:
                    if "contract" in raw:
                        raise ValueError(f"{path}: a fixed record call already declares its contract")
                    record = self.records[selector["key"]][1]
                if slot == "body":
                    family = self.definition["families"][record["body"]]
                    function_name = family["methods"].get(str(role))
                    if function_name is None:
                        raise ValueError(f"{path}: record has no declared role{role}")
                else:
                    function_name = record[slot]
            function = self.definition["functions"][function_name]
            contract = self.contract(function_name)
            if list(contract["inputs"]) != function["binding"]["inputs"] or list(contract["outputs"]) != list(function["binding"]["outputs"]):
                raise ValueError(f"{path}: nominal contract and actual numerical binding disagree")
            args = raw["args"]
            if not isinstance(args, dict) or list(args) != list(contract["inputs"]):
                raise ValueError(f"{path}.args: expected ordered named arguments {list(contract['inputs'])!r}")
            node["args"] = [self.reference(args[name], path + "/args/" + _pointer(name), kind)
                            for name, kind in contract["inputs"].items()]
            node["dependencies"].extend(node["args"])
            node["function"], node["signature"] = function_name, function["signature"]
            outputs = contract["outputs"]
        node["outputs"] = []
        for name, kind in outputs.items():
            key = ("node", identity, name)
            self.values[key] = {"type": _type(kind, path + ".output type", self.graph["type_profile"]),
                                "reference": {"node": identity, "output": name}}
            node["outputs"].append(key)
        self.by_id[identity] = node
        self.nodes.append(node)
        self.uses.update(node["dependencies"])

    def materialize(self, key):
        if key in self.registers:
            return self.registers[key]
        if key[0] == "node":
            raise ValueError("Internal graph lowering error: node value was not retained")
        register = self.allocate(1)
        step = len(self.words)
        if key[0] == "state": self.emit(1, register, list(self.states).index(key[1]), 1)
        elif key[0] == "literal": self.emit(0, register, key[2])
        elif key[0] == "target_index": self.emit(9, register)
        else: raise ValueError("Internal graph lowering error: unsupported value")
        self.registers[key] = register
        self.input_reads.append({"step": step, "reference": self.values[key]["reference"], "register": register})
        return register

    def consume(self, key):
        self.uses[key] -= 1
        if self.uses[key] < 0:
            raise ValueError("Internal graph lowering error: negative reference lifetime")
        if self.uses[key] == 0 and key in self.registers:
            self.occupied.remove(self.registers.pop(key))

    def lower_node(self, node):
        start = len(self.words)
        selector = node.get("record", {})
        dynamic = "dynamic" in selector
        selected = self.materialize(selector["dynamic"]) if dynamic else selector.get("ordinal")
        if node["op"] != "read_record":
            for offset, key in enumerate(node["args"]):
                self.emit(10, ARGUMENT_BASE + offset, self.materialize(key), 1)
            for key in node["args"]:
                self.consume(key)
        output = self.allocate(len(node["outputs"]))
        if node["op"] == "read_record":
            fields = [list(self.record_fields).index(name) for name in node["fields"]]
            offset = 0
            while offset < len(fields):
                count = 1
                while offset + count < len(fields) and fields[offset + count] == fields[offset] + count:
                    count += 1
                self.emit(12 if dynamic else 2, output + offset, selected, fields[offset], count, node["bank"])
                offset += count
        elif node["op"] == "call_helper":
            handle = list(self.definition["functions"]).index(node["function"])
            self.calls.append({"step": len(self.words), "helper": node["function"],
                               "inputs": list(range(ARGUMENT_BASE, ARGUMENT_BASE + len(node["args"]))), "output_base": output,
                               "graph_node": node["id"], "source_pointer": node["path"]})
            self.emit(3, handle, ARGUMENT_BASE, output)
        else:
            self.calls.append({"step": len(self.words), "record": selected, "dynamic_source_index": dynamic,
                               "slot": ("body", "field", "placement").index(node["slot"]), "bank": node["bank"],
                               "signature": node["signature"], "role": node["role"],
                               "inputs": list(range(ARGUMENT_BASE, ARGUMENT_BASE + len(node["args"]))), "output_base": output,
                               "graph_node": node["id"], "source_pointer": node["path"]})
            self.emit(11 if dynamic else 4, selected, ("body", "field", "placement").index(node["slot"]),
                      node["bank"], ARGUMENT_BASE, output, node["signature"], node["role"])
        if dynamic:
            self.consume(selector["dynamic"])
        for offset, key in enumerate(node["outputs"]):
            if self.uses[key]: self.registers[key] = output + offset
            else: self.occupied.remove(output + offset)
        self.provenance.append({"node": node["id"], "source_pointer": node["path"], "phase": node["phase"],
                                "plan_step_start": start, "plan_step_end_exclusive": len(self.words),
                                "output_registers": {key[2]: output + i for i, key in enumerate(node["outputs"])}})

    def lower(self, returns):
        expected = self.record_fields if self.mutation else self.states
        ir.exact_keys(returns, set(expected), set(expected), "mutation returns" if self.mutation else "state returns")
        output_refs = {name: self.reference(returns[name], "/mutation/returns/" + _pointer(name) if self.mutation
                                          else "/returns/" + _pointer(name), kind) for name, kind in expected.items()}
        self.uses.update(output_refs.values())
        active_phase = None
        for node in self.nodes:
            if node["phase"] != active_phase:
                if self.phase_ranges:
                    self.phase_ranges[-1]["action_step_end_exclusive"] = len(self.words)
                active_phase = node["phase"]
                self.phase_ranges.append({"phase": active_phase, "action_step_start": len(self.words)})
            self.lower_node(node)
        return_steps = []
        for index, (name, key) in enumerate(output_refs.items()):
            register = self.materialize(key)
            return_steps.append({"field": name, "step": len(self.words), "reference": deepcopy(returns[name])})
            if self.mutation: self.emit(10, ARGUMENT_BASE + index, register, 1)
            else: self.emit(6, index, register, 1)
            self.consume(key)
        if self.mutation: self.emit(5, 0, ARGUMENT_BASE, resident.RECORD_WORDS)
        if self.phase_ranges:
            self.phase_ranges[-1]["action_step_end_exclusive"] = len(self.words)
        if any(self.uses.values()) or self.occupied:
            raise ValueError("Internal graph lowering error: unresolved value lifetime")
        return {"nodes": self.provenance, "inputs": self.input_reads, "returns": return_steps,
                "value_register_high_water": self.high_water, "argument_base": ARGUMENT_BASE,
                "plan_sha256": ir.sha256(ir.json_bytes(self.words))}


def _refresh_source_layout(definition, mutation, action, structural, action_metadata):
    """Replace construction-layout claims with the newly lowered graph layout.

    Only semantic policy fields identify the relevant graph nodes. No old tape,
    call-site positions or allocator operands are used to derive these mappings.
    The same policy appears in authoring provenance and must agree there too.
    """
    def call_maps(lowering):
        positions = {item["node"]: item for item in lowering.provenance}
        result = {}
        for call in lowering.calls:
            identity = call["graph_node"]
            node, position = lowering.by_id[identity], positions[identity]
            inputs = lowering.contract(node["function"])["inputs"]
            result[identity] = {
                "node": identity, "source_pointer": node["path"], "phase": node["phase"],
                "plan": "mutation" if lowering.mutation else "action", "call_step": call["step"],
                "plan_step_start": position["plan_step_start"],
                "plan_step_end_exclusive": position["plan_step_end_exclusive"],
                "argument_registers": dict(zip(inputs, call["inputs"])),
                "output_registers": deepcopy(position["output_registers"]),
            }
        return result

    mutation_calls, action_calls = call_maps(mutation), call_maps(action)
    source = definition["source"]
    retention = structural["mutation"]["retention"]

    def refresh_retention(policy):
        # Discard the builder's physical layout, retaining its semantic policy.
        for key in ("step", "inputs", "argument_base", "output_base"):
            policy.pop(key, None)
        policy["layout_source"] = PROFILE
        policy["graph_calls"] = [deepcopy(mutation_calls[item["node"]]) for item in retention
                                 if item["function"] == policy["function"]]

    def refresh_slots(metadata):
        if metadata:
            for policy in metadata.get("mutation_program_retention", []):
                refresh_retention(policy)

    def refresh_extension(metadata):
        if not metadata or not metadata.get("added"):
            return
        refresh_retention(metadata["mutation_retention"])
        routing = metadata["routing"]
        routing.pop("call_step", None)
        routing["layout_source"] = PROFILE
        routing["graph_calls"] = [deepcopy(action_calls[node["id"]]) for node in action.nodes
                                  if node["op"] == "call_record" and node["function"] == routing["function"]
                                  and node["slot"] == "body" and node["role"] == 0]

    refresh_slots(source.get("source_slot_bindings"))
    refresh_extension(source.get("catalogue_extension"))
    authoring = source.get("authoring", {})
    refresh_slots(authoring.get("slot_resolutions"))
    refresh_extension(authoring.get("catalogue_extension"))
    if structural["enzyme"] is not None:
        source["enzyme"]["resident_application"] = {
            "phase": "surface_return", "layout_source": PROFILE,
            "placement": "Explicit graph calls in surface_return; every final state write is lowered from the graph return mapping.",
            "graph_calls": {role: deepcopy(action_calls[identity])
                            for role, identity in structural["enzyme"].items()},
            "return_writes": [deepcopy(item) for item in action_metadata["returns"]
                              if item["field"] in source["enzyme"]["state_layout"]],
            "scope": "Current graph layout, not the construction builder's provisional-write prefix. Situated placement/field dependencies are recorded in application_graph.structural_fidelity.",
        }


def apply_graph(definition, cycle, graph, *, resident_backend=resident):
    """Atomically replace BOTH final plans using only the supplied source graph."""
    keys = {"profile", "type_profile", "functions", "mutation", "phases", "returns", "source", "meaning", "status"}
    ir.exact_keys(graph, keys, keys - {"source", "meaning", "status"}, "source graph")
    if graph["profile"] != PROFILE or graph["type_profile"] not in {nominal.TYPE_PROFILE, nominal.EXTENDED_TYPE_PROFILE}:
        raise ValueError("Unknown source graph or nominal type profile")
    if definition.get("source", {}).get("graph_type_contracts") is not None and graph["type_profile"] != nominal.EXTENDED_TYPE_PROFILE:
        raise ValueError("Additional state/function declarations require the explicit extended type profile")
    if len(definition["state_names"]) > getattr(resident_backend, "MAX_STATES", resident_backend.ir.MAX_INPUTS):
        raise ValueError("Source graph state exceeds the selected resident backend")
    ir.exact_keys(graph["mutation"], {"nodes", "returns"}, {"nodes", "returns"}, "graph.mutation")
    if not isinstance(graph["mutation"]["nodes"], list):
        raise ValueError("graph.mutation.nodes must be an array")
    phases = graph["phases"]
    if not isinstance(phases, list) or [phase.get("name") if isinstance(phase, dict) else None for phase in phases] != cycle["phases"]:
        raise ValueError("Graph phases must match the complete declared source cycle in order")
    working = deepcopy(definition)
    extras = {}
    if not isinstance(graph["functions"], dict):
        raise ValueError("graph.functions must be an ordered mapping")
    for name, entry in graph["functions"].items():
        _name(name, "graph helper name")
        if name in working["functions"]:
            raise ValueError("A graph helper cannot replace an existing numerical definition")
        ir.exact_keys(entry, {"binding", "inputs", "outputs"}, {"binding", "inputs", "outputs"}, "graph helper " + name)
        ir.validate_binding(entry["binding"], "graph helper " + name)
        if (not isinstance(entry["inputs"], dict) or not isinstance(entry["outputs"], dict)
                or list(entry["inputs"]) != entry["binding"]["inputs"]
                or list(entry["outputs"]) != list(entry["binding"]["outputs"])):
            raise ValueError("Graph helper type contract must match its exact ordered numerical inputs and outputs")
        for kind in [*entry["inputs"].values(), *entry["outputs"].values()]: _type(kind, "graph helper type", graph["type_profile"])
        compiler = ir.ExpressionCompiler(entry["binding"]["inputs"])
        for index, guard in enumerate(entry["binding"].get("requires", [])):
            compiler._emit(17, compiler.expression(guard, f"graph.functions.{name}.requires[{index}]"))
        for field, expression in entry["binding"]["outputs"].items():
            compiler.expression(expression, f"graph.functions.{name}.outputs.{field}")
        extras[name] = {"inputs": deepcopy(entry["inputs"]), "outputs": deepcopy(entry["outputs"])}
        signature = max(f["signature"] for f in working["functions"].values()) + 1
        working["functions"][name] = {"signature": signature, "binding": deepcopy(entry["binding"])}
    if len(working["functions"]) > resident_backend.MAX_FUNCTIONS:
        raise ValueError("Graph helper declarations exceed the resident function-bank limit")
    mutation = Lowering(working, graph, True, extras, resident_backend)
    action = Lowering(working, graph, False, extras, resident_backend)
    for index, node in enumerate(graph["mutation"]["nodes"]):
        mutation.collect(node, f"/mutation/nodes/{index}", "old_snapshot_mutation")
    for phase_index, phase in enumerate(phases):
        ir.exact_keys(phase, {"name", "nodes"}, {"name", "nodes"}, f"graph.phases[{phase_index}]")
        if not isinstance(phase["nodes"], list) or not phase["nodes"]:
            raise ValueError("Each declared source phase needs explicit graph nodes")
        for index, node in enumerate(phase["nodes"]):
            action.collect(node, f"/phases/{phase_index}/nodes/{index}", phase["name"])
    mutation_metadata = mutation.lower(graph["mutation"]["returns"])
    action_metadata = action.lower(graph["returns"])
    structural = fidelity.audit_graph(working, cycle, graph)
    # No original tape or call-site layout contributes to the new executable.
    working["mutation_plan"], working["action_plan"] = mutation.words, action.words
    working["source"]["mutation_calls"], working["source"]["action_calls"] = mutation.calls, action.calls
    working["source"]["stage_boundaries"] = action.phase_ranges
    _refresh_source_layout(working, mutation, action, structural, action_metadata)
    metadata = {"profile": PROFILE, "type_profile": graph["type_profile"],
                "graph_sha256": ir.sha256(ir.json_bytes(graph)), "graph": deepcopy(graph),
                "mutation": mutation_metadata, "action": action_metadata, "structural_fidelity": structural,
                "compiler_sha256": ir.sha256(Path(__file__).read_bytes()),
                "types_sha256": ir.sha256(Path(nominal.__file__).read_bytes()),
                "fidelity_checker_sha256": ir.sha256(Path(fidelity.__file__).read_bytes()),
                "scope": "Both call plans and every final record/state write are lowered from named source graph references. Numerical function/record banks and initial data remain explicit edition/source bindings. All nodes execute in declaration order; unused outputs do not remove calls or their guards.",
                "allocation": "At most192 live value registers plus a separate64-value argument window; no registers appear in source graph operands.",
                "typing": "Nominal wiring contracts distinguish representations and roles; they are not a proof of dimensional consistency or physical validity of authored arithmetic."}
    if graph["type_profile"] == nominal.EXTENDED_TYPE_PROFILE:
        metadata["resident_profile"] = resident_backend.PROFILE
        metadata["additional_contracts"] = deepcopy(nominal.extension_contracts(working))
    working["source"]["application_graph"] = metadata
    definition.clear()
    definition.update(working)
    return deepcopy(metadata)
