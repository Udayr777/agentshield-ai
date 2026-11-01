# Attack & Intercept Lifecycle

Local preview: http://127.0.0.1:5174. New navigation: **Visual invoice guard**, **Defend your wallet**, **Hall of Scams**, and **Browser companion**. All money and agent mutations are simulated. No public site, stream, store listing or global threat repository has been published.

## 1. Upload → extract → verify

Open Visual invoice guard and choose a PDF, PNG or JPEG up to 4 MB. PDFs must be unencrypted, 1–5 pages and contain no more than 8,000 extracted characters. The app rejects oversized evidence rather than silently omitting later instructions. The first page is rendered as a private normalized image; PDF text from all supported pages is included for review.

Local PDF processing proposes fields and exact PDF text rectangles without making model calls. Low-visibility text is flagged using font size and a rendered-background contrast heuristic; this is not comprehensive hidden-content detection. Image uploads without live extraction require manual fields.

The **Send this synthetic document to Meta** checkbox enables Muse field extraction. All fields remain proposals. Enter or verify the reference, merchant, total and due date; explicitly map the recipient to a trusted registry entry. **Save reviewed invoice** creates a private pending invoice, not a payment approval. The original normalized draft is kept separately.

Box labels identify their provenance:

- `pdf_text_geometry`: text locations from the PDF, not model segmentation or proof of content trust.
- `muse_estimate`: approximate model-proposed coordinates.
- `sam-3.1`: real SAM output, only after an explicit segmentation request.

**Refine anchor regions with Meta SAM 3.1** sends the preview and box prompts in one Responses API stream. Each returned region is interactive. No matches and model errors are shown as such; fallback boxes are not relabeled as SAM. SAM locates pixels, not bank authenticity or PII. The app displays returned boxes and mask counts; pixel masks are not painted as full overlays.

Live verification returned five boxes/masks for the clean synthetic invoice, and a browser test returned six for the hidden-instruction fixture. The hidden instruction text was detected from PDF source extraction and subsequently blocked by Muse content risk analysis; this should not be misrepresented as SAM reading invisible text.

## 2. Chaos against the selected invoice

Open the reviewed invoice in Invoice workspace. Enable **Chaos Engineer Sandbox** and choose a recipient swap, $10,000 escalation, hidden instruction, reused approval, expired approval or custom text.

The service checks invoice ownership and issues a scoped demo capability for the original recipient/amount. It then mutates a copy of the proposal, preserving the saved invoice and recording the source-text SHA-256 plus original mandate in the receipt. Payloads are strings, never executable JavaScript or backend scripts. A custom benign proposal may legitimately pass; a pass is a synthetic receipt only.

Payment review also enforces rolling per-account limits: fewer than 30 allowed actions and at most USD 10,000 combined proposed value in a rolling minute, in addition to the USD 1,000 per-action ceiling. The local server serializes authorization transactions; multi-instance deployment needs a reviewed distributed locking/serialization strategy.

## 3. Interactive exploded audit

After a receipt arrives, the graph displays all ten recorded controls and highlights failed/unknown checks. Click a node to inspect its actual explanation and enforcement layer. The animation is a replay of recorded evidence, not an invented timeline of backend execution. Some checks are evaluated even when another check failed.

The browser test uploaded a tiny-white-text malicious PDF, refined its anchors with real SAM, confirmed the fields, and ran a real Muse review. The invoice remained pending; the model-analysis node failed and displayed the injection, recipient-redirection and concealment explanation. Other passing controls did not override that denial.

## 4. Hall of Scams

The gallery is readable without signing in at `/#hall`. Four seed cards are clearly marked synthetic. Contributions require an authenticated owner to open their own document, choose a fixed attack category, inspect the geometry-only preview and explicitly approve sharing.

Only a generated ID, allowlisted category, normalized suspicious-region rectangles and timestamp are returned publicly. Original images, text, merchant names, references, amounts, bank details, source filenames and owner identity are excluded. This is privacy by withholding originals, not a promise that SAM strips every personal detail. Contributions are not verified fraud judgments. Host moderation, abuse reporting and production retention controls are not implemented.

## 5. Defend Your Wallet / broadcast stage

Create a local simulated arena. Its reserve starts at USD 1,000,000. Host controls run a preset or custom proposed invoice through the real gateway. A dedicated `/#live/<arena-id>` viewer polls only sanitized counters and the last committed verdict; it never receives private source text or host identity.

Public submissions are disabled by default. Enabling them permits anonymous text to enter a host-only queue. The host explicitly approves each paid attempt. Public submission itself makes no model call. Each arena has a hard 30-attempt lifetime budget, a 20-item queue ceiling, and request rate limits. Signed-in hosts can resume their last arena after navigation; the public arena identifier is stored per account locally, never an authentication token.

The reserve decreases only when an allowed proposal deviates from the authorized recipient or amount. Allowed within-mandate controls do not count as theft. A model outage also denies a proposal, so the denied counter alone is not an attack-detection metric. No gambling, prizes, actual banking, livestream-service integrations, arbitrary script execution or automatic public inference are implemented.

## 6. Deep-Scan browser companion

The unpacked Manifest V3 package is in `extension/` and the output ZIP. Load it manually through Chrome's Extensions page. It has `activeTab`, scripting and session storage, with network access restricted to localhost.

Generate a pairing credential in Browser companion. It is valid for one hour and at most ten draft-upload attempts. It cannot read invoices, chat, run Muse/SAM or approve a payment. Pairings can be revoked and are revoked on logout. The Meta key stays server-side.

Select invoice text, click the toolbar, preview the selection, consent and send. Alternatively choose a local PDF/image in the popup. An optional shield can be injected only after an explicit toolbar action. It reads only a selection when clicked. A successful import opens `/#draft=<id>` in the paired private workspace for review. The backend forces model extraction off for extension handoffs; the user opts into any later scan.

No inbox crawling or automatic Gmail-attachment overlay is claimed. Attachment internals, restricted PDF viewers and frames may not allow selection; use the file picker. The extension package passes JS syntax validation and its scoped handoff API is tested, but the extension is not installed or runtime-verified in the user's Chrome profile.

## Reproduce checks

```powershell
cd agent
python -m pip install -r requirements.txt
python -m unittest -v
cd ../gateway
go test ./...
cd ../dashboard
npm.cmd ci
npm.cmd run build
cd ..
python scripts/check-lifecycle.py --url http://127.0.0.1:8080
```

Add `--live` only when prepared for up to three synthetic model calls: Muse extraction, SAM segmentation and one arena risk analysis. The standard local launcher now manages a project `.venv` and installs document dependencies. Fixture regeneration optionally requires ReportLab; the PDFs/PNGs are already provided in `samples/`.

The authored preview uses gateway 8083; the launcher uses 8080 and Compose uses 8082. Docker configuration validates, but PostgreSQL/Compose runtime is still unverified because this session cannot access Docker. Keep the application local until identity, upload-parser isolation, moderation, proxy limits, HTTPS and secrets are reviewed for public hosting. Review third-party dependency licensing before publishing.
