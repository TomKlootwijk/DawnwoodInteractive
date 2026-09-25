"""Bounded, compositional resource SDF programs and independent geometry checks.

All stored coordinates and policy scalars are explicitly packed to binary32.
The formula evaluator then uses binary64.  Exact certificates and the separate
edge-projection oracle use the rational values of those packed constants.
This module does not install a resident program, run a GPU, or search for one.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import math
import struct

PROFILE = "DWI-DEVELOPMENT-SDF-0.1"
MAX_BOXES = 4
MAX_NODES = 7
MAX_REVISION = 16777215
NODE_INACTIVE = 0
NODE_BOX = 1
NODE_SEPARATED_UNION = 2
OPCODES = {"inactive": NODE_INACTIVE, "box": NODE_BOX,
           "separated_union": NODE_SEPARATED_UNION}
PROGRAM_KEYS = frozenset({"nodes", "boxes", "node_count", "root", "revision"})
CANONICAL_BINARY_FORMAT = (
    "DWI-DEVELOPMENT-SDF-0.1: ASCII DWSDF001, then little-endian uint32 "
    "node_count,root,revision; 7 opcode/a/b uint32 triples; 4 cx/cy/hx/hy "
    "binary32 quadruples. This is a source-program hash encoding, not a resident VM image.")


class ProgramFormatError(ValueError):
    """Malformed source structure, operand encoding, or policy configuration."""


class CandidateGeometryError(ValueError):
    """Well-formed program which fails a declared exact geometric gate."""

    def __init__(self, report):
        self.report = report
        failed = [gate["name"] for gate in report["geometric_gates"] if not gate["passed"]]
        super().__init__("Candidate geometry failed: " + ", ".join(failed))


def _integer(value, where, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ProgramFormatError(f"{where}: expected integer in {low}..{high}")
    return value


def _packed(value, where):
    if type(value) not in (int, float):
        raise ProgramFormatError(f"{where}: expected a finite real number, not a boolean")
    try:
        authored = float(value)
        raw = struct.pack("<f", authored)
        packed = struct.unpack("<f", raw)[0]
    except (OverflowError, ValueError, struct.error) as error:
        raise ProgramFormatError(f"{where}: not representable as finite binary32") from error
    if not math.isfinite(authored) or not math.isfinite(packed):
        raise ProgramFormatError(f"{where}: expected finite binary32")
    # Signed zero has the same mathematical region; canonicalize its encoding.
    if packed == 0:
        packed = 0.0
    return packed, authored != packed


def _fraction(value):
    return Fraction.from_float(value)


def _fraction_text(value):
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _policy(beta, proof_margin, separation_margin):
    beta, _ = _packed(beta, "beta")
    proof_margin, _ = _packed(proof_margin, "proof_margin")
    separation_margin, _ = _packed(separation_margin, "separation_margin")
    if not 0 < proof_margin < beta:
        raise ProgramFormatError("Policy requires 0 < packed proof_margin < packed beta")
    if separation_margin < 0:
        raise ProgramFormatError("Policy requires packed separation_margin >= 0")
    return {"beta": beta, "proof_margin": proof_margin, "separation_margin": separation_margin}


def _structure(program):
    if not isinstance(program, dict) or set(program) != PROGRAM_KEYS:
        raise ProgramFormatError("Program requires exactly nodes, boxes, node_count, root, revision")
    count = _integer(program["node_count"], "node_count", 1, MAX_NODES)
    root = _integer(program["root"], "root", 0, count - 1)
    revision = _integer(program["revision"], "revision", 0, MAX_REVISION)
    if root != count - 1:
        raise ProgramFormatError("Root must be the last active postorder node")
    if not isinstance(program["nodes"], list) or len(program["nodes"]) != MAX_NODES:
        raise ProgramFormatError(f"nodes must contain exactly {MAX_NODES} triples")
    if not isinstance(program["boxes"], list) or len(program["boxes"]) != MAX_BOXES:
        raise ProgramFormatError(f"boxes must contain exactly {MAX_BOXES} quadruples")
    nodes, supports, leaves = [], [], set()
    for i, row in enumerate(program["nodes"]):
        if not isinstance(row, list) or len(row) != 3:
            raise ProgramFormatError(f"nodes[{i}]: expected opcode/a/b triple")
        code, a, b = [_integer(v, f"nodes[{i}][{j}]", 0, 0xFFFFFFFF) for j, v in enumerate(row)]
        if i >= count:
            if row != [0, 0, 0]:
                raise ProgramFormatError(f"nodes[{i}]: inactive padding must be [0,0,0]")
        elif code == NODE_BOX:
            if not a < MAX_BOXES or b != 0:
                raise ProgramFormatError(f"nodes[{i}]: box requires index 0..3 and b=0")
            if a in leaves:
                raise ProgramFormatError(f"nodes[{i}]: duplicate box leaf index {a}")
            leaves.add(a)
            supports.append({a})
        elif code == NODE_SEPARATED_UNION:
            if not a < i or not b < i:
                raise ProgramFormatError(f"nodes[{i}]: union references must precede their parent")
            if supports[a].intersection(supports[b]):
                raise ProgramFormatError(f"nodes[{i}]: union children reuse overlapping leaf supports")
            supports.append(supports[a] | supports[b])
        else:
            raise ProgramFormatError(f"nodes[{i}]: active opcode must be box(1) or separated_union(2)")
        nodes.append([code, a, b])
    reached = set()
    def visit(index):
        if index in reached:
            return
        reached.add(index)
        code, a, b = nodes[index]
        if code == NODE_SEPARATED_UNION:
            visit(a)
            visit(b)
    visit(root)
    if reached != set(range(count)):
        raise ProgramFormatError("All active nodes must be reachable from the root")
    boxes, rounding = [], []
    for i, row in enumerate(program["boxes"]):
        if not isinstance(row, list) or len(row) != 4:
            raise ProgramFormatError(f"boxes[{i}]: expected cx/cy/hx/hy quadruple")
        packed_row = []
        for j, value in enumerate(row):
            packed, changed = _packed(value, f"boxes[{i}][{j}]")
            packed_row.append(packed)
            if changed:
                rounding.append({"box": i, "component": j, "authored": float(value), "packed": packed})
        if i not in leaves and any(value != 0 for value in packed_row):
            raise ProgramFormatError(f"boxes[{i}]: unused box slots must be zero")
        boxes.append(packed_row)
    return {"nodes": nodes, "boxes": boxes, "node_count": count, "root": root,
            "revision": revision}, sorted(leaves), rounding


def _canonical_bytes(packed):
    integers = [packed["node_count"], packed["root"], packed["revision"]]
    integers.extend(value for row in packed["nodes"] for value in row)
    coordinates = [value for row in packed["boxes"] for value in row]
    return b"DWSDF001" + struct.pack("<24I16f", *integers, *coordinates)


def _hashes(packed, leaves):
    def shape(index):
        code, a, b = packed["nodes"][index]
        if code == NODE_BOX:
            return ["box"]
        children = [shape(a), shape(b)]
        children.sort(key=_json_bytes)
        return ["separated_union", *children]
    # The region semantics ignore leaf identifiers, union associativity and
    # revision. Sorted binary32 boxes give a canonical union-region identity.
    region_boxes = sorted(struct.pack("<4f", *packed["boxes"][i]).hex() for i in leaves)
    return {"program_sha256": _sha(_canonical_bytes(packed)),
            "topology_sha256": _sha(_json_bytes(shape(packed["root"]))),
            "semantic_sha256": _sha(_json_bytes({"operation": "union_of_boxes", "binary32_boxes": region_boxes}))}


def _pretty(packed):
    def expression(index):
        code, a, b = packed["nodes"][index]
        if code == NODE_BOX:
            cx, cy, hx, hy = packed["boxes"][a]
            return f"box(center=({cx:.9g}, {cy:.9g}), half_extents=({hx:.9g}, {hy:.9g}))"
        return f"separated_union({expression(a)}, {expression(b)})"
    return expression(packed["root"])


def validate_program(program, *, beta=1.0, proof_margin=1e-4, separation_margin=0.0):
    """Validate structure; return separate exact geometric admission gates.

    Malformed programs/policies raise ProgramFormatError. Geometrically invalid
    but well-formed candidates return ``admissible=False`` with exact receipts.
    All proof inequalities concern the packed program and packed policy.
    """
    packed, leaves, rounding = _structure(program)
    policy = _policy(beta, proof_margin, separation_margin)
    quota, margin, separation = [_fraction(policy[k]) for k in ("beta", "proof_margin", "separation_margin")]
    gates, rational_boxes = [], {}
    for index in leaves:
        cx, cy, hx, hy = [_fraction(v) for v in packed["boxes"][index]]
        rational_boxes[index] = (cx, cy, hx, hy)
        lower_x, lower_y = cx-hx, cy-hy
        upper_sum = cx+hx+cy+hy
        gates.append({"name": f"box_{index}_positive_extents", "passed": hx > 0 and hy > 0,
                      "half_extents_exact": [_fraction_text(hx), _fraction_text(hy)]})
        gates.append({"name": f"box_{index}_quota_containment", "passed": lower_x >= margin and lower_y >= margin and upper_sum <= quota-margin,
                      "lower_x_exact": _fraction_text(lower_x), "lower_y_exact": _fraction_text(lower_y),
                      "upper_sum_exact": _fraction_text(upper_sum), "lower_bound_exact": _fraction_text(margin),
                      "upper_sum_bound_exact": _fraction_text(quota-margin)})
    for offset, left in enumerate(leaves):
        for right in leaves[offset+1:]:
            x0,y0,hx0,hy0 = rational_boxes[left]
            x1,y1,hx1,hy1 = rational_boxes[right]
            gaps = [max(Fraction(0), x1-hx1-x0-hx0, x0-hx0-x1-hx1),
                    max(Fraction(0), y1-hy1-y0-hy0, y0-hy0-y1-hy1)]
            distance_squared = sum(gap*gap for gap in gaps)
            gates.append({"name": f"boxes_{left}_{right}_strict_separation",
                          "passed": distance_squared > separation*separation,
                          "axis_gaps_exact": [_fraction_text(gap) for gap in gaps],
                          "distance_squared_exact": _fraction_text(distance_squared),
                          "strict_lower_bound_squared_exact": _fraction_text(separation*separation)})
    admitted = all(gate["passed"] for gate in gates)
    return {"profile": PROFILE, "valid_structure": True, "admissible": admitted,
            "packed_program": packed, "policy": policy, "leaf_indices": leaves,
            "geometric_gates": gates, "input_rounding": rounding, **_hashes(packed, leaves),
            "expression": _pretty(packed), "canonical_binary_format": CANONICAL_BINARY_FORMAT,
            "canonical_binary_bytes": len(_canonical_bytes(packed)),
            "exactness": "Exact Euclidean signed distance in the declared normalized memory coordinates in real arithmetic, conditional on all geometric gates; no exact machine-arithmetic claim."}


def _admitted(program, policy):
    report = validate_program(program, **policy)
    if not report["admissible"]:
        raise CandidateGeometryError(report)
    return report


def _point(point):
    if not isinstance(point, (list, tuple)) or len(point) != 2:
        raise ProgramFormatError("point requires exactly two coordinates")
    return [_packed(value, f"point[{i}]")[0] for i, value in enumerate(point)]


def evaluate_program(program, point, **policy):
    """Evaluate the postorder SDF formula in binary64 at a packed FP32 point."""
    report = _admitted(program, policy)
    packed, values = report["packed_program"], []
    x, y = _point(point)
    for code, a, b in packed["nodes"][:packed["node_count"]]:
        if code == NODE_BOX:
            cx, cy, hx, hy = packed["boxes"][a]
            qx, qy = abs(x-cx)-hx, abs(y-cy)-hy
            values.append(math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0))
        else:
            values.append(min(values[a], values[b]))
    return values[packed["root"]]


def boundary_oracle(program, point, **policy):
    """Independent exact-rational edge projection, followed by binary64 sqrt.

    This does not call evaluate_program or use the box SDF formula. Every edge
    of every separated closed rectangle remains a boundary of the union.
    Ties choose the lowest leaf index, then the lowest edge index.
    """
    report = _admitted(program, policy)
    point_float = _point(point)
    point_exact = tuple(_fraction(value) for value in point_float)
    best = None
    inside = False
    for index in report["leaf_indices"]:
        cx,cy,hx,hy = [_fraction(v) for v in report["packed_program"]["boxes"][index]]
        lx,ux,ly,uy = cx-hx,cx+hx,cy-hy,cy+hy
        inside |= lx <= point_exact[0] <= ux and ly <= point_exact[1] <= uy
        vertices = [(lx,ly),(ux,ly),(ux,uy),(lx,uy)]
        for edge, start in enumerate(vertices):
            end = vertices[(edge+1)%4]
            direction = (end[0]-start[0],end[1]-start[1])
            delta = (point_exact[0]-start[0],point_exact[1]-start[1])
            denominator = direction[0]**2+direction[1]**2
            amount = max(Fraction(0),min(Fraction(1),(delta[0]*direction[0]+delta[1]*direction[1])/denominator))
            witness = (start[0]+amount*direction[0],start[1]+amount*direction[1])
            squared = sum((point_exact[i]-witness[i])**2 for i in range(2))
            candidate = (squared,index,edge,witness)
            if best is None or candidate[:3] < best[:3]:
                best = candidate
    squared,index,edge,witness = best
    distance = math.sqrt(float(squared))
    if inside and distance:
        distance = -distance
    return {"distance": distance, "inside_or_boundary": inside,
            "packed_query": point_float, "boundary": [float(v) for v in witness],
            "boundary_exact": [_fraction_text(v) for v in witness],
            "squared_boundary_distance_exact": _fraction_text(squared),
            "box_index": index, "edge_index": edge,
            "nearest_feasible": point_float if inside else [float(v) for v in witness],
            "oracle": "Independent rational rectangle-edge projections; binary64 square root of the exact squared distance."}


def canonical_program_bytes(program):
    """Hash serialization of structurally valid source; not a native checkpoint."""
    packed, _, _ = _structure(program)
    return _canonical_bytes(packed)


def program_hashes(program):
    packed, leaves, _ = _structure(program)
    return _hashes(packed, leaves)


def pretty_expression(program):
    packed, _, _ = _structure(program)
    return _pretty(packed)


def single_box_program(box, *, revision=0):
    """Author one structurally valid candidate; geometric admission is separate."""
    result = {"nodes": [[1,0,0]]+[[0,0,0] for _ in range(MAX_NODES-1)],
              "boxes": [list(box)]+[[0.,0.,0.,0.] for _ in range(MAX_BOXES-1)],
              "node_count": 1, "root": 0, "revision": revision}
    return _structure(result)[0]


def append_box_candidate(program, box):
    """Reference structural edit: append a new box and a union with the old root.

    This authoring utility is not a search procedure or resident constructor.
    It returns an unchecked geometric candidate, including candidates whose
    exact containment/separation gates fail.
    """
    packed, leaves, _ = _structure(program)
    if packed["node_count"]+2 > MAX_NODES or len(leaves) == MAX_BOXES:
        raise ProgramFormatError("Appending a box exceeds the four-box/seven-node limit")
    if packed["revision"] == MAX_REVISION:
        raise ProgramFormatError("Revision increment exceeds exact resident integer range")
    result = deepcopy(packed)
    index = next(i for i in range(MAX_BOXES) if i not in leaves)
    leaf = packed["node_count"]
    result["boxes"][index] = list(box)
    result["nodes"][leaf] = [NODE_BOX,index,0]
    result["nodes"][leaf+1] = [NODE_SEPARATED_UNION,packed["root"],leaf]
    result.update(node_count=leaf+2,root=leaf+1,revision=packed["revision"]+1)
    return _structure(result)[0]
