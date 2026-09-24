# Authored domain fields and their exact meaning

`local_lab/domain_fields.py` is a standard-library reference evaluator for explicit domain knowledge. It checks biochemical conservation, an acid/base activity window, kinetic consistency, resource envelopes and spatial clearance. These are executable formulas with units, coordinates, assumptions, provenance and individual boundary witnesses. The library reports `DW-Domain-0.1 CPU bindings`; it does not itself execute or modify the DWI-N1 GPU kernel. Any native domain-specialization profile must identify its own bindings and compare its output with this reference.

The source catalogue is `domain_knowledge/catalogue.json`; `domain_knowledge/examples/*.json` contains five editable definitions and illustrative defaults. Those defaults are authored scenarios, not measurements or constants for a named enzyme, buffer or physical device.

## Interface and reproducible use

```python
from local_lab.domain_fields import catalogue, evaluate

definitions = catalogue()
result = evaluate({
    "example": "enzyme_pool",
    "values": {"E": 8, "ES": 3, "S": 78, "P": 20},
    "parameters": {"E_total": 10, "S_total": 100,
                   "concentration_scale_uM": 1}
})
```

`catalogue()` expands the example identifiers into their full definitions. `evaluate(spec)` accepts an example identifier plus optional value/parameter overrides; omitted values retain that example's declared defaults. Unknown keys, nonnumeric/nonfinite values, invalid dimensions and invalid physical domains raise `ValueError`. Input magnitude is limited to `1e12`, vectors to 16 coordinates, and positive scales to at least `1e-12`. These implementation limits prevent pathological inputs; they do not define a physical validity range.

Run from the repository in PowerShell:

```powershell
$dwPython = 'C:\Users\ietsm\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $dwPython -B local_lab/domain_fields.py --catalogue
& $dwPython -B local_lab/domain_fields.py --example enzyme_pool --values '{"E":8,"ES":3,"S":78,"P":20}' --parameters '{"E_total":10,"S_total":100}' --output output/domain_pool_report.json
& $dwPython -B local_lab/domain_fields.py --example buffer_window --values '{"log10_base_activity":-2.5}'
& $dwPython -B local_lab/domain_fields.py --example enzyme_kinetics --values '{"rate_uM_per_s":0.7}'
```

For a custom analytic primitive, `--spec` reads a JSON **request** file, for example `{"primitive":{"type":"sphere","center":[0,0,0],"radius":2,"unit":"m"},"values":[3,0,0]}`. Catalogue example-definition files contain additional metadata and are not request files. Supported primitive types are `halfspace`, `hyperplane`, `slab`, `sphere` and `box`. The CLI returns zero for a successfully evaluated request even if `feasible` is false; malformed inputs return two. No network service or HTML interface is needed.

Each field reports its formula, metric, value, kind, unit, explicit constraint, tolerance, `inside`/`passes`, assumptions, source URLs and gradient where differentiable. `inside` means **the reported constraint passes**. For an equality hyperplane, that is `abs(value)<=tolerance`, not the entire negative halfspace. A null gradient marks a nondifferentiable point or an unavailable quantity. An individual boundary witness is not a solution to all constraints simultaneously.

## What is an exact SDF here?

For an oriented halfspace `a·x<=b`, orthogonal projection gives

`d=(a·x-b)/||a||`, with boundary witness `x-d*a/||a||`.

For the slab `low<=a·x<=high`, its signed distance is

`d=(|a·x-(low+high)/2|-(high-low)/2)/||a||`.

For a sphere, `d=||x-center||-radius`. For an axis-aligned box, define `q=abs(x-center)-half_extents`; then `d=||max(q,0)||+min(max(q),0)`. Outside the box, clamping gives the Euclidean nearest point. Inside, the nearest face determines the negative distance. These elementary geometric derivations supply the mathematical provenance; the formulas are not attributed to biochemical sources.

`exact_sdf` means that the analytic function is a Euclidean signed-distance formula **in the stated coordinates**. Python evaluates it with finite float64 arithmetic. It does not mean exact machine arithmetic, a complete scientific model, or an SDF under arbitrary coordinate changes. A zero-width slab is labelled `unsigned_distance`. The code checks intersections as separate constraints: it does not advertise `max(fields)` as a generally exact SDF of their intersection.

## Biochemical fields

**Closed enzyme and substrate pools.** For the explicit mechanism `E+S <=> ES -> E+P`, enzyme moiety conservation gives `E+ES=E_total`; a single substrate moiety gives `S+ES+P=S_total`. The mechanism is recorded by [IUPAC](https://goldbook.iupac.org/terms/view/M03893). These pool identities additionally assume fixed volume, no transport, synthesis or degradation, and no omitted bound forms. They are not the entire reaction's elemental or charge balance.

With `x=(E,ES,S,P)/c_ref`, the two oriented exact hyperplane distances are `(E+ES-E_total)/(c_ref*sqrt(2))` and `(ES+S+P-S_total)/(c_ref*sqrt(3))`. Nonnegative concentrations are exact halfspaces `-x_i<=0`. Choosing a concentration scale declares the metric; a different per-species scaling would require different transformed normals. Equality tolerance is expressed in that normalized distance.

For `E=8, ES=2, S=78, P=20`, totals 10 and 100, and `c_ref=1 uM`, both distances are zero. Changing only `ES` to 3 gives **0.7071067811865475** and **0.5773502691896258** in normalized concentration coordinates. The direct reference evaluation returned infeasible at tolerance `1e-9`. A nearest point on either hyperplane may violate the other pool or nonnegativity; it is a witness, not an automatic repair.

Species-level chemical bookkeeping must be distinguished from transformed biochemical equations with fixed pH and pooled protonation states. A buffered hydrogen-ion concentration must not be treated as an independently conserved closed pool. The distinction and the need for both representations are described in the [NIST thermodynamics recommendations](https://www.nist.gov/publications/recommendations-terminology-and-databases-biochemical-thermodynamics).

**Acid/base activity window.** Let `u=log10(a_acid)` and `v=log10(a_base)`. Under a declared single acid-dissociation equilibrium using compatible standard states, `pH=pKa+v-u`. A target interval therefore becomes a slab with normal `(-1,1)`; divide its pH residual margin by `sqrt(2)` to obtain distance in the `(u,v)` metric. Default `pKa=7` is illustrative. The mapping uses [Henderson-Hasselbalch](https://goldbook.iupac.org/terms/view/H02781), the [activity definition of pH](https://goldbook.iupac.org/terms/view/P04524) and an [acid dissociation constant](https://goldbook.iupac.org/terms/view/A00080). Concentration substitution requires its own activity approximation. This field does not solve electroneutrality, buffer capacity, changing ionic strength or a multi-acid mixture.

**Kinetic consistency is a residual.** The example evaluates `r=v/Vmax-S/(Km+S)` with positive `Km,Vmax` and nonnegative substrate. In coordinates `(S/Km,v/Vmax)`, its gradient is `(-1/(1+S/Km)^2,1)`, which is not generally unit length. It is explicitly labelled `residual`, with no nearest-distance witness. The supplied tolerance is an authored fraction of `Vmax`, not measured uncertainty. The initial-rate law, limiting-rate interpretation and kinetic scope come from [IUPAC Michaelis-Menten kinetics](https://goldbook.iupac.org/terms/view/M03892). A small residual does not identify a reaction mechanism; illustrative parameters do not become measured enzyme constants.

## Other fields and native integration boundary

The resource example checks a supplied count using `states*state_bytes*copies` plus explicit overhead/reserve, and checks supplied epoch time against a deadline. Its Euclidean axes are `(states/state_scale,epoch_ms/time_scale_ms)`. This is a continuous metric for a resource model, with integer counts required at input. It neither probes the GPU nor predicts execution time. Vulkan [budget estimates](https://docs.vulkan.org/refpages/latest/refpages/source/VkPhysicalDeviceMemoryBudgetPropertiesEXT.html) do not guarantee allocation; all overhead omitted from a supplied model remains omitted.

Spatial clearance uses the complementary SDF of a sphere inflated by clearance and a Euclidean rounded offset of an axis-aligned box. A negative field means sufficient clearance. Distances are metres; each witness concerns one obstacle. These are point-clearance calculations, not full trajectories or arbitrary rigid-body collision checks.

Direct reference runs evaluated all five default examples as feasible; the perturbed enzyme-pool example failed both conservation equalities as expected. Those observations validate these particular evaluations only. Native integration must preserve formulas, coordinate scales, immutable conservation constraints, permitted mutable parameters and profile identity, and record its own CPU/GPU evidence. A shader successfully reading a field does not by itself demonstrate the complete Dawnwood self-referential architecture or useful adaptive behavior.
