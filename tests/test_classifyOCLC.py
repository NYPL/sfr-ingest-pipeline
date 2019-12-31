import unittest
from unittest.mock import patch, MagicMock

from helpers.errorHelpers import DataError, OCLCError
from lib.readers.oclcClassify import QueryManager


class TestOCLCClassify(unittest.TestCase):

    def test_query_create(self):
        testQuery = QueryManager(
            'test',
            'testID',
            'testType',
            'testAuthor',
            'testTitle',
            0
        )
        self.assertEqual(testQuery.title, 'testTitle')
        self.assertEqual(testQuery.query, None)
    
    @patch('lib.readers.oclcClassify.QueryManager.generateIdentifierURL')
    @patch('lib.readers.oclcClassify.QueryManager.generateAuthorTitleURL')
    def test_generate_query(self, mock_title, mock_id):
        testQuery = QueryManager(
            'test',
            'testID',
            'testType',
            'testAuthor',
            'testTitle',
            0
        )
        testQuery.generateQueryURL()
        mock_title.assert_called_once()
        mock_id.assert_not_called()
    
    @patch('lib.readers.oclcClassify.QueryManager.generateIdentifierURL')
    @patch('lib.readers.oclcClassify.QueryManager.generateAuthorTitleURL')
    def test_generate_author_query(self, mock_title, mock_id):
        testQuery = QueryManager(
            'identifier',
            'testID',
            'testType',
            'testAuthor',
            'testTitle',
            0
        )
        testQuery.generateQueryURL()
        mock_id.assert_called_once()
        mock_title.assert_not_called()
    
    def test_clean_title(self):
        rawTitle = ' Hello\r weird\n title thingy '
        testQuery = QueryManager(None, None, None, None, rawTitle, 0)
        testQuery.cleanTitle()
        self.assertEqual(testQuery.title, 'Hello weird title thingy')
    
    @patch('lib.readers.oclcClassify.QueryManager.cleanTitle')
    @patch('lib.readers.oclcClassify.QueryManager.addClassifyOptions')
    def test_author_generate(self, mock_add, mock_clean):
        testQuery = QueryManager(None, None, None, 'Tester', 'Test Title', 0)
        testQuery.generateAuthorTitleURL()

        self.assertEqual(
            testQuery.query,
            'http://classify.oclc.org/classify2/Classify?title=Test Title&author=Tester'
        )
        mock_add.assert_called_once()
        mock_clean.assert_called_once()
    
    def test_author_missing(self):
        with self.assertRaises(DataError):
            testQuery = QueryManager(None, None, None, None, 'Sole Title', 0)
            testQuery.generateAuthorTitleURL()

    def test_author_missing_empty_string(self):
        with self.assertRaises(DataError):
            testQuery = QueryManager(None, None, None, '', 'Sole Title', 0)
            testQuery.generateAuthorTitleURL()
            
    
    @patch('lib.readers.oclcClassify.QueryManager.addClassifyOptions')
    def test_identifier_generate(self, mock_add):
        testQuery = QueryManager(None, 'testID', 'isbn', None, None, 0)
        testQuery.generateIdentifierURL()

        self.assertEqual(
            testQuery.query,
            'http://classify.oclc.org/classify2/Classify?isbn=testID'
        )
        mock_add.assert_called_once()
    
    @patch('lib.readers.oclcClassify.QueryManager.generateAuthorTitleURL')
    def test_identifier_none(self, mock_author):
        testQuery = QueryManager(None, None, None, None, None, 0)
        testQuery.generateIdentifierURL()

        mock_author.asert_called_once()
    
    def test_identifier_error(self):
        testQuery = QueryManager(None, 'testID', 'testType', None, None, 0)
        try:
            testQuery.generateIdentifierURL()
        except DataError:
            pass
        self.assertRaises(DataError)
    
    def test_add_options(self):
        testQuery = QueryManager(None, None, None, None, None, 0)
        testQuery.query = 'testQuery'
        testQuery.addClassifyOptions()
        self.assertEqual(
            testQuery.query,
            'testQuery&summary=false&startRec=0&maxRecs=500'
        )
    
    @patch('lib.readers.oclcClassify.requests')
    def test_exec_query(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = 'testing'
        mock_requests.get.return_value = mock_resp
        
        testQuery = QueryManager(None, None, None, None, None, 0)
        testRes = testQuery.execQuery()
        self.assertEqual(testRes, 'testing')

    @patch('lib.readers.oclcClassify.requests')
    def test_exec_query_err(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = 'testing'
        mock_requests.get.return_value = mock_resp
        
        testQuery = QueryManager(None, None, None, None, None, 0)
        
        try:
            testQuery.execQuery()
        except OCLCError:
            pass
        self.assertRaises(OCLCError)
