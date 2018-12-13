import unittest
from unittest.mock import patch, mock_open, call

from lib.parsers.parseOCLC import readFromClassify, extractFromXML, parseWork

class TestOCLCParse(unittest.TestCase):

    @patch('lib.parsers.parseOCLC.extractFromXML')
    @patch('lib.parsers.parseOCLC.combineData', return_value=True)
    def test_classify_read(self, mock_combine, mock_xml):
        res = readFromClassify(['some', 'data'])
        mock_combine.assert_called_once()
        mock_xml.assert_called_once()
        self.assertTrue(res)

    @patch('lib.parsers.parseOCLC.parseWork', return_value=True)
    def test_xml_extract(self, mock_parse):
        res = extractFromXML(['data1', 'data2'])
        mock_parse.assert_has_calls([call('data1'), call('data2')])
        self.assertEqual(res, [True, True])
