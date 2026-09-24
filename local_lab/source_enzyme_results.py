"""Export resident enzyme results and explicit numerical diagnostics as JSON.

This reads the returned checkpoint; it never projects or repairs a candidate.
Feasibility tolerance and the resident FP32 gap estimate are reported separately.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

try:
    from . import source_resident_v2 as resident
except ImportError:
    import source_resident_v2 as resident


SPECIES = ("E", "S", "ES", "P")


def positive(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("expected a finite positive number")
    return number


def export_results(checkpoint, manifest_path, feasibility_tolerance=1e-5,
                   gap_tolerance=1e-5):
    if any(not math.isfinite(x) or x <= 0
           for x in (feasibility_tolerance, gap_tolerance)):
        raise ValueError("Diagnostic tolerances must be finite and positive")
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    metadata = manifest.get("definition_metadata", {}).get("source", {}).get("enzyme")
    if not isinstance(metadata, dict) or metadata.get("input_profile") != "DWI-ENZYME-0.1":
        raise ValueError("Manifest does not declare the DWI-ENZYME-0.1 specialization")
    pools = metadata["pools"]
    enzyme_total = pools["E_total_uM"]
    substrate_total = pools["S_total_uM"]
    scale = pools["concentration_scale_uM"]
    if not (0 < enzyme_total < substrate_total and scale > 0
            and all(math.isfinite(x) for x in (enzyme_total, substrate_total, scale))):
        raise ValueError("Manifest pool totals or concentration scale are invalid")
    result = resident.inspect_checkpoint(Path(checkpoint), manifest_path)
    ids = metadata["observation_ids"]
    if len(ids) != result["count"] or len(set(ids)) != len(ids):
        raise ValueError("Manifest observation IDs do not match the checkpoint")
    tolerance_uM = feasibility_tolerance * scale
    rows = []
    for sample_id, instance in zip(ids, result["instances"]):
        state = instance["named_state"]
        observed = {name + "_uM": state["obs_" + name + "_normalized"] * scale
                    for name in SPECIES}
        species = {name + "_uM": state["enzyme_" + name + "_uM"] for name in SPECIES}
        residual_e = species["E_uM"] + species["ES_uM"] - enzyme_total
        residual_s = species["S_uM"] + species["ES_uM"] + species["P_uM"] - substrate_total
        minimum = min(species.values())
        healthy = instance["status"] == 0
        feasible = (healthy and abs(residual_e) <= tolerance_uM
                    and abs(residual_s) <= tolerance_uM and minimum >= -tolerance_uM)
        gap = state["enzyme_gap_estimate"]
        evaluated = healthy and instance["epoch"] >= 1
        family = next(record["slot_definitions"]["body"]
                      for record in instance["records"] if record["key"] == "blend")
        rows.append({
            "id": sample_id,
            "epoch": instance["epoch"],
            "runtime_status": instance["status"],
            "runtime_healthy": healthy,
            "application_diagnostics_evaluated": evaluated,
            "executed_observation_uM": observed,
            "returned_species_uM": species,
            "conservation_residuals_uM": {"E_plus_ES_minus_total": residual_e,
                                         "S_plus_ES_plus_P_minus_total": residual_s},
            "minimum_returned_species_uM": minimum,
            "feasible_within_declared_tolerance": feasible,
            "resident_objective_normalized_squared": state["enzyme_objective"],
            "returned_correction_distance_uM": math.sqrt(sum(
                (species[key] - observed[key]) ** 2 for key in species)),
            "resident_optimality_gap_estimate_normalized_squared": gap if evaluated else None,
            "gap_estimate_below_requested_threshold": evaluated and 0 <= gap <= gap_tolerance,
            "trial_intrinsic_sdf_normalized": state["enzyme_trial_sdf"] if evaluated else None,
            "trial_projection_distance_normalized": state["enzyme_projection_distance"] if evaluated else None,
            "last_proposal_accepted": bool(state["enzyme_accepted"]) if evaluated else None,
            "last_objective_improvement": state["enzyme_improvement"] if evaluated else None,
            "last_step": state["enzyme_step"] if evaluated else None,
            "current_proposal_family": family,
        })
    return {
        "profile": "DWI-ENZYME-0.1-results",
        "scope": "Readout of the resident enzyme-consistency application; no host correction or projection.",
        "checkpoint_sha256": hashlib.sha256(Path(checkpoint).read_bytes()).hexdigest(),
        "configuration_sha256": result["configuration_sha256"],
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "pools": pools,
        "species_order": list(SPECIES),
        "metric": "Equal-weight Euclidean distance in the four concentrations, using one common scale.",
        "feasibility_tolerance_normalized": feasibility_tolerance,
        "feasibility_tolerance_uM": tolerance_uM,
        "gap_threshold_normalized_squared": gap_tolerance,
        "gap_interpretation": "Resident FP32 estimate of a convex objective-gap bound; not an interval-certified bound or a proof of exact nearest projection.",
        "observation_precision": "Executed normalized FP32 inputs multiplied by the declared common scale; original decimal inputs may have rounded.",
        "all_runtime_healthy": all(row["runtime_healthy"] for row in rows),
        "all_feasible_within_declared_tolerance": all(row["feasible_within_declared_tolerance"] for row in rows),
        "all_gap_estimates_below_requested_threshold": all(row["gap_estimate_below_requested_threshold"] for row in rows),
        "results": rows,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["results"])
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--feasibility-tolerance", type=positive, default=1e-5,
                        help="Normalized concentration tolerance for readout diagnostics")
    parser.add_argument("--gap-tolerance", type=positive, default=1e-5,
                        help="Threshold applied to the resident FP32 gap estimate")
    args = parser.parse_args(argv)
    report = export_results(args.checkpoint, args.manifest, args.feasibility_tolerance,
                            args.gap_tolerance)
    raw = (json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    if args.output is None:
        sys.stdout.buffer.write(raw)
    else:
        with args.output.open("xb") as handle:
            handle.write(raw)
        print(json.dumps({"output": str(args.output.resolve()), "count": len(report["results"]),
                          "all_runtime_healthy": report["all_runtime_healthy"],
                          "all_feasible_within_declared_tolerance": report["all_feasible_within_declared_tolerance"],
                          "all_gap_estimates_below_requested_threshold": report["all_gap_estimates_below_requested_threshold"]}))
    return 0 if report["all_runtime_healthy"] else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(1)
