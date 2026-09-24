"""Export the editable LaTeX manuscript as Markdown using Pandoc."""
from pathlib import Path
import re
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
if shutil.which('pandoc') is None:
    raise SystemExit('Install Pandoc to regenerate the Markdown export.')
source=ROOT/'docs/unified_specification.tex'
target=ROOT/'docs/unified_specification.md'
# TeX spacing has no semantic role in the text export. Expand it before conversion
# to preserve following digits, including the edition day in the title-page table.
text=source.read_text(encoding='utf-8').replace(r'\enspace',' ')
subprocess.run(['pandoc','-f','latex','-t','gfm','--wrap=none','-o',str(target)],input=text,text=True,check=True)
markdown=target.read_text(encoding='utf-8')
markdown=re.sub(r'<span class="sans-serif">(.*?)</span>',r'\1',markdown)
markdown=re.sub(r'</?div[^>]*>\n?', '', markdown)
markdown=markdown.replace('**DAWNWOOD INTERACTIVE**','# Dawnwood Interactive',1)
markdown=re.sub(r'\n{3,}','\n\n',markdown)
target.write_text(markdown.strip()+'\n',encoding='utf-8')
print(target)
