# Dawnwood Interactive — RTX 5070 Ti texture kernel
## Current integer edition 1 / v0.4

The document's computational architecture now has a complete **integer numerical
implementation**, including signed supports, Klein folding, Hadamard mixing,
phase/dot coupling, the fourth-slot RK4 events, inverse phase words, history,
mutable operator programs and the VRAM feedback chain. Numerical rules missing
from the source are recorded in [the integer binding](model/integer_binding.json).

Start with the measured optimized build:

```powershell
.\scripts\build_windows.ps1
.\build\dawnwood_integer_cached.exe --self-test
.\build\dawnwood_integer_cached.exe --codec bc5 --pages 32 --page-side 2048 `
  --blocks-per-step 65536 --steps 256 --batch 32 --report work\integer.json
```

On this RTX 5070 Ti Laptop, three repeated larger-field runs measured **6.86
billion BC5 pair updates/s** and **5.86 billion RG8 pair updates/s**, respectively
**3.37x and 2.51x** the direct-SDF integer reference at the same balanced cache
preference. The optional `--cache-policy l1` reached 7.22 and 5.97 billion in this
workload. The compact 4,004-byte alternatives remain available; the faster build
adds an exhaustively verified 64 KiB integer pair table, for **69,540 hot data
bytes**, read through real integer texture lookups.

**Quantum-style mechanism evidence:** raw integer Hadamard-squared minimum
normalized fidelity is 0.999985 across 65,280 nonzero input pairs. The complete
LP8-encoded path is much less reliable at radial-wrap boundaries. This edition
implements the source mechanisms as a classical finite numerical machine; it
does not establish a general entangled-state quantum simulator. The report
separates interference accuracy, amplitude loss, execution speed and capacity.

Read the new [integer formalization PDF](output/pdf/Dawnwood_Interactive_Integer_Formalization.pdf),
[measured edition guide](docs/INTEGER_EDITION.md), and
[literal source requirements](docs/INTEGER_REQUIREMENTS.md).
Current evidence is [results/integer/final_summary.json](results/integer/final_summary.json).
Snapshots use version 4 and reject the historical floating version 3.
Native BC5 retains its sampler interface; the compiled audit explicitly records
that boundary and compiler constant-only HFMA2 instructions. It is not a claim
of zero floating opcodes anywhere in the GPU.

## Historical floating substrate binding v0.3

**Tom Klootwijk · NL200678942 · 10-07-1990**

A CUDA/C++17 kernel package for the **GeForce RTX 5070 Ti Laptop GPU, 12 GB**.
It runs the double-pinion / Hadamard / log-polar / Klein / SDF-operator / one-bit
BST / Ψ feedback circulation as one evolving device field. The original
`source/double-slit-theory.pdf` is included unchanged.

The delivered code contains real CUDA texture objects and surface writes, a
packed operator interpreter, an automatic VRAM-capacity allocator, chained
texture reads, and executable operator-body mutation. **The optimized v0.3 was
compiled and measured on the RTX 5070 Ti Laptop GPU on 2026-09-16.** Against the
reference build's original L1 preference, the larger-field median circulation
speedup was **3.56× for BC5 and 3.13× for RG8**. With both builds using the same
balanced preference, the kernel changes alone delivered **1.32× and 1.30×**.
Both comparisons used five alternating trials with the same recurrence inputs.
Three alternating trials on approximately **7.9 GiB fields with allocation
headroom** measured **3.89× BC5 and 3.34× RG8** under the respective defaults.

Full small-field snapshots matched between builds; GPU self-tests and Compute
Sanitizer checks passed. Automatic capacity runs stored **7.52 billion BC5 token
pairs** or **4.51 billion RG8 pairs**, covering the entire field at least once.
These are storage/update measurements. They do not validate physical double-slit
behavior: the implemented LP8 recurrence does not preserve physical wave energy.

Read [optimization, measurements and reproduction](docs/OPTIMIZATION.md), the
[source and theory audit](results/optimization/THEORY_AUDIT.md), and the
[formalization and ELI5 performance PDF](output/pdf/Dawnwood_Interactive_Optimized_Formalization.pdf).
The authoritative new evidence is in `results/optimization/`.
`results/VALIDATION.json` records the original delivery only; its statement that
native CUDA had not run describes that earlier environment.

## Build and run on Windows

Install CUDA Toolkit **12.8 or later**, CMake **3.24 or later**, and Visual Studio
2022 with its C++ tools and CUDA integration. Use a driver that supports the
installed toolkit. The default CUDA build includes `sm_120` machine-code and
`compute_120` PTX targets. Hardware references are in `docs/SOURCES.md` [N1,N6].

From a Visual Studio Developer PowerShell, in the extracted folder:

```powershell
.\scripts\build_windows.ps1
.\build\Release\dawnwood.exe --probe
.\build\Release\dawnwood.exe --self-test
```

The build also produces `dawnwood_reference.exe`, which retains the original
computation and L1 preference while sharing the required BC5 texture-view
compatibility fix. Both use the v0.3 operator and snapshot formats. The measured
session used the Ninja generator and therefore placed executables directly in
`build\`; use the executable paths produced by your selected generator.

Run the complete small-field GPU acceptance sequence:

```powershell
python tools\gpu_acceptance.py build\Release\dawnwood.exe --out work\acceptance_01
python tools\benchmark_optimization.py build\Release\dawnwood_reference.exe build\Release\dawnwood.exe --out work\optimization_01
```

After the native self-test succeeds, start the packed field at near-capacity:

```powershell
.\build\Release\dawnwood.exe --codec bc5 --fill 0.90 --reserve-mib 1024 --steps 8192 --batch 32 --report work\rtx5070ti.json
```

This bounded command leaves headroom for the desktop. Confirm
`complete_sweeps_this_run >= 1` in its report. The more aggressive measured
`--fill 0.98 --reserve-mib 256` allocation succeeded individually but a later
fixed-page repeat ran out of memory; concurrent desktop memory use can change
capacity. A separate repeat at 75% of those page counts completed successfully.
See the optimization notes for the retained evidence.

`--steps 0` continues until Ctrl+C if an ongoing run is wanted. The launch
batch ends before the final report and operator image are written. Run
`--help` for every switch. The available memory reported by the device—not a
hard-coded 12 GB—is used to size the field. Allocations are in whole pages.

The main run report includes observed allocation/free-byte figures, completed
Ψ intervals, block coverage, token update rate, codec error, and the final
operator-image digest. It does **not** substitute an estimated cache-hit rate
or nominal bandwidth for a measurement.

## Linux

```bash
bash scripts/build_linux.sh
./build/dawnwood --probe
./build/dawnwood --self-test
python3 tools/gpu_acceptance.py build/dawnwood --out work/acceptance_01
python3 tools/benchmark_optimization.py build/dawnwood_reference build/dawnwood --out work/optimization_01
./build/dawnwood --codec bc5 --fill 0.90 --reserve-mib 1024 --steps 8192 --batch 32 --report work/rtx5070ti.json
```

## The circulating field

```text
GPU-owned Ψ / cursor / seed
       |
       v
packed texture pages -> data-selected chain reads -> implicit one-bit BST
       ^                                           |
       |                                           v
  surface commit <- RG + B/A <- double pinion / Hadamard / RK4 / SDF bodies
       |                                           |
       +--------------- field feedback ------------+
                               |
                               v
                  mutate body words, references,
                  support, placement and routing
                               |
                               +----> next Ψ
```

`src/kernels.cuh` contains the actual device kernels. `src/main.cu` allocates
and binds the texture pages, requests cache policy, records/replays the CUDA
Graph, and manages explicit exports. `include/dawnwood/core.hpp` contains the
shared CPU/GPU representation and numerical operators.

**Hot working set:** 31 operator records × 64 bytes, plus a 256-entry × 16-byte
log-polar decode LUT: **6,080 bytes per CUDA thread block** in shared memory.
Operators are loaded through texture objects; the hot backing allocation also
receives an L2 persistence preference when the device permits it. Texture cache
retention is a hardware policy, not a permanent cache lock [N2,N3,N4].
The optimized kernel additionally builds a **1 MiB table of all 65,536 LP8
input-pair transforms** on the same GPU. Evolving chart offsets are applied after
the lookup. This avoids repeating the immutable logarithm/angle calculation;
the table is runtime data and does not change the snapshot format.

`--cache-policy l1|balanced|shared` selects a hardware preference. The optimized
default is `balanced`; the reference default is `l1`. Cache preference affects
scheduling and storage partitioning, not the definition of a Ψ update. Use the
benchmark's two cache-policy overrides to compare both builds at one preference.

**Packed VRAM field:** BC5 R/G texture blocks plus separate exact B-history and
A-inverse-T words. Every allocated page is initialized with field data, is
available to the chain, and lies on the rolling update sweep. There are no
padding-only payload allocations used to inflate the VRAM figure.

**Self-reference:** live operator records contain eight executable words,
operator references, an SDF support, and a surface position. A device mutation
step uses field results and prior operator state to change these records. The
next Ψ executes the changed bodies. The interpreter's words mutate; NVIDIA's
loaded machine-code kernel is not rewritten.

The original document leaves numerical bindings open. This edition supplies
an explicit, editable binding for those positions; its exact equations and
formats are in `docs/NATIVE_BINDING.md`, with page-by-page source correspondence
in `docs/SOURCE_MAP.md`. No unspecified numerical equation is presented as a
quotation from the source.

## Storage modes and capacity

| Mode | Dichromatic storage per 16 token pairs | B/A per 16 pairs | Total per pair |
|---|---:|---:|---:|
| `bc5` | 16 bytes | 8 bytes | 1.5 bytes |
| `rg8` | 32 bytes | 8 bytes | 2.5 bytes |

These are this implementation's payload totals. Operator banks, page handles,
staging, array padding and runtime resources are additional. At the default
4096 × 4096 page side, BC5 pages have **24 MiB** of payload; RG8 pages have
**40 MiB**. There is no second full-size atlas. A 64-byte staging record is used
only for each block in the current update window.

BC5 is a lossy encoding of token bytes. `rg8` preserves those bytes exactly;
both modes use the same LP8 geometry quantization and recurrence. B/A and
executable words are never stored in BC5. Use the exact mode to distinguish
recurrence effects from BC5 compression effects:

```powershell
.\build\Release\dawnwood.exe --codec rg8 --pages 4 --steps 128 --report work\exact.json
```

The allocator uses:

```text
budget = min(current_free_bytes * fill, current_free_bytes - reserve_bytes)
```

`--fill 1 --reserve-mib 0` is available for an explicit maximum-allocation
attempt. Driver and launch resources still need memory. The bounded command
above keeps at least 1 GiB of headroom; the existing continuous saturation
scripts request 256 MiB. Changing the memory budget does not change
an operator law, disable mutation, or clip a geometric radius.

## Edit the running definition

The supplied `model/operators.json` and `model/operators.bin` encode the same
initial 31-record catalogue. Edit JSON instructions, pack the image, then load
it at startup:

```powershell
python tools\operator_image.py pack model\operators.json work\custom.bin
.\build\Release\dawnwood.exe --operators work\custom.bin --pages 4 --steps 128 --report work\custom.json
```

Every completed run also writes a sibling `*.operators.bin` file. Decode that
file to inspect what the field changed:

```powershell
python tools\operator_image.py dump work\custom.operators.bin work\evolved.json
```

For controlled comparisons use `--freeze-operators`, `--no-jitter`, `--hops 0`,
or `--inverse-gain 0`. These are explicit experiment switches, not automatic
interventions in the recurrence.

## Save and continue

A full snapshot stores all packed textures, B/A planes, both operator banks,
and the GPU-owned circulation state. It can be many gigabytes. Snapshot
transfer happens only when explicitly requested, outside the circulation.

```powershell
.\build\Release\dawnwood.exe --pages 4 --steps 128 --snapshot work\session.snapshot --report work\session.json
.\build\Release\dawnwood.exe --resume work\session.snapshot --steps 128 --report work\continued.json
```

Resume retains the stored codec, dimensions, seed, Ψ interval and update-window
size; `--steps` specifies additional intervals. Choose a new snapshot filename
for each export. Runtime texture handles are recreated, not serialized.

## Tests without a GPU

```bash
cmake -S . -B build-cpu -DDW_ENABLE_CUDA=OFF -DCMAKE_BUILD_TYPE=Release
cmake --build build-cpu --config Release
ctest --test-dir build-cpu -C Release --output-on-failure
python -m unittest discover -s tests -p "test_*.py" -v
python tools/verify_manifest.py
```

The delivered checks cover packed words, SDF primitives, Klein seam identities,
LP8 round trips, one-bit body mutation, reproducibility, sweep coverage, codec
error and allocation arithmetic. New optimization checks exhaust the BC4
endpoint/selector domain and all LP8 pairs, and compare fused codec errors and
cached recurrence stages. `tools/gpu_acceptance.py` checks hardware texture
decoding, write/read coherence and full snapshot continuation.
`tools/benchmark_optimization.py` adds complete snapshot hashes across optimized,
reference and graph/sequential executions plus repeated timing reports.
[The optimization record](docs/OPTIMIZATION.md) describes the executed checks;
`docs/CODEX_HANDOFF.md` retains the original development handoff.

This archive and the run reports include your supplied personal attribution.
