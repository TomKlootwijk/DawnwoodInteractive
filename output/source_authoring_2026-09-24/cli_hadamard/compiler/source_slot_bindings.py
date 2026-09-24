"""Resolve explicit source-slot declarations into the existing resident edition.

This module adds no numerical meanings to arbitrary symbolic JSON. The original
declarations keep their versioned cycle bindings. A changed declaration needs
an inline resident_binding or an exactly matched external registry entry.
The caller generates the canonical cycle/enzyme first, then applies resolutions
to that final typed bank before passing it to source_resident_v2.
"""
from __future__ import annotations

from copy import deepcopy

try:
    from . import source_cycle as base
    from . import source_ir_v2 as ir
    from . import source_resident_v2 as resident
except ImportError:
    import source_cycle as base
    import source_ir_v2 as ir
    import source_resident_v2 as resident


PROFILE = "DWI-SOURCE-SLOTS-0.1"
SLOTS = ("body", "field", "placement")
PROTECTED_ENZYME_ROLES = frozenset(("0", "101", "102", "103", "104"))


def _object(value, where):
    if not isinstance(value, dict):
        raise ValueError(f"{where}: expected an object")
    return value


def _name(value, where):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{where}: expected a nonempty string")
    return value


def _original_slots(symbol):
    return {"body": {"symbol": symbol}, "field": {"symbol": symbol + "_SDF"},
            "placement": {"symbol": "Phyllotaxis_on_Klein"}}


def _validate_slot_binding(binding, slot, where):
    """Validate declaration shape here; role contracts require the final bank."""
    required = {"kind", "variants", "mutation_policy"} if slot == "body" else {
        "kind", "function", "mutation_policy"}
    ir.exact_keys(binding, required, required, where)
    if binding["kind"] != slot:
        raise ValueError(f"{where}.kind: expected {slot!r}")
    policy = "declared_variants" if slot == "body" else "preserve_program"
    if binding["mutation_policy"] != policy:
        raise ValueError(f"{where}.mutation_policy: expected {policy!r}")
    if slot != "body":
        ir.validate_binding(binding["function"], where + ".function")
        return
    variants = _object(binding["variants"], where + ".variants")
    if not variants:
        raise ValueError(f"{where}.variants: at least one explicit family is required")
    for name, variant in variants.items():
        _name(name, where + ".variant name")
        location = f"{where}.variants[{name!r}]"
        ir.exact_keys(variant, {"inherit", "roles"}, {"roles"}, location)
        if "inherit" in variant and type(variant["inherit"]) is not bool:
            raise ValueError(f"{location}.inherit: expected a Boolean")
        roles = _object(variant["roles"], location + ".roles")
        for role, function in roles.items():
            if (not isinstance(role, str) or not role.isascii() or not role.isdecimal()
                    or str(int(role)) != role or int(role) > ir.UINT32_MAX):
                raise ValueError(f"{location}: role keys must be canonical uint32 strings")
            ir.validate_binding(function, f"{location}.roles[{role!r}]")


def prepare_model(actual_model, registry=None):
    """Return (canonical_model, resolutions) without changing caller objects.

    registry = {"profile": PROFILE, "entries": [
        {"key": "circle", "slot": "body", "declaration": <exact source JSON>,
         "binding": <slot binding>} ]}

    An inline slot is exactly {"resident_binding": <slot binding>}. It cannot
    also have a registry entry. Existing record identities/order remain fixed;
    this resolver does not add records, infer source expressions or import DAGs.
    Seed and cycle validation remain with base.build_definition, using the
    unchanged seed carried in the canonical model.
    """
    _object(actual_model, "source model")
    operators = actual_model.get("operators")
    if not isinstance(operators, list) or len(operators) != len(base.CATALOGUE):
        raise ValueError("Source-slot resolution requires exactly the existing 31 records")
    explicit = {}
    if registry is not None:
        ir.exact_keys(registry, {"profile", "entries"}, {"profile", "entries"}, "slot registry")
        if registry["profile"] != PROFILE:
            raise ValueError(f"slot registry.profile: expected {PROFILE}")
        if not isinstance(registry["entries"], list):
            raise ValueError("slot registry.entries: expected an array")
        for position, entry in enumerate(registry["entries"]):
            where = f"slot registry.entries[{position}]"
            ir.exact_keys(entry, {"key", "slot", "declaration", "binding"},
                          {"key", "slot", "declaration", "binding"}, where)
            key = _name(entry["key"], where + ".key")
            slot = entry["slot"]
            if slot not in SLOTS:
                raise ValueError(f"{where}.slot: expected body, field or placement")
            identity = (key, slot)
            if identity in explicit:
                raise ValueError(f"{where}: duplicate binding for {key}.{slot}")
            _validate_slot_binding(entry["binding"], slot, where + ".binding")
            explicit[identity] = (entry, position)
    canonical = deepcopy(actual_model)
    resolutions = []
    consumed = set()
    for index, (key, symbol) in enumerate(base.CATALOGUE):
        entry = _object(operators[index], f"source operators[{index}]")
        if entry.get("key") != key or type(entry.get("index")) is not int or entry["index"] != index:
            raise ValueError(f"Source record {index} must retain key {key!r} and index {index}")
        if "parameters" in entry:
            raise ValueError(f"Source record {key}: record parameters need a separate explicit edition binding")
        for slot, original in _original_slots(symbol).items():
            if slot not in entry:
                raise ValueError(f"Source record {key}: missing {slot} declaration")
            declaration = entry[slot]
            identity = (key, slot)
            inline = isinstance(declaration, dict) and "resident_binding" in declaration
            if inline:
                ir.exact_keys(declaration, {"resident_binding"}, {"resident_binding"}, f"{key}.{slot}")
                if identity in explicit:
                    raise ValueError(f"{key}.{slot}: inline and external bindings are ambiguous")
                binding = declaration["resident_binding"]
                _validate_slot_binding(binding, slot, f"{key}.{slot}.resident_binding")
                origin = "inline"
            elif identity in explicit:
                supplied, position = explicit[identity]
                if not resident.same_structure(supplied["declaration"], declaration):
                    raise ValueError(f"{key}.{slot}: registry declaration does not exactly match the source")
                binding = supplied["binding"]
                consumed.add(identity)
                origin = "registry"
            else:
                if not resident.same_structure(declaration, original):
                    raise ValueError(f"{key}.{slot}: changed declaration has no explicit resident binding")
                continue
            canonical["operators"][index][slot] = deepcopy(original)
            location = {"source_document": "model", "source_pointer": f"/operators/{index}/{slot}",
                        "binding_document": "model" if origin == "inline" else "registry",
                        "binding_pointer": (f"/operators/{index}/{slot}/resident_binding" if origin == "inline"
                                            else f"/entries/{position}/binding")}
            if origin == "registry":
                location["registry_semantic_sha256"] = ir.sha256(ir.json_bytes(registry))
            resolutions.append({"key": key, "index": index, "slot": slot,
                                "declaration": deepcopy(declaration), "binding": deepcopy(binding),
                                "origin": origin, "location": location})
    unused = set(explicit) - consumed
    if unused:
        raise ValueError(f"Unused slot registry entries: {sorted(unused)}")
    # The original validator checks seed, T interpretation and canonical slots.
    # Its cycle argument is only a validation fixture, not a caller cycle edit.
    base.validate_sources(canonical, {"phases": list(base.PHASES),
                                      "fourth_rk4_slot": {"y_up_applications": 2}})
    return canonical, resolutions


def _contract_binding(binding, original, where):
    ir.validate_binding(binding, where)
    if binding["inputs"] != original["inputs"]:
        raise ValueError(f"{where}: ordered input names must match {original['inputs']!r}")
    if list(binding["outputs"]) != list(original["outputs"]):
        raise ValueError(f"{where}: ordered output names must match {list(original['outputs'])!r}")
    original_guards = original.get("requires", [])
    replacement_guards = binding.get("requires", [])
    if (len(replacement_guards) < len(original_guards)
            or not resident.same_structure(replacement_guards[:len(original_guards)], original_guards)):
        raise ValueError(f"{where}: original ordered numerical guards must remain an unchanged prefix")
    compiler = ir.ExpressionCompiler(binding["inputs"])
    for index, condition in enumerate(binding.get("requires", [])):
        register = compiler.expression(condition, f"{where}.requires[{index}]")
        compiler._emit(17, register)
    for name, expression in binding["outputs"].items():
        compiler.expression(expression, f"{where}.outputs[{name!r}]")


def _private_function(definition, label, original, binding):
    name = "source_slot__" + label
    if name in definition["functions"]:
        raise ValueError(f"Private binding function name collision: {name}")
    definition["functions"][name] = {"signature": original["signature"], "binding": deepcopy(binding)}
    return name


def _frame_usage(plan, definition):
    """Conservative whole-plan frame usage for fresh scratch allocation."""
    functions = list(definition["functions"].values())
    signatures = {f["signature"]: (len(f["binding"]["inputs"]), len(f["binding"]["outputs"]))
                  for f in functions}
    used = set()
    def mark(start, width):
        used.update(range(start, start + width))
    for row in plan:
        op = row[0]
        if op in (0, 8, 9):
            mark(row[1], 1)
        elif op == 1:
            mark(row[1], row[3])
        elif op == 2:
            mark(row[1], row[4])
        elif op == 3:
            binding = functions[row[1]]["binding"]
            mark(row[2], len(binding["inputs"])); mark(row[3], len(binding["outputs"]))
        elif op in (4, 11):
            ins, outs = signatures[row[6]]
            mark(row[4], ins); mark(row[5], outs)
            if op == 11:
                mark(row[1], 1)
        elif op in (5, 6):
            mark(row[2], row[3])
        elif op == 7:
            mark(row[1], 1)
        elif op == 10:
            mark(row[1], row[3]); mark(row[2], row[3])
        elif op == 12:
            mark(row[1], row[4]); mark(row[2], 1)
        else:
            raise ValueError(f"Unsupported plan opcode in source-slot mutation adapter: {op}")
    return used


def _preserve_slot_programs(definition, indices_by_slot):
    """Retain declared custom programs while preserving proposed record values."""
    if not indices_by_slot:
        return []
    plan = definition["mutation_plan"]
    writes = [i for i, row in enumerate(plan) if row[0] == 5]
    if len(writes) != 1:
        raise ValueError("Custom field/placement requires one final whole-record mutation write")
    write_step = writes[0]
    write = plan[write_step]
    if write_step != len(plan) - 1 or write[1] != 0 or write[3] != resident.RECORD_WORDS:
        raise ValueError("Custom field/placement requires the authored final 24-word mutation write")
    reads = [row for row in plan[:write_step]
             if row[0] == 2 and row[2] == resident.TARGET and row[3:6] == [0, 24, 0]]
    indices = [row for row in plan[:write_step] if row[0] == 9]
    if len(reads) != 1 or len(indices) != 1:
        raise ValueError("Custom field/placement requires one old-target record read and source-index load")
    old_base, proposal_base, source_register = reads[0][1], write[2], indices[0][1]
    used = _frame_usage(plan, definition)
    scratch = next((start for start in range(resident.FRAME_WORDS - 3, -1, -1)
                    if all(start + i not in used for i in range(3))), None)
    if scratch is None:
        raise ValueError("No independent three-register mutation scratch span for source-slot retention")
    inserted, witnesses = [], []
    for slot in ("field", "placement"):
        source_indices = indices_by_slot.get(slot)
        if not source_indices:
            continue
        slot_word = SLOTS.index(slot)
        expression = {"input": "proposed_handle"}
        for index in reversed(sorted(source_indices)):
            source = {"input": "source_index"}
            equal = {"op": "sub", "args": [1, {"op": "max", "args": [
                {"op": "less", "args": [source, index]},
                {"op": "less", "args": [index, source]}]}]}
            expression = {"op": "select", "args": [equal, {"input": "old_handle"}, expression]}
        name = "source_slot__preserve_" + slot
        if name in definition["functions"]:
            raise ValueError(f"Private binding function name collision: {name}")
        signature = max(f["signature"] for f in definition["functions"].values()) + 1
        binding = {"inputs": ["old_handle", "proposed_handle", "source_index"],
                   "outputs": {"handle": expression},
                   "source": PROFILE + " explicit preserve_program policy",
                   "meaning": "Retain only the old custom program handle for listed source indices; proposed anchors, radii, generations and controls remain unchanged.",
                   "status": "Authored source-slot mutation adapter."}
        definition["functions"][name] = {"signature": signature, "binding": binding}
        handle = list(definition["functions"]).index(name)
        for offset, source in enumerate((old_base + slot_word, proposal_base + slot_word, source_register)):
            inserted.append([10, scratch + offset, source, 1, 0, 0, 0, 0])
        call_step = write_step + len(inserted)
        inserted.append([3, handle, scratch, proposal_base + slot_word, 0, 0, 0, 0])
        witnesses.append({"slot": slot, "source_indices": sorted(source_indices), "function": name,
                          "step": call_step, "inputs": [old_base + slot_word, proposal_base + slot_word, source_register],
                          "argument_base": scratch, "output_base": proposal_base + slot_word})
    plan[write_step:write_step] = inserted
    calls = definition.setdefault("source", {}).setdefault("mutation_calls", [])
    for call in calls:
        if call.get("step", -1) >= write_step:
            call["step"] += len(inserted)
    calls.extend({"step": item["step"], "helper": item["function"], "inputs": item["inputs"],
                  "output_base": item["output_base"]} for item in witnesses)
    return witnesses


def apply_resolutions(actual_model, definition, resolutions):
    """Atomically mutate the generated final definition and return provenance.

    All reachable variants of an edited body interface must be accounted for.
    Exact ordered contracts, existing family handles and scientific law identity
    are preserved. Native validation/compilation is still required afterwards.
    The no-resolution path changes metadata only, never executable program data.
    """
    if not isinstance(resolutions, list):
        raise ValueError("resolutions: expected the array returned by prepare_model")
    _object(actual_model, "actual source model")
    operators = actual_model.get("operators")
    if not isinstance(operators, list) or len(operators) != len(base.CATALOGUE):
        raise ValueError("Source-slot application requires exactly the existing 31 source records")
    resolved_identities = set()
    for resolution in resolutions:
        ir.exact_keys(resolution, {"key", "index", "slot", "declaration", "binding", "origin", "location"},
                      {"key", "index", "slot", "declaration", "binding", "origin", "location"}, "resolution")
        key = _name(resolution["key"], "resolution.key")
        slot = resolution["slot"]
        if slot not in SLOTS:
            raise ValueError("resolution.slot: expected body, field or placement")
        if (key, slot) in resolved_identities:
            raise ValueError(f"Duplicate resolution for {key}.{slot}")
        resolved_identities.add((key, slot))
        if resolution["origin"] not in ("inline", "registry"):
            raise ValueError("resolution.origin: expected inline or registry")
    canonical_context = deepcopy(actual_model)
    for index, (key, symbol) in enumerate(base.CATALOGUE):
        entry = _object(operators[index], f"source operators[{index}]")
        if entry.get("key") != key or type(entry.get("index")) is not int or entry["index"] != index:
            raise ValueError(f"Source record {index} must retain key {key!r} and index {index}")
        if "parameters" in entry:
            raise ValueError(f"Source record {key}: unbound record parameters")
        for slot, original in _original_slots(symbol).items():
            if slot not in entry or ((key, slot) not in resolved_identities
                                     and not resident.same_structure(entry[slot], original)):
                raise ValueError(f"{key}.{slot}: actual source declaration has not been resolved")
            canonical_context["operators"][index][slot] = deepcopy(original)
    base.validate_sources(canonical_context, {"phases": list(base.PHASES),
                                              "fourth_rk4_slot": {"y_up_applications": 2}})
    if definition.get("source", {}).get("model_semantic_sha256") != ir.sha256(ir.json_bytes(canonical_context)):
        raise ValueError("Generated definition does not identify the canonical form of this actual source model")
    working = deepcopy(definition)
    records = working["records"]
    by_key = {record["key"]: record for record in records}
    if len(by_key) != len(records):
        raise ValueError("Generated definition has duplicate record keys")
    source_operators = {item["key"]: item for item in actual_model["operators"]}
    families = working["families"]
    functions = working["functions"]
    original_family_order = list(families)
    old_function_order = list(functions)
    enzyme = working.get("source", {}).get("enzyme")
    protected = {}
    if enzyme is not None:
        blend_interface = families["blend"]["interface"]
        for name, family in families.items():
            if family["interface"] == blend_interface:
                protected[name] = {role: family["methods"][role] for role in PROTECTED_ENZYME_ROLES}
        for role in PROTECTED_ENZYME_ROLES:
            if len({methods[role] for methods in protected.values()}) != 1:
                raise ValueError(f"Existing enzyme protected role {role} already differs between families")
    applied, preserve, seen = [], {}, set()
    for resolution in resolutions:
        ir.exact_keys(resolution, {"key", "index", "slot", "declaration", "binding", "origin", "location"},
                      {"key", "index", "slot", "declaration", "binding", "origin", "location"}, "resolution")
        key, slot = resolution["key"], resolution["slot"]
        if key not in by_key or key not in source_operators or slot not in SLOTS:
            raise ValueError("Resolution refers to an absent record or unsupported slot")
        identity = (key, slot)
        if identity in seen:
            raise ValueError(f"Duplicate resolution for {key}.{slot}")
        seen.add(identity)
        source = source_operators[key]
        if type(resolution["index"]) is not int or resolution["index"] != source["index"]:
            raise ValueError(f"{key}.{slot}: source index changed after preparation")
        if not resident.same_structure(resolution["declaration"], source[slot]):
            raise ValueError(f"{key}.{slot}: source declaration changed after preparation")
        binding = resolution["binding"]
        if resolution["origin"] == "inline":
            declaration = source[slot]
            if (not isinstance(declaration, dict) or set(declaration) != {"resident_binding"}
                    or not resident.same_structure(declaration["resident_binding"], binding)):
                raise ValueError(f"{key}.{slot}: inline resolution differs from the source binding")
        _validate_slot_binding(binding, slot, f"{key}.{slot}")
        record = by_key[key]
        details = {"key": key, "source_index": source["index"], "slot": slot,
                   "origin": resolution["origin"], "declaration": deepcopy(source[slot]),
                   "location": deepcopy(resolution["location"]),
                   "declaration_sha256": ir.sha256(ir.json_bytes(source[slot])),
                   "binding_sha256": ir.sha256(ir.json_bytes(binding)),
                   "mutation_policy": binding["mutation_policy"], "functions": []}
        if slot == "body":
            interface = families[record["body"]]["interface"]
            expected = {name for name, family in families.items() if family["interface"] == interface}
            if set(binding["variants"]) != expected:
                raise ValueError(f"{key}.body: explicitly account for all compatible variants {sorted(expected)}")
            details["variants"] = {}
            for family_name, variant in binding["variants"].items():
                methods = families[family_name]["methods"]
                roles = variant["roles"]
                unknown = set(roles) - set(methods)
                if unknown:
                    raise ValueError(f"{key}.{family_name}: undeclared roles {sorted(unknown)}")
                if not variant.get("inherit", False) and set(roles) != set(methods):
                    raise ValueError(f"{key}.{family_name}: every role needs a definition unless inherit is explicitly true")
                if family_name in protected and set(roles) & PROTECTED_ENZYME_ROLES:
                    raise ValueError(f"{key}.{family_name}: enzyme roles0/101..104 must inherit protected laws")
                changed = {}
                for role, replacement in roles.items():
                    original_name = methods[role]
                    original = functions[original_name]
                    _contract_binding(replacement, original["binding"], f"{key}.{family_name}.role{role}")
                    name = _private_function(working, f"{key}__{family_name}__role{role}", original, replacement)
                    methods[role] = name
                    changed[role] = {"original_function": original_name, "function": name,
                                     "sha256": ir.sha256(ir.json_bytes(functions[name]))}
                    details["functions"].append(name)
                details["variants"][family_name] = {"replaced_roles": changed,
                                                     "inherited_roles": sorted(set(methods) - set(roles))}
        else:
            original_name = record[slot]
            original = functions[original_name]
            replacement = binding["function"]
            _contract_binding(replacement, original["binding"], f"{key}.{slot}.function")
            name = _private_function(working, f"{key}__{slot}", original, replacement)
            record[slot] = name
            preserve.setdefault(slot, set()).add(source["index"])
            details.update(original_function=original_name, function=name,
                           function_sha256=ir.sha256(ir.json_bytes(functions[name])))
            details["functions"].append(name)
        applied.append(details)
    for name, methods in protected.items():
        if any(families[name]["methods"][role] != function for role, function in methods.items()):
            raise ValueError("Source-slot resolution changed a protected enzyme law")
    retention = _preserve_slot_programs(working, preserve)
    if list(families) != original_family_order or list(functions)[:len(old_function_order)] != old_function_order:
        raise ValueError("Source-slot resolution changed existing family/function handle ordering")
    if len(functions) > resident.MAX_FUNCTIONS:
        raise ValueError("Source-slot resolution exceeds the resident function-bank limit")
    if len(working["mutation_plan"]) > resident.MAX_STEPS:
        raise ValueError("Source-slot resolution exceeds the resident mutation-plan limit")
    for record in records:
        if record["key"] not in source_operators:
            raise ValueError("Generated record is absent from the actual source model")
        record["source_slots"] = {slot: deepcopy(source_operators[record["key"]][slot]) for slot in SLOTS}
    provenance = {
        "profile": PROFILE, "resolutions": applied, "mutation_program_retention": retention,
        "actual_model_semantic_sha256": ir.sha256(ir.json_bytes(actual_model)),
        "existing_family_handles_preserved": True, "existing_function_handles_preserved": True,
        "scope": "Explicit existing-record slot bindings, exact named role contracts and finite authored variant coverage; no arbitrary symbolic-DAG lowering or runtime program synthesis.",
        "evidence_scope": "Bindings and stage topology remain inspectable; baseline numerical accuracy and causal observations do not transfer automatically to an edited program.",
    }
    metadata = working.setdefault("source", {})
    metadata["source_slot_bindings"] = provenance
    metadata["model_semantic_sha256"] = provenance["actual_model_semantic_sha256"]
    metadata["source_slot_policy"] = "Original declarations retain their authored numerical laws; altered or explicitly rebound declarations resolve through DWI-SOURCE-SLOTS-0.1. Unknown meanings fail."
    if enzyme is not None and ("blend", "body") in seen:
        enzyme["proposal_functions"] = [families[name]["methods"]["100"] for name in enzyme["proposal_families"]]
    if enzyme is not None and any(key == "blend" for key, slot in seen):
        enzyme["base_source_record"] = deepcopy(enzyme["source_record"])
        enzyme["source_record"] = {"key": "blend", "index": source_operators["blend"]["index"],
                                   "source_slots": deepcopy(by_key["blend"]["source_slots"])}
    definition.clear()
    definition.update(working)
    return deepcopy(provenance)
