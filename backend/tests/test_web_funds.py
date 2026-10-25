import asyncio
from fastapi import APIRouter
from test_web_identity import system, login
from web_funds import register_fund_routes, ensure_fund_indexes


def setup(system, admin=True):
    c, db, mail = system
    login(c, mail)
    router = APIRouter(prefix="/api")
    register_fund_routes(router, db)
    c.app.include_router(router)
    asyncio.run(ensure_fund_indexes(db))
    db.raw.web_users.update_one({}, {"$set": {"role": "superadmin" if admin else "user", "mfa_enabled": True}})
    db.raw.web_sessions.update_many({}, {"$set": {"mfa_verified": True}})
    return c, db


def create(c, name="Fondo uno"):
    r = c.post('/api/staff/funds/entities', json={"name": name})
    assert r.status_code == 201, r.text
    return r.json()['entity_id']


def published(db, ref="OP-UNO", internal="private-id"):
    db.raw.web_operation_bindings.insert_one({'public_ref': ref, 'internal_id': internal,
        'publication_approved': True, 'catalog_reference_safe': True})
    db.raw.presentation_web_published.insert_one({'internal_id': internal, 'publication_state': 'PUBLISHED',
        'item': {'title': 'Operación real de prueba', 'phase': 'Análisis', 'debtor_name': 'SECRET DEBTOR',
            'documents': {'private_url': 'https://private.invalid'}, 'provider_secret': 'SECRET'}})


def test_no_self_enrollment_or_forged_role(system):
    c, db = setup(system, False)
    assert c.get('/api/funds/entities').json()['items'] == []
    assert c.post('/api/staff/funds/entities', json={'name': 'Fake'}, headers={'X-Role': 'superadmin'}).status_code == 403
    assert c.get('/api/funds/entities/arbitrary/portfolio').status_code == 403


def test_admin_mfa_csrf_and_verified_account_required(system):
    c, db = setup(system)
    db.raw.web_sessions.update_many({}, {'$set': {'mfa_verified': False}})
    assert c.get('/api/funds/entities').status_code == 403
    db.raw.web_sessions.update_many({}, {'$set': {'mfa_verified': True}})
    assert c.post('/api/staff/funds/entities', json={'name':'Fondo'}, headers={'X-CSRF-Token':'wrong'}).status_code == 403
    owner=create(c)
    assert c.post(f'/api/staff/funds/entities/{owner}/members', json={'email':'unknown@example.com'}).status_code == 409
    assert c.post('/api/staff/funds/entities', json={'name':'   '}).status_code == 422


def test_tenant_isolation_projection_and_revoke_without_logout(system):
    c, db=setup(system)
    one,two=create(c),create(c,'Fondo dos')
    published(db)
    published(db,'OP-DOS','second-private')
    for owner,ref in [(one,'OP-UNO'),(two,'OP-DOS')]:
        assert c.post(f'/api/staff/funds/entities/{owner}/operations',json={'op_ref':ref}).status_code==200
    assert c.post(f'/api/staff/funds/entities/{one}/members',json={'email':'one@example.com'}).status_code==200
    own=db.raw.web_users.find_one({})['subject_id']
    db.raw.web_users.update_one({}, {'$set': {'role':'user'}})
    assert [r['entity_id'] for r in c.get('/api/funds/entities').json()['items']]==[one]
    r=c.get(f'/api/funds/entities/{one}/portfolio')
    assert r.status_code==200 and r.json()['total']==1
    assert r.json()['by_phase']=={'Análisis':1}
    for private in ['SECRET','private.invalid','private-id','OP-DOS']:
        assert private not in r.text
    assert c.get(f'/api/funds/entities/{two}/portfolio').status_code==403
    assert c.get(f'/api/staff/funds/entities/{one}/access').status_code==403
    db.raw.web_users.update_one({}, {'$set': {'role':'superadmin'}})
    assert c.delete(f'/api/staff/funds/entities/{one}/members/{own}').status_code==200
    db.raw.web_users.update_one({}, {'$set': {'role':'user'}})
    assert c.get(f'/api/funds/entities/{one}/portfolio').status_code==403


def test_only_published_operations_and_no_double_assignment(system):
    c,db=setup(system)
    one,two=create(c),create(c,'Fondo dos')
    assert c.post(f'/api/staff/funds/entities/{one}/operations',json={'op_ref':'OP-UNKNOWN'}).status_code==409
    published(db)
    assert c.post(f'/api/staff/funds/entities/{one}/operations',json={'op_ref':'OP-UNO'}).status_code==200
    assert c.post(f'/api/staff/funds/entities/{two}/operations',json={'op_ref':'OP-UNO'}).status_code==409
    db.raw.presentation_web_published.update_one({}, {'$set':{'publication_state':'WITHDRAWN'}})
    assert c.get(f'/api/funds/entities/{one}/portfolio').json()['total']==0
    db.raw.presentation_web_published.update_one({}, {'$set':{'publication_state':'PUBLISHED'}})
    assert c.delete(f'/api/staff/funds/entities/{one}/operations/OP-UNO').status_code==200
    assert c.get(f'/api/funds/entities/{one}/portfolio').json()['total']==0
    assert c.post(f'/api/staff/funds/entities/{two}/operations',json={'op_ref':'OP-UNO'}).status_code==200


def test_member_mfa_and_disabled_entity(system):
    c,db=setup(system)
    owner=create(c)
    c.post(f'/api/staff/funds/entities/{owner}/members',json={'email':'one@example.com'})
    db.raw.web_users.update_one({}, {'$set':{'role':'user'}})
    db.raw.web_sessions.update_many({}, {'$set':{'mfa_verified':False}})
    assert c.get(f'/api/funds/entities/{owner}/portfolio').status_code==403
    db.raw.web_sessions.update_many({}, {'$set':{'mfa_verified':True}})
    db.raw.web_fund_entities.update_one({}, {'$set':{'active':False}})
    assert c.get(f'/api/funds/entities/{owner}/portfolio').status_code==404
    assert c.get('/api/funds/entities').json()['items']==[]
