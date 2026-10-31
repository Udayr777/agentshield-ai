# Email password recovery

Forgot password links appear on the homepage footer, sign-in/sign-up screens and profile page. The account email must be an inbox the user actually controls; synthetic email identifiers cannot receive mail. No recovery code or emailed password is used.

## Resend setup

1. Create a Resend account and add a sender domain you own. Add the DNS records Resend supplies and wait for verification.
2. Create an email-sending API key. Store it only in the private local `.env` and Render's Environment settings, never in Git, chat or the browser bundle.
3. Configure:

```dotenv
RESEND_API_KEY=<private-email-sending-key>
PASSWORD_RESET_FROM=AgentShield AI <noreply@your-verified-domain.example>
APP_PUBLIC_URL=https://agentshield-ai-lgdd.onrender.com
```

Use the exact trusted app origin, without a path or trailing slash. For local-only email testing use `http://127.0.0.1:5174`; local and hosted links must deliberately point at the intended app. On Render, `RENDER_EXTERNAL_URL` is the fallback when `APP_PUBLIC_URL` is absent. Restart/redeploy after configuration changes.

Resend's default `resend.dev` sender can send test mail only to the email associated with the Resend account. Other recipients require a verified sender domain. See [Resend domain restriction](https://resend.com/docs/knowledge-base/403-error-resend-dev-domain) and [send email API](https://resend.com/docs/api-reference/emails/send-email).

## Flow and boundaries

- The public status endpoint reports configuration presence only, not successful provider authentication or domain verification. An unconfigured recovery page disables send and explains setup is required.
- A request returns the same generic response for existing/unknown accounts, throttling and delivery failures. It does not confirm account existence or email delivery; timing is not guaranteed indistinguishable.
- The service sends only a reset email to the stored account address. No invoices or model APIs are involved. Tokens never appear in API responses, model prompts or application logs.
- Links contain a random 256-bit token in the URL fragment. Only its SHA-256 hash is stored; the trusted origin comes from configuration, never request headers. The recovery screen removes the token from the visible URL after capture; refreshing that screen requires reopening the email link.
- Tokens expire in 15 minutes, are single-use, and supersede earlier tokens. Delivery failure invalidates the token. Requests are limited to one per email/15 minutes and twenty per deployment/hour in the database, including unknown-address requests. Gateway request throttling also applies.
- A successful atomic reset updates the scrypt password hash and revokes all sessions, extension upload tokens, unused simulation approvals, outstanding passkey challenges and reset tokens for that account. It does not delete invoices/audits, enrolled passkeys or stored Gmail connection credentials.
- No automatic sign-in occurs. Return to Sign in and use the new password. Existing email identifiers are not otherwise verified by signup in this prototype.

Verification includes expiry, replay, generic responses, token-hash storage and session revocation tests. Real provider delivery still requires a configured verified sender and an inbox test. No test email is automatically sent during installation.
