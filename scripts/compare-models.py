"""Operator-only paired synthetic evaluation. No invoices/approvals/bank/database writes."""
import argparse,csv,hashlib,inspect,json,math,os,statistics,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'agent'))
import app

def summarize(rows):
    result={}
    for model in dict.fromkeys(r['model_requested'] for r in rows):
        group=[r for r in rows if r['model_requested']==model];latencies=sorted(r['latency_ms'] for r in group)
        result[model]={'cases':len(group),'correct':sum(r['risk']==r['expected'] for r in group),'benign_cases':sum(r['expected']=='low' for r in group),'attack_cases':sum(r['expected']=='high' for r in group),'benign_flagged_high':sum(r['expected']=='low' and r['risk']=='high' for r in group),'attacks_classified_low':sum(r['expected']=='high' and r['risk']=='low' for r in group),'unknown_or_errors':sum(r['risk']=='unknown' for r in group),'p50_ms':round(statistics.median(latencies),2),'p95_nearest_rank_ms':latencies[max(0,math.ceil(.95*len(latencies))-1)],'reported_tokens':sum(r['usage'].get('total_tokens',0) for r in group),'calls_without_token_usage':sum('total_tokens' not in r['usage'] for r in group)}
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--live',action='store_true',help='Explicitly authorize paid API calls');parser.add_argument('--limit',type=int,default=12);parser.add_argument('--models',nargs=2,default=['muse-spark-1.3','muse-wonder-1.0']);parser.add_argument('--output',default='comparison-results.json');args=parser.parse_args()
    if not 2<=args.limit<=12 or args.limit%2:parser.error('--limit must be even and between 2 and 12 (balanced benign/attack pairs)')
    if args.models[0]==args.models[1]:parser.error('Choose two distinct models')
    path=ROOT/'samples'/'model-comparison.json';cases=json.loads(path.read_text())[:args.limit]
    metadata={'models':args.models,'cases':len(cases),'planned_calls':2*len(cases),'dataset_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'analyzer_sha256':hashlib.sha256(inspect.getsource(app.analyze).encode()).hexdigest(),'scope':'Fresh synthetic author-labeled cases, not external independent validation. Text content classification only, not vision/SAM, full gateway, payment approval, or safety probability.','method':'Same analyzer prompt, amount, recipient and model settings. Model order alternates per case. One call per pair member; no retries. Errors remain unknown and do not count as correct.','settings':{'max_completion_tokens':os.getenv('META_MAX_COMPLETION_TOKENS','2048'),'reasoning_effort':os.getenv('META_REASONING_EFFORT','low'),'timeout_seconds':os.getenv('META_TIMEOUT_SECONDS','45')}}
    if not args.live:print(json.dumps({'status':'plan_only',**metadata},indent=2));return 0
    if not (os.getenv('META_API_KEY') or os.getenv('MODEL_API_KEY')):parser.error('Configure the private Meta key before --live; never pass it as a CLI argument')
    # Refuse silent heuristic benchmarking: force only this process to use actual model requests.
    os.environ['ANALYZER_MODE']='meta';rows=[]
    for i,case in enumerate(cases):
        order=args.models if i%2==0 else args.models[::-1]
        for model in order:
            start=time.perf_counter();answer=app.analyze({'invoice':case['invoice'],'recipient':'vendor_acme','amount_cents':10000},model_override=model)
            rows.append({'case_id':case['id'],'expected':case['label'],'model_requested':model,'model_returned':answer.get('model'),'risk':answer['risk'],'mode':answer['mode'],'reason':answer['reason'],'latency_ms':round((time.perf_counter()-start)*1000,2),'usage':answer.get('usage',{})})
            print(f"{len(rows)}/{metadata['planned_calls']} {model} {case['id']}: {answer['risk']} ({answer['mode']})",flush=True)
            # Persist partial results so an interrupted run still exposes failed/missing coverage.
            report={**metadata,'completed_calls':len(rows),'complete':len(rows)==metadata['planned_calls'],'summary':summarize(rows),'rows':rows}
            target=Path(args.output);target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    csv_path=Path(args.output).with_suffix('.csv')
    with csv_path.open('w',newline='',encoding='utf-8') as handle:
        writer=csv.DictWriter(handle,fieldnames=['case_id','expected','model_requested','model_returned','risk','mode','latency_ms']);writer.writeheader();writer.writerows({k:r[k] for k in writer.fieldnames} for r in rows)
    print(json.dumps(report['summary'],indent=2))
    return 0 if all(s['unknown_or_errors']==0 for s in report['summary'].values()) else 2
if __name__=='__main__':raise SystemExit(main())
