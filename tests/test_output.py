from datetime import datetime
import os
import unittest
from unittest.mock import patch, MagicMock

from helpers.errorHelpers import OutputError

os.environ['REDIS_HOST'] = 'redis_url'

from lib.outputManager import OutputManager  # noqa: E402


class MockOutputManager(OutputManager):
    KINESIS_CLIENT = MagicMock()
    SQS_CLIENT = MagicMock()
    AWS_REDIS = MagicMock()


class MockOutObject:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class OutputTest(unittest.TestCase):
    @patch('redis.StrictRedis.get', return_value=(
        datetime.now().strftime('%Y-%m-%dT%H:%M:%S').encode('utf-8')
    ))
    @patch('redis.StrictRedis.set')
    def test_redis_current(self, mock_set, mock_get):
        res = MockOutputManager.checkRecentQueries('test/value')
        self.assertTrue(res)

    @patch('redis.StrictRedis.get', return_value=None)
    @patch('redis.StrictRedis.set')
    def test_redis_missing(self, mock_set, mock_get):
        res = MockOutputManager.checkRecentQueries('test/value')
        self.assertEqual(res, False)

    @patch('redis.StrictRedis.get', return_value=(
        '2000-01-01T00:00:00'.encode('utf-8')
    ))
    @patch('redis.StrictRedis.set')
    def test_redis_old(self, mock_set, mock_get):
        res = MockOutputManager.checkRecentQueries('test/value')
        self.assertEqual(res, False)

    @patch.object(OutputManager, '_convertToJSON', return_value='stream')
    @patch.object(OutputManager, '_createPartitionKey', return_value=1)
    def test_putKinesis(self, mockPartition, mockJSON):
        testManager = MockOutputManager()
        testManager.putKinesis('data', 'test-stream',
                               recType='testing', attempts=2)
        testManager.KINESIS_CLIENT.put_record.assert_called_once_with(
            StreamName='test-stream',
            Data='stream',
            PartitionKey=1
        )

    @patch.object(OutputManager, '_convertToJSON', return_value='stream')
    @patch.object(OutputManager, '_createPartitionKey', return_value=1)
    def test_putKinesis_failure(self, mockPartition, mockJSON):
        testManager = MockOutputManager()
        testManager.KINESIS_CLIENT.put_record.side_effect = Exception
        with self.assertRaises(OutputError):
            testManager.putKinesis('data', 'test-stream', recType='testing')

    @patch.object(OutputManager, '_convertToJSON', return_value='message')
    def test_putQueue(self, mockJSON):
        testManager = MockOutputManager()
        testManager.putQueue('data', 'test-queue')
        mockJSON.assert_called_once_with('data')
        testManager.SQS_CLIENT.send_message.assert_called_once_with(
            QueueUrl='test-queue',
            MessageBody='message'
        )

    @patch.object(OutputManager, '_convertToJSON', return_value='stream')
    def test_putQueue_failure(self, mockJSON):
        testManager = MockOutputManager()
        testManager.SQS_CLIENT.send_message.side_effect = Exception
        with self.assertRaises(OutputError):
            testManager.putQueue('data', 'test-queue')
            mockJSON.assert_called_once_with('data')

    def test_convertToJSON_object(self):
        testObj = MockOutObject(field1='testing', field2='again')

        jsonStr = MockOutputManager._convertToJSON(testObj)
        assert jsonStr == '{"field1": "testing", "field2": "again"}'

    @patch('lib.outputManager.json')
    def test_convertToJSON_failure(self, mockJSON):
        testDict = {'field': 'something'}
        mockJSON.dumps.side_effect = [TypeError, '{"field": "something"}']
        jsonStr = MockOutputManager._convertToJSON(testDict)
        assert jsonStr == '{"field": "something"}'

    def test_createPartitionKey_primaryIdentifier(self):
        testObj = {
            'primary_identifier': {
                'identifier': 1
            }
        }

        testKey = MockOutputManager._createPartitionKey(testObj)
        self.assertEqual(testKey, '1')

    def test_createPartitionKey_otherIdentifier(self):
        testObj = {
            'identifiers': [
                {
                    'identifier': 3
                }, {
                    'identifier': 1
                }
            ]
        }

        testKey = MockOutputManager._createPartitionKey(testObj)
        self.assertEqual(testKey, '3')

    def test_createPartitionKey_rowID(self):
        testObj = {
            'id': 123
        }

        testKey = MockOutputManager._createPartitionKey(testObj)
        self.assertEqual(testKey, '123')

    def test_createPartitionKey_None(self):
        testObj = {}

        testKey = MockOutputManager._createPartitionKey(testObj)
        self.assertEqual(testKey, '0')
