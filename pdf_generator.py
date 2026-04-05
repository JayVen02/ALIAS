from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io

PAGE = landscape(A4)
W, H = PAGE

def generate_physical_count_pdf(category_name, as_of_date, accountable_person,
                                  position, department, items):
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer, pagesize=PAGE,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=12*mm, bottomMargin=12*mm
    )

    title_s  = ParagraphStyle('t',  fontName='Times-Bold',   fontSize=11, alignment=TA_CENTER, leading=14)
    sub_s    = ParagraphStyle('s',  fontName='Times-Roman',  fontSize=10, alignment=TA_CENTER, leading=13)
    acct_s   = ParagraphStyle('a',  fontName='Times-Roman',  fontSize=8.5, leading=11)
    th_s     = ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=7.5, alignment=TA_CENTER, leading=9)
    td_s     = ParagraphStyle('td', fontName='Helvetica',    fontSize=7.5, alignment=TA_CENTER, leading=9)
    td_l_s   = ParagraphStyle('tl', fontName='Helvetica',    fontSize=7.5, alignment=TA_LEFT,   leading=9)
    sig_s    = ParagraphStyle('sg', fontName='Times-Roman',  fontSize=8,   alignment=TA_CENTER, leading=10)
    sig_b_s  = ParagraphStyle('sb', fontName='Times-Bold',   fontSize=8.5, alignment=TA_CENTER, leading=10)

    def P(txt, sty): return Paragraph(str(txt), sty)

    story = []
    story.append(P("REPORT ON THE PHYSICAL COUNT OF PROPERTY, PLANT AND EQUIPMENT", title_s))
    story.append(P(category_name.upper(), title_s))
    story.append(P(f"As of {as_of_date}", sub_s))
    story.append(Spacer(1, 6*mm))

    acct_line = (
        f'For which &nbsp;&nbsp; <u><b>{accountable_person}</b></u>, &nbsp;&nbsp; '
        f'<u><b>{position}</b></u>, &nbsp;&nbsp; <u><b>{department}</b></u>'
        f' &nbsp;&nbsp; is accountable, having assumed such accountability on ___________'
    )
    story.append(P(acct_line, acct_s))
    story.append(Spacer(1, 5*mm))

    header1 = [
        P('Article', th_s), P('Description', th_s), P('Property no.', th_s),
        P('Unit\nMeasure', th_s), P('Unit\nvalue', th_s),
        P('Quantity per\nProperty Card', th_s), P('Quantity per\nPhysical Count', th_s),
        P('Shortage/Overage', th_s), '', P('Remarks', th_s),
    ]
    header2 = ['', '', '', '', '', '', '', P('Quantity', th_s), P('Value', th_s), '']

    tbl_data = [header1, header2]

    for item in items:
        try:
            qc   = float(item.get('qty_card', 0)   or 0)
            qp   = float(item.get('qty_physical', 0) or 0)
            uv   = float(item.get('unit_value', 0)  or 0)
            diff = qp - qc
            val  = diff * uv
            s_q  = (f'+{diff:.0f}' if diff > 0 else f'{diff:.0f}') if item.get('qty_physical', '') != '' else ''
            s_v  = (f'+{val:,.2f}' if val > 0 else f'{val:,.2f}') if item.get('qty_physical', '') != '' else ''
            uv_s = f"{uv:,.2f}" if uv else ''
        except:
            s_q = s_v = uv_s = ''

        tbl_data.append([
            P(item.get('article', ''),      td_l_s),
            P(item.get('description', ''),  td_l_s),
            P(item.get('property_no', ''),  td_s),
            P(item.get('unit_measure', ''), td_s),
            P(uv_s,                         td_s),
            P(str(item.get('qty_card', '')), td_s),
            P(str(item.get('qty_physical', '')), td_s),
            P(s_q,                          td_s),
            P(s_v,                          td_s),
            P(item.get('remarks', ''),      td_l_s),
        ])

    BLUE  = colors.HexColor('#31449b')
    LGRAY = colors.HexColor('#f5f6fc')

    col_w = [28*mm, 62*mm, 26*mm, 18*mm, 22*mm, 24*mm, 24*mm, 20*mm, 22*mm, 30*mm]

    tbl = Table(tbl_data, colWidths=col_w, repeatRows=2)
    tbl.setStyle(TableStyle([
        ('SPAN',          (0,0),(0,1)),  ('SPAN',(1,0),(1,1)), ('SPAN',(2,0),(2,1)),
        ('SPAN',          (3,0),(3,1)),  ('SPAN',(4,0),(4,1)), ('SPAN',(5,0),(5,1)),
        ('SPAN',          (6,0),(6,1)),  ('SPAN',(7,0),(8,0)), ('SPAN',(9,0),(9,1)),
        ('BACKGROUND',    (0,0),(-1,1),  BLUE),
        ('TEXTCOLOR',     (0,0),(-1,1),  colors.white),
        ('ROWBACKGROUNDS',(0,2),(-1,-1), [colors.white, LGRAY]),
        ('GRID',          (0,0),(-1,-1), 0.4, colors.HexColor('#c0c8e8')),
        ('BOX',           (0,0),(-1,-1), 0.8, BLUE),
        ('LINEBELOW',     (0,1),(-1,1),  0.8, BLUE),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('ALIGN',         (0,0),(-1,1),  'CENTER'),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 3),
        ('RIGHTPADDING',  (0,0),(-1,-1), 3),
    ]))

    story.append(tbl)
    story.append(Spacer(1, 8*mm))

    sig_data = [
        [P('Certified Correct by:', sig_s), P('Approved by:', sig_s),
         P('Verified by:', sig_s),          P('', sig_s)],
        [Spacer(1,12*mm), Spacer(1,12*mm), Spacer(1,12*mm), Spacer(1,12*mm)],
        [P('<u>PAUL ROGER P. NERI</u>', sig_b_s), P('<u>EMMANNUEL. JAMIS, DVM</u>', sig_b_s),
         P('', sig_b_s), P('', sig_b_s)],
        [P('GSO-Designate<br/>Inventory Chair Committee', sig_s),
         P('Municipal Mayor', sig_s),
         P('_______________________________<br/>COA Representative', sig_s),
         P('', sig_s)],
    ]

    sig_tbl = Table(sig_data, colWidths=[(W-30*mm)/4]*4)
    sig_tbl.setStyle(TableStyle([
        ('VALIGN',       (0,0),(-1,-1),'TOP'),
        ('ALIGN',        (0,0),(-1,-1),'CENTER'),
        ('TOPPADDING',   (0,0),(-1,-1), 2),
        ('BOTTOMPADDING',(0,0),(-1,-1), 2),
    ]))
    story.append(sig_tbl)

    doc.build(story)
    buffer.seek(0)
    return buffer