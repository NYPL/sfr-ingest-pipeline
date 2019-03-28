import unittest
from unittest.mock import patch, MagicMock, call
from collections import namedtuple

from sqlalchemy.orm.exc import NoResultFound

from model.work import Work, AgentWorks
from model.date import DateField

from helpers.errorHelpers import DataError, DBError

TestDate = namedtuple('TestDate', ['id', 'display_date', 'date_range', 'date_type'])

class WorkTest(unittest.TestCase):

    def test_work_init(self):
        testWork = Work(
            title='Testing',
            summary='Summary'
        )
        self.assertEqual(testWork.summary, 'Summary')
        self.assertEqual(str(testWork), '<Work(title=Testing)>')

    def test_child_dict(self):
        workData = {
            'title': 'Testing',
            'instances': ['instance1', 'instance2'],
            'agents': ['agent1', 'agent2', 'agent3']
        }

        childFields = Work._buildChildDict(workData)
        self.assertEqual(childFields['instances'][1], 'instance2')
        self.assertEqual(len(childFields['agents']), 3)
        self.assertEqual(workData['title'], 'Testing')
        with self.assertRaises(KeyError):
            workData['instances']

    @patch('model.work.RawData', return_value=MagicMock())
    def test_work_insert(self, mock_raw):
        mock_session = MagicMock()
        testData = {
            'title': 'Testing'
        }
        testWork = Work.insert(mock_session, testData)
        self.assertEqual(testWork.title, 'Testing')
        self.assertNotEqual(testWork.uuid, '')

    @patch('model.work.Instance')
    def test_add_instance(self, mock_inst):
        mock_work = MagicMock()
        mock_work.instances = []

        mock_inst.insert.return_value = 'test_instance'

        Work._addInstances('session', mock_work, ['instance1'])
        self.assertEqual(mock_work.instances[0], 'test_instance')
    
    @patch('model.work.Identifier')
    def test_add_identifiers(self, mock_identifier):
        mock_work = MagicMock()
        mock_work.identifiers = []

        mock_identifier.returnOrInsert.side_effect = [
            (0, 'test_identifier'),
            DataError('testing')
        ]

        Work._addIdentifiers('session', mock_work, ['id1', 'id2'])
        self.assertEqual(len(mock_work.identifiers), 1)
        self.assertEqual(mock_work.identifiers[0], 'test_identifier')
    
    @patch('model.work.Agent')
    @patch('model.work.AgentWorks')
    def test_add_agents(self, mock_agent_works, mock_agent):
        mock_work = MagicMock()
        mock_work.agents = []
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
        Work._addAgents('session', mock_work, test_agents)
        mock_agent_works.assert_has_calls([
            call(agent=mock_name, work=mock_work, role='tester'),
            call(agent=mock_name, work=mock_work, role='tester2')
        ])

    @patch('model.work.AltTitle')
    def test_add_alt_title(self, mock_alt):
        mock_work = MagicMock()
        mock_work.alt_titles = []

        mock_alt.return_value = 'test_title'

        Work._addAltTitles(mock_work, ['alt1'])
        self.assertEqual(mock_work.alt_titles[0], 'test_title')
    
    @patch('model.work.Subject')
    def test_add_subject(self, mock_subj):
        mock_work = MagicMock()
        mock_work.subjects = []

        mock_subj.updateOrInsert.return_value = (1, 'test_subject')

        Work._addSubjects('session', mock_work, ['subject1'])
        self.assertEqual(mock_work.subjects[0], 'test_subject')
    
    @patch('model.work.Measurement')
    def test_add_measurement(self, mock_meas):
        mock_work = MagicMock()
        mock_work.measurements = []

        mock_meas.insert.return_value = ('test_measure')

        Work._addMeasurements('session', mock_work, ['measure1'])
        self.assertEqual(mock_work.measurements[0], 'test_measure')
    
    @patch('model.work.Link')
    def test_add_link(self, mock_link):
        mock_work = MagicMock()
        mock_work.links = []

        mock_link.return_value = 'test_link'

        Work._addLinks(mock_work, [MagicMock()])
        self.assertEqual(mock_work.links[0], 'test_link')
    
    @patch('model.work.DateField')
    def test_add_date(self, mock_date):
        mock_work = MagicMock()
        mock_work.dates = []

        mock_date.insert.return_value = 'test_date'

        Work._addDates(mock_work, ['1999-01-01'])
        self.assertEqual(mock_work.dates[0], 'test_date')
    
    @patch('model.work.Language')
    def test_add_languages(self, mock_lang):
        mock_work = MagicMock()
        mock_work.language = []

        mock_lang.updateOrInsert.side_effect = [
            'test_language',
            DataError('testing')
        ]

        Work._addLanguages('session', mock_work, ['lang1', 'lang2'])
        self.assertEqual(len(mock_work.language), 1)
        self.assertEqual(mock_work.language[0], 'test_language')
    
    @patch('model.work.Language')
    def test_add_language_str(self, mock_lang):
        mock_work = MagicMock()
        mock_work.language = []

        mock_lang.updateOrInsert.side_effect = [
            'test_language',
            DataError('testing')
        ]

        Work._addLanguages('session', mock_work, 'lang1')
        self.assertEqual(len(mock_work.language), 1)
        self.assertEqual(mock_work.language[0], 'test_language')

    @patch('model.work.Work.getByUUID', return_value='test_id')
    def test_lookup_uuid(self, mock_get_uuid):
        testID = Work.lookupWork('session', ['id1'], {
            'type': 'uuid',
            'identifier': 'test_uuid'
        })
        self.assertEqual(testID, 'test_id')
    
    @patch('model.work.Identifier')
    def test_lookup_work(self, mock_iden):
        mock_session = MagicMock()
        mock_session.query().get().uuid = 'test_uuid'
        mock_iden.getByIdentifier.return_value = 'test_id'
        testID = Work.lookupWork(mock_session, ['id1'], None)
        self.assertEqual(testID, 'test_uuid')
    
    @patch('model.work.Identifier')
    def test_lookup_work_by_instance(self, mock_iden):
        mock_session = MagicMock()
        mock_session.query().get().work.uuid = 'test_uuid'
        mock_iden.getByIdentifier.side_effect = [None, 'test_id']
        testID = Work.lookupWork(mock_session, ['id1'], None)
        self.assertEqual(testID, 'test_uuid')
    
    @patch('model.work.Identifier')
    def test_lookup_work_not_found(self, mock_iden):
        mock_session = MagicMock()
        mock_session.query().get().work.uuid = 'test_uuid'
        mock_iden.getByIdentifier.side_effect = [None, None]
        testID = Work.lookupWork(mock_session, ['id1'], None)
        self.assertEqual(testID, None)

    @patch('model.work.uuid.UUID', return_value='test_uuid')
    def test_get_by_uuid(self, mock_uuid):
        mock_session = MagicMock()
        mock_session.query().filter().one.return_value = 'exist_uuid'
        testUUID = Work.getByUUID(mock_session, 'uuid')
        self.assertEqual(testUUID, 'exist_uuid')
    
    @patch('model.work.uuid.UUID', return_value='test_uuid')
    def test_get_by_uuid_missing(self, mock_uuid):
        mock_session = MagicMock()
        mock_session.query().filter().one.side_effect = NoResultFound
        with self.assertRaises(DBError):
            Work.getByUUID(mock_session, 'uuid')
    
    def test_create_agent_work(self):
        testRec = AgentWorks(
            work_id=1,
            agent_id=1,
            role='tester'
        )
        self.assertEqual(str(testRec), '<AgentWorks(work=1, agent=1, role=tester)>')
    
    def test_role_exists(self):
        mock_session = MagicMock()
        mock_session.query().filter().filter().filter().one_or_none.return_value = 'test_role'
        mock_agent = MagicMock()
        mock_agent.id = 1
        role = AgentWorks.roleExists(mock_session, mock_agent, 'role', 1)
        self.assertEqual(role, 'test_role')

    # Special test case to ensure that dates are handled properly
    def test_date_backref(self):
        testWork = Work()
        tDate = DateField.insert({
            'id': 1,
            'display_date': 'January 1, 2019',
            'date_range': '2019-01-01',
            'date_type': 'test'
        })
        testWork.dates.append(tDate)
        self.assertIsInstance(testWork, Work)
        self.assertEqual(len(testWork.dates), 1)
        self.assertEqual(testWork.dates[0].date_range, '[2019-01-01,)')