import unittest
from unittest.mock import MagicMock, patch, call

from lib.linkParser import LinkParser, DefaultParser, FrontierParser, Link, Identifier


class TestLinkParser(unittest.TestCase):
    def test_init(self):
        testParser = LinkParser('mockItem', 'mockURI', 'mockType')
        self.assertEqual(testParser.item, 'mockItem')
        self.assertEqual(testParser.uri, 'mockURI')
        self.assertEqual(testParser.media_type, 'mockType')
    
    @patch.object(DefaultParser, 'validateURI')
    @patch.object(FrontierParser, 'validateURI')
    def test_selectParser_first(self, frontValidate, defaultValidate):
        frontValidate.return_value = True
        testParser = LinkParser('mockItem', 'mockURI', 'mockType')
        testParser.selectParser()

        frontValidate.assert_called_once()
        defaultValidate.assert_not_called()
        self.assertIsInstance(testParser.parser, FrontierParser)

    @patch.object(DefaultParser, 'validateURI')
    @patch.object(FrontierParser, 'validateURI')
    def test_selectParser_last(self, frontValidate, defaultValidate):
        frontValidate.return_value = False
        defaultValidate.return_value = True
        testParser = LinkParser('mockItem', 'mockURI', 'mockType')
        testParser.selectParser()

        frontValidate.assert_called_once()
        defaultValidate.assert_called_once()
        self.assertIsInstance(testParser.parser, DefaultParser)

    def test_createLinks(self):
        mockItem = MagicMock()
        mockParser = MagicMock()
        mockParser.createLinks.return_value = [
            ('url1', 'flags1', 'type1', '1_test.epub'),
            ('url2', 'flags2', 'type2', None)
        ]

        testParser = LinkParser(mockItem, 'mockURI', 'mockType')
        testParser.parser = mockParser

        testParser.createLinks()

        mockItem.addClassItem.assert_has_calls([
            call(
                'links', Link, url='url1', media_type='type1', flags='flags1'
            ),
            call(
                'identifiers', Identifier, type='doab', identifier='1_test.epub', weight=1
            ),
            call(
                'links', Link, url='url2', media_type='type2', flags='flags2'
            )
        ])
