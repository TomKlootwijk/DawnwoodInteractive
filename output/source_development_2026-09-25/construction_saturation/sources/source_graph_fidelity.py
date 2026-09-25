"""Structural source obligations for a declared resident application graph.

This audit checks named edges and execution order, not numerical sensitivity,
scientific correctness or equivalence of arbitrary authored expressions. Schema,
nominal types, expression validation and tape validation belong to the compiler.
"""
from __future__ import annotations

import json

PHASES = ("operator_mutation", "log_polar", "split_and_hinge", "selected_operator",
          "rk4_four_slots", "geometry_divergence", "rgba_crystal", "surface_return")
PAIR = ("ar", "ai", "br", "bi")
GEOMETRY = ("T_shape", "pyramid", "circle", "cone", "sphere", "apex")


def _fail(message):
    raise ValueError("Source graph fidelity: " + message)


def _identity(record):
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class _Graph:
    def __init__(self, scope, groups):
        self.scope, self.nodes, self.by_id, self.phase, self.order = scope, [], {}, {}, {}
        self.cache = {}
        for phase, nodes in groups:
            for node in nodes:
                name = node.get("id")
                if not isinstance(name, str) or not name or name in self.by_id:
                    _fail(f"{scope}: missing or duplicate node identity {name!r}")
                self.by_id[name] = node
                self.phase[name], self.order[name] = phase, len(self.nodes)
                self.nodes.append(node)
        self.visiting = set()

    def token(self, node, output):
        return (self.scope, "node", node["id"] if isinstance(node, dict) else node, output)

    def ancestors(self, ref):
        if not isinstance(ref, dict):
            _fail(f"{self.scope}: reference must be an object")
        if "state" in ref:
            return frozenset(((self.scope, "state", ref["state"]),))
        if "literal" in ref:
            return frozenset()
        if ref.get("target_index") is True:
            return frozenset(((self.scope, "target_index"),))
        if "node" not in ref or "output" not in ref:
            _fail(f"{self.scope}: unsupported reference {ref!r}")
        key = (ref["node"], ref["output"])
        if key in self.cache:
            return self.cache[key]
        if key in self.visiting:
            _fail(f"{self.scope}: cyclic reference at {key!r}")
        if ref["node"] not in self.by_id:
            _fail(f"{self.scope}: absent node {ref['node']!r}")
        self.visiting.add(key)
        node = self.by_id[ref["node"]]
        result = {self.token(node, ref["output"])}
        for arg in node.get("args", {}).values():
            result.update(self.ancestors(arg))
        selector = node.get("record", {})
        if "source_index" in selector:
            result.update(self.ancestors(selector["source_index"]))
        self.visiting.remove(key)
        self.cache[key] = frozenset(result)
        return self.cache[key]

    def has(self, ref, node, output):
        return self.token(node, output) in self.ancestors(ref)

    def has_state(self, ref, state):
        return (self.scope, "state", state) in self.ancestors(ref)

    def joined(self, refs):
        result = set()
        for ref in refs:
            result.update(self.ancestors(ref))
        return result

    def calls(self, key=None, role=None, phase=None, slot="body", bank=None):
        result = []
        for node in self.nodes:
            if node.get("op") != "call_record" or node.get("slot") != slot:
                continue
            logical_key = node.get("record", {}).get("key", node.get("contract", {}).get("key"))
            if key is not None and logical_key != key:
                continue
            if role is not None and node.get("role", 0) != role:
                continue
            if phase is not None and self.phase[node["id"]] != phase:
                continue
            if bank is not None and node.get("bank") != bank:
                continue
            result.append(node)
        return result

    def helpers(self, function):
        return [n for n in self.nodes if n.get("op") == "call_helper" and n.get("function") == function]

    def all_outputs(self, ref_values, node, outputs):
        ancestors = self.joined(ref_values)
        return all(self.token(node, output) in ancestors for output in outputs)

    def choose(self, nodes, description, predicate=lambda n: True):
        for node in reversed(nodes):
            if predicate(node):
                return node
        _fail(description)

    def read_dependency(self, ref, record, bank, field):
        return any(n.get("op") == "read_record" and n.get("record") == record
                   and n.get("bank") == bank and field in n.get("fields", [])
                   and self.has(ref, n, field) for n in self.nodes)


def _need(condition, message):
    if not condition:
        _fail(message)


def _args(node, names):
    try:
        return [node["args"][name] for name in names]
    except KeyError as error:
        _fail(f"node {node.get('id')!r} lacks required named argument {error.args[0]!r}")


def _situated(a, body, klein):
    """Find one same-query placement/field chain preceding this application."""
    record, phase, limit = body["record"], a.phase[body["id"]], a.order[body["id"]]
    fields = [n for n in a.calls(slot="field", role=0, bank="published", phase=phase)
              if n["record"] == record and a.order[n["id"]] < limit]
    if "field_distance" in body.get("args", {}):
        fields = [n for n in fields if a.has(body["args"]["field_distance"], n, "distance")]
    for field in reversed(fields):
        nearests = [n for n in a.helpers("nearest_klein_lift")
                    if a.order[n["id"]] < a.order[field["id"]]
                    and a.has(field["args"].get("dx", {}), n, "dx")
                    and a.has(field["args"].get("dy", {}), n, "dy")]
        for nearest in reversed(nearests):
            q = nearest["args"]
            if body is klein:
                query_ok = a.has_state(q["query_u"], "surface_u") and a.has_state(q["query_v"], "surface_v")
            else:
                query_ok = a.has(q["query_u"], klein, "ku") and a.has(q["query_v"], klein, "kv")
            if not query_ok or not a.read_dependency(field["args"]["radius"], record, "published", "radius"):
                continue
            placements = [n for n in a.calls(slot="placement", role=0, bank="published", phase=phase)
                          if n["record"] == record and a.order[n["id"]] < a.order[nearest["id"]]
                          and all(a.has(q[arg], n, out) for arg, out in
                                  (("anchor_u", "u"), ("anchor_v", "v"), ("anchor_orientation", "orientation")))]
            for placement in placements:
                if all(a.read_dependency(placement["args"][arg], record, "published", field_name)
                       for arg, field_name in (("u", "anchor_u"), ("v", "anchor_v"), ("orientation", "anchor_orientation"))):
                    return {"body": body["id"], "placement": placement["id"], "nearest": nearest["id"],
                            "field": field["id"], "field_dependency": "argument" if "field_distance" in body.get("args", {}) else "ordered_execution_only"}
    _fail(f"{body['id']}: missing same-record current placement/nearest-lift/field application chain")


def _mutation(m, returns, enzyme, definition):
    target = {"target": True}
    for node in m.nodes:
        if node.get("op") in ("read_record", "call_record"):
            _need(node.get("bank") == "old", f"mutation node {node['id']} reads a non-old record bank")
    mutator = m.choose(m.calls("mutation", 0, bank="old"), "missing old mutation-body application",
                       lambda n: m.has(returns["body"], n, "body_handle"))
    pinion = m.choose(m.calls("pinion", 1, bank="old"), "missing old pinion transport role1",
                      lambda n: m.has(returns["anchor_u"], n, "u") and m.has(returns["anchor_v"], n, "v"))
    _need(m.read_dependency(mutator["args"]["old_body"], target, "old", "body"), "mutator must consume old target body")
    _need((m.scope, "target_index") in m.ancestors(mutator["args"]["target_index"]), "mutator must consume actual target source index")
    for name in PAIR + ("jitter", "dt"):
        _need(m.has_state(mutator["args"][name], name), f"old mutator lacks old-state {name}")
    for argument, record, field in (("old_control", target, "control"), ("mutator_control", {"key": "mutation"}, "control")):
        _need(m.read_dependency(mutator["args"][argument], record, "old", field), f"mutator lacks {argument} dependency")
    placement = m.choose([n for n in m.calls(slot="placement", bank="old") if n["record"] == target],
                         "missing old target placement application",
                         lambda n: all(m.has(pinion["args"][arg], n, out) for arg, out in (("u", "u"), ("v", "v"), ("orientation", "orientation"))))
    for arg, field in (("u", "anchor_u"), ("v", "anchor_v"), ("orientation", "anchor_orientation")):
        _need(m.read_dependency(placement["args"][arg], target, "old", field), f"old placement lacks target {field}")
    for name in PAIR + ("jitter", "dt"):
        _need(m.has_state(pinion["args"][name], name), f"old pinion lacks old-state {name}")
    for arg, field in (("du", "du"), ("dv", "dv"), ("old_placement", "placement")):
        _need(m.read_dependency(pinion["args"][arg], target, "old", field), f"old pinion loses target {field}")
    for name in ("surface_u", "surface_v"):
        _need(m.has_state(pinion["args"][name], name), f"old pinion loses preceding {name}")
    field_nodes = {}
    for key, argument in (("mutation", "field_distance"), (None, "target_field")):
        expected = target if key is None else {"key": key}
        field_nodes[argument] = m.choose([n for n in m.calls(slot="field", bank="old") if n["record"] == expected],
                                          f"old mutator lacks {argument} field evaluation",
                                          lambda n: m.has(mutator["args"][argument], n, "distance"))
    field_nodes["pinion"] = m.choose(m.calls("pinion", slot="field", bank="old"), "old pinion lacks its old field evaluation",
                                      lambda n: m.has(pinion["args"]["field_distance"], n, "distance"))
    nearest_nodes = {}
    for key, field_key in (("mutation", "field_distance"), ("pinion", "pinion")):
        owner = {"key": key}
        field = field_nodes[field_key]
        nearest = m.choose(m.helpers("nearest_klein_lift"), f"old {key} field loses situated target query",
                            lambda n: all(m.has(field["args"][axis], n, axis) for axis in ("dx", "dy"))
                            and all(m.has(n["args"][arg], placement, out) for arg, out in (("query_u", "u"), ("query_v", "v"))))
        anchor = m.choose([n for n in m.calls(slot="placement", bank="old") if n["record"] == owner],
                           f"old {key} field loses its own placement",
                           lambda n: all(m.has(nearest["args"][arg], n, out) for arg, out in
                                         (("anchor_u", "u"), ("anchor_v", "v"), ("anchor_orientation", "orientation"))))
        for arg, field_name in (("u", "anchor_u"), ("v", "anchor_v"), ("orientation", "anchor_orientation")):
            _need(m.read_dependency(anchor["args"][arg], owner, "old", field_name), f"old {key} placement loses {field_name}")
        _need(m.read_dependency(field["args"]["radius"], owner, "old", "radius"), f"old {key} field loses radius")
        nearest_nodes[key] = nearest
    target_field = field_nodes["target_field"]
    _need(all(m.has(target_field["args"][axis], nearest_nodes["mutation"], axis) for axis in ("dx", "dy")),
          "old target field must use the declared shared target-to-mutator local query")
    _need(m.read_dependency(target_field["args"]["radius"], target, "old", "radius"), "old target field loses radius")
    rebind = m.choose(m.helpers("rebind_field"), "missing old-field/new-body/new-anchor rebinding",
                      lambda n: m.has(n["args"]["new_body"], mutator, "body_handle")
                      and m.has(n["args"]["new_u"], pinion, "u") and m.has(n["args"]["new_v"], pinion, "v")
                      and m.read_dependency(n["args"]["old_field"], target, "old", "field"))
    _need(m.read_dependency(rebind["args"]["old_radius"], target, "old", "radius"), "rebinding loses old target radius")
    for name in ("surface_u", "surface_v"):
        _need(m.has_state(rebind["args"][name], name), f"rebinding loses old {name}")
    for field, node, output in (("body", mutator, "body_handle"), ("anchor_u", pinion, "u"),
                                ("anchor_v", pinion, "v"), ("anchor_orientation", pinion, "orientation"),
                                ("placement", pinion, "placement_handle"), ("field", rebind, "field_handle"), ("radius", rebind, "radius")):
        _need(m.has(returns[field], node, output), f"mutation return {field} loses its source update dependency")
    _need(m.read_dependency(returns["generation"], target, "old", "generation"), "next generation must depend on old target generation")
    _need(m.has(returns["control"], mutator, "control"), "mutation return loses proposed control")
    if enzyme:
        for argument, state in (("domain_trial_sdf", "enzyme_trial_sdf"), ("domain_improvement", "enzyme_improvement"), ("domain_accepted", "enzyme_accepted")):
            _need(argument in mutator["args"] and m.has_state(mutator["args"][argument], state), f"enzyme mutation loses previous-epoch {state}")
    retention = _retention(m, returns, definition, mutator, pinion, rebind)
    return {"old_mutator": mutator["id"], "old_pinion_transport": pinion["id"], "old_target_placement": placement["id"],
            "rebind": rebind["id"], "retention": retention}


def _retention(m, returns, definition, mutator, pinion, rebind):
    target = {"target": True}
    producers = {"body": (mutator, "body_handle"), "field": (rebind, "field_handle"), "placement": (pinion, "placement_handle")}
    source, evidence = definition.get("source", {}), []
    for policy in source.get("source_slot_bindings", {}).get("mutation_program_retention", []):
        slot, function = policy["slot"], policy["function"]
        node = m.choose(m.helpers(function), f"missing declared {slot} preserve_program policy",
                         lambda n: m.has(returns[slot], n, "handle"))
        _need(node["args"]["source_index"] == {"target_index": True}, "slot retention must inspect actual target index")
        _need(m.read_dependency(node["args"]["old_handle"], target, "old", slot), f"{slot} retention loses old target handle")
        _need(m.has(node["args"]["proposed_handle"], *producers[slot]), f"{slot} retention loses normal proposed handle")
        evidence.append({"function": function, "node": node["id"], "slots": [slot], "source_indices": policy["source_indices"]})
    extension = source.get("catalogue_extension") or source.get("authoring", {}).get("catalogue_extension")
    if extension and extension.get("added"):
        policy = extension["mutation_retention"]
        node = m.choose(m.helpers(policy["function"]), "missing declared catalogue handle-retention policy",
                         lambda n: all(m.has(returns[slot], n, slot) for slot in ("body", "field", "placement")))
        _need(node["args"]["source_index"] == {"target_index": True}, "catalogue retention must inspect actual target index")
        for slot in ("body", "field", "placement"):
            _need(m.read_dependency(node["args"]["old_" + slot], target, "old", slot), f"catalogue retention loses old {slot}")
            _need(m.has(node["args"]["new_" + slot], *producers[slot]), f"catalogue retention loses proposed {slot}")
        evidence.append({"function": policy["function"], "node": node["id"], "slots": ["body", "field", "placement"], "source_indices": [policy["source_index"]]})
    return evidence


def audit_graph(definition, cycle, graph):
    """Raise ValueError for missing mandatory source edges; return evidence.

    Additional calls/helpers and transitive helper transformations are allowed.
    Arithmetic input dependence is intentionally not inferred from call wiring.
    """
    _need(graph.get("profile") == "DWI-SOURCE-GRAPH-0.1", "unsupported graph profile")
    names = [p.get("name") for p in graph.get("phases", [])]
    _need(tuple(cycle.get("phases", [])) == PHASES and names == list(cycle["phases"]), "all eight phases must follow the actual source cycle order")
    m = _Graph("mutation", [("mutation", graph["mutation"]["nodes"])])
    a = _Graph("action", [(p["name"], p["nodes"]) for p in graph["phases"]])
    returns = graph["returns"]
    _need(set(returns) == set(definition["state_names"]), "complete next-state return mapping required")
    _need(set(graph["mutation"]["returns"]) == {"body", "field", "placement", "generation", *definition["record_value_names"]}, "complete next-record return mapping required")
    for node in a.nodes:
        if node.get("op") == "call_record":
            _need(node.get("bank") == "published", f"action call {node['id']} must resolve published definitions")
    live = a.joined(returns.values())
    def pick(key, role, phase, predicate=lambda n: True):
        return a.choose(a.calls(key, role, phase, bank="published"), f"missing live {phase}: {key} role{role}",
                        lambda n: any(t[:3] == (a.scope, "node", n["id"]) for t in live) and predicate(n))
    def edges(node, arguments, parent, outputs, message):
        _need(a.all_outputs(_args(node, arguments), parent, outputs), message)
    returned = pick("return", 0, "surface_return", lambda n: all(a.has(returns[k], n, k) for k in PAIR + ("u", "v", "orientation", "phase")))
    klein = pick("klein", 0, "operator_mutation")
    for arg, state in (("ku", "surface_u"), ("kv", "surface_v"), ("ko", "K_orientation")):
        _need(a.has_state(klein["args"][arg], state), f"new Klein loses old {state}")
    _need(all(a.has_state(klein["args"][name], name) for name in PAIR), "new Klein loses preceding returned wave")
    feedback = a.choose(a.helpers("nearest_klein_lift"), "new Klein loses situated preceding returned coordinates",
                         lambda n: a.has(klein["args"]["feedback_dx"], n, "dx") and a.has(klein["args"]["feedback_y"], n, "anchor_frame_y"))
    for arg, state in (("query_u", "u"), ("query_v", "v"), ("anchor_u", "surface_u"), ("anchor_v", "surface_v"), ("anchor_orientation", "K_orientation")):
        _need(a.has_state(feedback["args"][arg], state), f"new Klein feedback loses preceding {state}")
    _need(a.has_state(klein["args"]["feedback_orientation"], "orientation"), "new Klein feedback loses preceding returned orientation")
    initial_psi = a.choose(a.calls("psi", 0, "operator_mutation", bank="published"), "missing initial PSI guard application")
    psi = pick("psi", 0, "selected_operator")
    for interval in (initial_psi, psi):
        _need(a.has_state(interval["args"]["dt"], "dt"), "PSI loses declared old interval")
    phi = pick("phi", 0, "log_polar")
    _need(all(a.has_state(phi["args"][name], name) for name in PAIR), "PHI must encode previous returned pair")
    split = pick("split", 0, "split_and_hinge")
    polar = ("rho0", "theta0", "rho1", "theta1")
    edges(split, polar, phi, polar, "split loses current PHI encoding")
    _need(a.has_state(split["args"]["jitter"], "jitter"), "split loses source jitter")
    parity = pick("parity", 0, "split_and_hinge")
    edges(parity, ("split_theta0", "split_theta1"), split, ("theta0", "theta1"), "parity loses actual split angles")
    for name in ("jitter", "neck"):
        _need(a.has_state(parity["args"][name], name), f"parity loses supplied {name}")
    hinge = pick("hadamard", 1, "split_and_hinge")
    edges(hinge, polar, split, polar, "hinge loses split channels")
    edges(hinge, ("parity", "phase"), parity, ("parity", "phase"), "hinge loses parity/phase context")
    _need(a.has_state(hinge["args"]["phase"], "phase"), "hinge loses previous returned phase")
    bst = pick("bst", 0, "selected_operator")
    for name in ("neck", "jitter"):
        _need(a.has_state(bst["args"][name], name), f"BST loses supplied {name}")
    _need(a.has_state(bst["args"]["depth"], "route_depth"), "BST loses supplied route depth")
    for i in range(5 if "route_b4" in definition["state_names"] else 4):
        _need(a.has_state(bst["args"][f"b{i}"], f"route_b{i}"), f"BST loses supplied route bit{i}")
    selected = a.choose([n for n in a.calls(role=99, phase="selected_operator", bank="published") if "source_index" in n.get("record", {})],
                        "missing dynamic selected source-record application",
                        lambda n: a.has(n["record"]["source_index"], bst, "index") and a.has(n["args"]["routing_phase"], bst, "routing_phase") and a.all_outputs(_args(n, PAIR), hinge, PAIR))
    combine = pick("rk4", 2, "rk4_four_slots")
    derivatives = a.calls("rk4", 1, "rk4_four_slots", bank="published")
    slopes = []
    for k in range(1, 5):
        args = [combine["args"][f"k{k}_{j}"] for j in range(4)]
        candidates = [n for n in derivatives if a.all_outputs(args, n, PAIR)]
        # The nearest derivative ancestor distinguishes each actual stage from
        # earlier slopes propagated through its intermediate-state arguments.
        slope = a.choose(candidates, f"RK combination lacks complete slope{k}")
        slopes.append(slope)
    _need(len({n["id"] for n in slopes}) == 4, "four distinct derivative evaluations are required")
    edges(slopes[0], PAIR, selected, PAIR, "k1 loses selected wave")
    for k in range(1, 4):
        edges(slopes[k], PAIR, slopes[k-1], PAIR, f"k{k+1} lacks preceding slope dependency")
        edges(slopes[k], PAIR, selected, PAIR, f"k{k+1} loses initial RK wave")
        _need(a.all_outputs(_args(slopes[k], PAIR), slopes[0], ("h",)), f"k{k+1} loses first-stage h")
    for slope in slopes:
        _need(a.has_state(slope["args"]["jitter"], "jitter"), "RK derivative loses jitter")
        _need(a.has(slope["args"]["dt"], psi, "dt"), "RK derivative loses effective PSI interval")
    _need(a.has(combine["args"]["dt"], psi, "dt"), "RK combination loses effective PSI interval")
    yup_count = cycle.get("fourth_rk4_slot", {}).get("y_up_applications")
    _need(type(yup_count) is int and yup_count >= 0, "invalid declared Y-up count")
    k4_refs = [combine["args"][f"k4_{j}"] for j in range(4)]
    yups = [n for n in a.calls("y_up", 0, "rk4_four_slots", bank="published") if a.all_outputs(k4_refs, n, PAIR)]
    _need(len(yups) == yup_count, "fourth slope must contain exactly the declared nested Y-up events")
    previous = slopes[3]
    for yup in yups:
        edges(yup, PAIR, previous, PAIR, "Y-up events must form a nested chain on k4")
        previous = yup
    for k in range(1, 4):
        refs = [combine["args"][f"k{k}_{j}"] for j in range(4)]
        _need(not any(a.all_outputs(refs, yup, PAIR) for yup in yups), "Y-up must not alter the first three slopes")
    shapes = [pick(key, 0, "geometry_divergence") for key in GEOMETRY]
    for shape in shapes:
        edges(shape, PAIR, combine, PAIR, "primitive loses combined RK wave")
    delta = pick("delta_phi", 0, "geometry_divergence")
    _need(a.has(delta["args"]["phase"], phi, "theta0"), "phase differential loses PHI angle")
    for arg, state in (("previous", "phase_previous"), ("previous2", "phase_previous2")):
        _need(a.has_state(delta["args"][arg], state), f"phase differential loses old {state}")
    _need(a.has_state(delta["args"]["jitter"], "jitter"), "phase differential loses jitter")
    _need(a.has(delta["args"]["dt"], psi, "dt"), "phase differential loses effective PSI interval")
    growth = pick("phyllotaxis", 0, "geometry_divergence")
    edges(growth, ("delta",), delta, ("delta",), "growth loses phase differential")
    _need(a.has(growth["args"]["dt"], psi, "dt"), "growth loses effective PSI interval")
    coupling = pick("double_dot", 0, "geometry_divergence")
    edges(coupling, PAIR, combine, PAIR, "coupling loses RK wave")
    edges(coupling, tuple(f"g{i}" for i in range(4)), growth, PAIR, "coupling loses growth wave")
    blend = pick("blend", 0, "geometry_divergence")
    edges(blend, (*PAIR, "score"), coupling, (*PAIR, "score"), "blend loses coupling result")
    edges(blend, tuple(f"growth{i}" for i in range(4)), growth, PAIR, "blend loses growth")
    for shape in shapes:
        for consumer in (growth, blend):
            edges(consumer, tuple(f"g{i}" for i in range(6)), shape, ("value",), f"{consumer['id']} loses primitive {shape['id']}")
    crystal = pick("crystal", 0, "rgba_crystal")
    edges(crystal, PAIR, blend, PAIR, "crystal loses geometric blend")
    dichromatic = pick("dichromatic", 0, "rgba_crystal")
    edges(dichromatic, PAIR, crystal, PAIR, "dichromatic channels lose crystal")
    _need(a.has(dichromatic["args"]["parity"], parity, "parity"), "dichromatic channels lose current parity")
    history = pick("phase_history", 0, "rgba_crystal")
    for j in range(4):
        _need(a.has_state(history["args"][f"B{j}"], f"B{j}"), "history loses preceding B component")
    _need(a.has_state(history["args"]["jitter"], "jitter"), "phase history loses jitter")
    for k, slope in enumerate(slopes, 1):
        edges(history, tuple(f"k{k}_{j}" for j in range(4)), previous if k == 4 else slope, PAIR, "history loses actual modified slopes")
    transform = pick("T_transform", 0, "rgba_crystal")
    edges(transform, PAIR, blend, PAIR, "T transformation loses blended wave")
    edges(transform, ("crystal_ar",), crystal, ("ar",), "T transformation loses crystal dependency")
    inverse = pick("inverse_T", 0, "rgba_crystal")
    matrix_in = ("t00", "t01", "t10", "t11")
    edges(inverse, matrix_in, transform, matrix_in, "inverse loses complete current T")
    pinion = pick("pinion", 0, "surface_return")
    edges(pinion, ("ku", "kv", "ko"), klein, ("ku", "kv", "ko"), "return pinion loses current K")
    edges(pinion, ("Rr", "Ri", "Gr", "Gi"), dichromatic, PAIR, "return pinion loses R/G streams")
    edges(pinion, tuple(f"B{i}" for i in range(4)), history, tuple(f"B{i}" for i in range(4)), "return pinion loses current complete B")
    inverse_out = ("a00", "a01", "a10", "a11")
    edges(pinion, inverse_out, inverse, inverse_out, "return pinion loses complete inverse matrix")
    edges(returned, (*PAIR, "u", "v", "orientation"), pinion, (*PAIR, "u", "v", "orientation"), "surface return loses pinion-carried state")
    _need(a.has(returned["args"]["parity"], parity, "parity"), "surface return loses parity")
    _need(a.has(returned["args"]["dt"], psi, "dt"), "surface return loses effective PSI interval")
    for name in ("neck", "phase"):
        _need(a.has_state(returned["args"][name], name), f"surface return loses preceding {name}")
    for out, node, name in (("surface_u", klein, "ku"), ("surface_v", klein, "kv"), ("K_orientation", klein, "ko"), ("phase_previous", delta, "unwrapped")):
        _need(a.has(returns[out], node, name), f"returned state loses {out}")
    _need(a.has_state(returns["phase_previous2"], "phase_previous"), "phase_previous2 must carry preceding encoded history")
    for i in range(4):
        _need(a.has(returns[f"B{i}"], history, f"B{i}"), "returned state loses new B")
    for out, name in zip(("A00", "A01", "A10", "A11"), inverse_out):
        _need(a.has(returns[out], inverse, name), f"returned state loses inverse component {out}")
    for out, name in zip(("T00", "T01", "T10", "T11"), matrix_in):
        _need(a.has(returns[out], transform, name), f"returned state loses matrix component {out}")
    for out, name in zip(("Rr", "Ri", "Gr", "Gi"), PAIR):
        _need(a.has(returns[out], dichromatic, name), f"returned state loses channel {out}")
    for name in PAIR:
        _need(a.has_state(returns["previous_" + name], name), "returned previous wave must carry old input")
    for name in ("dt", "jitter", "neck", "route_depth", *("route_b" + str(i) for i in range(5 if "route_b4" in returns else 4))):
        _need(a.has_state(returns[name], name), f"returned state loses configured {name}")
    _need(a.has(returns["selected_index"], bst, "index"), "returned state loses actual selected index")
    _need(a.all_outputs([returns["energy"]], returned, PAIR), "energy diagnostic loses returned wave")
    _need(any(a.has(returns["last_field"], n, "distance") for n in a.calls("return", slot="field", bank="published")), "returned state loses last return field")
    situated = [_situated(a, n, klein) for n in a.calls(slot="body", bank="published")]
    enzyme = bool(definition.get("source", {}).get("enzyme"))
    enzyme_evidence = _enzyme(a, returns, returned, history, inverse) if enzyme else None
    mutation_evidence = _mutation(m, graph["mutation"]["returns"], enzyme, definition)
    return {"profile": "DWI-SOURCE-GRAPH-FIDELITY-0.1", "passed": True, "phases": names,
            "mutation": mutation_evidence, "situated_calls": situated,
            "rk_derivatives": [n["id"] for n in slopes], "k4_y_up_chain": [n["id"] for n in yups],
            "surface_return": returned["id"], "enzyme": enzyme_evidence,
            "psi": {"initial_executed_guard": initial_psi["id"], "effective_interval": psi["id"]},
            "scope": "Named structural dependency and execution-order audit. Helpers may transform values; callee arithmetic may ignore supplied inputs. Passing is not numerical causality, scientific correctness, equivalence, convergence, or runtime evidence."}


def _enzyme(a, returns, returned, history, inverse):
    phase = "surface_return"
    proposal = a.choose(a.calls("blend", 100, phase, bank="published"), "missing resident enzyme proposal role100")
    for state, arg in (("enzyme_y0", "y0"), ("enzyme_y1", "y1"), ("obs_E_normalized", "obs_E"),
                       ("obs_S_normalized", "obs_S"), ("obs_ES_normalized", "obs_ES"), ("obs_P_normalized", "obs_P")):
        _need(a.has_state(proposal["args"][arg], state), f"enzyme proposal loses old {state}")
    _need(a.has_state(proposal["args"]["dt"], "dt"), "enzyme proposal loses configured old interval")
    for parent, args, outputs in ((returned, PAIR, PAIR), (history, tuple(f"B{i}" for i in range(4)), tuple(f"B{i}" for i in range(4))),
                                  (inverse, ("A00", "A01", "A10", "A11"), ("a00", "a01", "a10", "a11"))):
        _need(a.all_outputs(_args(proposal, args), parent, outputs), "enzyme proposal loses current source-cycle context")
    sdf = a.choose(a.calls("blend", 101, phase, bank="published"), "missing enzyme SDF role101",
                    lambda n: a.has(n["args"]["y0"], proposal, "trial_y0") and a.has(n["args"]["y1"], proposal, "trial_y1"))
    project = a.choose(a.calls("blend", 102, phase, bank="published"), "missing enzyme projection role102",
                        lambda n: a.all_outputs(_args(n, ("distance", "boundary_y0", "boundary_y1")), sdf, ("distance", "boundary_y0", "boundary_y1")))
    for arg, out in (("trial_y0", "trial_y0"), ("trial_y1", "trial_y1")):
        _need(a.has(project["args"][arg], proposal, out), "enzyme projection loses proposed point")
    accept = a.choose(a.calls("blend", 103, phase, bank="published"), "missing enzyme acceptance role103",
                       lambda n: a.all_outputs(_args(n, ("candidate_y0", "candidate_y1", "candidate_objective")), project, ("candidate_y0", "candidate_y1", "objective")))
    for arg, state in (("incumbent_y0", "enzyme_y0"), ("incumbent_y1", "enzyme_y1")):
        _need(a.has_state(accept["args"][arg], state), f"enzyme acceptance loses old {state}")
    witnesses = a.calls("blend", 104, phase, bank="published")
    old = a.choose(witnesses, "enzyme acceptance needs reevaluated old objective",
                    lambda n: a.has_state(n["args"]["y0"], "enzyme_y0") and a.has_state(n["args"]["y1"], "enzyme_y1") and a.has(accept["args"]["incumbent_objective"], n, "objective"))
    final = a.choose(witnesses, "enzyme final witness must evaluate accepted coordinates",
                      lambda n: a.has(n["args"]["y0"], accept, "y0") and a.has(n["args"]["y1"], accept, "y1"))
    for node in (project, old, accept, final):
        for species in ("E", "S", "ES", "P"):
            _need(a.has_state(node["args"]["obs_" + species], "obs_" + species + "_normalized"), f"enzyme {node['id']} loses observation {species}")
    for field, node, out in (("enzyme_y0", accept, "y0"), ("enzyme_y1", accept, "y1"), ("enzyme_accepted", accept, "accepted"),
                              ("enzyme_improvement", accept, "improvement"), ("enzyme_trial_sdf", sdf, "distance"),
                              ("enzyme_gap_estimate", final, "gap_estimate"), ("enzyme_objective", final, "objective")):
        _need(a.has(returns[field], node, out), f"enzyme next state loses {field}")
    for species in ("E", "S", "ES", "P"):
        _need(a.has(returns["enzyme_" + species + "_uM"], final, species + "_uM"), "enzyme return loses witness concentration")
        name = "obs_" + species + "_normalized"
        _need(a.has_state(returns[name], name), f"enzyme return loses supplied observation {species}")
    for field, node, out in (("enzyme_step", proposal, "step"), ("enzyme_trial_y0", proposal, "trial_y0"),
                              ("enzyme_trial_y1", proposal, "trial_y1"), ("enzyme_projection_distance", project, "projection_distance"),
                              ("enzyme_previous_objective", old, "objective")):
        _need(a.has(returns[field], node, out), f"enzyme next state loses {field}")
    return {"proposal": proposal["id"], "sdf": sdf["id"], "projection": project["id"], "incumbent_witness": old["id"], "acceptance": accept["id"], "final_witness": final["id"]}
