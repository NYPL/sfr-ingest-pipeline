from base64 import b64encode
import json
import os
import unittest
from unittest.mock import patch, call

from helpers.errorHelpers import NoRecordsReceived, DataError

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
    from service import handler, parseRecords, parseRecord


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

    @patch('service.parseRecord', side_effect=[1, 2, 3])
    @patch('service.MANAGER')
    def test_parseRecords_success(self, mockManager, mockParse):
        recResults = parseRecords(['rec1', 'rec2', 'rec3'])
        self.assertEqual(recResults, [1, 2, 3])
        mockManager.closeConnection.assert_called_once()
        mockParse.assert_has_calls([call('rec1'), call('rec2'), call('rec3')])

    @patch('service.parseRecord', side_effect=[1, DataError('testing'), 3])
    @patch('service.MANAGER')
    def test_parseRecords_error(self, mockManager, mockParse):
        recResults = parseRecords(['rec1', 'rec2', 'rec3'])
        self.assertEqual(recResults, None)
        mockManager.closeConnection.assert_called_once()

    @patch('service.importRecord', return_value='import_record')
    @patch('service.MANAGER')
    def test_parseRecord_success(self, mockManager, mockImport):
        encStr = b64encode(json.dumps({
            'status': 200,
            'source': 'testing'
        }).encode('utf-8'))
        testRecord = {
            'kinesis': {
                'data': encStr
            }
        }
        importRec = parseRecord(testRecord)
        mockManager.startSession.assert_called_once()
        mockManager.commitChanges.assert_called_once()
        self.assertEqual(importRec, 'import_record')

    @patch('service.importRecord', side_effect=Exception)
    @patch('service.MANAGER')
    def test_parseRecord_dbErr(self, mockManager, mockImport):
        encStr = b64encode(json.dumps({
            'status': 200,
            'source': 'testing'
        }).encode('utf-8'))
        testRecord = {
            'kinesis': {
                'data': encStr
            }
        }
        importRec = parseRecord(testRecord)
        mockManager.startSession.assert_called_once()
        mockManager.commitChanges.assert_not_called()
        mockManager.session.rollback.assert_called_once()
        self.assertEqual(importRec, None)

    def test_parseRecord_noRecordsErr(self):
        encStr = b64encode(json.dumps({
            'status': 204,
            'source': 'testing'
        }).encode('utf-8'))
        testRecord = {
            'kinesis': {
                'data': encStr
            }
        }
        with self.assertRaises(NoRecordsReceived):
            parseRecord(testRecord)

    def test_parseRecord_otherRecordErr(self):
        encStr = b64encode(json.dumps({
            'status': 500,
            'source': 'testing'
        }).encode('utf-8'))
        testRecord = {
            'kinesis': {
                'data': encStr
            }
        }
        with self.assertRaises(DataError):
            parseRecord(testRecord)

    def test_parseRecord_jsonErr(self):
        encStr = b64encode('{"bad: "json"}'.encode('utf-8'))
        testRecord = {
            'kinesis': {
                'data': encStr
            }
        }
        with self.assertRaises(DataError):
            parseRecord(testRecord)

    def test_parseRecord_b64Err(self):
        encStr = json.dumps({'bad': 'base64'}).encode('utf-8')
        testRecord = {
            'kinesis': {
                'data': encStr
            }
        }
        with self.assertRaises(DataError):
            parseRecord(testRecord)


if __name__ == '__main__':
    unittest.main()
