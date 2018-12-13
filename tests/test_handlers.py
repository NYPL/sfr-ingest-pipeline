import json
import unittest
from unittest.mock import patch, mock_open, call

# Set this variable here as it gets checked at loadtime
import os
os.environ['OUTPUT_REGION'] = 'us-test-1'

from service import handler, parseRecords, parseRecord
from helpers.errorHelpers import NoRecordsReceived


class TestHandler(unittest.TestCase):

    @patch('service.parseRecords')
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
        mock_parse.assert_called_once()


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


    @patch('service.parseRecord', return_value=[1,2])
    def test_parseRecords(self, mock_parse):
        records = [
            {
                'data': 'test1'
            },{
                'data': 'test2'
            }
        ]
        resCalls = [
            call({'data': 'test1'}),
            call({'data': 'test2'})
        ]
        res = parseRecords(records)
        mock_parse.assert_has_calls(resCalls)
        self.assertEqual(res, [1,2])


    @patch('service.enhanceRecord', return_value=True)
    @patch('json.loads', return_value={
        'status': 200,
        'stage': 'oclc',
        'data': 'test data'
    })
    def test_parseRecords(self, mock_enhance, mock_json):
        res = parseRecord({'kinesis': {'data': ''}})
        mock_enhance.assert_called_once()
        mock_json.assert_called_once()
        self.assertTrue(res)

    @patch('json.loads', return_value={
        'status': 500,
        'stage': 'oclc',
        'data': 'test data'
    })
    def test_parseRecords_err(self, mock_json):
        res = parseRecord({'kinesis': {'data': ''}})
        mock_json.assert_called_once()
        self.assertFalse(res)

    @patch('json.loads', return_value={
        'status': 200,
        'stage': 'mw',
        'data': 'test data'
    })
    def test_parseRecords_bad_stage(self, mock_json):
        res = parseRecord({'kinesis': {'data': ''}})
        mock_json.assert_called_once()
        self.assertFalse(res)


if __name__ == '__main__':
    unittest.main()
