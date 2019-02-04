import unittest
import os
from unittest.mock import patch, MagicMock
from elasticsearch.exceptions import ConnectionError, TransportError, ConflictError

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
    
    @patch.dict('os.environ', {'ES_HOST': 'test', 'ES_PORT': '9200', 'ES_TIMEOUT': '60'})
    @patch('lib.esManager.Work')
    @patch('lib.esManager.Elasticsearch', return_value=client_mock)
    def test_index_new_record(self, mock_client, mock_work):
        inst = ESConnection()
        testRec = MagicMock(
            uuid='test_uuid',
            title='Test Title',
            sort_title='Test Title',
            sub_title='A Test',
            language='en',
            medium='test_medium',
            series='Test Series',
            series_position='1 of 3',
            date_modified='2019-02-01',
            date_created='2019-01-01',
            instances=[],
            identifiers=[],
            agents=[],
            alt_titles=[
                MagicMock(
                    title='Alternate Title'
                )
            ],
            subjects=[
                MagicMock(
                    authority='test_auth',
                    uri='subject_uri',
                    subject='test_subject'
                )
            ],
            measurements=[
                MagicMock(
                    quantity='test',
                    value=1,
                    weight=1,
                    taken_at='now'
                )
            ],
            links=[],
            dates=['test_date'],
            rights=[]
        )
        
        mock_work.get.side_effect = TransportError
        
        testRec.loadDates.return_value = {
            'test_date': {
                'range': MagicMock(
                    lower='2018-01-01',
                    upper='2019-01-01'
                ),
                'display': '2018'
            },
            'other_date': {
                'range': None,
                'display': '2017'
            }
        }


        inst.indexRecord(testRec)
        
        self.assertEqual(inst.work.uuid, 'test_uuid')
        self.assertEqual(inst.work.test_date_display, '2018')
        self.assertEqual(inst.work.alt_titles[0], 'Alternate Title')
        self.assertEqual(inst.work.subjects[0].subject, 'test_subject')
        self.assertEqual(inst.work.measurements[0].quantity, 'test')

    @patch.dict('os.environ', {'ES_HOST': 'test', 'ES_PORT': '9200', 'ES_TIMEOUT': '60'})
    @patch('lib.esManager.Work')
    @patch('lib.esManager.Elasticsearch', return_value=client_mock)
    def test_index_existing_record(self, mock_client, mock_work):
        inst = ESConnection()
        testRec = MagicMock(
            uuid='test_uuid',
            title='Test Title'
        )

        existingRec = MagicMock(
            uuid='old_uuid',
            title='Existing Title'
        )
        
        mock_work.get.return_value = existingRec

        inst.indexRecord(testRec)
        
        self.assertEqual(inst.work.uuid, 'test_uuid')
        self.assertEqual(inst.work.title, 'Test Title')
    
    @patch.dict('os.environ', {'ES_HOST': 'test', 'ES_PORT': '9200', 'ES_TIMEOUT': '60'})
    @patch('lib.esManager.Work')
    @patch('lib.esManager.Elasticsearch', return_value=client_mock)
    def test_index_retry(self, mock_client, mock_work):
        inst = ESConnection()
        testRec = MagicMock(
            uuid='test_uuid',
            title='Test Title'
        )
        
        mock_work.get.side_effect = TransportError

        testRec.save.side_effect = [ConflictError, True]
        with patch('lib.esManager.time.sleep'):
            inst.indexRecord(testRec)
        
        self.assertEqual(inst.work.uuid, 'test_uuid')
        self.assertEqual(inst.work.title, 'Test Title')
        self.assertEqual(inst.tries, 1)
    
    @patch.dict('os.environ', {'ES_HOST': 'test', 'ES_PORT': '9200', 'ES_TIMEOUT': '60'})
    @patch('lib.esManager.Work')
    @patch('lib.esManager.Elasticsearch', return_value=client_mock)
    def test_index_failure(self, mock_client, mock_work):
        inst = ESConnection()
        testRec = MagicMock(
            uuid='test_uuid',
            title='Test Title'
        )
        
        mock_work.get.side_effect = TransportError

        testRec.save.side_effect = ConflictError
        with patch('lib.esManager.time.sleep'):
            inst.indexRecord(testRec)
        
        self.assertEqual(inst.tries, 3)
    
    def test_add_identifier(self):
        testRec = MagicMock(identifiers=[])
        testID = MagicMock(
            type='test',
            test=[
                MagicMock(
                    value='1.1.1'
                )
            ]
        )
        ESConnection.addIdentifier(testRec, testID)
        self.assertEqual(testRec.identifiers[0].identifier, '1.1.1')
    
    def test_generic_identifier(self):
        testRec = MagicMock(identifiers=[])
        testID = MagicMock(
            type=None,
            test=[
                MagicMock(
                    value='1.1.1'
                )
            ]
        )
        ESConnection.addIdentifier(testRec, testID)
        self.assertEqual(testRec.identifiers[0].id_type, 'generic')
    
    def test_add_link(self):
        testRec = MagicMock(links=[])
        testLink = MagicMock(
            url='test_url',
            media_type='test/test',
            rel_type='test',
            thumbnail=None
        )
        ESConnection.addLink(testRec, testLink)
        self.assertEqual(testRec.links[0].url, 'test_url')
    
    def test_add_measurement(self):
        testRec = MagicMock(measurements=[])
        testMeasure = MagicMock(
            quantity='test',
            value=1,
            weight=1,
            taken_at='2019-01-01'
        )
        ESConnection.addMeasurement(testRec, testMeasure)
        self.assertEqual(testRec.measurements[0].value, 1)
    
    def test_add_single_agent(self):
        testRec = MagicMock(agents=[])
        testAgent = MagicMock(
            agent=MagicMock(
                sort_name='Tester, Test',
                lcnaf='lcnaf',
                viaf='viaf',
                biography='biography',
                aliases=[
                    MagicMock(
                        alias='Test Guy'
                    )
                ]
            ),
            role='tester'
        )
        testAgent.agent.name = 'Tester, Test'

        testAgent.agent.loadDates.return_value = {
            'test_date': {
                'range': MagicMock(
                    lower='2018-01-01',
                    upper='2019-01-01'
                ),
                'display': '2018'
            },
            'other_date': {
                'range': None,
                'display': '2017'
            }
        }

        ESConnection.addAgent(testRec, testAgent)
        self.assertEqual(testRec.agents[0].name, 'Tester, Test')
        self.assertEqual(testRec.agents[0].aliases[0], 'Test Guy')
        self.assertEqual(testRec.agents[0].test_date_display, '2018')
    
    def test_add_matching_agents(self):
        existingAgent = MagicMock(
            sort_name='Tester, Test',
            lcnaf='lcnaf',
            viaf='viaf',
            biography='biography',
            roles=['existing']
        )
        existingAgent.name='Tester, Test'

        testRec = MagicMock(agents=[existingAgent])
        testAgent = MagicMock(
            agent=MagicMock(
                sort_name='Tester, Test',
                lcnaf='lcnaf',
                viaf='viaf',
                biography='biography'
            ),
            role='tester'
        )
        testAgent.agent.name='Tester, Test'

        ESConnection.addAgent(testRec, testAgent)
        self.assertEqual(testRec.agents[0].roles, ['existing', 'tester'])
    
    def test_add_rights(self):
        testRec = MagicMock(rights=[])
        testRights = MagicMock(
            source='test',
            license='test_uri',
            rights_statement='test_statement',
            rights_reason='test_reason'
        )
        ESConnection.addRights(testRec, testRights)
        self.assertEqual(testRec.rights[0].license, 'test_uri')
    
    def test_add_instance(self):
        testRec = MagicMock(instances=[])
        testInstance = MagicMock(
            title='A Title',
            sub_title='For a Book',
            pub_place='New York',
            edition='1st Ed',
            edition_statement='1st Edition Hardcover',
            table_of_contents='1. Nothing',
            language='en',
            extent='400pp'
        )
        ESConnection.addInstance(testRec, testInstance)
        self.assertEqual(testRec.instances[0].extent, '400pp')
    
    def test_add_item(self):
        testRec = MagicMock(items=[])
        testItem = MagicMock(
            source='test',
            content_type='ebook',
            drm=None
        )
        ESConnection.addItem(testRec, testItem)
        self.assertEqual(testRec.items[0].content_type, 'ebook')

    def test_add_report(self):
        testRec = MagicMock(access_reports=[])
        testReport = MagicMock(
            ace_version='1',
            score=4.5,
            report_json='JSON String'
        )
        ESConnection.addReport(testRec, testReport)
        self.assertEqual(testRec.access_reports[0].score, 4.5)
