# Independent amplitude-budget numerical experiment

All three paired workloads completed successfully on CPU and **NVIDIA GeForce RTX 5070 Ti Laptop GPU**. Each complete CPU checkpoint matched its GPU checkpoint byte for byte. All statuses were zero; Vulkan validation reported zero errors and warnings. The experiment checked 257 actual selected-stage inputs and 543 isolated component inputs. The two capture prefixes plus the isolated component executed 1,057 lanes per backend.

The authored operation is the Euclidean projection onto the closed unit ball in `C² = R⁴`, with dimensionless real coordinates `w=(ar,ai,br,bi)`:

```text
d(w) = hypot(ar,ai,br,bi) - 1
projection(w) = w / max(1,hypot(ar,ai,br,bi))
```

The independent reference uses Python's binary64 `math.hypot` on the actual packed/captured inputs. It does not recursively evaluate the authored expression tree or repeat the implementation's nested scaled two-component norm formula.

## Actual source-cycle prefixes

The experiment compiles [`amplitude_budget_model.json`](../../../source_bindings/examples/amplitude_budget_model.json) through the actual `source_program.build_definition`. It retains the entire generated function/family bank, all 32 records, the complete old-snapshot mutation plan, and the original action phases leading up to selection. The inputs vary both nonzero complex amplitudes, neck and jitter. All routes target the actual source index 31; inverse route construction accounts for each supplied neck bit.

The selected call at action step 216 is:

```text
[11,80,0,1,200,64,90,99]
```

Two explicitly labelled diagnostic programs stop immediately before and immediately after that dynamic source-index body call. They capture the current wave from frame 64..67 into state `ar..bi`, and selected index from frame 80. Other state values are restored from the original old state solely to produce a complete diagnostic checkpoint. The mutation record tables match between the two captures. The diagnostic programs **do not complete the whole source cycle**.

The selected input norms ranged from 0.0001093791878 to 7,448.158589. There were 129 inside and 128 outside points.

| Quantity | Measured maximum |
|---|---:|
| Absolute error in any projected component |1.2084955925e-7|
| Projected norm |1.0000001384256556|
| Error in projection displacement length |1.3842566204e-7|

All 257 cases passed the predeclared 1e-6 absolute component tolerance and 1e-6 norm-overshoot tolerance. Small measured overshoot is retained; the report does not clip it into an exact bound.

## Isolated original expression

The separate component fixture uses the exact four authored projection-output expressions. It exposes their already-used signed-distance subexpression as one additional diagnostic output under a new diagnostic signature. It does not change the arithmetic of any of the four original projection outputs. This instrumentation is explicitly recorded in its definition; it is not presented as an additional output supplied by the source role 99 interface.

The 543 cases include the zero vector, signed coordinate axes, the exact four-component boundary point `(0.5,0.5,0.5,0.5)`, immediately adjacent FP32 boundary values, and deterministic random directions with magnitudes spanning very small through very large normal inputs. Input norms ranged from zero to approximately 2.00000004e20. There were 253 strictly inside, 10 exactly on the reference boundary and 280 outside points.

| Quantity | Measured maximum |
|---|---:|
| Absolute projected-component error |1.5991811320e-7|
| `abs(actual_distance-reference_distance)/max(1,input_norm)` |1.5542318082e-7|
| Projected norm |1.00000020033379|
| Change to an inside input |0|

All component cases passed the tolerances fixed before execution: 1e-6 absolute output-component error, 1e-6 norm overshoot, and `1e-6*max(1,input_norm)` absolute signed-distance error. There were no sign disagreements farther from the boundary than that declared scaled tolerance. The ten mathematically exact boundary cases produced signed distances between −5.9604644775e-8 and zero, illustrating ordinary finite-precision uncertainty at the boundary.

The selected source body explicitly ignores `routing_phase` and `field_distance`. This is declared in the source binding so that this operation has a fixed unit-ball meaning. The actual preceding placement and carrier-field calls remain in the source prefixes; their evaluation is not a claim that every input numerically changes this particular body. No hidden carrier-dependent projection radius was added by the experiment.

## Scope and provenance

The projection property applies to its immediate selected-stage output. Later RK4, geometric, RGBA and surface-return stages can change the amplitudes. This experiment makes **no claim that the final returned cycle state remains in the unit ball**, nor does it supply a whole-cycle execution or throughput measurement. The top-level authoring campaign covers full-cycle integration separately.

The source model SHA256 is `82e867f1462c482076edad4836c4d4ba43a6517de03dc37abfde8efa8a83e080`. All source files monitored at the start and end of the experiment were unchanged. JSON/source reads used explicit UTF-8.

Each workload retains its actual program, definition, manifest, paired raw checkpoints, stdout/stderr and execution receipts with commands, binary/shader hashes and validation settings. `full_program_unexecuted.bin` and its definition preserve the unclipped parent program; the filename deliberately states that this subexperiment did not execute it. Reference comparisons, input cases, source snapshots and experiment-script text are retained. `independent_numeric_audit.json` records exact values and scope, and `artifact_manifest.json` hashes the evidence files.

This is a finite numerical computational constraint operator. No physical power, quantum hardware, biology, learning objective or universal-programming result follows from these measurements.
