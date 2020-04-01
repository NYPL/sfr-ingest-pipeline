import unittest
from unittest.mock import MagicMock, patch, call

from lib.linkParser import LinkParser, Link, Identifier
from lib.parsers import SpringerParser, DefaultParser


class FakeParserTrue:
    def __init__(self, *args):
        pass

    def validateURI(self):
        return True


class FakeParserFalse:
    def __init__(self, *args):
        pass

    def validateURI(self):
        return False


class TestLinkParser(unittest.TestCase):
    def test_init(self):
        testParser = LinkParser('mockItem', 'mockURI', 'mockType')
        self.assertEqual(testParser.item, 'mockItem')
        self.assertEqual(testParser.uri, 'mockURI')
        self.assertEqual(testParser.media_type, 'mockType')
        self.assertEqual(len(testParser.parsers), 6)
    
    @patch.object(LinkParser, 'sortParsers')
    def test_selectParser_first(self, mockParserSort):
        mockParserSort.return_value = [FakeParserTrue] * 6

        testParser = LinkParser('mockItem', 'mockURI', 'mockType')
        testParser.selectParser()

    @patch.object(LinkParser, 'sortParsers')
    def test_selectParser_last(self, mockParserSort):
        mockParser = MagicMock()
        mockParser.validateURI.return_value = [FakeParserFalse] * 5 + [FakeParserTrue]
        mockParserSort.return_value = [mockParser] * 6

        testParser = LinkParser('mockItem', 'mockURI', 'mockType')
        testParser.selectParser()

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

    def test_sortParsers(self):
        testParser = LinkParser('mockItem', 'mockURI', 'mockType')
        sortedParsers = testParser.sortParsers()

        self.assertEqual(sortedParsers[0], SpringerParser)
        self.assertEqual(sortedParsers[5], DefaultParser)
