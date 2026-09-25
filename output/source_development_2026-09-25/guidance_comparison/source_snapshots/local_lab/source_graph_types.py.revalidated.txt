"""Versioned nominal wiring contracts for the authored resident source graph.

These contracts distinguish values which happen to occupy identical FP32 words.
They are not a units proof, a range proof, or permission to reinterpret a field.
Numerical guards and resident ABI validation still apply.  Known source-role
edits inherit the exact ordered contract of their signature; an unknown helper
needs an explicit graph contract rather than inference from its expression.
"""
from __future__ import annotations

TYPE_PROFILE = "DWI-GRAPH-TYPES-0.1"
EXTENDED_TYPE_PROFILE = "DWI-GRAPH-TYPES-0.2"
TYPES = frozenset({
    "amplitude", "log_radius", "phase", "interval", "bit", "index",
    "body_handle", "field_handle", "placement_handle", "generation",
    "chart_coordinate", "chart_displacement", "lattice_shift",
    "carrier_distance", "geometric_distance", "slope_scalar",
    "matrix_scalar", "history_scalar", "coupling_scalar",
    "amplitude_squared_norm", "domain_coordinate", "domain_distance",
    "normalized_concentration", "physical_concentration", "objective",
    "coefficient", "control", "reserved_scalar",
})
EXTENDED_TYPES = TYPES | frozenset({
    "program_opcode", "program_index", "program_size", "program_revision",
    "resource_coordinate", "resource_distance", "resource_area",
})


def extension_contracts(definition):
    """Explicit additional state/function contracts; existing laws cannot be relabeled."""
    extension = definition.get("source", {}).get("graph_type_contracts")
    if extension is None:
        return {"states": {}, "functions": {}}
    if (not isinstance(extension, dict) or set(extension) != {"profile", "states", "functions"}
            or extension["profile"] != EXTENDED_TYPE_PROFILE):
        raise ValueError("Expected a DWI-GRAPH-TYPES-0.2 state/function contract declaration")
    states, functions = extension["states"], extension["functions"]
    if not isinstance(states, dict) or not isinstance(functions, dict):
        raise ValueError("Additional state/function contracts must be named mappings")
    if set(states).intersection(_STATE):
        raise ValueError("Additional contracts cannot replace an existing state's meaning")
    if set(states).difference(definition["state_names"]):
        raise ValueError("Unused additional state contracts")
    for name, kind in states.items():
        if not isinstance(name, str) or not name or kind not in EXTENDED_TYPES:
            raise ValueError("Invalid additional state name/type")
    for name, contract in functions.items():
        function = definition["functions"].get(name)
        if function is None:
            raise ValueError("Additional function contract has no numerical definition")
        if _special_contract(name) is not None or function.get("signature") in _CONTRACTS:
            raise ValueError("Additional contracts cannot replace an established source role")
        if not isinstance(contract, dict) or set(contract) != {"inputs", "outputs"}:
            raise ValueError("Additional function needs ordered input/output type maps")
        for direction in ("inputs", "outputs"):
            mapping = contract[direction]
            if not isinstance(mapping, dict) or any(not isinstance(n, str) or not n or t not in EXTENDED_TYPES for n, t in mapping.items()):
                raise ValueError("Invalid additional function name/type")
            if list(mapping) != list(function["binding"][direction]):
                raise ValueError("Additional contract differs from numerical binding's ordered operands")
    return extension

_PAIR = ("ar", "ai", "br", "bi")
_POLAR = ("rho0", "theta0", "rho1", "theta1")
_SLOPES = tuple(f"k{s}_{i}" for s in range(1, 5) for i in range(4))
_HISTORY = tuple(f"B{i}" for i in range(4))
_OBS = ("obs_E", "obs_S", "obs_ES", "obs_P")


def _typed(names, kind):
    return dict.fromkeys(names, kind)


def _join(*parts):
    result = {}
    for part in parts:
        overlap = set(result).intersection(part)
        if overlap:
            raise ValueError(f"Duplicate contract names: {sorted(overlap)}")
        result.update(part)
    return result


_WAVE = _typed(_PAIR, "amplitude")
_POLAR_TYPES = dict(zip(_POLAR, ("log_radius", "phase", "log_radius", "phase")))
_FIELD = {"field_distance": "carrier_distance"}
_B = _typed(_HISTORY, "history_scalar")
_K = {"ku": "chart_coordinate", "kv": "chart_coordinate", "ko": "bit"}
_CHART = {"u": "chart_coordinate", "v": "chart_coordinate", "orientation": "bit"}
_MAT_T = _typed(("t00", "t01", "t10", "t11"), "matrix_scalar")
_MAT_A = _typed(("a00", "a01", "a10", "a11"), "matrix_scalar")
_MAT_A_UPPER = _typed(("A00", "A01", "A10", "A11"), "matrix_scalar")
_Y = _typed(("y0", "y1"), "domain_coordinate")
_OBS_TYPES = _typed(_OBS, "normalized_concentration")
_GEO = _typed(tuple(f"g{i}" for i in range(6)), "geometric_distance")

_STATE = _join(
    _CHART, _WAVE, {"phase": "phase", "dt": "interval", "jitter": "bit"},
    _typed(tuple(f"previous_{n}" for n in _PAIR), "amplitude"),
    _typed(("surface_u", "surface_v"), "chart_coordinate"),
    {"neck": "bit", "route_depth": "index"},
    _typed(tuple(f"route_b{i}" for i in range(5)), "bit"),
    {"K_orientation": "bit"}, _B,
    _typed(("phase_previous", "phase_previous2"), "phase"),
    _typed(("T00", "T01", "T10", "T11", "A00", "A01", "A10", "A11"), "matrix_scalar"),
    _typed(("Rr", "Ri", "Gr", "Gi"), "amplitude"),
    {"selected_index": "index", "last_field": "carrier_distance", "energy": "amplitude_squared_norm"},
    _typed(tuple(f"{n}_normalized" for n in _OBS), "normalized_concentration"),
    _typed(("enzyme_y0", "enzyme_y1", "enzyme_trial_y0", "enzyme_trial_y1"), "domain_coordinate"),
    _typed(("enzyme_objective", "enzyme_improvement", "enzyme_gap_estimate", "enzyme_previous_objective"), "objective"),
    _typed(("enzyme_trial_sdf", "enzyme_projection_distance"), "domain_distance"),
    {"enzyme_accepted": "bit", "enzyme_step": "coefficient"},
    _typed(("enzyme_E_uM", "enzyme_S_uM", "enzyme_ES_uM", "enzyme_P_uM"), "physical_concentration"),
)

_RECORD_HEADER = {"body": "body_handle", "field": "field_handle",
                  "placement": "placement_handle", "generation": "generation"}
_RECORD_VALUES = {
    "anchor_u": "chart_coordinate", "anchor_v": "chart_coordinate", "anchor_orientation": "bit",
    "radius": "carrier_distance", "phase_gain": "coefficient",
    "shift_u": "chart_displacement", "shift_v": "chart_displacement",
    "placement_scale": "chart_displacement", "control": "control",
    "du": "chart_displacement", "dv": "chart_displacement", "feedback_gain": "coefficient",
    "last_mutator_field": "carrier_distance", "previous_body_handle": "body_handle",
    "last_pinion_field": "carrier_distance",
    **_typed(tuple(f"reserved_{i}" for i in range(5)), "reserved_scalar"),
}


def _ordered_names(names, known, where):
    if not isinstance(names, list) or any(not isinstance(n, str) for n in names) or len(set(names)) != len(names):
        raise ValueError(f"{where}: expected unique ordered names")
    unknown = set(names).difference(known)
    if unknown:
        raise ValueError(f"{where}: no {TYPE_PROFILE} contract for {sorted(unknown)}")
    return {name: known[name] for name in names}


def state_types(definition):
    """Return named state types in the actual definition's word order."""
    return _ordered_names(definition["state_names"], _join(_STATE, extension_contracts(definition)["states"]), "state_names")


def record_types(definition):
    """Return all 24 ABI word types, with the four header words first."""
    values = _ordered_names(definition["record_value_names"], _RECORD_VALUES, "record_value_names")
    if len(values) != 20:
        raise ValueError("record_value_names: this type edition requires exactly 20 value words")
    return _join(_RECORD_HEADER, values)


def _contract(inputs, outputs):
    return {"inputs": dict(inputs), "outputs": dict(outputs)}


def _bst_contract(five=False):
    return _contract(_join({"depth": "index"}, _typed(tuple(f"b{i}" for i in range(5 if five else 4)), "bit"),
                           {"neck": "bit", "jitter": "bit"}, _FIELD),
                     {"index": "index", "routing_phase": "phase"})


_MUTATION = _join(
    {"old_body": "body_handle", "target_index": "index"}, _FIELD, _WAVE,
    {"jitter": "bit", "old_control": "control", "mutator_control": "control",
     "target_field": "carrier_distance", "dt": "interval"})
_MUTATION_ENZYME = _join(_MUTATION, {"domain_trial_sdf": "domain_distance",
                                    "domain_improvement": "objective", "domain_accepted": "bit"})

# Signatures are fixed by the existing numerical source edition, not inferred
# from arbitrary scalar spellings (g0 and ar have several different roles).
_CONTRACTS = {
    1: _contract(_join(_WAVE, {"phase": "phase"}), _WAVE),
    2: _contract(_MUTATION, {"body_handle": "body_handle", "control": "control"}),
    3: _contract(_join(_CHART, _WAVE, _FIELD, {"dt": "interval", "du": "chart_displacement", "dv": "chart_displacement",
                  "surface_u": "chart_coordinate", "surface_v": "chart_coordinate", "old_placement": "placement_handle", "jitter": "bit"}),
                 _join(_CHART, {"placement_handle": "placement_handle"})),
    4: _contract({"dx": "chart_displacement", "dy": "chart_displacement", "radius": "carrier_distance"}, {"distance": "carrier_distance"}),
    5: _contract(_CHART, _CHART),
    6: _contract({"query_u": "chart_coordinate", "query_v": "chart_coordinate", "anchor_u": "chart_coordinate",
                  "anchor_v": "chart_coordinate", "anchor_orientation": "bit"},
                 {"dx": "chart_displacement", "dy": "chart_displacement", "lift_m": "lattice_shift", "anchor_frame_y": "chart_displacement"}),
    7: _contract({"old_field": "field_handle", "new_body": "body_handle", "new_u": "chart_coordinate", "new_v": "chart_coordinate",
                  "old_radius": "carrier_distance", "surface_u": "chart_coordinate", "surface_v": "chart_coordinate"},
                 {"field_handle": "field_handle", "radius": "carrier_distance"}),
    8: _contract({"generation": "generation"}, {"generation": "generation"}),
    11: _contract(_join(_POLAR_TYPES, {"phase": "phase", "parity": "bit"}, _FIELD), _WAVE),
    12: _contract(_join(_K, _typed(("Rr", "Ri", "Gr", "Gi"), "amplitude"), _B, _MAT_A, _FIELD), _join(_WAVE, _CHART)),
    90: _contract(_join(_WAVE, {"routing_phase": "phase"}, _FIELD), _WAVE),
    100: _contract(_join(_K, _WAVE, {"feedback_dx": "chart_displacement", "feedback_y": "chart_displacement", "feedback_orientation": "bit"}, _FIELD), _K),
    101: _contract(_join(_WAVE, _FIELD), _POLAR_TYPES),
    102: _contract(_join(_POLAR_TYPES, {"jitter": "bit"}, _FIELD), _POLAR_TYPES),
    103: _contract(_join({"split_theta0": "phase", "split_theta1": "phase", "jitter": "bit", "neck": "bit"}, _FIELD), {"parity": "bit", "phase": "phase"}),
    104: _bst_contract(),
    105: _contract(_join(_WAVE, {"dt": "interval", "jitter": "bit"}, _FIELD), _join(_typed(_PAIR, "slope_scalar"), {"h": "interval"})),
    106: _contract(_join(_WAVE, {"dt": "interval"}, _typed(_SLOPES, "slope_scalar"), _FIELD), _WAVE),
    107: _contract(_join(_WAVE, _typed(("k0", "k1", "k2", "k3"), "slope_scalar"), {"h": "interval", "fraction": "coefficient"}), _WAVE),
    108: _contract(_join(_typed(_PAIR, "slope_scalar"), _FIELD), _typed(_PAIR, "slope_scalar")),
    **{signature: _contract(_join(_WAVE, _FIELD), {"value": "geometric_distance"}) for signature in range(109, 115)},
    115: _contract(_join({"phase": "phase", "previous": "phase", "previous2": "phase", "jitter": "bit", "dt": "interval"}, _FIELD),
                   {"delta": "phase", "unwrapped": "phase"}),
    116: _contract(_join({"delta": "phase"}, _GEO, {"dt": "interval"}, _FIELD), _WAVE),
    117: _contract(_join(_WAVE, _typed(("g0", "g1", "g2", "g3"), "amplitude"), _FIELD), _join(_WAVE, {"score": "coupling_scalar"})),
    118: _contract(_join(_WAVE, {"score": "coupling_scalar"}, _typed(tuple(f"growth{i}" for i in range(4)), "amplitude"), _GEO, _FIELD), _WAVE),
    119: _contract(_join(_WAVE, _FIELD), _WAVE),
    120: _contract(_join(_WAVE, {"parity": "bit"}, _FIELD), _WAVE),
    121: _contract(_join(_B, {"jitter": "bit"}, _typed(_SLOPES, "slope_scalar"), _FIELD), _B),
    122: _contract(_join(_WAVE, {"crystal_ar": "amplitude"}, _FIELD), _MAT_T),
    123: _contract(_join(_MAT_T, _FIELD), _MAT_A),
    124: _contract(_join(_WAVE, _CHART, {"neck": "bit", "parity": "bit", "phase": "phase", "dt": "interval"}, _FIELD),
                   _join(_WAVE, _CHART, {"phase": "phase"})),
    125: _contract(_join(_POLAR_TYPES, _FIELD), _WAVE),
    126: _contract(_join({"jitter": "bit"}, _FIELD), {"bit": "bit", "phase": "phase"}),
    127: _contract(_join({"dt": "interval"}, _FIELD), {"dt": "interval"}),
    128: _contract(_join({"value": "coefficient", "threshold": "coefficient"}, _FIELD), {"bit": "bit"}),
    129: _contract(_FIELD, {"unsupported": "control"}),
    130: _contract({"a": "phase", "b": "phase"}, {"phase": "phase"}),
    131: _contract(_WAVE, {"energy": "amplitude_squared_norm"}),
    132: _contract(_join(_Y, _OBS_TYPES, _WAVE, _B, _MAT_A_UPPER, {"dt": "interval"}, _FIELD),
                   {"trial_y0": "domain_coordinate", "trial_y1": "domain_coordinate", "step": "coefficient"}),
    133: _contract(_Y, {"distance": "domain_distance", "boundary_y0": "domain_coordinate", "boundary_y1": "domain_coordinate"}),
    134: _contract(_join({"trial_y0": "domain_coordinate", "trial_y1": "domain_coordinate", "distance": "domain_distance",
                         "boundary_y0": "domain_coordinate", "boundary_y1": "domain_coordinate"}, _OBS_TYPES),
                   {"candidate_y0": "domain_coordinate", "candidate_y1": "domain_coordinate", "objective": "objective", "projection_distance": "domain_distance"}),
    135: _contract(_join(_typed(("incumbent_y0", "incumbent_y1", "candidate_y0", "candidate_y1"), "domain_coordinate"),
                         _typed(("incumbent_objective", "candidate_objective"), "objective"), _OBS_TYPES),
                   _join(_Y, {"objective": "objective", "improvement": "objective", "accepted": "bit"})),
    136: _contract(_join(_Y, _OBS_TYPES), _join(_typed(("E_uM", "S_uM", "ES_uM", "P_uM"), "physical_concentration"),
                                              {"objective": "objective", "gap_estimate": "objective"})),
}


def _special_contract(function_name):
    if function_name == "source_extension__bst_five_bits":
        return _bst_contract(five=True)
    if function_name in ("source_slot__preserve_field", "source_slot__preserve_placement"):
        kind = "field_handle" if function_name.endswith("field") else "placement_handle"
        return _contract({"old_handle": kind, "proposed_handle": kind, "source_index": "index"}, {"handle": kind})
    if function_name == "source_extension__preserve_handles":
        return _contract({"source_index": "index", "old_body": "body_handle", "old_field": "field_handle", "old_placement": "placement_handle",
                          "new_body": "body_handle", "new_field": "field_handle", "new_placement": "placement_handle"},
                         {"body": "body_handle", "field": "field_handle", "placement": "placement_handle"})
    return None


def function_contract(definition, function_name):
    """Return an exact ordered scalar contract for a known bank function.

    A source-slot replacement keeps the original signature and operand names.
    Its private generated name therefore does not weaken nominal validation.
    The three extension/retention helpers use their explicit name contracts,
    since their signatures are allocated after the edition's fixed bank.
    """
    functions = definition["functions"]
    if function_name not in functions:
        raise ValueError(f"Unknown function: {function_name}")
    function = functions[function_name]
    signature = function.get("signature")
    if type(signature) is not int or signature <= 0:
        raise ValueError(f"Function {function_name}: expected a positive integer signature")
    binding = function["binding"]
    additional = extension_contracts(definition)["functions"].get(function_name)
    if additional is not None:
        return _contract(additional["inputs"], additional["outputs"])
    expected = _special_contract(function_name)
    if expected is None:
        expected = _CONTRACTS.get(signature)
        if signature == 2 and binding.get("inputs") == list(_MUTATION_ENZYME):
            expected = _contract(_MUTATION_ENZYME, _CONTRACTS[2]["outputs"])
    if expected is None:
        raise ValueError(f"Function {function_name}: no {TYPE_PROFILE} contract for signature {signature}; declare a graph helper contract")
    if binding.get("inputs") != list(expected["inputs"]) or list(binding.get("outputs", {})) != list(expected["outputs"]):
        raise ValueError(f"Function {function_name}: ordered operands differ from its {TYPE_PROFILE} signature contract")
    return _contract(expected["inputs"], expected["outputs"])


def record_contract(definition, key, slot, role=0):
    """Get a current-record call contract, checking all compatible body variants.

    ``key`` is a declared record key, ``slot`` is body/field/placement, and role
    is an integer (or canonical decimal string).  Dynamic selected calls use
    the declared reference contract, e.g. circle/body/99.  This function does
    not grant old/published bank access or dynamic routing permission.
    """
    if slot not in ("body", "field", "placement"):
        raise ValueError(f"Unknown record slot: {slot}")
    if isinstance(role, str) and role.isdecimal() and str(int(role)) == role:
        role = int(role)
    if type(role) is not int or role < 0:
        raise ValueError("Record role must be a nonnegative integer")
    matches = [record for record in definition["records"] if record.get("key") == key]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one record with key {key!r}")
    record = matches[0]
    if slot != "body":
        if role != 0:
            raise ValueError("Field and placement calls require role zero")
        name = record[slot]
        required = 4 if slot == "field" else 5
        if definition["functions"][name]["signature"] != required:
            raise ValueError(f"Record {key}.{slot}: expected fixed signature {required}")
        return function_contract(definition, name)
    families = definition["families"]
    family = families[record["body"]]
    expected, signature = None, None
    for family_name, candidate in families.items():
        if candidate["interface"] != family["interface"]:
            continue
        name = candidate["methods"].get(str(role))
        if name is None:
            raise ValueError(f"Compatible family {family_name} has no role {role}")
        contract = function_contract(definition, name)
        current_signature = definition["functions"][name]["signature"]
        if expected is not None and (contract != expected or current_signature != signature):
            raise ValueError(f"Compatible family {family_name} changes role {role}'s contract")
        expected, signature = contract, current_signature
    return expected
