"""Irreversible dossier erasure. Never report success after a storage failure."""
import asyncio
from datetime import datetime, timezone

import web_personal_storage as storage
import web_quarantine as quarantine


def erase_objects(row):
    if row.get('storage_bucket') and row.get('storage_key'):
        storage.client(row.get('storage_backend')).delete_object(
            Bucket=row['storage_bucket'], Key=row['storage_key'])
    if row.get('quarantine_bucket') and row.get('quarantine_key'):
        # Delete every version of this exact object, not just a delete marker.
        client = quarantine.client()
        bucket, key = row['quarantine_bucket'], row['quarantine_key']
        for page in client.get_paginator('list_object_versions').paginate(Bucket=bucket, Prefix=key):
            for item in page.get('Versions', []) + page.get('DeleteMarkers', []):
                if item['Key'] == key:
                    client.delete_object(Bucket=bucket, Key=key, VersionId=item['VersionId'])


async def purge(db, subject):
    stamp = datetime.now(timezone.utc)
    target = await db.web_users.find_one({'subject_id': subject}) or {}
    await db.web_users.update_one({'subject_id': subject}, {'$set': {
        'active': False, 'dossier_removed': True, 'purge_started_at': stamp}, '$inc': {'session_version': 1}})
    await db.web_sessions.update_many({'subject_id': subject}, {'$set': {'revoked': True}})
    await db.web_profile_drafts.update_one({'subject_id': subject}, {'$set': {'state': 'WITHDRAWN'}})
    await db.web_access_reviews.update_one({'subject_id': subject}, {'$set': {'revoked': True}})
    await db.web_personal_documents.update_many({'subject_id': subject}, {'$set': {'deleted': True}})
    # Retain object coordinates until every physical deletion succeeds, allowing retries.
    rows = await db.web_personal_documents.find({'subject_id': subject}).to_list(10000)
    if any(row.get('scan_state') == 'PROMOTING' and row.get('promotion_until') and
           row['promotion_until'] > stamp for row in rows):
        raise RuntimeError('document_write_finishing')
    for row in rows:
        await asyncio.to_thread(erase_objects, row)
    for name in ('web_personal_documents', 'web_profile_drafts', 'web_verified_profiles',
                 'web_workspace_settings', 'web_access_reviews', 'web_review_requests',
                 'web_notifications', 'web_sessions', 'web_identity_tokens',
                 'web_login_challenges', 'web_entitlements', 'web_operation_grants'):
        await getattr(db, name).delete_many({'subject_id': subject})
    # Keep the non-restorable account tombstone to prevent bootstrap recreation.
    await db.web_users.update_one({'subject_id': subject}, {'$set': {
        'purge_completed': True, 'purged_at': stamp, 'name': 'Expediente eliminado',
        'bootstrap_username': target.get('username'), 'username': 'deleted.' + subject,
        'email': 'deleted+' + subject + '@invalid.example'},
        '$unset': {'password_hash': '', 'mfa_secret': '', 'mfa_pending': '',
                   'mfa_recovery_hashes': '', 'recovery_email': ''}})
    # Veto records and transaction/audit records are independent of the dossier.
    return {'saved': True, 'action': 'PURGE', 'permanently_deleted': True}
