import unittest
from unittest.mock import patch
import os

from helpers.errorHelpers import NoRecordsReceived

os.environ['DB_USER'] = 'test'
os.environ['DB_PASS'] = 'test'
os.environ['DB_HOST'] = 'test'
os.environ['DB_PORT'] = '1'
os.environ['DB_NAME'] = 'test'
os.environ['REDIS_HOST'] = 'test_host'

# This method is invoked outside of the main handler method as this allows
# us to re-use db connections across Lambda invocations, but it requires a
# little testing weirdness, e.g. we need to mock it on import to prevent errors
with patch('service.SessionManager') as mock_db:
    from service import handler


class TestHandler(unittest.TestCase):

    @patch('service.parseRecords', return_value=True)
    def test_handler_clean(self, mock_parse):
        testRec = {
            'source': 'Kinesis',
            'Records': [
                {
                    'kinesis': {
                        'data': 'data'
                    }
                }
            ]
        }
        resp = handler(testRec, None)
        self.assertTrue(resp)

    def test_handler_error(self):
        testRec = {
            'source': 'Kinesis',
            'Records': []
        }
        try:
            handler(testRec, None)
        except NoRecordsReceived:
            pass
        self.assertRaises(NoRecordsReceived)

    def test_records_none(self):
        testRec = {
            'source': 'Kinesis'
        }
        try:
            handler(testRec, None)
        except NoRecordsReceived:
            pass
        self.assertRaises(NoRecordsReceived)


if __name__ == '__main__':
    unittest.main()
