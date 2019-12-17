import unittest
from unittest.mock import patch, MagicMock, call, DEFAULT

from sfrCore.model import Instance
from sfrCore.model.instance import AgentInstances
from sfrCore.helpers.errors import DataError


class InstanceTest(unittest.TestCase):
    def test_create_instance(self):
        testInst = Instance()
        testInst.title = 'Testing'
        testInst.edition = '1st ed'
        testInst.summary = 'test summary'

        self.assertEqual(
            str(testInst),
            '<Instance(title=Testing, edition=1st ed, work=None)>'
        )
        self.assertEqual(testInst.summary, 'test summary')

    def test_create_tmp(self):
        instanceData = {
            'formats': ['item1', 'item2'],
            'agents': ['agent1', 'agent2', 'agent3']
        }
        testInst = Instance()
        testInst.createTmpRelations(instanceData)
        self.assertEqual(testInst.tmp_formats[1], 'item2')
        self.assertEqual(len(testInst.tmp_agents), 3)
        self.assertEqual(testInst.items, set())

    def test_remove_tmp(self):
        testInst = Instance()
        testInst.createTmpRelations({})
        testInst.tmp_agents = ['agent1', 'agent2']
        testInst.removeTmpRelations()
        with self.assertRaises(AttributeError):
            testInst.tmp_agents

    @patch.object(Instance, 'lookup', return_value=None)
    @patch.object(
        Instance,
        'createNew',
        return_value=('newInstance', ['epub'])
    )
    def test_updateInsert_insert(self, mock_create, mock_lookup):
        mock_work = MagicMock()
        newInstance = Instance.updateOrInsert('session', {}, mock_work)
        self.assertEqual(newInstance, 'newInstance')
        self.assertEqual(mock_work.epubsToLoad[0], 'epub')

    @patch.object(Instance, 'lookup', return_value=1)
    def test_updateInsert_update(self, mock_lookup):
        mock_work = MagicMock()
        mock_instance = MagicMock()
        mock_instance.update.return_value = ['epub']
        mock_session = MagicMock()
        mock_session.query().get.return_value = mock_instance
        oldInstance = Instance.updateOrInsert(mock_session, {}, mock_work)
        self.assertEqual(oldInstance, mock_instance)
        self.assertEqual(mock_work.epubsToLoad[0], 'epub')

    @patch('sfrCore.model.instance.Identifier.getByIdentifier', return_value=1)
    def test_lookup_found(self, mock_get):
        mock_session = MagicMock()
        mock_session.query().filter().one.return_value = ('vol',)
        existingID = Instance.lookup(mock_session, [], 'vol')
        self.assertEqual(existingID, 1)

    @patch('sfrCore.model.instance.Identifier.getByIdentifier', return_value=1)
    def test_lookup_not_found(self, mock_get):
        mock_session = MagicMock()
        mock_session.query().filter().one.return_value = ('vol',)
        existingID = Instance.lookup(mock_session, [], 'other_vol')
        self.assertEqual(existingID, None)

    def test_add_new_item(self):
        mock_instance = MagicMock()
        mock_instance.items = set()
        mock_session = MagicMock()
        mock_session.query().get.return_value = mock_instance
        Instance.addItemRecord(mock_session, 1, 'newItem')
        self.assertEqual(list(mock_instance.items)[0], 'newItem')

    @patch.object(Instance, 'createTmpRelations')
    @patch.object(Instance, 'insertData', return_value=['epub'])
    @patch.object(Instance, 'removeTmpRelations')
    def test_create_new(self, mock_rm, mock_insert, mock_tmp):
        testInst, testEpubs = Instance.createNew('session', {})
        self.assertIsInstance(testInst, Instance)
        self.assertEqual(testEpubs, ['epub'])

    def test_insertData(self):
        testData = {
            'title': 'Test Instance'
        }
        testInstance = Instance()
        with patch.multiple(Instance,
                            cleanData=DEFAULT,
                            addAgents=DEFAULT,
                            addIdentifiers=DEFAULT,
                            addAltTitles=DEFAULT,
                            addMeasurements=DEFAULT,
                            addLinks=DEFAULT,
                            addDates=DEFAULT,
                            addRights=DEFAULT,
                            insertLanguages=DEFAULT,
                            insertItems=DEFAULT
                            ) as inst_mocks:
            inst_mocks['insertItems'].return_value = ['epub']
            newEpubs = testInstance.insertData(testData)
            self.assertEqual(testInstance.title, 'Test Instance')
            self.assertEqual(newEpubs, ['epub'])

    def test_update(self):
        testData = {
            'title': 'New Instance'
        }
        testInstance = Instance()
        testInstance.title = 'Old Instance'
        testInstance.work = MagicMock()
        with patch.multiple(Instance,
                            setWorkFields=DEFAULT,
                            createTmpRelations=DEFAULT,
                            cleanData=DEFAULT,
                            updateAgents=DEFAULT,
                            addIdentifiers=DEFAULT,
                            updateAltTitles=DEFAULT,
                            updateMeasurements=DEFAULT,
                            updateLinks=DEFAULT,
                            updateDates=DEFAULT,
                            updateRights=DEFAULT,
                            insertLanguages=DEFAULT,
                            insertItems=DEFAULT,
                            removeTmpRelations=DEFAULT
                            ) as inst_mocks:
            inst_mocks['insertItems'].return_value = ['epub']
            newEpubs = testInstance.update('session', testData)
            self.assertEqual(testInstance.title, 'New Instance')
            self.assertEqual(newEpubs, ['epub'])

    def test_set_work_fields(self):
        testInstance = Instance()
        mock_work = MagicMock()
        mock_work.importSubjects.return_value = ['subj1', 'subj2']
        testInstance.work = mock_work
        testSubjects = ['subj1', 'subj2']
        testInstance.setWorkFields('series', 'pos', testSubjects)
        self.assertEqual(testInstance.work.series, 'series')
        self.assertEqual(testInstance.work.series_position, 'pos')

    def test_cleanData(self):
        testInstance = Instance()
        testInstance.pub_place = 'Boston : '
        testInstance.cleanData()
        self.assertEqual(testInstance.pub_place, 'Boston')

    @patch.object(Instance, 'addAgent')
    def test_add_agents(self, mock_add):
        testInstance = Instance()
        testInstance.tmp_agents = ['agent1', 'agent2', 'agent3']
        testInstance.addAgents()
        mock_add.assert_has_calls([
            call('agent1'),
            call('agent2'),
            call('agent3')
        ])

    @patch('sfrCore.model.instance.Agent')
    @patch('sfrCore.model.instance.AgentInstances')
    def test_add_agent(self, mock_agent_instances, mock_agent):
        mock_agent.updateOrInsert.return_value = ('agent1', ['tester'])
        test_agent = {'name': 'agent1'}
        testInstance = Instance()
        testInstance.addAgent(test_agent)
        mock_agent_instances.assert_has_calls([
            call(agent='agent1', instance=testInstance, role='tester')
        ])

    @patch.object(Instance, 'updateAgent')
    def test_update_agents(self, mock_update):
        testInstance = Instance()
        testInstance.tmp_agents = ['agent1', 'agent2', 'agent3']
        testInstance.updateAgents()
        mock_update.assert_has_calls([
            call('agent1'),
            call('agent2'),
            call('agent3')
        ])

    @patch('sfrCore.model.instance.Agent')
    @patch('sfrCore.model.instance.AgentInstances')
    def test_update_agent(self, mock_agent_instances, mock_agent):
        mock_agent.updateOrInsert.return_value = ('agent1', None)
        mock_agent_instances.roleExists.return_value = None
        test_agent = {'name': 'agent1'}
        mockSession = MagicMock()
        testInstance = Instance(session=mockSession)
        testInstance.updateAgent(test_agent)
        mock_agent_instances.assert_has_calls([
            call.roleExists(mockSession, 'agent1', 'author', None),
            call(agent='agent1', instance=testInstance, role='author')
        ])
        mockSession.add.assert_called_once()

    @patch('sfrCore.model.Instance.upsertIdentifier')
    @patch('sfrCore.model.Instance.fetchUnglueitSummary')
    def test_add_identifiers(self, mock_unglue, mock_identifier):
        testInst = Instance()
        testInst.tmp_identifiers = [
            {'identifier': 'id1', 'type': 'test'},
            {'identifier': 'id2', 'type': 'isbn'}
        ]
        mockTestID = MagicMock()
        mockTestID.type = 'test'
        mockTestISBN = MagicMock()
        mockTestISBN.type = 'isbn'
        mockISBNValue = MagicMock()
        mockISBNValue.value = 'testISBN'
        mockTestISBN.isbn = [mockISBNValue]
        mock_identifier.side_effect = [
            mockTestID,
            mockTestISBN
        ]

        testInst.addIdentifiers()
        # mock_unglue.assert_called_once_with('testISBN')
        mock_unglue.assert_not_called()  # Temporarily disabled for performance
        mock_identifier.assert_has_calls([
            call(testInst.tmp_identifiers[0]),
            call(testInst.tmp_identifiers[1])
        ])

    @patch('sfrCore.model.instance.Identifier.returnOrInsert', return_value=1)
    def test_identifier_upsert(self, mock_returnOrInsert):
        testInst = Instance()
        newIden = testInst.upsertIdentifier({
            'type': 'test',
            'identifier': 1
        })
        self.assertEqual(newIden, 1)

    @patch(
        'sfrCore.model.instance.Identifier.returnOrInsert',
        side_effect=DataError('Test Error')
    )
    def test_identifier_upsert_err(self, mock_returnOrInsert):
        testInst = Instance()
        newIden = testInst.upsertIdentifier({
            'type': 'test',
            'identifier': 1
        })
        self.assertEqual(newIden, None)

    @patch('sfrCore.model.instance.AltTitle', return_value='test_title')
    @patch.object(Instance, 'alt_titles', return_value=set('test_title'))
    def test_add_alt_title(self, mock_inst_alt, mock_alt):
        testInst = Instance()
        testInst.tmp_alt_titles = ['test_title']
        testInst.addAltTitles()
        self.assertEqual(list(testInst.alt_titles)[0], 'test_title')

    @patch('sfrCore.model.instance.Measurement')
    @patch.object(Instance, 'measurements', return_value=set('test_measure'))
    def test_add_measurement(self, mock_measures, mock_meas):
        mock_meas.insert.return_value = ('test_measure')
        testInst = Instance()
        testInst.tmp_measurements = ['measure1']
        testInst.addMeasurements()
        self.assertEqual(list(testInst.measurements)[0], 'test_measure')

    @patch('sfrCore.model.instance.Link')
    @patch.object(Instance, 'links', return_value=set('test_link'))
    def test_add_link(self, mock_links, mock_link):
        mock_link.return_value = 'test_link'

        testInst = Instance()
        testInst.tmp_links = [{'link': 'test_link'}]
        testInst.addLinks()
        self.assertEqual(list(testInst.links)[0], 'test_link')

    @patch('sfrCore.model.instance.DateField')
    @patch.object(Instance, 'dates', return_value=set('test_date'))
    def test_add_date(self, mock_dates, mock_date):
        mock_date.insert.return_value = 'test_date'

        testInst = Instance()
        testInst.tmp_dates = ['1999-01-01']
        testInst.addDates()
        self.assertEqual(list(testInst.dates)[0], 'test_date')

    @patch.object(Instance, 'insertLanguage')
    def test_insert_languages(self, mock_insert):

        testInst = Instance()
        testInst.tmp_language = 'lang1'
        testInst.insertLanguages()
        mock_insert.assert_called_with('lang1')

    def test_insert_language(self):
        with patch('sfrCore.model.instance.Language.updateOrInsert') as mock_lang:  # noqa: E501
            mock_insert = MagicMock()
            mock_lang.return_value = [mock_insert]
            testInst = Instance()
            testInst.insertLanguage('test_lang')
            self.assertEqual(list(testInst.language)[0], mock_insert)

    @patch('sfrCore.model.instance.Rights')
    @patch.object(Instance, 'rights', return_value=set('test_rights'))
    def test_add_rights(self, mock_right, mock_rights):
        mock_rights.insert.return_value = 'test_rights'
        testInst = Instance()
        testInst.tmp_rights = [{
            'rights': 'rights1',
            'dates': ['rd1']
        }]
        testInst.addRights()
        self.assertEqual(list(testInst.rights)[0], 'test_rights')

    @patch('sfrCore.model.instance.Item.createOrStore', side_effect=[
        MagicMock(), MagicMock()
    ])
    def test_insert_items(self, mock_item):
        testInst = Instance()
        testInst.tmp_formats = ['item1', 'item2']
        testInst.epubsToLoad = []
        newEpubs = testInst.insertItems()
        self.assertEqual(len(list(testInst.items)), 2)
        self.assertEqual(newEpubs, [])

    def test_role_exists(self):
        mock_session = MagicMock()
        mock_session.query().filter().filter().filter()\
            .one_or_none.return_value = 'test_role'
        mock_agent = MagicMock()
        mock_agent.id = 1
        role = AgentInstances.roleExists(mock_session, mock_agent, 'role', 1)
        self.assertEqual(role, 'test_role')
