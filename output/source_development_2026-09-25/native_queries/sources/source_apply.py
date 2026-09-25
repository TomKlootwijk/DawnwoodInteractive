"""Link explicit placement, field and body definitions into one situated Apply.

The application binding supplies every connection between the source record's
definitions. This compiler adds no activation predicate or multiplication rule.
The source cycle, record mutation and whole-state recurrence remain unlowered.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import struct
import sys

if __package__:
    from . import source_ir as ir
else:
    import source_ir as ir


PROFILE = "DWI-APPLY-0.1"
SLOTS = ("placement", "field", "body")
APPLICATION_KEYS = {"inputs", "calls", "outputs", "action_outputs", "source", "meaning", "status"}


@dataclass(frozen=True)
class Value:
    register: int
    data: frozenset[str] = frozenset()
    control: frozenset[str] = frozenset()


def merged(values, attribute):
    return frozenset().union(*(getattr(value, attribute) for value in values))


def call_identity(call, output):
    """Keep arbitrary call/output names distinct, including dots and quotes."""
    return "call:" + json.dumps([call, output], ensure_ascii=True, separators=(",", ":"))


def provenance(value):
    def names(dependencies, prefix):
        return sorted(item[len(prefix):] for item in dependencies if item.startswith(prefix))
    return {
        "register": value.register,
        "numeric_dependencies": sorted(value.data),
        "control_dependencies": sorted(value.control),
        "numeric_source_slots": names(value.data, "slot:"),
        "control_source_slots": names(value.control, "slot:"),
        "guard_only_source_slots": names(value.control - value.data, "slot:"),
    }


def named_mapping(value, where):
    if not isinstance(value, dict) or any(not isinstance(name, str) or not name for name in value):
        raise ValueError(f"{where}: expected an object with nonempty string names")


def validate_application(application, where):
    ir.exact_keys(application, APPLICATION_KEYS,
                  {"inputs", "calls", "outputs", "action_outputs"}, where)
    # The pure binding validator already defines input/output name limits. Its
    # expression validation is deliberately deferred until the graph is linked.
    ir.validate_binding({"inputs": application["inputs"], "outputs": application["outputs"]}, where)
    calls = application["calls"]
    if not isinstance(calls, list) or not 1 <= len(calls) <= ir.MAX_INSTRUCTIONS:
        raise ValueError(f"{where}.calls: expected 1..{ir.MAX_INSTRUCTIONS} ordered calls")
    actions = application["action_outputs"]
    if (not isinstance(actions, list) or not actions
            or any(not isinstance(name, str) or name not in application["outputs"] for name in actions)
            or len(set(actions)) != len(actions)):
        raise ValueError(f"{where}.action_outputs: expected unique names from outputs")


def resolve_definition(definition, symbols, where):
    if isinstance(definition, dict) and "symbol" in definition:
        ir.exact_keys(definition, {"symbol"}, {"symbol"}, where)
        name = definition["symbol"]
        if not isinstance(name, str) or name not in symbols:
            raise ValueError(f"{where}: symbol {name!r} has no explicit numerical binding")
        return symbols[name], {"kind": "symbol", "name": name}
    ir.exact_keys(definition, {"expression"}, {"expression"}, where)
    ir.validate_binding(definition["expression"], where + ".expression")
    return definition["expression"], {"kind": "inline_expression"}


class ApplyLinker:
    """Compose pure definitions over shared SSA while keeping value provenance.

    Provenance belongs to each linked value, not to the interned instruction.
    Thus common subexpression sharing cannot make an unused callee argument
    appear to contribute to an output, or lose a source slot's identity.
    """

    def __init__(self, inputs, parameters, record_values):
        self.engine = ir.ExpressionCompiler(inputs)
        self.parameters = parameters
        self.record_values = record_values
        self.calls = {}
        self.call_details = []
        self.requirements = []
        self.expression_sites = []
        self.active_call = None

    def trace(self, value, where, kind):
        site = {"where": where, "kind": kind, **provenance(value)}
        if self.active_call is not None:
            site["call"] = self.active_call["id"]
            site["record_slot"] = self.active_call.get("record_slot")
        self.expression_sites.append(site)
        return site

    def require(self, value, where):
        register = self.engine._emit(17, value.register)
        result = Value(register, value.data, value.control | value.data)
        self.requirements.append(self.trace(result, where, "require"))
        return result

    def expression(self, expression, where, environment=None, depth=0):
        value = self._expression(expression, where, environment, depth)
        self.trace(value, where, "caller_expression" if environment is None else "callee_expression")
        return value

    def _expression(self, expression, where, environment=None, depth=0):
        if depth > ir.MAX_INSTRUCTIONS:
            raise ValueError(f"{where}: expression nesting exceeds {ir.MAX_INSTRUCTIONS}")
        if type(expression) in (int, float):
            _, bits = ir.fp32(expression, where)
            return Value(self.engine._emit(0, bits))
        if not isinstance(expression, dict):
            raise ValueError(f"{where}: expected a number, input, operation or permitted caller reference")
        if "input" in expression:
            ir.exact_keys(expression, {"input"}, {"input"}, where)
            name = expression["input"]
            if environment is not None:
                if not isinstance(name, str) or name not in environment:
                    raise ValueError(f"{where}: undeclared callee input {name!r}")
                return environment[name]
            if not isinstance(name, str) or name not in self.engine.input_columns:
                raise ValueError(f"{where}: undeclared application input {name!r}")
            return Value(self.engine._emit(1, self.engine.input_columns[name]), frozenset({f"input:{name}"}))
        if environment is None and "ref" in expression:
            ir.exact_keys(expression, {"ref"}, {"ref"}, where)
            reference = expression["ref"]
            if (not isinstance(reference, list) or len(reference) != 2
                    or any(not isinstance(name, str) or not name for name in reference)):
                raise ValueError(f"{where}.ref: expected [earlier_call_id, output_name]")
            call, output = reference
            if call not in self.calls or output not in self.calls[call]:
                raise ValueError(f"{where}: unknown or forward call output {reference!r}")
            return self.calls[call][output]
        if environment is None and "parameter" in expression:
            ir.exact_keys(expression, {"parameter"}, {"parameter"}, where)
            name = expression["parameter"]
            if not isinstance(name, str) or name not in self.parameters:
                raise ValueError(f"{where}: undeclared operator parameter {name!r}")
            _, bits = ir.fp32(self.parameters[name], where)
            return Value(self.engine._emit(0, bits), frozenset({f"parameter:{name}"}))
        if environment is None and "record" in expression:
            ir.exact_keys(expression, {"record"}, {"record"}, where)
            name = expression["record"]
            if not isinstance(name, str) or name not in self.record_values:
                raise ValueError(f"{where}: record reference must be index or operator_count")
            _, bits = ir.fp32(self.record_values[name], where)
            return Value(self.engine._emit(0, bits), frozenset({f"record:{name}"}))
        ir.exact_keys(expression, {"op", "args"}, {"op", "args"}, where)
        name = expression["op"]
        if not isinstance(name, str) or name not in ir.OPERATIONS:
            raise ValueError(f"{where}: unsupported operation {name!r}")
        opcode, arity = ir.OPERATIONS[name]
        args = expression["args"]
        if not isinstance(args, list) or len(args) != arity:
            raise ValueError(f"{where}: {name} requires exactly {arity} operands")
        values = [self.expression(arg, f"{where}.args[{index}]", environment, depth + 1)
                  for index, arg in enumerate(args)]
        if name == "require":
            return self.require(values[0], where)
        operands = [value.register for value in values] + [0] * (3 - arity)
        return Value(self.engine._emit(opcode, *operands), merged(values, "data"), merged(values, "control"))

    def link_call(self, call, binding, resolution, where):
        self.active_call = call
        arguments = call["arguments"]
        ir.exact_keys(arguments, binding["inputs"], binding["inputs"], where + ".arguments")
        environment = {name: self.expression(arguments[name], f"{where}.arguments[{name!r}]")
                       for name in binding["inputs"]}
        guards = [self.require(self.expression(condition, f"{where}.requires[{index}]", environment),
                               f"{where}.requires[{index}]")
                  for index, condition in enumerate(binding.get("requires", []))]
        guard_dependencies = merged(guards, "data") | merged(guards, "control")
        results = {}
        slot = call.get("record_slot")
        for name, expression in binding["outputs"].items():
            value = self.expression(expression, f"{where}.outputs[{name!r}]", environment)
            own = {call_identity(call["id"], name)}
            if slot is not None:
                own.add(f"slot:{slot}")
            results[name] = Value(value.register, value.data | frozenset(own), value.control | guard_dependencies)
        self.calls[call["id"]] = results
        self.call_details.append({
            "id": call["id"], "record_slot": slot, "resolution": resolution,
            "binding": binding, "arguments": arguments,
            "argument_values": {name: provenance(value) for name, value in environment.items()},
            "requires": [provenance(value) for value in guards],
            "outputs": {name: provenance(value) for name, value in results.items()},
        })
        self.active_call = None


def compile_apply(model, bindings, operator_key, rows):
    """Return (DWIR0001 bytes, situated-Apply manifest) without writing files."""
    operator = ir.resolve_operator(model, operator_key)
    ir.exact_keys(bindings, {"profile", "symbols", "applications", "operator_parameters"},
                  {"profile", "symbols", "applications", "operator_parameters"}, "bindings")
    if bindings["profile"] != PROFILE:
        raise ValueError(f"Bindings profile must be {PROFILE}")
    symbols = bindings["symbols"]
    named_mapping(symbols, "bindings.symbols")
    for name, binding in symbols.items():
        ir.validate_binding(binding, f"bindings.symbols[{name!r}]")
    applications = bindings["applications"]
    named_mapping(applications, "bindings.applications")
    if operator_key not in applications:
        raise ValueError(f"Operator {operator_key!r} has no explicit application binding")
    application = applications[operator_key]
    validate_application(application, f"applications[{operator_key!r}]")
    all_parameters = bindings["operator_parameters"]
    named_mapping(all_parameters, "bindings.operator_parameters")
    for key, values in all_parameters.items():
        named_mapping(values, f"operator_parameters[{key!r}]")
        for name, value in values.items():
            ir.fp32(value, f"operator_parameters[{key!r}][{name!r}]")
    defaults = all_parameters.get(operator_key, {})
    overrides = operator.get("parameters", {})
    named_mapping(overrides, f"operator[{operator_key!r}].parameters")
    parameters = {**defaults, **overrides}
    parameter_details = {}
    for name, value in parameters.items():
        rounded, bits = ir.fp32(value, f"selected operator parameter {name!r}")
        parameter_details[name] = {"declared_value": value, "value_fp32": rounded,
                                   "fp32_bits": f"0x{bits:08x}",
                                   "source": "source_record" if name in overrides else "binding_default"}
    record_values = {"index": operator["index"], "operator_count": len(model["operators"])}
    for name, value in record_values.items():
        rounded, _ = ir.fp32(value, f"record.{name}")
        if rounded != value:
            raise ValueError(f"record.{name}: integer must be exactly representable as FP32")
    definitions = {}
    for slot in SLOTS:
        if slot not in operator:
            raise ValueError(f"Operator {operator_key!r} is missing its {slot} definition")
        binding, resolution = resolve_definition(operator[slot], symbols, f"operator[{operator_key!r}].{slot}")
        definitions[slot] = {"source_definition": operator[slot], "binding": binding, "resolution": resolution}
    linker = ApplyLinker(application["inputs"], parameters, record_values)
    seen_calls = set()
    for index, call in enumerate(application["calls"]):
        where = f"application.calls[{index}]"
        ir.exact_keys(call, {"id", "arguments", "record_slot", "symbol"}, {"id", "arguments"}, where)
        name = call["id"]
        if not isinstance(name, str) or not name or name in seen_calls:
            raise ValueError(f"{where}.id: expected a unique nonempty name")
        seen_calls.add(name)
        if ("record_slot" in call) == ("symbol" in call):
            raise ValueError(f"{where}: specify exactly one of record_slot or symbol")
        if "record_slot" in call:
            slot = call["record_slot"]
            if not isinstance(slot, str) or slot not in definitions:
                raise ValueError(f"{where}.record_slot: expected placement, field or body")
            definition = definitions[slot]
            binding, resolution = definition["binding"], definition["resolution"]
        else:
            binding, resolution = resolve_definition({"symbol": call["symbol"]}, symbols, where)
        linker.link_call(call, binding, resolution, where)
    outputs = {name: linker.expression(expression, f"application.outputs[{name!r}]")
               for name, expression in application["outputs"].items()}
    final_dependencies = merged(list(outputs.values()), "data") | merged(list(outputs.values()), "control")
    unused_calls = [call["id"] for call in application["calls"]
                    if not any(call_identity(call["id"], name) in final_dependencies
                               for name in linker.calls[call["id"]])]
    if unused_calls:
        raise ValueError(f"Calls do not contribute to returned outputs or their guards: {unused_calls}")
    actions = [outputs[name] for name in application["action_outputs"]]
    action_data, action_control = merged(actions, "data"), merged(actions, "control")
    missing_slots = [slot for slot in SLOTS if f"slot:{slot}" not in action_data | action_control]
    if missing_slots:
        raise ValueError(f"Situated Apply action_outputs do not depend on source slots {missing_slots}; diagnostic outputs alone do not qualify")
    unused_parameters = sorted(name for name in parameters if f"parameter:{name}" not in final_dependencies)
    if unused_parameters:
        raise ValueError(f"Operator parameters do not contribute to returned outputs or their guards: {unused_parameters}")
    if not isinstance(rows, list) or not 1 <= len(rows) <= ir.UINT32_MAX:
        raise ValueError("Inputs file must be a nonempty list of named input objects")
    names = application["inputs"]
    input_data, rounded_rows = bytearray(), []
    changed_values, max_rounding_error = 0, 0.0
    for index, row in enumerate(rows):
        where = f"inputs[{index}]"
        ir.exact_keys(row, names, names, where)
        rounded = []
        for name in names:
            value, bits = ir.fp32(row[name], f"{where}[{name!r}]")
            error = abs(float(row[name]) - value)
            changed_values += error != 0.0
            max_rounding_error = max(max_rounding_error, error)
            input_data.extend(struct.pack("<I", bits))
            rounded.append(value)
        rounded_rows.append(rounded)
    instructions = linker.engine.instructions
    program = bytearray(ir.PROGRAM_MAGIC)
    program.extend(struct.pack("<4I", len(rows), len(instructions), len(names), len(outputs)))
    for instruction in instructions:
        program.extend(struct.pack("<4I", *instruction))
    for value in outputs.values():
        program.extend(struct.pack("<I", value.register))
    program.extend(input_data)
    disassembly = []
    for register, (opcode, a, b, c) in enumerate(instructions):
        item = {"register": register, "opcode": opcode, "operation": ir.OPCODE_NAMES[opcode], "words": [opcode, a, b, c]}
        if opcode == 0:
            item.update(value=struct.unpack("<f", struct.pack("<I", a))[0], fp32_bits=f"0x{a:08x}")
        elif opcode == 1:
            item.update(input=names[a], column=a)
        else:
            item["operands"] = [a, b, c][:ir.OPERATIONS[ir.OPCODE_NAMES[opcode]][1]]
        disassembly.append(item)
    sites_by_register = {index: [] for index in range(len(instructions))}
    for site in linker.expression_sites:
        sites_by_register[site["register"]].append(site)
    execution_sites = []
    for register, (opcode, _, _, _) in enumerate(instructions):
        checks = ["finite_result"]
        if opcode == 5:
            checks.append("nonzero_denominator")
        elif opcode == 9:
            checks.append("nonnegative_radicand")
        elif opcode == 17:
            checks.append("nonzero_guard")
        execution_sites.append({"register": register, "opcode": opcode,
                                "operation": ir.OPCODE_NAMES[opcode], "runtime_checks": checks,
                                "source_sites": sites_by_register[register]})
    description = {
        "profile": PROFILE, "numeric_backend_profile": ir.PROFILE,
        "scope": "situated_apply", "complete_application_lowered": False, "status": "partial_lowering",
        "operator": {key: operator[key] for key in ("index", "key", "label", "head", "source_pages", "body", "field", "placement", "parameters") if key in operator},
        "source_definitions": definitions, "application_binding": application,
        "resolved_parameters": parameter_details, "unused_parameters": [], "record_values": record_values,
        "calls": linker.call_details,
        "unused_calls": [],
        "output_provenance": {name: provenance(value) for name, value in outputs.items()},
        "action_outputs": application["action_outputs"],
        "action_source_slots": {
            "numeric": sorted(slot for slot in SLOTS if f"slot:{slot}" in action_data),
            "control": sorted(slot for slot in SLOTS if f"slot:{slot}" in action_control),
            "guard_only": sorted(slot for slot in SLOTS if f"slot:{slot}" in action_control - action_data),
        },
        "dependency_policy": "Structural numeric and guard dependencies are tracked on linked values, independent of common-subexpression registers. They do not prove nonzero numerical sensitivity; multiplication by zero can retain structural ancestry. Unused callee arguments do not qualify as output dependencies.",
        "global_execution_control": {
            "policy": "Every instruction executes eagerly in register order until the first failure; any failure zeroes the complete output row and sets lane status. Call arguments execute even when their callee never reads the supplied input. Select operands also execute eagerly.",
            "qualification": "Global execution and failure provenance is distinct from action ancestry. Unrelated guards and unused arguments cannot satisfy the source-slot contribution requirement. A call with no output reaching any returned output or its guards is rejected.",
            "requirements": linker.requirements,
            "instruction_sites": execution_sites,
        },
        "lowering": {
            "executed_by_this_component": ["the selected source record's explicit placement, field and body bindings", "ordered explicit application calls, guards and named output expressions"],
            "retained_but_not_executed": ["source-model seed and symbol declarations outside explicit bindings", "other source operator records and their parameters"],
            "not_lowered": ["whole application cycle and its schedule", "dynamic routing and surface transport beyond any explicit bound expressions", "operator record metamutation", "whole-state return and recurrent feedback"],
            "cycle_input": "No cycle file is consumed by this situated-Apply compiler.",
            "application_policy": "The application binding defines field and placement influence explicitly; no implicit gate, multiplication or coordinate interpretation is added.",
            "metadata": "Binding source, meaning and status are retained provenance; they are not instructions.",
        },
        "format": "DWIR0001", "row_count": len(rows), "instruction_count": len(instructions),
        "input_width": len(names), "output_width": len(outputs),
        "input_names": names, "output_names": list(outputs),
        "output_registers": [value.register for value in outputs.values()],
        "requirement_registers": [item["register"] for item in linker.requirements],
        "requirements": linker.requirements,
        "precondition_policy": "Each call's requires expressions execute before its outputs; zero fails the lane and finite nonzero satisfies a guard. Guard dependencies are distinguished from numeric output dependencies. All calls and select operands are eagerly evaluated.",
        "instructions": disassembly,
        "numeric_input_policy": "Finite constants, parameters and inputs round to IEEE FP32 before execution; negative zero bits are retained. Record index and operator_count must be exactly representable as FP32.",
        "optimization": "Identical instruction tuples are shared; no algebraic rewriting or constant folding.",
        "compiled_input_rows_fp32": rounded_rows,
        "source_input_fp32_rounding": {"value_count": len(rows) * len(names), "changed_value_count": changed_values,
                                       "max_absolute_difference": max_rounding_error,
                                       "reference": "JSON numbers decoded as Python numeric values before packing; compiled_input_rows_fp32 are the execution inputs."},
        "program_sha256": ir.sha256(program),
    }
    return bytes(program), description


def write_compilation(model_path, bindings_path, inputs_path, operator_key, output):
    model_path, bindings_path, inputs_path, output = map(Path, (model_path, bindings_path, inputs_path, output))
    model, model_raw = ir.read_json(model_path)
    bindings, bindings_raw = ir.read_json(bindings_path)
    rows, inputs_raw = ir.read_json(inputs_path)
    program, manifest = compile_apply(model, bindings, operator_key, rows)
    files = {"source_model.json": model_raw, "bindings.json": bindings_raw,
             "inputs.json": inputs_raw, "program.bin": program}
    manifest["created_at"] = datetime.now(timezone.utc).isoformat()
    manifest["sources"] = {
        "model": {"path": str(model_path.resolve()), "sha256": ir.sha256(model_raw)},
        "bindings": {"path": str(bindings_path.resolve()), "sha256": ir.sha256(bindings_raw)},
        "inputs": {"path": str(inputs_path.resolve()), "sha256": ir.sha256(inputs_raw)},
    }
    manifest["files"] = {name: {"sha256": ir.sha256(data), "bytes": len(data)} for name, data in files.items()}
    manifest_raw = ir.json_bytes(manifest)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        (output / name).write_bytes(data)
    (output / "manifest.json").write_bytes(manifest_raw)
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    compile_parser = commands.add_parser("compile", help="Link one source record's explicit situated application")
    compile_parser.add_argument("--model", type=Path, default=ir.DEFAULT_MODEL)
    compile_parser.add_argument("--bindings", type=Path, required=True)
    compile_parser.add_argument("--operator", required=True)
    compile_parser.add_argument("--inputs", type=Path, required=True)
    compile_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    manifest = write_compilation(args.model, args.bindings, args.inputs, args.operator, args.output)
    print(json.dumps({"output": str(args.output.resolve()), "profile": PROFILE,
                      "scope": manifest["scope"], "complete_application_lowered": False,
                      "row_count": manifest["row_count"], "instruction_count": manifest["instruction_count"],
                      "action_source_slots": manifest["action_source_slots"],
                      "program_sha256": manifest["program_sha256"]}, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, RecursionError, struct.error) as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(1)
