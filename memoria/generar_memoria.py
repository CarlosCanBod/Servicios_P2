"""Genera la memoria PDF a partir del texto editable de memoria.md."""
from pathlib import Path
import html
import re
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, Flowable

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'memoria/memoria.md'
DEST=ROOT/'output/pdf/Memoria_P2.pdf'
FONT='/usr/share/fonts/truetype/dejavu/'
pdfmetrics.registerFont(TTFont('DejaVu',FONT+'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuBold',FONT+'DejaVuSans-Bold.ttf'))
pdfmetrics.registerFontFamily('DejaVu',normal='DejaVu',bold='DejaVuBold',italic='DejaVu',boldItalic='DejaVuBold')

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='TituloP2',fontName='DejaVuBold',fontSize=20,leading=26,textColor=colors.HexColor('#15364c'),spaceAfter=14))
styles.add(ParagraphStyle(name='SubtituloP2',fontName='DejaVu',fontSize=12,leading=18,textColor=colors.HexColor('#36566a'),spaceAfter=14))
styles.add(ParagraphStyle(name='SeccionP2',fontName='DejaVuBold',fontSize=13,leading=17,textColor=colors.HexColor('#163e57'),spaceBefore=13,spaceAfter=7,keepWithNext=True))
styles.add(ParagraphStyle(name='SubseccionP2',fontName='DejaVuBold',fontSize=10.5,leading=14,textColor=colors.HexColor('#23536c'),spaceBefore=9,spaceAfter=5,keepWithNext=True))
styles.add(ParagraphStyle(name='TextoP2',fontName='DejaVu',fontSize=10.0,leading=14.5,alignment=TA_JUSTIFY,spaceAfter=7,allowWidows=0,allowOrphans=0))
styles.add(ParagraphStyle(name='CeldaP2',fontName='DejaVu',fontSize=8.5,leading=12,spaceAfter=0))
styles.add(ParagraphStyle(name='CabezaP2',fontName='DejaVuBold',fontSize=8.5,leading=12,textColor=colors.white))
styles.add(ParagraphStyle(name='PieP2',fontName='DejaVu',fontSize=8.5,leading=11.7,textColor=colors.HexColor('#475b68'),spaceBefore=5,spaceAfter=9))


def markup(text):
    """Convertir los resaltados utilizados en el texto a marcado de ReportLab."""
    text=html.escape(text,quote=False)
    text=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',text)
    text=re.sub(r'`([^`]+)`',r'<font color="#174c67">\1</font>',text)
    return text


def paragraph(text,style='TextoP2'):
    return Paragraph(markup(text),styles[style])


def footer(canvas,doc):
    canvas.saveState()
    width,height=A4
    canvas.setStrokeColor(colors.HexColor('#c6d2d8'))
    canvas.line(doc.leftMargin,42,width-doc.rightMargin,42)
    canvas.setFont('DejaVu',7.5)
    canvas.setFillColor(colors.HexColor('#536875'))
    canvas.drawString(doc.leftMargin,29,'Robótica de Servicios · Práctica 2')
    canvas.drawRightString(width-doc.rightMargin,29,str(doc.page))
    canvas.restoreState()


class Esquema(Flowable):
    """Dibujos esquemáticos: representan la regla, no una medición de una persona."""
    def __init__(self,kind,width):
        Flowable.__init__(self); self.kind=kind; self.width=width
        self.height={'cara':154,'ojo':144,'estados':142}[kind]

    def draw(self):
        c=self.canv; w=self.width
        blue=colors.HexColor('#24536b'); green=colors.HexColor('#287a69')
        c.setFillColor(colors.HexColor('#f3f7f9')); c.setStrokeColor(colors.HexColor('#d5e1e6'))
        c.roundRect(0,0,w,self.height,7,fill=1,stroke=1)

        def label(x,y,text,size=8,color=blue):
            c.setFont('DejaVu',size); c.setFillColor(color); c.drawString(x,y,text)

        def point(x,y):
            c.setFillColor(blue); c.circle(x,y,3,stroke=0,fill=1)

        def arrow(x1,y1,x2,y2,color=blue):
            import math
            c.setStrokeColor(color); c.setFillColor(color); c.setLineWidth(1.1)
            c.line(x1,y1,x2,y2)
            a=math.atan2(y2-y1,x2-x1); length=5
            path=c.beginPath(); path.moveTo(x2,y2)
            path.lineTo(x2-length*math.cos(a-.5),y2-length*math.sin(a-.5))
            path.lineTo(x2-length*math.cos(a+.5),y2-length*math.sin(a+.5)); path.close()
            c.drawPath(path,stroke=0,fill=1)

        if self.kind=='cara':
            mid=w/2
            c.setFillColor(colors.white); c.setStrokeColor(colors.HexColor('#7e9aa8'))
            c.ellipse(mid-53,17,mid+53,139,stroke=1,fill=1)
            a=(mid-25,101); b=(mid+25,101); nose=(mid,74); mouth=(mid,49)
            ear1=(mid-54,78); ear2=(mid+54,78)
            for x,y in (a,b,nose,mouth,ear1,ear2): point(x,y)
            c.setStrokeColor(colors.HexColor('#6f9aaa')); c.setDash(3,3)
            c.line(a[0],a[1],b[0],b[1]); c.setDash()
            arrow(a[0]+4,a[1],b[0]-5,b[1],blue); label(mid-15,112,'u',8,blue)
            arrow(mid,98,mid,54,green); label(mid+5,84,'v',8,green)
            label(32,118,'Ojo A'); c.line(72,119,a[0]-3,a[1]+3)
            label(w-91,118,'Ojo B'); c.line(w-93,119,b[0]+3,b[1]+3)
            label(32,80,'Oreja A'); c.line(74,81,ear1[0]-4,ear1[1])
            label(w-91,80,'Oreja B'); c.line(w-93,81,ear2[0]+4,ear2[1])
            label(w-91,57,'Nariz'); c.line(w-93,60,nose[0]+3,nose[1]-2)
            label(w-91,33,'Boca'); c.line(w-93,37,mouth[0]+3,mouth[1]-2)
            label(32,32,'C: punto medio entre ojos',8)
            point(mid,101); label(mid+5,105,'C',7)
        elif self.kind=='ojo':
            mid=w/2; left=mid-112; right=mid+112; cy=83
            c.setFillColor(colors.white); c.setStrokeColor(colors.HexColor('#7e9aa8'))
            path=c.beginPath(); path.moveTo(left,cy)
            path.curveTo(mid-65,cy+46,mid+65,cy+46,right,cy)
            path.curveTo(mid+65,cy-46,mid-65,cy-46,left,cy); path.close()
            c.drawPath(path,stroke=1,fill=1)
            c.setFillColor(colors.HexColor('#d5e8ee')); c.circle(mid,cy,15,stroke=0,fill=1)
            c.setFillColor(blue); c.circle(mid,cy,4,stroke=0,fill=1)
            for x,y in ((left,cy),(right,cy),(mid-42,cy+27),(mid+42,cy+27),(mid-42,cy-27),(mid+42,cy-27)): point(x,y)
            for x,name in ((mid-42,'h1'),(mid+42,'h2')):
                arrow(x,cy-24,x,cy+24,green); arrow(x,cy+24,x,cy-24,green)
                label(x+5,cy-2,name,8,green)
            arrow(left,27,right,27,blue); arrow(right,27,left,27,blue)
            label(mid-7,13,'w',9); label(mid+20,cy+4,'iris',8)
        else:
            boxes=[('Inicial',),('Ligeramente','molesto'),('Claramente','molesto'),('Final malo',)]
            margin=5; gap=22; bw=(w-2*margin-3*gap)/4; y=91; bh=38
            for i,parts in enumerate(boxes):
                x=margin+i*(bw+gap)
                c.setFillColor(colors.white); c.setStrokeColor(blue); c.roundRect(x,y,bw,bh,4,stroke=1,fill=1)
                c.setFillColor(blue); c.setFont('DejaVuBold',7.6)
                for j,part in enumerate(parts):
                    c.drawCentredString(x+bw/2,y+21-(j*11) if len(parts)>1 else y+15,part)
            for i,t in enumerate(('4 s','6 s','8 s')):
                x=margin+i*(bw+gap)+bw; arrow(x,y+22,x+gap,y+22)
                c.setFont('DejaVu',7); c.setFillColor(blue); c.drawCentredString(x+gap/2,y+30,t)
            for i in (0,1):
                x=margin+i*(bw+gap)+bw
                c.setStrokeColor(green); c.line(x,y,x,y-7); c.line(x+gap,y,x+gap,y-7)
                arrow(x+gap,y-7,x,y-7,green)
                c.setFont('DejaVu',7); c.setFillColor(green); c.drawCentredString(x+gap/2,y-18,'1 s')
            label(16,39,'Desatención: avanza hacia el aviso siguiente.',8)
            label(16,22,'Atención estable: recupera un nivel cada 1 s.',8,green)
            label(16,7,'Describimos el chiste, el descanso y el final bueno en la tabla 2.',7.5)


def main():
    DEST.parent.mkdir(parents=True,exist_ok=True)
    doc=SimpleDocTemplate(str(DEST),pagesize=A4,leftMargin=52,rightMargin=52,topMargin=48,bottomMargin=58,
                          title='Práctica 2: Tutor visual',author='Alejandro Lavandeira Casais; Carlos Adrián Cancela Bodlak; Yago Martínez Pena')
    lines=SOURCE.read_text(encoding='utf-8').splitlines()
    story=[]; i=0; first_intro=True
    while i<len(lines):
        line=lines[i].strip()
        if not line: i+=1; continue
        if line.startswith('[[FIGURA_'):
            kind={'[[FIGURA_CARA]]':'cara','[[FIGURA_OJO]]':'ojo','[[FIGURA_ESTADOS]]':'estados'}[line]
            i+=1
            while i<len(lines) and not lines[i].strip(): i+=1
            if i>=len(lines) or not lines[i].strip().startswith('*Figura '):
                raise ValueError(f'La figura {kind} no tiene pie')
            caption=paragraph(lines[i].strip().strip('*'),'PieP2'); i+=1
            story.append(KeepTogether([Esquema(kind,doc.width),caption])); continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                parts=[x.strip() for x in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-{3,}:?',p) for p in parts): rows.append(parts)
                i+=1
            columns=len(rows[0]); ratios=([.26,.74] if columns==2 else [.32,.29,.39])
            widths=[doc.width*r for r in ratios]
            wrapped=[[paragraph(cell,'CabezaP2' if row_no==0 else 'CeldaP2') for cell in row] for row_no,row in enumerate(rows)]
            state_rows=(rows[0]==['Estado','Entrada','Salidas y condiciones'])
            # Si se divide la tabla de estados, conservar al menos dos estados
            # en la página siguiente, junto a la cabecera repetida.
            split_range=(1,len(rows)-2) if state_rows else None
            table=Table(wrapped,colWidths=widths,repeatRows=1,hAlign='LEFT',rowSplitRange=split_range)
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#24536b')),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#f1f5f7'),colors.white]),
                ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
                ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
                ('LINEBELOW',(0,-1),(-1,-1),.4,colors.HexColor('#a7bbc6'))]))
            while i<len(lines) and not lines[i].strip(): i+=1
            caption=None
            caption_line=''
            if i<len(lines) and lines[i].strip().startswith('*Tabla '):
                caption_line=lines[i].strip().strip('*')
                caption=paragraph(caption_line,'PieP2'); i+=1
            if caption_line.startswith('Tabla 2.'):
                # La tabla de estados es extensa: se puede dividir entre páginas
                # conservando la cabecera, con el pie al terminar la tabla.
                story.append(table)
                story.append(caption)
            else:
                story.append(KeepTogether([table,caption] if caption else [table]))
            continue
        if line.startswith('# '): story.append(paragraph(line[2:],'TituloP2')); i+=1; continue
        if line.startswith('## '): story.append(paragraph(line[3:],'SeccionP2')); i+=1; continue
        if line.startswith('### '): story.append(paragraph(line[4:],'SubseccionP2')); i+=1; continue
        if first_intro:
            story.append(paragraph(line,'SubtituloP2')); first_intro=False; i+=1; continue
        if line.startswith('Alejandro Lavandeira Casais'):
            authors=[]
            for _ in range(3): authors.append(lines[i].strip()); i+=1
            story.append(Paragraph('<br/>'.join(markup(a) for a in authors),styles['TextoP2']))
            story.append(Spacer(1,10)); continue
        chunks=[line]; i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].lstrip().startswith(('# ','## ','### ','|')):
            chunks.append(lines[i].strip()); i+=1
        story.append(paragraph(' '.join(chunks)))
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print(DEST)

if __name__=='__main__': main()
