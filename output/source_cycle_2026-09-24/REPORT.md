# Authored resident source cycle — 24 September 2026

The final **cycle_v0.1** edition executes the source's eight-stage core through **DWI-RESIDENT-0.2**. Its 31 resident records contain current body-family, field and placement handles. The preceding mutator and pinion create the next table, including their own definitions; subsequent calls execute the newly published definitions. The complete numerical state and program bank survive checkpoints.

This is an explicit finite numerical interpretation of the source relationships. The [source fidelity audit](SOURCE_FIDELITY_AUDIT.md) maps each relationship to the original application and final compiler. The [binding contract](../../docs/SOURCE_CYCLE_BINDING.md) states the equations, metric, units, domains and limits. Source statements, authored numerical laws, static wiring and measured behavior are separate evidence.

## Final executed edition

| Property | Value |
|---|---|
| Resident source records | 31 |
| Typed body families | 34 |
| Expression functions | 55 |
| Per-instance state | 44 FP32 values plus complete live record table |
| Mutation/action tape lengths | 92 / 955 instructions |
| Complete instance image | 794 uint32 words, 3,176 bytes |
| Typed RGBA payload | R complex2, G complex2, B history4, A inverse-matrix4 |
| Carrier | Unit flat Klein quotient with chart coordinates and orientation |
| Selected-action adapters | Source indices 7–12; incompatible roles fail explicitly |

The original wavefront seed `[0,2,0,1]` supplies the initial two complex amplitudes. The actual source cycle controls phase order and Y-up count. Each current semantic action evaluates its live placement and field before its typed body. The current Klein point controls subsequent field queries in that cycle, and the preceding returned chart influences the next Klein update. The metric itself remains fixed.

Mutation reads one common preceding snapshot for all 31 targets. Rebinding uses the old field and new body/anchor. Publication precedes the new Klein call and subsequent phases. A failure anywhere restores the whole preceding instance; a failed instance remains frozen until the user supplies a repaired input.

The numerical edition retains the source order: mutation, PHI, split/hinge, selected operator, dependent four-slot RK, geometry/divergence, RGBA, and return. The double-Hadamard law is `H diag(1,exp(±i*phase)) H`. Two non-cancelling Y-up shears act on k4 before weighted combination; unmodified classical fourth-order accuracy is not claimed with these events. T is an actual 2×2 transformation and A its complete inverse.

## Execution and causal evidence

The final campaign records **46 complete-cycle paired CPU/GPU workloads and two diagnostic RK-prefix pairs**: 1,054 returned instance observations, 836,876 compared instance words and 20,846 committed instance-epochs. All complete checkpoint bytes match between CPU and the physical RTX 5070 Ti Laptop GPU. Five intentional failed observations retain the exact previous state/records. All GPU runs enable validation with zero errors and warnings. These totals exclude the separate component-math and saturation workloads below.

- Seventeen instances agree after 1, 2, 8 and 64 epochs. Reversed target traversal and continuation `1+63` equal uninterrupted 64-epoch checkpoints exactly. A wider 257-instance run agrees through 65 epochs, including the submission-batch boundary.
- Deliberately editing each of **28 executed body roles** changes numerical state in all 17 instances. This includes both RK roles, the selected geometric adapter, current Klein, PHI, split/parity, each primitive, history, transformation/inverse and return. These scalar perturbations are causal interventions; some intentionally violate the edited body's mathematical specification and are not proposed valid production laws.
- Separate old-pinion transport, carrier-field and placement edits affect all 17 returned states. Bodies, fields and positions are numerically connected rather than decorative metadata.
- Freezing only the mutator's successor leaves all first-epoch state words identical and changes exactly its 17 resident body handles. At epoch two, all 17 returned states change. This demonstrates delayed resident self-change, distinct from an external recompilation alone.
- Altering preceding B history, encoded phase history, or the returned spatial chart changes all 17 returned states. A Klein body edit now changes 459 state words across the 17 instances, including downstream computation. A preceding-chart edit changes 451.
- The actual cycle's RK-prefix probe preserves k1–k3 bit for bit when Y-up is disabled and changes k4 in all 17 instances when two events are enabled. The complete-cycle zero-event intervention also changes all 17 results. Diagnostic prefixes are not counted as complete cycles.
- Fifteen dyadic representatives of the same previous returned Klein point produce identical complete returned images. This is a sampled quotient-consistency result, not a proof of smooth tangent covariance for arbitrary asymmetric fields.
- Every one of the six selected-action adapters executes under both neck conventions. An unsupported role, fractional route depth, zero complex amplitude, zero interval and invalid jitter produce the expected failures and exact whole-epoch rollback.

See [the aggregate](FINAL_SUMMARY.json), [baseline runs](cycle_baseline_summary.json), [interventions](cycle_intervention_summary.json), [additional runs](cycle_additional_summary.json) and [connection checks](cycle_connection_audit.json). `cycle_runs/` retains each program or exact baseline input, raw CPU/GPU checkpoints, commands, exit codes, logs and the declared change. Exit3 denotes the intentional instance failures, not a healthy result.

## Independent mathematics

The [component audit](cycle_math/REPORT.md) covers **3,902 active final-edition cases**, using the actual expression bodies and independent binary64 references on the packed FP32 inputs. Every paired CPU/GPU checkpoint is identical.

The six geometry bodies are checked against independent segment/radial/cone calculations; the maximum sampled absolute error is `2.461287e-7`. T-shaped and pyramid-side fields are exact distances in their declared two-dimensional metrics; the capped cone is three-dimensional; the apex is an unsigned point distance. These distinctions are part of the binding.

Independent Gauss-Jordan references verify the inverse; the largest sampled entry of `T*A-I` is `1.509629e-7`. Pinion references check both return variants across negative, positive and multiple seams. Jitter-aware RK references use the complex stability polynomial plus the separately derived two-shear correction, with maximum sampled absolute error below `1.47e-7`. All four slopes, both jitter values and the Y-up intervention are represented.

The [portable log/atan2 campaign](RUNTIME_REPORT.md) separately records 27,240 CPU/GPU cases, including domain failures, signed axes and subnormal angle results. None of these finite samples is an exhaustive floating-point proof or a measurement validating a new physical law.

## Laptop compute saturation

The final [sustained run](saturation_sustained/summary.json) executes **32,896 independent instances × 2,048 epochs**, or **67,371,008 complete instance-epochs**. Its initial population repeats 257 distinct templates 128 times. Every returned GPU image is compared with the corresponding independently executed 2,048-epoch CPU template: **26,119,424 words compared, zero differences**. Replication is explicit; this is not a claim of 32,896 distinct scientific inputs.

| Measurement | Observed value |
|---|---|
| GPU | NVIDIA GeForce RTX 5070 Ti Laptop GPU, 12,227 MiB reported total |
| Native GPU execution timer | 50.106702 seconds |
| Timer scope | Sum of host submit-to-fence waits; excludes setup, command recording and readback |
| Telemetry | 108 samples at requested 500 ms intervals; 92 report 100% GPU utilization |
| Highest recorded temperature | 70°C |
| Highest recorded power | 121.76 W |
| Highest recorded device memory used | 395 MiB |
| Two instance buffers | 208,955,392 bytes, plus configuration/runtime allocation |
| Validation errors/warnings | 0 / 0, validation enabled |
| Explicit per-epoch host reads/uploads | 0 / 0 |

The earlier [256-epoch load](saturation/summary.json) also reaches 100% reported GPU utilization with all-word agreement. The sustained run extends that observation. Both use the unchanged final numerical edition and native executable. No power limit, voltage or clock configuration was changed. The recorded 90°C stop condition was not reached.

This establishes **compute saturation for these runs**, not maximum VRAM capacity, permanent cache residence, zero physical bus traffic, a FLOPS result or an application speedup. The CPU timing is for 257 templates, while the GPU population contains 128 replicas of each; comparing those two wall times directly would be misleading.

Complete large input/output files are retained losslessly as `input.bin.xz` and `output.bin.xz` in each saturation directory. Their uncompressed and archive hashes are recorded, and decompression was checked byte for byte. The `.bin` payloads use the same native checkpoint format; decompress them before running or inspecting them. Raw telemetry, stdout/stderr and commands are retained alongside the archives.

## Reproduction and scope

```powershell
.\Dawnwood-Cycle.cmd compile --output output/my_cycle
.\Dawnwood-Cycle.cmd run --backend vulkan --device "RTX 5070 Ti" --input output/my_cycle/program.bin --output output/my_cycle/after_64.bin --epochs 64
.\Dawnwood-Cycle.cmd inspect output/my_cycle/after_64.bin --manifest output/my_cycle/manifest.json
```

The actual launcher compile and inspect were exercised; compilation reproduces the final baseline bytes. Sixteen invalid source/cycle edits were rejected. The earlier runtime campaign separately records eighteen malformed frontend definitions and fifty-nine malformed binary rejections. No persistent test suite was added.

Final baseline program SHA256:
`f746ede446a773057084dc6a01f296100c35531fa676a1a71ea41863c4501dc5`.
`full_cycle/` contains source snapshots, authoring/dependency snapshots, the explicit definition, program and manifest. The [native build receipt](../../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/bin/windows-resident-v2/build.json) identifies the executable and shader already verified by the runtime campaign.

`pre_guard/` preserves an earlier candidate's runs before primitive-domain guards and direct-source-edge corrections. `pre_direct_edges/` preserves a compiled intermediate candidate. They are excluded from final totals. Old pre-jitter RK diagnostics remain labelled historical inside `cycle_math/`. Retained evidence is not silently reassigned to a later definition.

The completed milestone is the **bounded authored numerical core and its source connections**. Operator-family selection is finite; arbitrary instruction synthesis and catalogue growth are absent. Only six selected-action interfaces are supplied. Optional Bayer layout/BC5 encoding and unrestricted symbolic lowering remain outside the edition. **A useful biochemical or other domain application through this resident cycle is still required**; the earlier fixed D1 solver does not fill that requirement. Nothing here establishes quantum computation, automatic optimization, universal expressibility or new physical behavior.
