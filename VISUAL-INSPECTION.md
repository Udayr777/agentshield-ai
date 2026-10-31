# Visual evidence inspector

Open **Visual invoice guard**, choose a synthetic visibility case and click **Load visibility fixture**, or upload a new PDF. The inspector appears above field review. Select an observation to highlight its normalized first-page region in the overlay. Existing drafts without inspection evidence require re-upload; original PDF bytes were not retained.

Three views show the original rendering, a grayscale/autocontrast image with contrast multiplied by 1.8, and an overlay. Enhancement cannot reveal white-on-white or non-rendered text by itself. The overlay locates suspicious extractable text independently of whether it is visibly readable.

## Measured checks

| Check | Rule | Limit |
|---|---|---|
| Low contrast | Declared text color vs estimated local background luminance ratio below 1.5 | Background is estimated from four neighboring corners; patterned backgrounds can produce false positives. |
| Tiny text | Font size below 6 PDF points | Fine print can be legitimate. |
| Visibility mismatch | Extractable text region has rendered grayscale standard deviation below 2 | This is a pixel-visibility proxy, not independent OCR or semantic comparison. |
| Invisible text layer | PDF text trace render mode 3 or opacity below 0.1 | Searchable/scanned PDFs may legitimately contain invisible OCR layers. |
| Overlap | Distinct text spans overlap more than 65% of the smaller area | Complex layouts can overlap legitimately. |

Only page 1 is inspected. At most 400 extracted spans, 400 text traces and 80 observations are reported; truncation is displayed. Raster images receive an enhanced view but text checks are marked unavailable. There is no steganography, logo authenticity, universal tamper detection or independent OCR implementation. These findings do not authorize a payment or automatically change gateway decisions. All pages and extracted fields still require human review.

## Optional Muse explanation

### 18-second invoice brief

Beside the findings, click **Generate Muse brief**, then **Play / replay 18s**. A separate explicit Muse call writes exactly three captions (4–14 words each) citing valid finding IDs: observations, meaning/uncertainty, and next manual review step. The server fixes the duration at 18 seconds and supplies only numeric first-page evidence, not invoice text or its preview. Scripts share the existing explanation quota and are cached per private document; failed attempts are not automatically retried.

AgentShield draws the actual preview, highlighted regions, captions and progress onto a browser canvas. This is code-rendered animation from a Muse-written script, not Meta video generation. Narration defaults on, selects a known female-named local English browser voice when installed, and offers a narrator selector and Preview narrator button. Voice gender/quality is not available as a standardized browser property and is not guaranteed. Rate 1.1 and pitch 1.06 give a slightly brighter delivery; if no local voice is available, captions remain. No voice-cloning or Meta TTS service is used. Voice timing varies by device and long/slow narration may be cut at a scene boundary.

Verified local Go gateway + Neon + live `muse-spark-1.3` scripting: three valid captions, fixed 18-second duration, valid evidence references and identical cached second response. The single generation used 1,426 tokens. All 43 Python tests, Go tests and frontend production build passed. Browser narration/recording was not exercised through automation.

On browsers supporting canvas capture and WebM MediaRecorder, **Render WebM + music** records the 18-second animation, then offers a download. Keep the tab visible while rendering. Stopping early produces a shorter recording. Export includes captions, the private invoice preview, and the original Web Audio soundtrack when enabled, but no browser speech audio; only share synthetic examples. The soundtrack is composed locally using scheduled oscillators at 112 BPM, with a volume control and an end fade. No downloaded commercial music or external audio service is used. Stop/navigation closes the audio context. Other browsers retain on-page playback/transcript. Replay/export make no new model calls. Generation is unavailable for Gmail imports and raster-only/unmeasured evidence. Leaving the page stops playback/voice and revokes temporary media URLs. Browser/device playback and export need manual validation; compilation and server tests do not prove device media support.

Click **Ask Muse to explain these findings** in live Meta mode. Only numerical findings, fixed check names, region coordinates and limitations are supplied; original image, extracted text and merchant identifiers are not supplied. Output references must match actual evidence IDs. Explanations cannot change evidence or authorize actions. Completed results are cached privately by document; failed attempts are not automatically retried. New calls are limited to five/account/hour and twenty/deployment/hour, including failures.

Gmail imports can be inspected locally, but server and UI both prohibit the external explanation. All document access remains owner-scoped. No observations are automatically published to the public gallery or threat feed.

## Reproducible synthetic benchmark

```powershell
python scripts/benchmark-visual.py
python -m unittest discover -s agent -p test_inspection.py -q
```

Use the project's Python environment with `agent/requirements.txt` installed. Fixture PDFs and the complete results are in `samples/visual-inspection/`. The benchmark regenerates 15 documents: three clean controls and three variants of each of four families (white text, tiny text, invisible layer, overlap). The generator uses ordinary PDF text operations, with no network or model calls.

Measured result: **12/12 tampered documents flagged, 0/3 clean documents flagged**. Timings in `results.json` cover enhancement and heuristic inspection only, excluding PDF render, upload, model, database and network. This deliberately small fixture corpus tests the implemented rules and does not estimate real-world precision, recall or adversarial robustness. Broader labeled benign layouts and independent OCR would be necessary for production validation.

October 31, 2026 local Go gateway + Neon integration: the clean fixture had zero findings; the white-text fixture produced low-contrast and render-visibility observations, persisted and reloaded privately. Unauthenticated retrieval returned 401. An explicit live `muse-spark-1.3` explanation used 1,200 tokens and referenced the actual `e1`/`e2` findings; the second request returned the cached result. All 41 Python tests, Go tests and the TypeScript/Vite build passed. Browser visual inspection was not automated in this environment.

Saved briefs restore through an authenticated, owner-scoped GET request when a draft is opened. This lookup does not generate content or consume quota. Replay uses the restored script locally. Draft selection is retained in the URL across refreshes. A temporary session-service failure shows Retry connection instead of treating the user as signed out; only an actual 401 selects the sign-in flow. New generation remains subject to rolling-hour limits, separate from the provider credit balance.
