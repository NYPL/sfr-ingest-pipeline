import json
import pytest
from unittest.mock import MagicMock, patch, DEFAULT

from sfrCore import SessionManager

from helpers.errorHelpers import NoRecordsReceived, DataError


class TestHandler(object):
    @pytest.fixture
    def mockManager(self, mocker):
        mocker.patch.multiple(SessionManager,
            generateEngine=DEFAULT,
            createSession=DEFAULT,
            closeConnection=DEFAULT,
            startSession=DEFAULT,
            commitChanges=DEFAULT
        )
        from service import handler, parseRecords, parseRecord, MANAGER
        MANAGER.session = MagicMock()
        return (handler, parseRecords, parseRecord)

    def test_handler_clean(self, mocker, mockManager):
        mockParser = mocker.patch('service.parseRecords')
        mockParser.return_value = 'Hello, World'
        testRec = {
            'source': 'Kinesis',
            'Records': [
                {
                    'kinesis': {
                        'data': 'data'
                    }
                }
            ]
        }
        res = mockManager[0](testRec, None)
        assert res == 'Hello, World'
        mockParser.assert_called_once()

    def test_handler_error(self, mockManager):
        testRec = {
            'source': 'Kinesis',
            'Records': []
        }
        with pytest.raises(NoRecordsReceived):
            mockManager[0](testRec, None)

    def test_records_none(self, mockManager):
        testRec = {
            'source': 'Kinesis'
        }
        with pytest.raises(NoRecordsReceived):
            mockManager[0](testRec, None)
    
    def test_parseRecords(self, mocker, mockManager):
        mockParse = mocker.patch('service.parseRecord')
        mockES = mocker.patch('service.ESConnection')
        mockParse.side_effect = ['test1', 'test2']
        testRecords = ['test1', 'test2']

        result = mockManager[1](testRecords)

        assert len(result) == 2
        assert result[1] == 'test2'

    def test_parseRecord_success(self, mocker, mockManager):
        mockCluster = mocker.patch('service.ClusterManager')()
        mockElastic = mocker.patch('service.ElasticManager')()
        mockCluster.work = MagicMock()
        mockCluster.work.uuid = 'uuid'
        mockCluster.work.title = 'title'
        testRec = {
            'body': json.dumps({'type': 'test', 'identifier': 'xxxxxxxxx'})
        }
        res = mockManager[2](testRec, 'session')
        assert res == ('success', 'uuid|title')
    
    def test_parseRecord_failure(self, mocker, mockManager):
        mockCluster = mocker.patch('service.ClusterManager')()
        mockCluster.work = MagicMock()
        mockCluster.work.uuid = 'uuid'
        mockCluster.work.title = 'title'
        mockCluster.storeEditions.side_effect = Exception
        res = mockManager[2]({'body': json.dumps({'identifier': 'xxxxxxxxx'})}, 'session')
        assert res == ('failure', 'uuid|title')
    
    def test_parseRecord_json_err(self, mocker, mockManager):
        mockCluster = mocker.patch('service.ClusterManager')()
        with pytest.raises(DataError):
            mockManager[2]({'body': 'randomString'}, 'session')
    
    def test_parseRecord_key_err(self, mocker, mockManager):
        mockCluster = mocker.patch('service.ClusterManager')()
        with pytest.raises(DataError):
            mockManager[2]({'other': 'randomString'}, 'session')