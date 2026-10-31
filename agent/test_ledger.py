import json,os,tempfile,unittest
from unittest.mock import patch
import app,ledger

class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=os.getcwd())
        self.patches=[patch.object(app,'PG',None),patch.object(app,'DB',self.temp.name+'/test.db'),patch.dict(os.environ,{'LEDGER_KEY_FILE':self.temp.name+'/key'})]
        for p in self.patches:p.start()
        app.init()
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()
    def event(self,ident):
        data={'id':ident,'checks':[{'id':'recipient','status':'fail'}],'decision':'deny'}
        with app.connect() as db:
            db.execute('INSERT INTO audit(id,payload,owner_id,recorded_at) VALUES (?,?,?,?)',(ident,json.dumps(data),'alice',0));ledger.append(db,False,'alice',data)
    def test_node_tamper_is_detected_and_append_refused(self):
        self.event('first')
        with app.connect() as db:db.execute("UPDATE audit SET payload=? WHERE id='first'",(json.dumps({'id':'first','checks':[],'decision':'allow'}),))
        self.assertFalse(ledger.inspect('alice',app.connect,False)['valid'])
        with self.assertRaises(Exception):self.event('second')
    def test_tail_deletion_detected_against_exported_checkpoint(self):
        self.event('first');self.event('second');checkpoint=ledger.inspect('alice',app.connect,False)['checkpoint']
        with app.connect() as db:
            db.execute("DELETE FROM audit WHERE id='second'");db.execute("DELETE FROM audit_ledger WHERE event_id='second'")
        self.assertTrue(ledger.inspect('alice',app.connect,False)['valid'])
        self.assertFalse(ledger.inspect('alice',app.connect,False,checkpoint)['valid'])
        self.assertFalse(ledger.inspect('bob',app.connect,False,checkpoint)['valid'])
