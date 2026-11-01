# Synthetic benchmark report

Measured October 31, 2026 on Windows 11. These are local, scripted synthetic tests, not production accuracy, fraud detection certification, or live model quality measurements.

## Policy gateway

- 35/35 expected outcomes across seven scenarios, five sequential rounds.
- False blocks on authorized fixtures: 0/5.
- Missed denials on attack/invalid-approval fixtures: 0/30.
- HTTP round trip including durable SQLite audit: median 71.3 ms; p95 100.0 ms. No warmup.
 - Go gateway, Python analyzer in explicit mock mode, isolated local SQLite database; no external model calls or real payments.

| Scenario | Matched expected | Expected |
|---|---:|---|
| Authorized payment | 5/5 | allow |
| Invoice account takeover | 5/5 | deny |
| Amount escalation | 5/5 | deny |
| Forged approval | 5/5 | deny |
| Policy override injection | 5/5 | deny |
| Approval replay | 5/5 | deny |
| Expired approval | 5/5 | deny |

[Raw policy results](samples/judge-policy-benchmark.json)

## Local visual inspection

- Detected anomalies in 12/12 tampered PDFs; false-positive documents 0/3 clean PDFs.
- Median local inspection time: 26.4 ms.
 - Families: white text, tiny text, invisible text layer and overlapping text. Three variants per family, three clean fixtures.
- Uses local PDF geometry and image heuristics. No SAM or Muse inference is measured. Timings exclude PDF rendering, upload, database, models and network.

[Raw visual results](samples/visual-inspection/results.json)

## Reproduce

```powershell
python scripts/benchmark.py --rounds 5 --url http://127.0.0.1:8088 --output samples/judge-policy-benchmark.json
python scripts/benchmark-visual.py
```

Start the isolated gateway on 8088 against an agent on 8015 configured with ANALYZER_MODE=mock, COOKIE_SECURE=false, DATABASE_URL empty and a separate SQLITE_PATH. The benchmark creates a fresh synthetic account. Never point the policy sweep at a live-model server unless you explicitly intend model charges. Use a fresh benchmark database for comparable runs. Fixture regeneration changes PDF byte-level metadata; measured findings are the comparison target.

## Limitations

Repeated synthetic templates are not independent real-world samples. Zero observed false positives on a few fixtures does not establish a zero false-positive rate. These timings are not Render/PostgreSQL or concurrent-load performance. Scripted replay does not measure autonomous model planning. The report does not evaluate SAM segmentation accuracy, model detection recall, credential security, browser recording or host compromise resistance. Live provider metadata demonstrates a response, not prize eligibility or generalized model accuracy.
