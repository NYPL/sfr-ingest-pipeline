import unittest
from unittest.mock import patch, MagicMock

from lib.parsers import DeGruyterParser


class TestDeGruyterParser(unittest.TestCase):
    def test_init(self):
        testGruy = DeGruyterParser('uri', 'type')
        self.assertEqual(testGruy.uri, 'uri')
        self.assertEqual(testGruy.media_type, 'type')
    
    def test_validateURI_success(self):
        testGruy = DeGruyterParser(
            'www.degruyter.com/view/books/123/123/123.xml', 'testType'
        )

        outcome = testGruy.validateURI()
        self.assertTrue(outcome)

    def test_validateURI_failure(self):
        testGruy = DeGruyterParser(
            'www.other.com/test/file', 'testType'
        )

        outcome = testGruy.validateURI()
        self.assertFalse(outcome)
    
    @patch('lib.parsers.degruyterParser.requests')
    def test_createLinks_isbn_link(self, mockReq):
        testGruy = DeGruyterParser('degruyter.com/97812346579', 'type')

        mockResp = MagicMock()
        mockResp.status_code = 301 
        mockResp.headers = {'Location': '/title/123456'}
        mockEpub = MagicMock()
        mockEpub.status_code = 200
        mockReq.head.side_effect = [mockResp, mockEpub]

        testLinks = testGruy.createLinks()
        self.assertEqual(
            testLinks[0][0], 'https://www.degruyter.com/downloadepub/title/123456'
        )
        self.assertEqual(
            testLinks[1][0], 'https://www.degruyter.com/downloadpdf/title/123456'
        )
        self.assertTrue(testLinks[0][1]['ebook'])
        self.assertTrue(testLinks[1][1]['ebook'])
        self.assertEqual(testLinks[0][2], 'application/epub+zip')
        self.assertEqual(testLinks[1][2], 'application/pdf')
        self.assertEqual(testLinks[0][3], 'degruyter_123456.epub')
        self.assertEqual(testLinks[1][3], None)

    @patch('lib.parsers.degruyterParser.requests')
    def test_createLinks_degruy_link_no_epub(self, mockReq):
        testGruy = DeGruyterParser('degruyter.com/viewtoc/987654', 'type')

        mockResp = MagicMock()
        mockResp.status_code = 301 
        mockResp.headers = {'Location': '/title/123456'}
        mockEpub = MagicMock()
        mockEpub.status_code = 404
        mockReq.head.side_effect = [mockResp, mockEpub]

        testLinks = testGruy.createLinks()
        self.assertEqual(
            testLinks[0][0], 'https://www.degruyter.com/downloadpdf/title/123456'
        )
        self.assertTrue(testLinks[0][1]['ebook'])
        self.assertEqual(testLinks[0][2], 'application/pdf')
        self.assertEqual(testLinks[0][3], None)