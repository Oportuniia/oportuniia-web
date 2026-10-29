"""Non-sensitive correction codes; never exposes OCR text or another identity."""
CODES = {'READABLE_ID_REQUIRED', 'LEGAL_NAME_MISMATCH', 'ID_NUMBER_MISMATCH',
         'BIRTH_DATE_MISMATCH', 'VALID_ID_REQUIRED', 'COMPANY_DOCUMENT_REQUIRED'}

def correction_codes(results, company):
    identities = [r for r in results if r.get('legible') and r.get('identity') and not r.get('fictitious')]
    codes = []
    if not identities:
        codes.append('READABLE_ID_REQUIRED')
    else:
        for field, code in [('name_matches','LEGAL_NAME_MISMATCH'),('number_matches','ID_NUMBER_MISMATCH'),
                            ('expiry_read_and_valid','VALID_ID_REQUIRED')]:
            if not any(r.get(field) for r in identities): codes.append(code)
        if not company and not any(r.get('birth_matches') for r in identities): codes.append('BIRTH_DATE_MISMATCH')
    if company and not any(r.get('legible') and r.get('fiscal') and r.get('company_matches') and not r.get('fictitious') for r in results):
        codes.append('COMPANY_DOCUMENT_REQUIRED')
    return codes
