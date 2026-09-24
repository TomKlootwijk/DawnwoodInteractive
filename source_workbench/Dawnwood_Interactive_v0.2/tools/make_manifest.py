"""Write SHA-256 hashes for the current package contents."""
from pathlib import Path
import hashlib

ROOT=Path(__file__).resolve().parents[1]
manifest=ROOT/'MANIFEST.sha256'
rows=[]
for path in sorted(ROOT.rglob('*')):
    if path.is_file() and path!=manifest and '__pycache__' not in path.parts and '.pyc'!=path.suffix:
        rows.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT).as_posix()}")
manifest.write_text('\n'.join(rows)+'\n',encoding='utf-8')
print(f'Wrote {len(rows)} file hashes')
