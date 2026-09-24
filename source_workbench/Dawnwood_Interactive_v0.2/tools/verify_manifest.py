"""Verify the file contents recorded in MANIFEST.sha256."""
from pathlib import Path
import hashlib
import sys

ROOT=Path(__file__).resolve().parents[1]
failures=[];count=0
for line in (ROOT/'MANIFEST.sha256').read_text(encoding='utf-8').splitlines():
    digest,name=line.split('  ',1)
    path=ROOT/name
    count+=1
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
        failures.append(name)
if failures:
    print('Changed or missing files:\n'+'\n'.join(failures),file=sys.stderr)
    raise SystemExit(1)
print(f'Verified {count} file hashes')
