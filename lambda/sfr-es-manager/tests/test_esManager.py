import unittest
import os
import pytest
from unittest.mock import patch, MagicMock, call
from elasticsearch.exceptions import ConnectionError, TransportError, ConflictError
from elasticsearch.helpers import BulkIndexError
from elasticsearch_dsl import DateRange

from helpers.errorHelpers import ESError

os.environ['ES_INDEX'] = 'test'

from lib.esManager import ESConnection, ESDoc
from helpers.errorHelpers import ESError

@patch.dict('os.environ', {'ES_HOST': 'test', 'ES_PORT': '9200', 'ES_TIMEOUT': '60'})
class TestESManager:
    @patch('lib.esManager.ESConnection.createElasticConnection')
    @patch('lib.esManager.ESConnection.createIndex')
    def test_class_create(self, mock_index, mock_connection):
        inst = ESConnection()
        assert isinstance(inst, ESConnection)
        assert inst.index == 'test'
    
    @patch('lib.esManager.Elasticsearch', return_value='default')
    @patch('lib.esManager.ESConnection')
    @patch('lib.esManager.ESConnection.createIndex')
    def test_connection_create(self, mock_index, mock_instance, mock_elastic):
        inst = ESConnection()
        assert inst.client == 'default'
    
    client_mock = MagicMock(name='test_client')
    client_mock.indices.exists.return_value = False

    @patch('lib.esManager.Elasticsearch', side_effect=ConnectionError)
    @patch('lib.esManager.ESConnection')
    @patch('lib.esManager.ESConnection.createIndex')
    def test_connection_err(self, mock_index, mock_instance, mock_elastic):
        with pytest.raises(ESError):
            inst = ESConnection()
        
    @patch('lib.esManager.Work')
    @patch('lib.esManager.ESConnection')
    @patch('lib.esManager.Elasticsearch', return_value=client_mock)
    def test_index_create(self, mock_elastic, mock_instance, mock_work):
        
        inst = ESConnection()
        assert isinstance(inst.client, MagicMock)
        mock_work.init.assert_called_once()
    
    client_mock = MagicMock(name='test_client')
    client_mock.indices.exists.return_value = True

    @patch('lib.esManager.Work')
    @patch('lib.esManager.ESConnection')
    @patch('lib.esManager.Elasticsearch', return_value=client_mock)
    def test_index_exists(self, mock_elastic, mock_instance, mock_work):
        
        inst = ESConnection()
        assert isinstance(inst.client, MagicMock)
        mock_work.init.assert_not_called()
    
    @patch('lib.esManager.streaming_bulk', return_value=iter([(True, 1)]))
    @patch('lib.esManager.ESConnection.process', side_effect=[1])
    @patch('lib.esManager.Elasticsearch', return_value=client_mock)
    def test_generate_success(self, mock_elastic, mock_process, mock_stream):
        inst = ESConnection()
        inst.generateRecords('session')
        mock_stream.assert_has_calls([call(TestESManager.client_mock, 1)])
    
    @patch('lib.esManager.streaming_bulk', return_value=iter([(False, 1)]))
    @patch('lib.esManager.ESConnection.process', side_effect=[1])
    @patch('lib.esManager.Elasticsearch', return_value=client_mock)
    def test_generate_failure(self, mock_elastic, mock_process, mock_stream):
        inst = ESConnection()
        inst.generateRecords('session')
        mock_stream.assert_has_calls([call(TestESManager.client_mock, 1)])
    
    @patch('lib.esManager.streaming_bulk', side_effect=BulkIndexError)
    @patch('lib.esManager.ESConnection.process', side_effect=[1])
    @patch('lib.esManager.Elasticsearch', return_value=client_mock)
    def test_generate_error(self, mock_elastic, mock_process, mock_stream):
        inst = ESConnection()
        with pytest.raises(ESError):
            inst.generateRecords('session')

    @patch('lib.esManager.retrieveRecords')
    @patch('lib.esManager.ESDoc.indexWork')
    @patch('lib.esManager.Elasticsearch', return_value=client_mock)
    def test_process(self, mock_elastic, mock_index, mock_retrieve):
        mock_retrieve.return_value = ['work1', 'work2', 'work3']
        with patch('lib.esManager.ESDoc.createWork') as mock_create:
            mock_dict = MagicMock()
            mock_dict.to_dict.side_effect = ['work1', 'work2', 'work3']
            mock_create.return_value = mock_dict
            inst = ESConnection()
            res = list(inst.process('session'))
            assert res == ['work1', 'work2', 'work3']
    
    @patch('lib.esManager.ESDoc.createWork', return_value='testWork')
    def test_init_esdoc(self, mock_create):
        newDoc = ESDoc(('work1',), 'session')
        assert newDoc.workID == 'work1'
        assert newDoc.session == 'session'
        assert newDoc.dbRec == None
        assert newDoc.work == 'testWork'
    
    @patch('lib.esManager.Work', return_value={'title': 'test', 'uuid': '000'})
    def test_create_es_work(self, mock_work):
        mock_session = MagicMock()
        mock_session.query.return_value.get.return_value = TestDict(uuid=0)
        testDoc = ESDoc(('1',), mock_session)
        newWork = testDoc.createWork()
        assert testDoc.dbRec.uuid == 0
        assert newWork == {'title': 'test', 'uuid': '000'}

    def test_add_identifier(self):
        testID = TestDict(**{
            'type': None,
            'generic': [
                TestDict(**{
                    'value': 'hello'
                })
            ]
        })

        idRec = ESDoc.addIdentifier(testID)
        assert idRec.id_type == 'generic'
        assert idRec.identifier == 'hello'
    
    def test_add_link(self):
        testLink = TestDict(**{
            'url': 'test/url',
            'media_type': 'test',
            'flags': '{\"local\": false}',
            'id': 1
        })

        linkRec = ESDoc.addLink(testLink)
        assert linkRec.url ==  'test/url'
        assert linkRec.media_type == 'test'
        assert linkRec.local == False
    
    def test_add_measure(self):
        testMeasure = TestDict(**{
            'quantity': 'test',
            'value': 1,
        })

        measureRec = ESDoc.addMeasurement(testMeasure)
        assert measureRec.quantity == 'test'
        assert measureRec.value == 1
    
    def test_add_language(self):
        testLang = TestDict(**{
            'language': 'test',
            'iso_2': 'te',
            'iso_3': 'tes'
        })

        langRec = ESDoc.addLanguage(testLang)
        assert langRec.language == 'test'
        assert langRec.iso_3 == 'tes'
    
    def test_add_cover_json_string(self):
        testCover = TestDict(**{
            'url': 'testURL',
            'media_type': 'image/test',
            'flags': '{"cover": true}'
        })

        coverRec = ESDoc.addCover(testCover)
        assert coverRec.url == 'testURL'
        assert coverRec.media_type == 'image/test'

    def test_add_cover_json_object(self):
        testCover = TestDict(**{
            'url': 'testURL',
            'media_type': 'image/test',
            'flags': {'cover': True}
        })

        coverRec = ESDoc.addCover(testCover)
        assert coverRec.url == 'testURL'
        assert coverRec.media_type == 'image/test'

    def test_add_cover_other_link(self):
        testCover = TestDict(**{
            'url': 'testURL',
            'media_type': 'image/test',
            'flags': {'cover': False}
        })

        coverRec = ESDoc.addCover(testCover)
        assert coverRec is None
    
    def test_insert_instance_w_pub_date(self):
        testInstance = MagicMock()
        testDate = MagicMock()
        testDate.lower = '2019-01-01'
        testDate.upper = '2019-12-31'
        dateObj = MagicMock()
        dateObj.date_type = 'pub_date'
        dateObj.display_date = '2019'
        dateObj.date_range = testDate
        testInstance.title = 'Test Title'
        testInstance.dates = [dateObj]
        newInstance = ESDoc.addInstance(testInstance)

        assert newInstance.title == 'Test Title'
        assert newInstance.pub_date_sort == '2019-01-01'
        assert newInstance.pub_date_sort_desc == '2019-12-31'


class TestDict(dict):

    def __init__(self, *args, **kwargs):
        super(TestDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
        self.fields = kwargs.keys()
    
    def __dir__(self):
        return self.fields
    
    def to_dict(self, bool):
        return vars(self)