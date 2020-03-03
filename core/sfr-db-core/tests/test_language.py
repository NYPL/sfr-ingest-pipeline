import unittest
from unittest.mock import patch

from sfrCore.model import Language
from sfrCore.helpers import DataError


class TestLanguage(unittest.TestCase):

    @patch.object(Language, 'lookupLanguage', return_value=None)
    @patch.object(Language, 'insert', return_value='test_language')
    def test_check_new(self, mock_insert, mock_lookup):
        res = Language.updateOrInsert('session', {'language': 'test_language'})
        mock_lookup.expect_to_be_called()
        self.assertEqual(res[0], 'test_language')
    
    @patch.object(Language, 'lookupLanguage', return_value='test_language')
    def test_check_existing(self, mock_lookup):
        res = Language.updateOrInsert('session', {'language': 'test_language'})
        self.assertEqual(res[0], 'test_language')

    @patch.object(Language, 'loadFromString', return_value='test_language')
    @patch.object(Language, 'lookupLanguage', return_value='test_language')
    def test_check_string(self, mock_lookup, mock_string):
        res = Language.updateOrInsert('session', 'test_language')
        self.assertEqual(res[0], 'test_language')

    @patch.object(Language, 'loadFromString', return_value=None)
    def test_bad_string(self, mock_string):
        with self.assertRaises(DataError):
            Language.updateOrInsert('session', 'test_language')
    
    def test_insert_lang(self):
        testLang = {
            'language': 'test',
            'iso_2': 'te',
            'iso_3': 'tes'
        }
        lang = Language.insert(testLang)
        self.assertEqual(lang.language, 'test')
    
    def test_iso2_load(self):
        lang = Language.loadFromString('EN')
        self.assertEqual(lang[0]['language'], 'English')
    
    def test_single_char_load(self):
        lang = Language.loadFromString('e')
        self.assertEqual(lang[0]['iso_3'], 'eee')
        self.assertEqual(lang[0]['iso_2'], None)
    
    def test_iso3_load(self):
        lang = Language.loadFromString('eng')
        self.assertEqual(lang[0]['language'], 'English')
    
    def test_lang_load(self):
        lang = Language.loadFromString('english')
        self.assertEqual(lang[0]['language'], 'English')
    
    def test_missing_load(self):
        lang = Language.loadFromString('test')
        self.assertEqual(lang, [])

    def test_parse_lang_plain(self):
        langList = Language.parseLangStr('deu')
        self.assertEqual(langList[0].name, 'German')

    def test_parse_lang_multi(self):
        langList = sorted([l.name for l in Language.parseLangStr('fra;deu')])
        self.assertListEqual(langList, ['French', 'German'])
    
    def test_parse_lang_multi_bad(self):
        langList = sorted([
            l.name for l in Language.parseLangStr('fra;zzz')
            if l is not None
        ])
        self.assertListEqual(langList, ['French'])
