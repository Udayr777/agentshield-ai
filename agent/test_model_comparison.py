import importlib.util,os,unittest
from pathlib import Path
from unittest.mock import patch
import app
spec=importlib.util.spec_from_file_location('comparison',Path(__file__).resolve().parents[1]/'scripts'/'compare-models.py');comparison=importlib.util.module_from_spec(spec);spec.loader.exec_module(comparison)
class ComparisonTests(unittest.TestCase):
    def test_override_does_not_mutate_default_model(self):
        with patch.dict(os.environ,{'ANALYZER_MODE':'meta','META_MODEL':'muse-spark-1.3'}),patch.object(app,'complete_json',return_value=({'risk':'low','reason':'ordinary content'},{'model':'muse-wonder-1.0','usage':{}})) as call:
            result=app.analyze({'invoice':'Synthetic service USD 100.00','recipient':'vendor_acme','amount_cents':10000},model_override='muse-wonder-1.0')
            self.assertEqual(call.call_args.kwargs['model_override'],'muse-wonder-1.0');self.assertEqual(result['model'],'muse-wonder-1.0');self.assertEqual(os.environ['META_MODEL'],'muse-spark-1.3')
    def test_abstentions_and_false_classifications_are_separate(self):
        rows=[{'model_requested':'test','expected':expected,'risk':risk,'latency_ms':ms,'usage':{}} for expected,risk,ms in [('high','unknown',10),('high','low',20),('low','high',30),('low','low',40)]]
        s=comparison.summarize(rows)['test'];self.assertEqual(s['correct'],1);self.assertEqual(s['attacks_classified_low'],1);self.assertEqual(s['benign_flagged_high'],1);self.assertEqual(s['unknown_or_errors'],1);self.assertEqual(s['calls_without_token_usage'],4);self.assertEqual(s['p50_ms'],25)
