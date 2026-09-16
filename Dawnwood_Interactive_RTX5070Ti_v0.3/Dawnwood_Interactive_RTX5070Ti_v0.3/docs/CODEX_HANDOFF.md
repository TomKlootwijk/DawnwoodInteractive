# Codex development and acceptance handoff

Work from `README.md`, `NATIVE_BINDING.md`, and the original PDF. Keep the
operator definitions and state feedback together. Preserve the source names.
Numerical changes belong in the binding document and in tests as well as code.

## First hardware session

Build native CUDA for `120-real;120-virtual` on the target laptop. The delivery
environment had neither nvcc nor an NVIDIA device, so CPU test results are not
native compilation or performance evidence. Start by recording `nvcc --version`,
`nvidia-smi`, `dawnwood --probe`, the native build log and `--self-test` output.

Run `tools/gpu_acceptance.py` with a new output directory. It verifies actual
texture decode, commit/read coherence, integer interpreter equivalence,
self-mutation, repeatability, full-field snapshot hashes and graph/sequential
launch agreement. GPU comparisons are tests to execute, not pre-existing pass
claims.

Run Compute Sanitizer memcheck, racecheck and synccheck on small dimensions and
partial windows. Check both BC5 and RG8. Pay particular attention to raw uint4
array BC5 resource-view setup, texture result component conversion, byte offsets
of surface writes, page seams, and alignment of the hot linear textures.

A toolkit/header API correction should not silently replace BC5 with an
uncompressed allocation while preserving the `bc5` label. Keep the exact RG8
companion separate and use the native decode test to demonstrate the actual
format in use.

## Capacity session

Run the saturation command and retain its report. Observe the selected device's
free memory before and after allocation. Verify that `token_pairs`, page count,
B/A storage and payload bytes reconcile. Run enough intervals for at least one
complete sweep; the report exposes both block updates and sweep count.

No claim of a texture-cache lock, zero PCIe utilization, bandwidth saturation
or a particular updates/second figure follows solely from allocation. Measure
those with the appropriate device/driver profiler. Do not replace missing
measurements with nominal specifications.

## Optimize without changing the definition accidentally

Keep immutable-read / commit ordering. Do not texture-read a location written
by another thread in the same kernel and assume a block barrier is sufficient.
Keep exact code words and B/A outside the lossy BC5 channels. Do not add an
unreported clamp to alpha or log radius; the quotient and token encoder already
define the representation.

Evaluate register usage, spills, occupancy, texture misses, BC5 encoder cost,
chain locality and launch overhead separately. The current BC5 encoder searches
eight endpoint-palette entries per token. A faster encoder may change the
quantized recurrence: retain a comparison mode and record its change.

`--blocks-per-step`, operator body depth, `--hops`, initial placement, numeric
precision and compression choices affect semantics. Do not call changes to
those values a semantics-preserving optimization without comparison evidence.

## Modification entry points

`core.hpp`: primitive fields, quotient, encoding, body interpreter, kinematics,
one-bit mutation. `model/operators.json`: initial executable bodies and fields.
`kernels.cuh`: texture-chain execution and ordered commit. `main.cu`: allocation,
cache-policy request, graph construction, reporting and snapshots.

The packed body interpreter is intentionally explicit. Adding more body
instructions, registers or catalogue entries requires a versioned image/snapshot
ABI and corresponding tests; it is not equivalent to changing a JSON label.

Do not commit run snapshots or reports containing private attribution to an
external repository as part of testing unless the project owner directs it.
