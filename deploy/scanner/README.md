# Private document scanner: awaiting cost approval

This is a prepared deployment, not a verified running antivirus. No service has
been purchased. WEB uploads remain disabled until the real journey passes.

Render cron setup:
- Repository: Oportuniia/oportuniia-web
- Branch: feat/web-registration-mail-20261022
- Name: oportuniia-web-document-scanner
- Region: Frankfurt
- Docker context: repository root
- Dockerfile: deploy/scanner/Dockerfile
- Schedule: hourly, at minute 7 (UTC).
- Compute: 2 CPU / 4 GB, subject to approval.
- No public endpoint. Local ClamAV only; document bytes never sent to an antivirus API.
- Copy WEB's MONGO_URL, DB_NAME and the seven WEB_PERSONAL storage/encryption
  variables through Render secrets, not this repository. Set
  WEB_PERSONAL_UPLOADS_ENABLED=true for the scanner only. Keep the WEB flag false
  until validation. Never copy mail, payment or unrelated ecosystem credentials.

Each run refreshes official signatures, processes at most 100 documents with a
10-minute loop budget, and exits. The outer process has a 15-minute deadline
(plus a 10-second kill grace). Timed-out documents retain quarantine and can be
reclaimed after their lease expires. Failed scans retry five times at most.
Human review and operation permissions are independent of scanner results.

Current Render published 4 GB cron rate: $0.00197/minute; minimum $1/month.
744 hourly runs at the full 15-minute limit = approximately $21.99 in a 31-day
month, excluding startup/build costs, taxes and manual runs. This is NOT a
provider-enforced billing cap. Actual runtime must be measured before predicting
normal cost. A continuously running 4 GB service is $85/month instead.

No-cost software alternative: run this container on an existing always-on
server with at least 3-4 GB spare memory. No suitable existing host has been
verified. The current 512 MB Render services cannot meet this recommendation.

Release gates after explicit approval:
1. Build container and verify fresh signatures and clean test file detection.
2. Verify official antivirus test signature is rejected (no actual malware).
3. Upload a synthetic PDF through the authenticated WEB route; observe durable
   encrypted quarantine, scan result, authorized retrieval, and cross-user denial.
4. Verify reviewer MFA, revision checking, and separate human approval.
5. Enable WEB uploads only after these gates pass; never seed a CLEAN verdict.

References: https://render.com/pricing, https://render.com/docs/cronjobs,
https://docs.clamav.net/Introduction.html
