"""DWI-XIR-0.2 expression compiler: isolated log/atan2 vocabulary extension.

This module is used by the resident-v2 frontend. It does not patch source_ir,
replace the v1 compiler, or silently enable new opcodes in a v1 executable.
The instruction encoding remains four uint32 words; evaluator version and
the enclosing resident format determine which opcodes are valid.
"""
from __future__ import annotations

try:
    from . import source_ir as v1
except ImportError:
    import source_ir as v1


PROFILE = "DWI-XIR-0.2"
NEW_OPERATIONS = {"log": (18, 1), "atan2": (19, 2)}
OPERATIONS = {**v1.OPERATIONS, **NEW_OPERATIONS}
OPCODE_NAMES = {0: "constant", 1: "input", **{value[0]: key for key, value in OPERATIONS.items()}}

# Explicitly export version-independent helpers used by resident frontends.
# Do not alias v1.compile_body/write_compilation/main: they close over the v1
# compiler and profile and would give a misleading versioned API.
ROOT = v1.ROOT
DEFAULT_MODEL = v1.DEFAULT_MODEL
PROGRAM_MAGIC = v1.PROGRAM_MAGIC
RESULT_MAGIC = v1.RESULT_MAGIC
MAX_INSTRUCTIONS = v1.MAX_INSTRUCTIONS
MAX_INPUTS = v1.MAX_INPUTS
MAX_OUTPUTS = v1.MAX_OUTPUTS
UINT32_MAX = v1.UINT32_MAX
BINDING_KEYS = frozenset(v1.BINDING_KEYS)
sha256 = v1.sha256
read_json = v1.read_json
json_bytes = v1.json_bytes
exact_keys = v1.exact_keys
fp32 = v1.fp32
validate_binding = v1.validate_binding
resolve_operator = v1.resolve_operator
read_result = v1.read_result
inspect_result = v1.inspect_result


class ExpressionCompiler(v1.ExpressionCompiler):
    """Strict v1 postorder SSA plus unary log and binary atan2(y, x)."""

    def expression(self, expression, where="expression", depth=0):
        if depth > MAX_INSTRUCTIONS:
            raise ValueError(f"{where}: expression nesting exceeds {MAX_INSTRUCTIONS}")
        name = expression.get("op") if isinstance(expression, dict) else None
        if not isinstance(name, str) or name not in NEW_OPERATIONS:
            # v1 recursively calls self.expression, so nested v2 expressions
            # work under existing operators without changing any v1 globals.
            return super().expression(expression, where, depth)
        exact_keys(expression, {"op", "args"}, {"op", "args"}, where)
        opcode, arity = NEW_OPERATIONS[name]
        args = expression["args"]
        if not isinstance(args, list) or len(args) != arity:
            raise ValueError(f"{where}: {name} requires exactly {arity} operands")
        registers = [self.expression(arg, f"{where}.args[{index}]", depth + 1)
                     for index, arg in enumerate(args)]
        return self._emit(opcode, *(registers + [0] * (3 - arity)))


def compile_binding(binding, where="binding"):
    """Compile a pure binding and retain names/guards for an enclosing frontend.

    Domain checks are runtime checks on the actual FP32 argument registers.
    Constant folding is deliberately absent, matching v1 failure ordering.
    """
    validate_binding(binding, where)
    compiler = ExpressionCompiler(binding["inputs"])
    requirements = []
    for index, condition in enumerate(binding.get("requires", [])):
        value = compiler.expression(condition, f"{where}.requires[{index}]")
        requirements.append(compiler._emit(17, value))
    output_names = list(binding["outputs"])
    output_registers = [compiler.expression(binding["outputs"][name], f"{where}.outputs[{name!r}]")
                        for name in output_names]
    return {
        "profile": PROFILE,
        "inputs": list(binding["inputs"]),
        "output_names": output_names,
        "output_registers": output_registers,
        "requirement_registers": requirements,
        "instructions": list(compiler.instructions),
    }
