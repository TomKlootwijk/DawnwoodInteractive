# Resident executable definitions

`DWI-RESIDENT-0.1` executes a three-record mutation-and-action component on CPU or Vulkan. Its resident mutation operator changes executable handles, including its own successor; its resident pinion transports recurrent anchors. Subsequent application resolves the changed record. This supplies numerical resident definition changes that the earlier body and situated-action components did not implement. It does **not** complete the 31-record, eight-stage source application.

The executable specification is [resident_v0.1.json](../source_bindings/resident_v0.1.json). The [frontend](../local_lab/source_resident.py) compiles its typed expressions and explicit call plans into the [resident ABI](RESIDENT_ABI.md). The [shared evaluator](../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/resident.inc) executes the same representation on both backends. The source application remains preserved [separately](../source_workbench/Dawnwood_Interactive_v0.2/README.md).

## What comes from the source

Physical page 9 of [Unified v0.2](../Dawnwood_Interactive_Unified_v0.2.pdf), equations 21–25, describes each operator as a body, field and anchor. The changed field depends on the old field and the **new** body and anchor. The preceding resident mutation record participates in changing the operator table, including itself. Pages 12–13 place mutation before application and return the changed operator field with the recurrent state. The original [kernel.py](../source_workbench/Dawnwood_Interactive_v0.2/src/dawnwood/kernel.py#L82) makes the old/new ordering explicit:

1. Capture the old LUT, mutation record and pinion record.
2. Derive each new body through the old mutation record.
3. Derive each new anchor through the old pinion record and old surface context.
4. Rebind the old field using the new body and anchor.
5. Publish the complete new LUT and use its current records in subsequent actions.

The workbench supplies symbolic relationships rather than numerical laws for those calls. Unified p16 leaves their numerical bindings open. The formulas below are therefore declared implementation choices, with source relationships preserved where stated. They are not recovered equations that the original discussion uniquely specifies.

A fixed interpreter is compatible with changing resident definitions. The [implementation brief](../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/source/Dawnwood_Codex_GPU_Implementation_Brief.md) explicitly calls for a compiled interpreter evaluating mutable typed records. Early [Formalization](../Dawnwood_Interactive_Formalization.pdf), physical p9 §7.3, proposes a bounded variant/anchor executor. Conversely, Unified pp10 and 17 describe an open symbolic workbench without fixed catalogue or opcode limits. The finite bank here is a restricted numerical profile; it does not implement that workbench's unrestricted authoring range.

## The selected records and their storage

Each GPU lane contains its **own independent substrate instance**: three live records and 16 state floats. Lanes do not form a population sharing one common operator LUT. Source indices remain distinct from compact storage ordinals.

| Ordinal | Source key/index | Initial body | Body alternatives | Field / placement |
|---|---|---|---|---|
| 0 | `hadamard`, 1 | `hinge_forward` | Forward or conjugate two-Hadamard expression | Intrinsic disk family / recurrent canonical or shifted placement |
| 1 | `pinion`, 5 | `pinion_forward` | Forward or reverse transport | Same field and placement families |
| 2 | `mutation`, 30 | `mutation_initial` | Initial or successor selection rule | Same field and placement families |

The immutable bank contains 15 functions. A live record holds body, field and placement handles, a generation counter, and 20 FP32 values. Its values include anchor coordinates/orientation, radius, phase gain, control, pinion increments, and diagnostics recording the old body and controller-field evaluations. Some retained fields, including `shift_u`, `shift_v`, `placement_scale`, `feedback_gain` and reserved values, do not drive this component's recurrence. A stored name alone does not establish an executed dependency.

The state contains the query's `u,v,orientation`, two complex amplitudes, phase, interval `dt`, a supplied jitter bit, one preceding amplitude pair, and two chart-context values called `surface_u/v`. These last values do not constitute a newly evaluated Klein-surface program. The quotient metric is fixed in this profile. History is retained but the complete source RGBA/history/inverse machinery is not present.

The initial anchor values are authored from the earlier golden-angle placement convention using the original indices and catalogue count 31. Only three records are instantiated. Later anchors recur from their preceding values; they are not regenerated from that initial phyllotaxis seed each epoch.

## The declared numerical laws

The following formulas describe the real-arithmetic laws. Actual constants, operands and intermediates execute as FP32 with the declared portable arithmetic. Parentheses and the expression AST determine rounding order; these equations are not a permission to reassociate instructions.

### Placement and fields

The carrier is the unit flat Klein quotient:

```text
(u+1,v) ~ (u,-v)       (u,v+1) ~ (u,v)
```

Canonicalization wraps both coordinates and flips the orientation bit on an odd horizontal seam crossing. An FP32 remainder rounded to one is replaced by the largest FP32 value below one, for both coordinates. The shifted placement program first adds `1/16` to its supplied recurrent `u`, then canonicalizes. A record's placement is an executed expression over its stored anchor, not merely a displayed coordinate.

The nearest-lift helper examines horizontal lifts `m=-1,0,1` in that order, wraps each vertical displacement using `dy -= floor(dy+0.5)`, and retains the first strict minimum. Its field is

```text
disk:           d_K(query,anchor) - radius
expanded disk:  d_K(query,anchor) - (radius + 1/32)
```

The effective radius must lie strictly between zero and `0.5`. Under this chosen quotient metric, these are signed distances to intrinsic geodesic disks in real arithmetic; negative means inside. The [situated-action document](SITUATED_APPLICATION.md) gives the metric and injectivity-radius argument. This is not an ambient three-dimensional Klein-bottle SDF.

During mutation, the old target, mutator and pinion placement handles first evaluate their old anchors. Let `M` be the old mutator's field at the target placement, `T` the old target's field evaluated with the same target–mutator distance, and `P` the old pinion's field at the target placement. All three calls resolve old resident field handles and radii. Reusing the distance for `T` is justified here by the symmetric radial disk family. It does not supply a general linker for directional or anisotropic fields.

### The resident mutation rule

Write the old wave pair as `a=ar+i*ai`, `b=br+i*bi`, old target body handle as `h`, target control as `c`, old mutator control as `c_m`, and jitter as `j`. The jitter guard requires exactly zero or one. Both mutation bodies compute

```text
s  = (ai-br) + 0.25*(M+0.5*T)
     + 0.125*c_m + 0.0625*j + 0.03125*(h-4)
c' = c + 0.001*(M+0.5*T) + 0.002*ai
```

The prior-body term is part of the discrete selection policy; it is not a physical law. With the bank order in this binding, handles 4/5 identify forward/conjugate hinge, 6/7 initial/successor mutator, and 8/9 forward/reverse pinion.

| Target | Old `mutation_initial` selects | Old `mutation_successor` selects |
|---|---|---|
| `hadamard` | Conjugate if `s<0`, otherwise forward | Forward if `s<0`, otherwise conjugate |
| `pinion` | Forward | Reverse |
| `mutation` | Successor | Successor |

Thus the initial mutator selects its own new definition. That successor cannot influence another target earlier in the same mutation pass: every target still calls the captured old mutator. It governs the following epoch's mutation. This is resident selection between different executable expressions, not synthesis of novel instructions.

### Pinion transport and field rebinding

Let `(u,v,o)` be the target's old **evaluated placement**, and let `k_u,k_v` be the old chart context. The forward/reverse pinion supplies `epsilon=+1/-1` and computes

```text
bias = 0.0005*(2*j-1)
du_eff = du + 0.01*(ar-br) + 0.005*P + 0.001*k_u + bias
dv_eff = dv + 0.01*(ai-bi) + 0.005*P + 0.001*k_v + bias
raw_u = u + epsilon*dt*du_eff
raw_v = v + (1-2*o)*epsilon*dt*dv_eff
```

The result is canonicalized with orientation transport. The orientation-relative vertical increment follows the proposed pinion convention in early Formalization, physical p8, Eq18. The additional wave, field, context and jitter terms are authored here. `dt` must be positive. Forward transport retains the target's placement handle; reverse transport toggles between the canonical and shifted placement programs.

Rebinding then consumes the old field handle `f`, new body handle `h'`, new stored anchor `(u',v')`, old radius `r`, and old chart context:

```text
f' = expanded_disk_handle if h' == conjugate_hinge_handle else f
r' = clamp(r + 0.001*[h' == conjugate_hinge_handle]
             + 0.001*((u'-k_u)+(v'-k_v)), 0.05, 0.30)
```

The old field persists unless this rule selects the expanded disk. Switching back to the forward hinge does not automatically restore the original disk. Rebinding uses the transported stored anchor before the new placement expression is subsequently invoked by application. `rebind_field` is a fixed, explicitly bound helper; the original symbolic workbench likewise names its `Mutate_operator_SDF` binding without supplying a separate resident field-mutator record.

### Applying and returning the new definition

After all records publish, the action plan executes the **new** Hadamard placement, field and body. If its signed distance is `F`, the phase adapter forms

```text
phi_eff = old_phase + new_phase_gain*F
U_plus  = H * diag(1, exp(+i*phi_eff)) * H
U_minus = H * diag(1, exp(-i*phi_eff)) * H
```

`U_plus` uses early Formalization's explicitly proposed physical-p6 Eq7. `U_minus` is an authored alternative executable definition. Each contains two Hadamard applications in the same expression. The adapter's gain has radians per normalized chart-distance unit. It is not a universal field-activation gate. The old N1 `D(phi)H` update has not been redefined by this separate profile.

The component return retains the acted pair and old pair as one-step history, increases phase by `0.01*F`, and transports the query by `0.02*dt*(new_ar-new_br)` horizontally and the orientation-relative `0.02*dt*(new_ai-new_bi)` vertically, then canonicalizes. The next chart context is the old query position. `dt` and the supplied jitter bit persist. No jitter generator, source BST selection, RGBA encoding or full surface return is inferred from those fields.

## Transaction, validation and continuation

The generic engine runs the same mutation plan once per target against one immutable old instance. It validates proposed handles, signatures, finite values and `generation=old_generation+1`. It then resolves the complete candidate table for action and increments epoch only after successful state writes. Reversing target traversal must preserve the result because no candidate record is read during mutation.

Any failure restores **all** old state and record words for that instance, retaining a structured failure header. An action failure also rolls back the provisional mutations. A failed checkpoint remains frozen on continuation; a failed value never becomes valid next state. Other instances can continue. This transaction and failure policy is a declared numerical binding, not a hardware-atomic guarantee recovered from the source text.

Before compilation, every selected record must contain `source_slots` assertions matching its actual source-model body, field and placement JSON. Unknown edited declarations fail visibly; per-instance overrides cannot bypass those assertions. The frontend then lowers explicitly assigned bank expressions. Matching an assertion does not automatically derive an arbitrary symbolic source expression's numerical meaning.

The compiler and native loader validate the complete bank, typed signatures, back-references, unused words, plan frame initialization, destination coverage and finite payloads. XIR `select` eagerly evaluates its operands. The ABI permits 32 records, 64 state floats, 256 functions, 256 scalar instructions per function, 32 outputs per function, 256 frame registers and 4,096 instructions per call plan. Epoch and generation are bounded by 16,777,215. These are explicit profile limits.

`DWRD0001` checkpoints contain the bank, signatures, immutable source identities, both call plans, every live handle/parameter, state, generation and epoch. GPU configuration and initial images upload once; epoch dispatches use resident buffers without per-epoch host definition edits or uploads. Full checkpoint readback happens at the requested run boundary. This is whole-*component* continuation, not yet the source application's complete whole-state closure.

## Running the component

From the repository root, choose a fresh compilation directory:

```powershell
.\Dawnwood-Resident.cmd compile --definition source_bindings/resident_v0.1.json --output output/my_resident
.\Dawnwood-Resident.cmd run --backend vulkan --device "RTX 5070 Ti" --epochs 8 --input output/my_resident/program.bin --output output/my_resident/gpu_8.bin
.\Dawnwood-Resident.cmd inspect output/my_resident/gpu_8.bin --manifest output/my_resident/manifest.json
```

For CPU comparison, use `--backend cpu` and omit `--device`. To continue, pass the resulting checkpoint as the next input:

```powershell
.\Dawnwood-Resident.cmd run --backend vulkan --device "RTX 5070 Ti" --epochs 8 --input output/my_resident/gpu_8.bin --output output/my_resident/gpu_16.bin
```

`compile` refuses an existing output directory. Native `run` replaces its named result file, so keep distinct result names when comparing. `inspect` retains raw integer words and FP32 bit patterns alongside named values; with a manifest it verifies the static configuration hash before assigning names. Set `$env:DAWNWOOD_VALIDATION='1'` before a GPU run to enable the installed Khronos validation layer. `--reverse-targets` runs the traversal-order diagnostic.

## Evidence and remaining scope

The completed [execution summary](../output/resident_definition_2026-09-24/execution_summary.json) and [causal/transaction audit](../output/resident_definition_2026-09-24/causal_and_transaction_audit.json) record **30 paired CPU/Vulkan workloads**, all with bit-identical checkpoints on the RTX 5070 Ti Laptop GPU. They cover 737 returned instance observations, 69,278 returned instance words and 34,800 committed instance epochs. These are aggregate observations, including repeated checkpoints, rather than counts of distinct substrates. The 123 expected failed observations include 17 observations of already-failed instances. All GPU runs enabled Vulkan validation, reported zero errors and warnings, used device-local buffers, and recorded zero per-epoch host reads or uploads.

The numerical interventions establish more than changed program identities:

- Freezing the mutator's self-change leaves the first epoch's numerical state unchanged, but changes the next acting hinge body and returned state in all 17 instances. The baseline mutator changes from handle 6 to 7 at epoch 1; its successor changes hinge/pinion bodies at epoch 2. The new reverse pinion affects placement handles at epoch 3, consistent with old-snapshot mutation.
- An edited hinge expression changes the first returned wave state without changing that epoch's record table. Feedback then changes the next hinge-body selection in 13 of 17 instances and the next returned state in all 17.
- Equal-energy inputs with opposite imaginary amplitude select different hinge bodies in all 17 instances. This demonstrates dependence on wave components beyond aggregate energy for this authored rule.
- Altering the old pinion, target field or target placement changes numerical state in all 17 instances. Reverse target traversal yields the same checkpoint; continuation for 1+7 epochs matches a continuous 8-epoch run.

The [independent mathematical audit](../output/resident_definition_2026-09-24/independent_mathematical_audit.json) evaluates 51 one-epoch transitions using binary64 formulas and actual preceding FP32 checkpoint operands. It uses a wider 7×7 Klein deck enumeration, explicit old-controller/rebind equations and the closed complex two-Hadamard formula; it does not calculate expected results by interpreting the bank or call plan. Maximum absolute state error was `7.475227148390218e-8`; maximum record-value error was `5.952283854693263e-8`, both below the declared `1e-6` comparison limit. Integer mismatches were zero. Maximum relative squared-norm/energy error was `2.630401866099419e-7`. These are measured errors on the sampled transitions, not universal error bounds or validation of the complete source cycle.

The [boundary checks](../output/resident_definition_2026-09-24/boundary_semantics.json) cover opposite orientations, positive and negative seam crossings, overlapping COPY, epoch reads and plan-require failure, with CPU/GPU bit agreement. They do not establish general smooth tangent-field covariance. The loaders rejected [27 malformed binary cases](../output/resident_definition_2026-09-24/rejections/binary_rejections.json) in both native and Python validation; [10 frontend cases](../output/resident_definition_2026-09-24/rejections/frontend_rejections.json) were also rejected. The [final binding audit](../output/resident_definition_2026-09-24/final_binding_audit.json) confirms that final provenance-wording edits leave the complete compiled program and initial image identical to the executed baseline.

Reported GPU `execution_seconds` sum host submit-to-fence waits and exclude setup, command recording and readback. They are not device timestamp measurements or an application-level speedup claim. Device-local buffers and zero per-epoch host transfers establish the declared residency path; they do not establish saturation or full application fidelity.

The open integration work still includes the remaining source records, PHI/log-polar encoding, split/parity and source routing, correctly dependent four-slot RK4 with two fourth-slot Y-up actions, geometric primitives/divergence/coupling, RGBA/history/inverse and the complete Klein-surface return. The authored call plans and finite function bank do not themselves evolve, and the source cycle file is not consumed. No biochemical or other domain application is completed by this component. The [literal application contract](LITERAL_APPLICATION_CONTRACT.md) remains the acceptance target for that continued work.
