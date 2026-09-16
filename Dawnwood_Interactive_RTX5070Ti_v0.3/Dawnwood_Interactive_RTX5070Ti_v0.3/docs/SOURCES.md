# Source register

Consulted 2026-09-16. The original concept is the supplied document, not an
external replacement specification.

**[S0]** `source/double-slit-theory.pdf` — original 24-page conversation supplied
by Tom Klootwijk. Page correspondence: `SOURCE_MAP.md`.

**[S1]** `source/v0.2_open_bindings.json` — the previous unified workbench's
record of open numerical binding positions, extracted unchanged from the
provided v0.2 archive.

**[N1] NVIDIA hardware and target architecture.**
`https://www.nvidia.com/en-us/geforce/laptops/50-series/`
`https://developer.nvidia.com/cuda/gpus`
Relevant facts: RTX 5070 Ti Laptop GPU 12 GB specification; RTX 5070 Ti compute
capability 12.0. Runtime properties determine the selected device's actual
allocation capacity and cache properties.

**[N2] CUDA Runtime API — Texture Object Management.**
`https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__TEXTURE__OBJECT.html`
Relevant contract: texture objects, linear/array resources, normalized reads,
BC5 resource views over four-channel unsigned 32-bit array storage and the
4× logical view dimensions.

**[N3] CUDA Programming Guide — L2 Cache Control.**
`https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/l2-cache-control.html`
Relevant contract: persisting cache set-aside, access-policy windows, property
queries and graph-node preferences. Preference is not a cache lock.

**[N4] CUDA C++ Programming Guide 12.8 — sections 3.2.14.3–4.**
`https://docs.nvidia.com/cuda/archive/12.8.0/cuda-c-programming-guide/index.html#read-write-coherency`
Relevant contract: CUDA arrays and texture/surface read/write coherence across
kernel invocations. Also used for shared-memory and texture binding semantics.

**[N5] NVIDIA Compute Sanitizer documentation.**
`https://docs.nvidia.com/compute-sanitizer/ComputeSanitizer/index.html`
Relevant tooling: memcheck, racecheck, synccheck, error reporting.

**[N6] CUDA 12.8 Update 1 release notes and architecture compilation guidance.**
`https://docs.nvidia.com/cuda/archive/12.8.1/cuda-toolkit-release-notes/index.html`
`https://docs.nvidia.com/cuda/blackwell-compatibility-guide/index.html`
Used together with [N1] to select a CUDA >=12.8 `sm_120`/PTX build. The program
ships source and build scripts, not a hardware-tested native executable.
