import unittest
from unittest.mock import patch, MagicMock

from lib.parsers.frontierParser import FrontierParser


class TestFrontierParser(unittest.TestCase):
    def test_init(self):
        testFront = FrontierParser('uri', 'type')
        self.assertEqual(testFront.uri, 'uri')
        self.assertEqual(testFront.media_type, 'type')
    
    def test_validateURI_success(self):
        testFront = FrontierParser(
            'www.frontiersin.org/research-topics/1/testing', 'testType'
        )

        outcome = testFront.validateURI()
        self.assertTrue(outcome)
        self.assertEqual(testFront.identifier, '1')

    def test_validateURI_failure(self):
        testFront = FrontierParser(
            'www.other.com/test/file', 'testType'
        )

        outcome = testFront.validateURI()
        self.assertFalse(outcome)
    
    @patch('lib.parsers.frontierParser.requests')
    def test_createLinks(self, mockReq):
        testFront = FrontierParser('uri', 'type')
        testFront.identifier = 1

        mockResp = MagicMock()
        mockResp.status_code = 200
        mockResp.headers = {'content-disposition': 'attachment; filename=testing.EPUB'}
        mockErr = MagicMock()
        mockErr.status_code = 500
        mockReq.head.side_effect = [mockResp, mockErr]

        testLinks = testFront.createLinks()
        self.assertEqual(
            testLinks[0][0], 'https://www.frontiersin.org/research-topics/1/epub'
        )
        self.assertEqual(
            testLinks[1][0], 'https://www.frontiersin.org/research-topics/1/pdf'
        )
        self.assertTrue(testLinks[0][1]['ebook'])
        self.assertTrue(testLinks[1][1]['ebook'])
        self.assertEqual(testLinks[0][2], 'application/epub+zip')
        self.assertEqual(testLinks[1][2], 'application/pdf')
        self.assertEqual(testLinks[0][3], '1_testing.epub')
        self.assertEqual(testLinks[1][3], None)
