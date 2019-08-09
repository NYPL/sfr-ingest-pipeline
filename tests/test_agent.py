import unittest
from unittest.mock import patch, MagicMock

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from sfrCore.helpers import DataError
from sfrCore.model import Agent
from sfrCore.model.agent import Alias


class TestAgent(unittest.TestCase):

    def test_agent_init(self):
        testAgent = Agent('session')
        self.assertEqual(testAgent.session, 'session')

    def test_agent_repr(self):
        testAgent = Agent('session')
        testAgent.name = 'Tester, Test'
        testAgent.viaf = 1
        self.assertEqual(
            str(testAgent),
            '<Agent(name=Tester, Test, sort_name=None, lcnaf=None, viaf=1)>'
        )

    def test_agent_dir(self):
        testAgent = Agent('session')
        self.assertEqual(
            dir(testAgent),
            ['biography', 'lcnaf', 'name', 'sort_name', 'viaf']
        )

    def test_agent_tmp_rels(self):
        testAgent = Agent('session')
        testAgent.createTmpRelations({'roles': None, 'dates': ['date']})
        self.assertEqual(testAgent.tmp_aliases, [])
        self.assertEqual(testAgent.tmp_roles, [])
        self.assertEqual(testAgent.tmp_dates, ['date'])

    def test_agent_remove_tmp_rels(self):
        testAgent = Agent('session')
        testAgent.createTmpRelations({})
        self.assertEqual(testAgent.tmp_roles, [])
        testAgent.removeTmpRelations()
        with self.assertRaises(AttributeError):
            testAgent.tmp_roles

    def test_updateInsert_insert(self):
        with patch('sfrCore.model.Agent.createAgent') as mock_create:
            mock_agent = MagicMock()
            mock_agent.lookup.return_value = None
            mock_create.return_value = (mock_agent, ['test'])
            testAgent, roles = Agent.updateOrInsert('session', 'fakeAgent')
            self.assertEqual(testAgent, mock_agent)
            self.assertEqual(roles, ['test'])

    def test_updateInsert_update(self):
        with patch('sfrCore.model.Agent.createAgent') as mock_create:
            mock_agent = MagicMock()
            mock_agent.lookup.return_value = 1
            mock_create.return_value = (mock_agent, ['test'])
            mock_existing = MagicMock()
            mock_existing.update.return_value = ['existing', 'test']
            mock_session = MagicMock()
            mock_session.query.return_value.get.return_value = mock_existing
            testAgent, roles = Agent.updateOrInsert(mock_session, 'fakeAgent')
            self.assertEqual(testAgent, mock_existing)
            self.assertTrue('existing' in roles and 'test' in roles)

    @patch.object(Agent, 'addLifespan')
    @patch.object(Agent, 'insertData')
    @patch.object(Agent, 'cleanName')
    @patch.object(Agent, 'removeTmpRelations')
    def test_agent_create(self, mock_rm, mock_clean, mock_inst, mock_add):
        with patch.object(Agent, 'name', 'Name, New'):
            testData = {'name': 'Name, New'}
            newAgent, newRoles = Agent.createAgent('session', testData)
            self.assertEqual(newAgent.name, 'Name, New')
            self.assertEqual(newRoles, [])

    @patch.object(Agent, 'addLifespan')
    @patch.object(Agent, 'insertData')
    @patch.object(Agent, 'cleanName')
    @patch.object(Agent, 'removeTmpRelations')
    def test_agent_create_err(self, mock_rm, mock_clean, mock_inst, mock_add):
        with patch.object(Agent, 'name', '    '):
            with self.assertRaises(DataError):
                testData = {'name': 'Name, New'}
                newAgent, newRoles = Agent.createAgent('session', testData)

    @patch.object(Agent, 'createTmpRelations')
    @patch.object(Agent, 'cleanName')
    @patch.object(Agent, 'removeTmpRelations')
    @patch('sfrCore.model.agent.Alias')
    @patch('sfrCore.model.agent.Link')
    @patch('sfrCore.model.agent.DateField')
    def test_agent_update(self,
                          mock_date,
                          mock_link,
                          mock_alias,
                          mock_rm,
                          mock_clean,
                          mock_tmp):
        testAgent = Agent()
        for tmp in [
            ('tmp_aliases', ['Alias, Name']),
            ('tmp_link', [{'link': 'test_link'}]),
            ('tmp_dates', ['test_date']),
            ('tmp_roles', ['test'])
        ]:
            setattr(testAgent, tmp[0], tmp[1])

        testAgent.name = 'Old, Name'

        newData = {'name': 'New, Name'}

        mock_alias.insertOrSkip.return_value = MagicMock()
        mock_link.updateOrInsert.side_effect = [MagicMock()]
        mock_date.updateOrInsert.side_effect = [MagicMock()]

        testAgent.update('session', newData)
        self.assertEqual(testAgent.name, 'New, Name')

    @patch('sfrCore.model.agent.Alias')
    @patch('sfrCore.model.agent.Link')
    @patch('sfrCore.model.agent.DateField')
    def test_agent_insertData(self, mock_date, mock_link, mock_alias):
        testAgent = Agent()
        for tmp in [
            ('tmp_aliases', ['Alias, Name']),
            ('tmp_link', {'link': 'test_link'}),
            ('tmp_dates', [{'date_type': 'test'}]),
            ('tmp_roles', ['test'])
        ]:
            setattr(testAgent, tmp[0], tmp[1])

        testAgent.name = 'Old, Name'

        newData = {'name': 'New, Name'}

        mock_alias.return_value = MagicMock()
        mock_link.side_effect = [MagicMock()]
        mock_date.insert.side_effect = [MagicMock()]

        testAgent.insertData(newData)
        self.assertEqual(testAgent.name, 'New, Name')
        self.assertEqual(testAgent.sort_name, 'new, name')

    def test_agent_insert_sort_none(self):
        testAgent = Agent()
        testData = {
            'name': 'New, Name',
            'sort_name': None
        }
        testAgent.createTmpRelations(testData)
        testAgent.insertData(testData)
        testAgent.removeTmpRelations()
        self.assertEqual(testAgent.name, 'New, Name')
        self.assertEqual(testAgent.sort_name, 'new, name')

    def test_agent_insert_sort_unicode(self):
        testAgent = Agent()
        testData = {
            'name': 'New, Name',
            'sort_name': 'New, Name'.encode('utf-8')
        }
        testAgent.createTmpRelations(testData)
        testAgent.insertData(testData)
        testAgent.removeTmpRelations()
        self.assertEqual(testAgent.name, 'New, Name')
        self.assertEqual(testAgent.sort_name, 'new, name')

    @patch.object(Agent, 'findTrgmQuery', return_value={'id': 'mockAgent'})
    @patch.object(Agent, 'findViafQuery', return_value=None)
    def test_agent_lookup_name(self, mock_viaf, mock_auth):
        testAgent = Agent()
        testAgent.name = 'Tester, Test'

        res = testAgent.lookup()
        self.assertEqual(res, 'mockAgent')

    @patch.object(Agent, 'authorityQuery', return_value='mockAgent')
    def test_agent_lookup_authority(self, mock_auth):
        testAgent = Agent()
        testAgent.viaf = 999999999
        testAgent.lcnaf = 999999999
        testAgent.name = 'Tester, Test'

        res = testAgent.lookup()
        self.assertEqual(res, 'mockAgent')

    def test_add_lifespan_date(self):
        testAgent = Agent()
        testAgent.tmp_dates = []
        testAgent.addLifespan('testdate', '1066')
        self.assertEqual(testAgent.tmp_dates[0]['display_date'], '1066')

    def test_trgm_query_success(self):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.rowcount = 1
        mock_resp.first.return_value = 'mockAgent'
        mock_session.execute.return_value = mock_resp
        testAgent = Agent(mock_session)
        testAgent.name = 'O\'Tester, Test'
        matchAgent = testAgent.findTrgmQuery()
        self.assertEqual(matchAgent, 'mockAgent')

    def test_trgm_query_multiple_response(self):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.rowcount = 2
        mock_session.execute.return_value = mock_resp
        testAgent = Agent(mock_session)
        testAgent.name = 'Tester, Test'
        manyMatches = testAgent.findTrgmQuery()
        self.assertEqual(manyMatches, None)

    def test_trgm_query_no_matches(self):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.rowcount = 0
        mock_response.first.return_value = None
        mock_session.execute.return_value = mock_response
        testAgent = Agent(mock_session)
        testAgent.name = 'Tester, Test'
        noMatches = testAgent.findTrgmQuery()
        self.assertEqual(noMatches, None)

    @patch('sfrCore.model.agent.requests')
    @patch.object(Agent, 'authorityQuery', return_value='matchedAgent')
    @patch.object(Agent, 'cleanName')
    def test_viaf_query_success(self, mock_clean, mock_auth, mock_req):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            'name': 'Test',
            'viaf': 000,
            'lcnaf': 000
        }
        mock_req.get.return_value = mock_resp
        testAgent = Agent()
        testAgent.name = 'Old'
        outAgent = testAgent.findViafQuery()
        self.assertEqual(outAgent, 'matchedAgent')

    @patch('sfrCore.model.agent.requests')
    def test_viaf_query_miss(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            'message': 'Missing'
        }
        mock_req.get.return_value = mock_resp
        testAgent = Agent()
        testAgent.name = 'Old'
        outAgent = testAgent.findViafQuery()
        self.assertEqual(outAgent, None)

    def test_authority_query_success(self):
        mock_session = MagicMock()
        mock_session.query().filter().one_or_none.return_value = 'mockAgent'
        testAgent = Agent(mock_session)
        testAgent.viaf = 999999999
        testAgent.lcnaf = 999999999
        foundAgent = testAgent.authorityQuery()
        self.assertEqual(foundAgent, 'mockAgent')

    def test_authority_query_multiple_error(self):
        mock_session = MagicMock()
        mock_session.query()\
            .filter().one_or_none.side_effect = MultipleResultsFound
        mock_session.query().filter().first.return_value = 'firstMatch'
        testAgent = Agent(mock_session)
        testAgent.viaf = 999999999
        testAgent.lcnaf = 999999999
        firstAgent = testAgent.authorityQuery()
        self.assertEqual(firstAgent, 'firstMatch')

    def test_authority_query_single_error(self):
        mock_session = MagicMock()
        mock_session.query().filter().one_or_none.return_value = None
        testAgent = Agent(mock_session)
        testAgent.viaf = 999999999
        testAgent.lcnaf = 999999999
        noAgent = testAgent.authorityQuery()
        self.assertEqual(noAgent, None)

    def test_clean_name(self):
        testAgent = Agent()
        testAgent.name = '[Test, Tester 1950-2000]'
        testAgent.tmp_dates = []
        testAgent.tmp_roles = []
        testAgent.cleanName()
        self.assertEqual(testAgent.tmp_roles, [])
        self.assertEqual(testAgent.name, 'Test, Tester')
        self.assertEqual(testAgent.tmp_dates[0]['display_date'], '1950')
        self.assertEqual(testAgent.tmp_dates[1]['display_date'], '2000')

    def test_clean_name_birth_only(self):
        testAgent = Agent()
        testAgent.name = 'Test, Tester 1950-'
        testAgent.tmp_dates = []
        testAgent.tmp_roles = []
        testAgent.cleanName()
        self.assertEqual(testAgent.tmp_roles, [])
        self.assertEqual(testAgent.name, 'Test, Tester')
        self.assertEqual(testAgent.tmp_dates[0]['display_date'], '1950')

    def test_clean_roles(self):
        testAgent = Agent()
        testAgent.name = 'Test, Tester [tester; testing]'
        testAgent.tmp_dates = []
        testAgent.tmp_roles = []
        testAgent.cleanName()
        self.assertEqual(testAgent.name, 'Test, Tester')
        self.assertEqual(testAgent.tmp_roles, ['tester', 'testing'])

    def test_clean_role(self):
        testAgent = Agent()
        testAgent.name = 'Test, Tester [tester]'
        testAgent.tmp_dates = []
        testAgent.tmp_roles = []
        testAgent.cleanName()
        self.assertEqual(testAgent.name, 'Test, Tester')
        self.assertEqual(testAgent.tmp_roles, ['tester'])

    def test_combined(self):
        testAgent = Agent()
        testAgent.name = 'Test, Tester 1950-2000 [tester]'
        testAgent.tmp_dates = []
        testAgent.tmp_roles = []
        testAgent.cleanName()
        self.assertEqual(testAgent.name, 'Test, Tester')
        self.assertEqual(testAgent.tmp_roles, ['tester'])
        self.assertEqual(testAgent.tmp_dates[0]['display_date'], '1950')
        self.assertEqual(testAgent.tmp_dates[1]['display_date'], '2000')

    def test_alias_repr(self):
        testAlias = Alias()
        testAlias.alias = 'Testing'
        self.assertEqual(str(testAlias), '<Alias(alias=Testing, agent=None)>')

    def test_alias_skip(self):
        mock_session = MagicMock()
        mock_session.query().join().filter().filter().one.return_value = None
        mock_model = MagicMock()

        Alias.insertOrSkip(mock_session, 'Alias Name', mock_model, 1)

    def test_alias_insert(self):
        mock_session = MagicMock()
        mock_session.query()\
            .join().filter().filter().one.side_effect = NoResultFound
        mock_model = MagicMock()

        newAlias = Alias.insertOrSkip(
            mock_session,
            'Alias Name',
            mock_model,
            1
        )
        self.assertEqual(newAlias.alias, 'Alias Name')

    # Name full integration tests

    def test_new_agent_creation(self):
        mockSession = MagicMock()
        newAgent, roles = Agent.createAgent(
            mockSession,
            {
                'name': 'Murry, Kathleen Beauchamp',
                'roles': ['author']
            }
        )
        self.assertEqual(newAgent.name, 'Murry, Kathleen Beauchamp')
        self.assertEqual(roles[0], 'author')
