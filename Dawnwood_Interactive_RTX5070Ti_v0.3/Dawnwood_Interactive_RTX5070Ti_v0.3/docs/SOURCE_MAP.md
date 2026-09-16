# Source-to-kernel correspondence

The page references below refer to the unchanged 24-page
`source/double-slit-theory.pdf`. The original user terminology is the naming
basis. The code's numerical parameters and representation choices are those of
`NATIVE_BINDING.md`.

| Source passage | Original pages | Native location |
|---|---:|---|
| Double slit / double pinion / Hadamard mitosis hinges | 3–5 | `core.hpp: evolve`, named seed bodies, twin complex Hadamard action |
| Log-encoded polar radius, phi, LUT | 3–4, 11 | `token_chart`, `chart_token`, `lut_entry`, 256-entry GPU LUT |
| Zero-order even/odd bit split and parity | 4–5 | `parity`, instruction packing, decision bit, word rotations |
| `[0,2,0,1]` wavefront FT vector | 6 | `seed_block`, `model/native_binding.json` |
| Two Y-up shifts at fourth RK4 slot | 7 | `rk4`, fourth derivative argument |
| T, pyramid side, circle, cone, sphere, apex, double-dot : | 8 | `support_sdf`, local primitives, `evolve` scalar contraction |
| Delta delta phi, Fibonacci phyllotaxis, blend | 8–9 | wrapped phase difference, golden-angle placement, blend instructions |
| RGBA crystal bifurcation and A inverse T | 9–12 | twin token result and exact B/A auxiliary record |
| SDF Klein bottle; no rasterization, raymarching, raytracing or square computational field | 12–14 | quotient coordinates, `fold`, `klein`, operator support fields; physical arrays only provide storage |
| Operators themselves move and change around the surface at Ψ | 14–16 | `mutate_op`, `mutate_operators`, live body words / support / location / references |
| Bare-metal cache aspiration and target RTX 5070 Ti laptop | 18 | native texture reads, shared working set, queried L2 policy |
| Chained packed VRAM texture pool, dichromatic BC5, no host hot-swap | 19–20 | `PageOwner`, `read_pair`, chain traversal, surface commit; optional explicit snapshot transfer |
| One-bit hierarchy and geometry-aware packing | 21 | implicit decision-tree walk and golden-step token ordering |
| Implicit array children `2i+1`, `2i+2` | 22 | `child`, `route`; no per-node child pointers |
| Universal Spatial State Automaton / source attribution | 22–23 | project title/author record and reusable packed-body interpreter |
| Optional Bayer downstream readout | 12–14 | retained catalogue label; no renderer is required or enabled by this kernel |

The source does not supply executable equations for all operators, a numerical
Klein SDF, a bit allocation, or a CUDA implementation. The prior v0.2 package
recorded those slots explicitly; that record is included here. This edition
fills them as one documented native recurrence rather than treating the
source's conversational descriptions as already-compiled machine instructions.

The numerical choices are not hidden in implementation defaults: LP8, chart
period, support primitives, pairwise phase-transform T, body-word arithmetic,
31-record catalogue, per-block B/A grouping, and update-window scheduling are
all specified in NATIVE_BINDING and the editable model files.

The attribution supplied for this edition is **Tom Klootwijk · NL200678942 ·
10-07-1990**, as requested in the current instruction. The unchanged source
retains its original spelling of the identifier in its earlier conversation.
