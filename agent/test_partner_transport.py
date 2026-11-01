import io,json,os,unittest
from unittest.mock import patch
import meta_client
class PartnerTransportTests(unittest.TestCase):
    def test_baseten_uses_separate_key_endpoint_and_reports_actual_metadata(self):
        response=io.BytesIO(json.dumps({'id':'provider-test','model':'meta-models/muse-spark-open','usage':{'total_tokens':12},'choices':[{'finish_reason':'stop','message':{'content':'{"risk":"low"}'}}]}).encode());response.headers={}
        with patch.dict(os.environ,{'META_API_KEY':'meta-private-test','BASETEN_API_KEY':'partner-private-test'}),patch.object(meta_client.urllib.request,'urlopen',return_value=response) as network,patch.object(meta_client,'record') as telemetry:
            result,meta=meta_client.complete_json('partner_test','Read only',{'synthetic':True},{'type':'object'},provider='baseten',model_override='meta-models/muse-spark-open-1026')
        req=network.call_args.args[0];body=json.loads(req.data)
        self.assertEqual(req.full_url,'https://inference.baseten.co/v1/chat/completions');self.assertEqual(req.get_header('Authorization'),'Bearer partner-private-test')
        self.assertIn('max_tokens',body);self.assertNotIn('max_completion_tokens',body);self.assertEqual(body['messages'][0]['role'],'system')
        self.assertEqual(meta['reported_model'],'meta-models/muse-spark-open');self.assertEqual(meta['provider'],'baseten');self.assertNotIn('partner-private-test',str(telemetry.call_args))
    def test_missing_partner_key_never_falls_back_to_meta(self):
        with patch.dict(os.environ,{'META_API_KEY':'meta-private-test','BASETEN_API_KEY':''}),patch.object(meta_client.urllib.request,'urlopen') as network:
            with self.assertRaises(meta_client.MetaError):meta_client.complete_json('test','test',{}, {},provider='baseten')
            network.assert_not_called()

    def test_safe_distinct_transport_errors(self):
        cases=[(TimeoutError('private detail'),'provider_timeout'),(meta_client.urllib.error.URLError('private host'),'provider_connection_failed')]
        for failure,expected in cases:
            with self.subTest(expected=expected),patch.dict(os.environ,{'BASETEN_API_KEY':'private-test'}),patch.object(meta_client.urllib.request,'urlopen',side_effect=failure),patch.object(meta_client,'record') as record:
                with self.assertRaises(meta_client.MetaError) as caught:meta_client.complete_json('test','private invoice',{}, {},provider='baseten')
                self.assertEqual(caught.exception.code,expected)
                self.assertNotIn('private',str(record.call_args))
    def test_malformed_response_is_not_reported_as_network_failure(self):
        response=io.BytesIO(b'not json');response.headers={}
        with patch.dict(os.environ,{'BASETEN_API_KEY':'private-test'}),patch.object(meta_client.urllib.request,'urlopen',return_value=response),patch.object(meta_client,'record'):
            with self.assertRaises(meta_client.MetaError) as caught:meta_client.complete_json('test','test',{}, {},provider='baseten')
        self.assertEqual(caught.exception.code,'invalid_provider_response')
