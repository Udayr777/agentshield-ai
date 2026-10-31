"""Opt-in live acceptance: three council calls plus one risk call, synthetic invoice only."""
import argparse,http.cookiejar,json,secrets,urllib.request,urllib.error,uuid
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8083');p.add_argument('--live',action='store_true');a=p.parse_args()
if not a.live:raise SystemExit('Pass --live to authorize up to four billable model calls. Use only synthetic data.')
c=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()));checks=[]
def request(path,body=None):
    req=urllib.request.Request(a.url+'/api'+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'})
    with c.open(req,timeout=140) as r:return json.load(r)
def check(ok,label):
    checks.append({'case':label,'passed':bool(ok)})
    if not ok:raise AssertionError(label)
try:
    request('/auth/register',{'name':'Council live validation','email':'council-live-'+uuid.uuid4().hex+'@example.test','password':secrets.token_urlsafe(24)})
    me=request('/auth/me');check(me['mode']=='meta','Live Meta mode confirmed')
    cases=request('/judge-pack',{})['cases'];invoice=next(c['invoice_id'] for c in cases if c['case']=='clean')
    initial=request('/council?invoice_id='+invoice);check(not initial['gate']['required'],'Council opt-in is explicit')
    outcome=request('/council/review',{'invoice_id':invoice});report=outcome['signed_report']['report']
    check(len(report['reviews'])==3,'Three real assessments returned')
    check(all(r['status']=='complete' and r.get('response_id') for r in report['reviews']),'Live model response provenance recorded')
    check(next(r for r in report['reviews'] if r['role']=='forensics')['visual_input'],'Forensic reviewer received synthetic invoice preview')
    check(outcome['gate']['signature_verified'],'Signed report matches exact invoice evidence')
    check(outcome['gate']['satisfied'],'Clean synthetic invoice achieved unanimous low content risk')
    receipt=request('/invoices/review',{'invoice_id':invoice})
    check(receipt['decision']=='allow' and receipt['analysis']['council']['satisfied'],'Council gate integrated with gateway and committed receipt')
    visual=next(c for c in receipt['checks'] if c['id']=='visual')
    check(visual['status']=='pass' and bool(visual.get('evidence')),'Visual comparison evidence carried into receipt')
    ledger=request('/ledger');check(ledger['valid'],'Council-enriched audit chain verifies')
    saved=request('/council?invoice_id='+invoice);check(saved['signed_report']['report']['id']==report['id'],'Signed report persists across fresh database requests')
    summary={'synthetic_only':True,'model_call_budget':4,'checks':checks,'votes':[{'role':r['role'],'risk':r['risk'],'model':r.get('model'),'usage':r.get('usage'),'latency_ms':r['latency_ms']} for r in report['reviews']]}
    (Path(__file__).resolve().parents[1]/'council-integration.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))
finally:
    try:request('/auth/logout',{})
    except Exception:pass
