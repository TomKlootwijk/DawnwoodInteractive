"""Measure real Android full-state capacity through the installed Dawnwood app.

No phone measurement is implied by this file existing. Run only with an authorized
ADB device. This measures completed circulation and health, not CPU equivalence.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import math
import shutil
import subprocess
import time

from measure_capacity import MIB, allocation_failure, completed, policy, write_json

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "nl.dawnwood.kernel"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial")
    parser.add_argument("--apk", type=Path, help="Optionally install this APK and record its SHA256")
    parser.add_argument("--out", type=Path, default=ROOT / "results/phone_capacity")
    parser.add_argument("--steps", type=int, default=2)
    parser.add_argument("--budget-fraction", type=float, default=.95)
    parser.add_argument("--reserve-mib", type=int, default=128)
    parser.add_argument("--granularity", type=int, default=65536)
    parser.add_argument("--timeout", type=float, default=600)
    args = parser.parse_args()
    if not (0 < args.budget_fraction <= .98) or args.reserve_mib < 0:
        parser.error("Require 0 < budget fraction <= .98 and reserve >= 0")
    if not (1 <= args.steps <= 0x7fffffff) or args.granularity < 64 or args.granularity % 64:
        parser.error("Android steps must fit a positive signed int; granularity must be a positive multiple of 64")
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("Timeout must be positive and finite")
    if args.apk and not args.apk.is_file():
        parser.error("APK does not exist")
    adb = shutil.which("adb")
    if not adb:
        parser.error("Install Android platform-tools; adb was not found")
    args.out.mkdir(parents=True, exist_ok=True)
    if any(args.out.iterdir()):
        parser.error("Output directory must be empty to preserve previous evidence")
    base = [adb] + (["-s", args.serial] if args.serial else [])
    summary = {"kind": "Actual Android full-state capacity measurement",
               "absolute_hardware_maximum": False, "numerical_equivalence_claimed": False,
               "cache_residence_claimed": False, "requested_epochs_per_candidate": args.steps,
               "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "apk_path": str(args.apk.resolve()) if args.apk else None,
               "apk_sha256": hashlib.sha256(args.apk.read_bytes()).hexdigest() if args.apk else None,
               "points": [], "policies": [], "commands": []}
    command_index = 0

    def adb_run(*command, timeout=30):
        nonlocal command_index
        full = base + list(command)
        start = time.monotonic()
        record = {"index": command_index, "command": full,
                  "utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
        command_index += 1
        try:
            process = subprocess.run(full, capture_output=True, text=True, errors="replace", timeout=timeout)
            record.update(exit_code=process.returncode, stdout=process.stdout, stderr=process.stderr)
        except subprocess.TimeoutExpired as error:
            record.update(exit_code=None, stdout="", stderr=str(error), timed_out=True)
        except OSError as error:
            record.update(exit_code=None, stdout="", stderr=str(error))
        record["wall_seconds"] = time.monotonic() - start
        with (args.out / "adb_commands.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, allow_nan=False) + "\n")
        return record

    def require(*command, timeout=30):
        result = adb_run(*command, timeout=timeout)
        if result["exit_code"] != 0:
            raise RuntimeError("ADB command failed: " + " ".join(command) + ": " + result["stderr"])
        return result["stdout"].strip()

    def launch(name, command, count, steps):
        identifier = "capacity_" + str(time.time_ns())
        require("shell", "am", "force-stop", PACKAGE)
        launch_record = adb_run("shell", "am", "start", "-n", PACKAGE + "/.MainActivity",
                                "--ez", "autorun", "true", "--es", "command", command,
                                "--es", "run_id", identifier, "--ei", "count", str(count),
                                "--ei", "steps", str(steps), "--ei", "batch", "1",
                                "--ef", "budget_fraction", str(args.budget_fraction))
        started = time.monotonic()
        record = {"name": name, "run_id": identifier, "launch": launch_record,
                  "exit_code": None, "report": {}, "stderr": "", "requested_count": count,
                  "requested_epochs": steps, "APK_hash": summary["apk_sha256"]}
        pids = set()
        if launch_record["exit_code"] != 0 or "Error:" in launch_record["stdout"]:
            record["error"] = "Activity launch failed"
        else:
            while time.monotonic() - started < args.timeout:
                live = adb_run("shell", "pidof", PACKAGE)
                current = {pid for pid in live["stdout"].split() if pid.isdigit()}
                pids.update(current)
                result = adb_run("shell", "run-as", PACKAGE, "cat", "files/reports/" + identifier + ".json")
                if result["exit_code"] == 0:
                    try:
                        envelope = json.loads(result["stdout"])
                        runtime = envelope.get("runtime")
                        native = envelope.get("native_arguments", [])
                        if envelope.get("run_id") != identifier or envelope.get("finished") is not True or not isinstance(runtime, dict):
                            raise ValueError("Incomplete or unexpected run report")
                        if "--budget-fraction" not in native or "--batch" not in native:
                            raise ValueError("Installed APK lacks v0.5 capacity argument forwarding; rebuild/install it")
                        if native[native.index("--batch") + 1] != "1" or abs(float(native[native.index("--budget-fraction") + 1]) - args.budget_fraction) > 1e-6:
                            raise ValueError("Installed APK did not forward requested capacity policy")
                        record.update(report=runtime, android_report=name + ".android.json",
                                      android_before=envelope["android_before"], android_after=envelope["android_after"],
                                      native_arguments=native, report_finished=True)
                        # JNI returns a JSON result, not a native process exit code.
                        # This completion status is synthetic and explicitly labeled.
                        record["exit_code"] = 0 if "error" not in runtime else 2
                        record["completion_code_is_synthetic"] = True
                        write_json(args.out / (name + ".android.json"), envelope)
                    except (ValueError, KeyError, IndexError, TypeError) as error:
                        record["error"] = "Invalid completed app report: " + str(error)
                    break
                if not current and time.monotonic() - started >= 10:
                    record["error"] = "App process disappeared without a completed report"
                    exits = adb_run("shell", "dumpsys", "activity", "exit-info", PACKAGE)
                    (args.out / (name + ".exit_info.txt")).write_text(exits["stdout"] + exits["stderr"], encoding="utf-8")
                    break
                time.sleep(1)
            else:
                record.update(error="No completed report before timeout", timed_out=True)
        for pid in sorted(pids):
            logs = adb_run("logcat", "-d", "--pid=" + pid)
            (args.out / (name + ".pid_" + pid + ".logcat.txt")).write_text(logs["stdout"] + logs["stderr"], encoding="utf-8")
        record["wall_seconds"] = time.monotonic() - started
        record["observed_pids"] = sorted(pids)
        write_json(args.out / (name + ".command.json"), record)
        summary["commands"].append(name + ".command.json")
        return record

    best, upper, fatal, stop, connected = 0, None, False, "", False
    try:
        if require("get-state") != "device":
            raise RuntimeError("ADB device is not authorized/ready")
        connected = True
        if args.apk:
            require("install", "-r", str(args.apk.resolve()), timeout=120)
        summary["device_identity"] = {"serial": require("get-serialno")}
        for field, prop in (("model", "ro.product.model"), ("manufacturer", "ro.product.manufacturer"),
                            ("brand", "ro.product.brand"), ("market_name", "ro.product.marketname"),
                            ("device", "ro.product.device")):
            summary["device_identity"][field] = require("shell", "getprop", prop)
        package = adb_run("shell", "dumpsys", "package", PACKAGE)
        (args.out / "installed_package.txt").write_text(package["stdout"] + package["stderr"], encoding="utf-8")
        for attempt in range(80):
            probe = launch(f"probe_{attempt:03d}", "probe", 1, 0)
            device = probe["report"].get("device")
            if probe.get("exit_code") != 0 or not device or device.get("software_device") is not False:
                raise RuntimeError("Physical Android Vulkan probe failed; see raw report")
            context = probe["android_after"]
            if context.get("system_low_memory") is not False:
                raise RuntimeError("Android reports low memory; growth stopped")
            if context.get("android_thermal_status", 0) >= 4:
                raise RuntimeError("Android reports critical-or-higher thermal status; growth stopped")
            host = {"available_bytes": int(context["system_available_ram_bytes"]),
                    "total_bytes": int(context["system_total_ram_bytes"]),
                    "source": "Actual Android ActivityManager.MemoryInfo after probe"}
            if host["available_bytes"] <= 0 or "system_low_memory_threshold_bytes" not in context:
                raise RuntimeError("Android available-memory/threshold evidence is missing")
            reserve = max(args.reserve_mib * MIB, int(context["system_low_memory_threshold_bytes"]))
            current = policy(device, host, args.budget_fraction, reserve, args.granularity)
            current.update(android_context=context, requested_reserve_bytes=args.reserve_mib * MIB,
                           effective_reserve_bytes=reserve, Android_INT_MAX=0x7fffffff)
            current["target_count"] = min(current["target_count"], 0x7fffffff) // 64 * 64
            summary["policies"].append(current)
            target = min(current["target_count"], upper - 64) if upper is not None else current["target_count"]
            if target <= best or (best and upper is not None and target - best < args.granularity):
                stop = "Allocation bracket refined" if upper is not None else "Current Android memory policy boundary reached"
                break
            candidate = min(target, 65536 if not best else best * 2)
            if upper is not None:
                candidate = ((best + target) // 2) // 64 * 64
            if candidate <= best or candidate < 64:
                stop = "No further aligned complete population fits the Android policy"
                break
            print(f"Phone: advancing {candidate:,} complete states for {args.steps} epochs", flush=True)
            record = launch(f"run_{attempt:03d}_{candidate}", "run", candidate, args.steps)
            if completed(record, candidate, args.steps):
                report, best = record["report"], candidate
                summary["points"].append({"count": candidate, "epochs": args.steps,
                    "state_payload_bytes": candidate * 128, "state_ping_pong_bytes": candidate * 256,
                    "kernel_seconds": report["seconds"], "timer": report["device"].get("timer"),
                    "state_updates_per_second": candidate * args.steps / report["seconds"],
                    "elapsed_launch_report_seconds": record["wall_seconds"], "health": report["health"],
                    "digest": report["state_and_operator_fnv1a64"], "device": report["device"],
                    "android_before": record["android_before"], "android_after": record["android_after"],
                    "command_record": record["name"] + ".command.json"})
            elif allocation_failure(record):
                upper = candidate if upper is None else min(upper, candidate)
            else:
                raise RuntimeError("Phone run failed health/completion or process checks; growth stopped")
            summary.update(highest_completed_count=best, failed_allocation_upper_count=upper)
            write_json(args.out / "summary.json", summary)
        else:
            raise RuntimeError("Iteration limit reached")
    except Exception as error:
        fatal, stop = True, str(error)
    finally:
        if connected:
            adb_run("shell", "am", "force-stop", PACKAGE)
    summary.update(highest_completed_count=best, failed_allocation_upper_count=upper, stop_reason=stop,
                   real_phone_run_completed=best > 0, completed_without_serious_error=not fatal and best > 0)
    write_json(args.out / "summary.json", summary)
    lines = ["Dawnwood Android full-state capacity measurement", "",
             f"Highest completed population: {best:,} states, {args.steps} epochs per candidate.",
             f"Stopping condition: {stop}.",
             "Uses actual Android available RAM and low-memory threshold; system RAM is not dedicated VRAM.",
             "This is a current-policy capacity result, not an absolute maximum or a numerical-equivalence claim.",
             "All ADB commands, completed reports, and own-process logs are retained."]
    (args.out / "CAPACITY.md").write_text("\n\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if not fatal and best else 2


if __name__ == "__main__":
    raise SystemExit(main())
