# Hardware binding and measurements

The RTX 5070 Ti Laptop GPU is listed with 12 GB GDDR7; the RTX 5070 Ti family
is listed at compute capability 12.0 [N1]. The program queries the actual
selected device rather than assuming cache sizes, SM count or free VRAM.

## The three storage layers

The **VRAM field** is allocated with CUDA arrays plus `cudaMalloc` auxiliary
planes. No `cudaMallocManaged` allocation or CPU page-in/page-out routine is
used. Allocation, initialization and optional snapshot export are distinct
from circulation.

The **texture path** uses actual `cudaTextureObject_t` handles. BC5 is a
`cudaResViewFormatUnsignedBlockCompressed5` view over a uint4 CUDA array whose
physical width/height are one quarter of the logical texture dimensions. RG8
uses an unsigned two-byte channel array. Both use point sampling; the storage
layout is not a rendered surface [N2].

The **hot working set** is copied into 6080 bytes of shared memory per thread
block while its evaluation kernel runs. Backing operator banks and the LUT
receive a requested L2 persistence preference. These are cache-use controls,
not a promise that every byte remains in L1/texture cache indefinitely [N3].

## Coherent self-reference

Evaluation reads texture state and writes staging memory. A separate kernel
commits surface writes. A subsequent kernel mutates the next operator bank.
The next evaluation occurs after these dependencies. This arrangement follows
the documented texture/surface coherence boundary between kernel calls [N4].
An indefinitely running kernel that reads and overwrites the same texture
address would not provide that documented behavior merely by inserting a
thread-block barrier.

## What the report means

`payload_bytes` counts this program's texture and exact B/A bytes. It does not
include runtime resources or claim that other applications' allocations belong
to Dawnwood. `free_after_packing` is a `cudaMemGetInfo` observation. CUDA/driver
array padding may make the free-memory change differ from payload arithmetic.

`token_pair_updates_per_second` is a measured application update rate. It is
not raw DRAM bandwidth. Event elapsed time includes gaps between submitted
batches; it is not the sum of isolated kernel timings. Cache hit rates, actual
DRAM traffic and physical-residency behavior are profiling questions, not
values that can be inferred from the allocated byte total.

The application does not expose a mechanism to force OS-level permanent
residency or to lock the complete VRAM field into on-chip cache. It reports the
allocation and cache preferences it actually requests. Filling capacity and
saturating memory bandwidth are separate experiments.

## Profiling on the laptop

`compute-sanitizer` can check memory accesses, shared-memory races and
synchronization behavior [N5]. Run the delivered native self-test and small
acceptance sequence before the capacity experiment. The Linux profiling script
also records an Nsight Compute report; on Windows use the corresponding
installed command-line tools with `build\Release\dawnwood.exe`.

No script changes GPU clocks, voltage, firmware, driver watchdog settings or
system graphics policy. Runtime knobs select page capacity, update window,
chain hops and experiment variants. A smaller update window shortens each
launch but also changes the per-Ψ scheduling, as specified in NATIVE_BINDING.
