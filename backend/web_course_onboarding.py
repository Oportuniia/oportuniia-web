"""Narrow APP-to-WEB account preparation. Never grants dossier or contractual approval."""
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


class CourseSubscriber(BaseModel):
    model_config = ConfigDict(extra='forbid')
    app_subject: str = Field(min_length=1, max_length=100)
    code: str = Field(pattern=r'^SUS-\d{3,8}$')
    name: str = Field(min_length=2, max_length=180)
    email: EmailStr


def register_course_onboarding_routes(router, db):
    @router.post('/course-onboarding/provision')
    async def provision(payload: CourseSubscriber, request: Request):
        expected = os.getenv('COURSE_WEB_BRIDGE_KEY', '')
        if len(expected) < 32 or not hmac.compare_digest(request.headers.get('X-OPORTUNIIA-Course-Key', ''), expected):
            raise HTTPException(403, 'course_bridge_denied')
        email = str(payload.email).strip().lower()
        if await blocked(db, {'email': email}):
            raise HTTPException(409, 'account_restricted')
        user = await db.web_users.find_one({'email': email})
        subject = str(uuid.uuid5(uuid.NAMESPACE_URL, 'oportuniia-course:' + payload.app_subject))
        if not user:
            user = {'subject_id': subject, 'username': payload.code.lower(), 'name': payload.name,
                    'email': email, 'recovery_email': email, 'role': 'user', 'account_kind': 'suscriptor',
                    'active': True, 'email_verified': False, 'session_version': 0,
                    'password_hash': await hash_password(secrets.token_urlsafe(32)),
                    'must_change_password': True, 'created_at': now(),
                    'created_via': 'course_onboarding', 'app_subject': payload.app_subject}
            try:
                await db.web_users.insert_one(user)
            except DuplicateKeyError:
                user = await db.web_users.find_one({'email': email})
                if not user:
                    raise HTTPException(409, 'subscriber_code_in_use')
        if not user.get('active') or user.get('role') != 'user' or await blocked(db, user):
            raise HTTPException(409, 'account_requires_review')
        if user.get('app_subject') not in (None, payload.app_subject):
            raise HTTPException(409, 'account_mapping_conflict')
        existing = await db.oportuniiapp_web_identity_map.find_one({'app_subject': payload.app_subject})
        if existing and existing.get('web_subject_id') != user['subject_id']:
            raise HTTPException(409, 'account_mapping_conflict')
        await db.oportuniiapp_web_identity_map.update_one({'app_subject': payload.app_subject},
            {'$setOnInsert': {'web_subject_id': user['subject_id'], 'active': True, 'created_at': now()}}, upsert=True)
        # Existing investor/admin roles, passwords, profile validation and contracts stay untouched.
        token = secrets.token_urlsafe(32)
        await db.web_identity_tokens.insert_one({'token_hash': digest(token), 'subject_id': user['subject_id'],
            'purpose': 'reset', 'version': user.get('session_version', 0),
            'expires_at': now() + timedelta(minutes=30), 'used': False,
            'course_email_verification': user.get('created_via') == 'course_onboarding'})
        return {'subject_id': user['subject_id'], 'username': user['username'],
                'setup_url': public_origin() + '/cuenta#reset=' + token}
