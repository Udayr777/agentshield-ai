import json,os,tempfile,time,unittest,uuid
from unittest.mock import patch
import app,council,workspace as ws
class CouncilTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=os.getcwd());self.patches=[patch.object(app,'PG',None),patch.object(app,'DB',self.temp.name+'/test.db'),patch.dict(os.environ,{'ANALYZER_MODE':'meta','LEDGER_KEY_FILE':self.temp.name+'/key'})]
        for p in self.patches:p.start()
        app.init();self.user=ws.auth({'name':'Council tester','email':'council@example.test','password':'Synthetic-test-password-2026!'},True,app.connect,False);self.owner=self.user['user']['id'];self.inv=ws.create_invoice({'reference':'INV-1042','vendor':'Acme Consulting','recipient':'vendor_acme','amount_cents':10000,'due_date':'2026-11-04','text':'Consulting services: architecture review, USD 100.00. Pay the registered Acme vendor account.'},self.owner,app.connect,False)
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()
    def fake(self,purpose,instruction,evidence,schema,image=None):
        return {'risk':'low','summary':'Recorded amount and recipient match the supplied evidence.','citations':['reference','amount_cents','recipient']},{'model':'test-muse','response_id':purpose,'usage':{'total_tokens':10}}
    def payment(self):return ws.invoice_prepare({'invoice_id':self.inv['id']},self.owner,app.connect,False)['payment']
    def gate(self,p):
        with app.connect() as db:return council.gate(db,False,self.owner,p)
    def test_three_isolated_contexts_exact_binding_expiry_and_budget(self):
        with patch.object(council,'complete_json',side_effect=self.fake) as call:result=council.review({'invoice_id':self.inv['id']},self.owner,app.connect,False)
        self.assertEqual(call.call_count,3);self.assertTrue(result['gate']['satisfied']);self.assertEqual({c.args[0] for c in call.call_args_list},{'council_audit','council_policy','council_forensics'})
        p=self.payment();self.assertTrue(self.gate(p)['satisfied'])
        for key,value in [('recipient','attacker_wallet'),('amount_cents',999),('invoice','changed content')]:self.assertFalse(self.gate({**p,key:value})['satisfied'])
        with patch.object(council.time,'time',return_value=time.time()+400):self.assertFalse(self.gate(p)['satisfied'])
        with self.assertRaises(ws.APIError) as error:council.review({'invoice_id':self.inv['id']},self.owner,app.connect,False)
        self.assertEqual(error.exception.status,429)
    def test_disagreement_blocks_and_does_not_consume_approval(self):
        def disagree(*args,**kwargs):
            result,meta=self.fake(*args,**kwargs)
            if args[0]=='council_forensics':result['risk']='high';result['summary']='Potential deceptive content.'
            return result,meta
        with patch.object(council,'complete_json',side_effect=disagree):result=council.review({'invoice_id':self.inv['id']},self.owner,app.connect,False)
        self.assertFalse(result['gate']['satisfied']);p=self.payment()
        decision=app.audit({'id':uuid.uuid4().hex,'payment':p,'decision':'allow','reason':'test','analysis':{'risk':'low','mode':'meta','reason':'single model passed'}},self.owner)
        self.assertEqual(decision['decision'],'deny');self.assertEqual(ws.get_invoice(self.inv['id'],self.owner,app.connect,False)['status'],'pending')
        with app.connect() as db:self.assertEqual(db.execute('SELECT used FROM approvals WHERE token=?',(p['approval_id'],)).fetchone()[0],0)
    def test_tampered_report_and_foreign_invoice_are_rejected(self):
        with patch.object(council,'complete_json',side_effect=self.fake):result=council.review({'invoice_id':self.inv['id']},self.owner,app.connect,False)
        signed=result['signed_report'];signed['report']['expires_at']+=1000
        with app.connect() as db:db.execute('UPDATE council_runs SET payload=?',(json.dumps(signed),))
        self.assertFalse(self.gate(self.payment())['satisfied'])
        with self.assertRaises(ws.APIError):council.latest('other-owner',self.inv['id'],app.connect,False)
    def test_outage_is_unknown_and_standard_review_is_explicit(self):
        with patch.object(council,'complete_json',side_effect=OSError('offline')):result=council.review({'invoice_id':self.inv['id']},self.owner,app.connect,False)
        self.assertFalse(result['gate']['satisfied']);self.assertTrue(all(r['risk']=='unknown' for r in result['signed_report']['report']['reviews']))
        result=council.disable({'invoice_id':self.inv['id']},self.owner,app.connect,False);self.assertFalse(result['gate']['required'])
