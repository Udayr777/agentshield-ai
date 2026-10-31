# AgentShield companion

## Install in three steps

1. Unzip `agentshield-extension.zip` into a normal folder.
2. Open `chrome://extensions` and turn **Developer mode** on.
3. Click **Load unpacked** and select the unzipped folder containing `manifest.json`.

Then open AgentShield's Browser companion page to create an upload-only pairing token. Paste that token into the extension popup. Never use your Meta key. The included manifest targets localhost; the hosted app's exact origin must be explicitly added before testing a cloud deployment. Do not grant access to every website.

Unpacked Manifest V3 extension for Chrome/compatible browsers. Open Extensions, enable developer mode, choose **Load unpacked**, and select this directory. This installation is not performed automatically by the development task.

Pair in the app's **Browser companion** page, copy the one-hour upload-only token, and paste it in the extension popup. The token allows at most ten private draft uploads and can be revoked in the app. It grants no invoice reading, chat, SAM, payment or Meta-key access. The token is stored in extension session storage.

Select invoice text on the active page and explicitly click **Read selected text**, review it, consent and send. Or choose a local PDF/PNG/JPEG. The optional page shield is injected only after a toolbar interaction; it reads an explicit selection when clicked. There is no automatic inbox crawl, attachment interception, URL fetching or background message scanning. Browser PDF viewers and some frames do not allow selection injection; use the file picker instead.

Network access is limited to localhost, default port 5174. Change the popup address for another local app port. Import creates a private draft only: later extraction and confirmation happen in the authenticated app. Never paste the Meta API key into the extension. No Chrome Web Store listing or public distribution has been created.
