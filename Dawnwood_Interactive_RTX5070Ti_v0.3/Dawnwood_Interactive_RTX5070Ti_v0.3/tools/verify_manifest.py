#!/usr/bin/env python3
"""Verify every listed packaged file, without executing the CUDA kernel."""
import hashlib
from pathlib import Path

root = Path(__file__).resolve().parents[1]
count = 0
for line in (root / 'MANIFEST.sha256').read_text(encoding='utf-8').splitlines():
    expected, relative = line.split('  ', 1)
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise SystemExit(f'Invalid or missing manifest path: {relative}')
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f'Hash mismatch: {relative}')
    count += 1
print(f'PASS {count} SHA-256 file hashes')
