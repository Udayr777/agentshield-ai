import hashlib,os,tempfile,time,unittest
from unittest.mock import patch
import app,workspace as ws,password_reset as reset
class ResetTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=os.getcwd());self.patches=[patch.object(app,'PG',None),patch.object(app,'DB',self.temp.name+'/test.db'),patch.dict(os.environ,{'RESEND_API_KEY':'test-only','PASSWORD_RESET_FROM':'AgentShield <noreply@example.test>','APP_PUBLIC_URL':'https://shield.example.test'})]
        for p in self.patches:p.start()
        app.init();self.account=ws.auth({'name':'Tester','email':'reset@example.test','password':'Old-password-2026!'},True,app.connect,False)
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()
    def test_single_use_hash_only_and_revokes_sessions(self):
        with patch.object(reset,'deliver') as mail:
            response=reset.request({'email':'reset@example.test'},app.connect,False);token=mail.call_args.args[1]
        with app.connect() as db:
            encoded=db.execute('SELECT token_hash FROM password_resets').fetchone()[0];self.assertEqual(encoded,hashlib.sha256(token.encode()).hexdigest());self.assertNotEqual(encoded,token)
        result=reset.reset({'token':token,'password':'New-password-2026!'},app.connect,False)
        self.assertNotIn(token,str(result));self.assertNotIn(token,str(response))
        with self.assertRaises(ws.APIError):ws.session(self.account['token'],app.connect,False)
        with self.assertRaises(ws.APIError):reset.reset({'token':token,'password':'Other-password-2026!'},app.connect,False)
        with self.assertRaises(ws.APIError):ws.auth({'email':'reset@example.test','password':'Old-password-2026!'},False,app.connect,False)
        self.assertEqual(ws.auth({'email':'reset@example.test','password':'New-password-2026!'},False,app.connect,False)['user']['id'],self.account['user']['id'])
    def test_generic_response_throttle_expiry_and_delivery_failure(self):
        with patch.object(reset,'deliver') as mail:
            known=reset.request({'email':'reset@example.test'},app.connect,False);token=mail.call_args.args[1]
            unknown=reset.request({'email':'absent@example.test'},app.connect,False);repeat=reset.request({'email':'reset@example.test'},app.connect,False)
            self.assertEqual(known,unknown);self.assertEqual(known,repeat);self.assertEqual(mail.call_count,1)
        with app.connect() as db:db.execute('UPDATE password_resets SET expires_at=0')
        with self.assertRaises(ws.APIError):reset.reset({'token':token,'password':'New-password-2026!'},app.connect,False)
        with app.connect() as db:db.execute('DELETE FROM reset_requests')
        with patch.object(reset,'deliver',side_effect=RuntimeError('provider failed')):
            self.assertEqual(reset.request({'email':'reset@example.test'},app.connect,False),known)
        with app.connect() as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM password_resets WHERE used=0 AND expires_at>?',(time.time(),)).fetchone()[0],0)
    def test_unconfigured_and_untrusted_origin(self):
        with patch.dict(os.environ,{'APP_PUBLIC_URL':'https://evil.example/path'}):
            self.assertFalse(reset.status()['configured'])
            with self.assertRaises(ws.APIError):reset.request({'email':'reset@example.test'},app.connect,False)
