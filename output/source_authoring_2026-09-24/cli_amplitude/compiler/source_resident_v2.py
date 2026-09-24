"""Compile and inspect typed resident definitions and computed source routing.

Application bindings supply the numerical laws and call plans. This generic
validator does not infer source-cycle semantics from a valid executable tape.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import struct
import sys

try:
    from . import source_ir_v2 as ir
except ImportError:
    import source_ir_v2 as ir


PROFILE = "DWI-RESIDENT-0.2"
MAGIC = b"DWRD0002"
TARGET = ir.UINT32_MAX
EXACT_LIMIT = 16777215
FRAME_WORDS = 256
RECORD_WORDS = 24
VALUE_WORDS = 20
MAX_RECORDS = 32
MAX_FUNCTIONS = 256
MAX_FAMILIES = 256
MAX_STEPS = 4096
SLOTS = ("body", "field", "placement")
DEFINITION_KEYS = {
    "profile", "functions", "records", "state_names", "record_value_names",
    "mutation_plan", "action_plan", "instances", "source", "meaning", "status", "families",
}
RECORD_KEYS = {"key", *SLOTS, "source_slots", "generation", "values"}
OVERRIDE_KEYS = {*SLOTS, "generation", "values"}


def uint(value, where, maximum=ir.UINT32_MAX, minimum=0):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{where}: expected an integer in {minimum}..{maximum}")
    return value


def names(value, where, minimum, maximum):
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise ValueError(f"{where}: expected {minimum}..{maximum} names")
    if any(not isinstance(item, str) or not item for item in value) or len(set(value)) != len(value):
        raise ValueError(f"{where}: names must be unique nonempty strings")
    return list(value)


def float_word(word):
    return struct.unpack("<f", struct.pack("<I", word))[0]


def finite_word(word, where):
    value = float_word(word)
    if not math.isfinite(value):
        raise ValueError(f"{where}: nonfinite FP32 word")
    return value


def checked_size(value, where):
    if not 0 <= value <= ir.UINT32_MAX:
        raise ValueError(f"{where}: computed word count exceeds uint32 indexing")
    return value


def span(start, width, limit, where, allow_empty=False):
    if (not allow_empty and width == 0) or start > limit or width > limit - start:
        raise ValueError(f"{where}: range [{start}, {start + width}) exceeds {limit} words")
    return range(start, start + width)


def exact_float_integer(value, where):
    rounded, _ = ir.fp32(value, where)
    if rounded != value:
        raise ValueError(f"{where}: integer must be represented exactly as FP32")


def same_structure(left, right):
    """JSON-tree identity, ignoring object key order but preserving value types."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(same_structure(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(same_structure(a, b) for a, b in zip(left, right))
    if isinstance(left, float) and left == 0.0 and right == 0.0:
        return math.copysign(1.0, left) == math.copysign(1.0, right)
    return left == right


def validate_functions(descriptors, heap):
    """Validate bank bytecode independently of the expression frontend."""
    signatures = {}
    functions = []
    arity_by_opcode = {value[0]: value[1] for value in ir.OPERATIONS.values()}
    for handle, descriptor in enumerate(descriptors):
        where = f"functions[{handle}]"
        code, outputs, count, input_width, output_width, signature = descriptor
        uint(count, where + ".instruction_count", ir.MAX_INSTRUCTIONS, 1)
        uint(input_width, where + ".input_width", ir.MAX_INPUTS)
        uint(output_width, where + ".output_width", ir.MAX_OUTPUTS, 1)
        uint(signature, where + ".signature", minimum=1)
        dimensions = (input_width, output_width)
        if signature in signatures and signatures[signature] != dimensions:
            raise ValueError(f"{where}: signature {signature} has inconsistent input/output widths")
        signatures[signature] = dimensions
        span(code, 4 * count, len(heap), where + ".code")
        span(outputs, output_width, len(heap), where + ".outputs")
        for register in range(count):
            opcode, a, b, c = heap[code + 4 * register:code + 4 * register + 4]
            instruction_where = f"{where}.instructions[{register}]"
            if opcode == 0:
                finite_word(a, instruction_where)
                if b or c:
                    raise ValueError(f"{instruction_where}: unused operand words must be zero")
            elif opcode == 1:
                if a >= input_width or b or c:
                    raise ValueError(f"{instruction_where}: invalid input column or unused operands")
            elif opcode in arity_by_opcode:
                arity = arity_by_opcode[opcode]
                operands = (a, b, c)
                if any(operand >= register for operand in operands[:arity]):
                    raise ValueError(f"{instruction_where}: operands must reference earlier instructions")
                if any(operands[arity:]):
                    raise ValueError(f"{instruction_where}: unused operand words must be zero")
            else:
                raise ValueError(f"{instruction_where}: unsupported opcode {opcode}")
        output_registers = heap[outputs:outputs + output_width]
        if any(register >= count for register in output_registers):
            raise ValueError(f"{where}: output register outside the expression program")
        functions.append({
            "handle": handle, "code_offset": code, "output_register_offset": outputs,
            "instruction_count": count, "input_width": input_width,
            "output_width": output_width, "signature": signature,
            "output_registers": list(output_registers),
        })
    return functions, signatures


def validate_families(descriptors, heap, functions):
    families, interfaces = [], {}
    for handle, descriptor in enumerate(descriptors):
        where = f"families[{handle}]"
        interface, offset, count, reserved = descriptor
        uint(interface, where + ".interface", minimum=1)
        uint(count, where + ".method_count", 32, 1)
        if reserved:
            raise ValueError(f"{where}: reserved word must be zero")
        span(offset, 2 * count, len(heap), where + ".methods")
        methods, contract = {}, []
        previous = -1
        for index in range(count):
            role, function = heap[offset + 2 * index:offset + 2 * index + 2]
            if role <= previous or function >= len(functions):
                raise ValueError(f"{where}: roles must be increasing and function handles valid")
            previous = role
            methods[role] = function
            contract.append((role, functions[function]["signature"]))
        if interface in interfaces and interfaces[interface] != contract:
            raise ValueError(f"{where}: families sharing an interface must have identical role/signature sets")
        interfaces[interface] = contract
        families.append({"handle": handle, "interface": interface, "methods_offset": offset,
                         "method_count": count, "methods": methods})
    return families, interfaces


def validate_plan(plan, mutation, metadata, functions, signatures, state_width, families, interfaces):
    label = "mutation_plan" if mutation else "action_plan"
    if not isinstance(plan, list) or not 1 <= len(plan) <= MAX_STEPS:
        raise ValueError(f"{label}: expected 1..{MAX_STEPS} instructions")
    initialized = set()
    written = set()
    write_limit = RECORD_WORDS if mutation else state_width

    def frame_range(base, width, where, read=False, allow_empty=False):
        registers = span(base, width, FRAME_WORDS, where, allow_empty)
        if read and any(register not in initialized for register in registers):
            raise ValueError(f"{where}: reads an uninitialized frame register")
        return registers

    def selector_indices(selector, where):
        if selector == TARGET:
            if not mutation:
                raise ValueError(f"{where}: TARGET is forbidden during action")
            return range(len(metadata))
        if selector >= len(metadata):
            raise ValueError(f"{where}: record ordinal is outside the table")
        return (selector,)

    def call(input_base, output_base, widths, where):
        input_width, output_width = widths
        frame_range(input_base, input_width, where + ".inputs", True, True)
        initialized.update(frame_range(output_base, output_width, where + ".outputs"))

    for step, words in enumerate(plan):
        where = f"{label}[{step}]"
        if not isinstance(words, list) or len(words) != 8:
            raise ValueError(f"{where}: instruction must contain exactly eight uint32 words")
        for index, word in enumerate(words):
            uint(word, f"{where}[{index}]")
        opcode = words[0]
        used = {0: 3, 1: 4, 2: 6, 3: 4, 4: 8, 5: 4, 6: 4, 7: 2, 8: 2, 9: 2,
                10: 4, 11: 8, 12: 6}.get(opcode)
        if used is None:
            raise ValueError(f"{where}: unsupported opcode {opcode}")
        if any(words[used:]):
            raise ValueError(f"{where}: unused instruction words must be zero")
        if opcode == 0:
            finite_word(words[2], where + ".constant")
            initialized.update(frame_range(words[1], 1, where + ".destination"))
        elif opcode == 1:
            destination, state_index, width = words[1:4]
            span(state_index, width, state_width, where + ".state")
            initialized.update(frame_range(destination, width, where + ".destination"))
        elif opcode in (2, 12):
            destination, selector, record_word, width, bank = words[1:6]
            if opcode == 2:
                selector_indices(selector, where)
            else:
                frame_range(selector, 1, where + ".source_index", True)
            if bank not in (0, 1) or (mutation and bank != 0):
                raise ValueError(f"{where}: mutation reads bank0; action reads bank0 or bank1")
            span(record_word, width, RECORD_WORDS, where + ".record")
            initialized.update(frame_range(destination, width, where + ".destination"))
        elif opcode == 3:
            handle, input_base, output_base = words[1:4]
            if handle >= len(functions):
                raise ValueError(f"{where}: helper function handle is outside the bank")
            function = functions[handle]
            call(input_base, output_base, (function["input_width"], function["output_width"]), where)
        elif opcode in (4, 11):
            selector, slot, bank, input_base, output_base, signature, role = words[1:8]
            if opcode == 4:
                indices = selector_indices(selector, where)
            else:
                frame_range(selector, 1, where + ".source_index", True)
                indices = ()
            if slot >= len(SLOTS):
                raise ValueError(f"{where}: record slot must be 0body, 1field or 2placement")
            if bank != (0 if mutation else 1):
                raise ValueError(f"{where}: mutation calls bank0; action calls bank1")
            if signature not in signatures:
                raise ValueError(f"{where}: call signature is not present in the function bank")
            if slot != 0 and role != 0:
                raise ValueError(f"{where}: field and placement roles must be zero")
            for index in indices:
                contract = metadata[index][slot + 1]
                if (slot == 0 and (role, signature) not in interfaces[contract]) or (slot != 0 and contract != signature):
                    raise ValueError(f"{where}: role/signature does not match the selected immutable slot")
            call(input_base, output_base, signatures[signature], where)
        elif opcode in (5, 6):
            if (opcode == 5) != mutation:
                raise ValueError(f"{where}: opcode {opcode} is not allowed in this plan")
            destination, source, width = words[1:4]
            destination_words = set(span(destination, width, write_limit, where + ".write"))
            frame_range(source, width, where + ".source", True)
            if written & destination_words:
                raise ValueError(f"{where}: each destination word must be written exactly once")
            written.update(destination_words)
        elif opcode == 7:
            frame_range(words[1], 1, where + ".require", True)
        elif opcode in (8, 9):
            if opcode == 9 and not mutation:
                raise ValueError(f"{where}: source-index read is mutation-only")
            initialized.update(frame_range(words[1], 1, where + ".destination"))
        elif opcode == 10:
            destination, source, width = words[1:4]
            frame_range(source, width, where + ".source", True)
            initialized.update(frame_range(destination, width, where + ".destination"))
    if written != set(range(write_limit)):
        missing = sorted(set(range(write_limit)) - written)
        raise ValueError(f"{label}: missing writes to destination words {missing}")


def validate_record(words, metadata, functions, where, families):
    for slot in range(3):
        handle = words[slot]
        bank = families if slot == 0 else functions
        if handle >= len(bank):
            raise ValueError(f"{where}.{SLOTS[slot]}: family/function handle is outside the bank")
        if bank[handle]["interface" if slot == 0 else "signature"] != metadata[slot + 1]:
            raise ValueError(f"{where}.{SLOTS[slot]}: handle has the wrong slot interface/signature")
    uint(words[3], where + ".generation", EXACT_LIMIT)
    for index, word in enumerate(words[4:]):
        finite_word(word, f"{where}.values[{index}]")


def validate_failure_header(header, records, metadata, mutation_plan, action_plan, functions, heap, families, where):
    epoch, status, phase, target, step, detail = header
    uint(epoch, where + ".epoch", EXACT_LIMIT)
    if status == 0:
        if any(header[2:]):
            raise ValueError(f"{where}: successful image must have zero failure metadata")
        return
    if status == 8:
        if phase != 3 or target != TARGET or step != 0 or epoch != EXACT_LIMIT or detail != epoch:
            raise ValueError(f"{where}: malformed epoch-limit failure")
        return
    if status not in (*range(1, 8), 9, 10, 11):
        raise ValueError(f"{where}: unknown failure status {status}")
    if phase == 1:
        if target >= len(records) or step >= len(mutation_plan):
            raise ValueError(f"{where}: invalid mutation failure target or step")
    elif phase == 2:
        if target != TARGET or step >= len(action_plan):
            raise ValueError(f"{where}: invalid action failure target or step")
    else:
        raise ValueError(f"{where}: runtime failure must name mutation or action phase")
    words = (mutation_plan if phase == 1 else action_plan)[step]
    opcode = words[0]
    post_validation = phase == 1 and step == len(mutation_plan) - 1
    valid = False
    if status == 1:
        ordinal, reason = detail >> 16, detail & 65535

        def possible(function):
            if not 1 <= ordinal <= function["instruction_count"] or not 1 <= reason <= 6:
                return False
            operation = heap[function["code_offset"] + 4 * (ordinal - 1)]
            return reason == 3 or operation == {1: 5, 2: 9, 4: 17, 5: 18, 6: 19}.get(reason)

        if opcode == 3:
            valid = possible(functions[words[1]])
        elif opcode in (4, 11):
            if phase == 1:
                selectors = (range(len(records)) if opcode == 11 else
                             (target if words[1] == TARGET else words[1],))
                for selector in selectors:
                    handle = records[selector][SLOTS[words[2]] + "_handle"]
                    if words[2] == 0:
                        handle = families[handle]["methods"].get(words[7])
                    if handle is not None and functions[handle]["signature"] == words[6]:
                        valid |= possible(functions[handle])
            else:
                valid = any(possible(function) for function in functions if function["signature"] == words[6])
    elif status == 2:
        limit = len(families) if words[2] == 0 else len(functions)
        valid = (post_validation and detail < 3) or (opcode in (4, 11) and detail >= limit)
    elif status == 3:
        valid = phase == 1 and opcode == 5 and words[1] <= detail < words[1] + words[3] and detail < 4
    elif status == 4:
        valid = (post_validation and detail < 3) or (opcode in (4, 11) and detail == words[2])
    elif status == 5:
        valid = post_validation and detail == 3
    elif status == 6:
        record_write = phase == 1 and opcode == 5 and words[1] <= detail < words[1] + words[3]
        state_write = phase == 2 and opcode == 6 and words[1] <= detail < words[1] + words[3]
        valid = ((post_validation and 4 <= detail < RECORD_WORDS) or record_write or state_write or
                 (opcode == 7 and detail == words[1]))
    elif status == 7:
        valid = opcode == 7 and detail == words[1]
    elif status == 9:
        valid = (opcode == 11 and detail == words[1]) or (opcode == 12 and detail == words[2])
    elif status == 10:
        valid = opcode in (11, 12) and detail <= EXACT_LIMIT and detail not in {row[0] for row in metadata}
    elif status == 11:
        valid = opcode in (4, 11) and detail == words[6]
    if not valid:
        raise ValueError(f"{where}: failure detail {detail} is inconsistent with status {status} and its plan step")


def decode_checkpoint(raw):
    """Validate the complete checkpoint, retaining every original uint32 word."""
    if not isinstance(raw, bytes):
        raw = bytes(raw)
    if len(raw) < 40 or raw[:8] != MAGIC:
        raise ValueError("Checkpoint requires DWRD0002 and its eight-word header")
    header = list(struct.unpack_from("<8I", raw, 8))
    count, record_count, state_width, function_count, heap_words, mutation_steps, action_steps, family_count = header
    uint(count, "count", minimum=1)
    uint(record_count, "recordCount", MAX_RECORDS, 1)
    uint(state_width, "stateWidth", ir.MAX_INPUTS, 1)
    uint(function_count, "functionCount", MAX_FUNCTIONS, 1)
    uint(heap_words, "heapWords", minimum=1)
    uint(mutation_steps, "mutationSteps", MAX_STEPS, 1)
    uint(action_steps, "actionSteps", MAX_STEPS, 1)
    uint(family_count, "familyCount", MAX_FAMILIES, 1)
    static_words = checked_size(8 + 4 * record_count + 6 * function_count + 4 * family_count + heap_words +
                                8 * (mutation_steps + action_steps), "configuration")
    image_words = checked_size(6 + state_width + RECORD_WORDS * record_count, "image")
    instance_words = checked_size(count * image_words, "instance storage")
    total_words = static_words + instance_words
    expected = 8 + 4 * total_words
    if len(raw) != expected:
        raise ValueError(f"Checkpoint length mismatch: expected {expected} bytes, received {len(raw)}")
    cursor = 40

    def take(width):
        nonlocal cursor
        result = list(struct.unpack_from(f"<{width}I", raw, cursor))
        cursor += 4 * width
        return result

    metadata = [take(4) for _ in range(record_count)]
    seen_indices = set()
    for ordinal, record in enumerate(metadata):
        index = record[0]
        uint(index, f"metadata[{ordinal}].source_index", EXACT_LIMIT)
        if index in seen_indices:
            raise ValueError("Source indices must be unique")
        seen_indices.add(index)
        exact_float_integer(index, f"metadata[{ordinal}].source_index")
        for slot, signature in zip(SLOTS, record[1:]):
            uint(signature, f"metadata[{ordinal}].{slot}_signature", minimum=1)
    descriptors = [take(6) for _ in range(function_count)]
    family_descriptors = [take(4) for _ in range(family_count)]
    heap = take(heap_words)
    functions, signatures = validate_functions(descriptors, heap)
    families, interfaces = validate_families(family_descriptors, heap, functions)
    for ordinal, record in enumerate(metadata):
        if record[1] not in interfaces or any(signature not in signatures for signature in record[2:]):
            raise ValueError(f"metadata[{ordinal}]: unknown body interface or slot signature")
    mutation_plan = [take(8) for _ in range(mutation_steps)]
    action_plan = [take(8) for _ in range(action_steps)]
    validate_plan(mutation_plan, True, metadata, functions, signatures, state_width, families, interfaces)
    validate_plan(action_plan, False, metadata, functions, signatures, state_width, families, interfaces)
    instances_offset = cursor
    instances = []
    for lane in range(count):
        where = f"instances[{lane}]"
        failure_header = take(6)
        state_bits = take(state_width)
        state = [finite_word(word, f"{where}.state[{index}]") for index, word in enumerate(state_bits)]
        records = []
        for ordinal in range(record_count):
            words = take(RECORD_WORDS)
            validate_record(words, metadata[ordinal], functions, f"{where}.records[{ordinal}]", families)
            records.append({
                "ordinal": ordinal, "source_index": metadata[ordinal][0],
                "body_handle": words[0], "field_handle": words[1],
                "placement_handle": words[2], "generation": words[3],
                "values": [float_word(word) for word in words[4:]],
                "value_bits": words[4:], "raw_words": words,
            })
        validate_failure_header(failure_header, records, metadata, mutation_plan, action_plan, functions, heap, families, where)
        instances.append({
            "epoch": failure_header[0], "status": failure_header[1],
            "failure_phase": failure_header[2], "failure_target_ordinal": failure_header[3],
            "failure_step": failure_header[4], "failure_detail": failure_header[5],
            "header_words": failure_header, "state": state, "state_bits": state_bits,
            "records": records,
        })
    return {
        "profile": PROFILE, "format": MAGIC.decode("ascii"), "count": count,
        "record_count": record_count, "state_width": state_width,
        "function_count": function_count, "heap_words": heap_words,
        "mutation_steps": mutation_steps, "action_steps": action_steps,
        "header_words": header, "record_metadata_words": metadata,
        "function_descriptor_words": descriptors, "functions": functions,
        "family_count": family_count, "family_descriptor_words": family_descriptors,
        "families": families, "interfaces": interfaces,
        "heap": heap, "mutation_plan": mutation_plan, "action_plan": action_plan,
        "instance_words": image_words, "instances_offset_bytes": instances_offset,
        "configuration_sha256": ir.sha256(raw[:instances_offset]),
        "all_status_ok": all(instance["status"] == 0 for instance in instances),
        "failed_instance_count": sum(instance["status"] != 0 for instance in instances),
        "instances": instances, "sha256": ir.sha256(raw),
    }


def compile_definition(model, definition):
    ir.exact_keys(definition, DEFINITION_KEYS, {
        "profile", "functions", "families", "records", "state_names", "mutation_plan", "action_plan", "instances",
    }, "definition")
    if definition["profile"] != PROFILE:
        raise ValueError(f"definition.profile must be {PROFILE}")
    state_names = names(definition["state_names"], "state_names", 1, ir.MAX_INPUTS)
    value_names = names(definition.get("record_value_names", [f"value_{i}" for i in range(VALUE_WORDS)]),
                        "record_value_names", VALUE_WORDS, VALUE_WORDS)
    bank = definition["functions"]
    if not isinstance(bank, dict) or not 1 <= len(bank) <= MAX_FUNCTIONS:
        raise ValueError(f"functions: expected an ordered mapping of 1..{MAX_FUNCTIONS} definitions")
    if any(not isinstance(name, str) or not name for name in bank):
        raise ValueError("functions: names must be nonempty strings")
    handles = {name: index for index, name in enumerate(bank)}
    heap, descriptors, function_manifest = [], [], []
    for name, entry in bank.items():
        where = f"functions[{name!r}]"
        ir.exact_keys(entry, {"signature", "binding"}, {"signature", "binding"}, where)
        signature = uint(entry["signature"], where + ".signature", minimum=1)
        binding = entry["binding"]
        ir.validate_binding(binding, where + ".binding")
        compiler = ir.ExpressionCompiler(binding["inputs"])
        requirements = []
        for index, condition in enumerate(binding.get("requires", [])):
            register = compiler.expression(condition, f"{where}.requires[{index}]")
            requirements.append(compiler._emit(17, register))
        outputs = [compiler.expression(expression, f"{where}.outputs[{key!r}]")
                   for key, expression in binding["outputs"].items()]
        code_offset = len(heap)
        for instruction in compiler.instructions:
            heap.extend(instruction)
        output_offset = len(heap)
        heap.extend(outputs)
        descriptors.append([code_offset, output_offset, len(compiler.instructions),
                            len(binding["inputs"]), len(outputs), signature])
        function_manifest.append({
            "handle": handles[name], "name": name, "signature": signature,
            "input_names": binding["inputs"], "output_names": list(binding["outputs"]),
            "requirement_registers": requirements, "binding": binding,
        })
    functions, signatures = validate_functions(descriptors, heap)
    for details, numerical in zip(function_manifest, functions):
        details.update(numerical)

    family_bank = definition["families"]
    if not isinstance(family_bank, dict) or not 1 <= len(family_bank) <= MAX_FAMILIES:
        raise ValueError(f"families: expected an ordered mapping of 1..{MAX_FAMILIES} body families")
    if any(not isinstance(name, str) or not name for name in family_bank):
        raise ValueError("families: names must be nonempty strings")
    family_handles = {name: index for index, name in enumerate(family_bank)}
    family_descriptors, family_manifest = [], []
    for name, entry in family_bank.items():
        where = f"families[{name!r}]"
        ir.exact_keys(entry, {"interface", "methods"}, {"interface", "methods"}, where)
        interface = uint(entry["interface"], where + ".interface", minimum=1)
        methods = entry["methods"]
        if not isinstance(methods, dict) or not 1 <= len(methods) <= 32:
            raise ValueError(f"{where}.methods: expected 1..32 role/function entries")
        resolved = []
        for role_text, function_name in methods.items():
            if not isinstance(role_text, str) or not role_text.isascii() or not role_text.isdecimal():
                raise ValueError(f"{where}: role keys must be canonical decimal uint32 strings")
            role = uint(int(role_text), where + ".role")
            if str(role) != role_text:
                raise ValueError(f"{where}: role keys must be canonical decimal uint32 strings")
            if not isinstance(function_name, str) or function_name not in handles:
                raise ValueError(f"{where}: method names an unknown function")
            resolved.append((role, handles[function_name]))
        resolved.sort()
        offset = len(heap)
        for role, handle in resolved:
            heap.extend((role, handle))
        family_descriptors.append([interface, offset, len(resolved), 0])
        family_manifest.append({"handle": family_handles[name], "name": name, "interface": interface,
                                "method_functions": dict(methods)})
    families, interfaces = validate_families(family_descriptors, heap, functions)
    for details, numerical in zip(family_manifest, families):
        details.update(numerical)

    records = definition["records"]
    if not isinstance(records, list) or not 1 <= len(records) <= MAX_RECORDS:
        raise ValueError(f"records: expected 1..{MAX_RECORDS} selected source records")
    metadata, selected, record_keys = [], [], set()
    for ordinal, record in enumerate(records):
        where = f"records[{ordinal}]"
        ir.exact_keys(record, RECORD_KEYS, {"key", *SLOTS, "source_slots", "values"}, where)
        key = record["key"]
        if not isinstance(key, str) or key in record_keys:
            raise ValueError(f"{where}.key: expected a unique source-model key")
        source = ir.resolve_operator(model, key)
        record_keys.add(key)
        uint(source["index"], where + ".source_index", EXACT_LIMIT)
        exact_float_integer(source["index"], where + ".source_index")
        ir.exact_keys(record["source_slots"], SLOTS, SLOTS, where + ".source_slots")
        slot_signatures = []
        for slot in SLOTS:
            if slot not in source:
                raise ValueError(f"{where}: selected source record is missing its {slot} definition")
            if not same_structure(record["source_slots"][slot], source[slot]):
                raise ValueError(f"{where}.source_slots.{slot}: asserted source declaration does not match the selected model; supply an explicit binding for the changed definition")
            function_name = record[slot]
            slot_handles = family_handles if slot == "body" else handles
            if not isinstance(function_name, str) or function_name not in slot_handles:
                raise ValueError(f"{where}.{slot}: expected a declared family/function name")
            slot_signatures.append(families[slot_handles[function_name]]["interface"] if slot == "body"
                                   else functions[slot_handles[function_name]]["signature"])
        metadata.append([source["index"], *slot_signatures])
        selected.append({
            "ordinal": ordinal, "key": key, "source_index": source["index"],
            "source_record": source,
            "asserted_source_slots": record["source_slots"],
            "initial_slot_bindings": {slot: {"definition": record[slot],
                                              "handle": (family_handles if slot == "body" else handles)[record[slot]],
                                              "interface" if slot == "body" else "signature": slot_signatures[index]}
                                      for index, slot in enumerate(SLOTS)},
            "resolution": "Explicit numerical function assignment bound to structurally checked source-slot declarations; unmatched model edits are rejected rather than silently retaining the old binding. Original slot expressions are not automatically lowered as XIR.",
        })
    mutation_plan, action_plan = definition["mutation_plan"], definition["action_plan"]
    validate_plan(mutation_plan, True, metadata, functions, signatures, len(state_names), families, interfaces)
    validate_plan(action_plan, False, metadata, functions, signatures, len(state_names), families, interfaces)
    rounding = {"value_count": 0, "changed_value_count": 0, "max_absolute_difference": 0.0}

    def pack_number(value, where):
        rounded, bits = ir.fp32(value, where)
        difference = abs(float(value) - rounded)
        rounding["value_count"] += 1
        rounding["changed_value_count"] += int(difference != 0.0)
        rounding["max_absolute_difference"] = max(rounding["max_absolute_difference"], difference)
        return bits

    def pack_record(record, ordinal, where):
        result = []
        for slot in SLOTS:
            name = record[slot]
            slot_handles = family_handles if slot == "body" else handles
            if not isinstance(name, str) or name not in slot_handles:
                raise ValueError(f"{where}.{slot}: expected a declared family/function name")
            result.append(slot_handles[name])
        result.append(uint(record.get("generation", 0), where + ".generation", EXACT_LIMIT))
        values = record["values"]
        if not isinstance(values, list) or len(values) != VALUE_WORDS:
            raise ValueError(f"{where}.values: expected exactly {VALUE_WORDS} values")
        result.extend(pack_number(value, f"{where}.values[{index}]") for index, value in enumerate(values))
        validate_record(result, metadata[ordinal], functions, where, families)
        return result

    # Validate global records even when every instance overrides one or more.
    for ordinal, record in enumerate(records):
        pack_record(record, ordinal, f"records[{ordinal}]")
    rounding = {"value_count": 0, "changed_value_count": 0, "max_absolute_difference": 0.0}
    instances = definition["instances"]
    if not isinstance(instances, list) or not 1 <= len(instances) <= ir.UINT32_MAX:
        raise ValueError("instances: expected a nonempty list of independent instance images")
    static_words = checked_size(8 + 4 * len(records) + 6 * len(functions) + 4 * len(families) + len(heap) +
                                8 * (len(mutation_plan) + len(action_plan)), "configuration")
    image_words = 6 + len(state_names) + RECORD_WORDS * len(records)
    checked_size(len(instances) * image_words, "instance storage")
    image = bytearray()
    for lane, instance in enumerate(instances):
        where = f"instances[{lane}]"
        ir.exact_keys(instance, {"state", "epoch", "records"}, {"state"}, where)
        epoch = uint(instance.get("epoch", 0), where + ".epoch", EXACT_LIMIT)
        state = instance["state"]
        ir.exact_keys(state, state_names, state_names, where + ".state")
        overrides = instance.get("records", {})
        ir.exact_keys(overrides, record_keys, set(), where + ".records")
        words = [epoch, 0, 0, 0, 0, 0]
        words.extend(pack_number(state[name], f"{where}.state[{name!r}]") for name in state_names)
        for ordinal, record in enumerate(records):
            override = overrides.get(record["key"], {})
            ir.exact_keys(override, OVERRIDE_KEYS, set(), f"{where}.records[{record['key']!r}]")
            words.extend(pack_record({**record, **override}, ordinal, f"{where}.records[{record['key']!r}]"))
        image.extend(struct.pack(f"<{len(words)}I", *words))
    header = [len(instances), len(records), len(state_names), len(functions), len(heap),
              len(mutation_plan), len(action_plan), len(families)]
    static = list(header)
    for record in metadata:
        static.extend(record)
    for descriptor in descriptors:
        static.extend(descriptor)
    for descriptor in family_descriptors:
        static.extend(descriptor)
    static.extend(heap)
    for instruction in mutation_plan + action_plan:
        static.extend(instruction)
    program = MAGIC + struct.pack(f"<{len(static)}I", *static) + bytes(image)
    # Run the same full binary validator used by checkpoint inspection before
    # exposing a compiled image. This includes plans and every instance word.
    decoded = decode_checkpoint(program)
    manifest = {
        "profile": PROFILE, "format": MAGIC.decode("ascii"),
        "scope": "typed_resident_definition_execution",
        "status": "application_semantics_require_separate_binding_and_evidence", "complete_application_lowered": False,
        "count": len(instances), "record_count": len(records), "state_width": len(state_names),
        "function_count": len(functions), "heap_words": len(heap),
        "mutation_steps": len(mutation_plan), "action_steps": len(action_plan),
        "state_names": state_names, "record_value_names": value_names,
        "selected_records": selected, "functions": function_manifest, "families": family_manifest,
        "family_count": len(families),
        "mutation_plan": mutation_plan, "action_plan": action_plan,
        "configuration_sha256": decoded["configuration_sha256"],
        "program_sha256": ir.sha256(program), "instance_words": image_words,
        "source_model_semantic_sha256": ir.sha256(ir.json_bytes(model)),
        "definition_semantic_sha256": ir.sha256(ir.json_bytes(definition)),
        "definition_metadata": {key: definition[key] for key in ("source", "meaning", "status") if key in definition},
        "binding_contract": {
            "function_bank": "Immutable validated expressions; mutable resident handles and values select and parameterize the expressions that execute.",
            "source_identity": "Record keys and source indices are checked against the selected source model. Each required source_slots declaration must match the actual body/field/placement JSON tree, ignoring object-key order and preserving scalar types. Numerical function assignments and call plans are explicit authored bindings; this guard is not unrestricted inline source-expression lowering.",
            "mutation_order": "Every mutation target reads the same old state and old record table. Candidate records publish together before action. Mutated controller handles govern the next mutation transaction.",
            "source_dependency_evidence": "Plan memory/call validity does not prove old-mutator, old-pinion, field-rebinding, or numerical sensitivity obligations. Inspect the authored plan and numerical intervention evidence.",
            "transaction": "Any lane failure rolls back all provisional state and record changes and retains failure metadata; successful action commits epoch+1.",
            "instance_semantics": "Each lane is an independent substrate instance with its own LUT and state; lanes do not share one operator field.",
            "continuation": "DWRD0002 checkpoints include the complete static bank and plans plus every instance state and live record word.",
            "arbitrary_expression_synthesis": False,
            "catalogue_growth": False,
            "complete_31_operator_catalogue_claimed": False,
            "cycle_input": "The generic definition compiler executes explicit plans; a separate application compiler must establish their source-cycle relationship.",
            "not_lowered": ["automatic lowering of unselected source records",
                            "unrestricted expression or catalogue editing", "implicit scientific/domain application semantics"],
        },
        "limits": {"records": MAX_RECORDS, "state_floats": ir.MAX_INPUTS, "functions": MAX_FUNCTIONS,
                   "families": MAX_FAMILIES, "methods_per_family": 32,
                   "plan_steps_each": MAX_STEPS, "frame_floats": FRAME_WORDS,
                   "xir_instructions_per_function": ir.MAX_INSTRUCTIONS,
                   "xir_inputs_per_function": ir.MAX_INPUTS, "xir_outputs_per_function": ir.MAX_OUTPUTS,
                   "record_value_floats": VALUE_WORDS, "maximum_epoch_and_generation": EXACT_LIMIT},
        "numeric_policy": "Finite numeric inputs and constants are packed to IEEE FP32; negative-zero bits are retained. Integer handles, generations and headers remain uint32 words. XIR select is eager.",
        "instance_input_fp32_rounding": rounding,
    }
    return program, manifest


def write_compilation(model_path, definition_path, output):
    model, model_raw = ir.read_json(Path(model_path))
    definition, definition_raw = ir.read_json(Path(definition_path))
    program, manifest = compile_definition(model, definition)
    output = Path(output).resolve()
    files = {"source_model.json": model_raw, "definition.json": definition_raw, "program.bin": program}
    manifest["created_at"] = datetime.now(timezone.utc).isoformat()
    manifest["sources"] = {
        "model": {"path": str(Path(model_path).resolve()), "sha256": ir.sha256(model_raw)},
        "definition": {"path": str(Path(definition_path).resolve()), "sha256": ir.sha256(definition_raw)},
    }
    manifest["files"] = {name: {"sha256": ir.sha256(data), "bytes": len(data)} for name, data in files.items()}
    manifest_raw = ir.json_bytes(manifest)
    output.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        (output / name).write_bytes(data)
    (output / "manifest.json").write_bytes(manifest_raw)
    return manifest


def read_checkpoint(path):
    return decode_checkpoint(Path(path).read_bytes())


def inspect_checkpoint(path, manifest_path=None):
    result = read_checkpoint(path)
    if manifest_path is not None:
        manifest, _ = ir.read_json(Path(manifest_path))
        if not isinstance(manifest, dict) or manifest.get("profile") != PROFILE:
            raise ValueError("Supplied manifest does not describe DWI-RESIDENT-0.2")
        if manifest.get("configuration_sha256") != result["configuration_sha256"]:
            raise ValueError("Checkpoint static bank, plans or dimensions do not match the manifest")
        state_names = names(manifest.get("state_names"), "manifest.state_names", result["state_width"], result["state_width"])
        value_names = names(manifest.get("record_value_names"), "manifest.record_value_names", VALUE_WORDS, VALUE_WORDS)
        records = manifest.get("selected_records")
        functions = manifest.get("functions")
        families = manifest.get("families")
        if not isinstance(records, list) or len(records) != result["record_count"]:
            raise ValueError("Manifest selected-record metadata does not match the checkpoint")
        if not isinstance(functions, list) or len(functions) != result["function_count"]:
            raise ValueError("Manifest function-name metadata does not match the checkpoint")
        if not isinstance(families, list) or len(families) != result["family_count"]:
            raise ValueError("Manifest family-name metadata does not match the checkpoint")
        family_names = []
        for handle, family in enumerate(families):
            if not isinstance(family, dict) or family.get("handle") != handle or not isinstance(family.get("name"), str):
                raise ValueError("Manifest families must retain their exact handle order and names")
            family_names.append(family["name"])
        function_names = []
        for handle, function in enumerate(functions):
            if not isinstance(function, dict) or function.get("handle") != handle or not isinstance(function.get("name"), str):
                raise ValueError("Manifest functions must retain their exact handle order and names")
            function_names.append(function["name"])
        keys = []
        for ordinal, record in enumerate(records):
            if (not isinstance(record, dict) or record.get("ordinal") != ordinal or
                    record.get("source_index") != result["record_metadata_words"][ordinal][0] or
                    not isinstance(record.get("key"), str)):
                raise ValueError("Manifest source-record ordinals/indices do not match the checkpoint")
            keys.append(record["key"])
        if len(set(keys)) != len(keys):
            raise ValueError("Manifest source-record keys must be unique")
        result["state_names"] = state_names
        result["record_value_names"] = value_names
        for instance in result["instances"]:
            instance["named_state"] = dict(zip(state_names, instance["state"]))
            for ordinal, record in enumerate(instance["records"]):
                record["key"] = keys[ordinal]
                record["named_values"] = dict(zip(value_names, record["values"]))
                record["slot_definitions"] = {slot: (family_names if slot == "body" else function_names)[record[slot + "_handle"]] for slot in SLOTS}
    result["raw_word_policy"] = "All integer headers, handles, generations, FP32 bit patterns, bank words and plans are retained without conversion to symbolic hashes."
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    compile_parser = commands.add_parser("compile", help="Compile explicit resident definitions and call plans")
    compile_parser.add_argument("--model", type=Path, default=ir.DEFAULT_MODEL)
    compile_parser.add_argument("--definition", type=Path, required=True)
    compile_parser.add_argument("--output", type=Path, required=True)
    inspect_parser = commands.add_parser("inspect", help="Validate and inspect a complete resident checkpoint")
    inspect_parser.add_argument("checkpoint", type=Path)
    inspect_parser.add_argument("--manifest", type=Path)
    args = parser.parse_args(argv)
    if args.command == "compile":
        manifest = write_compilation(args.model, args.definition, args.output)
        print(json.dumps({"output": str(args.output.resolve()), "profile": PROFILE,
                          "scope": manifest["scope"], "complete_application_lowered": False,
                          "count": manifest["count"], "record_count": manifest["record_count"],
                          "function_count": manifest["function_count"],
                          "program_sha256": manifest["program_sha256"]}, indent=2, allow_nan=False))
        return 0
    result = inspect_checkpoint(args.checkpoint, args.manifest)
    print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
    return 0 if result["all_status_ok"] else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, RecursionError, struct.error) as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(1)
