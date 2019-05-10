import unittest
import os
from unittest.mock import patch, MagicMock, call
from elasticsearch.exceptions import ConnectionError, TransportError, ConflictError
from elasticsearch.helpers import BulkIndexError

from helpers.errorHelpers import ESError

os.environ['ES_INDEX'] = 'test'

from lib.esManager import ESConnection, ESDoc
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
        try:
            inst.generateRecords('session')
        except ESError:
            pass
        self.assertRaises(ESError)

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
            self.assertEqual(res, ['work1', 'work2', 'work3'])
    
    @patch('lib.esManager.ESDoc.createWork', return_value='testWork')
    def test_init_esdoc(self, mock_create):
        newDoc = ESDoc(('work1',), 'session')
        self.assertEqual(newDoc.workID, 'work1')
        self.assertEqual(newDoc.session, 'session')
        self.assertEqual(newDoc.dbRec, None)
        self.assertEqual(newDoc.work, 'testWork')
    
    @patch('lib.esManager.Work', return_value={'title': 'test', 'uuid': '000'})
    def test_create_es_work(self, mock_work):
        mock_session = MagicMock()
        mock_session.query.return_value.get.return_value = TestDict(uuid=0)
        testDoc = ESDoc(('1',), mock_session)
        newWork = testDoc.createWork()
        self.assertEqual(testDoc.dbRec.uuid, 0)
        self.assertEqual(newWork, {'title': 'test', 'uuid': '000'})

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
        self.assertEqual(idRec.id_type, 'generic')
        self.assertEqual(idRec.identifier, 'hello')
    
    def test_add_link(self):
        testLink = TestDict(**{
            'url': 'test/url',
            'media_type': 'test',
            'flags': '{\"local\": false}'
        })

        linkRec = ESDoc.addLink(testLink)
        self.assertEqual(linkRec.url, 'test/url')
        self.assertEqual(linkRec.media_type, 'test')
        self.assertEqual(linkRec.local, False)
    
    def test_add_measure(self):
        testMeasure = TestDict(**{
            'quantity': 'test',
            'value': 1,
        })

        measureRec = ESDoc.addMeasurement(testMeasure)
        self.assertEqual(measureRec.quantity, 'test')
        self.assertEqual(measureRec.value, 1)
    
    def test_add_language(self):
        testLang = TestDict(**{
            'language': 'test',
            'iso_2': 'te',
            'iso_3': 'tes'
        })

        langRec = ESDoc.addLanguage(testLang)
        self.assertEqual(langRec.language, 'test')
        self.assertEqual(langRec.iso_3, 'tes')


class TestDict(dict):

    def __init__(self, *args, **kwargs):
        super(TestDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
        self.fields = kwargs.keys()
    
    def __dir__(self):
        return self.fields
    
    def to_dict(self, bool):
        return vars(self)