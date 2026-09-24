# RTX 5070 Ti Laptop edition — 0.5.1-rtx1

This Windows runtime retains the DWI-N1-0.5 numerical definition and checkpoint
ABI. Its scheduling and storage have changed. The historical directory name
does not identify the current runtime version. Validation and final saturation
results are recorded separately in the dated RTX campaign report.

## Runtime changes

- The identified NVIDIA device (vendor `0x10de`, device `0x2f18`) defaults to
  32-lane workgroups and 1,048,576 states per evolution dispatch. Other devices
  retain 64 lanes and the 65,536-state default. `DAWNWOOD_WORKGROUP_SIZE` can
  select 32/64/128/256; `DAWNWOOD_DISPATCH_STATES` must be a workgroup multiple,
  within device limits and at most 4,194,304. Reports record both values.
- Small-population batching is capped at eight epochs and approximately
  524,288 state updates per submission (at least one epoch). Large populations
  retain one mutation per epoch, all old-state reads, and one final swap.
- Each logical state buffer can occupy two physical storage-buffer pages.
  The page capacity is the actual `maxStorageBufferRange / 128`; on this GPU it
  is 33,554,431 records. Shader specialization maps indices to the correct
  page, including mutation feedback. The population is still one connected
  recurrence. `DAWNWOOD_STATE_PAGE_RECORDS` can reduce the page size for
  diagnostics; a request exceeding two pages is rejected.
- `run --stream` generates initial state in 65,536-record chunks using the
  same CPU initializer, then reads **every** final state through the same 8 MiB
  chunk. Hashes and health checks cover the whole population. Vulkan staging
  remains capped at 16 MiB. Operators are held in their ordinary host vector;
  driver/compiler memory is additional and is not claimed to fit in 24 MiB.
- Streaming can write the normal checkpoint ABI through a `.partial` file,
  committed after complete valid readback. Its destination must not already
  exist. Resume uses the normal full-snapshot path; `--stream --resume` is
  rejected explicitly. Streamed readback timing includes health/hash work;
  its separately measured analysis time is an overlapping subinterval.
- `DAWNWOOD_VALIDATION=1` requests Khronos validation. With
  `VK_LAYER_VALIDATE_SYNC=1`, the runtime also enables synchronization
  validation explicitly through `VkValidationFeaturesEXT` and reports it.

All scalar equations, bytecode, state/operator/config layouts and tolerances
remain unchanged. Workgroup/page changes must pass CPU/GPU comparisons and
checkpoint identity checks. No higher arithmetic precision, fast math,
renormalization, parameter clipping or reduced state representation is used.

## Run on this laptop

From the kernel directory:

```powershell
.\scripts\run_rtx5070ti.ps1
.\bin\windows-rtx5070ti\dawnwood.exe verify --device 'RTX 5070 Ti' --count 257 --steps 4096
python tools\measure_capacity.py --binary bin\windows-rtx5070ti\dawnwood.exe --device 'RTX 5070 Ti' --stream --budget-fraction 0.98 --reserve-mib 32 --steps 4 --out results\my_rtx_capacity
```

The capacity output directory must be new. Capacity is a completed population
under the current Vulkan budget and host-memory policy, not an absolute device
maximum. `run --stream` avoids a full host-state vector. Ordinary `verify`
retains CPU and GPU snapshots and should use populations appropriate to host RAM.

The existing CMake build remains supported. Regenerate shaders before building:

```powershell
python tools\build_shaders.py --optimize --preserve-math-functions --preserve-interpreter-functions
cmake -S . -B build -A x64
cmake --build build --config Release
```

The measured edition was built with portable LLVM-MinGW 20260922 and Vulkan SDK
1.4.357.0 using C++17, `-O2 -ffp-contract=off -fno-fast-math -static`.
The repository-level `tools/build_rtx.ps1` reproduces that path and records its
commands. Runtime reports identify `0.5.1-rtx1`; numerical reports still identify
`DWI-N1-0.5`. The supplied v0.5 Android and GTX artifacts remain historical;
this edition's fresh hardware validation is on the RTX laptop.

The new layout requires four storage-buffer bindings for monolithic evolution
and five for staged evolution, plus the existing LUT image bindings. Runtime
feature checks reject insufficient device limits. This edition does not claim
fresh validation on the phone or a speed improvement on other GPUs.
