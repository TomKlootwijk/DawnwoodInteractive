# Situated source-record execution, 24 September 2026

**DWI-APPLY-0.1 executes one actual source record's placement, field and body on CPU and Vulkan. The complete source cycle and resident self-mutation remain unfinished.**

The selected `hadamard` record comes from the restored original source model. Its placement produces an anchor in the flat Klein chart. The field evaluates signed distance to a geodesic disk in that chart. The explicitly authored application supplies `phase + phase_gain * distance` to the early formalization's `H diag(1,exp(i*phase)) H` body. Changing each actual source slot changes the measured action through this composition.

The [binding documentation](../../docs/SITUATED_APPLICATION.md) gives the source relationships, formulas, units, guards, frame convention and proof for the intrinsic disk distance. The phase coupling and normalized placement are declared numerical choices, not equations recovered verbatim from an otherwise complete source specification.

## Executed evidence

The [primary campaign](execution_summary.json) comprises 11 workloads: **6,177 lanes and 98,832 output FP32 words**. Every CPU/GPU result file is byte-identical, including statuses. Four intentionally invalid lanes fail with native exit code 3 and zeroed rows; the other lanes succeed.

| Experiment | Lanes | Result |
|---|---:|---|
| Baseline composition | 1,028 | 207 instructions; all three source slots numerically contribute to action outputs. |
| Placement expression edit | 1,028 | Anchor, field, phase and action change on every row. |
| Field expression edit | 1,028 | Field, phase and action change; anchor is unchanged. |
| Body expression edit | 1,028 | Negated `ar` changes action; anchor, field and phase are unchanged. |
| Two zero-gain controls | 2,056 | Shift changes all fields but no action outputs. |
| Klein seam and frame witness | 3 | Correct reflected lift and anchor-frame transverse sign; equivalent query matches. |
| Zero/half radius and negative placement scale | 3 | Three intended failed lanes. |
| Invalid orientation among valid rows | 3 | Only the invalid middle row fails. |

Each workload folder retains its model, numerical bindings, inputs, program, manifest, CPU/GPU output binaries, commands, exit codes and stdout/stderr. Baseline and interventions use the same 257 dyadic base inputs plus three equivalent representatives of each point: `(u+1,-v,1-orientation)`, `(u,v+1,orientation)` and `(u-1,-v,1-orientation)`. All **771 representation comparisons are bit-identical**.

The [independent comparison](mathematical_comparison.json) uses a binary64 closed complex matrix and a wider 7-by-7 deck-transformation enumeration. It does not evaluate the bytecode to obtain expected answers. Maximum observed errors are `6.879503089418648e-8` for field distance and `8.989368327494418e-8` for action components; the comparison limit is `1e-6`. The relative squared-norm error is `2.2246852641553494e-7`. These are sampled errors, not universal accuracy bounds.

An [additional three-row boundary experiment](boundary_comparison.json), outside the primary counts above, has byte-identical CPU/GPU results. It checks the first horizontal lift on a tie, the negative half-unit vertical tie, and the greatest-below-one correction when FP32 wrapping a tiny negative coordinate rounds the remainder to one.

All recorded GPU receipts identify **NVIDIA GeForce RTX 5070 Ti Laptop GPU** and report Khronos validation enabled with zero warnings or errors. [Hardware identification](hardware.txt) is also recorded independently. The unchanged XIR executable SHA-256 is `c7f0ab76c3956222f3abbf93b214d0ab3c2d8be6b682ec3f531d1c7c6df68e01`. Its adjacent SPIR-V and original build record remain necessary parts of the native evaluator.

## Compiler and provenance checks

The linker resolves all three actual source slots as registered symbols or inline expressions. A global call table does not substitute for a missing record definition. It tracks numeric and guard ancestry separately from register sharing, rejects entirely unused calls, and requires all three source slots to reach declared action outputs. Structural ancestry does not prove nonzero sensitivity; the edit and zero-gain experiments supply that separate evidence.

[Frontend rejection evidence](frontend_rejections.json) records malformed definitions, calls, parameters and input rejection, including disconnected slots, unused callee arguments, unused failing calls and ambiguous call-name collision checks. Eager evaluation means an arithmetic failure in an ignored argument can fail the whole lane. `global_execution_control` records every instruction's failure policy and source sites separately from action ancestry; unrelated guards cannot make a disconnected field qualify as an action dependency.

[Compiler provenance audit](compiler_provenance_audit.json) records the final compiler hash and confirms that refreshed provenance manifests compile to exactly the already executed program bytes. The correction changes provenance and validation, not the numerical programs. [Launcher and artifact checks](launcher_and_artifact_audit.json) exercise the actual compile/run/inspect commands and verify all 2,215 existing native manifest entries without a mismatch.

The original workbench and historical native profiles are preserved. No new test files were added; the campaign uses direct numerical experiments, existing validation and recorded artifacts in accordance with repository instructions.

## Reproduce a situated action

From the repository root, choose a fresh directory:

```powershell
.\Dawnwood-Apply.cmd compile --bindings source_bindings/situated_v0.1.json --operator hadamard --inputs source_bindings/examples/situated_inputs.json --output output/my_situated
.\Dawnwood-Apply.cmd run --backend vulkan --device "RTX 5070 Ti" --input output/my_situated/program.bin --output output/my_situated/gpu.bin
.\Dawnwood-Apply.cmd inspect output/my_situated/gpu.bin --manifest output/my_situated/manifest.json
```

Use `--backend cpu` without `--device` for the other backend. `DAWNWOOD_VALIDATION=1` requests the installed Khronos layer; this campaign also set `VK_LAYER_PATH` to the cached SDK's `Bin` directory. Compilation refuses an existing directory. Native execution overwrites its named result, so use separate CPU/GPU filenames.

The source cycle is not consumed by this command. The current program is static during dispatch; definition edits in this campaign are external edits followed by recompilation. These small correctness runs are not saturation measurements and do not establish an AI, biochemical or complete recurrent application. Resident, versioned definitions, snapshot-based mutation, typed stage dispatch, the authored eight-stage circulation and whole-state continuation are the next runtime requirements.
