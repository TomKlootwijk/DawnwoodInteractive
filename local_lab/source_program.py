"""Compile explicitly authored source slots into the complete resident cycle.

Original symbolic declarations retain their published numerical-edition binding.
Changed declarations require explicit expressions; no symbolic meaning is guessed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

try:
    from . import source_cycle as cycle_binding
    from . import source_enzyme as enzyme
    from . import source_ir as ir
    from . import source_resident_v2 as resident
    from . import source_slot_bindings as slots
    from . import source_catalogue_extension as catalogue
except ImportError:
    import source_cycle as cycle_binding
    import source_enzyme as enzyme
    import source_ir as ir
    import source_resident_v2 as resident
    import source_slot_bindings as slots
    import source_catalogue_extension as catalogue

AUTHORING_PROFILE = "DWI-SOURCE-PROGRAM-0.1"


def build_definition(model, cycle, instance_count=17, *, registry=None,
                     enzyme_inputs=None, routes=None):
    core_model, extension = catalogue.prepare_extended_model(model)
    canonical, resolutions = slots.prepare_model(core_model, registry)
    if enzyme_inputs is None:
        definition = cycle_binding.build_definition(canonical, cycle, instance_count)
    else:
        if extension is not None:
            raise ValueError("The enzyme profile uses all64 state words; its catalogue extension requires a separately declared routing layout")
        definition = enzyme.build_definition(canonical, cycle, enzyme_inputs)
    resolved = slots.apply_resolutions(core_model, definition, resolutions)
    extended = catalogue.apply_extension(model, definition, extension) if extension is not None else None
    routed = catalogue.set_routes(definition, routes) if routes is not None else None
    definition["source"]["model_semantic_sha256"] = ir.sha256(ir.json_bytes(model))
    definition["source"]["source_slot_policy"] = (
        "Changed declarations are resolved from inline resident_binding expressions or an exact-declaration registry. "
        "Compatible body variants, field and placement persistence are explicit authored policies.")
    definition["source"]["authoring"] = {
        "profile": AUTHORING_PROFILE,
        "actual_model_sha256": ir.sha256(ir.json_bytes(model)),
        "canonical_edition_model_sha256": ir.sha256(ir.json_bytes(canonical)),
        "slot_resolutions": resolved,
        "catalogue_extension": extended,
        "routes": routed,
        "application": "enzyme_pool" if enzyme_inputs is not None else "source_cycle",
        "authoring_time": "Before compilation; runtime mutation selects resident compatible programs and updates record values.",
        "snapshot_policy": "Input is an authored model, not snapshot.model from the symbolic application's stale edit history. Use complete DWRD0002 checkpoints for numerical continuation.",
        "generator_sha256": ir.sha256(Path(__file__).read_bytes()),
        "slot_resolver_sha256": ir.sha256(Path(slots.__file__).read_bytes()),
        "catalogue_resolver_sha256": ir.sha256(Path(catalogue.__file__).read_bytes()),
    }
    return definition


def compile_program(model, cycle, instance_count=17, **kwargs):
    definition = build_definition(model, cycle, instance_count, **kwargs)
    program, manifest = resident.compile_definition(model, definition)
    authored = definition["source"]["authoring"]
    manifest.update(source_cycle_lowered=True,
                    domain_application_implemented=kwargs.get("enzyme_inputs") is not None,
                    source_authoring_profile=AUTHORING_PROFILE,
                    scope="explicit_source_slot_authoring_into_the_eight_stage_resident_cycle")
    manifest["binding_contract"]["source_authoring"] = authored
    manifest["binding_contract"]["catalogue_growth"] = (
        "One explicitly bound record can be added before compilation in the core profile; no runtime allocation."
        if authored["catalogue_extension"] is not None else False)
    return definition, program, manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("compile")
    command.add_argument("--model", type=Path, default=cycle_binding.MODEL)
    command.add_argument("--cycle", type=Path, default=cycle_binding.CYCLE)
    command.add_argument("--registry", type=Path)
    command.add_argument("--enzyme-inputs", type=Path)
    command.add_argument("--routes", type=Path, help="JSON list of explicit source-index or bit-path route declarations")
    command.add_argument("--instances", type=int, default=None)
    command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.enzyme_inputs and args.instances is not None:
        raise ValueError("With --enzyme-inputs, the observation rows determine the instance count")
    files, documents = {}, {}
    for key, path, filename in [
        ("model", args.model, "source_model.json"),
        ("cycle", args.cycle, "source_cycle.json"),
        ("registry", args.registry, "slot_registry.json"),
        ("enzyme_inputs", args.enzyme_inputs, "enzyme_inputs.json"),
        ("routes", args.routes, "routes.json"),
    ]:
        if path is not None:
            documents[key], files[filename] = ir.read_json(path)
    definition, program, manifest = compile_program(
        documents["model"], documents["cycle"], args.instances if args.instances is not None else 17,
        registry=documents.get("registry"), enzyme_inputs=documents.get("enzyme_inputs"), routes=documents.get("routes"))
    files.update({"definition.json": ir.json_bytes(definition), "program.bin": program,
                  "resident_binding_dependency.json": cycle_binding.RESIDENT.read_bytes()})
    for module in [sys.modules[__name__], slots, catalogue, cycle_binding, enzyme, ir, resident]:
        path = Path(module.__file__)
        files["compiler/" + path.name] = path.read_bytes()
    # The generic resident compiler also imports this expression-format module.
    dependency = Path(resident.__file__).with_name("source_ir_v2.py")
    files["compiler/" + dependency.name] = dependency.read_bytes()
    manifest["files"] = {name: {"bytes": len(data), "sha256": ir.sha256(data)} for name, data in files.items()}
    manifest["source_model"] = {"path": str(args.model.resolve()), "sha256": ir.sha256(files["source_model.json"])}
    manifest["source_cycle"] = {"path": str(args.cycle.resolve()), "sha256": ir.sha256(files["source_cycle.json"])}
    manifest["authoring_input_documents"] = {
        key: {"path": str(path.resolve()), "retained_file": filename,
              "sha256": ir.sha256(files[filename])}
        for key, path, filename in [
            ("model", args.model, "source_model.json"), ("cycle", args.cycle, "source_cycle.json"),
            ("registry", args.registry, "slot_registry.json"),
            ("enzyme_inputs", args.enzyme_inputs, "enzyme_inputs.json"), ("routes", args.routes, "routes.json")]
        if path is not None}
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    (output / "manifest.json").write_bytes(ir.json_bytes(manifest))
    print(json.dumps({"output": str(output), "profile": AUTHORING_PROFILE,
                      "program_sha256": ir.sha256(program), "bytes": len(program),
                      "instances": len(definition["instances"]), "records": len(definition["records"]),
                      "functions": len(definition["functions"]), "families": len(definition["families"]),
                      "state_width": len(definition["state_names"])}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, KeyError, RecursionError, OverflowError) as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(1)
