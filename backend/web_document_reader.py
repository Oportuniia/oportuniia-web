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

READER_VERSION = 5

def norm(value):
    return re.sub(r'[^A-Z0-9]', '', ''.join(c for c in unicodedata.normalize('NFKD', str(value).upper()) if not unicodedata.combining(c)))

def mrz_expiry(text, birth):
    # TD1 expiry has a defined position and its own check digit. Never guess a date.
    def check(value):
        return str(sum((int(c) if c.isdigit() else ord(c)-55 if c.isalpha() else 0)*[7,3,1][i%3] for i,c in enumerate(value))%10)
    try: expected=date.fromisoformat(birth).strftime('%y%m%d')
    except (ValueError,TypeError): return False
    for line in text.upper().splitlines():
        line=re.sub(r'\s','',line)
        if not re.fullmatch(r'\d{7}[MF<]\d{7}[A-Z]{3}[A-Z0-9<]{11}\d',line):continue
        if line[:6]!=expected or check(line[:6])!=line[6] or check(line[8:14])!=line[14]:continue
        try:
            yy,mm,dd=int(line[8:10]),int(line[10:12]),int(line[12:14])
            today=date.today()
            candidates=[date(c+yy,mm,dd) for c in (1900,2000,2100)]
            if any(today<=v and (v-today).days<=20*366 for v in candidates):return True
        except ValueError:continue
    return False

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
            m=re.search(r'(?:^|\n)[ \t]*'+label+r'(?:[ \t]*/[ \t]*[A-Z]+)*[ \t]*[:.]?[ \t]*(?:\n[ \t]*)?([A-Z][A-Z \t]+)(?=\n|$)',upper)
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
    if not expiry and not company:expiry=mrz_expiry(text,birth)
    try:
        b=date.fromisoformat(birth);birth_matches=any(v in compact for v in (b.strftime('%d%m%Y'),b.strftime('%Y%m%d'),b.strftime('%y%m%d')))
    except ValueError:birth_matches=False
    company_number=norm(profile.get('company_tax_id',''))
    company_name=norm(profile.get('company_name',''))
    fictitious=bool(re.search(r'FICTICIO|SIN\s+VALIDEZ|SPECIMEN|\bSAMPLE\b',text,re.I))
    observed_ids={norm(v) for v in re.findall(r'\b(?:\d{8}|[XYZ]\d{7})[ \t]*[A-Z]\b',upper)}
    return {'reader_version':READER_VERSION,'confidence':round(float(confidence),3),'legible':len(compact)>=40 and confidence>=.8,
        'identity':identity,'fiscal':fiscal,'name_matches':name_matches,'number_matches':valid_number and observed_ids=={number},
        'birth_matches':birth_matches if not company else True,'expiry_read_and_valid':expiry,
        'company_matches':bool(company_number and company_name and company_number in compact and company_name in compact),
        'fictitious':fictitious}

def create_engine():
    from rapidocr import RapidOCR, ModelType, OCRVersion, LangRec
    # Pin compact models: upstream defaults may change to a larger model.
    # One crop at a time prevents a batch of long lines exhausting WEB memory.
    return RapidOCR(params={'Global.log_level':'error','Global.max_side_len':1800,
        'Det.model_type':ModelType.MOBILE,'Det.ocr_version':OCRVersion.PPOCRV4,
        'Det.limit_side_len':960,'Det.limit_type':'max',
        'Rec.model_type':ModelType.MOBILE,'Rec.ocr_version':OCRVersion.PPOCRV5,
        'Rec.lang_type':LangRec.LATIN,'Rec.rec_batch_num':1,'Cls.cls_batch_num':1,
        'EngineConfig.onnxruntime.enable_cpu_mem_arena':False,
        'EngineConfig.onnxruntime.intra_op_num_threads':1,'EngineConfig.onnxruntime.inter_op_num_threads':1})

def read_bytes(data,profile):
    import cv2
    cv2.setNumThreads(1)
    import numpy as np
    from PIL import Image
    engine=create_engine()
    texts=[];scores=[];alternatives=[]
    def scan(image):
        image.thumbnail((1800,1800));result=engine(np.array(image.convert('RGB')))
        texts.extend(result.txts or []);scores.extend(float(s) for s in (result.scores or []))
        return result
    if data.startswith(b'%PDF-'):
        import pypdfium2 as pdfium
        with pdfium.PdfDocument(data) as pdf:
            if len(pdf)>10:raise ValueError('page_limit')
            for page in pdf:
                width,height=page.get_size()
                bitmap=page.render(scale=min(2,1800/max(width,height)),limit_image_cache=True)
                image=bitmap.to_pil();scan(image);image.close();bitmap.close()
                if len(pdf)<=2:
                    for crop in ((0,0,width/2,0),(width/2,0,0,0)):
                        bitmap=page.render(scale=min(2,1800/max(width/2,height)),crop=crop,limit_image_cache=True)
                        image=bitmap.to_pil();result=scan(image)
                        alternatives.append(evaluate_text('\n'.join(result.txts or []),sum(result.scores)/len(result.scores) if result.scores is not None and len(result.scores) else 0,profile))
                        del result
                        image.close();bitmap.close()
                page.close()
    else:
        with Image.open(io.BytesIO(data)) as image:
            if image.width*image.height>18_000_000:raise ValueError('pixel_limit')
            scan(image)
    main=evaluate_text('\n'.join(texts),sum(scores)/len(scores) if scores else 0,profile)
    for candidate in alternatives:
        if all(candidate.get(k) for k in ('legible','identity','name_matches','number_matches','birth_matches','expiry_read_and_valid')) and not main.get('fictitious'):
            return candidate
    return main

if __name__=='__main__':
    payload=json.loads(sys.stdin.buffer.read(30*1024*1024))
    raw=base64.b64decode(payload['data'],validate=True)
    if len(raw)>20*1024*1024:raise ValueError('byte_limit')
    print(json.dumps(read_bytes(raw,payload['profile'])))
