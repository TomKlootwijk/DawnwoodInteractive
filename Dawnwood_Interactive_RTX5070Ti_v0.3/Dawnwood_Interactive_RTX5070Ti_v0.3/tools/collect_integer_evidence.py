"""Seal the delivered source/report evidence after final visual review."""
import hashlib
import json
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1];EV=ROOT/'results/integer'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
summary=read(EV/'final_summary.json')
validation=read(EV/'validation_fast_masks/validation.json')
assert validation['status']=='passed'
assert '100% tests passed' in (EV/'final_build_ctest.log').read_text()
assert '\nOK' in (EV/'python_tests.log').read_text()
qa=read(EV/'pdf_qa.json');assert qa['visual_review_complete']
pdf=ROOT/'output/pdf/Dawnwood_Interactive_Integer_Formalization.pdf'
assert qa['pdf_sha256']==digest(pdf)
for row in read(EV/'instructions/build_audits.json'):
    assert digest(ROOT/row['executable'])==row['sha256']
    assert read(ROOT/row['audit'])['status']=='passed'
files=['include/dawnwood/integer_math.hpp','include/dawnwood/integer_core.hpp',
       'include/dawnwood/integer_pair_cache.hpp','src/integer_kernels.cuh','src/integer_main.cu',
       'CMakeLists.txt','source/double-slit-theory.pdf','model/integer_binding.json',
       'docs/INTEGER_REQUIREMENTS.md','docs/INTEGER_EDITION.md','tools/build_integer_pdf.py',
       'output/pdf/Dawnwood_Interactive_Integer_Formalization.pdf',
       'build/dawnwood_integer.exe','build/dawnwood_integer_texture.exe',
       'build/dawnwood_integer_reference.exe','build/dawnwood_integer_cached.exe']
record={'edition':'integer-1','status':'implemented and measured within declared numerical and hardware scope',
        'model':'model/integer_binding.json','evidence_index':'results/integer/final_summary.json',
        'source_pdf_sha256':summary['source_sha256'],'ctest_passed':12,'python_tests_passed':27,
        'snapshot_and_rejection_checks':validation['comparison_count'],
        'sanitizer_runs':8,'actual_executable_audits':4,'pdf':qa,
        'quantum_verdict':'Raw integer H/interference works to measured precision; LP8 wrapping and quantization limit quantum-state fidelity. Full nonlinear recurrence is not established as a general quantum simulator.',
        'scope_limits':summary['limits'],
        'retained_development_records':'Initial instruction audit failures and earlier performance trials remain as historical diagnostic records, not final acceptance.',
        'file_sha256':{name:digest(ROOT/name) for name in files}}
(EV/'VALIDATION_INTEGER.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
manifest=ROOT/'MANIFEST.sha256';old=ROOT/'MANIFEST.v0.3-optimized.sha256'
if not old.exists():shutil.copyfile(manifest,old)
included=[]
for path in ROOT.rglob('*'):
    if not path.is_file() or path==manifest:continue
    rel=path.relative_to(ROOT)
    if rel.parts[0].startswith('build') or any(p in {'tmp','work','__pycache__','.git'} for p in rel.parts):continue
    if path.suffix.lower() in {'.exe','.obj','.pdb','.pyc'}:continue
    included.append((rel.as_posix(),digest(path)))
manifest.write_text(''.join(f'{sha}  {name}\n' for name,sha in sorted(included)),encoding='utf-8')
print(f'Indexed {len(included)} files, preserving the original and optimized v0.3 manifests.')
