"""Read-only Gmail OAuth and explicit attachment import. Never sends mail or invokes Meta."""
import base64,datetime,hashlib,json,os,re,secrets,threading,time,urllib.parse,urllib.request,urllib.error
from pathlib import Path
import workspace as ws,visual
SCOPE='https://www.googleapis.com/auth/gmail.readonly'
ROOT=Path(__file__).resolve().parents[1];IMPORT_LOCK=threading.Lock()
DEFAULT_QUERY='newer_than:180d has:attachment (filename:pdf OR filename:png OR filename:jpg OR filename:jpeg) (invoice OR bill OR receipt)'
def migrate(db):
    for sql in [
      'CREATE TABLE IF NOT EXISTS gmail_states (state_hash TEXT PRIMARY KEY, owner_id TEXT NOT NULL, session_hash TEXT NOT NULL, secret TEXT NOT NULL, expires_at BIGINT NOT NULL, used INTEGER NOT NULL DEFAULT 0)',
      'CREATE TABLE IF NOT EXISTS gmail_connections (owner_id TEXT PRIMARY KEY, mailbox TEXT NOT NULL, secret TEXT NOT NULL, updated_at BIGINT NOT NULL)',
      'CREATE TABLE IF NOT EXISTS gmail_imports (owner_id TEXT NOT NULL, source_hash TEXT NOT NULL, content_hash TEXT NOT NULL, document_id TEXT NOT NULL, created_at BIGINT NOT NULL, PRIMARY KEY(owner_id,source_hash), UNIQUE(owner_id,content_hash))']:
        db.execute(sql)
def config():
    cfg={}
    path=ROOT/'.gmail-oauth-client.json'
    if path.exists():cfg=json.loads(path.read_text(encoding='utf-8-sig')).get('web',{})
    client=os.getenv('GOOGLE_CLIENT_ID') or cfg.get('client_id');secret=os.getenv('GOOGLE_CLIENT_SECRET') or cfg.get('client_secret')
    redirect=os.getenv('GOOGLE_REDIRECT_URI') or next(iter(cfg.get('redirect_uris',[])),'')
    url=urllib.parse.urlparse(redirect)
    if not client or not secret or not redirect or url.path!='/api/gmail/callback' or url.query or url.fragment or url.username or not (url.scheme=='https' or (url.scheme=='http' and url.hostname in ('127.0.0.1','localhost'))):raise ws.APIError(503,'Gmail OAuth is not configured. Ask the app owner to configure the web client and callback.')
    return {'web':{'client_id':client,'client_secret':secret,'auth_uri':'https://accounts.google.com/o/oauth2/auth','token_uri':'https://oauth2.googleapis.com/token','redirect_uris':[redirect]}}
def cipher():
    from cryptography.fernet import Fernet
    key=os.getenv('GMAIL_TOKEN_KEY')
    if not key:
        if os.getenv('RENDER'):raise ws.APIError(503,'Configure a persistent GMAIL_TOKEN_KEY in Render before connecting Gmail.')
        path=ROOT/'.gmail-token-key'
        try:
            with path.open('xb') as f:f.write(Fernet.generate_key())
            try:path.chmod(0o600)
            except OSError:pass
        except FileExistsError:pass
        key=path.read_bytes()
    return Fernet(key.encode() if isinstance(key,str) else key)
def encrypt(owner,value):return cipher().encrypt(json.dumps({'owner':owner,'value':value}).encode()).decode()
def decrypt(owner,value):
    try:
        result=json.loads(cipher().decrypt(value.encode()))
        if result['owner']!=owner:raise ValueError('owner')
        return result['value']
    except Exception:raise ws.APIError(503,'Gmail credentials cannot be decrypted. Reconnect using the configured token key.') from None
def flow(state,verifier):
    from google_auth_oauthlib.flow import Flow
    cfg=config();return Flow.from_client_config(cfg,scopes=[SCOPE],state=state,code_verifier=verifier,redirect_uri=cfg['web']['redirect_uris'][0])
def status(owner,connect,pg):
    try:cfg=config();cipher();configured=True;redirect=cfg['web']['redirect_uris'][0]
    except Exception:configured=False;redirect=''
    with connect() as db:
        row=ws.query(db,'SELECT mailbox FROM gmail_connections WHERE owner_id=?',(owner,),pg).fetchone()
        imports=ws.query(db,'SELECT g.document_id,d.filename,d.invoice_id FROM gmail_imports g JOIN documents d ON d.id=g.document_id AND d.owner_id=g.owner_id WHERE g.owner_id=? ORDER BY g.created_at DESC LIMIT 30',(owner,),pg).fetchall()
    return {'configured':configured,'connected':bool(row),'mailbox':row[0] if row else '', 'redirect_uri':redirect,'imports':[dict(zip(('document_id','filename','invoice_id'),r)) for r in imports],'scope':'gmail.readonly','meta_processing':'blocked_for_gmail_imports'}
def begin(owner,session_token,connect,pg):
    user=ws.session(session_token,connect,pg)
    if user['id']!=owner:raise ws.APIError(403,'Session mismatch.')
    state=secrets.token_urlsafe(32);verifier=secrets.token_urlsafe(64);cfg=config()
    f=flow(state,verifier);url,_=f.authorization_url(access_type='offline',prompt='consent',include_granted_scopes='false')
    with connect() as db:
        ws.query(db,'DELETE FROM gmail_states WHERE expires_at<?',(int(time.time()),),pg)
        ws.query(db,'INSERT INTO gmail_states(state_hash,owner_id,session_hash,secret,expires_at) VALUES (?,?,?,?,?)',(hashlib.sha256(state.encode()).hexdigest(),owner,hashlib.sha256(session_token.encode()).hexdigest(),encrypt(owner,{'verifier':verifier,'client_id':cfg['web']['client_id'],'redirect':cfg['web']['redirect_uris'][0]}),int(time.time())+600),pg)
    return {'authorization_url':url}
def api(token,path,params=None,limit=7_000_000):
    url='https://gmail.googleapis.com/gmail/v1/users/me/'+path
    if params:url+='?'+urllib.parse.urlencode(params,doseq=True)
    req=urllib.request.Request(url,headers={'Authorization':'Bearer '+token})
    try:
        with urllib.request.urlopen(req,timeout=25) as r:
            raw=r.read(limit+1)
            if len(raw)>limit:raise ws.APIError(413,'Gmail response exceeds the import limit.')
            return json.loads(raw)
    except urllib.error.HTTPError as e:raise ws.APIError(401 if e.code in (401,403) else 503,'Gmail access failed. Check consent, test-user access or reconnect.') from None
def callback(params,connect,pg):
    state=params.get('state','');code=params.get('code','')
    if not isinstance(state,str) or not 20<=len(state)<=200:raise ws.APIError(400,'Invalid OAuth state. Start Connect Gmail again.')
    with connect() as db:
        row=ws.query(db,'UPDATE gmail_states SET used=1 WHERE state_hash=? AND used=0 AND expires_at>? RETURNING owner_id,session_hash,secret',(hashlib.sha256(state.encode()).hexdigest(),int(time.time())),pg).fetchone()
        if not row:raise ws.APIError(400,'OAuth request expired or already used. Start again.')
        owner,session_hash,sealed=row
        if not ws.query(db,'SELECT user_id FROM sessions WHERE token_hash=? AND user_id=? AND expires_at>?',(session_hash,owner,int(time.time())),pg).fetchone():raise ws.APIError(401,'Sign in and reconnect Gmail.')
    if params.get('error') or not isinstance(code,str) or not 1<=len(code)<=4096:raise ws.APIError(400,'Google authorization was not completed.')
    value=decrypt(owner,sealed);cfg=config()['web']
    if value['client_id']!=cfg['client_id'] or value['redirect']!=cfg['redirect_uris'][0]:raise ws.APIError(400,'OAuth configuration changed. Start again.')
    try:
        f=flow(state,value['verifier']);f.fetch_token(code=code,timeout=25);token=f.oauth2session.token
        granted=token.get('scope',[])
        scopes=set(granted.split() if isinstance(granted,str) else granted)
        if SCOPE not in scopes or scopes-{SCOPE,'openid','https://www.googleapis.com/auth/userinfo.email','https://www.googleapis.com/auth/userinfo.profile'}:raise ValueError('scope')
        if not token.get('access_token') or not token.get('refresh_token'):raise ValueError('offline_access')
        profile=api(token['access_token'],'profile',limit=20000)
        creds={'token':token['access_token'],'refresh_token':token['refresh_token'],'expires_at':int(token.get('expires_at',time.time()+int(token.get('expires_in',3600))))}
    except ws.APIError:raise
    except Exception:raise ws.APIError(503,'Google token exchange failed. Reconnect and grant read-only access.') from None
    with connect() as db:ws.query(db,'INSERT INTO gmail_connections(owner_id,mailbox,secret,updated_at) VALUES (?,?,?,?) ON CONFLICT(owner_id) DO UPDATE SET mailbox=excluded.mailbox,secret=excluded.secret,updated_at=excluded.updated_at',(owner,profile['emailAddress'],encrypt(owner,creds),int(time.time())),pg)
    return {'connected':True}
def access(owner,connect,pg):
    with connect() as db:row=ws.query(db,'SELECT mailbox,secret FROM gmail_connections WHERE owner_id=?',(owner,),pg).fetchone()
    if not row:raise ws.APIError(409,'Connect Gmail first.')
    creds=decrypt(owner,row[1])
    if creds['expires_at']<time.time()+60:
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            cfg=config()['web'];c=Credentials(creds['token'],refresh_token=creds['refresh_token'],token_uri=cfg['token_uri'],client_id=cfg['client_id'],client_secret=cfg['client_secret'],scopes=[SCOPE])
            request=Request()
            def bounded(*args,**kwargs):kwargs['timeout']=25;return request(*args,**kwargs)
            c.refresh(bounded);creds={'token':c.token,'refresh_token':c.refresh_token,'expires_at':int(time.time())+3500}
        except Exception:raise ws.APIError(401,'Gmail authorization expired. Please reconnect.') from None
        with connect() as db:ws.query(db,'UPDATE gmail_connections SET secret=?,updated_at=? WHERE owner_id=?',(encrypt(owner,creds),int(time.time()),owner),pg)
    return row[0],creds['token']
def ident(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,256}',value):raise ws.APIError(400,'Invalid Gmail message identifier.')
    return value
def attachment_reference(value):
    # Google attachment references are opaque and can be much longer than message IDs.
    # Encode the entire value as one path segment; never concatenate raw provider data.
    if not isinstance(value,str) or not 1<=len(value)<=8192 or any(ord(c)<33 or ord(c)==127 for c in value):
        raise ws.APIError(400,'Invalid or oversized Gmail attachment reference. Select the attachment again.')
    return urllib.parse.quote(value,safe='')
def search(data,owner,connect,pg):
    query=data.get('query',DEFAULT_QUERY)
    if not isinstance(query,str) or not 1<=len(query)<=300:raise ws.APIError(400,'Use a search query up to 300 characters.')
    _,token=access(owner,connect,pg);listing=api(token,'messages',{'q':query,'maxResults':10},limit=100000);out=[]
    for item in listing.get('messages',[])[:10]:
        message=api(token,'messages/'+ident(item['id']),{'format':'metadata','metadataHeaders':['Subject','From','Date']},limit=100000)
        headers={h['name'].lower():h['value'] for h in message.get('payload',{}).get('headers',[])}
        out.append({'id':item['id'],'subject':headers.get('subject','(no subject)')[:300],'from':headers.get('from','')[:300],'date':headers.get('date','')[:100]})
    return {'messages':out,'query':query,'limit':10}
def parts(message):
    out=[]
    def visit(part,depth=0):
        if depth>10 or len(out)>=50:return
        mime=part.get('mimeType','');body=part.get('body',{})
        if part.get('filename') and mime in ('application/pdf','image/png','image/jpeg'):
            out.append({'part_id':part.get('partId') or '0','filename':part['filename'].replace('\\','/').split('/')[-1][:120],'mime':mime,'size':body.get('size',0),'body':body})
        for child in part.get('parts',[])[:50]:visit(child,depth+1)
    visit(message.get('payload',{}));return out
def attachments(data,owner,connect,pg):
    _,token=access(owner,connect,pg);message=api(token,'messages/'+ident(data.get('message_id')),{'format':'full'})
    return {'attachments':[{k:v for k,v in p.items() if k!='body'} for p in parts(message) if 0<p['size']<=visual.MAX_BYTES]}
def import_selected(data,owner,connect,pg):
    if data.get('confirmed') is not True:raise ws.APIError(400,'Explicitly select and confirm this attachment for import.')
    message_id=ident(data.get('message_id'));part_id=data.get('part_id')
    with IMPORT_LOCK:
        mailbox,token=access(owner,connect,pg);source=hashlib.sha256((mailbox.lower()+'|'+message_id+'|'+str(part_id)).encode()).hexdigest()
        with connect() as db:row=ws.query(db,'SELECT document_id FROM gmail_imports WHERE owner_id=? AND source_hash=?',(owner,source),pg).fetchone()
        if row:return {'document_id':row[0],'duplicate':True}
        message=api(token,'messages/'+message_id,{'format':'full'});part=next((p for p in parts(message) if p['part_id']==part_id),None)
        if not part or not 0<part['size']<=visual.MAX_BYTES:raise ws.APIError(400,'Choose a PDF, PNG or JPEG attachment up to 4 MB.')
        body=part['body']
        if body.get('attachmentId'):body=api(token,'messages/'+message_id+'/attachments/'+attachment_reference(body['attachmentId']))
        encoded=body.get('data','')
        try:
            if len(encoded)>6_000_000:raise ValueError('size')
            raw=base64.b64decode(encoded+'='*((-len(encoded))%4),altchars=b'-_',validate=True)
        except Exception:raise ws.APIError(400,'Invalid attachment data.') from None
        content=hashlib.sha256(raw).hexdigest()
        with connect() as db:row=ws.query(db,'SELECT document_id FROM gmail_imports WHERE owner_id=? AND content_hash=?',(owner,content),pg).fetchone()
        if row:return {'document_id':row[0],'duplicate':True}
        draft=visual.ingest({'filename':part['filename'],'mime':part['mime'],'data':base64.b64encode(raw).decode(),'use_muse':False},owner,connect,pg,source='gmail')
        with connect() as db:ws.query(db,'INSERT INTO gmail_imports(owner_id,source_hash,content_hash,document_id,created_at) VALUES (?,?,?,?,?)',(owner,source,content,draft['id'],int(time.time())),pg)
        return {'document_id':draft['id'],'duplicate':False,'note':'Private draft created using local parsing only. No Meta call or payment.'}
def disconnect(owner,connect,pg):
    with connect() as db:
        row=ws.query(db,'SELECT secret FROM gmail_connections WHERE owner_id=?',(owner,),pg).fetchone()
        ws.query(db,'DELETE FROM gmail_connections WHERE owner_id=?',(owner,),pg);ws.query(db,'DELETE FROM gmail_states WHERE owner_id=?',(owner,),pg)
    revoked=not row
    if row:
        try:
            value=decrypt(owner,row[0]);body=urllib.parse.urlencode({'token':value['refresh_token']}).encode()
            with urllib.request.urlopen(urllib.request.Request('https://oauth2.googleapis.com/revoke',data=body,headers={'Content-Type':'application/x-www-form-urlencoded'}),timeout=20):revoked=True
        except Exception:pass
    return {'disconnected':True,'google_revoked':revoked,'note':'Imported drafts remain private. If remote revocation failed, remove access in your Google Account connections.'}
def delete_draft(data,owner,connect,pg):
    with connect() as db:
        row=ws.query(db,"SELECT d.id FROM documents d JOIN gmail_imports g ON g.document_id=d.id AND g.owner_id=d.owner_id WHERE d.id=? AND d.owner_id=? AND d.invoice_id=''",(data.get('document_id',''),owner),pg).fetchone()
        if not row:raise ws.APIError(409,'Only your unconfirmed Gmail drafts can be deleted here. Confirmed invoice records are retained separately.')
        ws.query(db,'DELETE FROM gmail_imports WHERE document_id=? AND owner_id=?',(row[0],owner),pg);ws.query(db,'DELETE FROM documents WHERE id=? AND owner_id=?',(row[0],owner),pg)
    return {'deleted':True}
def is_gmail_invoice(db,pg,owner,invoice_id):return bool(ws.query(db,"SELECT id FROM invoices WHERE id=? AND owner_id=? AND origin='gmail'",(invoice_id,owner),pg).fetchone())
