"""Author the complete eight-stage numerical source-cycle binding as VM data.

This is an explicit numerical edition, not a claim that the PDFs uniquely
specified its open laws. No application arithmetic is installed in native code.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import sys

try:
    from . import source_ir as ir
except ImportError:
    import source_ir as ir

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "source_workbench/Dawnwood_Interactive_v0.2/model/substrate.json"
CYCLE = ROOT / "source_workbench/Dawnwood_Interactive_v0.2/model/cycle.json"
RESIDENT = ROOT / "source_bindings/resident_v0.1.json"
OUTPUT = ROOT / "source_bindings/cycle_v0.1.json"
PROFILE = "DWI-RESIDENT-0.2"
PHASES = ["operator_mutation", "log_polar", "split_and_hinge", "selected_operator",
          "rk4_four_slots", "geometry_divergence", "rgba_crystal", "surface_return"]
CATALOGUE = [
    ("klein", "SDF_Klein"), ("hadamard", "Hadamard_mitosis"), ("phi", "Log_polar_PHI"),
    ("rk4", "RK4"), ("phyllotaxis", "Fibonacci_phyllotaxis"), ("pinion", "Double_pinion"),
    ("double_dot", "Pinion_double_dot"), ("T_shape", "SDF_T"), ("pyramid", "SDF_pyramid_side"),
    ("circle", "SDF_circle"), ("cone", "SDF_cone"), ("sphere", "SDF_sphere"), ("apex", "SDF_apex"),
    ("delta_phi", "delta_delta_phi"), ("blend", "Math_blend"), ("wavefront", "FT_wavefront"),
    ("y_up", "Y_up"), ("crystal", "Crystal_bifurcation"), ("inverse_T", "Inverse_T"),
    ("T_transform", "T_transformation"), ("jitter", "One_bit_jitter"), ("bst", "BST"),
    ("return", "Nonorientable_return"), ("phase_history", "Phase_history"),
    ("dichromatic", "Dichromatic"), ("bayer", "Bayer_output"), ("bc5", "BC5_pack"),
    ("split", "Bitshift_split"), ("parity", "Parity"), ("psi", "PSI_interval"),
    ("mutation", "Operator_mutation"),
]
INDEX = {key: i for i, (key, _) in enumerate(CATALOGUE)}
STATE = ["u", "v", "orientation", "ar", "ai", "br", "bi", "phase", "dt", "jitter",
         "previous_ar", "previous_ai", "previous_br", "previous_bi", "surface_u", "surface_v",
         "neck", "route_depth", "route_b0", "route_b1", "route_b2", "route_b3", "K_orientation",
         "B0", "B1", "B2", "B3", "phase_previous", "phase_previous2",
         "T00", "T01", "T10", "T11", "A00", "A01", "A10", "A11",
         "Rr", "Ri", "Gr", "Gi", "selected_index", "last_field", "energy"]
SID = {name: i for i, name in enumerate(STATE)}
PAIR = ["ar", "ai", "br", "bi"]
TARGET = 0xFFFFFFFF


def V(name): return {"input": name}
def op(name, *args): return {"op": name, "args": list(args)}
def add(a, b): return op("add", a, b)
def sub(a, b): return op("sub", a, b)
def mul(a, b): return op("mul", a, b)
def div(a, b): return op("div", a, b)
def neg(a): return op("neg", a)
def sq(a): return mul(a, a)
def abs_(a): return op("abs", a)
def lt(a, b): return op("less", a, b)
def choose(c, a, b): return op("select", c, a, b)
def eq(a, b): return sub(1, lt(0, abs_(sub(a, b))))
def clamp(a, lo, hi): return op("min", hi, op("max", lo, a))
def sum_(items):
    result = 0
    for item in items: result = add(result, item)
    return result
def dot(a, b): return sum_([mul(x, y) for x, y in zip(a, b)])
def bit_guard(x): return choose(eq(x, 0), 1, eq(x, 1))
def le(a,b): return sub(1,lt(b,a))
def norm2(x,y):
    maximum=op("max",abs_(x),abs_(y));minimum=op("min",abs_(x),abs_(y))
    safe=choose(lt(0,maximum),maximum,1)
    return mul(maximum,op("sqrt",add(1,sq(div(minimum,safe)))))
def polygon_distance(x,y,vertices,inside):
    candidates=[]
    for i,(ax,ay) in enumerate(vertices):
        bx,by=vertices[(i+1)%len(vertices)]
        ex,ey=sub(bx,ax),sub(by,ay);px,py=sub(x,ax),sub(y,ay)
        t=clamp(div(add(mul(px,ex),mul(py,ey)),add(sq(ex),sq(ey))),0,1)
        candidates.append(add(sq(sub(px,mul(t,ex))),sq(sub(py,mul(t,ey)))))
    nearest=candidates[0]
    for candidate in candidates[1:]:nearest=op("min",nearest,candidate)
    distance=op("sqrt",nearest)
    return choose(inside,neg(distance),distance)
def canonical(u, v, orientation):
    m = op("floor", u)
    parity = sub(m, mul(2, op("floor", mul(0.5, m))))
    x = sub(u, m)
    vertical = choose(parity, neg(v), v)
    y = sub(vertical, op("floor", vertical))
    top = 0.9999999403953552
    return [choose(lt(x, 1), x, top), choose(lt(y, 1), y, top),
            sub(add(orientation, parity), mul(2, mul(orientation, parity)))]


class Bank:
    def __init__(self, old):
        self.functions = {}
        for name in ["placement_canonical", "placement_shifted", "disk", "disk_expanded", "nearest_klein_lift"]:
            self.functions[name] = deepcopy(old["functions"][name])
        self.families = {key: {"interface": 1000 + i, "methods": {}} for i, (key, _) in enumerate(CATALOGUE)}
        for name, base in [("hadamard_conjugate", "hadamard"), ("pinion_reverse", "pinion"), ("mutation_successor", "mutation")]:
            self.families[name] = {"interface": self.families[base]["interface"], "methods": {}}
        self.next_signature = 100

    def fn(self, name, inputs, outputs, meaning, requires=None, signature=None):
        if name in self.functions: raise ValueError(f"Duplicate function {name}")
        if signature is None:
            signature = self.next_signature
            self.next_signature += 1
        binding = {"inputs": list(inputs), "outputs": outputs,
                   "source": "Unified v0.2 source relationship; explicitly authored cycle_v0.1 numerical binding",
                   "meaning": meaning, "status": "Authored numerical law; execution evidence recorded separately."}
        if requires: binding["requires"] = requires
        self.functions[name] = {"signature": signature, "binding": binding}
        return name

    def method(self, family, role, name):
        self.families[family]["methods"][str(role)] = name

    def body(self, key, inputs, outputs, meaning, role=0, requires=None, signature=None, name=None):
        name = name or f"{key}_role{role}"
        self.fn(name, inputs, outputs, meaning, requires, signature)
        self.method(key, role, name)
        return name

    def handle(self, name): return list(self.functions).index(name)
    def family(self, name): return list(self.families).index(name)


def make_bank(old):
    b = Bank(old)
    d = V("field_distance")
    w = [V(name) for name in PAIR]
    # Exact chosen H diag(1,exp(+-i phi)) H, plus its log-polar overload.
    for family, sign in [("hadamard", 1), ("hadamard_conjugate", -1)]:
        direct = deepcopy(old["functions"]["hinge_forward" if sign == 1 else "hinge_conjugate"]["binding"])
        name = f"{family}_complex"
        b.functions[name] = {"signature": 1, "binding": direct}
        b.method(family, 0, name)
        rho0, theta0, rho1, theta1 = [V(k) for k in ["rho0", "theta0", "rho1", "theta1"]]
        z = [mul(op("exp", rho0), op("cos", theta0)), mul(op("exp", rho0), op("sin", theta0)),
             mul(op("exp", rho1), op("cos", theta1)), mul(op("exp", rho1), op("sin", theta1))]
        phase = mul(sign, add(V("phase"), add(mul(0.05, V("parity")), d)))
        h = math.sqrt(0.5)
        s = [mul(h, add(z[i], z[i+2])) for i in range(2)]
        t = [mul(h, sub(z[i], z[i+2])) for i in range(2)]
        rot = [sub(mul(op("cos", phase), t[0]), mul(op("sin", phase), t[1])),
               add(mul(op("sin", phase), t[0]), mul(op("cos", phase), t[1]))]
        out = [mul(h, add(s[i], rot[i])) for i in range(2)] + [mul(h, sub(s[i], rot[i])) for i in range(2)]
        b.body(family, ["rho0", "theta0", "rho1", "theta1", "phase", "parity", "field_distance"],
               dict(zip(PAIR, out)), "Decode the typed log-polar pair then execute exactly two Hadamards with a field/parity phase.",
               role=1, signature=11)
    # Old resident controllers. These families select numerical programs, not native opcodes.
    for family, successor in [("mutation", False), ("mutation_successor", True)]:
        M, T = V("field_distance"), V("target_field")
        signal = add(add(sub(V("ai"), V("br")), mul(0.25, add(M, mul(0.5, T)))),
                     add(add(mul(0.125, V("mutator_control")), mul(0.0625, V("jitter"))),
                         mul(0.03125, sub(V("old_body"), b.family("hadamard")))))
        hf, hc = b.family("hadamard"), b.family("hadamard_conjugate")
        hinge = choose(lt(signal, 0), hf if successor else hc, hc if successor else hf)
        body = choose(eq(V("target_index"), 30), b.family("mutation_successor"),
                      choose(eq(V("target_index"), 1), hinge,
                             choose(eq(V("target_index"), 5), b.family("pinion_reverse" if successor else "pinion"), V("old_body"))))
        control = add(V("old_control"), add(mul(0.001, add(M, mul(0.5, T))), mul(0.002, V("ai"))))
        b.body(family, ["old_body", "target_index", "field_distance", *PAIR, "jitter", "old_control", "mutator_control", "target_field"],
               {"body_handle": body, "control": control}, "Old situated mutator selects compatible family handles, including its successor, using prior wave, target body and both old fields.",
               requires=[bit_guard(V("jitter"))], signature=2)
    for family, original in [("pinion", "pinion_forward"), ("pinion_reverse", "pinion_reverse")]:
        name = family + "_transport"
        b.functions[name] = deepcopy(old["functions"][original])
        b.method(family, 1, name)
    b.fn("rebind_field", ["old_field", "new_body", "new_u", "new_v", "old_radius", "surface_u", "surface_v"],
         {"field_handle": choose(eq(V("new_body"), b.family("hadamard_conjugate")), b.handle("disk_expanded"), V("old_field")),
          "radius": clamp(add(V("old_radius"), add(mul(0.001, eq(V("new_body"), b.family("hadamard_conjugate"))),
                          mul(0.001, add(sub(V("new_u"), V("surface_u")), sub(V("new_v"), V("surface_v")))))), 0.05, 0.30)},
         "Old field plus new body/anchor and old chart context; radius and expanded-disk selection are authored laws.", signature=7)
    b.fn("next_generation", ["generation"], {"generation": add(V("generation"), 1)}, "Exact bounded generation increment.", signature=8)
    # Common surface and actual logarithmic phase encoding.
    kvals = canonical(add(V("ku"), mul(0.002, add(sub(w[0], w[2]), d))),
                      add(V("kv"), mul(sub(1, mul(2, V("ko"))), mul(0.002, add(sub(w[1], w[3]), d)))), V("ko"))
    b.body("klein", ["ku", "kv", "ko", *PAIR, "field_distance"], dict(zip(["ku", "kv", "ko"], kvals)),
           "Recurrent intrinsic Klein chart and orientation, driven by current field and prior wave; not an ambient 3D surface.", requires=[bit_guard(V("ko"))])
    norms = [norm2(w[0],w[1]),norm2(w[2],w[3])]
    maxima=[op("max",abs_(w[0]),abs_(w[1])),op("max",abs_(w[2]),abs_(w[3]))]
    minima=[op("min",abs_(w[0]),abs_(w[1])),op("min",abs_(w[2]),abs_(w[3]))]
    lognorms=[add(op("log",maxima[i]),mul(.5,op("log",add(1,sq(div(minima[i],maxima[i])))))) for i in range(2)]
    b.body("phi", [*PAIR, "field_distance"],
           {"rho0": lognorms[0], "theta0": add(op("atan2", w[1], w[0]), mul(0.01, d)),
            "rho1": lognorms[1], "theta1": sub(op("atan2", w[3], w[2]), mul(0.01, d))},
           "Natural-log radius and radian angle; each complex amplitude must be nonzero. Field changes phase, not coordinate units.",
           requires=[lt(0, maxima[0]), lt(0, maxima[1])])
    polar = ["rho0", "theta0", "rho1", "theta1"]
    b.body("split", [*polar, "jitter", "field_distance"],
           {name: add(choose(V("jitter"), V(polar[(i+2)%4]), V(name)), mul((0.005 if i == 1 else -0.005) if i in (1,3) else 0, d)) for i, name in enumerate(polar)},
           "One-bit exchange of two typed log-polar channels with an explicit field phase; not integer bit shifting of floats.", requires=[bit_guard(V("jitter"))])
    split_integer=op("floor",abs_(sub(V("split_theta0"),V("split_theta1"))))
    split_bit=sub(split_integer,mul(2,op("floor",mul(.5,split_integer))))
    mixed=sub(add(split_bit,V("jitter")),mul(2,mul(split_bit,V("jitter"))))
    parity = sub(add(mixed, V("neck")), mul(2, mul(mixed, V("neck"))))
    b.body("parity", ["split_theta0","split_theta1","jitter", "neck", "field_distance"], {"parity": parity, "phase": mul(0.01, d)},
           "Declared parity from the current split-phase difference's integer parity XOR jitter XOR neck, plus a separate field phase.", requires=[bit_guard(V("jitter")), bit_guard(V("neck"))])
    idx = 0
    for k in range(4):
        bit = sub(add(V(f"b{k}"), V("neck")), mul(2, mul(V(f"b{k}"), V("neck"))))
        idx = choose(lt(k, V("depth")), add(mul(2, idx), add(1, bit)), idx)
    b.body("bst", ["depth", "b0", "b1", "b2", "b3", "neck", "field_distance"],
           {"index": idx, "routing_phase": mul(0.01, d)}, "Implicit child=2*i+1+bit traversal with explicit neck reversal. No modulo or missing-address alias.",
           requires=[eq(V("depth"), op("floor", V("depth"))), sub(1, lt(V("depth"), 0)), sub(1, lt(4, V("depth"))), *[bit_guard(V(k)) for k in ["b0", "b1", "b2", "b3", "neck"]]])
    # Dependent RK stages; Y-up is a deliberately non-cancelling k4 event.
    omega = add(0.2, mul(0.01, d))
    deriv = [sub(mul(-1, mul(omega, w[1])), mul(0.02, w[0])), sub(mul(omega, w[0]), mul(0.02, w[1])),
             sub(mul(-1, mul(omega, w[3])), mul(0.02, w[2])), sub(mul(omega, w[2]), mul(0.02, w[3]))]
    heff = div(V("dt"), add(1, mul(0.001, abs_(d))))
    b.body("rk4", [*PAIR, "dt", "field_distance"], {**dict(zip(PAIR, deriv)), "h": heff},
           "Linear complex rotation/damping derivative and field-dependent positive interval; role1 is derivative evaluation.", role=1, requires=[lt(0,V("dt"))])
    kin = [f"k{s}_{i}" for s in range(1,5) for i in range(4)]
    combined = [add(w[i], mul(div(heff,6), add(add(V(f"k1_{i}"), mul(2,V(f"k2_{i}"))), add(mul(2,V(f"k3_{i}")),V(f"k4_{i}"))))) for i in range(4)]
    b.body("rk4", [*PAIR,"dt",*kin,"field_distance"], dict(zip(PAIR,combined)),
           "RK4-weighted combination of genuinely dependent slopes. Two authored Y-up events modify k4; fourth-order accuracy is not claimed with events.", role=2)
    b.fn("rk_stage", [*PAIR,*[f"k{i}" for i in range(4)],"h","fraction"],
         {PAIR[i]:add(w[i],mul(mul(V("h"),V("fraction")),V(f"k{i}"))) for i in range(4)}, "Explicit RK intermediate-state algebra.")
    eta=add(0.02,mul(0.001,d))
    b.body("y_up",[*PAIR,"field_distance"],{"ar":w[0],"ai":add(w[1],mul(eta,w[0])),"br":w[2],"bi":add(w[3],mul(eta,w[2]))},
           "Non-cancelling vertical shear applied twice to k4 only: ai+=eta*ar, bi+=eta*br, eta=.02+.001*field.")
    # The six named geometric bodies, with exactness labels preserved.
    x,y,z=w[:3]; radius=add(0.5,mul(0.01,d))
    shoulder=sub(radius,.12);top=add(radius,.12)
    t_vertices=[(-.12,neg(radius)),(.12,neg(radius)),(.12,shoulder),(radius,shoulder),
                (radius,top),(neg(radius),top),(neg(radius),shoulder),(-.12,shoulder)]
    t_inside=op("max",mul(le(abs_(x),.12),mul(le(neg(radius),y),le(y,shoulder))),
                mul(le(abs_(x),radius),mul(le(shoulder,y),le(y,top))))
    triangle_inside=mul(le(0,z),mul(le(z,radius),le(abs_(x),sub(radius,z))))
    rho=norm2(x,y)
    cone_t=clamp(div(add(mul(sub(rho,radius),neg(radius)),mul(z,radius)),mul(2,sq(radius))),0,1)
    cone_side=add(sq(sub(rho,mul(radius,sub(1,cone_t)))),sq(sub(z,mul(radius,cone_t))))
    cone_base=add(sq(op("max",sub(rho,radius),0)),sq(z))
    cone_distance=op("sqrt",op("min",cone_base,cone_side))
    cone_inside=mul(le(0,z),mul(le(z,radius),le(rho,sub(radius,z))))
    shapes={
        "T_shape":polygon_distance(x,y,t_vertices,t_inside),
        "pyramid":polygon_distance(x,z,[(neg(radius),0),(radius,0),(0,radius)],triangle_inside),
        "circle":sub(norm2(x,y),radius),
        "cone":choose(cone_inside,neg(cone_distance),cone_distance),
        "sphere":sub(op("sqrt",add(add(sq(x),sq(y)),sq(z))),radius),
        "apex":op("sqrt",add(add(sq(sub(x,mul(0.01,d))),sq(y)),sq(z))),
    }
    for i,(key,shape) in enumerate(shapes.items()):
        kind="unsigned point distance" if key=="apex" else "exact Euclidean signed distance in the declared2D/3D coordinates"
        b.body(key,[*PAIR,"field_distance"],{"value":shape},f"{key}: {kind}; field controls radius or apex center.")
        scale=mul(0.01,op("sin",add(shape,V("routing_phase"))))
        b.body(key,[*PAIR,"routing_phase","field_distance"],{name:add(w[j],mul(scale,[1,-1,0.5,-0.5][(j+i)%4])) for j,name in enumerate(PAIR)},
               f"Typed selected-action adapter for {key}; its primitive value controls a bounded wave displacement.",role=99,signature=90)
    angular_difference=sub(V("phase"),V("previous"))
    unwrapped=add(V("previous"),op("atan2",op("sin",angular_difference),op("cos",angular_difference)))
    b.body("delta_phi",["phase","previous","previous2","jitter","dt","field_distance"],
           {"delta":add(sub(add(unwrapped,V("previous2")),mul(2,V("previous"))),add(mul(0.001,mul(V("dt"),V("jitter"))),mul(0.001,d))),"unwrapped":unwrapped},
           "Unwrap the actual PHI-encoded angle against prior encoded history, then second difference plus declared interval/jitter/field terms.")
    geom=[f"g{i}" for i in range(6)];geo=sum_([V(x) for x in geom])
    angle=add(mul(2.39996322972865332,V("delta")),add(mul(0.05,geo),mul(0.01,d)))
    growth=[mul(0.1,op("cos",angle)),mul(0.1,op("sin",angle)),mul(0.1,op("cos",add(angle,1.5707963267948966))),mul(0.1,op("sin",add(angle,1.5707963267948966)))]
    b.body("phyllotaxis",["delta",*geom,"field_distance"],dict(zip(PAIR,growth)),"Golden-angle phase-driven candidate pair, coupled to all six current geometric values; no uniform-sampling claim.")
    g=[V(f"g{i}") for i in range(4)]
    score=add(dot(w,g),mul(0.001,mul(d,dot(w,w))))
    b.body("double_dot",[*PAIR,*[f"g{i}" for i in range(4)],"field_distance"],{**dict(zip(PAIR,w)),"score":score},
           "Frobenius contraction of two real2x2 amplitude arrays plus declared field term; CoupledWave retains its original pair.")
    weight=div(1,add(2,abs_(add(V("score"),add(mul(0.01,geo),mul(0.01,d))))))
    b.body("blend",[*PAIR,"score",*[f"growth{i}" for i in range(4)],*geom,"field_distance"],
           {name:add(mul(sub(1,weight),w[i]),mul(weight,V(f"growth{i}"))) for i,name in enumerate(PAIR)},
           "Bounded convex blend driven by contraction, all primitive values and current field.")
    theta=mul(0.05,d);cs=op("cos",theta);sn=op("sin",theta)
    crystal=[sub(mul(cs,w[0]),mul(sn,w[2])),sub(mul(cs,w[1]),mul(sn,w[3])),add(mul(sn,w[0]),mul(cs,w[2])),add(mul(sn,w[1]),mul(cs,w[3]))]
    b.body("crystal",[*PAIR,"field_distance"],dict(zip(PAIR,crystal)),"Field-dependent orthogonal bifurcation of the two complex streams.")
    swapped=[choose(V("parity"),w[(i+2)%4],w[i]) for i in range(4)]
    b.body("dichromatic",[*PAIR,"parity","field_distance"],{name:add(swapped[i],mul(mul(0.001,d),[1,-1,-1,1][i])) for i,name in enumerate(PAIR)},
           "R and G remain complex streams (four reals); parity exchanges them and field contributes a declared small signed offset.",requires=[bit_guard(V("parity"))])
    bnames=[f"B{i}" for i in range(4)]
    b.body("phase_history",[*bnames,"jitter",*kin,"field_distance"],
           {bnames[i]:add(mul(0.875,V(bnames[i])),add(mul(0.125,div(add(add(V(f"k1_{i}"),mul(2,V(f"k2_{i}"))),add(mul(2,V(f"k3_{i}")),V(f"k4_{i}"))),6)),add(mul(0.001,V("jitter")),mul(0.001,d)))) for i in range(4)},
           "Finite four-component exponentially weighted history of all four slopes, including changed k4; history feeds return and the next mutation.")
    matrix=["t00","t01","t10","t11"]
    diagonal=[add(1,add(mul(0.1,norms[i]),mul(0.01,abs_(d)))) for i in range(2)]
    off=mul(0.02,op("sin",V("crystal_ar")))
    b.body("T_transform",[*PAIR,"crystal_ar","field_distance"],dict(zip(matrix,[diagonal[0],off,off,diagonal[1]])),
           "Explicit symmetric positive-definite2x2 transformation; diagonals>=1, absolute off-diagonal<=.02.")
    aa,bb,cc,dd=[V(k) for k in matrix];det=sub(mul(aa,dd),mul(bb,cc));schur=sub(dd,div(mul(cc,bb),aa))
    adj=[div(dd,det),div(neg(bb),det),div(neg(cc),det),div(aa,det)]
    gauss=[add(div(1,aa),div(mul(bb,cc),mul(sq(aa),schur))),div(neg(bb),mul(aa,schur)),div(neg(cc),mul(aa,schur)),div(1,schur)]
    b.body("inverse_T",[*matrix,"field_distance"],{f"a{i//2}{i%2}":choose(lt(d,0),adj[i],gauss[i]) for i in range(4)},
           "Actual2x2 inverse. Field selects adjugate or Schur evaluation, mathematically the same inverse; eager branches require positive pivot/determinant.",
           requires=[lt(0.000001,aa),lt(0.000001,det),lt(0.000001,schur)])
    # Full typed RGBA has Rcomplex2,Gcomplex2,Bhistory4,Ainverse4: twelve scalars.
    rgba=["Rr","Ri","Gr","Gi",*bnames,"a00","a01","a10","a11"]
    r=[V(k) for k in rgba]
    lifted=[add(mul(r[8],r[0]),mul(r[9],r[2])),add(mul(r[8],r[1]),mul(r[9],r[3])),
            add(mul(r[10],r[0]),mul(r[11],r[2])),add(mul(r[10],r[1]),mul(r[11],r[3]))]
    for family,sign in [("pinion",1),("pinion_reverse",-1)]:
        out=[add(lifted[i],add(mul(0.02,r[4+i]),mul(sign*0.001,d))) for i in range(4)]
        chart=canonical(add(V("ku"),mul(sign*0.002,sub(out[0],out[2]))),
                        add(V("kv"),mul(sub(1,mul(2,V("ko"))),mul(sign*0.002,sub(out[1],out[3])))),V("ko"))
        b.body(family,["ku","kv","ko",*rgba,"field_distance"],{**dict(zip(PAIR,out)),**dict(zip(["u","v","orientation"],chart))},
               "Current pinion return overload consumes both complex streams, all finite history values and all four inverse-matrix entries.",role=0,signature=12)
    outpair=[choose(V("neck"),w[(i+2)%4],w[i]) for i in range(4)]
    theta=mul(0.01,add(d,V("parity")));c=op("cos",theta);s=op("sin",theta)
    finalpair=[sub(mul(c,outpair[0]),mul(s,outpair[1])),add(mul(s,outpair[0]),mul(c,outpair[1])),sub(mul(c,outpair[2]),mul(s,outpair[3])),add(mul(s,outpair[2]),mul(c,outpair[3]))]
    chart=canonical(V("u"),choose(V("neck"),neg(V("v")),V("v")),
                    sub(add(V("orientation"),V("neck")),mul(2,mul(V("orientation"),V("neck")))))
    b.body("return",[*PAIR,"u","v","orientation","neck","parity","phase","dt","field_distance"],
           {**dict(zip(PAIR,finalpair)),**dict(zip(["u","v","orientation"],chart)),"phase":add(V("phase"),mul(V("dt"),mul(0.01,d)))},
           "Nonorientable current-record return with explicit neck reversal, phase rotation and interval-dependent phase feedback.",requires=[bit_guard(V("neck")),bit_guard(V("parity"))])
    # Optional/initial catalogue roles are not silently counted as cycle stages.
    b.body("wavefront",polar+["field_distance"],dict(zip(PAIR,[mul(op("exp",V("rho0")),op("cos",add(V("theta0"),mul(.01,d)))),mul(op("exp",V("rho0")),op("sin",add(V("theta0"),mul(.01,d)))),mul(op("exp",V("rho1")),op("cos",sub(V("theta1"),mul(.01,d)))),mul(op("exp",V("rho1")),op("sin",sub(V("theta1"),mul(.01,d))))])),"Explicit log-polar source-wavefront decoding overload; initialization retains supplied finite wave samples.")
    b.body("jitter",["jitter","field_distance"],{"bit":V("jitter"),"phase":mul(d,sub(mul(2,V("jitter")),1))},"Supplied guarded bit with separate field-weighted control; no invented random generator.",requires=[bit_guard(V("jitter"))])
    b.body("psi",["dt","field_distance"],{"dt":div(V("dt"),add(1,mul(.001,abs_(d))))},"Positive numerical interval with declared field modulation; no physical-time calibration.",requires=[lt(0,V("dt"))])
    b.body("bayer",["value","threshold","field_distance"],{"bit":sub(1,lt(V("value"),add(V("threshold"),mul(.001,d))))},"Optional supplied-threshold scalar readout, not an implemented Bayer texture layout; not called by the cycle.")
    b.body("bc5",["field_distance"],{"unsupported":0},"BC5 device encoding is explicitly unsupported in this numerical cycle edition; invocation fails rather than pretending to pack.",requires=[0])
    return b


class Plan:
    def __init__(self, bank):
        self.bank = bank
        self.words = []
        self.calls = []

    def emit(self, opcode, *args):
        if len(args) > 7: raise ValueError("Plan instruction exceeds eight words")
        self.words.append([opcode, *args, *([0] * (7-len(args)))])

    def copy(self, dst, src, width=1): self.emit(10,dst,src,width)
    def const(self, dst, value): self.emit(0,dst,ir.fp32(value,"plan constant")[1])
    def args(self, args):
        for i, register in enumerate(args): self.copy(200+i,register)
    def helper(self,name,args,out):
        expected=len(self.bank.functions[name]["binding"]["inputs"])
        if len(args)!=expected: raise ValueError(f"{name}: wrong plan input width {len(args)} != {expected}")
        self.args(args)
        self.calls.append({"step":len(self.words),"helper":name,"inputs":list(args),"output_base":out})
        self.emit(3,self.bank.handle(name),200,out)
    def record(self, ordinal, slot, bank, signature, role, args, out, dynamic=False):
        self.args(args)
        self.calls.append({"step":len(self.words),"record":ordinal,"dynamic_source_index":dynamic,
                           "slot":slot,"bank":bank,"signature":signature,"role":role,"inputs":list(args),"output_base":out})
        self.emit(11 if dynamic else 4,ordinal,slot,bank,200,out,signature,role)
    def read(self,dst,ordinal,word,width,bank=0,dynamic=False):
        if dynamic:self.emit(12,dst,ordinal,word,width,bank)
        else:self.emit(2,dst,ordinal,word,width,bank)

    def situated(self,key,role,context,out,dynamic=False):
        ordinal=80 if dynamic else INDEX[key]
        self.read(216,ordinal,4,3,1,dynamic)
        self.record(ordinal,2,1,5,0,[216,217,218],219,dynamic)
        self.helper("nearest_klein_lift",[0,1,219,220,221],223)
        self.read(227,ordinal,7,1,1,dynamic)
        self.record(ordinal,1,1,4,0,[223,224,227],228,dynamic)
        self.copy(239,228)
        if dynamic:
            function=self.bank.functions[self.bank.families["circle"]["methods"]["99"]]
        else:
            function=self.bank.functions[self.bank.families[key]["methods"][str(role)]]
        args=[239 if name=="field_distance" else context[name] for name in function["binding"]["inputs"]]
        self.record(ordinal,0,1,function["signature"],role,args,out,dynamic)


def mutation_plan(b):
    p=Plan(b)
    p.emit(1,0,0,len(STATE))
    p.read(64,TARGET,0,24)
    p.read(88,INDEX["mutation"],0,24)
    p.read(112,INDEX["pinion"],0,24)
    p.copy(140,64,24)
    p.emit(9,195)
    p.record(TARGET,2,0,5,0,[68,69,70],164)
    p.record(INDEX["mutation"],2,0,5,0,[92,93,94],167)
    p.record(INDEX["pinion"],2,0,5,0,[116,117,118],170)
    p.helper("nearest_klein_lift",[164,165,167,168,169],177)
    p.record(INDEX["mutation"],1,0,4,0,[177,178,95],183)
    p.record(TARGET,1,0,4,0,[177,178,71],184)
    p.record(INDEX["mutation"],0,0,2,0,[64,195,183,3,4,5,6,9,76,100,184],186)
    p.helper("nearest_klein_lift",[164,165,170,171,172],177)
    p.record(INDEX["pinion"],1,0,4,0,[177,178,119],185)
    p.record(INDEX["pinion"],0,0,3,1,[164,165,166,3,4,5,6,185,8,77,78,14,15,66,9],188)
    p.helper("rebind_field",[65,186,188,189,71,14,15],192)
    p.helper("next_generation",[67],194)
    for dst,src,width in [(140,186,1),(141,192,1),(142,191,1),(143,194,1),(144,188,3),
                          (147,193,1),(152,187,1),(156,183,1),(157,64,1),(158,185,1)]:p.copy(dst,src,width)
    p.emit(5,0,140,24)
    return p


def action_plan(b,cycle):
    p=Plan(b)
    b.fn("sum_phases",["a","b"],{"phase":add(V("a"),V("b"))},"Named scalar phase adapter.")
    b.fn("wave_energy",PAIR,{"energy":dot([V(x) for x in PAIR],[V(x) for x in PAIR])},"Squared norm of the returned pair.")
    p.emit(1,0,0,len(STATE));p.copy(64,3,4);p.copy(68,14,2);p.copy(70,22)
    p.copy(81,8);p.copy(174,7);p.const(175,0.5);p.const(176,1)
    stages=[]
    def pair(base):return {name:base+i for i,name in enumerate(PAIR)}
    def slots():return {f"k{s}_{i}":84+4*(s-1)+i for s in range(1,5) for i in range(4)}
    available=set()
    for phase in cycle["phases"]:
        stage_start=len(p.words)
        required=set(PHASES[:PHASES.index(phase)])
        if not required<=available:raise ValueError(f"Cycle phase {phase} precedes required dependencies {sorted(required-available)}")
        if phase=="operator_mutation":
            p.situated("klein",0,{"ku":68,"kv":69,"ko":70,**pair(64)},68)
            p.situated("psi",0,{"dt":8},81)
        elif phase=="log_polar":
            p.situated("phi",0,pair(64),71)
        elif phase=="split_and_hinge":
            p.situated("split",0,{**dict(zip(["rho0","theta0","rho1","theta1"],range(71,75))),"jitter":9},75)
            p.situated("parity",0,{"split_theta0":76,"split_theta1":78,"jitter":9,"neck":16},79)
            # Parity output phase shares register80 temporarily; selected index
            # is not yet defined. Preserve its contribution before routing.
            p.helper("sum_phases",[7,80],174)
            p.situated("hadamard",1,{**dict(zip(["rho0","theta0","rho1","theta1"],range(75,79))),"phase":174,"parity":79},64)
        elif phase=="selected_operator":
            p.situated("bst",0,{"depth":17,"b0":18,"b1":19,"b2":20,"b3":21,"neck":16},80)
            p.copy(82,81) # second BST output; restore effective interval below
            p.situated("circle",99,{**pair(64),"routing_phase":82},64,dynamic=True)
            p.situated("psi",0,{"dt":8},81)
        elif phase=="rk4_four_slots":
            p.copy(108,64,4)
            p.situated("rk4",1,{**pair(108),"dt":81},84)
            p.copy(100,88)
            for derivative_base,previous,fraction in [(88,84,175),(92,88,175),(96,92,176)]:
                p.helper("rk_stage",[*range(108,112),*range(previous,previous+4),100,fraction],104)
                p.situated("rk4",1,{**pair(104),"dt":81},derivative_base)
            for _ in range(cycle["fourth_rk4_slot"]["y_up_applications"]):
                p.situated("y_up",0,pair(96),96)
            p.situated("rk4",2,{**pair(108),"dt":81,**slots()},64)
        elif phase=="geometry_divergence":
            for i,key in enumerate(["T_shape","pyramid","circle","cone","sphere","apex"]):p.situated(key,0,pair(64),112+i)
            p.situated("delta_phi",0,{"phase":72,"previous":27,"previous2":28,"jitter":9,"dt":81},118)
            p.situated("phyllotaxis",0,{"delta":118,**{f"g{i}":112+i for i in range(6)}},120)
            p.situated("double_dot",0,{**pair(64),**{f"g{i}":120+i for i in range(4)}},124)
            p.situated("blend",0,{**pair(124),"score":128,**{f"growth{i}":120+i for i in range(4)},**{f"g{i}":112+i for i in range(6)}},64)
        elif phase=="rgba_crystal":
            p.situated("crystal",0,pair(64),132)
            p.situated("dichromatic",0,{**pair(132),"parity":79},136)
            p.situated("phase_history",0,{**{f"B{i}":23+i for i in range(4)},"jitter":9,**slots()},140)
            p.situated("T_transform",0,{**pair(64),"crystal_ar":132},144)
            p.situated("inverse_T",0,dict(zip(["t00","t01","t10","t11"],range(144,148))),148)
        elif phase=="surface_return":
            rgba={**dict(zip(["Rr","Ri","Gr","Gi"],range(136,140))),**{f"B{i}":140+i for i in range(4)},
                  **dict(zip(["a00","a01","a10","a11"],range(148,152)))}
            p.situated("pinion",0,{"ku":68,"kv":69,"ko":70,**rgba},152)
            p.situated("return",0,{**pair(152),"u":156,"v":157,"orientation":158,"neck":16,"parity":79,"phase":7,"dt":81},160)
            p.copy(177,239)
            p.helper("wave_energy",list(range(160,164)),178)
            outputs={"u":164,"v":165,"orientation":166,**pair(160),"phase":167,"dt":8,"jitter":9,
                     **{f"previous_{name}":3+i for i,name in enumerate(PAIR)},"surface_u":68,"surface_v":69,
                     "neck":16,"route_depth":17,**{f"route_b{i}":18+i for i in range(4)},"K_orientation":70,
                     **{f"B{i}":140+i for i in range(4)},"phase_previous":119,"phase_previous2":27,
                     **dict(zip(["T00","T01","T10","T11"],range(144,148))),
                     **dict(zip(["A00","A01","A10","A11"],range(148,152))),
                     **dict(zip(["Rr","Ri","Gr","Gi"],range(136,140))),"selected_index":80,"last_field":177,"energy":178}
            for name in STATE:p.emit(6,SID[name],outputs[name],1)
        available.add(phase)
        stages.append({"phase":phase,"action_step_start":stage_start,"action_step_end_exclusive":len(p.words)})
    return p,stages


def validate_sources(model,cycle):
    if not isinstance(model,dict) or not isinstance(model.get("operators"),list) or len(model["operators"])!=31:
        raise ValueError("This authored edition requires exactly the original31-entry catalogue")
    for i,(key,symbol) in enumerate(CATALOGUE):
        entry=model["operators"][i]
        expected={"body":{"symbol":symbol},"field":{"symbol":symbol+"_SDF"},"placement":{"symbol":"Phyllotaxis_on_Klein"}}
        if entry.get("index")!=i or entry.get("key")!=key:
            raise ValueError(f"Source record {i} has an unbound index/key change")
        for slot,value in expected.items():
            if entry.get(slot)!=value:raise ValueError(f"Unbound changed source declaration: {key}.{slot}")
        if "parameters" in entry:raise ValueError(f"Source numerical parameters for {key} need an explicit edition binding")
    if model.get("symbols",{}).get("T_inverse_role")!="transformation":
        raise ValueError("This edition binds T as an actual2x2 transformation, not temperature or another role")
    seed=model.get("seed",{}).get("wavefront")
    if not isinstance(seed,list) or len(seed)!=4:raise ValueError("Source seed.wavefront must contain exactly four finite real components")
    packed=[ir.fp32(value,"source seed.wavefront")[0] for value in seed]
    if (packed[0]==0 and packed[1]==0) or (packed[2]==0 and packed[3]==0):raise ValueError("Each source complex seed must be nonzero for PHI")
    if not isinstance(cycle,dict) or not isinstance(cycle.get("phases"),list):raise ValueError("Cycle requires an explicit phase array")
    phases=cycle["phases"]
    if len(phases)!=8 or len(set(phases))!=8 or set(phases)!=set(PHASES):raise ValueError("Unknown, duplicate, missing or unexecutable source phase")
    fourth=cycle.get("fourth_rk4_slot",{})
    count=fourth.get("y_up_applications")
    if type(count)is not int or not 0<=count<=8:raise ValueError("Bounded Y-up count must be an integer in0..8")


def build_definition(model,cycle,instance_count=17):
    validate_sources(model,cycle)
    if type(instance_count)is not int or not 1<=instance_count<=1000000:raise ValueError("Instance count must be1..1000000")
    old,old_raw=ir.read_json(RESIDENT)
    b=make_bank(old)
    mutation=mutation_plan(b)
    action,stages=action_plan(b,cycle)
    records=[]
    for i,(key,_) in enumerate(CATALOGUE):
        angle=i*2.39996322972865332
        radius=.4*math.sqrt((i+.5)/31)
        values=[.5+radius*math.cos(angle),.5+radius*math.sin(angle),0,.18,1,0,0,.4,0,.001,.002,0,0,float(b.family(key)),0,0,0,0,0,0]
        records.append({"key":key,"body":key,"field":"disk","placement":"placement_canonical","generation":0,"values":values,
                        "source_slots":{slot:deepcopy(model["operators"][i][slot]) for slot in ["body","field","placement"]}})
    instances=[]
    for i in range(instance_count):
        state={name:0 for name in STATE}
        seed=model["seed"]["wavefront"]
        state.update(u=(i%17)/17,v=.125+((i//17)%8)/16,orientation=0,ar=seed[0],ai=seed[1],br=seed[2],bi=seed[3],
                     phase=.125,dt=.125,jitter=i%2,surface_u=.5,surface_v=.5,neck=0,route_depth=3,
                     route_b0=0,route_b1=1,route_b2=0,route_b3=0,B0=.1,B1=-.05,B2=.075,B3=.025,
                     T00=1,T11=1,A00=1,A11=1)
        instances.append({"state":state})
    definition={
        "profile":PROFILE,"functions":b.functions,"families":b.families,"records":records,
        "record_value_names":old["record_value_names"],"state_names":STATE,
        "mutation_plan":mutation.words,"action_plan":action.words,"instances":instances,
        "source":{"model":"source_workbench/Dawnwood_Interactive_v0.2/model/substrate.json",
                  "cycle":"source_workbench/Dawnwood_Interactive_v0.2/model/cycle.json",
                  "model_semantic_sha256":ir.sha256(ir.json_bytes(model)),"cycle_semantic_sha256":ir.sha256(ir.json_bytes(cycle)),
                  "generator_sha256":ir.sha256(Path(__file__).read_bytes()),
                  "resident_binding_dependency":{"path":"source_bindings/resident_v0.1.json","sha256":ir.sha256(old_raw)},
                  "cycle_definition":cycle,"stage_boundaries":stages,"mutation_calls":mutation.calls,"action_calls":action.calls,
                  "source_slot_policy":"Hard-coded original declaration assertions; unknown source-slot edits fail rather than acquiring the old law automatically.",
                  "selected_route_role":99,"selected_route_source_indices":[7,8,9,10,11,12],
                  "typed_RGBA":"Rcomplex2 + Gcomplex2 + Bhistory4 + Ainverse2x2 =12 real scalars",
                  "optional_unlowered":["BC5 texture encoding","Bayer texture layout; only supplied-threshold overload is present"],
                  "rk4_binding":"Dependent k1,k2,k3,k4 with field-dependent interval; configured non-cancelling Y-up shear acts only on k4 before weighted combination. No fourth-order accuracy claim with events.",
                  "geometric_exactness":{"circle":"exact Euclidean circle SDF in(ar,ai)","sphere":"exact Euclidean sphere SDF in(ar,ai,br)","apex":"unsigned point distance","T_shape":"exact2D8-edge polygon SDF in(ar,ai)","pyramid":"exact2Dtriangular side SDF in(ar,br)","cone":"exact3Dcappedcone SDF in(ar,ai,br)"},
                  "seed_policy":"The actual model.seed.wavefront supplies all four initial amplitude components unchanged; carrier query coordinates vary per independent instance."},
        "meaning":"All eight source phases explicitly lowered to immutable expression-bank data and resident typed calls, with old-snapshot mutation, newly published records, typed12-scalarRGBA and whole-cycle component state return.31 records are present; selected-action role initially supports six primitive source indices. This is an authored numerical edition, not a unique recovered source equation or a domain application.",
        "status":"Generated executable numerical binding; independent CPU/GPU and mathematical evidence pending.",
    }
    return definition


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest="command",required=True)
    for name in ["generate","compile"]:
        command=commands.add_parser(name)
        command.add_argument("--model",type=Path,default=MODEL)
        command.add_argument("--cycle",type=Path,default=CYCLE)
        command.add_argument("--instances",type=int,default=17)
        command.add_argument("--output",type=Path,required=name=="compile",default=OUTPUT if name=="generate" else None)
    args=parser.parse_args(argv)
    model,model_raw=ir.read_json(args.model);cycle,cycle_raw=ir.read_json(args.cycle)
    definition=build_definition(model,cycle,args.instances)
    # The v2 frontend is the independent structural/binary compiler. The cycle
    # authoring layer does not manufacture native records without its checks.
    try:from . import source_resident_v2 as resident
    except ImportError:import source_resident_v2 as resident
    program,manifest=resident.compile_definition(model,definition)
    if args.command=="generate":
        args.output.write_bytes(ir.json_bytes(definition))
        print(json.dumps({"definition":str(args.output.resolve()),"profile":PROFILE,"functions":len(definition['functions']),"families":len(definition['families']),"records":len(definition['records']),"mutation_steps":len(definition['mutation_plan']),"action_steps":len(definition['action_plan']),"bytes":len(program)},indent=2))
        return 0
    output=args.output.resolve()
    manifest["source_cycle_lowered"]=True
    manifest["domain_application_implemented"]=False
    manifest["scope"]="authored_eight_stage_source_cycle_with_restricted_selected_role_and_optional_packing_unlowered"
    manifest["source_cycle"]={"path":str(args.cycle.resolve()),"sha256":ir.sha256(cycle_raw),"stage_boundaries":definition["source"]["stage_boundaries"],"definition":cycle}
    manifest["source_model"]={"path":str(args.model.resolve()),"sha256":ir.sha256(model_raw)}
    files={"source_model.json":model_raw,"source_cycle.json":cycle_raw,"definition.json":ir.json_bytes(definition),"program.bin":program,
           "source_cycle_generator.py":Path(__file__).read_bytes(),"resident_binding_dependency.json":RESIDENT.read_bytes()}
    manifest["files"]={name:{"bytes":len(data),"sha256":ir.sha256(data)} for name,data in files.items()}
    manifest_raw=ir.json_bytes(manifest)
    output.mkdir(parents=True,exist_ok=False)
    for name,data in files.items():(output/name).write_bytes(data)
    (output/"manifest.json").write_bytes(manifest_raw)
    print(json.dumps({"output":str(output),"profile":PROFILE,"program_sha256":ir.sha256(program),"bytes":len(program),"source_cycle_lowered":True,"domain_application_implemented":False},indent=2))
    return 0


if __name__=="__main__":
    try:raise SystemExit(main())
    except (OSError,ValueError,TypeError,KeyError,RecursionError) as error:
        print(f"{type(error).__name__}: {error}",file=sys.stderr)
        raise SystemExit(1)
