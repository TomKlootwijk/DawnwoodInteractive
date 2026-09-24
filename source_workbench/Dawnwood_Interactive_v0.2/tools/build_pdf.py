"""Rebuild the unified manuscript using a LaTeX installation with pdflatex."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs'
if shutil.which('pdflatex') is None:
    raise SystemExit('Install a LaTeX distribution containing pdflatex and the packages named in the manuscript.')
with tempfile.TemporaryDirectory(prefix='dawnwood_pdf_') as temp:
    for _ in range(3):
        process=subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error',
                                f'-output-directory={temp}','unified_specification.tex'],
                               cwd=DOCS,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        if process.returncode:
            print(process.stdout[-10000:],file=sys.stderr)
            raise SystemExit(process.returncode)
    target=DOCS/'Dawnwood_Interactive_Unified_v0.2.pdf'
    shutil.copy2(Path(temp)/'unified_specification.pdf',target)
print(target)
