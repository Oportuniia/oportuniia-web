"""WEB-owned acquisition attribution. Referral ownership grants no client access.

No payouts are made here. Financial policy is deliberately separate from
identity, client acceptance and operation participation.
"""
import io
import secrets
from datetime import timedelta
from typing import Literal

from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, Field
from pymongo.errors import DuplicateKeyError

from web_identity import now, digest, resolve_session, public_origin, denied, rate_limit
from web_accounts import administrator

COOKIE = '__Host-opp_referral'
WINDOW = 30 * 24 * 3600


async def ensure_indexes(db):
    await db.web_referral_links.create_index('code', unique=True)
    await db.web_referral_links.create_index('subject_id', unique=True)
    await db.web_referral_touches.create_index('expires_at', expireAfterSeconds=0)
    await db.web_users.create_index('acquisition.referrer_id')


async def valid_owner(db, subject):
    from web_access_restrictions import blocked
    user = await db.web_users.find_one({'subject_id': subject, 'active': True, 'email_verified': True})
    return bool(user and not await blocked(db, user))


async def own_link(db, subject):
    # Unique owner and code indexes arbitrate concurrent creation.
    try:
        await db.web_referral_links.update_one({'subject_id': subject}, {'$setOnInsert': {
            'subject_id': subject, 'code': secrets.token_urlsafe(24), 'active': True, 'created_at': now()}}, upsert=True)
    except DuplicateKeyError:
        if not await db.web_referral_links.find_one({'subject_id': subject}):
            raise
    return await db.web_referral_links.find_one({'subject_id': subject, 'active': True}, {'_id': 0})


def initial_origin(source, referrer=None, evidence=None):
    return {'source': source, 'referrer_id': referrer, 'evidence': evidence,
            'recorded_at': now(), 'revision': 1, 'history': []}


async def signup_origin(db, request):
    raw = request.cookies.get(COOKIE, '')
    if not raw:
        return initial_origin('ORGANIC')
    touch = await db.web_referral_touches.find_one({'_id': digest(raw), 'expires_at': {'$gt': now()}}) if len(raw) <= 200 else None
    if touch and await valid_owner(db, touch['referrer_id']):
        link = await db.web_referral_links.find_one({'subject_id': touch['referrer_id'], 'active': True})
        if link:
            return initial_origin(touch['channel'], touch['referrer_id'], touch['_id'])
    # Missing/expired evidence is not silently presented as organic.
    return initial_origin('UNRESOLVED')


class Attribution(BaseModel):
    model_config = ConfigDict(extra='forbid')
    subject_id: str = Field(min_length=1, max_length=200)
    referrer_id: str | None = Field(default=None, min_length=1, max_length=200)
    source: Literal['MANUAL', 'CORRECTED']
    expected_revision: int = Field(ge=0)
    event_id: str = Field(min_length=8, max_length=100)
    reason: str = Field(min_length=10, max_length=1000)


async def attribute(db, actor, payload):
    user = await db.web_users.find_one({'subject_id': payload.subject_id, 'active': True})
    if not user:
        denied('referral_subject_not_found', 404)
    old = user.get('acquisition') or {'source': 'LEGACY_UNKNOWN', 'revision': 0, 'history': []}
    content = payload.model_dump()
    for entry in old.get('history', []):
        if entry.get('event_id') == payload.event_id:
            if entry.get('request') != content: denied('referral_event_conflict', 409)
            return {'saved': True, 'replayed': True, 'revision': old['revision']}
    if payload.referrer_id == payload.subject_id:
        denied('self_referral_forbidden', 409)
    if payload.referrer_id and not await valid_owner(db, payload.referrer_id):
        denied('referrer_not_available', 409)
    if payload.source == 'MANUAL' and old.get('referrer_id'):
        denied('use_audited_correction', 409)
    if payload.source == 'MANUAL' and not payload.referrer_id:
        denied('manual_referrer_required', 422)
    if old['revision'] != payload.expected_revision:
        denied('referral_revision_conflict', 409)
    if len(old.get('history', [])) >= 100:
        denied('referral_history_review_required', 409)
    event = {'event_id': payload.event_id, 'request': content, 'actor_id': actor,
             'at': now(), 'before': {k: v for k, v in old.items() if k != 'history'}}
    current = {'source': payload.source, 'referrer_id': payload.referrer_id, 'revision': old['revision'] + 1,
               'recorded_at': now(), 'history': [*old.get('history', []), event]}
    query = {'subject_id': payload.subject_id}
    query['acquisition.revision' if old['revision'] else 'acquisition'] = old['revision'] if old['revision'] else {'$exists': False}
    # Audit and current ownership are a single atomic document update.
    result = await db.web_users.update_one(query, {'$set': {'acquisition': current}})
    if not result.matched_count: denied('referral_revision_conflict_retry', 409)
    return {'saved': True, 'revision': current['revision'], 'replayed': False}


def incentive_preview(*, kind, collected_minor, refunded_minor=0, referred_kind='', partner=False,
                      participation_verified=False, results_verified=False, first_operation_verified=False,
                      recognition_already_recorded=False):
    """Integer cents; preview only, never an entitlement or a payable ledger."""
    if type(collected_minor) is not int or type(refunded_minor) is not int or not 0 <= refunded_minor <= collected_minor:
        raise ValueError('invalid_collected_amount')
    net = collected_minor - refunded_minor
    if kind == 'FEE' and partner and referred_kind in {'suscriptor', 'colaborador_premium'}:
        return {'status': 'PREVIEW_ONLY', 'amount_minor': (net * 15 + 50) // 100, 'rate_percent': 15}
    if kind == 'COLLABORATOR_FIRST_OPERATION':
        if recognition_already_recorded:
            return {'status': 'ALREADY_RECOGNIZED', 'amount_minor': 0}
        if first_operation_verified and referred_kind == 'colaborador':
            return {'status': 'PREVIEW_ONLY', 'amount_minor': (net * 15 + 50) // 100, 'rate_percent': 15,
                    'basis': 'OPORTUNIIA_NET_FEES_ACTUALLY_COLLECTED', 'once_per_collaborator': True}
        return {'status': 'FIRST_COLLECTED_OPERATION_EVIDENCE_REQUIRED', 'amount_minor': None}
    if kind == 'AGENCY_OPERATION':
        return {'status': 'TERMS_REVIEW_REQUIRED' if participation_verified and results_verified else 'ACTIVE_PARTICIPATION_AND_RESULTS_REQUIRED', 'amount_minor': None}
    return {'status': 'NOT_ELIGIBLE', 'amount_minor': 0}


def register_routes(router, db):
    @router.get('/integrations/oportuniiapp/v1/referral-portfolio')
    async def app_portfolio(request: Request):
        import os
        # Reuse the existing personal-identity bridge when the separate control
        # bridge is absent. Both routes require an explicit APP→WEB mapping.
        course = bool(request.headers.get('x-oportuniia-course-key'))
        key = os.getenv('COURSE_WEB_BRIDGE_KEY' if course else 'WEB_OPORTUNIIAPP_CONTROL_M2M_KEY', '')
        supplied = request.headers.get('x-oportuniia-course-key' if course else 'x-oportuniia-web-app-m2m-key', '')
        if len(key) < 32: denied('referral_bridge_not_configured', 503)
        if not secrets.compare_digest(key, supplied): denied('unauthorized', 401)
        subject = request.headers.get('x-app-subject', '')
        if not 1 <= len(subject) <= 200: denied('invalid_subject', 400)
        mapping = await db.oportuniiapp_web_identity_map.find_one({'app_subject': subject, 'active': True})
        if not mapping or not await valid_owner(db, mapping['web_subject_id']):
            denied('web_identity_mapping_required', 409)
        link = await own_link(db, mapping['web_subject_id'])
        if not link: denied('referral_link_disabled', 403)
        return {'link': public_origin() + '/api/account/referrals/visit/' + link['code'],
                'qr_value': public_origin() + '/api/account/referrals/visit/' + link['code'] + '?channel=QR',
                'portal': public_origin() + '/mi-oportuniia#referidos',
                'financial_status': 'NOT_CONNECTED'}

    @router.get('/account/referrals')
    async def mine(request: Request):
        user, _ = await resolve_session(request, db)
        link = await own_link(db, user['subject_id'])
        if not link: denied('referral_link_disabled', 403)
        rows = await db.web_users.find({'acquisition.referrer_id': user['subject_id']},
            {'_id': 0, 'subject_id': 1, 'account_kind': 1, 'created_at': 1,
             'acquisition.source': 1, 'acquisition.revision': 1}).sort('created_at', -1).to_list(101)
        return {'sender_name': user.get('name', ''), 'link': public_origin() + '/api/account/referrals/visit/' + link['code'],
                'qr_image': public_origin() + '/api/account/referrals/qr', 'items': rows[:100],
                'limited': len(rows) > 100, 'financial_status': 'NOT_CONNECTED', 'client_access_granted': False}

    @router.get('/account/referrals/qr')
    async def qr(request: Request):
        import qrcode
        import qrcode.image.svg
        user, _ = await resolve_session(request, db)
        link = await own_link(db, user['subject_id'])
        if not link: denied('referral_link_disabled', 403)
        url = public_origin() + '/api/account/referrals/visit/' + link['code'] + '?channel=QR'
        image = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathFillImage, border=4)
        buffer = io.BytesIO(); image.save(buffer)
        return Response(buffer.getvalue(), media_type='image/svg+xml', headers={'Cache-Control': 'private, no-store'})

    @router.get('/account/referrals/visit/{code}')
    @router.get('/referrals/visit/{code}')
    async def visit(code: str, request: Request, channel: Literal['LINK', 'QR'] = 'LINK'):
        await rate_limit(db, request, 'referral_visit')
        link = await db.web_referral_links.find_one({'code': code, 'active': True}) if len(code) <= 100 else None
        if not link or not await valid_owner(db, link['subject_id']): denied('referral_not_available', 404)
        response = RedirectResponse(public_origin() + '/cuenta', status_code=303)
        existing = await signup_origin(db, request)
        # First valid touch wins for 30 days. Already registered identities are never reassigned here.
        if not existing.get('referrer_id'):
            raw = secrets.token_urlsafe(32)
            await db.web_referral_touches.insert_one({'_id': digest(raw), 'referrer_id': link['subject_id'],
                'channel': channel, 'created_at': now(), 'expires_at': now() + timedelta(seconds=WINDOW)})
            response.set_cookie(COOKIE, raw, max_age=WINDOW, secure=True, httponly=True, samesite='lax', path='/')
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response

    @router.post('/account/admin/referrals/attribution')
    async def change(payload: Attribution, request: Request):
        user = await administrator(request, db)
        return await attribute(db, user['subject_id'], payload)

    @router.get('/account/admin/referrals/{subject_id}')
    async def history(subject_id: str, request: Request):
        await administrator(request, db)
        user = await db.web_users.find_one({'subject_id': subject_id}, {'_id': 0, 'acquisition': 1})
        if user is None: denied('referral_subject_not_found', 404)
        return user.get('acquisition') or {'source': 'LEGACY_UNKNOWN', 'revision': 0, 'history': []}
