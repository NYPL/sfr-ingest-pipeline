import unittest
from unittest.mock import patch, call, MagicMock

from model.agent import Agent


class TestAgent(unittest.TestCase):

    def test_agent_lookup_jw(self):
        mock_session = MagicMock()
        mock_session.query().filter().one.side_effect = [True]
        testAgent = {
            'viaf': None,
            'lcnaf': None,
            'name': 'Tester, Test'
        }
        res = Agent.lookupAgent(mock_session, testAgent)
        self.assertTrue(res)       

    @patch('model.agent.DateField')
    def test_clean_name(self, mock_date):
        
        nameTest = Agent(
            name='Test, Tester 1950-2000',
        )
        roles = nameTest._cleanName()
        self.assertEqual(roles, [])
        self.assertEqual(nameTest.name, 'Test, Tester')
        mock_date.insert.assert_any_call({
            'date_display': '1950',
            'date_range': '1950',
            'date_type': 'birth_date'
        })
        mock_date.insert.assert_any_call({
            'date_display': '2000',
            'date_range': '2000',
            'date_type': 'death_date'
        })
    
    @patch('model.agent.DateField')
    def test_clean_name_birth_only(self, mock_date):
        
        singleTest = Agent(
            name='Test, Tester 1950-',
        )
        roles = singleTest._cleanName()
        self.assertEqual(roles, [])
        self.assertEqual(singleTest.name, 'Test, Tester')
        mock_date.insert.assert_any_call({
            'date_display': '1950',
            'date_range': '1950',
            'date_type': 'birth_date'
        })
    
    def test_clean_roles(self):
        roleTest = Agent(
            name='Test, Tester [tester; testing]',
        )
        roles = roleTest._cleanName()
        self.assertEqual(roles, ['tester', 'testing'])
        self.assertEqual(roleTest.name, 'Test, Tester')
    
    def test_clean_role(self):
        roleTest = Agent(
            name='Test, Tester [tester]',
        )
        roles = roleTest._cleanName()
        self.assertEqual(roles, ['tester'])
        self.assertEqual(roleTest.name, 'Test, Tester')
    
    @patch('model.agent.DateField')
    def test_combined(self, mock_date):
        roleTest = Agent(
            name='Test, Tester 1950-2000 [tester]',
        )
        roles = roleTest._cleanName()
        self.assertEqual(roles, ['tester'])
        self.assertEqual(roleTest.name, 'Test, Tester')
        mock_date.insert.assert_any_call({
            'date_display': '1950',
            'date_range': '1950',
            'date_type': 'birth_date'
        })
        mock_date.insert.assert_any_call({
            'date_display': '2000',
            'date_range': '2000',
            'date_type': 'death_date'
        })
    