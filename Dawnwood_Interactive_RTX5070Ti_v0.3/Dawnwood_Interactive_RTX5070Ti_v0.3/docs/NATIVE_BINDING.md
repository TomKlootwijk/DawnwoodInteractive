# Dawnwood Interactive — the native recurrence

Tom Klootwijk · NL200678942 · 10-07-1990

This is the executable numerical binding of the source's unified substrate.
The names and circulation come from `source/double-slit-theory.pdf`. Numerical
choices below are this edition's definitions for the open binding positions
also recorded in `source/v0.2_open_bindings.json`.

## One state, one interval

Write the state at Ψ as `F = (P, O, B, A, clock, cursor)`. `P` is the dichromatic
packed field, `O` is its operator catalogue, and `B/A` is its exact auxiliary
state. No rendering stage participates in the recurrence.

For each interval:

1. Select a contiguous window of owned blocks from the GPU cursor. Follow
   data-directed texture-chain links to obtain neighbouring field values.
2. Evaluate the implicit SDF decision tree. Execute the selected operator's
   two referenced bodies and then its own body.
3. Apply the Hadamard double split, double-dot coupling, double-pinion drift,
   phase differential, RK4 action and the fourth-slot double Y-up event.
4. Encode the next R/G token pairs; update B and A; commit the window.
5. Use these results to mutate the operator bodies and references, SDF support,
   coefficients, surface locations and reversal parity. Advance the GPU clock.

All reads in the evaluation stage see the previous committed state. The commit
stage owns unique destination blocks. Operator banks alternate between Ψ
intervals; the entire texture field is not duplicated.

## The log-encoded polar LUT

Each R or G value is an 8-bit LP8 token. The high nibble chooses a log-radius
cell; the low nibble chooses a phase cell. High-nibble zero denotes exactly
zero amplitude; its 16 byte patterns share that meaning. The other 240 byte
patterns have the following reconstruction:

```text
h = token >> 4                         h = 1 ... 15
p = token & 15                         p = 0 ... 15
u = (h - 1/2) / 15
v = (p + 1/2) / 16
rho = -4 + 7.5 u                       log2 radius
z = 2^rho [ cos(2 pi v) + i sin(2 pi v) ]
```

The 256 reconstructed entries are precomputed and stored as `(Re z, Im z,u,v)`
in a 4096-byte texture-backed table. This retains two independent dichromatic
streams: R is the first pinion token, G the second. It does not reinterpret R
as a standalone radius while silently assigning G to the first stream's phase.

Encoding maps a nonzero complex value into this quotient chart and selects the
containing radial/phase cells. An exactly zero value produces token zero. This
is a finite, quantized log-polar representation; RG8 is exact for token bytes,
not for arbitrary real-valued amplitudes.

## Klein return and operator SDFs

The computational surface uses the identifications

```text
(u + 1, v) ~ (u, -v)
(u, v + 1) ~ (u, v)
```

`fold()` removes integral u windings, reverses v for odd winding, wraps v, and
returns the reversal bit. That bit contributes to routing/history. The radius
window is the chosen chart period, not a rejection radius or an opacity gate.

A coordinate realization is

```text
K(u,v) = ((2 + 0.5 cos(2 pi v)) cos(2 pi u),
          (2 + 0.5 cos(2 pi v)) sin(2 pi u),
           0.5 sin(2 pi v) cos(pi u),
           0.5 sin(2 pi v) sin(pi u)) .
```

This four-coordinate binding obeys `K(u+1,-v)=K(u,v)`. Tests exercise that seam
for positive and negative windings. Surface flow advances chart coordinates;
there is no raymarch, projection iteration, rasterizer or Cartesian simulation
lattice to keep the operators on the surface.

Every operator record also carries an SDF support. Circle, T, pyramid-side,
cone-meridian, sphere and apex supports are supplied. The triangle and box
primitives use signed distance; the T uses their union; the sphere is an
ambient four-coordinate radial field restricted to K; the apex has a point
zero set. These are the native support fields, rather than a fabricated global
three-dimensional signed distance to the complete Klein surface. Nearest
local deck images implement the non-orientable chart comparison.

Physical 4×4 BC5 blocks and 2D CUDA array dimensions describe **storage**.
They are not the geometry of the computational field.

## The packed operator body

An operator record occupies 64 bytes:

| Bytes | Field | Meaning |
|---|---|---|
| 0–3 | `location` | Two 16-bit chart coordinates |
| 4–7 | `support` | Radius word and SDF primitive selector |
| 8–11 | `links` | Two five-bit references into the same operator field |
| 12–15 | `coeff` | Kinematic coefficient words |
| 16–47 | `code[8]` | Eight executable instructions |
| 48–51 | `last_rg` | Previous field result and selection feedback |
| 52–55 | `history` | Operator history |
| 56–59 | `inverse_t` | Prior inverse transformation state |
| 60–63 | `route` | Return/routing parity |

The body interpreter has eight 16-bit registers. Each 32-bit instruction
contains a four-bit operation, three-bit destination and two three-bit operand
indices, three reserved bits, and a 16-bit immediate. Its primitives are MOV,
ADD, SUB, fractional MUL, XOR, AND, OR, 16-bit rotation, Hadamard sum/difference,
MIN, MAX, BLEND, IMM, ADDI and parity selection. Word overflow is modular
arithmetic. No instruction depends on unchecked memory addresses.

Reference value 31 is the root alias 0. The 31-record layout uses the prior
catalogue's order. For the implicit tree the children of i are `2i+1` and
`2i+2`; leaf traversal stops at indices 15–30. Here “1-bit BST” is implemented
as the source's binary operator-decision hierarchy, not a separate ordered-key
database index. No child pointer is stored per tree node.

A selected node's referenced body A, referenced body B, and own body execute
in that order. References may point back to the same node. The interpretation
is temporal feedback through the committed field; it does not recursively
expand a cyclic graph on a thread's call stack.

At Ψ, one jitter bit controls one instruction-word bit flip. Its location is
selected from the previous field/operator result. The changed bit can alter
an operation, operand, destination, immediate or reserved position. The same
feedback updates body references and support/placement parameters. This is
executable data mutation—not merely choosing another label in a fixed
operation catalogue. The interpreter itself remains a normal loaded CUDA
kernel.

## Double pinion, Hadamard, : and RK4

For decoded complex values a and b, the double split is

```text
h0 = (a + b) / sqrt(2)
h1 = (a - b) / sqrt(2)
```

The native `:` coupling is the real-vector contraction
`dot(a,b)=Re(a)Re(b)+Im(a)Im(b)`. Its angular contribution is `dt*dot(a,b)`.
The double phase differential is a wrapped second difference of the selected
neighbour phase, local phase and the second neighbour stream. The selected
operator body supplies the drive words.

The chart derivative is

```text
f(u,v) = (drive_u + coupling sin(2 pi v),
          drive_v + coupling cos(2 pi u)).
```

The native update is a **forced four-stage map using RK4 weights**. Its
fourth derivative evaluation uses an additional `2/65536` in its Y/phase
chart coordinate: the source's two one-bit Y-up shifts occur specifically
in the fourth slot (source page 7). This event is part of the model and is
preserved by optimization. With that fixed event present, the map is not
classical fourth-order integration of the unforced derivative above.

For `q=(u,v)` and `epsilon=2/65536`, the stages are

```text
a = f(q)
b = f(q + dt*a/2)
c = f(q + dt*b/2)
d = f(q + dt*c + (0,epsilon))
q_next = q + dt*(a + 2*b + 2*c + d)/6
```

As `dt` tends to zero with `epsilon` fixed, the limiting derivative is
`(5*f(q) + f(q+(0,epsilon)))/6`. Consequently an event-induced difference
from the unforced ODE remains even as its integration step shrinks. The
double pinion applies opposite log-radius/phase drifts to the twin streams
before folding and encoding them. The independent diagnostic and its scope
are recorded in [THEORY_SUPPLEMENT.md](THEORY_SUPPLEMENT.md).

Initial operator locations use golden-angle phyllotaxis: normalized radius
`sqrt((i+1/2)/31)` and phase `i * (3-sqrt(5))/2` turns, converted into the
logarithmic chart. Packed field ordering uses the corresponding integer
golden-step sequence. This is the chosen packing/address rule, not a claim of
measured uniform area density on K.

## RGBA and inverse T

The source wavefront `[0,2,0,1]` seeds the first block as zero and quantized
amplitude two in its dichromatic streams, zero B history, and the inverse-T
identity. The amplitude two passes through the same LP8 encoder as every
other amplitude; it is not silently assumed exactly representable.

B is a rolling 32-bit per-block history, incorporating the one-bit jitter,
return parity and previous field result. A is two 16-bit modular inverse
phase rotations, one for each pinion. For a forward rotation word p, the
inverse word is `-p mod 65536`; their composition is exactly zero turns.

Thus T in this edition is the pair of **phase rotations**, not the entire
Hadamard/quantization/update map, and not time or temperature. A contributes
to subsequent circulation through the editable `inverse_gain` coefficient.
It is never treated as an opacity value or clipped to [0,1].

B/A are one exact eight-byte record per 16 token pairs. This grouping is an
explicit packing choice. There is no claim that two extra independent
per-texel channels fit inside a one-byte-per-texel BC5 allocation.

## BC5 and the exact companion

In BC5 mode, each channel of a 16-pair block is encoded using two endpoints
and sixteen three-bit selectors. Native hardware texture fetches perform the
read-side decode. Re-encoding occurs in the field evolution, with raw block
words committed by a later surface-write kernel.

BC5 interpolation acts on **token bytes**, not independently on their
log-radius and phase nibbles. It can change either part, including at nibble
boundaries. The `software_codec_mean_absolute_token_error` report is byte-code
error; it is not angular error or a geometric-distance error. GPU self-tests
allow one UNORM8 unit when comparing hardware and software BC5 reconstruction.

The RG8 companion uses the identical operators and LP8 tokens with no BC5
loss. It is the experiment for isolating that additional compression effect.
Changing between these modes changes storage/codec behavior, not the source
operator catalogue.

## Interval size and work

`--blocks-per-step` is an explicit part of the asynchronous field schedule:
only that window is committed at an interval, while operators change at every
interval. Changing it changes the temporal recurrence, not merely performance.
A snapshot retains it for continuation.

With B active blocks, H chain hops, D tree depth and L body length, the native
interval performs work proportional to `B * (H + D + L + codec work)`, plus 31
operator mutations. A complete sweep must visit every payload block. The
constant-size hot catalogue does not imply an O(1) rewrite of all VRAM data.

No automatic opacity clipping, divergence pruning, damping reset, external
reward optimizer or host texture swapping is inserted in this circulation.
