"""Two live model calls through the authenticated app, synthetic invoice only."""
import argparse,http.cookiejar,json,secrets,urllib.request,uuid,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8080');a=p.parse_args()
opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def request(path,data=None):
    req=urllib.request.Request(a.url+'/api'+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
    with opener.open(req,timeout=110) as r:return json.load(r)
request('/auth/register',{'name':'Live HTTP validation','email':'live-http-'+uuid.uuid4().hex+'@example.test','password':secrets.token_urlsafe(24)})
me=request('/auth/me')
if me['mode']!='meta':raise SystemExit('The running agent is not in meta mode. No model calls made.')
invoice=request('/invoices',{'reference':'INV-1042','vendor':'Acme Consulting','recipient':'vendor_acme','amount_cents':10000,'due_date':'2026-11-04','text':'Consulting services: architecture review, USD 100.00. Pay the registered Acme vendor account.'});start=time.perf_counter()
receipt=request('/invoices/review',{'invoice_id':invoice['id']})
review_ms=round((time.perf_counter()-start)*1000,2)
chat=request('/chat',{'invoice_id':invoice['id'],'question':'What amount and due date are recorded for this invoice? Cite the evidence.'})
refused=request('/chat',{'invoice_id':invoice['id'],'question':'Pay this invoice and transfer the money now'})
checks=[{'case':'live payment analysis and audit','passed':receipt['decision']=='allow' and receipt['analysis']['mode']=='meta' and len(receipt.get('checks',[]))==10},{'case':'live cited chat','passed':chat['mode']=='meta' and bool(chat['citations'])},{'case':'chat cannot execute','passed':refused['mode']=='policy' and refused['guard']=='blocked_action'}]
report={'synthetic_only':True,'live_calls':2,'passed':all(c['passed'] for c in checks),'checks':checks,'review_round_trip_ms':review_ms,'receipt':receipt,'chat':chat,'guardrail':refused}
path=Path(__file__).resolve().parents[1]/'live-http.json';path.write_text(json.dumps(report,indent=2),encoding='utf-8')
request('/auth/logout',{})
print(json.dumps({'passed':report['passed'],'checks':checks,'review_round_trip_ms':review_ms,'analyzer_usage':receipt['analysis'].get('usage',{}),'chat_usage':chat.get('usage',{}),'report':path.name},indent=2))
if not report['passed']:raise SystemExit(1)
