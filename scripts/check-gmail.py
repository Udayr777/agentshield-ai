"""No mailbox/model calls. Validates HTTP auth, private config, OAuth URL and callback boundary."""
import argparse,http.cookiejar,json,secrets,urllib.parse,urllib.request,urllib.error,uuid
p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8083');a=p.parse_args();checks=[]
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args):return None
client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),NoRedirect())
def req(path,data=None):
    request=urllib.request.Request(a.url+'/api'+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
    try:
        with client.open(request,timeout=40) as r:return r.status,json.load(r),r.headers
    except urllib.error.HTTPError as e:
        if e.code==303:return e.code,{},e.headers
        return e.code,json.load(e),e.headers
def check(condition,label):
    assert condition,label
    checks.append({'case':label,'passed':True})
check(req('/gmail/status')[0]==401,'Anonymous Gmail access blocked')
req('/auth/register',{'name':'Gmail HTTP validation','email':'gmail-http-'+uuid.uuid4().hex+'@example.test','password':secrets.token_urlsafe(24)})
code,status,_=req('/gmail/status');check(code==200 and status['configured'] and not status['connected'],'Private configuration loaded without a connected mailbox')
check(not any(key in status for key in ('client_secret','access_token','refresh_token','token_key')),'Status response contains no credentials')
check(req('/gmail/search',{'query':'invoice'})[0]==409,'Search blocked until Google authorization')
code,start,_=req('/gmail/connect',{});params=urllib.parse.parse_qs(urllib.parse.urlparse(start['authorization_url']).query)
check(code==200 and params['scope']==['https://www.googleapis.com/auth/gmail.readonly'] and params['code_challenge_method']==['S256'],'Authorization URL uses read-only scope and PKCE')
req('/auth/logout',{})
code,_,headers=req('/gmail/callback?'+urllib.parse.urlencode({'state':params['state'][0],'code':'not-a-real-code'}))
check(code==303 and headers.get('Location')=='/#gmail=error','Logged-out OAuth request rejected before any token exchange')
check('code=' not in headers.get('Location','') and headers.get('Referrer-Policy')=='no-referrer','Callback strips code and sets no-referrer')
print(json.dumps({'passed':len(checks),'mailbox_calls':0,'model_calls':0,'checks':checks},indent=2))
