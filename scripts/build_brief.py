"""Render the Swarm Research paper with vector STIX equations."""
import json
import os
from pathlib import Path
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Flowable
from reportlab.graphics.shapes import Drawing, Path as ShapePath
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
M = json.loads((ROOT / 'METRICS.json').read_text())
PUBLIC = M['retrospective']
INK, BODY, GREY = map(HexColor, ['#17191E', '#292C32', '#6C7078'])
RULE, PANEL, HEAD = map(HexColor, ['#DEDFE2', '#F6F7F8', '#F0F1F2'])
A4 = (595.2756, 841.8898)
LEFT, WIDTH = 62.3622, 470.5512
FONT = Path(os.environ.get('IWU_FONT_TTC', ''))
VERSION = '0.1.0-rc.1'
FORMULAS = {
 'work': {'latex': r'\widehat{W}=\sum_{i=1}^{N}\pi_i h_i\widehat{p}_i', 'plain': 'W_hat = sum_i(pi_i * h_i * p_hat_i)', 'meaning': 'Estimated IWU-E60 credit per assigned task.'},
 'acceptance': {'latex': r'h_i=\frac{t_i}{60},\qquad \widehat{p}_i=\frac{1}{n_i}\sum_{j=1}^{n_i}Y_{ij}', 'plain': 'h_i = t_i / 60; p_hat_i = sum_j(Y_ij) / n_i', 'meaning': 'Reference expert minutes and acceptance over scheduled episodes.'},
 'cost': {'latex': r'\widehat{C}=\sum_i\pi_i\frac{1}{n_i}\sum_j C_{ij},\qquad \widehat{\eta}_C=\frac{\widehat{W}}{\widehat{C}}', 'plain': 'C_hat = sum_i(pi_i * mean_j(C_ij)); efficiency = W_hat / C_hat', 'meaning': 'Ratio of workload-weighted mean credit to complete mean episode cost.'},
 'missing': {'latex': r'\widehat{W}^{-}=\sum_i\pi_i h_i\frac{A_i}{n_i},\qquad \widehat{W}^{+}=\sum_i\pi_i h_i\frac{A_i+U_i}{n_i}', 'plain': 'W_minus = sum_i(pi_i * h_i * A_i / n_i); W_plus = sum_i(pi_i * h_i * (A_i + U_i) / n_i)', 'meaning': 'Missingness bounds: A_i observed accepted; U_i unknown.'},
 'lower95': {'latex': r'\mathrm{IWU\! -\! L95}=\max\!\left(0,\widehat{W}^{-}-\sqrt{\frac{\ln(20)}{2}\sum_{g\in G}B_g^2}\right)', 'plain': 'IWU-L95 = max(0, W_minus - sqrt(ln(20) * sum_g(B_g^2) / 2))', 'meaning': 'One-sided 95% lower confidence bound on expected fixed-registry credit under the stated assumptions.'},
 'block': {'latex': r'B_g=\sum_{(i,j)\in g}\frac{\pi_i h_i}{n_i}', 'plain': 'B_g = sum_(i,j in g)(pi_i * h_i / n_i)', 'meaning': 'Maximum contribution of independent block g; dependent observations share a block.'},
}

def register_fonts():
    if not FONT.is_file(): raise RuntimeError('Matching typography requires HelveticaNeue.ttc; set IWU_FONT_TTC.')
    for name, index in [('HN', 0), ('HNItalic', 2), ('HNLight', 7), ('HNMedium', 10)]:
        pdfmetrics.registerFont(TTFont(name, str(FONT), subfontIndex=index))
    pdfmetrics.registerFontFamily('HN', normal='HN', bold='HNMedium', italic='HNItalic', boldItalic='HNItalic')

def equation_drawing(key, width, height, size=22):
    tp = TextPath((0,0), '$'+FORMULAS[key]['latex']+'$', size=size, prop=FontProperties(math_fontfamily='stix'))
    box = tp.get_extents(); scale = min(1., (width-16)/box.width, (height-8)/box.height)
    dx = (width-scale*box.width)/2-scale*box.x0; dy = (height-scale*box.height)/2-scale*box.y0
    shape = ShapePath(fillColor=INK, strokeColor=None)
    current = start = None
    def xy(x,y): return dx+scale*x, dy+scale*y
    for coords, code in tp.iter_segments(curves=True):
        if code == 1:
            current = start = xy(*coords); shape.moveTo(*current)
        elif code == 2:
            current = xy(*coords); shape.lineTo(*current)
        elif code == 3:
            control, end = xy(*coords[:2]), xy(*coords[2:])
            c1 = tuple(current[k]+2*(control[k]-current[k])/3 for k in (0,1))
            c2 = tuple(end[k]+2*(control[k]-end[k])/3 for k in (0,1))
            shape.curveTo(*c1,*c2,*end); current=end
        elif code == 4:
            pts = [xy(*coords[k:k+2]) for k in (0,2,4)]
            shape.curveTo(*(v for point in pts for v in point)); current=pts[-1]
        elif code == 79: shape.closePath(); current=start
        else: raise ValueError(code)
    d = Drawing(width,height); d.add(shape); return d

class EquationPanel(Flowable):
    def __init__(self,key,caption,height=81,size=22):
        Flowable.__init__(self)
        self.key,self.caption,self.width,self.height,self.size=key,caption,WIDTH,height,size
    def draw(self):
        c=self.canv; c.setFillColor(PANEL); c.setStrokeColor(RULE); c.setLineWidth(.45)
        c.rect(0,0,self.width,self.height,fill=1,stroke=1)
        renderPDF.draw(equation_drawing(self.key,self.width-18,self.height-27,self.size),c,9,24)
        c.setFillColor(GREY); c.setFont('HN',7.5); c.drawCentredString(self.width/2,10,self.caption)

class ResearchCover(Flowable):
    """Front matter positioned to the supplied Swarm Research paper's measured grid."""
    def __init__(self):
        Flowable.__init__(self); self.width=WIDTH; self.height=207.0
    def draw(self):
        c=self.canv
        def line(text,top,size=9.2,font='HN',color=BODY,x=0):
            c.setFont(font,size);c.setFillColor(color)
            c.drawString(x,self.height-(top-65.1969)-size*.787,text)
        line('IWU: Inference Work Units',70.5219,25,'HNLight',INK)
        line('for Verified AI Work',100.5219,25,'HNLight',INK)
        line('A proposed accounting standard with an explicit evidence and uncertainty contract',140.1464,11.5,'HNItalic',GREY)
        line('Swarm Research',179.1565)
        line('September 2026',192.8565)
        for title,value,top in [('Study ID: ','iwu-validation-v01',221.8435),
                                ('Version: ',VERSION+' / IWU-E60 draft 0.1',234.0435)]:
            line(title,top,8.2,color=GREY)
            line(value,top-.1558,8.2,'Courier',GREY,pdfmetrics.stringWidth(title,'HN',8.2))
        line('Study date: September 15, 2026',246.2435,8.2,color=GREY)

def p(text,kind='body'):
    styles={
      'body':('HN',9.2,13.7,BODY,0,15.5), 'small':('HN',7.8,11.4,GREY,0,7),
      'title':('HNLight',25,30,INK,0,12.5), 'subtitle':('HNItalic',11.5,16,GREY,0,14),
      'h1':('HNMedium',14.2,18.5,INK,14,9), 'h2':('HNMedium',11.2,15,INK,9,7),
      'meta':('Courier',8.2,12,GREY,0,11)}
    font,size,leading,color,before,after=styles[kind]
    return Paragraph(text,ParagraphStyle(kind,fontName=font,fontSize=size,leading=leading,textColor=color,spaceBefore=before,spaceAfter=after))

def table(headers,rows,widths):
    def cell(s,bold=False):
        return Paragraph(str(s),ParagraphStyle('cell',fontName='HNMedium' if bold else 'HN',fontSize=7.6,leading=10.6,textColor=BODY))
    t=Table([[cell(x,True) for x in headers]]+[[cell(x) for x in row] for row in rows],colWidths=widths)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HEAD),('VALIGN',(0,0),(-1,-1),'TOP'),
      ('LINEBELOW',(0,0),(-1,-1),.35,RULE),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
      ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    return t

def chrome(c,doc):
    c.setCreator('Swarm Research')
    c.saveState(); c.setFillColor(INK); c.setFont('HNLight',15); c.drawString(28.34646,812.126,'Swarm')
    c.setStrokeColor(RULE); c.setLineWidth(.45); c.line(28.34646,800.7874,566.9291,800.7874)
    c.setFont('HN',7.2); c.setFillColor(GREY); c.drawString(28.34646,19.84252,str(doc.page))
    c.drawRightString(566.9291,19.84252,'swarm.services')
    w=pdfmetrics.stringWidth('swarm.services','HN',7.2)
    c.linkURL('https://swarm.services',(566.9291-w,18,566.9291,29),relative=0,thickness=0)
    c.restoreState()

def make_pdf():
    out=ROOT/'output/pdf'; out.mkdir(parents=True,exist_ok=True)
    dest=out/'IWU-RESEARCH-BRIEF.pdf'
    doc=SimpleDocTemplate(str(dest),pagesize=A4,leftMargin=LEFT-6,rightMargin=LEFT-6,topMargin=59.1969,bottomMargin=55,
        title='IWU: Inference Work Units for Verified AI Work',author='Swarm Research',
        subject='Reference-work accounting, uncertainty and verification for AI systems',invariant=1)
    s=[]
    def add(*items):s.extend(items)
    add(ResearchCover(),p('Abstract','h1'),
        p('IWU (Inference Work Units) proposes a common calculation for verified AI work on a named workload. The IWU-E60 reference profile credits 60 active expert seconds to each unit of independently accepted work. The profile specifies acceptance, task weights, observable execution evidence, resource costs and uncertainty. Its meaning depends on the registered workload and human calibration.'),
        p('A reference implementation passed 60 software test methods, including 3,000 deterministic randomized cases. A retrospective pilot analyzed 5,293 public records across 170 task IDs. Six fresh model sessions supplied 72 accepted answers on 12 repeated test items. An additional 12,000 synthetic experiments examined a dependence-aware uncertainty correction. These tests support implementation review. Human calibration, trusted trace completeness and independent replication remain open.'),
        p('1. Research question and proposed unit','h1'),
        p('Can a versioned reference-work accounting profile support useful comparisons of AI systems across models, tools and execution strategies? The proposed unit anchors credit to a verified outcome and a frozen expert-time reference. A result identifies the workload, acceptance rules, system configuration and operating budget.'),
        EquationPanel('work','Estimated IWU-E60 credit per assigned task on the registered workload.',85,24),Spacer(1,11),
        p('Here pi is the frozen task probability, h is reference-expert time in minutes, and p-hat is observed acceptance averaged over scheduled episodes. Accepted deliverables earn credit. Retry costs and tool activity remain part of the episode evidence.'),
        p('Status and scope','h2'),
        p('Current status: an accounting prototype and standards proposal. Empirical scores use provisional human-time references. Audited certification requires independently calibrated weights, complete episode evidence and known effective system identity.','small'),PageBreak())
    add(p('2. Calculation and evidence contract','h1'),
        p('Freeze a registry of tasks i, probabilities pi_i summing to one, calibrated expert seconds t_i, an acceptance function and a complete system policy. For scheduled episode j, Y_ij is an independently verified acceptance outcome in {0,1}. The sample plan and permitted assistance are fixed before execution.'),
        EquationPanel('acceptance','n_i counts every scheduled episode; t_i is calibrated active expert time.',83),Spacer(1,10),
        p('Average within each task before applying workload weights. Internal retries share one external episode and one maximum task credit. Optional partial-credit atoms require prespecified acceptance gates and fractions summing to one. Their total credit is bounded by the original task weight.'),
        p('Full-cost efficiency','h2'),EquationPanel('cost','C_ij includes failed attempts, permitted tools and all charges inside the declared boundary.',87),Spacer(1,10),
        p('Report currency, price date, actual or estimated charges, and cost completeness. Full-cost efficiency requires a complete positive denominator. Tokens, elapsed time and energy can be reported as separate resource measures with their own definitions.'),
        p('Unknown outcomes','h2'),EquationPanel('missing','A_i is the observed accepted count; U_i is the unknown count among scheduled episodes.',83),Spacer(1,10),
        p('These identified bounds describe missingness. Sampling and calibration uncertainty require additional treatment. An unidentified point estimate is reported as unavailable.'),
        p('Observable evidence','h2'),
        p('A conformant record links frozen inputs and task versions to effective model identity, allowed tools, consumed artifacts, retry lineage, final outputs, independent verification and disjoint charges. Sensitive tool evidence may remain auditor-accessible. Private internal reasoning is outside the collection boundary. A trusted capture layer and external checks establish completeness.'),
        p('Score identity: specification version + registry hash + workload + effective system configuration + budget policy. Comparability requires matching references and operating boundaries.','small'),PageBreak())
    rows=[[a['alias'],f"{a['reference_minute_credit_per_task']:.2f}",f"{a['task_bootstrap_95ci'][0]:.2f} to {a['task_bootstrap_95ci'][1]:.2f}"] for a in PUBLIC['systems']]
    add(p('3. Pilot evidence','h1'),
        p('The retrospective selection contains 5,293 records, 170 shared task IDs and 50 task families across four historical aliases from one provider. The availability-based selection rule was recorded before analysis. Imported human-time references and heterogeneous task versions give the following scores the status of reference-minute proxies.'),
        table(['Historical system alias','Credit / task','Conditional task-bootstrap 95% interval'],rows,[186,87,WIDTH-273]),Spacer(1,9),
        p('Intervals use 10,000 paired task resamples and describe task-resampling sensitivity conditional on recorded outcomes. Family-cluster intervals and full diagnostics accompany the release. They address a different uncertainty target from the fixed-registry bounds in Section 4.','small'),
        p('Sensitivity and provenance','h2'),
        p('The longest 10% of tasks carry 63.7% of reference-time weight. Across 1,000 split-half partitions, full rankings disagree in 11.5% of partitions. Nineteen task weights are estimates. Every task in the selected four-alias comparison has a task-version consistency or completeness gap. These properties limit calibration and comparability claims.'),
        p('An exploratory four-provider calculation used 5,477 records on the same 170 task IDs, with overlap in the primary sample. It extends the data-processing feasibility check. Original harness differences, calibration gaps and trace limitations remain.'),
        p('Implementation and live instrumentation','h2'),
        table(['Check','Observed result','Scope'],[
          ['Software conformance','60 test methods passed','Includes 3,000 deterministic randomized cases.'],
          ['Selected fault injection','12 / 12 faults detected','Hand-selected same-project mutations.'],
          ['Local reproduction','Two byte-identical reexecutions','Same environment and pinned source.'],
          ['Live smoke test','72 / 72 accepted answers','Six sessions; 12 reused arithmetic/path/selection items.']], [123,123,WIDTH-246]),Spacer(1,10),
        p('The live test requested gpt-5.6-sol at medium effort in three direct-answer sessions and three local-computation sessions. Effective-model attestation, full replayable tool bodies, invoice-backed costs and human timing calibration were unavailable. The results support a small scoring and instrumentation check. Broader task reliability and audited work measurement need further evidence.'),
        p('Source: METR/eval-analysis-public, commit 52cb829c7a2efb2d659285c4b1768d191d97f8d2. Raw-source and protocol SHA-256 commitments are recorded in the manifest. Organizational endorsement remains unclaimed.','small'),PageBreak())
    labels=['Independent tasks','Concentrated weights','Near-ceiling success','Near-floor success','Family dependence','One shared outcome']
    rows=[[label,f"{100*a['methods']['task_bootstrap']['coverage_or_lower_validity']:.2f}%",f"{100*a['methods']['block_bound']['coverage_or_lower_validity']:.2f}%"] for label,a in zip(labels,M['uncertainty_correction']['scenarios'])]
    add(p('4. A dependence-aware confidence bound','h1'),
        p('A supplemental near-ceiling simulation exposed a release-critical interpretation error: a task-bootstrap interval covered fixed-registry expected credit in 38.9% of experiments when assessed as a general 95% guarantee. The correction explicitly defines the uncertainty target and uses a conservative bounded-sum procedure.'),
        p('Let G partition scheduled contributions into independent blocks. B_g is the maximum contribution of block g. Correlated observations share a block. W-hat-minus is observed accepted credit; unknown assigned outcomes remain uncredited within the lower-bound calculation.'),
        EquationPanel('lower95','One-sided 95% lower confidence bound on expected fixed-registry reference-work credit.',87,23),Spacer(1,9),
        EquationPanel('block','Block ranges include all scheduled contributions, including unknown outcomes.',73,22),Spacer(1,10),
        p("The result follows from Hoeffding's one-sided inequality [7]. Conditions are fixed truthful weights, independent bounded blocks and a prespecified sample plan. The companion two-sided 95% interval uses ln(40) in its radius. Human calibration, judge error and future-workload changes require separate treatment."),
        p('Fresh synthetic validation','h2'),
        table(['Scenario (2,000 experiments each)','Task bootstrap*','Two-sided block bound'],rows,[211,112,WIDTH-323]),Spacer(1,9),
        p('*Coverage of known fixed-registry expected credit. The bootstrap column probes the broader interpretation that caused the original failure. All 12,000 experiments are synthetic; one-sided IWU-L95 validity is reported separately in the machine-readable results.','small'),
        p('Valid coverage can require wide bounds. The fully dependent normalized case yields [0,1] and an IWU-L95 value of zero. A fixed-registry confidence statement concerns repeated sampling under its assumptions. Next-task acceptance, human-time accuracy and economic usefulness are additional targets for validation.','small'),PageBreak())
    add(p('5. Interpretation and next validation steps','h1'),
        p('The proposed contribution is a concrete reference-work accounting and evidence profile, a tested implementation and a transparent pilot. Its mathematical ingredients have established precedents. The profile is suitable for researcher review and independent implementation.'),p('Priority validation work','h2'),
        table(['Requirement','Evidence needed'],[
          ['Human calibration','Independently timed experts; accepted-quality equivalence; censoring policy; uncertainty for each weight.'],
          ['Measurement integrity','Provider-attested identity, trusted traces, replayable permitted evidence, reconciled bills and external audit.'],
          ['External validity','Fresh held-out tasks, realistic tool workflows, judge agreement studies, drift checks and independent harnesses.'],
          ['Comparability and adoption','Cross-registry linking studies, second implementations, open governance, licensing and community use.']], [126,WIDTH-126]),Spacer(1,11),
        p('Every published score should include its point estimate or missingness bounds, uncertainty target, sample counts, dependence structure, calibration status and evidence completeness. L95 depends on both evidence quantity and observed performance. Comparisons require a prespecified paired uncertainty procedure.'),p('Related work','h2'),
        p('Human-time evaluation [1], joint cost and accuracy analysis [2], item-response evaluation [3], human-time bridges [4], quality-adjusted prices [5] and existing telemetry conventions [6] inform this proposal. The standardization work concerns a shared accounting profile, its evidence requirements and validation process.'),p('References','h2'),
        p('[1] METR. <link href="https://arxiv.org/abs/2503.14499">Measuring AI Ability to Complete Long Tasks</link>. arXiv:2503.14499. Data: <link href="https://github.com/METR/eval-analysis-public">METR/eval-analysis-public</link>.','small'),
        p('[2] Kapoor et al. <link href="https://arxiv.org/abs/2407.01502">AI Agents That Matter</link>. arXiv:2407.01502.','small'),
        p('[3] Stanford CRFM. <link href="https://crfm.stanford.edu/2025/06/04/reliable-and-efficient-evaluation.html">Reliable and efficient evaluation using item-response methods</link> (2025).','small'),
        p('[4] <link href="https://arxiv.org/abs/2602.07267">BRIDGE</link>. arXiv:2602.07267. [5] <link href="https://arxiv.org/abs/2608.29843">The Price of Intelligence</link>. arXiv:2608.29843.','small'),
        p('[6] OpenTelemetry. <link href="https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/">Generative AI semantic conventions</link>.','small'),
        p('[7] Hoeffding (1963). <link href="https://www.tandfonline.com/doi/abs/10.1080/01621459.1963.10500830">Probability Inequalities for Sums of Bounded Random Variables</link>. JASA 58(301), 13-30.','small'),p('Research resources','h2'),
        p('The reference implementation, tests, methods and reproduction resources accompany this paper. Original code: MIT. Original research materials: CC BY 4.0. Swarm Research, maintained by blackscaletech. <link href="https://swarm.services">swarm.services</link>.','small'))
    doc.build(s,onFirstPage=chrome,onLaterPages=chrome)
    return dest


def main():
    register_fonts()
    print(make_pdf())

if __name__=='__main__':main()
