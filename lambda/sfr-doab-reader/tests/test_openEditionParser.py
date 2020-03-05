import unittest
from unittest.mock import patch, MagicMock, DEFAULT, call

from lib.parsers import OpenEditionParser


class TestOpenEditionParser(unittest.TestCase):
    def test_init(self):
        testFront = OpenEditionParser('uri', 'type')
        self.assertEqual(testFront.uri, 'http://uri')
        self.assertEqual(testFront.media_type, 'type')
    
    def test_init_withHTTP(self):
        testFront = OpenEditionParser('http://uri', 'type')
        self.assertEqual(testFront.uri, 'http://uri')
        self.assertEqual(testFront.media_type, 'type')
    
    def test_validateURI_success(self):
        testSpring = OpenEditionParser(
            'externallinkservice.com?url=books.openedition.org/test/123', 'testType'
        )

        outcome = testSpring.validateURI()
        self.assertTrue(outcome)
        self.assertEqual(testSpring.publisher, 'test')
        self.assertEqual(testSpring.identifier, '123')

    def test_validateURI_failure(self):
        testSpring = OpenEditionParser(
            'www.other.com/test/file', 'testType'
        )

        outcome = testSpring.validateURI()
        self.assertFalse(outcome)

    @patch.multiple(
        OpenEditionParser,
        loadEbookLinks=DEFAULT,
        parseBookLink=DEFAULT,
        getBestLink=DEFAULT
    )
    @patch('lib.parsers.openEditionParser.requests')
    def test_createLinks_success(self, mockReq, loadEbookLinks, parseBookLink, getBestLink):
        testSpring = OpenEditionParser('uri', 'type')
        testSpring.uri = 'openedition.org/test/123'

        oeResp = MagicMock()
        oeResp.status_code = 200
        oeResp.text = 'mock_html_content'

        mockReq.get.return_value = oeResp

        loadEbookLinks.return_value = ['link1', 'link2']
        getBestLink.return_value = True

        testLinks = testSpring.createLinks()
        self.assertTrue(testLinks)
        mockReq.get.assert_called_once_with('http://openedition.org/test/123')
        loadEbookLinks.assert_called_once_with('mock_html_content')
        parseBookLink.assert_has_calls([
            call([], 'link1'), call([], 'link2')
        ])
        getBestLink.assert_called_once_with([])
    
    @patch.object(OpenEditionParser, 'getBestLink', return_value=False)
    @patch('lib.parsers.openEditionParser')
    def test_createLinks_failure(self, mockReq, mockGetBest):
        testSpring = OpenEditionParser('uri', 'type')
        testSpring.uri = 'openedition.org/test/123'

        oeResp = MagicMock()
        oeResp.status_code = 404

        self.assertFalse(testSpring.createLinks())
    
    def test_loadEbookLinks_found(self):
        mockHTML = """<html>
        <head>
            <title>HTML Test Page With Links</title>
        </head>
        <body>
            <div class="open-edition-body">
                <div id="book-access">
                    <a href="test1">Testing</a>
                    <a href="test2">Testing</a>
                    <a href="test3">Testing</a>
                </div>
            </div>
        </body>
        </html>
        """

        testSpring = OpenEditionParser('uri', 'type')
        linkList = testSpring.loadEbookLinks(mockHTML)
        self.assertEqual(len(linkList), 3)
        self.assertEqual(linkList[1].get('href'), 'test2')
    
    def test_parseBookLink_foundMatch(self):
        testSpring = OpenEditionParser('uri', 'type')
        testSpring.publisher = 'test'
        testSpring.identifier = '123'

        testOptions = []
        mockLink = MagicMock()
        mockLink.get.return_value = 'books.openedition.org/epub/123'

        testSpring.parseBookLink(testOptions, mockLink)

        self.assertEqual(len(testOptions), 1)
        self.assertEqual(testOptions[0][3], 'application/epub+zip')
        self.assertEqual(testOptions[0][4], 'test_123.epub')

    def test_parseBookLink_noMatch(self):
        testSpring = OpenEditionParser('uri', 'type')

        testOptions = []
        mockLink = MagicMock()
        mockLink.get.return_value = 'books.openedition.org/something/123'

        testSpring.parseBookLink(testOptions, mockLink)

        self.assertEqual(len(testOptions), 0)

    def test_getBestLink_success(self):
        testSpring = OpenEditionParser('uri', 'type')
        testOptions = [(3, 'test3'), (1, 'test1'), (2, 'test2')]
        testMatch = testSpring.getBestLink(testOptions)
        self.assertEqual(testMatch[0], 'test1')

    def test_getBestLink_none(self):
        testSpring = OpenEditionParser('uri', 'type')
        testOptions = []
        testMatch = testSpring.getBestLink(testOptions)
        self.assertEqual(testMatch, [])
