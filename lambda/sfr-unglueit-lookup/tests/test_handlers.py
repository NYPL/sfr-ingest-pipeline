import unittest
from unittest.mock import patch

from service import handler
from helpers.errorHelpers import InvalidExecutionType, UnglueError


class TestHandler(unittest.TestCase):

    @patch('service.Unglueit')
    def test_handler_clean(self, mock_unglue):
        testRec = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'isbn': '9999999999'
            }
        }
        mock_unglue().fetchSummary.return_value = {
            'status': 200,
            'data': {
                'test': 'test'
            }
        }
        resp = handler(testRec, None)
        self.assertEqual(resp['status'], 200)
        self.assertEqual(resp['data']['test'], 'test')
        mock_unglue().validate.assert_called_once()

    def test_handler_error(self):
        testRec = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'nonISBN': '987.23'
            }
        }
        try:
            handler(testRec, None)
        except InvalidExecutionType:
            pass
        self.assertRaises(InvalidExecutionType)

    @patch('service.Unglueit')
    def test_unglue_query_error(self, mock_unglue):
        testRec = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'isbn': '9999999999'
            }
        }
        mock_unglue().fetchSummary.side_effect = UnglueError(
            500,
            'test unglue error'
        )
        mock_unglue.formatResponse.return_value = {
            'status': 500,
            'data': 'test error'
        }
        resp = handler(testRec, None)
        self.assertEqual(resp['status'], 500)


if __name__ == '__main__':
    unittest.main()
