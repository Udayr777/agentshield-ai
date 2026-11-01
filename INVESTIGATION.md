# Bounded invoice investigation

Select an invoice in **Invoice workspace**, find **Investigate. Explain. Keep control.**, explicitly consent, and start a run. Gmail imports remain blocked from external models. A run observes one server-owned account-scoped invoice; it does not perform a payment review or grant approval.

## Actual agent loop

The configured Meta planner selects from an allowlist using validated structured output. It must read the invoice first, may inspect saved first-page visual evidence, must call a configured open-weight reviewer before finishing, and must finish within four selections. Each tool is fixed in code and bound to the same server-resolved invoice. There are no user-specified tool arguments, arbitrary URLs, shell commands, inbox actions, policy edits or payment tools. The displayed reason is a brief operational rationale, not private chain-of-thought.

The final `muse-wonder-1.0` call creates a three-card cited investigation storyboard and a manual next step. Every card must cite an actual observed evidence ID. Saved evidence is not automatically re-segmented or OCR'd. A source fingerprint must match before and after the run; changing evidence invalidates completion. Findings are probabilistic observations, not authenticity certification, legal advice or a safety probability.

## Partner configuration

Baseten is implemented using its documented OpenAI-compatible endpoint `https://inference.baseten.co/v1`. The partner key is separate from `META_API_KEY` and is never sent to Meta or the browser. In the private local environment and Render Environment, set:

```dotenv
BASETEN_API_KEY=<private partner key>
OPEN_WEIGHT_MODEL=meta-models/muse-spark-open-1026
INVESTIGATION_REPORT_MODEL=muse-wonder-1.0
```

The participant guide supplied to this project specifies the `-1026` hackathon alias. The public Meta cookbook documents `meta-models/muse-spark-open`; both identifiers are allowed, but access and prize eligibility must be confirmed with the partner/organizer. A missing/invalid alias is an error, never an automatic substitution. Restart/redeploy after settings change. Baseten usage draws on that provider's credits/billing, not Meta's API balance.

Without the key, the UI explicitly offers **Meta-only investigation** and never claims an open-weight call occurred. With the key configured, the provider review is required. Successful partner responses retain requested model, provider-reported model when returned, response/request IDs, usage and latency. These are useful evidence for infrastructure-partner verification, not an independent cryptographic proof of model identity or a guarantee of prize eligibility.

## Persistence and limits

Runs and reports are stored in PostgreSQL/SQLite, HMAC-signed and account-scoped. The worker publishes completed steps as they occur; it does not reveal model hidden reasoning. A job makes at most six model calls and runs in the background. Provider failures are visible and are never silently changed to another provider. Completed steps survive a failed run. The UI polls the signed record. A server restart can interrupt a job; stale running jobs expire rather than being presented as completed.

There is one worker per process, a 15-second account start cooldown, and at most 100 runs per deployment per rolling hour including failures. Provider-specific token/rate limits still apply. This is a single-deployment demo worker, not a durable distributed task queue. Jobs have a bounded execution window and cannot issue approvals or audit payment receipts.

## Public demo kit and recording

Only completed runs for server-owned Judge Demo Pack fixtures can prepare a public kit. The kit uses fixed demo copy and recording steps; it omits private invoice text, recipient, account IDs, raw generated prose and request IDs. Private report exports are labeled private. Share-kit eligibility also requires the original evidence fingerprint to remain unchanged.

The optional browser screen recorder requires an explicit tab-selection permission prompt. Choose AgentShield only, use synthetic fixtures and hide personal data. It captures silently, auto-stops at 45 seconds, saves a local MP4 when supported (otherwise WebM) and never uploads it. Browser/media support and the actual video need manual verification. The short clip supplements rather than replaces the required submission video.

Nothing automatically posts on X, submits a project, requests votes, or claims an award. Post the reviewed recording yourself and submit its post link through the event platform. Use the official gallery voting link when available; do not fabricate engagement or eligibility claims.

## Acceptance

```powershell
# Paid, bounded synthetic run, local app:
python scripts/check-investigation.py --live --require-partner

# Run against the deployed app after pushing/redeploying:
python scripts/check-investigation.py --url https://agentshield-ai-lgdd.onrender.com --live --require-partner
```

The script creates a synthetic test account, loads the synthetic judge fixture, checks partner configuration, starts/polls a run, verifies its completion and partner-response flag, verifies no payment events were created and the invoice remains pending, and checks the sanitized share kit. It saves a private `live-investigation.json` report (Git-ignored). `--require-partner` fails before model calls when the partner is absent. It does not verify a physical screen-recording permission ceremony or partner adjudication.

When only one tool is allowed, code selects it without a model call. These trace entries are explicitly labeled Code-enforced transition. Model planning is used only where several actions are available; invalid planner output still fails closed.
