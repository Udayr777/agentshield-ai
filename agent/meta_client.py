"""Bounded Meta JSON calls. Telemetry contains no prompts, answers or credentials."""
import json, os, time, threading, socket, ssl, urllib.request, urllib.error
from pathlib import Path

LOCK=threading.Lock()
class MetaError(Exception):
    def __init__(self,code):self.code=code;super().__init__(code)

def load_config(path=None):
    root=Path(__file__).resolve().parents[1]
    paths=[Path(path)] if path else [root/'.env.local',root/'.env',root/'.env.gmail']
    allowed={'ANALYZER_MODE','META_API_KEY','MODEL_API_KEY','META_MODEL','META_BASE_URL','META_MAX_COMPLETION_TOKENS','META_TIMEOUT_SECONDS','META_REASONING_EFFORT','META_SAM_MODEL','META_VISUAL_MODE','DATABASE_URL','DATABASE_URL_UNPOOLED','COOKIE_SECURE'}
    allowed.update({'LEDGER_SIGNING_KEY','LEDGER_KEY_FILE','RESEND_API_KEY','PASSWORD_RESET_FROM','APP_PUBLIC_URL'})
    allowed.update({'GOOGLE_CLIENT_ID','GOOGLE_CLIENT_SECRET','GOOGLE_REDIRECT_URI','GMAIL_TOKEN_KEY'})
    allowed.update({'POLICY_MODEL','WEBAUTHN_ORIGIN','EXPLANATION_ACCOUNT_HOURLY_LIMIT','EXPLANATION_GLOBAL_HOURLY_LIMIT','BASETEN_API_KEY','OPEN_WEIGHT_MODEL','INVESTIGATION_REPORT_MODEL'})
    for path in paths:
      if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            if not line.strip() or line.lstrip().startswith('#') or '=' not in line:continue
            key,value=line.split('=',1);key=key.strip()
            if key in allowed:os.environ.setdefault(key,value.strip().strip('"').strip("'"))

def record(meta):
    target=Path(os.getenv('META_USAGE_PATH',str(Path(__file__).with_name('model-usage.jsonl'))))
    try:
        with LOCK,target.open('a',encoding='utf-8') as f:f.write(json.dumps(meta)+'\n')
    except OSError:pass # Usage diagnostics cannot turn a blocked payment into an allow.

def complete_json(purpose,instruction,evidence,schema,image=None,model_override=None,provider=None):
    key=os.getenv('BASETEN_API_KEY') if provider=='baseten' else os.getenv('META_API_KEY') or os.getenv('MODEL_API_KEY')
    if provider not in (None,'baseten'):raise MetaError('unsupported_provider')
    if not key:raise MetaError('missing_key')
    model=model_override or os.getenv('META_MODEL','muse-spark-1.3');start=time.perf_counter()
    cap=max(256,min(8192,int(os.getenv('META_MAX_COMPLETION_TOKENS','2048'))))
    timeout=max(5,min(90,int(os.getenv('META_TIMEOUT_SECONDS','45'))))
    body={'model':model,'messages':[{'role':'developer','content':instruction},{'role':'user','content':json.dumps(evidence)}],
          'response_format':{'type':'json_schema','json_schema':{'name':purpose,'schema':schema}},
          'max_completion_tokens':cap,'reasoning_effort':os.getenv('META_REASONING_EFFORT','low')}
    if image:body['messages'][1]['content']=[{'type':'text','text':json.dumps(evidence)},{'type':'image_url','image_url':{'url':image}}]
    if provider=='baseten':
        body['messages'][0]['role']='system';body['max_tokens']=body.pop('max_completion_tokens')
    endpoint='https://inference.baseten.co/v1' if provider=='baseten' else os.getenv('META_BASE_URL','https://api.meta.ai/v1').rstrip('/')
    req=urllib.request.Request(endpoint+'/chat/completions',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    meta={'time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'purpose':purpose,'model':model,'provider':provider or 'meta','status':'error','max_completion_tokens':cap}
    try:
        # No automatic retry: avoid hidden duplicate consumption during initial validation.
        with urllib.request.urlopen(req,timeout=timeout) as response:
            raw=json.load(response)
            meta['provider_request_id']=response.headers.get('x-request-id','') if hasattr(response,'headers') else ''
        meta['reported_model']=raw.get('model');usage=raw.get('usage',{})
        meta['usage']={k:v for k,v in usage.items() if k in ('prompt_tokens','completion_tokens','total_tokens') and type(v) is int}
        choice=raw['choices'][0]
        if choice.get('finish_reason') not in (None,'stop'):raise MetaError('incomplete_response')
        result=json.loads(choice['message']['content'])
        if not isinstance(result,dict):raise MetaError('invalid_response')
        meta['status']='ok';meta['response_id']=raw.get('id','');return result,meta
    except urllib.error.HTTPError as error:
        code={400:'invalid_request',401:'authentication_failed',402:'billing_unavailable',403:'permission_denied',404:'model_or_endpoint_missing',429:'rate_limited'}.get(error.code,'provider_unavailable')
        meta['error_code']=code;raise MetaError(code) from None
    except MetaError as error:meta['error_code']=error.code;raise
    except (TimeoutError,socket.timeout):
        meta['error_code']='provider_timeout';raise MetaError('provider_timeout') from None
    except urllib.error.URLError as error:
        reason=error.reason
        code='provider_timeout' if isinstance(reason,(TimeoutError,socket.timeout)) else 'tls_connection_failed' if isinstance(reason,ssl.SSLError) else 'provider_connection_failed'
        meta['error_code']=code;raise MetaError(code) from None
    except (json.JSONDecodeError,UnicodeDecodeError,KeyError,IndexError,TypeError,AttributeError):
        meta['error_code']='invalid_provider_response';raise MetaError('invalid_provider_response') from None
    except Exception:meta['error_code']='unexpected_client_error';raise MetaError('unexpected_client_error') from None
    finally:
        meta['latency_ms']=round((time.perf_counter()-start)*1000,2);record(meta)
