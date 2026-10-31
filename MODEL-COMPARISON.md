# Spark versus Wonder evaluation

This operator-only experiment compares `muse-spark-1.3` and `muse-wonder-1.0` on the same invoice-content classification task. It does not change the production model or integrate another payment authority. No database initialization, invoice creation, payment simulation or approval issuance occurs in the runner. Existing Meta telemetry records only request metadata, not prompts or answers.

## Run

Use the project Python environment with `agent/requirements.txt` installed and your private Meta configuration available. Never supply keys as command-line arguments.

```powershell
# Preview the plan without API calls:
python scripts/compare-models.py

# Full run: 12 cases x 2 models = 24 calls; consumes Meta credits:
python scripts/compare-models.py --live --output samples/model-comparison-results.json

# Smaller balanced pilot: 4 cases x 2 models = 8 calls:
python scripts/compare-models.py --live --limit 4 --output comparison-results.json
```

The JSON contains per-case predictions, reasons, errors/abstentions, elapsed request latency, provider-reported token usage, dataset/analyzer SHA-256 hashes, model settings and model summaries. A companion CSV makes the classifications easy to compare. Partial JSON results are saved after every call. No retries hide failed requests; a run with unknown/error results exits with code 2. Model access must exist on the configured endpoint. Output field `model_returned` is the model identifier returned by AgentShield's analyzer metadata, not an independent provider routing attestation.

## Method and limits

- Six benign and six instruction-injection cases, interleaved. Each model sees identical recipient, amount, content and the existing risk-classification prompt.
- The first model alternates across cases to reduce simple order bias. Both share configured reasoning effort, completion cap and timeout; provider infrastructure may still differ.
- Every case gets one response from each model. There is no seed/repeat estimate of variability.
- Unknown responses and provider errors are separate from correct classifications. Benign `high` and attack `low` classifications are reported separately. Production treats unknown as a denial, but this benchmark never executes the gateway.
- Latency is the local elapsed analyzer request time, not complete application latency. Median and nearest-rank p95 are descriptive only; twelve observations are too few for dependable tail performance estimates.
- The fixture set was authored after the current prompt, but remains a small author-labeled synthetic set, not external independent validation or a real-world fraud benchmark. It has no vision/SAM, OCR, multi-page, multilingual or exhaustive adaptive-attack coverage.
- Token totals do not equal money: per-model prices can differ. No automatic model promotion occurs.

Review cases where predictions disagree first. If accuracy ties, latency and usage can inform the choice for this task, but do not establish general model superiority. Keep the deterministic controls unchanged regardless of the result.

## Recorded live run — October 31, 2026

| Measurement | Muse Spark 1.3 | Muse Wonder 1.0 |
|---|---:|---:|
| Matching labels | 12/12 | 12/12 |
| Benign flagged high | 0/6 | 0/6 |
| Attacks classified low | 0/6 | 0/6 |
| Unknown/provider errors | 0 | 0 |
| Median request latency | 1,772.23 ms | 3,817.28 ms |
| Nearest-rank p95 (small sample) | 2,816.76 ms | 4,588.58 ms |
| Reported total tokens | 8,283 | 7,844 |

The full 24-call run and hashes are committed in `samples/model-comparison-results.json` and its CSV companion. Both models matched this dataset; Spark was faster in this run. Keep Spark as the application default. This result does not show that either model detects all attacks, and lower token usage does not establish lower cost across different models.
