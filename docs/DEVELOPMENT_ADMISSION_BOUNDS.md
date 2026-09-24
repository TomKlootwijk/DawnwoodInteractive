# FP32 admission bounds for developed resource regions

This is a source-level bound for the guards in
[`source_development_bindings.py`](../local_lab/source_development_bindings.py),
compared with the exact packed-constant certificate in
[`development_sdf.py`](../local_lab/development_sdf.py). It is not a GPU
measurement. Direct arithmetic counterexamples and reference experiments are
retained in [admission_bounds](../output/source_development_2026-09-25/admission_bounds/).

The distinction is between **the actual protected domain** and **the full
declared interior proof margin**. With quota at most 16, the original
one-margin FP32 guards protect nonnegative coordinates, the quota, and positive
separation. They do not necessarily preserve the entire exact `1e-4` margin
used by the standalone certificate. Two-margin box guards close that gap.

## Preconditions

The following conditions are part of the bound, not consequences of a sampled
test:

1. Stored coordinates, extents, quota and code words are finite binary32.
   Every nonfinite intermediate is rejected by the interpreter.
2. The protected structural check establishes canonical active counts
   `1,3,5,7`, the corresponding root, unique active leaves, exact references,
   zero inactive words and bounded integer revision before interpretation.
3. Both box and separation checks pass before a program is admitted. They are
   protected validation definitions; the developing constructor cannot replace
   them or rewrite the quota's meaning.
4. Extents exceed packed `1e-5`; quota satisfies `8m < Q <= 16`, where
   `m = binary32(1e-4) = 0.00009999999747378752`.
5. The declared addition/subtraction order is preserved. FP32 operations are
   not reduced to a lower-precision format or reassociated under fast math.

For normal results, use the conservative relative error bound
`epsilon = 2^-23`, covering either adjacent binary32 rounding result. This does
not require a particular nearest-rounding choice. Vulkan specifies the
precision and rounding requirements for shader FP32 addition/subtraction in
its [SPIR-V environment](https://docs.vulkan.org/spec/latest/appendices/spirvenv.html).
The guards' positive magnitudes and minimum extents keep the successful
comparisons away from the subnormal range. Absolute value, minimum, maximum
and comparisons do not introduce the arithmetic errors bounded below.

The retained direct experiment simulates nearest-even binary32 operations;
its observations therefore have that narrower numerical scope. The analytical
bound uses the larger `epsilon` above.

## Box containment

Write `fl` for one declared FP32 operation and let `g` be the guard margin.
The native box checks are:

```text
fl(cx-hx) >= g
fl(cy-hy) >= g
fl(fl(cx+hx) + fl(cy+hy)) <= fl(Q-g)
```

A successful lower check implies the exact packed-constant difference is
positive, so centers and extents are positive. More precisely:

```text
cx-hx >= g/(1+epsilon)
cy-hy >= g/(1+epsilon)
```

Let `T=cx+hx+cy+hy`, evaluated exactly from the packed constants. The two levels
of positive summation give:

```text
fl(fl(cx+hx)+fl(cy+hy)) >= (1-epsilon)^2*T
fl(Q-g) <= (1+epsilon)*(Q-g)

T <= (Q-g)*(1+epsilon)/(1-epsilon)^2
```

For `Q<=16`, the worst resulting quota slack occurs at `Q=16`:

| FP32 guard margin | Exact lower-coordinate bound | Minimum exact `Q-T` |
|---|---:|---:|
| `g=m` | `9.999998555e-5` | `9.427798620e-5` |
| `g=2m` | `1.999999711e-4` | `1.942780194e-4` |

Thus one-margin guards keep the real region inside `x>=0,y>=0,x+y<=Q`.
Two-margin guards additionally imply the standalone certificate's exact
`cx-hx>=m`, `cy-hy>=m`, and `T<=Q-m` conditions. The recommended change is only
to the lower-coordinate and quota-corner guards; the standalone proof margin
and coverage margin can remain `m`.

### Concrete one-margin discrepancies

All numbers below denote the exact values of binary32 inputs:

```text
cx = 0.0001219959813170135
hx = 0.00002199598566221539
```

Nearest-even `fl(cx-hx)` equals packed `m`, but the exact difference is below
`m` by `1.8189894035458565e-12`. The box can still be safely positive; it simply
does not have the entire claimed exact margin.

At quota 16, another accepted one-margin example is:

```text
cx = 14.76984691619873
cy = 1.1500531435012817
hx = hy = 0.03999999910593033
```

The rounded upper sum and rounded right-hand side both equal
`15.999899864196777`, so the FP32 check passes. The exact upper sum exceeds
`16-m` by `5.790934665128589e-8`. It remains below 16. Both examples are
rejected by the stronger two-margin box guards.

The quota cap is essential. If it were removed, quota 4096, centers
`(2048,2048)` and extents `(0.00002,0.00002)` would allow the small additions
and subtraction of `m` to round away. The rounded upper test would pass even
though the exact upper sum exceeds 4096. The actual `Q<=16` guard rejects this
case. Raising the quota range requires a new error bound or scale-dependent
guard margin.

## Separation

For one coordinate of two boxes, define the exact signed interval gap:

```text
G = abs(ci-cj) - (hi+hj)
G_fp = fl(abs(fl(ci-cj)) - fl(hi+hj))
```

Containment already establishes `0<ci<16` and `0<hi<8`. Therefore the absolute
center difference and the pair's extent sum are each at most 16. Bounding the
three operations gives:

```text
abs(G_fp-G) <= 48*epsilon + 16*epsilon^2
             = 0.0000057220461258111754
```

The check `max(Gx_fp,Gy_fp)>m` consequently implies at least one exact axis
gap greater than `9.427795134e-5`. Closed boxes are strictly separated, so
minimum composition retains its exact-arithmetic signed-distance meaning.
This axis-gap requirement is stricter than the standalone certificate's
positive Euclidean gap. It can reject a valid close pair; it cannot admit a
touching pair under the stated bounds.

## Constructor versus admission

The proposed half extent is capped by four-margin coordinate/quota terms and
one quarter of the preceding uncovered witness's reported distance. These
are useful proposal restrictions; they are not a substitute for final
validation. The witness distance is a finite-precision evaluation, and a
candidate must be checked against **every** retained leaf. The square's
half-diagonal relation alone must not be promoted to a global admission proof.

An invalid candidate should preserve the entire incumbent code, boxes, root
and revision while returning rejection diagnostics. Invalid already-live code
must fail before it acts. At the maximum revision, construction can also
produce an inadmissible revision unless prevented earlier; that is a bounded
candidate rejection, not permission to round an integer control into range.

All initial and resumed live programs need the same protected checks.
Candidate score, validation bits and retained program identity must refer to
the same candidate. A host exact certificate can audit the result, but it
cannot repair a missing resident check after the program has already acted.

## Predeclared structural task

Use quota one and the following nine training requests:

| Cluster | Requests |
|---|---|
| A | `(0.71,0.15)`, `(0.72,0.16)`, `(0.73,0.17)` |
| B | `(0.15,0.71)`, `(0.16,0.72)`, `(0.17,0.73)` |
| C | `(0.41,0.41)`, `(0.42,0.42)`, `(0.43,0.43)` |

The fixed initial baseline is one box centered at `(0.72,0.16)` with half
extents `(0.03,0.03)`. It covers three requests. No quota-safe axis-aligned box
can cover requests from two different clusters: the required upper-corner
sums are at least `1.42` for A/B and `1.12` for A/C or B/C. Hence three covered
training points are a proven upper bound for **any one-box baseline** in this
grammar, not just this parameter choice.

Three separated components can cover all nine requests. The declared score
is coverage count minus `0.02` per leaf and `0.005` times admitted area.
New opcode/reference nodes, changed region semantics, objective improvement
and subsequent numerical action must all be observed before claiming useful
structural development.

Freeze the retained candidate before holdout evaluation. Generate 300 requests
per cluster independently in the two-dimensional square of center plus/minus
`0.015`, using a separate fixed seed. These requests are not restricted to the
training diagonal. Record all 900 membership/margin results, alongside the
fixed one-box baseline. Do not tune the constructor after inspecting holdout
results and still call the same set held out.

Predeclare an absolute FP32 SDF error limit of `1e-5` for queries bounded to
`[-0.25,16]^2`, compared with the independent rational-edge oracle. Coverage
means distance at most `-m`; classify disagreements within `1e-5` of that
threshold as boundary-ambiguous, rather than silently moving the threshold.
The training and compact cluster holdouts should have much larger interior
margins. Exact packed-constant quota/separation certificates remain mandatory
and do not receive this floating-point tolerance.

This is a synthetic resource-demand task under an explicit accounting model.
It demonstrates structural coverage and a checkable distance program, not
measured allocation success, faster GPU execution or a discovered hardware law.
