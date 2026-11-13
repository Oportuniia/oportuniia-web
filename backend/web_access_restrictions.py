"""Private access restrictions; never use name-only matching."""
import re


def identifiers(user, profile=None):
    profile = profile or {}
    keys = [{'subject_id': user['subject_id']}] if user.get('subject_id') else []
    if user.get('email'): keys.append({'email': user['email'].strip().lower()})
    for field in ('tax_id', 'company_tax_id', 'representative_id'):
        value = re.sub(r'[^A-Z0-9]', '', str(profile.get(field, '')).upper())
        if value: keys.append({'tax_id': value})
    return keys


async def blocked(db, user, profile=None):
    if user.get('subject_id'):
        stored = await db.web_users.find_one({'subject_id': user['subject_id']})
        if stored: user = stored
    if user.get('dossier_removed') or user.get('access_blocked'): return True
    if profile is None and user.get('subject_id'):
        draft = await db.web_profile_drafts.find_one({'subject_id': user['subject_id']}) or {}
        profile = draft.get('profile', {})
    keys = identifiers(user, profile)
    return bool(keys and await db.web_registration_blocks.find_one({'active': True, '$or': keys}))
