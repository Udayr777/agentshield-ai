# AgentShield rehearsal and narration reference

Use this as a practice guide, not text to read word-for-word. Target a 2:50 video. Speak calmly and show the working application. No face camera is required.

## 1. Where to practise

- Local: http://127.0.0.1:5174/ (dashboard), API on 8083, Python on 8005.
- Hosted: https://agentshield-ai-lgdd.onrender.com/
- Local startup was checked through the homepage, readiness, saved artwork, authenticated login/session, fresh empty workspace and logout. This does not prove every model operation succeeds.
- Local Meta configuration and PostgreSQL are present. Baseten is configured on Render only at this check. Use the hosted app for the partner segment, or privately add BASETEN_API_KEY and your supported OPEN_WEIGHT_MODEL to the local .env and restart Python. Do not paste keys into the video or chat. There is no need to copy private production data.
- Local and hosted are separate runtime configurations, even when they point at the same configured database. A Render-only key does not configure the local process.

To restart later, from the project root (stop older instances first):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1 -DashboardPort 5174 -GatewayPort 8083 -AgentPort 8005
```

The launcher installs dependencies on first setup and runs all three services. Leave the terminal open; Ctrl+C stops its launched processes. Do not start another copy while the app is already running. Default launcher ports remain 5173/8080/8001 when no parameters are passed.

## 2. Prepare before recording

1. Use the hosted origin for the final recording so judges see the public app. Localhost is fine for rehearsal.
2. Prepare a fresh account with synthetic documents. Keep email addresses and profile screens out of the recording. Email verification is optional; the current test sender does not deliver to arbitrary accounts.
3. Have the homepage, Invoice workspace, a successful read-only investigation and a visual draft ready in tabs on the same intended environment.
4. Load Judge Demo Pack explicitly. It contains clean, hidden-injection and shifted-layout synthetic $100 documents. Loading the pack is not a model call.
5. Use JUDGE-CLEAN for the first successful simulation. A previously simulated clean fixture will be denied on replay; do not call that a clean first-run failure. A fresh account gives fresh fixtures.
6. Prepare a successful Baseten/Wonder report before recording. You can show the real saved result, or label a cut while a new run completes. Do not imply that an edited wait was instantaneous.
7. If demonstrating SAM, run it explicitly in Visual invoice guard and confirm completed source metadata. Without that, describe only PDF geometry. Never call candidate boxes SAM results.
8. Turn off browser narration/music while explaining with your own voice. Close configuration tabs and other personal content. Do not record keys, reset/verification URLs or approval tokens.

## 3. Three-minute recording plan

### 0:00-0:20 / The problem and opening

Show: landing hero with the saved Muse artwork, then the workspace.

Say: "An invoice should tell an AI what is owed, not tell it who is in charge. AgentShield separates untrusted document content from permission to act. It is a synthetic finance security workspace: no bank accounts are connected and no real money moves."

Why: states the problem, solution and demonstration scope immediately. The artwork was generated with Muse Image; displaying it makes no new generation call.

### 0:20-0:50 / Legitimate work succeeds

Click: Invoice workspace -> Start judge demo -> clean fixture. Inspect $100 and vendor_acme. Click Review exact simulation -> Confirm simulation review. Wait for the actual receipt.

Say: "This clean invoice requests $100 for the registered vendor. I explicitly confirm that exact amount and recipient. The gateway evaluates policy, approval and persistence checks, and records the simulated outcome. An invoice or chatbot cannot grant that authority."

Verify: the receipt says allow for the first review. An error, timeout or loading animation is not an allow. Avoid claiming all ten controls passed if any are unknown or not measured.

### 0:50-1:25 / Change intent, show the block

Click: choose JUDGE-HIDDEN -> Enable Chaos Engineer Sandbox -> recipient-swap preset -> Run attack against this invoice. Open Security observatory and original/proposed comparison.

Say: "Now a scripted mutation redirects the proposal to attacker_wallet while the saved invoice still names vendor_acme. AgentShield denies the proposal. The receipt shows the changed recipient and every failed control, including recipient continuity and approval binding."

Adapt to the real source: if mode is network, say "A shared synthetic threat pattern matched before risk-model processing." If mode is mock, say "This run used the local heuristic." Only describe live Muse analysis when the receipt records it. Seven passed controls and three failures are expected for some attacks, not a safety score.

### 1:25-2:10 / Meaningful Meta investigation

Click: the selected synthetic invoice's Investigate. Explain. Keep control. panel. Show consent, actual trace, completed partner assessment/provenance, then Wonder's three cited cards. Use a saved successful report or an explicitly labeled time cut.

Say: "The read-only investigator uses Muse Spark for tool choices where there is a choice. Code handles mandatory transitions. Muse Spark Open, served through Baseten, examines the evidence. Muse Wonder turns the observations into a cited three-part briefing and a manual next step. This workflow has no banking, approval or code-execution tools."

Verify: COMPLETE, Live partner response recorded, actual provider-reported model, and a Wonder report. A configured model label alone does not prove a call succeeded. Do not call this independent cryptographic consensus; same-provider model errors can be correlated.

### 2:10-2:30 / Visual evidence and SAM

Show: a prepared synthetic draft, original/contrast/overlay, and geometry provenance. If SAM has completed, show that recorded label/refinement result.

Say when SAM completed: "Local document inspection surfaces visibility clues. Optional Meta SAM 3.1 refinement provides recorded anchor boxes for structural comparison with our trusted synthetic template. Layout deviation is a review signal, not proof of fraud."

Say if SAM was not run: "These are local PDF geometry candidates and visibility heuristics. Optional SAM refinement is available, but it was not measured in this run."

Do not claim detection of arbitrary hidden pixel code or QR fraud. Uploaded documents do not automatically become trusted templates.

### 2:30-2:50 / Evidence and close

Show: receipt export or audit integrity view, a brief architecture summary and public URL.

Say: "Go enforces the policy boundary. Python and PostgreSQL bind approvals, invoice state and audit commit. Signed chains and separately saved checkpoints support tamper detection. AgentShield makes agent proposals inspectable and accountable while keeping authority human."

Optional benchmark sentence: "Our small mock regression set matched all 35 expected outcomes; this is not a real-world detection accuracy claim."

End with the public URL. Identify only event-eligible contributions as event-built, consistent with BUILD-TIMELINE.md and organizer guidance.

## 4. Meta model reference: what to explain accurately

| Model | Actual role in AgentShield | Where to show it |
|---|---|---|
| Muse Spark, configured as muse-spark-1.3 | Invoice risk assessment, cited invoice/app copilots, optional visual extraction, three-context council, decision/visual explanations, optional clip scripting and investigation tool choices | A recorded live answer or receipt, council report, extraction metadata or investigation trace |
| Muse Spark Open, configured on the hosted app as meta-models/muse-spark-open | Open-weight advisory forensic review through Baseten | Investigation partner assessment, actual model and response metadata |
| Muse Wonder, configured as muse-wonder-1.0 | Final investigation briefing with three cited storyboard cards; separate optional Spark/Wonder comparison tool | Completed report provenance and storyboard |
| Muse Image, muse-image-1.0 | Original mascot and saved landing/empty-workspace illustrations | Homepage artwork and saved provenance; generated once, not at every visit |
| Meta SAM 3.1, sam-3.1 | Optional explicit document anchor refinement; completed boxes can feed trusted-template layout comparison | Visual guard completed refinement metadata, not merely a colored local box |

The three council reviewers are roles on the same configured Spark model, not three different Meta models. The optional council can be skipped by earlier shared/owner policy; use JUDGE-CLEAN to demonstrate it. The separate investigator can explain eligible blocked synthetic evidence without approving it.

Not integrated as live model workflows: Muse Glimmer, Muse Voice Transcribe, and Muse Video generation. Browser narration is a device voice, browser animations are local rendering, and music is synthesized locally. Do not attribute these to a Meta audio/video model. Model options in an event catalog do not mean the project must pretend to use every listed model.

Gmail documents are excluded from all external model workflows. Their invoice copilot uses local recorded facts. Use only the synthetic fixtures for the live Meta demonstration.

## 5. Optional features: practise separately, omit if time is tight

- Invoice copilot: ask When is this invoice due? Show citations. Ask it to pay: the action is refused and no payment tool runs.
- Muse council: select clean fixture -> Require & run Muse council. Explain audit/policy/forensic roles, signed evidence binding and correlated-error limits. High/unknown or stale reports cannot satisfy a required gate.
- Video explanation: Play/replay renders saved/local evidence immediately; Upgrade script with Muse makes an optional live scripting call. The clip is not a generated Muse video. The optional voice is local playback, not included in exported narration.
- Audit: verify integrity, export a checkpoint and explain that a separately retained trusted checkpoint is needed to detect truncation. Do not claim logs are mathematically impossible to alter under full host/key compromise.
- Security frontier: opt-in synthetic signature sharing, passkey verification for simulated holds, constrained additive policy proposals. No real banking escrow, autonomous code repair or general immunity claims.
- Resend: mailbox verification and password recovery, not financial authority. Show only with an allowed inbox/verified sender. Do not expose the private token URL.
- Gmail: explicit read-only search and selected attachment import; no background scans, outbound email or model transfer. Keep real mailbox data out of the recording.

## 6. Short answers for questions

**Who is it for?** Teams experimenting with AI-assisted accounts payable and developers building agents that propose sensitive actions.

**Why not just ask the model if the invoice is safe?** Content analysis cannot grant authority. Deterministic ownership, recipient, limits and exact approval checks remain required even if a model judges content low risk.

**What is agentic?** Bounded selection among read-only evidence tools, optional partner review and a cited briefing. It is not an autonomous payment agent in the real world.

**What is the unique engineering story?** The same owned invoice connects visual inspection, a mutated proposal, a code-enforced decision, original/proposed audit evidence and a cited explanation.

**What does 10/10 mean?** Ten observed control results, not a probability of safety or proof of authenticity.

**Are signatures the same as WORM storage?** No. HMAC/hash chaining provides tamper evidence with protected keys/checkpoints; it is not independent immutable storage or a host-compromise guarantee.

**How are models used responsibly?** Credentials stay server-side; evidence is scoped, model output is validated, no model can approve a payment, and Gmail-derived documents remain excluded from external processing.

**Do I need to show everything?** No. The core clean -> attack -> block -> explanation story matters more than a tour of every page. Keep optional features for follow-up questions.

## 7. If a rehearsal step fails

- Local page unavailable: confirm the terminal processes are running. Start the parameterized launcher only after stopping older copies; inspect the printed port.
- Local partner says not configured: expected until the Baseten key is saved locally. Use the hosted instance for that segment instead.
- Clean invoice denied: inspect the actual failed controls. It may already be simulated, have a required stale/high-risk council report or an active owner policy. Use a fresh account/clean fixture; never relabel a denial as success.
- Hidden council skipped: earlier threat policy prevented council calls. Use the independent read-only investigation, or demonstrate council on clean evidence.
- Invalid model response/timeout: keep the visible failure honest; inspect its stage. Prepare a saved successful synthetic report with its metadata rather than inventing output.
- SAM unavailable: show local geometry with the accurate label; do not claim live SAM evidence.
- Email 403: current test sender restriction. Use the allowed Resend account inbox or configure a verified domain.

## 8. Confidence checklist

Before recording, answer these in your own words: what changed in the attack, which exact control blocked it, which provider/model actually ran, which parts are deterministic, and what remains simulated. If those five answers are clear, the demonstration has a coherent technical story.

Narration should sound like a product walkthrough, not a list of model names. Name each model as its useful contribution appears. The in-app recorder is silent and limited to 45 seconds; use a full screen recorder/editor for the narrated three-minute submission.
