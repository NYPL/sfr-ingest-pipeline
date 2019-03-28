import unittest
from unittest.mock import patch, MagicMock, call
from collections import namedtuple

from sqlalchemy.orm.exc import NoResultFound

from model.instance import Instance, AgentInstances

from helpers.errorHelpers import DataError, DBError

class InstanceTest(unittest.TestCase):

    def test_create_instance(self):
        testInst = Instance()
        testInst.title = 'Testing'
        testInst.edition = '1st ed'

        self.assertEqual(str(testInst), '<Instance(title=Testing, edition=1st ed, work=None)>')
    
    def test_child_dict(self):
        instanceData = {
            'title': 'Testing',
            'formats': ['item1', 'item2'],
            'agents': ['agent1', 'agent2', 'agent3']
        }

        childFields = Instance._buildChildDict(instanceData)
        self.assertEqual(childFields['formats'][1], 'item2')
        self.assertEqual(len(childFields['agents']), 3)
        self.assertEqual(instanceData['title'], 'Testing')
        with self.assertRaises(KeyError):
            instanceData['items']
    
    def test_instance_insert(self):
        mock_session = MagicMock()
        testData = {
            'title': 'Testing'
        }
        testWork = Instance.insert(mock_session, testData)
        self.assertEqual(testWork.title, 'Testing')
        
    @patch('model.instance.Identifier')
    def test_add_identifiers(self, mock_identifier):
        mock_inst = MagicMock()
        mock_inst.identifiers = []

        mock_identifier.returnOrInsert.side_effect = [
            (0, 'test_identifier'),
            DataError('testing')
        ]

        Instance._addIdentifiers('session', mock_inst, ['id1', 'id2'])
        self.assertEqual(len(mock_inst.identifiers), 1)
        self.assertEqual(mock_inst.identifiers[0], 'test_identifier')
    
    @patch('model.instance.Agent')
    @patch('model.instance.AgentInstances')
    def test_add_agents(self, mock_agent_instances, mock_agent):
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
        Instance._addAgents('session', mock_inst, test_agents)
        mock_agent_instances.assert_has_calls([
            call(agent=mock_name, instance=mock_inst, role='tester'),
            call(agent=mock_name, instance=mock_inst, role='tester2')
        ])

    @patch('model.instance.AltTitle')
    def test_add_alt_title(self, mock_alt):
        mock_inst = MagicMock()
        mock_inst.alt_titles = []

        mock_alt.return_value = 'test_title'

        Instance._addAltTitles(mock_inst, ['alt1'])
        self.assertEqual(mock_inst.alt_titles[0], 'test_title')
    
    @patch('model.instance.Measurement')
    def test_add_measurement(self, mock_meas):
        mock_inst = MagicMock()
        mock_inst.measurements = []

        mock_meas.insert.return_value = ('test_measure')

        Instance._addMeasurements('session', mock_inst, ['measure1'])
        self.assertEqual(mock_inst.measurements[0], 'test_measure')
    
    @patch('model.instance.Link')
    def test_add_link(self, mock_link):
        mock_inst = MagicMock()
        mock_inst.links = []

        mock_link.return_value = 'test_link'

        Instance._addLinks(mock_inst, [MagicMock()])
        self.assertEqual(mock_inst.links[0], 'test_link')
    
    @patch('model.instance.DateField')
    def test_add_date(self, mock_date):
        mock_inst = MagicMock()
        mock_inst.dates = []

        mock_date.insert.return_value = 'test_date'

        Instance._addDates(mock_inst, ['1999-01-01'])
        self.assertEqual(mock_inst.dates[0], 'test_date')
    
    @patch('model.instance.Language')
    def test_add_languages(self, mock_lang):
        mock_inst = MagicMock()
        mock_inst.language = []

        mock_lang.updateOrInsert.side_effect = [
            'test_language',
            DataError('testing')
        ]

        Instance._addLanguages('session', mock_inst, ['lang1', 'lang2'])
        self.assertEqual(len(mock_inst.language), 1)
        self.assertEqual(mock_inst.language[0], 'test_language')
    
    @patch('model.instance.Language')
    def test_add_language_str(self, mock_lang):
        mock_inst = MagicMock()
        mock_inst.language = []

        mock_lang.updateOrInsert.side_effect = [
            'test_language',
            DataError('testing')
        ]

        Instance._addLanguages('session', mock_inst, 'lang1')
        self.assertEqual(len(mock_inst.language), 1)
        self.assertEqual(mock_inst.language[0], 'test_language')
    
    @patch('model.instance.Rights')
    def test_add_rights(self, mock_rights):
        mock_inst = MagicMock()
        mock_inst.rights = []

        mock_rights.insert.return_value = 'test_rights'
        testRights = {
            'rights': 'rights1',
            'dates': ['rd1']
        }
        Instance._addRights(mock_inst, [testRights])
        self.assertEqual(mock_inst.rights[0], 'test_rights')
    
    @patch('model.instance.Item')
    def test_add_items(self, mock_item):
        mock_inst = MagicMock()
        mock_inst.items = []

        mock_item.createOrStore.return_value = ('test_item', 'inserted')

        Instance._addItems('session', mock_inst, ['item1'])
        self.assertEqual(mock_inst.items[0], 'test_item')
    
    def test_role_exists(self):
        mock_session = MagicMock()
        mock_session.query().filter().filter().filter().one_or_none.return_value = 'test_role'
        mock_agent = MagicMock()
        mock_agent.id = 1
        role = AgentInstances.roleExists(mock_session, mock_agent, 'role', 1)
        self.assertEqual(role, 'test_role')
