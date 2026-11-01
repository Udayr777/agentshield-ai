"""Hosted/local acceptance: explicitly paid bounded investigation, synthetic fixtures only."""
import argparse,http.cookiejar,json,secrets,time,urllib.request,uuid
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--url',default='http://127.0.0.1:5174');p.add_argument('--live',action='store_true');p.add_argument('--require-partner',action='store_true');p.add_argument('--output',default='live-investigation.json');a=p.parse_args()
if not a.live:p.error('--live explicitly authorizes up to six model calls on synthetic data')
c=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def request(path,data=None):
    req=urllib.request.Request(a.url.rstrip('/')+'/api'+path,None if data is None else json.dumps(data).encode(),{'Content-Type':'application/json'})
    with c.open(req,timeout=60) as r:return json.load(r)
request('/auth/register',{'name':'Synthetic investigation verification','email':'investigate-'+uuid.uuid4().hex+'@example.test','password':secrets.token_urlsafe(24)})
invoice=next(case['invoice_id'] for case in request('/judge-pack',{})['cases'] if case['case']=='hidden')
settings=request('/investigations?invoice_id='+invoice)
if a.require_partner and not settings['configuration']['partner_configured']:raise SystemExit('Partner not configured; no model calls made. Add the private Baseten key and restart/redeploy.')
before=request('/events');run=request('/investigations/start',{'invoice_id':invoice,'confirmed_external_processing':True});deadline=time.monotonic()+340
while run['status']=='running' and time.monotonic()<deadline:
    time.sleep(3);run=request('/investigations/run?id='+run['id']);print('Investigation:',run['status'],'steps:',len(run['trace']),flush=True)
Path(a.output).write_text(json.dumps(run,indent=2)+'\n',encoding='utf-8')
assert run['status']=='complete',run.get('error_code','incomplete')
assert not a.require_partner or run['partner_response_recorded']
assert request('/events')==before,'Investigation must not issue payment receipts'
assert next(i for i in request('/invoices') if i['id']==invoice)['status']=='pending'
kit=request('/investigations/share?id='+run['id']);assert 'attacker_wallet' not in json.dumps(kit)
print(json.dumps({'result':'PASS','partner_response_recorded':run['partner_response_recorded'],'report_model':run['report_provenance']['model'],'actions':[t['action'] for t in run['trace']],'read_only_verified':True,'private_report_saved':a.output},indent=2))
