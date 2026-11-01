# Meta model usage in AgentShield

An operator-only Spark-versus-Wonder comparison uses the same risk analyzer with an explicit per-call model override. It leaves `META_MODEL` and payment behavior unchanged. See [Model comparison](MODEL-COMPARISON.md) for the synthetic dataset, run command and limits.

Invoice briefs add an explicit `visual_clip_script` Muse call: exactly three bounded captions with validated evidence references, cached per document and sharing inspection quotas. The browser renders an 18-second animation and optional WebM export with an original locally synthesized music bed. Selectable energetic narration uses a local browser voice, not a Meta audio model. There is no claim of Meta-generated video/audio. Gmail scripts remain blocked. See [Visual inspection](VISUAL-INSPECTION.md).

Visual evidence explanations are explicit, bounded Muse calls supplied only with numeric first-page observations and fixed check metadata. References are validated against finding IDs; completed responses are cached. Gmail imports cannot use this call. Contrast enhancement and visibility heuristics run locally without models. See [Visual inspection](VISUAL-INSPECTION.md).

Security frontier adds explicit live policy synthesis using `POLICY_MODEL` or the configured `META_MODEL`. One bounded structured-output call receives only aggregate synthetic threat categories; the actual model and token usage are retained with the proposal. Code validates the finite rule schema and runs 1,024 fixture variations before owner promotion. No generated code runs, no base guardrails are rewritten, and no fine-tuned Llama model is claimed. Known shared signatures and active additive policies can block before any model call. Passkey verification itself makes no model calls. See [Security frontier](SECURITY-FRONTIER.md).

Gmail exception: documents imported by the read-only Gmail connector and their confirmed invoices remain local-only. Server guards block their risk-model calls, Muse chat, council review, SAM refinement and public sharing until suitable provider data-use terms are reviewed. These records are not eligible for payment simulation. See `GMAIL.md`.

The text/vision model is configurable through `META_MODEL` (current default `muse-spark-1.3`). Live calls require `ANALYZER_MODE=meta` and a private Meta API key. Credentials stay on the Python service, never in the React app or extension.

| Feature | Integration | Trigger / evidence |
| --- | --- | --- |
| Risk analyzer | Muse Spark structured JSON | `agent/app.py`, `analyze`: classifies injection/redirection content during simulation review. Missing/failed analysis is unknown and payment fails closed. |
| Optional review council | Three isolated Muse Spark contexts; Forensics also receives the document preview when available | `agent/council.py`: explicit per-invoice opt-in, signed evidence fingerprint and five-minute expiry. All three completed low-risk assessments are required when enabled. Same-model errors can be correlated. See `COUNCIL.md`. |
| Private invoice copilot | Muse Spark structured JSON | `agent/workspace.py`, `chat`: answers from the selected owner's invoice and cites evidence. Has no payment tools. |
| Visual field extraction | Muse Spark vision | `agent/visual.py`, `ingest`: explicit opt-in on upload; proposes fields and approximate anchors. Human review is required. |
| App Help / Zivvi copilot | Muse Spark structured JSON | `agent/helpdesk.py`, `chat`: receives app documentation and the question only. No invoice, password, account or payment context. Five questions per owner per minute. |
| Zivvi artwork | Muse Image `muse-image-1.0` | `scripts/create-guide-avatar.py`: one-time generation. Provenance is saved in `dashboard/public/guide-provenance.json`. Animation is CSS, not live generation. |
| Visual region refinement | Meta SAM `sam-3.1` | `agent/visual.py`, `segment`: explicit Refine anchor regions request. SAM is a separate Meta model, not Muse. The template heuristic uses returned boxes when completed; otherwise it identifies PDF geometry as the evidence source. |

The Go policy gateway, registry, amount/velocity limits, exact approval binding, expiry, idempotency and ledger signatures are deterministic code. Models do not approve payments. The demo pack is three synthetic $100 invoices: a clean service bill, a white-on-white prompt injection, and a look-alike merchant with shifted banking anchors and substituted synthetic routing text. Loading it creates private reviewed sample invoices and PDF drafts without executing a payment or calling a model. It is idempotent per account.

The five-stop tour ends with **Finish tour**. Completion is saved per account in browser storage; the large demo introduction collapses, and Zivvi becomes a small, stationary **Ask Zivvi** launcher. It opens app-help chat, with **Replay tour** and the full Help center still accessible. Browser storage contains only this UI preference, not authorization state.

All pages use `dashboard/src/workspace-theme.css` for light panels and readable text, including the actual `.chat-panel`, `.security-board`, `.approval-bar`, `.upload-zone` and `.invoice-chaos` elements. The separate cinematic landing-page illustration retains its intentional dark treatment.

Zivvi hover greeting uses a six-pose full-character sheet derived from the original Muse character reference with the OpenAI image-generation/editing tool. Runtime frame playback is local, not Muse Video or live image generation, and not a rigged 3D model. The original Muse asset/provenance remain unchanged; derived-sheet provenance is recorded separately in dashboard/public/zivvi-wave-provenance.json. There is no detached hand overlay.
