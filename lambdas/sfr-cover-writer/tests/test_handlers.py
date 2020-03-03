import pytest
from unittest.mock import call, MagicMock

from service import handler, parseRecords, parseRecord
from helpers.errorHelpers import NoRecordsReceived, DataError


class TestHandler:
    @pytest.fixture
    def testSource(self):
        return {'source': 'SQS'}

    def test_handler_clean(self, testSource, mocker):
        mocker.patch('service.parseRecords', return_value='Hello, World')
        testSource['Records'] = [{
            'body': '{"data": "data"}'
        }]
        resp = handler(testSource, None)
        assert resp == 'Hello, World'

    def test_handler_error(self, testSource):
        testSource['Records'] = []
        with pytest.raises(NoRecordsReceived):
            handler(testSource, None)

    def test_records_none(self, testSource):
        with pytest.raises(NoRecordsReceived):
            handler(testSource, None)

    def test_parseRecords(self, mocker):
        testRecords = ['record1', 'record2', 'record3']
        mocker.patch('service.OutputManager', return_value=True)
        mockParse = mocker.patch('service.parseRecord', side_effect=[1, 2, 3])
        parseResults = parseRecords(testRecords)
        assert parseResults == [1, 2, 3]
        mockParse.assert_has_calls([
            call('record1', True),
            call('record2', True),
            call('record3', True)
        ])

    def test_parseRecord(self, mocker):
        testEncRec = {
            'body': '{"url": "www.testing.url"}'
        }
        testURL = 's3.testing.url'
        mockCoverParse = mocker.patch('service.CoverParse')()
        mockCoverParse.s3CoverURL = testURL
        mockKinesisPut = MagicMock()
        mocker.patch.dict('os.environ', {'DB_UPDATE_STREAM': 'testing'})

        outURL = parseRecord(testEncRec, mockKinesisPut)
        assert outURL == testURL
        mockCoverParse.storeCover.assert_called_once()
        mockKinesisPut.putKinesis.assert_called_once()

    def test_parseRecord_invalidJSON(self):
        malformedJSON = {
            'body': '{"field: "its missing a quotation mark"}'
        }
        with pytest.raises(DataError):
            parseRecord(malformedJSON, 'outManager')

    def test_parseRecord_missingBody(self):
        missingBodyRecord = {
            'record': '{"data": "data"}'
        }
        with pytest.raises(DataError):
            parseRecord(missingBodyRecord, 'outManager')
