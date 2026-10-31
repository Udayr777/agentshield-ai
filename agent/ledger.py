"""Tamper-evident audit chain. Trust: signing secret and exported checkpoints stay safe."""
import hashlib, hmac, json, os, secrets, time
from pathlib import Path
import workspace as ws

ZERO='0'*64
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def key():
    value=os.getenv('LEDGER_SIGNING_KEY')
    if value:return value.encode()
    path=Path(os.getenv('LEDGER_KEY_FILE',str(Path(__file__).resolve().parents[1]/'.ledger-key')))
    path.parent.mkdir(parents=True,exist_ok=True)
    try:
        with path.open('x') as f:f.write(secrets.token_hex(32))
        try:path.chmod(0o600)
        except OSError:pass
    except FileExistsError:pass
    return path.read_bytes().strip()
def sign(value):return hmac.new(key(),canonical(value).encode(),hashlib.sha256).hexdigest()
def migrate(db):
    db.execute('CREATE TABLE IF NOT EXISTS audit_ledger (owner_id TEXT NOT NULL, seq BIGINT NOT NULL, event_id TEXT NOT NULL UNIQUE, previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL, node_hash TEXT NOT NULL, entry_hash TEXT NOT NULL, signature TEXT NOT NULL, PRIMARY KEY(owner_id,seq))')

def nodes(checks):
    head=ZERO
    for index,check in enumerate(checks):head=digest({'previous':head,'index':index,'check':check})
    return head
def verify(db,pg,owner,checkpoint=None):
    rows=ws.query(db,'SELECT seq,event_id,previous_hash,event_hash,node_hash,entry_hash,signature FROM audit_ledger WHERE owner_id=? ORDER BY seq',(owner,),pg).fetchall()
    previous=ZERO;count=0;error=''
    for seq,event_id,prev,event_hash,node_hash,entry_hash,signature in rows:
        row=ws.query(db,'SELECT payload FROM audit WHERE id=? AND owner_id=?',(event_id,owner),pg).fetchone()
        content={'owner':owner,'seq':seq,'event_id':event_id,'previous':prev,'event_hash':event_hash,'node_hash':node_hash}
        if seq!=count+1 or prev!=previous or not row or digest(json.loads(row[0]))!=event_hash or nodes(json.loads(row[0]).get('checks',[]))!=node_hash or digest(content)!=entry_hash or not hmac.compare_digest(sign(content),signature):
            error='Audit content, node chain, sequence or signature mismatch';break
        count+=1;previous=entry_hash
    pinned=False
    if checkpoint:
        body={k:checkpoint.get(k) for k in ('owner','seq','head')}
        signature=checkpoint.get('signature','')
        valid=body['owner']==owner and type(body['seq']) is int and isinstance(signature,str) and hmac.compare_digest(sign(body),signature)
        if not valid:error='Checkpoint signature or owner mismatch'
        elif body['seq']>len(rows) or (body['seq']>0 and rows[body['seq']-1][5]!=body['head']) or (body['seq']==0 and body['head']!=ZERO):error='History deleted or replaced relative to checkpoint'
        else:pinned=True
    unsigned=ws.query(db,'SELECT COUNT(*) FROM audit a WHERE a.owner_id=? AND NOT EXISTS (SELECT 1 FROM audit_ledger l WHERE l.event_id=a.id)',(owner,),pg).fetchone()[0]
    body={'owner':owner,'seq':count,'head':previous}
    return {'valid':not error,'error':error,'events_verified':count,'legacy_unsigned':unsigned,'checkpoint_compared':pinned,'checkpoint':{**body,'signature':sign(body)},'algorithm':'SHA-256 + HMAC-SHA256','scope':'DB-only modification detection. Tail deletion requires a previously exported checkpoint; host/key compromise is outside this guarantee.'}

def append(db,pg,owner,data):
    # Serialize across processes as well as threads. SQL row and receipt commit together.
    if pg:db.execute('SELECT pg_advisory_xact_lock(4815162342)')
    result=verify(db,pg,owner)
    if not result['valid']:raise ws.APIError(409,'Audit integrity verification failed. Simulation halted.')
    seq=result['events_verified']+1
    content={'owner':owner,'seq':seq,'event_id':data['id'],'previous':result['checkpoint']['head'],'event_hash':digest(data),'node_hash':nodes(data.get('checks',[]))}
    ws.query(db,'INSERT INTO audit_ledger (owner_id,seq,event_id,previous_hash,event_hash,node_hash,entry_hash,signature) VALUES (?,?,?,?,?,?,?,?)',(owner,seq,data['id'],content['previous'],content['event_hash'],content['node_hash'],digest(content),sign(content)),pg)

def inspect(owner,connect,pg,checkpoint=None):
    with connect() as db:return verify(db,pg,owner,checkpoint)
