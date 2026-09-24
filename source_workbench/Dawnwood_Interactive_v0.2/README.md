# Dawnwood Interactive
## Unified Substrate Definition — Version 0.2

**Tom Klootwijk**  
**Identifier:** NL200678942  
**Date of birth:** 10-07-1990  
**Telephone:** +31655954068

The working definition is a self-referential log-polar Klein-bottle SDF system: the double pinion, Hadamard mitosis hinges, geometric operator LUT, one-bit BST, jitter at interval Ψ, RK4/Y-up action, phyllotaxis, RGBA inverse-T state and surface return belong to one recurrence. The source names the whole a **Universal Spatial State Automaton**.

The source is `source/double-slit-theory.pdf`, particularly pages 3–16 and 22–23. The original discussion is included unchanged. The manuscript gives page references throughout.

## Open the definition

`docs/Dawnwood_Interactive_Unified_v0.2.pdf` is the 18-page attributed edition. Its editable source is `docs/unified_specification.tex`; `docs/unified_specification.md` is a Markdown export of the same text. `docs/operator_dictionary.md` lists the named operators and their source locations.

The model is in `model/substrate.json`. The written execution order is in `model/cycle.json`. The record layout, initial array order and example control sequences are editable working notation for the source relationships.

## Run a working session

Python 3.10 or later is sufficient. The workbench uses the Python standard library; run it directly from this extracted directory without installing a package.

```console
python run.py catalogue
python run.py run --steps 16 --out work/session
python run.py inspect work/session/snapshot.json --operator double_dot
```

The executable is a **symbolic expression workbench**. It constructs the full recurrent expression graph, changes the live SDF operator records, follows explicit one-bit array routes and saves the resulting state. Its named geometric and kinematic terms preserve the source's operator relationships. Numerical laws absent from the source stay visible as named bodies; their binding positions are collected in `model/bindings.json`.

Each operator record contains a body, SDF expression and surface-position expression. At a Ψ step, the previous whole state and the one-bit input participate in changing those records. The changed records are the ones applied in that same written cycle. The returned state becomes the next input. The primitive geometry, fourth-slot Y-up action, phase differential, colon coupling, blend, RGBA and inverse T are part of the cycle, not detached helper functions.

A run writes:

| File | Contents |
|---|---|
| `trace.jsonl` | One record per interval: input bits, implicit route, selected entry, state identities and expression counts. |
| `snapshot.json` | The live operator field, whole state and shared expression graph. |
| `summary.json` | Session length, catalogue size, graph size and final state identity. |

The default source seed is `[0, 2, 0, 1]`, as recorded on source page 6. The jitter sequence, route bits and neck/reversal bits in `examples/session.json` are editable example inputs. The symbol Ψ remains symbolic; the workbench does not sleep on a hidden wall-clock interval.

## Continue or change the same recurrence

```console
python run.py run --resume work/session/snapshot.json --steps 16 --out work/continued
python run.py run --body-edit examples/body_edit.json --steps 16 --out work/edited
python run.py run --steps 16 --bayer --out work/readout
```

`--resume` preserves the operator history and resumes the example bit sequences at the saved epoch. `--body-edit` replaces the indicated live operator body before the next interval. `--bayer` adds a downstream readout expression; the recurrent state's content identity remains the same for otherwise identical inputs.

The workbench API exposes `Kernel.set_body(key, expression)` and `Kernel.add_operator(key, label, expression, index=None)`. Bodies are editable JSON. Their changing expression records can be exported to a numerical or device evaluator as development proceeds. A body edit changes the graph's definition; entering a JSON expression is not an automatic numerical compilation step.

There is no imposed upper step count, chart-size cap, fixed opcode whitelist, opacity clamp, field-radius gate or modulo redirection of an unfilled route. Python integers retain their ordinary expandable representation. One-bit values remain 0 or 1, and implicit array indices remain nonnegative integers. These are the types of the source's stated relations.

## Edit the model

| File | Editing role |
|---|---|
| `model/substrate.json` | Names, bodies, SDF descriptions, initial implicit indices and source seed. |
| `model/cycle.json` | The written sequence of the unified Ψ circulation. |
| `model/bindings.json` | Inventory of the numerical laws and representations to attach to named source terms. |
| `model/operator_catalogue.csv` | Operator inventory for search, annotation and comparison. |
| `model/gpu_target.json` | The owner's GPU target and the source's on-chip/VRAM residency objectives. |
| `model/packing_scenarios.json` | The source's hypothetical packing figures and operation-level cost labels. |
| `examples/session.json` | Explicit one-bit controls, route and optional readout for a work session. |

The initial catalogue order and complete cycle ordering are this edition's authoring choices. They are written out rather than presented as numeric instructions already contained in the discussion. `bindings.json` is the binding inventory; the executable reads operator bodies from `substrate.json` and live body edits. See `docs/WORKBENCH.md` for the graph format and extension points.

## Packing arithmetic

```console
python run.py packing
python run.py packing --bytes 12000000000
```

The calculation is `floor(byte_budget / bytes_per_element)`. The default byte budget is `12 * 2**30`, reproducing the scale of the source's rounded 805 million / 3.22 billion / 12.88 billion figures on page 20. The source's page-22 24–48 billion operational-state range remains a separately named scenario with its byte width open. The GPU target record follows the owner's target in the source; it is not populated by a hardware probe.

## Tests and reproducibility

```console
python tools/run_tests.py
python tools/reproduce.py
python tools/verify_manifest.py
```

The included release result records **36 passing tests**. They exercise source parity and implicit indexing, graph identity, full-state feedback, live operator changes, primitive participation, double Y-up, inverse T, history, optional readout independence, large indices and checkpoint continuation. Test output is in `results/test_report.txt` and `results/test_summary.json`.

The shipped 16-interval run is in `results/source_session/`. `tools/reproduce.py` compares an independent run and a checkpointed run with the saved final content identity. The content identity hashes the expression and its dependencies, so adding a downstream readout does not relabel the recurrent state.

The integrity manifest describes the shipped files. Editing a file or regenerating a run can change its hash. After deliberate edits, `python tools/make_manifest.py` records the new working package.

## Rebuild the manuscript

```console
python tools/build_pdf.py
python tools/export_markdown.py
```

PDF rebuilding uses `pdflatex` and the packages listed at the top of `docs/unified_specification.tex`, including the New TX and Source Sans Pro TeX packages. Markdown export uses Pandoc. Font files are not included in the package. Rebuilding produces the PDF in `docs/`; review its pages after changing the manuscript.

**Start by opening the PDF, then edit `model/substrate.json` and run a short session whose expression graph you can inspect.**
