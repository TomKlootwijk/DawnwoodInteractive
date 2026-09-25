"""Structural checks for circulating resident SDF program construction.

This is an additional source-graph audit, not an SDF correctness proof or a
numerical sensitivity test. The source compiler owns schema, nominal types,
register allocation and the runtime ABI. Here each named program word is
followed through construction, guarded interpretation and complete return.
"""
from __future__ import annotations

try:
    from . import source_graph_fidelity as core
    from . import source_development_bindings as bindings
except ImportError:
    import source_graph_fidelity as core
    import source_development_bindings as bindings


PROFILE = "DWI-SDF-DEVELOPMENT-FIDELITY-0.1"
PROGRAM = bindings.PROGRAM_NAMES
CODE = bindings.HEADER_NAMES + bindings.CODE_NAMES
BOXES = bindings.BOX_NAMES


def _need(condition, message):
    if not condition:
        raise ValueError("Source development fidelity: " + message)


def _ref(node, output):
    return {"node": node["id"], "output": output}


def _exact(actual, expected, message):
    _need(actual == expected, message)


class _Flow:
    def __init__(self, scope, groups, definition, graph, metadata):
        self.g = core._Graph(scope, groups)
        self.definition, self.graph, self.metadata = definition, graph, metadata
        self.key = metadata["record_key"]
        self.roles = metadata["roles"]

    def call(self, reference, name, output=None):
        _need(isinstance(reference, dict) and set(reference) == {"node", "output"},
              f"{name}: expected a direct named result")
        node = self.g.by_id.get(reference["node"])
        _need(node is not None, f"{name}: missing producer")
        _need(node.get("op") == "call_record" and node.get("record") == {"key": self.key}
              and node.get("slot") == "body" and node.get("bank") == "published"
              and node.get("role", 0) == self.roles[name],
              f"{name}: result must come from the current resource record role")
        if output is not None:
            _exact(reference["output"], output, f"{name}: wrong result field")
        return node

    def calls(self, name):
        return self.g.calls(self.key, self.roles[name], slot="body", bank="published")

    def earlier(self, first, second, description):
        _need(self.g.order[first["id"]] < self.g.order[second["id"]], description)

    def words(self, node, names, program, description):
        for name in names:
            _exact(node.get("args", {}).get(name), program[name],
                   f"{description}: wrong {name} word")

    def interpret(self, reference, program, *, query=None, after=()):
        """Check a complete staged interpreter with one unambiguous program.

        The final three calls do not merely need a shared ancestor. Every
        opcode, child reference, materialized node value and leaf distance
        must reach its matching named operand.
        """
        final = self.call(reference, "interpret", "distance")
        self.words(final, ("root", *(f"{f}{i}" for i in (5, 6) for f in ("op", "a", "b"))),
                   program, "final interpreter")
        leaf = self.call(final["args"]["d0"], "leaf_distances", "d0")
        prefix = self.call(final["args"]["v0"], "interpret_prefix", "v0")
        middle = self.call(final["args"]["v3"], "interpret_middle", "v3")
        self.words(leaf, BOXES, program, "leaf distances")
        self.words(prefix, tuple(f"{f}{i}" for i in range(3) for f in ("op", "a", "b")),
                   program, "prefix interpreter")
        self.words(middle, tuple(f"{f}{i}" for i in (3, 4) for f in ("op", "a", "b")),
                   program, "middle interpreter")
        for node in (prefix, middle, final):
            for i in range(4):
                _exact(node["args"][f"d{i}"], _ref(leaf, f"d{i}"),
                       "staged interpreter mixes leaf evaluations")
        for node in (middle, final):
            for i in range(3):
                _exact(node["args"][f"v{i}"], _ref(prefix, f"v{i}"),
                       "staged interpreter loses matching prefix output")
        for i in (3, 4):
            _exact(final["args"][f"v{i}"], _ref(middle, f"v{i}"),
                   "final interpreter loses matching middle output")
        for first, second in ((leaf, prefix), (prefix, middle), (middle, final)):
            self.earlier(first, second, "interpreter stages execute out of order")
        for guard in after:
            self.earlier(guard, leaf, "live-program guard must execute before leaf interpretation")
        if query is not None:
            for axis in ("x", "y"):
                _exact(leaf["args"][axis], query[axis], f"interpreter loses {axis} query")
        return {"leaf": leaf["id"], "prefix": prefix["id"],
                "middle": middle["id"], "final": final["id"],
                "query": {axis: leaf["args"][axis] for axis in ("x", "y")}}

    def validation(self, program):
        """Find both independent geometry gates and the grammar check."""
        code = self.g.choose(self.calls("validate_code"), "missing live code validation",
                             lambda n: all(n["args"].get(k) == program[k] for k in CODE))
        boxes = self.g.choose(self.calls("validate_geometry_boxes"), "missing matching box validation",
                              lambda n: all(n["args"].get(k) == program[k] for k in (*BOXES, "node_count")))
        separated = self.g.choose(self.calls("validate_geometry_separation"), "missing matching separation validation",
                                  lambda n: all(n["args"].get(k) == program[k] for k in (*BOXES, "node_count")))
        combined = self.g.choose(self.calls("validate_geometry"), "missing combined geometry validation",
                                 lambda n: n["args"].get("valid_boxes") == _ref(boxes, "valid_boxes")
                                 and n["args"].get("valid_separation") == _ref(separated, "valid_separation"))
        self.earlier(boxes, combined, "box validity is consumed before evaluation")
        self.earlier(separated, combined, "separation validity is consumed before evaluation")
        return code, boxes, separated, combined

    def helper(self, reference, purpose, output=None):
        _need(isinstance(reference, dict) and set(reference) == {"node", "output"},
              f"{purpose}: expected a direct helper result")
        node = self.g.by_id.get(reference["node"])
        _need(node is not None and node.get("op") == "call_helper"
              and node.get("function") == self.metadata["helpers"][purpose],
              f"{purpose}: missing declared helper")
        if output is not None:
            _exact(reference["output"], output, f"{purpose}: wrong result field")
        return node

    def select(self, selected, condition, new, old):
        result = []
        for group, names in (("code", CODE), ("boxes", BOXES)):
            node = self.helper(selected[names[0]], "development_select_" + group, names[0])
            _exact(node["args"].get("condition"), condition, "program selector changes acceptance condition")
            for name in names:
                _exact(selected[name], _ref(node, name), "program return mixes selector outputs")
                _exact(node["args"].get("new_" + name), new[name], "program selector loses matching candidate " + name)
                _exact(node["args"].get("old_" + name), old[name], "program selector loses matching incumbent " + name)
            result.append(node)
        return result

    def score(self, reference, program, *, after=()):
        node = self.call(reference, "score", "score")
        self.words(node, (*BOXES, "node_count"), program, "score")
        samples = []
        for i, point in enumerate(self.metadata["training_points"]):
            query = {axis: {"literal": value, "type": "resource_coordinate"}
                     for axis, value in zip(("x", "y"), point)}
            evidence = self.interpret(node["args"][f"d{i}"], program, query=query, after=after)
            self.earlier(self.g.by_id[evidence["final"]], node, "score executes before its distance sample")
            samples.append(evidence)
        _exact(set(node["args"]), {*(f"d{i}" for i in range(len(samples))), "node_count", *BOXES},
               "score sample count differs from declared training requests")
        return node, samples


def _helpers(definition, graph, meta):
    """Protect the small protocol helpers, including their eager guards.

    Domain arithmetic remains a separately validated binding. These selectors
    and bit gates have a fixed structural meaning in this protocol edition;
    accepting a helper with merely similar ancestry would permit partial
    checkpoint publication or evaluation of rejected candidate data.
    """
    c, V = bindings.c, bindings.V
    expected = {}
    for group, names in (("code", CODE), ("boxes", BOXES),
                         ("score", tuple(meta["source"]["bindings"]["score"]["outputs"]))):
        expected["development_select_" + group] = (
            {k: c.choose(V("condition"), V("new_" + k), V("old_" + k)) for k in names},
            [c.bit_guard(V("condition"))])
    expected["development_require_live"] = ({"valid": 1},
        [c.eq(V("code"), 1), c.eq(V("geometry"), 1), c.le(c.abs_(V("query_x")), 16),
         c.le(c.abs_(V("query_y")), 16), c.bit_guard(V("enabled"))])
    expected["development_candidate_valid"] = ({"valid": bindings.both(V("code"), V("geometry"), V("proposed"))},
        [c.bit_guard(V(k)) for k in ("code", "geometry", "proposed")])
    expected["development_descriptor_encode"] = (
        {f"reserved_{i}": c.choose(c.eq(V("source_index"), meta["source_index"]),
             V(("x", "y", "half")[i]) if i < 3 else
             bindings.both(V("valid"), V("enabled"), c.lt(V("revision"), bindings.sdf.MAX_REVISION)) if i == 3 else 0,
             V(f"old_{i}")) for i in range(5)},
        [c.bit_guard(V("valid")), c.bit_guard(V("enabled"))])
    expected["development_descriptor_decode"] = (
        {name: V(f"reserved_{i}") for i, name in enumerate(("x", "y", "half", "valid"))},
        [c.bit_guard(V("reserved_3")), c.eq(V("reserved_4"), 0)])
    expected["development_diagnostics"] = (
        {"admitted": c.le(V("distance"), 0), "trials": c.add(V("trials"), 1)},
        [c.eq(V("trials"), c.op("floor", V("trials"))), c.le(0, V("trials")),
         c.lt(V("trials"), bindings.sdf.MAX_REVISION)])
    for purpose, (outputs, guards) in expected.items():
        name = meta["helpers"].get(purpose)
        _need(name in graph.get("functions", {}), "missing protocol helper " + purpose)
        binding = graph["functions"][name]["binding"]
        _exact(binding["outputs"], outputs, purpose + ": changed protected protocol expression")
        _exact(binding.get("requires", []), guards, purpose + ": changed protected protocol guards")
        if name in definition["functions"]:
            _exact(definition["functions"][name]["binding"], binding,
                   purpose + ": compiled helper differs from graph declaration")
    return list(expected)


def _metadata(definition, graph):
    meta = definition.get("source", {}).get("development")
    _need(isinstance(meta, dict) and meta.get("profile") == "DWI-SDF-DEVELOPMENT-0.1",
          "missing development edition declaration")
    _need(meta.get("record_key") == "resource_definition" and meta.get("source_index") == 31
          and meta.get("record_ordinal") == 31 and meta.get("mutator_role") == 2,
          "this edition requires resource source31 and old-mutator role2")
    _exact(set(meta["program_state_fields"]), set(PROGRAM), "incomplete program state declaration")
    diagnostic_names = {"query_x", "query_y", "quota", "score", "coverage", "witness_x", "witness_y",
                        "witness_distance", "accepted", "improvement", "distance", "trials", "previous_score",
                        "enabled", "admitted"}
    _exact(set(meta["diagnostic_state_fields"]), diagnostic_names, "incomplete diagnostic state declaration")
    names = [*meta["program_state_fields"].values(), *meta["diagnostic_state_fields"].values()]
    _need(len(names) == len(set(names)) and set(names).issubset(definition["state_names"]),
          "program or diagnostic words alias or are absent from the checkpoint")
    _exact(meta["descriptor_fields"], dict(zip(("x", "y", "half", "valid", "reserved"),
                                               (f"reserved_{i}" for i in range(5)))),
           "descriptor must occupy only the declared five resource-record words")
    records = [r for r in definition["records"] if r.get("key") == meta["record_key"]]
    extension = definition["source"].get("catalogue_extension", {})
    _need(len(records) == 1 and len(definition["records"]) == 32
          and definition["records"][31] is records[0]
          and extension.get("record_source_indices", {}).get(meta["record_key"]) == 31,
          "resource record identity differs from declaration")
    record = records[0]
    _exact(record["body"], meta["family"], "resource family differs from declaration")
    source = meta["source"]
    _exact(meta["training_points"], source["training_points"], "training requests differ from development source")
    for name, entry in source["bindings"].items():
        function = meta["functions"][name]
        _exact(definition["functions"][function]["binding"], entry["binding"],
               "resident binding differs from declared development source: " + name)
        if name == "propose_edit":
            for family in ("mutation", "mutation_successor"):
                _exact(definition["families"][family]["methods"].get("2"), function,
                       "old mutator family loses its construction method")
        else:
            _exact(definition["families"][record["body"]]["methods"].get(str(meta["roles"][name])), function,
                   "current resource role resolves a different function: " + name)
    return meta


def audit_development_graph(definition, cycle, graph):
    """Audit the full source recurrence and the additional definition loop.

    IDs are discovered from matching typed calls and exact operand references;
    metadata does not get to assert that an arbitrary node passed. Every eager
    interpreter call must be accounted for as incumbent, safe candidate or
    retained-query evaluation. No native execution is performed here.
    """
    core_evidence = core.audit_graph(definition, cycle, graph)
    meta = _metadata(definition, graph)
    helper_evidence = _helpers(definition, graph, meta)
    m = _Flow("mutation", [("mutation", graph["mutation"]["nodes"])], definition, graph, meta)
    a = _Flow("action", [(p["name"], p["nodes"]) for p in graph["phases"]], definition, graph, meta)
    returns, mutation_returns = graph["returns"], graph["mutation"]["returns"]
    old = {k: {"state": v} for k, v in meta["program_state_fields"].items()}
    states = {k: {"state": v} for k, v in meta["diagnostic_state_fields"].items()}
    current = {k: returns[v] for k, v in meta["program_state_fields"].items()}
    diagnostics = {k: returns[v] for k, v in meta["diagnostic_state_fields"].items()}
    for name in ("query_x", "query_y", "quota", "enabled"):
        _exact(diagnostics[name], states[name], "return changes protected/configured " + name)

    # The construction descriptor is produced from the old resident mutator,
    # stored only for the actual target31, and consumed from its published record.
    encoder = m.helper(mutation_returns["reserved_0"], "development_descriptor_encode", "reserved_0")
    _exact(encoder["args"]["source_index"], {"target_index": True}, "descriptor publication must inspect actual target index")
    _exact(encoder["args"]["enabled"], states["enabled"], "descriptor loses configured enabled bit")
    _exact(encoder["args"]["revision"], old["revision"], "descriptor loses old program revision")
    for i in range(5):
        _exact(mutation_returns[f"reserved_{i}"], _ref(encoder, f"reserved_{i}"), "mutation returns only part of descriptor")
        reference = encoder["args"][f"old_{i}"]
        read = m.g.by_id.get(reference.get("node"), {})
        _need(set(reference) == {"node", "output"} and reference["output"] == f"reserved_{i}"
              and read.get("op") == "read_record" and read.get("record") == {"target": True}
              and read.get("bank") == "old" and f"reserved_{i}" in read.get("fields", []),
              "descriptor retention must preserve the matching old target reserved word directly")
    proposals = m.g.calls("mutation", 2, bank="old")
    proposal = m.g.choose(proposals, "missing old resident construction method",
                          lambda n: all(encoder["args"].get(k) == _ref(n, k) for k in ("x", "y", "half", "valid")))
    for name in ("witness_x", "witness_y", "witness_distance", "quota"):
        _exact(proposal["args"][name], states[name], "old construction method loses preceding " + name)
    _exact(proposal["args"]["node_count"], old["node_count"], "construction loses preceding program count")
    _exact(proposal["args"]["ar"], {"state": "ar"}, "construction loses preceding returned wave")
    base_mutator = m.g.by_id[core_evidence["mutation"]["old_mutator"]]
    for arg, source_arg in (("field_distance", "field_distance"), ("target_field", "target_field"), ("control", "mutator_control")):
        _exact(proposal["args"][arg], base_mutator["args"][source_arg], "construction changes old situated mutator context")
    m.earlier(proposal, encoder, "descriptor published before its old-mutator proposal")

    # Follow acceptance backwards to discover the old and safe-candidate score.
    acceptance = a.call(diagnostics["accepted"], "accept", "accepted")
    _exact(diagnostics["improvement"], _ref(acceptance, "improvement"), "return loses actual acceptance improvement")
    valid = acceptance["args"]["valid"]
    candidate_guard = a.helper(valid, "development_candidate_valid", "valid")
    code = a.g.choose(a.calls("construct_code"), "missing resident code construction")
    boxes = a.g.choose(a.calls("construct_boxes"), "missing resident box construction")
    a.words(code, CODE, old, "code constructor incumbent")
    a.words(boxes, (*BOXES, "node_count"), old, "box constructor incumbent")
    decoder = a.helper(code["args"]["valid"], "development_descriptor_decode", "valid")
    for name in ("x", "y", "half", "valid"):
        _exact(boxes["args"][name], _ref(decoder, name), "box constructor loses published descriptor " + name)
    _exact(candidate_guard["args"]["proposed"], _ref(decoder, "valid"), "candidate validity loses proposal eligibility")
    for i in range(5):
        reference = decoder["args"][f"reserved_{i}"]
        _need(a.g.read_dependency(reference, {"key": meta["record_key"]}, "published", f"reserved_{i}"),
              "action descriptor must read the same current resource record")
        _need(set(reference) == {"node", "output"} and reference["output"] == f"reserved_{i}"
              and a.g.by_id[reference["node"]].get("op") == "read_record",
              "descriptor must read matching published record word directly")
    a.earlier(decoder, code, "code construction precedes published descriptor decoding")
    a.earlier(decoder, boxes, "box construction precedes published descriptor decoding")
    candidate = {**{k: _ref(code, k) for k in CODE}, **{k: _ref(boxes, k) for k in BOXES}}

    # Only matching live and candidate programs may supply admission gates.
    old_checks, candidate_checks = a.validation(old), a.validation(candidate)
    for checks in (old_checks, candidate_checks):
        _exact(checks[1]["args"]["quota"], states["quota"], "geometry gate changes protected quota")
    _exact(candidate_guard["args"]["code"], _ref(candidate_checks[0], "valid"), "candidate validity loses code gate")
    _exact(candidate_guard["args"]["geometry"], _ref(candidate_checks[3], "valid"), "candidate validity loses both geometry gates")
    for check in candidate_checks:
        a.earlier(check, candidate_guard, "candidate eligibility computed before its validation")
    guard = a.g.choose(a.g.helpers(meta["helpers"]["development_require_live"]), "missing live program fail guard",
                       lambda n: n["args"].get("code") == _ref(old_checks[0], "valid")
                       and n["args"].get("geometry") == _ref(old_checks[3], "valid"))
    for check in old_checks:
        a.earlier(check, guard, "live program fail guard precedes validation")
    for name in ("query_x", "query_y", "enabled"):
        _exact(guard["args"][name], states[name], "live guard loses configured " + name)

    retained_nodes = []
    safe = {}
    for group, names in (("code", CODE), ("boxes", BOXES)):
        selected = a.helper(current[names[0]], "development_select_" + group, names[0])
        retained_nodes.append(selected)
        safe.update({k: selected["args"]["new_" + k] for k in names})
    retained_nodes = a.select(current, _ref(acceptance, "accepted"), safe, old)
    safe_nodes = a.select(safe, valid, candidate, old)
    for node in safe_nodes:
        a.earlier(candidate_guard, node, "candidate masking precedes validity")
    old_score, old_samples = a.score(acceptance["args"]["old_score"], old, after=(guard,))
    candidate_score, candidate_samples = a.score(acceptance["args"]["candidate_score"], safe, after=(guard, *safe_nodes))
    a.earlier(old_score, acceptance, "acceptance precedes incumbent score")
    a.earlier(candidate_score, acceptance, "acceptance precedes candidate score")
    for node in retained_nodes:
        a.earlier(acceptance, node, "retained program selected before acceptance")

    # Cached score/witness selection uses the same accepted bit and the same
    # matching old/candidate result. It is not a third recomputation.
    score_selector = a.helper(diagnostics["score"], "development_select_score", "score")
    _exact(score_selector["args"]["condition"], _ref(acceptance, "accepted"), "score selection differs from program selection")
    for name in meta["source"]["bindings"]["score"]["outputs"]:
        _exact(score_selector["args"]["new_" + name], _ref(candidate_score, name), "selected score loses matching candidate " + name)
        _exact(score_selector["args"]["old_" + name], _ref(old_score, name), "selected score loses matching incumbent " + name)
        if name in diagnostics:
            _exact(diagnostics[name], _ref(score_selector, name), "returned witness/score differs from accepted program")
    _exact(diagnostics["previous_score"], _ref(old_score, "score"), "previous_score must be freshly evaluated incumbent score")
    final_query = a.interpret(diagnostics["distance"], current,
                             query={"x": states["query_x"], "y": states["query_y"]},
                             after=(guard, *retained_nodes))
    diagnostic_node = a.helper(diagnostics["admitted"], "development_diagnostics", "admitted")
    _exact(diagnostic_node["args"]["distance"], diagnostics["distance"], "admission loses retained-program distance")
    _exact(diagnostic_node["args"]["trials"], states["trials"], "trial counter loses preceding state")
    _exact(diagnostics["trials"], _ref(diagnostic_node, "trials"), "trial counter return is incomplete")

    # A detached or eagerly evaluated raw-candidate interpreter is not harmless.
    chains = [*old_samples, *candidate_samples, final_query]
    for role, field in (("leaf_distances", "leaf"), ("interpret_prefix", "prefix"),
                        ("interpret_middle", "middle"), ("interpret", "final")):
        _exact({n["id"] for n in a.calls(role)}, {entry[field] for entry in chains},
               "unaccounted eager " + role + " call bypasses protected program flow")
    _exact({n["id"] for n in a.calls("score")}, {old_score["id"], candidate_score["id"]},
           "unaccounted score does not belong to incumbent/candidate comparison")
    for node in a.g.nodes:
        if node.get("op") == "read_record":
            _need(node.get("bank") == "published", "action reads a stale record bank")
    return {"profile": PROFILE, "passed": True, "core": core_evidence,
            "resource_record": {"key": meta["record_key"], "source_index": meta["source_index"]},
            "program_words": len(PROGRAM), "protocol_helpers": helper_evidence,
            "old_mutator": proposal["id"], "descriptor_publication": encoder["id"],
            "descriptor_read": decoder["id"], "live_guard": guard["id"],
            "constructors": [code["id"], boxes["id"]], "candidate_guard": candidate_guard["id"],
            "safe_program": [n["id"] for n in safe_nodes], "acceptance": acceptance["id"],
            "retained_program": [n["id"] for n in retained_nodes],
            "old_samples": old_samples, "candidate_samples": candidate_samples,
            "selected_score_witness": score_selector["id"], "retained_query": final_query,
            "score_publication": "Matching cached incumbent/candidate score and witness selected by the same accepted bit as every returned program word; not a third score recomputation.",
            "scope": "Full source-graph obligations plus exact named program-word wiring, fixed protocol-selector/guard expression checks, current situated record dispatch and guarded eager interpreter coverage. Domain binding arithmetic requires independent numerical/geometry validation; this is not evidence of runtime execution, sensitivity, novelty, improvement, learning or unrestricted synthesis."}


# Match the conventional source-fidelity entry-point spelling as well.
audit_graph = audit_development_graph
