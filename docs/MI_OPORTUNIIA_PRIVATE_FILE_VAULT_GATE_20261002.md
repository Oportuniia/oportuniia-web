# MI OPORTUNIIA · Private file vault implementation gate
State: sandbox technical scaffold only. NOT deployed, usable or provisioned.

## Existing and proposed hosting
- WEB application/backend: existing Render service.
- Private user metadata and access audit: existing WEB MongoDB Atlas, dedicated collections `mi_user_files`, `mi_file_events` (pending migration).
- Personal documents: **new dedicated PRIVATE Cloudflare R2 bucket**; never CORE or PRESENTACIÓN production buckets. Bucket not yet created and no credentials installed.
- Files persist in R2, not the Render instance; Render is stateless.
- This is completely independent of LEGAL LAB, judicial dossiers, and PRESENTACIÓN PDFs.

## Isolated module in this branch
`backend/personal_document_storage.py` implements short-lived scoped R2 PUT/GET signing, immutable unguessable IDs, actor-based namespace and fail-closed configuration checks. Not mounted on an API route. No browser/client may select their own actor ID: only the future server-side investor identity verifier may construct its scope.
`backend/tests/test_personal_document_storage.py` adds isolation checks; CI verification still pending.

## Authorization and upload flow required before activating
1. Audit existing WordPress/LeadConnector validated investor identity; design trustworthy short-lived WEB session associated with stable sovereign actor_id and revocation.
2. POST /api/mi/documents/upload-intent, using verified WEB investor session and CSRF/abuse defenses, exact MIME and file size declarations, quota checks. Create Mongo PENDING row for actor; issue URL for own namespace only. Never expose internal R2 keys, credentials or other users' metadata.
3. Browser uploads directly via time-limited R2 presign; configure restrictive private bucket CORS for permitted WEB origin. Disable public bucket access.
4. POST /api/mi/documents/confirm: backend checks object exists, actual content length/magic MIME, quota, ownership, malware scanning or quarantine, digest and state; only then mark AVAILABLE. The scaffold currently validates DECLARED size, which does not enforce actual upload byte limits: require post-upload verification and immediate rejection/removal for mismatches; optionally use POST policy constraints if supported.
5. GET /api/mi/documents lists **only actor's own** documents; GET /api/mi/documents/{file_id}/download loads document Mongo row scoped by actor_id first, uses 60-second download authorization and `Cache-Control: no-store`. Keep GET URLs out of analytics/logs; prohibit cross-user request. Log reads minimally with retention.
6. Encryption, backup/export, versioning, lifecycle, deletion policy, incident response and GDPR legal basis/data processor agreements to be reviewed before production. Keep originals and confirmed organized derivatives distinct.
7. Document organizer and reminders added later as isolated workers; n8n receives limited metadata events only, NEVER private file bytes or R2 secrets.

## 750-concurrent-user target
Not benchmarked. Need baseline real Render instance count/plan, Mongo tier, R2 quotas and load test using 750 virtual users across view/list/download/upload profiles in **separate sandbox**. Downloads should be R2 temporary URLs and not proxy bytes via Render. Verify per-user permissions under concurrency, error rate, p95 latency, and cost. 750 simultaneous browsing users cannot be equated to 750 simultaneous downloads/uploads or OCR jobs. No capacity guarantee before measured test.
