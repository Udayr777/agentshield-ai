"""Opt-in, single-service shared defense. Only fixed categories from blocked synthetic fixtures leave an account."""
import hashlib,hmac,json,re,time,unicodedata
import workspace as ws,ledger
SIGNALS={
 'control_bypass':r'\b(ignore previous|override.{0,25}(policy|controls|security)|bypass.{0,20}(policy|verification)|disable safeguards)',
 'recipient_redirect':r'\b(redirect.{0,65}(payment|account|wallet)|pay.{0,60}attacker|new account|attacker_wallet)',
 'authority_forgery':r'\b(manager already approved|cfo.{0,30}authoriz|skip verification|forged approval)',
 'audit_suppression':r'\b(hide.{0,40}(audit|payment|entry)|suppress.{0,20}(audit|log)|delete.{0,20}audit)',
 'hidden_instruction':r'\b(hidden instruction|invisible instruction|white.on.white payload)'}
def migrate(db):
    db.execute('CREATE TABLE IF NOT EXISTS network_preferences (owner_id TEXT PRIMARY KEY, enabled INTEGER NOT NULL DEFAULT 0)')
    db.execute('CREATE TABLE IF NOT EXISTS network_signatures (id TEXT PRIMARY KEY, seq BIGINT NOT NULL UNIQUE, categories TEXT NOT NULL, previous_hash TEXT NOT NULL, entry_hash TEXT NOT NULL, signature TEXT NOT NULL)')
def categories(payment):
    text=unicodedata.normalize('NFKC',str(payment.get('invoice',''))[:8000]).lower()
    return sorted(k for k,pattern in SIGNALS.items() if re.search(pattern,text))
def preference(db,pg,owner):
    row=ws.query(db,'SELECT enabled FROM network_preferences WHERE owner_id=?',(owner,),pg).fetchone();return bool(row and row[0])
def set_preference(data,owner,connect,pg):
    if type(data.get('enabled')) is not bool:raise ws.APIError(400,'Choose whether to join the synthetic threat network.')
    with connect() as db:ws.query(db,'INSERT INTO network_preferences(owner_id,enabled) VALUES (?,?) ON CONFLICT(owner_id) DO UPDATE SET enabled=excluded.enabled',(owner,int(data['enabled'])),pg)
    return state(owner,connect,pg)
def verified_feed(db,pg):
    rows=db.execute('SELECT id,seq,categories,previous_hash,entry_hash,signature FROM network_signatures ORDER BY seq').fetchall();previous=ledger.ZERO;out=[]
    for ident,seq,encoded,prev,head,sig in rows:
        flags=json.loads(encoded);body={'id':ident,'seq':seq,'categories':flags,'previous':prev}
        if seq!=len(out)+1 or prev!=previous or not isinstance(flags,list) or len(flags)<2 or flags!=sorted(set(flags)) or any(f not in SIGNALS for f in flags) or ident!=ledger.digest(flags) or head!=ledger.digest(body) or not hmac.compare_digest(ledger.sign(body),sig):raise ws.APIError(503,'Shared signature integrity failed. Network-enabled simulations are held.')
        out.append({'id':ident,'sequence':seq,'categories':flags});previous=head
    return out,previous
def preflight(db,pg,owner,payment):
    if not preference(db,pg,owner):return {'blocked':False,'enabled':False}
    feed,head=verified_feed(db,pg);found=set(categories(payment))
    match=next((r for r in feed if set(r['categories'])<=found),None)
    return {'blocked':bool(match),'enabled':True,'signature_id':match['id'] if match else None,'categories':match['categories'] if match else [],'reason':'Shared synthetic threat pattern matched before model processing.' if match else 'No shared pattern matched. Normal checks still apply.'}
def observe(db,pg,owner,receipt):
    if receipt.get('decision')!='deny' or not preference(db,pg,owner):return
    if receipt.get('analysis',{}).get('risk')!='high':return # Model outages are not detected attacks.
    p=receipt.get('payment',{})
    # Enrollment is server-owned demo provenance, never a client "synthetic" checkbox.
    fixture=ws.query(db,'SELECT i.invoice_text FROM judge_pack j JOIN invoices i ON i.id=j.invoice_id AND i.owner_id=j.owner_id WHERE j.owner_id=? AND j.invoice_id=?',(owner,p.get('invoice_id','')),pg).fetchone()
    if not fixture or fixture[0]!=p.get('invoice'):return
    flags=categories(p)
    if len(flags)<2:return
    if pg:db.execute('SELECT pg_advisory_xact_lock(4815162344)')
    feed,previous=verified_feed(db,pg);ident=ledger.digest(flags)
    if any(r['id']==ident for r in feed):return
    body={'id':ident,'seq':len(feed)+1,'categories':flags,'previous':previous}
    ws.query(db,'INSERT INTO network_signatures(id,seq,categories,previous_hash,entry_hash,signature) VALUES (?,?,?,?,?,?)',(ident,body['seq'],json.dumps(flags),previous,ledger.digest(body),ledger.sign(body)),pg)
def state(owner,connect,pg):
    with connect() as db:feed,head=verified_feed(db,pg);enabled=preference(db,pg,owner)
    checkpoint={'sequence':len(feed),'head':head}
    return {'enabled':enabled,'signatures':feed,'checkpoint':{**checkpoint,'signature':ledger.sign(checkpoint)},'scope':'One shared registry on this service, not a global decentralized ledger. Fixed categories only; no invoice text, names, bank details, document hashes, geometry or account IDs are published. Only blocked server-owned judge fixtures contribute. No guarantee of immunity.'}
def public_feed(connect,pg):
    result=state('',connect,pg);result.pop('enabled');return result
