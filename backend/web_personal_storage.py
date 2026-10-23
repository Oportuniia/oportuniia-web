"""Private document storage. R2 receives only authenticated ciphertext.

Per-record backend/key version preserves existing KMS objects and supports key
rotation without rewriting historical documents. No public or presigned URLs.
"""
import base64
import hashlib
import os
from urllib.parse import urlparse

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAX_BYTES = 20 * 1024 * 1024


def backend():
    return os.getenv('WEB_PERSONAL_STORAGE_BACKEND', 's3-kms')


def key_id():
    value = os.getenv('WEB_PERSONAL_KEY_ID', 'V1')
    if not value.isalnum() or len(value) > 20:
        raise ValueError('invalid_document_key_version')
    return value


def encryption_key(version):
    if not version.isalnum() or len(version) > 20:
        raise ValueError('invalid_document_key_version')
    key = base64.b64decode(os.environ['WEB_PERSONAL_ENCRYPTION_KEY_' + version], validate=True)
    if len(key) != 32:
        raise ValueError('invalid_document_key')
    return key


def ready():
    if os.getenv('WEB_PERSONAL_UPLOADS_ENABLED') != 'true' or not os.getenv('WEB_PERSONAL_BUCKET'):
        return False
    if backend() == 's3-kms':
        return bool(os.getenv('WEB_PERSONAL_KMS_KEY_ID'))
    if backend() != 'r2-aesgcm':
        return False
    try:
        encryption_key(key_id())
        endpoint = urlparse(os.environ['WEB_PERSONAL_R2_ENDPOINT'])
        return (endpoint.scheme == 'https' and bool(endpoint.hostname)
                and bool(os.getenv('WEB_PERSONAL_R2_ACCESS_KEY_ID'))
                and bool(os.getenv('WEB_PERSONAL_R2_SECRET_ACCESS_KEY')))
    except (KeyError, ValueError):
        return False


def client(storage_backend=None):
    import boto3
    if (storage_backend or backend()) == 'r2-aesgcm':
        return boto3.client('s3', endpoint_url=os.environ['WEB_PERSONAL_R2_ENDPOINT'], region_name='auto',
                            aws_access_key_id=os.environ['WEB_PERSONAL_R2_ACCESS_KEY_ID'],
                            aws_secret_access_key=os.environ['WEB_PERSONAL_R2_SECRET_ACCESS_KEY'])
    return boto3.client('s3')


def aad(row):
    return ('OPORTUNIIA_PERSONAL_V1\0' + row['subject_id'] + '\0' + row['document_id']
            + '\0' + row['storage_key']).encode()


def encrypt(data, row):
    nonce = os.urandom(12)
    return nonce + AESGCM(encryption_key(row['encryption_key_id'])).encrypt(nonce, data, aad(row))


def decrypt(data, row):
    if len(data) < 28 or len(data) > MAX_BYTES + 28:
        raise ValueError('invalid_document_ciphertext')
    return AESGCM(encryption_key(row['encryption_key_id'])).decrypt(data[:12], data[12:], aad(row))


def write(data, row):
    row['storage_backend'] = backend()
    row['storage_bucket'] = os.environ['WEB_PERSONAL_BUCKET']
    options = {}
    body, mime = data, row['mime']
    if backend() == 'r2-aesgcm':
        row['encryption_key_id'] = key_id()
        body, mime = encrypt(data, row), 'application/octet-stream'
    elif backend() == 's3-kms':
        options = dict(ServerSideEncryption='aws:kms', SSEKMSKeyId=os.environ['WEB_PERSONAL_KMS_KEY_ID'])
    else:
        raise ValueError('unsupported_document_storage')
    client().put_object(Bucket=row['storage_bucket'], Key=row['storage_key'], Body=body,
                        ContentType=mime, **options)


def read(row):
    storage_backend = row.get('storage_backend', 's3-kms')
    obj = client(storage_backend).get_object(Bucket=row.get('storage_bucket') or os.environ['WEB_PERSONAL_BUCKET'], Key=row['storage_key'])
    data = obj['Body'].read(MAX_BYTES + 29)
    if storage_backend == 'r2-aesgcm':
        data = decrypt(data, row)
    elif storage_backend != 's3-kms':
        raise ValueError('unsupported_document_storage')
    if len(data) > MAX_BYTES or hashlib.sha256(data).hexdigest() != row['sha256']:
        raise ValueError('document_integrity_failure')
    return data
