from test_web_identity import system, login


def founder(system):
    c, db, mail=system
    login(c,mail,'info@oportuniia.com')
    db.raw.web_users.update_one({}, {'$set':{'role':'superadmin','username':'rafamaster','mfa_enabled':True}})
    db.raw.web_sessions.update_many({}, {'$set':{'mfa_verified':True}})
    return c,db


def test_save_persist_and_remove_without_changing_preferences(system):
    c,db=founder(system)
    subject=db.raw.web_users.find_one({})['subject_id']
    db.raw.web_workspace_settings.insert_one({'subject_id':subject,'email_copies':False,'photo':'kept'})
    data={'items':[{'name':'Barcelona','province':'Barcelona','min_price':1000,'max_price':200000}]}
    assert c.put('/api/investor/perimeters',json=data).status_code==200
    assert c.get('/api/investor/perimeters').json()['items'][0]['province']=='Barcelona'
    row=db.raw.web_workspace_settings.find_one({'subject_id':subject})
    assert row['photo']=='kept' and row['email_copies'] is False
    assert c.put('/api/investor/perimeters',json={'items':[]}).status_code==200
    assert c.get('/api/investor/perimeters').json()['items']==[]


def test_validation_and_csrf(system):
    c,db=founder(system)
    endpoint='/api/investor/perimeters'
    for data in [ {'items':[{'name':'x','min_price':200,'max_price':100}]},
                  {'items':[{'name':'x'}]*11}, {'items':[{'name':'   '}]},
                  {'items':[{'name':'x','subject_id':'someone-else'}]} ]:
        assert c.put(endpoint,json=data).status_code==422
    assert c.put(endpoint,json={'items':[]},headers={'X-CSRF-Token':'wrong'}).status_code==403


def test_premium_server_gate_and_ownership(system):
    c,db,mail=system
    login(c,mail)
    assert c.get('/api/investor/perimeters',headers={'X-Role':'premium'}).status_code==403
    assert c.put('/api/investor/perimeters',json={'items':[]}).status_code==403


def test_other_subject_filters_not_returned(system):
    c,db=founder(system)
    db.raw.web_workspace_settings.insert_one({'subject_id':'other','perimeters':[{'name':'PRIVATE'}]})
    assert 'PRIVATE' not in c.get('/api/investor/perimeters').text
