"""Author a resident enzyme-pool application inside the eight-stage source cycle.

The host compiles declarations and a feasible initial corner. Proposal, chemical
distance, projection, objective, acceptance and feedback execute as resident
expression-bank definitions. The biochemical metric is separate from the Klein
carrier metric. This is an explicit specialization, not a recovered source law.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
import math
from pathlib import Path
import sys

try:
    from . import source_cycle as base
    from . import source_resident_v2 as resident
except ImportError:
    import source_cycle as base
    import source_resident_v2 as resident

ir = base.ir
ROOT = base.ROOT
INPUT_PROFILE = "DWI-ENZYME-0.1"
DEFAULT_INPUTS = ROOT / "source_bindings/examples/enzyme_inputs.json"
DOMAIN_STATE = [
    "obs_E_normalized", "obs_S_normalized", "obs_ES_normalized", "obs_P_normalized",
    "enzyme_y0", "enzyme_y1", "enzyme_objective", "enzyme_trial_sdf",
    "enzyme_improvement", "enzyme_accepted", "enzyme_E_uM", "enzyme_S_uM",
    "enzyme_ES_uM", "enzyme_P_uM", "enzyme_gap_estimate", "enzyme_step",
    "enzyme_trial_y0", "enzyme_trial_y1", "enzyme_projection_distance",
    "enzyme_previous_objective",
]
STATE = [*base.STATE, *DOMAIN_STATE]
SID = {name: index for index, name in enumerate(STATE)}
OBS = ["obs_E", "obs_S", "obs_ES", "obs_P"]
PROTECTED_ROLES = {
    "101": "enzyme_domain_sdf",
    "102": "enzyme_project_evaluate",
    "103": "enzyme_accept",
    "104": "enzyme_witness_gap",
}
V, add, sub, mul, div = base.V, base.add, base.sub, base.mul, base.div
sq, lt, choose, clamp, op = base.sq, base.lt, base.choose, base.clamp, base.op


def number(value, where):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{where}: expected a finite number")
    return float(value)


def validate_inputs(document):
    ir.exact_keys(document, {"profile", "pools", "observations"}, {"profile", "pools", "observations"}, "inputs")
    if document["profile"] != INPUT_PROFILE:
        raise ValueError(f"inputs.profile must be {INPUT_PROFILE}")
    pools = document["pools"]
    keys = {"E_total_uM", "S_total_uM", "concentration_scale_uM"}
    ir.exact_keys(pools, keys, keys, "inputs.pools")
    et, st, scale = [number(pools[key], f"inputs.pools.{key}") for key in
                     ("E_total_uM", "S_total_uM", "concentration_scale_uM")]
    if not 0 < et < st or not scale > 0:
        raise ValueError("Pool constants require 0 < E_total_uM < S_total_uM and concentration_scale_uM > 0")
    en, sn = et / scale, st / scale
    if not 1e-4 <= en or not 1e-4 <= sn - en or not sn <= 1e4 or scale > 1e6:
        raise ValueError("This FP32 edition requires normalized E_total and S_total-E_total >= 1e-4, S_total <= 1e4, and scale <= 1e6 uM")
    # The actual packed constants must still describe four nondegenerate edges.
    ep, sp, cp = [ir.fp32(value, "packed pool constant")[0] for value in (en, sn, scale)]
    if not 0 < ep < sp or cp <= 0:
        raise ValueError("Pool geometry degenerates after FP32 encoding")
    rows = document["observations"]
    if not isinstance(rows, list) or not 1 <= len(rows) <= 1000000:
        raise ValueError("inputs.observations: expected 1..1000000 observation objects")
    ids = set()
    for index, row in enumerate(rows):
        where = f"inputs.observations[{index}]"
        ir.exact_keys(row, {"id", "E_uM", "S_uM", "ES_uM", "P_uM"},
                      {"id", "E_uM", "S_uM", "ES_uM", "P_uM"}, where)
        if not isinstance(row["id"], str) or not row["id"] or row["id"] in ids:
            raise ValueError(f"{where}.id: expected a unique nonempty string")
        ids.add(row["id"])
        for key in ("E_uM", "S_uM", "ES_uM", "P_uM"):
            observed = number(row[key], f"{where}.{key}")
            if abs(observed / scale) > 1e4:
                raise ValueError(f"{where}.{key}: normalized observation magnitude exceeds 1e4")
            ir.fp32(observed / scale, f"{where}.{key} normalized")
    return en, sn, scale


def species(y0, y1, et, st):
    c = mul(math.sqrt(2 / 5), y0)
    p = mul(.5, sub(mul(math.sqrt(2), y1), c))
    return [sub(et, c), sub(sub(st, c), p), c, p]


def target(observed, et, st):
    e, s, c, p = observed
    chat = div(base.sum_([2 * et, st, mul(-2, e), base.neg(s), mul(2, c), base.neg(p)]), 5)
    phat = div(base.sum_([-et, 2 * st, e, mul(-2, s), base.neg(c), mul(3, p)]), 5)
    return [mul(math.sqrt(5 / 2), chat), div(add(chat, mul(2, phat)), math.sqrt(2))]


def objective(y0, y1, observed, et, st):
    return base.sum_([sq(sub(value, observation)) for value, observation in zip(species(y0, y1, et, st), observed)])


def vertices(et, st):
    return [(0., 0.), (math.sqrt(5 / 2) * et, et / math.sqrt(2)),
            (math.sqrt(5 / 2) * et, (2 * st - et) / math.sqrt(2)),
            (0., math.sqrt(2) * st)]


def add_functions(bank, et, st, scale):
    """Application arithmetic is exclusively authored scalar-expression data."""
    observed = [V(name) for name in OBS]
    y = [V("y0"), V("y1")]
    desired = target(observed, et, st)
    common_inputs = ["y0", "y1", *OBS, *base.PAIR, "B0", "B1", "B2", "B3",
                     "A00", "A01", "A10", "A11", "dt", "field_distance"]
    drive = base.sum_([
        mul(.1, base.sum_([V("ar"), base.neg(V("ai")), V("br"), base.neg(V("bi"))])),
        mul(.02, base.sum_([V("B0"), base.neg(V("B1")), V("B2"), base.neg(V("B3"))])),
        mul(.03, base.sum_([V("A00"), base.neg(V("A01")), V("A10"), base.neg(V("A11"))])),
        mul(.2, V("field_distance")), mul(.01, V("dt")),
    ])
    gate = mul(.5, add(1, op("sin", drive)))
    proposal_signature = bank.next_signature
    for name, low, span in [("enzyme_proposal_fast", .45, .45), ("enzyme_proposal_cautious", .1, .25)]:
        alpha = add(low, mul(span, gate))
        bank.fn(name, common_inputs,
                {"trial_y0": sub(y[0], mul(alpha, sub(y[0], desired[0]))),
                 "trial_y1": sub(y[1], mul(alpha, sub(y[1], desired[1]))), "step": alpha},
                "Resident projected-gradient proposal before projection. The current returned wave, all four B values, all four inverse entries, interval and this record's current carrier field control the bounded step. Scientific totals and metric are unchanged.",
                requires=[lt(0, V("dt"))], signature=proposal_signature)
    bank.next_signature += 1

    polygon = vertices(et, st)
    closest = []
    for index, a in enumerate(polygon):
        b = polygon[(index + 1) % len(polygon)]
        edge = [b[j] - a[j] for j in range(2)]
        fraction = clamp(div(base.sum_([mul(sub(y[j], a[j]), edge[j]) for j in range(2)]),
                             sum(component * component for component in edge)), 0, 1)
        point = [add(a[j], mul(fraction, edge[j])) for j in range(2)]
        distance2 = base.sum_([sq(sub(y[j], point[j])) for j in range(2)])
        closest.append([distance2, *point])
    best = closest[0]
    for candidate in closest[1:]:
        better = lt(candidate[0], best[0])
        best = [choose(better, candidate[j], best[j]) for j in range(3)]
    decoded = species(y[0], y[1], et, st)
    outside = op("max", op("max", lt(decoded[0], 0), lt(decoded[1], 0)),
                 op("max", lt(decoded[2], 0), lt(decoded[3], 0)))
    distance = op("sqrt", best[0])
    bank.fn("enzyme_domain_sdf", ["y0", "y1"],
            {"distance": choose(outside, distance, base.neg(distance)), "boundary_y0": best[1], "boundary_y1": best[2]},
            "Exact-arithmetic Euclidean signed distance and nearest boundary witness of the enzyme conservation-plane trapezoid in its isometric coordinates. Negative inside, zero on its boundary. This is a resident chemical distance operator, not the Klein carrier disk; FP32 evaluates the formula approximately.")

    px = choose(lt(0, V("distance")), V("boundary_y0"), V("trial_y0"))
    py = choose(lt(0, V("distance")), V("boundary_y1"), V("trial_y1"))
    bank.fn("enzyme_project_evaluate", ["trial_y0", "trial_y1", "distance", "boundary_y0", "boundary_y1", *OBS],
            {"candidate_y0": px, "candidate_y1": py, "objective": objective(px, py, observed, et, st),
             "projection_distance": op("max", 0, V("distance"))},
            "Resident projection using the exact polygon-distance witness: preserve an inside proposal, otherwise use its nearest boundary point. Evaluate equal-weight squared error of all four normalized concentrations. No host projection or physical-law mutation.")

    change = [sub(V(f"candidate_y{i}"), V(f"incumbent_y{i}")) for i in range(2)]
    difference = base.sum_([add(mul(2, mul(sub(V(f"incumbent_y{i}"), desired[i]), change[i])), sq(change[i]))
                            for i in range(2)])
    accepted = lt(difference, 0)
    bank.fn("enzyme_accept", ["incumbent_y0", "incumbent_y1", "candidate_y0", "candidate_y1",
                              "incumbent_objective", "candidate_objective", *OBS],
            {"y0": choose(accepted, V("candidate_y0"), V("incumbent_y0")),
             "y1": choose(accepted, V("candidate_y1"), V("incumbent_y1")),
             "objective": choose(accepted, V("candidate_objective"), V("incumbent_objective")),
             "improvement": choose(accepted, base.neg(difference), 0),
             "accepted": accepted},
            "Protected resident acceptance law: evaluate the cancellation-resistant intrinsic quadratic difference 2*(old_y-y_target) dot delta + ||delta||^2, exactly equal to the full four-species objective change in real arithmetic. Accept only a negative difference; retain full objective diagnostics. This avoids subtraction of large common normal-distance errors. A declined proposal is a successful cycle, not a VM transaction failure.")

    decoded = species(y[0], y[1], et, st)
    gradient = [mul(2, sub(y[j], desired[j])) for j in range(2)]
    gap = 0
    for vertex in polygon:
        gap = op("max", gap, base.sum_([mul(gradient[j], sub(y[j], vertex[j])) for j in range(2)]))
    bank.fn("enzyme_witness_gap", ["y0", "y1", *OBS],
            {**{name: mul(scale, value) for name, value in zip(["E_uM", "S_uM", "ES_uM", "P_uM"], decoded)},
             "objective": objective(y[0], y[1], observed, et, st), "gap_estimate": gap},
            "Decode the accepted resident plane point into E,S,ES,P in uM and compute the full normalized squared-error objective. max_vertex grad(J) dot(y-vertex) is an exact-arithmetic convex upper bound on suboptimality for a feasible point. Its FP32 evaluation is an estimate, not a rigorously rounded certificate.")

    for name in ["enzyme_proposal_fast", "enzyme_proposal_cautious", *PROTECTED_ROLES.values()]:
        bank.functions[name]["binding"]["source"] = "DWI-ENZYME-0.1 authored application of the resident source-cycle binding; fixed-volume E+S <=> ES -> E+P moiety conservation; see docs/ENZYME_POOL_DOMAIN_GROUNDING.md"
    bank.families["blend"]["methods"].update({"100": "enzyme_proposal_fast", **PROTECTED_ROLES})
    bank.families["blend_enzyme_cautious"] = deepcopy(bank.families["blend"])
    bank.families["blend_enzyme_cautious"]["methods"]["100"] = "enzyme_proposal_cautious"


def protect_laws(bank):
    interface = bank.families["blend"]["interface"]
    expected_roles = set(bank.families["blend"]["methods"])
    for name, family in bank.families.items():
        if family["interface"] != interface:
            continue
        if set(family["methods"]) != expected_roles:
            raise ValueError(f"{name}: enzyme strategies must share the complete typed interface")
        for role, function in {"0": "blend_role0", **PROTECTED_ROLES}.items():
            if family["methods"][role] != function:
                raise ValueError(f"{name}: protected resident law role {role} differs")
        if family["methods"]["100"] not in {"enzyme_proposal_fast", "enzyme_proposal_cautious"}:
            raise ValueError(f"{name}: undeclared enzyme proposal strategy")


def extend_mutation(definition, bank):
    new_inputs = ["domain_trial_sdf", "domain_improvement", "domain_accepted"]
    signal = base.sum_([V(new_inputs[0]), mul(-.05, V(new_inputs[1])),
                       mul(.02, sub(1, V(new_inputs[2]))), mul(.001, sub(V("ai"), V("br")))])
    next_body = choose(lt(signal, 0), bank.family("blend"), bank.family("blend_enzyme_cautious"))
    for family_name in ["mutation", "mutation_successor"]:
        name = bank.families[family_name]["methods"]["0"]
        binding = bank.functions[name]["binding"]
        binding["inputs"].extend(new_inputs)
        binding["outputs"]["body_handle"] = choose(base.eq(V("target_index"), base.INDEX["blend"]),
                                                   next_body, binding["outputs"]["body_handle"])
        chemical_feedback = base.sum_([mul(.02, op("sin", V("domain_trial_sdf"))),
                                       mul(.01, op("sin", V("domain_improvement"))),
                                       mul(.01, sub(mul(2, V("domain_accepted")), 1))])
        binding["outputs"]["control"] = add(binding["outputs"]["control"],
                                              mul(base.eq(V("target_index"), base.INDEX["mutation"]), chemical_feedback))
        binding.setdefault("requires", []).append(base.bit_guard(V("domain_accepted")))
        binding["meaning"] += " For the blend record, prior chemical trial distance, improvement, acceptance and old wave select a compatible proposal family; protected chemical laws retain identical handles. Only the mutation record's control also receives bounded chemical feedback, closing the path to subsequent core hinge choices while preserving old-snapshot publication."
    words = definition["mutation_plan"]
    matches = [i for i, row in enumerate(words) if row[:5] == [4, base.INDEX["mutation"], 0, 0, 200]]
    if len(matches) != 1 or words[0] != [1, 0, 0, len(base.STATE), 0, 0, 0, 0]:
        raise ValueError("Base mutation plan shape changed; application extension requires review")
    step = matches[0]
    extra = [[10, 212 + j, SID[name], 1, 0, 0, 0, 0] for j, name in enumerate(
             ["enzyme_trial_sdf", "enzyme_improvement", "enzyme_accepted"])]
    words[step:step] = extra
    words[0][3] = len(STATE)
    for call in definition["source"]["mutation_calls"]:
        if call["step"] >= step:
            call["step"] += len(extra)
        if call.get("record") == base.INDEX["mutation"] and call.get("slot") == 0:
            call["inputs"].extend([SID[name] for name in ["enzyme_trial_sdf", "enzyme_improvement", "enzyme_accepted"]])


def extend_action(definition, bank):
    original = deepcopy(definition["action_plan"])
    if original[0] != [1, 0, 0, len(base.STATE), 0, 0, 0, 0] or [row[0] for row in original[-44:]] != [6] * 44:
        raise ValueError("Base action plan shape changed; application extension requires review")
    p = base.Plan(bank)
    p.words = definition["action_plan"]
    p.words[0][3] = len(STATE)
    p.calls = definition["source"]["action_calls"]
    begin = len(p.words)
    # The original 44 state writes are provisional until the entire epoch
    # commits. With those sources consumed, registers0..43 are safe scratch.
    obs = dict(zip(OBS, range(44, 48)))
    current = {"y0": 48, "y1": 49, **obs}
    returned = {name: 160 + i for i, name in enumerate(base.PAIR)}
    p.situated("blend", 100, {**current, **returned, **{f"B{i}": 140 + i for i in range(4)},
                               **dict(zip(["A00", "A01", "A10", "A11"], range(148, 152))), "dt": 8}, 0)
    p.situated("blend", 101, {"y0": 0, "y1": 1}, 5)
    p.situated("blend", 102, {"trial_y0": 0, "trial_y1": 1, "distance": 5,
                               "boundary_y0": 6, "boundary_y1": 7, **obs}, 8)
    p.situated("blend", 104, current, 12)
    p.situated("blend", 103, {"incumbent_y0": 48, "incumbent_y1": 49,
                               "candidate_y0": 8, "candidate_y1": 9,
                               "incumbent_objective": 16, "candidate_objective": 10, **obs}, 18)
    p.situated("blend", 104, {"y0": 18, "y1": 19, **obs}, 23)
    outputs = [44, 45, 46, 47, 18, 19, 27, 5, 21, 22, 23, 24, 25, 26, 28, 2, 0, 1, 11, 16]
    for name, register in zip(DOMAIN_STATE, outputs):
        p.emit(6, SID[name], register, 1)
    # Existing source actions and all eight stages survive in order. Changing
    # the initial state read width is the sole difference in this prefix.
    checked = deepcopy(p.words[:len(original)])
    checked[0][3] = len(base.STATE)
    if checked != original:
        raise ValueError("Domain insertion altered the original source-cycle action prefix")
    definition["source"]["stage_boundaries"][-1]["action_step_end_exclusive"] = len(p.words)
    return {"phase": "surface_return", "action_step_start": begin, "action_step_end_exclusive": len(p.words),
            "placement": "After the original44 provisional state writes, before the epoch transaction commits.",
            "original_action_prefix_preserved": True, "base_action_steps": len(original)}


def build_definition(model, cycle, inputdoc):
    et, st, scale = validate_inputs(inputdoc)
    definition = base.build_definition(model, cycle, len(inputdoc["observations"]))
    bank = object.__new__(base.Bank)
    bank.functions, bank.families = definition["functions"], definition["families"]
    bank.next_signature = max(function["signature"] for function in bank.functions.values()) + 1
    add_functions(bank, et, st, scale)
    protect_laws(bank)
    extend_mutation(definition, bank)
    action = extend_action(definition, bank)
    definition["state_names"] = STATE
    for instance, row in zip(definition["instances"], inputdoc["observations"]):
        observed = [row[name] / scale for name in ["E_uM", "S_uM", "ES_uM", "P_uM"]]
        state = instance["state"]
        state.update({name: 0 for name in DOMAIN_STATE})
        state.update(dict(zip(DOMAIN_STATE[:4], observed)))
        # A declared feasible corner initializes the recurrence; this is not
        # an observation-dependent solution or a host projection.
        cost = sum((value - observation) ** 2 for value, observation in zip([et, st, 0, 0], observed))
        state.update(enzyme_objective=cost, enzyme_E_uM=inputdoc["pools"]["E_total_uM"],
                     enzyme_S_uM=inputdoc["pools"]["S_total_uM"], enzyme_previous_objective=cost)
    metadata = {
        "input_profile": INPUT_PROFILE, "pools": deepcopy(inputdoc["pools"]), "concentration_unit": "uM",
        "normalized_constants": {"E_total": et, "S_total": st},
        "packed_fp32_constants": {name: ir.fp32(value, name)[0] for name, value in
                                  {"E_total": et, "S_total": st, "concentration_scale_uM": scale}.items()},
        "observation_ids": [row["id"] for row in inputdoc["observations"]],
        "input_sha256": ir.sha256(ir.json_bytes(inputdoc)), "input_hash_encoding": "canonical JSON via source_ir.json_bytes",
        "input_document": deepcopy(inputdoc), "state_layout": {name: SID[name] for name in DOMAIN_STATE},
        "state_meaning": "Normalized observations and intrinsic accepted/trial coordinates; physical returned species in uM; objective and gap in squared normalized-concentration units; domain distance in normalized-concentration units.",
        "species_order": ["E", "S", "ES", "P"],
        "plane": "x=(ET-c,ST-c-p,c,p), all normalized by concentration_scale_uM",
        "isometry": "y=(sqrt(5/2)*c,(c+2*p)/sqrt(2)); Euclidean y distance equals Euclidean four-species distance within the conservation plane",
        "geometry": "0<=c<=ET, 0<=p, c+p<=ST; exact-arithmetic convex trapezoid SDF in the intrinsic plane, not a signed solid in R4",
        "law_functions": dict(PROTECTED_ROLES), "proposal_functions": ["enzyme_proposal_fast", "enzyme_proposal_cautious"],
        "proposal_families": ["blend", "blend_enzyme_cautious"],
        "law_identity_policy": "Every reachable blend interface family retains identical role0 and role101..104 function handles; only role100 proposal varies. The bank and role map are immutable during execution.",
        "law_hashes": {name: ir.sha256(ir.json_bytes(bank.functions[name])) for name in PROTECTED_ROLES.values()},
        "source_record": {"key": "blend", "index": 14, "body_symbol": "Math_blend", "field_symbol": "Math_blend_SDF", "placement_symbol": "Phyllotaxis_on_Klein"},
        "carrier_domain_separation": "The original field slot remains a Klein geodesic disk. The additional resident body role101 is the chemical SDF. No concentration is identified with u or v, and carrier distance never changes the scientific domain/evaluator/acceptance laws.",
        "resident_application": action,
        "adaptation": "The old mutation definition reads the preceding trial SDF, improvement, acceptance and wave; it selects the next blend proposal family in the same old-snapshot transaction as all other records, while retaining original mutator self-change. For the mutation record only, add 0.02*sin(prior_trial_sdf)+0.01*sin(prior_improvement)+0.01*(2*prior_accepted-1) to its control. This bounded computational feedback reaches later core hinge decisions; it is not chemical kinetics.",
        "feedback": "All eight source phases produce the current wave, B history and inverse matrix used in a situated domain proposal; accepted chemical-state metrics return in the same committed state and control the next resident mutation.",
        "objective": "Minimize equal-weight squared discrepancy of E,S,ES,P from supplied observations, constrained by the two supplied conserved pools and nonnegative species. This is consistency reconciliation, not kinetics or clinical inference.",
        "gap_status": "FP32 estimate of an exact-arithmetic convex upper bound, not a rigorously rounded certificate or an exact-nearest claim. Independent original-unrounded-data audit is required for a numerical accuracy claim.",
        "acceptance": "Use intrinsic quadratic difference DeltaJ=2*(old_y-y_target) dot(candidate_y-old_y)+||candidate_y-old_y||^2 < 0. Improvement is -DeltaJ for accepted proposals. Full four-species objective is separately recomputed for diagnostics; its subtraction does not decide acceptance.",
        "diagnostic_validity": "Gap, trial and acceptance diagnostics are evaluated only after at least one committed epoch; the epoch-zero initializer is not an evaluated optimality estimate.",
        "initialization": "Every observation starts at the explicit feasible corner ES=P=0, E=ET, S=ST. No host projection, optimization or reference-solution lookup.",
        "status": "Authored executable application binding; execution and independent numerical evidence pending.",
    }
    definition["source"]["enzyme"] = metadata
    definition["source"]["enzyme_generator_sha256"] = ir.sha256(Path(__file__).read_bytes())
    definition["source"]["base_cycle_generator_sha256"] = ir.sha256(Path(base.__file__).read_bytes())
    definition["meaning"] = "The complete authored eight-stage source cycle with resident enzyme-pool proposal, exact-arithmetic domain SDF, projection, evaluation, acceptance, returned concentrations and self-mutating proposal strategy. The chemical SDF is an added typed Math_blend body role situated through its existing Klein field/placement; the carrier disk is not reinterpreted as chemistry."
    definition["status"] = "Executable explicit specialization; verification evidence recorded separately."
    return definition


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("compile")
    command.add_argument("--model", type=Path, default=base.MODEL)
    command.add_argument("--cycle", type=Path, default=base.CYCLE)
    command.add_argument("--inputs", type=Path, default=DEFAULT_INPUTS)
    command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    model, model_raw = ir.read_json(args.model)
    cycle, cycle_raw = ir.read_json(args.cycle)
    inputdoc, input_raw = ir.read_json(args.inputs)
    definition = build_definition(model, cycle, inputdoc)
    program, manifest = resident.compile_definition(model, definition)
    manifest.update(source_cycle_lowered=True, domain_application_implemented=True,
                    scope="authored_eight_stage_resident_enzyme_pool_reconciliation_with_typed_chemical_SDF")
    manifest["source_model"] = {"path": str(args.model.resolve()), "sha256": ir.sha256(model_raw)}
    manifest["source_cycle"] = {"path": str(args.cycle.resolve()), "sha256": ir.sha256(cycle_raw),
                                "stage_boundaries": definition["source"]["stage_boundaries"], "definition": cycle}
    files = {"source_model.json": model_raw, "source_cycle.json": cycle_raw, "inputs.json": input_raw,
             "definition.json": ir.json_bytes(definition), "program.bin": program,
             "source_enzyme_generator.py": Path(__file__).read_bytes(),
             "source_cycle_generator.py": Path(base.__file__).read_bytes(),
             "resident_binding_dependency.json": base.RESIDENT.read_bytes()}
    manifest["files"] = {name: {"bytes": len(data), "sha256": ir.sha256(data)} for name, data in files.items()}
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        (output / name).write_bytes(data)
    (output / "manifest.json").write_bytes(ir.json_bytes(manifest))
    print(json.dumps({"output": str(output), "profile": definition["profile"], "application_profile": INPUT_PROFILE,
                      "program_sha256": ir.sha256(program), "bytes": len(program), "instances": len(definition["instances"]),
                      "functions": len(definition["functions"]), "families": len(definition["families"]),
                      "state_width": len(STATE), "mutation_steps": len(definition["mutation_plan"]),
                      "action_steps": len(definition["action_plan"]), "domain_application_implemented": True}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, KeyError, RecursionError, OverflowError) as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(1)
