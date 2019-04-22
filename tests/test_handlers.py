import unittest
from unittest.mock import patch

from service import handler
from helpers.errorHelpers import InvalidExecutionType, VIAFError


class TestHandler(unittest.TestCase):

    @patch('service.VIAFSearch')
    def test_handler_clean(self, mock_viaf):
        testRec = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'queryName': 'Tester, Test'
            }
        }
        mock_viaf().query.return_value = {
            'status': 200,
            'data': {
                'test': 'test'
            }
        }
        resp = handler(testRec, None)
        self.assertEqual(resp['status'], 200)
        self.assertEqual(resp['data']['test'], 'test')
    
    def test_handler_error(self):
        testRec = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'otherQuery': 'Tester, Test'
            }
        }
        try:
            handler(testRec, None)
        except InvalidExecutionType:
            pass
        self.assertRaises(InvalidExecutionType)

    @patch('service.VIAFSearch')
    def test_viaf_query_error(self, mock_viaf):
        testRec = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'queryName': 'Tester, Test'
            }
        }
        mock_viaf().query.side_effect = VIAFError('test viaf error')
        mock_viaf.formatResponse.return_value = {
            'status': 500,
            'data': 'test error'
        }
        resp = handler(testRec, None)
        self.assertEqual(resp['status'], 500)

if __name__ == '__main__':
    unittest.main()
