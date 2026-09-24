"""One explicit situated catalogue addition for source-owned cycle authoring.

The first 31 entries are resolved by source_slot_bindings. A new record supplies
its own numerical wave-action body, field and placement; this module does not
invent an adapter from an unrelated operator type. The resident ABI is unchanged.
"""
from __future__ import annotations

from copy import deepcopy

try:
    from . import source_cycle as base
    from . import source_ir_v2 as ir
    from . import source_resident_v2 as resident
    from . import source_slot_bindings as slots
except ImportError:
    import source_cycle as base
    import source_ir_v2 as ir
    import source_resident_v2 as resident
    import source_slot_bindings as slots


PROFILE = "DWI-SOURCE-EXTENSION-0.1"
SLOTS = ("body", "field", "placement")
RECORD_VALUES = ["anchor_u", "anchor_v", "anchor_orientation", "radius", "phase_gain",
                 "shift_u", "shift_v", "placement_scale", "control", "du", "dv", "feedback_gain",
                 "last_mutator_field", "previous_body_handle", "last_pinion_field",
                 "reserved_0", "reserved_1", "reserved_2", "reserved_3", "reserved_4"]
CONTRACTS = {
    "body": (["ar", "ai", "br", "bi", "routing_phase", "field_distance"], ["ar", "ai", "br", "bi"], 90),
    "field": (["dx", "dy", "radius"], ["distance"], 4),
    "placement": (["u", "v", "orientation"], ["u", "v", "orientation"], 5),
}


def _uint(value, where, minimum=0, maximum=resident.EXACT_LIMIT):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{where}: expected an integer in {minimum}..{maximum}")
    return value


def _binding(record, slot):
    where = f"added source record {record['key']}.{slot}"
    declaration = record[slot]
    ir.exact_keys(declaration, {"resident_binding"}, {"resident_binding"}, where)
    binding = declaration["resident_binding"]
    ir.exact_keys(binding, {"kind", "function", "mutation_policy"},
                  {"kind", "function", "mutation_policy"}, where + ".resident_binding")
    expected_kind = "selected_body" if slot == "body" else slot
    expected_policy = "preserve_family" if slot == "body" else "preserve_program"
    if binding["kind"] != expected_kind or binding["mutation_policy"] != expected_policy:
        raise ValueError(f"{where}: expected kind={expected_kind!r} and mutation_policy={expected_policy!r}")
    function = binding["function"]
    ir.validate_binding(function, where + ".function")
    inputs, outputs, _ = CONTRACTS[slot]
    if function["inputs"] != inputs or list(function["outputs"]) != outputs:
        raise ValueError(f"{where}: ordered contract must be {inputs!r} -> {outputs!r}")
    # Compile each authored expression to check the actual vocabulary, guards,
    # dependencies and 256-instruction limit; no default numerical law is added.
    compiler = ir.ExpressionCompiler(inputs)
    for index, condition in enumerate(function.get("requires", [])):
        register = compiler.expression(condition, f"{where}.requires[{index}]")
        compiler._emit(17, register)
    for name, expression in function["outputs"].items():
        compiler.expression(expression, f"{where}.outputs[{name!r}]")
    return function


def prepare_extended_model(actual_model):
    """Return (first31_model, extension_record_or_none), without mutation.

    The caller passes first31_model through source_slot_bindings.prepare_model.
    One additional record may use an unoccupied source index31..62, reachable
    in five implicit-tree steps. All three slots are explicit resident_binding
    declarations; all20 record parameters are required by name.
    """
    if not isinstance(actual_model, dict) or not isinstance(actual_model.get("operators"), list):
        raise ValueError("Source catalogue must contain an operators array")
    operators = actual_model["operators"]
    if len(operators) not in (31, 32):
        raise ValueError("This source edition supports the original31 records and at most one explicit addition")
    first = deepcopy(actual_model)
    first["operators"] = first["operators"][:31]
    if len(operators) == 31:
        return first, None
    extension = deepcopy(operators[31])
    required = {"index", "key", "body", "field", "placement", "parameters"}
    allowed = required | {"label", "head", "role", "source_pages"}
    ir.exact_keys(extension, allowed, required, "added source record")
    index = _uint(extension["index"], "added source index", 31, 62)
    key = extension["key"]
    if not isinstance(key, str) or not key:
        raise ValueError("Added source key must be a nonempty string")
    if any(item.get("key") == key or item.get("index") == index for item in operators[:31] if isinstance(item, dict)):
        raise ValueError("Added source record duplicates an occupied key or index")
    for name in ("label", "head", "role", "source_pages"):
        if name in extension and not isinstance(extension[name], str):
            raise ValueError(f"added source record.{name}: descriptive metadata must be a string")
    for slot in SLOTS:
        _binding(extension, slot)
    ir.exact_keys(extension["parameters"], set(RECORD_VALUES), set(RECORD_VALUES), "added source parameters")
    for name in RECORD_VALUES:
        ir.fp32(extension["parameters"][name], "added source parameters." + name)
    return first, extension


def _append_function(definition, name, signature, binding):
    if name in definition["functions"]:
        raise ValueError(f"Private extension function name collision: {name}")
    definition["functions"][name] = {"signature": signature, "binding": deepcopy(binding)}
    return list(definition["functions"]).index(name)


def _shift_trace(definition, plan, position, count):
    for call in definition.setdefault("source", {}).setdefault(plan + "_calls", []):
        if call.get("step", -1) >= position:
            call["step"] += count
    if plan == "action":
        for stage in definition["source"]["stage_boundaries"]:
            for key in ("action_step_start", "action_step_end_exclusive"):
                if stage[key] >= position:
                    stage[key] += count


def _preserve_added_handles(definition, source_index):
    plan = definition["mutation_plan"]
    writes = [i for i, row in enumerate(plan) if row[0] == 5]
    if len(writes) != 1 or writes[0] != len(plan) - 1 or plan[-1][1] != 0 or plan[-1][3] != 24:
        raise ValueError("Catalogue extension requires one final whole-record mutation write")
    reads = [row for row in plan if row[0] == 2 and row[2] == resident.TARGET and row[3:6] == [0, 24, 0]]
    indices = [row for row in plan if row[0] == 9]
    if len(reads) != 1 or len(indices) != 1:
        raise ValueError("Catalogue extension requires one old-target read and source-index load")
    old, proposal, index_register = reads[0][1], plan[-1][2], indices[0][1]
    used = slots._frame_usage(plan, definition)
    scratch = next((start for start in range(resident.FRAME_WORDS - 7, -1, -1)
                    if all(start + i not in used for i in range(7))), None)
    if scratch is None:
        raise ValueError("No independent mutation scratch span for added-record program retention")
    names = ["source_index", "old_body", "old_field", "old_placement", "new_body", "new_field", "new_placement"]
    equal = base.eq(base.V("source_index"), source_index)
    binding = {"inputs": names,
               "outputs": {slot: base.choose(equal, base.V("old_" + slot), base.V("new_" + slot)) for slot in SLOTS},
               "source": PROFILE + " explicit preserve_family/preserve_program policies",
               "meaning": "For the added source index only, retain all three old executable handles after the common old-snapshot proposal. Numerical anchors, radius, control, generation and other record values still use the common mutation proposal.",
               "status": "Authored bounded catalogue-extension policy."}
    name = "source_extension__preserve_handles"
    signature = max(function["signature"] for function in definition["functions"].values()) + 1
    handle = _append_function(definition, name, signature, binding)
    arguments = [index_register, old, old + 1, old + 2, proposal, proposal + 1, proposal + 2]
    inserted = [[10, scratch + i, value, 1, 0, 0, 0, 0] for i, value in enumerate(arguments)]
    position = len(plan) - 1
    call_step = position + len(inserted)
    inserted.append([3, handle, scratch, proposal, 0, 0, 0, 0])
    _shift_trace(definition, "mutation", position, len(inserted))
    plan[position:position] = inserted
    definition["source"]["mutation_calls"].append({"step": call_step, "helper": name,
                                                       "inputs": arguments, "output_base": proposal})
    return {"function": name, "source_index": source_index, "step": call_step,
            "argument_base": scratch, "output_base": proposal, "slots": list(SLOTS)}


def _extend_bst(definition):
    families, functions = definition["families"], definition["functions"]
    # Do not replace an authored BST body with a hidden five-bit policy. Even an
    # explicit identity override is still an override needing its own contract.
    resolutions = definition.get("source", {}).get("source_slot_bindings", {}).get("resolutions", [])
    if any(item.get("key") == "bst" and item.get("slot") == "body" for item in resolutions):
        raise ValueError("A catalogue addition cannot currently combine with a source-owned BST body override")
    old_data, _ = ir.read_json(base.RESIDENT)
    canonical = base.make_bank(old_data)
    active_name = families["bst"]["methods"].get("0")
    original = canonical.functions[canonical.families["bst"]["methods"]["0"]]
    if active_name not in functions or not resident.same_structure(functions[active_name], original):
        raise ValueError("A catalogue addition requires the original authored BST body before five-bit extension")
    inputs = ["depth", "b0", "b1", "b2", "b3", "b4", "neck", "jitter", "field_distance"]
    index = 0
    for k in range(5):
        bit = base.sub(base.add(base.V(f"b{k}"), base.V("neck")), base.mul(2, base.mul(base.V(f"b{k}"), base.V("neck"))))
        index = base.choose(base.lt(k, base.V("depth")), base.add(base.mul(2, index), base.add(1, bit)), index)
    binding = {"inputs": inputs,
               "outputs": {"index": index, "routing_phase": deepcopy(original["binding"]["outputs"]["routing_phase"])},
               "requires": [base.eq(base.V("depth"), base.op("floor", base.V("depth"))),
                            base.sub(1, base.lt(base.V("depth"), 0)), base.sub(1, base.lt(5, base.V("depth"))),
                            *[base.bit_guard(base.V(name)) for name in ["b0", "b1", "b2", "b3", "b4", "neck", "jitter"]]],
               "source": PROFILE + "; Unified v0.2 p10 implicit child relation",
               "meaning": "The authored BST relation extended from four to five supplied raw bits; neck XOR acts before each child step. Actual source indices are retained without modulo aliasing.",
               "status": "Explicit bounded five-bit route binding."}
    new_signature = max(function["signature"] for function in functions.values()) + 1
    name = "source_extension__bst_five_bits"
    _append_function(definition, name, new_signature, binding)
    families["bst"]["methods"]["0"] = name
    plan = definition["action_plan"]
    matches = [i for i, row in enumerate(plan) if row[:5] == [4, base.INDEX["bst"], 0, 1, 200]
               and row[6:] == [original["signature"], 0]]
    if len(matches) != 1:
        raise ValueError("Five-bit extension requires exactly one current BST action call")
    step = matches[0]
    old_arguments = [17, 18, 19, 20, 21, 16, 9, 239]
    expected = [[10, 200 + i, value, 1, 0, 0, 0, 0] for i, value in enumerate(old_arguments)]
    if plan[step - len(expected):step] != expected:
        raise ValueError("BST action argument layout changed; review the five-bit extension")
    arguments = [17, 18, 19, 20, 21, 44, 16, 9, 239]
    replacement = [[10, 200 + i, value, 1, 0, 0, 0, 0] for i, value in enumerate(arguments)]
    start = step - len(expected)
    position = start + 5
    _shift_trace(definition, "action", position, 1)
    plan[start:step] = replacement
    plan[step + 1][6] = new_signature
    for call in definition["source"]["action_calls"]:
        if call.get("step") == step + 1 and call.get("record") == base.INDEX["bst"] and call.get("slot") == 0:
            call["signature"], call["inputs"] = new_signature, arguments
    return {"function": name, "signature": new_signature, "call_step": step + 1,
            "max_depth": 5, "additional_state": {"name": "route_b4", "index": 44}}


def _path(index):
    directions = []
    while index:
        directions.append((index - 1) % 2)
        index = (index - 1) // 2
    return list(reversed(directions))


def set_routes(definition, routes):
    """Set checked initial routes and return metadata; one entry broadcasts.

    Each entry is exactly {"index": existing_source_index} or {"bits": [0,1,..]}.
    Index form derives raw bits by XOR with that instance's existing neck bit.
    Bits form supplies raw bits directly; neck reversal then determines its
    actual target. Missing records and records without the exact role99 contract
    fail at authoring time. A runtime may still reject independently edited data.
    """
    if not isinstance(routes, list) or len(routes) not in (1, len(definition["instances"])):
        raise ValueError("routes must contain one broadcast entry or one entry per instance")
    max_depth = 5 if "route_b4" in definition["state_names"] else 4
    metadata = definition.get("source", {}).get("catalogue_extension", {})
    mapping = metadata.get("record_source_indices", base.INDEX)
    by_index = {mapping[record["key"]]: record for record in definition["records"]}
    staged, trace = [], []
    for i, instance in enumerate(definition["instances"]):
        route = routes[0 if len(routes) == 1 else i]
        ir.exact_keys(route, {"index", "bits"}, set(), f"routes[{i}]")
        if len(route) != 1:
            raise ValueError(f"routes[{i}]: provide exactly one of index or bits")
        neck = instance["state"]["neck"]
        if type(neck) not in (int, float) or neck not in (0, 1):
            raise ValueError(f"instances[{i}].neck must be zero or one for routing")
        neck = int(neck)
        if "index" in route:
            target = _uint(route["index"], f"routes[{i}].index")
            raw = [bit ^ neck for bit in _path(target)]
        else:
            raw = route["bits"]
            if not isinstance(raw, list) or any(type(bit) is not int or bit not in (0, 1) for bit in raw):
                raise ValueError(f"routes[{i}].bits must be an array of integer bits")
            target = 0
            for bit in raw:
                target = 2 * target + 1 + (bit ^ neck)
        if len(raw) > max_depth:
            raise ValueError(f"routes[{i}]: route exceeds this edition's {max_depth}-bit limit")
        if target not in by_index:
            raise ValueError(f"routes[{i}]: source index {target} is not an occupied record; no alias is applied")
        record = by_index[target]
        family = definition["families"][record["body"]]
        for name, candidate in definition["families"].items():
            if candidate["interface"] != family["interface"]:
                continue
            function_name = candidate["methods"].get("99")
            function = definition["functions"].get(function_name)
            ins, outs, signature = CONTRACTS["body"]
            if (function is None or function["signature"] != signature or
                    function["binding"]["inputs"] != ins or list(function["binding"]["outputs"]) != outs):
                raise ValueError(f"routes[{i}]: record {record['key']!r}, family {name!r} lacks the declared selected-body role99 contract")
        state = deepcopy(instance["state"])
        state["route_depth"] = len(raw)
        for k in range(max_depth):
            state[f"route_b{k}"] = raw[k] if k < len(raw) else 0
        staged.append(state)
        trace.append({"instance": i, "source_index": target, "record_key": record["key"],
                      "raw_bits": list(raw), "neck": neck, "effective_bits": [bit ^ neck for bit in raw]})
    for instance, state in zip(definition["instances"], staged):
        instance["state"] = state
    provenance = {"max_depth": max_depth, "inputs": deepcopy(routes), "resolved": trace,
                  "semantics": "Index form is inverse implicit routing adjusted for current neck. Bits form is raw before neck XOR. Missing or incompatible targets reject; no modulo alias."}
    definition.setdefault("source", {})["initial_routes"] = deepcopy(provenance)
    return provenance


def apply_extension(actual_model, definition, extension):
    """Atomically append the explicit record after existing-slot resolution.

    No-extension calls are executable no-ops. One addition is supported only for
    the core44-state edition; the enzyme edition already occupies64 state words.
    Native compilation/validation remains mandatory after this authoring step.
    """
    _, prepared = prepare_extended_model(actual_model)
    if not resident.same_structure(prepared, extension):
        raise ValueError("Source catalogue extension changed after preparation")
    if extension is None:
        return {"profile": PROFILE, "added": False, "scope": "No catalogue addition; executable definition unchanged."}
    if definition["state_names"] != base.STATE or len(definition["records"]) != 31:
        raise ValueError("One catalogue addition requires the core44-state edition; the64-state enzyme application has no route_b4 capacity")
    if definition.get("record_value_names") != RECORD_VALUES:
        raise ValueError("Catalogue extension requires the declared20-value resident record layout")
    working = deepcopy(definition)
    original_functions, original_families = list(working["functions"]), list(working["families"])
    key, index = extension["key"], extension["index"]
    functions = {}
    for slot in SLOTS:
        name = f"source_extension__{index}__{slot}"
        _append_function(working, name, CONTRACTS[slot][2], _binding(extension, slot))
        functions[slot] = name
    family_name = f"source_extension__{index}__family"
    if family_name in working["families"]:
        raise ValueError(f"Private extension family name collision: {family_name}")
    interface = max(family["interface"] for family in working["families"].values()) + 1
    working["families"][family_name] = {"interface": interface, "methods": {"99": functions["body"]}}
    working["records"].append({"key": key, "body": family_name, "field": functions["field"],
                               "placement": functions["placement"], "generation": 0,
                               "values": [extension["parameters"][name] for name in RECORD_VALUES],
                               "source_slots": {slot: deepcopy(extension[slot]) for slot in SLOTS}})
    for plan_name in ("mutation_plan", "action_plan"):
        if working[plan_name][0] != [1, 0, 0, 44, 0, 0, 0, 0]:
            raise ValueError("Catalogue extension requires the original initial44-word whole-state read")
        working[plan_name][0][3] = 45
    working["state_names"].append("route_b4")
    for instance in working["instances"]:
        instance["state"]["route_b4"] = 0
    routing = _extend_bst(working)
    retention = _preserve_added_handles(working, index)
    working["action_plan"].append([6, 44, 44, 1, 0, 0, 0, 0])
    working["source"]["stage_boundaries"][-1]["action_step_end_exclusive"] += 1
    source_by_key = {item["key"]: item for item in actual_model["operators"]}
    for record in working["records"]:
        source = source_by_key[record["key"]]
        record["source_slots"] = {slot: deepcopy(source[slot]) for slot in SLOTS}
    if list(working["functions"])[:len(original_functions)] != original_functions or list(working["families"])[:len(original_families)] != original_families:
        raise ValueError("Catalogue extension changed a previous executable handle")
    if len(working["functions"]) > resident.MAX_FUNCTIONS or len(working["families"]) > resident.MAX_FAMILIES:
        raise ValueError("Catalogue extension exceeds a resident bank limit")
    if any(len(working[name]) > resident.MAX_STEPS for name in ("mutation_plan", "action_plan")):
        raise ValueError("Catalogue extension exceeds a resident plan limit")
    metadata = {"profile": PROFILE, "added": True, "record_key": key, "source_index": index,
                "record_ordinal": 31, "record_source_indices": {item["key"]: item["index"] for item in actual_model["operators"]},
                "family": family_name, "functions": functions, "routing": routing, "mutation_retention": retention,
                "function_provenance": {slot: {
                    "source_path": f"operators[31].{slot}.resident_binding.function",
                    "function": name, "function_handle": list(working["functions"]).index(name),
                    "function_sha256": ir.sha256(ir.json_bytes(working["functions"][name])),
                    "source_binding_sha256": ir.sha256(ir.json_bytes(extension[slot]["resident_binding"]["function"])),
                    "contract": {"inputs": CONTRACTS[slot][0], "outputs": CONTRACTS[slot][1], "signature": CONTRACTS[slot][2]},
                } for slot, name in functions.items()},
                "declaration": deepcopy(extension), "declaration_sha256": ir.sha256(ir.json_bytes(extension)),
                "actual_model_semantic_sha256": ir.sha256(ir.json_bytes(actual_model)),
                "existing_slot_resolver_model_scope": "source_slot_bindings provenance refers to the first31-entry model; this extension's actual_model_semantic_sha256 covers the full32-entry model.",
                "scope": "One explicit selected-wave-action record, fixed body family and field/placement programs with common resident numerical anchor/radius/control mutation. All three executable slots come from source declarations; no universal adapter, arbitrary record synthesis or missing-address alias is inferred.",
                "parameter_scope": "All20 record values are supplied by name and retained in the initializer. Existing recurrence conventions determine which values are read or overwritten; supplying a value does not claim it independently affects action."}
    working["source"]["catalogue_extension"] = metadata
    working["source"]["model_semantic_sha256"] = metadata["actual_model_semantic_sha256"]
    working["source"]["selected_route_source_indices"] = [*working["source"].get("selected_route_source_indices", []), index]
    metadata["default_route"] = set_routes(working, [{"index": index}])
    definition.clear()
    definition.update(working)
    return deepcopy(metadata)
