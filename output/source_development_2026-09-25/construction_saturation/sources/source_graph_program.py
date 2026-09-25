"""Compile a source-declared complete recurrence graph for CPU/Vulkan execution."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

try:
    from . import source_program as author
    from . import source_graph as graph_compiler
    from . import source_graph_types as graph_types
    from . import source_graph_fidelity as fidelity
except ImportError:
    import source_program as author
    import source_graph as graph_compiler
    import source_graph_types as graph_types
    import source_graph_fidelity as fidelity

ir, resident = author.ir, author.resident


def build_definition(model, cycle, graph, instance_count=17, **kwargs):
    definition = author.build_definition(model, cycle, instance_count, **kwargs)
    graph_compiler.apply_graph(definition, cycle, graph)
    definition["source"]["graph_program_generator_sha256"] = ir.sha256(Path(__file__).read_bytes())
    return definition


def compile_program(model, cycle, graph, instance_count=17, **kwargs):
    definition = build_definition(model, cycle, graph, instance_count, **kwargs)
    program, manifest = compile_definition(model, definition)
    return definition, program, manifest


def compile_definition(model, definition):
    """Compile a graph-lowered definition and state its bounded application scope."""
    if definition.get("source", {}).get("application_graph", {}).get("profile") != graph_compiler.PROFILE:
        raise ValueError("Expected a definition lowered from the complete source graph")
    program, manifest = resident.compile_definition(model, definition)
    manifest.update(source_cycle_lowered=True, source_graph_lowered=True,
                    source_graph_profile=graph_compiler.PROFILE,
                    complete_application_lowered=True,
                    status="explicit_source_graph_lowered_numerical_evidence_recorded_separately",
                    domain_application_implemented="enzyme" in definition["source"],
                    scope="source_declared_complete_mutation_and_eight_stage_action_graph")
    manifest["binding_contract"]["application_graph"] = definition["source"]["application_graph"]
    manifest["binding_contract"]["source_authoring"] = definition["source"]["authoring"]
    manifest["binding_contract"]["catalogue_growth"] = (
        "One source-bound record can be added before compilation in the core profile; no runtime allocation."
        if definition["source"]["authoring"]["catalogue_extension"] is not None else False)
    return program, manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("compile")
    command.add_argument("--model", type=Path, default=author.cycle_binding.MODEL)
    command.add_argument("--cycle", type=Path, default=author.cycle_binding.CYCLE)
    command.add_argument("--graph", type=Path, required=True)
    command.add_argument("--registry", type=Path)
    command.add_argument("--enzyme-inputs", type=Path)
    command.add_argument("--routes", type=Path)
    command.add_argument("--instances", type=int)
    command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.enzyme_inputs and args.instances is not None:
        raise ValueError("With --enzyme-inputs the observation rows determine instance count")
    paths = {"model": args.model, "cycle": args.cycle, "graph": args.graph,
             "registry": args.registry, "enzyme_inputs": args.enzyme_inputs, "routes": args.routes}
    documents, files, origins = {}, {}, {}
    for key, path in paths.items():
        if path is not None:
            documents[key], raw = ir.read_json(path)
            filename = "source_" + key + ".json"
            files[filename] = raw
            origins[key] = {"path": str(path.resolve()), "retained_file": filename, "sha256": ir.sha256(raw)}
    definition, program, manifest = compile_program(
        documents["model"], documents["cycle"], documents["graph"],
        args.instances if args.instances is not None else 17,
        registry=documents.get("registry"), enzyme_inputs=documents.get("enzyme_inputs"), routes=documents.get("routes"))
    files.update({"definition.json": ir.json_bytes(definition), "program.bin": program,
                  "resident_binding_dependency.json": author.cycle_binding.RESIDENT.read_bytes()})
    for module in [sys.modules[__name__], author, graph_compiler, graph_types, fidelity,
                   author.slots, author.catalogue, author.cycle_binding, author.enzyme, ir, resident]:
        path = Path(module.__file__)
        files["compiler/" + path.name] = path.read_bytes()
    for name in ["source_ir.py", "source_ir_v2.py"]:
        files["compiler/" + name] = Path(__file__).with_name(name).read_bytes()
    manifest["input_documents"] = origins
    manifest["files"] = {name: {"bytes": len(raw), "sha256": ir.sha256(raw)} for name, raw in files.items()}
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    for name, raw in files.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (output / "manifest.json").write_bytes(ir.json_bytes(manifest))
    print(json.dumps({"output": str(output), "profile": graph_compiler.PROFILE,
                      "program_sha256": ir.sha256(program), "bytes": len(program),
                      "instances": len(definition["instances"]), "records": len(definition["records"]),
                      "state_width": len(definition["state_names"]),
                      "mutation_steps": len(definition["mutation_plan"]),
                      "action_steps": len(definition["action_plan"])}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, KeyError, RecursionError, OverflowError) as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(1)
