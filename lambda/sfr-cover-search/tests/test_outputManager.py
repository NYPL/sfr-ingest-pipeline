import pytest
from unittest.mock import MagicMock

from helpers.errorHelpers import OutputError
from lib.outputManager import OutputManager


class MockOutputManager(OutputManager):
    KINESIS_CLIENT = MagicMock()


class MockOutObject:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestOutputManager:
    @pytest.fixture
    def testManager(self):
        return MockOutputManager()

    def test_putKinesis(self, testManager, mocker):
        mocker.patch.object(
            OutputManager, '_convertToJSON', return_value='stream'
        )
        mocker.patch.object(
            OutputManager, '_createPartitionKey', return_value=1
        )
        testManager.putKinesis('data', 'test-stream',
                               recType='testing')
        testManager.KINESIS_CLIENT.put_record.assert_called_once_with(
            StreamName='test-stream',
            Data='stream',
            PartitionKey=1
        )

    def test_putKinesis_failure(self, testManager, mocker):
        mocker.patch.object(OutputManager, '_convertToJSON')
        mocker.patch.object(OutputManager, '_createPartitionKey')
        testManager.KINESIS_CLIENT.put_record.side_effect = Exception
        with pytest.raises(OutputError):
            testManager.putKinesis('data', 'test-stream', recType='testing')

    def test_convertToJSON_object(self):
        testObj = MockOutObject(field1='testing', field2='again')

        jsonStr = MockOutputManager._convertToJSON(testObj)
        assert jsonStr == '{"field1": "testing", "field2": "again"}'

    def test_convertToJSON_failure(self, mocker):
        mockJSON = mocker.patch('lib.outputManager.json')
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
        assert testKey == '1'

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
        assert testKey == '3'

    def test_createPartitionKey_rowID(self):
        testObj = {
            'id': 123
        }

        testKey = MockOutputManager._createPartitionKey(testObj)
        assert testKey == '123'

    def test_createPartitionKey_None(self):
        testObj = {}

        testKey = MockOutputManager._createPartitionKey(testObj)
        assert testKey == '0'
