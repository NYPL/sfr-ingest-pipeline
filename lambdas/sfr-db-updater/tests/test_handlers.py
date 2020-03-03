from base64 import b64encode
import json
import os
from sfrCore import SessionManager
import unittest
from unittest.mock import patch, MagicMock, DEFAULT
from psycopg2 import OperationalError

from helpers.errorHelpers import NoRecordsReceived, DataError

os.environ['DB_USER'] = 'test'
os.environ['DB_PASS'] = 'test'
os.environ['DB_HOST'] = 'test'
os.environ['DB_PORT'] = '1'
os.environ['DB_NAME'] = 'test'
os.environ['REDIS_HOST'] = 'test_host'


class TestHandler(unittest.TestCase):

    @patch.multiple(
        SessionManager,
        generateEngine=DEFAULT, decryptEnvVar=DEFAULT
    )
    def setUp(self, generateEngine, decryptEnvVar):
        from service import handler, parseRecords, parseRecord
        self.handler = handler
        self.parseRecords = parseRecords
        self.parseRecord = parseRecord

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
        resp = self.handler(testRec, None)
        self.assertTrue(resp)

    def test_handler_error(self):
        testRec = {
            'source': 'Kinesis',
            'Records': []
        }
        try:
            self.handler(testRec, None)
        except NoRecordsReceived:
            pass
        self.assertRaises(NoRecordsReceived)

    def test_records_none(self):
        testRec = {
            'source': 'Kinesis'
        }
        try:
            self.handler(testRec, None)
        except NoRecordsReceived:
            pass
        self.assertRaises(NoRecordsReceived)

    @patch('service.parseRecord', side_effect=[1, 2, 3])
    @patch('service.MANAGER')
    @patch('service.DBUpdater')
    def test_parseRecords_success(self, mockUpdater, mockManager, mockParse):
        recResults = self.parseRecords(['rec1', 'rec2', 'rec3'])
        self.assertEqual(recResults, [1, 2, 3])
        mockManager.closeConnection.assert_called_once()
        self.assertEqual(mockParse.call_count, 3)

    @patch('service.parseRecord', side_effect=[1, DataError('testing'), 3])
    @patch('service.MANAGER')
    def test_parseRecords_error(self, mockManager, mockParse):
        recResults = self.parseRecords(['rec1', 'rec2', 'rec3'])
        self.assertEqual(recResults[0], 1)
        self.assertEqual(len(recResults), 1)
        mockManager.closeConnection.assert_called_once()

    @patch('service.MANAGER')
    def test_parseRecord_success(self, mockManager):
        encStr = b64encode(json.dumps({
            'status': 200,
            'source': 'testing'
        }).encode('utf-8'))
        testRecord = {
            'kinesis': {
                'data': encStr
            }
        }
        mockUpdater = MagicMock()
        mockUpdater.importRecord.return_value = 'import_record'
        importRec = self.parseRecord(testRecord, mockUpdater)
        mockManager.startSession.assert_called_once()
        mockManager.commitChanges.assert_called_once()
        self.assertEqual(importRec, 'import_record')

    @patch('service.MANAGER')
    def test_parseRecord_dbErr(self, mockManager):
        encStr = b64encode(json.dumps({
            'status': 200,
            'source': 'testing'
        }).encode('utf-8'))
        testRecord = {
            'kinesis': {
                'data': encStr
            }
        }
        mockUpdater = MagicMock()
        mockUpdater.importRecord.side_effect = OperationalError
        importRec = self.parseRecord(testRecord, mockUpdater)
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
            self.parseRecord(testRecord, 'updater')

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
            self.parseRecord(testRecord, 'updater')

    def test_parseRecord_jsonErr(self):
        encStr = b64encode('{"bad: "json"}'.encode('utf-8'))
        testRecord = {
            'kinesis': {
                'data': encStr
            }
        }
        with self.assertRaises(DataError):
            self.parseRecord(testRecord, 'updater')

    def test_parseRecord_b64Err(self):
        encStr = json.dumps({'bad': 'base64'}).encode('utf-8')
        testRecord = {
            'kinesis': {
                'data': encStr
            }
        }
        with self.assertRaises(DataError):
            self.parseRecord(testRecord, 'updater')


if __name__ == '__main__':
    unittest.main()
