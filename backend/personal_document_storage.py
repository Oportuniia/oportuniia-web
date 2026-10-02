"""MI OPORTUNIIA personal-file storage; isolated from LEGAL and PRESENTACION.

Infrastructure adapter only. NO public routes. Caller must authenticate the
real WEB investor server-side and enforce actor_id ownership before invoking.
Credentials are read from MI_* env vars; production bucket must be dedicated.
"""
from __future__ import annotations
import hashlib
import os
import re
import secrets
from dataclasses import dataclass

import boto3
from botocore.config import Config

_ID = re.compile(r"^[a-zA-Z0-9_-]{8,100}$")
_ALLOWED = {"application/pdf", "image/jpeg", "image/png", "image/webp"}
_MAX_SIZE = 25 * 1024 * 1024


@dataclass(frozen=True)
class PersonalFileScope:
    """Must be built ONLY by verified server-side investor identity adapter."""
    actor_id: str
    verified_session: bool


def _scope(scope: PersonalFileScope) -> str:
    if not isinstance(scope, PersonalFileScope) or not scope.verified_session:
        raise PermissionError("verified investor session required")
    if not _ID.fullmatch(scope.actor_id):
        raise PermissionError("invalid server-side actor id")
    return hashlib.sha256(("mi-oportuniia-actor-v1:" + scope.actor_id).encode()).hexdigest()


def _r2():
    names = ("MI_R2_ENDPOINT", "MI_R2_ACCESS_KEY_ID", "MI_R2_SECRET_ACCESS_KEY", "MI_R2_BUCKET")
    cfg = {name: os.environ.get(name, "").strip() for name in names}
    if any(not v for v in cfg.values()):
        raise RuntimeError("private MI OPORTUNIIA storage is not configured")
    if not cfg["MI_R2_ENDPOINT"].startswith("https://"):
        raise RuntimeError("MI R2 endpoint must use TLS")
    if cfg["MI_R2_BUCKET"] in {
        os.environ.get("R2_BUCKET"), "oportuniia-core-prod", "oportuniia-presentacion-prod"
    }:
        raise RuntimeError("personal documents require a separate R2 bucket")
    client = boto3.client(
        "s3", endpoint_url=cfg["MI_R2_ENDPOINT"],
        aws_access_key_id=cfg["MI_R2_ACCESS_KEY_ID"],
        aws_secret_access_key=cfg["MI_R2_SECRET_ACCESS_KEY"],
        region_name="auto", config=Config(signature_version="s3v4"),
    )
    return client, cfg["MI_R2_BUCKET"]


def new_upload(scope: PersonalFileScope, *, mime: str, size: int) -> dict:
    """Issue a short-lived scoped PUT URL; metadata remains server-side only."""
    actor_namespace = _scope(scope)
    if mime not in _ALLOWED or type(size) is not int or not 1 <= size <= _MAX_SIZE:
        raise ValueError("unsupported type or file size")
    client, bucket = _r2()
    file_id = secrets.token_hex(16)
    key = f"personal/v1/{actor_namespace}/{file_id}/original"
    url = client.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": key, "ContentType": mime},
        ExpiresIn=300,
        HttpMethod="PUT",
    )
    # Do not expose key in API responses; persist returned storage_key in
    # private Mongo document associated with the authenticated actor.
    return {"file_id": file_id, "storage_key": key, "upload_url": url,
            "expires_seconds": 300, "mime": mime, "size": size}


def private_download(scope: PersonalFileScope, *, storage_key: str) -> str:
    """Caller MUST first look up file by (actor_id, file_id) in private Mongo.
    The key is an internal value, NEVER taken from a request.
    """
    namespace = _scope(scope)
    expected_prefix = f"personal/v1/{namespace}/"
    if not isinstance(storage_key, str) or not storage_key.startswith(expected_prefix):
        raise PermissionError("cross-user document access denied")
    if not re.fullmatch(re.escape(expected_prefix) + r"[0-9a-f]{32}/original", storage_key):
        raise PermissionError("invalid private storage key")
    client, bucket = _r2()
    return client.generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": storage_key},
        ExpiresIn=60, HttpMethod="GET",
    )
