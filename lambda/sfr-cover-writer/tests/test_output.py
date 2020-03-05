import hashlib
import pytest
from unittest.mock import MagicMock

from lib.outputs import OutputManager
from helpers.errorHelpers import OutputError


class MockOutputManager(OutputManager):
    KINESIS_CLIENT = MagicMock()


class MockOutObject:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestOutPutManager:
    @pytest.fixture
    def testManager(self, mocker):
        return MockOutputManager()

    def test_putKinesis(self, mocker, testManager):
        mocker.patch.object(
            OutputManager, '_convertToJSON', return_value='stream'
        )
        mocker.patch.object(
            OutputManager, '_createPartitionKey', return_value='md5'
        )
        testManager.putKinesis('data', 'test-stream', recType='testing')
        testManager.KINESIS_CLIENT.put_record.assert_called_once_with(
            StreamName='test-stream',
            Data='stream',
            PartitionKey='md5'
        )

    def test_putKinesis_failure(self, mocker, testManager):
        mocker.patch.object(
            OutputManager, '_convertToJSON', return_value='stream'
        )
        mocker.patch.object(
            OutputManager, '_createPartitionKey', return_value='md5'
        )
        testManager.KINESIS_CLIENT.put_record.side_effect = Exception
        with pytest.raises(OutputError):
            testManager.putKinesis('data', 'test-stream', recType='testing')

    def test_convertToJSON_dict(self):
        testDict = {
            'field1': 'testing',
            'field2': 'again',
            'field3': {
                'nested': 'value'
            }
        }
        jsonStr = MockOutputManager._convertToJSON(testDict)
        assert jsonStr == '{"field1": "testing", "field2": "again", "field3": {"nested": "value"}}'  # noqa: E501

    def test_convertToJSON_object(self):
        testObj = MockOutObject(field1='testing', field2='again')

        jsonStr = MockOutputManager._convertToJSON(testObj)
        assert jsonStr == '{"field1": "testing", "field2": "again"}'

    def test_convertToJSON_failure(self, mocker):
        testDict = {'field': 'something'}
        mockJSON = mocker.patch('lib.outputs.json')
        mockJSON.dumps.side_effect = [TypeError, '{"field": "something"}']
        jsonStr = MockOutputManager._convertToJSON(testDict)
        assert jsonStr == '{"field": "something"}'

    def test_createPartitionKey(self):
        testHasher = hashlib.md5()
        testHasher.update('testURL'.encode('utf-8'))
        checkHash = MockOutputManager._createPartitionKey(
            {'storedURL': 'testURL'}
        )
        assert checkHash == testHasher.hexdigest()
