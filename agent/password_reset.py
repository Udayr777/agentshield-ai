"""Email recovery. Raw reset tokens exist only in memory and the recipient email."""
import hashlib,json,os,re,secrets,time,threading,urllib.request
from urllib.parse import urlparse
import workspace as ws
LOCK=threading.Lock()
GENERIC={'message':'If an eligible account exists, a reset link will be sent. Check your inbox and spam folder. Requests are limited to prevent email abuse.'}
def migrate(db):
    db.execute('CREATE TABLE IF NOT EXISTS password_resets (token_hash TEXT PRIMARY KEY, owner_id TEXT NOT NULL, expires_at BIGINT NOT NULL, used INTEGER NOT NULL DEFAULT 0)')
    db.execute('CREATE TABLE IF NOT EXISTS reset_requests (id TEXT PRIMARY KEY, email_hash TEXT NOT NULL, created_at BIGINT NOT NULL)')
def config():
    origin=(os.getenv('APP_PUBLIC_URL') or os.getenv('RENDER_EXTERNAL_URL') or '').rstrip('/')
    p=urlparse(origin)
    valid=p.scheme=='https' or (p.scheme=='http' and p.hostname in ('localhost','127.0.0.1'))
    if not valid or not p.hostname or p.username or p.path or p.query or p.fragment:return None
    sender=os.getenv('PASSWORD_RESET_FROM','')
    if not os.getenv('RESEND_API_KEY') or not sender or '\r' in sender or '\n' in sender:return None
    return origin,sender
def status():return {'configured':config() is not None}
def deliver(email,token,settings):
    origin,sender=settings
    link=origin+'/#reset-password?token='+token
    from recovery_email import content
    text,html=content(link)
    body={'from':sender,'to':[email],'subject':'Reset your AgentShield password','text':text,'html':html}
    req=urllib.request.Request('https://api.resend.com/emails',json.dumps(body).encode(),{'Authorization':'Bearer '+os.environ['RESEND_API_KEY'],'Content-Type':'application/json','User-Agent':'AgentShield-Recovery/1.0'})
    with urllib.request.urlopen(req,timeout=15) as response:
        if response.status not in (200,201,202):raise ValueError('Email rejected')
def request(data,connect,pg):
    email=data.get('email','')
    if not isinstance(email,str) or len(email)>254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):raise ws.APIError(400,'Enter a valid account email.')
    email=email.strip().lower();settings=config()
    if not settings:raise ws.APIError(503,'Email recovery is not configured yet. The app owner must configure a verified sender and email-provider credentials.')
    digest=hashlib.sha256(email.encode()).hexdigest();now=int(time.time());token=None
    with LOCK,connect() as db:
        if pg:db.execute('SELECT pg_advisory_xact_lock(4815162348)')
        db.execute('DELETE FROM reset_requests WHERE created_at<'+str(now-86400))
        db.execute('DELETE FROM password_resets WHERE expires_at<'+str(now-86400))
        row=ws.query(db,'SELECT id,created_at FROM users WHERE email=?',(email,),pg).fetchone()
        # Requests made before registration must not suppress the new account's first recovery.
        cutoff=max(now-900,row[1]-1) if row else now-900
        if ws.query(db,'SELECT COUNT(*) FROM reset_requests WHERE created_at>?',(now-3600,),pg).fetchone()[0]>=20 or ws.query(db,'SELECT id FROM reset_requests WHERE email_hash=? AND created_at>?',(digest,cutoff),pg).fetchone():return dict(GENERIC)
        ws.query(db,'INSERT INTO reset_requests(id,email_hash,created_at) VALUES (?,?,?)',(secrets.token_hex(16),digest,now),pg)
        if row:
            token=secrets.token_urlsafe(32);token_hash=hashlib.sha256(token.encode()).hexdigest()
            ws.query(db,'UPDATE password_resets SET used=1 WHERE owner_id=?',(row[0],),pg)
            ws.query(db,'INSERT INTO password_resets(token_hash,owner_id,expires_at) VALUES (?,?,?)',(token_hash,row[0],now+900),pg)
    if token:
        try:deliver(email,token,settings)
        except Exception:
            # Do not reveal account existence, provider errors, reset URL or raw token.
            with connect() as db:ws.query(db,'UPDATE password_resets SET used=1 WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),),pg)
    return dict(GENERIC)
def reset(data,connect,pg):
    token=data.get('token','');password=data.get('password','')
    if not isinstance(token,str) or not re.fullmatch(r'[A-Za-z0-9_-]{40,100}',token):raise ws.APIError(400,'Reset link is invalid or expired. Request another link.')
    if not isinstance(password,str) or not 12<=len(password)<=128:raise ws.APIError(400,'Use a new password of 12–128 characters.')
    salt=secrets.token_hex(16);hashed=ws.password_hash(password,salt)
    with LOCK,connect() as db:
        if pg:db.execute('SELECT pg_advisory_xact_lock(4815162348)')
        row=ws.query(db,'UPDATE password_resets SET used=1 WHERE token_hash=? AND used=0 AND expires_at>? RETURNING owner_id',(hashlib.sha256(token.encode()).hexdigest(),int(time.time())),pg).fetchone()
        if not row:raise ws.APIError(400,'Reset link is invalid, expired or already used. Request another link.')
        owner=row[0]
        ws.query(db,'UPDATE users SET salt=?,password_hash=? WHERE id=?',(salt,hashed,owner),pg)
        ws.query(db,'DELETE FROM sessions WHERE user_id=?',(owner,),pg)
        ws.query(db,'DELETE FROM extension_tokens WHERE owner_id=?',(owner,),pg)
        ws.query(db,'UPDATE approvals SET used=1 WHERE owner_id=?',(owner,),pg)
        ws.query(db,'UPDATE passkey_challenges SET used=1 WHERE owner_id=?',(owner,),pg)
        ws.query(db,'UPDATE password_resets SET used=1 WHERE owner_id=?',(owner,),pg)
    return {'message':'Password updated. Sign in with your new password. All previous sign-in sessions were revoked.'}
