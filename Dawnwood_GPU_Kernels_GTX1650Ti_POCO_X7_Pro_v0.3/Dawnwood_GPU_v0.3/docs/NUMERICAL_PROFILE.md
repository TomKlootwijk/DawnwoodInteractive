# DWI-N1 — numerical bindings for the Dawnwood recurrence

**Tom Klootwijk · Dawnwood Interactive · Version 0.3.0**

This profile turns the source's connected operator/state definition into executable FP32/uint32 operations. The original discussion is `source/double-slit-theory.pdf`. The original relationships are listed below alongside the equations and storage choices introduced to execute them. A numerical binding is an implementation choice, not an equation retrospectively attributed to the source.

## 1. One evolving field, two scheduled compute passes

The live state consists of a set of wavefront states and one shared, mutable operator LUT. Each operator has a scalar expression program, field parameters, position, phase, transport parameters and one-bit/routing context. The default catalogue has the 31 source-named entries retained by the v0.2 formalization.

One Ψ interval is scheduled as:

1. `mutate.comp`: read the preceding whole state and preceding operator field; write the next operator bodies, field parameters and Klein-surface positions.
2. A Vulkan compute-write → compute-read memory dependency.
3. `evolve.comp`: read the preceding wavefront state and the changed operator field; evaluate the numerical recurrence; write the next whole wavefront/history/inverse-T state.
4. A dependency before the next interval; exchange the roles of the two state buffers and two operator buffers.

The operator that performs mutation is itself record 30 of the preceding LUT. The pinion is record 5. The mutation pass reads two reproducible feedback states for each operator: `(17*i + epoch) mod N` and `(31*i + epoch + 1) mod N`. These sampling rules are this profile's explicit coupling choice. The operator change therefore depends on numerical results of earlier circulation, not a detached animation timer. All operators share the same evolving field.

These are actual GPU storage-buffer writes and subsequent GPU reads. Updating an operator's `program` changes its interpreted body without recompiling the native compute pipeline. There is no per-interval host upload of that operator change.

## 2. Klein carrier and situated fields

Source basis: pages 12–16. The carrier is the quotient

`(u+1,v) ~ (u,-v)` and `(u,v+1) ~ (u,v)`.

The local chart is continuous; it is not a pixel raster. Points are stored as two FP32 chart coordinates and a transported orientation bit. Crossing an odd number of u-seams reverses v and flips the orientation bit. Negative and multiple wraps use the same rule.

For inspection, the carrier has the analytic four-dimensional embedding

```
U = 2πu; V = 2πv
E(u,v) = ((2+cos V)cos U, (2+cos V)sin U,
          sin V cos(U/2), sin V sin(U/2))
```

`E(u+1,v) = E(u,-v)`. The two pinion transport components change operator chart positions; canonicalization keeps those positions on the carrier. There is no projection onto a substitute sphere or a flat disk.

The source does not prescribe an ambient-space Klein SDF formula. N1 binds that term to the intrinsic Klein carrier with local signed primitive fields. It does **not** represent the Klein bottle as the boundary of an ordinary signed 3D solid. This choice is explicit so a different surface equation can replace it without changing the source record.

For a point and an operator anchor, `dw_field` chooses the shortest flat-quotient displacement from three horizontal lifted images and the nearest vertical image. It evaluates a local geometric field at that displacement, with log-radius-derived local transverse coordinate. The orientation bit transports the sign of the local transverse coordinate. This local signed coordinate is not a global orientation of the Klein bottle.

## 3. Every operator has an executable body and a field

An operator is 64 bytes:

| Word positions | Values |
|---|---|
| 0–3, FP32 | u, v, radius, height |
| 4–7, FP32 | phase, gain, coupling, shear |
| 8–11, FP32 | du, dv, mutationRate, reserved |
| 12–15, uint32 | program, seed, kind, flags |

A body contains eight four-bit scalar instructions in a uint32. The low nibble executes first. The instruction set is: identity, add gain, subtract gain, multiply by coupling, sine, cosine, absolute value, negate, square. Zero is an explicit identity instruction; unknown instructions are rejected by the authoring/CLI path. The default body is `0x341`: add gain, sine, multiply by coupling, then identity slots.

`dw_field` evaluates the situated primitive and the current body. `dw_apply` combines an input value with the current situated field and evaluates the body. This makes an operator's body and location participate in its action. The integer jitter, branch and parity roles additionally consume the current packed program as an integer control word.

At mutation, the body word can change between the add/subtract or sine/cosine alternatives. The gain, phase, shear and surface position also evolve. Their change depends on the current mutation operator, the preceding feedback state and local field values. This is a concrete finite expression profile, not a claim that eight scalar instructions alone prove universal computation.

`--program index:0xHEX` changes a body before a run. `tools/edit_checkpoint.py` changes actual live operator records between checkpointed runs. Both paths affect subsequent numerical evaluation.

## 4. The wavefront, log-polar encoding and twin pinion

Source basis: pages 3–6 and 11–12. The source instance `[0,2,0,1]` initializes the two complex channels `(ar,ai)` and `(br,bi)` as `(0,2)` and `(0,1)`. Its squared norm is five. The runtime does not silently normalize the supplied vector to one.

The source labels this an FT wavefront but does not supply a general 756-to-vector map. The exact four numbers are preserved. A separate test evaluates the forward-DFT interpretation of those four samples, yielding `[3,-i,-3,i]`; that test is not used to invent a timestamp encoder.

The numerical radius coordinate is `rho = ln(r)` with angle `theta`; decoding uses `r = exp(rho)`. Decoded polar components participate in the local geometric fields and pinion coupling. Multiplicative radial scaling is additive in rho. No fixed quantization range or opacity clipping is introduced into this coordinate definition.

The hinge is the normalized two-channel Hadamard action, followed by opposite complex phase rotations for the two pinions. The phase depends on one-bit jitter and the changed Hadamard, crystal, wavefront and dichromatic field/body records. The existing channel norm is preserved to floating-point accuracy; there is no after-the-fact renormalization hiding numerical error.

Population parity and integer even/odd classification are distinct operations. The source's 7/54 fixture yields the stated 1/0 pair under population parity. The implicit binary route uses `2*i+1+b`. Its branch bit combines the declared one-bit controls, transported orientation and current routing records.

## 5. Kinematics, geometry and the source's fourth-slot event

Source basis: pages 7–9. `dw_derivative` supplies the autonomous vector field for `(u,v,rho,theta)`. It uses the six source primitive fields, the pinion, the colon coupling, log-polar components, the selected operator, the phase differential and the preceding inverse-T response. The exact equations are shared in `include/numeric_evolve.inc` and are compiled into both CPU and GPU implementations.

The six source primitives are real numerical fields:

- T: union field of two boxes.
- Pyramid side: a signed triangular cross-section extruded in the local transverse coordinate.
- Circle: radial signed distance in the local two-dimensional section.
- Cone: signed distance to the side/base of a capped rotational cone.
- Sphere: Euclidean radial signed distance.
- Apex: distance to a point.

The apex field is unsigned away from its zero. A blended or bytecode-transformed scalar field need not remain an exact metric distance field. The suite explicitly tests a scaling counterexample instead of assigning the SDF label an untested unit-gradient guarantee.

The colon binding is a Frobenius coupling of the two constructed pinion tensors. The source leaves its operand equation open; N1 makes this choice visible. Fibonacci phyllotaxis initializes states and operator anchors with golden-angle positions and square-root radial progression. The live phyllotaxis operator also participates in phase divergence. The phase differential uses the current and preceding two phase samples, then the current delta-phi body.

RK4 uses four actual derivative evaluations. Before the fourth evaluation, the stage's local v coordinate receives the current Y-up displacement **twice**. Its value is the configured `yup` multiplied by the current Y-up field/body response. Tests confirm that this changes the fourth stage without changing the first three in the same interval. The source did not provide a numerical derivative or displacement size; these are N1 bindings. With this additional event enabled, ordinary unmodified-RK4 order is not simply assumed.

The Ψ record supplies a small numerical modulation of the local integration step. The global logical Ψ cadence remains one pair of compute passes. The source did not specify a physical wall-clock duration.

## 6. RGBA, history and inverse T remain connected

Source basis: pages 9–12. R and G represent the two pinion streams; their complex phases remain in the live state rather than being lost in an intensity-only texture. B is a declared finite history recurrence of the previous history, four kinematic slopes, jitter and inverse-T response.

T is bound to a two-dimensional rotation/shear transformation. The runtime evaluates its actual 2×2 inverse. A is an **integer reference to the inverse matrix stored with that state's record**, not a scalar opacity substituted for four matrix components. The storage cost of the four inverse coefficients is counted. The inverse-T body's output participates in the following history, radial derivative and operator mutation.

The test suite checks `T * inverse(T)` numerically. It also supplies a counterexample showing that an inverse transform does not by itself remove added channel noise. That distinction tests the source's inverse-related claims without deleting the inverse from the recurrence.

Each live state is 128 bytes: 24 FP32 values, four uint32 values, then four FP32 values. The final four carry the two preceding phase samples, inverse-T response and last jitter. The whole state and changed LUT feed the next interval. Checkpoints store all live numerical state and operators.

## 7. Optional output and packing

Catalogue entries 25 (Bayer) and 26 (BC5) are downstream markers. If an intrinsic route ends at either, its scalar input passes through unchanged; their output operation is scheduled only by the downstream tools, not injected into feedback. This is an explicit scheduling rule, not an unimplemented operation hidden as a no-op.

The optional Bayer function is downstream of returned state; it is not a required raster, raymarcher or raytracer. `tools/readout.py` reads a completed numerical checkpoint and exports channel values and ordered-threshold output as CSV. It never feeds a display pixel back into the compute recurrence.

BC5 is tested with an actual CPU block encoder/decoder and a device-format probe. It uses 16 bytes for a two-channel 4×4 block and generally reconstructs arbitrary inputs approximately. The exact live operator/state records therefore remain in storage buffers in N1. The source's BC5 compression figures are tested as storage-format claims, not assumed to encode a full 128-byte state losslessly in one texel. The POCO probe reports BC5 support rather than substituting another format without telling you.

## 8. Parallel semantics and storage

N states share M operator records. Mutation is one invocation per operator; evolution is one invocation per state. Each output has one writer. Mutation reads old state and old operator records; evolution reads old state and new operator records. The compute barriers implement that ordering. No cross-workgroup spin barrier or global in-place race is used.

The two state buffers use `2*N*128` bytes and two operator buffers use `2*M*64`. One reusable host-visible transfer buffer uses `max(N*128,M*64)` bytes. Driver allocation padding and all additional objects are reported separately where available. There are no stored child pointers. Removing two hypothetical uint32 child pointers would save `8*M` bytes, not multiply the already pointer-free state capacity.

The workgroup size is 64. The runtime requires Vulkan 1.1, FP32, uint32 and storage buffers, not CUDA, ray tracing, tensor operations, device addresses or FP64. It checks actual storage-buffer, dispatch and memory-budget limits before allocation. Allocation failure is reported; the recurrence is not clipped or silently shrunk. The epoch representation is explicitly uint32 and is checked before exhaustion.

## 9. Meaning of the tests

CPU and Vulkan compile the same numerical functions. Their agreement tests the backend, ABI, ordering and implementation of these equations. Independent analytic fixtures test the basic mathematical bindings. Numerical agreement is not presented as an independent derivation of the source's physical claims.

`docs/CLAIMS.md` links each original requirement or claim to a runnable test, a measurement protocol, a counterexample, or the additional evidence needed to evaluate it. The report never turns shader compilation, a software Vulkan run, or the presence of a phone build project into a claim that your physical devices have been tested.
