CREATE TABLE IF NOT EXISTS users (
 id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
 salt TEXT NOT NULL, password_hash TEXT NOT NULL, created_at BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), expires_at BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS invoices (
 id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES users(id), reference TEXT NOT NULL,
 vendor TEXT NOT NULL, recipient TEXT NOT NULL, amount_cents BIGINT NOT NULL,
 due_date TEXT NOT NULL, invoice_text TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', created_at BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS invoice_owner_idx ON invoices(owner_id,created_at);
CREATE TABLE IF NOT EXISTS messages (
 id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES users(id), invoice_id TEXT NOT NULL REFERENCES invoices(id),
 role TEXT NOT NULL, content TEXT NOT NULL, mode TEXT NOT NULL, created_at BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS message_owner_invoice_idx ON messages(owner_id,invoice_id,created_at);
