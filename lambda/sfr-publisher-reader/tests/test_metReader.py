import pytest
from unittest.mock import patch, DEFAULT, call, MagicMock

from lib.readers.metReader import MetReader
from lib.models.metRecord import MetItem


class TestMETReader:
    @pytest.fixture
    def testReader(self):
        return MetReader()

    def test_init(self, testReader):
        assert testReader.source == 'Metropolitan Museum of Art'
        assert testReader.startPage == 1
        assert testReader.stopPage == 48
        assert testReader.works == []
        assert testReader.itemIDs == []

    @patch('lib.readers.metReader.requests')
    def test_collectResourceURLs(self, mockReq, testReader):
        mockResp = MagicMock()
        mockReq.get.return_value = mockResp
        mockResp.json.return_value = {'items': [{'itemId': 1}, {'itemId': 2}]}
        testReader.collectResourceURLs()
        assert len(testReader.itemIDs) == 94

    @patch('lib.readers.metReader.requests')
    def test_scrapeResourcePages(self, mockReq, testReader):
        mockResp = MagicMock()
        mockReq.get.return_value = mockResp
        mockResp.json.side_effect = ['data1', 'data2']
        testReader.itemIDs = [1, 2]

        with patch.object(MetReader, 'scrapeRecordMetadata') as mockScrape:
            mockScrape.side_effect = ['work1', 'work2']
            testReader.scrapeResourcePages()
            assert len(testReader.works) == 2
            mockScrape.assert_has_calls([call(1, 'data1'), call(2, 'data2')])

    @patch.object(MetReader, 'transformMetadata', return_value='testWork')
    @patch.object(MetItem, 'extractRelevantData')
    def test_scrapeRecordMetadata(self, mockTransform, mockExtract, testReader):
        newItem = testReader.scrapeRecordMetadata(1, {})
        mockExtract.assert_called_once()
        mockTransform.assert_called_once()
        assert newItem == 'testWork'
    
    def test_transformMetadata(self, testReader):
        testItem = MagicMock()
        testItem.instance = MagicMock()
        mockWork = MagicMock()
        mockWork.title = 'testing'
        testItem.work = mockWork

        outWork = testReader.transformMetadata(testItem)
        assert outWork.title == 'testing'
        testItem.createStructure.assert_called_once()
        testItem.parseIdentifiers.assert_called_once()
        testItem.parseSubjects.assert_called_once()
        testItem.parseAgents.assert_called_once()
        testItem.parseRights.assert_called_once()
        testItem.parseLanguages.assert_called_once()
        testItem.parseDates.assert_called_once()
        testItem.parseLinks.assert_called_once()
        testItem.addCover.assert_called_once()
        