"""Bounded OCR subprocess. Only CLEAN, integrity-checked bytes enter this process.
No network document transmission, no raw OCR text in logs or persistent output.
"""
import base64
import io
import json
import re
import sys
import unicodedata
from datetime import date

def norm(value):
    return re.sub(r'[^A-Z0-9]', '', ''.join(c for c in unicodedata.normalize('NFKD', str(value).upper()) if not unicodedata.combining(c)))

def evaluate_text(text, confidence, profile):
    compact=norm(text)
    company=profile.get('subject_type')=='PJ'
    identity=bool(re.search(r'DOCUMENTO\s+NACIONAL|IDENTITY\s+CARD|IDESP|\bDNI\b',text,re.I))
    fiscal=bool(re.search(r'IDENTIFICACI[ÓO]N\s+FISCAL|NIF\s+(?:DEFINITIVO|PROVISIONAL)|AGENCIA\s+TRIBUTARIA',text,re.I))
    name=profile.get('representative' if company else 'full_name','')
    number=norm(profile.get('representative_id' if company else 'tax_id',''))
    tokens=re.findall(r'[A-Z]+',unicodedata.normalize('NFKD',name.upper()).encode('ascii','ignore').decode())
    upper=unicodedata.normalize('NFKD',text.upper()).encode('ascii','ignore').decode()
    mrz=re.search(r'(?:^|\n)\s*([A-Z]+(?:<[A-Z]+)*)<<([A-Z]+(?:<[A-Z]+)*)',upper)
    detected=[]
    if mrz:detected=re.findall(r'[A-Z]+',mrz[1]+' '+mrz[2])
    else:
        for label in ('NOMBRE','APELLIDOS'):
            m=re.search(r'(?:^|\n)\s*'+label+r'(?:\s*/\s*[A-Z ]+)?\s*[:.]?\s*\n\s*([A-Z ]+)(?=\n|$)',upper)
            if m:detected.extend(m[1].split())
    name_matches=len(tokens)>=2 and sorted(tokens)==sorted(detected)
    valid_number=False
    if re.fullmatch(r'\d{8}[A-Z]',number):
        valid_number='TRWAGMYFPDXBNJZSQVHLCKE'[int(number[:8])%23]==number[-1]
    elif re.fullmatch(r'[XYZ]\d{7}[A-Z]',number):
        valid_number='TRWAGMYFPDXBNJZSQVHLCKE'[int(str('XYZ'.index(number[0]))+number[1:8])%23]==number[-1]
    expiry=False
    # Explicit expiry labels only: never infer validity from an arbitrary date.
    m=re.search(r'(?:VALIDEZ|CADUCIDAD|EXPIRY|VALIDITY)[^\d]{0,35}(\d{2})[ ./-](\d{2})[ ./-](\d{4})',text,re.I)
    if m:
        try:expiry=date(int(m[3]),int(m[2]),int(m[1]))>=date.today()
        except ValueError:pass
    birth=profile.get('birth_date','')
    try:
        b=date.fromisoformat(birth);birth_matches=any(v in compact for v in (b.strftime('%d%m%Y'),b.strftime('%Y%m%d'),b.strftime('%y%m%d')))
    except ValueError:birth_matches=False
    company_number=norm(profile.get('company_tax_id',''))
    company_name=norm(profile.get('company_name',''))
    fictitious=bool(re.search(r'FICTICIO|SIN\s+VALIDEZ|SPECIMEN|\bSAMPLE\b',text,re.I))
    observed_ids=set(re.findall(r'\b(?:\d{8}|[XYZ]\d{7})[A-Z]\b',upper))
    return {'reader_version':1,'confidence':round(float(confidence),3),'legible':len(compact)>=40 and confidence>=.8,
        'identity':identity,'fiscal':fiscal,'name_matches':name_matches,'number_matches':valid_number and observed_ids=={number},
        'birth_matches':birth_matches if not company else True,'expiry_read_and_valid':expiry,
        'company_matches':bool(company_number and company_name and company_number in compact and company_name in compact),
        'fictitious':fictitious}

def read_bytes(data,profile):
    import numpy as np
    from PIL import Image
    from rapidocr import RapidOCR
    engine=RapidOCR(params={'Global.log_level':'error','Global.max_side_len':1800,
        'EngineConfig.onnxruntime.intra_op_num_threads':1,'EngineConfig.onnxruntime.inter_op_num_threads':1})
    texts=[];scores=[]
    def scan(image):
        image.thumbnail((1800,1800));result=engine(np.array(image.convert('RGB')))
        texts.extend(result.txts or []);scores.extend(float(s) for s in (result.scores or []))
    if data.startswith(b'%PDF-'):
        import pypdfium2 as pdfium
        with pdfium.PdfDocument(data) as pdf:
            if len(pdf)>10:raise ValueError('page_limit')
            for page in pdf:
                scale=min(2,1800/max(page.get_size()))
                bitmap=page.render(scale=scale);scan(bitmap.to_pil());bitmap.close();page.close()
    else:
        with Image.open(io.BytesIO(data)) as image:
            if image.width*image.height>18_000_000:raise ValueError('pixel_limit')
            scan(image)
    return evaluate_text('\n'.join(texts),sum(scores)/len(scores) if scores else 0,profile)

if __name__=='__main__':
    payload=json.loads(sys.stdin.buffer.read(30*1024*1024))
    raw=base64.b64decode(payload['data'],validate=True)
    if len(raw)>20*1024*1024:raise ValueError('byte_limit')
    print(json.dumps(read_bytes(raw,payload['profile'])))
