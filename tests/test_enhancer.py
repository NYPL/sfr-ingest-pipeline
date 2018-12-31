import unittest
from unittest.mock import patch, mock_open, call

from lib.enhancer import enhanceRecord
from helpers.errorHelpers import OCLCError
from lib.dataModel import WorkRecord

class TestEnhancer(unittest.TestCase):

    @patch.dict('os.environ', {'OUTPUT_KINESIS': 'tester', 'OUTPUT_REGION': 'us-test-1'})
    @patch('lib.enhancer.classifyRecord', return_value=(True, True))
    @patch('lib.enhancer.readFromClassify')
    @patch('lib.enhancer.KinesisOutput.putRecord')
    def test_basic_enhancer(self, mock_classify, mock_read, mock_put):
        testRec = {
            'source': 'test',
            'recordID': 1,
            'data': {
                'uuid': '11111111-1111-1111-1111-111111111111',
                'type': 'test',
                'fields': {
                    'test': 'test'
                }
            }
        }

        res = enhanceRecord(testRec)
        self.assertTrue(res)

    def test_basic_enhancer_missing_field(self):
        testRec = {
            'source': 'test',
            'recordID': 1
        }

        res = enhanceRecord(testRec)
        self.assertFalse(res)

    @patch('lib.enhancer.classifyRecord', return_value=(True, True), side_effect=OCLCError('testing'))
    def test_enhancer_err(self, mock_classify):
        testRec = {
            'source': 'test',
            'recordID': 1,
            'data': 'some data'
        }

        res = enhanceRecord(testRec)
        self.assertFalse(res)
        self.assertRaises(OCLCError)
