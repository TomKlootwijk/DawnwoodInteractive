# Dawnwood Interactive — Operator dictionary

Tom Klootwijk · NL200678942 · 10-07-1990 · +31655954068

All page references below refer to `source/double-slit-theory.pdf`. The initial implicit indices are the editable catalogue order of this edition.

| Index | Key | Source term | Role in the whole | Source pages |
|---:|---|---|---|---|
| 0 | `klein` | Self-referential Klein bottle SDF | Surface, return and the common field of data and operators. | 12-16 |
| 1 | `hadamard` | Hadamard mitosis hinges | Split the wavefront into the twin pinion streams. | 3-5, 13 |
| 2 | `phi` | Log-encoded polar radius PHI | Encode the radius/phase position used by the LUT. | 3-4, 11 |
| 3 | `rk4` | RK4 fourth timeslot | Gather the four kinematic slots into the next wavefront. | 7 |
| 4 | `phyllotaxis` | Fibonacci phyllotaxis | Arrange divergence and operator placement along the BST. | 8-9, 15, 21 |
| 5 | `pinion` | Double pinion | Drive the twin streams and hold operator flow to the Klein surface. | 3-5, 14-16 |
| 6 | `double_dot` | Pinion double dot : product operator | Couple the geometric and kinematic operator values. | 8 |
| 7 | `T_shape` | T geometry | The T primitive in the geometric LUT. | 8 |
| 8 | `pyramid` | Side view of the pyramid | The pyramid-side primitive in the geometric LUT. | 8 |
| 9 | `circle` | Circle | The circle primitive in the geometric LUT. | 8 |
| 10 | `cone` | Cone | The cone primitive in the geometric LUT. | 8 |
| 11 | `sphere` | Sphere | The sphere primitive in the geometric LUT. | 8 |
| 12 | `apex` | Apex | The apex associated with the double-dot pinion operator. | 8 |
| 13 | `delta_phi` | Lowercase delta delta phi | Phase divergence paired with the Fibonacci phyllotaxis blend. | 8-9 |
| 14 | `blend` | Math blend operator | Bring the branching geometric streams into the shared field. | 8-9 |
| 15 | `wavefront` | Wavefront FT vector | Carry the source vector [0, 2, 0, 1]. | 6 |
| 16 | `y_up` | Y up | Apply twice in the fourth RK4 timeslot. | 7 |
| 17 | `crystal` | Crystal bifurcation of RGBA values | Express the circulating wavefront through the RGBA state. | 9-11 |
| 18 | `inverse_T` | A means inverse T | Preserve the inverse-T role of A. | 9-12 |
| 19 | `T_transform` | T transformation | The transformation reading of T used by the later inverse loop. | 10-12 |
| 20 | `jitter` | 1bit jitter | Move and change the LUT operators at interval PSI. | 6, 14-16 |
| 21 | `bst` | 1bit BST | Route by the binary spatial/operator relationships. | 8-9, 13-15, 22 |
| 22 | `return` | Non-orientable return | Return output as input, carrying the path/parity reversal. | 13-17 |
| 23 | `phase_history` | B phase history | Carry the jitter and RK4 history in the texture state. | 11-12 |
| 24 | `dichromatic` | Dichromatic operators | Keep the two active pinion channels distinct within RGBA. | 11-12 |
| 25 | `bayer` | Optional Bayer matrix | Read out downstream from the already-circulating state. | 12-14 |
| 26 | `bc5` | BC5 packing | The named dichromatic packing route in the GPU design. | 19-22 |
| 27 | `split` | 0-order bit-shifted even/odd split | Express the twin paths in the source one-bit notation. | 4-5 |
| 28 | `parity` | 1-bit parity | Carry the source parity relationship at the split and return. | 4-5, 15 |
| 29 | `psi` | Interval PSI | Advance the operator-changing circulation. | 8-9, 14-16 |
| 30 | `mutation` | Operator self-mutation | Let previous state and one-bit jitter change the current operator field. | 14-16 |

Each live entry carries its body, SDF expression and surface-position expression. The full set is included in the recurrent state and in the operator-mutation step.

## Source record and editable expression

`model/substrate.json` preserves the source labels and page references. The `body` and `field` values are editable expressions. `model/bindings.json` keeps the open numerical binding positions together, and `model/cycle.json` supplies the written circulation used by the workbench.
