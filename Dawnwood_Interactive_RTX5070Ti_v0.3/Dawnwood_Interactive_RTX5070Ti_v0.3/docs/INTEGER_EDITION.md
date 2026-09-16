# Dawnwood Interactive: measured integer edition

This edition runs the source architecture as an explicit finite numerical law.
It does not simply pack the earlier floating kernel. The original PDF and v0.3
implementation remain available. `model/integer_binding.json` specifies choices
that the PDF leaves open; `INTEGER_REQUIREMENTS.md` maps the source components.

## What works, and what the quantum probes mean

The actual integer primitives produce constructive/destructive interference,
exact antipodal cancellation, Hadamard mixing and phase-dependent two-port
interference. Across all 65,280 nonzero LP8 input pairs, the normalized overlap
after H twice has minimum fidelity **0.9999850671** and median **1** before LP8
re-encoding. This is a component calculation using the implementation's Q11
complex vectors and quantized Hadamard coefficient.

Packing changes the answer. With LP8 between and after the two transforms,
minimum fidelity is **0.0169163** and median **0.9974364**. Even the subset with
no radial wrap has a minimum of **0.9479598**. Norm ratios are reported alongside
normalized overlap because normalization can conceal amplification or loss.
For equal-amplitude phase scans, the middle radial band has a maximum encoded
probability error of about **3.54 percentage points**; extreme bands reach about
**96.1 points**. Perfect dark ports/visibility alone do not establish fidelity.

These results support digital interference experiments and study of this
particular nonlinear feedback machine. They do not demonstrate accurate general
quantum circuits. The runtime has no explicit tensor-product entanglement or
Born measurement transition. The normalized probabilities in the diagnostics
are readout calculations, not a newly inserted measurement law. No physical
double-slit apparatus, wavelength/aperture propagation model or quantum advantage
is inferred from the architecture or its speed.

Reproducible data: `results/integer/quantum_mechanism_checks.json` and
`theory_diagnostics.json`. Both retain diagnostic scope and build information.

## Runtime and optimization

Each interval reads the old field and operator bank, stages each selected block,
commits the field, mutates operator words and locations, rebuilds exact SDF sign
predicates, then advances the device-owned clock. Kernel boundaries establish
texture visibility. No same-kernel texture-read/surface-write coherence is
assumed. Graph and sequential launch modes execute the same ordered stages.

The math table is 1,540 bytes; 31 operators occupy 1,984 bytes; 15 nodes times
256 support predicates occupy 480 bytes. Full signed Q18 support functions
remain available. The optimized predicate compiler uses squared distances,
strict box interiors and triangle cross products, avoiding unnecessary roots
and segment projections. It agrees with the complete signed support law in
187,164 tested cases, with 3,598 additional boundary/coverage assertions.

The faster build adds 8,192 eight-byte cached Hadamard charts. Exact quarter-turn
and reflection symmetries reduce a full pair table to 64 KiB. The difference
output is the sum output with the second input phase inverted. Every pair,
both outputs and eight offset scenarios match the original integer law;
all 65,536 GPU texture entries also match direct GPU mathematics. No phase
corrections were needed. Total logical hot data is 69,540 bytes; allocated
hot arenas, second banks, code, driver resources, stacks and staging are separate.

| Executable | Purpose |
|---|---|
| `dawnwood_integer_cached` | Recommended: direct integer textures plus exact 64 KiB pair cache |
| `dawnwood_integer_reference` | Same integer law with direct signed-SDF evaluation and no pair cache |
| `dawnwood_integer` | Compact shared-memory math/operators and predicate cache |
| `dawnwood_integer_texture` | Compact direct-texture math/operators and predicate cache |

The compact predicate-cache variants are **slower** than the integer reference
in measured runs. Smaller data and fewer source-level calculations did not
guarantee better compiled execution. They are retained as measured comparison
paths, not advertised as improvements. The exact pair-cache build is the winner.

## Performance in plain language

The larger workload stores 134,217,728 token pairs across 32 pages of side 2048.
Each interval updates 65,536 blocks, or 1,048,576 pairs. Three rotated trials
follow one excluded warmup; each trial runs 256 intervals in batches of 32.
Seed=756, dt=1024 Q16, inverse gain=16384 Q16, two hops, mutation and jitter on.

| Codec / balanced preference | Reference ms | Cached ms | Speedup | Cached billion pair updates/s |
|---|---:|---:|---:|---:|
| BC5 | 132.04 | 39.15 | 3.37x | 6.86 |
| RG8 | 114.98 | 45.78 | 2.51x | 5.86 |

Times cover circulation and launch/synchronization gaps, excluding allocation,
initialization, snapshot export and reports. Full-process times are also saved.
Clocks were not locked. The source law differs from the historical float law,
so those old timing results are not the denominator in these speedups.

For BC5, 39.15 ms covers two full sweeps of this 134-million-pair field: an
equivalent mean sweep is about **19.6 ms**, and an interval averages **0.153 ms**.
These are field-computation metrics, not rendered frames or quantum gate counts.
RG8's corresponding mean sweep is about **22.9 ms**. BC5 and RG8 can follow
different trajectories because BC5 compresses the tokens lossily.

The L1 preference measured 7.22 billion BC5 and 5.97 billion RG8 updates/s in
this larger workload. The default remains balanced; choose `--cache-policy l1`
to reproduce that tuning comparison. In profiling, cached L1/TEX hit rate rose
from 72.38% balanced to 85.47% with L1 preference. Those counters include all
evolve traffic, not just LUT accesses, and do not guarantee cache residency.
The balanced cached evolve samples used about 12.43% of peak DRAM throughput:
the run did **not** saturate DRAM bandwidth.

## VRAM and correctness

Automatic allocation with fill=0.92 and a 768 MiB reserve exercised **9.891 GiB
BC5** (7.080 billion stored pairs) and **9.883 GiB RG8** (4.245 billion pairs).
Both were initialized and traversed completely; the runs completed one and two
whole sweeps respectively. This is tested capacity with desktop headroom, not
a claim of maximum allocatable memory or permanently pinned physical residency.

Validation passes include 46 complete-state/rejection comparisons across four
variants and both codecs, graph/sequential equivalence, partial windows and
cross-variant snapshot continuation. All 12 CTest checks and 27 Python checks
pass. Eight Compute Sanitizer runs cover memory, race, synchronization and
initialization checks in both codecs. Native BC5 decoding is checked separately
from exact subsequent integer recurrence; RG8 byte reads are exact.

The actual executables' PTX and SASS pass the arithmetic audit. Explicit
exceptions are the native float-typed sampler/bit-transfer interface and
`HFMA2 dst,-RZ,RZ,literal,literal` instructions used by the compiler only to
materialize constants. No state-dependent floating arithmetic, conversions or
reciprocal SFU operations were found. This is not a zero-floating-opcode claim.

## Reproduce

```powershell
.\scripts\build_windows.ps1
ctest --test-dir build --output-on-failure
python tools\measure_integer.py --mode validate --include-cached --out work\verify
python tools\measure_integer.py --mode bench --include-cached --include-l1 `
  --pages 32 --page-side 2048 --blocks-per-step 65536 --steps 256 --out work\bench
python tools\audit_integer_build.py
python tools\profile_integer.py
python tools\sanitize_integer.py
python tools\capacity_integer.py
python tools\summarize_integer.py
python tools\build_integer_pdf.py
```

The report builder requires ReportLab; the bundled document Python provides it.
Snapshot v4 is distinct from v3. Operator images remain editable packed data;
loading an old operator image supplies integer words but does not reproduce the
historical floating numerical trajectory. Detailed evidence and exact commands
are in `results/integer/final_summary.json` and its linked run directories.
