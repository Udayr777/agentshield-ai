# Muse review council

An optional simulation gate combines three separately prompted assessments: Audit (fact consistency), Policy (instruction/authority bypass), and Forensics (document deception, plus the preview image when available). Each reviewer calls the configured `META_MODEL` through Meta Model API with its own context and structured output. Reviewers do not see each other's answers and have no action tools. This is not independent infrastructure or a distributed consensus protocol; same-model errors can be correlated.

## Try it

1. Sign in and load the Judge Demo Pack. Select a pending clean invoice.
2. In **Muse review council**, click **Require & run Muse council**. This opts that invoice into the extra gate and makes three live calls. There is no mock vote generation.
3. Inspect each review's content risk, explanation, evidence keys, model, response metadata and latency. The forensic card identifies whether an image was supplied.
4. A matching signed report is usable for five minutes. All three assessments must be completed and low risk. A high/unknown result, disagreement or outage holds the simulation.
5. Use the separate **Review exact simulation** flow. The normal analyzer still runs; the gateway and database recheck the council requirement and existing deterministic controls before consuming an approval. No real money moves.
6. Any change in recipient, amount, source text, source document hash or geometry invalidates the report. Run a fresh council review if needed. The owner can explicitly **Return to standard review**, which removes only this optional requirement.

The report has an HMAC-SHA256 integrity signature under the ledger signing secret, owner/invoice binding, evidence fingerprint and expiry. A signature attests integrity, not truth. A separate read-only `/council` endpoint exposes only the current owner's report. The signed report itself is not an approval capability.

## Cost and failure controls

One council run uses three calls, each using the existing configured completion cap and timeout. Calls run concurrently in separate model contexts, with no automatic retries. Only one council runs at a time per service process. PostgreSQL serializes budget reservations across processes. Quotas count failed attempts: one run per owner/minute, three per owner/hour and ten globally/hour. A maximum of thirty council model calls per rolling hour is enforced globally; standard analyzer and chat usage are separate. Actual provider billing is authoritative.

The optional requirement is enabled before model calls start. An unfinished run, invalid signature, missing report, unavailable reviewer or expired evidence cannot establish council satisfaction. Failed runs remain stored for operational visibility. Do not describe denials caused by model outages as detected attacks.

## Visual proof

The **Visual Template Anchor Binding** node now includes normalized trusted/observed banking boxes, maximum center deviation, threshold and the synthetic routing-text comparison. Evidence explicitly names `live SAM 3.1 segments` when SAM output was used, or PDF geometry otherwise. The trusted demo template is PDF-derived. A layout deviation is a review signal, not a verified fraud finding or a general invoice-authenticity guarantee.

## Reproduce verification

```powershell
python -m unittest discover -s agent -p "test*.py"
cd gateway
go test ./...
cd ..
npm run build
# Explicit paid validation: up to three council calls + one normal analyzer call.
python scripts/check-council.py --url http://127.0.0.1:8083 --live
```

The live check creates a synthetic account and a private clean PDF, verifies model response provenance and forensic image input, then validates council-gated simulation and the audit chain. It stores an ignored diagnostic report without credentials. It does not measure general injection-detection accuracy. Tests cover disagreement, unavailable reviewers, report tampering, evidence mutation, expiry, isolation and budget rejection.

Recorded development validation: all 27 Python tests, Go tests and the production UI build passed. The live acceptance check passed 11/11 assertions against Neon using `muse-spark-1.3`. Reviewer latencies were Audit 4.60 s, Policy 2.77 s and Forensics 2.36 s, with reported totals of 2,093, 1,454 and 3,120 tokens respectively. These are one-run observations, not latency guarantees or detection-accuracy estimates. The normal risk call was additional. Docker/cloud redeployment and visual browser review are separate checks.

Future roadmap only: real financial connectors, federated threat distribution and hardware enclave execution. No real banking calls, escrow, biometric authorization, enclave protection or global immunity is implemented.
