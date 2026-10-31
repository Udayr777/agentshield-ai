# Security frontier

Open **Security frontier** after signing in. These features extend the synthetic sandbox; no bank accounts or real money are connected.

## Shared synthetic threat intelligence

1. In two separate test accounts, explicitly enable the shared filter.
2. Load the Judge Demo Pack in account A and review its hidden-injection invoice. A high-risk denial of an unchanged server-owned fixture can enroll its fixed attack categories.
3. In account B, review the matching fixture. A known category signature blocks the proposal before a model call.
4. Open `/#network` to inspect the public category feed and download its signed checkpoint.

Only fixed category labels enter the feed, never invoice text, names, document hashes, geometry, or account IDs. Personal uploads and Gmail imports cannot enroll. Entries are hash-chained and HMAC-signed using the existing ledger key. This is a shared registry within one deployment, not a decentralized ledger or proof of immunity. Pattern matching is a heuristic. A signed checkpoint needs independent retention to detect removal of the entire feed or its tail; compromise of the signing key defeats authenticity.

## Passkey-gated synthetic holds

1. Use the deployed HTTPS app in a WebAuthn-compatible browser.
2. Register a passkey; the authenticator must perform user verification.
3. Select a pending synthetic invoice and create a hold.
4. Release it using the passkey. The server validates origin, RP ID, challenge, session, owner, signature and counter. It binds a short-lived single-use approval to the exact invoice, recipient and amount.
5. The ordinary model, policy and durable-audit checks still run. A valid passkey does not override a denial.

Holds expire after ten minutes. Challenges expire after two minutes and are consumed even when verification fails. If a release is interrupted, its authorization may remain in progress for up to two minutes; inspect the hold, wait for that window, then cancel/recreate it. Cancelling an optional hold returns the invoice to the ordinary simulation workflow.

`WEBAUTHN_ORIGIN` can explicitly set the exact public origin, e.g. `https://agentshield-ai-lgdd.onrender.com` (no trailing slash). Otherwise the server uses Render's external URL, the Gmail callback origin, or `http://localhost:5174`. An origin mismatch disables the browser action. Localhost and 127.0.0.1 are different origins.

User verification can use a PIN or a biometric. Synced passkeys are allowed. No hardware-only credential, HSM attestation, legal escrow, phone notification or bank settlement is claimed. Hold signatures detect payload modification, not deletion of the requirement by a fully privileged database administrator. Browser/device testing is required in addition to software cryptographic fixtures.

## Adversarial policy studio

1. In live Meta mode, request a policy proposal. This makes one model call using aggregate synthetic categories and a finite JSON schema, with no private invoice data.
2. Inspect the proposed deny categories, amount cap and deterministic benchmark.
3. Explicitly promote an eligible candidate. Promotion re-verifies its signature and reruns the benchmark.
4. Roll back to remove the additional policy. Base gateway controls remain in effect.

Candidates can only add category denials or lower the existing amount ceiling. They cannot authorize a payment, execute code, rewrite the gateway, or relax its original controls. Requests are limited to one per account per ten minutes and ten per deployment per hour, including failed requests.

The benchmark is 1,024 deterministic fixture variations, not 1,024 independent attacks, an end-to-end latency test, a formal proof or a real-world accuracy estimate. The actual model and usage are recorded. `POLICY_MODEL` optionally selects another model supported by the configured Meta-compatible endpoint; by default it uses `META_MODEL`. No Llama fine-tuning is implemented or implied.

## Verification

`agent/test_frontier.py` tests cross-account pre-model blocking, privacy restrictions, signed policy promotion/rollback, and real P-256 WebAuthn signature verification including origin and challenge replay rejection. It uses an isolated SQLite database; deployment startup creates the corresponding PostgreSQL tables. Run the full Python suite and `go test ./...`, then `npm run build` before publishing.

Local gateway + Neon + live Meta verification on October 31, 2026: account A's synthetic hidden-injection review was denied in `meta` mode; account B's matching review was denied in `network` mode. A live `muse-spark-1.3` policy proposal used 1,551 tokens, passed all 1,024 fixture variations (512 benign / 512 attack, zero false blocks), and was explicitly promoted then rolled back. An ordinary review could not release a held synthetic invoice without its passkey authorization. The unauthenticated public feed returned the category signature. This was a bounded local integration check against Neon, not a hosted browser/device passkey test or a production performance benchmark.
