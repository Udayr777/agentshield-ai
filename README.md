# AgentShield AI

**Invoice intelligence with a code-enforced authority boundary.** Inspect synthetic invoices, challenge an agent with attacks, and understand the recorded outcome. Models advise; explicit human approval and deterministic controls govern simulations. **No real bank accounts or money movement.**

[Watch the demo video on YouTube](https://www.youtube.com/watch?v=Sm9qTm1qLg8) · [Project post on X](https://x.com/udayramesh007/status/2117922697703514224) · [Open hosted demo](https://agentshield-ai-lgdd.onrender.com/) · [GitHub repository](https://github.com/Udayr777/agentshield-ai)

For a narrated demo, model attribution and practice troubleshooting, see the [rehearsal guide](REHEARSAL-GUIDE.md).

## First-time walkthrough

1. Choose **Sign up**. Use an email you control if you want password recovery. New accounts start empty.
2. Open **Invoice workspace → Start judge demo**. This loads three synthetic invoices: clean, hidden prompt injection and shifted banking layout.
3. Inspect the clean $100 invoice. Click **Review exact simulation**, then explicitly confirm its recipient and amount. Reusing a previously simulated invoice exercises duplicate protection.
4. Follow **Next: select attack fixture → Run recipient-swap review**. Open **Security observatory** and compare original intent with the denied proposal.
5. Select **Ask Muse: why this decision?** for an optional cited explanation, separate from the recorded decision.
6. In **Investigate. Explain. Keep control.**, consent to external processing of synthetic evidence and run the investigation. Inspect the Baseten assessment/provenance and Wonder's three cited storyboard cards.
7. Prepare a synthetic demo share kit. Optionally choose a browser tab to record: silent, maximum 45 seconds, downloaded locally, never automatically uploaded or posted.

Live features require operator-configured credentials and consume provider credits. A failed model request is not evidence of a blocked attack. Gmail imports use a separate local-only path.

## Features

| Area | Included | Boundary |
|---|---|---|
| Accounts | Sign up/in/out, private workspace, profile, session-scoped chat, mailbox verification, branded password-reset emails | Optional mailbox verification; no production identity certification |
| Visual invoice guard | PDF/image upload, editable fields, original/enhanced/anomaly views, geometry anchors, optional Muse extraction and SAM refinement | Local geometry is not SAM; inspect actual provenance |
| Go security gateway | Ten observed controls, exact approvals, expiry, replay prevention and atomic audit | Simulated payments only |
| Chaos/replay | Recipient swaps, oversized transfers, injection and invalid approvals | Scripted attack fixtures and baselines are labeled |
| Invoice copilot | Cited answers about the selected owned invoice | No payment tools or cross-account access |
| Bounded investigation | Read-only tools, Baseten open-weight assessment, Wonder briefing | Maximum four tool selections; only-choice transitions run in code and are labeled |
| Decision evidence | Original/proposed comparison, failed controls, optional Muse explanation, receipt export | Explanations do not change decisions |
| Audit ledger | HMAC-signed event/node chains and exported checkpoints | Tail deletion needs an earlier trusted checkpoint; host/key compromise is outside the guarantee |
| Security frontier | Opt-in shared synthetic signatures, WebAuthn simulated holds, proposed additive policies with benchmark/promotion/rollback | No live financial escrow or automatic gateway code rewriting |
| Gmail | Read-only OAuth, explicit search/attachment import, local cited facts | No background scanning, external-model processing, payment simulation or public sharing of imports |
| Presentation | Muse Image landing/welcome artwork, animated Zivvi, guided demo, public app-help copilot, local explanation clips and screen recording | Browser animation/voice is not Muse-generated video |
| Other tools | Review council, Spark/Wonder comparison, Hall of Scams, synthetic broadcast arena, browser companion | Optional; focused guides linked below |

## Architecture and connected services

```text
React / TypeScript browser
       | same-origin HTTP + session cookie
       v
Go policy gateway ---> authenticated Python service
       |                 | document inspection / model adapters
       +-----------------+--> SQLite or PostgreSQL
                         +--> Meta / Baseten (eligible input only)
                         +--> Resend (password reset email)
                         +--> Gmail (explicit read-only import)
```

| Service | Role | Needed for a new local demo? |
|---|---|---|
| Go 1.24+, Python 3.12+, Node.js 22+/npm | Gateway, backend and React/Vite dashboard | Yes, or use Docker |
| SQLite | Default persistent local storage | Included with Python |
| Neon PostgreSQL | Hosted users, sessions, invoices, approvals and audit | No |
| Render | Combined UI, Go and private Python Docker web service | No |
| Meta Model API | Spark analysis/copilots/extraction, Wonder briefing, optional SAM 3.1 | No; mock mode needs no key |
| Baseten | Muse Spark Open forensic reviewer | No |
| Resend | Branded single-use password-reset links | No |
| Google Cloud/Gmail | Optional read-only OAuth import | No |

The hosted app has operator-configured Render, Neon, Meta, Baseten and Resend settings. **A clone does not include access to those accounts or secrets.** A hosted synthetic Spark/Baseten/Wonder run passed acceptance; the operator confirmed Resend delivery and Gmail import. This is not an uptime or model-quality guarantee. Verify your own deployment.

## Local quickstart: Windows, no API keys

Install Git, Go 1.24+, Python 3.12+, Node.js 22+ and npm. In PowerShell:

```powershell
git clone https://github.com/Udayr777/agentshield-ai.git
cd agentshield-ai
# Fresh clone only: do not overwrite an existing private .env.
Copy-Item .env.example .env
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

Open **http://127.0.0.1:5173**, create an account and click **Start judge demo**. The launcher creates `.venv`, installs Python dependencies, builds Go and installs/starts the dashboard. Initial setup needs network access. Leave the terminal open; **Ctrl+C** stops the processes it launched.

The example configuration uses `ANALYZER_MODE=mock`, `COOKIE_SECURE=false` and no database/model credentials. Mock output is a local heuristic, not live Muse. Live-only features require provider configuration.

| Component | Default |
|---|---|
| Dashboard | http://127.0.0.1:5173 |
| Gateway readiness | http://127.0.0.1:8080/api/ready |
| Private Python health | http://127.0.0.1:8001/health |
| Local database | `agent/audit.sqlite3` |

Vite may choose another dashboard port; read its terminal output. Existing developer sessions may use 5174/8083/8005. Stop older copies to avoid a new dashboard connecting to an old backend. The launcher is Windows-specific; Docker is the packaged alternative.

The launcher reads `.env.local` and `.env`; Python also reads `.env.gmail`. Existing process variables take precedence. Restart after changes. Local service/signing keys are generated privately and ignored by Git. Preserve the ledger key associated with existing signed audit records.

## Optional provider setup

Store values privately in local `.env` or **Render → Environment**. Render settings do not configure localhost. Never put secrets in React code, `VITE_` variables, Git, screenshots or chat.

### Meta and Baseten

```dotenv
ANALYZER_MODE=meta
META_API_KEY=<private-meta-key>
META_BASE_URL=https://api.meta.ai/v1
META_MODEL=muse-spark-1.3
META_SAM_MODEL=sam-3.1
META_MAX_COMPLETION_TOKENS=2048
META_TIMEOUT_SECONDS=45
META_REASONING_EFFORT=low
INVESTIGATION_REPORT_MODEL=muse-wonder-1.0
BASETEN_API_KEY=<private-baseten-key>
OPEN_WEIGHT_MODEL=meta-models/muse-spark-open
```

Use models supported by your account. Baseten calls use `https://inference.baseten.co/v1/chat/completions` and separate provider credits. The standard model ID above succeeded in the hosted test. `.env.example` retains the participant-guide `meta-models/muse-spark-open-1026` alias; that alias returned a missing-model error in this deployment. Explicitly configure your supported ID and confirm prize eligibility with the partner. No automatic model substitution occurs.

A successful partner run says **Live partner response recorded** with provider metadata; configuration presence alone is not proof. Invalid provider responses fail visibly. Missing live risk analysis does not silently become an allowing mock result. Extraction, SAM, copilots, explanations, council and investigation use separate calls. Animations, saved replay playback, local geometry and loading fixtures do not themselves use models.

### Neon PostgreSQL

```dotenv
DATABASE_URL=<private-pooled-url-with-TLS-options>
DATABASE_URL_UNPOOLED=<private-direct-url-with-TLS-options>
```

Startup applies schema migrations. Runtime uses the pooled URL; migrations use the direct URL when supplied. Preserve TLS options. SQLite records are not automatically migrated. Use a separate development database for experiments.

### Resend password recovery

```dotenv
RESEND_API_KEY=<private-sending-key>
PASSWORD_RESET_FROM=AgentShield AI <noreply@your-verified-domain.example>
APP_PUBLIC_URL=https://your-app.onrender.com
```

Verify a sender domain for general delivery. The `onboarding@resend.dev` test sender is restricted to the Resend account owner's address. The recipient must be the email registered in AgentShield. For local testing deliberately set `APP_PUBLIC_URL` to the actual localhost dashboard origin.

Signup attempts a mailbox-verification email when delivery is configured. In **My profile**, inspect verification status or click **Send verification link**. Open the emailed link and explicitly confirm. Verification links expire after 30 minutes and work once; resends invalidate earlier links. Verification is optional for this synthetic demo and does not authorize payments. See [email verification](EMAIL-VERIFICATION.md).

Use **Forgot password**, request the email and open its link. Links expire after 15 minutes and are single-use; successful reset revokes sessions. The generic confirmation does not prove delivery. Inspect Resend delivery/log status and spam if needed. See [password recovery](PASSWORD-RECOVERY.md).

### Gmail and passkeys

[Gmail setup](GMAIL.md) covers Google consent/test users, callback, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` and stable private `GMAIL_TOKEN_KEY`. Even with model credentials, Gmail imports stay local-only. Their local facts copilot does not call Muse.

[Security frontier](SECURITY-FRONTIER.md) covers the exact `WEBAUTHN_ORIGIN` and passkey ceremony for simulated holds. Passkeys do not connect a bank.

## Render deployment

Use the root `Dockerfile`, not the individual Compose service Dockerfiles.

1. Push to GitHub. Create a Render Web Service using Docker and your intended branch. Leave Root Directory blank.
2. Set Docker Build Context `.`, Dockerfile Path `Dockerfile`, Health Check Path `/api/ready`. Leave Docker Command and Pre-Deploy Command blank.
3. Add `DATABASE_URL`, optionally `DATABASE_URL_UNPOOLED`, separate stable random `SERVICE_TOKEN` and `LEDGER_SIGNING_KEY` (at least 32 random bytes each), and `COOKIE_SECURE=true`. Add optional provider settings and your HTTPS `APP_PUBLIC_URL`.
4. Deploy, wait for Live, check the commit in Events, then refresh the website.
5. Create a fresh account, follow Start judge demo and verify persistence across refresh/sign-in.

Python stays on loopback; Go serves the UI and API on Render's `PORT`. Keep signing/encryption keys stable across deploys. Neon stores records; container files are ephemeral. Check provider dashboards for current costs/limits. See [deployment details](DEPLOYMENT.md).

## Docker Compose

Start Docker Desktop's Linux engine, create `.env` as above, then run:

```powershell
docker compose up --build -d
docker compose ps
```

Open http://127.0.0.1:3000. Go is on localhost:8082; Python and PostgreSQL stay internal. Compose uses its own PostgreSQL even when `.env` contains Neon URLs. Data and keys persist in `audit-data` and `service-secret`.

```powershell
docker compose logs --tail 80
docker compose down
```

`down` preserves volumes. Full Docker runtime has not been reverified in this authoring session. Compose currently forwards core Meta settings but not all optional Baseten/Resend/Gmail settings; adding those to `.env` alone does not enable them in Compose. Use the Windows launcher or Render for the full configured stack, or explicitly extend service environment settings privately.

## Verification and measured evidence

Run from the repository root after installing dependencies:

```powershell
.venv/Scripts/python.exe -m unittest discover -s agent -p "test_*.py" -q
Push-Location gateway
go test ./...
Pop-Location
npm --prefix dashboard ci
npm --prefix dashboard run build

# Running mock instance only:
.venv/Scripts/python.exe scripts/check-workspace.py --url http://127.0.0.1:8080
.venv/Scripts/python.exe scripts/benchmark.py --url http://127.0.0.1:8080 --rounds 5 --output benchmark-results.json
.venv/Scripts/python.exe scripts/benchmark-visual.py

# Optional billable synthetic live investigation:
.venv/Scripts/python.exe scripts/check-investigation.py --url https://your-app.onrender.com --live --require-partner
```

Measured local mock results: 35/35 expected outcomes; 0/5 authorized fixtures falsely blocked; median 71.3 ms and p95 100.0 ms including durable SQLite audit. Visual heuristics flagged 12/12 tampered fixtures and 0/3 clean fixtures. These are small synthetic tests, not real-world accuracy or hosted live-model latency. See [benchmark report and raw results](BENCHMARK-REPORT.md).

Browser recording permissions, voice playback, real email delivery and Google consent require manual testing. Private live report exports must not be published. A dashboard build does not prove cloud deployment success.

## Ten observed controls

1. Authenticated session and private invoice ownership.
2. Visual template anchor binding against a trusted synthetic layout; unmeasured for manual invoices.
3. Typed/bounded fields and integer cents.
4. USD 1,000 ceiling plus rolling action/value limits.
5. Registered recipient (`vendor_acme` in the demo).
6. Injection analysis with recorded mock/live/network/unavailable provenance.
7. Approval bound to owner, invoice, recipient and amount.
8. Approval expiry after 120 seconds.
9. Single-use approval and invoice duplicate protection.
10. Audit commit in the authorization transaction.

A model cannot issue approval. Missing, mismatched, expired or reused approvals are denied. Shared synthetic threat matching can deny before risk-model processing; do not attribute that receipt to a live model. Passing all controls is not a safety probability.

Passwords use salted scrypt. Hashed session tokens, HttpOnly/SameSite cookies and logout revocation enforce the login boundary. Chat is scoped to account, invoice and login session; invoice/audit history persists. This prototype does not provide reviewed production identity, complete account erasure or general role separation.

## Troubleshooting

| Symptom | Check |
|---|---|
| No containers | Start Docker Desktop and run Compose from this repository |
| Old hosted UI | Commit in Render Events, deployment Live, hard refresh; localhost is separate |
| Local login fails | `COOKIE_SECURE=false` for HTTP localhost; true for hosted HTTPS |
| Live-only feature unavailable | Meta mode, credentials in the running environment, restart/redeploy |
| Baseten missing model | Supported model ID and account entitlement; see alias distinction above |
| Investigation failed | Read the stage-specific error; fix configuration and start a new run |
| Reset email missing | Registered account address, sender restriction, Resend delivery logs and spam |
| Gmail model disabled | Expected local-only boundary; use synthetic fixtures for live models |
| Upload error | Check format/size/page limits and try a small synthetic fixture |
| Audit signature mismatch | Stable signing key and earlier trusted checkpoint |

## Documentation and scope

- [Benchmark evidence](BENCHMARK-REPORT.md) and [build timeline disclosure](BUILD-TIMELINE.md)
- [Model usage](MODEL-USAGE.md), [investigation](INVESTIGATION.md), [decision explanations](DECISION-INSIGHTS.md)
- [Visual inspection](VISUAL-INSPECTION.md), [Attack & Intercept lifecycle](LIFECYCLE-GUIDE.md)
- [Review council](COUNCIL.md), [Spark/Wonder comparison](MODEL-COMPARISON.md), [Security frontier](SECURITY-FRONTIER.md)
- [Deployment](DEPLOYMENT.md), [password recovery](PASSWORD-RECOVERY.md), [Gmail](GMAIL.md)
- [Extension installation](extension/README.md), [historical validation](VALIDATION.md)

Identify event-built contributions accurately. Commit dates do not prove original authorship. Disclose pre-event work, dependencies and generated assets. Organizer eligibility confirmation remains pending; provider metadata is not an award ruling.

AgentShield is an experimental synthetic finance demonstration, with no production certification, universal injection detection, document authenticity guarantee or host-compromise immunity. Never commit private configuration, OAuth JSON, database URLs, tokens, signing keys, uploads or reset links. Preserve independent trusted checkpoints and rotate exposed credentials.
