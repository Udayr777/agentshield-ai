"""Mailbox ownership evidence, not identity certification or payment authority."""
import hashlib,html,json,os,re,secrets,threading,time,urllib.request
import workspace as ws,password_reset
LOCK=threading.Lock()
def migrate(db):
    db.execute('CREATE TABLE IF NOT EXISTS verified_emails (owner_id TEXT PRIMARY KEY, email TEXT NOT NULL, verified_at BIGINT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS email_verifications (token_hash TEXT PRIMARY KEY, owner_id TEXT NOT NULL, email TEXT NOT NULL, expires_at BIGINT NOT NULL, used INTEGER NOT NULL DEFAULT 0)')
    db.execute('CREATE TABLE IF NOT EXISTS verification_requests (id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, created_at BIGINT NOT NULL)')
def state(owner,connect,pg):
    with connect() as db:
        row=ws.query(db,'SELECT email FROM users WHERE id=?',(owner,),pg).fetchone()
        if not row:raise ws.APIError(404,'Account not found.')
        verified=ws.query(db,'SELECT verified_at FROM verified_emails WHERE owner_id=? AND email=?',(owner,row[0]),pg).fetchone()
        now=int(time.time())
        own=ws.query(db,'SELECT created_at FROM verification_requests WHERE owner_id=? AND created_at>? ORDER BY created_at',(owner,now-3600),pg).fetchall()
        all_requests=ws.query(db,'SELECT created_at FROM verification_requests WHERE created_at>? ORDER BY created_at',(now-3600,),pg).fetchall()
        retry=max([0]+([own[-1][0]+60-now] if own else [])+([own[-3][0]+3600-now] if len(own)>=3 else [])+([all_requests[-20][0]+3600-now] if len(all_requests)>=20 else []))
        pending=ws.query(db,'SELECT token_hash FROM email_verifications WHERE owner_id=? AND used=0 AND expires_at>?',(owner,now),pg).fetchone()
    return {'test_sender':password_reset.test_sender(),'retry_after_seconds':max(0,retry),'pending_link':bool(pending),'verified':bool(verified),'verified_at':verified[0] if verified else None,'configured':password_reset.config() is not None}
def deliver(email,token,settings):
    origin,sender=settings;link=origin+'/#verify-email?token='+token;escaped=html.escape(link,quote=True)
    text='Verify your AgentShield email address. Open this single-use link within 30 minutes: '+link+'\nThis confirms mailbox ownership only. It does not authorize a payment. If you did not request it, ignore this message. Never share the link.'
    body={'from':sender,'to':[email],'subject':'Verify your AgentShield email','text':text,'html':'<div style="background:#eef5ff;padding:28px;font-family:Arial;color:#16324c"><h2>AgentShield AI</h2><h1>Make your inbox part of your shield.</h1><p>Confirm that you own this account email address.</p><p><a style="background:#1557b0;color:white;padding:14px;display:inline-block" href="'+escaped+'">Verify email address</a></p><p>Expires in 30 minutes. Works once. This does not authorize a payment.</p><p>If you did not request this, ignore it. Never share verification links.</p></div>'}
    request=urllib.request.Request('https://api.resend.com/emails',json.dumps(body).encode(),{'Authorization':'Bearer '+os.environ['RESEND_API_KEY'],'Content-Type':'application/json','User-Agent':'AgentShield-Verification/1.0'})
    with urllib.request.urlopen(request,timeout=15) as response:
        if response.status not in (200,201,202):raise ValueError('Delivery rejected')
def request(owner,connect,pg):
    settings=password_reset.config()
    if not settings:raise ws.APIError(503,'Email verification is not configured. Ask the operator to configure Resend and a verified sender.')
    now=int(time.time())
    with LOCK,connect() as db:
        if pg:db.execute('SELECT pg_advisory_xact_lock(4815162351)')
        email=ws.query(db,'SELECT email FROM users WHERE id=?',(owner,),pg).fetchone()
        if not email:raise ws.APIError(404,'Account not found.')
        if ws.query(db,'SELECT owner_id FROM verified_emails WHERE owner_id=? AND email=?',(owner,email[0]),pg).fetchone():return {'message':'Your email is already verified.'}
        db.execute('DELETE FROM verification_requests WHERE created_at<'+str(now-86400))
        db.execute('DELETE FROM email_verifications WHERE expires_at<'+str(now-86400))
        recent=ws.query(db,'SELECT COUNT(*) FROM verification_requests WHERE owner_id=? AND created_at>?',(owner,now-3600),pg).fetchone()[0]
        total=ws.query(db,'SELECT COUNT(*) FROM verification_requests WHERE created_at>?',(now-3600,),pg).fetchone()[0]
        cooldown=ws.query(db,'SELECT id FROM verification_requests WHERE owner_id=? AND created_at>?',(owner,now-60),pg).fetchone()
        if cooldown or recent>=3 or total>=20:raise ws.APIError(429,'Verification limit: wait one minute between sends, three per account/hour and twenty per deployment/hour. Failures count.')
        token=secrets.token_urlsafe(32);digest=hashlib.sha256(token.encode()).hexdigest()
        ws.query(db,'INSERT INTO verification_requests(id,owner_id,created_at) VALUES (?,?,?)',(secrets.token_hex(16),owner,now),pg)
        ws.query(db,'UPDATE email_verifications SET used=1 WHERE owner_id=?',(owner,),pg)
        ws.query(db,'INSERT INTO email_verifications(token_hash,owner_id,email,expires_at) VALUES (?,?,?,?)',(digest,owner,email[0],now+1800),pg)
    try:deliver(email[0],token,settings)
    except Exception:
        with connect() as db:ws.query(db,'UPDATE email_verifications SET used=1 WHERE token_hash=?',(digest,),pg)
        raise ws.APIError(503,'Verification email could not be sent. Check the sender configuration and provider delivery logs; retry after the cooldown.') from None
    return {'message':'Verification email submitted to the provider. Check your inbox and spam. The link expires in 30 minutes.'}
def confirm(data,connect,pg):
    token=data.get('token','')
    if not isinstance(token,str) or not re.fullmatch(r'[A-Za-z0-9_-]{40,100}',token):raise ws.APIError(400,'Verification link is invalid or expired. Request a new one from your profile.')
    with LOCK,connect() as db:
        if pg:db.execute('SELECT pg_advisory_xact_lock(4815162351)')
        row=ws.query(db,'UPDATE email_verifications SET used=1 WHERE token_hash=? AND used=0 AND expires_at>? RETURNING owner_id,email',(hashlib.sha256(token.encode()).hexdigest(),int(time.time())),pg).fetchone()
        if not row:raise ws.APIError(400,'Verification link is invalid, expired or already used.')
        current=ws.query(db,'SELECT email FROM users WHERE id=?',(row[0],),pg).fetchone()
        if not current or current[0]!=row[1]:raise ws.APIError(400,'Account email changed; request a new verification link.')
        ws.query(db,'INSERT INTO verified_emails(owner_id,email,verified_at) VALUES (?,?,?) ON CONFLICT(owner_id) DO UPDATE SET email=excluded.email,verified_at=excluded.verified_at',(row[0],row[1],int(time.time())),pg)
        ws.query(db,'UPDATE email_verifications SET used=1 WHERE owner_id=?',(row[0],),pg)
    return {'message':'Email verified. Return to your workspace or sign in. No password, session or payment authority was changed.'}
def signup(owner,connect,pg):
    if password_reset.config():
        def send():
            try:request(owner,connect,pg)
            except Exception:pass # Account creation remains valid; profile provides explicit resend.
        threading.Thread(target=send,daemon=True).start()
