"""Provision valid accounts and verify public referral transport with labelled test records.

Run from backend: python scripts/verify_referrals_live.py
No mail, payments, real client data, passwords or credentials are emitted.
Verification records are disabled afterwards and retained as audit evidence.
"""
import asyncio
import json
import os
from pathlib import Path
import secrets
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.requests import Request
from web_identity import now, digest, public_origin, SESSION_COOKIE
from web_referrals import own_link, valid_owner, signup_origin, ensure_indexes, COOKIE


async def main():
    client=AsyncIOMotorClient(os.environ['MONGO_URL'],tz_aware=True)
    db=client[os.environ['DB_NAME']]
    origin=public_origin()
    await ensure_indexes(db)
    count=0
    async for user in db.web_users.find({'active':True,'email_verified':True},{'subject_id':1}):
        if user.get('subject_id') and await valid_owner(db,user['subject_id']):
            if await own_link(db,user['subject_id']): count+=1
    print(json.dumps({'provisioned_active_verified_accounts':count,'origin':origin}),flush=True)
    run='referral-verification:'+str(uuid.uuid4())
    owner=run+':owner';lead=run+':lead'; token=secrets.token_urlsafe(32)
    from datetime import timedelta
    try:
        await db.web_users.insert_one({'subject_id':owner,'name':'Verificación técnica de referidos','active':True,'email_verified':True,'session_version':0,'verification_run':run,'created_at':now(),'account_kind':'colaborador'})
        await db.web_sessions.insert_one({'token_hash':digest(token),'subject_id':owner,'version':0,'revoked':False,'expires_at':now()+timedelta(minutes=5),'last_seen':now(),'created_at':now(),'verification_run':run})
        async with httpx.AsyncClient(timeout=30,follow_redirects=False) as http:
            me=await http.get(origin+'/api/account/referrals',cookies={SESSION_COOKIE:token})
            assert me.status_code==200,('own_link',me.status_code)
            data=me.json()
            qr=await http.get(origin+'/api/account/referrals/qr',cookies={SESSION_COOKIE:token})
            assert qr.status_code==200 and '<svg' in qr.text,('qr',qr.status_code)
            visit=await http.get(data['link']+'?channel=QR')
            assert visit.status_code==303 and visit.headers['location']==origin+'/cuenta',('visit',visit.status_code)
            assert 'HttpOnly' in visit.headers['set-cookie'] and 'Secure' in visit.headers['set-cookie']
            raw=visit.cookies.get(COOKIE)
            assert raw
            request=Request({'type':'http','headers':[(b'cookie',(COOKIE+'='+raw).encode())]})
            acquisition=await signup_origin(db,request)
            assert acquisition['referrer_id']==owner and acquisition['source']=='QR'
            await db.web_users.insert_one({'subject_id':lead,'active':False,'verification_run':run,'acquisition':acquisition,'created_at':now()})
            saved=await db.web_users.find_one({'subject_id':lead})
            assert saved['acquisition']['referrer_id']==owner
            again=await http.get(origin+'/api/account/referrals',cookies={SESSION_COOKIE:token})
            assert len(again.json()['items'])==1 and again.json()['link']==data['link']
            anonymous=await http.get(origin+'/api/account/referrals')
            assert anonymous.status_code==401
            print(json.dumps({'public_link':True,'qr_svg':True,'secure_cookie':True,'persisted_attribution':True,'stable_link':True,'portfolio_isolation':True,'verification_run':run}),flush=True)
        founder=await db.web_users.find_one({'username':'rafamaster','active':True,'email_verified':True,'role':'superadmin'})
        if founder:
            link=await own_link(db,founder['subject_id'])
            if link: print(json.dumps({'founder_link':origin+'/api/account/referrals/visit/'+link['code']}),flush=True)
    finally:
        await db.web_sessions.update_many({'verification_run':run},{'$set':{'revoked':True}})
        await db.web_users.update_many({'verification_run':run},{'$set':{'active':False,'verification_completed_at':now()}})
        await db.web_referral_links.update_many({'subject_id':owner},{'$set':{'active':False}})
        client.close()


if __name__=='__main__':asyncio.run(main())
