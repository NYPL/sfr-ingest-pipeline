import unittest
import base64
import json
from sfrCore import SessionManager
from unittest.mock import patch, DEFAULT, MagicMock
import os

from helpers.errorHelpers import NoRecordsReceived, DBError, DataError

# This method is invoked outside of the main handler method as this allows
# us to re-use db connections across Lambda invocations, but it requires a
# little testing weirdness, e.g. we need to mock it on import to prevent errors
os.environ['DB_USER'] = 'test'
os.environ['DB_PSWD'] = 'test'
os.environ['DB_HOST'] = 'test'
os.environ['DB_PORT'] = '0'
os.environ['DB_NAME'] = 'test'


class TestHandler(unittest.TestCase):
    @patch.multiple(
        SessionManager, generateEngine=DEFAULT, decryptEnvVar=DEFAULT
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
    def test_parse_records_success(self, mock_parse, mock_manager):
        res = self.parseRecords([1, 2, 3])
        self.assertEqual(res, [1, 2, 3])
    
    @patch('service.parseRecord', side_effect=DBError('test', 'error'))
    @patch('service.MANAGER')
    def test_parse_records_error(self, mock_parse, mock_manager):
        res = self.parseRecords([1, 2, 3])
        self.assertEqual([], res)
                  
    @patch('service.DBManager')
    @patch('service.MANAGER')
    def test_record_parse_success(self, mockManager, mockSession):
        testRec = base64.b64encode(json.dumps({
            'status': 200,
            'data': 'data'
        }).encode('utf-8'))
        mockManager.importRecord.return_value = True
        self.assertTrue(
            self.parseRecord({'kinesis': {'data': testRec}}, mockManager)
        )
    
    def test_record_parse_none(self):
        testRec = base64.b64encode(json.dumps({
            'status': 204,
            'source': 'test',
            'data': None
        }).encode('utf-8'))
        with self.assertRaises(NoRecordsReceived):
            self.parseRecord({'kinesis': {'data': testRec}}, 'session')
    
    def test_record_parse_error_status(self):
        testRec = base64.b64encode(json.dumps({
            'status': 500,
            'data': None
        }).encode('utf-8'))
        with self.assertRaises(DataError):
            self.parseRecord({'kinesis': {'data': testRec}}, 'session')

    @patch('service.json.loads', side_effect=json.decoder.JSONDecodeError('test', 'test', 1))
    def test_record_json_error(self, mock_json):
        testRec = base64.b64encode(json.dumps({
            'status': 200,
            'data': 'bad data'
        }).encode('utf-8'))
        with self.assertRaises(DataError):
            self.parseRecord({'kinesis': {'data': testRec}}, 'session')
    
    @patch('service.base64.b64decode', side_effect=UnicodeDecodeError('test', b'test', 0, 0, 'test'))
    def test_record_unicode_error(self, mock_base64):
        testRec = base64.b64encode(json.dumps({
            'status': 200,
            'data': 'bad unicode'
        }).encode('utf-8'))
        with self.assertRaises(DataError):
            self.parseRecord({'kinesis': {'data': testRec}}, 'session')

    @patch('service.DBManager')
    @patch('service.MANAGER')
    def test_record_parse_write_err(self, mockManager, mockSession):
        testRec = base64.b64encode(json.dumps({
            'status': 200,
            'data': 'data'
        }).encode('utf-8'))
        mockManager.importRecord.side_effect = DataError('test err')
        res = self.parseRecord({'kinesis': {'data': testRec}}, mockManager)
        self.assertNotEqual(res, True)


if __name__ == '__main__':
    unittest.main()
