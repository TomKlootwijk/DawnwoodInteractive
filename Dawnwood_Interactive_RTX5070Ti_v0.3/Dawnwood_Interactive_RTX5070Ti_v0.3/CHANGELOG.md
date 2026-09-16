# Dawnwood Interactive — v0.4 / integer edition 1

Tom Klootwijk · NL200678942 · 10-07-1990

## 2026-09-16 — complete integer numerical edition

- Added an explicit integer law for the entire operator/field recurrence,
  including signed geometric supports, Klein folding, log/phase encoding,
  Hadamard/dot coupling, forced RK4 stages, inverse phase words and mutation.
- Added compact shared and direct-texture paths, a direct-SDF integer reference,
  and the recommended exact D4 pair-cache path. The 64 KiB symmetry cache and
  exact sign specialization preserve the new integer law; this is a different
  numerical binding from historical floating v0.3.
- Measured 3.37x BC5 / 2.51x RG8 circulation speedup over the integer reference
  at the same balanced preference on the larger field. Exercised approximately
  9.9 GiB fields in both formats with complete sweep coverage.
- Added v4 snapshots, Q16 CLI controls, complete-state comparisons, native GPU
  math/cache checks, sanitizer runs and actual-executable PTX/SASS audits.
  Native sampling and compiler constant-materialization exceptions are explicit.
- Added quantum-style interference/reversibility diagnostics that separate raw
  integer algebra from LP8 amplitude/fidelity loss. Updated source requirements,
  numerical manifest and a new PDF with measured performance and ELI5 metrics.
- Historical executables, source PDF, results and formalization remain available.

## 2026-09-16 — measured kernel optimization, v0.3 ABI retained

- Fixed CUDA BC5 texture creation: the unsigned block-compressed resource view
  supplies normalized decoding, while its uint4 backing array requires element
  read mode. RG8 retains normalized-float reads. This compatibility fix is in
  both optimized and reference builds.
- Added a GPU-generated 1 MiB LP8 pair-transform cache, exact BC4 threshold
  selection with fused error accounting, bounded integer/address simplifications,
  and warp reduction for commit error totals. Ordered evolution, commit,
  operator mutation and cursor advance remain separate kernels. Operator-image,
  field, staging and snapshot formats remain v0.3.
- Added a reference executable and explicit cache-policy controls. The optimized
  default is balanced; the reference retains L1 preference. Five-trial larger-field
  CUDA-event medians improve by 3.56× BC5 / 3.13× RG8 with those defaults and
  1.32× / 1.30× with both builds balanced. These are observed workstation results,
  not guaranteed rates on other devices or thermal conditions.
- Verified complete small-field snapshot equality, GPU decoding and pair-cache
  checks, continuation, CPU tests, and zero reported memcheck/racecheck/synccheck
  errors for exercised BC5/RG8 cases. Added reproducible alternating benchmarks
  with hashes, commands and dispersion.
- Measured automatic near-capacity storage and complete sweep coverage for
  448 BC5 pages and 269 RG8 pages. Preserved the subsequent fixed-page repetition
  failure at explicit device allocation; allocation success is not bandwidth
  saturation or a persistent cache lock.
- Completed three alternating trials on 336 BC5 / 201 RG8 pages, approximately
  7.9 GiB payload with allocation margin: 3.89× / 3.34× default-policy speedups.
  The capacity helper now defaults to 75% of recorded maximum pages, supports
  both Windows build layouts and pauses between processes for allocation release.
- Added the source/theory audit and
  [formalization/performance PDF](output/pdf/Dawnwood_Interactive_Optimized_Formalization.pdf).
  The finite self-referential recurrence implements the chosen source binding;
  it does not establish quantum double-slit physics or norm-preserving wave
  evolution. See [the measured optimization record](docs/OPTIMIZATION.md).

Current native evidence is in `results/optimization/`. The older
`results/VALIDATION.json` is retained as an original-delivery record.

## Original v0.3 delivery

The v0.2 unified symbolic workbench is followed by an explicit native numerical
binding: packed CUDA BC5/RG8 texture fields, device-owned circulation, mutable
operator words and SDF supports, a shared-memory hot set, requested L2 policy,
automatic capacity packing, chained reads, ordered commits and complete snapshots.

`docs/NATIVE_BINDING.md` defines the executable choices and
`docs/SOURCE_MAP.md` connects them to the original 24-page source. The exact
validation performed for this release is recorded in `results/VALIDATION.json`.
