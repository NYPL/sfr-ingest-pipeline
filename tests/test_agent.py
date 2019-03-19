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

    def test_clean_name(self):
        
        nameTest = {
            'name': 'Test, Tester 1950-2000',
            'sort_name': '',
            'viaf': None,
            'lcnaf': None
        }
        roleTest = []
        dateTest = []
        Agent._cleanName(nameTest, roleTest, dateTest)
        self.assertEqual(roleTest, [])
        self.assertEqual(nameTest['name'], 'Test, Tester')
        self.assertEqual(dateTest[0]['date_display'], '1950')
        self.assertEqual(dateTest[1]['date_display'], '2000')
    
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
        self.assertEqual(dateTest[0]['date_display'], '1950')
    
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
        self.assertEqual(dateTest[0]['date_display'], '1950')
        self.assertEqual(dateTest[1]['date_display'], '2000')
    