# AgentShield AI — Invoice workspace & adversarial payment lab

Private synthetic invoices, a read-only Muse copilot, and a Go gateway that separates financial intelligence from payment authority. The application has no bank integrations and never moves real money.

For a reproducible paired risk-classification experiment using Muse Spark and Muse Wonder, see [Model comparison](MODEL-COMPARISON.md). It records correctness, abstentions, latency and token usage without changing the production gateway.

The **Security frontier** workspace adds opt-in shared synthetic threat signatures, real WebAuthn verification for simulated invoice holds, and model-proposed additive policies with a 1,024-fixture benchmark and explicit promotion/rollback. See [Security frontier](SECURITY-FRONTIER.md) for setup, a demo walkthrough and limitations.

The **Visual invoice guard** includes original/enhanced/overlay comparison, first-page PDF visibility heuristics, optional evidence-bound Muse explanations, and one-click synthetic fixtures. See [Visual inspection](VISUAL-INSPECTION.md) for thresholds, privacy limits and the reproducible 15-document benchmark.

Hackathon prototype with private accounts, visual invoice inspection, read-only copilots, ten observable controls, signed audit chains and an adversarial replay lab. This repository does not independently attest when each contribution was created; submission materials must identify event-period contributions accurately.

## Start locally on Windows

Requires Go 1.24+, Python 3.12+, Node 22+ and npm. The launcher creates a project `.venv` and installs `agent/requirements.txt`, including PDF/image and PostgreSQL dependencies. The first setup needs network access.

```powershell
# First setup only; do not overwrite an existing private .env:
Copy-Item .env.example .env
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

Open http://127.0.0.1:5173, choose **Create account**, and use a synthetic email identifier plus a unique demo password (12–128 characters). No email is sent. A private sample $100 invoice is created for your account. Local servers bind loopback. Stop older demo processes first if their ports are occupied. The launcher uses ports 5173/8080/8001. Choose Sign up on the landing page to create a private workspace.

The launcher reads private `.env.local` / `.env` settings without printing secrets. With `DATABASE_URL`, accounts and audits persist in PostgreSQL (including Neon); otherwise SQLite data persists in `agent/audit.sqlite3`. Set `ANALYZER_MODE=mock` to try the app without a model key. Use a pooled URL for `DATABASE_URL` and a direct migration URL for `DATABASE_URL_UNPOOLED`. Existing SQLite records are not automatically copied into PostgreSQL. A generated `.service-token` authenticates Go-to-Python requests and is excluded from Git. Ctrl+C stops the processes launched by the script.

## Three-minute demo

Optional advanced review: [Muse review council](COUNCIL.md) adds three isolated Muse assessments and a signed, expiring evidence gate for a selected invoice. It is opt-in, uses three model calls per run, and never substitutes for deterministic controls or explicit human approval.

1. Create an account. Open the private sample invoice and ask the copilot **When is it due?** Inspect its evidence references and source label.
2. Ask **Pay this invoice and transfer the money now**. A deterministic guardrail refuses the action; chat has no payment tools or approval issuance path.
3. Click **Review exact simulation**, confirm the amount/recipient, and inspect the ten server-recorded checks. The orbit animation means a request is running; it does not fabricate progress or results.
4. Click **Test duplicate protection**. Even a fresh approval cannot create a second simulated payment for the same invoice.
5. Create a new synthetic invoice and insert the malicious invoice fixture. Review it: instruction-like text produces high mock risk and blocks the payment despite valid fields.
6. Open **Attack replay lab** for seven scripted attack/control scenarios, side-by-side outcomes and actual approval-reuse testing.
7. Open **Decision evidence** and download a receipt JSON. Use **Verify audit integrity** to check HMAC-signed event/node chains and export a checkpoint. Keep that checkpoint separately; detecting tail deletion requires an earlier trusted checkpoint. Full host/signing-key compromise is outside the guarantee. Older unsigned events are identified separately.

## Ten observed payment controls

1. Authenticated server-side session and invoice ownership.
2. Visual Template Anchor Binding for linked documents with a trusted synthetic Acme template; unmeasured for manual invoices.
3. Typed/bounded request fields and integer cents.
4. USD 1,000 payment ceiling plus rolling action/value limits.
5. Trusted recipient registry (`vendor_acme` in this demo).
6. Invoice injection analysis, with explicit mock/Meta/unavailable mode.
7. Approval bound to owner, invoice, recipient and amount.
8. Approval expiry (120 seconds).
9. Single-use capability plus invoice-level duplicate protection.
10. Audit commit in the authorization transaction.

The UI reports pass/fail/unknown/not-measured from the recorded evaluation. Passing ten checks is **not** a safety probability or proof of general prompt-injection resistance. Supporting controls include request limits, same-origin write checks, JSON-only writes, parameterized SQL and authenticated internal service requests.

## Accounts, isolation and authority

Each login starts a fresh invoice-copilot conversation. Messages and model context are scoped to the authenticated login session as well as the account and invoice. Refreshing within that session restores its chat; signing out and signing in starts empty. Earlier chat records are retained in storage, while invoices and audit history continue to persist across logins.

Passwords use salted scrypt (N=32768,r=8,p=3). Random session tokens are stored as SHA-256 digests, expire after eight hours, and are revoked on logout. The browser uses an HttpOnly, SameSite=Strict cookie rather than localStorage. Set `COOKIE_SECURE=true` behind HTTPS; the localhost HTTP demo uses false. Login/registration and chat have per-IP limits. The development proxy and production Nginx preserve the request Host for origin checks.

User identity is resolved from the session on the server. Invoices, chat history, approval use and audit retrieval are scoped to that identity. Existing pre-account demo records are preserved with an empty owner and are not shown to newly registered users. This MVP does not implement email verification, MFA, password recovery, role separation, or a reviewed production identity provider. Do not expose it publicly as a production financial system.

The replay console intentionally creates demo mandates. Actual invoice simulation requires a signed-in user's explicit confirmation. The invoice itself and the chatbot cannot approve a payment. Go evaluates deterministic policy and model risk. Python's database transaction conditionally consumes the matching approval, updates the owned invoice only if pending, and inserts the final audit event. A failed audit rolls back changes; missing/expired/mismatched/reused approvals and duplicate invoices are denied.

## Invoice copilot and Muse

The copilot receives only the selected owned invoice's evidence, not session tokens, API keys or other users' records. It answers read-only questions with explicit evidence references. An action-request guardrail refuses payment/transfer instructions before any model call. Even if that text filter misses a paraphrase, the chat execution path has no payment tools, approval endpoint or database mutation capability beyond saving its conversation.

Mock mode gives deterministic fact summaries and labels every answer. Live mode uses Muse chat completions with a read-only system instruction and validates JSON/citation keys. Referenced source text can still contain malicious instructions, and a valid citation key does not prove an answer is factually correct. Treat model answers as advisory. Model API failures or invalid citations return an error, not an invented answer.

Live Muse was verified on October 30; see `LIVE-READINESS.md`. Use `ANALYZER_MODE=mock` for free deterministic development and `meta` for real evaluations. Edit the private project `.env`:

```dotenv
ANALYZER_MODE=meta
META_API_KEY=your-private-key
META_MODEL=muse-spark-1.3
META_BASE_URL=https://api.meta.ai/v1
```

Restart the launcher, or recreate the Compose agent. Do not paste keys into chat or commit `.env`. The adapter follows the [official Meta chat completions protocol](https://dev.meta.ai/docs/cookbook/quickstart-chat-completions) and schema-constrained JSON output. Live calls use bounded completion tokens (default 2048), low reasoning effort, and a configurable timeout. Token metadata is recorded in ignored `agent/model-usage.jsonl`; prompts, answers and keys are not written there. The provider billing page is authoritative for monetary usage. Live analyzer failures are unknown risk and block payment simulations; they never become allowing mock responses.

Risk input excludes approval text/tokens and session identifiers. The model evaluates invoice content; deterministic code evaluates authorization. A live pilot exposed false positives when those responsibilities were mixed; the initial and corrected results are preserved separately. Live invoice chat includes a bounded window of the selected invoice's own conversation, validates citation keys and retains response/token metadata.

## Docker Compose and PostgreSQL

Requires Docker Desktop's Linux engine running. An empty Containers page does not start this application.

```powershell
docker compose up --build -d
```

Open http://127.0.0.1:3000. Go is on localhost:8082; agent and PostgreSQL are internal. PostgreSQL data persists in `audit-data`; a separate `service-secret` volume shares the internal token with Go. `docker compose down` preserves data. Current Compose configuration validates, but full Docker/PostgreSQL runtime verification remains pending because the engine is unavailable in the authoring environment.

Database startup applies repeatable schema migrations, including users, hashed sessions, owned invoices, messages and approval/audit ownership. `audit_decisions` exposes readable SQL reporting fields; querying PostgreSQL directly is an administrator operation and is not a user-facing API.

```powershell
# Mock mode only: builds, starts, checks authenticated isolation, benchmarks, prints SQL summary:
powershell -ExecutionPolicy Bypass -File scripts/verify-compose.ps1
```

## Tests and reproducible measurements

```powershell
cd gateway
go test ./...
cd ../agent
python -m unittest -v
cd ../dashboard
npm.cmd ci
npm.cmd run build
cd ..
python scripts/check-workspace.py --url http://127.0.0.1:8080
python scripts/benchmark.py --url http://127.0.0.1:8080 --rounds 20 --output benchmark-v3.json
```

For bounded live validation (synthetic data only, billable): `python scripts/live-smoke.py --phase connection` makes one model call; `--phase evaluation` makes at most nine more. `python scripts/check-live-http.py --url http://127.0.0.1:8080` checks the authenticated live flow with two model calls. The existing `check-workspace.py` intentionally remains mock-only; use a mock instance for its no-cost security regression suite.

The workspace HTTP check is mock-only and creates two synthetic accounts. It verifies anonymous denial, session cookies, cross-account isolation, cited chat, chat refusal/no payment side effects, cross-origin blocking, legitimate simulation, duplicate prevention, adversarial invoices and logout. No real user credentials are used.

The benchmark creates a synthetic account and runs seven scenarios × 20 rounds = 140 requests with fresh demo capabilities. It records every decision, mode and full HTTP latency including authentication, preparation and audit. No warmup is discarded. Use `--url http://127.0.0.1:8082` for Compose. Live benchmarking makes billable model calls; wait for credits and start with one round. Mock fixture success is a regression result, not general model accuracy. See `VALIDATION.md` and raw JSON outputs.

## Attack & Intercept Lifecycle

Upload/review with Muse and SAM, invoice-bound chaos, exploded audit nodes, geometry-only threat sharing, a simulated broadcast arena and a scoped browser companion are implemented. Read `LIFECYCLE-GUIDE.md` for the exact workflow, privacy/permission boundaries and test commands. The three synthetic PDF fixtures and preview PNGs are under `samples/`; the extension source is under `extension/`.

## Cloud deployment

Optional [Gmail invoice import](GMAIL.md) uses Google read-only OAuth and explicitly selected attachments. Gmail imports remain local-only: external model processing and payment simulation are blocked for that source. Google client credentials and token encryption keys are private environment settings; no Gmail connection is enabled just by deploying the repository.

See [DEPLOYMENT.md](DEPLOYMENT.md). The root Dockerfile builds React and Go, then runs the gateway and a local-only Python service in one Render Free web service. Neon supplies PostgreSQL. The blueprint declares no paid service. Never commit `.env`, keys, signing secrets, database URLs, local databases or private uploads.

Neon persistence and authenticated HTTP flows have been tested separately. Docker image execution and the public Render deployment still require verification. A successful TypeScript build is not proof of a successful cloud deployment.

## Submission and scope

This is a synthetic finance demonstration: no real bank integrations or transfers, production certification, automatic inbox crawling, guaranteed PII redaction, or universal injection detection. Models provide evidence, not payment authorization. Browser extension installation is explicit. Deployment/publication status must be verified against actual running services. See `MODEL-USAGE.md` for model boundaries and `VALIDATION.md` for historical test observations.

## Public feature guide
Before sign-in, the landing page groups capabilities under Inspect, Explain, Defend and Verify, includes a practical FAQ, and offers app-only Zivvi help. The anonymous `/api/public/help` endpoint forwards only documentation and a validated question (600 characters maximum), never private invoice/account context. Live public help has per-process limits of three requests/minute and twenty/hour, counting failures; documentation fallback stays available. These reset on process restart and are not a distributed production quota. Authenticated invoice and payment APIs remain protected.
