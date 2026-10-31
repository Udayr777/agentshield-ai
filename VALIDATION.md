# Validation — October 29, 2026

Verified on Windows 11 with Go 1.24.3, Python 3.12 and a local Vite dashboard.

- Go policy and HTTP interception tests pass. Includes missing/ambiguous approvals, invalid amounts, untrusted recipient, model failure, unrecognized analyzer mode, malformed input, and unavailable audit storage.
- Python mock analysis and live failure tests pass.
- TypeScript checking and production dashboard build pass.
- Local end-to-end benchmark: 20 rounds × 5 scenarios, 100/100 expected decisions, 20 allows and 80 denies.
- Sequential HTTP latency including SQLite audit: p50 **23.60 ms**, p95 **46.05 ms**. Analyzer: **mock**. No warmup discarded. Raw measurements: `benchmark-results.json`.
- Browser verification: dashboard loaded all scenarios and audit history; clicking Authorized payment created a new visible ALLOW mock event.

Not verified: real Meta calls (credentials/credits pending), PostgreSQL runtime, Docker image builds and full Compose startup (Docker engine not running). Mock outcomes are fixture regression results, not model accuracy evidence. Go's internal `duration_ms` excludes audit write and differs from the benchmark's full HTTP duration.

## October 30 follow-up

- Fixed connection cleanup: transactions commit/rollback and connections always close.
- Added idempotent PostgreSQL schema migration, insertion timestamp index and `audit_decisions` reporting view. Existing audit payloads are preserved.
- Added persistence regression test: reconnect/read, duplicate rejection, rollback isolation. All three Python tests pass.
- Go tests pass after requiring an explicit `saved: true` audit acknowledgement.
- Compose configuration validates. Compose gateway moved to localhost:8082 to avoid the development server on 8080.
- Local launcher now reads approved settings from `.env` without printing secrets.
- Added `scripts/check-postgres.py` and `scripts/verify-compose.ps1` for real database verification.
- Docker start returned success but the engine never became available; WSL status returned access denied. A portable PostgreSQL initialization also stalled and was stopped. Real PostgreSQL runtime verification and live Meta verification remain pending. No claim of PostgreSQL benchmark results is made.

## October 30 adversarial replay upgrade

- Replaced the hard-coded $125 approval string with a random server-issued capability bound to recipient and integer USD cents, expiring after 120 seconds and consumable once.
- Approval consumption and audit insertion share one transaction. A database authorization failure downgrades the response and saved event to DENY.
- Added seven replay fixtures and a side-by-side scripted unguarded/protected comparison, editable payment amount, inspectable evidence and history.
- Added an actual duplicate-payment request button after successful payment simulation.
- Four Python tests pass, including simultaneous consumption (one allow), mismatch/expiry rejection, and audit failure rolling back token consumption. Go tests pass; TypeScript and production build pass; Compose config validates.
- Browser verified $100 recipient redirect: scripted baseline would send to attacker_wallet; gateway blocked it, and the audit event appeared.
- Local preview for this run uses dashboard 5174, gateway 8083 and agent 8002 to avoid existing development processes. Standard launcher defaults remain 5173/8080/8001.
- Model calls remain disabled in the running upgraded demo (`mock`). PostgreSQL runtime and real Meta evaluation are still unverified.
- Updated sweep: 140/140 expected decisions (seven fixtures × 20 rounds), full round-trip p50 47.93 ms / p95 68.35 ms, Windows local SQLite + mock. Raw results are in `benchmark-v2.json`; these are not Meta accuracy measurements.
- Browser verified an actual successful $100 payment followed by a second request using that same approval: the second request was denied as already consumed.

## October 30 authenticated invoice workspace

- Added persistent accounts with salted scrypt hashes, hashed eight-hour sessions, HttpOnly/SameSite cookies and logout revocation. Added per-IP limits, same-origin/JSON write checks and service-to-service authentication. Cookies require `COOKIE_SECURE=true` for HTTPS deployment; demo remains loopback HTTP.
- Added per-account invoices, messages, audit records and approval ownership. Existing unowned demo records are preserved and hidden from newly registered users.
- Invoice chat is read-only, scoped to an owned invoice, with mode labels and evidence references. The action guard refuses payment instructions before model use. Live answers require valid citation keys; unavailable live providers fail closed. No live provider was called.
- Added explicit human-confirmed simulation review, ten server-recorded checks, animated pending visualization, receipt download and an owned decision evidence page. The check count is not a safety probability.
- Added invoice-level idempotency: a fresh capability cannot pay a previously simulated invoice again.
- Eight Python tests pass, including cross-account lookup/chat/history/approval denial, session revocation, read-only chat, unknown live provider, invalid citations, atomic approval races and rollback. Go tests include origin/JSON/method boundaries and anonymous denial. Production TypeScript/Vite build passes.
- `workspace-integration.json`: **21/21 authenticated HTTP assertions passed**, including real registration/session cookies, cross-account 404s, chat refusal/no payment side effects, cited answer, cross-origin rejection, explicit $100 simulation with 10 checks passed, duplicate denial, private adversarial invoice denial and logout.
- Browser verified account creation, sample invoice loading, a cited due-date answer, action refusal, explicit approval confirmation, persisted ten-check receipt and private conversation history. Dev proxy Host handling was corrected after browser testing exposed a same-origin mismatch.
- Local preview remains http://127.0.0.1:5174. Earlier unauthenticated demo servers were stopped. Screenshots: `../agentshield-login.png` and `../agentshield-workspace.png`.
- Remaining limits: no live Meta evaluation while credits are pending, PostgreSQL/Docker runtime still unverified, no production identity-provider review, email verification, MFA, password recovery, or public deployment. No claim of unique invention, prize outcome or independent security certification.
- Authenticated seven-fixture benchmark: **140/140** expected decisions; local SQLite + mock, p50 **68.66 ms**, p95 **97.11 ms** including session validation, capability preparation and durable audit. Raw rows: `benchmark-v3.json`.

## October 30 live Meta validation

Live connectivity, schema-constrained risk classification, cited invoice chat and authenticated simulation are now verified with `muse-spark-1.3`. See `LIVE-READINESS.md`, `live-connection.json`, `live-evaluation-initial.json`, `live-evaluation.json`, and `live-http.json`. Initial false positives are preserved; the corrected eight-case classification set and two chat/authority checks passed. The live HTTP flow passed three assertions with two real model calls. Nine Python tests pass after adding authorization-data exclusion. Prior statements that live Meta is unverified are historical; PostgreSQL/Docker runtime remains unverified.

## October 30 Attack & Intercept Lifecycle

- Private PDF/PNG/JPEG/text drafts, normalized previews, exact PDF text candidate geometry, reviewed fields and explicit trusted-recipient mapping implemented. Invalid/oversized/encrypted files are rejected; evidence above the workspace text limit is rejected rather than silently truncated.
- Two generated synthetic PDF fixtures and their PNG previews were visually inspected. Hidden fixture contains tiny white instruction text that is intentionally not visible in its ordinary rendering.
- Live Muse visual extraction passed. Live SAM 3.1 Responses stream returned five boxes and masks on the clean fixture; a browser refinement on the hidden fixture returned six. Rectangles retain explicit PDF/Muse/SAM provenance. This does not establish SAM-based OCR, bank authenticity or guaranteed PII removal.
- Browser upload → source-text warning → SAM refinement → field review → private invoice → real Muse denial verified. The exploded graph displayed the failed analysis node, its reason and its enforcement layer.
- Invoice-bound chaos targets the authenticated user's selected invoice. Scripted mutations affect a copy only; the original mandate and source-text digest are attached to the receipt. `invoice-chaos-integration.json`: **6/6** HTTP assertions passed, live Meta classification and unchanged saved source.
- Added actual rolling amount/velocity checks. Tests confirm the limit denies before capability consumption and permits recovery after the window expires.
- Hall of Scams public output contains fixed vector labels and normalized suspicious-region geometry, not source images, names, text, amounts, bank details or owner identity. Contributions require explicit geometry-only confirmation. Seeds are synthetic and contributions are unverified.
- Added host-controlled simulated $1,000,000 arena, dedicated sanitized public viewer, queued anonymous challenges and bounded 30-attempt lifetime budget. Queueing does not call a model. Live recipient swap was intercepted and the reserve remained unchanged. Browser viewer showed last committed DENY, one attempt and one denied proposal without private source data.
- Built Manifest V3 extension with activeTab selection, opt-in page shield, file chooser, local-only network access and one-hour/ten-attempt upload-only pairing. Backend forces model extraction off for extension handoffs. Pairings revoke explicitly and on logout. Syntax and scoped HTTP handoff are tested; browser installation/runtime remains manual and unverified.
- `lifecycle-integration.json`: **21/21** HTTP checks passed, including live Muse extraction, actual SAM output, owner isolation, malformed upload rejection, geometry privacy, extension-origin handoff, revocation, host queue privacy and live arena interception.
- Final Python suite: **17 tests passed**. Go tests pass; TypeScript/Vite production build passes (40 modules). Compose configuration and launcher PowerShell syntax validate. Extension JavaScript syntax validates and unpacked source is packaged at `../agentshield-extension.zip`.
- Standard launcher now creates a project virtual environment and installs pinned document dependencies. Authoring preview continues at port 5174 with gateway 8083 and private agent 8002.
- No public hosting, Chrome Web Store publication, automatic Gmail attachment scanning, executable payload runner, real payments, full pixel-mask overlay renderer or automatic personal-data redaction is claimed. PostgreSQL runtime is still unverified because Docker access remains unavailable.
