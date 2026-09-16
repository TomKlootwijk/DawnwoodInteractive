# Measured v0.3 optimization

Measured on 2026-09-16 with an NVIDIA GeForce RTX 5070 Ti Laptop GPU, compute
capability 12.0, CUDA Toolkit 12.8.61 and MSVC 19.44. The device reports
12,820,480,000 bytes total memory and 36 MiB L2. Compilation, raw timings,
snapshots, profiler captures and sanitizer logs are retained in
[`results/optimization/`](../results/optimization/). The original
[`results/VALIDATION.json`](../results/VALIDATION.json) predates this hardware
session and describes the original delivery only.

The [formalization and ELI5 performance report](../output/pdf/Dawnwood_Interactive_Optimized_Formalization.pdf)
contains the mathematical interpretation. The
[source/theory audit](../results/optimization/THEORY_AUDIT.md) distinguishes source
requirements, implementation choices and unsupported physical claims.

## What changed, and what equality means

Both executables now create the BC5 view successfully on the actual GPU. The
initial native self-test failed because normalized-float read mode was applied
to the uint4 backing array. BC5 normalization belongs to its compressed resource
view, so BC5 now uses element read mode; RG8 keeps normalized-float read mode.
The reference includes this compatibility repair. A non-running original build
is not a meaningful timing baseline.

The optimized path makes four principal changes:

1. A 1 MiB table caches all 65,536 immutable LP8 input-pair chart transforms.
   It is generated on the same GPU using the same LUT and floating-point policy.
   Mutable offsets and feedback still execute each interval; exact zero retains
   its existing special handling.
2. BC4 palette thresholds choose the same selector, including tie behavior,
   while the selected palette value supplies the compression-error total in the
   same pass. The stored BC5 bytes remain identical for the tested domain.
3. Integer operations use narrower arithmetic only where bounds establish that
   results fit. Valid rolling windows use conditional wrap; power-of-two texture
   dimensions use shifts/masks, with a general-dimension fallback.
4. Commit error totals use warp shuffles and a small shared reduction. All lanes
   participate, including partial windows; the global total remains 64-bit.

The optimized default cache preference is `balanced`; the reference keeps `l1`.
This changed the measured resource balance substantially: register use fell
from 100 to 61 per evolve thread, and the reported theoretical active-block
limit rose from one to eight per SM under the respective defaults. These are
resource/occupancy observations, not an eightfold performance claim. The
explicit `--cache-policy` flag can select `l1`, `balanced` or `shared` on either
build.

The 31-record operator image, each 64-byte operator, BC5/RG8 payload layout,
8-byte per-block B/A state, 64-byte staging record and v0.3 snapshot ABI remain
unchanged. The pair cache and CUDA handles are reconstructed runtime resources,
not serialized field state. Evolution reads the committed field; a separate
commit publishes the active window before operator mutation and cursor advance.
The forced fourth RK slot, LP8 quotient, jitter law and self-mutation are retained.

Complete SHA256 snapshot equality establishes equality for the exercised inputs.
It is stronger than comparing the final 31-operator digest, but it is not a
proof for all possible future inputs, hardware or compiler versions.

## Repeated circulation measurements

All rows below use CUDA-event milliseconds, including host launch gaps. Each
row is a median of five alternating reference/optimized trials after one
excluded warmup per build. The active window is 65,536 blocks, batch is 32,
seed is 756, dt is 1/64, hops is two, inverse gain is 0.25, and mutation/jitter
are enabled. There are no snapshot exports during timed trials.

| Field / policy | Codec | Intervals | Reference ms | Optimized ms | Speedup |
|---|---|---:|---:|---:|---:|
| 2 × 1024² pages; L1 → balanced | BC5 | 1,024 | 423.244 | 112.361 | 3.767× |
| 2 × 1024² pages; L1 → balanced | RG8 | 1,024 | 458.815 | 151.821 | 3.022× |
| 32 × 2048² pages; L1 → balanced | BC5 | 2,048 | 889.475 | 249.562 | 3.564× |
| 32 × 2048² pages; L1 → balanced | RG8 | 2,048 | 989.858 | 316.742 | 3.125× |
| 32 × 2048² pages; balanced → balanced | BC5 | 2,048 | 330.002 | 249.745 | 1.321× |
| 32 × 2048² pages; balanced → balanced | RG8 | 2,048 | 411.382 | 316.750 | 1.299× |

The smaller field stores 3 MiB BC5 or 5 MiB RG8 payload. The larger field stores
192 MiB BC5 or 320 MiB RG8 payload, exceeding the device's 36 MiB L2. A 2,048-step
larger-field run performs 2,147,483,648 token-pair updates and 16 complete sweeps.
The larger default-policy runs deliver approximately **8.61 billion BC5** or
**6.78 billion RG8 token-pair updates per second** of circulation wall time.
An update is another visit to an item, not another unique stored item.

The optimized larger-field CUDA-event median absolute deviations were 0.164 ms
BC5 and 0.070 ms RG8. At matched balanced preference they were 0.106 ms and
0.213 ms. The raw reports include min/max, all samples, sample standard deviation,
paired speedups and process wall time. The large default-policy process-wall
speedups were smaller, 2.63× BC5 and 2.37× RG8, because process startup, allocation
and initialization are outside the circulation timer.

Read the source reports:
[small](../results/optimization/benchmark_small/benchmark.json),
[large](../results/optimization/benchmark_large/benchmark.json), and
[same balanced policy](../results/optimization/benchmark_balanced/benchmark.json).
Default-to-default improvement combines kernel and cache-policy changes.
The matched-policy rows isolate the additional kernel work at that preference.
Five trials describe this session's dispersion; they do not establish a
guaranteed speedup over all inputs or thermal conditions.

## VRAM capacity, cache traffic and bandwidth answer different questions

Automatic allocation with page side 4096, fill 0.98, reserve 256 MiB, 8,192
intervals, active window 65,536 and batch 32 produced these individual optimized
runs:

| Metric | BC5 | RG8 |
|---|---:|---:|
| Allocated payload pages | 448 | 269 |
| Payload bytes | 11,274,289,152 | 11,282,677,760 |
| Stored token pairs | 7,516,192,768 | 4,513,071,104 |
| Payload / total reported device memory | 87.94% | 88.01% |
| Free bytes after packing | 278,921,216 | 270,532,608 |
| Completed whole-field sweeps | 1 | 1 |
| Circulation CUDA-event time | 1,027.058 ms | 1,288.962 ms |
| Software mean absolute codec token error | 6.1217 | 0 |

Sources: [BC5 capacity](../results/optimization/capacity_bc5.json) and
[RG8 capacity](../results/optimization/capacity_rg8.json). The payload occupies
about 97.6% of the free bytes available at allocation planning; desktop/driver
allocations explain why that differs from 88% of total device memory. The actual
process allocation delta also includes overhead and array allocation granularity.
Zero RG8 codec error means exact storage of token bytes, not exact physical
amplitudes; LP8 geometry remains quantized.

The first fixed-page capacity repetition subsequently ran out of device memory
while allocating its second reference trial. Its
[failed record and completed trials](../results/optimization/benchmark_capacity/benchmark.json)
are retained. A single completed pair must not be presented as a successful
three-trial near-capacity benchmark. Capacity depends on memory available during
allocation, so retaining more headroom is appropriate for repeatable desktop use.

A separate [multi-GiB benchmark with allocation margin](../results/optimization/benchmark_capacity_margin/benchmark.json)
completed all three alternating pairs for each codec. It used 75% of the
recorded maximum page counts, 8,192 intervals and the respective default cache
policies. It did not include separate warmup processes. A one-second pause
between processes allowed allocation release and was outside the timers.

| Multi-GiB workload | BC5 | RG8 |
|---|---:|---:|
| Pages | 336 | 201 |
| Payload bytes | 8,455,716,864 | 8,430,551,040 |
| Stored token pairs | 5,637,144,576 | 3,372,220,416 |
| Whole-field sweeps per trial | 1 | 2 |
| Reference median CUDA-event ms | 4,044.542 | 4,389.660 |
| Optimized median CUDA-event ms | 1,040.322 | 1,313.309 |
| Reference / optimized speedup | 3.888× | 3.342× |
| Optimized timing median absolute deviation | 2.615 ms | 1.836 ms |
| Optimized token-pair updates / second | 8.257 billion | 6.541 billion |

This confirms improvement while evolving an approximately 7.9 GiB field with
memory headroom. It is not a completed repeated maximum-capacity test. All
reference/optimized report invariants agreed; no full-field snapshots were
exported at this scale, so equivalence evidence here is weaker than the complete
snapshot checks on small fields.

ELI5: capacity tells us how many items fit on the shelves; updates per second
tells us how quickly the worker revisits them; cache counters tell us how often
the worker finds something nearby. Filling the shelves does not establish that
the worker or the memory bus is fully occupied.

The sampled BC5 evolve kernels in
[reference](../results/optimization/ncu_reference.csv) and
[optimized](../results/optimization/ncu_optimized.csv) Nsight Compute captures
illustrate this distinction. Under the respective defaults, sampled active-warp
occupancy rose from about 8.31% to 51.6%, while L1 texture-sector hit rate fell
from about 93% to 59%. The optimized sampled kernels still finished faster.
Their DRAM-throughput counter reached roughly 8–12% of peak sustained throughput;
these samples do **not** show saturated DRAM bandwidth. The profiler explicitly
warned that GPU clocks and caches were uncontrolled. Profiling replays and these
few evolve kernels are not substitutes for the unprofiled circulation timings.
An L2 persistence request is a preference, not a cache lock or a measured hit rate.

## Executed validation and theory verdict

- [CTest](../results/optimization/ctest_final.txt): core tests, both CPU codec
  recurrences and native GPU self-test passed.
- [GPU pair-cache checks](../results/optimization/gpu_pair_checks.txt): every
  one of the 65,536 pairs at four chart offsets passed on the GPU, alongside
  native BC5/RG8 decode, commit/read, mutation and circulation checks.
- [Optimized GPU acceptance](../results/optimization/optimized_acceptance/acceptance.json)
  and [baseline GPU acceptance](../results/optimization/baseline_acceptance/acceptance.json)
  passed, including complete snapshot repeat/resume comparisons.
- The small benchmark records 20 complete-snapshot comparisons: eight
  reference/optimized cases per codec plus graph/sequential comparisons for
  each build and codec. Cases include one-block fields, page wrap, a 257-block
  partial CUDA block, frozen operators, no jitter, zero inverse gain and zero hops.
- Compute Sanitizer memcheck, racecheck and synccheck each reported zero errors
  for exercised BC5/RG8 partial-window runs; raw `sanitizer_*` logs are retained.
  CPU selector tests exhaust every endpoint pair and byte; cached stages and
  fused error calculations also have independent reference comparisons.

The source-inspired self-referential digital recurrence is present and tested.
It is not a validated physical double-slit simulator. The theory audit found
that the isolated unquantized Hadamard transform satisfies its norm identity to
float precision, but LP8 encoding changes energy substantially and can turn tiny
cancellation residuals into large decoded amplitudes. No spatial slit aperture,
wave propagation/detector protocol or experimental dataset establishes the
stronger physical claims. The optimization deliberately preserves this existing
law instead of silently replacing it with different physics.

## Reproduce the work

Use a Visual Studio 2022 developer shell with CUDA 12.8 or later. The existing
`scripts/build_windows.ps1` builds the Visual Studio configuration, producing
`build/Release/*.exe`. The measured session used Ninja, whose single-configuration
executables are in `build/*.exe`. Configure a fresh build directory if changing
generators. For example, from the project root in a developer shell:

```powershell
cmake -S . -B build-ninja -G Ninja -DCMAKE_BUILD_TYPE=Release '-DCMAKE_CUDA_ARCHITECTURES=120-real;120-virtual'
cmake --build build-ninja --parallel
ctest --test-dir build-ninja --output-on-failure
python -m unittest discover -s tests -p 'test_*.py' -v
$Ref = '.\build-ninja\dawnwood_reference.exe'
$Opt = '.\build-ninja\dawnwood.exe'
python tools\gpu_acceptance.py $Opt --out work\acceptance_01
python tools\benchmark_optimization.py $Ref $Opt --out work\benchmark_small
python tools\benchmark_optimization.py $Ref $Opt --out work\benchmark_large --pages 32 --page-side 2048 --steps 2048 --skip-equivalence
python tools\benchmark_optimization.py $Ref $Opt --out work\benchmark_balanced --pages 32 --page-side 2048 --steps 2048 --reference-cache-policy balanced --optimized-cache-policy balanced --skip-equivalence
```

The benchmark refuses existing output directories. Omit `--skip-equivalence`
whenever the executables or recurrence inputs have changed since the checked
run. Each report saves actual commands, executable hashes and environment data;
timing files and logs remain alongside it. `--no-graph` measures sequential
launches while keeping the same recurrence.

For bounded automatic capacity allocation with additional desktop headroom:

```powershell
& $Opt --codec bc5 --fill 0.90 --reserve-mib 1024 --page-side 4096 --blocks-per-step 65536 --steps 8192 --batch 32 --report work\capacity_bc5.json
& $Opt --codec rg8 --fill 0.90 --reserve-mib 1024 --page-side 4096 --blocks-per-step 65536 --steps 8192 --batch 32 --report work\capacity_rg8.json
```

Verify `complete_sweeps_this_run >= 1`; larger GPUs or smaller active windows can
need more intervals. Do not export full multi-gigabyte snapshots merely to time
capacity. The existing continuous Windows script is
`scripts/run_saturation_windows.ps1 -Report work\continuous.json`; it uses
`build/Release/dawnwood.exe`, fill 0.98, reserve 256 MiB and runs until Ctrl+C.
`scripts/run_saturation_linux.sh` is its Linux counterpart.

The multi-GiB comparison helper takes a fixed fraction of recorded maximum
page counts, leaving additional headroom for repeated desktop runs:

```powershell
python tools\capacity_benchmark.py --out work\capacity_comparison --repeats 3 --page-fraction 0.75
```

The default fraction is 0.75, rounded down to whole pages: the recorded plans
give 336 BC5 pages and 201 RG8 pages, approximately 7.9 GiB of payload. This is
a multi-GiB comparison with margin, separate from the maximum-allocation
experiment. `--page-fraction 1` attempts the original recorded maximum page
counts and reproduces the more demanding allocation conditions.

The helper finds executables directly in `build/` or in `build/Release/` and
loads the saved `results/optimization/capacity_bc5.json` / `capacity_rg8.json`
plans. It pauses one second between processes to allow WDDM to finish releasing
the preceding allocation; this pause is outside process and circulation timers.
The fixed plan does not adapt to newly occupied VRAM. Inspect the final status
and retained logs before using its results; partial runs are not completed
benchmark evidence.
