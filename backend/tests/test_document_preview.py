import asyncio
import base64
import io
import os
from unittest.mock import AsyncMock
import pytest
from PIL import Image
from cryptography.exceptions import InvalidTag
from fastapi import HTTPException
from web_document_preview import render, seal, unseal, MAX_PREVIEW
from web_workspace import stream_personal_document

def test_preview_is_small_encrypted_and_bound_to_owner(monkeypatch):
    monkeypatch.setenv('WEB_PERSONAL_ENCRYPTION_KEY_V1',base64.b64encode(os.urandom(32)).decode())
    raw=io.BytesIO();Image.new('RGB',(2400,1600),'white').save(raw,'PNG')
    thumb=render(raw.getvalue())
    assert len(thumb)<MAX_PREVIEW
    with Image.open(io.BytesIO(thumb)) as image: assert max(image.size)<=640
    row={'subject_id':'fake-owner','document_id':'fake-doc','sha256':'fake-hash'}
    encrypted=seal(thumb,row)
    assert thumb not in encrypted['data']
    assert unseal(encrypted,row)==thumb
    with pytest.raises(InvalidTag):unseal(encrypted,{**row,'subject_id':'other'})
    with pytest.raises(ValueError):unseal(encrypted,{**row,'sha256':'changed'})

@pytest.mark.parametrize('row,status',[(None,404),({'scan_state':'QUARANTINED'},409),({'scan_state':'CLEAN','dossier_state':'EXPIRED'},404)])
def test_preview_never_bypasses_document_access(row,status):
    db=AsyncMock();db.web_personal_documents.find_one.return_value=row
    with pytest.raises(HTTPException) as error:
        asyncio.run(stream_personal_document(db,'fake-owner','fake-doc','fake-owner',preview=True))
    assert error.value.status_code==status
    query=db.web_personal_documents.find_one.call_args.args[0]
    assert query['subject_id']=='fake-owner' and query['deleted']=={'$ne':True}

def test_cached_preview_avoids_original_download(monkeypatch):
    import web_workspace
    monkeypatch.setenv('WEB_PERSONAL_ENCRYPTION_KEY_V1',base64.b64encode(os.urandom(32)).decode())
    monkeypatch.setattr(web_workspace,'storage_ready',lambda:True)
    def forbidden(*args):raise AssertionError('Original must not be fetched for a cached preview')
    monkeypatch.setattr(web_workspace.web_personal_storage,'read',forbidden)
    row={'subject_id':'fake-owner','document_id':'fake-doc','sha256':'fake-hash','scan_state':'CLEAN'}
    row['private_preview']=seal(b'\xff\xd8fake-thumbnail',row)
    db=AsyncMock();db.web_personal_documents.find_one.return_value=row
    response=asyncio.run(stream_personal_document(db,'fake-owner','fake-doc','fake-owner',preview=True))
    assert response.media_type=='image/jpeg'
    assert response.headers['cache-control']=='private, no-store'
