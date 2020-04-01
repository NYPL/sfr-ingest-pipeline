import pytest
from unittest.mock import patch, DEFAULT, call, MagicMock

from lib.sourceManager import SourceManager, OutputManager, readers
from lib.readers.abstractReader import AbsSourceReader


class TestManager:
    @pytest.fixture
    def testManager(self):
        return SourceManager()

    def test_init(self, testManager):
        assert testManager.updatePeriod == 1200
        assert testManager.works == []
        assert isinstance(testManager.output, OutputManager)
        for module in testManager.readers:
            name, reader = module
            assert isinstance(reader(), AbsSourceReader)

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

        testManager.fetchRecords()
        assert len(testManager.works) == 3 * len(testManager.readers)

    @patch.dict('os.environ', {'KINESIS_INGEST_STREAM': 'testStream'})
    def test_sendWorksToKinesis(self, testManager):
        mockWork = MagicMock()
        testManager.works = [mockWork]
        with patch.object(OutputManager, 'putKinesis') as mockPut:
            testManager.sendWorksToKinesis()
            mockPut.assert_called_with(vars(mockWork), 'testStream', recType='work')
