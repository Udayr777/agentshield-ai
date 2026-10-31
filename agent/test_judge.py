import copy,os,tempfile,unittest,uuid
from unittest.mock import patch
import app,judge,workspace as ws,ledger,helpdesk
class JudgeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=os.getcwd());self.patches=[patch.object(app,'PG',None),patch.object(app,'DB',self.temp.name+'/test.db'),patch.dict(os.environ,{'ANALYZER_MODE':'mock','LEDGER_KEY_FILE':self.temp.name+'/key'})]
        for p in self.patches:p.start()
        app.init();self.user=ws.auth({'name':'Judge','email':'judge@example.test','password':'Synthetic-test-password-2026!'},True,app.connect,False);self.owner=self.user['user']['id']
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()
    def test_pack_is_idempotent_and_geometry_blocks_before_consumption(self):
        cases=judge.load(self.owner,app.connect,False)['cases'];self.assertEqual(len(cases),3)
        self.assertEqual(cases,judge.load(self.owner,app.connect,False)['cases'])
        for case in cases:
            prepared=ws.invoice_prepare({'invoice_id':case['invoice_id']},self.owner,app.connect,False)
            payment=prepared.get('payment',prepared)
            result=app.audit({'id':uuid.uuid4().hex,'payment':payment,'decision':'allow','reason':'test','analysis':{'mode':'mock','risk':'low','reason':'deliberately force low to isolate visual enforcement'}},self.owner)
            visual=next(c for c in result['checks'] if c['id']=='visual')
            self.assertEqual(visual['status'],'fail' if case['case']=='shifted' else 'pass')
            if case['case']=='shifted':
                self.assertEqual(result['decision'],'deny');self.assertEqual(ws.get_invoice(case['invoice_id'],self.owner,app.connect,False)['status'],'pending')
                with app.connect() as db:self.assertEqual(db.execute('SELECT used FROM approvals WHERE token=?',(payment['approval_id'],)).fetchone()[0],0)
        self.assertTrue(ledger.inspect(self.owner,app.connect,False)['valid'])
    def test_help_has_no_financial_or_tool_context(self):
        result=helpdesk.chat({'question':'How do I upload an invoice?'},self.owner)
        self.assertEqual(result['mode'],'static');self.assertIn('upload',result['citations'])
        self.assertEqual(app.events(self.owner),[])
