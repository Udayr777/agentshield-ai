import os, unittest, tempfile, json, uuid, copy
from concurrent.futures import ThreadPoolExecutor
from replay import prepare
import app
from unittest.mock import patch
from app import analyze, scenarios
class AnalyzerTests(unittest.TestCase):
    def test_authorization_secrets_never_enter_model_evidence(self):
        with patch.dict(os.environ,{'ANALYZER_MODE':'meta'}),patch('app.complete_json',return_value=({'risk':'low','reason':'ordinary invoice'},{'model':'test','usage':{}})) as complete:
            p={**scenarios()[0]['payment'],'approval':'secret approval text','approval_id':'private capability','session':'private session'}
            self.assertEqual(analyze(p)['risk'],'low')
            evidence=complete.call_args.args[2]
            self.assertEqual(set(evidence),{'recipient','amount_cents','invoice','currency'})
    def test_mock(self):
        with patch.dict(os.environ,{'ANALYZER_MODE':'mock'}):
            self.assertEqual(analyze(scenarios()[0]['payment'])['risk'],'low')
            self.assertEqual(analyze(scenarios()[4]['payment'])['risk'],'high')
    def test_live_failure_blocks(self):
        with patch.dict(os.environ,{'ANALYZER_MODE':'meta','META_API_KEY':''}):
            with patch('urllib.request.urlopen',side_effect=OSError('offline')):
                self.assertEqual(analyze({})['risk'],'unknown')
class AuditTests(unittest.TestCase):
    def test_capability_single_use_mismatch_expiry_and_atomic_rollback(self):
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as folder:
            with patch.object(app,'PG',None), patch.object(app,'DB',folder+'/audit.db'):
                app.init()
                def event(p,ident=None): return {'id':ident or str(uuid.uuid4()),'decision':'allow','reason':'policy passed','payment':copy.deepcopy(p)}
                prepared=prepare({'scenario':'authorized','amount_cents':10000},app.connect,False)
                p=prepared['payment']
                wrong={**p,'amount_cents':9999}
                self.assertEqual(app.audit(event(wrong))['decision'],'deny')
                # Two simultaneous submissions can consume a capability only once.
                with ThreadPoolExecutor(2) as pool:
                    decisions=list(pool.map(lambda _:app.audit(event(p))['decision'],range(2)))
                self.assertEqual(sorted(decisions),['allow','deny'])
                expired=prepare({'scenario':'expired','amount_cents':10000},app.connect,False)
                self.assertEqual(app.audit(event(expired['payment']))['decision'],'deny')
                fresh=prepare({'scenario':'authorized','amount_cents':10000},app.connect,False)['payment']
                app.audit({'id':'duplicate','decision':'deny'})
                with self.assertRaises(Exception):app.audit(event(fresh,'duplicate'))
                self.assertEqual(app.audit(event(fresh))['decision'],'allow','Failed audit must roll back capability consumption')
    def test_durable_insert_duplicate_rollback_and_reopen(self):
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as folder:
            with patch.object(app,'PG',None), patch.object(app,'DB',folder+'/audit.db'):
                app.init(); app.init()
                item={'id':'test-1','decision':'allow'}
                app.audit(item)
                self.assertEqual(app.events(),[item])
                with self.assertRaises(Exception): app.audit(item)
                self.assertEqual(app.events(),[item])
                app.audit({'id':'test-2','decision':'deny'})
                self.assertEqual(len(app.events()),2)
if __name__=='__main__': unittest.main()
