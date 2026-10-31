"""One real configured analyzer call, bound to a synthetic owned invoice."""
import http.cookiejar,json,secrets,urllib.request,uuid,argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8080');a=p.parse_args()
client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def req(path,data=None):
    request=urllib.request.Request(a.url+'/api'+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
    with client.open(request,timeout=110) as response:return json.load(response)
req('/auth/register',{'name':'Invoice chaos validation','email':uuid.uuid4().hex+'@example.test','password':secrets.token_urlsafe(24)})
invoice=req('/invoices')[0]
receipt=req('/invoices/chaos',{'invoice_id':invoice['id'],'scenario':'recipient_swap','payload':''})
after=next(i for i in req('/invoices') if i['id']==invoice['id'])
checks={'owned_invoice_target':receipt['payment']['invoice_id']==invoice['id'],'original_mandate_preserved':receipt['replay']['mandate']['recipient']=='vendor_acme','copied_proposal_mutated':receipt['payment']['recipient']=='attacker_wallet','intercepted':receipt['decision']=='deny','source_unchanged':after==invoice,'ten_controls':len(receipt['checks'])==10}
report={'passed':all(checks.values()),'checks':checks,'receipt':receipt}
(Path(__file__).resolve().parents[1]/'invoice-chaos-integration.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
req('/auth/logout',{})
print(json.dumps({'passed':report['passed'],'checks':checks,'mode':receipt['analysis']['mode']},indent=2))
if not report['passed']:raise SystemExit(1)
