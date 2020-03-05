import unittest
from unittest.mock import patch, MagicMock

from lib.parsers.springerParser import SpringerParser 


class TestSpringerParser(unittest.TestCase):
    def test_init(self):
        testFront = SpringerParser('uri', 'type')
        self.assertEqual(testFront.uri, 'uri')
        self.assertEqual(testFront.media_type, 'type')
    
    def test_validateURI_success(self):
        testSpring = SpringerParser(
            'link.springer.com/book/10.007/123-456-7890', 'testType'
        )

        outcome = testSpring.validateURI()
        self.assertTrue(outcome)
        self.assertEqual(testSpring.identifier, '123-456-7890')
        self.assertEqual(testSpring.code, '10.007')

    def test_validateURI_failure(self):
        testSpring = SpringerParser(
            'www.other.com/test/file', 'testType'
        )

        outcome = testSpring.validateURI()
        self.assertFalse(outcome)

    @patch('lib.parsers.springerParser.requests')
    def test_validateURI_recursive(self, mockReq):
        testSpring = SpringerParser(
            'link.springer.com/content?isbn=XXXX-XXXX-XXXX-XXXX', 'testType'
        )

        mockHead = MagicMock()
        mockHead.headers = {
            'Location': 'link.springer.com/book/10.027/999-999-999'
        }
        mockReq.head.return_value = mockHead

        outcome = testSpring.validateURI()
        self.assertTrue(outcome)
        self.assertEqual(testSpring.uri, 'link.springer.com/book/10.027/999-999-999')
    
    def test_createLinks(self):
        testSpring = SpringerParser('uri', 'type')
        testSpring.code = '10.000'
        testSpring.identifier = 1

        testLinks = testSpring.createLinks()
        self.assertEqual(
            testLinks[0][0], 'https://link.springer.com/download/epub/10.000/1.epub'
        )
        self.assertEqual(
            testLinks[1][0], 'https://link.springer.com/content/pdf/10.000/1.pdf'
        )
        self.assertTrue(testLinks[0][1]['ebook'])
        self.assertTrue(testLinks[1][1]['ebook'])
        self.assertEqual(testLinks[0][2], 'application/epub+zip')
        self.assertEqual(testLinks[1][2], 'application/pdf')
        self.assertEqual(testLinks[0][3], None)
        self.assertEqual(testLinks[1][3], None)
