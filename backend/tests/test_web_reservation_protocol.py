import asyncio
from datetime import timedelta
from fastapi import APIRouter
from test_web_identity import system,login
import web_reservation_protocol as protocol
from web_identity import now

def setup(system):
 c,db,mail=system;login(c,mail)
 db.raw.web_users.update_one({}, {'$set':{'role':'superadmin','mfa_enabled':True}})
 db.raw.web_sessions.update_many({}, {'$set':{'mfa_verified':True}})
 router=APIRouter(prefix='/api');protocol.register_protocol_routes(router,db);c.app.include_router(router)
 subject=db.raw.web_users.find_one({})['subject_id']
 db.raw.web_reservations.insert_one({'checkout_request_id':'test-reserve','subject_id':subject,'op_ref':'OP-TEST','state':'PAID_PENDING_OPERATION_REVIEW','currency':'EUR','amount_received_minor':500000,'payment_reference':'synthetic-payment'})
 return c,db,subject

def approve(c):
 return c.post('/api/account/reservation-protocols/test-reserve/approve',json={'required_documents':['identity'],'confirmation':'APROBAR RESERVA'})

def test_start_only_approval_and_idempotent(system):
 c,db,subject=setup(system)
 assert db.raw.web_reservation_protocols.count_documents({})==0
 assert approve(c).status_code==200
 row=db.raw.web_reservation_protocols.find_one({})
 assert row['deadline_at']-row['approved_at']==timedelta(hours=72)
 assert approve(c).json()['already_approved'] is True
 assert db.raw.web_reservation_protocols.find_one({})['deadline_at']==row['deadline_at']

def test_permissions_and_unpaid_rejected(system):
 c,db,subject=setup(system)
 db.raw.web_users.update_one({}, {'$set':{'role':'user'}})
 assert approve(c).status_code==403
 assert c.get('/api/account/reservation-protocols/manage').status_code==403
 assert c.get('/api/account/reservation-protocols').status_code==200
 db.raw.web_users.update_one({}, {'$set':{'role':'superadmin'}})
 db.raw.web_reservations.update_one({}, {'$set':{'amount_received_minor':300000}})
 assert approve(c).status_code==409
 assert db.raw.web_reservation_protocols.count_documents({})==0

def test_daily_once_stops_at_deadline(system,monkeypatch):
 c,db,subject=setup(system);approve(c)
 sent=[]
 async def send(*args):sent.append(args)
 monkeypatch.setattr(protocol,'send_transactional',send)
 row=db.raw.web_reservation_protocols.find_one({})
 for h in (0,0,12,24,24,48,72,96):asyncio.run(protocol.tick(db,row['approved_at']+timedelta(hours=h)))
 assert len(sent)==3
 assert db.raw.web_reservation_protocols.find_one({})['state']=='EXPIRED'
 assert db.raw.web_notifications.count_documents({'protocol_id':'test-reserve','resolved':True})==3

def test_completion_and_cancellation_stop(system,monkeypatch):
 c,db,subject=setup(system);approve(c)
 async def forbidden(*args):raise AssertionError('Must not send')
 monkeypatch.setattr(protocol,'send_transactional',forbidden)
 row=db.raw.web_reservation_protocols.find_one({})
 db.raw.web_personal_documents.insert_one({'subject_id':subject,'scan_state':'CLEAN','dossier_state':'FILED','review_state':'APPROVED','document_kinds':['identity'],'created_at':row['approved_at']})
 asyncio.run(protocol.tick(db,row['approved_at']+timedelta(hours=24)))
 assert db.raw.web_reservation_protocols.find_one({})['state']=='DOCUMENTS_COMPLETE'
 assert db.raw.web_protocol_mail.count_documents({})==0
 db.raw.web_reservation_protocols.update_one({}, {'$set':{'state':'ACTIVE'}})
 db.raw.web_reservations.update_one({}, {'$set':{'state':'CANCELLED'}})
 asyncio.run(protocol.tick(db))
 assert db.raw.web_reservation_protocols.find_one({})['state']=='CANCELLED'

def test_bad_or_late_documents_dont_complete(system):
 c,db,subject=setup(system);approve(c)
 row=db.raw.web_reservation_protocols.find_one({})
 for extra in ({'scan_state':'PENDING'},{'identity_discrepancy':True},{'created_at':row['deadline_at']+timedelta(seconds=1)}):
  db.raw.web_personal_documents.insert_one({'subject_id':subject,'scan_state':'CLEAN','dossier_state':'FILED','review_state':'APPROVED','document_kinds':['identity'],'created_at':row['approved_at'],**extra})
 asyncio.run(protocol.advance(db,row,row['deadline_at']))
 assert db.raw.web_reservation_protocols.find_one({})['state']=='EXPIRED'


def test_initial_delivery_on_time_waits_for_review_and_later_compliance_does_not_restart(system,monkeypatch):
 c,db,subject=setup(system);approve(c)
 row=db.raw.web_reservation_protocols.find_one({})
 db.raw.web_personal_documents.insert_one({'subject_id':subject,'scan_state':'CLEAN','dossier_state':'FILED','review_state':'PENDING','document_kinds':['identity'],'created_at':row['deadline_at']-timedelta(minutes=1)})
 async def forbidden(*args):raise AssertionError('No reminders during review')
 monkeypatch.setattr(protocol,'send_transactional',forbidden)
 asyncio.run(protocol.tick(db,row['deadline_at']+timedelta(days=1)))
 assert db.raw.web_reservation_protocols.find_one({})['state']=='INITIAL_REVIEW_PENDING'
 db.raw.web_personal_documents.update_one({}, {'$set':{'review_state':'APPROVED'}})
 asyncio.run(protocol.tick(db,row['deadline_at']+timedelta(days=2)))
 assert db.raw.web_reservation_protocols.find_one({})['state']=='DOCUMENTS_COMPLETE'
 db.raw.web_reservations.update_one({}, {'$set':{'additional_compliance_documents':['source_of_funds']}})
 asyncio.run(protocol.tick(db,row['deadline_at']+timedelta(days=20)))
 assert db.raw.web_reservation_protocols.find_one({})['state']=='DOCUMENTS_COMPLETE'
 assert db.raw.web_reservations.find_one({})['state']=='APPROVED'
 assert db.raw.web_protocol_mail.count_documents({})==0
