"""MFA-only team inbox over existing investor conversations."""
import asyncio
import logging
from fastapi import Request, Query
from web_accounts import administrator
from web_identity import denied, audit
from investor_access import TeamReply, save_team_reply

NEW_REPLY_SCOPE = 'MASTER_NEW_REPLIES_20261025'


async def mail_worker(db):
    from web_workers import dispatch_email_once
    while True:
        try:
            result = await dispatch_email_once(db, notification_scope=NEW_REPLY_SCOPE)
            delay = 2 if result.get('processed') else 30
        except Exception:
            logging.getLogger(__name__).warning('new_team_reply_notification_retry')
            delay = 30
        await asyncio.sleep(delay)


def register_team_message_routes(router, db):
    @router.get('/account/team-messages')
    async def inbox(request: Request, offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=50)):
        await administrator(request, db)
        rows = await db.web_message_threads.find({}, {'_id': 0}).sort('updated_at', -1).skip(offset).limit(limit + 1).to_list(limit + 1)
        items = []
        for row in rows[:limit]:
            user = await db.web_users.find_one({'subject_id': row['subject_id'], 'active': True}, {'name': 1})
            if not user:
                continue
            items.append({'thread_id': row['thread_id'], 'name': user.get('name', 'Usuario'),
                'op_ref': row.get('op_ref', ''), 'state': row.get('state'),
                'updated_at': row.get('updated_at'), 'messages': row.get('messages', [])})
        return {'items': items, 'next_offset': offset + limit if len(rows) > limit else None}

    @router.post('/account/team-messages/reply')
    async def reply(request: Request, payload: TeamReply):
        actor = await administrator(request, db)
        thread = await db.web_message_threads.find_one({'thread_id': payload.thread_id})
        if not thread or not await db.web_users.find_one({'subject_id': thread['subject_id'], 'active': True}):
            denied('thread_not_found', 404)
        result = await save_team_reply(db, payload, notification_scope=NEW_REPLY_SCOPE)
        if not result.get('idempotent'):
            await audit(db, actor['subject_id'], 'team_reply:' + payload.event_id)
        return result
