# Meta model usage in AgentShield

The text/vision model is configurable through `META_MODEL` (current default `muse-spark-1.3`). Live calls require `ANALYZER_MODE=meta` and a private Meta API key. Credentials stay on the Python service, never in the React app or extension.

| Feature | Integration | Trigger / evidence |
| --- | --- | --- |
| Risk analyzer | Muse Spark structured JSON | `agent/app.py`, `analyze`: classifies injection/redirection content during simulation review. Missing/failed analysis is unknown and payment fails closed. |
| Optional review council | Three isolated Muse Spark contexts; Forensics also receives the document preview when available | `agent/council.py`: explicit per-invoice opt-in, signed evidence fingerprint and five-minute expiry. All three completed low-risk assessments are required when enabled. Same-model errors can be correlated. See `COUNCIL.md`. |
| Private invoice copilot | Muse Spark structured JSON | `agent/workspace.py`, `chat`: answers from the selected owner's invoice and cites evidence. Has no payment tools. |
| Visual field extraction | Muse Spark vision | `agent/visual.py`, `ingest`: explicit opt-in on upload; proposes fields and approximate anchors. Human review is required. |
| App Help / Aegis copilot | Muse Spark structured JSON | `agent/helpdesk.py`, `chat`: receives app documentation and the question only. No invoice, password, account or payment context. Five questions per owner per minute. |
| Aegis artwork | Muse Image `muse-image-1.0` | `scripts/create-guide-avatar.py`: one-time generation. Provenance is saved in `dashboard/public/guide-provenance.json`. Animation is CSS, not live generation. |
| Visual region refinement | Meta SAM `sam-3.1` | `agent/visual.py`, `segment`: explicit Refine anchor regions request. SAM is a separate Meta model, not Muse. The template heuristic uses returned boxes when completed; otherwise it identifies PDF geometry as the evidence source. |

The Go policy gateway, registry, amount/velocity limits, exact approval binding, expiry, idempotency and ledger signatures are deterministic code. Models do not approve payments. The demo pack is three synthetic $100 invoices: a clean service bill, a white-on-white prompt injection, and a look-alike merchant with shifted banking anchors and substituted synthetic routing text. Loading it creates private reviewed sample invoices and PDF drafts without executing a payment or calling a model. It is idempotent per account.

The five-stop tour ends with **Finish tour**. Completion is saved per account in browser storage; the large demo introduction collapses, and Aegis becomes a small, stationary **Ask Aegis** launcher. It opens app-help chat, with **Replay tour** and the full Help center still accessible. Browser storage contains only this UI preference, not authorization state.

All pages use `dashboard/src/workspace-theme.css` for light panels and readable text, including the actual `.chat-panel`, `.security-board`, `.approval-bar`, `.upload-zone` and `.invoice-chaos` elements. The separate cinematic landing-page illustration retains its intentional dark treatment.
