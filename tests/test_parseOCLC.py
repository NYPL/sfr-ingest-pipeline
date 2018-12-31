import unittest
from unittest.mock import patch, mock_open, call

from lib.parsers.parseOCLC import readFromClassify

class TestOCLCParse(unittest.TestCase):

    @patch('lib.parsers.parseOCLC.parseWork', return_value=True)
    def test_classify_read(self, mock_parse):
        res = readFromClassify(['some', 'data'])
        mock_parse.assert_called_once()
        self.assertTrue(res)
