import os
import json
import unittest
from unittest.mock import patch, MagicMock

from helpers.errorHelpers import UnglueError
from lib.unglueit import Unglueit


@patch.dict(os.environ, {
    'ISBN_LOOKUP': 'unglueISBN',
    'OPDS_LOOKUP': 'unglueOPDS',
    'USERNAME': 'test_user',
    'API_KEY': 'test_api_key'

})
class TestUnglueSearch(unittest.TestCase):
    def test_create_search_object(self):
        testInstance = Unglueit('9999999999')
        self.assertEqual(testInstance.isbn, '9999999999')
        self.assertEqual(testInstance.unglueitSearch, 'unglueISBN')

    @patch('lib.unglueit.Unglueit.validateISBN10')
    def test_validate_isbn10(self, mock_isbn10):
        validateTest = Unglueit('99-999-9999-9')
        validateTest.validate()
        mock_isbn10.assert_called_once_with('9999999999')

    @patch('lib.unglueit.Unglueit.validateISBN13')
    def test_validate_isbn13(self, mock_isbn13):
        validateTest = Unglueit('978-99-999-9999-9')
        validateTest.validate()
        mock_isbn13.assert_called_once_with('9789999999999')

    def test_validate_invalid_characters(self):
        validateTest = Unglueit('fake iSBN 978xxxxx')
        with self.assertRaises(UnglueError):
            validateTest.validate()

    def test_validate_invalid_character_count(self):
        validateTest = Unglueit('999999999')
        with self.assertRaises(UnglueError):
            validateTest.validate()

    def test_isbn10_validate(self):
        Unglueit.validateISBN10('080442957X')
        Unglueit.validateISBN10('8090273416')
        Unglueit.validateISBN10('9386954214')
        Unglueit.validateISBN10('1843560283')
        with self.assertRaises(UnglueError):
            Unglueit.validateISBN10('9992159107')

    def test_isbn13_validate(self):
        Unglueit.validateISBN13('9781566199094')
        Unglueit.validateISBN13('9781402894626')
        Unglueit.validateISBN13('9781861978769')
        Unglueit.validateISBN13('9780199535569')
        with self.assertRaises(UnglueError):
            Unglueit.validateISBN13('9781585340982')
        with self.assertRaises(UnglueError):
            Unglueit.validateISBN13('978158534098X')

    @patch('lib.unglueit.Unglueit.getWork', return_value=1)
    @patch('lib.unglueit.Unglueit.getSummary', return_value='summary')
    @patch('lib.unglueit.Unglueit.formatResponse', return_value=True)
    def test_summary_fetch(self, mock_resp, mock_summary, mock_work):
        unglueTest = Unglueit('9999999999')
        output = unglueTest.fetchSummary()
        mock_work.assert_called_once()
        mock_summary.assert_called_once_with(1)
        mock_resp.assert_called_once_with(
            200,
            {
                'match': True,
                'isbn': '9999999999',
                'summary': 'summary'
            }
        )
        self.assertTrue(output)

    @patch('lib.unglueit.requests.get')
    def test_uglueit_work_search(self, mock_get):
        unglueTest = Unglueit('999999999')
        mock_req = MagicMock()
        mock_get.return_value = mock_req
        mock_req.status_code = 200
        mock_req.json.return_value = {
            'objects': [
                {
                    'work': '/api/test/1/'
                }
            ]
        }

        testWorkID = unglueTest.getWork()
        self.assertEqual(testWorkID, '1')

    @patch('lib.unglueit.requests.get')
    def test_uglueit_work_search_error(self, mock_get):
        unglueTest = Unglueit('999999999')
        mock_req = MagicMock()
        mock_get.return_value = mock_req
        mock_req.status_code = 500
        with self.assertRaises(UnglueError):
            unglueTest.getWork()

    @patch('lib.unglueit.requests.get')
    def test_uglueit_work_id_error(self, mock_get):
        unglueTest = Unglueit('999999999')
        mock_req = MagicMock()
        mock_get.return_value = mock_req
        mock_req.status_code = 200
        mock_req.json.return_value = {
            'objects': [
                {
                    'work': '/api/test/something/'
                }
            ]
        }
        with self.assertRaises(UnglueError):
            unglueTest.getWork()

    @patch('lib.unglueit.requests.get')
    @patch('lib.unglueit.Unglueit.parseOPDS', return_value='fakeXMLDocument')
    def test_unglueit_summary_fetch(self, mock_parse, mock_get):
        unglueTest = Unglueit('999999999')
        mock_req = MagicMock()
        mock_get.return_value = mock_req
        mock_req.status_code = 200
        mock_req.text = 'fakeXMLDocument'

        testSummary = unglueTest.getSummary('1')
        mock_parse.assert_called_once_with('fakeXMLDocument')
        self.assertEqual(testSummary, 'fakeXMLDocument')

    @patch('lib.unglueit.requests.get')
    def test_unglueit_summary_fetch_error(self, mock_get):
        unglueTest = Unglueit('999999999')
        mock_req = MagicMock()
        mock_get.return_value = mock_req
        mock_req.status_code = 500
        with self.assertRaises(UnglueError):
            unglueTest.getSummary('1')

    def test_unglueit_opds_parse(self):
        testXML = """<feed xmlns="http://www.w3.org/2005/Atom">
            <title>Test Unglue.it Record</title>
            <entry xmlns:ns0="http://www.w3.org/2005/Atom">
                <title>Test Unglue.it Record</title>
                <content ns0:type="html">A summary of the work</content>
            </entry>
        </feed>
        """
        unglueTest = Unglueit('9999999999')
        summaryText = unglueTest.parseOPDS(testXML)
        self.assertEqual(summaryText, 'A summary of the work')

    def test_format_response(self):
        testResp = Unglueit.formatResponse(200, {'test': 'test'})
        self.assertEqual(testResp['statusCode'], 200)
        self.assertEqual(json.loads(testResp['body'])['test'], 'test')
