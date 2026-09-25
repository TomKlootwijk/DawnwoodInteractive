"""Explicit source bindings for resident construction of resource-distance ASTs.

The AI authors the grammar, domain policy and constructors. These bindings
declare methods for constructing opcode/reference data, evaluating it and
deciding which definition to retain. This module does not integrate that
resident loop, solve a request or supply an evolved program to the runtime.
"""
from __future__ import annotations

from copy import deepcopy
import math

from . import source_cycle as c
from . import source_ir_v2 as ir
from . import development_sdf as sdf

PROFILE = "DWI-SDF-DEVELOPMENT-BINDINGS-0.1"
PROOF_MARGIN = 1e-4
MIN_HALF_EXTENT = 1e-5
MAX_TRAINING = 12
CODE_NAMES = tuple(f"{field}{i}" for i in range(sdf.MAX_NODES) for field in ("op", "a", "b"))
BOX_NAMES = tuple(f"{field}{i}" for i in range(sdf.MAX_BOXES) for field in ("cx", "cy", "hx", "hy"))
HEADER_NAMES = ("node_count", "root", "revision")
PROGRAM_NAMES = HEADER_NAMES + CODE_NAMES + BOX_NAMES
PROGRAM_TYPES = {name: ("program_size" if name == "node_count" else
                        "program_revision" if name == "revision" else
                        "program_opcode" if name.startswith("op") else
                        "resource_coordinate" if name in BOX_NAMES else "program_index")
                 for name in PROGRAM_NAMES}
V, add, sub, mul, div, lt, eq, choose = c.V, c.add, c.sub, c.mul, c.div, c.lt, c.eq, c.choose


def minimum(*values):
    value = values[0]
    for other in values[1:]:
        value = c.op("min", value, other)
    return value


def maximum(*values):
    value = values[0]
    for other in values[1:]:
        value = c.op("max", value, other)
    return value


def both(*conditions):
    value = 1
    for condition in conditions:
        value = mul(value, condition)
    return value


def either(*conditions):
    return minimum(1, c.sum_(conditions))


def select(index, values):
    """Pure indexed selection; protected callers validate the index first."""
    result = 0
    for i, value in reversed(list(enumerate(values))):
        result = choose(eq(index, i), value, result)
    return result


def _entry(inputs, outputs, expressions, meaning, requires=()):
    binding = {"inputs": list(inputs), "outputs": expressions,
               "requires": list(requires), "source": PROFILE,
               "meaning": meaning,
               "status": "Authored numerical binding; resident integration and independent execution evidence required."}
    ir.validate_binding(binding, PROFILE)
    compiler = ir.ExpressionCompiler(binding["inputs"])
    for condition in binding["requires"]:
        compiler._emit(17, compiler.expression(condition, "requires"))
    for name, expression in expressions.items():
        compiler.expression(expression, name)
    return {"inputs": inputs, "outputs": outputs, "binding": binding}


def pack_program(program):
    result = {name: float(program[name]) for name in HEADER_NAMES}
    for i, node in enumerate(program["nodes"]):
        result.update({f"{field}{i}": float(value) for field, value in zip(("op", "a", "b"), node)})
    for i, box in enumerate(program["boxes"]):
        result.update({f"{field}{i}": float(value) for field, value in zip(("cx", "cy", "hx", "hy"), box)})
    return result


def unpack_program(values):
    """Decode program words without repairing malformed integer controls.

    Structural admission is mandatory here; geometric admission remains the
    caller's separate policy decision. Coordinates are packed to FP32 exactly
    as in the standalone domain library.
    """
    ir.exact_keys(values, PROGRAM_NAMES, PROGRAM_NAMES, "program words")
    integer_words = {}
    for name in HEADER_NAMES + CODE_NAMES:
        value = values[name]
        if (type(value) not in (int, float) or value < 0 or value > sdf.MAX_REVISION
                or not math.isfinite(value) or value != int(value)):
            raise ValueError(f"{name}: expected an exact nonnegative resident integer")
        integer_words[name] = int(value)
    packed_boxes = [[ir.fp32(values[f"{field}{i}"], f"{field}{i}")[0]
                     for field in ("cx", "cy", "hx", "hy")]
                    for i in range(sdf.MAX_BOXES)]
    result = {**{name: integer_words[name] for name in HEADER_NAMES},
              "nodes": [[integer_words[f"{field}{i}"] for field in ("op", "a", "b")]
                        for i in range(sdf.MAX_NODES)],
              "boxes": [[0.0 if value == 0 else value for value in box] for box in packed_boxes]}
    # This public serializer validates structure without imposing a quota.
    sdf.canonical_program_bytes(result)
    return result


def make_bindings(training_points, *, base_half_extent=.045, complexity_cost=.02, area_cost=.005,
                  admission_margin=PROOF_MARGIN):
    """Return inspectable typed expressions; all program words are runtime inputs.

    The resident constructor appends a new leaf and an explicit union node.
    Its generated subset is the canonical left-associated postorder grammar;
    the standalone domain validator also handles other valid postorder trees.
    """
    if not isinstance(training_points, list) or not 1 <= len(training_points) <= MAX_TRAINING:
        raise ValueError(f"Supply 1..{MAX_TRAINING} explicit training requests")
    points = []
    for row in training_points:
        if not isinstance(row, (list, tuple)) or len(row) != 2:
            raise ValueError("Each training request has two normalized resource coordinates")
        packed = [ir.fp32(value, "training coordinate")[0] for value in row]
        if any(value < 0 or value > 16 for value in packed):
            raise ValueError("Training coordinates must lie in the declared [0,16] numerical envelope")
        points.append(packed)
    if any(not math.isfinite(x) or x <= 0 for x in (base_half_extent, complexity_cost, area_cost)):
        raise ValueError("Policy magnitudes must be finite and positive")
    if type(admission_margin) not in (int, float) or not math.isfinite(admission_margin) or not PROOF_MARGIN <= admission_margin <= 2 * PROOF_MARGIN:
        raise ValueError("Admission margin must lie between one and two proof margins")
    result = {}

    # The old resident mutator creates an edit descriptor. Geometry/goal feedback
    # can change its size; protected quota semantics cannot be changed by it.
    inputs = {"witness_x": "resource_coordinate", "witness_y": "resource_coordinate",
              "witness_distance": "resource_distance", "node_count": "program_size",
              "quota": "resource_coordinate", "control": "control", "ar": "amplitude",
              "field_distance": "carrier_distance", "target_field": "carrier_distance"}
    drive = add(add(V("control"), V("ar")), add(V("field_distance"), V("target_field")))
    size = mul(base_half_extent, add(.75, mul(.25, mul(.5, add(1, c.op("sin", drive))))))
    half = maximum(0, minimum(size, sub(V("witness_x"), 4 * PROOF_MARGIN),
                              sub(V("witness_y"), 4 * PROOF_MARGIN),
                              mul(.5, sub(sub(sub(V("quota"), 4 * PROOF_MARGIN), V("witness_x")), V("witness_y"))),
                              mul(.25, V("witness_distance"))))
    valid = both(lt(V("node_count"), sdf.MAX_NODES), lt(MIN_HALF_EXTENT, half), lt(0, V("witness_distance")))
    result["propose_edit"] = _entry(inputs,
        {"x": "resource_coordinate", "y": "resource_coordinate", "half": "resource_coordinate", "valid": "bit"},
        {"x": V("witness_x"), "y": V("witness_y"), "half": half, "valid": valid},
        "Construct a new square-leaf proposal around the preceding uncovered demand witness. Its half diagonal is less than half the old boundary distance, and a four-margin quota/nonnegative guard bounds its extent. The old situated mutator's field, target field, control and wave influence extent.")

    inputs = {name: PROGRAM_TYPES[name] for name in HEADER_NAMES + CODE_NAMES}
    inputs["valid"] = "bit"
    expressions = {"node_count": choose(V("valid"), add(V("node_count"), 2), V("node_count")),
                   "root": choose(V("valid"), add(V("node_count"), 1), V("root")),
                   "revision": choose(V("valid"), add(V("revision"), 1), V("revision"))}
    for i in range(sdf.MAX_NODES):
        leaf = both(V("valid"), eq(i, V("node_count")))
        union = both(V("valid"), eq(i, add(V("node_count"), 1)))
        expressions[f"op{i}"] = choose(leaf, sdf.NODE_BOX, choose(union, sdf.NODE_SEPARATED_UNION, V(f"op{i}")))
        expressions[f"a{i}"] = choose(leaf, mul(.5, add(V("node_count"), 1)), choose(union, V("root"), V(f"a{i}")))
        expressions[f"b{i}"] = choose(leaf, 0, choose(union, V("node_count"), V(f"b{i}")))
    result["construct_code"] = _entry(inputs, {name: PROGRAM_TYPES[name] for name in expressions}, expressions,
        "Write a new BOX opcode and a new SEPARATED_UNION opcode with actual computed backward references. Previous nodes are retained. This creates expression structure as mutable program data; it does not select a whole precompiled SDF program.", [c.bit_guard(V("valid"))])

    inputs = {name: PROGRAM_TYPES[name] for name in BOX_NAMES}
    inputs.update(node_count="program_size", x="resource_coordinate", y="resource_coordinate", half="resource_coordinate", valid="bit")
    expressions = {}
    for i in range(sdf.MAX_BOXES):
        change = both(V("valid"), eq(i, mul(.5, add(V("node_count"), 1))))
        for field, value in (("cx", "x"), ("cy", "y"), ("hx", "half"), ("hy", "half")):
            expressions[f"{field}{i}"] = choose(change, V(value), V(f"{field}{i}"))
    result["construct_boxes"] = _entry(inputs, {name: PROGRAM_TYPES[name] for name in expressions}, expressions,
        "Materialize only the newly constructed leaf constants; inactive box slots remain zero.", [c.bit_guard(V("valid"))])

    # Structural checks run once for a live definition, before interpreting it.
    inputs = {name: PROGRAM_TYPES[name] for name in HEADER_NAMES + CODE_NAMES}
    legal_count = either(*(eq(V("node_count"), count) for count in (1, 3, 5, 7)))
    guards = [legal_count, eq(V("root"), sub(V("node_count"), 1)), c.le(0, V("revision")),
              eq(V("revision"), c.op("floor", V("revision"))), c.le(V("revision"), 16777215)]
    for i in range(sdf.MAX_NODES):
        active = lt(i, V("node_count"))
        is_leaf = i == 0 or i % 2 == 1
        op = sdf.NODE_BOX if is_leaf else sdf.NODE_SEPARATED_UNION
        a = (0 if i == 0 else (i + 1) // 2) if is_leaf else i - 2
        b = 0 if is_leaf else i - 1
        guards.extend([eq(V(f"op{i}"), choose(active, op, 0)),
                       eq(V(f"a{i}"), choose(active, a, 0)),
                       eq(V(f"b{i}"), choose(active, b, 0))])
    result["validate_code"] = _entry(inputs, {"valid": "bit"}, {"valid": both(*guards)},
        "Validate the generated canonical postorder grammar, active node count, root, inactive zero words and exact revision. Invalid live code must fail a protected guard before interpretation.")

    inputs = {name: PROGRAM_TYPES[name] for name in BOX_NAMES}
    inputs.update(node_count="program_size", quota="resource_coordinate")
    leaves = mul(.5, add(V("node_count"), 1))
    guards = [lt(8 * PROOF_MARGIN, V("quota")), c.le(V("quota"), 16)]
    for i in range(sdf.MAX_BOXES):
        active = lt(i, leaves)
        cx, cy, hx, hy = [V(f"{field}{i}") for field in ("cx", "cy", "hx", "hy")]
        legal = both(lt(MIN_HALF_EXTENT, hx), lt(MIN_HALF_EXTENT, hy),
                     c.le(admission_margin, sub(cx, hx)), c.le(admission_margin, sub(cy, hy)),
                     c.le(add(add(cx, hx), add(cy, hy)), sub(V("quota"), admission_margin)))
        zero = both(*(eq(V(f"{field}{i}"), 0) for field in ("cx", "cy", "hx", "hy")))
        guards.append(choose(active, legal, zero))
    result["validate_geometry_boxes"] = _entry(inputs, {"valid_boxes": "bit"}, {"valid_boxes": both(*guards)},
        "First protected geometry stage: check positive extents, nonnegative resource demand, conservative quota corners and inactive zero boxes. Combine this result with validate_geometry_separation before using a candidate.")

    inputs = {name: PROGRAM_TYPES[name] for name in BOX_NAMES}
    inputs["node_count"] = "program_size"
    guards = []
    for i in range(sdf.MAX_BOXES):
        active = lt(i, leaves)
        cx, cy, hx, hy = [V(f"{field}{i}") for field in ("cx", "cy", "hx", "hy")]
        for j in range(i):
            gap = maximum(sub(c.op("abs", sub(cx, V(f"cx{j}"))), add(hx, V(f"hx{j}"))),
                          sub(c.op("abs", sub(cy, V(f"cy{j}"))), add(hy, V(f"hy{j}"))))
            guards.append(choose(active, lt(PROOF_MARGIN, gap), 1))
    result["validate_geometry_separation"] = _entry(inputs, {"valid_separation": "bit"}, {"valid_separation": both(*guards)},
        "Second protected geometry stage: check positive pairwise axis separation for active boxes. The structural validator must establish the active count; the box and separation results must both pass.")
    result["validate_geometry"] = _entry({"valid_boxes": "bit", "valid_separation": "bit"}, {"valid": "bit"},
        {"valid": both(V("valid_boxes"), V("valid_separation"))},
        "Combine both protected geometry stages. Independent exact-rational packed-constant validation supplies the stronger mathematical certificate.",
        [c.bit_guard(V("valid_boxes")), c.bit_guard(V("valid_separation"))])

    inputs = {"x": "resource_coordinate", "y": "resource_coordinate", **{name: PROGRAM_TYPES[name] for name in BOX_NAMES}}
    distances = {}
    for i in range(sdf.MAX_BOXES):
        dx = sub(c.op("abs", sub(V("x"), V(f"cx{i}"))), V(f"hx{i}"))
        dy = sub(c.op("abs", sub(V("y"), V(f"cy{i}"))), V(f"hy{i}"))
        outside = c.op("sqrt", add(c.sq(maximum(dx, 0)), c.sq(maximum(dy, 0))))
        distances[f"d{i}"] = add(outside, minimum(maximum(dx, dy), 0))
    result["leaf_distances"] = _entry(inputs, {name: "resource_distance" for name in distances}, distances,
        "Euclidean signed distance to each supplied rectangle. Inactive zero rectangles are never referenced by a valid active AST. The protected metric uses the same memory scale for both coordinates.")

    # Materialized node values cross explicit call boundaries. This keeps each
    # scalar SSA program below the unchanged 256-instruction limit while the
    # opcodes, references and root remain runtime program data.
    for stage, start, stop in (("interpret_prefix", 0, 3),
                               ("interpret_middle", 3, 5),
                               ("interpret", 5, sdf.MAX_NODES)):
        inputs = {f"{field}{i}": PROGRAM_TYPES[f"{field}{i}"]
                  for i in range(start, stop) for field in ("op", "a", "b")}
        inputs.update({f"d{i}": "resource_distance" for i in range(sdf.MAX_BOXES)})
        inputs.update({f"v{i}": "resource_distance" for i in range(start)})
        if stage == "interpret":
            inputs["root"] = "program_index"
        values = [V(f"v{i}") for i in range(start)]
        expressions = {}
        for i in range(start, stop):
            box = select(V(f"a{i}"), [V(f"d{j}") for j in range(sdf.MAX_BOXES)])
            union = minimum(select(V(f"a{i}"), values), select(V(f"b{i}"), values)) if values else 0
            value = choose(eq(V(f"op{i}"), sdf.NODE_BOX), box,
                           choose(eq(V(f"op{i}"), sdf.NODE_SEPARATED_UNION), union, 0))
            values.append(value)
            expressions[f"v{i}"] = value
        if stage == "interpret":
            expressions = {"distance": select(V("root"), values)}
        result[stage] = _entry(inputs, {name: "resource_distance" for name in expressions}, expressions,
            f"Interpret runtime AST nodes {start} through {stop - 1}, using supplied earlier-node values. BOX selects a runtime leaf and SEPARATED_UNION composes runtime child results. The final stage selects the runtime root. Run all three stages after structural and geometry validation; validated strict separation makes min an exact-arithmetic signed union distance.")

    inputs = {f"d{i}": "resource_distance" for i in range(len(points))}
    inputs.update(node_count="program_size", **{name: PROGRAM_TYPES[name] for name in BOX_NAMES})
    covered = c.sum_([c.le(V(f"d{i}"), -PROOF_MARGIN) for i in range(len(points))])
    leaves = mul(.5, add(V("node_count"), 1))
    area = c.sum_([choose(lt(i, leaves), mul(4, mul(V(f"hx{i}"), V(f"hy{i}"))), 0) for i in range(sdf.MAX_BOXES)])
    worst, wx, wy = V("d0"), points[0][0], points[0][1]
    for i in range(1, len(points)):
        change = lt(worst, V(f"d{i}"))
        wx, wy = choose(change, points[i][0], wx), choose(change, points[i][1], wy)
        worst = maximum(worst, V(f"d{i}"))
    outputs = {"score": "objective", "coverage": "coefficient", "witness_x": "resource_coordinate", "witness_y": "resource_coordinate", "witness_distance": "resource_distance", "area": "resource_area"}
    result["score"] = _entry(inputs, outputs,
        {"score": sub(sub(covered, mul(complexity_cost, leaves)), mul(area_cost, area)),
         "coverage": covered, "witness_x": wx, "witness_y": wy, "witness_distance": worst, "area": area},
        "Score declared training-demand coverage with explicit leaf-count and area penalties; return the worst uncovered request as next-epoch construction evidence. This is application policy, not a discovered physical law.")
    result["accept"] = _entry({"old_score": "objective", "candidate_score": "objective", "valid": "bit"},
        {"accepted": "bit", "improvement": "objective"},
        {"accepted": both(V("valid"), lt(add(V("old_score"), 1e-6), V("candidate_score"))),
         "improvement": choose(both(V("valid"), lt(add(V("old_score"), 1e-6), V("candidate_score"))), sub(V("candidate_score"), V("old_score")), 0)},
        "Retain a geometrically admissible candidate only for a measured improvement of the declared objective; otherwise preserve the complete incumbent program.", [c.bit_guard(V("valid"))])
    return result
