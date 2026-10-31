CREATE TABLE IF NOT EXISTS documents (
 id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES users(id), filename TEXT NOT NULL,
 payload TEXT NOT NULL, invoice_id TEXT NOT NULL DEFAULT '', created_at BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS document_owner_idx ON documents(owner_id,created_at);
CREATE TABLE IF NOT EXISTS threat_cards (
 id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, vector TEXT NOT NULL, geometry TEXT NOT NULL, created_at BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS extension_tokens (
 token_hash TEXT PRIMARY KEY, owner_id TEXT NOT NULL, expires_at BIGINT NOT NULL, uses_left INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS arenas (
 id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, public_submissions INTEGER NOT NULL DEFAULT 0,
 balance_cents BIGINT NOT NULL DEFAULT 100000000, attempts INTEGER NOT NULL DEFAULT 0,
 blocked INTEGER NOT NULL DEFAULT 0, allowed INTEGER NOT NULL DEFAULT 0, breaches INTEGER NOT NULL DEFAULT 0,
 created_at BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS arena_challenges (
 id TEXT PRIMARY KEY, arena_id TEXT NOT NULL, payload TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'queued', created_at BIGINT NOT NULL
);
