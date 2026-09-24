# Enzyme-pool conservation as an exact distance specialization

**Status:** biochemical grounding and mathematical specification, researched
24 September 2026. This document proposes a concrete domain binding for the
resident architecture; it does not claim that the binding has been implemented
or validated on the GPU. The metric, coordinate transform and projection below
are derived here. They are not equations attributed to the Dawnwood PDFs or
biochemical papers.

## The useful local task

Given user-specified total enzyme and substrate pools and a batch of candidate
concentrations, return the nearest nonnegative state that satisfies those two
pools, its correction distance, and the constraint reached. This provides a
precise consistency filter for synthetic assay candidates, proposed simulator
states, or candidate states emitted by another numerical model. It does not
predict reaction time, enzyme efficiency or disease response.

Two input forms must remain distinct:

| Input | Meaning | Main output |
|---|---|---|
| `(ES, P, E_T, S_T)` | Candidate already parameterized on a fixed conservation plane | Intrinsic signed distance, closest boundary witness, and nearest feasible state |
| `(E, S, ES, P, E_T, S_T)` | Candidate may also violate conservation | Plane residual, intrinsic margin of the orthogonal plane projection, and nearest feasible four-species state |

For an already feasible candidate, its nearest feasible state is itself;
its nearest boundary witness generally differs. An implementation must not
force a valid interior candidate onto the boundary.

## Biochemical basis and exact scope

Let `C = ES`. The closed, constant-volume reaction is

```text
E + S  <->  C  ->  E + P
        k1,k-1    kcat
```

For this mass-action scheme, the two conserved pools are `E+C=E_T` and
`S+C+P=S_T`. These are exact balances of the stated scheme; they do not require
a quasi-steady-state approximation. The reaction and both balances appear in
Shin, Chae, Lee and Kim's original research, equations 2–3.
[PLOS Computational Biology, 2024](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1012205).

Explicitly, with concentrations as variables,

```text
dE/dt = -k1*E*S + (k-1+kcat)*C
dS/dt = -k1*E*S + k-1*C
dC/dt =  k1*E*S - (k-1+kcat)*C
dP/dt =  kcat*C
```

Adding the first and third equations gives `d(E+C)/dt=0`; adding the second,
third and fourth gives `d(S+C+P)/dt=0`. Totals include initially bound enzyme
and any initial product: `E_T=E(0)+C(0)` and `S_T=S(0)+C(0)+P(0)`.

Closed means no substrate feed, product removal, enzyme synthesis/degradation,
or other reactions affecting these pools. Enzyme turnover changes the first
balance; the distinction is explicit in Gabrielsson and Peletier's original
research, equations 1–3. Their broader model also includes substrate infusion;
all such source terms must be zero for the specialization here.
[The AAPS Journal, 2018](https://link.springer.com/article/10.1208/s12248-018-0256-z).

For this first profile, require `0 < E_T < S_T`, with finite concentrations in
one shared unit. This strict ordering gives the nondegenerate quadrilateral
used below. The balances themselves do not require that ordering; other pool
ratios need their own polygon construction or a more general solver.
Raw observations may be negative: reconciling a finite but inconsistent
candidate is the task. Nonnegativity constrains the returned scientific state,
not the observations supplied to the distance/projection calculation.

## Four-species geometry and the correct metric

Use species order `q=(E,S,C,P)` and free coordinates `z=(c,p)=(C,P)`:

```text
q(z) = b + B*z = (E_T-c, S_T-c-p, c, p)

b = (E_T, S_T, 0, 0)

     [-1  0]
B =  [-1 -1]
     [ 1  0]
     [ 0  1]
```

Nonnegativity is exactly the convex trapezoid

```text
Kz = { (c,p): 0 <= c <= E_T, 0 <= p, c+p <= S_T }
vertices, counterclockwise:
z0=(0,0), z1=(E_T,0), z2=(E_T,S_T-E_T), z3=(0,S_T).
```

Define distance as ordinary Euclidean distance across all four concentrations,
with equal species weights and the same concentration unit. This is a declared
error metric, not a biochemical free energy or a kinetic law. Then

```text
||q(z+dz)-q(z)||^2 = dz^T * G * dz

G = B^T*B = [3 1]       G^-1 = (1/5)*[ 2 -1]
            [1 2]                     [-1  3]

= 3*dc^2 + 2*dc*dp + 2*dp^2.
```

Therefore ordinary Euclidean distance in the untransformed `(C,P)` plot is
**not** four-species Euclidean distance. A coordinate transform that preserves
the intended distance exactly in real arithmetic is

```text
x = sqrt(5/2)*c
y = (c+2*p)/sqrt(2)

c = sqrt(2/5)*x
p = (sqrt(2)*y-c)/2.
```

Writing `X=T*z`, the identity `T^T*T=G` proves
`||X1-X2|| = ||q(z1)-q(z2)||`. The transformed vertices are

```text
v0 = (0, 0)
v1 = (sqrt(5/2)*E_T, E_T/sqrt(2))
v2 = (sqrt(5/2)*E_T, (2*S_T-E_T)/sqrt(2))
v3 = (0, sqrt(2)*S_T).
```

All coordinates and distances have concentration units. If numerical scaling
is needed, divide **every** species and both totals by the same positive
reference concentration `C_ref`, execute in those dimensionless coordinates,
then multiply reported concentrations/distances by `C_ref`. Scaling enzyme
and substrate separately changes the metric. A measurement-weighted metric is
possible, but requires an explicit positive-definite weight matrix and a newly
derived transform; it must not silently reuse this one.

## Exact signed distance and witnesses on the plane

For an arbitrary plane point `X`, enumerate the four closed edge segments
`[v_i,v_(i+1 mod 4)]`. For each edge,

```text
e_i = v_(i+1) - v_i
t_i = clamp(dot(X-v_i,e_i)/dot(e_i,e_i), 0, 1)
w_i = v_i + t_i*e_i
D_i = ||X-w_i||^2.
```

Choose the smallest `D_i` and its witness `w`. Use the smallest edge index on
exact ties for reproducible boundary reporting. The radius-free inside test
is simply `0<=c<=E_T`, `p>=0`, `c+p<=S_T`, after the inverse transform. Define

```text
d_plane(X) = -sqrt(min D_i)  if inside
             sqrt(min D_i)  if outside.
```

This is an exact signed distance to the feasible-region boundary **within the
conservation plane**, before floating-point rounding. It is negative in the
relative interior. It is zero on the boundary, with zero sign canonicalized
if needed for reporting. Corners and equidistant boundaries need not have a
unique gradient or boundary witness.

The closest feasible point is `X_feasible=X` when inside and `w` when outside.
Decode either witness with the inverse transform and `q(z)`. Edge labels, in
the order above, are `P=0`, `E=0`, `S=0`, `C=0`. The closed feasible set is
convex, so its nearest feasible point is unique; an interior point's nearest
boundary witness can have ties.

For interior points an independent simplification is

```text
d_plane = -min(sqrt(5/2)*C, sqrt(5/2)*E,
               sqrt(5/3)*P, sqrt(5/3)*S).
```

Outside, taking the maximum of normalized inequality residuals is generally
not exact near a corner. The segment calculation is still required. For
example `(c,p)=(-1,-1)` has distance `sqrt(7)` to `(0,0)` in the four-species
metric, while the largest violated supporting-line distance is only
`sqrt(5/2)`.

## Candidates outside the conservation plane

The feasible set has dimension two inside four-dimensional concentration
space. It has no four-dimensional interior, so this intrinsic signed distance
must not be advertised as a signed distance to an ordinary solid in R4.

For an arbitrary raw candidate `q`, first compute the orthogonal projection
onto the affine conservation plane. Let

```text
A = [1 0 1 0],    totals = (E_T,S_T)
    [0 1 1 1]

r = A*q - totals = (r_E,r_S)
alpha = (3*r_E-r_S)/5
beta  = (-r_E+2*r_S)/5

q_plane = (E-alpha, S-beta, C-alpha-beta, P-beta)
normal_distance^2 = (3*r_E^2 - 2*r_E*r_S + 2*r_S^2)/5.
```

Equivalently, the closed-form plane coordinates in the specified input order
`(E,S,C,P)` are

```text
c_hat = (2*E_T + S_T - 2*E - S + 2*C - P)/5
p_hat = (-E_T + 2*S_T + E - 2*S - C + 3*P)/5

q_plane = (E_T-c_hat, S_T-c_hat-p_hat, c_hat, p_hat).
```

These formulas consume all four observations. Replacing `c_hat,p_hat` with
the observed C,P would silently discard E,S and solve a different problem.
If a common concentration normalization is used, normalize the observations
and totals before applying these formulas and consistently keep all subsequent
coordinates, objectives and error bounds in those normalized units.

Use `z_plane=(q_plane.C,q_plane.P)` in the transformed polygon algorithm.
Decode its closest feasible witness into `q_star`. Orthogonality gives

```text
distance_to_feasible_set^2
  = normal_distance^2 + max(d_plane(T*z_plane),0)^2
  = ||q-q_star||^2.
```

The first expression separates conservation error from nonnegativity error;
the second is an independent output check. Report the ambient distance as
**unsigned**, alongside the signed intrinsic margin. A negative intrinsic
margin after plane projection does not mean the original raw candidate
already obeyed conservation.

## Concrete example and output contract

In micromolar units, take `E_T=1`, `S_T=3`, and `(C,P)=(1.5,0.5)`.
The implied candidate is `q=(-0.5,1,1.5,0.5)`. The exact nearest feasible
state is

```text
(C_star,P_star) = (1,0.75)
q_star = (0,1.25,1,0.75)
distance = sqrt(0.625) = 0.7905694150420949 micromolar.
active boundary: E=0.
```

Clamping only C to 1 and leaving P at 0.5 gives a larger four-species correction
of `sqrt(0.75)`. This is a concrete reason to preserve the induced metric.
For the feasible point `(C,P)=(0.5,1)`, nearest-set distance is zero and the
intrinsic margin is `-sqrt(0.625)`; it must remain unchanged by repair.

An executable profile should return the original candidate, common unit and
scale, both totals, conserved-plane residuals, signed intrinsic margin,
unsigned repair distance, repaired four-species state, boundary witness and
edge/tie label, and the actual definition/checkpoint identity. Finite-input
guards and `0<E_T<S_T` must execute rather than remain documentation. Report
FP32 residuals and any boundary tolerance separately from the real-arithmetic
definition; never claim bitwise exact conservation after rounded subtraction.

## Resident-architecture integration and independent oracle

The domain field can be a resident executable expression with the distance
calculation above; its body can expose the nearest witness and a correction
proposal. A controller can change proposal policy using observed residuals,
while subsequent calls execute the selected resident definition. The same
domain field then participates in the calculation and validates its returned
state. Encoding this in the authored function bank is different from applying
a detached host-side filter after a run.

The two stoichiometric balances and chosen totals define the scientific task.
Changing them creates a different authored task. Mutable controllers or
alternative equivalent distance implementations must retain that distinction;
an arbitrary mutated scalar field is not automatically an exact enzyme-pool
SDF. This document establishes neither convergence of a controller nor a need
for iterative repair: the stated nearest-point problem already has the finite
closed construction above.

If the specialization deliberately exercises recurrent proposals, let
`X_hat=T*(c_hat,p_hat)` and use a feasible current point X. The variable part of
the least-squares objective and its gradient are

```text
f(X) = 0.5*||X-X_hat||^2
gradient f = X-X_hat

proposal = projection_K(X - eta*(X-X_hat)).
```

The omitted constant is `normal_distance^2/2`. In real arithmetic, `eta=1`
already returns the global nearest feasible point. For a fixed
`0<eta<2`, nonexpansiveness of convex projection yields contraction toward
that point by at most `abs(1-eta)`. A changing step with uniform bounds
`epsilon<=eta<=2-epsilon`, `epsilon>0`, likewise has a uniform contraction
bound. Merely placing each step in the open interval without a uniform bound
does not by itself give that geometric convergence guarantee. Any added source
phase perturbation or alternative proposal law requires its own analysis.
Finite iterates must not be labelled nearest just because objective values
decrease. These statements concern the declared projected-gradient law before
FP32 errors, not arbitrary resident mutation.

A useful independent gap estimate needs only the four polygon vertices:

```text
g(X) = max_i dot(X-X_hat, X-v_i), for feasible X
0 <= f(X)-f(X_star) <= g(X)
||X-X_star|| <= sqrt(2*g(X)).
```

The first inequality follows from convexity and the minimum of a linear
function over the polygon; the distance bound uses the quadratic's strong
convexity and constrained optimality. Thus this vertex calculation is an
independent optimality check that does not repeat the nearest-edge algorithm.
For the full **squared** four-species error, the objective-gap bound is `2*g`;
the four-species distance to the optimum remains bounded by `sqrt(2*g)`.
After normalization, multiply the distance bound by `C_ref` and objective-gap
bounds by `C_ref^2` to restore units. A value computed in FP32 is a numerical
gap estimate; a rigorous upper-bound certificate additionally needs a rounding
error bound and verified feasibility. Preserve any numerical violations
rather than clipping them into an apparent proof.

A separate numerical oracle should solve the four-species quadratic program
directly, without reusing the transformed polygon or recursively evaluating
its expression AST:

```text
minimize 0.5*||y-q||^2
subject to A*y=totals and y>=0.
```

Only four species are involved. Enumerate zero-species active sets, solve each
consistent equality-constrained projection, retain nonnegative candidates,
and select the minimum objective. Exact rational arithmetic is possible for
packed FP32 inputs, totals and these integer constraint coefficients; evaluate
the final square root at high precision. For a boundary-distance oracle,
use `q_plane` and require at least one zero species. Independently certify the nearest feasible
point by conservation, nonnegativity, and
`dot(q-q_star, vertex-q_star)<=0` for all four feasible vertices. Convexity
makes these vertex inequalities sufficient for global projection optimality.

Useful numerical checks include all edges and corners, strict interior points,
outside each edge and corner, unequal pool ratios, off-plane candidates,
common-unit rescaling, and exactly repeated projection. Compare against the
**packed** input values, retain source-input rounding separately, compare all
CPU/GPU checkpoint words, and retain failed guards. A benchmark must compare
equivalent projection tasks; it must not infer speedup from a larger unrelated
simulation.

The independent audit must also retain the actual FP32 transform constants
and measure `T_FP32^T*T_FP32-G` against the exact integer matrix above. Rounded
square roots do not produce an algebraically exact isometry. Compare signed
distances and returned witnesses with the exact four-species oracle rather
than silently defining the reference metric from the same rounded transform.
Input conversion, transform-coefficient error, expression-rounding error and
CPU/GPU backend disagreement are distinct quantities to report.

## Limits of the result

Conservation and nonnegativity do not specify a time course, a reaction rate,
a steady state, or kinetic reachability from a given initial condition. No
`k1`, `k-1`, `kcat` or time increment appears in this task. A kinetic extension
would additionally need its declared rates, initial conditions and integration
error analysis. In the irreversible scheme, product increases along a
physical trajectory; a static projection does not enforce that temporal
condition.

Fixed local pools do not model exchange between spatial locations. Diffusion
can invalidate pointwise pool conservation even when a closed domain has a
conserved total, as distinguished in the spatial research above, around
equations 9–10. [Shin et al., 2024](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1012205).
Additional complexes, inhibitors, transport, changing volume or enzyme
turnover require a different stoichiometric model. A repaired numerical
candidate is not evidence of assay validity, biological benefit, clinical
efficacy, quantum behavior, or general AI capability.
