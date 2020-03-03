import unittest
from unittest.mock import patch, MagicMock

from lib.enhancer import enhanceRecord
from helpers.errorHelpers import OCLCError, DataError


class TestEnhancer(unittest.TestCase):
    @patch.dict('os.environ', {'OUTPUT_KINESIS': 'tester', 'OUTPUT_REGION': 'us-test-1'})
    @patch('lib.enhancer.classifyRecord', return_value=(True, True))
    @patch('lib.enhancer.readFromClassify')
    @patch('lib.enhancer.OutputManager.putKinesis')
    def test_basic_enhancer(self, mock_classify, mock_read, mock_put):
        testRec = {
            'uuid': '11111111-1111-1111-1111-111111111111',
            'type': 'test',
            'fields': {
                'test': 'test'
            }
        }
        mockWork = MagicMock()
        mockWork.instances = [1, 2, 3]
        mock_read.return_value = (mockWork, 3, 123456)

        res = enhanceRecord(testRec)
        self.assertTrue(res)

    def test_basic_enhancer_missing_field(self):
        testRec = {
            'source': 'test',
            'recordID': 1
        }
        with self.assertRaises(DataError):
            enhanceRecord(testRec)
    
    @patch.dict('os.environ', {'OUTPUT_KINESIS': 'tester', 'OUTPUT_REGION': 'us-test-1'})
    @patch('lib.enhancer.extractAndAppendEditions')
    @patch('lib.enhancer.OutputManager.putKinesis')
    @patch('lib.enhancer.readFromClassify')
    @patch('lib.enhancer.classifyRecord')
    def test_enhancer_500_plus(self, mockClassify, mockRead, mockPut, mockExtract):
        testRec = {
            'uuid': '11111111-1111-1111-1111-111111111111',
            'type': 'test',
            'fields': {
                'test': 'test'
            }
        }
        mockWork = MagicMock()
        mockWork.instances = [True] * 600
        mockRead.return_value = (mockWork, 600, 123456)

        res = enhanceRecord(testRec)

        self.assertEqual(len(mockClassify.mock_calls), 2)
        mockRead.assert_called_once()
        mockExtract.assert_called_once()
        self.assertEqual(len(mockPut.mock_calls), 6)
        self.assertTrue(res)

    @patch.dict('os.environ', {'CLASSIFY_QUEUE': 'testQ', 'OUTPUT_KINESIS': 'tester', 'OUTPUT_REGION': 'us-test-1'})
    @patch('lib.enhancer.extractAndAppendEditions')
    @patch('lib.enhancer.OutputManager.putKinesis')
    @patch('lib.enhancer.OutputManager.putQueue')
    @patch('lib.enhancer.readFromClassify')
    @patch('lib.enhancer.classifyRecord')
    def test_enhancer_1500_plus(self, mockClassify, mockRead, mockSQS, mockPut, mockExtract):
        testRec = {
            'uuid': '11111111-1111-1111-1111-111111111111',
            'type': 'test',
            'fields': {
                'test': 'test'
            }
        }
        mockWork = MagicMock()
        mockWork.instances = [True] * 1500
        mockRead.return_value = (mockWork, 1600, 123456)

        res = enhanceRecord(testRec)

        self.assertEqual(len(mockClassify.mock_calls), 3)
        mockRead.assert_called_once()
        self.assertEqual(len(mockExtract.mock_calls), 2)
        mockSQS.assert_called_once()
        self.assertEqual(len(mockPut.mock_calls), 15)
        self.assertTrue(res)

    @patch.dict('os.environ', {'OUTPUT_KINESIS': 'tester', 'OUTPUT_REGION': 'us-test-1'})
    @patch('lib.enhancer.extractAndAppendEditions')
    @patch('lib.enhancer.OutputManager.putKinesis')
    @patch('lib.enhancer.readFromClassify')
    @patch('lib.enhancer.classifyRecord')
    def test_enhancer_1500_start(self, mockClassify, mockRead, mockPut, mockExtract):
        testRec = {
            'uuid': '11111111-1111-1111-1111-111111111111',
            'type': 'test',
            'fields': {
                'test': 'test'
            },
            'start': 1500
        }
        mockWork = MagicMock()
        mockWork.instances = [True] * 600
        mockRead.return_value = (mockWork, 600, 123456)

        res = enhanceRecord(testRec)

        self.assertEqual(len(mockClassify.mock_calls), 2)
        mockRead.assert_called_once()
        mockExtract.assert_called_once()
        self.assertEqual(len(mockPut.mock_calls), 6)
        self.assertTrue(res)

    @patch('lib.enhancer.classifyRecord', return_value=(True, True), side_effect=OCLCError('testing'))
    def test_enhancer_err(self, mock_classify):
        testRec = {
            'source': 'test',
            'recordID': 1,
            'body': 'some data'
        }
        with self.assertRaises(DataError):
            enhanceRecord(testRec)
