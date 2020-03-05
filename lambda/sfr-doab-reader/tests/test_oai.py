import unittest
from unittest.mock import patch, MagicMock, call

from lib.oaiParse import parseOAI, readRecord, getResumptionToken
from helpers.errorHelpers import OAIFeedError


class TestOAI(unittest.TestCase):
    
    @patch('lib.oaiParse.readRecord', side_effect=['xml1', 'xml2', None, 'xml3'])
    @patch('lib.oaiParse.getResumptionToken', return_value='token')
    def test_parse_oai(self, mock_read, mock_token):
        with patch('lib.oaiParse.etree') as mock_tree:
            mock_xml = MagicMock()
            mock_xml.findall.return_value = ['rec1', 'rec2', 'badRec', 'rec3']
            mock_tree.XML.return_value = mock_xml

            resToken, records = parseOAI('oaiFeed')
            
            self.assertEqual(resToken, 'token')
            self.assertEqual(records[2], 'xml3')
    
    def test_read_xml(self):
        testRec = MagicMock()
        testRec.findtext.return_value = 'testID'

        testHeader = MagicMock()
        testDate = MagicMock()
        testDate.text = 'testDate'
        testHeader.find.return_value = testDate
        testMARC = MagicMock()
        testRec.find.side_effect = [testHeader, testMARC]

        testXML = MagicMock()
        testXML.titleStatement.return_value = 'test_title'
        testXML.name = 'testXML'

        with patch('lib.oaiParse.marcalyx') as mock_parse:
            mock_parse.Record.return_value = testXML

            recData = readRecord(testRec)

            self.assertEqual(recData[0], 'testID')
            self.assertEqual(recData[1], 'testDate')
            self.assertEqual(recData[2].name, 'testXML')
    
    def test_read_deleted(self):
        testRec = MagicMock()
        testHeader = MagicMock()
        testHeader.get.return_value = 'deleted'
        testRec.find.return_value = testHeader
        res = readRecord(testRec)
        self.assertEqual(res, None)
    
    def test_marcalyx_err(self):
        testRec = MagicMock()

        with patch('lib.oaiParse.marcalyx') as mock_parse:
            mock_parse.side_effect = TypeError
        
        res = readRecord(testRec)
        self.assertEqual(res, None)
    
    def test_get_resumption_token(self):
        testFeed = MagicMock()
        testToken = MagicMock()
        testToken.text = 'test_token'
        testFeed.find.return_value = testToken

        res = getResumptionToken(testFeed)
        self.assertEqual(res, 'test_token')
    
    def test_check_for_missing_token(self):
        testFeed = MagicMock()
        testFeed.find.side_effect = AttributeError

        res = getResumptionToken(testFeed)
        self.assertEqual(res, None)