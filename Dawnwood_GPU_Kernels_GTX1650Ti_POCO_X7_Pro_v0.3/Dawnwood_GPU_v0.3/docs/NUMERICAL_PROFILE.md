# DWI-N1 — numerical bindings for the Dawnwood recurrence

This document specifies the preserved N1 path. The optional DWI-D1-0.1 extension
has separately declared domain coordinates, affine laws, projections and
checkpoint identity in [DOMAIN_KERNEL.md](../../../docs/DOMAIN_KERNEL.md).

The complete current definition is `FORMALIZATION_v0.5.md`, developed from the supplied unified v0.2 formalization through v0.4. See `CHANGES_v0.5.md` for the arithmetic and texture changes and `VALIDATION_v0.5.md` for measured status. The profile is a discrete recurrence in a canonical Klein chart. Position wrapping does not establish smooth tangent-field covariance across chart transitions; asymmetric operator-frame transport remains an explicit limitation.

**Tom Klootwijk · Dawnwood Interactive · Version 0.5.0 / DWI-N1-0.5**

This profile turns the source's connected operator/state definition into executable FP32/uint32 operations. The original discussion is `source/double-slit-theory.pdf`. The original relationships are listed below alongside the equations and storage choices introduced to execute them. A numerical binding is an implementation choice, not an equation retrospectively attributed to the source.

## 1. One evolving field, mutation then evolution

The live state consists of a set of wavefront states and one shared, mutable operator LUT. Each operator has a scalar expression program, field parameters, position, phase, transport parameters and one-bit/routing context. The default catalogue has the 31 source-named entries retained by the v0.2 formalization.

One Ψ interval is scheduled as:

1. `mutate.comp`: read the preceding whole state and preceding operator field; write the next operator bodies, field parameters and Klein-surface positions.
2. A Vulkan compute-write → compute-read memory dependency.
3. Evolution reads the preceding wavefront state and the changed operator field, evaluates the numerical recurrence, and writes the next whole wavefront/history/inverse-T state. The monolithic path uses `evolve.comp`; the ARM path uses the staged schedule below.
4. A dependency before the next interval; exchange the roles of the two state buffers and two operator images.

The operator that performs mutation is itself record 30 of the preceding LUT. The pinion is record 5. The mutation pass reads two reproducible feedback states for each operator: `(17*i + epoch) mod N` and `(31*i + epoch + 1) mod N`. These sampling rules are this profile's explicit coupling choice. The operator change therefore depends on numerical results of earlier circulation, not a detached animation timer. All operators share the same evolving field.

These are actual GPU image writes and subsequent integer texel reads for the LUT; wavefronts remain storage buffers. Updating an operator's `program` changes its interpreted scalar body without recompiling the native compute pipeline. There is no per-interval host upload of that operator change.

To reduce Mali compiler workload, the ARM path divides evolution into **eight dispatches per population partition**: prepare, four slope evaluations, combine, geometry and finish. Five shader entry points share `dw_prepare`, `dw_slope`, `dw_combine`, `dw_geometry` and `dw_finish` with the CPU and monolithic GPU path. Each dependent dispatch has a compute-write to compute-read/write barrier. The preceding state remains unchanged, the changed LUT is common to all stages, and mutation still executes once per logical epoch. These are subdivisions of one recurrence, not eight epochs. `VALIDATION_v0.5.md` records successful actual phone execution and scoped bitwise comparisons; smaller shaders alone would not establish those results.

The descriptor interpreter, RK4 stage algorithm, Hadamard matrix, primitive formulas, Klein wrapping, route-address rule, update order and allocation sizes remain native implementation rules. The `rk4` record modulates a derivative response; it does not contain an editable integrator. The `hadamard` record affects phase; it does not replace the matrix. Operator feedback changes supported record values and scalar programs, while the fixed tree/population does not grow itself. This is partial realization of the source's stronger proposal that the entire algorithm should be geometrically self-defined.

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

Version 0.5 stores those words in four `RGBA32_UINT` texels per record, in two sampled/storage images. FP32 parameter bits are packed and unpacked losslessly; point `texelFetch` reads perform no interpolation. Orientation is flag bit 0, and all other flag bits survive transfer. This is the agreed representation of packed one-bit controls with full-precision field parameters; neither distances nor complete operators are one bit. The texture contains descriptors for field evaluation, not a spatial grid of precomputed distances.

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

Source basis: pages 7–9. `dw_derivative` supplies the canonical-chart stage derivative for `(u,v,rho,theta)`. It uses the six source primitive fields, the pinion, the colon coupling, log-polar components, the selected operator, the phase differential and the preceding inverse-T response. The exact equations are shared in `include/numeric_evolve.inc` and are compiled into both CPU and GPU implementations.

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

Under the default body, the Ψ record supplies a small numerical modulation of the local integration step. The global logical Ψ cadence remains one pair of compute passes. The source did not specify a physical wall-clock duration.

## 6. RGBA, history and inverse T remain connected

Source basis: pages 9–12. R and G represent the two pinion streams; their complex phases remain in the live state rather than being lost in an intensity-only texture. B is a declared finite history recurrence of the previous history, four kinematic slopes, jitter and inverse-T response.

T is bound to a two-dimensional rotation/shear transformation. The runtime evaluates its actual 2×2 inverse. A is an **integer reference to the inverse matrix stored with that state's record**, not a scalar opacity substituted for four matrix components. The storage cost of the four inverse coefficients is counted. The inverse-T body's output participates in the following history, radial derivative and operator mutation.

The test suite checks `T * inverse(T)` numerically. It also supplies a counterexample showing that an inverse transform does not by itself remove added channel noise. That distinction tests the source's inverse-related claims without deleting the inverse from the recurrence.

Each live state is 128 bytes: 24 FP32 values, four uint32 values, then four FP32 values. The final four carry the two preceding phase samples, inverse-T response and last jitter. The whole state and changed LUT feed the next interval. Checkpoints store all live numerical state and operators.

## 7. Optional output and packing

Catalogue entries 25 (Bayer) and 26 (BC5) are downstream markers. If an intrinsic route ends at either, its scalar input passes through unchanged; their output operation is scheduled only by the downstream tools, not injected into feedback. This is an explicit scheduling rule, not an unimplemented operation hidden as a no-op.

The optional Bayer function is downstream of returned state; it is not a required raster, raymarcher or raytracer. `tools/readout.py` reads a completed numerical checkpoint and exports channel values and ordered-threshold output as CSV. It never feeds a display pixel back into the compute recurrence.

BC5 is tested with an actual CPU block encoder/decoder and a device-format probe. It uses 16 bytes for a two-channel 4×4 block and generally reconstructs arbitrary inputs approximately. Live wavefronts therefore retain full storage-buffer records and operators retain exact integer-texture records. The source's BC5 compression figures are tested as storage-format claims, not assumed to encode a full 128-byte state losslessly in one texel. Device-format availability must be read from the identified probe; the prior POCO probe reported BC5 unavailable.

## 8. Parallel semantics and storage

N states share M operator records. Mutation is one invocation per operator; evolution is one invocation per state. Each output has one writer. Mutation reads old state and old operator records; evolution reads old state and new operator records. The compute barriers implement that ordering. No cross-workgroup spin barrier or global in-place race is used.

The two state buffers use `2*N*128` payload bytes and two operator images contain `2*M*64` meaningful payload bytes before image-row padding and allocation alignment. Reusable host-visible staging is capped at 16 MiB; buffer transfers and whole image-row copies are chunked. Ordinary GPU runs release the initialization snapshot before allocating the final readback snapshot. A snapshot is another `N*128 + M*64` host bytes. On a phone, device allocations and host snapshots share physical RAM. Reported heap allocations include resource padding but omit unreported driver/compiler allocations. There are no stored child pointers. Removing two hypothetical uint32 child pointers would save `8*M` bytes, not multiply the already pointer-free state capacity.

The ARM staged path adds a transient **96-byte `EvolutionScratch` record per active partition state**, containing local step, phase difference, Y-up displacement, geometry result, route/RNG controls and four four-component slopes. Device scratch is `96*min(N,stateDispatchLimit)` bytes, at most **6 MiB** with the current 65,536-state limit. Binding 5 exposes this scratch to the staged shaders. It is reused after all stages of a partition finish and is not part of the 128-byte persistent state or checkpoint. Transient `Config.reserved0` carries the partition base and `reserved1` carries the slope stage; neither overwrites stored configuration. Monolithic GPU execution does not allocate this buffer.

Evolution shares the core 31 operators in 1,984 bytes of workgroup memory; mutation shares two control records in 128 bytes. Higher operator indices use texture fetches. This specifies reuse for a workgroup's lifetime, not permanent residence in the device's hardware caches. At most 65,536 wavefronts are dispatched per current evolution partition. Every partition reads the same old population and changed LUT, and exchange occurs only after all partitions finish, so this does not simulate independent smaller populations. Mutation runs once per logical epoch.

Each staged dispatch initializes its own workgroup-shared LUT window; that storage does not persist across dispatches. ARM vendor ID `0x13b5` selects the staged path in the current implementation; other devices default to the monolithic path. `DAWNWOOD_SPLIT_EVOLUTION=1` selects the same staged path on desktop for comparison and synchronization inspection. Additional dispatches, barriers and scratch traffic are real costs that require separate timing.

The workgroup size is 64. The runtime requires Vulkan 1.1, FP32, uint32, storage buffers and sampled/storage `RGBA32_UINT` images. It checks actual format, buffer, image, dispatch and memory-budget limits before allocation. Allocation failure is reported; the recurrence is not clipped or silently shrunk. The epoch representation is explicitly uint32 and is checked before exhaustion. Capacity measurements use explicit budget fractions and memory reserves; they are completed populations under a stated policy, not hardware maxima.

## 9. Meaning of the tests

CPU and Vulkan compile the same numerical functions. Their agreement tests the backend, ABI, ordering and implementation of these equations. Independent analytic fixtures test the basic mathematical bindings. Numerical agreement is not presented as an independent derivation of the source's physical claims.

The v0.5 arithmetic binding in `include/numeric_math.inc` supplies ordered FP32 sine/cosine/exponential approximations and integer-corrected, round-to-nearest/even division and square root. `PORTABLE_MATH_v0.5.md` specifies reduction, special cases and sampled accuracy. Native division/square-root instructions supply estimates rather than final answers. This revision changes FP32 trajectories from older profiles without changing the real-function intent. Basic arithmetic retains strict noncontraction; absolute/relative comparison tolerance remains `1e-5 + 2e-5*max(abs(cpu),abs(gpu))` and integer comparison remains exact. A separate bitwise-word counter reports stronger identity when actually observed. No finite set of successful trajectories proves arbitrary-horizon or all-device identity.

The portable binding applies to evolution/mutation, while `initialize()` in `src/cpu.cpp` still uses host-native `std::sqrt`, `std::sin`, `std::cos`, `std::log`, `std::fmod` and ordinary initialization division. Therefore Windows and Android can construct different initial FP32 bits from identical configuration and seeds. A local `verify` run supplies its CPU and GPU with the same initial snapshot, so that paired comparison remains valid. It does not establish cross-device replay from CLI parameters alone. Such a comparison must first use an identical checkpoint/initial-state payload and identify the executable profile; no universal cross-device bitwise claim is made.

`docs/CLAIMS.md` links each original requirement or claim to a runnable test, a measurement protocol, a counterexample, or the additional evidence needed to evaluate it. The report never turns shader compilation, a software Vulkan run, or the presence of a phone build project into a claim that your physical devices have been tested.
