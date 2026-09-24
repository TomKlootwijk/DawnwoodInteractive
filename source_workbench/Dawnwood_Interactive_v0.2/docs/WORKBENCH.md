# The unified symbolic workbench

## State and operator records

The model preserves the source's distinction between an operator's changing body, its SDF and its location while retaining all three in one record. The field that acts is a component of the recurrent state it acts on. Source basis: pages 12–16 of `source/double-slit-theory.pdf`.

A live operator record contains:

```text
index   implicit integer address
key     editable operator name
body    reference to its definition expression
field   reference to its SDF expression
anchor  reference to its pinion-held surface-position expression
record  reference joining key, body, field and anchor
```

No child-pointer fields are stored. The native route uses `2 * index + 1 + bit`. A reversal bit applies XOR to each supplied route bit before the child relation is evaluated. The one-bit reversal notation is an editable writing of the source's neck/path reversal (source page 15); the child relation is explicit on source page 22.

The source names the surface and field relationships but does not supply all their numerical laws. The executable therefore produces symbolic applications of those laws. Its graph is an intermediate representation for developing and attaching them, not an array of silently substituted numerical approximations.

## Expression graph format

`snapshot.json` contains a `graph` array. Every node has an `id` and content-based `sha256`.

```json
{"id": 0, "kind": "symbol", "name": "PSI", "sha256": "..."}
```

A literal owns a JSON value. A call contains a head and argument node indices:

```json
{"id": 8, "kind": "call", "head": "SDF_definition", "args": [3, 4, 6, 1], "sha256": "..."}
```

Calls refer to preceding nodes. Identical expressions share a node. Hashes incorporate the content hashes of arguments, not their incidental numeric node IDs. This permits an independent run, or a run with extra downstream readout nodes, to identify the same recurrent expression.

The graph itself is an acyclic record of successive expressions. Self-reference is expressed by each epoch consuming the previous whole-state expression, including its operator field, and emitting the next one. It is the recurrence of definitions and state, rather than a Python reference cycle.

## The written cycle

`model/cycle.json` supplies this order:

```text
operator_mutation
log_polar
split_and_hinge
selected_operator
rk4_four_slots
geometry_divergence
rgba_crystal
surface_return
```

This sequence is the edition's editable linear writing of the source's intertwined relationships. The source's six geometric primitives are all applied in the geometric phase. The phase differential, phyllotaxis, colon operator and blend are applied in the same phase. The fourth RK4 slot receives two nested applications of the current `y_up` record. All four slots enter the RK4 result and the B history. A is an application of the current `inverse_T` record to its selected T expression.

At the beginning of a step, mutation reads the preceding LUT and preceding whole state. Each resulting record then participates in the current step's applications. Mutation uses the preceding mutation-operator record itself; that operator is also changed in the new LUT. This is the explicit causal ordering used by the workbench.

The numerical operators can be bound through a downstream evaluator that handles `Apply_SDF_operator`, `SDF_definition`, `Mutate_operator_body`, `Mutate_operator_SDF` and `Double_pinion_surface_position` using the body and field expressions. The named bindings in `model/bindings.json` identify the source relationships for which such numerical laws are to be entered. The exported graph retains the information needed to distinguish a body before and after an edit.

## Live edits and additional entries

```python
import json
import sys
from pathlib import Path

root = Path.cwd()
sys.path.insert(0, str(root / "src"))
from dawnwood.kernel import Kernel

model = json.loads((root / "model/substrate.json").read_text(encoding="utf-8"))
cycle = json.loads((root / "model/cycle.json").read_text(encoding="utf-8"))
kernel = Kernel(model, cycle)

kernel.set_body("double_dot", {
    "symbol": "My_double_dot_definition",
    "operands": ["left_pinion", "right_pinion", "local_SDF"]
})
kernel.add_operator("extension", "My situated operator", {
    "symbol": "My_SDF_definition"
})

row = kernel.step(jitter=1, route_bits=[0, 1], neck=0)
print(row["state_after_sha256"])
Path("my_state.json").write_text(
    json.dumps(kernel.snapshot(), ensure_ascii=False), encoding="utf-8"
)
```

`set_body` changes a definition and the associated field reference. `add_operator` appends an implicit entry, or accepts an explicit unoccupied nonnegative index. Both changes are read by the next mutation-and-application cycle.

The operator catalogue and the cycle are coupled. Core stage handlers refer to their named entries (`phi`, `hadamard`, `rk4`, and so on), while `selected_operator` uses the current routed entry. Keep those names aligned when changing the catalogue or change the corresponding stage in `src/dawnwood/kernel.py`. Additional stages can be written there; a new phase name without a Python handler is preserved as a named symbolic phase application.

## Checkpoints and output

`Kernel.snapshot()` exports the current model, cycle, live operator records, state references and graph. `Kernel.from_snapshot()` restores them and verifies their expression identities. The session runner resumes at the saved epoch, so a run of 8 intervals followed by another 8 uses the same explicit controls as one run of 16.

Bayer output is requested after state return. It receives the whole state as its operand and is not used as the next feedback input. The tests compare recurrent content identities with and without that optional output over several intervals.
