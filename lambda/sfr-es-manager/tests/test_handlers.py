import unittest
from unittest.mock import patch, call, MagicMock
import os

from helpers.errorHelpers import ESError

os.environ['DB_USER'] = 'test'
os.environ['DB_PASS'] = 'test'
os.environ['DB_HOST'] = 'test'
os.environ['DB_PORT'] = '1'
os.environ['DB_NAME'] = 'test'
os.environ['ES_INDEX'] = 'test'

# This method is invoked outside of the main handler method as this allows
# us to re-use db connections across Lambda invocations, but it requires a
# little testing weirdness, e.g. we need to mock it on import to prevent errors
with patch('service.SessionManager') as mock_db:
    from service import handler, indexRecords


class TestHandler(unittest.TestCase):

    @patch('service.indexRecords', return_value=True)
    def test_handler_clean(self, mock_index):
        testRec = {
            'source': 'CloudWatch'
        }
        resp = handler(testRec, None)
        mock_index.assert_called_once()
        self.assertTrue(resp)

    def test_parse_records_success(self):
        mock_es = MagicMock()
        with patch('service.ESConnection', return_value=mock_es) as mock_conn:
            indexRecords()
            mock_es.generateRecords.assert_called_once()
