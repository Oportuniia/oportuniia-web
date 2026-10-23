import base64
import hashlib
import io
import os
import pytest
from cryptography.exceptions import InvalidTag
import web_personal_storage as storage


@pytest.fixture
def configured(monkeypatch):
    for name, value in {'WEB_PERSONAL_STORAGE_BACKEND': 'r2-aesgcm', 'WEB_PERSONAL_UPLOADS_ENABLED': 'true',
                        'WEB_PERSONAL_BUCKET': 'private-test', 'WEB_PERSONAL_R2_ENDPOINT': 'https://test.invalid',
                        'WEB_PERSONAL_R2_ACCESS_KEY_ID': 'fake', 'WEB_PERSONAL_R2_SECRET_ACCESS_KEY': 'fake',
                        'WEB_PERSONAL_ENCRYPTION_KEY_V1': base64.b64encode(os.urandom(32)).decode()}.items():
        monkeypatch.setenv(name, value)
    return dict(subject_id='person-a', document_id='doc-1', storage_key='web-personal/quarantine/person-a/doc-1',
                mime='application/pdf', sha256=hashlib.sha256(b'%PDF-fictitious').hexdigest())


def test_r2_stores_only_ciphertext_and_roundtrip(configured, monkeypatch):
    saved = {}
    class Fake:
        def put_object(self, **kwargs): saved.update(kwargs)
        def get_object(self, **kwargs): return {'Body': io.BytesIO(saved['Body'])}
    monkeypatch.setattr(storage, 'client', lambda *args: Fake())
    storage.write(b'%PDF-fictitious', configured)
    assert saved['Body'] != b'%PDF-fictitious'
    assert b'%PDF-fictitious' not in saved['Body']
    assert saved['ContentType'] == 'application/octet-stream'
    assert storage.read(configured) == b'%PDF-fictitious'
    with pytest.raises(InvalidTag): storage.read({**configured, 'subject_id': 'person-b'})
    saved['Body'] = saved['Body'][:-1] + bytes([saved['Body'][-1] ^ 1])
    with pytest.raises(InvalidTag): storage.read(configured)


def test_storage_fails_closed_without_key(configured, monkeypatch):
    assert storage.ready()
    monkeypatch.delenv('WEB_PERSONAL_ENCRYPTION_KEY_V1')
    assert not storage.ready()


def test_rotation_preserves_old_key_and_binds_document(configured, monkeypatch):
    configured['encryption_key_id'] = 'V1'
    encrypted = storage.encrypt(b'fictional identity', configured)
    monkeypatch.setenv('WEB_PERSONAL_KEY_ID', 'V2')
    monkeypatch.setenv('WEB_PERSONAL_ENCRYPTION_KEY_V2', base64.b64encode(os.urandom(32)).decode())
    assert storage.decrypt(encrypted, configured) == b'fictional identity'
    with pytest.raises(InvalidTag): storage.decrypt(encrypted, {**configured, 'document_id': 'another'})
