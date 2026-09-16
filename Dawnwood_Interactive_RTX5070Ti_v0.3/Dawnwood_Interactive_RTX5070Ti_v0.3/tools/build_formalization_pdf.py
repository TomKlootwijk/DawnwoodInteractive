"""Build the measured Dawnwood formalization directly from saved evidence."""
from pathlib import Path
import csv
import io
import json
import statistics
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, String, Line, PolyLine

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'results/optimization'
OUT = ROOT/'output/pdf/Dawnwood_Interactive_Optimized_Formalization.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
pdfmetrics.registerFont(TTFont('Calibri', 'C:/Windows/Fonts/calibri.ttf'))
pdfmetrics.registerFont(TTFont('CalibriB', 'C:/Windows/Fonts/calibrib.ttf'))
pdfmetrics.registerFont(TTFont('CalibriI', 'C:/Windows/Fonts/calibrii.ttf'))
pdfmetrics.registerFont(TTFont('Consolas', 'C:/Windows/Fonts/consola.ttf'))
pdfmetrics.registerFontFamily('Calibri', normal='Calibri', bold='CalibriB', italic='CalibriI', boldItalic='CalibriB')
NAVY = colors.HexColor('#152B3B')
TEAL = colors.HexColor('#087F8C')
GRAY = colors.HexColor('#51636F')
PALE = colors.HexColor('#EDF4F6')
ORANGE = colors.HexColor('#A95128')
ST = getSampleStyleSheet()
ST.add(ParagraphStyle(name='BodyD', fontName='Calibri', fontSize=10.5, leading=14.2, textColor=NAVY, spaceAfter=8))
ST.add(ParagraphStyle(name='SmallD', parent=ST['BodyD'], fontSize=9, leading=11.8, spaceAfter=5))
ST.add(ParagraphStyle(name='H1D', fontName='CalibriB', fontSize=24, leading=28, textColor=NAVY, spaceAfter=16))
ST.add(ParagraphStyle(name='H2D', fontName='CalibriB', fontSize=13, leading=17, textColor=TEAL, spaceBefore=8, spaceAfter=7))
ST.add(ParagraphStyle(name='KickerD', fontName='CalibriB', fontSize=9, leading=12, textColor=TEAL, spaceAfter=12))
ST.add(ParagraphStyle(name='CellD', parent=ST['BodyD'], fontSize=9, leading=11.5, spaceAfter=0))
ST.add(ParagraphStyle(name='CodeD', fontName='Consolas', fontSize=9, leading=12, textColor=NAVY, backColor=PALE, borderPadding=10, spaceBefore=5, spaceAfter=13))
story=[]

def read(name): return json.loads((EVIDENCE/name).read_text(encoding='utf-8'))
small=read('benchmark_small/benchmark.json')
large=read('benchmark_large/benchmark.json')
balanced=read('benchmark_balanced/benchmark.json')
capacity=read('benchmark_capacity_margin/benchmark.json')
diag=read('theory_diagnostics.json')
cap={c:read(f'capacity_{c}.json') for c in ('bc5','rg8')}

def p(text, small=False): story.append(Paragraph(text,ST['SmallD' if small else 'BodyD']))
def h(text): story.append(Paragraph(text,ST['H2D']))
def code(text):
    text=text.replace(' '+chr(92)+chr(10),' '+chr(96)+chr(10))
    story.append(Preformatted(text,ST['CodeD']))
def page(n,title):
    if story: story.append(PageBreak())
    story.append(Paragraph(f'DAWNWOOD INTERACTIVE / {n:02d}',ST['KickerD']))
    story.append(Paragraph(title,ST['H1D']))
def table(rows,widths):
    data=[[Paragraph(str(c),ST['CellD']) for c in row] for row in rows]
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('LINEBELOW',(0,0),(-1,0),1,TEAL),
                          ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),
                          ('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),
                          ('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#D6E1E5'))]))
    story.append(t);story.append(Spacer(1,10))
def summ(data,c):return data['performance'][c]['summary']
def fmt(x,n=2):return f'{x:,.{n}f}'
def speed(data,c):return summ(data,c)['circulation_wall_ms']['reference_over_optimized_ratio_of_medians']
def profile(name):
    lines=(EVIDENCE/name).read_text().splitlines()
    i=next(i for i,line in enumerate(lines) if line.startswith('"ID"'))
    rows=list(csv.DictReader(io.StringIO('\n'.join(lines[i:]))))
    values={}
    for row in rows:
        raw=row['Metric Value']
        value=float(raw.replace('.','').replace(',','.'))
        values.setdefault(row['Metric Name'],[]).append(value)
    return {k:statistics.median(v) for k,v in values.items()}
prof={v:profile(f'ncu_{v}.csv') for v in ('reference','optimized')}

page(1,'Dawnwood<br/>Interactive')
p('<b>Optimized kernel formalization, literal-source supplement,<br/>and measured RTX 5070 Ti performance</b>')
p('Native binding v0.3, optimized edition | 16 September 2026<br/>Project author: Tom Klootwijk')
story.append(Spacer(1,12))
table([['Measured outcome','Result'],
       ['BC5 circulation, larger field',f'<b>{speed(large,"bc5"):.2f}x faster</b> / {summ(large,"bc5")["token_pair_updates_per_second"]["optimized"]["median"]/1e9:.2f} billion pair updates/s'],
       ['RG8 circulation, larger field',f'<b>{speed(large,"rg8"):.2f}x faster</b> / {summ(large,"rg8")["token_pair_updates_per_second"]["optimized"]["median"]/1e9:.2f} billion pair updates/s'],
       ['BC5 capacity exercised',f'<b>{cap["bc5"]["token_pairs"]/1e9:.3f} billion stored pairs</b> / {cap["bc5"]["payload_bytes"]/2**30:.3f} GiB payload'],
       ['Preserved behavior','Complete reference/optimized snapshots agree on all 16 small cases; graph checks and continuation checks pass.'],
       ['Theory verdict','Digital self-reference and component algebra are supported. Physical double-slit behavior is not validated.']], [178,317])
h('What this document adds')
p('The supplied 24-page <i>double-slit-theory.pdf</i> is a conversation containing design requirements, interpretations and predictions. This edition turns the executable parts into an explicit finite numerical law, traces them to source pages, and reports measurements from the actual laptop. Numerical choices are identified as implementation definitions, not equations quoted from the source.')
p('The optimized recurrence preserves the existing log-polar/Klein representation, one-bit jitter, field-directed mutation, exact B/A words and fourth-slot Y-up event. It also preserves their numerical limitations. In particular, logarithmic radius wrapping can amplify tiny cancellation residues; RG8 does not remove that effect.')
p('<b>Reading guide:</b> pages 2-4 define the source relationship and state law; page 5 formalizes the optimization; pages 6-8 explain speed, VRAM and cache metrics; pages 9-10 assess theory fidelity and correctness; pages 11-12 give reproduction and references.',small=True)

page(2,'Literal source to executable law')
p('Page numbers below refer to the supplied source PDF, not this report. Literal requirements and assistant predictions are distinguished; neither is experimental evidence.')
table([['Source pages / requirement','Executable supplement and boundary'],
['3-4 / two pinions, Hadamard hinges, log-polar LUT','Two LP8 complex streams; H(a,b)=((a+b)/sqrt(2),(a-b)/sqrt(2)). A finite chart and cell sizes are defined by this edition. No spatial slit aperture is specified.'],
['4-6 / one-bit parity, jitter, [0,2,0,1]','Packed bit operations, deterministic hash-derived jitter, quantized amplitude-two seed, zero B and phase-inverse identity. Jitter is reproducible, not quantum randomness.'],
['7 / two Y-up shifts in fourth RK slot','Fourth derivative receives epsilon=2/65536 in its y coordinate. This is an intentional forced four-stage map, not textbook RK4 for the unforced ODE.'],
['8-9 / shapes, double-dot, phase difference','Local SDF supports and real two-vector contraction. T union, triangle, cone meridian, ambient 4D sphere support and apex are explicit numerical bindings.'],
['9-12 / R,G with B history and inverse T in A','R/G are token streams. Per 16 pairs, B is a 32-bit history and A packs two 16-bit inverse phase words. A does not invert the complete recurrence.'],
['12-14 / self-referential SDF Klein surface','Klein quotient with local SDF supports; rectangular CUDA arrays are storage. No global signed distance to a Klein bottle or physical square lattice is asserted.'],
['14-16 / moving, changing operators at Psi','31 mutable records; field results alter body words, references, support, coefficients, positions and routing. The CUDA machine-code kernel itself stays fixed.'],
['16-22 / texture cache and VRAM saturation','Native BC5 textures, surface commits, a rolling whole-field sweep and capacity accounting. Cache retention is a hardware preference; allocation is not bandwidth saturation.'],
['22-23 / universality and application claims','Programmable finite state feedback exists. There is no universality proof, task reward, learned objective, database implementation or physical quantum computer.']], [178,317])
p('The detailed derivation and page map are maintained in <b>docs/THEORY_SUPPLEMENT.md</b> and <b>results/optimization/THEORY_AUDIT.md</b>. The original source PDF is unchanged.',small=True)

page(3,'State, storage and geometry')
p('Let F<sub>e</sub>=(P<sub>e</sub>, O<sub>e</sub>, B<sub>e</sub>, A<sub>e</sub>, e, c<sub>e</sub>, seed). P is the stored two-stream field, O is the mutable operator catalogue, e is the Psi interval and c is the rolling block cursor. There are N physical 4x4 blocks; W=min(requested window,N).')
code('i(t) = (c_e + t) mod N,     0 <= t < W\nS_t  = E(P_e, O_e, B_e, A_e, i(t), e, seed)\nP, B, A <- commit all S_t to unique owned blocks\nO_(e+1) = M(O_e, S, e, seed)\nc_(e+1) = (c_e + W) mod N;  e <- e + 1')
p('Evaluation reads the last committed field. A separate kernel commits the staged window; mutation reads the old operator bank and staged results; an ordered final kernel advances the clock. This prevents same-kernel surface-write/texture-read coherence assumptions. Four kernels are replayed as a CUDA Graph. [R2]')
table([['Representation','Bytes / role'],['Operator record','64 bytes; 31 records per bank, two alternating banks. Eight 32-bit instruction words per body.'],['BC5 block','16 bytes for 16 R/G token pairs, plus 8 bytes exact B/A: 1.5 bytes per pair.'],['RG8 block','32 bytes for 16 R/G token pairs, plus 8 bytes B/A: 2.5 bytes per pair.'],['Staging','64 bytes per active block; 4 MiB at W=65,536. No second full-size field.'],['Hot data','6,080 bytes shared per CTA; optimized immutable pair table adds 1 MiB in device memory.']], [160,335])
h('LP8 decode and the Klein quotient')
code('h = q >> 4; p = q & 15\nu = (h - 0.5)/15; v = (p + 0.5)/16  [h > 0]\nz(q) = 2^(-4 + 7.5*u) * exp(i*2*pi*v)\nh == 0 denotes exact zero amplitude\n(u+1, v) ~ (u, -v);    (u, v+1) ~ (u, v)')
p('Encoding a nonzero z uses u=(0.5 log2(|z|²)+4)/7.5 and v=arg(z)/(2pi), folds the quotient, then selects a containing cell. Exact zero returns token 0 before offsets. Radial wrapping identifies magnitudes differing by 2^7.5, approximately 181.02. This is a computational quotient, not a physical amplitude scale.')
code('tau=2*pi; r(v)=2+0.5*cos(tau*v)\nK(u,v)=(r(v)*cos(tau*u), r(v)*sin(tau*u),\n        0.5*sin(tau*v)*cos(pi*u),\n        0.5*sin(tau*v)*sin(pi*u))\nK(u+1,-v)=K(u,v)')

page(4,'The complete interval')
h('Selection, body execution and forced chart motion')
p('The payload chooses two page-chain directions by default. A depth-four implicit binary decision tree chooses a leaf from operators 15-30 using SDF sign, jitter, history and routing parity. The leaf executes its two referenced bodies, then its own body, on eight 16-bit registers. Arithmetic overflow is modular. Operator reference 31 aliases record 0.')
code('f(u,v) = (drive_u + k*sin(2*pi*v),\n          drive_v + k*cos(2*pi*u))\na=f(q); b=f(q+dt*a/2); c=f(q+dt*b/2)\nd=f(q+dt*c+(0,2/65536))\nq_next=q+dt*(a+2*b+2*c+d)/6')
p('The drive and coupling k come from the executed register words and operator coefficient. The phase offset also includes the wrapped second difference of the sampled neighbour phases. The fixed fourth-stage event is retained from source page 7. As dt approaches zero, the effective derivative tends to (5 f(q)+f(q+(0,epsilon)))/6, not exactly f(q).')
h('Double pinion and exact auxiliary words')
code('z_plus  = (z_R + z_G)/sqrt(2)\nz_minus = (z_R - z_G)/sqrt(2)\ntwist = dt*(Re(z_R)*Re(z_G) + Im(z_R)*Im(z_G))\nR_next = C(z_plus,  du, qa+twist) XOR jitter\nG_next = C(z_minus,-du, qb-twist) XOR jitter')
p('C is the LP8 quotient encoder with chart offsets. qa and qb are quantized phase rotations including inverse-T feedback. A stores their modular additive inverses: p+(-p)=0 mod 65,536. B rolls its previous history together with jitter, return parity, output parity and a mixed epoch word. A excludes Hadamard mixing, twist, codec loss, radial drift and the rest of the update.')
h('Self-reference has an executable meaning')
p('Each operator selects a staged sample using its old location, history, index and epoch. A hash of field feedback and prior operator state selects a body-word bit; jitter controls its flip. Related bits change links, support and coefficients. Positions move by the defined chart law. The next interval executes those altered bodies. This is field-dependent program-data mutation, with no fitness objective or proof that changes improve a task.')
p('Work per interval is proportional to W(H+D+3L+16C<sub>codec</sub>)+31, with D=4 and L=8. A complete field sweep is at least linear in N. Changing W changes the mutation schedule and therefore the model, so every fair speed comparison fixes W.',small=True)

page(5,'Optimization without a new law')
h('Memoize finite token-pair mathematics')
code('P[r+256*g] = (U(z_plus), V(z_plus),\n              U(z_minus),V(z_minus))\nU(z)=(0.5*log2(|z|^2)+4)/7.5\nV(z)=atan2(Im(z),Re(z))/(2*pi)\nP: 65,536 entries * 16 bytes = 1,048,576 bytes')
p('The table is built once on the GPU from the same uploaded 256-entry LP8 LUT. Zero branches retain an explicit sentinel. At runtime the original evolving offsets and dot product are applied in the same operation order. Sixteen V4 reads replace up to 64 log2/atan2 evaluations per 16-pair block. No evolving operator or phase is frozen. Fused multiply-add stays disabled in both builds.')
table([['Change','Why it is safe / measured cost'],['Exact BC5 selector search','Monotone midpoint comparisons preserve the original lowest-index tie rule. Absolute reconstruction error is accumulated while encoding.'],['Bounded VM arithmetic','Only operations whose ranges fit are narrowed; final 16-bit modular results are unchanged.'],['Address calculation','One conditional subtraction replaces window modulo under c&lt;N and W&lt;=N. Power-of-two page sides use shifts/masks; other sides retain division.'],['Commit error reduction','Warp shuffles and four shared partial sums replace the 128-entry reduction. Partial windows keep all CTA lanes participating.'],['Balanced cache preference','Prevents excessive L1 preference from starving shared-memory residency on this device. Estimated resident CTAs/SM: 1 to 8. This remains a driver preference.'],['Resource and evidence reporting','Reports parameters, kernel variant, cache preference, staging/table bytes, registers and estimated occupancy. Reference binary remains available.']], [160,335])
p('The compiler reports 100 to 61 registers per evolve thread. Shared hot data remains 6,080 bytes. Local stack rises from 192 bytes in the original build to 208 bytes in the updated builds; reported spill stores/loads are zero. Stack allocation and compiler spills are different measurements.')
p('The default comparison includes both kernel changes and the cache policy change. With both binaries explicitly set to balanced, the measured gains are <b>'+fmt(speed(balanced,'bc5'))+'x BC5</b> and <b>'+fmt(speed(balanced,'rg8'))+'x RG8</b>. These isolate the implementation changes more closely. [R3]',small=True)

page(6,'Performance, in plain language')
p('Think of a token pair as one two-color item. Updates per second tells you how many items the machine revises; it does not count independent simulated universes, floating-point operations, frames, or newly stored items.')
rows=[['Workload / codec','Reference ms','Optimized ms','Speedup']]
for name,data in [('2 x 1024²',small),('32 x 2048²',large),('Both balanced',balanced)]:
    for c in ('bc5','rg8'):
        s=summ(data,c)['circulation_wall_ms']
        rows.append([f'{name} / {c.upper()}',fmt(s['reference']['median']),fmt(s['optimized']['median']),fmt(s['reference_over_optimized_ratio_of_medians'])+'x'])
table(rows,[189,102,102,102])
p('Each row is the median of five timed runs with alternating build order and excluded process warmups. Small-field runs use 1,024 intervals; the other rows use 2,048. All use W=65,536, batch=32, seed=756, dt=1/64, two hops, jitter and mutation enabled. BC5 and RG8 are different recurrences because BC5 is lossy; compare builds within a codec.')
h('Billion pair updates per second: larger field')
d=Drawing(495,150)
for i,(c,v,label) in enumerate([('bc5','reference','BC5 original policy'),('bc5','optimized','BC5 optimized'),('rg8','reference','RG8 original policy'),('rg8','optimized','RG8 optimized')]):
    rate=summ(large,c)['token_pair_updates_per_second'][v]['median']/1e9
    y=117-i*33
    d.add(String(0,y+5,label,fontName='Calibri',fontSize=10,fillColor=NAVY))
    d.add(Rect(155,y,rate*30,20,fillColor=TEAL if v=='optimized' else GRAY,strokeColor=None))
    d.add(String(162+rate*30,y+5,fmt(rate),fontName='CalibriB',fontSize=10,fillColor=NAVY))
story.append(d)
h('What the stopwatch includes')
p('Circulation wall time and CUDA-event time include launch gaps and batch synchronization. They exclude context creation, allocation, initialization, report output and snapshots. Full process speedups on the larger field are '+fmt(summ(large,'bc5')['process_wall_ms']['reference_over_optimized_ratio_of_medians'])+'x BC5 and '+fmt(summ(large,'rg8')['process_wall_ms']['reference_over_optimized_ratio_of_medians'])+'x RG8; those smaller numbers reflect startup costs.')
for c in ('bc5','rg8'):
    s=summ(large,c)['circulation_wall_ms']['optimized']
    p(f'{c.upper()} optimized larger-field variation: median {fmt(s["median"])} ms; range {fmt(s["min"])}-{fmt(s["max"])} ms; median absolute deviation {fmt(s["median_absolute_deviation"],3)} ms.',small=True)
p('The laptop ran under Windows WDDM, without externally fixed clocks or power limits. These are measured workloads on this machine, not a universal speed guarantee or a statistical significance claim.',small=True)

page(7,'VRAM capacity and sweep rate')
p('VRAM is the large shelf; cache is the small nearby workbench. Filling the shelf is a storage result. A full sweep means every stored block has been revisited. A token may be updated several times in one run.')
rows=[['Measured capacity','BC5','RG8']]
for label,key,fn in [('4096² pages','pages',lambda v:str(v)),('Payload GiB','payload_bytes',lambda v:fmt(v/2**30,3)),('Stored pairs, billions','token_pairs',lambda v:fmt(v/1e9,3)),('Free after packing, MiB','free_after_packing',lambda v:fmt(v/2**20,1)),('Payload / total device','payload_fraction_of_total_device',lambda v:fmt(v*100,2)+'%')]:
    rows.append([label,fn(cap['bc5'][key]),fn(cap['rg8'][key])])
rows.append(['Payload / initially free',*(fmt(cap[c]['payload_bytes']/cap[c]['free_at_payload_planning']*100,2)+'%' for c in ('bc5','rg8'))])
rows.append(['Margin-run payload GiB',*(fmt(capacity['performance'][c]['pairs'][0]['optimized']['report']['payload_bytes']/2**30,3) for c in ('bc5','rg8'))])
rows.append(['Repeated margin-run speedup',*(fmt(speed(capacity,c))+'x' for c in ('bc5','rg8'))])
rows.append(['Optimized billion updates/s',*(fmt(summ(capacity,c)['token_pair_updates_per_second']['optimized']['median']/1e9) for c in ('bc5','rg8'))])
table(rows,[229,133,133])
p('The maximum-allocation run used fill=0.98 and reserve=256 MiB. A later repetition at that maximum failed during allocation. Three successful alternating trials therefore used 75% of the observed page counts: 336 BC5 / 201 RG8 pages, each for 8,192 intervals. The last three rows describe this margin workload. Full snapshots were not exported at these sizes.')
code('payload bytes/pair = 1.5 (BC5) or 2.5 (RG8)\nupdates/s = 16 * visited_blocks / circulation_seconds\nmean interval time = circulation_seconds / intervals\nequivalent sweep time = stored_pairs / updates_per_second\nVRAM budget = min(free*fill, free-reserve)')
for c in ('bc5','rg8'):
    s=summ(capacity,c)
    wall=s['circulation_wall_ms']['optimized']['median']/1000
    rate=s['token_pair_updates_per_second']['optimized']['median']
    pairs=capacity['performance'][c]['pairs'][0]['optimized']['report']['token_pairs']
    p(f'<b>{c.upper()} margin workload:</b> {rate/1e9:.2f} billion item revisions/s; {wall/8192*1e6:.1f} microseconds per interval; {pairs/rate:.3f} seconds per equivalent sweep at the average rate. Sweep time is derived. Every trial covered the full field and matched final operator digest and codec-error total across builds.',small=True)
p('BC5 uses 40% fewer payload bytes than RG8, including B/A, and has additional lossy encoding. For this capacity workload its software mean absolute error is '+fmt(cap['bc5']['software_codec_mean_absolute_token_error'],3)+' token-byte units; RG8 is zero in that byte metric. Neither says how accurate real amplitudes or angles are. Allocator counts establish allocation, not guaranteed physical residency of every page at every moment.',small=True)

page(8,'What the hardware counters say')
p('Nsight Compute 2025.1 sampled three evolve-kernel invocations after eight earlier evolve launches: 32 pages of 2048², W=65,536, BC5, sequential kernel launches. The table reports the median per-invocation counter values. This is a 192 MiB field, not the near-capacity experiment.')
rows=[['Counter / meaning','Reference','Optimized']]
spec=[('Evolve duration (microseconds)','gpu__time_duration.sum',.001),('Active-warp occupancy (%)','sm__warps_active.avg.pct_of_peak_sustained_active',1),('L1/TEX sector hit rate (%)','l1tex__t_sector_hit_rate.pct',1),('L2 sector hit rate (%)','lts__t_sector_hit_rate.pct',1),('L1/TEX throughput / peak (%)','l1tex__throughput.avg.pct_of_peak_sustained_elapsed',1),('DRAM throughput / peak (%)','dram__throughput.avg.pct_of_peak_sustained_elapsed',1)]
for label,key,scale in spec:rows.append([label,fmt(prof['reference'][key]*scale),fmt(prof['optimized'][key]*scale)])
table(rows,[285,105,105])
h('More hits is not always faster')
p('The optimized kernel has a lower L1/TEX sector hit percentage while finishing substantially sooner. Balanced shared-memory capacity admits more concurrent work, and the pair table trades repeated transcendental math for reads. Cache-hit percentage alone would therefore rank these builds incorrectly.')
h('Three different uses of the word saturation')
table([['Quantity','What the evidence supports'],['Storage occupancy','Roughly 97.6% of the memory free at payload planning was used for payload in the capacity runs.'],['Cache effectiveness','Sector-hit counters above are measured for the profiled kernels. The configured L2 hitRatio=1 is only a retention preference.'],['Bandwidth saturation','The sampled optimized DRAM and L1/TEX throughput are below 100% of profiler sustained peak. Full bandwidth saturation is not demonstrated.']], [155,340])
p('Cache flushing and clock control were disabled to avoid claiming cold-cache timings as normal recurrence behavior. Nsight warns that uncontrolled caches and clocks can affect consistency; replay and instrumentation also perturb execution. These counters diagnose the observed bottleneck, while unprofiled repeated timings are the main speed evidence. They do not measure end-to-end PCIe traffic. [R2-R4]')
p('The selected L2 persistence window covers the 1,056,768-byte hot arena, including the pair table. The device reports 36 MiB L2 and a 22.5 MiB maximum persisting allowance. Persistence, shared-memory carveout and cached texture access are policies and mechanisms, not permanent cache locks.',small=True)

page(9,'Does it behave like double-slit theory?')
p('<b>It implements identifiable source mechanisms. It does not validate a physical double-slit model.</b> The following diagnostics separate algebraic correctness from the behavior of the encoded recurrence. They run on the native CPU header, plus an explicit double-precision ODE diagnostic. [R1, R5]')
h('An isolated interference comparison')
code('a=1, b=exp(i*phi)\nI_plus = |(a+b)/sqrt(2)|^2 = 1+cos(phi)\nI_minus= |(a-b)/sqrt(2)|^2 = 1-cos(phi)\nI_plus + I_minus = 2')
p('This is the coherent two-input Hadamard identity before quotient encoding. It is a useful component check, not a spatial slit-and-detector experiment. A detector model would also need normalized probabilities, geometry, propagation, wavelength/path phases and comparison with independent observations.')
table([['Executed diagnostic','Observed result'],['Float Hadamard, all 65,280 nonzero LUT pairs','Maximum relative norm residual: 1.67e-7 before encoding.'],['Same split followed by LP8','53,440 pairs change energy by more than 1e-4 relative; output/input energy ratios span 3.05e-5 to 32,768.00365.'],['Opposite-phase cancellation','240/240 directed opposite-phase pairs encode a nonzero sum. Largest raw cancellation amplitude is 1.22e-6; largest decoded sum is 9.51366 (different maxima).'],['Concrete quotient witness','Input tokens [17,0] produce [254,254] after the encoded split. Tiny nonzero amplitudes can wrap to a large radius.'],['Source amplitude 2','Encodes as token 176: magnitude 2.37841, phase 11.25 degrees; complex absolute error 0.570964.'],['Klein seam and inverse words','Maximum sampled seam residual 4.01e-6; zero failures across all 65,536 modular phase inverses.'],['Fourth-stage forcing','At 256 steps over T=1: classical double RK4 error 1.29e-12; forced map error 2.22e-6 against the unforced reference.']], [187,308])
p('These measurements explain why exact RG8 storage is not an exact wave simulation: LP8 quantization and radius identification already change the physical interpretation. No epsilon cutoff, renormalization or removal of the fourth-stage event was inserted to conceal this. Such changes would define a different binding.')

page(10,'Validation and practical limits')
table([['Evidence','Result and scope'],['Native CUDA self-test','BC5 hardware texture decode, exact RG8 readback, CPU/GPU instruction cases, one-step recurrence, ordered write/read coherence and executable-word mutation pass.'],['Pair cache on this GPU','All 65,536 token-pair entries at four offsets and two channels match the uncached device calculation.'],['Core equivalence','8,355,840 BC4 endpoint/sample selector cases; 10,000 BC5 block/error comparisons; all 65,536 LP8 pairs at four offsets; 1,024 complete staged comparisons pass.'],['Full snapshot equivalence','16 small cases across both codecs: partial windows and CTAs, page/cursor wrapping, whole field, one block, frozen operators, no jitter, inverse gain zero and zero hops.'],['Graphs and continuation','Both builds checked against sequential full snapshots. Acceptance suite checks repeatability and 7+13 versus 20-interval full snapshot continuation in both codecs.'],['Memory and synchronization','Compute Sanitizer memcheck, racecheck and synccheck: zero errors/hazards for both codecs on three 48² pages, a 257-block partial window and five intervals.'],['Repeated measurements','Five paired trials for small, larger and common-cache workloads; three paired multi-GiB trials with capacity margin. The failed maximum-capacity repetition is retained.']], [165,330])
h('Boundaries of the result')
p('Full-snapshot comparisons validate the tested digital states; they are not a proof over every possible custom operator image, seed, device or compiler. Floating math can differ on other hardware. The original BC5 build could not create its texture; the reference measurements use the minimal read-mode compatibility fix required to execute it.')
p('The source claim of 24-48 billion stored states is not supported by this format. Even an ideal 12 GiB entirely devoted to payload holds at most 8.590 billion BC5+B/A pairs or 5.154 billion RG8+B/A pairs. Actual usable memory is lower. Updating a fixed-size window is not an O(1) update of the full VRAM field.')
p('Self-mutation demonstrates feedback, not automatic improvement. There is no defined reward function, convergence proof, quantum randomness, guaranteed avoidance of cycles, unrestricted universality proof, or measured zero-PCIe claim. The useful validated artifact is an efficient, editable classical finite-state kernel with a documented source relationship.')

page(11,'Reproduce and extend')
p('Project directory: <b>Dawnwood_Interactive_RTX5070Ti_v0.3 / Dawnwood_Interactive_RTX5070Ti_v0.3</b>. The originally supplied path with separate underscore directories did not exist; this matching package is the edited project. Use a fresh output folder for each harness run.')
h('Build and validate')
code('.\\scripts\\build_windows.ps1\n.\\build\\dawnwood.exe --self-test\npython tools\\gpu_acceptance.py build\\dawnwood.exe \\\n  --out work\\acceptance_new\npython -m unittest discover -s tests -p "test_*.py" -v')
p('A Ninja Release build places executables directly in build; a Visual Studio generator places them in build/Release. The script preserves an existing generator. Tested toolchain: MSVC 19.44, nvcc 12.8.61, sm_120 plus compute_120 PTX, driver 591.59, CUDA driver API 13.1, RTX 5070 Ti Laptop GPU (46 SMs).')
h('Compare and isolate cache policy')
code('python tools\\benchmark_optimization.py \\\n  build\\dawnwood_reference.exe build\\dawnwood.exe \\\n  --out work\\compare_new --pages 32 --page-side 2048 \\\n  --steps 2048\n# Add these to isolate kernel changes at the same preference:\n  --reference-cache-policy balanced \\\n  --optimized-cache-policy balanced')
h('Bounded saturation run')
code('.\\build\\dawnwood.exe --codec bc5 --fill 0.98 \\\n  --reserve-mib 256 --page-side 4096 \\\n  --blocks-per-step 65536 --steps 8192 --batch 32 \\\n  --report work\\capacity.json')
p('Commands use PowerShell backtick continuation. If local policy requires signed scripts, run the build through powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\build_windows.ps1; this applies only to that process. Finite --steps is intentional; --steps 0 runs until Ctrl+C. Changing W changes the recurrence.')
p('Editable operator definitions remain in model/operators.json and can be packed with tools/operator_image.py. Snapshot ABI and operator record sizes remain v0.3. The reference binary and cache switches make future comparisons reviewable. The report builder reads saved JSON evidence; it does not substitute theoretical peak specifications for measurements.',small=True)

page(12,'Evidence index and references')
h('Files that make the conclusions reviewable')
table([['Project-relative evidence','Purpose'],['results/optimization/benchmark_{small,large,balanced}/benchmark.json','Commands, hardware record, executable hashes, full-state checks and five-trial timing statistics.'],['results/optimization/benchmark_capacity_margin/benchmark.json','Three paired multi-GiB trials; complete sweep assertion. Original benchmark_capacity records the failed maximum repeat.'],['results/optimization/capacity_{bc5,rg8}.json','Automatic allocation, exact payload/free bytes and initial capacity-run metrics.'],['results/optimization/ncu_{reference,optimized}.csv','Three sampled evolve invocations; locale-aware numeric parsing in this PDF builder.'],['results/optimization/sanitizer_*.txt','Native memory, race and synchronization diagnostics.'],['results/optimization/theory_diagnostics.json','Independent numerical findings; generated from tools/theory_diagnostics.cpp.'],['docs/THEORY_SUPPLEMENT.md','Full literal-source map and mathematical supplement.'],['docs/OPTIMIZATION.md','Changes, reproduction and measurement interpretation.']], [265,230])
h('Primary sources')
refs=[
('R1','Supplied double-slit-theory.pdf, 24 pages. SHA-256: e3cf7d49e6a4942c7ccad4805f6a2a07e1c817753ff8d384b1f2e37791ebbe27. Original source preserved.'),
('R2','NVIDIA CUDA 12.8 Programming Guide: texture/surface coherence and L2 policies. <link href="https://docs.nvidia.com/cuda/archive/12.8.0/cuda-c-programming-guide/index.html" color="#087F8C">Official programming guide</link>.'),
('R3','NVIDIA CUDA 12.8 Runtime API: texture views, cache preference and occupancy queries. <link href="https://docs.nvidia.com/cuda/archive/12.8.0/cuda-runtime-api/group__CUDART__TEXTURE__OBJECT.html" color="#087F8C">Texture objects</link>; <link href="https://docs.nvidia.com/cuda/archive/12.8.0/cuda-runtime-api/group__CUDART__EXECUTION.html" color="#087F8C">Execution control</link>.'),
('R4','NVIDIA Nsight Compute Profiling Guide: replay, cache flushing, clocks and metric interpretation. <link href="https://docs.nvidia.com/nsight-compute/ProfilingGuide/" color="#087F8C">Official profiling guide</link>.'),
('R5','Feynman Lectures on Physics, volume III, chapter 1: amplitudes, interference and detection probability. <link href="https://www.feynmanlectures.caltech.edu/III_01.html" color="#087F8C">Quantum behavior</link>.'),
('R6','Microsoft Direct3D 11 block-compression documentation: BC5 stores two channels in 16 bytes per 4x4 block. <link href="https://learn.microsoft.com/en-us/windows/win32/direct3d11/texture-block-compression-in-direct3d-11" color="#087F8C">Block compression</link>.')]
for label,text in refs:p(f'<b>[{label}]</b> {text}',small=True)
p('Measurements are dated 16 September 2026. Source mathematics, implementation definitions, CPU diagnostics, GPU correctness checks, allocator observations and profiler samples are separate evidence classes throughout this report.',small=True)

def footer(c,doc):
    c.saveState(); w,h=doc.pagesize
    c.setStrokeColor(TEAL);c.setLineWidth(.7);c.line(50,42,w-50,42)
    c.setFont('Calibri',8);c.setFillColor(GRAY)
    c.drawString(50,28,'Dawnwood Interactive | optimized native binding v0.3 | 16 Sep 2026')
    c.drawRightString(w-50,28,str(doc.page));c.restoreState()

doc=SimpleDocTemplate(str(OUT),pagesize=(595.276,841.89),rightMargin=50,leftMargin=50,topMargin=43,bottomMargin=57,
                      title='Dawnwood Interactive - Optimized Kernel Formalization',author='Tom Klootwijk',subject='Literal-source supplement and measured CUDA performance')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(OUT)
