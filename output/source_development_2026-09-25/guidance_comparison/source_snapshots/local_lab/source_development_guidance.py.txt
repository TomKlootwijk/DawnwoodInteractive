"""Checked publication of new authored guidance over an existing substrate.

This is an explicit immutable-definition change, not ordinary checkpoint
resume. Existing expression data, live records, state and epochs survive
bit-for-bit; an optional common query changes only its two declared words.
Compatibility and preservation are checked here. The changed numerical
semantics and their usefulness still require a subsequent resident experiment.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import struct

from . import source_development_bindings as bindings
from . import source_development_results as results
from . import source_ir_v2 as ir
from . import source_resident_v3 as resident


PROFILE = "DWI-DEVELOPMENT-GUIDANCE-PUBLICATION-0.1"


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _json_sha(value):
    return _sha(ir.json_bytes(value))


def _json_equal(left, right):
    return (json.dumps(left, sort_keys=True, allow_nan=False, separators=(",", ":"))
            == json.dumps(right, sort_keys=True, allow_nan=False, separators=(",", ":")))


def _bytes(value, where):
    if not isinstance(value, (bytes, bytearray, memoryview)):
        raise ValueError(f"{where}: expected the actual binary payload")
    return bytes(value)


def _native_function(decoded, function):
    start = function["code_offset"]
    code = decoded["heap"][start:start + function["instruction_count"] * 4]
    output = function["output_registers"]
    # Offsets within the enclosing heap are storage layout, not function meaning.
    identity = [function["signature"], function["input_width"], function["output_width"],
                function["instruction_count"], *code, *output]
    return code, output, _sha(struct.pack(f"<{len(identity)}I", *identity))


def _method_handles(value, where):
    # The compiler returns integer role keys; JSON roundtrips stringify them.
    # Accept both exact forms, but reject aliases such as01 and duplicate1/'1'.
    if not isinstance(value, dict):
        raise ValueError(f"{where}: expected a role-to-handle mapping")
    result = {}
    for key, handle in value.items():
        if type(key) is int:
            role = key
        elif isinstance(key, str) and key.isascii() and key.isdigit() and str(int(key)) == key:
            role = int(key)
        else:
            raise ValueError(f"{where}: role keys must be exact canonical nonnegative integers")
        if not 0 <= role <= ir.UINT32_MAX or type(handle) is not int or not 0 <= handle <= ir.UINT32_MAX:
            raise ValueError(f"{where}: invalid role or function handle")
        if str(role) in result:
            raise ValueError(f"{where}: ambiguous duplicate role identity")
        result[str(role)] = handle
    return result


def _verified_source(decoded, manifest, where):
    """Cross-check named source/bindings against their actual compiled words."""
    functions = manifest["functions"]
    function_names = [item["name"] for item in functions]
    numerical = []
    for handle, (item, native) in enumerate(zip(functions, decoded["functions"])):
        for key in ("handle", "signature", "code_offset", "output_register_offset",
                    "instruction_count", "input_width", "output_width"):
            if type(item.get(key)) is not int or item[key] != native[key]:
                raise ValueError(f"{where}.functions[{handle}]: {key} disagrees with native data")
        compiled = ir.compile_binding(item.get("binding"), f"{where}.functions[{handle}].binding")
        if (item.get("input_names") != compiled["inputs"]
                or item.get("output_names") != compiled["output_names"]
                or item.get("requirement_registers") != compiled["requirement_registers"]
                or len(compiled["inputs"]) != native["input_width"]
                or len(compiled["output_names"]) != native["output_width"]):
            raise ValueError(f"{where}.functions[{handle}]: ordered contract differs from its binding")
        code, outputs, numeric_hash = _native_function(decoded, native)
        if (code != [word for instruction in compiled["instructions"] for word in instruction]
                or outputs != compiled["output_registers"] or item.get("output_registers") != outputs):
            raise ValueError(f"{where}.functions[{handle}]: declared binding does not compile to native words")
        numerical.append({"handle": handle, "name": item["name"], "signature": native["signature"],
            "input_names": compiled["inputs"], "output_names": compiled["output_names"],
            "instruction_count": native["instruction_count"], "numeric_sha256": numeric_hash,
            "binding_sha256": _json_sha(item["binding"])})
    family_identities = []
    for handle, (item, native) in enumerate(zip(manifest["families"], decoded["families"])):
        for key in ("handle", "interface", "methods_offset", "method_count"):
            if type(item.get(key)) is not int or item[key] != native[key]:
                raise ValueError(f"{where}.families[{handle}]: {key} disagrees with native data")
        expected_methods = {str(role): function for role, function in native["methods"].items()}
        expected_names = {str(role): function_names[function] for role, function in native["methods"].items()}
        if (not _json_equal(_method_handles(item.get("methods"), f"{where}.families[{handle}].methods"), expected_methods)
                or not _json_equal(item.get("method_functions"), expected_names)):
            raise ValueError(f"{where}.families[{handle}]: role/method identity disagrees with native data")
        family_identities.append({"handle": handle, "name": item["name"], "interface": native["interface"],
                                  "methods": expected_methods, "method_functions": expected_names})
    source = manifest["definition_metadata"]["source"]
    development = manifest["binding_contract"]["development"]
    authored = development.get("source")
    if not isinstance(authored, dict) or development.get("source_sha256") != _json_sha(authored):
        raise ValueError(f"{where}: development source hash does not describe its retained source object")
    graph = source.get("application_graph")
    if not isinstance(graph, dict) or not isinstance(graph.get("graph"), dict):
        raise ValueError(f"{where}: retain the actual named application graph for checked publication")
    graph_hash = _json_sha(graph["graph"])
    if graph.get("graph_sha256") != graph_hash or development.get("graph_sha256") != graph_hash:
        raise ValueError(f"{where}: named application graph hash is inconsistent")
    plan_hashes = {}
    for phase in ("mutation", "action"):
        plan = decoded[phase + "_plan"]
        if not _json_equal(manifest.get(phase + "_plan"), plan):
            raise ValueError(f"{where}: manifest {phase} plan does not match native words")
        metadata = graph.get(phase)
        plan_hashes[phase] = _json_sha(plan)
        if not isinstance(metadata, dict) or metadata.get("plan_sha256") != plan_hashes[phase]:
            raise ValueError(f"{where}: named graph {phase} plan hash is inconsistent")
    bank = {"functions": numerical, "families": family_identities}
    return {"functions": numerical, "families": family_identities,
            "source_sha256": development["source_sha256"], "graph_sha256": graph_hash,
            "plan_sha256": plan_hashes, "named_bank_sha256": _json_sha(bank)}


def _score_contract(manifest, function):
    development = manifest["binding_contract"]["development"]
    return (function["name"] == development.get("functions", {}).get("score")
            and function["input_names"] == [
                *(f"d{index}" for index in range(len(development["training_points"]))),
                "node_count", *bindings.BOX_NAMES]
            and function["output_names"] == [
                "score", "coverage", "witness_x", "witness_y", "witness_distance", "area"])


def _layout_compatibility(parent, parent_manifest, new, new_manifest, old_source, new_source):
    for key in ("count", "record_count", "state_width", "instance_words"):
        if parent[key] != new[key]:
            raise ValueError(f"Guidance publication requires the same {key}")
    if parent_manifest["state_names"] != new_manifest["state_names"]:
        raise ValueError("Guidance publication requires identical ordered state names")
    old_values = resident.names(parent_manifest.get("record_value_names"), "parent.record_value_names",
                                resident.VALUE_WORDS, resident.VALUE_WORDS)
    new_values = resident.names(new_manifest.get("record_value_names"), "new.record_value_names",
                                resident.VALUE_WORDS, resident.VALUE_WORDS)
    if old_values != new_values:
        raise ValueError("Guidance publication requires identical ordered record value names")
    if parent["record_metadata_words"] != new["record_metadata_words"]:
        raise ValueError("Record source indices and body/field/placement interfaces must stay identical")
    if ([r["key"] for r in parent_manifest["selected_records"]]
            != [r["key"] for r in new_manifest["selected_records"]]):
        raise ValueError("Record keys must keep their source-index and ordinal identities")
    for name in ("program_state_fields", "diagnostic_state_fields"):
        if not _json_equal(parent_manifest["binding_contract"]["development"][name],
                           new_manifest["binding_contract"]["development"][name]):
            raise ValueError(f"Guidance publication cannot reinterpret {name}")
    old_functions, new_functions = old_source["functions"], new_source["functions"]
    if len(new_functions) < len(old_functions):
        raise ValueError("Guidance publication cannot discard an existing function handle")
    changed = []
    for before, after in zip(old_functions, new_functions):
        if before["name"] != after["name"] or before["signature"] != after["signature"]:
            raise ValueError("An existing function handle cannot change its name or signature identity")
        names_changed = (before["input_names"] != after["input_names"]
                         or before["output_names"] != after["output_names"])
        if names_changed and not (_score_contract(parent_manifest, before) and _score_contract(new_manifest, after)):
            raise ValueError(f"{before['name']}: only the declared training-count score contract may change arity")
        if before != after:
            changed.append({"handle": before["handle"], "name": before["name"],
                "numeric_changed": before["numeric_sha256"] != after["numeric_sha256"],
                "binding_source_changed": before["binding_sha256"] != after["binding_sha256"],
                "ordered_contract_changed": names_changed, "before": before, "after": after})
    old_families, new_families = old_source["families"], new_source["families"]
    if len(new_families) < len(old_families):
        raise ValueError("Guidance publication cannot discard an existing family handle")
    for before, after in zip(old_families, new_families):
        if not _json_equal(before, after):
            raise ValueError("Existing family names, interfaces and role-to-method identities must stay identical")
    return changed


def migrate_guidance(parent_checkpoint_bytes, parent_manifest, new_program_bytes, new_manifest, *, query=None):
    """Publish new checked definitions around the complete retained parent image.

    ``query`` is either None or one common finite(x,y) pair in[-16,16]. It
    replaces only resource_query_x/y in each lane. No other state, program,
    record, generation, failure-header or epoch word is rewritten. Returned
    diagnostics remain historical until the next successful resident epoch.

    The new payload must be the fresh compiled template named by its manifest.
    Existing handles keep their identities; declared function code can change.
    Score inputs alone may expand/contract with the explicit training count.
    Pure-binding recompile and graph/plan hashes cross-check the declarations.
    New semantics are recorded, not certified useful or scientifically correct
    merely because this publication satisfies the native interface contract.
    """
    parent_raw = _bytes(parent_checkpoint_bytes, "parent_checkpoint_bytes")
    template_raw = _bytes(new_program_bytes, "new_program_bytes")
    parent = resident.decode_checkpoint(parent_raw)
    new = resident.decode_checkpoint(template_raw)
    parent_assessment = results.evaluate_results(parent_raw, parent_manifest)
    new_assessment = results.evaluate_results(template_raw, new_manifest)
    if not parent_assessment["all_assessments_passed"] or not parent_assessment["all_runtime_healthy"]:
        raise ValueError("Parent checkpoint must contain healthy, independently valid programs and readout")
    if not new_assessment["all_assessments_passed"] or not new_assessment["all_runtime_healthy"]:
        raise ValueError("New compiled template must contain healthy, independently valid initial programs")
    if new_manifest.get("program_sha256") != _sha(template_raw):
        raise ValueError("new_program_bytes must match the compiled template program hash")
    if "guidance_publication" in new_manifest or "query_population" in new_manifest:
        raise ValueError("The new definition template must be freshly compiled, not another published checkpoint")
    if any(instance["epoch"] != 0 for instance in new["instances"]):
        raise ValueError("The new definition template must have initial epoch0")
    if not _json_equal(parent_assessment["packed_protected"], new_assessment["packed_protected"]):
        raise ValueError("Guidance publication cannot silently change protected geometry or coverage margins")
    epochs = [instance["epoch"] for instance in parent["instances"]]
    if any(epoch >= resident.EXACT_LIMIT for epoch in epochs):
        raise ValueError("Parent epoch limit leaves no subsequent epoch for refreshed diagnostics")
    if any(record["generation"] >= resident.EXACT_LIMIT
           for instance in parent["instances"] for record in instance["records"]):
        raise ValueError("A parent record generation at its limit cannot complete the required next mutation")
    old_source = _verified_source(parent, parent_manifest, "parent")
    new_source = _verified_source(new, new_manifest, "new")
    changes = _layout_compatibility(parent, parent_manifest, new, new_manifest, old_source, new_source)
    query_values, query_bits = None, None
    if query is not None:
        if not isinstance(query, (list, tuple)) or len(query) != 2:
            raise ValueError("query must be one explicit common(x,y) pair")
        packed = [ir.fp32(value, f"query[{index}]") for index, value in enumerate(query)]
        if any(abs(value) > 16 for value, bits in packed):
            raise ValueError("query exceeds the declared[-16,16] evaluation envelope")
        query_values = [value for value, bits in packed]
        query_bits = [bits for value, bits in packed]
    old_image = parent_raw[parent["instances_offset_bytes"]:]
    image = bytearray(old_image)
    indices = [parent_manifest["state_names"].index(name)
               for name in ("resource_query_x", "resource_query_y")]
    if query_bits is not None:
        for lane in range(parent["count"]):
            for index, bits in zip(indices, query_bits):
                struct.pack_into("<I", image, 4 * (lane * parent["instance_words"] + 6 + index), bits)
    published = template_raw[:new["instances_offset_bytes"]] + bytes(image)
    installed = resident.decode_checkpoint(published)
    preserved, query_changes = [], []
    for lane, (before, after) in enumerate(zip(parent["instances"], installed["instances"])):
        if before["header_words"] != after["header_words"]:
            raise ValueError("Internal publication error: parent epoch/failure header changed")
        before_records = [word for record in before["records"] for word in record["raw_words"]]
        after_records = [word for record in after["records"] for word in record["raw_words"]]
        if before_records != after_records:
            raise ValueError("Internal publication error: live records changed")
        changed_indices = [index for index, (a, b) in enumerate(zip(before["state_bits"], after["state_bits"])) if a != b]
        permitted = set(indices) if query_bits is not None else set()
        if any(index not in permitted for index in changed_indices):
            raise ValueError("Internal publication error: a state word outside the declared query changed")
        state_without_query = [word for index, word in enumerate(before["state_bits"]) if index not in permitted]
        retained = [*before["header_words"], *state_without_query, *before_records]
        preserved.append({"lane": lane, "epoch": before["epoch"],
            "preserved_word_count": len(retained),
            "preserved_words_sha256": _sha(struct.pack(f"<{len(retained)}I", *retained)),
            "program_sha256": parent_assessment["results"][lane]["program_sha256"],
            "topology_sha256": parent_assessment["results"][lane]["topology_sha256"],
            "semantic_sha256": parent_assessment["results"][lane]["semantic_sha256"]})
        if query_bits is not None:
            query_changes.append({"lane": lane,
                "before_bits": [before["state_bits"][index] for index in indices],
                "after_bits": [after["state_bits"][index] for index in indices],
                "changed_word_count": len(changed_indices)})
    next_epochs = [epoch + 1 for epoch in epochs]
    floor = next_epochs[0] if len(set(next_epochs)) == 1 else next_epochs
    publication = {
        "profile": PROFILE, "kind": "explicit_changed_definition_publication",
        "ordinary_resume": False,
        "actor_boundary": "AI/author selects and compiles the new guidance before this publication; subsequent candidate construction and retention remain resident execution.",
        "parent_checkpoint_sha256": _sha(parent_raw), "parent_manifest_sha256": _json_sha(parent_manifest),
        "compiled_template_program_sha256": _sha(template_raw),
        "compiled_template_manifest_sha256": _json_sha(new_manifest),
        "published_input_sha256": _sha(published),
        "parent_epoch": epochs[0] if len(set(epochs)) == 1 else None,
        "parent_epoch_range": [min(epochs), max(epochs)],
        "parent_epochs": epochs, "diagnostics_require_epoch_at_least": floor,
        "diagnostic_policy": "All returned diagnostics remain preceding-definition/query values. The next successful epoch refreshes score, witness, query distance and admission under the new definition; no host score or witness is substituted.",
        "configuration": {"before_sha256": parent["configuration_sha256"], "after_sha256": new["configuration_sha256"],
                          "changed": parent["configuration_sha256"] != new["configuration_sha256"]},
        "definition_changes": {
            "source_sha256": {"before": old_source["source_sha256"], "after": new_source["source_sha256"]},
            "named_bank_sha256": {"before": old_source["named_bank_sha256"], "after": new_source["named_bank_sha256"]},
            "named_graph_sha256": {"before": old_source["graph_sha256"], "after": new_source["graph_sha256"]},
            "native_plan_sha256": {"before": old_source["plan_sha256"], "after": new_source["plan_sha256"]},
            "functions": changes, "appended_functions": new_source["functions"][len(old_source["functions"]):],
            "appended_families": new_source["families"][len(old_source["families"]):]},
        "compatibility": {"count": parent["count"], "state_width": parent["state_width"],
            "record_count": parent["record_count"], "state_names_identical": True,
            "record_value_names_identical": True, "source_record_identities_identical": True,
            "existing_function_and_family_handle_identities_preserved": True,
            "family_interfaces_and_role_method_identities_preserved": True,
            "new_function_code_semantics_may_differ": True},
        "state_preservation": {"complete_record_words_identical": True, "epoch_and_header_words_identical": True,
            "all_state_words_except_optional_query_identical": True,
            "complete_mutable_image_identical": old_image == bytes(image),
            "parent_mutable_image_sha256": _sha(old_image), "published_mutable_image_sha256": _sha(bytes(image)),
            "lanes": preserved},
        "query_override": {"provided": query is not None, "authored": list(query) if query is not None else None,
            "packed_fp32": query_values, "packed_bits": query_bits,
            "only_permitted_state_fields": ["resource_query_x", "resource_query_y"] if query is not None else [],
            "lanes": query_changes},
        "template_initialization": "The compiled template supplies only immutable configuration. Its initial records, seed programs, diagnostics, query and epochs are discarded in favor of the complete retained parent images and the optional explicitly supplied query.",
        "parent_guidance_publication_sha256": _json_sha(parent_manifest["guidance_publication"])
            if "guidance_publication" in parent_manifest else None,
        "limitations": [
            "This check establishes declared handle identity, binary/manifest consistency and exact state preservation, not equivalent function semantics across the changed configuration.",
            "Named source and plan hashes are verified against the retained objects/native plans. Recompiling each scalar binding verifies its native function words; this is not an independent proof of the full source graph lowering or every source relationship.",
            "Current programs are independently checked before publication. New semantics, future candidate safety, refreshed diagnostics and useful behavior require actual subsequent resident execution evidence."]}
    output_manifest = deepcopy(new_manifest)
    output_manifest["guidance_publication"] = publication
    output_manifest["program_sha256"] = _sha(published)
    if isinstance(output_manifest.get("files"), dict) and "program.bin" in output_manifest["files"]:
        publication["compiled_template_program_file_record"] = deepcopy(output_manifest["files"]["program.bin"])
        output_manifest["files"]["program.bin"] = {"sha256": _sha(published), "bytes": len(published)}
    if "instance_input_fp32_rounding" in output_manifest:
        publication["compiled_template_input_rounding"] = output_manifest.pop("instance_input_fp32_rounding")
    output_manifest["publication_numeric_policy"] = "Parent FP32 words are copied without numeric conversion. Only explicitly supplied query coordinates are rounded once to FP32, with authored values and resulting bits retained in guidance_publication."
    # The current reader must understand the diagnostic publication boundary.
    check = results.evaluate_results(published, output_manifest)
    if (not check["all_assessments_passed"] or check["evaluated_diagnostic_count"] != 0
            or not check["all_programs_geometrically_admissible"]):
        raise ValueError("Published image failed independent program/readout assessment or stale-diagnostic handling")
    return published, output_manifest
