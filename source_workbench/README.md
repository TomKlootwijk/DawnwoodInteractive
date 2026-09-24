# Original unified source application

`Dawnwood_Interactive_v0.2/` is a byte-for-byte extraction of the repository's
[original archive](../Dawnwood_Interactive_Unified_v0.2.zip). The 40 original
files are unmodified, including the existing checks and historical results.
[PROVENANCE.json](PROVENANCE.json) records the archive and extracted file hashes.
New execution evidence lives outside the preserved application.

This is the source's **symbolic authoring application**. Its operator records
connect body, field and anchor expressions; its cycle returns those changed
definitions as part of the next input. It constructs an expression graph. It
does not evaluate arbitrary SDF expressions numerically, run on the GPU, or
execute the D1 biochemical examples. Read the
[literal application contract](../docs/LITERAL_APPLICATION_CONTRACT.md) for the
missing numerical integration.

From the repository root:

```powershell
.\Dawnwood-Source.cmd catalogue
.\Dawnwood-Source.cmd run --steps 8 --out output/my_source_08
.\Dawnwood-Source.cmd run --resume output/my_source_08/snapshot.json --body-edit source_workbench/Dawnwood_Interactive_v0.2/examples/body_edit.json --steps 8 --out output/my_source_edited_16
.\Dawnwood-Source.cmd inspect output/my_source_edited_16/snapshot.json --operator double_dot
```

Use fresh output directories: the preserved application's CLI overwrites files
in an existing output directory. The launcher chooses the installed laptop
Python, falling back to `python`. Python 3.10+ and the standard library suffice;
`-X utf8 -B` supports the source's Unicode on Windows without cache writes.

For a portable direct invocation:

```powershell
python -X utf8 -B source_workbench/Dawnwood_Interactive_v0.2/run.py catalogue
```

The actual authoring surfaces are:

| File | Role |
|---|---|
| [model/substrate.json](Dawnwood_Interactive_v0.2/model/substrate.json) | Catalogue of 31 situated operator definitions and source references |
| [model/cycle.json](Dawnwood_Interactive_v0.2/model/cycle.json) | Eight circulation stages and two fourth-slot Y-up actions |
| [model/bindings.json](Dawnwood_Interactive_v0.2/model/bindings.json) | Inventory of nine unbound numerical meanings; not a loaded numerical plugin system |
| [src/dawnwood/kernel.py](Dawnwood_Interactive_v0.2/src/dawnwood/kernel.py) | Record mutation, application references and whole-state return |
| [src/dawnwood/terms.py](Dawnwood_Interactive_v0.2/src/dawnwood/terms.py) | Content-addressed expression graph |
| [docs/WORKBENCH.md](Dawnwood_Interactive_v0.2/docs/WORKBENCH.md) | Original commands and authoring instructions |

To experiment, copy definitions outside the preserved directory and supply
`--model`, `--cycle` or `--body-edit`. A resumed snapshot uses its saved model and
cycle, with an optional body edit applied afterward. Its session bit sequence is
supplied separately; use the same session when comparing continued runs.

[The current reproduction](../output/source_application_2026-09-24/REPORT.md)
passes all 36 original checks, reproduces the shipped 16-cycle graph exactly,
and records continuation and live body/metarule interventions. These are
structural results, not numerical performance or scientific validation.
