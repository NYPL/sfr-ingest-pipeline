import unittest
from unittest.mock import patch, call
import os

from helpers.errorHelpers import NoRecordsReceived, DataError, DBError

os.environ['DB_USER'] = 'test'
os.environ['DB_PASS'] = 'test'
os.environ['DB_HOST'] = 'test'
os.environ['DB_PORT'] = '1'
os.environ['DB_NAME'] = 'test'

# This method is invoked outside of the main handler method as this allows
# us to re-use db connections across Lambda invocations, but it requires a
# little testing weirdness, e.g. we need to mock it on import to prevent errors
with patch('lib.dbManager.dbGenerateConnection') as mock_db:
    from service import handler, parseRecords, parseRecord


class TestHandler(unittest.TestCase):

    @patch('service.parseRecords', return_value=True)
    def test_handler_clean(self, mock_parse):
        testRec = {
            'source': 'SQS',
            'Records': [
                {
                    'Body': '{"type": "work", "identifier": "uuid"}'
                }
            ]
        }
        resp = handler(testRec, None)
        self.assertTrue(resp)

    def test_handler_error(self):
        testRec = {
            'source': 'SQS',
            'Records': []
        }
        with self.assertRaises(NoRecordsReceived):
            handler(testRec, None)

    def test_records_none(self):
        testRec = {
            'source': 'SQQ'
        }
        with self.assertRaises(NoRecordsReceived):
            handler(testRec, None)

    @patch('service.parseRecord', return_value=True)
    def test_parse_records_success(self, mock_parse):
        testRecords = ['rec1', 'rec2']
        res = parseRecords(testRecords)
        mock_parse.assert_has_calls([call('rec1'), call('rec2')])
        self.assertEqual(res, [True, True])

    @patch('service.parseRecord', side_effect=DataError('test error'))
    def test_parse_records_err(self, mock_parse):
        testRecord = ['badRecord']
        res = parseRecords(testRecord)
        self.assertEqual(res, None)

    @patch('service.indexRecord', return_value=True)
    @patch('service.createSession')
    def test_parse_record_success(self, mock_session, mock_index):
        testJSON = {
            'Body': '{"type": "work", "identifier": "a3800805fa64454095c459400c424271"}'
        }
        res = parseRecord(testJSON)
        mock_session.assert_called_once()
        mock_index.assert_called_once()
        self.assertTrue(res)

    def test_parse_bad_json(self):
        badJSON = {
            'Body': '{"type: "work", "identifier": "a3800805fa64454095c459400c424271"}'
        }
        with self.assertRaises(DataError):
            parseRecord(badJSON)

    def test_parse_missing_field(self):
        missingJSON = {
            'Body': '{"type": "work"}'
        }
        with self.assertRaises(DataError):
            parseRecord(missingJSON)

    @patch('service.indexRecord', side_effect=DBError('work', 'Test Error'))
    @patch('service.createSession')
    def test_indexing_error(self, mock_session, mock_index):
        testJSON = {
            'Body': '{"type": "work", "identifier": "a3800805fa64454095c459400c424271"}'
        }
        with self.assertRaises(DBError):
            parseRecord(testJSON)
            mock_session.assert_called_once()
            mock_index.assert_called_once()


if __name__ == '__main__':
    unittest.main()
