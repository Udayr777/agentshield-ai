"""One explicit Muse Image generation; no credentials in output or saved metadata."""
import base64,json,os,sys,time,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'agent'))
from meta_client import load_config
load_config();target=ROOT/'dashboard/public/guide-muse.png';target.parent.mkdir(parents=True,exist_ok=True)
if target.exists():raise SystemExit('Avatar already exists; no additional generation charged.')
prompt='Create one original friendly premium 3D security guardian mascot called Aegis, full body centered, a small rounded pearlescent ceramic robot with cobalt blue glass face and two luminous mint eyes, tiny orange neck scarf, articulated little legs and feet, one hand waving hello and other holding a translucent shield. Elegant product design, warm approachable personality, soft studio light, minimal pale ivory seamless background, crisp silhouette, generous empty margin around whole body. No writing, no letters, no logos, no existing characters. Square composition.'
body={'model':'muse-image-1.0','prompt':prompt,'n':1,'size':'1024x1024','response_format':'b64_json','tool_enablement':{'enable_image_search':False,'enable_web_search':False,'enable_shell':False}}
req=urllib.request.Request(os.getenv('META_BASE_URL','https://api.meta.ai/v1').rstrip('/')+'/images/generations',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+(os.getenv('META_API_KEY') or os.environ['MODEL_API_KEY']),'Content-Type':'application/json'})
try:
    with urllib.request.urlopen(req,timeout=180) as response:data=json.load(response)
    raw=base64.b64decode(data['data'][0]['b64_json'],validate=True);target.write_bytes(raw)
    (target.parent/'guide-provenance.json').write_text(json.dumps({'provider':'Meta Model API','model':body['model'],'prompt':prompt,'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'response_id':data.get('id','')},indent=2))
    print('Muse avatar generated and saved; bytes:',len(raw))
except urllib.error.HTTPError as e:raise SystemExit('Muse Image request failed: HTTP '+str(e.code))
