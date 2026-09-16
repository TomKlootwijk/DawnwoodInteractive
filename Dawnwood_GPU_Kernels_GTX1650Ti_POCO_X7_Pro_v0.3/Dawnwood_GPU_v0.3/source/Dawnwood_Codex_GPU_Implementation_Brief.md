# Dawnwood Interactive — GPU implementation brief for Codex

Prepared 16 September 2026. This is an implementation task, not a replacement for the author's source definition.

## Goal and project basis

Implement a numerical, self-referential Dawnwood compute runtime for a Windows/Linux NVIDIA laptop and an Android POCO X7 Pro. Use the supplied v0.2 Unified Substrate Definition, its editable model/cycle files, and the original `double-slit-theory.pdf` as the architectural basis. Inspect the actual repository before relying on filenames or earlier test counts. Keep the existing symbolic workbench available as an authoring and structural reference.

Preserve the double pinion, Hadamard mitosis hinges, log-polar PHI, Klein-bottle SDF, one-bit BST and jitter, fourth RK4 slot with two Y-up actions, primitive geometry, delta-delta-phi, phyllotaxis, colon coupling, blend, RGBA roles, inverse T, and whole-state return. Source pages 3–16 establish these relationships; pages 18–23 contain the GPU and packing discussion. Keep source statements distinct from numerical bindings introduced during implementation.

Deliver running numerical evaluations, not only an expanding expression graph, shader placeholders, or a rendering that does not execute the operator recurrence.

## Targets and first task: discover the devices

The owner describes the laptop as “GTX 1650 Ti 6 GB.” Manufacturer specifications distinguish GTX 1650 Ti configurations with 4 GB from GTX 1660 Ti configurations with 6 GB. Do not assume which GPU is installed. Probe its name, driver, Vulkan support and memory. Either model is listed by NVIDIA's Vulkan driver support documentation. [R1, R2]

Xiaomi lists the POCO X7 Pro with Dimensity 8400-Ultra, Mali-G720 GPU and a 12 GB LPDDR5X configuration. The phone uses shared system memory; its advertised RAM is not a dedicated GPU allocation budget. Probe the installed driver and available features on the actual phone. [R3, R4]

Build a reusable `dawnwood_probe` executable and equivalent Android probe. Export JSON containing device name, vendor/device IDs, API and driver versions, compute queue families, memory heaps/types, memory-budget extension results when available, maxStorageBufferRange, allocation limits, maximum workgroup sizes/invocations, shared-memory size, subgroup properties, supported integer/float features, and format capabilities relevant to any planned textures. Do not allocate all advertised memory to discover a limit.

Useful initial host commands, when the relevant tools are installed:

```sh
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
adb devices
```

ADB tests require the owner's authorized device connection. A simulator, software Vulkan driver, or desktop GPU is not a substitute for identifying the phone in a phone-test result. [R5, R6]

## Proposed implementation stack

Use C++20 for a numerical CPU reference and shared runtime code, CMake for native builds, and Vulkan compute for the common GPU backend. Use GLSL compute shaders compiled to SPIR-V with an explicit common feature target. Provide a desktop CLI and an Android arm64-v8a application using the NDK, with a small Kotlin/Java interface for run/stop, configuration, status and report export. This is an application-level compute runtime, not a replacement operating-system kernel. [R4, R7]

Use native desktop GPU access for initial testing. An optional CUDA backend can follow; it is not the common backend for the Mali phone. Do not assume that a Windows virtualized Linux environment exposes the same Vulkan device as native Windows.

Use uint32 and float32 as the proposed baseline. Document integer overflow/index behavior, packed-bit ordering, numerical precision, operation order, branch/tie behavior and the meaning of every state field. Query optional features before using float16, int16, int64, float64 or subgroup-specific operations. Do not hard-code an NVIDIA warp width into the portable algorithm. [R4]

## Numerical binding work

Before calling an operator numerically implemented, define its actual operands, parameters, domains, state changes and executable equation. The current symbolic workbench does not itself supply a numerical law merely by naming an operator.

Create a versioned numerical profile covering:

- Klein surface representation, chart/sheet identity, local orientation, distance/field interpretation, and return/transport. Preserve the intended topology rather than silently substituting a torus, sphere or ordinary grid field.
- PHI encoding, log base, radius domain and angular representation.
- Hinge/pinion action, the colon product, primitive fields, phase differential, phyllotaxis and blend.
- The RK4 derivative and the exact meaning/order of the two fourth-slot Y-up actions.
- PSI and reproducible jitter generation, operator body/field/position mutation, and whether mutations consume local state or shared reductions.
- The selected meaning and representation of T, its inverse, and the RGBA/B-history semantics. A matrix inverse needs a matrix or a defined encoding; do not silently replace it by scalar opacity clipping.

For a missing source equation, write a concrete proposed binding and a test fixture in the profile, and identify the decision needing author review. Continue building the probe, layout, runtime and test harness while decisions are reviewed. Do not conceal unbound operators behind no-ops or claim symbolic tags are numerical execution.

## Preserve self-reference in device memory

Represent operators as mutable, typed records with their executable expression/bytecode body, SDF parameters and surface placement. Use an extensible intermediate representation. The compiled compute interpreter evaluates the records; changing the records changes later computation. Do not attempt to overwrite native GPU instruction memory during execution.

Use the v0.2 mutation-before-application order unless an explicit profile revision changes it. A starting schedule is:

```text
Read state[n] and operators[n].
Pass A: compute operators[next] from that old snapshot and jitter[n].
GPU write-to-read dependency.
Pass B: evaluate the full Dawnwood cycle using state[n] and operators[next].
        Write state[next], including the declared history and return state.
GPU dependency before the next interval.
Exchange current/next resource roles.
Optionally evaluate downstream output from the completed state.
```

Use one writer per output operator/state record where the profile permits it. Add explicitly ordered reductions or further passes when a mutation depends on shared/global state. Packed bits require word ownership or suitable atomics; two independent bit indices can still share one machine word. Never treat a workgroup barrier as device-wide synchronization. [R8]

Separate compute passes are an execution schedule for one recurrence, not separate behavioral models. Batch a finite number of intervals per submission and keep the state alive between submissions. Stopping/resuming must preserve the next logical interval and jitter state. Do not reset the state at presentation boundaries.

## Memory and execution design

Start with ordinary GPU storage buffers for live numerical state, mutable operator records, routes and flags. Keep bit controls packed, but account separately for coordinates, amplitudes, inverse-T data, operator bodies, indices and history. All layout sizes must include alignment and both current/next buffers.

BC5 and other compressed texture schemes are a later, explicitly tested path for suitable sampled data, not a mandatory representation for mutable executable records. Query format/usage support on each target. Do not assume the phone has the same texture formats as the laptop.

The numerical runtime should not append an entire symbolic execution trace to device memory at every interval. Keep the symbolic trace as an optional diagnostic. However, do not discard mathematically relevant history: define sufficient live state, retain history required by the selected B/feedback binding, and garbage-collect only records proven unreachable. Make any history-window approximation an explicit profile choice.

Use reported budgets, configured headroom and allocation failure handling. Support segmented buffers when a useful working set exceeds a single storage-buffer binding range. Scale workload size separately from the equations. Begin with a small regression fixture, then a proposed 65,536-state trial. These are test sizes, not limits on the definition. Record Android thermal status and sustained behavior instead of reporting only a short cold-start burst. [R4]

## Acceptance tests

Implement and run these layers, recording them separately:

1. Structural compatibility: source vector [0,2,0,1], source parity fixtures, implicit child relation 2i+1+b, route/reversal examples, catalogue coverage and cycle order.
2. Numerical operator tests: each selected binding has scalar/vector fixtures, domain tests and an independently checkable expected result. Every required source operator has an active execution path.
3. Self-reference tests: mutate a body/field/location, apply the next step, and demonstrate a corresponding numerical result change. Check that updates use the intended old/new snapshots and that previous-state feedback is consumed.
4. CPU versus GPU comparison: exact equality for integer-only operations; declared absolute/relative tolerances for float32. Compare each stage and report the first divergent interval. Floating-point-derived branch disagreements are diagnostic failures to investigate, not automatically acceptable merely because scalar error is small.
5. Topology tests: seam/return behavior, local-frame transport and sheet identity according to the chosen binding. Do not merge paths simply because their displayed 3D positions coincide.
6. Replay, checkpoint/resume, explicit jitter streams and optional readout independence. Do not require bit-identical numerical hashes across distinct GPU architectures unless the arithmetic policy actually guarantees them.
7. Execution tests: non-multiple workgroup sizes, packed-word collisions, different supported workgroup sizes, segmented buffers and allocation failure. Enable available Vulkan validation during development.
8. Real-device sessions: laptop and phone each report selected device, driver, profile, numerical errors, memory use, completed intervals, host timings, GPU timings when supported, and sustained throughput. Include shader compilation and APK installation logs separately from execution evidence.

Mark a target `NOT RUN` if the environment cannot access it. Keep compilation, emulated execution, actual NVIDIA execution and actual Mali execution as different statuses. Retain raw logs and commands; never infer a device pass from a successful build.

## Deliverables and development order

Deliver a device probe; the explicit numerical profile and fixtures; a CPU numerical reference; Vulkan shaders and host runtime; a desktop CLI; an Android debug APK and build project; deterministic test runners; checkpoint/export support; and machine-readable actual-device reports.

First make one numerically specified PSI interval agree on CPU and laptop GPU. Then execute that same profile on the phone. After correctness, optimize memory layout, dispatch fusion, local/shared-memory use and numeric packing without changing the declared recurrence.

Codex can be run locally in the extracted repository to edit code and invoke installed tools. For physical-device tests, its execution environment must actually have the NVIDIA driver and/or the authorized ADB connection. [R9]

## References checked for this brief

[R1] Dell G3 15 3500 specifications, discrete GPU configurations:
https://www.dell.com/support/manuals/nl-nl/g-series-15-3500-laptop/dell-g3-15-3500-setup-and-specifications/gpu-afzonderlijk?guid=guid-ffe6a8f0-b956-4d30-b696-a897ef21cf69&lang=nl-nl

[R2] NVIDIA Vulkan driver support, supported notebook GPUs:
https://developer.nvidia.com/vulkan-driver

[R3] Xiaomi POCO X7 Pro official specifications:
https://www.mi.com/global/product/poco-x7-pro/specs/

[R4] Khronos Vulkan documentation, Compute on Android:
https://docs.vulkan.org/tutorial/latest/Advanced_Vulkan_Compute/12_Mobile_and_Embedded_Compute/02_android_compute.html

[R5] NVIDIA System Management Interface documentation:
https://docs.nvidia.com/deploy/nvidia-smi/index.html

[R6] Android Debug Bridge documentation:
https://developer.android.com/tools/adb

[R7] Android NDK, Get started with Vulkan:
https://developer.android.com/ndk/guides/graphics/getting-started

[R8] Khronos Vulkan synchronization examples:
https://docs.vulkan.org/guide/latest/synchronization_examples.html

[R9] OpenAI Codex CLI documentation (official documentation redirects to ChatGPT Learn):
https://developers.openai.com/codex/cli/
