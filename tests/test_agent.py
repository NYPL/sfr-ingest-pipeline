import unittest
from unittest.mock import patch, call, MagicMock

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from helpers.errorHelpers import DataError
from model.agent import Agent


class TestAgent(unittest.TestCase):

    def test_agent_repr(self):
        testAgent = Agent()
        testAgent.name = 'Tester'
        testAgent.sort_name = 'Tester'
        self.assertEqual(
            str(testAgent),
            '<Agent(name=Tester, sort_name=Tester, lcnaf=None, viaf=None)>'
        )
    
    @patch('model.agent.Agent._cleanName')
    @patch('model.agent.Agent.lookupAgent', return_value=None)
    @patch('model.agent.Agent.insert', return_value='newAgent')
    def test_updateInsert_insert(self, mock_insert, mock_lookup, mock_clean):
        mockAgent = {'name': 'Tester, Test', 'roles': None, 'dates': None}
        testAgent, roles = Agent.updateOrInsert('session', mockAgent)
        self.assertEqual(testAgent, 'newAgent')
        self.assertEqual(roles, [])
        mock_clean.called_once_with(mockAgent, [], [])
        mock_lookup.called_once_with('session', mockAgent, [], [], [])
        mock_insert.called_once_with(mockAgent, aliases=[], link=[], dates=[])
    
    @patch('model.agent.Agent._cleanName')
    def test_updateInsert_noName(self, mock_clean):
        mockAgent = {'name': ''}
        try:
            Agent.updateOrInsert('session', mockAgent)
        except DataError:
            pass
        mock_clean.called_once_with(mockAgent, [], [])
        self.assertRaises(DataError)

    @patch('model.agent.Agent._cleanName')
    @patch('model.agent.Agent.lookupAgent', return_value=1)
    @patch('model.agent.Agent.update')
    def test_updateInsert_update(self, mock_update, mock_lookup, mock_clean):
        mockAgent = {'name': 'Tester, Test'}
        mock_session = MagicMock()
        mock_session.query().get.return_value = 'existingAgent'
        testAgent, roles = Agent.updateOrInsert(mock_session, mockAgent)
        self.assertEqual(testAgent, 'existingAgent')
        self.assertEqual(roles, [])
        mock_clean.called_once_with(mockAgent, [], [])
        mock_lookup.called_once_with(mock_session, mockAgent, [], [], [])
        mock_update.called_once_with(
            mock_session,
            'existingAgent',
            mockAgent,
            aliases=[],
            link=[],
            dates=[]
        )

    @patch('model.agent.Alias')
    @patch('model.agent.Link')
    @patch('model.agent.DateField')
    def test_agent_update(self, mock_date, mock_link, mock_alias):
        testUpdate = {'name': 'Name, New'}
        testExisting = MagicMock()
        testExisting.name = 'Name, Old'
        testExisting.aliases = set()
        testExisting.links = set()
        testExisting.dates = set()
        mock_alias.insertOrSkip.return_value = 'Name, Other'
        mock_link.updateOrInsert.side_effect = ['link1']
        mock_date.updateOrInsert.side_effect = ['date1', 'date2', 'date3']
        Agent.update(
            'session',
            testExisting,
            testUpdate,
            aliases=['Name, Other'],
            link={'link': 'linker', 'link2': 'linker'},
            dates=['date1', 'date2', 'date3']
        )
        self.assertEqual(testExisting.name, 'Name, New')
        self.assertEqual(testExisting.aliases, set(['Name, Other']))
        self.assertEqual(testExisting.dates, set(['date1', 'date2', 'date3']))
    
    @patch('model.agent.Agent')
    @patch('model.agent.Alias')
    @patch('model.agent.Link')
    @patch('model.agent.DateField')
    def test_agent_insert(self, mock_date, mock_link, mock_alias, mock_agent):
        testInsert = {'name': 'Name, New'}
        mock_alias.return_value = 'Name, Other'
        mock_link.side_effect = ['link1']
        mock_date.insert.side_effect = ['date1', 'date2', 'date3']

        mock_new = MagicMock()
        mock_new.name = 'Name, New'
        mock_new.sort_name = None
        mock_new.aliases = set()
        mock_new.links = set()
        mock_new.dates = set()
        mock_agent.return_value = mock_new

        outAgent = Agent.insert(
            testInsert,
            aliases=['Name, Other'],
            link={'link': 'linker', 'link2': 'linker'},
            dates=[
                {'date_type': 'test', 'display': 'test'}, 
                {'date_type': 'test2', 'display_date': 'test2'},    
                {'date_type': 'test', 'display': 'test'} 
            ]
        )
        self.assertEqual(outAgent.name, 'Name, New')
        self.assertEqual(outAgent.sort_name, 'Name, New')
        self.assertEqual(outAgent.aliases, set(['Name, Other']))
        self.assertEqual(outAgent.dates, set(['date1', 'date2']))


    @patch('model.agent.Agent._findJaroWinklerQuery', return_value='mockAgent')
    @patch('model.agent.Agent._findViafQuery', return_value=None)
    def test_agent_lookup_name(self, mock_viaf, mock_auth):
        testAgent = {
            'viaf': None,
            'lcnaf': None,
            'name': 'Tester, Test'
        }
        res = Agent.lookupAgent('session', testAgent, [], [], [])
        self.assertEqual(res, 'mockAgent')
    
    @patch('model.agent.Agent._authorityQuery', return_value='mockAgent')
    def test_agent_lookup_authority(self, mock_auth):
        testAgent = {
            'viaf': 00000000,
            'lcnaf': 00000000,
            'name': 'Tester, Test'
        }
        res = Agent.lookupAgent('session', testAgent, [], [], [])
        self.assertEqual(res, 'mockAgent')
    
    def test_jw_query_success(self):
        mock_session = MagicMock()
        mock_session.query().filter().one.return_value = 'mockAgent'
        testAgent = Agent._findJaroWinklerQuery(
            mock_session,
            {'name': 'O\'Tester, Test'}
        )
        self.assertEqual(testAgent, 'mockAgent')

    def test_jw_query_multiple_error(self):
        mock_session = MagicMock()
        mock_session.query().filter().one.side_effect = MultipleResultsFound
        testAgent = Agent._findJaroWinklerQuery(
            mock_session,
            {'name': 'Tester, Test'}
        )
        self.assertEqual(testAgent, None)
    
    def test_jw_query_single_error(self):
        mock_session = MagicMock()
        mock_session.query().filter().one.side_effect = NoResultFound
        testAgent = Agent._findJaroWinklerQuery(
            mock_session,
            {'name': 'Tester, Test'}
        )
        self.assertEqual(testAgent, None)
    
    @patch('model.agent.requests')
    @patch('model.agent.Agent._authorityQuery', return_value='matchedAgent')
    @patch('model.agent.Agent._cleanName')
    def test_viaf_query_success(self, mock_clean, mock_auth, mock_req):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            'name': 'Test',
            'viaf': 000,
            'lcnaf': 000
        }
        mock_req.get.return_value = mock_resp
        outAgent = Agent._findViafQuery('session', {'name': 'Old'}, [], [], [])
        self.assertEqual(outAgent, 'matchedAgent')
    
    @patch('model.agent.requests')
    def test_viaf_query_miss(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            'message': 'Missing'
        }
        mock_req.get.return_value = mock_resp
        outAgent = Agent._findViafQuery('session', {'name': 'Old'}, [], [], [])
        self.assertEqual(outAgent, None)
    
    def test_authority_query_success(self):
        mock_session = MagicMock()
        mock_session.query().filter().one_or_none.return_value = 'mockAgent'
        testAgent = Agent._authorityQuery(
            mock_session,
            {
                'name': 'Tester, Test',
                'viaf': 000,
                'lcnaf': 000
            }
        )
        self.assertEqual(testAgent, 'mockAgent')

    def test_authority_query_multiple_error(self):
        mock_session = MagicMock()
        mock_session.query().filter().one.side_effect = MultipleResultsFound
        try:
            Agent._authorityQuery(
                mock_session,
                {
                    'name': 'Tester, Test',
                    'viaf': 000,
                    'lcnaf': 000
                }
            )
        except MultipleResultsFound:
            pass
        self.assertRaises(MultipleResultsFound)
    
    def test_authority_query_single_error(self):
        mock_session = MagicMock()
        mock_session.query().filter().one_or_none.return_value = None
        testAgent = Agent._authorityQuery(
            mock_session,
            {
                'name': 'Tester, Test',
                'viaf': 000,
                'lcnaf': 000
            }
        )
        self.assertEqual(testAgent, None)

    def test_clean_name(self):
        
        nameTest = {
            'name': '[Test, Tester 1950-2000]',
            'sort_name': '',
            'viaf': None,
            'lcnaf': None
        }
        roleTest = []
        dateTest = []
        Agent._cleanName(nameTest, roleTest, dateTest)
        self.assertEqual(roleTest, [])
        self.assertEqual(nameTest['name'], 'Test, Tester')
        self.assertEqual(dateTest[0]['display_date'], '1950')
        self.assertEqual(dateTest[1]['display_date'], '2000')
    
    @patch('model.agent.DateField')
    def test_clean_name_birth_only(self, mock_date):
        
        singleTest = Agent(
            name='Test, Tester 1950-',
        )
        nameTest = {
            'name': 'Test, Tester 1950-',
            'sort_name': '',
            'viaf': None,
            'lcnaf': None
        }
        roleTest = []
        dateTest = []
        Agent._cleanName(nameTest, roleTest, dateTest)
        self.assertEqual(roleTest, [])
        self.assertEqual(nameTest['name'], 'Test, Tester')
        self.assertEqual(dateTest[0]['display_date'], '1950')
    
    def test_clean_roles(self):
        nameTest = {
            'name': 'Test, Tester [tester; testing]',
            'sort_name': '',
            'viaf': None,
            'lcnaf': None
        }
        roleTest = []
        dateTest = []
        Agent._cleanName(nameTest, roleTest, dateTest)
        self.assertEqual(nameTest['name'], 'Test, Tester')
        self.assertEqual(roleTest, ['tester', 'testing'])
    
    def test_clean_role(self):
        nameTest = {
            'name': 'Test, Tester [tester]',
            'sort_name': '',
            'viaf': None,
            'lcnaf': None
        }
        roleTest = []
        dateTest = []
        Agent._cleanName(nameTest, roleTest, dateTest)
        self.assertEqual(nameTest['name'], 'Test, Tester')
        self.assertEqual(roleTest, ['tester'])
    
    @patch('model.agent.DateField')
    def test_combined(self, mock_date):
        nameTest = {
            'name': 'Test, Tester 1950-2000 [tester]',
            'sort_name': '',
            'viaf': None,
            'lcnaf': None
        }
        roleTest = []
        dateTest = []
        Agent._cleanName(nameTest, roleTest, dateTest)
        self.assertEqual(nameTest['name'], 'Test, Tester')
        self.assertEqual(roleTest, ['tester'])
        self.assertEqual(dateTest[0]['display_date'], '1950')
        self.assertEqual(dateTest[1]['display_date'], '2000')
    