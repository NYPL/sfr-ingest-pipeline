import unittest
from unittest.mock import patch, MagicMock, call, DEFAULT
from collections import namedtuple

from sqlalchemy.orm.exc import NoResultFound

from sfrCore.model.item import Item, AgentItems, AccessReport

from sfrCore.helpers import DataError, DBError

class ItemTest(unittest.TestCase):

    def test_create_item(self):
        testItem = Item()
        testItem.source = 'Testing'
        testItem.instance_id = '1'

        self.assertEqual(str(testItem), '<Item(source=Testing, instance=None)>')
    
    def test_create_tmp(self):
        itemData = {
            'links': ['link1', 'link2'],
            'identifiers': ['id1', 'id2', 'id3']
        }
        testItem = Item()
        testItem.createTmpRelations(itemData)
        self.assertEqual(testItem.tmp_identifiers[1], 'id2')
        self.assertEqual(len(testItem.tmp_links), 2)
        self.assertEqual(testItem.links, set())
    
    def test_remove_tmp(self):
        testItem = Item()
        testItem.createTmpRelations({})
        testItem.tmp_links = ['link1', 'link2']
        testItem.removeTmpRelations()
        with self.assertRaises(AttributeError):
            tmpLinks = testItem.tmp_links
    
    @patch.object(Item, 'createLocalEpub')
    @patch.object(Item, 'updateOrInsert')
    def test_create_store_create(self, mock_upsert, mock_create):
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
        record = Item.createOrStore(mock_session, testItem, mock_inst)
        self.assertEqual(record, None)
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_create.assert_called_once()
        mock_upsert.assert_not_called()

    
    @patch.object(Item, 'updateOrInsert', return_value='test_item')
    def test_create_store_store(self, mock_create):
        testItem = {
            'source': 'testing',
            'links': [
                {
                    'url': 'other.org/records/1'
                }
            ]
        }
        mock_inst = MagicMock()
        record = Item.createOrStore('session', testItem, mock_inst)
        self.assertEqual(record, 'test_item')
    
    @patch.object(Item, 'updateOrInsert', return_value='test_item')
    def test_create_store_no_url(self, mock_create):
        testItem = {
            'source': 'testing',
            'links': [
                {
                    'url': None
                }
            ]
        }
        mock_inst = MagicMock()
        record = Item.createOrStore('session', testItem, mock_inst)
        self.assertEqual(record, 'test_item')

    
    def test_create_epub(self):
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
        testPayload = Item.createLocalEpub(testItem, testLink, 1)
        self.assertEqual(testPayload['url'], 'test_link')
        self.assertEqual(testPayload['id'], 1)
    
    @patch.object(Item, 'lookup', return_value=None)
    @patch.object(Item, 'createItem', return_value='newItem')
    def test_updateInsert_insert(self, mock_create, mock_lookup):
        testData = {'identifiers': []}
        newItem = Item.updateOrInsert('session', testData)
        self.assertEqual(newItem, 'newItem')
    
    @patch.object(Item, 'lookup', return_value=1)
    @patch.object(Item, 'update')
    def test_updateInsert_update(self, mock_update, mock_lookup):
        testData = {'identifiers': []}
        mock_item = MagicMock()
        mock_item.name = 'existingItem'
        mock_session = MagicMock()
        mock_session.query().get.return_value = mock_item
        existingItem = Item.updateOrInsert(mock_session, testData)
        self.assertEqual(existingItem.name, 'existingItem')
    
    @patch.object(Item, 'createTmpRelations')
    @patch.object(Item, 'insertData')
    @patch.object(Item, 'removeTmpRelations')
    def test_item_createItem(self, mock_rm, mock_insert, mock_tmp):
        newItem = Item.createItem('session', {})
        self.assertIsInstance(newItem, Item)
    
    @patch('sfrCore.model.item.Identifier.getByIdentifier', return_value=True)
    def test_item_lookup(self, mock_get):
        self.assertTrue(Item.lookup('session', ['id1']))
    
    def test_item_insertData(self):
        testData = {
            'source': 'testing'
        }
        testItem = Item()
        with patch.multiple(Item,
            addIdentifiers=DEFAULT,
            addAgents=DEFAULT,
            addMeasurements=DEFAULT,
            addLinks=DEFAULT,
            addDates=DEFAULT,
            addRights=DEFAULT
        ) as item_mocks:
            testItem.insertData(testData)
            self.assertEqual(testItem.source, 'testing')
    
    def test_item_update(self):
        testData = {
            'source': 'newSource'
        }
        testItem = Item()
        testItem.source = 'oldSource'
        with patch.multiple(Item,
            createTmpRelations=DEFAULT,
            updateIdentifiers=DEFAULT,
            updateAgents=DEFAULT,
            updateMeasurements=DEFAULT,
            updateLinks=DEFAULT,
            updateDates=DEFAULT,
            updateRights=DEFAULT,
            removeTmpRelations=DEFAULT
        ) as item_mocks:
            testItem.update('session', testData)
            self.assertEqual(testItem.source, 'newSource')

    @patch('sfrCore.model.item.Identifier')
    def test_add_identifiers(self, mock_identifier):
        testItem = Item()
        testItem.tmp_identifiers = ['id1', 'id2']

        mock_identifier.returnOrInsert.side_effect = [
            MagicMock(), MagicMock()
        ]

        testItem.addIdentifiers()
        self.assertEqual(len(testItem.identifiers), 2)
    
    @patch.object(Item, 'addAgent')
    def test_add_agents(self, mock_add):
        testItem = Item()
        testItem.tmp_agents = ['agent1', 'agent2']
        testItem.addAgents()
        mock_add.assert_has_calls([call('agent1'), call('agent2')])

    @patch('sfrCore.model.item.Agent')
    @patch('sfrCore.model.item.AgentItems')
    def test_add_agent(self, mock_agent_items, mock_agent):
        testItem = Item()
        mock_name = MagicMock()
        mock_name.name = 'test_agent'
        mock_agent.updateOrInsert.return_value = (mock_name, ['tester'])
        testItem.addAgent('agent1')
        mock_agent_items.assert_has_calls([
            call(agent=mock_name, item=testItem, role='tester'),
        ])
    
    
    @patch('sfrCore.model.item.Measurement')
    def test_add_measurement(self, mock_meas):
        testItem = Item()
        testItem.tmp_measurements = ['measure1']
        mock_value = MagicMock()
        mock_value.name = 'test_measure'
        mock_meas.insert.return_value = mock_value

        testItem.addMeasurements()
        self.assertEqual(list(testItem.measurements)[0].name, 'test_measure')
    
    @patch('sfrCore.model.item.Link')
    def test_add_link(self, mock_link):
        testItem = Item()
        testItem.tmp_links = [{'link': 'test_link'}]
        mock_val = MagicMock()
        mock_val.name = 'test_link'

        mock_link.return_value = mock_val

        testItem.addLinks()
        self.assertEqual(list(testItem.links)[0].name, 'test_link')
    
    @patch('sfrCore.model.item.DateField')
    def test_add_date(self, mock_date):
        testItem = Item()
        testItem.tmp_dates = ['1999']
        mock_val = MagicMock()
        mock_val.name = 'test_date'
        mock_date.insert.return_value = mock_val

        testItem.addDates()
        self.assertEqual(list(testItem.dates)[0].name, 'test_date')
    
    @patch('sfrCore.model.item.Rights')
    def test_add_rights(self, mock_rights):
        testItem = Item()
        testItem.tmp_rights = [{
            'rights': 'rights1',
            'dates': ['rd1']
        }]
        mock_val = MagicMock()
        mock_val.name = 'test_rights'
        mock_rights.insert.return_value = mock_val
        testItem.addRights()
        self.assertEqual(list(testItem.rights)[0].name, 'test_rights')
    
    @patch('sfrCore.model.item.Identifier')
    @patch.object(Item, 'buildReport', return_value='newReport')
    def test_add_access_report(self, mock_build, mock_iden):
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
        mock_item.access_reports = set()
        mock_session.query().get.return_value=mock_item
        Item.addReportData(mock_session, testReport)
        self.assertEqual(list(mock_item.access_reports)[0], 'newReport')

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