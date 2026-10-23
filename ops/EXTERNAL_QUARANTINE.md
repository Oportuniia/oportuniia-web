# External document quarantine

Prepared, not yet enabled for WEB. Do not set WEB_SCAN_MODE=guardduty-s3 until IAM, CORS and both deployments have passed live checks.

AWS account 257719178923; region eu-north-1; bucket oportuniia-document-quarantine-257719178923; GuardDuty plan 6ad0b4b2f8efa803eca0. Public access blocked; SSE-S3; versioning enabled. GuardDuty tags each scanned version.

WEB requires a dedicated non-console credential with permissions restricted to incoming/* in this bucket:
- PutObject (presigned POST is size/checksum/type bound and lasts 300 seconds).
- GetObjectTagging and GetObjectVersionTagging.
- GetObject and GetObjectVersion ONLY when s3:ExistingObjectTag/GuardDutyMalwareScanStatus equals NO_THREATS_FOUND.
- Explicitly deny PutObjectTagging, PutObjectVersionTagging, DeleteObjectTagging and DeleteObjectVersionTagging for this principal.
- No access to other buckets, IAM or GuardDuty administration. Do not use root credentials.

CORS: AllowedOrigins https://oportuniia.com and https://www.oportuniia.com, AllowedMethods POST, AllowedHeaders *, MaxAgeSeconds 300. No public bucket policy.

Required WEB environment: WEB_QUARANTINE_BUCKET, WEB_QUARANTINE_REGION, WEB_QUARANTINE_ACCESS_KEY_ID, WEB_QUARANTINE_SECRET_ACCESS_KEY, WEB_SCAN_MODE=guardduty-s3. Existing private R2 configuration remains the final encrypted storage. Do not log credentials or signed upload forms.

Maximum 20 MiB includes originals. ZIPs not accepted. The document record pins the scanned S3 version; a later overwrite cannot substitute bytes. A SHA-256 mismatch, missing verdict, scan failure or unsupported content never promotes bytes. A clean result does not approve identity, account activation or investment access.

The frontend checks pending documents when the profile opens. Continuous background reconciliation, retention lifecycle and operational alerts remain to be connected and tested before calling the overall workflow complete.

Validation so far: 39 local tests passed (quarantine, storage, scan recovery, identity). After tightening tag-first inspection, 17 quarantine tests passed again. These tests simulate AWS and Mongo. One real innocent-file scan completed in AWS; EICAR and direct browser upload integration remain pending. No personal document uploaded in tests.
