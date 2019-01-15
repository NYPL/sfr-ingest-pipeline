import unittest
import os
from unittest.mock import patch, MagicMock
from elasticsearch.exceptions import ConnectionError

os.environ['ES_INDEX'] = 'test'

from lib.esManager import ESConnection
from helpers.errorHelpers import ESError

class TestESManager(unittest.TestCase):
    @patch('lib.esManager.ESConnection.createElasticConnection')
    @patch('lib.esManager.ESConnection.createIndex')
    def test_class_create(self, mock_index, mock_connection):
        inst = ESConnection()
        self.assertIsInstance(inst, ESConnection)
        self.assertEqual(inst.index, 'test')
    
    @patch.dict('os.environ', {'ES_HOST': 'test', 'ES_PORT': '9200', 'ES_TIMEOUT': '60'})
    @patch('lib.esManager.Elasticsearch', return_value='default')
    @patch('lib.esManager.ESConnection')
    @patch('lib.esManager.ESConnection.createIndex')
    def test_connection_create(self, mock_index, mock_instance, mock_elastic):
        inst = ESConnection()
        self.assertEqual(inst.client, 'default')
    
    client_mock = MagicMock(name='test_client')
    client_mock.indices.exists.return_value = False

    @patch.dict('os.environ', {'ES_HOST': 'test', 'ES_PORT': '9200', 'ES_TIMEOUT': '60'})
    @patch('lib.esManager.Elasticsearch', side_effect=ConnectionError)
    @patch('lib.esManager.ESConnection')
    @patch('lib.esManager.ESConnection.createIndex')
    def test_connection_err(self, mock_index, mock_instance, mock_elastic):
        with self.assertRaises(ESError):
            inst = ESConnection()
        
    @patch.dict('os.environ', {'ES_HOST': 'test', 'ES_PORT': '9200', 'ES_TIMEOUT': '60'})
    @patch('lib.esManager.Work')
    @patch('lib.esManager.ESConnection')
    @patch('lib.esManager.Elasticsearch', return_value=client_mock)
    def test_index_create(self, mock_elastic, mock_instance, mock_work):
        
        inst = ESConnection()
        self.assertIsInstance(inst.client, MagicMock)
        mock_work.init.assert_called_once()
    
    client_mock = MagicMock(name='test_client')
    client_mock.indices.exists.return_value = True

    @patch.dict('os.environ', {'ES_HOST': 'test', 'ES_PORT': '9200', 'ES_TIMEOUT': '60'})
    @patch('lib.esManager.Work')
    @patch('lib.esManager.ESConnection')
    @patch('lib.esManager.Elasticsearch', return_value=client_mock)
    def test_index_exists(self, mock_elastic, mock_instance, mock_work):
        
        inst = ESConnection()
        self.assertIsInstance(inst.client, MagicMock)
        mock_work.init.assert_not_called()