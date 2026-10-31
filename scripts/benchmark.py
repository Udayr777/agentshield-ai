"""Reproducible HTTP scenario sweep. No external model calls unless server is in meta mode."""
import argparse, json, time, urllib.request, statistics, platform, http.cookiejar, secrets, uuid
p=argparse.ArgumentParser();p.add_argument('--rounds',type=int,default=20);p.add_argument('--url',default='http://127.0.0.1:8080');p.add_argument('--output',default='benchmark-results.json');a=p.parse_args()
opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def request(path,data=None):
    req=urllib.request.Request(a.url+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
    with opener.open(req,timeout=20) as r:return json.load(r)
request('/api/auth/register',{'name':'Benchmark','email':'benchmark-'+uuid.uuid4().hex+'@example.test','password':secrets.token_urlsafe(24)})
scenarios=request('/api/catalog');latencies=[];rows=[]
for _ in range(a.rounds):
    for s in scenarios:
        start=time.perf_counter();r=request('/api/replay',{'scenario':s['id'],'amount_cents':10000});elapsed=(time.perf_counter()-start)*1000;latencies.append(elapsed)
        rows.append(dict(scenario=s['name'],expected=s['expected'],actual=r['decision'],mode=r['analysis']['mode'],latency_ms=elapsed,id=r['id']))
latencies.sort();report=dict(rounds=a.rounds,requests=len(rows),correct=sum(r['expected']==r['actual'] for r in rows),p50_ms=statistics.median(latencies),p95_ms=latencies[max(0,int(len(latencies)*.95)-1)],platform=platform.platform(),measurement='Sequential HTTP round trip including durable audit; no warmup',results=rows)
with open(a.output,'w') as f:json.dump(report,f,indent=2)
print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2))
if report['correct']!=len(rows):raise SystemExit('Unexpected decisions')
