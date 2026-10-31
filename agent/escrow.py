"""Passkey-gated synthetic holds. No banking, blockchain, real funds, HSM attestation or push service."""
import base64,hashlib,hmac,json,os,secrets,time,uuid
from urllib.parse import urlparse
import workspace as ws,ledger
def b64(raw):return base64.urlsafe_b64encode(raw).decode().rstrip('=')
def unb64(value):return base64.urlsafe_b64decode(value+'='*((-len(value))%4))
def origin():
    value=os.getenv('WEBAUTHN_ORIGIN') or os.getenv('RENDER_EXTERNAL_URL') or os.getenv('GOOGLE_REDIRECT_URI','').split('/api/')[0] or 'http://localhost:5174'
    p=urlparse(value)
    if p.scheme not in ('http','https') or not p.hostname or p.username or p.path not in ('','/') or p.query or p.fragment or (p.scheme!='https' and p.hostname!='localhost'):raise ws.APIError(503,'Configure WEBAUTHN_ORIGIN as the exact HTTPS app origin, or localhost for local tests.')
    return value.rstrip('/'),p.hostname
def migrate(db):
    db.execute('CREATE TABLE IF NOT EXISTS passkey_credentials (id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, public_key TEXT NOT NULL, sign_count BIGINT NOT NULL, device_type TEXT NOT NULL, backed_up INTEGER NOT NULL, created_at BIGINT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS passkey_challenges (id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, session_hash TEXT NOT NULL, purpose TEXT NOT NULL, challenge TEXT NOT NULL, expires_at BIGINT NOT NULL, used INTEGER NOT NULL DEFAULT 0)')
    db.execute('CREATE TABLE IF NOT EXISTS simulated_holds (id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, invoice_id TEXT NOT NULL, payload TEXT NOT NULL, signature TEXT NOT NULL, UNIQUE(owner_id,invoice_id))')
def read(db,pg,owner,ident):
    row=ws.query(db,'SELECT payload,signature FROM simulated_holds WHERE id=? AND owner_id=?',(ident,owner),pg).fetchone()
    if not row:raise ws.APIError(404,'Synthetic hold not found in your account.')
    p=json.loads(row[0])
    if not hmac.compare_digest(ledger.sign(p),row[1]):raise ws.APIError(503,'Synthetic hold integrity failed.')
    return p
def save(db,pg,p):
    ws.query(db,'UPDATE simulated_holds SET payload=?,signature=? WHERE id=? AND owner_id=?',(json.dumps(p),ledger.sign(p),p['id'],p['owner_id']),pg)
def public(p):return {k:v for k,v in p.items() if k not in ('release_approval','owner_id','invoice_fingerprint','contract_nonce')}
def fingerprint(inv):return ledger.digest({k:inv[k] for k in ('id','recipient','amount_cents','text')})
def create(data,owner,connect,pg):
    inv=ws.get_invoice(data.get('invoice_id',''),owner,connect,pg)
    if inv.get('source')=='gmail' or inv['status']!='pending' or inv['recipient']!='vendor_acme' or not 0<inv['amount_cents']<=100000:raise ws.APIError(400,'Choose a pending, non-Gmail synthetic invoice for the registered vendor, up to USD 1,000.')
    now=int(time.time())
    with connect() as db:
        if pg:db.execute('SELECT pg_advisory_xact_lock(4815162345)')
        row=ws.query(db,'SELECT id FROM simulated_holds WHERE owner_id=? AND invoice_id=?',(owner,inv['id']),pg).fetchone()
        if row:
            previous=read(db,pg,owner,row[0])
            if previous['status']!='cancelled':return public(previous)
        p={'id':row[0] if row else uuid.uuid4().hex,'owner_id':owner,'invoice_id':inv['id'],'reference':inv['reference'],'recipient':inv['recipient'],'amount_cents':inv['amount_cents'],'invoice_fingerprint':fingerprint(inv),'contract_nonce':secrets.token_hex(16),'created_at':now,'expires_at':now+600,'status':'held','release_approval':'','mode':'simulation-only'}
        if row:save(db,pg,p)
        else:ws.query(db,'INSERT INTO simulated_holds(id,owner_id,invoice_id,payload,signature) VALUES (?,?,?,?,?)',(p['id'],owner,inv['id'],json.dumps(p),ledger.sign(p)),pg)
    return public(p)
def state(owner,connect,pg):
    configured_origin,rp=origin()
    with connect() as db:
        credentials=ws.query(db,'SELECT id,device_type,backed_up,created_at FROM passkey_credentials WHERE owner_id=?',(owner,),pg).fetchall()
        holds=ws.query(db,'SELECT id FROM simulated_holds WHERE owner_id=?',(owner,),pg).fetchall()
        contracts=[public(read(db,pg,owner,r[0])) for r in holds]
    return {'origin':configured_origin,'rp_id':rp,'credentials':[{'id':r[0],'device_type':r[1],'backed_up':bool(r[2]),'created_at':r[3]} for r in credentials],'holds':contracts,'limits':'Simulated holds only. WebAuthn user verification may use a device PIN or biometrics. No biometric data is received, and no HSM/hardware attestation or financial escrow is claimed.'}
def challenge(owner,session,purpose,connect,pg):
    if ws.session(session,connect,pg)['id']!=owner:raise ws.APIError(401,'Sign in again.')
    ident=uuid.uuid4().hex;raw=secrets.token_bytes(32)
    with connect() as db:
        ws.query(db,'DELETE FROM passkey_challenges WHERE expires_at<?',(int(time.time()),),pg)
        ws.query(db,'INSERT INTO passkey_challenges(id,owner_id,session_hash,purpose,challenge,expires_at) VALUES (?,?,?,?,?,?)',(ident,owner,hashlib.sha256(session.encode()).hexdigest(),purpose,b64(raw),int(time.time())+120),pg)
    return ident,raw
def claim(data,owner,session,purpose,connect,pg):
    if ws.session(session,connect,pg)['id']!=owner:raise ws.APIError(401,'Sign in again.')
    with connect() as db:
        row=ws.query(db,'UPDATE passkey_challenges SET used=1 WHERE id=? AND owner_id=? AND session_hash=? AND purpose=? AND used=0 AND expires_at>? RETURNING challenge',(data.get('challenge_id',''),owner,hashlib.sha256(session.encode()).hexdigest(),purpose,int(time.time())),pg).fetchone()
    if not row:raise ws.APIError(409,'Passkey challenge expired, used or belongs to another session. Start again.')
    return unb64(row[0])
def register_options(owner,session,connect,pg):
    from webauthn import generate_registration_options,options_to_json
    from webauthn.helpers.structs import AuthenticatorSelectionCriteria,UserVerificationRequirement,ResidentKeyRequirement,PublicKeyCredentialDescriptor
    user=ws.session(session,connect,pg);_,rp=origin()
    with connect() as db:rows=ws.query(db,'SELECT id FROM passkey_credentials WHERE owner_id=?',(owner,),pg).fetchall()
    if len(rows)>=5:raise ws.APIError(409,'Maximum five passkeys per account.')
    ident,raw=challenge(owner,session,'register',connect,pg)
    opts=generate_registration_options(rp_id=rp,rp_name='AgentShield Synthetic Lab',user_id=owner.encode(),user_name=user['name'],challenge=raw,exclude_credentials=[PublicKeyCredentialDescriptor(id=unb64(r[0])) for r in rows],authenticator_selection=AuthenticatorSelectionCriteria(resident_key=ResidentKeyRequirement.REQUIRED,require_resident_key=True,user_verification=UserVerificationRequirement.REQUIRED))
    return {'challenge_id':ident,'options':json.loads(options_to_json(opts))}
def register_verify(data,owner,session,connect,pg):
    from webauthn import verify_registration_response
    raw=claim(data,owner,session,'register',connect,pg);expected,rp=origin()
    try:v=verify_registration_response(credential=data.get('credential',{}),expected_challenge=raw,expected_rp_id=rp,expected_origin=expected,require_user_verification=True)
    except Exception:raise ws.APIError(400,'Passkey registration verification failed. No credential was stored.') from None
    with connect() as db:
        if ws.query(db,'SELECT id FROM passkey_credentials WHERE id=?',(b64(v.credential_id),),pg).fetchone():raise ws.APIError(409,'This passkey is already registered.')
        ws.query(db,'INSERT INTO passkey_credentials(id,owner_id,public_key,sign_count,device_type,backed_up,created_at) VALUES (?,?,?,?,?,?,?)',(b64(v.credential_id),owner,b64(v.credential_public_key),v.sign_count,v.credential_device_type.value,int(v.credential_backed_up),int(time.time())),pg)
    return state(owner,connect,pg)
def release_options(data,owner,session,connect,pg):
    from webauthn import generate_authentication_options,options_to_json
    from webauthn.helpers.structs import UserVerificationRequirement,PublicKeyCredentialDescriptor
    with connect() as db:
        p=read(db,pg,owner,data.get('hold_id',''));rows=ws.query(db,'SELECT id FROM passkey_credentials WHERE owner_id=?',(owner,),pg).fetchall()
    if not rows or p['status'] not in ('held','blocked') or p['expires_at']<=time.time():raise ws.APIError(409,'Register a passkey and select an unexpired held/blocked contract.')
    ident,raw=challenge(owner,session,'release:'+p['id']+':'+p['contract_nonce'],connect,pg);_,rp=origin()
    opts=generate_authentication_options(rp_id=rp,challenge=raw,allow_credentials=[PublicKeyCredentialDescriptor(id=unb64(r[0])) for r in rows],user_verification=UserVerificationRequirement.REQUIRED)
    return {'challenge_id':ident,'options':json.loads(options_to_json(opts)),'hold':public(p)}
def authorize_release(data,owner,session,connect,pg):
    from webauthn import verify_authentication_response
    with connect() as db:p=read(db,pg,owner,data.get('hold_id',''))
    raw=claim(data,owner,session,'release:'+p['id']+':'+p['contract_nonce'],connect,pg);expected,rp=origin();credential=data.get('credential',{})
    with connect() as db:
        if pg:db.execute('SELECT pg_advisory_xact_lock(4815162345)')
        p=read(db,pg,owner,p['id']);inv=ws.get_invoice(p['invoice_id'],owner,connect,pg)
        if p['status'] not in ('held','blocked') or p['expires_at']<=time.time() or p['invoice_fingerprint']!=fingerprint(inv) or inv['status']!='pending':raise ws.APIError(409,'Contract changed, expired or already used.')
        row=ws.query(db,'SELECT public_key,sign_count FROM passkey_credentials WHERE id=? AND owner_id=?',(credential.get('id',''),owner),pg).fetchone()
        if not row:raise ws.APIError(403,'Passkey not registered to this account.')
        try:v=verify_authentication_response(credential=credential,expected_challenge=raw,expected_rp_id=rp,expected_origin=expected,credential_public_key=unb64(row[0]),credential_current_sign_count=row[1],require_user_verification=True)
        except Exception:raise ws.APIError(403,'Passkey assertion failed. Simulation remains held.') from None
        ws.query(db,'UPDATE passkey_credentials SET sign_count=? WHERE id=? AND owner_id=?',(v.new_sign_count,credential['id'],owner),pg)
        token=secrets.token_hex(32)
        ws.query(db,'INSERT INTO approvals(token,recipient,amount_cents,expires_at,used,owner_id,invoice_id) VALUES (?,?,?,?,?,?,?)',(token,inv['recipient'],inv['amount_cents'],int(time.time())+120,0,owner,inv['id']),pg)
        p['status']='release_authorized';p['release_approval']=token;save(db,pg,p)
    return {'payment':{'recipient':inv['recipient'],'amount_cents':inv['amount_cents'],'invoice':inv['text'],'invoice_id':inv['id'],'approval_id':token,'approval':''},'hold_id':p['id']}
def guard(db,pg,owner,payment):
    row=ws.query(db,'SELECT id FROM simulated_holds WHERE owner_id=? AND invoice_id=?',(owner,payment.get('invoice_id','')),pg).fetchone()
    if not row:return {'required':False,'satisfied':True}
    p=read(db,pg,owner,row[0])
    if p['status']=='cancelled':return {'required':False,'satisfied':True}
    proposal={'id':payment.get('invoice_id'),'recipient':payment.get('recipient'),'amount_cents':payment.get('amount_cents'),'text':payment.get('invoice')}
    matched=p['status']=='release_authorized' and p['expires_at']>time.time() and p['invoice_fingerprint']==fingerprint(proposal) and hmac.compare_digest(p['release_approval'],payment.get('approval_id',''))
    return {'required':True,'satisfied':bool(matched),'hold_id':p['id'],'reason':'Passkey verification and the exact signed synthetic hold are required.'}
def finish(db,pg,owner,payment,decision):
    result=guard(db,pg,owner,payment)
    if result['required'] and result['satisfied']:
        p=read(db,pg,owner,result['hold_id']);p['status']='released' if decision=='allow' else 'blocked';p['release_approval']='';save(db,pg,p)
def cancel(data,owner,connect,pg):
    with connect() as db:
        p=read(db,pg,owner,data.get('hold_id',''))
        if p['status']=='released':raise ws.APIError(409,'A released hold cannot be cancelled.')
        if p['status']=='release_authorized':
            cap=ws.query(db,'SELECT expires_at FROM approvals WHERE token=? AND owner_id=?',(p['release_approval'],owner),pg).fetchone()
            if cap and cap[0]>time.time():raise ws.APIError(409,'Release is in progress. Wait for its two-minute authorization window to expire.')
            ws.query(db,'UPDATE approvals SET used=1 WHERE token=? AND owner_id=?',(p['release_approval'],owner),pg)
        p['status']='cancelled';p['release_approval']='';save(db,pg,p)
    return state(owner,connect,pg)
