from datetime import datetime
import pytest
from unittest.mock import patch, DEFAULT, call, MagicMock

from lib.readers.iaReader import IAReader
from lib.models.iaRecord import IAItem


class TestIAReader:
    @pytest.fixture
    def testReader(self):
        with patch('lib.readers.iaReader.get_session') as mockSession:
            with patch.dict('os.environ', {'IA_COLLECTIONS': '1, 2, 3'}):
                with patch('lib.readers.iaReader.decryptEnvVar') as mockDecrypt:
                    return IAReader(100)

    def test_init(self, testReader):
        assert testReader.updateSince == 100
        assert testReader.source == 'Internet Archive'
        assert testReader.works == []
        assert testReader.itemIDs == []
        assert isinstance(testReader.iaSession, MagicMock)
        assert testReader.importCollections == ['1', '2', '3']

    def test_collectResourceURLs(self, testReader):
        testReader.iaSession.search_items.side_effect = [
            [{'identifier': 'id1'}, {'identifier': 'id2'}],
            [{'identifier': 'id3'}],
            [{'identifier': 'id4'}, {'identifier': 'id5'}],
        ]
        testReader.collectResourceURLs()
        assert len(testReader.itemIDs) == 5
        testReader.iaSession.search_items.assert_has_calls([
            call('collection:1'), call('collection:2'), call('collection:3')
        ])

    @patch.object(IAReader, 'scrapeRecordMetadata')
    def test_scrapeResourcePages(self, mockScrapeMeta, testReader):
        testReader.itemIDs = ['id1', 'id2', 'id3']
        testReader.iaSession.get_item.side_effect = ['item1', 'item2', 'item3']

        testReader.scrapeResourcePages()

        testReader.iaSession.get_item.assert_has_calls([
            call('id1'), call('id2'), call('id3')
        ])
        mockScrapeMeta.assert_has_calls([
            call('id1', 'item1'), call('id2', 'item2'), call('id3', 'item3')
        ])

    @patch.object(IAReader, 'transformMetadata', return_value='testWork')
    def test_scrapeRecordMetadata_recent(self, mockTransform, testReader):
        testReader.updateSince = datetime.utcnow()
        testItem = MagicMock()
        testItem.metadata = {'title': 'testing', 'updatedate': '3030-01-01 12:00:00'}

        testReader.scrapeRecordMetadata(1, testItem)

        mockTransform.assert_called_once_with(1, testItem.metadata)
    
    @patch.object(IAReader, 'transformMetadata', return_value='testWork')
    def test_scrapeRecordMetadata_old(self, mockTransform, testReader):
        testReader.updateSince = datetime.utcnow()
        testItem = MagicMock()
        testItem.metadata = {'title': 'testing', 'updatedate': '1999-12-31 12:00:00'}

        testReader.scrapeRecordMetadata(1, testItem)

        mockTransform.assert_not_called()
    
    def test_transformMetadata(self, testReader):
        with patch.multiple(IAItem,
            createStructure=DEFAULT,
            parseIdentifiers=DEFAULT,
            parseSubjects=DEFAULT,
            parseAgents=DEFAULT,
            parseRights=DEFAULT,
            parseLanguages=DEFAULT,
            parseDates=DEFAULT,
            parseLinks=DEFAULT,
            parseSummary=DEFAULT,
            addCover=DEFAULT,
        ) as iaItemMethods:
            testReader.transformMetadata(1, {})

            for name, method in iaItemMethods.items():
                method.assert_called_once()
            
            assert len(testReader.works) == 1
