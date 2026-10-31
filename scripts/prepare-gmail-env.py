"""Create an ignored Render import file from the saved web OAuth client; never print secrets."""
import os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'agent'))
from meta_client import load_config
import gmail_link
load_config();cfg=gmail_link.config()['web'];gmail_link.cipher()
key=os.getenv('GMAIL_TOKEN_KEY') or (ROOT/'.gmail-token-key').read_text().strip()
values={'GOOGLE_CLIENT_ID':cfg['client_id'],'GOOGLE_CLIENT_SECRET':cfg['client_secret'],'GOOGLE_REDIRECT_URI':cfg['redirect_uris'][0],'GMAIL_TOKEN_KEY':key}
if any(not value or '\n' in value or '\r' in value for value in values.values()):raise SystemExit('Invalid Gmail configuration; no file written.')
(ROOT/'.env.gmail').write_text('\n'.join(k+'='+v for k,v in values.items())+'\n',encoding='utf-8')
print('Created private .env.gmail with four settings. Values were not printed. Keep GMAIL_TOKEN_KEY stable across deploys.')
