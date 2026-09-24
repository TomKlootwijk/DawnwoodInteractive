# Author executable source definitions

`Dawnwood-Author.cmd` compiles edited source declarations into the complete eight-stage resident numerical cycle. Body, field and placement expressions in the supplied model become the programs resolved by its resident records. The original symbolic workbench remains available through `Dawnwood-Source.cmd`; its commands are unchanged.

This is a bounded authoring interface for the [source requirements](SOURCE_AUTHORING_REQUIREMENTS.md). It does not infer numerical meaning from an arbitrary new symbol. The [original numerical cycle](SOURCE_CYCLE_BINDING.md), its chosen equations and the [resident ABI](RESIDENT_V2_ABI.md) remain the baseline.

## Run a source-authored program

From the repository root in PowerShell, use a fresh output directory:

```powershell
.\Dawnwood-Author.cmd compile --model source_bindings/examples/amplitude_budget_model.json --instances 129 --output output/my_amplitude
.\Dawnwood-Author.cmd run --backend vulkan --device "RTX 5070 Ti" --input output/my_amplitude/program.bin --output output/my_amplitude/after_64.bin --epochs 64
.\Dawnwood-Author.cmd inspect output/my_amplitude/after_64.bin --manifest output/my_amplitude/manifest.json
```

The added record at **source index31** supplies its own body, field, placement and all20 record values. Its five-bit path reaches that actual index. All32 records participate in the common old-snapshot mutation. The added record retains its declared program handles while its anchor, radius, control and generation can change. The normal source stages continue after its selected application.

The compilation folder retains the actual UTF-8 model and cycle, any supplied registry/routes/domain inputs, generated definition, executable program, compiler-source copies and a hash manifest. A full `.bin` checkpoint contains the expression bank, call plans, current slot handles, record values, state and failure information. Continue it with another `run --input after_64.bin`; recompiling a model starts a new run.

## What the amplitude operator computes

The two complex channels form `w=(ar,ai,br,bi)` in Euclidean `R4`. The example's feasible set is the closed unit ball. Its exact real-arithmetic signed distance and projection are:

```text
d(w) = sqrt(ar² + ai² + br² + bi²) - 1
P(w) = w / (1 + max(0,d(w)))
```

The implementation uses scaled norms to avoid unnecessary overflow and underflow. It keeps inside points unchanged and preserves the relative complex amplitudes when projecting an outside point onto the boundary. The units are dimensionless computational amplitude. A physical power interpretation would require an independently declared normalization and device model.

This is useful as an explicit amplitude-budget operation in recurrent numerical work: the source record itself carries the operation, the route selects it, and the remaining cycle receives its result. The projection is **at the selected-operator stage**. Subsequent RK, geometry and return stages can move the final wave outside the unit ball. Neither final-state boundedness nor an optimization advantage is claimed.

The amplitude-space distance differs from the operator's Klein carrier field. The example explicitly leaves `routing_phase` and `field_distance` unused in its projection body; its carrier programs still execute and participate in situated mutation. Calling an arbitrary scalar `distance` would not establish an exact SDF.

## Edit existing definitions

```powershell
.\Dawnwood-Author.cmd compile --model source_bindings/examples/authored_hadamard_model.json --output output/my_hinge_edit
```

This example explicitly edits both reachable Hadamard families' log-polar role1, adding a0.125-radian phase offset. It inherits each family's complex role0. It also supplies a shifted local disk SDF and a translated canonical Klein placement. Their `preserve_program` policies retain those programs through mutation while the normal anchor/radius rebinding proceeds.

An inline source slot is `{"resident_binding": binding}`. A body binding enumerates every compatible family, its replaced roles and whether remaining roles are inherited. Field and placement bindings supply a typed expression function and a program-retention policy. The complete schema and role/guard rules are in [the authoring requirements](SOURCE_AUTHORING_REQUIREMENTS.md#existing-record-slot-bindings). The JSON examples are executable inputs, not prose placeholders.

Alternatively use `--registry path.json`. Each registry entry must name a source record and slot, include the exact actual declaration, and supply its explicit binding. A registry can therefore resolve an authored symbolic declaration without rewriting it as inline XIR. Duplicate, unused, ambiguous or mismatched entries fail. Original ordered input/output names and guard prefixes must remain valid.

Roles are explicit overloads. For example, editing a primitive's scalar role0 does not automatically rewrite its separately authored selected role99. Edit both when that is the intended numerical definition; the compiler does not infer an adapter.

## Specialize the biochemical proposal from source

```powershell
.\Dawnwood-Author.cmd compile --model source_bindings/examples/authored_enzyme_model.json --enzyme-inputs source_bindings/examples/enzyme_inputs.json --output output/my_authored_enzyme
.\Dawnwood-Author.cmd run --backend vulkan --input output/my_authored_enzyme/program.bin --output output/my_authored_enzyme/after_128.bin --epochs 128
.\Dawnwood-Enzyme.cmd results output/my_authored_enzyme/after_128.bin --manifest output/my_authored_enzyme/manifest.json --output output/my_authored_enzyme/results.json
```

The source model replaces role100 in both reachable blend families with explicit half-step proposals. The current wave, history, inverse matrix, interval and carrier field still feed those proposals. Role0 retains the core Math_blend law; roles101–104 retain the shared chemical laws. The preceding domain results still feed the resident mutator. Observation rows determine the instance count.

This example's proposal expressions are authored for normalized enzyme/substrate totals **1 and10**, matching the supplied input file. If those totals change, author a matching proposal expression as well; the compiler does not rederive constants embedded in a user's expression. The protected domain/projection/evaluation use the actual supplied pools regardless. An incompatible proposal may therefore perform poorly even though its evaluated candidate remains subject to those laws.

The [scientific derivation](ENZYME_POOL_DOMAIN_GROUNDING.md) and [enzyme numerical limits](RESIDENT_ENZYME_BINDING.md) still apply. It reconciles concentration observations under declared conservation and nonnegativity assumptions. Computational mutation is not biochemical reaction kinetics. FP32 feasibility tolerances and gap estimates retain their original limitations.

## Routes and limits

`--routes routes.json` accepts a JSON array containing one broadcast entry or one entry per instance. An entry is `{"index":31}` or `{"bits":[0,0,0,0,0]}`. Index form derives the path adjusted for each initial neck bit. Bits form supplies the raw path before neck XOR. Targets must exist and all compatible families must provide the selected role99 contract. No modulo alias is used.

This checks the reference implicit-tree relation. In the31-record mode an explicitly edited BST body can intentionally compute another index; its measured returned `selected_index` is authoritative. The extension mode requires the declared five-bit BST binding and rejects a simultaneous BST-body override.

The core authoring edition supports the original31 records plus **one** explicit added record at source index31..62, with45 state values and a five-bit route. Without an addition it retains the original44 values and four-bit contract. The existing64-state enzyme application cannot also take this extra route word. That combination is rejected explicitly. A custom BST body cannot currently be combined with the automatic five-bit extension.

The initial bank is authored before compilation. Runtime changes select compatible resident variants and update numerical record values; this interface does not synthesize new bytecode or allocate records during execution. The original symbolic workbench's `snapshot.model` can be stale after live edits; it is not a numerical continuation format.

The application call graph and eight-stage wiring still come from the versioned cycle/application builders. A general source-declared typed application graph, heterogeneous routed procedures and larger catalogues remain further work. This authoring milestone does not establish unrestricted source expressibility, universality or new physical computation.

See the [recorded authoring campaign](../output/source_authoring_2026-09-24/REPORT.md) for separate source-edit, continuation, failure, mathematical and laptop-saturation evidence.
