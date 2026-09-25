"""Fork a retained resident SDF into a headless batch of new resource queries.

Only the population count, two query coordinates and construction-enabled bit
change. Every selected instance header, program word and record is otherwise
copied byte for byte. This module does not execute a native kernel, construct a
candidate, supply query answers, or implement ordinary checkpoint resume.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import struct
import sys

try:
    from . import source_development_results as results
    from . import source_resident_v3 as resident
    from . import source_ir_v2 as ir
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from local_lab import source_development_results as results
    from local_lab import source_resident_v3 as resident
    from local_lab import source_ir_v2 as ir


PROFILE = "DWI-SDF-QUERY-POPULATION-0.1"


def _packed_queries(queries):
    if not isinstance(queries, list) or not queries:
        raise ValueError("queries: expected a nonempty JSON list of [x,y] coordinate pairs")
    resident.uint(len(queries), "query count", minimum=1)
    packed, bits, rounding = [], [], []
    for index, query in enumerate(queries):
        if not isinstance(query, list) or len(query) != 2:
            raise ValueError(f"queries[{index}]: expected exactly [x,y]")
        coordinates, words = [], []
        for axis, original in enumerate(query):
            value, word = ir.fp32(original, f"queries[{index}][{axis}]")
            # Check the authored value as well as its packed value. A number
            # just outside the domain must not become admissible by rounding.
            if abs(original) > 16 or abs(value) > 16:
                raise ValueError(f"queries[{index}][{axis}]: coordinate must lie in [-16,16]")
            coordinates.append(value)
            words.append(word)
            if value != original:
                rounding.append({"query": index, "axis": axis, "source": original,
                                 "packed": value, "absolute_difference": abs(value - original)})
        packed.append(coordinates)
        bits.append(words)
    return packed, bits, rounding


def _selected_assessment(raw, decoded, manifest, lane):
    """Use the existing reader on one exact instance, without an all-lane oracle."""
    offset, width = decoded["instances_offset_bytes"], 4 * decoded["instance_words"]
    start = offset + lane * width
    image = raw[start:start + width]
    one = bytearray(raw[:offset])
    struct.pack_into("<I", one, 8, 1)
    single = bytes(one) + image
    check_manifest = deepcopy(manifest)
    check_manifest.update(count=1, configuration_sha256=ir.sha256(single[:offset]),
                          program_sha256=ir.sha256(single))
    for kind in ("query_population", "guidance_publication"):
        publication = check_manifest.get(kind)
        if publication is None:
            continue
        if not isinstance(publication, dict):
            raise ValueError(kind + " must be a mapping")
        floor = publication.get("diagnostics_require_epoch_at_least")
        if isinstance(floor, list):
            if len(floor) != decoded["count"]:
                raise ValueError(kind + " needs one diagnostic epoch per source lane")
            if any(type(value) is not int or not 1 <= value <= resident.EXACT_LIMIT for value in floor):
                raise ValueError(kind + " has an invalid diagnostic epoch")
            publication["diagnostics_require_epoch_at_least"] = floor[lane]
    report = results.evaluate_results(single, check_manifest)
    row = report["results"][0]
    if not row["runtime_healthy"]:
        raise ValueError(f"Parent lane {lane} has runtime failure status {row['runtime_status']}")
    if row["epoch"] == 0 or not row["application_diagnostics_evaluated"]:
        raise ValueError(f"Parent lane {lane} has no completed resident query evaluation")
    if not row["assessment_passed"]:
        raise ValueError(f"Parent lane {lane} fails retained-program/diagnostic assessment: "
                         f"{row['program_error'] or 'inspect the source results report'}")
    if row["epoch"] >= resident.EXACT_LIMIT:
        raise ValueError(f"Parent lane {lane} cannot execute another epoch within the resident bound")
    if any(record["generation"] >= resident.EXACT_LIMIT for record in decoded["instances"][lane]["records"]):
        raise ValueError(f"Parent lane {lane} has exhausted the resident record-generation bound")
    if row["native_diagnostics"]["trials"] >= resident.EXACT_LIMIT:
        raise ValueError(f"Parent lane {lane} has exhausted its query/trial counter bound")
    return image, row


def prepare_queries(checkpoint_bytes, manifest, queries, *, lane=0):
    """Return (DWRD0003 query input bytes, updated manifest), without execution.

    Queries are normalized [persistent/M_ref, scratch/M_ref] pairs under the
    existing common-scale resource metric. The selected healthy, evaluated
    parent remains unchanged. Other source lanes need valid native encoding
    but are not selected or merged. New diagnostics are explicitly stale until
    a complete subsequent resident epoch, even when the parent epoch is nonzero.
    """
    if not isinstance(checkpoint_bytes, (bytes, bytearray, memoryview)):
        raise ValueError("checkpoint_bytes must contain the actual retained binary checkpoint")
    raw = bytes(checkpoint_bytes)
    decoded = resident.decode_checkpoint(raw)
    contract = results._manifest_contract(decoded, manifest)
    resident.uint(lane, "parent lane", decoded["count"] - 1)
    packed, query_bits, rounding = _packed_queries(queries)
    if "enabled" not in contract["diagnostic_fields"]:
        raise ValueError("The development manifest lacks the construction-enabled state field")
    image, assessment = _selected_assessment(raw, decoded, manifest, lane)
    count, width, offset = len(queries), decoded["instance_words"], decoded["instances_offset_bytes"]
    resident.checked_size(count * width, "query population instance words")
    resident.checked_size((offset - 8) // 4 + count * width, "query population total words")
    names = contract["state_names"]
    fields = contract["diagnostic_fields"]
    indices = {purpose: names.index(fields[purpose]) for purpose in ("query_x", "query_y", "enabled")}
    parent = decoded["instances"][lane]
    header = bytearray(raw[:offset])
    struct.pack_into("<I", header, 8, count)
    population = bytearray(header)
    changes = []
    for index, words in enumerate(query_bits):
        clone = bytearray(image)
        edits = []
        for purpose, word in zip(("query_x", "query_y", "enabled"), (*words, 0)):
            state_index = indices[purpose]
            before = parent["state_bits"][state_index]
            struct.pack_into("<I", clone, 4 * (6 + state_index), word)
            edits.append({"field": fields[purpose], "state_index": state_index,
                          "before_bits": before, "after_bits": word,
                          "before": resident.float_word(before), "after": resident.float_word(word),
                          "changed": before != word})
        population.extend(clone)
        changes.append({"lane": index, "query": packed[index], "state_writes": edits})
    prepared = bytes(population)
    checked = resident.decode_checkpoint(prepared)
    if prepared[:8] != raw[:8] or prepared[12:offset] != raw[12:offset]:
        raise ValueError("Internal error: query preparation altered static bytes beyond the count word")
    parent_program_bits = b"".join(struct.pack("<I", assessment["program_word_bits"][key])
                                  for key in results.bindings.PROGRAM_NAMES)
    parent_records = image[4 * (6 + decoded["state_width"]):]
    source_query_bytes = ir.json_bytes(queries)
    manifest_bytes = ir.json_bytes(manifest)
    new_manifest = deepcopy(manifest)
    old_files = new_manifest.pop("files", None)
    old_definition_hash = new_manifest.pop("definition_semantic_sha256", None)
    old_rounding = new_manifest.pop("instance_input_fp32_rounding", None)
    old_created = new_manifest.pop("created_at", None)
    old_guidance = new_manifest.pop("guidance_publication", None)
    lineage = {
        "profile": PROFILE,
        "scope": "Forked query population from one retained complete instance, not ordinary checkpoint resume or a host solver.",
        "parent_checkpoint_sha256": ir.sha256(raw),
        "parent_manifest_semantic_sha256": ir.sha256(manifest_bytes),
        "parent_configuration_sha256": decoded["configuration_sha256"],
        "parent_declared_compilation_program_sha256": manifest.get("program_sha256"),
        "parent_count": decoded["count"], "parent_lane": lane, "parent_epoch": parent["epoch"],
        "parent_instance_sha256": ir.sha256(image),
        "parent_program_sha256": assessment["program_sha256"],
        "parent_topology_sha256": assessment["topology_sha256"],
        "parent_semantic_region_sha256": assessment["semantic_sha256"],
        "parent_program_state_sha256": ir.sha256(parent_program_bits),
        "parent_record_table_sha256": ir.sha256(parent_records),
        "parent_program_revision": assessment["program"]["revision"],
        "parent_assessment_passed": assessment["assessment_passed"],
        "parent_compilation_definition_semantic_sha256": old_definition_hash,
        "parent_compilation_input_rounding": old_rounding,
        "parent_artifact_index": old_files, "parent_created_at": old_created,
        "parent_query_population": deepcopy(manifest.get("query_population")),
        "parent_guidance_publication": old_guidance,
        "query_count": count, "queries_sha256": ir.sha256(source_query_bytes),
        "packed_query_words_sha256": ir.sha256(b"".join(struct.pack("<2I", *v) for v in query_bits)),
        "packed_queries": packed, "query_input_fp32_rounding": rounding,
        "diagnostics_require_epoch_at_least": parent["epoch"] + 1,
        "diagnostics_status": "Previous measurements retained byte for byte; run at least one native epoch before reading the new query answers.",
        "construction_enabled": False,
        "change_list": changes,
        "static_change": {"byte_offset": 8, "field": "count", "before": decoded["count"], "after": count},
        "unchanged_static_bytes_after_count_sha256": ir.sha256(raw[12:offset]),
        "preservation": "Complete selected header/epoch, all program words, all record words and every other state word are cloned exactly. Only the two query coordinates and enabled=0 are patched per clone. Ordinary source-cycle state/record evolution still occurs when the native kernel subsequently runs.",
        "preparer_sha256": ir.sha256(Path(__file__).read_bytes()),
    }
    new_manifest.update(count=count, configuration_sha256=checked["configuration_sha256"],
                        program_sha256=ir.sha256(prepared), query_population=lineage,
                        scope="Retained resident SDF forked into a frozen-construction query population; native evaluation pending.")
    # This small index describes bytes reproducible by the pure preparation API.
    # The file CLI adds exact input-file hashes and source-code snapshots.
    new_manifest["files"] = {name: {"bytes": len(data), "sha256": ir.sha256(data)}
                             for name, data in (("program.bin", prepared), ("queries.json", source_query_bytes))}
    results._manifest_contract(checked, new_manifest)
    return prepared, new_manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("prepare")
    command.add_argument("--input", type=Path, required=True, help="Healthy retained DWRD0003 checkpoint")
    command.add_argument("--manifest", type=Path, required=True)
    command.add_argument("--queries", type=Path, required=True, help="JSON list of normalized [x,y] pairs")
    command.add_argument("--lane", type=int, default=0)
    command.add_argument("--output", type=Path, required=True, help="New output directory")
    args = parser.parse_args(argv)
    if args.output.exists():
        raise ValueError("Output directory already exists; query preparation requires a fresh directory")
    manifest, manifest_raw = ir.read_json(args.manifest)
    queries, queries_raw = ir.read_json(args.queries)
    checkpoint = args.input.read_bytes()
    prepared, result = prepare_queries(checkpoint, manifest, queries, lane=args.lane)
    result["created_at"] = datetime.now(timezone.utc).isoformat()
    result["query_population"]["parent_manifest_file_sha256"] = ir.sha256(manifest_raw)
    result["query_population"]["source_queries_file_sha256"] = ir.sha256(queries_raw)
    result["query_population"]["source_files"] = {
        "checkpoint": str(args.input.resolve()), "manifest": str(args.manifest.resolve()),
        "queries": str(args.queries.resolve())}
    files = {"program.bin": prepared, "queries.json": ir.json_bytes(queries),
             "source_queries.json": queries_raw, "source_manifest.json": manifest_raw}
    modules = (sys.modules[__name__], results, resident, ir, results.bindings, results.sdf)
    for module in modules:
        path = Path(module.__file__)
        files["compiler/" + path.name] = path.read_bytes()
    result["files"] = {name: {"bytes": len(data), "sha256": ir.sha256(data)} for name, data in files.items()}
    args.output.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        target = args.output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as handle:
            handle.write(data)
    with (args.output / "manifest.json").open("xb") as handle:
        handle.write(ir.json_bytes(result))
    print(json.dumps({"profile": PROFILE, "output": str(args.output.resolve()), "count": result["count"],
                      "parent_lane": args.lane, "parent_epoch": result["query_population"]["parent_epoch"],
                      "diagnostics_require_epoch_at_least": result["query_population"]["diagnostics_require_epoch_at_least"],
                      "program_sha256": result["program_sha256"], "native_execution_performed": False}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(1)
