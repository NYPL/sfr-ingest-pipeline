import unittest
from unittest.mock import patch, MagicMock

from lib.parsers.mdpiParser import MDPIParser


class TestMDPIParser(unittest.TestCase):
    def test_init(self):
        testMDPI = MDPIParser('uri', 'type')
        self.assertEqual(testMDPI.uri, 'uri')
        self.assertEqual(testMDPI.media_type, 'type')
    
    def test_validateURI_success(self):
        testMDPI = MDPIParser(
            'mdpi.com/books/pdfview/book/1', 'testType'
        )

        outcome = testMDPI.validateURI()
        self.assertTrue(outcome)
        self.assertEqual(testMDPI.identifier, '1')

    def test_validateURI_failure(self):
        testMDPI = MDPIParser(
            'www.other.com/test/file', 'testType'
        )

        outcome = testMDPI.validateURI()
        self.assertFalse(outcome)
    
    def test_createLinks(self):
        testMDPI = MDPIParser('mdpi.com/books/pdfview/book/1', 'type')
        testMDPI.identifier = 1

        testLinks = testMDPI.createLinks()
        self.assertEqual(
            testLinks[0][0], 'mdpi.com/books/pdfdownload/book/1'
        )
        self.assertTrue(testLinks[0][1]['ebook'])
        self.assertTrue(testLinks[0][1]['download'])
        self.assertEqual(testLinks[0][2], 'application/pdf')
