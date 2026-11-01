"""Explicit two-asset Muse Image generation. Existing outputs are never regenerated."""
import base64,json,os,sys,time,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'agent'))
from meta_client import load_config
load_config()
COMMON='Original premium 3D editorial product illustration for AgentShield AI. Friendly small pearlescent ceramic security robot, cobalt glass face with two luminous mint eyes, tiny warm orange scarf, articulated arms and legs, rounded proportions, approachable personality. Violet, teal and warm gold accents on pale ivory. Soft studio lighting, refined materials, crisp silhouette, sophisticated restrained composition. No text, letters, numbers, logos, watermarks, charts, screenshots, certification badges or real financial details. '
SCENES={
 'muse-landing-guardian':COMMON+'Square composition. Robot stands beside a large translucent glass shield protecting a floating abstract invoice sheet with simple blank embossed lines. A single orange ribbon representing untrusted input stops at the outside of the shield and resolves into a few small glowing evidence tiles. Clear visual hierarchy, generous breathing space, dimensional grounded shadows, beautiful luminous glass and subtle depth. Robot and invoice clearly visible, no overly busy particles. Conceptual brand artwork, not a real security result.',
 'muse-workspace-welcome':COMMON+'Square composition. The robot sits on a low rounded lavender platform holding out a blank ivory invoice sheet inviting the viewer to begin. A small translucent teal shield leans beside it and three subtle floating paper tiles complete the scene. Cozy welcoming pose, character centered with full body visible, uncluttered ivory background, generous margins, calm bright lighting. Conceptual empty workspace illustration, no implied analysis or approval.'}
public=ROOT/'dashboard/public'
for name,prompt in SCENES.items():
 target=public/(name+'.png')
 if target.exists():print(name+': existing asset retained',flush=True);continue
 key=os.getenv('META_API_KEY') or os.getenv('MODEL_API_KEY')
 if not key:raise SystemExit('Missing local Meta credential; no generation performed.')
 body={'model':'muse-image-1.0','prompt':prompt,'n':1,'size':'1024x1024','response_format':'b64_json','tool_enablement':{'enable_image_search':False,'enable_web_search':False,'enable_shell':False}}
 req=urllib.request.Request(os.getenv('META_BASE_URL','https://api.meta.ai/v1').rstrip('/')+'/images/generations',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
 try:
  print(name+': requesting Muse Image',flush=True)
  with urllib.request.urlopen(req,timeout=180) as response:data=json.load(response)
  raw=base64.b64decode(data['data'][0]['b64_json'],validate=True)
  if not raw.startswith(b'\x89PNG\r\n\x1a\n'):
   import io
   from PIL import Image
   converted=io.BytesIO();Image.open(io.BytesIO(raw)).save(converted,format='PNG');raw=converted.getvalue()
  target.write_bytes(raw)
  (public/(name+'-provenance.json')).write_text(json.dumps({'provider':'Meta Model API','model':body['model'],'prompt':prompt,'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'response_id':data.get('id',''),'scope':'Conceptual brand illustration, not document evidence or a security assessment.'},indent=2)+'\n',encoding='utf-8')
  print(name+': saved '+str(len(raw))+' bytes',flush=True)
 except urllib.error.HTTPError as error:raise SystemExit('Muse Image HTTP '+str(error.code)+'; no alternative provider used.') from None
 except Exception as error:
  detail=type(error).__name__
  if isinstance(error,urllib.error.URLError):detail+=' / '+type(error.reason).__name__
  raise SystemExit('Muse Image failed: '+detail+'; no alternative provider used.') from None
