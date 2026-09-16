# Dawnwood Interactive: literal source, mathematical binding, and evidence audit

Audit date: 2026-09-16. Source: the complete 24-page `double-slit-theory.pdf` supplied by the user. Its SHA-256 is `e3cf7d49e6a4942c7ccad4805f6a2a07e1c817753ff8d384b1f2e37791ebbe27`, identical to `source/double-slit-theory.pdf`. All pages were extracted and rendered; the relevant text, tables, diagrams and notes on pages 3-23 were reviewed. The source is an exported conversation, containing the user's design requirements and another assistant's interpretations and predictions. These are different kinds of evidence. No physical experimental dataset, numerical convergence result, independent universality proof, or GPU measurement is supplied by that conversation.

## Verdict

Dawnwood implements a finite, deterministic, self-modifying numerical state machine inspired by the user's stated design. It contains the source's two streams, one-bit decisions, moving and mutating operators, quotient geometry, chained texture storage and four-slot update. These claims are directly inspectable and falsifiable. It does not thereby validate quantum double-slit physics, a quantum computer, an optimal search process, or an unrestricted universal computer. New diagnostic measurements actively rule out interpreting the default LP8 recurrence as a norm-preserving physical wave simulation.

The appropriate formal description is **a self-referential digital automaton on a quantized Klein quotient, with a forced four-stage chart update and a mutable packed operator interpreter**. This describes what it executes, without granting stronger properties merely because familiar physics words appear in the source.

## Literal source correspondence

| Source pages and literal design | Executable binding | Assessment and unresolved meaning |
|---|---|---|
| 3-4: double vertical slit, two pinions, Hadamard mitosis hinges, log-encoded polar LUT | `lut_entry`, `complex_token`, `evolve`: two complex streams and `(a+b,a-b)/sqrt(2)` | The unquantized Hadamard algebra is present. A spatial slit aperture, wavelength, detector, propagation equation and experimental likelihood are absent. LP8 is a chosen finite quotient, not a physical derivation. |
| 4-5: zero-order even/odd one-bit parity | `parity`, `ins`, `execute`, `route`, `jit` | Actual bit operations exist. Population parity is distinct from integer even/odd parity; the source's example 7 and 54 uses population parity. A one-bit decision does not imply all state or all arithmetic is one bit. |
| 6: `[0,2,0,1]` wavefront and one-bit jitter | `seed_block(0)`, deterministic hashed `jit` | First block is bound to zero R, quantized amplitude-two G, zero history and phase-inverse identity. This is not a Fourier transform of timestamp 756. The seed clock interpretation is chosen, not derived. |
| 7: two Y-up shifts in the fourth RK4 slot | `rk4`: add `2/65536` only to the y argument of the fourth derivative | Literal event is implemented. Preserve it when optimizing. Call this a forced RK4-like map, not fourth-order integration of the unforced derivative. The source never supplies an ODE or a units convention. |
| 8-9: T, pyramid side, circle, cone, sphere, apex; double-dot; double phase difference; Fibonacci blend | `support_sdf`, `sd_triangle`, `sd_box`, `evolve`, golden-angle `seed_op` | T and triangle are local support shapes, cone is a meridian and sphere an ambient 4D radial support restricted to K. Double-dot is chosen as a real two-vector contraction. There is no derivation that these are exact full 3D solids or a tensor cross-product. |
| 9-12: dichromatic RG with B history and A inverse T | LP8 R/G, exact `Aux {history,inverse_t}` per 16 pairs | A stores the inverse of two quantized phase words only. It does not undo Hadamard, BC5 loss, radius folding, coupling twist, jitter or the entire recurrence. B/A consume eight explicit bytes per block. |
| 12-14: disregard rasterization, raymarching, raytracing and square computational fields; self-referential SDF Klein bottle; optional Bayer readout | `fold`, `klein`, local supports, implicit operator tree; rectangular CUDA arrays only as storage | Quotient identity is present and measurable. A global signed distance to a Klein surface is not implemented. The Klein bottle is a closed surface, not a surface with the source assistant's purported single edge. Optional Bayer readout is not necessary for this kernel and is not evidence for physics. |
| 14-16: operators themselves move and change at Psi | `mutate_op`, alternate operator banks, field-selected stage sample | Actual instruction words, references, support, coefficients, location and routing change. GPU machine code remains fixed. Tree storage stays 31 nodes; no nodes grow and no topology is dynamically allocated. |
| 18-20: texture cache working set, packed VRAM saturation, no host hot-swap | cooperative shared hot set, texture objects, requested L2 policy, GPU-owned pages | Resident allocation and update coverage are testable. Cache retention and performance are hardware outcomes. There are still floating trigonometric, logarithmic and geometric operations. Shared memory is loaded per CUDA block, not an immortal on-chip store. |
| 21-22: one-bit hierarchy and implicit children `2i+1`, `2i+2` | `child`, `route`, 31 operator records | Four decisions choose among 16 leaves. This tree does not search every billion-scale payload element. Child pointers are absent; live body references remain. |
| 23: anything can be expressed, Turing completeness, neural inference/database mappings | eight-register, eight-word bodies, finite field and state feedback | No reduction from a known universal machine or scalable memory/control construction is supplied. The actual finite hardware machine has a finite state space. Useful programmable behavior and universality are distinct claims. |

## Explicit state transition

Let `F_e = (P_e, O_e, A_e, B_e, e, c_e, seed)`; `N` is the number of 4x4 blocks and `W <= N` the update window. At interval e, block `i = (c_e+t) mod N`, `0 <= t < W`, reads the committed field, follows H data-selected page hops, traverses the depth-four operator tree, executes its two referenced bodies and own body, and writes a private staged result. A separate commit publishes unique destinations. Thirty-one operator updates read the previous bank and sampled stage results. Finally `c_(e+1)=(c_e+W) mod N` and `e` increments.

This separation is semantically important: changing W changes how much of the field evolves before its operators change. W is a model parameter, not a neutral benchmark tuning switch. A performance comparison must hold W, seed, dt, H, codec, jitter and mutation flags fixed unless it is explicitly a different recurrence.

For `q=(u,v)`, `f(q)=(d_u+k sin(2*pi*v), d_v+k cos(2*pi*u))`. The four slopes are `a=f(q)`, `b=f(q+dt*a/2)`, `c=f(q+dt*b/2)`, `d=f(q+dt*c+(0,epsilon))`, with `epsilon=2/65536`. The update is `q'=q+dt*(a+2b+2c+d)/6`. As dt tends to zero while epsilon stays fixed, its limiting vector is `[5*f(q)+f(q+(0,epsilon))]/6`, not f(q). This follows directly by taking the limit of the slope arguments. The event is intentional source fidelity; its numerical meaning must be stated.

The decoding coordinates use `rho=-4+7.5*u` and `z=2^rho*exp(i*2*pi*v)`. The fold identifies `(u+1,v)` with `(u,-v)`. It therefore also identifies radii differing by `2^7.5`, approximately 181.02, with a phase reversal. Such equivalence is a quotient-computing choice and cannot preserve an ordinary physical amplitude scale.

## Executed independent diagnostics

The standalone `tools/theory_diagnostics.cpp` was compiled with MSVC 19.44, C++17, `/O2` and `DW_REFERENCE_KERNEL=1`. Raw results are in `results/optimization/theory_diagnostics.json`. It evaluates the native header on the CPU, plus a clearly separated double-precision mirror of the stated four-stage equation for convergence analysis. It is not a GPU performance benchmark or an experiment on photons/electrons.

| Measurement | Result | Meaning |
|---|---:|---|
| Nonzero LUT-pair inputs exhaustively evaluated | 65,280 | All 256 squared token combinations except 256 zero/zero combinations. |
| Largest relative norm residual of float Hadamard before encoding | 1.6708e-7 | The isolated linear split agrees with its norm identity to float precision. |
| Input pairs whose LP8 output energy differs by more than 1e-4 relative | 53,440 | The complete encoded split is not unitary, even without BC5. |
| Minimum / maximum LP8 output-to-input pair energy ratio | 3.0518e-5 / 32,768.00365 | Radius wrapping can destroy the physical magnitude interpretation. The maximum witness is input tokens `[17,0]`, output `[254,254]`. |
| Ideal opposite-phase directed token pairs with nonzero encoded sum | 240 / 240 | Tiny floating cancellation residuals are nonzero and wrap through the logarithmic quotient. |
| Largest raw canceled amplitude / largest decoded encoded-sum amplitude | 1.2157e-6 / 9.51366 | Different maxima over the same 240-pair population; these are not one paired measurement. Maximum output witness: `[19,27]` gives token 248. |
| Nonzero LP8 cell-centre roundtrip failures | 0 / 240 | Byte-centre reproducibility holds; this does not imply real-amplitude fidelity. |
| Maximum Klein seam coordinate residual over 29,161 sampled points | 4.0121e-6 | Native float K respects the specified seam to small numerical error. |
| Modular phase inverse failures | 0 / 65,536 | Each 16-bit phase word plus its stored additive inverse is exactly zero modulo 65,536. |
| Encoding the source amplitude 2 | token 176, magnitude 2.37841, complex absolute error 0.570964 | Exact RG8 bytes still represent quantized amplitudes, not exact physical amplitude 2. |
| 256-step unforced classical double error over T=1 | 1.2906e-12 | Ordinary RK4 converges against the 131,072-step reference for the diagnostic ODE. |
| 256-step forced double error against that same unforced reference | 2.2248e-6 | Fixed event produces a nonzero model bias; halving dt does not remove that event. |

The Hadamard identity is `|h0|^2+|h1|^2=|a|^2+|b|^2`, and its constructive/destructive law is `|a+b|^2=|a|^2+|b|^2+2 Re(a conj(b))`. Passing that local identity checks an algebraic component. Physical double-slit validation would require specified geometry, preparation, propagation, a measurement/detection rule and quantitative comparison to independent observations. The current program contains none of that complete protocol. The primary physics reference gives the amplitude-addition and detection-probability distinction: [Feynman Lectures, volume III, chapter 1](https://www.feynmanlectures.caltech.edu/III_01.html).

## Capacity and complexity corrections to the source assistant's predictions

BC5 stores sixteen R/G pairs in sixteen bytes; it cannot also contain independent B and A channels for free. This binding adds eight bytes of B/A per sixteen pairs: 1.5 bytes per pair in BC5 and 2.5 bytes per pair in RG8. BC5's two channels and block layout are documented by [Microsoft's block-compression reference](https://learn.microsoft.com/en-us/windows/win32/direct3d11/texture-block-compression-in-direct3d-11).

An ideal 12 GiB entirely available to payload holds at most 8,589,934,592 BC5 pairs or 5,153,960,755 RG8 pairs under these layouts, before headers, staging, page rounding, driver resources and reserve. For decimal 12 GB the corresponding bounds are 8.0 billion and 4.8 billion. Neither bound is an observed usable allocation. Source page 20 conflates GB and GiB; page 22's 24-48 billion capacity is not derived from this storage format. Removing 31 pairs of child pointers does not multiply a gigabyte-scale payload's capacity by two or four.

For fixed formats, each interval costs `Theta(W*(H+D+3L+16*C_codec)+31)` with D=4 and L=8; a full sweep must touch N blocks and costs at least `Omega(N)`. The constant-size operator mutation is O(31), hence O(1) relative to payload N, but does not update all N payload blocks immediately. Space is `Theta(N)+Theta(W)+Theta(31)` with small additional page and LUT metadata. Ordinary fixed-dimensional coordinate transforms are also O(1) per point; ordinary rendering is not generally exponential in the number of pixels.

Allocating most VRAM proves occupancy of storage. It does not prove that the texture cache has a high hit rate, that bandwidth is saturated, or that runtime is minimal. L2 persistence gives favored retention; its configured `hitRatio` is not the observed cache-hit percentage. [NVIDIA's L2 cache-control guide](https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/l2-cache-control.html) documents the policy and possible evictions. Cache behavior requires hardware counters; timed throughput and allocator byte counts answer different questions.

## Honest supplements supported by the literal document

1. Keep a source requirement table like the one above alongside the new formalization. Mark each numeric choice as a definition of this edition rather than a formula copied from the original conversation.
2. Include the isolated interference identities and the failed full LP8 energy/cancellation observations together. This supplies a falsifiable interpretation of the source's double-pinion claim without pretending the default recurrence is a physical wave model.
3. Specify the fourth-slot event as a first-class part of the law and include its refinement diagnostic. Removing it to recover textbook RK4 would reduce fidelity to the user's page-7 statement.
4. Report code mutation, routing change, operator movement, sweep coverage and reproducible continuation as separate evidence for self-reference. Deterministic hashed jitter is not quantum randomness. Finite loops and total instructions establish termination of each kernel invocation; jitter does not prove absence of global cycles or improved solutions.
5. Report stored pairs, actual allocated/free bytes, token-pair updates per second, time per interval, complete sweep time, codec error and optional profiler counters. ELI5: shelf occupancy, items updated per second, time until every item is revisited, and how much the packing changes each item.
6. Treat BC5 error in phase and radius units as a possible next diagnostic. Byte error alone is insufficient because a small byte change can cross a nibble boundary and change both phase and radius. Keep zero/nonzero flips separate from circular phase errors.
7. If a future physical companion is desired, define it explicitly: a coherent two-path amplitude model, Born-rule detector, path-length/phase parameters, norm/error tolerances, and coherent versus which-path controls. Replacing quotient wrapping or silently suppressing small amplitudes would change this native model and needs a separate named binding and comparison. Such a companion would validate its own equations; it would still not constitute a new experiment proving the source's quantum claims.

## Required performance evidence

A fair optimization holds recurrence parameters fixed and compares the same initialized state. Verify optimized/reference results by complete state/snapshot comparison where feasible, report hardware-decoder tolerance separately from exact RG8 byte equality, and record compiler/driver/GPU and clocks or thermal context. Use repeated timings with warm-up and report the distribution. Include full resident-field runs because a tiny cache-resident case is not evidence about near-capacity VRAM.

The source's promises of permanently locked caches, zero stalls, zero PCIe traffic, universally optimal paths and unrestricted universality remain unsupported. Avoid replacing them with another unmeasured number. Successful source correspondence, a correct digital recurrence, measured GPU speed, numerical fidelity and physical validation are five separate conclusions.
