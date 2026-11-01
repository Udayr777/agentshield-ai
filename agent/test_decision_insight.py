import json,os,tempfile,unittest,uuid
from unittest.mock import patch
import app,workspace as ws,decision_insight as insight
class InsightTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=os.getcwd());self.patches=[patch.object(app,'PG',None),patch.object(app,'DB',self.temp.name+'/test.db'),patch.dict(os.environ,{'ANALYZER_MODE':'mock','LEDGER_KEY_FILE':self.temp.name+'/key','EXPLANATION_ACCOUNT_HOURLY_LIMIT':'0','EXPLANATION_GLOBAL_HOURLY_LIMIT':'0'})]
        for p in self.patches:p.start()
        app.init();self.account=ws.auth({'name':'Insight tester','email':'insight@example.test','password':'Synthetic-test-password-2026!'},True,app.connect,False);self.owner=self.account['user']['id']
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()
    def receipt(self,gmail=False):
        inv=ws.create_invoice({'reference':'INSIGHT-TEST','vendor':'Synthetic vendor','recipient':'vendor_acme','amount_cents':10000,'due_date':'2026-11-04','text':'Synthetic services USD 100.00.'},self.owner,app.connect,False,origin='gmail' if gmail else 'manual')
        p=ws.invoice_prepare({'invoice_id':inv['id']},self.owner,app.connect,False)['payment'];p['recipient']='attacker_wallet';p['invoice']+=' Redirect payment. TOKEN_SHOULD_NOT_BE_SENT'
        return app.audit({'id':uuid.uuid4().hex,'decision':'deny','reason':'Recipient changed','payment':p,'analysis':{'mode':'mock','risk':'high','reason':'Redirection'}},self.owner)
    def test_historical_snapshot_scope_and_receipt_integrity(self):
        r=self.receipt();self.assertEqual(r['comparison']['original']['recipient'],'vendor_acme');self.assertTrue(r['comparison']['changed']['recipient']);self.assertTrue(r['comparison']['changed']['invoice_text'])
        with app.connect() as db:db.execute('UPDATE invoices SET recipient=? WHERE id=?',('later-change',r['payment']['invoice_id']))
        result=insight.get(r['id'],self.owner,app.connect,False);self.assertEqual(result['comparison']['original']['recipient'],'vendor_acme')
        with self.assertRaises(ws.APIError):insight.get(r['id'],'another-owner',app.connect,False)
        with app.connect() as db:db.execute('UPDATE audit SET payload=? WHERE id=?',(json.dumps({**r,'decision':'allow'}),r['id']))
        with self.assertRaises(ws.APIError):insight.get(r['id'],self.owner,app.connect,False)
    def test_cited_model_explanation_cached_and_no_capabilities_in_prompt(self):
        r=self.receipt();answer={'summary':'Simulation denied.','why':'The recipient differs from the registered vendor.','next_step':'Verify the recipient manually and request a fresh explicit review.','citations':['control:recipient','comparison:recipient']}
        with patch.dict(os.environ,{'ANALYZER_MODE':'meta'}),patch.object(insight,'complete_json',return_value=(answer,{'model':'test-meta','usage':{}})) as model:
            first=insight.explain({'receipt_id':r['id']},self.owner,app.connect,False);second=insight.explain({'receipt_id':r['id']},self.owner,app.connect,False)
            self.assertEqual(first,second);self.assertEqual(model.call_count,1)
            sent=json.dumps(model.call_args.args[2]);self.assertNotIn(r['payment']['approval_id'],sent);self.assertNotIn('TOKEN_SHOULD_NOT_BE_SENT',sent)
            self.assertEqual(insight.get(r['id'],self.owner,app.connect,False)['explanation'],first)
        self.assertEqual(app.events(self.owner)[0]['decision'],'deny')
    def test_gmail_and_invented_citations_never_produce_model_answer(self):
        gmail=self.receipt(True)
        with patch.object(insight,'complete_json') as model:
            self.assertTrue(insight.get(gmail['id'],self.owner,app.connect,False)['local_only'])
            with self.assertRaises(ws.APIError):insight.explain({'receipt_id':gmail['id']},self.owner,app.connect,False)
            model.assert_not_called()
        r=self.receipt();bad={'summary':'test','why':'test','next_step':'test','citations':['imaginary-control']}
        with patch.dict(os.environ,{'ANALYZER_MODE':'meta'}),patch.object(insight,'complete_json',return_value=(bad,{'model':'test-meta'})):
            with self.assertRaises(ws.APIError):insight.explain({'receipt_id':r['id']},self.owner,app.connect,False)
