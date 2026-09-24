# Independent cycle-body mathematics, 24 September 2026

Seven component probes, totaling 3,384 lanes, executed the actual frozen
`cycle_v0.1` expression bodies through the resident-v2 CPU and Vulkan engines.
Every paired checkpoint was byte-identical. All lanes committed successfully.
The physical device was **NVIDIA GeForce RTX 5070 Ti Laptop GPU**; Vulkan
validation was enabled for every probe and recorded zero errors and warnings.

These are component diagnostics with explicit field-distance operands and
generation-only mutation. They do not run the full cycle's situated field and
placement calls or its mutation policy. The copied body ASTs were compared
structurally with the final `source_bindings/cycle_v0.1.json`; all matched.
`function_provenance.json` retains each function's identity and digest. The
actual source author file stayed unchanged during the experiment, with SHA256
`c0d3586844c5787784447f60944effa782d90868a5785399f114c245f4d8424c`.

| Probe | Lanes | Largest absolute error against independent reference |
|---|---:|---:|
| Six geometric bodies | 1,669 | `2.461286923161055e-7` |
| Inverse, both evaluation branches | 516 | `1.340238193758836e-7` |
| T generation followed by inverse | 257 | `1.265259622629245e-7` |
| Forward pinion return and Klein wrap | 212 | `1.184876681215030e-7` |
| Reverse pinion return and Klein wrap | 212 | `1.184876681215030e-7` |
| Dependent RK4, Y-up disabled for diagnostic | 259 | `1.291311226836456e-7` |
| Same RK4, two actual Y-up calls | 259 | `1.291311226836456e-7` |

The references use independent binary64 mathematics on the actual packed
FP32 inputs. They do not evaluate the source AST with another interpreter.
The existing repository threshold, `1e-5 + 2e-5*max(abs(actual),abs(reference))`,
was unchanged; every measured error was substantially below it. These finite
samples are neither an exhaustive error bound nor a physical validation.

## Geometric meaning and references

The six bodies share `r = 0.5 + 0.01*field_distance`; the apex instead shifts its
x coordinate by `0.01*field_distance`. The authored guards require positive r
for signed radial/triangle/cone primitives and r greater than 0.12 for the T.

- **T:** exact boundary distance to a two-dimensional eight-vertex T polygon
  in `(ar, ai)`. Stem half-width is 0.12, bottom is `-r`, shoulder is `r-0.12`,
  top is `r+0.12`, and bar half-width is r. The reference uses nearest segments
  and independent ray-crossing containment. It is not the minimum of two box
  fields, which would give incorrect interior boundary distances at overlaps.
- **Pyramid side:** signed distance to the two-dimensional triangular face in
  `(ar, br)` with vertices `(-r,0)`, `(r,0)`, `(0,r)`. The reference uses generic
  triangle edge distances and ray crossing. This is the specified side, not a
  three-dimensional closed pyramid solid.
- **Circle and sphere:** independent radial norm minus r in two and three
  coordinates respectively.
- **Capped cone:** signed distance to the three-dimensional rotational cone
  with base radius r at z=0 and apex at z=r. The independent reference compares
  closest points on the sloping surface and base disk; the rotation axis is
  not incorrectly treated as a boundary inside the cone.
- **Apex:** unsigned Euclidean distance to the shifted point.

The sample contains known surfaces, inside/outside points, polygon shoulders,
vertices and edges, a coordinate grid with varying radii, and deterministic
random points. At zero field, the origin returns circle/sphere `-0.5` and apex
`0`; `(0.5,0,0)` returns exact circle/sphere `0`. All per-output references and
errors, including boundary rounding, are retained. Selected known points are
listed in `geometry_known_fixtures.json`.

## Inverse, transport and RK checks

The inverse reference uses independent binary64 Gauss-Jordan elimination on
well-conditioned matrices, with both signs of the field selecting the authored
adjugate/Schur branches. The largest observed entry of `T*A-I`, computed from
the actual output inverse, was `1.509628404505747e-7`. For the actual generated
T family followed by inversion, it was `1.080924230123515e-7`. This checks
matrix inversion; it does not establish general error correction.

The forward and reverse pinion references independently apply the 2x2 inverse
to both real/imaginary streams, add all four history terms, then apply the
declared displacement and Klein quotient. Cases include negative, positive and
multiple u-seams, both input orientations, and v outside the chart. Every
returned coordinate was canonical and every orientation was a valid bit.

The RK diagnostic calls the actual derivative, intermediate-state helper and
combination bodies. With fixed field, the derivative is the complex linear law
`z' = lambda*z`, where `lambda = -0.02 + i*(0.2+0.01*field)`, and the effective
interval is `h = dt/(1+0.001*abs(field))`. The independent no-event result is

```text
z_next = z * (1 + lambda*h + (lambda*h)^2/2
              + (lambda*h)^3/6 + (lambda*h)^4/24)
```

All four dependent slopes were independently checked as well as the final
pair. The event-enabled probe invokes the actual Y-up body twice on k4 and
checks the analytically derived extra contribution
`h/6 * [0, 2*eta*k4_ar, 0, 2*eta*k4_br]`, with `eta=0.02+0.001*field`.
The first three slopes remained bit-identical between the two probes; k4 and
the final pair changed in **all 259 lanes**. The normal cycle retains its two
events; the disabled case is only a controlled diagnostic. No ordinary RK4
fourth-order accuracy claim is made for the event-modified scheme.

## Evidence

`summary.json` gives group results and device-validation status.
Each group retains its exact definition, source model, manifest, program,
CPU/Vulkan checkpoints, stdout/stderr, execution receipts, independent
reference outputs and audit JSON. `artifact_manifest.json` records sizes and
hashes. The experiment's temporary runner is
`tmp/run_cycle_math_probe.py`; no persistent test suite was added.

Executable SHA256:
`d6e08b44edf484571ad5d49954a8b3797c71e5bfc80ec4ce8cde795e8d865d29`.
Shader SHA256:
`9e90c89135a93a115db1ceaea5475338a389f8ab41ab7e64165751d4410f6098`.
