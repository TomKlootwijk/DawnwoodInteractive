# Structurally developed resource-admissibility SDFs

`DWI-DEVELOPMENT-SDF-0.1` defines a small language of exact-distance resource
regions. A program can acquire a new rectangle leaf and a new union node; that
changes its executable expression structure. This is a bounded constructor
language, not a claim that every composition of distance functions remains a
distance function.

The [source library](../local_lab/development_sdf.py) implements source-format
validation, exact packed-constant certificates, a binary64 formula evaluator,
an independent boundary oracle, hashes and readable expressions. It does not
execute a GPU, select a best program, or install a resident definition. Runtime
construction and evaluation belong to the corresponding resident development
edition and must supply their own evidence. The helpers in this library are
reference authoring operations, not that runtime implementation.

## Resource meaning and protected facts

Let `p` and `s` be the modeled bytes of persistent and scratch buffers. Choose
one positive common reference `M_ref` and set:

```text
x = (p/M_ref, s/M_ref)
metric(x,y) = sqrt((x0-y0)^2 + (x1-y1)^2)
protected quota: x0 >= 0, x1 >= 0, x0+x1 <= beta
```

The SDF has dimensionless distance units. Multiplication by `M_ref` expresses
the corresponding Euclidean distance in memory-coordinate bytes; it does not
predict execution time or measure a physical separation. The two axes use the
same scale. A different per-axis scale would define a different metric.

`beta` is an explicit application quota after declared overhead and reserve.
Memory omitted from that model remains omitted. Where a real allocation is
being admitted, an independent protected integer accounting check should
remain in force; a learned preference region does not replace resource
accounting or the allocator's result.

Device budget observations are metadata, not permanent physical constants.
Microsoft identifies an OS-provided budget applications should target and
describes possible penalties for exceeding it. [DXGI budget documentation](https://learn.microsoft.com/en-us/windows/win32/api/dxgi1_4/ns-dxgi1_4-dxgi_query_video_memory_info).
The Vulkan specification describes heap budget and usage as estimates, says
the values can change, and does not guarantee that an allocation below budget
succeeds. [Vulkan device memory](https://docs.vulkan.org/spec/latest/chapters/memory.html).
Record the source, units and timestamp of a device observation separately from
the quota used to validate an executable program.

The mutable region is a **preferred admissibility hypothesis**: a subset of
the protected quota region intended to cover useful requested workloads. It
does not redefine the quota. Coverage weights, region-area penalties and
program-complexity penalties are application objectives, not scientific laws.

## Program data and exact constructor rules

The source object contains exactly these keys:

```json
{
  "nodes": [[1,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]],
  "boxes": [[0.72,0.16,0.04,0.04],[0,0,0,0],[0,0,0,0],[0,0,0,0]],
  "node_count": 1,
  "root": 0,
  "revision": 0
}
```

There are four possible boxes, seven node slots, and three scalar control
words. A box is `[cx,cy,hx,hy]`. Node triples are:

| Opcode | Operands | Meaning |
|---|---|---|
| `0` | `0,0` | Inactive zero padding, only after `node_count`. |
| `1` | `box_index,0` | Evaluate one box with index in `0..3`. |
| `2` | `earlier_node_a,earlier_node_b` | Separated union of two earlier subtrees. |

All active nodes must be reachable from the last active node, which is the
root. Leaf indices are unique. Union children must have disjoint leaf-support
sets; repeated subtrees are rejected. Every unused box slot must contain zero.
The revision is an integer in `0..16777215`. Booleans are not accepted as
numbers or integer controls. Unknown keys, opcodes, forward references and
unreachable active nodes are malformed programs.

For one box, with `q=abs(x-center)-half_extents`, the formula is:

```text
d_box(x) = norm(max(q,0)) + min(max(q0,q1),0)
d_union(x) = min(d_left(x),d_right(x))
```

The first formula is the Euclidean signed distance to the box. The second is
an exact signed distance for this language because **all closed leaves are
strictly separated**. Outside the union, the nearest component determines the
distance. Inside it, only one component contains the point; its boundary
remains a boundary of the union. A closest path to another component must
already cross the containing component's boundary.

Overlapping and touching boxes are rejected. In particular, a shared face can
become interior to a union, making a plain minimum of component SDFs return
zero where the true signed distance is negative. Smooth minimum, arbitrary
non-isometric transforms and unrestricted field blends are not constructors
in this exact-distance language.

## Packing, admission gates and independent oracle

Every coordinate and policy scalar is explicitly rounded to binary32; negative
zero is canonicalized to positive zero. Nonfinite or overflowing values are
rejected. The returned `packed_program` is the program whose geometry is
checked and evaluated. The report lists input-coordinate rounding changes.
`beta`, `proof_margin` and `separation_margin` in the report are the actual
packed policy values.

Default policy is `beta=1`, `proof_margin=1e-4`, `separation_margin=0`.
The proof margin must remain positive after packing. For every used box,
the exact rational values of the packed constants must satisfy:

```text
hx > 0, hy > 0
cx-hx >= proof_margin
cy-hy >= proof_margin
cx+hx+cy+hy <= beta-proof_margin
```

For every box pair, compute its nonnegative horizontal and vertical interval
gaps. The sum of their squared gaps must be strictly greater than the squared
separation margin. With margin zero, this still excludes touching boxes.
Certificates use `fractions.Fraction`; they do not validate one rounded
floating-point computation against another copy of itself.

`validate_program()` raises `ProgramFormatError` for malformed structure,
encoding or policy. A structurally valid candidate with failed extent, quota
or separation gates instead returns `admissible: false` and the failed gates.
This is an ordinary rejected geometric candidate. `evaluate_program()` and
`boundary_oracle()` refuse to execute such a candidate and raise
`CandidateGeometryError` carrying that report. A resident controller must
distinguish a recoverable rejected candidate from a malformed runtime program.

The formula evaluator uses binary64 arithmetic at an explicitly packed
binary32 query. The separate oracle enumerates each rectangle's four edges,
projects the rational query onto each closed segment with an exactly clamped
rational parameter, selects the smallest squared distance, then performs one
binary64 square root. It determines the sign from interval membership rather
than the SDF formula. It returns the boundary witness and exact squared
distance; a feasible interior point's nearest feasible witness is the point
itself. Ties choose the lowest box index, then edge index.

The exact certificate concerns the real geometry of packed constants.
Neither the formula evaluator nor a future FP32 device evaluator becomes
exact machine arithmetic. Device tolerance and actual boundary behavior need
independent measurements.

## Identity, structural change and source integration

Three hashes answer different questions:

- `program_sha256` includes revision, node layout and packed box coordinates.
- `topology_sha256` removes coordinates and leaf identifiers and canonicalizes
  child order. It retains binary nesting, so reassociation can change it.
- `semantic_sha256` identifies the sorted packed boxes of the union, ignoring
  identifiers, revision and associative nesting. For admitted separated
  rectangles, these are its uniquely separated rectangular components.

The canonical source serialization is the eight-byte marker `DWSDF001`, three
little-endian uint32 controls, 21 uint32 node words and 16 binary32 box values:
168 bytes. It is a hash serialization, **not a resident checkpoint format**.

Structural novelty cannot be established by a hash change alone. Require a
changed topology, a changed region, a changed numerical action and improvement
under the declared objective. An added leaf at an existing location fails
separation; a reordered union is not a new admissibility region.

The source architecture places body, field and anchor in one situated record
and uses preceding resident definitions to create the next acting definition.
[Unified v0.2, physical pp9 and13](../Dawnwood_Interactive_Unified_v0.2.pdf).
For a resident development application, the newly constructed domain program
must be the program evaluated and potentially retained; a stored candidate
description beside an independently executing old function is insufficient.
Its Klein placement and carrier field retain carrier meanings. They must not
be silently reinterpreted as the two memory axes.

`single_box_program()` and `append_box_candidate()` provide inspectable
reference edits. Appending uses an unused box slot and writes a new box node
and union-with-old-root node, incrementing revision. These Python helpers do
not choose a candidate, perform admission, or demonstrate resident creation.

## Objective and holdout policy

Requests near `(0.72,0.16)` and `(0.16,0.72)` give a concrete reason for adding
structure under quota one. A single axis-aligned rectangle covering both needs
an upper corner with sum at least `1.44`, violating quota. Two separated
rectangles can cover both clusters safely under the declared accounting
model. A third cluster near `(0.42,0.42)` can motivate another component.
These are authored synthetic workloads, not recorded laptop measurements.

A proposed objective is weighted interior-margin coverage minus admitted area
and compiled instruction cost. Extent/containment/separation gates are hard
constraints outside that objective. Holdout requests use separate sampling
seeds and are not revealed during candidate selection. Boundary, corner,
inter-component-gap and exterior geometry checks are a separate mathematical
validation set. A sampled objective improvement is not a proof of a globally
optimal program, a performance advantage or allocation success.

Direct source-library observations are retained under
[domain_definition](../output/source_development_2026-09-25/domain_definition/).
Their experiment text and JSON identify which format errors, geometric gates,
packed-constant proofs and oracle comparisons were actually exercised. GPU
execution and resident proposal/evaluate/retain evidence belong to subsequent
runtime receipts.

The [recorded direct run](../output/source_development_2026-09-25/domain_definition/summary.json)
checked four valid one-to-four-box programs, 25 malformed-program/policy
rejections and seven well-formed geometric rejections. Across 3,608 formula
versus independent rational-edge comparisons, maximum scaled error was
`2.218e-16`, below the predeclared `2e-15` reference threshold. Identity controls
also checked revision changes, swapped union children and equivalent balanced
versus chained unions. These are bounded source-library observations, not
device measurements or a demonstrated learned objective improvement.
