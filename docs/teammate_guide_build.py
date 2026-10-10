"""Build the 12-page teammate guide from the maintained Markdown source.

Requires reportlab (tested 5.0.1). From the repo root:
    python docs/teammate_guide_build.py
For visual QA, render the PDF with Poppler or PyMuPDF; see verification JSON.
No network, notebook execution, model loading or project-code mutation occurs.
"""
from pathlib import Path
import re
from html import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/teammate_guide.md'
OUTPUT = ROOT / 'output/pdf/Hinglish_Math_Teammate_Guide.pdf'
NAVY = colors.HexColor('#153148')
TEAL = colors.HexColor('#007C83')
GRAY = colors.HexColor('#52616E')
PALE = colors.HexColor('#EAF4F5')
WIDTH = A4[0] - 84
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='GuideBody', fontName='Helvetica', fontSize=9.7, leading=13.3, textColor=NAVY, spaceAfter=6))
styles.add(ParagraphStyle(name='GuideTitle', fontName='Helvetica-Bold', fontSize=21, leading=25, textColor=NAVY, spaceAfter=13))
styles.add(ParagraphStyle(name='GuideSub', fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=TEAL, spaceAfter=12))
styles.add(ParagraphStyle(name='GuideH3', fontName='Helvetica-Bold', fontSize=11.3, leading=14.5, textColor=TEAL, spaceBefore=5, spaceAfter=5))
styles.add(ParagraphStyle(name='GuideCell', fontName='Helvetica', fontSize=8.8, leading=11.9, textColor=NAVY, spaceAfter=0, wordWrap='CJK'))
styles.add(ParagraphStyle(name='GuideHeadCell', fontName='Helvetica-Bold', fontSize=8.8, leading=11.9, textColor=colors.white, spaceAfter=0))
styles.add(ParagraphStyle(name='GuideBullet', parent=styles['GuideBody'], leftIndent=12, firstLineIndent=-10, spaceAfter=5))
styles.add(ParagraphStyle(name='GuideCallout', fontName='Helvetica-Bold', fontSize=9.5, leading=13, textColor=NAVY))

def inline(text):
    text = escape(text)
    text = re.sub(r'`([^`]+)`', lambda m: '<font face="Courier" size="8.5">'+m.group(1)+'</font>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'(https://[^\s<]+)', lambda m: '<link href="'+m.group(1)+'" color="#007C83">'+m.group(1)+'</link>', text)
    return text

def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(TEAL)
    canvas.setLineWidth(.6)
    canvas.line(48, A4[1]-39, A4[0]-48, A4[1]-39)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(GRAY)
    canvas.drawString(48, A4[1]-29, 'DTU | HINGLISH MATHEMATICAL REASONING')
    canvas.drawRightString(A4[0]-48, A4[1]-29, 'TEAM GUIDE | 10 OCT 2026')
    canvas.drawString(48, 28, 'Software verified; research data and experiments pending human review.')
    canvas.drawRightString(A4[0]-48, 28, str(doc.page))
    canvas.restoreState()

def make_table(lines):
    rows = [[v.strip() for v in row.strip().strip('|').split('|')] for row in lines]
    rows = [r for r in rows if not all(re.fullmatch(r'[-: ]+', c) for c in r)]
    n = len(rows[0])
    if n == 3:
        sizes = [WIDTH*.24, WIDTH*.43, WIDTH*.33]
        # Wider middle/right when column 1 is a brief code or label.
        if rows[0][0] in ('Code','Arm'):
            sizes = [WIDTH*.12, WIDTH*.39, WIDTH*.49]
    else:
        sizes = [WIDTH*.40, WIDTH*.60]
    cells = [[Paragraph(inline(c), styles['GuideHeadCell' if i==0 else 'GuideCell']) for c in r] for i,r in enumerate(rows)]
    table = Table(cells, colWidths=sizes, repeatRows=1, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),NAVY),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#F2F6F8'),colors.white]),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),5.5),('BOTTOMPADDING',(0,0),(-1,-1),5.5),
        ('LINEBELOW',(0,0),(-1,0),.6,TEAL),('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#DDE5E9')),
    ]))
    return table

story=[]
lines=SOURCE.read_text(encoding='utf8').splitlines()
i=0
while i<len(lines):
    line=lines[i].strip()
    if not line:
        i+=1;continue
    if line=='<!-- PAGEBREAK -->':
        story.append(PageBreak());i+=1;continue
    if line.startswith('|'):
        block=[]
        while i<len(lines) and lines[i].strip().startswith('|'):
            block.append(lines[i]);i+=1
        story += [make_table(block),Spacer(1,10)];continue
    if line.startswith('> '):
        p=Paragraph(inline(line[2:]),styles['GuideCallout'])
        t=Table([[p]],colWidths=[WIDTH])
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('BOX',(0,0),(-1,-1),.6,TEAL),('LEFTPADDING',(0,0),(-1,-1),11),('RIGHTPADDING',(0,0),(-1,-1),11),('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9)]))
        story += [t,Spacer(1,12)];i+=1;continue
    for marker,sty in [('### ','GuideH3'),('## ','GuideSub'),('# ','GuideTitle')]:
        if line.startswith(marker):
            story.append(Paragraph(inline(line[len(marker):]),styles[sty]));break
    else:
        bullet=line.startswith('- ') or bool(re.match(r'\d+\. ',line))
        if line.startswith('- '):
            line='- '+line[2:]
        story.append(Paragraph(inline(line),styles['GuideBullet' if bullet else 'GuideBody']))
    i+=1
OUTPUT.parent.mkdir(parents=True,exist_ok=True)
doc=SimpleDocTemplate(str(OUTPUT),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=54,bottomMargin=43,invariant=1,title='Hinglish Mathematical Reasoning in LLMs - Teammate Guide',author='DTU project team',subject='Project status, pilot software and pending research review')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(OUTPUT)
