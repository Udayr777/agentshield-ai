import os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from meta_client import load_config

class ConfigTests(unittest.TestCase):
    def test_database_settings_load_without_overriding_runtime_secrets(self):
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as folder:
            path=Path(folder)/'.env'
            path.write_text('DATABASE_URL=postgresql://test.invalid/db\nDATABASE_URL_UNPOOLED=postgresql://direct.invalid/db\nMETA_API_KEY=file-secret\nUNRELATED_SETTING=ignored\n',encoding='utf-8')
            with patch.dict(os.environ,{'META_API_KEY':'runtime-secret'},clear=True):
                load_config(path)
                self.assertEqual(os.environ['DATABASE_URL'],'postgresql://test.invalid/db')
                self.assertEqual(os.environ['DATABASE_URL_UNPOOLED'],'postgresql://direct.invalid/db')
                self.assertEqual(os.environ['META_API_KEY'],'runtime-secret')
                self.assertNotIn('UNRELATED_SETTING',os.environ)
