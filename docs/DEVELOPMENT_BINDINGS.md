# Numerical components for resident SDF construction

[source_development_bindings.py](../local_lab/source_development_bindings.py) supplies thirteen explicit typed expression bindings for the [resource-distance language](DEVELOPMENT_RESOURCE_DOMAIN.md). They are component definitions for the ongoing resident application. They have not yet been connected into a complete source-cycle construction loop.

`make_bindings(training_points, ...)` declares the training requests and positive policy costs. Every expression's ordered input/output type maps are available in the returned dictionary and retained [contract receipt](../output/source_development_2026-09-25/binding_capacity/binding_contracts.json). Program opcodes, child references, root, leaf geometry and revision are runtime operands. The constructor's new node structure is a canonical left-associated BOX/SEPARATED_UNION expression with at most four leaves and seven nodes.

| Components | Intended caller responsibility |
|---|---|
| `propose_edit` | Read prior witness, state/control and situated fields; propose bounded leaf geometry and an eligibility bit. |
| `construct_code`, `construct_boxes` | Generate candidate instruction/reference words and geometry from the incumbent plus eligible edit. These are components, not a complete admission procedure. |
| `validate_code` | Establish valid count, canonical active structure, root, revision and zero inactive words before interpretation. |
| `validate_geometry_boxes`, `validate_geometry_separation`, `validate_geometry` | Check component bounds, protected quota and positive axis separation, then combine both guarded validity bits. |
| `leaf_distances` | Evaluate the four supplied box distances in the declared metric. |
| `interpret_prefix`, `interpret_middle`, `interpret` | Execute runtime nodes 0–2, 3–4, then 5–6 and the root. Thread all preceding `v0..v4` values in their declared order. |
| `score`, `accept` | Evaluate authored training coverage/complexity/area policy and strict score improvement. A caller must retain all incumbent program words on rejection. |

Inactive values are finite padding and cannot be referenced by a valid live program. Interpreter selectors have a zero fallback; that is not an admission guard. The graph must validate live code, separately decline invalid search candidates and select safe incumbent data before any eager candidate evaluation. A malformed retained program must fail the protected transaction. The caller must also prevent count/revision overflow; passing `valid=1` blindly to a constructor does not satisfy those bounds.

Geometry admission in the native components is deliberately narrower than the independent library: positive extents exceed `1e-5`, and axis separation exceeds `1e-4`. FP32 predicates alone do not supply an exact-rational certificate at their thresholds. The separate packed-constant certificates remain the mathematical reference. The domain's exact-distance theorem, native rounding error and candidate policy have distinct meanings.

The [direct component report](../output/source_development_2026-09-25/binding_capacity/REPORT.json) records 37 passing checks and 17 passing malformed-word rejection probes, with 17 native CPU invocations. All thirteen bindings compile for 3, 9 and 12 training requests within the existing 256-instruction, 64-input and 32-output limits. The largest component uses 202 instructions.

There are 1,180 independent boundary-oracle comparisons with maximum absolute error `1.91678699224e-6`, within the predeclared `2e-5` tolerance. In each row the composed union result also equals the minimum of the actual native FP32 leaf results bit for bit. These component observations do not establish Vulkan parity, a retained growing definition, accepted-program continuation, a source-connected evidence loop or useful task improvement. Those remain the next integration requirements.
