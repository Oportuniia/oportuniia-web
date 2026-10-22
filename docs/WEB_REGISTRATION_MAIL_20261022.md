# WEB registration mail

Based on the account service's deployed commit `7cf6ec6`, on a separate branch.
This change does not replace the public website or alter other applications.

The approved confirmation includes a single-use 30-minute link, a plain-text
alternative and an HTML button. User names are escaped. No tracking images.
Password recovery keeps its existing message and token lifecycle.

Set `WEB_MAIL_TRANSPORT=gmail` to use HTTPS rather than SMTP. Required hosting
secrets: `WEB_GOOGLE_CLIENT_ID`, `WEB_GOOGLE_CLIENT_SECRET`,
`WEB_GOOGLE_REFRESH_TOKEN`, and `WEB_MAIL_FROM=OPORTUNIIA <web@oportuniia.com>`.
Missing Gmail configuration does not fall back to a different provider.
Google errors remain generic at the public API; an ambiguous timeout does not
automatically repeat the send. Existing SMTP and bridge users remain compatible.

`scripts/authorize_web_mail.py` obtains a one-time operator authorization for
the exact `gmail.send` scope using a Desktop OAuth client, a loopback callback,
state and PKCE. It must be run locally with a downloaded client JSON and a
secret output path outside this repository. It sends no email. The resulting
secret JSON must go only into the hosting environment, never a commit or chat.
The Google OAuth application's audience/publishing status must be checked before
production use to avoid a test-mode refresh-token expiry.

The alias must be configured in Gmail's Send as settings before delivery.
Registration still requires the existing public origin, privacy/terms versions,
registration switch, database and same-origin website routes.

## Executed validation

2026-10-22: `test_web_identity.py`, `test_web_mail_templates.py`,
`test_web_gmail.py`: **21 passed, 0 failed**. These are local tests using fake
accounts, Mongo mock and simulated Google responses. They are not evidence of
live delivery. Live authorization, deploy and registration-to-inbox verification
remain pending.
