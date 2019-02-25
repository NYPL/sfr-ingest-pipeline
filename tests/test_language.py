import unittest
from unittest.mock import patch

from model.language import Language
from helpers.errorHelpers import DataError


class TestLanguage(unittest.TestCase):

    @patch('model.language.Language.lookupLanguage', return_value=None)
    @patch('model.language.Language.insert', return_value='test_language')
    def test_check_new(self, mock_insert, mock_lookup):
        res = Language.updateOrInsert('session', {'language': 'test_language'})
        mock_lookup.expect_to_be_called()
        self.assertEqual(res, 'test_language')
    
    @patch('model.language.Language.lookupLanguage', return_value='test_language')
    def test_check_existing(self, mock_lookup):
        res = Language.updateOrInsert('session', {'language': 'test_language'})
        self.assertEqual(res, 'test_language')

    @patch('model.language.Language.loadFromString', return_value='test_language')
    @patch('model.language.Language.lookupLanguage', return_value='test_language')
    def test_check_string(self, mock_lookup, mock_string):
        res = Language.updateOrInsert('session', 'test_language')
        self.assertEqual(res, 'test_language')

    @patch('model.language.Language.loadFromString', return_value=None)
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
        self.assertEqual(lang['language'], 'English')
    
    def test_single_char_load(self):
        lang = Language.loadFromString('e')
        self.assertEqual(lang, None)
    
    def test_iso3_load(self):
        lang = Language.loadFromString('eng')
        self.assertEqual(lang['language'], 'English')
    
    def test_lang_load(self):
        lang = Language.loadFromString('english')
        self.assertEqual(lang['language'], 'English')
    
    def test_missing_load(self):
        lang = Language.loadFromString('test')
        self.assertEqual(lang, None)