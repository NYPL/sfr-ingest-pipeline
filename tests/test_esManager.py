import unittest
import os
from unittest.mock import patch, MagicMock
from elasticsearch.exceptions import ConnectionError, TransportError, ConflictError
from elasticsearch.helpers import BulkIndexError

from helpers.errorHelpers import ESError

os.environ['ES_INDEX'] = 'test'

from lib.esManager import ESConnection
from helpers.errorHelpers import ESError

@patch.dict('os.environ', {'ES_HOST': 'test', 'ES_PORT': '9200', 'ES_TIMEOUT': '60'})
class TestESManager(unittest.TestCase):
    @patch('lib.esManager.ESConnection.createElasticConnection')
    @patch('lib.esManager.ESConnection.createIndex')
    def test_class_create(self, mock_index, mock_connection):
        inst = ESConnection()
        self.assertIsInstance(inst, ESConnection)
        self.assertEqual(inst.index, 'test')
    
    @patch('lib.esManager.Elasticsearch', return_value='default')
    @patch('lib.esManager.ESConnection')
    @patch('lib.esManager.ESConnection.createIndex')
    def test_connection_create(self, mock_index, mock_instance, mock_elastic):
        inst = ESConnection()
        self.assertEqual(inst.client, 'default')
    
    client_mock = MagicMock(name='test_client')
    client_mock.indices.exists.return_value = False

    @patch('lib.esManager.Elasticsearch', side_effect=ConnectionError)
    @patch('lib.esManager.ESConnection')
    @patch('lib.esManager.ESConnection.createIndex')
    def test_connection_err(self, mock_index, mock_instance, mock_elastic):
        with self.assertRaises(ESError):
            inst = ESConnection()
        
    @patch('lib.esManager.Work')
    @patch('lib.esManager.ESConnection')
    @patch('lib.esManager.Elasticsearch', return_value=client_mock)
    def test_index_create(self, mock_elastic, mock_instance, mock_work):
        
        inst = ESConnection()
        self.assertIsInstance(inst.client, MagicMock)
        mock_work.init.assert_called_once()
    
    client_mock = MagicMock(name='test_client')
    client_mock.indices.exists.return_value = True

    @patch('lib.esManager.Work')
    @patch('lib.esManager.ESConnection')
    @patch('lib.esManager.Elasticsearch', return_value=client_mock)
    def test_index_exists(self, mock_elastic, mock_instance, mock_work):
        
        inst = ESConnection()
        self.assertIsInstance(inst.client, MagicMock)
        mock_work.init.assert_not_called()
    
    @patch('lib.esManager.bulk')
    @patch('lib.esManager.ESConnection')
    @patch('lib.esManager.Elasticsearch', return_value=client_mock)
    def test_process_batch(self, mock_elastic, mock_instance, mock_bulk):

        inst = ESConnection()
        inst.batch = [{'test': 'test'}]
        inst.processBatch()
        mock_bulk.assert_called_once()
    
    @patch('lib.esManager.bulk', side_effect=BulkIndexError)
    @patch('lib.esManager.ESConnection')
    @patch('lib.esManager.Elasticsearch', return_value=client_mock)
    def test_batch_err(self, mock_elastic, mock_instance, mock_bulk):

        inst = ESConnection()
        inst.batch = [{'test': 'test'}]
        with self.assertRaises(ESError):
            inst.processBatch()
    
    @patch('lib.esManager.ESConnection')
    @patch('lib.esManager.Work')
    @patch('lib.esManager.Elasticsearch', return_value=client_mock)
    def test_record_index(self, mock_instance, mock_work, mock_elastic):
        inst = ESConnection()
        mock_work.title = 'Text Record'
        mock_work.uuid = '000000-0000-0000-0000-000000000000'

        mock_work.loadDates.return_value = {'test': '2019-01-01'}

        inst.indexRecord(mock_work)
        self.assertEqual(len(inst.batch), 1)
        self.assertEqual(inst.work.title, 'Text Record')
    
    @patch('lib.esManager.ESConnection')
    @patch('lib.esManager.Elasticsearch', return_value=client_mock)
    def test_add_identifier(self, mock_instance, mock_elastic):
        inst = ESConnection()
        testID = TestDict(**{
            'type': None,
            'generic': [
                TestDict(**{
                    'value': 'hello'
                })
            ]
        })

        idRec = inst.addIdentifier(testID)
        self.assertEqual(idRec.id_type, 'generic')
        self.assertEqual(idRec.identifier, 'hello')
    
    @patch('lib.esManager.ESConnection')
    @patch('lib.esManager.Elasticsearch', return_value=client_mock)
    def test_add_link(self, mock_instance, mock_elastic):
        inst = ESConnection()
        testLink = TestDict(**{
            'url': 'test/url',
            'media_type': 'test',
            'md5': 'hash_value'
        })

        linkRec = inst.addLink(testLink)
        self.assertEqual(linkRec.url, 'test/url')
        self.assertEqual(linkRec.media_type, 'test')
        self.assertEqual(linkRec.md5, 'hash_value')
        self.assertEqual(linkRec.rel_type, None)
    
    @patch('lib.esManager.ESConnection')
    @patch('lib.esManager.Elasticsearch', return_value=client_mock)
    def test_add_measure(self, mock_instance, mock_elastic):
        inst = ESConnection()
        testMeasure = TestDict(**{
            'quantity': 'test',
            'value': 1,
        })

        measureRec = inst.addMeasurement(testMeasure)
        self.assertEqual(measureRec.quantity, 'test')
        self.assertEqual(measureRec.value, 1)
    
    @patch('lib.esManager.ESConnection')
    @patch('lib.esManager.Elasticsearch', return_value=client_mock)
    def test_add_language(self, mock_instance, mock_elastic):
        inst = ESConnection()
        testLang = TestDict(**{
            'language': 'test',
            'iso_2': 'te',
            'iso_3': 'tes'
        })

        langRec = inst.addLanguage(testLang)
        self.assertEqual(langRec.language, 'test')
        self.assertEqual(langRec.iso_3, 'tes')


class TestDict(dict):

    def __init__(self, *args, **kwargs):
        super(TestDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
        self.fields = kwargs.keys()
    
    def __dir__(self):
        return self.fields