from __future__ import annotations
from pathlib import Path
import hashlib,json,zipfile
import fitz
import numpy as np

ROOT=Path('/mnt/data')
WORK=ROOT/'_upgrade/work'
FINAL=ROOT/'Tom_Klootwijk_Ontological_Deterministic_Computing_Revision16.pdf'
compiled=fitz.open(WORK/'upgrade.pdf')
baseline=fitz.open(WORK/'kernel_original.pdf')
offset=len(compiled)-len(baseline)
names=compiled.resolve_names()
new=fitz.open()
# Import only the newly authored pages. Append the source as native PDF pages,
# avoiding rescaling, duplicate headers, or a regenerated baseline text layer.
new.insert_pdf(compiled,from_page=0,to_page=offset-1,links=False,annots=False)
new.insert_pdf(baseline,links=True,annots=True)


def target(info:dict) -> tuple[int,fitz.Point]:
    """Resolve XeLaTeX named destinations to concrete MuPDF coordinates."""
    if info.get('kind')==fitz.LINK_NAMED:
        loc=names.get(info.get('nameddest',''),info)
        page=loc.get('page',info.get('page',-1))
        xy=loc.get('to')
        point=fitz.Point(xy)*compiled[page].transformation_matrix if xy is not None else fitz.Point(0,0)
    else:
        page=info.get('page',-1);point=fitz.Point(info.get('to',(0,0)))
    if not 0<=page<len(new): raise ValueError(f'unresolved destination: {info}')
    return page,point

main_links=0
for i in range(offset):
    for link in compiled[i].get_links():
        if link['kind'] in (fitz.LINK_GOTO,fitz.LINK_NAMED):
            page,point=target(link)
            spec={'kind':fitz.LINK_GOTO,'from':link['from'],'page':page,'to':point,'zoom':0}
        elif link['kind']==fitz.LINK_URI:
            spec={'kind':fitz.LINK_URI,'from':link['from'],'uri':link['uri']}
        else:
            raise ValueError(f'Unhandled authored link kind {link}')
        new[i].insert_link(spec);main_links+=1

outline=[]
for level,title,page,info in compiled.get_toc(simple=False):
    if page<=offset:
        dest,point=target(info)
        outline.append([level,title,dest+1,{'kind':fitz.LINK_GOTO,'page':dest,'to':point,'zoom':0}])
outline.append([1,'Revision 15 | complete authoritative source',offset+1])
groups=[(1,'Core, source authority and finite field'),(35,'FI | Field-guided individual'),(39,'PX | Local Psi and f8'),(44,'HP | Hadamard routing'),(50,'GD | Dyadic growth'),(58,'OG | Parameterized organogram'),(69,'W | Forward interface and recovery'),(84,'DP | Directional formal-first contract'),(98,'DP / Wv2 | Recorded implementation evidence'),(101,'VP / Wv3 | Formal-only volume contract')]
original_titles={page:title for _,title,page in baseline.get_toc()}
starts={a:b for a,b in groups}
for p in range(1,len(baseline)+1):
    if p in starts: outline.append([2,starts[p],offset+p])
    outline.append([3,f'K-{p} | {original_titles.get(p,"Source page")}',offset+p])
new.set_toc(outline,collapse=1)
new.set_page_labels([{'startpage':0,'prefix':'U-','style':'D','firstpagenum':1},{'startpage':offset,'prefix':'K-','style':'D','firstpagenum':1}])
new.set_metadata({'title':'TK-LPLUT-2.0 Revision 16 - Corpus-integrated kernel edition','author':'Tom Klootwijk (paradigm author); AI-assisted revision preparation','subject':'Ontological Deterministic Computing: exact retained kernel, latch/pinion integration and scoped arithmetic checks','keywords':'TK-LPLUT, RP32, OTAN2, latch, pinion, SDF, Klein, Revision 16','creator':'Source-grounded Revision 16 document preparation','producer':'XeLaTeX and native PDF assembly','creationDate':'D:20261002000000Z','modDate':'D:20261002000000Z'})

# Verify native appended pages against the actual original, including all pixels
# in a 72-dpi reference render. This is a document preservation check, not a
# verification of the original kernel's mathematical or runtime claims.
rows=[]
for i in range(len(baseline)):
    a=baseline[i];b=new[offset+i]
    pa=a.get_pixmap(matrix=fitz.Matrix(1,1),alpha=False)
    pb=b.get_pixmap(matrix=fitz.Matrix(1,1),alpha=False)
    exact=(pa.width,pa.height,pa.samples)==(pb.width,pb.height,pb.samples)
    text=a.get_text()==b.get_text()
    rows.append({'source_page':i+1,'output_page':offset+i+1,'text_exact_equal':text,'render_pixels_exact_equal_at_72dpi':exact})
    if not text or not exact: raise AssertionError(rows[-1])

# Confirm new text is within page bounds; ignore whitespace and font ascender
# extents outside individual lines, but reject actual off-page text boxes.
text_violations=[]
replacement_glyphs=[]
for i in range(offset):
    page=new[i]
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines',[]):
            for span in line['spans']:
                if not span['text'].strip():continue
                r=fitz.Rect(span['bbox'])
                if r.x0 < -0.1 or r.y0 < -0.1 or r.x1>page.rect.width+0.1 or r.y1>page.rect.height+0.1:
                    text_violations.append({'page':i+1,'text':span['text'],'bbox':list(r)})
                if '\ufffd' in span['text']: replacement_glyphs.append({'page':i+1,'text':span['text']})
if text_violations or replacement_glyphs:raise AssertionError((text_violations,replacement_glyphs))

audit={'format':'tk-lplut-rev16-document-audit-v1','new_pages':offset,'retained_source_pages':len(baseline),'total_pages':len(new),'baseline_original_sha256':hashlib.sha256((WORK/'kernel_original.pdf').read_bytes()).hexdigest(),'native_source_page_text_matches':sum(x['text_exact_equal'] for x in rows),'native_source_page_pixel_matches_72dpi':sum(x['render_pixels_exact_equal_at_72dpi'] for x in rows),'authored_links_recreated':main_links,'bookmarks':len(outline),'off_page_new_text_spans':text_violations,'replacement_glyphs':replacement_glyphs,'scope':'Document construction and byte/page preservation only. Not kernel runtime verification.','pages':rows}
(WORK/'document_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
attachments={
 'revision15-original.pdf':WORK/'kernel_original.pdf',
 'independent_reference.py':WORK/'independent_reference.py',
 'independent_checks.json':WORK/'independent_checks.json',
 'source_manifest.json':WORK/'source_manifest.json',
 'document_audit.json':WORK/'document_audit.json',
 'README.txt':WORK/'README.txt',
}
for name,path in attachments.items():new.embfile_add(name,path.read_bytes(),filename=name,ufilename=name,desc='Revision 16 supporting material: '+name)
new.save(FINAL,garbage=4,deflate=True)
new.close()

# Reopen the delivered bytes to verify all embedded assets, navigation and labels.
check=fitz.open(FINAL)
assert check.page_count==offset+117
assert check[0].get_label()=='U-1' and check[offset].get_label()=='K-1' and check[-1].get_label()=='K-117'
for name,path in attachments.items():assert check.embfile_get(name)==path.read_bytes()
all_links=[(i,l) for i,p in enumerate(check) for l in p.get_links()]
assert all(0<=l['page']<len(check) for _,l in all_links if l['kind']==fitz.LINK_GOTO)
assert sum(len(check[i].get_links()) for i in range(offset))==main_links

bundle=ROOT/'TK_LPLUT_Revision16_Reproducibility.zip'
with zipfile.ZipFile(bundle,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for fn in ['independent_reference.py','independent_checks.json','source_manifest.json','document_audit.json','README.txt','upgrade.tex','checks_table.tex','kernel_original.pdf','finalize_pdf.py']:
        z.write(WORK/fn,fn)
    z.writestr('DELIVERABLE_SHA256.txt',hashlib.sha256(FINAL.read_bytes()).hexdigest()+'  '+FINAL.name+'\n')
print(json.dumps({'pdf':str(FINAL),'pdf_bytes':FINAL.stat().st_size,'pages':len(check),'new_pages':offset,'baseline_pages':117,'bookmarks':len(check.get_toc()),'links':len(all_links),'attachments':check.embfile_names(),'native_pixel_matches':117,'bundle':str(bundle),'bundle_bytes':bundle.stat().st_size},indent=2))
