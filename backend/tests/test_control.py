import asyncio
from datetime import datetime,timezone,timedelta
from fastapi import APIRouter
from test_web_identity import system,login
import web_control as control

def test_control_denies_investor(system):
 c,db,mail=system;login(c,mail)
 r=APIRouter(prefix='/api');control.register_control_routes(r,db);c.app.include_router(r)
 assert c.get('/api/account/control').status_code==403
 assert c.get('/api/account/control/records').status_code==403
 assert c.post('/api/account/control/rafa-premium',json={}).status_code==403

def test_control_counts_and_omits_secrets(system):
 c,db,mail=system
 now=datetime.now(timezone.utc)
 db.raw.web_users.insert_one({'subject_id':'u','active':True,'account_kind':'inversor','created_at':now,'password_hash':'SECRET'})
 db.raw.web_recommendations.insert_one({'created_at':now,'viewed_at':now,'op_ref':'OP-1'})
 db.raw.web_recommendations.insert_one({'created_at':now-timedelta(days=9),'op_ref':'OP-2'})
 db.raw.web_checkout_intents.insert_one({'state':'PENDING_PAYMENT','created_at':now})
 result=asyncio.run(control.data(db,7));m={x['key']:x for x in result['metrics']}
 assert m['recommendations']['value']==1 and m['recommendations']['previous']==1
 assert m['views']['value']==1 and m['payments']['value']==0
 assert 'SECRET' not in str(result)
 assert result['segments']['standard']==1

def test_test_premium_separate_from_paid(system):
 c,db,mail=system
 db.raw.web_users.insert_one({'subject_id':'u','active':True})
 db.raw.web_entitlements.insert_one({'subject_id':'u','product':'PREMIUM','active':True,'provider':'MASTER_TEST','valid_until':'2099-01-01T00:00:00Z'})
 result=asyncio.run(control.data(db,7))
 assert result['segments']['premium_test']==1 and result['segments']['premium_paid']==0
