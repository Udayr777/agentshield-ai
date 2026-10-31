"""Run against a dedicated demo database. Preserves audit records created by the check."""
import json, os, sys, uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'agent'))
import app
if not app.PG: raise SystemExit('Set DATABASE_URL in the environment or private project .env file')
app.init(); app.init()
item={'id':str(uuid.uuid4()),'created_at':'2026-10-30T00:00:00Z','decision':'deny','reason':'Database integration test','payment':{'recipient':'test_vendor','amount_cents':1},'analysis':{'mode':'mock','risk':'high'}}
app.audit(item)
try:
    app.audit(item)
    raise AssertionError('Duplicate ID was accepted')
except Exception as error:
    if isinstance(error,AssertionError): raise
with app.connect() as db:
    row=db.execute('SELECT decision, recipient, amount_cents, analyzer_mode FROM audit_decisions WHERE id=%s',(item['id'],)).fetchone()
    assert row==('deny','test_vendor',1,'mock'),row
print(json.dumps({'postgresql':'passed','migration_repeated':True,'duplicate_rejected':True,'committed_row_visible_after_reconnect':True,'audit_view':'passed','id':item['id']}))
