"""Verify this extracted Dawnwood release against its SHA-256 manifest."""
from pathlib import Path
import hashlib
import sys
ROOT = Path(__file__).resolve().parents[1]
failures = []
count = 0
for line in (ROOT / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
    expected, relative = line.split("  ", 1)
    path = (ROOT / relative).resolve()
    if ROOT not in path.parents:
        failures.append(relative + ": unsafe manifest path")
        continue
    count += 1
    if not path.is_file():
        failures.append(relative + ": missing")
    elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        failures.append(relative + ": changed")
print(f"Checked {count} files; {len(failures)} failures.")
for item in failures:
    print(item)
sys.exit(1 if failures else 0)
