import os,time,unittest
from unittest.mock import patch
import helpdesk,workspace as ws
class PublicHelpTests(unittest.TestCase):
    def setUp(self):
        self.old_calls=list(helpdesk.PUBLIC_CALLS);self.old_limits=dict(helpdesk.LIMITS);helpdesk.PUBLIC_CALLS.clear();helpdesk.LIMITS.clear()
    def tearDown(self):
        helpdesk.PUBLIC_CALLS[:]=self.old_calls;helpdesk.LIMITS.clear();helpdesk.LIMITS.update(self.old_limits)
    def test_anonymous_help_has_only_docs_and_question(self):
        with patch.dict(os.environ,{'ANALYZER_MODE':'meta'}),patch.object(helpdesk,'complete_json',return_value=({'answer':'Load the Judge Demo Pack.','citations':['demo']},{'model':'test-meta','usage':{}})) as call:
            result=helpdesk.public_chat({'question':'How do I start?','invoice':'must not be forwarded','owner_id':'ignored'})
            self.assertEqual(result['mode'],'meta');self.assertEqual(set(call.call_args.args[2]),{'documentation','question'});self.assertNotIn('must not be forwarded',str(call.call_args))
    def test_public_budget_returns_help_without_model_calls(self):
        helpdesk.PUBLIC_CALLS[:]=[time.time()]*20
        with patch.object(helpdesk,'complete_json') as call:
            result=helpdesk.public_chat({'question':'How do I upload?'})
            self.assertEqual(result['mode'],'static_fallback');call.assert_not_called()
    def test_invalid_question_never_reaches_model(self):
        with patch.object(helpdesk,'complete_json') as call:
            for q in ('',None,'x'*601):
                with self.assertRaises(ws.APIError):helpdesk.public_chat({'question':q})
            call.assert_not_called()
