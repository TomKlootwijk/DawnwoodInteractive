"""Measure completed full-state runs near the current memory policy boundary.

This runs the normal kernel, not an allocation-only filler or an equivalence test.
Every candidate is a fresh process; raw output and failures remain in --out.
"""
from pathlib import Path
import argparse
import ctypes
import datetime
import hashlib
import json
import math
import os
import subprocess
import time

MIB = 1 << 20
ROOT = Path(__file__).resolve().parents[1]


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def available_memory():
    """Physical headroom on the machine actually launching the binary."""
    if os.name == "nt":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [("length", ctypes.c_uint32), ("load", ctypes.c_uint32)] + [
                (name, ctypes.c_uint64) for name in (
                    "total", "available", "page_total", "page_available",
                    "virtual_total", "virtual_available", "extended_available")]
        status = MemoryStatus()
        status.length = ctypes.sizeof(status)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            raise OSError("GlobalMemoryStatusEx failed")
        return {"available_bytes": status.available, "total_bytes": status.total,
                "source": "GlobalMemoryStatusEx"}
    values = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, value = line.split(":", 1)
        values[key] = int(value.split()[0]) * 1024
    if "MemAvailable" not in values:
        raise RuntimeError("No physical MemAvailable estimate; refusing an unbounded run")
    return {"available_bytes": values["MemAvailable"], "total_bytes": values["MemTotal"],
            "source": "/proc/meminfo MemAvailable"}


def policy(device, host, fraction, reserve, granularity):
    heaps = {int(h["index"]): h for h in device["heaps"]}
    indices = device.get("state_buffer_heaps")
    inferred = False
    if not (isinstance(indices, list) and len(indices) == 2):
        index = device.get("states_heap_index")
        if index is None:
            inferred = True
            choices = [h for h in heaps.values() if h.get("device_local")]
            index = max(choices, key=lambda h: h.get("budget_at_start", h["size"]))["index"]
        indices = [index, index]
    indices = [int(index) for index in indices]
    device_type = device.get("device_type")
    discrete = device_type in (2, "discrete", "discrete_gpu", "VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU")
    # Unknown device types use the conservative shared-memory accounting.
    unified = not discrete
    scratch_enabled = device.get("split_evolution") is True
    scratch_record_bytes = scratch_dispatch_limit = scratch_allowance = 0
    if scratch_enabled:
        scratch_record_bytes = device.get("evolution_scratch_record_bytes")
        scratch_dispatch_limit = device.get("state_dispatch_limit")
        if (type(scratch_record_bytes) is not int or scratch_record_bytes <= 0
                or type(scratch_dispatch_limit) is not int or scratch_dispatch_limit <= 0):
            raise RuntimeError("Split evolution requires reported scratch record size and dispatch limit")
        # Future candidates can be larger than the one-state probe. Reserve the
        # full bounded scratch payload, even for candidates below this limit.
        scratch_allowance = scratch_record_bytes * scratch_dispatch_limit
    limits = {"storage_buffer_range": int(device["max_storage_buffer_range"]) // 128,
              "uint32_state_count": (1 << 32) - 1}
    allocation_limit = device.get("max_memory_allocation_size")
    if allocation_limit:
        limits["single_allocation"] = int(allocation_limit) // 128
    heap_rows = []
    for index in sorted(set(indices)):
        heap = heaps[index]
        budgeted = "budget_at_start" in heap and "usage_at_start" in heap
        free = max(0, int(heap["budget_at_start"]) - int(heap["usage_at_start"])) if budgeted else int(heap["size"])
        usable = max(0, int(fraction * free) - reserve - scratch_allowance)
        bytes_per_state = 128 * indices.count(index)
        limits[f"state_heap_{index}"] = usable // bytes_per_state
        heap_rows.append({"index": index, "available_estimate_bytes": free,
                          "source": "Vulkan process budget minus usage" if budgeted else "heap size; not free RAM",
                          "usable_after_policy_bytes": usable, "state_bytes_per_record": bytes_per_state,
                          "evolution_scratch_allowance_bytes": scratch_allowance})
    # Two GPU records plus one transient CPU snapshot on UMA; only the CPU
    # snapshot on discrete hardware. Runtime uses a bounded 16 MiB staging area.
    host_bytes_per_state = 384 if unified else 128
    host_scratch_allowance = scratch_allowance if unified else 0
    host_usable = max(0, int(.85 * host["available_bytes"]) - reserve - 16 * MIB - host_scratch_allowance)
    limits["physical_host_memory"] = host_usable // host_bytes_per_state
    target = min(limits.values()) // 64 * 64
    return {"target_count": target, "limiting_factor": min(limits, key=limits.get),
            "count_limits": limits, "state_heaps": indices, "heap_selection_inferred": inferred,
            "unified_memory_accounting": unified, "device_type": device_type,
            "host_bytes_per_state_at_peak": host_bytes_per_state, "host_memory": host,
            "heap_policy": heap_rows, "gpu_budget_fraction": fraction,
            "host_available_fraction": .85, "reserve_bytes": reserve,
            "staging_allowance_bytes": 16 * MIB, "refinement_count_granularity": granularity,
            "evolution_scratch_policy": {
                "enabled": scratch_enabled, "record_bytes": scratch_record_bytes,
                "dispatch_record_limit": scratch_dispatch_limit,
                "maximum_payload_allowance_bytes": scratch_allowance,
                "host_allowance_bytes": host_scratch_allowance,
                "charged_state_heap_indices": sorted(set(indices)) if scratch_enabled else [],
                "heap_charge_basis": "Full bound deducted from each state heap; scratch heap is not independently reported" if scratch_enabled else "No split scratch allocation",
                "candidate_charge_basis": "Full dispatch bound, conservative below the dispatch record limit",
                "probe_payload_bytes": device.get("evolution_scratch_bytes"),
                "probe_allocated_bytes": device.get("evolution_scratch_allocated_bytes"),
                "allocation_padding_included_in_allowance": False}}


def completed(record, count, steps):
    report = record.get("report") or {}
    device = report.get("device") or {}
    seconds = report.get("seconds", 0)
    return (record.get("exit_code") == 0 and "error" not in report
            and report.get("health", {}).get("passed") is True
            and report.get("config", {}).get("count") == count
            and report.get("new_epochs") == steps and device.get("completed_epochs") == steps
            and device.get("software_device") is False
            and bool(report.get("state_only_fnv1a64")) and bool(report.get("state_and_operator_fnv1a64"))
            and isinstance(seconds, (int, float)) and math.isfinite(seconds) and seconds > 0)


def allocation_failure(record):
    text = (str(record.get("error", "")) + " " + json.dumps(record.get("report"))
            + " " + record.get("stderr", "")).lower()
    if record.get("timed_out") or any(x in text for x in (
            "device lost", "device_lost", "vkresult -4", "validation reported", "access violation")):
        return False
    return any(x in text for x in ("vkallocatememory", "out of device memory", "out_of_device_memory",
                                  "out of host memory", "bad_alloc", "insufficient", "sufficient reported heap budget"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--device", required=True, help="Explicit physical Vulkan device selector")
    parser.add_argument("--out", type=Path, default=ROOT / "results/capacity")
    parser.add_argument("--budget-fraction", type=float, default=.95)
    parser.add_argument("--reserve-mib", type=int, default=128)
    parser.add_argument("--steps", type=int, default=2)
    parser.add_argument("--granularity", type=int, default=65536, help="Refinement resolution in full states")
    parser.add_argument("--timeout", type=float, default=600, help="Per-process seconds; timeout stops measurement")
    args = parser.parse_args()
    if not (0 < args.budget_fraction <= .98) or args.reserve_mib < 0 or args.steps < 1 or args.steps > 0xffffffff:
        parser.error("Require 0 < budget fraction <= .98, reserve >= 0, and 1..UINT32_MAX steps")
    if args.granularity < 64 or args.granularity % 64 or not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("Granularity must be a positive multiple of 64; timeout must be positive and finite")
    if not args.binary.is_file():
        parser.error("Binary does not exist")
    args.out.mkdir(parents=True, exist_ok=True)
    if any(args.out.iterdir()):
        parser.error("Output directory must be empty so previous evidence is preserved")
    binary = str(args.binary.resolve())
    binary_hash = hashlib.sha256(Path(binary).read_bytes()).hexdigest()
    common = ["--device", args.device, "--budget-fraction", str(args.budget_fraction)]
    records, points, policies = [], [], []
    summary = {"kind": "Full-state GPU capacity measurement", "absolute_hardware_maximum": False,
               "numerical_equivalence_claimed": False, "requested_epochs_per_candidate": args.steps,
               "binary": binary, "binary_sha256": binary_hash,
               "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "device_selector": args.device, "points": points, "policies": policies}

    def run(name, command):
        full_command = [binary] + command + common
        record = {"name": name, "command": full_command, "host_before": available_memory(),
                  "binary_sha256": binary_hash,
                  "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  "validation_environment": {key: os.environ[key] for key in
                      ("DAWNWOOD_VALIDATION", "VK_LAYER_PATH", "VK_LAYER_VALIDATE_SYNC") if key in os.environ}}
        start = time.monotonic()
        stdout_path, stderr_path = args.out / (name + ".stdout"), args.out / (name + ".stderr")
        with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            try:
                process = subprocess.run(full_command, stdout=stdout, stderr=stderr, timeout=args.timeout)
                record["exit_code"] = process.returncode
            except subprocess.TimeoutExpired as error:
                record.update(error=str(error), timed_out=True, exit_code=None)
            except OSError as error:
                record.update(error=str(error), exit_code=None)
        record["wall_seconds"] = time.monotonic() - start
        record["stderr"] = stderr_path.read_text(encoding="utf-8", errors="replace")
        try:
            record["report"] = json.loads(stdout_path.read_text(encoding="utf-8", errors="replace"))
            if not isinstance(record["report"], dict):
                raise ValueError("Expected a JSON object")
        except ValueError as error:
            record["report"] = {"error": "No valid JSON report: " + str(error)}
        write_json(args.out / (name + ".command.json"), record)
        records.append({"name": name, "exit_code": record.get("exit_code")})
        return record

    best, upper, fatal, stop = 0, None, False, ""
    try:
        for attempt in range(80):  # More than enough for uint32 doubling and binary refinement.
            probe = run(f"probe_{attempt:03d}", ["probe", "--count", "1", "--steps", "0"])
            device = probe["report"].get("device")
            if probe.get("exit_code") != 0 or not device or device.get("software_device") is not False:
                fatal, stop = True, "Physical-device probe failed; see raw evidence"
                break
            host = available_memory()
            current = policy(device, host, args.budget_fraction, args.reserve_mib * MIB, args.granularity)
            policies.append(current)
            target = current["target_count"]
            if upper is not None:
                target = min(target, upper - 64)
            if target <= best or (best and upper is not None and target - best < args.granularity):
                stop = "Allocation bracket refined" if upper is not None else "Current memory policy boundary reached"
                break
            candidate = min(target, 65536 if not best else best * 2)
            if upper is not None:
                candidate = ((best + target) // 2) // 64 * 64
            if candidate <= best or candidate < 64:
                stop = "No additional aligned full-state allocation fits the current policy"
                break
            print(f"Advancing {candidate:,} complete states for {args.steps} epochs; policy target {target:,}", flush=True)
            record = run(f"run_{attempt:03d}_{candidate}", ["run", "--backend", "vulkan", "--count", str(candidate),
                         "--steps", str(args.steps), "--batch", "1"])
            if completed(record, candidate, args.steps):
                report, best = record["report"], candidate
                points.append({"count": candidate, "epochs": args.steps, "state_payload_bytes": 128 * candidate,
                               "state_ping_pong_bytes": 256 * candidate, "kernel_seconds": report["seconds"],
                               "timer": report["device"].get("timer", "not reported"),
                               "state_updates_per_second": candidate * args.steps / report["seconds"],
                               "process_wall_seconds": record["wall_seconds"], "health": report["health"],
                               "digest": report["state_and_operator_fnv1a64"], "device": report["device"],
                               "command_record": record["name"] + ".command.json"})
                print(f"Completed: {candidate:,} states, {report['seconds']:.6f} kernel seconds", flush=True)
            elif allocation_failure(record):
                upper = candidate if upper is None else min(upper, candidate)
                print(f"Allocation boundary at {candidate:,}; refining below it", flush=True)
            else:
                fatal, stop = True, "Run failed health/completion checks or had a serious runtime error; growth stopped"
                break
            summary.update(highest_completed_count=best, failed_allocation_upper_count=upper, commands=records)
            write_json(args.out / "summary.json", summary)
        else:
            fatal, stop = True, "Iteration limit reached before a bounded result"
    except Exception as error:
        fatal, stop = True, f"Measurement stopped: {type(error).__name__}: {error}"
    summary.update(highest_completed_count=best, failed_allocation_upper_count=upper, stop_reason=stop,
                   completed_without_serious_error=not fatal and best > 0, commands=records)
    write_json(args.out / "summary.json", summary)
    lines = ["Dawnwood full-state capacity measurement", "", f"Highest completed population: {best:,} states.",
             f"Every counted state advanced {args.steps} epochs; full readback health and digests were required.",
             f"Stopping condition: {stop}.", "This is a current-budget policy result, not an absolute hardware maximum."]
    if points:
        last = points[-1]
        lines += [f"State payload: {last['state_payload_bytes'] / MIB:.2f} MiB; two GPU copies: {last['state_ping_pong_bytes'] / MIB:.2f} MiB.",
                  f"Kernel time: {last['kernel_seconds']:.6f} s ({last['timer']}); {last['state_updates_per_second']:,.0f} state updates/s.",
                  f"Whole process: {last['process_wall_seconds']:.3f} s, including setup and readback."]
    lines += ["Kernel timing follows the recorded device timer; initialization and readback are outside its scope.",
              "Memory capacity does not establish bandwidth, cache residence, occupancy, or CPU/GPU numerical equivalence."]
    (args.out / "CAPACITY.md").write_text("\n\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines), flush=True)
    return 0 if not fatal and best else 2


if __name__ == "__main__":
    raise SystemExit(main())
