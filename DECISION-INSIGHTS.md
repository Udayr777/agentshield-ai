# Recorded decision insights

After reviewing an invoice simulation or running its Chaos sandbox, open the Security observatory. **See the difference. Understand the decision.** compares the source invoice recipient, amount and text with the proposal actually reviewed. Changed fields are highlighted; text comparison is expandable. The same component is available in Decision evidence when a receipt is expanded.

The source snapshot is taken from the owned invoice within the audit transaction and included in the signed receipt. It is not reconstructed later from current invoice fields. Receipts without a historical snapshot explicitly say so. A text preview may be truncated; the snapshot records that limitation. A changed field is not independently proof of fraud.

**Ask Muse: why this decision?** makes an explicit live call. It explains the already recorded result, distinguishes code-enforced failures from model observations, and suggests a manual next step. Valid citations must reference actual facts/control IDs; when failed checks exist, at least one failed control must be cited. This does not prove the narrative correct; original evidence remains visible.

The authenticated server loads the owner's saved receipt, verifies its audit chain, and supplies only recorded checks, analysis, recipient/amount differences and a text-change flag. It never accepts a client-provided receipt or sends raw invoice text, approval tokens, sessions, email or account IDs to the model. The feature has no execution tools and cannot update a decision, policy, invoice or payment.

Completed explanations are HMAC-signed, bound to the receipt digest, and cached privately. Failed/pending attempts are not retried automatically. New generations share the configurable inspection/explanation quota. Cached/local views make no model call. Gmail provenance is checked from both the recorded snapshot and current server invoice; external explanations are blocked for Gmail-derived decisions while local evidence stays available. Legacy unsigned or integrity-failed receipts cannot request a model explanation.

Tests cover historical snapshot preservation, changed-field detection, owner isolation, altered receipt rejection, cached explanations, unsupported citations, no capability/raw-text forwarding and Gmail restrictions. A local explanation is not a safety certification or financial advice.

Verified October 31, 2026 through the local frontend, Go gateway, Neon and live Muse Spark 1.3: recipient-swap denied, historical recipient/text differences returned, explanation cited actual failed controls, and repeated generation returned the identical cached answer. The explanation call used 1,640 reported tokens. All 59 Python tests, Go tests and the production frontend build passed. Visible receipt panels load evidence on demand so collapsed activity history does not eagerly verify every receipt. Browser visual interaction was not automated.
