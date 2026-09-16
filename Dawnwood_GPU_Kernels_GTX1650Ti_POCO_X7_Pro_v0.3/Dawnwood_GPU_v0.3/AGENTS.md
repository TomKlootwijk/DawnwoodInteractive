# Dawnwood development instructions

Preserve the controlling source and source-page references. Work from DWI-N1's explicit numerical bindings, not a new unrelated simulation. Read docs/NUMERICAL_PROFILE.md and docs/CLAIMS.md before changing semantics.

The active implementation is numerical C++ plus two Vulkan compute shaders. It is not the previous symbolic DAG workbench. Operator body, field, position and feedback must remain connected. No source term may be replaced by a silent no-op. Unknown bytecode must be rejected by input validation, not advertised as implemented.

Edit shared equations in include/numeric_types.inc and include/numeric_evolve.inc. Regenerate shaders with tools/build_shaders.py. Keep scalar-layout ABI tests. Do not relax CPU/GPU tolerances solely to obtain a pass; report the first divergent epoch and field, then diagnose ordering, contraction, precision or a genuine binding change.

Body-coverage tests must inspect numerical state, not only an edited instruction word. Preserve fourth-slot double Y-up, six primitive fields, inverse-T matrix storage, history and non-orientable transport. Bayer and compression are downstream experiments, not a required pixel substrate.

Run CPU fixtures and Vulkan validation/comparison. Record real hardware identity. A CPU/software Vulkan result is never a GTX or Mali result. A compiled APK is never a completed phone test. Keep command exit codes and raw logs. Do not replace an unavailable measurement with an assumed zero or an estimated speedup.

The source's physical, capacity, cache, deadlock and universality claims have distinct evidence requirements. Keep counterexamples and unmeasured rows visible. Do not delete a failing claim test to make the project look validated.

Primary target profiles: GTX 1650 Ti laptop 4 GB and POCO X7 Pro 12 GB system RAM. Query actual device memory and feature support; do not treat phone RAM as dedicated VRAM. Keep the numerical profile reproducible across both implementations.
