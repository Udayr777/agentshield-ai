-- Idempotent migration. Keeps existing audit rows and the original text payload.
CREATE TABLE IF NOT EXISTS audit (
    id TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    stored_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE audit ADD COLUMN IF NOT EXISTS stored_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;
CREATE INDEX IF NOT EXISTS audit_stored_at_idx ON audit (stored_at DESC);
CREATE TABLE IF NOT EXISTS approvals (
    token TEXT PRIMARY KEY,
    recipient TEXT NOT NULL,
    amount_cents BIGINT NOT NULL,
    expires_at BIGINT NOT NULL,
    used INTEGER NOT NULL DEFAULT 0
);
CREATE OR REPLACE VIEW audit_decisions AS
SELECT id, stored_at,
       payload::jsonb ->> 'created_at' AS proposed_at,
       payload::jsonb ->> 'decision' AS decision,
       payload::jsonb ->> 'reason' AS reason,
       payload::jsonb #>> '{payment,recipient}' AS recipient,
       (payload::jsonb #>> '{payment,amount_cents}')::bigint AS amount_cents,
       payload::jsonb #>> '{analysis,mode}' AS analyzer_mode,
       payload::jsonb #>> '{analysis,risk}' AS risk
FROM audit;
