import unittest
import base64
import json
from unittest.mock import patch
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
    @patch('service.SessionManager')
    def test_parse_records_success(self, mock_parse, mock_manager):
        res = parseRecords([1, 2, 3])
        self.assertEqual(res, [1, 2, 3])
    
    @patch('service.parseRecord', side_effect=DBError('test', 'error'))
    @patch('service.SessionManager')
    def test_parse_records_error(self, mock_parse, mock_manager):
        res = parseRecords([1, 2, 3])
        self.assertRaises(DBError)
    
    @patch('service.importRecord', return_value=True)
    @patch('service.SessionManager')
    def test_record_parse_success(self, mock_import, mock_manager):
        testRec = base64.b64encode(json.dumps({
            'status': 200,
            'data': 'data'
        }).encode('utf-8'))
        self.assertTrue(parseRecord({'kinesis': {'data': testRec}}, 'session'))
    
    def test_record_parse_none(self):
        testRec = base64.b64encode(json.dumps({
            'status': 204,
            'source': 'test',
            'data': None
        }).encode('utf-8'))
        with self.assertRaises(NoRecordsReceived):
            parseRecord({'kinesis': {'data': testRec}}, 'session')
    
    def test_record_parse_error_status(self):
        testRec = base64.b64encode(json.dumps({
            'status': 500,
            'data': None
        }).encode('utf-8'))
        with self.assertRaises(DataError):
            parseRecord({'kinesis': {'data': testRec}}, 'session')

    @patch('service.json.loads', side_effect=json.decoder.JSONDecodeError('test', 'test', 1))
    def test_record_json_error(self, mock_json):
        testRec = base64.b64encode(json.dumps({
            'status': 200,
            'data': 'bad data'
        }).encode('utf-8'))
        with self.assertRaises(DataError):
            parseRecord({'kinesis': {'data': testRec}}, 'session')
    
    @patch('service.base64.b64decode', side_effect=UnicodeDecodeError('test', b'test', 0, 0, 'test'))
    def test_record_unicode_error(self, mock_base64):
        testRec = base64.b64encode(json.dumps({
            'status': 200,
            'data': 'bad unicode'
        }).encode('utf-8'))
        with self.assertRaises(DataError):
            parseRecord({'kinesis': {'data': testRec}}, 'session')
        
    @patch('service.importRecord', side_effect=DataError('test err'))
    @patch('service.SessionManager')
    def test_record_parse_write_err(self, mock_import, mock_manager):
        testRec = base64.b64encode(json.dumps({
            'status': 200,
            'data': 'data'
        }).encode('utf-8'))
        res = parseRecord({'kinesis': {'data': testRec}}, 'session')
        self.assertNotEqual(res, True)


if __name__ == '__main__':
    unittest.main()
