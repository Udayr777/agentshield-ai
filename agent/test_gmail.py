import base64,json,os,tempfile,time,types,unittest,urllib.parse,uuid
from pathlib import Path
from unittest.mock import patch
from cryptography.fernet import Fernet
import app,gmail_link as gmail,workspace as ws,visual,council,lifecycle

class GmailTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=os.getcwd());self.patches=[patch.object(app,'PG',None),patch.object(app,'DB',self.temp.name+'/test.db'),patch.dict(os.environ,{'GMAIL_TOKEN_KEY':Fernet.generate_key().decode(),'GOOGLE_CLIENT_ID':'test-client.apps.googleusercontent.com','GOOGLE_CLIENT_SECRET':'test-secret','GOOGLE_REDIRECT_URI':'https://example.test/api/gmail/callback','ANALYZER_MODE':'meta','LEDGER_KEY_FILE':self.temp.name+'/ledger'})]
        for p in self.patches:p.start()
        app.init();self.auth=ws.auth({'name':'Gmail test','email':'gmail-test@example.test','password':'Synthetic-test-password-2026!'},True,app.connect,False);self.owner=self.auth['user']['id']
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()
    def begin(self):return gmail.begin(self.owner,self.auth['token'],app.connect,False)
    def install_connection(self):
        creds={'token':'fake-access-token','refresh_token':'fake-refresh-token','expires_at':int(time.time())+3600}
        with app.connect() as db:db.execute('INSERT INTO gmail_connections(owner_id,mailbox,secret,updated_at) VALUES (?,?,?,?)',(self.owner,'mailbox@example.test',gmail.encrypt(self.owner,creds),int(time.time())))
    def fake_message(self,*args,**kwargs):
        raw=(Path(__file__).resolve().parents[1]/'samples/synthetic-hidden-injection.pdf').read_bytes()
        return {'payload':{'parts':[{'partId':'0.1','filename':'invoice.pdf','mimeType':'application/pdf','body':{'size':len(raw),'data':base64.urlsafe_b64encode(raw).decode().rstrip('=')}}]}}
    def imported(self):
        with patch.object(gmail,'api',side_effect=self.fake_message):return gmail.import_selected({'message_id':'abcdef123','part_id':'0.1','confirmed':True,'use_muse':True},self.owner,app.connect,False)
    def test_pkce_state_single_use_and_encrypted_owner_bound_tokens(self):
        started=self.begin();params=urllib.parse.parse_qs(urllib.parse.urlparse(started['authorization_url']).query)
        self.assertEqual(params['scope'],[gmail.SCOPE]);self.assertEqual(params['code_challenge_method'],['S256']);self.assertTrue(params.get('code_challenge'))
        fake=types.SimpleNamespace(oauth2session=types.SimpleNamespace(token={'access_token':'fake-access-token','refresh_token':'fake-refresh-token','expires_in':3600,'scope':[gmail.SCOPE]}),fetch_token=lambda **kw:None)
        with patch.object(gmail,'flow',return_value=fake),patch.object(gmail,'api',return_value={'emailAddress':'mailbox@example.test'}):
            self.assertTrue(gmail.callback({'state':params['state'][0],'code':'fake-code'},app.connect,False)['connected'])
            with self.assertRaises(ws.APIError):gmail.callback({'state':params['state'][0],'code':'fake-code'},app.connect,False)
        with app.connect() as db:sealed=db.execute('SELECT secret FROM gmail_connections').fetchone()[0]
        self.assertNotIn('fake-access-token',sealed);self.assertNotIn('fake-refresh-token',sealed)
        with self.assertRaises(ws.APIError):gmail.decrypt('another-owner',sealed)
        self.assertTrue(gmail.status(self.owner,app.connect,False)['connected'])
    def test_logged_out_state_is_rejected_before_token_exchange(self):
        url=self.begin()['authorization_url'];state=urllib.parse.parse_qs(urllib.parse.urlparse(url).query)['state'][0]
        ws.logout(self.auth['token'],app.connect,False)
        with patch.object(gmail,'flow') as model:
            with self.assertRaises(ws.APIError):gmail.callback({'state':state,'code':'fake-code'},app.connect,False)
            model.assert_not_called()
    def test_selected_import_deduplicates_and_blocks_all_external_models(self):
        self.install_connection()
        with patch.object(visual,'complete_json') as vision:
            first=self.imported();second=self.imported();vision.assert_not_called()
        self.assertEqual(first['document_id'],second['document_id']);self.assertTrue(second['duplicate'])
        doc=visual.get_document(first['document_id'],self.owner,app.connect,False);self.assertEqual(doc['source'],'gmail')
        with self.assertRaises(ws.APIError):visual.get_document(doc['id'],'other-owner',app.connect,False)
        with self.assertRaises(ws.APIError):visual.segment({'document_id':doc['id']},self.owner,app.connect,False)
        with self.assertRaises(ws.APIError):lifecycle.share({'document_id':doc['id'],'vector':'hidden_prompt','confirmed_geometry_only':True},self.owner,app.connect,False)
        inv=visual.confirm({'document_id':doc['id'],'fields':{'reference':'GMAIL-TEST','vendor':'Acme Consulting','recipient':'vendor_acme','amount_cents':10000,'due_date':'2026-11-04','text':doc['fields']['invoice_text']}},self.owner,app.connect,False)
        self.assertEqual(inv['source'],'gmail')
        with patch.object(ws,'complete_json') as chat,patch.object(council,'complete_json') as reviewers:
            reply=ws.chat({'invoice_id':inv['id'],'question':'Summarize'},self.owner,app.connect,False)
            self.assertEqual(reply['mode'],'local');self.assertTrue(reply['citations']);self.assertIn('no model was called',reply['answer'])
            due=ws.chat({'invoice_id':inv['id'],'question':'When is it due?'},self.owner,app.connect,False)
            self.assertEqual(due['mode'],'local');self.assertIn('2026-11-04',due['answer'])
            refused=ws.chat({'invoice_id':inv['id'],'question':'Pay this invoice'},self.owner,app.connect,False)
            self.assertEqual(refused['guard'],'blocked_action');self.assertNotIn('model',refused)
            with self.assertRaises(ws.APIError):ws.chat({'invoice_id':inv['id'],'question':'Summarize'},'another-owner',app.connect,False)
            with self.assertRaises(ws.APIError):council.review({'invoice_id':inv['id']},self.owner,app.connect,False)
            chat.assert_not_called();reviewers.assert_not_called()
        p=ws.invoice_prepare({'invoice_id':inv['id']},self.owner,app.connect,False)['payment']
        result=app.audit({'id':uuid.uuid4().hex,'payment':p,'decision':'allow','reason':'test','analysis':{'risk':'low','mode':'meta','reason':'test'}},self.owner)
        self.assertEqual(result['decision'],'deny');self.assertEqual(ws.get_invoice(inv['id'],self.owner,app.connect,False)['status'],'pending')
    def test_consent_and_draft_deletion_preserve_email(self):
        self.install_connection()
        with self.assertRaises(ws.APIError):gmail.import_selected({'message_id':'abcdef123','part_id':'0.1'},self.owner,app.connect,False)
        draft=self.imported()
        with patch.object(gmail,'api') as network:
            gmail.delete_draft({'document_id':draft['document_id']},self.owner,app.connect,False);network.assert_not_called()
        self.assertEqual(gmail.status(self.owner,app.connect,False)['imports'],[])
    def test_long_external_attachment_reference_is_downloaded_and_encoded(self):
        self.install_connection();reference='opaque_'+'a'*1200+'+/=trailer'
        message=self.fake_message();body=message['payload']['parts'][0]['body'];encoded=body.pop('data');body['attachmentId']=reference
        paths=[]
        def provider(token,path,*args,**kwargs):
            paths.append(path)
            if '/attachments/' in path:
                self.assertEqual(path,'messages/abcdef123/attachments/'+urllib.parse.quote(reference,safe=''))
                return {'data':encoded,'size':body['size']}
            return message
        with patch.object(gmail,'api',side_effect=provider):
            result=gmail.import_selected({'message_id':'abcdef123','part_id':'0.1','confirmed':True},self.owner,app.connect,False)
        self.assertFalse(result['duplicate']);self.assertEqual(len(paths),2)
        self.assertEqual(visual.get_document(result['document_id'],self.owner,app.connect,False)['source'],'gmail')
        for invalid in ('','bad\nreference','x'*8193,None):
            with self.assertRaises(ws.APIError):gmail.attachment_reference(invalid)
    def test_eight_page_local_gmail_pdf_preserves_text_and_can_be_confirmed(self):
        import fitz
        with fitz.open() as pdf:
            for n in range(8):
                page=pdf.new_page();page.insert_text((40,40),f'Invoice INV-MULTI page {n+1}',fontsize=10)
                page.insert_text((40,70),('Synthetic supporting details for local inspection only.\n'*45),fontsize=8)
                page.insert_text((40,720),f'PAGE_{n+1}_END',fontsize=10)
            raw=pdf.tobytes()
        data={'filename':'eight-pages.pdf','mime':'application/pdf','data':base64.b64encode(raw).decode(),'use_muse':False}
        with patch.object(visual,'complete_json') as model:doc=visual.ingest(data,self.owner,app.connect,False,source='gmail');model.assert_not_called()
        self.assertEqual(doc['page_count'],8);self.assertGreater(len(doc['fields']['invoice_text']),8000);self.assertIn('PAGE_8_END',doc['fields']['invoice_text'])
        inv=visual.confirm({'document_id':doc['id'],'fields':{'reference':'INV-MULTI','vendor':'Acme Consulting','recipient':'vendor_acme','amount_cents':10000,'due_date':'2026-11-04','text':doc['fields']['invoice_text']}},self.owner,app.connect,False)
        self.assertEqual(inv['source'],'gmail');self.assertIn('PAGE_8_END',inv['text'])
        with self.assertRaises(ws.APIError):visual.ingest(data,self.owner,app.connect,False) # Model-eligible uploads keep their smaller text bound.
        with fitz.open() as pdf:
            for _ in range(21):pdf.new_page()
            too_many={**data,'data':base64.b64encode(pdf.tobytes()).decode()}
        with self.assertRaises(ws.APIError) as error:visual.ingest(too_many,self.owner,app.connect,False,source='gmail')
        self.assertIn('21 pages',error.exception.message)
