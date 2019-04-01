import unittest
from unittest.mock import patch, MagicMock, call
from collections import namedtuple

from sqlalchemy.orm.exc import NoResultFound

from model.item import Item, AgentItems, AccessReport

from helpers.errorHelpers import DataError, DBError

class ItemTest(unittest.TestCase):

    def test_create_item(self):
        testItem = Item()
        testItem.source = 'Testing'
        testItem.instance_id = '1'

        self.assertEqual(str(testItem), '<Item(source=Testing, instance=None)>')
    
    def test_child_dict(self):
        itemData = {
            'source': 'Testing',
            'links': ['link1', 'link2'],
            'agents': ['agent1', 'agent2', 'agent3']
        }

        childFields = Item._buildChildDict(itemData)
        self.assertEqual(childFields['links'][1], 'link2')
        self.assertEqual(len(childFields['agents']), 3)
        self.assertEqual(itemData['source'], 'Testing')
        with self.assertRaises(KeyError):
            itemData['links']
    
    @patch('model.item.Item.createLocalEpub')
    def test_create_store_create(self, mock_create):
        testItem = {
            'source': 'testing',
            'links': [
                {
                    'url': 'gutenberg.org/ebooks/1.epub.images'
                },{
                    'url': None
                }
            ]
        }
        mock_inst = MagicMock()
        mock_inst.id = None
        mock_session = MagicMock()
        record, op = Item.createOrStore(mock_session, testItem, mock_inst)
        self.assertEqual(record, None)
        self.assertEqual(op, 'creating')
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @patch('model.item.Item.insert', return_value=('test_item', 'test'))
    def test_create_store_store(self, mock_create):
        testItem = {
            'source': 'testing',
            'links': [
                {
                    'url': 'other.org/records/1'
                }
            ]
        }
        record, op = Item.createOrStore('session', testItem, 1)
        self.assertEqual(record, 'test_item')
        self.assertEqual(op, 'test')
    
    @patch.dict('os.environ', {'EPUB_STREAM': 'test-stream'})
    @patch('model.item.OutputManager')
    def test_create_epub(self, mock_out):
        testItem = {
            'source': 'testing',
            'modified': '2019-01-01',
            'measurements': [{
                'quantity': 'bytes',
                'value': 0
            }]
        }
        testLink = {
            'url': 'test_link'
        }
        Item.createLocalEpub(testItem, testLink, 1)
        mock_out.putKinesis.assert_called_once()
    
    def test_item_insert(self):
        mock_session = MagicMock()
        testData = {
            'source': 'Testing'
        }
        testWork, op = Item.insert(mock_session, testData)
        self.assertEqual(testWork.source, 'Testing')
        
    @patch('model.item.Identifier')
    def test_add_identifiers(self, mock_identifier):
        mock_inst = MagicMock()
        mock_inst.identifiers = []

        mock_identifier.returnOrInsert.side_effect = [
            (0, 'test_identifier'),
            DataError('testing')
        ]

        Item._addIdentifiers('session', mock_inst, ['id1', 'id2'])
        self.assertEqual(len(mock_inst.identifiers), 1)
        self.assertEqual(mock_inst.identifiers[0], 'test_identifier')
    
    @patch('model.item.Agent')
    @patch('model.item.AgentItems')
    def test_add_agents(self, mock_agent_items, mock_agent):
        mock_inst = MagicMock()
        mock_inst.agents = []
        mock_name = MagicMock()
        mock_name.name = 'test_agent'
        mock_agent.updateOrInsert.side_effect = [
            (mock_name, ['tester']),
            (mock_name, ['tester2', 'tester2']),
            DataError('testing')
        ]
        test_agents = [
            {'name': 'ag1'},
            {'name': 'ag3'},
            {'name': 'ag2'}
        ]
        Item._addAgents('session', mock_inst, test_agents)
        mock_agent_items.assert_has_calls([
            call(agent=mock_name, item=mock_inst, role='tester'),
            call(agent=mock_name, item=mock_inst, role='tester2')
        ])
    
    @patch('model.item.Measurement')
    def test_add_measurement(self, mock_meas):
        mock_inst = MagicMock()
        mock_inst.measurements = []

        mock_meas.insert.return_value = ('test_measure')

        Item._addMeasurements('session', mock_inst, ['measure1'])
        self.assertEqual(mock_inst.measurements[0], 'test_measure')
    
    @patch('model.item.Link')
    def test_add_link(self, mock_link):
        mock_inst = MagicMock()
        mock_inst.links = []

        mock_link.return_value = 'test_link'

        Item._addLinks(mock_inst, [MagicMock()])
        self.assertEqual(mock_inst.links[0], 'test_link')
    
    @patch('model.item.DateField')
    def test_add_date(self, mock_date):
        mock_inst = MagicMock()
        mock_inst.dates = []

        mock_date.insert.return_value = 'test_date'

        Item._addDates(mock_inst, ['1999-01-01'])
        self.assertEqual(mock_inst.dates[0], 'test_date')
    
    @patch('model.item.Rights')
    def test_add_rights(self, mock_rights):
        mock_inst = MagicMock()
        mock_inst.rights = []

        mock_rights.insert.return_value = 'test_rights'
        testRights = {
            'rights': 'rights1',
            'dates': ['rd1']
        }
        Item._addRights(mock_inst, [testRights])
        self.assertEqual(mock_inst.rights[0], 'test_rights')
    
    @patch('model.item.Identifier')
    @patch('model.item.Measurement')
    @patch('model.item.AccessReport', return_value=MagicMock())
    def test_add_access_report(self, mock_report, mock_measure, mock_iden):
        testReport = {
            'identifier': 'item_id',
            'instanceID': 'instance_id',
            'violations': {
                'testing': 1
            },
            'aceVersion': 'testing',
            'json': 'json_string',
            'timestamp': 'timestamp'
        }
        mock_iden.getByidentifier.return_value = 1
        mock_session = MagicMock()
        mock_item = MagicMock()
        mock_item.access_reports = []
        mock_session.query().get.return_value=mock_item
        testItem = Item.addReportData(mock_session, testReport)
        self.assertIsInstance(testItem, MagicMock)
        mock_report.assert_called_once()
        mock_measure.assert_called_once()
    
    def test_init_report(self):
        testReport = AccessReport(
            score=1,
            item_id=1
        )
        self.assertEqual(str(testReport), '<AccessReport(score=1, item=None)>')

    def test_role_exists(self):
        mock_session = MagicMock()
        mock_session.query().filter().filter().filter().one_or_none.return_value = 'test_role'
        mock_agent = MagicMock()
        mock_agent.id = 1
        role = AgentItems.roleExists(mock_session, mock_agent, 'role', 1)
        self.assertEqual(role, 'test_role')