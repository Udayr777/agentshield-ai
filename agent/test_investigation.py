import base64,json,os,tempfile,unittest
from unittest.mock import patch
import app,workspace as ws,investigation as agent,judge
class InvestigationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=os.getcwd());self.patches=[patch.object(app,'PG',None),patch.object(app,'DB',self.temp.name+'/test.db'),patch.dict(os.environ,{'ANALYZER_MODE':'meta','BASETEN_API_KEY':'test-partner-key','LEDGER_KEY_FILE':self.temp.name+'/key'})]
        for p in self.patches:p.start()
        app.init();self.owner=ws.auth({'name':'Investigator','email':'investigator@example.test','password':'Synthetic-test-password-2026!'},True,app.connect,False)['user']['id'];self.invoice=judge.load(self.owner,app.connect,False)['cases'][1]['invoice_id']
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()
    def model(self,purpose,instruction,evidence,schema,**kwargs):
        meta={'model':kwargs.get('model_override'),'provider':kwargs.get('provider') or 'meta','reported_model':kwargs.get('model_override'),'response_id':'fixture-response','usage':{'total_tokens':10}}
        if purpose=='investigation_plan':
            options=evidence['available_tools'];action=next(t for t in ('read_invoice','inspect_visual','review_open_weight','finish') if t in options)
            return {'action':action,'reason':'Inspect available evidence.'},meta
        if purpose=='open_weight_forensics':return {'risk':'high','summary':'Instruction-like content warrants manual inspection.','citations':['invoice:content']},meta
        return {'headline':'Evidence for manual review','summary':'Read-only observations; no payment was approved.','next_step':'Verify fields through a trusted channel.','storyboard':[{'title':name,'caption':'Inspect the recorded evidence and its limitations.','citations':['invoice:fields']} for name in ('Observed','Uncertain','Next step')]},meta
    def start(self,**kwargs):return agent.start({'invoice_id':self.invoice,'confirmed_external_processing':True},self.owner,app.connect,False,spawn=False,**kwargs)
    def test_model_selected_tools_partner_provenance_and_no_payment_mutation(self):
        with patch.object(agent,'complete_json',side_effect=self.model) as model:run=self.start()
        self.assertEqual(run['status'],'complete');self.assertTrue(run['partner_response_recorded']);self.assertEqual(len(run['trace']),4)
        self.assertEqual([t['action'] for t in run['trace']],['read_invoice','inspect_visual','review_open_weight','finish'])
        self.assertEqual(sum(c.args[0]=='investigation_plan' for c in model.call_args_list),1);self.assertEqual(run['trace'][2]['planner']['provider'],'deterministic');self.assertTrue(any(c.kwargs.get('provider')=='baseten' for c in model.call_args_list));self.assertEqual(run['report_provenance']['model'],'muse-wonder-1.0')
        self.assertEqual(ws.get_invoice(self.invoice,self.owner,app.connect,False)['status'],'pending');self.assertEqual(app.events(self.owner),[])
        with app.connect() as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM approvals').fetchone()[0],0)
        public=agent.share(run['id'],self.owner,app.connect,False);self.assertNotIn('attacker_wallet',json.dumps(public));self.assertNotIn('invoice:content',json.dumps(public))
        with self.assertRaises(ws.APIError):agent.read(run['id'],'other-owner',app.connect,False)
        with app.connect() as db:db.execute('UPDATE investigation_runs SET payload=? WHERE id=?',('{}',run['id']))
        with self.assertRaises(ws.APIError):agent.read(run['id'],self.owner,app.connect,False)
    def test_unauthorized_tools_fail_and_release_capacity(self):
        with patch.object(agent,'complete_json',return_value=({'action':'execute_payment','reason':'unsafe'},{'model':'fixture'})):
            run=self.start()
        self.assertEqual(run['status'],'failed');self.assertEqual(app.events(self.owner),[])
        self.assertTrue(agent.CAPACITY.acquire(False));agent.CAPACITY.release()
    def test_gmail_and_no_consent_never_call_models(self):
        with patch.object(agent,'complete_json') as model:
            with self.assertRaises(ws.APIError):agent.start({'invoice_id':self.invoice},self.owner,app.connect,False,spawn=False)
            with app.connect() as db:db.execute('UPDATE invoices SET origin=? WHERE id=?',('gmail',self.invoice))
            with self.assertRaises(ws.APIError):self.start()
            model.assert_not_called()
    def test_meta_only_mode_does_not_claim_partner_use(self):
        with patch.dict(os.environ,{'BASETEN_API_KEY':''}),patch.object(agent,'complete_json',side_effect=self.model):run=self.start()
        self.assertEqual(run['status'],'complete');self.assertFalse(run['partner_response_recorded']);self.assertNotIn('review_open_weight',[t['action'] for t in run['trace']])

    def test_malformed_planner_cannot_skip_required_partner_review(self):
        from meta_client import MetaError
        with patch.object(agent,'complete_json',side_effect=MetaError('invalid_model_json')) as model:run=self.start()
        self.assertEqual(run['status'],'failed')
        self.assertEqual(run['error_stage'],'planner_step_2')
        self.assertEqual([t['action'] for t in run['trace']],['read_invoice'])
        self.assertFalse(run['partner_response_recorded'])
        self.assertEqual(model.call_count,1)

    def test_invalid_json_after_partner_uses_labeled_saved_visual_fallback(self):
        from meta_client import MetaError
        def model(purpose,instruction,evidence,schema,**kwargs):
            if purpose=='investigation_plan':
                if 'review_open_weight' in evidence['available_tools']:
                    return {'action':'review_open_weight','reason':'Review the evidence.'},{'model':'fixture'}
                raise MetaError('invalid_model_json')
            return self.model(purpose,instruction,evidence,schema,**kwargs)
        with patch.object(agent,'complete_json',side_effect=model):run=self.start()
        self.assertEqual(run['status'],'complete');self.assertTrue(run['partner_response_recorded'])
        self.assertEqual([t['action'] for t in run['trace']],['read_invoice','review_open_weight','inspect_visual','finish'])
        self.assertEqual(run['trace'][2]['planner']['provider'],'deterministic')
        self.assertIn('invalid JSON',run['trace'][2]['reason'])
        self.assertEqual(app.events(self.owner),[])
        self.assertEqual(ws.get_invoice(self.invoice,self.owner,app.connect,False)['status'],'pending')
