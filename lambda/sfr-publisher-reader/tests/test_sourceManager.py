from datetime import datetime, timedelta
import pytest
from unittest.mock import patch, DEFAULT, call, MagicMock

from lib.sourceManager import SourceManager, OutputManager, readers
from lib.readers.abstractReader import AbsSourceReader


class TestManager:
    @pytest.fixture
    def testTime(self):
        return datetime.utcnow()

    @pytest.fixture
    def testManager(self, testTime):
        with patch('lib.sourceManager.datetime') as mockDT:
            mockDT.utcnow.return_value = testTime
            return SourceManager()

    def test_init(self, testManager, testTime):
        assert testManager.updatePeriod == testTime - timedelta(seconds=1200)
        assert testManager.works == []
        assert isinstance(testManager.output, OutputManager)
        for module in testManager.readers:
            name, reader = module
            assert isinstance(reader(100), AbsSourceReader)

    def test_fetchRecords(self, testManager):
        mockReader = MagicMock()
        mockClass = MagicMock()
        mockClass.return_value = mockReader

        mockReader.collectResourceURLs = MagicMock()
        mockReader.scrapeResourcePages.return_value = MagicMock()
        mockReader.works = ['test1', 'test2', 'test3']

        testManager.readers = [
            (module[0], mockClass) for module in testManager.readers
        ]
        testManager.activeReaders = [r[0] for r in testManager.readers]

        testManager.fetchRecords()
        assert len(testManager.works) == 3 * len(testManager.readers)
    
    def test_fetchRecords_reader_inactive(self, testManager):
        mockReader = MagicMock()
        mockClass = MagicMock()

        testManager.readers = [
            (module[0], mockClass) for module in testManager.readers
        ]

        testManager.fetchRecords()

        mockClass.assert_not_called()
        assert len(testManager.works) == 0


    @patch.dict('os.environ', {'KINESIS_INGEST_STREAM': 'testStream'})
    def test_sendWorksToKinesis(self, testManager):
        mockWork = MagicMock()
        testManager.works = [mockWork]
        with patch.object(OutputManager, 'putKinesis') as mockPut:
            testManager.sendWorksToKinesis()
            mockPut.assert_called_with(vars(mockWork), 'testStream', recType='work')
