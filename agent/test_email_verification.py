import hashlib,os,tempfile,time,unittest
from unittest.mock import patch
import app,workspace as ws,email_verification as ev
class EmailVerificationTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(dir=os.getcwd());self.patches=[patch.object(app,'PG',None),patch.object(app,'DB',self.temp.name+'/test.db'),patch.dict(os.environ,{'RESEND_API_KEY':'test-private','PASSWORD_RESET_FROM':'shield@example.test','APP_PUBLIC_URL':'https://example.test','LEDGER_KEY_FILE':self.temp.name+'/key'})]
  for p in self.patches:p.start()
  app.init();self.user=ws.auth({'name':'Mailbox tester','email':'mail@example.test','password':'Synthetic-password-2026!'},True,app.connect,False)['user'];self.owner=self.user['id']
 def tearDown(self):
  for p in reversed(self.patches):p.stop()
  self.temp.cleanup()
 def token(self):
  with patch.object(ev,'deliver') as deliver:ev.request(self.owner,app.connect,False)
  self.assertEqual(deliver.call_args.args[0],'mail@example.test');return deliver.call_args.args[1]
 def test_one_use_hash_only_no_session_or_payment_side_effects(self):
  token=self.token()
  with app.connect() as db:
   stored=db.execute('SELECT token_hash FROM email_verifications').fetchone()[0];before=db.execute('SELECT COUNT(*) FROM sessions').fetchone()[0]
  self.assertEqual(stored,hashlib.sha256(token.encode()).hexdigest());self.assertNotEqual(token,stored)
  self.assertFalse(ev.state(self.owner,app.connect,False)['verified']);ev.confirm({'token':token},app.connect,False)
  self.assertTrue(ev.state(self.owner,app.connect,False)['verified'])
  with self.assertRaises(ws.APIError):ev.confirm({'token':token},app.connect,False)
  with app.connect() as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM sessions').fetchone()[0],before)
  self.assertEqual(app.events(self.owner),[])
 def test_expiry_resend_and_account_bound_address(self):
  old=self.token()
  with self.assertRaises(ws.APIError) as caught:ev.request(self.owner,app.connect,False)
  self.assertEqual(caught.exception.status,429)
  with patch.object(ev.time,'time',return_value=time.time()+61):new=self.token()
  with self.assertRaises(ws.APIError):ev.confirm({'token':old},app.connect,False)
  with patch.object(ev.time,'time',return_value=time.time()+1900):
   with self.assertRaises(ws.APIError):ev.confirm({'token':new},app.connect,False)
  with app.connect() as db:db.execute('UPDATE users SET email=? WHERE id=?',('changed@example.test',self.owner))
  with self.assertRaises(ws.APIError):ev.confirm({'token':new},app.connect,False)
  self.assertFalse(ev.state(self.owner,app.connect,False)['verified'])
 def test_delivery_failure_invalidates_token_without_leaking_details(self):
  with patch.object(ev,'deliver',side_effect=RuntimeError('private-provider-detail')):
   with self.assertRaises(ws.APIError) as caught:ev.request(self.owner,app.connect,False)
  self.assertNotIn('private-provider-detail',str(caught.exception))
  with app.connect() as db:self.assertEqual(db.execute('SELECT used FROM email_verifications').fetchone()[0],1)
 def test_unconfigured_invalid_origin_and_owner_isolation(self):
  with patch.dict(os.environ,{'APP_PUBLIC_URL':'https://untrusted.test/path'}):
   self.assertFalse(ev.state(self.owner,app.connect,False)['configured'])
   with self.assertRaises(ws.APIError):ev.request(self.owner,app.connect,False)
  with self.assertRaises(ws.APIError):ev.state('another-owner',app.connect,False)
  with self.assertRaises(ws.APIError):ev.confirm({'token':'invalid'},app.connect,False)
 def test_limits_three_per_account_and_global(self):
  self.token()
  for seconds in (61,122):
   with patch.object(ev.time,'time',return_value=time.time()+seconds):self.token()
  with patch.object(ev.time,'time',return_value=time.time()+183):
   with self.assertRaises(ws.APIError) as caught:ev.request(self.owner,app.connect,False)
  self.assertEqual(caught.exception.status,429)

 def test_state_exposes_cooldown_without_exposing_token(self):
  token=self.token();status=ev.state(self.owner,app.connect,False)
  self.assertGreater(status['retry_after_seconds'],0);self.assertLessEqual(status['retry_after_seconds'],60)
  self.assertTrue(status['pending_link']);self.assertNotIn(token,str(status))
  with patch.object(ev.time,'time',return_value=time.time()+61):self.assertEqual(ev.state(self.owner,app.connect,False)['retry_after_seconds'],0)
