# Deploy AgentShield to Render Free + Neon

The repository root is the app root. Use the root `Dockerfile`, not the individual Compose service Dockerfiles. `render.yaml` describes one free Docker web service in Oregon. PostgreSQL is your separately created Neon database; no Render database or paid disk is needed.

## Render dashboard

1. Choose **New → Web Service**, connect this GitHub repository, and select branch `main`.
2. Choose **Docker** runtime, **Oregon** region, **Free** instance. Leave Root Directory blank. Dockerfile Path is `./Dockerfile`; no custom build/start command is required.
3. Add the environment variables below in Render's private Environment settings. Set the health check path to `/api/ready`.
4. Deploy. Check the build/runtime logs without sharing secrets. Open the resulting `https://...onrender.com` URL.

Alternatively, deploy the repository as a Render Blueprint using `render.yaml`; it prompts for private values and generates the service and ledger secrets. Do not regenerate the ledger secret during later deploys.

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | Neon pooled URL, with its TLS parameters preserved |
| `DATABASE_URL_UNPOOLED` | Neon direct URL for migrations |
| `META_API_KEY` | A current, private Meta API key; rotate previously shared keys |
| `META_MODEL` | `muse-spark-1.3`, or your available supported model |
| `META_BASE_URL` | `https://api.meta.ai/v1` |
| `META_SAM_MODEL` | `sam-3.1` |
| `ANALYZER_MODE` | `meta`, or `mock` for a no-model smoke test |
| `COOKIE_SECURE` | `true` |
| `SERVICE_TOKEN` | A generated cryptographically random secret, at least 32 random bytes |
| `LEDGER_SIGNING_KEY` | A separate generated random secret, at least 32 random bytes; keep stable and backed up privately |

For a manual Web Service deployment, generate the last two values with a password manager's secure generator and enter them only into Render. Blueprint deployment generates them automatically. These are service secrets, not user passwords. If copying an existing database with signed events, use its existing ledger signing key: a different key fails verification of those events. Never copy local personal/demo records into the public environment unintentionally.

The supervisor binds Go to Render's `PORT` on `0.0.0.0`; Python remains local-only. All requests use one HTTPS origin, so session cookies and same-origin write checks continue to work. The UI, samples and avatar are included in the image. Database data survives application restarts; ephemeral container files do not. Exported checkpoints must be kept independently. User-uploaded document payloads currently live in the database, so monitor Neon storage usage.

## Hosted acceptance checks

- `/api/ready` responds successfully and the landing page loads.
- Create two synthetic accounts. Check sign-in/out and private invoice isolation.
- Load the Judge Demo Pack, run a legitimate $100 simulation, and inspect a denied malicious case. All money is simulated.
- Upload a synthetic PDF; explicitly opt into Muse extraction or SAM only when testing those live features.
- Verify the audit chain, export a checkpoint, restart/redeploy and compare it again using the same signing key.
- Confirm accounts, invoices, documents and audit events remain available after refresh and restart.
- Confirm no browser response or bundled asset exposes API keys, database URLs, service secrets or signing keys.

Free Render services sleep after inactivity, so cold starts may delay a judge's first visit. Free resources have usage limits; review dashboard usage during judging. No always-on availability or production SLA is claimed.

The extension is scoped to localhost by default. Before using it with the hosted app, explicitly add only your final HTTPS origin to its manifest and URL validation; rebuild the extension ZIP. Do not grant blanket access to all sites. See `extension/README.md` for the three-step installation.

Reference: [Render web services](https://render.com/docs/web-services), [Render free instances](https://render.com/docs/free), [Blueprint configuration](https://render.com/docs/blueprint-spec).
