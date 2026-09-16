"""Build the integer-1 formalization from this edition's saved evidence only.

The final GPU summary is optional during report preparation. If absent, GPU
measurements remain visibly pending; previous floating-edition timings are never
substituted. The authoring-operation marker is run by the coordinating agent.
"""
from pathlib import Path
import json
import math
from xml.sax.saxutils import escape

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Line, PolyLine, Circle, String, Rect

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / 'results/integer'
OUT = ROOT / 'output/pdf/Dawnwood_Interactive_Integer_Formalization.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)

def read(path, default=None):
    path = Path(path)
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else default

DIAG = read(EV / 'theory_diagnostics.json', {})
QUANTUM = read(EV / 'quantum_mechanism_checks.json', {})
MODEL = read(ROOT / 'model/integer_binding.json', {})
SUMMARY = read(EV / 'final_summary.json', {})
BENCH = read(ROOT / SUMMARY['performance_evidence'], {}) if SUMMARY.get('performance_evidence') else {}
PERF = SUMMARY.get('performance', [])
PERF = PERF if isinstance(PERF, list) else PERF.get('rows', [])
CAPACITY = SUMMARY.get('capacity', [])
CAPACITY = CAPACITY if isinstance(CAPACITY, list) else CAPACITY.get('rows', [])
VALIDATION = SUMMARY.get('validation', {})
AUDITS = SUMMARY.get('instruction_audits', {})
PROFILES = SUMMARY.get('profiles', {})

for name, filename in [('DI', 'calibri.ttf'), ('DIB', 'calibrib.ttf'), ('DII', 'calibrii.ttf'), ('DIM', 'consola.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(Path('C:/Windows/Fonts') / filename)))
pdfmetrics.registerFontFamily('DI', normal='DI', bold='DIB', italic='DII', boldItalic='DIB')
NAVY = colors.HexColor('#183343')
TEAL = colors.HexColor('#057A88')
MUTED = colors.HexColor('#526672')
PALE = colors.HexColor('#EDF4F6')
ORANGE = colors.HexColor('#B75324')
PURPLE = colors.HexColor('#725591')
RULE = colors.HexColor('#D3E0E5')
ST = getSampleStyleSheet()
ST.add(ParagraphStyle('BodyI', fontName='DI', fontSize=10.2, leading=13.6, textColor=NAVY, spaceAfter=7.4))
ST.add(ParagraphStyle('SmallI', parent=ST['BodyI'], fontSize=8.8, leading=11.4, spaceAfter=5.3))
ST.add(ParagraphStyle('TitleI', fontName='DIB', fontSize=23, leading=27, textColor=NAVY, spaceAfter=13))
ST.add(ParagraphStyle('HeadI', fontName='DIB', fontSize=12.5, leading=16, textColor=TEAL, spaceBefore=7, spaceAfter=6))
ST.add(ParagraphStyle('KickerI', fontName='DIB', fontSize=8.8, leading=11.5, textColor=TEAL, spaceAfter=10))
ST.add(ParagraphStyle('CellI', parent=ST['BodyI'], fontSize=8.8, leading=11.2, spaceAfter=0))
ST.add(ParagraphStyle('TinyCellI', parent=ST['CellI'], fontSize=8.0, leading=10.0))
ST.add(ParagraphStyle('CodeI', fontName='DIM', fontSize=8.5, leading=11.2, textColor=NAVY, backColor=PALE,
                     borderPadding=8, spaceBefore=4, spaceAfter=10))
story = []

def p(text, small=False):
    story.append(Paragraph(text, ST['SmallI' if small else 'BodyI']))

def h(text):
    story.append(Paragraph(text, ST['HeadI']))

def page(n, title):
    if story:
        story.append(PageBreak())
    story.append(Paragraph(f'DAWNWOOD INTERACTIVE / INTEGER-1 / {n:02d}', ST['KickerI']))
    story.append(Paragraph(title, ST['TitleI']))

def code(text):
    story.append(Preformatted(text, ST['CodeI']))

def table(rows, widths, tiny=False, padding=6):
    style = ST['TinyCellI' if tiny else 'CellI']
    cells = [[Paragraph(str(cell), style) for cell in row] for row in rows]
    item = Table(cells, colWidths=widths, repeatRows=1, hAlign='LEFT')
    item.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PALE),
        ('LINEBELOW', (0, 0), (-1, 0), .9, TEAL),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), padding), ('BOTTOMPADDING', (0, 0), (-1, -1), padding),
        ('LINEBELOW', (0, 1), (-1, -1), .3, RULE),
    ]))
    story.append(item)
    story.append(Spacer(1, 7))

def number(value, places=2, fallback='pending'):
    return f'{float(value):,.{places}f}' if isinstance(value, (int, float)) else fallback

def label(text):
    return str(text).replace('_', ' ')

def value_summary(value):
    if isinstance(value, dict):
        favored = ['status', 'passed', 'failures', 'violation_count', 'cases', 'assertions', 'scope', 'note', 'path']
        keys = [key for key in favored if key in value]
        keys += [key for key in value if key not in keys]
        return '; '.join(f'{label(key)}: {value_summary(value[key])}' for key in keys[:5])
    if isinstance(value, list):
        return '; '.join(value_summary(item) for item in value[:4]) + (f'; {len(value)} entries total' if len(value) > 4 else '')
    return str(value)

def evidence_rows(obj, limit=8):
    if isinstance(obj, list):
        values = [(row.get('variant', row.get('name', f'entry {i+1}')), row) if isinstance(row, dict) else (f'entry {i+1}', row)
                  for i, row in enumerate(obj)]
    elif isinstance(obj, dict):
        values = list(obj.items())
    else:
        values = [('result', obj)] if obj else []
    rows = [[escape(label(key)), escape(value_summary(value))] for key, value in values[:limit]]
    if len(values) > limit:
        rows.append(['Additional saved entries', f'{len(values)-limit} more entries are retained in final_summary.json.'])
    return rows

def phase_plot():
    points = DIAG.get('phase_sweep', {}).get('points', [])
    if not points:
        return Paragraph('Phase-sweep data are pending.', ST['BodyI'])
    d = Drawing(495, 306)
    x0, width, plot_h = 42, 430, 103
    ymax = max(1.5, max(max(row['encoded_plus'], row['encoded_minus']) for row in points) * 1.06)
    def panel(y0, title, encoded):
        d.add(String(x0, y0 + plot_h + 12, title, fontName='DIB', fontSize=9.5, fillColor=NAVY))
        for y in [0, .5, 1.0, 1.5]:
            yy = y0 + y / ymax * plot_h
            d.add(Line(x0, yy, x0 + width, yy, strokeColor=RULE, strokeWidth=.45))
            d.add(String(x0-8, yy-3, f'{y:.1f}', fontName='DI', fontSize=8, textAnchor='end', fillColor=MUTED))
        for phase, tick in [(0, '0'), (.25, '1/4'), (.5, '1/2'), (.75, '3/4')]:
            xx = x0 + phase / (15/16) * width
            d.add(Line(xx, y0, xx, y0+plot_h, strokeColor=RULE, strokeWidth=.4))
            d.add(String(xx, y0-13, tick, fontName='DI', fontSize=8, textAnchor='middle', fillColor=MUTED))
        d.add(String(x0+width, y0-13, '15/16', fontName='DI', fontSize=8, textAnchor='end', fillColor=MUTED))
        for side, color in [('plus', TEAL if not encoded else ORANGE), ('minus', PURPLE)]:
            ideal = []
            measured = []
            for row in points:
                xx = x0 + row['phase_turns'] / (15/16) * width
                ideal.extend([xx, y0 + row[f'nominal_ideal_{side}']/ymax*plot_h])
                yy = y0 + row[f'{"encoded" if encoded else "integer"}_{side}']/ymax*plot_h
                measured.extend([xx, yy])
                d.add(Circle(xx, yy, 2.1, fillColor=color, strokeColor=color, strokeWidth=.3))
            d.add(PolyLine(ideal, strokeColor=colors.HexColor('#A6B6BE'), strokeWidth=1, strokeDashArray=[3, 2]))
            d.add(PolyLine(measured, strokeColor=color, strokeWidth=1.4))
        d.add(Line(x0, y0, x0+width, y0, strokeColor=NAVY, strokeWidth=.8))
        d.add(String(x0+width-115, y0+plot_h+12, '+ port', fontName='DI', fontSize=8, fillColor=TEAL if not encoded else ORANGE))
        d.add(String(x0+width-68, y0+plot_h+12, '- port', fontName='DI', fontSize=8, fillColor=PURPLE))
    panel(179, 'Integer Hadamard before LP8 re-encoding', False)
    panel(31, 'The same outputs after LP8 re-encoding', True)
    d.add(String(253, 0, 'Relative phase in turns; dashed gray curves: nominal equal-radius identity', fontName='DI', fontSize=8, textAnchor='middle', fillColor=MUTED))
    return d

page(1, 'Dawnwood<br/>Interactive')
p('<b>The complete integer kernel</b><br/>Literal-source formalization, numerical evidence and ELI5 performance metrics')
p('Model <b>integer-1</b> | report version 0.4 | snapshot version 4<br/>16 September 2026 | Project author: Tom Klootwijk')
story.append(Spacer(1, 10))
rows = [['Delivered definition / measured evidence', 'Result and scope'],
        ['Quantum-style mechanisms', 'Actual integer two-path Hadamard interference and H followed by H are probed. Raw H-squared minimum normalized fidelity is 0.999985; LP8 between gates materially changes this result.'],
        ['Whole recurrence', 'Integer geometry, chart motion, phase calculus, Hadamard, encoding, feedback and code-word mutation. The native sampler has an explicit typed-interface boundary.'],
        ['Compact active hot data', '<b>4,004 bytes</b>: operator words, small log-polar/trigonometric LUT and live routing masks. This excludes machine code, driver resources and staging.'],
        ['Exact cancellation and seams', 'All 256 symbolic antipodes cancel exactly; 36,864 integer Klein seam cases have zero mismatches. These are component diagnostics.']]
if PERF:
    best = max(PERF, key=lambda row: row.get('median_pair_updates_per_second', 0) or 0)
    rows.append(['Saved throughput example', f'{escape(str(best.get("variant", "variant")))} / {escape(str(best.get("codec", "codec")))}: <b>{number(best.get("median_pair_updates_per_second", 0)/1e6, 2)} million pair updates/s</b>. Workload and comparison scope appear on page 10.'])
else:
    rows.append(['GPU performance and acceptance', '<b>Pending final evidence summary.</b> This preparation copy does not borrow timings from the earlier floating edition.'])
rows.append(['Physical interpretation', 'A source-inspired classical digital automaton. LP8 radius wrapping remains nonunitary; physical double-slit behavior is not claimed.'])
table(rows, [172, 323])
h('What changed from the earlier edition')
p('This edition implements the complete numerical circulation with integer words. Signed SDF calculations are part of it; they are not the entire change. Exact symmetric LUT construction removes floating cancellation residue. The fourth-slot two-unit Y event, moving operators, B/A state and self-reference remain explicit parts of the law.')
p('The optional 64 KiB D4 pair cache reuses exact finite integer results. The measured cached variant is the recommended executable; the 4004-byte compact variants remain available for comparison. Full snapshot checks precede interpretation of the speed ratios.', small=True)
p('Source definitions, chosen numerical bindings, CPU component diagnostics, GPU state checks, instruction audits and hardware performance are separate evidence classes throughout this report.', small=True)

page(2, 'The literal document, component by component')
p('Page references below refer to the supplied 24-page double-slit-theory.pdf. The original user requirements are distinguished from the other assistant\'s interpretations and unsupported predictions.')
table([
 ['Source / requirement', 'Integer realization and explicit boundary'],
 ['3-4 / two pinions, Hadamard, log-polar LUT', 'Two complete complex token streams. Q11 integer sum/difference with 23170/32768 scaling and specified rounding.'],
 ['4-6 / parity, one-bit jitter, [0,2,0,1]', 'Packed population parity and deterministic one-bit jitter. First-block tokens R=0, G=176; B=0 and A=0 encode history and inverse identity.'],
 ['7 / two Y-up events in fourth RK slot', 'A +2 Q16 phase-unit event enters only the fourth derivative argument. Integer rounding is defined at each stage.'],
 ['8-9 / shapes, double-dot, phase difference', 'Signed Q18 circle, T, triangle, cone-meridian, ambient sphere and apex supports; Q22 dot product; wrapped second phase difference.'],
 ['8-9 / Fibonacci phyllotaxis and blend', 'Integer log-radius placement, Q16 golden-angle step 25032, and executable fixed-word blend instructions. No unmeasured uniform-area claim.'],
 ['9-12 / dichromatic RG, B, inverse T in A', 'R and G each encode a full stream. Exact per-block B/A words. A inverts two modular phase words, not the whole lossy update.'],
 ['12-14 / SDF Klein surface, no raster grid', 'Integer quotient coordinates and a four-coordinate K realization attach moving signed supports to the surface. Arrays supply storage, not geometry.'],
 ['14-16 / operators themselves change at Psi', 'Field feedback rewrites body words, links, support, coefficients, placement and routing. The next interval consumes the changed data.'],
 ['18 / small cached substrate, resident packed field', '1540-byte math LUT plus 1984-byte operator bank and 480-byte live masks. GPU-owned packed pages, ordered commits and bounded staging.'],
 ['20-22 / packing, complexity, implicit tree', 'Real byte counts and full-sweep work; implicit children 2i+1 and 2i+2. Four decisions choose an operator leaf; no billion-node payload search is implied.'],
 ['12 / optional Bayer readout', 'Downstream and optional. No renderer participates in recurrence or is needed for these checks.'],
 ['16-23 / physics, optimality and universality', 'These require separate definitions, experiments or proofs. Mutability alone supplies neither a reward objective nor quantum behavior.'],
], [183, 312], tiny=True)
p('<b>Phi ambiguity resolved:</b> the user says log-encoded polar radius PHI, but gives no logarithm-of-phase definition. This binding uses logarithmic radius and linear modular phase. A logarithm of phase would require another branch/zero/periodicity convention; it is not silently invented.', small=True)

page(3, 'Integer words and the small LUT')
table([
 ['Quantity', 'Exact representation / chosen units'],
 ['LP8 token', '8 bits: high nibble 1..15 is log-radius cell; low nibble is one of 16 phase cells. All 16 high-zero patterns decode zero.'],
 ['Chart and phase', 'Q16: 65,536 units per normalized log-radius period or phase turn. Extended signed u preserves winding before fold.'],
 ['Complex vector', 'Two signed Q11 components packed into uint32; scale 2048. Antipodal entries are exact negations. Products use widened intermediates.'],
 ['Sine lookup', '257 unsigned Q15 quarter-wave values; scale 32,768, integer interpolation, exact quadrant symmetry.'],
 ['Signed geometry', 'Q18 distance/support values; scale 262,144. Radius word is low16(support)+1.'],
 ['Config', 'dt_q16=1024 (1/64), inverse_gain_q16=16384 (1/4). Allowed dt: 1..65536; gain: 0..65536.'],
 ['Math LUT payload', '256 uint32 LP words + 257 uint16 sine words = 1538 bytes; aligned sizeof(MathLut)=1540 bytes.'],
], [142, 353])
h('Encode, decode and fold')
code('h=q>>4; p=q&15; h=0 means exact complex zero\nu=(h-1/2)/15; v=(p+1/2)/16             [real definition]\nz=2^(-4+7.5*u) * exp(i*2*pi*v)       [rounded to Q11]\n\nUword=round((log2_q16(x*x+y*y)-14*65536)/15)+du\nVword=atan2_turn16(y,x)+dv\n(u+65536,v) ~ (u,-v); (u,v+65536) ~ (u,v)')
p('The runtime encoder uses integer repeated-squaring log2 and integer CORDIC phase. These supply finite Q16 words; the real equation specifies what the LUT samples mean. Zero is tested before logarithm or offsets. Negative radial winding uses floor semantics, so odd winding reverses phase consistently.')
p('Rounding is symmetric nearest with ties away from zero where specified. Chart/phase wrap; supported products use bounded or widened integers. Fixed-point words are not exact real numbers. No arbitrary epsilon cutoff is introduced.', small=True)

page(4, 'One complete integer interval')
p('State F contains the packed field P, 31 operator records O, exact per-block B/A, epoch e, cursor c and seed. W blocks form one update window; changing W changes how much field evolves before the operators mutate.')
code('i(t)=(c+t) mod N, 0<=t<W\nstaged[t]=E(P,O,B,A,i(t),e,seed)\ncommit staged results to distinct blocks\nmutate next operator bank from old O and staged feedback\nrebuild live integer routing masks; advance c and e')
p('Data-selected page hops supply neighbours. Four implicit-tree decisions select a leaf 15..30. Its first referenced body, second referenced body and own body execute on eight 16-bit registers; overflow is modular. Body-reference 31 aliases root 0.')
code('drive=(round(s16(reg0)/2), round(s16(reg1)/2)+25032)\nk=round((low16(coeff)+1)/16)           [all Q16]\nf(q)=(drive.u + round(k*sinQ15(q.v)/32768),\n      drive.v + round(k*cosQ15(q.u)/32768))\na=f(q)\nb=f(q + round(dt*a/131072))\nc=f(q + round(dt*b/131072))\nd=f(q + round(dt*c/65536) + (0,2))\nnext=q + round(dt*(a+2*b+2*c+d)/393216)')
p('The +2 event is faithful to source page 7. This is a rounded forced four-stage map; textbook fourth-order real-ODE accuracy is not claimed. Phase displacement adds dt times the wrapped neighbour second difference, then the previous inverse words feed back through the integer gain.')
code('Hplus=round((zR+zG)*23170/32768)\nHminus=round((zR-zG)*23170/32768)\ntwist=round(dt*(xR*xG+yR*yG)/4194304)\nRnext=Q(Hplus, du, qa+twist) XOR jitter\nGnext=Q(Hminus,-du, qb-twist) XOR jitter')
p('A stores -pa and -pb modulo 65,536. It does not invert dot twist, Hadamard, radius fold, codec loss or mutation. B rolls history with event/return/output parity. Feedback also changes code bits, references, signed support, coefficients and positions. Stored interpreter words change; the CUDA ISA does not rewrite itself.', small=True)

page(5, 'Signed SDFs, surface attachment and masks')
code('K(u,v)=((2+.5*cos(2*pi*v))*cos(2*pi*u),\n        (2+.5*cos(2*pi*v))*sin(2*pi*u),\n         .5*sin(2*pi*v)*cos(pi*u),\n         .5*sin(2*pi*v)*sin(pi*u))\nK(u+1,-v)=K(u,v)')
p('This real parameterization defines the geometry sampled by integer Q18 operations. Canonical integer folding makes quotient-equivalent inputs produce identical integer coordinates. It attaches operator locations to K by construction, without ray traversal or projection iteration.')
table([
 ['Support', 'Integer implementation and its limits'],
 ['Circle / apex', 'Nearest integer radial distance; subtract radius for the circle. Apex is a point-distance field.'],
 ['T', 'Minimum of two box signed fields. Membership is meaningful; the union is not exact Euclidean interior distance throughout overlaps.'],
 ['Pyramid side / cone', 'Signed triangle distance from projected edges; cone means the explicitly chosen two-dimensional meridian.'],
 ['Sphere', 'Radial support from ambient four-coordinate K distance, restricted to the chart surface.'],
 ['Near a boundary', 'Circle/sphere/triangle preserve integer inside/outside membership with -1 or +1 when distance rounding would create a false zero.'],
], [119, 376])
h('A 480-byte cache of live decisions')
code('15 internal nodes * 256 LP8 inputs * 1 bit = 480 bytes\nmask[node,token] = (signed_support(node,token_chart)>=0)')
p('The full signed integer support functions remain executable and define these bits. The optimized rebuild uses exact integer sign predicates that avoid unneeded square roots and projections; comparison against signed evaluation checks this specialization. Masks are rebuilt from every current operator bank. Jitter, history and route parity still combine with the cached predicate at runtime.')
p('The sign specialization passed 187,164 CPU comparisons and 3,598 boundary/coverage assertions with zero failures. GPU checks compare all 3,840 live support bits with the signed CPU reference.',small=True)
p('The source gives no global scalar signed-distance equation for a Klein bottle. This binding uses quotient-constrained locations and signed local supports. It does not assert a global inside/outside field for a non-orientable surface, or replace all geometric values with Boolean masks.', small=True)

page(6, 'Cache footprint and the native sampler boundary')
table([
 ['Active data component', 'Compact', 'Optional exact D4 cache'],
 ['31 operator records', '1984 B', '1984 B'],
 ['Integer math LUT', '1540 B', '1540 B'],
 ['15 x 256 routing decisions', '480 B', '480 B'],
 ['Canonical pair cache', '0 B', '8192 x 8 B = 65,536 B'],
 ['Logical active data total', '<b>4004 B</b>', '<b>69,540 B</b>'],
], [215, 125, 155])
p('These totals exclude CUDA machine code, interpreter implementation, stack/register spills, the second operator bank, allocation alignment, handles, driver/runtime resources, staging and payload. Exact allocated/shared bytes belong in each run report. The small representation is not a claim that the entire program fits in 4004 bytes.')
p('The optional D4 table stores canonical integer Hadamard/log/phase outputs under four quarter-turn rotations and reflection. The minus output reuses plus with an antipodal second input. A record stores u, phase and orientation correction bits. CPU cache checks passed 1,253,890 assertions; the GPU cache check exactly matches both output charts across all 65,536 pairs. Full snapshot equality is checked separately.')
h('Integer data arithmetic is narrower than zero floating opcodes')
p('Native BC5 hardware decoding retains a float-typed CUDA sampler interface. Centre-coordinate bits are built with integer operations and returned UNORM bits are recovered as integer tokens. RG8 returns integer texels. Bit-preserving moves and this explicit fixed-function boundary are reported, rather than hidden.')
p('<b>Machine-code exception:</b> SASS uses HFMA2 with architectural zero-register operands and literal constants to materialize fixed bits. The verifier permits only the recognized constant-only form. This is a floating opcode, so <b>zero floating opcodes would be false</b>. It does not perform input-dependent floating arithmetic. Dynamic floating arithmetic/conversions/comparisons and SFU reciprocals remain prohibited; both PTX and SASS must be audited.')
audit_rows = evidence_rows(AUDITS, 3)
if audit_rows:
    table([['Saved instruction audit', 'Result / scope']] + audit_rows, [157, 338], tiny=True)
else:
    p('<b>Final per-variant instruction audit summary: pending.</b> The explicit native-sampler and constant-materialization exceptions must appear in the saved evidence.', small=True)
p('Cache preference and persistence are hardware policies, not locks. A larger exact table may win or lose depending on reuse and occupancy; its inclusion does not itself establish a speedup.', small=True)

page(7, 'Two-stream interference: measured component behavior')
code('a=r*exp(i*theta); b=r*exp(i*(theta+phi))\nIplus=r*r*(1+cos(phi)); Iminus=r*r*(1-cos(phi))\nIplus+Iminus=2*r*r              [isolated real Hadamard]')
p('The diagnostic sweeps sixteen phase differences at radial nibble 8. Solid sample curves use the actual integer functions; dashed curves use the nominal equal-radius identity. Connecting samples guides the eye and does not introduce a physical screen or propagation model.')
story.append(phase_plot())
cancel = DIAG.get('exact_cancellation', {})
sweep = DIAG.get('phase_sweep', {})
p(f'<b>Exact symbolic cancellation:</b> {cancel.get("antipodal_raw_nonzero_failures", "pending")} failures across 256 symbols, including sixteen zero aliases and 240 nonzero values. Equal-input difference cancellation and encoded antipodal zero also have {cancel.get("equal_input_difference_nonzero_failures", "pending")} failures.')
p('The rounded integer input vectors have slightly phase-dependent radii. The JSON therefore also records the exact real sum/difference identity for those actual decoded vectors, separate from the nominal curve. Raw integer port energy differs from that identity by at most '+number(sweep.get('maximum_integer_port_energy_error_against_decoded_input_identity'), 7)+' in this sweep.', small=True)
p('This validates finite interference algebra and its error. The next page tests quantum-style two-arm compositions using the production math. The full field recurrence has no detector, Born measurement, entangled tensor-product register or established quantum-state fidelity.', small=True)

page(8, 'Quantum mechanisms: fidelity, fringes and lost norm')
p('Two probes exercise the production integer primitives: apply H twice, and split one occupied arm with H, rotate the second arm, then recombine with H. These are isolated CPU mathematical circuits, not a substitute simulation of the full evolving field.')
code('ideal H*H = identity\nideal Pminus after H-phase-H = sin(phi/2)^2\nF = |<input,output>|^2 / (norm(input)*norm(output))\nR = norm(output)/norm(input)      [squared vector norms]')
p('F compares state direction up to a global phase and is normalized only in the diagnostic. R separately reveals amplification or loss. The kernel does not normalize its state or perform measurement. Reported probabilities are host readouts, not implemented Born-rule events.',small=True)
recovery = {row['name']:row for row in QUANTUM.get('recovery_diagnostics',[])}
qr = recovery.get('raw_integer_H_squared',{})
qe = recovery.get('H_LP8_H_LP8',{})
def qm(row,metric,key,places=6):
    return number(row.get(metric,{}).get(key),places)
table([
 ['Recovery over 65,280 nonzero pairs','Minimum F','Median F','Norm ratio R range'],
 ['Integer H then H',qm(qr,'normalized_state_overlap_fidelity','min'),qm(qr,'normalized_state_overlap_fidelity','median'),qm(qr,'unnormalized_output_input_norm_ratio','min')+' to '+qm(qr,'unnormalized_output_input_norm_ratio','max')],
 ['H / LP8 / H / LP8',qm(qe,'normalized_state_overlap_fidelity','min'),qm(qe,'normalized_state_overlap_fidelity','median'),qm(qe,'unnormalized_output_input_norm_ratio','min')+' to '+qm(qe,'unnormalized_output_input_norm_ratio','max',2)],
], [198,83,83,131],tiny=True)
p('The census includes all 65,536 token pairs and excludes 256 zero/zero alias pairs from normalization. A high median fidelity cannot certify every state: LP8 wrapping produces a worst-case direction mismatch as well as large norm changes.',small=True)
h('Fringe-shape accuracy, not just a bright and a dark point')
sweep_rows=[['Probe / radial bin','Raw max error, percentage points','LP8 max error, percentage points']]
for key,title in [('equal_amplitude_phase_sweeps','Equal arms'),('H_phase_H_interferometer','H-phase-H')]:
    for row in QUANTUM.get(key,{}).get('sweeps',[]):
        sweep_rows.append([f'{title} / {row["radial_bin"]}',number(row['max_raw_probability_error']*100,5),number(row['max_encoded_probability_error']*100,5)])
table(sweep_rows,[198,148,149],tiny=True,padding=5)
p('Each row uses sixteen phase settings. All these sampled port-energy visibilities are 1, using (maximum-minimum)/(maximum+minimum), because exact dark ports survive. Yet some encoded fringe shapes deviate by about 96 percentage points. Visibility alone conceals that failure.',small=True)
p('<b>Application evidence:</b> the raw integer H and phase operations are useful two-path interference building blocks at measured precision. The present LP8 quotient is not a general quantum-state codec. Full nonlinear motion, history/inverse feedback, BC5 loss and operator mutation have not been shown to implement unitary quantum evolution.',small=True)

page(9, 'Numerical accuracy and limits of the quotient')
pair = DIAG.get('exhaustive_pair_energy', {})
raw = pair.get('raw_integer_hadamard_relative_norm_error', {})
ratio = pair.get('after_lp8_output_input_energy_ratio', {})
err = pair.get('after_lp8_absolute_relative_energy_error', {})
amp = DIAG.get('amplitude_accuracy', {}).get('lp8_encoding_in_window_relative_amplitude_error', {})
src = DIAG.get('source_wavefront', {})
def percent(obj, key, places=4):
    val = obj.get(key)
    return number(val*100, places) + '%' if isinstance(val, (int,float)) else 'pending'
table([
 ['Executed diagnostic', 'Measured result / interpretation'],
 ['Hadamard before LP8', f'Median relative norm error {percent(raw,"p50")}; maximum {percent(raw,"maximum")}. All 65,536 pairs checked; 256 zero/zero pairs excluded from ratios.'],
 ['After LP8 re-encoding', f'Energy ratios range from {number(ratio.get("minimum"),8)} to {number(ratio.get("maximum"),3)}. Median absolute relative energy error {percent(err,"p50")}; 95th percentile {percent(err,"p95")}.'],
 ['Concrete wrapping witness', 'Input tokens [0,16] produce [255,247] after the encoded split. Exact cancellation does not stop small nonzero radii from wrapping into the high-radius cells.'],
 ['In-window amplitude quantization', f'Median {percent(amp,"p50")}; 95th percentile {percent(amp,"p95")}; maximum {percent(amp,"maximum")}. {amp.get("count","pending"):,} accepted samples from the stated radius/phase grid.' if isinstance(amp.get('count'),int) else 'Pending diagnostic data.'],
 ['Source amplitude 2', f'Token 176 decodes magnitude {number(src.get("decoded_G_magnitude"),8)}, phase {number(src.get("decoded_phase_degrees"),5)} degrees; relative amplitude error {percent(src,"relative_amplitude_error")}.'],
], [151, 344])
p('Radius folding identifies magnitudes differing by 2^7.5, approximately 181.02, with phase reversal. This computational quotient does not conserve ordinary wave energy. RG8 removes BC5 token-byte loss; it does not remove LP8 quantization or the quotient.', small=True)
h('Exact invariants and the fourth-stage event')
inv = DIAG.get('exact_invariants', {})
rk = DIAG.get('forced_four_stage_map', {})
table([
 ['Check', 'Result'],
 ['Klein coordinate seam', f'{inv.get("klein_quotient_cases","pending")} cases; {inv.get("klein_coordinate_mismatches","pending")} integer coordinate mismatches.'],
 ['Modular inverse phase', f'{inv.get("phase_inverse_words","pending")} words; {inv.get("phase_inverse_failures","pending")} composition failures.'],
 ['Forced four-stage map', f'{rk.get("cases","pending")} cases; {rk.get("native_reference_mismatches","pending")} mismatches against independently assembled integer stages. The event changes {rk.get("event_changes_final_integer_output_cases","pending")} final outputs; rounding hides its effect in the others.'],
], [151, 344])
p('The amplitude sample uses 960 logarithmic radial midpoints by 256 phase midpoints, quantized to Q11. Sixteen rounded inputs outside the actual nominal radius window are excluded and counted. These deterministic populations are diagnostic scopes, not measured application distributions or statistical confidence intervals.', small=True)

page(10, 'Performance: how fast the items are revised')
p('One token pair is one two-stream item. Pair updates per second count revisions, not unique stored items, physical particles, frames, FLOPS or solved tasks. A fair optimization comparison holds the integer numerical law and recurrence parameters fixed.')
if PERF:
    rows = [['Variant / codec', 'Cache', 'Million<br/>updates/s', 'Wall ms', 'Reference<br/>ratio']]
    for row in PERF[:10]:
        rate = row.get('median_pair_updates_per_second')
        wall = row.get('median_wall_seconds')
        rows.append([escape(str(row.get('variant','')))+' / '+escape(str(row.get('codec',''))),
                     escape(str(row.get('cache_policy','recorded'))), number(rate/1e6 if isinstance(rate,(int,float)) else None,2),
                     number(wall*1000 if isinstance(wall,(int,float)) else None,2), number(row.get('speedup_vs_reference'),2)])
    table(rows, [169,73,86,80,87], tiny=True,padding=5)
    if len(PERF)>10:
        p(f'{len(PERF)-10} additional measurement rows are retained in final_summary.json.',small=True)
    scope=SUMMARY.get('benchmark_scope',SUMMARY.get('performance_scope',SUMMARY.get('notes')))
    p('<b>Recorded measurement scope:</b> '+escape(value_summary(scope)) if scope else '<b>Scope note absent from the summary:</b> consult the underlying run commands for field size, W, steps, batch, repetitions and clocks.',small=True)
    ranges=[]
    for codec in ['bc5','rg8']:
        timing=BENCH.get('performance',{}).get(codec,{}).get('summary',{}).get('timings',{}).get('cached_balanced',{}).get('circulation_wall_ms',{})
        if timing:
            ranges.append(f'{codec.upper()} {number(timing.get("min"),3)}-{number(timing.get("max"),3)} ms')
    if ranges:
        p('<b>Three-trial cached/balanced ranges:</b> '+ '; '.join(ranges)+'. These are observed ranges, not confidence intervals. The shared and uncached texture variants are slower than the reference in this workload.',small=True)
else:
    table([['Required evidence','Preparation status'],['Repeated integer reference/optimized timings','Pending final_summary.json; no old floating-edition timings substituted.'],['Workload and timing distribution','Record pages, side, W, steps, dt/gain words, seed, hops, codec, cache policy, warmup and repetition count.'],['Cache variant comparison','Compact and optional D4 paths must prove same-law state equality before a speed ratio is interpreted as an optimization.']], [172,323])
h('Read the stopwatch correctly')
code('updates/s = 16*visited_blocks / circulation_seconds\nmean interval time = circulation_seconds / intervals\nequivalent sweep time = stored_pairs / updates_per_second')
p('A circulation timer excludes allocation/initialization/export only when the measured harness says so. Whole-process timing includes startup. A derived equivalent sweep time uses average throughput; it is not a directly timestamped visit to every block. Faster results for a different W, codec or numerical binding are different workloads.')
chosen=next((row for row in PERF if row.get('variant')=='cached' and row.get('codec')=='bc5' and row.get('cache_policy')=='balanced'),None)
if chosen:
    p(f'<b>ELI5, cached BC5:</b> each interval revises 1,048,576 items in an average {number(chosen.get("mean_interval_ms"),3)} ms. Revising the 134.22 million stored items once takes a derived {number(chosen.get("derived_sweep_ms"),2)} ms; the whole process median is {number(chosen.get("median_process_seconds",0)*1000,1)} ms including startup.',small=True)
h('Counters answer a different question')
profile_rows=evidence_rows(PROFILES,3)
if profile_rows:
    table([['Saved profiler observation','Recorded scope/result']]+profile_rows,[160,335],tiny=True)
else:
    p('Final profiler summary is pending or was not supplied. No cache-hit rate, achieved DRAM bandwidth or bandwidth-saturation claim is inferred from allocation size or a configured cache policy.')
p('The cache hitRatio setting is a preference, not an observed hit percentage. More cache hits do not necessarily imply a faster kernel. Occupancy, working-set size and arithmetic cost must be interpreted alongside unprofiled repeated runtime measurements.',small=True)

page(11, 'Capacity and validation: what is actually established')
table([['Packed layout','Token bytes / 16 pairs','B/A bytes','Total bytes/pair'],['BC5','16','8','1.5'],['RG8','32','8','2.5']],[143,145,82,125])
p('BC5 uses 40% fewer payload bytes than RG8 with the same exact B/A grouping. Neither the extra channels nor the second operator bank are free. A complete field sweep has work at least proportional to the payload block count.',small=True)
if CAPACITY:
    rows=[['Codec / variant','Payload GiB','Stored pairs, million','Free MiB / sweeps']]
    for row in CAPACITY[:4]:
        report=row.get('report',row)
        payload=report.get('payload_bytes'); pairs=report.get('token_pairs'); free=report.get('free_after_packing',report.get('free_bytes'))
        rows.append([escape(str(report.get('codec',row.get('codec',''))))+' / '+escape(str(row.get('variant',report.get('kernel_variant','')))),
                     number(payload/2**30 if isinstance(payload,(int,float)) else None,3),number(pairs/1e6 if isinstance(pairs,(int,float)) else None,2),
                     number(free/2**20 if isinstance(free,(int,float)) else None,1)+' / '+str(report.get('complete_sweeps_this_run','pending'))])
    table(rows,[140,100,140,115],tiny=True)
    p(escape(value_summary(SUMMARY.get('capacity_scope','Counts describe the recorded allocation runs. Actual physical residency and recurring transfers require separate evidence.'))),small=True)
else:
    p('<b>New integer-edition capacity evidence: pending.</b> The theoretical layout above is not a measured usable allocation. Near-capacity runs must retain useful payload, initialize it and complete a full sweep.',small=True)
h('Saved acceptance summary')
validation_rows=evidence_rows(VALIDATION,7)
if validation_rows:
    table([['Evidence','Result and scope']]+validation_rows,[157,338],tiny=True,padding=5)
    p('The validation harness ran 70 processes for its 46 checks. Separate regression runs passed all 12 CTest entries and 27 Python tests. Those totals include historical/regression checks and are not additional independent proofs of quantum behavior.',small=True)
else:
    table([['Component evidence already available','Scope'],['Math: 11 cases / 1,483,985 assertions','CPU integer math, signed support magnitudes and independent error bounds.'],['Core: 8 cases / 296,554 assertions','CPU route/mask and staged-state equivalence, forced event, mutation, continuation and ablations.'],['Full GPU acceptance, sanitizers and variants','Pending final summary. CPU checks do not establish a complete GPU run.']],[193,302],tiny=True)
p('Exact snapshots are stronger evidence than matching only an operator digest. State equality applies to the tested inputs and decoder law. Native BC5 rounding is a separately checked boundary; a tolerated local decode unit cannot excuse arbitrary later state divergence. Integer-1 snapshots use version 4 and reject historical floating version 3.',small=True)

page(12, 'Reproduce, inspect and extend')
p('Use a Visual Studio 2022 developer shell with CUDA 12.8 or later. The following uses a separate Ninja Release build folder; PowerShell continuations are real backticks. The integer CLI accepts integer dt/gain words.')
code('cmake -S . -B build-integer -G Ninja `\n  -DCMAKE_BUILD_TYPE=Release\ncmake --build build-integer --parallel\n.\\build-integer\\dawnwood_integer_cached.exe --self-test\n.\\build-integer\\dawnwood_integer_cached.exe --codec bc5 `\n  --pages 32 --page-side 2048 --blocks-per-step 65536 `\n  --dt-q16 1024 --inverse-gain-q16 16384 `\n  --steps 256 --batch 32 --report work\\integer.json\npython tools\\build_integer_pdf.py')
p('The recommended cached executable defaults to balanced cache policy. Adding <font name="DIM">--cache-policy l1</font> improved the recorded large-case circulation median; profile counter results are scoped separately. Keep the numerical configuration fixed when comparing policies.',small=True)
p('The saved final summary and individual reports identify variant names, exact commands and hashes. Repeat with the matching integer reference and the same parameters. A comparison to the earlier floating model is a cross-model comparison, not bitwise optimization evidence.',small=True)
table([
 ['Project-relative artifact','Why it matters'],
 ['model/integer_binding.json','Numerical units, rounding, model/snapshot identifiers and evidence contract.'],
 ['docs/INTEGER_REQUIREMENTS.md','Literal source requirements and a complete code-plus-evidence checklist.'],
 ['results/integer/theory_diagnostics.json','Phase-sweep plot data, error distributions, invariants and compiler/source/binary provenance.'],
 ['results/integer/quantum_mechanism_checks.json','Actual H-squared and H-phase-H probes, normalized overlap, unnormalized norm ratios and phase-sweep error.'],
 ['results/integer/final_summary.json','New performance, capacity, validation and instruction-audit summary consumed by this report.'],
 ['tools/verify_integer_device_code.py','PTX/SASS checks and explicit native sampler / constant-only HFMA2 exceptions.'],
], [244,251],tiny=True,padding=5)
h('Primary references')
refs=[
 ('Source', 'Supplied double-slit-theory.pdf, 24 pages; unchanged SHA-256 e3cf7d49e6a4942c7ccad4805f6a2a07e1c817753ff8d384b1f2e37791ebbe27.'),
 ('NVIDIA', '<link href="https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__TEXTURE__OBJECT.html" color="#057A88">Texture object API</link>; <link href="https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/l2-cache-control.html" color="#057A88">L2 cache control</link>; <link href="https://docs.nvidia.com/cuda/parallel-thread-execution/index.html" color="#057A88">PTX ISA</link>; <link href="https://docs.nvidia.com/cuda/cuda-binary-utilities/index.html" color="#057A88">Binary utilities</link>.'),
 ('Physics', '<link href="https://www.feynmanlectures.caltech.edu/III_01.html" color="#057A88">Feynman Lectures III.1</link>: amplitude addition, interference and probability of detection.'),
 ('Packing', '<link href="https://learn.microsoft.com/en-us/windows/win32/direct3d11/texture-block-compression-in-direct3d-11" color="#057A88">Microsoft block-compression reference</link>: BC5 two-channel 16-byte blocks.'),
]
for name,text in refs:
    p(f'<b>{name}:</b> {text}',small=True)
p('No physical experiment, quantum hardware, universal-computation proof or beneficial-mutation theorem is implied. The delivered object is an explicit, editable, finite classical recurrence whose numerical and hardware properties can be measured.',small=True)

def footer(canvas,doc):
    canvas.saveState(); width,height=doc.pagesize
    canvas.setStrokeColor(TEAL);canvas.setLineWidth(.65);canvas.line(50,42,width-50,42)
    canvas.setFont('DI',8);canvas.setFillColor(MUTED)
    canvas.drawString(50,28,'Dawnwood Interactive | integer-1 | 16 Sep 2026')
    canvas.drawRightString(width-50,28,str(doc.page));canvas.restoreState()

document=SimpleDocTemplate(str(OUT),pagesize=(595.276,841.89),leftMargin=50,rightMargin=50,topMargin=42,bottomMargin=57,
                          title='Dawnwood Interactive - Complete Integer Kernel Formalization',author='Tom Klootwijk',
                          subject='Literal-source integer binding, numerical diagnostics and measured CUDA evidence')
document.build(story,onFirstPage=footer,onLaterPages=footer)
print(OUT)
print('Final GPU summary present:', bool(SUMMARY))
