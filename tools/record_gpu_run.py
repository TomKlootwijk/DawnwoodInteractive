"""Record a real command and optional NVIDIA telemetry; no synthetic workload.

Use this with Dawnwood's existing selftest, verify, run and capacity commands.
Each name is immutable so a later attempt cannot overwrite a failed observation.
"""
import argparse
import csv
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import threading
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--telemetry", action="store_true")
    parser.add_argument("--gpu", default="0")
    parser.add_argument("--temperature-stop", type=float, default=88)
    parser.add_argument("--timeout", type=float, default=1800)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or Path(args.name).name != args.name:
        parser.error("A command and a plain filename stem are required")
    args.out.mkdir(parents=True, exist_ok=True)
    stem = args.out / args.name
    receipt = stem.with_suffix(".command.json")
    if receipt.exists() or stem.with_suffix(".stdout").exists():
        parser.error("This run name already exists; choose a fresh name")
    record = {"command": command, "cwd": os.getcwd(),
              "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "environment": {k: v for k, v in os.environ.items()
                              if k.startswith("DAWNWOOD_") or k in ("VK_LAYER_PATH", "VK_LAYER_VALIDATE_SYNC")}}
    executable = Path(command[0])
    if executable.is_file():
        record["executable_sha256"] = hashlib.sha256(executable.read_bytes()).hexdigest()
    receipt.write_text(json.dumps(record, indent=2) + "\n")
    hidden = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    monitor = None
    samples = []
    stop_reason = []
    telemetry_fields = ["timestamp", "name", "utilization.gpu", "utilization.memory",
                        "memory.used", "memory.total", "temperature.gpu", "power.draw",
                        "power.limit", "clocks.current.sm", "clocks.current.memory", "pstate",
                        "clocks_event_reasons.sw_power_cap", "clocks_event_reasons.sw_thermal_slowdown",
                        "clocks_event_reasons.hw_thermal_slowdown"]
    with stem.with_suffix(".stdout").open("wb") as stdout, stem.with_suffix(".stderr").open("wb") as stderr:
        start = time.perf_counter()
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr, creationflags=hidden)
        if args.telemetry:
            monitor_errors = stem.with_suffix(".telemetry.stderr").open("w")
            try:
                monitor = subprocess.Popen(["nvidia-smi", "-i", args.gpu,
                    "--query-gpu=" + ",".join(telemetry_fields), "--format=csv,nounits", "--loop-ms=1000"],
                    stdout=subprocess.PIPE, stderr=monitor_errors, text=True, creationflags=hidden)
            except OSError as error:
                record["telemetry_error"] = str(error)

            def collect():
                with stem.with_suffix(".telemetry.csv").open("w", newline="") as output:
                    for line in monitor.stdout:
                        output.write(line)
                        output.flush()
                        row = next(csv.reader([line], skipinitialspace=True))
                        if len(row) != len(telemetry_fields) or row[0] == "timestamp":
                            continue
                        sample = dict(zip(telemetry_fields, row))
                        samples.append(sample)
                        try:
                            if float(sample["temperature.gpu"]) >= args.temperature_stop and process.poll() is None:
                                stop_reason.append("GPU temperature reached the configured stop threshold")
                                process.terminate()
                        except ValueError:
                            pass

            if monitor:
                thread = threading.Thread(target=collect, daemon=True)
                thread.start()
        try:
            record["exit_code"] = process.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            record["exit_code"] = process.wait()
            stop_reason.append("Command timeout")
        record["process_wall_seconds"] = time.perf_counter() - start
        if monitor:
            monitor.terminate()
            monitor.wait(timeout=10)
            thread.join(timeout=10)
            monitor_errors.close()
    if stop_reason:
        record["stopped"] = stop_reason
    if args.telemetry:
        summary = {"sample_count": len(samples), "sample_interval_ms": 1000,
                   "scope": "Whole command including setup and readback; device-wide NVML observations",
                   "temperature_stop_celsius": args.temperature_stop}
        for key in telemetry_fields[2:11]:
            values = []
            for row in samples:
                try:
                    values.append(float(row[key]))
                except ValueError:
                    pass
            summary[key] = {"min": min(values), "max": max(values), "mean": sum(values) / len(values)} if values else None
        for key in telemetry_fields[12:]:
            summary[key] = {"active_samples": sum(row[key] == "Active" for row in samples)}
        record["telemetry"] = summary
    try:
        report = json.loads(stem.with_suffix(".stdout").read_text(encoding="utf-8"))
        record["report_passed"] = report.get("passed", report.get("health", {}).get("passed"))
    except (ValueError, AttributeError):
        pass
    receipt.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    print(json.dumps(record, indent=2))
    return record["exit_code"] if record["exit_code"] else (2 if stop_reason or record.get("report_passed") is False else 0)


if __name__ == "__main__":
    raise SystemExit(main())
