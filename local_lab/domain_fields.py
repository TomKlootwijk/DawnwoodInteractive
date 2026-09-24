"""Authored domain constraints with declared metrics and exactness classes.

This module does not modify or invoke Dawnwood's GPU recurrence. Public API:
    catalogue() -> dict
    evaluate({"example": "enzyme_pool", "values": {...}, "parameters": {...}})
    evaluate({"primitive": {"type": "sphere", "center": [...], "radius": 1},
              "values": [...]})

The analytic formulas are exact over real numbers in their stated metric;
evaluation uses ordinary Python float64. No external packages or eval are used.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
import sys

PROFILE = "DW-Domain-0.1 CPU bindings"
ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "domain_knowledge"
MAX_INPUT = 1e12
MIN_SCALE = 1e-12


def _number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    result = float(value)
    if not math.isfinite(result) or abs(result) > MAX_INPUT:
        raise ValueError(f"{label} must be finite with absolute value <= {MAX_INPUT:g}")
    return result


def _positive(value, label):
    result = _number(value, label)
    if result < MIN_SCALE:
        raise ValueError(f"{label} must be >= {MIN_SCALE:g}")
    return result


def _nonnegative(value, label):
    result = _number(value, label)
    if result < 0:
        raise ValueError(f"{label} must be nonnegative")
    return result


def _integer(value, label, minimum=0, maximum=4294967295):
    result = _number(value, label)
    if not result.is_integer() or not minimum <= result <= maximum:
        raise ValueError(f"{label} must be an integer in [{minimum}, {maximum}]")
    return int(result)


def _vector(value, label, length=None):
    if not isinstance(value, list) or not 1 <= len(value) <= 16:
        raise ValueError(f"{label} must be a list with 1 to 16 coordinates")
    if length is not None and len(value) != length:
        raise ValueError(f"{label} must have {length} coordinates")
    return [_number(x, f"{label}[{i}]") for i, x in enumerate(value)]


def _merge(defaults, supplied, label):
    if not isinstance(supplied, dict):
        raise ValueError(f"{label} must be an object")
    extra = set(supplied) - set(defaults)
    if extra:
        raise ValueError(f"Unknown {label}: {', '.join(sorted(extra))}")
    return {**copy.deepcopy(defaults), **supplied}


def catalogue():
    """Return catalogue metadata with each example expanded to its editable data."""
    data = json.loads((KNOWLEDGE / "catalogue.json").read_text(encoding="utf-8"))
    data["examples"] = [json.loads((KNOWLEDGE / "examples" / f"{name}.json")
                                   .read_text(encoding="utf-8"))
                        for name in data["examples"]]
    data["primitive_types"] = ["halfspace", "hyperplane", "slab", "sphere", "box"]
    return data


def _dot(a, b):
    return math.fsum(x * y for x, y in zip(a, b))


def _plane(point, normal, offset):
    length = math.hypot(*normal)
    if length < MIN_SCALE:
        raise ValueError("The normal must have nonzero length >= 1e-12")
    unit = [x / length for x in normal]
    distance = (_dot(normal, point) - offset) / length
    witness = [x - distance * n for x, n in zip(point, unit)]
    return distance, unit, witness


def _slab(point, normal, low, high):
    if high < low:
        raise ValueError("Slab upper bound must be >= lower bound")
    signed, unit, _ = _plane(point, normal, (low + high) / 2)
    length = math.hypot(*normal)
    halfwidth = (high - low) / (2 * length)
    direction = 1.0 if signed >= 0 else -1.0
    chosen_normal = [direction * n for n in unit]
    distance = abs(signed) - halfwidth
    witness = [x - distance * n for x, n in zip(point, chosen_normal)]
    gradient = chosen_normal if signed != 0 else None
    return distance, gradient, witness


def _sphere(point, center, radius):
    delta = [x - c for x, c in zip(point, center)]
    length = math.hypot(*delta)
    chosen_normal = [d / length for d in delta] if length else [1.0] + [0.0] * (len(point) - 1)
    witness = [c + radius * n for c, n in zip(center, chosen_normal)]
    return length - radius, chosen_normal if length else None, witness


def _box(point, center, half_extents, rounding=0.0):
    delta = [x - c for x, c in zip(point, center)]
    q = [abs(d) - h for d, h in zip(delta, half_extents)]
    outside = [max(v, 0.0) for v in q]
    outside_length = math.hypot(*outside)
    original_distance = outside_length + min(max(q), 0.0)
    signs = [1.0 if d >= 0 else -1.0 for d in delta]
    if outside_length:
        chosen_normal = [s * v / outside_length for s, v in zip(signs, outside)]
        gradient = chosen_normal
    else:
        index = max(range(len(q)), key=q.__getitem__)
        chosen_normal = [0.0] * len(point)
        chosen_normal[index] = signs[index]
        unique_face = sum(v == q[index] for v in q) == 1 and delta[index] != 0
        gradient = chosen_normal if unique_face else None
    distance = original_distance - rounding
    witness = [x - distance * n for x, n in zip(point, chosen_normal)]
    return distance, gradient, witness


def _field(identifier, label, value, kind, unit, formula, metric, assumptions,
           source_urls, relation="le", tolerance=0.0, gradient=None, witness=None):
    inside = abs(value) <= tolerance if relation == "eq" else value <= tolerance
    result = {
        "id": identifier, "label": label, "value": value, "kind": kind,
        "unit": unit, "inside": inside, "passes": inside,
        "constraint": "abs(value) <= tolerance" if relation == "eq" else "value <= tolerance",
        "relation": relation, "tolerance": tolerance,
        "formula": formula, "metric": metric, "assumptions": assumptions,
        "source_urls": source_urls, "gradient": gradient,
    }
    if gradient is not None:
        result["gradient_norm"] = math.hypot(*gradient)
    if witness is not None:
        result["nearest_boundary"] = {"point": witness, "distance": abs(value),
                                      "coordinates": metric["axes"],
                                      "scope": "This individual field only; other constraints may fail."}
    elif kind == "residual":
        result["nearest_boundary"] = None
    return result


def _report(example, values, parameters, fields, notes=None, derived=None):
    result = {
        "profile": PROFILE, "name": example["name"], "example": example.get("id"),
        "domain": example["domain"], "values": values, "parameters": parameters,
        "fields": fields, "feasible": all(field["inside"] for field in fields),
        "notes": ["This report is CPU reference evaluation; it does not load or run GPU operators.",
                  "Exactness is analytic in the declared metric; evaluation uses float64.",
                  "Conjunction checks all fields separately, without claiming an exact intersection SDF."] + (notes or []),
        "assumptions": example.get("assumptions", []),
        "derived": derived or {},
    }
    # Reject any derived overflow rather than emitting non-standard JSON NaN/Infinity.
    try:
        json.dumps(result, allow_nan=False)
    except ValueError as exc:
        raise ValueError("Inputs produced a nonfinite derived value") from exc
    return result


def _example_eval(example, values, params, source_urls):
    identifier = example["id"]
    assumptions = example["assumptions"]
    values = {key: _number(value, f"values.{key}") for key, value in values.items()}
    fields = []

    def add(fid, label, calculation, formula, metric, unit, relation="le", tolerance=0.0, kind="exact_sdf"):
        distance, gradient, witness = calculation
        fields.append(_field(fid, label, distance, kind, unit, formula, metric,
                             assumptions, source_urls, relation, tolerance, gradient, witness))

    if identifier == "enzyme_pool":
        scale = _positive(params["concentration_scale_uM"], "concentration_scale_uM")
        et = _nonnegative(params["E_total"], "E_total")
        st = _nonnegative(params["S_total"], "S_total")
        tolerance = _nonnegative(params["equality_tolerance"], "equality_tolerance")
        point = [values[k] / scale for k in ("E", "ES", "S", "P")]
        metric = {"axes": ["E/scale", "ES/scale", "S/scale", "P/scale"],
                  "point": point, "scale_uM": scale, "type": "Euclidean"}
        unit = "normalized concentration coordinate"
        add("enzyme_conservation", "Enzyme-moiety conservation", _plane(point, [1, 1, 0, 0], et / scale),
            "(E+ES-E_total)/(scale*sqrt(2))", metric, unit, "eq", tolerance)
        add("substrate_conservation", "Substrate-moiety conservation", _plane(point, [0, 1, 1, 1], st / scale),
            "(ES+S+P-S_total)/(scale*sqrt(3))", metric, unit, "eq", tolerance)
        for i, key in enumerate(("E", "ES", "S", "P")):
            normal = [0.0] * 4
            normal[i] = -1.0
            add(f"nonnegative_{key}", f"{key} nonnegative", _plane(point, normal, 0), f"-{key}/scale", metric, unit)
        derived = {"enzyme_total_uM": values["E"] + values["ES"],
                   "substrate_moiety_total_uM": values["ES"] + values["S"] + values["P"]}
        return _report(example, values, params, fields, ["A conservation hyperplane uses an equality constraint; its sign identifies a side, not a permitted concentration region."], derived)

    if identifier == "buffer_window":
        params = {k: _number(v, f"parameters.{k}") for k, v in params.items()}
        point = [values["log10_acid_activity"], values["log10_base_activity"]]
        metric = {"axes": ["log10_acid_activity", "log10_base_activity"], "point": point, "type": "Euclidean in logarithmic activities"}
        low, high = params["pH_min"] - params["pKa"], params["pH_max"] - params["pKa"]
        kind = "unsigned_distance" if low == high else "exact_sdf"
        add("pH_window", "Specified pH interval", _slab(point, [-1, 1], low, high),
            "(abs(pKa+log10_base_activity-log10_acid_activity-(pH_min+pH_max)/2)-(pH_max-pH_min)/2)/sqrt(2)",
            metric, "log10-activity coordinate", kind=kind)
        return _report(example, values, params, fields, derived={"pH": params["pKa"] + point[1] - point[0]})

    if identifier == "enzyme_kinetics":
        km = _positive(params["Km_uM"], "Km_uM")
        vmax = _positive(params["Vmax_uM_per_s"], "Vmax_uM_per_s")
        tolerance = _nonnegative(params["residual_tolerance"], "residual_tolerance")
        substrate = _nonnegative(values["substrate_uM"], "substrate_uM")
        point = [substrate / km, values["rate_uM_per_s"] / vmax]
        metric = {"axes": ["substrate/Km", "rate/Vmax"], "point": point,
                  "type": "Euclidean in normalized concentration/rate coordinates; kinetic residual is not distance"}
        predicted = point[0] / (1.0 + point[0])
        residual = point[1] - predicted
        fields.append(_field("kinetic_consistency", "Initial-rate law residual", residual, "residual", "fraction of Vmax",
                             "rate/Vmax - substrate/(Km+substrate)", metric, assumptions, source_urls,
                             "eq", tolerance, [-1.0 / (1.0 + point[0]) ** 2, 1.0]))
        add("rate_nonnegative", "Nonnegative rate", _plane(point, [0, -1], 0), "-rate/Vmax", metric, "normalized rate coordinate")
        add("rate_limit", "Rate no larger than limiting rate", _plane(point, [0, 1], 1), "rate/Vmax-1", metric, "normalized rate coordinate")
        return _report(example, values, params, fields,
                       ["No nearest-Euclidean-boundary claim is made for the kinetic residual; its gradient is not unit length."],
                       {"predicted_rate_uM_per_s": vmax * predicted, "supplied_rate_fraction": point[1]})

    if identifier == "gpu_resource_budget":
        values["states"] = _integer(values["states"], "states")
        _nonnegative(values["epoch_ms"], "epoch_ms")
        for key in ("budget_mib", "state_scale", "time_scale_ms"):
            params[key] = _positive(params[key], key)
        for key in ("reserve_mib", "overhead_mib", "deadline_ms"):
            params[key] = _nonnegative(params[key], key)
        for key in ("state_bytes", "copies"):
            params[key] = _integer(params[key], key, 1)
        point = [values["states"] / params["state_scale"], values["epoch_ms"] / params["time_scale_ms"]]
        metric = {"axes": ["states/state_scale", "epoch_ms/time_scale_ms"], "point": point, "type": "Euclidean in declared normalized resource coordinates"}
        per_scale = params["state_bytes"] * params["copies"] * params["state_scale"] / 1048576.0
        available = params["budget_mib"] - params["reserve_mib"] - params["overhead_mib"]
        # Unit normal avoids rejecting a physically small bytes-per-coordinate coefficient.
        add("memory_budget", "Modeled memory within declared budget", _plane(point, [1, 0], available / per_scale),
            "states/state_scale - (budget_mib-reserve_mib-overhead_mib)*1048576/(state_bytes*copies*state_scale)", metric, "normalized state-count coordinate")
        add("time_budget", "Supplied epoch time within deadline", _plane(point, [0, 1], params["deadline_ms"] / params["time_scale_ms"]),
            "(epoch_ms-deadline_ms)/time_scale_ms", metric, "normalized time coordinate")
        return _report(example, values, params, fields, derived={
            "state_payload_mib": values["states"] * params["state_bytes"] * params["copies"] / 1048576.0,
            "model_total_mib": values["states"] * params["state_bytes"] * params["copies"] / 1048576.0 + params["overhead_mib"],
            "continuous_state_capacity": available * 1048576.0 / (params["state_bytes"] * params["copies"])})

    if identifier == "spatial_clearance":
        point = [values[k] for k in ("x", "y", "z")]
        sphere_center = _vector(params["sphere_center"], "sphere_center", 3)
        box_center = _vector(params["box_center"], "box_center", 3)
        extents = _vector(params["box_half_extents"], "box_half_extents", 3)
        extents = [_positive(v, f"box_half_extents[{i}]") for i, v in enumerate(extents)]
        radius = _positive(params["sphere_radius"], "sphere_radius")
        clearance = _nonnegative(params["clearance_m"], "clearance_m")
        metric = {"axes": ["x_m", "y_m", "z_m"], "point": point, "type": "Euclidean"}
        for fid, label, result, formula in [
            ("sphere_clearance", "Clearance from sphere", _sphere(point, sphere_center, radius + clearance), "sphere_radius+clearance-norm(point-sphere_center)"),
            ("box_clearance", "Clearance from box", _box(point, box_center, extents, clearance), "clearance-box_sdf(point)"),
        ]:
            distance, gradient, witness = result
            add(fid, label, (-distance, [-v for v in gradient] if gradient is not None else None, witness), formula, metric, "m")
        return _report(example, values, params, fields)
    raise ValueError(f"Unsupported example: {identifier}")


def _primitive(spec):
    descriptor = spec["primitive"]
    if not isinstance(descriptor, dict):
        raise ValueError("primitive must be an object")
    kind = descriptor.get("type")
    keys = {"halfspace": {"normal", "offset"}, "hyperplane": {"normal", "offset", "tolerance"},
            "slab": {"normal", "low", "high"}, "sphere": {"center", "radius"},
            "box": {"center", "half_extents"}}
    if kind not in keys:
        raise ValueError("primitive.type must be halfspace, hyperplane, slab, sphere or box")
    extra = set(descriptor) - keys[kind] - {"type", "unit"}
    if extra:
        raise ValueError(f"Unknown primitive parameters: {', '.join(sorted(extra))}")
    point = _vector(spec.get("values"), "values")
    unit = descriptor.get("unit", "declared coordinate unit")
    if not isinstance(unit, str) or not 1 <= len(unit) <= 80:
        raise ValueError("primitive.unit must be a nonempty string up to 80 characters")
    metric = {"axes": [f"x{i}" for i in range(len(point))], "point": point, "type": "Euclidean, equally scaled axes"}
    relation, tolerance, category = "le", 0.0, "exact_sdf"
    try:
        if kind in ("halfspace", "hyperplane", "slab"):
            normal = _vector(descriptor["normal"], "normal", len(point))
            if kind == "slab":
                low, high = _number(descriptor["low"], "low"), _number(descriptor["high"], "high")
                result = _slab(point, normal, low, high)
                formula = "(abs(normal dot x-(low+high)/2)-(high-low)/2)/norm(normal)"
                if low == high:
                    category = "unsigned_distance"
            else:
                result = _plane(point, normal, _number(descriptor["offset"], "offset"))
                formula = "(normal dot x-offset)/norm(normal)"
                if kind == "hyperplane":
                    relation = "eq"
                    tolerance = _nonnegative(descriptor.get("tolerance", 1e-9), "tolerance")
        else:
            center = _vector(descriptor["center"], "center", len(point))
            if kind == "sphere":
                result = _sphere(point, center, _positive(descriptor["radius"], "radius"))
                formula = "norm(x-center)-radius"
            else:
                extents = _vector(descriptor["half_extents"], "half_extents", len(point))
                extents = [_positive(v, f"half_extents[{i}]") for i, v in enumerate(extents)]
                result = _box(point, center, extents)
                formula = "q=abs(x-center)-half_extents; norm(max(q,0))+min(max(q),0)"
    except KeyError as exc:
        raise ValueError(f"Missing primitive parameter: {exc.args[0]}") from exc
    distance, gradient, witness = result
    example = {"name": f"Analytic {kind}", "domain": "Euclidean geometry",
               "assumptions": ["Coordinates share the stated unit and Euclidean scale.",
                               "Analytic boundary projection is for this individual primitive."]}
    field = _field(kind, example["name"], distance, category, unit, formula, metric,
                   example["assumptions"], [], relation, tolerance, gradient, witness)
    return _report(example, point, descriptor, [field])


def evaluate(spec):
    """Evaluate one bounded domain specification; invalid inputs raise ValueError."""
    if not isinstance(spec, dict):
        raise ValueError("Specification must be an object")
    extra = set(spec) - {"example", "values", "parameters", "primitive"}
    if extra:
        raise ValueError(f"Unknown specification keys: {', '.join(sorted(extra))}")
    if "primitive" in spec:
        if "example" in spec or "parameters" in spec:
            raise ValueError("A primitive specification uses primitive and values only")
        return _primitive(spec)
    data = catalogue()
    examples = {example["id"]: example for example in data["examples"]}
    identifier = spec.get("example")
    if not isinstance(identifier, str) or identifier not in examples:
        raise ValueError("Unknown example; choose " + ", ".join(examples))
    example = examples[identifier]
    values = _merge(example["values"], spec.get("values", {}), "values")
    parameters = _merge(example["parameters"], spec.get("parameters", {}), "parameters")
    # Validate all scalar/list values, even when a particular formula would not use them.
    for name, value in parameters.items():
        if isinstance(value, list):
            _vector(value, f"parameters.{name}")
        else:
            _number(value, f"parameters.{name}")
    sources = [data["sources"][key]["url"] for key in example["source_ids"]]
    return _example_eval(example, values, parameters, sources)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--example", help="Example id from --catalogue")
    group.add_argument("--spec", type=Path, help="JSON specification file")
    group.add_argument("--catalogue", action="store_true")
    parser.add_argument("--values", default="{}", help="JSON object overriding example values")
    parser.add_argument("--parameters", default="{}", help="JSON object overriding example parameters")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.catalogue:
            result = catalogue()
        elif args.spec:
            if args.values != "{}" or args.parameters != "{}":
                raise ValueError("Use either --spec or --values/--parameters overrides")
            if args.spec.stat().st_size > 65536:
                raise ValueError("Specification file exceeds 64 KiB")
            result = evaluate(json.loads(args.spec.read_text(encoding="utf-8-sig")))
        else:
            if len(args.values) + len(args.parameters) > 65536:
                raise ValueError("JSON overrides exceed 64 KiB")
            result = evaluate({"example": args.example, "values": json.loads(args.values),
                               "parameters": json.loads(args.parameters)})
        text = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
        print(text, end="")
        return 0
    except (ValueError, OSError, OverflowError) as exc:
        print(json.dumps({"profile": PROFILE, "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
