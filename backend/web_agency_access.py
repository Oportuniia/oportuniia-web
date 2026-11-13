"""APP-owned member identities, WEB-owned sessions; recycled seats never recycle people."""
import hmac
import os
import secrets
import uuid
from datetime import timedelta
from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pymongo.errors import DuplicateKeyError
from web_identity import digest, hash_password, now, public_origin
from web_access_restrictions import blocked


class Member(BaseModel):
    model_config = ConfigDict(extra='forbid')
    app_subject: str = Field(min_length=1, max_length=100)
    agency_id: str = Field(min_length=1, max_length=100)
    code: str = Field(pattern=r'^SUS-\d{3,8}\.(?:0[1-9]|[1-9][0-9])$')
    name: str = Field(min_length=2, max_length=180)
    email: EmailStr


class Revoke(BaseModel):
    model_config = ConfigDict(extra='forbid')
    app_subject: str = Field(min_length=1, max_length=100)
    agency_id: str = Field(min_length=1, max_length=100)


def authorize(request):
    expected = os.getenv('COURSE_WEB_BRIDGE_KEY', '')
    if len(expected) < 32 or not hmac.compare_digest(request.headers.get('X-OPORTUNIIA-Course-Key', ''), expected):
        raise HTTPException(403, 'agency_bridge_denied')


def register_agency_access_routes(router, db):
    @router.post('/agency-access/provision')
    async def provision(payload: Member, request: Request):
        authorize(request)
        if await db.web_agency_revocations.find_one({'_id': payload.app_subject}):
            raise HTTPException(409, 'member_revoked')
        parent = await db.oportuniiapp_web_identity_map.find_one({'app_subject': payload.agency_id, 'active': True})
        if not parent or not await db.web_users.find_one({'subject_id': parent['web_subject_id'], 'active': True}):
            raise HTTPException(409, 'agency_web_access_required')
        email = str(payload.email).lower()
        if await blocked(db, {'email': email}):
            raise HTTPException(409, 'account_restricted')
        subject = str(uuid.uuid5(uuid.NAMESPACE_URL, 'oportuniia-adherido:' + payload.app_subject))
        user = await db.web_users.find_one({'subject_id': subject})
        if not user:
            user = {'subject_id': subject, 'username': payload.code.lower(), 'name': payload.name,
                'email': email, 'recovery_email': email, 'role': 'user', 'account_kind': 'adherido',
                'agency_id': payload.agency_id, 'app_subject': payload.app_subject,
                'active': True, 'email_verified': False, 'session_version': 0,
                'password_hash': await hash_password(secrets.token_urlsafe(32)), 'must_change_password': True,
                'created_at': now(), 'created_via': 'agency_training'}
            try:
                await db.web_users.insert_one(user)
            except DuplicateKeyError:
                user = await db.web_users.find_one({'subject_id': subject})
                if not user:
                    raise HTTPException(409, 'member_email_or_code_in_use')
        if not user.get('active') or user.get('agency_id') != payload.agency_id or user.get('email') != email:
            raise HTTPException(409, 'member_mapping_conflict')
        # Revoke wins if a late provisioning request races with a departure.
        if await db.web_agency_revocations.find_one({'_id': payload.app_subject}):
            await db.web_users.update_one({'subject_id': subject}, {'$set': {'active': False, 'username': 'retired-' + subject}, '$inc': {'session_version': 1}})
            raise HTTPException(409, 'member_revoked')
        await db.oportuniiapp_web_identity_map.update_one({'app_subject': payload.app_subject},
            {'$setOnInsert': {'web_subject_id': subject, 'active': True, 'created_at': now()}}, upsert=True)
        token = secrets.token_urlsafe(32)
        await db.web_identity_tokens.insert_one({'token_hash': digest(token), 'subject_id': subject,
            'purpose': 'reset', 'version': user.get('session_version', 0), 'expires_at': now()+timedelta(minutes=30),
            'used': False, 'course_email_verification': True})
        return {'subject_id': subject, 'username': user['username'], 'setup_url': public_origin()+'/cuenta#reset='+token}

    @router.post('/agency-access/revoke')
    async def revoke(payload: Revoke, request: Request):
        authorize(request)
        subject = str(uuid.uuid5(uuid.NAMESPACE_URL, 'oportuniia-adherido:' + payload.app_subject))
        user = await db.web_users.find_one({'subject_id': subject})
        if user and user.get('agency_id') != payload.agency_id:
            raise HTTPException(409, 'member_mapping_conflict')
        await db.web_agency_revocations.update_one({'_id': payload.app_subject},
            {'$setOnInsert': {'agency_id': payload.agency_id, 'revoked_at': now()}}, upsert=True)
        await db.web_users.update_one({'subject_id': subject, 'active': True},
            {'$set': {'active': False, 'username': 'retired-'+subject}, '$inc': {'session_version': 1}})
        await db.oportuniiapp_web_identity_map.update_one({'app_subject': payload.app_subject}, {'$set': {'active': False}})
        await db.web_identity_tokens.update_many({'subject_id': subject, 'used': False}, {'$set': {'used': True}})
        return {'state': 'revoked'}
