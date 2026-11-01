# Email ownership verification

## Configure

Verification reuses the existing Resend credentials and sender: `RESEND_API_KEY`, `PASSWORD_RESET_FROM` and the trusted `APP_PUBLIC_URL` (or Render external URL fallback). No additional key is required. The sender name is reused for verification and recovery. Use your own verified domain for arbitrary recipients; Resend's test sender only reaches the Resend account owner. No mail is sent by installation or migrations.

## User flow

1. Signup creates the account and session. When email delivery is configured, a best-effort background task requests the verification email. An interrupted send does not destroy the new account.
2. Open My profile for verified/unverified status and explicit resend. Unconfigured instances show that sending is unavailable.
3. Open the email link and explicitly click Confirm email ownership. Merely loading the link does not consume it. No automatic sign-in or password change occurs.
4. Reopen/refresh My profile to see verified status. Opening the verification screen removes the raw token from the visible URL; refresh requires reopening the original email link.

Existing accounts are unverified until a link is confirmed. Verification is optional for this synthetic sandbox; unverified accounts remain usable. This feature confirms mailbox access, not legal identity, certification, financial authority or invoice authenticity. Email changes remain unsupported by the UI.

## Security and delivery

- Random 256-bit token, SHA-256 hash stored, 30-minute expiry, single-use atomic confirmation. Tokens never appear in API responses or model inputs.
- Token binds the server-resolved account and exact registered email. Changed email invalidates the old link; frontend data cannot mark verification complete.
- Authenticated request endpoint accepts no recipient override. Only the account's stored email receives the message.
- New sends supersede prior links. One-minute cooldown, three per account/hour and twenty globally/hour, including failed deliveries. PostgreSQL uses an advisory transaction lock; SQLite uses the process lock and transaction.
- Delivery failure invalidates the token and returns a safe error for manual requests. Signup background failures do not expose provider details; use profile resend and provider logs.
- Confirmation creates no session, approval or payment receipt. The mail text and HTML distinguish ownership from authority.
- Public confirmation endpoint is JSON POST behind the normal gateway origin/request limits. Verification is not consumed by GET/email previews.

## Acceptance after deployment

1. Confirm the deployed commit, then create an account with an inbox allowed by your sender configuration.
2. In Resend, inspect a message titled Verify your AgentShield email. Provider acceptance is not proof of inbox delivery.
3. Open the message, confirm, and refresh the profile: Email verified should appear.
4. Try the same link again: it must be rejected. Check resend cooldown and a second account's isolated state.
5. Check Forgot password still works separately. Use synthetic invoices to confirm payment controls are unchanged.

Automated tests mock Resend; they do not prove real mailbox delivery, browser email-link behavior or production deliverability. A verified sender domain remains an operator task. Registration without mail configuration remains available for local mock development.
