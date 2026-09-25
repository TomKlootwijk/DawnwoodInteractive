"""Compile one explicitly bound source-model operator body to Dawnwood XIR.

This is a numeric body component, not a compiler for the entire application.
The source field, placement, cycle and feedback semantics remain unlowered and
are identified as such in the manifest. No Python expressions are evaluated.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = ROOT / "source_workbench/Dawnwood_Interactive_v0.2/model/substrate.json"
PROFILE = "DWI-XIR-0.1"
PROGRAM_MAGIC = b"DWIR0001"
RESULT_MAGIC = b"DWIRO001"
MAX_INSTRUCTIONS = 256
MAX_INPUTS = 64
MAX_OUTPUTS = 32
UINT32_MAX = (1 << 32) - 1
OPERATIONS = {
    "add": (2, 2), "sub": (3, 2), "mul": (4, 2), "div": (5, 2),
    "sin": (6, 1), "cos": (7, 1), "exp": (8, 1), "sqrt": (9, 1),
    "abs": (10, 1), "min": (11, 2), "max": (12, 2), "neg": (13, 1),
    "floor": (14, 1), "less": (15, 2), "select": (16, 3), "require": (17, 1),
}
OPCODE_NAMES = {0: "constant", 1: "input", **{value[0]: key for key, value in OPERATIONS.items()}}
BINDING_KEYS = {"inputs", "outputs", "requires", "source", "meaning", "status"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f"Nonfinite JSON number is not supported: {value}")


def read_json(path: Path):
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                           parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError(f"{path}: invalid UTF-8 JSON: {error}") from error
    return value, raw


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def exact_keys(value, allowed, required, where):
    if not isinstance(value, dict):
        raise ValueError(f"{where}: expected an object")
    unknown = set(value) - set(allowed)
    missing = set(required) - set(value)
    if unknown:
        raise ValueError(f"{where}: unsupported keys {sorted(unknown)}")
    if missing:
        raise ValueError(f"{where}: missing keys {sorted(missing)}")


def fp32(value, where):
    if type(value) not in (int, float):
        raise ValueError(f"{where}: expected a finite numeric value, not a Boolean or other type")
    try:
        number = float(value)
        if not math.isfinite(number):
            raise ValueError(f"{where}: nonfinite numbers are not supported")
        packed = struct.pack("<f", number)
    except (OverflowError, struct.error) as error:
        raise ValueError(f"{where}: value cannot be represented as finite FP32") from error
    rounded = struct.unpack("<f", packed)[0]
    if not math.isfinite(rounded):
        raise ValueError(f"{where}: FP32 conversion overflowed")
    return rounded, struct.unpack("<I", packed)[0]


def validate_binding(binding, where):
    exact_keys(binding, BINDING_KEYS, {"inputs", "outputs"}, where)
    inputs = binding["inputs"]
    outputs = binding["outputs"]
    if not isinstance(inputs, list) or len(inputs) > MAX_INPUTS:
        raise ValueError(f"{where}.inputs: expected at most {MAX_INPUTS} names")
    if any(not isinstance(name, str) or not name for name in inputs) or len(set(inputs)) != len(inputs):
        raise ValueError(f"{where}.inputs: names must be unique nonempty strings")
    if not isinstance(outputs, dict) or not 1 <= len(outputs) <= MAX_OUTPUTS:
        raise ValueError(f"{where}.outputs: expected 1..{MAX_OUTPUTS} named expressions")
    if any(not isinstance(name, str) or not name for name in outputs):
        raise ValueError(f"{where}.outputs: names must be nonempty strings")
    requirements = binding.get("requires", [])
    if not isinstance(requirements, list) or len(requirements) > MAX_INSTRUCTIONS:
        raise ValueError(f"{where}.requires: expected a list of at most {MAX_INSTRUCTIONS} conditions")


class ExpressionCompiler:
    """Strict postorder SSA: operands reference only already-emitted registers."""

    def __init__(self, inputs):
        self.inputs = list(inputs)
        self.input_columns = {name: index for index, name in enumerate(inputs)}
        self.instructions = []
        self._intern = {}

    def _emit(self, opcode, a=0, b=0, c=0):
        instruction = (opcode, a, b, c)
        if instruction in self._intern:
            return self._intern[instruction]
        if len(self.instructions) >= MAX_INSTRUCTIONS:
            raise ValueError(f"Expression program exceeds {MAX_INSTRUCTIONS} instructions")
        register = len(self.instructions)
        self.instructions.append(instruction)
        self._intern[instruction] = register
        return register

    def expression(self, expression, where="expression", depth=0):
        if depth > MAX_INSTRUCTIONS:
            raise ValueError(f"{where}: expression nesting exceeds {MAX_INSTRUCTIONS}")
        if type(expression) in (int, float):
            _, bits = fp32(expression, where)
            return self._emit(0, bits)
        if not isinstance(expression, dict):
            raise ValueError(f"{where}: expected a number, an input reference or an operation")
        if "input" in expression:
            exact_keys(expression, {"input"}, {"input"}, where)
            name = expression["input"]
            if not isinstance(name, str) or name not in self.input_columns:
                raise ValueError(f"{where}: undeclared input {name!r}")
            return self._emit(1, self.input_columns[name])
        exact_keys(expression, {"op", "args"}, {"op", "args"}, where)
        name = expression["op"]
        if not isinstance(name, str) or name not in OPERATIONS:
            raise ValueError(f"{where}: unsupported operation {name!r}")
        opcode, arity = OPERATIONS[name]
        args = expression["args"]
        if not isinstance(args, list) or len(args) != arity:
            raise ValueError(f"{where}: {name} requires exactly {arity} operands")
        registers = [self.expression(arg, f"{where}.args[{index}]", depth + 1)
                     for index, arg in enumerate(args)]
        return self._emit(opcode, *(registers + [0] * (3 - arity)))


def resolve_operator(model, operator_key):
    if not isinstance(model, dict) or not isinstance(model.get("operators"), list):
        raise ValueError("Source model must contain an operators array")
    keys, indices = set(), set()
    selected = None
    for position, operator in enumerate(model["operators"]):
        where = f"source_model.operators[{position}]"
        if not isinstance(operator, dict):
            raise ValueError(f"{where}: expected an operator object")
        key, index = operator.get("key"), operator.get("index")
        if not isinstance(key, str) or not key or key in keys:
            raise ValueError(f"{where}: operator key must be nonempty and unique")
        if type(index) is not int or not 0 <= index <= UINT32_MAX or index in indices:
            raise ValueError(f"{where}: index must be a unique uint32")
        keys.add(key)
        indices.add(index)
        if key == operator_key:
            selected = operator
    if selected is None:
        raise ValueError(f"Source model has no operator {operator_key!r}")
    if "body" not in selected:
        raise ValueError(f"Operator {operator_key!r} has no body")
    return selected


def resolve_binding(operator, bindings):
    exact_keys(bindings, {"profile", "symbols"}, {"profile", "symbols"}, "bindings")
    if bindings["profile"] != PROFILE:
        raise ValueError(f"Bindings profile must be {PROFILE}")
    symbols = bindings["symbols"]
    if not isinstance(symbols, dict) or any(not isinstance(name, str) or not name for name in symbols):
        raise ValueError("bindings.symbols must map nonempty names to explicit bindings")
    # Validate declaration shape for every symbol. Expression lowering below is
    # scoped to the selected body and is never claimed for unused definitions.
    for name, binding in symbols.items():
        validate_binding(binding, f"bindings.symbols[{name!r}]")
    body = operator["body"]
    where = f"operator[{operator['key']!r}].body"
    if isinstance(body, dict) and "symbol" in body:
        exact_keys(body, {"symbol"}, {"symbol"}, where)
        symbol = body["symbol"]
        if not isinstance(symbol, str) or symbol not in symbols:
            raise ValueError(f"{where}: source symbol {symbol!r} has no explicit numerical binding")
        return symbols[symbol], {"kind": "symbol", "name": symbol}
    exact_keys(body, {"expression"}, {"expression"}, where)
    validate_binding(body["expression"], where + ".expression")
    return body["expression"], {"kind": "inline_expression"}


def compile_body(model, bindings, operator_key, rows):
    operator = resolve_operator(model, operator_key)
    binding, resolution = resolve_binding(operator, bindings)
    validate_binding(binding, "selected binding")
    compiler = ExpressionCompiler(binding["inputs"])
    requirement_registers = []
    for index, condition in enumerate(binding.get("requires", [])):
        value = compiler.expression(condition, f"requires[{index}]")
        requirement_registers.append(compiler._emit(17, value))
    output_names = list(binding["outputs"])
    output_registers = [compiler.expression(binding["outputs"][name], f"outputs[{name!r}]")
                        for name in output_names]
    if not isinstance(rows, list) or not 1 <= len(rows) <= UINT32_MAX:
        raise ValueError("Inputs file must be a nonempty list of named input objects")
    names = binding["inputs"]
    input_data = bytearray()
    rounded_rows = []
    input_rounding_changed_values = 0
    input_rounding_max_absolute = 0.0
    for row_index, row in enumerate(rows):
        where = f"inputs[{row_index}]"
        exact_keys(row, set(names), set(names), where)
        rounded = []
        for name in names:
            value, bits = fp32(row[name], f"{where}[{name!r}]")
            rounding_error = abs(float(row[name]) - value)
            input_rounding_changed_values += rounding_error != 0.0
            input_rounding_max_absolute = max(input_rounding_max_absolute, rounding_error)
            input_data.extend(struct.pack("<I", bits))
            rounded.append(value)
        rounded_rows.append(rounded)
    program = bytearray(PROGRAM_MAGIC)
    program.extend(struct.pack("<4I", len(rows), len(compiler.instructions), len(names), len(output_names)))
    for instruction in compiler.instructions:
        program.extend(struct.pack("<4I", *instruction))
    for register in output_registers:
        program.extend(struct.pack("<I", register))
    program.extend(input_data)
    disassembly = []
    for register, (opcode, a, b, c) in enumerate(compiler.instructions):
        item = {"register": register, "opcode": opcode, "operation": OPCODE_NAMES[opcode], "words": [opcode, a, b, c]}
        if opcode == 0:
            item.update(value=struct.unpack("<f", struct.pack("<I", a))[0], fp32_bits=f"0x{a:08x}")
        elif opcode == 1:
            item.update(input=names[a], column=a)
        else:
            item["operands"] = [a, b, c][:OPERATIONS[OPCODE_NAMES[opcode]][1]]
        disassembly.append(item)
    description = {
        "profile": PROFILE,
        "scope": "selected_operator_body",
        "complete_application_lowered": False,
        "status": "partial_lowering",
        "operator": {key: operator[key] for key in ("index", "key", "label", "head", "source_pages", "body", "field", "placement") if key in operator},
        "binding_resolution": resolution,
        "selected_binding": binding,
        "lowering": {
            "executed_by_this_component": ["explicit numerical preconditions, then selected scalar-expression outputs over supplied input rows"],
            "retained_but_not_executed": ["operator field", "operator placement", "source-model seed and symbol declarations"],
            "not_lowered": ["whole application cycle and its schedule", "operator mutation", "routing and surface transport", "whole-state return and feedback", "other operator bodies"],
            "cycle_input": "No cycle file is consumed by this body-only compiler.",
            "metadata": "Binding source, meaning and status are retained provenance; they are not instructions.",
        },
        "format": "DWIR0001",
        "row_count": len(rows), "instruction_count": len(compiler.instructions),
        "input_width": len(names), "output_width": len(output_names),
        "input_names": names, "output_names": output_names, "output_registers": output_registers,
        "requirement_registers": requirement_registers,
        "precondition_policy": "Each requires expression emits opcode17 before output expressions; zero fails the lane and any finite nonzero value satisfies the guard.",
        "instructions": disassembly,
        "numeric_input_policy": "Finite constants and inputs rounded to IEEE FP32 before execution; negative zero bits retained.",
        "optimization": "Identical instruction tuples are shared; no algebraic rewriting or constant folding.",
        "compiled_input_rows_fp32": rounded_rows,
        "source_input_fp32_rounding": {
            "value_count": len(rows) * len(names),
            "changed_value_count": input_rounding_changed_values,
            "max_absolute_difference": input_rounding_max_absolute,
            "reference": "JSON numbers decoded as Python numeric values before packing; compiled_input_rows_fp32 are the actual execution inputs.",
        },
        "program_sha256": sha256(program),
    }
    return bytes(program), description


def write_compilation(model_path, bindings_path, inputs_path, operator_key, output):
    model, model_raw = read_json(model_path)
    bindings, bindings_raw = read_json(bindings_path)
    rows, inputs_raw = read_json(inputs_path)
    program, manifest = compile_body(model, bindings, operator_key, rows)
    output = output.resolve()
    files = {"source_model.json": model_raw, "bindings.json": bindings_raw,
             "inputs.json": inputs_raw, "program.bin": program}
    manifest["created_at"] = datetime.now(timezone.utc).isoformat()
    manifest["sources"] = {
        "model": {"path": str(model_path.resolve()), "sha256": sha256(model_raw)},
        "bindings": {"path": str(bindings_path.resolve()), "sha256": sha256(bindings_raw)},
        "inputs": {"path": str(inputs_path.resolve()), "sha256": sha256(inputs_raw)},
    }
    manifest["files"] = {name: {"sha256": sha256(data), "bytes": len(data)} for name, data in files.items()}
    # Resolve and validate everything before creating an immutable new output
    # directory. A later I/O failure preserves its partial evidence for inspection.
    manifest_raw = json_bytes(manifest)
    output.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        (output / name).write_bytes(data)
    (output / "manifest.json").write_bytes(manifest_raw)
    return manifest


def read_result(path):
    """Read exact DWIRO001 rows, retaining status codes and raw FP32 bits."""
    path = Path(path)
    raw = path.read_bytes()
    if len(raw) < 16 or raw[:8] != RESULT_MAGIC:
        raise ValueError("Result header must be DWIRO001 followed by count and output width")
    count, width = struct.unpack_from("<2I", raw, 8)
    if not count or not 1 <= width <= MAX_OUTPUTS:
        raise ValueError("Result count must be positive and output width must be 1..32")
    expected = 16 + count * 4 + count * width * 4
    if len(raw) != expected:
        raise ValueError(f"Result length mismatch: expected {expected} bytes, received {len(raw)}")
    statuses = list(struct.unpack_from(f"<{count}I", raw, 16))
    values_offset = 16 + count * 4
    outputs, bits = [], []
    nonfinite = 0
    for row in range(count):
        offset = values_offset + row * width * 4
        values = list(struct.unpack_from(f"<{width}f", raw, offset))
        words = list(struct.unpack_from(f"<{width}I", raw, offset))
        nonfinite += sum(not math.isfinite(value) for value in values)
        outputs.append(values)
        bits.append(words)
    return {"format": "DWIRO001", "count": count, "output_width": width,
            "statuses": statuses, "all_status_ok": all(status == 0 for status in statuses),
            "nonfinite_output_values": nonfinite, "outputs": outputs, "output_bits": bits,
            "sha256": sha256(raw)}


def inspect_result(path, manifest_path=None):
    result = read_result(path)
    if manifest_path:
        manifest, _ = read_json(manifest_path)
        if manifest.get("row_count") != result["count"] or manifest.get("output_width") != result["output_width"]:
            raise ValueError("Result dimensions do not match the supplied compilation manifest")
        names = manifest.get("output_names")
        if not isinstance(names, list) or len(names) != result["output_width"]:
            raise ValueError("Compilation manifest has no matching output names")
        result["output_names"] = names
        result["named_outputs"] = [dict(zip(names, row)) for row in result["outputs"]]
    # JSON has no NaN/Infinity encoding. Keep the raw bits and explicit count,
    # and use null only in the inspection presentation for faulty numeric slots.
    def finite_json(value):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        if isinstance(value, list):
            return [finite_json(item) for item in value]
        if isinstance(value, dict):
            return {key: finite_json(item) for key, item in value.items()}
        return value
    result["nonfinite_presentation"] = "Nonfinite values display as null; output_bits retain the exact returned words."
    return finite_json(result)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    compile_parser = commands.add_parser("compile", help="Lower one explicitly bound source operator body")
    compile_parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    compile_parser.add_argument("--bindings", type=Path, required=True)
    compile_parser.add_argument("--operator", required=True)
    compile_parser.add_argument("--inputs", type=Path, required=True)
    compile_parser.add_argument("--output", type=Path, required=True)
    inspect_parser = commands.add_parser("inspect", help="Read native numeric output and lane status")
    inspect_parser.add_argument("result", type=Path)
    inspect_parser.add_argument("--manifest", type=Path)
    args = parser.parse_args(argv)
    if args.command == "compile":
        manifest = write_compilation(args.model, args.bindings, args.inputs, args.operator, args.output)
        print(json.dumps({"output": str(args.output.resolve()), "profile": PROFILE,
                          "scope": manifest["scope"], "complete_application_lowered": False,
                          "row_count": manifest["row_count"], "instruction_count": manifest["instruction_count"],
                          "program_sha256": manifest["program_sha256"]}, indent=2, allow_nan=False))
        return 0
    result = inspect_result(args.result, args.manifest)
    print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
    return 0 if result["all_status_ok"] and not result["nonfinite_output_values"] else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, RecursionError, struct.error) as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(1)
