"""Recipient-bound summaries. Sharing never grants Premium or full dossier access."""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal
from urllib.parse import quote

from fastapi import Depends, Request
from pydantic import BaseModel, ConfigDict, Field
from pymongo import ReturnDocument

from investor_access import authenticated_subject, context, fail, future, OP_RE
from web_accounts import administrator
from web_identity import audit, public_origin, rate_limit
from web_access_restrictions import blocked

SCOPE = 'CLIENT_RECOMMENDATIONS_V1'


def now():
    return datetime.now(timezone.utc)


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Professional(Strict):
    subject_id: str = Field(min_length=1, max_length=200)
    kind: Literal['colaborador', 'suscriptor']
    active: bool
    valid_until: str


class Link(Strict):
    professional_id: str = Field(min_length=1, max_length=200)
    investor_id: str = Field(min_length=1, max_length=200)


class Decision(Strict):
    accept: bool


class Summary(Strict):
    op_ref: str = Field(pattern=r'^OP-[A-Za-z0-9-]{1,70}$')
    title: str = Field(min_length=1, max_length=160)
    location: str = Field(min_length=1, max_length=160)
    investment: str = Field(min_length=1, max_length=100)
    roi: str = Field(min_length=1, max_length=100)
    timeframe: str = Field(min_length=1, max_length=100)
    profit: str = Field(min_length=1, max_length=100)
    assumptions: str = Field(min_length=1, max_length=1000)
    approved: bool


class Share(Strict):
    op_ref: str = Field(pattern=r'^OP-[A-Za-z0-9-]{1,70}$')
    investor_ids: list[str] = Field(min_length=1, max_length=20)
    channel: Literal['email', 'whatsapp']


class Reply(Strict):
    event_id: str = Field(min_length=8, max_length=80)
    body: str = Field(min_length=1, max_length=2000)


async def active_user(db, subject):
    user = await db.web_users.find_one({'subject_id': subject, 'active': True, 'email_verified': True})
    if not user or await blocked(db, user):
        fail('recommendation_not_available', 404)
    return user


async def professional(db, subject):
    user = await active_user(db, subject)
    grant = await db.web_professionals.find_one({'_id': subject, 'active': True}) or {}
    if grant.get('kind') not in {'colaborador', 'suscriptor'} or not future(grant.get('valid_until')):
        fail('professional_access_required')
    return user, grant


async def accepted_link(db, sender, recipient):
    link = await db.web_client_links.find_one({'_id': recipient, 'professional_id': sender, 'state': 'ACCEPTED'})
    if not link:
        fail('accepted_client_link_required')
    return link


async def summary_allowed(db, sender, op):
    await professional(db, sender)
    ctx = await context(db, sender, op)
    if not ctx['premium'] or ctx['stage'] < 2:
        fail('premium_required')
    if not ctx.get('founder_access') and 'CATALOG' not in ctx['grant'].get('permissions', []):
        fail('operation_permission_required')
    binding = await db.web_operation_bindings.find_one({'public_ref': op, 'publication_approved': True, 'catalog_reference_safe': True})
    summary = await db.web_share_summaries.find_one({'_id': op, 'approved': True})
    if not binding or not summary:
        fail('summary_not_published', 404)
    return summary


async def authorized_share(db, ident, subject):
    row = await db.web_recommendations.find_one({'_id': ident})
    if not row or subject not in {row['sender_id'], row['investor_id']} or row.get('revoked') or not future(row['valid_until']):
        fail('recommendation_not_available', 404)
    await active_user(db, row['investor_id'])
    await accepted_link(db, row['sender_id'], row['investor_id'])
    summary = await summary_allowed(db, row['sender_id'], row['op_ref'])
    return row, summary


async def notification(db, recipient, ident, title, body):
    await db.web_notifications.update_one({'subject_id': recipient, 'id': ident}, {'$setOnInsert': {
        'subject_id': recipient, 'id': ident, 'title': title, 'body': body, 'read': False,
        'created_at': now().isoformat()}}, upsert=True)


async def recommendation_mail(db, outbox):
    """Recheck authority at dispatch; no arbitrary message/recipient from a browser."""
    row, _ = await authorized_share(db, outbox['recommendation_id'], outbox['subject_id'])
    prefs = await db.web_workspace_settings.find_one({'subject_id': row['investor_id']}) or {}
    if prefs.get('operation_alerts') is False:
        fail('recommendation_opt_out')
    sender = await active_user(db, row['sender_id'])
    name = ' '.join(sender.get('name', 'Tu profesional').split())[:160]
    url = public_origin() + '/mi-oportuniia#ficha/' + row['_id']
    return (f"{name} te recomienda {row['op_ref']} · OPORTUNIIA",
        f"Hola,\n\n{name} te ha recomendado la operación {row['op_ref']}.\n"
        f"Consulta el resumen y comenta tus dudas con {name} desde tu área privada:\n\n{url}\n\n"
        "El acceso es personal. Esta recomendación no activa Premium ni implica una reserva.")


def register_recommendation_routes(router, db):
    @router.post('/account/professionals')
    async def set_professional(payload: Professional, request: Request):
        actor = await administrator(request, db)
        await active_user(db, payload.subject_id)
        if payload.active and not future(payload.valid_until): fail('invalid_professional_period', 422)
        await db.web_professionals.update_one({'_id': payload.subject_id}, {'$set': payload.model_dump()}, upsert=True)
        await audit(db, actor['subject_id'], 'professional_access:' + payload.subject_id)
        return {'saved': True}

    @router.post('/account/client-links')
    async def invite(payload: Link, request: Request):
        actor = await administrator(request, db)
        sender, _ = await professional(db, payload.professional_id)
        await active_user(db, payload.investor_id)
        if payload.professional_id == payload.investor_id: fail('invalid_client_link', 422)
        # Unique investor key prevents silently assigning an existing client twice.
        await db.web_client_links.update_one({'_id': payload.investor_id}, {'$setOnInsert': {
            **payload.model_dump(), 'state': 'PENDING', 'created_at': now().isoformat(),
            'invitation_id': str(uuid.uuid4()), 'created_by': actor['subject_id']}}, upsert=True)
        row = await db.web_client_links.find_one({'_id': payload.investor_id})
        if row['professional_id'] != payload.professional_id or row['state'] != 'PENDING':
            fail('client_already_linked_or_invitation_closed', 409)
        await notification(db, payload.investor_id, row['invitation_id'], 'Confirma quién te acompaña',
            sender.get('name', 'Tu profesional') + ' solicita vincularte a su cartera. Revisa la invitación en Mis inversores y recomendaciones.')
        return {'state': 'PENDING'}

    @router.post('/account/professional/invitation')
    async def decide(payload: Decision, subject: str = Depends(authenticated_subject)):
        row = await db.web_client_links.find_one_and_update({'_id': subject, 'state': 'PENDING'},
            {'$set': {'state': 'ACCEPTED' if payload.accept else 'DECLINED', 'decided_at': now().isoformat(),
                      'consent_version': 'CLIENT_LINK_V1', 'consented_by': subject}}, return_document=ReturnDocument.AFTER)
        if not row: fail('invitation_not_pending', 409)
        await notification(db, row['professional_id'], row['invitation_id'] + '-decision', 'Respuesta a tu invitación',
            'El cliente ha aceptado la vinculación.' if payload.accept else 'El cliente ha rechazado la vinculación. No se ha bloqueado su cuenta.')
        return {'state': row['state']}

    @router.post('/account/share-summaries')
    async def publish(payload: Summary, request: Request):
        actor = await administrator(request, db)
        await db.web_share_summaries.update_one({'_id': payload.op_ref}, {'$set': {
            **payload.model_dump(), 'approved_by': actor['subject_id'], 'updated_at': now().isoformat()}}, upsert=True)
        await audit(db, actor['subject_id'], 'share_summary:' + payload.op_ref)
        return {'saved': True}

    @router.get('/account/professional/workspace')
    async def workspace(subject: str = Depends(authenticated_subject)):
        grant = await db.web_professionals.find_one({'_id': subject, 'active': True}) or {}
        is_prof = grant.get('kind') in {'colaborador', 'suscriptor'} and future(grant.get('valid_until'))
        clients = []
        if is_prof:
            links = await db.web_client_links.find({'professional_id': subject}, {'_id': 0}).to_list(500)
            for link in links:
                user = await db.web_users.find_one({'subject_id': link['investor_id'], 'active': True})
                if not user or await blocked(db, user): continue
                draft = await db.web_profile_drafts.find_one({'subject_id': link['investor_id']}) or {}
                clients.append({'id': link['investor_id'], 'name': (draft.get('profile') or {}).get('company_name') or user.get('name'), 'state': link['state']})
        invitation = await db.web_client_links.find_one({'_id': subject, 'state': 'PENDING'})
        if invitation:
            sender = await db.web_users.find_one({'subject_id': invitation['professional_id'], 'active': True}) or {}
            invitation = {'name': sender.get('name', 'Tu profesional')}
        rows = await db.web_recommendations.find({'$or': [{'sender_id': subject}, {'investor_id': subject}]}, {'_id': 1, 'op_ref': 1, 'sender_id': 1, 'investor_id': 1, 'channel': 1, 'created_at': 1, 'viewed_at': 1, 'valid_until': 1, 'revoked': 1}).sort('created_at', -1).to_list(100)
        for row in rows:
            row['id'] = row.pop('_id')
            sender = await db.web_users.find_one({'subject_id': row['sender_id']}) or {}
            row['sender_name'] = sender.get('name', 'Tu profesional')
            mail = await db.web_email_outbox.find_one({'_id': 'recommendation:' + row['id']}) or {}
            row['mail_state'] = mail.get('state')
        return {'kind': grant.get('kind') if is_prof else None, 'clients': clients, 'invitation': invitation, 'recommendations': rows}

    @router.post('/account/professional/recommendations')
    async def recommend(payload: Share, request: Request, subject: str = Depends(authenticated_subject)):
        sender, _ = await professional(db, subject)
        await summary_allowed(db, subject, payload.op_ref)
        recipients = list(dict.fromkeys(payload.investor_ids))
        prepared = []
        for recipient in recipients:
            await active_user(db, recipient)
            await accepted_link(db, subject, recipient)
            prefs = await db.web_workspace_settings.find_one({'subject_id': recipient}) or {}
            if prefs.get('operation_alerts') is False or (payload.channel == 'email' and prefs.get('email_copies') is False):
                fail('recommendation_opt_out', 409)
            phone = ''
            if payload.channel == 'whatsapp':
                draft = await db.web_profile_drafts.find_one({'subject_id': recipient}) or {}
                import re
                phone = re.sub(r'[\s().-]', '', (draft.get('profile') or {}).get('phone', ''))
                if not re.fullmatch(r'\+[1-9][0-9]{7,14}', phone): fail('international_phone_required', 422)
            prepared.append((recipient, phone))
        await rate_limit(db, request, 'recommendation', subject)
        result = []
        for recipient, phone in prepared:
            # Same sender/recipient/operation/channel/day: double click/retry does not resend.
            ident = hashlib.sha256(f'{subject}|{recipient}|{payload.op_ref}|{payload.channel}|{now().date()}'.encode()).hexdigest()[:40]
            stamp = now()
            await db.web_recommendations.update_one({'_id': ident}, {'$setOnInsert': {
                'sender_id': subject, 'investor_id': recipient, 'op_ref': payload.op_ref, 'channel': payload.channel,
                'created_at': stamp.isoformat(), 'valid_until': (stamp + timedelta(days=7)).isoformat()}}, upsert=True)
            url = public_origin() + '/mi-oportuniia#ficha/' + ident
            await notification(db, recipient, 'recommendation:' + ident,
                sender.get('name', 'Tu profesional') + ' te ha recomendado ' + payload.op_ref,
                'Puedes consultar la ficha en Mis inversores y recomendaciones. Acceso personal, disponible durante siete días.')
            if payload.channel == 'email':
                await db.web_email_outbox.update_one({'_id': 'recommendation:' + ident}, {'$setOnInsert': {
                    'subject_id': recipient, 'recommendation_id': ident, 'notification_scope': SCOPE,
                    'state': 'PENDING_EMAIL_PROVIDER', 'created_at': stamp}}, upsert=True)
            result.append({'id': ident, 'channel': payload.channel, 'url': url, 'whatsapp_url':
                'https://wa.me/' + phone[1:] + '?text=' + quote('Hola, he visto esta operación *' + payload.op_ref + '* que podría interesarte. Revísala y comentamos cualquier duda.\n' + url)
                if phone else None})
        return {'items': result}

    @router.get('/account/professional/recommendations/{ident}')
    async def read(ident: str, subject: str = Depends(authenticated_subject)):
        row, summary = await authorized_share(db, ident, subject)
        if subject == row['investor_id']:
            await db.web_recommendations.update_one({'_id': ident}, {'$set': {'viewed_at': now().isoformat()}})
        sender = await active_user(db, row['sender_id'])
        # Explicit allowlist: never forward provider/internal/source document fields.
        fields = ('op_ref', 'title', 'location', 'investment', 'roi', 'timeframe', 'profit', 'assumptions', 'updated_at')
        messages = await db.web_recommendation_messages.find({'recommendation_id': ident}, {'_id': 0, 'body': 1, 'author_name': 1, 'created_at': 1}).sort('created_at', 1).to_list(100)
        return {'summary': {k: summary.get(k) for k in fields}, 'sender_name': sender.get('name'),
                'watermark': 'Uso personal · ' + hashlib.sha256(row['investor_id'].encode()).hexdigest()[:12] + ' · ' + row['op_ref'] + ' · ' + now().date().isoformat(),
                'valid_until': row['valid_until'], 'can_revoke': subject == row['sender_id'], 'messages': messages}

    @router.post('/account/professional/recommendations/{ident}/reply')
    async def reply(ident: str, payload: Reply, request: Request, subject: str = Depends(authenticated_subject)):
        row, _ = await authorized_share(db, ident, subject)
        await rate_limit(db, request, 'recommendation-reply', subject)
        user = await active_user(db, subject)
        key = hashlib.sha256(f'{ident}|{subject}|{payload.event_id}'.encode()).hexdigest()
        await db.web_recommendation_messages.update_one({'_id': key}, {'$setOnInsert': {'recommendation_id': ident,
            'author_name': user.get('name', 'Usuario'), 'body': payload.body, 'created_at': now().isoformat()}}, upsert=True)
        other = row['sender_id'] if subject == row['investor_id'] else row['investor_id']
        await notification(db, other, key, 'Respuesta sobre ' + row['op_ref'], 'Tienes una respuesta en Mis inversores y recomendaciones.')
        return {'saved': True}

    @router.post('/account/professional/recommendations/{ident}/revoke')
    async def revoke(ident: str, subject: str = Depends(authenticated_subject)):
        row = await db.web_recommendations.find_one({'_id': ident, 'sender_id': subject})
        if not row: fail('recommendation_not_available', 404)
        await db.web_recommendations.update_one({'_id': ident}, {'$set': {'revoked': True}})
        return {'revoked': True}
