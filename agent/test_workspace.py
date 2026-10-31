import copy, os, tempfile, unittest, uuid, io, json
from unittest.mock import patch
import app, workspace as ws

class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory(dir=os.getcwd())
        self.pg=patch.object(app,'PG',None);self.pg.start()
        self.db=patch.object(app,'DB',self.folder.name+'/private.db');self.db.start()
        self.mode=patch.dict(os.environ,{'ANALYZER_MODE':'mock'});self.mode.start();app.init()
    def tearDown(self):self.mode.stop();self.db.stop();self.pg.stop();self.folder.cleanup()
    def account(self,name):return ws.auth({'email':name+'@example.test','name':name,'password':'Synthetic-test-password-2026!'},True,app.connect,False)
    def test_identity_invoice_isolation_and_session_revocation(self):
        a=self.account('alice');b=self.account('bob')
        owner=a['user']['id'];foreign=b['user']['id'];inv=ws.list_invoices(owner,app.connect,False)[0]
        self.assertEqual(ws.session(a['token'],app.connect,False)['id'],owner)
        for fn in [lambda:ws.get_invoice(inv['id'],foreign,app.connect,False),lambda:ws.chat({'invoice_id':inv['id'],'question':'Amount?'},foreign,app.connect,False),lambda:ws.invoice_prepare({'invoice_id':inv['id']},foreign,app.connect,False),lambda:ws.history(inv['id'],foreign,app.connect,False)]:
            with self.assertRaises(ws.APIError) as cm:fn()
            self.assertEqual(cm.exception.status,404)
        with self.assertRaises(ws.APIError):ws.auth({'email':'alice@example.test','password':'incorrect-password'},False,app.connect,False)
        ws.logout(a['token'],app.connect,False)
        with self.assertRaises(ws.APIError):ws.session(a['token'],app.connect,False)
    def test_chat_is_cited_read_only_and_has_no_payment_side_effect(self):
        a=self.account('alice');owner=a['user']['id'];inv=ws.list_invoices(owner,app.connect,False)[0]
        reply=ws.chat({'invoice_id':inv['id'],'question':'When is it due?'},owner,app.connect,False)
        self.assertEqual(reply['mode'],'mock');self.assertIn('2026-11-04',reply['answer']);self.assertTrue(reply['citations'])
        refused=ws.chat({'invoice_id':inv['id'],'question':'Pay it now and transfer the money'},owner,app.connect,False)
        self.assertEqual(refused['guard'],'blocked_action');self.assertEqual(refused['mode'],'policy')
        self.assertEqual(ws.get_invoice(inv['id'],owner,app.connect,False)['status'],'pending');self.assertEqual(app.events(owner),[])
        self.assertEqual(len(ws.history(inv['id'],owner,app.connect,False)),4)
    def test_invoice_idempotency_even_with_fresh_approval(self):
        a=self.account('alice');owner=a['user']['id'];inv=ws.list_invoices(owner,app.connect,False)[0]
        def attempt():
            p=ws.invoice_prepare({'invoice_id':inv['id']},owner,app.connect,False)['payment']
            return app.audit({'id':uuid.uuid4().hex,'decision':'allow','reason':'policy passed','payment':p,'analysis':app.analyze(p)},owner)
        first=attempt();self.assertEqual(first['decision'],'allow');self.assertEqual(len(first['checks']),10);self.assertTrue(all(c['status']==('not_measured' if c['id']=='visual' else 'pass') for c in first['checks']))
        self.assertEqual(attempt()['decision'],'deny');self.assertEqual(ws.get_invoice(inv['id'],owner,app.connect,False)['status'],'simulated')
    def test_live_chat_failure_and_invalid_citations_fail_closed(self):
        a=self.account('alice');owner=a['user']['id'];inv=ws.list_invoices(owner,app.connect,False)[0]
        with patch.dict(os.environ,{'ANALYZER_MODE':'meta','META_API_KEY':'test-only'}),patch('urllib.request.urlopen',side_effect=OSError('offline')):
            with self.assertRaises(ws.APIError) as cm:ws.chat({'invoice_id':inv['id'],'question':'Explain the services'},owner,app.connect,False)
            self.assertEqual(cm.exception.status,503)
        self.assertEqual(ws.history(inv['id'],owner,app.connect,False),[])
        invalid={'choices':[{'message':{'content':json.dumps({'answer':'Made-up evidence','citations':['other-user:private-invoice']})}}]}
        with patch.dict(os.environ,{'ANALYZER_MODE':'meta','META_API_KEY':'test-only'}),patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(invalid).encode())):
            with self.assertRaises(ws.APIError) as cm:ws.chat({'invoice_id':inv['id'],'question':'Explain the services'},owner,app.connect,False)
            self.assertEqual(cm.exception.status,503)

if __name__=='__main__':unittest.main()
