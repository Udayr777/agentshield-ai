import base64,importlib.util,io,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import fitz,app,visual,workspace as ws,inspection
spec=importlib.util.spec_from_file_location('visual_benchmark',Path(__file__).resolve().parents[1]/'scripts'/'benchmark-visual.py');fixtures=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixtures)

class InspectionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=os.getcwd());self.patches=[patch.object(app,'PG',None),patch.object(app,'DB',self.temp.name+'/test.db'),patch.dict(os.environ,{'ANALYZER_MODE':'mock'})]
        for p in self.patches:p.start()
        app.init();self.owner=ws.auth({'name':'Visual tester','email':'visual@example.test','password':'Unique-synthetic-pass-2026!'},True,app.connect,False)['user']['id']
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()
    def upload(self,kind,source='upload'):
        with fixtures.fixture(kind,0) as doc:raw=doc.tobytes()
        return visual.ingest({'filename':kind+'.pdf','mime':'application/pdf','data':base64.b64encode(raw).decode()},self.owner,app.connect,False,source)
    def test_labeled_families_and_clean_control(self):
        self.assertEqual(self.upload('clean')['inspection']['findings'],[])
        for kind,expected in [('white_text','low_contrast'),('tiny_text','tiny_text'),('invisible_layer','invisible_text_layer'),('overlap','overlapping_text')]:
            result=self.upload(kind)['inspection'];self.assertIn(expected,{f['kind'] for f in result['findings']})
            self.assertEqual(result['page'],1)
            for finding in result['findings']:
                b=finding['box'];self.assertGreaterEqual(b['x'],0);self.assertLessEqual(b['x']+b['w'],1)
                self.assertNotIn('attacker_wallet',json.dumps(finding))
    def test_raster_and_nonpreview_are_not_claimed_as_scanned(self):
        out=io.BytesIO();Image.new('RGB',(100,100),'white').save(out,format='PNG')
        result=inspection.inspect('data:image/png;base64,'+base64.b64encode(out.getvalue()).decode())
        self.assertEqual(result['status'],'not_measured');self.assertTrue(result['enhanced_preview']);self.assertEqual(inspection.inspect('')['status'],'not_measured')
    def test_clip_script_is_bounded_private_and_cached(self):
        doc=self.upload('white_text');gmail=self.upload('white_text','gmail')
        result={'scenes':[{'caption':'Low contrast text was observed in the first page.','evidence_ids':['e1']},{'caption':'These observations do not establish whether this invoice is authentic.','evidence_ids':[]},{'caption':'Inspect highlighted regions and manually verify fields and recipient.','evidence_ids':[]}]}
        with patch.dict(os.environ,{'ANALYZER_MODE':'meta'}),patch('meta_client.complete_json',return_value=(result,{'model':'test-meta','usage':{}})) as model:
            with self.assertRaises(ws.APIError):inspection.clip({'document_id':doc['id']},'another-owner',app.connect,False)
            with self.assertRaises(ws.APIError):inspection.clip({'document_id':gmail['id']},self.owner,app.connect,False)
            first=inspection.clip({'document_id':doc['id']},self.owner,app.connect,False)
            self.assertEqual(first['duration_seconds'],18);self.assertEqual(len(first['scenes']),3)
            self.assertEqual(first,inspection.clip({'document_id':doc['id']},self.owner,app.connect,False));self.assertEqual(model.call_count,1)
            # Restoring a saved clip stays read-only even after new-generation quota is full.
            with app.connect() as db:
                for i in range(5):db.execute('INSERT INTO inspection_explanations(document_id,owner_id,payload,created_at) VALUES (?,?,?,?)',('quota-'+str(i),self.owner,'{}',int(__import__('time').time())))
            self.assertEqual(first,inspection.cached_clip(doc['id'],self.owner,app.connect,False))
            self.assertEqual(model.call_count,1)
            with self.assertRaises(ws.APIError):inspection.cached_clip(doc['id'],'another-owner',app.connect,False)
            self.assertNotIn('attacker_wallet',json.dumps(model.call_args.args[2]));self.assertNotIn('preview',model.call_args.args[2])
    def test_clip_rejects_invented_evidence_and_does_not_retry(self):
        doc=self.upload('white_text');scene={'caption':'This is an invented unsupported evidence reference.','evidence_ids':['fake']}
        with patch.dict(os.environ,{'ANALYZER_MODE':'meta'}),patch('meta_client.complete_json',return_value=({'scenes':[scene]*3},{'model':'test-meta'})) as model:
            with self.assertRaises(ws.APIError):inspection.clip({'document_id':doc['id']},self.owner,app.connect,False)
            with self.assertRaises(ws.APIError):inspection.clip({'document_id':doc['id']},self.owner,app.connect,False)
            self.assertEqual(model.call_count,1)
    def test_explanation_owner_gmail_reference_validation_and_cache(self):
        doc=self.upload('white_text');gmail=self.upload('white_text','gmail');ids=[f['id'] for f in doc['inspection']['findings']]
        with patch.dict(os.environ,{'ANALYZER_MODE':'meta'}),patch('meta_client.complete_json',return_value=({'summary':'Low contrast requires review.','evidence_ids':ids[:1],'next_step':'Inspect the original.'},{'model':'test-meta','usage':{}})) as model:
            with self.assertRaises(ws.APIError):inspection.explain({'document_id':doc['id']},'another-owner',app.connect,False)
            with self.assertRaises(ws.APIError):inspection.explain({'document_id':gmail['id']},self.owner,app.connect,False)
            first=inspection.explain({'document_id':doc['id']},self.owner,app.connect,False);second=inspection.explain({'document_id':doc['id']},self.owner,app.connect,False)
            self.assertEqual(first,second);self.assertEqual(model.call_count,1);self.assertNotIn('invoice_text',json.dumps(model.call_args.args[2]))
        other=self.upload('tiny_text')
        with patch.dict(os.environ,{'ANALYZER_MODE':'meta'}),patch('meta_client.complete_json',return_value=({'summary':'test','evidence_ids':['invented'],'next_step':'test'},{'model':'test-meta'})):
            with self.assertRaises(ws.APIError):inspection.explain({'document_id':other['id']},self.owner,app.connect,False)
