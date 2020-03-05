import pytest
import os
from unittest.mock import patch, MagicMock, call
from elasticsearch.exceptions import ConnectionError, TransportError, ConflictError
from elasticsearch.helpers import BulkIndexError
from elasticsearch_dsl import DateRange

from helpers.errorHelpers import ESError

from lib.esManager import ESConnection, Work

class TestESConnection(object):
    @pytest.fixture
    def testManager(self, mocker):
        mocker.patch.dict(
            'os.environ',
            {
                'ES_HOST': 'test',
                'ES_PORT': '9200',
                'ES_TIMEOUT': '60',
                'ES_INDEX': 'test'
            }
        )
        mockCreate = patch.object(ESConnection, 'createElasticConnection')
        mockIndex = patch.object(ESConnection, 'createIndex')

        mockCreate.start()
        mockIndex.start()
        testES = ESConnection()
        mockCreate.stop()
        mockIndex.stop()

        return testES
    
    @pytest.fixture
    def mockClient(self, testManager):
        testManager.client = MagicMock(name='test_client')

    def test_class_create(self, testManager):
        assert isinstance(testManager, ESConnection)
        assert testManager.index == 'test'
    
    def test_connection_create(self, mocker, testManager):
        mockElastic = mocker.patch('lib.esManager.Elasticsearch')
        mockElastic.return_value = 'default'

        testManager.createElasticConnection()

        assert testManager.client == 'default'
    
    def test_connection_err(self, mocker, testManager):
        mockElastic = mocker.patch('lib.esManager.Elasticsearch')
        mockElastic.side_effect = ConnectionError

        with pytest.raises(ESError):
            testManager.createElasticConnection()

    def test_index_create(self, mocker, testManager, mockClient):
        mockInit = mocker.patch.object(Work, 'init')
        testManager.client.indices.exists.return_value = False

        testManager.createIndex()

        mockInit.assert_called_once()

    def test_index_existing(self, mocker, testManager, mockClient):
        mockInit = mocker.patch.object(Work, 'init')
        testManager.client.indices.exists.return_value = True
        
        testManager.createIndex()

        mockInit.assert_not_called()
