"""Small encrypted first-page previews. Originals remain unchanged."""
import io
import os
import subprocess
import sys
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from web_personal_storage import encryption_key, key_id

MAX_PREVIEW = 96 * 1024

def render(data):
    from PIL import Image, ImageOps
    if data.startswith(b'%PDF-'):
        import pypdfium2 as pdfium
        with pdfium.PdfDocument(data) as pdf:
            if not 0 < len(pdf) <= 200: raise ValueError('page_limit')
            page = pdf[0]
            bitmap = page.render(scale=min(1, 640/max(page.get_size())))
            image = bitmap.to_pil().copy()
            bitmap.close(); page.close()
    else:
        image = Image.open(io.BytesIO(data))
        if image.width * image.height > 18_000_000: raise ValueError('pixel_limit')
        image = ImageOps.exif_transpose(image)
    image.thumbnail((640, 640))
    image = image.convert('RGB')
    out = io.BytesIO(); image.save(out, 'JPEG', quality=65, optimize=True)
    raw = out.getvalue()
    if len(raw) > MAX_PREVIEW: raise ValueError('preview_limit')
    return raw

def aad(row):
    return ('OPPORTUNIIA_PREVIEW_V1\0'+row['subject_id']+'\0'+row['document_id']+'\0'+row['sha256']).encode()

def seal(raw, row):
    if not raw.startswith(b'\xff\xd8') or len(raw)>MAX_PREVIEW: raise ValueError('invalid_preview')
    version=key_id(); nonce=os.urandom(12)
    return {'key_id':version,'sha256':row['sha256'],'data':nonce+AESGCM(encryption_key(version)).encrypt(nonce,raw,aad(row))}

def unseal(value, row):
    if value['sha256']!=row['sha256']: raise ValueError('preview_version_changed')
    data=bytes(value['data'])
    if not 28 < len(data) <= MAX_PREVIEW+28: raise ValueError('invalid_preview')
    return AESGCM(encryption_key(value['key_id'])).decrypt(data[:12],data[12:],aad(row))

def prepare(data, row):
    # Separate bounded process; no file is parsed before CLEAN + integrity checks.
    result=subprocess.run([sys.executable,str(Path(__file__))],input=data,
        stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=30,check=True)
    return seal(result.stdout,row)

if __name__=='__main__':
    data=sys.stdin.buffer.read(20*1024*1024+1)
    if len(data)>20*1024*1024: raise ValueError('byte_limit')
    sys.stdout.buffer.write(render(data))
