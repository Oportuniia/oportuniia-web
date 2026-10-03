"""Premium-formatted, non-binding commercial offer preview.

This is NOT the legally approved reservation, an electronic signature, or a
submission to the supplier/CRM. PDF contains only public property fields and
applicant data explicitly reviewed in the browser. Independently verified
server-side offer/published-item scope must be checked before calling.
"""
from __future__ import annotations
from decimal import Decimal
from io import BytesIO
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

NAVY=colors.HexColor("#0B1B2C")
BRAND=colors.HexColor("#1E729A")
MUTED=colors.HexColor("#506878")

def _clean(s,limit=180):
    if not isinstance(s,str) or not 1<=len(s.strip())<=limit or any(ord(ch)<32 for ch in s):
        raise ValueError("Dato de oferta incompleto o inválido")
    return re.sub(r"\\s+"," ",s.strip())

def _line(c,label,value,y):
    c.setFont("Helvetica",9)
    c.setFillColor(MUTED)
    c.drawString(46,y,label)
    c.setFont("Helvetica",11)
    c.setFillColor(NAVY)
    from reportlab.lib.utils import simpleSplit
    for line in simpleSplit(value,"Helvetica",11,480):
        y-=16
        c.drawString(46,y,line)
    return y-24

def make_offer_preview_pdf(*,reference,property_title,property_city,applicant_name,
                           tax_identifier,email,amount_eur,notes=""):
    """Render a clearly labeled draft; every value is passed from reviewed data."""
    reference=_clean(reference,20)
    if not re.fullmatch(r"OP[0-9]{4,10}",reference):
        raise ValueError("Referencia inválida")
    amount=Decimal(str(amount_eur))
    if not amount.is_finite() or not Decimal("0")<amount<Decimal("100000000000"):
        raise ValueError("Importe de oferta inválido")
    property_title=_clean(property_title,140)
    property_city=_clean(property_city,150) if property_city else "No indicado"
    applicant_name=_clean(applicant_name,140)
    tax_identifier=_clean(tax_identifier,30)
    email=_clean(email,254)
    if notes and (len(notes)>1200 or any(ord(ch)<32 and ch not in "\\n\\t" for ch in notes)):
        raise ValueError("Observaciones no admitidas")
    stream=BytesIO()
    c=Canvas(stream,pagesize=A4,pageCompression=1)
    c.setTitle("Borrador de oferta OPORTUNIIA - "+reference)
    c.setAuthor("OPORTUNIIA")
    c.setFillColor(NAVY)
    c.rect(0,744,595,98,stroke=0,fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold",22)
    c.drawString(45,787,"OPORTUNIIA")
    c.setFont("Helvetica",10)
    c.drawString(45,767,"HUMANIZAMOS LA DEUDA")
    c.setFillColor(BRAND)
    c.setFont("Helvetica-Bold",12)
    c.drawString(46,704,"PROPUESTA COMERCIAL · BORRADOR")
    y=663
    for label,value in (
      ("Referencia pública",reference),("Oportunidad",property_title),
      ("Localidad",property_city),("Nombre / razón social declarado",applicant_name),
      ("Identificación declarada",tax_identifier),("Correo de la cuenta WEB",email),
      ("Importe propuesto",f"{amount:,.2f} EUR"),
    ):
        y=_line(c,label,value,y)
    if notes:
        y=_line(c,"Observaciones declaradas",notes.replace("\\n"," "),y-3)
    if y<140:
        c.showPage()
        y=755
    c.setStrokeColor(BRAND)
    c.line(45,y,548,y)
    c.setFont("Helvetica-Bold",10)
    c.setFillColor(NAVY)
    c.drawString(46,y-22,"REVISIÓN Y ENVÍO PENDIENTES")
    from reportlab.lib.utils import simpleSplit
    terms=("Documento informativo no vinculante. No representa oferta presentada, "
           "aceptación, firma, adjudicación ni reserva. Los datos declarados "
           "y la referencia requieren comprobación antes de su envío formal.")
    c.setFont("Helvetica",9)
    for i,line in enumerate(simpleSplit(terms,"Helvetica",9,492)):
        c.drawString(46,y-41-i*13,line)
    c.setFont("Helvetica",8)
    c.setFillColor(MUTED)
    c.drawString(46,32,"MI OPORTUNIIA · Copia para revisión personal")
    c.save()
    return stream.getvalue()
