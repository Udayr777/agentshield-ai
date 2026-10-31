# Read-only Gmail invoice import

This connector is application code, not the assistant's Gmail account connector. Users authorize their own Gmail account in Google OAuth, search explicitly, choose an attachment, and import a private draft. It cannot send, edit or delete Gmail messages, and does not run a background mailbox scan.

## Deployment setup

1. In Google Cloud, enable Gmail API. Configure an External OAuth app in Testing, add your test Gmail account, and declare `https://www.googleapis.com/auth/gmail.readonly` under Google Auth Platform → Data Access. This is a restricted scope; broader public access requires Google's applicable verification process.
2. Create a Web application OAuth client. Authorized redirect URI: `https://YOUR-APP.onrender.com/api/gmail/callback`. Leave JavaScript origins blank for this server-side flow. Download its JSON to ignored `.gmail-oauth-client.json` locally.
3. Install the current `agent/requirements.txt`. Run `python scripts/prepare-gmail-env.py` to create ignored `.env.gmail`. It contains `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, and `GMAIL_TOKEN_KEY`. Import those four private settings into Render; do not commit or paste their values in chat. Keep the encryption key stable. A cloud instance without an explicit key disables the connection instead of creating an ephemeral replacement key.
4. Deploy the new commit. Set the Google branding homepage/privacy links to the deployed app and `https://YOUR-APP.onrender.com/#privacy` as appropriate. Read and confirm that the data notice reflects your actual operation before broader release.
5. Sign in to AgentShield at its hosted origin, open **Gmail invoice import**, read the notice and click **Connect Gmail**. Complete consent yourself in Google using an added test account. A local preview cannot complete a hosted-only callback; either use the hosted app or explicitly register/configure a separate local callback.
6. Search, select an email, then click **Import this attachment**. Only PDF/PNG/JPEG up to 4 MB are accepted. Review local geometry and fields in Visual invoice guard. No automatic invoice authorization occurs.

## Security and privacy boundaries

- Authorization code flow uses Google's OAuth library, PKCE S256, a ten-minute random state hashed in storage, single-use state consumption and binding to an active AgentShield session. The callback uses fixed application routes and strips the authorization code via a same-origin redirect. Codes and tokens are not logged.
- OAuth access/refresh credentials and pending PKCE verifiers are encrypted with Fernet in PostgreSQL, with an owner-binding inside the encrypted value. The key is separate from ledger signing. Protect it in private environment settings; this does not protect against a fully compromised application host.
- Gmail profile address, imported documents and extracted fields are private account data. Document contents are not application-level encrypted. The database uses its configured transport TLS. Search retrieves at most ten candidate messages and selected attachment bodies; raw email HTML is never rendered or executed.
- Imports are deduplicated by owner/source and owner/content digest. Only explicit clicks create drafts. Sender, subject and invoice content remain untrusted. Selecting an email does not prove the invoice's authenticity.
- Disconnect deletes stored OAuth credentials and pending requests, then attempts Google token revocation. If remote revocation fails, remove access in [Google Account connections](https://myaccount.google.com/connections). Disconnect does not delete imported records.
- Unconfirmed Gmail drafts can be deleted in-app without altering the source email. Confirmed invoice/audit records are retained separately; complete account erasure is not implemented in this prototype. The public data notice states this limitation.

## Model-processing boundary

Gmail-derived documents are marked `source=gmail` and confirmed invoices preserve that origin. The server blocks their Muse risk analysis, invoice chat, review council, SAM refinement and public gallery contribution. The UI labels the local-only boundary. Payment simulation for these records is denied even if a caller presents a fabricated low-risk assessment. This restriction is independent of the standard synthetic demo workflow.

Google Workspace's data policy restricts generalized AI/ML training or improvement using API data. The configured Meta free-credit notice permits product-improvement use, so model transfer stays disabled for this connector until provider terms and processing configuration are reviewed. User consent alone is not treated as overriding those restrictions. Manually uploading/copied content outside the managed connector is not provenance detection.

## Validation and limitations

`python -m unittest discover -s agent -p "test*.py"` covers PKCE, encrypted owner-bound credentials, callback replay, logout invalidation, explicit selection, deduplication, private draft deletion and external-model blocks. Tests use synthetic PDF attachments and mocked Google network responses. The UI build and Go checks are separate. A real Google consent and mailbox import must still be completed by a test user after deployment; no live mailbox access is claimed from automated unit checks.

Development validation passed 31 Python tests, Go tests and the production UI build. `python scripts/check-gmail.py --url http://127.0.0.1:8083` passed seven HTTP checks against the local gateway and Neon-backed service, with zero Google mailbox calls and zero model calls. It verified private configuration loading, anonymous denial, read-only PKCE authorization URL construction, disconnected-search rejection and callback failure after logout. Visual browser verification and real Google consent remain separate acceptance steps.

Source references: [OAuth web-server flow](https://developers.google.com/identity/protocols/oauth2/web-server), [Gmail scopes](https://developers.google.com/workspace/gmail/api/auth/scopes), [attachments](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages.attachments), [Workspace data policy](https://developers.google.com/workspace/workspace-api-user-data-developer-policy).
